# Prompt Builder Refactoring Workflow Analysis

**Datum**: 2025-08-26
**Status**: Analyse Compleet
**Doel**: Refactor legacy prompt builder naar clean services architectuur

## Executive Summary

De legacy `PromptBouwer` in `prompt_builder.py` moet gerefactord worden conform de enterprise architectuur en solution architecture richtlijnen. De huidige implementatie is een monolithische class met hardcoded regels en te veel verantwoordelijkheden. De nieuwe implementatie moet modulair, testbaar en performant zijn volgens EPIC-006 doelstellingen.

## Huidige Situatie Analyse

### Legacy Prompt Builder Problematiek

1. **Monolithische Structuur**
   - 343 regels code in één bestand
   - Hardcoded AFKORTINGEN dictionary (11 entries)
   - Hardcoded TOEGESTANE_TOETSREGELS set (35 entries)
   - Directe OpenAI client instantiatie

2. **Performance Issues**
   - Prompts tot 35k karakters (doel: <10k)
   - Geen dynamische content selectie
   - Alle regels worden altijd toegevoegd
   - Geen template caching

3. **Architectuur Problemen**
   - Business logic gemengd met presentation
   - Geen dependency injection
   - Tight coupling met OpenAI API
   - Geen proper error handling voor rate limits

4. **Context Verwerking Bug**
   - `ontologische_categorie` wordt als string toegevoegd aan `base_context`
   - Legacy builder verwacht alleen lijsten in context dictionary
   - Veroorzaakt TypeError bij prompt generatie

### Bestaande Nieuwe Componenten

1. **UnifiedPromptBuilder** (definition_generator_prompts.py)
   - Implementeert Strategy pattern
   - Ondersteunt multiple prompt strategies
   - Heeft adapter voor legacy compatibility
   - Basis structuur voor nieuwe implementatie

2. **PromptTemplate** dataclass
   - Template-based prompt generation
   - Variable substitution
   - Category-based selection

3. **BasicPromptBuilder**
   - Implementeert ontologische categorie support
   - Template selectie op basis van context
   - Modulaire prompt opbouw

## Refactoring Strategie

### 🚀 NIEUWE AANBEVELING: Modulaire Prompt Architectuur (Fase 0)

#### Waarom Modulair?
De modulaire aanpak biedt een snellere, minder risicovolle route naar betere prompt management:
- **Direct implementeerbaar**: Werkt binnen bestaande structuur
- **Component-based**: Elke prompt sectie wordt een eigen component
- **Plugin architectuur**: Makkelijk nieuwe componenten toevoegen
- **Testbaar**: Elke component kan apart getest worden

#### Implementatie Voorbeeld
```python
# src/prompt_builder/components/prompt_orchestrator.py
class PromptOrchestrator:
    """Centrale coordinator voor modulaire prompt opbouw."""

    def __init__(self):
        self.components = {
            'context': ContextComponent(),
            'ontology': OntologyInstructionComponent(),
            'rules': RuleSelectionComponent(),
            'examples': ExampleSelectionComponent(),
            'constraints': ConstraintComponent(),
            'metadata': MetadataComponent()
        }

    def build_prompt(self, request: PromptRequest) -> str:
        sections = []

        for name, component in self.components.items():
            if component.should_include(request):
                section = component.generate(request)
                sections.append(section)

        return self._combine_sections(sections)
```

#### Voorbeeld Component
```python
# src/prompt_builder/components/ontology_component.py
class OntologyInstructionComponent(PromptComponent):
    """Component voor ontologische categorie instructies."""

    def should_include(self, request: PromptRequest) -> bool:
        return request.ontologische_categorie is not None

    def generate(self, request: PromptRequest) -> str:
        templates = {
            'type': self._type_template,
            'proces': self._proces_template,
            'resultaat': self._resultaat_template,
            'exemplaar': self._exemplaar_template
        }

        template = templates.get(request.ontologische_categorie)
        if template:
            return template(request.begrip)
        return ""
```

#### Voordelen Modulaire Architectuur
1. **Flexibiliteit**: Components kunnen aan/uit gezet worden
2. **Herbruikbaarheid**: Components voor verschillende prompt types
3. **Maintainability**: Wijzigingen geïsoleerd per component
4. **Testbaarheid**: Unit tests per component
5. **Backward Compatible**: Kan legacy prompt builder wrappen

### Fase 1: Directe Bug Fix (Urgent)

```python
# In definition_orchestrator.py, regel 406-413
# VOOR:
base_context = {
    "organisatorisch": [...],
    "juridisch": [...],
    "wettelijk": [],
    "ontologische_categorie": context.request.ontologische_categorie,  # BUG!
}

# NA:
base_context = {
    "organisatorisch": [...],
    "juridisch": [...],
    "wettelijk": [],
    # Verwijder ontologische_categorie uit base_context
}
# Behoud alleen in metadata waar het thuishoort
```

### Fase 2: Extract Configuration - Service Extractie Uitgelegd (Week 1)

#### Wat is Service Extractie?
Service extractie is het proces waarbij functionaliteit uit een monolithische codebase wordt gehaald en verplaatst naar aparte, onafhankelijke services. Dit verhoogt modulariteit, testbaarheid en onderhoudbaarheid.

#### Voorbeeld: Van Monoliet naar Services
**Huidige Situatie (Monoliet)**:
```python
# Alles zit in één grote class/module
class PromptBouwer:
    def __init__(self):
        # Hardcoded data
        self.afkortingen = {
            "OM": "Openbaar Ministerie",
            "ZM": "Zittende Magistratuur",
            # ... 11 entries
        }
        self.regels = {...}       # Hardcoded
        self.templates = {...}    # Hardcoded

    def bouw_prompt(self):
        # Alle logica in één methode
        # - Context verwerking
        # - Template selectie
        # - Regel filtering
        # Alles door elkaar
```

**Na Service Extractie**:
```python
# Aparte services met eigen verantwoordelijkheid
class ConfigurationService:
    """Beheert alle configuratie"""
    def get_abbreviations(self) -> dict[str, str]
    def get_rules(self) -> set[str]
    def get_forbidden_words(self) -> list[str]

class TemplateService:
    """Beheert prompt templates"""
    def select_template(context) -> Template
    def render_template(template, data) -> str

class RuleService:
    """Beheert validatie regels"""
    def filter_rules(context) -> list
    def compress_rules(rules) -> str
```

#### Concrete Implementatie Stappen

1. **Maak ConfigurationService**
```python
# src/services/prompt_configuration_service.py
class PromptConfigurationService:
    """Centralized prompt configuration management."""

    def __init__(self):
        self._config = self._load_config()

    def _load_config(self) -> dict:
        """Laadt configuratie van JSON/Database/API."""
        with open('config/prompt_config.json') as f:
            return json.load(f)

    def get_abbreviations(self) -> dict[str, str]:
        """Retourneert afkortingen dictionary."""
        return self._config['abbreviations']

    def get_allowed_rules(self) -> set[str]:
        """Retourneert toegestane validatie regels."""
        return set(self._config['allowed_rules'])

    def get_forbidden_words(self) -> list[str]:
        """Retourneert verboden startwoorden."""
        return self._config['forbidden_words']
```

2. **Verplaats hardcoded data naar JSON**
```json
// src/config/prompt_config.json
{
    "abbreviations": {
        "OM": "Openbaar Ministerie",
        "ZM": "Zittende Magistratuur",
        "3RO": "Samenwerkingsverband Reclasseringsorganisaties",
        "DJI": "Dienst Justitiële Inrichtingen",
        // etc.
    },
    "allowed_rules": ["CON-01", "CON-02", "ESS-01", "ESS-02", ...],
    "forbidden_words": ["de", "het", "een", "is", "betekent", ...],
    "templates": { ... }
}
```

#### Voordelen van Service Extractie
1. **Modulariteit**: Elke service heeft één duidelijke taak
2. **Testbaarheid**: Services kunnen onafhankelijk getest worden
3. **Configuratie Management**: Wijzigingen zonder code aanpassingen
4. **Herbruikbaarheid**: Services kunnen door meerdere componenten gebruikt worden
5. **Schaalbaarheid**: Services kunnen apart geschaald/geoptimaliseerd worden

### Fase 3: Implement Template System (Week 1-2)

1. **Enhanced PromptTemplate System**
```python
# src/services/prompt_templates/
├── base_templates.py      # Basis templates
├── ontological_templates.py # Ontologische categorie templates
├── domain_templates.py     # Domein-specifieke templates
└── template_registry.py    # Template management
```

2. **Dynamic Template Selection**
```python
class TemplateSelector:
    """Select optimal template based on context."""

    def select_template(
        self,
        begrip: str,
        context: EnrichedContext,
        requirements: dict
    ) -> PromptTemplate:
        # Intelligente template selectie
        # Gebaseerd op ontologische categorie
        # Context rijkheid score
        # Domein specifieke requirements
```

### Fase 4: Implement Dynamic Content Selection (Week 2-3)

Conform EPIC-006 requirements:

1. **Example Selection Service**
```python
class ExampleSelectionService:
    """Select most relevant examples using embeddings."""

    def select_examples(
        self,
        term: str,
        context: str,
        limit: int = 3
    ) -> list[Example]:
        # Semantic similarity matching
        # Context-aware selection
        # Maximum 3 examples (was 20+)
```

2. **Rule Compression Service**
```python
class RuleCompressionService:
    """Compress rules to essential information."""

    def compress_rules(
        self,
        context: str,
        requirements: dict
    ) -> str:
        # Select only applicable rules
        # Compress to key points
        # Target: 2k chars (was 8k)
```

3. **Context Compression**
```python
class ContextCompressionService:
    """Intelligent context compression."""

    def compress_context(
        self,
        raw_context: dict,
        target_size: int = 5000
    ) -> str:
        # Remove redundancy
        # Prioritize relevant info
        # Maintain semantic meaning
```

### Fase 5: Service Integration (Week 3-4)

#### Service Orchestratie met Dependency Injection

1. **Nieuwe PromptBuilderService**
```python
class PromptBuilderService:
    """Clean service implementation for prompt building."""

    def __init__(
        self,
        config_service: PromptConfigurationService,
        template_selector: TemplateSelector,
        example_service: ExampleSelectionService,
        rule_service: RuleCompressionService,
        context_service: ContextCompressionService
    ):
        """
        Constructor met dependency injection.
        Alle services worden van buitenaf geïnjecteerd voor testbaarheid.
        """
        self.config = config_service
        self.templates = template_selector
        self.examples = example_service
        self.rules = rule_service
        self.context = context_service

    async def build_prompt(
        self,
        request: PromptBuildRequest
    ) -> PromptBuildResponse:
        """
        Orchestreert het bouwen van een prompt door verschillende services aan te roepen.
        """
        # Stap 1: Selecteer template gebaseerd op context
        template = await self.templates.select_template(
            request.begrip,
            request.context,
            request.requirements
        )

        # Stap 2: Selecteer relevante voorbeelden (max 3)
        examples = await self.examples.select_examples(
            request.begrip,
            request.context,
            limit=3
        )

        # Stap 3: Filter en comprimeer regels
        rules = await self.rules.compress_rules(
            request.context,
            request.requirements
        )

        # Stap 4: Comprimeer context
        compressed_context = await self.context.compress_context(
            request.raw_context,
            target_size=5000
        )

        # Stap 5: Render template met alle data
        prompt = template.render(
            begrip=request.begrip,
            compressed_context=compressed_context,
            selected_rules=rules,
            dynamic_examples=examples
        )

        # Stap 6: Valideer grootte
        if len(prompt) > 10000:
            prompt = await self._optimize_prompt(prompt)

        return PromptBuildResponse(
            prompt=prompt,
            token_count=self._count_tokens(prompt),
            template_used=template.name,
            compression_ratio=len(request.raw_context) / len(prompt)
        )
```

#### Dependency Injection Container
```python
# src/services/container.py
class ServiceContainer:
    """Container voor dependency injection."""

    _instances = {}

    @classmethod
    def register(cls, service_class, instance):
        """Registreer service instance."""
        cls._instances[service_class] = instance

    @classmethod
    def get(cls, service_class):
        """Verkrijg service instance."""
        if service_class not in cls._instances:
            # Lazy initialization
            cls._instances[service_class] = cls._create_instance(service_class)
        return cls._instances[service_class]

    @classmethod
    def _create_instance(cls, service_class):
        """Creëer nieuwe service instance met dependencies."""
        if service_class == PromptBuilderService:
            return PromptBuilderService(
                config_service=cls.get(PromptConfigurationService),
                template_selector=cls.get(TemplateSelector),
                example_service=cls.get(ExampleSelectionService),
                rule_service=cls.get(RuleCompressionService),
                context_service=cls.get(ContextCompressionService)
            )
        # etc. voor andere services
```

2. **Adapter Pattern Update**
```python
class LegacyPromptAdapter:
    """Maintain backward compatibility during transition."""

    def __init__(self, new_service: PromptBuilderService):
        self.new_service = new_service

    def bouw_prompt(self) -> str:
        # Convert legacy format to new
        # Call new service
        # Convert response back
```

### Fase 6: Migration & Testing (Week 4-5)

1. **A/B Testing Framework**
```python
class PromptABTestService:
    """Test new vs legacy implementation."""

    def should_use_new_builder(self, user_id: str) -> bool:
        # Gradual rollout logic
        # Start with 10% traffic

    def track_metrics(self, variant: str, result: dict):
        # Response time
        # Token count
        # Validation score
        # Cost metrics
```

2. **Migration Steps**
   - Week 1: Fix urgent bug, extract configuration
   - Week 2: Implement template system
   - Week 3: Dynamic content selection
   - Week 4: Service integration
   - Week 5: A/B testing & rollout

## Success Metrics

Conform EPIC-006 targets:

1. **Prompt Size**
   - Current: ~35,000 chars
   - Target: <10,000 chars (71% reduction)

2. **Performance**
   - Current: 8-12 seconds
   - Target: <5 seconds (60% improvement)

3. **Cost**
   - Current: €0.35 per request
   - Target: €0.10 per request (70% reduction)

4. **Quality**
   - No degradation in validation scores
   - Maintain 90% first-time-right target

## Risk Mitigation

1. **Quality Risks**
   - A/B testing met gradual rollout
   - Rollback capability
   - Continuous monitoring

2. **Integration Risks**
   - Adapter pattern voor compatibility
   - Feature flags voor rollout control
   - Comprehensive testing

3. **Performance Risks**
   - Caching strategy
   - Async processing
   - Load testing

## Implementation Checklist

### Optie A: Modulaire Architectuur (Aanbevolen - 2 weken)
#### Week 1: Component Framework
- [ ] Fix ontologische_categorie bug (✅ Already done!)
- [ ] Implementeer PromptOrchestrator base class
- [ ] Creëer PromptComponent interface
- [ ] Bouw eerste components (Context, Ontology)
- [ ] Test component isolation

#### Week 2: Complete Components & Integration
- [ ] Implementeer alle prompt components
- [ ] Integreer met bestaande UnifiedPromptBuilder
- [ ] Migreer legacy prompt logic naar components
- [ ] A/B test nieuwe vs oude implementatie
- [ ] Documenteer component API

### Optie B: Service Extractie (Origineel plan - 5 weken)
#### Week 1: Foundation
- [ ] Fix ontologische_categorie bug (✅ Already done!)
- [ ] Extract configuration to service
- [ ] Create JSON configuration files
- [ ] Setup dependency injection

#### Week 2: Templates
- [ ] Implement enhanced template system
- [ ] Create template registry
- [ ] Build template selector
- [ ] Test template variations

#### Week 3: Dynamic Content
- [ ] Example selection with embeddings
- [ ] Rule compression logic
- [ ] Context compression algorithm
- [ ] Integration testing

#### Week 4: Service Integration
- [ ] New PromptBuilderService
- [ ] Update LegacyPromptAdapter
- [ ] Wire up dependencies
- [ ] Performance testing

#### Week 5: Rollout
- [ ] A/B testing framework
- [ ] Metrics collection
- [ ] Gradual rollout (10% → 25% → 100%)
- [ ] Monitor quality metrics

### Hybride Aanpak (Beste van beide - 3 weken)
1. **Week 1**: Implementeer modulaire components
2. **Week 2**: Extraheer components naar services
3. **Week 3**: Testing & rollout

## Dependencies & Constraints

1. **Technical Dependencies**
   - OpenAI API compatibility
   - Existing validation framework
   - Current UI/session state

2. **Business Constraints**
   - No quality degradation allowed
   - Backward compatibility required
   - Cost reduction targets

3. **Architecture Alignment**
   - Follow clean architecture principles
   - Implement proper service boundaries
   - Use dependency injection
   - Maintain testability

## Next Steps

1. **Immediate Action**: Fix ontologische_categorie bug in definition_orchestrator.py
2. **Week 1 Start**: Begin configuration extraction
3. **Weekly Reviews**: Monitor progress against metrics
4. **Stakeholder Updates**: Report cost savings and performance gains

## Appendix: Code Examples

### Example: New Template Format
```python
ONTOLOGICAL_PROCESS_TEMPLATE = PromptTemplate(
    name="ontological_process",
    template="""
Genereer een definitie voor het PROCES begrip: {begrip}

Relevante context ({context_size} chars):
{compressed_context}

Belangrijkste regels ({rule_count}):
{selected_rules}

Top {example_count} voorbeelden:
{dynamic_examples}

BELANGRIJK: Begin met "is een activiteit waarbij..."

Definitie:""",
    variables=["begrip", "compressed_context", "selected_rules", "dynamic_examples"],
    category="ontological",
    max_size=10000
)
```

### Example: Compression Algorithm
```python
def compress_context(self, context: dict, max_chars: int = 5000) -> str:
    """Compress context while maintaining relevance."""
    # Priority order
    priorities = ["ontologische_categorie", "juridisch", "wettelijk", "organisatorisch"]

    compressed = []
    char_count = 0

    for priority in priorities:
        if priority in context and context[priority]:
            section = f"{priority}: {', '.join(context[priority])}\n"
            if char_count + len(section) <= max_chars:
                compressed.append(section)
                char_count += len(section)
            else:
                # Truncate if needed
                remaining = max_chars - char_count
                compressed.append(section[:remaining] + "...")
                break

    return "\n".join(compressed)
```

## Document History

- 2025-08-26: Initial workflow analysis created
  - Focus: Legacy prompt builder refactoring naar services architectuur
  - Author: BMad Master (Claude Code)
- 2025-08-26: Service extractie details toegevoegd
  - Uitleg wat service extractie betekent
  - Concrete voorbeelden van monoliet naar services
  - Dependency injection patterns
- 2025-08-26: Modulaire prompt architectuur aanbeveling toegevoegd
  - Component-based architecture als snellere alternatief
  - Hybride aanpak voor beste van beide werelden
  - Implementation checklist met meerdere opties
