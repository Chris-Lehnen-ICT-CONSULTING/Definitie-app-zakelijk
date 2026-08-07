#!/usr/bin/env python3
"""Orphan-module detector for DefinitieAgent (DEF-600).

Vindt modules in ``src/`` die door niets meer worden geimporteerd. Zulke
modules blijven meeliften in refactors en onderhoud: in DEF-600 bleek dat vijf
van de acht gevonden wezen hun laatste commit kregen van de mypy-campagne
(DEF-170/435/436) en black-reformats -- onderhoud aan code die niemand draait.

Waarom AST en niet grep
-----------------------
Een grep op de modulenaam mist relatieve imports (``from .x import y``) en
dynamisch laden. Dit script bouwt daarom een importindex via de AST van elk
bestand in ``src/``, ``tests/`` en ``scripts/``, en kijkt per kandidaat zowel
naar module-imports als naar imports van de symbolen die de module exporteert.

Bekende onnauwkeurigheid -- de uitkomst is een ONDERGRENS
----------------------------------------------------------
De symbool-index is gesleuteld op de kále symboolnaam, niet op
``(module, symbool)``. Een import van ``RuleViolation`` uit
``services.validation.interfaces`` houdt dus ook een andere module die
``RuleViolation`` exporteert "levend". Idem voor de module-index, die op
``path.stem`` matcht: twee gelijknamige modules in verschillende packages
houden elkaar overeind.

Beide fouten wijzen dezelfde kant op: het script meldt eerder **te weinig**
wezen dan te veel. Dat is de veilige richting voor een gate (geen vals alarm),
maar het betekent dat de baseline een ondergrens is en dat een gemelde wees
altijd handmatig geverifieerd moet worden op de *herkomst* van schijnbare
referenties -- niet alleen op het aantal. Verfijning naar
``(module, symbool)`` staat getrackt in DEF-609.

Bekende uitzonderingen (worden nooit als wees gemeld)
-----------------------------------------------------
* ``src/main.py`` -- Streamlit entrypoint, wordt niet geimporteerd.
* ``src/pages/*`` -- Streamlit multipage-conventie: automatisch geladen omdat
  de map naast het entrypoint staat.
* ``src/toetsregels/validators/*`` en ``src/toetsregels/regels/*`` -- worden
  dynamisch geladen via ``importlib.util.spec_from_file_location`` in
  ``json_validator_loader.py``. (Dat die loader zelf alleen door tests wordt
  aangeroepen is een apart probleem; zie DEF-606.)
* ``__init__.py`` -- package-markers.
* Alles in ``scripts/allowlist_orphan_modules.txt``.

Usage:
    python scripts/detect_orphan_modules.py            # check (CI gate)
    python scripts/detect_orphan_modules.py --update   # ratchet de baseline
    python scripts/detect_orphan_modules.py --verbose  # toon per module details
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# Waar we naar importers zoeken (een import híer telt als "leeft").
SCAN_ROOTS = ("src", "tests", "scripts")

# Waar we naar wezen zoeken. `scripts/` staat erbij omdat dode tooling
# net zo goed meelift in refactors als dode productiecode -- DEF-609 vond
# daar een script dat al maanden crashte op een verwijderde import.
CANDIDATE_ROOTS = ("src", "scripts")

BASELINE_PATH = Path(__file__).with_name("orphan_modules_baseline.txt")
ALLOWLIST_PATH = Path(__file__).with_name("allowlist_orphan_modules.txt")

SKIP_DIR_PARTS = {"__pycache__", "_archief", "archief", "ARCHIEF", "archive", ".venv"}

# Paden die per definitie geen statische importer hebben.
EXEMPT_PREFIXES = (
    "src/pages/",  # Streamlit multipage auto-discovery
    "src/toetsregels/validators/",  # dynamisch via importlib (json_validator_loader)
    "src/toetsregels/regels/",  # idem
)
EXEMPT_FILES = ("src/main.py",)

# Te generiek om als bewijs van leven te tellen.
GENERIC_SYMBOLS = {"logger", "T", "F", "main", "setup", "run", "app", "config"}


# Onder dit aantal gescande bestanden klopt er iets niet met de checkout of de
# skip-filters; dan faalt het script liever hard dan dat het "0 wezen" meldt.
MIN_EXPECTED_FILES = 100


def iter_python_files(
    roots: tuple[str, ...], root: Path | None = None, min_expected: int | None = None
) -> list[Path]:
    """Verzamel te scannen bestanden; faalt hard bij een verdacht lege scan.

    De skip-filters worden op het pad **relatief aan de repo-root** toegepast.
    Zou je ``p.parts`` gebruiken, dan filtert een checkout onder bijvoorbeeld
    ``~/archive/`` of ``~/archief/`` de hele boom weg en meldt de gate vrolijk
    "0 wezen -- OK": fail-open precies daar waar het niet mag.

    ``root``/``min_expected`` zijn parameters zodat tests tegen een tmp-boom
    kunnen draaien zonder module-globals te monkeypatchen.
    """
    base_root = root if root is not None else ROOT
    threshold = min_expected if min_expected is not None else MIN_EXPECTED_FILES

    files: list[Path] = []
    for sub in roots:
        base = base_root / sub
        if not base.exists():
            continue
        files.extend(
            p
            for p in base.rglob("*.py")
            if not SKIP_DIR_PARTS & set(p.relative_to(base_root).parts)
        )

    if len(files) < threshold:
        raise SystemExit(
            f"detect_orphan_modules: slechts {len(files)} bestanden gevonden onder "
            f"{base_root} (verwacht >= {threshold}). Klopt de working directory, "
            "of filtert SKIP_DIR_PARTS te veel weg? Afgebroken om een vals-groene "
            "gate te voorkomen."
        )
    return sorted(files)


def parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        sys.stderr.write(f"detect_orphan_modules: kan {path} niet parsen: {exc}\n")
        return None


def build_import_index(
    files: list[Path], root: Path | None = None
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Bouw (module-stem -> importers, symboolnaam -> importers).

    Naast echte import-statements tellen ook string-literals die op een
    modulepad lijken. Dat vangt dynamisch laden zoals
    ``importlib.import_module("services.validation.module_adapter")`` en
    ``monkeypatch.setattr("services.x.y", ...)`` in tests -- zonder die
    heuristiek zou zulke code onterecht als wees worden gemeld.
    """
    base_root = root if root is not None else ROOT
    modules: dict[str, set[str]] = defaultdict(set)
    symbols: dict[str, set[str]] = defaultdict(set)

    for path in files:
        tree = parse(path)
        if tree is None:
            continue
        rel = path.relative_to(base_root).as_posix()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for part in alias.name.split("."):
                        modules[part].add(rel)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for part in node.module.split("."):
                        modules[part].add(rel)
                for alias in node.names:
                    if alias.name == "*":
                        if node.module:
                            modules[node.module.split(".")[-1]].add(rel)
                    else:
                        symbols[alias.name].add(rel)
                        # `from . import x` / `from .pkg import x`: x kan zelf een
                        # module zijn. Zonder deze regel belandt hij alleen in de
                        # symbol-index en wordt een module die niets exporteert
                        # onterecht als wees gemeld -- de gevaarlijke richting.
                        if node.level > 0:
                            modules[alias.name].add(rel)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                # Dotted string die een modulepad kan zijn (dynamische import).
                value = node.value
                if "." in value and " " not in value and "/" not in value:
                    for part in value.split("."):
                        if part.isidentifier():
                            modules[part].add(rel)
    return modules, symbols


def has_main_block(path: Path) -> bool:
    """True als de module een ``if __name__ == "__main__":`` block heeft."""
    tree = parse(path)
    if tree is None:
        return False
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and any(
                isinstance(c, ast.Constant) and c.value == "__main__"
                for c in test.comparators
            )
        ):
            return True
    return False


# Statements die op moduleniveau geen "uitvoering" zijn: definities, imports,
# docstrings, constanten en type-aliassen.
_DECLARATIEF = (
    ast.Import,
    ast.ImportFrom,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Assign,
    ast.AnnAssign,
    ast.Expr,  # docstrings (verder gefilterd op ast.Constant)
    ast.Pass,
)


def has_toplevel_code(path: Path) -> bool:
    """True als de module uitvoerbare code op moduleniveau heeft.

    Een script dat je start met ``python pad/naar/script.py`` of
    ``streamlit run script.py`` heeft vaak geen ``__main__``-guard: het doet
    zijn werk gewoon op moduleniveau. Zulke bestanden zijn entrypoints, geen
    wezen -- ``debug_session_state.py`` roept bijvoorbeeld direct ``st.title()``
    aan.

    Alleen echte uitvoering telt: imports, definities, constanten en
    docstrings blijven declaratief.
    """
    tree = parse(path)
    if tree is None:
        return False
    for node in tree.body:
        if isinstance(node, ast.Expr):
            # Docstring of losse constante -> declaratief; een call wel niet.
            if isinstance(node.value, ast.Constant):
                continue
            return True
        if not isinstance(node, _DECLARATIEF):
            return True
    return False


def broken_src_imports(path: Path, root: Path) -> tuple[list[str], list[str]]:
    """Imports naar een ``src``-module die niet (meer) bestaat.

    Geeft ``(runtime, type_only)`` terug -- twee verschillende ernstniveaus:

    * **runtime**: een gewone import. Het bestand crasht met
      ``ModuleNotFoundError`` zodra het wordt uitgevoerd of geimporteerd.
    * **type_only**: een import onder ``if TYPE_CHECKING:``. Die draait niet,
      dus er crasht niets, maar de annotatie verwijst naar het niets. Mypy
      vangt dat hier niet: de services-gate draait met
      ``--ignore-missing-imports``.

    Een wees en een kapot bestand zijn verschillende problemen: DEF-609 vond
    een script met een ``__main__``-block -- dus geen wees -- dat al maanden
    crashte omdat de geimporteerde module in een eerdere opruiming was
    verdwenen. Alleen wezen tellen zou dat gemist hebben.

    Er wordt uitsluitend gekeken naar imports waarvan het eerste pad-segment
    een bestaand top-level item in ``src/`` is; externe pakketten blijven
    buiten beschouwing (die horen bij de dependency-audit).
    """
    src = root / "src"
    tree = parse(path)
    if tree is None:
        return [], []

    def hoort_bij_src(dotted: str) -> bool:
        top = dotted.split(".", maxsplit=1)[0]
        return (src / top).is_dir() or (src / f"{top}.py").exists()

    def bestaat(dotted: str) -> bool:
        target = src / Path(*dotted.split("."))
        return target.with_suffix(".py").exists() or (target / "__init__.py").exists()

    # Verzamel de regelnummers die onder `if TYPE_CHECKING:` vallen.
    type_only_regels: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        is_tc = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
            isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
        )
        if is_tc:
            for kind in ast.walk(node):
                type_only_regels.add(kind.lineno) if hasattr(kind, "lineno") else None

    runtime: list[str] = []
    type_only: list[str] = []

    def registreer(dotted: str, lineno: int) -> None:
        (type_only if lineno in type_only_regels else runtime).append(dotted)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module and hoort_bij_src(node.module):
                if not bestaat(node.module):
                    registreer(node.module, node.lineno)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if hoort_bij_src(alias.name) and not bestaat(alias.name):
                    registreer(alias.name, node.lineno)
    return sorted(set(runtime)), sorted(set(type_only))


def is_entrypoint(path: Path, rel: str) -> bool:
    """Een module die vanaf de commandline gestart wordt, is geen wees.

    De top-level-code-heuristiek geldt **alleen voor** ``scripts/``. Daar is
    uitvoering op moduleniveau de normale vorm voor een tool zonder
    ``__main__``-guard. In ``src/`` zou dezelfde heuristiek te ruim zijn: een
    configuratiemodule met bijvoorbeeld ``__all__.append(...)`` op moduleniveau
    is geen entrypoint maar gewoon een module -- die moet als wees zichtbaar
    blijven.
    """
    if has_main_block(path):
        return True
    return rel.startswith("scripts/") and has_toplevel_code(path)


def exported_symbols(path: Path) -> list[str]:
    """Publieke top-level namen (class/def/constante)."""
    tree = parse(path)
    if tree is None:
        return []
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            if not node.name.startswith("_"):
                names.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    names.append(target.id)
    return [n for n in names if n not in GENERIC_SYMBOLS]


def is_exempt(rel: str, allowlist: set[str]) -> bool:
    if rel in allowlist or rel in EXEMPT_FILES:
        return True
    return any(rel.startswith(prefix) for prefix in EXEMPT_PREFIXES)


def read_allowlist() -> set[str]:
    if not ALLOWLIST_PATH.exists():
        return set()
    entries = set()
    for line in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            entries.add(stripped)
    return entries


def find_orphans(
    verbose: bool = False,
    root: Path | None = None,
    scan_roots: tuple[str, ...] | None = None,
    min_expected: int | None = None,
    candidate_roots: tuple[str, ...] | None = None,
) -> tuple[
    list[tuple[str, int]],
    list[str],
    list[tuple[str, list[str]]],
    list[tuple[str, list[str]]],
]:
    """Geef (wezen, cli_entrypoints, kapotte_imports, type_only_kapot) terug.

    CLI-entrypoints worden vanaf de commandline gestart en hebben per definitie
    geen importer; ze tellen niet als wees maar worden wel apart gemeld, zodat
    een ongebruikte tool niet ongemerkt blijft rondslingeren.

    Kapotte imports staan hier los van: een bestand met een ``__main__``-block
    is geen wees, maar kan wel crashen op een module die in een eerdere
    opruiming is verdwenen. Die twee categorieen overlappen niet.

    ``root``/``scan_roots``/``min_expected`` zijn parameters zodat tests tegen
    een tmp-boom kunnen draaien zonder module-globals te monkeypatchen.
    """
    root = root if root is not None else ROOT
    roots = scan_roots if scan_roots is not None else SCAN_ROOTS
    kandidaat_mappen = (
        candidate_roots if candidate_roots is not None else CANDIDATE_ROOTS
    )

    allowlist = read_allowlist()
    all_files = iter_python_files(roots, root=root, min_expected=min_expected)
    modules, symbols = build_import_index(all_files, root=root)

    orphans: list[tuple[str, int]] = []
    entrypoints: list[str] = []
    broken: list[tuple[str, list[str]]] = []
    type_only_broken: list[tuple[str, list[str]]] = []

    kandidaten = sorted(
        p
        for m in kandidaat_mappen
        if (root / m).exists()
        for p in (root / m).rglob("*.py")
    )
    for path in kandidaten:
        if (
            SKIP_DIR_PARTS & set(path.relative_to(root).parts)
            or path.name == "__init__.py"
        ):
            continue
        rel = path.relative_to(root).as_posix()
        if is_exempt(rel, allowlist):
            continue

        # Onafhankelijk van wees-zijn: verwijst dit bestand naar een verdwenen module?
        runtime_kapot, type_kapot = broken_src_imports(path, root)
        if runtime_kapot:
            broken.append((rel, runtime_kapot))
        if type_kapot:
            type_only_broken.append((rel, type_kapot))

        importers = {f for f in modules.get(path.stem, set()) if f != rel}
        if importers:
            # Short-circuit: scheelt een tweede AST-parse (exported_symbols) voor
            # de ~95% modules die sowieso leven.
            if verbose:
                print(f"  LEEFT  {rel}  <- {', '.join(sorted(importers)[:3])}")
            continue

        symbol_importers: set[str] = set()
        for sym in exported_symbols(path):
            symbol_importers |= {f for f in symbols.get(sym, set()) if f != rel}

        if symbol_importers:
            if verbose:
                print(f"  LEEFT  {rel}  <- {', '.join(sorted(symbol_importers)[:3])}")
            continue

        if is_entrypoint(path, rel):
            entrypoints.append(rel)
            continue

        loc = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        orphans.append((rel, loc))

    return orphans, entrypoints, broken, type_only_broken


def read_baseline() -> int:
    if not BASELINE_PATH.exists():
        raise SystemExit(
            f"detect_orphan_modules: baseline ontbreekt ({BASELINE_PATH}).\n"
            "Draai eerst: python scripts/detect_orphan_modules.py --update"
        )
    for line in BASELINE_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            try:
                return int(stripped)
            except ValueError:
                raise SystemExit(
                    f"detect_orphan_modules: baseline bevat geen geldig getal "
                    f"({BASELINE_PATH}): {stripped!r}"
                ) from None
    raise SystemExit("detect_orphan_modules: baseline bevat geen getal")


def write_baseline(count: int) -> None:
    BASELINE_PATH.write_text(
        "# Orphan-module baseline (DEF-600) -- modules in src/ zonder enige\n"
        "# importer. Mag alleen dalen.\n"
        "# Bijwerken: python scripts/detect_orphan_modules.py --update\n"
        "# Bewuste uitzondering? Zet het pad in allowlist_orphan_modules.txt\n"
        f"{count}\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Orphan-module detector (DEF-600)")
    parser.add_argument(
        "--update", action="store_true", help="schrijf de huidige telling als baseline"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="sta toe dat --update de baseline VERHOOGT (vereist een reden in de PR)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="toon ook de levende modules"
    )
    args = parser.parse_args()

    orphans, entrypoints, broken, type_only_broken = find_orphans(verbose=args.verbose)
    current = len(orphans)
    total_loc = sum(loc for _, loc in orphans)

    print(f"Verweesde modules: {current}  ({total_loc} regels)")
    for rel, loc in sorted(orphans, key=lambda x: -x[1]):
        print(f"  {rel}  ({loc}r)")

    if entrypoints and args.verbose:
        print(
            f"\nCLI-entrypoints zonder importer: {len(entrypoints)} "
            "(tellen niet als wees -- worden vanaf de commandline gestart)"
        )
        for rel in entrypoints:
            print(f"  {rel}")
    elif entrypoints:
        print(
            f"\n{len(entrypoints)} CLI-entrypoints zonder importer "
            "(niet als wees geteld; --verbose toont de lijst)"
        )

    # Waarschuwing, niet blokkerend: een TYPE_CHECKING-import draait niet, dus
    # er crasht niets. De annotatie wijst wel naar het niets, en de mypy-gate
    # ziet het niet (die draait met --ignore-missing-imports).
    if type_only_broken:
        print(
            f"\nLET OP: {len(type_only_broken)} bestand(en) hebben een "
            "TYPE_CHECKING-import naar een src-module die niet bestaat. "
            "Crasht niet, maar de annotatie klopt niet:"
        )
        for rel, mods in type_only_broken:
            print(f"  {rel}")
            for mod in mods:
                print(f"      -> {mod}")

    # Blokkerend: dit is geen schuld-met-baseline maar kapotte code.
    if broken:
        print(
            f"\nFAIL: {len(broken)} bestand(en) importeren een src-module die "
            "niet bestaat -- deze crashen bij uitvoering:",
            file=sys.stderr,
        )
        for rel, mods in broken:
            print(f"  {rel}", file=sys.stderr)
            for mod in mods:
                print(f"      -> {mod}", file=sys.stderr)
        return 1

    if args.update:
        # De baseline belooft "mag alleen dalen"; dwing dat hier af, anders
        # betonneert een enkele --update na een groei de regressie.
        if BASELINE_PATH.exists():
            previous = read_baseline()
            if current > previous and not args.force:
                print(
                    f"\nFAIL: --update zou de baseline VERHOGEN "
                    f"({previous} -> {current}).\n"
                    "   Ruim de nieuwe wezen op, of gebruik --force met een "
                    "expliciete reden in de PR.",
                    file=sys.stderr,
                )
                return 1
        write_baseline(current)
        print(f"\nBaseline bijgewerkt naar {current}.")
        return 0

    baseline = read_baseline()
    if current > baseline:
        print(
            f"\nFAIL: verweesde modules gegroeid: {current} > baseline {baseline}.\n"
            "   Sluit de module aan, verwijder hem, of zet het pad in\n"
            "   scripts/allowlist_orphan_modules.txt met een reden.",
            file=sys.stderr,
        )
        return 1

    if current < baseline:
        print(
            f"\nOK: gedaald van {baseline} naar {current} "
            f"({baseline - current} minder). Zet de nieuwe vloer vast met --update."
        )
        return 0

    print(f"\nOK: gelijk aan baseline ({baseline}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
