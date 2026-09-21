"""ESS-03 (DEF-766): de vier uitkomsten, de vraag en fouten zichtbaar in de UI.

Streamlit-aanroepen worden opgevangen (geen browser). Wat deze tests
bewijzen: 'niet van toepassing' is een eigen, zichtbare uitkomst (geen pass,
geen open punt) in dekking en regeluitkomsten; 'onvoldoende informatie'
toont precies de gerichte vraag; een technische fout staat apart; een
negatieve uitkomst is herkenbaar als AI-beoordeling; en de ESS-03-reden wordt
niet dubbel getoond nu de regel een gestructureerde uitkomst heeft.
"""

from __future__ import annotations

import pytest

from domain.ess03.contract import Intentie, beoordeel_telbaarheid
from tests.fixtures.def766_fakes import BINDING, bouw_ess03_beoordeling
from ui.components import validation_view
from ui.components.definition_generator_tab import _dekkingstegel
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

BEGRIP = "water"
TEKST = "Vloeistof bestaande uit H2O."
CONTEXT = {
    "organisatorische_context": ["Synthetisch Lab"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
INTENTIE = Intentie(toelichting="Bedoeld: de stof, niet een monster.")


def _rule_result(scenario: str) -> dict:
    beoordeling = bouw_ess03_beoordeling(
        BEGRIP, TEKST, CONTEXT, None, intentie=INTENTIE, scenario=scenario
    )
    return beoordeel_telbaarheid(
        BEGRIP,
        TEKST,
        CONTEXT,
        None,
        intentie=INTENTIE,
        assessment=beoordeling,
        binding=BINDING,
    ).als_dict()


@pytest.fixture
def shown(monkeypatch):
    opgevangen = {
        api: []
        for api in ("markdown", "info", "warning", "success", "error", "write", "text")
    }
    for api in opgevangen:
        monkeypatch.setattr(
            validation_view.st,
            api,
            lambda t, *a, _api=api, **kw: opgevangen[_api].append(str(t)),
            raising=False,
        )
    monkeypatch.setattr(validation_view.st, "button", lambda *a, **kw: False)

    class _Expander:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(
        validation_view.st, "expander", lambda *a, **kw: _Expander(), raising=False
    )
    return opgevangen


def _alles(shown: dict) -> str:
    return "\n".join(t for waarden in shown.values() for t in waarden)


class TestDekking:
    def test_niet_van_toepassing_telt_apart_uit_evaluation_coverage(self):
        dekking = validation_view.bereken_beoordelingsdekking(
            {
                "evaluation_coverage": {
                    "evaluated": 40,
                    "passed": 38,
                    "failed": 2,
                    "review_required": 9,
                    "not_evaluated": 2,
                    "error": 1,
                    "not_applicable": 1,
                    "total": 53,
                    "coverage_ratio": 0.75,
                }
            }
        )
        assert dekking["not_applicable"] == 1
        regel = validation_view.dekkingsregel(dekking)
        assert "1 niet van toepassing" in regel
        assert "53 regels" in regel

    def test_oud_resultaat_zonder_telling_blijft_leesbaar(self):
        dekking = validation_view.bereken_beoordelingsdekking(
            {
                "evaluation_coverage": {
                    "evaluated": 1,
                    "passed": 1,
                    "failed": 0,
                    "review_required": 0,
                    "not_evaluated": 0,
                    "error": 0,
                    "total": 1,
                    "coverage_ratio": 1.0,
                }
            }
        )
        assert dekking["not_applicable"] == 0
        assert "niet van toepassing" not in validation_view.dekkingsregel(dekking)

    def test_niet_van_toepassing_uit_rule_statuses(self):
        dekking = validation_view.bereken_beoordelingsdekking(
            {"rule_statuses": {"ESS-03": "not_applicable", "VER-01": "pass"}}
        )
        assert dekking == {
            "total": 2,
            "pass": 1,
            "fail": 0,
            "review_required": 0,
            "error": 0,
            "not_evaluated": 0,
            "not_applicable": 1,
        }

    def test_dekkingstegel_generatie_toont_niet_van_toepassing(self):
        tegel = _dekkingstegel(
            {
                "validation_details": {
                    "rule_statuses": {
                        "ESS-03": "not_applicable",
                        "VER-01": "pass",
                        "ESS-01": "review_required",
                    }
                }
            }
        )
        assert "1 voldoet" in tegel
        assert "1 open" in tegel
        assert "1 n.v.t." in tegel


class TestRegeluitkomsten:
    def test_niet_van_toepassing_is_info_geen_pass_geen_waarschuwing(self, shown):
        validation_view.render_rule_results({"ESS-03": _rule_result("not_applicable")})
        kop = shown["markdown"][0]
        assert "ESS-03" in kop and "Niet van toepassing" in kop
        assert "Voldoet" not in kop.replace("Voldoet niet", "")
        assert shown["success"] == []
        assert shown["error"] == []
        [deel] = shown["info"]
        assert "Niet van toepassing" in deel
        assert "AI-beoordeling" in deel
        assert "geen afzonderlijke identificatie" in deel.lower()
        assert any("fake-ess03-model" in r for r in shown["markdown"])

    def test_voldoet_niet_is_error_met_ai_herkomst_en_bewijs(self, shown):
        validation_view.render_rule_results({"ESS-03": _rule_result("fail")})
        [deel] = shown["error"]
        assert "Voldoet niet" in deel
        assert "AI-beoordeling" in deel
        assert "aanleiding: 'Vloeistof bestaande'" in deel
        assert "Vervolgstap" in deel

    def test_onvoldoende_informatie_toont_precies_de_vraag(self, shown):
        validation_view.render_rule_results({"ESS-03": _rule_result("insufficient")})
        # Correctieronde 1 (R9): eigen inhoudelijk label, geen generiek open punt.
        assert "Onvoldoende informatie" in shown["markdown"][0]
        [deel] = shown["warning"]
        assert "Onvoldoende informatie" in deel
        assert "Nog te beoordelen" not in deel
        assert (
            "Vraag: Binnen welk register en welke populatie geldt het nummer?" in deel
        )
        assert "Ontbrekende informatie" in deel
        assert shown["error"] == []

    def test_technische_fout_staat_apart_van_een_oordeel(self, shown):
        validation_view.render_rule_results({"ESS-03": _rule_result("error")})
        [deel] = shown["warning"]
        assert "Technisch probleem" in deel
        assert "geen inhoudelijk oordeel" in deel.lower()
        assert any("technisch mislukt" in r.lower() for r in shown["markdown"])

    def test_niet_beschikbaar_is_geen_eindantwoord(self, shown):
        validation_view.render_rule_results({"ESS-03": _rule_result("unavailable")})
        [deel] = shown["warning"]
        assert "niet beoordeeld" in deel.lower()
        assert "synthetisch: geen dienst" in deel
        assert any(
            "geen beoordelingsdienst beschikbaar" in r.lower()
            for r in shown["markdown"]
        )

    def test_voldoet_is_success(self, shown):
        validation_view.render_rule_results({"ESS-03": _rule_result("pass")})
        [deel] = shown["success"]
        assert "Voldoet" in deel and "AI-beoordeling" in deel


class TestVolledigeWeergave:
    def test_ess03_reden_wordt_niet_dubbel_getoond(self, shown):
        detail = _rule_result("insufficient")
        reden = detail["parts"][0]["reason"]
        result = {
            "version": "2.1.0",
            "validation_status": "validated",
            "overall_score": None,
            "is_acceptable": False,
            "violations": [],
            "passed_rules": [],
            "detailed_scores": {},
            "system": {},
            "rule_statuses": {"ESS-03": "review_required", "ESS-01": "review_required"},
            "rule_results": {"ESS-03": detail},
            "review_required": [
                {
                    "rule_id": "ESS-03",
                    "category": "juridisch",
                    "reason": reden,
                    "signals": [],
                },
                {
                    "rule_id": "ESS-01",
                    "category": "juridisch",
                    "reason": "ESS-01 — Nog te beoordelen: kenmerken.",
                    "signals": [],
                },
            ],
        }
        SessionStateManager.set_value("def766w_show_validation_details", True)
        validation_view.render_validation_detailed_list(result, key_prefix="def766w")
        # ESS-01 blijft via st.text zichtbaar; ESS-03 komt uit rule_results.
        assert any("ESS-01 — Nog te beoordelen" in t for t in shown["text"])
        assert not any(reden in t for t in shown["text"])
        assert sum(reden in t for t in shown["warning"]) == 1
        # De statuslijst noemt ESS-03 niet nogmaals (heeft gestructureerde uitkomst).
        statuslijnen = [
            t for t in shown["info"] if t.startswith("🟠 Nog te beoordelen:")
        ]
        assert statuslijnen and "ESS-03" not in statuslijnen[0]
        assert "ESS-01" in statuslijnen[0]

    def test_statuslijst_noemt_niet_van_toepassing_zonder_detail(self):
        lijnen = validation_view._statuslijst_regels(
            {"rule_statuses": {"XYZ-01": "not_applicable"}}, uitgesloten=set()
        )
        assert lijnen == ["➖ Niet van toepassing: XYZ-01"]
