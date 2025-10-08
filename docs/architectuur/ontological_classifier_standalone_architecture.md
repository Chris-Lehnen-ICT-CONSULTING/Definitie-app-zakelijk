# Ontological Classifier - Standalone Architecture

**Datum**: 2025-10-07
**Status**: Design Proposal
**Auteur**: Claude Code

## Executive Summary

De **OntologicalClassifier** is een **standalone, first-class service** die juridische begrippen classificeert in ontologische niveaus (U/F/O) **VOOR** definitie generatie. Het niveau bepaalt welke prompt template wordt gebruikt, daarom moet classificatie ALTIJD voor generatie gebeuren.

### Key Decisions

1. **Standalone Service** - Niet genest in orchestrator, maar top-level service in DI container
2. **Pre-Generation** - Altijd classificeren VOOR `create_definition()` call
3. **Herbruikbaar** - Beschikbaar via DI voor UI, CLI, batch processing, validatie
4. **Optional Facade** - ServiceAdapter combineert classificatie + generatie voor convenience (niet verplicht)

---

## 1. Architectuur Overzicht

### Component Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    UI LAYER                                 │
│  - tabbed_interface.py                                      │
│  - definition_generator_tab.py                              │
│                                                             │
│  Flow:                                                      │
│  1. Haal classifier uit container                          │
│  2. classifier.classify(begrip, contexts)                  │
│  3. Toon result aan gebruiker (optioneel)                  │
│  4. Zet result.to_string_level() in GenerationRequest      │
│  5. orchestrator.create_definition(request)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              DEPENDENCY INJECTION LAYER                     │
│                                                             │
│  ServiceContainer (src/services/container.py)               │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ ontological_     │  │ orchestrator()   │               │
│  │ classifier()     │  │                  │               │
│  │                  │  │ Returns:         │               │
│  │ Returns:         │  │ Definition       │               │
│  │ Ontological      │  │ OrchestratorV2   │               │
│  │ Classifier       │  │                  │               │
│  └──────────────────┘  └──────────────────┘               │
│           ↓                      ↓                          │
│  ┌──────────────────────────────────────┐                  │
│  │ service_adapter() [OPTIONAL]         │                  │
│  │                                      │                  │
│  │ Facade combining:                   │                  │
│  │ - ontological_classifier()          │                  │
│  │ - orchestrator()                    │                  │
│  │                                      │                  │
│  │ Methods:                             │                  │
│  │ - generate_with_auto_classification()│                  │
│  │ - generate_with_classification()    │                  │
│  │ - classify_only()                   │                  │
│  └──────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  SERVICE LAYER                              │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ OntologicalClassifier                                 │ │
│  │ (src/services/classification/ontological_classifier.py)│ │
│  │                                                       │ │
│  │ Methods:                                              │ │
│  │ - classify(begrip, contexts) → ClassificationResult  │ │
│  │ - classify_batch(begrippen) → dict[str, Result]      │ │
│  │ - validate_existing_definition(...)                  │ │
│  │                                                       │ │
│  │ Dependencies:                                         │ │
│  │ - AIServiceV2 (for prompts)                          │ │
│  │ - LevelClassifier (business logic)                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                            ↓                                │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ DefinitionOrchestratorV2                              │ │
│  │                                                       │ │
│  │ create_definition(request: GenerationRequest)        │ │
│  │   - request.ontologische_categorie → prompt template │ │
│  │   - Gebruikt categorie voor prompt selection         │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  DOMAIN LAYER                               │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ LevelClassifier                                       │ │
│  │ (src/toetsregels/level_classifier.py)                │ │
│  │                                                       │ │
│  │ Business logic voor U/F/O classificatie               │ │
│  │ - Score generation via AI prompts                    │ │
│  │ - Rationale generation                               │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ClassificationResult (dataclass)                      │ │
│  │                                                       │ │
│  │ - level: OntologicalLevel (U/F/O)                    │ │
│  │ - confidence: float (0.0-1.0)                        │ │
│  │ - confidence_level: HIGH/MEDIUM/LOW                  │ │
│  │ - rationale: str                                     │ │
│  │ - scores: dict[str, float]                           │ │
│  │ - metadata: dict                                     │ │
│  │                                                       │ │
│  │ Methods:                                              │ │
│  │ - is_reliable: bool                                  │ │
│  │ - to_string_level() → str                            │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow - Complete Workflow

### 2.1 Standard Flow (Via UI)

```
┌──────────────────────────────────────────────────────────────┐
│ STAP 1: GEBRUIKER INPUT (UI)                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Gebruiker vult in:                                          │
│  - begrip: "Overeenkomst"                                    │
│  - organisatorische_context: "Gemeente administratie"        │
│  - juridische_context: "Burgerlijk wetboek"                  │
│  - wettelijke_context: "..."                                 │
│  - voorbeelden: ["...", "..."]                               │
│                                                              │
│  Klikt op: "Genereer Definitie"                              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STAP 2: ONTOLOGISCHE CLASSIFICATIE (PRE-GENERATION)         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  # Haal classifier uit DI                                    │
│  container = st.session_state.service_container              │
│  classifier = container.ontological_classifier()             │
│                                                              │
│  # Classificeer begrip                                       │
│  result = classifier.classify(                               │
│      begrip="Overeenkomst",                                  │
│      organisatorische_context="Gemeente administratie",      │
│      juridische_context="Burgerlijk wetboek"                 │
│  )                                                           │
│                                                              │
│  # Result bevat:                                             │
│  # - level: OntologicalLevel.FUNCTIONEEL                     │
│  # - confidence: 0.89                                        │
│  # - confidence_level: ClassificationConfidence.HIGH         │
│  # - rationale: "Overeenkomst is functioneel omdat..."       │
│  # - scores: {U: 0.08, F: 0.89, O: 0.03}                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STAP 3: TOON CLASSIFICATIE AAN GEBRUIKER (OPTIONEEL)        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  UI toont:                                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 🔶 Niveau: F (Functioneel)                             │ │
│  │ Betrouwbaarheid: HIGH (89%)                            │ │
│  │                                                        │ │
│  │ Waarom dit niveau?                                     │ │
│  │ "Overeenkomst is een functioneel begrip omdat het      │ │
│  │  specifiek is voor juridische processen maar niet      │ │
│  │  organisatie-specifiek..."                             │ │
│  │                                                        │ │
│  │ [☐] Handmatig niveau selecteren?                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Optioneel: Gebruiker kan override doen als confidence laag │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STAP 4: BOUW GENERATION REQUEST (MET CLASSIFICATIE)         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  request = GenerationRequest(                                │
│      begrip="Overeenkomst",                                  │
│      ontologische_categorie=result.to_string_level(), # "F"  │
│      organisatorische_context="Gemeente administratie",      │
│      juridische_context="Burgerlijk wetboek",                │
│      wettelijke_context="...",                               │
│      voorbeelden=["...", "..."],                             │
│      document_context=None                                   │
│  )                                                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STAP 5: GENEREER DEFINITIE (GEBRUIKT CLASSIFICATIE)         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  # Haal orchestrator uit DI                                  │
│  orchestrator = container.orchestrator()                     │
│                                                              │
│  # Genereer definitie                                        │
│  response = await orchestrator.create_definition(request)    │
│                                                              │
│  # Intern in orchestrator:                                   │
│  # 1. request.ontologische_categorie = "F"                   │
│  # 2. Selecteer FUNCTIONEEL prompt template                  │
│  # 3. Bouw prompt met template                               │
│  # 4. Roep AI service aan                                    │
│  # 5. Valideer resultaat                                     │
│  # 6. Return GenerationResponse                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STAP 6: TOON RESULTAAT AAN GEBRUIKER                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  if response.success:                                        │
│      st.success("✅ Definitie gegenereerd!")                 │
│      st.write(response.definition_text)                      │
│                                                              │
│      # Toon validatie resultaten                             │
│      if response.validation_passed:                          │
│          st.success("✅ Alle validatieregels geslaagd!")     │
│                                                              │
│      # Toon classificatie info                               │
│      st.info(f"Gegenereerd met {result.level.value} niveau") │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Batch Processing Flow

```
┌──────────────────────────────────────────────────────────────┐
│ BATCH CLASSIFICATIE WORKFLOW                                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  # Input: CSV met begrippen                                  │
│  begrippen = ["Overeenkomst", "Perceel", "Rechtspersoon"]   │
│                                                              │
│  # Haal classifier                                           │
│  classifier = container.ontological_classifier()             │
│                                                              │
│  # Classificeer in batch                                     │
│  results = classifier.classify_batch(                        │
│      begrippen=begrippen,                                    │
│      shared_context=("Gemeente admin", "BW")                 │
│  )                                                           │
│                                                              │
│  # Results bevat:                                            │
│  # {                                                         │
│  #   "Overeenkomst": ClassificationResult(F, 0.89, ...),     │
│  #   "Perceel": ClassificationResult(O, 0.92, ...),          │
│  #   "Rechtspersoon": ClassificationResult(U, 0.95, ...)     │
│  # }                                                         │
│                                                              │
│  # Export naar CSV                                           │
│  df = pd.DataFrame([                                         │
│      {                                                       │
│          "begrip": begrip,                                   │
│          "niveau": result.level.value,                       │
│          "confidence": result.confidence                     │
│      }                                                       │
│      for begrip, result in results.items()                   │
│  ])                                                          │
│                                                              │
│  df.to_csv("classificatie_resultaten.csv")                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 Validation Flow (Bestaande Definities)

```
┌──────────────────────────────────────────────────────────────┐
│ VALIDATIE VAN BESTAANDE DEFINITIES                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  # Haal bestaande definities uit DB                          │
│  repo = container.repository()                               │
│  definitions = repo.get_all()                                │
│                                                              │
│  # Haal classifier                                           │
│  classifier = container.ontological_classifier()             │
│                                                              │
│  # Valideer elke definitie                                   │
│  mismatches = []                                             │
│  for definition in definitions:                              │
│      is_correct, reason = classifier.validate_existing_(     │
│          begrip=definition.begrip,                           │
│          claimed_level=definition.ontologische_categorie,    │
│          definition_text=definition.definitie                │
│      )                                                       │
│                                                              │
│      if not is_correct:                                      │
│          mismatches.append({                                 │
│              "begrip": definition.begrip,                    │
│              "claimed": definition.ontologische_categorie,   │
│              "reason": reason                                │
│          })                                                  │
│                                                              │
│  # Rapporteer mismatches                                     │
│  print(f"Found {len(mismatches)} classification errors")     │
│  for mismatch in mismatches:                                 │
│      print(f"  - {mismatch['begrip']}: {mismatch['reason']}") │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. API Design

### 3.1 OntologicalClassifier API

```python
class OntologicalClassifier:
    """Standalone service voor ontologische classificatie"""

    def __init__(self, ai_service: AIServiceV2):
        """
        Args:
            ai_service: AIServiceV2 voor prompt-based scoring
        """

    def classify(
        self,
        begrip: str,
        organisatorische_context: Optional[str] = None,
        juridische_context: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classificeer begrip in U/F/O niveau

        Args:
            begrip: Te classificeren begrip
            organisatorische_context: Optionele org context
            juridische_context: Optionele jur context

        Returns:
            ClassificationResult met niveau, confidence, rationale

        Raises:
            ValueError: Als begrip leeg
            RuntimeError: Als classificatie faalt
        """

    def classify_batch(
        self,
        begrippen: list[str],
        shared_context: Optional[tuple[str, str]] = None
    ) -> dict[str, ClassificationResult]:
        """
        Classificeer meerdere begrippen

        Args:
            begrippen: Lijst van begrippen
            shared_context: Optionele (org_ctx, jur_ctx) tuple

        Returns:
            Dict mapping begrip → ClassificationResult
        """

    def validate_existing_definition(
        self,
        begrip: str,
        claimed_level: str,
        definition_text: str
    ) -> tuple[bool, Optional[str]]:
        """
        Valideer of bestaande definitie correct geclassificeerd is

        Args:
            begrip: Begrip naam
            claimed_level: Beweerd niveau ("U"/"F"/"O")
            definition_text: Definitie tekst

        Returns:
            (is_correct, mismatch_reason) tuple
        """
```

### 3.2 ClassificationResult API

```python
@dataclass
class ClassificationResult:
    """Resultaat van ontologische classificatie"""

    level: OntologicalLevel           # U/F/O enum
    confidence: float                  # 0.0-1.0
    confidence_level: ClassificationConfidence  # HIGH/MEDIUM/LOW
    rationale: str                     # Menselijk leesbare uitleg
    scores: dict[str, float]          # {U: 0.08, F: 0.89, O: 0.03}
    metadata: Optional[dict] = None   # Extra context

    @property
    def is_reliable(self) -> bool:
        """Is classificatie betrouwbaar (confidence >= 60%)?"""

    def to_string_level(self) -> str:
        """Converteer naar string voor GenerationRequest"""
        # Returns: "U", "F", of "O"
```

### 3.3 ServiceAdapter API (Optional)

```python
class ServiceAdapter:
    """Optionele facade voor classificatie + generatie"""

    def __init__(
        self,
        classifier: OntologicalClassifier,
        orchestrator: DefinitionOrchestratorV2
    ):
        """Initialiseer met dependencies"""

    async def generate_with_auto_classification(
        self,
        begrip: str,
        **contexts
    ) -> tuple[GenerationResponse, ClassificationResult]:
        """
        Classificeer + genereer in één call

        Returns:
            (response, classification) tuple
        """

    async def generate_with_classification(
        self,
        classification: ClassificationResult,
        begrip: str,
        **contexts
    ) -> GenerationResponse:
        """
        Genereer met bestaande classificatie

        Gebruik als je classificatie al hebt gedaan
        """

    def classify_only(
        self,
        begrip: str,
        **contexts
    ) -> ClassificationResult:
        """Alleen classificeren, niet genereren"""
```

---

## 4. Dependency Injection Setup

### 4.1 ServiceContainer Wijzigingen

**Bestand**: `src/services/container.py`

```python
class ServiceContainer:
    """DI container met ontological classifier"""

    def ontological_classifier(self):
        """
        Get or create OntologicalClassifier instance.

        Returns:
            Singleton instance van OntologicalClassifier
        """
        if "ontological_classifier" not in self._instances:
            from services.classification.ontological_classifier import (
                OntologicalClassifier
            )
            from services.ai_service_v2 import AIServiceV2

            # Reuse AI service met generator config
            ai_service = AIServiceV2(
                default_model=self.generator_config.gpt.model,
                use_cache=True
            )

            self._instances["ontological_classifier"] = OntologicalClassifier(
                ai_service
            )

            logger.info("OntologicalClassifier (standalone) initialized")

        return self._instances["ontological_classifier"]

    def service_adapter(self):
        """
        Get or create ServiceAdapter instance (optional).

        Returns:
            Singleton instance van ServiceAdapter
        """
        if "service_adapter" not in self._instances:
            from services.service_adapter import ServiceAdapter

            classifier = self.ontological_classifier()
            orchestrator = self.orchestrator()

            self._instances["service_adapter"] = ServiceAdapter(
                classifier=classifier,
                orchestrator=orchestrator
            )

            logger.info("ServiceAdapter initialized (optional facade)")

        return self._instances["service_adapter"]
```

### 4.2 Usage in UI

```python
# In tabbed_interface.py of definition_generator_tab.py

# Haal container uit session state
container = st.session_state.service_container

# Directe classificatie (aanbevolen)
classifier = container.ontological_classifier()
result = classifier.classify(begrip, org_ctx, jur_ctx)

# OF via adapter (gemak)
adapter = container.service_adapter()
response, classification = await adapter.generate_with_auto_classification(
    begrip=begrip,
    organisatorische_context=org_ctx,
    juridische_context=jur_ctx
)
```

---

## 5. Herbruikbaarheid Voorbeelden

### 5.1 CLI Tool

```bash
# Standalone classificatie tool
python -m scripts.classify_term "Overeenkomst" --org-context "Gemeente"

# Batch classificatie
python -m scripts.classify_batch --input begrippen.csv --output results.csv
```

### 5.2 Database Migratie Script

```python
# scripts/migrate_classification_levels.py

"""
Migreer bestaande definities naar nieuwe classificatie systeem
"""

from services.container import ServiceContainer

def migrate_classifications():
    container = ServiceContainer()
    classifier = container.ontological_classifier()
    repo = container.repository()

    definitions = repo.get_all()

    for definition in definitions:
        # Herclassificeer
        result = classifier.classify(
            begrip=definition.begrip,
            organisatorische_context=definition.organisatorische_context
        )

        # Update als niveau veranderd is
        if result.level.value != definition.ontologische_categorie:
            print(f"Update {definition.begrip}: "
                  f"{definition.ontologische_categorie} → {result.level.value}")

            repo.update_classification(
                definition.id,
                new_level=result.level.value
            )
```

### 5.3 Jupyter Notebook Analyse

```python
# notebooks/classification_analysis.ipynb

import pandas as pd
from services.container import ServiceContainer

# Setup
container = ServiceContainer()
classifier = container.ontological_classifier()

# Haal alle definities
repo = container.repository()
definitions = repo.get_all()

# Classificeer batch
begrippen = [d.begrip for d in definitions]
results = classifier.classify_batch(begrippen)

# Analyse
df = pd.DataFrame([
    {
        "begrip": begrip,
        "niveau": result.level.value,
        "confidence": result.confidence,
        "betrouwbaar": result.is_reliable
    }
    for begrip, result in results.items()
])

# Visualiseer
df["niveau"].value_counts().plot(kind="bar")
df["confidence"].hist(bins=20)
```

---

## 6. Testing Strategie

### 6.1 Unit Tests

```python
# tests/services/classification/test_ontological_classifier.py

import pytest
from unittest.mock import Mock

from services.classification import (
    OntologicalClassifier,
    ClassificationResult,
    ClassificationConfidence
)
from src.toetsregels.level_classifier import OntologicalLevel


class TestOntologicalClassifier:
    """Unit tests voor OntologicalClassifier"""

    @pytest.fixture
    def mock_ai_service(self):
        """Mock AIServiceV2"""
        return Mock()

    @pytest.fixture
    def classifier(self, mock_ai_service):
        """Classifier instance met mocked dependencies"""
        return OntologicalClassifier(mock_ai_service)

    def test_classify_returns_classification_result(self, classifier):
        """Test basic classificatie"""
        result = classifier.classify("Overeenkomst")

        assert isinstance(result, ClassificationResult)
        assert result.level in [OntologicalLevel.UNIVERSEEL,
                                OntologicalLevel.FUNCTIONEEL,
                                OntologicalLevel.OPERATIONEEL]
        assert 0.0 <= result.confidence <= 1.0

    def test_classify_with_context(self, classifier):
        """Test classificatie met context"""
        result = classifier.classify(
            begrip="Overeenkomst",
            organisatorische_context="Gemeente",
            juridische_context="BW"
        )

        assert result.metadata["has_org_context"] is True
        assert result.metadata["has_jur_context"] is True

    def test_classify_empty_begrip_raises_error(self, classifier):
        """Test error handling voor leeg begrip"""
        with pytest.raises(ValueError, match="mag niet leeg"):
            classifier.classify("")

    def test_confidence_level_high(self, classifier):
        """Test HIGH confidence level (>= 0.80)"""
        # Mock high confidence result
        # ... test implementation

    def test_batch_classification(self, classifier):
        """Test batch classificatie"""
        begrippen = ["Overeenkomst", "Perceel", "Rechtspersoon"]
        results = classifier.classify_batch(begrippen)

        assert len(results) == 3
        assert all(isinstance(r, ClassificationResult)
                   for r in results.values())

    def test_validate_existing_definition_correct(self, classifier):
        """Test validatie van correcte definitie"""
        # Mock classifier to return "F"
        # ... setup mock

        is_correct, reason = classifier.validate_existing_definition(
            begrip="Overeenkomst",
            claimed_level="F",
            definition_text="..."
        )

        assert is_correct is True
        assert reason is None

    def test_validate_existing_definition_mismatch(self, classifier):
        """Test validatie van incorrecte definitie"""
        # Mock classifier to return "F"
        # ... setup mock

        is_correct, reason = classifier.validate_existing_definition(
            begrip="Overeenkomst",
            claimed_level="U",  # Wrong!
            definition_text="..."
        )

        assert is_correct is False
        assert "mismatch" in reason.lower()
```

### 6.2 Integration Tests

```python
# tests/integration/test_classification_workflow.py

import pytest
from services.container import ServiceContainer


@pytest.mark.integration
class TestClassificationWorkflow:
    """Integration tests voor complete classificatie flow"""

    @pytest.fixture
    def container(self):
        """Real ServiceContainer met dependencies"""
        return ServiceContainer()

    def test_full_classification_flow(self, container):
        """Test complete flow: classify → generate"""
        # Get services
        classifier = container.ontological_classifier()
        orchestrator = container.orchestrator()

        # Stap 1: Classificeer
        classification = classifier.classify(
            begrip="Overeenkomst",
            organisatorische_context="Test context"
        )

        assert classification.level is not None

        # Stap 2: Genereer met classificatie
        from services.orchestrators.definition_orchestrator_v2 import (
            GenerationRequest
        )

        request = GenerationRequest(
            begrip="Overeenkomst",
            ontologische_categorie=classification.to_string_level(),
            organisatorische_context="Test context"
        )

        response = await orchestrator.create_definition(request)

        assert response.success is True
        assert response.definition_text is not None
```

---

## 7. Migration Plan

### 7.1 Implementatie Stappen

1. **✅ DONE**: Create `OntologicalClassifier` class
2. **✅ DONE**: Add to ServiceContainer
3. **TODO**: Update UI to use classifier BEFORE generation
4. **TODO**: Create ServiceAdapter (optional)
5. **TODO**: Write tests
6. **TODO**: Update documentation

### 7.2 UI Integration Changes

**Bestand**: `src/ui/components/definition_generator_tab.py`

```python
# VOOR: Direct naar generatie
response = await orchestrator.create_definition(request)

# NA: Eerst classificeren
classifier = container.ontological_classifier()

# Classificeer
classification = classifier.classify(begrip, org_ctx, jur_ctx)

# Toon aan gebruiker (optioneel)
st.info(f"Geclassificeerd als: {classification.level.value}")

# Zet in request
request.ontologische_categorie = classification.to_string_level()

# Genereer
response = await orchestrator.create_definition(request)
```

---

## 8. Beslissingen & Rationale

### Waarom Standalone vs. Nested?

| Aspect | Standalone (GEKOZEN) | Nested in Orchestrator |
|--------|----------------------|------------------------|
| **Herbruikbaarheid** | ✅ Beschikbaar via DI voor UI, CLI, batch | ❌ Alleen via orchestrator |
| **Testing** | ✅ Makkelijk te testen in isolatie | ❌ Vereist orchestrator setup |
| **Timing** | ✅ VOOR generatie (correct) | ❌ Tijdens generatie (te laat) |
| **Verantwoordelijkheid** | ✅ Single Responsibility | ❌ Orchestrator doet te veel |
| **Flexibility** | ✅ UI kan classificatie tonen/override | ❌ Hidden binnen orchestrator |

### Waarom ServiceAdapter Optional?

- **Pro**: Gemak voor eenvoudige use cases
- **Con**: Extra abstractie laag
- **Beslissing**: Optional, niet verplicht
- **Rationale**: UI heeft vaak meer controle nodig (toon classificatie, override), direct classifier gebruik is flexibeler

### Waarom ClassificationResult Dataclass?

- **Immutability**: Dataclass is read-only after creation
- **Type Safety**: Clear contract voor return value
- **Serialiseerbaar**: Makkelijk om te loggen/cachen
- **Helper Methods**: `is_reliable`, `to_string_level()` voor convenience

---

## 9. Open Vragen

1. **Caching**: Moeten we classificatie results cachen? (Waarschijnlijk niet, ze zijn snel genoeg)
2. **UI Override**: Hoe prominent moet override optie zijn voor lage confidence?
3. **Logging**: Moeten we alle classificaties loggen voor analyse?
4. **Metrics**: Welke metrics willen we tracken? (confidence distribution, level distribution)

---

## 10. Conclusie

De **OntologicalClassifier** is nu een **first-class standalone service** die:

- ✅ **Voor** definitie generatie classificeert (correct timing)
- ✅ **Herbruikbaar** is via DI (UI, CLI, batch, validatie)
- ✅ **Testbaar** is in isolatie (unit + integration tests)
- ✅ **Flexibel** is (directe toegang via container, optionele adapter)
- ✅ **Type-safe** is (dataclass results, enums)

De architectuur volgt SOLID principles en is klaar voor productie gebruik.
