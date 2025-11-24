#!/usr/bin/env python3
"""
Traceability Update Script for Justice Documentation
Ensures all cross-references and dependencies are valid and complete
"""

import json
import logging
import re
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/traceability.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of documentation"""

    EPIC = "epic"
    STORY = "story"
    REQUIREMENT = "requirement"
    UNKNOWN = "unknown"


class LinkStatus(Enum):
    """Status of document links"""

    VALID = "valid"
    BROKEN = "broken"
    ORPHANED = "orphaned"
    CIRCULAR = "circular"


@dataclass
class Document:
    """Represents a documentation file"""

    path: Path
    doc_id: str
    doc_type: DocumentType
    title: str = ""
    epic_id: str | None = None
    references_to: set[str] = field(default_factory=set)
    referenced_by: set[str] = field(default_factory=set)
    dependencies: set[str] = field(default_factory=set)
    status: str = ""


@dataclass
class TraceabilityIssue:
    """Represents a traceability issue"""

    doc_id: str
    issue_type: str
    description: str
    severity: str  # HIGH, MEDIUM, LOW
    suggested_fix: str


@dataclass
class TraceabilityReport:
    """Complete traceability analysis report"""

    total_documents: int
    valid_links: int
    broken_links: int
    orphaned_stories: int
    circular_dependencies: int
    issues: list[TraceabilityIssue]
    traceability_matrix: dict[str, dict[str, list[str]]]
    fixes_applied: int


class TraceabilityAnalyzer:
    """Analyzes and fixes traceability in documentation"""

    def __init__(self, dry_run: bool = False, backup: bool = True):
        self.dry_run = dry_run
        self.backup = backup
        self.documents: dict[str, Document] = {}
        self.issues: list[TraceabilityIssue] = []
        self.stats = {
            "files_analyzed": 0,
            "links_fixed": 0,
            "orphans_assigned": 0,
            "dependencies_added": 0,
            "errors": [],
        }

        # Epic mapping for orphaned stories
        self.epic_mapping = {
            "generation": "EPIC-001",  # Basis Definitie Generatie
            "validation": "EPIC-002",  # Kwaliteitstoetsing
            "enrichment": "EPIC-003",  # Content Verrijking
            "ui": "EPIC-004",  # User Interface
            "export": "EPIC-005",  # Export & Import
            "security": "EPIC-006",  # Beveiliging & Auth
            "performance": "EPIC-007",  # Prestaties & Scaling
            "advanced": "EPIC-009",  # Advanced Features
            "refactor": "EPIC-010",  # Context Flow Refactoring
        }

        # Create backup directory if needed
        if self.backup and not self.dry_run:
            self.backup_dir = (
                Path("backups")
                / f'traceability_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            )
            self.backup_dir.mkdir(parents=True, exist_ok=True)

    def extract_document_id(self, file_path: Path) -> str | None:
        """Extract document ID from filename"""
        patterns = [
            r"(EPIC-\d{3})",
            r"(US-\d{3})",
            r"(REQ-\d{3})",
        ]

        for pattern in patterns:
            match = re.search(pattern, file_path.name)
            if match:
                return match.group(1)

        return None

    def determine_document_type(self, file_path: Path) -> DocumentType:
        """Determine document type from filename"""
        if "EPIC-" in file_path.name:
            return DocumentType.EPIC
        if "US-" in file_path.name:
            return DocumentType.STORY
        if "REQ-" in file_path.name:
            return DocumentType.REQUIREMENT
        return DocumentType.UNKNOWN

    def extract_references(self, content: str) -> set[str]:
        """Extract all document references from content"""
        references = set()

        # Patterns for different reference types
        patterns = [
            r"EPIC-\d{3}",
            r"US-\d{3}",
            r"REQ-\d{3}",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            references.update(matches)

        return references

    def extract_epic_assignment(self, content: str) -> str | None:
        """Extract epic assignment from story content"""
        # Look for epic assignment patterns
        patterns = [
            r"Epic:\s*(EPIC-\d{3})",
            r"Parent Epic:\s*(EPIC-\d{3})",
            r"Belongs to:\s*(EPIC-\d{3})",
            r"Part of:\s*(EPIC-\d{3})",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def extract_dependencies(self, content: str) -> set[str]:
        """Extract dependencies from content"""
        dependencies = set()

        # Look for dependency section
        dep_section = re.search(
            r"##\s*(?:Dependencies|Afhankelijkheden)(.*?)(?:##|\Z)",
            content,
            re.IGNORECASE | re.DOTALL,
        )

        if dep_section:
            dep_text = dep_section.group(1)
            # Extract document IDs from dependency section
            patterns = [r"EPIC-\d{3}", r"US-\d{3}", r"REQ-\d{3}"]
            for pattern in patterns:
                matches = re.findall(pattern, dep_text)
                dependencies.update(matches)

        return dependencies

    def extract_title(self, content: str) -> str:
        """Extract document title from content"""
        # Look for H1 header
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()
        return ""

    def analyze_file(self, file_path: Path) -> Document | None:
        """Analyze a single documentation file"""
        try:
            doc_id = self.extract_document_id(file_path)
            if not doc_id:
                return None

            doc_type = self.determine_document_type(file_path)

            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            doc = Document(
                path=file_path,
                doc_id=doc_id,
                doc_type=doc_type,
                title=self.extract_title(content),
                epic_id=(
                    self.extract_epic_assignment(content)
                    if doc_type == DocumentType.STORY
                    else None
                ),
                references_to=self.extract_references(content),
                dependencies=self.extract_dependencies(content),
            )

            # Extract status if present
            status_match = re.search(r"Status:\s*(\w+)", content, re.IGNORECASE)
            if status_match:
                doc.status = status_match.group(1)

            self.documents[doc_id] = doc
            self.stats["files_analyzed"] += 1

            return doc

        except Exception as e:
            error_msg = f"Error analyzing {file_path}: {e!s}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return None

    def build_reverse_references(self):
        """Build reverse reference mappings"""
        for doc_id, doc in self.documents.items():
            for ref_id in doc.references_to:
                if ref_id in self.documents:
                    self.documents[ref_id].referenced_by.add(doc_id)

    def check_broken_links(self):
        """Check for broken document references"""
        for doc_id, doc in self.documents.items():
            for ref_id in doc.references_to:
                if ref_id not in self.documents:
                    self.issues.append(
                        TraceabilityIssue(
                            doc_id=doc_id,
                            issue_type="broken_link",
                            description=f"References non-existent document {ref_id}",
                            severity="HIGH",
                            suggested_fix=f"Remove reference to {ref_id} or create the document",
                        )
                    )

    def check_orphaned_stories(self):
        """Check for user stories not assigned to any epic"""
        for doc_id, doc in self.documents.items():
            if doc.doc_type == DocumentType.STORY and not doc.epic_id:
                # Try to determine epic based on story content
                suggested_epic = self.suggest_epic_for_story(doc)

                self.issues.append(
                    TraceabilityIssue(
                        doc_id=doc_id,
                        issue_type="orphaned_story",
                        description=f"User story {doc_id} is not assigned to any epic",
                        severity="MEDIUM",
                        suggested_fix=f"Assign to {suggested_epic} based on content analysis",
                    )
                )

    def suggest_epic_for_story(self, story: Document) -> str:
        """Suggest an epic for an orphaned story based on content"""

        # Read story content
        try:
            with open(story.path, encoding="utf-8") as f:
                content = f.read().lower()
        except Exception:
            return "EPIC-001"  # Default to first epic

        # Keywords for each epic
        epic_keywords = {
            "EPIC-001": [
                "generatie",
                "generate",
                "definition",
                "definitie",
                "create",
                "maken",
            ],
            "EPIC-002": [
                "validatie",
                "validation",
                "toets",
                "check",
                "quality",
                "kwaliteit",
            ],
            "EPIC-003": ["verrijk", "enrich", "web", "lookup", "external", "source"],
            "EPIC-004": ["ui", "interface", "gebruiker", "user", "frontend", "display"],
            "EPIC-005": ["export", "import", "save", "load", "file", "bestand"],
            "EPIC-006": [
                "security",
                "beveiliging",
                "auth",
                "login",
                "permission",
                "role",
            ],
            "EPIC-007": [
                "performance",
                "prestatie",
                "scale",
                "speed",
                "optimize",
                "cache",
            ],
            "EPIC-009": ["advanced", "geavanceerd", "feature", "complex", "special"],
            "EPIC-010": ["refactor", "context", "flow", "architecture", "restructure"],
        }

        # Count keyword matches for each epic
        scores = {}
        for epic_id, keywords in epic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > 0:
                scores[epic_id] = score

        # Return epic with highest score, or default to EPIC-001
        if scores:
            return max(scores, key=scores.get)
        # Try to guess based on story number
        story_num = int(re.search(r"US-(\d+)", story.doc_id).group(1))
        if story_num <= 10:
            return "EPIC-001"
        if story_num <= 20:
            return "EPIC-002"
        if story_num <= 30:
            return "EPIC-003"
        if story_num <= 35:
            return "EPIC-004"
        return "EPIC-001"

    def check_circular_dependencies(self):
        """Check for circular dependency chains"""

        def find_cycles(
            doc_id: str, visited: set[str], path: list[str]
        ) -> list[str] | None:
            """DFS to find circular dependencies"""
            if doc_id in path:
                cycle_start = path.index(doc_id)
                return [*path[cycle_start:], doc_id]

            if doc_id in visited:
                return None

            visited.add(doc_id)
            path.append(doc_id)

            if doc_id in self.documents:
                for dep_id in self.documents[doc_id].dependencies:
                    cycle = find_cycles(dep_id, visited, path.copy())
                    if cycle:
                        return cycle

            return None

        visited_global = set()
        for doc_id in self.documents:
            if doc_id not in visited_global:
                cycle = find_cycles(doc_id, set(), [])
                if cycle:
                    self.issues.append(
                        TraceabilityIssue(
                            doc_id=doc_id,
                            issue_type="circular_dependency",
                            description=f"Circular dependency detected: {' -> '.join(cycle)}",
                            severity="HIGH",
                            suggested_fix="Remove one of the dependencies to break the cycle",
                        )
                    )
                    visited_global.update(cycle)

    def check_missing_dependencies(self):
        """Check for missing but implied dependencies"""
        for doc_id, doc in self.documents.items():
            if doc.doc_type == DocumentType.STORY:
                # Stories should depend on their epic
                if doc.epic_id and doc.epic_id not in doc.dependencies:
                    self.issues.append(
                        TraceabilityIssue(
                            doc_id=doc_id,
                            issue_type="missing_dependency",
                            description=f"Story {doc_id} should list its epic {doc.epic_id} as dependency",
                            severity="LOW",
                            suggested_fix=f"Add {doc.epic_id} to dependencies section",
                        )
                    )

                # Check for implied dependencies based on numbering
                story_num = int(re.search(r"US-(\d+)", doc_id).group(1))
                if story_num > 1:
                    prev_story = f"US-{story_num-1:03d}"
                    if (
                        prev_story in self.documents
                        and prev_story not in doc.dependencies
                    ):
                        # Check if they're in the same epic
                        prev_doc = self.documents[prev_story]
                        if prev_doc.epic_id == doc.epic_id:
                            self.issues.append(
                                TraceabilityIssue(
                                    doc_id=doc_id,
                                    issue_type="possible_dependency",
                                    description=f"Story {doc_id} might depend on previous story {prev_story}",
                                    severity="LOW",
                                    suggested_fix=f"Consider adding {prev_story} to dependencies if there's a logical dependency",
                                )
                            )

    def build_traceability_matrix(self) -> dict[str, dict[str, list[str]]]:
        """Build a complete traceability matrix"""
        matrix = {}

        # Group documents by type
        epics = [d for d in self.documents.values() if d.doc_type == DocumentType.EPIC]
        stories = [
            d for d in self.documents.values() if d.doc_type == DocumentType.STORY
        ]
        requirements = [
            d for d in self.documents.values() if d.doc_type == DocumentType.REQUIREMENT
        ]

        # Epic to Stories mapping
        for epic in epics:
            epic_stories = [s.doc_id for s in stories if s.epic_id == epic.doc_id]
            epic_reqs = [
                r.doc_id for r in requirements if epic.doc_id in r.references_to
            ]

            matrix[epic.doc_id] = {
                "title": epic.title,
                "stories": epic_stories,
                "requirements": epic_reqs,
                "dependencies": list(epic.dependencies),
                "referenced_by": list(epic.referenced_by),
            }

        return matrix

    def fix_orphaned_story(self, story: Document, suggested_epic: str) -> bool:
        """Fix an orphaned story by assigning it to an epic"""

        if self.dry_run:
            logger.info(f"[DRY RUN] Would assign {story.doc_id} to {suggested_epic}")
            return False

        try:
            # Backup file
            if self.backup:
                backup_path = self.backup_dir / story.path.relative_to(
                    story.path.parents[2]
                )
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(story.path, backup_path)

            # Read content
            with open(story.path, encoding="utf-8") as f:
                content = f.read()

            # Check if epic assignment already exists
            if re.search(r"Epic:\s*EPIC-\d{3}", content, re.IGNORECASE):
                # Update existing assignment
                content = re.sub(
                    r"Epic:\s*EPIC-\d{3}",
                    f"Epic: {suggested_epic}",
                    content,
                    flags=re.IGNORECASE,
                )
            else:
                # Add epic assignment after title
                title_match = re.search(r"^(#\s+.+)$", content, re.MULTILINE)
                if title_match:
                    insert_pos = title_match.end()
                    epic_section = f"\n\n**Epic:** {suggested_epic}"
                    content = content[:insert_pos] + epic_section + content[insert_pos:]

            # Add to dependencies if not present
            if (
                "afhankelijkheden" not in content.lower()
                and "dependencies" not in content.lower()
            ):
                # Add dependencies section
                dep_section = (
                    f"\n\n## Afhankelijkheden\n\n- {suggested_epic}: Parent epic\n"
                )
                content += dep_section

            # Update change log
            if "wijzigingslog" in content.lower() or "change log" in content.lower():
                today = datetime.now().strftime("%Y-%m-%d")
                new_entry = f"| {today} | 2.2 | Toegewezen aan {suggested_epic} |"

                content = re.sub(
                    r"(\| \d{4}-\d{2}-\d{2} \| [\d.]+ \| [^|]+ \|)(\n)",
                    r"\1\n" + new_entry + r"\2",
                    content,
                    count=1,
                )

            # Write updated content
            with open(story.path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Assigned {story.doc_id} to {suggested_epic}")
            self.stats["orphans_assigned"] += 1
            return True

        except Exception as e:
            error_msg = f"Error fixing orphaned story {story.doc_id}: {e!s}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return False

    def fix_broken_link(self, doc: Document, broken_ref: str) -> bool:
        """Fix or remove a broken link"""

        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would fix broken link to {broken_ref} in {doc.doc_id}"
            )
            return False

        try:
            # Backup file
            if self.backup:
                backup_path = self.backup_dir / doc.path.relative_to(
                    doc.path.parents[2]
                )
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(doc.path, backup_path)

            # Read content
            with open(doc.path, encoding="utf-8") as f:
                content = f.read()

            # Comment out broken references instead of removing
            content = re.sub(
                rf"\b{re.escape(broken_ref)}\b",
                f"<!-- BROKEN LINK: {broken_ref} -->",
                content,
            )

            # Write updated content
            with open(doc.path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Fixed broken link to {broken_ref} in {doc.doc_id}")
            self.stats["links_fixed"] += 1
            return True

        except Exception as e:
            error_msg = f"Error fixing broken link in {doc.doc_id}: {e!s}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return False

    def add_missing_dependency(self, doc: Document, dependency: str) -> bool:
        """Add a missing dependency to a document"""

        if self.dry_run:
            logger.info(f"[DRY RUN] Would add dependency {dependency} to {doc.doc_id}")
            return False

        try:
            # Backup file
            if self.backup:
                backup_path = self.backup_dir / doc.path.relative_to(
                    doc.path.parents[2]
                )
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(doc.path, backup_path)

            # Read content
            with open(doc.path, encoding="utf-8") as f:
                content = f.read()

            # Find or create dependencies section
            dep_section = re.search(
                r"##\s*(?:Dependencies|Afhankelijkheden)(.*?)(?:##|\Z)",
                content,
                re.IGNORECASE | re.DOTALL,
            )

            if dep_section:
                # Add to existing section
                insert_pos = dep_section.end(1)
                new_dep = f"- {dependency}\n"
                content = content[:insert_pos] + new_dep + content[insert_pos:]
            else:
                # Create new section
                dep_section = f"\n\n## Afhankelijkheden\n\n- {dependency}\n"

                # Insert before test scenarios or at end
                test_match = re.search(
                    r"##\s*(?:Test|Scenario)", content, re.IGNORECASE
                )
                if test_match:
                    insert_pos = test_match.start()
                    content = content[:insert_pos] + dep_section + content[insert_pos:]
                else:
                    content += dep_section

            # Write updated content
            with open(doc.path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Added dependency {dependency} to {doc.doc_id}")
            self.stats["dependencies_added"] += 1
            return True

        except Exception as e:
            error_msg = f"Error adding dependency to {doc.doc_id}: {e!s}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return False

    def apply_fixes(self):
        """Apply automatic fixes for identified issues"""

        fixes_applied = 0

        for issue in self.issues:
            if issue.issue_type == "orphaned_story" and issue.severity in [
                "HIGH",
                "MEDIUM",
            ]:
                doc = self.documents[issue.doc_id]
                # Extract suggested epic from fix description
                epic_match = re.search(r"(EPIC-\d{3})", issue.suggested_fix)
                if epic_match:
                    if self.fix_orphaned_story(doc, epic_match.group(1)):
                        fixes_applied += 1

            elif issue.issue_type == "broken_link" and issue.severity == "HIGH":
                doc = self.documents[issue.doc_id]
                # Extract broken reference from description
                ref_match = re.search(r"((?:EPIC|US|REQ)-\d{3})", issue.description)
                if ref_match:
                    if self.fix_broken_link(doc, ref_match.group(1)):
                        fixes_applied += 1

            elif issue.issue_type == "missing_dependency" and issue.severity == "LOW":
                doc = self.documents[issue.doc_id]
                # Extract dependency from fix description
                dep_match = re.search(r"((?:EPIC|US|REQ)-\d{3})", issue.suggested_fix)
                if dep_match:
                    if self.add_missing_dependency(doc, dep_match.group(1)):
                        fixes_applied += 1

        return fixes_applied

    def generate_report(self) -> str:
        """Generate traceability analysis report"""

        # Count issue types
        issue_counts = defaultdict(int)
        for issue in self.issues:
            issue_counts[issue.issue_type] += 1

        # Count valid links
        valid_links = sum(
            len(doc.references_to)
            for doc in self.documents.values()
            if all(ref in self.documents for ref in doc.references_to)
        )

        report = []
        report.append("=" * 80)
        report.append("TRACEABILITY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        report.append("")

        # Statistics
        report.append("STATISTICS")
        report.append("-" * 40)
        report.append(f"Documents analyzed: {len(self.documents)}")
        report.append(f"Valid links: {valid_links}")
        report.append(f"Issues found: {len(self.issues)}")
        report.append("")

        # Issue breakdown
        report.append("ISSUE BREAKDOWN")
        report.append("-" * 40)
        for issue_type, count in sorted(issue_counts.items()):
            report.append(f"{issue_type}: {count}")
        report.append("")

        # Fixes applied
        if not self.dry_run:
            report.append("FIXES APPLIED")
            report.append("-" * 40)
            report.append(
                f"Orphaned stories assigned: {self.stats['orphans_assigned']}"
            )
            report.append(f"Broken links fixed: {self.stats['links_fixed']}")
            report.append(f"Dependencies added: {self.stats['dependencies_added']}")
            report.append("")

        # High severity issues
        high_severity = [i for i in self.issues if i.severity == "HIGH"]
        if high_severity:
            report.append("HIGH SEVERITY ISSUES")
            report.append("-" * 40)
            for issue in high_severity[:10]:
                report.append(f"- {issue.doc_id}: {issue.description}")
                report.append(f"  Fix: {issue.suggested_fix}")
            report.append("")

        # Traceability matrix summary
        matrix = self.build_traceability_matrix()
        report.append("TRACEABILITY MATRIX SUMMARY")
        report.append("-" * 40)
        for epic_id, data in sorted(matrix.items()):
            report.append(f"{epic_id}: {data['title']}")
            report.append(f"  Stories: {len(data['stories'])}")
            report.append(f"  Requirements: {len(data['requirements'])}")
            if data["dependencies"]:
                report.append(f"  Dependencies: {', '.join(data['dependencies'][:3])}")
        report.append("")

        # Orphaned stories
        orphaned = [
            d
            for d in self.documents.values()
            if d.doc_type == DocumentType.STORY and not d.epic_id
        ]
        if orphaned:
            report.append("ORPHANED USER STORIES")
            report.append("-" * 40)
            for story in orphaned[:10]:
                suggested = self.suggest_epic_for_story(story)
                report.append(f"- {story.doc_id}: {story.title}")
                report.append(f"  Suggested epic: {suggested}")
            report.append("")

        # Errors
        if self.stats["errors"]:
            report.append("ERRORS")
            report.append("-" * 40)
            for error in self.stats["errors"][:10]:
                report.append(f"- {error}")
            report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 40)

        health_score = 100
        health_score -= len(high_severity) * 5
        health_score -= issue_counts["orphaned_story"] * 2
        health_score -= issue_counts["broken_link"] * 3
        health_score = max(0, health_score)

        report.append(f"Traceability health score: {health_score}%")

        if health_score >= 90:
            report.append("Status: EXCELLENT - Documentation has strong traceability")
        elif health_score >= 70:
            report.append("Status: GOOD - Most traceability links are valid")
        else:
            report.append("Status: NEEDS IMPROVEMENT - Significant traceability issues")

        return "\n".join(report)

    def export_traceability_matrix(self, output_path: Path):
        """Export traceability matrix to JSON"""
        matrix = self.build_traceability_matrix()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(matrix, f, indent=2, ensure_ascii=False)

        logger.info(f"Traceability matrix exported to {output_path}")


def main():
    """Main execution function"""

    import argparse

    parser = argparse.ArgumentParser(
        description="Update and fix traceability in documentation"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip creating backups"
    )
    parser.add_argument(
        "--auto-fix", action="store_true", help="Automatically apply suggested fixes"
    )
    parser.add_argument(
        "--export-matrix", help="Export traceability matrix to JSON file"
    )

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = TraceabilityAnalyzer(dry_run=args.dry_run, backup=not args.no_backup)

    # Base path
    base_path = Path("/Users/chrislehnen/Projecten/Definitie-app/docs")

    print("=" * 80)
    print("TRACEABILITY UPDATE SCRIPT")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Backup: {'ENABLED' if not args.no_backup else 'DISABLED'}")
    print(f"Auto-fix: {'ENABLED' if args.auto_fix else 'DISABLED'}")
    print()

    # Analyze all documents
    directories = [
        ("epics", "EPIC-*.md"),
        ("stories", "US-*.md"),
        ("requirements", "REQ-*.md"),
    ]

    print("Analyzing documents...")
    for dir_name, pattern in directories:
        dir_path = base_path / dir_name
        if dir_path.exists():
            for file_path in sorted(dir_path.glob(pattern)):
                analyzer.analyze_file(file_path)

    # Build reverse references
    print("Building reference mappings...")
    analyzer.build_reverse_references()

    # Run checks
    print("Checking for issues...")
    analyzer.check_broken_links()
    analyzer.check_orphaned_stories()
    analyzer.check_circular_dependencies()
    analyzer.check_missing_dependencies()

    # Apply fixes if requested
    if args.auto_fix:
        print("Applying automatic fixes...")
        fixes_applied = analyzer.apply_fixes()
        print(f"Applied {fixes_applied} fixes")

    # Generate report
    report = analyzer.generate_report()

    # Save report
    report_path = (
        Path("logs")
        / f'traceability_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    )
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + report)
    print(f"\nReport saved to: {report_path}")

    # Export matrix if requested
    if args.export_matrix:
        matrix_path = Path(args.export_matrix)
        analyzer.export_traceability_matrix(matrix_path)
        print(f"Traceability matrix exported to: {matrix_path}")

    if args.dry_run:
        print("\nThis was a DRY RUN. No files were modified.")
        print("Run without --dry-run to apply changes.")

    return 0 if len(analyzer.stats["errors"]) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
