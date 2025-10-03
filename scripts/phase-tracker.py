#!/usr/bin/env python3
"""
Phase Tracker: Tracks current TDD phase

This script helps track and transition between TDD phases:
- RED: Test written, failing (test exists, implementation missing/incomplete)
- GREEN: Test passing, minimal implementation (test passes)
- REFACTOR: Code cleanup, optimization (improving working code)

Usage:
    python scripts/phase-tracker.py                    # Show current phase
    python scripts/phase-tracker.py set RED            # Set phase to RED
    python scripts/phase-tracker.py set GREEN          # Set phase to GREEN
    python scripts/phase-tracker.py set REFACTOR       # Set phase to REFACTOR
    python scripts/phase-tracker.py auto               # Auto-detect phase from git diff

The phase is stored in .tdd-phase file (gitignored)
"""

import argparse
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar


class PhaseTracker:
    """Tracks TDD workflow phases"""

    VALID_PHASES: ClassVar[list[str]] = ["RED", "GREEN", "REFACTOR"]
    PHASE_FILE: ClassVar[str] = ".tdd-phase"
    PHASE_LOG: ClassVar[str] = ".tdd-phase-log"

    def __init__(self):
        self.project_root = Path.cwd()
        self.phase_file = self.project_root / self.PHASE_FILE
        self.log_file = self.project_root / self.PHASE_LOG

    def get_current_phase(self) -> str | None:
        """Get current TDD phase"""
        if self.phase_file.exists():
            return self.phase_file.read_text().strip()
        return None

    def set_phase(self, phase: str) -> bool:
        """Set TDD phase"""
        phase = phase.upper()

        if phase not in self.VALID_PHASES:
            print(f"❌ Invalid phase: {phase}")
            print(f"Valid phases: {', '.join(self.VALID_PHASES)}")
            return False

        # Get previous phase
        prev_phase = self.get_current_phase()

        # Validate transition
        if prev_phase and not self._is_valid_transition(prev_phase, phase):
            print(f"⚠️  Warning: Unusual transition {prev_phase} → {phase}")
            print("   Normal flow: RED → GREEN → REFACTOR → RED")

        # Write phase
        self.phase_file.write_text(phase)

        # Log transition
        self._log_transition(prev_phase, phase)

        # Show phase with icon
        self._display_phase(phase)

        return True

    def auto_detect_phase(self) -> str | None:
        """Auto-detect phase from git diff"""
        try:
            # Get git diff
            result = subprocess.run(
                ["git", "diff", "--stat"], capture_output=True, text=True, check=True
            )

            diff_output = result.stdout

            # Check for test files
            has_test_changes = bool(re.search(r"test_.*\.py", diff_output))

            # Check for implementation files
            has_impl_changes = bool(re.search(r"src/.*\.py", diff_output))

            # Detect phase
            if has_test_changes and not has_impl_changes:
                phase = "RED"
                print("🔍 Auto-detected phase: RED (test changes only)")
            elif has_test_changes and has_impl_changes:
                phase = "GREEN"
                print("🔍 Auto-detected phase: GREEN (test + implementation)")
            elif has_impl_changes and not has_test_changes:
                phase = "REFACTOR"
                print("🔍 Auto-detected phase: REFACTOR (implementation changes only)")
            else:
                print("⚠️  No changes detected")
                return None

            return phase

        except subprocess.CalledProcessError:
            print("❌ Failed to detect phase (git diff failed)")
            return None

    def show_phase(self):
        """Show current phase with context"""
        phase = self.get_current_phase()

        if phase:
            self._display_phase(phase)
            self._show_phase_help(phase)
        else:
            print("📊 No TDD phase set")
            print()
            print(
                "Set phase with: python scripts/phase-tracker.py set [RED|GREEN|REFACTOR]"
            )
            print("Auto-detect: python scripts/phase-tracker.py auto")

    def _display_phase(self, phase: str):
        """Display phase with icon and color"""
        icons = {"RED": "🔴", "GREEN": "🟢", "REFACTOR": "🔵"}

        print()
        print(f"{icons.get(phase, '⚪')} Current TDD Phase: {phase}")
        print()

    def _show_phase_help(self, phase: str):
        """Show helpful tips for current phase"""
        help_text = {
            "RED": """
Next steps:
  1. Write a failing test that describes desired behavior
  2. Run tests to confirm failure
  3. Transition to GREEN phase: python scripts/phase-tracker.py set GREEN
            """,
            "GREEN": """
Next steps:
  1. Write minimal implementation to make test pass
  2. Run tests to confirm they pass
  3. Transition to REFACTOR phase: python scripts/phase-tracker.py set REFACTOR
            """,
            "REFACTOR": """
Next steps:
  1. Improve code quality (no new functionality)
  2. Run tests to ensure they still pass
  3. Commit changes, then transition to RED: python scripts/phase-tracker.py set RED
            """,
        }

        print(help_text.get(phase, "").strip())
        print()

    def _is_valid_transition(self, from_phase: str, to_phase: str) -> bool:
        """Check if phase transition is valid"""
        valid_transitions = {
            "RED": ["GREEN"],
            "GREEN": ["REFACTOR", "RED"],  # RED if test failed
            "REFACTOR": ["RED", "GREEN"],  # Back to RED for next feature
        }

        return to_phase in valid_transitions.get(from_phase, [])

    def _log_transition(self, from_phase: str | None, to_phase: str):
        """Log phase transition"""
        timestamp = datetime.now(UTC).isoformat()
        transition = f"{from_phase or 'NONE'} → {to_phase}"

        log_entry = f"{timestamp} | {transition}\n"

        with self.log_file.open("a") as f:
            f.write(log_entry)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="TDD Phase Tracker")
    parser.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "set", "auto"],
        help="Action to perform",
    )
    parser.add_argument("phase", nargs="?", help="Phase to set (RED, GREEN, REFACTOR)")

    args = parser.parse_args()

    tracker = PhaseTracker()

    if args.action == "show":
        tracker.show_phase()
    elif args.action == "set":
        if not args.phase:
            print("❌ Phase argument required for 'set' action")
            print(
                f"Usage: python scripts/phase-tracker.py set [{'|'.join(PhaseTracker.VALID_PHASES)}]"
            )
            sys.exit(1)
        success = tracker.set_phase(args.phase)
        sys.exit(0 if success else 1)
    elif args.action == "auto":
        phase = tracker.auto_detect_phase()
        if phase:
            tracker.set_phase(phase)
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
