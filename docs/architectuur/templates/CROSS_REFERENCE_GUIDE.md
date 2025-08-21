# Cross-Reference Guide: EA ↔ SA

## Overview
Deze guide definieert hoe Enterprise Architecture (EA) en Solution Architecture (SA) documenten naar elkaar verwijzen en elkaar aanvullen zonder duplicatie.

## Reference Notation Standard

### Format
```
→ [Document Type] Section X.X: [Section Name]
Example: → EA Section 3.1: Application Portfolio
```

### Link Types
- **→** Direct reference (must read)
- **↗** Related information (optional)
- **⇄** Bidirectional dependency
- **◉** Source of truth

## Cross-Reference Matrix

### From EA to SA

| EA Section | References SA | Type | Purpose |
|------------|--------------|------|---------|
| 3.1 Application Portfolio | SA 1.1: Component Architecture | → | Technical details of applications |
| 4.1 Technology Standards | SA 2.1: Technology Stack | ◉ | SA must comply with EA standards |
| 5.1 Security Framework | SA 4: Security Implementation | → | How security policies are implemented |
| 6.2 Principles | SA 1.3: Development Architecture | → | How principles are applied |
| 7.1 Strategic Roadmap | SA 7: Migration Strategy | → | Technical execution of roadmap |

### From SA to EA

| SA Section | References EA | Type | Purpose |
|------------|--------------|------|---------|
| Executive Summary | EA 1: Business Architecture | → | Business context and drivers |
| 2.1 Technology Stack | EA 4.1: Technology Standards | ⇄ | Compliance with standards |
| 4.3 Cryptography | EA 5: Security Architecture | → | Security requirements |
| 10: Cost Optimization | EA 7.2: Investment Portfolio | ↗ | Alignment with investment strategy |
| 11: ADRs | EA 6.1: Architecture Governance | → | Governance process |

## Content Ownership Rules

### Enterprise Architecture Owns:
```yaml
Business:
  - Business capabilities
  - Value streams
  - Business services
  - Strategic KPIs

Information:
  - Enterprise data model
  - Data governance
  - Master data management

Standards:
  - Technology standards
  - Security policies
  - Compliance requirements
  - Architecture principles

Portfolio:
  - Application portfolio
  - Investment decisions
  - Strategic roadmap
```

### Solution Architecture Owns:
```yaml
Technical:
  - Component design
  - API specifications
  - Database schemas
  - Code organization

Implementation:
  - Technology selection (within standards)
  - Design patterns
  - Integration patterns
  - Performance optimization

Operations:
  - Deployment architecture
  - Monitoring setup
  - CI/CD pipelines
  - Runbooks
```

## Reference Examples

### Example 1: Security
```markdown
# In EA Document:
## 5.1 Security Framework
The organization adopts a Zero Trust security model with the following principles:
- Never trust, always verify
- Least privilege access
- Assume breach

For technical implementation details → SA Section 4: Security Implementation

# In SA Document:
## 4. Security Implementation
This section implements the Zero Trust model defined in → EA Section 5.1: Security Framework

### 4.1 Authentication & Authorization
Implementation uses OAuth 2.0 with PKCE flow...
```

### Example 2: Technology Standards
```markdown
# In EA Document:
## 4.1 Technology Standards
Approved technology stack:
- Frontend: React 18+
- Backend: Python 3.11+ with FastAPI
- Database: PostgreSQL 14+

# In SA Document:
## 2.1 Technology Stack
Following → EA Section 4.1: Technology Standards, this solution uses:
- Frontend: React 18.2.0 (latest approved version)
- Backend: Python 3.11.5 with FastAPI 0.104.1
- Database: PostgreSQL 14.9
```

## Anti-Patterns to Avoid

### ❌ Don't Duplicate Content
```markdown
# Wrong - Same content in both docs:
EA: "The system must support 1000 concurrent users"
SA: "The system must support 1000 concurrent users"

# Right - Reference from source:
EA: "Performance requirement: 1000 concurrent users"
SA: "To meet the 1000 concurrent user requirement (→ EA Section X.X)..."
```

### ❌ Don't Mix Abstraction Levels
```markdown
# Wrong - Technical details in EA:
EA: "Use Redis with 10GB memory allocation"

# Right - Policy in EA, implementation in SA:
EA: "Caching strategy required for performance"
SA: "Implements caching (→ EA requirement) using Redis with 10GB allocation"
```

### ❌ Don't Create Circular Dependencies
```markdown
# Wrong:
EA: "See SA for business drivers" → SA: "See EA for business context"

# Right:
EA: "Business drivers: [defines here]"
SA: "Addresses business drivers from → EA Section 1.3"
```

## Maintenance Guidelines

### When Updating EA:
1. Check if referenced SA sections need updates
2. Verify technology standards still current
3. Update roadmap based on SA progress
4. Review and update cross-references

### When Updating SA:
1. Verify compliance with EA standards
2. Check if EA principles still applied correctly
3. Update technical details without changing EA refs
4. Validate all EA cross-references work

## Validation Checklist

### Monthly Review:
- [ ] All cross-references resolve correctly
- [ ] No duplicate content between documents
- [ ] Abstraction levels maintained
- [ ] New sections have appropriate references
- [ ] Deprecated sections removed from both

### Quarterly Review:
- [ ] EA/SA alignment on standards
- [ ] Roadmap progress reflected
- [ ] Investment tracking accurate
- [ ] Governance process followed

## Tools and Automation

### Reference Validator Script
```python
# validate_references.py
def validate_references():
    """
    Checks:
    1. All → references exist in target document
    2. No circular dependencies
    3. No duplicate content
    4. Correct abstraction levels
    """
    pass
```

### Auto-Generate Reference Index
```python
# generate_index.py
def generate_reference_index():
    """
    Creates:
    1. List of all cross-references
    2. Dependency graph
    3. Orphaned sections report
    """
    pass
```

## Templates for Common References

### Business Context Reference
```markdown
For business drivers and strategic context → EA Section 1: Business Architecture
```

### Technical Standards Reference
```markdown
This implementation complies with technology standards defined in → EA Section 4.1
```

### Security Requirements Reference
```markdown
Security controls implement requirements from → EA Section 5: Security Architecture
```

### Cost/Investment Reference
```markdown
Cost optimization aligns with investment strategy in → EA Section 7.2
```
