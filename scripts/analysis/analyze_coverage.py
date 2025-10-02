#!/usr/bin/env python3
"""Comprehensive test coverage and quality analyzer."""

import ast
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path


class TestCoverageAnalyzer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_path = project_root / "src"
        self.tests_path = project_root / "tests"

    def find_all_source_files(self) -> dict[str, Path]:
        """Find all Python source files in src/."""
        source_files = {}
        for file_path in self.src_path.rglob("*.py"):
            if "__pycache__" not in str(file_path):
                relative_path = file_path.relative_to(self.src_path)
                source_files[str(relative_path)] = file_path
        return source_files

    def find_all_test_files(self) -> dict[str, Path]:
        """Find all test files."""
        test_files = {}
        for file_path in self.tests_path.rglob("test_*.py"):
            if "__pycache__" not in str(file_path):
                relative_path = file_path.relative_to(self.tests_path)
                test_files[str(relative_path)] = file_path
        return test_files

    def map_source_to_test(
        self, source_files: dict[str, Path], test_files: dict[str, Path]
    ) -> dict[str, list[str]]:
        """Map source files to their test files."""
        mapping = defaultdict(list)

        for src_file in source_files:
            # Remove .py extension and __init__ handling
            src_base = src_file.replace(".py", "").replace("/__init__", "")
            src_module = src_base.replace("/", "_")

            # Look for matching test files
            for test_file in test_files:
                test_name = Path(test_file).stem

                # Check various naming patterns
                if (
                    test_name == f"test_{src_module}"
                    or src_module in test_name
                    or src_base.split("/")[-1] in test_name
                ):
                    mapping[src_file].append(test_file)

        return dict(mapping)

    def analyze_test_quality(self, test_file: Path) -> dict:
        """Analyze a test file for quality metrics."""
        metrics = {
            "total_tests": 0,
            "tests_with_no_assertions": [],
            "tests_with_many_assertions": [],
            "tests_with_unclear_names": [],
            "uses_real_services": False,
            "has_docstrings": 0,
            "uses_mock_any": False,
            "complex_mocks": [],
            "has_sleep": False,
        }

        try:
            with open(test_file, encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)
        except:
            return metrics

        # Check for real service usage patterns
        if re.search(r"(requests\.|urllib\.|openai\.|boto3\.)", content):
            metrics["uses_real_services"] = True

        if "Mock.ANY" in content or "ANY" in content:
            metrics["uses_mock_any"] = True

        if "time.sleep" in content or "sleep(" in content:
            metrics["has_sleep"] = True

        # Analyze test methods
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                metrics["total_tests"] += 1

                # Check for docstring
                if ast.get_docstring(node):
                    metrics["has_docstrings"] += 1

                # Count assertions
                assertions = 0
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if hasattr(child.func, "attr"):
                            if child.func.attr in [
                                "assertEqual",
                                "assertTrue",
                                "assertFalse",
                                "assertIn",
                                "assertIsNone",
                                "assertIsNotNone",
                                "assertRaises",
                                "assert_called",
                                "assert_called_once",
                            ]:
                                assertions += 1
                    elif isinstance(child, ast.Assert):
                        assertions += 1

                if assertions == 0:
                    metrics["tests_with_no_assertions"].append(node.name)
                elif assertions > 5:
                    metrics["tests_with_many_assertions"].append(
                        (node.name, assertions)
                    )

                # Check test name clarity
                if len(node.name) < 10 or "_" not in node.name[5:]:
                    metrics["tests_with_unclear_names"].append(node.name)

        return metrics

    def get_coverage_data(self) -> dict:
        """Run pytest with coverage and get results."""
        try:
            # Run pytest with coverage in JSON format
            subprocess.run(
                [
                    "python",
                    "-m",
                    "pytest",
                    "--cov=src",
                    "--cov-report=json",
                    "-q",
                    "--tb=no",
                ],
                cwd=self.project_root,
                capture_output=True,
                timeout=60,
                check=False,
            )

            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    return json.load(f)
        except:
            pass
        return {}

    def analyze(self):
        """Run comprehensive analysis."""
        print("=" * 80)
        print("TEST COVERAGE AND QUALITY AUDIT")
        print("=" * 80)

        source_files = self.find_all_source_files()
        test_files = self.find_all_test_files()
        mapping = self.map_source_to_test(source_files, test_files)

        print("\n📊 PROJECT STATISTICS")
        print(f"  Source files: {len(source_files)}")
        print(f"  Test files: {len(test_files)}")
        print(f"  Source files with tests: {len(mapping)}")
        print(f"  Source files without tests: {len(source_files) - len(mapping)}")

        # 1. COVERAGE GAPS ANALYSIS
        print("\n\n1. COVERAGE GAPS ANALYSIS")
        print("-" * 40)

        # Get coverage data
        coverage_data = self.get_coverage_data()

        if coverage_data and "files" in coverage_data:
            coverage_by_module = {}
            for file_path, data in coverage_data["files"].items():
                if file_path.startswith("src/"):
                    rel_path = file_path.replace("src/", "")
                    coverage_by_module[rel_path] = data["summary"]["percent_covered"]

            # Sort by coverage
            sorted_coverage = sorted(coverage_by_module.items(), key=lambda x: x[1])

            print("\n🔴 CRITICAL: Modules with < 50% coverage:")
            critical_modules = [(m, c) for m, c in sorted_coverage if c < 50]
            for module, cov in critical_modules[:20]:
                print(f"  {module:60} {cov:5.1f}%")

            print("\n🟡 WARNING: Modules with 50-80% coverage:")
            warning_modules = [(m, c) for m, c in sorted_coverage if 50 <= c < 80]
            for module, cov in warning_modules[:10]:
                print(f"  {module:60} {cov:5.1f}%")

            print("\n🟢 GOOD: Modules with > 80% coverage:")
            good_modules = [(m, c) for m, c in sorted_coverage if c >= 80]
            for module, cov in good_modules[:10]:
                print(f"  {module:60} {cov:5.1f}%")

        # 2. TEST FILE MAPPING
        print("\n\n2. TEST FILE MAPPING")
        print("-" * 40)

        # Find source files without tests
        untested_files = [f for f in source_files.keys() if f not in mapping]

        print(f"\n❌ Source files WITHOUT test files ({len(untested_files)}):")
        for file in sorted(untested_files)[:30]:
            if not file.endswith("__init__.py"):
                print(f"  src/{file}")

        # 3. TEST QUALITY METRICS
        print("\n\n3. TEST QUALITY METRICS")
        print("-" * 40)

        quality_issues = {
            "no_assertions": [],
            "too_many_assertions": [],
            "unclear_names": [],
            "uses_real_services": [],
            "uses_mock_any": [],
            "has_sleep": [],
            "low_docstring_coverage": [],
        }

        for test_file_rel, test_file_path in test_files.items():
            metrics = self.analyze_test_quality(test_file_path)

            if metrics["tests_with_no_assertions"]:
                quality_issues["no_assertions"].append(
                    (test_file_rel, metrics["tests_with_no_assertions"])
                )

            if metrics["tests_with_many_assertions"]:
                quality_issues["too_many_assertions"].append(
                    (test_file_rel, metrics["tests_with_many_assertions"])
                )

            if metrics["tests_with_unclear_names"]:
                quality_issues["unclear_names"].append(
                    (test_file_rel, metrics["tests_with_unclear_names"][:3])
                )

            if metrics["uses_real_services"]:
                quality_issues["uses_real_services"].append(test_file_rel)

            if metrics["uses_mock_any"]:
                quality_issues["uses_mock_any"].append(test_file_rel)

            if metrics["has_sleep"]:
                quality_issues["has_sleep"].append(test_file_rel)

            if metrics["total_tests"] > 0:
                docstring_ratio = metrics["has_docstrings"] / metrics["total_tests"]
                if docstring_ratio < 0.3:
                    quality_issues["low_docstring_coverage"].append(
                        (test_file_rel, docstring_ratio)
                    )

        print("\n⚠️ Tests with NO assertions:")
        for file, tests in quality_issues["no_assertions"][:10]:
            print(f"  {file}: {', '.join(tests[:3])}")

        print("\n⚠️ Tests with TOO MANY assertions (>5):")
        for file, tests in quality_issues["too_many_assertions"][:10]:
            test_info = [f"{name}({count})" for name, count in tests[:3]]
            print(f"  {file}: {', '.join(test_info)}")

        print("\n⚠️ Tests using REAL services (not mocked):")
        for file in quality_issues["uses_real_services"][:10]:
            print(f"  {file}")

        print("\n⚠️ Tests using Mock.ANY (lazy assertions):")
        for file in quality_issues["uses_mock_any"][:10]:
            print(f"  {file}")

        print("\n⚠️ Tests with sleep() calls:")
        for file in quality_issues["has_sleep"][:10]:
            print(f"  {file}")

        # 4. MISSING TEST SCENARIOS
        print("\n\n4. CRITICAL SERVICE COVERAGE")
        print("-" * 40)

        critical_services = [
            "services/ai_service_v2.py",
            "services/orchestrators/definition_orchestrator_v2.py",
            "services/orchestrators/validation_orchestrator_v2.py",
            "services/validation/modular_validation_service.py",
            "services/definition_repository.py",
            "services/export_service.py",
            "services/container.py",
            "services/service_factory.py",
        ]

        print("\n📌 Critical Service Coverage:")
        for service in critical_services:
            if service in source_files:
                test_count = len(mapping.get(service, []))
                cov = (
                    coverage_by_module.get(service, 0)
                    if "coverage_by_module" in locals()
                    else "?"
                )
                status = "🟢" if test_count > 0 else "🔴"
                print(f"  {status} {service:50} Tests: {test_count}, Coverage: {cov}%")

        # 5. TEST IMPROVEMENT PRIORITY MATRIX
        print("\n\n5. TEST IMPROVEMENT PRIORITY MATRIX")
        print("-" * 40)

        print("\n🎯 HIGH PRIORITY (Critical services with low/no coverage):")
        high_priority = []
        for service in critical_services:
            if service in untested_files or (
                service in coverage_by_module and coverage_by_module[service] < 50
            ):
                high_priority.append(service)
                print(f"  - src/{service}")

        print("\n📊 SUMMARY METRICS:")
        print(f"  Total source files: {len(source_files)}")
        print(
            f"  Files with tests: {len(mapping)} ({len(mapping)*100/len(source_files):.1f}%)"
        )
        print(
            f"  Files without tests: {len(untested_files)} ({len(untested_files)*100/len(source_files):.1f}%)"
        )
        print(
            f"  Test quality issues found: {sum(len(v) for v in quality_issues.values())}"
        )

        if coverage_data and "totals" in coverage_data:
            totals = coverage_data["totals"]
            print("\n📈 OVERALL COVERAGE:")
            print(f"  Lines: {totals.get('num_statements', 0)}")
            print(f"  Covered: {totals.get('covered_lines', 0)}")
            print(f"  Missing: {totals.get('missing_lines', 0)}")
            print(f"  Coverage: {totals.get('percent_covered', 0):.1f}%")


if __name__ == "__main__":
    analyzer = TestCoverageAnalyzer(Path("/Users/chrislehnen/Projecten/Definitie-app"))
    analyzer.analyze()
