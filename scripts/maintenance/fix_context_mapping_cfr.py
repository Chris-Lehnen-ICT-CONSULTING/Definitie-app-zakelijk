#!/usr/bin/env python3
"""
QUICK FIX SCRIPT - CFR Context Mapping Issue
Temporary patch for Epic CFR Story CFR.1

This script patches the context mapping issue where UI context fields
are not passed to the AI prompts. This is a TEMPORARY fix until the
full refactoring is complete.

Usage:
    python scripts/fix_context_mapping_cfr.py [--check|--apply|--rollback]

Author: Business Analyst / Development Team
Date: 2025-09-04
Related: Epic CFR, Bug CFR-BUG-001
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path


class ContextMappingFixer:
    """Quick fix for context mapping issue in prompt_service_v2.py."""

    def __init__(self):
        """Initialize fixer with paths."""
        self.project_root = Path(__file__).parent.parent
        self.target_file = (
            self.project_root / "src/services/prompts/prompt_service_v2.py"
        )
        self.backup_file = self.target_file.with_suffix(".py.backup_cfr")

    def check_issue(self) -> bool:
        """Check if the context mapping issue exists."""
        if not self.target_file.exists():
            print(f"❌ Target file not found: {self.target_file}")
            return False

        content = self.target_file.read_text()

        # Check for the problematic code pattern
        issues = []

        # Issue 1: Context fields not extracted
        if 'getattr(request, "organisatorische_context", None)' in content:
            if (
                'extend_unique(getattr(request, "organisatorische_context", None)'
                in content
            ):
                print("✅ Organisatorische context mapping appears to be present")
            else:
                issues.append("organisatorische_context not properly mapped")
        else:
            issues.append("organisatorische_context field not accessed")

        # Issue 2: Check if context is actually used
        if 'base_context["organisatorisch"]' in content:
            print("✅ Base context structure exists")
        else:
            issues.append("base_context structure missing")

        if issues:
            print(f"❌ Found {len(issues)} issues:")
            for issue in issues:
                print(f"   - {issue}")
            return True
        else:
            print("✅ No context mapping issues detected")
            return False

    def create_backup(self) -> bool:
        """Create backup of the original file."""
        try:
            shutil.copy2(self.target_file, self.backup_file)
            print(f"✅ Backup created: {self.backup_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            return False

    def apply_fix(self) -> bool:
        """Apply the context mapping fix."""
        if not self.create_backup():
            return False

        try:
            content = self.target_file.read_text()

            # Find the _convert_request_to_context method
            method_start = content.find("def _convert_request_to_context(")
            if method_start == -1:
                print("❌ Could not find _convert_request_to_context method")
                return False

            # Find the end of the method (next method or end of class)
            next_method = content.find("\n    def ", method_start + 1)
            method_end = next_method if next_method != -1 else len(content)

            # Extract the method
            method_content = content[method_start:method_end]

            # Create the fixed version
            fixed_method = '''    def _convert_request_to_context(
        self, request: GenerationRequest, extra_context: dict[str, Any] | None = None
    ) -> EnrichedContext:
        """Convert V2 GenerationRequest to EnrichedContext for existing prompt system.

        FIXED by CFR Quick Fix Script - Properly maps UI context fields.
        """

        # Build base context from request (CFR FIX: Complete mapping with dedupe)
        base_context: dict[str, list[str]] = {
            "organisatorisch": [],
            "juridisch": [],
            "wettelijk": [],
            "domein": [],
        }

        def extend_unique(values: list[str] | str | None, into: list[str]) -> None:
            """Helper to add unique values to a list."""
            if not values:
                return
            # Handle both string and list inputs
            if isinstance(values, str):
                values = [values]
            seen = set(into)
            for v in values:
                if v and v not in seen:
                    into.append(v)
                    seen.add(v)

        # CFR FIX: Properly extract and map UI context fields
        # These fields come from the UI context selectors
        if hasattr(request, "organisatorische_context") and request.organisatorische_context:
            extend_unique(request.organisatorische_context, base_context["organisatorisch"])
            logger.debug(f"CFR FIX: Added organisatorische_context: {request.organisatorische_context}")

        if hasattr(request, "juridische_context") and request.juridische_context:
            extend_unique(request.juridische_context, base_context["juridisch"])
            logger.debug(f"CFR FIX: Added juridische_context: {request.juridische_context}")

        if hasattr(request, "wettelijke_basis") and request.wettelijke_basis:
            extend_unique(request.wettelijke_basis, base_context["wettelijk"])
            logger.debug(f"CFR FIX: Added wettelijke_basis: {request.wettelijke_basis}")

        # Legacy field support (lower priority than UI fields)
        if request.domein and not base_context["domein"]:
            extend_unique([request.domein], base_context["domein"])

        # Use legacy vrije context ONLY if the new fields are empty
        if (
            not any(
                [
                    base_context["organisatorisch"],
                    base_context["juridisch"],
                    base_context["wettelijk"],
                ]
            )
            and request.context
        ):
            extend_unique([request.context], base_context["organisatorisch"])
            logger.debug("CFR FIX: Falling back to legacy context field")

        # CRITICAL FIX: Preserve context_dict from extra_context
        # This fixes the voorbeelden dictionary regression
        if extra_context and "context_dict" in extra_context:
            context_dict = extra_context["context_dict"]
            logger.debug(
                f"CFR FIX: Preserving context_dict with keys: {list(context_dict.keys())}"
            )

            # Merge context_dict into base_context (context_dict has priority)
            for key, value in context_dict.items():
                if isinstance(value, list) and value:  # Only add non-empty lists
                    base_context[key] = value
                    logger.debug(f"CFR FIX: Merged context_dict[{key}] = {value}")

        # Log final context for debugging
        logger.info(f"CFR FIX: Final context mapping:")
        for key, values in base_context.items():
            if values:
                logger.info(f"  {key}: {values}")

        # Create sources list (empty for now, could be extended)
        sources = []

        # Build metadata with ontological category
        metadata = {
            "ontologische_categorie": request.ontologische_categorie,
            "semantic_category": request.ontologische_categorie,  # For template module compatibility
            "request_id": request.id,
            "actor": request.actor,'''

            # Continue with the rest of the method
            rest_start = method_content.find("        # Build metadata")
            if rest_start == -1:
                rest_start = method_content.find("        metadata = {")

            if rest_start != -1:
                # Skip to after the metadata section
                rest_start = method_content.find("        return EnrichedContext(")
                if rest_start != -1:
                    rest_of_method = method_content[rest_start:]
                    fixed_method += "\n" + rest_of_method
                else:
                    # Add default return
                    fixed_method += """
        }

        return EnrichedContext(
            base_context=base_context,
            sources=sources,
            metadata=metadata
        )
"""

            # Replace the method in the content
            new_content = content[:method_start] + fixed_method + content[method_end:]

            # Add import for logger if not present
            if "import logging" not in new_content:
                import_pos = new_content.find('"""')
                if import_pos != -1:
                    # Find end of docstring
                    import_pos = new_content.find('"""', import_pos + 3) + 3
                    new_content = (
                        new_content[:import_pos]
                        + "\n\nimport logging"
                        + new_content[import_pos:]
                    )

            if "logger = logging.getLogger(__name__)" not in new_content:
                # Add after imports
                import_end = new_content.rfind("from services.web_lookup")
                if import_end != -1:
                    line_end = new_content.find("\n", import_end)
                    new_content = (
                        new_content[: line_end + 1]
                        + "\nlogger = logging.getLogger(__name__)\n"
                        + new_content[line_end + 1 :]
                    )

            # Write the fixed content
            self.target_file.write_text(new_content)
            print(f"✅ Fix applied to {self.target_file}")
            print("✅ Context fields will now be properly mapped to prompts")

            # Log the fix
            self._log_fix_application()

            return True

        except Exception as e:
            print(f"❌ Failed to apply fix: {e}")
            self.rollback()
            return False

    def rollback(self) -> bool:
        """Rollback to the backup version."""
        if not self.backup_file.exists():
            print("❌ No backup file found to rollback")
            return False

        try:
            shutil.copy2(self.backup_file, self.target_file)
            print(f"✅ Rolled back to backup: {self.backup_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to rollback: {e}")
            return False

    def _log_fix_application(self):
        """Log that the fix was applied."""
        log_file = self.project_root / "docs/CFR-FIX-LOG.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_entry = f"""
## Fix Applied: {timestamp}

- **Script:** fix_context_mapping_cfr.py
- **Target:** src/services/prompts/prompt_service_v2.py
- **Issue:** Context fields not mapped from UI to prompts
- **Status:** TEMPORARY FIX - Full refactoring needed per Epic CFR
- **Backup:** {self.backup_file.name}

### Changes Made:
1. Fixed extraction of organisatorische_context from request
2. Fixed extraction of juridische_context from request
3. Fixed extraction of wettelijke_basis from request
4. Added proper type handling for string/list inputs
5. Added debug logging for context mapping

### Verification:
- Generate a definition with context fields selected
- Check debug output for "CFR FIX:" log entries
- Verify context appears in the AI prompt

"""

        if log_file.exists():
            content = log_file.read_text()
            content += log_entry
        else:
            content = "# CFR Context Fix Log\n\n" + log_entry

        log_file.write_text(content)
        print(f"✅ Fix logged to {log_file}")


def main():
    """Main entry point for the fix script."""
    parser = argparse.ArgumentParser(
        description="Quick fix for CFR context mapping issue"
    )
    parser.add_argument(
        "action",
        choices=["check", "apply", "rollback"],
        nargs="?",
        default="check",
        help="Action to perform (default: check)",
    )

    args = parser.parse_args()
    fixer = ContextMappingFixer()

    print(f"\n{'='*60}")
    print("CFR CONTEXT MAPPING QUICK FIX")
    print(f"{'='*60}\n")

    if args.action == "check":
        print("🔍 Checking for context mapping issues...\n")
        has_issues = fixer.check_issue()
        if has_issues:
            print("\n💡 Run with 'apply' to fix the issues:")
            print("   python scripts/fix_context_mapping_cfr.py apply")
        sys.exit(0 if not has_issues else 1)

    elif args.action == "apply":
        print("🔧 Applying context mapping fix...\n")
        success = fixer.apply_fix()
        if success:
            print("\n✅ Fix successfully applied!")
            print("⚠️  Remember: This is a TEMPORARY fix")
            print("📋 Full refactoring required per Epic CFR")
            print("\n🔄 To rollback if needed:")
            print("   python scripts/fix_context_mapping_cfr.py rollback")
        sys.exit(0 if success else 1)

    elif args.action == "rollback":
        print("🔄 Rolling back to backup...\n")
        success = fixer.rollback()
        if success:
            print("\n✅ Successfully rolled back")
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
