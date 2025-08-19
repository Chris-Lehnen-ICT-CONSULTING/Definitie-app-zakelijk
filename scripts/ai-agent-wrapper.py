#!/usr/bin/env python3
"""
AI Agent Code Review Wrapper for DefinitieAgent Project

This script provides automated code review and fixing for AI-generated code
with a maximum of 5 iterations to ensure quality standards are met.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


class AICodeReviewer:
    """Automated code review for AI-generated code with auto-fix capabilities."""

    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.issues_found = []
        self.auto_fixes_applied = []
        self.project_root = Path(__file__).parent.parent

    def run_quality_checks(self) -> tuple[bool, list[dict]]:
        """Run all quality checks and return status + issues."""
        checks = [
            {
                "name": "ruff",
                "command": ["ruff", "check", "src/"],
                "fixable": True,
                "fix_command": ["ruff", "check", "src/", "--fix"],
            },
            {
                "name": "black",
                "command": ["black", "--check", "src/"],
                "fixable": True,
                "fix_command": ["black", "src/"],
            },
            {"name": "mypy", "command": ["mypy", "src/"], "fixable": False},
            {
                "name": "bandit",
                "command": ["bandit", "-r", "src/", "-ll"],
                "fixable": False,
            },
            {
                "name": "pytest",
                "command": ["pytest", "-x"],  # Stop on first failure
                "fixable": False,
            },
        ]

        all_passed = True
        issues = []

        print(
            f"\n🔍 Running quality checks (Iteration {self.current_iteration + 1}/{self.max_iterations})..."
        )

        for check in checks:
            print(f"  Running {check['name']}...", end="", flush=True)

            try:
                result = subprocess.run(
                    check["command"],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )

                if result.returncode == 0:
                    print(" ✅")
                else:
                    print(" ❌")
                    all_passed = False
                    issues.append(
                        {
                            "check": check["name"],
                            "output": result.stdout or result.stderr,
                            "fixable": check.get("fixable", False),
                            "fix_command": check.get("fix_command", []),
                        }
                    )
            except FileNotFoundError:
                print(f" ⚠️  ({check['name']} not installed)")

        return all_passed, issues

    def apply_auto_fixes(self, issues: list[dict]) -> int:
        """Apply automatic fixes where possible."""
        fixes_applied = 0

        print("\n🔧 Applying automatic fixes...")

        for issue in issues:
            if issue["fixable"] and issue["fix_command"]:
                print(f"  Fixing {issue['check']} issues...", end="", flush=True)

                result = subprocess.run(
                    issue["fix_command"],
                    check=False,
                    capture_output=True,
                    cwd=self.project_root,
                )

                if result.returncode == 0:
                    print(" ✅")
                    fixes_applied += 1
                    self.auto_fixes_applied.append(issue["check"])
                else:
                    print(" ❌")

        return fixes_applied

    def generate_ai_feedback(self, issues: list[dict]) -> str:
        """Generate specific feedback for AI agent to fix issues."""
        feedback = "# Code Review Feedback voor AI Agent\n\n"
        feedback += "De volgende issues moeten worden opgelost:\n\n"

        for issue in issues:
            if not issue["fixable"]:
                feedback += f"## {issue['check'].upper()} Issues\n\n"

                # Truncate output voor readability
                output = issue["output"]
                if len(output) > 1000:
                    output = output[:1000] + "\n... (truncated)"

                feedback += f"```\n{output}\n```\n\n"

                # Add specific guidance based on check type
                feedback += self._get_fix_guidance(issue["check"]) + "\n\n"

        feedback += self._get_definitieagent_specific_guidance()

        return feedback

    def _get_fix_guidance(self, check_name: str) -> str:
        """Get specific fix guidance for each check type."""
        guidance = {
            "mypy": """**Fix suggesties voor Type Errors:**
- Voeg type hints toe aan alle functies: `def functie(param: str) -> int:`
- Gebruik Optional voor nullable values: `from typing import Optional`
- Voor Streamlit: `st.session_state: Dict[str, Any]`
- Voor database results: `Optional[DefinitieRecord]`""",
            "bandit": """**Fix suggesties voor Security Issues:**
- Gebruik nooit `eval()` of `exec()` met user input
- SQL queries altijd met parameters: `cursor.execute("SELECT * WHERE id = ?", (id,))`
- Valideer en sanitize alle user input
- Gebruik `secrets.token_urlsafe()` voor tokens""",
            "pytest": """**Fix suggesties voor Failing Tests:**
- Check of nieuwe functionaliteit tests breekt
- Update test fixtures als data models zijn veranderd
- Mock externe dependencies (GPT API calls)
- Gebruik `pytest.raises()` voor exception testing""",
        }

        return guidance.get(
            check_name, f"**Fix alle {check_name} issues volgens de output hierboven.**"
        )

    def _get_definitieagent_specific_guidance(self) -> str:
        """Get project-specific guidance."""
        return """## DefinitieAgent Specifieke Requirements:

1. **Nederlandse Documentatie**:
   ```python
   def genereer_definitie(begrip: str) -> str:
       \"\"\"
       Genereer een definitie voor het gegeven begrip.

       Args:
           begrip: Het te definiëren begrip

       Returns:
           De gegenereerde definitie
       \"\"\"
   ```

2. **SQLite Connection Handling**:
   ```python
   with self._get_connection() as conn:
       cursor = conn.cursor()
       # queries hier
   ```

3. **Streamlit Session State**:
   ```python
   if 'key' not in st.session_state:
       st.session_state.key = default_value
   ```

4. **GPT Prompt Safety**:
   ```python
   # Sanitize input tegen prompt injection
   begrip = begrip.replace("\\n", " ").strip()
   if len(begrip) > 500:
       raise ValueError("Begrip te lang")
   ```"""

    def create_pr_description(self) -> str:
        """Create a detailed PR description with review results."""
        description = f"""## 🤖 AI Code Review Report

**AI Agent**: {os.getenv('AI_AGENT_NAME', 'Unknown')}
**Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}
**Review Iterations**: {self.current_iteration}
**Final Status**: {'✅ Passed' if not self.issues_found else '⚠️ Issues Remaining'}

### Auto-fixes Applied
"""

        if self.auto_fixes_applied:
            for fix in set(self.auto_fixes_applied):
                description += f"- ✅ {fix} issues automatically fixed\n"
        else:
            description += "- No automatic fixes applied\n"

        description += "\n### Quality Checks Summary\n"

        if self.issues_found:
            description += "\n⚠️ **Remaining Issues:**\n"
            for issue in self.issues_found:
                description += f"- {issue}\n"
        else:
            description += "\n✅ All quality checks passed!\n"

        description += "\n### Review Process\n"
        description += f"""
1. Initial code generated by AI
2. Ran {self.current_iteration} review iterations
3. Applied {len(self.auto_fixes_applied)} automatic fixes
4. {'All issues resolved' if not self.issues_found else 'Some issues require human review'}

### Next Steps
"""

        if self.issues_found:
            description += "- [ ] Human review required for remaining issues\n"
            description += "- [ ] Security review for any flagged items\n"
        else:
            description += "- [ ] Standard PR review process\n"
            description += "- [ ] Merge when approved\n"

        return description

    def save_metrics(self):
        """Save metrics for dashboard tracking."""
        metrics_file = self.project_root / "ai_metrics.json"

        try:
            if metrics_file.exists():
                with open(metrics_file) as f:
                    metrics = json.load(f)
            else:
                metrics = {}

            agent_name = os.getenv("AI_AGENT_NAME", "Unknown")

            if agent_name not in metrics:
                metrics[agent_name] = {
                    "total_reviews": 0,
                    "successful_reviews": 0,
                    "total_iterations": 0,
                    "auto_fixes": 0,
                }

            metrics[agent_name]["total_reviews"] += 1
            metrics[agent_name]["total_iterations"] += self.current_iteration

            if not self.issues_found:
                metrics[agent_name]["successful_reviews"] += 1

            metrics[agent_name]["auto_fixes"] += len(self.auto_fixes_applied)

            with open(metrics_file, "w") as f:
                json.dump(metrics, f, indent=2)

        except Exception as e:
            print(f"⚠️  Could not save metrics: {e}")

    def run(self) -> bool:
        """Run the complete review loop."""
        print("🤖 AI Agent Code Review Starting...")
        print(f"Agent: {os.getenv('AI_AGENT_NAME', 'Unknown')}")
        print(f"Max iterations: {self.max_iterations}")

        for i in range(self.max_iterations):
            self.current_iteration = i + 1

            # Run quality checks
            passed, issues = self.run_quality_checks()

            if passed:
                print(f"\n✅ All checks passed in iteration {self.current_iteration}!")
                self.save_metrics()
                return True

            # Try auto-fixes
            fixes = self.apply_auto_fixes(issues)

            if fixes > 0:
                print(f"  Applied {fixes} automatic fixes, retrying...")
                continue

            # If we can't auto-fix, we need AI intervention
            if i < self.max_iterations - 1:
                print("\n📝 Generating feedback for AI agent...")
                feedback = self.generate_ai_feedback(issues)

                # Save feedback for AI to read
                feedback_file = self.project_root / "ai_feedback.md"
                with open(feedback_file, "w") as f:
                    f.write(feedback)

                print(f"  Feedback saved to: {feedback_file}")
                print("  Waiting for AI to fix issues...")

                # In real implementation, this would trigger AI to fix
                # For now, we'll break to avoid infinite loop
                input("\nPress Enter after AI has fixed the issues...")
            else:
                # Final iteration, save remaining issues
                self.issues_found = [issue["check"] for issue in issues]

        print(f"\n⚠️  Max iterations ({self.max_iterations}) reached.")
        self.save_metrics()
        return False


def main():
    """Main entry point."""
    reviewer = AICodeReviewer()
    success = reviewer.run()

    # Create PR description
    pr_description = reviewer.create_pr_description()

    # Save PR description
    pr_file = Path("pr_description.md")
    with open(pr_file, "w") as f:
        f.write(pr_description)

    print(f"\n📄 PR description saved to: {pr_file}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
