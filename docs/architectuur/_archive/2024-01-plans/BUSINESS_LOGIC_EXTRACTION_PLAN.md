# Business Logic Extraction Plan - Definitie App

## 🎯 Doel
Extract business logic uit de legacy database repository (1437 regels) naar clean services, zonder de database layer aan te raken.

## 📊 Overzicht Business Logic te Extracten

| Business Logic | Huidige Locatie | Nieuwe Service | Prioriteit | Effort |
|----------------|-----------------|----------------|------------|--------|
| Duplicate Detection | `find_duplicates()` + `_calculate_similarity()` | DuplicateDetectionService | HIGH | 1 dag |
| Status Workflow | `change_status()` | WorkflowService | HIGH | 0.5 dag |
| Import/Export | `import_from_json()` + `export_to_json()` | ImportExportService | MEDIUM | 2 dagen |
| Voorbeelden Management | `save_voorbeelden()` + `beoordeel_voorbeeld()` | VoorbeeldenService | MEDIUM | 1 dag |
| Statistics | `get_statistics()` | StatisticsService | LOW | 0.5 dag |

**Totaal: 5 dagen werk**

## 🚀 Implementatie Plan

### Week 1: Core Services (3 dagen)

#### Dag 1: Duplicate Detection Service
```python
# src/services/duplicate_detection_service.py
class DuplicateDetectionService:
    """
    Pure business logic voor duplicate detection.
    Geen database dependencies!
    """
    def __init__(self, similarity_threshold: float = 0.7):
        self.threshold = similarity_threshold

    def find_duplicates(self,
                       new_definition: Definition,
                       existing_definitions: List[Definition]) -> List[DuplicateMatch]:
        """
        Business logic voor duplicate detection.
        """
        matches = []

        for existing in existing_definitions:
            # Exact match logic
            if self._is_exact_match(new_definition, existing):
                matches.append(DuplicateMatch(
                    definition=existing,
                    score=1.0,
                    reason="Exact match: begrip + context"
                ))
            # Fuzzy match logic
            else:
                score = self._calculate_similarity(
                    new_definition.begrip,
                    existing.begrip
                )
                if score > self.threshold:
                    matches.append(DuplicateMatch(
                        definition=existing,
                        score=score,
                        reason=f"Similar: {score:.0%} match"
                    ))

        return sorted(matches, key=lambda x: x.score, reverse=True)

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Jaccard similarity algoritme."""
        set1 = set(str1.lower().split())
        set2 = set(str2.lower().split())

        if not set1 or not set2:
            return 0.0

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union

    def _is_exact_match(self, def1: Definition, def2: Definition) -> bool:
        """Business rule voor exact match."""
        return (
            def1.begrip.lower() == def2.begrip.lower() and
            def1.context == def2.context
        )
```

#### Dag 2: Workflow Service
```python
# src/services/workflow_service.py
class WorkflowService:
    """
    Business logic voor definitie status workflow.
    """
    ALLOWED_TRANSITIONS = {
        "draft": ["review", "archived"],
        "review": ["established", "draft", "archived"],
        "established": ["archived"],
        "archived": ["draft"]  # Restore mogelijk
    }

    def can_change_status(self,
                         current_status: str,
                         new_status: str,
                         user_role: str = None) -> bool:
        """
        Business rule: check of status transition toegestaan is.
        """
        allowed = self.ALLOWED_TRANSITIONS.get(current_status, [])

        # Extra business rule: alleen reviewers mogen naar 'established'
        if new_status == "established" and user_role != "reviewer":
            return False

        return new_status in allowed

    def prepare_status_change(self,
                            definition: Definition,
                            new_status: str,
                            user: str,
                            notes: str = None) -> Dict[str, Any]:
        """
        Bereid status change voor met business logic.
        """
        if not self.can_change_status(definition.status, new_status):
            raise ValueError(f"Invalid transition: {definition.status} → {new_status}")

        changes = {
            "status": new_status,
            "updated_at": datetime.now(),
            "updated_by": user
        }

        # Business rule: established requires approval info
        if new_status == "established":
            changes.update({
                "approved_by": user,
                "approved_at": datetime.now(),
                "approval_notes": notes
            })

        return changes
```

#### Dag 3: Import/Export Service (start)
```python
# src/services/import_export_service.py
class ImportExportService:
    """
    Business logic voor import/export transformaties.
    """
    def __init__(self):
        self.supported_versions = ["1.0", "1.1", "2.0"]

    def prepare_export(self,
                      definitions: List[Definition],
                      format: str = "json",
                      version: str = "2.0") -> Dict[str, Any]:
        """
        Transform definitions voor export.
        """
        if version not in self.supported_versions:
            raise ValueError(f"Unsupported version: {version}")

        export_data = {
            "version": version,
            "exported_at": datetime.now().isoformat(),
            "total_count": len(definitions),
            "definitions": []
        }

        for definition in definitions:
            # Business logic: filter sensitive data
            exported = self._transform_for_export(definition, version)
            export_data["definitions"].append(exported)

        return export_data

    def validate_import(self, data: Dict[str, Any]) -> List[str]:
        """
        Business validation voor import data.
        """
        errors = []

        # Version check
        version = data.get("version")
        if version not in self.supported_versions:
            errors.append(f"Unsupported version: {version}")

        # Required fields
        if "definitions" not in data:
            errors.append("Missing 'definitions' field")

        # Business rule: max 1000 definitions per import
        if len(data.get("definitions", [])) > 1000:
            errors.append("Too many definitions (max 1000)")

        return errors

    def transform_import(self, data: Dict[str, Any]) -> List[Definition]:
        """
        Transform import data naar Definition objects.
        """
        version = data.get("version", "1.0")
        definitions = []

        for item in data.get("definitions", []):
            definition = self._transform_from_version(item, version)
            definitions.append(definition)

        return definitions
```

### Week 2: Supporting Services (2 dagen)

#### Dag 4: Voorbeelden Service
```python
# src/services/voorbeelden_service.py
class VoorbeeldenService:
    """
    Business logic voor voorbeelden management.
    """
    MAX_ACTIVE_EXAMPLES = 5
    MIN_RATING_FOR_ACTIVE = 3.0

    def select_best_examples(self,
                           examples: List[Example],
                           max_count: int = None) -> List[Example]:
        """
        Business logic: selecteer beste voorbeelden.
        """
        max_count = max_count or self.MAX_ACTIVE_EXAMPLES

        # Sort by rating, then by date
        sorted_examples = sorted(
            examples,
            key=lambda x: (x.average_rating, x.created_at),
            reverse=True
        )

        # Business rule: only examples with good ratings
        good_examples = [
            ex for ex in sorted_examples
            if ex.average_rating >= self.MIN_RATING_FOR_ACTIVE
        ]

        return good_examples[:max_count]

    def calculate_rating(self, ratings: List[int]) -> float:
        """
        Business logic voor rating berekening.
        """
        if not ratings:
            return 0.0

        # Weighted average: recent ratings count more
        weights = [0.5 + (0.5 * i/len(ratings)) for i in range(len(ratings))]
        weighted_sum = sum(r * w for r, w in zip(ratings, weights))

        return weighted_sum / sum(weights)
```

#### Dag 5: Statistics Service
```python
# src/services/statistics_service.py
class StatisticsService:
    """
    Business intelligence en statistics logic.
    """
    def calculate_quality_metrics(self,
                                definitions: List[Definition]) -> Dict[str, Any]:
        """
        Business logic voor kwaliteitsmetrics.
        """
        total = len(definitions)
        if total == 0:
            return self._empty_metrics()

        metrics = {
            "total_definitions": total,
            "by_status": self._count_by_status(definitions),
            "quality_score": self._calculate_quality_score(definitions),
            "completeness": self._calculate_completeness(definitions),
            "validation_scores": self._aggregate_validation_scores(definitions)
        }

        return metrics

    def _calculate_quality_score(self, definitions: List[Definition]) -> float:
        """
        Business rule: quality score calculation.
        """
        scores = []

        for definition in definitions:
            score = 0.0

            # Has description: +0.3
            if definition.definitie and len(definition.definitie) > 50:
                score += 0.3

            # Has examples: +0.2
            if definition.voorbeelden:
                score += 0.2

            # Has context: +0.2
            if definition.context:
                score += 0.2

            # Validated: +0.3
            if definition.validation_score and definition.validation_score > 0.7:
                score += 0.3

            scores.append(score)

        return sum(scores) / len(scores)
```

## 🔧 Integration Strategy

### Stap 1: Services naast Legacy
```python
# src/services/__init__.py
from .duplicate_detection_service import DuplicateDetectionService
from .workflow_service import WorkflowService
from .import_export_service import ImportExportService
from .voorbeelden_service import VoorbeeldenService
from .statistics_service import StatisticsService

# Registreer in ServiceContainer
class ServiceContainer:
    def duplicate_detector(self) -> DuplicateDetectionService:
        if "duplicate_detector" not in self._instances:
            self._instances["duplicate_detector"] = DuplicateDetectionService()
        return self._instances["duplicate_detector"]

    # ... andere services
```

### Stap 2: Update Repository Wrapper
```python
# src/services/definition_repository.py
class DefinitionRepository(DefinitionRepositoryInterface):
    def __init__(self, db_path: str):
        self.legacy_repo = LegacyRepository(db_path)

        # Inject business services
        container = get_container()
        self.duplicate_service = container.duplicate_detector()
        self.workflow_service = container.workflow_service()

    def find_duplicates(self, definition: Definition) -> List[DuplicateMatch]:
        """
        Gebruik nieuwe service voor business logic.
        """
        # Haal data op via legacy
        all_definitions = self._get_all_definitions()

        # Business logic via service
        return self.duplicate_service.find_duplicates(
            definition,
            all_definitions
        )
```

### Stap 3: Gradual Migration
```python
# Feature flag voor geleidelijke migratie
USE_NEW_BUSINESS_LOGIC = os.getenv("USE_NEW_BUSINESS_LOGIC", "true")

if USE_NEW_BUSINESS_LOGIC:
    duplicates = self.duplicate_service.find_duplicates(...)
else:
    duplicates = self.legacy_repo.find_duplicates(...)
```

## ✅ Voordelen van deze aanpak

1. **Geen risico**: Legacy blijft intact
2. **Testbaar**: Pure business logic zonder database
3. **Incrementeel**: Service voor service
4. **Clean**: Business logic gescheiden van data
5. **Snel**: 5 dagen vs 15 weken

## 📅 Timeline

| Week | Deliverables | Status |
|------|-------------|--------|
| Week 1 | DuplicateDetectionService ✓<br>WorkflowService ✓<br>ImportExportService (deel 1) ✓ | Core Logic |
| Week 2 | ImportExportService (deel 2) ✓<br>VoorbeeldenService ✓<br>StatisticsService ✓ | Complete |

## 🎯 Success Criteria

- [ ] Alle business logic geëxtraheerd naar services
- [ ] Services hebben geen database dependencies
- [ ] 100% unit test coverage voor services
- [ ] Legacy repository blijft werken
- [ ] Feature flags voor gradual rollout

## 🚀 Next Steps

1. Start met `DuplicateDetectionService` (hoogste prioriteit)
2. Write unit tests voor elke service
3. Integreer met ServiceContainer
4. Update repository wrapper
5. Deploy met feature flags

---
*Geschatte effort: 5 dagen development + 2 dagen testing*
