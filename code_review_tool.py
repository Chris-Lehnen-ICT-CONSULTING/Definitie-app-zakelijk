#!/usr/bin/env python3
"""Simple code review tool voor de OntologischeAnalyzer changes."""

import ast
import re
from pathlib import Path
from typing import List, Dict, Tuple

class CodeReviewer:
    """Basis code review functionaliteit."""
    
    def __init__(self):
        self.issues = []
        self.stats = {
            "lines": 0,
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "todos": 0,
            "type_hints": 0,
            "docstrings": 0
        }
    
    def review_file(self, filepath: str) -> Dict:
        """Review een Python bestand."""
        print(f"\n🔍 Reviewing: {filepath}")
        
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.splitlines()
        
        self.stats["lines"] = len(lines)
        
        # Parse AST
        try:
            tree = ast.parse(content)
            self._analyze_ast(tree)
        except SyntaxError as e:
            self.issues.append(f"SYNTAX ERROR: {e}")
        
        # Pattern checks
        self._check_patterns(content, lines)
        
        return {
            "file": filepath,
            "stats": self.stats.copy(),
            "issues": self.issues.copy()
        }
    
    def _analyze_ast(self, tree):
        """Analyseer de Abstract Syntax Tree."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.stats["functions"] += 1
                # Check for type hints
                if node.returns or any(arg.annotation for arg in node.args.args):
                    self.stats["type_hints"] += 1
                else:
                    self.issues.append(f"Missing type hints: {node.name}()")
                    
                # Check docstring
                if ast.get_docstring(node):
                    self.stats["docstrings"] += 1
                    
            elif isinstance(node, ast.ClassDef):
                self.stats["classes"] += 1
                if ast.get_docstring(node):
                    self.stats["docstrings"] += 1
                    
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self.stats["imports"] += 1
    
    def _check_patterns(self, content: str, lines: List[str]):
        """Check voor specifieke patterns."""
        # TODOs
        self.stats["todos"] = len(re.findall(r'#\s*TODO', content, re.IGNORECASE))
        
        # Long lines
        for i, line in enumerate(lines):
            if len(line) > 100:
                self.issues.append(f"Line {i+1} too long ({len(line)} chars)")
        
        # Empty except blocks
        if re.search(r'except.*:\s*pass', content):
            self.issues.append("Empty except block gevonden")
        
        # Print statements (should use logging)
        if re.search(r'\bprint\s*\(', content):
            self.issues.append("Print statements gevonden - gebruik logging")

def compare_files(old_file: str, new_file: str):
    """Vergelijk oude en nieuwe versie."""
    print("\n📊 CHANGE ANALYSIS")
    print("=" * 50)
    
    # Count additions/deletions
    with open(old_file, 'r') as f:
        old_lines = f.readlines()
    with open(new_file, 'r') as f:
        new_lines = f.readlines()
    
    print(f"Lines in original: {len(old_lines)}")
    print(f"Lines in new:      {len(new_lines)}")
    print(f"Net change:        {len(new_lines) - len(old_lines):+d}")

def main():
    """Run code review on the changed file."""
    print("🤖 AUTOMATED CODE REVIEW TOOL")
    print("=" * 50)
    
    reviewer = CodeReviewer()
    
    # Review the updated file
    filepath = "src/ontologie/ontological_analyzer.py"
    if Path(filepath).exists():
        results = reviewer.review_file(filepath)
        
        print("\n📈 CODE STATISTICS:")
        for key, value in results["stats"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        print("\n⚠️  ISSUES FOUND:")
        if results["issues"]:
            for issue in results["issues"]:
                print(f"  • {issue}")
        else:
            print("  ✅ No major issues found!")
        
        # Specific checks for our changes
        print("\n🔍 INTEGRATION SPECIFIC CHECKS:")
        
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Check if mock is removed
        if "class DefinitieZoeker:" in content and "mock" in content.lower():
            print("  ❌ Mock implementation still present")
        else:
            print("  ✅ Mock implementation removed")
            
        # Check for proper imports
        if "from services.container import get_container" in content:
            print("  ✅ ServiceContainer properly imported")
        else:
            print("  ❌ ServiceContainer import missing")
            
        # Check for adapter pattern
        if "DefinitieZoekerAdapter" in content:
            print("  ✅ Adapter pattern implemented")
        else:
            print("  ❌ Adapter pattern missing")
            
        # Check error handling
        error_handling = len(re.findall(r'try:', content))
        print(f"  ℹ️  Try/except blocks: {error_handling}")
        
    else:
        print(f"❌ File not found: {filepath}")

if __name__ == "__main__":
    main()