"""INT-03 (DEF-772 WP4): de uitkomsten, verwijzingen, kandidaten, vraag en fouten
zichtbaar in de gedeelde toetsweergave.

Streamlit-aanroepen worden opgevangen (geen browser). Wat deze tests
bewijzen: de vier uitkomsten zijn herkenbaar als AI-beoordeling met het
verwijzende woord, de passage, de plausibele kandidaten en de motivering; de
K7-uitkomst toont 'Voldoet — niet van toepassing (geen voornaamwoord)';
'onvoldoende informatie' toont precies de gerichte vraag; een technische fout,
een niet-beoordeelde en een historische beoordeling staan apart van een
oordeel en verschijnen nooit als 'Voldoet'; de INT-03-reden wordt niet dubbel
getoond.
"""

from __future__ import annotations

from typing import Any

import pytest

from domain.int03.contract import (
    MOTIVERING_GEEN_VERWIJZEND_WOORD,
    Beoordelingsbinding,
    beoordeel_verwijzingen,
)
from tests.fixtures.def772_fakes import BINDING, bouw_int03_beoordeling
from ui.components import validation_view
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

BEGRIP = "archiefkaart"
TEKST = "Beschrijving van een verzameling documenten die bij een zaak horen."
TEKST_ZONDER = "Beschrijving van een verzameling documenten van een archiefvormer."
TOELICHTING = "Synthetische toelichting."
CONTEXT = {
    "organisatorische_context": ["Stichting Zilver"],
    "juridische_context": [],
    "wettelijke_basis": [],
}


def _rule_result(
    scenario: str,
    *,
    tekst: str = TEKST,
    assessment: Any = "auto",
    binding: Beoordelingsbinding | None = BINDING,
) -> dict:
    document = (
        bouw_int03_beoordeling(BEGRIP, tekst, CONTEXT, TOELICHTING, scenario=scenario)
        if assessment == "auto"
        else assessment
    )
    return beoordeel_verwijzingen(
        BEGRIP, tekst, CONTEXT, TOELICHTING, assessment=document, binding=binding
    ).als_dict()


@pytest.fixture
def shown(monkeypatch):
    opgevangen = {
        api: []
        for api in (
            "markdown",
            "info",
            "warning",
            "success",
            "error",
            "write",
            "text",
            "caption",
        )
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


def _kop(shown: dict) -> str:
    koppen = [t for t in shown["markdown"] if t.startswith("**INT-03**")]
    assert len(koppen) == 1, shown["markdown"]
    return koppen[0]


class TestRegeluitkomsten:
    def test_voldoet_toont_woord_passage_antecedent_en_ai_herkomst(self, shown):
        validation_view.render_rule_results({"INT-03": _rule_result("pass")})
        kop = _kop(shown)
        assert "Voldoet" in kop and "Voldoet niet" not in kop
        [deel] = shown["success"]
        assert "AI-beoordeling" in deel
        assert "'die'" in deel
        assert "verzameling documenten die bij een" in deel
        assert "→" in deel  # het aangewezen antecedent
        assert shown["error"] == [] and shown["warning"] == []
        assert any("fake-int03-model" in r for r in shown["markdown"])
        # Gestructureerde verwijzingsregels naast de motivering.
        assert any("Verwijzend woord" in r and "'die'" in r for r in shown["markdown"])

    def test_geen_verwijzend_woord_is_voldoet_niet_van_toepassing(self, shown):
        validation_view.render_rule_results(
            {"INT-03": _rule_result("no_word", tekst=TEKST_ZONDER)}
        )
        kop = _kop(shown)
        assert "Voldoet — niet van toepassing (geen voornaamwoord)" in kop
        assert "Nog te beoordelen" not in kop
        [deel] = shown["success"]
        assert "niet van toepassing (geen voornaamwoord)" in deel
        assert MOTIVERING_GEEN_VERWIJZEND_WOORD in deel
        assert "AI-beoordeling" in deel
        assert shown["warning"] == [] and shown["error"] == []

    def test_voldoet_niet_toont_woord_passage_en_plausibele_kandidaten(self, shown):
        validation_view.render_rule_results({"INT-03": _rule_result("fail")})
        assert "Voldoet niet" in _kop(shown)
        [deel] = shown["error"]
        assert "AI-beoordeling" in deel
        assert "aanleiding: 'verzameling documenten die bij een'" in deel
        assert "'die'" in deel
        assert "'Beschrijving'" in deel and "'verzameling'" in deel  # kandidaten
        assert "Vervolgstap" in deel
        assert "wijzigt de tekst niet" in deel
        assert "niet automatisch" in deel
        assert shown["success"] == []
        regels = "\n".join(shown["markdown"])
        assert "Kandidaten" in regels and "'Beschrijving'" in regels

    def test_geen_antecedent_is_voldoet_niet_zonder_kandidaten(self, shown):
        validation_view.render_rule_results({"INT-03": _rule_result("no_antecedent")})
        [deel] = shown["error"]
        assert "geen antecedent in de definitie" in deel
        assert "Voldoet niet" in _kop(shown)

    def test_onvoldoende_informatie_toont_precies_de_ene_vraag(self, shown):
        validation_view.render_rule_results({"INT-03": _rule_result("insufficient")})
        kop = _kop(shown)
        assert "Onvoldoende informatie" in kop and "Nog te beoordelen" not in kop
        [deel] = shown["warning"]
        # Het label van het onderdeel is de inhoudelijke uitkomst, niet het
        # generieke open punt; de motivering zelf (contracttekst WP3) noemt
        # het model en de per-woordstatus.
        assert deel.startswith("❓ Onvoldoende informatie")
        assert "Vraag: Naar welk antecedent verwijst het aangewezen woord?" in deel
        assert shown["error"] == [] and shown["success"] == []
        assert (
            _alles(shown).count("Naar welk antecedent verwijst het aangewezen woord?")
            == 2
        )
        # De vraag staat ook als eigen regel naast de motivering.
        assert any(r.startswith("❓") for r in shown["markdown"])

    def test_technische_fout_staat_apart_van_een_oordeel(self, shown):
        validation_view.render_rule_results({"INT-03": _rule_result("error")})
        assert "Technisch probleem" in _kop(shown)
        [deel] = shown["warning"]
        assert "Technisch probleem" in deel
        assert "geen inhoudelijk oordeel" in deel.lower()
        assert any("technisch mislukt" in r.lower() for r in shown["markdown"])
        assert shown["success"] == [] and shown["error"] == []

    def test_niet_beschikbaar_is_geen_eindantwoord(self, shown):
        validation_view.render_rule_results({"INT-03": _rule_result("unavailable")})
        [deel] = shown["warning"]
        assert "niet beoordeeld" in deel.lower()
        assert "synthetisch: geen dienst" in deel
        assert any(
            "geen beoordelingsdienst beschikbaar" in r.lower()
            for r in shown["markdown"]
        )
        assert shown["success"] == []

    def test_zonder_beoordeling_zichtbaar_niet_beoordeeld(self, shown):
        validation_view.render_rule_results(
            {"INT-03": _rule_result("pass", assessment=None)}
        )
        assert "Nog te beoordelen" in _kop(shown)
        [deel] = shown["warning"]
        assert "niet beoordeeld" in deel.lower()
        assert "niet uitgevoerd" in deel
        assert shown["success"] == []

    def test_historische_beoordeling_is_geen_actuele_pass(self, shown):
        ander = Beoordelingsbinding(**{**BINDING.als_dict(), "model": "ander-model"})
        validation_view.render_rule_results(
            {"INT-03": _rule_result("pass", binding=ander)}
        )
        assert "Nog te beoordelen" in _kop(shown)
        [deel] = shown["warning"]
        assert "historisch" in deel.lower()
        assert "eerder oordeel: pass" in deel
        assert shown["success"] == []
        assert any("verouderd/historisch" in r for r in shown["markdown"])
        # Geen oude verwijzingsregels alsof zij actueel zijn.
        assert not any("Verwijzend woord" in r for r in shown["markdown"])

    def test_afgewezen_modelclaims_worden_benoemd(self, shown):
        document = bouw_int03_beoordeling(
            BEGRIP, TEKST, CONTEXT, TOELICHTING, scenario="pass"
        )
        document["rejected"] = [{"reason": "unverifiable_quote", "detail": "x"}]
        validation_view.render_rule_results(
            {"INT-03": _rule_result("pass", assessment=document)}
        )
        assert any("1 modelclaim(s) afgewezen" in r for r in shown["markdown"])


class TestVolledigeWeergave:
    def test_int03_reden_wordt_niet_dubbel_getoond(self, shown):
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
            "rule_statuses": {"INT-03": "review_required", "ESS-01": "review_required"},
            "rule_results": {"INT-03": detail},
            "review_required": [
                {
                    "rule_id": "INT-03",
                    "category": "integriteit",
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
        SessionStateManager.set_value("def772w_show_validation_details", True)
        validation_view.render_validation_detailed_list(result, key_prefix="def772w")
        assert not any(reden in t for t in shown["text"])
        assert sum(reden in t for t in shown["warning"]) == 1
        statuslijnen = [
            t for t in shown["info"] if t.startswith("🟠 Nog te beoordelen:")
        ]
        assert statuslijnen and "INT-03" not in statuslijnen[0]
        assert "ESS-01" in statuslijnen[0]

    def test_niet_beoordeeld_zonder_detail_staat_in_de_statuslijst(self):
        lijnen = validation_view._statuslijst_regels(
            {"rule_statuses": {"INT-03": "not_evaluated"}}, uitgesloten=set()
        )
        assert lijnen == ["⏸️ Niet beoordeeld: INT-03"]

    def test_dekking_telt_de_int03_uitkomst_mee(self):
        dekking = validation_view.bereken_beoordelingsdekking(
            {"rule_statuses": {"INT-03": "fail", "VER-01": "pass"}}
        )
        assert dekking["fail"] == 1 and dekking["pass"] == 1
        assert "1 voldoet niet" in validation_view.dekkingsregel(dekking)
