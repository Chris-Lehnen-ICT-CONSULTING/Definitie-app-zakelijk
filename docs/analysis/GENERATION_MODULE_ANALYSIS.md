# Generation Module - Complete Analysis

## Overzicht

De generation module (`src/generation/definitie_generator.py`) is de kern AI-generatie engine van de Definitie-app. Deze module verzorgt intelligente definitie generatie door toetsregels te interpreteren als creatieve richtlijnen voor optimale GPT prompts.

## Module Architectuur

### Core Componenten

```
src/generation/
├── __init__.py              # Minimale package definitie
└── definitie_generator.py   # Hoofdmodule met alle generatie logica
```

### Belangrijke Classes

#### 1. **OntologischeCategorie** (Enum)
Classificeert begrippen in vier ontologische categorieën:
- `TYPE`: Voor types/klassen (bijv. "Document dat...")
- `PROCES`: Voor processen/activiteiten (bijv. "Verificatie waarbij...")
- `RESULTAAT`: Voor uitkomsten/resultaten (bijv. "Besluit dat volgt uit...")
- `EXEMPLAAR`: Voor specifieke instanties (bijv. "Document met uniek nummer...")

#### 2. **GenerationInstruction** (Dataclass)
Structuur voor definitie generatie instructies uit toetsregels:
```python
@dataclass
class GenerationInstruction:
    rule_id: str                     # Unieke ID van toetsregel
    guidance: str                    # Positieve instructie
    template: Optional[str] = None   # Template structuur
    examples: List[str] = None       # Referentie voorbeelden
    focus_areas: List[str] = None    # Aandachtsgebieden
    priority: str = "medium"         # Prioriteit niveau
```

#### 3. **GenerationContext** (Dataclass)
Volledige context voor definitie generatie:
```python
@dataclass
class GenerationContext:
    # Basis context
    begrip: str
    organisatorische_context: str
    juridische_context: str
    categorie: OntologischeCategorie
    
    # Feedback en instructies
    feedback_history: List[str] = None
    custom_instructions: List[str] = None
    
    # Hybride context uitbreidingen
    hybrid_context: Optional[Any] = None
    use_hybrid_enhancement: bool = False
    web_context: Optional[Dict[str, Any]] = None
    document_context: Optional[Dict[str, Any]] = None
```

#### 4. **GenerationResult** (Dataclass)
Resultaat van definitie generatie:
```python
@dataclass
class GenerationResult:
    # Kern resultaat
    definitie: str
    gebruikte_instructies: List[GenerationInstruction]
    prompt_template: str
    
    # Metadata
    iteration_nummer: int = 1
    context: GenerationContext = None
    
    # Voorbeelden uitbreidingen
    voorbeelden: Dict[str, List[str]] = None
    voorbeelden_gegenereerd: bool = False
    voorbeelden_error: Optional[str] = None
```

#### 5. **RegelInterpreter**
Vertaalt toetsregels naar positieve generatie instructies:
- `for_generation()`: Converteert regel data naar GenerationInstruction
- `_extract_positive_guidance()`: Haalt positieve guidance uit regels
- `_build_template()`: Bouwt regel-specifieke templates
- `_determine_focus_areas()`: Bepaalt aandachtsgebieden

#### 6. **DefinitieGenerator**
Hoofdklasse voor intelligente definitie generatie:

**Key Methods:**
- `generate()`: Basis definitie generatie
- `generate_with_examples()`: Generatie met voorbeelden
- `generate_examples_only()`: Alleen voorbeelden voor bestaande definitie
- `generate_with_feedback()`: Iteratieve generatie (placeholder)
- `_enhance_with_hybrid_context()`: Hybrid context verrijking
- `_build_generation_prompt()`: Prompt constructie
- `_call_gpt()`: OpenAI API aanroep

## Generation Workflow

### 1. Basis Generatie Flow
```
1. Context creatie (GenerationContext)
   ↓
2. Hybrid context enhancement (optioneel)
   ↓
3. Toetsregels laden als instructies
   ↓
4. Prompt bouwen met alle context
   ↓
5. GPT API aanroep
   ↓
6. Resultaat packaging (GenerationResult)
```

### 2. Enhanced Flow met Voorbeelden
```
1. Basis definitie generatie
   ↓
2. Voorbeelden generatie via unified_voorbeelden:
   - Sentence examples
   - Practical examples
   - Counter examples
   - Synonyms
   - Antonyms
   - Explanations
   ↓
3. Bulk generatie voor performance
   ↓
4. Resultaat met voorbeelden
```

## Prompt Engineering

### Prompt Structuur
De generator bouwt gestructureerde prompts met deze secties:

1. **Systeem Instructie**
   - Expert rol definitie
   - Precisie en correctheid focus

2. **Structuur Template** (categorie-specifiek)
   - Basis structuur patroon
   - Focus gebieden per categorie

3. **Generatie Richtlijnen**
   - Positieve instructies uit toetsregels
   - Gesorteerd op prioriteit

4. **Hybride Context** (indien beschikbaar)
   - Kwaliteit score
   - Geaggregeerde context
   - Bronvermelding
   - Gebruik instructies

5. **Context Informatie**
   - Begrip details
   - Organisatorische/juridische context
   - Ontologische categorie

6. **Aanvullende Instructies**
   - Custom user instructies
   - Feedback historie

7. **Opdracht**
   - Specifieke generatie instructie
   - Kwaliteitscriteria

### Toetsregel Mapping
De module bevat uitgebreide mappings voor toetsregels:

```python
guidance_mapping = {
    "CON-01": "Formuleer specifiek voor context zonder expliciet te benoemen",
    "CON-02": "Baseer op authentieke bronnen, verwijs impliciet",
    "ESS-01": "Beschrijf wat het IS, niet het doel",
    "ESS-02": "Maak categorie expliciet (type/proces/resultaat)",
    # ... etc
}
```

## OpenAI API Integratie

### API Configuratie
- Gebruikt `get_api_config()` voor parameters
- Flexibele overrides voor model, temperature, max_tokens
- Default model via config management

### API Call Pattern
```python
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model=gpt_params['model'],
    messages=[
        {"role": "system", "content": "Expert rol..."},
        {"role": "user", "content": prompt}
    ],
    temperature=gpt_params['temperature'],
    max_tokens=gpt_params['max_tokens']
)
```

### Error Handling
- OpenAIError specifieke handling
- Fallback mechanismen
- Gedetailleerde logging

## Hybrid Context Support

### Integratie
- Optionele import met fallback
- `HYBRID_CONTEXT_AVAILABLE` flag
- Graceful degradation

### Enhancement Flow
1. Check hybrid availability
2. Create/use existing hybrid context
3. Update generation context
4. Build enhanced prompt section
5. Quality-based instructions

### Context Kwaliteit Levels
- **High (>0.8)**: "Integreer rijke context optimaal"
- **Medium (>0.6)**: "Gebruik context waar relevant"
- **Low (<0.6)**: "Gebruik context zorgvuldig"

## Voorbeelden Integratie

### Unified Voorbeelden Module
- Import van `unified_voorbeelden`
- Bulk generatie support
- Performance monitoring

### Example Types
- `SENTENCE`: Zin voorbeelden
- `PRACTICAL`: Praktische voorbeelden
- `COUNTER`: Tegen voorbeelden
- `SYNONYMS`: Synoniemen
- `ANTONYMS`: Antoniemen
- `EXPLANATION`: Toelichtingen

### Generatie Modes
- `FAST`: Snelste bulk generatie
- `SYNC`: Synchrone generatie
- `ASYNC`: Asynchrone generatie

## Integration Points

### 1. Config & Toetsregels
- `get_toetsregel_manager()`: Toegang tot regels
- `get_api_config()`: API configuratie
- Fallback naar legacy `toetsregels.json`

### 2. Voorbeelden Module
- `get_examples_generator()`: Factory functie
- `genereer_alle_voorbeelden()`: Bulk functie
- Rate limiting support

### 3. Hybrid Context
- `get_hybrid_context_engine()`: Engine toegang
- Document selectie support
- Web context integratie

### 4. Performance Monitoring
- Import van `utils.performance_monitor`
- Timing voor totale generatie
- Timing voor voorbeelden

## Convenience Functions

### `create_generation_context()`
Helper voor simpele context creatie

### `create_hybrid_generation_context()`
Helper met hybrid context support

### `generate_definitie()`
Quick definitie generatie met string parameters

## Usage Patterns

### Basis Gebruik
```python
generator = DefinitieGenerator()
context = create_generation_context(
    begrip="toezicht",
    organisatorische_context="DJI",
    categorie=OntologischeCategorie.PROCES
)
result = generator.generate(context)
```

### Met Voorbeelden
```python
result = generator.generate_with_examples(
    context,
    generate_examples=True,
    example_types=[ExampleType.SENTENCE, ExampleType.PRACTICAL]
)
```

### Met Hybrid Context
```python
context = create_hybrid_generation_context(
    begrip="toezicht",
    organisatorische_context="DJI",
    selected_document_ids=["doc1", "doc2"],
    enable_hybrid=True
)
result = generator.generate(context)
```

## Performance Optimalisaties

### Bulk Voorbeelden
- Gebruikt `genereer_alle_voorbeelden()` voor efficiency
- Single API call voor meerdere types
- Parallel processing waar mogelijk

### Caching Strategieën
- Toetsregel caching via manager
- API config caching
- Template hergebruik

### Error Recovery
- Fallback naar legacy toetsregels
- Minimale default instructies
- Graceful degradation voor hybrid

## Future Uitbreidingen

### Geplande Features
1. **Iteratieve Verbetering**
   - `generate_with_feedback()` implementatie
   - Multi-iteratie support
   - Automatische kwaliteitsverbetering

2. **Advanced Prompt Engineering**
   - Dynamische template selectie
   - Context-aware instructie prioritering
   - Multi-model support

3. **Enhanced Hybrid Context**
   - Realtime document updates
   - Intelligente bron selectie
   - Context conflict resolution

## Conclusie

De generation module is een geavanceerde, flexibele engine voor AI-gedreven definitie generatie. Het combineert:
- Intelligente toetsregel interpretatie
- Gestructureerde prompt engineering
- Robuuste OpenAI integratie
- Uitgebreide voorbeelden support
- Optionele hybrid context verrijking

De modulaire architectuur maakt het eenvoudig om nieuwe features toe te voegen terwijl backwards compatibility behouden blijft.