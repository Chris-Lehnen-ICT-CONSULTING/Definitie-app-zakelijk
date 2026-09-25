"""DEF-770: offline serviceproef na implementatie; geen wijziging van applicatiecode.

Zelfde zes gevallen als de nulmeting van onderzoek A (proefverwachtingen-v1,
commit 26f2374d) plus vier ontwerpgevallen (E07, E08, EB03, EB04), via beide
laadpaden (ToetsregelManager en CachedToetsregelManager). Anders dan de
nulmeting legt deze proef naast de status ook reden, passage en positie vast.
De verwachtingen staan hieronder vóór de uitvoering en komen uit synthese v3;
de ontwerpgevallen zijn regressiemateriaal, geen ongeziene eindset.

Aanroep vanuit de repositorywortel:
    <python> -B docs/analyses/.../proef-na-implementatie-v1.py <uitvoerpad.json>
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
UIT = Path(sys.argv[1]).resolve()
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tests import offline_bootstrap

offline_bootstrap.install()
werk = offline_bootstrap.session_root() / "int01-na-implementatie"
werk.mkdir()
for naam in ("src", "config"):
    (werk / naam).symlink_to(ROOT / naam, target_is_directory=True)
(werk / "data").mkdir()
os.chdir(werk)
sys.path.insert(0, str(ROOT / "src"))
logging.disable(logging.CRITICAL)

from services.validation.modular_validation_service import (
    ModularValidationService,
)
from toetsregels.cached_manager import CachedToetsregelManager
from toetsregels.manager import ToetsregelManager

ASTRA = (
    "eis die een organisatie moet ondersteunen om migratie van de huidige naar "
    "de toekomstige situatie mogelijk te maken."
)
GEVALLEN = [
    # id, begrip, tekst, nulmeting-status (A), verwachte status na DEF-770
    ("INT01-E01", "transitie-eis", ASTRA, "fail", "review_required"),
    ("INT01-E02", "object", "Object dat gegevens bevat.", "pass", "review_required"),
    ("INT01-E03", "object", "Object die gegevens bevat.", "fail", "review_required"),
    (
        "INT01-E04",
        "document",
        "Document op naam van dr. Smit.",
        "fail",
        "review_required",
    ),
    ("INT01-E05", "object", "Wat is dit? Afgebakend object.", "pass", "fail"),
    ("INT01-E06", "object", "Afgebakend object. Heeft vaste vorm.", "fail", "fail"),
    (
        "INT01-E07",
        "veelhoek",
        "Veelhoek met precies\ndrie zijden.",
        None,
        "review_required",
    ),
    ("INT01-E08", "object", "“Afgebakend object. Heeft vaste vorm.”", None, "fail"),
    (
        "INT01-EB03",
        "object",
        "Object met gegevens enz. Het wordt geregistreerd.",
        None,
        "review_required",
    ),
    (
        "INT01-EB04",
        "voertuig",
        "Voertuig voor personenvervoer. Het heeft ten hoogste acht zitplaatsen.",
        None,
        "fail",
    ),
]


def _rij(geval: tuple, route: str, res: dict) -> dict:
    gid, _, tekst, nul, verwacht = geval
    status = res["rule_statuses"].get("INT-01")
    violations = [v for v in res["violations"] if v.get("code") == "INT-01"]
    review = [r for r in res["review_required"] if r["rule_id"] == "INT-01"]
    detail = res["rule_results"].get("INT-01") or {}
    return {
        "id": gid,
        "route": route,
        "tekst": tekst,
        "nulmeting_status": nul,
        "verwacht": verwacht,
        "status": status,
        "matches": status == verwacht,
        "in_passed_rules": "INT-01" in res["passed_rules"],
        "melding": violations[0]["message"] if violations else None,
        "suggestie": violations[0].get("suggestion") if violations else None,
        "reviewreden": review[0]["reason"] if review else None,
        "onderdelen": [
            {k: p[k] for k in ("id", "status", "evidence", "position", "reason")}
            for p in detail.get("parts", [])
        ],
    }


async def main() -> int:
    rijen = []
    for route, manager in (
        ("manager", ToetsregelManager()),
        ("cache", CachedToetsregelManager()),
    ):
        svc = ModularValidationService(manager, None, None)
        for geval in GEVALLEN:
            res = await svc.validate_definition(
                begrip=geval[1], text=geval[2], context={}
            )
            rijen.append(_rij(geval, route, res))
    rapport = {
        "basis": "26f2374d302fc66fc0b12ed29dc34585f7c0a5c3 + niet-gecommitte DEF-770-diff",
        "python": sys.version,
        "offline_gate": offline_bootstrap.gate_is_actief(),
        "scope": "service manager/cache; geen UI, opslag, live model of normvalidatie",
        "rows": rijen,
        "alle_verwachtingen_gehaald": all(r["matches"] for r in rijen),
        "nooit_int01_in_passed_rules": not any(r["in_passed_rules"] for r in rijen),
    }
    with UIT.open("x", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    ok = (
        rapport["alle_verwachtingen_gehaald"] and rapport["nooit_int01_in_passed_rules"]
    )
    return 0 if ok else 1


raise SystemExit(asyncio.run(main()))
