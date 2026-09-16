"""CON-02 (DEF-743): canonieke bronidentiteit zonder verzonnen gegevens.

Zuivere domeintests: geen AI, geen database. Bewijzen dat een aangeleverde
bron (documents/rag/web) een stabiel id, een lokaal berekende inhoudshash en
uitsluitend wérkelijk aangeleverde coördinaten krijgt — en dat de invoer
onaangeroerd blijft.
"""

import hashlib
from copy import deepcopy

import pytest

from domain.sources.normalisatie import (
    PROFIEL_BELEID,
    PROFIEL_OVERIG,
    PROFIELEN,
    Bronidentiteit,
    bereken_inhoudshash,
    bron_op_id,
    canoniseer_bronnen,
)

pytestmark = [pytest.mark.unit]

PASSAGE = "Een bestuursorgaan is een orgaan van een rechtspersoon die krachtens publiekrecht is ingesteld."

DOCUMENT = {
    "provider": "documents",
    "doc_id": "upload-01",
    "filename": "awb.txt",
    "title": "awb.txt",
    "citation_label": "§ 1:1",
    "snippet": PASSAGE,
    "score": 1.0,
    "selection_basis": "term_match",
    "url": None,
}
RAG_CHUNK = {
    "provider": "rag",
    "chunk_id": 501,
    "document_id": 81,
    "chunk_index": 0,
    "created_at": "2026-09-14T10:00:00Z",
    "filename": "beleidsregel.txt",
    "bron_type": "beleid",
    "rechtsgebied": "Bestuursrecht",
    "wet_regeling": "Synthetische beleidsregel",
    "artikel_lid": "2",
    "metadata": {"pagina_nummer": 2, "locator": {"section": "Begrippen"}},
    "title": "Synthetische beleidsregel",
    "url": None,
    "snippet": "Onder toezichthouder wordt verstaan: de door het bestuur aangewezen persoon.",
    "score": 0.91,
    "legal": {"citation_text": "Bestuursrecht · Synthetische beleidsregel · 2"},
}
WEB = {
    "provider": "wikipedia",
    "title": "Bestuursorgaan",
    "url": "https://nl.wikipedia.org/wiki/Bestuursorgaan",
    "snippet": "Een bestuursorgaan is in Nederland een orgaan met openbaar gezag.",
    "score": 0.4,
    "retrieved_at": "2026-09-15T08:00:00Z",
}


def test_zes_profielen_zijn_de_goedgekeurde_set():
    assert PROFIELEN == (
        "wet_regelgeving",
        "beleid",
        "convenant",
        "norm_standaard",
        "vakpublicatie",
        "overig",
    )


def test_document_krijgt_stabiel_id_hash_en_locator_zonder_verzonnen_url():
    (bron,) = canoniseer_bronnen([DOCUMENT])
    assert isinstance(bron, Bronidentiteit)
    assert bron.source_id == "doc:upload-01"
    assert bron.provider == "documents"
    assert bron.title == "awb.txt"
    assert bron.locator == "§ 1:1"
    assert bron.url is None
    assert bron.version is None
    assert bron.passage == PASSAGE
    assert bron.content_hash == hashlib.sha256(PASSAGE.encode("utf-8")).hexdigest()
    assert bron.content_hash == bereken_inhoudshash(PASSAGE)
    # Geen bron_type aangeleverd: het profiel is onbekend, niet 'overig'.
    assert bron.declared_profile is None


def test_rag_chunk_behoudt_coordinaten_en_gedeclareerd_profiel_zonder_verzonnen_versie():
    (bron,) = canoniseer_bronnen([RAG_CHUNK])
    assert bron.source_id == "rag:81:501"
    # created_at is een observatie (wanneer de chunk is aangemaakt), geen
    # normatieve bronversie/-editie: die wordt niet verzonnen.
    assert bron.version is None
    assert bron.als_dict()["identity"]["created_at"] == "2026-09-14T10:00:00Z"
    assert bron.declared_profile == PROFIEL_BELEID
    # Alle aangeleverde vindplaatsdelen, geen verzonnen delen.
    assert "Bestuursrecht · Synthetische beleidsregel · 2" in bron.locator
    assert "p. 2" in bron.locator
    assert "section=Begrippen" in bron.locator
    assert bron.url is None


def test_webbron_gebruikt_url_als_identiteit_en_retrieved_at_is_observatie():
    (bron,) = canoniseer_bronnen([WEB])
    assert bron.source_id == "url:https://nl.wikipedia.org/wiki/Bestuursorgaan"
    assert bron.url == WEB["url"]
    assert bron.version is None
    assert bron.als_dict()["identity"]["retrieved_at"] == "2026-09-15T08:00:00Z"
    (met_versie,) = canoniseer_bronnen([{**WEB, "source_version": "2024-01"}])
    assert met_versie.version == "2024-01"
    assert bron.locator is None
    # Een aanvoerroute of zoekscore is geen gezag: er is geen 'authoritative'-veld.
    assert "authoritative" not in bron.als_dict()
    assert "score" not in bron.als_dict()


def test_expliciet_source_id_wint_en_hash_fallback_zonder_coordinaten():
    bewaard = {"source_id": "bewaard-7", "snippet": "Tekst.", "provider": "rag"}
    kaal = {"snippet": "Alleen tekst."}
    a, b = canoniseer_bronnen([kaal, bewaard])
    assert {a.source_id, b.source_id} == {
        "bewaard-7",
        "hash:" + bereken_inhoudshash("Alleen tekst.")[:16],
    }


def test_botsende_basis_id_met_andere_inhoud_krijgt_hash_suffix():
    eerste = {**DOCUMENT, "snippet": "Eerste passage."}
    tweede = {**DOCUMENT, "snippet": "Tweede passage."}
    bronnen = canoniseer_bronnen([eerste, tweede])
    ids = sorted(b.source_id for b in bronnen)
    assert len(ids) == 2
    assert all(i.startswith("doc:upload-01#") for i in ids)
    assert ids[0] != ids[1]


def test_exacte_duplicaten_worden_ontdubbeld_en_volgorde_is_deterministisch():
    bronnen = canoniseer_bronnen([WEB, DOCUMENT, deepcopy(DOCUMENT), RAG_CHUNK])
    assert [b.source_id for b in bronnen] == [
        "doc:upload-01",
        "rag:81:501",
        "url:https://nl.wikipedia.org/wiki/Bestuursorgaan",
    ]
    assert canoniseer_bronnen([RAG_CHUNK, WEB, DOCUMENT]) == bronnen


def test_invoer_wordt_diep_gekopieerd_en_niet_gemuteerd():
    invoer = [deepcopy(RAG_CHUNK)]
    momentopname = deepcopy(invoer)
    (bron,) = canoniseer_bronnen(invoer)
    assert invoer == momentopname
    # Geneste metadata van de invoer blijft onafhankelijk van het resultaat.
    invoer[0]["metadata"]["locator"]["section"] = "Gemuteerd"
    assert "section=Begrippen" in bron.locator


@pytest.mark.parametrize(
    "ruw",
    [None, "geen lijst", 7, [None, "tekst", 3, ["lijst"]]],
)
def test_niet_bruikbare_invoer_levert_geen_bronnen_en_geen_fout(ruw):
    assert canoniseer_bronnen(ruw) == ()


def test_bron_zonder_passage_blijft_zichtbaar_met_lege_inhoud():
    (bron,) = canoniseer_bronnen([{"provider": "documents", "doc_id": "leeg-1"}])
    assert bron.passage == ""
    assert bron.content_hash == bereken_inhoudshash("")


def test_onbekend_bron_type_wordt_overig_alleen_als_het_expliciet_is():
    (bron,) = canoniseer_bronnen([{**RAG_CHUNK, "bron_type": "krantenknipsel"}])
    assert bron.declared_profile == PROFIEL_OVERIG


def test_bron_op_id_vindt_alleen_bestaande_ids():
    bronnen = canoniseer_bronnen([DOCUMENT, WEB])
    assert bron_op_id(bronnen, "doc:upload-01").passage == PASSAGE
    assert bron_op_id(bronnen, "doc:verzonnen") is None


def test_als_dict_is_json_vriendelijk_en_volledig():
    (bron,) = canoniseer_bronnen([DOCUMENT])
    d = bron.als_dict()
    assert set(d) == {
        "source_id",
        "provider",
        "title",
        "url",
        "locator",
        "version",
        "content_hash",
        "declared_profile",
        "identity",
        "used_in_prompt",
    }
    assert (
        "passage" not in d
    )  # de passage zelf reist met de bronlijst, niet met de identiteit
    # citation_label is al in `locator` opgenomen; de overige feiten in identity.
    assert d["identity"] == {"doc_id": "upload-01", "filename": "awb.txt"}


def test_identity_bewaart_feitelijke_metadata_maar_geen_score_of_badges():
    verrijkt = {
        **RAG_CHUNK,
        "used_in_prompt": True,
        "is_authoritative": True,
        "source_label": "RAG: Synthetische beleidsregel",
        "confidence": 0.99,
        "issuer": "Synthetisch bestuur",
        "approval_status": "vastgesteld",
    }
    (bron,) = canoniseer_bronnen([verrijkt])
    identity = bron.als_dict()["identity"]
    for verboden in ("score", "used_in_prompt", "is_authoritative", "source_label"):
        assert verboden not in identity
    assert "confidence" not in identity
    assert identity["issuer"] == "Synthetisch bestuur"
    assert identity["approval_status"] == "vastgesteld"
    assert identity["metadata"] == RAG_CHUNK["metadata"]
    assert identity["metadata"] is not RAG_CHUNK["metadata"]
    assert bron.used_in_prompt is True


def test_prompt_content_is_de_passage_wanneer_aanwezig():
    """Positief bewijs moet in de werkelijk geleverde (gesanitiseerde/afgekapte) inhoud staan."""
    gebruikt = {
        **DOCUMENT,
        "prompt_content": "Een bestuursorgaan is een orgaan van een rechtspersoon",
        "used_in_prompt": True,
    }
    (bron,) = canoniseer_bronnen([gebruikt])
    assert bron.passage == "Een bestuursorgaan is een orgaan van een rechtspersoon"
    assert bron.content_hash == bereken_inhoudshash(bron.passage)
    (kaal,) = canoniseer_bronnen([DOCUMENT])
    assert kaal.content_hash != bron.content_hash


def test_zelfde_id_en_inhoud_met_andere_metadata_blijven_onderscheiden():
    """Invoervolgorde mag nooit bepalen welke identiteit 'de echte' is."""
    a = {**DOCUMENT, "source_version": "2024-01"}
    b = {**DOCUMENT, "source_version": "2025-01"}
    voor = canoniseer_bronnen([a, b])
    na = canoniseer_bronnen([b, a])
    assert voor == na
    assert len(voor) == 2
    assert len({x.source_id for x in voor}) == 2
    assert all(x.source_id.startswith("doc:upload-01#") for x in voor)
    assert {x.version for x in voor} == {"2024-01", "2025-01"}
    # bron_op_id levert precies de gevraagde variant, nooit een andere passage.
    for x in voor:
        assert bron_op_id(voor, x.source_id).version == x.version
    # Volledig identieke bronnen blijven wél ontdubbeld, zonder suffix.
    assert [x.source_id for x in canoniseer_bronnen([a, deepcopy(a)])] == [
        "doc:upload-01"
    ]


def test_correlatievelden_uit_de_kwitantie_zijn_niet_substantief():
    from domain.sources.contract import bereken_bronvingerafdruk

    kaal = bereken_bronvingerafdruk("t", "x", {}, [DOCUMENT])
    gekoppeld = bereken_bronvingerafdruk(
        "t",
        "x",
        {},
        [
            {
                **DOCUMENT,
                "input_index": 3,
                "original_content_hash": "sha256:abc",
                "receipt_nr": 2,
                "receipt_correlation": "verified",
                "prompt_content": PASSAGE,
                "prompt_content_hash": "x",
            }
        ],
    )
    assert kaal == gekoppeld


def _hash(tekst):
    return "sha256:" + hashlib.sha256(tekst.encode("utf-8")).hexdigest()


class TestKoppelKwitantieV2:
    """Kwitantie v2 van pakket E: (source_type, input_index) + original_content_hash."""

    DOC_A = {
        "doc_id": "doc1",
        "provider": "documents",
        "citation_label": "§ 1",
        "snippet": "Eerste passage doc1.",
        "score": 1.0,
    }
    DOC_B = {
        "doc_id": "doc1",
        "provider": "documents",
        "citation_label": "§ 2",
        "snippet": "Tweede passage doc1.",
        "score": 0.9,
    }
    RAG_X = {
        "provider": "rag",
        "document_id": 81,
        "snippet": "Gedeelde prefix alfa.",
        "score": 0.9,
    }
    RAG_Y = {
        "provider": "rag",
        "document_id": 81,
        "snippet": "Gedeelde prefix beta.",
        "score": 0.8,
    }
    WEB_1 = {
        "provider": "wikipedia",
        "url": "https://w/x",
        "title": "Een",
        "snippet": "<p>Web & een</p>",
        "score": 0.5,
    }
    WEB_2 = {
        "provider": "wikipedia",
        "url": "https://w/x",
        "title": "Twee",
        "snippet": "Web twee.",
        "score": 0.4,
    }

    def _record(self, nr, soort, ident, index, origineel, content, **extra):
        return {
            "nr": nr,
            "source_type": soort,
            "source_id": ident,
            "input_index": index,
            "original_content_hash": _hash(origineel),
            "identity": {},
            "retrieval_score": None,
            "content": content,
            "content_hash": _hash(content),
            "sanitized": content != origineel and not extra.get("truncated", False),
            "truncated": extra.get("truncated", False),
            "xml": "<bron/>",
            "used_in_prompt": True,
        }

    def _omitted(self, soort, ident, index, origineel, reden):
        return {
            "source_type": soort,
            "source_id": ident,
            "input_index": index,
            "original_content_hash": _hash(origineel),
            "identity": {},
            "reason": reden,
        }

    def _receipt(self, sources, omitted=(), errors=()):
        return {
            "version": "2",
            "status": "used" if sources else "none",
            "sources": list(sources),
            "omitted": list(omitted),
            "errors": list(errors),
            "channels": {},
        }

    def test_dubbel_doc_id_wordt_per_positie_en_hash_gekoppeld(self):
        from domain.sources.normalisatie import koppel_kwitantie

        receipt = self._receipt(
            [
                self._record(
                    1,
                    "document",
                    "doc1",
                    0,
                    "Eerste passage doc1.",
                    "Eerste passage doc1.",
                )
            ],
            [self._omitted("document", "doc1", 1, "Tweede passage doc1.", "budget")],
        )
        a, b = koppel_kwitantie([deepcopy(self.DOC_A), deepcopy(self.DOC_B)], receipt)
        assert (
            a["used_in_prompt"] is True
            and a["prompt_content"] == "Eerste passage doc1."
        )
        assert a["receipt_correlation"] == "verified"
        assert b["used_in_prompt"] is False and b["omitted_reason"] == "budget"
        assert b["receipt_correlation"] == "verified"
        assert "prompt_content" not in b

    def test_ontbrekende_ids_en_gelijke_afgekapte_prefix_worden_niet_verwisseld(self):
        from domain.sources.normalisatie import koppel_kwitantie

        # Beide chunks zonder chunk_id; beide afgekapt tot dezelfde prefix.
        receipt = self._receipt(
            [
                self._record(
                    1,
                    "rag",
                    None,
                    1,
                    "Gedeelde prefix beta.",
                    "Gedeelde prefix",
                    truncated=True,
                ),
                self._record(
                    2,
                    "rag",
                    None,
                    0,
                    "Gedeelde prefix alfa.",
                    "Gedeelde prefix",
                    truncated=True,
                ),
            ]
        )
        x, y = koppel_kwitantie([deepcopy(self.RAG_X), deepcopy(self.RAG_Y)], receipt)
        assert x["receipt_nr"] == 2 and y["receipt_nr"] == 1
        assert (
            x["snippet"] == "Gedeelde prefix alfa."
            and y["snippet"] == "Gedeelde prefix beta."
        )
        assert x["prompt_content"] == y["prompt_content"] == "Gedeelde prefix"
        assert x["truncated"] is True

    def test_gesanitiseerde_inhoud_koppelt_via_de_oorspronkelijke_hash(self):
        from domain.sources.normalisatie import koppel_kwitantie

        receipt = self._receipt(
            [
                self._record(1, "web", "https://w/x", 1, "Web twee.", "Web twee."),
                self._record(
                    2, "web", "https://w/x", 0, "<p>Web & een</p>", "Web & een"
                ),
            ]
        )
        een, twee = koppel_kwitantie(
            [deepcopy(self.WEB_1), deepcopy(self.WEB_2)], receipt
        )
        assert (
            een["title"] == "Een"
            and een["prompt_content"] == "Web & een"
            and een["sanitized"] is True
        )
        assert twee["title"] == "Twee" and twee["receipt_nr"] == 1

    def test_hash_mismatch_is_zichtbaar_en_koppelt_nooit_positioneel(self):
        from domain.sources.normalisatie import koppel_kwitantie

        receipt = self._receipt(
            [
                self._record(
                    1, "document", "doc1", 0, "Andere oorspronkelijke tekst.", "Andere"
                )
            ]
        )
        a, los = koppel_kwitantie([deepcopy(self.DOC_A)], receipt)
        assert a["used_in_prompt"] is False
        assert a["omitted_reason"] == "not_in_receipt"
        assert a["receipt_correlation"] == "not_in_receipt"
        assert "prompt_content" not in a
        assert los["receipt_correlation"] == "unmatched"
        assert los["prompt_content"] == "Andere"
        assert los.get("doc_id") == "doc1"

    def test_source_id_afwijking_bij_kloppende_hash_is_ook_mismatch(self):
        from domain.sources.normalisatie import koppel_kwitantie

        receipt = self._receipt(
            [
                self._record(
                    1,
                    "document",
                    "doc9",
                    0,
                    "Eerste passage doc1.",
                    "Eerste passage doc1.",
                )
            ]
        )
        a, los = koppel_kwitantie([deepcopy(self.DOC_A)], receipt)
        assert a["receipt_correlation"] == "not_in_receipt"
        assert los["receipt_correlation"] == "unmatched"

    def test_index_buiten_bereik_of_verkeerd_kanaal_koppelt_niet(self):
        from domain.sources.normalisatie import koppel_kwitantie

        receipt = self._receipt(
            [
                self._record(
                    1,
                    "document",
                    "doc1",
                    5,
                    "Eerste passage doc1.",
                    "Eerste passage doc1.",
                ),
                self._record(
                    2, "rag", "doc1", 0, "Eerste passage doc1.", "Eerste passage doc1."
                ),
            ]
        )
        uit = koppel_kwitantie([deepcopy(self.DOC_A)], receipt)
        assert uit[0]["receipt_correlation"] == "not_in_receipt"
        assert [b["receipt_correlation"] for b in uit[1:]] == ["unmatched", "unmatched"]

    def test_expliciete_kanaallijsten_gaan_voor_de_providergroepering(self):
        from domain.sources.normalisatie import koppel_kwitantie

        # Gesorteerde webkanaallijst (score-volgorde) wijkt af van de bronlijstvolgorde.
        web_kanaal = [self.WEB_2, self.WEB_1]
        bronnen = [self.WEB_1, self.WEB_2]
        receipt = self._receipt(
            [self._record(1, "web", "https://w/x", 0, "Web twee.", "Web twee.")]
        )
        uit = koppel_kwitantie(
            bronnen, receipt, kanalen={"web": web_kanaal, "rag": [], "document": []}
        )
        per_titel = {b["title"]: b for b in uit}
        assert per_titel["Twee"]["used_in_prompt"] is True
        assert per_titel["Een"]["used_in_prompt"] is False

    def test_v1_kwitantie_koppelt_alleen_bij_uniek_id(self):
        from domain.sources.normalisatie import koppel_kwitantie

        v1_uniek = {
            "version": "1",
            "status": "used",
            "sources": [
                {
                    "nr": 1,
                    "source_type": "document",
                    "source_id": "doc1",
                    "identity": {},
                    "content": "Eerste passage doc1.",
                    "content_hash": "x",
                    "sanitized": False,
                    "truncated": False,
                    "xml": "",
                    "used_in_prompt": True,
                }
            ],
            "omitted": [],
            "errors": [],
            "channels": {},
        }
        (a,) = koppel_kwitantie([deepcopy(self.DOC_A)], v1_uniek)
        assert a["used_in_prompt"] is True and a["receipt_correlation"] == "verified"
        a, b, los = koppel_kwitantie(
            [deepcopy(self.DOC_A), deepcopy(self.DOC_B)], v1_uniek
        )
        assert a["receipt_correlation"] == b["receipt_correlation"] == "not_in_receipt"
        assert los["receipt_correlation"] == "ambiguous"

    def test_koppelrapport_telt_de_correlatie(self):
        from domain.sources.normalisatie import (
            koppel_kwitantie,
            kwitantie_koppelrapport,
        )

        receipt = self._receipt(
            [
                self._record(
                    1,
                    "document",
                    "doc1",
                    0,
                    "Eerste passage doc1.",
                    "Eerste passage doc1.",
                )
            ],
            [self._omitted("document", "doc1", 1, "Onbekende tekst.", "budget")],
        )
        uit = koppel_kwitantie([deepcopy(self.DOC_A), deepcopy(self.DOC_B)], receipt)
        assert kwitantie_koppelrapport(uit) == {
            "verified": 1,
            "not_in_receipt": 1,
            "unmatched": 1,
            "ambiguous": 0,
        }

    def test_zonder_bruikbare_kwitantie_blijft_de_lijst_ongewijzigd(self):
        from domain.sources.normalisatie import koppel_kwitantie

        invoer = [deepcopy(DOCUMENT)]
        assert koppel_kwitantie(invoer, None) == invoer
        assert koppel_kwitantie(invoer, "geen dict") == invoer
        assert koppel_kwitantie(invoer, None)[0] is not invoer[0]

    def test_invoer_wordt_niet_gemuteerd_en_canonieke_passage_is_promptinhoud(self):
        from domain.sources.normalisatie import koppel_kwitantie

        invoer = [deepcopy(self.RAG_X)]
        momentopname = deepcopy(invoer)
        receipt = self._receipt(
            [
                self._record(
                    1,
                    "rag",
                    None,
                    0,
                    "Gedeelde prefix alfa.",
                    "Gedeelde prefix",
                    truncated=True,
                )
            ]
        )
        gekoppeld = koppel_kwitantie(invoer, receipt)
        assert invoer == momentopname
        (bron,) = canoniseer_bronnen(gekoppeld)
        assert bron.passage == "Gedeelde prefix" and bron.used_in_prompt is True
