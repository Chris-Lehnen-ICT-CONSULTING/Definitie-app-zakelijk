# DEF-126: Categorie-Specifieke Instructie Injectie

## ✅ De Juiste Aanpak

**Probleem:** Nu staan er instructies voor ALLE 4 categorieën in de prompt + "bepaal zelf" instructies
**Oplossing:** Eén module die ALLEEN de instructies voor de GEKOZEN categorie injecteert

## 🎯 Single Module Design

### SemanticCategorisationModule - Refactored

```python
class SemanticCategorisationModule(BasePromptModule):
    """
    Injecteert categorie-SPECIFIEKE instructies op basis van
    de door de UI/applicatie bepaalde categorie.

    GEEN categorie bepaling, alleen instructie injectie!
    """

    def execute(self, context: ModuleContext) -> ModuleOutput:
        # Haal de AL BEPAALDE categorie op
        category = context.get_metadata("ontologische_categorie")

        if not category:
            # Geen categorie? Dan geen instructies
            return ModuleOutput(content="", skip=True)

        # Injecteer ALLEEN de instructies voor DEZE categorie
        content = self._get_category_specific_instruction(category)

        # Deel met andere modules voor consistency
        context.set_shared("ontological_category", category)

        return ModuleOutput(content=content)

    def _get_category_specific_instruction(self, category: str) -> str:
        """Retourneert ALLEEN instructies voor de gegeven categorie."""

        instructions = {
            "type": """### 📐 TYPE Definitie Instructies:
Begin DIRECT met het kernwoord (zelfstandig naamwoord):
- Start: [Kernwoord] dat/die [onderscheidend kenmerk]
- Voorbeelden: "document dat...", "persoon die...", "maatregel die..."
- NIET: "soort van...", "type...", "categorie..."
- Focus op: wat maakt dit type uniek?""",

            "proces": """### 📐 PROCES Definitie Instructies:
Start met een handelingsnaamwoord:
- Start: "activiteit waarbij..." OF "handeling die..." OF "proces waarin..."
- Focus op: WIE doet WAT met welk DOEL
- Beschrijf het verloop, niet het resultaat
- Voorbeelden: "activiteit waarbij gegevens worden verzameld..."""""",

            "resultaat": """### 📐 RESULTAAT Definitie Instructies:
Beschrijf als uitkomst of product:
- Start: "resultaat van..." OF "uitkomst van..." OF "product dat ontstaat door..."
- Focus op: wat is het eindproduct/gevolg
- Verwijs naar het proces waaruit het ontstaat
- Voorbeelden: "uitkomst van een beoordelingsproces waarbij..."""",

            "exemplaar": """### 📐 EXEMPLAAR Definitie Instructies:
Beschrijf als specifiek geval:
- Start: "exemplaar van... dat..." OF "specifiek geval van..."
- Geef aan: van welke klasse dit een instantie is
- Wat maakt dit exemplaar uniek (tijd/plaats/kenmerken)
- Voorbeelden: "exemplaar van een besluit genomen op [datum] door [instantie]""""
        }

        return instructions.get(category, "")
```

## 🚫 Wat MOET Eruit

Deze instructies moeten VOLLEDIG verwijderd worden:

### 1. Uit SemanticCategorisationModule (regels 70-87)
```
❌ "Je **moet** één van de vier categorieën expliciet maken..."
❌ "BELANGRIJK: Bepaal de juiste categorie op basis van het BEGRIP zelf"
❌ "Eindigt op -ING of -TIE en beschrijft een handeling? → PROCES"
```

### 2. Uit ExpertiseModule (regel 3)
```
❌ "Als het begrip een resultaat is, beschrijf het dan als..."
```
→ Deze module weet niet welke categorie gekozen is!

### 3. Uit DefinitionTaskModule (regels 413-415)
```
❌ "Ontologische marker (lever als eerste regel):"
❌ "Ontologische categorie: kies uit [soort, exemplaar, proces, resultaat]"
```
→ De categorie is al gekozen!

### 4. Uit EssRulesModule (regel 150)
```
❌ "ESS-02 - Ontologische categorie expliciteren"
```
→ Niet nodig, categorie is al expliciet

## ✅ Nieuwe Prompt Structuur

### Voor categorie "type":
```
[ExpertiseModule output - alleen rol & basis]
[OutputSpecificationModule output]
[GrammarModule output]
[ContextAwarenessModule output]

### 📐 TYPE Definitie Instructies:
Begin DIRECT met het kernwoord...
[ALLEEN type-specifieke instructies]

[Validation rules - zonder ESS-02]
[Templates voor TYPE]
[Metrics]
[Final task - zonder "kies categorie"]
```

### Voor categorie "proces":
```
[Zelfde basis modules]

### 📐 PROCES Definitie Instructies:
Start met een handelingsnaamwoord...
[ALLEEN proces-specifieke instructies]

[Rest van de modules]
```

## 📊 Impact

### Huidige Situatie
- **65+ regels** met instructies voor ALLE categorieën
- Model moet "kiezen" terwijl keuze al gemaakt is
- Verwarrende/conflicterende instructies

### Na Implementatie
- **~10 regels** met ALLEEN relevante instructies
- Model krijgt duidelijke, specifieke instructies
- Geen verwarring meer

### Token Besparing
- **Van ~2000 tokens → ~1500 tokens** (25% reductie)
- Betere output kwaliteit (geen verwarring)
- Snellere generatie

## 🔧 Implementatie

### Stap 1: Update SemanticCategorisationModule
```python
# Volledig herschrijven naar category-specific injection
# Geen bepaling, alleen instructie selectie
```

### Stap 2: Clean andere modules
```python
# ExpertiseModule: verwijder word_type logic
# DefinitionTaskModule: verwijder "kies categorie"
# EssRulesModule: skip ESS-02
```

### Stap 3: Update TemplateModule
```python
class TemplateModule:
    def execute(self, context):
        category = context.get_shared("ontological_category")
        if not category:
            return ModuleOutput(skip=True)  # Skip als geen categorie

        # Geef ALLEEN templates voor deze categorie
        return self._get_templates_for_category(category)
```

### Stap 4: Module Orchestrator Config
```yaml
modules:
  semantic_categorisation:
    # Alleen actief als categorie bekend is
    requires: ["metadata.ontologische_categorie"]

  template:
    # Ook alleen actief met categorie
    requires: ["shared.ontological_category"]
```

## 🎯 Conclusie

Door één module verantwoordelijk te maken voor categorie-specifieke instructie injectie:
- **Elimineren we alle "bepaal zelf" instructies**
- **Reduceren we de prompt met 85%** voor categorie instructies
- **Model krijgt precise, relevante instructies**
- **Geen conflicten of verwarring meer**

Dit is DE kernverbetering voor DEF-126!