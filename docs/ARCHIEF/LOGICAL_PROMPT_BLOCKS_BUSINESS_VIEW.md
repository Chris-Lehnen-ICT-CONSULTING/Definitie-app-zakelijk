# Logische Prompt Blokken - Business Perspectief

## Overzicht: Van 6 Technische Modules naar 8 Business Blokken

### Huidige Technische Indeling (Developer View)
1. Rol & Basis Instructies
2. Context Sectie
3. Ontologische Categorie (ESS-02)
4. Validatie Regels
5. Verboden Patronen
6. Afsluitende Instructies

### Correcte Business Indeling (Product Owner View)

#### 1. **Expertise Module** 🎓
**Doel**: ChatGPT de juiste mindset geven
- Expert rol definitie
- Domeinkennis activeren
- Professioneel taalniveau instellen

#### 2. **Output Specificatie Module** 📋
**Doel**: Exact specificeren wat we willen
- Één zin requirement
- Geen toelichting regel
- Format vereisten
- Karakterlimieten

#### 3. **Grammatica Module** 📝
**Doel**: Taalkundig correcte definities
- Woordsoort detectie
- Werkwoord → proces/activiteit
- Deverbaal → resultaat/uitkomst
- Overig → zakelijke stijl

#### 4. **Context Bewustzijn Module** 🌍
**Doel**: Definitie past bij gebruiksomgeving
- Organisatorische context (OM, DJI, NP)
- Juridische context
- Domein context
- MAAR: niet letterlijk noemen!

#### 5. **Semantische Categorisatie Module** 🏷️
**Doel**: Betekenis ondubbelzinnig maken (ESS-02)
- Type (wat voor soort?)
- Exemplaar (welk specifiek geval?)
- Proces (welke activiteit?)
- Resultaat (welke uitkomst?)

#### 6. **Kwaliteitsregels Module** ✅
**Doel**: Voldoen aan overheidsstandaarden
- 30+ validatieregels
- Per regel: uitleg + voorbeelden
- Prioriteit per regel
- Toetsvragen

#### 7. **Foutpreventie Module** 🚫
**Doel**: Veelgemaakte fouten voorkomen
- Verboden startwoorden (40+)
- Algemene schrijffouten
- Context-specifieke valkuilen
- Cirkelredeneringen

#### 8. **Definitie Opdracht Module** 🎯
**Doel**: Concrete actie triggeren
- Ontologische marker eerst
- Expliciete opdracht voor [begrip]
- Metadata voor tracking
- Finale checklist

## Waarom Deze Indeling Beter Is

### 1. **Business Logica Centraal**
Elke module heeft één duidelijk business doel, niet een technisch doel.

### 2. **Gebruiker Perspectief**
- "Ik wil dat de definitie past bij mijn organisatie" → Context Module
- "Ik wil geen taalfouten" → Grammatica Module
- "Ik wil dat het aan standaarden voldoet" → Kwaliteitsregels Module

### 3. **Configureerbaar per Use Case**
```yaml
Juridische Definities:
  - Expertise: Juridisch expert
  - Grammatica: Formeel
  - Context: Rechtspraak
  - Kwaliteit: Strenge regels

Technische Definities:
  - Expertise: IT expert
  - Grammatica: Technisch
  - Context: ICT domein
  - Kwaliteit: Andere regels
```

### 4. **Testbaar vanuit Business**
- "Gebruikt ChatGPT de juiste expertrol?" → Test Expertise Module
- "Zijn definities grammaticaal correct?" → Test Grammatica Module
- "Worden context-namen vermeden?" → Test Context Module

## Implementatie Suggestie

```python
class PromptBuilder:
    def __init__(self, use_case: str):
        self.modules = {
            'expertise': ExpertiseModule(use_case),
            'output_spec': OutputSpecificationModule(),
            'grammar': GrammarModule(),
            'context': ContextAwarenessModule(),
            'semantics': SemanticCategorisationModule(),
            'quality': QualityRulesModule(use_case),
            'error_prevention': ErrorPreventionModule(),
            'task': DefinitionTaskModule()
        }

    def build_prompt(self, begrip: str, context: dict) -> str:
        # Elke module levert zijn deel
        prompt_parts = []

        for module_name, module in self.modules.items():
            if self.is_module_needed(module_name, context):
                prompt_parts.append(
                    module.generate_section(begrip, context)
                )

        return "\n\n".join(prompt_parts)
```

## Voordelen voor Stakeholders

### Voor Product Owners
- Begrijpelijke modules met business waarde
- Makkelijk nieuwe requirements toe te voegen
- Per module kunnen features aan/uit

### Voor Gebruikers
- Betere definities door specialisatie per module
- Configureerbaar per domein
- Transparant wat elke module doet

### Voor Developers
- Clean architecture
- Single responsibility per module
- Makkelijk te testen en uitbreiden

## Conclusie

Door de prompt op te delen in business-logische blokken in plaats van technische componenten, wordt het systeem:
- **Begrijpelijker** voor niet-technische stakeholders
- **Configureerbaarder** per use case
- **Onderhoudbaarder** omdat elk blok één business doel heeft
- **Testbaarder** vanuit business perspectief

---
*Business-driven architecture voor prompt generatie*
*Focus op WAT (business waarde) in plaats van HOE (technische implementatie)*
