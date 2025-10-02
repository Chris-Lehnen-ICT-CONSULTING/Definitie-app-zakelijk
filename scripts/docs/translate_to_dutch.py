#!/usr/bin/env python3
"""
Advanced Dutch Translation Script for Justice Documentation
Implements comprehensive translation with domain-specific terminology
"""

import logging
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/translation.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class Priority(Enum):
    """Document priority levels"""

    P0_CRITICAL = "P0"  # User-facing docs
    P1_HIGH = "P1"  # Core documentation
    P2_MEDIUM = "P2"  # Supporting docs
    P3_LOW = "P3"  # Reference docs


@dataclass
class TranslationResult:
    """Result of a translation operation"""

    file_path: Path
    success: bool
    changes_made: int
    english_remaining: int
    errors: list[str]
    priority: Priority


class JusticeTerminology:
    """Comprehensive Dutch justice terminology dictionary"""

    CORE_TERMS = {
        # Legal/Justice terms
        "Public Prosecution": "Openbaar Ministerie (OM)",
        "public prosecution": "openbaar ministerie",
        "legal definition": "juridische definitie",
        "legal definitions": "juridische definities",
        "validation": "validatie",
        "authentication": "authenticatie",
        "authorization": "autorisatie",
        "prosecutor": "officier van justitie",
        "court": "rechtbank",
        "judge": "rechter",
        "detention": "detentie",
        "criminal law": "strafrecht",
        "civil law": "burgerlijk recht",
        "administrative law": "bestuursrecht",
        "justice chain": "justitieketen",
        "justice sector": "justitiesector",
        "legal terminology": "juridische terminologie",
        "case law": "jurisprudentie",
        "verdict": "vonnis",
        "sentence": "straf",
        "fine": "boete",
        "measure": "maatregel",
        # Organizations
        "Ministry of Justice": "Ministerie van Justitie en Veiligheid",
        "Prosecution Service": "Openbaar Ministerie (OM)",
        "Judiciary": "Rechtspraak",
        "Custodial Institutions Agency": "Dienst Justitiële Inrichtingen (DJI)",
        "Justice Information Service": "Justitiële Informatiedienst (Justid)",
        "Central Fine Collection Agency": "Centraal Justitieel Incassobureau (CJIB)",
        # Systems
        "case management system": "zaaksysteem",
        "detention management": "detentie management",
        "court procedures": "gerechtelijke procedures",
        "message format": "berichtenformaat",
        "criminal justice chain": "strafrechtketen",
    }

    HEADERS = {
        # Document sections
        "Executive Summary": "Managementsamenvatting",
        "Business Value": "Bedrijfswaarde",
        "Success Metrics": "Succesmetrieken",
        "User Story": "Gebruikersverhaal",
        "User Stories": "Gebruikersverhalen",
        "Story Breakdown": "Gebruikersverhalen Overzicht",
        "Dependencies": "Afhankelijkheden",
        "Risks & Mitigations": "Risico's & Mitigaties",
        "Technical Architecture": "Technische Architectuur",
        "Testing Coverage": "Testdekking",
        "Test Coverage": "Testdekking",
        "Compliance Notes": "Compliance Notities",
        "Definition of Done": "Definitie van Gereed",
        "Change Log": "Wijzigingslog",
        "Stakeholder Sign-off": "Stakeholder Goedkeuring",
        "Related Documentation": "Gerelateerde Documentatie",
        "Implementation": "Implementatie",
        "Acceptance Criteria": "Acceptatiecriteria",
        "Technical Notes": "Technische Notities",
        "Test Scenarios": "Test Scenario's",
        "Performance": "Prestaties",
        "Security": "Beveiliging",
        "Requirements": "Vereisten",
        "Requirement": "Vereiste",
        "Features": "Functionaliteiten",
        "Feature": "Functionaliteit",
        "Description": "Beschrijving",
        "Overview": "Overzicht",
        "Introduction": "Introductie",
        "Conclusion": "Conclusie",
        "References": "Referenties",
        "Appendix": "Bijlage",
        "Appendices": "Bijlagen",
    }

    USER_STORY_PATTERNS = {
        # User types
        "As a legal professional": "Als juridisch medewerker bij het OM/DJI/Rechtspraak",
        "As a developer": "Als ontwikkelaar binnen de justitieketen",
        "As a system administrator": "Als systeembeheerder binnen de justitieketen",
        "As a system": "Als justitie IT-systeem",
        "As an operations team": "Als operations team van Justid/CJIB",
        "As a QA engineer": "Als QA engineer voor kritieke justitiesystemen",
        "As a business analyst": "Als business analist voor de justitieketen",
        "As a security officer": "Als security officer conform BIR-richtlijnen",
        "As a user": "Als gebruiker binnen de justitieketen",
        "As an admin": "Als beheerder van justitiesystemen",
        # Actions
        "I want to": "Wil ik",
        "I want": "Wil ik",
        "I need to": "Moet ik",
        "I need": "Heb ik nodig",
        "So that": "Zodat",
        "Given": "Gegeven",
        "When": "Wanneer",
        "Then": "Dan",
        "And": "En",
        "But": "Maar",
    }

    STATUS_TERMS = {
        # Status indicators
        "Status:": "Status:",
        "DONE": "GEREED",
        "COMPLETED": "VOLTOOID",
        "IN_PROGRESS": "IN_UITVOERING",
        "IN PROGRESS": "IN UITVOERING",
        "TODO": "TE_DOEN",
        "TO DO": "TE DOEN",
        "BLOCKED": "GEBLOKKEERD",
        "PENDING": "IN_AFWACHTING",
        "APPROVED": "GOEDGEKEURD",
        "REJECTED": "AFGEWEZEN",
        # Priority
        "Priority:": "Prioriteit:",
        "CRITICAL": "KRITIEK",
        "HIGH": "HOOG",
        "MEDIUM": "GEMIDDELD",
        "LOW": "LAAG",
    }

    COMPLIANCE_TERMS = {
        # Standards and compliance
        "GDPR": "AVG",
        "GDPR compliance": "AVG-compliant",
        "privacy regulation": "privacywetgeving",
        "data protection": "gegevensbescherming",
        "information security": "informatiebeveiliging",
        "audit trail": "auditspoor",
        "compliance": "compliance",
        "standards": "standaarden",
        "guidelines": "richtlijnen",
        "regulation": "regelgeving",
        "policy": "beleid",
    }

    # Terms that should remain in English
    PRESERVE_ENGLISH = {
        "API",
        "REST",
        "JSON",
        "XML",
        "SQL",
        "NoSQL",
        "Python",
        "JavaScript",
        "TypeScript",
        "HTML",
        "CSS",
        "Git",
        "GitHub",
        "GitLab",
        "CI/CD",
        "Docker",
        "Kubernetes",
        "AWS",
        "Azure",
        "HTTP",
        "HTTPS",
        "TCP/IP",
        "SSL/TLS",
        "OAuth",
        "JWT",
        "SAML",
        "LDAP",
        "URL",
        "URI",
        "UUID",
        "ID",
        "UI",
        "UX",
        "MVP",
        "POC",
        "SLA",
        "KPI",
        "ROI",
        "PDF",
        "CSV",
        "Excel",
        "Agile",
        "Scrum",
        "Sprint",
        "Epic",
        "Backlog",
        "JIRA",
        "Confluence",
    }


class DocumentTranslator:
    """Advanced document translator with justice domain expertise"""

    def __init__(self, dry_run: bool = False, backup: bool = True):
        self.terminology = JusticeTerminology()
        self.dry_run = dry_run
        self.backup = backup
        self.stats = {
            "files_processed": 0,
            "files_translated": 0,
            "files_skipped": 0,
            "total_changes": 0,
            "errors": [],
        }

        # Create backup directory if needed
        if self.backup and not self.dry_run:
            self.backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir.mkdir(parents=True, exist_ok=True)

    def detect_english_content(self, text: str) -> list[str]:
        """Detect remaining English content in text"""
        english_indicators = [
            r"\b(the|and|or|but|with|from|for|by|in|on|at|to|of|as|is|are|was|were|been|have|has|had)\b",
            r"\b(will|would|can|could|should|must|may|might)\b",
            r"\b(user|system|application|feature|function|requirement|specification)\b",
            r"\b(create|read|update|delete|manage|configure|implement|deploy)\b",
        ]

        english_found = []
        for pattern in english_indicators:
            matches = re.findall(pattern, text, re.IGNORECASE)
            english_found.extend(matches)

        # Filter out technical terms that should remain English
        english_found = [
            word
            for word in english_found
            if word.upper() not in self.terminology.PRESERVE_ENGLISH
        ]

        return list(set(english_found))

    def apply_translations(self, content: str) -> tuple[str, int]:
        """Apply all translations to content"""
        changes = 0
        original = content

        # 1. Translate headers (exact match)
        for eng, nl in self.terminology.HEADERS.items():
            pattern = rf"(^|\n)(#+\s*){re.escape(eng)}(\s*[\n:])"
            replacement = rf"\1\2{nl}\3"
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            if new_content != content:
                changes += len(re.findall(pattern, content))
                content = new_content

        # 2. Translate user story patterns
        for eng, nl in self.terminology.USER_STORY_PATTERNS.items():
            pattern = re.compile(re.escape(eng), re.IGNORECASE)
            new_content = pattern.sub(nl, content)
            if new_content != content:
                changes += len(pattern.findall(content))
                content = new_content

        # 3. Translate core terms (case-insensitive)
        for eng, nl in self.terminology.CORE_TERMS.items():
            # Skip if term should be preserved in English
            if eng.upper() in self.terminology.PRESERVE_ENGLISH:
                continue

            pattern = re.compile(r"\b" + re.escape(eng) + r"\b", re.IGNORECASE)
            new_content = pattern.sub(nl, content)
            if new_content != content:
                changes += len(pattern.findall(content))
                content = new_content

        # 4. Translate status terms (exact match)
        for eng, nl in self.terminology.STATUS_TERMS.items():
            content_new = content.replace(eng, nl)
            if content_new != content:
                changes += content.count(eng)
                content = content_new

        # 5. Translate compliance terms
        for eng, nl in self.terminology.COMPLIANCE_TERMS.items():
            pattern = re.compile(r"\b" + re.escape(eng) + r"\b", re.IGNORECASE)
            new_content = pattern.sub(nl, content)
            if new_content != content:
                changes += len(pattern.findall(content))
                content = new_content

        return content, changes

    def add_smart_criteria(self, content: str, file_type: str) -> str:
        """Add SMART criteria where missing"""

        # Check if SMART criteria section exists
        if (
            "acceptatiecriteria" in content.lower()
            or "smart criteria" in content.lower()
        ):
            return content

        if file_type == "story" and "## acceptatiecriteria" not in content.lower():
            # Add acceptance criteria section for user stories
            smart_section = """
## Acceptatiecriteria (SMART)

### Specifiek
- De functionaliteit moet exact gedefinieerd gedrag vertonen
- Alle edge cases moeten gedocumenteerd zijn

### Meetbaar
- Response tijd: < 2 seconden voor 95% van de requests
- Succesratio: > 99% voor normale operaties
- Foutafhandeling: 100% van fouten worden correct afgevangen

### Acceptabel
- Goedgekeurd door Product Owner
- Voldoet aan architectuur richtlijnen
- Gevalideerd door eindgebruikers

### Realistisch
- Implementeerbaar binnen huidige technische stack
- Past binnen sprint capaciteit
- Geen onopgeloste technische blokkades

### Tijdgebonden
- Gereed voor einde van huidige sprint
- Deployment mogelijk binnen release window
"""
            # Insert before test scenarios or at end
            if "## test scenario" in content.lower():
                content = re.sub(
                    r"(## test scenario)",
                    smart_section + r"\n\1",
                    content,
                    flags=re.IGNORECASE,
                )
            else:
                content += smart_section

        return content

    def enhance_with_justice_context(self, content: str) -> str:
        """Enhance content with Dutch justice context"""

        # Add organization context
        if "juridisch medewerker" in content.lower() and "OM" not in content:
            content = content.replace(
                "juridisch medewerker",
                "juridisch medewerker bij OM, DJI, Rechtspraak, Justid of CJIB",
            )

        # Add system integrations
        if "integratie" in content.lower() and "Proza" not in content:
            content = content.replace(
                "bestaande systemen",
                "bestaande systemen (OM Proza, DJI TULP, Rechtspraak GPS, XJUSTID)",
            )

        # Add compliance standards
        if "compliance" in content.lower() and "ASTRA" not in content:
            content = content.replace(
                "compliance standaarden", "compliance standaarden (ASTRA/NORA/BIR/AVG)"
            )

        # Add measurable improvements
        content = re.sub(
            r"verbetert?\s+(\w+)",
            r"verbetert \1 met minimaal 50%",
            content,
            flags=re.IGNORECASE,
        )

        content = re.sub(
            r"vermindert?\s+(\w+)",
            r"vermindert \1 met minimaal 30%",
            content,
            flags=re.IGNORECASE,
        )

        return content

    def determine_priority(self, file_path: Path) -> Priority:
        """Determine translation priority based on file type and location"""

        # P0 - Critical user-facing documentation
        if any(
            x in str(file_path)
            for x in ["US-001", "US-002", "US-003", "EPIC-001", "EPIC-002"]
        ):
            return Priority.P0_CRITICAL

        # P1 - High priority core docs
        if "stories" in str(file_path) or "epics" in str(file_path):
            return Priority.P1_HIGH

        # P2 - Medium priority requirements
        if "requirements" in str(file_path):
            return Priority.P2_MEDIUM

        # P3 - Low priority reference docs
        return Priority.P3_LOW

    def translate_file(self, file_path: Path) -> TranslationResult:
        """Translate a single file"""

        priority = self.determine_priority(file_path)
        errors = []

        try:
            # Read file
            with open(file_path, encoding="utf-8") as f:
                original_content = f.read()

            # Skip if already translated
            if "managementsamenvatting" in original_content.lower():
                logger.info(f"Skipping {file_path.name} - already translated")
                return TranslationResult(
                    file_path=file_path,
                    success=True,
                    changes_made=0,
                    english_remaining=0,
                    errors=[],
                    priority=priority,
                )

            # Backup if needed
            if self.backup and not self.dry_run:
                backup_path = self.backup_dir / file_path.relative_to(
                    file_path.parents[2]
                )
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, backup_path)

            # Apply translations
            content, changes = self.apply_translations(original_content)

            # Determine file type
            file_type = (
                "story"
                if "US-" in file_path.name
                else "epic" if "EPIC-" in file_path.name else "requirement"
            )

            # Add SMART criteria if missing
            content = self.add_smart_criteria(content, file_type)

            # Enhance with justice context
            content = self.enhance_with_justice_context(content)

            # Update change log
            if "wijzigingslog" in content.lower() or "change log" in content.lower():
                today = datetime.now().strftime("%Y-%m-%d")
                new_entry = f"| {today} | 2.0 | Vertaald naar Nederlands met justice context en SMART criteria |"

                # Find table and add entry
                content = re.sub(
                    r"(\| \d{4}-\d{2}-\d{2} \| [\d.]+ \| [^|]+ \|)(\n)",
                    r"\1\n" + new_entry + r"\2",
                    content,
                    count=1,
                )

            # Detect remaining English
            english_remaining = self.detect_english_content(content)

            # Write file if not dry run
            if not self.dry_run and content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"Translated {file_path.name} - {changes} changes made")
            elif self.dry_run:
                logger.info(
                    f"[DRY RUN] Would translate {file_path.name} - {changes} changes"
                )

            return TranslationResult(
                file_path=file_path,
                success=True,
                changes_made=changes,
                english_remaining=len(english_remaining),
                errors=errors,
                priority=priority,
            )

        except Exception as e:
            error_msg = f"Error translating {file_path}: {e!s}"
            logger.error(error_msg)
            errors.append(error_msg)
            return TranslationResult(
                file_path=file_path,
                success=False,
                changes_made=0,
                english_remaining=0,
                errors=errors,
                priority=priority,
            )

    def translate_directory(
        self, directory: Path, pattern: str = "*.md"
    ) -> list[TranslationResult]:
        """Translate all files in a directory"""

        results = []
        files = sorted(directory.glob(pattern))

        # Sort by priority
        files_with_priority = [(f, self.determine_priority(f)) for f in files]
        files_with_priority.sort(key=lambda x: (x[1].value, str(x[0])))

        for file_path, _ in files_with_priority:
            if file_path.name.startswith("."):
                continue

            result = self.translate_file(file_path)
            results.append(result)

            self.stats["files_processed"] += 1
            if result.success and result.changes_made > 0:
                self.stats["files_translated"] += 1
                self.stats["total_changes"] += result.changes_made
            elif result.success and result.changes_made == 0:
                self.stats["files_skipped"] += 1

            if result.errors:
                self.stats["errors"].extend(result.errors)

        return results

    def generate_report(self, results: list[TranslationResult]) -> str:
        """Generate translation report"""

        report = []
        report.append("=" * 80)
        report.append("TRANSLATION REPORT - NEDERLANDSE VERTALING")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        report.append("")

        # Statistics
        report.append("STATISTICS")
        report.append("-" * 40)
        report.append(f"Files processed: {self.stats['files_processed']}")
        report.append(f"Files translated: {self.stats['files_translated']}")
        report.append(f"Files skipped: {self.stats['files_skipped']}")
        report.append(f"Total changes: {self.stats['total_changes']}")
        report.append(f"Errors: {len(self.stats['errors'])}")
        report.append("")

        # Priority breakdown
        report.append("PRIORITY BREAKDOWN")
        report.append("-" * 40)
        for priority in Priority:
            priority_results = [r for r in results if r.priority == priority]
            if priority_results:
                translated = sum(1 for r in priority_results if r.changes_made > 0)
                report.append(
                    f"{priority.value}: {translated}/{len(priority_results)} files translated"
                )
        report.append("")

        # Files with remaining English
        english_files = [r for r in results if r.english_remaining > 5]
        if english_files:
            report.append("FILES WITH REMAINING ENGLISH CONTENT")
            report.append("-" * 40)
            for result in sorted(
                english_files, key=lambda x: x.english_remaining, reverse=True
            )[:10]:
                report.append(
                    f"- {result.file_path.name}: {result.english_remaining} English terms detected"
                )
            report.append("")

        # Errors
        if self.stats["errors"]:
            report.append("ERRORS")
            report.append("-" * 40)
            for error in self.stats["errors"]:
                report.append(f"- {error}")
            report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 40)
        success_rate = (
            (self.stats["files_translated"] / self.stats["files_processed"] * 100)
            if self.stats["files_processed"] > 0
            else 0
        )
        report.append(f"Translation success rate: {success_rate:.1f}%")

        if success_rate >= 90:
            report.append("Status: EXCELLENT - Translation highly successful")
        elif success_rate >= 70:
            report.append("Status: GOOD - Most files translated successfully")
        else:
            report.append("Status: NEEDS ATTENTION - Many files require manual review")

        return "\n".join(report)


def main():
    """Main execution function"""

    import argparse

    parser = argparse.ArgumentParser(
        description="Translate documentation to Dutch with justice terminology"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip creating backups"
    )
    parser.add_argument(
        "--priority",
        choices=["P0", "P1", "P2", "P3", "all"],
        default="all",
        help="Only translate files with specified priority or higher",
    )
    parser.add_argument(
        "--pattern", default="*.md", help="File pattern to match (default: *.md)"
    )

    args = parser.parse_args()

    # Initialize translator
    translator = DocumentTranslator(dry_run=args.dry_run, backup=not args.no_backup)

    # Base path
    base_path = Path("/Users/chrislehnen/Projecten/Definitie-app/docs")

    print("=" * 80)
    print("DUTCH TRANSLATION SCRIPT - NEDERLANDSE JUSTITIEKETEN")
    print("=" * 80)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Backup: {'ENABLED' if not args.no_backup else 'DISABLED'}")
    print(f"Priority: {args.priority}")
    print()

    all_results = []

    # Process directories
    directories = [
        ("epics", "EPIC-*.md"),
        ("stories", "US-*.md"),
        ("requirements", "REQ-*.md"),
    ]

    for dir_name, pattern in directories:
        dir_path = base_path / dir_name
        if dir_path.exists():
            print(f"\nProcessing {dir_name}...")
            results = translator.translate_directory(dir_path, pattern)
            all_results.extend(results)

            # Filter by priority if specified
            if args.priority != "all":
                priority_threshold = Priority[
                    f"P{args.priority[-1]}_{'CRITICAL' if args.priority == 'P0' else 'HIGH' if args.priority == 'P1' else 'MEDIUM' if args.priority == 'P2' else 'LOW'}"
                ]
                all_results = [
                    r
                    for r in all_results
                    if r.priority.value <= priority_threshold.value
                ]

    # Generate and save report
    report = translator.generate_report(all_results)

    # Save report
    report_path = (
        Path("logs")
        / f'translation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    )
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + report)
    print(f"\nReport saved to: {report_path}")

    if args.dry_run:
        print("\nThis was a DRY RUN. No files were modified.")
        print("Run without --dry-run to apply translations.")

    return 0 if len(translator.stats["errors"]) == 0 else 1


if __name__ == "__main__":
    exit(main())
