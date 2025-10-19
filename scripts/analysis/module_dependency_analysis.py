#!/usr/bin/env python3
"""
Module Dependency Analysis Tool

Analyzes the dependencies between prompt modules and creates a dependency graph.
"""

import json
import re
from pathlib import Path


def analyze_module_dependencies() -> dict[str, dict[str, any]]:
    """
    Analyze all module dependencies based on get_dependencies() methods.
    """
    modules_dir = Path(
        "/Users/chrislehnen/Projecten/Definitie-app/src/services/prompts/modules"
    )

    # Module files to analyze
    module_files = [
        "context_awareness_module.py",
        "definition_task_module.py",
        "error_prevention_module.py",
        "expertise_module.py",
        "output_specification_module.py",
        "quality_rules_module.py",
        "semantic_categorisation_module.py",
    ]

    # Results dictionary
    analysis = {}

    for module_file in module_files:
        module_name = module_file.replace("_module.py", "")
        file_path = modules_dir / module_file

        if file_path.exists():
            # Read the file and extract get_dependencies() return value
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Find get_dependencies method
            deps_start = content.find("def get_dependencies(self) -> list[str]:")
            if deps_start != -1:
                # Find the return statement
                deps_section = content[deps_start : deps_start + 500]

                # Extract dependencies
                dependencies = []
                if "return []" in deps_section:
                    dependencies = []
                elif 'return ["' in deps_section:
                    # Extract the list of dependencies
                    match = re.search(r"return \[(.*?)\]", deps_section, re.DOTALL)
                    if match:
                        deps_str = match.group(1)
                        # Parse the dependencies
                        deps = re.findall(r'"([^"]+)"', deps_str)
                        dependencies = deps

                # Also check what shared data this module sets
                shared_data_set = []
                for line in content.split("\n"):
                    if "context.set_shared(" in line:
                        match = re.search(r'context\.set_shared\("([^"]+)"', line)
                        if match:
                            shared_data_set.append(match.group(1))

                # Check what shared data this module gets
                shared_data_get = []
                for line in content.split("\n"):
                    if "context.get_shared(" in line:
                        match = re.search(r'context\.get_shared\("([^"]+)"', line)
                        if match:
                            shared_data_get.append(match.group(1))

                analysis[module_name] = {
                    "dependencies": dependencies,
                    "shared_data_set": list(set(shared_data_set)),
                    "shared_data_get": list(set(shared_data_get)),
                    "file": module_file,
                }

    return analysis


def create_dependency_graph(analysis: dict[str, dict[str, any]]) -> str:
    """
    Create a Mermaid diagram showing module dependencies.
    """
    mermaid = ["graph TD"]

    # Add nodes
    for module in analysis:
        mermaid.append(f"    {module}[{module}]")

    # Add direct dependencies (from get_dependencies())
    for module, info in analysis.items():
        for dep in info["dependencies"]:
            mermaid.append(f"    {module} -->|depends on| {dep}")

    # Add data dependencies (shared data flow)
    data_providers = {}
    for module, info in analysis.items():
        for data in info["shared_data_set"]:
            if data not in data_providers:
                data_providers[data] = []
            data_providers[data].append(module)

    # Show data flow relationships
    for module, info in analysis.items():
        for data in info["shared_data_get"]:
            if data in data_providers:
                for provider in data_providers[data]:
                    if provider != module:
                        mermaid.append(f"    {provider} -.->|{data}| {module}")

    return "\n".join(mermaid)


def analyze_coupling(analysis: dict[str, dict[str, any]]) -> dict[str, any]:
    """
    Analyze the coupling between modules.
    """
    coupling_analysis = {
        "direct_dependencies": {},
        "data_dependencies": {},
        "independent_modules": [],
        "tightly_coupled_pairs": [],
        "dependency_chains": [],
    }

    # Analyze direct dependencies
    for module, info in analysis.items():
        if info["dependencies"]:
            coupling_analysis["direct_dependencies"][module] = info["dependencies"]
        else:
            coupling_analysis["independent_modules"].append(module)

    # Analyze data dependencies
    data_flow = {}
    for module, info in analysis.items():
        if info["shared_data_get"]:
            data_flow[module] = {
                "needs": info["shared_data_get"],
                "provides": info["shared_data_set"],
            }

    coupling_analysis["data_dependencies"] = data_flow

    # Find tightly coupled modules
    for module1, info1 in analysis.items():
        for module2, info2 in analysis.items():
            if module1 != module2:
                # Check if they depend on each other's data
                module1_needs = set(info1["shared_data_get"])
                module2_provides = set(info2["shared_data_set"])
                module2_needs = set(info2["shared_data_get"])
                module1_provides = set(info1["shared_data_set"])

                if (module1_needs & module2_provides) and (
                    module2_needs & module1_provides
                ):
                    pair = tuple(sorted([module1, module2]))
                    if pair not in coupling_analysis["tightly_coupled_pairs"]:
                        coupling_analysis["tightly_coupled_pairs"].append(pair)

    # Find dependency chains
    def find_chains(module, visited=None):
        if visited is None:
            visited = []
        if module in visited:
            return [[*visited, module]]  # Circular dependency

        visited.append(module)
        chains = []

        if module in analysis:
            for dep in analysis[module]["dependencies"]:
                chains.extend(find_chains(dep, visited.copy()))

        if not chains:
            return [visited]
        return chains

    all_chains = []
    for module in analysis:
        chains = find_chains(module)
        for chain in chains:
            if len(chain) > 1 and chain not in all_chains:
                all_chains.append(chain)

    coupling_analysis["dependency_chains"] = all_chains

    return coupling_analysis


def generate_report(
    analysis: dict[str, dict[str, any]], coupling: dict[str, any]
) -> str:
    """
    Generate a comprehensive report on module dependencies.
    """
    report = []
    report.append("# Module Dependency Analysis Report\n")
    report.append("## Overview\n")
    report.append(f"Total modules analyzed: {len(analysis)}\n")

    # Module details
    report.append("## Module Dependencies\n")
    for module, info in sorted(analysis.items()):
        report.append(f"### {module}")
        report.append(
            f"- **Direct Dependencies**: {info['dependencies'] if info['dependencies'] else 'None'}"
        )
        report.append(
            f"- **Shared Data Set**: {info['shared_data_set'] if info['shared_data_set'] else 'None'}"
        )
        report.append(
            f"- **Shared Data Get**: {info['shared_data_get'] if info['shared_data_get'] else 'None'}"
        )
        report.append("")

    # Coupling analysis
    report.append("## Coupling Analysis\n")

    report.append("### Independent Modules")
    report.append("Modules with no direct dependencies:")
    for module in coupling["independent_modules"]:
        report.append(f"- {module}")
    report.append("")

    report.append("### Direct Dependencies")
    for module, deps in coupling["direct_dependencies"].items():
        report.append(f"- **{module}** depends on: {', '.join(deps)}")
    report.append("")

    report.append("### Data Flow Dependencies")
    for module, data in coupling["data_dependencies"].items():
        if data["needs"]:
            report.append(f"- **{module}**")
            report.append(f"  - Needs: {', '.join(data['needs'])}")
            report.append(
                f"  - Provides: {', '.join(data['provides']) if data['provides'] else 'None'}"
            )
    report.append("")

    report.append("### Dependency Chains")
    for i, chain in enumerate(coupling["dependency_chains"], 1):
        report.append(f"{i}. {' → '.join(chain)}")
    report.append("")

    # Modularity assessment
    report.append("## Modularity Assessment\n")

    independent_count = len(coupling["independent_modules"])
    total_modules = len(analysis)
    modularity_score = (independent_count / total_modules) * 100

    report.append(
        f"- **Modularity Score**: {modularity_score:.1f}% ({independent_count}/{total_modules} modules are independent)"
    )
    report.append(
        f"- **Tightly Coupled Pairs**: {len(coupling['tightly_coupled_pairs'])}"
    )
    report.append(
        f"- **Longest Dependency Chain**: {max(len(chain) for chain in coupling['dependency_chains']) if coupling['dependency_chains'] else 0}"
    )

    # Recommendations
    report.append("\n## Recommendations\n")

    if modularity_score < 50:
        report.append("⚠️ **Low modularity detected**. Consider:")
        report.append("- Reducing direct dependencies between modules")
        report.append(
            "- Using event-based communication instead of direct dependencies"
        )
        report.append("- Implementing a mediator pattern for shared data")

    if coupling["tightly_coupled_pairs"]:
        report.append("\n⚠️ **Tightly coupled modules detected**:")
        for pair in coupling["tightly_coupled_pairs"]:
            report.append(f"- {pair[0]} ↔️ {pair[1]}")

    return "\n".join(report)


def main():
    """Main function to run the analysis."""
    print("Analyzing module dependencies...")

    # Analyze dependencies
    analysis = analyze_module_dependencies()

    # Create dependency graph
    mermaid_graph = create_dependency_graph(analysis)

    # Analyze coupling
    coupling = analyze_coupling(analysis)

    # Generate report
    report = generate_report(analysis, coupling)

    # Save results
    with open("module_dependency_report.md", "w", encoding="utf-8") as f:
        f.write(report)
        f.write("\n\n## Dependency Graph\n\n")
        f.write("```mermaid\n")
        f.write(mermaid_graph)
        f.write("\n```\n")

    # Save raw analysis as JSON
    with open("module_dependency_analysis.json", "w", encoding="utf-8") as f:
        json.dump({"analysis": analysis, "coupling": coupling}, f, indent=2)

    print("Analysis complete!")
    print("- Report saved to: module_dependency_report.md")
    print("- Raw data saved to: module_dependency_analysis.json")

    # Print summary
    print("\nSummary:")
    print(f"- Total modules: {len(analysis)}")
    print(f"- Independent modules: {len(coupling['independent_modules'])}")
    print(f"- Modules with dependencies: {len(coupling['direct_dependencies'])}")
    print(f"- Data flow relationships: {len(coupling['data_dependencies'])}")


if __name__ == "__main__":
    main()
