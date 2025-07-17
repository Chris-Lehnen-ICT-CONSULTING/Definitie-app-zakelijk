# Nieuwe Toetsregels Structuur

## 📁 Directory Structuur

```
src/
├── toetsregels/                # Alles m.b.t. toetsregels
│   ├── __init__.py            # Package exports
│   ├── manager.py             # ToetsregelManager (was config/toetsregel_manager.py)
│   ├── loader.py              # Laadt toetsregels uit individuele bestanden
│   ├── adapter.py             # Legacy adapter (was config/toetsregels_adapter.py)
│   ├── regels/                # JSON configuratie bestanden
│   │   ├── CON-01.json
│   │   ├── ESS-01.json
│   │   └── ... (45 JSON files)
│   └── validators/            # Python implementaties
│       ├── __init__.py
│       ├── CON_01.py
│       ├── ESS_01.py
│       └── ... (45 Python files)
│
├── ai_toetser/
│   ├── modular_toetser.py    # Gebruikt JSONValidatorLoader
│   └── json_validator_loader.py # Laadt validators dynamisch
│
└── config/                    # Alleen echte configuratie
    ├── config_loader.py       # Compatibility layer (DEPRECATED)
    └── verboden_woorden.json  # Blijft hier (is echte config)
```

## 🗑️ Verwijderd/Gearchiveerd

1. **toetsregels.json** - Monolithisch bestand met alle 45 regels
   - Gearchiveerd naar: `archive/legacy_toetsregels/`
   
2. **BaseValidator architectuur** - Te rigide voor flexibele regels
   - Gearchiveerd naar: `archive/basevalidator_architecture/`

3. **Backup directory** - Niet meer nodig
   - Verwijderd: `regels_backup_20250716_153755/`

## ✅ Voordelen Nieuwe Structuur

1. **Scheiding van verantwoordelijkheden**
   - Config (JSON) gescheiden van implementatie (Python)
   - Toetsregels uit config directory gehaald

2. **Flexibiliteit**
   - Elke regel kan eigen velden hebben
   - Geen verplichte structuur

3. **Onderhoudbaarheid**
   - Makkelijk nieuwe regels toevoegen
   - Duidelijke locatie voor alles

4. **Performance**
   - Alleen benodigde validators worden geladen
   - Caching in ToetsregelManager

## 🔄 Migratie

Voor bestaande code:
```python
# Oud (werkt nog via compatibility layer)
from config.config_loader import laad_toetsregels

# Nieuw (aanbevolen)
from toetsregels import load_toetsregels
```

## 📝 Nieuwe Toetsregel Toevoegen

1. Maak JSON bestand: `src/toetsregels/regels/NEW-01.json`
2. Maak Python validator: `src/toetsregels/validators/NEW_01.py`
3. Klaar! Wordt automatisch geladen

## ⚠️ Let Op

- De oude `config_loader.py` is een compatibility layer
- Nieuwe code moet `from toetsregels import ...` gebruiken
- JSON en Python bestanden moeten matching namen hebben (NEW-01 → NEW_01)