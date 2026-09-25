"""Kleine offline onderzoeksproef INT-03; schrijft geen applicatiebestanden."""

import asyncio
import hashlib
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(sys.argv[1]).resolve()
OUT = Path(__file__).resolve().parent
VERWACHTINGEN = OUT / "proefverwachtingen-b-v1.json"
verwachtingen = json.loads(VERWACHTINGEN.read_text())
sys.path.insert(0, str(ROOT))
from tests import offline_bootstrap

offline_bootstrap.install()
werk = offline_bootstrap.session_root() / "int03-b"
werk.mkdir()
for naam in ("src", "config"):
    (werk / naam).symlink_to(ROOT / naam, target_is_directory=True)
(werk / "data").mkdir()
os.chdir(werk)
sys.path.insert(0, str(ROOT / "src"))
logging.disable(logging.CRITICAL)

from services.definition_generator_config import UnifiedGeneratorConfig
from services.definition_generator_context import EnrichedContext
from services.prompts.modular_prompt_adapter import ModularPromptAdapter
from services.prompts.modules.base_module import ModuleContext
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.cached_manager import CachedToetsregelManager
from toetsregels.manager import ToetsregelManager


def blok(tekst):
    regels = tekst.splitlines()
    for i, regel in enumerate(regels):
        if regel.startswith("🔹 **INT-03 -"):
            einde = next(
                (j for j in range(i + 1, len(regels)) if regels[j].startswith("🔹 **")),
                len(regels),
            )
            return "\n".join(regels[i:einde]).rstrip("\n")
    return None


async def main():
    rijen = []
    for route, manager in (
        ("manager", ToetsregelManager()),
        ("cache", CachedToetsregelManager()),
    ):
        service = ModularValidationService(manager, None, None)
        for geval in verwachtingen["gevallen"]:
            if not geval["uitvoeren"]:
                continue
            resultaat = await service.validate_definition(
                begrip=geval["begrip"], text=geval["tekst"], context={}
            )
            reviews = [
                item
                for item in resultaat.get("review_required", [])
                if item["rule_id"] == "INT-03"
            ]
            werkelijk = {
                "status": resultaat["rule_statuses"].get("INT-03"),
                "reden": reviews[0]["reason"] if reviews else None,
                "signalen": reviews[0]["signals"] if reviews else None,
            }
            rijen.append(
                {
                    "id": geval["id"],
                    "route": route,
                    "invoer": {
                        "begrip": geval["begrip"],
                        "text": geval["tekst"],
                        "context": {},
                    },
                    "verwacht": geval["verwacht_huidig"],
                    "werkelijk": werkelijk,
                    "overeenkomst": werkelijk == geval["verwacht_huidig"],
                    "review_items": reviews,
                    "int03_violations": [
                        v
                        for v in resultaat.get("violations", [])
                        if v.get("rule_id") == "INT-03"
                    ],
                    "int03_geslaagd": "INT-03" in resultaat.get("passed_rules", []),
                    "buurstatussen": {
                        k: resultaat["rule_statuses"].get(k)
                        for k in ("INT-01", "ARAI-05", "CON-CIRC-001", "VAL-EMP-001")
                    },
                }
            )
    adapter = ModularPromptAdapter()
    module = adapter._orchestrator.modules["integrity_rules"]
    configuratie = UnifiedGeneratorConfig()
    prompts = []
    for variant in verwachtingen["promptverwachtingen"]["contexten"]:
        context = EnrichedContext(
            base_context=variant["base_context"],
            sources=[],
            expanded_terms={},
            confidence_scores={},
            metadata={},
        )
        module_resultaat = module.execute(
            ModuleContext("context", context, configuratie)
        )
        volledig = adapter.build_prompt("context", context, configuratie)
        moduleblok = blok(module_resultaat.content)
        adapterblok = blok(volledig)
        prompts.append(
            {
                "id": variant["id"],
                "invoer": variant,
                "moduleklasse": type(module).__name__,
                "module_metadata": module_resultaat.metadata,
                "exact_moduleblok": moduleblok,
                "exact_adapterblok": adapterblok,
                "volledige_adapterprompt_sha256": hashlib.sha256(
                    volledig.encode()
                ).hexdigest(),
                "volledige_adapterprompt_tekens": len(volledig),
                "overeenkomst": bool(moduleblok)
                and (bool(adapterblok) == variant["adapter_int03"]),
            }
        )
    zelfde = len({p["exact_moduleblok"] for p in prompts}) == 1
    commit = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    geslaagd = (
        all(r["overeenkomst"] for r in rijen + prompts)
        and zelfde
        and commit == verwachtingen["commit"]
    )
    rapport = {
        "commit": commit,
        "python": sys.version,
        "python_executable": sys.executable,
        "offline_gate": offline_bootstrap.installatie_rapport(),
        "stubs": "Geen modelresponsstubs; geen cleaning-service of repository geïnjecteerd; bootstrap neutraliseert sleutels en blokkeert netwerk/gebruikersdatabases.",
        "verwachtingen_sha256": hashlib.sha256(VERWACHTINGEN.read_bytes()).hexdigest(),
        "scope": "Service manager/cache en echte module/adapterpromptbouw; geen UI, opslag of modelkwaliteit.",
        "service": rijen,
        "prompts": prompts,
        "zelfde_moduleblok": zelfde,
        "alle_runtimeverwachtingen_uitgekomen": geslaagd,
    }
    print(json.dumps(rapport, ensure_ascii=False))
    return 0 if geslaagd else 1


raise SystemExit(asyncio.run(main()))
