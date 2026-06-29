"""Tests for validation configuration (ValidationConfig.from_yaml + validate_config).

DEF-480: de env-overlay/fallback/V1-pariteit-scaffolding is verwijderd; deze
tests dekken nog de wel-gewirede functies van services.validation.config.
"""

import os
import tempfile

import pytest
import yaml

pytestmark = [pytest.mark.unit]


@pytest.mark.unit
def test_config_load_from_yaml_file():
    """Test loading configuration from YAML file."""
    m = pytest.importorskip(
        "services.validation.config",
        reason="ValidationConfig module not implemented yet",
    )

    ValidationConfig = getattr(m, "ValidationConfig", None)
    assert ValidationConfig is not None, "ValidationConfig class must exist"

    # Create temporary YAML config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(
            {
                "enabled_codes": ["ESS-01", "CON-01", "STR-01"],
                "weights": {
                    "ESS-01": 1.0,
                    "CON-01": 0.8,
                    "STR-01": 0.6,
                },
                "thresholds": {
                    "overall_accept": 0.75,
                    "category_min": {
                        "ESS": 0.7,
                        "CON": 0.6,
                        "STR": 0.5,
                    },
                },
                "params": {
                    "ESS-01": {"min_length": 12},
                    "CON-01": {"max_circular_ratio": 0.3},
                },
            },
            f,
        )
        config_path = f.name

    try:
        # Load config
        config = ValidationConfig.from_yaml(config_path)

        # Verify loaded values
        assert "ESS-01" in config.enabled_codes
        assert config.weights["CON-01"] == 0.8
        assert config.thresholds["overall_accept"] == 0.75
        assert config.thresholds["category_min"]["ESS"] == 0.7
        assert config.params["ESS-01"]["min_length"] == 12
    finally:
        os.unlink(config_path)


@pytest.mark.unit
def test_config_validation_at_startup():
    """Test that invalid configuration is validated and rejected."""
    m = pytest.importorskip(
        "services.validation.config",
        reason="ValidationConfig module not implemented yet",
    )

    getattr(m, "ValidationConfig", None)
    validate_config = getattr(m, "validate_config", None)

    if not validate_config:
        pytest.skip("validate_config function not found")

    # Valid config
    valid_config = {
        "enabled_codes": ["ESS-01"],
        "weights": {"ESS-01": 1.0},
        "thresholds": {"overall_accept": 0.75},
    }

    errors = validate_config(valid_config)
    assert len(errors) == 0, "Valid config should have no errors"

    # Invalid config - weight out of range
    invalid_config1 = {
        "enabled_codes": ["ESS-01"],
        "weights": {"ESS-01": 1.5},  # > 1.0
        "thresholds": {"overall_accept": 0.75},
    }

    errors = validate_config(invalid_config1)
    assert len(errors) > 0, "Weight > 1.0 should be invalid"
    assert any("weight" in str(e).lower() for e in errors)

    # Invalid config - threshold out of range
    invalid_config2 = {
        "enabled_codes": ["ESS-01"],
        "weights": {"ESS-01": 1.0},
        "thresholds": {"overall_accept": 1.5},  # > 1.0
    }

    errors = validate_config(invalid_config2)
    assert len(errors) > 0, "Threshold > 1.0 should be invalid"
    assert any("threshold" in str(e).lower() for e in errors)

    # Invalid config - code in weights but not enabled
    invalid_config3 = {
        "enabled_codes": ["ESS-01"],
        "weights": {"ESS-01": 1.0, "CON-01": 0.8},  # CON-01 not enabled
        "thresholds": {"overall_accept": 0.75},
    }

    errors = validate_config(invalid_config3)
    assert len(errors) > 0, "Weight for disabled code should be invalid"
