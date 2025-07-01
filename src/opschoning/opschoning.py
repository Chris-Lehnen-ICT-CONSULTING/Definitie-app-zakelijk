import re
from config.config_loader import laad_verboden_woorden

# ✅ Geïsoleerde module voor opschoning van GPT-gegenereerde definities
# ✅ Verwijdert alle verboden aanhefconstructies, dwingt hoofdletter en punt af.

def opschonen(definitie: str, begrip: str) -> str:
    """
    ✅ Verwijdert herhaaldelijk alle verboden beginconstructies:
    - Koppelwerkwoorden (bijv. 'is', 'omvat', 'betekent')
    - Lidwoorden (bijv. 'de', 'het', 'een')
    - Cirkeldefinities (begrip + verboden woord of dubbelepunt)
    ✅ Dwingt daarna een hoofdletter en eindpunt af.
    """
    # ✅ 1. Voorbewerking: strip whitespace
    d = definitie.strip()

    # ✅ 2. Laad verboden woordenlijst (uit centrale config)
    config = laad_verboden_woorden()
    verboden_lijst = config.get("verboden_woorden", []) if isinstance(config, dict) else []

    # ✅ 3. Genereer regex-patronen voor alle verboden beginconstructies
    begrip_esc = re.escape(begrip.strip().lower())
    regex_lijst = []

    for woord in verboden_lijst:
        w = woord.strip().lower()
        if not w:
            continue
        w_esc = re.escape(w)

        # ✅ 3a. Exact woord aan het begin
        regex_lijst.append(rf"^{w_esc}\b")

        # ✅ 3b. Begrip gevolgd door verboden woord
        regex_lijst.append(rf"^{begrip_esc}\s+{w_esc}\b")

    # ✅ 3c. Extra patroon: begrip gevolgd door dubbelepunt of streepje
    regex_lijst.append(rf"^{begrip_esc}\s*[:\-]?\s*")
    # 💚 Vangt constructies zoals 'Vonnis:', 'vonnis -', 'vonnis :'

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
