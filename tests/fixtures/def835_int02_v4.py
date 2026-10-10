"""Bouwstenen voor INT-02-modeluitvoer onder contract def835-int02-assessment/4.

DEF-835, besluit 16 (bronfuncties). Geen model, geen netwerk en geen
goldset-inhoud: de helpers vullen per passage een `kernvorm` en per grondbron
van de invoer precies één bronfunctie in, in de vaste volgorde van
`domain.int02.contract.grondbronnen`. Wat niet expliciet is opgegeven, zwijgt
(`not_addressed`, citaat null).

`respons_voor_status` levert de kleinste geldige uitvoer waaruit de dienst de
gevraagde status afleidt; zo kunnen dienst-, wrapper- en runnertests een
status kiezen zonder de beslisregel na te bootsen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from domain.int02 import contract

ZWIJGEND: tuple[str, None] = ("not_addressed", None)
VRAAG = "Bepaalt deze passage een kenmerk van het begrip?"


def _invoer(invoer: Any) -> Any:
    if isinstance(invoer, Mapping):
        return contract.maak_invoer(**invoer)
    return invoer


def grondbronnen(invoer: Any) -> tuple[str, ...]:
    return tuple(contract.grondbronnen(_invoer(invoer)))


def bronfuncties(
    invoer: Any, functies: Mapping[str, tuple[str, str | None]] | None = None
) -> list[dict[str, Any]]:
    """Eén bronfunctie per grondbron; onbekende sleutels zijn een testfout."""
    functies = dict(functies or {})
    sleutels = grondbronnen(invoer)
    onbekend = set(functies) - set(sleutels)
    if onbekend:
        msg = f"geen grondbron van deze invoer: {sorted(onbekend)}"
        raise ValueError(msg)
    return [
        {
            "bron": sleutel,
            "function": functies.get(sleutel, ZWIJGEND)[0],
            "quote": functies.get(sleutel, ZWIJGEND)[1],
        }
        for sleutel in sleutels
    ]


def passage(
    invoer: Any,
    quote: str,
    kernvorm: str,
    functies: Mapping[str, tuple[str, str | None]] | None = None,
) -> dict[str, Any]:
    return {
        "quote": quote,
        "kernvorm": kernvorm,
        "bronfuncties": bronfuncties(invoer, functies),
    }


def uitvoer(
    passages: list[dict[str, Any]],
    verdict: str,
    *,
    reason: str = "Synthetische onderbouwing.",
    question: str | None = None,
    uncertainty: str | None = None,
    coverage: str | None = None,
    scope_reason: str | None = None,
) -> dict[str, Any]:
    """Modeluitvoer in schemavolgorde; het eigen verdict staat als laatste."""
    if verdict == "insufficient_information":
        question = question if question is not None else VRAAG
        uncertainty = uncertainty or "decisive"
    if verdict == "not_applicable":
        coverage = coverage or "none"
    return {
        "passages": passages,
        "reason": reason,
        "question": question,
        "uncertainty": uncertainty or "none",
        "coverage": coverage or "complete",
        "scope_reason": scope_reason,
        "verdict": verdict,
    }


#: Kernvorm bij een /3-functie met de kern als grond.
_KERNVORM_BIJ_FUNCTIE = {
    "actor_prescription": "instruction",
    "discretionary_decision_rule": "discretion_form",
    "criterion": "no_act",
    "derivation": "no_act",
    "unclear": "descriptive_act",
}


def naar_v4(invoer: Any, respons: Any) -> Any:
    """Een /3-modelrespons (één functie en grond per passage) in /4-vorm.

    Voor bestaande fixtures (`def835_int02_ontwerpgevallen.json` blijft
    ongewijzigd; het is manifestinvoer). Grond in de kern: de kernvorm volgt
    de functie (`unclear` laat bovendien de eerste grondbron open); grond in
    een bron: beschrijvende kern en die bron draagt functie en citaat. Geen
    dict: ongewijzigd terug (ongeldige uitvoer blijft ongeldig).
    """
    if not isinstance(respons, Mapping):
        return respons
    invoer = _invoer(invoer)
    sleutel_bij = {
        (veld, ref): sleutel
        for sleutel, (veld, ref, _) in contract._grondbronmap(invoer).items()
    }
    passages = []
    for p in respons["passages"]:
        ground, functie = p["ground"], p["function"]
        if ground["field"] == "kern":
            kernvorm = _KERNVORM_BIJ_FUNCTIE[functie]
            functies = {}
            if functie == "unclear":
                functies = {grondbronnen(invoer)[0]: ("unclear", None)}
        else:
            kernvorm = "descriptive_act"
            bron = sleutel_bij[(ground["field"], ground["ref"])]
            functies = {bron: (functie, ground["quote"])}
        passages.append(passage(invoer, p["quote"], kernvorm, functies))
    return {
        "passages": passages,
        "reason": respons["reason"],
        "question": respons["question"],
        "uncertainty": respons["uncertainty"],
        "coverage": respons["coverage"],
        "scope_reason": respons["scope_reason"],
        "verdict": respons["verdict"],
    }


#: Het eigen modelverdict bij elke afgeleide status (zonder omzetting).
VERDICT_BIJ_STATUS = {
    "pass": "pass",
    "fail": "fail",
    "review_required": "insufficient_information",
}


def respons_voor_status(
    invoer: Any, status: str, *, verdict: str | None = None
) -> dict[str, Any]:
    """Kleinste geldige /4-uitvoer waaruit de dienst `status` afleidt.

    - fail: de hele kern als zelfstandig voorschrift (`instruction`, stap 1);
    - pass: de hele kern zonder handeling (`no_act`), alle grondbronnen zwijgen;
    - review_required: beschrijvende handeling, de eerste grondbron laat de
      functie open (`unclear`, zonder citaat; `bronnen_open`).
    `verdict` overschrijft het eigen modelverdict (voor omzettingstests).
    """
    invoer = _invoer(invoer)
    kern = invoer.kern
    if status == "fail":
        passages = [passage(invoer, kern, "instruction")]
    elif status == "pass":
        passages = [passage(invoer, kern, "no_act")]
    elif status == "review_required":
        eerste = grondbronnen(invoer)[0]
        passages = [
            passage(invoer, kern, "descriptive_act", {eerste: ("unclear", None)})
        ]
    else:
        msg = f"onbekende status: {status}"
        raise ValueError(msg)
    return uitvoer(passages, verdict or VERDICT_BIJ_STATUS[status])
