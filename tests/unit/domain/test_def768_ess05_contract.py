"""DEF-768 — ESS-05-contract: buren, gesloten modeluitvoer, samenvoeging, binding.

Toetst het domeincontract `domain.ess05.contract` zonder model, netwerk of DB.
Kern (K-3b, synthese v3): de vraag per buur is een kenmerkvraag, geen
extensievraag. ESS05-E05 (lener vs. werknemer; één persoon kan beide zijn)
voldoet; ESS05-E06 (beide 'persoon die in het systeem is geregistreerd')
voldoet niet — en kan in code nooit 'voldoet' worden: twee volledig gelijke
definities die toch als 'distinguished' terugkomen, zijn een technische fout.

Review 24-09 (correctie 5): een gedeelde subpassage met de buur is op zichzelf
géén technische fout (negatie of context kan verschillen). Code bewaakt alleen
wat code kan bewaken — citaat letterlijk in de kern, schema, ID's en herkomst,
volledig gelijke kernen; of een gedeelde passage inhoudelijk onderscheidt, is
een inhoudelijk oordeel. De gedeelde passage is dan een zichtbaar signaal in
de bestaande redenweergave en beslist niet over voldoet/voldoet niet.
"""

from __future__ import annotations

import hashlib
from copy import deepcopy

import pytest

from domain.ess03.contract import Intentie
from domain.ess05.contract import (
    CONTRACTVERSIE,
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_NOT_EVALUATED,
    STATUS_OPEN,
    STATUS_PASS,
    Buur,
    Ess05Beoordelingsbinding,
    OngeldigeBurenlijstError,
    beoordeel_onderscheid,
    beoordelingsmateriaal,
    bereken_ess05_vingerafdruk,
    buur_id,
    normaliseer_buren,
    pas_verificatie_toe,
    stel_burenlijst_samen,
    valideer_concept,
)
from tests.fixtures.def768_fakes import (
    bouw_document,
    concept_uit_spec,
    verificatie_voor,
)

pytestmark = [pytest.mark.unit]

BINDING = Ess05Beoordelingsbinding(
    prompt_version="ess05-assess/1",
    verification_prompt_version="ess05-verify/1",
    norm_sha256="n" * 64,
    provider="fake",
    model="m",
    verification_provider="fake",
    verification_model="m",
)
CONTEXT = {
    "organisatorische_context": ["Studiefinanciering"],
    "juridische_context": [],
    "wettelijke_basis": [],
}

LENER = "persoon met een actuele lening bij de instelling"
WERKNEMER = "persoon met een arbeidsovereenkomst met de instelling"
GEREGISTREERD = "persoon die in het systeem is geregistreerd"


def _buur(term, definitie, herkomst="gebruiker", bevestigd=True, **extra):
    return {
        "term": term,
        "definitie": definitie,
        "herkomst": herkomst,
        "bevestigd": bevestigd,
        **extra,
    }


def _document(begrip, tekst, buren, judgment, *, bronnen=None, intentie=None, **kw):
    """Een `/2`-document (concept + volledige verificatie) voor exact deze invoer.

    `judgment` is de eenvoudige testspecificatie die `concept_uit_spec` omzet
    in een gesloten conceptoordeel met exacte bewijsplaatsen.
    """
    return bouw_document(
        begrip,
        tekst,
        CONTEXT,
        bronnen or [],
        buren=buren,
        spec=judgment,
        intentie=intentie,
        binding=BINDING,
        **kw,
    )


def _oordeel(neighbours, *, lacks=False, proposals=None, question=None):
    return {
        "lacks_differentia": lacks,
        "reason": "Synthetische onderbouwing.",
        "neighbours": neighbours,
        "proposed_neighbours": proposals or [],
        "question": question,
    }


def _nb(buur_id_, distinction, quote=None, missing=None):
    return {
        "neighbour_id": buur_id_,
        "distinction": distinction,
        "distinguishing_feature_quote": quote,
        "missing_feature": missing,
        "reason": "Onderbouwing per buur.",
        "uncertainty": None,
    }


def _toegepast(spec, materiaal, buren, *, begrip, uitgesloten_termen=()):
    """(oordeel, fouten of genegeerde voorstellen) via concept + volledige verificatie."""
    concept, fouten = valideer_concept(
        concept_uit_spec(spec, materiaal), materiaal, buren
    )
    if concept is None:
        return None, fouten
    oordeel, uitkomst, rejected = pas_verificatie_toe(
        concept,
        verificatie_voor(concept.data),
        buren,
        begrip=begrip,
        uitgesloten_termen=uitgesloten_termen,
    )
    assert uitkomst.goedgekeurd
    return oordeel, rejected


def _beoordeel(begrip, tekst, buren, assessment=None, **kw):
    return beoordeel_onderscheid(
        begrip,
        tekst,
        kw.pop("contexten", CONTEXT),
        kw.pop("bronnen", []),
        buren=buren,
        assessment=assessment,
        binding=kw.pop("binding", BINDING),
        **kw,
    )


# --- buren ------------------------------------------------------------------------


class TestBuren:
    def test_id_is_deterministisch_per_herkomst_en_term(self):
        assert buur_id("gebruiker", "Werknemer") == buur_id("gebruiker", " werknemer ")
        assert buur_id("gebruiker", "werknemer") != buur_id("model", "werknemer")
        assert buur_id("repository", "x", db_id=12) == "repository:12"

    def test_normaliseer_vult_id_en_behoudt_herkomst(self):
        (buur,) = normaliseer_buren([_buur("werknemer", WERKNEMER)])
        assert isinstance(buur, Buur)
        assert buur.id == buur_id("gebruiker", "werknemer")
        assert (buur.herkomst, buur.bevestigd) == ("gebruiker", True)

    @pytest.mark.parametrize(
        "ruw",
        [
            "werknemer",
            [{"term": "", "herkomst": "gebruiker", "bevestigd": True}],
            [{"term": "x", "herkomst": "fantasie", "bevestigd": True}],
            [{"term": "x", "herkomst": "gebruiker", "bevestigd": "ja"}],
            [_buur("x", "a"), _buur("x", "b")],
        ],
    )
    def test_ongeldige_burenlijst_faalt_gesloten(self, ruw):
        with pytest.raises(OngeldigeBurenlijstError):
            normaliseer_buren(ruw)

    def test_ontologie_is_gereserveerd_maar_geldig(self):
        (buur,) = normaliseer_buren([_buur("x", None, "ontologie", False)])
        assert buur.herkomst == "ontologie"

    def test_afgewezen_buur_valt_uit_de_actieve_lijst(self):
        opgeslagen = [
            _buur("werknemer", WERKNEMER),
            _buur("klant", None, "model", False, afgewezen=True, grond="geen buur"),
        ]
        actief, afgewezen = stel_burenlijst_samen(opgeslagen, [])
        assert [b.term for b in actief] == ["werknemer"]
        assert afgewezen == ("klant",)

    def test_repository_buur_komt_vers_uit_de_database(self):
        vers = [{"id": 7, "begrip": "werknemer", "definitie": WERKNEMER}]
        actief, _ = stel_burenlijst_samen([], vers)
        (buur,) = actief
        assert (buur.id, buur.herkomst, buur.bevestigd) == (
            "repository:7",
            "repository",
            False,
        )
        assert buur.definitie == WERKNEMER

    def test_besluit_over_repository_buur_blijft_gelden_zolang_hij_bestaat(self):
        besluit = {
            "id": "repository:7",
            "term": "werknemer (oud)",
            "definitie": "oude tekst",
            "herkomst": "repository",
            "bevestigd": True,
        }
        vers = [{"id": 7, "begrip": "werknemer", "definitie": WERKNEMER}]
        (buur,), _ = stel_burenlijst_samen([besluit], vers)
        assert buur.bevestigd is True
        assert (buur.term, buur.definitie) == ("werknemer", WERKNEMER)
        actief, _ = stel_burenlijst_samen([besluit], [])
        assert actief == ()


# --- gesloten modeluitvoer ----------------------------------------------------------


class TestModeluitvoer:
    """Gesloten `/2`-concept via de contractgrens (details: test_def768_ess05_bewijs)."""

    def _setup(self):
        buren = normaliseer_buren([_buur("werknemer", WERKNEMER)])
        materiaal = beoordelingsmateriaal("lener", LENER, [], buren, contexten=CONTEXT)
        return buren, materiaal, buren[0].id

    def _concept(self):
        buren, materiaal, bid = self._setup()
        spec = _oordeel([_nb(bid, "distinguished", quote="met een actuele lening")])
        return buren, materiaal, concept_uit_spec(spec, materiaal)

    def test_geldig_onderscheid_met_citaat_uit_de_kern(self):
        buren, materiaal, bid = self._setup()
        oordeel, rejected = _toegepast(
            _oordeel([_nb(bid, "distinguished", quote="met een actuele lening")]),
            materiaal,
            buren,
            begrip="lener",
        )
        assert rejected == []
        assert oordeel.neighbours[0]["distinction"] == "distinguished"
        assert oordeel.neighbours[0]["distinguishing_feature_quote"] == (
            "met een actuele lening"
        )

    @pytest.mark.parametrize(
        "mutatie",
        [
            lambda c: c.update(satisfies_definition=True),  # oude planveld
            lambda c: c.update(lacks_differentia=True),  # geen modelindicator meer
            lambda c: c.update(status="pass"),  # status is een codebeslissing
            lambda c: c.update(reason="vrije paragraaf"),  # `/1`-veld
            lambda c: c.update(reason_claims=[]),
            lambda c: c.update(question={"text": "Twee? Vragen?", "claims": []}),
            lambda c: c.update(neighbours=[]),  # verzonden buur ontbreekt
            lambda c: c["neighbours"].append(deepcopy(c["neighbours"][0])),  # dubbel
            lambda c: c["neighbours"][0].update(neighbour_id="gebruiker:verzonnen"),
            lambda c: c["neighbours"][0].update(distinction="maybe"),
            lambda c: c["neighbours"][0].update(feature_evidence=None),
            lambda c: c["neighbours"][0].update(missing_feature_claim="C1"),
            lambda c: c["neighbours"][0].update(extra="veld"),
            lambda c: c.update(core_features=[]),  # afgeleid true naast distinguished
        ],
    )
    def test_structuurafwijking_is_een_technische_fout(self, mutatie):
        buren, materiaal, concept = self._concept()
        mutatie(concept)
        resultaat, fouten = valideer_concept(concept, materiaal, buren)
        assert resultaat is None
        assert fouten and fouten[0]["reason"] == "structuurfout"

    def test_not_distinguished_eist_ontbrekend_kenmerk_en_geen_citaat(self):
        buren, materiaal, bid = self._setup()
        zonder = concept_uit_spec(_oordeel([_nb(bid, "not_distinguished")]), materiaal)
        assert valideer_concept(zonder, materiaal, buren)[0] is None
        met_citaat = concept_uit_spec(
            _oordeel([_nb(bid, "not_distinguished", quote="persoon", missing="rol")]),
            materiaal,
        )
        assert valideer_concept(met_citaat, materiaal, buren)[0] is None

    def test_verzonnen_citaat_maakt_het_hele_oordeel_onbruikbaar(self):
        buren, materiaal, bid = self._setup()
        spec = _oordeel([_nb(bid, "distinguished", quote="met een hypotheek")])
        oordeel, fouten = _toegepast(spec, materiaal, buren, begrip="lener")
        assert oordeel is None
        assert fouten[0]["reason"] == "citaat wijkt af van de bewijsplaats"

    def test_citaat_uit_de_toelichting_telt_niet_als_kernfragment(self):
        buren = normaliseer_buren([_buur("werknemer", WERKNEMER)])
        intentie = Intentie(toelichting="zie de leenregeling")
        materiaal = beoordelingsmateriaal(
            "lener", LENER, [], buren, contexten=CONTEXT, intentie=intentie
        )
        concept = concept_uit_spec(
            _oordeel([_nb(buren[0].id, "distinguished", quote="leenregeling")]),
            materiaal,
        )
        plaats = next(e for e in concept["evidence"] if e["quote"] == "leenregeling")
        tekst = materiaal["meaning"]
        plaats.update(
            material_id="meaning",
            material_sha256=hashlib.sha256(tekst.encode()).hexdigest(),
            start=tekst.index("leenregeling"),
            end=tekst.index("leenregeling") + len("leenregeling"),
        )
        resultaat, fouten = valideer_concept(concept, materiaal, buren)
        assert resultaat is None and fouten[0]["reason"] == "structuurfout"

    def test_context_en_bedoelde_betekenis_zijn_bewijsplaats_voor_claims(self):
        buren = normaliseer_buren([])
        intentie = Intentie(toelichting="Het gaat om lopende leningen.")
        materiaal = beoordelingsmateriaal(
            "lener", LENER, [], buren, contexten=CONTEXT, intentie=intentie
        )
        assert materiaal["context"] == "organisatorische_context: Studiefinanciering"
        assert materiaal["meaning"] == "toelichting: Het gaat om lopende leningen."
        assert "categorie" not in materiaal["meaning"]

    def test_buur_zonder_definitie_kan_alleen_onduidelijk_zijn(self):
        buren = normaliseer_buren([_buur("werknemer", None)])
        materiaal = beoordelingsmateriaal("lener", LENER, [], buren, contexten=CONTEXT)
        bid = buren[0].id
        onderscheiden = concept_uit_spec(
            _oordeel([_nb(bid, "distinguished", quote="actuele lening")]), materiaal
        )
        assert valideer_concept(onderscheiden, materiaal, buren)[0] is None
        onduidelijk = concept_uit_spec(_oordeel([_nb(bid, "unclear")]), materiaal)
        assert valideer_concept(onduidelijk, materiaal, buren)[0] is not None

    def test_voorstel_uit_bron_moet_letterlijk_in_de_bron_staan(self):
        bronnen = [{"source_id": "wet-1", "content": "De lener en de borg tekenen."}]
        buren = normaliseer_buren([])
        materiaal = beoordelingsmateriaal("lener", LENER, bronnen, buren)
        bron_id = next(k for k in materiaal if k.startswith("source:"))[7:]

        def voorstel(citaat):
            return _oordeel(
                [],
                proposals=[
                    {
                        "term": "borg",
                        "source_id": bron_id,
                        "quote": citaat,
                        "reason": "r",
                    }
                ],
            )

        oordeel, _ = _toegepast(voorstel("de borg"), materiaal, buren, begrip="lener")
        assert oordeel.proposed_neighbours[0]["source_id"] == bron_id
        assert oordeel.proposed_neighbours[0]["quote"] == "de borg"
        oordeel, fouten = _toegepast(
            voorstel("de gever"), materiaal, buren, begrip="lener"
        )
        assert oordeel is None
        assert fouten[0]["reason"] == "citaat wijkt af van de bewijsplaats"

    def test_voorstel_van_bekende_of_afgewezen_buur_wordt_zichtbaar_genegeerd(self):
        buren, materiaal, bid = self._setup()
        spec = _oordeel(
            [_nb(bid, "distinguished", quote="met een actuele lening")],
            proposals=[
                {"term": "Werknemer", "source_id": None, "quote": None, "reason": "r"},
                {"term": "klant", "source_id": None, "quote": None, "reason": "r"},
                {"term": "borg", "source_id": None, "quote": None, "reason": "r"},
            ],
        )
        oordeel, rejected = _toegepast(
            spec, materiaal, buren, begrip="lener", uitgesloten_termen=("klant",)
        )
        assert [p["term"] for p in oordeel.proposed_neighbours] == ["borg"]
        assert {r["detail"] for r in rejected} == {"Werknemer", "klant"}

    def test_ongeverifieerd_concept_levert_nooit_een_oordeel(self):
        buren, materiaal, concept = self._concept()
        gevalideerd, _ = valideer_concept(concept, materiaal, buren)
        for verificatie in (
            None,
            verificatie_voor(concept, uitkomsten={"completeness": "unsupported"}),
            verificatie_voor(concept, uitkomsten={"claim:C1": "undetermined"}),
            verificatie_voor(concept, candidate_hash="0" * 64),
        ):
            oordeel, uitkomst, _ = pas_verificatie_toe(
                gevalideerd, verificatie, buren, begrip="lener"
            )
            assert oordeel is None and not uitkomst.goedgekeurd

    def test_zichtbare_teksten_zijn_gecontroleerde_claims(self):
        buren, materiaal, bid = self._setup()
        spec = _oordeel([_nb(bid, "not_distinguished", missing="het leenkenmerk")])
        oordeel, _ = _toegepast(spec, materiaal, buren, begrip="lener")
        (buur,) = oordeel.neighbours
        assert buur["missing_feature"].startswith("het leenkenmerk.")
        assert "[definitie: “" in buur["missing_feature"]
        assert oordeel.lacks_differentia is False


# --- samenvoeging (K-3b, E05/E06, K-8, K-1, K-2) -------------------------------------


class TestSamenvoeging:
    def test_e05_verschillende_rolkenmerken_voldoen(self):
        buren = [_buur("werknemer", WERKNEMER)]
        bid = normaliseer_buren(buren)[0].id
        doc = _document(
            "lener",
            LENER,
            buren,
            _oordeel([_nb(bid, "distinguished", quote="met een actuele lening")]),
        )
        uitkomst = _beoordeel("lener", LENER, buren, doc)
        assert uitkomst.status == STATUS_PASS
        assert uitkomst.als_dict()["score"] is None

    def test_e06_zelfde_omschrijving_voldoet_niet_met_inhoudelijke_reden(self):
        buren = [_buur("klant", GEREGISTREERD)]
        bid = normaliseer_buren(buren)[0].id
        doc = _document(
            "gebruiker",
            GEREGISTREERD,
            buren,
            _oordeel(
                [
                    _nb(
                        bid,
                        "not_distinguished",
                        missing="de rol ten opzichte van de dienst",
                    )
                ]
            ),
        )
        uitkomst = _beoordeel("gebruiker", GEREGISTREERD, buren, doc)
        assert uitkomst.status == STATUS_FAIL
        reden = uitkomst.parts[0].reason
        assert "klant" in reden and "de rol ten opzichte van de dienst" in reden

    @pytest.mark.parametrize(
        "buurtekst",
        [GEREGISTREERD, "  Persoon die in het  systeem is geregistreerd. "],
    )
    def test_e06_kan_in_code_nooit_voldoen_met_gelijke_definities(self, buurtekst):
        buren = normaliseer_buren([_buur("klant", buurtekst)])
        materiaal = beoordelingsmateriaal("gebruiker", GEREGISTREERD, [], buren)
        ruw = _oordeel(
            [_nb(buren[0].id, "distinguished", quote="in het systeem is geregistreerd")]
        )
        oordeel, rejected = _toegepast(ruw, materiaal, buren, begrip="gebruiker")
        assert oordeel is None
        assert rejected[0]["reason"] == "kern gelijk aan de buurdefinitie"

    def test_gedeelde_subpassage_met_negatie_is_geen_technische_fout(self):
        """'beschikt over' vs. 'beschikt niet over': dezelfde woorden, ander kenmerk."""
        met = "persoon die beschikt over een geldige vergunning"
        zonder = "persoon die niet beschikt over een geldige vergunning"
        buren = [_buur("illegale exploitant", zonder)]
        bid = normaliseer_buren(buren)[0].id
        doc = _document(
            "vergunninghouder",
            met,
            buren,
            _oordeel([_nb(bid, "distinguished", quote="beschikt over een geldige")]),
        )
        uitkomst = _beoordeel("vergunninghouder", met, buren, doc)
        assert uitkomst.status == STATUS_PASS
        (buurdeel,) = [p for p in uitkomst.parts if p.context_value]
        assert buurdeel.status == STATUS_PASS
        assert "staat ook in de buurdefinitie" in buurdeel.reason

    @pytest.mark.parametrize(
        "citaat",
        [
            "actuele lening",
            "persoon met een actuele lening bij de instelling",  # hele kern
        ],
    )
    def test_citaatlengte_beslist_niet_zolang_het_citaat_in_de_kern_staat(self, citaat):
        buren = normaliseer_buren([_buur("werknemer", WERKNEMER)])
        materiaal = beoordelingsmateriaal("lener", LENER, [], buren)
        ruw = _oordeel([_nb(buren[0].id, "distinguished", quote=citaat)])
        oordeel, rejected = _toegepast(ruw, materiaal, buren, begrip="lener")
        assert oordeel is not None and rejected == []

    def test_citaat_langer_dan_de_kern_blijft_een_harde_fout(self):
        buren = normaliseer_buren([_buur("werknemer", WERKNEMER)])
        materiaal = beoordelingsmateriaal("lener", LENER, [], buren)
        ruw = _oordeel([_nb(buren[0].id, "distinguished", quote=f"{LENER} of borg")])
        oordeel, rejected = _toegepast(ruw, materiaal, buren, begrip="lener")
        assert oordeel is None
        assert rejected[0]["reason"] == "bewijsplaats buiten bereik"

    def test_gelijkwaardige_parafrase_met_niet_onderscheiden_voldoet_niet(self):
        """Code herkent geen parafrase; het modeloordeel draagt de afkeuring."""
        parafrase = "persoon die staat ingeschreven in het register van het systeem"
        buren = [_buur("klant", parafrase)]
        bid = normaliseer_buren(buren)[0].id
        doc = _document(
            "gebruiker",
            GEREGISTREERD,
            buren,
            _oordeel([_nb(bid, "not_distinguished", missing="rol ten opzichte van")]),
        )
        assert _beoordeel("gebruiker", GEREGISTREERD, buren, doc).status == STATUS_FAIL

    # ASTRA-paar (correctie 4). De buurdefinitie van 'ontvluchting' is
    # SYNTHETISCH (niet uit ASTRA); de modeloordelen zijn fakes. Dit bewijst de
    # samenvoeging en de codegrens, geen AI-kwaliteit.
    ASTRA_FOUT = (
        "Incident waarbij een jeugdige zonder toestemming de justitiële "
        "jeugdinrichting verlaat."
    )
    ASTRA_GOED = (
        "Incident waarbij een jeugdige zonder toestemming één van de volgende "
        "justitiële voorzieningen verlaat: de open justitiële jeugdinrichting of "
        "het terrein dat tot de gesloten justitiële jeugdinrichting behoort."
    )
    ONTVLUCHTING_SYNTHETISCH = (
        "Incident waarbij een jeugdige zonder toestemming de beveiligde grens van "
        "een gesloten justitiële jeugdinrichting doorbreekt."
    )

    def _astra(self, tekst, neighbour):
        buren = [_buur("ontvluchting", self.ONTVLUCHTING_SYNTHETISCH)]
        bid = normaliseer_buren(buren)[0].id
        doc = _document("onttrekking", tekst, buren, _oordeel([neighbour(bid)]))
        return _beoordeel("onttrekking", tekst, buren, doc)

    def test_astra_fout_voldoet_niet(self):
        uitkomst = self._astra(
            self.ASTRA_FOUT,
            lambda bid: _nb(
                bid, "not_distinguished", missing="de voorziening die wordt verlaten"
            ),
        )
        assert uitkomst.status == STATUS_FAIL

    def test_astra_goed_voldoet(self):
        uitkomst = self._astra(
            self.ASTRA_GOED,
            lambda bid: _nb(
                bid,
                "distinguished",
                quote="één van de volgende justitiële voorzieningen",
            ),
        )
        assert uitkomst.status == STATUS_PASS

    def test_codegrens_beperkt_kenmerk_jeugdige_krijgt_alleen_een_signaal(self):
        """Een (foutief) 'distinguished' op alleen 'jeugdige' kan code niet weren.

        'jeugdige' staat ook in de buurdefinitie: dat wordt zichtbaar als
        signaal. Dat zo'n kenmerk niets afgrenst, is een inhoudelijk oordeel
        (T-instructie); de code bewaakt het niet en claimt dat ook niet.
        """
        uitkomst = self._astra(
            self.ASTRA_FOUT,
            lambda bid: _nb(bid, "distinguished", quote="jeugdige"),
        )
        (buurdeel,) = [p for p in uitkomst.parts if p.context_value]
        assert "staat ook in de buurdefinitie" in buurdeel.reason

    def test_zonder_gedeelde_passage_geen_signaal(self):
        buren = [_buur("werknemer", WERKNEMER)]
        bid = normaliseer_buren(buren)[0].id
        doc = _document(
            "lener",
            LENER,
            buren,
            _oordeel([_nb(bid, "distinguished", quote="met een actuele lening")]),
        )
        uitkomst = _beoordeel("lener", LENER, buren, doc)
        assert all("buurdefinitie" not in p.reason for p in uitkomst.parts)

    def test_k8_ontbrekende_toespitsing_is_een_eigen_ess05_reden(self):
        doc = _document("gebruiker", "persoon", [], _oordeel([], lacks=True))
        uitkomst = _beoordeel("gebruiker", "persoon", [], doc)
        assert uitkomst.status == STATUS_FAIL
        assert "geen enkel verwant begrip" in uitkomst.parts[0].reason

    def test_geen_buren_is_open_met_precies_een_vraag(self):
        doc = _document("lener", LENER, [], _oordeel([]))
        uitkomst = _beoordeel("lener", LENER, [], doc)
        assert uitkomst.status == STATUS_OPEN
        vraag = uitkomst.review["question"]
        assert vraag.endswith("?") and vraag.count("?") == 1

    def test_modelvoorstel_blijft_onbevestigd_en_maakt_open(self):
        buren = [_buur("werknemer", WERKNEMER)]
        bid = normaliseer_buren(buren)[0].id
        doc = _document(
            "lener",
            LENER,
            buren,
            _oordeel(
                [_nb(bid, "distinguished", quote="met een actuele lening")],
                proposals=[
                    {"term": "borg", "source_id": None, "quote": None, "reason": "r"}
                ],
            ),
        )
        uitkomst = _beoordeel("lener", LENER, buren, doc)
        assert uitkomst.status == STATUS_OPEN
        (voorstel,) = uitkomst.review["proposals"]
        assert (voorstel["herkomst"], voorstel["bevestigd"]) == ("model", False)
        assert "borg" in uitkomst.review["question"]

    @pytest.mark.parametrize(
        ("herkomst", "verwacht"),
        [("repository", STATUS_PASS), ("bron", STATUS_OPEN), ("model", STATUS_OPEN)],
    )
    def test_beslisvolgorde_onbevestigde_onderscheiden_buur(self, herkomst, verwacht):
        """Bestaande implementatiekeuze (review 24-09, correctie 2; binnen K-1/K-2).

        Een onbevestigde repositorybuur die 'distinguished' is, blokkeert 'voldoet'
        niet zolang minstens één bevestigde buur onderscheiden is; een
        onbevestigde bron-/model-/ontologiebuur houdt de uitkomst open.
        """
        buren = [
            _buur("werknemer", WERKNEMER),
            _buur(
                "borg",
                "persoon die instaat voor de schuld van een ander",
                herkomst,
                False,
            ),
        ]
        ids = [b.id for b in normaliseer_buren(buren)]
        doc = _document(
            "lener",
            LENER,
            buren,
            _oordeel(
                [_nb(i, "distinguished", quote="met een actuele lening") for i in ids]
            ),
        )
        assert _beoordeel("lener", LENER, buren, doc).status == verwacht

    def test_onbevestigde_buur_niet_onderscheiden_keurt_niet_af(self):
        buren = [_buur("klant", GEREGISTREERD, "repository", False, id="repository:3")]
        doc = _document(
            "gebruiker",
            GEREGISTREERD,
            buren,
            _oordeel([_nb("repository:3", "not_distinguished", missing="rol")]),
        )
        uitkomst = _beoordeel("gebruiker", GEREGISTREERD, buren, doc)
        assert uitkomst.status == STATUS_OPEN

    def test_bevestigde_onduidelijke_buur_geeft_de_modelvraag(self):
        buren = [_buur("werknemer", WERKNEMER)]
        bid = normaliseer_buren(buren)[0].id
        doc = _document(
            "lener",
            LENER,
            buren,
            _oordeel(
                [_nb(bid, "unclear")], question="Telt een afgeloste lening nog mee?"
            ),
        )
        uitkomst = _beoordeel("lener", LENER, buren, doc)
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["question"] == "Telt een afgeloste lening nog mee?"

    def test_per_buur_een_zichtbaar_onderdeel(self):
        buren = [_buur("werknemer", WERKNEMER)]
        bid = normaliseer_buren(buren)[0].id
        doc = _document(
            "lener",
            LENER,
            buren,
            _oordeel([_nb(bid, "distinguished", quote="met een actuele lening")]),
        )
        ids = [p.id for p in _beoordeel("lener", LENER, buren, doc).parts]
        assert ids == ["distinction", f"neighbour:{bid}"]


# --- invoer, fouten, binding ---------------------------------------------------------


class TestInvoerEnBinding:
    def test_zonder_context_niet_beoordeeld(self):
        leeg = {k: [] for k in CONTEXT}
        uitkomst = _beoordeel("lener", LENER, [], contexten=leeg)
        assert uitkomst.status == STATUS_NOT_EVALUATED
        assert "context" in uitkomst.parts[0].reason

    @pytest.mark.parametrize(("term", "tekst"), [("", LENER), ("lener", "  ")])
    def test_zonder_term_of_tekst_niet_beoordeeld(self, term, tekst):
        assert _beoordeel(term, tekst, []).status == STATUS_NOT_EVALUATED

    def test_ongeldige_burenlijst_is_een_technische_fout(self):
        uitkomst = _beoordeel("lener", LENER, "geen lijst")
        assert uitkomst.status == STATUS_ERROR

    def test_zonder_beoordeling_open_nooit_pass(self):
        uitkomst = _beoordeel("lener", LENER, [_buur("werknemer", WERKNEMER)])
        assert uitkomst.status == STATUS_OPEN

    def test_foutdocument_is_error(self):
        doc = {
            "contract_version": CONTRACTVERSIE,
            "status": "error",
            "fingerprint": "x",
            "error": {"type": "timeout", "message": "t"},
        }
        assert _beoordeel("lener", LENER, [], doc).status == STATUS_ERROR

    def test_gewijzigde_buurdefinitie_maakt_beoordeling_historisch(self):
        buren = [_buur("werknemer", WERKNEMER)]
        bid = normaliseer_buren(buren)[0].id
        doc = _document(
            "lener",
            LENER,
            buren,
            _oordeel([_nb(bid, "distinguished", quote="met een actuele lening")]),
        )
        gewijzigd = [_buur("werknemer", WERKNEMER + " of uitzendovereenkomst")]
        uitkomst = _beoordeel("lener", LENER, gewijzigd, doc)
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["assessment"]["historical"] is True

    def test_andere_binding_maakt_beoordeling_historisch(self):
        buren = [_buur("werknemer", WERKNEMER)]
        bid = normaliseer_buren(buren)[0].id
        doc = _document(
            "lener",
            LENER,
            buren,
            _oordeel([_nb(bid, "distinguished", quote="met een actuele lening")]),
        )
        ander = Ess05Beoordelingsbinding(
            **{**BINDING.als_dict(), "prompt_version": "ess05-assess/2"}
        )
        uitkomst = _beoordeel("lener", LENER, buren, doc, binding=ander)
        assert uitkomst.status == STATUS_OPEN

    def test_bedoelde_betekenis_hoort_bij_de_vingerafdruk(self):
        een = bereken_ess05_vingerafdruk("lener", LENER, CONTEXT, [], buren=())
        twee = bereken_ess05_vingerafdruk(
            "lener", LENER, CONTEXT, [], buren=(), intentie=Intentie(toelichting="x")
        )
        assert een != twee


class TestLegeRuimte:
    def _bevestiging(self, **overschrijf):
        basis = {
            "fingerprint": bereken_ess05_vingerafdruk(
                "lener", LENER, CONTEXT, [], buren=()
            ),
            "contract_version": CONTRACTVERSIE,
            "grond": "In deze context bestaat geen ander leenbegrip.",
            "actor": "deskundige",
            "at": "2026-09-23T10:00:00+00:00",
        }
        return {**basis, **overschrijf}

    def test_gemotiveerde_bevestiging_voldoet_zonder_modelcall(self):
        uitkomst = _beoordeel("lener", LENER, [], lege_ruimte=self._bevestiging())
        assert uitkomst.status == STATUS_PASS
        assert uitkomst.parts[0].field == "ess05_empty_space"

    @pytest.mark.parametrize("veld", ["grond", "actor"])
    def test_zonder_grond_of_actor_telt_de_bevestiging_niet(self, veld):
        uitkomst = _beoordeel(
            "lener", LENER, [], lege_ruimte=self._bevestiging(**{veld: " "})
        )
        assert uitkomst.status == STATUS_OPEN

    def test_bevestiging_vervalt_bij_gewijzigde_tekst(self):
        uitkomst = _beoordeel(
            "lener", LENER + " of borg", [], lege_ruimte=self._bevestiging()
        )
        assert uitkomst.status == STATUS_OPEN

    def test_bevestiging_telt_niet_zodra_er_buren_zijn(self):
        uitkomst = _beoordeel(
            "lener",
            LENER,
            [_buur("werknemer", WERKNEMER)],
            lege_ruimte=self._bevestiging(),
        )
        assert uitkomst.status == STATUS_OPEN


# --- `/2`: tweestapsbinding en replay (ADR-003) ---------------------------------------


class TestTweestapsReplay:
    BUREN = [_buur("werknemer", WERKNEMER, "repository", False, id="repository:4")]

    def _doc(self, **kw):
        spec = _oordeel(
            [_nb("repository:4", "distinguished", quote="met een actuele lening")]
        )
        return _document("lener", LENER, self.BUREN, spec, **kw)

    def _status(self, doc, buren=None, **kw):
        return _beoordeel("lener", LENER, buren or self.BUREN, doc, **kw)

    def test_volledig_geverifieerd_wordt_toegepast(self):
        uitkomst = self._status(self._doc())
        assert uitkomst.review["assessment"]["applied"] is True
        assert uitkomst.review["assessment"]["verification"] == {
            "approved": True,
            "type": None,
        }

    @pytest.mark.parametrize(
        "sabotage",
        [
            lambda d: d.update(verification=None),
            lambda d: d.update(verification_input=None),
            lambda d: d.update(concept=None),
            lambda d: d["verification"]["checks"].pop(),
            lambda d: d["verification"]["checks"][0].update(outcome="undetermined"),
            lambda d: d["concept"]["claims"][0].update(text="Andere claim."),
        ],
    )
    def test_zonder_geldige_verificatie_nooit_een_toegepast_oordeel(self, sabotage):
        doc = self._doc()
        sabotage(doc)
        uitkomst = self._status(doc)
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["assessment"]["applied"] is False
        assert "Voldoet" not in uitkomst.parts[0].reason

    def test_opgeslagen_judgment_is_alleen_weergave(self):
        """Replay leidt het oordeel af uit concept + verificatie, niet uit `judgment`."""
        doc = self._doc()
        doc["judgment"]["lacks_differentia"] = True
        assert self._status(doc).status != STATUS_FAIL

    @pytest.mark.parametrize(
        "veld",
        [
            "verification_prompt_version",
            "verification_model",
            "verification_provider",
            "schema_version",
            "verification_schema_version",
            "renderer_version",
        ],
    )
    def test_elke_bindingswijziging_maakt_historisch(self, veld):
        ander = Ess05Beoordelingsbinding(**{**BINDING.als_dict(), veld: "anders"})
        uitkomst = self._status(self._doc(), binding=ander)
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["assessment"]["historical"] is True
        assert veld in uitkomst.review["assessment"]["reason"]

    def test_buurbevestiging_na_beoordeling_maakt_historisch(self):
        bevestigd = [dict(self.BUREN[0], bevestigd=True)]
        uitkomst = self._status(self._doc(), buren=bevestigd)
        assert uitkomst.review["assessment"]["historical"] is True
        assert "buurbevestiging" in uitkomst.review["assessment"]["reason"]

    def test_afgewezen_voorstel_na_beoordeling_maakt_historisch(self):
        uitkomst = self._status(self._doc(), uitgesloten_termen=("borg",))
        assert uitkomst.review["assessment"]["historical"] is True

    def test_gelijke_afwijzingen_blijven_actueel(self):
        doc = self._doc(uitgesloten_termen=("Borg",))
        uitkomst = self._status(doc, uitgesloten_termen=(" borg ",))
        assert uitkomst.review["assessment"]["applied"] is True

    def test_contractversie_1_blijft_historie(self):
        doc = self._doc()
        doc["contract_version"] = "ess05/1"
        uitkomst = self._status(doc)
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["assessment"]["historical"] is True
        assert "ess05/1" in uitkomst.review["assessment"]["reason"]

    def test_semantische_weigering_is_geen_oordeel_over_de_definitie(self):
        from tests.fixtures.def768_fakes import bouw_ess05_beoordeling

        doc = bouw_ess05_beoordeling(
            "lener", LENER, CONTEXT, buren=self.BUREN, scenario="semantic"
        )
        uitkomst = self._status(doc)
        assert uitkomst.status == STATUS_ERROR
        reden = uitkomst.parts[0].reason
        assert "geen oordeel over de definitie" in reden
        assert uitkomst.review["assessment"]["phase"] == "verification"
        assert "Voeg in de kern" not in uitkomst.parts[0].action

    def test_kop_noemt_beide_modellen(self):
        reden = self._status(self._doc()).parts[0].reason
        assert "semantisch geverifieerd door m" in reden


class TestBindingstype:
    def test_rondreis_en_gesloten_parser(self):
        assert Ess05Beoordelingsbinding.uit_dict(BINDING.als_dict()) == BINDING
        assert Ess05Beoordelingsbinding.uit_dict({"model": "vervalst"}) is None
        onvolledig = dict(BINDING.als_dict(), verification_prompt_version="")
        assert Ess05Beoordelingsbinding.uit_dict(onvolledig) is None
        extra = dict(BINDING.als_dict(), extra="x")
        assert Ess05Beoordelingsbinding.uit_dict(extra) is None

    def test_ess03_binding_blijft_ongewijzigd(self):
        from domain.ess03.contract import Beoordelingsbinding

        assert set(Beoordelingsbinding.__dataclass_fields__) == {
            "prompt_version",
            "norm_sha256",
            "provider",
            "model",
        }

    def test_contractversie_is_2(self):
        assert CONTRACTVERSIE == "ess05/2"
