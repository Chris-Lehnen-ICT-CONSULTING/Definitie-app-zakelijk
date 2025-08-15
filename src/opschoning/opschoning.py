"""Opschoning module voor het verbeteren van AI-gegenereerde definities.

Dit module bevat functionaliteit voor het opschonen van definities
door verboden beginconstructies te verwijderen en formatting te verbeteren.
"""

import re  # Reguliere expressies voor patroon matching

from config.config_loader import laad_verboden_woorden  # Verboden woorden configuratie

# Geïsoleerde module voor opschoning van GPT-gegenereerde definities
# Verwijdert alle verboden aanhefconstructies, dwingt hoofdletter en punt af


def opschonen(definitie: str, begrip: str) -> str:
    """
    Verwijdert herhaaldelijk alle verboden beginconstructies uit definitie.

    Args:
        definitie: De te schonen definitie tekst
        begrip: Het begrip dat gedefinieerd wordt

    Returns:
        Opgeschoonde definitie met correcte formatting

    Verwijdert:
    - Koppelwerkwoorden (bijv. 'is', 'omvat', 'betekent')
    - Lidwoorden (bijv. 'de', 'het', 'een')
    - Cirkeldefinities (begrip + verboden woord of dubbelepunt)

    Dwingt daarna een hoofdletter en eindpunt af.
    """
    # Stap 1: Voorbewerking - verwijder leading/trailing whitespace
    d = definitie.strip()  # Verwijder spaties aan begin en einde van definitie

    # Stap 2: Laad verboden woordenlijst uit centrale configuratie
    config = laad_verboden_woorden()  # Laad configuratie uit JSON bestand
    # Haal verboden woorden lijst uit config (ondersteunt zowel dict als lijst formaat)
    verboden_lijst = (
        config.get("verboden_woorden", []) if isinstance(config, dict) else []
    )  # Extract lijst met veilige fallback

    # Stap 3: Genereer regex patronen voor alle verboden beginconstructies
    begrip_esc = re.escape(
        begrip.strip().lower()
    )  # Escape speciale karakters in begrip voor veilige regex
    regex_lijst = []  # Lijst om alle gegenereerde regex patronen in op te slaan

    # Doorloop alle verboden woorden en maak specifieke regex patronen
    for woord in verboden_lijst:  # Itereer over elke verboden woord
        w = (
            woord.strip().lower()
        )  # Normaliseer woord naar lowercase en verwijder whitespace
        if not w:  # Skip lege of whitespace-only woorden
            continue  # Ga door naar volgende woord
        w_esc = re.escape(
            w
        )  # Escape speciale regex karakters voor veilige pattern matching

        # Patroon 3a: Exact woord aan het begin van definitie
        regex_lijst.append(rf"^{w_esc}\b")

        # Patroon 3b: Begrip gevolgd door verboden woord (circulaire definitie)
        regex_lijst.append(rf"^{begrip_esc}\s+{w_esc}\b")

    # Patroon 3c: Extra patroon voor begrip gevolgd door dubbelepunt of streepje
    regex_lijst.append(rf"^{begrip_esc}\s*[:\-]?\s*")
    # Vangt constructies zoals 'Vonnis:', 'vonnis -', 'vonnis :'

    # ✅ 4. Verwijder alle opeenvolgende verboden prefixes
    while True:
        for patroon in regex_lijst:
            if re.match(patroon, d, flags=re.IGNORECASE):
                d = re.sub(patroon, "", d, flags=re.IGNORECASE, count=1)
                d = d.lstrip(" ,:-")
                break
        else:
            # ✅ Geen patroon meer gevonden
            break

    # ✅ 5. Herstel hoofdletter
    d = d.strip()
    if d and not d[0].isupper():
        d = d[0].upper() + d[1:]

    # ✅ 6. Voeg punt toe indien ontbrekend
    if d and not d.endswith("."):
        d += "."

    return d
