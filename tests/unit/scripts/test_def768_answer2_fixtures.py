"""DEF-768 answer/2 — fixtures, historische regressie, omvang en offline keten.

- **R11 (echt, answer/1)** blijft uitsluitend een negatieve regressie: onder
  de answer/1-parser `malformed_response` met ongebruikte claim C10, live
  (answer/2) geweigerd, nooit getransformeerd of gerepareerd.
- **R9/R10 (answer/2)** zijn synthetisch getransformeerd uit het echte,
  geldige answer/1-antwoord, geen modeluitvoer. De afleiding geeft het
  historische concept terug modulo ID's (claims, rollen, teksten, citaten,
  posities, buurlabels en gebruik).
- De semantische negatieven R9-C5 en R10-C3 blijven in de offline tweestappen-
  keten staan: een verifierstub met `unsupported` blokkeert zonder herstel.
  Sinds answer/3 (assess/19) is de afleiding hier expliciet historisch
  (`schema=ANTWOORDSCHEMA_2`); de live keten krijgt `als_answer3(...)`.
- Omvang: alleen tekens en bytes, geen tokenclaim.

Wat dit NIET bewijst: dat een echt model onder answer/2 het schema volgt,
binnen 3000 tokens blijft of geen semantische overclaim schrijft; dat de echte
verifier C3/C5 afwijst. Dat vraagt een afzonderlijk besloten echte proef.
"""

from __future__ import annotations

import hashlib
import json
import sys

import pytest

from tests.fixtures.def768_fakes import als_answer3, verificatie_voor
from tests.unit.scripts.test_def768_ess05_proefrunner import ROOT, _FakeProvider
from tests.unit.scripts.test_def768_r8_proef import _omgeving8
from tests.unit.scripts.test_def768_r10_c3_bewijsroute import (
    _callrecord,
    _draai,
    _EchteR720,
    _routes,
)

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import maak_answer2_fixtures as maker
import migreer_r7_naar_v2 as mig
import proefinvoer as pi
import run_ess05_proef as runner

from domain.ess05 import bewijs
from domain.ess05.contract import valideer_antwoord

FIXMAP = ROOT / "tests" / "fixtures" / "ess05"
#: De oorspronkelijke fixtures en V8 blijven byte-identiek.
ONGEWIJZIGD = {
    "r8_r720_ruwe_respons_v1.json": None,
    "r9_r720_callrecord_uittreksel_v1.json": (
        "5a7ff2b045f49b59aa480ce4183aa196e58c2d27d2fcfd953f9f2399e6693720"
    ),
    "r10_r720_callrecord_uittreksel_v1.json": (
        "9d64ae98981fc1cdf43c4f91e07e0218f2016dc51c30d845ffb6c463ac92e559"
    ),
}
R11_CALLRECORD_SHA256 = (
    "196542e41632ec6125cd047ed110e2a2350dc80030023cd5e8a3b40fa9a53d9e"
)
R11_RUW_SHA256 = "1f2eca00a90b079d9e48ee20c4c54a7cd72eae2eb55d23f7be86e43467f20f67"


def _sha(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _laad(naam: str) -> dict:
    return json.loads((FIXMAP / naam).read_text(encoding="utf-8"))


R9 = _laad("r9_r720_callrecord_uittreksel_v1.json")
R10 = _laad("r10_r720_callrecord_uittreksel_v1.json")
R11 = _laad("r11_r720_callrecord_uittreksel_v1.json")
A2 = {r: _laad(maker.doelnaam(r)) for r in ("r9", "r10")}
UITTREKSEL = {"r9": R9, "r10": R10}


def _materiaal(geval):
    materiaal, buren, _ = mig.verificatiemateriaal(geval)
    return materiaal, buren


def _genormaliseerd(concept: dict) -> dict:
    """Onafhankelijk van de maker: elke verwijzing opgelost, ID's weg."""
    plaats = {
        e["id"]: [
            e["material_id"],
            e["material_sha256"],
            e["start"],
            e["end"],
            e["quote"],
        ]
        for e in concept["evidence"]
    }
    claims = {c["id"]: c for c in concept["claims"]}

    def c(ref):
        if ref is None:
            return None
        claim = claims[ref]
        return {
            "rol": claim["role"],
            "tekst": claim["text"],
            "citaten": [plaats[e] for e in claim["evidence"]],
            "premissen": [c(p) for p in claim["premises"]],
        }

    return {
        "genus": plaats.get(concept["genus_evidence"]),
        "kenmerken": [plaats[k["evidence"]] for k in concept["core_features"]],
        "reden": [c(r) for r in concept["reason_claims"]],
        "buren": [
            {
                "id": b["neighbour_id"],
                "label": b["distinction"],
                "kenmerk": plaats.get(b["feature_evidence"]),
                "reden": [c(r) for r in b["reason_claims"]],
                "ontbrekend": c(b["missing_feature_claim"]),
                "onzeker": c(b["uncertainty_claim"]),
            }
            for b in concept["neighbours"]
        ],
        "voorstellen": [
            [
                p["term"],
                plaats.get(p["source_evidence"]),
                [c(r) for r in p["reason_claims"]],
            ]
            for p in concept["proposals"]
        ],
        "vraag": concept["question"]
        and [
            concept["question"]["text"],
            [c(r) for r in concept["question"]["claims"]],
        ],
        "alle_claims": sorted(json.dumps(c(i), ensure_ascii=False) for i in claims),
        "alle_citaten": sorted(
            json.dumps(p, ensure_ascii=False) for p in plaats.values()
        ),
    }


class TestBronnenOngewijzigd:
    def test_oorspronkelijke_fixtures_byte_identiek(self):
        for naam, verwacht in ONGEWIJZIGD.items():
            data = (FIXMAP / naam).read_bytes()
            if verwacht is not None:
                assert _sha(data) == verwacht, naam

    def test_r11_uittreksel_letterlijk_uit_het_callrecord(self):
        assert R11["bron"]["callrecord_sha256"] == R11_CALLRECORD_SHA256
        assert R11["raw_response_sha256"] == R11_RUW_SHA256 == _sha(R11["raw_response"])
        assert R11["beoordelingsdocument"]["raw_response"] == R11["raw_response"]
        assert R11["geval_sha256"] == R10["geval_sha256"] == pi.sha_json(R11["geval"])
        assert R11["bron"]["answer_schema_version"] == "ess05-answer/1"


class TestR11BlijftNegatief:
    """Uitsluitend negatieve answer/1-regressie; geen transformatie, geen roundtrip."""

    def test_answer1_parser_geeft_ongebruikte_c10(self):
        materiaal, buren = _materiaal(R11["geval"])
        concept, fouten = valideer_antwoord(
            json.loads(R11["raw_response"]),
            materiaal,
            buren,
            schema=bewijs.ANTWOORDSCHEMA_1,
        )
        assert concept is None
        assert fouten == [
            {"reason": "structuurfout", "detail": "ongebruikte claim(s): ['C10']"}
        ]
        doc = R11["beoordelingsdocument"]
        assert doc["error"] == {
            "type": "malformed_response",
            "message": "modelantwoord schendt de antwoordstructuur: "
            "ongebruikte claim(s): ['C10']",
            "phase": "assessment",
        }
        assert doc["concept"] is None and doc["concept_derivation"] is None

    def test_live_answer2_weigert_het_r11_antwoord(self):
        materiaal, buren = _materiaal(R11["geval"])
        concept, fouten = valideer_antwoord(
            json.loads(R11["raw_response"]), materiaal, buren
        )
        assert concept is None and fouten[0]["reason"] == "structuurfout"

    def test_maker_biedt_r11_niet_aan_en_weigert_een_ongeldig_antwoord(
        self, monkeypatch
    ):
        assert set(maker.BRONNEN) == {"r9", "r10"}
        with pytest.raises(KeyError):
            maker.bouw_fixture("r11")
        # Ook aangeboden (met juiste hash) weigert de maker R11 inhoudelijk:
        # onder answer/1 geeft het antwoord geen concept (ongebruikte C10).
        pad = "tests/fixtures/ess05/r11_r720_callrecord_uittreksel_v1.json"
        monkeypatch.setitem(
            maker.BRONNEN, "r11", (pad, _sha((ROOT / pad).read_bytes()))
        )
        with pytest.raises(maker.MakerfoutError, match="ongebruikte claim"):
            maker.bouw_fixture("r11")


class TestAnswer2Fixtures:
    @pytest.mark.parametrize("ronde", ["r9", "r10"])
    def test_label_en_herkomst(self, ronde):
        fixture = A2[ronde]
        pad, sha = maker.BRONNEN[ronde]
        assert fixture["synthetisch_getransformeerd"] is True
        assert fixture["modeluitvoer"] is False
        assert "GEEN MODELUITVOER" in fixture["label"]
        assert fixture["bron"]["uittreksel"] == pad
        assert (
            fixture["bron"]["uittreksel_sha256"]
            == sha
            == _sha((ROOT / pad).read_bytes())
        )
        bron = UITTREKSEL[ronde]
        assert fixture["bron"]["callrecord_sha256"] == bron["bron"]["callrecord_sha256"]
        assert fixture["bron"]["raw_response_sha256"] == bron["raw_response_sha256"]
        assert fixture["transformatie"] == {
            "script": maker.SCRIPT,
            "script_sha256": _sha((ROOT / maker.SCRIPT).read_bytes()),
        }
        assert fixture["raw_response_sha256"] == _sha(fixture["raw_response"])
        assert json.loads(fixture["raw_response"])["schema_version"] == "ess05-answer/2"

    @pytest.mark.parametrize("ronde", ["r9", "r10"])
    def test_deterministisch_reproduceerbaar(self, ronde):
        tekst = (FIXMAP / maker.doelnaam(ronde)).read_text(encoding="utf-8")
        assert maker.bouw_fixture(ronde) == tekst

    @pytest.mark.parametrize("ronde", ["r9", "r10"])
    def test_afleiding_geeft_het_historische_concept_modulo_ids(self, ronde):
        bron = UITTREKSEL[ronde]
        historisch = bron["beoordelingsdocument"]["concept"]
        materiaal, buren = _materiaal(bron["geval"])
        concept, fouten = valideer_antwoord(
            json.loads(A2[ronde]["raw_response"]),
            materiaal,
            buren,
            schema=bewijs.ANTWOORDSCHEMA_2,
        )
        assert fouten == []
        nieuw = concept.als_dict()
        assert _genormaliseerd(nieuw) == _genormaliseerd(historisch)
        for veld in ("evidence", "claims", "core_features", "neighbours", "proposals"):
            assert len(nieuw[veld]) == len(historisch[veld]), veld
        # Dedup verschuift niets: de claim-ID's volgen hier zelfs de historische.
        assert [c["id"] for c in nieuw["claims"]] == [
            c["id"] for c in historisch["claims"]
        ]
        assert concept.hash == A2[ronde]["afgeleid_concept_hash"]

    def test_r9_c5_blijft_de_gevolgtrekking_op_c1_en_c4(self):
        materiaal, buren = _materiaal(R9["geval"])
        concept, _ = valideer_antwoord(
            json.loads(A2["r9"]["raw_response"]),
            materiaal,
            buren,
            schema=bewijs.ANTWOORDSCHEMA_2,
        )
        c5 = next(c for c in concept.data["claims"] if c["id"] == "C5")
        assert (c5["role"], c5["premises"]) == ("inference", ["C1", "C4"])

    def test_r10_c3_blijft_material_op_alleen_het_e7_citaat(self):
        materiaal, buren = _materiaal(R10["geval"])
        concept, _ = valideer_antwoord(
            json.loads(A2["r10"]["raw_response"]),
            materiaal,
            buren,
            schema=bewijs.ANTWOORDSCHEMA_2,
        )
        historisch = R10["beoordelingsdocument"]["concept"]
        e7 = next(e for e in historisch["evidence"] if e["id"] == "E7")
        c3 = next(c for c in concept.data["claims"] if c["id"] == "C3")
        (plaats,) = [e for e in concept.data["evidence"] if e["id"] in c3["evidence"]]
        assert (plaats["quote"], plaats["start"], plaats["end"]) == (
            e7["quote"],
            e7["start"],
            e7["end"],
        )


class TestOmvang:
    """Alleen tekens en bytes; geen tokenclaim, geen tokenizer.

    Gemeten (compact, zonder witruimte): answer/2 is 1,89x (R9) en 1,63x (R10)
    het echte answer/1-antwoord; zonder de hashes 1,69x en 1,47x. De groei zit
    in de herhaalde citaten (materiaal-id, hash en fragment per inline citaat;
    R9: 22 inline citaten tegen 7 bewijsplaatsen) en in herhaalde premissen.
    De diagnoseschatting (1,24x/1,10x) liet hash en materiaal-id per citaat
    weg. Deze grenzen bewaken alleen tegen onverwachte groei; ze bewijzen geen
    marge onder 3000 outputtokens (zie het resultaatrapport).
    """

    @staticmethod
    def _compact(ruw: str) -> str:
        return json.dumps(json.loads(ruw), ensure_ascii=False, separators=(",", ":"))

    @pytest.mark.parametrize(
        ("ronde", "citaten", "bewijsplaatsen"), [("r9", 22, 7), ("r10", 19, 7)]
    )
    def test_gemeten_omvang_blijft_begrensd(self, ronde, citaten, bewijsplaatsen):
        ruw2 = A2[ronde]["raw_response"]
        compact2 = self._compact(ruw2)
        compact1 = self._compact(UITTREKSEL[ronde]["raw_response"])
        assert len(compact2) <= 2.0 * len(compact1)
        assert compact2.count('"material_sha256"') == citaten
        assert compact1.count('"material_sha256"') == bewijsplaatsen
        # Ook zonder de hashes groeit het antwoord (gemeten 1,47-1,69x).
        zonder2 = len(compact2) - 64 * citaten
        zonder1 = len(compact1) - 64 * bewijsplaatsen
        assert zonder2 <= 1.8 * zonder1

    def test_stap1_payload_blijft_binnen_de_bytegrens(self):
        omg = _omgeving8(_FakeProvider())
        grens = runner.PROEVEN["R11"].identiteit.kostenbewaking.bytegrens
        prompt = pi.bouw_t_prompt(pi.modelprojectie(R10["geval"]), omg.norm)
        system, user = prompt.teksten
        bytes_ = runner._payloadbytes(omg, "t", omg.dienst._max_tokens, system, user)
        assert bytes_ <= grens[omg.dienst.TASK_TYPE]
        assert bewijs.ANTWOORDSCHEMA in system


def _volledig(kandidaat, concept):
    return verificatie_voor(concept, candidate_hash=kandidaat)


def _met(**uitkomsten):
    def verifier(kandidaat, concept):
        return verificatie_voor(
            concept, candidate_hash=kandidaat, uitkomsten=uitkomsten
        )

    return verifier


#: Live geldt answer/3: de offline keten krijgt de answer/2-fixture via
#: `als_answer3` (schema actueel, top-level bronclaims naar de reden van de
#: eerste buur; claim- en bewijs-ID's gelijk). Synthetisch, geen modeluitvoer.
LIVE = {r: als_answer3(A2[r]["raw_response"]) for r in ("r9", "r10")}


def _live_concepthash(ronde: str) -> str:
    materiaal, buren = _materiaal(UITTREKSEL[ronde]["geval"])
    concept, fouten = valideer_antwoord(json.loads(LIVE[ronde]), materiaal, buren)
    assert concept is not None, fouten
    return concept.hash


class TestOfflineKeten:
    """De echte runnerketen (stap 1 + verifier-stap), offline, met stubs."""

    def test_answer3_r10_volledig_supported_wordt_vrijgegeven(self, tmp_path):
        provider = _EchteR720(LIVE["r10"], _volledig)
        (resultaat,) = _draai(tmp_path, provider)["resultaten"]
        assert resultaat["geaccepteerd"] is True
        assert provider.stappen == ["beoordeling", "verificatie"]
        doc = _callrecord(tmp_path)["beoordelingsdocument"]
        assert doc["raw_response"] == LIVE["r10"]  # onveranderd
        assert doc["concept_derivation"]["answer_schema_version"] == (
            bewijs.ANTWOORDSCHEMA
        )
        assert doc["prompt_version"] == "ess05-assess/19"
        assert doc["concept_derivation"]["concept_hash"] == _live_concepthash("r10")

    def test_r10_c3_unsupported_blokkeert_zonder_herstel(self, tmp_path):
        import proefgrootboek as gb

        provider = _EchteR720(LIVE["r10"], _met(**{"claim:C3": "unsupported"}))
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _draai(tmp_path, provider)
        assert provider.stappen == ["beoordeling", "verificatie"]
        doc = _callrecord(tmp_path)["beoordelingsdocument"]
        assert doc["error"]["type"] == "semantic_verification_failed"
        assert doc["judgment"] is None
        assert doc["raw_response"] == LIVE["r10"]

    def test_r9_c5_unsupported_blokkeert_zonder_herstel(self, tmp_path):
        import proefgrootboek as gb

        provider = _EchteR720(LIVE["r9"], _met(**{"claim:C5": "unsupported"}))
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _draai(tmp_path, provider)
        doc = _callrecord(tmp_path)["beoordelingsdocument"]
        assert doc["error"]["type"] == "semantic_verification_failed"

    def test_geneste_premissen_komen_als_route_bij_de_verifier(self, tmp_path):
        provider = _EchteR720(LIVE["r9"], _volledig)
        _draai(tmp_path, provider)
        routes = _routes(provider.gebruikers[1])
        teksten = {
            c["id"]: c["text"] for c in R9["beoordelingsdocument"]["concept"]["claims"]
        }
        assert routes["C5"]["gesloten_bewijsroute"] == [
            {"premisse": p, "uitspraak": teksten[p]} for p in ("C1", "C4")
        ]

    @pytest.mark.parametrize("bron", [R9, R10, R11], ids=["r9", "r10", "r11"])
    def test_historisch_answer1_antwoord_wordt_live_geweigerd(self, tmp_path, bron):
        import proefgrootboek as gb

        provider = _EchteR720(bron["raw_response"], _volledig)
        with pytest.raises(gb.BudgetSchendingError, match="niet geaccepteerd"):
            _draai(tmp_path, provider)
        assert provider.stappen == ["beoordeling"]  # geen verificatie
        doc = _callrecord(tmp_path)["beoordelingsdocument"]
        assert doc["error"]["type"] == "malformed_response"
        assert doc["concept"] is None
        assert doc["raw_response"] == bron["raw_response"]
