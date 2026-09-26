"""DEF-772 WP3: het INT-03-verwijzingscontract (K1, K2 T-c, K6, K7).

Bron: besluiten-chris-v1.md (K2 T-c, K6, K7) en de uitvoeringsopdracht WP3.
Alle verwachtingen hieronder zijn uit die bron afgeleid, niet uit het gedrag
van de implementatie.

Wat deze tests bewijzen (zuiver domein, geen AI, geen Streamlit):

- de vingerafdruk bindt aan term, exacte tekst, de drie contextlijsten en de
  toelichting — verandert daar iets, dan geldt een eerdere beoordeling niet;
- het modelantwoord is een gesloten structuur: vijf velden, per verwijzing
  vijf velden, statussen uit een gesloten set, kandidaten passend bij de
  status, verdict consistent met de door code afgeleide bevinding, precies
  één gerichte vraag bij `insufficient_information` (bij `fail` mag er een
  herstelvraag naast staan, bij `pass` nooit);
- citaten worden door code gecontroleerd: elk verwijzend woord staat als heel
  woord in de definitie én in zijn passage, elke passage en elk
  kandidaatscitaat staat letterlijk in de definitie; één verzonnen citaat
  maakt het hele oordeel onbruikbaar (fail-closed);
- replay: een ontbrekende beoordeling is expliciet niet uitgevoerd (nooit
  pass); een beoordeling van een andere tekst/term/context/toelichting,
  promptversie, norm of model is historisch;
- samenstelling: pass / fail (woord + kandidaten, of lege kandidatenlijst
  met motivering bij ontbrekend antecedent) / review_required met precies
  één vraag / error; zonder verwijzend woord `pass` met exact de motivering
  "niet van toepassing: de definitie bevat geen verwijzend voornaamwoord" en
  een herkenbare bevinding voor de UI; nooit een cijfer.

Formaatcontrole bewijst geen semantische juistheid; de gevallen zijn de
A/B/C/D-ontwikkelgevallen (WP2-record), geen goldset.

Reviewcorrecties (review-codex-wp3-v1, dispositie v3): meldingen over een
structuurfout of afgewezen citaat dragen nooit tekst uit het modelantwoord
(R2); een structureel ongeldige of niet-verifieerbare beoordeling is bij
replay een technische fout (`error`), terwijl ontbrekend, niet beschikbaar
en historisch open blijven (R4).
"""

from __future__ import annotations

import pytest

from domain.int03.contract import (
    BASIS_ASSESSMENT,
    BEVINDING_DUIDELIJK,
    BEVINDING_GEEN_ANTECEDENT,
    BEVINDING_GEEN_VERWIJZEND_WOORD,
    BEVINDING_MEERDUIDIG,
    BEVINDING_ONBESLIST,
    CONTRACTVERSIE,
    MOTIVERING_GEEN_VERWIJZEND_WOORD,
    ONDERDEEL_VERWIJZING,
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_OPEN,
    STATUS_PASS,
    VERDICT_FAIL,
    VERDICT_INSUFFICIENT,
    VERDICT_PASS,
    VERWIJZING_DUIDELIJK,
    VERWIJZING_GEEN_ANTECEDENT,
    VERWIJZING_MEERDUIDIG,
    VERWIJZING_NIET_VERWIJZEND,
    VERWIJZING_ONBESLIST,
    Beoordelingsbinding,
    afgeleide_bevinding,
    beoordeel_verwijzingen,
    beoordeling_niet_beschikbaar,
    beoordeling_technische_fout,
    bereken_int03_vingerafdruk,
    structuurfout_modeluitvoer,
    toelichting_uit_context,
    valideer_beoordeling,
    valideer_oordeel,
)
from tests.fixtures.def772_fakes import BINDING, MODEL, bouw_int03_beoordeling

pytestmark = [pytest.mark.unit]

TERM = "proefbegrip"
CONTEXT = {
    "organisatorische_context": ["Synthetische Organisatie"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
TOELICHTING = "Synthetische toelichting."

#: ASTRA-paar (letterlijk uit INT-03.json, WP2).
ASTRA_GOED = (
    "Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die "
    "de basis vormen waardoor die gebeurtenis volledig kan worden begrepen en "
    "geanalyseerd."
)
ASTRA_FOUT = (
    "Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die "
    "de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd."
)
DEZE_VERTREKT = "handeling van een medewerker aan een collega waarbij deze vertrekt"
HET_VOORTGEZET = "voorziening waardoor het kan worden voortgezet"
PERSOON_DIE = "persoon die wordt verdacht van een strafbaar feit"
GEEN_WOORD = "veelhoek met precies drie zijden"
VOEGWOORD_DAT = "verklaring dat een aanvraag volledig is"
#: Synthetische modeltekst die nooit in een melding mag belanden (R2).
MODELTEKST = "ZZPRIVEZZ"


def _verwijzing(
    word: str,
    passage: str,
    status: str,
    candidates: list[dict[str, str]] | None = None,
    reading: str = "interpretatie",
) -> dict:
    return {
        "word": word,
        "passage": passage,
        "status": status,
        "reading": reading,
        "candidates": list(candidates or []),
    }


#: Ontwikkelgevallen als modelantwoorden (synthetisch, geen modelkwaliteit).
ANTWOORD_ASTRA_GOED = {
    "verdict": VERDICT_PASS,
    "reason": "Elk 'die' verwijst eenduidig naar 'omstandigheden' of 'gebeurtenis'.",
    "references": [
        _verwijzing(
            "die",
            "omstandigheden die de omgeving",
            VERWIJZING_DUIDELIJK,
            [{"quote": "omstandigheden", "reason": "betrekkelijke bijzin"}],
            reading="omstandigheden",
        ),
        _verwijzing(
            "die",
            "waardoor die gebeurtenis volledig",
            VERWIJZING_DUIDELIJK,
            [{"quote": "gebeurtenis", "reason": "aanwijzend bij herhaald naamwoord"}],
            reading="gebeurtenis",
        ),
    ],
    "question": None,
    "uncertainty": None,
}
ANTWOORD_ASTRA_FOUT = {
    "verdict": VERDICT_FAIL,
    "reason": "'het' kan naar 'Geheel' of 'gebeurtenis' verwijzen.",
    "references": [
        _verwijzing(
            "het",
            "waardoor het volledig kan worden begrepen",
            VERWIJZING_MEERDUIDIG,
            [
                {"quote": "Geheel", "reason": "onzijdig, onderwerp van de zin"},
                {"quote": "gebeurtenis", "reason": "dichtstbijzijnde naamwoord"},
            ],
            reading="twee plausibele lezingen",
        )
    ],
    "question": None,
    "uncertainty": None,
}
ANTWOORD_DEZE_VERTREKT = {
    "verdict": VERDICT_FAIL,
    "reason": "'deze' kan naar 'medewerker' of 'collega' verwijzen.",
    "references": [
        _verwijzing(
            "deze",
            "waarbij deze vertrekt",
            VERWIJZING_MEERDUIDIG,
            [
                {"quote": "medewerker", "reason": "handelende persoon"},
                {"quote": "collega", "reason": "dichtstbijzijnde persoon"},
            ],
        )
    ],
    "question": "Wie vertrekt?",
    "uncertainty": None,
}
ANTWOORD_HET_VOORTGEZET = {
    "verdict": VERDICT_FAIL,
    "reason": "'het' heeft in de definitie geen antecedent.",
    "references": [
        _verwijzing(
            "het",
            "waardoor het kan worden voortgezet",
            VERWIJZING_GEEN_ANTECEDENT,
            [],
            reading="geen naamwoordgroep of inhoud in de definitie komt in aanmerking",
        )
    ],
    "question": None,
    "uncertainty": None,
}
ANTWOORD_GEEN_WOORD = {
    "verdict": VERDICT_PASS,
    "reason": "De definitie bevat geen verwijzend woord.",
    "references": [],
    "question": None,
    "uncertainty": None,
}
ANTWOORD_VOEGWOORD = {
    "verdict": VERDICT_PASS,
    "reason": "'dat' is hier een voegwoord en verwijst niet.",
    "references": [
        _verwijzing(
            "dat",
            "verklaring dat een aanvraag",
            VERWIJZING_NIET_VERWIJZEND,
            [],
            reading="voegwoord",
        )
    ],
    "question": None,
    "uncertainty": None,
}
ANTWOORD_ONBESLIST = {
    "verdict": VERDICT_INSUFFICIENT,
    "reason": "Of 'deze' eenduidig vooruitwijst hangt af van de bedoelde betekenis.",
    "references": [
        _verwijzing(
            "deze",
            "waarbij deze vertrekt",
            VERWIJZING_ONBESLIST,
            [{"quote": "medewerker", "reason": "te onderzoeken kandidaat"}],
        )
    ],
    "question": "Is met 'deze' de medewerker bedoeld?",
    "uncertainty": "Betekenisgrond ontbreekt.",
}


# ---------------------------------------------------------------------------
# Vingerafdruk en toelichting
# ---------------------------------------------------------------------------


class TestVingerafdruk:
    def test_zelfde_invoer_zelfde_vingerafdruk(self):
        a = bereken_int03_vingerafdruk(TERM, ASTRA_GOED, CONTEXT, TOELICHTING)
        b = bereken_int03_vingerafdruk(TERM, ASTRA_GOED, dict(CONTEXT), TOELICHTING)
        assert a == b
        assert len(a) == 64

    @pytest.mark.parametrize(
        "wijziging",
        [
            {"begrip": "anderbegrip"},
            {"tekst": ASTRA_GOED + " Aanvulling."},
            {"contexten": {**CONTEXT, "juridische_context": ["Strafrecht"]}},
            {"toelichting": "Andere toelichting."},
        ],
        ids=["term", "tekst", "context", "toelichting"],
    )
    def test_elke_wijziging_maakt_een_andere_vingerafdruk(self, wijziging):
        basis = {
            "begrip": TERM,
            "tekst": ASTRA_GOED,
            "contexten": CONTEXT,
            "toelichting": TOELICHTING,
        }
        anders = {**basis, **wijziging}
        assert bereken_int03_vingerafdruk(**basis) != bereken_int03_vingerafdruk(
            **anders
        )

    def test_lege_toelichting_en_none_zijn_gelijk(self):
        assert bereken_int03_vingerafdruk(
            TERM, ASTRA_GOED, CONTEXT, None
        ) == bereken_int03_vingerafdruk(TERM, ASTRA_GOED, CONTEXT, "   ")


class TestToelichtingUitContext:
    def test_top_level_gaat_voor_record(self):
        ctx = {"toelichting": "Top.", "definition": {"toelichting": "Record."}}
        assert toelichting_uit_context(ctx) == "Top."

    def test_record_toelichting_als_top_level_ontbreekt(self):
        assert toelichting_uit_context({"definition": {"toelichting": " R "}}) == "R"

    def test_zonder_toelichting_none(self):
        assert toelichting_uit_context({}) is None
        assert toelichting_uit_context(None) is None


# ---------------------------------------------------------------------------
# Afgeleide bevinding (subtype) — door code, niet door het model
# ---------------------------------------------------------------------------


class TestAfgeleideBevinding:
    def test_zonder_verwijzingen_geen_verwijzend_woord(self):
        assert afgeleide_bevinding([]) == BEVINDING_GEEN_VERWIJZEND_WOORD

    def test_alleen_niet_verwijzend_gebruik_is_geen_verwijzend_woord(self):
        # K6(2): lidwoord, loos 'het' en voegwoord 'dat' verwijzen niet.
        assert (
            afgeleide_bevinding(ANTWOORD_VOEGWOORD["references"])
            == BEVINDING_GEEN_VERWIJZEND_WOORD
        )

    def test_duidelijk(self):
        assert afgeleide_bevinding(ANTWOORD_ASTRA_GOED["references"]) == (
            BEVINDING_DUIDELIJK
        )

    def test_meerduidig_gaat_voor_alles(self):
        refs = [*ANTWOORD_ASTRA_GOED["references"], *ANTWOORD_ASTRA_FOUT["references"]]
        assert afgeleide_bevinding(refs) == BEVINDING_MEERDUIDIG

    def test_geen_antecedent(self):
        assert afgeleide_bevinding(ANTWOORD_HET_VOORTGEZET["references"]) == (
            BEVINDING_GEEN_ANTECEDENT
        )

    def test_onbeslist(self):
        assert afgeleide_bevinding(ANTWOORD_ONBESLIST["references"]) == (
            BEVINDING_ONBESLIST
        )


# ---------------------------------------------------------------------------
# Gesloten antwoordstructuur
# ---------------------------------------------------------------------------


class TestStructuurfout:
    @pytest.mark.parametrize(
        "antwoord",
        [
            ANTWOORD_ASTRA_GOED,
            ANTWOORD_ASTRA_FOUT,
            ANTWOORD_DEZE_VERTREKT,
            ANTWOORD_HET_VOORTGEZET,
            ANTWOORD_GEEN_WOORD,
            ANTWOORD_VOEGWOORD,
            ANTWOORD_ONBESLIST,
        ],
        ids=[
            "astra-goed",
            "astra-fout",
            "deze-vertrekt",
            "het-voortgezet",
            "geen-woord",
            "voegwoord",
            "onbeslist",
        ],
    )
    def test_ontwikkelgevallen_zijn_structureel_geldig(self, antwoord):
        assert structuurfout_modeluitvoer(antwoord) is None

    def test_geen_object(self):
        assert structuurfout_modeluitvoer(["pass"]) == "geen object"

    def test_onbekend_veld(self):
        fout = structuurfout_modeluitvoer({**ANTWOORD_GEEN_WOORD, "score": 0.9})
        assert fout is not None and "onbekend veld" in fout
        # R2: de door het model gekozen veldnaam is modeltekst en blijft
        # buiten de melding.
        assert "score" not in fout

    @pytest.mark.parametrize(
        "antwoord",
        [
            {**ANTWOORD_GEEN_WOORD, MODELTEKST: 1},
            {**ANTWOORD_GEEN_WOORD, "verdict": MODELTEKST},
            {
                **ANTWOORD_ASTRA_GOED,
                "references": [
                    {**ANTWOORD_ASTRA_GOED["references"][0], "status": MODELTEKST}
                ],
            },
            {
                **ANTWOORD_ASTRA_GOED,
                "references": [
                    {**ANTWOORD_ASTRA_GOED["references"][0], MODELTEKST: "x"}
                ],
            },
        ],
        ids=["veldnaam", "verdict", "verwijzingsstatus", "verwijzingsveld"],
    )
    def test_structuurfout_meldingen_dragen_geen_modeltekst(self, antwoord):
        fout = structuurfout_modeluitvoer(antwoord)
        assert fout is not None
        assert MODELTEKST not in fout

    def test_ontbrekend_veld(self):
        zonder = {k: v for k, v in ANTWOORD_GEEN_WOORD.items() if k != "uncertainty"}
        fout = structuurfout_modeluitvoer(zonder)
        assert fout is not None and "ontbreekt" in fout and "uncertainty" in fout

    def test_onbekend_verdict(self):
        fout = structuurfout_modeluitvoer({**ANTWOORD_GEEN_WOORD, "verdict": "ok"})
        assert fout is not None and "verdict" in fout

    def test_lege_reden(self):
        fout = structuurfout_modeluitvoer({**ANTWOORD_GEEN_WOORD, "reason": " "})
        assert fout is not None and "reason" in fout

    def test_references_geen_lijst(self):
        fout = structuurfout_modeluitvoer({**ANTWOORD_GEEN_WOORD, "references": {}})
        assert fout is not None and "references" in fout

    def test_verwijzing_met_extra_of_ontbrekend_veld(self):
        ref = {**ANTWOORD_ASTRA_GOED["references"][0], "confidence": 0.8}
        fout = structuurfout_modeluitvoer({**ANTWOORD_ASTRA_GOED, "references": [ref]})
        assert fout is not None and "references[0]" in fout
        kaal = {
            k: v
            for k, v in ANTWOORD_ASTRA_GOED["references"][0].items()
            if k != "reading"
        }
        fout = structuurfout_modeluitvoer({**ANTWOORD_ASTRA_GOED, "references": [kaal]})
        assert fout is not None and "references[0]" in fout

    def test_onbekende_verwijzingsstatus(self):
        ref = {**ANTWOORD_ASTRA_GOED["references"][0], "status": "onduidelijk"}
        fout = structuurfout_modeluitvoer({**ANTWOORD_ASTRA_GOED, "references": [ref]})
        assert fout is not None and "status" in fout

    def test_kandidaat_zonder_quote_of_reason(self):
        ref = {
            **ANTWOORD_ASTRA_FOUT["references"][0],
            "candidates": [
                {"quote": "Geheel"},
                {"quote": "gebeurtenis", "reason": "x"},
            ],
        }
        fout = structuurfout_modeluitvoer({**ANTWOORD_ASTRA_FOUT, "references": [ref]})
        assert fout is not None and "candidates" in fout

    def test_meerduidig_vereist_minstens_twee_kandidaten(self):
        # "werkelijk plausibele kandidaten": één kandidaat is geen ambiguïteit.
        ref = {
            **ANTWOORD_ASTRA_FOUT["references"][0],
            "candidates": [{"quote": "Geheel", "reason": "x"}],
        }
        fout = structuurfout_modeluitvoer({**ANTWOORD_ASTRA_FOUT, "references": [ref]})
        assert fout is not None and "twee" in fout

    def test_geen_antecedent_vereist_lege_kandidatenlijst(self):
        ref = {
            **ANTWOORD_HET_VOORTGEZET["references"][0],
            "candidates": [{"quote": "voorziening", "reason": "x"}],
        }
        fout = structuurfout_modeluitvoer(
            {**ANTWOORD_HET_VOORTGEZET, "references": [ref]}
        )
        assert fout is not None and "no_antecedent" in fout

    def test_niet_verwijzend_vereist_lege_kandidatenlijst(self):
        ref = {
            **ANTWOORD_VOEGWOORD["references"][0],
            "candidates": [{"quote": "verklaring", "reason": "x"}],
        }
        fout = structuurfout_modeluitvoer({**ANTWOORD_VOEGWOORD, "references": [ref]})
        assert fout is not None and "non_referring" in fout

    @pytest.mark.parametrize(
        ("verdict", "references"),
        [
            (VERDICT_PASS, ANTWOORD_ASTRA_FOUT["references"]),
            (VERDICT_PASS, ANTWOORD_ONBESLIST["references"]),
            (VERDICT_FAIL, ANTWOORD_ASTRA_GOED["references"]),
            (VERDICT_FAIL, []),
            (VERDICT_INSUFFICIENT, ANTWOORD_ASTRA_GOED["references"]),
            (VERDICT_INSUFFICIENT, ANTWOORD_ASTRA_FOUT["references"]),
        ],
        ids=[
            "pass-met-meerduidig",
            "pass-met-onbeslist",
            "fail-met-alleen-duidelijk",
            "fail-zonder-verwijzing",
            "insufficient-met-duidelijk",
            "insufficient-met-meerduidig",
        ],
    )
    def test_verdict_moet_stroken_met_de_afgeleide_bevinding(self, verdict, references):
        antwoord = {
            "verdict": verdict,
            "reason": "x",
            "references": references,
            "question": "Vraag?" if verdict != VERDICT_PASS else None,
            "uncertainty": None,
        }
        fout = structuurfout_modeluitvoer(antwoord)
        assert fout is not None and "strookt niet" in fout

    def test_onvoldoende_informatie_vereist_precies_een_vraag(self):
        zonder = {**ANTWOORD_ONBESLIST, "question": None}
        assert "vraag" in (structuurfout_modeluitvoer(zonder) or "")
        twee = {**ANTWOORD_ONBESLIST, "question": "Wie? En wat?"}
        assert "vraag" in (structuurfout_modeluitvoer(twee) or "")
        geen_vraagteken = {**ANTWOORD_ONBESLIST, "question": "Onbekend"}
        assert "vraag" in (structuurfout_modeluitvoer(geen_vraagteken) or "")

    def test_pass_zonder_vraag_fail_mag_een_herstelvraag_dragen(self):
        met_vraag = {**ANTWOORD_ASTRA_GOED, "question": "Wie?"}
        assert "question" in (structuurfout_modeluitvoer(met_vraag) or "")
        # Een aantoonbare fout blijft fail als de herstelbedoeling onbekend is;
        # de herstelvraag staat ernaast (synthese-v2 §2, INT03-A-E07).
        assert structuurfout_modeluitvoer(ANTWOORD_DEZE_VERTREKT) is None
        twee = {**ANTWOORD_DEZE_VERTREKT, "question": "Wie? Waarom?"}
        assert "vraag" in (structuurfout_modeluitvoer(twee) or "")


# ---------------------------------------------------------------------------
# Citaatcontrole door code
# ---------------------------------------------------------------------------


class TestValideerOordeel:
    def test_geldig_oordeel_draagt_status_en_bevinding(self):
        oordeel, rejected = valideer_oordeel(ANTWOORD_ASTRA_FOUT, ASTRA_FOUT)
        assert rejected == []
        assert oordeel is not None
        assert oordeel.verdict == VERDICT_FAIL
        assert oordeel.status == STATUS_FAIL
        assert oordeel.finding == BEVINDING_MEERDUIDIG
        assert [r.word for r in oordeel.references] == ["het"]
        assert [c["quote"] for c in oordeel.references[0].candidates] == [
            "Geheel",
            "gebeurtenis",
        ]

    def test_geen_woord_geeft_pass_met_bevinding_geen_verwijzend_woord(self):
        oordeel, _ = valideer_oordeel(ANTWOORD_GEEN_WOORD, GEEN_WOORD)
        assert oordeel is not None
        assert oordeel.status == STATUS_PASS
        assert oordeel.finding == BEVINDING_GEEN_VERWIJZEND_WOORD

    def test_verzonnen_verwijzend_woord_wijst_het_hele_oordeel_af(self):
        ref = {**ANTWOORD_ASTRA_FOUT["references"][0], "word": "zij"}
        oordeel, rejected = valideer_oordeel(
            {**ANTWOORD_ASTRA_FOUT, "references": [ref]}, ASTRA_FOUT
        )
        assert oordeel is None
        assert any("verwijzend woord" in r["reason"] for r in rejected)

    def test_woord_moet_als_heel_woord_voorkomen(self):
        # 'het' zit als deelstring in 'Geheel', maar dat is geen voorkomen.
        antwoord = {
            "verdict": VERDICT_PASS,
            "reason": "x",
            "references": [
                _verwijzing(
                    "het", "Geheel van omstandigheden", VERWIJZING_DUIDELIJK, []
                )
            ],
            "question": None,
            "uncertainty": None,
        }
        oordeel, rejected = valideer_oordeel(
            antwoord, "Geheel van omstandigheden rond een zaak"
        )
        assert oordeel is None
        assert rejected

    def test_passage_moet_letterlijk_in_de_definitie_staan(self):
        ref = {**ANTWOORD_ASTRA_FOUT["references"][0], "passage": "waardoor het niet"}
        oordeel, rejected = valideer_oordeel(
            {**ANTWOORD_ASTRA_FOUT, "references": [ref]}, ASTRA_FOUT
        )
        assert oordeel is None
        assert any("passage" in r["reason"] for r in rejected)

    def test_woord_moet_in_zijn_passage_staan(self):
        ref = {**ANTWOORD_ASTRA_FOUT["references"][0], "passage": "Geheel van"}
        oordeel, rejected = valideer_oordeel(
            {**ANTWOORD_ASTRA_FOUT, "references": [ref]}, ASTRA_FOUT
        )
        assert oordeel is None
        assert rejected

    def test_verzonnen_kandidaat_wijst_het_hele_oordeel_af(self):
        ref = {
            **ANTWOORD_ASTRA_FOUT["references"][0],
            "candidates": [
                {"quote": "Geheel", "reason": "x"},
                {"quote": "dossier", "reason": "verzonnen"},
            ],
        }
        oordeel, rejected = valideer_oordeel(
            {**ANTWOORD_ASTRA_FOUT, "references": [ref]}, ASTRA_FOUT
        )
        assert oordeel is None
        assert any("kandidaat" in r["reason"] for r in rejected)

    def test_kandidaat_uit_de_term_of_toelichting_telt_niet(self):
        # K6(5): het losse lemma is geen antecedent; alleen de definitie is
        # bewijsplaats voor een kandidaat.
        ref = {
            **ANTWOORD_HET_VOORTGEZET["references"][0],
            "status": VERWIJZING_DUIDELIJK,
            "candidates": [{"quote": TERM, "reason": "het lemma"}],
        }
        antwoord = {**ANTWOORD_HET_VOORTGEZET, "verdict": VERDICT_PASS}
        oordeel, rejected = valideer_oordeel(
            {**antwoord, "references": [ref]}, HET_VOORTGEZET
        )
        assert oordeel is None
        assert rejected

    def test_structuurfout_is_ook_afwijzing(self):
        oordeel, rejected = valideer_oordeel({"verdict": VERDICT_PASS}, GEEN_WOORD)
        assert oordeel is None
        assert rejected[0]["reason"] == "structuurfout"


# ---------------------------------------------------------------------------
# Replay van een opgeslagen of zojuist verkregen beoordeling
# ---------------------------------------------------------------------------


def _doc(scenario: str = "pass", *, tekst: str = ASTRA_GOED, **over) -> dict:
    args = {
        "begrip": TERM,
        "tekst": tekst,
        "contexten": CONTEXT,
        "toelichting": TOELICHTING,
    }
    args.update({k: v for k, v in over.items() if k in args})
    return bouw_int03_beoordeling(
        args["begrip"],
        args["tekst"],
        args["contexten"],
        args["toelichting"],
        scenario=scenario,
        **{k: v for k, v in over.items() if k not in args},
    )


def _vingerafdruk(tekst: str = ASTRA_GOED) -> str:
    return bereken_int03_vingerafdruk(TERM, tekst, CONTEXT, TOELICHTING)


#: Corrupte beoordelingsdocumenten (reviewbevinding R4, v2): elk een functie van
#: een verder geldig, actueel gebonden document.
CORRUPTE_DOCUMENTEN = {
    "lijst": lambda _doc: [],
    "tekst": lambda _doc: "geen document",
    "onbekende-status": lambda doc: {**doc, "status": MODELTEKST},
    "status-ontbreekt": lambda doc: {k: v for k, v in doc.items() if k != "status"},
    "status-none": lambda doc: {**doc, "status": None},
}


class TestValideerBeoordeling:
    def test_zonder_beoordeling_expliciet_niet_uitgevoerd(self):
        oordeel, samenvatting = valideer_beoordeling(
            None, _vingerafdruk(), ASTRA_GOED, binding=BINDING
        )
        assert oordeel is None
        assert samenvatting["applied"] is False
        assert "niet uitgevoerd" in samenvatting["reason"]

    def test_geldige_beoordeling_wordt_toegepast(self):
        oordeel, samenvatting = valideer_beoordeling(
            _doc("pass"), _vingerafdruk(), ASTRA_GOED, binding=BINDING
        )
        assert oordeel is not None
        assert samenvatting["applied"] is True
        assert samenvatting["verdict"] == VERDICT_PASS
        assert samenvatting["finding"] == BEVINDING_DUIDELIJK
        assert samenvatting["model"] == MODEL

    def test_andere_tekst_is_historisch(self):
        oordeel, samenvatting = valideer_beoordeling(
            _doc("pass"),
            _vingerafdruk(ASTRA_GOED + " x"),
            ASTRA_GOED + " x",
            binding=BINDING,
        )
        assert oordeel is None
        assert samenvatting["historical"] is True
        assert "gewijzigd" in samenvatting["reason"]

    def test_zonder_actuele_binding_niet_actueel(self):
        oordeel, samenvatting = valideer_beoordeling(
            _doc("pass"), _vingerafdruk(), ASTRA_GOED, binding=None
        )
        assert oordeel is None
        assert "binding" in samenvatting["reason"]

    @pytest.mark.parametrize(
        "afwijking",
        [
            {"prompt_version": "int03-assess/other"},
            {"norm_sha256": "m" * 64},
            {"provider": "other"},
            {"model": "other-model"},
        ],
        ids=["prompt", "norm", "provider", "model"],
    )
    def test_andere_prompt_norm_provider_of_model_is_historisch(self, afwijking):
        binding = Beoordelingsbinding(**{**BINDING.als_dict(), **afwijking})
        oordeel, samenvatting = valideer_beoordeling(
            _doc("pass"), _vingerafdruk(), ASTRA_GOED, binding=binding
        )
        assert oordeel is None
        assert samenvatting["historical"] is True
        assert samenvatting["expected_binding"] == binding.als_dict()

    def test_andere_contractversie_telt_niet(self):
        doc = {**_doc("pass"), "contract_version": "int03/0"}
        oordeel, samenvatting = valideer_beoordeling(
            doc, _vingerafdruk(), ASTRA_GOED, binding=BINDING
        )
        assert oordeel is None
        assert "contractversie" in samenvatting["reason"]

    def test_technische_fout_en_niet_beschikbaar_zijn_geen_oordeel(self):
        fout, s1 = valideer_beoordeling(
            _doc("error"), _vingerafdruk(), ASTRA_GOED, binding=BINDING
        )
        assert fout is None and s1["status"] == "error"
        assert "technische fout" in s1["reason"]
        weg, s2 = valideer_beoordeling(
            _doc("unavailable"), _vingerafdruk(), ASTRA_GOED, binding=BINDING
        )
        assert weg is None and s2["status"] == "unavailable"

    def test_opgeslagen_oordeel_wordt_opnieuw_tegen_de_tekst_gelegd(self):
        # Caller-supplied positief oordeel met verzonnen citaat: telt niet.
        doc = _doc("pass")
        doc["judgment"]["references"] = [
            _verwijzing("zij", "zij vertrekt", VERWIJZING_DUIDELIJK, [])
        ]
        oordeel, samenvatting = valideer_beoordeling(
            doc, _vingerafdruk(), ASTRA_GOED, binding=BINDING
        )
        assert oordeel is None
        assert "bruikbaar" in samenvatting["reason"]
        assert samenvatting["rejected"] >= 1
        # R4: technisch ongeldig, geen ontbrekende of historische beoordeling.
        assert samenvatting["invalid"] is True
        assert samenvatting["historical"] is False
        # R2: het afgewezen citaat staat niet in de reden.
        assert "zij vertrekt" not in samenvatting["reason"]

    def test_strijdige_opgeslagen_status_telt_niet(self):
        doc = _doc("pass")
        doc["judgment"]["status"] = STATUS_FAIL
        oordeel, samenvatting = valideer_beoordeling(
            doc, _vingerafdruk(), ASTRA_GOED, binding=BINDING
        )
        assert oordeel is None
        assert "strookt niet" in samenvatting["reason"]
        assert samenvatting["invalid"] is True

    def test_ontbrekend_niet_beschikbaar_en_historisch_zijn_niet_ongeldig(self):
        for assessment, tekst in (
            (None, ASTRA_GOED),
            (_doc("unavailable"), ASTRA_GOED),
            (_doc("error"), ASTRA_GOED),
            (_doc("pass"), ASTRA_GOED + " x"),
        ):
            _, samenvatting = valideer_beoordeling(
                assessment, _vingerafdruk(tekst), tekst, binding=BINDING
            )
            assert samenvatting["invalid"] is False

    @pytest.mark.parametrize(
        "corrupt",
        list(CORRUPTE_DOCUMENTEN.values()),
        ids=list(CORRUPTE_DOCUMENTEN),
    )
    def test_documentcorruptie_is_ongeldig_niet_ontbrekend(self, corrupt):
        # Reviewbevinding R4 (v2): een aangeleverd niet-object of een document
        # zonder geldige status is corrupt — geen ontbrekende beoordeling.
        oordeel, samenvatting = valideer_beoordeling(
            corrupt(_doc("pass")), _vingerafdruk(), ASTRA_GOED, binding=BINDING
        )
        assert oordeel is None
        assert samenvatting["invalid"] is True
        assert samenvatting["historical"] is False
        assert samenvatting["applied"] is False
        # Geen documentwaarde in de reden of de samenvatting (R2).
        assert MODELTEKST not in (samenvatting["reason"] or "")
        assert samenvatting["status"] is None


# ---------------------------------------------------------------------------
# Samenstelling: de zichtbare INT-03-uitkomst
# ---------------------------------------------------------------------------


def _beoordeel(assessment, *, tekst: str = ASTRA_GOED, binding=BINDING):
    return beoordeel_verwijzingen(
        TERM, tekst, CONTEXT, TOELICHTING, assessment=assessment, binding=binding
    )


class TestBeoordeelVerwijzingen:
    def test_zonder_beoordeling_open_nooit_pass(self):
        uitkomst = _beoordeel(None)
        (deel,) = uitkomst.parts
        assert uitkomst.status == STATUS_OPEN
        assert deel.id == ONDERDEEL_VERWIJZING
        assert "niet beoordeeld" in deel.reason
        assert uitkomst.als_dict()["score"] is None
        assert uitkomst.als_dict()["contract_version"] == CONTRACTVERSIE

    def test_pass_draagt_model_en_verwijzingen(self):
        doc = _doc("pass", verwijzingen=ANTWOORD_ASTRA_GOED["references"])
        uitkomst = _beoordeel(doc)
        (deel,) = uitkomst.parts
        assert uitkomst.status == STATUS_PASS
        assert deel.field == BASIS_ASSESSMENT
        assert MODEL in deel.reason
        assert "'die'" in deel.reason and "omstandigheden" in deel.reason
        assert deel.evidence == "omstandigheden die de omgeving"
        assert uitkomst.review["assessment"]["finding"] == BEVINDING_DUIDELIJK

    def test_geen_verwijzend_woord_is_pass_met_exacte_motivering(self):
        # K7: pas ná de inhoudelijke controle, met exact deze motivering en
        # een herkenbare bevinding voor de UI.
        uitkomst = _beoordeel(_doc("no_word", tekst=GEEN_WOORD), tekst=GEEN_WOORD)
        (deel,) = uitkomst.parts
        assert uitkomst.status == STATUS_PASS
        assert deel.reason == MOTIVERING_GEEN_VERWIJZEND_WOORD
        assert MOTIVERING_GEEN_VERWIJZEND_WOORD == (
            "niet van toepassing: de definitie bevat geen verwijzend voornaamwoord"
        )
        assert uitkomst.review["assessment"]["finding"] == (
            BEVINDING_GEEN_VERWIJZEND_WOORD
        )
        assert uitkomst.als_dict()["review"]["assessment"]["finding"] == (
            BEVINDING_GEEN_VERWIJZEND_WOORD
        )

    def test_alleen_voegwoord_is_ook_geen_verwijzend_woord(self):
        doc = _doc(
            "pass", tekst=VOEGWOORD_DAT, verwijzingen=ANTWOORD_VOEGWOORD["references"]
        )
        uitkomst = _beoordeel(doc, tekst=VOEGWOORD_DAT)
        assert uitkomst.status == STATUS_PASS
        assert uitkomst.parts[0].reason == MOTIVERING_GEEN_VERWIJZEND_WOORD

    def test_fail_noemt_woord_kandidaten_en_herstelvraag(self):
        doc = _doc(
            "fail",
            tekst=DEZE_VERTREKT,
            verwijzingen=ANTWOORD_DEZE_VERTREKT["references"],
        )
        doc["judgment"]["question"] = "Wie vertrekt?"
        uitkomst = _beoordeel(doc, tekst=DEZE_VERTREKT)
        (deel,) = uitkomst.parts
        assert uitkomst.status == STATUS_FAIL
        assert "'deze'" in deel.reason
        assert "medewerker" in deel.reason and "collega" in deel.reason
        assert "Wie vertrekt?" in deel.reason
        assert "herhaal" in deel.action.lower() or "herformuleer" in deel.action.lower()
        assert "niet automatisch" in deel.action.lower() or "op verzoek" in (
            deel.action.lower()
        )
        assert uitkomst.review["assessment"]["finding"] == BEVINDING_MEERDUIDIG

    def test_fail_zonder_antecedent_heeft_lege_kandidatenlijst_met_motivering(self):
        doc = _doc(
            "no_antecedent",
            tekst=HET_VOORTGEZET,
            verwijzingen=ANTWOORD_HET_VOORTGEZET["references"],
        )
        uitkomst = _beoordeel(doc, tekst=HET_VOORTGEZET)
        (deel,) = uitkomst.parts
        assert uitkomst.status == STATUS_FAIL
        assert "'het'" in deel.reason
        assert "geen antecedent" in deel.reason.lower()
        assert uitkomst.review["assessment"]["finding"] == BEVINDING_GEEN_ANTECEDENT
        referenties = uitkomst.als_dict()["assessment"]["judgment"]["references"]
        assert referenties[0]["candidates"] == []

    def test_onvoldoende_informatie_is_open_met_precies_die_vraag(self):
        doc = _doc(
            "insufficient",
            tekst=DEZE_VERTREKT,
            verwijzingen=ANTWOORD_ONBESLIST["references"],
            vraag="Is met 'deze' de medewerker bedoeld?",
        )
        uitkomst = _beoordeel(doc, tekst=DEZE_VERTREKT)
        (deel,) = uitkomst.parts
        assert uitkomst.status == STATUS_OPEN
        assert "Is met 'deze' de medewerker bedoeld?" in deel.reason
        assert uitkomst.review["assessment"]["question"] == (
            "Is met 'deze' de medewerker bedoeld?"
        )
        assert uitkomst.review["assessment"]["finding"] == BEVINDING_ONBESLIST

    def test_technische_fout_is_error_zonder_oordeel(self):
        uitkomst = _beoordeel(_doc("error"))
        assert uitkomst.status == STATUS_ERROR
        assert "geen inhoudelijk oordeel" in uitkomst.parts[0].reason

    def test_stale_beoordeling_is_open_met_reden(self):
        uitkomst = _beoordeel(_doc("pass"), tekst=ASTRA_GOED + " Extra.")
        assert uitkomst.status == STATUS_OPEN
        assert "historisch" in uitkomst.parts[0].reason

    def test_structureel_ongeldige_beoordeling_is_error_niet_open(self):
        # Reproductie van reviewbevinding R4: `judgment.verdict` gewijzigd in
        # een verder geldig, actueel gebonden document.
        doc = _doc("pass")
        doc["judgment"]["verdict"] = MODELTEKST
        uitkomst = _beoordeel(doc)
        (deel,) = uitkomst.parts
        assert uitkomst.status == STATUS_ERROR
        assert "geen inhoudelijk oordeel" in deel.reason
        assert MODELTEKST not in deel.reason
        assert uitkomst.review["assessment"]["invalid"] is True
        assert uitkomst.review["assessment"]["question"] is None

    def test_ongeldig_citaat_bij_replay_is_error_zonder_citaat_in_de_reden(self):
        doc = _doc("pass")
        doc["judgment"]["references"] = [
            _verwijzing("die", f"{MODELTEKST} verzonnen passage", VERWIJZING_DUIDELIJK)
        ]
        uitkomst = _beoordeel(doc)
        assert uitkomst.status == STATUS_ERROR
        assert MODELTEKST not in uitkomst.parts[0].reason
        assert uitkomst.review["assessment"]["rejected"] >= 1

    def test_ontbrekend_niet_beschikbaar_en_historisch_blijven_open(self):
        assert _beoordeel(None).status == STATUS_OPEN
        assert _beoordeel(_doc("unavailable")).status == STATUS_OPEN
        assert _beoordeel(_doc("pass"), tekst=ASTRA_GOED + " x").status == STATUS_OPEN
        fout = _beoordeel(_doc("error"))
        assert fout.status == STATUS_ERROR
        assert fout.review["assessment"]["invalid"] is False

    @pytest.mark.parametrize(
        "corrupt",
        list(CORRUPTE_DOCUMENTEN.values()),
        ids=list(CORRUPTE_DOCUMENTEN),
    )
    def test_documentcorruptie_is_error_zonder_vraag(self, corrupt):
        uitkomst = _beoordeel(corrupt(_doc("pass")))
        (deel,) = uitkomst.parts
        assert uitkomst.status == STATUS_ERROR
        assert "geen inhoudelijk oordeel" in deel.reason
        assert MODELTEKST not in deel.reason
        assert uitkomst.review["assessment"]["invalid"] is True
        assert uitkomst.review["assessment"]["question"] is None

    def test_uitkomst_draagt_het_volledige_document(self):
        doc = _doc("pass")
        detail = _beoordeel(doc).als_dict()
        assert detail["assessment"] == doc
        assert detail["assessment"] is not doc
        assert detail["fingerprint"] == doc["fingerprint"]
        assert detail["parts"][0]["id"] == ONDERDEEL_VERWIJZING

    def test_niet_beschikbaar_documenten_zijn_store_ready(self):
        weg = beoordeling_niet_beschikbaar("f" * 64, "geen dienst")
        assert weg["status"] == "unavailable" and weg["contract_version"] == (
            CONTRACTVERSIE
        )
        fout = beoordeling_technische_fout("f" * 64, "timeout", "te laat")
        assert fout["status"] == "error"
        assert fout["error"] == {"type": "timeout", "message": "te laat"}
        assert fout["judgment"] is None
