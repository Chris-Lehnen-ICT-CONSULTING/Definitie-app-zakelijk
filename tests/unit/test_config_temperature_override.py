"""Unit tests voor temperature override fix in config adapters."""

import pytest
from config.config_adapters import get_api_config


class TestTemperatureOverride:
    """Test dat temperature overrides correct werken zonder defaults te overschrijven."""

    def test_no_override_uses_default(self):
        """Test dat zonder override de default temperature wordt gebruikt."""
        api_config = get_api_config()
        params = api_config.get_gpt_call_params()

        # Get model-specific config
        model_config = api_config.get_model_config()

        # Moet model-specifieke defaults gebruiken
        assert params['temperature'] == model_config['temperature']
        assert params['model'] == model_config['model']
        assert params['max_tokens'] == model_config['max_tokens']

    def test_explicit_temperature_override(self):
        """Test dat een expliciete temperature override werkt."""
        api_config = get_api_config()
        override_temp = 0.5
        params = api_config.get_gpt_call_params(temperature=override_temp)

        # Get model-specific config
        model_config = api_config.get_model_config()

        # Temperature moet overschreven zijn
        assert params['temperature'] == override_temp
        # Andere parameters moeten model-specifieke defaults blijven
        assert params['model'] == model_config['model']
        assert params['max_tokens'] == model_config['max_tokens']

    def test_none_temperature_preserves_default(self):
        """Test dat temperature=None de default behoudt (geen override)."""
        api_config = get_api_config()
        params = api_config.get_gpt_call_params(temperature=None)

        # Get model-specific config
        model_config = api_config.get_model_config()

        # Moet model-specifieke defaults behouden
        assert params['temperature'] == model_config['temperature']
        assert params['model'] == model_config['model']
        assert params['max_tokens'] == model_config['max_tokens']

    def test_multiple_overrides(self):
        """Test dat meerdere overrides tegelijk werken."""
        api_config = get_api_config()
        override_model = "gpt-3.5-turbo"
        override_temp = 0.8
        override_tokens = 500

        params = api_config.get_gpt_call_params(
            model=override_model,
            temperature=override_temp,
            max_tokens=override_tokens
        )

        # Alle overrides moeten toegepast zijn
        assert params['model'] == override_model
        assert params['temperature'] == override_temp
        assert params['max_tokens'] == override_tokens

    def test_partial_overrides_with_nones(self):
        """Test dat None waarden in overrides de defaults behouden."""
        api_config = get_api_config()
        override_model = "gpt-4-turbo"

        params = api_config.get_gpt_call_params(
            model=override_model,
            temperature=None,
            max_tokens=None
        )

        # Get model-specific config for the overridden model
        model_config = api_config.get_model_config(override_model)

        # Model moet overschreven zijn, rest moet model-specifieke defaults gebruiken
        assert params['model'] == override_model
        assert params['temperature'] == model_config['temperature']
        assert params['max_tokens'] == model_config['max_tokens']

    def test_zero_temperature_override(self):
        """Test dat temperature=0 correct wordt toegepast (niet gefilterd als falsy)."""
        api_config = get_api_config()
        params = api_config.get_gpt_call_params(temperature=0)

        # Temperature 0 moet toegepast worden
        assert params['temperature'] == 0

    def test_custom_kwargs_support(self):
        """Test dat extra kwargs ook ondersteund worden."""
        api_config = get_api_config()
        params = api_config.get_gpt_call_params(
            temperature=0.3,
            top_p=0.9,
            frequency_penalty=0.5
        )

        # Get model-specific config
        model_config = api_config.get_model_config()

        # Standaard params moeten aanwezig zijn
        assert params['temperature'] == 0.3
        assert params['model'] == model_config['model']
        assert params['max_tokens'] == model_config['max_tokens']

        # Extra kwargs moeten ook aanwezig zijn
        assert params['top_p'] == 0.9
        assert params['frequency_penalty'] == 0.5
