"""DEF-743 pakket D: duurzaam bronbewijs, herladen, expertuitzondering en voorstellen.

Alles via de publieke servicelaag (`DefinitionRepository`) op een tijdelijke,
echte SQLite-database (schema uit `schema.sql`), telkens herladen met een
vérse repository-instantie zodat niets van sessie- of objectstaat afhangt.

Bewezen (en niet meer dan dat):

* De rijke bronlijst (`sources`, incl. geneste metadata en dubbele
  aanvoerroutes), de promptkwitantie, de AI-bronbeoordeling en de tekststadia
  van de kandidaat overleven opslaan → ID-only herladen exact, onder C's
  sleutels (`sources` én `provenance_sources`, `source_assessment`,
  `source_review`).
* Een historisch record met alléén `source_reference` is onvolledig bewijs;
  er wordt niets bij verzonnen. Een serialisatiefout laat de opslag falen.
* Status-only wijziging behoudt een geldig gebonden CON-02-review; tekst-,
  term-, context- of bronwijziging maakt bewijs en review stale, met behoud
  van de historie. Een vervallen binding herleeft nooit.
* De deskundige uitzondering (C §5) wordt vóór schrijven geweigerd bij
  vervalste actor, verkeerd getypeerd versienummer, onbekende sleutels,
  ontbrekende vindplaats/bronhash/reden, ongedocumenteerd zoeken; bij
  versieconflict of afwijkende vingerafdruk wordt niets geschreven. CON-01
  en overige issues blijven staan; een mislukte transactie rolt terug.
* Handmatig voorstel (F-primitieven): één reservering per oorspronkelijke
  generatie (duurzaam, ook bij gelijktijdige versie), uitkomst verbruikt de
  poging, toepassen is atomair met versieguard, stale/vervalst wordt
  geweigerd, historie/bewijs/nieuwe versie kloppen na succes.

De vingerafdruk-, canoniserings- en reviewvalidatiehelpers zijn de échte van
kernpakket C (`domain.sources`); deze tests bewijzen de persistentiebinding
en de aansluiting daarop, niet C's vingerafdruksemantiek zelf. Synthetische
gegevens; geen uitspraak over modelkwaliteit of expertgoldset.
"""

from __future__ import annotations

import json
import threading
from copy import deepcopy
from typing import Any

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieStatus
from database.models import CONTEXT_REVIEW_CODE, SOURCE_REVIEW_CODE
from domain.sources.contract import bereken_bronvingerafdruk
from domain.sources.normalisatie import bereken_inhoudshash, canoniseer_bronnen
from services.definition_repository import DefinitionRepository
from services.exceptions import RepositoryError
from services.interfaces import Definition

pytestmark = [pytest.mark.unit]

ACTOR = "synthetische-expert"
BEGRIP = "bestuursorgaan"
TEKST = "orgaan van een rechtspersoon die krachtens publiekrecht is ingesteld"
ORG = ["Stichting Zilver"]
JUR = ["bestuursrecht"]
WET = ["Awb"]
PASSAGE = (
    "Onder bestuursorgaan wordt verstaan: een orgaan van een rechtspersoon die "
    "krachtens publiekrecht is ingesteld"
)

# Drie aanvoerroutes; de RAG-passage komt bewust óók via de documentroute
# binnen (dubbele route): beide worden exact bewaard, niets wordt ontdubbeld
# of verzonnen.
BRONNEN: list[dict[str, Any]] = [
    {
        "provider": "rag",
        "chunk_id": "chunk-awb-1-1",
        "document_id": "doc-awb",
        "chunk_index": 4,
        "title": "Awb artikel 1:1",
        "url": None,
        "snippet": PASSAGE,
        "score": 0.83,
        "metadata": {
            "coordinates": {"page": 3, "offset": 120, "length": 96},
            "nested": {"deep": ["a", {"b": 1}]},
        },
    },
    {
        "provider": "documents",
        "filename": "awb-uittreksel.pdf",
        "citation_label": "p. 3",
        "selection_basis": "term_match",
        "doc_id": 7,
        "title": "awb-uittreksel.pdf",
        "url": None,
        "snippet": PASSAGE,
        "score": 1.0,
    },
    {
        "provider": "web",
        "title": "wetten.overheid.nl — Awb",
        "url": "https://wetten.overheid.nl/BWBR0005537/",
        "snippet": "Algemene wet bestuursrecht, hoofdstuk 1.",
        "score": 0.5,
    },
]

KWITANTIE: dict[str, Any] = {
    "version": "1",
    "status": "used",
    "sources": [
        {
            "nr": 1,
            "source_type": "rag",
            "source_id": "chunk-awb-1-1",
            "identity": {"chunk_id": "chunk-awb-1-1", "document_id": "doc-awb"},
            "retrieval_score": 0.83,
            "content": PASSAGE,
            "content_hash": "sha256:abc",
            "sanitized": False,
            "truncated": False,
            "xml": '<bron nr="1" type="rag">…</bron>',
            "used_in_prompt": True,
        }
    ],
    "omitted": [{"source_type": "web", "source_id": None, "reason": "budget"}],
    "errors": [],
    "channels": {"rag": {"enabled": True, "supplied": 1, "used": 1}},
}

BEOORDELING: dict[str, Any] = {
    "contract_version": "con02/1",
    "prompt_version": "con02-assess/1",
    "fingerprint": "ai-vingerafdruk-synthetisch",
    "status": "assessed",
    "error": None,
    "assessed_at": "2026-09-15T12:00:00+00:00",
    "attribution": {
        "provider": "fake",
        "model": "synthetisch-model",
        "task_type": "validation",
        "cached": False,
        "tokens_used": 10,
    },
    "peildatum": "2026-09-15",
    "sources": [],
    "parts": {
        "source_authority": {
            "status": "pass",
            "reason": "Wettekst uit de Awb.",
            "uncertainty": None,
            "evidence": [
                {
                    "source_id": "rag:doc-awb:chunk-awb-1-1",
                    "quote": "Onder bestuursorgaan wordt verstaan",
                    "locator": None,
                }
            ],
            "sources": [
                {
                    "source_id": "rag:doc-awb:chunk-awb-1-1",
                    "profile": "wet_regelgeving",
                    "applicable": True,
                    "reason": "Awb.",
                }
            ],
        },
        "semantic_support": {
            "status": "review_required",
            "reason": "Dekking van uitzonderingen niet aangetoond.",
            "uncertainty": "Uitzonderingen van artikel 1:1 lid 2 niet beoordeeld.",
            "evidence": [],
            "claims": [],
        },
        "reference_quality": {
            "status": "review_required",
            "reason": "Geen bruikbare hyperlink.",
            "uncertainty": None,
            "evidence": [],
            "sources": [],
        },
    },
    "rejected": [
        {"part": "semantic_support", "reason": "citaat niet in bron", "detail": "x"}
    ],
    "raw_response_sha256": None,
}


# ------------------------------------------- C's echte helpers (geen nep-helper)


def _inhoudshash(passage: str) -> str:
    return bereken_inhoudshash(passage)


def _vingerafdruk(record: DefinitieRecord, tekst: str | None = None) -> str:
    """De bronvingerafdruk over het OPGESLAGEN record, met C's helper."""
    bewijs = record.get_source_evidence() or {}
    return bereken_bronvingerafdruk(
        record.begrip,
        record.get_definitie_tekst() if tekst is None else tekst,
        record.get_contextlijsten(),
        bewijs.get("sources") or [],
        peildatum=bewijs.get("peildatum"),
    )


def _bron_id(index: int) -> str:
    """Het door C afgeleide stabiele id van BRONNEN[index]."""
    [bron] = canoniseer_bronnen([BRONNEN[index]])
    return bron.source_id


def _repo(tmp_path, naam: str = "bronbewijs.db") -> DefinitionRepository:
    return DefinitionRepository(str(tmp_path / naam))


def _definition(**overrides: Any) -> Definition:
    metadata = {
        "status": DefinitieStatus.DRAFT.value,
        "created_by": "generator",
        "sources": deepcopy(BRONNEN),
        "source_receipt": deepcopy(KWITANTIE),
        "source_assessment": deepcopy(BEOORDELING),
        "source_review": None,
        "definitie_origineel": TEKST,
        "definitie_kern_geextraheerd": "Ontologische categorie: ENT\n" + TEKST,
        "definitie_eindtekst": TEKST,
        "tekst_na_generatie_aangepast": True,
        "generated_at": "2026-09-15T11:59:00+00:00",
        "peildatum": "2026-09-15",
    }
    metadata.update(overrides.pop("metadata", {}))
    velden: dict[str, Any] = {
        "begrip": BEGRIP,
        "definitie": TEKST,
        "categorie": "ENT",
        "organisatorische_context": list(ORG),
        "juridische_context": list(JUR),
        "wettelijke_basis": list(WET),
        "metadata": metadata,
    }
    velden.update(overrides)
    return Definition(**velden)


def _versie(repo: DefinitionRepository, did: int) -> int:
    rec = repo.get_definitie(did)
    assert rec is not None
    return int(rec.version_number)


def _verwijzingsuitzondering(repo: DefinitionRepository, did: int) -> dict[str, Any]:
    rec = repo.get_definitie(did)
    assert rec is not None
    # Platte, getypeerde vorm (coördinator-freeze punt 1).
    return {
        "type": "reference_exception",
        "accepted": True,
        "actor": ACTOR,
        "rationale": "Intern raadpleegbaar via het documentbeheersysteem.",
        "version_number": rec.version_number,
        "fingerprint": _vingerafdruk(rec),
        "reviewed_at": None,
        "source_id": _bron_id(0),
        "content_hash": _inhoudshash(PASSAGE),
        "source_version": None,
        "locator": "artikel 1:1, eerste lid, onderdeel a",
    }


def _geen_passende_bron(repo: DefinitionRepository, did: int) -> dict[str, Any]:
    rec = repo.get_definitie(did)
    assert rec is not None
    return {
        "type": "no_appropriate_source",
        "accepted": True,
        "actor": ACTOR,
        "rationale": "Organisatie-eigen term zonder authentieke bron.",
        "version_number": rec.version_number,
        "fingerprint": _vingerafdruk(rec),
        "search": {
            "queries": ["bestuursorgaan definitie", "Awb 1:1"],
            "consulted": ["wetten.overheid.nl", "intern begrippenregister"],
            "conclusion": "Geen passende bron gevonden.",
        },
    }


def _aantal(repo: DefinitionRepository) -> int:
    """Aantal records met het testbegrip (het schema bevat eigen seed-rijen)."""
    conn = repo.legacy_repo._db.get_connection()
    return int(
        conn.execute(
            "SELECT COUNT(*) FROM definities WHERE begrip = ?", (BEGRIP,)
        ).fetchone()[0]
    )


def _rij(repo: DefinitionRepository, did: int) -> dict[str, Any]:
    conn = repo.legacy_repo._db.get_connection()
    return dict(
        conn.execute("SELECT * FROM definities WHERE id = ?", (did,)).fetchone()
    )


# ----------------------------------------------------------------- opslag/herladen


class TestOpslaanEnHerladen:
    def test_bronbewijs_overleeft_opslaan_en_id_only_herladen(self, tmp_path):
        repo = _repo(tmp_path)
        definition = _definition()
        did = repo.save(definition)

        # Geneste bronmetadata is na opslag onafhankelijk van de invoer.
        definition.metadata["sources"][0]["metadata"]["nested"]["deep"][0] = "MUT"

        vers = _repo(tmp_path).get(did)
        assert vers is not None
        meta = vers.metadata
        assert meta["sources"] == BRONNEN
        assert meta["provenance_sources"] == BRONNEN
        assert meta["provenance_sources"] is not meta["sources"]
        assert meta["source_receipt"] == KWITANTIE
        assert meta["source_assessment"] == BEOORDELING
        assert meta["source_review"] is None
        assert meta["peildatum"] == "2026-09-15"
        bewijs = meta["source_evidence"]
        assert bewijs["candidate"] == {
            "definitie": TEKST,
            "definitie_origineel": TEKST,
            "definitie_kern_geextraheerd": "Ontologische categorie: ENT\n" + TEKST,
            "definitie_eindtekst": TEKST,
            "tekst_na_generatie_aangepast": True,
        }
        assert bewijs["context"] == {
            "organisatorische_context": ORG,
            "juridische_context": JUR,
            "wettelijke_basis": WET,
        }
        assert bewijs["begrip"] == BEGRIP
        assert bewijs["origin"] == "generation"
        assert bewijs["version_number"] == 1
        assert len(bewijs["generation_identity"]) == 64
        assert meta["source_evidence_status"] == {
            "status": "present",
            "current": True,
            "reason": None,
        }
        assert meta["source_evidence_history"] == []
        assert meta["source_proposals"] == []
        assert meta["source_review_status"]["status"] == "absent"

    def test_contractvelden_komen_uitsluitend_van_het_record(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        velden = _repo(tmp_path).get_definitie(did).get_contractvelden()
        assert velden["sources"] == BRONNEN
        assert velden["provenance_sources"] == BRONNEN
        assert velden["source_assessment"] == BEOORDELING
        assert velden["source_review"] is None
        assert velden["peildatum"] == "2026-09-15"
        assert velden["definition_version"] == 1
        assert velden["source_evidence_status"]["current"] is True

    def test_bewijs_wordt_ook_zonder_promptregistratie_bewaard(self, tmp_path):
        """Het bewijs hangt niet aan de aanwezigheid van `prompt_text` (DEF-151)."""
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        assert _rij(repo, did)["generation_prompt_data"] is not None
        assert _repo(tmp_path).get(did).metadata["sources"] == BRONNEN

    def test_bewijs_en_promptregistratie_delen_de_kolom(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(
            _definition(metadata={"prompt_text": "PROMPT", "model": "synthetisch"})
        )
        opgeslagen = json.loads(_rij(repo, did)["generation_prompt_data"])
        assert opgeslagen["prompt"] == "PROMPT"
        assert opgeslagen["definitie_eindtekst"] == TEKST
        assert opgeslagen["source_evidence"]["sources"] == BRONNEN
        assert repo.get_generation_prompt_data(did)["prompt"] == "PROMPT"

    def test_provenance_sources_canoniek_en_sources_alias(self, tmp_path):
        repo = _repo(tmp_path)
        definition = _definition()
        definition.metadata["provenance_sources"] = definition.metadata.pop("sources")
        did = repo.save(definition)
        meta = _repo(tmp_path).get(did).metadata
        assert meta["sources"] == BRONNEN
        assert meta["provenance_sources"] == BRONNEN

    def test_conflicterende_aliassen_worden_gesloten_geweigerd(self, tmp_path):
        """Beide sleutels aanwezig maar ongelijk: geen keuze maken (freeze punt 2)."""
        repo = _repo(tmp_path)
        definition = _definition()
        definition.metadata["provenance_sources"] = [deepcopy(BRONNEN[0])]
        with pytest.raises(RepositoryError, match="provenance_sources"):
            repo.save(definition)
        assert _aantal(repo) == 0
        # Ook bij een update: het opgeslagen bewijs blijft onaangeraakt.
        did = repo.save(_definition())
        herladen = repo.get(did)
        herladen.metadata["provenance_sources"] = [deepcopy(BRONNEN[0])]
        with pytest.raises(RepositoryError, match="provenance_sources"):
            repo.save(herladen)
        assert _repo(tmp_path).get(did).metadata["sources"] == BRONNEN

    def test_dubbele_routes_en_volgorde_blijven_exact(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        bronnen = _repo(tmp_path).get(did).metadata["sources"]
        assert [b["provider"] for b in bronnen] == ["rag", "documents", "web"]
        assert bronnen[0]["snippet"] == bronnen[1]["snippet"]
        assert bronnen[0]["metadata"]["coordinates"] == {
            "page": 3,
            "offset": 120,
            "length": 96,
        }

    def test_oud_record_met_alleen_source_reference_is_onvolledig(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.legacy_repo.create_definitie(
            DefinitieRecord(
                begrip=BEGRIP,
                definitie=TEKST,
                categorie="ENT",
                organisatorische_context=json.dumps(ORG),
                juridische_context=json.dumps(JUR),
                wettelijke_basis=json.dumps(WET),
                source_reference="Awb art. 1:1",
            )
        )
        vers = _repo(tmp_path).get(did)
        assert vers.bron == "Awb art. 1:1"
        assert vers.metadata["source_reference"] == "Awb art. 1:1"
        assert vers.metadata["source_evidence_status"]["status"] == "reference_only"
        assert vers.metadata["source_evidence_status"]["current"] is False
        assert "sources" not in vers.metadata
        assert "provenance_sources" not in vers.metadata
        assert "source_assessment" not in vers.metadata
        assert vers.metadata["source_review"] is None

    def test_record_zonder_bronnen_is_afwezig_niet_verzonnen(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(
            Definition(
                begrip=BEGRIP,
                definitie=TEKST,
                categorie="ENT",
                organisatorische_context=list(ORG),
                metadata={"status": "draft"},
            )
        )
        meta = _repo(tmp_path).get(did).metadata
        assert meta["source_evidence_status"] == {
            "status": "absent",
            "current": False,
            "reason": None,
        }
        assert "sources" not in meta

    def test_serialisatiefout_laat_opslag_falen_zonder_record(self, tmp_path):
        repo = _repo(tmp_path)
        kapot = _definition()
        kapot.metadata["sources"][0]["metadata"]["obj"] = object()
        with pytest.raises(RepositoryError, match="niet serialiseerbaar"):
            repo.save(kapot)
        assert _aantal(repo) == 0

    def test_misvormd_bewijs_in_kolom_is_expliciet_ongeldig(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        assert repo.legacy_repo.update_definitie(
            did,
            {"generation_prompt_data": json.dumps({"source_evidence": "kapot"})},
        )
        status = _repo(tmp_path).get(did).metadata["source_evidence_status"]
        assert status["status"] == "invalid"
        assert status["current"] is False
        assert status["reason"]

    def test_source_reference_korte_vorm_blijft_naast_bewijs(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition(metadata={"source_reference": "Awb art. 1:1"}))
        vers = _repo(tmp_path).get(did)
        assert vers.bron == "Awb art. 1:1"
        assert vers.metadata["sources"] == BRONNEN
        assert vers.metadata["source_evidence_status"]["status"] == "present"


# ------------------------------------------------------- status-only vs wijziging


class TestBindingBijWijzigingen:
    def _met_uitzondering(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        assert repo.set_source_review(
            did,
            _verwijzingsuitzondering(repo, did),
            updated_by=ACTOR,
            expected_version=_versie(repo, did),
        )
        return repo, did

    def test_uitzondering_wordt_gebonden_aan_opslagversie(self, tmp_path):
        repo, did = self._met_uitzondering(tmp_path)
        vers = _repo(tmp_path).get(did)
        review = vers.metadata["source_review"]
        assert review["type"] == "reference_exception"
        assert review["accepted"] is True
        assert review["actor"] == ACTOR
        assert review["rationale"]
        assert review["reviewed_at"]
        assert review["source_id"] == _bron_id(0)
        assert review["locator"] == "artikel 1:1, eerste lid, onderdeel a"
        assert review["version_number"] == 2 == vers.metadata["version_number"]
        assert vers.metadata["source_review_status"] == {
            "status": "present",
            "reason": None,
        }

    def test_statuswijziging_behoudt_bewijs_en_uitzondering(self, tmp_path):
        repo, did = self._met_uitzondering(tmp_path)
        assert repo.change_status(
            did, DefinitieStatus.REVIEW, ACTOR, expected_version=_versie(repo, did)
        )
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["version_number"] == 3
        assert vers.metadata["source_review"]["version_number"] == 3
        assert vers.metadata["source_review_status"]["status"] == "present"
        assert vers.metadata["source_evidence_status"]["current"] is True
        assert vers.metadata["source_evidence_history"] == []

    def test_vaststelling_behoudt_uitzondering_en_bewijs(self, tmp_path):
        repo, did = self._met_uitzondering(tmp_path)
        assert repo.change_status(
            did,
            DefinitieStatus.ESTABLISHED,
            ACTOR,
            expected_version=_versie(repo, did),
        )
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["status"] == DefinitieStatus.ESTABLISHED.value
        assert vers.metadata["source_review_status"]["status"] == "present"
        assert vers.metadata["source_evidence_status"]["current"] is True

    def test_con01_beoordeling_stalet_de_bronbinding_niet(self, tmp_path):
        """Een ongerelateerde CON-01-schrijfactie raakt tekst/context/bron niet."""
        from domain.context.contract import bereken_vingerafdruk

        repo, did = self._met_uitzondering(tmp_path)
        rec = repo.get_definitie(did)
        assert repo.set_context_review(
            did,
            {
                "fingerprint": bereken_vingerafdruk(
                    rec.begrip, rec.get_definitie_tekst(), rec.get_contextlijsten()
                ),
                "actor": ACTOR,
                "version_number": rec.version_number,
                "decisions": {},
            },
            updated_by=ACTOR,
            expected_version=rec.version_number,
        )
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["context_review"]["actor"] == ACTOR
        assert vers.metadata["source_review_status"]["status"] == "present"
        assert vers.metadata["source_review"]["version_number"] == 3

    def test_tekstwijziging_maakt_bewijs_en_uitzondering_stale(self, tmp_path):
        repo, did = self._met_uitzondering(tmp_path)
        bewerkt = repo.get(did)
        bewerkt.definitie = TEKST + " of een ander persoon met openbaar gezag"
        bewerkt.metadata["updated_by"] = "redacteur"
        assert repo.save(bewerkt) == did

        vers = _repo(tmp_path).get(did)
        status = vers.metadata["source_evidence_status"]
        assert status["status"] == "present"
        assert status["current"] is False
        assert "definitie" in status["reason"]
        # Het bewijs zelf blijft historisch beschikbaar, met de oude kandidaat.
        assert vers.metadata["sources"] == BRONNEN
        assert vers.metadata["source_evidence"]["candidate"]["definitie"] == TEKST
        assert vers.metadata["source_review_status"]["status"] == "stale"
        assert vers.metadata["source_review"]["version_number"] == 2

    def test_contextwijziging_maakt_binding_stale(self, tmp_path):
        repo, did = self._met_uitzondering(tmp_path)
        bewerkt = repo.get(did)
        bewerkt.juridische_context = ["strafrecht"]
        assert repo.save(bewerkt) == did
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_evidence_status"]["current"] is False
        assert vers.metadata["source_review_status"]["status"] == "stale"

    def test_termwijziging_maakt_binding_stale(self, tmp_path):
        repo, did = self._met_uitzondering(tmp_path)
        bewerkt = repo.get(did)
        bewerkt.begrip = "bestuursorganen"
        assert repo.save(bewerkt) == did
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_evidence_status"]["current"] is False
        assert vers.metadata["source_review_status"]["status"] == "stale"

    def test_bronwijziging_bewaart_historie_en_stalet_uitzondering(self, tmp_path):
        repo, did = self._met_uitzondering(tmp_path)
        nieuw = repo.get(did)
        nieuwe_bronnen = [deepcopy(BRONNEN[2])]
        nieuw.metadata["sources"] = nieuwe_bronnen
        nieuw.metadata["provenance_sources"] = deepcopy(nieuwe_bronnen)
        nieuw.metadata["source_assessment"] = {
            **deepcopy(BEOORDELING),
            "fingerprint": "ai-vingerafdruk-2",
        }
        nieuw.metadata["updated_by"] = "generator"
        assert repo.save(nieuw) == did

        vers = _repo(tmp_path).get(did)
        assert vers.metadata["sources"] == nieuwe_bronnen
        assert vers.metadata["source_assessment"]["fingerprint"] == "ai-vingerafdruk-2"
        assert vers.metadata["source_evidence_status"]["current"] is True
        historie = vers.metadata["source_evidence_history"]
        assert len(historie) == 1
        assert historie[0]["sources"] == BRONNEN
        assert historie[0]["superseded_on_version"] == 2
        assert historie[0]["superseded_at"]
        # De uitzondering hoorde bij de oude bronset: niet meer actueel.
        assert vers.metadata["source_review_status"]["status"] == "stale"

    def test_metadata_only_bronwijziging_telt_als_bronwijziging(self, tmp_path):
        """Andere URL/locator bij gelijke passage is een andere bronset (C-correctie 2)."""
        repo, did = self._met_uitzondering(tmp_path)
        nieuw = repo.get(did)
        nieuw.metadata["sources"][1]["citation_label"] = "p. 9"
        nieuw.metadata["provenance_sources"] = deepcopy(nieuw.metadata["sources"])
        assert repo.save(nieuw) == did
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["sources"][1]["citation_label"] == "p. 9"
        assert len(vers.metadata["source_evidence_history"]) == 1
        assert vers.metadata["source_review_status"]["status"] == "stale"

    def test_ongewijzigd_bewijs_bij_heropslag_maakt_geen_historie(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        herladen = repo.get(did)
        herladen.toelichting_proces = "notitie"
        assert repo.save(herladen) == did
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_evidence_history"] == []
        assert vers.metadata["source_evidence_status"]["current"] is True

    def test_update_zonder_bronsleutel_laat_bewijs_onaangeraakt(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        kaal = Definition(
            id=did,
            begrip=BEGRIP,
            definitie=TEKST,
            categorie="ENT",
            organisatorische_context=list(ORG),
            juridische_context=list(JUR),
            wettelijke_basis=list(WET),
            metadata={"status": "review"},
        )
        assert repo.save(kaal) == did
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["sources"] == BRONNEN
        assert vers.metadata["source_evidence_status"]["current"] is True

    def test_vervallen_binding_herleeft_niet_na_ongerelateerde_opslag(self, tmp_path):
        repo, did = self._met_uitzondering(tmp_path)
        bewerkt = repo.get(did)
        bewerkt.definitie = TEKST + " (gewijzigd)"
        assert repo.save(bewerkt) == did
        assert _repo(tmp_path).get(did).metadata["source_review_status"]["status"] == (
            "stale"
        )
        # Tekst terugzetten én daarna een status-only wijziging: blijft stale.
        terug = repo.get(did)
        terug.definitie = TEKST
        assert repo.save(terug) == did
        assert repo.change_status(
            did, DefinitieStatus.REVIEW, ACTOR, expected_version=_versie(repo, did)
        )
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_evidence_status"]["current"] is True
        assert vers.metadata["source_review_status"]["status"] == "stale"
        assert vers.metadata["source_review"]["version_number"] == 2


# ------------------------------------------------------------- expertbeoordeling


class TestExpertbeoordelingSafeguards:
    def _opgeslagen(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        return repo, did

    def _schrijf(self, repo, did, review, **kw):
        return repo.set_source_review(
            did,
            review,
            updated_by=kw.pop("updated_by", ACTOR),
            expected_version=kw.pop("expected_version", _versie(repo, did)),
        )

    def test_vervalste_actor_wordt_geweigerd_zonder_schrijven(self, tmp_path):
        repo, did = self._opgeslagen(tmp_path)
        review = {**_verwijzingsuitzondering(repo, did), "actor": "iemand-anders"}
        with pytest.raises(ValueError, match="handelende gebruiker"):
            self._schrijf(repo, did, review)
        assert _versie(repo, did) == 1
        assert repo.get_definitie(did).get_source_review() is None

    def test_ontbrekende_handelende_gebruiker_wordt_geweigerd(self, tmp_path):
        repo, did = self._opgeslagen(tmp_path)
        with pytest.raises(ValueError, match="updated_by"):
            self._schrijf(repo, did, _verwijzingsuitzondering(repo, did), updated_by="")

    @pytest.mark.parametrize("versie", [True, 1.0, "1", None])
    def test_versienummer_moet_strikt_geheel_getal_zijn(self, tmp_path, versie):
        repo, did = self._opgeslagen(tmp_path)
        review = {**_verwijzingsuitzondering(repo, did), "version_number": versie}
        with pytest.raises(ValueError, match="versienummer"):
            self._schrijf(repo, did, review)
        assert _versie(repo, did) == 1

    def test_expected_version_bool_wordt_geweigerd(self, tmp_path):
        repo, did = self._opgeslagen(tmp_path)
        with pytest.raises(ValueError, match="expected_version"):
            self._schrijf(
                repo, did, _verwijzingsuitzondering(repo, did), expected_version=True
            )
        assert _versie(repo, did) == 1

    @pytest.mark.parametrize("expected", [2, 0])
    def test_versieconflict_schrijft_niets(self, tmp_path, expected):
        repo, did = self._opgeslagen(tmp_path)
        review = {**_verwijzingsuitzondering(repo, did), "version_number": expected}
        assert self._schrijf(repo, did, review, expected_version=expected) is False
        assert _versie(repo, did) == 1
        assert repo.get_definitie(did).get_source_review() is None

    def test_afwijkende_vingerafdruk_schrijft_niets(self, tmp_path):
        repo, did = self._opgeslagen(tmp_path)
        review = {**_verwijzingsuitzondering(repo, did), "fingerprint": "vervalst"}
        assert self._schrijf(repo, did, review) is False
        assert _versie(repo, did) == 1
        assert repo.get_definitie(did).get_source_review() is None

    def test_vingerafdruk_wordt_over_het_opgeslagen_record_herberekend(self, tmp_path):
        """Een beoordeling over een ándere kandidaat (verouderde lezing) bindt niet."""
        repo, did = self._opgeslagen(tmp_path)
        review = _verwijzingsuitzondering(repo, did)
        bewerkt = repo.get(did)
        bewerkt.definitie = TEKST + " gewijzigd"
        assert repo.save(bewerkt) == did
        review["version_number"] = _versie(repo, did)
        assert self._schrijf(repo, did, review) is False
        assert repo.get_definitie(did).get_source_review() is None

    def test_zonder_kernhelpers_wordt_gesloten_gefaald(self, tmp_path, monkeypatch):
        import database.definitie_crud as crud

        repo = DefinitionRepository(str(tmp_path / "zonder.db"))
        did = repo.save(_definition())
        review = _verwijzingsuitzondering(repo, did)
        monkeypatch.setattr(
            crud, "_standaard_bronhelpers", lambda: (_ for _ in ()).throw(ImportError)
        )
        with pytest.raises(ValueError, match="kernhelpers"):
            repo.set_source_review(did, review, updated_by=ACTOR, expected_version=1)
        assert _versie(repo, did) == 1

    @pytest.mark.parametrize(
        ("veld", "waarde"),
        [
            # Inhoudelijke eisen komen van C's `valideer_bronreview`; D schrijft
            # dan niets en benoemt de reden. Geen generieke pass: type/accepted
            # zijn getypeerde velden, geen vrije statusvelden.
            ("type", "pass"),
            ("type", "part_review"),
            ("type", None),
            ("accepted", False),
            ("accepted", "ja"),
            ("accepted", None),
            ("rationale", "   "),
            ("rationale", None),
            ("locator", ""),
            ("locator", None),
            ("content_hash", ""),
            ("content_hash", "deadbeef"),
            ("source_id", "onbekend"),
            ("source_id", None),
            ("fingerprint", ""),
            ("fingerprint", None),
        ],
    )
    def test_onvolledige_verwijzingsuitzondering_wordt_geweigerd(
        self, tmp_path, veld, waarde
    ):
        repo, did = self._opgeslagen(tmp_path)
        review = {**_verwijzingsuitzondering(repo, did), veld: waarde}
        if veld == "fingerprint":
            # Vingerafdrukverschil is geen payloadfout maar een stale/vervalste
            # binding: geen exception, wel niets geschreven.
            assert self._schrijf(repo, did, review) is False
        else:
            with pytest.raises(ValueError, match="niet toepasbaar"):
                self._schrijf(repo, did, review)
        assert _versie(repo, did) == 1
        assert repo.get_definitie(did).get_source_review() is None

    def test_geen_passende_bron_vereist_gedocumenteerd_zoeken(self, tmp_path):
        repo, did = self._opgeslagen(tmp_path)
        basis = _geen_passende_bron(repo, did)
        for kapot in (
            {**basis, "search": None},
            {**basis, "search": {"queries": [], "consulted": [], "conclusion": ""}},
            {**basis, "search": {"queries": ["x"], "consulted": [], "conclusion": " "}},
            {**basis, "accepted": False},
            {**basis, "rationale": ""},
        ):
            with pytest.raises(ValueError, match="niet toepasbaar"):
                self._schrijf(repo, did, kapot)
        assert _versie(repo, did) == 1
        assert self._schrijf(repo, did, basis)
        review = _repo(tmp_path).get(did).metadata["source_review"]
        assert review["type"] == "no_appropriate_source"
        assert review["accepted"] is True
        assert review["search"]["queries"] == ["bestuursorgaan definitie", "Awb 1:1"]
        assert review["search"]["conclusion"] == "Geen passende bron gevonden."
        assert "source_id" not in review

    def test_geen_passende_bron_kan_zonder_opgeslagen_bronnen(self, tmp_path):
        """Precies dán is de uitzondering aan de orde: er is geen bron gevonden."""
        repo = _repo(tmp_path)
        did = repo.save(
            Definition(
                begrip=BEGRIP,
                definitie=TEKST,
                categorie="ENT",
                organisatorische_context=list(ORG),
                metadata={"status": "draft"},
            )
        )
        assert self._schrijf(repo, did, _geen_passende_bron(repo, did))
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_review"]["type"] == "no_appropriate_source"
        assert vers.metadata["source_review_status"]["status"] == "present"
        assert vers.metadata["source_evidence_status"]["status"] == "absent"

    def test_verwijzingsuitzondering_zonder_opgeslagen_bron_wordt_geweigerd(
        self, tmp_path
    ):
        repo = _repo(tmp_path)
        did = repo.save(
            Definition(
                begrip=BEGRIP,
                definitie=TEKST,
                categorie="ENT",
                organisatorische_context=list(ORG),
                metadata={"status": "draft"},
            )
        )
        rec = repo.get_definitie(did)
        review = {
            **_verwijzingsuitzondering(repo, did),
            "fingerprint": _vingerafdruk(rec),
            "version_number": rec.version_number,
        }
        with pytest.raises(ValueError, match="niet toepasbaar"):
            self._schrijf(repo, did, review)
        assert _versie(repo, did) == 1

    def test_beoordeling_bewaart_con01_en_overige_issues(self, tmp_path):
        from domain.context.contract import bereken_vingerafdruk

        repo, did = self._opgeslagen(tmp_path)
        assert repo.legacy_repo.update_definitie(
            did,
            {
                "validation_issues": json.dumps(
                    [{"code": "TAAL-01", "severity": "warning", "description": "x"}]
                )
            },
        )
        rec = repo.get_definitie(did)
        assert repo.set_context_review(
            did,
            {
                "fingerprint": bereken_vingerafdruk(
                    rec.begrip, rec.get_definitie_tekst(), rec.get_contextlijsten()
                ),
                "actor": ACTOR,
                "version_number": rec.version_number,
                "decisions": {},
            },
            updated_by=ACTOR,
            expected_version=rec.version_number,
        )
        assert self._schrijf(repo, did, _verwijzingsuitzondering(repo, did))

        vers = _repo(tmp_path).get_definitie(did)
        codes = [i.get("code") for i in vers.get_validation_issues_list()]
        assert codes.count("TAAL-01") == 1
        assert codes.count(CONTEXT_REVIEW_CODE) == 1
        assert codes.count(SOURCE_REVIEW_CODE) == 1
        assert vers.get_context_review()["actor"] == ACTOR
        assert vers.get_source_review()["type"] == "reference_exception"

        # Verwijderen raakt alleen de CON-02-marker.
        assert repo.set_source_review(
            did, None, updated_by=ACTOR, expected_version=_versie(repo, did)
        )
        vers = _repo(tmp_path).get_definitie(did)
        codes = [i.get("code") for i in vers.get_validation_issues_list()]
        assert SOURCE_REVIEW_CODE not in codes
        assert codes.count("TAAL-01") == 1
        assert codes.count(CONTEXT_REVIEW_CODE) == 1

    def test_dubbele_of_misvormde_markers_zijn_ongeldig(self, tmp_path):
        repo, did = self._opgeslagen(tmp_path)
        review = _verwijzingsuitzondering(repo, did)
        issues = [
            {"code": SOURCE_REVIEW_CODE, "rule_id": "CON-02", "source_review": review},
            {"code": SOURCE_REVIEW_CODE, "rule_id": "CON-02", "source_review": review},
        ]
        assert repo.legacy_repo.update_definitie(
            did, {"validation_issues": json.dumps(issues, ensure_ascii=False)}
        )
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_review"] is None
        assert vers.metadata["source_review_status"]["status"] == "invalid"
        assert "2" in vers.metadata["source_review_status"]["reason"]

        assert repo.legacy_repo.update_definitie(
            did,
            {
                "validation_issues": json.dumps(
                    [{"code": SOURCE_REVIEW_CODE, "source_review": "misvormd"}]
                )
            },
        )
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_review"] is None
        assert vers.metadata["source_review_status"]["status"] == "invalid"

    def test_mislukte_transactie_rolt_beoordeling_terug(self, tmp_path, monkeypatch):
        repo, did = self._opgeslagen(tmp_path)
        audit = repo.legacy_repo._crud._audit

        def _storing(*args, **kwargs):
            raise RuntimeError("synthetische auditstoring")

        monkeypatch.setattr(audit, "log_geschiedenis", _storing)
        with pytest.raises(RuntimeError):
            self._schrijf(repo, did, _verwijzingsuitzondering(repo, did))
        rij = _rij(repo, did)
        assert rij["version_number"] == 1
        assert not rij["validation_issues"]
        assert repo.get_definitie(did).get_source_review() is None


# ------------------------------------------------------------- AI-herbeoordeling


class TestHerbeoordeling:
    def test_set_source_assessment_vervangt_met_historie(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        rec = repo.get_definitie(did)
        nieuw = {**deepcopy(BEOORDELING), "fingerprint": _vingerafdruk(rec)}
        nieuw["parts"]["semantic_support"]["status"] = "pass"
        assert repo.set_source_assessment(
            did, nieuw, updated_by="validator", expected_version=rec.version_number
        )
        vers = _repo(tmp_path).get(did)
        assert (
            vers.metadata["source_assessment"]["parts"]["semantic_support"]["status"]
            == "pass"
        )
        bewijs = vers.metadata["source_evidence"]
        assert bewijs["origin"] == "revalidation"
        assert bewijs["generation_identity"] == (
            vers.metadata["source_evidence_history"][0]["generation_identity"]
        )
        assert vers.metadata["sources"] == BRONNEN
        assert vers.metadata["source_receipt"] == KWITANTIE
        assert vers.metadata["source_evidence_status"]["current"] is True
        assert len(vers.metadata["source_evidence_history"]) == 1
        assert (
            vers.metadata["source_evidence_history"][0]["source_assessment"]
            == BEOORDELING
        )

    def test_herbeoordeling_na_tekstwijziging_bindt_aan_actuele_tekst(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        bewerkt = repo.get(did)
        bewerkt.definitie = TEKST + " (bewerkt)"
        assert repo.save(bewerkt) == did
        assert (
            _repo(tmp_path).get(did).metadata["source_evidence_status"]["current"]
            is False
        )
        rec = repo.get_definitie(did)
        nieuw = {**deepcopy(BEOORDELING), "fingerprint": _vingerafdruk(rec)}
        assert repo.set_source_assessment(
            did, nieuw, updated_by="validator", expected_version=rec.version_number
        )
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_evidence_status"]["current"] is True
        assert vers.metadata["source_evidence"]["candidate"]["definitie"] == (
            TEKST + " (bewerkt)"
        )

    def test_set_source_assessment_weigert_afwijkende_vingerafdruk(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        assert (
            repo.set_source_assessment(
                did,
                {**deepcopy(BEOORDELING), "fingerprint": "anders"},
                updated_by="validator",
                expected_version=1,
            )
            is False
        )
        assert _repo(tmp_path).get(did).metadata["source_assessment"] == BEOORDELING
        assert _versie(repo, did) == 1


# ----------------------------------------------------------- handmatig voorstel


class TestVoorstelPrimitieven:
    KANDIDAAT = (
        TEKST + ", met uitzondering van de in artikel 1:1 lid 2 genoemde organen"
    )

    def _gereserveerd(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        res = repo.reserve_source_proposal(did, updated_by=ACTOR, expected_version=1)
        assert res.status == "reserved"
        return repo, did, res

    def _voorgesteld(self, tmp_path):
        repo, did, res = self._gereserveerd(tmp_path)
        assert repo.record_source_proposal_outcome(
            did,
            res.proposal_id,
            {
                "status": "proposed",
                "candidate_text": self.KANDIDAAT,
                "rationale": "Uitzondering uit artikel 1:1 lid 2 ontbrak.",
                "model": "synthetisch-model",
                "prompt_version": "con02-repair/1",
                "prompt_fingerprint": "pf-1",
            },
            updated_by=ACTOR,
            expected_version=res.version_number,
        )
        return repo, did, res

    def _gebonden_beoordeling(self, repo, did, tekst):
        return {
            **deepcopy(BEOORDELING),
            "fingerprint": _vingerafdruk(repo.get_definitie(did), tekst),
        }

    def test_reservering_is_duurzaam_en_eenmalig(self, tmp_path):
        repo, did, res = self._gereserveerd(tmp_path)
        assert res.proposal_id
        assert res.version_number == 2 == _versie(repo, did)
        assert len(res.generation_identity) == 64

        vers = _repo(tmp_path).get(did)
        [voorstel] = vers.metadata["source_proposals"]
        assert voorstel["proposal_id"] == res.proposal_id
        assert voorstel["status"] == "reserved"
        assert voorstel["actor"] == ACTOR
        assert voorstel["generation_identity"] == res.generation_identity
        assert voorstel["original"]["text"] == TEKST
        assert voorstel["original"]["fingerprint"] == _vingerafdruk(
            repo.get_definitie(did)
        )
        assert voorstel["outcome"] is None
        assert [e["event"] for e in voorstel["events"]] == ["reserved"]
        # Tweede reservering (rerun/reload/dubbelklik) is verbruikt, ook op de
        # nieuwe versie én na een herbeoordeling.
        opnieuw = _repo(tmp_path).reserve_source_proposal(
            did, updated_by=ACTOR, expected_version=_versie(repo, did)
        )
        assert opnieuw.status == "attempt_consumed"
        assert opnieuw.proposal_id == res.proposal_id
        rec = repo.get_definitie(did)
        assert repo.set_source_assessment(
            did,
            {**deepcopy(BEOORDELING), "fingerprint": _vingerafdruk(rec)},
            updated_by="validator",
            expected_version=rec.version_number,
        )
        assert (
            repo.reserve_source_proposal(
                did, updated_by=ACTOR, expected_version=_versie(repo, did)
            ).status
            == "attempt_consumed"
        )
        assert len(_repo(tmp_path).get(did).metadata["source_proposals"]) == 1

    def test_reservering_versieconflict_schrijft_niets(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        res = repo.reserve_source_proposal(did, updated_by=ACTOR, expected_version=5)
        assert res.status == "version_conflict"
        assert res.proposal_id is None
        assert _versie(repo, did) == 1
        assert _repo(tmp_path).get(did).metadata["source_proposals"] == []

    def test_reservering_vereist_bronbewijs(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(
            Definition(
                begrip=BEGRIP,
                definitie=TEKST,
                categorie="ENT",
                organisatorische_context=list(ORG),
                metadata={"status": "draft"},
            )
        )
        res = repo.reserve_source_proposal(did, updated_by=ACTOR, expected_version=1)
        assert res.status == "no_evidence"
        assert _versie(repo, did) == 1

    def test_gelijktijdige_reserveringen_laten_een_poging_over(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        pad = str(tmp_path / "bronbewijs.db")
        uitkomsten: list[str] = []
        start = threading.Barrier(2)

        def _poging():
            eigen = DefinitionRepository(pad)
            start.wait()
            uitkomsten.append(
                eigen.reserve_source_proposal(
                    did, updated_by=ACTOR, expected_version=1
                ).status
            )

        draden = [threading.Thread(target=_poging) for _ in range(2)]
        for d in draden:
            d.start()
        for d in draden:
            d.join()
        assert sorted(uitkomsten) == ["reserved", "version_conflict"]
        assert len(_repo(tmp_path).get(did).metadata["source_proposals"]) == 1

    def test_uitkomst_verbruikt_de_poging_ook_bij_fout(self, tmp_path):
        repo, did, res = self._gereserveerd(tmp_path)
        assert repo.record_source_proposal_outcome(
            did,
            res.proposal_id,
            {"status": "error", "error": {"type": "timeout", "message": "t"}},
            updated_by=ACTOR,
            expected_version=res.version_number,
        )
        vers = _repo(tmp_path).get(did)
        [voorstel] = vers.metadata["source_proposals"]
        assert voorstel["status"] == "error"
        assert voorstel["outcome"]["error"] == {"type": "timeout", "message": "t"}
        assert voorstel["original"]["text"] == TEKST
        assert [e["event"] for e in voorstel["events"]] == ["reserved", "error"]
        assert (
            repo.reserve_source_proposal(
                did, updated_by=ACTOR, expected_version=_versie(repo, did)
            ).status
            == "attempt_consumed"
        )
        # Een tweede uitkomst voor dezelfde reservering wordt niet geaccepteerd.
        assert (
            repo.record_source_proposal_outcome(
                did,
                res.proposal_id,
                {"status": "proposed", "candidate_text": "x", "rationale": "r"},
                updated_by=ACTOR,
                expected_version=_versie(repo, did),
            )
            is False
        )

    def test_uitkomst_valideert_payload_en_versie(self, tmp_path):
        repo, did, res = self._gereserveerd(tmp_path)
        with pytest.raises(ValueError, match="candidate_text"):
            repo.record_source_proposal_outcome(
                did,
                res.proposal_id,
                {"status": "proposed", "candidate_text": " ", "rationale": "r"},
                updated_by=ACTOR,
                expected_version=res.version_number,
            )
        with pytest.raises(ValueError, match="rationale"):
            repo.record_source_proposal_outcome(
                did,
                res.proposal_id,
                {"status": "proposed", "candidate_text": self.KANDIDAAT},
                updated_by=ACTOR,
                expected_version=res.version_number,
            )
        with pytest.raises(ValueError, match="status"):
            repo.record_source_proposal_outcome(
                did,
                res.proposal_id,
                {"status": "applied"},
                updated_by=ACTOR,
                expected_version=res.version_number,
            )
        assert (
            repo.record_source_proposal_outcome(
                did,
                res.proposal_id,
                {"status": "blocked", "findings": ["geen bewezen bronsteun"]},
                updated_by=ACTOR,
                expected_version=res.version_number + 1,
            )
            is False
        )
        assert _repo(tmp_path).get(did).metadata["source_proposals"][0]["status"] == (
            "reserved"
        )

    def _validatie(self, beoordeling: dict[str, Any], **over: Any) -> dict[str, Any]:
        """Een volledig validatieresultaat (bestaand contract, 1.4.0) over de kandidaat."""
        v: dict[str, Any] = {
            "version": "1.4.0",
            "overall_score": None,
            "is_acceptable": False,
            "violations": [],
            "passed_rules": ["TAAL-01"],
            "detailed_scores": {},
            "system": {"service": "test"},
            "validation_status": "validated",
            "validation_readiness": {
                "ready": True,
                "expected_total": 2,
                "loaded_total": 2,
                "missing_rule_ids": [],
                "unexpected_rule_ids": [],
            },
            "rule_statuses": {"TAAL-01": "pass", "CON-02": "review_required"},
            "evaluation_coverage": {
                "evaluated": 1,
                "passed": 1,
                "failed": 0,
                "review_required": 1,
                "not_evaluated": 0,
                "error": 0,
                "total": 2,
                "coverage_ratio": 0.5,
            },
            "rule_results": {
                "CON-02": {
                    "status": "review_required",
                    "score": None,
                    "fingerprint": beoordeling["fingerprint"],
                    "parts": [],
                    "review": None,
                }
            },
            "source_assessment": beoordeling,
        }
        v.update(over)
        return v

    def test_toepassen_is_atomair_met_historie_bewijs_en_nieuwe_versie(self, tmp_path):
        from domain.context.contract import bereken_vingerafdruk

        repo, did, res = self._voorgesteld(tmp_path)
        # Een geldige CON-01-review vóór het toepassen: moet vervallen (tekst).
        rec = repo.get_definitie(did)
        assert repo.set_context_review(
            did,
            {
                "fingerprint": bereken_vingerafdruk(
                    rec.begrip, rec.get_definitie_tekst(), rec.get_contextlijsten()
                ),
                "actor": ACTOR,
                "version_number": rec.version_number,
                "decisions": {},
            },
            updated_by=ACTOR,
            expected_version=rec.version_number,
        )
        versie_voor = _versie(repo, did)
        beoordeling = self._gebonden_beoordeling(repo, did, self.KANDIDAAT)
        toepassing = repo.apply_source_proposal(
            did,
            res.proposal_id,
            updated_by=ACTOR,
            expected_version=versie_voor,
            validation=self._validatie(beoordeling),
        )
        assert toepassing.status == "applied", toepassing.reason
        assert toepassing.version_number == versie_voor + 1

        vers = _repo(tmp_path).get(did)
        assert vers.definitie == self.KANDIDAAT
        assert vers.metadata["version_number"] == versie_voor + 1
        assert vers.metadata["validation_score"] is None
        bewijs = vers.metadata["source_evidence"]
        assert bewijs["origin"] == "proposal_applied"
        assert bewijs["candidate"]["definitie"] == self.KANDIDAAT
        assert bewijs["generation_identity"] == res.generation_identity
        assert vers.metadata["sources"] == BRONNEN
        assert vers.metadata["provenance_sources"] == BRONNEN
        assert vers.metadata["source_receipt"] == KWITANTIE
        assert vers.metadata["source_assessment"] == beoordeling
        assert vers.metadata["source_assessment"]["fingerprint"] == _vingerafdruk(
            repo.get_definitie(did)
        )
        assert vers.metadata["source_evidence_status"]["current"] is True
        [oud] = vers.metadata["source_evidence_history"]
        assert oud["candidate"]["definitie"] == TEKST
        assert oud["source_assessment"] == BEOORDELING
        [voorstel] = vers.metadata["source_proposals"]
        assert voorstel["status"] == "applied"
        assert voorstel["original"]["text"] == TEKST
        assert voorstel["outcome"]["candidate_text"] == self.KANDIDAAT
        assert voorstel["applied"]["version_number"] == versie_voor + 1
        assert voorstel["applied"]["validation"]["rule_statuses"]["CON-02"] == (
            "review_required"
        )
        assert [e["event"] for e in voorstel["events"]] == [
            "reserved",
            "proposed",
            "applied",
        ]
        # CON-01-review is vervallen (versie), niet verwijderd.
        assert vers.metadata["context_review"]["version_number"] == versie_voor
        # Geen tweede toepassing en geen nieuwe reservering.
        assert (
            repo.apply_source_proposal(
                did,
                res.proposal_id,
                updated_by=ACTOR,
                expected_version=_versie(repo, did),
                validation=self._validatie(self._gebonden_beoordeling(repo, did, "x")),
            ).status
            == "invalid_status"
        )
        assert (
            repo.reserve_source_proposal(
                did, updated_by=ACTOR, expected_version=_versie(repo, did)
            ).status
            == "attempt_consumed"
        )

    def test_toepassen_bewaart_toelichting_en_source_review_vervalt(self, tmp_path):
        repo, did, res = self._voorgesteld(tmp_path)
        assert repo.set_source_review(
            did,
            _verwijzingsuitzondering(repo, did),
            updated_by=ACTOR,
            expected_version=_versie(repo, did),
        )
        met_toelichting = repo.get(did)
        met_toelichting.toelichting = "Toelichting blijft."
        assert repo.save(met_toelichting) == did
        beoordeling = self._gebonden_beoordeling(repo, did, self.KANDIDAAT)
        toepassing = repo.apply_source_proposal(
            did,
            res.proposal_id,
            updated_by=ACTOR,
            expected_version=_versie(repo, did),
            validation=self._validatie(beoordeling),
        )
        assert toepassing.status == "applied", toepassing.reason
        vers = _repo(tmp_path).get(did)
        assert vers.definitie == self.KANDIDAAT
        assert vers.toelichting == "Toelichting blijft."
        assert vers.metadata["source_review_status"]["status"] == "stale"
        assert vers.metadata["source_review"]["type"] == "reference_exception"

    def test_expliciete_assessment_moet_gelijk_zijn_aan_resultaatveld(self, tmp_path):
        repo, did, res = self._voorgesteld(tmp_path)
        beoordeling = self._gebonden_beoordeling(repo, did, self.KANDIDAAT)
        andere = {**beoordeling, "assessed_at": "2026-09-16T00:00:00+00:00"}
        uitkomst = repo.apply_source_proposal(
            did,
            res.proposal_id,
            updated_by=ACTOR,
            expected_version=_versie(repo, did),
            validation=self._validatie(beoordeling),
            source_assessment=andere,
        )
        assert uitkomst.status == "assessment_not_bound"
        # Alleen de kwarg (resultaat zonder 1.4.0-veld) volstaat ook.
        uitkomst = repo.apply_source_proposal(
            did,
            res.proposal_id,
            updated_by=ACTOR,
            expected_version=_versie(repo, did),
            validation=self._validatie(beoordeling, source_assessment=None),
            source_assessment=beoordeling,
        )
        assert uitkomst.status == "applied", uitkomst.reason

    @pytest.mark.parametrize(
        ("mutatie", "verwacht"),
        [
            ("tekst", "stale_original"),
            ("context", "stale_original"),
            ("bron", "stale_original"),
            ("versie", "version_conflict"),
            ("beoordeling", "assessment_not_bound"),
            ("geen_beoordeling", "assessment_not_bound"),
            ("beoordeling_fout", "technical_error"),
            ("validatie_onbekend", "technical_error"),
            ("readiness", "technical_error"),
            ("dekking_error", "technical_error"),
            ("bronregel_not_evaluated", "technical_error"),
            ("regelstatus_error", "technical_error"),
            ("regelresultaat_error", "technical_error"),
            ("onbekend", "not_found"),
        ],
    )
    def test_stale_of_vervalste_toepassing_schrijft_niets(
        self, tmp_path, mutatie, verwacht
    ):
        repo, did, res = self._voorgesteld(tmp_path)
        proposal_id = res.proposal_id
        if mutatie == "tekst":
            d = repo.get(did)
            d.definitie = TEKST + " tussentijds bewerkt"
            assert repo.save(d) == did
        elif mutatie == "context":
            d = repo.get(did)
            d.wettelijke_basis = ["Awb", "Gemeentewet"]
            assert repo.save(d) == did
        elif mutatie == "bron":
            d = repo.get(did)
            d.metadata["sources"][2]["url"] = "https://example.invalid/"
            d.metadata["provenance_sources"] = deepcopy(d.metadata["sources"])
            assert repo.save(d) == did
        elif mutatie == "onbekend":
            proposal_id = "bestaat-niet"
        beoordeling = self._gebonden_beoordeling(repo, did, self.KANDIDAAT)
        validatie = self._validatie(beoordeling)
        if mutatie == "beoordeling":
            validatie["source_assessment"] = {**beoordeling, "fingerprint": "vervalst"}
        elif mutatie == "geen_beoordeling":
            validatie["source_assessment"] = None
        elif mutatie == "beoordeling_fout":
            validatie["source_assessment"] = {
                **beoordeling,
                "status": "error",
                "error": {"type": "timeout", "message": "t"},
            }
        elif mutatie == "validatie_onbekend":
            validatie["validation_status"] = "validation_unknown"
        elif mutatie == "readiness":
            validatie["validation_readiness"]["ready"] = False
        elif mutatie == "dekking_error":
            validatie["evaluation_coverage"]["error"] = 1
        elif mutatie == "bronregel_not_evaluated":
            validatie["rule_statuses"]["CON-02"] = "not_evaluated"
            validatie["evaluation_coverage"]["not_evaluated"] = 1
        elif mutatie == "regelstatus_error":
            validatie["rule_statuses"]["CON-02"] = "error"
        elif mutatie == "regelresultaat_error":
            validatie["rule_results"]["CON-02"]["status"] = "error"
        versie = _versie(repo, did)
        expected = versie + 1 if mutatie == "versie" else versie
        before = _rij(repo, did)

        uitkomst = repo.apply_source_proposal(
            did,
            proposal_id,
            updated_by=ACTOR,
            expected_version=expected,
            validation=validatie,
        )
        assert uitkomst.status == verwacht
        assert uitkomst.reason
        assert _rij(repo, did) == before
        [voorstel] = _repo(tmp_path).get(did).metadata["source_proposals"]
        assert voorstel["status"] == "proposed"

    def test_not_evaluated_van_andere_regel_is_geen_technische_fout(self, tmp_path):
        """SAM-regels zonder voorbeelden zijn bij tekstvalidatie regulier
        `not_evaluated` (bestaand contract); dat blokkeert het toepassen niet,
        maar blijft zichtbaar in het bewaarde resultaat."""
        repo, did, res = self._voorgesteld(tmp_path)
        validatie = self._validatie(
            self._gebonden_beoordeling(repo, did, self.KANDIDAAT)
        )
        validatie["rule_statuses"]["SAM-03"] = "not_evaluated"
        validatie["evaluation_coverage"]["not_evaluated"] = 1
        uitkomst = repo.apply_source_proposal(
            did,
            res.proposal_id,
            updated_by=ACTOR,
            expected_version=_versie(repo, did),
            validation=validatie,
        )
        assert uitkomst.status == "applied", uitkomst.reason
        [voorstel] = _repo(tmp_path).get(did).metadata["source_proposals"]
        assert voorstel["applied"]["validation"]["rule_statuses"]["SAM-03"] == (
            "not_evaluated"
        )

    def test_toepassen_zonder_validatie_is_een_payloadfout(self, tmp_path):
        repo, did, res = self._voorgesteld(tmp_path)
        with pytest.raises(ValueError, match="validation"):
            repo.apply_source_proposal(
                did,
                res.proposal_id,
                updated_by=ACTOR,
                expected_version=_versie(repo, did),
                validation=None,  # type: ignore[arg-type]
            )
        with pytest.raises(ValueError, match="expected_version"):
            repo.apply_source_proposal(
                did,
                res.proposal_id,
                updated_by=ACTOR,
                expected_version=True,
                validation=self._validatie(
                    self._gebonden_beoordeling(repo, did, self.KANDIDAAT)
                ),
            )
        assert _repo(tmp_path).get(did).definitie == TEKST

    def test_toepassen_faalt_gesloten_bij_transactiefout(self, tmp_path, monkeypatch):
        repo, did, res = self._voorgesteld(tmp_path)
        audit = repo.legacy_repo._crud._audit

        def _storing(*args, **kwargs):
            raise RuntimeError("synthetische auditstoring")

        monkeypatch.setattr(audit, "log_geschiedenis", _storing)
        before = _rij(repo, did)
        with pytest.raises(RuntimeError):
            repo.apply_source_proposal(
                did,
                res.proposal_id,
                updated_by=ACTOR,
                expected_version=_versie(repo, did),
                validation=self._validatie(
                    self._gebonden_beoordeling(repo, did, self.KANDIDAAT)
                ),
            )
        assert _rij(repo, did) == before

    def test_afwijzen_van_voorstel_bewaart_bewijs(self, tmp_path):
        repo, did, res = self._voorgesteld(tmp_path)
        assert repo.set_source_proposal_status(
            did,
            res.proposal_id,
            "rejected",
            updated_by=ACTOR,
            expected_version=_versie(repo, did),
            note="Te ruim.",
        )
        vers = _repo(tmp_path).get(did)
        [voorstel] = vers.metadata["source_proposals"]
        assert voorstel["status"] == "rejected"
        assert voorstel["outcome"]["candidate_text"] == self.KANDIDAAT
        laatste = voorstel["events"][-1]
        assert laatste["event"] == "rejected"
        assert laatste["note"] == "Te ruim."
        assert laatste["actor"] == ACTOR
        assert vers.definitie == TEKST
        with pytest.raises(ValueError, match="status"):
            repo.set_source_proposal_status(
                did,
                res.proposal_id,
                "applied",
                updated_by=ACTOR,
                expected_version=_versie(repo, did),
            )
        assert (
            repo.set_source_proposal_status(
                did,
                res.proposal_id,
                "superseded",
                updated_by=ACTOR,
                expected_version=_versie(repo, did),
            )
            is False
        )


# ------------------------------------------- Codex-reviewbevindingen (D-fix)


class TestReviewbevindingen:
    """Regressies uit de onafhankelijke Codex-review op pakket D.

    1. Toepassen publiceert de validatie-issues van de nieuwe kandidaat
       (oude overtredingen niet meer actueel; historie apart bewaard).
    2. De generatie-identiteit overleeft handmatige bron-/context-/
       peildatumcorrecties en herladen; alleen een echte nieuwe generatie
       krijgt een nieuwe identiteit (geen extra voorstelpoging).
    4. `get_contractvelden()` levert een onafhankelijke kopie van de
       kwitantie (`source_receipt`).
    Audit: vervangen/verwijderde CON-02-reviews blijven duurzaam in de
       generatieregistratie met actor/tijd/kandidaatbinding; verwijderen of
       terugzetten laat niets herleven.
    """

    KANDIDAAT = (
        TEKST + ", met uitzondering van de in artikel 1:1 lid 2 genoemde organen"
    )

    def _voorgesteld(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        res = repo.reserve_source_proposal(did, updated_by=ACTOR, expected_version=1)
        assert res.status == "reserved"
        assert repo.record_source_proposal_outcome(
            did,
            res.proposal_id,
            {
                "status": "proposed",
                "candidate_text": self.KANDIDAAT,
                "rationale": "Uitzondering ontbrak.",
            },
            updated_by=ACTOR,
            expected_version=res.version_number,
        )
        return repo, did, res

    def _validatie(self, repo, did, tekst, **over):
        beoordeling = {
            **deepcopy(BEOORDELING),
            "fingerprint": _vingerafdruk(repo.get_definitie(did), tekst),
        }
        v = TestVoorstelPrimitieven._validatie(TestVoorstelPrimitieven(), beoordeling)
        v.update(over)
        return v

    # ---- bevinding 1: validation_issues bij toepassen

    def test_toepassen_publiceert_nieuwe_issues_en_bewaart_oude_apart(self, tmp_path):
        from domain.context.contract import bereken_vingerafdruk

        repo, did, res = self._voorgesteld(tmp_path)
        assert repo.legacy_repo.update_definitie(
            did,
            {
                "validation_issues": json.dumps(
                    [
                        {
                            "code": "TAAL-01",
                            "rule_id": "TAAL-01",
                            "severity": "high",
                            "description": "oude overtreding",
                        }
                    ]
                )
            },
        )
        rec = repo.get_definitie(did)
        assert repo.set_context_review(
            did,
            {
                "fingerprint": bereken_vingerafdruk(
                    rec.begrip, rec.get_definitie_tekst(), rec.get_contextlijsten()
                ),
                "actor": ACTOR,
                "version_number": rec.version_number,
                "decisions": {},
            },
            updated_by=ACTOR,
            expected_version=rec.version_number,
        )
        validatie = self._validatie(
            repo,
            did,
            self.KANDIDAAT,
            violations=[
                {
                    "code": "STR-STR-002",
                    "rule_id": "STR-02",
                    "severity": "error",
                    "message": "nieuwe overtreding op de kandidaat",
                    "category": "structuur",
                }
            ],
            passed_rules=["TAAL-01"],
        )
        uitkomst = repo.apply_source_proposal(
            did,
            res.proposal_id,
            updated_by=ACTOR,
            expected_version=_versie(repo, did),
            validation=validatie,
        )
        assert uitkomst.status == "applied", uitkomst.reason

        vers = _repo(tmp_path).get_definitie(did)
        issues = vers.get_validation_issues_list()
        gewone = [
            i
            for i in issues
            if i.get("code") not in (CONTEXT_REVIEW_CODE, SOURCE_REVIEW_CODE)
        ]
        assert [i["rule_id"] for i in gewone] == ["STR-02"]
        assert gewone[0]["description"] == "nieuwe overtreding op de kandidaat"
        assert gewone[0]["severity"] == "error"
        assert gewone[0]["code"] == "STR-STR-002"
        # CON-01-marker blijft (vervallen door tekst, niet verwijderd).
        assert vers.get_context_review() is not None
        assert vers.get_context_review()["version_number"] != vers.version_number
        # Oude issues historisch bewaard bij het voorstel.
        [voorstel] = vers.get_source_proposals()
        assert [
            i["rule_id"] for i in voorstel["applied"]["previous_validation_issues"]
        ] == ["TAAL-01"]
        assert voorstel["applied"]["validation"]["passed_rules"] == ["TAAL-01"]
        assert _repo(tmp_path).get(did).metadata["validation_issues"] == issues

    def test_toepassen_zonder_overtredingen_maakt_issues_leeg(self, tmp_path):
        repo, did, res = self._voorgesteld(tmp_path)
        assert repo.legacy_repo.update_definitie(
            did,
            {
                "validation_issues": json.dumps(
                    [
                        {
                            "code": "TAAL-01",
                            "rule_id": "TAAL-01",
                            "severity": "high",
                            "description": "x",
                        }
                    ]
                )
            },
        )
        uitkomst = repo.apply_source_proposal(
            did,
            res.proposal_id,
            updated_by=ACTOR,
            expected_version=_versie(repo, did),
            validation=self._validatie(repo, did, self.KANDIDAAT, violations=[]),
        )
        assert uitkomst.status == "applied", uitkomst.reason
        vers = _repo(tmp_path).get_definitie(did)
        assert vers.get_validation_issues_list() == []

    # ---- bevinding 2: generatie-identiteit

    def test_identiteit_overleeft_correcties_en_herladen(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition(metadata={"generation_id": "gen-0001"}))
        eerste = repo.reserve_source_proposal(did, updated_by=ACTOR, expected_version=1)
        assert eerste.status == "reserved"
        assert eerste.generation_identity == "generation_id:gen-0001"
        assert repo.record_source_proposal_outcome(
            did,
            eerste.proposal_id,
            {"status": "error", "error": {"type": "timeout", "message": "t"}},
            updated_by=ACTOR,
            expected_version=eerste.version_number,
        )

        # Herladen herstelt de bestaande generation_id (niet verzonnen).
        herladen = _repo(tmp_path).get(did)
        assert herladen.metadata["generation_id"] == "gen-0001"

        # Peildatumcorrectie via herladen + opslaan.
        herladen.metadata["peildatum"] = "2026-10-01"
        assert repo.save(herladen) == did
        vers = _repo(tmp_path).get(did)
        assert (
            vers.metadata["source_evidence"]["generation_identity"]
            == "generation_id:gen-0001"
        )
        assert vers.metadata["source_evidence"]["origin"] == "correction"
        assert vers.metadata["peildatum"] == "2026-10-01"
        assert len(vers.metadata["source_evidence_history"]) == 1
        assert (
            repo.reserve_source_proposal(
                did, updated_by=ACTOR, expected_version=_versie(repo, did)
            ).status
            == "attempt_consumed"
        )

        # Locatorcorrectie van een bron.
        herladen = repo.get(did)
        herladen.metadata["sources"][1]["citation_label"] = "p. 4"
        herladen.metadata["provenance_sources"] = deepcopy(herladen.metadata["sources"])
        assert repo.save(herladen) == did
        vers = _repo(tmp_path).get(did)
        assert (
            vers.metadata["source_evidence"]["generation_identity"]
            == "generation_id:gen-0001"
        )
        assert (
            repo.reserve_source_proposal(
                did, updated_by=ACTOR, expected_version=_versie(repo, did)
            ).status
            == "attempt_consumed"
        )

        # Contextcorrectie + herbeoordeling wijzigen de identiteit evenmin.
        herladen = repo.get(did)
        herladen.juridische_context = ["strafrecht"]
        assert repo.save(herladen) == did
        rec = repo.get_definitie(did)
        assert repo.set_source_assessment(
            did,
            {**deepcopy(BEOORDELING), "fingerprint": _vingerafdruk(rec)},
            updated_by="validator",
            expected_version=rec.version_number,
        )
        assert (
            repo.reserve_source_proposal(
                did, updated_by=ACTOR, expected_version=_versie(repo, did)
            ).status
            == "attempt_consumed"
        )

        # Een echte nieuwe generatie (andere generation_id) is een nieuwe poging.
        opnieuw = repo.get(did)
        opnieuw.metadata["generation_id"] = "gen-0002"
        opnieuw.metadata["source_assessment"] = {
            **deepcopy(BEOORDELING),
            "fingerprint": "nieuw",
        }
        assert repo.save(opnieuw) == did
        vers = _repo(tmp_path).get(did)
        assert (
            vers.metadata["source_evidence"]["generation_identity"]
            == "generation_id:gen-0002"
        )
        assert vers.metadata["source_evidence"]["origin"] == "generation"
        assert vers.metadata["generation_id"] == "gen-0002"
        assert (
            repo.reserve_source_proposal(
                did, updated_by=ACTOR, expected_version=_versie(repo, did)
            ).status
            == "reserved"
        )

    def test_afgeleide_identiteit_overleeft_correcties_zonder_generation_id(
        self, tmp_path
    ):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        eerste = repo.reserve_source_proposal(did, updated_by=ACTOR, expected_version=1)
        assert eerste.status == "reserved"
        assert "generation_id" not in _repo(tmp_path).get(did).metadata

        herladen = repo.get(did)
        herladen.metadata["sources"][2]["url"] = "https://example.invalid/awb"
        herladen.metadata["provenance_sources"] = deepcopy(herladen.metadata["sources"])
        herladen.metadata["peildatum"] = "2026-10-02"
        assert repo.save(herladen) == did
        vers = _repo(tmp_path).get(did)
        assert (
            vers.metadata["source_evidence"]["generation_identity"]
            == eerste.generation_identity
        )
        assert (
            repo.reserve_source_proposal(
                did, updated_by=ACTOR, expected_version=_versie(repo, did)
            ).status
            == "attempt_consumed"
        )
        # Een echte regeneratie (nieuw generatietijdstip + nieuwe eindtekst) telt wel.
        nieuw = repo.get(did)
        nieuw.definitie = TEKST + " en bestuursorganen van de Staat"
        nieuw.metadata["definitie_eindtekst"] = nieuw.definitie
        nieuw.metadata["generated_at"] = "2026-09-16T08:00:00+00:00"
        nieuw.metadata["source_assessment"] = {
            **deepcopy(BEOORDELING),
            "fingerprint": "nieuw",
        }
        assert repo.save(nieuw) == did
        vers = _repo(tmp_path).get(did)
        assert (
            vers.metadata["source_evidence"]["generation_identity"]
            != eerste.generation_identity
        )
        assert vers.metadata["source_evidence"]["origin"] == "generation"
        assert (
            repo.reserve_source_proposal(
                did, updated_by=ACTOR, expected_version=_versie(repo, did)
            ).status
            == "reserved"
        )

    # ---- bevinding 4: kwitantie in contractvelden

    def test_contractvelden_dragen_onafhankelijke_kwitantie(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        rec = _repo(tmp_path).get_definitie(did)
        velden = rec.get_contractvelden()
        assert velden["source_receipt"] == KWITANTIE
        velden["source_receipt"]["sources"][0]["content"] = "GEMUTEERD"
        assert rec.get_contractvelden()["source_receipt"] == KWITANTIE
        assert rec.get_source_evidence()["source_receipt"] == KWITANTIE

    def test_contractvelden_zonder_bewijs_hebben_geen_kwitantie(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(
            Definition(
                begrip=BEGRIP,
                definitie=TEKST,
                categorie="ENT",
                organisatorische_context=list(ORG),
                metadata={"status": "draft"},
            )
        )
        assert (
            "source_receipt"
            not in _repo(tmp_path).get_definitie(did).get_contractvelden()
        )

    # ---- audit: reviewhistorie

    def test_vervangen_en_verwijderde_reviews_blijven_historisch(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        review1 = _verwijzingsuitzondering(repo, did)
        assert repo.set_source_review(
            did, review1, updated_by=ACTOR, expected_version=_versie(repo, did)
        )
        assert _repo(tmp_path).get(did).metadata["source_review_history"] == []
        vingerafdruk_bij_vervanging = _vingerafdruk(repo.get_definitie(did))

        review2 = _geen_passende_bron(repo, did)
        review2["version_number"] = _versie(repo, did)
        review2["actor"] = "tweede-expert"
        assert repo.set_source_review(
            did,
            review2,
            updated_by="tweede-expert",
            expected_version=_versie(repo, did),
        )

        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_review"]["type"] == "no_appropriate_source"
        [gebeurtenis] = vers.metadata["source_review_history"]
        assert gebeurtenis["event"] == "replaced"
        assert gebeurtenis["actor"] == "tweede-expert"
        assert gebeurtenis["at"]
        assert gebeurtenis["version_number"] == 2
        assert gebeurtenis["previous_status"] == "present"
        assert gebeurtenis["previous_review"]["type"] == "reference_exception"
        assert gebeurtenis["previous_review"]["actor"] == ACTOR
        assert gebeurtenis["previous_review"]["locator"] == review1["locator"]
        assert gebeurtenis["candidate"] == {
            "definitie": TEKST,
            "fingerprint": vingerafdruk_bij_vervanging,
        }
        assert gebeurtenis["new_review_type"] == "no_appropriate_source"

        # Verwijderen: tweede gebeurtenis; niets herleeft.
        assert repo.set_source_review(
            did, None, updated_by=ACTOR, expected_version=_versie(repo, did)
        )
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_review"] is None
        assert vers.metadata["source_review_status"]["status"] == "absent"
        historie = vers.metadata["source_review_history"]
        assert [g["event"] for g in historie] == ["replaced", "removed"]
        assert historie[1]["previous_review"]["type"] == "no_appropriate_source"
        assert historie[1]["new_review_type"] is None

        # Opnieuw vastleggen na verwijdering: alleen de nieuwe telt, historie groeit niet stil.
        review3 = _verwijzingsuitzondering(repo, did)
        assert repo.set_source_review(
            did, review3, updated_by=ACTOR, expected_version=_versie(repo, did)
        )
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_review"]["type"] == "reference_exception"
        assert (
            vers.metadata["source_review"]["version_number"]
            == vers.metadata["version_number"]
        )
        assert [g["event"] for g in vers.metadata["source_review_history"]] == [
            "replaced",
            "removed",
        ]

    def test_stale_review_vervangen_registreert_stale_als_vorige_status(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        assert repo.set_source_review(
            did,
            _verwijzingsuitzondering(repo, did),
            updated_by=ACTOR,
            expected_version=_versie(repo, did),
        )
        bewerkt = repo.get(did)
        bewerkt.definitie = TEKST + " (bewerkt)"
        assert repo.save(bewerkt) == did
        assert (
            _repo(tmp_path).get(did).metadata["source_review_status"]["status"]
            == "stale"
        )

        # Een verouderde (oude vingerafdruk) nieuwe review wordt geweigerd: niets geschreven.
        oud = _verwijzingsuitzondering(repo, did)
        oud["fingerprint"] = "verouderd"
        assert (
            repo.set_source_review(
                did, oud, updated_by=ACTOR, expected_version=_versie(repo, did)
            )
            is False
        )
        assert _repo(tmp_path).get(did).metadata["source_review_history"] == []

        nieuw = _verwijzingsuitzondering(repo, did)
        assert repo.set_source_review(
            did, nieuw, updated_by=ACTOR, expected_version=_versie(repo, did)
        )
        vers = _repo(tmp_path).get(did)
        [gebeurtenis] = vers.metadata["source_review_history"]
        assert gebeurtenis["event"] == "replaced"
        assert gebeurtenis["previous_status"] == "stale"
        assert gebeurtenis["candidate"]["definitie"] == TEKST + " (bewerkt)"
        assert vers.metadata["source_review_status"]["status"] == "present"

    def test_reviewhistorie_faalt_gesloten_bij_transactiefout(
        self, tmp_path, monkeypatch
    ):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        assert repo.set_source_review(
            did,
            _verwijzingsuitzondering(repo, did),
            updated_by=ACTOR,
            expected_version=_versie(repo, did),
        )
        audit = repo.legacy_repo._crud._audit
        monkeypatch.setattr(
            audit,
            "log_geschiedenis",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("storing")),
        )
        before = _rij(repo, did)
        review2 = _geen_passende_bron(repo, did)
        review2["version_number"] = _versie(repo, did)
        with pytest.raises(RuntimeError):
            repo.set_source_review(
                did, review2, updated_by=ACTOR, expected_version=_versie(repo, did)
            )
        assert _rij(repo, did) == before


# ------------------------------------------ part_correction (C §6b) via D


def _deelcorrectie(repo: DefinitionRepository, did: int, **over: Any) -> dict[str, Any]:
    rec = repo.get_definitie(did)
    assert rec is not None
    review = {
        "type": "part_correction",
        "accepted": True,
        "actor": ACTOR,
        "rationale": "De Awb-passage definieert het begrip letterlijk.",
        "version_number": rec.version_number,
        "fingerprint": _vingerafdruk(rec),
        "reviewed_at": None,
        "part_id": "semantic_support",
        "status": "pass",
        "evidence": [
            {
                "source_id": _bron_id(0),
                "content_hash": _inhoudshash(PASSAGE),
                "source_version": None,
                "quote": "Onder bestuursorgaan wordt verstaan",
                "locator": None,
            }
        ],
    }
    review.update(over)
    return review


class TestDeelcorrectieViaD:
    """D bewaart C's `part_correction`-payload via hetzelfde `set_source_review`.

    D valideert niets inhoudelijks zelf (C's `valideer_bronreview` is
    gezaghebbend); D bewaakt actor, versie, vingerafdruk over het opgeslagen
    record, historie en de stale-regels. Samenstelling van meerdere gelijk-
    tijdige correcties is bewust niet in D uitgevonden: één marker = één
    actuele review.
    """

    def test_roundtrip_en_stale(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        assert repo.set_source_review(
            did, _deelcorrectie(repo, did), updated_by=ACTOR, expected_version=1
        )
        vers = _repo(tmp_path).get(did)
        review = vers.metadata["source_review"]
        assert review["type"] == "part_correction"
        assert review["part_id"] == "semantic_support"
        assert review["status"] == "pass"
        assert review["evidence"][0]["quote"] == "Onder bestuursorgaan wordt verstaan"
        assert review["version_number"] == 2
        assert vers.metadata["source_review_status"]["status"] == "present"

        bewerkt = repo.get(did)
        bewerkt.definitie = TEKST + " (bewerkt)"
        assert repo.save(bewerkt) == did
        assert (
            _repo(tmp_path).get(did).metadata["source_review_status"]["status"]
            == "stale"
        )

    @pytest.mark.parametrize(
        "over",
        [
            {"actor": "iemand-anders"},
            {"accepted": False},
            {"part_id": "expert_exception:no_source"},
            {"status": "error"},
            {"evidence": []},  # pass zonder bewijs
            {
                "evidence": [
                    {"source_id": "onbekend", "content_hash": "x", "quote": "y"}
                ]
            },
            {"rationale": " "},
        ],
    )
    def test_ongeldige_correctie_wordt_geweigerd_zonder_schrijven(self, tmp_path, over):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        # D-actorcontrole ("handelende gebruiker") of C-inhoudelijke afwijzing
        # ("niet toepasbaar"): beide vóór mutatie.
        with pytest.raises(ValueError, match=r"niet toepasbaar|handelende gebruiker"):
            repo.set_source_review(
                did,
                _deelcorrectie(repo, did, **over),
                updated_by=ACTOR,
                expected_version=1,
            )
        assert _versie(repo, did) == 1
        assert repo.get_definitie(did).get_source_review() is None

    def test_correctie_vervangt_uitzondering_met_historie(self, tmp_path):
        repo = _repo(tmp_path)
        did = repo.save(_definition())
        assert repo.set_source_review(
            did,
            _verwijzingsuitzondering(repo, did),
            updated_by=ACTOR,
            expected_version=1,
        )
        assert repo.set_source_review(
            did, _deelcorrectie(repo, did), updated_by=ACTOR, expected_version=2
        )
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_review"]["type"] == "part_correction"
        [gebeurtenis] = vers.metadata["source_review_history"]
        assert gebeurtenis["previous_review"]["type"] == "reference_exception"
        assert gebeurtenis["new_review_type"] == "part_correction"


class TestNieuweGeneratieMetIdentiekBewijs:
    """Codex-follow-up (P2): een échte nieuwe generatie met identiek bewijs.

    De bewijsvergelijking (bronset/kwitantie/beoordeling/peildatum gelijk)
    mag de generatiecheck niet kortsluiten: een afwijkende expliciete
    `generation_id` — of zonder id een nieuwe generatieregistratie — is een
    nieuwe generatie met een eigen voorstelpoging, ook als het model exact
    hetzelfde bewijs opleverde. Handmatige bewerking en herbeoordeling
    blijven binnen dezelfde generatie (geen extra poging).
    """

    def _verbruikt(self, tmp_path, **metadata):
        repo = _repo(tmp_path)
        did = repo.save(_definition(metadata=metadata))
        eerste = repo.reserve_source_proposal(did, updated_by=ACTOR, expected_version=1)
        assert eerste.status == "reserved"
        assert repo.record_source_proposal_outcome(
            did,
            eerste.proposal_id,
            {"status": "error", "error": {"type": "timeout", "message": "t"}},
            updated_by=ACTOR,
            expected_version=eerste.version_number,
        )
        return repo, did, eerste

    def test_expliciete_nieuwe_generatie_met_identiek_bewijs_telt(self, tmp_path):
        repo, did, eerste = self._verbruikt(tmp_path, generation_id="gen-0001")
        assert eerste.generation_identity == "generation_id:gen-0001"

        herladen = _repo(tmp_path).get(did)
        assert herladen.metadata["generation_id"] == "gen-0001"
        assert herladen.metadata["sources"] == BRONNEN
        # Alleen de generatie-id verschilt; bronset, kwitantie, beoordeling en
        # peildatum zijn exact gelijk aan het opgeslagen bewijs.
        herladen.metadata["generation_id"] = "gen-0002"
        assert repo.save(herladen) == did

        vers = _repo(tmp_path).get(did)
        bewijs = vers.metadata["source_evidence"]
        assert bewijs["generation_identity"] == "generation_id:gen-0002"
        assert bewijs["generation_id"] == "gen-0002"
        assert bewijs["origin"] == "generation"
        assert vers.metadata["generation_id"] == "gen-0002"
        assert vers.metadata["sources"] == BRONNEN
        assert vers.metadata["source_assessment"] == BEOORDELING
        [oud] = vers.metadata["source_evidence_history"]
        assert oud["generation_identity"] == "generation_id:gen-0001"
        # De verbruikte poging hoort bij gen-0001; gen-0002 heeft een eigen poging.
        tweede = repo.reserve_source_proposal(
            did, updated_by=ACTOR, expected_version=_versie(repo, did)
        )
        assert tweede.status == "reserved"
        assert tweede.generation_identity == "generation_id:gen-0002"
        assert tweede.proposal_id != eerste.proposal_id
        assert len(_repo(tmp_path).get(did).metadata["source_proposals"]) == 2

    def test_zelfde_generatie_id_met_identiek_bewijs_blijft_verbruikt(self, tmp_path):
        """Tegenproef: identiek bewijs mét dezelfde id is géén nieuwe generatie."""
        repo, did, eerste = self._verbruikt(tmp_path, generation_id="gen-0001")
        herladen = _repo(tmp_path).get(did)
        herladen.toelichting_proces = "notitie"
        assert repo.save(herladen) == did
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_evidence"]["generation_identity"] == (
            "generation_id:gen-0001"
        )
        assert vers.metadata["source_evidence_history"] == []
        assert (
            repo.reserve_source_proposal(
                did, updated_by=ACTOR, expected_version=_versie(repo, did)
            ).status
            == "attempt_consumed"
        )

    def test_afgeleide_nieuwe_generatie_met_identiek_bewijs_telt(self, tmp_path):
        """Zonder expliciete id: een nieuwe generatieregistratie (tijdstip +
        eindtekst) met exact hetzelfde bewijs is eveneens een nieuwe generatie."""
        repo, did, eerste = self._verbruikt(tmp_path)
        herladen = _repo(tmp_path).get(did)
        herladen.metadata["definitie_eindtekst"] = TEKST
        herladen.metadata["generated_at"] = "2026-09-16T09:00:00+00:00"
        assert repo.save(herladen) == did
        vers = _repo(tmp_path).get(did)
        assert vers.metadata["source_evidence"]["generation_identity"] != (
            eerste.generation_identity
        )
        assert vers.metadata["source_evidence"]["origin"] == "generation"
        assert len(vers.metadata["source_evidence_history"]) == 1
        assert (
            repo.reserve_source_proposal(
                did, updated_by=ACTOR, expected_version=_versie(repo, did)
            ).status
            == "reserved"
        )
