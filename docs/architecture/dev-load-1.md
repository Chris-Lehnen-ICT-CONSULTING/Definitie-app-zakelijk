# Dev Load 1: Core Business Logic & Models

## Overview

Dit document bevat essentiële business logic informatie voor AI agents om snel context te krijgen over de kernfunctionaliteit van DefinitieAgent.

## Core Business Concepts

### 1. Definitie Generatie

Het hart van de applicatie is het genereren van Nederlandse definities voor juridische en overheidstermen.

**Kernproces:**
1. Gebruiker voert term in + optionele context
2. Systeem genereert definitie via GPT-4
3. 46 validatieregels worden toegepast
4. Ontologische categorisatie (6-stappen protocol)
5. Score berekening en feedback

### 2. Validatieregels (Toetsregels)

**46 regels in 7 categorieën:**
- **ARAI** (6): AI-specifieke regels (geen disclaimers, objectief)
- **SAM** (8): Samenhang (geen cirkelredeneringen, logisch)
- **STR** (9): Structuur (hoofdletter, punt, spelling)
- **ESS** (5): Essentiële inhoud (onderscheidend, context)
- **INT** (10): Interne consistentie (term match, metadata)
- **CON** (2): Context (juridisch taalgebruik)
- **VER** (3): Verboden content (discriminatie, privacy)

### 3. Ontologie Protocol (6-stappen)

```python
# Wetenschappelijk protocol voor categorisatie
1. Structurele Analyse → Enkelvoudig/Samengesteld
2. Semantische Categorisatie → Type/Proces/Resultaat/Exemplaar
3. Functionele Classificatie → Rol in juridische context
4. Contextuele Plaatsing → Domein bepaling
5. Relationele Mapping → Relaties met andere begrippen
6. Validatie & Verificatie → Check consistentie
```

### 4. Content Enrichment

**Aanvullende generatie features:**
- Synoniemen generatie
- Antoniemen generatie
- Voorbeeldzinnen
- Gerelateerde begrippen
- Bronvermelding

## Data Models

### Definition Model
```python
{
    "id": int,
    "term": str,
    "definition": str,
    "context": str,
    "context_type": str,  # proces/resultaat/type/exemplaar
    "metadata": {
        "model": str,
        "temperature": float,
        "timestamp": datetime,
        "version": int
    },
    "validation_score": int,
    "ontology_score": float
}
```

### ValidationResult Model
```python
{
    "definition_id": int,
    "rule_code": str,  # bijv. "SAM-01"
    "passed": bool,
    "message": str,
    "severity": str,  # error/warning/info
    "details": dict
}
```

## Business Rules

### 1. Definitie Kwaliteit
- Score >= 80% voor acceptatie
- Alle verplichte regels moeten slagen
- Minimaal 20 woorden, maximaal 500

### 2. Context Types
- **Proces**: Activiteit of handeling
- **Resultaat**: Uitkomst of product
- **Type**: Categorie of soort
- **Exemplaar**: Specifiek voorbeeld

### 3. Temperature Settings
- Default: 0.3 (consistentie)
- Creative mode: 0.7
- Strict mode: 0.1

## Critical Business Logic

### Score Calculation
```python
def calculate_score(validation_results):
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

### Prompt Structure
```
Systeem: Je bent een expert in Nederlandse juridische terminologie...
Context: {context}
Term: {term}
Instructies: Genereer een definitie volgens deze regels...
```

## Integration Points

1. **OpenAI API**: GPT-4 voor generatie
2. **Web Lookup**: Externe bronnen raadplegen
3. **Document Upload**: PDF/Word parsing
4. **Export**: TXT, Excel, PDF formats

## Performance Considerations

- Prompt size: Target <10k chars (nu 35k)
- Response time: Target <5 sec (nu 8-12)
- Caching: Definitions, validations, examples
- Rate limiting: 100 req/min development

## Common Issues & Solutions

1. **Cirkelredeneringen**: Check SAM-01 validator
2. **Te lange definities**: STR-06 enforcement
3. **Context mismatch**: CON-01/02 validators
4. **Encoding issues**: UTF-8 in web lookup

---
*Dit document wordt automatisch geladen door BMAD dev agents*