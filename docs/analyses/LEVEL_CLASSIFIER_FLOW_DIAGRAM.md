# Ontological Category Classification - Flow Diagram

**Datum:** 2025-10-07
**Context:** Visualisatie van huidige implementatie

---

## Volledige Flow: Van UI naar Database

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ UI LAYER (tabbed_interface.py)                                              │
│                                                                              │
│  _generate_definition_with_hybrid_context()                                 │
│    │                                                                         │
│    ├─ Input: begrip="toets", org_context=[], jur_context=[]                 │
│    │                                                                         │
│    └─ Call: asyncio.run(_determine_ontological_category(...))               │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ ONTOLOGY LAYER (ontological_analyzer.py)                                    │
│                                                                              │
│  OntologischeAnalyzer.bepaal_ontologische_categorie()                       │
│    │                                                                         │
│    ├─ STAP 1: Lexicale Verkenning                                           │
│    │   └─ Web lookup → semantisch_profiel = {                               │
│    │         "definities": [...],                                           │
│    │         "semantische_kenmerken": {                                     │
│    │            "is_abstract": False,                                       │
│    │            "is_concreet": True,                                        │
│    │            "is_classificeerbaar": True,                                │
│    │            "gebeurt_in_tijd": False,                                   │
│    │            ...                                                          │
│    │         }                                                               │
│    │       }                                                                 │
│    │                                                                         │
│    ├─ STAP 2: Context & Domein Analyse                                      │
│    │   └─ Juridische lookup → context_map = {                               │
│    │         "juridische_verwijzingen": [...],                              │
│    │         "domein_analyse": {"rechtsgebied": "..."},                     │
│    │         "afhankelijkheden": [...]                                      │
│    │       }                                                                 │
│    │                                                                         │
│    ├─ STAP 3: Formele Categorietoets ← SCORE GENERATIE HIER                 │
│    │   │                                                                     │
│    │   ├─ _test_type(begrip, profiel, context)                              │
│    │   │   ├─ Check: "toets" in type_woorden? → +0.5                        │
│    │   │   ├─ Check: is_concreet? → +0.3                                    │
│    │   │   ├─ Check: is_classificeerbaar? → +0.4                            │
│    │   │   └─ Return: min(1.2, 1.0) = 1.0                                   │
│    │   │                                                                     │
│    │   ├─ _test_proces(begrip, profiel, context)                            │
│    │   │   ├─ Check: eindigt op "atie"/"ing"? → Nee                         │
│    │   │   ├─ Check: gebeurt_in_tijd? → Nee                                 │
│    │   │   └─ Return: 0.0                                                   │
│    │   │                                                                     │
│    │   ├─ _test_resultaat(begrip, profiel, context)                         │
│    │   │   ├─ Check: "resultaat" in begrip? → Nee                           │
│    │   │   ├─ Check: is_uitkomst? → Nee                                     │
│    │   │   └─ Return: 0.0                                                   │
│    │   │                                                                     │
│    │   ├─ _test_exemplaar(begrip, profiel, context)                         │
│    │   │   ├─ Check: "specifiek" in begrip? → Nee                           │
│    │   │   ├─ Check: is_specifiek? → Nee                                    │
│    │   │   └─ Return: 0.0                                                   │
│    │   │                                                                     │
│    │   └─ Aggregatie & Classificatie:                                       │
│    │       test_scores = {                                                  │
│    │         "type": 1.0,      ← HOOGSTE SCORE                              │
│    │         "proces": 0.0,                                                 │
│    │         "resultaat": 0.0,                                              │
│    │         "exemplaar": 0.0                                               │
│    │       }                                                                 │
│    │       primaire_categorie = max(test_scores, ...) = "type"              │
│    │       confidence = 1.0                                                 │
│    │                                                                         │
│    ├─ STAP 4: Identiteit & Persistentie                                     │
│    │   └─ _identiteit_type() → identiteitscriteria                          │
│    │                                                                         │
│    ├─ STAP 5: Rol vs Intrinsieke Eigenschappen                              │
│    │   └─ _detecteer_rol_indicatoren() → rol_analyse                        │
│    │                                                                         │
│    ├─ STAP 6: Documentatie                                                  │
│    │   └─ _genereer_definitie() → documentatie                              │
│    │                                                                         │
│    └─ Return: (                                                             │
│          OntologischeCategorie.TYPE,                                        │
│          {                                                                   │
│            "categorie_resultaat": {                                         │
│              "primaire_categorie": "type",                                  │
│              "test_scores": {"type": 1.0, ...},                             │
│              "confidence": 1.0                                              │
│            },                                                                │
│            "reasoning": "...",                                              │
│            ...                                                               │
│          }                                                                   │
│        )                                                                     │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ UI LAYER (tabbed_interface.py) - VERWERKING                                 │
│                                                                              │
│  auto_categorie = OntologischeCategorie.TYPE                                │
│  category_reasoning = "Ontologische analyse voltooid..."                    │
│  category_scores = {"type": 1.0, "proces": 0.0, ...}                        │
│                                                                              │
│  → Gebruikt in:                                                             │
│     ├─ Prompt generation (via SemanticCategorisationModule)                 │
│     ├─ UI feedback (toon scores aan gebruiker)                              │
│     └─ Database storage (bij opslaan definitie)                             │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PROMPT SERVICE (semantic_categorisation_module.py)                          │
│                                                                              │
│  SemanticCategorisationModule.execute()                                     │
│    │                                                                         │
│    ├─ Input: context.get_metadata("ontologische_categorie") = "type"        │
│    │                                                                         │
│    ├─ Set shared state: context.set_shared("ontological_category", "type")  │
│    │                                                                         │
│    └─ Generate ESS-02 section:                                              │
│        """                                                                   │
│        ### 📐 Let op betekenislaag (ESS-02):                                │
│        Je moet één van de vier categorieën expliciet maken:                 │
│        • type (soort) ← GESELECTEERD                                        │
│        • exemplaar (specifiek geval)                                        │
│        • proces (activiteit)                                                │
│        • resultaat (uitkomst)                                               │
│                                                                              │
│        **TYPE CATEGORIE - Focus op CLASSIFICATIE en KENMERKEN:**            │
│        Gebruik formuleringen zoals:                                         │
│        - 'is een soort...'                                                  │
│        - 'betreft een categorie van...'                                     │
│        - 'is een type...'                                                   │
│        ...                                                                   │
│        """                                                                   │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ DEFINITION GENERATION (via DefinitionOrchestratorV2)                        │
│                                                                              │
│  → Definitie wordt gegenereerd met TYPE-specifieke guidance                 │
│  → Bijvoorbeeld: "Een toets is een type evaluatie-instrument dat..."        │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ DATABASE LAYER (definitie_repository.py)                                    │
│                                                                              │
│  DefinitionRepository.save_definition()                                     │
│    │                                                                         │
│    └─ definitie.ontological_category = "type"  # OntologischeCategorie.value│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Fallback Flow (Bij Fouten)

```
OntologischeAnalyzer.bepaal_ontologische_categorie()
  │
  ├─ Try: Volledige 6-stappen analyse
  │   └─ Exception → Fallback
  │
  └─ Fallback: QuickOntologischeAnalyzer
      │
      ├─ Pattern matching:
      │   ├─ Eindigt op "atie"/"ing"? → PROCES
      │   ├─ Bevat "type"/"soort"? → TYPE
      │   ├─ Bevat "resultaat"? → RESULTAAT
      │   ├─ Bevat "specifiek"? → EXEMPLAAR
      │   └─ Default → TYPE
      │
      └─ Return: (categorie, "Quick analyse - {reasoning}")
```

---

## Score Berekening Details

### _test_type() Logica

```python
Score Accumulatie:
─────────────────
Lexicale Indicatoren:
  "type", "soort", "klasse", "categorie", "vorm",
  "systeem", "methode", "instrument", "tool", "middel"  → +0.3 elk

Sterke Type Indicatoren:
  "toets", "test", "document", "formulier", "certificaat"  → +0.5 elk

Semantische Kenmerken:
  is_abstract       → +0.2
  is_concreet       → +0.3
  is_classificeerbaar → +0.4

Maximum: min(accumulated_score, 1.0)

Voorbeeld voor "toets":
  "toets" in sterke_type_woorden    → +0.5
  is_concreet = True                → +0.3
  is_classificeerbaar = True        → +0.4
  Total: min(1.2, 1.0) = 1.0 ✓
```

### _test_proces() Logica

```python
Score Accumulatie:
─────────────────
Eindingen:
  -atie, -tie, -ing, -eren, -ering  → +0.4 (break na eerste match)

Proces Woorden:
  "proces", "handeling", "actie",
  "operatie", "procedure", "behandeling", "verwerking"  → +0.3 elk

Semantische Kenmerken:
  gebeurt_in_tijd   → +0.4
  heeft_actoren     → +0.2

Maximum: min(accumulated_score, 1.0)

Voorbeeld voor "validatie":
  Eindigt op "tie"          → +0.4
  gebeurt_in_tijd = True    → +0.4
  Total: min(0.8, 1.0) = 0.8 ✓
```

### _test_resultaat() Logica

```python
Score Accumulatie:
─────────────────
Resultaat Woorden:
  "resultaat", "uitkomst", "gevolg", "conclusie", "besluit"  → +0.4

Semantische Kenmerken:
  is_uitkomst       → +0.4
  heeft_oorzaak     → +0.3

Maximum: min(accumulated_score, 1.0)

Voorbeeld voor "besluit":
  "besluit" in resultaat_woorden  → +0.4
  is_uitkomst = True              → +0.4
  Total: min(0.8, 1.0) = 0.8 ✓
```

### _test_exemplaar() Logica

```python
Score Accumulatie:
─────────────────
Exemplaar Woorden:
  "specifiek", "individueel", "concreet", "bepaald"  → +0.4

Semantische Kenmerken:
  is_specifiek      → +0.4
  is_instantie      → +0.3

Maximum: min(accumulated_score, 1.0)

Voorbeeld voor "specifiek incident":
  "specifiek" in exemplaar_woorden  → +0.4
  is_specifiek = True               → +0.4
  Total: min(0.8, 1.0) = 0.8 ✓
```

---

## Integratie Punten

### 1. UI → Ontology Layer

**Interface:**
```python
async def _determine_ontological_category(
    self,
    begrip: str,
    org_context: str,
    jur_context: str
) -> tuple[OntologischeCategorie, str, dict[str, float]]:
    """
    Returns:
        (categorie, reasoning, scores)
    """
```

### 2. Ontology Layer → Prompt Service

**Data Flow:**
```python
# In _generate_definition_with_hybrid_context()
auto_categorie, category_reasoning, category_scores = asyncio.run(...)

# Doorgegeven via metadata naar prompt service
metadata = {
    "ontologische_categorie": auto_categorie.value,  # "type"
    ...
}

# Prompt service leest uit context
categorie = context.get_metadata("ontologische_categorie")
```

### 3. Prompt Service → AI Service

**ESS-02 Section Injection:**
```python
# SemanticCategorisationModule genereert:
content = """
### 📐 Let op betekenislaag (ESS-02):
**TYPE CATEGORIE - Focus op CLASSIFICATIE:**
Gebruik formuleringen zoals 'is een soort...', 'betreft een categorie van...'
...
"""

# Wordt geïnjecteerd in volledige prompt naar GPT-4
```

### 4. Generated Definition → Database

**Storage:**
```python
# In DefinitionRepository.save_definition()
definitie.ontological_category = auto_categorie.value  # "type"

# SQLite schema:
# ontological_category TEXT (stores: "type", "proces", "resultaat", "exemplaar")
```

---

## Kritieke Observatie

**ER IS GEEN GAP in deze flow:**

1. ✅ Scores worden gegenereerd in `_stap3_formele_categorietoets()`
2. ✅ Classificatie gebeurt via `max(test_scores)`
3. ✅ Categorie wordt doorgegeven aan alle layers
4. ✅ Prompt service gebruikt categorie voor ESS-02 guidance
5. ✅ Database slaat categorie op

**Geen "nieuwe implementatie" nodig.**

---

## Bestandslocaties

| Component | Bestand | Regels |
|-----------|---------|--------|
| Score Generation | `src/ontologie/ontological_analyzer.py` | L276-323 |
| Test Functions | `src/ontologie/ontological_analyzer.py` | L426-532 |
| UI Integration | `src/ui/tabbed_interface.py` | L231-291 |
| Prompt Module | `src/services/prompts/modules/semantic_categorisation_module.py` | L74-114 |
| Database Storage | `src/database/definitie_repository.py` | - |

---

**Conclusie:** Huidige implementatie is compleet en functioneel. Geen actie nodig.
