#!/usr/bin/env python3
"""Regressietests voor de EPIC/US-validatiegate (DEF-665).

Hermetisch: standaard-library `unittest` + `subprocess` (plus de al aanwezige
PyYAML om de workflow te lezen), dummy-planningsbestanden in verse tijdelijke
mappen. Geen app-imports, geen conftest, geen netwerk, geen sleutels en geen
echte planningsdocumenten.

Twee groepen:

* `TestEpicValidationGate` draait het nieuwe gate-script als subproces tegen
  dummy-scopes en toetst het publieke contract.
* `TestLegacyInlineStappen` voert de **bestaande** inline blokken uit
  `.github/workflows/epic-validation.yml` uit onder een lege dummy-layout. Dat
  legt het werkelijke defect bloot: de shell-lussen lopen leeg door, melden
  `✅` en eindigen met status 0, en de rapportstap schrijft drie successen die
  niets meten. Die groep is dus echte RED op bestaande code, niet op een
  ontbrekende module.

Fixtures blijven bewust staan (`tempfile.mkdtemp`); er wordt niets verwijderd.

Publiek contract van de gate:
    exit 0 = beide scopes niet leeg en alles geldig
    exit 1 = geldige scan met bevindingen (ontbrekend veld, dubbel ID,
             verwijzing naar een onbekende epic)
    exit 2 = ongeldige scan (ontbrekende of lege scope, onleesbaar bestand,
             misvormde frontmatter)

Belangrijk: met de huidige repository is de juiste uitkomst **2**, want de
EPIC/US-scope ontbreekt. Dat is geen restdefect maar de eerlijke uitslag; deze
suite legt dat vast en verzint geen planningsdata.

Stdout draagt uitsluitend één JSON-rapport met metadata: root, tellingen, exacte
ID's en bevindingen. Nooit bestandsinhoud, nooit rauwe YAML, nooit een traceback.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE = REPO_ROOT / "scripts" / "ci" / "epic_validation_gate.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "epic-validation.yml"
TIMEOUT = 120

#: Staat in de dummy-inhoud en in een kapotte YAML-waarde; mag nooit in de
#: gate-uitvoer belanden.
MARKER = "DEF665-EPIC-MARKER"

EPIC_PAD = "docs/epics/EPIC-1.md"
STORY_PAD = "docs/stories/US-1.md"

#: Het rapport draagt uitsluitend deze sleutels. ID's en epic-verwijzingen zijn
#: vrije frontmatterwaarden en horen er nadrukkelijk niet in.
RAPPORT_SLEUTELS = {
    "gate",
    "status",
    "exit_code",
    "reason",
    "root",
    "counts",
    "findings",
}
BEVINDING_SLEUTELS = {"kind", "path", "field"}

EPIC_VELDEN = {
    "id": "EPIC-1",
    "title": "Dummy epic",
    "status": "draft",
    "owner": "def665",
    "priority": "low",
}
STORY_VELDEN = {
    "id": "US-1",
    "epic": "EPIC-1",
    "title": "Dummy story",
    "status": "draft",
    "priority": "low",
}


def _md(velden: dict[str, str]) -> str:
    regels = "".join(f"{sleutel}: {waarde}\n" for sleutel, waarde in velden.items())
    return f"---\n{regels}---\n\n# {MARKER}\n"


EPIC_GELDIG = _md(EPIC_VELDEN)
STORY_GELDIG = _md(STORY_VELDEN)

#: Niet-afgesloten YAML-lijst; de marker zit in de waarde, zodat een
#: doorgegeven parserfout meteen zichtbaar zou zijn.
KAPOTTE_FRONTMATTER = f"---\nid: [{MARKER}\ntitle: kapot\n---\n"
GEEN_FRONTMATTER = f"# {MARKER}\n\nGeen frontmatter-scheidingstekens.\n"


def _new_dir(prefix: str) -> Path:
    """Verse fixture-map die bewust blijft staan, met canoniek pad."""
    return Path(tempfile.mkdtemp(prefix=f"def665-{prefix}-")).resolve()


def _root(
    *,
    epics: tuple[tuple[str, str | bytes], ...] = (("EPIC-1.md", EPIC_GELDIG),),
    stories: tuple[tuple[str, str | bytes], ...] = (("US-1.md", STORY_GELDIG),),
    maak_epics: bool = True,
    maak_stories: bool = True,
) -> Path:
    """Verse checkout met alleen het gate-script en dummy-planningsbestanden."""
    root = _new_dir("epicroot")
    (root / "scripts" / "ci").mkdir(parents=True)
    if GATE.exists():
        shutil.copy2(GATE, root / "scripts" / "ci" / GATE.name)

    for maak, submap, bestanden in (
        (maak_epics, "docs/epics", epics),
        (maak_stories, "docs/stories", stories),
    ):
        if not maak:
            continue
        doelmap = root / submap
        doelmap.mkdir(parents=True)
        for naam, inhoud in bestanden:
            pad = doelmap / naam
            if isinstance(inhoud, bytes):
                pad.write_bytes(inhoud)
            else:
                pad.write_text(inhoud, encoding="utf-8")
    return root


def _env(thuis: Path) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(thuis),
        "LC_ALL": "C",
        "LANG": "C",
    }


def _run(root: Path, *, werkmap: Path | None = None) -> subprocess.CompletedProcess:
    """Draai de gate vanuit een werkmap die bewust niet de root is."""
    elders = werkmap if werkmap is not None else _new_dir("elders")
    return subprocess.run(
        [sys.executable, str(root / "scripts" / "ci" / GATE.name)],
        cwd=str(elders),
        env=_env(elders),
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )


def _uit(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout or "") + (proc.stderr or "")


def _rapport(proc: subprocess.CompletedProcess) -> dict:
    """Stdout moet één JSON-rapport zijn; anders is er geen bewijs."""
    try:
        data = json.loads(proc.stdout)
    except ValueError as fout:
        raise AssertionError(
            f"stdout is geen JSON-rapport ({fout}); stderr:\n{proc.stderr}"
        ) from None
    assert isinstance(data, dict), data
    return data


def _soorten(rapport: dict) -> set[str]:
    return {bevinding["kind"] for bevinding in rapport["findings"]}


class TestEpicValidationGate(unittest.TestCase):
    """Afwezige scope is ongeldig, nooit een stille groene doorgang."""

    def test_geldige_scopes_zijn_groen_met_exacte_metadata(self):
        root = _root()
        proc = _run(root)
        rapport = _rapport(proc)
        uitvoer = _uit(proc)

        assert proc.returncode == 0, uitvoer
        assert rapport["status"] == "ok", rapport
        assert rapport["exit_code"] == 0, rapport
        assert rapport["root"] == str(root), rapport
        assert rapport["counts"] == {"epics": 1, "stories": 1}, rapport
        assert rapport["findings"] == [], rapport
        assert set(rapport) == RAPPORT_SLEUTELS, sorted(rapport)
        assert MARKER not in uitvoer, "geen bestandsinhoud in het rapport"
        assert "Traceback" not in uitvoer, uitvoer

    def test_ontbrekende_of_lege_scope_is_ongeldig(self):
        gevallen = (
            ("geen epicmap", {"maak_epics": False}),
            ("geen storymap", {"maak_stories": False}),
            ("lege epicmap", {"epics": ()}),
            ("lege storymap", {"stories": ()}),
            ("beide leeg", {"epics": (), "stories": ()}),
        )
        for naam, kwargs in gevallen:
            with self.subTest(naam=naam):
                proc = _run(_root(**kwargs))
                rapport = _rapport(proc)
                assert proc.returncode == 2, _uit(proc)
                assert rapport["status"] == "invalid", rapport
                assert rapport["exit_code"] == 2, rapport
                assert rapport["reason"], "een ongeldige scan noemt haar reden"

    def test_onleesbare_of_misvormde_frontmatter_is_ongeldig(self):
        gevallen = (
            ("kapotte yaml", KAPOTTE_FRONTMATTER),
            ("geen frontmatter", GEEN_FRONTMATTER),
            ("leeg bestand", ""),
            ("geen utf-8", b"---\nid: \xff\xfe\n---\n"),
        )
        for naam, inhoud in gevallen:
            with self.subTest(naam=naam):
                root = _root(epics=(("EPIC-1.md", inhoud),))
                proc = _run(root)
                rapport = _rapport(proc)
                uitvoer = _uit(proc)
                assert proc.returncode == 2, uitvoer
                assert rapport["status"] == "invalid", rapport
                assert MARKER not in uitvoer, "geen rauwe YAML in het rapport"
                assert "Traceback" not in uitvoer, uitvoer

    def test_ontbrekend_verplicht_veld_geeft_bevinding(self):
        for veld in EPIC_VELDEN:
            with self.subTest(soort="epic", veld=veld):
                zonder = {k: v for k, v in EPIC_VELDEN.items() if k != veld}
                root = _root(epics=(("EPIC-1.md", _md(zonder)),))
                proc = _run(root)
                rapport = _rapport(proc)
                assert proc.returncode == 1, _uit(proc)
                assert rapport["status"] == "findings", rapport
                assert any(
                    bevinding["kind"] == "missing_field"
                    and bevinding["field"] == veld
                    and bevinding["path"] == EPIC_PAD
                    for bevinding in rapport["findings"]
                ), rapport

        for veld in STORY_VELDEN:
            with self.subTest(soort="story", veld=veld):
                zonder = {k: v for k, v in STORY_VELDEN.items() if k != veld}
                root = _root(stories=(("US-1.md", _md(zonder)),))
                proc = _run(root)
                rapport = _rapport(proc)
                assert proc.returncode == 1, _uit(proc)
                assert any(
                    bevinding["kind"] == "missing_field"
                    and bevinding["field"] == veld
                    and bevinding["path"] == STORY_PAD
                    for bevinding in rapport["findings"]
                ), rapport

    def test_dubbele_ids_geven_bevinding(self):
        with self.subTest(soort="epic"):
            root = _root(
                epics=(
                    ("EPIC-1.md", EPIC_GELDIG),
                    ("EPIC-1-kopie.md", EPIC_GELDIG),
                )
            )
            proc = _run(root)
            rapport = _rapport(proc)
            assert proc.returncode == 1, _uit(proc)
            assert "duplicate_id" in _soorten(rapport), rapport
            assert rapport["counts"]["epics"] == 2, rapport

        with self.subTest(soort="story"):
            root = _root(
                stories=(
                    ("US-1.md", STORY_GELDIG),
                    ("US-1-kopie.md", STORY_GELDIG),
                )
            )
            proc = _run(root)
            rapport = _rapport(proc)
            assert proc.returncode == 1, _uit(proc)
            assert "duplicate_id" in _soorten(rapport), rapport

    def test_verwijzing_naar_onbekende_epic_geeft_bevinding(self):
        afwijkend = dict(STORY_VELDEN, epic="EPIC-9")
        root = _root(stories=(("US-1.md", _md(afwijkend)),))
        proc = _run(root)
        rapport = _rapport(proc)

        assert proc.returncode == 1, _uit(proc)
        assert rapport["status"] == "findings", rapport
        assert "unknown_epic_reference" in _soorten(rapport), rapport
        for bevinding in rapport["findings"]:
            assert set(bevinding) == BEVINDING_SLEUTELS, bevinding

    def test_ids_en_verwijzingen_verschijnen_niet_in_het_rapport(self):
        """ID's zijn vrije velden; ze worden intern vergeleken, niet gemeld."""
        epic = _md(dict(EPIC_VELDEN, id=f"EPIC-{MARKER}-A"))
        story = _md(dict(STORY_VELDEN, id=f"US-{MARKER}-B", epic=f"EPIC-{MARKER}-C"))
        root = _root(epics=(("EPIC-1.md", epic),), stories=(("US-1.md", story),))
        proc = _run(root)
        rapport = _rapport(proc)
        uitvoer = _uit(proc)

        assert proc.returncode == 1, uitvoer
        assert "unknown_epic_reference" in _soorten(rapport), rapport
        assert MARKER not in uitvoer, "ID's en verwijzingen horen niet in de uitvoer"
        assert set(rapport) == RAPPORT_SLEUTELS, sorted(rapport)

    def test_rapport_meldt_nooit_een_vals_succes(self):
        root = _root(stories=(("US-1.md", _md(dict(STORY_VELDEN, epic="EPIC-9"))),))
        proc = _run(root)
        rapport = _rapport(proc)
        uitvoer = _uit(proc)

        assert rapport["exit_code"] == proc.returncode, (rapport, proc.returncode)
        assert rapport["status"] != "ok", rapport
        assert "✅" not in uitvoer, "geen vaste vinkjes los van de uitkomst"
        assert MARKER not in uitvoer, uitvoer
        assert "Traceback" not in uitvoer, uitvoer

    def test_zelfde_uitkomst_vanuit_verschillende_werkmappen(self):
        root = _root()
        eerste = _rapport(_run(root, werkmap=_new_dir("elders-a")))
        tweede = _rapport(_run(root, werkmap=_new_dir("elders-b")))

        assert eerste == tweede, (eerste, tweede)
        assert eerste["root"] == str(root), eerste


MAKEFILE = REPO_ROOT / "Makefile"

#: Het exacte, onvoorwaardelijke commando van de gatestap. Een vergelijking op de
#: volledige regel weigert een stapnaam, commentaar of `echo` die het commando
#: slechts noemt.
GATECOMMANDO = "make epic-check > validation-report.json"
RAPPORTBESTAND = "validation-report.json"
ARTEFACTNAAM = "validation-report"

WORKFLOW_SJABLOON = """name: Epic and Story Validation

on:
  workflow_dispatch:

jobs:
  validate-structure:
    runs-on: ubuntu-latest

    steps:
{stap}
      - name: Upload Validation Report
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: validation-report
          path: validation-report.json
"""


def _workflow_stappen(pad: Path | None = None) -> list[dict]:
    """De stappen van `jobs.validate-structure`; alleen lezen, niets uitvoeren."""
    document = yaml.safe_load((pad or WORKFLOW).read_text(encoding="utf-8"))
    return document["jobs"]["validate-structure"]["steps"]


def _gatestap(pad: Path | None = None) -> dict:
    """De ene stap die de gedeelde gate onvoorwaardelijk en blokkerend draait."""
    stappen = [
        stap
        for stap in _workflow_stappen(pad)
        if isinstance(stap.get("run"), str) and stap["run"].strip() == GATECOMMANDO
    ]
    assert (
        len(stappen) == 1
    ), f"verwacht precies één stap met exact {GATECOMMANDO!r}: {stappen}"
    stap = stappen[0]
    assert "if" not in stap, stap
    assert stap.get("continue-on-error") in (None, False), stap
    return stap


def _workflow_variant(naam: str, commando: str, voorwaarde: str | None) -> Path:
    regels = [f"      - name: Valideer structuur ({GATECOMMANDO})"]
    if voorwaarde is not None:
        regels.append(f"        if: {voorwaarde}")
    regels.append(f"        run: {commando}")
    pad = _new_dir("workflowvariant") / f"{naam.replace(' ', '-')}.yml"
    pad.write_text(
        WORKFLOW_SJABLOON.format(stap="\n".join(regels) + "\n"), encoding="utf-8"
    )
    return pad


def _make_recept(doel: str) -> str:
    """De receptregels van één Make-doel; puur tekstueel, niets uitgevoerd."""
    recept: list[str] = []
    verzamelen = False
    for regel in MAKEFILE.read_text(encoding="utf-8").splitlines():
        if regel.startswith(f"{doel}:"):
            verzamelen = True
            continue
        if verzamelen:
            if regel.startswith("\t"):
                recept.append(regel)
                continue
            break
    return "\n".join(recept)


class TestWorkflowKoppeling(unittest.TestCase):
    """De workflow moet de gedeelde gate onvoorwaardelijk blijven aanroepen."""

    def test_workflow_roept_de_gedeelde_gate_onvoorwaardelijk_aan(self):
        _gatestap()

        uploads = [
            stap
            for stap in _workflow_stappen()
            if str(stap.get("uses", "")).startswith("actions/upload-artifact@")
        ]
        assert len(uploads) == 1, uploads
        assert uploads[0]["if"] == "always()", uploads[0]
        assert uploads[0]["with"]["name"] == ARTEFACTNAAM, uploads[0]
        assert RAPPORTBESTAND in str(uploads[0]["with"]["path"]), uploads[0]

    def test_stapnaam_of_uitgeschakelde_stap_telt_niet_als_aanroep(self):
        gevallen = (
            ("alleen genoemd", f'echo "{GATECOMMANDO}"', None),
            ("uitgeschakeld", GATECOMMANDO, "false"),
        )
        for naam, commando, voorwaarde in gevallen:
            with self.subTest(naam=naam):
                variant = _workflow_variant(naam, commando, voorwaarde)
                try:
                    _gatestap(variant)
                except AssertionError:
                    continue
                raise AssertionError(f"{naam}: deze variant hoort te worden afgewezen")

    def test_makefile_epic_check_roept_dezelfde_gate_aan(self):
        recept = _make_recept("epic-check")
        assert recept, "make-doel epic-check ontbreekt"
        assert "scripts/ci/epic_validation_gate.py" in recept, recept
        assert "-I" in recept and "-B" in recept, recept

    def test_gedeelde_gate_onderscheidt_gevulde_en_lege_scope(self):
        gevuld = _run(_root())
        assert gevuld.returncode == 0, _uit(gevuld)
        assert _rapport(gevuld)["status"] == "ok", _rapport(gevuld)

        leeg = _run(_root(epics=(), stories=()))
        assert leeg.returncode == 2, _uit(leeg)
        assert _rapport(leeg)["status"] == "invalid", _rapport(leeg)


if __name__ == "__main__":
    unittest.main()
