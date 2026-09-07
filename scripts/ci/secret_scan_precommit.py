"""secret_scan_precommit.py — pre-commit-entry voor de staged scan (DEF-522).

Dunne entry zonder eigen opties: pre-commit start dit script in de
repository-root, en de entry wijst daaruit zelf de scope (die werkmap), de config
(`.gitleaks.toml` in die root), de binary (`gitleaks` op PATH) en een vaste
wachttijd aan. De scan loopt via `secret_scan_gate.main()` in de staged-modus,
dus er is geen tweede Gitleaks-caller en geen tweede resultaatvorm.

Kan die invoer niet worden bepaald — geen `gitleaks` op PATH, of een onbruikbare
werkmap — dan gaat er niets half ingevulds naar de gate: die krijgt een lege
argumentenlijst en levert daarvoor haar eigen vaste foutuitkomst met exitcode 1.
Er wordt geen pad geraden en er verlaat geen exceptietekst deze entry.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import secret_scan_gate

#: Vaste wachttijd voor de tool; lokale feedback moet kort blijven.
_TIMEOUT_SECONDEN = 60

#: De configuratie die in de repository-root wordt verwacht.
_CONFIG_NAAM = ".gitleaks.toml"

#: Alleen PATH bepaalt welke binary wordt gebruikt; de gate eist daarna een
#: bestaand, uitvoerbaar en absoluut toolpad.
_TOOL = "gitleaks"


def _argumenten() -> list[str]:
    """De expliciete invoer voor de gate; alle paden absoluut."""
    binary = shutil.which(_TOOL)
    if binary is None:
        return []
    root = Path.cwd().resolve()
    return [
        "--mode",
        "staged",
        "--source",
        str(root),
        "--config",
        str(root / _CONFIG_NAAM),
        "--binary",
        str(Path(binary).resolve()),
        "--timeout",
        str(_TIMEOUT_SECONDEN),
    ]


def main() -> int:
    """Scan de index van de repository-root waarin pre-commit deze entry start."""
    # Fail-closed buitengrens: is de invoer niet te bepalen, dan gaat er een lege
    # lijst naar de gate, die daarvoor haar eigen vaste foutuitkomst heeft. Zo
    # verlaat er nooit exceptietekst met pad- of omgevingsdetails deze entry.
    try:
        argumenten = _argumenten()
    except Exception:
        argumenten = []
    return secret_scan_gate.main(argumenten)


if __name__ == "__main__":
    raise SystemExit(main())
