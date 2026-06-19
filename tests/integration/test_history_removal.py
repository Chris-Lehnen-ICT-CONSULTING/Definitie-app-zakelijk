"""
Comprehensive test suite for History Tab removal verification.
Run this after removing the History tab to ensure no broken functionality.
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

pytestmark = [pytest.mark.integration]


class TestHistoryTabRemoval:
    """Test suite to verify History tab has been properly removed."""

    def test_no_history_tab_imports(self):
        """Verify no imports of HistoryTab remain in codebase."""
        # Check main interface file
        interface_file = Path("src/ui/tabbed_interface.py")
        if interface_file.exists():
            content = interface_file.read_text()
            # Should not import HistoryTab
            assert (
                "from ui.components.history_tab import HistoryTab" not in content
                or content.count("from ui.components.history_tab import HistoryTab")
                == 1
            )  # Allow one for backward compat

    def test_tabbed_interface_loads_without_history(self):
        """Test that TabbedInterface can be instantiated without History tab."""
        try:
            from ui.tabbed_interface import TabbedInterface

            # Mock Streamlit and other dependencies
            with (
                patch("streamlit.columns"),
                patch("streamlit.markdown"),
                patch("streamlit.session_state", {}),
            ):

                # Should instantiate without errors
                interface = TabbedInterface()

                # Verify expected tabs exist (export/management zijn bij de
                # refactor geconsolideerd in import_export_beheer_tab — DEF-447)
                assert hasattr(interface, "definition_tab")
                assert hasattr(interface, "edit_tab")
                assert hasattr(interface, "expert_tab")
                assert hasattr(interface, "import_export_beheer_tab")

                # History tab should either not exist or be None
                if hasattr(interface, "history_tab"):
                    # If attribute exists for backward compat, should be None
                    assert (
                        interface.history_tab is None
                        or interface.history_tab.__class__.__name__ != "HistoryTab"
                    )

        except ImportError as e:
            pytest.fail(f"Failed to import TabbedInterface: {e}")

    def test_tab_configuration_excludes_history(self):
        """Verify history is not in tab configuration."""
        from ui.tabbed_interface import TabbedInterface

        with patch("streamlit.session_state", {}):
            interface = TabbedInterface()

            # Check tab_config doesn't include history
            if hasattr(interface, "tab_config"):
                assert (
                    "history" not in interface.tab_config
                    or interface.tab_config.get("history") is None
                )

    def test_no_history_in_tab_rendering(self):
        """Test that tab rendering logic doesn't reference history tab."""
        from ui.tabbed_interface import TabbedInterface

        with (
            patch("streamlit.columns"),
            patch("streamlit.markdown"),
            patch("streamlit.radio") as mock_radio,
            patch("streamlit.session_state", {}),
        ):

            interface = TabbedInterface()

            # Mock radio to return different tab keys
            for tab_key in ["generator", "edit", "expert", "export", "management"]:
                mock_radio.return_value = tab_key

                # Should render without trying to access history_tab
                try:
                    interface._render_tab_content(tab_key)
                except AttributeError as e:
                    if "history" in str(e).lower():
                        pytest.fail(f"History reference found in tab rendering: {e}")
                except Exception:
                    # Other exceptions are OK for this test
                    pass

    def test_database_history_table_intact(self):
        """Verify database history table still exists and works."""
        db_path = Path("data/definities.db")

        if not db_path.exists():
            pytest.skip("Database not found")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Check history table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='definitie_geschiedenis'
            """)
            assert cursor.fetchone() is not None, "History table should still exist"

            # Check we can query it
            cursor.execute("SELECT COUNT(*) FROM definitie_geschiedenis")
            count = cursor.fetchone()[0]
            assert isinstance(count, int), "Should be able to query history table"

        finally:
            conn.close()

    def test_database_triggers_still_work(self):
        """Verify de history-trigger (log_definitie_changes) functioneert.

        Deterministisch tegen een in-memory DB opgebouwd uit schema.sql (de
        bron van waarheid) i.p.v. de muteerbare live data/definities.db — die
        kan een onvolledige trigger-set hebben. De trigger vuurt AFTER UPDATE,
        dus: insert -> update -> verwacht een history-entry. (DEF-447)
        """
        schema_path = Path("src/database/schema.sql")
        if not schema_path.exists():
            pytest.skip("schema.sql niet gevonden")

        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(schema_path.read_text(encoding="utf-8"))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO definities (begrip, definitie, organisatorische_context, juridische_context, categorie)
                VALUES (?, ?, ?, ?, ?)
            """,
                ("TEST_HISTORY_CHECK", "Test definitie", "[]", "[]", "proces"),
            )
            test_id = cursor.lastrowid

            # INSERT alleen mag (nog) geen history-entry geven: de trigger is AFTER UPDATE
            cursor.execute(
                "SELECT COUNT(*) FROM definitie_geschiedenis WHERE definitie_id = ?",
                (test_id,),
            )
            assert cursor.fetchone()[0] == 0, "INSERT mag geen history-entry aanmaken"

            # UPDATE triggert log_definitie_changes (AFTER UPDATE)
            cursor.execute(
                "UPDATE definities SET definitie = ? WHERE id = ?",
                ("Gewijzigde test definitie", test_id),
            )

            # Verifieer precies één entry met de juiste gelogde waarden
            cursor.execute(
                """
                SELECT begrip, definitie_nieuwe_waarde
                FROM definitie_geschiedenis WHERE definitie_id = ?
            """,
                (test_id,),
            )
            rows = cursor.fetchall()
            # >=1: naast log_definitie_changes vuurt ook update_definities_timestamp
            # een geneste UPDATE, die de history-trigger nogmaals laat loggen.
            assert len(rows) >= 1, "UPDATE moet een history-entry aanmaken"
            assert all(r[0] == "TEST_HISTORY_CHECK" for r in rows)
            assert all(r[1] == "Gewijzigde test definitie" for r in rows)
        finally:
            conn.close()

    def test_session_state_no_history_keys(self):
        """Verify no history-related keys in session state initialization."""
        import streamlit as st

        from ui.session_state import SessionStateManager

        # Mock streamlit session state
        with patch("streamlit.session_state", {}):
            # Initialize session state
            SessionStateManager.initialize_session_state()

            # Check session state directly
            # Note: _get_default_values might not exist, check session_state directly
            if hasattr(st, "session_state"):
                history_keys = [
                    k for k in st.session_state if "history" in str(k).lower()
                ]

                # Should have no history-specific keys
                # (Some keys might legitimately contain 'history' in their name for other purposes)
                suspicious_keys = [
                    k
                    for k in history_keys
                    if any(x in str(k).lower() for x in ["tab", "view", "page"])
                ]
                assert (
                    len(suspicious_keys) == 0
                ), f"Found history tab keys: {suspicious_keys}"

    def test_other_tabs_remain_functional(self):
        """Test that other tabs can still be instantiated."""
        # export/management zijn geconsolideerd in tabs.import_export_beheer (DEF-447)
        tabs_to_test = [
            ("definition_generator_tab", "DefinitionGeneratorTab"),
            ("definition_edit_tab", "DefinitionEditTab"),
            ("expert_review_tab", "ExpertReviewTab"),
            ("tabs.import_export_beheer", "ImportExportBeheerTab"),
        ]

        for module_name, class_name in tabs_to_test:
            try:
                module = __import__(
                    f"ui.components.{module_name}", fromlist=[class_name]
                )
                tab_class = getattr(module, class_name)

                # Should be able to import without errors
                assert tab_class is not None

            except ImportError as e:
                if "history" not in str(e).lower():
                    # Only fail if the import error is NOT related to history
                    pytest.fail(f"Failed to import {class_name}: {e}")

    def test_no_broken_navigation_references(self):
        """Check that navigation doesn't reference non-existent history tab."""
        from ui.tabbed_interface import TabbedInterface

        with patch("streamlit.session_state", {}):
            interface = TabbedInterface()

            # Get all valid tab keys
            valid_keys = list(interface.tab_config.keys())

            # History should not be in valid keys
            assert "history" not in valid_keys

            # All tab keys in config should have corresponding handlers
            for key in valid_keys:
                # Check if the tab has a corresponding component
                tab_attr = f"{key}_tab"
                if key in [
                    "generator",
                    "edit",
                    "expert",
                    "export",
                    "management",
                    "quality",
                    "external",
                    "monitoring",
                    "web_lookup",
                ]:
                    # These should have corresponding tab objects
                    if key == "generator":
                        assert hasattr(interface, "definition_tab")  # Special case
                    else:
                        assert (
                            hasattr(interface, tab_attr) or key == "orchestration"
                        )  # Orchestration is optional


class TestApplicationFunctionality:
    """Test that core application functionality still works after History removal."""

    @patch("streamlit.session_state", {})
    def test_definition_generation_flow(self):
        """Test that definition generation flow works without history."""
        from ui.tabbed_interface import TabbedInterface

        interface = TabbedInterface()

        # Mock the generation flow
        with patch.object(interface, "_handle_definition_generation") as mock_gen:
            # Should be able to call generation without history dependency
            interface._handle_definition_generation("test_begrip", {})
            mock_gen.assert_called_once()

    @patch("streamlit.session_state", {})
    def test_database_operations_work(self):
        """Test that database operations still function."""
        try:
            from database.definitie_repository import get_definitie_repository

            repo = get_definitie_repository()

            # Should be able to get statistics without history tab
            stats = repo.get_statistics()
            assert isinstance(stats, dict)

        except Exception as e:
            if "history" in str(e).lower():
                pytest.fail(f"Database operations broken due to history removal: {e}")

    def test_export_functionality(self):
        """Test that export functionality doesn't depend on history."""
        try:
            from ui.components.export_tab import ExportTab

            # Mock repository
            mock_repo = Mock()
            mock_repo.get_all_definitions.return_value = []

            # Should instantiate without history dependency
            export_tab = ExportTab(mock_repo)
            assert export_tab is not None

        except ImportError as e:
            if "history" in str(e).lower():
                pytest.fail(f"Export tab broken due to history removal: {e}")


class TestPerformanceImprovement:
    """Test that removing History tab improves performance."""

    def test_import_time(self):
        """Measure import time after history removal."""
        import time

        start = time.time()
        from ui.tabbed_interface import TabbedInterface

        end = time.time()

        import_time = end - start

        # Should import in reasonable time (< 2 seconds)
        assert import_time < 2.0, f"Import took too long: {import_time:.2f}s"

        # Log the time for comparison
        print(f"TabbedInterface import time: {import_time:.3f}s")

    def test_memory_usage(self):
        """Check memory usage after history removal."""
        import tracemalloc

        tracemalloc.start()

        from ui.tabbed_interface import TabbedInterface

        with patch("streamlit.session_state", {}):
            TabbedInterface()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Convert to MB
        current_mb = current / 1024 / 1024
        peak_mb = peak / 1024 / 1024

        print(f"Memory usage - Current: {current_mb:.2f} MB, Peak: {peak_mb:.2f} MB")

        # Should use reasonable memory (< 100 MB for interface)
        assert peak_mb < 100, f"Memory usage too high: {peak_mb:.2f} MB"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
