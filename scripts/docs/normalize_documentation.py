#!/usr/bin/env python3
"""
Documentatie Normalisatie Script
Normaliseert alle documentatie naar volledig Nederlands met consistente terminologie.
"""

import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# Engelse naar Nederlandse vertalingen
TRANSLATIONS = {
    # Status termen
    "BACKLOG": "ACHTERSTAND",
    "IN_PROGRESS": "IN_UITVOERING",
    "IN PROGRESS": "IN UITVOERING",
    "DONE": "GEREED",
    "TODO": "TE_DOEN",
    "BLOCKED": "GEBLOKKEERD",
    "READY": "KLAAR",
    "PENDING": "WACHTEND",
    "COMPLETED": "VOLTOOID",
    "ACTIVE": "ACTIEF",
    "DRAFT": "CONCEPT",
    "ARCHIVED": "GEARCHIVEERD",
    # Prioriteit termen
    "HIGH": "HOOG",
    "MEDIUM": "GEMIDDELD",
    "LOW": "LAAG",
    "CRITICAL": "KRITIEK",
    # Development termen
    "dependencies": "afhankelijkheden",
    "Dependencies": "Afhankelijkheden",
    "requirements": "vereisten",
    "Requirements": "Vereisten",
    "Related Requirements": "Gerelateerde Vereisten",
    "acceptance criteria": "acceptatiecriteria",
    "Acceptance Criteria": "Acceptatiecriteria",
    # BDD termen
    "Given": "Gegeven",
    "When": "Wanneer",
    "Then": "Dan",
    "And": "En",
    "But": "Maar",
    # Project termen
    "Business Value": "Bedrijfswaarde",
    "User Story": "Gebruikersverhaal",
    "User Stories": "Gebruikersverhalen",
    "Epic": "Episch Verhaal",
    "Epics": "Epische Verhalen",
    "Story Points": "Verhaalpunten",
    "Sprint": "Sprint",
    # Documentatie termen
    "Domain Rules": "Domeinregels",
    "Implementation Notes": "Implementatie Notities",
    "Security": "Beveiliging",
    "Privacy": "Privacy",
    "Performance": "Prestaties",
    "Testing": "Testen",
    "Deployment": "Uitrol",
    "Implementation": "Implementatie",
    "Workflow": "Werkstroom",
    "Handover": "Overdracht",
    "Cache": "Cache",
    "Status": "Status",
    "Priority": "Prioriteit",
    # Extra termen
    "Completed Stories": "Voltooide Verhalen",
    "Pending Stories": "Wachtende Verhalen",
    "Quick Navigation": "Snelle Navigatie",
    "Document Purpose": "Document Doel",
    "Last Updated": "Laatst Bijgewerkt",
    "Applies To": "Van Toepassing Op",
    "Owner": "Eigenaar",
    "Version": "Versie",
    "Type": "Type",
}

# Typefouten die gecorrigeerd moeten worden
TYPO_FIXES = {
    "valiDatum": "validatie",
    "HEnling": "Handling",
    "fLAAG": "flag",
    "geïmplementeerd": "geïmplementeerd",  # Correct spelling
    "geuploaded": "geüpload",
    "geupdated": "geüpdatet",
    "gevalideerd": "gevalideerd",  # Correct spelling
}

# Justice domein standaardisatie
JUSTICE_TERMS = {
    "om": "OM",
    "Om": "OM",
    "openbaar ministerie": "Openbaar Ministerie (OM)",
    "dji": "DJI",
    "Dji": "DJI",
    "dienst justitiële inrichtingen": "Dienst Justitiële Inrichtingen (DJI)",
    "rechtspraak": "Rechtspraak",
    "justid": "Justid",
    "JustId": "Justid",
    "astra": "ASTRA",
    "Astra": "ASTRA",
    "nora": "NORA",
    "Nora": "NORA",
    "gemma": "GEMMA",
    "Gemma": "GEMMA",
}

# Datum/tijd formaat patterns
DATE_PATTERNS = [
    (r"\b(\d{4})-(\d{2})-(\d{2})\b", r"\3-\2-\1"),  # YYYY-MM-DD naar DD-MM-YYYY
    (r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", r"\1-\2-\3"),  # MM/DD/YYYY naar DD-MM-YYYY
]


class DocumentNormalizer:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.stats = {
            "files_processed": 0,
            "files_modified": 0,
            "translations": Counter(),
            "typos": Counter(),
            "justice_terms": Counter(),
            "date_formats": Counter(),
        }

    def should_process_file(self, filepath: Path) -> bool:
        """Check of bestand verwerkt moet worden."""
        # Skip archief en backup bestanden
        if "archief" in str(filepath) or "backup" in str(filepath):
            return False
        # Skip niet-markdown bestanden
        if filepath.suffix != ".md":
            return False
        # Skip backup bestanden
        return not (
            filepath.name.endswith(".backup")
            or filepath.name.endswith(".linkfix_backup")
        )

    def normalize_content(self, content: str, filepath: Path) -> tuple[str, bool]:
        """Normaliseer de inhoud van een document."""
        original = content

        # 1. Vervang Engelse termen
        for eng, nl in TRANSLATIONS.items():
            # Case-sensitive replacement voor exact matches
            if eng in content:
                # Speciale handling voor status termen in frontmatter
                if eng in ["BACKLOG", "IN_PROGRESS", "DONE", "TODO", "BLOCKED"]:
                    # Alleen vervangen in status velden
                    pattern = rf"(\bstatus:\s*)(✅\s*)?{re.escape(eng)}\b"
                    replacement = rf"\1\2{nl}"
                    new_content = re.sub(pattern, replacement, content)
                else:
                    # Normale word boundary replacement
                    pattern = rf"\b{re.escape(eng)}\b"
                    new_content = re.sub(pattern, nl, content)

                if new_content != content:
                    count = content.count(eng)
                    self.stats["translations"][f"{eng} → {nl}"] += count
                    content = new_content

        # 2. Corrigeer typefouten
        for typo, correct in TYPO_FIXES.items():
            if typo in content:
                count = content.count(typo)
                content = content.replace(typo, correct)
                self.stats["typos"][f"{typo} → {correct}"] += count

        # 3. Harmoniseer justice terminologie
        for term, standard in JUSTICE_TERMS.items():
            pattern = rf"\b{re.escape(term)}\b"
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                content = re.sub(pattern, standard, content, flags=re.IGNORECASE)
                self.stats["justice_terms"][f"{term} → {standard}"] += len(matches)

        # 4. Standaardiseer datum formaten
        for pattern, replacement in DATE_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                self.stats["date_formats"]["datum formaat"] += len(matches)

        # 5. Specifieke epic/story normalisaties
        if "US-" in str(filepath) or "EPIC-" in str(filepath):
            # Vervang Epic headers
            content = re.sub(
                r"^## Epic (\d+):",
                r"## Episch Verhaal \1:",
                content,
                flags=re.MULTILINE,
            )
            content = re.sub(
                r"^### Story (\d+\.\d+):",
                r"### Verhaal \1:",
                content,
                flags=re.MULTILINE,
            )

            # Acceptatiecriteria format
            content = re.sub(
                r"^\s*Given\s+", "   Gegeven ", content, flags=re.MULTILINE
            )
            content = re.sub(r"^\s*When\s+", "   Wanneer ", content, flags=re.MULTILINE)
            content = re.sub(r"^\s*Then\s+", "   Dan ", content, flags=re.MULTILINE)

        return content, (content != original)

    def process_directory(self, directory: str):
        """Verwerk alle bestanden in een directory."""
        base_path = Path(directory)

        for filepath in base_path.rglob("*.md"):
            if not self.should_process_file(filepath):
                continue

            self.stats["files_processed"] += 1

            try:
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()

                normalized_content, was_modified = self.normalize_content(
                    content, filepath
                )

                if was_modified:
                    self.stats["files_modified"] += 1

                    if not self.dry_run:
                        # Maak backup
                        backup_path = filepath.with_suffix(".md.normbackup")
                        with open(backup_path, "w", encoding="utf-8") as f:
                            f.write(content)

                        # Schrijf genormaliseerde content
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(normalized_content)

                        print(f"✓ Genormaliseerd: {filepath.relative_to(base_path)}")
                    else:
                        print(
                            f"[DRY RUN] Zou normaliseren: {filepath.relative_to(base_path)}"
                        )

            except Exception as e:
                print(f"✗ Fout bij verwerken van {filepath}: {e}")

    def generate_report(self) -> str:
        """Genereer een rapport van de normalisatie."""
        report = []
        report.append("# Documentatie Normalisatie Rapport")
        report.append(f'\nDatum: {datetime.now().strftime("%d-%m-%Y %H:%M")}')
        report.append(f'Modus: {"DRY RUN" if self.dry_run else "UITGEVOERD"}')

        report.append("\n## Samenvatting")
        report.append(f'- Bestanden verwerkt: {self.stats["files_processed"]}')
        report.append(f'- Bestanden aangepast: {self.stats["files_modified"]}')

        if self.stats["translations"]:
            report.append("\n## Engelse → Nederlandse Vertalingen")
            for term, count in sorted(
                self.stats["translations"].items(), key=lambda x: x[1], reverse=True
            ):
                report.append(f"- {term}: {count}x")

        if self.stats["typos"]:
            report.append("\n## Gecorrigeerde Typefouten")
            for typo, count in sorted(
                self.stats["typos"].items(), key=lambda x: x[1], reverse=True
            ):
                report.append(f"- {typo}: {count}x")

        if self.stats["justice_terms"]:
            report.append("\n## Geharmoniseerde Justice Terminologie")
            for term, count in sorted(
                self.stats["justice_terms"].items(), key=lambda x: x[1], reverse=True
            ):
                report.append(f"- {term}: {count}x")

        if self.stats["date_formats"]:
            report.append("\n## Gestandaardiseerde Datum Formaten")
            for format_type, count in self.stats["date_formats"].items():
                report.append(f"- {format_type}: {count}x")

        total_changes = (
            sum(self.stats["translations"].values())
            + sum(self.stats["typos"].values())
            + sum(self.stats["justice_terms"].values())
            + sum(self.stats["date_formats"].values())
        )

        report.append(f"\n## Totaal Aantal Wijzigingen: {total_changes}")

        return "\n".join(report)


def main():
    # Parse command line arguments
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    print("=" * 60)
    print("DOCUMENTATIE NORMALISATIE TOOL")
    print("=" * 60)

    if dry_run:
        print("🔍 DRY RUN MODUS - Geen bestanden worden gewijzigd")
    else:
        print("⚠️  PRODUCTIE MODUS - Bestanden worden gewijzigd")
        response = input("Weet je zeker dat je door wilt gaan? (ja/nee): ")
        if response.lower() != "ja":
            print("Normalisatie geannuleerd.")
            return

    normalizer = DocumentNormalizer(dry_run=dry_run)

    # Verwerk docs directory
    docs_dir = "/Users/chrislehnen/Projecten/Definitie-app/docs"
    print(f"\n📁 Verwerken van: {docs_dir}")
    normalizer.process_directory(docs_dir)

    # Genereer en toon rapport
    report = normalizer.generate_report()
    print("\n" + "=" * 60)
    print(report)

    # Sla rapport op
    if not dry_run:
        report_path = (
            "/Users/chrislehnen/Projecten/Definitie-app/docs/NORMALISATIE_RAPPORT.md"
        )
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n📄 Rapport opgeslagen in: {report_path}")


if __name__ == "__main__":
    main()
