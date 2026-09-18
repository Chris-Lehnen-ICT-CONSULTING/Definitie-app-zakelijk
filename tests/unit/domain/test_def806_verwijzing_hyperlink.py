"""CON-02 (DEF-806): verwijskwaliteit 'voldoet' vereist een bruikbare hyperlink.

Regressie op het echte generatierecord 4 (17 september 2026): vier geüploade
documentpassages zonder url, een AI-oordeel `reference_quality: pass` met
`locatable: true` en een geldig citaat, geen deskundige uitzondering — en
toch een gewone positieve verwijzingsbeoordeling. Besluit 1 van 15 september
2026: zonder hyperlink is alleen een zichtbare deskundige uitzondering
mogelijk; een bruikbare interne link volstaat wél.

Domein én service, zonder modelcall: de gestructureerde beoordeling is
synthetisch of letterlijk uit record 4 overgenomen.
"""

from copy import deepcopy

import pytest

from domain.sources.contract import (
    BASIS_ASSESSMENT,
    BASIS_REVIEW,
    CONTRACTVERSIE,
    ONDERDEEL_GEZAG,
    ONDERDEEL_STEUN,
    ONDERDEEL_VERWIJZING,
    REVIEW_TYPE_CORRECTIE,
    REVIEW_TYPE_VERWIJZING,
    STATUS_OPEN,
    STATUS_PASS,
    beoordeel_bronbasis,
    bereken_bronvingerafdruk,
)
from domain.sources.normalisatie import bereken_inhoudshash, canoniseer_bronnen
from services.validation.source_assessment_service import (
    SourceAssessmentService,
    bouw_beoordelingsprompt,
)

pytestmark = [pytest.mark.unit]

# --- record 4, teruggebracht tot wat de contractkern ziet ---------------------

BEGRIP = "besluit"
TEKST = (
    "Resultaat van besluitvorming door een bestuursorgaan in de vorm van een "
    "schriftelijke beslissing die een publiekrechtelijke rechtshandeling inhoudt."
)
CONTEXT = {
    "organisatorische_context": [],
    "juridische_context": ["Bestuursrecht"],
    "wettelijke_basis": ["Algemene wet bestuursrecht"],
}
PASSAGE_AWB = (
    "Algemene wet bestuursrecht Artikel 1:3 1. Onder besluit wordt verstaan: een "
    "schriftelijke beslissing van een bestuursorgaan, inhoudende een "
    "publiekrechtelijke rechtshandeling. 2. Onder beschikki"
)
BRON_AWB = {
    "provider": "documents",
    "filename": "awb-1-3-20260815.txt",
    "title": "awb-1-3-20260815.txt",
    "url": None,
    "snippet": PASSAGE_AWB,
    "score": 1.0,
    "used_in_prompt": True,
    "doc_id": "01e121c20018eed2",
    "source_label": "Geüpload document",
}
BRON_AWB_MET_LINK = {**BRON_AWB, "url": "https://intern.example/awb#art-1-3"}
BEWIJS_AWB = {
    "source_id": "doc:01e121c20018eed2",
    "quote": "Algemene wet bestuursrecht Artikel 1:3 1. Onder besluit wordt verstaan:",
}


def _parts_record4():
    """De drie 'pass'-onderdelen zoals record 4 ze opsloeg (citaten letterlijk)."""
    return {
        ONDERDEEL_GEZAG: {
            "status": "pass",
            "reason": "De bron is de Algemene wet bestuursrecht, artikel 1:3.",
            "uncertainty": "Peildatum is niet opgegeven.",
            "evidence": [
                {
                    "source_id": "doc:01e121c20018eed2",
                    "quote": (
                        "Onder besluit wordt verstaan: een schriftelijke beslissing van "
                        "een bestuursorgaan, inhoudende een publiekrechtelijke "
                        "rechtshandeling."
                    ),
                }
            ],
            "sources": [
                {
                    "source_id": "doc:01e121c20018eed2",
                    "reason": "Bevat de wettelijke definitie van 'besluit'.",
                    "profile": "wet_regelgeving",
                    "applicable": True,
                }
            ],
        },
        ONDERDEEL_STEUN: {
            "status": "pass",
            "reason": "De bron ondersteunt letterlijk alle bepalende kenmerken.",
            "uncertainty": None,
            "evidence": [
                {
                    "source_id": "doc:01e121c20018eed2",
                    "quote": "een schriftelijke beslissing van een bestuursorgaan",
                }
            ],
            "claims": [
                {
                    "aspect": "kenmerk",
                    "text": "schriftelijke beslissing",
                    "supported": True,
                    "source_id": "doc:01e121c20018eed2",
                }
            ],
        },
        ONDERDEEL_VERWIJZING: {
            "status": "pass",
            "reason": (
                "De bron is precies terugvindbaar: de regeling en het exacte artikel "
                "en lid (Artikel 1:3 lid 1) worden in de passage genoemd."
            ),
            "uncertainty": None,
            "evidence": [dict(BEWIJS_AWB)],
            "sources": [
                {
                    "source_id": "doc:01e121c20018eed2",
                    "reason": "Bevat expliciete vindplaats.",
                    "locatable": True,
                }
            ],
        },
    }


def _assessment(bronnen, parts=None):
    canoniek = canoniseer_bronnen(bronnen)
    return {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": "con02-assess/1",
        "fingerprint": bereken_bronvingerafdruk(BEGRIP, TEKST, CONTEXT, bronnen),
        "status": "assessed",
        "error": None,
        "assessed_at": "2026-09-17T10:43:11.885916+00:00",
        "attribution": {
            "provider": "anthropic",
            "model": "opgeslagen-model",
            "task_type": "validation",
            "cached": False,
            "tokens_used": 1398,
        },
        "peildatum": None,
        "sources": [b.als_dict() for b in canoniek],
        "parts": parts if parts is not None else _parts_record4(),
        "rejected": [],
        "raw_response_sha256": None,
        "assessment_receipt": None,
    }


def _beoordeel(bronnen, **kw):
    return beoordeel_bronbasis(BEGRIP, TEKST, CONTEXT, bronnen, **kw)


def _part(uitkomst, onderdeel):
    return next(p for p in uitkomst.parts if p.id == onderdeel)


# --- domein: de technische controle ---------------------------------------------


class TestVerwijzingZonderHyperlink:
    def test_record4_zonder_url_krijgt_geen_gewone_verwijzings_pass(self):
        bronnen = [BRON_AWB]
        uitkomst = _beoordeel(bronnen, assessment=_assessment(bronnen))

        verwijzing = _part(uitkomst, ONDERDEEL_VERWIJZING)
        assert verwijzing.status == STATUS_OPEN
        assert verwijzing.field == BASIS_ASSESSMENT
        assert "hyperlink" in verwijzing.reason.casefold()
        assert "uitzondering" in verwijzing.reason.casefold()
        # De vindplaats-onderbouwing van het model blijft zichtbaar.
        assert "Artikel 1:3 lid 1" in verwijzing.reason
        assert "hyperlink" in verwijzing.action.casefold()
        assert "uitzondering" in verwijzing.action.casefold()
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["assessment"]["applied"] is True

    def test_brongezag_en_betekenissteun_blijven_onverminderd_pass(self):
        bronnen = [BRON_AWB]
        uitkomst = _beoordeel(bronnen, assessment=_assessment(bronnen))
        assert _part(uitkomst, ONDERDEEL_GEZAG).status == STATUS_PASS
        assert _part(uitkomst, ONDERDEEL_STEUN).status == STATUS_PASS

    def test_definitietekst_wordt_niet_aangeraakt(self):
        bronnen = [BRON_AWB]
        beoordeling = _assessment(bronnen)
        momentopname = deepcopy(beoordeling)
        uitkomst = _beoordeel(bronnen, assessment=beoordeling)
        assert beoordeling == momentopname
        assert uitkomst.fingerprint == bereken_bronvingerafdruk(
            BEGRIP, TEKST, CONTEXT, bronnen
        )
        assert (
            "Pas de definitie aan" not in _part(uitkomst, ONDERDEEL_VERWIJZING).action
        )

    def test_interne_hyperlink_volstaat_voor_pass(self):
        bronnen = [BRON_AWB_MET_LINK]
        uitkomst = _beoordeel(bronnen, assessment=_assessment(bronnen))
        assert _part(uitkomst, ONDERDEEL_VERWIJZING).status == STATUS_PASS
        assert uitkomst.status == STATUS_PASS

    def test_hyperlink_van_een_andere_bron_draagt_het_oordeel_niet(self):
        andere = {
            "provider": "web",
            "url": "https://intern.example/beleid",
            "title": "Beleidsnotitie",
            "snippet": "Een besluit is wat het bestuursorgaan besluit.",
            "score": 0.3,
        }
        bronnen = [BRON_AWB, andere]
        uitkomst = _beoordeel(bronnen, assessment=_assessment(bronnen))
        verwijzing = _part(uitkomst, ONDERDEEL_VERWIJZING)
        assert verwijzing.status == STATUS_OPEN
        assert "doc:01e121c20018eed2" in verwijzing.reason
        assert uitkomst.status == STATUS_OPEN

    def test_readback_van_een_eerder_opgeslagen_pass_gaat_niet_om_de_controle_heen(
        self,
    ):
        """Een oud positief AI-oordeel (con02-assess/1) telt bij replay niet meer als pass."""
        bronnen = [BRON_AWB]
        opgeslagen = _assessment(bronnen)
        opgeslagen["parts"][ONDERDEEL_VERWIJZING]["evidence"] = [
            {**BEWIJS_AWB, "locator": None}
        ]
        uitkomst = _beoordeel(bronnen, assessment=opgeslagen)
        assert uitkomst.review["assessment"]["applied"] is True
        assert uitkomst.review["assessment"]["prompt_version"] == "con02-assess/1"
        assert _part(uitkomst, ONDERDEEL_VERWIJZING).status == STATUS_OPEN
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["assessment"]["rejected"] == 1

    def test_afwijzing_is_herkenbaar_als_hyperlinkgebrek(self):
        from domain.sources.contract import valideer_onderdelen

        onderdelen, rejected = valideer_onderdelen(
            _parts_record4(), canoniseer_bronnen([BRON_AWB])
        )
        assert onderdelen[ONDERDEEL_VERWIJZING].status == STATUS_OPEN
        assert [r["part"] for r in rejected] == [ONDERDEEL_VERWIJZING]
        assert "hyperlink" in rejected[0]["reason"]
        assert "doc:01e121c20018eed2" in rejected[0]["detail"]


class TestDeskundigeRoutesBlijvenGelden:
    def _review(self, bronnen, **overrides):
        basis = {
            "type": REVIEW_TYPE_VERWIJZING,
            "accepted": True,
            "actor": "synthetische-deskundige",
            "rationale": "Het artikel is intern beschikbaar; er is geen hyperlink.",
            "version_number": 1,
            "fingerprint": bereken_bronvingerafdruk(BEGRIP, TEKST, CONTEXT, bronnen),
            "reviewed_at": "2026-09-17T12:00:00+00:00",
            "source_id": "doc:01e121c20018eed2",
            "content_hash": bereken_inhoudshash(PASSAGE_AWB),
            "source_version": None,
            "locator": "Awb art. 1:3 lid 1",
        }
        basis.update(overrides)
        return basis

    def test_verwijzingsuitzondering_blijft_zichtbaar_een_uitzondering(self):
        bronnen = [BRON_AWB]
        uitkomst = _beoordeel(
            bronnen,
            assessment=_assessment(bronnen),
            review=self._review(bronnen),
            definitie_versie=1,
        )
        verwijzing = _part(uitkomst, ONDERDEEL_VERWIJZING)
        assert verwijzing.status == STATUS_OPEN
        assert verwijzing.field == BASIS_REVIEW
        assert "uitzondering" in verwijzing.reason.casefold()
        assert "hyperlink" in verwijzing.reason.casefold()
        assert uitkomst.review["accepted_exception"] == "reference"
        assert uitkomst.status == STATUS_OPEN
        assert _part(uitkomst, ONDERDEEL_GEZAG).status == STATUS_PASS

    def test_uitzondering_bij_bron_met_link_blijft_niet_van_toepassing(self):
        bronnen = [BRON_AWB_MET_LINK]
        uitkomst = _beoordeel(
            bronnen,
            assessment=_assessment(bronnen),
            review=self._review(bronnen),
            definitie_versie=1,
        )
        assert uitkomst.review["applied"] is False
        assert "hyperlink" in uitkomst.review["reason"].casefold()
        assert _part(uitkomst, ONDERDEEL_VERWIJZING).status == STATUS_PASS

    def test_deskundige_correctie_naar_pass_vereist_ook_een_hyperlink(self):
        bewijs = {
            "source_id": "doc:01e121c20018eed2",
            "content_hash": bereken_inhoudshash(PASSAGE_AWB),
            "source_version": None,
            "quote": "Artikel 1:3",
            "locator": "Awb art. 1:3 lid 1",
        }

        def correctie(bronnen):
            return {
                "type": REVIEW_TYPE_CORRECTIE,
                "accepted": True,
                "actor": "synthetische-deskundige",
                "rationale": "De vindplaats is exact.",
                "version_number": 1,
                "fingerprint": bereken_bronvingerafdruk(
                    BEGRIP, TEKST, CONTEXT, bronnen
                ),
                "reviewed_at": None,
                "part_id": ONDERDEEL_VERWIJZING,
                "status": STATUS_PASS,
                "evidence": [dict(bewijs)],
            }

        zonder = _beoordeel(
            [BRON_AWB], review=correctie([BRON_AWB]), definitie_versie=1
        )
        assert zonder.review["applied"] is False
        assert "hyperlink" in zonder.review["reason"].casefold()
        assert _part(zonder, ONDERDEEL_VERWIJZING).status == STATUS_OPEN

        met = _beoordeel(
            [BRON_AWB_MET_LINK],
            review=correctie([BRON_AWB_MET_LINK]),
            definitie_versie=1,
        )
        assert met.review["applied_correction"]["part_id"] == ONDERDEEL_VERWIJZING
        assert _part(met, ONDERDEEL_VERWIJZING).status == STATUS_PASS


# --- Codex-review v1 (P1/P2): per dragende bron, en bruikbaarheid van de link ----

PASSAGE_BELEID = (
    "Beleidsregel besluitvorming, § 2: onder een schriftelijke beslissing wordt "
    "mede een elektronisch vastgelegde beslissing verstaan."
)
BRON_BELEID_MET_LINK = {
    "provider": "documents",
    "doc_id": "beleid-01",
    "filename": "beleidsregel-besluitvorming.txt",
    "title": "Beleidsregel besluitvorming",
    "citation_label": "§ 2",
    "url": "https://intern.example/beleid#p2",
    "snippet": PASSAGE_BELEID,
    "score": 0.9,
    "used_in_prompt": True,
}
BEWIJS_BELEID = {
    "source_id": "doc:beleid-01",
    "quote": "Beleidsregel besluitvorming, § 2",
}


def _parts_twee_dragende_bronnen():
    """A (Awb, zonder url) en B (beleid, met url) dragen elk een kenmerk; beide
    `locatable: true` met geverifieerd citaat — B mag het gebrek van A niet opheffen."""
    parts = _parts_record4()
    parts[ONDERDEEL_STEUN]["evidence"].append(dict(BEWIJS_BELEID))
    parts[ONDERDEEL_STEUN]["claims"].append(
        {
            "aspect": "kenmerk",
            "text": "elektronisch vastgelegde beslissing",
            "supported": True,
            "source_id": "doc:beleid-01",
        }
    )
    parts[ONDERDEEL_VERWIJZING]["evidence"].append(dict(BEWIJS_BELEID))
    parts[ONDERDEEL_VERWIJZING]["sources"].append(
        {
            "source_id": "doc:beleid-01",
            "reason": "Paragraaf genoemd.",
            "locatable": True,
        }
    )
    return parts


class TestPerDragendeBron:
    def test_gelinkte_bron_b_heft_ontbrekende_link_van_dragende_bron_a_niet_op(self):
        bronnen = [BRON_AWB, BRON_BELEID_MET_LINK]
        uitkomst = _beoordeel(
            bronnen,
            assessment=_assessment(bronnen, parts=_parts_twee_dragende_bronnen()),
        )
        verwijzing = _part(uitkomst, ONDERDEEL_VERWIJZING)
        assert verwijzing.status == STATUS_OPEN
        assert "doc:01e121c20018eed2" in verwijzing.reason
        assert "hyperlink" in verwijzing.reason.casefold()
        assert _part(uitkomst, ONDERDEEL_STEUN).status == STATUS_PASS
        assert uitkomst.status == STATUS_OPEN

    def test_beide_dragende_bronnen_met_link_geven_wel_pass(self):
        bronnen = [BRON_AWB_MET_LINK, BRON_BELEID_MET_LINK]
        uitkomst = _beoordeel(
            bronnen,
            assessment=_assessment(bronnen, parts=_parts_twee_dragende_bronnen()),
        )
        assert _part(uitkomst, ONDERDEEL_VERWIJZING).status == STATUS_PASS
        assert uitkomst.status == STATUS_PASS

    def test_menselijke_correctie_controleert_iedere_bewijsbron(self):
        def correctie(bronnen):
            return {
                "type": REVIEW_TYPE_CORRECTIE,
                "accepted": True,
                "actor": "synthetische-deskundige",
                "rationale": "Beide vindplaatsen zijn exact.",
                "version_number": 1,
                "fingerprint": bereken_bronvingerafdruk(
                    BEGRIP, TEKST, CONTEXT, bronnen
                ),
                "reviewed_at": None,
                "part_id": ONDERDEEL_VERWIJZING,
                "status": STATUS_PASS,
                "evidence": [
                    {
                        "source_id": "doc:01e121c20018eed2",
                        "content_hash": bereken_inhoudshash(PASSAGE_AWB),
                        "source_version": None,
                        "quote": "Artikel 1:3",
                        "locator": "Awb art. 1:3 lid 1",
                    },
                    {
                        "source_id": "doc:beleid-01",
                        "content_hash": bereken_inhoudshash(PASSAGE_BELEID),
                        "source_version": None,
                        "quote": "§ 2",
                        "locator": "§ 2",
                    },
                ],
            }

        gemengd = [BRON_AWB, BRON_BELEID_MET_LINK]
        zonder = _beoordeel(gemengd, review=correctie(gemengd), definitie_versie=1)
        assert zonder.review["applied"] is False
        assert "hyperlink" in zonder.review["reason"].casefold()
        assert "doc:01e121c20018eed2" in zonder.review["reason"]

        beide = [BRON_AWB_MET_LINK, BRON_BELEID_MET_LINK]
        met = _beoordeel(beide, review=correctie(beide), definitie_versie=1)
        assert met.review["applied_correction"]["part_id"] == ONDERDEEL_VERWIJZING


ONBRUIKBARE_LINKS = [
    "https://",
    "http://",
    "geen hyperlink",
    "   ",
    "https://intern.example/awb art 1",
    "https:// intern.example/awb",
    "javascript:alert(1)",
    "data:text/html,x",
    "ftp://intern.example/awb",
    "mailto:beheer@intern.example",
    "file:///srv/awb.txt",
    "intern.example/awb",
    "//intern.example/awb",
    "https://intern.example/awb\ttab",
    # Codex-review v2 (P2): ongeldige poort — urlsplit faalt pas bij `.port`.
    "https://intern.example:ongeldig/awb",
    "https://intern.example:99999/awb",
]
BRUIKBARE_LINKS = [
    "https://intern.example/awb#art-1-3",
    "http://intranet/awb?art=1:3",
    "https://wetten.overheid.nl/BWBR0005537/2026-01-01#Hoofdstuk1_Titeldeel1.1_Artikel1:3",
    "HTTPS://Intern.Example/Awb",
    "https://intranet.example:8443/awb#art-1-3",
]


class TestBruikbareHyperlink:
    @pytest.mark.parametrize("url", ONBRUIKBARE_LINKS)
    def test_onbruikbare_tekst_geldt_niet_als_hyperlink(self, url):
        from domain.sources.contract import is_bruikbare_hyperlink

        assert is_bruikbare_hyperlink(url) is False
        bronnen = [{**BRON_AWB, "url": url}]
        uitkomst = _beoordeel(bronnen, assessment=_assessment(bronnen))
        verwijzing = _part(uitkomst, ONDERDEEL_VERWIJZING)
        assert verwijzing.status == STATUS_OPEN, url
        assert "hyperlink" in verwijzing.reason.casefold()
        assert "hyperlink" in verwijzing.action.casefold()

    @pytest.mark.parametrize("url", BRUIKBARE_LINKS)
    def test_http_en_https_links_zijn_bruikbaar(self, url):
        from domain.sources.contract import is_bruikbare_hyperlink

        assert is_bruikbare_hyperlink(url) is True
        bronnen = [{**BRON_AWB, "url": url}]
        uitkomst = _beoordeel(bronnen, assessment=_assessment(bronnen))
        assert _part(uitkomst, ONDERDEEL_VERWIJZING).status == STATUS_PASS, url

    @pytest.mark.parametrize("waarde", [None, "", 7, True, ["https://x"]])
    def test_geen_tekst_is_geen_hyperlink(self, waarde):
        from domain.sources.contract import is_bruikbare_hyperlink

        assert is_bruikbare_hyperlink(waarde) is False

    def test_uitzondering_volgt_dezelfde_definitie_van_bruikbaar(self):
        """Een bron met onbruikbare url-tekst is een bron zónder bruikbare hyperlink:
        de verwijzingsuitzondering is dan van toepassing; met een echte link niet."""
        review = TestDeskundigeRoutesBlijvenGelden()._review
        onbruikbaar = [{**BRON_AWB, "url": "geen hyperlink"}]
        toegepast = _beoordeel(
            onbruikbaar,
            assessment=_assessment(onbruikbaar),
            review=review(onbruikbaar),
            definitie_versie=1,
        )
        assert toegepast.review["accepted_exception"] == "reference"
        assert _part(toegepast, ONDERDEEL_VERWIJZING).field == BASIS_REVIEW

        echt = [BRON_AWB_MET_LINK]
        niet = _beoordeel(
            echt, assessment=_assessment(echt), review=review(echt), definitie_versie=1
        )
        assert niet.review["applied"] is False
        assert "hyperlink" in niet.review["reason"].casefold()

    def test_uitzondering_geldt_ook_bij_ongeldige_poort(self):
        review = TestDeskundigeRoutesBlijvenGelden()._review
        bronnen = [{**BRON_AWB, "url": "https://intern.example:99999/awb"}]
        uitkomst = _beoordeel(
            bronnen,
            assessment=_assessment(bronnen),
            review=review(bronnen),
            definitie_versie=1,
        )
        assert uitkomst.review["accepted_exception"] == "reference"
        assert _part(uitkomst, ONDERDEEL_VERWIJZING).field == BASIS_REVIEW

    @pytest.mark.parametrize("url", ["https://", "https://intern.example:ongeldig/awb"])
    def test_menselijke_correctie_volgt_dezelfde_definitie_van_bruikbaar(self, url):
        bewijs = {
            "source_id": "doc:01e121c20018eed2",
            "content_hash": bereken_inhoudshash(PASSAGE_AWB),
            "source_version": None,
            "quote": "Artikel 1:3",
            "locator": "Awb art. 1:3 lid 1",
        }
        bronnen = [{**BRON_AWB, "url": url}]
        uitkomst = _beoordeel(
            bronnen,
            review={
                "type": REVIEW_TYPE_CORRECTIE,
                "accepted": True,
                "actor": "synthetische-deskundige",
                "rationale": "De vindplaats is exact.",
                "version_number": 1,
                "fingerprint": bereken_bronvingerafdruk(
                    BEGRIP, TEKST, CONTEXT, bronnen
                ),
                "reviewed_at": None,
                "part_id": ONDERDEEL_VERWIJZING,
                "status": STATUS_PASS,
                "evidence": [bewijs],
            },
            definitie_versie=1,
        )
        assert uitkomst.review["applied"] is False
        assert "hyperlink" in uitkomst.review["reason"].casefold()


# --- service: prompt noemt dezelfde voorwaarden, promptversie traceerbaar --------


class TestBeoordelingsprompt:
    def test_promptversie_is_opgehoogd(self):
        assert SourceAssessmentService.PROMPT_VERSION == "con02-assess/2"

    def test_systeemprompt_noemt_hyperlink_en_uitzonderingsvoorwaarden(self):
        systeem, _ = bouw_beoordelingsprompt(
            BEGRIP, TEKST, CONTEXT, canoniseer_bronnen([BRON_AWB])
        )
        blok = systeem.split("3. reference_quality", 1)[1].split("\n\nRegels", 1)[0]
        for fragment in (
            "hyperlink",
            "url",
            "interne",
            "review_required",
            "deskundige",
            "uitzondering",
            "bronversie",
            "vindplaats",
        ):
            assert fragment in blok.casefold(), fragment

    def test_gebruikersprompt_toont_de_url_alleen_als_die_er_is(self):
        _, zonder = bouw_beoordelingsprompt(
            BEGRIP, TEKST, CONTEXT, canoniseer_bronnen([BRON_AWB])
        )
        _, met = bouw_beoordelingsprompt(
            BEGRIP, TEKST, CONTEXT, canoniseer_bronnen([BRON_AWB_MET_LINK])
        )
        assert "url=" not in zonder
        assert 'url="https://intern.example/awb#art-1-3"' in met


class TestServiceZonderHyperlink:
    class _FakeAI:
        default_model = "fake-model"

        def __init__(self, uitvoer):
            import json

            self._tekst = json.dumps(uitvoer, ensure_ascii=False)

        async def generate_definition(self, prompt, **kwargs):
            from services.interfaces import AIGenerationResult

            return AIGenerationResult(
                text=self._tekst, model="fake-model", tokens_used=1, generation_time=0.0
            )

    @pytest.mark.asyncio
    async def test_dienst_levert_geen_verwijzings_pass_zonder_url(self):
        service = SourceAssessmentService(self._FakeAI(_parts_record4()))
        beoordeling = await service.assess(BEGRIP, TEKST, CONTEXT, [BRON_AWB])
        d = beoordeling.als_dict()
        assert d["status"] == "assessed"
        assert d["prompt_version"] == "con02-assess/2"
        assert d["parts"][ONDERDEEL_GEZAG]["status"] == STATUS_PASS
        assert d["parts"][ONDERDEEL_VERWIJZING]["status"] == STATUS_OPEN
        assert "hyperlink" in d["parts"][ONDERDEEL_VERWIJZING]["reason"].casefold()
        assert any("hyperlink" in r["reason"] for r in d["rejected"])

    @pytest.mark.asyncio
    async def test_dienst_levert_wel_pass_met_interne_url(self):
        service = SourceAssessmentService(self._FakeAI(_parts_record4()))
        beoordeling = await service.assess(BEGRIP, TEKST, CONTEXT, [BRON_AWB_MET_LINK])
        d = beoordeling.als_dict()
        assert d["parts"][ONDERDEEL_VERWIJZING]["status"] == STATUS_PASS
        assert d["rejected"] == []
