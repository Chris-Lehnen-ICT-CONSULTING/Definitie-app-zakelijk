# Multi-Agent Code Review — DefinitieAgent
**Datum:** 26 maart 2026
**Methode:** Prompt Forge Orchestrator (10 agents, 5 areas, weighted consensus)
**Codebase:** ~97.000 LOC (371 Python bestanden)

---

## Executive Summary

De DefinitieAgent codebase is een functioneel sterke applicatie met goede architectuurintentie, maar bevat **8 bevestigde kritieke/hoge issues** die aandacht vereisen. De zwakste gebieden zijn security (niet-aangesloten middleware, pickle kwetsbaarheden) en de UI-laag (Streamlit widget race conditions). De sterkste gebieden zijn configuratiebeheer en de plugin-achtige validatieregel-architectuur.

**Gewogen totaalscore: 6.3 / 10**

---

## Scores per Area

| # | Area | LOC | Code Quality (1.5x) | Architecture (2.0x) | Gewogen Score |
|---|------|-----|---------------------|---------------------|---------------|
| 1 | Core Services | 37.340 | 7.2 | 6.0 | 6.5 |
| 2 | UI Layer (Streamlit) | 15.861 | 6.5 | 6.5 | 6.5 |
| 3 | Validation Engine | 18.639 | 6.2 | 6.5 | 6.4 |
| 4 | Data Layer | 6.936 | 6.5 | 5.5 | 5.9 |
| 5 | Infrastructure | 10.880 | 6.5 | 6.3 | 6.4 |
| | **Totaal** | **~97K** | | | **6.3** |

---

## Bevestigde Kritieke Issues (Geverifieerd)

### CRITICAL-1: Streamlit Race Conditions (6 widgets)
**Status:** BEVESTIGD door verificatie-agent
**Consensus:** 100% (beide UI-agents + verificatie)
**Locatie:** `src/ui/components/definition_edit_tab.py` regels 476-712

Zes widgets gebruiken `value=` samen met `key=`, wat direct in strijd is met de verplichte key-only pattern uit `streamlit-patterns.md`:

```python
# FOUT (huidige code):
st.text_input("Begrip", value=definition.begrip, key=k("begrip"))
st.text_area("Definitie tekst", value=definition.definitie, key=k("definitie"))
# + 4 andere instances (org_custom, jur_custom, wet_custom, toelichting)

# GOED (fix):
st.text_input("Begrip", key=k("begrip"))  # Gebruik SessionStateManager voor initialisatie
```

**Impact:** Race conditions waarbij user-input wordt overschreven bij elke Streamlit rerun.
**Prioriteit:** P0 — Direct fixen

---

### CRITICAL-2: Pickle Deserialisatie zonder Integriteitscheck
**Status:** BEVESTIGD
**Consensus:** 100% (infra code quality + verificatie)
**Locaties:**
- `src/utils/cache.py` regels 114, 619
- `src/utils/resilience.py` regel 374

```python
with open(cache_file, "rb") as f:
    return pickle.load(f)  # Geen HMAC verificatie
```

**Impact:** Kwaadaardige cache-bestanden kunnen willekeurige code uitvoeren.
**Prioriteit:** P0 — Vervang door JSON/msgpack of voeg HMAC toe

---

### CRITICAL-3: Security Middleware Niet Aangesloten
**Status:** BEVESTIGD
**Consensus:** 100% (beide infra-agents + verificatie)
**Locatie:** `src/security/security_middleware.py` (731 LOC)

Volledige security middleware (validatie, threat detection, rate limiting, security headers) is geïmplementeerd maar **nergens aangesloten op FastAPI routes**. Grep in `src/api/` levert nul imports op.

**Impact:** API heeft geen runtime security-validatie ondanks 730 regels implementatie.
**Prioriteit:** P0 — Wire into FastAPI

---

### CRITICAL-4: XSS Filter Regex Bypass
**Status:** BEVESTIGD
**Consensus:** 100%
**Locatie:** `src/validation/sanitizer.py` regel 189

```python
pattern=r'\s(on\w+|javascript:|vbscript:|data:)\s*=\s*["\'][^"\']*["\']'
#         ^^ Vereist leading whitespace — kan worden omzeild
```

**Impact:** XSS aanvallen zonder voorafgaande spatie passeren de sanitizer.
**Prioriteit:** P1 — Vervang regex met `bleach` library

---

## Bevestigde Hoge Issues

### HIGH-1: God Classes (3 bestanden >1500 LOC)
**Consensus:** 100% (alle architecture agents)

| Bestand | LOC | Verantwoordelijkheden |
|---------|-----|----------------------|
| `database/definitie_repository.py` | 2.209 | CRUD + Search + Examples + Synonyms + Import/Export + History |
| `ui/components/definition_edit_tab.py` | 1.905 | Selector + Form + Context + Actions + History + Metadata |
| `services/validation/modular_validation_service.py` | 1.766 | Rule evaluation + Result formatting + Aggregation |

**Aanbeveling:** Split elk in 3-4 gefocuste klassen

### HIGH-2: Hardcoded Validatieregels
**Status:** BEVESTIGD
**Locatie:** `src/validation/definitie_validator.py` regels 166-189

43 patronen/regels staan hardcoded in code terwijl `config/toetsregels.json` de bron zou moeten zijn (per CLAUDE.md). Dit schendt het core principe van het project.

### HIGH-3: ServiceContainer is God Class (1002 LOC)
**Consensus:** 100% (beide services agents)
**Locatie:** `src/services/container.py`

30 factory methods + configuratie-loading + model routing + lazy/eager coördinatie — te veel verantwoordelijkheden.

**Aanbeveling:** Split in `ServiceFactory` + `ConfigurationPolicy`

### HIGH-4: Data Model Mismatch (str vs list)
**Consensus:** 100% (beide data-agents)

`DefinitieRecord` (DB): context velden zijn `str` (JSON)
`Definition` (Service): context velden zijn `list[str]`

Conversie tussen lagen is fragiel en ongevalideerd. Kan leiden tot silent data loss.

### HIGH-5: Fragmented Resilience (4 modules)
**Consensus:** 100% (beide infra-agents)

Vier overlappende modules: `resilience.py`, `enhanced_retry.py`, `smart_rate_limiter.py`, `integrated_resilience.py`. Onduidelijk welke te gebruiken.

---

## Afgewezen / Gemitigeerde Issues

| Issue | Status | Reden |
|-------|--------|-------|
| SQL ORDER BY injection (synonym_registry.py:854) | **GEMITIGEERD** | Whitelist validatie op regel 811 voorkomt exploitatie |
| ai_toetser dead code | **WAARSCHIJNLIJK** | Geen imports gevonden, maar tests niet volledig gecontroleerd |
| 91 broad exception handlers | **DEELS AFGEWEZEN** | Veel zijn bewuste fallback-patronen; ~30 verdienen herziening |

---

## Aanbevolen Actieplan

### Sprint 1 (Week 1-2): Security & Stability
1. Fix 6 Streamlit race conditions in definition_edit_tab.py
2. Vervang pickle met JSON/msgpack + HMAC in cache.py en resilience.py
3. Wire security middleware into FastAPI routes
4. Vervang XSS regex met `bleach` library
5. Voeg thread lock toe aan singleton repositories

### Sprint 2 (Week 3-4): Architecture Cleanup
6. Split definitie_repository.py god class (→ Examples, Synonyms, Search repos)
7. Split definition_edit_tab.py (→ Form, Selector, Actions, Metadata)
8. Verplaats hardcoded validatieregels naar config
9. Unify resilience modules (kies SmartRateLimiter als standaard)
10. Externaliseer security patterns naar config

### Sprint 3 (Week 5-6): Architecture Improvement
11. Refactor ServiceContainer (→ ServiceFactory + ConfigurationPolicy)
12. Extract sub-orchestrators uit DefinitionOrchestratorV2
13. Fix data model mismatch (Pydantic validatie op conversie-laag)
14. Reorganiseer utils/ in subdirectories
15. Verwijder of archiveer ai_toetser dead code

---

## Methodologie

### Agent Teams (10 agents, 5 areas)

| Area | Code Quality Reviewer (1.5x) | Architecture Reviewer (2.0x) |
|------|------------------------------|------------------------------|
| Core Services | Bugs, error handling, code smells | SOLID, coupling, DI patterns |
| UI Layer | Streamlit patterns, DRY, complexity | Component architecture, state mgmt |
| Validation Engine | Correctness, security, regex quality | Pipeline design, rule loading |
| Data Layer | SQL safety, transactions, resources | Repository pattern, model design |
| Infrastructure | Security vulns, race conditions | Cross-cutting, layering, config |

### Consensus Protocol
- **Gewogen stemming:** 60% threshold voor bevestiging
- **Agent gewichten:** Code Quality = 1.5x, Architecture = 2.0x
- **Verificatie:** Top-7 kritieke issues geverifieerd door 11e agent
- **False positive filtering:** 2 van 9 geverifieerde issues afgewezen/gemitigeerd

### Statistieken
- **Totaal gevonden issues:** 67
- **Na consensus filtering:** 42
- **Na verificatie:** 38 bevestigd
- **CRITICAL:** 4 | **HIGH:** 5 | **MEDIUM:** 18 | **LOW:** 11
