# Legacy AI Toetser Code

Deze directory bevat de legacy implementatie van de AI toetser module die is vervangen door het nieuwe modulaire systeem.

## Gearchiveerde bestanden

### core.py
- Oorspronkelijke monolithische implementatie van alle toetsregels
- Bevatte alle 45+ toetsregels in één groot bestand
- Gebruikte hardcoded logica zonder configuratie mogelijkheden

### centrale_module_definitie_kwaliteit.py
- De oude centrale module die alle definitie kwaliteit functionaliteit bevatte
- Monolithisch bestand met 1000+ regels code
- Mengde generatie, validatie en UI logica

## Migratie naar nieuw systeem

Deze bestanden zijn vervangen door:
- `/src/ai_toetser/modular_toetser.py` - Nieuwe modulaire toetser
- `/src/config/toetsregels/` - JSON configuratie bestanden
- `/src/config/toetsregels/regels/` - Individuele Python validator modules

## Datum van archivering
16 januari 2025

De legacy code wordt niet meer gebruikt in het actieve systeem.