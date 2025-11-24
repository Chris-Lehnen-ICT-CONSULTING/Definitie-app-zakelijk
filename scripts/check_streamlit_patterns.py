#!/usr/bin/env python3
"""
Pre-commit hook: Check Streamlit anti-patterns in UI code.

Based on DEF-56 lessons learned - enforces key-only pattern and SessionStateManager usage.

Exit codes:
    0 - All checks passed
    1 - Anti-patterns detected (fails pre-commit)
"""

import re
import sys
from pathlib import Path

# ANSI color codes
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"


class StreamlitPatternChecker:
    """Checks Python files for Streamlit anti-patterns."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.errors: list[tuple[Path, int, str]] = []
        self.warnings: list[tuple[Path, int, str]] = []

    def check_file(self, file_path: Path) -> None:
        """Check single Python file for anti-patterns."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            for i, line in enumerate(lines, start=1):
                self._check_line(file_path, i, line)

        except Exception as e:
            print(f"{YELLOW}⚠️  Skipped {file_path}: {e}{RESET}")

    def _check_line(self, file_path: Path, line_num: int, line: str) -> None:
        """Check single line for anti-patterns."""
        stripped = line.strip()

        # Ignore comments and docstrings
        if (
            stripped.startswith("#")
            or stripped.startswith('"""')
            or stripped.startswith("'''")
        ):
            return

        # 1️⃣ CRITICAL: Detect value + key parameter combination
        # Pattern: st.text_area(..., value=..., key=...) or st.text_input(...)
        if re.search(
            r"st\.(text_area|text_input|number_input|selectbox|multiselect)\s*\([^)]*value\s*=[^)]*key\s*=",
            line,
        ):
            self.errors.append(
                (
                    file_path,
                    line_num,
                    "CRITICAL: Widget has both 'value' and 'key' parameters (race condition!). Use key-only pattern.",
                )
            )

        # 2️⃣ HIGH: Direct st.session_state access in UI modules
        # Pattern: st.session_state["key"] or st.session_state.get("key")
        if "src/ui/" in str(file_path):
            if re.search(r"st\.session_state\[", line) or re.search(
                r"st\.session_state\.get\(", line
            ):
                # Allow in session_state.py itself
                if file_path.name != "session_state.py":
                    self.errors.append(
                        (
                            file_path,
                            line_num,
                            "HIGH: Direct st.session_state access forbidden. Use SessionStateManager.get_value() / set_value().",
                        )
                    )

        # 3️⃣ MEDIUM: Generic widget keys (potential conflicts)
        # Pattern: key="name", key="text", key="value" (too generic)
        generic_keys = ["name", "text", "value", "input", "data", "content"]
        for generic in generic_keys:
            if re.search(rf'key\s*=\s*["\']({generic})["\']', line):
                self.warnings.append(
                    (
                        file_path,
                        line_num,
                        f"MEDIUM: Generic widget key '{generic}' may cause conflicts. Use context-specific keys (e.g., 'edit_23_{generic}').",
                    )
                )

        # 4️⃣ CRITICAL: DEF-110 - force_clean=True in UI code (causes rerun cascade)
        # Pattern: init_context_cleaner(force_clean=True) or any function with force_clean=True
        if re.search(r"force_clean\s*=\s*True", line):
            self.errors.append(
                (
                    file_path,
                    line_num,
                    "CRITICAL: force_clean=True detected! This causes state mutation and rerun cascades. Remove or use force_clean=False.",
                )
            )

        # 5️⃣ HIGH: DEF-110 - State mutation in render() methods
        # Pattern: SessionStateManager.set_value() or .clear_value() inside render methods
        # Note: This is heuristic-based, requires context awareness for accuracy
        if re.search(r"SessionStateManager\.(set_value|clear_value|set_values)", line):
            # Check if we're likely in a render() method (heuristic)
            # Full AST analysis would be more accurate, but this catches common cases
            self.warnings.append(
                (
                    file_path,
                    line_num,
                    "HIGH: State mutation detected. Ensure this is NOT in render() method (causes rerun cascade). See DEF-110 post-mortem.",
                )
            )

        # 6️⃣ MEDIUM: Late state initialization (after widget)
        # This requires multi-line context, so we check for pattern
        if re.search(r"st\.(text_area|text_input).*key\s*=\s*[\"'](\w+)[\"']", line):
            key_match = re.search(r"key\s*=\s*[\"'](\w+)[\"']", line)
            if key_match:
                widget_key = key_match.group(1)
                # This is a heuristic - would need full AST analysis for accuracy
                # For now, just warn if we see st.session_state assignment after widget
                # (This check is best effort - full analysis requires AST)

    def check_all_ui_files(self) -> None:
        """Check all Python files in src/ui/ directory."""
        ui_dir = self.root_dir / "src" / "ui"
        if not ui_dir.exists():
            print(f"{YELLOW}⚠️  UI directory not found: {ui_dir}{RESET}")
            return

        py_files = list(ui_dir.rglob("*.py"))
        print(
            f"🔍 Checking {len(py_files)} UI Python files for Streamlit anti-patterns...\n"
        )

        for py_file in py_files:
            self.check_file(py_file)

    def report(self) -> int:
        """Print report and return exit code."""
        print("\n" + "=" * 80)
        print("📊 Streamlit Pattern Check Report")
        print("=" * 80 + "\n")

        # Print errors
        if self.errors:
            print(f"{RED}❌ ERRORS (blocking):{RESET}\n")
            for file_path, line_num, message in self.errors:
                rel_path = file_path.relative_to(self.root_dir)
                print(f"  {rel_path}:{line_num}")
                print(f"    {message}\n")

        # Print warnings
        if self.warnings:
            print(f"{YELLOW}⚠️  WARNINGS (non-blocking):{RESET}\n")
            for file_path, line_num, message in self.warnings:
                rel_path = file_path.relative_to(self.root_dir)
                print(f"  {rel_path}:{line_num}")
                print(f"    {message}\n")

        # Summary
        print("=" * 80)
        if self.errors:
            print(f"{RED}❌ {len(self.errors)} error(s) found - FIX REQUIRED{RESET}")
            print(
                "\n📚 See: docs/guidelines/STREAMLIT_PATTERNS.md for correct patterns"
            )
            return 1
        if self.warnings:
            print(
                f"{YELLOW}⚠️  {len(self.warnings)} warning(s) found - REVIEW RECOMMENDED{RESET}"
            )
            print(f"{GREEN}✅ No blocking errors - pre-commit PASSES{RESET}")
            return 0
        print(
            f"{GREEN}✅ All checks passed - code follows Streamlit best practices{RESET}"
        )
        return 0


def main() -> int:
    """Main entry point."""
    root_dir = Path(__file__).parent.parent  # Go up from scripts/ to project root

    checker = StreamlitPatternChecker(root_dir)
    checker.check_all_ui_files()
    return checker.report()


if __name__ == "__main__":
    sys.exit(main())
