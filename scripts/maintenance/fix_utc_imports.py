#!/usr/bin/env python3
"""Fix UTC imports voor Python 3.10 compatibility."""
import os
import re


def fix_utc_import(filepath):
    """Fix UTC import in een bestand."""
    with open(filepath) as f:
        content = f.read()

    # Check if file has UTC import
    if "from datetime import" in content and "UTC" in content:
        # Replace the import line
        pattern = r"from datetime import ([^#\n]*)"

        def replace_import(match):
            imports = match.group(1)
            if "UTC" in imports:
                # Remove UTC from imports
                imports_list = [i.strip() for i in imports.split(",")]
                imports_list = [i for i in imports_list if i != "UTC"]
                new_import = "from datetime import " + ", ".join(imports_list)
                # Add timezone import and UTC alias
                return (
                    new_import
                    + "\nfrom datetime import timezone\nUTC = timezone.utc  # Python 3.10 compatibility"
                )
            return match.group(0)

        new_content = re.sub(pattern, replace_import, content)

        if new_content != content:
            with open(filepath, "w") as f:
                f.write(new_content)
            print(f"Fixed: {filepath}")
            return True
    return False


# Fix all Python files in src
fixed_count = 0
for root, _dirs, files in os.walk("src"):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            if fix_utc_import(filepath):
                fixed_count += 1

print(f"\nFixed {fixed_count} files with UTC imports")
