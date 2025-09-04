---
canonical: false
status: active
owner: development
last_verified: 2025-09-03
applies_to: definitie-app@v2.3
document_type: epic
epic: epic-7-performance-scaling
priority: critical
sprint: UAT-2025-09
---

# Epic 7: Performance & Scaling - Extended User Stories

**Epic Goal**: Optimaliseer performance door prompt reductie, context flow fixes, en service caching
**UAT Deadline**: 20 september 2025
**Totale Effort**: 8-10 dagen (inclusief bestaande stories)
**Business Value**: 80% snellere responses, €1,000+/maand API kosten besparing

---

## 📊 Epic 7 Complete Overview

Dit epic bevat ALLE performance optimalisaties inclusief:
- Prompt token reductie (7,250 → 1,250 tokens)
- Context flow fixes (alle 3 velden)
- Toetsregel → Prompt mapping
- Ontologie instructie fixes
- Service caching optimalisaties

---

## 🎯 User Stories Overview

### Bestaande Stories (uit requirements)
| ID | Story | Status | Notes |
|----|-------|--------|-------|
| PER-001 | <5 sec response | ❌ Niet Gestart | Nu 8-12 sec |
| PER-002 | Caching | 🔄 In Progress | Basic in-memory |
| PER-003 | Horizontal scaling | ❌ Niet Gestart | Post-UAT |
| PER-004 | Async processing | 🔄 In Progress | Celery planned |
| PER-005 | Database optimization | ✅ Compleet | SQLite optimized |

### Nieuwe Stories (Prompt & Context Optimalisatie)
| ID | Story | Priority | Points | Impact |
|----|-------|----------|---------|---------|
| PER-006 | Prompt Token Reductie | P1 | 3 | -83% tokens |
| PER-007 | Context Flow Fix | P1 | 2 | 3 velden werkend |
| PER-008 | Toetsregel-Prompt Mapping | P1 | 5 | Per-regel beheer |
| PER-009 | Ontologie als Instructie | P1 | 3 | Kwaliteit++ |
| PER-010 | Service Container Caching | P1 | 1 | 6x → 1x init |

---

## 📝 Detailed User Stories

### Story PER-006: Prompt Token Reductie (Was PROMPT-4.1 t/m 4.3)
**Als** systeem
**Wil ik** minimale prompt tokens gebruiken
**Zodat** responses sneller en goedkoper zijn

**Acceptance Criteria:**
- [ ] Consolideer 42 "Start niet met" regels → 5 categorieën
- [ ] Fix 5+ tegenstrijdigheden in prompt
- [ ] Context-aware prompt compositie
- [ ] Van 7,250 → 1,250 tokens (83% reductie)
- [ ] Kwaliteit behouden >80%

**Implementation Details:**
```python
# Consolidatie van duplicate regels
FORBIDDEN_STARTS = {
    "articles": ["de", "het", "een"],
    "verbs": ["is", "zijn", "wordt"],
    "constructs": ["proces waarbij", "type van"]
}

# Context-aware compositie
def compose_prompt(context: DefinitionContext) -> str:
    base = load_base_instructions()  # 500 tokens
    rules = filter_rules_by_context(context)  # 400 tokens
    examples = select_examples(context, max=2)  # 350 tokens
    return optimize(base + rules + examples)
```

**Effort**: 3 points (1.5 dag)
**Priority**: P1 - UAT Blocker

---

### Story PER-007: Complete Context Flow Fix ⚠️
**Als** gebruiker
**Wil ik** dat alle 3 contextvelden gebruikt worden
**Zodat** definities volledig context-aware zijn

**Current Problem:**
```python
# src/generation/definition_generator_context.py:237-258
def _build_base_context(self):
    return {
        "term": self.term,
        "context": self.organisatorische_context,  # ALLEEN DEZE!
        # juridische_context wordt GENEGEERD
        # wettelijke_basis wordt GENEGEERD
    }
```

**Required Fix:**
```python
def _build_base_context(self):
    return {
        "term": self.term,
        "organisatorische_context": self.organisatorische_context,
        "juridische_context": self.juridische_context,  # ADD
        "wettelijke_basis": self.wettelijke_basis,      # ADD
        "context": self._combine_contexts()  # Backward compatible
    }

def _combine_contexts(self) -> str:
    """Combineer alle contexten voor prompt"""
    contexts = []
    if self.organisatorische_context:
        contexts.append(f"Org: {self.organisatorische_context}")
    if self.juridische_context:
        contexts.append(f"Juridisch: {self.juridische_context}")
    if self.wettelijke_basis:
        contexts.append(f"Wettelijk: {self.wettelijke_basis}")
    return " | ".join(contexts) if contexts else ""
```

**Test Case:**
```python
def test_all_contexts_in_prompt():
    result = generate_definition(
        term="arrestatie",
        org_context="OM",
        juridische_context="Strafrecht",
        wettelijke_basis="Art. 141 Sr"
    )
    assert "OM" in result.prompt_used
    assert "Strafrecht" in result.prompt_used
    assert "Art. 141 Sr" in result.prompt_used
```

**Effort**: 2 points (1 dag)
**Priority**: P1 - CRITICAL FIX

---

### Story PER-008: Toetsregel → Prompt Mapping Service
**Als** ontwikkelaar
**Wil ik** per toetsregel een prompt instructie beheren
**Zodat** regels individueel geoptimaliseerd kunnen worden

**Requirements:**
- 45 YAML/JSON bestanden voor individuele regel instructies
- Context-aware variaties (default/juridisch/DJI)
- Centraal beheer en versionering
- Token budget per regel

**Directory Structure:**
```
config/prompt-instructions/
├── arai/
│   ├── ARAI-01.yaml
│   ├── ARAI-02.yaml
│   └── ...
├── con/
│   ├── CON-01.yaml
│   └── ...
└── defaults.yaml
```

**YAML Format Example:**
```yaml
# config/prompt-instructions/arai/ARAI-01.yaml
rule_id: ARAI-01
name: "Geen werkwoord als kern"
priority: CRITICAL
token_budget: 50
contexts:
  default:
    instruction: "Start NOOIT met een werkwoord. Begin met zelfstandig naamwoord."
    examples:
      good: "registratie van gegevens"
      bad: "registreren van gegevens"
  juridisch:
    instruction: "Juridische begrippen starten met substantief, geen infinitief."
    examples:
      good: "vervolging door het OM"
      bad: "vervolgen door het OM"
  dji:
    instruction: "Detentie-begrippen altijd als naamwoord formuleren."
    examples:
      good: "plaatsing in isolatie"
      bad: "plaatsen in isolatie"
```

**Service Implementation:**
```python
class RulePromptMappingService:
    """Maps validation rules to context-aware prompt instructions"""

    def __init__(self):
        self.instructions = self._load_all_instructions()
        self._cache = {}

    @st.cache_data(ttl=3600)
    def get_instructions_for_context(
        self,
        context: Dict[str, str],
        token_budget: int = 1000
    ) -> List[str]:
        """Get all relevant rule instructions within token budget"""

        cache_key = self._get_cache_key(context)
        if cache_key in self._cache:
            return self._cache[cache_key]

        instructions = []
        remaining_budget = token_budget

        # Priority order: CRITICAL → HIGH → MEDIUM → LOW
        for rule in self._get_priority_sorted_rules():
            instruction = self._select_context_variant(rule, context)
            tokens = count_tokens(instruction)

            if remaining_budget >= tokens:
                instructions.append(instruction)
                remaining_budget -= tokens
            else:
                log.debug(f"Skipping {rule.id}: budget exceeded")

        self._cache[cache_key] = instructions
        return instructions
```

**Effort**: 5 points (2.5 dagen)
**Priority**: P1 - Structurele verbetering

---

### Story PER-009: Ontologie als Instructie
**Als** AI model
**Wil ik** ontologie als instructie ontvangen
**Zodat** ik het juiste type definitie genereer

**Current Problem:**
```python
# FOUT: Ontologie als vraag
prompt = f"Wat is de ontologische categorie van {term}?"
```

**Required Fix:**
```python
class OntologyInstructionService:
    """Converts ontology category to prompt instruction"""

    TEMPLATES = {
        "object": """
        INSTRUCTIE: Definieer als OBJECT (concrete/abstracte entiteit)
        - Focus op WAT het is
        - Beschrijf identificerende kenmerken
        """,
        "proces": """
        INSTRUCTIE: Definieer als PROCES (handeling/activiteit)
        - Focus op WAT er gebeurt
        - Beschrijf begin- en eindtoestand
        """,
        "actor": """
        INSTRUCTIE: Definieer als ACTOR (persoon/instantie)
        - Focus op WIE/WELKE instantie
        - Beschrijf rol en verantwoordelijkheden
        """,
        "toestand": """
        INSTRUCTIE: Definieer als TOESTAND (status/conditie)
        - Focus op de situatie
        - Beschrijf voorwaarden
        """
    }

    def get_instruction(self, term: str, context: Dict) -> str:
        category = self._determine_category(term, context)
        return self.TEMPLATES[category]
```

**Integration:**
```python
def build_prompt(term: str, context: Dict):
    parts = []

    # 1. Ontologie instructie EERST
    parts.append(ontology_service.get_instruction(term, context))

    # 2. Context instructies
    parts.append(build_context_instruction(context))

    # 3. Toetsregel instructies
    parts.extend(rule_service.get_instructions_for_context(context))

    # 4. De vraag
    parts.append(f"\nGenereer definitie voor: {term}")

    return "\n".join(parts)
```

**Effort**: 3 points (1.5 dag)
**Priority**: P1 - Kwaliteitsverbetering

---

### Story PER-010: Service Container Caching
**Als** systeem
**Wil ik** services één keer initialiseren
**Zodat** startup tijd minimaal is

**Current Problem:**
- ServiceContainer wordt 6x geïnitialiseerd
- 20 seconden startup tijd
- Memory overhead

**Required Fix:**
```python
# src/services/container.py
@st.cache_resource
def get_service_container() -> ServiceContainer:
    """Get or create singleton service container"""
    return ServiceContainer()

# src/services/validation/modular_validation_service.py
@st.cache_data(ttl=3600)
def load_validation_rules() -> Dict[str, Rule]:
    """Load and cache all validation rules"""
    return load_all_rules_from_config()
```

**Effort**: 1 point (0.5 dag)
**Priority**: P1 - Quick Win

---

## 📅 Implementation Planning voor UAT

### Week 1 (4-6 Sep): Critical Fixes & Quick Wins
```
Dag 1 (4 Sep):
├── PER-010: Service caching (2 uur) ⚡
├── PER-007: Context flow fix (6 uur) 🔴
└── Result: 3 contexts working + 50% faster startup

Dag 2-3 (5-6 Sep):
├── PER-006: Prompt token reductie
│   ├── Consolidate duplicates
│   ├── Fix contradictions
│   └── Context-aware composition
└── Result: 7,250 → 1,250 tokens
```

### Week 2 (9-13 Sep): Structural Improvements
```
Dag 4-5 (9-10 Sep):
├── PER-008: Rule-Prompt Mapping
│   ├── Create 45 YAML configs
│   ├── Build service
│   └── Integration
└── Result: Per-rule prompt management

Dag 6 (11 Sep):
├── PER-009: Ontologie instructies
└── Result: Quality improvement
```

### Week 3 (16-20 Sep): Testing & Polish
```
Integration testing
Performance verification
UAT preparation
```

---

## ✅ Definition of Done for Epic 7

- [ ] Response tijd < 5 seconden (van 8-12s)
- [ ] Prompt tokens < 1,500 (van 7,250)
- [ ] Alle 3 contextvelden werkend
- [ ] 45 regel-specifieke instructies
- [ ] Ontologie als instructie
- [ ] Service init 1x (van 6x)
- [ ] Cache hit rate > 80%
- [ ] Test coverage > 70%
- [ ] Quality score > 80%

---

## 📊 Success Metrics

| Metric | Baseline | Target | Priority |
|--------|----------|---------|----------|
| Response Time | 8-12s | <5s | P1 |
| Token Count | 7,250 | 1,250 | P1 |
| API Cost/month | €1,500 | €250 | P1 |
| Service Init | 6x | 1x | P1 |
| Context Fields | 1/3 | 3/3 | P1 |
| Cache Hit Rate | 0% | >80% | P2 |

---

*Epic updated: 3 september 2025*
*Contains: 10 user stories (5 existing + 5 new)*
*UAT Critical: PER-006, PER-007, PER-008, PER-009, PER-010*
