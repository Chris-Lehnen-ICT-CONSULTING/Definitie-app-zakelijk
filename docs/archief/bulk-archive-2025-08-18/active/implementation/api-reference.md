# DefinitieAgent API Reference

## Overview

De DefinitieAgent API biedt programmatische toegang tot alle definitie generatie en validatie functionaliteit. Momenteel is de API intern gebruikt door de Streamlit UI, maar kan uitgebreid worden voor externe integraties.

## Core Services

### UnifiedDefinitionService

Het centrale service endpoint voor alle definitie-gerelateerde operaties.

#### Instantie verkrijgen

```python
from services.unified_definition_service import UnifiedDefinitionService

service = UnifiedDefinitionService.get_instance()
```

#### Generate Definition

Genereert een nieuwe definitie voor een gegeven term.

```python
async def generate_definition(
    term: str,
    context: Optional[str] = None,
    mode: GenerationMode = GenerationMode.AUTO,
    temperature: float = 0.3
) -> Dict[str, Any]
```

**Parameters:**
- `term` (str): Het begrip waarvoor een definitie gegenereerd moet worden
- `context` (str, optional): Aanvullende context informatie
- `mode` (GenerationMode): AUTO, MODERN, LEGACY, of HYBRID
- `temperature` (float): OpenAI temperature parameter (0.0 - 1.0)

**Response:**
```json
{
    "success": true,
    "definition": {
        "term": "authenticatie",
        "definition": "Het proces waarbij...",
        "context": "juridisch",
        "metadata": {
            "model": "gpt-4",
            "timestamp": "2025-01-17T10:30:00Z",
            "mode": "AUTO"
        }
    },
    "validation": {
        "score": 85,
        "passed_rules": ["SAM-01", "STR-01"],
        "failed_rules": ["VER-02"],
        "messages": []
    }
}
```

#### Validate Definition

Valideert een bestaande definitie tegen de 46 toetsregels.

```python
def validate_definition(
    definition_text: str,
    term: str,
    rules: Optional[List[str]] = None
) -> ValidationResult
```

**Parameters:**
- `definition_text` (str): De definitie tekst om te valideren
- `term` (str): Het gedefinieerde begrip
- `rules` (List[str], optional): Specifieke regels om te controleren (default: alle)

**Response:**
```json
{
    "valid": true,
    "score": 92,
    "total_rules": 46,
    "passed": 42,
    "failed": 4,
    "details": [
        {
            "rule": "SAM-01",
            "passed": true,
            "message": "Definitie bevat geen cirkelredeneringen"
        }
    ]
}
```

## Validation Rules API

### Get Available Rules

```python
GET /api/validation/rules
```

Retourneert lijst van alle beschikbare validatieregels.

### Get Rule Details

```python
GET /api/validation/rules/{rule_code}
```

Retourneert details van een specifieke regel.

**Response:**
```json
{
    "code": "SAM-01",
    "category": "Samenhang",
    "name": "Geen cirkelredeneringen",
    "description": "Een definitie mag het te definiëren begrip niet bevatten",
    "severity": "error",
    "examples": {
        "good": "Authenticatie is het proces van identiteitsverificatie",
        "bad": "Authenticatie is het authenticeren van gebruikers"
    }
}
```

## Document Processing API

### Upload Document

```python
POST /api/documents/upload
Content-Type: multipart/form-data

file: <document file>
```

Upload een document voor begrippen extractie.

### Extract Terms

```python
POST /api/documents/extract-terms

{
    "document_id": "doc-123",
    "min_frequency": 2,
    "include_compounds": true
}
```

Extract relevante begrippen uit een document.

## Web Lookup API

### Search Definition

```python
POST /api/lookup/definition

{
    "term": "authenticatie",
    "sources": ["wetten.nl", "officielebekendmakingen.nl"],
    "max_results": 10
}
```

Zoekt definities in externe bronnen.

## Rate Limiting

Alle API endpoints hebben rate limiting:

- **Development**: 100 requests per minuut
- **Production**: 1000 requests per uur per API key
- **Burst**: Max 10 concurrent requests

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642435200
```

## Error Responses

Standaard error formaat:

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input parameters",
        "details": {
            "field": "term",
            "issue": "Term cannot be empty"
        }
    },
    "timestamp": "2025-01-17T10:30:00Z",
    "request_id": "req-abc123"
}
```

Error Codes:
- `VALIDATION_ERROR` - Input validatie gefaald
- `RATE_LIMIT_EXCEEDED` - Rate limit overschreden
- `INTERNAL_ERROR` - Server error
- `NOT_FOUND` - Resource niet gevonden
- `UNAUTHORIZED` - Authenticatie vereist

## WebSocket Events (Planned)

Voor real-time updates tijdens lange operaties:

```javascript
ws.on('generation.started', (data) => {
    console.log(`Generating definition for: ${data.term}`);
});

ws.on('generation.progress', (data) => {
    console.log(`Progress: ${data.percentage}%`);
});

ws.on('generation.completed', (data) => {
    console.log(`Definition generated: ${data.definition}`);
});
```

## Authentication (Planned)

Future API versies zullen JWT-based authenticatie gebruiken:

```
Authorization: Bearer <jwt-token>
```

## Pagination

Voor endpoints die lijsten retourneren:

```
GET /api/definitions?page=1&limit=20

Response Headers:
X-Total-Count: 156
Link: <api/definitions?page=2&limit=20>; rel="next"
```

## SDK Support (Planned)

Python SDK example:

```python
from definitie_agent import Client

client = Client(api_key="your-api-key")

# Generate definition
result = client.definitions.generate(
    term="authenticatie",
    context="juridisch"
)

# Validate definition
validation = client.validation.check(
    definition=result.definition,
    term=result.term
)
```
