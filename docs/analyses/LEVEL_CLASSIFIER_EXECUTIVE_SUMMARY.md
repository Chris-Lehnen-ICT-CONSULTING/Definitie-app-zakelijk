# Level Classifier Integration - Executive Summary

**Datum:** 2025-10-07
**Auteur:** Claude Code
**Review:** Ready

---

## TL;DR

**ER IS GEEN IMPLEMENTATIE GAP.**

De "nieuwe `level_classifier.py`" bestaat NIET. De vraag is gebaseerd op een misvatting.

---

## Huidige Staat: VOLLEDIG FUNCTIONEEL ✅

```
Input: begrip + org_context + jur_context
  ↓
OntologischeAnalyzer (6-stappen protocol)
  ├─ Stap 1: Web lookup → semantisch profiel
  ├─ Stap 2: Juridische lookup → context map
  ├─ Stap 3: Score generatie + classificatie
  │   ├─ _test_type(begrip, profiel, context) → 0.8
  │   ├─ _test_proces(begrip, profiel, context) → 0.3
  │   ├─ _test_resultaat(begrip, profiel, context) → 0.1
  │   └─ _test_exemplaar(begrip, profiel, context) → 0.2
  │   └─ primaire_categorie = max(scores) → TYPE
  ├─ Stap 4-6: Identiteit, rol, documentatie
  └─ Output: (OntologischeCategorie.TYPE, {scores, reasoning})
```

**Alle componenten werken:**
- ✅ Score generatie in `OntologischeAnalyzer._stap3_formele_categorietoets()`
- ✅ Classificatie via `max(test_scores)`
- ✅ UI integratie via `_determine_ontological_category()`
- ✅ Prompt injection via `SemanticCategorisationModule`
- ✅ Database opslag via `DefinitionRepository`

---

## Verwarringsoorsprong

**Mogelijke bronnen:**
1. EPIC-028 cleanup discussies → plan om te refactoren nooit uitgevoerd
2. US-445 "Remove Regeneration Service" → verwarring regeneration vs classificatie
3. Theoretische discussie over modulaire architectuur → nooit geïmplementeerd

---

## Antwoorden op Kritieke Vragen

### 1. Wat is de missing link?

**ANTWOORD:** Er IS geen missing link. Scores worden al gegenereerd in stap 3.

### 2. Kan bestaande pattern matching worden gebruikt?

**ANTWOORD:** Pattern matching WORDT al gebruikt in de test functies (`_test_type()`, etc.)

### 3. Wat moet er gebeuren met OntologischeCategorie enum?

**ANTWOORD:** NIETS - blijft zoals het is. Werkt perfect.

### 4. Is dit een DROP-IN replacement?

**ANTWOORD:** Er IS geen "nieuwe implementatie" om te vervangen.

### 5. Wat zijn de integratierisico's?

**ANTWOORD:** GEEN - omdat er niets te integreren valt.

---

## Aanbeveling: GEEN ACTIE NODIG

**Voor EPIC-028 Cleanup:**
- ✅ Behoud status quo voor ontologische categorisatie
- ✅ Focus op US-441 t/m US-446 (feature removal)
- ✅ GEEN wijzigingen aan score generatie
- ✅ GEEN nieuwe level_classifier.py bouwen

**Rationale:**
1. Huidige implementatie is volledig functioneel
2. EPIC-028 gaat over VERWIJDEREN van complexity, niet TOEVOEGEN
3. Geen business value in refactoring tijdens cleanup
4. Regressie risico is ONACCEPTABEL in cleanup fase

---

## Toekomstige Overweging (Post-EPIC-028)

**ALS je toch wilt refactoren naar modulair design:**

```python
# Optie B: Modulaire Architectuur (7 SP effort)

# 1. Extract score generator
class OntologicalScoreGenerator:
    async def generate_scores(begrip, profiel, context) -> dict[str, float]:
        return {"type": 0.8, "proces": 0.3, ...}

# 2. Create policy-based classifier
class OntologicalLevelClassifier:
    def classify_level(scores, policy="gebalanceerd") -> OntologischeCategorie:
        # Policy: gebalanceerd, streng, conservatief
        return max(scores, key=scores.get)

# 3. Refactor analyzer to use DI
class OntologischeAnalyzer:
    def __init__(self, score_generator, level_classifier):
        self.score_generator = score_generator
        self.level_classifier = level_classifier
```

**Voordelen:**
- Policy-based classification (meer controle)
- Herbruikbare score generator
- Betere testbaarheid

**Nadelen:**
- +3 classes, +7 SP effort
- Complexiteit stijgt
- Geen directe business value

**Timing:** Aparte tech debt epic, NA EPIC-028

---

## Bestandslocaties

| Component | Pad |
|-----------|-----|
| **VOLLEDIG RAPPORT** | `docs/analyses/LEVEL_CLASSIFIER_INTEGRATION_GAP_ANALYSIS.md` |
| Huidige Implementatie | `src/ontologie/ontological_analyzer.py` |
| UI Integration | `src/ui/tabbed_interface.py` (L231-291) |
| Prompt Module | `src/services/prompts/modules/semantic_categorisation_module.py` |

---

**CONCLUSIE:** GEEN actie nodig. Huidige implementatie werkt volledig. Focus op EPIC-028 feature cleanup.
