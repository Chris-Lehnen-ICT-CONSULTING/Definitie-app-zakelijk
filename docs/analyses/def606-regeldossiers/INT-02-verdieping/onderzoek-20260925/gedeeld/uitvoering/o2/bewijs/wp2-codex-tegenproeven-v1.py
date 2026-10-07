import sys
sys.path.insert(0, "/private/tmp/def835-wp2-review-20260927")
import tests.conftest  # installeert netwerkblokkade en geisoleerde testomgeving
import asyncio, copy, io, json, logging
from types import SimpleNamespace as N
from tests.unit.validation.test_def835_int02_assessment_service import (
    FakeAI, FakeRouter, _budget, _dienst, _echte_ai, _fail_uitvoer,
    _invoer, _profiel, _Provider,
)
from services.ai.openai_client import OpenAIClient
from services.ai.anthropic_client import AnthropicClient
from services.ai.model_router import ModelRouter
from services.ai.base_client import AIConnectionClientError
from domain.int02.contract import toets_actualiteit

from services.ai_service_v2 import AIServiceV2
from utils.async_api import RateLimitConfig

def _echte_ai(provider):
    # Alleen offline testconstructie: vermijd encoderdownload bij initialisatie.
    # De beoordeelde call blijft het expliciete profielmodel doorgeven.
    return AIServiceV2(default_model="claude-offline-fixture",
        rate_limit_config=RateLimitConfig(max_retries=3, backoff_factor=1.0),
        use_cache=True, ai_client=provider, model_router=FakeRouter())

async def main():
    # 1: echte OpenAI-adapter, alleen de SDK-netwerkgrens is fake.
    class SDK:
        def __init__(self):
            self.calls = 0
            self.chat = N(completions=N(create=self.create))
        def with_options(self, **kwargs):
            assert kwargs == {"max_retries": 0}
            return self
        async def create(self, **kwargs):
            self.calls += 1
            return N(choices=[N(message=N(content=json.dumps(_fail_uitvoer())),
                                finish_reason="length")],
                     usage=N(total_tokens=800), model=kwargs["model"])
    sdk = SDK()
    provider = object.__new__(OpenAIClient)
    provider._timeout = 30
    provider._sdk_voor_deze_loop = lambda: sdk
    router = FakeRouter(provider="openai", model="gpt-4.1")
    service = _dienst(_echte_ai(provider), router,
                      profiel=_profiel(provider="openai", model="gpt-4.1"))
    first = await service.assess(_invoer())
    second = await service.assess(_invoer())
    print("OPENAI_AFKAPPING", json.dumps(dict(status=first.status,
          reden=first.reden, stop_reason=first.stop_reason,
          tweede_gecachet=second.gecachet, sdk_calls=sdk.calls)))
    assert first.status == "fail" and second.gecachet and sdk.calls == 1

    # 2: capabilities veranderen echt verzendbeleid, zonder andere model-ID.
    config = copy.deepcopy(ModelRouter._DEFAULT_CONFIG)
    model = config["providers"]["anthropic"]["critical"]
    config["capabilities"] = {"anthropic": {
        "thinking_default_on": {"model_families": [model]},
        "temperature": {"model_families": [model]}}}
    router = ModelRouter(config)
    chosen_provider, chosen_model = router.get_model("validation")
    assert chosen_provider == "anthropic" and chosen_model == model
    anthropic = object.__new__(AnthropicClient)
    anthropic._model_router = router
    old_policy = tuple(repr(v) for v in anthropic._verzendbeleid(model, 0.0))
    ai = FakeAI()
    service = _dienst(ai, router, profiel=_profiel(provider=chosen_provider, model=model))
    old = await service.assess(_invoer())
    config["capabilities"]["anthropic"]["thinking_default_on"]["model_families"].clear()
    config["capabilities"]["anthropic"]["temperature"]["model_families"].clear()
    new_policy = tuple(repr(v) for v in anthropic._verzendbeleid(model, 0.0))
    new = await service.assess(_invoer())
    fresh = await _dienst(FakeAI(), router, profiel=_profiel(provider=chosen_provider, model=model)).assess(_invoer())
    replay = toets_actualiteit(old.document, _invoer(), fresh.document.binding.configuratie())
    print("ROUTERBINDING", json.dumps(dict(oud_beleid=old_policy, nieuw_beleid=new_policy,
          tweede_gecachet=new.gecachet, calls=len(ai.calls),
          binding_gelijk=old.document.binding == fresh.document.binding,
          actualiteit_oud=replay.status, actualiteit_reden=replay.reden)))
    assert old_policy != new_policy and new.gecachet
    assert old.document.binding == fresh.document.binding and replay.reden is None

    # 3: echte stack wacht op capaciteit; geen provider-call voor de deadline.
    provider = _Provider()
    ai = _echte_ai(provider)
    ai._get_client().rate_limiter.semaphore = asyncio.Semaphore(0)
    result = await _dienst(ai, budget=_budget(deadline_seconden=0.03)).assess(_invoer())
    print("POGINGENTELLING", json.dumps(dict(status=result.status, reden=result.reden,
          providercalls=len(provider.calls),
          gerapporteerde_transportpogingen=result.document.uitvoering.transportpogingen)))
    assert result.reden == "timeout" and not provider.calls
    assert result.document.uitvoering.transportpogingen == 1

    # 4: bekende transportlogging, synthetische foutmarkering.
    marker = "SYNTHETISCH-PRIVE-REVIEW-835"
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        result = await _dienst(_echte_ai(_Provider(AIConnectionClientError(marker)))).assess(_invoer())
    finally:
        root.removeHandler(handler)
    lines = [line for line in stream.getvalue().splitlines() if marker in line]
    print("TRANSPORTLOGGING", json.dumps(dict(status=result.status, lekkende_regels=lines)))
    assert any("utils.async_api: API call failed:" in line for line in lines)
    assert not any("int02_assessment_service" in line for line in lines)

asyncio.run(main())
