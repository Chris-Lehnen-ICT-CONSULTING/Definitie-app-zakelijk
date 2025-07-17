# Gearchiveerd: validatie_toetsregels

## Archiveringsdatum
17 januari 2025

## Reden voor archivering
Deze module is obsoleet en vervangen door de modulaire validator architectuur in `src/ai_toetser/validators/`.

## Wat deed deze module?
- Controleerde consistentie tussen JSON toetsregels en Python implementaties
- Valideerde of elke JSON regel een corresponderende Python functie had
- Quality assurance tool voor development, NIET voor runtime gebruik

## Vervangen door
- `src/ai_toetser/modular_toetser.py` - Voor runtime toetsing
- `src/config/toetsregel_manager.py` - Voor regel beheer
- `src/validation/definitie_validator.py` - Voor definitie validatie met scoring

## Originele functionaliteit
- `validator.py`: Bevatte `valideer_toetsregels_consistentie()` functie
- `__init__.py`: Exporteerde validator functionaliteit

## Waarom gearchiveerd?
1. Duplicatie met nieuwe modulaire architectuur
2. Verouderde aanpak (monolithisch)
3. Verwarring door 3 verschillende validatie mappen
4. Functionaliteit is overgenomen door betere tools

## Migratie notities
Als je de consistentie check functionaliteit nodig hebt, gebruik dan:
```python
from validation.definitie_validator import valideer_modulaire_toetsregels_consistentie
```

Deze nieuwe functie doet hetzelfde maar voor de modulaire architectuur.