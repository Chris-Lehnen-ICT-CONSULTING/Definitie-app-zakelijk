"""
Tests voor YAMLConfigUpdater.

Test coverage:
- Add/remove synonyms
- Backup creation and rollback
- YAML validation
- Duplicate detection
- Weighted synonym format support
"""

import contextlib
import shutil
from pathlib import Path

import pytest
import yaml

from src.services.synonym_automation.yaml_updater import (
    YAMLConfigUpdater,
    YAMLUpdateError,
)


class TestYAMLConfigUpdater:
    """Tests voor YAMLConfigUpdater."""

    @pytest.fixture()
    def test_yaml_path(self, tmp_path):
        """Create test YAML file."""
        yaml_path = tmp_path / "test_synoniemen.yaml"

        # Create initial YAML content
        initial_data = {
            "voorlopige_hechtenis": ["voorarrest", "bewaring"],
            "verdachte": ["beklaagde", "beschuldigde"],
            "vonnis": [
                {"synoniem": "uitspraak", "weight": 0.95},
                {"synoniem": "arrest", "weight": 0.85},
            ],
        }

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(initial_data, f, allow_unicode=True)

        return yaml_path

    @pytest.fixture()
    def updater(self, test_yaml_path, tmp_path):
        """Create YAMLConfigUpdater with test file."""
        backup_dir = tmp_path / "backups"
        return YAMLConfigUpdater(yaml_path=test_yaml_path, backup_dir=backup_dir)

    def test_load_yaml(self, updater):
        """Test loading YAML data."""
        data = updater._load_yaml()

        assert "voorlopige_hechtenis" in data
        assert "voorarrest" in data["voorlopige_hechtenis"]
        assert isinstance(data, dict)

    def test_normalize_hoofdterm(self, updater):
        """Test hoofdterm normalization."""
        # Spaces → underscores
        assert (
            updater._normalize_hoofdterm("voorlopige hechtenis")
            == "voorlopige_hechtenis"
        )

        # Already underscores
        assert (
            updater._normalize_hoofdterm("voorlopige_hechtenis")
            == "voorlopige_hechtenis"
        )

        # Whitespace trimming
        assert updater._normalize_hoofdterm("  test term  ") == "test_term"

    def test_create_backup(self, updater, tmp_path):
        """Test backup creation."""
        backup_path = updater._create_backup()

        assert backup_path.exists()
        assert backup_path.parent == updater.backup_dir
        assert backup_path.name.startswith("juridische_synoniemen_")
        assert backup_path.suffix == ".yaml"

    def test_validate_yaml_valid(self, updater):
        """Test YAML validation with valid data."""
        valid_data = {
            "term1": ["syn1", "syn2"],
            "term2": [
                {"synoniem": "syn3", "weight": 0.95},
            ],
            "_clusters": {"cluster1": ["term1", "term2"]},  # Reserved key OK
        }

        # Should not raise
        updater._validate_yaml(valid_data)

    def test_validate_yaml_invalid_not_dict(self, updater):
        """Test YAML validation rejects non-dict root."""
        with pytest.raises(YAMLUpdateError, match="dictionary zijn"):
            updater._validate_yaml(["not", "a", "dict"])

    def test_validate_yaml_invalid_synoniemen_not_list(self, updater):
        """Test YAML validation rejects non-list synoniemen."""
        invalid_data = {
            "term1": "not a list",  # Should be list
        }

        with pytest.raises(YAMLUpdateError, match="moet een list zijn"):
            updater._validate_yaml(invalid_data)

    def test_validate_yaml_invalid_weighted_format(self, updater):
        """Test YAML validation rejects weighted format without synoniem key."""
        invalid_data = {"term1": [{"weight": 0.95}]}  # Missing 'synoniem' key

        with pytest.raises(YAMLUpdateError, match="mist 'synoniem' key"):
            updater._validate_yaml(invalid_data)

    def test_add_synonym_plain_format(self, updater):
        """Test adding synoniem in plain string format."""
        success = updater.add_synonym(
            hoofdterm="voorlopige hechtenis", synoniem="preventieve detentie"
        )

        assert success

        # Verify added
        synoniemen = updater.get_synonyms("voorlopige hechtenis")
        assert "preventieve detentie" in synoniemen

    def test_add_synonym_weighted_format(self, updater):
        """Test adding synoniem in weighted format."""
        success = updater.add_synonym(
            hoofdterm="voorlopige hechtenis", synoniem="gevangenhouding", weight=0.70
        )

        assert success

        # Verify added (check raw data for weight)
        data = updater._load_yaml()
        synoniemen_list = data["voorlopige_hechtenis"]

        # Find the weighted entry
        found = False
        for item in synoniemen_list:
            if isinstance(item, dict):
                if item["synoniem"] == "gevangenhouding":
                    assert item["weight"] == 0.70
                    found = True
                    break

        assert found

    def test_add_synonym_new_hoofdterm(self, updater):
        """Test adding synoniem for new hoofdterm."""
        success = updater.add_synonym(
            hoofdterm="cassatie", synoniem="hogere voorziening"
        )

        assert success

        # Verify hoofdterm created
        synoniemen = updater.get_synonyms("cassatie")
        assert "hogere voorziening" in synoniemen

    def test_add_synonym_duplicate_skip(self, updater):
        """Test dat duplicate synoniem geskipped wordt."""
        # Add first time
        success1 = updater.add_synonym("verdachte", "beklaagde")
        assert not success1  # Already exists in test data

        # Verify not duplicated
        synoniemen = updater.get_synonyms("verdachte")
        assert synoniemen.count("beklaagde") == 1

    def test_add_synonym_duplicate_raise_error(self, updater):
        """Test dat duplicate error raised kan worden."""
        with pytest.raises(YAMLUpdateError, match="already exists"):
            updater.add_synonym(
                hoofdterm="verdachte", synoniem="beklaagde", skip_if_exists=False
            )

    def test_add_synonym_invalid_weight_raises_error(self, updater):
        """Test dat invalide weight een error geeft."""
        with pytest.raises(YAMLUpdateError, match="tussen 0.0 en 1.0"):
            updater.add_synonym("test", "test2", weight=1.5)  # Out of range

    def test_remove_synonym_plain_format(self, updater):
        """Test removing synoniem in plain format."""
        success = updater.remove_synonym(
            hoofdterm="voorlopige hechtenis", synoniem="voorarrest"
        )

        assert success

        # Verify removed
        synoniemen = updater.get_synonyms("voorlopige hechtenis")
        assert "voorarrest" not in synoniemen

    def test_remove_synonym_weighted_format(self, updater):
        """Test removing synoniem in weighted format."""
        success = updater.remove_synonym(hoofdterm="vonnis", synoniem="uitspraak")

        assert success

        # Verify removed
        synoniemen = updater.get_synonyms("vonnis")
        assert "uitspraak" not in synoniemen

    def test_remove_synonym_not_found_returns_false(self, updater):
        """Test dat remove False returnt voor non-existent synoniem."""
        success = updater.remove_synonym("verdachte", "non-existent-synonym")

        assert not success

    def test_remove_synonym_hoofdterm_not_found_returns_false(self, updater):
        """Test dat remove False returnt voor non-existent hoofdterm."""
        success = updater.remove_synonym("non-existent-term", "synoniem")

        assert not success

    def test_get_synonyms(self, updater):
        """Test ophalen synoniemen."""
        synoniemen = updater.get_synonyms("voorlopige hechtenis")

        assert "voorarrest" in synoniemen
        assert "bewaring" in synoniemen
        assert len(synoniemen) == 2

    def test_get_synonyms_weighted_format(self, updater):
        """Test ophalen synoniemen met weighted format."""
        synoniemen = updater.get_synonyms("vonnis")

        # Should extract plain strings from weighted format
        assert "uitspraak" in synoniemen
        assert "arrest" in synoniemen

    def test_get_synonyms_non_existent_returns_empty(self, updater):
        """Test dat get_synonyms lege lijst returnt voor non-existent term."""
        synoniemen = updater.get_synonyms("non-existent-term")

        assert synoniemen == []

    def test_backup_and_rollback(self, updater, test_yaml_path):
        """Test backup creation and rollback on error."""
        # Get original content
        with open(test_yaml_path, encoding="utf-8") as f:
            original_content = f.read()

        # Force an error by corrupting the YAML after adding
        backup_path = updater._create_backup()

        # Write invalid YAML
        with open(test_yaml_path, "w") as f:
            f.write("this is not valid yaml: {")

        # Restore backup
        updater._restore_backup(backup_path)

        # Verify restored
        with open(test_yaml_path, encoding="utf-8") as f:
            restored_content = f.read()

        assert restored_content == original_content

    def test_cleanup_old_backups(self, updater, tmp_path):
        """Test cleanup van oude backups."""
        from datetime import UTC, datetime, timedelta

        # Ensure backup dir exists
        updater.backup_dir.mkdir(parents=True, exist_ok=True)

        # Create 15 backups with different timestamps by directly creating files
        # (instead of using _create_backup which uses current timestamp)
        for i in range(15):
            # Generate timestamp offset by i seconds
            timestamp = (datetime.now(UTC) - timedelta(seconds=i)).strftime(
                "%Y%m%d_%H%M%S"
            )
            backup_path = (
                updater.backup_dir / f"juridische_synoniemen_{timestamp}_{i}.yaml"
            )
            # Copy the current config to the backup
            shutil.copy2(updater.yaml_path, backup_path)

        # Verify we have 15 backups
        backups_before = list(updater.backup_dir.glob("juridische_synoniemen_*.yaml"))
        assert len(backups_before) == 15

        # Cleanup (keep only 10)
        updater.cleanup_old_backups(keep_count=10)

        # Verify count after cleanup
        backups_after = list(updater.backup_dir.glob("juridische_synoniemen_*.yaml"))
        assert len(backups_after) == 10

    def test_write_preserves_formatting(self, updater, test_yaml_path):
        """Test dat write YAML formatting preserved."""
        # Add synonym
        updater.add_synonym("test_term", "test_syn")

        # Read raw YAML
        with open(test_yaml_path, encoding="utf-8") as f:
            content = f.read()

        # Check readable formatting
        assert "test_term:" in content
        assert "test_syn" in content
        assert content.count("\n") > 5  # Multiple lines


class TestIntegration:
    """Integration tests voor complete workflows."""

    @pytest.fixture()
    def test_yaml_path(self, tmp_path):
        """Create test YAML file."""
        yaml_path = tmp_path / "test_synoniemen.yaml"

        initial_data = {
            "voorlopige_hechtenis": ["voorarrest"],
            "verdachte": ["beklaagde"],
        }

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(initial_data, f, allow_unicode=True)

        return yaml_path

    @pytest.fixture()
    def updater(self, test_yaml_path, tmp_path):
        """Create YAMLConfigUpdater."""
        backup_dir = tmp_path / "backups"
        return YAMLConfigUpdater(yaml_path=test_yaml_path, backup_dir=backup_dir)

    def test_complete_workflow_add_approve_remove(self, updater):
        """Test complete workflow: add → verify → remove."""
        # Step 1: Add synonym
        success = updater.add_synonym("voorlopige hechtenis", "bewaring", weight=0.90)
        assert success

        # Step 2: Verify added
        synoniemen = updater.get_synonyms("voorlopige hechtenis")
        assert "bewaring" in synoniemen
        assert len(synoniemen) == 2  # voorarrest + bewaring

        # Step 3: Remove synonym
        success = updater.remove_synonym("voorlopige hechtenis", "bewaring")
        assert success

        # Step 4: Verify removed
        synoniemen_after = updater.get_synonyms("voorlopige hechtenis")
        assert "bewaring" not in synoniemen_after
        assert len(synoniemen_after) == 1  # Only voorarrest

    def test_batch_additions(self, updater):
        """Test batch adding multiple synonyms."""
        batch_additions = [
            ("voorlopige hechtenis", "bewaring", 0.90),
            ("voorlopige hechtenis", "preventieve detentie", 0.80),
            ("verdachte", "beschuldigde", 0.90),
            ("verdachte", "aangeklaagde", 0.85),
        ]

        # Add all
        for hoofdterm, synoniem, weight in batch_additions:
            updater.add_synonym(hoofdterm, synoniem, weight)

        # Verify voorlopige hechtenis
        vh_synoniemen = updater.get_synonyms("voorlopige hechtenis")
        assert len(vh_synoniemen) == 3  # voorarrest + bewaring + preventieve detentie

        # Verify verdachte
        vd_synoniemen = updater.get_synonyms("verdachte")
        assert len(vd_synoniemen) == 3  # beklaagde + beschuldigde + aangeklaagde

    def test_error_rollback(self, updater, test_yaml_path):
        """Test dat error correct rollback doet."""
        # Get original state
        original_synoniemen = updater.get_synonyms("verdachte")

        # Try to add with invalid weight (should fail)
        with contextlib.suppress(YAMLUpdateError):
            updater.add_synonym("verdachte", "test", weight=2.0)

        # Verify rollback - state should be unchanged
        current_synoniemen = updater.get_synonyms("verdachte")
        assert current_synoniemen == original_synoniemen
