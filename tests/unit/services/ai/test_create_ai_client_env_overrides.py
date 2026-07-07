"""Tests voor DEF-566: env-overrides op de AI-client-factory.

CI-testruns zetten AI_CLIENT_TIMEOUT/AI_SDK_MAX_RETRIES om de retry-stapeling
op de dummy-key te stoppen; zonder env blijven de productie-defaults exact
gelijk (timeout 30s, SDK-default max_retries 2).
"""

from __future__ import annotations

import pytest

from services.ai import create_ai_client

pytestmark = [pytest.mark.unit]


def test_defaults_zonder_env(monkeypatch):
    monkeypatch.delenv("AI_CLIENT_TIMEOUT", raising=False)
    monkeypatch.delenv("AI_SDK_MAX_RETRIES", raising=False)

    client = create_ai_client(provider="anthropic", api_key="sk-ant-test")

    assert client._client.timeout == 30.0
    assert client._client.max_retries == 2


def test_env_overrides_timeout_en_retries(monkeypatch):
    monkeypatch.setenv("AI_CLIENT_TIMEOUT", "2")
    monkeypatch.setenv("AI_SDK_MAX_RETRIES", "0")

    client = create_ai_client(provider="anthropic", api_key="sk-ant-test")

    assert client._client.timeout == 2.0
    assert client._client.max_retries == 0


def test_env_overrides_gelden_ook_voor_openai(monkeypatch):
    monkeypatch.setenv("AI_CLIENT_TIMEOUT", "2")
    monkeypatch.setenv("AI_SDK_MAX_RETRIES", "0")

    client = create_ai_client(provider="openai", api_key="sk-test")

    assert client._client.timeout == 2.0
    assert client._client.max_retries == 0


def test_expliciete_timeout_arg_wordt_gerespecteerd_zonder_env(monkeypatch):
    """Precedentie: caller-arg wint van de param-default; env wint van beide."""
    monkeypatch.delenv("AI_CLIENT_TIMEOUT", raising=False)
    monkeypatch.delenv("AI_SDK_MAX_RETRIES", raising=False)

    client = create_ai_client(provider="anthropic", api_key="sk-ant-test", timeout=15.0)
    assert client._client.timeout == 15.0

    monkeypatch.setenv("AI_CLIENT_TIMEOUT", "2")
    client = create_ai_client(provider="anthropic", api_key="sk-ant-test", timeout=15.0)
    assert client._client.timeout == 2.0  # env > caller-arg (bewust, voor CI)


def test_ongeldige_env_waarde_faalt_hard(monkeypatch):
    """Fail-fast op misconfiguratie is het vastgepinde gedrag."""
    monkeypatch.setenv("AI_SDK_MAX_RETRIES", "abc")

    with pytest.raises(ValueError, match="invalid literal"):
        create_ai_client(provider="anthropic", api_key="sk-ant-test")


def test_config_manager_rate_limit_nul_wordt_niet_weggedefault(monkeypatch):
    """De 0-footgun aan de config-kant: '0' is truthy als string → int 0."""
    from config.config_manager import ConfigManager

    monkeypatch.setenv("AI_RATE_LIMIT_MAX_RETRIES", "0")

    cm = ConfigManager()

    assert cm.api.rate_limit_max_retries == 0


def test_config_manager_rate_limit_overrides(monkeypatch):
    """AI_RATE_LIMIT_* stuurt de async_api-retrylaag (gelezen via getattr)."""
    from config.config_manager import ConfigManager

    monkeypatch.setenv("AI_RATE_LIMIT_MAX_RETRIES", "1")
    monkeypatch.setenv("AI_RATE_LIMIT_BACKOFF_FACTOR", "1.0")

    cm = ConfigManager()

    assert cm.api.rate_limit_max_retries == 1
    assert cm.api.rate_limit_backoff_factor == 1.0


def test_config_manager_zonder_env_rate_limit_defaults(monkeypatch):
    """Zonder env gelden de productie-defaults (3 / 1.5) — gedrag ongewijzigd."""
    from config.config_manager import ConfigManager

    monkeypatch.delenv("AI_RATE_LIMIT_MAX_RETRIES", raising=False)
    monkeypatch.delenv("AI_RATE_LIMIT_BACKOFF_FACTOR", raising=False)

    cm = ConfigManager()

    assert cm.api.rate_limit_max_retries == 3
    assert cm.api.rate_limit_backoff_factor == 1.5


def test_lege_env_valt_terug_op_default(monkeypatch):
    """Lege strings (bv. per abuis gezet) mogen niet crashen → defaults."""
    monkeypatch.setenv("AI_CLIENT_TIMEOUT", "")
    monkeypatch.setenv("AI_SDK_MAX_RETRIES", "")

    client = create_ai_client(provider="anthropic", api_key="sk-ant-test")

    assert client._client.timeout == 30.0
    assert client._client.max_retries == 2
