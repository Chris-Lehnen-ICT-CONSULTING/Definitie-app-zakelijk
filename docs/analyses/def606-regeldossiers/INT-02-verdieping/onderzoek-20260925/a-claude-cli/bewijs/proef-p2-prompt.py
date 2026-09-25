"""Proef P2 (onderzoekslijn A, INT-02): werkelijke rendering in de generatieprompt.

Offline; bouwt de geregistreerde promptmodules met de standaardconfig van
ModularPromptAdapter en legt de relevante regels vast. Geen modelcalls.
Uitvoeren vanuit de repo-root:
    PYTHONPATH=src .venv/bin/python <dit bestand>
"""

import json
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

from services.prompts.modular_prompt_adapter import ModularPromptAdapter
from services.prompts.modules.integrity_rules_module import IntegrityRulesModule

HIER = Path(__file__).resolve().parent
MODULES = ["integrity_rules", "structure_rules", "ess_rules", "arai_rules"]
ZOEK = re.compile(r"indien|mits|tenzij|alleen als|voorwaard|beslisregel|INT-02|ARAI-04|INT-01 |STR-09", re.IGNORECASE)


def main():
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    adapter = ModularPromptAdapter()
    orch = adapter._orchestrator
    geregistreerd = {mid: type(m).__name__ for mid, m in orch.modules.items()}
    ctx = SimpleNamespace(enriched_context=None)
    uitvoer = {}
    for mid in MODULES:
        out = orch.modules[mid].execute(ctx)
        uitvoer[mid] = {
            "success": out.success,
            "metadata": out.metadata,
            "relevante_regels": [r for r in out.content.splitlines() if ZOEK.search(r)],
        }
    int_content = orch.modules["integrity_rules"].execute(ctx).content
    blok = []
    actief = False
    for r in int_content.splitlines():
        if r.startswith("🔹 **INT-02"):
            actief = True
        elif r.startswith("🔹") and actief:
            break
        if actief:
            blok.append(r)
    alle = "\n".join(orch.modules[m].execute(ctx).content for m in orch.modules if hasattr(orch.modules[m], "execute") and m in MODULES)
    resultaat = {
        "commit": commit,
        "include_examples_in_rules": adapter.component_config.include_examples_in_rules,
        "geregistreerde_modules": geregistreerd,
        "integrity_rules_module_geregistreerd": any(isinstance(m, IntegrityRulesModule) for m in orch.modules.values()),
        "dode_toegang_voorbeeld_in_uitvoer": "toestemming verleend door een bevoegde autoriteit" in alle,
        "int02_blok_letterlijk": blok,
        "modules": uitvoer,
    }
    (HIER / "p2-uitkomsten.json").write_text(json.dumps(resultaat, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: resultaat[k] for k in ("include_examples_in_rules", "integrity_rules_module_geregistreerd", "dode_toegang_voorbeeld_in_uitvoer", "int02_blok_letterlijk")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
