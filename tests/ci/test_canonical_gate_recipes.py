"""De gedocumenteerde Make-gates moeten de bewaakte profielen draaien (DEF-519).

Waarom deze suite bestaat
-------------------------
`scripts/testing/run_profile.py` is fail-closed bewezen in
`test_run_profile_fail_closed.py`, maar die suite roept de runner rechtstreeks
aan. Dat zegt niets over de commando's die mensen en CI werkelijk gebruiken.
Hier draait daarom de **echte `make`** op een eigen miniatuur-checkout, met de
ongewijzigde `Makefile` van dit project, en wordt gecontroleerd wat er
daadwerkelijk geselecteerd, uitgevoerd en gemeten is.

Veiligheidsontwerp
------------------
* Elke test bouwt een verse, synthetische checkout in `tmp_path`: de echte
  `Makefile`, de echte runner, de echte offline-bootstrap en de echte
  markercheck-scripts, plus eigen synthetische tests en één eigen `src`-module.
  De echte testsuite en `tests/conftest.py` worden nadrukkelijk **niet**
  gekopieerd — dat zou deze gate zichzelf laten draaien.
* `make` draait als kindproces in een eigen procesgroep met een harde
  buitendeadline; bij overschrijding gaat de hele groep neer, zodat er geen
  weeskinderen achterblijven. Er wordt niets verwijderd: alle artefacten blijven
  in `tmp_path` staan.
* De omgeving erft bewust een synthetische, niet-`dummy` providerkey en
  `ALLOW_NETWORK=1`. Slaagt een gate tóch, dan is dat bewijs dat de vroege
  bootstrap die omgeving heeft geneutraliseerd — niet dat de omgeving toevallig
  goed stond. Er is geen netwerk, geen echte key en geen gebruikersdata.
* `PY` wijst expliciet naar de projectinterpreter, want `check-python` eist 3.13.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

from tests import offline_bootstrap

pytestmark = [pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = REPO_ROOT / "Makefile"
RUNNER = REPO_ROOT / "scripts" / "testing" / "run_profile.py"
BOOTSTRAP = REPO_ROOT / "tests" / "offline_bootstrap.py"
MARKERCHECK = REPO_ROOT / "scripts" / "testing" / "check_test_markers.py"
MARKERUTILS = REPO_ROOT / "scripts" / "testing" / "_marker_utils.py"

#: Synthetische sleutel: de vórm van een providerkey, zonder geldige waarde.
#: Bewust niet `dummy`, zodat een gate die de omgeving zou erven aantoonbaar
#: iets anders ziet dan wat de bootstrap hoort te zetten.
SYNTHETISCHE_KEY = "sk-ant-api03-DEF519-SYNTHETISCH-GEEN-ECHTE-SLEUTEL"

#: Buitendeadline per `make`-aanroep. De gates krijgen zelf een kleiner
#: budget mee (`GATE_BUDGET`), zodat de runner eerder afkapt dan deze grens.
BUITENDEADLINE = 180

MINI_INI = (
    "[pytest]\n"
    "testpaths = tests\n"
    "pythonpath = src\n"
    "addopts = -q\n"
    "markers =\n"
    "    unit: unit\n"
    "    integration: integration\n"
    "    acceptance: acceptance\n"
    "    smoke: smoke\n"
    "    slow: slow\n"
    "    contract: contract\n"
    "    regression: regression\n"
    "    advisory: advisory\n"
    "    future: future\n"
    "    live: live\n"
)

#: Eigen `src`-module. `traag_pad` wordt uitsluitend door de slow-unittest
#: aangeroepen: hits op die regels bewijzen dat `slow` werkelijk meedeed.
GATEMODULE = "src/def519_gatemodule.py"
GATEMODULE_SNEL = (
    "def snel_pad(getallen):\n"
    "    totaal = 0\n"
    "    for getal in getallen:\n"
    "        totaal += getal\n"
    "    return totaal\n"
)
GATEMODULE_TRAAG = (
    "\n\ndef traag_pad(getallen):\n"
    "    tussenstand = 0\n"
    "    for getal in getallen:\n"
    "        tussenstand += getal * 2\n"
    "    tussenstand -= 1\n"
    "    return tussenstand\n"
)
#: Nooit aangeroepen; lang genoeg om de gemeten dekking onder de 45%-vloer te
#: duwen zonder een enkele echte regel te verzwakken.
GATEMODULE_ONGEDEKT = "".join(
    ["\n\ndef nooit_aangeroepen(waarde):\n"]
    + [f"    waarde += {n}\n" for n in range(1, 26)]
    + ["    return waarde\n"]
)

SNEL_BESTAND = "tests/test_gate_unit_snel.py"
SNELLE_TEST = "test_snelle_unitnode"
TRAAG_BESTAND = "tests/test_gate_unit_traag.py"
TRAGE_TEST = "test_trage_unitnode"
ACCEPTATIE_BESTAND = "tests/test_gate_acceptance.py"
ACCEPTATIE_TEST = "test_acceptancenode"
SMOKE_BESTAND = "tests/test_gate_smoke.py"
SMOKE_TEST = "test_smokenode"
MARKER_BESTAND = "tests/integration/test_gate_marker.py"
MARKER_TEST = "test_integration_markernode"
PAD_BESTAND = "tests/integration/test_gate_pad_contract.py"
PAD_TEST = "test_padnode_met_contractmarker"

SNELLE_NODE = f"{SNEL_BESTAND}::{SNELLE_TEST}"
TRAGE_NODE = f"{TRAAG_BESTAND}::{TRAGE_TEST}"
ACCEPTATIE_NODE = f"{ACCEPTATIE_BESTAND}::{ACCEPTATIE_TEST}"
SMOKE_NODE = f"{SMOKE_BESTAND}::{SMOKE_TEST}"
MARKER_NODE = f"{MARKER_BESTAND}::{MARKER_TEST}"
PAD_NODE = f"{PAD_BESTAND}::{PAD_TEST}"

UNIT_VERWACHT = {SNELLE_NODE, TRAGE_NODE}
ACCEPTATIE_VERWACHT = {ACCEPTATIE_NODE, SMOKE_NODE}
INTEGRATIE_VERWACHT = {MARKER_NODE, PAD_NODE}
#: Het contractprofiel selecteert op de `contract`-marker. In deze
#: miniatuur-checkout draagt precies één node die marker; diezelfde node zit
#: daarnaast in de integrationunie hierboven.
CONTRACT_VERWACHT = {PAD_NODE}

#: Elk synthetisch testbestand draagt een MODULE-pytestmark: de echte
#: markercheck accepteert geen losse functiedecorators.
BASISSUITE = {
    SNEL_BESTAND: (
        "import pytest\n\n"
        "from def519_gatemodule import snel_pad\n\n"
        "pytestmark = [pytest.mark.unit]\n\n\n"
        f"def {SNELLE_TEST}():\n"
        "    assert snel_pad([1, 2, 3]) == 6\n"
    ),
    TRAAG_BESTAND: (
        "import pytest\n\n"
        "from def519_gatemodule import traag_pad\n\n"
        "pytestmark = [pytest.mark.unit, pytest.mark.slow]\n\n\n"
        f"def {TRAGE_TEST}():\n"
        "    assert traag_pad([1, 2, 3]) == 11\n"
    ),
    ACCEPTATIE_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.acceptance]\n\n\n"
        f"def {ACCEPTATIE_TEST}():\n"
        "    waarden = [5, 5]\n"
        "    assert sum(waarden) * 2 == 20\n"
    ),
    SMOKE_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.smoke]\n\n\n"
        f"def {SMOKE_TEST}():\n"
        "    waarden = [6]\n"
        "    assert sum(waarden) * 2 == 12\n"
    ),
    MARKER_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.integration]\n\n\n"
        f"def {MARKER_TEST}():\n"
        "    waarden = [1, 2, 3]\n"
        "    assert sum(waarden) * 2 == 12\n"
    ),
    PAD_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.contract]\n\n\n"
        f"def {PAD_TEST}():\n"
        "    waarden = [3, 4, 5]\n"
        "    assert sum(waarden) * 2 == 24\n"
    ),
}


def _gate_project(
    tmp_path: Path,
    *,
    extra: dict[str, str] | None = None,
    basis: bool = True,
    dekking: str = "hoog",
) -> Path:
    """Verse miniatuur-checkout met de échte Makefile, runner en markercheck."""
    root = tmp_path / "gateproject"
    (root / "tests" / "integration").mkdir(parents=True)
    (root / "scripts" / "testing").mkdir(parents=True)
    (root / "src").mkdir()

    shutil.copy(MAKEFILE, root / "Makefile")
    shutil.copy(RUNNER, root / "scripts" / "testing" / "run_profile.py")
    shutil.copy(BOOTSTRAP, root / "tests" / "offline_bootstrap.py")
    shutil.copy(MARKERCHECK, root / "scripts" / "testing" / "check_test_markers.py")
    shutil.copy(MARKERUTILS, root / "scripts" / "testing" / "_marker_utils.py")
    (root / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (root / "pytest.ini").write_text(MINI_INI, encoding="utf-8")

    bron = GATEMODULE_SNEL + GATEMODULE_TRAAG
    if dekking == "laag":
        bron += GATEMODULE_ONGEDEKT
    (root / GATEMODULE).write_text(bron, encoding="utf-8")

    bestanden = dict(BASISSUITE) if basis else {}
    bestanden.update(extra or {})
    for naam, inhoud in bestanden.items():
        pad = root / naam
        pad.parent.mkdir(parents=True, exist_ok=True)
        pad.write_text(inhoud, encoding="utf-8")
    return root


def _gate_omgeving() -> dict[str, str]:
    """Omgeving die de gate juist moet neutraliseren, niet erven."""
    env = offline_bootstrap.omgeving_zonder_startupinstallatie()
    env["ANTHROPIC_API_KEY"] = SYNTHETISCHE_KEY
    env["OPENAI_API_KEY"] = SYNTHETISCHE_KEY
    env["ALLOW_NETWORK"] = "1"
    for naam in ("DEFINITIE_DISABLE_DOTENV", "DEF519_SESSION_ROOT", "PYTEST_ADDOPTS"):
        env.pop(naam, None)
    return env


class MakeResultaat:
    """Uitkomst van één `make`-aanroep, plus de artefacten van die gate."""

    def __init__(self, returncode: int, uitvoer: str, rapportmap: Path):
        self.returncode = returncode
        self.uitvoer = uitvoer
        self.rapportmap = rapportmap

    def status(self) -> str:
        for regel in self.uitvoer.splitlines():
            if regel.startswith("[run_profile] status="):
                return regel.split("status=", 1)[1].split(" ", 1)[0]
        return ""

    def inventaris(self, naam: str) -> dict:
        pad = self.rapportmap / naam
        assert pad.is_file(), f"{pad} ontbreekt\n{self.uitvoer}"
        return json.loads(pad.read_text(encoding="utf-8"))

    def nodes(self, naam: str) -> set[str]:
        return {item["nodeid"] for item in self.inventaris(naam)["items"]}


def _draai_make(
    root: Path, doel: str, *, budget: str = "120", timeout: int = BUITENDEADLINE
) -> MakeResultaat:
    """Roep de échte `make` aan in een eigen procesgroep met harde deadline."""
    rapportmap = root.parent / f"rapporten-{doel}"
    opdracht = [
        "make",
        "-C",
        str(root),
        f"PY={sys.executable}",
        f"GATE_REPORTS={rapportmap}",
        f"GATE_BUDGET={budget}",
        doel,
    ]
    proces = subprocess.Popen(
        opdracht,
        env=_gate_omgeving(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    try:
        uitvoer, _ = proces.communicate(timeout=timeout)
        code = proces.returncode
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proces.pid), signal.SIGKILL)
        uitvoer, _ = proces.communicate(timeout=30)
        code = 124
    return MakeResultaat(code, uitvoer or "", rapportmap)


def _lijnen(xml_pad: Path, bestandsnaam: str) -> dict[int, int]:
    """Regelnummer → hits voor `bestandsnaam` in een coverage-XML."""
    for klasse in ET.parse(xml_pad).getroot().iter("class"):
        if Path(klasse.get("filename", "")).name == bestandsnaam:
            return {
                int(r.get("number")): int(r.get("hits", "0"))
                for r in klasse.iter("line")
            }
    return {}


# --- De drie hoofdcommando's ------------------------------------------------


def test_make_test_unit_draait_de_canonieke_unitgate(tmp_path):
    """`make test-unit` moet de runner draaien: alle unit, inclusief slow.

    Bewijs uit de gate zelf: de inventaris bevat exact de twee unitnodes, beide
    bodies draaiden, en het bootstrapbewijs is aanwezig op de sessieroot van
    déze run — ondanks de geërfde synthetische key en `ALLOW_NETWORK=1`.
    """
    root = _gate_project(tmp_path)
    resultaat = _draai_make(root, "test-unit")

    assert resultaat.returncode == 0, resultaat.uitvoer
    assert resultaat.status() == "ok", resultaat.uitvoer

    data = resultaat.inventaris("unit-inventaris.json")
    assert {item["nodeid"] for item in data["items"]} == UNIT_VERWACHT, data
    assert data["uitgevoerd"] == 2, data
    assert data["overgeslagen"] == 0, data
    assert data["bootstrap"]["gate_actief"] is True, data
    assert data["bootstrap"]["sessieroot"], data
    assert (resultaat.rapportmap / "unit-junit.xml").is_file(), resultaat.uitvoer


def test_make_test_integration_dekt_de_padunie(tmp_path):
    """`make test-integration` neemt padtests zonder integrationmarker mee."""
    root = _gate_project(tmp_path)
    resultaat = _draai_make(root, "test-integration")

    assert resultaat.returncode == 0, resultaat.uitvoer
    assert resultaat.status() == "ok", resultaat.uitvoer

    data = resultaat.inventaris("integration-inventaris.json")
    assert {item["nodeid"] for item in data["items"]} == INTEGRATIE_VERWACHT, data
    assert data["uitgevoerd"] == 2, data
    assert data["overgeslagen"] == 0, data


def test_make_test_acceptance_selecteert_acceptance_en_smoke(tmp_path):
    """`make test-acceptance` draait het acceptance-smoke-profiel."""
    root = _gate_project(tmp_path)
    resultaat = _draai_make(root, "test-acceptance")

    assert resultaat.returncode == 0, resultaat.uitvoer
    assert resultaat.status() == "ok", resultaat.uitvoer

    data = resultaat.inventaris("acceptance-smoke-inventaris.json")
    assert {item["nodeid"] for item in data["items"]} == ACCEPTATIE_VERWACHT, data
    assert data["uitgevoerd"] == 2, data


# --- Gedocumenteerde aliassen ------------------------------------------------


def test_make_test_is_alias_van_de_unitgate(tmp_path):
    """`make test` moet dezelfde selectie draaien als `make test-unit`.

    De oude alias draaide `unit and not slow` met `--maxfail=1`: een kleinere
    scope onder dezelfde naam. Die stille afwijking is precies wat hier faalt.
    """
    root = _gate_project(tmp_path)
    resultaat = _draai_make(root, "test")

    assert resultaat.returncode == 0, resultaat.uitvoer
    assert resultaat.status() == "ok", resultaat.uitvoer
    data = resultaat.inventaris("unit-inventaris.json")
    assert {item["nodeid"] for item in data["items"]} == UNIT_VERWACHT, data
    assert data["uitgevoerd"] == 2, data
    # De bestaande markercheck blijft een prerequisite van deze alias.
    assert "test files have classification markers" in resultaat.uitvoer


def test_make_test_smoke_is_alias_van_de_acceptancegate(tmp_path):
    """`make test-smoke` draait dezelfde acceptance-smoke-scope."""
    root = _gate_project(tmp_path)
    resultaat = _draai_make(root, "test-smoke")

    assert resultaat.returncode == 0, resultaat.uitvoer
    assert resultaat.status() == "ok", resultaat.uitvoer
    data = resultaat.inventaris("acceptance-smoke-inventaris.json")
    assert {item["nodeid"] for item in data["items"]} == ACCEPTATIE_VERWACHT, data


# --- Fail-closed: sabotage, leegte, collectiefout, budget --------------------


ROOD_PAD_BESTAND = "tests/integration/test_gate_pad_rood.py"
ROOD_PAD_TEST = "test_padnode_faalt_op_echte_assertie"
ROOD_PAD_NODE = f"{ROOD_PAD_BESTAND}::{ROOD_PAD_TEST}"
SABOTAGE = {
    ROOD_PAD_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.contract]\n\n\n"
        f"def {ROOD_PAD_TEST}():\n"
        "    waarden = [1, 1]\n"
        "    assert sum(waarden) * 2 == 5\n"
    )
}


def test_falende_padtest_maakt_make_test_integration_nonzero(tmp_path):
    """Sabotage: één rood bestand onder het integratiepad maakt de gate rood.

    Het bestand draagt bewust géén integrationmarker — precies zoals de
    contract-, regression- en compliancebestanden in de echte suite. Exact
    hetzelfde `make test-integration` moet daarop nonzero geven.
    """
    root = _gate_project(tmp_path, extra=SABOTAGE)
    resultaat = _draai_make(root, "test-integration")

    assert resultaat.status() == "testfalen", resultaat.uitvoer
    assert resultaat.returncode != 0, resultaat.uitvoer
    data = resultaat.inventaris("integration-inventaris.json")
    verzameld = {item["nodeid"] for item in data["items"]}
    assert ROOD_PAD_NODE in verzameld, data
    assert data["uitgevoerd"] == 3, data


def test_lege_selectie_is_nonzero_zonder_groene_route(tmp_path):
    """Geen integratietests: nonzero, nooit een stille groene doorgang.

    De oude CI-stap sloeg de hele integratiestap over als `tests/integration`
    ontbrak (`if [ -d ... ]`) en meldde succes. Hier bestaat de map niet en
    bestaat er geen enkele integratienode; dat hoort een harde fout te zijn.
    """
    root = _gate_project(
        tmp_path,
        basis=False,
        extra={
            SNEL_BESTAND: BASISSUITE[SNEL_BESTAND],
            TRAAG_BESTAND: BASISSUITE[TRAAG_BESTAND],
        },
    )
    resultaat = _draai_make(root, "test-integration")

    assert resultaat.status() == "lege-selectie", resultaat.uitvoer
    assert resultaat.returncode != 0, resultaat.uitvoer


def test_collectiefout_maakt_de_gate_nonzero(tmp_path):
    """Een niet-importeerbaar testbestand is een harde fout, geen overslaan."""
    root = _gate_project(
        tmp_path,
        extra={
            "tests/integration/test_gate_kapot.py": (
                "import pytest\n\n"
                "pytestmark = [pytest.mark.integration]\n\n"
                "import def519_bestaat_niet\n"
            )
        },
    )
    resultaat = _draai_make(root, "test-integration")

    assert resultaat.status() == "collectiefout", resultaat.uitvoer
    assert resultaat.returncode != 0, resultaat.uitvoer


#: Onafgesloten uitvoer, in de vorm waarin pytest zijn eigen voortgangstekens
#: schrijft. De hangende node zet hem zelf neer, vlak voordat hij het budget
#: overschrijdt. Dat maakt de proef deterministisch: het aantal voortgangstekens
#: dat pytest zelf vóór de hang produceert hangt af van hoeveel nodes al klaar
#: zijn, en die volgorde ligt met `pytest-randomly` niet vast.
#:
#: De node moet daarvoor de globale capture even opschorten — precies de greep
#: die pytest zelf gebruikt om zijn voortgang op de echte stdout te zetten.
#: Zonder die stap vangt pytest de uitvoer af in zijn capturebestand en bereikt
#: zij de gedeelde stroom nooit.
GATE_PARTIELE_UITVOER = "DEF519-PARTIELE-UITVOER-ZONDER-NEWLINE"


def test_budgetoverschrijding_is_nonzero(tmp_path):
    """Een gate die zijn eindige budget overschrijdt, faalt hard en leesbaar.

    Het budget (5s) ligt ruim onder de buitendeadline van deze test (25s), zodat
    de runner zelf afkapt en zijn eigen procesgroep opruimt. Kapt hij niet af,
    dan grijpt de buitendeadline in — ruim binnen de per-test-timeout van deze
    suite, zodat een regressie hier zichtbaar faalt in plaats van te hangen.

    De hangende node schrijft eerst tekst zonder afsluitende newline op de
    stdout die hij met de runner deelt. Zonder een eigen newline in de melding
    plakt de statusregel daarachter (`..[run_profile] status=…`) en vindt geen
    enkele regelgebaseerde lezer de status nog — het patroon uit
    `root-final-unit-01/make.log`. Status, exitcode en deadline blijven exact
    hetzelfde; alleen de leesbaarheid van de regel wordt hier bewaakt.
    """
    root = _gate_project(
        tmp_path,
        extra={
            "tests/integration/test_gate_traag.py": (
                "import sys\nimport time\n\nimport pytest\n\n"
                "pytestmark = [pytest.mark.integration]\n\n\n"
                "def test_hangt_langer_dan_het_budget(request):\n"
                "    capman = request.config.pluginmanager.getplugin('capturemanager')\n"
                "    capman.suspend_global_capture(in_=False)\n"
                f"    sys.stdout.write({GATE_PARTIELE_UITVOER!r})\n"
                "    sys.stdout.flush()\n"
                "    time.sleep(45)\n"
            )
        },
    )
    resultaat = _draai_make(root, "test-integration", budget="5", timeout=25)

    # Zonder dit bewijs zou de proef ook slagen als er nooit partiële uitvoer was.
    assert GATE_PARTIELE_UITVOER in resultaat.uitvoer, resultaat.uitvoer
    statusregels = [
        regel
        for regel in resultaat.uitvoer.splitlines()
        if regel.startswith("[run_profile] status=")
    ]
    assert len(statusregels) == 1, resultaat.uitvoer
    assert GATE_PARTIELE_UITVOER not in statusregels[0], resultaat.uitvoer

    assert resultaat.status() == "budget-overschreden", resultaat.uitvoer
    assert resultaat.returncode != 0, resultaat.uitvoer


# --- Contractgate (required check "Validation Contract Tests") ---------------


def _junit_tellingen(pad: Path) -> dict[str, int]:
    """De testsuite-attributen die de PR-comment van de contractjob afleest."""
    suite = next(ET.parse(pad).getroot().iter("testsuite"))
    return {
        naam: int(suite.get(naam, "-1"))
        for naam in ("tests", "failures", "errors", "skipped")
    }


def test_make_test_contract_selecteert_en_draait_de_contractnode(tmp_path):
    """`make test-contract` voert de contractnode werkelijk uit.

    De contractjob is een required check, dus de gate moet een niet-lege
    selectie mét uitgevoerde body opleveren — niet slechts een bestaand
    rapportbestand. Het JUnit-rapport wordt hier inhoudelijk gelezen, want dat
    is exact wat de PR-comment van die job telt.
    """
    root = _gate_project(tmp_path)
    resultaat = _draai_make(root, "test-contract")

    assert resultaat.returncode == 0, resultaat.uitvoer
    assert resultaat.status() == "ok", resultaat.uitvoer

    data = resultaat.inventaris("contract-inventaris.json")
    assert {item["nodeid"] for item in data["items"]} == CONTRACT_VERWACHT, data
    assert data["uitgevoerd"] == 1, data
    assert data["overgeslagen"] == 0, data
    assert data["bootstrap"]["gate_actief"] is True, data

    junit = resultaat.rapportmap / "contract-junit.xml"
    assert junit.is_file(), resultaat.uitvoer
    assert _junit_tellingen(junit) == {
        "tests": 1,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
    }, junit.read_text(encoding="utf-8")


def test_falende_contractnode_maakt_make_test_contract_nonzero(tmp_path):
    """Eén rode contractnode maakt exact hetzelfde `make test-contract` rood.

    De oude job had een `|| python -m pytest ...`-fallback: een tweede,
    bredere aanroep kon een echte contractfout overschrijven. Hier telt alleen
    de ene aanroep, en die hoort nonzero te zijn zodra een contractnode faalt.
    """
    root = _gate_project(tmp_path, extra=SABOTAGE)
    resultaat = _draai_make(root, "test-contract")

    assert resultaat.status() == "testfalen", resultaat.uitvoer
    assert resultaat.returncode != 0, resultaat.uitvoer

    data = resultaat.inventaris("contract-inventaris.json")
    verzameld = {item["nodeid"] for item in data["items"]}
    assert verzameld == CONTRACT_VERWACHT | {ROOD_PAD_NODE}, data
    assert data["uitgevoerd"] == 2, data

    junit = resultaat.rapportmap / "contract-junit.xml"
    assert junit.is_file(), resultaat.uitvoer
    tellingen = _junit_tellingen(junit)
    assert tellingen["tests"] == 2, tellingen
    assert tellingen["failures"] == 1, tellingen
    assert tellingen["errors"] == 0, tellingen


# --- Coverage-ratchet --------------------------------------------------------


def test_make_test_cov_ci_meet_alle_unit_inclusief_slow(tmp_path):
    """`make test-cov-ci` meet de volledige unitscope tegen de 45%-vloer.

    De slow-only functie `traag_pad` wordt uitsluitend door de slow-unittest
    aangeroepen. Hits op die regels zijn dus het bewijs dat de ratchetmeting
    `slow` werkelijk meeneemt en niet stilzwijgend een kleinere scope meet.
    """
    root = _gate_project(tmp_path)
    resultaat = _draai_make(root, "test-cov-ci")

    assert resultaat.returncode == 0, resultaat.uitvoer
    assert resultaat.status() == "ok", resultaat.uitvoer

    data = resultaat.inventaris("unit-cov-inventaris.json")
    assert {item["nodeid"] for item in data["items"]} == UNIT_VERWACHT, data
    assert data["uitgevoerd"] == 2, data

    xml = resultaat.rapportmap / "unit-coverage.xml"
    assert xml.is_file(), resultaat.uitvoer
    hits = _lijnen(xml, Path(GATEMODULE).name)
    assert hits, resultaat.uitvoer
    # `traag_pad` begint na de vijf regels van `snel_pad`; die body is alleen
    # via de slow-node bereikbaar.
    slow_regels = [nummer for nummer in hits if nummer >= 8]
    assert slow_regels, hits
    assert all(hits[nummer] > 0 for nummer in slow_regels), hits

    # De gate wijst naar de coveragedata die zij zelf heeft geproduceerd, zodat
    # CI precies dát bestand kan archiveren.
    artefact = data.get("coverage_artefacten")
    assert isinstance(artefact, dict), data
    assert Path(artefact["data_file"]).is_file(), artefact
    assert str(root) not in artefact["data_file"], artefact


def test_make_test_cov_ci_faalt_onder_de_vloer(tmp_path):
    """Een echt niet-gehaalde 45%-vloer maakt `make test-cov-ci` nonzero.

    Het XML-rapport wordt inhoudelijk gelezen: de nooit aangeroepen body heeft
    aantoonbaar nul hits en de gemeten line-rate ligt onder 0,45. Dit is een
    meting op een eigen synthetische bron en zegt niets over het projectcijfer.
    """
    root = _gate_project(tmp_path, dekking="laag")
    resultaat = _draai_make(root, "test-cov-ci")

    assert resultaat.status() == "coverage-onder-vloer", resultaat.uitvoer
    assert resultaat.returncode != 0, resultaat.uitvoer

    xml = resultaat.rapportmap / "unit-coverage.xml"
    assert xml.is_file(), resultaat.uitvoer
    hits = _lijnen(xml, Path(GATEMODULE).name)
    ongeraakt = [nummer for nummer, aantal in hits.items() if aantal == 0]
    assert len(ongeraakt) >= 20, hits
    klasse = next(
        k
        for k in ET.parse(xml).getroot().iter("class")
        if Path(k.get("filename", "")).name == Path(GATEMODULE).name
    )
    assert float(klasse.get("line-rate")) < 0.45, klasse.attrib


def test_gates_schrijven_gescheiden_artefacten(tmp_path):
    """Unit-, integration- en coveragegate delen geen enkel artefactpad.

    Zonder scheiding overschrijft een latere gate de meting van de ratchet —
    precies het patroon uit DEF-679.
    """
    root = _gate_project(tmp_path)
    unit = _draai_make(root, "test-unit")
    integratie = _draai_make(root, "test-integration")
    dekking = _draai_make(root, "test-cov-ci")

    assert unit.returncode == 0, unit.uitvoer
    assert integratie.returncode == 0, integratie.uitvoer
    assert dekking.returncode == 0, dekking.uitvoer

    paden = set()
    for resultaat, naam in (
        (unit, "unit-inventaris.json"),
        (integratie, "integration-inventaris.json"),
        (dekking, "unit-cov-inventaris.json"),
    ):
        pad = resultaat.rapportmap / naam
        assert pad.is_file(), resultaat.uitvoer
        paden.add(pad)
    assert len(paden) == 3

    # De ratchetmeting staat op haar eigen pad; geen enkele gate schrijft een
    # `.coverage` in de checkout zelf.
    assert (dekking.rapportmap / "unit-coverage.xml").is_file()
    assert not (root / ".coverage").exists()


# --- De required CI-job moet de canonieke gate draaien ----------------------
#
# De `tests`-job van `.github/workflows/ci.yml` draaide een eigen pytest-subset
# met `--cov=src`. pytest-cov schrijft dan `.coverage.*` in de checkout; de
# vroege offline-bootstrap weigert dat terecht, en op PR #427 eindigde de stap
# in een INTERNALERROR (`pr427-tests-job-view-01.log`). Het was bovendien een
# tweede selectie naast de Makefile.
#
# De nodes hieronder lezen `jobs.tests.steps` gestructureerd en toetsen het
# werkelijke `run`-veld, niet losse jobtekst: een stapnaam die de gate noemt
# terwijl het commando niets doet, moet worden afgewezen. Het gevonden doel
# wordt daarna echt gedraaid op de miniatuur-checkout. Er wordt uitsluitend
# gelezen — geen workflowsetup, geen netwerk, geen tweede runtime.

CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

#: Naam waaronder deze job zijn eigen gate-rapporten bewaart. Eigen naam, zodat
#: de artefacten van `test.yml` niet worden overschreven.
CI_ARTEFACTNAAM = "acceptance-gate-results"

#: `make <doel>` in een runveld. Alleen de canonieke gatedoelen tellen.
_MAKE_DOEL = re.compile(r"\bmake\s+(test-[a-z-]+)\b")


def _ci_stappen() -> list[dict]:
    """De stappen van `jobs.tests` uit `ci.yml`.

    `yaml.safe_load` bouwt alleen datastructuren op; er wordt niets uit de
    workflow geëvalueerd of uitgevoerd.
    """
    document = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    return document["jobs"]["tests"]["steps"]


def _ci_runvelden() -> list[str]:
    """Uitsluitend de werkelijke `run`-commando's van die stappen."""
    return [stap["run"] for stap in _ci_stappen() if isinstance(stap.get("run"), str)]


def _ci_gatestap() -> dict:
    """De ene stap waarvan het `run`-veld een canoniek gatedoel aanroept."""
    stappen = [
        stap
        for stap in _ci_stappen()
        if isinstance(stap.get("run"), str) and _MAKE_DOEL.search(stap["run"])
    ]
    assert stappen, (
        "geen enkele stap in de tests-job draait een canoniek make-gatedoel; "
        f"gevonden runvelden: {_ci_runvelden()}"
    )
    assert len(stappen) == 1, f"meer dan één gatestap in de tests-job: {stappen}"
    return stappen[0]


def _ci_gate_doel() -> str:
    """Het make-doel dat de required `tests`-job onvoorwaardelijk aanroept."""
    stap = _ci_gatestap()
    commando = stap["run"].strip()
    assert commando == "make test-acceptance", commando
    # Onvoorwaardelijk en blokkerend: geen `if:` en geen continue-on-error.
    assert "if" not in stap, stap
    assert stap.get("continue-on-error") in (None, False), stap
    return _MAKE_DOEL.search(commando).group(1)


def _ci_artefactstap() -> dict:
    """De ene stap die de gate-rapporten als artefact bewaart."""
    stappen = [
        stap
        for stap in _ci_stappen()
        if str(stap.get("uses", "")).startswith("actions/upload-artifact@")
    ]
    assert len(stappen) == 1, f"verwacht precies één uploadstap: {stappen}"
    return stappen[0]


#: Workflowvariant waarin alleen de *naam* en het commentaar de gate nog
#: noemen, terwijl de runregel niets doet. Een lezer die op losse tekst zoekt
#: keurt dit goed; het echte commando is dan `true` en de gate draait niet.
CI_VARIANT_ZONDER_ECHT_COMMANDO = """name: CI

on:
  pull_request:
    branches: [main]

jobs:
  tests:
    runs-on: ubuntu-latest

    steps:
      # Hier stond ooit: make test-acceptance
      - name: Acceptance/smoke gate (make test-acceptance, blokkerend)
        run: true

      - name: Archive acceptance gate results
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: acceptance-gate-results
          path: |
            reports/gates/
"""


def test_contractlezer_wijst_stapnaam_zonder_echt_commando_af(tmp_path, monkeypatch):
    """De koppeling moet op het runveld zitten, niet op losse jobtekst.

    Discriminator: in deze variant blijven de stapnaam en het commentaar
    `make test-acceptance` noemen, maar het werkelijke commando is `true`. Een
    lezer die de jobtekst doorzoekt keurt dat goed en houdt beide gedragsproeven
    hieronder groen zonder dat CI de gate nog draait. De contractlezer hoort de
    variant daarom af te wijzen.

    Het bestand leeft alleen in `tmp_path`; er wordt niets uitgevoerd.
    """
    variant = tmp_path / "ci-variant.yml"
    variant.write_text(CI_VARIANT_ZONDER_ECHT_COMMANDO, encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "CI_WORKFLOW", variant)

    with pytest.raises(AssertionError, match="make-gatedoel"):
        _ci_gate_doel()


def test_ci_tests_job_draait_de_canonieke_acceptancegate(tmp_path):
    """`ci.yml` moet de acceptance/smoke-gate draaien en haar rapporten bewaren.

    Eerst het contract van het workflowbestand zelf: één canoniek make-doel,
    geen eigen pytest-subset en geen `--cov` in deze job (dat is precies wat
    `.coverage.*` in de checkout schreef en de bootstrap deed weigeren). De
    unitcoverage-ratchet blijft waar hij hoort, in `test.yml`; hier wordt geen
    tweede coveragemeting opgetuigd.

    Daarna hetzelfde doel écht draaien op de miniatuur-checkout: de gate moet
    zowel de acceptance- als de smokenode selecteren én uitvoeren. Zou `ci.yml`
    een ander doel noemen, dan ontbreekt de acceptance-inventaris en faalt deze
    node — de koppeling is dus geen tekstvergelijking alleen.
    """
    doel = _ci_gate_doel()
    assert doel == "test-acceptance"

    # Geen tweede, eigen selectie of coveragemeting in deze job.
    commandos = "\n".join(_ci_runvelden())
    assert "python -m pytest" not in commandos, commandos
    assert "--cov" not in commandos, commandos

    # Rapporten blijven bewaard, volgens de bestaande artefactconventie en met
    # een eigen naam voor deze job.
    artefact = _ci_artefactstap()
    assert artefact["uses"] == "actions/upload-artifact@v7", artefact
    assert artefact["if"] == "always()", artefact
    assert artefact["with"]["name"] == CI_ARTEFACTNAAM, artefact
    assert "reports/gates/" in artefact["with"]["path"].split(), artefact

    root = _gate_project(tmp_path)
    resultaat = _draai_make(root, doel)

    assert resultaat.returncode == 0, resultaat.uitvoer
    assert resultaat.status() == "ok", resultaat.uitvoer

    data = resultaat.inventaris("acceptance-smoke-inventaris.json")
    verzameld = {item["nodeid"] for item in data["items"]}
    assert verzameld == ACCEPTATIE_VERWACHT, data
    assert ACCEPTATIE_NODE in verzameld, data
    assert SMOKE_NODE in verzameld, data
    assert data["uitgevoerd"] == 2, data
    assert data["overgeslagen"] == 0, data
    assert data["collectiefouten"] == 0, data


#: Falende smokenode: draagt de smokemarker en faalt op een echte assertie.
CI_ROOD_SMOKE_BESTAND = "tests/test_gate_smoke_rood.py"
CI_ROOD_SMOKE_TEST = "test_smokenode_faalt_op_echte_assertie"
CI_ROOD_SMOKE_NODE = f"{CI_ROOD_SMOKE_BESTAND}::{CI_ROOD_SMOKE_TEST}"
CI_ROOD_SMOKE = {
    CI_ROOD_SMOKE_BESTAND: (
        "import pytest\n\n"
        "pytestmark = [pytest.mark.smoke]\n\n\n"
        f"def {CI_ROOD_SMOKE_TEST}():\n"
        "    waarden = [2, 2]\n"
        "    assert sum(waarden) * 2 == 9\n"
    )
}


def test_ci_gatedoel_is_nonzero_bij_falende_smokenode(tmp_path):
    """Een falende geselecteerde node maakt exact dit CI-commando rood.

    Zonder deze proef zou de node hierboven ook groen blijven bij een gate die
    niets kan laten falen. Het doel komt weer uit `ci.yml`; er wordt niets
    verwijderd en de rode node leeft alleen in `tmp_path`.
    """
    doel = _ci_gate_doel()
    root = _gate_project(tmp_path, extra=CI_ROOD_SMOKE)
    resultaat = _draai_make(root, doel)

    assert resultaat.status() == "testfalen", resultaat.uitvoer
    assert resultaat.returncode != 0, resultaat.uitvoer

    data = resultaat.inventaris("acceptance-smoke-inventaris.json")
    verzameld = {item["nodeid"] for item in data["items"]}
    assert CI_ROOD_SMOKE_NODE in verzameld, data
    assert verzameld == ACCEPTATIE_VERWACHT | {CI_ROOD_SMOKE_NODE}, data
    assert data["uitgevoerd"] == 3, data
