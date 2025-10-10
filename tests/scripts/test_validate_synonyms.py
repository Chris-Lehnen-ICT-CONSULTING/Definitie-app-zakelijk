"""
Unit tests for scripts/validate_synonyms.py

Tests all validation functions with various edge cases and fixtures.
"""

import sys
from pathlib import Path

import pytest
import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from validate_synonyms import (
    Colors,
    load_yaml_file,
    normalize_term,
    validate_circular_references,
    validate_cross_contamination,
    validate_duplicates_within_hoofdterm,
    validate_empty_lists,
    validate_normalization_consistency,
)


@pytest.fixture()
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures"


class TestNormalizeTerm:
    """Test the normalize_term function."""

    def test_lowercase(self):
        """Test that terms are converted to lowercase."""
        assert normalize_term("Onherroepelijk") == "onherroepelijk"
        assert normalize_term("VONNIS") == "vonnis"

    def test_strip_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        assert normalize_term("  onherroepelijk  ") == "onherroepelijk"
        assert normalize_term("\tvonnis\n") == "vonnis"

    def test_replace_underscores(self):
        """Test that underscores are replaced with spaces."""
        assert normalize_term("voorlopige_hechtenis") == "voorlopige hechtenis"
        assert normalize_term("kracht_van_gewijsde") == "kracht van gewijsde"

    def test_combined_normalization(self):
        """Test combined normalization rules."""
        assert normalize_term("  Voorlopige_Hechtenis  ") == "voorlopige hechtenis"
        assert normalize_term("KRACHT_VAN_GEWIJSDE") == "kracht van gewijsde"


class TestLoadYamlFile:
    """Test the load_yaml_file function."""

    def test_valid_yaml(self, fixtures_dir):
        """Test loading a valid YAML file."""
        data, errors = load_yaml_file(fixtures_dir / "valid_synoniemen.yaml")
        assert not errors
        assert isinstance(data, dict)
        assert "onherroepelijk" in data
        assert isinstance(data["onherroepelijk"], list)

    def test_nonexistent_file(self, tmp_path):
        """Test loading a nonexistent file."""
        data, errors = load_yaml_file(tmp_path / "nonexistent.yaml")
        assert errors
        assert "File not found" in errors[0]
        assert data == {}

    def test_invalid_yaml_syntax(self, fixtures_dir):
        """Test loading a file with invalid YAML syntax."""
        data, errors = load_yaml_file(fixtures_dir / "invalid_yaml_synoniemen.yaml")
        assert errors
        assert "YAML syntax error" in errors[0]
        assert data == {}

    def test_empty_yaml_file(self, tmp_path):
        """Test loading an empty YAML file."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")
        data, errors = load_yaml_file(empty_file)
        assert errors
        assert "empty" in errors[0].lower()

    def test_non_dict_yaml(self, tmp_path):
        """Test loading a YAML file that doesn't contain a dict at root."""
        list_file = tmp_path / "list.yaml"
        list_file.write_text("- item1\n- item2\n")
        data, errors = load_yaml_file(list_file)
        assert errors
        assert "Expected dict" in errors[0]


class TestValidateEmptyLists:
    """Test the validate_empty_lists function."""

    def test_no_empty_lists(self, fixtures_dir):
        """Test with valid file (no empty lists)."""
        data, _ = load_yaml_file(fixtures_dir / "valid_synoniemen.yaml")
        errors = validate_empty_lists(data)
        assert not errors

    def test_empty_list_detected(self, fixtures_dir):
        """Test detection of empty synonym lists."""
        data, _ = load_yaml_file(fixtures_dir / "empty_list_synoniemen.yaml")
        errors = validate_empty_lists(data)
        assert len(errors) == 1
        assert "empty_term" in errors[0]
        assert "Empty synonym list" in errors[0]

    def test_invalid_type_detected(self):
        """Test detection of non-list values."""
        data = {"term1": "not a list", "term2": ["valid", "list"]}
        errors = validate_empty_lists(data)
        assert len(errors) == 1
        assert "term1" in errors[0]
        assert "expected list" in errors[0]


class TestValidateDuplicatesWithinHoofdterm:
    """Test the validate_duplicates_within_hoofdterm function."""

    def test_no_duplicates(self, fixtures_dir):
        """Test with valid file (no duplicates)."""
        data, _ = load_yaml_file(fixtures_dir / "valid_synoniemen.yaml")
        errors = validate_duplicates_within_hoofdterm(data)
        assert not errors

    def test_exact_duplicates_detected(self, fixtures_dir):
        """Test detection of exact duplicates."""
        data, _ = load_yaml_file(fixtures_dir / "duplicate_synoniemen.yaml")
        errors = validate_duplicates_within_hoofdterm(data)
        # Should detect duplicates in both 'onherroepelijk' and 'verdachte'
        assert len(errors) >= 2
        assert any("verdachte" in e and "beklaagde" in e for e in errors)

    def test_normalized_duplicates_detected(self, fixtures_dir):
        """Test detection of duplicates after normalization."""
        data, _ = load_yaml_file(fixtures_dir / "duplicate_synoniemen.yaml")
        errors = validate_duplicates_within_hoofdterm(data)
        # Should detect 'kracht_van_gewijsde' as duplicate of 'kracht van gewijsde'
        assert any("onherroepelijk" in e and "kracht" in e.lower() for e in errors)

    def test_non_string_synonym_detected(self):
        """Test detection of non-string synonyms."""
        data = {"term1": ["valid", 123, "also valid"]}
        errors = validate_duplicates_within_hoofdterm(data)
        assert len(errors) == 1
        assert "Non-string synonym" in errors[0]
        assert "123" in errors[0]


class TestValidateCrossContamination:
    """Test the validate_cross_contamination function."""

    def test_no_cross_contamination(self, fixtures_dir):
        """Test with valid file (no cross-contamination)."""
        data, _ = load_yaml_file(fixtures_dir / "valid_synoniemen.yaml")
        errors = validate_cross_contamination(data)
        assert not errors

    def test_cross_contamination_detected(self, fixtures_dir):
        """Test detection of synonyms under multiple hoofdtermen."""
        data, _ = load_yaml_file(fixtures_dir / "cross_contamination_synoniemen.yaml")
        errors = validate_cross_contamination(data)
        # Should detect at least 2 cross-contaminations
        assert len(errors) >= 2
        # Check for specific cross-contaminations
        assert any("definitieve uitspraak" in e.lower() for e in errors)
        assert any("hogere voorziening" in e.lower() for e in errors)

    def test_cross_contamination_after_normalization(self):
        """Test cross-contamination detection with normalization."""
        data = {
            "term1": ["shared_synonym"],
            "term2": ["shared synonym"],  # Same after normalization
        }
        errors = validate_cross_contamination(data)
        assert len(errors) == 1
        assert "shared synonym" in errors[0]
        assert "term1" in errors[0] and "term2" in errors[0]


class TestValidateCircularReferences:
    """Test the validate_circular_references function."""

    def test_no_circular_references(self, fixtures_dir):
        """Test with valid file (no circular references)."""
        data, _ = load_yaml_file(fixtures_dir / "valid_synoniemen.yaml")
        errors = validate_circular_references(data)
        assert not errors

    def test_circular_references_detected(self, fixtures_dir):
        """Test detection of circular references."""
        data, _ = load_yaml_file(fixtures_dir / "circular_reference_synoniemen.yaml")
        errors = validate_circular_references(data)
        # Should detect at least 2 circular references
        assert len(errors) >= 2
        # Check for specific circular references
        assert any("vonnis" in e and "onherroepelijk" in e for e in errors)
        assert any("onherroepelijk" in e and "vonnis" in e for e in errors)

    def test_circular_reference_after_normalization(self):
        """Test circular reference detection with normalization."""
        data = {
            "term_one": ["term two"],  # 'term two' is also a hoofdterm
            "term_two": ["other"],
        }
        errors = validate_circular_references(data)
        assert len(errors) == 1
        assert "term two" in errors[0]


class TestValidateNormalizationConsistency:
    """Test the validate_normalization_consistency function."""

    def test_consistent_normalization(self, fixtures_dir):
        """Test with valid file (consistent normalization)."""
        data, _ = load_yaml_file(fixtures_dir / "valid_synoniemen.yaml")
        warnings = validate_normalization_consistency(data)
        assert not warnings

    def test_hoofdterm_with_spaces_warning(self, fixtures_dir):
        """Test warning for hoofdterm with spaces."""
        data, _ = load_yaml_file(fixtures_dir / "normalization_issues_synoniemen.yaml")
        warnings = validate_normalization_consistency(data)
        assert any("kracht van gewijsde" in w and "spaces" in w for w in warnings)

    def test_synonym_with_underscore_warning(self, fixtures_dir):
        """Test warning for synonym with underscore."""
        data, _ = load_yaml_file(fixtures_dir / "normalization_issues_synoniemen.yaml")
        warnings = validate_normalization_consistency(data)
        assert any("definitieve_uitspraak" in w and "underscore" in w for w in warnings)

    def test_whitespace_warnings(self, fixtures_dir):
        """Test warnings for leading/trailing whitespace."""
        data, _ = load_yaml_file(fixtures_dir / "normalization_issues_synoniemen.yaml")
        warnings = validate_normalization_consistency(data)
        # Should detect whitespace issues
        assert any("whitespace" in w.lower() for w in warnings)


class TestColorsClass:
    """Test the Colors class."""

    def test_colors_enabled_by_default(self):
        """Test that colors are enabled by default."""
        assert Colors.RED != ""
        assert Colors.GREEN != ""
        assert Colors.RESET != ""

    def test_disable_colors(self):
        """Test disabling colors."""
        # Save original values
        original_red = Colors.RED
        original_green = Colors.GREEN

        # Disable colors
        Colors.disable()

        assert Colors.RED == ""
        assert Colors.GREEN == ""
        assert Colors.RESET == ""

        # Restore (for other tests)
        Colors.RED = original_red
        Colors.GREEN = original_green


class TestIntegrationScenarios:
    """Integration tests with real-world scenarios."""

    def test_production_file_validation(self):
        """Test validation of the actual production file."""
        prod_file = (
            Path(__file__).parent.parent.parent
            / "config"
            / "juridische_synoniemen.yaml"
        )

        if not prod_file.exists():
            pytest.skip("Production file not found")

        data, errors = load_yaml_file(prod_file)
        assert not errors, f"Production file has YAML errors: {errors}"

        # Run all validations
        empty_errors = validate_empty_lists(data)
        dup_errors = validate_duplicates_within_hoofdterm(data)
        cross_errors = validate_cross_contamination(data)
        circular_errors = validate_circular_references(data)

        all_errors = empty_errors + dup_errors + cross_errors + circular_errors

        assert not all_errors, f"Production file has validation errors: {all_errors}"

    def test_large_file_performance(self, tmp_path):
        """Test performance with a large file."""
        # Create a large YAML file
        large_data = {}
        for i in range(1000):
            large_data[f"term_{i}"] = [f"synonym_{i}_{j}" for j in range(10)]

        large_file = tmp_path / "large.yaml"
        with open(large_file, "w") as f:
            yaml.dump(large_data, f)

        # Load and validate
        data, errors = load_yaml_file(large_file)
        assert not errors

        # Should handle large files efficiently
        validate_empty_lists(data)
        validate_duplicates_within_hoofdterm(data)
        validate_cross_contamination(data)
        validate_circular_references(data)

    def test_unicode_handling(self, tmp_path):
        """Test handling of Unicode characters."""
        unicode_file = tmp_path / "unicode.yaml"
        unicode_data = {
            "café": ["koffiehuis", "espressobar"],
            "naïef": ["onnozel", "eenvoudig"],
        }

        with open(unicode_file, "w", encoding="utf-8") as f:
            yaml.dump(unicode_data, f, allow_unicode=True)

        data, errors = load_yaml_file(unicode_file)
        assert not errors
        assert "café" in data
        assert "naïef" in data

        # Validations should work with Unicode
        all_errors = []
        all_errors.extend(validate_empty_lists(data))
        all_errors.extend(validate_duplicates_within_hoofdterm(data))
        all_errors.extend(validate_cross_contamination(data))
        all_errors.extend(validate_circular_references(data))

        assert not all_errors
