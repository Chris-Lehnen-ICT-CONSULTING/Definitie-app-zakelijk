# Gearchiveerde Migratie Scripts

Deze directory bevat de scripts die zijn gebruikt voor de migratie van het legacy toetsing systeem naar de nieuwe modulaire architectuur.

## Gearchiveerde bestanden

### migrate_legacy_rules.py
- Script om legacy toets functies uit core.py te migreren naar modulaire validator classes
- Extraheerde functie logica uit de monolithische core.py
- Genereerde nieuwe Python validator modules

### migrate_all_rules.py
- Bulk migratie script voor alle toetsregels
- Converteerde alle 46 toetsregels naar het nieuwe systeem

### MIGRATION_PLAN.md
- Documentatie van het migratie plan
- Beschrijft de stappen van legacy naar modulair systeem

### create_regel_module.py
- Helper script om nieuwe regel modules te maken
- Genereerde boilerplate code voor validators

## Status
De migratie is **volledig afgerond** op 16 januari 2025. Alle toetsregels zijn succesvol gemigreerd naar:
- JSON configuratie bestanden in `/src/config/toetsregels/`
- Python validator modules in `/src/config/toetsregels/regels/`

Deze scripts worden niet meer gebruikt maar zijn bewaard voor historische referentie.

## Let op
Deze scripts verwijzen naar `core.py` die nu in `/archive/legacy_ai_toetser/` staat.
Als je deze scripts om een of andere reden wilt gebruiken, moet je de paden aanpassen.
