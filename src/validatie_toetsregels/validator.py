# 🔧 Bestand: validatie_toetsregels.py
# 📍 Locatie: vervang bestaande functie lade_json_ids
import os
import re
from typing import Dict, Any
from config.config_loader import load_toetsregels  # ✅ Centrale JSON‐loader

def laad_json_ids(path: str = None) -> Dict[str, Dict[str, Any]]:
    """
    💚 Laadt de volledige toetsregels via de centrale loader.
    💚 Retourneert het sub‐dict 'regels' uit het JSON‐object.
    """
    # ✅ Als er een specifiek pad is opgegeven, gebruik dat; anders de default.
    data = load_toetsregels(path) if path else load_toetsregels()
    # ✅ Haal de regels‐sectie eruit
    return data.get("regels", {})

# ✅ Detecteert toetsfuncties zoals toets_CON_01 en zet om naar ID-vorm zoals CON-01
def detecteer_functies_in_toetser(python_pad: str) -> set:
    with open(python_pad, "r", encoding="utf-8") as f:
        inhoud = f.read()
    matches = re.findall(r"def\s+toets_([A-Z0-9_]+)\s*\(", inhoud)
    return {match.replace("_", "-") for match in matches}

# ✅ Voert validatie uit en toont overzichtelijk rapport
def valideer_toetsregels(json_pad: str, python_pad: str) -> None:
    json_regels = laad_json_ids(json_pad)
    code_ids = detecteer_functies_in_toetser(python_pad)

    print("\n📊 VALIDATIERAPPORT TOETSREGELS\n")

    # 🟥 Ontbrekende functies
    ontbrekend_in_code = [rid for rid in json_regels if rid not in code_ids]
    if ontbrekend_in_code:
        print("🟥 Ontbrekende functies in ai_toetser.py:")
        for rid in ontbrekend_in_code:
            print(f" - {rid}")
    else:
        print("✅ Alle regels hebben een bijbehorende functie in ai_toetser.py.\n")

    # 🟨 Onvolledige regels in JSON
    for rid, data in json_regels.items():
        ontbreekt = []
        if "uitleg" not in data or not isinstance(data["uitleg"], str) or not data["uitleg"].strip():
            ontbreekt.append("❌ uitleg ontbreekt")
        if "herkenbaar_patronen" not in data or not data["herkenbaar_patronen"]:
            ontbreekt.append("❌ herkenbare patronen ontbreken")
        if ontbreekt:
            print(f"🟨 Onvolledig in JSON voor {rid}: {' | '.join(ontbreekt)}")

    # 🟩 Volledig consistente regels
    correct = [
        rid for rid in json_regels
        if rid in code_ids
        and isinstance(json_regels[rid].get("uitleg"), str) and json_regels[rid]["uitleg"].strip()
        and "herkenbaar_patronen" in json_regels[rid] and json_regels[rid]["herkenbaar_patronen"]
    ]
    totaal = len(json_regels)
    percentage = round(100 * len(correct) / totaal, 1)
    print(f"\n✅ Volledig consistente regels: {len(correct)} van {totaal} ({percentage}%)")

# ✅ Script starten
if __name__ == "__main__":
    pad_json = "toetsregels.json"
    pad_code = "ai_toetser.py"

    if not os.path.exists(pad_json) or not os.path.exists(pad_code):
        print("❌ Bestand ontbreekt. Controleer of toetsregels.json en ai_toetser.py bestaan.")
    else:
        valideer_toetsregels(pad_json, pad_code)
