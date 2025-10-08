# Level Classifier - Modulaire Refactoring Plan (Optie B)

**Status:** 🔵 OPTIONEEL - Alleen NA EPIC-028
**Effort:** 7 story points
**Priority:** LOW (Tech Debt)
**Created:** 2025-10-07

---

## Executive Summary

**BELANGRIJK:** Dit plan is OPTIONEEL en alleen relevant NADAT EPIC-028 succesvol is afgerond.

**Doel:** Refactor huidige monolithische `OntologischeAnalyzer` naar modulaire architectuur met herbruikbare componenten.

**Business Value:**
- Policy-based classification (meer controle voor power users)
- Herbruikbare score generator (potentieel voor andere use cases)
- Betere testbaarheid (mocking wordt eenvoudiger)
- Duidelijkere separation of concerns

**Waarschuwing:**
- Voegt complexiteit toe (1 class → 3 classes)
- Geen directe eindgebruiker impact
- Risico op regressie als slecht uitgevoerd

---

## Huidige Architectuur (Monolithisch)

```python
class OntologischeAnalyzer:
    """
    All-in-one implementation:
    - Web lookup orchestration
    - Score generation (4 test functions)
    - Category classification (max logic)
    - Identity & role analysis
    - Documentation generation
    """

    async def bepaal_ontologische_categorie(begrip, org, jur):
        # Stap 1-2: Context gathering
        profiel = await self._stap1_lexicale_verkenning(begrip)
        context = await self._stap2_context_analyse(begrip, org, jur)

        # Stap 3: Score + Classification (MONOLITHIC)
        scores = {
            "type": await self._test_type(begrip, profiel, context),
            "proces": await self._test_proces(begrip, profiel, context),
            "resultaat": await self._test_resultaat(begrip, profiel, context),
            "exemplaar": await self._test_exemplaar(begrip, profiel, context),
        }
        categorie = max(scores, key=scores.get)  # HARD-CODED LOGIC

        # Stap 4-6: Post-processing
        ...
        return (OntologischeCategorie(categorie), resultaat)
```

**Problemen:**
1. Score generation en classification zijn gekoppeld
2. Hard-coded `max()` logica (geen policy support)
3. Moeilijk te testen (moet hele analyzer mocken)
4. Niet herbruikbaar buiten 6-stappen protocol

---

## Nieuwe Architectuur (Modulair)

### Component 1: OntologicalScoreGenerator

**Verantwoordelijkheid:** Score generatie op basis van lexicale en semantische analyse

**Locatie:** `src/services/ontology/score_generator.py`

```python
"""Score generator voor ontologische categorieën."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class OntologicalScoreGenerator:
    """
    Genereert scores voor ontologische categorieën.

    Gebruikt lexicale patterns en semantische kenmerken om te bepalen
    hoe sterk een begrip past bij elke categorie.
    """

    async def generate_scores(
        self,
        begrip: str,
        semantic_profile: dict[str, Any],
        context_map: dict[str, Any],
    ) -> dict[str, float]:
        """
        Genereer scores voor alle ontologische categorieën.

        Args:
            begrip: Te analyseren begrip
            semantic_profile: Semantische kenmerken (uit stap 1)
            context_map: Context informatie (uit stap 2)

        Returns:
            Dictionary met scores per categorie:
            {"type": 0.8, "proces": 0.3, "resultaat": 0.1, "exemplaar": 0.2}
        """
        scores = {}
        scores["type"] = await self._calculate_type_score(
            begrip, semantic_profile, context_map
        )
        scores["proces"] = await self._calculate_proces_score(
            begrip, semantic_profile, context_map
        )
        scores["resultaat"] = await self._calculate_resultaat_score(
            begrip, semantic_profile, context_map
        )
        scores["exemplaar"] = await self._calculate_exemplaar_score(
            begrip, semantic_profile, context_map
        )

        logger.debug(f"Generated scores for '{begrip}': {scores}")
        return scores

    async def _calculate_type_score(
        self, begrip: str, profile: dict, context: dict
    ) -> float:
        """Calculate TYPE category score."""
        score = 0.0

        # Lexicale indicatoren
        type_woorden = [
            "type", "soort", "klasse", "categorie", "vorm",
            "systeem", "methode", "instrument", "tool", "middel",
        ]
        for woord in type_woorden:
            if woord in begrip.lower():
                score += 0.3

        # Sterke type woorden
        sterke_type_woorden = ["toets", "test", "document", "formulier", "certificaat"]
        for woord in sterke_type_woorden:
            if woord in begrip.lower():
                score += 0.5

        # Semantische kenmerken
        kenmerken = profile.get("semantische_kenmerken", {})
        if kenmerken.get("is_abstract", False):
            score += 0.2
        if kenmerken.get("is_concreet", False):
            score += 0.3
        if kenmerken.get("is_classificeerbaar", False):
            score += 0.4

        return min(score, 1.0)

    async def _calculate_proces_score(
        self, begrip: str, profile: dict, context: dict
    ) -> float:
        """Calculate PROCES category score."""
        # Similar logic to current _test_proces()
        ...

    async def _calculate_resultaat_score(
        self, begrip: str, profile: dict, context: dict
    ) -> float:
        """Calculate RESULTAAT category score."""
        # Similar logic to current _test_resultaat()
        ...

    async def _calculate_exemplaar_score(
        self, begrip: str, profile: dict, context: dict
    ) -> float:
        """Calculate EXEMPLAAR category score."""
        # Similar logic to current _test_exemplaar()
        ...
```

**Tests:** `tests/services/ontology/test_score_generator.py`

---

### Component 2: OntologicalLevelClassifier

**Verantwoordelijkheid:** Policy-based classificatie op basis van scores

**Locatie:** `src/services/ontology/level_classifier.py`

```python
"""Policy-based ontological level classification."""

import logging
from enum import Enum

from domain.ontological_categories import OntologischeCategorie

logger = logging.getLogger(__name__)


class ClassificationPolicy(Enum):
    """Beschikbare classificatie policies."""

    GEBALANCEERD = "gebalanceerd"  # Max score wins
    STRENG = "streng"              # Require high confidence
    CONSERVATIEF = "conservatief"  # Prefer TYPE bij ambiguity


class OntologicalLevelClassifier:
    """
    Policy-based classificatie van ontologische categorieën.

    Bepaalt de primaire categorie op basis van scores en gekozen policy.
    Verschillende policies bieden verschillende trade-offs tussen
    precision en recall.
    """

    def classify_level(
        self,
        scores: dict[str, float],
        text_context: str | None = None,
        policy_name: str = "gebalanceerd",
    ) -> OntologischeCategorie:
        """
        Classificeer begrip op basis van scores en policy.

        Args:
            scores: Scores per categorie {"type": 0.8, "proces": 0.3, ...}
            text_context: Optionele text context voor tie-breaking
            policy_name: Policy naam ("gebalanceerd", "streng", "conservatief")

        Returns:
            OntologischeCategorie enum value

        Raises:
            ValueError: Als policy_name onbekend is
        """
        try:
            policy = ClassificationPolicy(policy_name)
        except ValueError:
            logger.warning(f"Unknown policy '{policy_name}', using 'gebalanceerd'")
            policy = ClassificationPolicy.GEBALANCEERD

        if policy == ClassificationPolicy.GEBALANCEERD:
            categorie = self._apply_gebalanceerd_policy(scores)
        elif policy == ClassificationPolicy.STRENG:
            categorie = self._apply_streng_policy(scores)
        elif policy == ClassificationPolicy.CONSERVATIEF:
            categorie = self._apply_conservatief_policy(scores)
        else:
            categorie = self._apply_gebalanceerd_policy(scores)

        logger.info(
            f"Classified as '{categorie}' using policy '{policy.value}' "
            f"(scores: {scores})"
        )
        return OntologischeCategorie(categorie)

    def _apply_gebalanceerd_policy(self, scores: dict[str, float]) -> str:
        """
        Gebalanceerd: Kies categorie met hoogste score.

        Dit is de huidige default logica.
        """
        return max(scores, key=scores.get)

    def _apply_streng_policy(self, scores: dict[str, float]) -> str:
        """
        Streng: Require high confidence (score > 0.7).

        Bij lage confidence, fallback naar TYPE als conservatieve keuze.
        """
        max_cat = max(scores, key=scores.get)
        max_score = scores[max_cat]

        if max_score < 0.7:
            logger.warning(
                f"Low confidence ({max_score:.2f}), falling back to TYPE"
            )
            return "type"

        return max_cat

    def _apply_conservatief_policy(self, scores: dict[str, float]) -> str:
        """
        Conservatief: Prefer TYPE bij ambiguity.

        Bij scores binnen 0.1 van elkaar, kies TYPE als die erbij zit.
        """
        max_score = max(scores.values())
        threshold = max_score - 0.1

        # Alle candidates binnen threshold
        candidates = [cat for cat, score in scores.items() if score >= threshold]

        if len(candidates) > 1:
            logger.debug(f"Ambiguous classification: {candidates}")
            if "type" in candidates:
                return "type"

        return max(scores, key=scores.get)

    def get_confidence(self, scores: dict[str, float]) -> float:
        """
        Bereken confidence score voor classificatie.

        Returns:
            Float tussen 0.0 en 1.0
        """
        if not scores:
            return 0.0

        max_score = max(scores.values())
        second_max = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0.0

        # Confidence is hoog als max duidelijk hoger is dan tweede
        gap = max_score - second_max
        return min(max_score * (1 + gap), 1.0)
```

**Tests:** `tests/services/ontology/test_level_classifier.py`

---

### Component 3: OntologischeAnalyzer (Refactored)

**Verantwoordelijkheid:** 6-stappen protocol orchestration met DI

**Locatie:** `src/ontologie/ontological_analyzer.py` (REFACTORED)

```python
"""
Ontologische Analyzer - 6-stappen protocol met modulaire services.

REFACTORED: Nu met dependency injection voor score generator en classifier.
"""

import logging
from typing import Any

from domain.ontological_categories import OntologischeCategorie
from services.container import get_container
from services.interfaces import LookupRequest

logger = logging.getLogger(__name__)


class OntologischeAnalyzer:
    """
    6-stappen ontologisch protocol met modulaire architectuur.

    Dependencies:
    - score_generator: OntologicalScoreGenerator (DI)
    - level_classifier: OntologicalLevelClassifier (DI)
    """

    def __init__(self, score_generator=None, level_classifier=None):
        """
        Initialiseer analyzer met optionele dependencies.

        Als dependencies niet gegeven, gebruik ServiceContainer.
        """
        # Get container for web lookup service (unchanged)
        container = get_container()
        self.web_lookup_service = container.web_lookup()
        self.definitie_zoeker = DefinitieZoekerAdapter(self.web_lookup_service)

        # Dependency injection voor nieuwe modules
        if score_generator is None:
            from services.ontology.score_generator import OntologicalScoreGenerator
            score_generator = OntologicalScoreGenerator()

        if level_classifier is None:
            from services.ontology.level_classifier import OntologicalLevelClassifier
            level_classifier = OntologicalLevelClassifier()

        self.score_generator = score_generator
        self.level_classifier = level_classifier

        self.category_templates = self._load_category_templates()
        logger.info(
            "OntologischeAnalyzer initialized with modular services "
            f"(score_gen={type(score_generator).__name__}, "
            f"classifier={type(level_classifier).__name__})"
        )

    async def bepaal_ontologische_categorie(
        self,
        begrip: str,
        org_context: str = "",
        jur_context: str = "",
        classification_policy: str = "gebalanceerd",
    ) -> tuple[OntologischeCategorie, dict[str, Any]]:
        """
        Doorloop het volledige 6-stappen protocol.

        Args:
            begrip: Te analyseren begrip
            org_context: Organisatorische context
            jur_context: Juridische context
            classification_policy: Policy voor classificatie
                ("gebalanceerd", "streng", "conservatief")

        Returns:
            (OntologischeCategorie, analyse_resultaat)
        """
        try:
            logger.info(f"Start ontologische analyse voor '{begrip}'")

            # Stap 1: Lexicale verkenning (UNCHANGED)
            semantisch_profiel = await self._stap1_lexicale_verkenning(begrip)

            # Stap 2: Context analyse (UNCHANGED)
            context_map = await self._stap2_context_analyse(
                begrip, org_context, jur_context
            )

            # Stap 3: DELEGEER naar modulaire services
            test_scores = await self.score_generator.generate_scores(
                begrip, semantisch_profiel, context_map
            )

            primaire_categorie_str = self.level_classifier.classify_level(
                scores=test_scores,
                text_context=begrip,
                policy_name=classification_policy,
            )

            # Bepaal secundaire aspecten (unchanged logic)
            max_score = test_scores[primaire_categorie_str.value]
            secundaire_aspecten = [
                cat
                for cat, score in test_scores.items()
                if cat != primaire_categorie_str.value and score > 0.3
            ]

            categorie_resultaat = {
                "primaire_categorie": primaire_categorie_str.value,
                "secundaire_aspecten": secundaire_aspecten,
                "test_scores": test_scores,
                "confidence": max_score,
                "classification_policy": classification_policy,
            }

            # Stap 4-6: UNCHANGED
            identiteit_criteria = await self._stap4_identiteit_persistentie(
                begrip, categorie_resultaat
            )
            rol_analyse = await self._stap5_rol_analyse(begrip, categorie_resultaat)
            documentatie = self._stap6_documentatie(
                begrip, categorie_resultaat, identiteit_criteria, rol_analyse
            )

            # Compileer resultaat (UNCHANGED)
            analyse_resultaat = {
                "begrip": begrip,
                "semantisch_profiel": semantisch_profiel,
                "context_map": context_map,
                "categorie_resultaat": categorie_resultaat,
                "identiteit_criteria": identiteit_criteria,
                "rol_analyse": rol_analyse,
                "documentatie": documentatie,
                "reasoning": self._generate_comprehensive_reasoning(
                    begrip, categorie_resultaat, semantisch_profiel, context_map
                ),
            }

            logger.info(
                f"Analyse voltooid voor '{begrip}': "
                f"{primaire_categorie_str.value} (policy: {classification_policy})"
            )

            return (primaire_categorie_str, analyse_resultaat)

        except Exception as e:
            logger.error(f"Fout in ontologische analyse voor '{begrip}': {e}")
            return await self._fallback_analyse(begrip, org_context, jur_context)

    # Stap 1-2 blijven UNCHANGED
    # Stap 4-6 blijven UNCHANGED
    # Helper functies blijven UNCHANGED
    # _test_* functies worden VERWIJDERD (nu in score_generator)
```

---

## Implementatie Roadmap

### Fase 1: Extract Score Generator (2 SP)

**User Story:**
```
Als developer
Wil ik score generation gescheiden van classification
Zodat ik scores kan hergebruiken in andere contexten
```

**Tasks:**
1. [ ] Create `src/services/ontology/score_generator.py`
2. [ ] Move `_test_type()` → `_calculate_type_score()`
3. [ ] Move `_test_proces()` → `_calculate_proces_score()`
4. [ ] Move `_test_resultaat()` → `_calculate_resultaat_score()`
5. [ ] Move `_test_exemplaar()` → `_calculate_exemplaar_score()`
6. [ ] Add `generate_scores()` method
7. [ ] Create `tests/services/ontology/test_score_generator.py`
8. [ ] Test all 4 score calculations independently
9. [ ] Update `OntologischeAnalyzer._stap3_formele_categorietoets()` to use generator
10. [ ] Run full test suite → ensure no regressions

**Acceptance:**
- [ ] Score generator werkt standalone
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Original analyzer functionality unchanged

---

### Fase 2: Create Level Classifier (2 SP)

**User Story:**
```
Als power user
Wil ik verschillende classificatie policies kunnen kiezen
Zodat ik controle heb over type vs proces beslissingen
```

**Tasks:**
1. [ ] Create `src/services/ontology/level_classifier.py`
2. [ ] Implement `ClassificationPolicy` enum
3. [ ] Implement `classify_level()` method
4. [ ] Implement `_apply_gebalanceerd_policy()` (current max logic)
5. [ ] Implement `_apply_streng_policy()` (high confidence requirement)
6. [ ] Implement `_apply_conservatief_policy()` (prefer TYPE)
7. [ ] Implement `get_confidence()` helper
8. [ ] Create `tests/services/ontology/test_level_classifier.py`
9. [ ] Test all 3 policies with different score distributions
10. [ ] Update `OntologischeAnalyzer` to use classifier
11. [ ] Run full test suite → ensure backwards compatibility

**Acceptance:**
- [ ] All 3 policies work correctly
- [ ] Policy "gebalanceerd" produces same results as old max()
- [ ] Unit tests cover edge cases (ties, low scores, etc.)
- [ ] Integration tests pass

---

### Fase 3: Update Service Container & DI (1 SP)

**User Story:**
```
Als developer
Wil ik score generator en classifier via DI krijgen
Zodat ik makkelijk kan testen met mocks
```

**Tasks:**
1. [ ] Add `score_generator()` method to `ServiceContainer`
2. [ ] Add `level_classifier()` method to `ServiceContainer`
3. [ ] Update `ontological_analyzer()` method to inject dependencies
4. [ ] Update UI `_determine_ontological_category()` to use container
5. [ ] Update config to support classification policy setting
6. [ ] Add configuration option in UI (dropdown "Classificatie Policy")
7. [ ] Test DI injection works correctly
8. [ ] Run full test suite

**Acceptance:**
- [ ] Container provides all 3 services
- [ ] UI uses container for analyzer instantiation
- [ ] No broken dependencies
- [ ] Config changes are optional (defaults to "gebalanceerd")

---

### Fase 4: Integration Testing & Documentation (2 SP)

**User Story:**
```
Als tester
Wil ik end-to-end flows testen met verschillende policies
Zodat ik zeker weet dat niets kapot is
```

**Tasks:**
1. [ ] Create `tests/integration/test_ontological_classification_policies.py`
2. [ ] Test policy "gebalanceerd" → same as old behavior
3. [ ] Test policy "streng" → rejects low confidence
4. [ ] Test policy "conservatief" → prefers TYPE
5. [ ] Test UI integration (dropdown + generated definitions)
6. [ ] Test prompt module integration (ESS-02 section)
7. [ ] Test database storage (policy saved in metadata?)
8. [ ] Manual smoke test all policies via UI
9. [ ] Update `docs/architectuur/ontological_classification.md`
10. [ ] Update `CLAUDE.md` with new architecture
11. [ ] Create migration guide for users

**Acceptance:**
- [ ] All integration tests pass
- [ ] Manual UI testing successful
- [ ] No regressions in existing functionality
- [ ] Documentation up to date
- [ ] Migration guide available

---

## Service Container Changes

### Before (Current)

```python
# In ServiceContainer
# (No specific method - analyzer instantiated directly in UI)
```

### After (Refactored)

```python
# In ServiceContainer
def score_generator(self):
    """Get or create OntologicalScoreGenerator."""
    if "score_generator" not in self._instances:
        from services.ontology.score_generator import OntologicalScoreGenerator
        self._instances["score_generator"] = OntologicalScoreGenerator()
    return self._instances["score_generator"]

def level_classifier(self):
    """Get or create OntologicalLevelClassifier."""
    if "level_classifier" not in self._instances:
        from services.ontology.level_classifier import OntologicalLevelClassifier
        self._instances["level_classifier"] = OntologicalLevelClassifier()
    return self._instances["level_classifier"]

def ontological_analyzer(self):
    """Get or create OntologischeAnalyzer with DI."""
    if "ontological_analyzer" not in self._instances:
        from ontologie.ontological_analyzer import OntologischeAnalyzer
        self._instances["ontological_analyzer"] = OntologischeAnalyzer(
            score_generator=self.score_generator(),
            level_classifier=self.level_classifier(),
        )
    return self._instances["ontological_analyzer"]
```

---

## UI Changes

### Before (Current)

```python
# In tabbed_interface.py
async def _determine_ontological_category(self, begrip, org_context, jur_context):
    from ontologie.ontological_analyzer import OntologischeAnalyzer
    analyzer = OntologischeAnalyzer()  # Direct instantiation
    categorie, analyse = await analyzer.bepaal_ontologische_categorie(
        begrip, org_context, jur_context
    )
    # ...
```

### After (Refactored)

```python
# In tabbed_interface.py
async def _determine_ontological_category(
    self,
    begrip,
    org_context,
    jur_context,
    classification_policy="gebalanceerd"
):
    # Get analyzer via DI container
    container = get_container()
    analyzer = container.ontological_analyzer()

    categorie, analyse = await analyzer.bepaal_ontologische_categorie(
        begrip, org_context, jur_context,
        classification_policy=classification_policy  # NEW parameter
    )
    # ...
```

**UI Dropdown:**
```python
# In definition generator tab
st.selectbox(
    "Classificatie Policy",
    options=["gebalanceerd", "streng", "conservatief"],
    help="""
    - Gebalanceerd: Kies hoogste score
    - Streng: Vereis hoge confidence (>0.7)
    - Conservatief: Prefer TYPE bij ambiguity
    """,
    key="classification_policy"
)
```

---

## Testing Strategy

### Unit Tests

**test_score_generator.py:**
```python
@pytest.mark.asyncio
async def test_calculate_type_score_high():
    generator = OntologicalScoreGenerator()
    score = await generator._calculate_type_score(
        "toets",
        {"semantische_kenmerken": {"is_concreet": True, "is_classificeerbaar": True}},
        {}
    )
    assert score == 1.0  # 0.5 (toets) + 0.3 (concreet) + 0.4 (classificeerbaar) = 1.2 → 1.0

@pytest.mark.asyncio
async def test_generate_scores_integration():
    generator = OntologicalScoreGenerator()
    scores = await generator.generate_scores(
        "validatie",
        {"semantische_kenmerken": {"gebeurt_in_tijd": True}},
        {}
    )
    assert scores["proces"] > 0.5  # -tie ending + gebeurt_in_tijd
    assert scores["proces"] > scores["type"]
```

**test_level_classifier.py:**
```python
def test_classify_gebalanceerd():
    classifier = OntologicalLevelClassifier()
    categorie = classifier.classify_level(
        {"type": 0.8, "proces": 0.3, "resultaat": 0.1, "exemplaar": 0.0},
        policy_name="gebalanceerd"
    )
    assert categorie == OntologischeCategorie.TYPE

def test_classify_streng_low_confidence():
    classifier = OntologicalLevelClassifier()
    categorie = classifier.classify_level(
        {"type": 0.6, "proces": 0.5, "resultaat": 0.4, "exemplaar": 0.3},
        policy_name="streng"
    )
    assert categorie == OntologischeCategorie.TYPE  # Fallback bij < 0.7

def test_classify_conservatief_ambiguous():
    classifier = OntologicalLevelClassifier()
    categorie = classifier.classify_level(
        {"type": 0.75, "proces": 0.72, "resultaat": 0.1, "exemplaar": 0.0},
        policy_name="conservatief"
    )
    assert categorie == OntologischeCategorie.TYPE  # Prefer TYPE bij ambiguity
```

### Integration Tests

**test_ontological_classification_policies.py:**
```python
@pytest.mark.asyncio
async def test_end_to_end_gebalanceerd_policy():
    """Test dat gebalanceerd policy zelfde resultaat geeft als oude implementatie."""
    container = get_container()
    analyzer = container.ontological_analyzer()

    categorie, resultaat = await analyzer.bepaal_ontologische_categorie(
        "toets", "", "", classification_policy="gebalanceerd"
    )

    assert categorie == OntologischeCategorie.TYPE
    assert resultaat["categorie_resultaat"]["classification_policy"] == "gebalanceerd"

@pytest.mark.asyncio
async def test_end_to_end_streng_policy():
    """Test dat streng policy hogere drempel hanteert."""
    # Test met ambiguous scores
    # Verify fallback to TYPE
```

---

## Migration Guide

### For Developers

**Old Code:**
```python
from ontologie.ontological_analyzer import OntologischeAnalyzer

analyzer = OntologischeAnalyzer()
categorie, resultaat = await analyzer.bepaal_ontologische_categorie(
    begrip, org_context, jur_context
)
```

**New Code (Recommended):**
```python
from services.container import get_container

container = get_container()
analyzer = container.ontological_analyzer()  # Get via DI
categorie, resultaat = await analyzer.bepaal_ontologische_categorie(
    begrip, org_context, jur_context,
    classification_policy="gebalanceerd"  # Optional
)
```

**Backwards Compatibility:**
Oude code blijft werken! Default constructor instantiates dependencies internally.

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Regressions in classification | MEDIUM | HIGH | Comprehensive test suite + manual testing |
| Performance degradation | LOW | MEDIUM | Benchmark before/after |
| Increased complexity confuses devs | MEDIUM | MEDIUM | Clear documentation + migration guide |
| Policy confusion for users | MEDIUM | LOW | Good UI help text + sensible defaults |

---

## Rollback Plan

**If refactoring causes issues:**

1. Revert commits to before Fase 1
2. Remove new files:
   - `src/services/ontology/score_generator.py`
   - `src/services/ontology/level_classifier.py`
3. Restore original `ontological_analyzer.py` from git history
4. Run tests to verify rollback success

**Git Strategy:**
- Create feature branch `feature/modular-ontology-classification`
- Merge to main only after ALL phases pass
- Tag stable version before merge for easy rollback

---

## Success Metrics

**Technical:**
- [ ] Test coverage > 90% for new modules
- [ ] No performance regression (< 5% overhead)
- [ ] All existing tests still pass
- [ ] No new linting errors

**Functional:**
- [ ] Policy "gebalanceerd" produces identical results as old code
- [ ] All 3 policies work as specified
- [ ] UI dropdown functional
- [ ] Database stores policy metadata

**Developer Experience:**
- [ ] Mocking in tests is easier
- [ ] Code review feedback positive
- [ ] Documentation complete

---

## Follow-up Work (Post-Refactoring)

**Potential future enhancements:**

1. **Custom Policies:** Allow users to define custom classification policies in config
2. **ML-based Scoring:** Replace lexical patterns with ML model
3. **Policy Analytics:** Track which policies are most used
4. **A/B Testing:** Compare policy effectiveness on real data
5. **Score Explanation:** Generate human-readable explanation of why each score was assigned

---

## Conclusion

**WHEN TO DO THIS:**
- ✅ AFTER EPIC-028 is fully complete
- ✅ AFTER all feature removal is stable
- ✅ AFTER test coverage is good
- ✅ WHEN team has bandwidth

**WHEN NOT TO DO THIS:**
- ❌ During EPIC-028 cleanup
- ❌ When rushing to meet deadline
- ❌ If test coverage is low
- ❌ If team is under pressure

**DEFAULT RECOMMENDATION:** Wait until Q1 2026 for tech debt epic.

---

**Document Version:** 1.0
**Author:** Claude Code
**Review Status:** Ready for Review
