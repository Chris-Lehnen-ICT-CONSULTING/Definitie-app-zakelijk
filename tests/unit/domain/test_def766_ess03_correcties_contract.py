"""DEF-766 correctieronde 1 — contractcorrecties R1, R2 en R3 (zuiver domein).

R1: de replay bindt niet alleen aan contractversie en kandidaatvingerafdruk,
maar aan de volledige actuele beoordelingsbinding (promptversie, normhash,
provider/model) én aan het werkelijk verzonden materiaal (hash per vindplaats).
Elke afwijking is zichtbaar niet-actueel; zonder bekende actuele binding is
een opgeslagen beoordeling nooit actueel.

R2: het antwoord is gesloten — één JSON-object zonder omliggende tekst, een
gesloten veldenset met typen, precies één gerichte vraag (alleen bij
`insufficient_information`), toepasselijkheid die met het verdict strookt.

R3: bewijs dat niet verifieerbaar is maakt het oordeel onbruikbaar (geen
'pass' op een reden waarvan een deel van de grond is afgewezen); een afgerond
verdict zonder bewijs is een structuurfout.
"""

from __future__ import annotations

import hashlib

import pytest

from domain.ess03.contract import (
    STATUS_FAIL,
    STATUS_OPEN,
    VERDICT_FAIL,
    VERDICT_INSUFFICIENT,
    VERDICT_NOT_APPLICABLE,
    VERDICT_PASS,
    Beoordelingsbinding,
    Intentie,
    beoordeel_telbaarheid,
    beoordelingsmateriaal,
    bereken_ess03_vingerafdruk,
    materiaalhashes,
    structuurfout_modeluitvoer,
    valideer_beoordeling,
    valideer_oordeel,
)
from domain.sources.normalisatie import canoniseer_bronnen
from services.validation.ess03_assessment_service import parse_modeluitvoer

pytestmark = [pytest.mark.unit]

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
    "snippet": PASSAGE,
}
INTENTIE = Intentie(toelichting="Bedoeld: het afzonderlijke fysieke exemplaar.")
BRON_ID = canoniseer_bronnen([BRON])[0].source_id
BINDING = Beoordelingsbinding(
    prompt_version="ess03-assess/2",
    norm_sha256="a" * 64,
    provider="anthropic",
    model="synthetisch-model",
)


def _materiaal():
    return beoordelingsmateriaal(BEGRIP, TEKST, CONTEXT, [BRON], INTENTIE)


def _fingerprint():
    return bereken_ess03_vingerafdruk(BEGRIP, TEKST, CONTEXT, [BRON], intentie=INTENTIE)


def _oordeel(**over) -> dict:
    basis = {
        "verdict": VERDICT_FAIL,
        "applicability": "applicable",
        "unit": "het afzonderlijke fysieke exemplaar",
        "reason": "Het ISBN onderscheidt volgens de bron geen fysieke exemplaren.",
        "evidence": [
            {"location": "definition", "quote": "uitsluitend door zijn ISBN"},
            {"location": f"source:{BRON_ID}", "quote": "dragen hetzelfde ISBN"},
        ],
        "missing_information": None,
        "question": None,
        "uncertainty": None,
    }
    basis.update(over)
    return basis


def _document(oordeel: dict | None = None, **over) -> dict:
    materiaal = _materiaal()
    gevalideerd, rejected = valideer_oordeel(oordeel or _oordeel(), materiaal)
    assert gevalideerd is not None, rejected
    document = {
        "contract_version": "ess03/1",
        "prompt_version": BINDING.prompt_version,
        "norm_sha256": BINDING.norm_sha256,
        "fingerprint": _fingerprint(),
        "status": "assessed",
        "error": None,
        "assessed_at": "2026-09-21T12:00:00+00:00",
        "attribution": {
            "provider": BINDING.provider,
            "model": BINDING.model,
            "task_type": "validation",
            "cached": False,
            "tokens_used": 1,
        },
        "input": {
            "intentie": INTENTIE.als_dict(),
            "materiaal": materiaalhashes(materiaal),
            "prompt_sha256": "p" * 64,
        },
        "judgment": gevalideerd.als_dict(),
        "rejected": rejected,
        "raw_response_sha256": "r" * 64,
    }
    document.update(over)
    return document


def _replay(document, *, binding=BINDING, **over):
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
        assessment=document,
        binding=binding,
    )


# --- R1: volledige actuele binding ------------------------------------------------


class TestR1VolledigeBinding:
    def test_actuele_binding_en_materiaal_geven_een_toegepaste_beoordeling(self):
        uitkomst = _replay(_document())
        assert uitkomst.status == STATUS_FAIL
        assert uitkomst.review["assessment"]["applied"] is True

    @pytest.mark.parametrize(
        ("wijziging", "fragment"),
        [
            ({"prompt_version": "obsolete-prompt"}, "promptversie"),
            ({"norm_sha256": "obsolete-norm"}, "norm"),
            ({"attribution_model": "retired-model"}, "model"),
            ({"attribution_provider": "other-provider"}, "provider"),
        ],
    )
    def test_oude_prompt_norm_of_model_is_historisch_niet_actueel(
        self, wijziging, fragment
    ):
        document = _document()
        if "attribution_model" in wijziging:
            document["attribution"]["model"] = wijziging["attribution_model"]
        elif "attribution_provider" in wijziging:
            document["attribution"]["provider"] = wijziging["attribution_provider"]
        else:
            document.update(wijziging)
        uitkomst = _replay(document)
        assert uitkomst.status == STATUS_OPEN
        samenvatting = uitkomst.review["assessment"]
        assert samenvatting["applied"] is False
        assert fragment in samenvatting["reason"].lower()
        # Het historische oordeel blijft zichtbaar in de samenvatting.
        assert samenvatting["verdict"] == VERDICT_FAIL
        assert samenvatting["historical"] is True

    def test_afwijkende_materiaalhash_is_niet_actueel(self):
        document = _document()
        document["input"]["materiaal"]["definition"] = "0" * 64
        uitkomst = _replay(document)
        assert uitkomst.status == STATUS_OPEN
        assert "materiaal" in uitkomst.review["assessment"]["reason"].lower()

    def test_ontbrekende_of_onvolledige_materiaalbinding_is_niet_actueel(self):
        zonder = _document()
        zonder["input"] = None
        assert _replay(zonder).review["assessment"]["applied"] is False
        onvolledig = _document()
        del onvolledig["input"]["materiaal"]["definition"]
        assert _replay(onvolledig).review["assessment"]["applied"] is False
        extra = _document()
        extra["input"]["materiaal"]["source:onbekend"] = "1" * 64
        assert _replay(extra).review["assessment"]["applied"] is False

    def test_zonder_bekende_actuele_binding_is_niets_actueel(self):
        uitkomst = _replay(_document(), binding=None)
        assert uitkomst.status == STATUS_OPEN
        samenvatting = uitkomst.review["assessment"]
        assert samenvatting["applied"] is False
        assert "actuele beoordelingsbinding" in samenvatting["reason"].lower()

    def test_valideer_beoordeling_rapporteert_de_verwachte_binding(self):
        _, samenvatting = valideer_beoordeling(
            _document(prompt_version="obsolete-prompt"),
            _fingerprint(),
            _materiaal(),
            binding=BINDING,
        )
        assert samenvatting["applied"] is False
        assert samenvatting["historical"] is True
        assert samenvatting["expected_binding"]["prompt_version"] == "ess03-assess/2"


# --- R2: gesloten antwoord -------------------------------------------------------------


class TestR2GeslotenAntwoord:
    def test_parser_accepteert_alleen_een_kaal_json_object(self):
        import json

        goed = json.dumps(_oordeel(), ensure_ascii=False)
        assert parse_modeluitvoer(goed) == _oordeel()
        assert parse_modeluitvoer("```json\n" + goed + "\n```") == _oordeel()
        assert parse_modeluitvoer("Hier is mijn antwoord:\n" + goed) is None
        assert parse_modeluitvoer(goed + "\nHopelijk helpt dit.") is None
        assert parse_modeluitvoer("[" + goed + "]") is None
        assert parse_modeluitvoer(goed + goed) is None

    @pytest.mark.parametrize(
        ("kapot", "fragment"),
        [
            ({**_oordeel(), "extra": 1}, "onbekend veld"),
            ({k: v for k, v in _oordeel().items() if k != "unit"}, "ontbreekt"),
            ({**_oordeel(), "unit": 3}, "unit"),
            ({**_oordeel(), "uncertainty": ["x"]}, "uncertainty"),
            ({**_oordeel(), "evidence": [{"location": "definition"}]}, "evidence"),
            (
                {
                    **_oordeel(),
                    "evidence": [{"location": "definition", "quote": "x", "extra": 1}],
                },
                "evidence",
            ),
            ({**_oordeel(), "evidence": ["geen object"]}, "evidence"),
            ({**_oordeel(), "evidence": []}, "zonder bewijs"),
            ({**_oordeel(), "question": "Welk register?"}, "question"),
            ({**_oordeel(), "applicability": "not_applicable"}, "applicability"),
            (
                {
                    **_oordeel(),
                    "verdict": VERDICT_NOT_APPLICABLE,
                    "applicability": "applicable",
                },
                "applicability",
            ),
            (
                {
                    **_oordeel(),
                    "verdict": VERDICT_INSUFFICIENT,
                    "applicability": "undetermined",
                    "question": "Welke bron? Welk tijdvak?",
                },
                "precies één",
            ),
            (
                {
                    **_oordeel(),
                    "verdict": VERDICT_INSUFFICIENT,
                    "applicability": "undetermined",
                    "question": "Geef het register",
                },
                "precies één",
            ),
        ],
    )
    def test_gesloten_veldenset_typen_en_vraagvorm(self, kapot, fragment):
        fout = structuurfout_modeluitvoer(kapot)
        assert fout is not None, kapot
        assert fragment in fout

    def test_onvoldoende_informatie_met_een_gerichte_vraag_is_welgevormd(self):
        goed = _oordeel(
            verdict=VERDICT_INSUFFICIENT,
            applicability="undetermined",
            evidence=[],
            missing_information="registerafspraak",
            question="Binnen welk register en welke populatie geldt het nummer?",
        )
        assert structuurfout_modeluitvoer(goed) is None


# --- R3: afgewezen bewijs maakt het oordeel onbruikbaar --------------------------


class TestR3Bewijs:
    def test_een_verzonnen_citaat_naast_een_echt_citaat_maakt_het_oordeel_onbruikbaar(
        self,
    ):
        oordeel = _oordeel(
            evidence=[
                {"location": "definition", "quote": "uitsluitend door zijn ISBN"},
                {"location": "source:missing", "quote": "hetzelfde ISBN"},
            ]
        )
        gevalideerd, rejected = valideer_oordeel(oordeel, _materiaal())
        assert gevalideerd is None
        assert any(r["reason"] == "onbekende vindplaats" for r in rejected)

    def test_uitsluitend_verzonnen_bewijs_maakt_het_oordeel_onbruikbaar(self):
        oordeel = _oordeel(
            verdict=VERDICT_PASS,
            evidence=[{"location": "definition", "quote": "met een uniek nummer"}],
        )
        gevalideerd, rejected = valideer_oordeel(oordeel, _materiaal())
        assert gevalideerd is None
        assert any(r["reason"] == "citaat niet in materiaal" for r in rejected)

    def test_geverifieerd_bewijs_blijft_onaangeroerd(self):
        gevalideerd, rejected = valideer_oordeel(_oordeel(), _materiaal())
        assert gevalideerd is not None
        assert rejected == []
        assert len(gevalideerd.evidence) == 2

    def test_replay_met_veranderd_bewijs_in_het_document_is_niet_actueel(self):
        document = _document()
        document["judgment"]["evidence"] = [
            {"location": "definition", "quote": "verzonnen citaat"}
        ]
        uitkomst = _replay(document)
        assert uitkomst.status == STATUS_OPEN
        assert uitkomst.review["assessment"]["applied"] is False


def test_materiaalhashes_zijn_sha256_per_vindplaats():
    materiaal = _materiaal()
    hashes = materiaalhashes(materiaal)
    assert set(hashes) == set(materiaal)
    assert hashes["definition"] == hashlib.sha256(TEKST.encode("utf-8")).hexdigest()
