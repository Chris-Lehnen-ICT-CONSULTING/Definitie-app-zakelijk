"""DEF-835 — mutatieproef voor de derde gitleaks-uitzondering (v2, zie _mutaties).

Bouwt per mutatie een tijdelijke kopie van de actuele `.gitleaks.toml` waarin
alleen de DEF-835-allowlist naïef is verzwakt, en draait daartegen
`scripts/ci/test_secret_scan_def835_metadata.py`. De repo-config wordt niet
gewijzigd: de module krijgt de kopie via een pytest-plugin die `_PROJECT_CONFIG`
na collectie vervangt. Uitvoer: alleen mutatienaam, exit en testnamen.

Gebruik (vanuit de werkroot, met DEF522_GITLEAKS_BINARY/DEF522_FIXTURE_ROOT):
    .venv/bin/python <dit bestand>
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

WERKROOT = Path.cwd()
CONFIG = WERKROOT / ".gitleaks.toml"
MODULE = "scripts/ci/test_secret_scan_def835_metadata.py"
KOP = "# Uitzondering 3 van 3"


def _splits() -> tuple[str, str]:
    tekst = CONFIG.read_text(encoding="utf-8")
    begin = tekst.index(KOP)
    einde = tekst.index("# Custom rules", begin)
    return tekst[:begin] + "\x00" + tekst[einde:], tekst[begin:einde]


def _vervang(blok: str, oud: str, nieuw: str) -> str:
    assert oud in blok, f"mutatieanker ontbreekt: {oud[:30]!r}"
    return blok.replace(oud, nieuw, 1)


def _mutaties() -> dict[str, str]:
    kader, blok = _splits()
    # v2: zoek pas vanaf de tabelkop; het commentaar erboven noemt dezelfde
    # sleutels en liet v1 midden in de commentaarregels knippen (ongeldige TOML).
    tabel = blok.index("[[allowlists]]")
    paden_begin = blok.index("\npaths = [", tabel) + 1
    paden_einde = blok.index("]\n", paden_begin) + 2
    regex_begin = blok.index('\nregexTarget = "line"', tabel) + 1
    regex_einde = blok.index("]\n", regex_begin) + 2
    varianten = {
        "zonder-uitzondering": "",
        "alleen-pad": blok[:regex_begin] + blok[regex_einde:],
        "alleen-regel": blok[:paden_begin] + blok[paden_einde:],
        "zonder-targetRules": _vervang(blok, 'targetRules = ["generic-api-key"]\n', ""),
        "zonder-eindanker": _vervang(blok, "\",$'''", "\",'''"),
        "zonder-beginanker": _vervang(blok, "'''^\\n?      \"src", "'''      \"src"),
    }
    return {naam: kader.replace("\x00", variant) for naam, variant in varianten.items()}


class _Plugin:
    def __init__(self, config: Path) -> None:
        self.config = config

    def pytest_collection_modifyitems(self, session, config, items) -> None:
        for item in items:
            item.module._PROJECT_CONFIG = self.config


def _toml_geldig(tekst: str) -> str:
    import tomllib

    try:
        tomllib.loads(tekst)
    except tomllib.TOMLDecodeError:
        return "ongeldig"
    return "geldig"


def _een(config: Path) -> int:
    import pytest

    return int(
        pytest.main(
            ["-q", "-p", "no:cacheprovider", "--tb=no", "-rf", MODULE],
            plugins=[_Plugin(config)],
        )
    )


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--een":
        return _een(Path(sys.argv[2]))
    basis = Path(tempfile.mkdtemp(prefix="def835-mutatie-"))
    omgeving = dict(os.environ, PYTEST_ADDOPTS="", PYTEST_PLUGINS="")
    for naam, tekst in _mutaties().items():
        pad = basis / f"{naam}.toml"
        pad.write_text(tekst, encoding="utf-8")
        sys.stdout.write(f"\n=== mutatie {naam} (toml {_toml_geldig(tekst)}) ===\n")
        sys.stdout.flush()
        voltooid = subprocess.run(
            [sys.executable, __file__, "--een", str(pad)],
            cwd=str(WERKROOT),
            env=omgeving,
            check=False,
        )
        sys.stdout.write(f"=== exit {voltooid.returncode} ===\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
