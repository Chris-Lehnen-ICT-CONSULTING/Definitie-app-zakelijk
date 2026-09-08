#!/usr/bin/env python3
"""Regressietests voor de Semgrep-gate (DEF-665).

Hermetisch: standaard-library `unittest` + `subprocess`, dummybron en
dummyrapporten in verse tijdelijke mappen, en een gecontroleerde PATH zonder de
echte Semgrep. Geen app-imports, geen conftest, geen netwerk, geen echte
projectbron en geen echte SAST-run.

De nagemaakte `semgrep` legt elke aanroep vast (werkmap plus argv), zodat de
positieve controle kan bewijzen dát de tool met de vaste vlaggenset is
aangeroepen — en zodat elke negatieve scanfase-test kan aantonen dat zij de
scanfase werkelijk bereikt en niet al eerder omvalt.

Fixtures blijven bewust staan (`tempfile.mkdtemp`); er wordt niets verwijderd of
opgeruimd.

Publiek contract van de gate:
    exit 0 = geldige scan, geaccepteerd (advisory-bevindingen toegestaan)
    exit 1 = geldige scan, ERROR-bevinding in src/
    exit 2 = ongeldige scan (tool, status, JSON, schema, scope of I/O)

Metadata-uitvoer waar de tests op steunen (nooit meldingen, snippets of bron):
    semgrep-gate: semgrep=<versie>
    semgrep-gate: root=<absoluut pad>
    semgrep-gate: scanned total=<n> src=<n>
    semgrep-gate: blocking findings=<n>
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE = REPO_ROOT / "scripts" / "ci" / "semgrep_gate.py"
TIMEOUT = 120

#: Staat in dummybron, in meldingen en in snippets; mag nooit in de gate-uitvoer
#: belanden.
MARKER = "DEF665-SEMGREP-MARKER"

VERSIE = "1.176.1"
DUMMY_SRC = f"# {MARKER}\nvalue = 1\n"
DUMMY_WORKFLOW = "naam: dummy\n"

#: Nagemaakte semgrep met een volledige interpreter-shebang, zodat een gestripte
#: omgeving haar niet onbruikbaar maakt.
FAKE_SEMGREP = f'''#!{sys.executable}
"""Nagemaakte semgrep (DEF-665); alleen voor gatetests."""

import json
import os
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
with (DIR / "calls.log").open("a", encoding="utf-8") as bestand:
    bestand.write(
        json.dumps({{"cwd": os.getcwd(), "argv": sys.argv[1:]}}) + "\\n"
    )

if "--version" in sys.argv[1:]:
    sys.stdout.write((DIR / "version.out").read_text(encoding="utf-8"))
    sys.exit(int((DIR / "version.rc").read_text(encoding="utf-8")))

rapport = DIR / "report.out"
if rapport.exists():
    sys.stdout.write(rapport.read_text(encoding="utf-8"))
sys.exit(int((DIR / "scan.rc").read_text(encoding="utf-8")))
'''


def _new_dir(prefix: str) -> Path:
    """Verse fixture-map die bewust blijft staan, met canoniek pad."""
    return Path(tempfile.mkdtemp(prefix=f"def665-{prefix}-")).resolve()


def _write_exec(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _fake_semgrep(
    *,
    version: str = f"{VERSIE}\n",
    version_rc: int = 0,
    report: object | None = None,
    scan_rc: int = 0,
) -> Path:
    d = _new_dir("fakesemgrep")
    _write_exec(d / "semgrep", FAKE_SEMGREP)
    (d / "version.out").write_text(version, encoding="utf-8")
    (d / "version.rc").write_text(str(version_rc), encoding="utf-8")
    (d / "scan.rc").write_text(str(scan_rc), encoding="utf-8")
    if report is not None:
        inhoud = report if isinstance(report, str) else json.dumps(report)
        (d / "report.out").write_text(inhoud, encoding="utf-8")
    return d


def _leeg_bin() -> Path:
    """Gecontroleerde PATH zonder semgrep."""
    return _new_dir("leegbin")


def _repo(
    *,
    bronnen: tuple[tuple[str, str], ...] = (("app.py", DUMMY_SRC),),
    extra: tuple[tuple[str, str], ...] = (),
    maak_src: bool = True,
    stale_rapport: object | None = None,
) -> Path:
    """Verse repo-layout met alleen het gate-script en dummybestanden."""
    root = _new_dir("sgrepo")
    (root / "scripts" / "ci").mkdir(parents=True)
    shutil.copy2(GATE, root / "scripts" / "ci" / GATE.name)

    if maak_src:
        (root / "src").mkdir()
        for naam, inhoud in bronnen:
            doel = root / "src" / naam
            doel.parent.mkdir(parents=True, exist_ok=True)
            doel.write_text(inhoud, encoding="utf-8")
    for pad, inhoud in extra:
        doel = root / pad
        doel.parent.mkdir(parents=True, exist_ok=True)
        doel.write_text(inhoud, encoding="utf-8")
    if stale_rapport is not None:
        (root / "semgrep-results.json").write_text(
            json.dumps(stale_rapport), encoding="utf-8"
        )
    return root


def _rapport(
    *,
    version: str = VERSIE,
    results: tuple = (),
    errors: tuple = (),
    scanned: tuple = ("src/app.py",),
    aanvulling: dict | None = None,
) -> dict:
    rapport: dict = {
        "version": version,
        "results": list(results),
        "errors": list(errors),
        "paths": {"scanned": list(scanned)},
    }
    if aanvulling:
        rapport.update(aanvulling)
    return rapport


def _bevinding(
    *,
    path: str = "src/app.py",
    severity: str = "ERROR",
    check_id: str = "rules.dummy.regel",
    line: int = 1,
) -> dict:
    return {
        "check_id": check_id,
        "path": path,
        "start": {"line": line},
        "end": {"line": line},
        "extra": {"severity": severity, "message": MARKER, "lines": MARKER},
    }


def _run(repo: Path, bindir: Path) -> subprocess.CompletedProcess:
    """Draai de gate vanuit een werkmap die bewust niet de repo-root is."""
    elders = _new_dir("elders")
    env = {
        "PATH": str(bindir),
        "HOME": str(elders),
        "LC_ALL": "C",
        "LANG": "C",
    }
    return subprocess.run(
        [sys.executable, str(repo / "scripts" / "ci" / GATE.name)],
        cwd=str(elders),
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )


def _uit(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout or "") + (proc.stderr or "")


def _aanroepen(bindir: Path) -> list[dict]:
    log = bindir / "calls.log"
    if not log.exists():
        return []
    return [
        json.loads(regel)
        for regel in log.read_text(encoding="utf-8").splitlines()
        if regel.strip()
    ]


def _scan_gedraaid(bindir: Path) -> bool:
    return any("scan" in aanroep["argv"] for aanroep in _aanroepen(bindir))


class TestSemgrepGate(unittest.TestCase):
    """Een onbetrouwbaar rapport mag nooit als schone scan doorgaan."""

    def test_schone_scan_wordt_geaccepteerd_met_vaste_vlaggen(self):
        repo = _repo()
        bindir = _fake_semgrep(report=_rapport(aanvulling={"skipped_rules": []}))
        proc = _run(repo, bindir)
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert f"semgrep-gate: semgrep={VERSIE}" in uitvoer, uitvoer
        assert f"semgrep-gate: root={json.dumps(str(repo))}" in uitvoer, uitvoer
        assert "semgrep-gate: scanned total=1 src=1" in uitvoer, uitvoer

        scans = [a for a in _aanroepen(bindir) if "scan" in a["argv"]]
        assert len(scans) == 1, scans
        argv = scans[0]["argv"]
        for vlag in (
            "scan",
            "--config",
            "p/owasp-top-ten",
            "p/python",
            "--metrics=off",
            "--json",
            "--strict",
            "--oss-only",
            "--disable-version-check",
            ".",
        ):
            assert vlag in argv, (vlag, argv)
        assert scans[0]["cwd"] == str(repo), scans[0]

    def test_error_in_src_blokkeert_zonder_lek(self):
        repo = _repo()
        bindir = _fake_semgrep(report=_rapport(results=(_bevinding(),)))
        proc = _run(repo, bindir)
        uitvoer = _uit(proc)

        assert proc.returncode == 1, uitvoer
        assert MARKER not in uitvoer, "geen meldingen of snippets in de log"
        assert "Traceback" not in uitvoer, uitvoer

    def test_advisory_bevindingen_blokkeren_niet(self):
        gevallen = (
            ("ERROR buiten src", ".github/workflows/ci.yml", "ERROR"),
            ("WARNING in src", "src/app.py", "WARNING"),
            ("INFO in src", "src/app.py", "INFO"),
            ("MEDIUM in src", "src/app.py", "MEDIUM"),
        )
        for naam, pad, severity in gevallen:
            with self.subTest(naam=naam):
                repo = _repo(extra=((".github/workflows/ci.yml", DUMMY_WORKFLOW),))
                bindir = _fake_semgrep(
                    report=_rapport(
                        results=(_bevinding(path=pad, severity=severity),),
                        scanned=("src/app.py", ".github/workflows/ci.yml"),
                    )
                )
                proc = _run(repo, bindir)
                assert proc.returncode == 0, _uit(proc)

    def test_onbekende_of_misvormde_severity_is_ongeldig(self):
        gevallen = (
            ("onbekend", "CRITICAL"),
            ("lijst", ["ERROR"]),
            ("object", {"niveau": "ERROR"}),
            ("ontbreekt", None),
        )
        for naam, severity in gevallen:
            with self.subTest(naam=naam):
                bevinding = _bevinding()
                bevinding["extra"]["severity"] = severity
                bindir = _fake_semgrep(report=_rapport(results=(bevinding,)))
                proc = _run(_repo(), bindir)
                uitvoer = _uit(proc)
                assert proc.returncode == 2, uitvoer
                assert "Traceback" not in uitvoer, uitvoer
                assert _scan_gedraaid(bindir)

    def test_gefaalde_scan_meldt_veilige_foutmetadata(self):
        """`--strict` eindigt nonzero bij waarschuwingen; de locaties blijven."""
        bindir = _fake_semgrep(
            report=_rapport(
                errors=(
                    {
                        "level": "warn",
                        "type": "PartialParsing",
                        "code": 3,
                        "path": "src/app.py",
                        "start": {"line": 7},
                        "message": MARKER,
                    },
                )
            ),
            scan_rc=1,
        )
        proc = _run(_repo(), bindir)
        uitvoer = _uit(proc)

        assert proc.returncode == 2, uitvoer
        assert "semgrep-gate: scan errors=1" in uitvoer, uitvoer
        assert 'type="PartialParsing"' in uitvoer, uitvoer
        assert 'path="src/app.py"' in uitvoer, uitvoer
        assert "line=7" in uitvoer, uitvoer
        assert MARKER not in uitvoer, "geen rauwe melding in de log"

    def test_vrije_tekst_in_foutmetadata_vervalt(self):
        bindir = _fake_semgrep(
            report=_rapport(
                errors=(
                    {
                        "level": f"warn {MARKER}",
                        "type": f"Partial {MARKER}",
                        "code": "3",
                        "message": MARKER,
                    },
                )
            ),
            scan_rc=1,
        )
        proc = _run(_repo(), bindir)
        uitvoer = _uit(proc)

        assert proc.returncode == 2, uitvoer
        assert MARKER not in uitvoer, "vrije tekst hoort niet in de log"
        for veld in ("code=null", "level=null", "type=null"):
            assert veld in uitvoer, (veld, uitvoer)

    def test_ontbrekende_tool_of_versiefout_is_ongeldig(self):
        with self.subTest(naam="geen executable"):
            proc = _run(_repo(), _leeg_bin())
            assert proc.returncode == 2, _uit(proc)

        gevallen = (
            ("versie faalt", {"version_rc": 1}),
            ("geen versieregel", {"version": "niet-semgrep\n"}),
        )
        for naam, kwargs in gevallen:
            with self.subTest(naam=naam):
                bindir = _fake_semgrep(report=_rapport(), **kwargs)
                proc = _run(_repo(), bindir)
                assert proc.returncode == 2, _uit(proc)

    def test_afwijkende_rapportversie_is_ongeldig(self):
        bindir = _fake_semgrep(report=_rapport(version="9.9.9"))
        proc = _run(_repo(), bindir)

        assert proc.returncode == 2, "rapportversie moet met --version overeenkomen"
        assert _scan_gedraaid(bindir)

    def test_toolstatussen_anders_dan_nul_zijn_ongeldig(self):
        for rc in (1, 2, 3, 137):
            with self.subTest(rc=rc):
                bindir = _fake_semgrep(report=_rapport(), scan_rc=rc)
                proc = _run(_repo(), bindir)
                assert proc.returncode == 2, _uit(proc)
                assert _scan_gedraaid(bindir)

    def test_onbruikbare_json_is_ongeldig(self):
        gevallen = (
            ("geen uitvoer", None),
            ("geen json", "niet-json"),
            ("lijst in plaats van object", "[]"),
        )
        for naam, rapport in gevallen:
            with self.subTest(naam=naam):
                bindir = _fake_semgrep(report=rapport)
                proc = _run(_repo(), bindir)
                assert proc.returncode == 2, _uit(proc)
                assert _scan_gedraaid(bindir)

    def test_oud_rapportbestand_telt_niet_als_bewijs(self):
        repo = _repo(stale_rapport=_rapport())
        bindir = _fake_semgrep(report=None)
        proc = _run(repo, bindir)

        assert (
            proc.returncode == 2
        ), "een achtergebleven semgrep-results.json is geen verse scan"
        assert _scan_gedraaid(bindir)

    def test_ontbrekende_sleutels_of_verkeerde_typen_zijn_ongeldig(self):
        for sleutel in ("version", "results", "errors", "paths"):
            with self.subTest(naam=f"mist {sleutel}"):
                rapport = _rapport()
                del rapport[sleutel]
                bindir = _fake_semgrep(report=rapport)
                assert _run(_repo(), bindir).returncode == 2

        typefouten = (
            ("results geen lijst", {"results": {}}),
            ("errors geen lijst", {"errors": {}}),
            ("paths geen object", {"paths": []}),
            ("scanned geen lijst", {"paths": {"scanned": "src/app.py"}}),
            ("version geen tekst", {"version": 1}),
            ("skipped_rules is null", {"skipped_rules": None}),
        )
        for naam, aanvulling in typefouten:
            with self.subTest(naam=naam):
                bindir = _fake_semgrep(report=_rapport(aanvulling=aanvulling))
                proc = _run(_repo(), bindir)
                assert proc.returncode == 2, _uit(proc)
                assert _scan_gedraaid(bindir)

    def test_gescande_paden_moeten_kloppen(self):
        gevallen = (
            ("niets gescand", ()),
            ("alleen niet-src", (".github/workflows/ci.yml",)),
            ("bestaat niet", ("src/ontbreekt.py",)),
            ("ontsnapt uit root", ("src/app.py", "../buiten.py")),
            ("absoluut pad", ("src/app.py", "/etc/passwd")),
            ("dubbel pad", ("src/app.py", "./src/app.py")),
            ("nulbyte in pad", ("src/app.py", "src/\x00app.py")),
            ("geen tekst", ("src/app.py", 3)),
        )
        for naam, scanned in gevallen:
            with self.subTest(naam=naam):
                repo = _repo(extra=((".github/workflows/ci.yml", DUMMY_WORKFLOW),))
                bindir = _fake_semgrep(report=_rapport(scanned=scanned))
                proc = _run(repo, bindir)
                uitvoer = _uit(proc)
                assert proc.returncode == 2, uitvoer
                assert "Traceback" not in uitvoer, uitvoer
                assert _scan_gedraaid(bindir)

    def test_symlinklus_in_gescand_pad_is_ongeldig(self):
        repo = _repo()
        (repo / "lus").symlink_to(repo / "lus")
        bindir = _fake_semgrep(report=_rapport(scanned=("src/app.py", "lus/x.py")))
        proc = _run(repo, bindir)
        uitvoer = _uit(proc)

        assert proc.returncode == 2, uitvoer
        assert "Traceback" not in uitvoer, uitvoer
        assert _scan_gedraaid(bindir)

    def test_src_als_symlink_is_ongeldig(self):
        repo = _repo(maak_src=False)
        (repo / "echte_bron").mkdir()
        (repo / "echte_bron" / "app.py").write_text(DUMMY_SRC, encoding="utf-8")
        (repo / "src").symlink_to(repo / "echte_bron")
        bindir = _fake_semgrep(report=_rapport())
        proc = _run(repo, bindir)

        assert proc.returncode == 2, _uit(proc)
        assert not _scan_gedraaid(bindir), "de scope wordt vóór de scan getoetst"

    def test_scanfouten_en_overgeslagen_regels_zijn_ongeldig(self):
        gevallen = (
            (
                "fatale fout",
                {"errors": ({"level": "error", "code": 2, "message": MARKER},)},
            ),
            (
                "waarschuwing PartialParsing",
                {
                    "errors": (
                        {
                            "level": "warn",
                            "type": "PartialParsing",
                            "path": "src/app.py",
                            "message": MARKER,
                        },
                    )
                },
            ),
            (
                "type als lijst",
                {"errors": ({"level": "warn", "type": ["PartialParsing", 3]},)},
            ),
        )
        for naam, kwargs in gevallen:
            with self.subTest(naam=naam):
                bindir = _fake_semgrep(report=_rapport(**kwargs))
                proc = _run(_repo(), bindir)
                uitvoer = _uit(proc)
                assert proc.returncode == 2, uitvoer
                assert MARKER not in uitvoer, "geen rauwe foutmelding in de log"
                assert _scan_gedraaid(bindir)

        with self.subTest(naam="overgeslagen regels"):
            bindir = _fake_semgrep(
                report=_rapport(
                    aanvulling={"skipped_rules": [{"rule_id": "rules.kapot"}]}
                )
            )
            proc = _run(_repo(), bindir)
            assert proc.returncode == 2, _uit(proc)
            assert _scan_gedraaid(bindir)

    def test_misvormde_bevinding_is_ongeldig(self):
        gevallen = (
            ("geen check_id", {"check_id": None}),
            ("pad buiten de scan", {"path": "src/onbekend.py"}),
            ("regel nul", {"start": {"line": 0}}),
            ("start geen object", {"start": []}),
            ("extra geen object", {"extra": "ERROR"}),
        )
        for naam, aanpassing in gevallen:
            with self.subTest(naam=naam):
                bevinding = _bevinding()
                bevinding.update(aanpassing)
                bindir = _fake_semgrep(report=_rapport(results=(bevinding,)))
                proc = _run(_repo(), bindir)
                assert proc.returncode == 2, _uit(proc)
                assert _scan_gedraaid(bindir)

    def test_ontbrekende_src_scope_is_ongeldig(self):
        gevallen = (
            ("geen src", {"maak_src": False}),
            ("lege bronnenmap", {"bronnen": ()}),
        )
        for naam, kwargs in gevallen:
            with self.subTest(naam=naam):
                bindir = _fake_semgrep(report=_rapport())
                proc = _run(_repo(**kwargs), bindir)
                assert proc.returncode == 2, _uit(proc)
                assert not _scan_gedraaid(
                    bindir
                ), "de scope wordt vóór de scan gecontroleerd"


if __name__ == "__main__":
    unittest.main()
