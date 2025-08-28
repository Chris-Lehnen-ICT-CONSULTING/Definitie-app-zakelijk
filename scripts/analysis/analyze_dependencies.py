import os
import re
from collections import Counter, defaultdict

# Track imports
service_imports = defaultdict(set)
interface_users = []
external_deps = Counter()

# Parse each file
for root, dirs, files in os.walk("src/services"):
    for file in files:
        if file.endswith(".py") and file != "__init__.py":
            service_name = file[:-3]
            filepath = os.path.join(root, file)

            with open(filepath) as f:
                content = f.read()

                # Find service imports
                service_import_pattern = r"from services\.(\w+) import"
                for match in re.finditer(service_import_pattern, content):
                    imported_service = match.group(1)
                    if imported_service != "interfaces":
                        service_imports[service_name].add(imported_service)

                # Check if uses interfaces
                if (
                    "from services.interfaces import" in content
                    or "from .interfaces import" in content
                ):
                    interface_users.append(service_name)

                # Find external imports
                import_pattern = r"^(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith(("import ", "from ")) and not line.startswith(
                        "#"
                    ):
                        match = re.match(import_pattern, line)
                        if match:
                            module = match.group(1)
                            if not module.startswith(
                                (
                                    "services",
                                    ".",
                                    "database",
                                    "models",
                                    "ui",
                                    "opschoning",
                                    "toetsregels",
                                    "validation",
                                )
                            ):
                                external_deps[module] += 1

# Count how many times each service is imported
import_count = Counter()
for service, imports in service_imports.items():
    for imported in imports:
        import_count[imported] += 1

print("=== KERN SERVICES (Top 5 meest geïmporteerde) ===")
for service, count in import_count.most_common(5):
    print(f"{service}: {count} keer geïmporteerd")

print("\n=== DEPENDENCY FLOW ===")
for service in sorted(service_imports.keys()):
    imports = service_imports[service]
    if imports:
        print(f'{service} -> {", ".join(sorted(imports))}')

print("\n=== INTERFACE GEBRUIKERS ===")
print(
    f'Services die interfaces gebruiken ({len(interface_users)}): {", ".join(sorted(interface_users))}'
)

print("\n=== EXTERNE DEPENDENCIES (Top 10) ===")
for dep, count in external_deps.most_common(10):
    print(f"{dep}: {count} keer")

# Check for circular dependencies
print("\n=== CIRCULAIRE DEPENDENCIES CHECK ===")
circular_found = False
for service_a, imports_a in service_imports.items():
    for service_b in imports_a:
        if service_b in service_imports and service_a in service_imports[service_b]:
            if not circular_found:
                circular_found = True
            print(f"CIRCULAIRE DEPENDENCY: {service_a} <-> {service_b}")

if not circular_found:
    print("Geen circulaire dependencies gevonden!")

# Create visualization data
print("\n=== GENERATING VISUALIZATION DATA ===")
import json

# Prepare data for visualization
nodes = []
links = []
node_set = set()

# Add all services as nodes
for service in service_imports.keys():
    node_set.add(service)
    for imported in service_imports[service]:
        node_set.add(imported)

# Add interface users too
for user in interface_users:
    node_set.add(user)

# Create node objects with metadata
for node in node_set:
    node_data = {
        "id": node,
        "group": "service",
        "imports_count": import_count.get(node, 0),
        "uses_interfaces": node in interface_users,
    }

    # Determine node type
    if node in [
        "definition_generator_config",
        "definition_generator_prompts",
        "definition_generator_context",
    ]:
        node_data["group"] = "config"
    elif node in import_count and import_count[node] >= 3:
        node_data["group"] = "core"
    elif node in interface_users:
        node_data["group"] = "interface_user"

    nodes.append(node_data)

# Create links
for source, targets in service_imports.items():
    for target in targets:
        links.append({"source": source, "target": target, "type": "imports"})

# Save to JSON
viz_data = {
    "nodes": nodes,
    "links": links,
    "stats": {
        "total_services": len(node_set),
        "interface_users": len(interface_users),
        "top_imports": dict(import_count.most_common(5)),
        "external_deps": dict(external_deps.most_common(10)),
    },
}

with open("service_dependencies.json", "w") as f:
    json.dump(viz_data, f, indent=2)

print("Visualization data saved to service_dependencies.json")
