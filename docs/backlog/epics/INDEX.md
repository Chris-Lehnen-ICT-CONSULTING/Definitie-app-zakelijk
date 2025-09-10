---
aangemaakt: '08-09-2025'
bijgewerkt: '08-09-2025'
canonical: true
document_type: index
last_verified: 05-09-2025
owner: business-analyst
prioriteit: medium
status: active
titel: Episch Verhaal Dashboard - Nederlandse Justitieketen
---



# 📊 Episch Verhaal Dashboard - DefinitieAgent voor Nederlandse Justitieketen

## Overzicht

Dit dashboard biedt een volledig overzicht van alle epics in het DefinitieAgent project voor de Nederlandse justitieketen (OM, DJI, Rechtspraak, Justid, CJIB). Elke epic vertegenwoordigt een belangrijk functiegebied of systeemcapaciteit voor juridische definities.

### Navigatie
- [🧭 Requirements Dashboard](../dashboard/index.html)
- [▸ Per‑Epic Overzicht (inklappen/uitklappen)](../dashboard/per-epic.html)
- [↗︎ Grafisch Overzicht (REQ ↔ EPIC)](../dashboard/graph.html)

## Episch Verhaal Status Summary

| ID | Episch Verhaal | Status | Prioriteit | Completion | Target Release | Stories |
|----|------|--------|----------|------------|----------------|---------|
| [EPIC-001](EPIC-001-basis-definitie-generatie.md) | Basis Definitie Generatie | ✅ Completed | HOOG | 100% | v1.0 | 5/5 |
| [EPIC-002](EPIC-002-kwaliteitstoetsing.md) | Kwaliteitstoetsing | ✅ Completed | HOOG | 100% | v1.0 | 8/8 |
| [EPIC-003](EPIC-003-content-verrijking-web-lookup.md) | Content Verrijking / Web Lookup | 🔄 In Progress | HOOG | 30% | v1.1 | 1/1 |
| [EPIC-004](EPIC-004-user-interface.md) | User Interface | 🔄 In Progress | GEMIDDELD | 30% | v1.2 | 3/6 |
| [EPIC-005](EPIC-005-export-import.md) | Export & Import | ⏳ TODO | LAAG | 10% | v1.3 | 0/3 |
| [EPIC-006](EPIC-006-security-auth.md) | Beveiliging & Auth | 🔄 In Progress | KRITIEK | 40% | v1.0 | 3/4 |
| [EPIC-007](EPIC-007-performance-scaling.md) | Prestaties & Scaling | 🔄 In Progress | HOOG | 35% | v1.1 | 2/7 |
| EPIC-008 | Web Lookup Module | 🔀 Merged | - | - | - | → EPIC-003 |
| [EPIC-009](EPIC-009-advanced-features.md) | Advanced Features | ⏳ TODO | LAAG | 5% | v2.0 | 0/6 |
| [EPIC-010](EPIC-010-context-flow-refactoring.md) | Context Flow Refactoring | 🚨 KRITIEK | KRITIEK | 0% | v1.0.1 | 0/6 |
| EPIC-011 | Documentatie Completering | ⏳ TODO | GEMIDDELD | 0% | v1.2 | 0/3 |
| [EPIC-012](EPIC-012-legacy-orchestrator-refactoring.md) | Legacy Orchestrator Refactoring | ⏳ TODO | HOOG | 0% | v1.1 | 0/5 |

## Progress Metrics

### Overall Project Completion
```
Completed: ████████████░░░░░░░░ 40%
```

### By Prioriteit
- **KRITIEK**: 1 epic (EPIC-010) - 0% complete 🚨
- **HOOG**: 5 epics - Average 53% complete (incl. EPIC-012)
- **GEMIDDELD**: 2 epics - 15% complete (incl. EPIC-011)
- **LAAG**: 2 epics - 7.5% complete

### By Release
- **v1.0**: 3 epics - 80% complete
- **v1.0.1**: 1 epic (hotfix) - 0% complete 🚨
- **v1.1**: 2 epics - 32.5% complete
- **v1.2**: 1 epic - 30% complete
- **v1.3**: 1 epic - 10% complete
- **v2.0**: 1 epic - 5% complete

## Story Distribution

| Episch Verhaal | Total Stories | Completed | In Progress | TODO | Blocked |
|------|--------------|-----------|-------------|------|---------|
| EPIC-001 | 5 | 5 | 0 | 0 | 0 |
| EPIC-002 | 8 | 8 | 0 | 0 | 0 |
| EPIC-003 | 1 | 0 | 0 | 1 | 0 |
| EPIC-004 | 6 | 3 | 0 | 3 | 0 |
| EPIC-005 | 3 | 0 | 0 | 3 | 0 |
| EPIC-006 | 4 | 3 | 0 | 1 | 0 |
| EPIC-007 | 7 | 2 | 0 | 5 | 0 |
| EPIC-009 | 6 | 0 | 0 | 6 | 0 |
| EPIC-010 | 6 | 0 | 0 | 6 | 0 |
| EPIC-011 | 3 | 0 | 0 | 3 | 0 |
| EPIC-012 | 5 | 0 | 0 | 5 | 0 |
| **TOTAL** | **60** | **21** | **0** | **39** | **0** |

## Critical Items Requiring Attention

### 🚨 EPIC-010: Context Flow Refactoring
- **Status**: KRITIEK - 0% complete
- **Issue**: Context fields NOT being passed to AI prompts
- **Impact**: Non-compliant legal definitions
- **Action Required**: IMMEDIATE hotfix deployment

### ⚠️ Prestaties Issues (EPIC-007)
- Service initialization happening 6x
- Prompt tokens at 7,250 (target: 3,000)
- Validation rules loading 45x per session

## Sprint 36 Focus (Current)

1. **US-041**: Fix context field mapping (KRITIEK)
2. **US-042**: Fix "Anders..." crashes (KRITIEK)
3. **US-028**: Service initialization caching (HOOG)
4. **US-029**: Prompt token optimization (HOOG)

## ASTRA Compliance Status

| Episch Verhaal | ASTRA Compliant | Notes |
|------|-----------------|-------|
| EPIC-001 | ✅ Yes | Fully compliant |
| EPIC-002 | ✅ Yes | Validation rules aligned |
| EPIC-003 | ✅ Yes | Following integration patterns |
| EPIC-004 | ✅ Yes | UI accessibility standards |
| EPIC-005 | ✅ Yes | Data exchange standards |
| EPIC-006 | ✅ Yes | Beveiliging guidelines |
| EPIC-007 | ✅ Yes | Prestaties patterns |
| EPIC-009 | ⏳ Planned | Enterprise patterns |
| EPIC-010 | ❌ **Blocked** | Cannot comply without context fix |

## Afhankelijkheden & Blockers

### Critical Afhankelijkheden
- **EPIC-010** blocks ASTRA compliance certification
- **EPIC-006** (Beveiliging) blocks production deployment
- **EPIC-007** (Prestaties) blocks scale testing

### Cross-Episch Verhaal Afhankelijkheden
```
EPIC-001 (Generation) → EPIC-002 (Validation)
                     ↓
              EPIC-003 (Enrichment)
                     ↓
              EPIC-004 (UI Display)
                     ↓
              EPIC-005 (Export)
```

## Resource Allocation

### Current Sprint (36)
- 2 developers on EPIC-010 (critical fixes)
- 1 developer on EPIC-007 (performance)
- 1 tester on validation coverage

### Recommended Allocation
- **Immediate**: All hands on EPIC-010
- **Next Sprint**: Focus on EPIC-007 performance
- **Future**: EPIC-003 web lookup, EPIC-004 UI

## Risk Matrix

| Episch Verhaal | Risk Level | Impact | Mitigation |
|------|------------|--------|------------|
| EPIC-010 | 🔴 KRITIEK | Legal compliance failure | Immediate hotfix |
| EPIC-006 | 🟠 HOOG | Beveiliging vulnerabilities | API key validation |
| EPIC-007 | 🟠 HOOG | Cost overruns ($5k/month) | Token optimization |
| EPIC-003 | 🟡 GEMIDDELD | Missing enrichment | Phased rollout |
| EPIC-004 | 🟡 GEMIDDELD | Poor UX | User testing |
| EPIC-005 | 🟢 LAAG | Limited integration | Defer to v1.3 |

## Success Metrics

### Key Prestaties Indicators
- **Definition Generation Time**: Target < 5s (Current: 9-11s)
- **Validation Coverage**: Target 45/45 rules (Current: 45/45 ✅)
- **API Token Usage**: Target < 3,000 (Current: 7,250)
- **User Satisfaction**: Target > 90% (Current: ~40%)
- **ASTRA Compliance**: Target 100% (Current: 88%)

## Navigation

### Quick Links
- [All Stories](../stories/INDEX.md)
- [Current Sprint](#sprint-36)
- [Product Backlog](#product-backlog)
- [Architecture Docs](../../architectuur/)
- [Testen Plans](../../testing/)

### Episch Verhaal Details
- [EPIC-001: Basis Definitie Generatie](EPIC-001-basis-definitie-generatie.md)
- [EPIC-002: Kwaliteitstoetsing](EPIC-002-kwaliteitstoetsing.md)
- [EPIC-003: Content Verrijking](EPIC-003-content-verrijking-web-lookup.md)
- [EPIC-004: User Interface](EPIC-004-user-interface.md)
- [EPIC-005: Export & Import](EPIC-005-export-import.md)
- [EPIC-006: Beveiliging & Auth](EPIC-006-security-auth.md)
- [EPIC-007: Prestaties & Scaling](EPIC-007-performance-scaling.md)
- [EPIC-009: Advanced Features](EPIC-009-advanced-features.md)
- [EPIC-010: Context Flow Refactoring](EPIC-010-context-flow-refactoring.md)

## Update History

| Date | Changes |
|------|---------|
| 05-09-2025 | Initial epic dashboard created |
| 05-09-2025 | Migration from monolithic MASTER document |

---

*This dashboard is maintained by the Business Analyst Agent and updated with each sprint planning cycle.*
