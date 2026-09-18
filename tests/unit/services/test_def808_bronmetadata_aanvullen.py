"""DEF-808 — bronmetadata aanvullen op een opgeslagen record (aanvulroute) en de P01-keten.

Op een tijdelijke echte SQLite-database, via de servicelaag van de editor
(`DefinitionEditService.vul_bronmetadata_aan`) en ID-only herladen:

* de opgegeven hyperlink/bronversie/vindplaats landen op álle passages van het
  gekozen document in het actuele bewijs, herkenbaar als opgegeven metadata
  (door/op), zonder de passages, kwitantieadministratie of andere bronnen te
  raken; het vorige bewijsdocument gaat naar de historie; de generatie-
  identiteit blijft;
* de eerdere AI-beoordeling geldt daarna niet meer (vingerafdruk: bronnen
  gewijzigd) en dat wordt benoemd — geen automatisch pass, geen goedkeuring;
* ongeldige invoer wordt zichtbaar afgewezen zonder te schrijven; onbekend
  document, versieconflict en alleen-lezen status schrijven evenmin;
* de P01-keten: aanvullen → verse beoordeling voor exact P01 met de aangevulde
  bronset → opslaan (DEF-809) → heropenen: metadata én beoordeling behouden,
  verwijskwaliteit 'voldoet' via de echte DEF-806-regel — geen no-linkuitzondering.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from database.definitie_repository import DefinitieRepository
from domain.sources.bronmetadata import DECLARED_METADATA_KEY
from domain.sources.contract import beoordeel_bronbasis, is_bruikbare_hyperlink
from domain.sources.normalisatie import canoniseer_bronnen
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import DefinitionEditService
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

pytestmark = [pytest.mark.unit]

ACTOR = "Chris"
RAGBRON = {
    "provider": "rag",
    "chunk_id": "chunk-x",
    "document_id": "doc-x",
    "title": "Andere bron",
    "url": None,
    "snippet": "Een andere passage zonder link.",
    "score": 0.5,
}


def _repo(tmp_path) -> DefinitionEditRepository:
    return DefinitionEditRepository(str(tmp_path / "def808.db"))


def _facade(repo) -> DefinitieRepository:
    return DefinitieRepository(repo.db_path)


def _herladen(repo, did: int) -> Definition:
    geladen = DefinitionRepository(repo.db_path).get(did)
    assert geladen is not None
    return geladen


def _record(
    tekst: str = P01_TEKST, *, bronnen: list | None = None, **meta
) -> Definition:
    bronnen = (
        deepcopy(DOCUMENTBRONNEN) + [deepcopy(RAGBRON)] if bronnen is None else bronnen
    )
    metadata: dict[str, Any] = {
        "status": "draft",
        "created_by": "generator",
        "sources": deepcopy(bronnen),
        "provenance_sources": deepcopy(bronnen),
        "source_assessment": bouw_documentbeoordeling(tekst, bronnen),
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


def _service(repo) -> DefinitionEditService:
    return DefinitionEditService(repository=repo, validation_service=None)


def _aanvullen(service, did: int, versie: int, **overrides: Any) -> dict[str, Any]:
    argumenten: dict[str, Any] = {
        "doc_id": DOC_ID,
        "url": P01_URL,
        "source_version": P01_VERSIE,
        "locator": P01_VINDPLAATS,
        "actor": ACTOR,
        "expected_version": versie,
    }
    argumenten.update(overrides)
    return service.vul_bronmetadata_aan(did, **argumenten)


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


# --------------------------------------------------------------- aanvulroute


def test_aanvullen_landt_op_alle_passages_van_het_document_met_herkomst(tmp_path):
    repo = _repo(tmp_path)
    did = repo.save(_record())
    voor = _facade(repo).get_definitie(did)
    oud_bewijs = voor.get_source_evidence()

    uit = _aanvullen(_service(repo), did, voor.version_number)
    assert uit["status"] == "applied", uit
    assert uit["aantal_bronnen"] == 2
    assert uit["version_number"] == voor.version_number + 1

    na = _facade(repo).get_definitie(did)
    assert na.version_number == voor.version_number + 1
    bewijs = na.get_source_evidence()
    documenten = [b for b in bewijs["sources"] if b["provider"] == "documents"]
    overige = [b for b in bewijs["sources"] if b["provider"] != "documents"]
    assert len(documenten) == 2 and overige == [RAGBRON]
    for oud, nieuw in zip(oud_bewijs["sources"][:2], documenten, strict=True):
        assert nieuw["url"] == P01_URL
        assert nieuw["source_version"] == P01_VERSIE
        assert nieuw["locator"] == P01_VINDPLAATS
        opgegeven = nieuw[DECLARED_METADATA_KEY]
        assert opgegeven["declared_by"] == ACTOR and opgegeven["declared_at"]
        assert opgegeven["url"] == P01_URL
        # Passage en overige administratie exact behouden.
        for sleutel, waarde in oud.items():
            if sleutel != "url":
                assert nieuw[sleutel] == waarde
    # Historie, identiteit en herkomst van het bewijsdocument.
    assert bewijs["origin"] == "correction"
    assert bewijs["recorded_by"] == ACTOR
    assert bewijs["candidate"]["definitie"] == P01_TEKST
    assert bewijs["generation_identity"] == oud_bewijs["generation_identity"]
    historie = na.get_source_evidence_history()
    assert len(historie) == 1 and historie[0]["sources"] == oud_bewijs["sources"]
    # Het contract leest de metadata; de bron-id blijft de stabiele documentbasis.
    canoniek = canoniseer_bronnen(bewijs["sources"])
    documentbronnen = [b for b in canoniek if b.provider == "documents"]
    assert all(b.source_id.startswith(f"doc:{DOC_ID}") for b in documentbronnen)
    assert all(
        b.url == P01_URL and b.version == P01_VERSIE and b.locator == P01_VINDPLAATS
        for b in documentbronnen
    )
    assert all(is_bruikbare_hyperlink(b.url) for b in documentbronnen)
    # Ook via de service-adapter (editor/UI) en de metadata-status.
    meta = _herladen(repo, did).metadata
    assert meta["provenance_sources"] == bewijs["sources"]
    assert meta["source_evidence_status"]["current"] is True


def test_aanvullen_maakt_de_eerdere_beoordeling_verouderd_zonder_pass_te_forceren(
    tmp_path,
):
    repo = _repo(tmp_path)
    did = repo.save(_record())
    voor = _facade(repo).get_definitie(did)
    assert _replay(voor)["review"]["assessment"]["applied"] is True

    assert _aanvullen(_service(repo), did, voor.version_number)["status"] == "applied"
    na = _facade(repo).get_definitie(did)
    bewijs = na.get_source_evidence()
    # De oude beoordeling blijft zichtbaar in het bewijs (historisch), maar
    # geldt niet meer: de bronnen zijn gewijzigd. Niets wordt goedgekeurd.
    assert (
        bewijs["source_assessment"] == voor.get_source_evidence()["source_assessment"]
    )
    replay = _replay(na)
    assert replay["review"]["assessment"]["applied"] is False
    assert "bronnen" in replay["review"]["assessment"]["reason"]
    assert replay["status"] == "review_required"
    assert all(p["status"] == "review_required" for p in replay["parts"])


def test_deskundige_verwijzingsuitzondering_vervalt_na_toevoegen_van_een_hyperlink(
    tmp_path,
):
    """Een vastgelegde uitzondering (bron zonder link) geldt niet meer zodra de
    bron een bruikbare link draagt: versiebump én vingerafdruk laten haar vervallen."""
    from domain.sources.contract import bereken_bronvingerafdruk

    repo = _repo(tmp_path)
    did = repo.save(_record())
    facade = _facade(repo)
    rec = facade.get_definitie(did)
    bewijs = rec.get_source_evidence()
    dragend, _rest = [
        b for b in canoniseer_bronnen(bewijs["sources"]) if b.provider == "documents"
    ][:2]
    review = {
        "type": "reference_exception",
        "accepted": True,
        "actor": ACTOR,
        "rationale": "Intern raadpleegbaar.",
        "version_number": rec.version_number,
        "fingerprint": bereken_bronvingerafdruk(
            rec.begrip,
            rec.get_definitie_tekst(),
            rec.get_contextlijsten(),
            bewijs["sources"],
        ),
        "source_id": dragend.source_id,
        "content_hash": dragend.content_hash,
        "source_version": None,
        "locator": P01_VINDPLAATS,
    }
    assert facade.set_source_review(
        did, review, updated_by=ACTOR, expected_version=rec.version_number
    )
    rec = facade.get_definitie(did)
    assert _replay(rec)["review"]["applied"] is True

    assert _aanvullen(_service(repo), did, rec.version_number)["status"] == "applied"
    na = facade.get_definitie(did)
    assert _replay(na)["review"]["applied"] is False
    assert na.get_source_review_status()["status"] == "stale"


# ------------------------------------------------------- afwijzingen (fail-closed)


@pytest.mark.parametrize(
    "ongeldig", ["javascript:alert(1)", "intern.example/awb", "https://", "ftp://x/y"]
)
def test_ongeldige_hyperlink_wordt_afgewezen_en_er_wordt_niets_geschreven(
    tmp_path, ongeldig
):
    repo = _repo(tmp_path)
    did = repo.save(_record())
    voor = _facade(repo).get_definitie(did)
    uit = _aanvullen(_service(repo), did, voor.version_number, url=ongeldig)
    assert uit["status"] == "invalid"
    assert uit["errors"] and "hyperlink" in uit["errors"][0].lower()
    na = _facade(repo).get_definitie(did)
    assert na.version_number == voor.version_number
    assert na.get_source_evidence() == voor.get_source_evidence()
    assert na.get_source_evidence_history() == []


def test_zonder_enige_waarde_wordt_niets_geschreven(tmp_path):
    repo = _repo(tmp_path)
    did = repo.save(_record())
    voor = _facade(repo).get_definitie(did)
    uit = _aanvullen(
        _service(repo),
        did,
        voor.version_number,
        url="",
        source_version=None,
        locator=" ",
    )
    assert uit["status"] == "invalid"
    assert _facade(repo).get_definitie(did).version_number == voor.version_number


def test_onbekend_document_versieconflict_en_alleen_lezen_schrijven_niet(tmp_path):
    repo = _repo(tmp_path)
    did = repo.save(_record())
    service = _service(repo)
    voor = _facade(repo).get_definitie(did)

    assert _aanvullen(service, did, voor.version_number, doc_id="onbekend")[
        "status"
    ] == ("no_matching_source")
    assert _aanvullen(service, did, voor.version_number + 5)["status"] == (
        "version_conflict"
    )
    assert (
        _aanvullen(service, did, voor.version_number, actor="")["status"] == "no_actor"
    )
    assert _aanvullen(service, 99999, 1)["status"] == "not_found"
    assert _facade(repo).get_definitie(did).version_number == voor.version_number

    # Alleen-lezen status (eigen database: de duplicaatguard laat geen tweede
    # record voor hetzelfde begrip en dezelfde context toe).
    repo2 = DefinitionEditRepository(str(tmp_path / "vastgesteld.db"))
    vastgesteld = repo2.save(_record(status="established"))
    rec = _facade(repo2).get_definitie(vastgesteld)
    assert _aanvullen(_service(repo2), vastgesteld, rec.version_number)["status"] == (
        "not_editable"
    )
    assert (
        _facade(repo2).get_definitie(vastgesteld).version_number == rec.version_number
    )


def test_record_zonder_bronbewijs_kan_niet_worden_aangevuld(tmp_path):
    repo = _repo(tmp_path)
    did = repo.save(
        Definition(
            begrip=BEGRIP,
            definitie=P01_TEKST,
            categorie="resultaat",
            juridische_context=list(JUR),
            metadata={"status": "draft"},
        )
    )
    rec = _facade(repo).get_definitie(did)
    uit = _aanvullen(_service(repo), did, rec.version_number)
    assert uit["status"] == "no_evidence"
    assert _facade(repo).get_definitie(did).version_number == rec.version_number


def test_tweede_opgave_vult_aan_en_bewaart_de_eerste_in_de_historie(tmp_path):
    repo = _repo(tmp_path)
    did = repo.save(_record())
    service = _service(repo)
    rec = _facade(repo).get_definitie(did)
    assert _aanvullen(
        service, did, rec.version_number, source_version=None, locator=None
    )["status"] == ("applied")
    rec = _facade(repo).get_definitie(did)
    uit = _aanvullen(
        service,
        did,
        rec.version_number,
        url=None,
        actor="Tweede",
        source_version=P01_VERSIE,
    )
    assert uit["status"] == "applied"
    na = _facade(repo).get_definitie(did)
    doc = next(
        b for b in na.get_source_evidence()["sources"] if b["provider"] == "documents"
    )
    assert doc["url"] == P01_URL  # eerdere opgave blijft
    assert doc["source_version"] == P01_VERSIE
    assert doc[DECLARED_METADATA_KEY]["declared_by"] == "Tweede"
    assert len(na.get_source_evidence_history()) == 2


# ------------------------------------------------------------------ P01-keten


def test_p01_keten_metadata_en_nieuwe_beoordeling_behouden_na_opslaan_en_heropenen(
    tmp_path,
):
    """Aanvullen (DEF-808) → valideren → status review + opslaan (DEF-809) →
    heropenen: eindcriterium P01, zonder no-linkuitzondering."""
    repo = _repo(tmp_path)
    did = repo.save(_record(GEGENEREERDE_TEKST))
    service = _service(repo)

    # Editor: tekst exact P01, opslaan.
    geladen = _herladen(repo, did)
    assert service.save_definition(
        did,
        {
            "begrip": BEGRIP,
            "definitie": P01_TEKST,
            "organisatorische_context": [],
            "juridische_context": list(JUR),
            "wettelijke_basis": list(WET),
            "status": "draft",
            "version_number": geladen.metadata["version_number"],
        },
        user=ACTOR,
    )["success"]

    # Bronmetadata aanvullen op het bestaande record.
    rec = _facade(repo).get_definitie(did)
    assert _aanvullen(service, did, rec.version_number)["status"] == "applied"

    # Valideren: verse beoordeling voor exact P01 met de aangevulde bronset.
    geladen = _herladen(repo, did)
    bronnen = geladen.metadata["provenance_sources"]
    assert all(b.get("url") == P01_URL for b in bronnen if b["provider"] == "documents")
    nieuw = bouw_documentbeoordeling(P01_TEKST, bronnen)

    # Status review + opslaan met de nieuwe beoordeling.
    uit = service.save_definition(
        did,
        {
            "begrip": BEGRIP,
            "definitie": P01_TEKST,
            "organisatorische_context": [],
            "juridische_context": list(JUR),
            "wettelijke_basis": list(WET),
            "status": "review",
            "version_number": geladen.metadata["version_number"],
        },
        user=ACTOR,
        source_assessment=nieuw,
    )
    assert uit["success"] and uit["source_assessment_persisted"] is True

    # Heropenen: metadata, kandidaat en beoordeling behouden; verwijskwaliteit
    # voldoet via de echte hyperlinkregel — geen uitzondering vastgelegd.
    na = _facade(repo).get_definitie(did)
    assert na.status == "review"
    bewijs = na.get_source_evidence()
    assert bewijs["candidate"]["definitie"] == P01_TEKST
    assert bewijs["source_assessment"] == nieuw
    documenten = [b for b in bewijs["sources"] if b["provider"] == "documents"]
    assert all(
        (b["url"], b["source_version"], b["locator"])
        == (P01_URL, P01_VERSIE, P01_VINDPLAATS)
        for b in documenten
    )
    replay = _replay(na)
    assert replay["status"] == "pass"
    assert replay["review"]["assessment"]["applied"] is True
    assert replay["review"]["applied"] is False  # geen deskundige uitzondering nodig
    delen = {p["id"]: p for p in replay["parts"]}
    assert delen["reference_quality"]["status"] == "pass"
    assert delen["reference_quality"]["field"] == "source_assessment"
    assert na.get_source_evidence_status()["current"] is True
    # Readback via de service-adapter (wat Expert Review en export lezen).
    meta = _herladen(repo, did).metadata
    assert meta["source_assessment"] == nieuw
    assert meta["source_evidence"]["candidate"]["definitie"] == P01_TEKST
    assert (
        len(meta["source_evidence_history"]) == 2
    )  # generatie → correctie → hervalidatie
