"""Inventaris van de 24 ontwikkelgevallen voor de paper test (alleen ontwikkeling-v1.json).

Leest uitsluitend `goldset-freeze-v1/ontwikkeling-v1.json` (geen hold-out).
Toont per geval: label, bedoeling bekend, bron-ID's, contextaantallen en de
labelpassages (citaat) met hun aantal voorkomens in de kern.
"""

import json
import sys
from pathlib import Path

PAD = Path(sys.argv[1])
data = json.loads(PAD.read_text(encoding="utf-8"))
for g in data["gevallen"]:
    geval, label = g["geval"], g["label"]
    ctx = geval["context"]
    passages = [
        (p["citaat"], geval["kern"].count(p["citaat"])) for p in label["passages"]
    ]
    print(
        g["id"],
        label["status"],
        "bedoeling" if geval["bedoeling"] is not None else "GEEN-bedoeling",
        [b["id"] for b in geval["bronnen"]],
        {k: len(v) for k, v in ctx.items()},
        passages,
    )
