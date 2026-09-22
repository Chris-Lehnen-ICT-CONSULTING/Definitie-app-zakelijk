"""ESS-03 (DEF-766): het telbaarheidscontract — vingerafdruk, bewijstoets, replay.

Zuiver domein: geen AI-aanroep, geen database, geen Streamlit. De
gestructureerde beoordeling in deze tests is synthetisch (alsof een
gevalideerde dienst haar leverde); de code toetst uitsluitend wat code kán
toetsen: binding, citaatbestaan, gesloten statussen en samenstelling — geen
interpretatie van telbaarheid.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from domain.ess03.contract import (
    BASIS_ASSESSMENT,
    CONTRACTVERSIE,
    ONDERDEEL_TELBAARHEID,
    STATUS_ERROR,
    STATUS_FAIL,
    STATUS_NOT_APPLICABLE,
    STATUS_OPEN,
    STATUS_PASS,
    VERDICT_FAIL,
    VERDICT_INSUFFICIENT,
    VERDICT_NOT_APPLICABLE,
    VERDICT_PASS,
    VERDICTS,
    Beoordelingsbinding,
    Intentie,
    beoordeel_telbaarheid,
    beoordeling_niet_beschikbaar,
    beoordeling_technische_fout,
    beoordelingsmateriaal,
    bereken_ess03_vingerafdruk,
    materiaalhashes,
    structuurfout_modeluitvoer,
    valideer_beoordeling,
    valideer_oordeel,
)
from domain.sources.normalisatie import canoniseer_bronnen

pytestmark = [pytest.mark.unit]

#: De actuele beoordelingsbinding waaraan de synthetische documenten voldoen
#: (correctieronde 1, R1): zonder binding is geen beoordeling actueel.
BINDING = Beoordelingsbinding(
    prompt_version="ess03-assess/1",
    norm_sha256="a" * 64,
    provider="anthropic",
    model="synthetisch-model",
)

BEGRIP = "boekexemplaar"
TEKST = (
    "Boekexemplaar dat uitsluitend door zijn ISBN van andere fysieke exemplaren "
    "wordt onderscheiden."
)
CONTEXT = {
    "organisatorische_context": ["Synthetische Bibliotheek"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
PASSAGE = (
    "Een ISBN identificeert een uitgave (titel, editie, verschijningsvorm). "
    "Meerdere fysieke exemplaren van dezelfde uitgave dragen hetzelfde ISBN."
)
BRON = {
    "provider": "documents",
    "doc_id": "reglement-1",
    "title": "Synthetisch bibliotheekreglement",
    "citation_label": "art. 2",
    "url": "https://intern.example/reglement#art-2",
    "snippet": PASSAGE,
    "used_in_prompt": True,
}
INTENTIE = Intentie(
    toelichting="Bedoeld: het afzonderlijke fysieke exemplaar in de collectie.",
    categorie="type",
    betekenisverduidelijking=None,
    verduidelijking=None,
)


def _bron_id() -> str:
    return canoniseer_bronnen([BRON])[0].source_id


def _fingerprint(**over) -> str:
    args = {
        "begrip": BEGRIP,
        "tekst": TEKST,
        "contexten": CONTEXT,
        "bronnen": [BRON],
        "intentie": INTENTIE,
    }
    args.update(over)
    return bereken_ess03_vingerafdruk(
        args["begrip"],
        args["tekst"],
        args["contexten"],
        args["bronnen"],
        intentie=args["intentie"],
    )


def _oordeel(**over) -> dict:
    """Een welgevormde modeluitvoer (verdict fail, bewijs uit kandidaat en bron)."""
    basis = {
        "verdict": VERDICT_FAIL,
        "applicability": "applicable",
        "unit": "het afzonderlijke fysieke exemplaar",
        "reason": (
            "Het enige gestelde onderscheidingsmiddel (ISBN) onderscheidt volgens de "
            "aangeleverde bron geen fysieke exemplaren."
        ),
        "evidence": [
            {"location": "definition", "quote": "uitsluitend door zijn ISBN"},
            {
                "location": f"source:{_bron_id()}",
                "quote": "dragen hetzelfde ISBN",
            },
        ],
        "missing_information": None,
        "question": None,
        "uncertainty": None,
    }
    basis.update(over)
    return basis


def _beoordeling(oordeel: dict | None = None, **over) -> dict:
    """Een store-ready beoordeling zoals de dienst haar oplevert (status assessed)."""
    materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)
    gevalideerd, rejected = valideer_oordeel(oordeel or _oordeel(), materiaal)
    document = {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": "ess03-assess/1",
        "norm_sha256": "a" * 64,
        "fingerprint": _fingerprint(),
        "status": "assessed",
        "error": None,
        "assessed_at": "2026-09-21T09:00:00+00:00",
        "attribution": {
            "provider": "anthropic",
            "model": "synthetisch-model",
            "task_type": "validation",
            "cached": False,
            "tokens_used": 123,
        },
        "input": {
            "intentie": INTENTIE.als_dict(),
            "materiaal": materiaalhashes(materiaal),
        },
        "judgment": gevalideerd.als_dict() if gevalideerd is not None else None,
        "rejected": rejected,
        "raw_response_sha256": "b" * 64,
    }
    document.update(over)
    return document


# --- vingerafdruk --------------------------------------------------------------


class TestVingerafdruk:
    def test_stabiel_en_hexadecimaal(self):
        assert _fingerprint() == _fingerprint()
        assert len(_fingerprint()) == 64
        int(_fingerprint(), 16)

    @pytest.mark.parametrize(
        "wijziging",
        [
            {"begrip": "boek"},
            {"tekst": TEKST + " "},
            {"contexten": {**CONTEXT, "juridische_context": ["auteursrecht"]}},
            {"bronnen": []},
            {"bronnen": [{**BRON, "snippet": PASSAGE + " Extra zin."}]},
            {"intentie": Intentie(toelichting="Bedoeld: de uitgave.")},
            {"intentie": Intentie(verduidelijking="Bedoeld zijn fysieke exemplaren.")},
            {"intentie": Intentie(categorie="proces")},
        ],
    )
    def test_elke_relevante_wijziging_verandert_de_vingerafdruk(self, wijziging):
        assert _fingerprint(**wijziging) != _fingerprint()

    def test_contextvolgorde_en_whitespace_zijn_geen_wijziging(self):
        context = {
            "organisatorische_context": ["  Synthetische Bibliotheek "],
            "juridische_context": None,
            "wettelijke_basis": [],
        }
        assert _fingerprint(contexten=context) == _fingerprint()

    def test_versie_zit_in_de_vingerafdruk(self):
        assert CONTRACTVERSIE == "ess03/1"


# --- materiaal en bewijstoets -----------------------------------------------------


class TestMateriaalEnBewijs:
    def test_materiaal_kent_alle_vindplaatsen(self):
        materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)
        assert materiaal["definition"] == TEKST
        assert materiaal["term"] == BEGRIP
        assert materiaal["toelichting"] == INTENTIE.toelichting
        assert "Synthetische Bibliotheek" in materiaal["context"]
        assert materiaal[f"source:{_bron_id()}"] == PASSAGE
        # Geen verduidelijking → geen vindplaats (niets verzonnen).
        assert "verduidelijking" not in materiaal

    def test_verzonnen_bewijs_naast_echt_bewijs_maakt_het_oordeel_onbruikbaar(self):
        # Correctieronde 1 (R3): één niet-verifieerbaar item volstaat; het
        # echte citaat 'redt' de reden niet. Elk item wordt benoemd.
        materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)
        oordeel = _oordeel(
            evidence=[
                {"location": "definition", "quote": "uitsluitend door zijn ISBN"},
                {"location": "definition", "quote": "met een uniek nummer"},
                {"location": "source:onbekend", "quote": "hetzelfde ISBN"},
                {"location": "toelichting", "quote": ""},
            ]
        )
        gevalideerd, rejected = valideer_oordeel(oordeel, materiaal)
        assert gevalideerd is None
        redenen = {r["reason"] for r in rejected}
        assert redenen == {
            "citaat niet in materiaal",
            "onbekende vindplaats",
            "leeg citaat",
        }
        # Een bewijsitem dat geen object is, is een structuurfout (R2).
        gevalideerd, rejected = valideer_oordeel(
            _oordeel(evidence=["geen object"]), materiaal
        )
        assert gevalideerd is None
        assert rejected[0]["reason"] == "structuurfout"

    def test_pass_zonder_geverifieerd_bewijs_is_onbruikbaar(self):
        materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)
        oordeel = _oordeel(
            verdict=VERDICT_PASS,
            evidence=[{"location": "definition", "quote": "niet in de tekst"}],
        )
        gevalideerd, rejected = valideer_oordeel(oordeel, materiaal)
        assert gevalideerd is None
        assert [r["reason"] for r in rejected] == ["citaat niet in materiaal"]
        # Een afgerond oordeel zónder enig bewijs is een structuurfout.
        gevalideerd, rejected = valideer_oordeel(
            _oordeel(verdict=VERDICT_PASS, evidence=[]), materiaal
        )
        assert gevalideerd is None
        assert "zonder bewijs" in rejected[0]["detail"]

    def test_fail_met_bewijs_behoudt_bevinding_en_onzekerheid(self):
        materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)
        oordeel = _oordeel(uncertainty="Of de collectie ook e-books omvat is onbekend.")
        gevalideerd, _ = valideer_oordeel(oordeel, materiaal)
        assert gevalideerd.status == STATUS_FAIL
        assert (
            gevalideerd.uncertainty == "Of de collectie ook e-books omvat is onbekend."
        )

    def test_niet_van_toepassing_met_grond(self):
        materiaal = beoordelingsmateriaal(
            "water",
            "Vloeistof bestaande uit H2O.",
            CONTEXT,
            [],
            Intentie(toelichting="Bedoeld: de stof, niet een monster."),
        )
        oordeel = _oordeel(
            verdict=VERDICT_NOT_APPLICABLE,
            applicability="not_applicable",
            unit=None,
            reason="Stoflezing zonder gekozen telbare eenheid.",
            evidence=[
                {"location": "toelichting", "quote": "de stof, niet een monster"}
            ],
        )
        gevalideerd, rejected = valideer_oordeel(oordeel, materiaal)
        assert gevalideerd.status == STATUS_NOT_APPLICABLE
        assert rejected == []

    def test_onvoldoende_informatie_vereist_precies_een_vraag(self):
        materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [], None)
        goed = _oordeel(
            verdict=VERDICT_INSUFFICIENT,
            applicability="undetermined",
            evidence=[],
            missing_information="Geen registerafspraak aangeleverd.",
            question="Binnen welk register en welke populatie geldt het nummer?",
        )
        gevalideerd, rejected = valideer_oordeel(goed, materiaal)
        assert gevalideerd.status == STATUS_OPEN
        assert gevalideerd.question == (
            "Binnen welk register en welke populatie geldt het nummer?"
        )
        assert rejected == []
        # Zonder vraag is het antwoord structureel onbruikbaar (fail-closed).
        zonder = dict(goed, question=None)
        assert structuurfout_modeluitvoer(zonder) is not None
        assert "question" in structuurfout_modeluitvoer(zonder)

    def test_vraag_bij_afgerond_oordeel_is_een_structuurfout(self):
        # Correctieronde 1 (R2): niet stil weglaten, maar afwijzen.
        fout = structuurfout_modeluitvoer(_oordeel(question="Is dit een e-book?"))
        assert fout is not None and "question" in fout

    def test_tegenstrijdige_toepasselijkheid_is_een_structuurfout(self):
        fout = structuurfout_modeluitvoer(_oordeel(applicability="not_applicable"))
        assert fout is not None and "applicability" in fout


class TestStructuurfout:
    def test_welgevormd_is_geen_structuurfout(self):
        assert structuurfout_modeluitvoer(_oordeel()) is None

    @pytest.mark.parametrize(
        ("kapot", "fragment"),
        [
            ("geen object", "geen object"),
            ({**_oordeel(), "verdict": "maybe"}, "verdict"),
            ({k: v for k, v in _oordeel().items() if k != "verdict"}, "verdict"),
            ({**_oordeel(), "reason": "   "}, "reason"),
            ({**_oordeel(), "evidence": "geen lijst"}, "evidence"),
            ({**_oordeel(), "applicability": "misschien"}, "applicability"),
            (
                {
                    **_oordeel(),
                    "verdict": VERDICT_INSUFFICIENT,
                    "applicability": "undetermined",
                    "question": "   ",
                },
                "question",
            ),
        ],
    )
    def test_structuurfouten_worden_benoemd(self, kapot, fragment):
        fout = structuurfout_modeluitvoer(kapot)
        assert fout is not None
        assert fragment in fout

    def test_verdictset_is_gesloten(self):
        assert set(VERDICTS) == {
            VERDICT_PASS,
            VERDICT_FAIL,
            VERDICT_NOT_APPLICABLE,
            VERDICT_INSUFFICIENT,
        }


# --- replay: binding, technische status, samenstelling -----------------------


def _replay(assessment, **over):
    args = {
        "begrip": BEGRIP,
        "tekst": TEKST,
        "contexten": CONTEXT,
        "bronnen": [BRON],
        "intentie": INTENTIE,
    }
    args.update(over)
    return beoordeel_telbaarheid(
        args["begrip"],
        args["tekst"],
        args["contexten"],
        args["bronnen"],
        intentie=args["intentie"],
        assessment=assessment,
        binding=BINDING,
    )


class TestReplay:
    def test_zonder_beoordeling_is_de_regel_open_en_benoemt_dat(self):
        uitkomst = _replay(None)
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.fingerprint == _fingerprint()
        [deel] = uitkomst.parts
        assert deel.id == ONDERDEEL_TELBAARHEID
        assert deel.status == STATUS_OPEN
        assert "niet uitgevoerd" in deel.reason.lower()
        assert uitkomst.review["assessment"]["applied"] is False

    def test_niet_beschikbaar_is_expliciet_geen_eindantwoord(self):
        doc = beoordeling_niet_beschikbaar(_fingerprint(), "geen dienst geïnjecteerd")
        assert doc["status"] == "unavailable"
        uitkomst = _replay(doc)
        assert uitkomst.status == STATUS_OPEN
        [deel] = uitkomst.parts
        assert "geen dienst geïnjecteerd" in deel.reason
        assert deel.field == BASIS_ASSESSMENT

    def test_technische_fout_is_error_nooit_pass_of_fail(self):
        doc = beoordeling_technische_fout(
            _fingerprint(),
            "timeout",
            "TimeoutError: 60s",
            prompt_version="ess03-assess/1",
        )
        uitkomst = _replay(doc)
        assert uitkomst.status == STATUS_ERROR
        [deel] = uitkomst.parts
        assert deel.status == STATUS_ERROR
        assert "timeout" in deel.reason
        detail = uitkomst.als_dict()
        assert detail["status"] == "error"
        assert detail["score"] is None

    def test_fail_met_bewijs_wordt_fail_met_bewijsplaats(self):
        uitkomst = _replay(_beoordeling())
        assert uitkomst.status == STATUS_FAIL
        [deel] = uitkomst.parts
        assert deel.status == STATUS_FAIL
        assert deel.evidence == "uitsluitend door zijn ISBN"
        assert deel.field == BASIS_ASSESSMENT
        assert "synthetisch-model" in deel.reason
        assert uitkomst.review["assessment"]["applied"] is True
        assert uitkomst.review["assessment"]["verdict"] == VERDICT_FAIL

    def test_pass_wordt_pass_zonder_cijfer(self):
        oordeel = _oordeel(
            verdict=VERDICT_PASS,
            reason="De kern draagt een natuurlijke grens.",
            evidence=[{"location": "definition", "quote": "fysieke exemplaren"}],
        )
        uitkomst = _replay(_beoordeling(oordeel))
        assert uitkomst.status == STATUS_PASS
        assert uitkomst.als_dict()["score"] is None

    def test_niet_van_toepassing_is_een_eigen_status_geen_pass(self):
        oordeel = _oordeel(
            verdict=VERDICT_NOT_APPLICABLE,
            applicability="not_applicable",
            reason="Stoflezing zonder gekozen eenheid.",
            evidence=[{"location": "term", "quote": BEGRIP}],
        )
        uitkomst = _replay(_beoordeling(oordeel))
        assert uitkomst.status == STATUS_NOT_APPLICABLE
        assert uitkomst.status != STATUS_PASS
        assert uitkomst.als_dict()["status"] == "not_applicable"

    def test_onvoldoende_informatie_draagt_de_vraag(self):
        oordeel = _oordeel(
            verdict=VERDICT_INSUFFICIENT,
            applicability="undetermined",
            evidence=[],
            missing_information="Geen registerafspraak.",
            question="Welk register geldt?",
        )
        uitkomst = _replay(_beoordeling(oordeel))
        assert uitkomst.status == STATUS_OPEN
        [deel] = uitkomst.parts
        assert "Welk register geldt?" in deel.reason
        assert uitkomst.review["assessment"]["question"] == "Welk register geldt?"
        assert uitkomst.review["assessment"]["verdict"] == VERDICT_INSUFFICIENT

    @pytest.mark.parametrize(
        ("wijziging", "fragment"),
        [
            ({"tekst": TEKST + " Extra."}, "gewijzigd"),
            (
                {"intentie": Intentie(verduidelijking="Fysieke exemplaren.")},
                "gewijzigd",
            ),
            ({"bronnen": []}, "gewijzigd"),
        ],
    )
    def test_stale_beoordeling_wordt_niet_toegepast_en_benoemd(
        self, wijziging, fragment
    ):
        uitkomst = _replay(_beoordeling(), **wijziging)
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["assessment"]["applied"] is False
        assert fragment in uitkomst.review["assessment"]["reason"]
        [deel] = uitkomst.parts
        assert deel.status == STATUS_OPEN

    def test_andere_contractversie_of_onbekend_model_telt_niet(self):
        oud = _beoordeling(contract_version="ess03/0")
        assert _replay(oud).review["assessment"]["applied"] is False
        zonder_model = _beoordeling()
        zonder_model["attribution"]["model"] = None
        samenvatting = _replay(zonder_model).review["assessment"]
        assert samenvatting["applied"] is False
        assert "herkomst" in samenvatting["reason"]

    def test_caller_supplied_positief_oordeel_zonder_bewijs_telt_niet(self):
        doc = _beoordeling()
        doc["judgment"] = {
            "verdict": VERDICT_PASS,
            "status": STATUS_PASS,
            "applicability": "applicable",
            "unit": None,
            "reason": "Alles prima.",
            "evidence": [],
            "missing_information": None,
            "question": None,
            "uncertainty": None,
        }
        uitkomst = _replay(doc)
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["assessment"]["applied"] is False
        [deel] = uitkomst.parts
        assert "zonder bewijs" in deel.reason

    def test_replay_hercontroleert_citaten_tegen_actueel_materiaal(self):
        doc = _beoordeling()
        doc["judgment"]["evidence"] = [
            {"location": "definition", "quote": "verzonnen citaat"}
        ]
        uitkomst = _replay(doc)
        assert uitkomst.status == STATUS_OPEN

    def test_als_dict_is_rule_result_vorm(self):
        detail = _replay(_beoordeling()).als_dict()
        assert set(detail) == {
            "status",
            "score",
            "contract_version",
            "fingerprint",
            "parts",
            "review",
        }
        assert detail["contract_version"] == CONTRACTVERSIE
        [deel] = detail["parts"]
        assert set(deel) == {
            "id",
            "status",
            "evidence",
            "context_value",
            "field",
            "position",
            "reason",
            "action",
        }

    def test_valideer_beoordeling_geeft_samenvatting_met_attributie(self):
        materiaal = beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)
        gevalideerd, samenvatting = valideer_beoordeling(
            _beoordeling(), _fingerprint(), materiaal, binding=BINDING
        )
        assert gevalideerd is not None
        assert samenvatting["applied"] is True
        assert samenvatting["model"] == "synthetisch-model"
        assert samenvatting["provider"] == "anthropic"
        assert samenvatting["prompt_version"] == "ess03-assess/1"
        assert samenvatting["norm_sha256"] == "a" * 64

    def test_replay_crasht_nooit_op_onleesbare_beoordeling(self):
        uitkomst = _replay(
            {"status": "assessed", "judgment": "onzin", "fingerprint": 3}
        )
        assert uitkomst.status == STATUS_OPEN
        uitkomst2 = _replay(deepcopy(["lijst"]))
        assert uitkomst2.status == STATUS_OPEN
