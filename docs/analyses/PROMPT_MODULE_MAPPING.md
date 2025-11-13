# Prompt Module Mapping Analyse

## Doel
Dit document mappt exact welke prompt module verantwoordelijk is voor welke regels in de gegenereerde prompt.

## Test Case
- **Begrip**: contradictie
- **Prompt bestand**: `/Users/chrislehnen/Downloads/_Definitie_Generatie_prompt-13.txt`
- **Totaal regels**: 423

## Module → Prompt Mapping (COMPLEET)

### 1. ExpertiseModule (`expertise_module.py`)
**Regels: 1-9**
- Regels 1-2: Rol definitie ("Je bent een expert...")
- Regel 3: Deverbaal-specifiek advies ("Als het begrip een resultaat is...")
- Regels 4-9: Belangrijke vereisten (objectieve taal, vermijd vage termen, etc.)

### 2. OutputSpecificationModule (`output_specification_module.py`)
**Regels: 11-22**
- Regels 11-16: OUTPUT FORMAT VEREISTEN (één zin, geen punt, geen haakjes)
- Regels 17-22: DEFINITIE KWALITEIT (formele taal, vermijd jargon, specifieke termen)

### 3. GrammarModule (`grammar_module.py`)
**Regels: 24-61**
- Regels 24-25: GRAMMATICA REGELS header
- Regels 26-31: Enkelvoud als standaard
- Regels 33-37: Actieve vorm prefereren
- Regels 39-44: Tegenwoordige tijd
- Regels 46-51: Komma gebruik
- Regels 53-60: Afkortingen en haakjes

### 4. ContextAwarenessModule (`context_awareness_module.py`)
**Regels: 63-69**
- Regel 63: VERPLICHTE CONTEXT INFORMATIE
- Regel 64: Belangrijke instructie voor context gebruik
- Regel 66: SPECIFIEKE CONTEXT VOOR DEZE DEFINITIE
- Regel 67-68: Organisatorische context ("test", ["test"])
- Regel 69: hybrid_context

### 5. SemanticCategorisationModule (`semantic_categorisation_module.py`)
**Regels: 70-116**
- Regels 70-87: Basis ESS-02 sectie (4 categorieën)
- Regels 88-116: TYPE-specifieke guidance (voor "contradictie")
  - Structuur instructies
  - Voorbeelden GOED en FOUT

### 6. TemplateModule (`template_module.py`)
**Regels: 117-131** ✅ GEVALIDEERD
- Regel 117: Definitie Templates header
- Regels 119-120: Template voor Object
- Regels 122-125: Aanbevolen definitiepatronen (deverbaal patterns)
- Regels 127-130: Voorbeelden uit categorie Object

### 7. Validatieregels Modules (7 modules)
**Regels: 132-300**

#### AraiRulesModule (`arai_rules_module.py`)
**Regels: 132-142**
- Algemene Regels AI (ARAI-01 t/m ARAI-06)

#### ConRulesModule (`con_rules_module.py`)
**Regels: 143-147**
- Context Regels (CON-01, CON-02, CON-CIRC-001)

#### EssRulesModule (`ess_rules_module.py`)
**Regels: 148-155**
- Essentie Regels (ESS-01 t/m ESS-05, ESS-CONT-001)

#### StructureRulesModule (`structure_rules_module.py`)
**Regels: 156-221**
- STR-01 t/m STR-09 met uitgebreide voorbeelden

#### IntegrityRulesModule (`integrity_rules_module.py`)
**Regels: 222-285**
- INT-01 t/m INT-08 met voorbeelden

#### SamRulesModule (`sam_rules_module.py`)
**Regels: 286-295**
- SAM-01 t/m SAM-08

#### VerRulesModule (`ver_rules_module.py`)
**Regels: 296-300**
- VER-01 t/m VER-03

### 8. ErrorPreventionModule (`error_prevention_module.py`)
**Regels: 301-356** ✅ GEVALIDEERD
- Regels 301-340: Veelgemaakte fouten (vermijden!) - uitgebreide lijst verboden startwoorden
- Regels 341-344: CONTEXT-SPECIFIEKE VERBODEN
- Regels 345-355: Validatiematrix tabel
- Regel 356: Context waarschuwing

### 9. MetricsModule (`metrics_module.py`)
**Regels: 358-384** ✅ GEVALIDEERD
- Regels 358-359: Kwaliteitsmetrieken header
- Regels 360-363: Karakterlimieten
- Regels 365-368: Complexiteit indicatoren
- Regels 370-375: Kwaliteitschecks
- Regels 377-380: Context complexiteit
- Regels 382-384: Aanbevelingen voor kwaliteit

### 10. DefinitionTaskModule (`definition_task_module.py`)
**Regels: 385-423** ✅ GEVALIDEERD
- Regels 385-386: FINALE INSTRUCTIES header
- Regels 387-388: Definitieopdracht
- Regels 390-397: Constructie guide checklist
- Regels 399-404: Kwaliteitscontrole vragen
- Regels 406-410: Metadata voor traceerbaarheid
- Regel 411: Separator
- Regels 413-415: Ontologische marker instructie
- Regel 417: Finale definitie opdracht
- Regels 419-423: Promptmetadata

## Status
✅ **COMPLEET** - Alle modules zijn gevalideerd en gemapped

## Samenvattende Statistieken

| Module | Aantal Regels | Percentage |
|--------|--------------|------------|
| ExpertiseModule | 9 | 2.1% |
| OutputSpecificationModule | 12 | 2.8% |
| GrammarModule | 38 | 9.0% |
| ContextAwarenessModule | 7 | 1.7% |
| SemanticCategorisationModule | 47 | 11.1% |
| TemplateModule | 15 | 3.5% |
| AraiRulesModule | 11 | 2.6% |
| ConRulesModule | 5 | 1.2% |
| EssRulesModule | 8 | 1.9% |
| StructureRulesModule | 66 | 15.6% |
| IntegrityRulesModule | 64 | 15.1% |
| SamRulesModule | 10 | 2.4% |
| VerRulesModule | 5 | 1.2% |
| ErrorPreventionModule | 56 | 13.2% |
| MetricsModule | 27 | 6.4% |
| DefinitionTaskModule | 39 | 9.2% |
| **TOTAAL** | **419** | **99%** |

*Opmerking: 4 regels (10, 23, 62, 357) zijn lege regels voor formatting*

## Geïdentificeerde Overlappingen en Optimalisaties

### 1. Redundante Instructies
- **Dubbele context instructies**: Regels 64 en 242 bevatten vergelijkbare instructies over context gebruik
- **Meerdere "vermijd" lijsten**: Verboden patronen worden herhaald in verschillende modules

### 2. Potentiële Consolidaties
- **Validatieregels**: 7 aparte modules voor validatieregels (132-300) kunnen mogelijk gecombineerd worden
- **Kwaliteitsinstructies**: OutputSpecificationModule en MetricsModule hebben overlap in kwaliteitscriteria

### 3. Module Afhankelijkheden
- DefinitionTaskModule gebruikt output van SemanticCategorisationModule
- ErrorPreventionModule gebruikt context van ContextAwarenessModule
- TemplateModule gebruikt word_type van ExpertiseModule

## Aanbevelingen voor DEF-126

1. **Consolideer validatieregels**: Overweeg één CompositeModule voor alle validatieregels
2. **Reduceer context herhaling**: Centraliseer context instructies in ContextAwarenessModule
3. **Optimaliseer verboden patronen**: Combineer alle verboden in ErrorPreventionModule
4. **Streamline kwaliteitsmetrieken**: Merge OutputSpecificationModule en MetricsModule waar mogelijk