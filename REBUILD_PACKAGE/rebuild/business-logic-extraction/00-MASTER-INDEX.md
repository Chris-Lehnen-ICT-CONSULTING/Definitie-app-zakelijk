# Business Logic Extraction - Master Index

**Project:** DefinitieAgent
**Extraction Date:** 2025-10-02
**Method:** 6 Parallel Agents (BMad Master)
**Status:** ✅ COMPLETE

---

## 📊 Executive Summary

### Extractie Statistieken
- **Totaal geëxtraheerde business rules:** 4,318 LOC
- **Aantal validatieregels:** 45+
- **Aantal services geanalyseerd:** 15+
- **Aantal database tabellen:** 8
- **Aantal UI tabs:** 6+
- **Gedocumenteerde regels:** ~3,200 LOC
- **Gap percentage:** 26% (1,118 LOC ongedocumenteerd)

### Kritieke Bevindingen
✅ **Sterk gedocumenteerd:** Validatieregels (87%), Orchestrators (67%), Domain Logic (100%)
⚠️ **Gaps:** 7 validatieregels, ModernWebLookupService, 2 orchestrators, config mismatch
🚨 **Actie vereist:** P0 critical gaps (12-14 uur), P1 high priority (26-37 uur)

---

## 📁 Navigatie - Extractie Documenten

### Agent 1: Services & Core Business Logic
**📄 Document:** [01-services-core-logic/SERVICES-EXTRACTION.md](01-services-core-logic/SERVICES-EXTRACTION.md)
**Grootte:** 56 KB | 800+ regels
**Scope:**
- ServiceContainer (Dependency Injection)
- ValidationOrchestratorV2 (45 validatieregels)
- DefinitionOrchestratorV2 (11-fase flow)
- PromptServiceV2 (Context-aware prompt building)
- AIServiceV2 (GPT-4 integratie, rate limiting)
- ModernWebLookupService (Wikipedia, SRU, ECLI)
- ModularValidationService (Regel loading, scoring)
- DefinitionRepository (Save, duplicate detection, search)
- DuplicateDetectionService (3-level matching)
- CleaningService (GPT format detectie)
- WorkflowService (Status transitions, permissions)
- GatePolicyService (Approval gates)

**Key Business Rules:**
- 15+ feature flags
- Rate limits: 60/min, 3000/hour
- Timeouts: AI=30s, Web=10s
- Token limits: Prompt=10K, Response=500
- PII sanitization
- Duplicate detection: Jaccard similarity 70% threshold

---

### Agent 2: Database Schema & Business Rules
**📄 Document:** [02-database-business-rules/DATABASE-EXTRACTION.md](02-database-business-rules/DATABASE-EXTRACTION.md)
**Grootte:** 48 KB | 1,400+ regels
**Scope:**
- 8 core tables (definities, definitie_geschiedenis, definitie_voorbeelden, definitie_tags, externe_bronnen, import_export_logs, definitie_synoniemen, validation_config)
- 80+ business rules
- 3 triggers (automatic audit logging)
- 11 indexes (performance optimization)
- 8 migration rules

**Key Business Rules:**
- **BR-DB-001:** 11-category ontological classification
- **BR-DB-002:** 5-stage status workflow (imported → draft → review → established → archived)
- **BR-DB-006:** JSON array storage for multi-value fields
- **BR-DB-009:** Voorkeursterm single source of truth
- **BR-DB-010:** 3-level duplicate detection (exact + synonym + fuzzy)
- **BR-DB-011:** Wettelijke basis normalization (order-independent comparison)

**Critical Algorithms:**
- Duplicate detection: 3-level matching (exact begrip + synonym + fuzzy)
- Similarity calculation: Jaccard similarity with 70% threshold
- JSON normalization: Unique, sorted, stripped arrays
- Automatic audit logging with context snapshots

---

### Agent 3: Validatieregels (45+)
**📄 Primary Document:** [03-validation-rules/VALIDATION-EXTRACTION.md](03-validation-rules/VALIDATION-EXTRACTION.md)
**📄 Quick Reference:** [03-validation-rules/QUICK_REFERENCE.md](03-validation-rules/QUICK_REFERENCE.md)
**📄 Summary:** [03-validation-rules/EXTRACTION_SUMMARY.md](03-validation-rules/EXTRACTION_SUMMARY.md)
**📄 Verification:** [03-validation-rules/VERIFICATION_REPORT.md](03-validation-rules/VERIFICATION_REPORT.md)
**Grootte:** 58 KB (primary) | 105 KB (totaal)
**Scope:**
- 45+ validatieregels in 7 categorieën
- ARAI (Atomiciteit, Relevantie, Adequaatheid, Inconsistentie)
- CON (Consistentie)
- ESS (Essentie)
- INT (Intertekstueel)
- SAM (Samenhang)
- STR (Structuur)
- VER (Verduidelijking)

**Rule Distribution:**
- High Priority: 15 regels
- Medium Priority: 22 regels
- Low Priority: 8 regels

**Validation Orchestration:**
- ModularValidationService (regel loading, deterministic evaluation)
- ApprovalGatePolicy (EPIC-016, hard/soft requirements)
- Score calculation and acceptability determination

**Critical Rules:**
- ARAI-001: Circulaire definities detectie
- CON-001: Context-specifieke inconsistenties
- ESS-001: Essentie-preservatie
- SAM-001: Samenhang tussen context en definitie
- STR-001: Structurele eisen (lengte, leesbaarheid)

---

### Agent 4: UI/Workflow Business Logic
**📄 Document:** [04-ui-workflow-logic/UI-WORKFLOW-EXTRACTION.md](04-ui-workflow-logic/UI-WORKFLOW-EXTRACTION.md)
**Grootte:** 39 KB
**Scope:**
- Application flow (startup, tab navigation, session state)
- 6+ Streamlit tabs (Generator, Edit, Repository, Expert Review, Import/Export, etc.)
- State management patterns (SessionStateManager)
- Workflow orchestration (status transitions, approval gates)

**Key Workflows:**
- **DefinitieGenerator:** begrip → context → category → generate → validate → save
- **DefinitionEditTab:** Search → select → edit → validate → auto-save → version
- **ExpertReviewTab:** Review queue → gate check → approve/reject/unlock
- **Complete Lifecycle:** Creation → Edit → Review → [Gate] → Established → [Unlock/Archive]

**Business Rules:**
- Duplicate check before generate (unless forced)
- At least one context required (org OR jur OR wet)
- Gate-based approval (hard/soft requirements)
- Auto-save with 30s throttle
- Optimistic locking for conflict prevention
- Voorkeursterm from synoniemen

---

### Agent 5: Bestaande Documentatie Inventarisatie
**📄 Primary Document:** [05-existing-docs-inventory/DOCS-INVENTORY.md](05-existing-docs-inventory/DOCS-INVENTORY.md)
**📄 Summary:** [05-existing-docs-inventory/SUMMARY.md](05-existing-docs-inventory/SUMMARY.md)
**📄 README:** [05-existing-docs-inventory/README.md](05-existing-docs-inventory/README.md)
**Grootte:** 28 KB (primary) | 38 KB (totaal)
**Scope:**
- 1,039 markdown bestanden geanalyseerd
- 850,684 woorden documentatie
- 127 business logic topics geïdentificeerd
- 6 documentatie categorieën

**Coverage Analysis:**
- ✅ **Excellent (85-95%):** EPIC-002 (Validation), EPIC-010 (Context), Enterprise Architecture, US-160 (Approval Gate)
- ⚠️ **Good (60-70%):** Solution Architecture, Workflows
- ❌ **Poor (25-35%):** Prompts, Export, Web Lookup, Quality Scoring

**Kritieke Gaps (35 geïdentificeerd):**
- Quality scoring algorithm rationale
- Context validation rules
- Workflow state machine
- Prompt engineering business logic
- Web lookup selection criteria
- Export business rules

---

### Agent 6: Gap Analyse & Vergelijking
**📄 Document:** [06-gap-analysis/GAP-ANALYSIS.md](06-gap-analysis/GAP-ANALYSIS.md)
**📄 README:** [06-gap-analysis/README.md](06-gap-analysis/README.md)
**Grootte:** 19 KB
**Scope:**
- Vergelijking code (agents 1-4) vs documentatie (agent 5)
- 8 kritieke gaps geïdentificeerd
- Prioritized recommendations (P0/P1/P2)
- Impact assessment

**Executive Summary:**
- **Overall Coverage:** ~85%
- **Total business rules in code:** 4,318 LOC
- **Total documented:** ~3,200 LOC
- **Gap:** 26% (1,118 LOC)
- **Critical gaps:** 8

**Kritieke Gaps:**
1. 7 validatieregels ongedocumenteerd (VAL-EMP-001, VAL-LEN-001, VAL-LEN-002, CON-CIRC-001, ESS-CONT-001, STR-TERM-001, STR-ORG-001)
2. ModernWebLookupService missing (1,019 LOC)
3. 2 orchestrators ongedocumenteerd (prompt_orchestrator, import_export_beheer/orchestrator)
4. Config structure mismatch (planned vs actual)
5. Regeneration service underspecified
6. Rule heuristics count mismatch (13 vs 20)
7. Business logic extraction progress niet geïntegreerd
8. Voorbeelden management partially extracted

**Recommendations:**
- **P0 CRITICAL (12-14 uur):** Update extraction plan, reconcile config, analyze 2 orchestrators
- **P1 HIGH (26-37 uur):** Document 7 rules, extract ModernWebLookupService, complete voorbeelden
- **P2 MEDIUM (11-15 uur):** Extract document limits, document prompt orchestrator

**Total gap closure effort:** 38-53 uur (1-2 weken)

---

## 🎯 Consolidated Business Logic - Quick Reference

### Services Layer (Agent 1)
| Service | LOC | Key Business Rules | Priority |
|---------|-----|-------------------|----------|
| ServiceContainer | 150 | Singleton, DI, feature flags | Critical |
| DefinitionOrchestratorV2 | 800+ | 11-phase flow, web lookup, validation | Critical |
| ValidationOrchestratorV2 | 250+ | Pre-cleaning, context enrichment, batch | High |
| PromptServiceV2 | 300+ | Context-aware, ontological mapping | High |
| AIServiceV2 | 200+ | Rate limiting, token estimation, caching | High |
| ModernWebLookupService | 1,019 | Provider weighting, ECLI boost | High |
| ModularValidationService | 400+ | 45 rules, scoring, acceptability | Critical |
| DefinitionRepository | 500+ | Save, duplicate detection, search | High |
| DuplicateDetectionService | 200+ | 3-level matching, Jaccard similarity | High |

### Database Layer (Agent 2)
| Table | Columns | Key Business Rules | Triggers |
|-------|---------|-------------------|----------|
| definities | 20+ | 11 categories, 5 statuses, voorkeursterm SSOT | 1 (audit) |
| definitie_geschiedenis | 8 | Audit trail, 6 change types, context snapshots | 1 (auto-log) |
| definitie_voorbeelden | 10 | 6 example types, active replacement, synonym lookup | 1 (timestamp) |
| definitie_tags | 3 | Many-to-many, cascade delete | - |
| externe_bronnen | 8 | 5 source types, duplicate detection | - |

### Validation Layer (Agent 3)
| Category | Rules | Priority | Key Business Logic |
|----------|-------|----------|-------------------|
| ARAI | 8 | High | Circulaire definitie detectie, relevantie checks |
| CON | 7 | High | Context consistentie, terminologie consistentie |
| ESS | 6 | Critical | Essentie preservatie, inhoudelijke volledigheid |
| INT | 5 | Medium | Cross-reference checks, intertekstualiteit |
| SAM | 7 | High | Context-definitie samenhang, coherentie |
| STR | 8 | Medium | Lengte, leesbaarheid, structuur |
| VER | 4 | Low | Duidelijkheid, begrijpelijkheid |

### UI/Workflow Layer (Agent 4)
| Component | Key Workflows | Business Rules | State Management |
|-----------|--------------|----------------|------------------|
| DefinitieGenerator | Generate → Validate → Save | Duplicate check, force option | Auto-load to Edit |
| DefinitionEditTab | Search → Edit → Auto-save | Version management, conflict detection | SessionStateManager |
| ExpertReviewTab | Review → Gate → Approve | Hard/soft requirements, override reason | Role-based permissions |
| Repository | Search → Export → Import | Format rules, bulk operations | Pagination, filters |

---

## 📋 Aanbevelingen voor Rebuild

### Must Preserve (Critical Business Logic)
1. **Validatieregels (45+):** Alle 45+ regels met business rationale
2. **Duplicate Detection:** 3-level matching algorithm (exact + synonym + fuzzy)
3. **Workflow Status Machine:** 5-stage lifecycle (imported → draft → review → established → archived)
4. **Approval Gates (US-160):** Hard/soft requirements, override reasoning
5. **Context Management:** At least one context required (org/jur/wet)
6. **Audit Trail:** Automatic logging with context snapshots
7. **UTF-8 Encoding:** Critical for Dutch legal text
8. **Rate Limiting:** 60/min, 3000/hour for API calls
9. **Session State Pattern:** SessionStateManager only
10. **Ontological Categorization:** 11-category classification

### Moet Verbeterd (Anti-patterns)
1. ❌ **God Object (DefinitionOrchestratorV2):** 800+ LOC, split naar kleinere services
2. ❌ **Monolithic Tabs:** Split tabs naar componenten
3. ❌ **Direct Session State Access:** Altijd via SessionStateManager
4. ❌ **Service Re-initialization:** Gebruik @st.cache_resource
5. ❌ **Hardcoded Config:** Extract naar config files
6. ❌ **Missing Interfaces:** Add voor testability

### Gap Closure Prioriteit
**P0 CRITICAL (12-14 uur):**
- Update extraction plan met 7 missing rules
- Reconcile config structure (planned vs actual)
- Analyze 2 missing orchestrators

**P1 HIGH (26-37 uur):**
- Document 7 missing validation rules
- Extract ModernWebLookupService logic
- Complete voorbeelden management extraction

**P2 MEDIUM (11-15 uur):**
- Extract document context limits
- Document prompt orchestrator
- Analyze import/export orchestrator

---

## 📊 Metrics & Statistics

### Extractie Statistieken
- **Totaal extractie bestanden:** 13 documenten
- **Totaal grootte:** 286 KB
- **Totaal regels:** ~5,000 regels markdown
- **Analyse tijd:** 6 agents × ~45 minuten = ~4.5 uur
- **Woorden geanalyseerd:** 850,684 woorden (bestaande docs)
- **Code LOC geanalyseerd:** 4,318 LOC (business logic)

### Coverage Statistieken
- **Overall business logic coverage:** 85%
- **Validation rules coverage:** 87% (46/53 rules)
- **Orchestration coverage:** 67% (4/6 orchestrators)
- **Database coverage:** 100% (8/8 tables)
- **UI/Workflow coverage:** 90% (6/6+ tabs)
- **Documentation coverage:** 74% (well-documented areas)

### Gap Statistieken
- **Total gaps identified:** 8 kritieke gaps
- **Ongedocumenteerde LOC:** 1,118 LOC (26%)
- **Missing validation rules:** 7 rules
- **Missing services:** 1 service (ModernWebLookupService)
- **Missing orchestrators:** 2 orchestrators
- **Gap closure effort:** 38-53 uur (1-2 weken)

---

## 🚀 Next Steps

### Immediate Actions (P0)
1. ✅ Review alle extractie documenten
2. ✅ Valideer gap analysis bevindingen
3. ⏳ Close P0 critical gaps (12-14 uur)
4. ⏳ Update EPIC-026 Phase 1 plan

### Short-term (P1)
1. ⏳ Document 7 missing validation rules (14-21 uur)
2. ⏳ Extract ModernWebLookupService (4-6 uur)
3. ⏳ Complete voorbeelden management (4-5 uur)

### Medium-term (P2)
1. ⏳ Extract remaining orchestrators (5-7 uur)
2. ⏳ Document prompt engineering logic (3-4 uur)
3. ⏳ Consolidate business logic in rebuild/

### Ready for Phase 2 (Implementation)
**DO NOT proceed tot:**
- ✅ All P0 gaps closed
- ✅ All P1 gaps closed
- ✅ Extraction plan updated
- ✅ Config structure reconciled
- ✅ Gap closure validated

**Revised Timeline:**
- **Phase 1 (Design):** Week 1-2 (gap closure) ← **CURRENT**
- **Phase 2 (Implementation):** Week 3-5 (extraction execution)
- **Phase 3 (Validation):** Week 6 (testing and validation)

---

## 📞 Contact & Handoff

**Extractie uitgevoerd door:** BMad Master (6 Parallel Agents)
**Date:** 2025-10-02
**Project:** DefinitieAgent
**Epic:** EPIC-026 Phase 1 (Design)

**Voor vragen over:**
- Agent 1 (Services): Zie [01-services-core-logic/SERVICES-EXTRACTION.md](01-services-core-logic/SERVICES-EXTRACTION.md)
- Agent 2 (Database): Zie [02-database-business-rules/DATABASE-EXTRACTION.md](02-database-business-rules/DATABASE-EXTRACTION.md)
- Agent 3 (Validation): Zie [03-validation-rules/README.md](03-validation-rules/README.md)
- Agent 4 (UI/Workflow): Zie [04-ui-workflow-logic/UI-WORKFLOW-EXTRACTION.md](04-ui-workflow-logic/UI-WORKFLOW-EXTRACTION.md)
- Agent 5 (Docs Inventory): Zie [05-existing-docs-inventory/README.md](05-existing-docs-inventory/README.md)
- Agent 6 (Gap Analysis): Zie [06-gap-analysis/README.md](06-gap-analysis/README.md)

**Repository:** `/Users/chrislehnen/Projecten/Definitie-app`
**Extractie Directory:** `rebuild/business-logic-extraction/`

---

**Status:** ✅ **EXTRACTION COMPLETE - READY FOR GAP CLOSURE**
