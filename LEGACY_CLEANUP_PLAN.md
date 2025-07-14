# Legacy Code Cleanup Plan

## Doel
Verwijder/archiveer legacy modules die niet meer gebruikt worden na de succesvolle refactoring naar modulaire architectuur.

## Te Archiveren

### 1. **centrale_module_definitie_kwaliteit.py**
- **Locatie**: `src/centrale_module_definitie_kwaliteit.py`
- **Grootte**: 1,035 regels
- **Status**: Volledig vervangen door `src/main.py` + modulaire componenten
- **Actie**: Verplaats naar `src/legacy/` of verwijder

### 2. **Build Artifacts**
- `build/` directory
- `__pycache__` directories
- `.pyc` files

### 3. **Oude Scripts**
- `scripts/start_definitie_webinterface.command` (verwijst naar niet-bestaand bestand)

## Acties

```bash
# 1. Maak legacy directory
mkdir -p src/legacy

# 2. Verplaats oude module
mv src/centrale_module_definitie_kwaliteit.py src/legacy/

# 3. Update CLAUDE.md - verwijder backup referentie
# Verwijder de "Original Version (Backup)" sectie

# 4. Clean build artifacts
rm -rf build/
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# 5. Update/verwijder oude scripts
rm scripts/start_definitie_webinterface.command
```

## Verificatie

Na cleanup, test dat alles nog werkt:
```bash
# Test nieuwe versie
streamlit run src/main.py

# Run tests
pytest
```

## Voordelen
- Minder verwarring voor nieuwe developers
- Duidelijke codebase zonder duplicatie
- Kleinere repository size
- Geen "welke versie moet ik gebruiken?" vragen