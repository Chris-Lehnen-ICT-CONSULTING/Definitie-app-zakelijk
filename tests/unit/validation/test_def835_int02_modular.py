"""DEF-835 WP5a: INT-02 (O2) via de echte `ModularValidationService` (eerst rood).

De WP3-evaluator `decision_rule_assessment` levert zijn uitkomst als
gestructureerde deeluitkomst; de modulaire service moet die voor elke status
in `rule_results['INT-02']` boeken, zonder cijfer en zonder poort
(`excluded_from_score`, besluiten B5/B6). De wrapper moet daarnaast in de
actieve regelset kunnen lezen welke evaluator INT-02 kiest
(`evaluator_voor`), zodat de O1-route nooit een INT-02-modelaanroep doet.

Het actieve `INT-02.json` blijft O1 (`judgment_review`). Een O2-regelset is
hier een tijdelijke kopie van alle regelbestanden waarin alleen het
INT-02-runtimecontract naar `decision_rule_assessment` wijst. De documenten
komen uit de WP1-functie `beoordeel` met handmatig ingevulde modelresponsen
uit de ontwerpgevallen: zij bewijzen de ketenmapping, geen modelkwaliteit.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from domain.int02.contract import (
    CONTRACTVERSIE,
    MELDING_E,
    MELDING_NE,
    MELDING_NIET_BEOORDEELD,
    Configuratie,
    Uitvoering,
    beoordeel,
    maak_invoer,
)
from services.validation import modular_validation_service as mvs
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import ToetsregelManager
from toetsregels.runtime_contract import EvaluatorType

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
REGELS = ROOT / "src" / "toetsregels" / "regels"
GEVALLEN = json.loads(
    (ROOT / "tests" / "fixtures" / "def835_int02_ontwerpgevallen.json").read_text(
        "utf-8"
    )
)["gevallen"]

#: Synthetische configuratie; geen echt profiel, geen modelkwalificatie.
CONFIG = Configuratie(
    normhash="a" * 64,
    promptversie="def835-wp5a-fixture/1",
    routeringshash="b" * 64,
    provider="fakeprovider",
    model="fake-int02-model",
)
VOLTOOID = Uitvoering(actor="ai", status="completed")


def _geval(geval_id: str, variant: str | None = None) -> dict[str, Any]:
    for geval in GEVALLEN:
        if geval["id"] == geval_id and geval.get("variant") == variant:
            return copy.deepcopy(geval)
    raise AssertionError(f"ontwerpgeval {geval_id}/{variant} ontbreekt")


def _invoer(geval: dict[str, Any]):
    return maak_invoer(**geval["invoer"])


def _document(geval: dict[str, Any], respons: Any = None):
    respons = geval["modelrespons"] if respons is None else respons
    return beoordeel(_invoer(geval), CONFIG, respons, VOLTOOID)


def _na_respons() -> dict[str, Any]:
    return {
        "verdict": "not_applicable",
        "passages": [],
        "reason": "Synthetische reikwijdtegrond.",
        "question": None,
        "uncertainty": "none",
        "scope_reason": "Synthetische tekst buiten het definitietoetsbereik.",
        "coverage": "none",
    }


def _pass_respons_c105() -> dict[str, Any]:
    kern = _geval("C105")["invoer"]["kern"]
    return {
        "verdict": "pass",
        "passages": [
            {
                "quote": kern,
                "start": 0,
                "end": len(kern),
                "function": "criterion",
                "ground": {
                    "field": "kern",
                    "ref": None,
                    "quote": None,
                    "start": None,
                    "end": None,
                },
            }
        ],
        "reason": "Synthetische pass voor de mapping; geen modeloordeel.",
        "question": None,
        "uncertainty": "none",
        "scope_reason": None,
        "coverage": "complete",
    }


def _onvoldoende_respons_c105() -> dict[str, Any]:
    return {
        "verdict": "insufficient_information",
        "passages": [],
        "reason": "Synthetisch: de bedoelde functie is onduidelijk.",
        "question": "Beschrijft de zin een kenmerk of een opdracht?",
        "uncertainty": "decisive",
        "scope_reason": None,
        "coverage": "partial",
    }


def _metadata(geval: dict[str, Any], document=None, configuratie=CONFIG) -> dict:
    invoer = geval["invoer"]
    metadata: dict[str, Any] = {
        "record_text": invoer["kern"],
        "organisatorische_context": list(invoer["organisatorische_context"]),
        "juridische_context": list(invoer["juridische_context"]),
        "wettelijke_basis": list(invoer["wettelijke_basis"]),
        "int02_bedoeling": invoer["bedoeling"],
        "int02_bronnen": copy.deepcopy(invoer["bronnen"]),
    }
    if configuratie is not None:
        metadata["int02_configuratie"] = configuratie
    if document is not None:
        metadata["int02_document"] = document
    return metadata


@pytest.fixture(scope="module")
def o2_regelmap(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Kopie van alle regelbestanden; alleen INT-02 wijst naar de O2-evaluator."""
    doel = tmp_path_factory.mktemp("def835_wp5a_o2") / "regels"
    doel.mkdir()
    for pad in sorted(REGELS.glob("*.json")):
        tekst = pad.read_text("utf-8")
        if pad.stem == "INT-02":
            data = json.loads(tekst)
            data["runtime_contract"].update(
                {
                    "evaluator": "decision_rule_assessment",
                    "automation_status": "automated",
                }
            )
            tekst = json.dumps(data, ensure_ascii=False, indent=2)
        (doel / pad.name).write_text(tekst, "utf-8")
    return doel


@pytest.fixture(scope="module")
def o2_service(o2_regelmap: Path) -> ModularValidationService:
    return ModularValidationService(
        toetsregel_manager=ToetsregelManager(base_dir=str(o2_regelmap.parent))
    )


async def _valideer(service, geval, metadata) -> dict[str, Any]:
    resultaat = await service.validate_definition(
        begrip=geval["invoer"]["begrip"],
        text=geval["invoer"]["kern"],
        context=metadata,
    )
    assert resultaat["validation_status"] == "validated", resultaat.get("system")
    return resultaat


# --- de actieve regelset lezen --------------------------------------------------


def test_evaluator_voor_leest_actieve_o1_en_expliciete_o2_regelset(o2_service):
    actief = ModularValidationService(toetsregel_manager=ToetsregelManager())
    assert actief.evaluator_voor("INT-02") is EvaluatorType.JUDGMENT_REVIEW
    assert o2_service.evaluator_voor("INT-02") is (
        EvaluatorType.DECISION_RULE_ASSESSMENT
    )
    assert o2_service.evaluator_voor("INT-03") is (
        EvaluatorType.PRONOUN_REFERENCE_ASSESSMENT
    )
    assert o2_service.evaluator_voor("BESTAAT-NIET") is None


def test_evaluator_voor_zonder_geldige_regelset_is_none():
    # Zonder manager is er geen regelset; dan is er ook geen O2-route.
    assert ModularValidationService().evaluator_voor("INT-02") is None


def test_decision_rule_assessment_levert_een_deeluitkomst():
    assert EvaluatorType.DECISION_RULE_ASSESSMENT in mvs._EVALUATORS_MET_DEELUITKOMST


# --- elke status landt in rule_results, zonder cijfer ---------------------------

#: (id, geval, respons, status, reden, actualiteit, document aanvaard)
STATUSGEVALLEN = [
    ("pass-C112", ("C112", None), None, "pass", None, "current", True),
    ("fail-C105", ("C105", None), None, "fail", None, "current", True),
    (
        "review-C107",
        ("C107", None),
        None,
        "review_required",
        "insufficient_information",
        "current",
        True,
    ),
    ("na-C105", ("C105", None), _na_respons, "not_applicable", None, "current", True),
    ("error-C117", ("C117", "verzonnen-citaat"), None, "error", None, None, False),
]


@pytest.mark.parametrize(
    ("geval_id", "respons", "status", "reden", "actualiteit", "aanvaard"),
    [pytest.param(*rij[1:], id=rij[0]) for rij in STATUSGEVALLEN],
)
async def test_elke_o2_status_landt_in_rule_results(
    o2_service, geval_id, respons, status, reden, actualiteit, aanvaard
):
    geval = _geval(*geval_id)
    document = _document(geval, respons() if callable(respons) else None)
    assert document.status == status  # WP1 bepaalt; de keten verandert niets

    resultaat = await _valideer(o2_service, geval, _metadata(geval, document))

    assert resultaat["rule_statuses"]["INT-02"] == status
    detail = resultaat["rule_results"]["INT-02"]
    assert detail["status"] == status
    assert detail["score"] is None
    assert detail["contract_version"] == CONTRACTVERSIE
    assert detail["review"]["actuality"] == actualiteit
    assert detail["parts"][0]["reason"] == document.melding
    if aanvaard:
        # Het WP1-document onveranderd in rule_results.
        assert detail["assessment"] == document.als_dict()
    else:
        assert detail["assessment"] is None
    if status == "review_required":
        assert reden == document.reden
        (item,) = [r for r in resultaat["review_required"] if r["rule_id"] == "INT-02"]
        assert item["reason"] == document.melding


@pytest.mark.parametrize(
    ("kern", "context", "ontbreekt"),
    [
        pytest.param(None, [], "context", id="context-C56"),
        pytest.param("Toegang:", ["synthetische context"], "kern", id="label-kern"),
        pytest.param("", ["synthetische context"], "kern", id="lege-kern"),
    ],
)
async def test_ontbrekende_kern_of_context_is_ne_zonder_oordeel(
    o2_service, kern, context, ontbreekt
):
    # Sinds review F1 beslist onder O2 uitsluitend de O2-evaluator, ook bij
    # ontbrekende context (O2-vorm: zie de F1-tests hieronder). Beide: NE, exacte
    # WP1-melding, geen oordeel en geen cijfer.
    geval = _geval("C56")
    if kern is not None:
        geval["invoer"]["kern"] = kern
    geval["invoer"]["organisatorische_context"] = context
    document = _document(geval)
    assert document.status == "not_evaluated"

    resultaat = await _valideer(o2_service, geval, _metadata(geval, document))

    assert resultaat["rule_statuses"]["INT-02"] == "not_evaluated"
    detail = resultaat["rule_results"]["INT-02"]
    assert detail["status"] == "not_evaluated"
    assert detail["score"] is None
    assert detail["parts"][0]["reason"] == document.melding
    assert ontbreekt in document.melding
    assert detail.get("assessment") is None
    assert not [v for v in resultaat["violations"] if v["code"] == "INT-02"]
    assert not [r for r in resultaat["review_required"] if r["rule_id"] == "INT-02"]


async def test_zonder_document_blijft_int02_expliciet_open(o2_service):
    geval = _geval("C105")
    resultaat = await _valideer(o2_service, geval, _metadata(geval))
    detail = resultaat["rule_results"]["INT-02"]
    assert detail["status"] == "review_required"
    assert detail["review"]["actuality"] == "not_assessed"
    assert detail["parts"][0]["reason"] == MELDING_NIET_BEOORDEELD
    assert detail["assessment"] is None


async def test_adviserende_fail_is_een_zichtbare_violation_zonder_poort(o2_service):
    geval = _geval("C105")
    document = _document(geval)
    resultaat = await _valideer(o2_service, geval, _metadata(geval, document))
    (violation,) = [v for v in resultaat["violations"] if v["code"] == "INT-02"]
    assert violation["severity"] == "warning"
    assert violation["metadata"]["advisory"] is True
    assert violation["description"] == document.melding


async def test_int02_geeft_geen_cijfer_en_geen_poort(o2_service):
    """Zelfde kern en context, alleen het INT-02-oordeel verschilt: score,
    categoriescores en acceptatie blijven exact gelijk."""
    geval = _geval("C105")
    uitkomsten = {}
    for naam, respons in (
        ("pass", _pass_respons_c105()),
        ("fail", geval["modelrespons"]),
        ("review_required", _onvoldoende_respons_c105()),
        ("not_applicable", _na_respons()),
    ):
        document = _document(geval, respons)
        assert document.status == naam
        resultaat = await _valideer(o2_service, geval, _metadata(geval, document))
        assert resultaat["rule_statuses"]["INT-02"] == naam
        uitkomsten[naam] = (
            resultaat["overall_score"],
            resultaat["detailed_scores"],
            resultaat["is_acceptable"],
            resultaat["acceptance_gate"],
        )
    referentie = uitkomsten["pass"]
    for naam, uitkomst in uitkomsten.items():
        assert uitkomst == referentie, naam


# --- F1 (review WP5a): alleen de O2-evaluator controleert de invoer -------------
#
# De voorafgaande `missing_inputs`-check van de service gaf voor INT-02 de
# oude DEF-771-NE-uitkomst, op `cleaned_text` en vóór de O2-evaluator. Onder
# O2 hoort de volledige WP1-invoercontrole (exacte recordkern, NE-vorm,
# ongeldige metadata = error) uitsluitend bij `decision_rule_assessment`.

GEEN_CONTEXT = {
    "organisatorische_context": [],
    "juridische_context": [],
    "wettelijke_basis": [],
}
KERN_C105 = "De medewerker laat de aanvrager toe."


class _VasteCleaning:
    """Cleaning die altijd dezelfde tekst oplevert; mag INT-02 niet raken."""

    def __init__(self, tekst: str) -> None:
        self.tekst = tekst

    def clean_text(self, _tekst):
        return self.tekst


def _assert_o2_vorm(detail: dict[str, Any], status: str, melding: str) -> None:
    # Eerst status en exacte melding, daarna de O2-documentvorm.
    assert detail["status"] == status
    assert [deel["reason"] for deel in detail["parts"]] == [melding]
    assert detail["score"] is None
    assert detail["contract_version"] == CONTRACTVERSIE
    assert detail["review"] == {"actuality": None}
    assert detail["assessment"] is None
    (deel,) = detail["parts"]
    assert deel["id"] == "beoordeling"
    assert deel["status"] == status


@pytest.mark.parametrize(
    ("kern", "cleaning", "context", "ontbreekt"),
    [
        pytest.param(KERN_C105, "", GEEN_CONTEXT, "context", id="kern-cleaning-leeg"),
        pytest.param(
            "", KERN_C105, GEEN_CONTEXT, "kern en context", id="leeg-cleaning-kern"
        ),
        pytest.param(KERN_C105, None, GEEN_CONTEXT, "context", id="zonder-cleaning"),
        pytest.param(
            "",
            None,
            {**GEEN_CONTEXT, "organisatorische_context": ["synthetische procedure"]},
            "kern",
            id="lege-kern-met-context",
        ),
    ],
)
async def test_f1_ne_volgt_de_oorspronkelijke_kern_in_o2_vorm(
    o2_regelmap, kern, cleaning, context, ontbreekt
):
    service = ModularValidationService(
        toetsregel_manager=ToetsregelManager(base_dir=str(o2_regelmap.parent)),
        cleaning_service=_VasteCleaning(cleaning) if cleaning is not None else None,
    )
    resultaat = await service.validate_definition(
        begrip="toelating",
        text=kern,
        context={"record_text": kern, **copy.deepcopy(context)},
    )

    assert resultaat["validation_status"] == "validated"
    assert resultaat["rule_statuses"]["INT-02"] == "not_evaluated"
    _assert_o2_vorm(
        resultaat["rule_results"]["INT-02"],
        "not_evaluated",
        MELDING_NE.replace("{kern/context}", ontbreekt),
    )


@pytest.mark.parametrize(
    "over",
    [
        pytest.param({"record_text": None}, id="recordkern-none"),
        pytest.param({"int02_bedoeling": 42}, id="bedoeling-getal"),
    ],
)
async def test_f1_ongeldige_metadata_zonder_context_is_error(o2_service, over):
    metadata = {"record_text": KERN_C105, **copy.deepcopy(GEEN_CONTEXT), **over}

    resultaat = await o2_service.validate_definition(
        begrip="toelating", text=KERN_C105, context=metadata
    )

    assert resultaat["rule_statuses"]["INT-02"] == "error"
    _assert_o2_vorm(resultaat["rule_results"]["INT-02"], "error", MELDING_E)
    assert not [v for v in resultaat["violations"] if v["code"] == "INT-02"]
    assert not [r for r in resultaat["review_required"] if r["rule_id"] == "INT-02"]
