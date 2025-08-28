# Prompt Components Mapping Document

## Overzicht
Dit document mapt alle prompt componenten van legacy naar modulair systeem voor de refactoring.

## Legacy PromptBouwer vs ModularPromptBuilder Vergelijking

### Structuur Analyse

| Aspect | Legacy PromptBouwer | ModularPromptBuilder |
|--------|-------------------|---------------------|
| Locatie | `/src/prompt_builder/prompt_builder.py` | `/src/services/prompts/modular_prompt_builder.py` |
| Aanpak | Monolithisch - alles in één methode | Modulair - 6 afzonderlijke componenten |
| Configuratie | PromptConfiguratie dataclass | PromptComponentConfig dataclass |
| Prompt Lengte | ~15-17k karakters | ~15-20k karakters (configureerbaar) |

### Component Mapping

#### Component 1: Rol & Basis Instructies
**Legacy (`bouw_prompt` regels 155-172):**
- Hardcoded expert rol definitie
- Woordsoort detectie inline
- Schrijfadvies per woordsoort

**Modulair (`_build_role_and_basic_rules`):**
- ✅ Gebruikt sub-builders: RoleDefinitionBuilder, TaskInstructionBuilder, etc.
- ✅ Lazy loading van builders
- ✅ Dynamische karakter limiet waarschuwingen
- 🔄 ACTIE: Moet nog volledig geïmplementeerd worden met sub-modules

#### Component 2: Context Sectie
**Legacy (`bouw_prompt` regels 174-198):**
- Hardcoded labelmapping
- Boolean + list ondersteuning
- Contextregels formattering

**Modulair (`_build_context_section`):**
- ✅ Adaptief - alleen als er context is
- ✅ Ondersteunt organisatorisch + domein context
- ✅ Volledig geïmplementeerd

#### Component 3: Ontologische Categorie (ESS-02)
**Legacy (`bouw_prompt` regels 201-213):**
- Statische ESS-02 sectie
- Geen category-specific guidance
- Altijd dezelfde tekst

**Modulair (`_build_ontological_section`):**
- ✅ Basis ESS-02 sectie behouden
- ✅ NIEUWE FEATURE: Category-specific guidance per type
- ✅ Intelligente templates voor proces/type/resultaat/exemplaar
- ✅ Volledig geïmplementeerd met uitgebreide guidance

#### Component 4: Validatie Regels
**Legacy (`bouw_prompt` regels 216-226):**
- Dynamisch uit toetsregels config
- Goede/foute voorbeelden
- Toetsvragen

**Modulair (`_build_validation_rules_section`):**
- ✅ Alle 24 validatieregels hardcoded
- ✅ Uitgebreide voorbeelden per regel
- ✅ Volledig geïmplementeerd

#### Component 5: Verboden Patronen
**Legacy (`bouw_prompt` regels 237-275):**
- Basis veelgemaakte fouten
- Verboden startwoorden uit config
- Context verboden via `voeg_contextverbod_toe`

**Modulair (`_build_forbidden_patterns_section`):**
- ✅ Uitgebreide verboden lijst (40+ patronen)
- ✅ Context-aware verboden toevoegingen
- ✅ Validatiematrix behouden
- ✅ Volledig geïmplementeerd

#### Component 6: Finale Instructies
**Legacy (`bouw_prompt` regels 278-302):**
- Ontologische marker
- Definitie opdracht
- Metadata sectie

**Modulair (`_build_final_instructions_section`):**
- ✅ Checklist toegevoegd
- ✅ Kwaliteitscontrole vragen
- ✅ Uitgebreide metadata voor traceerbaarheid
- ✅ Volledig geïmplementeerd

## Geïdentificeerde Modules voor Refactoring

### Core Modules (8 stuks)

1. **RoleDefinitionModule**
   - Expert rol definitie
   - Verantwoordelijkheid: definieer AI persona

2. **TaskInstructionModule**
   - Basis opdracht specificatie
   - Verantwoordelijkheid: wat moet AI doen

3. **WordTypeAdvisorModule**
   - Woordsoort detectie & advies
   - Verantwoordelijkheid: werkwoord/deverbaal/anders advies

4. **ContextProcessorModule**
   - Context sectie generatie
   - Verantwoordelijkheid: organisatorisch/domein context

5. **OntologicalGuideModule**
   - ESS-02 categorie instructies
   - Verantwoordelijkheid: type/proces/resultaat/exemplaar guidance

6. **ValidationRulesModule**
   - Toetsregels processor
   - Verantwoordelijkheid: 24 validatieregels toepassen

7. **ForbiddenPatternsModule**
   - Verboden patronen checker
   - Verantwoordelijkheid: context-aware verboden genereren

8. **MetadataTrackerModule**
   - Finale instructies & metadata
   - Verantwoordelijkheid: kwaliteit checks & traceerbaarheid

### Orchestrator Module

**PromptOrchestrator**
- Coördineert alle 8 modules
- Bepaalt module volgorde
- Combineert outputs
- Valideert totale prompt

## Dependencies

### External Dependencies
- `UnifiedGeneratorConfig`
- `EnrichedContext`
- Toetsregels configuratie
- Verboden woorden configuratie

### Inter-Module Dependencies
1. WordTypeAdvisor → RoleDefinition (voor woordsoort-specifiek advies)
2. ContextProcessor → ForbiddenPatterns (voor context-specifieke verboden)
3. OntologicalGuide → MetadataTracker (voor categorie in finale checks)
4. Alle modules → PromptOrchestrator (voor coördinatie)

## Migration Strategy

### Fase 1: Foundations
1. Creëer basis module interface/abstract class
2. Implementeer PromptOrchestrator skeleton
3. Setup module registry systeem

### Fase 2: Core Module Implementation
1. RoleDefinitionModule (eenvoudig)
2. TaskInstructionModule (eenvoudig)
3. WordTypeAdvisorModule (medium - woordsoort detectie)
4. ContextProcessorModule (reeds grotendeels klaar)

### Fase 3: Complex Module Implementation
5. OntologicalGuideModule (complex - category logic)
6. ValidationRulesModule (groot - 24 regels)
7. ForbiddenPatternsModule (medium - context aware)
8. MetadataTrackerModule (medium)

### Fase 4: Integration
1. Wire alle modules in orchestrator
2. Implementeer module communicatie
3. Add configuration management
4. Feature toggle voor rollout

## Risico's & Mitigaties

### Risico 1: Module Interface Complexiteit
- **Mitigatie**: Start met simpele interface, iteratief uitbreiden

### Risico 2: Backwards Compatibility
- **Mitigatie**: Feature toggle, A/B testing mogelijk maken

### Risico 3: Performance Overhead
- **Mitigatie**: Lazy loading, module caching

### Risico 4: Testing Complexiteit
- **Mitigatie**: Unit tests per module, integration tests voor orchestrator

## Next Steps

1. ✅ Component mapping compleet
2. ✅ Module definities bepaald
3. ⏳ Implementatie planning maken
4. ⏳ Begin met module interface design
5. ⏳ Start RoleDefinitionModule als proof of concept
