# Services Business Logic Extraction

**Date:** 2025-10-02
**Scope:** Service Layer Business Logic
**Purpose:** Extract all business rules, decision logic, and constraints from services layer for rebuild

---

## Table of Contents

1. [ServiceContainer - Dependency Injection](#servicecontainer)
2. [Orchestration Services](#orchestration-services)
3. [Generation Services](#generation-services)
4. [AI Services](#ai-services)
5. [Validation Services](#validation-services)
6. [Data Services](#data-services)
7. [Infrastructure Services](#infrastructure-services)
8. [Cross-Cutting Concerns](#cross-cutting-concerns)

---

## ServiceContainer (container.py)

### Business Rules

**1. Singleton Pattern per Service Type**
- Each service type has exactly ONE instance per container
- Services are lazy-loaded (created on first request)
- Container tracks initialization count for debugging

**2. Configuration Priority**
```
1. Explicit config passed to container
2. Environment variables (OPENAI_API_KEY, OPENAI_API_KEY_PROD)
3. Central config_manager defaults
4. Hard-coded fallbacks
```

**3. Service Dependencies**
```
DefinitionOrchestratorV2 (top-level) requires:
  → PromptServiceV2 (REQUIRED)
  → AIServiceV2 (REQUIRED)
  → ValidationOrchestratorV2 (REQUIRED)
  → CleaningService (REQUIRED)
  → DefinitionRepository (REQUIRED)
  → WebLookupService (OPTIONAL - fails gracefully)
  → EnhancementService (OPTIONAL)
  → SecurityService (OPTIONAL)
  → MonitoringService (OPTIONAL)
  → FeedbackEngine (OPTIONAL)
```

**4. Database Decision Logic**
- If `use_database=True` → DefinitionRepository with real DB
- If `use_database=False` → NullDefinitionRepository (no-op)
- Database path defaults to `data/definities.db`

**5. Duplicate Detection Integration**
```python
if config.get("use_new_duplicate_detection", True):
    repository.set_duplicate_service(duplicate_detector())
```

**6. Validation Mode Selection**
```python
if use_json_rules:
    # Use ToetsregelManager with JSON rules
    manager = get_cached_toetsregel_manager()
    vcfg = ValidationConfig.from_yaml("src/config/validation_rules.yaml")
else:
    # Use internal baseline rules (for tests)
    manager = None
    vcfg = None
```

### Decision Logic

**Generator Instance Resolution**
```
generator() method → returns orchestrator instance
Reasoning: V2 orchestrator IS the generator (no separate generator class)
```

**Validator Removal**
```
validator attribute → raises AttributeError
Reasoning: Validation now handled by ValidationOrchestratorV2, no standalone validator
```

**Web Lookup Failure Handling**
```python
try:
    web_lookup = ModernWebLookupService()
    logger.info("✅ Web lookup AVAILABLE")
except Exception as e:
    logger.error("⚠️ Web lookup FAILED - definitions WITHOUT external context")
    web_lookup = None
```
**Business Impact:** Definitions generate successfully even when web lookup fails

### Configuration Parameters

**Core Paths:**
- `db_path`: Default "data/definities.db"
- `export_dir`: Default "exports"
- `approval_gate_config_path`: Default "config/approval_gate.yaml"

**Feature Flags:**
- `use_database`: Default True
- `use_json_rules`: Default True
- `use_new_duplicate_detection`: Default True
- `enable_cleaning`: Default True
- `enable_monitoring`: Default False
- `enable_ontology`: Default True
- `enable_export_validation_gate`: Default False

**Model Configuration:**
```python
# Priority order:
1. config.get("generator_model")
2. definition_config.get("model") from central config
3. get_default_model() fallback
```

---

## Orchestration Services

### ValidationOrchestratorV2 (validation_orchestrator_v2.py)

#### Business Rules

**1. Pre-Cleaning Policy**
```
IF cleaning_service is available:
    cleaned_text = await cleaning_service.clean_text(text, begrip)
ELSE:
    cleaned_text = text (original)
```

**2. Context Enrichment**
```python
# Context dict structure:
{
    "profile": context.profile,
    "correlation_id": str(context.correlation_id),
    "locale": context.locale,
    "feature_flags": dict(context.feature_flags)
}
```

**3. Error Isolation**
```
Per validation:
- Individual failure → degraded result (not batch failure)
- Error logged with correlation_id
- Returns schema-compliant result with error details
```

**4. Schema Compliance Guarantee**
```python
result = await validation_service.validate_definition(...)
return ensure_schema_compliance(result, correlation_id)
```
**WHY:** Ensures downstream consumers always receive consistent structure

#### Decision Logic

**Batch Processing Strategy**
```
Story 2.2: Sequential processing (max_concurrency ignored)
Story 2.3 (future): Parallel processing with concurrency control
```

**Correlation ID Resolution**
```python
if context and context.correlation_id:
    correlation_id = str(context.correlation_id)
else:
    correlation_id = str(uuid.uuid4())
```

**Definition Context Enrichment** (for validate_definition)
```python
# Extract definition fields into context for duplicate checks:
- organisatorische_context → context["organisatorische_context"]
- juridische_context → context["juridische_context"]
- wettelijke_basis → context["wettelijke_basis"]
- categorie → context["categorie"]
```

**WHY:** Enables validator to perform context-aware duplicate detection

#### Validation Gates

**None** - This orchestrator is pure coordination, all gates are in underlying services

---

### DefinitionOrchestratorV2 (definition_orchestrator_v2.py)

#### Business Rules

**11-Phase Orchestration Flow:**

**Phase 1: Security & Privacy (DPIA/AVG Compliance)**
```
IF security_service available:
    sanitized_request = await security_service.sanitize_request(request)
ELSE:
    sanitized_request = request (original)
```

**Phase 2: Feedback Integration (GVI Rode Kabel)**
```
IF config.enable_feedback_loop AND feedback_engine:
    feedback_history = await feedback_engine.get_feedback_for_request(
        begrip, ontologische_categorie
    )
ELSE:
    feedback_history = None
```

**Phase 2.5: Web Lookup Context Enrichment**
```python
# Decision tree:
IF web_lookup_service is available:
    try:
        # Build context from request fields
        context_str = " | ".join(org_context + jur_context + wet_basis)

        # Configurable timeout (default 10s, override via WEB_LOOKUP_TIMEOUT_SECONDS)
        web_results = await asyncio.wait_for(
            web_lookup_service.lookup(...),
            timeout=WEB_LOOKUP_TIMEOUT
        )

        # Build provenance records with legal metadata extraction
        provenance_sources = build_provenance(web_results, extract_legal=True)

        # Mark top-K for prompt injection (default K=3)
        for i, src in enumerate(provenance_sources[:top_k]):
            src["used_in_prompt"] = True

        web_lookup_status = "success"

    except TimeoutError:
        web_lookup_status = "timeout"
        logger.warning("Proceeding WITHOUT external context")
        # Continue generation (not a failure)

    except Exception:
        web_lookup_status = "error"
        # Continue generation (not a failure)
ELSE:
    web_lookup_status = "not_available"
```

**WHY Web Lookup Never Fails Generation:**
- External context is enhancement, not requirement
- Network issues should not block definition creation
- Graceful degradation principle

**Phase 2.9: Document Snippets Merge**
```python
# Merge uploaded document snippets into provenance
docs_ctx = context.get("documents", {})
doc_snippets = docs_ctx.get("snippets", [])

if doc_snippets:
    normalized_docs = [
        {
            "provider": "documents",
            "title": s.get("title") or s.get("filename") or "document",
            "snippet": s.get("snippet", ""),
            "score": s.get("score", 0.0),
            "used_in_prompt": True,  # Always inject documents
            "source_label": "Geüpload document"
        }
        for s in doc_snippets
    ]

    # Prepend documents (highest priority)
    provenance_sources = normalized_docs + provenance_sources
```

**WHY Documents First:** User-uploaded content has highest relevance

**Phase 3: Intelligent Prompt Generation**
```python
prompt_result = await prompt_service.build_generation_prompt(
    sanitized_request,
    feedback_history=feedback_history,
    context=context  # includes web_lookup and documents
)
```

**Phase 4: AI Generation**
```python
generation_result = await ai_service.generate_definition(
    prompt=prompt_result.text,
    temperature=request.options.get("temperature", 0.7),
    max_tokens=request.options.get("max_tokens", 500),
    model=request.options.get("model", None)  # None → use default
)
```

**Phase 5: Voorbeelden Generation**
```python
voorbeelden_context = {
    "organisatorisch": request.organisatorische_context or [],
    "juridisch": request.juridische_context or [],
    "wettelijk": request.wettelijke_basis or []
}

voorbeelden = await genereer_alle_voorbeelden_async(
    begrip=request.begrip,
    definitie=generation_result.text,
    context_dict=voorbeelden_context
)
```

**Phase 6: Text Cleaning**
```python
cleaning_result = await cleaning_service.clean_text(
    generation_result.text,
    request.begrip
)
cleaned_text = cleaning_result.cleaned_text
```

**Phase 7: Validation**
```python
# Build ValidationContext with correlation_id
try:
    correlation_id = uuid.UUID(generation_id)
except:
    correlation_id = uuid.uuid4()

# Extract force_duplicate flag
meta = {"generation_id": generation_id}
if request.options and request.options.get("force_duplicate"):
    meta["force_duplicate"] = True

validation_context = ValidationContext(
    correlation_id=correlation_id,
    metadata=meta
)

# Validate using Definition object
temp_definition = Definition(
    begrip=request.begrip,
    definitie=cleaned_text,
    organisatorische_context=request.organisatorische_context or [],
    juridische_context=request.juridische_context or [],
    wettelijke_basis=request.wettelijke_basis or [],
    ontologische_categorie=request.ontologische_categorie,
    created_by=request.actor
)

raw_validation = await validation_service.validate_definition(
    definition=temp_definition,
    context=validation_context
)

validation_result = ensure_schema_compliance(raw_validation)
```

**Phase 8: Enhancement (Conditional)**
```
IF validation failed AND config.enable_enhancement AND enhancement_service:
    enhanced_text = await enhancement_service.enhance_definition(
        cleaned_text,
        validation_result.violations,
        context=request
    )

    # Re-validate enhanced text
    enhanced_validation = await validation_service.validate_definition(...)

    IF enhanced_validation.is_acceptable:
        cleaned_text = enhanced_text
        was_enhanced = True
```

**Phase 9: Definition Object Creation**
```python
definition = Definition(
    begrip=request.begrip,
    definitie=cleaned_text,
    organisatorische_context=request.organisatorische_context or [],
    juridische_context=request.juridische_context or [],
    wettelijke_basis=request.wettelijke_basis or [],
    ontologische_categorie=request.ontologische_categorie,
    ufo_categorie=request.ufo_categorie,
    valid=validation_result.is_acceptable,
    validation_violations=validation_result.violations,
    metadata={
        "model": generation_result.model,
        "tokens_used": generation_result.tokens_used,
        "prompt_components": prompt_result.components_used,
        "has_feedback": bool(feedback_history),
        "enhanced": was_enhanced,
        "generation_time": time.time() - start_time,
        "generated_at": datetime.now(UTC).isoformat(),
        "orchestrator_version": "v2.0",
        "ontological_category_used": request.ontologische_categorie,
        "sources": provenance_sources,
        "web_lookup_status": web_lookup_status,
        "web_sources_count": len(provenance_sources),
        "voorbeelden": voorbeelden,
        "prompt_text": prompt_result.text,
        "force_duplicate": request.options.get("force_duplicate", False)
    },
    created_by=request.actor,
    created_at=datetime.now(UTC)
)
```

**Phase 10: Storage**
```python
# ALWAYS save (regardless of validation score)
definition_id = await repository.save(definition)

# Log failed attempts for learning
IF NOT validation_result.is_acceptable:
    await _save_failed_attempt(definition, validation_result, generation_id)
```

**WHY Always Save:**
- User may override validation gates
- Failed definitions provide learning data
- UI needs ID for further actions

**Phase 11: Feedback Loop Update**
```
IF NOT validation_result.is_acceptable AND feedback_engine:
    await feedback_engine.process_validation_feedback(
        definition_id=generation_id,
        validation_result=validation_result,
        original_request=request
    )
```

**Phase 12: Monitoring & Metrics**
```
IF monitoring:
    await monitoring.complete_generation(
        generation_id=generation_id,
        success=validation_result.is_acceptable,
        duration=time.time() - start_time,
        token_count=generation_result.tokens_used,
        components_used=prompt_result.components_used,
        had_feedback=bool(feedback_history)
    )
```

#### Decision Logic

**Ontological Category Template Selection**
```
Request includes ontologische_categorie → passed to prompt service
Prompt service enriches context.metadata with semantic_category
Template module selects appropriate template based on category
```

**Error Handling Strategy**
```
Phase-level try/catch:
- Web lookup fails → continue with status="error"
- Voorbeelden fails → continue with empty voorbeelden
- Enhancement fails → use original text
- Overall failure → return DefinitionResponseV2 with success=False
```

**Force Duplicate Override**
```python
# In metadata:
if request.options.get("force_duplicate"):
    metadata["force_duplicate"] = True

# Passed to repository:
repository.save(definition)  # Repository checks metadata["force_duplicate"]
```

#### Validation Gates

**Quality Gate (Storage)**
- NO GATE - Always save definition
- Validation result stored in `definition.valid` field
- UI decides whether to show warnings/blocks

**Enhancement Gate**
```
IF validation_result.is_acceptable == False:
    IF config.enable_enhancement:
        IF enhancement_service available:
            → Attempt enhancement
```

---

## Generation Services

### PromptServiceV2 (prompt_service_v2.py)

#### Business Rules

**1. Context Manager Integration (US-043)**
```
Single entry point: HybridContextManager.build_enriched_context()
NO direct context manipulation in prompt service
```

**2. Ontological Category Mapping (US-179)**
```python
# Minimal ESS → Semantic category mapping:
mapping = {
    "proces": "Proces",
    "activiteit": "Proces",
    "type": "Object",
    "soort": "Object",
    "exemplaar": "Object",
    "particulier": "Object",
    "resultaat": "Maatregel",
    "uitkomst": "Maatregel"
}

if request.ontologische_categorie:
    semantic = mapping.get(request.ontologische_categorie.lower())
    if semantic:
        enriched_context.metadata["semantic_category"] = semantic
```

**WHY:** Template module needs semantic category for proper template selection

**3. Web Lookup Prompt Augmentation (Epic 3)**
```python
# Config-driven augmentation:
aug_cfg = web_lookup_config.get("prompt_augmentation", {})

IF aug_cfg.get("enabled", False):
    sources = context.get("web_lookup", {}).get("sources", [])

    IF aug_cfg.get("include_all_hits"):
        selected = sources  # All sources
    ELSE:
        selected = [s for s in sources if s.get("used_in_prompt")]

    IF aug_cfg.get("prioritize_juridical", True):
        # Sort: authoritative first, then score descending
        selected.sort(key=lambda s: (
            -1 if is_authoritative(s) else 0,
            -s.get("score", 0.0)
        ))

    # Token budget management
    max_snippets = aug_cfg.get("max_snippets", 3)
    max_tokens_per_snippet = aug_cfg.get("max_tokens_per_snippet", 100)
    total_budget = aug_cfg.get("total_token_budget", 400)

    # Build injection block
    for src in selected[:max_snippets]:
        snippet = truncate_to_tokens(src["snippet"], max_tokens_per_snippet)
        if tokens_used + estimate_tokens(snippet) > total_budget:
            break
        lines.append(f"- Bron {count}: {snippet}")
        tokens_used += estimate_tokens(snippet)

    # Insert based on position
    position = aug_cfg.get("position", "after_context")
    IF position == "prepend":
        prompt = block + "\n\n" + prompt
    ELSE:
        prompt = prompt + "\n\n" + block
```

**4. Document Snippets Injection (EPIC-018/US-229)**
```python
# Config-driven injection:
enabled = os.getenv("DOCUMENT_SNIPPETS_ENABLED", "true") == "true"
max_snippets = int(os.getenv("DOCUMENT_SNIPPETS_MAX", "16"))
max_chars = int(os.getenv("DOCUMENT_SNIPPETS_MAX_CHARS", "800"))

IF enabled AND doc_snippets:
    lines = ["📄 DOCUMENTCONTEXT (snippets):"]

    for s in doc_snippets[:max_snippets]:
        snippet = sanitize_snippet(s["snippet"])[:remaining_chars]
        title = s.get("title") or s.get("filename") or "document"
        cite = s.get("citation_label")

        prefix = f"• {title}"
        if cite:
            prefix += f" ({cite})"

        lines.append(f"{prefix}: {snippet}")

    # Prepend to prompt (context first)
    prompt = "\n".join(lines) + "\n\n" + prompt
```

#### Decision Logic

**Feedback Integration**
```python
feedback_integrated = bool(feedback_history)
# Feedback passed to UnifiedPromptBuilder for prompt enhancement
```

**Token Optimization**
```python
# Rough estimation: words * 1.3
token_count = len(prompt_text.split()) * 1.3

IF token_count > config.max_token_limit:
    # No truncation implemented (would need priority-based removal)
    pass
```

**Component Tracking**
```python
components_used = ["base_template"]

IF request.ontologische_categorie:
    components_used.append(f"ontologische_{request.ontologische_categorie}")

IF enriched_context.metadata.get("juridisch_context"):
    components_used.append("juridisch_template")
```

#### Configuration Parameters

**PromptServiceConfig:**
- `max_token_limit`: 10000 (hard limit)
- `cache_enabled`: True
- `cache_ttl_seconds`: 3600
- `feedback_integration`: True
- `token_optimization`: True

**Web Lookup Augmentation:**
- `enabled`: False (default, enable via config)
- `max_snippets`: 3
- `max_tokens_per_snippet`: 100
- `total_token_budget`: 400
- `position`: "after_context" | "prepend"
- `include_all_hits`: False
- `prioritize_juridical`: True

**Document Snippets:**
- `DOCUMENT_SNIPPETS_ENABLED`: "true"
- `DOCUMENT_SNIPPETS_MAX`: 16
- `DOCUMENT_SNIPPETS_MAX_CHARS`: 800

---

### AIServiceV2 (ai_service_v2.py)

#### Business Rules

**1. Rate Limiting**
```python
RateLimitConfig(
    requests_per_minute=60,    # From config_manager
    requests_per_hour=3000,
    max_concurrent=10,
    backoff_factor=1.5,
    max_retries=3
)
```

**2. Token Estimation**
```python
# Priority order:
1. tiktoken.encoding_for_model(model) if available
2. Heuristic: len(text) * 0.75 with bounds [0.5, 1.0] tokens/char

# WHY heuristic: >90% accuracy for Dutch/English text without tiktoken dependency
```

**3. Caching Strategy**
```python
# V1-compatible cache key:
cache_key = f"{model}:{temperature}:{max_tokens}:{hash(prompt)}:{hash(system_prompt)}"

IF use_cache AND cached_result exists:
    return cached_result (with cached=True flag)

result = await api_call(...)

IF use_cache:
    cache.set(cache_key, result, ttl=3600)
```

**4. Error Handling**
```python
try:
    result = await asyncio.wait_for(api_call(...), timeout=timeout_seconds)
except TimeoutError:
    raise AITimeoutError(f"Timed out after {timeout_seconds}s")
except RateLimitError:
    raise AIRateLimitError(str(e))
except APIConnectionError as e:
    if "timeout" in str(e).lower():
        raise AITimeoutError(str(e))
    raise AIServiceError(str(e))
except OpenAIError:
    raise AIServiceError(str(e))
```

**WHY Specific Exceptions:** Enables orchestrator to handle different failure modes

#### Decision Logic

**Model Selection**
```python
model_to_use = model or self.default_model
# Default: "gpt-4o-mini" (from config)
```

**Batch Processing**
```python
tasks = [generate_definition(...) for req in requests]
results = await asyncio.gather(*tasks, return_exceptions=True)

# Re-raise exceptions with context
for i, result in enumerate(results):
    if isinstance(result, Exception):
        raise AIServiceError(f"Batch request {i} failed: {result}")
```

#### Configuration Parameters

- `default_model`: "gpt-4o-mini"
- `use_cache`: True
- `timeout_seconds`: 30 (per request)
- `rate_limit_config`: From config_manager

---

### ModernWebLookupService (modern_web_lookup_service.py)

#### Business Rules

**1. Source Prioritization**
```python
# Juridical context detection:
juridical_keywords = [
    "strafrecht", "bestuursrecht", "civiel", "jurid",
    "wetboek", "artikel", "ecli", "rechtbank",
    "jurisprudentie", "wetgeving"
]

is_juridical = (
    any(k in term.lower() for k in ["wet", "artikel", "recht"])
    OR any(k in context.lower() for k in juridical_keywords)
)

IF is_juridical:
    sources = ["wetgeving", "overheid", "rechtspraak", "overheid_zoek", "wikipedia", "wiktionary"]
ELSE:
    sources = ["wikipedia", "wiktionary", "overheid", "rechtspraak"]
```

**WHY:** Juridical terms need authoritative sources first

**2. Provider Weights (from config)**
```python
{
    "wikipedia": 0.8,
    "wiktionary": 0.9,
    "overheid": 1.0,      # Highest (government sources)
    "rechtspraak": 0.95,
    "wetgeving": 0.9
}
```

**3. Context-Based Query Strategy (Stage Backoff)**
```python
# Classify context tokens:
org_tokens = ["om", "zm", "dji", "justid", "kmar", "cjib", "reclassering"]
jur_keywords = ["recht", "civiel", "bestuursrecht", "strafrecht", "jurid"]
wet_keywords = ["wet", "wetboek", "awb", "sv", "sr", "rv"]

# Stage-based search (Wikipedia/Wiktionary):
stages = [
    ("context_full", org + jur + wet),  # All context
    ("jur_wet", jur + wet),              # Juridical + legal
    ("wet_only", wet),                    # Legal only
    ("no_ctx", [])                        # Term only
]

for stage_name, tokens in stages:
    query = term if not tokens else f"{term} {' '.join(tokens)}"
    result = await provider_lookup(query)
    if result and result.success:
        return result

# Heuristic fallbacks:
IF term.endswith("tekst") and len(term) > 6:
    try_fallback(term[:-5])  # Strip suffix

IF " " in term and "-" not in term:
    try_fallback(term.replace(" ", "-"))  # Add hyphens

IF term.lower() == "vonnistekst":
    try_fallback("vonnis")
    try_fallback("uitspraak")
```

**WHY Stages:** Broader context may reduce recall; fallback to narrower queries

**4. SRU Search Strategy**
```python
# For Rechtspraak: term-only first (context reduces recall)
IF endpoint == "rechtspraak":
    stages = [("no_ctx", [])]
ELSE:
    # For other SRU: wet-only first, then no_ctx
    IF wet_tokens:
        stages = [("wet_only", wet)]
    stages.append(("no_ctx", []))

for stage_name, tokens in stages:
    combo_term = term if not tokens else f"{term} {' '.join(tokens)}"
    results = await sru_service.search(term=combo_term, endpoint=endpoint)
    if results:
        return results[0]

# Post-stage fallbacks:
IF term.endswith("tekst"):
    try_fallback(term[:-5])
IF " " in term:
    try_fallback(term.replace(" ", "-"))
```

**5. Ranking & Deduplication (Epic 3)**
```python
# Convert results to contract dicts
prepared = [_to_contract_dict(r) for r in valid_results]

# Rank with provider weights
ranked = rank_and_dedup(prepared, provider_weights)

# Apply max_results limit
return ranked[:request.max_results]
```

**6. Legal Metadata Extraction (STORY 3.1)**
```python
# In provenance building:
provenance_sources = build_provenance(prepared, extract_legal=True)

# Enriches snippet with article metadata:
IF metadata contains article_number + law_code:
    snippet = f"Artikel {num} {code}: {original_snippet}"
    IF clause:
        snippet = f"Artikel {num} lid {clause} {code}: {original_snippet}"
```

**7. ECLI Boost**
```python
# For rechtspraak provider:
IF "ECLI:" in metadata.dc_identifier OR "ECLI:" in snippet:
    score = min(1.0, score + 0.05)  # 5% boost for ECLI presence
```

#### Decision Logic

**Timeout Handling**
```python
WEB_LOOKUP_TIMEOUT = float(os.getenv("WEB_LOOKUP_TIMEOUT_SECONDS", "10.0"))

result = await asyncio.wait_for(
    provider_lookup(term),
    timeout=WEB_LOOKUP_TIMEOUT
)
```

**Confidence Weighting**
```python
result.source.confidence *= source_config.confidence_weight

# Example: Wikipedia result with base 0.9
# After weighting: 0.9 * 0.8 = 0.72
```

**Debug Tracking**
```python
self._debug_attempts = []  # Reset per lookup

for provider in providers:
    attempt = {
        "provider": provider_name,
        "term": term,
        "api_type": api_type,
        "stage": stage_name,
        "success": bool(result),
        "duration_ms": duration,
        "url": result.url if result else None,
        "confidence": result.confidence if result else 0.0
    }
    self._debug_attempts.append(attempt)

# Available via service._last_debug for orchestrator
```

#### Configuration Parameters

**SourceConfig per provider:**
- `enabled`: True/False (from config)
- `confidence_weight`: Provider-specific weight
- `timeout`: 30s
- `max_retries`: 3

**Lookup Settings:**
- `max_results`: 20 (default, override via env: WEB_LOOKUP_MAX_RESULTS)
- `timeout`: 10s (default, override via env: WEB_LOOKUP_TIMEOUT_SECONDS)
- `include_examples`: False

---

## Validation Services

### ModularValidationService (modular_validation_service.py)

#### Business Rules

**1. Rule Loading Strategy**
```python
IF toetsregel_manager available:
    # Load all JSON rules from manager
    all_rules = manager.get_all_regels()
    _internal_rules = list(all_rules.keys())

    # Calculate weights from rule metadata
    for rule_id, rule_data in all_rules.items():
        IF rule_data.get("weight"):
            weight = float(rule_data["weight"])
        ELSE:
            # Priority-based weights:
            priority_weights = {
                "hoog": 1.0,
                "midden": 0.7,
                "laag": 0.4
            }
            weight = priority_weights.get(rule_data.get("prioriteit", "midden"), 0.4)
        _default_weights[rule_id] = weight

    # Add baseline internal rules (safeguards)
    for rid in ["VAL-EMP-001", "VAL-LEN-001", "VAL-LEN-002", "ESS-CONT-001",
                "CON-CIRC-001", "STR-TERM-001", "STR-ORG-001"]:
        if rid not in _internal_rules:
            _internal_rules.append(rid)
ELSE:
    # Fallback: Use baseline internal rules only
    _internal_rules = ["VAL-EMP-001", "VAL-LEN-001", ...]
    _default_weights = {"VAL-EMP-001": 1.0, ...}
```

**2. Baseline Rules (Always Applied)**
```python
# These rules ALWAYS run (even without ToetsregelManager):
{
    "VAL-EMP-001": {  # Empty check
        "prioriteit": "hoog",
        "aanbeveling": "verplicht",
        "min_chars": 1
    },
    "VAL-LEN-001": {  # Minimum length
        "prioriteit": "midden",
        "aanbeveling": "verplicht",
        "min_words": 5,
        "min_chars": 15
    },
    "VAL-LEN-002": {  # Maximum length
        "prioriteit": "laag",
        "aanbeveling": "aanbevolen",
        "max_words": 80,
        "max_chars": 600
    },
    "ESS-CONT-001": {  # Content check
        "prioriteit": "hoog",
        "aanbeveling": "verplicht",
        "min_words": 6
    },
    "CON-CIRC-001": {  # Circular definition
        "prioriteit": "midden",
        "aanbeveling": "verplicht",
        "circular_definition": True
    },
    "STR-TERM-001": {  # Forbidden phrases
        "prioriteit": "laag",
        "aanbeveling": "aanbevolen",
        "forbidden_phrases": ["HTTP protocol"]
    },
    "STR-ORG-001": {  # Organization check
        "prioriteit": "midden",
        "aanbeveling": "aanbevolen",
        "max_chars": 300,
        "min_commas": 6,
        "redundancy_patterns": [...]
    }
}
```

**3. Pre-Validation Cleaning**
```python
IF cleaning_service available AND has clean_text method:
    result = cleaning_service.clean_text(text)
    # Support both sync and async
    IF has __await__:
        result = await result
    # Support both string and object result
    IF isinstance(result, str):
        cleaned = result
    ELIF has cleaned_text attribute:
        cleaned = result.cleaned_text
ELSE:
    cleaned = text
```

**4. Rule Evaluation**
```python
# Deterministic order: sorted(rule_ids)
for rule_id in sorted(_internal_rules):
    try:
        passed, message = await _evaluate_rule(rule_id, text, context)

        IF passed:
            passed_rules.append(rule_id)
        ELSE:
            violations.append({
                "rule_id": rule_id,
                "message": message,
                "severity": _get_severity(rule_id),
                "category": _extract_category(rule_id)
            })
    except Exception as e:
        # Isolate rule failure
        logger.error(f"Rule {rule_id} evaluation failed: {e}")
        violations.append({
            "rule_id": rule_id,
            "message": f"Evaluation error: {e}",
            "severity": "high",
            "category": "SYSTEM"
        })
```

**WHY Deterministic Order:** Ensures reproducible results for testing

**5. Score Calculation (Aggregation)**
```python
# Category-level scoring
category_scores = {}
for category in ["ARAI", "CON", "ESS", "INT", "SAM", "STR", "VER"]:
    cat_rules = [r for r in passed_rules if r.startswith(category)]
    cat_weights = [weights[r] for r in cat_rules]

    IF cat_weights:
        category_scores[category] = calculate_weighted_score(cat_weights)
    ELSE:
        category_scores[category] = 0.0

# Overall score (weighted average of categories)
overall_score = calculate_weighted_score(category_scores.values())
```

**6. Acceptability Determination**
```python
is_acceptable = determine_acceptability(
    overall_score=overall_score,
    category_scores=category_scores,
    violations=violations,
    overall_threshold=_overall_threshold,  # Default 0.75
    category_threshold=_category_threshold  # Default 0.70
)

# Logic:
is_acceptable = (
    overall_score >= overall_threshold
    AND all(cat_score >= category_threshold for cat_score in category_scores.values())
    AND no_critical_violations(violations)
)
```

#### Decision Logic

**Force Duplicate Override**
```python
# Extract from context metadata:
force_duplicate = False
IF context and isinstance(context, dict):
    force_duplicate = bool(context.get("metadata", {}).get("force_duplicate"))

# Apply during duplicate check:
IF force_duplicate:
    # Skip duplicate violation or downgrade severity
    pass
```

**Correlation ID Generation**
```python
IF context and context.get("correlation_id"):
    correlation_id = context["correlation_id"]
ELSE:
    correlation_id = str(uuid.uuid4())
```

**Result Wrapping**
```python
# Return dict wrapped in ValidationResultWrapper
# Allows both dict-style and attribute-style access
result_dict = {
    "is_acceptable": is_acceptable,
    "violations": violations,
    "passed_rules": passed_rules,
    "detailed_scores": {
        "overall": overall_score,
        "categories": category_scores
    },
    "version": CONTRACT_VERSION,
    "system": {
        "correlation_id": correlation_id,
        "rules_evaluated": len(_internal_rules)
    }
}

return ValidationResultWrapper(result_dict)
```

#### Configuration Parameters

**Thresholds (from config or defaults):**
- `overall_threshold`: 0.75
- `category_threshold`: 0.70

**Rule Weights:**
- Explicit: `rule_data.get("weight")`
- Priority-based: hoog=1.0, midden=0.7, laag=0.4

---

## Data Services

### DefinitionRepository (definition_repository.py)

#### Business Rules

**1. Save Strategy**
```python
IF definition.id exists:
    # Update existing
    updates = _definition_to_updates(definition)
    updated_by = definition.metadata.get("updated_by")
    legacy_repo.update_definitie(definition.id, updates, updated_by)
ELSE:
    # Create new
    record = _definition_to_record(definition)

    # Check force_duplicate flag
    allow_duplicate = bool(definition.metadata.get("force_duplicate"))

    id = legacy_repo.create_definitie(record, allow_duplicate=allow_duplicate)
```

**2. Duplicate Detection Integration**
```python
IF _duplicate_service available:
    # Use new business logic service
    all_definitions = _get_all_definitions()
    matches = _duplicate_service.find_duplicates(definition, all_definitions)
    return [match.definition for match in matches]
ELSE:
    # Fallback to legacy detection
    record = _definition_to_record(definition)
    matches = legacy_repo.find_duplicates(record)
    return [_record_to_definition(m.definitie_record) for m in matches]
```

**3. Soft Delete Strategy**
```python
# delete() performs soft delete:
record = legacy_repo.get_definitie(definition_id)
IF record:
    record.status = DefinitieStatus.ARCHIVED.value
    legacy_repo.update_definitie(definition_id, record)

# hard_delete() performs permanent deletion:
with _get_connection() as conn:
    cur.execute("DELETE FROM definities WHERE id = ?", (definition_id,))
```

**4. Search Logic**
```python
results = legacy_repo.search(search_term=query, limit=limit)

# Convert all records to Definition objects
definitions = [_record_to_definition(r) for r in results if r]
```

**5. Status Filtering**
```python
# get_by_status():
with _get_connection() as conn:
    cursor.execute(
        "SELECT * FROM definities WHERE status = ? ORDER BY updated_at DESC LIMIT ?",
        (status, limit)
    )

    rows = cursor.fetchall()
    return [_record_to_definition(_row_to_record(row)) for row in rows]
```

#### Decision Logic

**Duplicate Service Injection**
```python
# Set by ServiceContainer:
def set_duplicate_service(self, service):
    self._duplicate_service = service

# Repository checks:
IF self._duplicate_service is not None:
    # Use injected service
ELSE:
    # Use legacy implementation
```

**Record Conversion**
```python
# Definition → DefinitieRecord
record = DefinitieRecord(
    begrip=definition.begrip,
    definitie=definition.definitie,
    organisatorische_context=json.dumps(definition.organisatorische_context or []),
    juridische_context=json.dumps(definition.juridische_context or []),
    wettelijke_basis=json.dumps(definition.wettelijke_basis or []),
    ontologische_categorie=definition.ontologische_categorie,
    ufo_categorie=definition.ufo_categorie,
    status=definition.status or DefinitieStatus.DRAFT.value,
    source_type=SourceType.AI.value,
    created_by=definition.created_by,
    metadata=json.dumps(definition.metadata or {})
)

# DefinitieRecord → Definition (reverse)
definition = Definition(
    id=record.id,
    begrip=record.begrip,
    definitie=record.definitie,
    organisatorische_context=json.loads(record.organisatorische_context or "[]"),
    juridische_context=json.loads(record.juridische_context or "[]"),
    wettelijke_basis=json.loads(record.wettelijke_basis or "[]"),
    ontologische_categorie=record.ontologische_categorie,
    ufo_categorie=record.ufo_categorie,
    status=record.status,
    valid=record.valid,
    metadata=json.loads(record.metadata or "{}"),
    created_by=record.created_by,
    created_at=datetime.fromisoformat(record.created_at)
)
```

#### Configuration Parameters

- `db_path`: "data/definities.db" (default)
- `similarity_threshold`: 0.7 (for duplicate service if injected)

---

### DuplicateDetectionService (duplicate_detection_service.py)

#### Business Rules

**1. Exact Match Definition**
```python
# Exact match requires:
1. begrip.lower() == begrip.lower() (case-insensitive)
2. Same organisatorische_context (order-independent)
3. Same juridische_context (order-independent)
4. Same wettelijke_basis (order-independent)

def _is_exact_match(def1, def2):
    IF def1.begrip.lower() != def2.begrip.lower():
        return False

    # Normalize context lists (sorted, lowercased)
    org1 = tuple(sorted([x.lower().strip() for x in (def1.organisatorische_context or [])]))
    org2 = tuple(sorted([x.lower().strip() for x in (def2.organisatorische_context or [])]))

    jur1 = tuple(sorted([x.lower().strip() for x in (def1.juridische_context or [])]))
    jur2 = tuple(sorted([x.lower().strip() for x in (def2.juridische_context or [])]))

    wet1 = tuple(sorted([x.lower().strip() for x in (def1.wettelijke_basis or [])]))
    wet2 = tuple(sorted([x.lower().strip() for x in (def2.wettelijke_basis or [])]))

    return org1 == org2 AND jur1 == jur2 AND wet1 == wet2
```

**2. Fuzzy Match Algorithm (Jaccard Similarity)**
```python
def _calculate_similarity(str1, str2):
    # Normalize tokens with light Dutch stemming
    def normalize(s):
        tokens = []
        for t in re.sub(r"[-/._]", " ", s.lower()).split():
            base = t.strip()
            # Strip common suffixes: elijke → elijk → e
            for suffix in ["elijke", "elijk", "en", "e"]:
                if base.endswith(suffix) and len(base) > len(suffix) + 1:
                    base = base[:-len(suffix)]
                    break
            tokens.append(base)
        return set(tokens)

    set1 = normalize(str1)
    set2 = normalize(str2)

    IF not set1 or not set2:
        return 0.0

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    return intersection / union if union > 0 else 0.0
```

**3. Duplicate Risk Assessment**
```python
def check_duplicate_risk(new_definition, existing_definitions):
    duplicates = find_duplicates(new_definition, existing_definitions)

    IF not duplicates:
        return "none"

    # Check for exact matches
    exact_matches = [d for d in duplicates if d.match_type == "exact"]
    IF exact_matches:
        return "high"

    # Check highest fuzzy score
    highest_score = max(d.score for d in duplicates)
    IF highest_score >= 0.9:
        return "high"
    ELIF highest_score >= 0.75:
        return "medium"
    ELSE:
        return "low"
```

#### Decision Logic

**Archived Definitions Filtering**
```python
for existing in existing_definitions:
    # Skip archived definitions
    status = getattr(existing, "status", None)
    IF not status and getattr(existing, "metadata", None):
        status = existing.metadata.get("status")

    IF status == "archived":
        continue  # Skip this definition
```

**Match Type Classification**
```python
IF _is_exact_match(new, existing):
    match = DuplicateMatch(
        definition=existing,
        score=1.0,
        reason="Exact match: begrip + context",
        match_type="exact"
    )
ELSE:
    score = _calculate_similarity(new.begrip, existing.begrip)
    IF score > threshold:
        match = DuplicateMatch(
            definition=existing,
            score=score,
            reason=f"Similar: {score:.0%} match op begrip",
            match_type="fuzzy"
        )
```

**Result Sorting**
```python
# Sort by score (highest first)
matches = sorted(matches, key=lambda x: x.score, reverse=True)
```

#### Configuration Parameters

- `similarity_threshold`: 0.7 (default, configurable per instance)

---

### CleaningService (cleaning_service.py)

#### Business Rules

**1. GPT Format Detection**
```python
handle_gpt = "ontologische categorie:" in text.lower()

IF handle_gpt:
    # Extract metadata first
    gpt_metadata = analyze_gpt_response(text)

    # Clean with GPT format handling
    cleaned = opschonen_enhanced(text, term, handle_gpt_format=True)

    # Track ontology extraction
    IF gpt_metadata.get("ontologische_categorie"):
        applied_rules.append(f"extracted_ontology_{gpt_metadata['ontologische_categorie']}")
ELSE:
    cleaned = opschonen_enhanced(text, term, handle_gpt_format=False)
```

**2. Change Analysis**
```python
IF original_text != cleaned_text:
    applied_rules.extend(_analyze_changes(original, cleaned, term))
    improvements.extend(_generate_improvements(original, cleaned))
```

**3. Metadata Preservation**
```python
# For clean_definition():
IF config.preserve_original AND result.was_cleaned:
    IF definition.metadata is None:
        definition.metadata = {}

    definition.metadata.update({
        "cleaning_applied": True,
        "original_definitie": result.original_text,
        "cleaning_timestamp": result.metadata.get("timestamp"),
        "cleaning_rules_applied": result.applied_rules
    })
```

**4. Error Handling**
```python
try:
    cleaned = opschonen_enhanced(text, term, handle_gpt_format)
except Exception as e:
    logger.error(f"Cleaning failed: {e}")
    # Return original on error
    return CleaningResult(
        original_text=text,
        cleaned_text=text,
        was_cleaned=False,
        applied_rules=["error_occurred"],
        metadata={"error": str(e)}
    )
```

#### Decision Logic

**Logging Strategy**
```python
IF config.log_operations AND result.was_cleaned:
    logger.info(f"Definition cleaned for '{begrip}': {len(applied_rules)} rules")
    logger.debug(f"Text: '{original[:50]}...' → '{cleaned[:50]}...'")
```

**Validation Config Check**
```python
def validate_cleaning_rules():
    config = laad_verboden_woorden()

    IF not config:
        logger.warning("No cleaning config found")
        return False

    IF isinstance(config, dict):
        verboden = config.get("verboden_woorden", [])
    ELIF isinstance(config, list):
        verboden = config
    ELSE:
        verboden = []

    IF not verboden:
        logger.warning("No forbidden words in config")
        return False

    return True
```

#### Configuration Parameters

**CleaningConfig:**
- `enable_cleaning`: True
- `track_changes`: True
- `preserve_original`: True
- `log_operations`: True

---

### WorkflowService (workflow_service.py)

#### Business Rules

**1. Status Transition Rules**
```python
ALLOWED_TRANSITIONS = {
    "imported": ["review", "draft", "archived"],
    "draft": ["review", "archived"],
    "review": ["established", "draft", "archived"],
    "established": ["archived"],
    "archived": ["draft"]  # Restore possible
}
```

**2. Role-Based Permissions**
```python
ROLE_PERMISSIONS = {
    "approve_to_established": ["reviewer", "admin"],
    "archive": ["admin"],
    "restore_from_archive": ["admin"]
}

# Permission checks:
IF new_status == "established":
    IF user_role not in ROLE_PERMISSIONS["approve_to_established"]:
        return False

IF new_status == "archived":
    IF user_role not in ROLE_PERMISSIONS["archive"]:
        return False

IF current_status == "archived" AND new_status == "draft":
    IF user_role not in ROLE_PERMISSIONS["restore_from_archive"]:
        return False
```

**3. Approval Metadata**
```python
# When transitioning to established:
changes = {
    "status": "established",
    "updated_at": datetime.now(UTC),
    "updated_by": user,
    "approved_by": user,
    "approved_at": datetime.now(UTC),
    "approval_notes": notes or "Goedgekeurd"
}
```

**4. Archive Metadata**
```python
# When transitioning to archived:
changes = {
    "status": "archived",
    "updated_at": datetime.now(UTC),
    "updated_by": user,
    "archived_by": user,
    "archived_at": datetime.now(UTC),
    "archive_reason": notes or "Gearchiveerd"
}
```

#### Decision Logic

**Transition Validation**
```python
def can_change_status(current, new, user_role):
    # Check basic transition rules
    allowed = ALLOWED_TRANSITIONS.get(current, [])
    IF new not in allowed:
        return False

    # Check role-based permissions
    # (see rules above)

    return True
```

**Prepare Status Change**
```python
def prepare_status_change(definition_id, current, new, user, role, notes):
    IF not can_change_status(current, new, role):
        raise ValueError(f"Invalid transition: {current} → {new}")

    changes = {
        "status": new,
        "updated_at": datetime.now(UTC),
        "updated_by": user
    }

    # Add status-specific metadata
    IF new == "established":
        changes.update({...})  # approval metadata
    ELIF new == "archived":
        changes.update({...})  # archive metadata

    return changes
```

---

## Infrastructure Services

### GatePolicyService (approval_gate_policy.py)

#### Business Rules

**1. Policy Loading**
```python
# Priority order:
1. Environment overlay (APPROVAL_GATE_CONFIG_OVERLAY)
2. Base YAML config (config/approval_gate.yaml)
3. DEFAULT_POLICY (hardcoded)

base_data = load_yaml(base_path) or {}
overlay_data = load_yaml(os.getenv("APPROVAL_GATE_CONFIG_OVERLAY")) or {}

policy_data = _deep_merge(DEFAULT_POLICY, base_data)
policy_data = _deep_merge(policy_data, overlay_data)
```

**2. Default Policy**
```python
DEFAULT_POLICY = {
    "hard_requirements": {
        "min_one_context_required": True,
        "forbid_critical_issues": True
    },
    "thresholds": {
        "hard_min_score": 0.75,
        "soft_min_score": 0.65
    },
    "soft_requirements": {
        "allow_high_issues_with_override": True,
        "missing_wettelijke_basis_soft": True,
        "allow_hard_override": False
    },
    "cache": {
        "ttl_seconds": 60
    }
}
```

**3. TTL-Based Caching**
```python
def get_policy():
    IF _cached_policy AND time.time() - _loaded_at < ttl:
        return _cached_policy

    policy = _load_policy()
    _cached_policy = policy
    _loaded_at = time.time()
    return policy
```

**4. Typed Access**
```python
@dataclass
class GatePolicy:
    hard_requirements: dict
    thresholds: dict
    soft_requirements: dict
    cache: dict

    @property
    def hard_min_score(self) -> float:
        return float(self.thresholds.get("hard_min_score", 0.75))

    @property
    def soft_min_score(self) -> float:
        return float(self.thresholds.get("soft_min_score", 0.65))

    @property
    def ttl_seconds(self) -> int:
        return int(self.cache.get("ttl_seconds", 60))
```

#### Decision Logic

**Deep Merge Strategy**
```python
def _deep_merge(base, overlay):
    # Overlay wins at all levels
    for key in overlay.keys():
        IF key in base AND isinstance(base[key], dict) AND isinstance(overlay[key], dict):
            base[key] = _deep_merge(base[key], overlay[key])
        ELSE:
            base[key] = overlay[key]
    return base
```

**Error Handling**
```python
# Config loading:
try:
    IF os.path.exists(base_path):
        with open(base_path) as f:
            base_data = yaml.safe_load(f) or {}
    ELSE:
        logger.warning("Config not found, using defaults")
        base_data = {}
except Exception as e:
    logger.warning(f"Invalid config: {e}, using defaults")
    base_data = {}
```

#### Configuration Parameters

**Thresholds:**
- `hard_min_score`: 0.75 (minimum for approval)
- `soft_min_score`: 0.65 (warning threshold)

**Requirements:**
- `min_one_context_required`: True
- `forbid_critical_issues`: True
- `allow_high_issues_with_override`: True
- `missing_wettelijke_basis_soft`: True
- `allow_hard_override`: False

**Cache:**
- `ttl_seconds`: 60

---

## Cross-Cutting Concerns

### Error Handling Patterns

**1. Graceful Degradation**
```
Web Lookup fails → Continue without external context
Voorbeelden fails → Continue with empty voorbeelden
Enhancement fails → Use original text
Cleaning fails → Use original text
```

**2. Error Isolation**
```
Individual rule fails → Log error, add system violation
Individual service fails → Log error, use fallback
Batch item fails → Continue with other items
```

**3. Exception Wrapping**
```
OpenAI errors → AIServiceError, AITimeoutError, AIRateLimitError
Database errors → Log and return None/False
Validation errors → ValidationResult with error field
```

### State Management

**1. Stateless Services**
```
All services are stateless (except caches)
State passed explicitly via parameters
No session state access in services
Container manages singleton instances
```

**2. Correlation IDs**
```
Generation request → generation_id (UUID)
Validation → correlation_id (UUID from context or generated)
Tracks request across service boundaries
```

**3. Metadata Propagation**
```
Request metadata → Generation metadata → Definition metadata
Includes: timestamps, actors, flags, provenance
Enables audit trail and debugging
```

### Caching Strategies

**1. Service-Level Caching**
```
AIServiceV2: Cache by (model, temp, tokens, prompt hash)
PromptServiceV2: No cache (builds fresh each time)
ToetsregelManager: Cached rules (100x performance gain)
GatePolicyService: TTL-based policy cache (60s default)
```

**2. Cache Keys**
```
AI: f"{model}:{temp}:{tokens}:{hash(prompt)}:{hash(system)}"
Repository: No cache (database is source of truth)
```

**3. Cache Invalidation**
```
TTL-based: Expire after configured time
Manual: Clear via container.reset()
No cache: Always fresh data
```

### Logging & Monitoring

**1. Structured Logging**
```python
logger.info(f"Generation {gen_id}: Phase N complete, status={status}")
logger.warning(f"Service failed: {service_name}, using fallback")
logger.error(f"Critical error in {phase}: {error}", exc_info=True)
```

**2. Audit Trail (ASTRA Compliance)**
```python
# Correlation IDs for tracking
logger.info(f"[AUDIT] correlation_id={id} | action={action} | actor={actor}")

# No PII in logs
logger.info(f"Definition saved: id={id}, status={status}")  # ✓
logger.info(f"Definition saved: text={text}")  # ✗ (may contain PII)
```

**3. Performance Metrics**
```python
start_time = time.time()
# ... operation ...
duration = time.time() - start_time
logger.info(f"Operation completed in {duration:.2f}s")

IF monitoring:
    await monitoring.track_metric(operation, duration, success)
```

### Configuration Management

**1. Configuration Priority**
```
1. Runtime parameter (function arg)
2. Environment variable
3. Config file (YAML/JSON)
4. Central config_manager
5. Hard-coded default
```

**2. Feature Flags**
```python
# Environment-based:
CONTEXT_V2_ENABLED = os.getenv("CONTEXT_V2_ENABLED", "false") == "true"
USE_CONTEXT_MANAGER = os.getenv("USE_CONTEXT_MANAGER", "true") == "true"
DOCUMENT_SNIPPETS_ENABLED = os.getenv("DOCUMENT_SNIPPETS_ENABLED", "true") == "true"

# Config-based:
config.enable_feedback_loop
config.enable_enhancement
config.enable_caching
```

**3. Configuration Files**
```
config/approval_gate.yaml → Gate policy
config/validation_rules.yaml → Validation config
config/web_lookup_defaults.yaml → Web lookup config
config/verboden_woorden.py → Cleaning rules
```

---

## Key Business Constraints

### Data Integrity

**1. Database Constraints**
- Unique (begrip, organisatorische_context, juridische_context, wettelijke_basis) unless force_duplicate=True
- Status transitions follow workflow rules
- Soft delete (archive) preserves data

**2. Validation Constraints**
- Minimum thresholds: overall=0.75, category=0.70
- Baseline rules always enforced
- Schema compliance guaranteed

**3. Context Constraints**
- At least one context field recommended (gate policy)
- Context fields are lists (not strings)
- Empty lists allowed

### Performance Constraints

**1. Timeouts**
```
AI generation: 30s default
Web lookup: 10s default (configurable)
Individual provider: Respect overall timeout budget
```

**2. Rate Limits**
```
OpenAI: 60 req/min, 3000 req/hour
Max concurrent: 10
Backoff factor: 1.5x
Max retries: 3
```

**3. Token Limits**
```
Prompt max: 10,000 tokens (hard limit)
Response max: 500 tokens (configurable)
Web snippet: 100 tokens (configurable)
```

### Security Constraints

**1. PII Handling**
```
IF security_service available:
    Sanitize request before processing
Log only non-PII fields
Audit trail without sensitive data
```

**2. API Key Management**
```
NEVER hardcode keys
Use environment variables
Fallback: OPENAI_API_KEY → OPENAI_API_KEY_PROD
```

**3. Input Validation**
```
Sanitize web content before prompt injection
Validate all user inputs
Escape special characters in queries
```

---

## Business Logic Extraction Summary

### Critical Business Rules by Domain

**Definition Generation:**
1. 11-phase orchestration flow (security → feedback → web → prompt → AI → voorbeelden → clean → validate → enhance → save → feedback → monitor)
2. Web lookup failure never blocks generation (graceful degradation)
3. Documents have highest priority in provenance
4. Ontological category drives template selection
5. Force duplicate flag overrides duplicate prevention

**Validation:**
1. Baseline rules always enforced (7 core rules)
2. Deterministic rule order (sorted by ID)
3. Category-level + overall scoring
4. Schema compliance guaranteed
5. Error isolation per rule

**Web Lookup:**
1. Juridical context → prioritize authoritative sources
2. Stage-based backoff (full context → juridical → legal → term-only)
3. Provider weighting (overheid=1.0, rechtspraak=0.95, wiktionary=0.9, wetgeving=0.9, wikipedia=0.8)
4. ECLI boost for rechtspraak (+5%)
5. Legal metadata extraction for juridical sources

**Duplicate Detection:**
1. Exact match: begrip + all 3 context lists (order-independent)
2. Fuzzy match: Jaccard similarity with Dutch stemming
3. Threshold: 0.7 default
4. Risk levels: exact/0.9+ = high, 0.75-0.9 = medium, <0.75 = low

**Workflow:**
1. Status transitions follow state machine
2. Role-based permissions (reviewer, admin)
3. Approval requires metadata (approved_by, approved_at)
4. Soft delete preserves data

**Data Storage:**
1. Always save definition (regardless of validation)
2. Force duplicate flag in metadata bypasses duplicate check
3. Metadata preserves full audit trail
4. JSON serialization for context lists

### Dependencies & Integration Points

**External Dependencies:**
```
OpenAI API → AI generation
Wikipedia API → General definitions
Wiktionary API → Word definitions
SRU (overheid.nl) → Government sources
Rechtspraak.nl → Legal jurisprudence
```

**Internal Dependencies:**
```
ServiceContainer → All services
DefinitionOrchestratorV2 → Prompt, AI, Validation, Cleaning, Repository
ValidationOrchestratorV2 → ValidationService, CleaningService
PromptServiceV2 → ContextManager, PromptBuilder
ModernWebLookupService → Provider services, Ranking, Provenance
```

**Configuration Dependencies:**
```
config_manager → Default model, temperature, rate limits
approval_gate.yaml → Gate policy thresholds
validation_rules.yaml → Validation config
web_lookup_defaults.yaml → Web lookup config
verboden_woorden.py → Cleaning rules
```

### Business Logic Hotspots

**High Complexity:**
1. DefinitionOrchestratorV2.create_definition() - 11 phases, 800+ lines
2. ModernWebLookupService.lookup() - Multi-provider coordination
3. ModularValidationService.validate_definition() - 45+ rules
4. PromptServiceV2._maybe_augment_with_web_context() - Complex injection logic

**High Business Value:**
1. Duplicate detection algorithm - Prevents data pollution
2. Validation scoring - Ensures quality
3. Web lookup ranking - Improves accuracy
4. Workflow permissions - Enforces governance

**High Change Frequency:**
1. Prompt augmentation logic - Evolving with Epic 3
2. Validation rules - Business requirements change
3. Gate policy thresholds - Tuned based on metrics
4. Provider weights - Adjusted for quality

---

## Recommendations for Rebuild

### 1. Preserve Business Logic
- **Extract all decision tables** (status transitions, provider weights, thresholds)
- **Document all business rules** before code changes
- **Maintain test coverage** for critical logic (duplicate detection, validation scoring)

### 2. Simplify Complexity
- **Break down DefinitionOrchestratorV2** into phase-specific services
- **Extract configuration** into dedicated config objects
- **Reduce conditional complexity** in web lookup (too many nested ifs)

### 3. Improve Testability
- **Make all timeouts configurable** (currently some hardcoded)
- **Inject all external dependencies** (no global state)
- **Use interfaces everywhere** (easier mocking)

### 4. Enhance Observability
- **Add distributed tracing** (correlation IDs exist, use them!)
- **Structured logging** (JSON format for parsing)
- **Business metrics** (track duplicate rates, validation pass rates, web lookup success)

### 5. Strengthen Error Handling
- **Consistent error types** across services
- **Circuit breakers** for external calls
- **Retry policies** as configuration (not hardcoded)

---

**END OF SERVICES BUSINESS LOGIC EXTRACTION**
