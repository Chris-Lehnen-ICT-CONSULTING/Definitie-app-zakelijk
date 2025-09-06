# MASTER EPICS AND USER STORIES

> ⚠️ **DEPRECATED DOCUMENT** ⚠️
>
> **Status:** DEPRECATED as of 2025-09-05
> **Reason:** Migrated to modern file-per-epic/story structure
>
> ## New Structure
>
> This document has been replaced by individual epic and story files:
>
> - **Epics:** See `/docs/epics/` directory
>   - Dashboard: [/docs/epics/INDEX.md](../epics/INDEX.md)
>   - Files: EPIC-001.md through EPIC-CFR.md
>
> - **Stories:** See `/docs/stories/` directory
>   - Index: [/docs/stories/INDEX.md](INDEX.md)
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
> - Migration Date: 2025-09-05
> - Migrated By: Business Analyst Agent
> - Archive Location: `/docs/archief/2025-09-epic-migration/`
> - Original preserved at: `MASTER-EPICS-USER-STORIES-20250905.md`
>
> ---
>
> ⬇️ **Original content preserved below for reference** ⬇️

---

# MASTER EPICS AND USER STORIES (ARCHIVED)

**Document Type:** Master Story Registry
**Version:** 1.0.0
**Status:** DEPRECATED
**Owner:** Business Analyst
**Last Updated:** 2025-09-04
**Applies To:** Historical reference only

## Document Purpose

This WAS the SINGLE SOURCE OF TRUTH for all epics and user stories in the DefinitieAgent project. It has been replaced by the new structure described above.

## Quick Navigation

- [Epic 1: Basis Definitie Generatie](#epic-1-basis-definitie-generatie)
- [Epic 2: Kwaliteitstoetsing](#epic-2-kwaliteitstoetsing)
- [Epic 3: Content Verrijking / Web Lookup](#epic-3-content-verrijking--web-lookup)
- [Epic 4: User Interface](#epic-4-user-interface)
- [Epic 5: Export & Import](#epic-5-export--import)
- [Epic 6: Security & Auth](#epic-6-security--auth)
- [Epic 7: Performance & Scaling](#epic-7-performance--scaling)
- [Epic 8: Web Lookup Module (Merged with Epic 3)](#epic-8-web-lookup-module)
- [Epic 9: Advanced Features](#epic-9-advanced-features)

---

## Epic 1: Basis Definitie Generatie
**Status:** ✅ DONE (100% Complete)
**Priority:** HIGH
**Business Value:** Core functionality for legal definition generation

### Completed Stories
- Story 1.1: Basic definition generation via GPT-4 ✅
- Story 1.2: Prompt template system ✅
- Story 1.3: V1 orchestrator elimination ✅ (V2-only architecture fully implemented)
- Story 1.4: AI Configuration System via ConfigManager ✅ (component-specific config active)
- Story 1.5: Centralized AI model configuration ✅ (no more hardcoded defaults)

### Related Requirements
- REQ-018: Core Definition Generation
- REQ-038: OpenAI GPT-4 Integration
- REQ-059: Environment-based Configuration
- REQ-078: Data Model Definition
- REQ-079: Data Validation and Integrity
- REQ-082: Data Search and Indexing

---

## Epic 2: Kwaliteitstoetsing
**Status:** ✅ DONE (100% Complete)
**Priority:** HIGH
**Business Value:** Quality assurance through validation rules

### Completed Stories
- Story 2.1: Validation interface design ✅
- Story 2.2: Core implementation ✅
- Story 2.3: Container wiring ✅
- Story 2.4: Integration migration ✅
- Story 2.5: Testing & QA ✅
- Story 2.6: Production rollout ✅
- Story 2.7: All 45/45 validation rules active and working ✅
- Story 2.8: Modular validation service fully operational ✅

### Related Requirements
- REQ-016: Nederlandse Juridische Terminologie
- REQ-017: 45 Validatieregels
- REQ-023: ARAI Validation Rules Implementation
- REQ-024: CON Validation Rules Implementation
- REQ-025: ESS Validation Rules Implementation
- REQ-026: INT Validation Rules Implementation
- REQ-027: SAM Validation Rules Implementation
- REQ-028: STR Validation Rules Implementation
- REQ-029: VER Validation Rules Implementation
- REQ-030: Rule Priority System
- REQ-032: Validation Orchestration Flow
- REQ-033: Rule Conflict Resolution
- REQ-034: Custom Rule Configuration
- REQ-068: Unit Test Coverage
- REQ-069: Integration Testing
- REQ-072: Test Data Management
- REQ-074: Test Automation Framework
- REQ-076: Regression Test Suite

---

## Epic 3: Content Verrijking / Web Lookup
**Status:** 🔄 IN_PROGRESS (30% Complete)
**Priority:** HIGH
**Business Value:** External source integration for definition enrichment

### Story 3.1: Modern Web Lookup Implementation
**Status:** TODO
**Priority:** HIGH
**Dependencies:** None

**User Story:**
As a legal definition author
I want to enrich definitions with external sources
So that definitions have authoritative references and context

**Acceptance Criteria:**
1. Given a definition request
   When external lookup is enabled
   Then Wikipedia and SRU sources are consulted
2. Given external content is retrieved
   When processing for inclusion
   Then content is validated and properly attributed

**Domain Rules:**
- All external content must include source attribution
- Content must align with ASTRA/NORA data quality standards
- Privacy-sensitive information must be filtered

**Implementation Notes:**
- Security: Sanitize all external content (XSS prevention)
- Privacy: No PII in external lookups
- Performance: Cache external results for 15 minutes

### Related Requirements
- REQ-017: 45 Validatieregels
- REQ-020: Validation Orchestrator V2
- REQ-039: Wikipedia API Integration
- REQ-040: SRU (Search/Retrieve via URL) Integration

---

## Epic 4: User Interface
**Status:** 🔄 IN_PROGRESS (30% Complete)
**Priority:** MEDIUM
**Business Value:** User experience and productivity

### Completed Stories
- Story 4.4: Basic tab structure implemented ✅
- Story 4.5: Definition generation UI functional ✅
- Story 4.6: Validation results display working ✅

### Pending Stories
- Story 4.1: Tab activation (7/10 tabs still needed: Voorbeelden, Grammatica, etc.) ⏳
- Story 4.2: UI performance optimization (target < 200ms response) ⏳
- Story 4.3: Responsive design implementation ⏳

### Related Requirements
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
- REQ-075: User Acceptance Testing

---

## Epic 5: Export & Import
**Status:** ❌ TODO (10% Complete)
**Priority:** LOW
**Business Value:** Data portability and integration

### Pending Stories
- Story 5.1: Export formats (JSON, PDF, DOCX)
- Story 5.2: Import validation
- Story 5.3: Batch operations

### Related Requirements
- REQ-022: Export Functionality
- REQ-042: Export to Multiple Formats
- REQ-043: Import from External Sources
- REQ-083: Data Export Formats
- REQ-084: Data Import Validation

---

## Epic 6: Security & Auth
**Status:** 🔄 IN_PROGRESS (40% Complete)
**Priority:** CRITICAL
**Business Value:** Security compliance and data protection

### Completed Stories
- Story 6.2: API Key Security Fix ✅ (removed exposed keys from config)
- Story 6.3: Environment variable configuration ✅ (all keys via env vars)
- Story 6.4: Component-specific AI configuration security ✅

### Story 6.1: API Key Validation at Startup 🆕
**Status:** TODO
**Priority:** HIGH
**Assigned:** Development Team
**Dependencies:** None

**User Story:**
As a system administrator
I want API keys validated at application startup
So that configuration errors are caught early and don't cause runtime failures

**Acceptance Criteria:**
1. Given the application starts
   When OpenAI API key is configured
   Then the key is validated via test API call
2. Given an invalid API key is detected
   When application initialization occurs
   Then clear error message is shown and startup is halted
3. Given a valid API key
   When application starts
   Then initialization continues normally

**Domain Rules:**
- Comply with NORA security guidelines for credential management
- Follow ASTRA patterns for configuration validation
- No sensitive data in error messages or logs

**Implementation Notes:**
- Security: Never log full API keys (only last 4 chars)
- Privacy: No API key in error tracking
- Performance: Validation timeout of 5 seconds
- Location: Add to `src/services/container.py` initialization

**Code References:**
- Files affected: `src/services/container.py`, `src/services/ai_service_v2.py`
- Key functions: `ServiceContainer.__init__()`, `AIServiceV2.validate_api_key()`

### Related Requirements
- REQ-044: Justice SSO Integration
- REQ-045: Audit Logging System
- REQ-047: Backup and Restore Functionality
- REQ-063: Rate Limiting Per User
- REQ-071: Security Testing
- REQ-081: Data Archival Strategy

---

## Epic 7: Performance & Scaling
**Status:** 🔄 IN_PROGRESS (35% Complete)
**Priority:** HIGH
**Business Value:** System efficiency and cost optimization

### Completed Stories
- Story 7.6: V1 to V2 migration completed ✅ (no more dual systems)
- Story 7.7: Service container optimization started ✅

### Story 7.1: Service Initialization Caching 🆕
**Status:** TODO
**Priority:** HIGH
**Assigned:** Development Team
**Dependencies:** None

**User Story:**
As a developer
I want service initialization to happen only once
So that application startup is fast and memory efficient

**Acceptance Criteria:**
1. Given Streamlit reruns occur
   When ServiceContainer is accessed
   Then the same singleton instance is returned
2. Given the application starts
   When ServiceContainer initializes
   Then it happens exactly once per session
3. Given cached services are accessed
   When multiple UI components request them
   Then no re-initialization occurs

**Domain Rules:**
- Follow NORA performance guidelines (response < 200ms)
- Implement according to ASTRA caching patterns
- Memory management per government IT standards

**Implementation Notes:**
- Security: Ensure cached services don't leak memory
- Privacy: No user data in cached services
- Performance: Target < 100ms service access time
- Technical: Use `@st.cache_resource` decorator

**Code References:**
- Files affected: `src/services/container.py`, `src/main.py`
- Key functions: `get_service_container()`, ServiceContainer initialization

### Story 7.2: Prompt Token Optimization 🆕
**Status:** TODO
**Priority:** HIGH
**Assigned:** Development Team
**Dependencies:** Story 7.3
**Target:** < 5s definition generation response time

**User Story:**
As a product owner
I want to minimize OpenAI API token usage
So that operational costs are reduced while maintaining quality

**Acceptance Criteria:**
1. Given validation rules are needed in prompts
   When prompt is constructed
   Then only relevant rules are included (not all 45)
2. Given prompts are generated multiple times
   When same context is used
   Then cached prompts are reused
3. Given token usage is measured
   When optimizations are applied
   Then 50% reduction in tokens is achieved

**Domain Rules:**
- Maintain ASTRA quality standards for prompts
- Follow NORA guidelines for resource optimization
- Ensure prompt quality per justice domain requirements

**Implementation Notes:**
- Security: No sensitive data in cached prompts
- Privacy: Comply with AVG/GDPR in prompt content
- Performance: Target < 3,000 tokens per request
- Technical: Implement prompt template caching

**Code References:**
- Files affected: `src/services/prompt_service_v2.py`, `src/services/validation/modular_validation_service.py`
- Key functions: `build_prompt()`, `get_relevant_rules()`

### Story 7.3: Validation Rules Caching 🆕
**Status:** TODO
**Priority:** HIGH
**Assigned:** Development Team
**Dependencies:** None

**User Story:**
As a developer
I want validation rules loaded once per session
So that validation performance is optimal

**Acceptance Criteria:**
1. Given validation rules are needed
   When first accessed in a session
   Then rules are loaded and cached
2. Given cached rules exist
   When subsequent validations occur
   Then cached rules are used without file I/O
3. Given rules are modified (development)
   When cache refresh is triggered
   Then new rules are loaded

**Domain Rules:**
- Comply with ASTRA architecture patterns for caching
- Follow NORA guidelines for data consistency
- Ensure rule integrity per justice domain standards

**Implementation Notes:**
- Security: Validate rule integrity on load
- Privacy: No PII in validation rules
- Performance: Target < 10ms rule access time
- Technical: Use `@st.cache_data` with TTL

**Code References:**
- Files affected: `src/toetsregels/rule_loader.py`, `src/services/validation/modular_validation_service.py`
- Key functions: `load_validation_rules()`, `get_cached_rules()`

### Story 7.4: ServiceContainer Circular Dependency Resolution 🆕
**Status:** TODO
**Priority:** MEDIUM
**Assigned:** Architecture Team
**Dependencies:** None

**User Story:**
As a developer
I want clean dependency injection without circular references
So that the codebase is maintainable and testable

**Acceptance Criteria:**
1. Given ServiceContainer dependencies
   When analyzed with dependency tools
   Then no circular references are detected
2. Given services are initialized
   When dependency graph is created
   Then it forms a DAG (Directed Acyclic Graph)
3. Given unit tests are written
   When mocking services
   Then no circular dependency issues occur

**Domain Rules:**
- Follow ASTRA architectural principles for loose coupling
- Implement NORA standard dependency patterns
- Ensure testability per government IT guidelines

**Implementation Notes:**
- Security: No security impact
- Privacy: No privacy impact
- Performance: Improved initialization time
- Technical: Refactor to lazy loading or factory pattern

**Code References:**
- Files affected: `src/services/container.py`, all service files
- Key functions: ServiceContainer constructor, service getters

### Story 7.5: Context Window Optimization
**Status:** TODO
**Priority:** MEDIUM
**Dependencies:** Story 7.2

**User Story:**
As a user
I want fast definition generation
So that I can work efficiently without delays

**Acceptance Criteria:**
1. Given a definition request
   When context is prepared
   Then only essential information is included
2. Given context window limits
   When approaching limits
   Then graceful degradation occurs

### Related Requirements
- REQ-019: Context Flow Integration (PER-007)
- REQ-031: Validation Result Caching
- REQ-035: Validation Performance Monitoring
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
- REQ-070: Performance Testing
- REQ-073: Continuous Integration Testing
- REQ-077: Test Reporting and Analytics

---

## Epic 8: Web Lookup Module
**Status:** MERGED
**Note:** This epic has been merged with Epic 3. No separate stories.

---

## Epic 9: Advanced Features
**Status:** ❌ TODO (5% Complete)
**Priority:** LOW (Post-UAT)
**Business Value:** Advanced capabilities for power users

### Pending Stories
- Story 9.1: Multi-definition batch processing
- Story 9.2: Version control integration
- Story 9.3: Collaborative editing
- Story 9.4: FastAPI REST endpoints 🆕 (for external integrations)
- Story 9.5: PostgreSQL migration 🆕 (for multi-user support)
- Story 9.6: Multi-tenant architecture 🆕 (for organizational isolation)

### Related Requirements
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
- **BLOCKED**: Cannot proceed due to dependencies
- 🆕 Newly added story

## Priority Levels

- **CRITICAL**: Security or compliance issues, must fix immediately
- **HIGH**: Core functionality or significant performance impact
- **MEDIUM**: Important but not blocking
- **LOW**: Nice to have, can be deferred

## Implementation Workflow

1. Story selected from this document
2. Technical design created (if HIGH or CRITICAL priority)
3. TDD approach: tests written first
4. Implementation following acceptance criteria
5. Code review against domain rules
6. Story marked DONE after verification

## Compliance References

### ASTRA Guidelines
- Architecture patterns: https://www.noraonline.nl/wiki/ASTRA
- Service design principles for justice domain
- Integration standards for chain systems

### NORA Framework
- Government-wide architecture standards
- Security and privacy requirements
- Performance benchmarks

### Justice Domain Standards
- Justid identity management specifications
- OM/DJI/Rechtspraak integration requirements
- AVG/GDPR compliance for justice systems

## Metrics & Tracking

### Current Sprint Focus (Week 36, 2025)
- Story 7.1: Service Initialization Caching (HIGH) - Performance < 5s target
- Story 7.2: Prompt Token Optimization (HIGH) - Reduce from 7,250 to < 3,000 tokens
- Story 7.3: Validation Rules Caching (HIGH) - Eliminate 45x rule reloads
- Story 4.1: UI Tab Activation (MEDIUM) - Complete remaining 7 tabs
- Story CFR.1: Fix Context Field Mapping (CRITICAL) - Context not reaching prompts

### Velocity Metrics
- Average story points per sprint: 15
- Critical bug fix SLA: 24 hours
- High priority story SLA: 1 week

### Project Status Summary (2025-09-04)
- **Epic 1 (Basis Generatie):** 100% Complete ✅
- **Epic 2 (Kwaliteitstoetsing):** 100% Complete ✅ (45/45 rules active)
- **Epic 3 (Web Lookup):** 30% Complete 🔄
- **Epic 4 (User Interface):** 30% Complete 🔄 (3/10 tabs functional)
- **Epic 5 (Export/Import):** 10% Complete ❌
- **Epic 6 (Security):** 40% Complete 🔄 (API keys secured)
- **Epic 7 (Performance):** 35% Complete 🔄 (V2-only active)
- **Epic 8 (Web Lookup):** Merged with Epic 3
- **Epic 9 (Advanced):** 5% Complete ❌
- **Epic CFR (Context Flow):** 0% Complete 🚨 (CRITICAL BUGS)

## Notes for Developers

1. **Always reference story IDs** in commits and PRs
2. **Update story status** immediately after completion
3. **Document deviations** from acceptance criteria
4. **Add code references** to completed stories
5. **Follow TDD** for all HIGH/CRITICAL stories

## Epic CFR: Context Flow Refactoring
**Status:** 🚨 CRITICAL (0% Complete)
**Priority:** CRITICAL
**Business Value:** Ensures legal definitions have complete context information for compliance
**Risk:** HIGH - Context fields are currently NOT passed to prompts, causing non-compliant definitions

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
**Priority:** CRITICAL
**Assigned:** Development Team
**Dependencies:** None

**User Story:**
As a legal professional
I want all three context types included in my definition prompts
So that generated definitions have complete legal and organizational context

**Acceptance Criteria:**
1. Given a user selects organisatorische_context values in the UI
   When the definition is generated
   Then the organisatorische_context appears in the AI prompt
2. Given a user selects juridische_context values in the UI
   When the definition is generated
   Then the juridische_context appears in the AI prompt
3. Given a user selects wettelijke_basis values in the UI
   When the definition is generated
   Then the wettelijke_basis appears in the AI prompt
4. Given all three context types are selected
   When viewing the debug prompt
   Then all context values are visible in the constructed prompt
5. Given context values are passed to the prompt
   When the prompt is logged
   Then context appears in the structured sections of the prompt

**Domain Rules:**
- All justice definitions MUST include organizational context (ASTRA requirement)
- Legal basis MUST be traceable to specific laws (NORA compliance)
- Juridical context MUST align with Dutch legal system categories
- Context terminology MUST match Justid standards

**Implementation Notes:**
- Security: No sensitive case data in context fields
- Privacy: Context fields must not contain PII
- Performance: Context should add < 100 tokens to prompt
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
**Priority:** CRITICAL
**Assigned:** Development Team
**Dependencies:** None

**User Story:**
As a legal professional
I want to enter custom context values not in the predefined lists
So that I can handle special cases and emerging legal frameworks

**Acceptance Criteria:**
1. Given a user selects "Anders..." in organisatorische_context
   When they enter custom text and generate
   Then the system processes without errors
2. Given a user selects "Anders..." in juridische_context
   When they enter custom text and generate
   Then the custom value is included in the prompt
3. Given a user selects "Anders..." in wettelijke_basis
   When they enter custom text and generate
   Then the custom legal reference appears in the definition
4. Given "Anders..." is selected without entering custom text
   When generating a definition
   Then the system handles gracefully without crashes
5. Given multiple "Anders..." entries across different context types
   When all are filled with custom values
   Then all custom values are processed correctly

**Domain Rules:**
- Custom entries must follow justice domain naming conventions
- Custom legal references must be validated for format
- Custom organizations must be logged for ASTRA compliance
- System must track usage of custom values for reporting

**Implementation Notes:**
- Security: Sanitize custom input to prevent injection
- Privacy: Log custom entries without user association
- Performance: Validate custom entries client-side first
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
**Priority:** HIGH
**Assigned:** Architecture Team
**Dependencies:** CFR.1, CFR.2

**User Story:**
As a developer
I want a single, clear path for context data flow
So that the system behavior is predictable and maintainable

**Acceptance Criteria:**
1. Given the codebase is analyzed
   When tracing context data flow
   Then only one path exists from UI to prompt
2. Given legacy context fields exist
   When they are identified
   Then they are marked deprecated with migration path
3. Given the refactored context flow
   When all tests are run
   Then no legacy route tests fail
4. Given context data is processed
   When debugging the flow
   Then a single, traceable path is visible
5. Given the migration is complete
   When generating definitions
   Then all context types work consistently

**Domain Rules:**
- Maintain backward compatibility for 1 release cycle
- Document migration path for existing integrations
- Ensure ASTRA architecture patterns are followed
- Create ADR (Architecture Decision Record) for changes

**Implementation Notes:**
- Security: Remove unused code paths to reduce attack surface
- Privacy: Ensure no context leaks through legacy routes
- Performance: Single path should improve response time
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
**Priority:** HIGH
**Assigned:** Development Team
**Dependencies:** CFR.1

**User Story:**
As a system administrator
I want context fields validated for correct types
So that type errors don't cause runtime failures

**Acceptance Criteria:**
1. Given context data is received from UI
   When it's processed for prompt generation
   Then type validation ensures all fields are lists
2. Given a string is passed where a list is expected
   When validation occurs
   Then it's automatically converted to a single-item list
3. Given invalid context data types
   When validation fails
   Then clear error messages guide correction
4. Given context validation is implemented
   When performance is measured
   Then validation adds < 10ms to request time
5. Given validation errors occur
   When they are logged
   Then sufficient detail exists for debugging

**Domain Rules:**
- All context fields MUST be lists of strings
- Empty lists are valid (no context selected)
- Null/undefined converts to empty list
- Validation must follow NORA data quality standards

**Implementation Notes:**
- Security: Prevent type confusion attacks
- Privacy: Don't log actual context values in errors
- Performance: Use Pydantic for fast validation
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
**Priority:** HIGH
**Assigned:** Development Team
**Dependencies:** CFR.1, CFR.3

**User Story:**
As a compliance officer
I want full traceability of context usage in definitions
So that I can demonstrate ASTRA compliance in audits

**Acceptance Criteria:**
1. Given a definition is generated
   When it's saved to the database
   Then all context values are stored in metadata
2. Given context is used in generation
   When the audit log is reviewed
   Then context selection is traceable to the user session
3. Given a definition is exported
   When compliance report is generated
   Then context chain-of-custody is documented
4. Given ASTRA audit requirements
   When context traceability is tested
   Then all required fields are captured
5. Given context changes during regeneration
   When the history is viewed
   Then all context versions are retained

**Domain Rules:**
- ASTRA requires full context attribution
- Context must link to authoritative sources
- Audit trail must be immutable
- Retention period: 7 years (justice requirement)

**Implementation Notes:**
- Security: Encrypt context in audit logs
- Privacy: Separate context from user PII
- Performance: Async audit logging
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
**Priority:** HIGH
**Assigned:** Test Team
**Dependencies:** CFR.1, CFR.2, CFR.4

**User Story:**
As a QA engineer
I want comprehensive tests for the entire context flow
So that context handling issues are caught before production

**Acceptance Criteria:**
1. Given the test suite runs
   When all context scenarios are tested
   Then 100% of context paths have coverage
2. Given "Anders..." option tests
   When edge cases are tested
   Then no crashes occur in any scenario
3. Given integration tests run
   When context flows through all layers
   Then values match at each checkpoint
4. Given regression tests exist
   When CFR bugs are fixed
   Then tests prevent reintroduction
5. Given performance tests run
   When context is processed
   Then response time remains under SLA

**Domain Rules:**
- Tests must cover all justice domain contexts
- Test data must use realistic legal scenarios
- Tests must validate ASTRA compliance
- Coverage requirement: >90% for context code

**Implementation Notes:**
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

**Severity:** CRITICAL
**Status:** OPEN
**Reported:** 2025-09-04
**Affected Version:** Current Production

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
- Cannot comply with ASTRA requirements
- Users must manually add context to definitions
- Reduces automation value of the system

### Bug Report: CFR-BUG-002 - "Anders..." Option Causes Validation Error

**Severity:** CRITICAL
**Status:** OPEN
**Reported:** 2025-09-04
**Affected Version:** Current Production

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

5. **Performance Impact**
   - Target: <100ms added by context processing
   - Measurement: APM tools
   - Baseline: N/A (context not processed)

### Definition of Done (DoD)

✅ **Code Complete**
- [ ] All context fields properly mapped from UI to prompts
- [ ] "Anders..." option works without errors
- [ ] Legacy routes removed or deprecated
- [ ] Type validation implemented
- [ ] Context traceability added

✅ **Testing Complete**
- [ ] Unit tests written and passing (>90% coverage)
- [ ] Integration tests cover all context flows
- [ ] E2E tests validate user scenarios
- [ ] Performance tests confirm SLA compliance
- [ ] Regression tests prevent bug reintroduction

✅ **Documentation Complete**
- [ ] Technical documentation updated
- [ ] API documentation reflects changes
- [ ] Migration guide for legacy routes
- [ ] ASTRA compliance report generated
- [ ] ADR created for architecture changes

✅ **Quality Gates Passed**
- [ ] Code review completed by senior developer
- [ ] Security review passed (no injection vulnerabilities)
- [ ] Performance benchmarks met (<100ms impact)
- [ ] Accessibility requirements validated
- [ ] No critical or high severity bugs

✅ **Compliance Verified**
- [ ] ASTRA requirements checklist completed
- [ ] NORA standards validated
- [ ] Justice domain expert approval received
- [ ] Privacy impact assessment completed
- [ ] Audit trail tested and verified

✅ **Deployment Ready**
- [ ] Feature flags configured for gradual rollout
- [ ] Rollback plan documented and tested
- [ ] Monitoring alerts configured
- [ ] Support team trained on changes
- [ ] User communication prepared

### Implementation Priority & Phases

**Phase 1: Critical Fixes (Week 1)**
- CFR.1: Fix context field mapping
- CFR.2: Fix "Anders..." crashes
- CFR-BUG-001 & 002 resolution

**Phase 2: Stabilization (Week 2)**
- CFR.4: Type validation
- CFR.6: E2E tests
- Performance optimization

**Phase 3: Cleanup & Compliance (Week 3)**
- CFR.3: Remove legacy routes
- CFR.5: Add traceability
- Documentation updates
- Compliance validation

### Risk Mitigation

1. **Risk**: Breaking existing integrations
   - **Mitigation**: Feature flags for gradual rollout
   - **Contingency**: Maintain legacy routes for 1 release

2. **Risk**: Performance degradation
   - **Mitigation**: Performance tests in each phase
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
| 2025-09-04 | Business Analyst | Initial document creation with Epic 6 & 7 performance stories |
| 2025-09-04 | Business Analyst | Added Epic CFR (Context Flow Refactoring) with 6 critical user stories and bug reports |
| 2025-09-04 | Developer Agent | Updated completion status: V2-only architecture complete, AI config system active, 45/45 validation rules working, security fixes implemented |

---

*This document is maintained by the Business Analyst Agent and serves as the authoritative source for all development work. Any questions about requirements should reference specific story IDs from this document.*
