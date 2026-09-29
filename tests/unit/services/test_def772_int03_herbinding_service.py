"""DEF-772 WP4 — `herbind_int03_in_validatieresultaat` (servicelaag).

De gedeelde functie achter het editor-resultatenblok: een V2-resultaat van een
eerdere toetsing wordt zonder AI-aanroep opnieuw aan de huidige kandidaat en
de actuele binding gelegd. Bewezen: bij gelijke binding hetzelfde object;
bij een afwijking (tekst, toelichting, term, context, prompt/norm/model,
onbekende binding) een kopie waarin INT-03 in rule_results, rule_statuses,
passed_rules, violations, review_required en de dekking (inclusief de
afgeleide velden) consistent open/historisch is, terwijl het origineel
ongewijzigd blijft en het beoordelingsdocument erin bewaard wordt.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from domain.int03.contract import Beoordelingsbinding, beoordeel_verwijzingen
from services.definition_edit_service import herbind_int03_in_validatieresultaat
from services.interfaces import Definition
from tests.fixtures.def772_fakes import BINDING, bouw_int03_beoordeling

pytestmark = [pytest.mark.unit]

BEGRIP = "archiefkaart"
TEKST = "Beschrijving van een verzameling documenten die bij een zaak horen."
TOELICHTING = "Synthetische toelichting."
CONTEXT = {
    "organisatorische_context": ["Stichting Zilver"],
    "juridische_context": [],
    "wettelijke_basis": [],
}


def _kandidaat(**over) -> Definition:
    velden = {
        "begrip": BEGRIP,
        "definitie": TEKST,
        "toelichting": TOELICHTING,
        "categorie": "type",
        **CONTEXT,
        "metadata": {},
    }
    velden.update(over)
    return Definition(**velden)


def _resultaat(scenario: str = "pass") -> dict:
    document = bouw_int03_beoordeling(
        BEGRIP, TEKST, CONTEXT, TOELICHTING, scenario=scenario
    )
    detail = beoordeel_verwijzingen(
        BEGRIP, TEKST, CONTEXT, TOELICHTING, assessment=document, binding=BINDING
    ).als_dict()
    detail["signals"] = ["\\bdie\\b"]
    status = detail["status"]
    return {
        "version": "2.1.0",
        "validation_status": "validated",
        "rule_statuses": {
            "INT-03": status,
            "VER-01": "pass",
            "ESS-01": "review_required",
        },
        "rule_results": {"INT-03": detail},
        "passed_rules": ["VER-01"] + (["INT-03"] if status == "pass" else []),
        "violations": (
            [
                {
                    "code": "INT-03",
                    "rule_id": "INT-03",
                    "severity": "warning",
                    "advisory": True,
                }
            ]
            if status == "fail"
            else []
        ),
        "review_required": [{"rule_id": "ESS-01", "category": "x", "reason": "open"}],
        "evaluation_coverage": {
            "total": 3,
            "passed": 1 + (status == "pass"),
            "failed": int(status == "fail"),
            "review_required": 1,
            "error": 0,
            "not_evaluated": 0,
            "not_applicable": 0,
            "evaluated": 1 + (status == "pass") + int(status == "fail"),
            "coverage_ratio": round(
                (1 + (status == "pass") + int(status == "fail")) / 3, 4
            ),
        },
    }


def test_gelijke_binding_geeft_hetzelfde_object_terug():
    resultaat = _resultaat("pass")
    assert (
        herbind_int03_in_validatieresultaat(resultaat, _kandidaat(), binding=BINDING)
        is resultaat
    )


@pytest.mark.parametrize(
    ("kandidaat", "binding"),
    [
        (_kandidaat(definitie=TEKST + " Aangepast."), BINDING),
        (_kandidaat(toelichting="Andere toelichting."), BINDING),
        (_kandidaat(begrip="archiefstuk"), BINDING),
        (_kandidaat(organisatorische_context=["Stichting Goud"]), BINDING),
        (
            _kandidaat(),
            Beoordelingsbinding(**{**BINDING.als_dict(), "model": "ander-model"}),
        ),
        (_kandidaat(), None),
    ],
    ids=[
        "tekst-gewijzigd",
        "toelichting-gewijzigd",
        "term-gewijzigd",
        "context-gewijzigd",
        "ander-model",
        "geen-binding",
    ],
)
def test_afwijkende_binding_maakt_int03_consistent_historisch(kandidaat, binding):
    resultaat = _resultaat("pass")
    origineel = deepcopy(resultaat)
    herbonden = herbind_int03_in_validatieresultaat(
        resultaat, kandidaat, binding=binding
    )
    assert resultaat == origineel, "het origineel wordt niet gemuteerd"
    assert herbonden is not resultaat
    assert herbonden["rule_statuses"]["INT-03"] == "review_required"
    assert herbonden["rule_statuses"]["VER-01"] == "pass"
    assert "INT-03" not in herbonden["passed_rules"]
    assert not any(v.get("code") == "INT-03" for v in herbonden["violations"])
    [open_int03] = [r for r in herbonden["review_required"] if r["rule_id"] == "INT-03"]
    assert open_int03["reason"] and "ESS-01" in {
        r["rule_id"] for r in herbonden["review_required"]
    }
    detail = herbonden["rule_results"]["INT-03"]
    assert detail["status"] == "review_required"
    assert detail["review"]["assessment"]["applied"] is False
    assert detail["review"]["assessment"]["verdict"] == "pass"  # zichtbaar als historie
    assert detail["assessment"] == resultaat["rule_results"]["INT-03"]["assessment"]
    dekking = herbonden["evaluation_coverage"]
    assert (dekking["passed"], dekking["review_required"], dekking["total"]) == (
        1,
        2,
        3,
    )
    assert dekking["evaluated"] == dekking["passed"] + dekking["failed"] == 1
    assert dekking["coverage_ratio"] == round(1 / 3, 4)
    assert herbonden["int03_rebound"]["from_status"] == "pass"
    assert herbonden["int03_rebound"]["to_status"] == "review_required"
    assert herbonden["int03_rebound"]["historical"] is (binding is not None)
    # Teruggezette invoer maakt de beoordeling weer actueel (geen blinde
    # invalidatie): het document reist in het resultaat mee.
    terug = herbind_int03_in_validatieresultaat(
        herbonden, _kandidaat(), binding=BINDING
    )
    assert terug["rule_statuses"]["INT-03"] == "pass"
    assert "INT-03" in terug["passed_rules"]
    assert not any(r["rule_id"] == "INT-03" for r in terug["review_required"])
    assert (
        terug["evaluation_coverage"]["passed"],
        terug["evaluation_coverage"]["review_required"],
        terug["evaluation_coverage"]["evaluated"],
    ) == (2, 1, 2)


def test_fail_wordt_bij_afwijking_geen_violation_meer():
    resultaat = _resultaat("fail")
    herbonden = herbind_int03_in_validatieresultaat(
        resultaat, _kandidaat(toelichting="Anders."), binding=BINDING
    )
    assert herbonden["violations"] == []
    assert herbonden["rule_statuses"]["INT-03"] == "review_required"
    assert herbonden["evaluation_coverage"]["failed"] == 0
    assert herbonden["evaluation_coverage"]["review_required"] == 2
    assert herbonden["evaluation_coverage"]["evaluated"] == 1
    # Terug naar de passende kandidaat: de afkeur is weer een niet-blokkerende
    # violation met de AI-onderbouwing.
    terug = herbind_int03_in_validatieresultaat(
        herbonden, _kandidaat(), binding=BINDING
    )
    [violation] = [v for v in terug["violations"] if v["code"] == "INT-03"]
    assert violation["severity"] == "warning" and violation["advisory"] is True
    assert "die" in violation["message"]
    assert terug["evaluation_coverage"]["failed"] == 1


def test_zonder_int03_uitkomst_blijft_het_resultaat_ongemoeid():
    kaal = {"rule_statuses": {"VER-01": "pass"}, "rule_results": {}}
    assert (
        herbind_int03_in_validatieresultaat(kaal, _kandidaat(), binding=BINDING) is kaal
    )
    zonder_document = _resultaat("pass")
    zonder_document["rule_results"]["INT-03"]["assessment"] = None
    assert (
        herbind_int03_in_validatieresultaat(
            zonder_document, _kandidaat(definitie="Anders."), binding=BINDING
        )
        is zonder_document
    )
