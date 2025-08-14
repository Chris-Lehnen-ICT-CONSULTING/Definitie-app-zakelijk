# Legacy Validatie Toetsregels Module

**Gearchiveerd op:** 2025-01-16  
**Reden:** Incompatibel met nieuwe modulaire architectuur

## Waarom gearchiveerd?

Deze module was een development/QA tool die:
1. Controleerde of alle JSON toetsregels een Python implementatie hadden
2. Verwachtte alle `toets_*` functies in één monolithisch `ai_toetser.py` bestand
3. Niet compatibel is met de nieuwe modulaire structuur waar elke regel zijn eigen module heeft

## Originele functionaliteit

- `laad_json_ids()` - Laadde regel IDs uit JSON configuratie
- `detecteer_functies_in_toetser()` - Zocht naar `toets_*` functies in Python code
- `valideer_toetsregels()` - Vergeleek JSON regels met Python implementaties

## Vervanging

De functionaliteit is gedeeltelijk gekopieerd naar `src/validation/definitie_validator.py` 
in de functie `valideer_toetsregels_consistentie()`, maar deze moet nog gerefactord worden
voor de nieuwe modulaire architectuur.

## Nieuwe architectuur

In de nieuwe architectuur:
- Elke toetsregel heeft zijn eigen module in `/config/toetsregels/regels/`
- Validators zijn classes, geen functies
- JSON en Python files staan naast elkaar (bijv. `ARAI01.json` en `ARAI01.py`)