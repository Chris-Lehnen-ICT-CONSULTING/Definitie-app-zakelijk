"""DEF-743 pakket F — echte Streamlit-controls (AppTest, subprocess, offline-gate).

Zelfde opzet als ``test_def743_sources_presentation.py``: de pytest-conftest
vervangt ``streamlit`` procesbreed door een mock, dus dit bestand start zichzelf
als subprocess-driver achter ``tests.offline_bootstrap`` en leest de
waarnemingen terug. Alles draait op een tijdelijke SQLite-database met de
geteld nagebootste AI-grenzen uit ``tests.fixtures.def743_fakes``.

Bewezen met échte widgets:

* geen UI-exceptie bij het renderen van de validatieweergave (oud numeriek
  resultaat), de bronbasis-sectie (assessment + platte uitzondering +
  kwitantie), de editor-voorstelsectie en de experttab-CON-02-sectie;
* geen totaalcijfer/percentage in de weergave, wél de dekking;
* de voorstelknop bestaat, doet niets zonder klik (0 modelaanroepen), doet
  precies één aanroep bij een klik en blokkeert een tweede klik
  (`attempt_consumed`) — het origineel blijft staan; het voorstel wordt
  afzonderlijk getoond met toepassen/afwijzen-knoppen;
* in de experttab schrijven de echte selectbox/text_area/checkbox/knop de
  platte, getypeerde `source_review` weg; de uitzondering verschijnt als
  uitzondering, niet als 'Voldoet';
* een niet-opgeslagen bewerking in het echte tekstwidget (autosave uit) zet
  'Pas voorstel toe' uit en de handler weigert zelf (widget/DB/voorstel
  onaangeroerd); na Opslaan weigert D's guard het verouderde origineel.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.slow]

REPO = Path(__file__).resolve().parents[3]
ACTOR = "Reviewer Rood"

# ------------------------------------------------------------------ driver
#
# `AppTest.from_function` voert de functie als los script uit: modulevariabelen
# van dit bestand zijn daar niet zichtbaar. De procesbrede staat (tmp-DB, fake
# AI) leeft daarom op de fixturemodule (één object in `sys.modules`).


def _opzet() -> dict:
    """Eenmalig per driverproces: tmp-DB, records, fake AI (op de fixturemodule)."""
    import tempfile
    from copy import deepcopy

    from services.definition_edit_repository import DefinitionEditRepository
    from services.interfaces import Definition
    from tests.fixtures import def743_fakes
    from tests.fixtures.def743_fakes import (
        BEGRIP,
        BRONNEN,
        JUR,
        ORG,
        TEKST,
        WET,
        FakeAI,
        FakeBronbeoordeling,
        bouw_beoordeling,
    )

    pad = Path(tempfile.mkdtemp()) / "apptest.db"
    repo = DefinitionEditRepository(str(pad))
    contexten = {
        "organisatorische_context": ORG,
        "juridische_context": JUR,
        "wettelijke_basis": WET,
    }
    did = repo.save(
        Definition(
            begrip=BEGRIP,
            definitie=TEKST,
            categorie="type",
            organisatorische_context=list(ORG),
            juridische_context=list(JUR),
            wettelijke_basis=list(WET),
            metadata={
                "status": "draft",
                "sources": deepcopy(BRONNEN),
                "provenance_sources": deepcopy(BRONNEN),
                "source_assessment": bouw_beoordeling(
                    BEGRIP,
                    TEKST,
                    contexten,
                    BRONNEN,
                    scenario="fail",
                    peildatum="2026-09-15",
                ),
                "peildatum": "2026-09-15",
            },
        )
    )
    # Tweede record (in review, zonder bronnen) voor de experttab-uitzondering.
    rid = repo.save(
        Definition(
            begrip="toezichthouder",
            definitie="door het bestuur aangewezen persoon die toeziet op de naleving",
            categorie="type",
            organisatorische_context=list(ORG),
            juridische_context=list(JUR),
            wettelijke_basis=list(WET),
            metadata={"status": "review", "sources": [], "provenance_sources": []},
        )
    )

    def _met_bronnen(begrip: str, tekst: str, *, scenario: str, status: str) -> int:
        return repo.save(
            Definition(
                begrip=begrip,
                definitie=tekst,
                categorie="type",
                organisatorische_context=list(ORG),
                juridische_context=list(JUR),
                wettelijke_basis=list(WET),
                metadata={
                    "status": status,
                    "sources": deepcopy(BRONNEN),
                    "provenance_sources": deepcopy(BRONNEN),
                    "source_assessment": bouw_beoordeling(
                        begrip,
                        tekst,
                        contexten,
                        BRONNEN,
                        scenario=scenario,
                        peildatum="2026-09-15",
                    ),
                    "peildatum": "2026-09-15",
                },
            )
        )

    # Volledige editor (F2): eigen record met CON-02-fail en verifieerbaar bewijs.
    did2 = _met_bronnen(
        "bestuursorgaan (editor)", TEKST, scenario="fail", status="draft"
    )
    # Bevinding 1 (vervolgreview): niet-opgeslagen bewerking vs. toepassen.
    did3 = _met_bronnen(
        "bestuursorgaan (onopgeslagen)", TEKST, scenario="fail", status="draft"
    )
    # Deskundige correctie via echte controls: naar pass (cid) en naar fail (cid2).
    cid = _met_bronnen(
        "bestuursorgaan (correctie)", TEKST, scenario="fail", status="review"
    )
    cid2 = _met_bronnen(
        "bestuursorgaan (correctie 2)", TEKST, scenario="pass", status="review"
    )
    # F6/C5: lange bron (> 300 tekens) met een beoordelingskwitantie op cap 300.
    lang = deepcopy(BRONNEN)
    lang[0]["snippet"] = lang[0]["snippet"] + " Vervolgtekst van de bron. " * 40
    kid = repo.save(
        Definition(
            begrip="bestuursorgaan (kwitantie)",
            definitie=TEKST,
            categorie="type",
            organisatorische_context=list(ORG),
            juridische_context=list(JUR),
            wettelijke_basis=list(WET),
            metadata={
                "status": "review",
                "sources": deepcopy(lang),
                "provenance_sources": deepcopy(lang),
                "source_assessment": bouw_beoordeling(
                    "bestuursorgaan (kwitantie)",
                    TEKST,
                    contexten,
                    lang,
                    scenario="pass",
                    peildatum="2026-09-15",
                    receipt_cap=300,
                ),
                "peildatum": "2026-09-15",
            },
        )
    )
    # F5 (root-probe): twee bronnen die alleen in `source_id` verschillen.
    ab = [
        {
            "source_id": "A",
            "title": "Gelijke titel",
            "snippet": "Gelijke passage over de toezichthouder.",
        },
        {
            "source_id": "B",
            "title": "Gelijke titel",
            "snippet": "Gelijke passage over de toezichthouder.",
        },
    ]
    staat = {
        "pad": str(pad),
        "did": did,
        "rid": rid,
        "kid": kid,
        "ab": ab,
        "lang_passage": lang[0]["snippet"],
        "did2": did2,
        "did3": did3,
        "cid": cid,
        "cid2": cid2,
        "ai": FakeAI(),
        "beoordeling": FakeBronbeoordeling("pass"),  # hertoetsing bij Apply
        "actor": ACTOR,
    }
    def743_fakes.APPTEST_STATE = staat  # type: ignore[attr-defined]
    return staat


def _app() -> None:
    import streamlit as st

    from database.definitie_repository import DefinitieRepository
    from services.definition_edit_repository import DefinitionEditRepository
    from services.definition_edit_service import DefinitionEditService
    from services.definition_repository import DefinitionRepository
    from services.source_proposal_service import SourceProposalService
    from tests.fixtures import def743_fakes
    from ui.components.definition_edit_tab import DefinitionEditTab
    from ui.components.expert_review_tab import ExpertReviewTab
    from ui.components.sources_renderer import SourcesRenderer
    from ui.components.validation_view import render_validation_detailed_list
    from ui.session_state import SessionStateManager

    staat = def743_fakes.APPTEST_STATE  # type: ignore[attr-defined]
    repo = DefinitionEditRepository(staat["pad"])
    did, rid = staat["did"], staat["rid"]
    ai = staat["ai"]

    st.markdown("## Validatieweergave (oud numeriek resultaat)")
    render_validation_detailed_list(
        {
            "validation_status": "validated",
            "overall_score": 0.82,
            "is_acceptable": True,
            "violations": [
                {"rule_id": "ESS-01", "description": "te kort", "severity": "high"}
            ],
            "passed_rules": ["VAL-EMP-001"],
            "rule_statuses": {
                "ESS-01": "fail",
                "VAL-EMP-001": "pass",
                "CON-02": "error",
            },
            "evaluation_coverage": {"total": 3, "passed": 1, "failed": 1, "error": 1},
            "rule_results": {},
        },
        key_prefix="legacy",
        show_toggle=False,
    )

    st.markdown("## Bronbasis (opgeslagen record)")
    geladen = DefinitionRepository(staat["pad"]).get(did)
    meta = dict(geladen.metadata or {})
    SourcesRenderer().render_bronbasis_section(
        sources=meta.get("provenance_sources"),
        assessment=meta.get("source_assessment"),
        receipt={
            "version": "1",
            "status": "used",
            "sources": [],
            "omitted": [
                {"source_type": "document", "source_id": "upload-7", "reason": "budget"}
            ],
            "errors": [],
            "channels": {"rag": {"enabled": True, "supplied": 1, "used": 1}},
        },
        review={
            "type": "reference_exception",
            "accepted": True,
            "actor": staat["actor"],
            "rationale": "Intern raadpleegbaar.",
            "version_number": 1,
            "fingerprint": "x",
            "reviewed_at": "2026-09-15T12:00:00",
            "source_id": "rag:doc-awb:chunk-awb-1-1",
            "content_hash": "abc",
            "source_version": "2026-09-14T10:00:00Z",
            "locator": "Awb art. 1:1",
        },
        con02=None,
        evidence_status=meta.get("source_evidence_status"),
        review_status={"status": "stale", "reason": None},
    )

    st.markdown("## Bronbasis — beoordelingskwitantie (cap 300)")
    kgeladen = DefinitionRepository(staat["pad"]).get(staat["kid"])
    kmeta = dict(kgeladen.metadata or {})
    SourcesRenderer().render_bronbasis_section(
        sources=kmeta.get("provenance_sources"),
        assessment=kmeta.get("source_assessment"),
        con02=None,
        titel="",
    )

    st.markdown("## Bronbasis — gelijke bronnen A/B (root-probe)")
    SourcesRenderer().render_bronbasis_section(
        sources=staat["ab"],
        assessment={
            "status": "assessed",
            "parts": {
                "semantic_support": {
                    "status": "pass",
                    "evidence": [
                        {"source_id": "B", "quote": "Gelijke passage", "locator": None}
                    ],
                    "claims": [],
                }
            },
        },
        con02=None,
        titel="",
    )

    st.markdown("## Editor — verbetervoorstel (losse sectie)")
    SessionStateManager.set_value("user", staat["actor"])
    # Elke run vers uit de DB (ID-only), zodat reservering/uitkomst zichtbaar zijn.
    los = DefinitionRepository(staat["pad"]).get(did)
    if SessionStateManager.get_value(f"edit_{did}_definitie") is None:
        SessionStateManager.set_value(f"edit_{did}_definitie", los.definitie)
    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = DefinitionEditService(
        repository=repo,
        validation_service=None,
        proposal_service=SourceProposalService(ai),
    )
    tab._render_bronbasis_section(los)
    tab._render_voorstel_section(los)

    st.markdown("## Experttab — CON-02")
    facade = DefinitieRepository(staat["pad"])
    rec = SessionStateManager.get_value("selected_review_definition")
    if rec is None or rec.id != rid:
        rec = facade.get_definitie(rid)
        SessionStateManager.set_value("selected_review_definition", rec)
    ExpertReviewTab(facade)._render_bronbasiscontract(rec)

    # ---- F2: de VOLLEDIGE editor (alle widgets, incl. het tekstwidget) ----
    st.markdown("## Volledige editor")
    from services.null_repository import NullDefinitionRepository
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from toetsregels.manager import get_toetsregel_manager

    orchestrator = ValidationOrchestratorV2(
        ModularValidationService(
            toetsregel_manager=get_toetsregel_manager(),
            repository=NullDefinitionRepository(),
        ),
        source_assessment_service=staat["beoordeling"],
    )
    volledige_tab = DefinitionEditTab(
        repository=DefinitionEditRepository(staat["pad"]),
        validation_service=orchestrator,
    )
    volledige_tab.edit_service.proposal_service = SourceProposalService(ai)
    # De driver kiest het editor-record (standaard did2; did3 voor bevinding 1).
    editor_id = SessionStateManager.get_value("apptest_editor_id") or staat["did2"]
    SessionStateManager.set_value("editing_definition_id", editor_id)
    volledige_tab.render()
    # Bevinding 1, tegenproef: de driver kan de Apply-handler rechtstreeks
    # aanroepen (de knop staat uit) — de handler moet zélf weigeren.
    probe = SessionStateManager.get_value("apptest_probe_toepassen")
    if isinstance(probe, dict):
        SessionStateManager.set_value("apptest_probe_toepassen", None)
        volledige_tab._pas_voorstel_toe(
            int(probe["def_id"]), str(probe["pid"]), staat["actor"]
        )

    # ---- deskundige correctie via echte controls (twee records) ----
    for sleutel in ("cid", "cid2"):
        st.markdown(f"## Experttab — correctie ({sleutel})")
        # Elke run vers uit de DB (ID-only herladen): de weergave toont wat
        # is opgeslagen, niet een eerder sessie-object.
        crec = facade.get_definitie(staat[sleutel])
        SessionStateManager.set_value("selected_review_definition", crec)
        ExpertReviewTab(facade)._render_bronbasiscontract(crec)


def _knop_disabled(at, sleutel: str) -> bool | None:
    """`disabled` van een knop; None als de knop (niet meer) bestaat."""
    for knop in at.button:
        if knop.key == sleutel:
            return bool(knop.disabled)
    return None


def _sessiewaarde(at, sleutel: str) -> dict:
    """`SafeSessionState` van AppTest kent geen `.get`; lees fail-safe."""
    if sleutel in at.session_state:
        waarde = at.session_state[sleutel]
        return dict(waarde) if isinstance(waarde, dict) else {}
    return {}


def _alle_tekst(at) -> str:
    return "\n".join(
        str(getattr(el, "value", el))
        for verzameling in (
            at.markdown,
            at.caption,
            at.success,
            at.info,
            at.warning,
            at.error,
            at.text,
        )
        for el in verzameling
    )


def _driver(uit_pad: str) -> None:
    for pad in (str(REPO), str(REPO / "src")):
        if pad not in sys.path:
            sys.path.insert(0, pad)
    from tests import offline_bootstrap

    offline_bootstrap.install()
    from streamlit.testing.v1 import AppTest

    from database.definitie_repository import DefinitieRepository
    from tests.fixtures.def743_fakes import BRONNEN as BRONNEN_KOPIE

    w: dict = {"gate_actief": offline_bootstrap.gate_is_actief(), "stappen": {}}
    staat = _opzet()
    ai = staat["ai"]

    at = AppTest.from_function(_app, default_timeout=180)
    at.run()
    did, rid = staat["did"], staat["rid"]
    facade = DefinitieRepository(staat["pad"])
    knop_vraag = f"edit_{did}_vraag_voorstel"
    w["stappen"]["render"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "tekst": _alle_tekst(at),
        # Lijst (geen dict op label): dezelfde bronlabels komen in meerdere
        # secties voor.
        "expander_teksten": [
            "\n".join(
                [str(x.value) for x in e.markdown]
                + [str(x.value) for x in e.caption]
                + [str(x.value) for x in e.text]
                + [str(x.value) for x in e.warning]
            )
            for e in at.expander
        ],
        "lang_passage": staat["lang_passage"],
        "ai_calls": ai.calls,
        "knoppen": [b.key for b in at.button],
        "expanders": [e.label for e in at.expander],
        "tekst_db": facade.get_definitie(did).get_definitie_tekst(),
        "voorstellen": len(facade.get_definitie(did).get_source_proposals()),
    }

    # Klik 1: precies één aanroep; voorstel getoond, origineel ongewijzigd.
    at.button(key=knop_vraag).click().run()
    rec = facade.get_definitie(did)
    voorstellen = rec.get_source_proposals()
    w["stappen"]["klik1"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "ai_calls": ai.calls,
        "tekst": _alle_tekst(at),
        "tekst_db": rec.get_definitie_tekst(),
        "voorstellen": [
            {
                "status": v.get("status"),
                "outcome": (v.get("outcome") or {}).get("status"),
            }
            for v in voorstellen
        ],
        "knoppen": [b.key for b in at.button],
    }

    # Klik 2: dubbelklik/rerun → geen tweede aanroep.
    at.button(key=knop_vraag).click().run()
    w["stappen"]["klik2"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "ai_calls": ai.calls,
        "tekst": _alle_tekst(at),
        "voorstellen": len(facade.get_definitie(did).get_source_proposals()),
        "resultaat_status": at.session_state[f"edit_{did}_voorstel_resultaat"][
            "status"
        ],
    }

    # ---- F2: volledige editor — aanvragen, toepassen, herladen ----
    did2 = staat["did2"]
    beoordeling = staat["beoordeling"]
    w["stappen"]["editor_render"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "tekst_widget": at.text_area(key=f"edit_{did2}_definitie").value,
        "ai_calls": ai.calls,
        "hertoets_calls": beoordeling.calls,
    }
    at.button(key=f"edit_{did2}_vraag_voorstel").click().run()
    rec2 = facade.get_definitie(did2)
    [voorstel2] = rec2.get_source_proposals()
    pid2 = voorstel2["proposal_id"]
    w["stappen"]["editor_aanvraag"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "ai_calls": ai.calls,
        "status": voorstel2["status"],
        "kandidaat": (voorstel2.get("outcome") or {}).get("candidate_text"),
        "knoppen": [b.key for b in at.button],
        "tekst_widget": at.text_area(key=f"edit_{did2}_definitie").value,
    }
    at.button(key=f"edit_{did2}_voorstel_{pid2}_toepassen").click().run()
    na = facade.get_definitie(did2)
    resultaat = at.session_state[f"edit_{did2}_voorstel_resultaat"]
    w["stappen"]["editor_apply"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "resultaat_status": resultaat.get("status"),
        "resultaat_message": resultaat.get("message"),
        "ai_calls": ai.calls,
        "hertoets_calls": beoordeling.calls,
        "hertoets_bronnen_gelijk": beoordeling.laatste_bronnen == BRONNEN_KOPIE,
        "tekst_db": na.get_definitie_tekst(),
        "versie_db": na.version_number,
        "tekst_widget": at.text_area(key=f"edit_{did2}_definitie").value,
        "voorstel_status": na.get_source_proposal(pid2)["status"],
        "historie_origineel": [
            h.get("candidate", {}).get("definitie")
            for h in na.get_source_evidence_history()
        ],
        "bewijs_origin": (na.get_source_evidence() or {}).get("origin"),
        "validatie_con02": (
            _sessiewaarde(at, "edit_last_validation")
            .get("rule_results", {})
            .get("CON-02", {})
            .get("status")
        ),
        "tekst": _alle_tekst(at),
    }
    # Herladen van hetzelfde ID (verse editor-sessie): tekst uit de DB.
    at.session_state["editing_definition"] = None
    at.run()
    herladen = at.session_state["editing_definition"]
    w["stappen"]["editor_herladen"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "tekst_geladen": getattr(herladen, "definitie", None),
        "tekst_widget": at.text_area(key=f"edit_{did2}_definitie").value,
        "voorstellen": [
            v.get("status") for v in facade.get_definitie(did2).get_source_proposals()
        ],
        "ai_calls": ai.calls,
        "tekst": _alle_tekst(at),
    }

    # ---- deskundige correctie via echte controls ----
    from domain.sources.normalisatie import canoniseer_bronnen

    awb = next(
        b for b in canoniseer_bronnen(BRONNEN_KOPIE) if b.source_id.startswith("rag:")
    )
    for sleutel, status, citaat in (
        ("cid", "pass", "krachtens publiekrecht is ingesteld"),
        ("cid2", "fail", "met uitzondering van de rechterlijke macht"),
    ):
        rid_c = staat[sleutel]
        s_c = f"con02_{rid_c}"
        at.selectbox(key=f"{s_c}_soort").select("part_correction").run()
        at.selectbox(key=f"{s_c}_corr_onderdeel").select("semantic_support").run()
        at.selectbox(key=f"{s_c}_corr_status").select(status).run()
        at.selectbox(key=f"{s_c}_corr_bron").select(awb.source_id).run()
        at.text_area(key=f"{s_c}_corr_citaat").input(citaat)
        at.text_area(key=f"{s_c}_corr_motivering").input(
            "Deskundig oordeel over de betekenissteun."
        )
        at.checkbox(key=f"{s_c}_accepted").check()
        at.run()
        origineel_tekst = _alle_tekst(at)
        at.button(key=f"{s_c}_vastleggen").click().run()
        crec = facade.get_definitie(rid_c)
        from services.definition_workflow_service import DefinitionWorkflowService

        w["stappen"][f"correctie_{sleutel}"] = {
            "exceptions": [str(e.value) for e in at.exception],
            "origineel_zichtbaar": "Oorspronkelijk oordeel over Betekenissteun (AI)"
            in origineel_tekst,
            "review": crec.get_source_review(),
            "versie": crec.version_number,
            "tekst": _alle_tekst(at),
            "blokkades": DefinitionWorkflowService._con02_blokkades(crec),
        }
    # Stale: tekstwijziging na de correctie (cid) → correctie telt niet meer,
    # het oorspronkelijke AI-oordeel (fail) geldt weer.
    from services.definition_repository import DefinitionRepository as _SR

    bewerkt = _SR(staat["pad"]).get(staat["cid"])
    bewerkt.definitie = bewerkt.definitie + " (gewijzigd)"
    _SR(staat["pad"]).save(bewerkt)
    at.run()
    stale_rec = facade.get_definitie(staat["cid"])
    w["stappen"]["correctie_stale"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "review_status": stale_rec.get_source_review_status()["status"],
        "review_bewaard": stale_rec.get_source_review() is not None,
        "blokkades": DefinitionWorkflowService._con02_blokkades(stale_rec),
        "tekst": _alle_tekst(at),
        "ai_calls": ai.calls,
    }

    # Experttab: echte controls voor 'geen passende bron'.
    s = f"con02_{rid}"
    at.selectbox(key=f"{s}_soort").select("no_appropriate_source").run()
    w["stappen"]["expert_soort"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "widgets": sorted(
            [ta.key for ta in at.text_area]
            + [ti.key for ti in at.text_input]
            + [cb.key for cb in at.checkbox]
        ),
    }
    at.text_area(key=f"{s}_queries").input("bestuursorgaan definitie\nAwb 1:1")
    at.text_area(key=f"{s}_consulted").input("wetten.overheid.nl")
    at.text_input(key=f"{s}_conclusie").input("Geen passende bron gevonden.")
    at.text_area(key=f"{s}_motivering").input("Organisatie-eigen term.")
    at.checkbox(key=f"{s}_accepted").check()
    at.run()
    vastleg = at.button(key=f"{s}_vastleggen")
    w["stappen"]["expert_ingevuld"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "vastleggen_disabled": bool(vastleg.disabled),
    }
    vastleg.click().run()
    na = facade.get_definitie(rid)
    w["stappen"]["expert_vastgelegd"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "review": na.get_source_review(),
        "updated_by": na.updated_by,
        "versie": na.version_number,
        "tekst": _alle_tekst(at),
        "success": [str(x.value) for x in at.success],
    }

    # ---- Bevinding 1: niet-opgeslagen bewerking vs. 'Pas voorstel toe' ----
    did3 = staat["did3"]
    w3 = f"edit_{did3}_definitie"
    at.session_state["apptest_editor_id"] = did3
    at.run()
    at.checkbox(key="auto_save_enabled").uncheck().run()
    w["stappen"]["onopgeslagen_render"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "autosave": at.checkbox(key="auto_save_enabled").value,
        "tekst_widget": at.text_area(key=w3).value,
        "ai_calls": ai.calls,
        "hertoets_calls": beoordeling.calls,
    }
    at.button(key=f"edit_{did3}_vraag_voorstel").click().run()
    rec3 = facade.get_definitie(did3)
    [voorstel3] = rec3.get_source_proposals()
    pid3 = voorstel3["proposal_id"]
    knop_toepassen = f"edit_{did3}_voorstel_{pid3}_toepassen"
    knop_afwijzen = f"edit_{did3}_voorstel_{pid3}_afwijzen"
    w["stappen"]["onopgeslagen_aanvraag"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "status": voorstel3["status"],
        "kandidaat": (voorstel3.get("outcome") or {}).get("candidate_text"),
        "ai_calls": ai.calls,
        "versie_db": rec3.version_number,
        "toepassen_disabled": _knop_disabled(at, knop_toepassen),
        "tekst_widget": at.text_area(key=w3).value,
    }
    # Bewerking in het échte tekstwidget, bewust niet opgeslagen (autosave uit).
    bewerkt3 = at.text_area(key=w3).value + " (nog niet opgeslagen)"
    at.text_area(key=w3).input(bewerkt3).run()
    toepassen = at.button(key=knop_toepassen)
    w["stappen"]["onopgeslagen_bewerkt"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "toepassen_disabled": bool(toepassen.disabled),
        "toepassen_help": toepassen.help,
        "afwijzen_disabled": _knop_disabled(at, knop_afwijzen),
        "tekst_widget": at.text_area(key=w3).value,
        "tekst_db": facade.get_definitie(did3).get_definitie_tekst(),
        "versie_db": facade.get_definitie(did3).version_number,
        "ai_calls": ai.calls,
        "hertoets_calls": beoordeling.calls,
    }
    # Tegenproef: de handler rechtstreeks (alsof de knop tóch vuurde).
    at.session_state["apptest_probe_toepassen"] = {"def_id": did3, "pid": pid3}
    at.run()
    na3 = facade.get_definitie(did3)
    w["stappen"]["onopgeslagen_probe"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "resultaat": _sessiewaarde(at, f"edit_{did3}_voorstel_resultaat"),
        "pending": (f"edit_{did3}_pending_definitie" in at.session_state)
        and at.session_state[f"edit_{did3}_pending_definitie"] is not None,
        "tekst_widget": at.text_area(key=w3).value,
        "tekst_db": na3.get_definitie_tekst(),
        "versie_db": na3.version_number,
        "voorstel_status": na3.get_source_proposal(pid3)["status"],
        "ai_calls": ai.calls,
        "hertoets_calls": beoordeling.calls,
        "toepassen_disabled": _knop_disabled(at, knop_toepassen),
        "tekst": _alle_tekst(at),
    }
    # De gebruiker slaat de bewerking op: het origineel van het voorstel is
    # daarmee verouderd — toepassen mag dan alleen nog door D's guard worden
    # geweigerd (`stale_original`), nooit stilzwijgend doorgaan.
    at.button(key="save_btn").click().run()
    opgeslagen3 = facade.get_definitie(did3)
    geladen3 = at.session_state["editing_definition"]
    w["stappen"]["onopgeslagen_opgeslagen"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "tekst_db": opgeslagen3.get_definitie_tekst(),
        "versie_db": opgeslagen3.version_number,
        "tekst_geladen": getattr(geladen3, "definitie", None),
        "versie_geladen": (getattr(geladen3, "metadata", None) or {}).get(
            "version_number"
        ),
        "tekst_widget": at.text_area(key=w3).value,
        "toepassen_aanwezig": any(b.key == knop_toepassen for b in at.button),
        "toepassen_disabled": _knop_disabled(at, knop_toepassen),
        "voorstel_status": opgeslagen3.get_source_proposal(pid3)["status"],
    }
    if _knop_disabled(at, knop_toepassen) is not None:
        at.button(key=knop_toepassen).click().run()
    na_apply3 = facade.get_definitie(did3)
    w["stappen"]["onopgeslagen_apply_na_opslaan"] = {
        "exceptions": [str(e.value) for e in at.exception],
        "resultaat": _sessiewaarde(at, f"edit_{did3}_voorstel_resultaat"),
        "tekst_db": na_apply3.get_definitie_tekst(),
        "tekst_widget": at.text_area(key=w3).value,
        "voorstel_status": na_apply3.get_source_proposal(pid3)["status"],
        "ai_calls": ai.calls,
        "tekst": _alle_tekst(at),
    }
    Path(uit_pad).write_text(
        json.dumps(w, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ------------------------------------------------------------------ pytest


@pytest.fixture(scope="module")
def w(tmp_path_factory) -> dict:
    uit = tmp_path_factory.mktemp("def743-editor-apptest") / "waarnemingen.json"
    proces = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--driver", str(uit)],
        cwd=str(REPO),
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert proces.returncode == 0, proces.stderr[-8000:]
    return json.loads(uit.read_text(encoding="utf-8"))


def test_driver_draait_achter_de_gate_zonder_ui_excepties(w):
    assert w["gate_actief"] is True
    for naam, stap in w["stappen"].items():
        assert stap.get("exceptions", []) == [], (naam, stap.get("exceptions"))


def test_weergave_toont_geen_cijfer_maar_dekking_en_bronbasis(w):
    tekst = w["stappen"]["render"]["tekst"]
    assert "Overall Score" not in tekst and "0.82" not in tekst and "%" not in tekst
    assert "Beoordelingsdekking" in tekst and "3 regels" in tekst
    assert "1 technisch probleem" in tekst
    # Bronbasis: kwitantie, per-bron-bewijs, citaat, uitzondering als uitzondering (verouderd).
    assert "Brontransport (kwitantie)" in tekst
    assert "Bron-id: rag:doc-awb:chunk-awb-1-1" in tekst
    assert "Geverifieerd citaat" in tekst
    assert "Verwijzingsuitzondering" in tekst and "VEROUDERD" in tekst
    assert "geen positieve bronbeoordeling" in tekst
    assert "geselecteerd maar NIET in de prompt" in tekst


def test_voorstelknop_bestaat_en_doet_zonder_klik_niets(w):
    render = w["stappen"]["render"]
    assert f"edit_{_did(w)}_vraag_voorstel" in render["knoppen"]
    assert render["ai_calls"] == 0
    assert render["voorstellen"] == 0
    assert any("Verbetervoorstel op verzoek" in e for e in render["expanders"])
    assert any("Bronbasis (CON-02)" in e for e in render["expanders"])


def _did(w) -> int:
    for key in w["stappen"]["render"]["knoppen"]:
        if key.endswith("_vraag_voorstel"):
            return int(key.split("_")[1])
    raise AssertionError(w["stappen"]["render"]["knoppen"])


def test_klik_doet_een_aanroep_en_toont_voorstel_apart(w):
    klik1 = w["stappen"]["klik1"]
    assert klik1["ai_calls"] == 1
    assert klik1["voorstellen"] == [{"status": "proposed", "outcome": "proposed"}]
    assert klik1["tekst_db"] == w["stappen"]["render"]["tekst_db"]  # origineel staat
    assert "Voorgestelde tekst" in klik1["tekst"]
    assert "Oorspronkelijke tekst (bewaard)" in klik1["tekst"]
    did = _did(w)
    assert any(
        k.startswith(f"edit_{did}_voorstel_") and k.endswith("_toepassen")
        for k in klik1["knoppen"]
    )
    assert any(
        k.startswith(f"edit_{did}_voorstel_") and k.endswith("_afwijzen")
        for k in klik1["knoppen"]
    )


def test_tweede_klik_doet_geen_tweede_aanroep(w):
    klik2 = w["stappen"]["klik2"]
    assert klik2["ai_calls"] == 1
    assert klik2["voorstellen"] == 1
    assert klik2["resultaat_status"] == "attempt_consumed"
    assert "Geen voorstel" in klik2["tekst"]


def test_experttab_controls_schrijven_platte_uitzondering(w):
    soort = w["stappen"]["expert_soort"]
    assert any(k.endswith("_queries") for k in soort["widgets"])
    assert any(k.endswith("_accepted") for k in soort["widgets"])
    assert w["stappen"]["expert_ingevuld"]["vastleggen_disabled"] is False
    vast = w["stappen"]["expert_vastgelegd"]
    review = vast["review"]
    assert review is not None, vast["tekst"][-3000:]
    assert review["type"] == "no_appropriate_source"
    assert review["accepted"] is True
    assert review["actor"] == ACTOR and vast["updated_by"] == ACTOR
    assert review["search"]["queries"] == ["bestuursorgaan definitie", "Awb 1:1"]
    assert "exceptions" not in review
    assert vast["versie"] == 2
    assert (
        "Geaccepteerde deskundige uitzondering wegens onderbouwd ontbreken"
        in vast["tekst"]
    )
    # De uitzondering zelf verschijnt nooit als groene 'Voldoet'-melding.
    assert not any(
        "uitzondering" in s.lower() and "Voldoet" in s for s in vast["success"]
    )
    assert "Dit is een uitzondering, geen 'voldoet'" in vast["tekst"]


def _expander_met(w, fragment: str) -> list[str]:
    return [t for t in w["stappen"]["render"]["expander_teksten"] if fragment in t]


def test_f6_kwitantie_toont_wat_de_beoordeling_zag_afgekapt_naast_de_volledige_bron(w):
    """F6/C5 met echte widgets: lange bron (> 300) + kwitantie op cap 300 —
    "Wat de beoordeling zag" is de exact verzonden (afgekapte) passage; de
    volledige aangeleverde/canonieke passage blijft apart leesbaar; het
    bron-id is dat van de Awb-chunk."""
    lang = w["stappen"]["render"]["lang_passage"]
    assert len(lang) > 300
    blokken = _expander_met(w, "afgekapt: 300 van")
    assert blokken, w["stappen"]["render"]["expander_teksten"][:20]
    (blok,) = [b for b in blokken if "Bron-id: rag:doc-awb:chunk-awb-1-1" in b]
    assert "Wat de beoordeling zag" in blok
    assert f"afgekapt: 300 van {len(lang)} tekens" in blok
    assert lang[:300] in blok  # exact de verzonden inhoud
    assert "Canonieke opgeslagen passage = de aangeleverde passage hierboven." in blok
    # De volledige passage staat in de aparte 'Volledige passage'-expander.
    # (`st.text` levert de tekst zonder omliggende witruimte terug.)
    assert any(lang.strip() in t for t in w["stappen"]["render"]["expander_teksten"])
    assert w["stappen"]["render"]["exceptions"] == []


def test_f6_historische_beoordeling_zonder_kwitantie_claimt_geen_modelinvoer(w):
    """Het oudere record (assessment zonder `assessment_receipt`): de
    modelinvoer is onbekend en wordt niet verzonnen; de opgeslagen passage
    blijft leesbaar."""
    blokken = [
        t
        for t in w["stappen"]["render"]["expander_teksten"]
        if "Bron-id: rag:doc-awb:chunk-awb-1-1" in t and "afgekapt: 300" not in t
    ]
    assert blokken
    assert all("Wat de beoordeling zag: onbekend" in b for b in blokken)
    assert all("gebonden beoordelingskwitantie" not in b for b in blokken)


def test_f5_root_probe_gelijke_bronnen_a_en_b_via_echte_ui(w):
    """Twee bronnen die alleen in `source_id` verschillen: rij A toont id A
    zonder het B-bewijs; rij B toont id B mét het bewijs."""
    a = [t for t in w["stappen"]["render"]["expander_teksten"] if "Bron-id: A ·" in t]
    b = [t for t in w["stappen"]["render"]["expander_teksten"] if "Bron-id: B ·" in t]
    assert len(a) == 1 and len(b) == 1
    assert "Geverifieerd citaat" not in a[0]
    assert "Geverifieerd citaat" in b[0] and "Gelijke passage" in b[0]


def test_f2_apply_in_volledige_editor_zonder_exceptie_en_herladen(w):
    """F2: Apply in de volledige editor (tekstwidget al gebouwd) crasht niet; de
    DB, het widget, de hertoetsing en de historie kloppen; herladen van
    hetzelfde ID toont de nieuwe tekst."""
    render = w["stappen"]["editor_render"]
    assert render["exceptions"] == []
    aanvraag = w["stappen"]["editor_aanvraag"]
    assert aanvraag["exceptions"] == [] and aanvraag["status"] == "proposed"
    assert aanvraag["tekst_widget"] == render["tekst_widget"]  # origineel staat nog
    apply = w["stappen"]["editor_apply"]
    assert apply["exceptions"] == [], apply["exceptions"]
    assert apply["resultaat_status"] == "applied", apply["resultaat_message"]
    assert apply["tekst_db"] == aanvraag["kandidaat"]
    assert apply["tekst_widget"] == aanvraag["kandidaat"]  # widget volgt de DB
    assert apply["voorstel_status"] == "applied"
    assert (
        apply["historie_origineel"][-1] == render["tekst_widget"]
    )  # origineel bewaard
    assert apply["bewijs_origin"] == "proposal_applied"
    assert apply["validatie_con02"] == "pass"  # hertoetsing is het actuele resultaat
    assert apply["hertoets_calls"] == render["hertoets_calls"] + 1
    assert apply["hertoets_bronnen_gelijk"] is True  # DEZELFDE bronset
    assert apply["ai_calls"] == aanvraag["ai_calls"]  # toepassen = geen modelaanroep
    assert "Voorstel toegepast" in apply["tekst"]
    herladen = w["stappen"]["editor_herladen"]
    assert herladen["exceptions"] == []
    assert herladen["tekst_geladen"] == aanvraag["kandidaat"]
    assert herladen["tekst_widget"] == aanvraag["kandidaat"]
    assert herladen["voorstellen"] == ["applied"]
    assert herladen["ai_calls"] == apply["ai_calls"]  # herladen doet geen aanroep


def test_correctie_beide_richtingen_via_echte_controls_en_stale(w):
    """C §6b via de experttab: correctie naar pass (gate open, AI-oordeel
    bewaard) en naar fail (gate dicht), zonder UI-excepties; na een
    tekstwijziging telt de correctie niet meer en blijft ze bewaard."""
    c1 = w["stappen"]["correctie_cid"]
    assert c1["exceptions"] == [] and c1["origineel_zichtbaar"] is True
    assert c1["review"]["type"] == "part_correction"
    assert (
        c1["review"]["part_id"] == "semantic_support"
        and c1["review"]["status"] == "pass"
    )
    assert c1["review"]["evidence"][0]["content_hash"]
    assert c1["review"]["actor"] == ACTOR and "exceptions" not in c1["review"]
    assert c1["blokkades"] == []
    assert "Deskundige correctie van betekenissteun" in c1["tekst"]
    assert "Oorspronkelijk AI-oordeel: ❌ Voldoet niet" in c1["tekst"]
    c2 = w["stappen"]["correctie_cid2"]
    assert c2["exceptions"] == []
    assert c2["review"]["status"] == "fail"
    assert any("CON-02 Voldoet niet" in b for b in c2["blokkades"])
    stale = w["stappen"]["correctie_stale"]
    assert stale["exceptions"] == []
    assert stale["review_status"] == "stale" and stale["review_bewaard"] is True
    assert any("niet toegepast" in b for b in stale["blokkades"])
    assert "niet toegepast" in stale["tekst"]
    assert stale["ai_calls"] == w["stappen"]["editor_apply"]["ai_calls"]


def test_bevinding1_onopgeslagen_bewerking_blokkeert_toepassen_in_volledige_editor(w):
    """Bevinding 1 (vervolgreview) met echte widgets, autosave uit: na een
    voorstel wordt de tekst bewerkt zonder opslaan → 'Pas voorstel toe' staat
    uit met Sla-eerst-uitleg; de handler rechtstreeks aanroepen verandert
    widget, DB, versie en voorstelstatus niet (geen hertoetsing, geen model);
    na Opslaan door de gebruiker weigert D's guard het verouderde origineel."""
    render = w["stappen"]["onopgeslagen_render"]
    assert render["exceptions"] == [] and render["autosave"] is False
    aanvraag = w["stappen"]["onopgeslagen_aanvraag"]
    assert aanvraag["exceptions"] == [] and aanvraag["status"] == "proposed"
    assert aanvraag["ai_calls"] == render["ai_calls"] + 1
    assert aanvraag["toepassen_disabled"] is False  # zonder bewerking: beschikbaar
    bewerkt = w["stappen"]["onopgeslagen_bewerkt"]
    assert bewerkt["exceptions"] == []
    assert bewerkt["tekst_widget"].endswith("(nog niet opgeslagen)")
    assert bewerkt["tekst_db"] == aanvraag["tekst_widget"]  # niet opgeslagen
    assert bewerkt["versie_db"] == aanvraag["versie_db"]
    assert bewerkt["toepassen_disabled"] is True
    assert "Sla eerst je bewerking op" in (bewerkt["toepassen_help"] or "")
    assert bewerkt["afwijzen_disabled"] is False
    probe = w["stappen"]["onopgeslagen_probe"]
    assert probe["exceptions"] == []
    assert probe["resultaat"].get("status") == "unsaved_changes"
    assert probe["pending"] is False
    assert probe["tekst_widget"] == bewerkt["tekst_widget"]  # widget onaangeroerd
    assert probe["tekst_db"] == bewerkt["tekst_db"]
    assert probe["versie_db"] == bewerkt["versie_db"]
    assert probe["voorstel_status"] == "proposed"
    assert probe["hertoets_calls"] == bewerkt["hertoets_calls"]  # geen hertoetsing
    assert probe["ai_calls"] == bewerkt["ai_calls"]  # geen modelaanroep
    assert probe["toepassen_disabled"] is True
    assert "Sla eerst je bewerking op" in probe["tekst"]
    opgeslagen = w["stappen"]["onopgeslagen_opgeslagen"]
    assert opgeslagen["exceptions"] == []
    assert opgeslagen["tekst_db"] == bewerkt["tekst_widget"]  # de bewerking staat
    assert opgeslagen["versie_db"] > bewerkt["versie_db"]
    assert opgeslagen["tekst_geladen"] == opgeslagen["tekst_db"]
    assert opgeslagen["versie_geladen"] == opgeslagen["versie_db"]
    assert opgeslagen["voorstel_status"] == "proposed"
    assert opgeslagen["toepassen_aanwezig"] is True
    assert opgeslagen["toepassen_disabled"] is False  # opgeslagen: weer klikbaar
    na = w["stappen"]["onopgeslagen_apply_na_opslaan"]
    assert na["exceptions"] == []
    assert na["resultaat"].get("status") == "stale_original", na["resultaat"]
    assert na["tekst_db"] == opgeslagen["tekst_db"]  # bewerking blijft staan
    assert na["tekst_widget"] == opgeslagen["tekst_db"]
    assert na["voorstel_status"] == "proposed"
    assert na["ai_calls"] == probe["ai_calls"]


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--driver":
        _driver(sys.argv[2])
    else:  # pragma: no cover - alleen als driver bedoeld
        raise SystemExit("gebruik: --driver <uitvoer.json>")
