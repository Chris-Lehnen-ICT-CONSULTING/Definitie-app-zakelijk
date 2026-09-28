"""DEF-768 R18 — invoer van de interpretatieproef R18A (A, C, D, E met orakel).

Plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md`, taak B2,
op bewijsregels v6 (`docs/technisch/ess05-bewijsregels-contract-v6.md`):
per item drie herhalingen van alleen de interpretatiestap (`interpreteer`),
gescoord met `bewijsscorer` tegen een vooraf vastgelegd orakel.

- **A** en **C** — gevalinhoud exact uit de gepinde R17-invoer: variant,
  label, geval, gevalhash, materiaalhashes, buren en onvolledig-markers. Een
  verschil is een makerfout. C blijft SYNTHETISCH, GEEN MODELUITVOER.
- **D** — SYNTHETISCH, GEEN MODELUITVOER: A met de bron uit het plan. De
  kosten staan in een eigen zin per begrip ("Voor uitleen betaalt …", "Voor
  verhuur betaalt …"); de teruggaafzin staat twee keer letterlijk. Toetst
  blind hergebruik van de Uitleen-eenheid, ontkenning en de herhaalde zin.
- **E** — SYNTHETISCH, GEEN MODELUITVOER: A met de bron uit het plan, waarin
  uitleen alleen "bij storing" kosteloos is. Toetst of de voorwaarde behouden
  blijft. Aanvulling op het orakel (`voorwaarde_vereist_voor`): een
  toegestane uitkomst telt alleen als `voorwaarde_behouden` waar is;
  `review_required` alleen met de voorwaarde als M-kenmerk (plan B2), en
  volgens deel C geldt dat voor elke uitkomst van E.

Het orakel gaat nooit naar het model. Binding: de berekende
contractidentiteit (`Ess05BewijsregelService.contractidentiteit()`) en per
item de prompthash van de huidige interpretatieprompt.

    .venv/bin/python scripts/ess05/maak_r18_bewijsregel_invoer.py [--doel P]

Het doel wordt nooit overschreven; alle bronnen worden alleen gelezen.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bewijsscorer as bs
import maak_r10_verificatie_invoer as mk10
import maak_r16_bewijsregel_invoer as mk16
import migreer_r7_naar_v2 as mig
import proefinvoer as pi
from maak_r10_verificatie_invoer import MakerfoutError

__all__ = [
    "INVOERSCHEMA",
    "ORAKELS",
    "MakerfoutError",
    "maak_bewijsregel_invoer",
    "main",
    "vergelijkingsinvoer",
]

INVOERSCHEMA = "def768-ess05-bewijsregel-invoer/2"
LABEL = mk16.LABEL
HERHALINGEN = 3
AUTEUR = "Claude Code CLI-uitvoerder, sessie 1f2d8472-4293-490d-b22f-60e829ec17d8"
PLAN = (
    PROJECT_ROOT
    / "docs"
    / "plans"
    / "2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md"
)
PLAN_SHA256 = "4b7dec58bed0479163c72ccf75d4d3af1df9213deca7ce4a37c1ecb4fb06c0e3"
R17_INVOER = (
    PROJECT_ROOT / "reports" / "DEF-768-AI-20260928-R17" / "bewijsregel-invoer-v1.json"
)
R17_INVOER_SHA256 = "cda6080dd160399cd605487890738ada5bbbfcedb62680cabeca59bf860bfab4"
DOEL = (
    PROJECT_ROOT / "reports" / "DEF-768-AI-20260928-R18" / "bewijsregel-invoer-v1.json"
)
#: Velden die voor A en C exact uit de R17-invoer komen.
R17_VELDEN = (
    "variant",
    "synthetisch",
    "label",
    "geval",
    "geval_sha256",
    "materiaal_sha256",
    "buren",
    "onvolledig",
)
INLEIDING = (
    "Lokale testwerkinstructie van de Servicedesk ICT-middelen, alleen voor deze "
    "beoordelingstest."
)
BRON_D = (
    f"{INLEIDING} Uitleen: de servicedesk stelt apparatuur tijdelijk ter beschikking "
    "aan een medewerker; de medewerker geeft de apparatuur daarna terug. Voor uitleen "
    "betaalt de medewerker niets. Verhuur: de servicedesk stelt apparatuur tijdelijk "
    "ter beschikking aan een medewerker; de medewerker geeft de apparatuur daarna "
    "terug. Voor verhuur betaalt de medewerker een vergoeding."
)
BRON_E = (
    f"{INLEIDING} Uitleen: bij storing stelt de servicedesk apparatuur tijdelijk en "
    "kosteloos ter beschikking aan een medewerker; de medewerker geeft de apparatuur "
    "daarna terug. Verhuur: de servicedesk stelt apparatuur tijdelijk ter beschikking "
    "aan een medewerker; de medewerker geeft de apparatuur daarna terug. Verdere "
    "informatie over verhuur staat niet in deze werkinstructie."
)
_BUUR = bs.BUURBESCHRIJVING
ORAKELS: dict[str, dict[str, Any]] = {
    "A": {
        "kenmerken": {
            "tijdelijk": {
                "doel": {"toestand": ["bevestigd"], "eenheden": ["Uitleen:"]},
                "verhuur": {"toestand": ["bevestigd"], "eenheden": ["Verhuur:", _BUUR]},
            },
            "kosteloos": {
                "doel": {"toestand": ["bevestigd"], "eenheden": ["Uitleen:"]},
                "verhuur": {
                    "toestand": ["onbesproken"],
                    "eenheden": [],
                    "f7": ["ontkend"],
                },
            },
        },
        "dragend": ["kosteloos"],
        "uitkomst": ["review_required"],
    },
    "C": {
        "kenmerken": {
            "tijdelijk": {
                "doel": {"toestand": ["bevestigd"], "eenheden": ["Uitleen:"]},
                "verhuur": {"toestand": ["ontkend"], "eenheden": ["Verhuur:", _BUUR]},
            }
        },
        "dragend": ["tijdelijk"],
        "uitkomst": ["pass"],
    },
    "D": {
        "kenmerken": {
            "kosteloos": {
                "doel": {
                    "toestand": ["bevestigd"],
                    "eenheden": ["Voor uitleen betaalt"],
                },
                "verhuur": {
                    "toestand": ["ontkend"],
                    "eenheden": ["Voor verhuur betaalt", _BUUR],
                },
            }
        },
        "dragend": ["kosteloos"],
        "uitkomst": ["pass"],
    },
    "E": {
        "kenmerken": {},
        "dragend": [],
        "voorwaarde": "storing",
        "uitkomst": ["error/buiten_bereik", "review_required"],
        "voorwaarde_vereist_voor": ["error/buiten_bereik", "review_required"],
        "toelichting": (
            "review_required telt alleen als voorwaarde_behouden waar is (de "
            "voorwaarde als M-kenmerk, plan B2); volgens deel C telt M-d bij E "
            "alleen als juist wanneer voorwaarde_behouden waar is, dus ook "
            "error/buiten_bereik; een E-run zonder behouden voorwaarde is kritiek"
        ),
    },
}
_VARIANTEN = {
    "D": (
        "doel kosteloos in een eigen zin, verhuur betaalt: blind hergebruik van de "
        "Uitleen-eenheid draagt kosteloos niet; teruggaafzin twee keer"
    ),
    "E": (
        "uitleen alleen bij storing kosteloos: de voorwaarde moet behouden blijven "
        "(buiten bereik of als betekeniskenmerk)"
    ),
}


def vergelijkingsinvoer(item: Mapping[str, Any]) -> Any:
    """De `Vergelijkingsinvoer` van een item, zoals de maker hem bouwt."""
    from domain.ess05 import bewijsregels as br

    materiaal, buren, _ = mig.verificatiemateriaal(item["geval"])
    if len(buren) != 1:
        msg = f"{item['id']}: precies één buur vereist"
        raise MakerfoutError(msg)
    return br.Vergelijkingsinvoer(
        term=item["geval"]["begrip"],
        materiaal=materiaal,
        buren=tuple((b.id, b.term) for b in buren),
        onvolledig=frozenset(item["onvolledig"]),
    )


def _controleer_prefixen(naam: str, invoer: Any, orakel: Mapping[str, Any]) -> None:
    """Elk orakelprefix (behalve de buurbeschrijving) raakt precies één eenheid."""
    teksten = [
        invoer.materiaal[r.material_id][r.start : r.end]
        for r in invoer.eenheden().values()
        if not r.material_id.startswith("neighbour:")
    ]
    for per_onderwerp in orakel["kenmerken"].values():
        for verwacht in per_onderwerp.values():
            for prefix in verwacht.get("eenheden", []):
                if prefix == _BUUR:
                    continue
                n = sum(t.startswith(prefix) for t in teksten)
                if n != 1:
                    msg = f"{naam}: orakelprefix {prefix!r} raakt {n} eenheden"
                    raise MakerfoutError(msg)


def _item(
    naam: str,
    geval: Mapping[str, Any],
    *,
    variant: str,
    synthetisch: bool,
    label: str,
    herkomst: Mapping[str, Any],
) -> dict[str, Any]:
    from services.validation.ess05_bewijsregel_service import bouw_interpretatieprompt
    from services.validation.ess05_verification_service import prompthash

    orakel = copy.deepcopy(ORAKELS[naam])
    item: dict[str, Any] = {
        "id": naam,
        "variant": variant,
        "synthetisch": synthetisch,
        "label": label,
        "geval": dict(geval),
        "geval_sha256": pi.sha_json(dict(geval)),
        "materiaal_sha256": {},
        "buren": [],
        "onvolledig": [],
        "prompt_sha256": "",
        "herhalingen": HERHALINGEN,
        "orakel": orakel,
        "herkomst": dict(herkomst),
    }
    invoer = vergelijkingsinvoer(item)
    item["materiaal_sha256"] = {m: mk10._sha(t) for m, t in invoer.materiaal.items()}
    item["buren"] = [list(b) for b in invoer.buren]
    system, user = bouw_interpretatieprompt(invoer)
    item["prompt_sha256"] = prompthash(system, user)
    try:
        bs.controleer_orakel(orakel, invoer)
    except bs.OrakelfoutError as exc:
        msg = f"{naam}: {exc}"
        raise MakerfoutError(msg) from exc
    _controleer_prefixen(naam, invoer, orakel)
    return item


def _uit_r17(oud: Mapping[str, Any], herkomst: Mapping[str, Any]) -> dict[str, Any]:
    """A of C opnieuw opgebouwd; elk verschil in de gevalinhoud is een makerfout."""
    nieuw = _item(
        oud["id"],
        oud["geval"],
        variant=oud["variant"],
        synthetisch=oud["synthetisch"],
        label=oud["label"],
        herkomst={
            **herkomst,
            "item": oud["id"],
            "bewerking": "gevalinhoud ongewijzigd uit de R17-invoer; nieuw zijn "
            "prompthash, herhalingen en orakel",
            "oorspronkelijk": oud["herkomst"],
        },
    )
    afwijkend = [k for k in R17_VELDEN if nieuw[k] != oud[k]]
    if afwijkend:
        msg = f"{oud['id']}: gevalinhoud wijkt af van de R17-invoer: {afwijkend}"
        raise MakerfoutError(msg)
    return nieuw


def _synthetisch(
    naam: str, a: Mapping[str, Any], bron: str, herkomst: Mapping[str, Any]
) -> dict[str, Any]:
    """D of E: R17-A met alleen een andere bronsnippet (plantekst)."""
    geval = copy.deepcopy(dict(a["geval"]))
    geval["id"] = f"R18-{naam}"
    (b,) = geval["bronnen"]
    if not b["snippet"].startswith(INLEIDING + " ") or not bron.startswith(
        INLEIDING + " "
    ):
        msg = f"{naam}: de bron begint niet met de vaste R17-inleiding"
        raise MakerfoutError(msg)
    b["snippet"] = bron
    return _item(
        naam,
        geval,
        variant=_VARIANTEN[naam],
        synthetisch=True,
        label=LABEL,
        herkomst={
            **herkomst,
            "item": "A",
            "label": LABEL,
            "bewerking": f"R17-item A met de bronsnippet van plan B2, item {naam}; "
            "definitie, context, titel en buur (de definitie van A) ongewijzigd",
        },
    )


def maak_bewijsregel_invoer() -> dict[str, Any]:
    """A/C uit de gepinde R17-invoer, D/E synthetisch; gebonden aan het huidige contract."""
    from services.validation.ess05_bewijsregel_service import Ess05BewijsregelService

    mk10._gepind(PLAN, PLAN_SHA256, "plan")
    r17 = json.loads(mk10._gepind(R17_INVOER, R17_INVOER_SHA256, "R17-invoer"))
    if r17.get("schema") != mk16.INVOERSCHEMA:
        msg = f"R17-invoer heeft niet het schema {mk16.INVOERSCHEMA}"
        raise MakerfoutError(msg)
    per_id = {i["id"]: i for i in r17["items"]}
    bron = {"bron": mk10._rel(R17_INVOER), "sha256": R17_INVOER_SHA256}
    items = [
        _uit_r17(per_id["A"], bron),
        _uit_r17(per_id["C"], bron),
        _synthetisch("D", per_id["A"], BRON_D, bron),
        _synthetisch("E", per_id["A"], BRON_E, bron),
    ]
    return {
        "schema": INVOERSCHEMA,
        "status": (
            "vooraf vastgelegd vóór elke R18-aanroep; A en C met gevalinhoud exact "
            f"uit de R17-invoer; C, D en E zijn {LABEL}; orakels buiten de "
            "modelpayload"
        ),
        "contract": Ess05BewijsregelService.contractidentiteit(),
        "herkomst": {
            "plan": {"pad": mk10._rel(PLAN), "sha256": PLAN_SHA256, "taak": "B2"},
            "gevallen": {**bron, "overgenomen": ["A", "C"], "velden": list(R17_VELDEN)},
            "scorer": "scripts/ess05/bewijsscorer.py",
            "regels": "scripts/ess05/maak_r18_bewijsregel_invoer.py (moduledocstring)",
            "contractnotitie": "docs/technisch/ess05-bewijsregels-contract-v6.md",
            "auteur": AUTEUR,
        },
        "items": items,
    }


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--doel", type=Path, default=DOEL)
    args = p.parse_args(argv)
    if args.doel.exists():
        msg = f"doel bestaat al: {args.doel}"
        raise FileExistsError(msg)
    invoer = maak_bewijsregel_invoer()
    mk16._schrijf(args.doel, json.dumps(invoer, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
