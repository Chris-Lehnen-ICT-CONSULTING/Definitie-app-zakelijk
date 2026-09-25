"""INT-03 offline proef onderzoeker A (Cowork), 25-09-2026. Geen wijziging van applicatiecode.
Aanroep: cd <repo> && .venv/bin/python docs/.../onderzoek-a/proef-a-v1.py <repo> <commit>
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(sys.argv[1]).resolve()
COMMIT = sys.argv[2]
OUT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tests import offline_bootstrap

offline_bootstrap.install()
work = offline_bootstrap.session_root() / "int03-a"
work.mkdir()
for name in ("src", "config"):
    (work / name).symlink_to(ROOT / name, target_is_directory=True)
(work / "data").mkdir()
os.chdir(work)
sys.path.insert(0, str(ROOT / "src"))
logging.disable(logging.CRITICAL)

from services.definition_generator_context import EnrichedContext
from services.prompts.modular_prompt_adapter import get_cached_orchestrator
from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.cached_manager import CachedToetsregelManager
from toetsregels.manager import ToetsregelManager

spec = json.loads((OUT / "proefverwachtingen-a-v1.json").read_text())


def norm_sig(s):
    return "additional:deze|dit|die|daarvan" if "(?!" in s else s


async def validatie():
    rows = []
    for route, manager in [
        ("manager", ToetsregelManager()),
        ("cache", CachedToetsregelManager()),
    ]:
        svc = ModularValidationService(manager, None, None)
        for c in spec["cases"]:
            r = await svc.validate_definition(
                begrip=c["term"], text=c["text"], context={}
            )
            status = r["rule_statuses"].get("INT-03")
            rr = [
                x
                for x in (r.get("review_required") or [])
                if x.get("rule_id") == "INT-03"
            ]
            reason = rr[0]["reason"] if rr else None
            signals = (
                sorted(norm_sig(s) for s in (rr[0].get("signals") or [])) if rr else []
            )
            rows.append(
                {
                    "id": c["id"],
                    "route": route,
                    "status": status,
                    "reason": reason,
                    "signals": signals,
                    "huidig_verwacht": c["huidig_verwacht"],
                    "signalen_verwacht": sorted(c["signalen_verwacht"]),
                    "status_ok": status == c["huidig_verwacht"],
                    "signalen_ok": signals == sorted(c["signalen_verwacht"]),
                    "violation_INT03": any(
                        v.get("rule_id") == "INT-03"
                        for v in (r.get("violations") or [])
                    ),
                }
            )
    return rows


def prompt():
    mgr = CachedToetsregelManager()
    regel = mgr.get_all_regels()["INT-03"]
    mod = JSONBasedRulesModule(
        rule_prefix="INT",
        module_id="integrity_rules",
        module_name="x",
        header_emoji="🔒",
        header_text="Integriteit Regels (INT)",
        priority=70,
    )
    mod.initialize({})
    blok = "\n".join(mod._format_rule("INT-03", regel))
    mod2 = JSONBasedRulesModule(
        rule_prefix="INT",
        module_id="integrity_rules",
        module_name="x",
        header_emoji="🔒",
        header_text="Integriteit Regels (INT)",
        priority=70,
    )
    mod2.initialize({"include_examples": False})
    blok_zonder = "\n".join(mod2._format_rule("INT-03", regel))
    orch = get_cached_orchestrator()

    def ctx(base):
        return EnrichedContext(
            base_context=base,
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},
        )

    cfg = SimpleNamespace(debug_mode=False, include_metrics=False)
    actief = {}
    for naam, base in [
        ("geen_context", {}),
        ("alleen_organisatorisch", {"organisatorisch": ["OM"]}),
        ("juridisch", {"juridisch": ["strafrecht"]}),
        ("wettelijk", {"wettelijk": ["Sv"]}),
    ]:
        a = orch._get_active_modules(ctx(base), cfg)
        actief[naam] = {
            "integrity_rules_actief": "integrity_rules" in a,
            "actief": sorted(a),
        }
    return {
        "blok_met_voorbeelden": blok,
        "blok_zonder_voorbeelden": blok_zonder,
        "actieve_modules": actief,
        "geregistreerd": sorted(orch.modules.keys()),
    }


def statisch():
    hits = {
        "IntegrityRulesModule(": [],
        "json_validator_loader": [],
        "validators.INT_03": [],
        "regels.INT-03": [],
    }
    for p in (ROOT / "src").rglob("*.py"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        for k, gevonden in hits.items():
            if k in t:
                gevonden.append(str(p.relative_to(ROOT)))
    return hits


async def main():
    rows = await validatie()
    rep = {
        "commit": COMMIT,
        "python": sys.version.split()[0],
        "offline_gate": offline_bootstrap.gate_is_actief(),
        "scope": "service (manager+cache), promptmodule-render, orchestrator-moduleselectie, statische import-scan; geen UI, opslag, live model, normvalidatie",
        "validatie": rows,
        "prompt": prompt(),
        "statisch": statisch(),
    }
    (OUT / "proefuitkomsten-a-v1.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2)
    )
    ok = all(r["status_ok"] and r["signalen_ok"] for r in rows)
    print(
        json.dumps(
            {
                "status_ok_all": all(r["status_ok"] for r in rows),
                "signalen_ok_all": all(r["signalen_ok"] for r in rows),
                "afwijkingen": [
                    (r["id"], r["route"], r["status"], r["signals"])
                    for r in rows
                    if not (r["status_ok"] and r["signalen_ok"])
                ],
                "actief": {
                    k: v["integrity_rules_actief"]
                    for k, v in rep["prompt"]["actieve_modules"].items()
                },
                "statisch": rep["statisch"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if ok else 1


raise SystemExit(asyncio.run(main()))
