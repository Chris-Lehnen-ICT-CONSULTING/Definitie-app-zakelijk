"""DEF-808 — bronmetadata bij een geüpload document: opslaan, herladen, doorvoer.

* `DocumentProcessor.set_source_metadata` valideert met de gedeelde DEF-806-
  hyperlinkregel, bewaart de opgave herkenbaar (door/op) bij het document,
  schrijft haar naar het metadata-bestand en leest haar bij een nieuwe
  processor exact terug; ongeldige invoer wordt afgewezen zonder te schrijven;
  bestaande metadata-bestanden zonder de sleutel laden ongewijzigd.
* `DefinitionGenerationHandler._build_document_snippets` geeft de opgave door
  op elke passage van dat document (`url`, `source_version`, `locator` +
  herkomstblok); documenten zonder opgave blijven exact zoals voorheen.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from document_processing.document_processor import DocumentProcessor, ProcessedDocument
from domain.sources.bronmetadata import DECLARED_METADATA_KEY
from tests.fixtures.def808_p01 import P01_URL, P01_VERSIE, P01_VINDPLAATS
from ui.handlers.definition_generation_handler import DefinitionGenerationHandler

pytestmark = [pytest.mark.unit]

AWB_TEKST = (
    "Algemene wet bestuursrecht Artikel 1:3 1. Onder besluit wordt verstaan: een "
    "schriftelijke beslissing van een bestuursorgaan, inhoudende een "
    "publiekrechtelijke rechtshandeling. 2. Onder beschikking wordt verstaan: een "
    "besluit dat niet van algemene strekking is."
)


def _processor(tmp_path) -> DocumentProcessor:
    return DocumentProcessor(storage_dir=str(tmp_path / "docs"))


def _upload(
    processor: DocumentProcessor, naam: str = "awb-1-3-20260815"
) -> ProcessedDocument:
    with patch(
        "document_processing.document_processor.extract_text_from_file",
        return_value=AWB_TEKST,
    ):
        return processor.process_uploaded_file(
            file_content=AWB_TEKST.encode("utf-8"),
            filename=f"{naam}.txt",
            mime_type="text/plain",
        )


# ------------------------------------------------------------ processor/opslag


def test_upload_zonder_opgave_draagt_geen_metadata(tmp_path):
    doc = _upload(_processor(tmp_path))
    assert doc.processing_status == "success"
    assert doc.source_metadata is None


def test_opgave_wordt_bewaard_en_bij_herladen_exact_teruggelezen(tmp_path):
    processor = _processor(tmp_path)
    doc = _upload(processor)
    bijgewerkt = processor.set_source_metadata(
        doc.id,
        url=P01_URL,
        source_version=P01_VERSIE,
        locator=P01_VINDPLAATS,
        declared_by="Chris",
    )
    assert bijgewerkt.id == doc.id
    opgave = bijgewerkt.source_metadata
    assert opgave["url"] == P01_URL
    assert opgave["source_version"] == P01_VERSIE
    assert opgave["locator"] == P01_VINDPLAATS
    assert opgave["declared_by"] == "Chris" and opgave["declared_at"]
    # Op schijf én bij een nieuwe processor (herstart van de app).
    op_schijf = json.loads((tmp_path / "docs" / "documents_metadata.json").read_text())
    assert op_schijf["documents"][0]["source_metadata"] == opgave
    herladen = _processor(tmp_path).get_document_by_id(doc.id)
    assert herladen is not None and herladen.source_metadata == opgave
    assert herladen.extracted_text == AWB_TEKST  # document zelf onaangeroerd


@pytest.mark.parametrize(
    "ongeldig", ["javascript:alert(1)", "intern.example/awb", "https://"]
)
def test_ongeldige_hyperlink_wordt_afgewezen_zonder_te_schrijven(tmp_path, ongeldig):
    processor = _processor(tmp_path)
    doc = _upload(processor)
    with pytest.raises(ValueError, match=r"(?i)hyperlink"):
        processor.set_source_metadata(
            doc.id, url=ongeldig, source_version=None, locator=None
        )
    assert processor.get_document_by_id(doc.id).source_metadata is None
    assert _processor(tmp_path).get_document_by_id(doc.id).source_metadata is None


def test_zonder_enige_waarde_en_onbekend_document_worden_geweigerd(tmp_path):
    processor = _processor(tmp_path)
    doc = _upload(processor)
    with pytest.raises(ValueError, match="geen bronmetadata"):
        processor.set_source_metadata(doc.id, url="", source_version=" ", locator=None)
    with pytest.raises(KeyError, match="onbekend"):
        processor.set_source_metadata(
            "onbekend", url=P01_URL, source_version=None, locator=None
        )


def test_tweede_opgave_vult_aan_en_vervangt_de_herkomst(tmp_path):
    processor = _processor(tmp_path)
    doc = _upload(processor)
    processor.set_source_metadata(
        doc.id, url=P01_URL, source_version=None, locator=None, declared_by="A"
    )
    processor.set_source_metadata(
        doc.id, url=None, source_version=P01_VERSIE, locator=None, declared_by="B"
    )
    opgave = processor.get_document_by_id(doc.id).source_metadata
    assert opgave["url"] == P01_URL and opgave["source_version"] == P01_VERSIE
    assert opgave["declared_by"] == "B"


def _schrijffout_op_metadatabestand(tmp_path):
    """Echte schrijffout: `open(..., "w")` op het metadata-bestand faalt; lezen
    en alle andere bestanden blijven normaal werken (patroon
    test_document_processor_exceptions)."""
    import builtins

    metadata_pad = str(tmp_path / "docs" / "documents_metadata.json")
    origineel = builtins.open

    def _open(bestand, *args, **kwargs):
        modus = args[0] if args else kwargs.get("mode", "r")
        if str(bestand) == metadata_pad and "w" in str(modus):
            raise PermissionError(13, "Permission denied", metadata_pad)
        return origineel(bestand, *args, **kwargs)

    return patch("builtins.open", side_effect=_open)


def test_mislukte_opslag_wordt_gemeld_en_laat_geheugen_en_schijf_ongewijzigd(tmp_path):
    """Codex-review 1 (P2): een schrijffout mag geen stil succes zijn en geen
    opgave in het geheugen achterlaten die bij herstart ontbreekt."""
    from document_processing.document_processor import BronmetadataOpslagError

    processor = _processor(tmp_path)
    doc = _upload(processor)
    processor.set_source_metadata(
        doc.id, url=P01_URL, source_version=None, locator=None, declared_by="A"
    )
    eerder = dict(processor.get_document_by_id(doc.id).source_metadata)
    schijf_voor = (tmp_path / "docs" / "documents_metadata.json").read_text()

    with (
        _schrijffout_op_metadatabestand(tmp_path),
        pytest.raises(BronmetadataOpslagError, match="niet opgeslagen"),
    ):
        processor.set_source_metadata(
            doc.id,
            url=None,
            source_version=P01_VERSIE,
            locator=P01_VINDPLAATS,
            declared_by="B",
        )
    # Geheugen teruggerold naar de eerdere opgave; schijf onaangeroerd; de
    # persistentievlag signaleert het opslagprobleem (bestaand contract).
    assert processor.get_document_by_id(doc.id).source_metadata == eerder
    assert (tmp_path / "docs" / "documents_metadata.json").read_text() == schijf_voor
    assert processor._persistence_failed is True
    herladen = _processor(tmp_path).get_document_by_id(doc.id)
    assert herladen.source_metadata == eerder
    assert herladen.source_metadata["source_version"] is None


def test_mislukte_eerste_opslag_laat_geen_opgave_achter(tmp_path):
    from document_processing.document_processor import BronmetadataOpslagError

    processor = _processor(tmp_path)
    doc = _upload(processor)
    with (
        _schrijffout_op_metadatabestand(tmp_path),
        pytest.raises(BronmetadataOpslagError),
    ):
        processor.set_source_metadata(
            doc.id, url=P01_URL, source_version=None, locator=None
        )
    assert processor.get_document_by_id(doc.id).source_metadata is None
    assert _processor(tmp_path).get_document_by_id(doc.id).source_metadata is None
    # Een volgende geslaagde opslag werkt gewoon en herstelt de vlag.
    processor.set_source_metadata(
        doc.id, url=P01_URL, source_version=None, locator=None
    )
    assert processor._persistence_failed is False
    assert _processor(tmp_path).get_document_by_id(doc.id).source_metadata["url"] == (
        P01_URL
    )


def test_bestaand_metadatabestand_zonder_sleutel_laadt_ongewijzigd(tmp_path):
    processor = _processor(tmp_path)
    doc = _upload(processor)
    pad = tmp_path / "docs" / "documents_metadata.json"
    data = json.loads(pad.read_text())
    for item in data["documents"]:
        item.pop("source_metadata", None)  # de oude vorm van vóór DEF-808
    pad.write_text(json.dumps(data))
    herladen = _processor(tmp_path).get_document_by_id(doc.id)
    assert herladen is not None
    assert herladen.source_metadata is None
    assert herladen.filename == doc.filename


# ------------------------------------------------------------- doorvoer snippets


def _snippets(monkeypatch, doc, term="besluit"):
    monkeypatch.setattr(
        "ui.handlers.definition_generation_handler.get_document_processor",
        lambda: SimpleNamespace(get_document_by_id={doc.id: doc}.get),
    )
    handler = DefinitionGenerationHandler(None, None, None)
    return handler._build_document_snippets(term, [doc.id])


def test_opgave_reist_mee_op_elke_passage_van_het_document(monkeypatch, tmp_path):
    processor = _processor(tmp_path)
    doc = _upload(processor)
    processor.set_source_metadata(
        doc.id,
        url=P01_URL,
        source_version=P01_VERSIE,
        locator=P01_VINDPLAATS,
        declared_by="Chris",
    )
    snippets = _snippets(monkeypatch, processor.get_document_by_id(doc.id))
    assert len(snippets) >= 2  # 'besluit' komt meermaals voor
    for snippet in snippets:
        assert snippet["doc_id"] == doc.id
        assert snippet["url"] == P01_URL
        assert snippet["source_version"] == P01_VERSIE
        assert snippet["locator"] == P01_VINDPLAATS
        assert snippet[DECLARED_METADATA_KEY]["declared_by"] == "Chris"
        assert snippet["selection_basis"] == "term_match"
        assert "besluit" in snippet["snippet"].lower()


def test_document_zonder_opgave_levert_exact_de_oude_passagevorm(monkeypatch, tmp_path):
    doc = _upload(_processor(tmp_path))
    snippets = _snippets(monkeypatch, doc)
    assert snippets
    for snippet in snippets:
        assert "url" not in snippet
        assert "source_version" not in snippet
        assert "locator" not in snippet
        assert DECLARED_METADATA_KEY not in snippet


def test_document_object_zonder_attribuut_blijft_werken(monkeypatch):
    """Oudere/gemockte documentobjecten zonder `source_metadata`."""
    doc = SimpleNamespace(
        id="kaal", filename="kaal.txt", extracted_text=AWB_TEKST, mime_type="text/plain"
    )
    snippets = _snippets(monkeypatch, doc)
    assert snippets and all("url" not in s for s in snippets)
