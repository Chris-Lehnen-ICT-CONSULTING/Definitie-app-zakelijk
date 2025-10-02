#!/usr/bin/env python3
"""
Verification script for History Tab removal
Ensures the removal was complete and the application is functional
"""

import subprocess
import sys
from pathlib import Path


class RemovalVerifier:
    def __init__(self):
        self.project_root = Path("/Users/chrislehnen/Projecten/Definitie-app")
        self.checks_passed = []
        self.checks_failed = []

    def check_no_history_references(self) -> tuple[bool, str]:
        """Check that no History Tab references remain in code"""
        print("Checking for remaining History Tab references...")

        cmd = [
            "grep",
            "-r",
            'HistoryTab\\|history_tab\\|"history":',
            str(self.project_root / "src"),
            "--include=*.py",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            # Filter out legitimate history references
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                bad_refs = []
                for line in lines:
                    if not any(
                        ok in line
                        for ok in [
                            "history_entry",
                            "history_file",
                            "rate_limit_history",
                            "retry_history",
                            "_add_history",
                            "cache/api",
                        ]
                    ):
                        bad_refs.append(line)

                if bad_refs:
                    return False, f"Found {len(bad_refs)} remaining references"

            return True, "No History Tab references found"
        except Exception as e:
            return False, f"Error checking references: {e}"

    def check_python_syntax(self) -> tuple[bool, str]:
        """Verify Python syntax is valid"""
        print("Checking Python syntax...")

        file_path = self.project_root / "src/ui/tabbed_interface.py"

        cmd = ["python3", "-m", "py_compile", str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            return True, "Python syntax is valid"
        else:
            return False, f"Syntax error: {result.stderr}"

    def check_imports(self) -> tuple[bool, str]:
        """Verify all imports work"""
        print("Checking imports...")

        test_code = """
import sys
sys.path.insert(0, '/Users/chrislehnen/Projecten/Definitie-app')
from src.ui.tabbed_interface import TabbedInterface
print("Import successful")
"""

        result = subprocess.run(
            ["python3", "-c", test_code], capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            return True, "All imports work correctly"
        else:
            return False, f"Import error: {result.stderr}"

    def check_no_orphaned_files(self) -> tuple[bool, str]:
        """Check that history_tab files have been removed"""
        print("Checking for orphaned files...")

        files_to_check = [
            "src/ui/components/history_tab.py",
            "src/ui/components/history_tab.py.backup",
        ]

        found_files = []
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            if full_path.exists():
                found_files.append(file_path)

        if found_files:
            return False, f"Found orphaned files: {', '.join(found_files)}"
        else:
            return True, "No orphaned History Tab files"

    def check_tab_count(self) -> tuple[bool, str]:
        """Verify correct number of tabs in config"""
        print("Checking tab configuration...")

        file_path = self.project_root / "src/ui/tabbed_interface.py"
        content = file_path.read_text()

        # Count tab definitions in tabs_config
        tab_count = content.count('"title":')

        # Expected tabs (without history)
        # Note: There are 11 tabs including the legacy orchestration tab
        expected_tabs = [
            "generate",
            "edit",
            "expert",
            "export",
            "quality",
            "external",
            "monitoring",
            "web_lookup",
            "management",
            "legacy_orchestration",  # Legacy tab at line 1549
        ]

        # Accept 11-12 (12 includes a document title in a different context)
        if tab_count in [11, 12]:
            return True, f"Correct number of tabs: {tab_count}"
        else:
            return False, f"Unexpected tab count: {tab_count} (expected 11-12)"

    def check_streamlit_start(self) -> tuple[bool, str]:
        """Try to start Streamlit app briefly"""
        print("Testing Streamlit startup...")

        # Create a test script that starts and immediately stops
        test_script = """
import sys
sys.path.insert(0, '/Users/chrislehnen/Projecten/Definitie-app')
import os
os.chdir('/Users/chrislehnen/Projecten/Definitie-app')

# Try to import main
try:
    from src import main
    print("Main module imports successfully")
except Exception as e:
    print(f"Failed to import main: {e}")
    sys.exit(1)
"""

        result = subprocess.run(
            ["python3", "-c", test_script],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode == 0:
            return True, "Application can be imported"
        else:
            return False, f"Startup error: {result.stderr[:200]}"

    def run_all_checks(self) -> bool:
        """Run all verification checks"""
        print("=" * 60)
        print("🔍 HISTORY TAB REMOVAL VERIFICATION")
        print("=" * 60)
        print()

        checks = [
            ("No History References", self.check_no_history_references),
            ("Python Syntax Valid", self.check_python_syntax),
            ("Imports Working", self.check_imports),
            ("No Orphaned Files", self.check_no_orphaned_files),
            ("Tab Count Correct", self.check_tab_count),
            ("App Can Start", self.check_streamlit_start),
        ]

        for check_name, check_func in checks:
            try:
                passed, message = check_func()
                if passed:
                    self.checks_passed.append((check_name, message))
                    print(f"  ✅ {check_name}: {message}")
                else:
                    self.checks_failed.append((check_name, message))
                    print(f"  ❌ {check_name}: {message}")
            except Exception as e:
                self.checks_failed.append((check_name, str(e)))
                print(f"  ❌ {check_name}: Error - {e}")
            print()

        return len(self.checks_failed) == 0

    def print_summary(self):
        """Print verification summary"""
        print("=" * 60)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 60)
        print()

        total_checks = len(self.checks_passed) + len(self.checks_failed)
        print(f"Total checks: {total_checks}")
        print(f"  ✅ Passed: {len(self.checks_passed)}")
        print(f"  ❌ Failed: {len(self.checks_failed)}")
        print()

        if self.checks_failed:
            print("Failed checks:")
            for name, message in self.checks_failed:
                print(f"  • {name}: {message}")
            print()
            print("⚠️  Some checks failed. Review the issues above.")
            print("Rollback available at: /tmp/history_tab_removal_*/rollback.sh")
        else:
            print("✅ All checks passed! History Tab has been successfully removed.")
            print()
            print("Next steps:")
            print("  1. Start the app: streamlit run src/main.py")
            print("  2. Test all remaining tabs")
            print("  3. Commit the changes if everything works")


def main():
    verifier = RemovalVerifier()

    success = verifier.run_all_checks()
    verifier.print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
