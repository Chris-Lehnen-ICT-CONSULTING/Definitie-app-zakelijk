"""DEF-768 R18B — invoer van de zes lokale controles (kern, doel, buur × A, C).

Plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md`, taak B3
(R18B), SYNTHETISCH, GEEN MODELUITVOER: de synthetisch herbonden
R17-interpretaties A en C uit het oorzakenonderzoek
(`reports/DEF-768-AI-20260928-R17/oorzakenonderzoek-ess05-v1-reproductie/
gecorrigeerd-R17-{A,C}.json`, zelf al gelabeld als synthetisch) worden hier:

1. omgezet naar bewijseenheden: elk letterlijk citaat `{material_id, citaat}`
   wordt de eenheid (of eenheden) die het raakt; het citaat moet precies één
   keer in materiaal mét eenheden staan, anders is het een makerfout
   (`naar_eenheden`, gelijk aan de testhulp in de domeintests, maar zelfstandig:
   de maker importeert geen testcode);
2. gebonden aan `ess05-interpretatie/3` en gevalideerd met
   `bewijsregels.valideer_interpretatie` op het materiaal van het R17-geval;
3. met `bewijsregels.controle_eenheden` omgezet naar precies drie
   controlepakketten per geval (kern, doel, buur).

Elk pakket wordt een lokale controle (`def768-ess05-lokale-invoer/1`, de
R15-route), `positief`, verwacht `supported`. Gevallen, materiaalhashes,
bronbestanden en het plan zijn gepind; een afwijking is een makerfout.

    .venv/bin/python scripts/ess05/maak_r18b_lokale_invoer.py [--doel P]

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

import maak_r10_verificatie_invoer as mk10
import maak_r16_bewijsregel_invoer as mk16
import maak_r18_bewijsregel_invoer as mk18
import proefinvoer as pi
from maak_r10_verificatie_invoer import MakerfoutError

__all__ = [
    "GECORRIGEERD",
    "INVOERSCHEMA",
    "MakerfoutError",
    "controleer_uniek",
    "lokale_items",
    "maak_lokale_invoer",
    "main",
    "naar_eenheden",
]

INVOERSCHEMA = "def768-ess05-lokale-invoer/1"
LABEL = mk16.LABEL
AUTEUR = mk18.AUTEUR
BRON_ID = "source:doc:testwerkinstructie-apparatuuruitgifte"
R17_INVOER, R17_INVOER_SHA256 = mk18.R17_INVOER, mk18.R17_INVOER_SHA256
_REPRODUCTIE = (
    PROJECT_ROOT
    / "reports"
    / "DEF-768-AI-20260928-R17"
    / "oorzakenonderzoek-ess05-v1-reproductie"
)
#: De synthetisch herbonden R17-interpretaties (SYNTHETISCH, GEEN MODELUITVOER).
GECORRIGEERD = {
    "A": (
        _REPRODUCTIE / "gecorrigeerd-R17-A.json",
        "38afa875cbaeacd9c6f9f01fe678c8a35b87498bc45b089c00a2bdc3d3542567",
    ),
    "C": (
        _REPRODUCTIE / "gecorrigeerd-R17-C.json",
        "ef375650309fc68347192f41affd960965d50b39f72c3d25530dd90878ef1c26",
    ),
}
DOEL = PROJECT_ROOT / "reports" / "DEF-768-AI-20260928-R18" / "lokale-invoer-v1.json"
#: De vaste volgorde van de drie eenheden per geval (`controle_eenheden`).
_EENHEDEN = ("kern", "doel", "buur")


def naar_eenheden(ruw: Mapping[str, Any], invoer: Any) -> dict[str, Any]:
    """Letterlijke citaten ({material_id, citaat}) → de eenheden die ze raken.

    Fail-closed: het citaat moet precies één keer voorkomen in materiaal met
    eenheden (niet definitie of context); een eenheidsnummer blijft staan.
    """
    eenheden = invoer.eenheden()
    ruw = copy.deepcopy(dict(ruw))

    def om(lijst: Sequence[Any], pad: str) -> list[str]:
        uit: list[str] = []
        for c in lijst:
            if isinstance(c, str):
                uit += [] if c in uit else [c]
                continue
            tekst = invoer.materiaal.get(c["material_id"], "")
            posities = [
                i for i in range(len(tekst)) if tekst.startswith(c["citaat"], i)
            ]
            if len(posities) != 1:
                msg = f"{pad}: citaat niet eenduidig ({len(posities)} treffers): {c}"
                raise MakerfoutError(msg)
            s, e = posities[0], posities[0] + len(c["citaat"])
            raak = [
                u
                for u, r in eenheden.items()
                if r.material_id == c["material_id"] and r.start < e and s < r.end
            ]
            if not raak:
                msg = f"{pad}: materiaal zonder eenheden (definitie/context?): {c}"
                raise MakerfoutError(msg)
            uit += [u for u in raak if u not in uit]
        return uit

    for soort in ("antwoorden", "buurgroepen"):
        for nummer, item in enumerate(ruw[soort], start=1):
            item["citaten"] = om(item["citaten"], f"{soort}[{nummer}]")
    return ruw


def _specificatie(pakket: Any) -> dict[str, Any]:
    return {
        "rol": pakket.inhoud["rol"],
        "uitspraak": pakket.inhoud["uitspraak"],
        "citaten": [
            {"material_id": c["material_id"], "start": c["start"], "end": c["end"]}
            for c in pakket.binding["citaten"]
        ],
    }


def lokale_items(
    naam: str,
    oud: Mapping[str, Any],
    interpretatie: Any,
    invoer: Any,
    herkomst: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """De drie controlepakketten (kern, doel, buur) van één geldige interpretatie."""
    from domain.ess05 import bewijsregels as br
    from services.validation.ess05_local_verification_service import (
        bouw_lokale_prompt,
    )
    from services.validation.ess05_verification_service import prompthash

    eenheden = br.controle_eenheden(interpretatie, invoer)
    namen = [e.naam.split(":", 1)[0] for e in eenheden]
    if namen != list(_EENHEDEN):
        msg = f"{naam}: controle-eenheden {namen}, verwacht {list(_EENHEDEN)}"
        raise MakerfoutError(msg)
    uit = []
    for eenheid, kort in zip(eenheden, _EENHEDEN, strict=True):
        pakket = eenheid.pakket
        uit.append(
            {
                "id": f"{naam}-{kort}",
                "soort": "positief",
                "verwacht": "supported",
                "geval": oud["geval"],
                "geval_sha256": oud["geval_sha256"],
                "materiaal_sha256": oud["materiaal_sha256"],
                "specificatie": _specificatie(pakket),
                "pakket": dict(pakket.inhoud),
                "pakket_hash": pakket.hash,
                "binding": dict(pakket.binding),
                "prompt_sha256": prompthash(*bouw_lokale_prompt(pakket)),
                "herkomst": {
                    **herkomst,
                    "label": LABEL,
                    "eenheid": eenheid.naam,
                    "regelversie": br.BEWIJSREGELVERSIE,
                },
            }
        )
    return uit


def controleer_uniek(items: Sequence[Mapping[str, Any]]) -> None:
    """Elk id en elk pakket precies eenmaal: een dubbel pakket is één controle."""
    for veld in ("id", "pakket_hash"):
        waarden = [i[veld] for i in items]
        if len(set(waarden)) != len(waarden):
            msg = f"dubbel {veld} in de lokale invoer: {waarden}"
            raise MakerfoutError(msg)


def _geval(oud: Mapping[str, Any]) -> Any:
    """De vergelijkingsinvoer van een R17-item, met controle van zijn hashes."""
    invoer = mk18.vergelijkingsinvoer(oud)
    if (
        pi.sha_json(oud["geval"]) != oud["geval_sha256"]
        or {m: mk10._sha(t) for m, t in invoer.materiaal.items()}
        != oud["materiaal_sha256"]
    ):
        msg = f"{oud['id']}: geval of materiaal wijkt af van de R17-invoer"
        raise MakerfoutError(msg)
    return invoer


def maak_lokale_invoer() -> dict[str, Any]:
    """Zes lokale controles uit de herbonden R17-interpretaties A en C."""
    from domain.ess05 import bewijsregels as br
    from services.validation.ess05_bewijsregel_service import Ess05BewijsregelService

    mk10._gepind(mk18.PLAN, mk18.PLAN_SHA256, "plan")
    r17 = json.loads(mk10._gepind(R17_INVOER, R17_INVOER_SHA256, "R17-invoer"))
    per_id = {i["id"]: i for i in r17["items"]}
    items: list[dict[str, Any]] = []
    for naam, (pad, sha) in GECORRIGEERD.items():
        oud = per_id[naam]
        invoer = _geval(oud)
        letterlijk = json.loads(mk10._gepind(pad, sha, f"gecorrigeerd-R17-{naam}"))
        ruw = naar_eenheden(letterlijk, invoer)
        ruw["schema_version"] = br.INTERPRETATIESCHEMA
        try:
            interpretatie = br.valideer_interpretatie(ruw, invoer)
        except br.BewijsregelfoutError as exc:
            msg = f"{naam}: herbonden interpretatie ongeldig onder v6: {exc}"
            raise MakerfoutError(msg) from exc
        items += lokale_items(
            naam,
            oud,
            interpretatie,
            invoer,
            {
                "interpretatie": {"pad": mk10._rel(pad), "sha256": sha},
                "r17_invoer": {
                    "pad": mk10._rel(R17_INVOER),
                    "sha256": R17_INVOER_SHA256,
                    "item": naam,
                },
                "omzetting": (
                    "letterlijke citaten naar eenheden (naar_eenheden), "
                    f"schema_version naar {br.INTERPRETATIESCHEMA}, gevalideerd met "
                    "valideer_interpretatie; pakketten uit controle_eenheden"
                ),
            },
        )
    controleer_uniek(items)
    return {
        "schema": INVOERSCHEMA,
        "status": (
            "lokale invoer R18B: kern-, doel- en buurpakket uit de synthetisch "
            f"herbonden R17-interpretaties A en C; {LABEL}; verwacht 6× supported"
        ),
        "herkomst": {
            "plan": {
                "pad": mk10._rel(mk18.PLAN),
                "sha256": mk18.PLAN_SHA256,
                "taak": "B3",
            },
            "bewijsregel_contract": Ess05BewijsregelService.contractidentiteit(),
            "regels": "scripts/ess05/maak_r18b_lokale_invoer.py (moduledocstring)",
            "contract": mk10._contract(),
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
    invoer = maak_lokale_invoer()
    mk16._schrijf(args.doel, json.dumps(invoer, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
