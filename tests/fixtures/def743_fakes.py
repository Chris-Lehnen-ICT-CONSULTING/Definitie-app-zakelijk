"""Deterministische stand-ins voor de AI-grenzen van pakket F (DEF-743).

Geen model, geen netwerk, geen productie-DB. Twee grenzen worden nagebootst:

* `FakeBronbeoordeling` — de `SourceAssessmentService`-grens die de actieve
  wrapper (C) aanroept. Bouwt een *geldige* beoordeling (contract C §5) met
  een geverifieerd citaat uit de werkelijk aangeleverde passage en de echte
  C-vingerafdruk, per scenario `pass` / `fail` / `open` / `error`. Telt
  aanroepen en bewaart de laatst ontvangen bronbundel (bewijs dat de
  hertoetsing dezelfde bronset kreeg).
* `FakeAI` — de `AIServiceV2.generate_definition`-grens die de
  voorsteldienst (F) aanroept. Telt aanroepen, bewaart prompts en geeft een
  configureerbaar JSON-antwoord.

Gedeeld door de service- en UI-tests van pakket F.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from domain.sources.contract import (
    CONTRACTVERSIE,
    beoordeling_technische_fout,
    bereken_bronvingerafdruk,
)
from domain.sources.normalisatie import bereken_inhoudshash, canoniseer_bronnen
from services.interfaces import AIGenerationResult

BEGRIP = "bestuursorgaan"
TEKST = "orgaan van een rechtspersoon die krachtens publiekrecht is ingesteld"
ORG = ["Stichting Zilver"]
JUR = ["bestuursrecht"]
WET = ["Awb"]
PASSAGE_AWB = (
    "Onder bestuursorgaan wordt verstaan: een orgaan van een rechtspersoon "
    "die krachtens publiekrecht is ingesteld, met uitzondering van de "
    "rechterlijke macht."
)
CITAAT = "een orgaan van een rechtspersoon die krachtens publiekrecht is ingesteld"

BRONNEN: list[dict[str, Any]] = [
    {
        "provider": "rag",
        "chunk_id": "chunk-awb-1-1",
        "document_id": "doc-awb",
        "chunk_index": 4,
        "created_at": "2026-09-14T10:00:00Z",
        "title": "Awb artikel 1:1",
        "url": None,
        "snippet": PASSAGE_AWB,
        "score": 0.83,
        "used_in_prompt": True,
        "bron_type": "wet_regelgeving",
        "legal": {"citation_text": "Awb art. 1:1"},
    },
    {
        "provider": "documents",
        "doc_id": "upload-7",
        "filename": "awb-uittreksel.pdf",
        "title": "awb-uittreksel.pdf",
        "citation_label": "p. 3",
        "selection_basis": "term_match",
        "url": None,
        "snippet": "Algemene wet bestuursrecht, hoofdstuk 1: begripsbepalingen.",
        "score": 1.0,
        "used_in_prompt": False,
        "omitted_reason": "budget",
    },
]


def bouw_beoordeling(
    begrip: str,
    tekst: str,
    contexten: dict[str, list[str]],
    bronnen_ruw: Any,
    *,
    scenario: str = "pass",
    peildatum: str | None = None,
    receipt_cap: int | None = None,
    claims: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Een contractconforme CON-02-beoordeling voor exact deze invoer.

    `claims`: expliciete claims voor `semantic_support` (ook `[]`) — voor de
    proef "fail zonder geïdentificeerde negatieve claim". `receipt_cap`: met een
    waarde krijgt de beoordeling een
    `assessment_receipt` (C §5a) met per canonieke bron exact de verzonden
    passage `passage[:cap]`, beide hashes en de afkapmarkering; zonder waarde
    ontbreekt de kwitantie (historische beoordeling).

    `pass`: alle onderdelen voldoen met geverifieerd citaat; `fail`:
    betekenissteun voldoet niet (citaat toont de ontbrekende uitzondering);
    `open`: betekenissteun nog te beoordelen (onzekerheid); `error`:
    technische fout (time-out), geen onderdelen.
    """
    canoniek = canoniseer_bronnen(bronnen_ruw)
    vingerafdruk = bereken_bronvingerafdruk(
        begrip, tekst, contexten, canoniek, peildatum=peildatum
    )
    if scenario == "error":
        return beoordeling_technische_fout(
            vingerafdruk, "timeout", "synthetische time-out", sources=canoniek
        )
    awb = next(b for b in canoniek if b.source_id == "rag:doc-awb:chunk-awb-1-1")
    bewijs = [{"source_id": awb.source_id, "quote": CITAAT, "locator": awb.locator}]
    # F1: niet-tekstuele tekortkomingen (gezag/verwijzing) naast een geslaagde
    # betekenissteun; en een betekenisfail waarvan het model óók een claim
    # verzon (`rejected`) — een vermoede evaluatorfout.
    gezag_status = "fail" if scenario == "authority_fail" else "pass"
    verwijzing_status = "fail" if scenario == "reference_fail" else "pass"
    steun_status = {
        "pass": "pass",
        "fail": "fail",
        "open": "review_required",
        "authority_fail": "pass",
        "reference_fail": "pass",
        "fail_rejected": "fail",
    }[scenario]
    steun_reden = {
        "pass": "De bron dekt de bepalende kenmerken.",
        "fail": (
            "De uitzondering voor de rechterlijke macht uit artikel 1:1 ontbreekt "
            "in de definitiezin."
        ),
        "open": "Onzeker of de uitzondering voor de rechterlijke macht bedoeld is.",
    }[
        {
            "authority_fail": "pass",
            "reference_fail": "pass",
            "fail_rejected": "fail",
        }.get(scenario, scenario)
    ]
    afgewezen = (
        [
            {
                "part": "semantic_support",
                "reason": "citaat niet in bron",
                "detail": "verzonnen citaat over de rechterlijke macht",
            }
        ]
        if scenario == "fail_rejected"
        else []
    )
    return {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": "con02-assess/1",
        "fingerprint": vingerafdruk,
        "status": "assessed",
        "error": None,
        "assessed_at": "2026-09-15T12:00:00+00:00",
        "attribution": {
            "provider": "fake",
            "model": "fake-beoordelaar",
            "task_type": "validation",
            "cached": False,
            "tokens_used": 0,
        },
        "peildatum": peildatum,
        "sources": [b.als_dict() for b in canoniek],
        "parts": {
            "source_authority": {
                "status": gezag_status,
                "reason": (
                    "Wettekst (Awb) is een authentieke bron voor dit begrip."
                    if gezag_status == "pass"
                    else "De aangeleverde bron is een niet-vastgestelde concepttekst."
                ),
                "uncertainty": None,
                "evidence": deepcopy(bewijs),
                "sources": [
                    {
                        "source_id": awb.source_id,
                        "profile": "wet_regelgeving",
                        "applicable": True,
                        "reason": "Awb art. 1:1 definieert het begrip.",
                    }
                ],
            },
            "semantic_support": {
                "status": steun_status,
                "reason": steun_reden,
                "uncertainty": (
                    "Uitzondering rechterlijke macht" if scenario == "open" else None
                ),
                "evidence": deepcopy(bewijs),
                # `claims`: expliciete lijst (ook leeg) overschrijft de standaardclaim.
                "claims": (
                    deepcopy(claims)
                    if claims is not None
                    else [
                        {
                            "aspect": "uitzondering",
                            "text": "met uitzondering van de rechterlijke macht",
                            "supported": scenario == "pass",
                            "source_id": awb.source_id,
                        }
                    ]
                ),
            },
            "reference_quality": {
                "status": verwijzing_status,
                "reason": (
                    "Artikel 1:1 Awb is precies terugvindbaar."
                    if verwijzing_status == "pass"
                    else "De verwijzing noemt geen artikel en is niet precies terugvindbaar."
                ),
                "uncertainty": None,
                "evidence": deepcopy(bewijs),
                "sources": [
                    {
                        "source_id": awb.source_id,
                        "locatable": True,
                        "reason": "artikelnummer aanwezig",
                    }
                ],
            },
        },
        "rejected": afgewezen,
        "raw_response_sha256": None,
        "assessment_receipt": (
            {
                "version": "1",
                "max_passage_chars": receipt_cap,
                "hash_algorithm": "sha256-utf8-hex",
                "sources": [
                    {
                        "source_id": b.source_id,
                        "original_content_hash": b.content_hash,
                        "content": b.passage[:receipt_cap],
                        "content_hash": bereken_inhoudshash(b.passage[:receipt_cap]),
                        "truncated": len(b.passage) > receipt_cap,
                        "source_version": b.version,
                    }
                    for b in canoniek
                ],
            }
            if receipt_cap is not None
            else None
        ),
    }


class FakeBronbeoordeling:
    """Stand-in voor `SourceAssessmentService.assess` (C-grens)."""

    PROMPT_VERSION = "con02-assess/1"

    def __init__(self, scenario: str = "pass") -> None:
        self.scenario = scenario
        self.calls = 0
        self.laatste_bronnen: Any = None
        self.laatste_tekst: str | None = None

    async def assess(
        self,
        begrip: str,
        tekst: str,
        contexten: Any,
        bronnen_ruw: Any,
        *,
        peildatum: str | None = None,
        correlation_id: str | None = None,
        receipt: Any = None,
    ) -> dict[str, Any]:
        self.calls += 1
        self.laatste_bronnen = deepcopy(bronnen_ruw)
        self.laatste_tekst = tekst
        if self.scenario == "raise":
            msg = "synthetische storing in de beoordelingsdienst"
            raise RuntimeError(msg)
        return bouw_beoordeling(
            begrip,
            tekst,
            contexten,
            bronnen_ruw,
            scenario=self.scenario,
            peildatum=peildatum,
        )


VOORSTEL_JSON = {
    "voorstel": (
        "orgaan van een rechtspersoon die krachtens publiekrecht is ingesteld, "
        "met uitzondering van de rechterlijke macht"
    ),
    "reden": (
        "Bevinding semantic_support: de uitzondering voor de rechterlijke macht "
        "uit bron rag:doc-awb:chunk-awb-1-1 ontbrak."
    ),
    "behouden": ["krachtens publiekrecht ingesteld"],
    "onzekerheid": None,
}


class FakeAI:
    """Stand-in voor `AIServiceV2.generate_definition` (F-grens)."""

    def __init__(
        self, antwoord: Any = None, *, storing: Exception | None = None
    ) -> None:
        self.calls = 0
        self.prompts: list[tuple[str, str | None]] = []
        self.antwoord = VOORSTEL_JSON if antwoord is None else antwoord
        self.storing = storing

    async def generate_definition(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        model: str | None = None,
        system_prompt: str | None = None,
        timeout_seconds: int = 30,
        task_type: str | None = None,
    ) -> AIGenerationResult:
        self.calls += 1
        self.prompts.append((prompt, system_prompt))
        if self.storing is not None:
            raise self.storing
        tekst = (
            self.antwoord
            if isinstance(self.antwoord, str)
            else json.dumps(self.antwoord)
        )
        return AIGenerationResult(
            text=tekst, model="fake-voorsteller", tokens_used=0, generation_time=0.0
        )


def geen_bron_uitzondering_marker(
    begrip: str,
    tekst: str,
    contexten: dict[str, list[str]],
    *,
    actor: str,
    version_number: int = 1,
    peildatum: str | None = None,
) -> dict[str, Any]:
    """De opgeslagen CON-02-marker voor een gedocumenteerde uitzondering
    "geen passende bron" (bevroren platte vorm), gebonden aan de kandidaat
    zoals D hem opslaat (record zonder bronbewijs ⇒ lege bronset).

    Voor testfixtures die een record zonder bronnen willen kunnen vaststellen
    (DEF-622-ketens): de uitzondering is echt (actor, motivering, zoeken,
    acceptatie, vingerafdruk) en wordt bij aanmaak in `validation_issues`
    gezaaid — geen versiebump, dus de bestaande versiegevoelige asserties
    blijven gelden. Wijzigt tekst/context, dan vervalt zij (vingerafdruk).
    """
    from database.models import SOURCE_REVIEW_CODE

    return {
        "code": SOURCE_REVIEW_CODE,
        "rule_id": "CON-02",
        "severity": "info",
        "source_review": {
            "type": "no_appropriate_source",
            "accepted": True,
            "actor": actor,
            "rationale": "Organisatie-eigen term zonder authentieke of gezaghebbende bron.",
            "version_number": version_number,
            "fingerprint": bereken_bronvingerafdruk(
                begrip, tekst, contexten, [], peildatum=peildatum
            ),
            "reviewed_at": "2026-09-15T12:00:00+00:00",
            "search": {
                "queries": [f"{begrip} definitie"],
                "consulted": ["wetten.overheid.nl", "intern begrippenregister"],
                "conclusion": "Geen passende authentieke bron gevonden.",
            },
        },
    }
