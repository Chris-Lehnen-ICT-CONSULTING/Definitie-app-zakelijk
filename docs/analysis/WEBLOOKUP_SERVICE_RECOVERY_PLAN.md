# WebLookupService Herstelplan

**Status**: 🔧 IN UITVOERING  
**Geschatte Doorlooptijd**: 3 weken  
**Prioriteit**: HOOG

## Overzicht

Dit document beschrijft het stapsgewijze herstelplan om de WebLookupService van niet-functioneel naar production-ready te krijgen.

## Week 1: Kritieke Fixes (Dag 1-5)

### Dag 1-2: Import & Basis Fixes

#### ✅ Stap 1: Fix Import Fouten
```python
# web_lookup_service.py - regel 28-36
from ..web_lookup.lookup import (
    zoek_definitie_op_wikipedia,
    zoek_definitie_op_wiktionary,
    zoek_definitie_op_overheidnl as zoek_overheid,
    zoek_definitie_op_wettennl as zoek_wetten,
    zoek_definitie_op_ensie as zoek_ensie,
    zoek_definitie_op_strafrechtketen as zoek_strafrechtketen,
    zoek_definitie_op_kamerstukken as zoek_kamerstukken
)
```

#### ✅ Stap 2: Maak Config Klasse
```python
# src/config/web_lookup_config.py
from dataclasses import dataclass

@dataclass
class WebLookupConfig:
    rate_limit_per_minute: int = 10
    cache_ttl_seconds: int = 3600
    request_timeout: int = 30
    max_concurrent_requests: int = 3
    
class Config:
    """Compatibility wrapper voor WebLookupService"""
    def __init__(self):
        self.web_lookup = WebLookupConfig()
```

#### ✅ Stap 3: Fix Async/Sync Wrapper
```python
# Voeg async wrapper functie toe
async def run_sync_in_async(func, *args, **kwargs):
    """Helper om sync functies in async context te draaien"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))
```

### Dag 3-4: Core Functionaliteit

#### ✅ Stap 4: Implementeer Data Transformatie
```python
def _transform_legacy_result(self, source_name: str, legacy_result: Any) -> dict:
    """Transformeer legacy resultaat naar verwacht formaat"""
    # Handle tuple responses
    if isinstance(legacy_result, tuple) and len(legacy_result) == 2:
        definitie, verwijzingen = legacy_result
        return {
            "definitie": definitie,
            "context": "",
            "voorbeelden": [],
            "verwijzingen": verwijzingen
        }
    # Handle string responses
    elif isinstance(legacy_result, str):
        return {
            "definitie": legacy_result,
            "context": "",
            "voorbeelden": [],
            "verwijzingen": []
        }
    return legacy_result if isinstance(legacy_result, dict) else None
```

#### ✅ Stap 5: Fix Lookup Methodes
Update `_lookup_with_timeout` om sync functies correct aan te roepen.

### Dag 5: Basis Testing

#### ✅ Stap 6: Minimale Test Suite
Maak basis tests om te verifiëren dat de service draait.

## Week 2: Stabilisatie & Integratie (Dag 6-10)

### Dag 6-7: Caching

#### ✅ Stap 7: Implementeer Async Cache
```python
# src/utils/async_cache.py
def cache_async_result(ttl: int = 3600):
    """Decorator voor async caching"""
    # Implementatie async cache
```

### Dag 8-9: Rate Limiting

#### ✅ Stap 8: Globale Rate Limiter
Implementeer file-based rate limiting voor cross-instance coordinatie.

### Dag 10: Container Integratie

#### ✅ Stap 9: Fix Service Container
Update container om correct Config te laden.

## Week 3: Optimalisatie & Productie (Dag 11-15)

### Dag 11-12: Orchestrator Integratie

#### ✅ Stap 10: Update Orchestrator
Zorg dat orchestrator WebLookupService gebruikt i.p.v. directe legacy imports.

### Dag 13-14: Complete Testing

#### ✅ Stap 11: Uitgebreide Test Suite
- Unit tests voor elke methode
- Integration tests
- Performance tests
- Error handling tests

### Dag 15: Documentatie

#### ✅ Stap 12: Update Alle Documentatie
- README updates
- Troubleshooting guide
- API documentatie

## Deliverables

### Week 1
- [ ] Service start zonder errors
- [ ] Basis lookup functionaliteit
- [ ] Config klasse werkt
- [ ] Async/sync issues opgelost

### Week 2
- [ ] Caching geïmplementeerd
- [ ] Rate limiting werkt globaal
- [ ] Container integratie compleet
- [ ] Basis tests draaien

### Week 3
- [ ] Orchestrator gebruikt service
- [ ] Test coverage >80%
- [ ] Performance geoptimaliseerd
- [ ] Documentatie bijgewerkt

## Success Criteria

1. **Alle tests slagen** (>80% coverage)
2. **Service draait stabiel** voor 24 uur
3. **Performance** <2s per lookup
4. **Geen memory leaks** na 1000 requests
5. **Feature flag test** succesvol

## Risico's

| Risico | Kans | Impact | Mitigatie |
|--------|------|--------|-----------|
| Legacy functies breken | Medium | Hoog | Uitgebreide tests |
| Performance degradatie | Laag | Medium | Benchmarks |
| API rate limits | Medium | Medium | Globale limiter |

## Code Voorbeelden

Zie de volledige code voorbeelden in het plan hierboven. Elke stap bevat concrete implementatie details.

## Tracking

Dit plan wordt bijgehouden in:
- Deze documentatie
- MASTER-TODO.md
- GitHub Issues/PR's

**Laatste update**: 2025-01-14