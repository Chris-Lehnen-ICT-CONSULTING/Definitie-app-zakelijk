#!/usr/bin/env python3
"""
Enhanced AI Code Reviewer met meerdere auto-fix tools.
Quinn's verbeterde versie voor maximale auto-fixing capability.
"""

import subprocess
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedCodeReviewer:
    """Verbeterde code reviewer met multiple fix tools."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.src_path = self.project_root / "src"
        self.total_fixes = 0
        
    def run_autoflake(self) -> int:
        """Run autoflake om unused imports te verwijderen."""
        logger.info("🔧 Running autoflake for unused imports...")
        cmd = [
            "autoflake",
            "--in-place",
            "--recursive",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "--ignore-init-module-imports",
            str(self.src_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # Count fixes by checking modified files
                fixes = len([line for line in result.stdout.split('\n') if 'Fixing' in line])
                logger.info(f"✅ Autoflake fixed {fixes} files")
                return fixes
            else:
                logger.error(f"❌ Autoflake failed: {result.stderr}")
                return 0
        except FileNotFoundError:
            logger.warning("⚠️ autoflake not installed. Run: pip install autoflake")
            return 0
            
    def run_isort(self) -> int:
        """Run isort om imports te sorteren en E402 te fixen."""
        logger.info("🔧 Running isort for import ordering...")
        cmd = [
            "isort",
            str(self.src_path),
            "--profile", "black",
            "--line-length", "88",
            "--multi-line", "3",
            "--trailing-comma",
            "--diff"
        ]
        
        try:
            # First check what would be changed
            result = subprocess.run(cmd, capture_output=True, text=True)
            changes = len([line for line in result.stdout.split('\n') if line.startswith('---')])
            
            if changes > 0:
                # Apply the changes
                cmd.remove("--diff")
                subprocess.run(cmd, capture_output=True)
                logger.info(f"✅ isort fixed {changes} files")
                return changes
            else:
                logger.info("✅ isort: No changes needed")
                return 0
        except FileNotFoundError:
            logger.warning("⚠️ isort not installed. Run: pip install isort")
            return 0
            
    def run_black(self) -> int:
        """Run black voor code formatting."""
        logger.info("🔧 Running black for code formatting...")
        cmd = ["black", str(self.src_path), "--quiet"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if "reformatted" in result.stderr:
                fixes = result.stderr.count("reformatted")
                logger.info(f"✅ Black reformatted {fixes} files")
                return fixes
            else:
                logger.info("✅ Black: No changes needed")
                return 0
        except FileNotFoundError:
            logger.warning("⚠️ black not installed")
            return 0
            
    def run_ruff_check(self) -> Dict:
        """Run ruff om remaining issues te checken."""
        logger.info("🔍 Running ruff check...")
        cmd = ["ruff", "check", str(self.src_path), "--output-format", "json"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            issues = json.loads(result.stdout) if result.stdout else []
            
            # Categorize issues
            categories = {}
            for issue in issues:
                code = issue.get('code', 'UNKNOWN')
                if code not in categories:
                    categories[code] = 0
                categories[code] += 1
                
            return categories
        except Exception as e:
            logger.error(f"❌ Error running ruff: {e}")
            return {}
            
    def run_ruff_fix(self) -> int:
        """Run ruff met auto-fix."""
        logger.info("🔧 Running ruff auto-fix...")
        cmd = ["ruff", "check", str(self.src_path), "--fix", "--unsafe-fixes"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Parse output voor aantal fixes
            if "Fixed" in result.stderr:
                import re
                match = re.search(r'Fixed (\d+) errors', result.stderr)
                if match:
                    fixes = int(match.group(1))
                    logger.info(f"✅ Ruff fixed {fixes} issues")
                    return fixes
            return 0
        except Exception as e:
            logger.error(f"❌ Error running ruff fix: {e}")
            return 0
            
    def fix_bare_excepts(self) -> int:
        """Custom fix voor bare except statements."""
        logger.info("🔧 Fixing bare except clauses...")
        fixes = 0
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                original = content
                
                # Simple regex replacement for bare except
                import re
                content = re.sub(
                    r'^(\s*)except:\s*$',
                    r'\1except Exception:',
                    content,
                    flags=re.MULTILINE
                )
                
                if content != original:
                    py_file.write_text(content)
                    fixes += 1
                    
            except Exception as e:
                logger.error(f"Error processing {py_file}: {e}")
                
        if fixes > 0:
            logger.info(f"✅ Fixed {fixes} bare except clauses")
        return fixes
        
    def run_full_review(self, max_iterations: int = 5) -> None:
        """Run volledige review cyclus met alle tools."""
        logger.info("🚀 Starting Enhanced AI Code Review")
        
        for iteration in range(1, max_iterations + 1):
            logger.info(f"\n📍 Iteration {iteration}/{max_iterations}")
            iteration_fixes = 0
            
            # Check current issues
            issues_before = self.run_ruff_check()
            total_issues = sum(issues_before.values())
            logger.info(f"📊 Found {total_issues} issues before fixes")
            
            if total_issues == 0:
                logger.info("✅ No issues found! Code is clean.")
                break
                
            # Run all fixers in order
            iteration_fixes += self.run_autoflake()
            iteration_fixes += self.run_isort()
            iteration_fixes += self.fix_bare_excepts()
            iteration_fixes += self.run_ruff_fix()
            iteration_fixes += self.run_black()
            
            self.total_fixes += iteration_fixes
            
            # Check remaining issues
            issues_after = self.run_ruff_check()
            total_after = sum(issues_after.values())
            
            logger.info(f"📊 {total_after} issues remaining after fixes")
            logger.info(f"🔧 Fixed {iteration_fixes} issues in this iteration")
            
            # If no fixes were made, stop
            if iteration_fixes == 0:
                logger.info("⚠️ No more auto-fixable issues")
                break
                
        # Final report
        logger.info(f"\n📈 SUMMARY")
        logger.info(f"Total iterations: {iteration}")
        logger.info(f"Total fixes applied: {self.total_fixes}")
        
        final_issues = self.run_ruff_check()
        if final_issues:
            logger.info(f"\n❗ Remaining issues requiring manual intervention:")
            for code, count in sorted(final_issues.items()):
                logger.info(f"  - {code}: {count} instances")
        

if __name__ == "__main__":
    reviewer = EnhancedCodeReviewer()
    reviewer.run_full_review()