"""Unit tests voor de geëxternaliseerde category-mapping (DEF-394).

Borgt dat de prefix→category-mapping uit config komt (single source =
toetsregels_config.yaml), met de hardcoded dict als veilige fallback, en dat
nieuwe categorieën géén code-change meer vereisen.
"""

import textwrap
from pathlib import Path

import pytest

from services.validation import violation_builder as vb
from services.validation.violation_builder import _CATEGORY_PREFIXES, category_for_rule

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _reset_prefix_cache():
    """Wis de mapping-cache rond elke test (geen lekkage tussen tests)."""
    vb._load_category_prefixes.cache_clear()
    yield
    vb._load_category_prefixes.cache_clear()


class TestCategoryRegression:
    """Bestaand gedrag blijft identiek (geen gedragswijziging)."""

    @pytest.mark.parametrize(
        ("code", "expected"),
        [
            ("STR-01", "structuur"),
            ("INT-01", "structuur"),
            ("CON-01", "samenhang"),
            ("SAM-04", "samenhang"),
            ("ESS-02", "juridisch"),
            ("VAL-EMP-001", "juridisch"),
            ("ARAI-02", "taal"),
            ("VER-03", "taal"),
            ("LANG-INF-001", "taal"),
            ("ONBEKEND-99", "system"),
            # Edge cases: case-insensitieve tak (c.upper()) en niet-string input.
            ("str-01", "structuur"),
            ("", "system"),
            (None, "system"),
        ],
    )
    def test_category_for_rule(self, code, expected):
        assert category_for_rule(code) == expected


class TestExternalizedSource:
    """De mapping komt uit config en de config mag niet driften van de code."""

    def test_config_contains_mapping_matching_code_fallback(self):
        """toetsregels_config.yaml moet de mapping bevatten, gelijk aan de
        code-fallback (single source — geen drift)."""
        import yaml

        with open(vb._CONFIG_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        mapping = data.get("violation_category_prefixes")
        assert mapping is not None, "violation_category_prefixes ontbreekt in config"
        assert {str(k): str(v) for k, v in mapping.items()} == _CATEGORY_PREFIXES

    def test_loader_reads_from_config(self):
        """_load_category_prefixes levert de mapping uit het configbestand."""
        assert vb._load_category_prefixes() == _CATEGORY_PREFIXES

    def test_new_category_without_code_change(self, tmp_path, monkeypatch):
        """Een nieuwe prefix in config wordt opgepikt zonder code te wijzigen."""
        cfg = tmp_path / "toetsregels_config.yaml"
        cfg.write_text(
            textwrap.dedent("""\
                violation_category_prefixes:
                  "XYZ-": experimenteel
                  "STR-": structuur
                """),
            encoding="utf-8",
        )
        monkeypatch.setattr(vb, "_CONFIG_PATH", cfg)
        vb._load_category_prefixes.cache_clear()
        assert category_for_rule("XYZ-99") == "experimenteel"
        assert category_for_rule("STR-01") == "structuur"

    def test_fallback_to_code_when_config_missing(self, tmp_path, monkeypatch):
        """Ontbrekend/onleesbaar configbestand → veilige code-fallback."""
        monkeypatch.setattr(vb, "_CONFIG_PATH", tmp_path / "does_not_exist.yaml")
        vb._load_category_prefixes.cache_clear()
        assert vb._load_category_prefixes() == _CATEGORY_PREFIXES
        assert category_for_rule("ESS-02") == "juridisch"

    def _write_cfg(self, tmp_path, monkeypatch, body: str) -> None:
        cfg = tmp_path / "toetsregels_config.yaml"
        cfg.write_text(body, encoding="utf-8")
        monkeypatch.setattr(vb, "_CONFIG_PATH", cfg)
        vb._load_category_prefixes.cache_clear()

    def test_fallback_on_empty_section(self, tmp_path, monkeypatch):
        """Aanwezige maar lege sectie ({}) → code-fallback (niet-leeg-guard)."""
        self._write_cfg(tmp_path, monkeypatch, "violation_category_prefixes: {}\n")
        assert vb._load_category_prefixes() == _CATEGORY_PREFIXES

    def test_fallback_on_non_dict_section(self, tmp_path, monkeypatch):
        """Sectie van het verkeerde type (YAML-list) → code-fallback (type-guard)."""
        self._write_cfg(
            tmp_path,
            monkeypatch,
            "violation_category_prefixes:\n  - STR-\n  - CON-\n",
        )
        assert vb._load_category_prefixes() == _CATEGORY_PREFIXES

    def test_fallback_on_corrupt_yaml(self, tmp_path, monkeypatch):
        """Onparseerbare YAML → code-fallback (YAMLError-tak)."""
        self._write_cfg(
            tmp_path, monkeypatch, "violation_category_prefixes: [unbalanced\n"
        )
        assert vb._load_category_prefixes() == _CATEGORY_PREFIXES

    def test_fallback_on_invalid_utf8(self, tmp_path, monkeypatch):
        """Config met ongeldige UTF-8 bytes → code-fallback (UnicodeDecodeError-tak).

        Borgt dat de genarrowde except ook UnicodeDecodeError (subclass van
        ValueError, niet van OSError/YAMLError) afvangt — invariant: laden
        breekt nooit op een config-probleem.
        """
        cfg = tmp_path / "toetsregels_config.yaml"
        cfg.write_bytes(b"violation_category_prefixes:\n  \xff\xfe: taal\n")
        monkeypatch.setattr(vb, "_CONFIG_PATH", cfg)
        vb._load_category_prefixes.cache_clear()
        assert vb._load_category_prefixes() == _CATEGORY_PREFIXES
        assert category_for_rule("ESS-02") == "juridisch"

    def test_longest_prefix_wins_regardless_of_order(self, tmp_path, monkeypatch):
        """Bij overlappende prefixes met verschillende categorie wint de langste,
        onafhankelijk van de bronvolgorde (longest-prefix-match)."""
        # Korte prefix staat bewust vóór de langere in de bron.
        self._write_cfg(
            tmp_path,
            monkeypatch,
            textwrap.dedent("""\
                violation_category_prefixes:
                  "AB": taal
                  "ABC-": juridisch
                """),
        )
        assert category_for_rule("ABC-01") == "juridisch"
        assert category_for_rule("AB-99") == "taal"
