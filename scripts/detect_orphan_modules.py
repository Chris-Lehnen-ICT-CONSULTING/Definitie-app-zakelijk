#!/usr/bin/env python3
"""Orphan-module detector for DefinitieAgent (DEF-600).

Vindt modules in ``src/`` die door niets meer worden geimporteerd. Zulke
modules blijven meeliften in refactors en onderhoud: in DEF-600 bleek dat vijf
van de acht gevonden wezen hun laatste commit kregen van de mypy-campagne
(DEF-170/435/436) en black-reformats -- onderhoud aan code die niemand draait.

Waarom AST en niet grep
-----------------------
Een grep op de modulenaam geeft zowel vals-negatieven als vals-positieven:

* Vals-positief: een module lijkt te leven omdat een *andere* module toevallig
  een symbool met dezelfde naam exporteert. In DEF-600 gebeurde dit bij
  ``RuleViolation`` (services.validation.interfaces vs validation.definitie_validator)
  en ``safe_execute`` (utils.exceptions vs utils.error_helpers).
* Vals-negatief: relatieve imports (``from .x import y``) matchen niet op het
  volledige modulepad.

Dit script bouwt daarom een importindex via de AST van elk bestand in
``src/``, ``tests/`` en ``scripts/``, en kijkt per kandidaat zowel naar
module-imports als naar imports van de symbolen die de module exporteert.

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
SCAN_ROOTS = ("src", "tests", "scripts")

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


def iter_python_files(roots: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        base = ROOT / root
        if not base.exists():
            continue
        files.extend(p for p in base.rglob("*.py") if not SKIP_DIR_PARTS & set(p.parts))
    return sorted(files)


def parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        sys.stderr.write(f"detect_orphan_modules: kan {path} niet parsen: {exc}\n")
        return None


def build_import_index(
    files: list[Path],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Bouw (module-stem -> importers, symboolnaam -> importers).

    Naast echte import-statements tellen ook string-literals die op een
    modulepad lijken. Dat vangt dynamisch laden zoals
    ``importlib.import_module("services.validation.module_adapter")`` en
    ``monkeypatch.setattr("services.x.y", ...)`` in tests -- zonder die
    heuristiek zou zulke code onterecht als wees worden gemeld.
    """
    modules: dict[str, set[str]] = defaultdict(set)
    symbols: dict[str, set[str]] = defaultdict(set)

    for path in files:
        tree = parse(path)
        if tree is None:
            continue
        rel = path.relative_to(ROOT).as_posix()

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


def find_orphans(verbose: bool = False) -> tuple[list[tuple[str, int]], list[str]]:
    """Geef (wezen, cli_entrypoints) terug.

    CLI-entrypoints worden vanaf de commandline gestart en hebben per definitie
    geen importer; ze tellen niet als wees maar worden wel apart gemeld, zodat
    een ongebruikte tool niet ongemerkt blijft rondslingeren.
    """
    allowlist = read_allowlist()
    all_files = iter_python_files(SCAN_ROOTS)
    modules, symbols = build_import_index(all_files)

    orphans: list[tuple[str, int]] = []
    entrypoints: list[str] = []

    for path in sorted(SRC.rglob("*.py")):
        if SKIP_DIR_PARTS & set(path.parts) or path.name == "__init__.py":
            continue
        rel = path.relative_to(ROOT).as_posix()
        if is_exempt(rel, allowlist):
            continue

        importers = {f for f in modules.get(path.stem, set()) if f != rel}
        symbol_importers: set[str] = set()
        for sym in exported_symbols(path):
            symbol_importers |= {f for f in symbols.get(sym, set()) if f != rel}

        if importers or symbol_importers:
            if verbose:
                who = sorted(importers | symbol_importers)[:3]
                print(f"  LEEFT  {rel}  <- {', '.join(who)}")
            continue

        if has_main_block(path):
            entrypoints.append(rel)
            continue

        loc = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        orphans.append((rel, loc))

    return orphans, entrypoints


def read_baseline() -> int:
    if not BASELINE_PATH.exists():
        raise SystemExit(
            f"detect_orphan_modules: baseline ontbreekt ({BASELINE_PATH}).\n"
            "Draai eerst: python scripts/detect_orphan_modules.py --update"
        )
    for line in BASELINE_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return int(stripped)
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
        "--verbose", action="store_true", help="toon ook de levende modules"
    )
    args = parser.parse_args()

    orphans, entrypoints = find_orphans(verbose=args.verbose)
    current = len(orphans)
    total_loc = sum(loc for _, loc in orphans)

    print(f"Verweesde modules in src/: {current}  ({total_loc} regels)")
    for rel, loc in sorted(orphans, key=lambda x: -x[1]):
        print(f"  {rel}  ({loc}r)")

    if entrypoints:
        print(
            f"\nCLI-entrypoints zonder importer: {len(entrypoints)} "
            "(tellen niet als wees -- worden vanaf de commandline gestart)"
        )
        for rel in entrypoints:
            print(f"  {rel}")

    if args.update:
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
