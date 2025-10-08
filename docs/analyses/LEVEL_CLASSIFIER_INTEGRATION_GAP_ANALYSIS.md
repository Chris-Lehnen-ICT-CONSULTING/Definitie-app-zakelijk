# Level Classifier Integration Gap Analysis

**Datum:** 2025-10-07
**Epic:** EPIC-028 - Feature Cleanup & UI Simplification
**Context:** Analyseer implementatie gap tussen beoogde `level_classifier.py` en bestaande ontologische categorisatie

---

## Executive Summary

**KRITIEKE BEVINDING:** Er bestaat GEEN `level_classifier.py` implementatie in de codebase. De vraagstelling is gebaseerd op een misvatting.

**HUIDIGE STAAT:**
- ✅ Werkende ontologische categorisatie via `OntologischeAnalyzer` (6-stappen protocol)
- ✅ Werkende fallback via `QuickOntologischeAnalyzer` (pattern matching)
- ✅ Scores worden al gegenereerd in stap 3 van het 6-stappen protocol
- ✅ Integratie met UI, prompt modules, en database is compleet

**CONCLUSIE:** Er is GEEN "nieuwe implementatie" die geïntegreerd moet worden. De bestaande implementatie is volledig functioneel.

---

## 1. Huidige Implementatie Status

### 1.1 Bestaande Componenten

| Component | Locatie | Status | Functionaliteit |
|-----------|---------|--------|----------------|
| **OntologischeAnalyzer** | `src/ontologie/ontological_analyzer.py` | ✅ LIVE | 6-stappen protocol met score generatie |
| **QuickOntologischeAnalyzer** | `src/ontologie/ontological_analyzer.py` | ✅ LIVE | Fallback pattern matching |
| **OntologischeCategorie Enum** | `src/domain/ontological_categories.py` | ✅ LIVE | TYPE, PROCES, RESULTAAT, EXEMPLAAR |
| **UI Integration** | `src/ui/tabbed_interface.py` | ✅ LIVE | `_determine_ontological_category()` |
| **Prompt Module** | `src/services/prompts/modules/semantic_categorisation_module.py` | ✅ LIVE | ESS-02 categorie instructies |
| **Database Storage** | `src/database/definitie_repository.py` | ✅ LIVE | Categorie wordt opgeslagen |

### 1.2 Bestaande Score Generatie

**In `OntologischeAnalyzer._stap3_formele_categorietoets()`:**

```python
async def _stap3_formele_categorietoets(
    self,
    begrip: str,
    semantisch_profiel: dict[str, Any],
    context_map: dict[str, Any],
) -> dict[str, Any]:
    """Stap 3: Formele Categorietoets - AI-gedreven classificatie."""

    # Categorieën met testvragen
    categorie_tests = {
        "type": self._test_type,
        "proces": self._test_proces,
        "resultaat": self._test_resultaat,
        "exemplaar": self._test_exemplaar,
    }

    # Voer tests uit per categorie
    test_resultaten = {}
    for categorie, test_func in categorie_tests.items():
        score = await test_func(begrip, semantisch_profiel, context_map)
        test_resultaten[categorie] = score

    # Bepaal primaire categorie
    primaire_categorie = max(test_resultaten, key=test_resultaten.get)

    return {
        "primaire_categorie": primaire_categorie,
        "secundaire_aspecten": secundaire_aspecten,
        "test_scores": test_resultaten,  # ← SCORES WORDEN HIER GEGENEREERD
        "confidence": test_resultaten[primaire_categorie],
    }
```

**Scores Flow:**
```
OntologischeAnalyzer.bepaal_ontologische_categorie()
  → _stap3_formele_categorietoets()
    → _test_type(), _test_proces(), _test_resultaat(), _test_exemplaar()
      → Returns: {"type": 0.8, "proces": 0.3, "resultaat": 0.1, "exemplaar": 0.2}
  → Returns: (OntologischeCategorie.TYPE, {analyse_resultaat_met_scores})
```

### 1.3 UI Integration Flow

**In `tabbed_interface.py._determine_ontological_category()`:**

```python
async def _determine_ontological_category(self, begrip, org_context, jur_context):
    """Bepaal automatisch de ontologische categorie via 6-stappen protocol."""
    analyzer = OntologischeAnalyzer()
    categorie, analyse_resultaat = await analyzer.bepaal_ontologische_categorie(
        begrip, org_context, jur_context
    )

    # Haal de scores uit het analyse resultaat
    test_scores = analyse_resultaat.get("categorie_resultaat", {}).get("test_scores", {})

    return categorie, reasoning, test_scores  # ← SCORES NAAR UI
```

**UI Gebruik:**
```python
# In _generate_definition_with_hybrid_context() - L715
auto_categorie, category_reasoning, category_scores = asyncio.run(
    self._determine_ontological_category(begrip, primary_org, primary_jur)
)
```

---

## 2. Veronderstellingen in de Vraag

### 2.1 "Nieuwe level_classifier.py implementatie"

**VERONDERSTELLING:** Er zou een nieuwe `level_classifier.py` module zijn met:
```python
classify_level(
    scores: Dict[str, float],  # {"type": 0.3, "proces": 0.7, ...}
    text_context: Optional[str] = None,
    policy_name: str = "gebalanceerd"
)
```

**WERKELIJKHEID:**
- ❌ Deze file bestaat NIET in de codebase
- ❌ `find` commando retourneert geen resultaten
- ❌ `grep` voor "LevelClassifier" retourneert geen resultaten

### 2.2 "Missing Link - Wie moet scores genereren?"

**VERONDERSTELLING:** De nieuwe implementatie verwacht scores als INPUT maar die worden nergens gegenereerd.

**WERKELIJKHEID:**
- ✅ Scores worden AL gegenereerd in `OntologischeAnalyzer._stap3_formele_categorietoets()`
- ✅ Elke test functie (`_test_type()`, etc.) retourneert een score tussen 0.0 en 1.0
- ✅ Scores worden doorgegeven aan UI via return tuple

---

## 3. Analyse: Huidige Implementatie vs. Hypothetische "Nieuwe" Implementatie

### 3.1 Functionaliteit Vergelijking

| Functie | Huidige OntologischeAnalyzer | Hypothetische level_classifier |
|---------|------------------------------|-------------------------------|
| **Score Generatie** | ✅ Ja - in stap 3 via test functies | ❓ Verwacht scores als INPUT |
| **Categorie Bepaling** | ✅ Ja - max(test_scores) | ❓ Mogelijk policy-based threshold logic |
| **Context Gebruik** | ✅ Ja - org/jur context in stap 2 | ❓ Optional text_context parameter |
| **Policy Support** | ❌ Nee - hard-coded logic | ❓ Ja - "gebalanceerd" policy parameter |
| **6-Stappen Protocol** | ✅ Ja - volledig geïmplementeerd | ❌ Nee - alleen classificatie |

### 3.2 Architecturaal Verschil

**HUIDIGE AANPAK (All-in-one):**
```
Input: begrip + org_context + jur_context
  ↓
OntologischeAnalyzer
  ├─ Stap 1: Lexicale verkenning (web lookup)
  ├─ Stap 2: Context analyse (juridische lookup)
  ├─ Stap 3: Score generatie + classificatie  ← SCORES HIER
  ├─ Stap 4: Identiteit/persistentie
  ├─ Stap 5: Rol analyse
  └─ Stap 6: Documentatie
  ↓
Output: (OntologischeCategorie, analyse_resultaat_met_scores)
```

**HYPOTHETISCHE AANPAK (Modular):**
```
Input: begrip + context
  ↓
??? Score Generator Service (ONTBREEKT)
  ↓
scores: {"type": 0.8, "proces": 0.3, ...}
  ↓
level_classifier.classify_level(scores, policy="gebalanceerd")
  ↓
Output: OntologischeCategorie
```

### 3.3 Kritieke Gap in Hypothetische Implementatie

**PROBLEEM:** Als `level_classifier.py` zou bestaan zoals beschreven:

1. **Wie genereert de scores?**
   - De huidige `OntologischeAnalyzer` genereert ze intern in stap 3
   - Een standalone `level_classifier` verwacht ze als input
   - Er zou een nieuwe "Score Generator Service" nodig zijn

2. **Dubbele verantwoordelijkheid?**
   - Score generatie zit NU in stap 3 van het 6-stappen protocol
   - Als we dat splitsen, welke stappen blijven bij analyzer?

3. **Context verlies?**
   - Stap 1-2 verzamelen context uit web lookup
   - Die context wordt gebruikt in stap 3 voor betere scores
   - Als `level_classifier` alleen scores krijgt, verlies je die context

---

## 4. Waarom Deze Vraag Gesteld Werd

### 4.1 Mogelijke Oorsprong

1. **EPIC-028 Context:**
   - Epic focust op cleanup en simplificatie
   - Mogelijk was er een PLAN om `level_classifier.py` te bouwen
   - Plan is nooit geïmplementeerd

2. **US-445 Context:**
   - US-445 verwijdert "Category Regeneration Service"
   - Mogelijk verwarring tussen regeneration en classificatie

3. **Modulaire Architectuur Discussie:**
   - Er is mogelijk gesproken over het opsplitsen van `OntologischeAnalyzer`
   - Score generatie vs. classificatie logica scheiden
   - Nooit daadwerkelijk uitgevoerd

### 4.2 Wat er WEL Is

**Bestaande Modulaire Componenten:**
- ✅ `SemanticCategorisationModule` - Prompt instructies per categorie
- ✅ `OntologischeCategorie` enum - Shared type definitie
- ✅ `OntologischeAnalyzer` - Volledige 6-stappen analyse
- ✅ `QuickOntologischeAnalyzer` - Snelle fallback

**Deze zijn AL geïntegreerd en werken:**
- UI gebruikt `_determine_ontological_category()`
- Prompt service injecteert categorie-specifieke guidance via `SemanticCategorisationModule`
- Database slaat categorie op
- Validatie gebruikt categorie voor context-aware checks

---

## 5. Mogelijke Acties (Als dit een PLAN was)

### 5.1 Optie A: Status Quo Behouden ✅ AANBEVOLEN

**Rationale:**
- Huidige implementatie werkt volledig
- Voldoet aan alle requirements
- Scores worden gegenereerd en gebruikt
- Geen broken gap

**Voordelen:**
- Geen refactoring risico
- Geen regressie risico
- Focus op EPIC-028 cleanup blijft intact

**Nadelen:**
- Geen policy-based threshold logic
- Geen herbruikbare score generator

### 5.2 Optie B: Implementeer Modulaire Architectuur

**Als je toch wilt refactoren:**

```python
# src/services/ontology/score_generator.py
class OntologicalScoreGenerator:
    """Genereer scores voor ontologische categorieën."""

    async def generate_scores(
        self,
        begrip: str,
        semantic_profile: dict,
        context_map: dict
    ) -> dict[str, float]:
        """
        Genereer scores voor alle categorieën.

        Returns:
            {"type": 0.8, "proces": 0.3, "resultaat": 0.1, "exemplaar": 0.2}
        """
        scores = {}
        scores["type"] = await self._test_type(begrip, semantic_profile, context_map)
        scores["proces"] = await self._test_proces(begrip, semantic_profile, context_map)
        scores["resultaat"] = await self._test_resultaat(begrip, semantic_profile, context_map)
        scores["exemplaar"] = await self._test_exemplaar(begrip, semantic_profile, context_map)
        return scores

# src/services/ontology/level_classifier.py
class OntologicalLevelClassifier:
    """Policy-based classificatie op basis van scores."""

    def classify_level(
        self,
        scores: dict[str, float],
        text_context: str | None = None,
        policy_name: str = "gebalanceerd"
    ) -> OntologischeCategorie:
        """
        Classificeer op basis van scores en policy.

        Policies:
        - "gebalanceerd": max(scores)
        - "streng": require score > 0.7
        - "conservatief": prefer TYPE bij ambiguity
        """
        policy = self._get_policy(policy_name)
        return policy.apply(scores)

# src/ontologie/ontological_analyzer.py (REFACTORED)
class OntologischeAnalyzer:
    """6-stappen protocol - NU met geïnjecteerde services."""

    def __init__(self, score_generator, level_classifier):
        self.score_generator = score_generator
        self.level_classifier = level_classifier

    async def bepaal_ontologische_categorie(
        self, begrip: str, org_context: str, jur_context: str
    ) -> tuple[OntologischeCategorie, dict]:
        # Stap 1-2: Context verzameling (unchanged)
        semantic_profile = await self._stap1_lexicale_verkenning(begrip)
        context_map = await self._stap2_context_analyse(begrip, org_context, jur_context)

        # Stap 3: DELEGEER naar score generator
        test_scores = await self.score_generator.generate_scores(
            begrip, semantic_profile, context_map
        )

        # DELEGEER naar level classifier
        primaire_categorie = self.level_classifier.classify_level(
            scores=test_scores,
            text_context=begrip,
            policy_name="gebalanceerd"
        )

        # Stap 4-6: Unchanged
        # ...
```

**Voordelen:**
- ✅ Score generator is herbruikbaar
- ✅ Policy-based classificatie is configureerbaar
- ✅ Betere testbaarheid (mock score generator)
- ✅ Duidelijkere separation of concerns

**Nadelen:**
- ❌ Complexiteit stijgt (3 classes ipv 1)
- ❌ Refactoring risico tijdens EPIC-028 cleanup
- ❌ Extra DI configuratie nodig
- ❌ Mogelijk performance overhead (extra object creations)

### 5.3 Optie C: Hybrid - Voeg Policy Support Toe Aan Bestaande Code

**Minimale wijziging:**

```python
# In OntologischeAnalyzer._stap3_formele_categorietoets()
def _determine_category_from_scores(
    self,
    test_scores: dict[str, float],
    policy: str = "gebalanceerd"
) -> str:
    """Bepaal categorie op basis van scores en policy."""

    if policy == "gebalanceerd":
        # Huidige logica
        return max(test_scores, key=test_scores.get)

    elif policy == "streng":
        # Require high confidence
        max_cat = max(test_scores, key=test_scores.get)
        if test_scores[max_cat] < 0.7:
            return "type"  # Conservative fallback
        return max_cat

    elif policy == "conservatief":
        # Prefer TYPE bij ambiguity
        max_score = max(test_scores.values())
        candidates = [cat for cat, score in test_scores.items() if score >= max_score - 0.1]
        return "type" if "type" in candidates else candidates[0]

    return max(test_scores, key=test_scores.get)
```

**Voordelen:**
- ✅ Minimale code wijziging
- ✅ Geen architecturele refactoring
- ✅ Policy support toegevoegd
- ✅ Backwards compatible

**Nadelen:**
- ❌ Score generatie blijft gekoppeld aan analyzer
- ❌ Niet herbruikbaar buiten 6-stappen protocol

---

## 6. Integratierisico's (Als Optie B Gekozen Wordt)

### 6.1 Database Layer

**Huidige staat:**
```python
# definitie_repository.py
definitie.ontological_category = categorie.value  # OntologischeCategorie enum
```

**Risico:** GEEN - enum blijft hetzelfde

### 6.2 UI Layer

**Huidige staat:**
```python
# tabbed_interface.py
auto_categorie, category_reasoning, category_scores = asyncio.run(
    self._determine_ontological_category(begrip, primary_org, primary_jur)
)
```

**Wijziging nodig:**
```python
# Nieuwe flow met modulaire services
analyzer = OntologischeAnalyzer(score_generator, level_classifier)
auto_categorie, category_reasoning, category_scores = asyncio.run(
    analyzer.bepaal_ontologische_categorie(begrip, primary_org, primary_jur)
)
```

**Risico:** LAAG - interface blijft hetzelfde, alleen DI verandert

### 6.3 Prompt Module

**Huidige staat:**
```python
# SemanticCategorisationModule
categorie = context.get_metadata("ontologische_categorie")
context.set_shared("ontological_category", categorie)
content = self._build_ess02_section(categorie)
```

**Risico:** GEEN - categorie blijft enum value string

### 6.4 Service Container

**Huidige staat:**
```python
# container.py
# OntologischeAnalyzer wordt direct geïnstantieerd in UI
```

**Wijziging nodig:**
```python
def ontological_analyzer(self):
    if "ontological_analyzer" not in self._instances:
        score_generator = OntologicalScoreGenerator()
        level_classifier = OntologicalLevelClassifier()
        self._instances["ontological_analyzer"] = OntologischeAnalyzer(
            score_generator, level_classifier
        )
    return self._instances["ontological_analyzer"]
```

**Risico:** MEDIUM - nieuwe services toevoegen aan DI container

### 6.5 Testing

**Huidige tests:**
```python
# tests/ui/test_ui_scores.py
await interface._determine_ontological_category(begrip, org, jur)
```

**Risico:** MEDIUM - mocking wordt complexer (3 services ipv 1)

---

## 7. Implementatieplan (Als Optie B Gekozen)

### 7.1 Fase 1: Extract Score Generator (2 SP)

**Tasks:**
1. Create `src/services/ontology/score_generator.py`
2. Move test functions from `OntologischeAnalyzer` to `OntologicalScoreGenerator`
3. Add unit tests for score generator
4. Update `OntologischeAnalyzer` to use score generator

**Acceptance:**
- [ ] All score generation logic in separate class
- [ ] Original functionality unchanged
- [ ] All tests pass

### 7.2 Fase 2: Create Level Classifier (2 SP)

**Tasks:**
1. Create `src/services/ontology/level_classifier.py`
2. Implement policy-based classification logic
3. Add policy configurations (gebalanceerd, streng, conservatief)
4. Add unit tests for all policies
5. Update `OntologischeAnalyzer` to use level classifier

**Acceptance:**
- [ ] Policy-based classification works
- [ ] All 3 policies tested
- [ ] Original max() logic preserved as "gebalanceerd"

### 7.3 Fase 3: Update Service Container (1 SP)

**Tasks:**
1. Add score_generator() method to ServiceContainer
2. Add level_classifier() method to ServiceContainer
3. Update ontological_analyzer() to inject dependencies
4. Update UI to use container for analyzer instantiation

**Acceptance:**
- [ ] DI container provides all 3 services
- [ ] UI uses container instead of direct instantiation
- [ ] No broken dependencies

### 7.4 Fase 4: Integration Testing (2 SP)

**Tasks:**
1. Update integration tests
2. Test all 3 policies end-to-end
3. Verify UI integration
4. Verify prompt module integration
5. Verify database storage

**Acceptance:**
- [ ] All integration tests pass
- [ ] Manual UI testing successful
- [ ] No regressions

**Total Effort:** 7 story points

---

## 8. Aanbeveling

### 8.1 Voor EPIC-028 Cleanup Context

**AANBEVELING: Optie A - Status Quo Behouden**

**Rationale:**
1. EPIC-028 focust op VERWIJDEREN van complexiteit, niet TOEVOEGEN
2. Huidige implementatie werkt volledig en voldoet aan requirements
3. Er is GEEN "missing link" - scores worden al gegenereerd
4. Modulaire refactoring (Optie B) is 7 SP EXTRA werk
5. Risico op regressie tijdens cleanup fase is ONACCEPTABEL

**Acties:**
- ✅ GEEN wijzigingen aan ontologische categorisatie
- ✅ Focus op US-441 t/m US-446 (feature removal)
- ✅ Documenteer huidige implementatie (dit document)

### 8.2 Voor Toekomstige Epics

**OVERWEEG: Optie B of C voor latere refactoring**

**Timing:** Na EPIC-028, mogelijk in EPIC-027 of aparte tech debt epic

**Voorwaarden:**
1. EPIC-028 cleanup succesvol afgerond
2. Alle tests groen
3. Code coverage > 80%
4. Team bandwidth beschikbaar

**Business value:**
- Policy-based classification = meer controle voor power users
- Herbruikbare score generator = potentieel voor andere use cases
- Betere testbaarheid = snellere development velocity

---

## 9. Conclusie

**ER IS GEEN IMPLEMENTATIE GAP.**

De vraag is gebaseerd op een misvatting dat er een nieuwe `level_classifier.py` zou zijn. Deze bestaat niet. De huidige `OntologischeAnalyzer` implementatie:

✅ **Genereert scores** in stap 3 via test functies
✅ **Classificeert** op basis van max(scores)
✅ **Integreert** met UI, prompt modules, en database
✅ **Werkt volledig** zonder missing links

**Voor EPIC-028:** Geen actie nodig op ontologische categorisatie. Focus op feature removal (US-441 t/m US-446).

**Voor toekomst:** Overweeg modulaire refactoring (Optie B) als tech debt improvement, maar niet tijdens cleanup epic.

---

## Appendix A: Huidige Score Generatie Details

### Test Functies in OntologischeAnalyzer

**1. _test_type()** - L426-462
```python
async def _test_type(self, begrip: str, profiel: dict, context: dict) -> float:
    score = 0.0

    # Lexicale indicatoren
    type_woorden = ["type", "soort", "klasse", "categorie", ...]
    for woord in type_woorden:
        if woord in begrip.lower():
            score += 0.3

    # Sterke type woorden
    sterke_type_woorden = ["toets", "test", "document", ...]
    for woord in sterke_type_woorden:
        if woord in begrip.lower():
            score += 0.5

    # Semantische kenmerken
    kenmerken = profiel.get("semantische_kenmerken", {})
    if kenmerken.get("is_abstract", False):
        score += 0.2
    if kenmerken.get("is_concreet", False):
        score += 0.3

    return min(score, 1.0)
```

**2. _test_proces()** - L464-496
```python
async def _test_proces(self, begrip: str, profiel: dict, context: dict) -> float:
    score = 0.0

    # Lexicale indicatoren - proces eindingen
    proces_eindingen = ["atie", "tie", "ing", "eren", "ering"]
    for eind in proces_eindingen:
        if begrip.lower().endswith(eind):
            score += 0.4
            break

    # Proces woorden
    proces_woorden = ["proces", "handeling", "actie", ...]
    for woord in proces_woorden:
        if woord in begrip.lower():
            score += 0.3

    # Semantische kenmerken
    if kenmerken.get("gebeurt_in_tijd", False):
        score += 0.4

    return min(score, 1.0)
```

**3. _test_resultaat()** - L498-514
```python
async def _test_resultaat(self, begrip: str, profiel: dict, context: dict) -> float:
    score = 0.0

    # Lexicale indicatoren
    resultaat_woorden = ["resultaat", "uitkomst", "gevolg", ...]
    if any(woord in begrip.lower() for woord in resultaat_woorden):
        score += 0.4

    # Semantische kenmerken
    if kenmerken.get("is_uitkomst", False):
        score += 0.4

    return min(score, 1.0)
```

**4. _test_exemplaar()** - L516-532
```python
async def _test_exemplaar(self, begrip: str, profiel: dict, context: dict) -> float:
    score = 0.0

    # Lexicale indicatoren
    exemplaar_woorden = ["specifiek", "individueel", "concreet", "bepaald"]
    if any(woord in begrip.lower() for woord in exemplaar_woorden):
        score += 0.4

    # Semantische kenmerken
    if kenmerken.get("is_specifiek", False):
        score += 0.4

    return min(score, 1.0)
```

### Score Aggregatie

**In _stap3_formele_categorietoets():**
```python
test_resultaten = {}
for categorie, test_func in categorie_tests.items():
    score = await test_func(begrip, semantisch_profiel, context_map)
    test_resultaten[categorie] = score

# Voorbeeld output:
# {
#     "type": 0.8,
#     "proces": 0.3,
#     "resultaat": 0.1,
#     "exemplaar": 0.2
# }

# Bepaal primaire categorie
primaire_categorie = max(test_resultaten, key=test_resultaten.get)  # → "type"
```

---

## Appendix B: Bestandslocaties

| Component | Pad |
|-----------|-----|
| Ontologische Analyzer | `src/ontologie/ontological_analyzer.py` |
| Categorie Enum | `src/domain/ontological_categories.py` |
| UI Integration | `src/ui/tabbed_interface.py` (L231-291) |
| Prompt Module | `src/services/prompts/modules/semantic_categorisation_module.py` |
| Database Repository | `src/database/definitie_repository.py` |
| Service Container | `src/services/container.py` |
| Test File | `tests/ui/test_ui_scores.py` |

---

**Document Version:** 1.0
**Auteur:** Claude Code
**Review Status:** Ready for Review
