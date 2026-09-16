"""DEF-743 pakket D: export van het opgeslagen bronbewijs (JSON/TXT/bulk).

Het opgeslagen record is de bron van waarheid: een export op alleen een ID,
met een vérse repository en exportservice (geen generatiesessie), draagt de
exacte bronset (citaten, coördinaten, geneste metadata), de AI-beoordeling
(delen, bewijs, onzekerheid, afgewezen bewijs, technische fout), de
deskundigenuitzondering (zichtbaar als uitzondering) en de stale-status.
Geen totaalcijfer en geen vervangende deelscore. Een record met alléén een
korte verwijzing exporteert dat als onvolledig bewijs; niets wordt verzonnen.
Aanvullende exportdata kan de bronvelden niet vervangen (K2-patroon).

Synthetische gegevens; offline; tijdelijke SQLite.
"""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository
from domain.sources.contract import bereken_bronvingerafdruk
from domain.sources.normalisatie import bereken_inhoudshash, canoniseer_bronnen
from services.data_aggregation_service import DataAggregationService
from services.definition_repository import DefinitionRepository
from services.export_service import ExportFormat, ExportLevel, ExportService
from services.interfaces import Definition

pytestmark = [pytest.mark.unit]

ACTOR = "synthetische-expert"
BEGRIP = "bestuursorgaan"
TEKST = "orgaan van een rechtspersoon die krachtens publiekrecht is ingesteld"
PASSAGE = (
    "Onder bestuursorgaan wordt verstaan: een orgaan van een rechtspersoon die "
    "krachtens publiekrecht is ingesteld"
)
CITAAT = "Onder bestuursorgaan wordt verstaan"
LOCATOR = "artikel 1:1, eerste lid, onderdeel a"

BRONNEN: list[dict[str, Any]] = [
    {
        "provider": "rag",
        "chunk_id": "chunk-awb-1-1",
        "document_id": "doc-awb",
        "title": "Awb artikel 1:1",
        "url": None,
        "snippet": PASSAGE,
        "score": 0.83,
        "metadata": {"coordinates": {"page": 3, "offset": 120}},
    },
    {
        "provider": "web",
        "title": "wetten.overheid.nl — Awb",
        "url": "https://wetten.overheid.nl/BWBR0005537/",
        "snippet": "Algemene wet bestuursrecht, hoofdstuk 1.",
        "score": 0.5,
    },
]


def _bron_id(index: int) -> str:
    [bron] = canoniseer_bronnen([BRONNEN[index]])
    return bron.source_id


def _beoordeling() -> dict[str, Any]:
    return {
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
                    {"source_id": _bron_id(0), "quote": CITAAT, "locator": None}
                ],
                # Zelfconsistent: een positief gezagsoordeel draagt zijn eigen
                # toepasselijke bron (kernreplay v5 eist dit).
                "sources": [
                    {
                        "source_id": _bron_id(0),
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


def _definition() -> Definition:
    return Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        categorie="ENT",
        organisatorische_context=["Stichting Zilver"],
        juridische_context=["bestuursrecht"],
        wettelijke_basis=["Awb"],
        metadata={
            "status": "review",
            "created_by": "generator",
            "sources": deepcopy(BRONNEN),
            "provenance_sources": deepcopy(BRONNEN),
            "source_receipt": {"version": "1", "status": "used", "sources": []},
            "source_assessment": _beoordeling(),
            "source_review": None,
            "definitie_eindtekst": TEKST,
            "peildatum": "2026-09-15",
        },
    )


def _opgeslagen_met_uitzondering(tmp_path: Path) -> tuple[Path, int]:
    pad = tmp_path / "export.db"
    repo = DefinitionRepository(str(pad))
    did = repo.save(_definition())
    rec = repo.get_definitie(did)
    assert rec is not None
    bewijs = rec.get_source_evidence() or {}
    assert repo.set_source_review(
        did,
        {
            "type": "reference_exception",
            "accepted": True,
            "actor": ACTOR,
            "rationale": "Intern raadpleegbaar via het documentbeheersysteem.",
            "version_number": rec.version_number,
            "fingerprint": bereken_bronvingerafdruk(
                rec.begrip,
                rec.get_definitie_tekst(),
                rec.get_contextlijsten(),
                bewijs.get("sources") or [],
                peildatum=bewijs.get("peildatum"),
            ),
            "source_id": _bron_id(0),
            "content_hash": bereken_inhoudshash(PASSAGE),
            "source_version": None,
            "locator": LOCATOR,
        },
        updated_by=ACTOR,
        expected_version=rec.version_number,
    )
    return pad, did


def _verse_export(pad: Path, export_dir: Path) -> ExportService:
    repo = DefinitieRepository(str(pad))
    return ExportService(
        repository=repo,
        data_aggregation_service=DataAggregationService(repo),
        export_dir=str(export_dir),
    )


def _geen_cijfer(obj: Any) -> None:
    """Nergens in beoordeling/uitzondering/status een kwaliteitscijfer of totaal.

    De aangeleverde bronrecords zelf (`sources`) blijven exact zoals
    aangeleverd, inclusief hun zoekscore: dat is zoekinformatie, geen
    kwaliteits- of gezagsoordeel, en wordt hier niet getoetst.
    """
    if isinstance(obj, dict):
        for sleutel, waarde in obj.items():
            if sleutel == "sources":
                continue
            assert sleutel not in {
                "overall_score",
                "total_score",
                "rule_scores",
            }, sleutel
            if sleutel == "score":
                assert waarde is None or isinstance(waarde, str), sleutel
            _geen_cijfer(waarde)
    elif isinstance(obj, list):
        for item in obj:
            _geen_cijfer(item)


class TestIndividueleExport:
    def test_json_export_op_id_draagt_het_opgeslagen_bronbewijs(self, tmp_path):
        pad, did = _opgeslagen_met_uitzondering(tmp_path)
        service = _verse_export(pad, tmp_path / "exports")
        bestand = Path(
            service.export_definitie(definitie_id=did, format=ExportFormat.JSON)
        )
        inhoud = json.loads(bestand.read_text(encoding="utf-8"))

        bewijs = inhoud["bronnen"]["bronbewijs"]
        assert bewijs["status"] == "present"
        assert bewijs["current"] is True
        assert bewijs["sources"] == BRONNEN
        assert bewijs["sources"][0]["metadata"]["coordinates"] == {
            "page": 3,
            "offset": 120,
        }
        beoordeling = bewijs["source_assessment"]
        assert (
            beoordeling["parts"]["source_authority"]["evidence"][0]["quote"] == CITAAT
        )
        assert beoordeling["parts"]["semantic_support"]["uncertainty"]
        assert beoordeling["rejected"][0]["reason"] == "citaat niet in bron"
        assert beoordeling["attribution"]["model"] == "synthetisch-model"
        review = bewijs["source_review"]
        assert review["type"] == "reference_exception"
        assert review["accepted"] is True
        assert review["locator"] == LOCATOR
        assert bewijs["source_review_status"]["status"] == "present"
        assert bewijs["peildatum"] == "2026-09-15"
        assert bewijs["history"] == []
        # De gewone bronnenlijst is uit het record afgeleid, niet uit een sessie.
        assert any("Awb artikel 1:1" in regel for regel in inhoud["bronnen"]["bronnen"])
        # Contractvelden komen van het record.
        assert inhoud["metadata"]["source_review"]["type"] == "reference_exception"
        assert inhoud["metadata"]["provenance_sources"] == BRONNEN
        _geen_cijfer(bewijs)

    def test_txt_export_op_id_toont_citaten_uitzondering_en_status(
        self, tmp_path, monkeypatch
    ):
        pad, did = _opgeslagen_met_uitzondering(tmp_path)
        monkeypatch.chdir(tmp_path)  # export_txt schrijft naar ./exports
        service = _verse_export(pad, tmp_path / "exports")
        bestand = Path(
            service.export_definitie(definitie_id=did, format=ExportFormat.TXT)
        )
        tekst = bestand.read_text(encoding="utf-8")

        assert "Awb artikel 1:1" in tekst
        assert PASSAGE in tekst
        assert CITAAT in tekst
        assert "Bronbeoordeling (CON-02)" in tekst
        assert "brongezag/toepasselijkheid" in tekst or "source_authority" in tekst
        assert "Uitzonderingen van artikel 1:1 lid 2 niet beoordeeld." in tekst
        assert "citaat niet in bron" in tekst
        assert "verwijzingsuitzondering" in tekst.lower()
        assert LOCATOR in tekst
        assert ACTOR in tekst
        assert "synthetisch-model" in tekst
        assert "totaalscore" not in tekst.lower()
        assert "score:" not in tekst.lower()

    def test_stale_bewijs_wordt_als_niet_actueel_geexporteerd(self, tmp_path):
        pad, did = _opgeslagen_met_uitzondering(tmp_path)
        repo = DefinitionRepository(str(pad))
        bewerkt = repo.get(did)
        bewerkt.definitie = TEKST + " (gewijzigd)"
        assert repo.save(bewerkt) == did

        service = _verse_export(pad, tmp_path / "exports")
        bestand = Path(
            service.export_definitie(definitie_id=did, format=ExportFormat.JSON)
        )
        bewijs = json.loads(bestand.read_text(encoding="utf-8"))["bronnen"][
            "bronbewijs"
        ]
        assert bewijs["current"] is False
        assert "definitie" in bewijs["reason"]
        assert bewijs["source_review_status"]["status"] == "stale"
        assert bewijs["sources"] == BRONNEN  # historisch bewijs blijft zichtbaar

    def test_reference_only_record_exporteert_onvolledig_bewijs(self, tmp_path):
        pad = tmp_path / "ref.db"
        repo = DefinitieRepository(str(pad))
        did = repo.create_definitie(
            DefinitieRecord(
                begrip=BEGRIP,
                definitie=TEKST,
                categorie="ENT",
                organisatorische_context='["Stichting Zilver"]',
                juridische_context='["bestuursrecht"]',
                wettelijke_basis='["Awb"]',
                source_reference="Awb art. 1:1",
            )
        )
        service = _verse_export(pad, tmp_path / "exports")
        bestand = Path(
            service.export_definitie(definitie_id=did, format=ExportFormat.JSON)
        )
        inhoud = json.loads(bestand.read_text(encoding="utf-8"))
        bewijs = inhoud["bronnen"]["bronbewijs"]
        assert bewijs["status"] == "reference_only"
        assert bewijs["current"] is False
        assert bewijs["source_reference"] == "Awb art. 1:1"
        assert bewijs["sources"] == []
        assert bewijs["source_assessment"] is None
        assert bewijs["source_review"] is None
        assert "provenance_sources" not in inhoud["metadata"]

    def test_aanvullende_data_kan_bronvelden_niet_vervangen(self, tmp_path):
        pad, did = _opgeslagen_met_uitzondering(tmp_path)
        service = _verse_export(pad, tmp_path / "exports")
        bestand = Path(
            service.export_definitie(
                definitie_id=did,
                format=ExportFormat.JSON,
                additional_data={
                    "metadata": {
                        "provenance_sources": [{"provider": "web", "url": "x"}],
                        "sources": [],
                        "source_assessment": {"status": "assessed", "parts": {}},
                        "source_review": {"type": "no_appropriate_source"},
                    },
                    "bronbewijs": {"status": "present", "sources": []},
                },
            )
        )
        inhoud = json.loads(bestand.read_text(encoding="utf-8"))
        assert inhoud["metadata"]["provenance_sources"] == BRONNEN
        assert inhoud["metadata"]["sources"] == BRONNEN
        assert inhoud["metadata"]["source_review"]["type"] == "reference_exception"
        assert inhoud["metadata"]["source_assessment"]["parts"]["source_authority"]
        assert inhoud["bronnen"]["bronbewijs"]["sources"] == BRONNEN


class TestBulkExport:
    def _records(self, tmp_path):
        pad, did = _opgeslagen_met_uitzondering(tmp_path)
        repo = DefinitieRepository(str(pad))
        return pad, [repo.get_definitie(did)]

    def test_bulk_json_en_csv_dragen_compact_bronbewijs(self, tmp_path):
        pad, records = self._records(tmp_path)
        service = _verse_export(pad, tmp_path / "exports")

        json_resultaat = service.export_multiple_definitions(
            records, format=ExportFormat.JSON, level=ExportLevel.UITGEBREID
        )
        [rij] = json.loads(Path(json_resultaat.path).read_text(encoding="utf-8"))[
            "definities"
        ]
        assert rij["bronbewijs"]["sources"] == BRONNEN
        assert rij["bronbewijs"]["source_review"]["type"] == "reference_exception"
        _geen_cijfer(rij["bronbewijs"])

        csv_resultaat = service.export_multiple_definitions(
            records, format=ExportFormat.CSV, level=ExportLevel.COMPLEET
        )
        with open(csv_resultaat.path, newline="", encoding="utf-8") as f:
            [csv_rij] = list(csv.DictReader(f))
        compact = json.loads(csv_rij["bronbewijs"])
        assert compact["sources"][0]["title"] == "Awb artikel 1:1"
        assert compact["source_review"]["locator"] == LOCATOR
        assert (
            compact["source_assessment"]["parts"]["source_authority"]["evidence"][0][
                "quote"
            ]
            == CITAAT
        )

    def test_bulk_txt_toont_bronbewijs_leesbaar(self, tmp_path):
        pad, records = self._records(tmp_path)
        service = _verse_export(pad, tmp_path / "exports")
        resultaat = service.export_multiple_definitions(
            records, format=ExportFormat.TXT, level=ExportLevel.UITGEBREID
        )
        tekst = Path(resultaat.path).read_text(encoding="utf-8")
        assert "Bronbewijs" in tekst
        assert "Awb artikel 1:1" in tekst
        assert CITAAT in tekst
        assert "verwijzingsuitzondering" in tekst.lower()
        assert LOCATOR in tekst

    def test_basisniveau_blijft_ongewijzigd_voor_externe_csv(self, tmp_path):
        pad, records = self._records(tmp_path)
        service = _verse_export(pad, tmp_path / "exports")
        resultaat = service.export_multiple_definitions(
            records, format=ExportFormat.CSV, level=ExportLevel.BASIS
        )
        with open(resultaat.path, newline="", encoding="utf-8") as f:
            kolommen = next(csv.reader(f))
        assert "bronbewijs" not in kolommen
        assert len(kolommen) == 17


# ------------------------------------------- Codex-reviewbevinding 3 + historie


def _gebonden_definition() -> Definition:
    """Zoals `_definition`, maar met een beoordeling die écht aan het record bindt."""
    d = _definition()
    vingerafdruk = bereken_bronvingerafdruk(
        BEGRIP,
        TEKST,
        {
            "organisatorische_context": ["Stichting Zilver"],
            "juridische_context": ["bestuursrecht"],
            "wettelijke_basis": ["Awb"],
        },
        BRONNEN,
        peildatum="2026-09-15",
    )
    d.metadata["source_assessment"]["fingerprint"] = vingerafdruk
    return d


class TestToepasbaarheidVanDeBeoordeling:
    def test_gebonden_beoordeling_is_toepasbaar_en_replay_is_de_actuele_uitkomst(
        self, tmp_path
    ):
        pad = tmp_path / "toepasbaar.db"
        did = DefinitionRepository(str(pad)).save(_gebonden_definition())
        service = _verse_export(pad, tmp_path / "exports")
        bestand = Path(
            service.export_definitie(definitie_id=did, format=ExportFormat.JSON)
        )
        bewijs = json.loads(bestand.read_text(encoding="utf-8"))["bronnen"][
            "bronbewijs"
        ]
        assert bewijs["current"] is True
        assert bewijs["source_assessment_status"]["applicable"] is True
        con02 = bewijs["con02"]
        assert con02["status"] == "review_required"  # twee onderdelen open
        statussen = {p["id"]: p["status"] for p in con02["parts"]}
        assert statussen["source_authority"] == "pass"
        assert statussen["semantic_support"] == "review_required"
        assert con02["review"]["assessment"]["applied"] is True
        assert con02["score"] is None

    def test_bronwijziging_zonder_herbeoordeling_maakt_beoordeling_niet_toepasbaar(
        self, tmp_path, monkeypatch
    ):
        pad = tmp_path / "stale.db"
        repo = DefinitionRepository(str(pad))
        did = repo.save(_gebonden_definition())
        herladen = repo.get(did)
        herladen.metadata["sources"][1]["url"] = "https://example.invalid/andere-awb"
        herladen.metadata["provenance_sources"] = deepcopy(herladen.metadata["sources"])
        assert repo.save(herladen) == did

        service = _verse_export(pad, tmp_path / "exports")
        bestand = Path(
            service.export_definitie(definitie_id=did, format=ExportFormat.JSON)
        )
        bewijs = json.loads(bestand.read_text(encoding="utf-8"))["bronnen"][
            "bronbewijs"
        ]
        # Bronset/kandidaat structureel actueel, maar de opgeslagen beoordeling
        # hoort bij de oude bronidentiteit: niet toepasbaar, met reden.
        assert bewijs["current"] is True
        assert bewijs["source_assessment_status"]["applicable"] is False
        assert bewijs["source_assessment_status"]["reason"]
        assert bewijs["con02"]["status"] == "review_required"
        assert all(p["status"] != "pass" for p in bewijs["con02"]["parts"])
        assert bewijs["con02"]["review"]["assessment"]["applied"] is False
        # De ruwe beoordeling blijft historisch zichtbaar.
        assert (
            bewijs["source_assessment"]["parts"]["source_authority"]["status"] == "pass"
        )

        monkeypatch.chdir(tmp_path)
        tekst = Path(
            service.export_definitie(definitie_id=did, format=ExportFormat.TXT)
        ).read_text(encoding="utf-8")
        assert "Actuele CON-02-uitkomst" in tekst
        assert "niet toepasbaar" in tekst
        actueel = tekst.split("Actuele CON-02-uitkomst", 1)[1].split(
            "Opgeslagen AI-bronbeoordeling", 1
        )[0]
        assert "voldoet" not in actueel.replace("voldoet niet", "").replace(
            "nog te beoordelen", ""
        )
        assert "historisch" in tekst

    def test_bulk_export_gebruikt_dezelfde_toepasbaarheid(self, tmp_path):
        pad = tmp_path / "bulk.db"
        repo = DefinitionRepository(str(pad))
        did = repo.save(_gebonden_definition())
        herladen = repo.get(did)
        herladen.metadata["peildatum"] = "2026-10-01"
        assert repo.save(herladen) == did
        records = [DefinitieRepository(str(pad)).get_definitie(did)]
        service = _verse_export(pad, tmp_path / "exports")
        resultaat = service.export_multiple_definitions(
            records, format=ExportFormat.JSON, level=ExportLevel.UITGEBREID
        )
        [rij] = json.loads(Path(resultaat.path).read_text(encoding="utf-8"))[
            "definities"
        ]
        assert rij["bronbewijs"]["source_assessment_status"]["applicable"] is False
        assert rij["bronbewijs"]["con02"]["status"] == "review_required"


class TestReviewhistorieInExport:
    def test_vervangen_review_staat_historisch_in_het_exportbewijs(self, tmp_path):
        pad, did = _opgeslagen_met_uitzondering(tmp_path)
        repo = DefinitionRepository(str(pad))
        rec = repo.get_definitie(did)
        bewijs = rec.get_source_evidence() or {}
        assert repo.set_source_review(
            did,
            {
                "type": "no_appropriate_source",
                "accepted": True,
                "actor": ACTOR,
                "rationale": "Toch geen passende bron.",
                "version_number": rec.version_number,
                "fingerprint": bereken_bronvingerafdruk(
                    rec.begrip,
                    rec.get_definitie_tekst(),
                    rec.get_contextlijsten(),
                    bewijs.get("sources") or [],
                    peildatum=bewijs.get("peildatum"),
                ),
                "search": {
                    "queries": ["bestuursorgaan"],
                    "consulted": ["wetten.overheid.nl"],
                    "conclusion": "Niets passends.",
                },
            },
            updated_by=ACTOR,
            expected_version=rec.version_number,
        )
        service = _verse_export(pad, tmp_path / "exports")
        inhoud = json.loads(
            Path(
                service.export_definitie(definitie_id=did, format=ExportFormat.JSON)
            ).read_text(encoding="utf-8")
        )
        bronbewijs = inhoud["bronnen"]["bronbewijs"]
        assert bronbewijs["source_review"]["type"] == "no_appropriate_source"
        [gebeurtenis] = bronbewijs["review_history"]
        assert gebeurtenis["event"] == "replaced"
        assert gebeurtenis["previous_review"]["type"] == "reference_exception"
        assert gebeurtenis["previous_review"]["locator"] == LOCATOR
        assert gebeurtenis["actor"] == ACTOR
        assert inhoud["metadata"]["source_review"]["type"] == "no_appropriate_source"


class TestDeelcorrectieInExport:
    def test_correctie_zichtbaar_als_correctie_in_replay_en_txt(
        self, tmp_path, monkeypatch
    ):
        pad = tmp_path / "correctie.db"
        repo = DefinitionRepository(str(pad))
        did = repo.save(_gebonden_definition())
        rec = repo.get_definitie(did)
        bewijs = rec.get_source_evidence() or {}
        assert repo.set_source_review(
            did,
            {
                "type": "part_correction",
                "accepted": True,
                "actor": ACTOR,
                "rationale": "De Awb-passage definieert het begrip letterlijk.",
                "version_number": rec.version_number,
                "fingerprint": bereken_bronvingerafdruk(
                    rec.begrip,
                    rec.get_definitie_tekst(),
                    rec.get_contextlijsten(),
                    bewijs.get("sources") or [],
                    peildatum=bewijs.get("peildatum"),
                ),
                "part_id": "semantic_support",
                "status": "pass",
                "evidence": [
                    {
                        "source_id": _bron_id(0),
                        "content_hash": bereken_inhoudshash(PASSAGE),
                        "source_version": None,
                        "quote": CITAAT,
                        "locator": None,
                    }
                ],
            },
            updated_by=ACTOR,
            expected_version=rec.version_number,
        )
        service = _verse_export(pad, tmp_path / "exports")
        bronbewijs = json.loads(
            Path(
                service.export_definitie(definitie_id=did, format=ExportFormat.JSON)
            ).read_text(encoding="utf-8")
        )["bronnen"]["bronbewijs"]
        con02 = bronbewijs["con02"]
        delen = {p["id"]: p for p in con02["parts"]}
        assert delen["semantic_support"]["status"] == "pass"
        assert delen["semantic_support"]["field"] == "source_review"
        assert con02["review"]["applied_correction"]["part_id"] == "semantic_support"
        assert con02["review"]["applied_correction"]["original"]["status"] == (
            "review_required"
        )
        assert con02["review"]["accepted_exception"] is None
        assert bronbewijs["source_review"]["type"] == "part_correction"

        monkeypatch.chdir(tmp_path)
        tekst = Path(
            service.export_definitie(definitie_id=did, format=ExportFormat.TXT)
        ).read_text(encoding="utf-8")
        assert "correctie van één AI-onderdeel" in tekst
        assert "betekenissteun" in tekst
        assert "oorspronkelijk ai-oordeel" in tekst.lower()


class TestAssessmentReceiptRoundtrip:
    """Additief veld `source_assessment.assessment_receipt` (kerncontract §5a).

    D projecteert niets: het volledige beoordelingsobject — inclusief dit
    voor D opake veld — overleeft opslaan → verse repository, ID-only
    herladen → JSON-export exact (inhoud, hashes, truncatievlag), als
    onafhankelijke kopie. Een kwitantie in de echte producer-vorm (de
    kern-`SourceAssessmentService`: string-versie, globale cap,
    hash-algoritme, `content == passage[:cap]`) is via de kernreplay
    toepasbaar; een afwijkende/ongeldige kwitantie blijft ruw bewaard maar is
    — terecht, zonder verzwakking van de kernguard — niet toepasbaar.
    """

    CAP = 40

    @classmethod
    def _geldige_ontvangst(cls) -> dict[str, Any]:
        """Exact de vorm die de kerndienst produceert, met de kernhelpers."""
        bronnen = canoniseer_bronnen(BRONNEN)
        return {
            "version": "1",
            "max_passage_chars": cls.CAP,
            "hash_algorithm": "sha256-utf8-hex",
            "sources": [
                {
                    "source_id": bron.source_id,
                    "original_content_hash": bron.content_hash,
                    "content": bron.passage[: cls.CAP],
                    "content_hash": bereken_inhoudshash(bron.passage[: cls.CAP]),
                    "truncated": len(bron.passage) > cls.CAP,
                    "source_version": bron.version,
                }
                for bron in bronnen
            ],
        }

    #: Bewust afwijkend van het contract (int-versie, geen hash_algorithm, cap
    #: 4000 maar afgekapte inhoud, per-item-cap): moet ruw bewaard blijven
    #: en door de replay als niet-toepasbaar worden gemarkeerd.
    ONGELDIGE_ONTVANGST = {
        "version": 1,
        "max_passage_chars": 4000,
        "sources": [
            {
                "source_id": "rag:doc-awb:chunk-awb-1-1",
                "original_content_hash": bereken_inhoudshash(PASSAGE),
                "content": PASSAGE[:40],
                "content_hash": bereken_inhoudshash(PASSAGE[:40]),
                "truncated": True,
                "max_passage_chars": 40,
                "source_version": None,
            }
        ],
    }

    @staticmethod
    def _opgeslagen_met_ontvangst(tmp_path, naam: str, ontvangst: dict[str, Any]):
        pad = tmp_path / naam
        definition = _gebonden_definition()
        definition.metadata["source_assessment"]["assessment_receipt"] = deepcopy(
            ontvangst
        )
        repo = DefinitionRepository(str(pad))
        did = repo.save(definition)
        # Onafhankelijkheid: invoer muteren na opslag raakt niets.
        definition.metadata["source_assessment"]["assessment_receipt"]["sources"][0][
            "content"
        ] = "GEMUTEERD"
        return pad, did

    def _export(self, pad, did, tmp_path) -> dict[str, Any]:
        service = _verse_export(pad, tmp_path / "exports")
        return json.loads(
            Path(
                service.export_definitie(definitie_id=did, format=ExportFormat.JSON)
            ).read_text(encoding="utf-8")
        )

    def test_roundtrip_via_opslag_herladen_en_json_export(self, tmp_path):
        ontvangst = self._geldige_ontvangst()
        assert ontvangst["sources"][0]["truncated"] is True
        assert CITAAT in ontvangst["sources"][0]["content"]  # in het verzonden deel
        pad, did = self._opgeslagen_met_ontvangst(tmp_path, "receipt.db", ontvangst)

        vers = DefinitionRepository(str(pad)).get(did)
        assert vers.metadata["source_assessment"]["assessment_receipt"] == ontvangst
        assert (
            vers.metadata["source_evidence"]["source_assessment"]["assessment_receipt"]
            == ontvangst
        )

        inhoud = self._export(pad, did, tmp_path)
        bewijs = inhoud["bronnen"]["bronbewijs"]
        geexporteerd = bewijs["source_assessment"]["assessment_receipt"]
        assert geexporteerd == ontvangst
        assert geexporteerd["sources"][0]["content"] == PASSAGE[: self.CAP]
        assert geexporteerd["sources"][0]["original_content_hash"] == (
            bereken_inhoudshash(PASSAGE)
        )
        assert (
            inhoud["metadata"]["source_assessment"]["assessment_receipt"] == ontvangst
        )
        # Geldige kwitantie: de beoordeling is toepasbaar en het citaat wordt
        # tegen de werkelijk verzonden passage geverifieerd (brongezag pass).
        assert bewijs["source_assessment_status"]["applicable"] is True
        statussen = {p["id"]: p["status"] for p in bewijs["con02"]["parts"]}
        assert statussen["source_authority"] == "pass"

    def test_ongeldige_kwitantie_blijft_ruw_bewaard_maar_is_niet_toepasbaar(
        self, tmp_path
    ):
        pad, did = self._opgeslagen_met_ontvangst(
            tmp_path, "ongeldig.db", self.ONGELDIGE_ONTVANGST
        )
        vers = DefinitionRepository(str(pad)).get(did)
        assert (
            vers.metadata["source_assessment"]["assessment_receipt"]
            == self.ONGELDIGE_ONTVANGST
        )
        inhoud = self._export(pad, did, tmp_path)
        bewijs = inhoud["bronnen"]["bronbewijs"]
        # Ruw en exact bewaard (historisch bewijs) ...
        assert bewijs["source_assessment"]["assessment_receipt"] == (
            self.ONGELDIGE_ONTVANGST
        )
        # ... maar niet toepasbaar: de kernguard weigert de kwitantie, met
        # reden; geen enkel onderdeel wordt daardoor een pass.
        assert bewijs["source_assessment_status"]["applicable"] is False
        assert bewijs["source_assessment_status"]["reason"]
        assert bewijs["con02"]["status"] == "review_required"
        assert all(p["status"] != "pass" for p in bewijs["con02"]["parts"])
