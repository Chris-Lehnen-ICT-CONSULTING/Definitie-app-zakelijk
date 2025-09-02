import io
from textwrap import dedent

import pytest


@pytest.mark.unit
def test_validation_config_from_yaml_parses_expected_sections(tmp_path):
    m = pytest.importorskip(
        "services.validation.config",
        reason="ValidationConfig module not implemented yet",
    )

    yaml_content = dedent(
        """
        enabled_codes:
          - ESS_01
          - CON_01
        weights:
          ESS_01: 1.0
          CON_01: 0.8
        thresholds:
          overall_accept: 0.75
          category_min:
            ESS: 0.7
            CON: 0.6
        params:
          ESS_01:
            min_length: 12
        """
    )

    cfg_file = tmp_path / "validation_rules.yaml"
    cfg_file.write_text(yaml_content, encoding="utf-8")

    ValidationConfig = getattr(m, "ValidationConfig")
    cfg = ValidationConfig.from_yaml(str(cfg_file))

    assert "ESS_01" in cfg.enabled_codes
    assert cfg.weights["CON_01"] == pytest.approx(0.8)
    assert cfg.thresholds["overall_accept"] == pytest.approx(0.75)
