# Maintenance Tools

Deze directory bevat onderhoudsscripts voor het DefinitieAgent project.

## Scripts

### fix_naming_consistency.py
**Doel:** Harmoniseer bestandsnamen tussen JSON en Python files
**Wanneer gebruikt:** 2025-01-16 - Om inconsistentie tussen dash (-) en underscore (_) op te lossen
**Status:** ✅ Voltooid - Kan hergebruikt worden indien nodig

#### Gebruik:
```bash
# Dry run (toont wat er zou gebeuren)
python tools/maintenance/fix_naming_consistency.py

# Daadwerkelijk uitvoeren
python tools/maintenance/fix_naming_consistency.py --execute
```

#### Wat het doet:
1. Maakt backup van huidige regels directory
2. Hernoemt JSON files van dash (-) naar underscore (_) notatie
3. Update ID's binnen JSON files om overeen te komen
4. Toont rapport van wijzigingen

## Richtlijnen voor nieuwe scripts

1. **Altijd dry-run mode** als default
2. **Maak backups** voor destructieve operaties
3. **Documenteer** wanneer en waarom het script is gebruikt
4. **Test grondig** voor productie gebruik
5. **Bewaar scripts** voor toekomstige referentie

## Script categorieën

- `fix_*.py` - Eenmalige fixes voor specifieke problemen
- `check_*.py` - Validatie en controle scripts
- `migrate_*.py` - Migratie scripts voor structurele wijzigingen
- `clean_*.py` - Opruim scripts voor maintenance
