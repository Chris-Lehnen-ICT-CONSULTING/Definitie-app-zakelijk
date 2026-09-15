"""DEF-743 pakket F — editorpariteit: sync-service en async-UI toetsen dezelfde kandidaat.

Bewezen zonder model, netwerk of productie-DB:

* `bouw_validatiecontext` vervoert de ACTUELE bewerkte tekst/term/drie
  contextlijsten (ook leeg, expliciet) plus id, recordversie, CON-01-beoordeling,
  CON-02-uitzondering, peildatum en — als deep copy — dezelfde bronset als het
  ID-only geladen record; nooit een `source_assessment` (de actieve wrapper
  beoordeelt zelf; een UI kan geen oude pass laten gelden).
* `normaliseer_validatieresultaat` bewaart status, onderdelen, bewijs, open en
  technische onderdelen, dekking en de volledige bronbeoordeling; een ontbrekend
  cijfer blijft None (geen 0.0, geen positief cijfer).
* Sync pad (`DefinitionEditService._validate_definition`) en async pad
  (`DefinitionEditTab._validate_definition` via de echte
  `ValidationOrchestratorV2` + echte `ModularValidationService`) geven voor
  pass / fail+open / error / stale dezelfde CON-02-uitkomst, gebonden aan
  dezelfde bronvingerafdruk, en de beoordelingsdienst kreeg precies de bronset
  van het geladen record.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
import streamlit as st

from database.definitie_repository import DefinitieRepository
from domain.sources.contract import bereken_bronvingerafdruk
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import (
    DefinitionEditService,
    bouw_validatiecontext,
    normaliseer_validatieresultaat,
)
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from tests.fixtures.def743_fakes import (
    BEGRIP,
    BRONNEN,
    JUR,
    ORG,
    TEKST,
    WET,
    FakeBronbeoordeling,
    bouw_beoordeling,
)
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

ACTOR = "synthetische-expert"


# ------------------------------------------------------------------ helpers


def _echte_validatie(beoordeling: FakeBronbeoordeling | None):
    from services.null_repository import NullDefinitionRepository
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from toetsregels.manager import get_toetsregel_manager

    return ValidationOrchestratorV2(
        ModularValidationService(
            toetsregel_manager=get_toetsregel_manager(),
            repository=NullDefinitionRepository(),
        ),
        source_assessment_service=beoordeling,
    )


class _SyncAdapter:
    """Sync `validate_text` op de echte async orchestrator (het sync-servicepad)."""

    def __init__(self, orchestrator: Any) -> None:
        self._orch = orchestrator

    def validate_text(self, **kwargs: Any) -> dict[str, Any]:
        from services.validation.interfaces import ValidationContext

        ctx = kwargs.pop("context")
        return asyncio.run(
            self._orch.validate_text(
                **kwargs, context=ValidationContext(correlation_id=None, metadata=ctx)
            )
        )


def _definition(**overrides: Any) -> Definition:
    metadata: dict[str, Any] = {
        "status": "draft",
        "created_by": "generator",
        "sources": deepcopy(BRONNEN),
        "provenance_sources": deepcopy(BRONNEN),
        "source_assessment": bouw_beoordeling(
            BEGRIP,
            TEKST,
            {
                "organisatorische_context": ORG,
                "juridische_context": JUR,
                "wettelijke_basis": WET,
            },
            BRONNEN,
            scenario="fail",
        ),
        "definitie_origineel": TEKST,
        "definitie_eindtekst": TEKST,
        "peildatum": "2026-09-15",
    }
    metadata.update(overrides.pop("metadata", {}))
    velden: dict[str, Any] = {
        "begrip": BEGRIP,
        "definitie": TEKST,
        "categorie": "type",
        "organisatorische_context": list(ORG),
        "juridische_context": list(JUR),
        "wettelijke_basis": list(WET),
        "metadata": metadata,
    }
    velden.update(overrides)
    return Definition(**velden)


@pytest.fixture
def repo(tmp_path) -> DefinitionEditRepository:
    return DefinitionEditRepository(str(tmp_path / "pariteit.db"))


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    return st.session_state


# ------------------------------------------------ bouw_validatiecontext


def test_context_vervoert_bewerkte_kandidaat_en_recordbronnen_zonder_beoordeling():
    geladen = {
        "version_number": 4,
        "context_review": {"actor": ACTOR, "version_number": 2},
        "source_review": {"type": "no_appropriate_source", "accepted": True},
        "peildatum": "2026-09-15",
        "provenance_sources": deepcopy(BRONNEN),
        "sources": [{"provider": "rag", "snippet": "andere lijst"}],
        "source_assessment": {"status": "assessed", "fingerprint": "oud-positief"},
    }
    bewerkt = Definition(
        id=7,
        begrip="bestuursorganen",
        definitie=TEKST + " (bewerkt)",
        organisatorische_context=[],
        juridische_context=["strafrecht"],
        wettelijke_basis=None,
    )
    ctx = bouw_validatiecontext(bewerkt, geladen)

    # De bewerkte lijsten zijn gezaghebbend en gaan ook leeg expliciet mee.
    assert ctx["organisatorische_context"] == []
    assert ctx["juridische_context"] == ["strafrecht"]
    assert ctx["wettelijke_basis"] == []
    assert ctx["record_text"] == TEKST + " (bewerkt)"
    assert ctx["definition_id"] == 7
    assert ctx["definition_version"] == 4
    assert ctx["context_review"] == geladen["context_review"]
    assert ctx["source_review"] == geladen["source_review"]
    assert ctx["peildatum"] == "2026-09-15"
    # Dezelfde bronset als het geladen record (canonieke sleutel wint), deep copy.
    assert ctx["provenance_sources"] == BRONNEN
    ctx["provenance_sources"][0]["snippet"] = "GEMUTEERD"
    assert geladen["provenance_sources"][0]["snippet"] != "GEMUTEERD"
    # Nooit een oude beoordeling als kortere weg naar een positief oordeel.
    assert "source_assessment" not in ctx


def test_context_valt_terug_op_sources_en_verzint_geen_bronnen():
    ctx = bouw_validatiecontext(
        Definition(id=1, begrip="x", definitie="y"),
        {"sources": [{"snippet": "s"}]},
    )
    assert ctx["provenance_sources"] == [{"snippet": "s"}]
    assert "provenance_sources" not in bouw_validatiecontext(
        Definition(id=1, begrip="x", definitie="y"), {}
    )
    assert "provenance_sources" not in bouw_validatiecontext(
        Definition(id=1, begrip="x", definitie="y"), None
    )


# ------------------------------------------- normaliseer_validatieresultaat


def test_normalisatie_bewaart_status_delen_bewijs_dekking_en_geen_nul():
    v2 = {
        "is_acceptable": False,
        "violations": [{"rule_id": "ESS-01", "description": "x", "severity": "high"}],
        "rule_results": {
            "CON-02": {
                "status": "fail",
                "score": None,
                "fingerprint": "fp",
                "parts": [
                    {"id": "semantic_support", "status": "fail", "evidence": "citaat"}
                ],
                "review": {"applied": False, "accepted_exception": None},
            }
        },
        "rule_statuses": {"CON-02": "fail", "ESS-01": "fail", "VER-01": "error"},
        "evaluation_coverage": {"total": 3, "passed": 0, "failed": 2, "error": 1},
        "review_required": [{"rule_id": "CON-02"}],
        "validation_status": "validated",
        "validation_readiness": {"ready": True},
        "source_assessment": {"status": "assessed", "fingerprint": "fp"},
    }
    uit = normaliseer_validatieresultaat(v2)
    assert uit["valid"] is False
    assert uit["score"] is None  # sleutel ontbreekt: geen 0.0
    assert uit["rule_results"]["CON-02"]["parts"][0]["evidence"] == "citaat"
    assert uit["rule_statuses"]["VER-01"] == "error"
    assert uit["evaluation_coverage"]["error"] == 1
    assert uit["review_required"] == [{"rule_id": "CON-02"}]
    assert uit["validation_status"] == "validated"
    assert uit["source_assessment"]["fingerprint"] == "fp"
    assert uit["issues"] == [{"rule": "ESS-01", "message": "x", "severity": "high"}]
    assert uit["raw_v2"] is not v2 and uit["raw_v2"] == v2
    # Deep copies: latere mutatie van het resultaat raakt de invoer niet.
    uit["rule_results"]["CON-02"]["status"] = "pass"
    assert v2["rule_results"]["CON-02"]["status"] == "fail"


@pytest.mark.parametrize("score", [None, "nvt"])
def test_normalisatie_geeft_geen_cijfer_bij_none_of_onleesbaar(score):
    uit = normaliseer_validatieresultaat(
        {"overall_score": score, "is_acceptable": True}
    )
    assert uit["score"] is None
    assert uit["valid"] is True


def test_normalisatie_neemt_geen_positief_oordeel_aan_zonder_sleutel():
    assert normaliseer_validatieresultaat({})["valid"] is False


# --------------------------------------------------- sync ↔ async pariteit


def _sla_op(repo: DefinitionEditRepository, **overrides: Any) -> Definition:
    did = repo.save(_definition(**overrides))
    geladen = DefinitionRepository(repo.db_path).get(did)
    assert geladen is not None
    return geladen


def _vul_editor(geladen: Definition, tekst: str | None = None) -> None:
    SessionStateManager.set_value("editing_definition_id", geladen.id)
    SessionStateManager.set_value("editing_definition", geladen)
    for veld, waarde in (
        ("begrip", geladen.begrip),
        ("definitie", tekst if tekst is not None else geladen.definitie),
        ("organisatorische_context", list(geladen.organisatorische_context or [])),
        ("juridische_context", list(geladen.juridische_context or [])),
        ("wettelijke_basis", list(geladen.wettelijke_basis or [])),
        ("categorie", "type"),
        ("toelichting", ""),
        ("status", "draft"),
    ):
        SessionStateManager.set_value(f"edit_{geladen.id}_{veld}", waarde)


def _async_pad(geladen: Definition, orchestrator: Any) -> dict[str, Any]:
    from ui.components.definition_edit_tab import DefinitionEditTab

    container = SimpleNamespace(
        orchestrator=lambda: SimpleNamespace(validation_service=orchestrator)
    )
    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.edit_service = SimpleNamespace(_validate_definition=lambda _d, _m: None)
    with patch(
        "ui.cached_services.get_cached_service_container", return_value=container
    ):
        resultaat: Any = tab._validate_definition()
    assert resultaat is not None
    return resultaat


def _sync_pad(
    repo: DefinitionEditRepository,
    geladen: Definition,
    orchestrator: Any,
    tekst: str | None = None,
) -> dict[str, Any]:
    service = DefinitionEditService(
        repository=repo, validation_service=_SyncAdapter(orchestrator)
    )
    bewerkt = Definition(
        id=geladen.id,
        begrip=geladen.begrip,
        definitie=tekst if tekst is not None else geladen.definitie,
        organisatorische_context=list(geladen.organisatorische_context or []),
        juridische_context=list(geladen.juridische_context or []),
        wettelijke_basis=list(geladen.wettelijke_basis or []),
        categorie="type",
        metadata={"status": "draft"},
    )
    resultaat = service._validate_definition(bewerkt, dict(geladen.metadata or {}))
    assert resultaat is not None
    return resultaat


def _con02(resultaat: dict[str, Any]) -> dict[str, Any]:
    return resultaat["raw_v2"]["rule_results"]["CON-02"]


@pytest.mark.parametrize(
    ("scenario", "verwacht"),
    [
        ("pass", "pass"),
        ("fail", "fail"),
        ("open", "review_required"),
        ("error", "error"),
    ],
)
def test_sync_en_async_geven_dezelfde_con02_uitkomst(repo, sessie, scenario, verwacht):
    geladen = _sla_op(repo)
    _vul_editor(geladen)

    b_async = FakeBronbeoordeling(scenario)
    b_sync = FakeBronbeoordeling(scenario)
    r_async = _async_pad(geladen, _echte_validatie(b_async))
    r_sync = _sync_pad(repo, geladen, _echte_validatie(b_sync))

    verwachte_vingerafdruk = bereken_bronvingerafdruk(
        BEGRIP,
        TEKST,
        {
            "organisatorische_context": ORG,
            "juridische_context": JUR,
            "wettelijke_basis": WET,
        },
        BRONNEN,
        peildatum="2026-09-15",
    )
    for resultaat in (r_async, r_sync):
        con02 = _con02(resultaat)
        assert con02["status"] == verwacht, con02
        assert con02["fingerprint"] == verwachte_vingerafdruk
        assert resultaat["score"] is None  # no_score-regel in de set
        assert resultaat["raw_v2"]["source_assessment"]["fingerprint"] == (
            verwachte_vingerafdruk
        )
        assert resultaat["evaluation_coverage"]["total"] > 0
    # Pariteit: identieke onderdelen, statussen en bewijs.
    assert _con02(r_async)["parts"] == _con02(r_sync)["parts"]
    assert r_async["rule_statuses"] == r_sync["rule_statuses"]
    assert r_async["evaluation_coverage"] == r_sync["evaluation_coverage"]
    # Beide paden gaven de beoordelingsdienst exact de bronset van het record.
    assert b_async.calls == 1 and b_sync.calls == 1
    assert b_async.laatste_bronnen == BRONNEN
    assert b_sync.laatste_bronnen == BRONNEN
    if scenario == "fail":
        delen = {p["id"]: p for p in _con02(r_async)["parts"]}
        assert delen["semantic_support"]["status"] == "fail"
        assert delen["semantic_support"]["field"] == "source_assessment"
        assert delen["semantic_support"]["evidence"]  # geverifieerd citaat
        assert delen["source_authority"]["status"] == "pass"
    if scenario == "error":
        assert all(p["status"] == "error" for p in _con02(r_async)["parts"])


def test_oude_positieve_beoordeling_in_het_record_telt_niet_voor_bewerkte_tekst(
    repo, sessie
):
    """Stale: het record draagt een pass-beoordeling; de bewerkte tekst krijgt een
    verse beoordeling (fail) — de oude pass reist niet mee als kortere weg."""
    contexten = {
        "organisatorische_context": ORG,
        "juridische_context": JUR,
        "wettelijke_basis": WET,
    }
    geladen = _sla_op(
        repo,
        metadata={
            "source_assessment": bouw_beoordeling(
                BEGRIP,
                TEKST,
                contexten,
                BRONNEN,
                scenario="pass",
                peildatum="2026-09-15",
            )
        },
    )
    nieuw = TEKST + " of een ander persoon met openbaar gezag"
    _vul_editor(geladen, tekst=nieuw)
    b = FakeBronbeoordeling("fail")
    r_async = _async_pad(geladen, _echte_validatie(b))
    r_sync = _sync_pad(
        repo, geladen, _echte_validatie(FakeBronbeoordeling("fail")), tekst=nieuw
    )
    for r in (r_async, r_sync):
        assert _con02(r)["status"] == "fail"
        assert (
            _con02(r)["fingerprint"]
            != geladen.metadata["source_assessment"]["fingerprint"]
        )
    assert b.laatste_tekst == nieuw


def test_verouderde_uitzondering_wordt_benoemd_niet_stil_genegeerd(repo, sessie):
    """Stale review: een vastgelegde uitzondering voor de opgeslagen tekst geldt
    niet voor de bewerkte tekst; beide paden melden dat expliciet."""
    contexten = {
        "organisatorische_context": ORG,
        "juridische_context": JUR,
        "wettelijke_basis": WET,
    }
    geladen = _sla_op(repo, metadata={"provenance_sources": [], "sources": []})
    facade = DefinitieRepository(repo.db_path)
    rec = facade.get_definitie(geladen.id)
    vingerafdruk = bereken_bronvingerafdruk(
        BEGRIP, TEKST, contexten, [], peildatum="2026-09-15"
    )
    assert facade.set_source_review(
        rec.id,
        {
            "type": "no_appropriate_source",
            "accepted": True,
            "actor": ACTOR,
            "rationale": "Organisatie-eigen term zonder authentieke bron.",
            "version_number": rec.version_number,
            "fingerprint": vingerafdruk,
            "search": {
                "queries": ["bestuursorgaan definitie"],
                "consulted": ["wetten.overheid.nl"],
                "conclusion": "Geen passende bron gevonden.",
            },
        },
        updated_by=ACTOR,
        expected_version=rec.version_number,
    )
    geladen = DefinitionRepository(repo.db_path).get(rec.id)
    assert geladen.metadata["source_review"]["type"] == "no_appropriate_source"

    # Ongewijzigde tekst: uitzondering zichtbaar als uitzondering (geen pass).
    _vul_editor(geladen)
    r = _async_pad(geladen, _echte_validatie(FakeBronbeoordeling("pass")))
    con02 = _con02(r)
    assert con02["status"] == "review_required"
    assert con02["review"]["applied"] is True
    assert con02["review"]["accepted_exception"] == "no_source"
    assert any(p["id"] == "expert_exception:no_source" for p in con02["parts"])

    # Bewerkte tekst: de uitzondering vervalt en dat wordt benoemd.
    _vul_editor(geladen, tekst=TEKST + " (gewijzigd)")
    r2 = _async_pad(geladen, _echte_validatie(FakeBronbeoordeling("pass")))
    r3 = _sync_pad(
        repo,
        geladen,
        _echte_validatie(FakeBronbeoordeling("pass")),
        tekst=TEKST + " (gewijzigd)",
    )
    for r in (r2, r3):
        assert _con02(r)["review"]["applied"] is False
        assert "gewijzigd" in _con02(r)["review"]["reason"]
        assert _con02(r)["review"]["accepted_exception"] is None
