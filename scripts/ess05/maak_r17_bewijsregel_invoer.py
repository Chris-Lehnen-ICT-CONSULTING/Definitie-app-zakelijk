"""DEF-768 R17 — invoer van de gerichte echte proef bewijsregels (A/B/C).

Opdracht Chris 28-09 ("go?", `logs/def768/ronde17-gebruikersopdracht-v1.json`),
startmandaat `logs/def768/ronde17-startmandaat-v1.md` en het budgetbesluit
`logs/def768/ronde17-bewijsregels-budgetbesluit-v1.json`: dezelfde drie
gevallen als R16, nu op de herstelde bewijsregels (`ess05-bewijsregels/5`,
interpretatie-prompt /3; `docs/technisch/ess05-bewijsregels-contract-v5.md`).

De gevalinhoud komt exact uit de gepinde R16-invoer: per item blijven id,
variant, label, geval, gevalhash, materiaalhashes, buren, onvolledig-markers,
verwachting en herkomst gelijk. Alleen het contract en de prompthash (de
payload van de huidige interpretatieprompt) zijn nieuw berekend; een verschil
in een ander veld is een makerfout. Daardoor blijft de inhoudelijke oracle
(`logs/def768/bewijsregels-oracle-result-v1.md`) van toepassing zonder nieuw
oracleonderzoek.

    .venv/bin/python scripts/ess05/maak_r17_bewijsregel_invoer.py [--doel P]

Het doel wordt nooit overschreven; alle bronnen worden alleen gelezen.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import maak_r10_verificatie_invoer as mk10
import maak_r16_bewijsregel_invoer as mk16
from maak_r10_verificatie_invoer import MakerfoutError

__all__ = ["GEVALVELDEN", "MakerfoutError", "maak_bewijsregel_invoer", "main"]

LOGS = PROJECT_ROOT / "logs" / "def768"
R16_INVOER = mk16.DOEL
R16_INVOER_SHA256 = "11730986c6e5faf4afedb811426fae26856c234bb96315efb3bb9b3b30111cd2"
ORACLE = LOGS / "bewijsregels-oracle-result-v1.md"
ORACLE_SHA256 = "f09d29407a3a6146f6d052ae2cbc516f935ddde652c5aea0497a763dbed6833d"
BRONNEN = {
    "gebruikersopdracht": (
        LOGS / "ronde17-gebruikersopdracht-v1.json",
        "da4094165955660ffb44cb3a59df01370455e7f3999e93f5bd428c0c75204230",
    ),
    "startmandaat": (
        LOGS / "ronde17-startmandaat-v1.md",
        "c126641444d41a18431f2572a141debba7039f10f659b90e990011056c9f9842",
    ),
    "implementatieopdracht": (
        LOGS / "ronde17-implementatie-opdracht-v1.md",
        "68b28bf374c7309aef761b3bc7997573ba4d0d5ead1f1cd6b275159954c3a6e9",
    ),
    "budgetbesluit": (
        LOGS / "ronde17-bewijsregels-budgetbesluit-v1.json",
        "1f825a6daab976b5e4a1a41631a35798fe49ce6a293856a0a456e8e0c0fcfeda",
    ),
}
DOEL = (
    PROJECT_ROOT / "reports" / "DEF-768-AI-20260928-R17" / "bewijsregel-invoer-v1.json"
)
#: Velden die exact uit de R16-invoer komen (alles behalve de prompthash).
GEVALVELDEN = (
    "id",
    "variant",
    "synthetisch",
    "label",
    "geval",
    "geval_sha256",
    "materiaal_sha256",
    "buren",
    "onvolledig",
    "verwacht",
    "herkomst",
)


def _item(oud: dict[str, Any]) -> dict[str, Any]:
    """Het R16-item opnieuw opgebouwd op de huidige code; alleen de prompthash mag wijzigen."""
    nieuw = mk16._item(
        oud["id"],
        oud["geval"],
        variant=oud["variant"],
        synthetisch=oud["synthetisch"],
        onvolledig=oud["onvolledig"],
        verwacht=oud["verwacht"],
        herkomst=oud["herkomst"],
    )
    if list(nieuw) != list(oud):
        msg = f"{oud['id']}: andere velden dan de R16-invoer: {list(nieuw)}"
        raise MakerfoutError(msg)
    afwijkend = [k for k in GEVALVELDEN if nieuw[k] != oud[k]]
    if afwijkend:
        msg = f"{oud['id']}: gevalinhoud wijkt af van de R16-invoer: {afwijkend}"
        raise MakerfoutError(msg)
    return nieuw


def maak_bewijsregel_invoer() -> dict[str, Any]:
    """A/B/C exact uit de gepinde R16-invoer, gebonden aan het huidige contract."""
    from services.validation.ess05_bewijsregel_service import Ess05BewijsregelService

    bronnen = {}
    for naam, (pad, sha) in BRONNEN.items():
        mk10._gepind(pad, sha, naam)
        bronnen[naam] = {"pad": mk10._rel(pad), "sha256": sha}
    mk10._gepind(ORACLE, ORACLE_SHA256, "oracle")
    r16 = json.loads(mk10._gepind(R16_INVOER, R16_INVOER_SHA256, "R16-invoer"))
    if r16.get("schema") != mk16.INVOERSCHEMA:
        msg = f"R16-invoer heeft niet het schema {mk16.INVOERSCHEMA}"
        raise MakerfoutError(msg)
    return {
        "schema": mk16.INVOERSCHEMA,
        "status": (
            "vooraf vastgelegd vóór elke R17-aanroep; gevalinhoud, markers en "
            "verwachtingen exact uit de R16-invoer; B en C zijn "
            f"{mk16.LABEL}; verwachtingen buiten de modelpayload"
        ),
        "contract": Ess05BewijsregelService.contractidentiteit(),
        "herkomst": {
            "bronnen": bronnen,
            "gevallen": {
                "pad": mk10._rel(R16_INVOER),
                "sha256": R16_INVOER_SHA256,
                "overgenomen": list(GEVALVELDEN),
                "nieuw": ["contract", "prompt_sha256"],
            },
            "oracle": {
                "pad": mk10._rel(ORACLE),
                "sha256": ORACLE_SHA256,
                "hergebruik": (
                    "gevalinhoud en onvolledig-markers exact gelijk aan R16; geen "
                    "nieuw oracleonderzoek"
                ),
            },
            "regels": "scripts/ess05/maak_r17_bewijsregel_invoer.py (moduledocstring)",
            "contractnotitie": "docs/technisch/ess05-bewijsregels-contract-v5.md",
            "auteur": mk16.AUTEUR,
        },
        "items": [_item(item) for item in r16["items"]],
    }


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--doel", type=Path, default=DOEL)
    args = p.parse_args(argv)
    invoer = maak_bewijsregel_invoer()
    mk16._schrijf(args.doel, json.dumps(invoer, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
