# Migratie Plan: Legacy core.py naar Modulaire Structuur

## Huidige Situatie

### Legacy Systeem (core.py)
- **47 toets functies** als losse functies
- **DISPATCHER dictionary** mapt regel IDs naar functies
- **Monolithisch bestand** van 2000+ regels
- **Moeilijk te testen** en onderhouden

### Nieuwe Modulaire Structuur
- **Validator classes** per regel in aparte bestanden
- **JSON + Python combinatie** voor flexibiliteit
- Al gemigreerd: CON (2), ESS (5), STR (9) = 16 regels

### Nog te Migreren
- ARAI regels (9 stuks)
- INT regels (9 stuks)
- SAM regels (8 stuks)
- VER regels (3 stuks)
- **Totaal: 29 regels**

## Migratie Strategie

### Fase 1: Hybrid Approach (HUIDIGE FASE)
1. **Behoud core.py** tijdelijk voor backward compatibility
2. **Gebruik modular_loader** die beide systemen ondersteunt
3. **Migreer regel voor regel** naar nieuwe structuur

### Fase 2: Volledige Migratie
1. **Maak Python modules** voor elke regel in `config/toetsregels/regels/`
2. **Update DISPATCHER** in core.py om nieuwe validators te gebruiken
3. **Test elke gemigreerde regel** uitgebreid

### Fase 3: Cleanup
1. **Verwijder legacy functies** uit core.py
2. **Update alle imports** naar nieuwe structuur
3. **Verwijder core.py** volledig

## Implementatie Aanpak

### Stap 1: Update toets_op_basis_van_regel

```python
# In core.py - update deze functie om beide systemen te ondersteunen
def toets_op_basis_van_regel(definitie, regel_id, regel, **kwargs):
    """Gebruik nieuwe validator als beschikbaar, anders legacy."""
    
    # Probeer eerst nieuwe modulaire systeem
    from config.toetsregels.modular_loader import get_modular_loader
    loader = get_modular_loader()
    
    if regel_id in loader.get_available_regels():
        # Gebruik nieuwe validator
        succes, melding, score = loader.validate_with_regel(
            regel_id, definitie, kwargs.get('begrip', ''), 
            context=kwargs
        )
        return melding
    
    # Fallback naar legacy
    if regel_id in DISPATCHER:
        func = DISPATCHER[regel_id]
        # ... aanroep legacy functie
```

### Stap 2: Migreer Regel voor Regel

Voor elke regel:

1. **Maak JSON configuratie** in `config/toetsregels/regels/REGEL-ID.json`
2. **Maak Python module** in `config/toetsregels/regels/REGEL_ID.py`
3. **Kopieer logica** uit core.py functie
4. **Test uitgebreid**
5. **Verwijder uit DISPATCHER** (optioneel in Fase 3)

### Voorbeeld Migratie: INT-01

#### 1. Maak INT-01.json
```json
{
  "id": "INT-01",
  "naam": "Logische consistentie",
  "uitleg": "Definitie moet logisch consistent zijn",
  "prioriteit": "hoog",
  ...
}
```

#### 2. Maak INT_01.py
```python
class INT01Validator:
    def __init__(self, config):
        self.config = config
        
    def validate(self, definitie, begrip, context=None):
        # Kopieer logica uit toets_INT_01
        # Pas aan voor nieuwe structuur
        return success, melding, score
```

## Voordelen van deze Aanpak

1. **Geen Breaking Changes**: Alles blijft werken tijdens migratie
2. **Geleidelijke Overgang**: Regel voor regel testen
3. **Rollback Mogelijk**: Legacy blijft beschikbaar
4. **Betere Structuur**: Elke regel in eigen bestand

## Tools om te Helpen

1. **create_regel_module.py**: Voor nieuwe regels
2. **migrate_legacy_rules.py**: Voor bulk migratie (met review)
3. **modular_loader.py**: Ondersteunt beide systemen

## Next Steps

1. ✅ Update `toets_op_basis_van_regel` voor hybrid approach
2. ⬜ Migreer INT regels (hoogste prioriteit)
3. ⬜ Migreer SAM regels
4. ⬜ Migreer ARAI regels
5. ⬜ Migreer VER regels
6. ⬜ Update alle tests
7. ⬜ Verwijder legacy code