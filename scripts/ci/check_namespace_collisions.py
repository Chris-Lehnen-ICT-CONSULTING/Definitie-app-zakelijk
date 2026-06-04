#!/usr/bin/env python3
"""check_namespace_collisions.py — DEF-409 / DEF-410

Detecteert dependency-confusion risico: src/ top-level packages die via een
PyPI-distributie met dezelfde *import-naam* in requirements*.txt geshadowd
kunnen worden. Met `pythonpath = src` (pytest.ini) zou zo'n PyPI-pakket
stilletjes de in-repo module overschaduwen — een dependency-confusion vector.

Deze Python-rewrite (DEF-410) vervangt de bash-detectie uit DEF-409 en dicht
de vier in de 5-agent review gevonden scope-gaten:

  1. Formele regressie-tests           → tests/ci/test_check_namespace_collisions.py
  2. PEP 508 direct-URL `pkg @ url`    → packaging.requirements.Requirement
  3. Distribution↔import mismatch       → importlib.metadata.packages_distributions()
     (bv. distributie `PyYAML` levert import-naam `yaml`)
  4. `-r`/`-c` requirements-recursie    → includes worden recursief gevolgd

Residuele limiet: een naamloze bare VCS-URL zonder `#egg=` (`git+https://…`)
kan statisch niet benoemd worden en wordt overgeslagen.

Exit codes:
  0 = geen collisions (of lege requirements: geen check mogelijk)
  1 = collision gevonden, OF setup-fout (missende/lege src/)

Gebruik:
  python3 scripts/ci/check_namespace_collisions.py
  python3 scripts/ci/check_namespace_collisions.py --src DIR --requirement FILE ...
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from collections.abc import Iterable, Iterator
from importlib import metadata
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_SRC = REPO_ROOT / "src"
DEFAULT_REQ_FILES = (
    REPO_ROOT / "requirements.txt",
    REPO_ROOT / "requirements-dev.txt",
)

# Een comment begint bij `#` aan regelbegin of voorafgegaan door whitespace.
# URL-fragmenten als `#egg=NAME` hebben géén voorafgaande whitespace en blijven.
_COMMENT_RE = re.compile(r"(^|\s)#.*$")
_EGG_RE = re.compile(r"#egg=([A-Za-z0-9._-]+)")
_INCLUDE_RE = re.compile(r"^(?:-r|--requirement|-c|--constraint)[=\s]+(.+)$")
_CANON_RE = re.compile(r"[-_.]+")


def canonical(name: str) -> str:
    """Normaliseer een distributienaam volgens PEP 503 (lowercase, runs van
    `-_.` → enkel `-`)."""
    return _CANON_RE.sub("-", name.strip()).lower()


def _strip_comment(line: str) -> str:
    return _COMMENT_RE.sub("", line)


def extract_distribution_name(line: str) -> str | None:
    """Geef de PEP 503-canonieke distributienaam van één requirement-regel.

    Dekt: version specs (`pkg>=1`), extras (`pkg[x]`), env-markers (`pkg; …`),
    inline comments, editable installs (`-e … #egg=NAME`), PEP 508 direct-URL
    (`name @ url`) en `#egg=`-URL's. Geeft None voor lege regels, comments,
    pip-optieregels en niet-benoembare URL's.
    """
    text = _strip_comment(line).strip()
    if not text:
        return None
    egg = _EGG_RE.search(text)
    if text.startswith(("-e", "--editable")):
        return canonical(egg.group(1)) if egg else None
    if text.startswith("-"):
        # Overige pip-opties (-i, --extra-index-url, --hash, …).
        # -r/-c includes worden in iter_requirement_lines afgehandeld.
        return None
    if egg:
        return canonical(egg.group(1))
    try:
        return canonical(Requirement(text).name)
    except InvalidRequirement:
        return None


def iter_requirement_lines(
    req_file: Path, _seen: set[Path] | None = None
) -> Iterator[str]:
    """Yield requirement-regels uit een file en volg `-r`/`-c` includes
    recursief. Een cycle-guard (`_seen`) voorkomt oneindige recursie bij
    onderling verwijzende files."""
    if _seen is None:
        _seen = set()
    resolved = req_file.resolve()
    if resolved in _seen or not req_file.is_file():
        return
    _seen.add(resolved)
    for raw in req_file.read_text(encoding="utf-8").splitlines():
        include = _INCLUDE_RE.match(_strip_comment(raw).strip())
        if include:
            target = (req_file.parent / include.group(1).strip()).resolve()
            if not target.is_file():
                print(
                    f"WAARSCHUWING: include-target niet gevonden, overgeslagen: {target}",
                    file=sys.stderr,
                )
            yield from iter_requirement_lines(target, _seen)
        else:
            yield raw


def collect_distributions(req_files: Iterable[Path]) -> set[str]:
    """Verzamel alle canonieke distributienamen uit de requirement-files
    (inclusief recursief geïncludeerde files)."""
    names: set[str] = set()
    for req_file in req_files:
        for line in iter_requirement_lines(Path(req_file)):
            name = extract_distribution_name(line)
            if name:
                names.add(name)
    return names


def build_distribution_import_map() -> dict[str, set[str]]:
    """Bouw een map: canonieke distributienaam → set van lowercase
    import-toplevels, via importlib.metadata. Lost mismatches als
    `PyYAML` → `yaml` op (gap 3)."""
    mapping: dict[str, set[str]] = defaultdict(set)
    for import_name, dists in metadata.packages_distributions().items():
        for dist in dists:
            mapping[canonical(dist)].add(import_name.lower())
    return mapping


def import_names_for(dist: str, dist_map: dict[str, set[str]]) -> set[str]:
    """Resolve de import-namen van een distributie. Valt terug op de canonieke
    naam met `-`→`_` wanneer het pakket niet geïnstalleerd is (en dus niet in
    de metadata-map zit). Een expliciete lege set (distributie zonder top-level
    imports) blijft leeg — alleen een ontbrekende sleutel triggert de fallback."""
    names = dist_map.get(dist)
    return names if names is not None else {dist.replace("-", "_")}


def collect_src_top_levels(src_dir: Path) -> set[str]:
    """Verzamel de genormaliseerde top-level import-namen onder src/: zowel
    package-directories als losse top-level `.py` modules. Beide zijn met
    `pythonpath=src` importeerbaar en dus shadowbaar (`src/main.py` → `main`)."""
    tops: set[str] = set()
    for child in src_dir.iterdir():
        if child.name.startswith(".") or child.name == "__pycache__":
            continue
        if child.is_dir() and not child.name.endswith(".egg-info"):
            tops.add(child.name.lower())
        elif child.is_file() and child.suffix == ".py" and child.stem != "__init__":
            tops.add(child.stem.lower())
    return tops


def find_collisions(
    req_files: Iterable[Path],
    src_dir: Path,
    dist_map: dict[str, set[str]] | None = None,
    distributions: set[str] | None = None,
) -> dict[str, str]:
    """Geef {import_naam: distributie} voor elke src/ top-level die door de
    import-naam van een vereiste distributie geshadowd wordt.

    `distributions` mag vooraf-gescand worden meegegeven (door `main`) zodat de
    requirement-files niet twee keer geparsed hoeven te worden."""
    src_tops = collect_src_top_levels(Path(src_dir))
    if distributions is None:
        distributions = collect_distributions(req_files)
    if dist_map is None:
        dist_map = build_distribution_import_map()
    collisions: dict[str, str] = {}
    for dist in distributions:
        for name in import_names_for(dist, dist_map) & src_tops:
            collisions[name] = dist
    return collisions


def _print_collisions(collisions: dict[str, str]) -> None:
    print(
        "❌ DEPENDENCY-CONFUSION RISICO: src/ top-level packages botsen met "
        "PyPI-deps:",
        file=sys.stderr,
    )
    for name, dist in sorted(collisions.items()):
        suffix = "" if canonical(name) == canonical(dist) else f"  (via dist '{dist}')"
        print(f"  - {name}{suffix}", file=sys.stderr)
    print("", file=sys.stderr)
    print(
        "Met pythonpath=src zou de PyPI-package de in-repo module stil kunnen",
        file=sys.stderr,
    )
    print("shadowen. Mogelijke fixes:", file=sys.stderr)
    print(
        "  1. Hernoem de src/-package (bv. naar definitieagent.X — zie DEF-409)",
        file=sys.stderr,
    )
    print(
        "  2. Verwijder de botsende PyPI-dependency uit requirements*.txt",
        file=sys.stderr,
    )
    print(
        "  3. Vervang door een specifiekere PyPI-package met andere naam",
        file=sys.stderr,
    )
    print("", file=sys.stderr)
    print(
        "Zie docs/CONTRIBUTING.md sectie 'Dependency-confusion policy'.",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detecteer dependency-confusion collisions tussen "
        "requirements*.txt en src/ top-levels."
    )
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC, help="src/ directory")
    parser.add_argument(
        "--requirement",
        "-r",
        dest="req_files",
        action="append",
        type=Path,
        help="requirements-file (herhaalbaar; default: requirements*.txt)",
    )
    args = parser.parse_args(argv)

    src_dir: Path = args.src
    req_files = args.req_files or list(DEFAULT_REQ_FILES)

    if not src_dir.is_dir():
        print(f"FOUT: src/ directory niet gevonden op {src_dir}", file=sys.stderr)
        return 1

    src_tops = collect_src_top_levels(src_dir)
    if not src_tops:
        print(f"FOUT: geen top-level packages gevonden in {src_dir}", file=sys.stderr)
        return 1

    existing = [f for f in req_files if Path(f).is_file()]
    distributions = collect_distributions(existing)
    if not distributions:
        # Lege/whitespace-only requirements is een geldige staat — geen
        # packages = geen collision mogelijk. Log wel hoeveel src/-modules
        # ongecontroleerd blijven zodat reviewers de stille staat niet missen.
        print(
            f"INFO: geen packages in requirements*.txt — {len(src_tops)} "
            "src/-modules ongecontroleerd."
        )
        return 0

    collisions = find_collisions(existing, src_dir, distributions=distributions)
    if collisions:
        _print_collisions(collisions)
        return 1

    print("✓ Geen namespace-collisions tussen requirements*.txt en src/ top-levels.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
