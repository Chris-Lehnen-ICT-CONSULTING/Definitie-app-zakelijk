"""CON-02 (DEF-743): het broncontract — vingerafdruk, bewijstoets, replay en uitzonderingen.

Zuiver domein: geen AI-aanroep, geen database. De gestructureerde beoordeling
in deze tests is synthetisch (alsof een gevalideerde service haar leverde);
de code toetst uitsluitend wat code kán toetsen: binding, bewijsbestaan,
structuur en samenstelling — geen interpretatie.
"""

from copy import deepcopy

import pytest

from domain.sources.contract import (
    AI_ONDERDELEN,
    BASIS_ASSESSMENT,
    BASIS_REVIEW,
    CONTRACTVERSIE,
    ONDERDEEL_GEZAG,
    ONDERDEEL_STEUN,
    ONDERDEEL_UITZONDERING_GEEN_BRON,
    ONDERDEEL_VERWIJZING,
    REVIEW_TYPE_CORRECTIE,
    REVIEW_TYPE_GEEN_BRON,
    REVIEW_TYPE_VERWIJZING,
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_OPEN,
    STATUS_PASS,
    beoordeel_bronbasis,
    beoordeling_niet_beschikbaar,
    beoordeling_technische_fout,
    bereken_bronvingerafdruk,
    valideer_bronreview,
    vind_citaat,
)
from domain.sources.normalisatie import bereken_inhoudshash, canoniseer_bronnen

pytestmark = [pytest.mark.unit]

BEGRIP = "bestuursorgaan"
TEKST = (
    "Orgaan van een rechtspersoon die krachtens publiekrecht is ingesteld, of een "
    "ander persoon of college met enig openbaar gezag bekleed."
)
CONTEXT = {
    "organisatorische_context": ["Synthetische Toezichthouder"],
    "juridische_context": ["bestuursrecht"],
    "wettelijke_basis": ["Synthetische Bestuurswet"],
}
PASSAGE_WET = (
    "Artikel 1:1. Onder bestuursorgaan wordt verstaan: een orgaan van een "
    "rechtspersoon die krachtens publiekrecht is ingesteld, of een ander persoon "
    "of college, met enig openbaar gezag bekleed."
)
PASSAGE_BELEID = (
    "De toezichthouder hanteert het begrip bestuursorgaan zoals de wet dat doet; "
    "adviesorganen zonder gezag vallen erbuiten."
)
BRON_WET = {
    "provider": "documents",
    "doc_id": "wet-01",
    "filename": "synthetische-bestuurswet.txt",
    "citation_label": "art. 1:1",
    "bron_type": "wet",
    "snippet": PASSAGE_WET,
    "score": 1.0,
    "used_in_prompt": True,
}
BRON_BELEID = {
    "provider": "rag",
    "chunk_id": 7,
    "document_id": 3,
    "filename": "toezichtbeleid.txt",
    "bron_type": "beleid",
    "created_at": "2026-09-01T00:00:00Z",
    "metadata": {"pagina_nummer": 4, "locator": {"section": "Begrippen"}},
    "chunk_text": PASSAGE_BELEID,
    "score": 0.8,
}
BRONNEN = [BRON_WET, BRON_BELEID]
# DEF-806: een gewoon 'voldoet' op de verwijskwaliteit vereist een bruikbare
# (ook interne) hyperlink; de bronset zonder url blijft de basis voor de
# verwijzingsuitzondering.
BRON_WET_MET_LINK = {**BRON_WET, "url": "https://intern.example/wet#art-1-1"}
BRONNEN_MET_LINK = [BRON_WET_MET_LINK, BRON_BELEID]


def _fp(**overrides):
    kw = {
        "begrip": BEGRIP,
        "tekst": TEKST,
        "contexten": CONTEXT,
        "bronnen": BRONNEN,
        "peildatum": "2026-09-15",
    }
    kw.update(overrides)
    bronnen = kw.pop("bronnen")
    peildatum = kw.pop("peildatum")
    return bereken_bronvingerafdruk(
        kw["begrip"], kw["tekst"], kw["contexten"], bronnen, peildatum=peildatum
    )


def _deel(status, *, evidence=(), reason="synthetische reden", **extra):
    return {
        "status": status,
        "reason": reason,
        "uncertainty": None,
        "evidence": [dict(e) for e in evidence],
        **extra,
    }


def _assessment(
    *,
    status="assessed",
    parts=None,
    fingerprint=None,
    model="fake-model",
    error=None,
    bronnen=BRONNEN,
):
    canoniek = canoniseer_bronnen(bronnen)
    return {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": "con02-assess/1",
        "fingerprint": (
            fingerprint if fingerprint is not None else _fp(bronnen=bronnen)
        ),
        "status": status,
        "error": error,
        "assessed_at": "2026-09-15T12:00:00+00:00",
        "attribution": {
            "provider": "fake",
            "model": model,
            "task_type": "validation",
            "cached": False,
            "tokens_used": 1,
        },
        "peildatum": "2026-09-15",
        "sources": [b.als_dict() for b in canoniek],
        "parts": parts or {},
        "rejected": [],
        "raw_response_sha256": None,
    }


def _gegrond():
    """Drie onderdelen pass, elk met een letterlijk citaat uit een bestaande bron."""
    wet = {
        "source_id": "doc:wet-01",
        "quote": "een orgaan van een rechtspersoon die krachtens publiekrecht is ingesteld",
    }
    beleid = {
        "source_id": "rag:3:7",
        "quote": "adviesorganen zonder gezag vallen erbuiten",
    }
    return {
        ONDERDEEL_GEZAG: _deel(
            STATUS_PASS,
            evidence=[wet],
            sources=[
                {
                    "source_id": "doc:wet-01",
                    "profile": "wet_regelgeving",
                    "applicable": True,
                    "reason": "definitiebepaling",
                }
            ],
        ),
        ONDERDEEL_STEUN: _deel(
            STATUS_PASS,
            evidence=[wet, beleid],
            claims=[
                {
                    "aspect": "kenmerk",
                    "text": "krachtens publiekrecht ingesteld",
                    "supported": True,
                    "source_id": "doc:wet-01",
                }
            ],
        ),
        ONDERDEEL_VERWIJZING: _deel(
            STATUS_PASS,
            evidence=[{"source_id": "doc:wet-01", "quote": "Artikel 1:1"}],
            sources=[
                {
                    "source_id": "doc:wet-01",
                    "locatable": True,
                    "reason": "artikelnummer aanwezig",
                }
            ],
        ),
    }


def _beoordeel(**kw):
    args = {
        "assessment": None,
        "review": None,
        "definitie_versie": None,
        "peildatum": "2026-09-15",
    }
    args.update(kw)
    bronnen = args.pop("bronnen", BRONNEN)
    return beoordeel_bronbasis(BEGRIP, TEKST, CONTEXT, bronnen, **args)


def _part(uitkomst, onderdeel):
    return next(p for p in uitkomst.parts if p.id == onderdeel)


# --- vingerafdruk --------------------------------------------------------------


class TestVingerafdruk:
    def test_is_deterministisch_en_volgorde_onafhankelijk(self):
        assert _fp() == _fp()
        assert _fp(bronnen=[BRON_BELEID, BRON_WET]) == _fp()
        assert _fp(bronnen=canoniseer_bronnen(BRONNEN)) == _fp()

    @pytest.mark.parametrize(
        "mutatie",
        [
            {"begrip": "toezichthouder"},
            {"tekst": TEKST + " "},
            {"contexten": {**CONTEXT, "wettelijke_basis": []}},
            {"peildatum": "2026-09-14"},
            {"peildatum": None},
        ],
    )
    def test_kandidaat_context_term_of_peildatum_wijziging_is_stale(self, mutatie):
        assert _fp(**mutatie) != _fp()

    @pytest.mark.parametrize(
        "wijziging",
        [
            {"snippet": PASSAGE_WET + " Extra zin."},
            {"url": "https://intern.example/wet"},
            {"citation_label": "art. 1:2"},
            {"filename": "andere-titel.txt"},
            {"source_version": "2"},
            {"bron_type": "beleid"},
            {"issuer": "Ander bestuur"},
            {"approval_status": "concept"},
            {"metadata": {"jurisdictie": "Caribisch Nederland"}},
        ],
    )
    def test_alleen_metadata_wijziging_van_een_bron_is_stale(self, wijziging):
        gewijzigd = [{**BRON_WET, **wijziging}, BRON_BELEID]
        assert _fp(bronnen=gewijzigd) != _fp()

    @pytest.mark.parametrize(
        "ruis",
        [
            {"score": 0.1},
            {"used_in_prompt": False},
            {"is_authoritative": True},
            {"source_label": "Officiële bron"},
            {"confidence": 0.99},
            {"selection_basis": "selected_short_document"},
        ],
    )
    def test_zoekscore_vlaggen_en_badges_veranderen_niets(self, ruis):
        assert _fp(bronnen=[{**BRON_WET, **ruis}, BRON_BELEID]) == _fp()

    def test_beleidsversie_zit_in_de_vingerafdruk(self):
        assert CONTRACTVERSIE == "con02/1"


def test_vind_citaat_is_letterlijk_maar_whitespace_tolerant():
    assert vind_citaat(PASSAGE_WET, "orgaan van een   rechtspersoon\ndie krachtens")
    assert not vind_citaat(PASSAGE_WET, "")
    assert not vind_citaat(PASSAGE_WET, "   ")
    assert not vind_citaat(PASSAGE_WET, "orgaan van een gemeente")
    assert not vind_citaat("", "iets")


# --- replay zonder / met beoordeling -------------------------------------------


class TestReplayZonderBeoordeling:
    def test_geen_bronnen_is_expliciet_open_zonder_violation(self):
        uitkomst = _beoordeel(bronnen=[])
        assert uitkomst.status == STATUS_OPEN
        assert [p.id for p in uitkomst.parts] == list(AI_ONDERDELEN)
        assert all(p.status == STATUS_OPEN and p.field is None for p in uitkomst.parts)
        assert "geen bronnen" in uitkomst.parts[0].reason.casefold()
        assert uitkomst.review["assessment"]["applied"] is False

    def test_bronwoord_in_de_zin_zonder_bronnen_verandert_niets(self):
        uitkomst = beoordeel_bronbasis(
            BEGRIP, TEKST + " Zoals bepaald in de wet.", CONTEXT, []
        )
        assert uitkomst.status == STATUS_OPEN

    def test_bronnen_zonder_beoordeling_is_open(self):
        uitkomst = _beoordeel()
        assert uitkomst.status == STATUS_OPEN
        assert all(p.status == STATUS_OPEN for p in uitkomst.parts)
        assert "niet uitgevoerd" in uitkomst.review["assessment"]["reason"]

    def test_niet_beschikbare_dienst_is_open_met_eigen_reden(self):
        uitkomst = _beoordeel(
            assessment=beoordeling_niet_beschikbaar(_fp(), "geen dienst geïnjecteerd")
        )
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["assessment"]["status"] == "unavailable"
        assert "geen dienst" in uitkomst.review["assessment"]["reason"]

    def test_technische_fout_is_error_en_nooit_pass(self):
        uitkomst = _beoordeel(
            assessment=beoordeling_technische_fout(_fp(), "timeout", "AI timed out")
        )
        assert uitkomst.status == STATUS_ERROR
        assert all(p.status == STATUS_ERROR for p in uitkomst.parts)
        assert uitkomst.review["assessment"]["status"] == "error"
        assert "timeout" in uitkomst.review["assessment"]["reason"]


class TestReplayMetBeoordeling:
    def test_gegronde_beoordeling_is_pass_met_geverifieerd_citaat(self):
        uitkomst = _beoordeel(
            assessment=_assessment(parts=_gegrond(), bronnen=BRONNEN_MET_LINK),
            bronnen=BRONNEN_MET_LINK,
        )
        assert uitkomst.status == STATUS_PASS
        gezag = _part(uitkomst, ONDERDEEL_GEZAG)
        assert gezag.status == STATUS_PASS
        assert gezag.field == BASIS_ASSESSMENT
        assert (
            gezag.evidence
            == "een orgaan van een rechtspersoon die krachtens publiekrecht is ingesteld"
        )
        assert "doc:wet-01" in gezag.reason
        assert uitkomst.review["assessment"] == {
            "applied": True,
            "status": "assessed",
            "reason": None,
            "model": "fake-model",
            "provider": "fake",
            "prompt_version": "con02-assess/1",
            "rejected": 0,
        }
        assert uitkomst.als_dict()["score"] is None

    def test_gegronde_beoordeling_zonder_hyperlink_is_geen_verwijzings_pass(self):
        """DEF-806: locatable + geldig citaat zonder url is geen gewoon 'voldoet'."""
        uitkomst = _beoordeel(assessment=_assessment(parts=_gegrond()))
        assert uitkomst.status == STATUS_OPEN
        verwijzing = _part(uitkomst, ONDERDEEL_VERWIJZING)
        assert verwijzing.status == STATUS_OPEN
        assert "hyperlink" in verwijzing.reason.casefold()
        assert _part(uitkomst, ONDERDEEL_GEZAG).status == STATUS_PASS
        assert _part(uitkomst, ONDERDEEL_STEUN).status == STATUS_PASS

    def test_pass_zonder_bewijs_wordt_open_met_bewaarde_modelreden(self):
        parts = _gegrond()
        parts[ONDERDEEL_STEUN]["evidence"] = []
        parts[ONDERDEEL_STEUN]["reason"] = "Het model vond de kenmerken gedekt."
        uitkomst = _beoordeel(assessment=_assessment(parts=parts))
        assert uitkomst.status == STATUS_OPEN
        steun = _part(uitkomst, ONDERDEEL_STEUN)
        assert steun.status == STATUS_OPEN
        assert steun.evidence is None
        assert "Het model vond de kenmerken gedekt." in steun.reason
        assert "onvoldoende onderbouwd" in steun.reason.casefold()

    @pytest.mark.parametrize(
        "vals",
        [
            {"source_id": "doc:verzonnen", "quote": "een orgaan van een rechtspersoon"},
            {"source_id": "doc:wet-01", "quote": "een orgaan van een gemeente"},
            {"source_id": "doc:wet-01", "quote": ""},
            {"source_id": "rag:3:7", "quote": "een orgaan van een rechtspersoon"},
        ],
    )
    def test_verzonnen_of_verkeerd_toegewezen_bewijs_telt_niet(self, vals):
        parts = _gegrond()
        parts[ONDERDEEL_GEZAG]["evidence"] = [vals]
        uitkomst = _beoordeel(assessment=_assessment(parts=parts))
        gezag = _part(uitkomst, ONDERDEEL_GEZAG)
        assert gezag.status == STATUS_OPEN
        assert gezag.evidence is None
        assert uitkomst.status == STATUS_OPEN

    def test_fail_met_bewijs_naast_open_blijft_beide_zichtbaar(self):
        parts = _gegrond()
        parts[ONDERDEEL_STEUN] = _deel(
            STATUS_FAIL,
            evidence=[
                {
                    "source_id": "rag:3:7",
                    "quote": "adviesorganen zonder gezag vallen erbuiten",
                }
            ],
            reason="De definitie sluit adviesorganen niet uit terwijl de bron dat vereist.",
        )
        parts[ONDERDEEL_VERWIJZING]["evidence"] = []
        uitkomst = _beoordeel(assessment=_assessment(parts=parts))
        assert uitkomst.status == STATUS_FAIL
        assert _part(uitkomst, ONDERDEEL_STEUN).status == STATUS_FAIL
        assert _part(uitkomst, ONDERDEEL_VERWIJZING).status == STATUS_OPEN
        assert _part(uitkomst, ONDERDEEL_GEZAG).status == STATUS_PASS

    def test_fail_zonder_bewijs_is_geen_aantoonbare_tekortkoming(self):
        parts = _gegrond()
        parts[ONDERDEEL_GEZAG] = _deel(STATUS_FAIL, reason="Bron is niet gezaghebbend.")
        uitkomst = _beoordeel(assessment=_assessment(parts=parts))
        assert _part(uitkomst, ONDERDEEL_GEZAG).status == STATUS_OPEN
        assert uitkomst.status == STATUS_OPEN

    @pytest.mark.parametrize(
        "mutatie",
        [
            {"fingerprint": "0" * 64},
            {"model": None},
            {"model": ""},
        ],
    )
    def test_stale_of_niet_toegeschreven_beoordeling_geeft_geen_pass(self, mutatie):
        uitkomst = _beoordeel(assessment=_assessment(parts=_gegrond(), **mutatie))
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["assessment"]["applied"] is False
        assert uitkomst.review["assessment"]["reason"]

    def test_beoordeling_bij_gewijzigde_tekst_of_bron_is_stale(self):
        beoordeling = _assessment(parts=_gegrond())
        gewijzigd = beoordeel_bronbasis(
            BEGRIP,
            TEKST + " Aangepast.",
            CONTEXT,
            BRONNEN,
            assessment=beoordeling,
            peildatum="2026-09-15",
        )
        assert gewijzigd.status == STATUS_OPEN
        andere_bron = _beoordeel(
            assessment=beoordeling,
            bronnen=[{**BRON_WET, "citation_label": "art. 9"}, BRON_BELEID],
        )
        assert andere_bron.status == STATUS_OPEN
        assert "gewijzigd" in andere_bron.review["assessment"]["reason"]

    def test_verkeerde_contractversie_of_onbekende_status_geeft_geen_pass(self):
        oud = {**_assessment(parts=_gegrond()), "contract_version": "con02/0"}
        assert _beoordeel(assessment=oud).status == STATUS_OPEN
        raar = {**_assessment(parts=_gegrond()), "status": "goedgekeurd"}
        assert _beoordeel(assessment=raar).status == STATUS_OPEN

    def test_ongeldige_deelstatus_wordt_open_niet_pass(self):
        parts = _gegrond()
        parts[ONDERDEEL_GEZAG]["status"] = "approved"
        uitkomst = _beoordeel(assessment=_assessment(parts=parts))
        assert _part(uitkomst, ONDERDEEL_GEZAG).status == STATUS_OPEN
        assert uitkomst.status == STATUS_OPEN

    def test_misvormde_beoordeling_is_open_zonder_crash(self):
        for kapot in (
            "tekst",
            7,
            {"parts": "geen dict"},
            {"parts": None, "status": "assessed"},
        ):
            assert _beoordeel(assessment=kapot).status == STATUS_OPEN


# --- deskundige uitzonderingen (bevroren platte vorm) -------------------------


def _review(**overrides):
    basis = {
        "type": REVIEW_TYPE_VERWIJZING,
        "accepted": True,
        "actor": "synthetische-deskundige",
        "rationale": "Het wetsartikel is intern beschikbaar; er is geen publieke hyperlink.",
        "version_number": 3,
        "fingerprint": _fp(),
        "reviewed_at": "2026-09-15T13:00:00+00:00",
        "source_id": "doc:wet-01",
        "content_hash": bereken_inhoudshash(PASSAGE_WET),
        "source_version": None,
        "locator": "art. 1:1",
    }
    basis.update(overrides)
    return basis


class TestVerwijzingsuitzondering:
    def test_geaccepteerde_uitzondering_blijft_review_required_en_zichtbaar(self):
        uitkomst = _beoordeel(
            assessment=_assessment(parts=_gegrond()),
            review=_review(),
            definitie_versie=3,
        )
        assert uitkomst.status == STATUS_OPEN  # nooit pass door een uitzondering
        verwijzing = _part(uitkomst, ONDERDEEL_VERWIJZING)
        assert verwijzing.status == STATUS_OPEN
        assert verwijzing.field == BASIS_REVIEW
        assert verwijzing.evidence == "art. 1:1"
        assert "synthetische-deskundige" in verwijzing.reason
        assert "uitzondering" in verwijzing.reason.casefold()
        # De andere onderdelen blijven onverminderd het AI-oordeel dragen.
        assert _part(uitkomst, ONDERDEEL_GEZAG).status == STATUS_PASS
        assert _part(uitkomst, ONDERDEEL_STEUN).status == STATUS_PASS
        assert uitkomst.review["applied"] is True
        assert uitkomst.review["accepted_exception"] == "reference"
        assert uitkomst.review["type"] == REVIEW_TYPE_VERWIJZING
        assert uitkomst.review["actor"] == "synthetische-deskundige"

    def test_uitzondering_zonder_ai_beoordeling_geeft_geen_pass(self):
        uitkomst = _beoordeel(review=_review(), definitie_versie=3)
        assert uitkomst.status == STATUS_OPEN
        assert _part(uitkomst, ONDERDEEL_VERWIJZING).field == BASIS_REVIEW
        assert _part(uitkomst, ONDERDEEL_GEZAG).status == STATUS_OPEN

    @pytest.mark.parametrize(
        ("mutatie", "fragment"),
        [
            ({"content_hash": "f" * 64}, "passage"),
            ({"source_id": "doc:verzonnen"}, "onbekend"),
            ({"locator": "art. 9:9"}, "vindplaats"),
            ({"locator": ""}, "vindplaats"),
            ({"accepted": False}, "accept"),
            ({"accepted": "ja"}, "accept"),
            ({"rationale": " "}, "motivering"),
            ({"actor": ""}, "beoordelaar"),
            ({"fingerprint": "0" * 64}, "gewijzigd"),
            ({"version_number": 2}, "versie"),
            ({"version_number": None}, "versie"),
            ({"type": "part_review"}, "niet ondersteund"),
            ({"type": "onbekend"}, "niet ondersteund"),
        ],
    )
    def test_onvolledige_of_vervalste_uitzondering_wordt_niet_toegepast(
        self, mutatie, fragment
    ):
        uitkomst = _beoordeel(
            assessment=_assessment(parts=_gegrond()),
            review=_review(**mutatie),
            definitie_versie=3,
        )
        assert uitkomst.review["applied"] is False
        assert uitkomst.review["accepted_exception"] is None
        assert fragment in uitkomst.review["reason"].casefold()
        assert _part(uitkomst, ONDERDEEL_VERWIJZING).field == BASIS_ASSESSMENT

    def test_bron_met_hyperlink_valt_buiten_de_verwijzingsuitzondering(self):
        met_link = [{**BRON_WET, "url": "https://intern.example/wet#1:1"}, BRON_BELEID]
        fp = _fp(bronnen=met_link)
        uitkomst = beoordeel_bronbasis(
            BEGRIP,
            TEKST,
            CONTEXT,
            met_link,
            review=_review(fingerprint=fp),
            definitie_versie=3,
            peildatum="2026-09-15",
        )
        assert uitkomst.review["applied"] is False
        assert "hyperlink" in uitkomst.review["reason"].casefold()

    def test_bronversie_moet_de_bewaarde_versie_zijn(self):
        met_versie = [{**BRON_WET, "source_version": "2024-01"}, BRON_BELEID]
        fp = _fp(bronnen=met_versie)
        fout = beoordeel_bronbasis(
            BEGRIP,
            TEKST,
            CONTEXT,
            met_versie,
            review=_review(fingerprint=fp, source_version="2023-01"),
            definitie_versie=3,
            peildatum="2026-09-15",
        )
        assert fout.review["applied"] is False
        assert "versie" in fout.review["reason"].casefold()
        goed = beoordeel_bronbasis(
            BEGRIP,
            TEKST,
            CONTEXT,
            met_versie,
            review=_review(fingerprint=fp, source_version="2024-01"),
            definitie_versie=3,
            peildatum="2026-09-15",
        )
        assert goed.review["accepted_exception"] == "reference"

    def test_zonder_recordversie_bindt_alleen_de_vingerafdruk(self):
        uitkomst = _beoordeel(
            review=_review(version_number=None), definitie_versie=None
        )
        assert uitkomst.review["accepted_exception"] == "reference"


class TestGeenPassendeBron:
    def _review(self, **overrides):
        basis = {
            "type": REVIEW_TYPE_GEEN_BRON,
            "accepted": True,
            "actor": "synthetische-deskundige",
            "rationale": "Er bestaat geen vastgestelde bron voor dit interne begrip.",
            "version_number": None,
            "fingerprint": _fp(bronnen=[]),
            "reviewed_at": None,
            "search": {
                "queries": ["bestuursorgaan definitie", "bestuursorgaan beleid"],
                "consulted": ["wetten.overheid.nl", "intern beleidsregister"],
                "conclusion": "Geen passende bron gevonden.",
            },
        }
        basis.update(overrides)
        return basis

    def test_gedocumenteerde_uitzondering_is_zichtbaar_en_geen_pass(self):
        uitkomst = _beoordeel(bronnen=[], review=self._review())
        assert uitkomst.status == STATUS_OPEN
        extra = _part(uitkomst, ONDERDEEL_UITZONDERING_GEEN_BRON)
        assert extra.status == STATUS_OPEN
        assert extra.field == BASIS_REVIEW
        assert "synthetische-deskundige" in extra.reason
        assert uitkomst.review["accepted_exception"] == "no_source"
        # De drie AI-onderdelen blijven onveranderd open.
        assert [p.id for p in uitkomst.parts[:3]] == list(AI_ONDERDELEN)

    @pytest.mark.parametrize(
        "search",
        [
            None,
            {},
            {"queries": [], "conclusion": "x"},
            {"queries": ["q"], "conclusion": ""},
            "vrije tekst",
        ],
    )
    def test_zonder_gedocumenteerd_zoeken_geen_uitzondering(self, search):
        uitkomst = _beoordeel(bronnen=[], review=self._review(search=search))
        assert uitkomst.review["applied"] is False
        assert "zoek" in uitkomst.review["reason"].casefold()
        assert all(p.id != ONDERDEEL_UITZONDERING_GEEN_BRON for p in uitkomst.parts)

    def test_uitzondering_naast_aanwezige_bronnen_verandert_de_ai_onderdelen_niet(self):
        parts = _gegrond()
        parts[ONDERDEEL_GEZAG] = _deel(
            STATUS_FAIL,
            evidence=[{"source_id": "rag:3:7", "quote": "adviesorganen zonder gezag"}],
            reason="Alleen beleid, geen wettelijke basis.",
        )
        uitkomst = _beoordeel(
            assessment=_assessment(parts=parts),
            review=self._review(fingerprint=_fp()),
        )
        assert uitkomst.status == STATUS_FAIL
        assert _part(uitkomst, ONDERDEEL_GEZAG).status == STATUS_FAIL
        assert _part(uitkomst, ONDERDEEL_UITZONDERING_GEEN_BRON).status == STATUS_OPEN


def test_valideer_bronreview_is_de_gezaghebbende_helper_voor_persistentie():
    bronnen = canoniseer_bronnen(BRONNEN)
    toepasbaar, samenvatting = valideer_bronreview(_review(), _fp(), bronnen, 3)
    assert toepasbaar is not None and toepasbaar["type"] == REVIEW_TYPE_VERWIJZING
    assert samenvatting["applied"] is True
    niets, samenvatting = valideer_bronreview(None, _fp(), bronnen, 3)
    assert niets is None and samenvatting["applied"] is False


def test_als_dict_past_in_het_rule_result_contract():
    uitkomst = _beoordeel(
        assessment=_assessment(parts=_gegrond()), review=_review(), definitie_versie=3
    )
    d = uitkomst.als_dict()
    assert set(d) == {
        "status",
        "score",
        "contract_version",
        "fingerprint",
        "parts",
        "review",
    }
    assert d["contract_version"] == CONTRACTVERSIE
    for part in d["parts"]:
        assert set(part) == {
            "id",
            "status",
            "evidence",
            "context_value",
            "field",
            "position",
            "reason",
            "action",
        }
        assert part["context_value"] is None and part["position"] is None
    assert deepcopy(d) == d


# --- deskundige correctie van één AI-onderdeel (part_correction) --------------


class TestDeelcorrectie:
    def _bewijs(self, **overrides):
        item = {
            "source_id": "doc:wet-01",
            "content_hash": bereken_inhoudshash(PASSAGE_WET),
            "source_version": None,
            "quote": "met enig openbaar gezag bekleed",
            "locator": "art. 1:1",
        }
        item.update(overrides)
        return item

    def _review(self, **overrides):
        basis = {
            "type": REVIEW_TYPE_CORRECTIE,
            "accepted": True,
            "actor": "synthetische-deskundige",
            "rationale": "De wettekst dekt ook het openbaar-gezagcriterium.",
            "version_number": 3,
            "fingerprint": _fp(),
            "reviewed_at": "2026-09-15T14:00:00+00:00",
            "part_id": ONDERDEEL_STEUN,
            "status": STATUS_PASS,
            "evidence": [self._bewijs()],
        }
        basis.update(overrides)
        return basis

    def _assessment_open_steun(self, bronnen=BRONNEN):
        parts = _gegrond()
        parts[ONDERDEEL_STEUN] = _deel(
            STATUS_OPEN, reason="Model twijfelt over het gezagscriterium."
        )
        return _assessment(parts=parts, bronnen=bronnen)

    def test_correctie_vervangt_alleen_het_gekozen_onderdeel_met_bewijs_en_attributie(
        self,
    ):
        # Bronset mét hyperlink (DEF-806), zodat de samenstelling tot 'pass' kan komen.
        origineel = self._assessment_open_steun(bronnen=BRONNEN_MET_LINK)
        review = self._review(fingerprint=_fp(bronnen=BRONNEN_MET_LINK))
        momentopname = (deepcopy(origineel), deepcopy(review))
        uitkomst = _beoordeel(
            assessment=origineel,
            review=review,
            definitie_versie=3,
            bronnen=BRONNEN_MET_LINK,
        )
        assert (origineel, review) == momentopname  # invoer niet gemuteerd
        steun = _part(uitkomst, ONDERDEEL_STEUN)
        assert steun.status == STATUS_PASS
        assert steun.field == BASIS_REVIEW
        assert steun.evidence == "met enig openbaar gezag bekleed"
        assert "synthetische-deskundige" in steun.reason
        assert (
            "Model twijfelt over het gezagscriterium." in steun.reason
        )  # oorspronkelijk AI-oordeel blijft zichtbaar
        assert _part(uitkomst, ONDERDEEL_GEZAG).field == BASIS_ASSESSMENT
        assert _part(uitkomst, ONDERDEEL_VERWIJZING).field == BASIS_ASSESSMENT
        assert uitkomst.review["applied"] is True
        assert uitkomst.review["accepted_exception"] is None
        assert uitkomst.review["applied_correction"] == {
            "part_id": ONDERDEEL_STEUN,
            "status": STATUS_PASS,
            "actor": "synthetische-deskundige",
            "evidence": [
                {
                    "source_id": "doc:wet-01",
                    "content_hash": bereken_inhoudshash(PASSAGE_WET),
                    "source_version": None,
                    "quote": "met enig openbaar gezag bekleed",
                    "locator": "art. 1:1",
                }
            ],
            "original": {
                "status": STATUS_OPEN,
                "field": BASIS_ASSESSMENT,
                "reason": _part(
                    _beoordeel(
                        assessment=self._assessment_open_steun(
                            bronnen=BRONNEN_MET_LINK
                        ),
                        bronnen=BRONNEN_MET_LINK,
                    ),
                    ONDERDEEL_STEUN,
                ).reason,
                "evidence": None,
            },
        }
        # De samenstelling volgt gewoon: alle drie pass → pass; geen 'globale pass' via het payload.
        assert uitkomst.status == STATUS_PASS

    def test_correctie_naar_fail_vereist_bewijs_en_blijft_naast_de_rest_zichtbaar(self):
        uitkomst = _beoordeel(
            assessment=_assessment(parts=_gegrond()),
            review=self._review(
                status=STATUS_FAIL,
                rationale="De definitie mist het publiekrechtcriterium.",
            ),
            definitie_versie=3,
        )
        assert _part(uitkomst, ONDERDEEL_STEUN).status == STATUS_FAIL
        assert uitkomst.status == STATUS_FAIL
        assert _part(uitkomst, ONDERDEEL_GEZAG).status == STATUS_PASS

    def test_open_correctie_mag_zonder_bewijs_met_motivering(self):
        uitkomst = _beoordeel(
            assessment=_assessment(parts=_gegrond()),
            review=self._review(
                status=STATUS_OPEN,
                evidence=[],
                rationale="Bewijs ontbreekt nog; opnieuw beoordelen.",
            ),
            definitie_versie=3,
        )
        assert _part(uitkomst, ONDERDEEL_STEUN).status == STATUS_OPEN
        assert uitkomst.review["applied_correction"]["status"] == STATUS_OPEN
        assert uitkomst.status == STATUS_OPEN

    @pytest.mark.parametrize(
        ("mutatie", "fragment"),
        [
            ({"part_id": "overall"}, "onderdeel"),
            ({"part_id": ONDERDEEL_UITZONDERING_GEEN_BRON}, "onderdeel"),
            ({"status": "approved"}, "status"),
            ({"evidence": []}, "bewijs"),
            ({"evidence": "geen lijst"}, "bewijs"),
            ({"accepted": False}, "accept"),
            ({"rationale": ""}, "motivering"),
            ({"fingerprint": "0" * 64}, "gewijzigd"),
            ({"version_number": 2}, "versie"),
        ],
    )
    def test_onvolledige_correctie_wordt_niet_toegepast(self, mutatie, fragment):
        uitkomst = _beoordeel(
            assessment=self._assessment_open_steun(),
            review=self._review(**mutatie),
            definitie_versie=3,
        )
        assert uitkomst.review["applied"] is False
        assert uitkomst.review.get("applied_correction") is None
        assert fragment in uitkomst.review["reason"].casefold()
        assert _part(uitkomst, ONDERDEEL_STEUN).field == BASIS_ASSESSMENT
        assert uitkomst.status == STATUS_OPEN

    @pytest.mark.parametrize(
        "slecht_bewijs",
        [
            {"source_id": "doc:verzonnen"},
            {"content_hash": "f" * 64},
            {"quote": "een tekst die niet in de bron staat"},
            {"quote": ""},
            {"locator": "art. 9:9"},
            {"source_version": "2024-01"},
        ],
    )
    def test_bewijs_moet_aan_de_bewaarde_bron_gebonden_zijn(self, slecht_bewijs):
        uitkomst = _beoordeel(
            assessment=self._assessment_open_steun(),
            review=self._review(evidence=[self._bewijs(**slecht_bewijs)]),
            definitie_versie=3,
        )
        assert uitkomst.review["applied"] is False
        assert "bewijs" in uitkomst.review["reason"].casefold()
        assert _part(uitkomst, ONDERDEEL_STEUN).status == STATUS_OPEN

    def test_verwijzingscorrectie_vereist_een_vindplaats(self):
        # Mét hyperlink (DEF-806): hier wordt alleen de vindplaats-eis getoetst.
        zonder_locator = [{**BRON_WET_MET_LINK, "citation_label": None}, BRON_BELEID]
        fp = _fp(bronnen=zonder_locator)
        review = self._review(
            fingerprint=fp,
            part_id=ONDERDEEL_VERWIJZING,
            evidence=[self._bewijs(locator=None)],
        )
        uitkomst = beoordeel_bronbasis(
            BEGRIP,
            TEKST,
            CONTEXT,
            zonder_locator,
            review=review,
            definitie_versie=3,
            peildatum="2026-09-15",
        )
        assert uitkomst.review["applied"] is False
        assert "vindplaats" in uitkomst.review["reason"].casefold()
        # Met een door de deskundige opgegeven exacte vindplaats wél.
        review_met = self._review(
            fingerprint=fp,
            part_id=ONDERDEEL_VERWIJZING,
            evidence=[self._bewijs(locator="art. 1:1 lid 1")],
        )
        uitkomst_met = beoordeel_bronbasis(
            BEGRIP,
            TEKST,
            CONTEXT,
            zonder_locator,
            review=review_met,
            definitie_versie=3,
            peildatum="2026-09-15",
        )
        assert (
            uitkomst_met.review["applied_correction"]["part_id"] == ONDERDEEL_VERWIJZING
        )
        assert (
            _part(uitkomst_met, ONDERDEEL_VERWIJZING).evidence
            == "met enig openbaar gezag bekleed"
        )

    def test_correctie_zonder_ai_beoordeling_geldt_alleen_voor_dat_onderdeel(self):
        uitkomst = _beoordeel(review=self._review(), definitie_versie=3)
        assert _part(uitkomst, ONDERDEEL_STEUN).status == STATUS_PASS
        assert _part(uitkomst, ONDERDEEL_GEZAG).status == STATUS_OPEN
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["applied_correction"]["original"]["field"] is None

    def test_valideer_bronreview_geeft_de_gevalideerde_correctie_terug(self):
        bronnen = canoniseer_bronnen(BRONNEN)
        toepasbaar, samenvatting = valideer_bronreview(
            self._review(), _fp(), bronnen, 3
        )
        assert samenvatting["applied_correction"]["part_id"] == ONDERDEEL_STEUN
        assert toepasbaar["evidence"][0]["quote"] == "met enig openbaar gezag bekleed"


def test_technische_fout_gaat_voor_op_geen_bronnen_bij_replay():
    """Bevinding 3 (domein): een foutbeoordeling zonder bronnen blijft een fout."""
    uitkomst = beoordeel_bronbasis(
        BEGRIP,
        TEKST,
        CONTEXT,
        [],
        assessment=beoordeling_technische_fout(
            _fp(bronnen=[]), "receipt_error", "verzamelfout rag"
        ),
        peildatum="2026-09-15",
    )
    assert uitkomst.status == STATUS_ERROR
    assert all(p.status == STATUS_ERROR for p in uitkomst.parts)
    assert "verzamelfout" in uitkomst.parts[0].reason
