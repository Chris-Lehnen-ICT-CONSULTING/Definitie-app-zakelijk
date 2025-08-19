#!/usr/bin/env python3
"""Analyze Python file usage across the project."""

import os
import ast
import re
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Tuple

def find_python_files(root_dir: str) -> List[Path]:
    """Find all Python files in the project."""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip __pycache__ and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files

def extract_imports(file_path: Path) -> Set[str]:
    """Extract all imports from a Python file."""
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    # Also add specific imports
                    for alias in node.names:
                        imports.add(f"{node.module}.{alias.name}")
    except:
        # If parsing fails, try regex as fallback
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find import statements
            import_pattern = r'(?:from\s+(\S+)\s+import|import\s+(\S+))'
            matches = re.findall(import_pattern, content)
            for match in matches:
                module = match[0] or match[1]
                if module:
                    imports.add(module.strip())
        except:
            pass
    
    return imports

def is_entry_point(file_path: Path) -> bool:
    """Check if file is an entry point (has if __name__ == '__main__')."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return 'if __name__ == "__main__"' in content or "if __name__ == '__main__'" in content
    except:
        return False

def analyze_module(file_path: Path) -> Dict[str, any]:
    """Analyze a Python module."""
    info = {
        'path': str(file_path),
        'name': file_path.stem,
        'size': file_path.stat().st_size,
        'imports': extract_imports(file_path),
        'is_entry_point': is_entry_point(file_path),
        'is_test': 'test' in str(file_path).lower(),
        'is_init': file_path.name == '__init__.py',
        'module_path': None,
        'description': None
    }
    
    # Determine module path
    if 'src' in file_path.parts:
        src_idx = file_path.parts.index('src')
        module_parts = file_path.parts[src_idx + 1:-1] + (file_path.stem,)
        if file_path.name != '__init__.py':
            info['module_path'] = '.'.join(module_parts)
        else:
            info['module_path'] = '.'.join(module_parts[:-1]) if module_parts[:-1] else 'src'
    
    # Try to extract module docstring
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
            docstring = ast.get_docstring(tree)
            if docstring:
                info['description'] = docstring.split('\n')[0].strip()
    except:
        pass
    
    return info

def main():
    """Main analysis function."""
    project_root = Path.cwd()
    
    # Find all Python files
    print("Scanning for Python files...")
    python_files = find_python_files(project_root)
    
    # Analyze each file
    print(f"Found {len(python_files)} Python files. Analyzing...")
    
    modules = []
    import_graph = defaultdict(set)  # module -> set of modules that import it
    
    for file_path in python_files:
        module_info = analyze_module(file_path)
        modules.append(module_info)
        
        # Build import graph
        module_name = module_info['module_path'] or str(file_path)
        for imp in module_info['imports']:
            import_graph[imp].add(module_name)
    
    # Categorize modules
    src_modules = [m for m in modules if 'src' in m['path'] and not m['is_test']]
    test_modules = [m for m in modules if m['is_test']]
    script_modules = [m for m in modules if 'scripts' in m['path'] or 'tools' in m['path']]
    entry_points = [m for m in modules if m['is_entry_point']]
    
    # Find potentially unused modules
    all_imports = set()
    for module in modules:
        all_imports.update(module['imports'])
    
    unused_modules = []
    for module in src_modules:
        if module['is_init']:
            continue
        
        module_variations = {
            module['module_path'],
            module['name'],
            str(Path(module['path']).relative_to(project_root)).replace('/', '.').replace('.py', ''),
        }
        
        # Check if any variation is imported
        is_imported = any(
            any(var in imp for imp in all_imports if var) 
            for var in module_variations if var
        )
        
        if not is_imported and not module['is_entry_point']:
            unused_modules.append(module)
    
    # Print results
    print("\n" + "="*80)
    print("PROJECT STRUCTURE ANALYSIS")
    print("="*80)
    
    print(f"\nSummary:")
    print(f"  Total Python files: {len(python_files)}")
    print(f"  Source modules: {len(src_modules)}")
    print(f"  Test modules: {len(test_modules)}")
    print(f"  Scripts/Tools: {len(script_modules)}")
    print(f"  Entry points: {len(entry_points)}")
    
    print("\n## ENTRY POINTS")
    print("-" * 40)
    for module in sorted(entry_points, key=lambda x: x['path']):
        print(f"  {module['path']}")
        if module['description']:
            print(f"    └─ {module['description']}")
    
    print("\n## MAIN SOURCE MODULES (src/)")
    print("-" * 40)
    
    # Group by directory
    by_dir = defaultdict(list)
    for module in src_modules:
        if module['is_init']:
            continue
        dir_path = str(Path(module['path']).parent.relative_to(project_root))
        by_dir[dir_path].append(module)
    
    for dir_path in sorted(by_dir.keys()):
        print(f"\n### {dir_path}/")
        for module in sorted(by_dir[dir_path], key=lambda x: x['name']):
            status = "✓" if module['module_path'] in import_graph else "?"
            print(f"  {status} {module['name']}.py")
            if module['description']:
                print(f"      {module['description'][:70]}...")
    
    print("\n## POTENTIALLY UNUSED MODULES")
    print("-" * 40)
    if unused_modules:
        for module in sorted(unused_modules, key=lambda x: x['path']):
            print(f"  ⚠️  {module['path']}")
    else:
        print("  None found!")
    
    print("\n## TEST COVERAGE")
    print("-" * 40)
    test_dirs = defaultdict(int)
    for module in test_modules:
        dir_path = str(Path(module['path']).parent.relative_to(project_root))
        test_dirs[dir_path] += 1
    
    for dir_path in sorted(test_dirs.keys()):
        print(f"  {dir_path}: {test_dirs[dir_path]} test files")

if __name__ == "__main__":
    main()