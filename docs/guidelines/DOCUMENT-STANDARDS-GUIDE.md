---
canonical: true
status: active
owner: doc-standards-guardian
last_verified: 2025-09-05
applies_to: architecture-consolidation@v1
---

# Document Standards Guide for Architecture Consolidation

## Executive Summary

This guide defines the authoritative standards for the DefinitieApp architecture consolidation from 47 documents to 3 canonical documents. It ensures consistency, ASTRA/NORA compliance, and maintainability while preserving all critical information.

## 1. Canonical Document Structure

### 1.1 Three-Tier Architecture Documentation

```
docs/architectuur/
├── ENTERPRISE_ARCHITECTURE.md (EA - Business/Organisational View)
├── SOLUTION_ARCHITECTURE.md   (SA - Solution Design & Integration)
└── TECHNICAL_ARCHITECTURE.md   (TA - Technical Implementation)
```

### 1.2 Maximum Document Size
- **Hard limit**: 3000 lines per document
- **Target**: 1500-2000 lines for optimal readability
- **Header depth**: Maximum 3 levels (###) for main content
- **Exception**: Level 4 (####) allowed for technical specifications only

### 1.3 Document Hierarchy

```yaml
ENTERPRISE_ARCHITECTURE.md:
  focus: Business capabilities, stakeholders, compliance
  audience: Management, Business Analysts, Compliance Officers
  max_technical_depth: High-level only

SOLUTION_ARCHITECTURE.md:
  focus: Solution design, integration patterns, data flow
  audience: Solution Architects, Technical Leads, DevOps
  max_technical_depth: Design patterns and contracts

TECHNICAL_ARCHITECTURE.md:
  focus: Implementation details, code structure, deployment
  audience: Developers, DevOps Engineers, SREs
  max_technical_depth: Full implementation details
```

## 2. Frontmatter Requirements

### 2.1 Mandatory Frontmatter Fields

Every canonical document MUST include:

```yaml
---
canonical: true                           # Always true for EA/SA/TA
status: active                            # active|draft|archived
owner: architecture                       # Responsible team
last_verified: YYYY-MM-DD                # Last content verification
applies_to: definitie-app@v2             # Application version
compliance:
  astra: true|false                      # ASTRA compliance
  nora: true|false                       # NORA compliance
  bio: true|false                        # BIO compliance
  gemma: true|false                      # GEMMA compliance
version_history:
  current: "2.0.0"                       # Document version
  previous: "1.x.x"                      # Previous version
  migration_date: "YYYY-MM-DD"          # Migration completion
cross_references:
  ea: "ENTERPRISE_ARCHITECTURE.md"      # EA document
  sa: "SOLUTION_ARCHITECTURE.md"        # SA document
  ta: "TECHNICAL_ARCHITECTURE.md"       # TA document
---
```

### 2.2 Optional Frontmatter Fields

```yaml
---
review_cycle: quarterly|monthly           # Review frequency
next_review: YYYY-MM-DD                  # Next scheduled review
stakeholders:
  - role: owner
    contact: team-email@justice.nl
  - role: reviewer
    contact: architect@justice.nl
dependencies:
  - "docs/requirements/REQUIREMENTS.md"
  - "docs/testing/TEST_STRATEGY.md"
supersedes:
  - "docs/archief/OLD_EA.md"
  - "docs/archief/OLD_SA.md"
---
```

## 3. Section Structure Standards

### 3.1 Enterprise Architecture Sections

```markdown
# ENTERPRISE_ARCHITECTURE

## 1. Executive Summary
### 1.1 Management Samenvatting
### 1.2 Key Decisions
### 1.3 Compliance Status

## 2. Business Context
### 2.1 Organisational Context
### 2.2 Stakeholder Analysis
### 2.3 Business Capabilities

## 3. Strategic Alignment
### 3.1 ASTRA Principles
### 3.2 NORA Requirements
### 3.3 Justice Chain Integration

## 4. Information Architecture
### 4.1 Domain Model
### 4.2 Information Flows
### 4.3 Data Governance

## 5. Application Architecture
### 5.1 Application Landscape
### 5.2 Integration Points
### 5.3 Service Portfolio

## 6. Governance & Compliance
### 6.1 Architecture Governance
### 6.2 Compliance Matrix
### 6.3 Risk Management

## 7. Roadmap & Evolution
### 7.1 Current State
### 7.2 Future State
### 7.3 Migration Strategy

## 8. References
```

### 3.2 Solution Architecture Sections

```markdown
# SOLUTION_ARCHITECTURE

## 1. Executive Summary
### 1.1 Solution Overview
### 1.2 Key Design Decisions
### 1.3 Integration Strategy

## 2. Solution Context
### 2.1 Problem Statement
### 2.2 Solution Scope
### 2.3 Constraints & Assumptions

## 3. Functional Architecture
### 3.1 Functional Decomposition
### 3.2 Service Design
### 3.3 Process Flows

## 4. Data Architecture
### 4.1 Data Model
### 4.2 Data Flow Design
### 4.3 Data Quality & Validation

## 5. Integration Architecture
### 5.1 Integration Patterns
### 5.2 API Contracts
### 5.3 Event Architecture

## 6. Security Architecture
### 6.1 Security Zones
### 6.2 Authentication & Authorization
### 6.3 Data Protection

## 7. Quality Attributes
### 7.1 Performance Requirements
### 7.2 Scalability Design
### 7.3 Reliability Patterns

## 8. Deployment Architecture
### 8.1 Deployment Model
### 8.2 Environment Strategy
### 8.3 Release Management

## 9. References
```

### 3.3 Technical Architecture Sections

```markdown
# TECHNICAL_ARCHITECTURE

## 1. Executive Summary
### 1.1 Technical Overview
### 1.2 Technology Stack
### 1.3 Implementation Approach

## 2. Technical Context
### 2.1 Technical Requirements
### 2.2 Technical Constraints
### 2.3 Technology Decisions

## 3. Component Architecture
### 3.1 Component Model
### 3.2 Service Implementation
### 3.3 Module Structure

## 4. Data Implementation
### 4.1 Database Design
### 4.2 Data Access Layer
### 4.3 Caching Strategy

## 5. Infrastructure Architecture
### 5.1 Infrastructure Components
### 5.2 Network Architecture
### 5.3 Storage Architecture

## 6. Development Architecture
### 6.1 Development Standards
### 6.2 Build & CI/CD
### 6.3 Testing Strategy

## 7. Operations Architecture
### 7.1 Monitoring & Logging
### 7.2 Backup & Recovery
### 7.3 Maintenance Procedures

## 8. Implementation Guidelines
### 8.1 Coding Standards
### 8.2 Configuration Management
### 8.3 Dependency Management

## 9. References
```

## 4. Naming Conventions

### 4.1 File Naming
- **Canonical documents**: `UPPERCASE_WITH_UNDERSCORES.md`
- **Supporting documents**: `lowercase-with-hyphens.md`
- **Archive documents**: `YYYY-MM-DD-original-name.md`
- **Version suffix**: Never use version numbers in filenames (use frontmatter)

### 4.2 Section Headers
```markdown
# DOCUMENT TITLE (All caps, document level)
## 1. Major Section (Numbered, Title Case)
### 1.1 Subsection (Numbered, Title Case)
#### Technical Detail (Only in TA, Sentence case)
```

### 4.3 Code Block Labeling
```markdown
```language:component/module
# Code here
```

Example:
```python:services/validation_orchestrator
class ValidationOrchestrator:
    pass
```

### 4.4 Diagram Naming
- Format: `{type}-{component}-{detail}.{ext}`
- Examples:
  - `sequence-validation-flow.mermaid`
  - `class-domain-model.puml`
  - `deployment-production-setup.drawio`

### 4.5 Reference Links
```markdown
Internal: [Component Name](../category/document.md#section)
External: [ASTRA Guidelines](https://astra.justice.nl)
Cross-ref: See [SA § 3.2](SOLUTION_ARCHITECTURE.md#32-service-design)
```

## 5. Content Standards

### 5.1 Language Usage
- **Headers & Structure**: English
- **Technical Content**: English
- **Business Context**: Dutch (Nederlands)
- **Legal/Domain Terms**: Dutch with English translation
  - Example: "toetsregels (validation rules)"

### 5.2 Compliance Sections

Every canonical document MUST include:

```markdown
## Compliance Matrix

| Standard | Requirement | Status | Evidence | Reference |
|----------|------------|--------|----------|-----------|
| ASTRA-01 | Traceability | ✅ COMPLIANT | All decisions tracked in canonical docs | See EA/SA/TA documents |
| NORA-AP03 | Proactief | ✅ COMPLIANT | Validation prevents errors | [SA § 4.3](#43-validation) |
| BIO-14.2.1 | Logging | ⚠️ PARTIAL | Audit logging implemented | [TA § 7.1](#71-monitoring) |
| GEMMA-2.0 | Services | ❌ TODO | Service registry pending | [Roadmap](#roadmap) |
```

### 5.3 Version Control in Content

```markdown
## Version-Specific Information

> **Version 2.0.0 Changes**
> - Consolidated from 47 documents
> - Added PER-007 context flow fixes
> - Removed V1 orchestrator references

> **Migration Note**
> For pre-2.0 documentation, see `/docs/archief/2025-09-architectuur-consolidatie/`
```

### 5.4 Cross-Reference Format

```markdown
## Related Documentation

- **Enterprise View**: See [EA § 2.1](ENTERPRISE_ARCHITECTURE.md#21-organisational-context)
- **Implementation**: See [TA § 3.1](TECHNICAL_ARCHITECTURE.md#31-component-model)
- **Testing**: See [Test Strategy](../testing/TEST_STRATEGY.md)
- **Requirements**: See [US-001](../stories/MASTER-EPICS-USER-STORIES.md#us-001)
```

## 6. Validation Rules

### 6.1 Document Validation Checklist

- [ ] Frontmatter complete and valid
- [ ] All sections present per template
- [ ] Maximum 3000 lines
- [ ] No broken internal links
- [ ] Compliance matrix included
- [ ] Cross-references to other canonical docs
- [ ] Version history documented
- [ ] Owner and review date current
- [ ] No duplicate content across EA/SA/TA
- [ ] All code blocks have language specified

### 6.2 Content Quality Checks

- [ ] No conflicting requirements
- [ ] Consistent terminology usage
- [ ] All acronyms defined on first use
- [ ] Domain terms include Dutch original
- [ ] Technical depth appropriate for document type
- [ ] Examples provided for complex concepts
- [ ] Diagrams have source files referenced
- [ ] External links verified active
- [ ] Security-sensitive info redacted
- [ ] Performance metrics quantified

## 7. Archive Structure

### 7.1 Archive Organization

```
docs/archief/
├── 2025-09-architectuur-consolidatie/
│   ├── README.md (Migration summary)
│   ├── mapping.json (Old → New document mapping)
│   ├── original/ (Original 47 documents)
│   │   ├── 2025-09-05-EA.md
│   │   ├── 2025-09-05-SA.md
│   │   └── 2025-09-05-TA.md
│   └── migration-log.md (Detailed changes)
├── decisions/ (Superseded ADRs)
└── versions/ (Major version archives)
```

### 7.2 Archive Naming Convention

```
Format: YYYY-MM-DD-original-name.md
Example: 2025-09-05-enterprise-architecture-v1.md
```

### 7.3 Archive README Template

```markdown
# Architecture Consolidation Archive - September 2025

## Overview
This archive contains the 47 original architecture documents consolidated into 3 canonical documents.

## Migration Summary
- **Date**: 2025-09-05
- **Documents Consolidated**: 47
- **New Canonical Documents**: 3
- **Information Loss**: 0% (all content preserved)

## Mapping
| Original Document | New Location | Section |
|------------------|--------------|---------|
| EA.md | ENTERPRISE_ARCHITECTURE.md | All |
| prompt-management-ea.md | ENTERPRISE_ARCHITECTURE.md | § 5.2 |

## Access
These documents are retained for historical reference only.
For current architecture, see: `/docs/architectuur/`
```

## 8. Migration Guidelines

### 8.1 Content Migration Process

1. **Extract**: Pull content from source documents
2. **Categorize**: Sort into EA/SA/TA buckets
3. **Deduplicate**: Remove redundant content
4. **Reconcile**: Resolve conflicts using latest verified info
5. **Structure**: Fit into canonical sections
6. **Validate**: Run compliance checks
7. **Review**: Stakeholder approval
8. **Archive**: Move originals to archive

### 8.2 Conflict Resolution

When content conflicts exist:
1. Use most recent `last_verified` date
2. Prefer implemented over planned features
3. Choose more restrictive security requirements
4. Select higher performance targets
5. Document conflict in migration log

### 8.3 Information Preservation

- **Critical**: Must appear in canonical document
- **Important**: Include or reference
- **Historical**: Archive with reference
- **Obsolete**: Archive with deprecation note
- **Redundant**: Remove, note in migration log

## 9. Compliance Requirements

### 9.1 ASTRA Compliance

Every canonical document must address:
- Traceability (decisions → implementation)
- Interoperability (integration standards)
- Security by Design (security sections)
- Data Protection (privacy measures)

### 9.2 NORA Principles

Documents must demonstrate:
- Proactive service delivery
- Transparency in design decisions
- Reusability of components
- Vendor independence

### 9.3 BIO Security

Technical documents must include:
- Security zones definition
- Access control matrices
- Audit logging specifications
- Incident response procedures

### 9.4 GEMMA Standards

Solution documents must show:
- Service orientation
- Standardized interfaces
- Reference architecture alignment
- Common ground usage

## 10. Quality Gates

### 10.1 Pre-Migration Gate
- [ ] All source documents identified
- [ ] Stakeholders notified
- [ ] Backup created
- [ ] Conflicts documented

### 10.2 Migration Gate
- [ ] Content categorized correctly
- [ ] No information loss
- [ ] Conflicts resolved
- [ ] Structure validated

### 10.3 Post-Migration Gate
- [ ] Compliance validated
- [ ] Cross-references working
- [ ] Archive complete
- [ ] Stakeholder sign-off

### 10.4 Go-Live Gate
- [ ] INDEX.md updated
- [ ] CANONICAL_LOCATIONS.md updated
- [ ] CI/CD pipelines updated
- [ ] Team notified

## 11. Tooling & Automation

### 11.1 Validation Scripts
```bash
# Check document compliance
python scripts/validate_architecture_docs.py

# Verify cross-references
python scripts/check_references.py

# Generate compliance matrix
python scripts/generate_compliance_matrix.py
```

### 11.2 Migration Tools
```bash
# Archive documents
bash scripts/archive_documents.sh

# Update references
python scripts/update_references.py

# Generate migration report
python scripts/migration_report.py
```

## 12. References

### Internal Documents
- [DOCUMENTATION_POLICY.md](../DOCUMENTATION_POLICY.md)
- [CANONICAL_LOCATIONS.md](../CANONICAL_LOCATIONS.md)
- [INDEX.md](../INDEX.md)
- [MASTER-EPICS-USER-STORIES.md](../stories/MASTER-EPICS-USER-STORIES.md)

### External Standards
- [ASTRA Framework](https://astra.justice.nl)
- [NORA Principles](https://www.noraonline.nl)
- [BIO Standards](https://bio-overheid.nl)
- [GEMMA Architecture](https://gemmaonline.nl)

---

*This document is the authoritative guide for architecture documentation standards during consolidation.*
