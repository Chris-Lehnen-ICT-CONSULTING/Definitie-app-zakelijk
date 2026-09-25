"""INT-01 (DEF-770): de opgeslagen deeluitkomst, gebonden aan kern en versie.

De persistentielaag bewaart bij iedere schrijfactie die de definitiekern zet
(nieuw record, update, bronvoorsteltoepassing) de INT-01-deeluitkomst van
exact die kern in de generatieregistratie (`generation_prompt_data`, JSON —
geen nieuwe kolom). INT-01 is deterministisch: dezelfde functie als de
validatie (`domain.int01.zinsgrenzen`) levert dezelfde onderdelen.

Wat bewaard wordt: status (`fail`, `review_required` of `not_evaluated`, nooit
`pass`), de melding en alle onderdelen (zinsstructuur of grenzen met passage
en positie, compactheid en begrijpelijkheid afzonderlijk open), plus de
binding: sha256 van de beoordeelde kern, de recordversie waarop is beoordeeld
en de contractversie. Bij lezen geldt de uitkomst alleen als de huidige kern
dezelfde vingerafdruk heeft; anders is zij historisch en niet toegepast.
Een gewijzigde kern krijgt een nieuwe uitkomst; de vorige gaat naar een
append-only historie. Dit is geen menselijk oordeel en geen vaststel- of
exportpoort.
"""

from __future__ import annotations

import hashlib
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from domain.int01.zinsgrenzen import (
    CONTRACTVERSIE,
    melding_meerdere_zinnen,
    open_melding,
    regeluitkomst,
    segmenteer,
)

__all__ = [
    "INT01_BEOORDELING_FIELD",
    "INT01_BEOORDELING_HISTORY_KEY",
    "INT01_OWNED_KEYS",
    "OPSLAGSCHEMA",
    "bouw_beoordeling",
    "exportregels",
    "lees_beoordeling",
    "met_nieuwe_beoordeling",
    "niet_toepasbaar_detail",
    "tekstvingerafdruk",
    "weergavedetail",
]

INT01_BEOORDELING_FIELD = "int01_beoordeling"
INT01_BEOORDELING_HISTORY_KEY = "int01_beoordeling_history"
#: Sleutels die uitsluitend de persistentielaag schrijft; een ruwe
#: registratie-aanlevering kan ze niet overschrijven of wissen.
INT01_OWNED_KEYS: tuple[str, ...] = (
    INT01_BEOORDELING_FIELD,
    INT01_BEOORDELING_HISTORY_KEY,
)
OPSLAGSCHEMA = "def770-int01-opslag/1"

_STATUSLABEL = {
    "pass": "voldoet",
    "fail": "voldoet niet",
    "review_required": "nog te beoordelen",
    "not_evaluated": "niet beoordeeld",
}


def tekstvingerafdruk(kern: str) -> str:
    """sha256 van exact de beoordeelde definitiekern (zonder toelichting)."""
    return hashlib.sha256((kern or "").encode("utf-8")).hexdigest()


def bouw_beoordeling(kern: str, version_number: int | None) -> dict[str, Any]:
    """De opslagvorm van de INT-01-deeluitkomst voor deze kern en versie."""
    basis: dict[str, Any] = {
        "schema": OPSLAGSCHEMA,
        "rule_id": "INT-01",
        "contract_version": CONTRACTVERSIE,
        "binding": {
            "tekst_sha256": tekstvingerafdruk(kern),
            "version_number": version_number,
        },
        "assessed_at": datetime.now(UTC).isoformat(),
        "score": None,
    }
    seg = segmenteer(kern)
    if seg is None:
        return {
            **basis,
            "status": "not_evaluated",
            "reason": "Geen definitietekst; INT-01 niet beoordeelbaar.",
            "parts": [],
        }
    detail = regeluitkomst(seg)
    reden = melding_meerdere_zinnen(seg) if seg.zekere_grenzen else open_melding(seg)
    return {
        **basis,
        "status": detail["status"],
        "reason": reden,
        "parts": detail["parts"],
    }


def met_nieuwe_beoordeling(
    registratie: dict[str, Any], kern: str, version_number: int | None
) -> dict[str, Any]:
    """Registratie met een verse beoordeling; de vorige gaat naar de historie.

    Gelijke kern als de opgeslagen, geldige beoordeling = ongewijzigd (geen
    nieuwe historie-regel voor een schrijfactie die de tekst niet raakt).
    """
    registratie = dict(registratie)
    vorige = registratie.get(INT01_BEOORDELING_FIELD)
    if isinstance(vorige, dict) and _bindt_aan(vorige, kern):
        return registratie
    historie = registratie.get(INT01_BEOORDELING_HISTORY_KEY)
    historie = list(historie) if isinstance(historie, list) else []
    if isinstance(vorige, dict):
        historie.append(
            {
                "assessment": deepcopy(vorige),
                "superseded_at": datetime.now(UTC).isoformat(),
                "superseded_on_version": version_number,
            }
        )
    registratie[INT01_BEOORDELING_FIELD] = bouw_beoordeling(kern, version_number)
    registratie[INT01_BEOORDELING_HISTORY_KEY] = historie
    return registratie


def _bindt_aan(beoordeling: dict[str, Any], kern: str) -> bool:
    binding = beoordeling.get("binding")
    return (
        isinstance(binding, dict)
        and binding.get("tekst_sha256") == tekstvingerafdruk(kern)
        and beoordeling.get("contract_version") == CONTRACTVERSIE
    )


def lees_beoordeling(beoordeling: Any, kern: str) -> dict[str, Any] | None:
    """De opgeslagen uitkomst met `applied` en, zo niet, de reden.

    Alleen een uitkomst die aan exact de huidige kern en contractversie bindt
    geldt (`applied: True`). Een andere kern of versie maakt haar historisch:
    zij blijft leesbaar maar wordt nooit als actuele uitkomst gepresenteerd.
    """
    if not isinstance(beoordeling, dict):
        return None
    uit = deepcopy(beoordeling)
    ruwe_binding = uit.get("binding")
    binding = ruwe_binding if isinstance(ruwe_binding, dict) else {}
    if binding.get("tekst_sha256") != tekstvingerafdruk(kern):
        uit["applied"] = False
        uit["applied_reason"] = (
            "De definitietekst is na deze INT-01-beoordeling gewijzigd; deze "
            "uitkomst geldt niet voor de huidige tekst. Opnieuw toetsen."
        )
    elif uit.get("contract_version") != CONTRACTVERSIE:
        uit["applied"] = False
        uit["applied_reason"] = (
            "Beoordeeld onder een andere INT-01-contractversie; opnieuw toetsen."
        )
    else:
        uit["applied"] = True
        uit["applied_reason"] = None
    return uit


def niet_toepasbaar_detail(reden: str) -> dict[str, Any]:
    """Regeluitkomst voor weergave als een eerdere INT-01-uitkomst niet bij de
    actuele tekst hoort: open, zonder de oude onderdelen (geen oude pass)."""
    return {
        "status": "review_required",
        "score": None,
        "contract_version": CONTRACTVERSIE,
        "fingerprint": None,
        "parts": [
            {
                "id": "tekstbinding",
                "status": "review_required",
                "evidence": None,
                "context_value": None,
                "field": "definitie",
                "position": None,
                "reason": reden,
                "action": "Toets de huidige tekst opnieuw.",
            }
        ],
        "review": None,
    }


def weergavedetail(beoordeling: Any, kern: str) -> dict[str, Any]:
    """De INT-01-regeluitkomst om te tonen bij de actuele tekst `kern`.

    Bindt de opgeslagen uitkomst aan deze tekst (vingerafdruk en
    contractversie): dan haar eigen status en onderdelen; anders zichtbaar
    niet toepasbaar; zonder opgeslagen uitkomst zichtbaar niet beoordeeld.
    """
    gelezen = lees_beoordeling(beoordeling, kern)
    if gelezen is None:
        return niet_toepasbaar_detail(
            "INT-01: geen opgeslagen uitkomst voor deze definitie — niet "
            "beoordeeld. Toets de tekst."
        )
    if not gelezen.get("applied"):
        return niet_toepasbaar_detail(f"INT-01: {gelezen.get('applied_reason')}")
    return {
        "status": gelezen.get("status"),
        "score": None,
        "contract_version": gelezen.get("contract_version"),
        "fingerprint": None,
        "parts": gelezen.get("parts") or [],
        "review": None,
    }


def exportregels(gelezen: dict[str, Any] | None) -> list[str]:
    """Leesbare regels voor de tekstexport; leeg zonder opgeslagen uitkomst."""
    if not gelezen:
        return []
    status = _STATUSLABEL.get(str(gelezen.get("status")), str(gelezen.get("status")))
    binding = gelezen.get("binding") or {}
    kop = (
        f"INT-01 — {status} (geen cijfer; beoordeeld op versie "
        f"{binding.get('version_number')})"
    )
    if not gelezen.get("applied"):
        kop += f" — niet toegepast: {gelezen.get('applied_reason')}"
    regels = [kop, f"  {gelezen.get('reason') or ''}".rstrip()]
    for deel in gelezen.get("parts") or []:
        if not isinstance(deel, dict):
            continue
        label = _STATUSLABEL.get(str(deel.get("status")), str(deel.get("status")))
        passage = f" · passage: “{deel['evidence']}”" if deel.get("evidence") else ""
        regels.append(f"  - {deel.get('id')}: {label}{passage} — {deel.get('reason')}")
    return regels
