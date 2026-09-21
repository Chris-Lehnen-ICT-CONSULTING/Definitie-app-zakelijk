"""Regressietests DEF-766 (correctieronde 3, F1): thinking-guard per modelfamilie.

Op Claude Opus 5 en Sonnet 5 staat adaptief denken standaard AAN wanneer de
`thinking`-parameter wordt weggelaten; op Opus 4.8/4.7/4.6 staat het standaard
uit. Denktokens tellen mee in `max_tokens`. Met de kleine budgetten van de app
(300/500/800/1200) komt dan een afgekapt of leeg tekstantwoord terug.

De guard is — net als de temperature-guard (DEF-441/DEF-731) — een
configuratiegestuurde allowlist: alleen families die in
`model_routing.capabilities.anthropic.thinking_default_on.model_families`
staan krijgen expliciet `thinking={"type": "disabled"}` mee; elk ander model
→ `anthropic.omit`, zodat het gedrag voor Opus 4.8 e.d. byte-identiek blijft.

Fable 5/Mythos 5 staan bewust NIET in de repo-configuratie: volgens de
modelreferentie (skill `claude-api`, tabel Thinking & Effort) geeft een
expliciete `disabled` daar een 400 — weglaten is de enige geldige vorm. Dat
het mechanisme zelf ook die families zou volgen, bewijst de test met een
geïnjecteerde router (configuratie, geen lijst in de client).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import anthropic
import pytest

from services.ai.base_client import ChatMessage

pytestmark = [pytest.mark.unit]

THINKING_UIT = {"type": "disabled"}


def _fake_response(model: str):
    return SimpleNamespace(
        content=[],
        usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        model=model,
    )


async def _capture_create_kwargs(model: str, client=None) -> dict:
    """Roep chat_completion aan met gemockte SDK en geef de create-kwargs terug."""
    from services.ai.anthropic_client import AnthropicClient

    client = client or AnthropicClient(api_key="dummy", timeout=5.0)
    fake_messages = SimpleNamespace(
        create=AsyncMock(return_value=_fake_response(model))
    )
    client._client = SimpleNamespace(messages=fake_messages)  # type: ignore[assignment]

    await client.chat_completion(
        messages=[ChatMessage(role="user", content="hi")],
        model=model,
        max_tokens=1200,
    )
    return dict(fake_messages.create.call_args.kwargs)


class TestThinkingDisabledOnDefaultOnModels:
    """Opus 5 / Sonnet 5 (repo-config): thinking expliciet uit."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "model",
        [
            "claude-opus-5",
            "claude-sonnet-5",
            "Claude-Opus-5",  # case-insensitief (guard lowercased het model)
        ],
    )
    async def test_thinking_is_disabled(self, model: str) -> None:
        kwargs = await _capture_create_kwargs(model)
        assert kwargs.get("thinking") == THINKING_UIT, (
            f"thinking niet uitgezet voor {model} — adaptief denken staat daar "
            "standaard aan en eet het max_tokens-budget op (DEF-766, F1)"
        )


class TestThinkingOmittedOnOtherModels:
    """Opus 4.8/4.7/4.6, Haiku, Fable/Mythos en onbekende modellen: weglaten."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "model",
        [
            "claude-opus-4-8",
            "claude-opus-4-7",
            "claude-opus-4-6",
            "claude-haiku-4-5-20251001",
            # Thinking staat hier altijd aan en `disabled` geeft een 400
            # (modelreferentie): weglaten is de enige geldige vorm.
            "claude-fable-5",
            "claude-mythos-5",
            # substring-collisie: bevat "opus-5" gevolgd door een cijfer —
            # mag NIET door de allowlist lekken (zelfde grens als DEF-441).
            "claude-opus-50",
        ],
    )
    async def test_thinking_is_omitted(self, model: str) -> None:
        kwargs = await _capture_create_kwargs(model)
        assert "thinking" in kwargs, "create-call hoort thinking=omit te dragen"
        assert isinstance(kwargs["thinking"], anthropic.Omit), (
            f"thinking werd meegestuurd naar {model} — voor modellen buiten de "
            "allowlist moet de aanroep byte-identiek blijven (DEF-766, F1)"
        )
        # De guard mag geen andere create-kwargs beïnvloeden.
        assert kwargs["model"] == model
        assert kwargs["max_tokens"] == 1200
        assert kwargs["messages"] == [{"role": "user", "content": "hi"}]


class TestPolicyComesFromConfigNotHardcodedList:
    """De verzendpolicy komt uit config, niet uit een lijst in de client.

    Productiepad ConfigManager -> ModelRouter.from_config() -> AnthropicClient;
    alleen de SDK-aanroep is gemockt.
    """

    @staticmethod
    def _policy(families):
        return {
            "capabilities": {
                "anthropic": {"thinking_default_on": {"model_families": families}}
            }
        }

    @pytest.mark.asyncio
    async def test_config_flip_disables_thinking_for_a_legacy_model(
        self, monkeypatch
    ) -> None:
        from config.config_manager import get_config_manager

        cfg = get_config_manager()
        monkeypatch.setattr(
            cfg, "_model_routing_config", self._policy(["opus-4-8"]), raising=False
        )
        kwargs = await _capture_create_kwargs("claude-opus-4-8")
        assert kwargs.get("thinking") == THINKING_UIT, (
            "config die opus-4-8 opneemt moet thinking=disabled naar de SDK "
            "sturen; een hardcoded lijst in de client negeert de config"
        )

    @pytest.mark.asyncio
    async def test_empty_policy_omits_thinking_for_opus_5(self, monkeypatch) -> None:
        from config.config_manager import get_config_manager

        cfg = get_config_manager()
        monkeypatch.setattr(
            cfg, "_model_routing_config", self._policy([]), raising=False
        )
        kwargs = await _capture_create_kwargs("claude-opus-5")
        assert isinstance(
            kwargs["thinking"], anthropic.Omit
        ), "lege policy moet thinking weglaten, ook voor Opus 5"

    @pytest.mark.asyncio
    async def test_malformed_policy_never_sends_thinking(self, monkeypatch) -> None:
        from config.config_manager import get_config_manager

        cfg = get_config_manager()
        # Een kale string zou per karakter matchen -> expliciet weigeren.
        monkeypatch.setattr(
            cfg, "_model_routing_config", self._policy("opus-5"), raising=False
        )
        kwargs = await _capture_create_kwargs("claude-opus-5")
        assert isinstance(kwargs["thinking"], anthropic.Omit)

    @pytest.mark.asyncio
    async def test_repo_config_drives_the_split(self) -> None:
        """Zonder monkeypatch: de echte config/config.yaml stuurt het gedrag."""
        modern = await _capture_create_kwargs("claude-opus-5")
        assert modern["thinking"] == THINKING_UIT
        legacy = await _capture_create_kwargs("claude-opus-4-8")
        assert isinstance(legacy["thinking"], anthropic.Omit)

    @pytest.mark.asyncio
    async def test_injected_router_can_extend_the_families(self) -> None:
        """Het mechanisme volgt élke geconfigureerde familie (bv. fable-5 als
        de coördinator daartoe besluit): configuratie, geen lijst in de client."""
        from services.ai.anthropic_client import AnthropicClient
        from services.ai.model_router import ModelRouter

        injected = ModelRouter(self._policy(["opus-5", "fable-5"]))
        client = AnthropicClient(api_key="dummy", timeout=5.0, model_router=injected)
        kwargs = await _capture_create_kwargs("claude-fable-5", client=client)
        assert kwargs["thinking"] == THINKING_UIT


class TestPolicyFollowsConfigReload:
    """Een al gebruikte client volgt een echte config-reload (zoals DEF-731/F1).

    Hele keten is echt — tijdelijke config.yaml, ConfigManager, reload,
    ModelRouter en AnthropicClient. Alleen de SDK-netwerkgrens is gemockt.
    """

    @staticmethod
    def _write_config(path, families) -> None:
        import yaml

        base = path.parent
        path.write_text(
            yaml.safe_dump(
                {
                    "model_routing": {
                        "capabilities": {
                            "anthropic": {
                                "thinking_default_on": {"model_families": families}
                            }
                        }
                    },
                    "paths": {
                        name: str(base / name)
                        for name in (
                            "cache_dir",
                            "exports_dir",
                            "logs_dir",
                            "reports_dir",
                        )
                    },
                }
            ),
            encoding="utf-8",
        )

    @pytest.mark.asyncio
    async def test_same_client_picks_up_policy_change_after_reload(
        self, tmp_path, monkeypatch
    ) -> None:
        from config import config_manager as cm
        from services.ai.anthropic_client import AnthropicClient

        monkeypatch.setattr(cm, "load_project_dotenv", lambda: None, raising=False)
        config_path = tmp_path / "config.yaml"

        # Policy A: opus-5 krijgt thinking=disabled.
        self._write_config(config_path, ["opus-5"])
        manager = cm.ConfigManager(config_dir=str(tmp_path))
        monkeypatch.setattr(cm, "get_config_manager", lambda: manager)

        client = AnthropicClient(api_key="dummy", timeout=5.0)
        first = await _capture_create_kwargs("claude-opus-5", client=client)
        assert first["thinking"] == THINKING_UIT, "policy A moet thinking uitzetten"

        # Policy B: familie verwijderd -> dezelfde client moet omitten.
        self._write_config(config_path, [])
        manager.reload_configuration()

        second = await _capture_create_kwargs("claude-opus-5", client=client)
        assert isinstance(second["thinking"], anthropic.Omit), (
            "dezelfde client stuurt na een echte reload nog de oude policy — "
            "de router-snapshot in de client veroudert"
        )


class TestModelRouterThinkingDefaultOn:
    """De routermethode zelf: dezelfde matching als `accepts_temperature`."""

    def test_repo_config_marks_opus_5_and_sonnet_5(self) -> None:
        from services.ai.model_router import ModelRouter

        router = ModelRouter.from_config()
        assert router.thinking_default_on("claude-opus-5", provider="anthropic")
        assert router.thinking_default_on("claude-sonnet-5", provider="anthropic")
        assert not router.thinking_default_on("claude-opus-4-8", provider="anthropic")
        assert not router.thinking_default_on("claude-opus-50", provider="anthropic")

    @pytest.mark.parametrize("model", ["", None, 5])
    def test_invalid_model_is_never_default_on(self, model) -> None:
        from services.ai.model_router import ModelRouter

        router = ModelRouter({})
        assert router.thinking_default_on(model, provider="anthropic") is False  # type: ignore[arg-type]

    def test_other_provider_has_no_families(self) -> None:
        from services.ai.model_router import ModelRouter

        router = ModelRouter.from_config()
        assert not router.thinking_default_on("claude-opus-5", provider="openai")
