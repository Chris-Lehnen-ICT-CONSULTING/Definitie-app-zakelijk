#!/usr/bin/env python3
"""Regressietests voor de complexity-ratchet (DEF-665).

Hermetisch: standaard-library `unittest` + `subprocess`, dummy-Pythonbestanden in
verse tijdelijke mappen. Geen app-imports, geen conftest, geen netwerk, geen
echte projectbron en geen wijziging van de echte baseline.

Twee niveaus, met een duidelijke rolverdeling:

* `TestComplexityGate` draait het gate-script als echt subproces tegen de
  geïnstalleerde Ruff. Twee van die tests zetten bewust een nagemaakt
  `ruff`-pakket klaar — één in de repo-root, één via `PYTHONPATH` — en eisen dat
  de echte Ruff tóch de meting doet. Dat is de regressie op de gevonden fout:
  zonder `-I` kan zo'n pakket de tool overschaduwen en een lege, groene meting
  opleveren.
* `TestProtocolViaUnitSeam` laadt uitsluitend `scripts/complexity_ratchet.py`
  via `importlib`, vervangt `subprocess` door een argv-bewuste dubbel en toetst
  daarmee wat een gezonde tool niet oplevert: een signaal en een onbruikbaar of
  tegenstrijdig rapportprotocol. Die gevallen lopen dus via een testnaad, niet
  via een injectiemogelijkheid in de productiecode.

Fixtures blijven bewust staan (`tempfile.mkdtemp`); er wordt niets verwijderd of
opgeruimd. Paden worden gecanonicaliseerd, want op macOS geeft `mkdtemp` een
`/var/...`-alias terwijl de gate haar root via `resolve()` rapporteert.

Publiek contract van de gate:
    exit 0 = geldige scan, aantal op of onder de baseline
    exit 1 = geldige scan, groei boven de baseline
    exit 2 = ongeldige scan (scope, tool, config, I/O, JSON of schema)

Metadata-uitvoer waar de tests op steunen (nooit broncode of rauwe toolfouten):
    complexity-gate: ruff=<versienummer>
    complexity-gate: root=<absoluut pad>
    complexity-gate: selected files=<n>
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "complexity_ratchet.py"
BASELINE_NAAM = "complexity_baseline.txt"
TIMEOUT = 180

#: Staat in dummybron en in een kapotte config; mag nooit in de gate-uitvoer
#: belanden.
MARKER = "DEF665-COMPLEXITY-MARKER"

#: Herkenningspunt van de nagemaakte ruff-module; als die ooit wordt gebruikt,
#: is dat direct zichtbaar in de uitvoer.
FAKE_MARKER = "DEF665-FAKE"
FAKE_VERSIE = "0.0.0"

SCHOON = f"# {MARKER}\ndef f(x: int) -> int:\n    return x\n"

#: Acht returns overschrijdt het standaardmaximum van PLR0911 (zes); de takken
#: en het aantal statements blijven ruim onder C901/PLR0912/PLR0915, dus dit
#: levert precies één bevinding op.
COMPLEX = (
    f"# {MARKER}\n"
    "def g(x: int) -> int:\n"
    + "".join(f"    if x == {n}:\n        return {n}\n" for n in range(1, 8))
    + "    return 0\n"
)

#: Kapotte TOML: de niet-afgesloten array maakt de config onleesbaar. De sleutel
#: draagt de marker, zodat een doorgegeven rauwe toolfout zichtbaar zou worden.
KAPOTTE_CONFIG = f'"{MARKER}" = [\n'

#: Nagemaakte ruff-module die een schone, lege meting voorspiegelt. Zou de gate
#: deze laden, dan meldt zij nul bevindingen en versie 0.0.0.
FAKE_RUFF = f'''\
"""Nagemaakte ruff-module (DEF-665); mag de echte tool nooit overschaduwen."""

import sys

ARGV = sys.argv[1:]

if "--version" in ARGV:
    print("ruff {FAKE_VERSIE}-{FAKE_MARKER}")
    sys.exit(0)

if "--show-files" in ARGV:
    print("src/clean.py")
    sys.exit(0)

sys.stdout.write("[]")
sys.exit(0)
'''


def _new_dir(prefix: str) -> Path:
    """Verse fixture-map die bewust blijft staan, met canoniek pad."""
    return Path(tempfile.mkdtemp(prefix=f"def665-{prefix}-")).resolve()


def _schrijf_fake_pakket(map_: Path) -> Path:
    """Twee bestanden: het minimale pakket dat `-m ruff` zou kunnen laden."""
    pakket = map_ / "ruff"
    pakket.mkdir(parents=True, exist_ok=True)
    (pakket / "__init__.py").write_text("", encoding="utf-8")
    (pakket / "__main__.py").write_text(FAKE_RUFF, encoding="utf-8")
    return map_


def _repo(
    *,
    bronnen: tuple[tuple[str, str], ...] = (("clean.py", SCHOON),),
    baseline: str | None = "0",
    ruff_toml: str | None = None,
    maak_src: bool = True,
    fake_pakket: bool = False,
) -> Path:
    """Verse repo-layout met alleen het gate-script, een baseline en dummybron."""
    root = _new_dir("cxrepo")
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(SCRIPT, scripts / SCRIPT.name)
    if baseline is not None:
        (scripts / BASELINE_NAAM).write_text(baseline, encoding="utf-8")
    if ruff_toml is not None:
        (root / "ruff.toml").write_text(ruff_toml, encoding="utf-8")
    if fake_pakket:
        _schrijf_fake_pakket(root)
    if maak_src:
        (root / "src").mkdir()
        for naam, inhoud in bronnen:
            (root / "src" / naam).write_text(inhoud, encoding="utf-8")
    return root


def _run(
    repo: Path,
    *,
    args: tuple[str, ...] = (),
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Draai de gate vanuit een werkmap die bewust niet de repo-root is."""
    elders = _new_dir("elders")
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(elders),
        "LC_ALL": "C",
        "LANG": "C",
    }
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(repo / "scripts" / SCRIPT.name), *args],
        cwd=str(elders),
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )


def _uit(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout or "") + (proc.stderr or "")


def _baseline_tekst(repo: Path) -> str:
    return (repo / "scripts" / BASELINE_NAAM).read_text(encoding="utf-8").strip()


class TestComplexityGate(unittest.TestCase):
    """Een lege of onbetrouwbare scan mag nooit als "op baseline" doorgaan."""

    def test_schone_scope_wordt_geaccepteerd_met_versie_en_telling(self):
        proc = _run(_repo())
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert "complexity-gate: ruff=" in uitvoer, "toolversie hoort gelogd te worden"
        assert (
            "complexity-gate: selected files=1" in uitvoer
        ), "de werkelijke selectie moet aantoonbaar zijn"

    def test_root_komt_uit_script_niet_uit_werkmap(self):
        repo = _repo()
        proc = _run(repo)
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert (
            f"complexity-gate: root={repo}" in uitvoer
        ), "de root hoort uit het script te komen, niet uit de werkmap"

    def test_ontbrekende_src_is_ongeldig(self):
        proc = _run(_repo(maak_src=False))

        assert proc.returncode == 2, "zonder src is er geen scope, dus geen scan"

    def test_config_die_alles_uitsluit_is_ongeldig(self):
        proc = _run(_repo(ruff_toml='extend-exclude = ["*.py", "src"]\n'))

        assert (
            proc.returncode == 2
        ), "een lege selectie met nul bevindingen mag nooit groen zijn"

    def test_kapotte_config_is_ongeldig_zonder_lek(self):
        proc = _run(_repo(ruff_toml=KAPOTTE_CONFIG))
        uitvoer = _uit(proc)

        assert proc.returncode == 2, uitvoer
        assert MARKER not in uitvoer, "geen rauwe configinhoud in de log"
        assert "Traceback" not in uitvoer, "geen traceback in de log"

    def test_echte_bevinding_boven_baseline_blokkeert(self):
        proc = _run(_repo(bronnen=(("complex.py", COMPLEX),), baseline="0"))
        uitvoer = _uit(proc)

        assert proc.returncode == 1, uitvoer
        assert "complexity-gate: selected files=1" in uitvoer, uitvoer

    def test_gelijk_of_onder_baseline_wordt_geaccepteerd(self):
        for baseline in ("1", "5"):
            with self.subTest(baseline=baseline):
                repo = _repo(bronnen=(("complex.py", COMPLEX),), baseline=baseline)
                proc = _run(repo)
                assert proc.returncode == 0, _uit(proc)

    def test_ongeldige_baseline_is_ongeldig(self):
        gevallen = (
            ("geen getal", "abc"),
            ("negatief", "-3"),
            ("leeg", ""),
            ("ontbrekend bestand", None),
        )
        for naam, inhoud in gevallen:
            with self.subTest(naam=naam):
                proc = _run(_repo(baseline=inhoud))
                assert (
                    proc.returncode == 2
                ), "een onbruikbare baseline mag de gate niet laten slagen"

    def test_update_ratelt_alleen_omlaag(self):
        omlaag = _repo(bronnen=(("complex.py", COMPLEX),), baseline="5")
        proc = _run(omlaag, args=("--update",))
        assert proc.returncode == 0, _uit(proc)
        assert _baseline_tekst(omlaag) == "1", "de baseline hoort omlaag te gaan"

        omhoog = _repo(bronnen=(("complex.py", COMPLEX),), baseline="0")
        proc = _run(omhoog, args=("--update",))
        assert proc.returncode == 1, _uit(proc)
        assert _baseline_tekst(omhoog) == "0", "--update mag nooit verhogen"

    def _bewijs_echte_ruff(self, proc: subprocess.CompletedProcess) -> None:
        uitvoer = _uit(proc)
        assert (
            proc.returncode == 1
        ), "de echte Ruff moet de meting doen en de bevinding blokkeren"
        assert FAKE_MARKER not in uitvoer, "de nagemaakte module is gebruikt"
        assert (
            f"complexity-gate: ruff={FAKE_VERSIE}" not in uitvoer
        ), "de gerapporteerde versie komt van de nagemaakte module"

    def test_nagemaakt_ruff_pakket_in_repo_root_schaduwt_niet(self):
        repo = _repo(bronnen=(("complex.py", COMPLEX),), baseline="0", fake_pakket=True)
        self._bewijs_echte_ruff(_run(repo))

    def test_nagemaakt_ruff_pakket_via_pythonpath_schaduwt_niet(self):
        repo = _repo(bronnen=(("complex.py", COMPLEX),), baseline="0")
        pad = _schrijf_fake_pakket(_new_dir("fakeruff"))
        self._bewijs_echte_ruff(_run(repo, env_extra={"PYTHONPATH": str(pad)}))


def _laad_gate():
    """Laad uitsluitend het gate-script; geen app-imports, geen pakketpad."""
    spec = importlib.util.spec_from_file_location("def665_complexity_ratchet", SCRIPT)
    assert spec and spec.loader, "gate-script moet laadbaar zijn"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestProtocolViaUnitSeam(unittest.TestCase):
    """Wat een gezonde tool niet oplevert, via een testnaad in plaats van een
    injectiemogelijkheid in de productiecode."""

    def _naad(
        self,
        *,
        returncode: int,
        stdout: bytes,
        versie: bytes = b"ruff 0.15.17\n",
        selectie: tuple[str, ...] = ("src/clean.py",),
    ):
        repo = _repo()
        module = _laad_gate()
        module.ROOT = repo
        module.BASELINE_PATH = repo / "scripts" / BASELINE_NAAM

        aanroepen: list[list[str]] = []

        def run(cmd, *args, **kwargs):
            argv = list(cmd)
            aanroepen.append(argv)
            if "--version" in argv:
                return SimpleNamespace(returncode=0, stdout=versie, stderr=b"")
            if "--show-files" in argv:
                data = "".join(f"{pad}\n" for pad in selectie).encode()
                return SimpleNamespace(returncode=0, stdout=data, stderr=b"")
            return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=b"")

        module.subprocess = SimpleNamespace(
            run=run, SubprocessError=subprocess.SubprocessError
        )
        return module, aanroepen

    def test_geldige_nagemaakte_scan_wordt_geaccepteerd(self):
        """Positieve controle: versie, selectie en rapport worden aanvaard."""
        module, aanroepen = self._naad(returncode=0, stdout=b"[]")

        totaal, per_code = module.count_violations()
        assert totaal == 0, totaal
        assert not per_code, per_code
        assert module.read_baseline(module.BASELINE_PATH) == 0
        assert len(aanroepen) == 3, aanroepen

    def test_alle_fasen_draaien_geisoleerd(self):
        module, aanroepen = self._naad(returncode=0, stdout=b"[]")
        module.count_violations()

        assert aanroepen, "er moet werkelijk een tool zijn aangeroepen"
        for argv in aanroepen:
            assert argv[:4] == [sys.executable, "-I", "-B", "-m"], argv
            assert argv[4] == "ruff", argv
        assert any("--version" in argv for argv in aanroepen), aanroepen
        assert any("--show-files" in argv for argv in aanroepen), aanroepen

    def test_toolprotocolfouten_zijn_ongeldig(self):
        gevallen = (
            ("signaal", -9, b""),
            ("status 2", 2, b"[]"),
            ("onbruikbare json", 1, b"niet-json"),
            ("geen lijst", 1, b'{"results": []}'),
            ("schema zonder code", 1, b'[{"filename": "src/clean.py"}]'),
            ("onbekende code", 1, b'[{"code": "E501", "filename": "src/clean.py"}]'),
            (
                "bestand buiten selectie",
                1,
                b'[{"code": "C901", "filename": "src/x.py"}]',
            ),
            (
                "status 0 met bevindingen",
                0,
                b'[{"code": "C901", "filename": "src/clean.py"}]',
            ),
            ("status 1 zonder bevindingen", 1, b"[]"),
        )
        for naam, rc, stdout in gevallen:
            with self.subTest(naam=naam):
                module, aanroepen = self._naad(returncode=rc, stdout=stdout)
                try:
                    module.count_violations()
                except SystemExit as fout:
                    assert fout.code == 2, f"{naam}: {fout.code}"
                else:
                    raise AssertionError(f"{naam}: verwachtte een ongeldige scan")
                assert any(
                    "--show-files" in argv for argv in aanroepen
                ), f"{naam}: versie en selectie moeten eerst zijn aanvaard"

    def test_lege_selectie_en_ongeldige_versie_zijn_ongeldig(self):
        gevallen = (
            ("lege selectie", {"selectie": ()}),
            ("geen ruff-versie", {"versie": b"niet-ruff\n"}),
        )
        for naam, kwargs in gevallen:
            with self.subTest(naam=naam):
                module, _ = self._naad(returncode=0, stdout=b"[]", **kwargs)
                try:
                    module.count_violations()
                except SystemExit as fout:
                    assert fout.code == 2, f"{naam}: {fout.code}"
                else:
                    raise AssertionError(f"{naam}: verwachtte een ongeldige scan")


if __name__ == "__main__":
    unittest.main()
