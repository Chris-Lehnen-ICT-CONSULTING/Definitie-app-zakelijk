"""Afgebakende offline onderzoeksproef INT-03 (onderzoeker C); geen wijziging van applicatiecode.

Gebruik: .venv/bin/python <dit bestand> <repo-root> <commit>
(A) INT-03 via ModularValidationService (manager- en cacheroute): status, reden, signalen.
(B) INT-03-promptblok via JSONBasedRulesModule en via de volledige ModularPromptAdapter
    met vier contextvarianten. Geen modelcalls, geen productiedata, verse werkmap.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
COMMIT = sys.argv[2]
OUT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tests import offline_bootstrap

offline_bootstrap.install()
work = offline_bootstrap.session_root() / "int03-onderzoek-c"
work.mkdir()
for name in ("src", "config"):
    (work / name).symlink_to(ROOT / name, target_is_directory=True)
(work / "data").mkdir()
os.chdir(work)
sys.path.insert(0, str(ROOT / "src"))
logging.disable(logging.CRITICAL)

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.prompts.modular_prompt_adapter import ModularPromptAdapter
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.json_based_rules_module import (
    JSONBasedRulesModule,
)
from services.validation.modular_validation_service import (
    ModularValidationService,
)
from toetsregels.cached_manager import CachedToetsregelManager
from toetsregels.manager import ToetsregelManager


def ctx(org=(), jur=(), wet=()):
    return EnrichedContext(
        base_context={
            "organisatorisch": list(org),
            "juridisch": list(jur),
            "wettelijk": list(wet),
        },
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={},
    )


def int03_blok(tekst):
    regels, bezig = [], False
    for regel in tekst.splitlines():
        if regel.startswith("🔹 **INT-03"):
            bezig = True
        elif bezig and (regel.startswith(("🔹", "#"))):
            break
        if bezig:
            regels.append(regel)
    while regels and not regels[-1].strip():
        regels.pop()
    return regels


async def validatie(exp):
    rows = []
    for route, manager in [
        ("manager", ToetsregelManager()),
        ("cache", CachedToetsregelManager()),
    ]:
        svc = ModularValidationService(manager, None, None)
        for c in exp["validatie"]:
            res = await svc.validate_definition(
                begrip=c["begrip"], text=c["tekst"], context={}
            )
            status = res["rule_statuses"].get("INT-03")
            items = [
                r
                for r in res.get("review_required") or []
                if r.get("rule_id") == "INT-03"
            ]
            reden = items[0].get("reason") if items else None
            signalen = list(items[0].get("signals") or []) if items else None
            v = c["verwacht_huidig"]
            match = (
                status == v["status"]
                and (reden == exp["toetsvraag_record"]) == v["reden_is_toetsvraag"]
                and signalen is not None
                and sorted(signalen) == sorted(v["signalen_exact"])
            )
            rows.append(
                {
                    "id": c["id"],
                    "route": route,
                    "status": status,
                    "reden": reden,
                    "signalen": signalen,
                    "aantal_int03_reviewitems": len(items),
                    "verwacht_huidig": v,
                    "verwacht_norm": c["verwacht_norm"],
                    "match_huidig": match,
                }
            )
    return rows


def prompts():
    rows = []
    cfg = UnifiedGeneratorConfig()
    varianten = {"geen": ctx(), "juridisch": ctx(jur=["strafrecht"])}
    blokken = {}
    for label, pid in (("geen", "INT03-C-P01"), ("juridisch", "INT03-C-P02")):
        mod = JSONBasedRulesModule(
            rule_prefix="INT",
            module_id="integrity_rules",
            module_name="Integrity Validation Rules (INT)",
            header_emoji="🔒",
            header_text="Integriteit Regels (INT)",
            priority=70,
        )
        mod.initialize({"include_examples": True})
        out = mod.execute(
            ModuleContext(
                begrip="regeling", enriched_context=varianten[label], config=cfg
            )
        )
        blok = int03_blok(out.content)
        blokken[pid] = blok
        rows.append(
            {
                "id": pid,
                "route": "JSONBasedRulesModule direct",
                "context": label,
                "success": out.success,
                "int03_blok_aanwezig": bool(blok),
                "blok": blok,
            }
        )
    adapter = ModularPromptAdapter()
    orch = adapter._orchestrator
    for pid, label, c in (
        ("INT03-C-P03", "geen", ctx()),
        ("INT03-C-P04", "organisatorisch", ctx(org=["OM"])),
        ("INT03-C-P05", "juridisch", ctx(jur=["strafrecht"])),
        ("INT03-C-P06", "wettelijk", ctx(wet=["Wetboek van Strafvordering"])),
    ):
        actief = orch._get_active_modules(c, cfg)
        fout, prompt = None, ""
        try:
            prompt = adapter.build_prompt("regeling", c, cfg)
        except Exception as e:  # vastleggen, niet verbergen
            fout = f"{type(e).__name__}: {e}"
        blok = int03_blok(prompt)
        rows.append(
            {
                "id": pid,
                "route": "ModularPromptAdapter.build_prompt",
                "context": label,
                "integrity_rules_actief": "integrity_rules" in actief,
                "fout": fout,
                "prompt_lengte": len(prompt),
                "int03_in_prompt": "INT-03" in prompt,
                "blok": blok,
                "blok_gelijk_aan_P01": blok == blokken["INT03-C-P01"],
            }
        )
    return rows


def beoordeel_prompt(exp, rows):
    per_id = {r["id"]: r for r in rows}
    for p in exp["prompt"]:
        r, v = per_id[p["id"]], p["verwacht"]
        checks = []
        if "blok_regels" in v:
            checks.append(r["blok"] == v["blok_regels"])
        for sleutel in (
            "int03_blok_aanwezig",
            "int03_in_prompt",
            "integrity_rules_actief",
            "blok_gelijk_aan_P01",
        ):
            if sleutel in v:
                waarde = r.get(sleutel)
                if sleutel == "blok_gelijk_aan_P01" and "blok_gelijk_aan_P01" not in r:
                    waarde = r["blok"] == per_id["INT03-C-P01"]["blok"]
                checks.append(waarde == v[sleutel])
        r["verwacht"] = v
        r["match"] = all(checks)
    return rows


async def main():
    exp = json.loads((OUT / "proefverwachtingen-c-v1.json").read_text())
    val = await validatie(exp)
    pr = beoordeel_prompt(exp, prompts())
    report = {
        "commit": COMMIT,
        "python": sys.version,
        "offline_gate": offline_bootstrap.gate_is_actief(),
        "commando": f".venv/bin/python {Path(__file__).name} {ROOT} {COMMIT}",
        "scope": "service manager/cache en promptbouw; geen UI, opslag, live model of normvalidatie",
        "validatie": val,
        "prompt": pr,
        "alle_verwachtingen_gehaald": all(r["match_huidig"] for r in val)
        and all(r["match"] for r in pr),
    }
    with (OUT / "proefuitkomsten-c-v1.json").open("x") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(
        json.dumps(
            {
                "alle": report["alle_verwachtingen_gehaald"],
                "val": [
                    (r["id"], r["route"], r["status"], r["match_huidig"]) for r in val
                ],
                "prompt": [(r["id"], r["match"]) for r in pr],
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["alle_verwachtingen_gehaald"] else 1


raise SystemExit(asyncio.run(main()))
