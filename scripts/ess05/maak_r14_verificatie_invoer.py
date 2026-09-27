"""DEF-768 R14 — verifier-only-invoer: twee gerichte negatieven na het R13-herstel.

Opdracht Chris 27-09 ("Ok kun je het nu wel fixen?",
`logs/def768/r13-herstel-gebruikersopdracht-v1.json`): de herproef krijgt naast
H1–H5 hoogstens twee gerichte verifier-negatieven die het false-positivegevaar
controleren. Keuze, vooraf vastgelegd en afgeleid uit het mechanisme:

answer/3 (`bewijs._dekkingsfout`) dwingt vóór de verifier af dat een route de
juiste SOORTEN materiaal bevat (kerncitaat plus drager of buurzijde). Het dekt
niet of die citaten de uitspraak inhoudelijk dragen. Het resterende gevaar is
dus dat een model de soorten aanvult met een citaat dat de uitspraak niet
draagt, en dat de verifier het gat opvult uit materiaal buiten de route (zoals
bij R13-H2 C13 en R13-H3 C7). Beide negatieven komen door de answer/3-
routecontrole en houden het oorspronkelijke inhoudelijke gat:

- **V-N6** (uit het echte R13-H2-antwoord) — de missing_feature-claim krijgt
  naast haar broncitaat het eerste kernkenmerkcitaat: een kernfragment dat
  niet laat zien dat het ontbrekende kenmerk in de hele kern ontbreekt. De
  vrije top-level claims buiten kandidaatmateriaal vervallen (answer/3).
  Foutdrager is de missing_feature-claim, tekst ongewijzigd.
- **V-N7** (uit het echte R13-H3-antwoord) — de directe gevolgtrekking in de
  buurreden zonder kerncitaat krijgt één kernpremisse met het genuscitaat
  ("De kern noemt: …"), die het kenmerk en de vergelijking in de conclusie
  niet draagt. Foutdrager is die gevolgtrekking, tekst ongewijzigd.

Verwacht per item: `unsupported` op de foutdrager (`_v_acceptatie`). Beide
items zijn SYNTHETISCH AFGELEID, GEEN MODELUITVOER; de oorspronkelijke R13-
callrecords blijven ongewijzigd en gepind. Het concept komt alleen uit de
actuele afleiding (`valideer_antwoord`, answer/3); een weigering daar is een
makerfout (niets geschreven).

    .venv/bin/python scripts/ess05/maak_r14_verificatie_invoer.py [--doel P]

Het doel wordt nooit overschreven; alle bronnen worden alleen gelezen.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections.abc import Callable, Mapping, Sequence
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
    "SELECTIE",
    "MakerfoutError",
    "maak_verificatie_invoer",
    "main",
    "n6_antwoord",
    "n7_antwoord",
]

R13_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260926-R13"
R14_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260927-R14"
GEVALLEN = R13_MAP / "herkenbare-gevallen-v1.json"
GEVALLEN_SHA256 = "b212b826ef51dce8c20b5a587e57389b13e3d24ab6d590e5dcfec7e60493841b"
_CALLS = R13_MAP / "ontwikkeling-20260926T214952592796Z" / "calls"
CALLRECORDS = {
    "H2": (
        _CALLS / "003-ontwikkeling-H2.json",
        "2b2956d631c6ff9f0f59545857f334b5fc0ef1b4d36e6333208642f957ed45a3",
    ),
    "H3": (
        _CALLS / "005-ontwikkeling-H3.json",
        "f37a5f01570ea8499b3e852d00b984067b80939fc2c384a7d22566d8e9843019",
    ),
}
INHOUDSCONTROLE = (
    PROJECT_ROOT
    / "logs"
    / "def768"
    / "herkenbare-gevallen-inhoudscontrole-result-v1.md"
)
INHOUDSCONTROLE_SHA256 = (
    "8a05e031c0779417be31efe4c35b5e2b619b165d9e5ed6fb0fd4c43ffe388014"
)
OPDRACHT = PROJECT_ROOT / "logs" / "def768" / "r13-herstel-gebruikersopdracht-v1.json"
DOEL = R14_MAP / "verificatie-invoer-v1.json"
AUTEUR = mk10.AUTEUR
LABEL = "SYNTHETISCH AFGELEID, GEEN MODELUITVOER"
_DEFINITIE = "definition"


def _is_kern(quote: Mapping[str, Any]) -> bool:
    return quote["material_id"] == _DEFINITIE


def n6_antwoord(ruw: Mapping[str, Any]) -> dict[str, Any]:
    """V-N6 uit een H2-antwoord: missing_feature met een niet-dragend kernfragment."""
    from domain.ess05.bewijs import ANTWOORDSCHEMA

    uit = copy.deepcopy(dict(ruw))
    uit["schema_version"] = ANTWOORDSCHEMA
    uit["reason"] = [
        c
        for c in uit["reason"]
        if c["role"] == "material" and all(_is_kern(q) for q in c["quotes"])
    ]
    (buur,) = uit["neighbours"]
    ontbrekend = buur["missing_feature"]
    if ontbrekend is None or any(_is_kern(q) for q in ontbrekend["quotes"]):
        msg = "V-N6: de missing_feature-claim is niet de claim zonder kerncitaat"
        raise MakerfoutError(msg)
    fragment = copy.deepcopy(uit["core_features"][0])
    ontbrekend["quotes"] = [fragment, *ontbrekend["quotes"]]
    return uit


def n7_antwoord(ruw: Mapping[str, Any]) -> dict[str, Any]:
    """V-N7 uit een H3-antwoord: buurgevolgtrekking met een niet-dragende kernpremisse."""
    from domain.ess05.bewijs import ANTWOORDSCHEMA

    uit = copy.deepcopy(dict(ruw))
    uit["schema_version"] = ANTWOORDSCHEMA
    (buur,) = uit["neighbours"]
    zonder_kern = [
        c
        for c in buur["reason"]
        if c["role"] == "inference"
        and not any(_is_kern(q) for p in c["premises"] for q in p.get("quotes", []))
    ]
    if len(zonder_kern) != 1:
        msg = "V-N7: niet precies één buurgevolgtrekking zonder kernpremisse"
        raise MakerfoutError(msg)
    genus = copy.deepcopy(uit["genus_quote"])
    premisse = {
        "role": "material",
        "quotes": [genus],
        "text": f"De kern noemt: {genus['quote']}.",
    }
    zonder_kern[0]["premises"] = [premisse, *zonder_kern[0]["premises"]]
    return uit


def _historische_foutdrager(concept: Mapping[str, Any], naam: str) -> dict[str, Any]:
    """De claim in het echte R13-concept die dezelfde rol heeft als de foutdrager."""
    claims = {c["id"]: c for c in concept["claims"]}
    (buur,) = concept["neighbours"]
    if naam == "V-N6":
        return claims[buur["missing_feature_claim"]]
    (claim,) = [
        claims[r] for r in buur["reason_claims"] if claims[r]["role"] == "inference"
    ]
    return claim


def _item(
    naam: str,
    geval_id: str,
    maak: Callable[[Mapping[str, Any]], dict[str, Any]],
    gevallen: Mapping[str, Any],
    norm: Mapping[str, str],
) -> dict[str, Any]:
    from domain.ess05.contract import valideer_antwoord

    pad, verwacht = CALLRECORDS[geval_id]
    record = json.loads(mk10._gepind(pad, verwacht, f"R13-callrecord {geval_id}"))
    doc = record["beoordelingsdocument"]
    geval = gevallen[geval_id]
    ruw = record["ruw_antwoord"]
    if (
        record["geval_id"] != geval_id
        or pi.sha_json(geval) != record["geval_sha256"]
        or mk10._sha(ruw) != record["ruw_antwoord_sha256"]
        or ruw != doc["raw_response"]
    ):
        msg = f"{naam}: callrecord hoort niet bij het geval of het ruwe antwoord"
        raise MakerfoutError(msg)
    materiaal, buren, _ = mig.verificatiemateriaal(geval, norm)
    antwoord = maak(json.loads(ruw))
    concept, fouten = valideer_antwoord(antwoord, materiaal, buren)
    if concept is None:
        msg = f"{naam}: de afgeleide answer/3-variant wordt geweigerd ({fouten})"
        raise MakerfoutError(msg)
    historisch = _historische_foutdrager(doc["concept"], naam)
    nieuw = _historische_foutdrager(concept.data, naam)
    if (nieuw["role"], nieuw["text"]) != (historisch["role"], historisch["text"]):
        msg = f"{naam}: de foutdrager wijkt inhoudelijk af van de R13-claim"
        raise MakerfoutError(msg)
    foutdrager = f"claim:{nieuw['id']}"
    bron = {
        "label": LABEL,
        "afgeleid_uit": {
            "callrecord": mk10._rel(pad),
            "callrecord_sha256": verwacht,
            "sleutel": record["sleutel"],
            "ruw_antwoord_sha256": record["ruw_antwoord_sha256"],
            "prompt_version": doc["prompt_version"],
            "concept_hash": doc["concept_derivation"]["concept_hash"],
        },
        "transformatie": (maak.__doc__ or "").strip(),
        "historische_foutdrager": {
            "claim": f"claim:{historisch['id']}",
            "verifieroordeel": mk10.historisch_oordeel(
                doc, f"claim:{historisch['id']}"
            ),
        },
        "verwacht": {"item": foutdrager, "outcome": "unsupported"},
        "inhoudscontrole": {
            "pad": mk10._rel(INHOUDSCONTROLE),
            "sha256": INHOUDSCONTROLE_SHA256,
        },
        "antwoord": json.dumps(antwoord, ensure_ascii=False),
    }
    return mig.invoeritem(naam, "fout", geval, concept.data, [foutdrager], bron, norm)


#: (id, R13-geval, afleiding) in vaste volgorde.
SELECTIE = (("V-N6", "H2", n6_antwoord), ("V-N7", "H3", n7_antwoord))


def maak_verificatie_invoer(*, gevallen: Path = GEVALLEN) -> dict[str, Any]:
    """De twee gerichte negatieven, afgeleid, gebonden aan de actuele code."""
    from services.validation.ess05_assessment_service import laad_ess05_norm

    data = json.loads(mk10._gepind(gevallen, GEVALLEN_SHA256, "R13-gevallen"))
    per_id = {g["id"]: g for g in data["gevallen"]}
    mk10._gepind(INHOUDSCONTROLE, INHOUDSCONTROLE_SHA256, "inhoudscontrole")
    norm = laad_ess05_norm()
    items = [_item(n, g, maak, per_id, norm) for n, g, maak in SELECTIE]
    return {
        "schema": mig.INVOERSCHEMA,
        "status": (
            f"verifier-only-invoer R14: V-N6 (uit R13-H2) en V-N7 (uit R13-H3), "
            f"{LABEL}; verwacht unsupported op de foutdrager"
        ),
        "herkomst": {
            "r13_gevallen": {"pad": mk10._rel(gevallen), "sha256": GEVALLEN_SHA256},
            "selectie": [n for n, _, _ in SELECTIE],
            "opdracht": mk10._rel(OPDRACHT),
            "regels": "scripts/ess05/maak_r14_verificatie_invoer.py (moduledocstring)",
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
    invoer = maak_verificatie_invoer()
    tekst = json.dumps(invoer, ensure_ascii=False, indent=2) + "\n"
    args.doel.parent.mkdir(parents=True, exist_ok=True)
    with args.doel.open("x", encoding="utf-8") as f:
        f.write(tekst)
    sys.stdout.write(f"{args.doel} sha256={mk10._sha(tekst)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
