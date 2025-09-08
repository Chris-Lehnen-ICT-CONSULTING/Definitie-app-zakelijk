# Toetsregels Module Guide

## Overzicht

Elke toetsregel in DefinitieAgent bestaat uit twee delen:
1. **JSON configuratie** - Metadata, patronen en voorbeelden
2. **Python module** - Specifieke validatie logica (optioneel)

## Structuur

V2 gebruikt primair JSON‑regels via de ToetsregelManager. Python validators zijn optioneel en leven in een aparte map.

```
src/toetsregels/
├── regels/
│   ├── ESS-03.json          # JSON configuratie (canoniek voor V2)
│   ├── CON-01.json          # Alleen JSON (fallback pattern‑based)
│   └── ...
└── validators/
    ├── ESS_03.py            # Python validator (underscores)
    ├── CON_01.py            # Python validator (underscores)
    └── ...
```

Let op naamgeving:
- JSON: koppeltekens (bijv. `ESS-03.json`).
- Python: underscores (bijv. `ESS_03.py`) in de map `validators/`.

## Nieuwe Toetsregel Maken

### Automatisch met Script

```bash
cd src/toetsregels
python create_regel_module.py TEST-01 "Test regel naam" "Uitleg van de regel"
```

Dit maakt:
- `regels/TEST-01.json` - Basis configuratie
- `regels/TEST_01.py` - Python module template

### JSON Configuratie

```json
{
  "id": "TEST-01",
  "naam": "Korte beschrijving van de regel",
  "uitleg": "Wat deze regel controleert",
  "toelichting": "Uitgebreide uitleg en context",
  "toetsvraag": "Vraag die met ja/nee beantwoord kan worden",
  "herkenbaar_patronen": [
    "\\bpatroon1\\b",
    "\\bpatroon2\\b"
  ],
  "goede_voorbeelden": [
    "Voorbeeld van goede definitie",
    "Nog een goed voorbeeld"
  ],
  "foute_voorbeelden": [
    "Voorbeeld van foute definitie"
  ],
  "prioriteit": "hoog|midden|laag",
  "aanbeveling": "verplicht|aanbevolen|optioneel",
  "geldigheid": "algemeen|specifiek domein",
  "status": "concept|definitief",
  "type": "essentie|structuur|content|integriteit",
  "thema": "thema van de regel",
  "brondocument": "ASTRA|eigen",
  "relatie": []
}
```

### Python Module (optioneel)

De Python validator geeft je volledige controle over de validatie logica en wordt door UI‑detailvalidatie gebruikt. V2‑service kan deze ook via een adapter benutten.

```python
class TEST01Validator:
    def __init__(self, config: Dict):
        """Initialiseer met JSON config."""
        self.config = config

    def validate(self, definitie: str, begrip: str,
                context: Optional[Dict] = None) -> Tuple[bool, str, float]:
        """
        Valideer de definitie.

        Returns:
            - bool: Success (True/False)
            - str: Melding voor gebruiker
            - float: Score (0.0 - 1.0)
        """
        # Complexe validatie logica hier
        if self._check_complex_rule(definitie):
            return True, f"✔️ {self.id}: Regel voldaan", 1.0
        else:
            return False, f"❌ {self.id}: {self.uitleg}", 0.0

    def get_generation_hints(self) -> List[str]:
        """Geef hints voor AI generatie."""
        return ["Hint 1", "Hint 2"]
```

## Validatie Logica Patterns

### 1. Context-Afhankelijke Validatie

```python
def validate(self, definitie: str, begrip: str, context: Optional[Dict] = None):
    # Check context
    if context and context.get('categorie') == 'proces':
        # Speciale logica voor processen
        return self._validate_proces(definitie)
    else:
        # Standaard validatie
        return self._validate_standaard(definitie)
```

### 2. Geavanceerde Pattern Matching

```python
def validate(self, definitie: str, begrip: str, context: Optional[Dict] = None):
    # Meerdere patronen met verschillende scores
    patterns = [
        (r'\buniek\s+identificatie', 1.0, "Expliciete unieke ID"),
        (r'\b(individueel|specifiek)\b', 0.8, "Impliciete uniciteit"),
        (r'\b(onderscheidbaar|herkenbaar)\b', 0.6, "Zwakke indicatie")
    ]

    for pattern, score, beschrijving in patterns:
        if re.search(pattern, definitie, re.IGNORECASE):
            return True, f"✔️ {self.id}: {beschrijving}", score

    return False, f"❌ {self.id}: Geen unieke identificatie", 0.0
```

### 3. Semantische Analyse

```python
def validate(self, definitie: str, begrip: str, context: Optional[Dict] = None):
    # Tel belangrijke concepten
    concepten = self._extract_concepten(definitie)

    score = len(concepten) / 5.0  # Normaliseer naar 0-1
    score = min(score, 1.0)

    if score > 0.6:
        return True, f"✔️ Voldoende concepten: {', '.join(concepten)}", score
    else:
        return False, f"❌ Te weinig concepten", score
```

## V2 Validatie en Testen

### V2 Service (ModularValidationService)
- Laadt JSON‑regels via de ToetsregelManager.
- Kan uitgebreid worden OM Python validators via een module‑adapter te evalueren.
- Geeft schema‑conforme resultaten terug (overall_score, violations, enz.).

### Unit Test Template (validators)

```python
# tests/test_toetsregel_TEST_01.py
import pytest
from toetsregels.modular_loader import validate_met_regel

def test_test01_success():
    """Test succesvolle validatie."""
    definitie = "Een test is een voorbeeld met unieke ID"
    succes, melding, score = validate_met_regel("TEST-01", definitie, "test")

    assert succes == True
    assert score > 0.8
    assert "✔️" in melding

def test_test01_failure():
    """Test gefaalde validatie."""
    definitie = "Een test is iets"
    succes, melding, score = validate_met_regel("TEST-01", definitie, "test")

    assert succes == False
    assert score < 0.5
    assert "❌" in melding
```

### Interactief Testen

```python
# Test een specifieke regel
from toetsregels.modular_loader import get_modular_loader

loader = get_modular_loader()
succes, melding, score = loader.validate_with_regel(
    "ESS-03",
    "Een auto is een voertuig met kenteken ABC-123",
    "auto"
)
print(f"{melding} (score: {score})")
```

## Best Practices

1. **Start Simpel**: Begin met pattern matching in JSON, voeg Python toe als nodig
2. **Hergebruik Patronen**: Gebruik `self.compiled_patterns` voor performance
3. **Duidelijke Meldingen**: Geef specifieke feedback wat er mis is
4. **Scores Gebruiken**: Gebruik scores (0-1) voor graduele validatie
5. **Context Bewust**: Gebruik context voor slimmere validatie
6. **Test Driven**: Schrijf tests voordat je de validator implementeert

## Troubleshooting

### Regel wordt niet geladen
- Check of JSON bestand bestaat in `regels/` directory
- Controleer JSON syntax met `python -m json.tool regels/REGEL-ID.json`

### Python module wordt niet gebruikt
- Bestandsnaam moet overeenkomen: `ESS-03.json` → `ESS_03.py`
- Check class naam: `ESS03Validator` of `create_validator` functie

### Validatie werkt niet
- Check logs voor regex fouten
- Test patronen met https://regex101.com
- Gebruik debugger in validate() methode
---
canonical: true
status: active
owner: validation
last_verified: 02-09-2025
applies_to: definitie-app@v2
---
