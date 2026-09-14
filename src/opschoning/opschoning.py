"""Opschoning module voor het verbeteren van AI-gegenereerde definities.

Dit module bevat de BASIS opschoningsfunctionaliteit voor definities
door verboden beginconstructies te verwijderen en formatting te verbeteren.

BELANGRIJK: Dit is de originele/basis versie. Voor moderne GPT responses
           met ontologische categorieën, gebruik opschoning_enhanced.py

Nederlandse Wetgevingstechniek vereist dat definities:
- NIET beginnen met lidwoorden (de, het, een)
- NIET beginnen met koppelwerkwoorden (is, zijn, wordt)
- NIET circulair zijn (begrip herhaalt zichzelf)
- WEL beginnen met een hoofdletter
- WEL eindigen met een punt

Voorbeelden van opschoning:
- "is een uitspraak" → "Uitspraak."
- "de rechterlijke beslissing" → "Rechterlijke beslissing."
- "Vonnis is een uitspraak" → "Uitspraak." (circulaire definitie)
- "betekent dat" → "Dat."
"""

import re  # Reguliere expressies voor patroon matching

from config.verboden_woorden import (
    laad_verboden_woorden,  # Verboden woorden configuratie
)

# Geïsoleerde module voor opschoning van GPT-gegenereerde definities
# Verwijdert alle verboden aanhefconstructies, dwingt hoofdletter en punt af

#: Koppel- en hulpwerkwoorden waarmee een verboden beginconstructie mag
#: beginnen om als vorm te gelden ("is een", "verwijst naar", "heeft
#: betrekking op"). Een meerwoordige frase die níet met zo'n werkwoord begint
#: draagt het bovenbegrip of een betekenisdragend woord ("handeling die",
#: "proces waarbij", "vorm van", "een belangrijk …") en wordt door de
#: nabewerking nooit verwijderd (DEF-622, CW-GEN-03): wat overblijft zou een
#: kernloos fragment zijn. Of zo'n bovenbegrip passend is, beoordelen de
#: toetsregels (ARAI-02/ARAI-03), niet de cleaner.
_KOPPELWERKWOORDEN: frozenset[str] = frozenset(
    {
        "is",
        "zijn",
        "was",
        "waren",
        "wordt",
        "worden",
        "betreft",
        "omvat",
        "betekent",
        "behelst",
        "bevat",
        "impliceert",
        "definieert",
        "beschrijft",
        "verwijst",
        "houdt",
        "heeft",
        "duidt",
        "staat",
        "bestaat",
    }
)


def is_vormconstructie(woord: str) -> bool:
    """Alleen een los functiewoord of een koppelwerkwoordfrase is vorm.

    Eén woord (lidwoord, koppelwerkwoord) mag als beginconstructie worden
    verwijderd; een meerwoordige frase alleen wanneer zij met een
    koppelwerkwoord begint. Alle andere frasen dragen betekenis.
    """
    delen = woord.strip().lower().split()
    if not delen:
        return False
    return len(delen) == 1 or delen[0] in _KOPPELWERKWOORDEN


def opschonen(definitie: str, begrip: str) -> str:
    """
    Verwijdert herhaaldelijk alle verboden beginconstructies uit definitie.

    Deze functie past de Nederlandse wetgevingstechniek toe door systematisch
    alle niet-toegestane beginconstructies te verwijderen tot een correcte
    definitie overblijft.

    Args:
        definitie: De te schonen definitie tekst
        begrip: Het begrip dat gedefinieerd wordt

    Returns:
        Opgeschoonde definitie met correcte formatting

    OPSCHONINGSREGELS IN DETAIL:

    1. VERBODEN WOORDEN (uit verboden_woorden.json), alleen als VORM:
       - Koppelwerkwoorden: "is", "omvat", "betekent", "verwijst naar"
       - Lidwoorden: "de", "het", "een"
       - NIET: bovenbegrip-/betekenisdragende frasen uit dezelfde lijst
         ("proces waarbij", "handeling die", "vorm van", "een belangrijk").
         Die blijven staan (DEF-622); de toetsregels beoordelen ze.

    2. DRIE OPSCHONINGSPATRONEN:
       A. Woord aan begin: "is een proces" → "proces"
       B. Circulaire definitie: "Vonnis is een uitspraak" → "uitspraak"
       C. Begrip met leesteken: "Vonnis: een uitspraak" → "uitspraak"

    3. ITERATIEF PROCES:
       Herhaalt tot geen vormconstructie meer aan het begin staat:
       "is een belangrijk proces waarbij"
       → "een belangrijk proces waarbij" (verwijder "is")
       → "belangrijk proces waarbij" (verwijder "een")
       → stopt: "belangrijk" en "proces waarbij" dragen betekenis

    4. FORMATTING:
       - Eerste letter wordt hoofdletter
       - Voegt punt toe indien ontbrekend

    Voorbeelden:
    - opschonen("is een uitspraak", "vonnis") → "Uitspraak."
    - opschonen("de rechterlijke beslissing", "vonnis") → "Rechterlijke beslissing."
    - opschonen("vonnis betekent een beslissing", "vonnis") → "Beslissing."
    """
    # Stap 1: Voorbewerking - verwijder leading/trailing whitespace
    d = definitie.strip()  # Verwijder spaties aan begin en einde van definitie

    # Stap 2: Laad verboden woordenlijst uit centrale configuratie
    config = laad_verboden_woorden()  # Laad configuratie uit JSON bestand
    # Haal verboden woorden lijst (ondersteunt zowel dict als lijst formaat)
    if isinstance(config, dict):
        verboden_lijst = config.get("verboden_woorden", [])
    elif isinstance(config, list):
        verboden_lijst = config
    else:
        verboden_lijst = []

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
        if not is_vormconstructie(w):
            # DEF-622: bovenbegrip-/betekenisdragende frasen ("handeling die",
            # "proces waarbij", "vorm van") blijven staan; alleen de
            # toetsregels beoordelen ze.
            continue
        w_esc = re.escape(
            w
        )  # Escape speciale regex karakters voor veilige pattern matching

        # Patroon 3a: Exact woord aan het begin van definitie
        # Voorbeeld: "is een uitspraak" → matcht "is" aan begin
        # Regex: ^is\b (^ = begin, \b = woordgrens)
        regex_lijst.append(rf"^{w_esc}\b")

        # Patroon 3b: Begrip gevolgd door verboden woord (circulaire definitie)
        # Voorbeeld: "vonnis is een uitspraak" → matcht "vonnis is"
        # Regex: ^vonnis\s+is\b (\s+ = één of meer spaties)
        regex_lijst.append(rf"^{begrip_esc}\s+{w_esc}\b")

    # Patroon 3c: Extra patroon voor begrip als label, gevolgd door een
    # dubbelepunt of een los streepje. Voorbeelden: 'Vonnis:', 'vonnis -',
    # 'vonnis: '. Regex: ^vonnis\b(?:\s*:|\s+-)\s* — mét woordgrens en
    # verplícht scheidingsteken.
    # DEF-622: zonder die twee eisen sneed dit patroon het begrip als woorddeel
    # weg ("Controlehandeling die …" → "handeling die …") en verwijderde het een
    # bovenbegrip dat het begrip herhaalt ("Handeling die …" bij begrip
    # "handeling" → "die …"). Of zo'n herhaling circulair is, beoordeelt SAM-05.
    # Een streepje telt alleen als labelscheider met witruimte ervóór: een
    # koppelteken dat aan het begrip vastzit is een samenstelling of
    # samentrekking ("Controle-handeling", "Controle- en toezichtshandeling")
    # en draagt betekenis (reviewbevinding op batch 2).
    regex_lijst.append(rf"^{begrip_esc}\b(?:\s*:|\s+-)\s*")

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
