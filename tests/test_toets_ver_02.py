from ai_toetser.core import toets_VER_02
from web_lookup.lookup import is_plurale_tantum

regel = {
    "herkenbaar_patronen": [r"\b\w+en zijn\b"],
    "goede_voorbeelden": ["natuurlijke persoon die wordt vertegenwoordigd"],
    "foute_voorbeelden": ["natuurlijke personen die ..."]
}

# 1. Plurale tantum uitzondering
assert toets_VER_02("…", regel, term="kosten").startswith("✔️ VER-02")  

# 2. Foute voorbeeld
foutzin = "natuurlijke personen die …"
assert toets_VER_02(foutzin, regel, term="natuurlijke persoon").startswith("❌ VER-02")

# 3. Goede voorbeeld
goedzin = "natuurlijke persoon die wordt vertegenwoordigd"
assert toets_VER_02(goedzin, regel, term="natuurlijke personen").startswith("✔️ VER-02")

# 4. Patronen
zin = "Gegevens zijn feiten en getallen."
assert toets_VER_02(zin, regel, term="gegeven").startswith("❌ VER-02")

# 5. Fallback
zin = "Natuurlijke persoon die gerechtigd is."
assert toets_VER_02(zin, regel, term="natuurlijke persoon").startswith("✔️ VER-02")