#!/usr/bin/env python3
"""Targeted test coverage analysis without running tests."""

import os
import re
import ast
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

class CoverageAuditor:
    def __init__(self, root_path: Path):
        self.root = root_path
        self.src_path = root_path / "src"
        self.tests_path = root_path / "tests"

    def scan_source_modules(self):
        """Scan all source modules and categorize them."""
        modules = {
            'services': [],
            'ui': [],
            'database': [],
            'toetsregels': [],
            'other': []
        }

        for py_file in self.src_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            rel_path = py_file.relative_to(self.src_path)

            if rel_path.parts[0] == "services":
                modules['services'].append(rel_path)
            elif rel_path.parts[0] == "ui":
                modules['ui'].append(rel_path)
            elif rel_path.parts[0] == "database":
                modules['database'].append(rel_path)
            elif rel_path.parts[0] == "toetsregels":
                modules['toetsregels'].append(rel_path)
            else:
                modules['other'].append(rel_path)

        return modules

    def find_test_for_module(self, module_path: Path) -> List[Path]:
        """Find test files for a given module."""
        tests = []
        module_name = module_path.stem

        # Skip __init__ files
        if module_name == "__init__":
            return tests

        # Search patterns
        patterns = [
            f"test_{module_name}.py",
            f"test_{module_name}_*.py",
            f"*{module_name}*.py"
        ]

        for pattern in patterns:
            for test_file in self.tests_path.rglob(pattern):
                if "__pycache__" not in str(test_file) and test_file.name.startswith("test_"):
                    tests.append(test_file)

        return tests

    def analyze_module_complexity(self, module_path: Path) -> Dict:
        """Analyze a module for complexity metrics."""
        metrics = {
            'lines': 0,
            'functions': 0,
            'classes': 0,
            'methods': 0,
            'complexity': 'low'
        }

        try:
            full_path = self.src_path / module_path
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                metrics['lines'] = len(content.splitlines())

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics['functions'] += 1
                elif isinstance(node, ast.ClassDef):
                    metrics['classes'] += 1
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            metrics['methods'] += 1

            # Determine complexity
            total_entities = metrics['functions'] + metrics['classes'] + metrics['methods']
            if metrics['lines'] > 500 or total_entities > 20:
                metrics['complexity'] = 'high'
            elif metrics['lines'] > 200 or total_entities > 10:
                metrics['complexity'] = 'medium'
        except:
            pass

        return metrics

    def analyze_test_file_quality(self, test_path: Path) -> Dict:
        """Analyze test file for quality issues."""
        issues = {
            'total_tests': 0,
            'assertions': 0,
            'mocks': 0,
            'fixtures': 0,
            'bad_practices': []
        }

        try:
            with open(test_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Count test methods
            issues['total_tests'] = len(re.findall(r'def test_\w+', content))

            # Count assertions
            assertion_patterns = [
                r'assert\s+',
                r'\.assert[A-Z]\w*\(',
                r'pytest\.raises',
                r'\.called',
                r'\.call_count'
            ]
            for pattern in assertion_patterns:
                issues['assertions'] += len(re.findall(pattern, content))

            # Count mocks
            mock_patterns = [
                r'@patch',
                r'Mock\(',
                r'MagicMock\(',
                r'@mock\.',
                r'mocker\.'
            ]
            for pattern in mock_patterns:
                issues['mocks'] += len(re.findall(pattern, content))

            # Count fixtures
            issues['fixtures'] = len(re.findall(r'@pytest\.fixture', content))

            # Check for bad practices
            if 'time.sleep' in content:
                issues['bad_practices'].append('uses_sleep')
            if 'requests.' in content and '@patch' not in content:
                issues['bad_practices'].append('unmocked_requests')
            if 'openai.' in content and '@patch' not in content:
                issues['bad_practices'].append('unmocked_openai')
            if issues['total_tests'] > 0 and issues['assertions'] == 0:
                issues['bad_practices'].append('no_assertions')
            if 'Mock.ANY' in content or 'ANY' in content:
                issues['bad_practices'].append('uses_mock_any')

        except:
            pass

        return issues

    def generate_report(self):
        """Generate comprehensive audit report."""
        print("=" * 100)
        print("COMPREHENSIVE TEST COVERAGE AND QUALITY AUDIT REPORT")
        print("=" * 100)

        modules = self.scan_source_modules()

        # 1. MODULE COVERAGE ANALYSIS
        print("\n1. MODULE COVERAGE ANALYSIS")
        print("-" * 50)

        coverage_stats = {
            'services': {'total': 0, 'tested': 0, 'untested': []},
            'ui': {'total': 0, 'tested': 0, 'untested': []},
            'database': {'total': 0, 'tested': 0, 'untested': []},
            'toetsregels': {'total': 0, 'tested': 0, 'untested': []},
        }

        high_complexity_untested = []

        for category, module_list in modules.items():
            if category == 'other':
                continue

            for module in module_list:
                if module.name == "__init__.py":
                    continue

                coverage_stats[category]['total'] += 1
                tests = self.find_test_for_module(module)

                if tests:
                    coverage_stats[category]['tested'] += 1
                else:
                    coverage_stats[category]['untested'].append(module)

                    # Check complexity
                    complexity = self.analyze_module_complexity(module)
                    if complexity['complexity'] == 'high':
                        high_complexity_untested.append((module, complexity))

        # Print coverage summary
        print("\n📊 COVERAGE SUMMARY BY CATEGORY:\n")
        for category, stats in coverage_stats.items():
            if stats['total'] > 0:
                coverage_pct = (stats['tested'] / stats['total']) * 100
                status = "🟢" if coverage_pct > 70 else "🟡" if coverage_pct > 40 else "🔴"
                print(f"{status} {category.upper():15} {stats['tested']:3}/{stats['total']:3} files tested ({coverage_pct:.1f}%)")

        # 2. CRITICAL UNTESTED MODULES
        print("\n\n2. CRITICAL UNTESTED MODULES (High Complexity)")
        print("-" * 50)

        critical_services = [
            "services/ai_service_v2.py",
            "services/container.py",
            "services/service_factory.py",
            "services/validation/modular_validation_service.py",
            "services/orchestrators/validation_orchestrator_v2.py",
            "services/orchestrators/definition_orchestrator_v2.py",
            "services/definition_repository.py",
            "services/export_service.py",
            "services/modern_web_lookup_service.py",
            "services/workflow_service.py"
        ]

        print("\n🚨 CRITICAL SERVICES STATUS:\n")
        for service_path in critical_services:
            service = Path(service_path)
            tests = self.find_test_for_module(service)
            complexity = self.analyze_module_complexity(service)

            if tests:
                status = "✅"
                test_info = f"{len(tests)} test file(s)"
            else:
                status = "❌"
                test_info = "NO TESTS"

            print(f"{status} {service_path:55} | {complexity['lines']:4} lines | {test_info}")

        # 3. TOP UNTESTED MODULES BY SIZE
        print("\n\n3. TOP 20 UNTESTED MODULES BY SIZE")
        print("-" * 50)

        all_untested = []
        for category, stats in coverage_stats.items():
            for module in stats['untested']:
                complexity = self.analyze_module_complexity(module)
                all_untested.append((module, complexity['lines']))

        all_untested.sort(key=lambda x: x[1], reverse=True)

        print("\n📏 LARGEST UNTESTED FILES:\n")
        for module, lines in all_untested[:20]:
            print(f"  {str(module):60} {lines:5} lines")

        # 4. TEST QUALITY ANALYSIS
        print("\n\n4. TEST QUALITY ANALYSIS")
        print("-" * 50)

        quality_issues = defaultdict(list)
        test_stats = {'total': 0, 'with_issues': 0}

        for test_file in self.tests_path.rglob("test_*.py"):
            if "__pycache__" in str(test_file):
                continue

            test_stats['total'] += 1
            analysis = self.analyze_test_file_quality(test_file)

            if analysis['bad_practices']:
                test_stats['with_issues'] += 1
                rel_path = test_file.relative_to(self.tests_path)
                for issue in analysis['bad_practices']:
                    quality_issues[issue].append(rel_path)

        print(f"\n📈 TEST QUALITY METRICS:")
        print(f"  Total test files: {test_stats['total']}")
        print(f"  Files with issues: {test_stats['with_issues']}")
        print(f"  Clean test files: {test_stats['total'] - test_stats['with_issues']}")

        print("\n⚠️ QUALITY ISSUES FOUND:\n")
        for issue, files in quality_issues.items():
            print(f"\n{issue.upper().replace('_', ' ')} ({len(files)} files):")
            for file in files[:5]:  # Show first 5
                print(f"  - {file}")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more")

        # 5. TEST FILE MAPPING ANALYSIS
        print("\n\n5. TEST FILE MAPPING ISSUES")
        print("-" * 50)

        # Find orphaned test files
        orphaned_tests = []
        for test_file in self.tests_path.rglob("test_*.py"):
            if "__pycache__" in str(test_file):
                continue

            test_name = test_file.stem.replace("test_", "")
            found_source = False

            for src_file in self.src_path.rglob("*.py"):
                if test_name in src_file.stem:
                    found_source = True
                    break

            if not found_source and not any(x in test_name for x in ['smoke', 'integration', 'performance', 'regression']):
                orphaned_tests.append(test_file.relative_to(self.tests_path))

        print(f"\n🔍 ORPHANED TEST FILES (no matching source): {len(orphaned_tests)}")
        for test in orphaned_tests[:10]:
            print(f"  - {test}")

        # 6. FINAL RECOMMENDATIONS
        print("\n\n6. RECOMMENDATIONS & PRIORITY MATRIX")
        print("-" * 50)

        print("\n🎯 HIGHEST PRIORITY (Fix immediately):")
        print("  1. Add tests for critical services without coverage")
        print("  2. Fix test files with no assertions")
        print("  3. Mock external service calls (OpenAI, requests)")

        print("\n⚡ HIGH PRIORITY (Fix this sprint):")
        print("  1. Test high-complexity modules (>500 lines)")
        print("  2. Remove sleep() calls from tests")
        print("  3. Replace Mock.ANY with specific assertions")

        print("\n📌 MEDIUM PRIORITY (Technical debt):")
        print("  1. Add tests for UI components")
        print("  2. Improve test documentation")
        print("  3. Clean up orphaned test files")

        # Summary statistics
        print("\n" + "=" * 100)
        print("EXECUTIVE SUMMARY")
        print("=" * 100)

        total_src_files = sum(stats['total'] for stats in coverage_stats.values())
        total_tested = sum(stats['tested'] for stats in coverage_stats.values())
        overall_coverage = (total_tested / total_src_files * 100) if total_src_files > 0 else 0

        print(f"\n📊 Overall test coverage: {total_tested}/{total_src_files} files ({overall_coverage:.1f}%)")
        print(f"🔴 Critical services without tests: {len([s for s in critical_services if not self.find_test_for_module(Path(s))])}")
        print(f"⚠️ Test files with quality issues: {test_stats['with_issues']}/{test_stats['total']}")
        print(f"📁 Orphaned test files: {len(orphaned_tests)}")

if __name__ == "__main__":
    auditor = CoverageAuditor(Path("/Users/chrislehnen/Projecten/Definitie-app"))
    auditor.generate_report()