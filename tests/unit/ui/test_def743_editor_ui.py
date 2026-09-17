"""DEF-743 pakket F — UI-gedrag met gemockte `st` (patroon test_def622_koppelingen_ui).

* Geen totaalcijfer/deelscore: ook een oud numeriek resultaat (overall_score
  0.82, 'x/y geslaagd') toont geen cijfer of percentage; wél regeloordelen en
  de beoordelingsdekking, met open/technische/niet-beoordeelde regels apart.
* CON-02-labels: geaccepteerde uitzondering is herkenbaar als uitzondering
  (nooit 'Voldoet'), een verouderde AI-beoordeling en een technische fout
  worden expliciet benoemd; herkomst AI vs. deskundige per onderdeel.
* Experttab: zonder reviewer-identiteit is vastleggen geblokkeerd (geen
  verzonnen actor); met identiteit schrijft de knop de platte, getypeerde
  `source_review` via D, herlaadt, en toont de uitzondering als uitzondering.
  Een verwijzingsuitzondering neemt id/hash/versie/vindplaats uit de bewaarde
  bron; na een tekstwijziging is de uitzondering verouderd. Een versieconflict
  is een waarschuwing, geen stil succes.
* Vaststelgate: CON-02 fail/error/verouderd/onbewezen/ontbrekend bewijs
  blokkeert niet-overrulebaar; een geaccepteerde uitzondering telt als
  uitzondering (en blokkeert niet), een deskundige correctie telt op status;
  de bestaande scoregate (validation_score None) blijft ongewijzigd blokkeren.
* Editor: de voorstelknop doet zonder klik niets (0 aanroepen) en met klik
  precies één modelaanroep via de servicelaag.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from database.definitie_repository import DefinitieRepository, DefinitieStatus
from domain.sources.contract import bereken_bronvingerafdruk
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import DefinitionEditService
from services.definition_repository import DefinitionRepository
from services.definition_workflow_service import DefinitionWorkflowService
from services.interfaces import Definition
from services.source_proposal_service import SourceProposalService
from tests.fixtures.def743_fakes import (
    BEGRIP,
    BRONNEN,
    JUR,
    ORG,
    TEKST,
    WET,
    FakeAI,
    bouw_beoordeling,
)
from ui.components.expert_review_tab import ExpertReviewTab
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

ACTOR = "Reviewer Rood"
CONTEXTEN = {
    "organisatorische_context": ORG,
    "juridische_context": JUR,
    "wettelijke_basis": WET,
}


# ------------------------------------------------------------------ helpers


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    return st.session_state


@pytest.fixture
def repo(tmp_path) -> DefinitionEditRepository:
    return DefinitionEditRepository(str(tmp_path / "ui.db"))


def _teksten(m: MagicMock) -> str:
    uit: list[str] = []
    for api in (
        "markdown",
        "success",
        "warning",
        "error",
        "info",
        "caption",
        "write",
        "text",
    ):
        uit.extend(str(c.args[0]) for c in getattr(m, api).call_args_list if c.args)
    return "\n".join(uit)


def _mock_st(**antwoorden: Any) -> MagicMock:
    """`st` met per widget-key instelbare antwoorden (default: eerste optie/leeg)."""
    m = MagicMock()

    def _per_key(default: Any):
        def _f(*args: Any, **kw: Any) -> Any:
            sleutel = kw.get("key")
            # Een uitgeschakelde knop kan in Streamlit niet 'True' geven.
            if kw.get("disabled") and default is False:
                return False
            if sleutel in antwoorden:
                return antwoorden[sleutel]
            if default == "eerste_optie":
                opties = kw.get("options") or (args[1] if len(args) > 1 else None)
                return opties[0] if opties else None
            if default == "" and "value" in kw:
                return kw["value"]  # zoals een (uitgeschakeld) veld met value=
            return default

        return _f

    m.selectbox.side_effect = _per_key("eerste_optie")
    m.text_input.side_effect = _per_key("")
    m.text_area.side_effect = _per_key("")
    m.checkbox.side_effect = _per_key(False)
    m.button.side_effect = _per_key(False)
    m.columns.side_effect = lambda spec, **kw: [
        MagicMock() for _ in (spec if isinstance(spec, list | tuple) else range(spec))
    ]
    return m


def _definition(*, scenario: str = "fail", bronnen: list | None = None, **meta: Any):
    bronnen = deepcopy(BRONNEN) if bronnen is None else bronnen
    metadata: dict[str, Any] = {
        "status": DefinitieStatus.REVIEW.value,
        "created_by": "generator",
        "sources": deepcopy(bronnen),
        "provenance_sources": deepcopy(bronnen),
        "source_assessment": (
            bouw_beoordeling(
                BEGRIP,
                TEKST,
                CONTEXTEN,
                bronnen,
                scenario=scenario,
                peildatum="2026-09-15",
            )
            if bronnen
            else None
        ),
        "peildatum": "2026-09-15",
    }
    metadata.update(meta)
    return Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        categorie="type",
        organisatorische_context=list(ORG),
        juridische_context=list(JUR),
        wettelijke_basis=list(WET),
        metadata=metadata,
    )


def _facade(repo) -> DefinitieRepository:
    return DefinitieRepository(repo.db_path)


def _vingerafdruk(bronnen: list | None = None, tekst: str = TEKST) -> str:
    return bereken_bronvingerafdruk(
        BEGRIP,
        tekst,
        CONTEXTEN,
        BRONNEN if bronnen is None else bronnen,
        peildatum="2026-09-15",
    )


# ------------------------------------------------- geen totaalcijfer (view)


LEGACY_NUMERIEK = {
    "validation_status": "validated",
    "overall_score": 0.82,
    "is_acceptable": True,
    "violations": [{"rule_id": "ESS-01", "description": "te kort", "severity": "high"}],
    "passed_rules": ["VAL-EMP-001", "CON-CIRC-001"],
    "rule_statuses": {
        "ESS-01": "fail",
        "VAL-EMP-001": "pass",
        "CON-CIRC-001": "pass",
        "CON-02": "review_required",
        "VER-01": "error",
        "SAM-05": "not_evaluated",
    },
    "evaluation_coverage": {
        "evaluated": 3,
        "passed": 2,
        "failed": 1,
        "review_required": 1,
        "not_evaluated": 1,
        "error": 1,
        "total": 6,
        "coverage_ratio": 0.5,
    },
    "rule_results": {},
    "acceptance_gate": {"status": "pass", "reasons": []},
}


def test_legacy_numeriek_resultaat_toont_geen_cijfer_maar_wel_dekking(sessie):
    from ui.components import validation_view

    m = MagicMock()
    with patch("ui.components.validation_view.st", m):
        validation_view.render_validation_detailed_list(
            deepcopy(LEGACY_NUMERIEK), key_prefix="t", show_toggle=False
        )
    tekst = _teksten(m)
    assert "Overall Score" not in tekst
    assert "0.82" not in tekst
    assert "%" not in tekst
    assert "regels geslaagd" not in tekst
    assert "Totaalscore:** niet beschikbaar" in tekst
    assert "Beoordelingsdekking" in tekst
    assert "6 regels" in tekst and "2 voldoet" in tekst and "1 voldoet niet" in tekst
    assert "1 nog te beoordelen" in tekst and "1 technisch probleem" in tekst
    assert "1 niet beoordeeld" in tekst
    # Open/technische/niet-beoordeelde regels blijven zichtbaar als eigen lijnen.
    assert "Nog te beoordelen: CON-02" in tekst
    assert "Technisch probleem: VER-01" in tekst
    assert "Niet beoordeeld: SAM-05" in tekst
    # De bestaande gate-indicator blijft (geen cijfer).
    assert "Gate: toegestaan" in tekst


def test_validation_unknown_guard_blijft_intact(sessie):
    from services.validation.interfaces import (
        UNKNOWN_REASON_RULESET_INCOMPLETE,
        VALIDATION_STATUS_UNKNOWN,
    )
    from ui.components import validation_view

    m = MagicMock()
    with patch("ui.components.validation_view.st", m):
        validation_view.render_validation_detailed_list(
            {
                "validation_status": VALIDATION_STATUS_UNKNOWN,
                "unknown_reason": UNKNOWN_REASON_RULESET_INCOMPLETE,
                "overall_score": 0.0,
                "validation_readiness": {"loaded_total": 7, "expected_total": 53},
            },
            key_prefix="u",
            show_toggle=False,
            gate={"status": "pass", "reasons": []},
        )
    tekst = _teksten(m)
    assert "niet te bepalen" in tekst.lower()
    assert "Beoordelingsdekking" not in tekst
    assert "Gate" not in tekst


def test_bereken_beoordelingsdekking_valt_terug_zonder_nul_of_pass_te_verzinnen():
    from ui.components.validation_view import (
        bereken_beoordelingsdekking,
        dekkingsregel,
    )

    assert bereken_beoordelingsdekking({}) is None
    assert "onbekend" in dekkingsregel(None)
    d = bereken_beoordelingsdekking({"rule_statuses": {"A": "pass", "B": "error"}})
    assert d == {
        "total": 2,
        "pass": 1,
        "fail": 0,
        "review_required": 0,
        "error": 1,
        "not_evaluated": 0,
    }
    legacy = bereken_beoordelingsdekking(
        {"violations": [{"rule_id": "X"}], "passed_rules": ["Y"]}
    )
    assert legacy["total"] == 2 and legacy["fail"] == 1 and legacy["pass"] == 1
    assert "%" not in dekkingsregel(legacy)


def test_con02_labels_uitzondering_stale_en_fout(sessie):
    from domain.sources.contract import beoordeel_bronbasis
    from ui.components import validation_view

    # Geaccepteerde uitzondering (geen bron): herkenbaar als uitzondering.
    review = {
        "type": "no_appropriate_source",
        "accepted": True,
        "actor": ACTOR,
        "rationale": "Organisatie-eigen term.",
        "version_number": 3,
        "fingerprint": _vingerafdruk([]),
        "search": {"queries": ["q"], "consulted": ["c"], "conclusion": "niets"},
    }
    uitkomst = beoordeel_bronbasis(
        BEGRIP,
        TEKST,
        CONTEXTEN,
        [],
        review=review,
        definitie_versie=3,
        peildatum="2026-09-15",
    )
    m = MagicMock()
    with patch("ui.components.validation_view.st", m):
        validation_view.render_rule_results({"CON-02": uitkomst.als_dict()})
    tekst = _teksten(m)
    assert "Nog te beoordelen" in tekst and "✅ Voldoet" not in tekst.split("\n")[0]
    assert "Geaccepteerde deskundige uitzondering wegens onderbouwd ontbreken" in tekst
    assert ACTOR in tekst and "geen positieve bronbeoordeling" in tekst
    assert "deskundige uitzondering · uitzondering" in tekst  # herkomst + markering

    # Verouderde AI-beoordeling: benoemd, niet stil.
    oud = bouw_beoordeling(BEGRIP, TEKST, CONTEXTEN, BRONNEN, scenario="pass")
    stale = beoordeel_bronbasis(
        BEGRIP, TEKST + " x", CONTEXTEN, BRONNEN, assessment=oud, peildatum="2026-09-15"
    )
    m = MagicMock()
    with patch("ui.components.validation_view.st", m):
        validation_view.render_rule_results({"CON-02": stale.als_dict()})
    tekst = _teksten(m)
    assert "verouderd/historisch en niet toegepast" in tekst
    assert "✅ Voldoet" not in tekst

    # Technische fout: eigen label, geen 'Voldoet niet'.
    fout = beoordeel_bronbasis(
        BEGRIP,
        TEKST,
        CONTEXTEN,
        BRONNEN,
        assessment=bouw_beoordeling(
            BEGRIP, TEKST, CONTEXTEN, BRONNEN, scenario="error", peildatum="2026-09-15"
        ),
        peildatum="2026-09-15",
    )
    m = MagicMock()
    with patch("ui.components.validation_view.st", m):
        validation_view.render_rule_results({"CON-02": fout.als_dict()})
    tekst = _teksten(m)
    assert "Technisch probleem" in tekst
    assert "technisch mislukt" in tekst
    assert "Voldoet niet" not in tekst

    # Toegepaste AI-beoordeling: herkenbaar als AI met attributie.
    toegepast = beoordeel_bronbasis(
        BEGRIP,
        TEKST,
        CONTEXTEN,
        BRONNEN,
        assessment=bouw_beoordeling(
            BEGRIP, TEKST, CONTEXTEN, BRONNEN, scenario="fail", peildatum="2026-09-15"
        ),
        peildatum="2026-09-15",
    )
    m = MagicMock()
    with patch("ui.components.validation_view.st", m):
        validation_view.render_rule_results({"CON-02": toegepast.als_dict()})
    tekst = _teksten(m)
    assert "AI-bronbeoordeling toegepast (fake · fake-beoordelaar)" in tekst
    assert "AI-beoordeling · aanleiding" in tekst  # herkomst per onderdeel + citaat


# ------------------------------------------------------- experttab (CON-02)


def _record_in_review(repo, **kw):
    did = repo.save(_definition(**kw))
    rec = _facade(repo).get_definitie(did)
    assert rec is not None
    return rec


def test_zonder_reviewer_identiteit_is_uitzondering_vastleggen_geblokkeerd(
    repo, sessie
):
    rec = _record_in_review(repo, scenario="fail")
    SessionStateManager.set_value("selected_review_definition", rec)
    m = _mock_st(**{f"con02_{rec.id}_soort": "no_appropriate_source"})
    with (
        patch("ui.components.expert_review_tab.st", m),
        patch("ui.components.validation_view.st", m),
        patch("ui.components.sources_renderer.st", m),
    ):
        ExpertReviewTab(_facade(repo))._render_bronbasiscontract(rec)
    vastleg = [
        c
        for c in m.button.call_args_list
        if c.kwargs.get("key") == f"con02_{rec.id}_vastleggen"
    ]
    assert len(vastleg) == 1
    assert vastleg[0].kwargs.get("disabled") is True
    assert _facade(repo).get_definitie(rec.id).get_source_review() is None
    tekst = _teksten(m)
    assert "Bronbasis" in tekst
    assert "voldoet niet" in tekst.lower()  # de fail blijft zichtbaar, geen valse pass


def test_geen_passende_bron_wordt_plat_getypeerd_vastgelegd_en_als_uitzondering_getoond(
    repo, sessie
):
    rec = _record_in_review(repo, scenario="fail", bronnen=[])
    SessionStateManager.set_value("selected_review_definition", rec)
    SessionStateManager.set_value("reviewer_name_input", f"  {ACTOR}  ")
    s = f"con02_{rec.id}"
    m = _mock_st(
        **{
            f"{s}_soort": "no_appropriate_source",
            f"{s}_queries": "bestuursorgaan definitie\nAwb 1:1",
            f"{s}_consulted": "wetten.overheid.nl\nintern register",
            f"{s}_conclusie": "Geen passende bron gevonden.",
            f"{s}_motivering": "Organisatie-eigen term zonder authentieke bron.",
            f"{s}_accepted": True,
            f"{s}_vastleggen": True,
        }
    )
    with (
        patch("ui.components.expert_review_tab.st", m),
        patch("ui.components.validation_view.st", m),
        patch("ui.components.sources_renderer.st", m),
    ):
        ExpertReviewTab(_facade(repo))._render_bronbasiscontract(rec)

    na = _facade(repo).get_definitie(rec.id)
    review = na.get_source_review()
    assert review is not None, _teksten(m)
    # Bevroren platte vorm (FREEZE punt 1): geen exceptions-dict, geen pass-sleutels.
    assert review["type"] == "no_appropriate_source"
    assert review["accepted"] is True
    assert review["actor"] == ACTOR and na.updated_by == ACTOR
    assert review["rationale"] == "Organisatie-eigen term zonder authentieke bron."
    assert review["version_number"] == rec.version_number + 1
    assert review["fingerprint"] == _vingerafdruk([])
    assert review["search"] == {
        "queries": ["bestuursorgaan definitie", "Awb 1:1"],
        "consulted": ["wetten.overheid.nl", "intern register"],
        "conclusion": "Geen passende bron gevonden.",
    }
    assert "exceptions" not in review
    assert not {"status", "overall", "score", "pass"} & set(review)
    assert "Uitzondering vastgelegd" in _teksten(m)
    m.rerun.assert_called_once()
    # Herladen: de selectie is het opgeslagen record (nieuwe versie).
    getoond: Any = SessionStateManager.get_value("selected_review_definition")
    assert getoond.version_number == rec.version_number + 1

    # Weergave: uitzondering herkenbaar, geen pass; gate herkent haar als uitzondering.
    m2 = _mock_st()
    with (
        patch("ui.components.expert_review_tab.st", m2),
        patch("ui.components.validation_view.st", m2),
        patch("ui.components.sources_renderer.st", m2),
    ):
        ExpertReviewTab(_facade(repo))._render_bronbasiscontract(getoond)
    tekst = _teksten(m2)
    assert "Geaccepteerde deskundige uitzondering wegens onderbouwd ontbreken" in tekst
    assert "Uitzondering: geen passende bron na onderbouwd zoeken" in tekst
    assert "Nog te beoordelen" in tekst
    assert not [c for c in m2.success.call_args_list if "Voldoet" in str(c.args[0])]
    assert DefinitionWorkflowService._con02_blokkades(getoond) == []


def test_verwijzingsuitzondering_neemt_bewaarde_bronversie_en_wordt_stale_na_tekstwijziging(
    repo, sessie
):
    from domain.sources.normalisatie import canoniseer_bronnen

    # DEF-806: de verwijzingsuitzondering geldt alleen voor een bron zónder
    # hyperlink; de gedeelde fixture draagt er een, dus hier zonder.
    bronnen = [{**BRONNEN[0], "url": None}, deepcopy(BRONNEN[1])]
    rec = _record_in_review(repo, scenario="pass", bronnen=bronnen)
    SessionStateManager.set_value("selected_review_definition", rec)
    SessionStateManager.set_value("user", ACTOR)
    s = f"con02_{rec.id}"
    awb = next(b for b in canoniseer_bronnen(bronnen) if b.source_id.startswith("rag:"))
    m = _mock_st(
        **{
            f"{s}_soort": "reference_exception",
            f"{s}_bron": awb.source_id,
            f"{s}_motivering_ref": "Intern raadpleegbaar via het documentbeheersysteem.",
            f"{s}_accepted": True,
            f"{s}_vastleggen": True,
        }
    )
    with (
        patch("ui.components.expert_review_tab.st", m),
        patch("ui.components.validation_view.st", m),
        patch("ui.components.sources_renderer.st", m),
    ):
        ExpertReviewTab(_facade(repo))._render_bronbasiscontract(rec)
    na = _facade(repo).get_definitie(rec.id)
    review = na.get_source_review()
    assert review is not None, _teksten(m)
    assert review["type"] == "reference_exception"
    assert review["source_id"] == awb.source_id
    assert (
        review["content_hash"] == awb.content_hash
    )  # bewaarde passage, niet vrije invoer
    assert review["source_version"] == awb.version
    assert review["locator"] == awb.locator
    assert review["accepted"] is True and review["actor"] == ACTOR
    # De vindplaats komt uit de bron: er is géén invoerveld voor (alleen een
    # caption) — een aanroeper-vindplaats vervangt nooit bronbewijs.
    assert not [
        c for c in m.text_input.call_args_list if "locator" in str(c.kwargs.get("key"))
    ]
    assert any(
        "Exacte vindplaats (uit de bewaarde bron)" in str(c.args[0])
        for c in m.caption.call_args_list
    )

    # Uitzondering blijft uitzondering: reference_quality open via deskundige.
    from domain.sources.contract import beoordeel_bronbasis

    velden = na.get_contractvelden()
    uitkomst = beoordeel_bronbasis(
        na.begrip,
        na.get_definitie_tekst(),
        na.get_contextlijsten(),
        velden["provenance_sources"],
        assessment=velden["source_assessment"],
        review=velden["source_review"],
        definitie_versie=velden["definition_version"],
        peildatum=velden["peildatum"],
    )
    assert uitkomst.status == "review_required"
    assert uitkomst.review["accepted_exception"] == "reference"
    verwijzing = next(p for p in uitkomst.parts if p.id == "reference_quality")
    assert (
        verwijzing.field == "source_review" and verwijzing.status == "review_required"
    )
    assert DefinitionWorkflowService._con02_blokkades(na) == []

    # Tekstwijziging: de uitzondering is verouderd en wordt zo getoond én geblokkeerd.
    bewerkt = DefinitionRepository(repo.db_path).get(rec.id)
    bewerkt.definitie = TEKST + " (gewijzigd)"
    assert repo.save(bewerkt) == rec.id
    gewijzigd = _facade(repo).get_definitie(rec.id)
    m3 = _mock_st()
    with (
        patch("ui.components.expert_review_tab.st", m3),
        patch("ui.components.validation_view.st", m3),
        patch("ui.components.sources_renderer.st", m3),
    ):
        ExpertReviewTab(_facade(repo))._render_bronbasiscontract(gewijzigd)
    tekst = _teksten(m3)
    assert "VEROUDERD" in tekst or "verouderd" in tekst
    assert "niet toegepast" in tekst
    blokkades = DefinitionWorkflowService._con02_blokkades(gewijzigd)
    assert any("eerdere uitzondering niet toegepast" in b for b in blokkades)


def test_versieconflict_bij_vastleggen_is_een_waarschuwing_geen_stil_succes(
    repo, sessie
):
    rec = _record_in_review(repo, scenario="fail", bronnen=[])
    SessionStateManager.set_value("selected_review_definition", rec)
    SessionStateManager.set_value("user", ACTOR)
    # Intussen gewijzigd door iemand anders (status-only): versie 2.
    assert _facade(repo).change_status(rec.id, DefinitieStatus.DRAFT, "iemand-anders")
    m = _mock_st()
    with patch("ui.components.expert_review_tab.st", m):
        ExpertReviewTab(_facade(repo))._leg_bronreview_vast(
            rec,
            {
                "type": "no_appropriate_source",
                "accepted": True,
                "actor": ACTOR,
                "rationale": "x",
                "version_number": rec.version_number,
                "fingerprint": _vingerafdruk([]),
                "search": {"queries": ["q"], "consulted": [], "conclusion": "niets"},
            },
            ACTOR,
        )
    assert m.success.call_count == 0
    assert any("intussen" in str(c.args[0]) for c in m.warning.call_args_list)
    assert _facade(repo).get_definitie(rec.id).get_source_review() is None
    getoond: Any = SessionStateManager.get_value("selected_review_definition")
    assert getoond.version_number == rec.version_number + 1


def test_payloadfout_uit_d_wordt_als_fout_getoond(repo, sessie):
    rec = _record_in_review(repo, scenario="fail", bronnen=[])
    SessionStateManager.set_value("selected_review_definition", rec)
    m = _mock_st()
    with patch("ui.components.expert_review_tab.st", m):
        ExpertReviewTab(_facade(repo))._leg_bronreview_vast(
            rec, {"type": "pass", "accepted": True, "actor": ACTOR}, ACTOR
        )
    assert m.success.call_count == 0
    assert any("geweigerd" in str(c.args[0]) for c in m.error.call_args_list)


# --------------------------------------------------------------- gate (CON-02)


@pytest.mark.parametrize(
    ("scenario", "bronnen", "verwacht_blok"),
    [
        ("pass", None, False),
        ("fail", None, True),
        ("open", None, True),
        ("error", None, True),
        # Geen bronnen en geen gedocumenteerde uitzondering: ontbrekend
        # bronbewijs kan niet als goedgekeurd gelden.
        ("fail", [], True),
    ],
)
def test_gate_blokkeert_op_fail_error_open_en_ontbrekend_bewijs(
    repo, scenario, bronnen, verwacht_blok
):
    rec = _record_in_review(repo, scenario=scenario, bronnen=bronnen)
    blokkades = DefinitionWorkflowService._con02_blokkades(rec)
    assert bool(blokkades) is verwacht_blok, blokkades
    if scenario == "error":
        assert any("Technisch probleem" in b for b in blokkades)
    if scenario == "fail" and bronnen is None:
        assert any("Voldoet niet" in b for b in blokkades)


def test_gate_blokkeert_op_verouderde_beoordeling(repo):
    rec = _record_in_review(repo, scenario="pass")
    assert DefinitionWorkflowService._con02_blokkades(rec) == []
    bewerkt = DefinitionRepository(repo.db_path).get(rec.id)
    bewerkt.definitie = TEKST + " (gewijzigd)"
    assert repo.save(bewerkt) == rec.id
    blokkades = DefinitionWorkflowService._con02_blokkades(
        _facade(repo).get_definitie(rec.id)
    )
    assert any("verouderd/niet toegepast" in b for b in blokkades), blokkades


def test_preview_gate_behoudt_scoregate_en_voegt_con02_toe(repo):
    """De bestaande blokkade bij validation_score None (DEF-630) blijft; CON-02
    komt er niet-overrulebaar bij; een kale vervanger zonder bronvelden krijgt
    geen verzonnen CON-02-blokkade."""
    rec = _record_in_review(repo, scenario="fail")
    from services.workflow_service import WorkflowService

    workflow = DefinitionWorkflowService(WorkflowService(), _facade(repo))
    gate = workflow.preview_gate(rec.id)
    assert gate["status"] == "blocked"
    assert (
        "Geen validatieresultaat beschikbaar (eerst (her)valideren)" in gate["reasons"]
    )
    assert any(r.startswith("CON-02 Voldoet niet") for r in gate["reasons"])
    kaal = MagicMock(spec=[])
    assert DefinitionWorkflowService._con02_blokkades(kaal) == []


# ----------------------------------------------------------- editor (knop)


def test_voorstelknop_doet_zonder_klik_niets_en_met_klik_een_aanroep(repo, sessie):
    from ui.components.definition_edit_tab import DefinitionEditTab

    did = repo.save(_definition(scenario="fail", status="draft"))
    geladen = DefinitionRepository(repo.db_path).get(did)
    SessionStateManager.set_value("editing_definition_id", did)
    SessionStateManager.set_value("editing_definition", geladen)
    SessionStateManager.set_value(f"edit_{did}_definitie", geladen.definitie)
    SessionStateManager.set_value("user", ACTOR)
    ai = FakeAI()
    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = DefinitionEditService(
        repository=repo,
        validation_service=None,
        proposal_service=SourceProposalService(ai),
    )

    # Rerun zonder klik (en bronbasis-weergave): geen aanroep.
    m = _mock_st()
    with (
        patch("ui.components.definition_edit_tab.st", m),
        patch("ui.components.sources_renderer.st", m),
        patch("ui.components.validation_view.st", m),
    ):
        tab._render_bronbasis_section(geladen)
        tab._render_voorstel_section(geladen)
    assert ai.calls == 0
    knop = [
        c
        for c in m.button.call_args_list
        if c.kwargs.get("key") == f"edit_{did}_vraag_voorstel"
    ]
    assert len(knop) == 1 and knop[0].kwargs.get("disabled") is False
    assert (
        "voldoet niet" in _teksten(m).lower()
    )  # de fail is zichtbaar, geen auto-aanvraag

    # Expliciete klik: precies één aanroep; origineel ongewijzigd; resultaat getoond.
    m2 = _mock_st(**{f"edit_{did}_vraag_voorstel": True})
    with (
        patch("ui.components.definition_edit_tab.st", m2),
        patch("ui.components.sources_renderer.st", m2),
        patch("ui.components.validation_view.st", m2),
    ):
        tab._render_voorstel_section(geladen)
    assert ai.calls == 1
    resultaat: Any = SessionStateManager.get_value(f"edit_{did}_voorstel_resultaat")
    assert resultaat["status"] == "proposed"
    na = _facade(repo).get_definitie(did)
    assert na.get_definitie_tekst() == TEKST
    assert len(na.get_source_proposals()) == 1
    # Het geladen record is ververst (reservering bumpt de versie).
    ververst: Any = SessionStateManager.get_value("editing_definition")
    assert ververst.metadata["version_number"] == na.version_number

    # Tweede klik (dubbelklik/rerun): geen tweede aanroep, expliciete melding.
    m3 = _mock_st(**{f"edit_{did}_vraag_voorstel": True})
    with (
        patch("ui.components.definition_edit_tab.st", m3),
        patch("ui.components.sources_renderer.st", m3),
        patch("ui.components.validation_view.st", m3),
    ):
        tab._render_voorstel_section(ververst)
    assert ai.calls == 1
    assert SessionStateManager.get_value(f"edit_{did}_voorstel_resultaat")[
        "status"
    ] == ("attempt_consumed")
    tekst = _teksten(m3)
    assert "Voorgestelde tekst" in tekst and "Oorspronkelijke tekst (bewaard)" in tekst


def test_voorstelknop_is_uitgeschakeld_bij_onopgeslagen_bewerking_of_zonder_actor(
    repo, sessie
):
    from ui.components.definition_edit_tab import DefinitionEditTab

    did = repo.save(_definition(scenario="fail", status="draft"))
    geladen = DefinitionRepository(repo.db_path).get(did)
    SessionStateManager.set_value("editing_definition_id", did)
    SessionStateManager.set_value("editing_definition", geladen)
    ai = FakeAI()
    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = DefinitionEditService(
        repository=repo,
        validation_service=None,
        proposal_service=SourceProposalService(ai),
    )

    def _knop(m: MagicMock):
        return next(
            c
            for c in m.button.call_args_list
            if c.kwargs.get("key") == f"edit_{did}_vraag_voorstel"
        )

    # Zonder actor: uitgeschakeld, klik doet niets.
    SessionStateManager.set_value(f"edit_{did}_definitie", geladen.definitie)
    m = _mock_st(**{f"edit_{did}_vraag_voorstel": True})
    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_voorstel_section(geladen)
    assert (
        _knop(m).kwargs["disabled"] is True
        and "reviewer" in _knop(m).kwargs["help"].lower()
    )
    # Met actor maar onopgeslagen bewerking: uitgeschakeld.
    SessionStateManager.set_value("user", ACTOR)
    SessionStateManager.set_value(
        f"edit_{did}_definitie", geladen.definitie + " bewerkt"
    )
    m = _mock_st(**{f"edit_{did}_vraag_voorstel": True})
    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_voorstel_section(geladen)
    assert (
        _knop(m).kwargs["disabled"] is True and "Sla eerst" in _knop(m).kwargs["help"]
    )
    assert ai.calls == 0
    assert _facade(repo).get_definitie(did).get_source_proposals() == []


def test_edit_service_zonder_dienst_meldt_unavailable_zonder_aanroep(repo):
    did = repo.save(_definition(scenario="fail", status="draft"))
    service = DefinitionEditService(repository=repo, validation_service=None)
    uit = asyncio.run(service.vraag_verbetervoorstel(did, actor=ACTOR))
    assert uit["status"] == "unavailable"


def test_toepassen_is_uitgeschakeld_en_geblokkeerd_bij_onopgeslagen_bewerking(
    repo, sessie
):
    """Bevinding 1 (Codex-vervolgreview): een niet-opgeslagen bewerking in het
    tekstwidget mag niet door 'Pas voorstel toe' worden overschreven. De knop
    staat uit mét Sla-eerst-uitleg; de handler zelf weigert ook (geen dienst-,
    model- of DB-aanroep, niets klaargezet, widget onaangeroerd)."""
    from ui.components.definition_edit_tab import DefinitionEditTab

    did = repo.save(_definition(scenario="fail", status="draft"))
    ai = FakeAI()
    dienst = DefinitionEditService(
        repository=repo,
        validation_service=None,
        proposal_service=SourceProposalService(ai),
    )
    aanvraag = asyncio.run(dienst.vraag_verbetervoorstel(did, actor=ACTOR))
    assert aanvraag["status"] == "proposed"
    pid = aanvraag["proposal_id"]
    geladen = DefinitionRepository(repo.db_path).get(did)
    SessionStateManager.set_value("editing_definition_id", did)
    SessionStateManager.set_value("editing_definition", geladen)
    SessionStateManager.set_value("user", ACTOR)
    bewerkt = geladen.definitie + " (nog niet opgeslagen)"
    SessionStateManager.set_value(f"edit_{did}_definitie", bewerkt)
    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = dienst

    def _knop(m: MagicMock, naam: str):
        return next(
            c
            for c in m.button.call_args_list
            if c.kwargs.get("key") == f"edit_{did}_voorstel_{pid}_{naam}"
        )

    # Weergave: Toepassen uit met Sla-eerst-uitleg; Afwijzen raakt de tekst niet.
    m = _mock_st(**{f"edit_{did}_voorstel_{pid}_toepassen": True})
    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_voorstel_section(geladen)
    toepassen = _knop(m, "toepassen")
    assert toepassen.kwargs["disabled"] is True
    assert "Sla eerst" in toepassen.kwargs["help"]
    assert _knop(m, "afwijzen").kwargs["disabled"] is False

    # Handler rechtstreeks (tegenproef): geen aanroep van de dienst.
    m2 = _mock_st()
    with (
        patch("ui.components.definition_edit_tab.st", m2),
        patch.object(dienst, "pas_voorstel_toe") as dienst_toepassen,
        patch.object(tab, "_refresh_current_definition") as ververs,
    ):
        tab._pas_voorstel_toe(did, pid, ACTOR)
    dienst_toepassen.assert_not_called()
    ververs.assert_not_called()
    resultaat: Any = SessionStateManager.get_value(f"edit_{did}_voorstel_resultaat")
    assert resultaat["status"] == "unsaved_changes"
    assert "Sla eerst" in resultaat["message"]
    assert SessionStateManager.get_value(f"edit_{did}_definitie") == bewerkt
    assert SessionStateManager.get_value(f"edit_{did}_pending_definitie") is None
    na = _facade(repo).get_definitie(did)
    assert na.get_definitie_tekst() == TEKST
    assert na.version_number == geladen.metadata["version_number"]
    assert [v["status"] for v in na.get_source_proposals()] == ["proposed"]
    # De melding is in de sectie zichtbaar als waarschuwing, niet als fout.
    m3 = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m3):
        tab._render_voorstel_section(geladen)
    assert any("Sla eerst" in str(c.args[0]) for c in m3.warning.call_args_list)
    assert not any("Sla eerst" in str(c.args[0]) for c in m3.error.call_args_list)

    # Na opslaan van de bewerking is de knop weer beschikbaar.
    SessionStateManager.set_value(f"edit_{did}_definitie", geladen.definitie)
    m4 = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m4):
        tab._render_voorstel_section(geladen)
    assert _knop(m4, "toepassen").kwargs["disabled"] is False


# ------------------------------------------- reviewbevindingen F5/F6 (bronnen)


def test_f5_gelijke_passages_in_verschillende_bronnen_houden_eigen_identiteit(sessie):
    """F5: twee bronnen met dezelfde passage maar een andere versie/vindplaats
    krijgen elk hun eigen canonieke id, versie, vindplaats en bewijs — niet
    de eerste die toevallig dezelfde inhoudshash heeft."""
    from domain.sources.normalisatie import canoniseer_bronnen
    from ui.components.sources_renderer import SourcesRenderer

    passage = (
        "Onder toezichthouder wordt verstaan: de door het bestuur aangewezen persoon."
    )
    bronnen = [
        {
            "provider": "rag",
            "chunk_id": "c1",
            "document_id": "beleid-2024",
            "title": "Beleidsregel 2024",
            "source_version": "2024",
            "legal": {"citation_text": "Beleidsregel 2024, art. 2"},
            "url": None,
            "snippet": passage,
        },
        {
            "provider": "rag",
            "chunk_id": "c2",
            "document_id": "beleid-2026",
            "title": "Beleidsregel 2026",
            "source_version": "2026",
            "legal": {"citation_text": "Beleidsregel 2026, art. 3"},
            "url": None,
            "snippet": passage,
        },
    ]
    ids = SourcesRenderer._canonieke_ids(bronnen)
    canoniek = {b.source_id: b for b in canoniseer_bronnen(bronnen)}
    assert len(canoniek) == 2
    assert ids[0].source_id != ids[1].source_id
    assert ids[0].version == "2024" and ids[1].version == "2026"
    assert ids[0].locator == "Beleidsregel 2024, art. 2"
    assert ids[1].locator == "Beleidsregel 2026, art. 3"
    # Dezelfde passage in twee bronnen: het bewijs van bron 2 hoort bij rij 2.
    beoordeling = {
        "status": "assessed",
        "parts": {
            "reference_quality": {
                "status": "pass",
                "sources": [
                    {
                        "source_id": ids[1].source_id,
                        "locatable": True,
                        "reason": "art. 3",
                    }
                ],
                "evidence": [
                    {
                        "source_id": ids[1].source_id,
                        "quote": "aangewezen persoon",
                        "locator": ids[1].locator,
                    }
                ],
            }
        },
    }
    m = _mock_st()
    with patch("ui.components.sources_renderer.st", m):
        SourcesRenderer()._render_bron_bewijs(bronnen[0], ids[0], beoordeling)
    assert "Geverifieerd citaat" not in _teksten(m)
    m2 = _mock_st()
    with patch("ui.components.sources_renderer.st", m2):
        SourcesRenderer()._render_bron_bewijs(bronnen[1], ids[1], beoordeling)
    tekst = _teksten(m2)
    assert "Geverifieerd citaat" in tekst and "aangewezen persoon" in tekst
    assert f"Bron-id: {ids[1].source_id}" in tekst and "versie: 2026" in tekst


def test_f5_identieke_rijen_delen_een_bron_en_meerdere_passages_zelfde_document(sessie):
    from ui.components.sources_renderer import SourcesRenderer

    bron = {
        "provider": "documents",
        "doc_id": "d1",
        "title": "d.pdf",
        "snippet": "Passage A.",
    }
    ander = {
        "provider": "documents",
        "doc_id": "d1",
        "title": "d.pdf",
        "snippet": "Passage B.",
    }
    ids = SourcesRenderer._canonieke_ids([bron, dict(bron), ander])
    assert ids[0].source_id == ids[1].source_id  # volledig identiek: één bron
    assert ids[2].source_id != ids[0].source_id  # zelfde document, andere passage
    assert ids[2].passage == "Passage B." and ids[0].passage == "Passage A."


def test_f6_beoordeelde_passage_en_content_only_bronnen_zichtbaar(sessie):
    """F6: een gesanitiseerde/afgekapte bron toont de canonieke opgeslagen
    passage (prompt_content) expliciet naast de aangeleverde — zonder
    kwitantie niet als 'wat de beoordeling zag'; een bron met alleen
    `content`/`chunk_text` toont wél een fragment."""
    from ui.components.sources_renderer import SourcesRenderer

    origineel = "Tekst met <b>opmaak</b> " + "en heel veel tekst. " * 40
    gesaneerd = ("Tekst met opmaak " + "en heel veel tekst. " * 40)[:300] + "[…]"
    bronnen = [
        {
            "provider": "rag",
            "chunk_id": "c1",
            "title": "Register",
            "snippet": origineel,
            "prompt_content": gesaneerd,
            "used_in_prompt": True,
            "sanitized": True,
            "truncated": True,
            "receipt_nr": 1,
        },
        {
            "provider": "rag",
            "chunk_id": "c2",
            "title": "Alleen content",
            "content": "Passage uit content.",
        },
        {
            "provider": "rag",
            "chunk_id": "c3",
            "title": "Alleen chunk",
            "chunk_text": "Passage uit chunk_text.",
        },
    ]
    m = _mock_st()
    m.expander.return_value.__enter__ = lambda s: s
    m.expander.return_value.__exit__ = lambda s, *a: False
    with patch("ui.components.sources_renderer.st", m):
        SourcesRenderer().render_bronbasis_section(
            sources=bronnen, assessment=None, titel=""
        )
    tekst = _teksten(m)
    # De canonieke opgeslagen passage (prompt_content) staat apart van de
    # aangeleverde; zonder beoordelingskwitantie wordt zij níet als
    # "wat de beoordeling zag" gepresenteerd.
    assert "Canonieke opgeslagen passage" in tekst
    assert "wijkt af van de aangeleverde passage" in tekst
    assert gesaneerd[:200] in tekst  # de canonieke tekst zelf
    assert "Wat de beoordeling zag: onbekend" in tekst
    assert "gebonden beoordelingskwitantie" not in tekst
    assert "**Fragment**: Tekst met <b>opmaak</b>" in tekst  # origineel blijft
    assert "**Fragment**: Passage uit content." in tekst
    assert "**Fragment**: Passage uit chunk_text." in tekst
    assert (
        "Generatie (kwitantie): werkelijk in de prompt als bron nr 1 (afgekapt, gesanitiseerd)"
        in tekst
    )
    assert "zegt niets over gezag" in tekst


# --------------------------------------- deskundige correctie (C §6b) — mocked st


def _correctie_mock(
    rec, *, status: str, citaat: str, onderdeel: str = "semantic_support"
):
    from domain.sources.normalisatie import canoniseer_bronnen

    awb = next(b for b in canoniseer_bronnen(BRONNEN) if b.source_id.startswith("rag:"))
    s = f"con02_{rec.id}"
    return _mock_st(
        **{
            f"{s}_soort": "part_correction",
            f"{s}_corr_onderdeel": onderdeel,
            f"{s}_corr_status": status,
            f"{s}_corr_bron": awb.source_id,
            f"{s}_corr_citaat": citaat,
            f"{s}_corr_motivering": "Deskundig oordeel over de betekenissteun.",
            f"{s}_accepted": True,
            f"{s}_vastleggen": True,
        }
    )


def _render_con02(repo, rec, m):
    with (
        patch("ui.components.expert_review_tab.st", m),
        patch("ui.components.validation_view.st", m),
        patch("ui.components.sources_renderer.st", m),
    ):
        ExpertReviewTab(_facade(repo))._render_bronbasiscontract(rec)


def test_correctie_naar_pass_toont_origineel_ai_oordeel_en_is_geen_uitzondering(
    repo, sessie
):
    from domain.sources.contract import beoordeel_bronbasis

    rec = _record_in_review(repo, scenario="fail")
    SessionStateManager.set_value("selected_review_definition", rec)
    SessionStateManager.set_value("user", ACTOR)
    m = _correctie_mock(
        rec, status="pass", citaat="krachtens publiekrecht is ingesteld"
    )
    _render_con02(repo, rec, m)
    tekst = _teksten(m)
    # Het oorspronkelijke AI-oordeel over het gekozen onderdeel staat apart.
    assert "Oorspronkelijk oordeel over Betekenissteun (AI): voldoet niet" in tekst
    na = _facade(repo).get_definitie(rec.id)
    review = na.get_source_review()
    assert review is not None, tekst[-2000:]
    assert review["type"] == "part_correction"
    assert review["part_id"] == "semantic_support" and review["status"] == "pass"
    assert review["evidence"][0]["source_id"].startswith("rag:")
    assert review["evidence"][0]["content_hash"]  # gebonden aan de bewaarde passage
    assert review["actor"] == ACTOR and review["accepted"] is True
    assert "exceptions" not in review

    velden = na.get_contractvelden()
    uitkomst = beoordeel_bronbasis(
        na.begrip,
        na.get_definitie_tekst(),
        na.get_contextlijsten(),
        velden["provenance_sources"],
        assessment=velden["source_assessment"],
        review=velden["source_review"],
        definitie_versie=velden["definition_version"],
        peildatum=velden["peildatum"],
    )
    assert uitkomst.status == "pass"  # alle onderdelen voldoen nu — geen uitzondering
    assert uitkomst.review["accepted_exception"] is None
    correctie = uitkomst.review["applied_correction"]
    assert correctie["part_id"] == "semantic_support"
    assert correctie["original"]["status"] == "fail"  # AI-oordeel bewaard
    steun = next(p for p in uitkomst.parts if p.id == "semantic_support")
    assert steun.field == "source_review" and steun.status == "pass"
    assert "Oorspronkelijk oordeel (fail)" in steun.reason
    # Weergave: correctie herkenbaar, niet als uitzondering.
    m2 = _mock_st()
    _render_con02(repo, na, m2)
    tekst2 = _teksten(m2)
    assert "Deskundige correctie van betekenissteun door Reviewer Rood" in tekst2
    assert "Oorspronkelijk AI-oordeel: ❌ Voldoet niet" in tekst2
    assert "geen uitzondering" in tekst2.lower()
    assert (
        "Er is al een vastgelegde CON-02-beoordeling" in tekst2
    )  # vervangen wordt gemeld
    assert DefinitionWorkflowService._con02_blokkades(na) == []


def test_correctie_naar_fail_met_bewijs_en_stale_na_tekstwijziging(repo, sessie):
    rec = _record_in_review(repo, scenario="pass")
    SessionStateManager.set_value("selected_review_definition", rec)
    SessionStateManager.set_value("user", ACTOR)
    m = _correctie_mock(
        rec, status="fail", citaat="met uitzondering van de rechterlijke macht"
    )
    _render_con02(repo, rec, m)
    na = _facade(repo).get_definitie(rec.id)
    review = na.get_source_review()
    assert review is not None and review["status"] == "fail"
    assert DefinitionWorkflowService._con02_blokkades(na)  # deskundige fail blokkeert
    # Tekstwijziging: de correctie is verouderd; het AI-oordeel (pass) geldt weer
    # als origineel maar de correctie telt niet meer en wordt benoemd.
    bewerkt = DefinitionRepository(repo.db_path).get(rec.id)
    bewerkt.definitie = TEKST + " (gewijzigd)"
    assert repo.save(bewerkt) == rec.id
    gewijzigd = _facade(repo).get_definitie(rec.id)
    m2 = _mock_st()
    _render_con02(repo, gewijzigd, m2)
    tekst = _teksten(m2)
    assert "niet toegepast" in tekst and ("VEROUDERD" in tekst or "verouderd" in tekst)


def test_correctie_met_citaat_dat_niet_in_de_bron_staat_wordt_geweigerd(repo, sessie):
    rec = _record_in_review(repo, scenario="fail")
    SessionStateManager.set_value("selected_review_definition", rec)
    SessionStateManager.set_value("user", ACTOR)
    m = _correctie_mock(rec, status="pass", citaat="dit citaat staat nergens")
    _render_con02(repo, rec, m)
    assert _facade(repo).get_definitie(rec.id).get_source_review() is None
    assert any("geweigerd" in str(c.args[0]) for c in m.error.call_args_list)
    assert not any("vastgelegd" in str(c.args[0]) for c in m.success.call_args_list)


def test_correctie_zonder_bewijs_bij_pass_is_uitgeschakeld(repo, sessie):
    rec = _record_in_review(repo, scenario="fail")
    SessionStateManager.set_value("selected_review_definition", rec)
    SessionStateManager.set_value("user", ACTOR)
    m = _correctie_mock(rec, status="pass", citaat="")
    _render_con02(repo, rec, m)
    knop = next(
        c
        for c in m.button.call_args_list
        if c.kwargs.get("key") == f"con02_{rec.id}_vastleggen"
    )
    assert knop.kwargs["disabled"] is True and "citaat" in knop.kwargs["help"]
    assert _facade(repo).get_definitie(rec.id).get_source_review() is None


# ------------------------------- F5 (root-probe) en F6/C5 (beoordelingskwitantie)


def test_f5_rijen_die_alleen_in_source_id_verschillen_houden_eigen_id_en_bewijs(sessie):
    """Root-probe: A en B met identieke titel/passage/metadata, alleen een
    ander aangeleverd `source_id`. Elke rij houdt haar eigen stabiele id; het
    bewijs dat aan B bindt verschijnt niet bij A."""
    from ui.components.sources_renderer import SourcesRenderer

    passage = (
        "Onder toezichthouder wordt verstaan: de door het bestuur aangewezen persoon."
    )
    bronnen = [
        {"source_id": "A", "title": "Gelijke titel", "snippet": passage},
        {"source_id": "B", "title": "Gelijke titel", "snippet": passage},
    ]
    ids = SourcesRenderer._canonieke_ids(bronnen)
    assert (ids[0].source_id, ids[1].source_id) == ("A", "B")
    beoordeling = {
        "status": "assessed",
        "parts": {
            "semantic_support": {
                "status": "pass",
                "evidence": [
                    {"source_id": "B", "quote": "aangewezen persoon", "locator": None}
                ],
                "claims": [],
            }
        },
    }
    m_a, m_b = _mock_st(), _mock_st()
    with patch("ui.components.sources_renderer.st", m_a):
        SourcesRenderer()._render_bron_bewijs(bronnen[0], ids[0], beoordeling)
    with patch("ui.components.sources_renderer.st", m_b):
        SourcesRenderer()._render_bron_bewijs(bronnen[1], ids[1], beoordeling)
    assert "Geverifieerd citaat" not in _teksten(m_a) and "Bron-id: A" in _teksten(m_a)
    assert "Geverifieerd citaat" in _teksten(m_b) and "Bron-id: B" in _teksten(m_b)


def test_f5_zelfde_source_id_andere_versie_krijgt_eigen_variant_en_hash_in_id_blijft(
    sessie,
):
    """Twee rijen met hetzelfde aangeleverde id maar een andere versie zijn
    twee varianten (`<id>#…`), elk correct gekoppeld; een origineel id dat
    zelf een '#' bevat wordt niet afgeknipt."""
    from ui.components.sources_renderer import SourcesRenderer

    bronnen = [
        {
            "source_id": "doc:reg#1",
            "title": "Register",
            "snippet": "Tekst.",
            "source_version": "2024",
        },
        {
            "source_id": "doc:reg#1",
            "title": "Register",
            "snippet": "Tekst.",
            "source_version": "2026",
        },
        {"source_id": "doc:reg#1#x", "title": "Register", "snippet": "Tekst."},
    ]
    ids = SourcesRenderer._canonieke_ids(bronnen)
    assert ids[0].version == "2024" and ids[1].version == "2026"
    assert ids[0].source_id != ids[1].source_id
    assert ids[0].source_id.startswith("doc:reg#1#") and ids[1].source_id.startswith(
        "doc:reg#1#"
    )
    assert ids[2].source_id == "doc:reg#1#x" and ids[2].version is None


def _beoordeling_met_kwitantie(bronnen, *, cap):
    return bouw_beoordeling(
        BEGRIP, TEKST, CONTEXTEN, bronnen, scenario="pass", receipt_cap=cap
    )


def test_f6_gebonden_kwitantie_toont_wat_de_beoordeling_zag_met_afkapping(sessie):
    from ui.components.sources_renderer import SourcesRenderer

    lang = deepcopy(BRONNEN)
    lang[0]["snippet"] = lang[0]["snippet"] + " Vervolgtekst. " * 40  # > 300 tekens
    beoordeling = _beoordeling_met_kwitantie(lang, cap=300)
    ids = SourcesRenderer._canonieke_ids(lang)
    verzonden, status, afgekapt = SourcesRenderer._beoordelingskwitantie(
        lang, beoordeling
    )
    assert status is None
    awb_id = next(i.source_id for i in ids.values() if i.source_id.startswith("rag:"))
    assert afgekapt[awb_id] is True and len(verzonden[awb_id].passage) == 300
    m = _mock_st()
    with patch("ui.components.sources_renderer.st", m):
        SourcesRenderer()._render_bron_bewijs(
            lang[0],
            ids[0],
            beoordeling,
            verzonden=verzonden,
            kwitantiestatus=status,
            afgekapt=afgekapt,
        )
    tekst = _teksten(m)
    assert "Wat de beoordeling zag" in tekst and "afgekapt: 300 van" in tekst
    assert verzonden[awb_id].passage[:200] in tekst
    # De volledige opgeslagen passage blijft apart leesbaar (andere rol).
    assert "Canonieke opgeslagen passage = de aangeleverde passage hierboven." in tekst
    assert f"Bron-id: {awb_id}" in tekst


def test_f6_zonder_kwitantie_is_de_modelinvoer_onbekend_en_wordt_niets_verzonnen(
    sessie,
):
    from ui.components.sources_renderer import SourcesRenderer

    beoordeling = bouw_beoordeling(BEGRIP, TEKST, CONTEXTEN, BRONNEN, scenario="pass")
    assert beoordeling["assessment_receipt"] is None
    verzonden, status, afgekapt = SourcesRenderer._beoordelingskwitantie(
        BRONNEN, beoordeling
    )
    assert (verzonden, status, afgekapt) == ({}, "afwezig", {})
    ids = SourcesRenderer._canonieke_ids(BRONNEN)
    m = _mock_st()
    with patch("ui.components.sources_renderer.st", m):
        SourcesRenderer()._render_bron_bewijs(
            BRONNEN[0],
            ids[0],
            beoordeling,
            verzonden=verzonden,
            kwitantiestatus=status,
            afgekapt=afgekapt,
        )
    tekst = _teksten(m)
    assert "Wat de beoordeling zag: onbekend" in tekst
    assert "gebonden beoordelingskwitantie" not in tekst  # geen verzonnen claim


def test_f6_niet_bindende_kwitantie_claimt_niets(sessie):
    from ui.components.sources_renderer import SourcesRenderer

    beoordeling = _beoordeling_met_kwitantie(BRONNEN, cap=300)
    # Kwitantie hoort bij een andere bronversie (vervalst/verouderd).
    beoordeling["assessment_receipt"]["sources"][0]["original_content_hash"] = "anders"
    verzonden, status, _ = SourcesRenderer._beoordelingskwitantie(BRONNEN, beoordeling)
    assert verzonden == {} and status and "hoort niet bij deze bronnen" in status
    m = _mock_st()
    m.expander.return_value.__enter__ = lambda s: s
    m.expander.return_value.__exit__ = lambda s, *a: False
    with patch("ui.components.sources_renderer.st", m):
        SourcesRenderer().render_bronbasis_section(
            sources=BRONNEN, assessment=beoordeling, titel=""
        )
    tekst = _teksten(m)
    assert "Beoordelingskwitantie bindt niet aan de opgeslagen bronnen" in tekst
    assert "Wat de beoordeling zag: niet vast te stellen" in tekst
    assert "gebonden beoordelingskwitantie" not in tekst
