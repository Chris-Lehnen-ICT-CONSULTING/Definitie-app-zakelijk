# Vergelijking: Actieve vs Backup Validators

## 📊 Overzicht

### Actieve Validators (16 stuks)
**Locatie**: `/src/ai_toetser/validators/`
- CON-01, CON-02
- ESS-01 t/m ESS-05
- STR-01 t/m STR-09

### Backup Validators (45 stuks)
**Locatie**: `/src/config/toetsregels/regels_backup_20250716_153755/`
- Alle 45 toetsregels met JSON + Python implementaties
- ARAI01-06, CON_01-02, ESS_01-05, INT_01-10, SAM_01-08, STR_01-09, VER_01-03

## 🔍 Architectuur Verschillen

### Backup Validators (Oude Architectuur)
```python
class CON01Validator:
    def __init__(self, config: Dict):
        # Configuratie uit JSON wordt meegegeven
        self.config = config
        self.id = config.get('id', 'CON-01')
        
    def validate(self, definitie: str, begrip: str, context: Optional[Dict] = None) -> Tuple[bool, str, float]:
        # Retourneert tuple: (success, message, score)
```

**Kenmerken**:
- Krijgt JSON config in constructor
- Simpele validate() signature
- Retourneert tuple (bool, string, float)
- Directe koppeling met JSON bestand
- Underscore naming: `CON_01.py`

### Actieve Validators (Nieuwe Architectuur)
```python
class CON01Validator(BaseValidator):
    def __init__(self):
        super().__init__(
            rule_id="CON-01",
            name="...",
            description="..."
        )
        
    def validate(self, context: ValidationContext) -> ValidationOutput:
        # Retourneert ValidationOutput object
```

**Kenmerken**:
- Erft van BaseValidator
- Geen directe JSON dependency
- ValidationContext object als input
- ValidationOutput object als output
- Hyphen naming: `CON-01` (in rule_id)
- Geregistreerd in ValidationRegistry

## 📈 Coverage Analyse

### Wat ontbreekt in Actieve Validators:
1. **ARAI regels** (9 stuks) - AI/Automatisering gerelateerd
2. **INT regels** (8 van 10) - Interpretatie regels
3. **SAM regels** (8 stuks) - Samenhang regels
4. **VER regels** (3 stuks) - Vergelijking regels

### Volledig geïmplementeerd:
- ✅ CON regels (2/2)
- ✅ ESS regels (5/5)
- ✅ STR regels (9/9)

## 🔄 Migratie Status

De backup validators gebruiken een **directe JSON-gekoppelde architectuur** waarbij:
- Elke validator zijn config uit JSON haalt
- Validators direct worden aangeroepen met parameters
- Output is een simpele tuple

De actieve validators gebruiken een **modulaire registry architectuur** waarbij:
- Validators onafhankelijk zijn van JSON
- Context wordt doorgegeven via ValidationContext object
- Output is een rijk ValidationOutput object
- Validators worden geregistreerd in een centrale registry

## 💡 Conclusie

Er zijn twee complete maar verschillende implementaties:
1. **45 backup validators** - Oude architectuur, direct JSON-gekoppeld
2. **16 actieve validators** - Nieuwe modulaire architectuur

De 29 ontbrekende validators in het actieve systeem worden waarschijnlijk nog steeds uitgevoerd via de legacy `core.py`, die de oude tuple-based interface gebruikt.