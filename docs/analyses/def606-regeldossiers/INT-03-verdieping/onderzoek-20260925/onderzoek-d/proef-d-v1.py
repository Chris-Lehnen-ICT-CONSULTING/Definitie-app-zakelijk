"""Kleine offline nulmeting van INT-03; wijzigt uitsluitend eigen proefwerkmap."""

import asyncio
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
commit = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
).strip()
expectations = json.loads((OUT / "proefverwachtingen-d-v1.json").read_text())
assert commit == expectations["commit"]


def audit(event, args):
    if event == "open" and not isinstance(args[0], int):
        mode, flags = args[1], args[2]
        writes = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int)
            and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        )
        if writes and not Path(args[0]).resolve().is_relative_to(OUT):
            raise PermissionError(
                "Proef mag niet schrijven buiten onderzoek-d: " + str(args[0])
            )


sys.addaudithook(audit)
from tests import offline_bootstrap

runtime = offline_bootstrap.install(OUT / ".offline-runtime-d-v1")
work = runtime / "werk"
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
from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.cached_manager import CachedToetsregelManager
from toetsregels.manager import ToetsregelManager


def block(text):
    match = re.search(r"🔹 \*\*INT-03[^\n]*\n.*?(?=\n🔹 \*\*|\n###|\Z)", text, re.S)
    return match.group(0) if match else None


async def main():
    rows = []
    for route, manager in [
        ("manager", ToetsregelManager()),
        ("cache", CachedToetsregelManager()),
    ]:
        service = ModularValidationService(manager, None, None)
        for case in expectations["casussen"]:
            if not case["uitvoeren"]:
                continue
            result = await service.validate_definition(
                begrip=case["term"], text=case["text"], context={}
            )
            reviews = [
                r
                for r in result.get("review_required", [])
                if r.get("rule_id") == "INT-03"
            ]
            observed = {
                "status": result["rule_statuses"].get("INT-03"),
                "reason": reviews[0]["reason"] if reviews else None,
                "signals": reviews[0]["signals"] if reviews else None,
            }
            rows.append(
                {
                    "id": case["id"],
                    "route": route,
                    "invoer": {
                        "term": case["term"],
                        "text": case["text"],
                        "context": {},
                    },
                    "verwacht": case["verwacht_huidig"],
                    "werkelijk": observed,
                    "gelijk_aan_verwachting": observed == case["verwacht_huidig"],
                    "reviews": reviews,
                    "rule_result": result.get("rule_results", {}).get("INT-03"),
                    "rule_score": result.get("rule_scores", {}).get("INT-03"),
                    "buurstatussen": {
                        k: result["rule_statuses"].get(k)
                        for k in ("INT-01", "ARAI-05", "CON-CIRC-001", "VAL-EMP-001")
                    },
                    "runstatus": result.get("validation_status"),
                }
            )
    prompts = []
    config = UnifiedGeneratorConfig()
    module = JSONBasedRulesModule(
        "INT",
        "integrity_rules",
        "Integrity Validation Rules (INT)",
        "🔒",
        "Integriteit Regels (INT)",
        70,
    )
    module.initialize({"include_examples": True})
    adapter = ModularPromptAdapter()
    for case in expectations["promptverwachtingen"]:
        context = EnrichedContext(
            base_context=case["context"],
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},
        )
        rendered = module.execute(ModuleContext("proefbegrip", context, config))
        prompt = adapter.build_prompt("proefbegrip", context, config)
        observed = {
            "module_INT03": block(rendered.content) is not None,
            "adapter_INT03": block(prompt) is not None,
        }
        prompts.append(
            {
                "id": case["id"],
                "invoer": case["context"],
                "verwacht": {k: case[k] for k in observed},
                "werkelijk": observed,
                "gelijk_aan_verwachting": all(observed[k] == case[k] for k in observed),
                "module_success": rendered.success,
                "module_metadata": rendered.metadata,
                "module_INT03_exact": block(rendered.content),
                "module_content_exact": rendered.content,
                "adapter_INT03_exact": block(prompt),
                "adapter_prompt_exact": prompt,
                "adapter_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "adapter_lengte": len(prompt),
            }
        )
    ok = all(r["gelijk_aan_verwachting"] for r in rows + prompts)
    report = {
        "commit": commit,
        "python": sys.version,
        "executable": sys.executable,
        "offline_gate": offline_bootstrap.installatie_rapport(),
        "stubs": [],
        "verwachtingen_sha256": hashlib.sha256(
            (OUT / "proefverwachtingen-d-v1.json").read_bytes()
        ).hexdigest(),
        "scope": "Service manager/cache en echte promptmodule/adapter; geen modelcall, UI-bediening, opslag of herstelproef",
        "service": rows,
        "prompts": prompts,
        "alle_verwachtingen_uitgekomen": ok,
        "geladen_legacy_INT03": any(
            n.endswith(("INT_03", "INT-03")) for n in sys.modules
        ),
    }
    print(json.dumps(report, ensure_ascii=False))
    return 0 if ok else 1


raise SystemExit(asyncio.run(main()))
