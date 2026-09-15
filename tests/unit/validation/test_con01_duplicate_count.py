"""CON-01 heeft geen uitvoerbare validator meer in de legacy-loader (DEF-464)."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "regel_id", ["CON-01", "CON_01", "CON01", "con-01", "con_01", "con01"]
)
def test_retired_con01_cannot_be_loaded_from_stale_cache(regel_id, monkeypatch, caplog):
    from toetsregels.json_validator_loader import JSONValidatorLoader

    loader = JSONValidatorLoader()
    loader._validators_cache[regel_id] = object()

    def unexpected_config_read(_):
        pytest.fail("Uitgefaseerde CON-01 mag geen bestands- of importpad bereiken")

    monkeypatch.setattr(loader, "load_json_config", unexpected_config_read)
    assert loader.load_validator(regel_id) is None
    assert "ModularValidationService" in caplog.text


def test_con01_json_and_manifest_remain_available():
    from toetsregels.json_validator_loader import JSONValidatorLoader

    loader = JSONValidatorLoader()
    assert loader.load_json_config("CON-01")["id"] == "CON-01"
    assert "CON-01" in loader.get_all_regel_ids()


@pytest.mark.parametrize("explicit", [True, False])
def test_retired_con01_is_visible_without_boolean_or_total_score(tmp_path, explicit):
    from toetsregels.json_validator_loader import JSONValidatorLoader

    (tmp_path / "CON-01.json").write_text("{}", encoding="utf-8")
    (tmp_path / "CON-02.json").write_text("{}", encoding="utf-8")
    loader = JSONValidatorLoader(str(tmp_path))

    class OtherValidator:
        def validate(self, definitie, begrip, context):
            return True, "Andere regel uitgevoerd", 1.0

    other = OtherValidator()
    loader._validators_cache["CON-02"] = other
    results = loader.validate_definitie(
        "een definitie", "begrip", ["CON-01", "CON-02"] if explicit else None
    )

    assert "onvolledig" in results[0].lower()
    assert "%" not in results[0]
    assert "ModularValidationService" in results[1]
    assert "CON-01" in results[1]
    assert "uitgefaseerd" in results[1].lower()
    assert not any(symbol in results[1] for symbol in ("✅", "❌", "%"))
    assert results[2] == "✅ CON-02: Andere regel uitgevoerd"
    assert loader.load_validator("CON-02") is other


@pytest.mark.parametrize("regel_id", ["CON_01", "con01"])
def test_retired_alias_diagnostic_directs_to_production_service(regel_id):
    from toetsregels.json_validator_loader import JSONValidatorLoader

    results = JSONValidatorLoader().validate_definitie(
        "een definitie", "begrip", [regel_id]
    )
    assert "onvolledig" in results[0].lower()
    assert "%" not in results[0]
    assert "ModularValidationService" in results[1]
    assert "Validator niet gevonden" not in results[1]


def test_legacy_con01_implementations_are_absent():
    root = Path(__file__).resolve().parents[3]
    assert not (root / "src/toetsregels/regels/CON-01.py").exists()
    assert not (root / "src/toetsregels/validators/CON_01.py").exists()
