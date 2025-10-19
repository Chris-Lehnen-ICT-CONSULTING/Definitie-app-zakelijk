#!/usr/bin/env python3
"""
Dependency analysis script to detect circular dependencies and architecture violations.
"""

import re
from pathlib import Path


class DependencyAnalyzer:
    def __init__(self, src_path: str):
        self.src_path = Path(src_path)
        self.dependencies: dict[str, set[str]] = {}

    def analyze_file(self, file_path: Path) -> set[str]:
        """Extract imports from a Python file."""
        imports = set()
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

                # Find relative imports
                for match in re.finditer(
                    r"^from\s+(\w+(?:\.\w+)*)\s+import", content, re.MULTILINE
                ):
                    module = match.group(1)
                    if not module.startswith(
                        "."
                    ):  # Skip relative imports starting with .
                        imports.add(module)

                # Find absolute imports
                for match in re.finditer(
                    r"^import\s+(\w+(?:\.\w+)*)", content, re.MULTILINE
                ):
                    module = match.group(1)
                    imports.add(module)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

        return imports

    def get_layer(self, module: str) -> str:
        """Determine which architecture layer a module belongs to."""
        if module.startswith("ui"):
            return "UI"
        if module.startswith("services"):
            return "Services"
        if module.startswith(("database", "repository")):
            return "Repository"
        if module.startswith("models"):
            return "Models"
        return "Other"

    def analyze_all(self):
        """Analyze all Python files in the source directory."""
        for py_file in self.src_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            relative_path = py_file.relative_to(self.src_path)
            module_name = str(relative_path.with_suffix("")).replace("/", ".")

            imports = self.analyze_file(py_file)
            self.dependencies[module_name] = imports

    def find_violations(self) -> list[str]:
        """Find clean architecture violations."""
        violations = []

        for module, imports in self.dependencies.items():
            module_layer = self.get_layer(module)

            for imported_module in imports:
                imported_layer = self.get_layer(imported_module)

                # Check for violations
                if module_layer == "Services" and imported_layer == "UI":
                    violations.append(
                        f"VIOLATION: Service '{module}' imports UI '{imported_module}'"
                    )
                elif module_layer == "Repository" and imported_layer in [
                    "UI",
                    "Services",
                ]:
                    violations.append(
                        f"VIOLATION: Repository '{module}' imports {imported_layer} '{imported_module}'"
                    )
                elif module_layer == "Models" and imported_layer in [
                    "UI",
                    "Services",
                    "Repository",
                ]:
                    violations.append(
                        f"VIOLATION: Model '{module}' imports {imported_layer} '{imported_module}'"
                    )

        return violations

    def find_cycles(self) -> list[list[str]]:
        """Find circular dependencies using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = [*path[cycle_start:], node]
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Get dependencies for this node
            deps = self.dependencies.get(node, set())
            for dep in deps:
                if dep in self.dependencies:  # Only analyze internal modules
                    dfs(dep)

            path.pop()
            rec_stack.remove(node)

        for module in self.dependencies:
            if module not in visited:
                dfs(module)

        return cycles


if __name__ == "__main__":
    analyzer = DependencyAnalyzer("src")
    analyzer.analyze_all()

    print("=== CLEAN ARCHITECTURE ANALYSIS ===\n")

    violations = analyzer.find_violations()
    if violations:
        print("ARCHITECTURE VIOLATIONS FOUND:")
        for violation in violations:
            print(f"  {violation}")
    else:
        print("No architecture violations found.")

    print("\n" + "=" * 50 + "\n")

    cycles = analyzer.find_cycles()
    if cycles:
        print("CIRCULAR DEPENDENCIES FOUND:")
        for i, cycle in enumerate(cycles, 1):
            print(f"  Cycle {i}: {' -> '.join(cycle)}")
    else:
        print("No circular dependencies found.")
