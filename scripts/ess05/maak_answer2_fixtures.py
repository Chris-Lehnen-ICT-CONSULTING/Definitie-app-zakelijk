"""DEF-768 answer/2 — synthetische `ess05-answer/2`-fixtures uit de echte R9/R10-antwoorden.

Besluit Chris 26-09 (`logs/def768/answer2-offline-goedkeuring-v1.json`) op
`logs/def768/ronde11-c10-diagnose-voorstel-v2.md`. Deterministische
transformatie van het echte, geldige `ess05-answer/1`-antwoord (R720) uit het
R9- en het R10-uittreksel naar de geneste vorm `ess05-answer/2`: elke claim
inline op haar gebruiksplaats, citaten en premissen vóór de tekst.

**Synthetisch getransformeerd, geen modeluitvoer.** De fixture bewijst alleen
de afleiding answer/2 → concept/1 en de keten; niet wat een model onder
answer/2 schrijft, en niet dat een claimtekst binnen haar citaten blijft.

Fail-closed, geen reparatie:

- het bronuittreksel heeft exact zijn gepinde hash;
- het bronantwoord geeft onder de answer/1-parser precies het bewaarde concept
  (een antwoord met een ongebruikte claim, zoals R11, komt hier dus nooit door
  en wordt ook niet aangeboden);
- de answer/2-afleiding geeft dat concept terug, modulo de ID-toekenning.

    .venv/bin/python scripts/ess05/maak_answer2_fixtures.py [--doelmap P]

Het doel wordt nooit overschreven; alle bronnen worden alleen gelezen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import migreer_r7_naar_v2 as mig

SCRIPT = "scripts/ess05/maak_answer2_fixtures.py"
FIXTUREMAP = "tests/fixtures/ess05"
SCHEMA = "def768-ess05-answer2-fixture/1"
LABEL = (
    "SYNTHETISCH GETRANSFORMEERD, GEEN MODELUITVOER: deterministische "
    "transformatie van het echte ess05-answer/1-antwoord naar ess05-answer/2. "
    "Bewijst alleen de afleiding en de keten, niet wat een model onder "
    "answer/2 schrijft."
)
#: ronde → (bronuittreksel, gepinde sha256).
BRONNEN: dict[str, tuple[str, str]] = {
    "r9": (
        f"{FIXTUREMAP}/r9_r720_callrecord_uittreksel_v1.json",
        "5a7ff2b045f49b59aa480ce4183aa196e58c2d27d2fcfd953f9f2399e6693720",
    ),
    "r10": (
        f"{FIXTUREMAP}/r10_r720_callrecord_uittreksel_v1.json",
        "9d64ae98981fc1cdf43c4f91e07e0218f2016dc51c30d845ffb6c463ac92e559",
    ),
}


class MakerfoutError(RuntimeError):
    """Bron of transformatie wijkt af: geen fixture (fail-closed)."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def doelnaam(ronde: str) -> str:
    return f"answer2_uit_{ronde}_r720_v1.json"


def naar_answer2(antwoord1: Mapping[str, Any]) -> dict[str, Any]:
    """Het platte answer/1-antwoord genest: elke verwijzing vervangen door haar inhoud."""
    bewijs = {e["id"]: e for e in antwoord1["evidence"]}
    claims = {c["id"]: c for c in antwoord1["claims"]}

    def citaat(ref: str | None) -> dict[str, Any] | None:
        if ref is None:
            return None
        e = bewijs[ref]
        return {
            "material_id": e["material_id"],
            "material_sha256": e["material_sha256"],
            "quote": e["quote"],
        }

    def claim(ref: str | None) -> dict[str, Any] | None:
        if ref is None:
            return None
        c = claims[ref]
        if c["role"] == "material":
            return {
                "role": c["role"],
                "quotes": [citaat(e) for e in c["evidence"]],
                "text": c["text"],
            }
        if c["role"] == "inference":
            return {
                "role": c["role"],
                "premises": [claim(p) for p in c["premises"]],
                "text": c["text"],
            }
        return {"role": c["role"], "text": c["text"]}

    vraag = antwoord1["question"]
    return {
        "schema_version": "ess05-answer/2",
        "genus_quote": citaat(antwoord1["genus_evidence"]),
        "core_features": [citaat(k["evidence"]) for k in antwoord1["core_features"]],
        "reason": [claim(r) for r in antwoord1["reason_claims"]],
        "neighbours": [
            {
                "neighbour_id": b["neighbour_id"],
                "distinction": b["distinction"],
                "feature_quote": citaat(b["feature_evidence"]),
                "reason": [claim(r) for r in b["reason_claims"]],
                "missing_feature": claim(b["missing_feature_claim"]),
                "uncertainty": claim(b["uncertainty_claim"]),
            }
            for b in antwoord1["neighbours"]
        ],
        "proposals": [
            {
                "term": p["term"],
                "source_quote": citaat(p["source_evidence"]),
                "reason": [claim(r) for r in p["reason_claims"]],
            }
            for p in antwoord1["proposals"]
        ],
        "question": (
            None
            if vraag is None
            else {"text": vraag["text"], "claims": [claim(r) for r in vraag["claims"]]}
        ),
    }


def zonder_ids(concept: Mapping[str, Any]) -> dict[str, Any]:
    """Het concept met elke verwijzing vervangen door haar inhoud (ID's vallen weg)."""
    bewijs = {
        e["id"]: (
            e["material_id"],
            e["material_sha256"],
            e["start"],
            e["end"],
            e["quote"],
        )
        for e in concept["evidence"]
    }
    claims = {c["id"]: c for c in concept["claims"]}

    def claim(ref: str | None) -> Any:
        if ref is None:
            return None
        c = claims[ref]
        return [
            c["role"],
            c["text"],
            [bewijs[e] for e in c["evidence"]],
            [claim(p) for p in c["premises"]],
        ]

    vraag = concept["question"]
    return {
        "genus": bewijs.get(concept["genus_evidence"]),
        "kenmerken": [bewijs[k["evidence"]] for k in concept["core_features"]],
        "reden": [claim(r) for r in concept["reason_claims"]],
        "buren": [
            [
                b["neighbour_id"],
                b["distinction"],
                bewijs.get(b["feature_evidence"]),
                [claim(r) for r in b["reason_claims"]],
                claim(b["missing_feature_claim"]),
                claim(b["uncertainty_claim"]),
            ]
            for b in concept["neighbours"]
        ],
        "voorstellen": [
            [
                p["term"],
                bewijs.get(p["source_evidence"]),
                [claim(r) for r in p["reason_claims"]],
            ]
            for p in concept["proposals"]
        ],
        "vraag": (
            None
            if vraag is None
            else [vraag["text"], [claim(r) for r in vraag["claims"]]]
        ),
        "claims": sorted(json.dumps(claim(c), ensure_ascii=False) for c in claims),
        "bewijs": sorted(bewijs.values()),
    }


def bouw_fixture(ronde: str) -> str:
    """De fixturetekst voor één ronde; MakerfoutError bij elke afwijking."""
    from domain.ess05 import bewijs
    from domain.ess05.contract import valideer_antwoord

    pad, verwacht = BRONNEN[ronde]
    data = (PROJECT_ROOT / pad).read_bytes()
    if _sha(data) != verwacht:
        msg = f"{ronde}: {pad} wijkt af van de gepinde hash {verwacht}"
        raise MakerfoutError(msg)
    uittreksel = json.loads(data)
    doc = uittreksel["beoordelingsdocument"]
    ruw1 = uittreksel["raw_response"]
    if _sha(ruw1.encode("utf-8")) != uittreksel["raw_response_sha256"]:
        msg = f"{ronde}: het ruwe antwoord hoort niet bij zijn hash"
        raise MakerfoutError(msg)
    materiaal, buren, _ = mig.verificatiemateriaal(uittreksel["geval"])
    historisch, fouten = valideer_antwoord(
        json.loads(ruw1), materiaal, buren, schema=bewijs.ANTWOORDSCHEMA_1
    )
    if historisch is None or historisch.data != doc["concept"]:
        msg = f"{ronde}: het bronantwoord geeft niet het bewaarde concept ({fouten})"
        raise MakerfoutError(msg)
    antwoord2 = naar_answer2(json.loads(ruw1))
    ruw2 = json.dumps(antwoord2, ensure_ascii=False, indent=2)
    # Sinds answer/3 historisch: expliciet onder answer/2 afgeleid.
    afgeleid, fouten = valideer_antwoord(
        json.loads(ruw2), materiaal, buren, schema=bewijs.ANTWOORDSCHEMA_2
    )
    if afgeleid is None or zonder_ids(afgeleid.data) != zonder_ids(historisch.data):
        msg = f"{ronde}: de answer/2-afleiding wijkt af van het concept ({fouten})"
        raise MakerfoutError(msg)
    fixture = {
        "schema": SCHEMA,
        "label": LABEL,
        "synthetisch_getransformeerd": True,
        "modeluitvoer": False,
        "bron": {
            "uittreksel": pad,
            "uittreksel_sha256": verwacht,
            "callrecord": uittreksel["bron"]["callrecord"],
            "callrecord_sha256": uittreksel["bron"]["callrecord_sha256"],
            "answer_schema_version": bewijs.ANTWOORDSCHEMA_1,
            "raw_response_sha256": uittreksel["raw_response_sha256"],
            "concept_hash": historisch.hash,
        },
        "transformatie": {
            "script": SCRIPT,
            "script_sha256": _sha((PROJECT_ROOT / SCRIPT).read_bytes()),
        },
        "answer_schema_version": bewijs.ANTWOORDSCHEMA_2,
        "geval_sha256": uittreksel["geval_sha256"],
        "raw_response": ruw2,
        "raw_response_sha256": _sha(ruw2.encode("utf-8")),
        "afgeleid_concept_hash": afgeleid.hash,
    }
    return json.dumps(fixture, ensure_ascii=False, indent=2) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--doelmap", type=Path, default=PROJECT_ROOT / FIXTUREMAP)
    args = parser.parse_args(argv)
    for ronde in BRONNEN:
        tekst = bouw_fixture(ronde)
        doel = args.doelmap / doelnaam(ronde)
        with open(doel, "x", encoding="utf-8") as f:
            f.write(tekst)
        print(f"{doel} {_sha(tekst.encode('utf-8'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
