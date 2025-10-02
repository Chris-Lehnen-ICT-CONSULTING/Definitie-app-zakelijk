#!/usr/bin/env python3
"""
Fix Broken Links Script
Automatisch repareren van gebroken links na vertaaloperatie
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path


class LinkFixer:
    def __init__(self, base_dir: str = "docs"):
        self.base_dir = Path(base_dir)
        self.fixes_applied = []
        self.manual_review_needed = []

        # Known link mappings for common issues
        self.link_mappings = {
            # EPIC-CFR werd EPIC-010
            "./epics/EPIC-CFR.md": "./epics/EPIC-010-context-flow-refactoring.md",
            "../epics/EPIC-CFR.md": "../epics/EPIC-010-context-flow-refactoring.md",
            # Moved to archief
            "../TARGET_ARCHITECTURE.md": "../architectuur/TECHNICAL_ARCHITECTURE.md",
            "../CURRENT_STATE.md": "../architectuur/ENTERPRISE_ARCHITECTURE.md",
            "../CFR-CONSOLIDATED-REFACTOR-PLAN.md": "../archief/2025-09-architectuur-consolidatie/cfr-documents/CFR-CONSOLIDATED-REFACTOR-PLAN.md",
            "../SOLUTION_ARCHITECTURE.md": "../architectuur/SOLUTION_ARCHITECTURE.md",
            "../SA.md": "../architectuur/SOLUTION_ARCHITECTURE.md",
            "../EA-CFR.md": "../archief/2025-09-architectuur-consolidatie/cfr-documents/EA-CFR.md",
            "../SA-CFR.md": "../archief/2025-09-architectuur-consolidatie/cfr-documents/SA-CFR.md",
            # Story references
            "../../stories/MASTER-EPICS-USER-STORIES.md#epic-cfr-context-flow-refactoring": "../../stories/MASTER-EPICS-USER-STORIES.md#epic-010-context-flow-refactoring",
            # Fix encoded spaces
            "../architectuur/definitie%20service/": "../architectuur/definitie-service/",
        }

    def find_all_markdown_files(self) -> list[Path]:
        """Find all markdown files in docs directory"""
        return list(self.base_dir.rglob("*.md"))

    def extract_links(self, content: str) -> list[tuple[str, str, int]]:
        """Extract all markdown links from content with line numbers"""
        links = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Find markdown links [text](url)
            matches = re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", line)
            for match in matches:
                link_text = match.group(1)
                link_url = match.group(2)
                links.append((link_text, link_url, i))

        return links

    def resolve_link(self, source_file: Path, link_path: str) -> Path:
        """Resolve a link relative to source file"""
        # Skip external links
        if link_path.startswith("http"):
            return None

        # Skip anchors
        if link_path.startswith("#"):
            return None

        # Remove anchor from path
        clean_path = link_path.split("#")[0] if "#" in link_path else link_path

        # Resolve relative paths
        if clean_path.startswith("../"):
            target = (source_file.parent / clean_path).resolve()
        elif clean_path.startswith("/"):
            target = Path(clean_path[1:])
        elif clean_path.startswith("./"):
            target = source_file.parent / clean_path[2:]
        else:
            target = source_file.parent / clean_path

        return target

    def find_alternative_path(self, broken_path: str, source_file: Path) -> str:
        """Try to find alternative path for broken link"""
        # Check known mappings first
        if broken_path in self.link_mappings:
            return self.link_mappings[broken_path]

        # Extract filename from broken path
        filename = Path(broken_path).name

        # Search for file with same name
        candidates = list(self.base_dir.rglob(filename))

        if len(candidates) == 1:
            # Calculate relative path from source to target
            target = candidates[0]
            try:
                rel_path = os.path.relpath(target, source_file.parent)
                # Preserve anchor if present
                if "#" in broken_path:
                    anchor = broken_path.split("#")[1]
                    rel_path = f"{rel_path}#{anchor}"
                return rel_path
            except ValueError:
                return None

        # Try searching for similar filenames
        base_name = filename.replace(".md", "")
        similar = list(self.base_dir.rglob(f"*{base_name}*.md"))

        if len(similar) == 1:
            target = similar[0]
            try:
                rel_path = os.path.relpath(target, source_file.parent)
                if "#" in broken_path:
                    anchor = broken_path.split("#")[1]
                    rel_path = f"{rel_path}#{anchor}"
                return rel_path
            except ValueError:
                return None

        return None

    def fix_file(self, file_path: Path, dry_run: bool = False) -> int:
        """Fix broken links in a single file"""
        content = file_path.read_text()
        original_content = content
        fixes = 0

        links = self.extract_links(content)

        for link_text, link_url, line_num in links:
            # Skip external links
            if link_url.startswith("http") or link_url.startswith("#"):
                continue

            # Check if link is broken
            target = self.resolve_link(file_path, link_url)
            if target and not target.exists():
                # Try to find alternative
                alternative = self.find_alternative_path(link_url, file_path)

                if alternative:
                    old_link = f"[{link_text}]({link_url})"
                    new_link = f"[{link_text}]({alternative})"
                    content = content.replace(old_link, new_link)

                    self.fixes_applied.append(
                        {
                            "file": str(file_path),
                            "line": line_num,
                            "old": link_url,
                            "new": alternative,
                            "text": link_text,
                        }
                    )
                    fixes += 1
                else:
                    self.manual_review_needed.append(
                        {
                            "file": str(file_path),
                            "line": line_num,
                            "link": link_url,
                            "text": link_text,
                        }
                    )

        # Write changes if not dry run and there were fixes
        if fixes > 0 and not dry_run:
            # Create backup
            backup_path = file_path.with_suffix(".md.linkfix_backup")
            backup_path.write_text(original_content)

            # Write fixed content
            file_path.write_text(content)

        return fixes

    def run(self, dry_run: bool = False):
        """Run link fixing on all markdown files"""
        print("=" * 80)
        print("BROKEN LINK FIXER")
        print("=" * 80)
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"Scanning: {self.base_dir}")
        print()

        md_files = self.find_all_markdown_files()
        total_fixes = 0
        files_fixed = 0

        for md_file in md_files:
            fixes = self.fix_file(md_file, dry_run)
            if fixes > 0:
                total_fixes += fixes
                files_fixed += 1
                print(
                    f"{'[DRY RUN] Would fix' if dry_run else 'Fixed'} {fixes} links in {md_file}"
                )

        # Generate report
        self.generate_report(dry_run, total_fixes, files_fixed)

    def generate_report(self, dry_run: bool, total_fixes: int, files_fixed: int):
        """Generate detailed report of fixes"""
        print()
        print("=" * 80)
        print("LINK FIX REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print()

        print("STATISTICS")
        print("-" * 40)
        print(f"Files processed: {len(list(self.base_dir.rglob('*.md')))}")
        print(f"Files with broken links: {files_fixed}")
        print(f"Links fixed: {total_fixes}")
        print(f"Manual review needed: {len(self.manual_review_needed)}")
        print()

        if self.fixes_applied:
            print("AUTOMATIC FIXES APPLIED")
            print("-" * 40)
            for fix in self.fixes_applied[:20]:  # Show first 20
                print(f"- {fix['file']}:{fix['line']}")
                print(f"  OLD: {fix['old']}")
                print(f"  NEW: {fix['new']}")
                print()

        if self.manual_review_needed:
            print("MANUAL REVIEW NEEDED")
            print("-" * 40)
            for issue in self.manual_review_needed[:20]:  # Show first 20
                print(f"- {issue['file']}:{issue['line']}")
                print(f"  BROKEN: [{issue['text']}]({issue['link']})")
                print()

        # Save detailed report
        report_file = (
            f"logs/link_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        os.makedirs("logs", exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "mode": "dry_run" if dry_run else "live",
                    "statistics": {
                        "files_processed": len(list(self.base_dir.rglob("*.md"))),
                        "files_fixed": files_fixed,
                        "links_fixed": total_fixes,
                        "manual_review": len(self.manual_review_needed),
                    },
                    "fixes_applied": self.fixes_applied,
                    "manual_review_needed": self.manual_review_needed,
                },
                f,
                indent=2,
            )

        print(f"Detailed report saved to: {report_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fix broken links in documentation")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying"
    )
    args = parser.parse_args()

    fixer = LinkFixer()
    fixer.run(dry_run=args.dry_run)
