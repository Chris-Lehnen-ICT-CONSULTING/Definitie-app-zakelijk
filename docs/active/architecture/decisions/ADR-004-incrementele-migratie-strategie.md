# ADR-004: Incrementele Migratie Strategie

**Status:** Geaccepteerd  
**Datum:** 2025-07-17  
**Deciders:** Development Team  

## Context

DefinitieAgent moet gemigreerd worden van een legacy architectuur naar een moderne, maintainable structuur zonder business continuity te verstoren. De applicatie is actief in gebruik en downtime is niet acceptabel.

Huidige uitdagingen:
- Legacy code met impliciete business rules
- 87% failing tests
- Productie gebruikers verwachten stabiliteit
- Geen rollback strategie
- Beperkte resources (1-2 developers)

## Probleemstelling

Hoe migreren we van legacy naar moderne architectuur met minimaal risico en zonder service onderbreking?

## Beslissing

We adopteren een incrementele "Strangler Fig" pattern waarbij we geleidelijk legacy componenten vervangen met moderne implementaties, ondersteund door feature flags en comprehensive monitoring.

## Rationale

1. **Zero downtime**: Business continuity is kritiek
2. **Risk mitigation**: Kleine incrementele changes zijn veiliger
3. **Rollback capability**: Elke stap is reversible
4. **Learning opportunity**: Leer van elke migratie stap
5. **Stakeholder confidence**: Zichtbare voortgang zonder disruption
6. **Testing in production**: Geleidelijke rollout met real users

## Gevolgen

### Positief
- ✅ Geen service onderbreking
- ✅ Rollback altijd mogelijk
- ✅ Geleidelijke risk exposure
- ✅ Continue feedback loop
- ✅ Legacy en modern kunnen co-existeren
- ✅ A/B testing mogelijkheden

### Negatief
- ❌ Langere totale migratie tijd
- ❌ Complexity van dual systems
- ❌ Extra code voor compatibility layers
- ❌ Mogelijk performance overhead

### Neutraal
- 🔄 Feature flags management required
- 🔄 Monitoring kritiek voor succes
- 🔄 Documentatie van beide systemen

## Implementatie Pattern

### Core Migration Pattern

```python
class MigrationFacade:
    """Transparante migratie van legacy naar modern"""
    
    def __init__(self):
        self.legacy = LegacySystem()
        self.modern = ModernSystem()
        self.feature_flags = FeatureFlags()
        self.metrics = MetricsCollector()
    
    def process(self, request: Request) -> Response:
        # Decision logic
        use_modern = self._should_use_modern(request)
        
        # Metrics collection
        self.metrics.record_decision(use_modern)
        
        if use_modern:
            try:
                response = self.modern.process(request)
                self.metrics.record_success("modern")
                return response
            except Exception as e:
                logger.warning(f"Modern failed, falling back: {e}")
                self.metrics.record_fallback()
                return self.legacy.process(request)
        
        response = self.legacy.process(request)
        self.metrics.record_success("legacy")
        return response
    
    def _should_use_modern(self, request: Request) -> bool:
        # Canary deployment
        if self.feature_flags.is_enabled("modern_canary", request.user_id):
            return True
        
        # Percentage rollout
        if self.feature_flags.percentage("modern_rollout") > random.random():
            return True
        
        # Specific features
        if request.feature in self.feature_flags.get("modern_features", []):
            return True
        
        return False
```

## Migration Phases

### Phase 0: Preparation ✅ (Completed)
- Service consolidation
- Basic wrapper implementation
- Monitoring setup

### Phase 1: Foundation (Week 1-2)
- Feature flags infrastructure
- Metrics collection
- Fallback mechanisms
- Basic health checks

### Phase 2: Core Services (Week 3-4)
- Definition generation migration
- Validation service migration
- Data layer compatibility

### Phase 3: UI Components (Week 5-6)
- Tab-by-tab migration
- Session state handling
- User preference migration

### Phase 4: Data Migration (Week 7-8)
- SQLite to PostgreSQL preparation
- Dual-write implementation
- Data consistency validation

### Phase 5: Cleanup (Future)
- Legacy code removal
- Feature flag cleanup
- Documentation finalization

## Feature Flag Strategy

```yaml
feature_flags:
  # Canary deployment - specific users
  modern_definition_canary:
    type: user_list
    users: [beta_user_1, beta_user_2]
  
  # Percentage rollout
  modern_definition_rollout:
    type: percentage
    value: 10  # Start with 10%
    increment: 10  # Increase by 10% daily if healthy
  
  # Feature specific flags
  modern_validation:
    type: boolean
    value: false
  
  # Emergency kill switch
  use_legacy_only:
    type: boolean
    value: false  # Set true in emergencies
```

## Monitoring Requirements

### Key Metrics

```python
metrics_to_track = {
    "response_time": {
        "legacy_p95": 8000,  # ms
        "modern_target": 5000  # ms
    },
    "error_rate": {
        "threshold": 0.01,  # 1%
        "action": "rollback"
    },
    "fallback_rate": {
        "warning": 0.05,  # 5%
        "critical": 0.10  # 10%
    },
    "feature_adoption": {
        "daily_target": 10  # percentage points
    }
}
```

### Alerting Rules

1. **Immediate rollback** if error rate > 5%
2. **Investigation** if fallback rate > 5%
3. **Pause rollout** if performance degrades >20%
4. **Success celebration** at each 25% milestone

## Risk Mitigation

### Rollback Procedures

```bash
# Quick rollback
./scripts/rollback.sh --component=definition_service --version=previous

# Emergency full rollback
./scripts/emergency_rollback.sh --kill-switch=use_legacy_only

# Gradual rollback
./scripts/adjust_rollout.sh --percentage=0 --component=all
```

### Data Consistency

```python
class DualWriteManager:
    """Ensure data consistency during migration"""
    
    async def write(self, data: Any) -> None:
        # Write to both systems
        legacy_result = await self.legacy_writer.write(data)
        modern_result = await self.modern_writer.write(data)
        
        # Verify consistency
        if not self._are_consistent(legacy_result, modern_result):
            await self._reconcile(legacy_result, modern_result)
            raise InconsistencyError("Data mismatch detected")
```

## Success Criteria

- [ ] Each phase completed without rollback
- [ ] Error rate remains <1%
- [ ] Performance improves or stays same
- [ ] 100% feature parity maintained
- [ ] User satisfaction stable/improved

## Communication Plan

- **Daily**: Migration metrics dashboard
- **Weekly**: Progress report to stakeholders
- **On-demand**: Incident reports
- **Milestone**: Celebration announcements

## Review Triggers

- Any emergency rollback
- Performance degradation >20%
- User complaints increase
- Team capacity changes

## Gerelateerde Beslissingen

- ADR-001: Monolith (simpler migration)
- ADR-002: Features First (know what to migrate)
- ADR-003: Legacy as Spec (what to preserve)

## Status Updates

- 2025-07-17: Strategy adopted
- [Future updates here]

## Referenties

- [Strangler Fig Application - Martin Fowler](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Feature Toggles - Pete Hodgson](https://martinfowler.com/articles/feature-toggles.html)
- [Database Refactoring - Scott Ambler](https://databaserefactoring.com/)