"""Besluit 22 — inventaris van de bewaarde antwoorden (v8, v9, variatiemeting v9).

Hulpscript, geen onderdeel van de testsuite; draai met
`python -m pytest -s <dit bestand>`. Leest alleen de bundels en resultaten van
v8/v9 (ontwikkeling en regressie) en `variatiemeting-v9/live-v1/calls.jsonl`;
geen hold-out, geen netwerk.
"""

import json
from pathlib import Path

G = Path(__file__).resolve().parents[2]


def test_inventaris():
    tekst = (G / "variatiemeting-v9/live-v1/calls.jsonl").read_text("utf-8")
    rs = [json.loads(r) for r in tekst.splitlines()]
    print(sorted(rs[0].keys()))
    print(type(rs[0]["ruw_antwoord"]), str(rs[0]["ruw_antwoord"])[:300])
    for r in rs:
        if r["geval"] in ("G021", "G045", "G050", "G055", "G060"):
            vormen = [
                (p["kernvorm"], [b["function"] for b in p["bronfuncties"]])
                for p in r["passages"]
            ]
            print("  ", r["call"], r["geval"], r["status"], r["uncertainty"], vormen)
    for r in rs:
        print(
            r["call"],
            r["herhaling"],
            r["geval"],
            r["label"],
            r.get("status"),
            r["afleiding"],
            r["modelverdict"],
            r["omzetting"],
        )
    for f in ["kwalificatieproef-v8", "kwalificatieproef-v9"]:
        for s in ["ontwikkeling", "regressie"]:
            pad = G / "goldset-freeze-v1" / f
            b = json.loads((pad / f"{s}-bundel.json").read_text())
            r = json.loads((pad / f"{s}-resultaat.json").read_text())
            print(f, s, sorted(b.keys()), sorted(r.keys()), len(r["gevallen"]))
            print("   ", sorted(r["gevallen"][0].keys()))
            for g in r["gevallen"]:
                print(
                    "   ", g["id"], g["status"], g.get("afleiding"), g.get("omzetting")
                )
