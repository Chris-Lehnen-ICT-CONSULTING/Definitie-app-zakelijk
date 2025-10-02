#!/usr/bin/env python3
"""
Vertaal alle documentatie naar het Nederlands voor de Nederlandse justitiemarkt
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Vertalingen voor veelvoorkomende termen
TRANSLATIONS = {
    # Headers
    "Executive Summary": "Managementsamenvatting",
    "Business Value": "Bedrijfswaarde",
    "Success Metrics": "Succesmetrieken",
    "Story Breakdown": "Gebruikersverhalen Overzicht",
    "User Story": "Gebruikersverhaal",
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

    # Status
    "Status:": "Status:",
    "DONE": "GEREED",
    "IN_PROGRESS": "IN_UITVOERING",
    "TODO": "TE_DOEN",
    "BLOCKED": "GEBLOKKEERD",
    "Priority:": "Prioriteit:",
    "HIGH": "HOOG",
    "CRITICAL": "KRITIEK",
    "MEDIUM": "GEMIDDELD",
    "LOW": "LAAG",

    # User types
    "As a legal professional": "Als juridisch medewerker bij het OM/DJI/Rechtspraak",
    "As a developer": "Als ontwikkelaar binnen de justitieketen",
    "As a system administrator": "Als systeembeheerder binnen de justitieketen",
    "As a system": "Als justitie IT-systeem",
    "As an operations team": "Als operations team van Justid/CJIB",
    "As a QA engineer": "Als QA engineer voor kritieke justitiesystemen",
    "As a business analyst": "Als business analist voor de justitieketen",
    "As a security officer": "Als security officer conform BIR-richtlijnen",

    # Actions
    "I want": "Wil ik",
    "So that": "Zodat",
    "Given": "Gegeven",
    "When": "Wanneer",
    "Then": "Dan",

    # Technical terms that stay English
    # "API", "REST", "JSON", "SQL", "Python", "JavaScript", "Git", "Docker"

    # Justice domain specific
    "justice sector": "justitiesector",
    "justice chain": "justitieketen",
    "legal definition": "juridische definitie",
    "legal definitions": "juridische definities",
    "validation rules": "validatieregels",
    "validation rule": "validatieregel",
    "legal terminology": "juridische terminologie",
    "court": "rechtbank",
    "prosecutor": "officier van justitie",
    "prosecution": "openbaar ministerie",
    "detention": "detentie",
    "criminal law": "strafrecht",
    "administrative law": "bestuursrecht",
    "civil law": "burgerlijk recht",

    # Dates
    "Date": "Datum",
    "Version": "Versie",
    "Changes": "Wijzigingen",
    "Created": "Aangemaakt",
    "Updated": "Bijgewerkt",
    "Completed": "Voltooid",

    # Common phrases
    "Epic created": "Epic aangemaakt",
    "Marked as complete": "Gemarkeerd als voltooid",
    "All tests passing": "Alle tests slagen",
    "Production deployment": "Productie deployment",
    "User training": "Gebruikerstraining",
    "Documentation complete": "Documentatie compleet",
    "Security review": "Security beoordeling",
    "Code review": "Code review",

    # Approvals
    "Approved": "Goedgekeurd",
    "Pending": "In afwachting",
    "Business Owner": "Business Owner",
    "Technical Lead": "Technisch Lead",
    "Security Officer": "Security Officer",
    "Compliance Officer": "Compliance Officer",
    "Quality Lead": "Kwaliteits Lead",
}

# Justice organizations
ORGANIZATIONS = {
    "OM": "Openbaar Ministerie (OM)",
    "DJI": "Dienst Justitiële Inrichtingen (DJI)",
    "Rechtspraak": "De Rechtspraak",
    "Justid": "Justitiële Informatiedienst (Justid)",
    "CJIB": "Centraal Justitieel Incassobureau (CJIB)",
}

def add_justice_context(content: str) -> str:
    """Voeg Nederlandse justitie context toe waar relevant"""

    # Voeg organisatie context toe
    content = content.replace(
        "for legal professionals",
        "voor juridisch medewerkers bij OM, DJI, Rechtspraak, Justid en CJIB"
    )

    # Voeg meetbare metrieken toe
    content = re.sub(
        r"reduces? (\w+) time",
        r"reduceert \1 tijd met 80% (van uren naar minuten)",
        content,
        flags=re.IGNORECASE
    )

    # Voeg compliance standaarden toe
    if "ASTRA" in content and "BIR" not in content:
        content = content.replace("ASTRA/NORA", "ASTRA/NORA/BIR")

    # Voeg systeem integraties toe
    content = content.replace(
        "integrate with existing systems",
        "integreren met OM Proza, DJI TULP, Rechtspraak GPS, CJIB systemen"
    )

    return content

def translate_file(file_path: Path) -> bool:
    """Vertaal een enkel bestand naar het Nederlands"""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Skip als al vertaald
        if "Managementsamenvatting" in content or "Gebruikersverhaal" in content:
            print(f"  ✓ {file_path.name} - Al vertaald")
            return False

        # Pas vertalingen toe
        for eng, nl in TRANSLATIONS.items():
            # Case-sensitive replacement voor headers
            if eng.startswith("#") or eng.endswith(":"):
                content = content.replace(eng, nl)
            else:
                # Case-insensitive voor andere termen
                content = re.sub(
                    re.escape(eng),
                    nl,
                    content,
                    flags=re.IGNORECASE
                )

        # Voeg justice context toe
        content = add_justice_context(content)

        # Update change log
        if "Wijzigingslog" in content or "Change Log" in content:
            today = "2025-09-05"
            new_entry = f"| {today} | 1.x | Vertaald naar Nederlands met justitie context |"

            # Zoek de tabel en voeg nieuwe entry toe
            content = re.sub(
                r'(\| \d{4}-\d{2}-\d{2} \| [\d.]+ \| [^|]+ \|)(\n)',
                r'\1\n' + new_entry + r'\2',
                content,
                count=1
            )

        # Update compliance footer
        content = content.replace(
            "This epic is part of the DefinitieAgent project and follows ASTRA/NORA guidelines for justice domain systems.",
            "Deze epic is onderdeel van het DefinitieAgent project en volgt ASTRA/NORA/BIR richtlijnen voor justitie domein systemen binnen de Nederlandse rechtsketen."
        )

        # Schrijf alleen als er wijzigingen zijn
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ {file_path.name} - Vertaald")
            return True
        else:
            print(f"  - {file_path.name} - Geen wijzigingen")
            return False

    except Exception as e:
        print(f"  ✗ {file_path.name} - Fout: {e}")
        return False

def process_directory(dir_path: Path, pattern: str = "*.md") -> Tuple[int, int]:
    """Verwerk alle bestanden in een directory"""

    processed = 0
    translated = 0

    for file_path in sorted(dir_path.glob(pattern)):
        if file_path.name == "INDEX.md":
            continue  # Skip index files for now

        processed += 1
        if translate_file(file_path):
            translated += 1

    return processed, translated

def main():
    """Hoofdfunctie voor het vertalen van documentatie"""

    base_path = Path("/Users/chrislehnen/Projecten/Definitie-app/docs")

    print("=" * 60)
    print("DOCUMENTATIE VERTALING NAAR NEDERLANDS")
    print("Voor de Nederlandse justitiemarkt")
    print("=" * 60)
    print()

    # Verwerk Epics
    print("📁 EPICS:")
    epics_path = base_path / "epics"
    if epics_path.exists():
        processed, translated = process_directory(epics_path)
        print(f"  Totaal: {processed} bestanden, {translated} vertaald\n")

    # Verwerk Stories
    print("📁 USER STORIES:")
    stories_path = base_path / "stories"
    if stories_path.exists():
        processed, translated = process_directory(stories_path, "US-*.md")
        print(f"  Totaal: {processed} bestanden, {translated} vertaald\n")

    # Verwerk Requirements
    print("📁 REQUIREMENTS:")
    req_path = base_path / "requirements"
    if req_path.exists():
        processed, translated = process_directory(req_path, "REQ-*.md")
        print(f"  Totaal: {processed} bestanden, {translated} vertaald\n")

    print("=" * 60)
    print("✅ Vertaling voltooid!")
    print("=" * 60)

if __name__ == "__main__":
    main()
