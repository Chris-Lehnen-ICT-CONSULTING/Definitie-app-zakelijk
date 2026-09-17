"""DEF-808/DEF-809 — UI-gedrag van editor en upload met gemockte `st`
(patroon test_def743_editor_ui): echte servicelaag, echte tijdelijke SQLite.

* DEF-809: "Opslaan" in de editor geeft de bronbeoordeling uit de laatste
  toetsing (`edit_last_validation`) door aan de servicelaag; na opslaan draagt
  het record de nieuwe beoordeling en de actuele kandidaat. Een beoordeling die
  niet bij de op te slaan tekst hoort wordt niet opgeslagen en dat wordt
  zichtbaar gemeld — geen stil verlies, geen oude pass.
* DEF-808 (aanvulroute): het bronmetadata-formulier in de editor schrijft via
  de servicelaag naar het bestaande record; ongeldige invoer wordt zichtbaar
  afgewezen zonder te schrijven; zonder reviewer-identiteit is de knop
  uitgeschakeld.
* DEF-808 (uploadroute): het formulier bij een geüpload document legt de
  opgave vast bij de documentprocessor en wijst ongeldige invoer af.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from database.definitie_repository import DefinitieRepository
from document_processing.document_processor import DocumentProcessor
from domain.sources.bronmetadata import DECLARED_METADATA_KEY
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import (
    DefinitionEditService,
    normaliseer_validatieresultaat,
)
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from tests.fixtures.def808_p01 import (
    BEGRIP,
    DOC_ID,
    DOCUMENTBRONNEN,
    GEGENEREERDE_TEKST,
    JUR,
    P01_TEKST,
    P01_URL,
    P01_VERSIE,
    P01_VINDPLAATS,
    WET,
    bouw_documentbeoordeling,
)
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

ACTOR = "Reviewer Rood"


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
            if kw.get("disabled") and default is False:
                return False
            if sleutel in antwoorden:
                return antwoorden[sleutel]
            if default == "eerste_optie":
                opties = kw.get("options") or (args[1] if len(args) > 1 else None)
                return opties[0] if opties else None
            if default == "" and sleutel is not None:
                # Key-only widgets lezen hun waarde uit de sessie.
                waarde = SessionStateManager.get_value(sleutel)
                return waarde if isinstance(waarde, str) else ""
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
    m.expander.return_value.__enter__.return_value = None
    return m


def _record(tekst: str = GEGENEREERDE_TEKST, **meta: Any) -> Definition:
    metadata: dict[str, Any] = {
        "status": "draft",
        "created_by": "generator",
        "sources": deepcopy(DOCUMENTBRONNEN),
        "provenance_sources": deepcopy(DOCUMENTBRONNEN),
        "source_assessment": bouw_documentbeoordeling(
            tekst, DOCUMENTBRONNEN, assessed_at="2026-09-17T14:43:02+00:00"
        ),
        "generation_id": "d96266b8-5a44-4578-89b2-f54258f51c7c",
    }
    metadata.update(meta)
    return Definition(
        begrip=BEGRIP,
        definitie=tekst,
        categorie="resultaat",
        organisatorische_context=[],
        juridische_context=list(JUR),
        wettelijke_basis=list(WET),
        metadata=metadata,
    )


def _facade(repo) -> DefinitieRepository:
    return DefinitieRepository(repo.db_path)


def _herladen(repo, did: int) -> Definition:
    geladen = DefinitionRepository(repo.db_path).get(did)
    assert geladen is not None
    return geladen


def _tab(repo):
    from ui.components.definition_edit_tab import DefinitionEditTab

    tab = DefinitionEditTab.__new__(DefinitionEditTab)
    tab.repository = repo
    tab.edit_service = DefinitionEditService(repository=repo, validation_service=None)
    return tab


def _vul_editor(geladen: Definition, *, tekst: str, status: str) -> None:
    SessionStateManager.set_value("editing_definition_id", geladen.id)
    SessionStateManager.set_value("editing_definition", geladen)
    for veld, waarde in (
        ("begrip", geladen.begrip),
        ("definitie", tekst),
        ("organisatorische_context", list(geladen.organisatorische_context or [])),
        ("juridische_context", list(geladen.juridische_context or [])),
        ("wettelijke_basis", list(geladen.wettelijke_basis or [])),
        ("categorie", "resultaat"),
        ("ufo_categorie", ""),
        ("toelichting", ""),
        ("status", status),
        ("save_reason", ""),
    ):
        SessionStateManager.set_value(f"edit_{geladen.id}_{veld}", waarde)


def _sessieresultaat(beoordeling: dict[str, Any]) -> dict[str, Any]:
    """Wat "Valideren" in `edit_last_validation` achterlaat (genormaliseerd V2)."""
    return normaliseer_validatieresultaat(
        {
            "validation_status": "validated",
            "is_acceptable": False,
            "violations": [],
            "rule_results": {},
            "rule_statuses": {"CON-02": "review_required"},
            "source_assessment": beoordeling,
        }
    )


# ------------------------------------------------------------------- DEF-809


def test_opslaan_geeft_de_sessiebeoordeling_door_en_het_record_draagt_haar(
    repo, sessie
):
    did = repo.save(_record())
    tab = _tab(repo)
    # Stap 2: tekst naar exact P01 opslaan (zonder sessiebeoordeling).
    geladen = _herladen(repo, did)
    _vul_editor(geladen, tekst=P01_TEKST, status="draft")
    with patch("ui.components.definition_edit_tab.st", _mock_st()):
        tab._save_definition()
    geladen = _herladen(repo, did)
    assert geladen.definitie == P01_TEKST
    assert geladen.metadata["source_evidence_status"]["current"] is False

    # Stap 3: "Valideren" → verse beoordeling in de sessie.
    nieuw = bouw_documentbeoordeling(P01_TEKST, geladen.metadata["provenance_sources"])
    SessionStateManager.set_value("edit_last_validation", _sessieresultaat(nieuw))

    # Stap 4: status review, Opslaan.
    _vul_editor(geladen, tekst=P01_TEKST, status="review")
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._save_definition()
    assert "opgeslagen" in _teksten(m).lower()
    assert "bronbeoordeling" in _teksten(m).lower()

    # Stap 5: heropenen.
    record = _facade(repo).get_definitie(did)
    assert record.status == "review"
    bewijs = record.get_source_evidence()
    assert bewijs["source_assessment"] == nieuw
    assert bewijs["candidate"]["definitie"] == P01_TEKST
    assert record.get_source_evidence_status()["current"] is True
    assert len(record.get_source_evidence_history()) == 1


def test_stale_sessiebeoordeling_wordt_niet_opgeslagen_en_zichtbaar_gemeld(
    repo, sessie
):
    did = repo.save(_record(P01_TEKST))
    tab = _tab(repo)
    geladen = _herladen(repo, did)
    # Beoordeling voor P01 in de sessie, maar de gebruiker bewerkt daarna verder.
    voor_p01 = bouw_documentbeoordeling(
        P01_TEKST,
        geladen.metadata["provenance_sources"],
        assessed_at="2026-09-17T21:16:46+00:00",
    )
    SessionStateManager.set_value("edit_last_validation", _sessieresultaat(voor_p01))
    _vul_editor(geladen, tekst=P01_TEKST + " van algemene strekking", status="draft")
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._save_definition()
    tekst = _teksten(m).lower()
    assert "opgeslagen" in tekst
    assert "niet opgeslagen" in tekst or "hoort niet bij" in tekst
    record = _facade(repo).get_definitie(did)
    assert record.get_definitie_tekst() == P01_TEKST + " van algemene strekking"
    assert record.get_source_evidence()["source_assessment"]["assessed_at"] == (
        "2026-09-17T14:43:02+00:00"
    )
    assert record.get_source_evidence_history() == []


# --------------------------------------------------------- DEF-808 (editor)


def test_bronmetadata_formulier_schrijft_via_de_servicelaag_naar_het_record(
    repo, sessie
):
    did = repo.save(_record(P01_TEKST))
    tab = _tab(repo)
    geladen = _herladen(repo, did)
    _vul_editor(geladen, tekst=P01_TEKST, status="draft")
    SessionStateManager.set_value("user", ACTOR)
    k = f"edit_{did}_bronmeta"
    SessionStateManager.set_value(f"{k}_url", P01_URL)
    SessionStateManager.set_value(f"{k}_versie", P01_VERSIE)
    SessionStateManager.set_value(f"{k}_vindplaats", P01_VINDPLAATS)

    # Zonder klik: niets geschreven, formulier toont het document.
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_bronmetadata_section(geladen)
    assert (
        _facade(repo).get_definitie(did).version_number
        == geladen.metadata["version_number"]
    )
    knop = next(
        c for c in m.button.call_args_list if c.kwargs.get("key") == f"{k}_vastleggen"
    )
    assert knop.kwargs.get("disabled") is False
    assert "awb-1-3-20260815.txt" in _teksten(m)
    assert "geen authenticiteitsbewijs" in _teksten(m).lower()

    # Klik: via de servicelaag vastgelegd, record ververst.
    m2 = _mock_st(**{f"{k}_vastleggen": True})
    with patch("ui.components.definition_edit_tab.st", m2):
        tab._render_bronmetadata_section(geladen)
    resultaat: Any = SessionStateManager.get_value(f"{k}_resultaat")
    assert resultaat["status"] == "applied", resultaat
    record = _facade(repo).get_definitie(did)
    documenten = [
        b
        for b in record.get_source_evidence()["sources"]
        if b["provider"] == "documents"
    ]
    assert len(documenten) == 2
    for bron in documenten:
        assert bron["url"] == P01_URL
        assert bron["source_version"] == P01_VERSIE
        assert bron["locator"] == P01_VINDPLAATS
        assert bron[DECLARED_METADATA_KEY]["declared_by"] == ACTOR
    ververst: Any = SessionStateManager.get_value("editing_definition")
    assert ververst.metadata["version_number"] == record.version_number

    # Volgende run toont het resultaat en de opgave bij het document.
    m3 = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m3):
        tab._render_bronmetadata_section(ververst)
    tekst = _teksten(m3)
    assert P01_URL in tekst and P01_VERSIE in tekst and P01_VINDPLAATS in tekst
    assert ACTOR in tekst


def test_bronmetadata_formulier_wijst_ongeldige_link_af_zonder_te_schrijven(
    repo, sessie
):
    did = repo.save(_record(P01_TEKST))
    tab = _tab(repo)
    geladen = _herladen(repo, did)
    _vul_editor(geladen, tekst=P01_TEKST, status="draft")
    SessionStateManager.set_value("user", ACTOR)
    k = f"edit_{did}_bronmeta"
    SessionStateManager.set_value(f"{k}_url", "javascript:alert(1)")
    m = _mock_st(**{f"{k}_vastleggen": True})
    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_bronmetadata_section(geladen)
    resultaat: Any = SessionStateManager.get_value(f"{k}_resultaat")
    assert resultaat["status"] == "invalid"
    record = _facade(repo).get_definitie(did)
    assert record.version_number == geladen.metadata["version_number"]
    assert all(b.get("url") is None for b in record.get_source_evidence()["sources"])
    # Zichtbaar afgewezen (in dezelfde of de volgende run).
    m2 = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m2):
        tab._render_bronmetadata_section(geladen)
    assert "hyperlink" in _teksten(m2).lower()


def test_bronmetadata_knop_is_uitgeschakeld_zonder_reviewer_of_zonder_invoer(
    repo, sessie
):
    did = repo.save(_record(P01_TEKST))
    tab = _tab(repo)
    geladen = _herladen(repo, did)
    _vul_editor(geladen, tekst=P01_TEKST, status="draft")
    k = f"edit_{did}_bronmeta"

    def _knop(m: MagicMock):
        return next(
            c
            for c in m.button.call_args_list
            if c.kwargs.get("key") == f"{k}_vastleggen"
        )

    # Zonder actor, met invoer: uitgeschakeld en klik doet niets.
    SessionStateManager.set_value(f"{k}_url", P01_URL)
    m = _mock_st(**{f"{k}_vastleggen": True})
    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_bronmetadata_section(geladen)
    assert _knop(m).kwargs["disabled"] is True
    assert "reviewer" in _knop(m).kwargs["help"].lower()
    # Met actor, zonder enige invoer: uitgeschakeld.
    SessionStateManager.set_value("user", ACTOR)
    SessionStateManager.set_value(f"{k}_url", "")
    m2 = _mock_st(**{f"{k}_vastleggen": True})
    with patch("ui.components.definition_edit_tab.st", m2):
        tab._render_bronmetadata_section(geladen)
    assert _knop(m2).kwargs["disabled"] is True
    assert (
        _facade(repo).get_definitie(did).version_number
        == geladen.metadata["version_number"]
    )


def test_bronmetadata_sectie_zonder_documentbronnen_biedt_geen_formulier(repo, sessie):
    did = repo.save(
        Definition(
            begrip=BEGRIP,
            definitie=P01_TEKST,
            categorie="resultaat",
            juridische_context=list(JUR),
            metadata={"status": "draft"},
        )
    )
    tab = _tab(repo)
    geladen = _herladen(repo, did)
    SessionStateManager.set_value("user", ACTOR)
    m = _mock_st()
    with patch("ui.components.definition_edit_tab.st", m):
        tab._render_bronmetadata_section(geladen)
    assert not [
        c
        for c in m.button.call_args_list
        if str(c.kwargs.get("key", "")).endswith("_vastleggen")
    ]
    assert "geen" in _teksten(m).lower()


# --------------------------------------------------------- DEF-808 (upload)


AWB_TEKST = (
    "Algemene wet bestuursrecht Artikel 1:3 1. Onder besluit wordt verstaan: een "
    "schriftelijke beslissing van een bestuursorgaan, inhoudende een "
    "publiekrechtelijke rechtshandeling."
)


def _upload(tmp_path):
    processor = DocumentProcessor(storage_dir=str(tmp_path / "docs"))
    with patch(
        "document_processing.document_processor.extract_text_from_file",
        return_value=AWB_TEKST,
    ):
        doc = processor.process_uploaded_file(
            AWB_TEKST.encode("utf-8"), "awb-1-3-20260815.txt", "text/plain"
        )
    return processor, doc


def test_uploadformulier_legt_opgave_vast_bij_het_document(tmp_path, sessie):
    from ui.renderers.document_upload_renderer import DocumentUploadRenderer

    processor, doc = _upload(tmp_path)
    SessionStateManager.set_value("user", ACTOR)
    k = f"docmeta_{doc.id}"
    SessionStateManager.set_value(f"{k}_url", P01_URL)
    SessionStateManager.set_value(f"{k}_versie", P01_VERSIE)
    SessionStateManager.set_value(f"{k}_vindplaats", P01_VINDPLAATS)
    m = _mock_st(**{f"{k}_vastleggen": True})
    with patch("ui.renderers.document_upload_renderer.st", m):
        DocumentUploadRenderer()._render_bronmetadata_invoer(processor, doc)
    opgave = processor.get_document_by_id(doc.id).source_metadata
    assert opgave["url"] == P01_URL
    assert opgave["source_version"] == P01_VERSIE
    assert opgave["locator"] == P01_VINDPLAATS
    assert opgave["declared_by"] == ACTOR
    assert "vastgelegd" in _teksten(m).lower()


def test_uploadformulier_wijst_ongeldige_link_af(tmp_path, sessie):
    from ui.renderers.document_upload_renderer import DocumentUploadRenderer

    processor, doc = _upload(tmp_path)
    k = f"docmeta_{doc.id}"
    SessionStateManager.set_value(f"{k}_url", "intern.example/awb")
    m = _mock_st(**{f"{k}_vastleggen": True})
    with patch("ui.renderers.document_upload_renderer.st", m):
        DocumentUploadRenderer()._render_bronmetadata_invoer(processor, doc)
    assert processor.get_document_by_id(doc.id).source_metadata is None
    assert "hyperlink" in _teksten(m).lower()
    assert m.error.called


def test_uploadformulier_meldt_mislukte_opslag_en_geen_succes(tmp_path, sessie):
    """Codex-review 1 (P2): een echte schrijffout op het metadata-bestand geeft
    een zichtbare afwijzing, geen succesmelding en geen aangenomen opgave."""
    import builtins

    from ui.renderers.document_upload_renderer import DocumentUploadRenderer

    processor, doc = _upload(tmp_path)
    SessionStateManager.set_value("user", ACTOR)
    k = f"docmeta_{doc.id}"
    SessionStateManager.set_value(f"{k}_url", P01_URL)
    metadata_pad = str(tmp_path / "docs" / "documents_metadata.json")
    origineel = builtins.open

    def _open(bestand, *args, **kwargs):
        modus = args[0] if args else kwargs.get("mode", "r")
        if str(bestand) == metadata_pad and "w" in str(modus):
            raise PermissionError(13, "Permission denied", metadata_pad)
        return origineel(bestand, *args, **kwargs)

    m = _mock_st(**{f"{k}_vastleggen": True})
    with (
        patch("ui.renderers.document_upload_renderer.st", m),
        patch("builtins.open", side_effect=_open),
    ):
        DocumentUploadRenderer()._render_bronmetadata_invoer(processor, doc)
    assert not m.success.called
    assert m.error.called
    assert "niet opgeslagen" in _teksten(m).lower()
    assert processor.get_document_by_id(doc.id).source_metadata is None
    assert (
        DocumentProcessor(storage_dir=str(tmp_path / "docs"))
        .get_document_by_id(doc.id)
        .source_metadata
        is None
    )
