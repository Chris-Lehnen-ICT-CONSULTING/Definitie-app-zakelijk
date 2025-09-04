---
canonical: true
status: active
owner: architecture
last_verified: 2025-09-04
document_type: action-plan
priority: high
---

# Architecture Documentation Update Plan
**UAT Deadline**: September 20, 2025
**Review Date**: September 4, 2025

## Immediate Actions Required (This Week)

### 1. Document Consolidation
**Responsible**: Architecture Team
**Deadline**: September 6, 2025

#### Actions:
```bash
# Archive redundant documents
mv docs/architectuur/EA.md docs/archief/EA_prompt_system_concept.md
mv docs/architectuur/SA.md docs/archief/SA_specific_improvements.md

# Keep as primary documents
# - docs/architectuur/ENTERPRISE_ARCHITECTURE.md (main EA)
# - docs/architectuur/SOLUTION_ARCHITECTURE.md (main SA)
```

### 2. Create Actual Technical Architecture
**File**: `/docs/architectuur/TA_CURRENT.md`
**Deadline**: September 7, 2025

```markdown
# Technical Architecture - DefinitieAgent (Current State)

## Technology Stack
- **Frontend**: Streamlit 1.32+
- **Backend**: Python 3.11
- **Database**: SQLite (data/definities.db)
- **AI Integration**: OpenAI API (GPT-4)
- **Deployment**: Local/Single-server
- **No caching layer currently**
- **No container orchestration**

## Service Architecture
- ServiceContainer (DI pattern)
- ValidationOrchestratorV2
- ModularValidationService (45 rules)
- DefinitionOrchestratorV2
- ModernWebLookupService

## Deployment Model
- Single-user desktop application
- No authentication required (MVP)
- Local file storage
- Direct API calls to OpenAI
```

### 3. Add Justice Sector Context
**Update**: `ENTERPRISE_ARCHITECTURE.md`
**Deadline**: September 8, 2025

Add new section:
```markdown
## Justice Chain Integration

### Stakeholders
- **OM (Openbaar Ministerie)**:
  - Requirements: Strafrechtelijke definities
  - Integration: Future API voor zaaksystemen

- **DJI (Dienst Justitiële Inrichtingen)**:
  - Requirements: Detentie-gerelateerde begrippen
  - Integration: TULP-koppeling (toekomst)

- **Rechtspraak**:
  - Requirements: Juridische terminologie validatie
  - Integration: MijnRechtspraak portaal (toekomst)

### ASTRA Compliance
- Begrippenkader alignment
- Metadata standaarden voor juridische content
- Versiebeheer voor wettelijke definities
```

## Short-term Actions (Next 2 Weeks)

### 4. Create Compliance Matrix
**File**: `/docs/architectuur/COMPLIANCE_MATRIX.md`
**Deadline**: September 14, 2025

| Standard | Requirement | Current State | Target | Priority | Action |
|----------|------------|---------------|--------|----------|--------|
| **NORA** |
| P01 | Proactief | Partial | Full | High | Implement predictive features |
| P02 | Vindbaar | Missing | API | Medium | Add discovery API |
| P03 | Toegankelijk | Missing | WCAG 2.1 | High | Accessibility audit |
| **BIO** |
| Auth | Authentication | None | OIDC | Low* | After multi-user |
| Encrypt | Data at rest | None | AES-256 | Medium | Migrate to PostgreSQL |
| Audit | Logging | Basic | Structured | High | Implement structured logging |
| **ASTRA** |
| Meta | Legal metadata | None | ECLI/BWB | Medium | Add metadata fields |
| Integration | Chain systems | None | API | Low | Future phase |

*Low priority due to single-user MVP status

### 5. Update Solution Architecture
**File**: `SOLUTION_ARCHITECTURE.md`
**Deadline**: September 15, 2025

Updates needed:
- Remove unrealistic microservices timeline
- Document actual service boundaries
- Add realistic migration path
- Update component diagram to reflect current state

### 6. Security Architecture Documentation
**File**: `/docs/architectuur/SECURITY_ARCHITECTURE.md`
**Deadline**: September 18, 2025

Content:
- Current security posture (single-user)
- Risk assessment
- Migration path to multi-user
- BIO compliance roadmap
- Threat model (when relevant)

## Architecture Documentation Standards

### 1. Frontmatter Requirements
All architecture documents MUST include:
```yaml
---
canonical: true
status: active|draft|deprecated
owner: architecture|development|business
last_verified: YYYY-MM-DD
applies_to: definitie-app@version
---
```

### 2. Document Structure
Each architecture document follows:
1. Executive Summary
2. Context & Scope
3. Architecture Decisions (link to ADRs)
4. Components/Design
5. Standards & Compliance
6. Risks & Mitigations
7. References

### 3. Naming Conventions
- EA documents: `ENTERPRISE_ARCHITECTURE.md`
- SA documents: `SOLUTION_ARCHITECTURE.md`
- TA documents: `TECHNICAL_ARCHITECTURE.md`
- ADRs: `ADR-XXX-description.md`

### 4. Version Control
- Major updates increment version
- Track changes in document
- Archive old versions in `/docs/archief/`

## Success Criteria

### Week 1 (Sept 9)
- [ ] Documents consolidated
- [ ] Current TA documented
- [ ] Justice context added
- [ ] Compliance matrix created

### Week 2 (Sept 16)
- [ ] SA updated to reality
- [ ] Security architecture documented
- [ ] Standards compliance tracked
- [ ] ADRs current

### UAT Ready (Sept 20)
- [ ] All architecture aligned with implementation
- [ ] Justice requirements documented
- [ ] Compliance gaps identified and planned
- [ ] Clear roadmap to production

## Review Process

1. **Daily Check**: Update progress in this document
2. **Week 1 Review**: September 9 - Document consolidation complete
3. **Week 2 Review**: September 16 - All updates complete
4. **UAT Checkpoint**: September 19 - Final review before UAT

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| UAT deadline missed | High | Focus on critical docs only |
| Standards non-compliance | Medium | Document gaps, plan post-UAT |
| Resource constraints | High | Prioritize by business value |
| Stakeholder alignment | Medium | Early review with OM/DJI |

## Contact Points

- **Architecture**: architecture@definitie-app.nl
- **Development**: dev-team@definitie-app.nl
- **OM Liaison**: [Contact needed]
- **DJI Representative**: [Contact needed]
- **Rechtspraak**: [Contact needed]

## Next Steps After Plan Completion

1. Implement monitoring architecture
2. Design API layer
3. Plan PostgreSQL migration
4. Develop integration strategy
5. Create production deployment architecture

---
*This plan is living document - update progress daily*
