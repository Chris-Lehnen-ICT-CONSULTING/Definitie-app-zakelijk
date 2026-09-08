"""DEF-731: capability configuration survives save and stops when removed."""

from pathlib import Path

import pytest
import yaml

from config.config_manager import ConfigManager

pytestmark = [pytest.mark.unit]


def _config(tmp_path: Path) -> tuple[Path, dict]:
    data = {
        "model_routing": {
            "capabilities": {
                "anthropic": {
                    "temperature": {
                        "model_families": ["fixture-model"],
                        "source": "https://example.invalid/fixture",
                        "checked_at": "2026-09-08",
                    }
                }
            }
        },
        "paths": {
            name: str(tmp_path / name)
            for name in ("cache_dir", "exports_dir", "logs_dir", "reports_dir")
        },
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data))
    return path, data


def test_model_routing_survives_configuration_save(tmp_path, monkeypatch):
    monkeypatch.setattr("config.config_manager.load_project_dotenv", lambda: None)
    path, data = _config(tmp_path)
    manager = ConfigManager(config_dir=str(tmp_path))

    manager.save_configuration()

    saved = yaml.safe_load(path.read_text())
    assert saved.get("model_routing") == data["model_routing"]
    restored = ConfigManager(config_dir=str(tmp_path))
    assert restored._model_routing_config == data["model_routing"]


def test_removed_model_routing_does_not_survive_reload(tmp_path, monkeypatch):
    monkeypatch.setattr("config.config_manager.load_project_dotenv", lambda: None)
    path, data = _config(tmp_path)
    manager = ConfigManager(config_dir=str(tmp_path))
    assert manager._model_routing_config == data["model_routing"]
    data.pop("model_routing")
    path.write_text(yaml.safe_dump(data))

    manager.reload_configuration()

    assert not getattr(manager, "_model_routing_config", {})


@pytest.mark.parametrize("invalid", [None, False, "anthropic", ["unexpected"]])
def test_invalid_model_routing_is_not_kept(tmp_path, monkeypatch, invalid):
    monkeypatch.setattr("config.config_manager.load_project_dotenv", lambda: None)
    path, data = _config(tmp_path)
    data["model_routing"] = invalid
    path.write_text(yaml.safe_dump(data))

    manager = ConfigManager(config_dir=str(tmp_path))

    assert manager._model_routing_config == {}
