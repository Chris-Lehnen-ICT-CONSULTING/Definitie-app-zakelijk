"""Afgebakende offline onderzoeksproef INT-03 (onderzoeker C); geen wijziging van applicatiecode.

Aanroep:
    .venv/bin/python -B <dit bestand> <repo-root> <commit>

Route A: ModularValidationService (manager- en cachepad) voor de gevallen uit
proefverwachtingen-c-v1.json → status, reden en signalen van INT-03.
Route B: het live INT-03-promptblok via JSONBasedRulesModule (met/zonder
context, met/zonder voorbeelden) en de aanwezigheid van INT-03 in de
volledige ModularPromptAdapter-prompt per contextvariant.

Geen live modelcalls, geen productiegegevens, geen brede testsuite. De
DEF-519-offline-gate (tests/offline_bootstrap.py) blokkeert netwerk en
repositorydata.
"""

import asyncio
import hashlib
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
from services.prompts.modular_prompt_builder import PromptComponentConfig
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.json_based_rules_module import (
    JSONBasedRulesModule,
)
from services.validation.modular_validation_service import (
    ModularValidationService,
)
from toetsregels.cached_manager import get_cached_toetsregel_manager
from toetsregels.manager import ToetsregelManager
from toetsregels.rule_cache import get_rule_cache

RULE = "INT-03"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _enriched(base: dict[str, list[str]]) -> EnrichedContext:
    volledig = {"organisatorisch": [], "juridisch": [], "wettelijk": []}
    volledig.update(base)
    return EnrichedContext(
        base_context=volledig,
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={"ontologische_categorie": "type"},
    )


def _int03_blok(tekst: str) -> list[str]:
    """De regels van het INT-03-blok: vanaf de INT-03-kop tot de volgende 🔹-kop."""
    regels = tekst.split("\n")
    blok: list[str] = []
    binnen = False
    for regel in regels:
        if regel.startswith("🔹 **INT-03"):
            binnen = True
            blok.append(regel)
            continue
        if binnen:
            if regel.startswith(("🔹", "### ")):
                break
            if regel.strip() == "":
                break
            blok.append(regel)
    return blok


async def route_a(verw: dict) -> list[dict]:
    rows: list[dict] = []
    get_rule_cache().clear_cache()  # geen stale FileCache-entries (DEF-750-les)
    for route, manager in [
        ("manager", ToetsregelManager()),
        ("cache", get_cached_toetsregel_manager()),
    ]:
        svc = ModularValidationService(manager, None, None)
        for c in verw["route_a_validatie"]:
            result = await svc.validate_definition(
                begrip=c["term"], text=c["text"], context={}
            )
            status = result.get("rule_statuses", {}).get(RULE)
            reviews = [
                r for r in result.get("review_required", []) if r.get("rule_id") == RULE
            ]
            violations = [
                v
                for v in result.get("violations", [])
                if str(v.get("code") or v.get("rule_id") or "").upper() == RULE
            ]
            reden = reviews[0].get("reason") if reviews else None
            signalen = list(reviews[0].get("signals", [])) if reviews else []
            matches = (
                status == c["expected_status"]
                and signalen == c["expected_signals"]
                and reden == verw["toetsvraag_record"]
                and not violations
            )
            rows.append(
                {
                    "id": c["id"],
                    "historisch": bool(c.get("historisch")),
                    "route": route,
                    "term": c["term"],
                    "text": c["text"],
                    "status": status,
                    "reason": reden,
                    "signals": signalen,
                    "violations_int03": len(violations),
                    "validation_status": result.get("validation_status"),
                    "expected_status": c["expected_status"],
                    "expected_signals": c["expected_signals"],
                    "matches": matches,
                }
            )
    return rows


def route_b(verw: dict) -> list[dict]:
    rows: list[dict] = []
    cfg = UnifiedGeneratorConfig()

    def module(include_examples: bool) -> JSONBasedRulesModule:
        m = JSONBasedRulesModule(
            rule_prefix="INT",
            module_id="integrity_rules",
            module_name="Integrity Validation Rules (INT)",
            header_emoji="🔒",
            header_text="Integriteit Regels (INT)",
            priority=70,
        )
        m.initialize({"include_examples": include_examples})
        return m

    def render(m: JSONBasedRulesModule, enriched: EnrichedContext) -> dict:
        ctx = ModuleContext(
            begrip="context", enriched_context=enriched, config=cfg, shared_state={}
        )
        out = m.execute(ctx)
        return {
            "success": out.success,
            "content": out.content,
            "metadata": out.metadata,
        }

    p = {e["id"]: e for e in verw["route_b_prompt"]}

    # P01: module zonder context, met voorbeelden
    r1 = render(module(True), _enriched({}))
    blok1 = _int03_blok(r1["content"])
    rows.append(
        {
            "id": "INT03-C-P01",
            "blok": blok1,
            "rules_count": r1["metadata"].get("rules_count"),
            "matches": blok1 == p["INT03-C-P01"]["expected_lines"],
        }
    )
    # P02: module met juridische context
    r2 = render(module(True), _enriched({"juridisch": ["strafrecht"]}))
    blok2 = _int03_blok(r2["content"])
    rows.append({"id": "INT03-C-P02", "blok": blok2, "matches": blok2 == blok1})
    # P03: module zonder voorbeelden
    r3 = render(module(False), _enriched({}))
    blok3 = _int03_blok(r3["content"])
    rows.append(
        {
            "id": "INT03-C-P03",
            "blok": blok3,
            "matches": blok3 == p["INT03-C-P03"]["expected_lines"],
        }
    )

    # P04–P07: volledige adapterprompt per contextvariant
    adapter = ModularPromptAdapter(PromptComponentConfig())
    varianten = [
        ("INT03-C-P04", {}),
        ("INT03-C-P05", {"organisatorisch": ["Prisma"]}),
        ("INT03-C-P06", {"juridisch": ["strafrecht"]}),
        ("INT03-C-P07", {"wettelijk": ["Wetboek van Strafrecht"]}),
    ]
    for pid, base in varianten:
        prompt = adapter.build_prompt("context", _enriched(base), cfg)
        meta = adapter.get_component_metadata().get("last_execution", {})
        skipped = list(meta.get("skipped_modules", []))
        aanwezig = "INT-03" in prompt
        blok = _int03_blok(prompt)
        exp = p[pid]
        matches = aanwezig == exp["expected_int03_present"] and all(
            s in skipped for s in exp["expected_skipped_contains"]
        )
        if exp["expected_int03_present"]:
            matches = matches and blok == blok1 and "integrity_rules" not in skipped
        rows.append(
            {
                "id": pid,
                "base_context": base,
                "int03_present": aanwezig,
                "skipped_modules": skipped,
                "prompt_length": len(prompt),
                "blok": blok,
                "matches": matches,
            }
        )
    return rows


async def main() -> int:
    verw = json.loads((OUT / "proefverwachtingen-c-v1.json").read_text())
    rows_a = await route_a(verw)
    rows_b = route_b(verw)
    code_files = [
        "src/toetsregels/regels/INT-03.json",
        "src/services/validation/evaluators/judgment_review.py",
        "src/validation/additional_patterns.py",
        "src/services/validation/modular_validation_service.py",
        "src/services/prompts/modules/json_based_rules_module.py",
        "src/services/prompts/modules/prompt_orchestrator.py",
        "src/services/prompts/modular_prompt_adapter.py",
    ]
    report = {
        "regel": RULE,
        "commit": COMMIT,
        "python": sys.version,
        "offline_gate": offline_bootstrap.gate_is_actief(),
        "scope": (
            "route A: service manager/cache, context={}; route B: promptmodule en "
            "adapterprompt; geen UI, opslag, live model of normvalidatie"
        ),
        "code_hashes": {f: _sha(ROOT / f) for f in code_files},
        "verwachtingen_sha256": _sha(OUT / "proefverwachtingen-c-v1.json"),
        "route_a": rows_a,
        "route_b": rows_b,
        "route_a_all_match": all(r["matches"] for r in rows_a),
        "route_b_all_match": all(r["matches"] for r in rows_b),
    }
    with (OUT / "proefuitkomsten-c-v1.json").open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    samenvatting = {
        "route_a": [(r["id"], r["route"], r["status"], r["matches"]) for r in rows_a],
        "route_b": [(r["id"], r["matches"]) for r in rows_b],
    }
    print(json.dumps(samenvatting, ensure_ascii=False, indent=1))
    return 0 if report["route_a_all_match"] and report["route_b_all_match"] else 1


raise SystemExit(asyncio.run(main()))
