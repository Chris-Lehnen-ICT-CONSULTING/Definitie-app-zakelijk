#!/usr/bin/env python3
"""Security review voor de code changes."""

import re
from pathlib import Path


def security_scan(filepath: str):
    """Scan voor security issues."""
    print("\n🔒 SECURITY SCAN")
    print("=" * 50)

    with open(filepath) as f:
        content = f.read()

    issues = []

    # Check for hardcoded secrets
    secret_patterns = [
        (r'api[_\-]?key\s*=\s*["\'][^"\']+["\']', "Possible hardcoded API key"),
        (r'password\s*=\s*["\'][^"\']+["\']', "Possible hardcoded password"),
        (r'token\s*=\s*["\'][^"\']+["\']', "Possible hardcoded token"),
    ]

    for pattern, msg in secret_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"⚠️  {msg}")

    # Check for SQL injection vulnerabilities
    if re.search(r'f["\'].*SELECT.*{.*}', content):
        issues.append("⚠️  Possible SQL injection - using f-strings in queries")

    # Check for unsafe eval/exec
    if re.search(r"\beval\s*\(", content):
        issues.append("🚨 Unsafe eval() usage detected")
    if re.search(r"\bexec\s*\(", content):
        issues.append("🚨 Unsafe exec() usage detected")

    # Check for pickle usage (can execute arbitrary code)
    if "pickle" in content:
        issues.append("⚠️  Pickle usage detected - potential security risk")

    # Check for proper input validation
    if "request" in content.lower() and not re.search(
        r"validat|sanitiz", content, re.IGNORECASE
    ):
        issues.append("i️  Consider adding input validation for request data")

    # Check logging for sensitive data
    if re.search(r"logger\.(debug|info).*password|token|key", content, re.IGNORECASE):
        issues.append("⚠️  Potential sensitive data in logs")

    # Results
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("  ✅ No security issues detected")

    # Good practices check
    print("\n✅ GOOD SECURITY PRACTICES:")
    if "get_container()" in content:
        print("  ✅ Using dependency injection (no hardcoded dependencies)")
    if "try:" in content and "except" in content:
        print("  ✅ Proper error handling implemented")
    if "logger" in content:
        print("  ✅ Using logging instead of print statements")


if __name__ == "__main__":
    filepath = "src/ontologie/ontological_analyzer.py"
    if Path(filepath).exists():
        security_scan(filepath)
    else:
        print(f"❌ File not found: {filepath}")
