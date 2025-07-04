import re

def zoek_wetsartikelstructuur(tekst):
    """
    ✅ Herkent gestructureerde verwijzingen naar wetsartikelen zoals:
       'Wetboek van Strafvordering, boek 1, artikel 15 lid 3'
       en retourneert een lijst van dicts met: wet, boek, artikel, lid.
    """
    patroon = re.compile(
        r'(?P<wet>Wetboek van [A-Z][a-z]+)(?:,\s*boek\s*(?P<boek>[0-9]+))?,?\s*artikel\s*(?P<artikel>[0-9a-zA-Z]+)(?:\s*lid\s*(?P<lid>[0-9]+))?',
        re.IGNORECASE
    )
    resultaten = []
    for match in patroon.finditer(tekst):
        resultaten.append({
            'wet': match.group('wet'),
            'boek': match.group('boek'),
            'artikel': match.group('artikel'),
            'lid': match.group('lid'),
        })
    return resultaten