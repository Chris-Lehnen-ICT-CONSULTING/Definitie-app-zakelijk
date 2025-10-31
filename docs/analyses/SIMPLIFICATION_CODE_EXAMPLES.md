# Code Simplification Examples: Enterprise vs Solo Developer Patterns

**Purpose:** Concrete before/after examples showing how to simplify DefinitieApp for solo developer reality.

---

## Example 1: ServiceContainer → Module Singletons

### ❌ BEFORE: Enterprise DI Container (818 lines)

```python
# src/services/container.py
class ServiceContainer:
    """
    Simpele Dependency Injection container voor service management.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self._instances = {}
        self._lazy_instances = {}  # Cache for lazy-loaded services
        self._initialization_count = 0
        self._container_id = str(uuid.uuid4())[:8]
        self._load_configuration()
        # ... 800+ more lines

    def generator(self) -> DefinitionGeneratorInterface:
        if "generator" not in self._instances:
            orchestrator_instance = self.orchestrator()
            self._instances["generator"] = orchestrator_instance
        return self._instances["generator"]

    def repository(self) -> DefinitionRepositoryInterface:
        if "repository" not in self._instances:
            use_database = self.config.get("use_database", True)
            if use_database:
                repository = DefinitionRepository(self.db_path)
                self._instances["repository"] = repository
            else:
                self._instances["repository"] = NullDefinitionRepository()
        return self._instances["repository"]

    # ... 17 more factory methods

# Usage in main.py
container = ServiceContainer(config)
generator = container.generator()
repository = container.repository()
validator = container.validation_orchestrator()
```

### ✅ AFTER: Module Singletons (100 lines)

```python
# src/services/registry.py
"""Simple service registry with module-level singletons."""
import os

# Singletons
_generator = None
_repository = None
_validator = None
_ai_service = None
_prompt_service = None

def get_generator():
    """Get or create the definition generator."""
    global _generator
    if _generator is None:
        _generator = DefinitionOrchestrator(
            prompt_service=get_prompt_service(),
            ai_service=get_ai_service(),
            validator=get_validator(),
            repository=get_repository(),
        )
    return _generator

def get_repository():
    """Get or create the repository."""
    global _repository
    if _repository is None:
        db_path = os.getenv("DB_PATH", "data/definities.db")
        _repository = DefinitionRepository(db_path)
    return _repository

def get_validator():
    """Get or create the validator."""
    global _validator
    if _validator is None:
        _validator = ValidationService()
    return _validator

def get_ai_service():
    """Get or create AI service."""
    global _ai_service
    if _ai_service is None:
        api_key = os.getenv("OPENAI_API_KEY")
        _ai_service = AIService(api_key=api_key)
    return _ai_service

def get_prompt_service():
    """Get or create prompt service."""
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service

def reset_all():
    """Reset all singletons (for testing)."""
    global _generator, _repository, _validator, _ai_service, _prompt_service
    _generator = None
    _repository = None
    _validator = None
    _ai_service = None
    _prompt_service = None

# Usage in main.py
from services.registry import get_generator, get_repository

generator = get_generator()
repository = get_repository()
```

**Savings:** 818 → 100 lines (87% reduction)
**Benefits:**
- No complex initialization tracking
- No dual instance dictionaries
- Easy to understand and debug
- Still testable with `reset_all()`

---

## Example 2: ValidationOrchestrator → Direct Service

### ❌ BEFORE: Orchestrator Wrapping Service (284 lines)

```python
# src/services/orchestrators/validation_orchestrator_v2.py
class ValidationOrchestratorV2(ValidationOrchestratorInterface):
    def __init__(self, validation_service, cleaning_service):
        self.validation_service = validation_service
        self.cleaning_service = cleaning_service

    async def validate_text(self, begrip, text, ...):
        # Set session state flag
        SessionStateManager.set_value("validating_definition", True)

        try:
            # Optional cleaning
            cleaned_text = text
            if self.cleaning_service:
                cleaning = await self.cleaning_service.clean_text(text, begrip)
                cleaned_text = cleaning.cleaned_text

            # Call underlying service
            result = await self.validation_service.validate_definition(
                begrip=begrip, text=cleaned_text, ...
            )

            # Map result format
            return ensure_schema_compliance(result, correlation_id)

        except Exception as e:
            return create_degraded_result(error=str(e), ...)
        finally:
            # Clear session state flag
            SessionStateManager.set_value("validating_definition", False)

    async def batch_validate(self, items, max_concurrency=1):
        # Ignores max_concurrency, sequential only
        results = []
        for item in items:
            results.append(await self.validate_text(...))
        return results
```

### ✅ AFTER: Merged into ValidationService (20 lines added)

```python
# src/services/validation_service.py
class ValidationService:
    def __init__(self, cleaning_service=None):
        self.cleaning_service = cleaning_service
        self._rules = self._load_rules()

    async def validate(self, begrip, text, context=None):
        """Validate definition text."""
        # Optional cleaning
        if self.cleaning_service:
            text = await self.cleaning_service.clean(text, begrip)

        # Run validation rules
        violations = []
        for rule in self._rules:
            if not rule.check(text, begrip):
                violations.append({
                    "rule_id": rule.id,
                    "message": rule.message,
                    "severity": rule.severity,
                })

        # Calculate score
        score = 1.0 - (len(violations) / len(self._rules))

        return {
            "is_valid": score >= 0.7,
            "score": score,
            "violations": violations,
        }
```

**Savings:** 284 lines removed entirely, 20 lines added to service
**Benefits:**
- No wrapper layer
- No session state side effects
- No result format conversion
- Removed unused batch_validate

---

## Example 3: Dual Repository → Direct SQL

### ❌ BEFORE: Repository Wrapping Repository (888 lines)

```python
# src/services/definition_repository.py
class DefinitionRepository(DefinitionRepositoryInterface):
    def __init__(self, db_path):
        self.legacy_repo = LegacyRepository(db_path)  # Wrapper!
        self._stats = {"total_saves": 0, ...}

    def save(self, definition: Definition) -> int:
        # Convert Definition → DefinitieRecord
        record = self._definition_to_record(definition)

        # Delegate to legacy repository
        id = self.legacy_repo.create_definitie(record)

        # Track statistics
        self._stats["total_saves"] += 1

        return id

    def _definition_to_record(self, definition):
        """Convert Definition to DefinitieRecord (150+ lines)."""
        record = DefinitieRecord(
            begrip=definition.begrip,
            definitie=definition.definitie,
            categorie=definition.categorie or "proces",
            organisatorische_context=json.dumps(definition.organisatorische_context),
            # ... 30+ more field mappings
        )
        return record

    def _record_to_definition(self, record):
        """Convert DefinitieRecord to Definition (150+ lines)."""
        return Definition(
            begrip=record.begrip,
            definitie=record.definitie,
            organisatorische_context=json.loads(record.organisatorische_context),
            # ... 30+ more field mappings
        )
```

### ✅ AFTER: Direct SQLite Repository (250 lines)

```python
# src/services/repository.py
import sqlite3
import json
from datetime import datetime

class DefinitionRepository:
    def __init__(self, db_path="data/definities.db"):
        self.db_path = db_path

    def save(self, begrip, definitie, context, categorie="proces"):
        """Save definition directly to database."""
        with self._connection() as conn:
            cur = conn.cursor()

            # Check for duplicates
            existing = self.find_by_begrip_and_context(begrip, context)
            if existing:
                raise ValueError(f"Definition already exists: {begrip}")

            # Direct insert
            cur.execute("""
                INSERT INTO definities (
                    begrip, definitie, categorie,
                    organisatorische_context, juridische_context,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                begrip,
                definitie,
                categorie,
                json.dumps(context.get("organisatorisch", [])),
                json.dumps(context.get("juridisch", [])),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ))

            return cur.lastrowid

    def get(self, id):
        """Get definition by ID."""
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM definities WHERE id = ?", (id,))
            row = cur.fetchone()

            if not row:
                return None

            # Return as dict (no conversion layer)
            return {
                "id": row[0],
                "begrip": row[1],
                "definitie": row[2],
                "categorie": row[3],
                "organisatorische_context": json.loads(row[4] or "[]"),
                "juridische_context": json.loads(row[5] or "[]"),
                "created_at": row[6],
                "updated_at": row[7],
            }

    def find_by_begrip_and_context(self, begrip, context):
        """Check if definition exists with same context."""
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id FROM definities
                WHERE begrip = ?
                  AND organisatorische_context = ?
                  AND juridische_context = ?
            """, (
                begrip,
                json.dumps(context.get("organisatorisch", [])),
                json.dumps(context.get("juridisch", [])),
            ))
            return cur.fetchone()

    def _connection(self):
        """Context manager for database connections."""
        return sqlite3.connect(self.db_path)
```

**Savings:** 888 → 250 lines (72% reduction)
**Benefits:**
- No Definition↔Record conversion
- No wrapper repository
- No statistics tracking (query DB directly: `SELECT COUNT(*)`)
- Simpler error handling (standard exceptions)

---

## Example 4: 45-Rule Validation → 15 Critical Rules

### ❌ BEFORE: JSON + Python Dual Format (1,632 lines)

```python
# config/toetsregels/regels/VAL-LEN-001.json
{
    "id": "VAL-LEN-001",
    "prioriteit": "midden",
    "aanbeveling": "verplicht",
    "min_words": 5,
    "min_chars": 15,
    "description": "Definitie moet minimaal 5 woorden bevatten"
}

# src/toetsregels/regels/val_len_001.py
def evaluate_val_len_001(text, metadata):
    """Python implementation for VAL-LEN-001."""
    words = len(text.split())
    chars = len(text.strip())

    if words < 5 or chars < 15:
        return {
            "passed": False,
            "score": 0.0,
            "violation": {"message": "Te kort", ...}
        }
    return {"passed": True, "score": 1.0}

# src/services/validation/modular_validation_service.py (1632 lines)
class ModularValidationService:
    def _load_rules_from_manager(self):
        all_rules = self.toetsregel_manager.get_all_regels()  # 45 rules
        self._internal_rules = list(all_rules.keys())
        self._default_weights = {...}  # 45 weights

    async def validate_definition(self, begrip, text, ...):
        for code in sorted(self._internal_rules):  # 45 iterations
            score, violation = self._evaluate_rule(code, ctx)
            rule_scores[code] = score

        # Weighted aggregation
        overall = calculate_weighted_score(rule_scores, weights)

        # Category scores
        detailed = self._calculate_category_scores(rule_scores)

        # Acceptance gates (3 levels)
        gates = self._evaluate_acceptance_gates(overall, detailed, violations)
```

### ✅ AFTER: Simple Rule List (250 lines)

```python
# src/services/validation_service.py
from dataclasses import dataclass

@dataclass
class ValidationRule:
    id: str
    message: str
    check: callable  # Lambda or function
    severity: str = "error"

# 15 critical rules only
VALIDATION_RULES = [
    ValidationRule(
        id="VAL-EMP-001",
        message="Tekst mag niet leeg zijn",
        check=lambda text, begrip: len(text.strip()) > 0,
        severity="critical"
    ),
    ValidationRule(
        id="VAL-LEN-001",
        message="Minimaal 5 woorden en 15 tekens",
        check=lambda text, begrip: len(text.split()) >= 5 and len(text.strip()) >= 15,
    ),
    ValidationRule(
        id="VAL-LEN-002",
        message="Maximaal 80 woorden",
        check=lambda text, begrip: len(text.split()) <= 80,
    ),
    ValidationRule(
        id="VAL-CIRC-001",
        message=f"Definitie mag niet circulair zijn",
        check=lambda text, begrip: begrip.lower() not in text.lower(),
    ),
    ValidationRule(
        id="VAL-LANG-001",
        message="Geen informele taal",
        check=lambda text, begrip: not any(
            word in text.lower()
            for word in ["enzo", "spelletjes", "zo'n ding"]
        ),
    ),
    # ... 10 more critical rules
]

class ValidationService:
    def __init__(self):
        self.rules = VALIDATION_RULES

    async def validate(self, begrip, text):
        """Simple validation with critical rules."""
        violations = []
        critical_failures = 0

        for rule in self.rules:
            if not rule.check(text, begrip):
                violations.append({
                    "rule_id": rule.id,
                    "message": rule.message,
                    "severity": rule.severity,
                })
                if rule.severity == "critical":
                    critical_failures += 1

        # Simple scoring: 0-100
        score = max(0, 100 - (len(violations) * 10))

        # Simple pass/fail: no critical failures AND score >= 70
        is_valid = (critical_failures == 0) and (score >= 70)

        return {
            "is_valid": is_valid,
            "score": score,
            "violations": violations,
        }
```

**Savings:** 1,632 → 250 lines (85% reduction)
**Benefits:**
- No JSON files (inline rules)
- No dual format (Python only)
- Simple scoring (0-100, no weighted aggregation)
- No category bucketing
- No acceptance gates (simple threshold)
- Lambdas for simple checks (readable!)

---

## Example 5: 11-Phase Orchestration → 5-Phase Simple

### ❌ BEFORE: Enterprise Orchestration (1,147 lines)

```python
# src/services/orchestrators/definition_orchestrator_v2.py (1147 lines)
async def create_definition(self, request, context):
    # Phase 1: Security & Privacy (DPIA/AVG)
    if self.security_service:
        request = await self.security_service.sanitize_request(request)

    # Phase 2: Feedback Integration
    if self.feedback_engine:
        history = await self.feedback_engine.get_feedback(...)

    # Phase 3: Synonym Enrichment
    if self.synonym_orchestrator:
        synonyms = await self.synonym_orchestrator.ensure_synonyms(...)

    # Phase 4: Web Lookup
    if self.web_lookup_service:
        web_results = await asyncio.wait_for(
            self.web_lookup_service.lookup(...),
            timeout=10.0
        )

    # Phase 5: Document Merge
    doc_snippets = context.get("documents", {}).get("snippets", [])

    # Phase 6: Prompt Generation
    prompt_result = await self.prompt_service.build_generation_prompt(...)

    # Phase 7: AI Generation
    generation_result = await self.ai_service.generate_definition(...)

    # Phase 8: Voorbeelden Generation
    voorbeelden = await genereer_alle_voorbeelden_async(...)

    # Phase 9: Cleaning
    cleaning_result = await self.cleaning_service.clean_text(...)

    # Phase 10: Validation
    validation_result = await self.validation_service.validate_definition(...)

    # Phase 11: Enhancement (if validation failed)
    if not validation_result.is_acceptable and self.enhancement_service:
        enhanced_text = await self.enhancement_service.enhance_definition(...)

    # Phase 12: Storage
    definition_id = await self._safe_save_definition(definition)

    # Phase 13: Feedback Loop Update
    if not validation_result.is_acceptable and self.feedback_engine:
        await self.feedback_engine.process_validation_feedback(...)

    # Phase 14: Monitoring
    if self.monitoring:
        await self.monitoring.complete_generation(...)

    # Return with 25+ metadata fields
    return DefinitionResponseV2(...)
```

### ✅ AFTER: Simple 5-Phase Pipeline (175 lines)

```python
# src/services/generator.py
class DefinitionGenerator:
    def __init__(self, ai_service, validator, repository):
        self.ai = ai_service
        self.validator = validator
        self.repository = repository

    async def generate(self, begrip, context):
        """Simple 5-phase generation pipeline."""

        # Phase 1: Build prompt (with optional web lookup)
        prompt = self._build_prompt(begrip, context)

        # Phase 2: Generate with AI
        raw_text = await self.ai.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=500
        )

        # Phase 3: Clean text
        clean_text = self._clean_text(raw_text, begrip)

        # Phase 4: Validate
        validation = await self.validator.validate(begrip, clean_text)

        # Phase 5: Save (always save, even if invalid)
        definition_id = self.repository.save(
            begrip=begrip,
            definitie=clean_text,
            context=context,
            categorie=context.get("categorie", "proces")
        )

        return {
            "id": definition_id,
            "begrip": begrip,
            "definitie": clean_text,
            "validation": validation,
            "is_valid": validation["is_valid"],
        }

    def _build_prompt(self, begrip, context):
        """Build simple prompt with optional web context."""
        # Base template
        prompt = f"""Genereer een Nederlandse definitie voor: {begrip}

Context:
- Organisatorisch: {', '.join(context.get('organisatorisch', []))}
- Juridisch: {', '.join(context.get('juridisch', []))}

Eisen:
- Helder en precies
- Geen circulaire definities
- 15-80 woorden
"""

        # Optional: Add web context if available
        web_snippets = context.get("web_snippets", [])
        if web_snippets:
            prompt += "\n\nExterne bronnen:\n"
            for snippet in web_snippets[:3]:  # Top 3
                prompt += f"- {snippet}\n"

        return prompt

    def _clean_text(self, text, begrip):
        """Simple text cleaning."""
        # Remove metadata headers
        if "Ontologische categorie:" in text:
            text = text.split("Ontologische categorie:")[0]

        # Remove term prefix (e.g., "Vervoersverbod:")
        if f"{begrip}:" in text:
            text = text.split(f"{begrip}:", 1)[1]

        return text.strip()
```

**Savings:** 1,147 → 175 lines (85% reduction)
**Benefits:**
- 5 phases instead of 11-14
- No optional services (security, feedback, monitoring)
- No timeout handling (local app)
- No correlation IDs (synchronous flow)
- Simple metadata (5 fields vs 25+)
- Web lookup is optional, not required

---

## Summary: Complexity Reduction

| Pattern | Enterprise Lines | Solo Lines | Reduction | Benefit |
|---------|------------------|------------|-----------|---------|
| **ServiceContainer** | 818 | 100 | 87% | Simpler dependency management |
| **ValidationOrchestrator** | 284 | 20 (merge) | 93% | No wrapper layers |
| **DefinitionRepository** | 888 | 250 | 72% | Direct SQL, no conversions |
| **ValidationService** | 1,632 | 250 | 85% | Inline rules, simple scoring |
| **DefinitionOrchestrator** | 1,147 | 175 | 85% | Focused pipeline, no bloat |
| **TOTAL** | **4,769** | **795** | **83%** | **Massive maintainability boost** |

---

## Key Takeaways

### ✅ What to Keep
- **Type hints** - Documentation through types
- **Async/await** - Performance for AI calls
- **Simple dataclasses** - Structured data
- **Clear function names** - Self-documenting code

### ❌ What to Remove
- **Dependency injection containers** → Module singletons
- **Wrapper layers** → Direct implementations
- **Conversion layers** → Direct data access
- **Optional services** → Remove unused features
- **Complex scoring** → Simple pass/fail or 0-100
- **Statistics tracking** → Query DB directly
- **Configuration files** → Inline constants

### 🎯 Golden Rule
> **"500 lines of clear code beats 2,000 lines of flexible architecture"**

For a **solo developer desktop app**, optimize for:
- **Readability** over reusability
- **Simplicity** over sophistication
- **Direct** over abstracted
- **Clear** over clever

---

Full analysis: `docs/analyses/OVER_ENGINEERING_ANALYSIS.md`
