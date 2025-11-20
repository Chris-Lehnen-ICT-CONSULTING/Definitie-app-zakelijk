# DEF-156: Context Flow Diagram & Quick Reference

## Current 3-Layer Context Flow (PROBLEM)

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: HybridContextManager (definition_generator_context.py) │
│ ─────────────────────────────────────────────────────────────── │
│ INPUT:  GenerationRequest                                       │
│         - organisatorische_context: list[str]                   │
│         - juridische_context: list[str]                         │
│         - wettelijke_basis: list[str]                           │
│                                                                 │
│ PROCESS: _build_base_context() → Lines 199-253                 │
│          Maps to SHORTENED names:                               │
│          - "organisatorisch" ← organisatorische_context        │
│          - "juridisch"       ← juridische_context              │
│          - "wettelijk"       ← wettelijke_basis                │
│                                                                 │
│ OUTPUT: EnrichedContext                                         │
│         base_context = {                                        │
│           "organisatorisch": [...],  ← RENAMED!                │
│           "juridisch": [...],        ← RENAMED!                │
│           "wettelijk": [...],        ← RENAMED!                │
│         }                                                       │
│         sources = [...]                                         │
│         metadata = {10+ keys}                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: PromptServiceV2 (prompt_service_v2.py)                │
│ ─────────────────────────────────────────────────────────────── │
│ INPUT:  EnrichedContext from Layer 1                            │
│                                                                 │
│ PROCESS: build_generation_prompt() → Lines 84-194              │
│          1. Merges extra context into metadata (lines 104-112) │
│             enriched_context.metadata["web_lookup"] = ...      │
│          2. Augments with web context (lines 414-541)          │
│             _maybe_augment_with_web_context()                  │
│          3. Augments with document snippets (lines 196-254)    │
│             _maybe_augment_with_document_snippets()            │
│                                                                 │
│ SIDE EFFECT: DEPRECATED method still present (lines 256-401)   │
│              Creates DUPLICATE storage:                         │
│              base_context = {                                   │
│                "organisatorisch": [],                          │
│                "juridisch": [],                                │
│                "wettelijk": [],                                │
│                "organisatorische_context": [],  ← DUPLICATE!   │
│                "juridische_context": [],        ← DUPLICATE!   │
│                "wettelijke_basis": []           ← DUPLICATE!   │
│              }                                                  │
│                                                                 │
│ OUTPUT: EnrichedContext (modified)                              │
│         + metadata bloat (web_lookup, documents, etc.)         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: ContextAwarenessModule (context_awareness_module.py)  │
│ ─────────────────────────────────────────────────────────────── │
│ INPUT:  EnrichedContext from Layer 2                            │
│                                                                 │
│ PROCESS: execute() → Lines 75-132                              │
│          1. Calculate context richness score                    │
│             _calculate_context_score() → 0.0-1.0              │
│          2. Choose formatting strategy:                         │
│             - Rich (≥0.8): Detailed with confidence indicators │
│             - Moderate (0.5-0.8): Standard formatting          │
│             - Minimal (<0.5): Compact text                     │
│          3. Share traditional context (lines 368-393)          │
│             Maps to THIRD naming scheme:                       │
│             context.set_shared("organization_contexts", ...)   │
│             context.set_shared("juridical_contexts", ...)      │
│             context.set_shared("legal_basis_contexts", ...)    │
│                                                                 │
│ OUTPUT: Formatted prompt section as string                      │
│         + shared_state with DIFFERENT field names              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Field Name Mapping Across Layers

| Source Field (Request) | Layer 1 (EnrichedContext) | Layer 2 (Metadata) | Layer 3 (shared_state) |
|------------------------|---------------------------|-------------------|------------------------|
| `organisatorische_context` | `organisatorisch` | `organisatorische_context` | `organization_contexts` |
| `juridische_context` | `juridisch` | `juridische_context` | `juridical_contexts` |
| `wettelijke_basis` | `wettelijk` | `wettelijke_basis` | `legal_basis_contexts` |
| `ontologische_categorie` | N/A | `ontologische_categorie` | N/A |
| N/A | N/A | `semantic_category` | N/A |

**Problem:** Same data has 3-4 different names depending on which layer you're in!

---

## Data Duplication Points

```
Request Fields (INPUT)
    ↓
┌───────────────────────────────────┐
│ EnrichedContext.base_context      │  ← Storage 1
│   organisatorisch: [...]          │
│   juridisch: [...]                │
│   wettelijk: [...]                │
└───────────────────────────────────┘
    ↓ (copied to)
┌───────────────────────────────────┐
│ EnrichedContext.metadata          │  ← Storage 2 (DUPLICATE)
│   web_lookup: {...}               │
│   documents: {...}                │
│   ontologische_categorie: "..."   │
│   [+ 7 more fields]               │
└───────────────────────────────────┘
    ↓ (extracted to)
┌───────────────────────────────────┐
│ ModuleContext.shared_state        │  ← Storage 3 (DUPLICATE)
│   organization_contexts: [...]    │
│   juridical_contexts: [...]       │
│   legal_basis_contexts: [...]     │
│   context_richness_score: 0.85    │
└───────────────────────────────────┘
    ↓ (DEPRECATED path also creates)
┌───────────────────────────────────┐
│ DEPRECATED base_context           │  ← Storage 4 (ZOMBIE)
│   organisatorisch: []             │
│   juridisch: []                   │
│   wettelijk: []                   │
│   organisatorische_context: []    │
│   juridische_context: []          │
│   wettelijke_basis: []            │
└───────────────────────────────────┘
```

**Result:** Same context data stored 3-4 times in memory!

---

## Proposed 2-Layer Consolidation (SOLUTION)

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: EnrichedContextBuilder (NEW - consolidated)           │
│ ─────────────────────────────────────────────────────────────── │
│ INPUT:  GenerationRequest                                       │
│                                                                 │
│ RESPONSIBILITIES:                                               │
│  1. Build base context (from HybridContextManager)             │
│  2. Augment with web lookup (from PromptServiceV2)             │
│  3. Augment with document snippets (from PromptServiceV2)      │
│                                                                 │
│ CANONICAL FIELD NAMES (everywhere):                            │
│  - organisatorische_context                                    │
│  - juridische_context                                          │
│  - wettelijke_basis                                            │
│                                                                 │
│ OUTPUT: EnrichedContext (single source of truth)                │
│         base_context = {                                        │
│           "organisatorische_context": [...],                   │
│           "juridische_context": [...],                         │
│           "wettelijke_basis": [...],                           │
│         }                                                       │
│         sources = [ContextSource, ...]                          │
│         metadata = {                                            │
│           "ontologische_categorie": "...",                     │
│           "context_richness_score": 0.85,                      │
│           # Only 3-4 essential keys                            │
│         }                                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: ContextFormatterModule (simplified)                   │
│ ─────────────────────────────────────────────────────────────── │
│ INPUT:  EnrichedContext (immutable)                             │
│                                                                 │
│ RESPONSIBILITIES:                                               │
│  1. Read context_richness_score from metadata                  │
│  2. Choose formatting strategy (rich/moderate/minimal)          │
│  3. Format as string                                            │
│  4. Return formatted section                                    │
│                                                                 │
│ NO STATE SHARING: Pure formatter, no shared_state writes       │
│                                                                 │
│ OUTPUT: Formatted prompt section (string only)                  │
└─────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- ✅ Single source of truth
- ✅ Consistent field names
- ✅ No duplication
- ✅ Clear boundaries
- ✅ Easy to test

---

## Rule Module Duplication Quick Reference

### Current Implementation (640 lines, 5 files)

```python
# arai_rules_module.py (128 lines)
class AraiRulesModule(BasePromptModule):
    def __init__(self):
        super().__init__(module_id="arai_rules", module_name="ARAI...", priority=75)
    def execute(self, context):
        sections = ["### ✅ Algemene Regels AI (ARAI):"]
        rules = {k: v for k, v in all_rules.items() if k.startswith("ARAI")}
        # ... formatting logic

# con_rules_module.py (128 lines)
class ConRulesModule(BasePromptModule):
    def __init__(self):
        super().__init__(module_id="con_rules", module_name="Context...", priority=70)
    def execute(self, context):
        sections = ["### 🌐 Context Regels (CON):"]
        rules = {k: v for k, v in all_rules.items() if k.startswith("CON-")}
        # ... IDENTICAL formatting logic

# + 3 more identical files (ess, sam, ver)
```

### Proposed Implementation (80 lines, 1 file)

```python
# json_based_rules_module.py (60 lines)
class JSONBasedRulesModule(BasePromptModule):
    """Generic JSON-based validation rules loader."""

    def __init__(self, category_id: str, category_name: str,
                 emoji: str, priority: int, filter_prefix: str):
        super().__init__(
            module_id=f"{category_id}_rules",
            module_name=f"{category_name} Validation Rules",
            priority=priority
        )
        self.emoji = emoji
        self.filter_prefix = filter_prefix
        self.include_examples = True

    def execute(self, context: ModuleContext) -> ModuleOutput:
        sections = [f"### {self.emoji} {self.category_name}:"]
        manager = get_cached_toetsregel_manager()
        rules = {k: v for k, v in manager.get_all_regels().items()
                 if k.startswith(self.filter_prefix)}
        for key, data in sorted(rules.items()):
            sections.extend(self._format_rule(key, data))
        return ModuleOutput(content="\n".join(sections), metadata={...})

    def _format_rule(self, key, data):
        # Shared formatting logic (30 lines)
        ...

# rule_module_factory.py (20 lines)
def create_rule_modules() -> list[BasePromptModule]:
    """Factory to create all rule modules from config."""
    configs = [
        ("arai", "Algemene Regels AI", "✅", 75, "ARAI"),
        ("con", "Context", "🌐", 70, "CON-"),
        ("ess", "Essentie", "🎯", 75, "ESS-"),
        ("sam", "Samenhang", "🔗", 65, "SAM-"),
        ("ver", "Vorm", "📐", 60, "VER-"),
    ]
    return [JSONBasedRulesModule(*cfg) for cfg in configs]
```

**Reduction:** 640 lines → 80 lines (88% reduction)

---

## Memory Layout Comparison

### Current (Per Request)

```
GenerationRequest: 2KB
  ↓
EnrichedContext.base_context: 2KB (copy 1)
EnrichedContext.metadata: 3KB (includes duplicates)
EnrichedContext.sources: 5KB
  ↓
ModuleContext.shared_state: 1.5KB (copy 2 - extracted data)
  ↓
DEPRECATED base_context: 2KB (copy 3 - zombie)

Total: ~15.5KB per request
Duplication: ~5.5KB (35% waste)
```

### Proposed (Per Request)

```
GenerationRequest: 2KB
  ↓
EnrichedContext.base_context: 2KB (single copy)
EnrichedContext.metadata: 1KB (lean, essential only)
EnrichedContext.sources: 5KB

Total: ~10KB per request
Duplication: 0KB (0% waste)

Savings: 35% memory reduction
```

---

## Testing Strategy

### Priority 1: Rule Module Consolidation

**Test Plan:**
1. ✅ **Output Comparison:** Old vs New modules produce identical output
2. ✅ **Unit Tests:** Each category config tested independently
3. ✅ **Integration Test:** All modules registered and executed
4. ✅ **Performance Test:** Verify no regression in load time

**Rollback Safety:** HIGH
- Keep old files as `.backup` until validated
- Can switch back by changing orchestrator registration

### Priority 2: Context Consolidation

**Test Plan:**
1. ⚠️ **Integration Tests FIRST:** Capture current behavior
2. ⚠️ **Parallel Run:** Old + New path, compare outputs
3. ⚠️ **Canary Deployment:** 10% traffic to new path
4. ⚠️ **Monitoring:** Track field access patterns

**Rollback Safety:** MEDIUM
- Requires feature flag for dual-path
- More complex migration

---

## Implementation Checklist

### Phase 1: Quick Wins (Week 1)
- [ ] Create `JSONBasedRulesModule` base class
- [ ] Migrate ARAI module (test thoroughly)
- [ ] Migrate CON module
- [ ] Migrate ESS module
- [ ] Migrate SAM module
- [ ] Migrate VER module
- [ ] Delete old module files
- [ ] Update orchestrator registration
- [ ] Verify token reduction (target: -2,800 tokens)

### Phase 2: Context Cleanup (Week 2-3)
- [ ] Design `EnrichedContextBuilder` API
- [ ] Write integration tests for current behavior
- [ ] Implement builder with augmentation
- [ ] Standardize field names across codebase
- [ ] Remove `_DEPRECATED_convert_request_to_context()`
- [ ] Simplify `ContextAwarenessModule` to pure formatter
- [ ] Update all metadata access points
- [ ] Remove shared_state extractions

### Phase 3: Validation (Week 3-4)
- [ ] Run full test suite
- [ ] Performance benchmarks
- [ ] Memory profiling
- [ ] Token count verification
- [ ] Code review
- [ ] Documentation updates

---

## Success Metrics

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| Total Lines (prompts/) | 5,383 | 2,700 | `find src/services/prompts -name "*.py" -exec wc -l {} + \| tail -1` |
| Duplicate Lines | 640 | 0 | Manual audit |
| Token Count | 7,250 | 4,000 | Prompt generation test |
| Memory/Request | 15.5KB | 10KB | Memory profiler |
| Context Layers | 3 | 2 | Architecture review |
| Field Name Variants | 4 | 1 | Code search |
| Deprecated Methods | 1 (145 lines) | 0 | Grep search |

**Target Date:** End of Sprint 2 (2 weeks)
