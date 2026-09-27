"""DEF-768 R8-offsetherstel — de toetsdienst op het antwoordcontract `ess05-answer/1`.

Echte async aanroepen van `Ess05AssessmentService.assess` op een fake AI-grens.
Bewijst: de prompt vraagt geen posities meer (`ess05-assess/15`, T/13
ongewijzigd), de ruwe respons wordt ongewijzigd bewaard en het afgeleide
concept is eraan en aan het materiaal gebonden, de verifier krijgt exact het
afgeleide concept, en de echte R8-respons (oud schema) blijft een weigering
zonder verificatiestap. Stubs bewijzen ketengedrag, geen semantische kwaliteit.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from domain.ess05.bewijs import ANTWOORDSCHEMA, concepthash
from domain.ess05.contract import (
    STATUS_PASS,
    afleidingsbinding,
    beoordeel_onderscheid,
    beoordelingsmateriaal,
    normaliseer_buren,
)
from services.interfaces import AIGenerationResult
from services.validation.ess05_assessment_service import (
    _TOETSINSTRUCTIE,
    Ess05AssessmentService,
    bouw_beoordelingsprompt,
    laad_ess05_norm,
)
from tests.fixtures.def768_fakes import (
    antwoord_uit_spec,
    materiaal_uit_prompt,
    verificatie_voor,
)

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
R8 = json.loads(
    (ROOT / "tests/fixtures/ess05/r8_r720_ruwe_respons_v1.json").read_text(
        encoding="utf-8"
    )
)
CONTEXT = {
    "organisatorische_context": ["Synthetische Uitleendienst"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
LENER = "Persoon met een actuele lening bij de instelling."
BUREN = normaliseer_buren(
    [
        {
            "term": "werknemer",
            "definitie": "Persoon met een arbeidsovereenkomst met de instelling.",
            "herkomst": "gebruiker",
            "bevestigd": True,
        }
    ]
)
#: sha256 van T/13 (`_TOETSINSTRUCTIE`), ongewijzigd sinds `ess05-assess/13`.
T13_SHA256 = "da9fff7fd83f6276060b3a7d0fd8f72b5dc3c1b3306c23bb28e535d63422a171"


def _sha(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def _spec(quote="met een actuele lening"):
    return {
        "reason": "Synthetische onderbouwing.",
        "neighbours": [
            {
                "neighbour_id": b.id,
                "distinction": "distinguished",
                "distinguishing_feature_quote": quote,
                "reason": "Per buur.",
            }
            for b in BUREN
        ],
    }


class FakeAI:
    """Stap 1 levert een vaste tekst of een antwoord uit een spec; stap 2 verifieert
    exact het concept uit de verificatievraag."""

    def __init__(self, stap1):
        self.stap1 = stap1
        self.calls: list[dict] = []
        self.default_model = "fake-default-model"
        self.teksten: list[str] = []

    async def generate_definition(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt, **kwargs})
        if kwargs["task_type"] == "validation":
            tekst = (
                self.stap1
                if isinstance(self.stap1, str)
                else json.dumps(
                    antwoord_uit_spec(self.stap1, materiaal_uit_prompt(prompt))
                )
            )
        else:
            start = prompt.index("<conceptoordeel candidate_hash=")
            blok = prompt[
                prompt.index(">", start) + 1 : prompt.index("</conceptoordeel>")
            ]
            from html import unescape

            tekst = json.dumps(verificatie_voor(json.loads(unescape(blok))))
        self.teksten.append(tekst)
        return AIGenerationResult(
            text=tekst,
            model=f"routed-{kwargs['task_type']}",
            tokens_used=42,
            generation_time=0.01,
            metadata={},
        )


class FakeRouter:
    def get_model(self, task_type):
        return "fakeprovider", f"routed-{task_type}"


async def _assess(stap1):
    ai = FakeAI(stap1)
    svc = Ess05AssessmentService(ai, model_router=FakeRouter())
    doc = await svc.assess("lener", LENER, CONTEXT, [], buren=BUREN)
    return ai, svc, doc.als_dict()


class TestPromptcontract:
    def test_versie_en_ongewijzigde_toetsinstructie(self):
        # assess/16 + verify/3 (R9-bewijsherstel): deelzin per bewijsroute; T/13 gelijk.
        # assess/17 + verify/4 (R10-C3): gesloten bewijsroute per claim; T/13 gelijk.
        # assess/18 (answer/2): genest, citaat-eerst antwoord; T/13 gelijk.
        assert Ess05AssessmentService.PROMPT_VERSION == "ess05-assess/19"
        assert _sha(_TOETSINSTRUCTIE) == T13_SHA256

    def test_prompt_vraagt_citaat_zonder_posities(self):
        systeem, _ = bouw_beoordelingsprompt(
            "lener", LENER, CONTEXT, (), buren=BUREN, intentie=None,
            norm=laad_ess05_norm(),
        )  # fmt: skip
        assert f'"schema_version": "{ANTWOORDSCHEMA}"' in systeem
        assert '"start"' not in systeem and '"end"' not in systeem
        assert "posities in tekens" not in systeem
        assert "precies één keer" in systeem


class TestAfleidingInDeDienst:
    @pytest.mark.asyncio
    async def test_ruwe_respons_bewaard_en_afgeleid_concept_gebonden(self):
        ai, svc, doc = await _assess(_spec())
        assert doc["status"] == "assessed", doc["error"]
        ruw = ai.teksten[0]
        assert doc["raw_response"] == ruw
        assert doc["raw_response_sha256"] == _sha(ruw)
        materiaal = beoordelingsmateriaal("lener", LENER, [], BUREN, contexten=CONTEXT)
        concept = doc["concept"]
        assert doc["concept_derivation"] == {
            "answer_schema_version": ANTWOORDSCHEMA,
            "raw_response_sha256": _sha(ruw),
            "material": doc["input"]["materiaal"],
            "concept_hash": concepthash(concept),
        }
        from domain.ess05.bewijs import Ess05Concept

        assert doc["concept_derivation"] == afleidingsbinding(
            _sha(ruw), Ess05Concept(concept), materiaal
        )
        # De verifier kreeg exact het afgeleide concept (met posities).
        assert doc["verification_input"]["candidate_hash"] == concepthash(concept)
        assert concepthash(concept) in ai.calls[1]["prompt"]
        e = next(
            i for i in concept["evidence"] if i["quote"] == "met een actuele lening"
        )
        assert materiaal["definition"][e["start"] : e["end"]] == e["quote"]
        # Replay past het oordeel toe met de actuele dienstbinding.
        uitkomst = beoordeel_onderscheid(
            "lener", LENER, CONTEXT, [], buren=BUREN, assessment=doc,
            binding=svc.binding(),
        )  # fmt: skip
        assert uitkomst.status == STATUS_PASS, uitkomst

    @pytest.mark.asyncio
    async def test_echte_r8_respons_blijft_weigering_zonder_verifier(self):
        ai, _, doc = await _assess(R8["raw_response"])
        assert doc["status"] == "error"
        assert doc["error"]["type"] == "malformed_response"
        assert doc["error"]["phase"] == "assessment"
        assert ANTWOORDSCHEMA in doc["error"]["message"]
        assert len(ai.calls) == 1  # geen verificatiestap
        assert doc["raw_response"] == R8["raw_response"]
        assert doc["raw_response_sha256"] == R8["raw_response_sha256"]
        assert doc["concept"] is None and doc["concept_derivation"] is None

    @pytest.mark.asyncio
    async def test_dubbelzinnig_citaat_blijft_onverifieerbaar(self):
        # "en" staat meermaals in de kern (een, lening): geen keuze, geen verificatie.
        ai, _, doc = await _assess(_spec(quote="en"))
        assert doc["status"] == "error"
        assert doc["error"]["type"] == "unverifiable_evidence"
        assert "dubbelzinnig" in doc["error"]["message"]
        assert len(ai.calls) == 1
        assert doc["raw_response"] == ai.teksten[0]
