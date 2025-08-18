# INT-01 Migratie Voorbeeld

Dit document toont het volledige migratieproces van een legacy toetsregel (INT-01) naar de nieuwe modulaire structuur.

## Uitgangssituatie

### Legacy Code (core.py)
```python
def toets_INT_01(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    complexiteit_gevonden = set()
    for patroon in patroon_lijst:
        complexiteit_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))
    
    # ... rest van de logica
```

### Bestaande JSON (INT-01.json)
De JSON configuratie bestond al in `src/config/toetsregels/regels/INT-01.json` met:
- Regel metadata (naam, uitleg, prioriteit)
- Herkenbare patronen voor complexiteit
- Goede en foute voorbeelden

## Migratiestappen

### 1. Python Module Maken
Creëer `src/config/toetsregels/regels/INT_01.py` (let op underscore ipv dash):

```python
class INT01Validator:
    def __init__(self, config: Dict):
        """Initialiseer met JSON config."""
        self.config = config
        self.compile_patterns()  # Pre-compile regex voor performance
    
    def validate(self, definitie: str, begrip: str, 
                context: Optional[Dict] = None) -> Tuple[bool, str, float]:
        """Valideer volgens INT-01 regel."""
        # Migreer legacy logica hier
```

### 2. Legacy Logica Migreren
- Kopieer de kern van `toets_INT_01` naar de `validate` methode
- Pas return waarden aan: `(bool, str, float)` ipv alleen string
- Voeg score berekening toe voor genuanceerde feedback

### 3. Factory Functie Toevoegen
```python
def create_validator(config_path: str = None) -> INT01Validator:
    """Factory om validator te maken."""
    # Laad JSON config en maak validator
```

## Test Resultaten

De nieuwe implementatie geeft exact dezelfde resultaten:

### Legacy Output
```
✔️ INT-01: geen complexe elementen herkend – mogelijk goed geformuleerd
❌ INT-01: complexe elementen gevonden (,, die, waarbij), maar geen expliciet fout voorbeeld herkend
```

### Nieuwe Module Output
```
✔️ INT-01: geen complexe elementen herkend – mogelijk goed geformuleerd (score: 0.9)
❌ INT-01: complexe elementen gevonden (,, die, waarbij), maar geen expliciet fout voorbeeld herkend (score: 0.4)
```

## Hybrid Approach

De `toets_op_basis_van_regel` functie in core.py ondersteunt nu beide systemen:

1. **Eerst**: Probeert nieuwe modulaire validator
2. **Fallback**: Gebruikt legacy functie als nieuwe niet bestaat

Dit maakt geleidelijke migratie mogelijk zonder breaking changes.

## Voordelen Nieuwe Structuur

1. **Scheiding van concerns**: JSON config vs Python logica
2. **Testbaarheid**: Elke regel kan individueel getest worden
3. **Performance**: Pre-compiled regex patterns
4. **Flexibiliteit**: Score-based feedback ipv alleen pass/fail
5. **Herbruikbaarheid**: `get_generation_hints()` voor AI prompts

## Volgende Stappen

Voor de resterende 28 legacy regels:
1. Gebruik `create_regel_module.py` script voor basis structuur
2. Kopieer legacy logica naar nieuwe validator class
3. Test uitgebreid met bestaande test cases
4. Verwijder legacy functie pas na verificatie

## Commando's

```bash
# Maak nieuwe regel module
cd src/config/toetsregels
python create_regel_module.py REGEL-ID "Naam" "Uitleg"

# Test specifieke regel
python test_int01_migration.py

# Bekijk alle beschikbare regels
python -c "from modular_loader import get_modular_loader; print(get_modular_loader().get_available_regels())"
```