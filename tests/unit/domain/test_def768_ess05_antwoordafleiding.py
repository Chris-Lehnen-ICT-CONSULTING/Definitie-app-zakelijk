"""DEF-768 R8-offsetherstel — de app leidt bewijsplaatsen af uit het modelantwoord.

Aanleiding: de enige echte R8-aanroep (R720) gaf zeven letterlijk en precies
één keer aanwezige citaten met de juiste materiaalhash, maar met door het
model verkeerd getelde posities (`unverifiable_evidence`). Tekens tellen door
het taalmodel is geen betrouwbare basis.

Contract `ess05-answer/1`: het model kiest per bewijsplaats materiaal-id, hash
en het exacte citaat; vaste code leidt begin en eind af, alleen bij één
ondubbelzinnige letterlijke match. Het resultaat is een gewoon
`ess05-concept/1` dat de bestaande vaste controles, de verifier (candidate
hash) en de replay doorloopt. Geen fuzzy matching, geen ander materiaal, geen
reparatie; oude `/1`-antwoorden worden niet als nieuw antwoord gelezen.

Grens: deze tests bewijzen deterministische binding, geen semantische
juistheid van de citaten.

Sinds `ess05-answer/2` (genest, citaat-eerst) is answer/1 historisch: de
afleidingstests hieronder draaien bewust met de expliciete versie
`ANTWOORDSCHEMA_1` (regressie van de plaatsbepaling). De replaytests gebruiken
het actuele, geneste antwoord; zie ook `test_def768_ess05_answer2.py`.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from domain.ess05 import bewijs
from domain.ess05.bewijs import (
    CONCEPTSCHEMA,
    valideer_concept,
)
from domain.ess05.contract import (
    Ess05Beoordelingsbinding,
    beoordelingsafwijzing,
)
from domain.modeluitvoer import parse_modeluitvoer
from tests.fixtures.def768_fakes import (
    antwoord1_uit_concept,
    bouw_document,
    verificatie_voor,
)

pytestmark = [pytest.mark.unit]

#: Historisch plat antwoord: de afleidingstests toetsen die versie expliciet.
ANTWOORDSCHEMA = bewijs.ANTWOORDSCHEMA_1
#: Het actuele antwoord (replay van nieuwe documenten).
LIVE_ANTWOORDSCHEMA = bewijs.ANTWOORDSCHEMA


def valideer_antwoord(antwoord, materiaal, buren):
    return bewijs.valideer_antwoord(antwoord, materiaal, buren, schema=ANTWOORDSCHEMA)


ROOT = Path(__file__).resolve().parents[3]
R8 = json.loads(
    (ROOT / "tests/fixtures/ess05/r8_r720_ruwe_respons_v1.json").read_text(
        encoding="utf-8"
    )
)
MAT: dict[str, str] = R8["materiaal"]
BUREN = {
    k.removeprefix("neighbour:"): v
    for k, v in MAT.items()
    if k.startswith("neighbour:")
}
RUW = json.loads(R8["raw_response"])
#: De werkelijke, unieke plaatsen van de zeven citaten in hun materiaal.
WERKELIJK = {
    "E1": (0, 13),
    "E2": (18, 32),
    "E3": (38, 78),
    "E4": (41, 103),
    "E5": (18, 49),
    "E6": (482, 562),
    "E7": (0, 114),
}


def _sha(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def _nieuw() -> dict:
    """Dezelfde modelkeuzes (id, materiaal, hash, citaat) in `ess05-answer/1`."""
    return antwoord1_uit_concept(RUW)


def _redenen(fouten) -> list[str]:
    return [f["reason"] for f in fouten]


# --- de echte R8-respons ---------------------------------------------------------------


class TestEchteR8Respons:
    def test_fixture_is_de_ongewijzigde_betaalde_respons(self):
        assert _sha(R8["raw_response"]) == R8["raw_response_sha256"]
        assert R8["fout"]["type"] == "unverifiable_evidence"
        assert RUW["schema_version"] == CONCEPTSCHEMA

    def test_diagnose_citaten_letterlijk_en_uniek_alleen_posities_fout(self):
        for item in RUW["evidence"]:
            tekst = MAT[item["material_id"]]
            assert item["material_sha256"] == _sha(tekst)
            assert tekst.count(item["quote"]) == 1
            start = tekst.index(item["quote"])
            assert (start, start + len(item["quote"])) == WERKELIJK[item["id"]]
            assert (item["start"], item["end"]) != WERKELIJK[item["id"]]

    def test_oude_respons_blijft_historisch_afgewezen(self):
        concept, fouten = valideer_concept(RUW, MAT, BUREN)
        assert concept is None
        assert len(fouten) == 7
        assert set(_redenen(fouten)) == {
            "citaat wijkt af van de bewijsplaats",
            "bewijsplaats buiten bereik",
        }

    def test_oude_respons_wordt_niet_als_nieuw_antwoord_gelezen(self):
        concept, fouten = valideer_antwoord(RUW, MAT, BUREN)
        assert concept is None
        assert fouten[0]["reason"] == "structuurfout"
        assert ANTWOORDSCHEMA in fouten[0]["detail"]

    def test_zelfde_keuzes_expliciet_worden_deterministisch_gebonden(self):
        concept, fouten = valideer_antwoord(_nieuw(), MAT, BUREN)
        assert fouten == []
        data = concept.als_dict()
        assert data["schema_version"] == CONCEPTSCHEMA
        for item in data["evidence"]:
            assert (item["start"], item["end"]) == WERKELIJK[item["id"]]
            tekst = MAT[item["material_id"]]
            assert tekst[item["start"] : item["end"]] == item["quote"]
        # Alles behalve schema en posities is letterlijk het modelantwoord.
        zonder = deepcopy(data)
        for item in zonder["evidence"]:
            del item["start"], item["end"]
        zonder["schema_version"] = ANTWOORDSCHEMA
        assert zonder == _nieuw()
        # Het afgeleide concept doorstaat de bestaande vaste controles.
        assert valideer_concept(data, MAT, BUREN) == (concept, [])
        assert valideer_antwoord(_nieuw(), MAT, BUREN)[0].hash == concept.hash


# --- weigeringen -----------------------------------------------------------------------


def _met(index: int, **velden) -> dict:
    antwoord = _nieuw()
    antwoord["evidence"][index].update(velden)
    return antwoord


class TestAfleidingWeigert:
    @pytest.mark.parametrize(
        ("antwoord", "reden"),
        [
            # Hoofdletter, dubbele spatie: niet letterlijk, geen fuzzy match.
            (_met(0, quote="Transportgang"), "citaat staat niet letterlijk"),
            (_met(1, quote="via  baan Neral"), "citaat staat niet letterlijk"),
            # Letterlijk in de bron, maar het aangewezen materiaal is de kern.
            (
                _met(
                    0,
                    quote="Neral en Dovar zijn verschillende banen",
                    material_id="definition",
                ),
                "citaat staat niet letterlijk",
            ),
            (_met(0, material_sha256="0" * 64), "materiaalhash wijkt af"),
            (_met(5, material_id="source:doc:onbekend"), "onbekend materiaal"),
            # "transportgang" staat meermaals in de bron: dubbelzinnig.
            (
                _met(
                    6,
                    quote="transportgang",
                    material_id="source:doc:synthetisch-R720",
                    material_sha256=_sha(MAT["source:doc:synthetisch-R720"]),
                ),
                "citaat is dubbelzinnig",
            ),
        ],
    )
    def test_niet_ondubbelzinnig_letterlijk_blijft_weigering(self, antwoord, reden):
        concept, fouten = valideer_antwoord(antwoord, MAT, BUREN)
        assert concept is None
        assert fouten[0]["reason"].startswith(reden), fouten

    def test_overlappende_treffers_zijn_dubbelzinnig(self):
        materiaal = {**MAT, "definition": "aaa " + MAT["definition"]}
        antwoord = _met(0, quote="aa", material_sha256=_sha(materiaal["definition"]))
        _, fouten = valideer_antwoord(antwoord, materiaal, BUREN)
        assert fouten[0]["reason"].startswith("citaat is dubbelzinnig")

    def test_alle_foute_plaatsen_worden_gemeld(self):
        antwoord = _nieuw()
        for item in antwoord["evidence"]:
            item["material_sha256"] = "0" * 64
        _, fouten = valideer_antwoord(antwoord, MAT, BUREN)
        assert _redenen(fouten) == ["materiaalhash wijkt af"] * 7

    @pytest.mark.parametrize(
        "anders",
        [
            {"start": 0, "end": 13},  # posities horen niet in het antwoord
            {"quote": ""},
        ],
    )
    def test_posities_of_leeg_citaat_zijn_structuurfout(self, anders):
        _, fouten = valideer_antwoord(_met(0, **anders), MAT, BUREN)
        assert fouten[0]["reason"] == "structuurfout"

    def test_structuurfout_gaat_voor_een_dubbelzinnige_plaats(self):
        antwoord = _met(
            6,
            quote="transportgang",
            material_sha256=_sha(MAT["source:doc:synthetisch-R720"]),
        )
        antwoord["reason_claims"] = ["C-bestaat-niet"]
        _, fouten = valideer_antwoord(antwoord, MAT, BUREN)
        assert fouten[0]["reason"] == "structuurfout"
        assert "C-bestaat-niet" in fouten[0]["detail"]

    def test_xml_escape_in_het_citaat_telt_als_een_teken(self):
        kern = "recht & plicht van de houder"
        materiaal = {**MAT, "definition": kern}
        antwoord = _nieuw()
        antwoord["evidence"][0].update(
            quote="recht &amp; plicht", material_sha256=_sha(kern)
        )
        antwoord["evidence"][1:3] = []
        antwoord["core_features"] = []
        antwoord["claims"][1]["evidence"] = ["E1"]
        antwoord["neighbours"] = [
            dict(n, distinction="unclear", feature_evidence=None)
            for n in antwoord["neighbours"]
        ]
        concept, fouten = valideer_antwoord(antwoord, materiaal, BUREN)
        assert fouten == []
        e1 = concept.data["evidence"][0]
        assert (e1["start"], e1["end"], e1["quote"]) == (0, 14, "recht & plicht")


# --- replay: afgeleid concept gebonden aan ruwe respons en materiaal ---------------------

BINDING = Ess05Beoordelingsbinding(
    prompt_version="ess05-assess/fake",
    verification_prompt_version="ess05-verify/fake",
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
BUURLIJST = [
    {
        "term": "werknemer",
        "definitie": WERKNEMER,
        "herkomst": "gebruiker",
        "bevestigd": True,
    }
]


def _document(**kw):
    from domain.ess05.contract import normaliseer_buren

    (buur,) = normaliseer_buren(BUURLIJST)
    spec = {
        "reason": "Synthetisch.",
        "neighbours": [
            {
                "neighbour_id": buur.id,
                "distinction": "distinguished",
                "distinguishing_feature_quote": "actuele lening",
                "reason": "Synthetisch buuroordeel.",
            }
        ],
    }
    return bouw_document(
        "lener", LENER, CONTEXT, [], buren=BUURLIJST, spec=spec, binding=BINDING, **kw
    )


def _afwijzing(document, tekst=LENER):
    return beoordelingsafwijzing(
        document, "lener", tekst, CONTEXT, [], intentie=None, buren=BUURLIJST,
        binding=BINDING,
    )  # fmt: skip


class TestReplaybinding:
    def test_document_bindt_ruwe_respons_materiaal_en_concept(self):
        document = _document()
        assert _afwijzing(document) is None
        afleiding = document["concept_derivation"]
        assert set(afleiding) == {
            "answer_schema_version",
            "raw_response_sha256",
            "material",
            "concept_hash",
        }
        assert afleiding["answer_schema_version"] == LIVE_ANTWOORDSCHEMA
        assert document["raw_response_sha256"] == _sha(document["raw_response"])
        assert afleiding["raw_response_sha256"] == document["raw_response_sha256"]
        assert afleiding["material"] == document["input"]["materiaal"]
        assert (
            afleiding["concept_hash"]
            == document["verification_input"]["candidate_hash"]
        )
        # De ruwe respons bevat geen posities en geen ID's; het concept wel (afgeleid).
        antwoord = parse_modeluitvoer(document["raw_response"])
        assert antwoord["schema_version"] == LIVE_ANTWOORDSCHEMA
        assert '"start"' not in document["raw_response"]
        assert '"id"' not in document["raw_response"]

    def test_gewijzigde_ruwe_respons_wordt_niet_toegepast(self):
        document = _document()
        document["raw_response"] = document["raw_response"].replace(
            "Synthetisch.", "Anders."
        )
        assert "ruwe respons" in _afwijzing(document)

    def test_ontbrekende_ruwe_respons_wordt_niet_toegepast(self):
        document = _document()
        document["raw_response"] = None
        assert "ruwe respons" in _afwijzing(document)

    def test_concept_dat_niet_uit_de_respons_volgt_wordt_niet_toegepast(self):
        document = _document()
        # Een geldig maar ander concept (andere reden) met passende verificatie.
        ander = deepcopy(document["concept"])
        ander["claims"][0]["text"] = "Een andere reden."
        document["concept"] = ander
        document["verification"] = verificatie_voor(ander)
        from domain.ess05.bewijs import concepthash

        document["verification_input"]["candidate_hash"] = concepthash(ander)
        document["concept_derivation"]["concept_hash"] = concepthash(ander)
        assert "afgeleid" in _afwijzing(document)

    def test_afleidingshash_moet_bij_het_concept_horen(self):
        document = _document()
        document["concept_derivation"]["concept_hash"] = "0" * 64
        assert "afleiding" in _afwijzing(document)

    def test_afleiding_hoort_bij_het_huidige_materiaal(self):
        document = _document()
        document["concept_derivation"]["material"] = {"definition": "0" * 64}
        assert "afleiding" in _afwijzing(document)

    def test_verificatie_van_een_ander_concept_wordt_niet_toegepast(self):
        document = _document()
        # De verifier moet het exact afgeleide concept toetsen, niet een
        # antwoordvorm ervan (hier: het platte antwoord zonder posities).
        antwoord = antwoord1_uit_concept(document["concept"])
        document["verification"] = verificatie_voor(antwoord)
        assert "verificatie" in _afwijzing(document)
