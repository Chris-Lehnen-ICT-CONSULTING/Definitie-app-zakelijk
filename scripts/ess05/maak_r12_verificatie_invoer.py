"""DEF-768 R12 — verifier-only-invoer van de microproef: V-N4 en V-N5 uit V8.

Besluit Chris 26-09 ("Ja akkoord", `logs/def768/answer2-microproef-goedkeuring-v1.json`):
een kleine, beslissende praktijkvergelijking op de eerdere foutgevallen. De
eerste vraag is of verify/4 de oorspronkelijke R9-C5 en R10-C3 afwijst, die
eerdere echte verifiers `supported` noemden. Regels (fail-closed, geen
reparatie, geen herlabeling, geen transformatie):

- **bron** — uitsluitend de bevroren R11-invoer V8 (gepinde hash); de
  answer/2-fixtures of een ander getransformeerd concept komen er niet in;
- **selectie** — exact V-N4 (R9-C5, foutdrager `claim:C5`) en daarna V-N5
  (R10-C3, foutdrager `claim:C3`), in die volgorde. De V-fase verwerkt de items
  in bestandsvolgorde en stopt bij het eerste niet-geaccepteerde item;
- **items** — byte-gelijk aan V8 (geval, materiaal, concept, controles, soort,
  foutdragers, verificatieprompthash en bron met het historische echte
  verifieroordeel). De runner bindt ze bij elke run opnieuw aan de huidige
  code (`valideer_v_invoer`).

    .venv/bin/python scripts/ess05/maak_r12_verificatie_invoer.py [--doel P]

Het doel wordt nooit overschreven; de bron wordt alleen gelezen.
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
import migreer_r7_naar_v2 as mig
from maak_r10_verificatie_invoer import MakerfoutError

__all__ = ["SELECTIE", "MakerfoutError", "maak_verificatie_invoer", "main"]

R11_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260926-R11"
R12_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260926-R12"
V8 = R11_MAP / "verificatie-invoer-v1.json"
V8_SHA256 = "d25bae233b6cc35760c8e86ae3d83b35b262ad0bcc1fa9cb4e864d40fec30164"
GOEDKEURING = (
    PROJECT_ROOT / "logs" / "def768" / "answer2-microproef-goedkeuring-v1.json"
)
DOEL = R12_MAP / "verificatie-invoer-v1.json"
AUTEUR = mk10.AUTEUR
#: (id, foutdrager) in de vaste volgorde: eerst R9-C5, dan R10-C3.
SELECTIE = (("V-N4", "claim:C5"), ("V-N5", "claim:C3"))


def maak_verificatie_invoer(*, v8: Path = V8) -> dict[str, Any]:
    """De twee oorspronkelijke negatieven uit V8, ongewijzigd en in vaste volgorde."""
    bron = json.loads(mk10._gepind(v8, V8_SHA256, "V8"))
    if bron.get("schema") != mig.INVOERSCHEMA or not isinstance(
        bron.get("items"), list
    ):
        msg = f"V8 heeft niet het schema {mig.INVOERSCHEMA}"
        raise MakerfoutError(msg)
    per_id = {item.get("id"): item for item in bron["items"]}
    items = []
    for naam, foutdrager in SELECTIE:
        item = per_id.get(naam)
        if (
            item is None
            or item.get("soort") != "fout"
            or item.get("foutdragende_items") != [foutdrager]
            or item.get("bron", {}).get("historisch_verifieroordeel", {}).get("item")
            != foutdrager
        ):
            msg = f"V8: {naam} is niet het negatieve item met foutdrager {foutdrager}"
            raise MakerfoutError(msg)
        items.append(item)
    return {
        "schema": mig.INVOERSCHEMA,
        "status": (
            "verifier-only-invoer R12 (microproef): V-N4 (R9-C5) en daarna V-N5 "
            "(R10-C3), ongewijzigd uit V8; geen transformatie, geen answer/2-fixture"
        ),
        "herkomst": {
            "r11_verificatie_invoer": {
                "pad": mk10._rel(v8),
                "sha256": V8_SHA256,
                "herkomst": bron["herkomst"],
            },
            "selectie": [naam for naam, _ in SELECTIE],
            "goedkeuring": mk10._rel(GOEDKEURING),
            "regels": "scripts/ess05/maak_r12_verificatie_invoer.py (moduledocstring)",
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
