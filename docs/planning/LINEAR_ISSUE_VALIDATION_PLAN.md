# Linear Issue Validation Plan

**Doel:** Valideer alle open Linear issues tegen de huidige staat van de codebase
**Methode:** Ultrathink + 5 Multiagents per issue
**Aangemaakt:** 2025-11-27

---

## Overzicht Open Issues

### In Progress (7 issues)
| # | ID | Titel | Priority |
|---|-----|-------|----------|
| 1 | DEF-149 | Clarify implicit vs explicit context usage | P1 |
| 2 | DEF-154 | Remove conflicting word_type_advice from ExpertiseModule | P1 |
| 3 | DEF-123 | Implement context-aware module loading (-25% tokens) | P1 |
| 4 | DEF-135 | Transform validation rules to instructions | P1 |
| 5 | DEF-106 | Create PromptValidator (Automated QA) | P2 |
| 6 | DEF-38 | Kritieke Issues in Ontologische Promptinjecties | P2 |
| 7 | DEF-40 | Optimaliseer category-specific prompt injecties | P3 |

### Backlog - High Priority (17 issues)
| # | ID | Titel | Priority |
|---|-----|-------|----------|
| 8 | DEF-138 | Fix Ontologische Categorie Instructies | P1 |
| 9 | DEF-140 | Refactor _generate_scores() - Reduce CC from 23 to <10 | P1 |
| 10 | DEF-141 | Refactor tabbed_interface.py - Split god object | P1 |
| 11 | DEF-127 | Phase 1.2: Reduce Cognitive Load | P1 |
| 12 | DEF-146 | Fix ESS-02 'is' usage + article "een" contradiction | P0 |
| 13 | DEF-147 | Exempt ontological markers from container rule (ARAI-02) | P0 |
| 14 | DEF-148 | Clarify relative clause usage guidelines | P0 |
| 15 | DEF-150 | Categorize 42 forbidden patterns | P0 |
| 16 | DEF-177 | Remove All DEPRECATED Code (12 instances) | P2 |
| 17 | DEF-139 | Improve Ontological Category Detection | P2 |
| 18 | DEF-142 | Extract magic numbers to configuration | P2 |
| 19 | DEF-143 | Fix async bridge timeout handling | P2 |
| 20 | DEF-179 | Decompose Giant UI Components | P2 |
| 21 | DEF-182 | Fix cache persistence warnings and pickle errors | P3 |
| 22 | DEF-183 | Fix singleton bypass in DUP_01.py | P3 |
| 23 | DEF-184 | Fix singleton bypass in synonym_service_refactored.py | P3 |
| 24 | DEF-180 | Improve Docstring Coverage | P3 |

### Backlog - Integrated Prompt Improvement Strategy (12 issues)
| # | ID | Titel |
|---|-----|-------|
| 25 | DEF-157 | Phase 1.1: Delete forbidden patterns (-500 tokens) |
| 26 | DEF-158 | Phase 1.2: Move metadata to UI (-600 tokens) |
| 27 | DEF-159 | Phase 1.3: Filter examples by relevance (-700 tokens) |
| 28 | DEF-160 | Phase 1.4: Fix ESS-01 template (+5% quality) |
| 29 | DEF-161 | Phase 1.5: Merge duplicate instructions (-200 tokens) |
| 30 | DEF-162 | Phase 1.6: Add token budget logger |
| 31 | DEF-163 | Phase 2.1: Generate 50 diverse baseline definitions |
| 32 | DEF-164 | Phase 2.2: Manual QA scoring |
| 33 | DEF-165 | Phase 2.3: Automated rule compliance check |
| 34 | DEF-166 | Phase 2.4: Analyze baseline results |
| 35 | DEF-167 | Phase 3: Decision Gate |
| 36 | DEF-168 | Phase 4: Implementation (TBD) |

### Backlog - Other (7+ issues)
| # | ID | Titel |
|---|-----|-------|
| 37 | DEF-117 | Sprint 2: Extract Repository Business Logic |
| 38 | DEF-144 | Refactor SessionStateManager |
| 39 | DEF-145 | Consolidate test fixtures |

---

## Onderzoeksprotocol per Issue

### Standaard Onderzoeksstappen (per issue)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ISSUE VALIDATION PROTOCOL                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FASE 1: ULTRATHINK ANALYSE (diepgaand)                         │
│  ────────────────────────────────────────                       │
│  • Lees issue description volledig                              │
│  • Analyseer genoemde bestanden in codebase                     │
│  • Vergelijk issue requirements met huidige code                │
│  • Bepaal: GELDIG / VEROUDERD / DEELS_GELDIG / DONE             │
│                                                                  │
│  FASE 2: MULTIAGENT VALIDATIE (5 agents parallel)               │
│  ────────────────────────────────────────────────               │
│  Agent 1: CODE-REVIEWER                                         │
│    → Analyseer genoemde code locaties                           │
│    → Check of probleem nog bestaat                              │
│                                                                  │
│  Agent 2: EXPLORE-AGENT                                         │
│    → Zoek gerelateerde code in codebase                         │
│    → Identificeer eventuele fixes die al gedaan zijn            │
│                                                                  │
│  Agent 3: DEBUG-SPECIALIST                                      │
│    → Valideer of het beschreven probleem reproduceerbaar is     │
│    → Check voor runtime issues                                  │
│                                                                  │
│  Agent 4: CODE-SIMPLIFIER                                       │
│    → Beoordeel complexiteit van huidige code                    │
│    → Vergelijk met issue's complexiteitsanalyse                 │
│                                                                  │
│  Agent 5: FULL-STACK-DEVELOPER                                  │
│    → Analyseer implementatie haalbaarheid                       │
│    → Check dependencies en blocking issues                      │
│                                                                  │
│  FASE 3: SYNTHESE & VERDICT                                     │
│  ──────────────────────────                                     │
│  • Combineer resultaten van 5 agents                            │
│  • Bepaal eindoordeel met confidence score                      │
│  • Genereer actie-aanbevelingen                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Gedetailleerd Plan per Issue

### ISSUE 1: DEF-149 - Clarify implicit vs explicit context usage

**Status:** In Progress | **Priority:** P1

**Onderzoeksvragen:**
1. Bestaat `src/services/prompts/modules/context_awareness_module.py` nog?
2. Zijn de methodes `_build_rich_context_section()`, `_build_moderate_context_section()`, `_build_minimal_context_section()` aanwezig?
3. Bevat de code al clarificatie over implicit vs explicit context?

**Multiagent Taken:**
| Agent | Taak | Focus |
|-------|------|-------|
| code-reviewer | Analyseer context_awareness_module.py | Lines 202, 242, 277 |
| explore | Zoek "implicit" en "explicit" in prompts/ | Bestaande implementatie |
| debug-specialist | Test prompt output voor context scenarios | Runtime validatie |
| code-simplifier | Beoordeel huidige context sectie complexiteit | Complexiteit score |
| full-stack-developer | Check of fix al geïmplementeerd is | Git history |

**Verwacht Resultaat:** GELDIG / VEROUDERD / DONE

---

### ISSUE 2: DEF-154 - Remove conflicting word_type_advice from ExpertiseModule

**Status:** In Progress | **Priority:** P1

**Onderzoeksvragen:**
1. Bestaat `src/services/prompts/modules/expertise_module.py`?
2. Bestaat methode `_build_word_type_advice()` (lines 169-185)?
3. Wordt deze methode aangeroepen in `execute()` (lines 86-88)?

**Multiagent Taken:**
| Agent | Taak | Focus |
|-------|------|-------|
| code-reviewer | Analyseer expertise_module.py | Lines 86-88, 169-185 |
| explore | Zoek "word_type_advice" in codebase | Alle referenties |
| debug-specialist | Valideer conflicting advice scenario | Test met voorbeelden |
| code-simplifier | Beoordeel impact van verwijdering | Dependencies |
| full-stack-developer | Check of methode nog aangeroepen wordt | Call graph |

**Verwacht Resultaat:** GELDIG / VEROUDERD / DONE

---

### ISSUE 3: DEF-123 - Implement context-aware module loading (-25% tokens)

**Status:** In Progress | **Priority:** P1

**Onderzoeksvragen:**
1. Bestaat `PromptOrchestrator` class?
2. Is er een `_get_active_modules()` methode geïmplementeerd?
3. Laden alle 16 modules nog steeds ALTIJD?

**Multiagent Taken:**
| Agent | Taak | Focus |
|-------|------|-------|
| code-reviewer | Analyseer prompt_orchestrator.py | Module loading logic |
| explore | Zoek "active_modules" of conditional loading | Bestaande implementatie |
| debug-specialist | Meet actual token count per prompt | Performance data |
| code-simplifier | Beoordeel huidige module architectuur | Complexiteit |
| full-stack-developer | Analyseer ModuleContext class | Data flow |

**Verwacht Resultaat:** GELDIG / VEROUDERD / DONE

---

### ISSUE 4: DEF-135 - Transform validation rules to instructions

**Status:** In Progress | **Priority:** P1

**Onderzoeksvragen:**
1. Bevatten rule modules nog "Check/Verify/Validate" taal?
2. Zijn rules al getransformeerd naar "Use/Do/Avoid" instructies?
3. Welke van de 7 modules is al aangepast?

**Multiagent Taken:**
| Agent | Taak | Focus |
|-------|------|-------|
| code-reviewer | Analyseer alle 7 rule modules | Taalgebruik |
| explore | Grep voor "Check dat", "Controleer of" | Pattern zoeken |
| debug-specialist | Valideer prompt output | Instructie formaat |
| code-simplifier | Beoordeel consistentie | Alle modules gelijk? |
| full-stack-developer | Count: hoeveel rules getransformeerd? | Progress tracking |

**Betrokken Bestanden:**
- `src/services/prompts/modules/arai_rules_module.py`
- `src/services/prompts/modules/con_rules_module.py`
- `src/services/prompts/modules/ess_rules_module.py`
- `src/services/prompts/modules/integrity_rules_module.py`
- `src/services/prompts/modules/sam_rules_module.py`
- `src/services/prompts/modules/structure_rules_module.py`
- `src/services/prompts/modules/ver_rules_module.py`

**Verwacht Resultaat:** GELDIG / VEROUDERD / DEELS_GELDIG

---

### ISSUE 5: DEF-106 - Create PromptValidator (Automated QA)

**Status:** In Progress | **Priority:** P2

**Onderzoeksvragen:**
1. Bestaat `src/services/prompts/prompt_validator.py`?
2. Is PromptValidator geïntegreerd in orchestrator?
3. Welke validation checks zijn geïmplementeerd?

**Multiagent Taken:**
| Agent | Taak | Focus |
|-------|------|-------|
| code-reviewer | Check of prompt_validator.py bestaat | File existence |
| explore | Zoek "PromptValidator" in codebase | Imports, usage |
| debug-specialist | Test validation functionaliteit | Runtime checks |
| code-simplifier | Beoordeel validation architectuur | Design |
| full-stack-developer | Analyseer 6+ validation checks | Completeness |

**Verwacht Resultaat:** GELDIG / VEROUDERD / DONE

---

### ISSUE 6: DEF-38 - Kritieke Issues in Ontologische Promptinjecties

**Status:** In Progress | **Priority:** P2

**Onderzoeksvragen:**
1. Is PROCES actieve/passieve contradictie opgelost?
2. Is TYPE/Instance confusion opgelost?
3. Zijn EXEMPLAAR voorbeelden gecorrigeerd?
4. Is PROCES/RESULTAAT grens verduidelijkt?
5. Zijn BFO foundations toegevoegd?

**Multiagent Taken:**
| Agent | Taak | Focus |
|-------|------|-------|
| code-reviewer | Analyseer semantic_categorisation_module.py | Lines 180-267 |
| explore | Zoek "BFO", "ontologische" in codebase | Implementatie |
| debug-specialist | Test alle 4 categorieën | PROCES/TYPE/EXEMPLAAR/RESULTAAT |
| code-simplifier | Beoordeel category guidance | Kwaliteit |
| full-stack-developer | Check Quality Score improvement | 5.2→7.0? |

**Verwacht Resultaat:** GELDIG / VEROUDERD / DEELS_GELDIG

---

### ISSUE 7: DEF-40 - Optimaliseer category-specific prompt injecties

**Status:** In Progress | **Priority:** P3

**Onderzoeksvragen:**
1. Is base_section verwijderd uit output?
2. Heeft elke categorie standalone guidance?
3. Zijn token counts gereduceerd?

**Multiagent Taken:**
| Agent | Taak | Focus |
|-------|------|-------|
| code-reviewer | Analyseer _build_ess02_section() | Fallback logic |
| explore | Zoek "base_section" in codebase | Verwijderd? |
| debug-specialist | Test prompt output per categorie | Token count |
| code-simplifier | Beoordeel category templates | Optimalisatie |
| full-stack-developer | Vergelijk met DEF-38 | Dependencies |

**Verwacht Resultaat:** GELDIG / VEROUDERD / DONE

---

### ISSUE 8: DEF-138 - Fix Ontologische Categorie Instructies

**Status:** Backlog | **Priority:** P1

**Onderzoeksvragen:**
1. Bevatten categorieën nog meta-woorden als kick-off?
2. Zijn instructies aangepast naar zelfstandig naamwoord start?
3. Zijn alle 4 categorieën gecorrigeerd?

**Multiagent Taken:**
| Agent | Taak | Focus |
|-------|------|-------|
| code-reviewer | Analyseer _get_category_specific_guidance() | Lines 180-267 |
| explore | Grep voor "proces waarin", "activiteit waarbij" | Verboden patterns |
| debug-specialist | Test definitie generatie per categorie | Output validatie |
| code-simplifier | Beoordeel instructie kwaliteit | Duidelijkheid |
| full-stack-developer | Check of voorbeelden correct zijn | Geen meta-woorden |

**Verwacht Resultaat:** GELDIG / VEROUDERD / DONE

---

### ISSUE 9: DEF-140 - Refactor _generate_scores()

**Status:** Backlog | **Priority:** P1

**Onderzoeksvragen:**
1. Wat is huidige cyclomatic complexity van _generate_scores()?
2. Is methode al gesplitst in sub-methodes?
3. Zijn er tests voor de refactored code?

**Multiagent Taken:**
| Agent | Taak | Focus |
|-------|------|-------|
| code-reviewer | Analyseer improved_classifier.py:203-329 | CC meting |
| explore | Zoek extracted methods | _apply_pattern_matching etc |
| debug-specialist | Run radon voor CC meting | Metrics |
| code-simplifier | Beoordeel huidige structuur | Refactor nodig? |
| full-stack-developer | Check test coverage | 98%+ behouden? |

**Verwacht Resultaat:** GELDIG / VEROUDERD / DONE

---

### ISSUE 10: DEF-141 - Refactor tabbed_interface.py

**Status:** Backlog | **Priority:** P1

**Onderzoeksvragen:**
1. Hoeveel lines heeft tabbed_interface.py nu?
2. Is het gesplitst in handlers/ en renderers/?
3. Zijn er <300 line files?

**Multiagent Taken:**
| Agent | Taak | Focus |
|-------|------|-------|
| code-reviewer | Analyseer tabbed_interface.py | LOC count |
| explore | Zoek src/ui/handlers/ en src/ui/renderers/ | Directory structuur |
| debug-specialist | Check voor god methods | 409-line method? |
| code-simplifier | Beoordeel file structuur | SRP compliance |
| full-stack-developer | Check dependencies | Circular imports? |

**Verwacht Resultaat:** GELDIG / VEROUDERD / DONE

---

### ISSUE 11-24: Batch Analyse (Backlog High Priority)

Voor issues 11-24 volgt hetzelfde protocol met focus op:

| Issue | Primaire Check |
|-------|----------------|
| DEF-127 | Cognitive load: <15 concepts? |
| DEF-146 | ESS-02 exception clause aanwezig? |
| DEF-147 | ARAI-02 exception voor ontological markers? |
| DEF-148 | Relative clause guidance geclarificeerd? |
| DEF-150 | 42 patterns → 7 categorieën? |
| DEF-177 | DEPRECATED markers: 12→0? |
| DEF-139 | Process vs Result classification fixed? |
| DEF-142 | Magic numbers in config? |
| DEF-143 | Async timeout handling fixed? |
| DEF-179 | UI components <600 LOC? |
| DEF-182 | Cache warnings fixed? |
| DEF-183 | DUP_01.py singleton fix? |
| DEF-184 | synonym_service singleton fix? |
| DEF-180 | Docstring coverage >80%? |

---

### ISSUE 25-36: Integrated Prompt Improvement Strategy

**Batch Validatie:**
- Check of Phase 1.1-1.6 geïmplementeerd zijn
- Check of Phase 2.1-2.4 baseline data bestaat
- Check of Phase 3 decision gate bereikt is
- Check of Phase 4 gestart is

---

## Uitvoeringsplan

### Fase 1: In Progress Issues (1-7)
**Geschatte tijd:** 2 uur
**Prioriteit:** HOOG - Deze claimen actief te zijn

### Fase 2: Backlog High Priority (8-24)
**Geschatte tijd:** 3 uur
**Prioriteit:** MEDIUM - Kunnen verouderd zijn

### Fase 3: Prompt Improvement Strategy (25-36)
**Geschatte tijd:** 1.5 uur
**Prioriteit:** MEDIUM - Project-specifiek

### Fase 4: Overige Backlog (37+)
**Geschatte tijd:** 1 uur
**Prioriteit:** LAAG - Algemene backlog

---

## Output Format per Issue

```yaml
issue_id: DEF-XXX
titel: "..."
huidige_status: "In Progress" | "Backlog"
validatie_resultaat: "GELDIG" | "VEROUDERD" | "DEELS_GELDIG" | "DONE"
confidence: 0.0-1.0
evidence:
  - "Code locatie X bestaat/bestaat niet"
  - "Functionaliteit Y is/is niet geïmplementeerd"
  - "Pattern Z gevonden/niet gevonden"
aanbeveling: "KEEP" | "CLOSE" | "UPDATE" | "SPLIT"
actie_items:
  - "..."
agent_consensus:
  code_reviewer: "..."
  explore: "..."
  debug_specialist: "..."
  code_simplifier: "..."
  full_stack_developer: "..."
```

---

## Volgende Stappen

1. **Gebruiker bevestigt plan** - Akkoord met aanpak?
2. **Start validatie** - Begin met In Progress issues (1-7)
3. **Per-issue rapportage** - Live updates tijdens uitvoering
4. **Eindrapport** - Samenvatting met alle resultaten

---

*Plan gegenereerd door BMad Master op 2025-11-27*
