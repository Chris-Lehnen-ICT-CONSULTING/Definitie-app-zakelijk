"""Proef C1 (coördinator A/Cowork) — INT-02 op main 26f2374d.

Doel: (a) vastleggen hoe INT-02 werkelijk in de generatieprompt rendert
(JSONBasedRulesModule, prefix INT, met en zonder voorbeelden); (b) het
toetsgedrag van ModularValidationService voor INT-02 op de historische
gevallen C01–C06 en coördinatorgevallen C80–C86 opnieuw meten op main.

Verwachtingen zijn vóór uitvoering vastgelegd in proef-c1-verwachtingen.json.
Offline, synthetisch, geen modelcalls (ai_service=None). Uitvoer:
proef-c1-uitkomsten.json naast dit script. Exitcode 0 = script liep; het
zegt niets over conformiteit — die staat per geval in 'match'.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import types
from datetime import UTC, datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
REPO = Path("/Users/chrislehnen/Projecten/Definitie-app")
sys.path.insert(0, str(REPO / "src"))
os.chdir(REPO)

VERWACHT = json.loads((HIER / "proef-c1-verwachtingen.json").read_text("utf-8"))


def commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO
    ).stdout.strip()


def render_prompt() -> dict:
    from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule

    uit = {}
    for include in (True, False):
        mod = JSONBasedRulesModule(
            rule_prefix="INT",
            module_id="integrity_rules",
            module_name="Integrity Validation Rules (INT)",
            header_emoji="🔒",
            header_text="Integriteit Regels (INT)",
            priority=70,
        )
        mod.initialize({"include_examples": include})
        ctx = types.SimpleNamespace(
            begrip="proef", enriched_context=None, config=None, shared_state={}
        )
        out = mod.execute(ctx)
        regels = out.content.split("\n")
        blok = []
        pak = False
        for r in regels:
            if r.startswith("🔹 **INT-02"):
                pak = True
            elif r.startswith("🔹 **") and pak:
                break
            if pak:
                blok.append(r)
        uit[f"include_examples={include}"] = {
            "success": out.success,
            "rules_count": out.metadata.get("rules_count"),
            "int02_blok": blok,
        }
    return uit


async def toets(gevallen: list[dict]) -> list[dict]:
    from services.validation.modular_validation_service import ModularValidationService
    from toetsregels.manager import get_toetsregel_manager

    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    res = []
    for g in gevallen:
        try:
            r = await svc.validate_definition(
                begrip=g.get("begrip", "proef"),
                text=g["tekst"],
                ontologische_categorie=None,
                context={},
            )
            review = {i["rule_id"]: i for i in r.get("review_required", []) or []}
            item = review.get("INT-02")
            status = (r.get("rule_statuses") or {}).get("INT-02")
            werkelijk = {
                "status_int02": status,
                "in_review_required": item is not None,
                "reason": item.get("reason") if item else None,
                "signals": sorted(item.get("signals") or []) if item else None,
                "in_passed_rules": "INT-02" in (r.get("passed_rules") or []),
                "violation": any(
                    v.get("code") == "INT-02" for v in (r.get("violations") or [])
                ),
                "validation_status": r.get("validation_status"),
            }
            fout = None
        except Exception as e:  # noqa: BLE001
            werkelijk, fout = None, f"{type(e).__name__}: {e}"
        verw = g["verwacht_T_main"]
        match = None
        if werkelijk is not None:
            match = (
                werkelijk["in_review_required"] == verw["in_review_required"]
                and (werkelijk["signals"] or []) == sorted(verw["signals"])
                and werkelijk["violation"] is False
                and werkelijk["in_passed_rules"] is False
            )
        res.append(
            {
                "id": g["id"],
                "tekst": g["tekst"],
                "verwacht_T_main": verw,
                "werkelijk": werkelijk,
                "fout": fout,
                "match": match,
            }
        )
    return res


def main() -> int:
    start = datetime.now(UTC).isoformat()
    uit = {
        "proef": "C1",
        "commit": commit(),
        "python": sys.version.split()[0],
        "start_utc": start,
        "prompt_rendering": render_prompt(),
        "toetsing": asyncio.run(toets(VERWACHT["gevallen"])),
    }
    uit["eind_utc"] = datetime.now(UTC).isoformat()
    uit["samenvatting"] = {
        "gevallen": len(uit["toetsing"]),
        "match": sum(1 for t in uit["toetsing"] if t["match"] is True),
        "mismatch": [t["id"] for t in uit["toetsing"] if t["match"] is False],
        "fouten": [t["id"] for t in uit["toetsing"] if t["fout"]],
    }
    (HIER / "proef-c1-uitkomsten.json").write_text(
        json.dumps(uit, ensure_ascii=False, indent=2), "utf-8"
    )
    print(json.dumps(uit["samenvatting"], ensure_ascii=False))
    for t in uit["toetsing"]:
        print(t["id"], t["match"], t["werkelijk"] and t["werkelijk"]["signals"], t["fout"] or "")
    for k, v in uit["prompt_rendering"].items():
        print(k, v["success"], v["rules_count"])
        for r in v["int02_blok"]:
            print("   ", r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
