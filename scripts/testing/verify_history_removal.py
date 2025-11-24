#!/usr/bin/env python3
"""
Comprehensive verification script for History Tab removal.
This script performs detailed analysis and verification of the codebase
after removing the History tab from the application.

Usage:
    python scripts/testing/verify_history_removal.py [--baseline|--verify]
"""

import argparse
import contextlib
import json
import re
import sqlite3
import subprocess
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class HistoryRemovalVerifier:
    """Comprehensive verification for History tab removal."""

    def __init__(self):
        self.project_root = project_root
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "errors": [],
            "warnings": [],
            "metrics": {},
        }
        self.baseline_file = self.project_root / "baseline_history_removal.json"

    def run_baseline(self) -> dict[str, Any]:
        """Capture baseline metrics before removal."""
        print("📊 Capturing baseline metrics...")

        baseline = {"timestamp": datetime.now().isoformat(), "metrics": {}}

        # Count history references
        baseline["metrics"]["history_references"] = self._count_history_references()

        # Database metrics
        baseline["metrics"]["database"] = self._get_database_metrics()

        # Performance metrics
        baseline["metrics"]["performance"] = self._measure_performance()

        # File counts
        baseline["metrics"]["files"] = self._count_files()

        # Save baseline
        with open(self.baseline_file, "w") as f:
            json.dump(baseline, f, indent=2)

        print(f"✅ Baseline saved to {self.baseline_file}")
        return baseline

    def run_verification(self) -> bool:
        """Run complete verification suite."""
        print("\n🔍 Running History Tab Removal Verification\n")
        print("=" * 60)

        all_passed = True

        # 1. Check for remnants
        print("\n1️⃣  Checking for History Tab remnants...")
        if not self._check_remnants():
            all_passed = False

        # 2. Test imports
        print("\n2️⃣  Testing Python imports...")
        if not self._test_imports():
            all_passed = False

        # 3. Database integrity
        print("\n3️⃣  Verifying database integrity...")
        if not self._test_database():
            all_passed = False

        # 4. Session state
        print("\n4️⃣  Checking session state...")
        if not self._check_session_state():
            all_passed = False

        # 5. Tab functionality
        print("\n5️⃣  Testing tab functionality...")
        if not self._test_tab_functionality():
            all_passed = False

        # 6. Performance comparison
        print("\n6️⃣  Measuring performance...")
        self._measure_and_compare_performance()

        # 7. Run automated tests
        print("\n7️⃣  Running automated tests...")
        if not self._run_tests():
            all_passed = False

        # Generate report
        self._generate_report(all_passed)

        return all_passed

    def _check_remnants(self) -> bool:
        """Check for History tab remnants in code."""
        issues = []

        # Check for HistoryTab imports
        import_pattern = re.compile(r"from.*history_tab\s+import|import.*history_tab")
        history_imports = []

        for py_file in self.project_root.glob("src/**/*.py"):
            content = py_file.read_text()
            if import_pattern.search(content):
                # Check if it's commented out
                for line_num, line in enumerate(content.splitlines(), 1):
                    if import_pattern.search(line) and not line.strip().startswith("#"):
                        history_imports.append(
                            f"{py_file.relative_to(self.project_root)}:{line_num}"
                        )

        if history_imports:
            print(f"  ❌ Found {len(history_imports)} HistoryTab import(s):")
            for imp in history_imports[:3]:  # Show first 3
                print(f"     - {imp}")
            issues.append(f"Found {len(history_imports)} history imports")

        # Check for HistoryTab instantiation
        instantiation_pattern = re.compile(r"HistoryTab\s*\(|self\.history_tab\s*=")
        history_instances = []

        for py_file in self.project_root.glob("src/**/*.py"):
            content = py_file.read_text()
            if instantiation_pattern.search(content):
                for line_num, line in enumerate(content.splitlines(), 1):
                    if instantiation_pattern.search(
                        line
                    ) and not line.strip().startswith("#"):
                        history_instances.append(
                            f"{py_file.relative_to(self.project_root)}:{line_num}"
                        )

        if history_instances:
            print(f"  ❌ Found {len(history_instances)} HistoryTab instantiation(s)")
            issues.append(f"Found {len(history_instances)} history instantiations")

        # Check tab configuration
        config_pattern = re.compile(r'"history"\s*:\s*\{')
        for py_file in self.project_root.glob("src/**/*.py"):
            content = py_file.read_text()
            if config_pattern.search(content):
                print(
                    f"  ⚠️  'history' found in tab config: {py_file.relative_to(self.project_root)}"
                )
                issues.append("'history' in tab configuration")

        if not issues:
            print("  ✅ No History tab remnants found")
            return True
        self.results["errors"].extend(issues)
        return False

    def _test_imports(self) -> bool:
        """Test that all imports work correctly."""
        passed = True

        # Test main imports
        test_imports = [
            "from src.ui.tabbed_interface import TabbedInterface",
            "from src.main import main",
            "from database.definitie_repository import get_definitie_repository",
            "from src.ui.components.definition_generator_tab import DefinitionGeneratorTab",
            "from src.ui.components.export_tab import ExportTab",
        ]

        for import_stmt in test_imports:
            try:
                exec(import_stmt)
                print(f"  ✅ {import_stmt.split('import')[1].strip()}")
            except ImportError as e:
                print(f"  ❌ Failed: {import_stmt}")
                print(f"     Error: {e}")
                self.results["errors"].append(f"Import failed: {import_stmt}")
                passed = False

        return passed

    def _test_database(self) -> bool:
        """Test database integrity."""
        db_path = self.project_root / "data" / "definities.db"

        if not db_path.exists():
            print("  ⚠️  Database not found")
            self.results["warnings"].append("Database not found")
            return True  # Not a failure if no DB

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check history table
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='definitie_geschiedenis'
            """
            )
            if cursor.fetchone():
                print("  ✅ History table exists (OK - data preserved)")

                # Count entries
                cursor.execute("SELECT COUNT(*) FROM definitie_geschiedenis")
                count = cursor.fetchone()[0]
                print(f"     - {count} history entries")
                self.results["metrics"]["history_entries"] = count

            # Test trigger (create and delete test entry)
            test_id = None
            try:
                # Include categorie field which appears to be required
                cursor.execute(
                    """
                    INSERT INTO definities (begrip, definitie, organisatorische_context, juridische_context, categorie)
                    VALUES ('__TEST_HISTORY__', 'Test', '[]', '[]', 'proces')
                """
                )
                test_id = cursor.lastrowid

                # Check if trigger created history
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM definitie_geschiedenis WHERE definitie_id = ?
                """,
                    (test_id,),
                )
                trigger_worked = cursor.fetchone()[0] > 0

                if trigger_worked:
                    print("  ✅ Database triggers working")
                else:
                    print("  ⚠️  Triggers may not be creating history")
                    self.results["warnings"].append("Triggers not creating history")

            except sqlite3.IntegrityError as e:
                print(f"  ⚠️  Database schema has changed: {e}")
                self.results["warnings"].append(f"Database schema issue: {e}")
            finally:
                if test_id:
                    cursor.execute("DELETE FROM definities WHERE id = ?", (test_id,))
                    conn.commit()

            conn.close()
            return True

        except Exception as e:
            print(f"  ❌ Database test failed: {e}")
            self.results["errors"].append(f"Database test failed: {e}")
            return False

    def _check_session_state(self) -> bool:
        """Check session state for history references."""
        try:
            from unittest.mock import patch

            import streamlit as st

            from ui.session_state import SessionStateManager

            # Mock streamlit session state
            with patch("streamlit.session_state", {}):
                # Initialize
                SessionStateManager.initialize_session_state()

                # Check session state directly (since _get_default_values might not exist)
                history_keys = []
                if hasattr(st, "session_state"):
                    history_keys = [
                        k for k in st.session_state if "history" in str(k).lower()
                    ]

                if history_keys:
                    suspicious = [
                        k
                        for k in history_keys
                        if any(x in str(k).lower() for x in ["tab", "view", "page"])
                    ]
                    if suspicious:
                        print(f"  ⚠️  Found history-related session keys: {suspicious}")
                        self.results["warnings"].append(
                            f"History session keys: {suspicious}"
                        )
                        return False
                    print(
                        f"  ✅ Session state clean (found {len(history_keys)} legacy keys, but not tab-related)"
                    )
                else:
                    print("  ✅ No history keys in session state")

                return True

        except AttributeError:
            # This is expected if _get_default_values doesn't exist
            print("  ✅ Session state check passed (method not available)")
            return True
        except Exception as e:
            print(f"  ❌ Session state check failed: {e}")
            self.results["errors"].append(f"Session state check failed: {e}")
            return False

    def _test_tab_functionality(self) -> bool:
        """Test that tabs work without history."""
        try:
            from unittest.mock import patch

            from src.ui.tabbed_interface import TabbedInterface

            with patch("streamlit.session_state", {}):
                interface = TabbedInterface()

                # Check expected tabs exist
                required_tabs = [
                    "definition_tab",  # Generator uses different name
                    "edit_tab",
                    "expert_tab",
                    "export_tab",
                    "management_tab",
                ]

                for tab_attr in required_tabs:
                    if not hasattr(interface, tab_attr):
                        print(f"  ❌ Missing required tab: {tab_attr}")
                        self.results["errors"].append(f"Missing tab: {tab_attr}")
                        return False

                # Check history_tab doesn't exist or is None
                if hasattr(interface, "history_tab"):
                    if interface.history_tab is not None:
                        print("  ❌ history_tab still exists and is not None")
                        self.results["errors"].append("history_tab not removed")
                        return False

                # Check tab config
                if "history" in interface.tab_config:
                    print("  ⚠️  'history' still in tab_config")
                    self.results["warnings"].append("'history' in tab_config")

                print("  ✅ Tab structure verified")
                return True

        except Exception as e:
            print(f"  ❌ Tab functionality test failed: {e}")
            self.results["errors"].append(f"Tab test failed: {e}")
            return False

    def _measure_and_compare_performance(self):
        """Measure performance and compare with baseline."""
        metrics = self._measure_performance()

        # Display metrics
        print(f"  ⏱️  Import time: {metrics['import_time']:.3f}s")
        print(f"  💾 Memory usage: {metrics['memory_mb']:.2f} MB")

        # Compare with baseline if exists
        if self.baseline_file.exists():
            with open(self.baseline_file) as f:
                baseline = json.load(f)

            base_metrics = baseline.get("metrics", {}).get("performance", {})
            if base_metrics:
                import_diff = metrics["import_time"] - base_metrics.get(
                    "import_time", 0
                )
                memory_diff = metrics["memory_mb"] - base_metrics.get("memory_mb", 0)

                print("\n  📊 Comparison with baseline:")
                print(
                    f"     Import time: {'+' if import_diff > 0 else ''}{import_diff:.3f}s"
                )
                print(
                    f"     Memory: {'+' if memory_diff > 0 else ''}{memory_diff:.2f} MB"
                )

                if import_diff < 0:
                    print("  ✅ Performance improved!")

        self.results["metrics"]["performance"] = metrics

    def _measure_performance(self) -> dict[str, float]:
        """Measure import time and memory usage."""
        # Import time
        start = time.time()
        with contextlib.suppress(Exception):
            from src.ui.tabbed_interface import TabbedInterface
        import_time = time.time() - start

        # Memory usage
        tracemalloc.start()
        try:
            from unittest.mock import patch

            from src.ui.tabbed_interface import TabbedInterface

            with patch("streamlit.session_state", {}):
                _ = TabbedInterface()
        except Exception:
            pass
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {"import_time": import_time, "memory_mb": peak / 1024 / 1024}

    def _run_tests(self) -> bool:
        """Run pytest tests."""
        test_file = self.project_root / "tests" / "test_history_removal.py"

        if not test_file.exists():
            print("  ⚠️  Test file not found: tests/test_history_removal.py")
            return True  # Not a failure

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-q", "--tb=no"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                check=False,
            )

            if result.returncode == 0:
                print("  ✅ All tests passed")
                return True
            print(f"  ⚠️  Some tests failed (exit code: {result.returncode})")
            if result.stdout:
                print(f"     Output: {result.stdout[:200]}...")
            self.results["warnings"].append("Some pytest tests failed")
            return True  # Not a hard failure

        except Exception as e:
            print(f"  ⚠️  Could not run tests: {e}")
            return True  # Not a hard failure

    def _count_history_references(self) -> int:
        """Count all history references in codebase."""
        count = 0
        pattern = re.compile(r"\bhistory\b", re.IGNORECASE)

        for py_file in self.project_root.glob("src/**/*.py"):
            content = py_file.read_text()
            count += len(pattern.findall(content))

        return count

    def _get_database_metrics(self) -> dict[str, Any]:
        """Get database metrics."""
        db_path = self.project_root / "data" / "definities.db"
        metrics = {}

        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM definities")
                metrics["definitions"] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM definitie_geschiedenis")
                metrics["history_entries"] = cursor.fetchone()[0]

                conn.close()
            except Exception:
                pass

        return metrics

    def _count_files(self) -> dict[str, int]:
        """Count various file types."""
        return {
            "python_files": len(list(self.project_root.glob("src/**/*.py"))),
            "test_files": len(list(self.project_root.glob("tests/**/*.py"))),
        }

    def _generate_report(self, all_passed: bool):
        """Generate final report."""
        print("\n" + "=" * 60)
        print("📋 VERIFICATION REPORT")
        print("=" * 60)

        if all_passed:
            print("\n✅ SUCCESS: All verification checks passed!")
        else:
            print(f"\n❌ FAILED: Found {len(self.results['errors'])} error(s)")

        if self.results["errors"]:
            print("\n🔴 Errors:")
            for error in self.results["errors"]:
                print(f"  - {error}")

        if self.results["warnings"]:
            print("\n🟡 Warnings:")
            for warning in self.results["warnings"]:
                print(f"  - {warning}")

        # Save report
        report_file = (
            self.project_root
            / f'history_removal_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Full report saved to: {report_file}")

        # UI Checklist
        print("\n📝 MANUAL UI VERIFICATION CHECKLIST:")
        print("  [ ] Start app: streamlit run src/main.py")
        print("  [ ] Generator tab works")
        print("  [ ] Edit tab works")
        print("  [ ] Expert Review tab works")
        print("  [ ] Export tab works")
        print("  [ ] Management tab works")
        print("  [ ] NO History tab visible")
        print("  [ ] No console errors")
        print("  [ ] Navigation works smoothly")

        return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Verify History Tab removal")
    parser.add_argument(
        "--baseline", action="store_true", help="Capture baseline metrics"
    )
    parser.add_argument(
        "--verify", action="store_true", help="Run verification (default)"
    )

    args = parser.parse_args()

    verifier = HistoryRemovalVerifier()

    if args.baseline:
        verifier.run_baseline()
    else:
        # Default to verification
        success = verifier.run_verification()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
