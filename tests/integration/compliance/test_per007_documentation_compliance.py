"""
Test suite for PER-007 documentation compliance after consolidation.
Validates that all PER-007 related content is preserved and accessible.

Dit zijn historische documentcontroles op aanwezigheid en tekstpatronen; geen
compliance-oordeel.

DEF-519: BASE_DIR wees naar tests/integration in plaats van de projectwortel,
waardoor elke controle in een niet-bestaande boom keek. Bronpaden die alleen
verplaatst zijn volgen nu hun aantoonbaar bestaande actuele locatie; een
ontbrekende verplichte bron faalt met het concrete pad in plaats van een
FileNotFoundError of een overgeslagen bron.

Dispositie van de resterende rode nodes (geen skip/xfail, blijven zichtbaar):
de ontbrekende SOLUTION_ARCHITECTURE.md / TECHNICAL_ARCHITECTURE.md-docfeiten
horen bij DEF-619; trigger is die story, herbeoordeling uiterlijk 2026-10-06.
Geen documenten herbouwd en geen complianceoplevering in deze batch.
"""

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.compliance]

# `advisory`-dispositie (DEF-519), per node en niet op bestandsniveau: de drie
# nodes zonder marker slagen op de huidige bron en blijven verplicht.
# Reden: PER007-documentatiefacts die nog niet geleverd zijn; de fixturefouten
# zijn hersteld, dus dit is echte documentatiedrift.
# Owner: DEF-619 (documentatiefacts).
# Trigger: DEF-619 levert de documentatiefacts, of het PER007-contract wordt
# formeel ingetrokken.
# Herbeoordeling: 2026-10-06.


class TestPER007DocumentationCompliance:
    """Validate PER-007 implementation documentation after consolidation."""

    # tests/integration/compliance/<dit bestand> -> parents[3] is de projectwortel.
    BASE_DIR = Path(__file__).resolve().parents[3]
    ARCH_DIR = BASE_DIR / "docs" / "architectuur"

    def test_base_dir_points_at_checkout(self):
        """Discriminator: de scope moet de echte checkout zijn, niet leeg."""
        assert (self.BASE_DIR / "pytest.ini").is_file(), self.BASE_DIR
        assert (self.BASE_DIR / "tests").is_dir(), self.BASE_DIR
        assert (self.BASE_DIR / "docs").is_dir(), self.BASE_DIR

    @pytest.mark.advisory
    def test_per007_coverage_in_solution_architecture(self):
        """Test that SA document contains comprehensive PER-007 documentation."""
        sa_path = self.ARCH_DIR / "SOLUTION_ARCHITECTURE.md"
        assert sa_path.exists(), f"SOLUTION_ARCHITECTURE.md not found at {sa_path}"

        with open(sa_path, encoding="utf-8") as f:
            content = f.read()

        # Check for PER-007 sections
        required_sections = [
            "PER-007",
            "Context Flow",
            "Presentation Layer",
            "Data Layer",
            "Anders Option",
            "Single Source of Truth",
        ]

        for section in required_sections:
            assert section in content, f"SA missing PER-007 section: {section}"

        # Check for specific PER-007 patterns
        assert (
            "context_flow" in content.lower()
        ), "Missing context_flow implementation details"
        assert "presentation" in content.lower(), "Missing presentation layer details"
        assert "anders_option" in content.lower(), "Missing anders_option details"

    @pytest.mark.advisory
    def test_per007_adr_references(self):
        """Test that PER-007 ADR is properly referenced or documented."""
        # Check if ADR exists in archive or is referenced in docs
        adr_locations = [
            self.BASE_DIR
            / "docs"
            / "architectuur"
            / "beslissingen"
            / "ADR-PER-007-presentation-data-separation.md",
            self.BASE_DIR
            / "docs"
            / "archief"
            / "ADR-PER-007-presentation-data-separation.md",
        ]

        adr_exists = any(path.exists() for path in adr_locations)

        # If ADR doesn't exist as separate file, check if it's documented in SA
        if not adr_exists:
            sa_path = self.ARCH_DIR / "SOLUTION_ARCHITECTURE.md"
            assert sa_path.exists(), (
                "PER-007 ADR niet gevonden op "
                f"{[str(p) for p in adr_locations]} en de terugvalbron ontbreekt: "
                f"{sa_path}"
            )
            with open(sa_path, encoding="utf-8") as f:
                content = f.read()

            # Check for ADR content within SA
            assert (
                "ADR" in content or "Architecture Decision" in content
            ), "PER-007 ADR not found and not documented in SA"

    @pytest.mark.advisory
    def test_per007_implementation_files_documented(self):
        """Test that PER-007 implementation files are documented."""
        ta_path = self.ARCH_DIR / "TECHNICAL_ARCHITECTURE.md"
        assert ta_path.exists(), f"TECHNICAL_ARCHITECTURE.md not found at {ta_path}"

        with open(ta_path, encoding="utf-8") as f:
            content = f.read()

        # Check for implementation file references
        implementation_files = [
            "context_flow.py",
            "streamlit_state_manager.py",
            "session_state_v2.py",
        ]

        documented_count = sum(1 for file in implementation_files if file in content)
        assert (
            documented_count >= 2
        ), f"Only {documented_count}/3 PER-007 implementation files documented in TA"

    def test_per007_test_coverage_documented(self):
        """Test that PER-007 test files are documented or exist."""
        test_files = [
            "test_per007_acceptance.py",
            "test_per007_anders_option_red.py",
            "test_per007_single_source_red.py",
            "test_per007_ui_separation_red.py",
            "test_per007_antipatterns.py",
            "test_per007_performance.py",
        ]

        tests_dir = self.BASE_DIR / "tests"
        assert tests_dir.is_dir(), f"tests-map ontbreekt: {tests_dir}"

        # De testbestanden zijn alleen verplaatst naar submappen (unit/,
        # integration/, integration/performance/); zoek ze daarom recursief op
        # exact dezelfde bestandsnaam. Geen vervangende bestanden.
        existing_tests = [
            test_file for test_file in test_files if any(tests_dir.rglob(test_file))
        ]

        assert len(existing_tests) >= 4, (
            f"Only {len(existing_tests)}/6 PER-007 test files exist; "
            f"gevonden: {existing_tests}"
        )

    def test_per007_compliance_report_exists(self):
        """Test that PER-007 compliance report exists."""
        possible_locations = [
            self.BASE_DIR / "docs" / "PER-007-COMPLIANCE-REPORT.md",
            self.BASE_DIR / "docs" / "testing" / "PER-007-COMPLIANCE-REPORT.md",
            self.BASE_DIR / "docs" / "architectuur" / "PER-007-COMPLIANCE-REPORT.md",
            # Verplaatst, niet vervangen: hetzelfde rapportbestand staat nu in
            # het gedateerde archief. De mapnaam is kleingeschreven — zo staat
            # hij getrackt in git. Op de hoofdletterongevoelige macOS-checkout
            # viel het verschil weg; op Linux-CI niet (PR #427, integration-job
            # 101574083642).
            self.BASE_DIR
            / "docs"
            / "archief"
            / "2025-09-05"
            / "PER-007-COMPLIANCE-REPORT.md",
        ]

        report_exists = any(path.exists() for path in possible_locations)
        assert report_exists, (
            "PER-007 compliance report not found in expected locations: "
            f"{[str(p) for p in possible_locations]}"
        )

    @pytest.mark.advisory
    def test_per007_workflows_documented(self):
        """Test that PER-007 workflows are documented."""
        # Check in SA or workflows directory
        sa_path = self.ARCH_DIR / "SOLUTION_ARCHITECTURE.md"
        assert sa_path.exists(), f"Verplichte bron ontbreekt: {sa_path}"

        with open(sa_path, encoding="utf-8") as f:
            sa_content = f.read()

        workflow_keywords = [
            "workflow",
            "process flow",
            "data flow",
            "context propagation",
        ]

        found_workflows = sum(
            1 for keyword in workflow_keywords if keyword.lower() in sa_content.lower()
        )

        assert (
            found_workflows >= 2
        ), f"Insufficient PER-007 workflow documentation (found {found_workflows}/4 keywords)"

    @pytest.mark.advisory
    def test_per007_validation_rules_preserved(self):
        """Test that PER-007 validation rules are preserved in documentation."""
        ta_path = self.ARCH_DIR / "TECHNICAL_ARCHITECTURE.md"
        assert ta_path.exists(), f"Verplichte bron ontbreekt: {ta_path}"

        with open(ta_path, encoding="utf-8") as f:
            content = f.read()

        # Check for validation rule mentions
        validation_patterns = [
            r"validation",
            r"toetsregel",
            r"rule.*PER-?007",
            r"constraint",
        ]

        found_patterns = 0
        for pattern in validation_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns += 1

        assert (
            found_patterns >= 2
        ), f"Insufficient validation rule documentation (found {found_patterns}/4 patterns)"

    @pytest.mark.advisory
    def test_per007_migration_status_documented(self):
        """Test that PER-007 migration/implementation status is documented."""
        docs_to_check = [
            self.ARCH_DIR / "SOLUTION_ARCHITECTURE.md",
            self.ARCH_DIR / "TECHNICAL_ARCHITECTURE.md",
        ]

        ontbrekend = [str(p) for p in docs_to_check if not p.exists()]
        assert not ontbrekend, f"Verplichte bron(nen) ontbreken: {ontbrekend}"

        status_found = False
        for doc_path in docs_to_check:
            with open(doc_path, encoding="utf-8") as f:
                content = f.read()

            # Check for status indicators
            if any(
                keyword in content.lower()
                for keyword in [
                    "implemented",
                    "complete",
                    "status",
                    "progress",
                    "migrated",
                ]
            ):
                status_found = True
                break

        assert status_found, "PER-007 implementation status not documented"

    @pytest.mark.advisory
    def test_per007_backwards_compatibility_noted(self):
        """Test that backwards compatibility considerations are documented."""
        sa_path = self.ARCH_DIR / "SOLUTION_ARCHITECTURE.md"
        assert sa_path.exists(), f"Verplichte bron ontbreekt: {sa_path}"

        with open(sa_path, encoding="utf-8") as f:
            content = f.read()

        compatibility_keywords = [
            "backward",
            "compatibility",
            "migration",
            "legacy",
            "v1",
            "v2",
        ]

        found_keywords = sum(
            1
            for keyword in compatibility_keywords
            if keyword.lower() in content.lower()
        )

        assert (
            found_keywords >= 3
        ), f"Insufficient backwards compatibility documentation (found {found_keywords}/6 keywords)"

    @pytest.mark.advisory
    def test_per007_configuration_documented(self):
        """Test that PER-007 configuration is documented."""
        ta_path = self.ARCH_DIR / "TECHNICAL_ARCHITECTURE.md"
        assert ta_path.exists(), f"Verplichte bron ontbreekt: {ta_path}"

        with open(ta_path, encoding="utf-8") as f:
            content = f.read()

        config_indicators = ["config", "environment", "settings", "parameters"]

        config_found = sum(
            1 for indicator in config_indicators if indicator.lower() in content.lower()
        )

        assert (
            config_found >= 2
        ), f"Insufficient configuration documentation (found {config_found}/4 indicators)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
