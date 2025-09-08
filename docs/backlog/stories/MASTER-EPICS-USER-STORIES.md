# MASTER EPICS AND USER STORIES

> ⚠️ **DEPRECATED DOCUMENT** ⚠️
>
> **Status:** DEPRECATED as of 05-09-2025
> **Reason:** Migrated to modern file-per-epic/story structure
>
> ## New Structure
>
> This document has been replaced by individual epic and story files:
>
> - **Epics:** Zie `/docs/backlog/epics/` directory
>   - Dashboard: [/docs/backlog/epics/INDEX.md](../epics/INDEX.md)
>   - Files: EPIC-001.md through EPIC-CFR.md
>
> - **Stories:** Zie `/docs/backlog/stories/` directory
>   - Index: [/docs/backlog/stories/INDEX.md](INDEX.md)
>   - Files: US-001.md through US-046.md
>
> ## Benefits of New Structure
> - Individual files with complete frontmatter
> - Better version control and tracking
> - Scalable for large projects
> - Enables CI/CD validation
> - Supports parallel editing
>
> ## Migration Details
> - Migration Date: 05-09-2025
> - Migrated By: Business Analyst Agent
> - Archive Location: `/docs/archief/2025-09-epic-migration/`
> - Original preserved at: `MASTER-EPICS-USER-STORIES-20250905.md`
>
> ---
>
> ⬇️ **Original content preserved below for reference** ⬇️

---

# MASTER EPICS AND USER STORIES (GEARCHIVEERD)

**Document Type:** Master Story Registry
**Versie:** 1.0.0
**Status:** DEPRECATED
**Eigenaar:** Business Analyst
**Laatst Bijgewerkt:** 04-09-2025
**Van Toepassing Op:** Historical reference only

## Document Doel

This WAS the SINGLE SOURCE OF TRUTH for all epics and user stories in the DefinitieAgent project. It has been replaced by the new structure described above.

## Snelle Navigatie

- [Episch Verhaal 1: Basis Definitie Generatie](#epic-1-basis-definitie-generatie)
- [Episch Verhaal 2: Kwaliteitstoetsing](#epic-2-kwaliteitstoetsing)
- [Episch Verhaal 3: Content Verrijking / Web Lookup](#epic-3-content-verrijking--web-lookup)
- [Episch Verhaal 4: User Interface](#epic-4-user-interface)
- [Episch Verhaal 5: Export & Import](#epic-5-export--import)
- [Episch Verhaal 6: Beveiliging & Auth](#epic-6-security--auth)
- [Episch Verhaal 7: Prestaties & Scaling](#epic-7-performance--scaling)
- [Episch Verhaal 8: Web Lookup Module (Merged with Episch Verhaal 3)](#epic-8-web-lookup-module)
- [Episch Verhaal 9: Advanced Features](#epic-9-advanced-features)

---

## Episch Verhaal 1: Basis Definitie Generatie
**Status:** ✅ DONE (100% Complete)
**Prioriteit:** HOOG
**Bedrijfswaarde:** Core functionality for legal definition generation

### Voltooide Verhalen
- Story 1.1: Basic definition generation via GPT-4 ✅
- Story 1.2: Prompt template system ✅
- Story 1.3: V1 orchestrator elimination ✅ (V2-only architecture fully geïmplementeerd)
- Story 1.4: AI Configuration System via ConfigManager ✅ (component-specific config active)
- Story 1.5: Centralized AI model configuration ✅ (no more hardcoded defaults)

### Related Vereisten
- REQ-018: Core Definition Generation
- REQ-038: OpenAI GPT-4 Integration
- REQ-059: Environment-based Configuration
- REQ-078: Data Model Definition
- REQ-079: Data Validation and Integrity
- REQ-082: Data Search and Indexing

---

## Episch Verhaal 2: Kwaliteitstoetsing
**Status:** ✅ DONE (100% Complete)
**Prioriteit:** HOOG
**Bedrijfswaarde:** Quality assurance through validation rules

### Voltooide Verhalen
- Story 2.1: Validation interface design ✅
- Story 2.2: Core implementation ✅
- Story 2.3: Container wiring ✅
- Story 2.4: Integration migration ✅
- Story 2.5: Testen & QA ✅
- Story 2.6: Production rollout ✅
- Story 2.7: All 45/45 validation rules active and working ✅
- Story 2.8: Modular validation service fully operational ✅

### Related Vereisten
- REQ-016: Nederlandse Juridische Terminologie
- REQ-017: 45 Validatieregels
- REQ-023: ARAI Validation Rules Implementatie
- REQ-024: CON Validation Rules Implementatie
- REQ-025: ESS Validation Rules Implementatie
- REQ-026: INT Validation Rules Implementatie
- REQ-027: SAM Validation Rules Implementatie
- REQ-028: STR Validation Rules Implementatie
- REQ-029: VER Validation Rules Implementatie
- REQ-030: Rule Prioriteit System
- REQ-032: Validation Orchestration Flow
- REQ-033: Rule Conflict Resolution
- REQ-034: Custom Rule Configuration
- REQ-068: Unit Test Coverage
- REQ-069: Integration Testen
- REQ-072: Test Data Management
- REQ-074: Test Automation Framework
- REQ-076: Regression Test Suite

---

## Episch Verhaal 3: Content Verrijking / Web Lookup
**Status:** 🔄 IN_PROGRESS (30% Complete)
**Prioriteit:** HOOG
**Bedrijfswaarde:** External source integration for definition enrichment

### Story 3.1: Modern Web Lookup Implementatie
**Status:** TODO
**Prioriteit:** HOOG
**Afhankelijkheden:** None

**Gebruikersverhaal:**
As a legal definition author
I want to enrich definitions with external sources
So that definitions have authoritative references and context

**Acceptatiecriteria:**
1. Gegeven a definition request
   Wanneer external lookup is enabled
   Dan Wikipedia and SRU sources are consulted
2. Gegeven external content is retrieved
   Wanneer processing for inclusion
   Dan content is validated and properly attributed

**Domeinregels:**
- All external content must include source attribution
- Content must align with ASTRA/NORA data quality standards
- Privacy-sensitive information must be filtered

**Implementatie Notities:**
- Beveiliging: Sanitize all external content (XSS prevention)
- Privacy: No PII in external lookups
- Prestaties: Cache external results for 15 minutes

### Related Vereisten
- REQ-017: 45 Validatieregels
- REQ-020: Validation Orchestrator V2
- REQ-039: Wikipedia API Integration
- REQ-040: SRU (Search/Retrieve via URL) Integration

---

## Episch Verhaal 4: User Interface
**Status:** 🔄 IN_PROGRESS (30% Complete)
**Prioriteit:** GEMIDDELD
**Bedrijfswaarde:** User experience and productivity

### Voltooide Verhalen
- Story 4.4: Basic tab structure geïmplementeerd ✅
- Story 4.5: Definition generation UI functional ✅
- Story 4.6: Validation results display working ✅

### Wachtende Verhalen
- Story 4.1: Tab activation (7/10 tabs still needed: Voorbeelden, Grammatica, etc.) ⏳
- Story 4.2: UI performance optimization (target < 200ms response) ⏳
- Story 4.3: Responsive design implementation ⏳

### Related Vereisten
- REQ-021: Web Lookup Integration
- REQ-048: Responsive Web Design
- REQ-049: Dark Mode Support
- REQ-050: Accessibility WCAG 2.1 AA Compliance
- REQ-051: Multi-language Support
- REQ-052: Real-time Validation Feedback
- REQ-053: Progress Indicators
- REQ-054: Clear Error Messaging
- REQ-055: Inline Help Documentation
- REQ-056: Keyboard Navigation Support
- REQ-057: Mobile Responsive Interface
- REQ-075: User Acceptance Testen

---

## Episch Verhaal 5: Export & Import
**Status:** ❌ TODO (10% Complete)
**Prioriteit:** LAAG
**Bedrijfswaarde:** Data portability and integration

### Wachtende Verhalen
- Story 5.1: Export formats (JSON, PDF, DOCX)
- Story 5.2: Import validation
- Story 5.3: Batch operations

### Related Vereisten
- REQ-022: Export Functionality
- REQ-042: Export to Multiple Formats
- REQ-043: Import from External Sources
- REQ-083: Data Export Formats
- REQ-084: Data Import Validation

---

## Episch Verhaal 6: Beveiliging & Auth
**Status:** 🔄 IN_PROGRESS (40% Complete)
**Prioriteit:** KRITIEK
**Bedrijfswaarde:** Beveiliging compliance and data protection

### Voltooide Verhalen
- Story 6.2: API Key Beveiliging Fix ✅ (removed exposed keys from config)
- Story 6.3: Environment variable configuration ✅ (all keys via env vars)
- Story 6.4: Component-specific AI configuration security ✅

### Story 6.1: API Key Validation at Startup 🆕
**Status:** TODO
**Prioriteit:** HOOG
**Assigned:** Development Team
**Afhankelijkheden:** None

**Gebruikersverhaal:**
As a system administrator
I want API keys validated at application startup
So that configuration errors are caught early and don't cause runtime failures

**Acceptatiecriteria:**
1. Gegeven the application starts
   Wanneer OpenAI API key is configured
   Dan the key is validated via test API call
2. Gegeven an invalid API key is detected
   Wanneer application initialization occurs
   Dan clear error message is shown and startup is halted
3. Gegeven a valid API key
   Wanneer application starts
   Dan initialization continues normally

**Domeinregels:**
- Comply with NORA security guidelines for credential management
- Follow ASTRA patterns for configuration validation
- No sensitive data in error messages or logs

**Implementatie Notities:**
- Beveiliging: Never log full API keys (only last 4 chars)
- Privacy: No API key in error tracking
- Prestaties: Validation timeout of 5 seconds
- Location: Add to `src/services/container.py` initialization

**Code References:**
- Files affected: `src/services/container.py`, `src/services/ai_service_v2.py`
- Key functions: `ServiceContainer.__init__()`, `AIServiceV2.validate_api_key()`

### Related Vereisten
- REQ-044: Justice SSO Integration
- REQ-045: Audit Logging System
- REQ-047: Backup and Restore Functionality
- REQ-063: Rate Limiting Per User
- REQ-071: Beveiliging Testen
- REQ-081: Data Archival Strategy

---

## Episch Verhaal 7: Prestaties & Scaling
**Status:** 🔄 IN_PROGRESS (35% Complete)
**Prioriteit:** HOOG
**Bedrijfswaarde:** System efficiency and cost optimization

### Voltooide Verhalen
- Story 7.6: V1 to V2 migration completed ✅ (no more dual systems)
- Story 7.7: Service container optimization started ✅

### Story 7.1: Service Initialization Caching 🆕
**Status:** TODO
**Prioriteit:** HOOG
**Assigned:** Development Team
**Afhankelijkheden:** None

**Gebruikersverhaal:**
As a developer
I want service initialization to happen only once
So that application startup is fast and memory efficient

**Acceptatiecriteria:**
1. Gegeven Streamlit reruns occur
   Wanneer ServiceContainer is accessed
   Dan the same singleton instance is returned
2. Gegeven the application starts
   Wanneer ServiceContainer initializes
   Dan it happens exactly once per session
3. Gegeven cached services are accessed
   Wanneer multiple UI components request them
   Dan no re-initialization occurs

**Domeinregels:**
- Follow NORA performance guidelines (response < 200ms)
- Implement according to ASTRA caching patterns
- Memory management per government IT standards

**Implementatie Notities:**
- Beveiliging: Ensure cached services don't leak memory
- Privacy: No user data in cached services
- Prestaties: Target < 100ms service access time
- Technical: Use `@st.cache_resource` decorator

**Code References:**
- Files affected: `src/services/container.py`, `src/main.py`
- Key functions: `get_service_container()`, ServiceContainer initialization

### Story 7.2: Prompt Token Optimization 🆕
**Status:** TODO
**Prioriteit:** HOOG
**Assigned:** Development Team
**Afhankelijkheden:** Story 7.3
**Target:** < 5s definition generation response time

**Gebruikersverhaal:**
As a product owner
I want to minimize OpenAI API token usage
So that operational costs are reduced while maintaining quality

**Acceptatiecriteria:**
1. Gegeven validation rules are needed in prompts
   Wanneer prompt is constructed
   Dan only relevant rules are included (not all 45)
2. Gegeven prompts are generated multiple times
   Wanneer same context is used
   Dan cached prompts are reused
3. Gegeven token usage is measured
   Wanneer optimizations are applied
   Dan 50% reduction in tokens is achieved

**Domeinregels:**
- Maintain ASTRA quality standards for prompts
- Follow NORA guidelines for resource optimization
- Ensure prompt quality per justice domain vereistes

**Implementatie Notities:**
- Beveiliging: No sensitive data in cached prompts
- Privacy: Comply with AVG/GDPR in prompt content
- Prestaties: Target < 3,000 tokens per request
- Technical: Implement prompt template caching

**Code References:**
- Files affected: `src/services/prompt_service_v2.py`, `src/services/validation/modular_validation_service.py`
- Key functions: `build_prompt()`, `get_relevant_rules()`

### Story 7.3: Validation Rules Caching 🆕
**Status:** TODO
**Prioriteit:** HOOG
**Assigned:** Development Team
**Afhankelijkheden:** None

**Gebruikersverhaal:**
As a developer
I want validation rules loaded once per session
So that validation performance is optimal

**Acceptatiecriteria:**
1. Gegeven validation rules are needed
   Wanneer first accessed in a session
   Dan rules are loaded and cached
2. Gegeven cached rules exist
   Wanneer subsequent validations occur
   Dan cached rules are used without file I/O
3. Gegeven rules are modified (development)
   Wanneer cache refresh is triggered
   Dan new rules are loaded

**Domeinregels:**
- Comply with ASTRA architecture patterns for caching
- Follow NORA guidelines for data consistency
- Ensure rule integrity per justice domain standards

**Implementatie Notities:**
- Beveiliging: Validate rule integrity on load
- Privacy: No PII in validation rules
- Prestaties: Target < 10ms rule access time
- Technical: Use `@st.cache_data` with TTL

**Code References:**
- Files affected: `src/toetsregels/rule_loader.py`, `src/services/validation/modular_validation_service.py`
- Key functions: `load_validation_rules()`, `get_cached_rules()`

### Story 7.4: ServiceContainer Circular Dependency Resolution 🆕
**Status:** TODO
**Prioriteit:** GEMIDDELD
**Assigned:** Architecture Team
**Afhankelijkheden:** None

**Gebruikersverhaal:**
As a developer
I want clean afhankelijkheid injection without circular references
So that the codebase is maintainable and testable

**Acceptatiecriteria:**
1. Gegeven ServiceContainer afhankelijkheden
   Wanneer analyzed with afhankelijkheid tools
   Dan no circular references are detected
2. Gegeven services are initialized
   Wanneer afhankelijkheid graph is created
   Dan it forms a DAG (Directed Acyclic Graph)
3. Gegeven unit tests are written
   Wanneer mocking services
   Dan no circular afhankelijkheid issues occur

**Domeinregels:**
- Follow ASTRA architectural principles for loose coupling
- Implement NORA standard afhankelijkheid patterns
- Ensure testability per government IT guidelines

**Implementatie Notities:**
- Beveiliging: No security impact
- Privacy: No privacy impact
- Prestaties: Improved initialization time
- Technical: Refactor to lazy loading or factory pattern

**Code References:**
- Files affected: `src/services/container.py`, all service files
- Key functions: ServiceContainer constructor, service getters

### Story 7.5: Context Window Optimization
**Status:** TODO
**Prioriteit:** GEMIDDELD
**Afhankelijkheden:** Story 7.2

**Gebruikersverhaal:**
As a user
I want fast definition generation
So that I can work efficiently without delays

**Acceptatiecriteria:**
1. Gegeven a definition request
   Wanneer context is prepared
   Dan only essential information is included
2. Gegeven context window limits
   Wanneer approaching limits
   Dan graceful degradation occurs

### Related Vereisten
- REQ-019: Context Flow Integration (PER-007)
- REQ-031: Validation Result Caching
- REQ-035: Validation Prestaties Monitoring
- REQ-036: Context-Aware Validation
- REQ-041: Database Connection Management
- REQ-046: Monitoring and Metrics Collection
- REQ-058: Logging Configuration System
- REQ-060: Health Check Endpoints
- REQ-061: Graceful Degradation
- REQ-062: Circuit Breaker Pattern
- REQ-064: Scheduled Maintenance Mode
- REQ-065: Database Migration System
- REQ-066: Configuration Hot-reload
- REQ-067: Service Monitoring Dashboard
- REQ-070: Prestaties Testen
- REQ-073: Continuous Integration Testen
- REQ-077: Test Reporting and Analytics

---

## Episch Verhaal 8: Web Lookup Module
**Status:** MERGED
**Note:** This epic has been merged with Episch Verhaal 3. No separate stories.

---

## Episch Verhaal 9: Advanced Features
**Status:** ❌ TODO (5% Complete)
**Prioriteit:** LAAG (Post-UAT)
**Bedrijfswaarde:** Advanced capabilities for power users

### Wachtende Verhalen
- Story 9.1: Multi-definition batch processing
- Story 9.2: Versie control integration
- Story 9.3: Collaborative editing
- Story 9.4: FastAPI REST endpoints 🆕 (for external integrations)
- Story 9.5: PostgreSQL migration 🆕 (for multi-user support)
- Story 9.6: Multi-tenant architecture 🆕 (for organizational isolation)

### Related Vereisten
- REQ-034: Custom Rule Configuration
- REQ-037: Batch Validation Processing
- REQ-080: Data Versioning System
- REQ-085: PostgreSQL Migration
- REQ-086: Multi-tenant Data Isolation
- REQ-087: Data Analytics and Reporting

---

## Story Status Legend

- **TODO**: Not started
- **IN_PROGRESS**: Currently being worked on
- **DONE**: Completed and verified
- **BLOCKED**: Cannot proceed due to afhankelijkheden
- 🆕 Newly added story

## Prioriteit Levels

- **KRITIEK**: Beveiliging or compliance issues, must fix immediately
- **HOOG**: Core functionality or significant performance impact
- **GEMIDDELD**: Important but not blocking
- **LAAG**: Nice to have, can be deferred

## Implementatie Werkstroom

1. Story selected from this document
2. Technical design created (if HOOG or KRITIEK priority)
3. TDD approach: tests written first
4. Implementatie following acceptatiecriteria
5. Code review against domain rules
6. Story marked DONE after verification

## Compliance References

### ASTRA Guidelines
- Architecture patterns: https://www.noraonline.nl/wiki/ASTRA
- Service design principles for justice domain
- Integration standards for chain systems

### NORA Framework
- Government-wide architecture standards
- Beveiliging and privacy vereistes
- Prestaties benchmarks

### Justice Domain Standards
- Justid identity management specifications
- OM/DJI/Rechtspraak integration vereistes
- AVG/GDPR compliance for justice systems

## Metrics & Tracking

### Current Sprint Focus (Week 36, 2025)
- Story 7.1: Service Initialization Caching (HOOG) - Prestaties < 5s target
- Story 7.2: Prompt Token Optimization (HOOG) - Reduce from 7,250 to < 3,000 tokens
- Story 7.3: Validation Rules Caching (HOOG) - Eliminate 45x rule reloads
- Story 4.1: UI Tab Activation (GEMIDDELD) - Complete remaining 7 tabs
- Story CFR.1: Fix Context Field Mapping (KRITIEK) - Context not reaching prompts

### Velocity Metrics
- Average story points per sprint: 15
- Critical bug fix SLA: 24 hours
- High priority story SLA: 1 week

### Project Status Summary (04-09-2025)
- **Episch Verhaal 1 (Basis Generatie):** 100% Complete ✅
- **Episch Verhaal 2 (Kwaliteitstoetsing):** 100% Complete ✅ (45/45 rules active)
- **Episch Verhaal 3 (Web Lookup):** 30% Complete 🔄
- **Episch Verhaal 4 (User Interface):** 30% Complete 🔄 (3/10 tabs functional)
- **Episch Verhaal 5 (Export/Import):** 10% Complete ❌
- **Episch Verhaal 6 (Beveiliging):** 40% Complete 🔄 (API keys secured)
- **Episch Verhaal 7 (Prestaties):** 35% Complete 🔄 (V2-only active)
- **Episch Verhaal 8 (Web Lookup):** Merged with Episch Verhaal 3
- **Episch Verhaal 9 (Advanced):** 5% Complete ❌
- **Episch Verhaal CFR (Context Flow):** 0% Complete 🚨 (KRITIEK BUGS)

## Notes for Developers

1. **Always reference story IDs** in commits and PRs
2. **Update story status** immediately after completion
3. **Document deviations** from acceptatiecriteria
4. **Add code references** to completed stories
5. **Follow TDD** for all HOOG/KRITIEK stories

## Episch Verhaal CFR: Context Flow Refactoring
**Status:** 🚨 KRITIEK (0% Complete)
**Prioriteit:** KRITIEK
**Bedrijfswaarde:** Ensures legal definitions have complete context information for compliance
**Risk:** HOOG - Context fields are currently NOT passed to prompts, causing non-compliant definitions

### Context
The current system has critical bugs in context field handling that prevent legal professionals from creating compliant definitions. Context fields (juridische_context, wettelijke_basis, organisatorische_context) are collected in the UI but not properly passed through to the AI prompts, resulting in definitions that lack required legal and organizational context.

### Critical Issues Identified
1. **Context Field Mapping Failure**: UI collects context but it's not passed to prompts
2. **"Anders..." Option Crashes**: Custom context entry causes validation errors
3. **Multiple Legacy Routes**: Inconsistent data flow paths cause unpredictable behavior
4. **Type Confusion**: String vs List handling throughout the system
5. **Missing ASTRA Compliance**: No traceability for context usage

### Business Impact
- **Legal Risk**: Definitions lack required juridical context for justice sector use
- **User Frustration**: System crashes when using custom context options
- **Compliance Failure**: Cannot demonstrate ASTRA/NORA compliance without context traceability
- **Quality Issues**: Generated definitions miss critical organizational and legal frameworks

### Story CFR.1: Fix Context Field Mapping to Prompts
**Status:** TODO
**Prioriteit:** KRITIEK
**Assigned:** Development Team
**Afhankelijkheden:** None

**Gebruikersverhaal:**
As a legal professional
I want all three context types included in my definition prompts
So that generated definitions have complete legal and organizational context

**Acceptatiecriteria:**
1. Gegeven a user selects organisatorische_context values in the UI
   Wanneer the definition is generated
   Dan the organisatorische_context appears in the AI prompt
2. Gegeven a user selects juridische_context values in the UI
   Wanneer the definition is generated
   Dan the juridische_context appears in the AI prompt
3. Gegeven a user selects wettelijke_basis values in the UI
   Wanneer the definition is generated
   Dan the wettelijke_basis appears in the AI prompt
4. Gegeven all three context types are selected
   Wanneer viewing the debug prompt
   Dan all context values are visible in the constructed prompt
5. Gegeven context values are passed to the prompt
   Wanneer the prompt is logged
   Dan context appears in the structured sections of the prompt

**Domeinregels:**
- All justice definitions MUST include organizational context (ASTRA vereiste)
- Legal basis MUST be traceable to specific laws (NORA compliance)
- Juridical context MUST align with Dutch legal system categories
- Context terminology MUST match Justid standards

**Implementatie Notities:**
- Beveiliging: No sensitive case data in context fields
- Privacy: Context fields must not contain PII
- Prestaties: Context should add < 100 tokens to prompt
- Location: Fix in `src/services/prompts/prompt_service_v2.py` lines 158-176

**Root Cause Analysis:**
- The `_convert_request_to_context` method creates `base_context` but doesn't properly map UI fields
- Context fields are available in `request` but not extracted correctly
- The prompt builder receives empty context arrays

**Code References:**
- Files affected:
  - `src/services/prompts/prompt_service_v2.py`
  - `src/ui/tabbed_interface.py`
  - `src/services/definition_generator_context.py`
- Key functions:
  - `PromptServiceV2._convert_request_to_context()`
  - `TabbedInterface._handle_definition_generation()`
  - `EnrichedContext` initialization

### Story CFR.2: Fix "Anders..." Custom Context Option
**Status:** TODO
**Prioriteit:** KRITIEK
**Assigned:** Development Team
**Afhankelijkheden:** None

**Gebruikersverhaal:**
As a legal professional
I want to enter custom context values not in the predefined lists
So that I can handle special cases and emerging legal frameworks

**Acceptatiecriteria:**
1. Gegeven a user selects "Anders..." in organisatorische_context
   Wanneer they enter custom text and generate
   Dan the system processes without errors
2. Gegeven a user selects "Anders..." in juridische_context
   Wanneer they enter custom text and generate
   Dan the custom value is included in the prompt
3. Gegeven a user selects "Anders..." in wettelijke_basis
   Wanneer they enter custom text and generate
   Dan the custom legal reference appears in the definition
4. Gegeven "Anders..." is selected without entering custom text
   Wanneer generating a definition
   Dan the system handles gracefully without crashes
5. Gegeven multiple "Anders..." entries across different context types
   Wanneer all are filled with custom values
   Dan all custom values are processed correctly

**Domeinregels:**
- Custom entries must follow justice domain naming conventions
- Custom legal references must be validated for format
- Custom organizations must be logged for ASTRA compliance
- System must track usage of custom values for reporting

**Implementatie Notities:**
- Beveiliging: Sanitize custom input to prevent injection
- Privacy: Log custom entries without user association
- Prestaties: Validate custom entries client-side first
- Bug: "The default value 'test' is not part of the options" error

**Root Cause Analysis:**
- The multiselect widget crashes when the final list differs from options
- "Anders..." is removed from the list but widget still references it
- Default values contain items not in the processed options list

**Code References:**
- Files affected:
  - `src/ui/components/context_selector.py` lines 137-183
  - `src/ui/tabbed_interface.py` context collection methods
- Key functions:
  - `ContextSelector._render_manual_selector()`
  - Context list processing logic

### Story CFR.3: Remove Legacy Context Routes
**Status:** TODO
**Prioriteit:** HOOG
**Assigned:** Architecture Team
**Afhankelijkheden:** CFR.1, CFR.2

**Gebruikersverhaal:**
As a developer
I want a single, clear path for context data flow
So that the system behavior is predictable and maintainable

**Acceptatiecriteria:**
1. Gegeven the codebase is analyzed
   Wanneer tracing context data flow
   Dan only one path exists from UI to prompt
2. Gegeven legacy context fields exist
   Wanneer they are identified
   Dan they are marked deprecated with migration path
3. Gegeven the refactored context flow
   Wanneer all tests are run
   Dan no legacy route tests fail
4. Gegeven context data is processed
   Wanneer debugging the flow
   Dan a single, traceable path is visible
5. Gegeven the migration is complete
   Wanneer generating definitions
   Dan all context types work consistently

**Domeinregels:**
- Maintain backward compatibility for 1 release cycle
- Document migration path for existing integrations
- Ensure ASTRA architecture patterns are followed
- Create ADR (Architecture Decision Record) for changes

**Implementatie Notities:**
- Beveiliging: Remove unused code paths to reduce attack surface
- Privacy: Ensure no context leaks through legacy routes
- Prestaties: Single path should improve response time
- Technical: Use feature flags for gradual rollout

**Legacy Routes Identified:**
1. Direct `context` field (string) - DEPRECATED
2. `domein` field separate from context - DEPRECATED
3. V1 orchestrator context passing - REMOVED
4. Session state context storage - REFACTOR
5. Multiple context_dict creation points - CONSOLIDATE

**Code References:**
- Files affected:
  - `src/orchestration/` (V1 orchestrator removal)
  - `src/services/interfaces.py` (GenerationRequest)
  - `src/ui/session_state.py` (context storage)
  - All files with `context` or `domein` fields
- Key functions:
  - Legacy context conversion functions
  - V1 to V2 migration helpers

### Story CFR.4: Implement Context Type Validation
**Status:** TODO
**Prioriteit:** HOOG
**Assigned:** Development Team
**Afhankelijkheden:** CFR.1

**Gebruikersverhaal:**
As a system administrator
I want context fields validated for correct types
So that type errors don't cause runtime failures

**Acceptatiecriteria:**
1. Gegeven context data is received from UI
   Wanneer it's processed for prompt generation
   Dan type validation ensures all fields are lists
2. Gegeven a string is passed where a list is expected
   Wanneer validation occurs
   Dan it's automatically converted to a single-item list
3. Gegeven invalid context data types
   Wanneer validation fails
   Dan clear error messages guide correction
4. Gegeven context validation is geïmplementeerd
   Wanneer performance is measured
   Dan validation adds < 10ms to request time
5. Gegeven validation errors occur
   Wanneer they are logged
   Dan sufficient detail exists for debugging

**Domeinregels:**
- All context fields MUST be lists of strings
- Empty lists are valid (no context selected)
- Null/undefined converts to empty list
- Validation must follow NORA data quality standards

**Implementatie Notities:**
- Beveiliging: Prevent type confusion attacks
- Privacy: Don't log actual context values in errors
- Prestaties: Use Pydantic for fast validation
- Location: Add validation layer before prompt building

**Code References:**
- Files affected:
  - `src/services/interfaces.py` (add validation)
  - `src/services/validation/context_validator.py` (NEW)
  - `src/services/prompts/prompt_service_v2.py`
- Key functions:
  - Create `ContextValidator` class
  - Add `validate_context_types()` method

### Story CFR.5: Add Context Traceability for ASTRA Compliance
**Status:** TODO
**Prioriteit:** HOOG
**Assigned:** Development Team
**Afhankelijkheden:** CFR.1, CFR.3

**Gebruikersverhaal:**
As a compliance officer
I want full traceability of context usage in definitions
So that I can demonstrate ASTRA compliance in audits

**Acceptatiecriteria:**
1. Gegeven a definition is generated
   Wanneer it's saved to the database
   Dan all context values are stored in metadata
2. Gegeven context is used in generation
   Wanneer the audit log is reviewed
   Dan context selection is traceable to the user session
3. Gegeven a definition is exported
   Wanneer compliance report is generated
   Dan context chain-of-custody is documented
4. Gegeven ASTRA audit vereistes
   Wanneer context traceability is tested
   Dan all required fields are captured
5. Gegeven context changes during regeneration
   Wanneer the history is viewed
   Dan all context versions are retained

**Domeinregels:**
- ASTRA requires full context attribution
- Context must link to authoritative sources
- Audit trail must be immutable
- Retention period: 7 years (justice vereiste)

**Implementatie Notities:**
- Beveiliging: Encrypt context in audit logs
- Privacy: Separate context from user PII
- Prestaties: Async audit logging
- Database: Add context_audit table

**Code References:**
- Files affected:
  - `src/database/schema.sql` (add audit table)
  - `src/services/audit_service.py` (NEW)
  - `src/database/definitie_repository.py`
- Key functions:
  - Create `AuditService.log_context_usage()`
  - Extend `save_definition()` with context metadata

### Story CFR.6: Create End-to-End Context Flow Tests
**Status:** TODO
**Prioriteit:** HOOG
**Assigned:** Test Team
**Afhankelijkheden:** CFR.1, CFR.2, CFR.4

**Gebruikersverhaal:**
As a QA engineer
I want comprehensive tests for the entire context flow
So that context handling issues are caught before production

**Acceptatiecriteria:**
1. Gegeven the test suite runs
   Wanneer all context scenarios are tested
   Dan 100% of context paths have coverage
2. Gegeven "Anders..." option tests
   Wanneer edge cases are tested
   Dan no crashes occur in any scenario
3. Gegeven integration tests run
   Wanneer context flows through all layers
   Dan values match at each checkpoint
4. Gegeven regression tests exist
   Wanneer CFR bugs are fixed
   Dan tests prevent reintroduction
5. Gegeven performance tests run
   Wanneer context is processed
   Dan response time remains under SLA

**Domeinregels:**
- Tests must cover all justice domain contexts
- Test data must use realistic legal scenarios
- Tests must validate ASTRA compliance
- Coverage vereiste: >90% for context code

**Implementatie Notities:**
- Use pytest for unit tests
- Use Streamlit testing for UI tests
- Create fixtures for common context scenarios
- Add performance benchmarks

**Test Scenarios:**
1. All three context types selected
2. Only one context type selected
3. No context selected
4. "Anders..." in each context type
5. Mixed predefined and custom values
6. Context with special characters
7. Very long context lists
8. Context type mismatches

**Code References:**
- Files affected:
  - `tests/services/test_context_flow.py` (NEW)
  - `tests/ui/test_context_selector.py` (NEW)
  - `tests/integration/test_context_e2e.py` (NEW)
- Key functions:
  - `test_context_mapping_to_prompt()`
  - `test_anders_option_handling()`
  - `test_context_type_validation()`

### Bug Report: CFR-BUG-001 - Context Fields Not Passed to Prompts

**Severity:** KRITIEK
**Status:** OPEN
**Reported:** 04-09-2025
**Affected Versie:** Current Production

**Description:**
Context fields (juridische_context, wettelijke_basis, organisatorische_context) collected in the UI are not being passed through to the AI prompt generation, resulting in definitions that lack critical legal and organizational context required for justice sector compliance.

**Steps to Reproduce:**
1. Open the Definition Generator
2. Enter a term (e.g., "voorlopige hechtenis")
3. Select multiple values in all three context fields
4. Generate definition
5. Check debug prompt output
6. Observe: Context fields are empty or missing in prompt

**Expected Behavior:**
All selected context values should appear in the structured prompt sent to the AI.

**Actual Behavior:**
Context fields are collected but not included in the prompt, causing the AI to generate generic definitions without justice-specific context.

**Root Cause:**
The `_convert_request_to_context` method in `prompt_service_v2.py` creates the context structure but doesn't properly extract values from the request object's context fields.

**Impact:**
- Definitions lack legal authority references
- Cannot comply with ASTRA vereistes
- Users must manually add context to definitions
- Reduces automation value of the system

### Bug Report: CFR-BUG-002 - "Anders..." Option Causes Validation Error

**Severity:** KRITIEK
**Status:** OPEN
**Reported:** 04-09-2025
**Affected Versie:** Current Production

**Description:**
Selecting "Anders..." option and entering custom text causes the application to crash with error: "The default value 'test' is not part of the options".

**Steps to Reproduce:**
1. Open Definition Generator
2. In any context field, select "Anders..."
3. Enter custom text in the input field
4. Try to proceed with generation
5. Observe: Application crashes with validation error

**Expected Behavior:**
Custom text should be accepted and processed as part of the context.

**Actual Behavior:**
Streamlit multiselect widget crashes because the processed list (without "Anders...") doesn't match the widget's option list.

**Root Cause:**
"Anders..." is removed from the selection list after processing but the widget still references it, causing a mismatch between options and values.

**Workaround:**
None currently available - users cannot use custom context values.

**Impact:**
- Cannot handle special legal frameworks
- Cannot add emerging organizations
- Limits system flexibility
- Causes user frustration and support tickets

### Success Metrics

1. **Context Completeness**
   - Target: 100% of context fields passed to prompts
   - Measurement: Audit log analysis of prompt content
   - Baseline: Currently 0% (fields not passed)

2. **System Stability**
   - Target: 0 crashes from context selection
   - Measurement: Error tracking system
   - Baseline: ~15 crashes/day from "Anders..." option

3. **ASTRA Compliance Score**
   - Target: 100% context traceability
   - Measurement: Compliance audit tool
   - Baseline: 0% (no traceability currently)

4. **User Satisfaction**
   - Target: >90% satisfaction with context handling
   - Measurement: User feedback surveys
   - Baseline: ~40% (many complaints about missing context)

5. **Prestaties Impact**
   - Target: <100ms added by context processing
   - Measurement: APM tools
   - Baseline: N/A (context not processed)

### Definition of Done (DoD)

✅ **Code Complete**
- [ ] All context fields properly mapped from UI to prompts
- [ ] "Anders..." option works without errors
- [ ] Legacy routes removed or deprecated
- [ ] Type validation geïmplementeerd
- [ ] Context traceability added

✅ **Testen Complete**
- [ ] Unit tests written and passing (>90% coverage)
- [ ] Integration tests cover all context flows
- [ ] E2E tests validate user scenarios
- [ ] Prestaties tests confirm SLA compliance
- [ ] Regression tests prevent bug reintroduction

✅ **Documentation Complete**
- [ ] Technical documentation updated
- [ ] API documentation reflects changes
- [ ] Migration guide for legacy routes
- [ ] ASTRA compliance report generated
- [ ] ADR created for architecture changes

✅ **Quality Gates Passed**
- [ ] Code review completed by senior developer
- [ ] Beveiliging review passed (no injection vulnerabilities)
- [ ] Prestaties benchmarks met (<100ms impact)
- [ ] Accessibility vereistes validated
- [ ] No critical or high severity bugs

✅ **Compliance Verified**
- [ ] ASTRA vereistes checklist completed
- [ ] NORA standards validated
- [ ] Justice domain expert approval received
- [ ] Privacy impact assessment completed
- [ ] Audit trail tested and verified

✅ **Uitrol Ready**
- [ ] Feature flags configured for gradual rollout
- [ ] Rollback plan documented and tested
- [ ] Monitoring alerts configured
- [ ] Support team trained on changes
- [ ] User communication prepared

### Implementatie Prioriteit & Phases

**Phase 1: Critical Fixes (Week 1)**
- CFR.1: Fix context field mapping
- CFR.2: Fix "Anders..." crashes
- CFR-BUG-001 & 002 resolution

**Phase 2: Stabilization (Week 2)**
- CFR.4: Type validation
- CFR.6: E2E tests
- Prestaties optimization

**Phase 3: Cleanup & Compliance (Week 3)**
- CFR.3: Remove legacy routes
- CFR.5: Add traceability
- Documentation updates
- Compliance validation

### Risk Mitigation

1. **Risk**: Breaking existing integrations
   - **Mitigation**: Feature flags for gradual rollout
   - **Contingency**: Maintain legacy routes for 1 release

2. **Risk**: Prestaties degradation
   - **Mitigation**: Prestaties tests in each phase
   - **Contingency**: Caching strategy for context data

3. **Risk**: User confusion during transition
   - **Mitigation**: Clear communication and training
   - **Contingency**: Dual-mode operation period

4. **Risk**: Compliance audit failure
   - **Mitigation**: Early compliance validation
   - **Contingency**: Fast-track compliance fixes

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 04-09-2025 | Business Analyst | Initial document creation with Episch Verhaal 6 & 7 performance stories |
| 04-09-2025 | Business Analyst | Added Episch Verhaal CFR (Context Flow Refactoring) with 6 critical user stories and bug reports |
| 04-09-2025 | Developer Agent | Updated completion status: V2-only architecture complete, AI config system active, 45/45 validation rules working, security fixes geïmplementeerd |

---

*This document is maintained by the Business Analyst Agent and serves as the authoritative source for all development work. Any questions about vereistes should reference specific story IDs from this document.*
