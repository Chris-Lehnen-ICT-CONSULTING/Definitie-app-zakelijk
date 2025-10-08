"""Enhanced opschoning module voor het verbeteren van AI-gegenereerde definities.

Dit is de MODERNE versie die gebruikt wordt door CleaningService voor het
opschonen van GPT-4 responses die ontologische categorieën bevatten.

WELKE VERSIE WORDT WANNEER GEBRUIKT?
====================================
1. opschoning.py (basis versie):
   - Originele implementatie
   - Alleen gebruikt als fallback

2. opschoning_enhanced.py (deze file):
   - ALTIJD gebruikt door CleaningService
   - Detecteert automatisch GPT format
   - Verwijdert ontologische headers
   - Roept intern opschoning.py aan voor de basis opschoning

CALL FLOW:
==========
CleaningService.clean_text()
    ↓
opschoning_enhanced.opschonen_enhanced()
    ↓
extract_definition_from_gpt_response() [indien GPT format]
    ↓
opschoning.opschonen() [basis opschoning]
    ↓
Opgeschoonde definitie

EXTRA FUNCTIONALITEIT:
=====================
- Verwijdert "Ontologische categorie: [type]" headers
- Extraheert metadata uit GPT responses
- Handelt moderne prompt formats
"""

import re

from opschoning.opschoning import opschonen


def extract_definition_from_gpt_response(text: str) -> str:
    r"""
    Extract de werkelijke definitie uit een GPT response.

    Moderne GPT-4 responses bevatten vaak metadata headers zoals:
    "Ontologische categorie: type
     Juridisch document dat..."

    Deze functie verwijdert:
    - Ontologische categorie headers (bijv. "Ontologische categorie: proces")
    - Lege regels aan het begin
    - Andere metadata regels

    Args:
        text: De volledige GPT response

    Returns:
        Alleen de definitie tekst zonder metadata

    Voorbeelden:
        Input:  "Ontologische categorie: resultaat\nVonnis is een uitspraak"
        Output: "Vonnis is een uitspraak"

        Input:  "Ontologische categorie: type\n\nDocument dat rechten vastlegt"
        Output: "Document dat rechten vastlegt"
    """
    lines = text.strip().split("\n")

    # Filter regels die metadata bevatten
    filtered_lines = []
    for line in lines:
        line_lower = line.lower().strip()
        # Skip ontologische categorie regels (met of zonder markdown dash)
        # Matches: "Ontologische categorie: type"
        # Matches: "- Ontologische categorie: type"
        # Matches: "  - Ontologische categorie: type"
        if line_lower.lstrip("- ").startswith("ontologische categorie:"):
            continue
        # Skip lege regels
        if not line.strip():
            continue
        # Voeg toe aan gefilterde regels
        filtered_lines.append(line)

    # Join de overgebleven regels
    return "\n".join(filtered_lines).strip()


def opschonen_enhanced(
    definitie: str, begrip: str, handle_gpt_format: bool = True
) -> str:
    r"""
    Enhanced versie van opschonen die ook moderne GPT formats aankan.

    Dit is de HOOFDFUNCTIE die ALTIJD gebruikt wordt door CleaningService.

    Workflow:
    1. Detecteert of input een GPT response is (bevat ontologische categorie)
    2. Verwijdert GPT metadata indien aanwezig
    3. Past basis opschoning toe via opschoning.opschonen()

    Args:
        definitie: De te schonen definitie tekst (mogelijk met GPT metadata)
        begrip: Het begrip dat gedefinieerd wordt
        handle_gpt_format: Of GPT format parsing toegepast moet worden (default True)

    Returns:
        Volledig opgeschoonde definitie met correcte formatting

    Voorbeelden:
        # Met GPT header:
        Input:  "Ontologische categorie: type\nis een document", "akte"
        Output: "Document."

        # Zonder GPT header:
        Input:  "de rechterlijke beslissing", "vonnis"
        Output: "Rechterlijke beslissing."

        # Circulaire definitie met GPT header:
        Input:  "Ontologische categorie: resultaat\nvonnis betekent een uitspraak", "vonnis"
        Output: "Uitspraak."
    """
    # Stap 1: Handle GPT format indien nodig
    if handle_gpt_format:
        definitie = extract_definition_from_gpt_response(definitie)

    # Stap 2: Gebruik de originele opschonen functie
    result: str = opschonen(definitie, begrip)
    return result


def analyze_gpt_response(text: str) -> dict:
    """
    Analyseer een GPT response voor metadata.

    Returns:
        Dict met geëxtraheerde metadata zoals ontologische categorie
    """
    metadata = {}

    # Zoek naar ontologische categorie
    ontology_match = re.search(r"ontologische categorie:\s*(\w+)", text, re.IGNORECASE)
    if ontology_match:
        metadata["ontologische_categorie"] = ontology_match.group(1).lower()

    return metadata
