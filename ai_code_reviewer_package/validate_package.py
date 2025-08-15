#!/usr/bin/env python3
"""
AI Code Reviewer Package Validation Script
Valideer package voor publicatie naar PyPI
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path


def run_command(cmd, description):
    """Run command en check exit code."""
    print(f"🔍 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
        return True
    else:
        print(f"❌ {description} - FAILED")
        print(f"Error: {result.stderr}")
        return False


def check_file_exists(filepath, description):
    """Check of bestand bestaat."""
    if Path(filepath).exists():
        print(f"✅ {description} - EXISTS")
        return True
    else:
        print(f"❌ {description} - MISSING")
        return False


def validate_version():
    """Valideer version consistency."""
    print("🔍 Checking version consistency...")
    
    # Check __init__.py version
    spec = importlib.util.spec_from_file_location("ai_code_reviewer", "ai_code_reviewer/__init__.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    version = module.__version__
    print(f"📋 Package version: {version}")
    
    if version.startswith("2.0"):
        print(f"✅ Version {version} - VALID")
        return True
    else:
        print(f"❌ Version {version} - INVALID (expected 2.0.x)")
        return False


def main():
    """Hoofdvalidatie functie."""
    print("🚀 AI Code Reviewer Package Validation")
    print("=" * 50)
    
    checks = []
    
    # File existence checks
    files_to_check = [
        ("README.md", "README file"),
        ("setup.py", "Setup script"),
        ("pyproject.toml", "Project config"),
        ("ai_code_reviewer/__init__.py", "Package init"),
        ("ai_code_reviewer/core.py", "Core module"),
        ("ai_code_reviewer/cli.py", "CLI module"),
        ("INSTALL.md", "Installation guide"),
        ("BUILD.md", "Build documentation"),
        ("USAGE.md", "Usage documentation"),
        ("Makefile", "Build automation"),
        ("MANIFEST.in", "Package manifest"),
    ]
    
    print("\n📁 File Existence Checks:")
    for filepath, description in files_to_check:
        checks.append(check_file_exists(filepath, description))
    
    # Version validation
    print("\n🏷️ Version Validation:")
    checks.append(validate_version())
    
    # Import validation
    print("\n📦 Import Validation:")
    try:
        from ai_code_reviewer import AICodeReviewer, ReviewResult, ReviewIssue
        print("✅ Core imports - SUCCESS")
        checks.append(True)
    except ImportError as e:
        print(f"❌ Core imports - FAILED: {e}")
        checks.append(False)
    
    # Build validation
    print("\n🏗️ Build System Validation:")
    checks.append(run_command("python -m build --version", "Build tool availability"))
    checks.append(run_command("python setup.py check --metadata --strict", "Metadata validation"))
    
    # Dependencies validation  
    print("\n📋 Dependencies Validation:")
    checks.append(run_command("python -c 'import ruff'", "Ruff import"))
    checks.append(run_command("python -c 'import black'", "Black import")) 
    checks.append(run_command("python -c 'import yaml'", "YAML import"))
    
    # Package structure validation
    print("\n📂 Package Structure:")
    expected_dirs = [
        "ai_code_reviewer",
        "ai_code_reviewer/templates",
    ]
    
    for dir_path in expected_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path} - EXISTS")
            checks.append(True)
        else:
            print(f"❌ {dir_path} - MISSING")
            checks.append(False)
    
    # Console scripts validation
    print("\n🔧 Console Scripts Validation:")
    scripts_to_check = [
        "ai-code-review",
        "ai-review", 
    ]
    
    for script in scripts_to_check:
        # Check if entry point is defined
        if f"{script}=ai_code_reviewer.cli:main" in open("setup.py").read():
            print(f"✅ {script} entry point - DEFINED")
            checks.append(True)
        else:
            print(f"❌ {script} entry point - MISSING")
            checks.append(False)
    
    # Final summary
    print("\n" + "=" * 50)
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"🎉 VALIDATION PASSED: {passed}/{total} checks successful")
        print("✅ Package is ready for publication!")
        return 0
    else:
        print(f"❌ VALIDATION FAILED: {passed}/{total} checks successful")
        print("🔧 Please fix the issues above before publishing")
        return 1


if __name__ == "__main__":
    sys.exit(main())