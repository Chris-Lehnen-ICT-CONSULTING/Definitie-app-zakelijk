#!/usr/bin/env python3
"""
AI Code Review Automation met Auto-Fix Loop
Integreert met bestaande tools en BMAD workflow
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ReviewIssue:
    """Representeert een code review issue."""

    check: str
    severity: str  # BLOCKING, IMPORTANT, SUGGESTION
    message: str
    file_path: str | None = None
    line_number: int | None = None
    fixable: bool = False
    auto_fixed: bool = False


@dataclass
class ReviewResult:
    """Resultaat van een complete review cycle."""

    passed: bool
    iterations: int
    issues: list[ReviewIssue]
    auto_fixes_applied: int
    timestamp: datetime
    duration_seconds: float


class AICodeReviewer:
    """Automated code review voor AI-gegenereerde code met auto-fix capabilities."""

    def __init__(self, max_iterations: int = 5, project_root: str = "."):
        self.max_iterations = max_iterations
        self.project_root = Path(project_root).resolve()
        self.current_iteration = 0
        self.issues_found: list[ReviewIssue] = []
        self.auto_fixes_applied = 0
        self.start_time = datetime.now()

    def run_quality_checks(self) -> tuple[bool, list[ReviewIssue]]:
        """Voer alle quality checks uit en verzamel issues."""
        logger.info("🔍 Starting quality checks...")
        issues = []
        all_passed = True

        # Ruff linting
        ruff_issues = self._run_ruff_check()
        if ruff_issues:
            all_passed = False
            issues.extend(ruff_issues)

        # Black formatting
        black_issues = self._run_black_check()
        if black_issues:
            all_passed = False
            issues.extend(black_issues)

        # MyPy type checking
        mypy_issues = self._run_mypy_check()
        if mypy_issues:
            all_passed = False
            issues.extend(mypy_issues)

        # Bandit security
        bandit_issues = self._run_bandit_check()
        if bandit_issues:
            all_passed = False
            issues.extend(bandit_issues)

        # Custom DefinitieApp checks
        custom_issues = self._run_custom_checks()
        if custom_issues:
            all_passed = False
            issues.extend(custom_issues)

        return all_passed, issues

    def _run_ruff_check(self) -> list[ReviewIssue]:
        """Run Ruff linter en parse output."""
        issues = []
        try:
            # Check of ruff geïnstalleerd is
            result = subprocess.run(
                ["ruff", "--version"], check=False, capture_output=True, text=True
            )
            if result.returncode != 0:
                logger.warning("Ruff niet geïnstalleerd, skip linting check")
                return issues

            # Run ruff check
            result = subprocess.run(
                ["ruff", "check", "--output-format=json", "src/"],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0 and result.stdout:
                try:
                    ruff_output = json.loads(result.stdout)
                    for violation in ruff_output:
                        # Bepaal of deze violation fixable is
                        # Ruff kan veel fixes toepassen, ook al is 'fix' None in de output
                        fixable_codes = {
                            "F401",  # unused import
                            "F841",  # unused variable
                            "F811",  # redefinition of unused
                            "I001",  # unsorted imports
                            "UP",  # pyupgrade rules
                            "D",  # pydocstyle rules
                            "ANN",  # flake8-annotations
                            "B",  # flake8-bugbear (sommige)
                            "C4",  # flake8-comprehensions
                            "EM",  # flake8-errmsg
                            "ICN",  # flake8-import-conventions
                            "PGH",  # pygrep-hooks
                            "PIE",  # flake8-pie
                            "PT",  # flake8-pytest-style
                            "RET",  # flake8-return
                            "SIM",  # flake8-simplify
                            "TCH",  # flake8-type-checking
                            "TID",  # pyupgrade
                        }

                        code = violation["code"]
                        # Check of de code of het prefix fixable is
                        is_fixable = (
                            code in fixable_codes
                            or any(code.startswith(prefix) for prefix in fixable_codes)
                            or violation.get("fix") is not None
                        )

                        issues.append(
                            ReviewIssue(
                                check="ruff",
                                severity="IMPORTANT",
                                message=f"{violation['code']}: {violation['message']}",
                                file_path=violation["filename"],
                                line_number=violation["location"]["row"],
                                fixable=is_fixable,
                            )
                        )
                except json.JSONDecodeError:
                    # Fallback voor non-JSON output
                    if result.stdout:
                        issues.append(
                            ReviewIssue(
                                check="ruff",
                                severity="IMPORTANT",
                                message="Linting issues found (run 'ruff check src/' for details)",
                                fixable=True,
                            )
                        )

        except FileNotFoundError:
            logger.warning("Ruff niet gevonden in PATH")
        except Exception as e:
            logger.error(f"Ruff check failed: {e}")

        return issues

    def _run_black_check(self) -> list[ReviewIssue]:
        """Check code formatting met Black."""
        issues = []
        try:
            result = subprocess.run(
                ["black", "--check", "src/"],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                # Black geeft files die reformatting nodig hebben
                unformatted_files = []
                for line in result.stderr.split("\n"):
                    if line.startswith("would reformat"):
                        file_path = line.replace("would reformat ", "").strip()
                        unformatted_files.append(file_path)

                if unformatted_files:
                    issues.append(
                        ReviewIssue(
                            check="black",
                            severity="SUGGESTION",
                            message=f"Code formatting needed for {len(unformatted_files)} files",
                            fixable=True,
                        )
                    )

        except FileNotFoundError:
            logger.warning("Black niet gevonden in PATH")
        except Exception as e:
            logger.error(f"Black check failed: {e}")

        return issues

    def _run_mypy_check(self) -> list[ReviewIssue]:
        """Run MyPy type checker."""
        issues = []
        try:
            result = subprocess.run(
                ["mypy", "src/", "--ignore-missing-imports", "--no-error-summary"],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0 and result.stdout:
                # Parse mypy output
                for line in result.stdout.split("\n"):
                    if line and ":" in line and "error:" in line:
                        parts = line.split(":", 3)
                        if len(parts) >= 4:
                            file_path = parts[0]
                            line_no = parts[1]
                            message = parts[3].strip()

                            issues.append(
                                ReviewIssue(
                                    check="mypy",
                                    severity="IMPORTANT",
                                    message=f"Type error: {message}",
                                    file_path=file_path,
                                    line_number=(
                                        int(line_no) if line_no.isdigit() else None
                                    ),
                                    fixable=False,
                                )
                            )

        except FileNotFoundError:
            logger.warning("MyPy niet gevonden in PATH")
        except Exception as e:
            logger.error(f"MyPy check failed: {e}")

        return issues

    def _run_bandit_check(self) -> list[ReviewIssue]:
        """Run Bandit security scanner."""
        issues = []
        try:
            result = subprocess.run(
                ["bandit", "-r", "src/", "-f", "json", "-ll"],
                check=False,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.stdout:
                try:
                    bandit_output = json.loads(result.stdout)
                    for issue in bandit_output.get("results", []):
                        severity = (
                            "BLOCKING"
                            if issue["issue_severity"] == "HIGH"
                            else "IMPORTANT"
                        )

                        issues.append(
                            ReviewIssue(
                                check="bandit",
                                severity=severity,
                                message=f"Security: {issue['issue_text']}",
                                file_path=issue["filename"],
                                line_number=issue["line_number"],
                                fixable=False,
                            )
                        )
                except json.JSONDecodeError:
                    pass

        except FileNotFoundError:
            logger.warning("Bandit niet gevonden in PATH")
        except Exception as e:
            logger.error(f"Bandit check failed: {e}")

        return issues

    def _run_custom_checks(self) -> list[ReviewIssue]:
        """DefinitieApp specifieke checks."""
        issues = []

        # Check voor Nederlandse docstrings
        issues.extend(self._check_dutch_docstrings())

        # Check voor SQL injection preventie
        issues.extend(self._check_sql_safety())

        # Check voor proper session state usage in Streamlit
        issues.extend(self._check_streamlit_patterns())

        return issues

    def _check_dutch_docstrings(self) -> list[ReviewIssue]:
        """Controleer of docstrings in het Nederlands zijn."""
        issues = []
        src_path = self.project_root / "src"

        if not src_path.exists():
            return issues

        for py_file in src_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                # Simpele check voor Engels in docstrings
                english_patterns = [
                    r'""".*\b(Returns?|Parameters?|Args?|Raises?|Examples?)\b.*"""',
                    r"'''.*\b(Returns?|Parameters?|Args?|Raises?|Examples?)\b.*'''",
                ]

                for pattern in english_patterns:
                    if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
                        issues.append(
                            ReviewIssue(
                                check="custom",
                                severity="SUGGESTION",
                                message="Docstring lijkt Engels te bevatten, gebruik Nederlands",
                                file_path=str(py_file.relative_to(self.project_root)),
                                fixable=False,
                            )
                        )
                        break

            except Exception as e:
                logger.error(f"Error checking {py_file}: {e}")

        return issues

    def _check_sql_safety(self) -> list[ReviewIssue]:
        """Check voor SQL injection kwetsbaarheden."""
        issues = []
        src_path = self.project_root / "src"

        if not src_path.exists():
            return issues

        # Verbeterde SQL injection patterns - specifiekere detectie
        unsafe_patterns = [
            # F-strings met SQL keywords aan begin of na whitespace/quotes
            (
                r'f["\'].*\b(SELECT|INSERT|UPDATE|DELETE)\s+.*{.*}.*["\']',
                "F-string in SQL query",
            ),
            # String formatting met SQL patterns
            (
                r'["\'].*\b(SELECT|INSERT|UPDATE|DELETE)\s+.*%.*["\'].*%',
                "String formatting in SQL query",
            ),
            # .format() met SQL
            (
                r'["\'].*\b(SELECT|INSERT|UPDATE|DELETE)\s+.*{\w+}.*["\']\.format\(',
                "Format method in SQL query",
            ),
            # conn.execute met f-string
            (r'\.execute\s*\(\s*f["\'].*{.*}.*["\']', "Database execute with f-string"),
        ]

        for py_file in src_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                for pattern, message in unsafe_patterns:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    for match in matches:
                        matched_text = match.group(0)

                        # Filter false positives - skip logging/UI strings
                        false_positive_indicators = [
                            "logger.",
                            "log.",
                            "print(",
                            "st.success",
                            "st.error",
                            "st.info",
                            "st.write",
                            "st.markdown",
                            'f".*selected.*documents"',
                            "hybrid context",
                            "details van",
                            "geselecteerd",
                            "definitie",
                            "errors.append",
                            'message=f"',
                            "logger.error",
                            "logger.warning",
                            "logger.debug",
                            "logger.info",
                            "raise",
                            "context.errors",
                        ]

                        # Check context around match voor false positives
                        context_start = max(0, match.start() - 50)
                        context_end = min(len(content), match.end() + 50)
                        context = content[context_start:context_end].lower()

                        is_false_positive = any(
                            indicator in context
                            for indicator in false_positive_indicators
                        )

                        if not is_false_positive:
                            issues.append(
                                ReviewIssue(
                                    check="security",
                                    severity="BLOCKING",
                                    message=f"Potential SQL injection: {message}",
                                    file_path=str(
                                        py_file.relative_to(self.project_root)
                                    ),
                                    fixable=False,
                                )
                            )

            except Exception as e:
                logger.error(f"Error checking {py_file}: {e}")

        return issues

    def _check_streamlit_patterns(self) -> list[ReviewIssue]:
        """Check voor correcte Streamlit patterns."""
        issues = []
        src_path = self.project_root / "src"

        if not src_path.exists():
            return issues

        # Patterns die problemen kunnen geven
        problematic_patterns = [
            (
                r"st\.session_state\[.*\]\s*=.*st\.",
                "Session state assignment in widget call",
            ),
            (
                r"if.*not.*in.*st\.session_state:.*\n.*st\..*input",
                "Missing session state initialization",
            ),
        ]

        for py_file in src_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                if "streamlit" in content or "st." in content:
                    for pattern, message in problematic_patterns:
                        if re.search(pattern, content):
                            issues.append(
                                ReviewIssue(
                                    check="streamlit",
                                    severity="IMPORTANT",
                                    message=f"Streamlit pattern issue: {message}",
                                    file_path=str(
                                        py_file.relative_to(self.project_root)
                                    ),
                                    fixable=False,
                                )
                            )

            except Exception as e:
                logger.error(f"Error checking {py_file}: {e}")

        return issues

    def apply_auto_fixes(self, issues: list[ReviewIssue]) -> int:
        """Pas automatische fixes toe waar mogelijk."""
        fixes_applied = 0

        # Track aantal issues voor en na fixes
        initial_ruff_issues = sum(1 for i in issues if i.check == "ruff")
        initial_black_issues = sum(1 for i in issues if i.check == "black")

        # Identificeer werkelijk fixable ruff issues
        fixable_ruff_codes = {
            "F401",
            "F841",
            "F811",
            "I001",
            "UP",
            "D",
            "C4",
            "EM",
            "ICN",
            "PGH",
            "PIE",
            "PT",
            "RET",
            "SIM",
            "TCH",
            "TID",
        }

        actually_fixable_ruff = sum(
            1
            for i in issues
            if i.check == "ruff"
            and any(i.message.startswith(code + ":") for code in fixable_ruff_codes)
        )

        # Apply Ruff fixes
        if actually_fixable_ruff > 0:
            logger.info(
                f"🔧 Applying Ruff auto-fixes ({actually_fixable_ruff} fixable out of {initial_ruff_issues} total)..."
            )
            try:
                # Get initial issue count
                before_fix = subprocess.run(
                    ["ruff", "check", "--statistics", "src/"],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )

                # Apply fixes
                fix_result = subprocess.run(
                    ["ruff", "check", "--fix", "--unsafe-fixes", "src/"],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Combine stderr with stdout
                    text=True,
                    cwd=self.project_root,
                )

                # Get count after fix
                after_fix = subprocess.run(
                    ["ruff", "check", "--statistics", "src/"],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )

                # Parse statistics to see what was fixed
                def parse_ruff_stats(output):
                    if not output:
                        return 0
                    lines = output.strip().split("\n")
                    total = 0
                    for line in lines:
                        if line.strip() and not line.startswith("Found"):
                            try:
                                count = int(line.split()[0])
                                total += count
                            except (ValueError, IndexError):
                                pass
                    return total

                before_count = parse_ruff_stats(before_fix.stdout)
                after_count = parse_ruff_stats(after_fix.stdout)

                # First check the fix result output for "X fixed" pattern
                fixed_count = 0
                if fix_result.stdout:
                    # Parse "Found X error (Y fixed, Z remaining)" from output
                    import re

                    match = re.search(r"\((\d+) fixed", fix_result.stdout)
                    if match:
                        fixed_count = int(match.group(1))

                # If no fixes found in output, try statistics comparison
                if fixed_count == 0:
                    fixed_count = before_count - after_count

                if fixed_count > 0:
                    fixes_applied += fixed_count
                    logger.info(f"✅ Ruff fixed {fixed_count} issues")
                else:
                    logger.info(
                        "⚠️ Ruff could not auto-fix any issues (manual intervention required)"
                    )

            except Exception as e:
                logger.error(f"Ruff auto-fix failed: {e}")

        # Apply Black formatting
        if initial_black_issues > 0:
            logger.info("🔧 Applying Black formatting...")
            try:
                # Get list of files that need formatting
                check_result = subprocess.run(
                    ["black", "--check", "--diff", "src/"],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )

                files_to_format = []
                if check_result.returncode != 0 and check_result.stderr:
                    for line in check_result.stderr.split("\n"):
                        if "would reformat" in line:
                            files_to_format.append(line)

                # Apply formatting
                format_result = subprocess.run(
                    ["black", "src/"],
                    check=False,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )

                # Check if formatting was applied
                if format_result.returncode == 0 and len(files_to_format) > 0:
                    fixes_applied += len(files_to_format)
                    logger.info(f"✅ Black formatted {len(files_to_format)} files")

            except Exception as e:
                logger.error(f"Black formatting failed: {e}")

        self.auto_fixes_applied += fixes_applied
        return fixes_applied

    def generate_ai_feedback(self, issues: list[ReviewIssue]) -> str:
        """Genereer gestructureerde feedback voor AI agents."""
        feedback = "# 🔍 Code Review Feedback\n\n"
        feedback += (
            f"**Iteration**: {self.current_iteration + 1}/{self.max_iterations}\n"
        )
        feedback += f"**Issues Found**: {len(issues)}\n\n"

        # Groepeer issues op severity
        blocking = [i for i in issues if i.severity == "BLOCKING"]
        important = [i for i in issues if i.severity == "IMPORTANT"]
        suggestions = [i for i in issues if i.severity == "SUGGESTION"]

        if blocking:
            feedback += "## 🔴 BLOCKING Issues (moet opgelost worden)\n\n"
            for issue in blocking:
                feedback += f"### {issue.check.upper()}\n"
                if issue.file_path:
                    feedback += f"**File**: `{issue.file_path}`"
                    if issue.line_number:
                        feedback += f" (line {issue.line_number})"
                    feedback += "\n"
                feedback += f"**Issue**: {issue.message}\n\n"

                # Voeg specifieke fix suggesties toe
                if "SQL injection" in issue.message:
                    feedback += "**Fix**: Gebruik parameterized queries:\n"
                    feedback += "```python\n"
                    feedback += (
                        "# Fout: query = f'SELECT * FROM table WHERE id = {user_id}'\n"
                    )
                    feedback += "# Goed: cursor.execute('SELECT * FROM table WHERE id = ?', (user_id,))\n"
                    feedback += "```\n\n"

        if important:
            feedback += "## 🟡 IMPORTANT Issues (sterk aanbevolen)\n\n"
            for issue in important[:5]:  # Limit to top 5
                feedback += f"- **{issue.check}**: {issue.message}"
                if issue.file_path:
                    feedback += f" (`{issue.file_path}`)"
                feedback += "\n"

        if suggestions:
            feedback += "\n## 🟢 SUGGESTIONS (nice to have)\n\n"
            for issue in suggestions[:3]:  # Limit to top 3
                feedback += f"- {issue.message}\n"

        # Algemene tips
        feedback += "\n## 💡 Algemene Tips\n\n"
        feedback += "1. Voeg type hints toe aan alle functies\n"
        feedback += "2. Schrijf docstrings in het Nederlands\n"
        feedback += "3. Gebruik parameterized queries voor database operaties\n"
        feedback += "4. Test nieuwe functionaliteit met unit tests\n"

        return feedback

    def create_review_report(self, result: ReviewResult) -> str:
        """Maak een volledig review rapport."""
        report = "# 🤖 AI Code Review Report\n\n"
        report += f"**Date**: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Duration**: {result.duration_seconds:.1f} seconds\n"
        report += f"**Status**: {'✅ PASSED' if result.passed else '❌ FAILED'}\n"
        report += f"**Iterations**: {result.iterations}\n"
        report += f"**Auto-fixes Applied**: {result.auto_fixes_applied}\n\n"

        if not result.passed and result.issues:
            report += "## Remaining Issues\n\n"

            # Groepeer op severity
            for severity in ["BLOCKING", "IMPORTANT", "SUGGESTION"]:
                severity_issues = [i for i in result.issues if i.severity == severity]
                if severity_issues:
                    emoji = {"BLOCKING": "🔴", "IMPORTANT": "🟡", "SUGGESTION": "🟢"}[
                        severity
                    ]
                    report += f"### {emoji} {severity} ({len(severity_issues)})\n\n"

                    for issue in severity_issues:
                        report += f"- **{issue.check}**: {issue.message}"
                        if issue.file_path:
                            report += f" (`{issue.file_path}`"
                            if issue.line_number:
                                report += f":{issue.line_number}"
                            report += ")"
                        report += "\n"
                    report += "\n"
        else:
            report += "## ✅ All Checks Passed!\n\n"
            report += "De code voldoet aan alle quality standards.\n"

        # Metrics summary
        report += "## 📊 Metrics\n\n"
        report += f"- Total issues found: {len(self.issues_found)}\n"
        report += f"- Issues auto-fixed: {self.auto_fixes_applied}\n"
        report += f"- Manual fixes required: {len(result.issues)}\n"
        report += f"- Review efficiency: {(self.auto_fixes_applied / len(self.issues_found) * 100) if self.issues_found else 100:.1f}%\n"

        # Add breakdown by tool
        report += "\n### Issues by Tool\n\n"
        tool_counts = {}
        for issue in result.issues:
            tool_counts[issue.check] = tool_counts.get(issue.check, 0) + 1

        for tool, count in sorted(tool_counts.items()):
            report += f"- **{tool}**: {count} issues\n"

        return report

    async def run_review_cycle(self) -> ReviewResult:
        """Voer de complete review cycle uit met auto-fix loop."""
        logger.info("🚀 Starting AI Code Review Cycle")
        all_issues = []

        for iteration in range(self.max_iterations):
            self.current_iteration = iteration
            logger.info(f"\n📍 Iteration {iteration + 1}/{self.max_iterations}")

            # Run quality checks
            passed, issues = self.run_quality_checks()

            if passed:
                logger.info("✅ All checks passed!")
                break

            # Store all issues for reporting
            all_issues.extend(issues)

            # Try auto-fixes first
            fixable_issues = [i for i in issues if i.fixable]
            if fixable_issues:
                logger.info(f"🔍 Found {len(fixable_issues)} fixable issues")
                fixes_applied = self.apply_auto_fixes(issues)
                if fixes_applied > 0:
                    logger.info(f"🔧 Applied {fixes_applied} auto-fixes")
                    continue
                logger.warning("⚠️ No auto-fixes could be applied")

            # Generate AI feedback for all remaining issues
            if issues:
                # Separate fixable but unfixed issues from truly unfixable ones
                fixable_but_unfixed = [i for i in issues if i.fixable]
                unfixable_issues = [i for i in issues if not i.fixable]

                if fixable_but_unfixed:
                    logger.info(
                        f"⚠️ {len(fixable_but_unfixed)} issues marked as fixable but couldn't be auto-fixed"
                    )

                feedback = self.generate_ai_feedback(issues)
                logger.info("📝 Generated AI feedback for remaining issues")

                # In een echte implementatie zou je hier de AI API aanroepen
                # Voor nu printen we de feedback
                print("\n" + "=" * 60)
                print(feedback)
                print("=" * 60 + "\n")

                # Voor demo: stop na eerste iteratie met blocking issues
                if any(i.severity == "BLOCKING" for i in issues):
                    logger.warning("🛑 Blocking issues require manual intervention")
                    break

        # Calculate final metrics
        duration = (datetime.now() - self.start_time).total_seconds()

        # Get final state
        final_passed, final_issues = self.run_quality_checks()

        result = ReviewResult(
            passed=final_passed,
            iterations=self.current_iteration + 1,
            issues=final_issues,
            auto_fixes_applied=self.auto_fixes_applied,
            timestamp=self.start_time,
            duration_seconds=duration,
        )

        # Generate and save report
        report = self.create_review_report(result)
        report_path = self.project_root / "review_report.md"
        report_path.write_text(report, encoding="utf-8")
        logger.info(f"📄 Review report saved to {report_path}")

        return result


def main():
    """CLI interface voor de AI Code Reviewer."""
    import argparse

    parser = argparse.ArgumentParser(description="AI Code Review Automation")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum number of review iterations",
    )
    parser.add_argument(
        "--project-root", type=str, default=".", help="Project root directory"
    )
    parser.add_argument(
        "--ai-agent",
        type=str,
        default="manual",
        help="AI agent to use (manual, claude, copilot)",
    )

    args = parser.parse_args()

    # Set environment variable for tracking
    os.environ["AI_AGENT_NAME"] = args.ai_agent

    reviewer = AICodeReviewer(
        max_iterations=args.max_iterations, project_root=args.project_root
    )

    # Run the review cycle
    result = asyncio.run(reviewer.run_review_cycle())

    # Exit with appropriate code
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
