---
aangemaakt: '08-09-2025'
applies_to: definitie-app@current
bijgewerkt: '08-09-2025'
canonical: true
last_verified: 04-09-2025
owner: architecture
prioriteit: medium
status: active
---



# Documentation Policy - DefinitieAgent

## Purpose

This policy establishes standards for documentation within the DefinitieAgent project to ensure consistency, maintainability, and compliance with government documentation vereistes.

## Scope

This policy applies to all documentation in the `/docs` directory and inline code documentation throughout the codebase.

## Documentation Standards

### 1. Frontmatter Vereisten

Every markdown document MUST include frontmatter with these fields:

```yaml
---
canonical: true|false        # Is this the authoritative source for this subject?
status: active|draft|archived # Document lifecycle state
owner: architecture|validation|platform|product|domain # Responsible party
last_verified: YYYY-MM-DD    # Date of last content verification
applies_to: definitie-app@version # Scope/version applicability
---
```

### 2. Single Source of Truth

- Only ONE document per subject may be marked `canonical: true`
- Non-canonical documents must reference the canonical source
- Duplicates must be archived in `/docs/archief/`

### 3. Document Structure

#### Naming Conventions
- Use UPPERCASE for policy/architecture docs (e.g., `ENTERPRISE_ARCHITECTURE.md`)
- Use lowercase-with-hyphens for technical docs (e.g., `module-afhankelijkheden.md`)
- Use descriptive names that indicate content

#### Required Sections
1. **Executive Summary** - High-level overview
2. **Context/Purpose** - Why this document exists
3. **Content** - Main body
4. **References** - Links to related documents

### 4. ID Reference Standards

All references to work items must use consistent formatting:

- Gebruikersverhalen: `US-XXX` (e.g., US-001)
- Bugs: `BUG-XXX` (e.g., BUG-042)
- Tasks: `TASK-XXX` (e.g., TASK-123)
- Epische Verhalen: `EPIC-X` (e.g., EPIC-007)

### 5. Markdown Standards

#### Headings
- Single H1 (`#`) per document
- Sequential heading levels (no skipping)
- Descriptive heading text

#### Lists
- Use bullets (`-`) for unordered lists
- Use numbers (`1.`) for ordered/procedural lists
- Maintain consistent indentation (2 spaces)

#### Code Blocks
- Always specify language: ` ```python`
- Use inline code for commands: `` `make test` ``
- Include context/explanation for code blocks

#### Links
- Use relative links for internal docs: `[text](./DOCUMENT-STANDARDS-GUIDE.md)`
- Use absolute URLs for external links
- Verify all links are valid

### 6. Language Standards

- **Technical documentation**: English
- **Business logic comments**: Dutch (Nederlands)
- **User-facing documentation**: Dutch (Nederlands)
- **Code comments**: English for technical, Dutch for domain logic

### 7. Versie Control

#### Commit Messages
Documentation changes must use these prefixes:
- `docs:` for general documentation updates
- `docs(<ID>):` for ID-specific updates (e.g., `docs(US-001):`)
- `docs(fix):` for documentation fixes
- `docs(refactor):` for reorganization

#### Change Tracking
- Update `last_verified` date when content changes
- Maintain changelog in significant documents
- Archive outdated versions in `/docs/archief/YYYY-MM-DD/`

## Document Locations

See `CANONICAL_LOCATIONS.md` for authoritative placement of document types.

### Core Locations
- `/docs/architectuur/` - Architecture documents
- `/docs/backlog/stories/` - User stories and epics
- `/docs/technisch/` - Technical specifications
- `/docs/archief/` - Archived documents (ONLY archive location)

## Quality Gates

Documentation must meet these criteria:

### Required Checks
- [ ] Frontmatter present and complete
- [ ] Canonical status validated (only one per subject)
- [ ] No broken internal links
- [ ] Proper markdown formatting
- [ ] ID references use standard format

### Warning Triggers
- `last_verified` > 90 days for canonical docs
- Missing frontmatter in active documents
- Documents outside canonical locations
- Duplicate canonical declarations

## Automated Validation

The Document Standards Guardian agent performs:
- Daily frontmatter validation
- Link checking on commits
- Canonical uniqueness verification
- Archive structure compliance
- ID reference format validation

## Archive Policy

### Wanneer to Archive
- Document superseded by newer version
- Content no longer relevant
- Status changed to `archived`
- Major refactoring/reorganization

### Archive Structure
```
/docs/archief/
├── YYYY-MM-DD/           # Date-based archives
├── REFERENTIE/           # Reference materials
├── HISTORISCH/           # Historical versions
└── ACTIEF/               # Still referenced but not primary
```

### Archive Rules
- NEVER create alternative archive directories
- ALWAYS use `/docs/archief/` as the sole archive location
- Maintain README.md in archive directories explaining content
- Preserve directory structure when archiving

## Compliance Monitoring

### Monthly Reviews
- Verify all canonical documents are current
- Check for orphaned documents
- Validate archive structure
- Update INDEX.md navigation

### Automated Reports
- `docs/docs-check.md` - Generated validation report
- Link check results in CI/CD pipeline
- Coverage metrics for documentation

## Justice Domain Vereisten

### ASTRA Compliance
- Documents must reference ASTRA standards where applicable
- Use justice domain terminology consistently
- Include compliance assessments for architecture docs

### Terminology
- Use official Dutch legal terms
- Reference authoritative sources (wetten.nl)
- Maintain glossary of domain terms

## Exceptions

Exceptions to this policy require:
1. Documented justification
2. Architecture owner approval
3. Temporary timeline for resolution
4. Entry in technical debt register

## References

- [CANONICAL_LOCATIONS.md](./CANONICAL_LOCATIONS.md) - Document placement standards
- [INDEX.md](../INDEX.md) - Documentation navigation hub
- ASTRA_COMPLIANCE.md - Justice standards (archived in /docs/archief/)
- [MASTER-EPICS-USER-STORIES.md](../backlog/stories/MASTER-EPICS-USER-STORIES.md) - Work item tracking

---

*Policy Versie: 1.0*
*Effective Date: 04-09-2025*
*Next Review: 04-12-2025*
