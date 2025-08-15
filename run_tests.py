#!/usr/bin/env python3
"""
Test runner voor moderne web lookup service tests.

Script om alle tests uit te voeren met proper setup en reporting.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def install_requirements():
    """Installeer test requirements als ze nog niet beschikbaar zijn."""
    try:
        import pytest
        import pytest_asyncio
    except ImportError:
        print("📦 Installing test requirements...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pytest", "pytest-asyncio", "pytest-mock"
        ], check=True)

def run_unit_tests():
    """Run unit tests."""
    print("🧪 Running Unit Tests")
    print("=" * 50)
    
    test_files = [
        "tests/test_modern_web_lookup_service.py",
        "tests/test_wikipedia_service.py"
    ]
    
    cmd = [
        sys.executable, "-m", "pytest",
        *test_files,
        "-v",  # verbose
        "--tb=short",  # short traceback format
        "-x",  # stop on first failure
        "--disable-warnings"  # clean output
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def run_integration_tests():
    """Run integration tests (met environment flag)."""
    print("\n🔗 Running Integration Tests")
    print("=" * 50)
    
    env = os.environ.copy()
    env["RUN_INTEGRATION_TESTS"] = "1"
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "-m", "integration",
        "--tb=short",
        "--disable-warnings"
    ]
    
    result = subprocess.run(cmd, cwd=project_root, env=env)
    return result.returncode == 0

def run_coverage_report():
    """Run tests met coverage report."""
    print("\n📊 Running Coverage Analysis")
    print("=" * 50)
    
    try:
        import coverage
    except ImportError:
        print("Installing coverage...")
        subprocess.run([sys.executable, "-m", "pip", "install", "coverage"], check=True)
    
    # Run tests met coverage
    cmd = [
        sys.executable, "-m", "coverage", "run", "-m", "pytest",
        "tests/test_modern_web_lookup_service.py",
        "tests/test_wikipedia_service.py",
        "-v", "--disable-warnings"
    ]
    
    subprocess.run(cmd, cwd=project_root)
    
    # Generate report
    print("\n📈 Coverage Report:")
    subprocess.run([sys.executable, "-m", "coverage", "report", "-m"], cwd=project_root)

def main():
    """Main test runner."""
    print("🚀 Modern Web Lookup Service - Test Suite")
    print("=" * 60)
    
    # Check project structure
    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        print(f"❌ Tests directory not found: {tests_dir}")
        return 1
    
    # Install requirements
    try:
        install_requirements()
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return 1
    
    # Run tests
    success = True
    
    try:
        # Unit tests
        if not run_unit_tests():
            success = False
            
        # Integration tests (only if requested)
        if os.getenv("RUN_INTEGRATION_TESTS"):
            if not run_integration_tests():
                success = False
        else:
            print("\n🔄 Integration tests skipped (set RUN_INTEGRATION_TESTS=1 to enable)")
            
        # Coverage (optional)
        if os.getenv("RUN_COVERAGE"):
            run_coverage_report()
    
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        print("\n🎯 Next steps:")
        print("  • Run integration tests: RUN_INTEGRATION_TESTS=1 python run_tests.py")
        print("  • Generate coverage: RUN_COVERAGE=1 python run_tests.py")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())