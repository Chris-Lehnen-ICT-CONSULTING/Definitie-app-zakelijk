"""Deterministische stand-ins voor de ESS-05-AI-grens (DEF-768, contract `/2`).

Geen model, geen netwerk, geen productie-DB. De `/2`-fixtures hier zijn
**nieuw ontworpen** testmateriaal (ADR-003); oorspronkelijke R1–R7-antwoorden
blijven ongewijzigd in hun eigen bewijsmappen.

- `concept_uit_spec` zet een eenvoudige testspecificatie (per buur label,
  citaat, ontbrekend kenmerk, reden; voorstellen; vraag) om in een gesloten
  `/2`-conceptoordeel met exacte bewijsplaatsen;
- `verificatie_voor` levert een volledige verificatie (standaard alles
  `supported`; per item overschrijfbaar);
- `bouw_document` maakt een store-ready, aan exact deze invoer en binding
  gebonden beoordelingsdocument;
- `bouw_ess05_beoordeling` doet dat per scenario `pass` / `fail` / `lacks` /
  `open` / `voorstel` / `error` / `semantic` / `unavailable`;
- `FakeEss05Assessor` boots de `Ess05AssessmentService`-grens na.

Een stub die correct weigert of vrijgeeft bewijst alleen het ketengedrag,
niet het detectievermogen van een echte verifier.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from html import unescape
from typing import Any

from domain.ess03.contract import Intentie
from domain.ess05.bewijs import (
    ANTWOORDSCHEMA,
    CONCEPTSCHEMA,
    VERIFICATIESCHEMA,
    Ess05Concept,
    verplichte_controles,
)
from domain.ess05.contract import (
    CONTRACTVERSIE,
    FASE_VERIFICATIE,
    FOUT_SEMANTISCH,
    Ess05Beoordelingsbinding,
    afleidingsbinding,
    beoordeling_niet_beschikbaar,
    beoordeling_technische_fout,
    beoordelingsmateriaal,
    bereken_ess05_vingerafdruk,
    bindingscontext,
    materiaalhashes,
    normaliseer_buren,
    pas_verificatie_toe,
    valideer_concept,
)

PROMPT_VERSION = "ess05-assess/2"
VERIFICATION_PROMPT_VERSION = "ess05-verify/2"
NORM_SHA256 = "e" * 64
PROVIDER = "fake"
MODEL = "fake-ess05-model"

BINDING = Ess05Beoordelingsbinding(
    prompt_version=PROMPT_VERSION,
    verification_prompt_version=VERIFICATION_PROMPT_VERSION,
    norm_sha256=NORM_SHA256,
    provider=PROVIDER,
    model=MODEL,
    verification_provider=PROVIDER,
    verification_model=MODEL,
)


def _sha(tekst: str) -> str:
    return hashlib.sha256(str(tekst).encode("utf-8")).hexdigest()


def _plaats(id_: str, materiaal: Mapping[str, str], locatie: str, citaat: str) -> dict:
    """Een bewijsplaats; een niet gevonden citaat krijgt bewust een foute plaats."""
    tekst = materiaal.get(locatie, "")
    start = tekst.find(citaat)
    start = max(start, 0)
    return {
        "id": id_,
        "material_id": locatie,
        "material_sha256": _sha(tekst),
        "start": start,
        "end": start + len(citaat),
        "quote": citaat,
    }


def _claim(id_: str, rol: str, tekst: str, bewijs: Iterable[str] = ()) -> dict:
    return {
        "id": id_,
        "role": rol,
        "text": tekst,
        "evidence": list(bewijs),
        "premises": [],
    }


def _buurdeel(
    index: int, item: Mapping[str, Any], materiaal: Mapping[str, str], concept: dict
) -> dict:
    citaat = item.get("distinguishing_feature_quote")
    bewijs = "E-kern"
    if citaat:
        bewijs = f"E-b{index}"
        concept["evidence"].append(_plaats(bewijs, materiaal, "definition", citaat))
    concept["claims"].append(
        _claim(f"C-b{index}", "material", item.get("reason") or "Reden.", [bewijs])
    )
    ontbrekend = None
    if item.get("missing_feature"):
        ontbrekend = f"C-m{index}"
        concept["claims"].append(
            _claim(ontbrekend, "material", item["missing_feature"], ["E-kern"])
        )
    onzeker = None
    if item.get("uncertainty"):
        onzeker = f"C-u{index}"
        concept["claims"].append(
            _claim(onzeker, "absence_in_supplied_material", item["uncertainty"])
        )
    return {
        "neighbour_id": item["neighbour_id"],
        "distinction": item["distinction"],
        "feature_evidence": bewijs if citaat else None,
        "reason_claims": [f"C-b{index}"],
        "missing_feature_claim": ontbrekend,
        "uncertainty_claim": onzeker,
    }


def _voorstel(
    index: int, item: Mapping[str, Any], materiaal: Mapping[str, str], concept: dict
) -> dict:
    bron, citaat = item.get("source_id"), item.get("quote")
    bewijs = None
    if bron and citaat:
        bewijs = f"E-p{index}"
        concept["evidence"].append(_plaats(bewijs, materiaal, f"source:{bron}", citaat))
        concept["claims"].append(
            _claim(f"C-p{index}", "material", item.get("reason") or "r", [bewijs])
        )
    else:
        concept["claims"].append(
            _claim(
                f"C-p{index}",
                "absence_in_supplied_material",
                item.get("reason") or "r",
            )
        )
    return {
        "id": f"P{index}",
        "term": item["term"],
        "source_evidence": bewijs,
        "reason_claims": [f"C-p{index}"],
    }


def concept_uit_spec(spec: Mapping[str, Any], materiaal: Mapping[str, str]) -> dict:
    """Een gesloten `/2`-concept uit een eenvoudige testspecificatie.

    `spec`: `lacks_differentia`, `reason`, `neighbours` (neighbour_id,
    distinction, distinguishing_feature_quote, missing_feature, reason,
    uncertainty), `proposed_neighbours` (term, source_id, quote, reason),
    `question`; optioneel `core_feature_quotes`.
    """
    kern = materiaal["definition"]
    concept: dict[str, Any] = {
        "schema_version": CONCEPTSCHEMA,
        "genus_evidence": None,
        "core_features": [],
        "evidence": [_plaats("E-kern", materiaal, "definition", kern)],
        "claims": [
            _claim("C-reden", "material", spec.get("reason") or "Reden.", ["E-kern"])
        ],
        "reason_claims": ["C-reden"],
        "neighbours": [],
        "proposals": [],
        "question": None,
    }
    concept["neighbours"] = [
        _buurdeel(i, item, materiaal, concept)
        for i, item in enumerate(spec.get("neighbours") or [])
    ]
    concept["proposals"] = [
        _voorstel(i, item, materiaal, concept)
        for i, item in enumerate(spec.get("proposed_neighbours") or [])
    ]
    if not spec.get("lacks_differentia"):
        citaten = list(spec.get("core_feature_quotes") or [])
        if not citaten:
            citaten = [
                n["distinguishing_feature_quote"]
                for n in spec.get("neighbours") or []
                if n.get("distinguishing_feature_quote")
            ][:1] or [kern]
        for i, citaat in enumerate(citaten):
            concept["evidence"].append(
                _plaats(f"E-f{i}", materiaal, "definition", citaat)
            )
            concept["core_features"].append({"id": f"F{i}", "evidence": f"E-f{i}"})
    if spec.get("question"):
        concept["question"] = {"text": spec["question"], "claims": []}
    return concept


def antwoord_uit_concept(concept: Mapping[str, Any]) -> dict:
    """Hetzelfde oordeel als modelantwoord (`ANTWOORDSCHEMA`): bewijsplaatsen
    met materiaal-id, hash en citaat, zonder posities (die leidt de app af)."""
    antwoord = deepcopy(dict(concept))
    antwoord["schema_version"] = ANTWOORDSCHEMA
    antwoord["evidence"] = [
        {k: e[k] for k in ("id", "material_id", "material_sha256", "quote")}
        for e in concept["evidence"]
    ]
    return antwoord


def antwoord_uit_spec(spec: Mapping[str, Any], materiaal: Mapping[str, str]) -> dict:
    """`concept_uit_spec` als modelantwoord (wat een fake provider teruggeeft)."""
    return antwoord_uit_concept(concept_uit_spec(spec, materiaal))


_PLAATS = re.compile(
    r"<plaats id=(\"[^\"]*\"|'[^']*') sha256=\"[0-9a-f]{64}\">(.*?)</plaats>", re.S
)


def materiaal_uit_prompt(prompt: str) -> dict[str, str]:
    """Het gebonden materiaal zoals een model het in de prompt ziet (<materiaal>)."""
    return {
        unescape(m.group(1)[1:-1]): unescape(m.group(2))
        for m in _PLAATS.finditer(prompt)
    }


def is_verificatievraag(prompt: str) -> bool:
    return "<conceptoordeel candidate_hash=" in prompt


def verificatie_voor(
    concept: Mapping[str, Any],
    *,
    uitkomsten: Mapping[str, str] | None = None,
    candidate_hash: str | None = None,
) -> dict:
    """Een volledige verificatie van exact dit concept (standaard alles supported)."""
    object_ = Ess05Concept(deepcopy(dict(concept)))
    uitkomsten = uitkomsten or {}
    return {
        "schema_version": VERIFICATIESCHEMA,
        "candidate_hash": candidate_hash or object_.hash,
        "checks": [
            {
                "item": item,
                "outcome": uitkomsten.get(item, "supported"),
                "finding": f"Synthetische bevinding voor {item}.",
            }
            for item in verplichte_controles(object_)
        ],
    }


def _attributie(model: str | None, taak: str) -> dict[str, Any]:
    return {
        "provider": PROVIDER,
        "model": model,
        "task_type": taak,
        "cached": False,
        "tokens_used": 7,
    }


def bouw_document(
    begrip: str,
    tekst: str,
    contexten: Mapping[str, Any] | None,
    bronnen_ruw: Any = None,
    *,
    buren: Any = None,
    spec: Mapping[str, Any] | None = None,
    concept: Mapping[str, Any] | None = None,
    verificatie: Callable[[dict], dict] | None = None,
    intentie: Intentie | None = None,
    uitgesloten_termen: Iterable[str] = (),
    binding: Ess05Beoordelingsbinding = BINDING,
) -> dict[str, Any]:
    """Een store-ready `/2`-document, gebonden aan exact deze invoer en binding.

    Zonder eigen `verificatie` wordt het concept volledig goedgekeurd en moet
    het de vaste controles doorstaan; het toegepaste oordeel is dan de vaste
    weergave (`judgment`).
    """
    actief = normaliseer_buren(buren)
    uitgesloten = tuple(uitgesloten_termen)
    materiaal = beoordelingsmateriaal(
        begrip, tekst, bronnen_ruw or [], actief, contexten=contexten, intentie=intentie
    )
    ruw = (
        dict(concept)
        if concept is not None
        else concept_uit_spec(spec or {}, materiaal)
    )
    verificatie_ruw = (verificatie or verificatie_voor)(ruw)
    oordeel = None
    rejected: list[dict[str, Any]] = []
    gevalideerd, fouten = valideer_concept(ruw, materiaal, actief)
    if verificatie is None:
        assert gevalideerd is not None, fouten
    if gevalideerd is not None:
        oordeel, _, rejected = pas_verificatie_toe(
            gevalideerd,
            verificatie_ruw,
            actief,
            begrip=begrip,
            uitgesloten_termen=uitgesloten,
        )
    hashes = materiaalhashes(materiaal)
    # Zoals de dienst: de ongewijzigde ruwe respons (antwoord zonder posities)
    # en de binding van het daaruit afgeleide concept.
    ruwe_respons = json.dumps(antwoord_uit_concept(ruw), ensure_ascii=False)
    ruwe_hash = _sha(ruwe_respons)
    return {
        "contract_version": CONTRACTVERSIE,
        "prompt_version": binding.prompt_version,
        "verification_prompt_version": binding.verification_prompt_version,
        "schema_version": binding.schema_version,
        "verification_schema_version": binding.verification_schema_version,
        "renderer_version": binding.renderer_version,
        "norm_sha256": binding.norm_sha256,
        "fingerprint": bereken_ess05_vingerafdruk(
            begrip, tekst, contexten, bronnen_ruw or [], intentie=intentie, buren=actief
        ),
        "status": "assessed",
        "error": None,
        "assessed_at": "2026-09-25T09:00:00+00:00",
        "verified_at": "2026-09-25T09:00:01+00:00",
        "attribution": _attributie(binding.model, "validation"),
        "verification_attribution": _attributie(
            binding.verification_model, "ess05_verification"
        ),
        "input": {"materiaal": hashes, **bindingscontext(actief, uitgesloten)},
        "verification_input": {
            "materiaal": hashes,
            "candidate_hash": Ess05Concept(deepcopy(ruw)).hash,
        },
        "concept": deepcopy(ruw),
        "verification": verificatie_ruw,
        "judgment": oordeel.als_dict() if oordeel is not None else None,
        "rejected": rejected,
        "raw_response": ruwe_respons,
        "raw_response_sha256": ruwe_hash,
        "concept_derivation": afleidingsbinding(
            ruwe_hash, Ess05Concept(deepcopy(ruw)), materiaal
        ),
        "verification_raw_response_sha256": "v" * 64,
    }


def _citaat(tekst: str, buurdefinities: list[str]) -> str:
    """Het kortste woordfragment uit de kandidaat dat in geen buurdefinitie staat."""
    woorden = str(tekst or "").split()
    for lengte in range(1, len(woorden) + 1):
        for start in range(len(woorden) - lengte + 1):
            fragment = " ".join(woorden[start : start + lengte])
            if not any(fragment in d for d in buurdefinities):
                return fragment
    return str(tekst)


def _buuroordeel(buur, scenario: str, tekst: str) -> dict[str, Any]:
    onderscheid = {
        "pass": "distinguished",
        "voorstel": "distinguished",
        "semantic": "distinguished",
        "fail": "not_distinguished",
        "lacks": "not_distinguished",
        "open": "unclear",
    }[scenario]
    if buur.definitie is None:
        onderscheid = "unclear"
    return {
        "neighbour_id": buur.id,
        "distinction": onderscheid,
        "distinguishing_feature_quote": (
            _citaat(tekst, [buur.definitie or ""])
            if onderscheid == "distinguished"
            else None
        ),
        "missing_feature": (
            "het synthetisch ontbrekende kenmerk"
            if onderscheid == "not_distinguished"
            else None
        ),
        "reason": f"Synthetisch oordeel {onderscheid}.",
        "uncertainty": None,
    }


def bouw_ess05_beoordeling(
    begrip: str,
    tekst: str,
    contexten: dict[str, Any] | None,
    bronnen_ruw: Any = None,
    *,
    buren: Any = None,
    intentie: Intentie | None = None,
    scenario: str = "pass",
    model: str | None = MODEL,
    uitgesloten_termen: Iterable[str] = (),
) -> dict[str, Any]:
    """Een contractconforme ESS-05-beoordeling voor exact deze invoer."""
    actief = normaliseer_buren(buren)
    vingerafdruk = bereken_ess05_vingerafdruk(
        begrip, tekst, contexten, bronnen_ruw or [], intentie=intentie, buren=actief
    )
    if scenario == "error":
        return beoordeling_technische_fout(
            vingerafdruk,
            "timeout",
            "synthetische time-out",
            prompt_version=PROMPT_VERSION,
            norm_sha256=NORM_SHA256,
            attribution={
                "provider": PROVIDER,
                "model": model,
                "task_type": "validation",
            },
        )
    if scenario == "semantic":
        return beoordeling_technische_fout(
            vingerafdruk,
            FOUT_SEMANTISCH,
            "semantische verificatie keurde het conceptoordeel niet goed "
            "(claim:C-reden unsupported: synthetische bevinding)",
            prompt_version=PROMPT_VERSION,
            norm_sha256=NORM_SHA256,
            attribution={
                "provider": PROVIDER,
                "model": model,
                "task_type": "validation",
            },
            phase=FASE_VERIFICATIE,
        )
    if scenario == "unavailable":
        return beoordeling_niet_beschikbaar(vingerafdruk, "synthetisch: geen dienst")
    spec = {
        "lacks_differentia": scenario == "lacks",
        "reason": f"Synthetisch totaaloordeel {scenario}.",
        "neighbours": [_buuroordeel(b, scenario, tekst) for b in actief],
        "proposed_neighbours": (
            [
                {
                    "term": "synthetisch voorstel",
                    "source_id": None,
                    "quote": None,
                    "reason": "r",
                }
            ]
            if scenario == "voorstel"
            else []
        ),
        "question": None,
    }
    binding = BINDING
    if model != MODEL:
        binding = Ess05Beoordelingsbinding(
            **{**BINDING.als_dict(), "model": model, "verification_model": model}
        )
    return bouw_document(
        begrip,
        tekst,
        contexten,
        bronnen_ruw,
        buren=list(actief),
        spec=spec,
        intentie=intentie,
        uitgesloten_termen=uitgesloten_termen,
        binding=binding,
    )


class FakeEss05Assessor:
    """De `Ess05AssessmentService`-grens: telt aanroepen, levert per scenario."""

    def __init__(self, *, scenario: str = "pass", fout: Exception | None = None):
        self.scenario = scenario
        self.fout = fout
        self.calls: list[dict[str, Any]] = []
        self.norm_sha256 = NORM_SHA256

    def binding(self) -> Ess05Beoordelingsbinding:
        return BINDING

    async def assess(
        self,
        begrip,
        tekst,
        contexten,
        bronnen_ruw,
        *,
        buren=(),
        intentie=None,
        uitgesloten_termen=(),
        correlation_id=None,
    ):
        from services.validation.ess05_assessment_service import Ess05Assessment

        self.calls.append(
            {
                "begrip": begrip,
                "tekst": tekst,
                "contexten": deepcopy(dict(contexten or {})),
                "bronnen": deepcopy(bronnen_ruw),
                "buren": tuple(buren),
                "intentie": intentie,
                "uitgesloten_termen": tuple(uitgesloten_termen),
                "correlation_id": correlation_id,
            }
        )
        if self.fout is not None:
            raise self.fout
        return Ess05Assessment(
            bouw_ess05_beoordeling(
                begrip,
                tekst,
                contexten,
                bronnen_ruw,
                buren=list(buren),
                intentie=intentie,
                scenario=self.scenario,
                uitgesloten_termen=uitgesloten_termen,
            )
        )
