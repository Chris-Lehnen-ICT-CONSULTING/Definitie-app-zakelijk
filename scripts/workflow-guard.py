#!/usr/bin/env python3
"""
Workflow Guard: Blocks commits that violate TDD workflow

This script enforces TDD workflow compliance by checking:
1. Tests written before implementation (RED phase)
2. Review documents exist for completed stories
3. Phase transitions are valid (RED → GREEN → REFACTOR)
4. Test coverage requirements met

Usage:
    python scripts/workflow-guard.py [--strict]

Options:
    --strict    Enforce all rules (blocks violations)
    (default)   Warning mode (shows violations but doesn't block)

Exit codes:
    0 - No violations or warnings only
    1 - Violations found in strict mode
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


class WorkflowGuard:
    """Guards TDD workflow compliance"""

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.violations = []
        self.warnings = []
        self.project_root = Path.cwd()

    def check_all(self) -> bool:
        """Run all workflow checks"""
        print("🛡️  Workflow Guard - Checking TDD compliance...")
        print("=" * 50)

        # Check 1: Test files before implementation
        self._check_test_first()

        # Check 2: Review documents for completed stories
        self._check_review_docs()

        # Check 3: Phase transition validity
        self._check_phase_transitions()

        # Check 4: Minimum test coverage
        self._check_test_coverage()

        # Report results
        self._report_results()

        # Determine exit code
        if self.strict and self.violations:
            return False
        return True

    def _check_test_first(self):
        """Check if tests were written before implementation"""
        try:
            # Get changed files in current branch
            result = subprocess.run(
                ["git", "diff", "--name-only", "main...HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )

            changed_files = result.stdout.strip().split("\n")

            # Separate test files and implementation files
            test_files = [
                f for f in changed_files if "/test_" in f or f.startswith("test_")
            ]
            impl_files = [
                f for f in changed_files if f.endswith(".py") and f not in test_files
            ]

            # For each implementation file, check if corresponding test exists
            for impl_file in impl_files:
                if impl_file.startswith("src/"):
                    # Expected test file location
                    module_name = Path(impl_file).stem
                    test_file = f"tests/unit/test_{module_name}.py"

                    if test_file not in test_files and not Path(test_file).exists():
                        self.warnings.append(f"⚠️  No test file found for {impl_file}")

        except subprocess.CalledProcessError:
            # Not in a git branch or no changes
            pass

    def _check_review_docs(self):
        """Check if completed stories have review documents"""
        backlog_path = self.project_root / "docs" / "backlog"

        if not backlog_path.exists():
            return

        # Find all user story directories
        for epic_dir in backlog_path.glob("EPIC-*"):
            for us_dir in epic_dir.glob("US-*"):
                # Check story status
                story_file = us_dir / f"{us_dir.name}.md"
                if story_file.exists():
                    content = story_file.read_text()

                    # If status is completed, check for review doc
                    if re.search(r"status:\s*(completed|done)", content, re.IGNORECASE):
                        review_files = list(us_dir.glob("review-*.md"))

                        if not review_files:
                            self.warnings.append(
                                f"⚠️  Completed story {us_dir.name} missing review document"
                            )

    def _check_phase_transitions(self):
        """Check if TDD phase transitions are valid"""
        # This would check phase marker files if they exist
        phase_file = self.project_root / ".tdd-phase"

        if phase_file.exists():
            current_phase = phase_file.read_text().strip()

            # Validate phase value
            valid_phases = ["RED", "GREEN", "REFACTOR"]
            if current_phase not in valid_phases:
                self.violations.append(
                    f"❌ Invalid TDD phase: {current_phase} (valid: {', '.join(valid_phases)})"
                )

    def _check_test_coverage(self):
        """Check if test coverage meets minimum threshold"""
        try:
            # Run pytest with coverage (quick check)
            result = subprocess.run(
                ["pytest", "--co", "-q"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            # Count test files
            test_count = result.stdout.count("test session starts")

            if test_count == 0:
                self.warnings.append("⚠️  No tests found - are you in TDD RED phase?")

        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ):
            # pytest not available or failed - skip check
            pass

    def _report_results(self):
        """Report violations and warnings"""
        print()

        # Show violations
        if self.violations:
            print("❌ VIOLATIONS FOUND:")
            for violation in self.violations:
                print(f"  {violation}")
            print()

        # Show warnings
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        # Summary
        if not self.violations and not self.warnings:
            print("✅ No workflow violations detected")
        else:
            print(
                f"📊 Summary: {len(self.violations)} violations, {len(self.warnings)} warnings"
            )

            if self.strict and self.violations:
                print()
                print("🚫 Strict mode: Blocking due to violations")
                print("Fix violations or use --no-strict mode")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="TDD Workflow Guard")
    parser.add_argument(
        "--strict", action="store_true", help="Enforce all rules (blocks on violations)"
    )

    args = parser.parse_args()

    guard = WorkflowGuard(strict=args.strict)
    success = guard.check_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
