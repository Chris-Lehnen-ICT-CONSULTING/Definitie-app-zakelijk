"""DEF-766 correctieronde 2, punt A — `herbind_ess03_in_validatieresultaat` (servicelaag).

De gedeelde functie achter het editor-resultatenblok: een V2-resultaat van een
eerdere toetsing wordt zonder AI-aanroep opnieuw aan de huidige kandidaat en
de actuele binding gelegd. Bewezen: bij gelijke binding hetzelfde object;
bij een afwijking (verduidelijking, tekst, model) een kopie waarin ESS-03 in
rule_results, rule_statuses, passed_rules, violations, review_required en de
dekking consistent open/historisch is, terwijl het origineel ongewijzigd
blijft en de beoordeling zelf erin bewaard wordt.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from domain.ess03.contract import Intentie
from services.definition_edit_service import herbind_ess03_in_validatieresultaat
from services.interfaces import Definition
from tests.fixtures.def766_fakes import BINDING, bouw_ess03_beoordeling

pytestmark = [pytest.mark.unit]

BEGRIP = "eiland"
TEKST = "Afzonderlijk aaneengesloten landoppervlak dat volledig door water is omgeven."
TOELICHTING = "Synthetische conventie."
CONTEXT = {
    "organisatorische_context": ["Synthetisch Waterschap"],
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
        "metadata": {"ess03_verduidelijking": "Peil P."},
    }
    velden.update(over)
    return Definition(**velden)


def _resultaat(scenario: str = "pass") -> dict:
    from domain.ess03.contract import beoordeel_telbaarheid

    beoordeling = bouw_ess03_beoordeling(
        BEGRIP,
        TEKST,
        CONTEXT,
        None,
        intentie=Intentie(
            toelichting=TOELICHTING, categorie="type", verduidelijking="Peil P."
        ),
        scenario=scenario,
    )
    detail = beoordeel_telbaarheid(
        BEGRIP,
        TEKST,
        CONTEXT,
        None,
        intentie=Intentie(
            toelichting=TOELICHTING, categorie="type", verduidelijking="Peil P."
        ),
        assessment=beoordeling,
        binding=BINDING,
    ).als_dict()
    status = detail["status"]
    return {
        "version": "2.1.0",
        "validation_status": "validated",
        "rule_statuses": {
            "ESS-03": status,
            "VER-01": "pass",
            "ESS-01": "review_required",
        },
        "rule_results": {"ESS-03": detail},
        "passed_rules": ["VER-01"] + (["ESS-03"] if status == "pass" else []),
        "violations": (
            [{"code": "ESS-03", "rule_id": "ESS-03", "severity": "warning"}]
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
        },
        "ess03_assessment": beoordeling,
    }


def test_gelijke_binding_geeft_hetzelfde_object_terug():
    resultaat = _resultaat("pass")
    assert (
        herbind_ess03_in_validatieresultaat(resultaat, _kandidaat(), binding=BINDING)
        is resultaat
    )


@pytest.mark.parametrize(
    ("kandidaat", "binding"),
    [
        (_kandidaat(metadata={"ess03_verduidelijking": ""}), BINDING),
        (_kandidaat(definitie=TEKST + " Aangepast."), BINDING),
        (_kandidaat(), BINDING.__class__(**{**BINDING.als_dict(), "model": "ander"})),
        (_kandidaat(), None),
    ],
    ids=["verduidelijking-gewist", "tekst-gewijzigd", "ander-model", "geen-binding"],
)
def test_afwijkende_binding_maakt_ess03_consistent_historisch(kandidaat, binding):
    resultaat = _resultaat("pass")
    origineel = deepcopy(resultaat)
    herbonden = herbind_ess03_in_validatieresultaat(
        resultaat, kandidaat, binding=binding
    )
    assert resultaat == origineel, "het origineel wordt niet gemuteerd"
    assert herbonden is not resultaat
    assert herbonden["rule_statuses"]["ESS-03"] == "review_required"
    assert herbonden["rule_statuses"]["VER-01"] == "pass"
    assert "ESS-03" not in herbonden["passed_rules"]
    assert not any(v.get("code") == "ESS-03" for v in herbonden["violations"])
    [open_ess03] = [r for r in herbonden["review_required"] if r["rule_id"] == "ESS-03"]
    assert open_ess03["reason"] and "ESS-01" in {
        r["rule_id"] for r in herbonden["review_required"]
    }
    detail = herbonden["rule_results"]["ESS-03"]
    assert detail["status"] == "review_required"
    assert detail["review"]["assessment"]["applied"] is False
    assert detail["review"]["assessment"]["verdict"] == "pass"  # zichtbaar als historie
    dekking = herbonden["evaluation_coverage"]
    assert (dekking["passed"], dekking["review_required"], dekking["total"]) == (
        1,
        2,
        3,
    )
    assert herbonden["ess03_rebound"]["from_status"] == "pass"
    assert herbonden["ess03_rebound"]["to_status"] == "review_required"
    assert herbonden["ess03_rebound"]["historical"] is (binding is not None)
    # De beoordeling blijft in het resultaat: teruggezette invoer maakt haar weer actueel.
    assert herbonden["ess03_assessment"] == resultaat["ess03_assessment"]
    terug = herbind_ess03_in_validatieresultaat(
        herbonden, _kandidaat(), binding=BINDING
    )
    assert terug["rule_statuses"]["ESS-03"] == "pass"
    assert "ESS-03" in terug["passed_rules"]
    assert not any(r["rule_id"] == "ESS-03" for r in terug["review_required"])
    assert (
        terug["evaluation_coverage"]["passed"],
        terug["evaluation_coverage"]["review_required"],
    ) == (2, 1)


def test_fail_wordt_bij_afwijking_geen_violation_meer():
    resultaat = _resultaat("fail")
    herbonden = herbind_ess03_in_validatieresultaat(
        resultaat, _kandidaat(metadata={"ess03_verduidelijking": ""}), binding=BINDING
    )
    assert herbonden["violations"] == []
    assert herbonden["rule_statuses"]["ESS-03"] == "review_required"
    assert herbonden["evaluation_coverage"]["failed"] == 0
    assert herbonden["evaluation_coverage"]["review_required"] == 2
    # Terug naar de passende kandidaat: de afkeur is weer een niet-blokkerende violation.
    terug = herbind_ess03_in_validatieresultaat(
        herbonden, _kandidaat(), binding=BINDING
    )
    [violation] = [v for v in terug["violations"] if v["code"] == "ESS-03"]
    assert violation["severity"] == "warning" and violation["advisory"] is True
    assert terug["evaluation_coverage"]["failed"] == 1


def test_zonder_beoordeling_of_statussen_blijft_het_resultaat_ongemoeid():
    kaal = {"rule_statuses": {"VER-01": "pass"}}
    assert (
        herbind_ess03_in_validatieresultaat(kaal, _kandidaat(), binding=BINDING) is kaal
    )
