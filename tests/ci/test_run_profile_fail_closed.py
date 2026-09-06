"""Fail-closed-contracten voor de canonieke testrunner (DEF-519).

Waarom deze suite bestaat
-------------------------
`scripts/testing/run_profile.py` is de enige poort waarlangs de drie verplichte
gates draaien. De rootbatch (`root-gate-boundaries-nhyhq6ll/result.json`) toonde
twee paden waarlangs die poort *groen* meldde zonder dat er ooit een beschermde
test is uitgevoerd:

* een `conftest.py` die vóór het schrijven van de rapporten afbreekt levert
  ``status=ok`` met ``verzameld=0``;
* een doorgegeven ``--collect-only`` levert ``status=ok`` terwijl geen enkele
  testbody is uitgevoerd.

Deze tests leggen het omgekeerde contract vast: de runner meldt alleen succes
als er een geldige inventaris is, bewijs dat de offline-bootstrap actief was, én
minstens één werkelijk uitgevoerde, niet-overgeslagen testcall.

Veiligheidsontwerp
------------------
* Elke fixture is een vers, synthetisch miniproject in `tmp_path`. Nooit de
  echte suite, nooit gebruikersdata, nooit netwerk.
* De échte runner wordt in kindprocessen aangeroepen, altijd met een harde
  buitendeadline (`timeout=`), zodat een regressie deze suite niet kan laten
  hangen.
* Geen enkele test leest ongetrackte incidentartefacten of resten van een
  lokale checkout; alles wordt hier aangemaakt.
* Geërfde omgevingswaarden worden nooit geprint.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests import offline_bootstrap

pytestmark = [pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "scripts" / "testing" / "run_profile.py"

#: Synthetische sleutel: de vórm van een providerkey, zonder geldige waarde.
SYNTHETISCHE_KEY = "sk-ant-api03-DEF519-SYNTHETISCH-GEEN-ECHTE-SLEUTEL"


def _runner_module():
    """Laad de échte runner als module om zijn gegenereerde bronnen te toetsen."""
    spec = importlib.util.spec_from_file_location("def519_run_profile", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _kindomgeving(**extra: str) -> dict[str, str]:
    """Omgeving voor een kindproces: precies wat de runner moet neutraliseren.

    De startupinstallatie van een omhullende run gaat eruit: draait deze suite
    zélf onder `run_profile.py`, dan staat diens sessieroot met een gegenereerde
    `sitecustomize.py` op ``PYTHONPATH``. De geteste runner moet zijn eigen
    bootstrap zetten en zijn eigen sessieroot bewijzen, niet die van de ouder
    erven.
    """
    env = offline_bootstrap.omgeving_zonder_startupinstallatie()
    env["ANTHROPIC_API_KEY"] = SYNTHETISCHE_KEY
    env["OPENAI_API_KEY"] = SYNTHETISCHE_KEY
    env["ALLOW_NETWORK"] = "1"
    for naam in ("DEFINITIE_DISABLE_DOTENV", "DEF519_SESSION_ROOT", "PYTEST_ADDOPTS"):
        env.pop(naam, None)
    env.update(extra)
    return env


def _mini_project(tmp_path: Path, bestanden: dict[str, str]) -> Path:
    """Bouw een vers, synthetisch pytest-project (nooit de echte suite)."""
    root = tmp_path / "miniproject"
    (root / "tests").mkdir(parents=True)
    (root / "pytest.ini").write_text(
        "[pytest]\ntestpaths = tests\naddopts = -q\n"
        "markers =\n    unit: unit\n    integration: integration\n"
        "    acceptance: acceptance\n    smoke: smoke\n    slow: slow\n",
        encoding="utf-8",
    )
    for naam, inhoud in bestanden.items():
        pad = root / naam
        pad.parent.mkdir(parents=True, exist_ok=True)
        pad.write_text(inhoud, encoding="utf-8")
    return root


#: Eén echt slagende unittest — de positieve controle van deze suite.
#:
#: Bestandsnaam en testnaam staan apart omdat de node-id hieronder uit precies
#: deze twee wordt samengesteld. Een voluit genoteerde bestandsnaam-plus-
#: nodeketen zou de verwijzingsguard van DEF-676
#: (tests/unit/validation/test_verwijzingen_bestaan.py) als een belofte over
#: déze repository lezen — terwijl het bestand pas in `tmp_path` ontstaat en
#: hier dus terecht niet bestaat. Afleiden houdt de fixture en haar node-id
#: bovendien vanzelf synchroon.
GEZOND_BESTAND = "tests/test_gezond.py"
GEZONDE_TEST = "test_slaagt"
GEZONDE_SUITE = {
    GEZOND_BESTAND: (
        f"import pytest\n\n@pytest.mark.unit\ndef {GEZONDE_TEST}():\n    assert True\n"
    )
}

#: Node-id van de synthetische fixture hierboven, afgeleid uit die fixture zelf.
GEZONDE_NODE = f"{GEZOND_BESTAND}::{GEZONDE_TEST}"


def _uitvoer(resultaat: subprocess.CompletedProcess) -> str:
    return resultaat.stdout + resultaat.stderr


def _draai_runner(
    root: Path, *args: str, timeout: int = 180
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUNNER), "--project-root", str(root), *args],
        cwd=str(REPO_ROOT),
        env=_kindomgeving(),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _status(resultaat: subprocess.CompletedProcess) -> str:
    """De gemelde status van de runner, of '' als er geen statusregel is."""
    for regel in _uitvoer(resultaat).splitlines():
        if regel.startswith("[run_profile] status="):
            return regel.split("status=", 1)[1].split(" ", 1)[0]
    return ""


# --- Positieve controle -----------------------------------------------------


def test_gezonde_run_blijft_groen(tmp_path):
    """Regressievangnet: een echte, slagende run moet groen blijven."""
    root = _mini_project(tmp_path, GEZONDE_SUITE)
    inventaris = tmp_path / "inventaris.json"
    resultaat = _draai_runner(root, "unit", "--inventory", str(inventaris))
    assert resultaat.returncode == 0, _uitvoer(resultaat)
    assert _status(resultaat) == "ok"
    data = json.loads(inventaris.read_text(encoding="utf-8"))
    assert len(data["items"]) == 1, data
    assert data["uitgevoerd"] == 1, data


#: Miniproject voor de slow-scope. Bestands- en testnamen staan apart zodat de
#: node-ids hieronder eruit worden afgeleid (zelfde reden als bij GEZOND_BESTAND).
SLOW_MODULE = "tests/def519_rekenmodule.py"
SLOW_MODULE_FUNCTIE = "som_van_regels"
SNEL_BESTAND = "tests/test_unit_snel.py"
SNELLE_TEST = "test_snelle_unitnode"
TRAAG_BESTAND = "tests/test_unit_traag.py"
TRAGE_TEST = "test_trage_unitnode_roept_module_aan"

#: Alleen de trage node importeert en gebruikt deze module. Draait die node niet,
#: dan blijven deze regels aantoonbaar ongedekt in het coveragerapport.
SLOW_SUITE = {
    SLOW_MODULE: (
        f"def {SLOW_MODULE_FUNCTIE}(getallen):\n"
        '    """Telt op en verdubbelt; echte uitvoering, geen constante."""\n'
        "    totaal = 0\n"
        "    for getal in getallen:\n"
        "        totaal += getal\n"
        "    return totaal * 2\n"
    ),
    SNEL_BESTAND: (
        "import pytest\n\n"
        f"@pytest.mark.unit\ndef {SNELLE_TEST}():\n"
        "    assert True\n"
    ),
    TRAAG_BESTAND: (
        "import pytest\n\n"
        f"from def519_rekenmodule import {SLOW_MODULE_FUNCTIE}\n\n"
        "@pytest.mark.unit\n@pytest.mark.slow\n"
        f"def {TRAGE_TEST}():\n"
        f"    assert {SLOW_MODULE_FUNCTIE}([1, 2, 3, 4]) == 20\n"
    ),
}

SNELLE_NODE = f"{SNEL_BESTAND}::{SNELLE_TEST}"
TRAGE_NODE = f"{TRAAG_BESTAND}::{TRAGE_TEST}"


def _geraakte_regels(xml_pad: Path, bestandsnaam: str) -> int:
    """Aantal geraakte regels van `bestandsnaam` in een coverage-XML."""
    import xml.etree.ElementTree as ET

    wortel = ET.parse(xml_pad).getroot()
    for klasse in wortel.iter("class"):
        if Path(klasse.get("filename", "")).name != bestandsnaam:
            continue
        return sum(
            1 for regel in klasse.iter("line") if int(regel.get("hits", "0")) > 0
        )
    return 0


def test_unit_profiel_voert_slow_daadwerkelijk_uit(tmp_path):
    """Het unitprofiel moet slow-unittests werkelijk verzamelen en uitvoeren.

    Geen coveragevlaggen: deze node meet uitvoering, niet dekking. De trage node
    importeert een eigen module en asserteert haar echte returnwaarde, dus een
    geslaagde run bewijst dat die body heeft gedraaid — een gedeselecteerde node
    zou nooit `uitgevoerd` verhogen.

    Met het oude profiel (`unit and not slow`) valt de trage node uit de
    collectie: de inventaris bevat dan één node en `uitgevoerd` is 1.

    Binnendeadline 45s onder de buitendeadline 90s. Niets wordt verwijderd; alle
    artefacten blijven in `tmp_path`.
    """
    root = _mini_project(tmp_path, SLOW_SUITE)
    inventaris = tmp_path / "uitvoering-inventaris.json"

    resultaat = _draai_runner(
        root,
        "unit",
        "--inventory",
        str(inventaris),
        "--budget",
        "45",
        timeout=90,
    )

    assert resultaat.returncode == 0, _uitvoer(resultaat)
    assert _status(resultaat) == "ok", _uitvoer(resultaat)

    data = json.loads(inventaris.read_text(encoding="utf-8"))
    verzameld = {item["nodeid"] for item in data["items"]}
    assert verzameld == {SNELLE_NODE, TRAGE_NODE}, data
    assert data["uitgevoerd"] == 2, data
    assert data["overgeslagen"] == 0, data
    assert data["collectiefouten"] == 0, data


def test_unit_profiel_voert_slow_uit_en_meet_coverage(tmp_path):
    """Het unitprofiel moet slow-unittests écht uitvoeren en meetellen.

    De gate draait op `alle unit inclusief slow`. Filtert het profiel `slow`
    weg, dan wordt de trage node niet verzameld, blijft haar module
    ongeimporteerd en registreert het coveragerapport nul geraakte regels voor
    die module. Deze test faalt in dat geval op alle drie de fronten:
    node-inventaris, uitgevoerde bodies en werkelijke dekking.

    De binnendeadline (45s) ligt bewust onder de buitendeadline (90s), zodat de
    runner zelf afbreekt voordat het kindproces hier hard wordt afgekapt. Er
    wordt niets verwijderd; alle artefacten blijven in `tmp_path` staan.
    """
    root = _mini_project(tmp_path, SLOW_SUITE)
    inventaris = tmp_path / "slow-inventaris.json"
    dekking_xml = tmp_path / "slow-coverage.xml"

    # `parallel = false` helpt hier niet: pytest-cov roept in `Central.finish`
    # altijd combine aan, ook zonder xdist, en `CoverageData.update` doet dat met
    # `ATTACH DATABASE ?`. De parameter is op autorisatiemoment nog ongebonden,
    # dus de offline-gate weigert fail-closed. De runner meet daarom zelf, via de
    # ondersteunde Coverage-API rond één `pytest.main`, zonder combine.
    resultaat = _draai_runner(
        root,
        "unit",
        "--inventory",
        str(inventaris),
        "--budget",
        "45",
        f"--cov={root / 'tests'}",
        f"--cov-report=xml:{dekking_xml}",
        "--cov-fail-under=45",
        timeout=90,
    )

    assert resultaat.returncode == 0, _uitvoer(resultaat)
    assert _status(resultaat) == "ok", _uitvoer(resultaat)

    data = json.loads(inventaris.read_text(encoding="utf-8"))
    verzameld = {item["nodeid"] for item in data["items"]}
    assert verzameld == {SNELLE_NODE, TRAGE_NODE}, data
    assert data["uitgevoerd"] == 2, data
    assert data["overgeslagen"] == 0, data

    # De module wordt uitsluitend door de trage node aangeroepen; geraakte
    # regels bewijzen dus dat die body werkelijk heeft gedraaid.
    assert dekking_xml.is_file(), _uitvoer(resultaat)
    geraakt = _geraakte_regels(dekking_xml, Path(SLOW_MODULE).name)
    assert geraakt >= 5, f"{geraakt} geraakte regels in {SLOW_MODULE}"


#: Bron met bewust ongedekte uitvoerbare regels: `nooit_aangeroepen` wordt door
#: geen enkele test aangeraakt, dus de dekking blijft aantoonbaar onder 100%.
ONGEDEKT_MODULE = "tests/def519_deels_gedekt.py"
ONGEDEKTE_SUITE = {
    ONGEDEKT_MODULE: (
        "def wel_aangeroepen(waarde):\n"
        "    return waarde + 1\n"
        "\n"
        "\n"
        "def nooit_aangeroepen(waarde):\n"
        "    tussenstand = waarde * 2\n"
        "    tussenstand += 3\n"
        "    tussenstand -= 1\n"
        "    tussenstand *= 5\n"
        "    tussenstand //= 2\n"
        "    tussenstand += 7\n"
        "    tussenstand -= 4\n"
        "    return tussenstand\n"
    ),
    "tests/test_deels.py": (
        "import pytest\n\n"
        "from def519_deels_gedekt import wel_aangeroepen\n\n"
        "@pytest.mark.unit\ndef test_deels_gedekt():\n"
        "    assert wel_aangeroepen(1) == 2\n"
    ),
}

#: Bron die geen enkele test importeert: coverage meet dan nul regels.
ONGEMETEN_SUITE = GEZONDE_SUITE | {
    "ongemeten/def519_ongemeten.py": "def nooit_geladen():\n    return 1\n"
}


def _klasse(xml_pad: Path, bestandsnaam: str):
    """Het `<class>`-element van `bestandsnaam` in een coverage-XML."""
    import xml.etree.ElementTree as ET

    for klasse in ET.parse(xml_pad).getroot().iter("class"):
        if Path(klasse.get("filename", "")).name == bestandsnaam:
            return klasse
    return None


def test_inventaris_wijst_naar_de_eigen_coveragedata(tmp_path):
    """De weggeschreven inventaris moet de geproduceerde coveragedata noemen.

    De runner meet in een verse sessieroot, dus CI kan het `.coverage`-bestand
    niet op een vaste plek in de checkout verwachten. Zonder een verwijzing in
    de inventaris is de datafile niet te archiveren zonder een generieke
    `--data-file`-optie of een tweede pad langs de gate. Het pad moet naar een
    bestaand bestand wijzen en buiten het gemeten project liggen.

    De XML-verwijzing wordt op het volledige pad vergeleken, niet op de
    bestandsnaam. De runner resolvet de doelpaden zelf, dus een verwijzing naar
    een gelijknamig bestand op een ándere plek is geen archiveerbaar artefact —
    en een `endswith`-controle zou daar groen op blijven.
    """
    root = _mini_project(tmp_path, SLOW_SUITE)
    inventaris = tmp_path / "artefact-inventaris.json"
    dekking_xml = tmp_path / "artefact-coverage.xml"

    resultaat = _draai_runner(
        root,
        "unit",
        "--inventory",
        str(inventaris),
        "--budget",
        "45",
        f"--cov={root / 'tests'}",
        f"--cov-report=xml:{dekking_xml}",
        timeout=90,
    )

    assert resultaat.returncode == 0, _uitvoer(resultaat)
    data = json.loads(inventaris.read_text(encoding="utf-8"))
    artefact = data.get("coverage_artefacten")
    assert isinstance(artefact, dict), data
    datafile = Path(artefact["data_file"])
    assert datafile.is_file(), artefact
    assert str(root) not in str(datafile), artefact

    verwacht_xml = dekking_xml.resolve()
    genoemd = [Path(pad).resolve() for pad in artefact["xml"]]
    assert verwacht_xml in genoemd, (str(verwacht_xml), artefact)
    assert verwacht_xml.is_file(), str(verwacht_xml)


def test_inventaris_zonder_coverage_noemt_geen_artefact(tmp_path):
    """Zonder coveragevlaggen hoort er geen artefactverwijzing te staan."""
    root = _mini_project(tmp_path, GEZONDE_SUITE)
    inventaris = tmp_path / "kale-inventaris.json"
    resultaat = _draai_runner(root, "unit", "--inventory", str(inventaris))

    assert resultaat.returncode == 0, _uitvoer(resultaat)
    data = json.loads(inventaris.read_text(encoding="utf-8"))
    assert "coverage_artefacten" not in data, data


def test_coverage_onder_vloer_is_nonzero(tmp_path):
    """Een echt niet-gehaalde vloer moet nonzero zijn, niet stil groen.

    Het XML-rapport wordt inhoudelijk gelezen: de nooit aangeroepen body heeft
    aantoonbaar nul hits en de gemeten line-rate ligt onder de gevraagde vloer.
    Dit is een meting op een eigen synthetische bron; het zegt niets over het
    45%-cijfer van het project.
    """
    root = _mini_project(tmp_path, ONGEDEKTE_SUITE)
    dekking_xml = tmp_path / "onder-vloer.xml"
    resultaat = _draai_runner(
        root,
        "unit",
        "--budget",
        "45",
        f"--cov={root / 'tests'}",
        f"--cov-report=xml:{dekking_xml}",
        "--cov-fail-under=95",
        timeout=90,
    )
    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert _status(resultaat) == "coverage-onder-vloer", _uitvoer(resultaat)
    assert dekking_xml.is_file(), _uitvoer(resultaat)

    klasse = _klasse(dekking_xml, Path(ONGEDEKT_MODULE).name)
    assert klasse is not None, dekking_xml.read_text(encoding="utf-8")
    hits = {int(r.get("number")): int(r.get("hits", "0")) for r in klasse.iter("line")}
    assert hits, klasse.attrib
    # De body van `nooit_aangeroepen` begint na de def-regel op regel 5.
    ongeraakt = [nummer for nummer, aantal in hits.items() if aantal == 0]
    assert len(ongeraakt) >= 7, hits
    assert min(ongeraakt) >= 6, hits
    assert float(klasse.get("line-rate")) < 0.95, klasse.attrib


def test_coverage_config_en_xml_relatief_pad_worden_gerespecteerd(tmp_path):
    """Relatieve `--cov-config` en `--cov-report=xml:` gelden vanuit de aanroep-CWD.

    Het kind draait in een verse werkmap; zonder resolutie zou de config daar
    niet bestaan en het XML-rapport op de verkeerde plek belanden. De eigen
    rcfile sluit bovendien een echte regel uit, zodat het behoud van
    `omit`/`exclude_lines` meetbaar is en niet alleen via een dict-vergelijking.
    """
    root = _mini_project(tmp_path, ONGEDEKTE_SUITE)
    (root / "tests" / "def519_weggelaten.py").write_text(
        "def genegeerd():\n    return 1\n", encoding="utf-8"
    )
    config = root / "eigen.rc"
    config.write_text(
        "[run]\nbranch = false\nomit =\n    */def519_weggelaten.py\n\n"
        "[report]\nexclude_lines =\n    def nooit_aangeroepen\n",
        encoding="utf-8",
    )
    dekking_xml = root / "relatief.xml"

    resultaat = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--project-root",
            str(root),
            "unit",
            "--budget",
            "45",
            f"--cov={root / 'tests'}",
            "--cov-config=eigen.rc",
            "--cov-report=xml:relatief.xml",
            "--cov-fail-under=1",
        ],
        cwd=str(root),
        env=_kindomgeving(),
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )

    assert resultaat.returncode == 0, _uitvoer(resultaat)
    assert _status(resultaat) == "ok", _uitvoer(resultaat)
    assert dekking_xml.is_file(), _uitvoer(resultaat)
    # `omit` uit de eigen config is toegepast: het weggelaten bestand ontbreekt.
    assert _klasse(dekking_xml, "def519_weggelaten.py") is None
    # `exclude_lines` is toegepast: de uitgesloten def-regel staat niet in het rapport.
    klasse = _klasse(dekking_xml, Path(ONGEDEKT_MODULE).name)
    assert klasse is not None
    assert 5 not in {int(r.get("number")) for r in klasse.iter("line")}, klasse.attrib


def test_rapportfout_na_groene_tests_is_nonzero(tmp_path):
    """Een onbruikbaar XML-doel moet nonzero geven, ook al slaagden de tests.

    Het doelpad is een bestaande, eigen map: coverage kan daar geen bestand
    schrijven. Er wordt niets verwijderd.
    """
    root = _mini_project(tmp_path, SLOW_SUITE)
    blokkerende_map = tmp_path / "rapport-doel-is-map.xml"
    blokkerende_map.mkdir()

    resultaat = _draai_runner(
        root,
        "unit",
        "--budget",
        "45",
        f"--cov={root / 'tests'}",
        f"--cov-report=xml:{blokkerende_map}",
        timeout=90,
    )

    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert _status(resultaat) == "coverage-rapportfout", _uitvoer(resultaat)
    assert blokkerende_map.is_dir()


def test_coverage_zonder_gemeten_regels_is_nonzero(tmp_path):
    """Nul gemeten regels mag nooit als geslaagde meting doorgaan."""
    root = _mini_project(tmp_path, ONGEMETEN_SUITE)
    resultaat = _draai_runner(
        root,
        "unit",
        "--budget",
        "45",
        f"--cov={root / 'ongemeten'}",
        timeout=90,
    )
    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert _status(resultaat) == "coverage-geen-data", _uitvoer(resultaat)


def test_onbruikbare_coverage_config_is_nonzero(tmp_path):
    """Een expliciet opgegeven config die niet bestaat, faalt fail-closed."""
    root = _mini_project(tmp_path, SLOW_SUITE)
    resultaat = _draai_runner(
        root,
        "unit",
        "--budget",
        "45",
        f"--cov={root / 'tests'}",
        f"--cov-config={tmp_path / 'bestaat-niet.rc'}",
        timeout=90,
    )
    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert _status(resultaat) == "coverage-config-onbruikbaar", _uitvoer(resultaat)


def test_paths_config_is_expliciet_niet_ondersteund(tmp_path):
    """`[paths]` wordt geweigerd, niet stil gestript."""
    root = _mini_project(tmp_path, SLOW_SUITE)
    config = tmp_path / "met-paths.rc"
    config.write_text(
        "[run]\nbranch = false\n\n[paths]\nbron =\n    src\n    */src\n",
        encoding="utf-8",
    )
    resultaat = _draai_runner(
        root,
        "unit",
        "--budget",
        "45",
        f"--cov={root / 'tests'}",
        f"--cov-config={config}",
        timeout=90,
    )
    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert _status(resultaat) == "coverage-unsupported-config", _uitvoer(resultaat)


def test_html_en_append_blijven_verboden_opties(tmp_path):
    """HTML-rapport, append en onbruikbare vloerwaarden zijn niet ondersteund."""
    root = _mini_project(tmp_path, SLOW_SUITE)
    for optie in (
        f"--cov-report=html:{tmp_path / 'html'}",
        "--cov-append",
        "--cov-fail-under=nan",
        "--cov-fail-under=inf",
        "--cov-fail-under=101",
        "--cov-fail-under=-1",
    ):
        resultaat = _draai_runner(
            root, "unit", "--budget", "45", f"--cov={root / 'tests'}", optie, timeout=90
        )
        assert resultaat.returncode != 0, _uitvoer(resultaat)
        assert _status(resultaat) == "verboden-optie", (optie, _uitvoer(resultaat))


def test_bestaande_coveragedata_in_werkmap_blijft_ongemoeid(tmp_path):
    """De meting raakt geen bestaand `.coverage` in het project.

    De runner draait in een verse werkmap onder zijn eigen sessieroot en schrijft
    zijn datafile daar. Een sentinel in de projectroot moet byte-identiek blijven:
    geen erase, geen overschrijving, geen verwijdering.
    """
    root = _mini_project(tmp_path, SLOW_SUITE)
    sentinel = root / ".coverage"
    inhoud = b"def519-sentinel-geen-coveragedata"
    sentinel.write_bytes(inhoud)

    resultaat = _draai_runner(
        root, "unit", "--budget", "45", f"--cov={root / 'tests'}", timeout=90
    )

    assert resultaat.returncode == 0, _uitvoer(resultaat)
    assert sentinel.read_bytes() == inhoud


def test_gewoon_testfalen_blijft_testfalen(tmp_path):
    """De integriteitschecks mogen een gewone rode test niet herbenoemen."""
    root = _mini_project(
        tmp_path,
        {
            "tests/test_rood.py": "import pytest\n\n"
            "@pytest.mark.unit\ndef test_faalt():\n    assert 1 == 2\n"
        },
    )
    resultaat = _draai_runner(root, "unit")
    assert resultaat.returncode != 0
    assert _status(resultaat) == "testfalen"


def test_gewone_collectiefout_blijft_collectiefout(tmp_path):
    root = _mini_project(
        tmp_path, {"tests/test_kapot.py": "import bestaat_niet_def519\n"}
    )
    resultaat = _draai_runner(root, "unit")
    assert resultaat.returncode != 0
    assert _status(resultaat) == "collectiefout"


# --- Inventaris moet er zijn en moet kloppen --------------------------------


def test_afgebroken_run_zonder_inventaris_is_niet_ok(tmp_path):
    """Rootbevinding (a): een conftest die vóór de rapporten afbreekt.

    `os._exit(0)` tijdens collectie laat pytest met exitcode 0 eindigen zonder
    dat er ook maar één testbody heeft gedraaid en zonder dat de inventaris
    geschreven wordt.
    """
    root = _mini_project(
        tmp_path,
        GEZONDE_SUITE
        | {
            "tests/conftest.py": "import os\n\n"
            "def pytest_collection_modifyitems(session, config, items):\n"
            "    os._exit(0)\n"
        },
    )
    resultaat = _draai_runner(root, "unit")
    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert _status(resultaat) == "geen-inventaris", _uitvoer(resultaat)


#: Rapportvormen die geen geldige inventaris zijn. De conftest overschrijft het
#: rapport als allerlaatste hook, ná de plugin van de runner.
BESCHADIGDE_RAPPORTEN = {
    "geen-json": "dit is geen json",
    "items-is-geen-lijst": json.dumps(
        {"profiel": "unit", "items": "twee", "collectiefouten": 0, "uitgevoerd": 1}
    ),
    "uitgevoerd-ontbreekt": json.dumps(
        {"profiel": "unit", "items": [{"nodeid": "a", "markers": ["unit"]}]}
    ),
}


@pytest.mark.parametrize("vorm", sorted(BESCHADIGDE_RAPPORTEN))
def test_beschadigde_inventaris_is_niet_ok(tmp_path, vorm):
    """Een onleesbare of vormloze inventaris telt niet als bewijs."""
    inhoud = BESCHADIGDE_RAPPORTEN[vorm]
    root = _mini_project(
        tmp_path,
        GEZONDE_SUITE
        | {
            "tests/conftest.py": "import os, pathlib, pytest\n\n"
            "@pytest.hookimpl(trylast=True)\n"
            "def pytest_sessionfinish(session, exitstatus):\n"
            "    pathlib.Path(os.environ['DEF519_REPORT']).write_text(\n"
            f"        {inhoud!r}, encoding='utf-8'\n"
            "    )\n"
        },
    )
    resultaat = _draai_runner(root, "unit")
    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert _status(resultaat) == "geen-inventaris", _uitvoer(resultaat)


def test_inventaris_zonder_bootstrapbewijs_is_niet_ok(tmp_path):
    """Een verder keurige inventaris zónder bootstrapbewijs is onvoldoende."""
    vervalst = json.dumps(
        {
            "profiel": "unit",
            "items": [{"nodeid": GEZONDE_NODE, "markers": []}],
            "collectiefouten": 0,
            "uitgevoerd": 1,
        }
    )
    root = _mini_project(
        tmp_path,
        GEZONDE_SUITE
        | {
            "tests/conftest.py": "import os, pathlib, pytest\n\n"
            "@pytest.hookimpl(trylast=True)\n"
            "def pytest_sessionfinish(session, exitstatus):\n"
            "    pathlib.Path(os.environ['DEF519_REPORT']).write_text(\n"
            f"        {vervalst!r}, encoding='utf-8'\n"
            "    )\n"
        },
    )
    resultaat = _draai_runner(root, "unit")
    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert _status(resultaat) == "geen-bootstrapbewijs", _uitvoer(resultaat)


# --- Er moet werkelijk iets uitgevoerd zijn ---------------------------------


def test_uitsluitend_overgeslagen_tests_is_niet_ok(tmp_path):
    """Een niet-lege collectie is geen bewijs van uitvoering.

    Alle geselecteerde nodes worden overgeslagen: pytest eindigt met 0 en de
    inventaris is niet leeg, maar geen enkele beschermde assertie draaide.
    """
    root = _mini_project(
        tmp_path,
        {
            "tests/test_alles_skip.py": "import pytest\n\n"
            "@pytest.mark.unit\n@pytest.mark.skip(reason='synthetisch')\n"
            "def test_gemarkeerd_skip():\n    assert False\n\n"
            "@pytest.mark.unit\ndef test_skip_in_body():\n"
            "    pytest.skip('synthetisch')\n"
        },
    )
    resultaat = _draai_runner(root, "unit")
    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert _status(resultaat) == "geen-uitvoering", _uitvoer(resultaat)


# --- Verplichte opties zijn niet uit te schakelen ---------------------------


#: Doorgegeven pytest-opties die het profiel, de bootstrap of de inventaris
#: zouden ondermijnen. Rootbevinding (b) is `--collect-only`.
VERBODEN_OPTIES = {
    "collect-only": ["--collect-only"],
    "collect-only-kort": ["--co"],
    "plugin-uit": ["-p", "no:def519_runner_plugin"],
    "plugin-uit-samen": ["-pno:def519_runner_plugin"],
    "markerselectie": ["-m", "smoke"],
    "naamselectie": ["-k", "bestaat_niet"],
    "eigen-config": ["-c", "elders.ini"],
    "ini-override": ["-o", "addopts=--collect-only"],
    "geen-conftest": ["--noconftest"],
    "collectiefouten-negeren": ["--continue-on-collection-errors"],
    "negeerpad": ["--ignore=tests"],
    "deselectie": ["--deselect", GEZONDE_NODE],
    "eigen-rootdir": ["--rootdir=/tmp"],
    "eigen-pad": ["tests/test_gezond.py"],
}


@pytest.mark.parametrize("geval", sorted(VERBODEN_OPTIES))
def test_verboden_pytest_opties_worden_geweigerd(tmp_path, geval):
    root = _mini_project(tmp_path, GEZONDE_SUITE)
    resultaat = _draai_runner(root, "unit", *VERBODEN_OPTIES[geval])
    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert _status(resultaat) == "verboden-optie", _uitvoer(resultaat)


def test_rapportageopties_blijven_wel_toegestaan(tmp_path):
    """De weigering mag de noodzakelijke rapportage niet meeblokkeren."""
    root = _mini_project(tmp_path, GEZONDE_SUITE)
    junit = tmp_path / "junit.xml"
    resultaat = _draai_runner(root, "unit", f"--junitxml={junit}", "-q", "--tb=short")
    assert resultaat.returncode == 0, _uitvoer(resultaat)
    assert _status(resultaat) == "ok"
    assert junit.is_file(), _uitvoer(resultaat)


# --- Budget -----------------------------------------------------------------


@pytest.mark.parametrize("waarde", ["0", "-5", "nan", "inf"])
def test_budget_moet_eindig_en_positief_zijn(tmp_path, waarde):
    """Een oneindig, nul of negatief budget is geen begrensde run."""
    root = _mini_project(tmp_path, GEZONDE_SUITE)
    resultaat = _draai_runner(root, "unit", "--budget", waarde, timeout=120)
    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert _status(resultaat) == "ongeldig-budget", _uitvoer(resultaat)


# --- Bootstrapfout stopt vóór applicatiecode --------------------------------


def test_bootstrapfout_stopt_voor_elke_applicatiecode(tmp_path):
    """Een kapotte bootstrap mag geen waarschuwing-en-doorgaan zijn.

    `site` slikt een exception uit `sitecustomize.py` in: het print een
    waarschuwing en start de interpreter alsnog — dan draait pytest zónder gate.
    Deze test draait de échte gegenereerde `sitecustomize` van de runner tegen
    een synthetische, kapotte bootstrapmodule en eist dat het proces stopt
    vóórdat er ook maar één regel applicatiecode draait.
    """
    kern = tmp_path / "synthetische-bootstrapwortel"
    (kern / "tests").mkdir(parents=True)
    (kern / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (kern / "tests" / "offline_bootstrap.py").write_text(
        "raise RuntimeError('DEF519-BOOTSTRAP-KAPOT')\n", encoding="utf-8"
    )
    startmap = tmp_path / "startmap"
    startmap.mkdir()
    (startmap / "sitecustomize.py").write_text(
        _runner_module()._SITECUSTOMIZE, encoding="utf-8"
    )

    resultaat = subprocess.run(
        [sys.executable, "-c", "print('APPLICATIECODE-DRAAIDE')"],
        cwd=str(tmp_path),
        env=_kindomgeving(
            PYTHONPATH=str(startmap),
            DEF519_BOOTSTRAP_ROOT=str(kern),
            PYTHONDONTWRITEBYTECODE="1",
        ),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert "APPLICATIECODE-DRAAIDE" not in resultaat.stdout, _uitvoer(resultaat)
    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert "DEF519-BOOTSTRAP-KAPOT" in resultaat.stderr, _uitvoer(resultaat)


# --- Integrationprofiel: unie van integratiepad en integrationmarker --------
#
# Het vastgestelde contract is dat `integration` de vereniging selecteert van
# (1) alles onder de integratiemap en (2) elke node met de integrationmarker,
# waar die node ook staat. Beide zijden bestaan in deze repository werkelijk:
# onder `tests/integration/` dragen bestanden `contract`, `regression`,
# `compliance` of `performance` zónder integrationmarker, en buiten die map
# dragen bestanden (onder meer in `tests/unit/`) juist wél die marker.
#
# De miniprojecten hieronder zijn synthetisch en modelleren precies dat: een
# padnode zonder integrationmarker, een markernode buiten het integratiepad, en
# een unitnode buiten beide die er níét bij hoort. Die derde node maakt de
# proef tweezijdig: een implementatie die simpelweg de hele testboom selecteert
# valt er even hard op om als het huidige, marker-only profiel.

#: Eigen mini-`pytest.ini` voor deze scope: dezelfde vorm als de standaard van
#: `_mini_project`, aangevuld met de markers die de padnodes hier dragen.
#: De helper schrijft zijn standaardini vóór de bestanden uit het dict, dus
#: deze sleutel vervangt hem zonder de andere suites te raken.
UNIE_INI = (
    "[pytest]\ntestpaths = tests\naddopts = -q\n"
    "markers =\n    unit: unit\n    integration: integration\n"
    "    acceptance: acceptance\n    smoke: smoke\n    slow: slow\n"
    "    contract: contract\n    regression: regression\n"
)

#: Bestands- en testnamen staan apart zodat de node-ids eruit worden afgeleid
#: (zelfde reden als bij `GEZOND_BESTAND`: geen voluit genoteerde
#: bestandsnaam-plus-nodeketen, want die zou de verwijzingsguard van DEF-676 als
#: belofte over déze repository lezen).
UNIE_PAD_CONTRACT_BESTAND = "tests/integration/test_def519_pad_contract.py"
UNIE_PAD_CONTRACT_TEST = "test_padnode_met_contractmarker"
UNIE_PAD_REGRESSIE_BESTAND = "tests/integration/test_def519_pad_regressie.py"
UNIE_PAD_REGRESSIE_TEST = "test_padnode_met_regressiemarker"
UNIE_MARKER_BESTAND = "tests/def519_buiten_pad/test_def519_marker_elders.py"
UNIE_MARKER_TEST = "test_markernode_buiten_het_integratiepad"
UNIE_UNIT_BESTAND = "tests/def519_buiten_pad/test_def519_unit_elders.py"
UNIE_UNIT_TEST = "test_unitnode_blijft_buiten_de_unie"

#: Elke node rekent en asserteert op een echte uitkomst; een gedeselecteerde
#: node kan `uitgevoerd` nooit verhogen, een uitgevoerde node bewijst zijn body.
UNIE_SUITE = {
    "pytest.ini": UNIE_INI,
    UNIE_PAD_CONTRACT_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.contract]\n\n\n"
        f"def {UNIE_PAD_CONTRACT_TEST}():\n"
        "    waarden = [3, 4, 5]\n"
        "    assert sum(waarden) * 2 == 24\n"
    ),
    UNIE_PAD_REGRESSIE_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.regression]\n\n\n"
        f"def {UNIE_PAD_REGRESSIE_TEST}():\n"
        "    waarden = [10, 1]\n"
        "    assert sum(waarden) * 2 == 22\n"
    ),
    UNIE_MARKER_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.integration]\n\n\n"
        f"def {UNIE_MARKER_TEST}():\n"
        "    waarden = [1, 2, 3]\n"
        "    assert sum(waarden) * 2 == 12\n"
    ),
    UNIE_UNIT_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.unit]\n\n\n"
        f"def {UNIE_UNIT_TEST}():\n"
        "    waarden = [7]\n"
        "    assert sum(waarden) * 2 == 14\n"
    ),
}

UNIE_PAD_CONTRACT_NODE = f"{UNIE_PAD_CONTRACT_BESTAND}::{UNIE_PAD_CONTRACT_TEST}"
UNIE_PAD_REGRESSIE_NODE = f"{UNIE_PAD_REGRESSIE_BESTAND}::{UNIE_PAD_REGRESSIE_TEST}"
UNIE_MARKER_NODE = f"{UNIE_MARKER_BESTAND}::{UNIE_MARKER_TEST}"
UNIE_UNIT_NODE = f"{UNIE_UNIT_BESTAND}::{UNIE_UNIT_TEST}"

#: De exact verwachte selectie van het integrationprofiel op dit miniproject.
UNIE_VERWACHT = {
    UNIE_PAD_CONTRACT_NODE,
    UNIE_PAD_REGRESSIE_NODE,
    UNIE_MARKER_NODE,
}


def test_integrationprofiel_selecteert_pad_en_marker_als_unie(tmp_path):
    """Het integrationprofiel moet padnodes én markernodes verzamelen.

    Met het huidige profiel (`-m integration`) blijven de twee padnodes buiten
    de collectie: de inventaris bevat dan uitsluitend de markernode en
    `uitgevoerd` is 1. Dat is de rode oorzaak die deze node aanwijst.

    De unitnode buiten het integratiepad hoort er niet bij. Doordat de
    inventaris exact wordt vergeleken, faalt deze node ook op een implementatie
    die de hele testboom zou selecteren — de proef is dus tweezijdig en niet met
    een bredere selectie groen te maken.

    Binnendeadline 45s onder de buitendeadline 90s. Er wordt niets verwijderd;
    alle artefacten blijven in `tmp_path`.
    """
    root = _mini_project(tmp_path, UNIE_SUITE)
    inventaris = tmp_path / "unie-inventaris.json"

    resultaat = _draai_runner(
        root,
        "integration",
        "--inventory",
        str(inventaris),
        "--budget",
        "45",
        timeout=90,
    )

    assert _status(resultaat) == "ok", _uitvoer(resultaat)
    assert resultaat.returncode == 0, _uitvoer(resultaat)

    data = json.loads(inventaris.read_text(encoding="utf-8"))
    verzameld = {item["nodeid"] for item in data["items"]}
    assert verzameld == UNIE_VERWACHT, data
    assert UNIE_UNIT_NODE not in verzameld, data
    assert data["uitgevoerd"] == 3, data
    assert data["overgeslagen"] == 0, data
    assert data["collectiefouten"] == 0, data


#: Padnode die op een echte assertie faalt; hij draagt geen integrationmarker en
#: wordt dus uitsluitend via het integratiepad geselecteerd.
UNIE_ROOD_BESTAND = "tests/integration/test_def519_pad_rood.py"
UNIE_ROOD_TEST = "test_padnode_faalt_op_echte_assertie"
UNIE_ROOD_NODE = f"{UNIE_ROOD_BESTAND}::{UNIE_ROOD_TEST}"

SABOTAGE_SUITE = UNIE_SUITE | {
    UNIE_ROOD_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.contract]\n\n\n"
        f"def {UNIE_ROOD_TEST}():\n"
        "    waarden = [1, 1]\n"
        "    assert sum(waarden) * 2 == 5\n"
    )
}


def test_falende_padtest_maakt_integrationgate_rood(tmp_path):
    """Een rood padtestbestand moet de verplichte integrationgate rood maken.

    Dit is de sabotageproef uit de acceptatiecriteria, op het niveau van de
    runner zelf: een nieuw bestand onder het integratiepad met een echte
    assertionfout. Het draagt bewust géén integrationmarker, precies zoals de
    contract- en regressiebestanden in de echte suite.

    De rest van het miniproject is groen en bevat een markernode, zodat de
    huidige, marker-only selectie niet leeg is: die meldt hier `status=ok` met
    exitcode 0 terwijl het rode bestand nooit is geselecteerd. Dát is de rode
    oorzaak — niet een lege selectie die toevallig ook nonzero zou zijn.

    Er wordt niets verwijderd; het sabotagebestand leeft alleen in `tmp_path`.
    """
    root = _mini_project(tmp_path, SABOTAGE_SUITE)
    inventaris = tmp_path / "sabotage-inventaris.json"

    resultaat = _draai_runner(
        root,
        "integration",
        "--inventory",
        str(inventaris),
        "--budget",
        "45",
        timeout=90,
    )

    assert _status(resultaat) == "testfalen", _uitvoer(resultaat)
    assert resultaat.returncode != 0, _uitvoer(resultaat)

    data = json.loads(inventaris.read_text(encoding="utf-8"))
    verzameld = {item["nodeid"] for item in data["items"]}
    assert UNIE_ROOD_NODE in verzameld, data
    assert verzameld == UNIE_VERWACHT | {UNIE_ROOD_NODE}, data
    assert data["uitgevoerd"] == 4, data
    assert data["collectiefouten"] == 0, data


# --- Expliciete advisory/future-scheiding -----------------------------------
#
# De hoofdgates `integration` en `acceptance-smoke` mogen precies één soort node
# buiten hun scope laten: de node die zichzelf expliciet als `advisory` of
# `future` markeert. Alles anders blijft binnen de gate — er is nadrukkelijk
# géén blanket-uitsluiting van `performance`, `slow` of `red_phase`, en geen
# bestandscatalogus. Het miniproject hieronder bevat daarom ook een trage,
# performance-gemarkeerde node die juist wél mee moet doen; een te brede
# uitsluiting valt daar even hard op om als een ontbrekende.
#
# Daarnaast krijgen `advisory` en `future` een eigen, optioneel offlineprofiel
# met dezelfde eigenschappen als de hoofdgates: vroege bootstrap, niet-lege
# selectie, echte uitvoering en nonzero bij falen. Een echte assertiefout in een
# advisory-node blijft dus zichtbaar als `testfalen` — advisory betekent
# "buiten de verplichte gate", niet "mag stil groen zijn". Deze batch voert die
# profielen alleen op een synthetisch miniproject uit; er draait geen werkelijke
# advisory-, future- of live-scope.
#
# `live` hoort volgens hetzelfde contract buiten de twee hoofdgates. De node
# hieronder modelleert dat puur synthetisch: hij draagt alleen de marker en
# faalt op een gewone rekenassertie. Er komt geen provider, netwerk, sleutel of
# echte livetest aan te pas — deze suite blijft volledig offline.
#
# `unit` verandert niet: alle unit inclusief slow (bestaande test) én inclusief
# een node die zichzelf advisory noemt. Advisory scheidt de hoofdgates, het
# krimpt de unitscope niet.

#: Eigen mini-`pytest.ini`: alle markers die dit miniproject gebruikt.
SCOPE_INI = (
    "[pytest]\ntestpaths = tests\naddopts = -q\n"
    "markers =\n    unit: unit\n    integration: integration\n"
    "    acceptance: acceptance\n    smoke: smoke\n    slow: slow\n"
    "    performance: performance\n    advisory: advisory\n    future: future\n"
    "    live: live\n"
)

#: Bestands- en testnamen apart, zodat de node-ids eruit worden afgeleid.
SCOPE_INTEGRATION_BESTAND = "tests/def519_scope/test_def519_regulier_integration.py"
SCOPE_INTEGRATION_TEST = "test_regulier_integrationnode"
SCOPE_TRAAG_BESTAND = "tests/integration/test_def519_regulier_traag.py"
SCOPE_TRAAG_TEST = "test_reguliere_trage_padnode_blijft_meedoen"
SCOPE_ACCEPTANCE_BESTAND = "tests/def519_scope/test_def519_regulier_acceptance.py"
SCOPE_ACCEPTANCE_TEST = "test_regulier_acceptancenode"
SCOPE_SMOKE_BESTAND = "tests/def519_scope/test_def519_regulier_smoke.py"
SCOPE_SMOKE_TEST = "test_regulier_smokenode"
SCOPE_ADVISORY_PAD_BESTAND = "tests/integration/test_def519_advisory_pad.py"
SCOPE_ADVISORY_PAD_TEST = "test_advisorynode_faalt_op_echte_assertie"
SCOPE_FUTURE_BESTAND = "tests/def519_scope/test_def519_future_elders.py"
SCOPE_FUTURE_TEST = "test_futurenode_faalt_op_echte_assertie"
SCOPE_LIVE_BESTAND = "tests/def519_scope/test_def519_live_elders.py"
SCOPE_LIVE_TEST = "test_livenode_faalt_op_echte_assertie"
SCOPE_ADVISORY_UNIT_BESTAND = "tests/def519_scope/test_def519_advisory_unit.py"
SCOPE_ADVISORY_UNIT_TEST = "test_advisory_unitnode_blijft_in_unit"

#: De advisory-node ligt bewust *onder* het integratiepad en de future-node er
#: bewust buiten: de uitsluiting moet langs beide routes werken — die van de
#: padunie én die van de gewone markerselectie.
SCOPE_SUITE = {
    "pytest.ini": SCOPE_INI,
    SCOPE_INTEGRATION_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.integration]\n\n\n"
        f"def {SCOPE_INTEGRATION_TEST}():\n"
        "    waarden = [1, 2, 3]\n"
        "    assert sum(waarden) * 2 == 12\n"
    ),
    SCOPE_TRAAG_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.performance, pytest.mark.slow]\n\n\n"
        f"def {SCOPE_TRAAG_TEST}():\n"
        "    waarden = [9, 9]\n"
        "    assert sum(waarden) * 2 == 36\n"
    ),
    SCOPE_ACCEPTANCE_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.acceptance]\n\n\n"
        f"def {SCOPE_ACCEPTANCE_TEST}():\n"
        "    waarden = [5]\n"
        "    assert sum(waarden) * 2 == 10\n"
    ),
    SCOPE_SMOKE_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.smoke]\n\n\n"
        f"def {SCOPE_SMOKE_TEST}():\n"
        "    waarden = [6]\n"
        "    assert sum(waarden) * 2 == 12\n"
    ),
    SCOPE_ADVISORY_PAD_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [\n"
        "    pytest.mark.advisory,\n"
        "    pytest.mark.integration,\n"
        "    pytest.mark.acceptance,\n"
        "]\n\n\n"
        f"def {SCOPE_ADVISORY_PAD_TEST}():\n"
        "    waarden = [2, 3]\n"
        "    assert sum(waarden) * 2 == 11\n"
    ),
    SCOPE_FUTURE_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [\n"
        "    pytest.mark.future,\n"
        "    pytest.mark.integration,\n"
        "    pytest.mark.acceptance,\n"
        "]\n\n\n"
        f"def {SCOPE_FUTURE_TEST}():\n"
        "    waarden = [4, 4]\n"
        "    assert sum(waarden) * 2 == 17\n"
    ),
    SCOPE_LIVE_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [\n"
        "    pytest.mark.live,\n"
        "    pytest.mark.integration,\n"
        "    pytest.mark.acceptance,\n"
        "]\n\n\n"
        f"def {SCOPE_LIVE_TEST}():\n"
        "    waarden = [6, 6]\n"
        "    assert sum(waarden) * 2 == 25\n"
    ),
    SCOPE_ADVISORY_UNIT_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.advisory, pytest.mark.unit]\n\n\n"
        f"def {SCOPE_ADVISORY_UNIT_TEST}():\n"
        "    waarden = [8]\n"
        "    assert sum(waarden) * 2 == 16\n"
    ),
}

SCOPE_INTEGRATION_NODE = f"{SCOPE_INTEGRATION_BESTAND}::{SCOPE_INTEGRATION_TEST}"
SCOPE_TRAAG_NODE = f"{SCOPE_TRAAG_BESTAND}::{SCOPE_TRAAG_TEST}"
SCOPE_ACCEPTANCE_NODE = f"{SCOPE_ACCEPTANCE_BESTAND}::{SCOPE_ACCEPTANCE_TEST}"
SCOPE_SMOKE_NODE = f"{SCOPE_SMOKE_BESTAND}::{SCOPE_SMOKE_TEST}"
SCOPE_ADVISORY_PAD_NODE = f"{SCOPE_ADVISORY_PAD_BESTAND}::{SCOPE_ADVISORY_PAD_TEST}"
SCOPE_FUTURE_NODE = f"{SCOPE_FUTURE_BESTAND}::{SCOPE_FUTURE_TEST}"
SCOPE_LIVE_NODE = f"{SCOPE_LIVE_BESTAND}::{SCOPE_LIVE_TEST}"
SCOPE_ADVISORY_UNIT_NODE = f"{SCOPE_ADVISORY_UNIT_BESTAND}::{SCOPE_ADVISORY_UNIT_TEST}"

#: De drie expliciet uitgezonderde nodes; alle drie falen op een echte assertie,
#: dus een gate die er ook maar één van selecteert wordt aantoonbaar rood.
SCOPE_UITGEZONDERD = {SCOPE_ADVISORY_PAD_NODE, SCOPE_FUTURE_NODE, SCOPE_LIVE_NODE}


def test_integrationprofiel_laat_expliciete_advisory_en_future_buiten(tmp_path):
    """`integration` houdt zijn reguliere scope, minus advisory, future en live.

    Verwacht: de gewone integrationnode én de trage, performance-gemarkeerde
    padnode. Die tweede staat er om de andere kant te bewaken: een
    implementatie die `slow` of `performance` blanket uitsluit, faalt hier.

    Met de huidige runner doen de advisory-, future- en livenode gewoon mee — de
    eerste via de padunie, de andere twee via hun integrationmarker — en maken
    hun echte assertiefouten de run rood. Dat is de rode oorzaak van deze node.

    Binnendeadline 45s onder de buitendeadline 90s; niets wordt verwijderd.
    """
    root = _mini_project(tmp_path, SCOPE_SUITE)
    inventaris = tmp_path / "scope-integration-inventaris.json"

    resultaat = _draai_runner(
        root,
        "integration",
        "--inventory",
        str(inventaris),
        "--budget",
        "45",
        timeout=90,
    )

    assert _status(resultaat) == "ok", _uitvoer(resultaat)
    assert resultaat.returncode == 0, _uitvoer(resultaat)

    data = json.loads(inventaris.read_text(encoding="utf-8"))
    verzameld = {item["nodeid"] for item in data["items"]}
    assert verzameld == {SCOPE_INTEGRATION_NODE, SCOPE_TRAAG_NODE}, data
    assert not verzameld & SCOPE_UITGEZONDERD, data
    assert data["uitgevoerd"] == 2, data
    assert data["overgeslagen"] == 0, data
    assert data["collectiefouten"] == 0, data


def test_acceptance_smoke_laat_expliciete_advisory_en_future_buiten(tmp_path):
    """`acceptance-smoke` houdt zijn scope, minus advisory, future en live.

    Alle drie de uitgezonderde nodes dragen ook de acceptancemarker, dus de
    huidige markerselectie pakt ze mee en de run wordt rood op hun
    assertiefouten.
    """
    root = _mini_project(tmp_path, SCOPE_SUITE)
    inventaris = tmp_path / "scope-acceptance-inventaris.json"

    resultaat = _draai_runner(
        root,
        "acceptance-smoke",
        "--inventory",
        str(inventaris),
        "--budget",
        "45",
        timeout=90,
    )

    assert _status(resultaat) == "ok", _uitvoer(resultaat)
    assert resultaat.returncode == 0, _uitvoer(resultaat)

    data = json.loads(inventaris.read_text(encoding="utf-8"))
    verzameld = {item["nodeid"] for item in data["items"]}
    assert verzameld == {SCOPE_ACCEPTANCE_NODE, SCOPE_SMOKE_NODE}, data
    assert not verzameld & SCOPE_UITGEZONDERD, data
    assert data["uitgevoerd"] == 2, data
    assert data["overgeslagen"] == 0, data
    assert data["collectiefouten"] == 0, data


def test_advisoryprofiel_levert_exact_de_advisorynodes(tmp_path):
    """Het advisoryprofiel selecteert exact zijn eigen marker, en faalt echt.

    Beide advisorynodes horen erbij — die onder het integratiepad én die met de
    unitmarker — want de selectie gaat over de marker, niet over de map. De rode
    advisorynode moet als `testfalen` naar buiten komen: buiten de verplichte
    gate staan is iets anders dan stil groen mogen zijn. Geen skip, geen xfail:
    `overgeslagen` moet nul blijven.

    De huidige runner kent het profiel nog niet en weigert het argument; dat is
    de rode oorzaak van deze node.
    """
    root = _mini_project(tmp_path, SCOPE_SUITE)
    inventaris = tmp_path / "scope-advisory-inventaris.json"

    resultaat = _draai_runner(
        root,
        "advisory",
        "--inventory",
        str(inventaris),
        "--budget",
        "45",
        timeout=90,
    )

    assert _status(resultaat) == "testfalen", _uitvoer(resultaat)
    assert resultaat.returncode != 0, _uitvoer(resultaat)

    data = json.loads(inventaris.read_text(encoding="utf-8"))
    verzameld = {item["nodeid"] for item in data["items"]}
    assert verzameld == {SCOPE_ADVISORY_PAD_NODE, SCOPE_ADVISORY_UNIT_NODE}, data
    assert data["uitgevoerd"] == 2, data
    assert data["overgeslagen"] == 0, data
    assert data["collectiefouten"] == 0, data


def test_futureprofiel_levert_exact_de_futurenodes(tmp_path):
    """Het futureprofiel selecteert exact zijn eigen marker, en faalt echt.

    Eén futurenode, die op een echte assertie faalt: `testfalen` en nonzero, met
    een uitgevoerde body en zonder overgeslagen node. Ook hier kent de huidige
    runner het profiel nog niet — dat is de rode oorzaak.
    """
    root = _mini_project(tmp_path, SCOPE_SUITE)
    inventaris = tmp_path / "scope-future-inventaris.json"

    resultaat = _draai_runner(
        root,
        "future",
        "--inventory",
        str(inventaris),
        "--budget",
        "45",
        timeout=90,
    )

    assert _status(resultaat) == "testfalen", _uitvoer(resultaat)
    assert resultaat.returncode != 0, _uitvoer(resultaat)

    data = json.loads(inventaris.read_text(encoding="utf-8"))
    verzameld = {item["nodeid"] for item in data["items"]}
    assert verzameld == {SCOPE_FUTURE_NODE}, data
    assert data["uitgevoerd"] == 1, data
    assert data["overgeslagen"] == 0, data
    assert data["collectiefouten"] == 0, data


def test_unitprofiel_behoudt_de_advisory_unitnode(tmp_path):
    """Regressievangnet: advisory krimpt de unitscope niet.

    De advisory-uitsluiting hoort alleen bij de hoofdgates `integration` en
    `acceptance-smoke`. Een node die zowel `advisory` als `unit` draagt, blijft
    onverkort onderdeel van het unitprofiel. Dat de scope daarnaast álle
    unittests inclusief `slow` omvat, is al vastgelegd door
    `test_unit_profiel_voert_slow_daadwerkelijk_uit`.

    Deze node hoort met de huidige runner al te slagen en bewaakt de aanstaande
    wijziging tegen een te brede, profieloverstijgende uitsluiting.
    """
    root = _mini_project(tmp_path, SCOPE_SUITE)
    inventaris = tmp_path / "scope-unit-inventaris.json"

    resultaat = _draai_runner(
        root,
        "unit",
        "--inventory",
        str(inventaris),
        "--budget",
        "45",
        timeout=90,
    )

    assert _status(resultaat) == "ok", _uitvoer(resultaat)
    assert resultaat.returncode == 0, _uitvoer(resultaat)

    data = json.loads(inventaris.read_text(encoding="utf-8"))
    verzameld = {item["nodeid"] for item in data["items"]}
    assert verzameld == {SCOPE_ADVISORY_UNIT_NODE}, data
    assert data["uitgevoerd"] == 1, data
    assert data["overgeslagen"] == 0, data
    assert data["collectiefouten"] == 0, data


# --- De statusregel moet machineleesbaar blijven ----------------------------
#
# De runner deelt zijn stdout met het pytest-kind. Pytest schrijft
# voortgangstekens zonder afsluitende newline, dus op het moment dat een run
# hard eindigt of wordt afgekapt staat er een onafgesloten regel op die stroom.
# Plakt de statusregel daarachter, dan luidt de uitvoer
# `..[run_profile] status=...` en vindt geen enkele regelgebaseerde lezer de
# status nog — precies het patroon uit `root-final-unit-01/make.log`. De ouder
# kan de kolompositie van het kind niet uitlezen, dus de eigen newline moet
# onvoorwaardelijk zijn.

#: Onafgesloten uitvoer met een herkenbare vorm, zodat de proef aantoonbaar
#: iets vóór de statusregel heeft neergezet en niet stil op niets slaagt.
PARTIELE_UITVOER = "DEF519-PARTIELE-UITVOER-ZONDER-NEWLINE"

#: Schrijft die onafgesloten uitvoer en beëindigt het proces meteen daarna.
#: Deterministisch: geen sleep, geen budget en geen afhankelijkheid van de
#: volgorde waarin pytest zijn tests uitvoert.
PARTIELE_CONFTEST = (
    "import os\n"
    "import sys\n\n"
    "def pytest_collection_modifyitems(session, config, items):\n"
    f"    sys.stdout.write({PARTIELE_UITVOER!r})\n"
    "    sys.stdout.flush()\n"
    "    os._exit(0)\n"
)


def test_statusregel_begint_op_een_eigen_regel_na_partiele_uitvoer(tmp_path):
    """De statusregel mag nooit achter onafgesloten kinduitvoer plakken.

    Het kind zet hier aantoonbaar tekst zonder newline op de gedeelde stdout en
    stopt dan. De uitkomst zelf verandert niet — dit blijft `geen-inventaris`,
    met dezelfde exitcode — maar de statusregel moet als eigen regel leesbaar
    zijn. Er wordt niets aan de parser toegegeven: die blijft op
    `[run_profile] status=` aan het regelbegin zoeken.
    """
    root = _mini_project(
        tmp_path, GEZONDE_SUITE | {"tests/conftest.py": PARTIELE_CONFTEST}
    )
    resultaat = _draai_runner(root, "unit")
    uitvoer = _uitvoer(resultaat)

    # Zonder dit bewijs zou de proef ook slagen als er nooit partiële uitvoer was.
    assert PARTIELE_UITVOER in uitvoer, uitvoer

    statusregels = [
        regel
        for regel in uitvoer.splitlines()
        if regel.startswith("[run_profile] status=")
    ]
    assert len(statusregels) == 1, uitvoer
    assert PARTIELE_UITVOER not in statusregels[0], uitvoer
    assert _status(resultaat) == "geen-inventaris", uitvoer
    assert resultaat.returncode != 0, uitvoer


# --- Skip-, xfail- en XPASS-inventaris --------------------------------------
#
# De inventaris telde alleen `call`-rapporten. Daardoor viel een module die
# zichzelf bij collectie overslaat volledig weg (hij levert nooit een item op),
# bleef een setupskip ongeteld en ging een xfail als gewone skip door. De
# JUnit-uitvoer van dezelfde run rapporteert die uitkomsten wél, dus de twee
# administraties waren niet te reconciliëren.
#
# Het miniproject hieronder bevat precies één geval van elke soort. Elke node
# rekent op een echte waarde, zodat een uitgevoerde body ook werkelijk iets
# heeft bewezen.

INVENTARIS_COLLECTIE_BESTAND = "tests/test_def519_inv_collectieskip.py"
INVENTARIS_SETUP_BESTAND = "tests/test_def519_inv_setupskip.py"
INVENTARIS_SETUP_TEST = "test_wordt_in_setup_overgeslagen"
INVENTARIS_RUNTIME_BESTAND = "tests/test_def519_inv_runtimeskip.py"
INVENTARIS_RUNTIME_TEST = "test_slaat_zichzelf_in_de_body_over"
INVENTARIS_PASS_BESTAND = "tests/test_def519_inv_pass.py"
INVENTARIS_PASS_TEST = "test_reguliere_node_draait_echt"
INVENTARIS_XFAIL_BESTAND = "tests/test_def519_inv_xfail.py"
INVENTARIS_XFAIL_TEST = "test_strikte_xfail_faalt_zoals_verwacht"
INVENTARIS_XPASS_BESTAND = "tests/test_def519_inv_xpass.py"
INVENTARIS_XPASS_TEST = "test_nietstrikte_xfail_slaagt_toch"

#: De module slaat zichzelf op moduleniveau over: er komt geen enkel item uit,
#: dus deze uitkomst kan per definitie niet uit de nodetelling blijken.
INVENTARIS_COLLECTIE_BRON = (
    "import pytest\n\n"
    "pytest.skip('synthetische collectieskip', allow_module_level=True)\n"
)

INVENTARIS_SUITE = {
    INVENTARIS_COLLECTIE_BESTAND: INVENTARIS_COLLECTIE_BRON,
    INVENTARIS_SETUP_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.unit]\n\n\n"
        "@pytest.fixture\n"
        "def weigerende_fixture():\n"
        "    pytest.skip('synthetische setupskip')\n\n\n"
        f"def {INVENTARIS_SETUP_TEST}(weigerende_fixture):\n"
        "    assert False\n"
    ),
    INVENTARIS_RUNTIME_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.unit]\n\n\n"
        f"def {INVENTARIS_RUNTIME_TEST}():\n"
        "    pytest.skip('synthetische runtimeskip')\n"
    ),
    INVENTARIS_PASS_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.unit]\n\n\n"
        f"def {INVENTARIS_PASS_TEST}():\n"
        "    waarden = [2, 3]\n"
        "    assert sum(waarden) * 2 == 10\n"
    ),
    INVENTARIS_XFAIL_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.unit]\n\n\n"
        "@pytest.mark.xfail(strict=True, reason='synthetische strikte xfail')\n"
        f"def {INVENTARIS_XFAIL_TEST}():\n"
        "    waarden = [1, 1]\n"
        "    assert sum(waarden) * 2 == 5\n"
    ),
    INVENTARIS_XPASS_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.unit]\n\n\n"
        "@pytest.mark.xfail(strict=False, reason='synthetische XPASS')\n"
        f"def {INVENTARIS_XPASS_TEST}():\n"
        "    waarden = [4]\n"
        "    assert sum(waarden) * 2 == 8\n"
    ),
}

INVENTARIS_SETUP_NODE = f"{INVENTARIS_SETUP_BESTAND}::{INVENTARIS_SETUP_TEST}"
INVENTARIS_RUNTIME_NODE = f"{INVENTARIS_RUNTIME_BESTAND}::{INVENTARIS_RUNTIME_TEST}"
INVENTARIS_PASS_NODE = f"{INVENTARIS_PASS_BESTAND}::{INVENTARIS_PASS_TEST}"
INVENTARIS_XFAIL_NODE = f"{INVENTARIS_XFAIL_BESTAND}::{INVENTARIS_XFAIL_TEST}"
INVENTARIS_XPASS_NODE = f"{INVENTARIS_XPASS_BESTAND}::{INVENTARIS_XPASS_TEST}"

#: De vijf nodes die pytest werkelijk selecteert; de collectieskip hoort er
#: nadrukkelijk niet bij.
INVENTARIS_VERWACHT = {
    INVENTARIS_SETUP_NODE,
    INVENTARIS_RUNTIME_NODE,
    INVENTARIS_PASS_NODE,
    INVENTARIS_XFAIL_NODE,
    INVENTARIS_XPASS_NODE,
}


def _junit_sleutel(nodeid: str) -> str:
    """Node-id → de `classname`/`name`-sleutel die JUnit voor die node schrijft."""
    bestand, _, naam = nodeid.partition("::")
    return f"{bestand.removesuffix('.py').replace('/', '.')}::{naam}"


def _junit_gevallen(pad: Path) -> dict[str, set[str]]:
    """Per JUnit-geval de skiptypes, gesleuteld op `classname`/`name`."""
    import xml.etree.ElementTree as ET

    gevallen: dict[str, set[str]] = {}
    for geval in ET.parse(pad).getroot().iter("testcase"):
        sleutel = f"{geval.get('classname', '')}::{geval.get('name', '')}"
        gevallen[sleutel] = {kind.get("type", "") for kind in geval.iter("skipped")}
    return gevallen


def _junit_totalen(pad: Path) -> dict[str, int]:
    """De `testsuite`-attributen waarop CI en PR-comments tellen."""
    import xml.etree.ElementTree as ET

    suite = next(ET.parse(pad).getroot().iter("testsuite"))
    return {
        naam: int(suite.get(naam, "-1"))
        for naam in ("tests", "failures", "errors", "skipped")
    }


def test_inventaris_scheidt_collectieskip_setupskip_runtimeskip_en_xfail(tmp_path):
    """De inventaris moet elke overslag-soort apart en herleidbaar vastleggen.

    Vergeleken wordt met de JUnit van dezelfde run: dat is de administratie
    waarop CI telt. De collectieskip staat daar als eigen geval zonder
    classname en hoort per definitie niet bij de geselecteerde nodes; skips
    tellen per unieke node, ongeacht of ze in setup of in de body vallen; en de
    xfail is als `pytest.xfail` van een gewone skip te onderscheiden.

    De XPASS is het geval dat JUnit juist níét apart merkt — hij staat er als
    gewone pass. Dat is precies waarom de inventaris hem zelf zichtbaar moet
    maken.

    Met de huidige runner ontbreken alle vier de velden en telt `overgeslagen`
    alleen de runtimeskip: dat is de rode oorzaak van deze node.

    Binnendeadline 45s onder de buitendeadline 90s; niets wordt verwijderd.
    """
    root = _mini_project(tmp_path, INVENTARIS_SUITE)
    inventaris = tmp_path / "inventaris-scenario.json"
    junit_pad = tmp_path / "inventaris-scenario-junit.xml"

    resultaat = _draai_runner(
        root,
        "unit",
        "--inventory",
        str(inventaris),
        "--budget",
        "45",
        f"--junitxml={junit_pad}",
        timeout=90,
    )

    assert _status(resultaat) == "ok", _uitvoer(resultaat)
    assert resultaat.returncode == 0, _uitvoer(resultaat)

    data = json.loads(inventaris.read_text(encoding="utf-8"))
    verzameld = {item["nodeid"] for item in data["items"]}
    assert verzameld == INVENTARIS_VERWACHT, data

    # Werkelijk bereikte bodies: de reguliere pass en de XPASS. De xfail
    # bereikte zijn body ook, maar bewees geen assertie van de suite en telt
    # daarom bewust niet als uitvoering.
    assert data["uitgevoerd"] == 2, data

    assert data["overgeslagen"] == 2, data
    assert set(data["overgeslagen_nodes"]) == {
        INVENTARIS_SETUP_NODE,
        INVENTARIS_RUNTIME_NODE,
    }, data
    assert data["collectie_overgeslagen"] == 1, data
    assert data["collectie_overgeslagen_nodes"] == [INVENTARIS_COLLECTIE_BESTAND], data
    assert data["xfail"] == 1, data
    assert data["xfail_nodes"] == [INVENTARIS_XFAIL_NODE], data
    assert data["xpassed"] == 1, data
    assert data["xpassed_nodes"] == [INVENTARIS_XPASS_NODE], data
    assert data["collectiefouten"] == 0, data

    # --- Reconciliatie met de JUnit van dezelfde run ---
    assert junit_pad.is_file(), _uitvoer(resultaat)
    totalen = _junit_totalen(junit_pad)
    assert totalen == {"tests": 6, "failures": 0, "errors": 0, "skipped": 4}, totalen

    gevallen = _junit_gevallen(junit_pad)
    geselecteerd = {_junit_sleutel(nodeid) for nodeid in verzameld}
    collectie_sleutel = (
        f"::{INVENTARIS_COLLECTIE_BESTAND.removesuffix('.py').replace('/', '.')}"
    )
    # Het zesde JUnit-geval is de collectieskip: wél gerapporteerd, geen node.
    assert set(gevallen) == geselecteerd | {collectie_sleutel}, sorted(gevallen)
    assert gevallen[collectie_sleutel], gevallen

    skip_sleutels = {
        sleutel
        for sleutel, soorten in gevallen.items()
        if sleutel in geselecteerd and "pytest.skip" in soorten
    }
    assert skip_sleutels == {
        _junit_sleutel(nodeid) for nodeid in data["overgeslagen_nodes"]
    }, gevallen

    xfail_sleutels = {
        sleutel for sleutel, soorten in gevallen.items() if "pytest.xfail" in soorten
    }
    assert xfail_sleutels == {
        _junit_sleutel(nodeid) for nodeid in data["xfail_nodes"]
    }, gevallen

    # JUnit ziet de XPASS als gewone pass; alleen de inventaris maakt hem zichtbaar.
    assert gevallen[_junit_sleutel(INVENTARIS_XPASS_NODE)] == set(), gevallen
    assert gevallen[_junit_sleutel(INVENTARIS_PASS_NODE)] == set(), gevallen


def test_uitsluitend_xfail_is_geen_werkelijke_uitvoering(tmp_path):
    """Een xfail-only selectie mag niet als geslaagde uitvoering doorgaan.

    De body draait wél, maar pytest levert de uitkomst als `skipped` met
    `wasxfail` af: er is geen assertie van de suite mee bewezen. Deze node legt
    die bestaande semantiek vast, zodat de nieuwe xfail-telling haar niet
    ongemerkt in `uitgevoerd` kan laten meelopen.
    """
    root = _mini_project(
        tmp_path,
        {INVENTARIS_XFAIL_BESTAND: INVENTARIS_SUITE[INVENTARIS_XFAIL_BESTAND]},
    )
    inventaris = tmp_path / "xfail-only-inventaris.json"
    resultaat = _draai_runner(root, "unit", "--inventory", str(inventaris))

    assert resultaat.returncode != 0, _uitvoer(resultaat)
    assert _status(resultaat) == "geen-uitvoering", _uitvoer(resultaat)

    data = json.loads(inventaris.read_text(encoding="utf-8"))
    assert {item["nodeid"] for item in data["items"]} == {INVENTARIS_XFAIL_NODE}, data
    assert data["uitgevoerd"] == 0, data
    assert data["xfail"] == 1, data
