"""DEF-809 — een nieuwe editorbeoordeling overleeft opslaan, statusovergang en heropenen.

Reproductie van de P01-appcontrole (17 september 2026) op een tijdelijke echte
SQLite-database via de servicelaag van de editor (`DefinitionEditService`),
telkens ID-only herladen met een verse repository:

1. record met gegenereerde tekst en een oude, daaraan gebonden AI-beoordeling;
2. tekst bewerkt naar exact P01 en opgeslagen — het oude bewijs hoort bij de
   oude tekst (historisch), dat blijft eerlijk zichtbaar;
3. "Valideren" levert een verse beoordeling voor exact P01 (stand-in voor de
   actieve wrapper, echte kernvingerafdruk);
4. status → review en opslaan mét die verse beoordeling;
5. heropenen (Expert Review / readback): de verse beoordeling en de actuele
   kandidaat staan in het bewijs, het oude document in de historie, de replay
   van de kern past de beoordeling toe.

Daarnaast: een beoordeling die niet bij de op te slaan kandidaat hoort (stale,
niet uitgevoerd, zonder bronset) wordt nooit als actueel bewijs opgeslagen en
dat wordt benoemd; een latere statusovergang zonder inhoudelijke wijziging
laat het bewaarde bewijs staan. Geen model, geen netwerk.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from database.definitie_repository import DefinitieRepository
from domain.sources.contract import beoordeel_bronbasis, beoordeling_technische_fout
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import DefinitionEditService
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from tests.fixtures.def808_p01 import (
    BEGRIP,
    CONTEXTEN,
    DOCUMENTBRONNEN,
    GEGENEREERDE_TEKST,
    JUR,
    P01_TEKST,
    WET,
    bouw_documentbeoordeling,
)

pytestmark = [pytest.mark.unit]

GEBRUIKER = "editor-gebruiker"
OUDE_BEOORDELING_TIJD = "2026-09-17T14:43:02+00:00"
NIEUWE_BEOORDELING_TIJD = "2026-09-17T21:16:46+00:00"


# ------------------------------------------------------------------ helpers


def _repo(tmp_path) -> DefinitionEditRepository:
    return DefinitionEditRepository(str(tmp_path / "def809.db"))


def _facade(repo) -> DefinitieRepository:
    return DefinitieRepository(repo.db_path)


def _herladen(repo, did: int) -> Definition:
    geladen = DefinitionRepository(repo.db_path).get(did)
    assert geladen is not None
    return geladen


def _gegenereerd_record() -> Definition:
    return Definition(
        begrip=BEGRIP,
        definitie=GEGENEREERDE_TEKST,
        categorie="resultaat",
        organisatorische_context=[],
        juridische_context=list(JUR),
        wettelijke_basis=list(WET),
        metadata={
            "status": "draft",
            "created_by": "generator",
            "sources": deepcopy(DOCUMENTBRONNEN),
            "provenance_sources": deepcopy(DOCUMENTBRONNEN),
            "source_assessment": bouw_documentbeoordeling(
                GEGENEREERDE_TEKST, DOCUMENTBRONNEN, assessed_at=OUDE_BEOORDELING_TIJD
            ),
            "definitie_origineel": GEGENEREERDE_TEKST,
            "definitie_eindtekst": GEGENEREERDE_TEKST,
            "generated_at": "2026-09-17T14:43:02+00:00",
            "generation_id": "d96266b8-5a44-4578-89b2-f54258f51c7c",
        },
    )


def _editor_updates(geladen: Definition, **wijzigingen: Any) -> dict[str, Any]:
    """Wat de editor bij Opslaan aanlevert: alle velden, ook ongewijzigd."""
    updates = {
        "begrip": geladen.begrip,
        "definitie": geladen.definitie,
        "organisatorische_context": list(geladen.organisatorische_context or []),
        "juridische_context": list(geladen.juridische_context or []),
        "wettelijke_basis": list(geladen.wettelijke_basis or []),
        "categorie": geladen.categorie,
        "ufo_categorie": None,
        "toelichting": geladen.toelichting or "",
        "status": (geladen.metadata or {}).get("status", "draft"),
        "version_number": (geladen.metadata or {}).get("version_number", 1),
    }
    updates.update(wijzigingen)
    return updates


def _p01_opgeslagen(repo) -> tuple[DefinitionEditService, int]:
    """Stap 1+2: gegenereerd record, daarna tekst bewerkt naar exact P01."""
    did = repo.save(_gegenereerd_record())
    service = DefinitionEditService(repository=repo, validation_service=None)
    geladen = _herladen(repo, did)
    uit = service.save_definition(
        did, _editor_updates(geladen, definitie=P01_TEKST), user=GEBRUIKER
    )
    assert uit["success"] is True
    return service, did


def _replay(record) -> dict[str, Any]:
    velden = record.get_contractvelden()
    return beoordeel_bronbasis(
        record.begrip,
        record.get_definitie_tekst(),
        record.get_contextlijsten(),
        velden.get("provenance_sources") or [],
        assessment=velden.get("source_assessment"),
        review=velden.get("source_review"),
        definitie_versie=velden.get("definition_version"),
        peildatum=velden.get("peildatum"),
    ).als_dict()


# --------------------------------------------------------------- reproductie


def test_tekstbewerking_zonder_nieuwe_beoordeling_laat_oud_bewijs_eerlijk_historisch(
    tmp_path,
):
    repo = _repo(tmp_path)
    _, did = _p01_opgeslagen(repo)
    record = _facade(repo).get_definitie(did)
    assert record.get_definitie_tekst() == P01_TEKST
    bewijs = record.get_source_evidence()
    assert bewijs["candidate"]["definitie"] == GEGENEREERDE_TEKST
    assert bewijs["source_assessment"]["assessed_at"] == OUDE_BEOORDELING_TIJD
    status = record.get_source_evidence_status()
    assert status["status"] == "present" and status["current"] is False
    assert "definitie" in (status["reason"] or "")
    replay = _replay(record)
    assert replay["review"]["assessment"]["applied"] is False
    assert "gewijzigd" in replay["review"]["assessment"]["reason"]


def test_valideren_status_review_opslaan_bewaart_de_nieuwe_beoordeling_en_kandidaat(
    tmp_path,
):
    repo = _repo(tmp_path)
    service, did = _p01_opgeslagen(repo)
    geladen = _herladen(repo, did)
    versie_voor = geladen.metadata["version_number"]

    # Stap 3: "Valideren" — verse beoordeling voor exact P01, dezelfde bronset.
    nieuw = bouw_documentbeoordeling(
        P01_TEKST,
        geladen.metadata["provenance_sources"],
        assessed_at=NIEUWE_BEOORDELING_TIJD,
    )
    assert nieuw["fingerprint"] != geladen.metadata["source_assessment"]["fingerprint"]

    # Stap 4: status → review en Opslaan, met de beoordeling uit de sessie.
    uit = service.save_definition(
        did,
        _editor_updates(geladen, status="review"),
        user=GEBRUIKER,
        source_assessment=nieuw,
    )
    assert uit["success"] is True
    assert uit["source_assessment_persisted"] is True
    assert uit["source_assessment_reason"] is None

    # Stap 5: heropenen met een verse repository (Expert Review / readback).
    record = _facade(repo).get_definitie(did)
    assert record.status == "review"
    assert record.get_definitie_tekst() == P01_TEKST
    assert record.version_number == versie_voor + 1  # één versiebump
    bewijs = record.get_source_evidence()
    assert bewijs["source_assessment"] == nieuw
    assert bewijs["candidate"]["definitie"] == P01_TEKST
    assert bewijs["context"]["juridische_context"] == JUR
    assert bewijs["origin"] == "revalidation"
    assert bewijs["version_number"] == record.version_number
    assert bewijs["recorded_by"] == GEBRUIKER
    # Stabiele identiteit en bronbinding: dezelfde generatie, dezelfde bronset.
    oud = _facade(repo).get_definitie(did).get_source_evidence_history()
    assert len(oud) == 1
    assert oud[0]["source_assessment"]["assessed_at"] == OUDE_BEOORDELING_TIJD
    assert oud[0]["candidate"]["definitie"] == GEGENEREERDE_TEKST
    assert bewijs["generation_identity"] == oud[0]["generation_identity"]
    assert bewijs["sources"] == oud[0]["sources"]
    assert record.get_source_evidence_status() == {
        "status": "present",
        "current": True,
        "reason": None,
    }
    # De kern past de nieuwe beoordeling toe op het opgeslagen record; de
    # verwijskwaliteit blijft zónder hyperlink open (DEF-806) — geen pass geforceerd.
    replay = _replay(record)
    assert replay["review"]["assessment"]["applied"] is True
    delen = {p["id"]: p for p in replay["parts"]}
    assert delen["source_authority"]["status"] == "pass"
    assert delen["semantic_support"]["status"] == "pass"
    assert delen["reference_quality"]["status"] == "review_required"
    assert "hyperlink" in delen["reference_quality"]["reason"]
    # Ook via de service-adapter die de editor en de UI lezen.
    meta = _herladen(repo, did).metadata
    assert meta["source_assessment"]["assessed_at"] == NIEUWE_BEOORDELING_TIJD
    assert meta["source_evidence"]["candidate"]["definitie"] == P01_TEKST


def test_statusovergang_zonder_inhoudelijke_wijziging_verliest_het_bewijs_niet(
    tmp_path,
):
    repo = _repo(tmp_path)
    service, did = _p01_opgeslagen(repo)
    geladen = _herladen(repo, did)
    nieuw = bouw_documentbeoordeling(
        P01_TEKST,
        geladen.metadata["provenance_sources"],
        assessed_at=NIEUWE_BEOORDELING_TIJD,
    )
    assert service.save_definition(
        did, _editor_updates(geladen), user=GEBRUIKER, source_assessment=nieuw
    )["source_assessment_persisted"]

    # Latere statusovergang zonder sessiebeoordeling (bv. ander tabblad).
    geladen = _herladen(repo, did)
    uit = service.save_definition(
        did, _editor_updates(geladen, status="review"), user=GEBRUIKER
    )
    assert uit["success"] is True
    record = _facade(repo).get_definitie(did)
    assert record.status == "review"
    bewijs = record.get_source_evidence()
    assert bewijs["source_assessment"]["assessed_at"] == NIEUWE_BEOORDELING_TIJD
    assert bewijs["candidate"]["definitie"] == P01_TEKST
    assert record.get_source_evidence_status()["current"] is True
    assert len(record.get_source_evidence_history()) == 1  # geen extra document
    assert _replay(record)["review"]["assessment"]["applied"] is True


def test_dezelfde_beoordeling_nogmaals_opslaan_schrijft_geen_nieuw_bewijsdocument(
    tmp_path,
):
    repo = _repo(tmp_path)
    service, did = _p01_opgeslagen(repo)
    geladen = _herladen(repo, did)
    nieuw = bouw_documentbeoordeling(P01_TEKST, geladen.metadata["provenance_sources"])
    service.save_definition(
        did, _editor_updates(geladen), user=GEBRUIKER, source_assessment=nieuw
    )
    geladen = _herladen(repo, did)
    uit = service.save_definition(
        did, _editor_updates(geladen), user=GEBRUIKER, source_assessment=nieuw
    )
    assert uit["success"] is True and uit["source_assessment_persisted"] is True
    assert len(_facade(repo).get_definitie(did).get_source_evidence_history()) == 1


# ------------------------------------------------- geen oude pass laten gelden


def test_stale_beoordeling_voor_een_andere_tekst_wordt_niet_als_actueel_opgeslagen(
    tmp_path,
):
    """Valideren op P01, daarna verder bewerken en pas dan opslaan: de
    beoordeling hoort niet bij de opgeslagen kandidaat en wordt benoemd."""
    repo = _repo(tmp_path)
    service, did = _p01_opgeslagen(repo)
    geladen = _herladen(repo, did)
    voor_p01 = bouw_documentbeoordeling(
        P01_TEKST, geladen.metadata["provenance_sources"]
    )
    verder = P01_TEKST + " van algemene strekking"
    uit = service.save_definition(
        did,
        _editor_updates(geladen, definitie=verder),
        user=GEBRUIKER,
        source_assessment=voor_p01,
    )
    assert uit["success"] is True
    assert uit["source_assessment_persisted"] is False
    assert "hoort niet bij" in uit["source_assessment_reason"]
    record = _facade(repo).get_definitie(did)
    assert record.get_definitie_tekst() == verder
    bewijs = record.get_source_evidence()
    assert bewijs["source_assessment"]["assessed_at"] == OUDE_BEOORDELING_TIJD
    assert bewijs["source_assessment"] != voor_p01
    assert record.get_source_evidence_history() == []
    assert _replay(record)["review"]["assessment"]["applied"] is False


@pytest.mark.parametrize(
    ("beoordeling", "verwacht"),
    [
        (None, None),
        ("geen object", "geen object"),
        ({"status": "unavailable", "fingerprint": "x"}, "niet uitgevoerd"),
        (
            beoordeling_technische_fout("x", "timeout", "synthetisch"),
            "niet uitgevoerd",
        ),
    ],
)
def test_niet_uitgevoerde_of_ontbrekende_beoordeling_raakt_het_bewijs_niet(
    tmp_path, beoordeling, verwacht
):
    repo = _repo(tmp_path)
    service, did = _p01_opgeslagen(repo)
    geladen = _herladen(repo, did)
    uit = service.save_definition(
        did, _editor_updates(geladen), user=GEBRUIKER, source_assessment=beoordeling
    )
    assert uit["success"] is True
    assert uit["source_assessment_persisted"] is False
    if verwacht is None:
        assert uit["source_assessment_reason"] is None
    else:
        assert verwacht in uit["source_assessment_reason"]
    record = _facade(repo).get_definitie(did)
    assert record.get_source_evidence()["source_assessment"]["assessed_at"] == (
        OUDE_BEOORDELING_TIJD
    )
    assert record.get_source_evidence_history() == []


def test_beoordeling_met_andere_context_bindt_niet(tmp_path):
    repo = _repo(tmp_path)
    service, did = _p01_opgeslagen(repo)
    geladen = _herladen(repo, did)
    andere_context = {**CONTEXTEN, "juridische_context": ["Strafrecht"]}
    nieuw = bouw_documentbeoordeling(
        P01_TEKST, geladen.metadata["provenance_sources"], contexten=andere_context
    )
    uit = service.save_definition(
        did, _editor_updates(geladen), user=GEBRUIKER, source_assessment=nieuw
    )
    assert uit["source_assessment_persisted"] is False
    assert _facade(repo).get_definitie(did).get_source_evidence_history() == []


# ------------------------------------- samenloop met DEF-751 B2 (categoriekeuze)


def test_categoriekeuze_en_nieuwe_beoordeling_landen_samen_in_een_opslag(tmp_path):
    """Integratie main (DEF-751 B2) × DEF-809: één editor-opslag met een
    gewijzigde categorie (expliciet keuzecommando, één UPDATE met versieguard)
    én de verse sessiebeoordeling — beide landen, geen van beide verdringt de
    ander in `generation_prompt_data`; de keuze is aan de handelende
    gebruiker geattribueerd."""
    repo = _repo(tmp_path)
    service, did = _p01_opgeslagen(repo)
    geladen = _herladen(repo, did)
    assert geladen.categorie == "resultaat"
    nieuw = bouw_documentbeoordeling(
        P01_TEKST,
        geladen.metadata["provenance_sources"],
        assessed_at=NIEUWE_BEOORDELING_TIJD,
    )
    uit = service.save_definition(
        did,
        _editor_updates(geladen, categorie="type", status="review"),
        user=GEBRUIKER,
        source_assessment=nieuw,
        categoriekeuze={
            "herkomst": "editor",
            "actor": GEBRUIKER,
            "actor_source": "typed_name",
        },
    )
    assert uit["success"] is True, uit
    assert uit["source_assessment_persisted"] is True

    record = _facade(repo).get_definitie(did)
    assert record.status == "review"
    assert record.categorie == "type"
    assert record.version_number == geladen.metadata["version_number"] + 1
    # DEF-751: het keuze-event met menselijke herkomst en actor.
    keuze = record.get_category_choice()
    assert keuze is not None
    assert keuze["origin"] == "editor" and keuze["value"] == "type"
    assert keuze["actor"] == GEBRUIKER and keuze["actor_source"] == "typed_name"
    assert record.get_category_choice_status()["status"] == "manual_confirmed"
    # DEF-809: de verse beoordeling en de actuele kandidaat in hetzelfde record.
    bewijs = record.get_source_evidence()
    assert bewijs["source_assessment"] == nieuw
    assert bewijs["candidate"]["definitie"] == P01_TEKST
    assert bewijs["origin"] == "revalidation"
    assert len(record.get_source_evidence_history()) == 1
    assert _replay(record)["review"]["assessment"]["applied"] is True
    # Een tweede opslag zonder keuze en zonder sessiebeoordeling laat beide staan.
    geladen = _herladen(repo, did)
    assert service.save_definition(did, _editor_updates(geladen), user=GEBRUIKER)[
        "success"
    ]
    na = _facade(repo).get_definitie(did)
    assert na.get_category_choice()["value"] == "type"
    assert na.get_source_evidence()["source_assessment"] == nieuw
    assert len(na.get_source_evidence_history()) == 1
