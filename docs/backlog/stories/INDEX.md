---
aangemaakt: '08-09-2025'
bijgewerkt: '08-09-2025'
canonical: true
document_type: index
last_verified: 05-09-2025
owner: business-analyst
prioriteit: medium
status: active
titel: Story Index
---



# 📋 Gebruikersverhaal Index - DefinitieAgent

## Overview

This index provides a complete listing of all user stories in the DefinitieAgent project, organized by epic and status. Each story follows the US-XXX naming convention.

## Story Status Summary

### Overall Statistics
- **Total Stories**: 65 (incl. US-061 t/m US-065 from EPIC-012)
- **Completed**: 21 (32%)
- **In Progress**: 0 (0%)
- **TODO**: 44 (68%)
- **Blocked**: 0 (0%)

### Current Sprint (36) Stories
| ID | Story | Episch Verhaal | Prioriteit | Status | Points |
|----|-------|------|----------|--------|--------|
| [US-041](US-041.md) | Fix Context Field Mapping | EPIC-010 | KRITIEK | TODO | 8 |
| US-042 | Fix "Anders..." Custom Context | EPIC-010 | KRITIEK | TODO | 5 |
| US-028 | Service Initialization Caching | EPIC-007 | HOOG | TODO | 5 |
| US-029 | Prompt Token Optimization | EPIC-007 | HOOG | TODO | 8 |
| US-030 | Validation Rules Caching | EPIC-007 | HOOG | TODO | 5 |

## Complete Story Listing

### EPIC-001: Basis Definitie Generatie (5 stories - 100% complete)
| ID | Story | Status | Prioriteit | Points |
|----|-------|--------|----------|--------|
| [US-001](US-001.md) | Basic Definition Generation via GPT-4 | ✅ DONE | HOOG | 8 |
| US-002 | Prompt Template System | ✅ DONE | HOOG | 5 |
| US-003 | V1 Orchestrator Elimination | ✅ DONE | HOOG | 13 |
| US-004 | AI Configuration System via ConfigManager | ✅ DONE | GEMIDDELD | 5 |
| US-005 | Centralized AI Model Configuration | ✅ DONE | GEMIDDELD | 3 |

### EPIC-002: Kwaliteitstoetsing (8 stories - 100% complete)
| ID | Story | Status | Prioriteit | Points |
|----|-------|--------|----------|--------|
| US-006 | Validation Interface Design | ✅ DONE | HOOG | 5 |
| US-007 | Core Implementatie | ✅ DONE | HOOG | 8 |
| US-008 | Container Wiring | ✅ DONE | HOOG | 3 |
| US-009 | Integration Migration | ✅ DONE | HOOG | 5 |
| US-010 | Testen & QA | ✅ DONE | HOOG | 8 |
| US-011 | Production Rollout | ✅ DONE | HOOG | 3 |
| US-012 | All 45/45 Validation Rules Active | ✅ DONE | KRITIEK | 13 |
| US-013 | Modular Validation Service Operational | ✅ DONE | HOOG | 8 |

### EPIC-003: Content Verrijking / Web Lookup (1 story - 0% complete)
| ID | Story | Status | Prioriteit | Points |
|----|-------|--------|----------|--------|
| US-014 | Modern Web Lookup Implementatie | ⏳ TODO | HOOG | 13 |

### EPIC-004: User Interface (6 stories - 50% complete)
| ID | Story | Status | Prioriteit | Points |
|----|-------|--------|----------|--------|
| US-015 | Tab Activation (7/10 tabs needed) | 🔄 IN_PROGRESS | GEMIDDELD | 8 |
| US-016 | UI Prestaties Optimization | ⏳ TODO | HOOG | 5 |
| US-017 | Responsive Design Implementatie | ⏳ TODO | GEMIDDELD | 8 |
| US-018 | Basic Tab Structure | ✅ DONE | HOOG | 3 |
| US-019 | Definition Generation UI | ✅ DONE | HOOG | 5 |
| US-020 | Validation Results Display | ✅ DONE | HOOG | 5 |

### EPIC-005: Export & Import (3 stories - 0% complete)
| ID | Story | Status | Prioriteit | Points |
|----|-------|--------|----------|--------|
| US-021 | Export Formats (JSON, PDF, DOCX) | ⏳ TODO | GEMIDDELD | 8 |
| US-022 | Import Validation | ⏳ TODO | HOOG | 5 |
| US-023 | Batch Operations | ⏳ TODO | LAAG | 8 |

### EPIC-006: Beveiliging & Auth (4 stories - 75% complete)
| ID | Story | Status | Prioriteit | Points |
|----|-------|--------|----------|--------|
| US-024 | API Key Validation at Startup | ⏳ TODO | HOOG | 3 |
| US-025 | API Key Beveiliging Fix | ✅ DONE | KRITIEK | 5 |
| US-026 | Environment Variable Configuration | ✅ DONE | HOOG | 3 |
| US-027 | Component-specific AI Configuration Beveiliging | ✅ DONE | GEMIDDELD | 5 |

### EPIC-007: Prestaties & Scaling (7 stories - 29% complete)
| ID | Story | Status | Prioriteit | Points |
|----|-------|--------|----------|--------|
| US-028 | Service Initialization Caching | ⏳ TODO | HOOG | 5 |
| US-029 | Prompt Token Optimization | ⏳ TODO | HOOG | 8 |
| US-030 | Validation Rules Caching | ⏳ TODO | HOOG | 5 |
| US-031 | ServiceContainer Circular Dependency Resolution | ⏳ TODO | GEMIDDELD | 8 |
| US-032 | Context Window Optimization | ⏳ TODO | GEMIDDELD | 5 |
| US-033 | V1 to V2 Migration | ✅ DONE | HOOG | 13 |
| US-034 | Service Container Optimization | ✅ DONE | HOOG | 8 |

### EPIC-009: Advanced Features (6 stories - 0% complete)
| ID | Story | Status | Prioriteit | Points |
|----|-------|--------|----------|--------|
| US-035 | Multi-definition Batch Processing | ⏳ TODO | GEMIDDELD | 13 |
| US-036 | Versie Control Integration | ⏳ TODO | LAAG | 8 |
| US-037 | Collaborative Editing | ⏳ TODO | LAAG | 13 |
| US-038 | FastAPI REST Endpoints | ⏳ TODO | HOOG | 8 |
| US-039 | PostgreSQL Migration | ⏳ TODO | HOOG | 13 |
| US-040 | Multi-tenant Architecture | ⏳ TODO | GEMIDDELD | 21 |

### EPIC-010: Context Flow Refactoring (6 stories - 0% complete) 🚨
**Note:** Related legacy cleanup stories US-043 and US-056 are now part of [EPIC-012](../epics/EPIC-012-legacy-orchestrator-refactoring.md).

### EPIC-012: Legacy Orchestrator Refactoring (5 stories - 0% complete)
| ID | Story | Status | Prioriteit | Points |
|----|-------|--------|----------|--------|
| US-061 | Extract Business Kennis uit Legacy | ⏳ TODO | KRITIEK | 5 |
| US-062 | Refactor FeedbackBuilder naar V2 | ⏳ TODO | KRITIEK | 8 |
| US-063 | Integreer Config en Context in V2 | ⏳ TODO | HOOG | 5 |
| US-064 | Consolideer Orchestration Logica | ⏳ TODO | HOOG | 8 |
| US-065 | Moderniseer UI Dependencies | ⏳ TODO | GEMIDDELD | 3 |
| ID | Story | Status | Prioriteit | Points |
|----|-------|--------|----------|--------|
| [US-041](US-041.md) | Fix Context Field Mapping to Prompts | ⏳ TODO | KRITIEK | 8 |
| US-042 | Fix "Anders..." Custom Context Option | ⏳ TODO | KRITIEK | 5 |
| US-043 | Remove Legacy Context Routes | ⏳ TODO | HOOG | 8 |
| US-044 | Implement Context Type Validation | ⏳ TODO | HOOG | 3 |
| US-045 | Add Context Traceability for ASTRA | ⏳ TODO | HOOG | 5 |
| US-046 | Create End-to-End Context Flow Tests | ⏳ TODO | HOOG | 8 |

## Prioriteit Distribution

### By Prioriteit Level
- **KRITIEK**: 5 stories (11%)
- **HOOG**: 27 stories (59%)
- **GEMIDDELD**: 10 stories (22%)
- **LAAG**: 4 stories (8%)

### Critical Stories Pending
1. US-041: Fix Context Field Mapping (EPIC-010)
2. US-042: Fix "Anders..." Option (EPIC-010)

## Story Point Analysis

### Total Points by Episch Verhaal
| Episch Verhaal | Total Points | Completed | Remaining |
|------|--------------|-----------|-----------|
| EPIC-001 | 34 | 34 | 0 |
| EPIC-002 | 53 | 53 | 0 |
| EPIC-003 | 13 | 0 | 13 |
| EPIC-004 | 34 | 13 | 21 |
| EPIC-005 | 21 | 0 | 21 |
| EPIC-006 | 16 | 13 | 3 |
| EPIC-007 | 52 | 21 | 31 |
| EPIC-009 | 76 | 0 | 76 |
| EPIC-010 | 37 | 0 | 37 |
| **TOTAL** | **336** | **134** | **202** |

### Velocity Metrics
- Average velocity per sprint: 15 points
- Completed to date: 134 points (40%)
- Remaining work: 202 points
- Estimated sprints to complete: 13-14

## Afhankelijkheden & Blockers

### Critical Afhankelijkheden
- US-041 (Context Mapping) blocks ASTRA compliance
- US-028 (Service Caching) blocks performance targets
- US-029 (Token Optimization) blocks cost targets

### Story Afhankelijkheden Map
```
US-041 (Context Fix)
    ├── US-044 (Type Validation)
    └── US-045 (Traceability)
        └── US-046 (E2E Tests)

US-029 (Token Optimization)
    └── US-032 (Context Window)
```

## File Organization

### Story File Naming Convention
- Pattern: `US-XXX.md` where XXX is a 3-digit number
- Example: `US-001.md`, `US-041.md`
- Location: `/docs/backlog/stories/`

### Required Frontmatter
```yaml
id: US-XXX
epic: EPIC-XXX
title: Story Title
status: todo|in_progress|done|blocked
priority: critical|high|medium|low
story_points: 1-21
sprint: sprint-XX|backlog|completed
```

## Quick Links

### Navigation
- [Episch Verhaal Dashboard](../epics/INDEX.md)
- [Requirements Dashboard](../dashboard/index.html)
- [Per‑Epic Overzicht](../dashboard/per-epic.html)
- [Current Sprint](../sprints/sprint-36.md)
- [Product Backlog](../backlog/product-backlog.md)
- [Vereisten](../vereistes/)

### Critical Stories
- [US-041: Fix Context Field Mapping](US-041.md)
- [US-001: Basic Definition Generation](US-001.md)

### Documentation
- [Story Template](../templates/story-template.md)
- [Definition of Done](../guidelines/definition-of-done.md)
- [ASTRA Guidelines](../guidelines/ASTRA-compliance.md)

## Update History

| Date | Changes |
|------|---------|
| 05-09-2025 | Initial story index created |
| 05-09-2025 | Migrated from MASTER-EPICS-USER-STORIES.md |

---

*This index is maintained by the Business Analyst Agent and updated with each story creation or status change.*
