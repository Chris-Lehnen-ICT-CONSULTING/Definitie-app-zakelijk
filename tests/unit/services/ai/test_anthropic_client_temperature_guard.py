"""Regressietests DEF-441: temperature-guard per modelfamilie.

Sampling-params (`temperature`/`top_p`/`top_k`) zijn verwijderd op
Opus 4.7+, Sonnet 5 en Fable/Mythos 5 — meesturen geeft een 400
("`temperature` is deprecated for this model"). Op Opus 4.6 en ouder,
Sonnet 4.x en Haiku 3/4.x is de parameter nog geldig.

De guard is een allowlist: alleen families die temperature aantoonbaar
accepteren krijgen hem mee; elk ander (nieuw) model → `anthropic.omit`.
Weglaten is altijd geldig, meesturen kan breken — fail-safe dus.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import anthropic
import pytest

from services.ai.base_client import ChatMessage

pytestmark = [pytest.mark.unit]


async def _capture_create_kwargs(model: str, temperature: float = 0.3) -> dict:
    """Roep chat_completion aan met gemockte SDK en geef de create-kwargs terug."""
    from services.ai.anthropic_client import AnthropicClient

    client = AnthropicClient(api_key="dummy", timeout=5.0)
    fake_response = SimpleNamespace(
        content=[],
        usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        model=model,
    )
    fake_messages = SimpleNamespace(create=AsyncMock(return_value=fake_response))
    client._client = SimpleNamespace(messages=fake_messages)  # type: ignore[assignment]

    await client.chat_completion(
        messages=[ChatMessage(role="user", content="hi")],
        model=model,
        temperature=temperature,
    )
    return dict(fake_messages.create.call_args.kwargs)


class TestTemperatureOmittedOnModernModels:
    """Opus 4.7+/Sonnet 5/Fable 5 en onbekende nieuwe modellen: geen temperature."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "model",
        [
            "claude-opus-4-8",
            "claude-opus-4-7",
            "claude-sonnet-5",
            "claude-fable-5",
            "claude-mythos-5",
            "claude-opus-5",  # hypothetisch toekomstig model → fail-safe weglaten
            # substring-collisie: bevat "opus-4-1" maar is een 4.7+-achtige
            # toekomstversie — mag NIET door de allowlist lekken (review #351)
            "claude-opus-4-10",
        ],
    )
    async def test_temperature_is_omitted(self, model: str) -> None:
        kwargs = await _capture_create_kwargs(model)
        assert "temperature" in kwargs, "create-call hoort temperature=omit te dragen"
        sent = kwargs["temperature"]
        assert isinstance(sent, anthropic.Omit), (
            f"temperature werd meegestuurd naar {model} — dat geeft een 400 "
            "('temperature is deprecated for this model', DEF-441)"
        )


class TestTemperatureSentOnLegacyModels:
    """Opus 4.6 en ouder, Sonnet 4.x, Haiku 3/4.x: temperature ongewijzigd meesturen."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "model",
        [
            "claude-opus-4-6",
            "claude-opus-4-5-20251101",
            "claude-opus-4-1",
            "claude-sonnet-4-6",
            "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
            "claude-3-haiku-20240307",
            "Claude-Opus-4-6",  # case-insensitief (guard lowercased het model)
        ],
    )
    async def test_temperature_is_sent_unchanged(self, model: str) -> None:
        kwargs = await _capture_create_kwargs(model, temperature=0.42)
        assert kwargs.get("temperature") == 0.42, (
            f"temperature ontbreekt voor {model} — gedrag voor oudere modellen "
            "moet ongewijzigd blijven (acceptatiecriterium DEF-441)"
        )
        # De guard mag geen andere create-kwargs beïnvloeden
        assert kwargs["model"] == model
        assert kwargs["messages"] == [{"role": "user", "content": "hi"}]


class TestPolicyComesFromConfigNotHardcodedList:
    """DEF-731: de verzendpolicy komt uit config, niet uit een lijst in de client.

    Deze tests lopen over het echte productiepad
    ConfigManager -> ModelRouter.from_config() -> AnthropicClient; alleen de
    SDK-aanroep is gemockt. Er wordt geen router in de client geinjecteerd.
    """

    @pytest.mark.asyncio
    async def test_config_flip_changes_final_sdk_kwargs(self, monkeypatch) -> None:
        from config.config_manager import get_config_manager

        cfg = get_config_manager()
        policy = {
            "capabilities": {
                "anthropic": {"temperature": {"model_families": ["opus-4-8"]}}
            }
        }
        monkeypatch.setattr(cfg, "_model_routing_config", policy, raising=False)
        kwargs = await _capture_create_kwargs("claude-opus-4-8", temperature=0.11)
        assert kwargs["temperature"] == 0.11, (
            "config die opus-4-8 toelaat moet temperature naar de SDK sturen; "
            "een hardcoded lijst in de client negeert de config"
        )

    @pytest.mark.asyncio
    async def test_empty_policy_omits_previously_allowed_model(
        self, monkeypatch
    ) -> None:
        from config.config_manager import get_config_manager

        cfg = get_config_manager()
        monkeypatch.setattr(
            cfg,
            "_model_routing_config",
            {"capabilities": {"anthropic": {"temperature": {"model_families": []}}}},
            raising=False,
        )
        kwargs = await _capture_create_kwargs("claude-opus-4-6")
        assert isinstance(
            kwargs["temperature"], anthropic.Omit
        ), "lege policy moet temperature weglaten, ook voor een legacy-model"

    @pytest.mark.asyncio
    async def test_malformed_policy_never_enables_temperature(
        self, monkeypatch
    ) -> None:
        from config.config_manager import get_config_manager

        cfg = get_config_manager()
        monkeypatch.setattr(
            cfg,
            "_model_routing_config",
            {
                "capabilities": {
                    "anthropic": {"temperature": {"model_families": "opus-4-6"}}
                }
            },
            raising=False,
        )
        kwargs = await _capture_create_kwargs("claude-opus-4-6")
        assert isinstance(kwargs["temperature"], anthropic.Omit)

    @pytest.mark.asyncio
    async def test_repo_config_preserves_legacy_contract(self) -> None:
        """Zonder monkeypatch: de echte config/config.yaml stuurt het gedrag."""
        legacy = await _capture_create_kwargs("claude-opus-4-6", temperature=0.42)
        assert legacy["temperature"] == 0.42
        modern = await _capture_create_kwargs("claude-opus-4-8")
        assert isinstance(modern["temperature"], anthropic.Omit)


class TestPolicyFollowsConfigReload:
    """DEF-731/F1: een al gebruikte client volgt een echte config-reload.

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
                            "anthropic": {"temperature": {"model_families": families}}
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

    @staticmethod
    async def _capture(client, model: str, temperature: float) -> dict:
        fake_response = SimpleNamespace(
            content=[],
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
            model=model,
        )
        fake_messages = SimpleNamespace(create=AsyncMock(return_value=fake_response))
        client._client = SimpleNamespace(messages=fake_messages)  # type: ignore[assignment]
        await client.chat_completion(
            messages=[ChatMessage(role="user", content="hi")],
            model=model,
            temperature=temperature,
        )
        return dict(fake_messages.create.call_args.kwargs)

    @pytest.mark.asyncio
    async def test_same_client_picks_up_policy_change_after_reload(
        self, tmp_path, monkeypatch
    ) -> None:
        from config import config_manager as cm
        from services.ai.anthropic_client import AnthropicClient

        monkeypatch.setattr(cm, "load_project_dotenv", lambda: None, raising=False)
        config_path = tmp_path / "config.yaml"

        # Policy A: opus-4-8 mag temperature ontvangen.
        self._write_config(config_path, ["opus-4-8"])
        manager = cm.ConfigManager(config_dir=str(tmp_path))
        monkeypatch.setattr(cm, "get_config_manager", lambda: manager)

        client = AnthropicClient(api_key="dummy", timeout=5.0)
        first = await self._capture(client, "claude-opus-4-8", 0.11)
        assert first["temperature"] == 0.11, "policy A moet temperature meesturen"

        # Policy B: familie verwijderd -> dezelfde client moet omitten.
        self._write_config(config_path, [])
        manager.reload_configuration()

        second = await self._capture(client, "claude-opus-4-8", 0.11)
        assert isinstance(second["temperature"], anthropic.Omit), (
            "dezelfde client stuurt na een echte reload nog de oude policy — "
            "de router-snapshot in de client veroudert (DEF-731/F1)"
        )

    @pytest.mark.asyncio
    async def test_reload_can_also_enable_temperature_for_existing_client(
        self, tmp_path, monkeypatch
    ) -> None:
        """Andersom ook: van omit naar meesturen, zonder nieuwe client."""
        from config import config_manager as cm
        from services.ai.anthropic_client import AnthropicClient

        monkeypatch.setattr(cm, "load_project_dotenv", lambda: None, raising=False)
        config_path = tmp_path / "config.yaml"

        self._write_config(config_path, [])
        manager = cm.ConfigManager(config_dir=str(tmp_path))
        monkeypatch.setattr(cm, "get_config_manager", lambda: manager)

        client = AnthropicClient(api_key="dummy", timeout=5.0)
        first = await self._capture(client, "claude-opus-4-6", 0.42)
        assert isinstance(first["temperature"], anthropic.Omit)

        self._write_config(config_path, ["opus-4-6"])
        manager.reload_configuration()

        second = await self._capture(client, "claude-opus-4-6", 0.42)
        assert (
            second["temperature"] == 0.42
        ), "na reload moet de client de nieuwe policy volgen"

    @pytest.mark.asyncio
    async def test_injected_router_stays_authoritative(self, tmp_path) -> None:
        """Expliciete injectie mag wel vast zijn: geen config-lookup."""
        from services.ai.anthropic_client import AnthropicClient
        from services.ai.model_router import ModelRouter

        injected = ModelRouter(
            {
                "capabilities": {
                    "anthropic": {"temperature": {"model_families": ["opus-4-8"]}}
                }
            }
        )
        client = AnthropicClient(api_key="dummy", timeout=5.0, model_router=injected)
        kwargs = await self._capture(client, "claude-opus-4-8", 0.33)
        assert kwargs["temperature"] == 0.33
