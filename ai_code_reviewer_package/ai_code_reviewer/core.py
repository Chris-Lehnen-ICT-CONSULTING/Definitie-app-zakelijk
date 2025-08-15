#!/usr/bin/env python3
"""
AI Code Reviewer Core Module - Updated Implementation
Geüpdatete versie met verbeterde SQL injection detectie, BMAD integratie,
universele post-edit hooks en uitgebreide security scanning.

Versie: 2.0.0
Laatste update: 2025-08-15
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
from typing import List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ReviewIssue:
    """Representeert een code review issue."""
    check: str
    severity: str  # "BLOCKING", "IMPORTANT", "SUGGESTION"
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    fixable: bool = False


@dataclass
class ReviewResult:
    """Representeert het resultaat van een complete review."""
    passed: bool
    iterations: int
    issues: List[ReviewIssue]
    auto_fixes_applied: int
    timestamp: datetime
    duration_seconds: float


class AICodeReviewer:
    """
    AI Code Reviewer - Geporteerde versie van het originele script.
    
    Features:
    - Multi-tool integratie (Ruff, Black, MyPy, Bandit)
    - Auto-fix loop (tot 5 iteraties)
    - Custom security checks voor SQL injection
    - Framework-specifieke validatie
    - BMAD Method integratie
    """
    
    def __init__(self, max_iterations: int = 5, project_root: str = ".", config: dict = None, ai_agent: str = "manual"):
        self.max_iterations = max_iterations
        self.project_root = Path(project_root).resolve()
        self.config = config or {}
        self.ai_agent = ai_agent
        self.current_iteration = 0
        self.issues_found: List[ReviewIssue] = []
        self.auto_fixes_applied = 0
        self.start_time = datetime.now()
        
        # Configureerbare patterns
        self.custom_checks_enabled = self.config.get('custom_checks', True)
        
        # Verbeterde false positive filters (v2.1.0)
        self.false_positive_filters = self.config.get('false_positive_filters', [
            'logger.', 'log.', 'print(', 'st.success', 'st.error', 'st.info',
            'st.write', 'st.markdown', 'f".*selected.*documents"',
            'hybrid context', 'details van', 'geselecteerd', 'definitie',
            'errors.append', 'message=f"', 'logger.error', 'logger.warning',
            'logger.debug', 'logger.info', 'raise', 'context.errors',
            'st.write(f"', 'st.markdown(f"', 'st.info(f"', 'st.success(f"',
            'st.error(f"', 'st.warning(f"', 'print(f"', 'raise ValueError(f"',
            'raise Exception(f"', 'logging.', 'log_message', 'debug_info'
        ])
        
        # BMAD integration detectie
        self.bmad_integration_enabled = self.config.get('bmad_integration', True)
        if self.bmad_integration_enabled:
            self.detect_bmad_environment()
    
    def detect_bmad_environment(self) -> None:
        """Detecteer BMAD omgeving en configureer integratie."""
        bmad_core_path = self.project_root / ".bmad-core"
        if bmad_core_path.exists():
            logger.info("🎭 BMAD environment detected")
            self.bmad_integration_enabled = True
            
            # Check voor BMAD agents
            agents_path = bmad_core_path / "agents" / "BMAD" / "agents"
            if agents_path.exists():
                self.config['bmad_agents_available'] = True
                logger.info("🤖 BMAD agents available")
        else:
            self.bmad_integration_enabled = False
            
    def detect_ai_agent(self) -> str:
        """Auto-detecteer AI agent type."""
        # Environment variables check
        if os.getenv('AI_AGENT_NAME'):
            return os.getenv('AI_AGENT_NAME')
        if os.getenv('BMAD_AGENT_NAME'):
            return os.getenv('BMAD_AGENT_NAME')
            
        # Process-based detection
        try:
            # Check voor Claude Code
            if 'claude' in sys.argv[0].lower() or os.getenv('CLAUDE_CODE'):
                return "claude"
            # Check voor GitHub Copilot
            if 'copilot' in os.getenv('PATH', ''):
                return "copilot"
        except Exception:
            pass
            
        return self.ai_agent or "manual"
    
    def run_quality_checks(self) -> Tuple[bool, List[ReviewIssue]]:
        """Voer alle quality checks uit en verzamel issues."""
        logger.info("🔍 Starting quality checks...")
        issues = []
        all_passed = True
        
        # Core tools
        check_methods = [
            self._run_ruff_check,
            self._run_black_check,
            self._run_mypy_check,
            self._run_bandit_check,
        ]
        
        # Custom checks indien ingeschakeld
        if self.custom_checks_enabled:
            check_methods.append(self._run_custom_checks)
        
        for check_method in check_methods:
            try:
                method_issues = check_method()
                if method_issues:
                    all_passed = False
                    issues.extend(method_issues)
            except Exception as e:
                logger.error(f"Error in {check_method.__name__}: {e}")
                
        return all_passed, issues
    
    def _run_ruff_check(self) -> List[ReviewIssue]:
        """Run Ruff linter en parse output."""
        issues = []
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                logger.warning("Ruff niet geïnstalleerd, skip linting check")
                return issues
                
            # Run ruff check
            src_dirs = self.config.get('source_dirs', ['src/'])
            for src_dir in src_dirs:
                if not (self.project_root / src_dir).exists():
                    continue
                    
                result = subprocess.run(
                    ["ruff", "check", src_dir, "--output-format=json"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                
                if result.returncode != 0 and result.stdout:
                    try:
                        ruff_output = json.loads(result.stdout)
                        for violation in ruff_output:
                            issues.append(ReviewIssue(
                                check="ruff",
                                severity="IMPORTANT",
                                message=f"{violation['code']}: {violation['message']}",
                                file_path=violation['filename'],
                                line_number=violation['location']['row'],
                                fixable=violation.get('fix') is not None
                            ))
                    except json.JSONDecodeError:
                        if result.stdout:
                            issues.append(ReviewIssue(
                                check="ruff",
                                severity="IMPORTANT",
                                message="Linting issues found (run 'ruff check' for details)",
                                fixable=True
                            ))
                        
        except FileNotFoundError:
            logger.warning("Ruff niet gevonden in PATH")
        except Exception as e:
            logger.error(f"Ruff check failed: {e}")
            
        return issues
    
    def _run_black_check(self) -> List[ReviewIssue]:
        """Check code formatting met Black."""
        issues = []
        try:
            src_dirs = self.config.get('source_dirs', ['src/'])
            for src_dir in src_dirs:
                if not (self.project_root / src_dir).exists():
                    continue
                    
                result = subprocess.run(
                    ["black", "--check", src_dir],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                
                if result.returncode != 0:
                    unformatted_files = []
                    for line in result.stderr.split('\n'):
                        if line.startswith('would reformat'):
                            file_path = line.replace('would reformat ', '').strip()
                            unformatted_files.append(file_path)
                            
                    if unformatted_files:
                        issues.append(ReviewIssue(
                            check="black",
                            severity="SUGGESTION",
                            message=f"Code formatting needed for {len(unformatted_files)} files",
                            fixable=True
                        ))
                    
        except FileNotFoundError:
            logger.warning("Black niet gevonden in PATH")
        except Exception as e:
            logger.error(f"Black check failed: {e}")
            
        return issues
    
    def _run_mypy_check(self) -> List[ReviewIssue]:
        """Run MyPy type checker."""
        issues = []
        try:
            src_dirs = self.config.get('source_dirs', ['src/'])
            for src_dir in src_dirs:
                if not (self.project_root / src_dir).exists():
                    continue
                    
                result = subprocess.run(
                    ["mypy", src_dir, "--ignore-missing-imports", "--no-error-summary"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                
                if result.returncode != 0 and result.stdout:
                    for line in result.stdout.split('\n'):
                        if line and ':' in line and 'error:' in line:
                            parts = line.split(':', 3)
                            if len(parts) >= 4:
                                file_path = parts[0]
                                line_no = parts[1]
                                message = parts[3].strip()
                                
                                issues.append(ReviewIssue(
                                    check="mypy",
                                    severity="IMPORTANT",
                                    message=f"Type error: {message}",
                                    file_path=file_path,
                                    line_number=int(line_no) if line_no.isdigit() else None,
                                    fixable=False
                                ))
                            
        except FileNotFoundError:
            logger.warning("MyPy niet gevonden in PATH")
        except Exception as e:
            logger.error(f"MyPy check failed: {e}")
            
        return issues
    
    def _run_bandit_check(self) -> List[ReviewIssue]:
        """Run Bandit security scanner."""
        issues = []
        try:
            src_dirs = self.config.get('source_dirs', ['src/'])
            for src_dir in src_dirs:
                if not (self.project_root / src_dir).exists():
                    continue
                    
                result = subprocess.run(
                    ["bandit", "-r", src_dir, "-f", "json", "-ll"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                
                if result.stdout:
                    try:
                        bandit_output = json.loads(result.stdout)
                        for issue in bandit_output.get('results', []):
                            severity = "BLOCKING" if issue['issue_severity'] == "HIGH" else "IMPORTANT"
                            
                            issues.append(ReviewIssue(
                                check="bandit",
                                severity=severity,
                                message=f"Security: {issue['issue_text']}",
                                file_path=issue['filename'],
                                line_number=issue['line_number'],
                                fixable=False
                            ))
                    except json.JSONDecodeError:
                        pass
                    
        except FileNotFoundError:
            logger.warning("Bandit niet gevonden in PATH")
        except Exception as e:
            logger.error(f"Bandit check failed: {e}")
            
        return issues
    
    def _run_custom_checks(self) -> List[ReviewIssue]:
        """Project-specifieke custom checks."""
        issues = []
        
        # Gebruik configureerbare check types
        check_types = self.config.get('custom_check_types', [
            'sql_safety', 'docstring_language', 'framework_patterns'
        ])
        
        if 'sql_safety' in check_types:
            issues.extend(self._check_sql_safety())
        if 'docstring_language' in check_types:
            issues.extend(self._check_docstring_language())
        if 'framework_patterns' in check_types:
            issues.extend(self._check_framework_patterns())
        
        return issues
    
    def _check_sql_safety(self) -> List[ReviewIssue]:
        """Check voor SQL injection kwetsbaarheden met verbeterde false positive filtering (v2.1.0)."""
        issues = []
        src_dirs = self.config.get('source_dirs', ['src/'])
        
        # Verbeterde SQL injection patterns - specifiekere detectie
        unsafe_patterns = [
            # F-strings met SQL keywords aan begin of na whitespace/quotes
            (r'f["\'].*\b(SELECT|INSERT|UPDATE|DELETE)\s+.*{.*}.*["\']', "F-string in SQL query"),
            # String formatting met SQL patterns
            (r'["\'].*\b(SELECT|INSERT|UPDATE|DELETE)\s+.*%.*["\'].*%', "String formatting in SQL query"),
            # .format() met SQL
            (r'["\'].*\b(SELECT|INSERT|UPDATE|DELETE)\s+.*{\w+}.*["\']\.format\(', "Format method in SQL query"),
            # conn.execute met f-string
            (r'\.execute\s*\(\s*f["\'].*{.*}.*["\']', "Database execute with f-string"),
            # PRAGMA statements (kunnen gevaarlijk zijn)
            (r'PRAGMA\s+.*{.*}', "Dynamic PRAGMA statement"),
            # ALTER TABLE met dynamic values
            (r'ALTER\s+TABLE\s+.*{.*}', "Dynamic ALTER TABLE statement"),
        ]
        
        for src_dir in src_dirs:
            src_path = self.project_root / src_dir
            if not src_path.exists():
                continue
                
            for py_file in src_path.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    for pattern, message in unsafe_patterns:
                        matches = list(re.finditer(pattern, content, re.IGNORECASE))
                        for match in matches:
                            # Verbeterde context-based false positive filtering (v2.1.0)
                            context_start = max(0, match.start() - 100)
                            context_end = min(len(content), match.end() + 100)
                            context = content[context_start:context_end].lower()
                            
                            # Multi-layer false positive detection
                            is_false_positive = any(
                                indicator in context for indicator in self.false_positive_filters
                            )
                            
                            # Specifieke context checks voor SQL false positives
                            context_indicators = [
                                'st.write', 'st.success', 'st.error', 'st.info', 'st.markdown',
                                'print(', 'logger.', 'log.', 'message=', 'raise ', 'return f"',
                                'error_message', 'display_text', 'user_message', 'status_text'
                            ]
                            
                            is_ui_context = any(indicator in context for indicator in context_indicators)
                            
                            if not is_false_positive and not is_ui_context:
                                issues.append(ReviewIssue(
                                    check="security",
                                    severity="BLOCKING",
                                    message=f"Potential SQL injection: {message}",
                                    file_path=str(py_file.relative_to(self.project_root)),
                                    fixable=False
                                ))
                            
                except Exception as e:
                    logger.error(f"Error checking {py_file}: {e}")
                    
        return issues
    
    def _check_docstring_language(self) -> List[ReviewIssue]:
        """Check docstring taal (configureerbaar)."""
        issues = []
        expected_language = self.config.get('docstring_language', 'dutch')
        
        if expected_language not in ['dutch', 'english']:
            return issues
            
        src_dirs = self.config.get('source_dirs', ['src/'])
        
        # Define patterns gebaseerd op verwachte taal
        if expected_language == 'dutch':
            unwanted_patterns = [
                r'""".*\b(Returns?|Parameters?|Args?|Raises?|Examples?)\b.*"""',
                r"'''.*\b(Returns?|Parameters?|Args?|Raises?|Examples?)\b.*'''"
            ]
            message = "Docstring lijkt Engels te bevatten, gebruik Nederlands"
        else:
            unwanted_patterns = [
                r'""".*\b(Retourneert|Parameters|Argumenten|Gooit|Voorbeelden)\b.*"""',
                r"'''.*\b(Retourneert|Parameters|Argumenten|Gooit|Voorbeelden)\b.*'''"
            ]
            message = "Docstring lijkt Nederlands te bevatten, gebruik Engels"
        
        for src_dir in src_dirs:
            src_path = self.project_root / src_dir
            if not src_path.exists():
                continue
                
            for py_file in src_path.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    for pattern in unwanted_patterns:
                        if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
                            issues.append(ReviewIssue(
                                check="custom",
                                severity="SUGGESTION",
                                message=message,
                                file_path=str(py_file.relative_to(self.project_root)),
                                fixable=False
                            ))
                            break
                            
                except Exception as e:
                    logger.error(f"Error checking {py_file}: {e}")
                    
        return issues
    
    def _check_framework_patterns(self) -> List[ReviewIssue]:
        """Check voor framework-specifieke patterns (configureerbaar)."""
        issues = []
        framework = self.config.get('framework', 'streamlit')
        
        if framework == 'streamlit':
            return self._check_streamlit_patterns()
        elif framework == 'django':
            return self._check_django_patterns()
        elif framework == 'flask':
            return self._check_flask_patterns()
        
        return issues
    
    def _check_streamlit_patterns(self) -> List[ReviewIssue]:
        """Streamlit-specifieke pattern checks."""
        issues = []
        src_dirs = self.config.get('source_dirs', ['src/'])
        
        problematic_patterns = [
            (r'st\.session_state\[.*\]\s*=.*st\.', "Session state assignment in widget call"),
            (r'if.*not.*in.*st\.session_state:.*\n.*st\..*input', "Missing session state initialization"),
        ]
        
        for src_dir in src_dirs:
            src_path = self.project_root / src_dir
            if not src_path.exists():
                continue
                
            for py_file in src_path.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    if 'streamlit' in content or 'st.' in content:
                        for pattern, message in problematic_patterns:
                            if re.search(pattern, content):
                                issues.append(ReviewIssue(
                                    check="streamlit",
                                    severity="IMPORTANT",
                                    message=f"Streamlit pattern issue: {message}",
                                    file_path=str(py_file.relative_to(self.project_root)),
                                    fixable=False
                                ))
                                
                except Exception as e:
                    logger.error(f"Error checking {py_file}: {e}")
                    
        return issues
    
    def _check_django_patterns(self) -> List[ReviewIssue]:
        """Django-specifieke pattern checks."""
        # Placeholder voor Django patterns
        return []
    
    def _check_flask_patterns(self) -> List[ReviewIssue]:
        """Flask-specifieke pattern checks."""  
        # Placeholder voor Flask patterns
        return []
    
    def apply_auto_fixes(self, issues: List[ReviewIssue]) -> int:
        """Pas automatische fixes toe waar mogelijk."""
        fixes_applied = 0
        src_dirs = self.config.get('source_dirs', ['src/'])
        
        # Groepeer fixable issues per tool
        ruff_fixable = any(i.check == "ruff" and i.fixable for i in issues)
        black_fixable = any(i.check == "black" and i.fixable for i in issues)
        
        if ruff_fixable:
            logger.info("🔧 Applying Ruff auto-fixes...")
            for src_dir in src_dirs:
                if not (self.project_root / src_dir).exists():
                    continue
                try:
                    result = subprocess.run(
                        ["ruff", "check", src_dir, "--fix"],
                        capture_output=True,
                        text=True,
                        cwd=self.project_root
                    )
                    if result.returncode == 0:
                        fixes_applied += 1
                        logger.info("✅ Ruff fixes applied")
                except Exception as e:
                    logger.error(f"Ruff auto-fix failed: {e}")
                    
        if black_fixable:
            logger.info("🔧 Applying Black formatting...")
            for src_dir in src_dirs:
                if not (self.project_root / src_dir).exists():
                    continue
                try:
                    result = subprocess.run(
                        ["black", src_dir],
                        capture_output=True,
                        text=True,
                        cwd=self.project_root
                    )
                    if result.returncode == 0:
                        fixes_applied += 1
                        logger.info("✅ Black formatting applied")
                except Exception as e:
                    logger.error(f"Black formatting failed: {e}")
                    
        self.auto_fixes_applied += fixes_applied
        return fixes_applied
    
    def generate_ai_feedback(self, issues: List[ReviewIssue]) -> str:
        """Genereer gestructureerde feedback voor AI agents."""
        feedback = "# 🔍 Code Review Feedback\n\n"
        feedback += f"**Iteration**: {self.current_iteration + 1}/{self.max_iterations}\n"
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
                    feedback += "# Fout: query = f'SELECT * FROM table WHERE id = {user_id}'\n"
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
                    emoji = {"BLOCKING": "🔴", "IMPORTANT": "🟡", "SUGGESTION": "🟢"}[severity]
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
                fixes_applied = self.apply_auto_fixes(issues)
                if fixes_applied > 0:
                    logger.info(f"🔧 Applied {fixes_applied} auto-fixes")
                    continue
                    
            # If we can't auto-fix, generate AI feedback
            unfixable_issues = [i for i in issues if not i.fixable]
            if unfixable_issues:
                feedback = self.generate_ai_feedback(unfixable_issues)
                logger.info("📝 Generated AI feedback")
                
                # Voor command-line usage, print feedback
                print("\n" + "="*60)
                print(feedback)
                print("="*60 + "\n")
                
                # Stop als er blocking issues zijn
                if any(i.severity == "BLOCKING" for i in unfixable_issues):
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
            duration_seconds=duration
        )
        
        # Generate and save report
        report = self.create_review_report(result)
        report_path = self.project_root / "review_report.md"
        report_path.write_text(report, encoding='utf-8')
        logger.info(f"📄 Review report saved to {report_path}")
        
        return result
    
    def setup_bmad_integration(self) -> bool:
        """Setup BMAD Method integratie including post-edit hooks."""
        if not self.bmad_integration_enabled:
            logger.warning("BMAD environment not detected")
            return False
            
        bmad_core_path = self.project_root / ".bmad-core"
        if not bmad_core_path.exists():
            logger.error("BMAD core directory not found")
            return False
            
        try:
            # Check voor post-edit hook
            hook_path = bmad_core_path / "utils" / "bmad-post-edit-hook.sh"
            if hook_path.exists():
                logger.info("✅ BMAD post-edit hook found")
            else:
                logger.warning("⚠️ BMAD post-edit hook not found")
                
            # Check voor agent configurations
            agents_path = bmad_core_path / "agents" / "BMAD" / "agents"
            if agents_path.exists():
                agent_files = list(agents_path.glob("*.md"))
                logger.info(f"✅ Found {len(agent_files)} BMAD agents")
                
                # Check of agents POST-EDIT REVIEW instructies hebben
                agents_with_hooks = 0
                for agent_file in agent_files:
                    content = agent_file.read_text(encoding='utf-8')
                    if "POST-EDIT REVIEW" in content and "bmad-post-edit-hook" in content:
                        agents_with_hooks += 1
                        
                logger.info(f"✅ {agents_with_hooks}/{len(agent_files)} agents have post-edit integration")
                
            return True
            
        except Exception as e:
            logger.error(f"BMAD integration setup failed: {e}")
            return False
    
    def trigger_bmad_hook(self, agent_name: str = None, files_changed: str = "unknown") -> int:
        """Trigger BMAD post-edit hook for automated review."""
        if not self.bmad_integration_enabled:
            return 1
            
        hook_path = self.project_root / ".bmad-core" / "utils" / "bmad-post-edit-hook.sh"
        if not hook_path.exists():
            logger.error("BMAD post-edit hook not found")
            return 1
            
        try:
            agent_name = agent_name or self.detect_ai_agent() or "AI-Agent"
            
            # Trigger the hook
            cmd = [
                "bash", str(hook_path),
                agent_name,
                files_changed
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            logger.info(f"🔄 BMAD hook triggered for agent: {agent_name}")
            return result.returncode
            
        except Exception as e:
            logger.error(f"BMAD hook trigger failed: {e}")
            return 1