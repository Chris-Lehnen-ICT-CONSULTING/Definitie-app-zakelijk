---
id: EPIC-007
title: Prestaties & Scaling
canonical: true
status: IN_UITVOERING
owner: business-analyst
last_verified: 2025-09-05
applies_to: definitie-app@current
priority: HOOG
target_release: v1.1
aangemaakt: 2025-01-01
bijgewerkt: 2025-09-05
completion: 35%
stories:
  - US-028  # Service Initialization Caching
  - US-029  # Prompt Token Optimization
  - US-030  # validatieregels Caching
  - US-031  # ServiceContainer Circular Dependency Resolution
  - US-032  # Context Window Optimization
  - US-033  # V1 to V2 migration (GEREED)
  - US-034  # Service container optimization (GEREED)
  - US-035  # Load testing & benchmarking
  - US-047  # Complete V1 code removal
vereisten:
  - REQ-019  # Context FLAAG Integration (PER-007)
  - REQ-031  # Validation Result Caching
  - REQ-035  # Validation Prestaties Monitoring
  - REQ-036  # Context-Aware Validation
  - REQ-041  # Database Connection Management
  - REQ-046  # Monitoring and Metrics Collection
  - REQ-058  # Logging Configuration System
  - REQ-060  # Health Check Endpoints
  - REQ-061  # Graceful Degradation
  - REQ-062  # Circuit Breaker Pattern
  - REQ-064  # Scheduled Maintenance Mode
  - REQ-065  # Database Migration System
  - REQ-066  # Configuration Hot-reload
  - REQ-067  # Service Monitoring Dashboard
  - REQ-070  # Prestaties Testing
  - REQ-073  # Continuous Integration Testing
  - REQ-077  # Test Reporting and Analytics
astra_compliance: true
nora_compliance: true
stakeholders:
  - OM (HOOG-volume usage)
  - DJI (real-time vereisten)
  - Rechtspraak (concurrent users)
  - Justid (peak load handling)
  - CJIB (batch processing)
---

# EPIC-007: Prestaties & Scaling

## Managementsamenvatting

System efficiency and cost optimization through Prestaties improvements and scalability enhancements. This epic addresses KRITIEK Prestaties issues including 6x service initialization, 7,250 token prompts, and 45x rule reloading.

**Business Case:** The Dutch justitieketen processes thousands of legal documents daily across multiple organizations. OM processes require near real-time definition generation for case preparation, DJI needs rapid responses for detentie decisions, and Rechtspraak requires support for multiple concurrent users during rechtbank sessions. Current Prestaties issues (6x initialization overhead, excessive token usage) create bottlenecks that delay KRITIEK justice processes and increase operational costs. With upcoming chain-wide integration, the system must handle 10x current load while maintaining sub-5-second response times required by ASTRA Prestaties standards.

## Bedrijfswaarde

- **Primary Value**: Reduce operational costs and improve user experience
- **Cost Savings**: 50% reduction in OpenAI API costs (€100K/year savings)
- **User Experience**: < 5 second response times for justice professionals
- **Scalability**: Support for 100+ concurrent users across justitieketen
- **Chain Impact**: Enable real-time definition sharing between OM/DJI/Rechtspraak
- **Peak Load Support**: Handle month-end reporting peaks (10x normal load)
- **Measurable Outcomes**:
  - 50% reduction in user wait time
  - 0% timeout errors during peak hours
  - 99.9% availability SLA for justitieketen
  - 80% reduction in memory footprint

## Succesmetrieken (SMART)

- [ ] **Specifiek**: < 5 second definition generation for 95th percentile
- [ ] **Meetbaar**: < 3,000 tokens per prompt (currently 7,250)
- [ ] **Haalbaar**: 1x service initialization (currently 6x)
- [ ] **Relevant**: < 1 second validation for ASTRA compliance
- [ ] **Tijdgebonden**: < 100ms service access by Q1 2025
- [ ] **Justice-specific**: Support 500 OM concurrent users
- [ ] **Chain-valiDatumd**: Meet DJI real-time vereisten (< 2s)
- [ ] **Rechtspraak-ready**: Handle 50 judges simultaneously

## Current Prestaties Issues

### KRITIEK Problems Identified
1. **Service Initialization**: Services initialized 6x due to Streamlit reruns
2. **Prompt Tokens**: 7,250 tokens with duplications and all 45 rules
3. **validatieregels**: 45x reload per session without caching
4. **Memory Leaks**: Uncached services accumulating in memory
5. **Circular Afhankelijkheden**: ServiceContainer has circular references

## Gebruikersverhalen Overzicht

### US-028: Service Initialization Caching
**Status:** Nog te bepalen
**Prioriteit:** HOOG
**Story Points:** 5
**Target:** 1x initialization

**Gebruikersverhaal:**
Als ontwikkelaar binnen de justitieketen
wil ik service initialization to happen only once
zodat application startup is fast and memory efficient

**Technical Solution:**
- Use `@st.cache_resource` on ServiceContainer
- Implement singleton pattern properly
- Add cache invalidation controls

### US-029: Prompt Token Optimization
**Status:** Nog te bepalen
**Prioriteit:** HOOG
**Story Points:** 8
**Target:** < 3,000 tokens

**Gebruikersverhaal:**
As a product owner
wil ik to minimize OpenAI API token usage
zodat operational costs are reduced while maintaining quality

**Optimization Strategy:**
1. Include only relevant validatieregels
2. Implement prompt template caching
3. Remove duplicate instructions
4. Compress context information
5. Use dynamic prompt building

### US-030: validatieregels Caching
**Status:** Nog te bepalen
**Prioriteit:** HOOG
**Story Points:** 5
**Target:** < 10ms access

**Gebruikersverhaal:**
Als ontwikkelaar binnen de justitieketen
wil ik validatieregels loaded once per session
zodat validation Prestaties is optimal

**Implementatie:**
- Use `@st.cache_data` with TTL
- Implement rule Versieing
- Add cache warming on startup
- Monitor cache hit rates

### US-031: ServiceContainer Circular Dependency Resolution
**Status:** Nog te bepalen
**Prioriteit:** GEMIDDELD
**Story Points:** 8

**Gebruikersverhaal:**
Als ontwikkelaar binnen de justitieketen
wil ik clean dependency injection without circular references
zodat the codebase is maintainable and testable

**Refactoring Plan:**
1. Map current Afhankelijkheden
2. Identify circular references
3. Implement lazy loading
4. Use factory pattern where needed
5. ValiDatum with dependency tools

### US-032: Context Window Optimization
**Status:** Nog te bepalen
**Prioriteit:** GEMIDDELD
**Story Points:** 5
**Afhankelijkheden:** US-029

**Gebruikersverhaal:**
As a user
wil ik fast definition generation
zodat I can work efficiently without delays

**Optimization Areas:**
- Selective context inclusion
- Context compression
- Graceful degradation
- Token budget management

### US-033: V1 to V2 Migration ✅
**Status:** GEREED
**Prioriteit:** HOOG
**Story Points:** 13

**Implementatie:**
- V2 orchestrator fully deployed
- V1 code removed from production
- No dual system overhead

### US-034: Service Container Optimization ✅
**Status:** GEREED
**Prioriteit:** HOOG
**Story Points:** 8

**Implementatie:**
- Basic optimization started
- Lazy loading implemented
- Further caching needed (US-028)

## Prestaties Architecture

### Current State
```
Request → Streamlit Rerun (6x)
           ↓
    ServiceContainer Init (6x)
           ↓
    Load All Rules (45x)
           ↓
    Build Full Prompt (7,250 tokens)
           ↓
    API Call
           ↓
    Response
```

### Target State
```
Request → Cached Services (1x)
           ↓
    Cached Rules (0x reload)
           ↓
    Optimized Prompt (< 3,000 tokens)
           ↓
    API Call
           ↓
    Response
```

## Prestaties Benchmarks

### Current Prestaties
- Service Init: 600ms x 6 = 3.6s
- Rule Loading: 50ms x 45 = 2.25s
- Prompt Build: 200ms
- API Call: 3-5s
- Total: 9-11 seconds

### Target Prestaties
- Service Init: 100ms x 1 = 0.1s
- Rule Loading: 10ms (cached)
- Prompt Build: 50ms
- API Call: 2-3s
- Total: < 5 seconds

## Cost Analysis

### Current Costs
- Tokens per request: 7,250
- Cost per request: $0.29
- Daily requests: 1,000
- Daily cost: $290
- Monthly cost: $8,700

### Target Costs
- Tokens per request: 3,000
- Cost per request: $0.12
- Daily requests: 1,000
- Daily cost: $120
- Monthly cost: $3,600
- **Savings: $5,100/month (59%)**

## Afhankelijkheden

- Streamlit caching mechanisms
- Memory profiling tools
- Prestaties monitoring
- Load testing infrastructure

## Risico's & Mitigaties

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cache Invalidation | HOOG | Versie-based cache keys |
| Memory Growth | HOOG | Cache size limits, TTL |
| Prompt Quality | GEMIDDELD | A/B testing, quality metrics |
| Breaking Wijzigingen | HOOG | Feature flags, gradual rollout |

## Definitie van Gereed

- [ ] < 5 second response time achieved
- [ ] < 3,000 token prompts
- [ ] 1x service initialization
- [ ] All caching implemented
- [ ] Prestaties tests passing
- [ ] Memory leaks fixed
- [ ] Cost reduction verified
- [ ] Monitoring dashboards ready

## Wijzigingslog

| Datum | Versie | Wijzigingen |
|------|---------|---------|
| 2025-01-01 | 1.0 | Epic aangemaakt |
| 2025-09-05 | 1.x | Vertaald naar Nederlands met justitie context |
| 2025-09-04 | 1.1 | V1→V2 migration complete |
| 2025-09-05 | 1.2 | Prestaties analysis added |

## Gerelateerde Documentatie

- [Prestaties Testing Plan](../testing/Prestaties_testing.md)
- [Caching Strategy](../architectuur/caching_strategy.md)
- [Cost Optimization Guide](../guides/cost_optimization.md)

## Stakeholder Goedkeuring

- Technisch Lead: ⏳ In progress
- Product Owner: ⏳ Reviewing costs
- Operations Team: ⏳ Monitoring setup
- Finance: ❌ Awaiting cost analysis

---

*This epic is part of the DefinitieAgent project and folLAAGs ASTRA/NORA/BIR guidelines for justice domain systems.*
