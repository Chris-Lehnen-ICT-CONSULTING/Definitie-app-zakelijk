"""Proef P3 (onderzoekslijn A, review op B): INT-10/INT-01-melding bij 'indien'.

Verwachting vooraf (vastgelegd in dit docstring vóór uitvoering, 25-09-2026):
- C04 ("Getal dat even is indien het zonder rest door twee deelbaar is.")
  geeft een INT-10-violation met een generieke meldingstekst die niets over
  achtergrondkennis zegt maar op het patroon 'indien' berust; C05 (zelfde
  criterium zonder 'indien') geeft geen INT-10-violation.
- De severity van die violation is niet 'critical' (onzeker; te meten), dus
  de vaststelgate-regel 'Kritieke issues aanwezig' wordt vermoedelijk niet
  geraakt.
Grond: INT-10.json:15 (\\bindien\\b, generic/automated/scored); P1-uitkomst.
Offline, synthetisch, geen modelcalls. Uitvoeren vanuit repo-root:
    PYTHONPATH=src .venv/bin/python <dit bestand>
"""

import asyncio
import json
import subprocess
from pathlib import Path

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

HIER = Path(__file__).resolve().parent
CTX = {"organisatorische_context": ["Synthetische wiskundeles"]}
CASUSSEN = [
    ("INT02-C04", "even getal", "Getal dat even is indien het zonder rest door twee deelbaar is."),
    ("INT02-C05", "even getal", "Geheel getal dat zonder rest door twee deelbaar is."),
]


async def draai():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    uit = []
    for cid, begrip, tekst in CASUSSEN:
        res = await svc.validate_definition(begrip=begrip, text=tekst, ontologische_categorie=None, context=dict(CTX))
        viol = [v for v in res.get("violations") or [] if str(v.get("code") or v.get("rule_id")) in ("INT-10", "INT-01")]
        uit.append({"id": cid, "tekst": tekst, "context": CTX, "int10_int01_violations": viol,
                    "rule_statuses": {k: (res.get("rule_statuses") or {}).get(k) for k in ("INT-02", "INT-10", "INT-01")}})
    return uit


def main():
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    uit = asyncio.run(draai())
    (HIER / "p3-uitkomsten.json").write_text(json.dumps({"commit": commit, "uitkomsten": uit}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(uit, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
