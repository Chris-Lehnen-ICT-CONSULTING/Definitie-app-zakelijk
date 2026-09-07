"""secret_scan_precommit.py — pre-commit-entry voor de secret-scan (DEF-522).

Dunne entry zonder eigen opties: pre-commit start dit script in de
repository-root, en de entry wijst daaruit zelf de scope (die werkmap), de config
(`.gitleaks.toml` in die root), de binary (`gitleaks` op PATH) en een vaste
wachttijd aan. De scan loopt via `secret_scan_gate.main()`, dus er is geen tweede
Gitleaks-caller en geen tweede resultaatvorm.

De omgeving bepaalt welke van de twee bestaande modi draait. Bij een gewone
commit staat er geen bereik in de omgeving en scant de entry de index
(staged-modus): aanvullende lokale feedback, zonder uitspraak over de historie.
Draait pre-commit met `--from-ref`/`--to-ref`, dan zet het zelf
`PRE_COMMIT_FROM_REF` en `PRE_COMMIT_TO_REF`, en draait de entry dezelfde gate in
de volledige modus — range, canonieke historie én werkboom. Dat is het geval in
CI, waar een schone checkout geen index heeft om op te scannen. Er komt geen
derde modus bij.

Aanwezigheid van één van beide namen is genoeg om de volledige modus te eisen,
óók als de waarde leeg is. De grenzen gaan dan ongewijzigd naar de gate, die als
enige beslist of het volledige commit-ID's zijn; een half of onbruikbaar paar
levert daar een vaste foutuitkomst met nonzero op. Er is dus geen pad waarlangs
een onvolledig bereik stil terugvalt op de index.

Kan de invoer niet worden bepaald — geen `gitleaks` op PATH, of een onbruikbare
werkmap — dan gaat er niets half ingevulds naar de gate: die krijgt een lege
argumentenlijst en levert daarvoor haar eigen vaste foutuitkomst met exitcode 1.
Er wordt geen pad geraden en er verlaat geen exceptietekst deze entry.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import secret_scan_gate

#: Vaste wachttijden voor de tool. Lokale feedback op de index moet kort blijven;
#: de volledige modus fetcht en scant twee keer en krijgt daarom dezelfde ruimte
#: als de CI-gate zelf.
_TIMEOUT_STAGED = 60
_TIMEOUT_FULL = 300

#: De configuratie die in de repository-root wordt verwacht.
_CONFIG_NAAM = ".gitleaks.toml"

#: Alleen PATH bepaalt welke binary wordt gebruikt; de gate eist daarna een
#: bestaand, uitvoerbaar en absoluut toolpad.
_TOOL = "gitleaks"

#: De namen die pre-commit zet zodra `--from-ref` én `--to-ref` zijn opgegeven.
_ENV_FROM_REF = "PRE_COMMIT_FROM_REF"
_ENV_TO_REF = "PRE_COMMIT_TO_REF"


def _refpaar() -> tuple[str, str] | None:
    """Het bereik uit de omgeving, of `None` als er geen bereik is aangewezen.

    Alleen de afwezigheid van béíde namen is een gewone commit. Staat er één
    naam, ook met een lege waarde, dan is er een bereik bedoeld en moet de
    volledige modus draaien; de gate keurt de waarden daarna af of goed. Zou een
    lege of halve invulling hier terugvallen op de staged-scan, dan zou een
    schone checkout zonder index groen kunnen worden op nul gescande bytes.
    """
    if not any(naam in os.environ for naam in (_ENV_FROM_REF, _ENV_TO_REF)):
        return None
    return os.environ.get(_ENV_FROM_REF, ""), os.environ.get(_ENV_TO_REF, "")


def _argumenten() -> list[str]:
    """De expliciete invoer voor de gate; alle paden absoluut."""
    binary = shutil.which(_TOOL)
    if binary is None:
        return []
    root = Path.cwd().resolve()
    refpaar = _refpaar()
    volledig = refpaar is not None
    argumenten = [
        "--mode",
        "full" if volledig else "staged",
        "--source",
        str(root),
        "--config",
        str(root / _CONFIG_NAAM),
        "--binary",
        str(Path(binary).resolve()),
        "--timeout",
        str(_TIMEOUT_FULL if volledig else _TIMEOUT_STAGED),
    ]
    if refpaar is None:
        return argumenten
    van, naar = refpaar
    return [*argumenten, "--base", van, "--head", naar]


def main() -> int:
    """Scan de repository-root waarin pre-commit deze entry start."""
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
