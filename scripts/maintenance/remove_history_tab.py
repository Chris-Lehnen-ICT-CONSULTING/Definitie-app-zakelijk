#!/usr/bin/env python3
"""
History Tab Removal Tool - Precise and Safe Removal
Removes all History Tab references from the codebase
"""

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


class HistoryTabRemover:
    """Handles safe removal of History Tab from the codebase"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backup_dir = Path(
            f"/tmp/history_tab_removal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.modifications: list[str] = []
        self.errors: list[str] = []

    def create_backups(self) -> bool:
        """Create backups of files to be modified"""
        print("📁 Creating backups...")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        files_to_backup = [
            self.project_root / "src/ui/tabbed_interface.py",
            self.project_root / "src/ui/components/history_tab.py.backup",
        ]

        for file_path in files_to_backup:
            if file_path.exists():
                backup_path = self.backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)
                print(f"  ✓ Backed up: {file_path.name}")

        # Create rollback script
        self._create_rollback_script()
        return True

    def _create_rollback_script(self):
        """Create a rollback script"""
        rollback_script = self.backup_dir / "rollback.sh"
        rollback_content = f"""#!/bin/bash
# Rollback script for History Tab removal
echo "Rolling back History Tab removal..."

# Restore files
cp {self.backup_dir}/tabbed_interface.py {self.project_root}/src/ui/tabbed_interface.py

# Restore history tab backup if it existed
if [ -f "{self.backup_dir}/history_tab.py.backup" ]; then
    cp {self.backup_dir}/history_tab.py.backup {self.project_root}/src/ui/components/history_tab.py.backup
fi

# Clear Streamlit cache
streamlit cache clear 2>/dev/null || true

echo "✓ Rollback complete!"
"""
        rollback_script.write_text(rollback_content)
        rollback_script.chmod(0o755)
        print(f"  ✓ Created rollback script: {rollback_script}")

    def remove_from_tabbed_interface(self) -> bool:
        """Remove History Tab references from tabbed_interface.py"""
        print("\n🔧 Modifying tabbed_interface.py...")

        file_path = self.project_root / "src/ui/tabbed_interface.py"
        if not file_path.exists():
            self.errors.append(f"File not found: {file_path}")
            return False

        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # Remove import statement
            if "from ui.components.history_tab import HistoryTab" in line:
                self.modifications.append(f"Line {i+1}: Removed HistoryTab import")
                i += 1
                continue

            # Remove initialization
            if "self.history_tab = HistoryTab" in line:
                self.modifications.append(
                    f"Line {i+1}: Removed HistoryTab initialization"
                )
                i += 1
                continue

            # Remove history tab config (multi-line block)
            if '"history":' in line and "{" in lines[i]:
                # Find the closing brace
                brace_count = 1
                start_line = i
                i += 1
                while i < len(lines) and brace_count > 0:
                    if "{" in lines[i]:
                        brace_count += lines[i].count("{")
                    if "}" in lines[i]:
                        brace_count -= lines[i].count("}")
                    i += 1
                self.modifications.append(
                    f"Lines {start_line+1}-{i}: Removed history tab config"
                )
                continue

            # Remove render block
            if 'elif tab_key == "history":' in line:
                start_line = i
                i += 1
                # Skip the render line
                if i < len(lines) and "self.history_tab.render()" in lines[i]:
                    i += 1
                self.modifications.append(
                    f"Lines {start_line+1}-{i}: Removed history tab render block"
                )
                continue

            new_lines.append(line)
            i += 1

        # Write modified content
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        print(f"  ✓ Applied {len(self.modifications)} modifications")
        return True

    def clean_session_state_references(self) -> bool:
        """Create script to clean session state references"""
        print("\n🧹 Creating session state cleanup script...")

        cleanup_script = self.project_root / "scripts/clean_history_session_state.py"
        cleanup_content = '''#!/usr/bin/env python3
"""Clean History Tab related session state keys"""

import streamlit as st

def clean_history_session_state():
    """Remove history-related keys from session state"""
    history_keys = [
        'history_date_range',
        'history_start_date',
        'history_end_date',
        'history_status_filter',
        'history_context_filter',
        'history_search',
        'history_filters',
        'history_page',
        'history_selected',
        'history_sort'
    ]

    removed = []
    for key in history_keys:
        if key in st.session_state:
            del st.session_state[key]
            removed.append(key)

    if removed:
        print(f"Removed {len(removed)} history-related session state keys:")
        for key in removed:
            print(f"  - {key}")
    else:
        print("No history-related session state keys found")

    return removed

if __name__ == "__main__":
    # This can be run standalone or imported
    if 'streamlit' in sys.modules:
        clean_history_session_state()
    else:
        print("Note: This script should be run within a Streamlit context")
        print("Add to your main.py: from scripts.clean_history_session_state import clean_history_session_state")
'''
        cleanup_script.write_text(cleanup_content)
        cleanup_script.chmod(0o755)
        print("  ✓ Created session state cleanup script")
        return True

    def cleanup_files(self) -> bool:
        """Remove backup files and clean cache"""
        print("\n🗑️ Cleaning up files...")

        # Remove history_tab.py.backup if it exists
        backup_file = self.project_root / "src/ui/components/history_tab.py.backup"
        if backup_file.exists():
            backup_file.unlink()
            print(f"  ✓ Removed {backup_file.name}")

        # Clean Python cache
        cache_patterns = ["**/__pycache__", "**/*.pyc", "**/*.pyo"]

        for pattern in cache_patterns:
            for path in self.project_root.glob(pattern):
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink(missing_ok=True)

        print("  ✓ Cleaned Python cache files")
        return True

    def verify_removal(self) -> tuple[bool, list[str]]:
        """Verify that all references have been removed"""
        print("\n✅ Verifying removal...")

        remaining_refs = []

        # Check for HistoryTab references
        patterns = [
            r"HistoryTab",
            r"history_tab(?!\.py\.backup)",
            r'"history":\s*{',
            r"'history':\s*{",
        ]

        src_dir = self.project_root / "src"
        for py_file in src_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                for pattern in patterns:
                    if re.search(pattern, content):
                        # Filter out non-UI history references
                        if not any(
                            skip in str(py_file)
                            for skip in [
                                "history_entry",
                                "history_file",
                                "rate_limit_history",
                                "retry_history",
                                "_add_history",
                            ]
                        ):
                            matches = re.findall(pattern, content)
                            for match in matches:
                                if "history_" not in match or "history_tab" in match:
                                    remaining_refs.append(f"{py_file}: {match}")
            except Exception as e:
                self.errors.append(f"Error checking {py_file}: {e}")

        if not remaining_refs:
            print("  ✓ No History Tab references found")
            return True, []
        print(f"  ⚠ Found {len(remaining_refs)} possible remaining references:")
        for ref in remaining_refs[:5]:  # Show first 5
            print(f"    - {ref}")
        return False, remaining_refs

    def test_syntax(self) -> bool:
        """Test Python syntax of modified files"""
        print("\n🧪 Testing Python syntax...")

        file_path = self.project_root / "src/ui/tabbed_interface.py"
        try:
            import py_compile

            py_compile.compile(str(file_path), doraise=True)
            print(f"  ✓ Syntax valid: {file_path.name}")
            return True
        except py_compile.PyCompileError as e:
            self.errors.append(f"Syntax error in {file_path.name}: {e}")
            print(f"  ✗ Syntax error in {file_path.name}")
            return False

    def generate_report(self):
        """Generate a summary report"""
        print("\n" + "=" * 60)
        print("📊 REMOVAL REPORT")
        print("=" * 60)

        print(f"\n📁 Backup Location: {self.backup_dir}")
        print(f"🔧 Modifications: {len(self.modifications)}")

        if self.modifications:
            print("\nModifications made:")
            for mod in self.modifications:
                print(f"  • {mod}")

        if self.errors:
            print(f"\n⚠️ Errors encountered: {len(self.errors)}")
            for error in self.errors:
                print(f"  • {error}")

        print("\n📝 Next Steps:")
        print("  1. Run: streamlit run src/main.py")
        print("  2. Verify all tabs work correctly")
        print(f"  3. If issues occur, run: {self.backup_dir}/rollback.sh")

    def run(self) -> bool:
        """Execute the complete removal process"""
        print("🚀 Starting History Tab Removal Process")
        print("=" * 60)

        steps = [
            ("Creating backups", self.create_backups),
            ("Modifying code", self.remove_from_tabbed_interface),
            ("Creating cleanup scripts", self.clean_session_state_references),
            ("Cleaning files", self.cleanup_files),
            ("Testing syntax", self.test_syntax),
        ]

        for step_name, step_func in steps:
            if not step_func():
                print(f"\n❌ Failed at step: {step_name}")
                if self.errors:
                    print("Errors:")
                    for error in self.errors:
                        print(f"  - {error}")
                return False

        # Final verification
        success, refs = self.verify_removal()

        self.generate_report()

        return success and not self.errors


def main():
    """Main entry point"""
    project_root = Path("/Users/chrislehnen/Projecten/Definitie-app")

    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)

    remover = HistoryTabRemover(project_root)

    try:
        if remover.run():
            print("\n✅ History Tab successfully removed!")
            sys.exit(0)
        else:
            print(
                "\n⚠️ Removal completed with warnings. Please review the report above."
            )
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print(f"Rollback script available at: {remover.backup_dir}/rollback.sh")
        sys.exit(1)


if __name__ == "__main__":
    main()
