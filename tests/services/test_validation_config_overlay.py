"""Tests for validation configuration with environment overlay."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml


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
def test_config_environment_overlay():
    """Test that environment variables can overlay YAML config."""
    m = pytest.importorskip(
        "services.validation.config",
        reason="ValidationConfig module not implemented yet",
    )

    getattr(m, "ValidationConfig", None)
    load_with_env_overlay = getattr(m, "load_with_env_overlay", None)

    if not load_with_env_overlay:
        pytest.skip("load_with_env_overlay function not found")

    # Create base config
    base_config = {
        "enabled_codes": ["ESS-01"],
        "weights": {"ESS-01": 1.0},
        "thresholds": {"overall_accept": 0.75},
    }

    # Create overlay config
    overlay_config = {
        "enabled_codes": ["ESS-01", "CON-01"],  # Add extra code
        "weights": {"ESS-01": 0.9, "CON-01": 0.8},  # Override weight
        "thresholds": {"overall_accept": 0.80},  # Override threshold
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as base_f:
        yaml.dump(base_config, base_f)
        base_path = base_f.name

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as overlay_f:
        yaml.dump(overlay_config, overlay_f)
        overlay_path = overlay_f.name

    try:
        # Set environment variable to overlay path
        os.environ["VALIDATION_CONFIG_OVERLAY"] = overlay_path

        # Load with overlay
        config = load_with_env_overlay(base_path)

        # Verify overlay applied
        assert "CON-01" in config.enabled_codes
        assert config.weights["ESS-01"] == 0.9  # Overridden
        assert config.thresholds["overall_accept"] == 0.80  # Overridden
    finally:
        os.unlink(base_path)
        os.unlink(overlay_path)
        os.environ.pop("VALIDATION_CONFIG_OVERLAY", None)


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


@pytest.mark.unit
def test_config_fallback_to_defaults_on_error():
    """Test that system falls back to defaults when config is invalid."""
    m = pytest.importorskip(
        "services.validation.config",
        reason="ValidationConfig module not implemented yet",
    )

    ValidationConfig = getattr(m, "ValidationConfig", None)
    get_default_config = getattr(m, "get_default_config", None)

    if not get_default_config:
        pytest.skip("get_default_config function not found")

    # Try to load invalid config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content: [[[")  # Invalid YAML
        invalid_path = f.name

    try:
        # Should fall back to defaults instead of crashing
        config = ValidationConfig.from_yaml_with_fallback(invalid_path)
        default_config = get_default_config()

        # Config should match defaults
        assert config.enabled_codes == default_config.enabled_codes
        assert (
            config.thresholds["overall_accept"]
            == default_config.thresholds["overall_accept"]
        )
    finally:
        os.unlink(invalid_path)


@pytest.mark.unit
def test_config_deep_merge_overlay():
    """Test that overlay performs deep merge, not shallow replace."""
    m = pytest.importorskip(
        "services.validation.config",
        reason="ValidationConfig module not implemented yet",
    )

    deep_merge = getattr(m, "deep_merge_configs", None)

    if not deep_merge:
        pytest.skip("deep_merge_configs function not found")

    base = {
        "weights": {
            "ESS-01": 1.0,
            "CON-01": 0.8,
        },
        "thresholds": {
            "overall_accept": 0.75,
            "category_min": {
                "ESS": 0.7,
                "CON": 0.6,
            },
        },
    }

    overlay = {
        "weights": {
            "CON-01": 0.9,  # Override one weight
            "STR-01": 0.7,  # Add new weight
        },
        "thresholds": {
            "category_min": {
                "ESS": 0.8,  # Override one category
                # CON should remain 0.6
            },
        },
    }

    result = deep_merge(base, overlay)

    # Check deep merge worked correctly
    assert result["weights"]["ESS-01"] == 1.0  # Preserved from base
    assert result["weights"]["CON-01"] == 0.9  # Overridden by overlay
    assert result["weights"]["STR-01"] == 0.7  # Added by overlay
    assert result["thresholds"]["overall_accept"] == 0.75  # Preserved from base
    assert result["thresholds"]["category_min"]["ESS"] == 0.8  # Overridden
    assert result["thresholds"]["category_min"]["CON"] == 0.6  # Preserved


@pytest.mark.unit
def test_config_handles_missing_overlay_gracefully():
    """Test that missing overlay file doesn't crash the system."""
    m = pytest.importorskip(
        "services.validation.config",
        reason="ValidationConfig module not implemented yet",
    )

    load_with_env_overlay = getattr(m, "load_with_env_overlay", None)

    if not load_with_env_overlay:
        pytest.skip("load_with_env_overlay function not found")

    # Create base config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(
            {
                "enabled_codes": ["ESS-01"],
                "weights": {"ESS-01": 1.0},
                "thresholds": {"overall_accept": 0.75},
            },
            f,
        )
        base_path = f.name

    try:
        # Set environment variable to non-existent file
        os.environ["VALIDATION_CONFIG_OVERLAY"] = "/non/existent/path.yaml"

        # Should load base config without crashing
        config = load_with_env_overlay(base_path)

        # Should have base values
        assert "ESS-01" in config.enabled_codes
        assert config.weights["ESS-01"] == 1.0
    finally:
        os.unlink(base_path)
        os.environ.pop("VALIDATION_CONFIG_OVERLAY", None)


@pytest.mark.unit
def test_config_v1_parity_extraction():
    """Test extraction of weights/thresholds from V1 DefinitionValidator."""
    m = pytest.importorskip(
        "services.validation.config",
        reason="ValidationConfig module not implemented yet",
    )

    extract_v1_config = getattr(m, "extract_v1_config", None)

    if not extract_v1_config:
        pytest.skip("extract_v1_config function not found")

    # Mock V1 validator with known weights
    class MockV1Validator:
        def __init__(self):
            self.rule_weights = {
                "essential_content": 2.0,
                "consistency": 1.5,
                "structure": 1.0,
            }
            self.min_score = 0.6
            self.category_thresholds = {
                "essential": 0.5,
                "consistency": 0.4,
            }

    v1_validator = MockV1Validator()

    # Extract config
    extracted = extract_v1_config(v1_validator)

    # Verify extraction
    assert extracted["weights"]["essential_content"] == 2.0
    assert extracted["thresholds"]["overall_accept"] == 0.6
    assert extracted["thresholds"]["category_min"]["essential"] == 0.5
