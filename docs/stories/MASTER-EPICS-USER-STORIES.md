# MASTER EPICS AND USER STORIES

**Document Type:** Master Story Registry
**Version:** 1.0.0
**Status:** ACTIVE
**Owner:** Business Analyst
**Last Updated:** 2025-09-04
**Applies To:** All development work

## Document Purpose

This is the SINGLE SOURCE OF TRUTH for all epics and user stories in the DefinitieAgent project. All development work must reference stories from this document.

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
**Status:** ✅ DONE (90% Complete)
**Priority:** HIGH
**Business Value:** Core functionality for legal definition generation

### Completed Stories
- Story 1.1: Basic definition generation via GPT-4
- Story 1.2: Prompt template system
- Story 1.3: V1 orchestrator elimination

---

## Epic 2: Kwaliteitstoetsing
**Status:** ✅ DONE (85% Complete)
**Priority:** HIGH
**Business Value:** Quality assurance through validation rules

### Completed Stories
- Story 2.1: Validation interface design
- Story 2.2: Core implementation
- Story 2.3: Container wiring
- Story 2.4: Integration migration
- Story 2.5: Testing & QA
- Story 2.6: Production rollout

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

---

## Epic 4: User Interface
**Status:** ❌ TODO (30% Complete)
**Priority:** MEDIUM
**Business Value:** User experience and productivity

### Pending Stories
- Story 4.1: Tab activation (Voorbeelden, Grammatica, etc.)
- Story 4.2: UI performance optimization
- Story 4.3: Responsive design implementation

---

## Epic 5: Export & Import
**Status:** ❌ TODO (10% Complete)
**Priority:** LOW
**Business Value:** Data portability and integration

### Pending Stories
- Story 5.1: Export formats (JSON, PDF, DOCX)
- Story 5.2: Import validation
- Story 5.3: Batch operations

---

## Epic 6: Security & Auth
**Status:** 🚨 CRITICAL (0% Complete)
**Priority:** CRITICAL
**Business Value:** Security compliance and data protection

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

---

## Epic 7: Performance & Scaling
**Status:** 🔄 IN_PROGRESS (20% Complete)
**Priority:** HIGH
**Business Value:** System efficiency and cost optimization

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
- Story 7.1: Service Initialization Caching (HIGH)
- Story 7.2: Prompt Token Optimization (HIGH)
- Story 7.3: Validation Rules Caching (HIGH)

### Velocity Metrics
- Average story points per sprint: 15
- Critical bug fix SLA: 24 hours
- High priority story SLA: 1 week

## Notes for Developers

1. **Always reference story IDs** in commits and PRs
2. **Update story status** immediately after completion
3. **Document deviations** from acceptance criteria
4. **Add code references** to completed stories
5. **Follow TDD** for all HIGH/CRITICAL stories

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-09-04 | Business Analyst | Initial document creation with Epic 6 & 7 performance stories |

---

*This document is maintained by the Business Analyst Agent and serves as the authoritative source for all development work. Any questions about requirements should reference specific story IDs from this document.*
