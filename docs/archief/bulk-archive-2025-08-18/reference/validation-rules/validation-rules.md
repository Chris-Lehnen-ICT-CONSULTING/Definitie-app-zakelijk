# Validation Rules (Toetsregels) Documentation

## Overview

DefinitieAgent gebruikt 46 gespecialiseerde validatieregels om de kwaliteit van gegenereerde definities te waarborgen. Deze regels zijn gebaseerd op best practices voor het schrijven van juridische en overheidsdefinities.

## Regel Categorieën

### 1. ARAI - Artificiële Intelligentie Regels
Regels specifiek voor AI-gegenereerde content.

| Code | Naam | Beschrijving | Prioriteit |
|------|------|--------------|------------|
| ARAI01 | Geen AI-disclaimer | Verwijdert "als AI taalmodel" disclaimers | Verplicht |
| ARAI02 | Geen onzekerheid | Voorkomt termen als "mogelijk", "waarschijnlijk" | Verplicht |
| ARAI03 | Geen meta-opmerkingen | Verwijdert meta-commentaar over de taak | Verplicht |
| ARAI04 | Objectieve taal | Zorgt voor neutrale, objectieve formulering | Hoog |
| ARAI05 | Geen herhalingen | Voorkomt onnodige herhalingen | Medium |
| ARAI06 | Consistente stijl | Handhaaft consistente schrijfstijl | Medium |

### 2. SAM - Samenhang Regels
Zorgen voor logische samenhang en consistentie.

| Code | Naam | Beschrijving | Prioriteit |
|------|------|--------------|------------|
| SAM-01 | Geen cirkelredeneringen | Term mag niet in eigen definitie | Verplicht |
| SAM-02 | Logische structuur | Definitie moet logisch opgebouwd zijn | Verplicht |
| SAM-03 | Eenduidige betekenis | Geen ambiguïteiten of dubbelzinnigheden | Verplicht |
| SAM-04 | Complete definitie | Alle essentiële aspecten gedekt | Hoog |
| SAM-05 | Interne consistentie | Geen tegenstrijdigheden | Verplicht |
| SAM-06 | Taxonomische correctheid | Juiste hiërarchische relaties | Hoog |
| SAM-07 | Voorkeursterm gebruik | Gebruik officiële terminologie | Medium |
| SAM-08 | Contextuele relevantie | Past bij opgegeven context | Hoog |

### 3. STR - Structuur Regels
Waarborgen correcte grammaticale en syntactische structuur.

| Code | Naam | Beschrijving | Prioriteit |
|------|------|--------------|------------|
| STR-01 | Hoofdletter start | Begint met hoofdletter | Verplicht |
| STR-02 | Punt beëindiging | Eindigt met punt | Verplicht |
| STR-03 | Geen dubbele spaties | Enkele spaties tussen woorden | Medium |
| STR-04 | Correcte leestekens | Juist gebruik van komma's etc. | Hoog |
| STR-05 | Alinea structuur | Logische alinea indeling | Medium |
| STR-06 | Maximale lengte | Niet langer dan 500 woorden | Medium |
| STR-07 | Minimale lengte | Minimaal 20 woorden | Medium |
| STR-08 | Genus vorm | "Een" of "het" correct gebruikt | Verplicht |
| STR-09 | Nederlandse spelling | Officiële spelling regels | Verplicht |

### 4. ESS - Essentiële Inhoud
Waarborgen dat kerninhoud aanwezig is.

| Code | Naam | Beschrijving | Prioriteit |
|------|------|--------------|------------|
| ESS-01 | Bevat definiendum | Term komt voor in definitie | Verplicht |
| ESS-02 | Onderscheidend kenmerk | Unieke eigenschappen benoemd | Verplicht |
| ESS-03 | Context appropriaat | Past bij juridische/overheidscontext | Hoog |
| ESS-04 | Geen voorbeelden | Voorbeelden in aparte sectie | Medium |
| ESS-05 | Actief taalgebruik | Bij voorkeur actieve vorm | Medium |

### 5. INT - Interne Consistentie
Consistentie binnen het systeem.

| Code | Naam | Beschrijving | Prioriteit |
|------|------|--------------|------------|
| INT-01 | Term overeenkomst | Term in DB = term in definitie | Verplicht |
| INT-02 | Context match | Context consistent toegepast | Hoog |
| INT-03 | Stijl consistentie | Uniforme stijl met andere definities | Medium |
| INT-04 | Relatie correctheid | Verwijzingen naar andere termen kloppen | Hoog |
| INT-06 | Metadata volledigheid | Alle verplichte metadata aanwezig | Medium |
| INT-07 | Versie tracking | Versie info correct | Low |
| INT-08 | Bron vermelding | Bronnen correct vermeld | Medium |
| INT-09 | Datum formaat | Consistent datum formaat | Low |
| INT-10 | Taal consistentie | Volledig Nederlands | Verplicht |

### 6. CON - Context Regels
Contextspecifieke validaties.

| Code | Naam | Beschrijving | Prioriteit |
|------|------|--------------|------------|
| CON-01 | Juridisch taalgebruik | Passend voor juridische context | Hoog |
| CON-02 | Domein terminologie | Correcte vakterminologie | Hoog |

### 7. VER - Verboden Content
Detectie van ongewenste inhoud.

| Code | Naam | Beschrijving | Prioriteit |
|------|------|--------------|------------|
| VER-01 | Geen verboden woorden | Lijst met uitgesloten termen | Verplicht |
| VER-02 | Geen discriminatie | Neutrale, inclusieve taal | Verplicht |
| VER-03 | Geen persoonlijke data | Privacy waarborging | Verplicht |

## Implementatie Details

### Validator Interface

```python
class BaseValidator:
    def __init__(self):
        self.code = "XXX-00"
        self.name = "Validator Name"
        self.category = "Category"
        self.priority = "medium"

    def validate(self, definition: str, term: str, context: dict) -> ValidationResult:
        """
        Returns:
            ValidationResult(
                passed=bool,
                message=str,
                severity=str,
                details=dict
            )
        """
        pass
```

### Prioriteit Levels

1. **Verplicht**: Moet slagen voor valide definitie
2. **Hoog**: Sterk aanbevolen, waarschuwing bij falen
3. **Medium**: Kwaliteitsverbetering, informatief
4. **Laag**: Nice-to-have, optimalisatie

### Score Berekening

```python
def calculate_score(results: List[ValidationResult]) -> int:
    weights = {
        "verplicht": 3.0,
        "hoog": 2.0,
        "medium": 1.0,
        "laag": 0.5
    }

    total_weight = sum(weights[r.priority] for r in results)
    passed_weight = sum(weights[r.priority] for r in results if r.passed)

    return int((passed_weight / total_weight) * 100)
```

## Configuratie

### Rule Sets

Voorgedefinieerde sets voor verschillende use cases:

```json
{
    "strict": ["verplicht", "hoog"],
    "balanced": ["verplicht", "hoog", "medium"],
    "comprehensive": ["verplicht", "hoog", "medium", "laag"],
    "minimal": ["verplicht"]
}
```

### Context-Specifieke Rules

```json
{
    "juridisch": ["CON-01", "VER-01", "VER-02", "SAM-07"],
    "technisch": ["STR-*", "SAM-*", "INT-*"],
    "algemeen": ["ARAI-*", "STR-*", "ESS-*"]
}
```

## Gebruik in Code

```python
from ai_toetsing.toetsing_service import ToetsingService

# Initialize service
toetsing = ToetsingService()

# Validate with all rules
result = toetsing.validate_definition(
    definition="Authenticatie is het proces...",
    term="authenticatie",
    context={"type": "juridisch"}
)

# Validate with specific rules
result = toetsing.validate_definition(
    definition="...",
    term="...",
    rules=["SAM-01", "STR-01", "STR-02"]
)

# Get rule info
rule_info = toetsing.get_rule_info("SAM-01")
```

## Custom Validators

### Toevoegen nieuwe validator:

1. Maak JSON configuratie in `src/toetsregels/regels/`:
```json
{
    "code": "CUS-01",
    "name": "Custom Validator",
    "category": "Custom",
    "description": "Beschrijving van de regel",
    "priority": "medium",
    "enabled": true
}
```

2. Implementeer validator in `src/toetsregels/validators/`:
```python
from .base import BaseValidator

class CUS_01(BaseValidator):
    def validate(self, definition, term, context):
        # Implementatie
        return ValidationResult(...)
```

## Monitoring & Metrics

### Validation Statistics

- Meest falende regels
- Gemiddelde score per categorie
- Trend analyse over tijd
- Performance metrics per regel

### Logging

```python
{
    "timestamp": "2025-01-17T10:30:00Z",
    "definition_id": 123,
    "total_rules": 46,
    "passed": 42,
    "failed": 4,
    "score": 91,
    "duration_ms": 245,
    "failed_rules": ["VER-02", "SAM-04", "INT-03", "STR-06"]
}
```

## Best Practices

1. **Regel volgorde**: Verplichte regels eerst voor snelle feedback
2. **Caching**: Cache regel resultaten voor identieke input
3. **Parallellisatie**: Voer onafhankelijke regels parallel uit
4. **Graceful degradation**: Systeem blijft werken als enkele validators falen
5. **Feedback kwaliteit**: Geef concrete, actionable feedback messages
