"""Gerichte offline meting INT-03 fase 2 (onderzoeker C); geen wijziging van applicatiecode.

Aanroep:
    .venv/bin/python -B <dit bestand> <repo-root> <commit>

Meet de promptomvang van de INT- en SAM-regelmodules zoals de adapter ze
registreert (JSONBasedRulesModule), plus het losse INT-03-blok, ter
onderbouwing van besluitpunt K3/B3/D2. Geen modelcalls, geen productiegegevens.
"""

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
work = offline_bootstrap.session_root() / "int03-onderzoek-c-v2"
work.mkdir()
for name in ("src", "config"):
    (work / name).symlink_to(ROOT / name, target_is_directory=True)
(work / "data").mkdir()
os.chdir(work)
sys.path.insert(0, str(ROOT / "src"))
logging.disable(logging.CRITICAL)

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.prompts.modular_prompt_adapter import (
    get_cached_orchestrator,
)
from services.prompts.modules.base_module import ModuleContext
from services.prompts.modules.json_based_rules_module import (
    JSONBasedRulesModule,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _enriched() -> EnrichedContext:
    return EnrichedContext(
        base_context={
            "organisatorisch": [],
            "juridisch": ["strafrecht"],
            "wettelijk": [],
        },
        sources=[],
        expanded_terms={},
        confidence_scores={},
        metadata={"ontologische_categorie": "type"},
    )


def _int03_blok(tekst: str) -> str:
    regels = tekst.split("\n")
    blok: list[str] = []
    binnen = False
    for regel in regels:
        if regel.startswith("🔹 **INT-03"):
            binnen = True
            blok.append(regel)
            continue
        if binnen:
            if regel.startswith(("🔹", "### ")) or regel.strip() == "":
                break
            blok.append(regel)
    return "\n".join(blok)


def main() -> int:
    verw = json.loads((OUT / "proefverwachtingen-c-v2.json").read_text())[
        "verwachtingen"
    ]
    cfg = UnifiedGeneratorConfig()
    orch = get_cached_orchestrator()
    # Dezelfde instanties als de adapter registreert; initialiseren zoals de
    # adapter dat doet (include_examples=True), plus een variant zonder.
    int_mod = orch.modules["integrity_rules"]
    sam_mod = orch.modules["sam_rules"]
    assert isinstance(int_mod, JSONBasedRulesModule)
    int_mod.initialize({"include_examples": True})
    sam_mod.initialize({"include_examples": True})
    ctx = ModuleContext(
        begrip="context", enriched_context=_enriched(), config=cfg, shared_state={}
    )
    int_out = int_mod.execute(ctx)
    sam_out = sam_mod.execute(ctx)
    blok = _int03_blok(int_out.content)
    # Variant zonder voorbeelden (compact / include_examples_in_rules=False)
    int_mod.initialize({"include_examples": False})
    int_out_zonder = int_mod.execute(ctx)
    int_mod.initialize({"include_examples": True})  # terugzetten voor de singleton

    # De orchestrator voegt module-uitvoer samen met "\n\n" (2 tekens) per
    # module; de meting P05→P06 in proef-c-v1 omvat dus ook die scheidingstekens.
    int_len = len(int_out.content)
    sam_len = len(sam_out.content)
    blok_len = len(blok)
    som = int_len + sam_len
    rows = {
        "int_module_tekens": int_len,
        "int_module_rules_count": int_out.metadata.get("rules_count"),
        "int_module_zonder_voorbeelden_tekens": len(int_out_zonder.content),
        "sam_module_tekens": sam_len,
        "sam_module_rules_count": sam_out.metadata.get("rules_count"),
        "int03_blok_tekens": blok_len,
        "int03_blok": blok,
        "int_plus_sam_tekens": som,
        "verschil_met_p05_p06_uit_v1": 35907 - 28500 - som,
    }
    checks = {
        "int_module_binnen_verwachting": verw["int_module_tekens_min"]
        <= int_len
        <= verw["int_module_tekens_max"],
        "int03_blok_binnen_verwachting": verw["int03_blok_tekens_min"]
        <= blok_len
        <= verw["int03_blok_tekens_max"],
        "int_plus_sam_binnen_tolerantie": abs(som - verw["int_plus_sam_tekens"])
        <= verw["int_plus_sam_tolerantie"],
        "int_rules_count_ok": int_out.metadata.get("rules_count")
        == verw["int_module_rules_count"],
        "sam_rules_count_ok": sam_out.metadata.get("rules_count")
        == verw["sam_module_rules_count"],
        "zonder_voorbeelden_kleiner": len(int_out_zonder.content) < int_len,
    }
    report = {
        "regel": "INT-03",
        "fase": "2",
        "commit": COMMIT,
        "python": sys.version,
        "offline_gate": offline_bootstrap.gate_is_actief(),
        "scope": "moduleomvang INT/SAM via de door de adapter geregistreerde JSONBasedRulesModule-instanties; geen UI, opslag, live model of normvalidatie",
        "code_hashes": {
            f: _sha(ROOT / f)
            for f in (
                "src/services/prompts/modules/json_based_rules_module.py",
                "src/services/prompts/modules/prompt_orchestrator.py",
                "src/services/prompts/modular_prompt_adapter.py",
                "src/toetsregels/regels/INT-03.json",
            )
        },
        "verwachtingen_sha256": _sha(OUT / "proefverwachtingen-c-v2.json"),
        "meting": rows,
        "checks": checks,
        "all_match": all(checks.values()),
    }
    with (OUT / "proefuitkomsten-c-v2.json").open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(
        json.dumps(
            {
                "meting": {k: v for k, v in rows.items() if k != "int03_blok"},
                "checks": checks,
            },
            ensure_ascii=False,
            indent=1,
        )
    )
    return 0 if report["all_match"] else 1


raise SystemExit(main())
