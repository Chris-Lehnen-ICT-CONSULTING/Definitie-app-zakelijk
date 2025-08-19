#!/usr/bin/env python3
"""
Analyze which Python files are not used in the DefinitieAgent application.
"""

import ast
from collections import defaultdict, deque
from pathlib import Path


def get_imports_from_file(filepath):
    """Extract all imports from a Python file."""
    imports = set()
    try:
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    # Also add the full import path
                    for alias in node.names:
                        imports.add(f"{node.module}.{alias.name}")
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")

    return imports


def module_to_filepath(module_name, base_path="src"):
    """Convert module name to potential file paths."""
    paths = []

    # Replace dots with slashes
    module_path = module_name.replace(".", "/")

    # Try as direct file
    paths.append(Path(base_path) / f"{module_path}.py")

    # Try as package __init__.py
    paths.append(Path(base_path) / module_path / "__init__.py")

    # Try without src prefix
    if module_path.startswith("src/"):
        module_path = module_path[4:]
        paths.append(Path(base_path) / f"{module_path}.py")
        paths.append(Path(base_path) / module_path / "__init__.py")

    return paths


def find_all_dependencies(start_files, base_path="src"):
    """Find all files that are imported directly or indirectly from start files."""
    used_files = set()
    to_process = deque(start_files)
    processed = set()

    while to_process:
        current_file = to_process.popleft()
        if current_file in processed:
            continue

        processed.add(current_file)
        if Path(current_file).exists():
            used_files.add(str(Path(current_file).relative_to(".")))

            # Get imports from this file
            imports = get_imports_from_file(current_file)

            # Convert imports to potential file paths
            for imp in imports:
                for filepath in module_to_filepath(imp, base_path):
                    if filepath.exists() and str(filepath) not in processed:
                        to_process.append(str(filepath))

    return used_files


def main():
    # Entry points
    entry_points = [
        "src/main.py",
        "src/app.py",
        "app.py",  # Check root level too
    ]

    # Find which entry point exists
    active_entry_points = []
    for ep in entry_points:
        if Path(ep).exists():
            active_entry_points.append(ep)
            print(f"Found entry point: {ep}")

    if not active_entry_points:
        print("No entry points found!")
        return

    # Find all Python files in src
    all_py_files = set()
    for py_file in Path("src").rglob("*.py"):
        all_py_files.add(str(py_file.relative_to(".")))

    print(f"\nTotal Python files in src: {len(all_py_files)}")

    # Find all used files
    used_files = find_all_dependencies(active_entry_points)
    print(f"Used Python files: {len(used_files)}")

    # Find unused files
    unused_files = all_py_files - used_files

    print(f"\nUnused Python files: {len(unused_files)}")

    # Group by directory
    unused_by_dir = defaultdict(list)
    for filepath in sorted(unused_files):
        dir_name = str(Path(filepath).parent)
        unused_by_dir[dir_name].append(Path(filepath).name)

    # Print results
    print("\n=== UNUSED FILES BY DIRECTORY ===\n")
    for dir_name in sorted(unused_by_dir.keys()):
        files = unused_by_dir[dir_name]
        print(f"{dir_name}/ ({len(files)} files)")
        for f in sorted(files)[:10]:  # Show max 10 files per dir
            print(f"  - {f}")
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more files")
        print()

    # Special directories that are likely fully unused
    special_dirs = ["deprecated", "archive", "old", "backup", "temp", "test"]
    print("\n=== LIKELY DEPRECATED DIRECTORIES ===\n")
    for dir_path in sorted(unused_by_dir.keys()):
        for special in special_dirs:
            if special in dir_path.lower():
                print(f"{dir_path}/ ({len(unused_by_dir[dir_path])} files)")
                break


if __name__ == "__main__":
    main()
