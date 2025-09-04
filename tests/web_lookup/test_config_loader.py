import pytest


def test_load_web_lookup_config_defaults():
    """Loads default YAML and exposes expected structure and provider settings."""
    try:
        from services.web_lookup.config_loader import load_web_lookup_config
    except Exception as e:
        pytest.fail(f"config_loader missing or import failed: {e}")

    cfg = load_web_lookup_config()
    assert isinstance(cfg, dict)
    assert "web_lookup" in cfg
    wl = cfg["web_lookup"]
    assert wl.get("enabled") is True

    # Cache section
    cache = wl.get("cache", {})
    assert cache.get("default_ttl") == 3600
    assert cache.get("max_entries") == 1000

    # Providers
    providers = wl.get("providers", {})
    assert "wikipedia" in providers
    assert "sru_overheid" in providers

    wikipedia = providers["wikipedia"]
    assert wikipedia.get("enabled") is True
    assert wikipedia.get("weight") == 0.7
    assert wikipedia.get("cache_ttl") == 7200

    overheid = providers["sru_overheid"]
    assert overheid.get("enabled") is True
    assert overheid.get("weight") == 1.0
    assert overheid.get("cache_ttl") == 3600
