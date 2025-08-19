from ai_toetser.core import toets_VER_02

regel = {
    "foute_voorbeelden": ["natuurlijke personen die ..."],
    "goede_voorbeelden": ["natuurlijke persoon die wordt vertegenwoordigd"],
    "herkenbaar_patronen": [r"\b\w+en zijn\b"],
}
foutzin = "natuurlijke personen die …"  # met Unicode-ellipsis

assert toets_VER_02(foutzin, regel, term="natuurlijke persoon").startswith("❌ VER-02")
assert toets_VER_02(
    "natuurlijke persoon die …", regel, term="natuurlijke persoon"
).startswith("✔️ VER-02")
