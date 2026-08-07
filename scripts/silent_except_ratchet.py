#!/usr/bin/env python3
"""Silent-except ratchet for DefinitieAgent (DEF-393).

`src/` bevat ~511 brede exception handlers (`except Exception` / bare except).
Die zijn niet allemaal schuld: een fallback aan een systeemgrens mag breed
vangen, zolang de fout zichtbaar blijft. Het probleem is de *stille* variant --
geen logging en geen re-raise -- want die verbergt bugs.

Dit script classificeert elke brede handler op wat er in de body gebeurt:

    C. HERGOOIT       bevat een raise-statement                 -> correct
    B. GELOGD         roept logger.*/st.error/st.warning aan    -> zichtbaar
    D. GEDOCUMENTEERD marker-comment boven de handler           -> bewuste keuze
    A. STIL           geen van bovenstaande                     -> ECHTE SCHULD

Alleen categorie A telt mee voor de ratchet.

- Faalt (exit 1) zodra het aantal stille handlers GROEIT boven de baseline.
- Slaagt wanneer het gelijk blijft.
- Bij een DALING toont het de winst; met ``--update`` zakt de baseline mee,
  zodat het plafond alleen omlaag kan.

Een bewuste brede vangst haal je uit de telling door de marker
``# Intentional broad catch: <reden>`` op de regel(s) direct boven de handler
te zetten.

Verhouding tot de bestaande hook
--------------------------------
`.claude/hooks/check-silent-exceptions.py` (DEF-254) blokkeert bij het
schrijven al het meest directe patroon: een brede except met alleen een
pass/return/ellipsis eronder. Die hook is *preventie* voor nieuwe code en
werkt op een regex over de diff.

Dit script is *afbouw* voor bestaande code en kijkt via de AST naar de hele
handler-body, dus het vindt ook stille handlers die de regex mist (meerdere
statements, tussenliggende comments, `except ... as e` met een kale return
verderop). De twee vullen elkaar aan.

Usage:
    python scripts/silent_except_ratchet.py            # check (CI gate)
    python scripts/silent_except_ratchet.py --update   # ratchet de baseline
    python scripts/silent_except_ratchet.py --list     # toon alle locaties
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections import Counter
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
BASELINE_PATH = Path(__file__).with_name("silent_except_baseline.txt")

SKIP_DIR_PARTS = {"__pycache__", "_archief", "archief", "ARCHIEF", "archive"}

# Namen die als "de fout is zichtbaar gemaakt" tellen.
LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical"}

# Marker waarmee een bewuste brede vangst zichzelf uit de telling haalt.
INTENTIONAL_MARKER = "intentional broad catch"

BROAD_NAMES = {"Exception", "BaseException"}


# Onder dit aantal klopt er iets niet met de checkout of de skip-filters; dan
# faalt het script liever hard dan dat het "0 stille handlers" meldt.
MIN_EXPECTED_FILES = 100


def iter_source_files() -> list[Path]:
    """Verzamel te scannen bestanden; faalt hard bij een verdacht lege scan.

    Skip-filters op het pad **relatief aan de repo-root**: met ``p.parts`` zou
    een checkout onder ``~/archive/`` de hele boom wegfilteren en zou de gate
    "0 stille handlers -- OK" melden. Fail-open in een gate is erger dan geen
    gate, want het geeft valse zekerheid.
    """
    root = SRC.parent
    files = [
        p
        for p in sorted(SRC.rglob("*.py"))
        if not SKIP_DIR_PARTS & set(p.relative_to(root).parts)
    ]
    if len(files) < MIN_EXPECTED_FILES:
        raise SystemExit(
            f"silent_except_ratchet: slechts {len(files)} bestanden gevonden onder "
            f"{SRC} (verwacht >= {MIN_EXPECTED_FILES}). Afgebroken om een "
            "vals-groene gate te voorkomen."
        )
    return files


def is_broad(handler: ast.ExceptHandler) -> bool:
    """True voor bare except, brede except en tuples die er een bevatten."""
    exc = handler.type
    if exc is None:
        return True
    if isinstance(exc, ast.Name):
        return exc.id in BROAD_NAMES
    if isinstance(exc, ast.Tuple):
        return any(
            isinstance(elt, ast.Name) and elt.id in BROAD_NAMES for elt in exc.elts
        )
    return False


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def classify(handler: ast.ExceptHandler, lines: list[str]) -> str:
    """Geef 'A'..'D' terug voor deze handler (zie moduledocstring)."""
    for node in ast.walk(handler):
        if isinstance(node, ast.Raise):
            return "C"

    for node in ast.walk(handler):
        if isinstance(node, ast.Call) and _call_name(node) in LOG_METHODS:
            return "B"

    # Marker op de handler-regel zelf of de twee regels ervoor.
    start = max(0, handler.lineno - 3)
    context = "\n".join(lines[start : handler.lineno]).lower()
    if INTENTIONAL_MARKER in context:
        return "D"

    return "A"


def scan() -> tuple[Counter[str], list[tuple[str, int, str]]]:
    counts: Counter[str] = Counter()
    silent: list[tuple[str, int, str]] = []

    for path in iter_source_files():
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
        except SyntaxError as exc:
            sys.stderr.write(f"silent_except_ratchet: kan {path} niet parsen: {exc}\n")
            continue

        lines = source.split("\n")
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler) or not is_broad(node):
                continue
            category = classify(node, lines)
            counts[category] += 1
            if category == "A":
                rel = path.relative_to(SRC.parent).as_posix()
                snippet = lines[node.lineno - 1].strip()[:70]
                silent.append((rel, node.lineno, snippet))

    return counts, silent


def read_baseline() -> int:
    if not BASELINE_PATH.exists():
        raise SystemExit(
            f"silent_except_ratchet: baseline ontbreekt ({BASELINE_PATH}).\n"
            "Draai eerst: python scripts/silent_except_ratchet.py --update"
        )
    for line in BASELINE_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            try:
                return int(stripped)
            except ValueError:
                raise SystemExit(
                    f"silent_except_ratchet: baseline bevat geen geldig getal "
                    f"({BASELINE_PATH}): {stripped!r}"
                ) from None
    raise SystemExit("silent_except_ratchet: baseline bevat geen getal")


def write_baseline(count: int) -> None:
    BASELINE_PATH.write_text(
        "# Silent-except baseline (DEF-393) -- aantal brede handlers zonder\n"
        "# logging en zonder re-raise. Mag alleen dalen.\n"
        "# Bijwerken: python scripts/silent_except_ratchet.py --update\n"
        f"{count}\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Silent-except ratchet (DEF-393)")
    parser.add_argument(
        "--update", action="store_true", help="schrijf de huidige telling als baseline"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="sta toe dat --update de baseline VERHOOGT (vereist een reden in de PR)",
    )
    parser.add_argument(
        "--list", action="store_true", help="toon alle stille handlers met locatie"
    )
    args = parser.parse_args()

    counts, silent = scan()
    total = sum(counts.values())
    current = counts["A"]

    print(f"Brede exception handlers in src/: {total}")
    print(f"  C hergooit        {counts['C']:4d}")
    print(f"  B gelogd          {counts['B']:4d}")
    print(f"  D gedocumenteerd  {counts['D']:4d}")
    print(f"  A STIL            {current:4d}  <- getelde schuld")

    if args.list:
        print("\nStille handlers:")
        for rel, lineno, snippet in silent:
            print(f"  {rel}:{lineno}  {snippet}")

    if args.update:
        # De baseline belooft "mag alleen dalen"; dwing dat af.
        if BASELINE_PATH.exists():
            previous = read_baseline()
            if current > previous and not args.force:
                print(
                    f"\nFAIL: --update zou de baseline VERHOGEN "
                    f"({previous} -> {current}).\n"
                    "   Los de nieuwe stille handlers op, markeer ze bewust, of\n"
                    "   gebruik --force met een expliciete reden in de PR.",
                    file=sys.stderr,
                )
                return 1
        write_baseline(current)
        print(f"\nBaseline bijgewerkt naar {current}.")
        return 0

    baseline = read_baseline()
    if current > baseline:
        print(
            f"\nFAIL: stille excepts gegroeid: {current} > baseline {baseline}.\n"
            "   Voeg logging toe, gooi opnieuw, of markeer de vangst bewust met\n"
            "   '# Intentional broad catch: <reden>' direct boven de handler.\n"
            "   Locaties: python scripts/silent_except_ratchet.py --list",
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
