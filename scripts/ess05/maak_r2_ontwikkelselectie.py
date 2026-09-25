"""DEF-768 ronde 2 — ontwikkelselectie uit de oude (nu diagnostische) eindset.

Kopieert negen gevallen exact (ook labels, gronden en verwachtingen) uit
`reports/DEF-768-AI-20260924/onafhankelijke-eindset-v1.json` naar een nieuwe
datasetversie met herkomst. Alleen selectie: geen veld wordt gewijzigd,
toegevoegd of verwijderd. Het resultaat is bekend diagnostisch materiaal,
nooit holdout of acceptatieset.

    .venv/bin/python scripts/ess05/maak_r2_ontwikkelselectie.py \\
        [--bron PAD] [--doel PAD]

Het doel wordt nooit overschreven; de bronhash moet exact de vastgelegde zijn.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRON = (
    PROJECT_ROOT / "reports" / "DEF-768-AI-20260924" / "onafhankelijke-eindset-v1.json"
)
BRON_SHA256 = "7eae4b79749f4fc44fcd281d20166ca30152846b3d1dae9fb85f5a5992dc968e"
DOEL = PROJECT_ROOT / "reports" / "DEF-768-AI-20260924-R2" / "ontwikkelselectie-v1.json"
#: Besluit ronde 2: de negen bekende diagnostische T-gevallen.
SELECTIE = ("E06", "E09", "E10", "E13", "E14", "E15", "E16", "E05", "E20")
SCHEMA = "def768-r2-ontwikkelselectie/1"
STATUS = (
    "bekend diagnostisch materiaal uit de eindset van ronde 1; geen holdout, "
    "geen acceptatieset"
)


class SelectiefoutError(RuntimeError):
    """De bron of de selectie voldoet niet (fail-closed, niets geschreven)."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def maak_selectie(
    bron_bytes: bytes,
    *,
    bron_pad: str,
    ids: Sequence[str] = SELECTIE,
    bron_sha256: str = BRON_SHA256,
) -> dict[str, Any]:
    """De selectie als nieuwe datasetversie; gevallen exact gekopieerd."""
    if _sha(bron_bytes) != bron_sha256:
        msg = f"bronhash {_sha(bron_bytes)} is niet de vastgelegde {bron_sha256}"
        raise SelectiefoutError(msg)
    bron = json.loads(bron_bytes)
    per_id = {g["id"]: g for g in bron["gevallen"]}
    ontbrekend = [i for i in ids if i not in per_id]
    if ontbrekend or len(set(ids)) != len(ids):
        msg = f"selectie ongeldig (ontbrekend {ontbrekend} of dubbel)"
        raise SelectiefoutError(msg)
    return {
        "schema": SCHEMA,
        "status": STATUS,
        "herkomst": {
            "bron": bron_pad,
            "bron_sha256": bron_sha256,
            "bron_schema": bron.get("schema"),
            "bron_status": bron.get("status"),
            "geselecteerde_ids": list(ids),
            "bewerking": "alleen selectie; elk geval byte-voor-byte gelijk als JSON",
            "besluit": "DEF-768 ronde 2 (uitkomst-en-vervolg-v1, akkoord Chris 24-09)",
        },
        "gevallen": [copy.deepcopy(per_id[i]) for i in ids],
    }


def controleer_selectie(selectie: dict[str, Any], bron_bytes: bytes) -> None:
    """Elk geselecteerd geval is exact gelijk aan het bronrecord."""
    bron = {g["id"]: g for g in json.loads(bron_bytes)["gevallen"]}
    ids = selectie["herkomst"]["geselecteerde_ids"]
    if [g["id"] for g in selectie["gevallen"]] != ids:
        msg = "volgorde of ids van de gevallen wijken af van de herkomst"
        raise SelectiefoutError(msg)
    for geval in selectie["gevallen"]:
        if json.dumps(geval, sort_keys=True) != json.dumps(
            bron[geval["id"]], sort_keys=True
        ):
            msg = f"{geval['id']} wijkt af van de bron"
            raise SelectiefoutError(msg)
    if "herhaal_ids" in selectie:
        msg = "een ontwikkelselectie heeft geen herhaal_ids"
        raise SelectiefoutError(msg)


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bron", type=Path, default=BRON)
    p.add_argument("--doel", type=Path, default=DOEL)
    args = p.parse_args(argv)
    bron_bytes = args.bron.read_bytes()
    selectie = maak_selectie(bron_bytes, bron_pad=str(args.bron))
    controleer_selectie(selectie, bron_bytes)
    tekst = json.dumps(selectie, ensure_ascii=False, indent=2) + "\n"
    args.doel.parent.mkdir(parents=True, exist_ok=True)
    with args.doel.open("x", encoding="utf-8") as f:
        f.write(tekst)
    sys.stdout.write(f"{args.doel} sha256={_sha(tekst.encode('utf-8'))}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
