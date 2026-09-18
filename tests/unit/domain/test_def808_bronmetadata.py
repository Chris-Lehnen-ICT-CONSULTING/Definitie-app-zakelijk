"""DEF-808 — opgegeven bronmetadata (hyperlink, bronversie, exacte vindplaats).

Pure domeinlogica, gedeeld door de uploadroute en de aanvulroute op een
opgeslagen record. Bewezen:

* validatie volgt de bestaande DEF-806-hyperlinkregel (`is_bruikbare_hyperlink`;
  interne http(s)-link volstaat), wijst ongeldige invoer zichtbaar af en levert
  dan niets op; zonder enige waarde is er geen metadata;
* toepassen zet `url`/`source_version`/`locator` op de bron én bewaart de
  herkomst (opgegeven door/op) herkenbaar apart; de invoer wordt niet gemuteerd;
* het broncontract leest de velden: canonieke identiteit draagt url, versie en
  vindplaats, de bronvingerafdruk verandert (een eerdere beoordeling vervalt);
* een opgegeven vindplaats telt ook naast een positie binnen het document.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from domain.sources.bronmetadata import (
    DECLARED_METADATA_KEY,
    Bronmetadata,
    pas_bronmetadata_toe,
    valideer_bronmetadata,
    vul_documentbronnen_aan,
)
from domain.sources.contract import bereken_bronvingerafdruk, is_bruikbare_hyperlink
from domain.sources.normalisatie import canoniseer_bronnen

pytestmark = [pytest.mark.unit]

P01_URL = (
    "https://wetten.overheid.nl/BWBR0005537/2026-08-15/0?g=2026-09-14&z=2026-09-14"
    "#Hoofdstuk1_Titeldeel1.1_Artikel1:3"
)
P01_VERSIE = "2026-08-15"
P01_VINDPLAATS = "artikel 1:3 lid 1 Awb"
DOC_ID = "01e121c20018eed2"
PASSAGE = (
    "Algemene wet bestuursrecht Artikel 1:3 1. Onder besluit wordt verstaan: een "
    "schriftelijke beslissing van een bestuursorgaan, inhoudende een "
    "publiekrechtelijke rechtshandeling."
)
DOCUMENTBRON = {
    "provider": "documents",
    "title": "awb-1-3-20260815.txt",
    "filename": "awb-1-3-20260815.txt",
    "doc_id": DOC_ID,
    "url": None,
    "snippet": PASSAGE,
    "score": 1.0,
    "selection_basis": "term_match",
    "used_in_prompt": True,
    "citation_label": None,
}
ANDERE_DOCUMENTBRON = {
    **DOCUMENTBRON,
    "doc_id": "ffffffffffffffff",
    "snippet": "Ander.",
}
RAGBRON = {"provider": "rag", "chunk_id": "c1", "snippet": "RAG.", "url": None}


# ------------------------------------------------------------------ validatie


def test_geldige_invoer_levert_metadata_met_herkomst():
    metadata, fouten = valideer_bronmetadata(
        f"  {P01_URL} ", P01_VERSIE, P01_VINDPLAATS, declared_by="Chris"
    )
    assert fouten == []
    assert isinstance(metadata, Bronmetadata)
    assert metadata.url == P01_URL  # getrimd
    assert metadata.source_version == P01_VERSIE
    assert metadata.locator == P01_VINDPLAATS
    assert metadata.declared_by == "Chris"
    assert metadata.declared_at  # tijdstip van opgave, nooit leeg
    assert is_bruikbare_hyperlink(metadata.url)


def test_interne_http_link_volstaat_besluit_1():
    metadata, fouten = valideer_bronmetadata("http://intern.example/awb", None, None)
    assert fouten == []
    assert metadata is not None and metadata.url == "http://intern.example/awb"


@pytest.mark.parametrize(
    "ongeldig",
    [
        "javascript:alert(1)",
        "intern.example/awb",
        "https://",
        "//host/pad",
        "https://host:99999/pad",
        "https://wetten.overheid.nl/BWB R0005537",
        "mailto:info@example.org",
        "file:///etc/passwd",
    ],
)
def test_ongeldige_hyperlink_wordt_zichtbaar_afgewezen(ongeldig):
    metadata, fouten = valideer_bronmetadata(ongeldig, P01_VERSIE, P01_VINDPLAATS)
    assert metadata is None
    assert len(fouten) == 1 and "hyperlink" in fouten[0].lower()
    # De ongeldige tekst wordt nooit stil weggelaten of als versie/vindplaats
    # doorgegeven: geen pass forceren, niets opleveren.


@pytest.mark.parametrize(
    ("url", "versie", "vindplaats"),
    [(None, None, None), ("", "  ", ""), (None, "", None)],
)
def test_zonder_enige_waarde_is_er_geen_metadata(url, versie, vindplaats):
    metadata, fouten = valideer_bronmetadata(url, versie, vindplaats)
    assert metadata is None
    assert fouten and "geen" in fouten[0].lower()


def test_alleen_versie_of_vindplaats_is_toegestaan_zonder_link():
    metadata, fouten = valideer_bronmetadata(None, P01_VERSIE, None)
    assert fouten == []
    assert metadata is not None
    assert metadata.url is None and metadata.source_version == P01_VERSIE


def test_bestaande_opgave_wordt_aangevuld_niet_gewist():
    eerder, _ = valideer_bronmetadata(P01_URL, None, None, declared_by="A")
    later, fouten = valideer_bronmetadata(
        None, P01_VERSIE, None, declared_by="B", bestaand=eerder.als_dict()
    )
    assert fouten == []
    assert later.url == P01_URL  # behouden uit de eerdere opgave
    assert later.source_version == P01_VERSIE
    assert later.declared_by == "B"  # herkomst is die van de laatste opgave


def test_als_dict_en_uit_dict_zijn_elkaars_inverse():
    metadata, _ = valideer_bronmetadata(P01_URL, P01_VERSIE, P01_VINDPLAATS)
    d = metadata.als_dict()
    assert set(d) == {"url", "source_version", "locator", "declared_by", "declared_at"}
    assert Bronmetadata.uit_dict(d) == metadata
    assert Bronmetadata.uit_dict(None) is None
    assert Bronmetadata.uit_dict({"url": None, "source_version": None}) is None


# ------------------------------------------------------------------ toepassen


def test_toepassen_zet_velden_en_bewaart_herkomst_zonder_de_invoer_te_muteren():
    metadata, _ = valideer_bronmetadata(
        P01_URL, P01_VERSIE, P01_VINDPLAATS, declared_by="Chris"
    )
    origineel = deepcopy(DOCUMENTBRON)
    bron = pas_bronmetadata_toe(origineel, metadata)
    assert origineel == DOCUMENTBRON  # niet gemuteerd
    assert bron["url"] == P01_URL
    assert bron["source_version"] == P01_VERSIE
    assert bron["locator"] == P01_VINDPLAATS
    # Herkenbaar als opgegeven metadata — geen authenticiteitsbewijs.
    assert bron[DECLARED_METADATA_KEY] == metadata.als_dict()
    # Alle andere velden (passage, kwitantieadministratie) blijven exact.
    for sleutel, waarde in DOCUMENTBRON.items():
        if sleutel != "url":
            assert bron[sleutel] == waarde


def test_contract_leest_opgegeven_url_versie_en_vindplaats_en_vingerafdruk_wijzigt():
    metadata, _ = valideer_bronmetadata(P01_URL, P01_VERSIE, P01_VINDPLAATS)
    voor = canoniseer_bronnen([DOCUMENTBRON])
    (na,) = canoniseer_bronnen([pas_bronmetadata_toe(DOCUMENTBRON, metadata)])
    assert voor[0].url is None and voor[0].version is None and voor[0].locator is None
    assert na.url == P01_URL
    assert na.version == P01_VERSIE
    assert na.locator == P01_VINDPLAATS
    assert na.source_id == voor[0].source_id == f"doc:{DOC_ID}"  # stabiele identiteit
    assert na.content_hash == voor[0].content_hash  # de passage is onaangeroerd
    assert is_bruikbare_hyperlink(na.url)
    contexten = {"juridische_context": ["Bestuursrecht"]}
    assert bereken_bronvingerafdruk("besluit", "x", contexten, voor) != (
        bereken_bronvingerafdruk("besluit", "x", contexten, (na,))
    )


def test_opgegeven_vindplaats_telt_ook_naast_positie_in_het_document():
    """Een pdf-passage draagt al `citation_label` (p. 3); de opgegeven exacte
    vindplaats mag daar niet stil achter verdwijnen."""
    metadata, _ = valideer_bronmetadata(None, None, P01_VINDPLAATS)
    pdf = {**DOCUMENTBRON, "citation_label": "p. 3"}
    (bron,) = canoniseer_bronnen([pas_bronmetadata_toe(pdf, metadata)])
    assert "p. 3" in bron.locator
    assert P01_VINDPLAATS in bron.locator
    # Ongewijzigd gedrag zonder opgave: alleen de positie.
    (kaal,) = canoniseer_bronnen([pdf])
    assert kaal.locator == "p. 3"


def test_vul_documentbronnen_aan_raakt_alleen_het_gekozen_document():
    metadata, _ = valideer_bronmetadata(P01_URL, P01_VERSIE, P01_VINDPLAATS)
    tweede_passage = {**DOCUMENTBRON, "snippet": "2. Onder beschikking wordt verstaan"}
    bronnen = [deepcopy(DOCUMENTBRON), RAGBRON, tweede_passage, ANDERE_DOCUMENTBRON]
    momentopname = deepcopy(bronnen)
    nieuw, aantal = vul_documentbronnen_aan(bronnen, DOC_ID, metadata)
    assert bronnen == momentopname
    assert aantal == 2
    assert [b.get("url") for b in nieuw] == [P01_URL, None, P01_URL, None]
    assert nieuw[1] == RAGBRON and nieuw[3] == ANDERE_DOCUMENTBRON
    assert all(DECLARED_METADATA_KEY in nieuw[i] for i in (0, 2))
    assert vul_documentbronnen_aan(bronnen, "onbekend", metadata) == (
        [deepcopy(b) for b in bronnen],
        0,
    )
