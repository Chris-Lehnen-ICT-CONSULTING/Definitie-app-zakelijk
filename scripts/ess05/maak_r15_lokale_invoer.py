"""DEF-768 R15 — invoer van de vier lokale controles (fase A bewijsisolatie).

Opdracht Chris 27-09 ("Akkoord om het zo op te pakken",
`logs/def768/isolatie-gebruikersopdracht-v1.json`) op het advies
`reports/DEF-768-AI-20260927-R14/oplossingsonderzoek-v1.md` (§6.2): vier vooraf
vastgelegde lokale controles, elk één afzonderlijk verzoek met alleen de
uitspraak, het toetsprincipe van haar rol en haar eigen route.

- **L-N1** — exact de R14-doelclaim van V-N6 (materiaalclaim) met haar
  huidige citaten: een kernfragment plus een broncitaat. Verwacht: unsupported.
- **L-N2** — exact de R14-doelclaim van V-N7 (gevolgtrekking) met haar huidige
  directe premissen. Verwacht: unsupported.
- **L-P1** — SYNTHETISCH, GEEN MODELUITVOER: dezelfde uitspraak als L-N1; elk
  kernfragment is vervangen door de volledige gebonden definitie, die als
  bewijsplaats al in hetzelfde concept staat (een uitspraak over wat de hele
  kern mist vraagt de hele kern als bereik). Het broncitaat blijft gelijk.
  Verwacht: supported.
- **L-P2** — SYNTHETISCH, GEEN MODELUITVOER: dezelfde uitspraak als L-N2 met
  de werkelijk benodigde directe premissen: drie bestaande materiaalclaims uit
  hetzelfde concept (kernkenmerken met kosteloos; de beschrijving van het
  verwante begrip zonder kostenkenmerk; de bron zonder kostenkenmerk en zonder
  verdere informatie) plus één premisse over de uitleenzin van dezelfde bron.
  Die premissetekst is die van een echte R14-claim over exact dezelfde zin in
  de bron van een ander geval; hier gebonden aan de letterlijk identieke zin in
  deze bron. Verwacht: supported.

De twee negatieven zijn ongewijzigd (uitspraak, citaten of premissen); de
positieven gebruiken niet dezelfde te korte route. Bronhashes, doel-ID's,
bindingen en verwachtingen staan in het item, buiten de modelpayload (`pakket`).
Het concept komt alleen uit gepinde bronnen; afwijking is een makerfout (niets
geschreven). `--oracle` schrijft daarnaast de invoer voor de onafhankelijke
inhoudelijke oraclecontrole.

    .venv/bin/python scripts/ess05/maak_r15_lokale_invoer.py [--doel P] [--oracle P]

Doelen worden nooit overschreven; alle bronnen worden alleen gelezen.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import maak_r10_verificatie_invoer as mk10
import migreer_r7_naar_v2 as mig
import proefinvoer as pi
from maak_r10_verificatie_invoer import MakerfoutError

__all__ = [
    "INVOERSCHEMA",
    "MakerfoutError",
    "maak_lokale_invoer",
    "main",
    "oracletekst",
]

INVOERSCHEMA = "def768-ess05-lokale-invoer/1"
R14_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260927-R14"
R15_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260928-R15"
LOGS = PROJECT_ROOT / "logs" / "def768"
V14 = R14_MAP / "verificatie-invoer-v1.json"
V14_SHA256 = "233fcbf0da84f897792c1e355c71d08eda237faabd92e3935950b8fd00609689"
_V_CALLS = R14_MAP / "verificatie_alleen-20260927T083332251367Z" / "calls"
_O_CALLS = R14_MAP / "ontwikkeling-20260927T082739100787Z" / "calls"
#: De echte R14-verifieroordelen over de twee negatieven (historisch supported).
R14_VERIFIER = {
    "V-N6": (
        _V_CALLS / "010-verificatie_alleen-V-N6.json",
        "94dd4bd01fcda0bbb58027ef61af00c9f762a025632885a5da5cb65199a6756f",
    ),
    "V-N7": (
        _V_CALLS / "011-verificatie_alleen-V-N7.json",
        "67767a3c0b214ebecda2eab2fc078cd095693c8cd9032cf37040ac6f82f50950",
    ),
}
#: Het echte R14-H2-callrecord met de claim over de uitleenzin van de bron.
R14_H2 = (
    _O_CALLS / "003-ontwikkeling-H2.json",
    "baae3c2d036bd148671fe40b30ec74a40b57f4d883cd0b670dd0dc255c6254a0",
)
INHOUDSCONTROLE = LOGS / "ronde14-inhoudscontrole-result-v1.md"
INHOUDSCONTROLE_SHA256 = (
    "626ee6987b8dff348e4768232d4cf8bf04852e50d92d74bb41d5fb1f80d4d8a5"
)
OPDRACHT = LOGS / "isolatie-gebruikersopdracht-v1.json"
DOEL = R15_MAP / "lokale-invoer-v1.json"
ORACLE = LOGS / "isolatie-fase-a-oracle-invoer-v1.md"
AUTEUR = mk10.AUTEUR
LABEL = "SYNTHETISCH, GEEN MODELUITVOER"
_DEFINITIE = "definition"

#: L-P2, vooraf vastgelegd: de benodigde directe premissen uit het V-N7-concept,
#: met per premisse de deelzin van de doeluitspraak die zij draagt.
P2_CONCEPTPREMISSEN = (
    ("C1", "de kern bevat het kenmerk kosteloos"),
    ("C3", "de beschrijving van het verwante begrip noemt geen kostenkenmerk"),
    ("C4", "de bron noemt voor het verwante begrip geen kosten en niets verder"),
)
#: L-P2: de claim in het R14-H2-concept over de uitleenzin van de bron; draagt
#: wat uitleen volgens de bron is (nodig voor 'buiten uitleen').
P2_UITLEENCLAIM = "C5"


def _concept_en_materiaal(item: Mapping[str, Any], norm: Mapping[str, str]):
    from domain.ess05.bewijs import Ess05Concept

    geval = item["geval"]
    if pi.sha_json(geval) != item["geval_sha256"]:
        msg = f"{item['id']}: geval wijkt af van geval_sha256"
        raise MakerfoutError(msg)
    materiaal, buren, _ = mig.verificatiemateriaal(geval, norm)
    if {m: mk10._sha(t) for m, t in materiaal.items()} != item["materiaal_sha256"]:
        msg = f"{item['id']}: materiaal wijkt af van de vastgelegde materiaalhashes"
        raise MakerfoutError(msg)
    concept = Ess05Concept(item["concept"])
    if concept.hash != item["concept_hash"]:
        msg = f"{item['id']}: concept wijkt af van concept_hash"
        raise MakerfoutError(msg)
    return concept, materiaal, {b.id: b.term for b in buren}


def _doelclaim(item: Mapping[str, Any]) -> str:
    (foutdrager,) = item["foutdragende_items"]
    if not foutdrager.startswith("claim:"):
        msg = f"{item['id']}: foutdrager {foutdrager!r} is geen claim"
        raise MakerfoutError(msg)
    return foutdrager.removeprefix("claim:")


def _specificatie(pakket) -> dict[str, Any]:
    inhoud = pakket.inhoud
    if "citaten" in inhoud:
        return {
            "rol": inhoud["rol"],
            "uitspraak": inhoud["uitspraak"],
            "citaten": [
                {"material_id": c["material_id"], "start": c["start"], "end": c["end"]}
                for c in pakket.binding["citaten"]
            ],
        }
    return {
        "rol": inhoud["rol"],
        "uitspraak": inhoud["uitspraak"],
        "premissen": [p["uitspraak"] for p in inhoud["premissen"]],
    }


def _item(
    naam: str,
    soort: str,
    bron: Mapping[str, Any],
    pakket,
    herkomst: Mapping[str, Any],
) -> dict[str, Any]:
    from services.validation.ess05_local_verification_service import (
        bouw_lokale_prompt,
    )
    from services.validation.ess05_verification_service import prompthash

    return {
        "id": naam,
        "soort": soort,
        "verwacht": "unsupported" if soort == "negatief" else "supported",
        "geval": bron["geval"],
        "geval_sha256": bron["geval_sha256"],
        "materiaal_sha256": bron["materiaal_sha256"],
        "specificatie": _specificatie(pakket),
        "pakket": dict(pakket.inhoud),
        "pakket_hash": pakket.hash,
        "binding": dict(pakket.binding),
        "prompt_sha256": prompthash(*bouw_lokale_prompt(pakket)),
        "herkomst": dict(herkomst),
    }


def _historisch(naam: str, claim: str) -> dict[str, Any]:
    pad, sha = R14_VERIFIER[naam]
    record = json.loads(mk10._gepind(pad, sha, f"R14-verifiercallrecord {naam}"))
    (check,) = [
        c
        for c in record["verificatie"]["ruw"]["checks"]
        if c["item"] == f"claim:{claim}"
    ]
    return {
        "callrecord": mk10._rel(pad),
        "sha256": sha,
        "item": check["item"],
        "outcome": check["outcome"],
        "finding": check["finding"],
    }


def _uitleenpremisse(materiaal: Mapping[str, str]) -> tuple[str, dict[str, Any]]:
    """(tekst, herkomst): de R14-H2-claim, gebonden aan dezelfde zin in deze bron."""
    pad, sha = R14_H2
    record = json.loads(mk10._gepind(pad, sha, "R14-H2-callrecord"))
    concept = record["beoordelingsdocument"]["concept"]
    claims = {c["id"]: c for c in concept["claims"]}
    plaatsen = {e["id"]: e for e in concept["evidence"]}
    claim = claims[P2_UITLEENCLAIM]
    (ref,) = claim["evidence"]
    plaats = plaatsen[ref]
    tekst = materiaal.get(plaats["material_id"], "")
    if claim["role"] != "material" or tekst.count(plaats["quote"]) != 1:
        msg = "L-P2: de uitleenzin staat niet precies eenmaal in deze bron"
        raise MakerfoutError(msg)
    start = tekst.index(plaats["quote"])
    return claim["text"], {
        "label": LABEL,
        "tekst_uit": {
            "callrecord": mk10._rel(pad),
            "sha256": sha,
            "claim": P2_UITLEENCLAIM,
        },
        "gebonden_citaat": {
            "material_id": plaats["material_id"],
            "material_sha256": mk10._sha(tekst),
            "start": start,
            "end": start + len(plaats["quote"]),
            "quote": plaats["quote"],
        },
    }


def maak_lokale_invoer(*, v14: Path = V14) -> dict[str, Any]:
    """De vier lokale controles, gebonden aan gepinde R14-bronnen en de huidige code."""
    from domain.ess05 import lokale_controle as lc
    from services.validation.ess05_assessment_service import laad_ess05_norm

    bron = json.loads(mk10._gepind(v14, V14_SHA256, "R14-V-invoer"))
    mk10._gepind(INHOUDSCONTROLE, INHOUDSCONTROLE_SHA256, "R14-inhoudscontrole")
    per_id = {item["id"]: item for item in bron["items"]}
    norm = laad_ess05_norm()
    n6, n7 = per_id["V-N6"], per_id["V-N7"]
    items = []

    # L-N1 en L-P1: de materiaalclaim van V-N6.
    concept, materiaal, termen = _concept_en_materiaal(n6, norm)
    doel = _doelclaim(n6)
    n1 = lc.pakket_uit_concept(concept, doel, materiaal, buurtermen=termen)
    if n1.rol != "material":
        msg = f"V-N6: {doel} is geen materiaalclaim"
        raise MakerfoutError(msg)
    basis = {"bron": mk10._rel(v14), "bron_sha256": V14_SHA256, "item": "V-N6"}
    items.append(
        _item("L-N1", "negatief", n6, n1, {
            **basis, "doelclaim": doel, "afleiding": "ongewijzigd",
            "historisch_r14": _historisch("V-N6", doel),
        })
    )  # fmt: skip
    kern = materiaal[_DEFINITIE]
    volledig = [
        e["id"]
        for e in concept.data["evidence"]
        if e["material_id"] == _DEFINITIE and e["quote"] == kern
    ]
    if not volledig:
        msg = "V-N6: het concept bevat geen bewijsplaats met de volledige definitie"
        raise MakerfoutError(msg)
    refs = [
        (
            lc.Citaatverwijzing(c["material_id"], c["start"], c["end"])
            if c["material_id"] != _DEFINITIE
            else lc.Citaatverwijzing(_DEFINITIE, 0, len(kern))
        )
        for c in n1.binding["citaten"]
    ]
    p1 = lc.bouw_materiaalpakket(
        n1.inhoud["uitspraak"], refs, materiaal, buurtermen=termen
    )
    if p1.inhoud["citaten"] == n1.inhoud["citaten"]:
        msg = "L-P1: de route verschilt niet van de negatieve route"
        raise MakerfoutError(msg)
    items.append(
        _item("L-P1", "positief", n6, p1, {
            **basis, "doelclaim": doel, "label": LABEL,
            "afleiding": (
                "kernfragment vervangen door de volledige gebonden definitie "
                f"(bestaande bewijsplaats {volledig[0]}); broncitaat ongewijzigd"
            ),
        })
    )  # fmt: skip

    # L-N2 en L-P2: de gevolgtrekking van V-N7.
    concept, materiaal, termen = _concept_en_materiaal(n7, norm)
    doel = _doelclaim(n7)
    n2 = lc.pakket_uit_concept(concept, doel, materiaal, buurtermen=termen)
    if n2.rol != "inference":
        msg = f"V-N7: {doel} is geen gevolgtrekking"
        raise MakerfoutError(msg)
    basis = {"bron": mk10._rel(v14), "bron_sha256": V14_SHA256, "item": "V-N7"}
    items.append(
        _item("L-N2", "negatief", n7, n2, {
            **basis, "doelclaim": doel, "afleiding": "ongewijzigd",
            "premissen": list(n2.binding["premissen"]),
            "historisch_r14": _historisch("V-N7", doel),
        })
    )  # fmt: skip
    claims = {c["id"]: c for c in concept.data["claims"]}
    for ref, _ in P2_CONCEPTPREMISSEN:
        if claims[ref]["role"] != "material":
            msg = f"L-P2: premisse {ref} is geen materiaalclaim"
            raise MakerfoutError(msg)
        lc.pakket_uit_concept(concept, ref, materiaal)  # bewijsplaatsen gebonden
    uitleen, uitleenherkomst = _uitleenpremisse(materiaal)
    kernpremisse, *verwant = [claims[r]["text"] for r, _ in P2_CONCEPTPREMISSEN]
    p2 = lc.bouw_gevolgtrekkingspakket(
        n2.inhoud["uitspraak"], [kernpremisse, uitleen, *verwant]
    )
    items.append(
        _item("L-P2", "positief", n7, p2, {
            **basis, "doelclaim": doel, "label": LABEL,
            "afleiding": "benodigde directe premissen (zie premissen)",
            "premissen": [
                {"claim": P2_CONCEPTPREMISSEN[0][0], "draagt": P2_CONCEPTPREMISSEN[0][1]},
                {"synthetisch": uitleenherkomst,
                 "draagt": "wat uitleen volgens de bron is (tijdelijk en kosteloos)"},
                *({"claim": r, "draagt": d} for r, d in P2_CONCEPTPREMISSEN[1:]),
            ],
        })
    )  # fmt: skip
    return {
        "schema": INVOERSCHEMA,
        "status": (
            "lokale invoer R15 (fase A): L-N1/L-N2 exact de R14-doelclaims van "
            f"V-N6/V-N7; L-P1/L-P2 {LABEL}, met complete eigen route"
        ),
        "herkomst": {
            "r14_verificatie_invoer": {"pad": mk10._rel(v14), "sha256": V14_SHA256},
            "inhoudscontrole": {
                "pad": mk10._rel(INHOUDSCONTROLE),
                "sha256": INHOUDSCONTROLE_SHA256,
            },
            "opdracht": mk10._rel(OPDRACHT),
            "regels": "scripts/ess05/maak_r15_lokale_invoer.py (moduledocstring)",
            "contract": mk10._contract(),
            "auteur": AUTEUR,
        },
        "items": items,
    }


def oracletekst(invoer: Mapping[str, Any]) -> str:
    """Invoer voor de onafhankelijke inhoudelijke oraclecontrole (geen modelpayload)."""
    delen = [
        "# DEF-768 R15 — invoer voor de oraclecontrole van de vier lokale controles",
        "",
        (
            "Per controle: wat het model ziet (`pakket`), de vooraf vastgelegde "
            "verwachting en de herkomst. Het gebonden materiaal staat erbij voor jouw "
            "eigen oordeel; het gaat NIET naar het model. Vragen: (1) is de verwachting "
            "juist als alleen dit pakket telt; (2) is bij de positieven elke premisse of "
            "elk citaat waar ten opzichte van het materiaal en is de route compleet; (3) "
            "is een doeluitspraak op zichzelf onjuist?"
        ),
        "",
    ]
    for item in invoer["items"]:
        delen += [
            f"## {item['id']} — {item['soort']}, verwacht `{item['verwacht']}`",
            "",
            f"- pakket_hash `{item['pakket_hash']}`, prompt_sha256 `{item['prompt_sha256']}`",
            "",
            "Pakket (exact de modelpayload, naast het toetsprincipe van de rol):",
            "",
            "```json",
            json.dumps(item["pakket"], ensure_ascii=False, indent=1),
            "```",
            "",
            "Herkomst en binding (buiten de payload):",
            "",
            "```json",
            json.dumps(
                {"herkomst": item["herkomst"], "binding": item["binding"]},
                ensure_ascii=False,
                indent=1,
            ),
            "```",
            "",
        ]
    materialen: dict[str, dict[str, str]] = {}
    for item in invoer["items"]:
        materiaal, _, _ = mig.verificatiemateriaal(item["geval"])
        materialen[item["herkomst"]["item"]] = materiaal
    delen += ["## Gebonden materiaal (alleen voor de oracle)", ""]
    for naam, materiaal in materialen.items():
        delen += [f"### {naam}", "", "```json"]
        delen += [json.dumps(materiaal, ensure_ascii=False, indent=1), "```", ""]
    return "\n".join(delen)


def _schrijf(doel: Path, tekst: str) -> None:
    if doel.exists():
        msg = f"doel bestaat al: {doel}"
        raise FileExistsError(msg)
    doel.parent.mkdir(parents=True, exist_ok=True)
    with doel.open("x", encoding="utf-8") as f:
        f.write(tekst)
    sys.stdout.write(f"{doel} sha256={mk10._sha(tekst)}\n")


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--doel", type=Path, default=DOEL)
    p.add_argument("--oracle", type=Path, default=None)
    args = p.parse_args(argv)
    invoer = maak_lokale_invoer()
    _schrijf(args.doel, json.dumps(invoer, ensure_ascii=False, indent=2) + "\n")
    if args.oracle is not None:
        _schrijf(args.oracle, oracletekst(invoer))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
