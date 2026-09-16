"""ESS-01: echte service/cache/renderer, geen semantische modelkwaliteitsclaim."""

import pytest

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.cached_manager import get_cached_toetsregel_manager
from toetsregels.manager import get_toetsregel_manager
from toetsregels.rule_cache import get_rule_cache
from ui.components import validation_view
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize("cached", [False, True])
@pytest.mark.parametrize(
    ("tekst", "fragment"),
    [
        ("activiteit In Het Kader Van uitvoering", "In Het Kader Van"),
        ("instrument bedoeld om temperatuur te meten", "bedoeld om"),
        ("behoefte of eis van een belanghebbende", None),
        (
            "behoefte of eis van een belanghebbende, die dient als brug naar systeemontwerp",
            None,
        ),
        (
            "systematisch volgen van handelingen om naleving van regels te waarborgen",
            None,
        ),
    ],
)
async def test_service_signaal_blijft_open_en_zichtbaar(
    cached, tekst, fragment, monkeypatch
):
    get_rule_cache().clear_cache()
    manager = get_cached_toetsregel_manager() if cached else get_toetsregel_manager()
    svc = ModularValidationService(manager, None, None)
    result = await svc.validate_definition(
        begrip="begrip",
        text=tekst,
        context={"organisatorisch": ["uitvoering"], "actor": "expert", "pass": True},
    )
    assert result["rule_statuses"]["ESS-01"] == "review_required"
    assert "ESS-01" not in result["passed_rules"]
    assert not any(v.get("code") == "ESS-01" for v in result["violations"])
    item = next(r for r in result["review_required"] if r["rule_id"] == "ESS-01")
    assert "welke kenmerken bepalen de betekenis" in item["reason"]
    if fragment:
        assert f"Te beoordelen passage: {fragment}." in item["reason"]
    else:
        assert "inhoudelijke beoordeling blijft nodig" in item["reason"]
    shown = []
    for api in ("markdown", "info", "warning", "success", "error", "write", "text"):
        monkeypatch.setattr(
            validation_view.st,
            api,
            lambda t, *a, **kw: shown.append(str(t)),
            raising=False,
        )
    monkeypatch.setattr(validation_view.st, "button", lambda *a, **kw: False)
    SessionStateManager.set_value("def746_show_validation_details", False)
    validation_view.render_validation_detailed_list(result, key_prefix="def746")
    assert item["reason"] in "\n".join(shown)


async def test_herhaalde_passage_wordt_een_keer_uitgelegd():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    result = await svc.validate_definition(
        begrip="begrip", text="in het kader van werk in het kader van beleid"
    )
    item = next(r for r in result["review_required"] if r["rule_id"] == "ESS-01")
    assert item["reason"].count("Te beoordelen passage: in het kader van.") == 1
