import asyncio, sys
sys.path[:0] = ["src", "tests"]
import offline_bootstrap
offline_bootstrap.install()
import yaml
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

probe = yaml.safe_load(open("tests/fixtures/toetsregels/runtime_cases.yaml", encoding="utf-8"))["INT-02"]["probe"]
res = asyncio.run(ModularValidationService(get_toetsregel_manager(), None, None).validate_definition(
    begrip=probe["begrip"], text=probe["tekst"], ontologische_categorie=None, context=dict(probe.get("context") or {})))
print("probe:", probe)
print("status:", res["rule_statuses"].get("INT-02"))
print("review_required:", [r.get("signals") for r in res["review_required"] if r["rule_id"] == "INT-02"])
print("rule_results:", res["rule_results"].get("INT-02", {}).get("parts"))
