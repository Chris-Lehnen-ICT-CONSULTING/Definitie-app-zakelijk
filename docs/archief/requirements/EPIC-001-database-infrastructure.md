# Epic 1: Database & Infrastructure Stabilisatie

**Epic Goal**: Stabiliseer de technische basis voor betrouwbare multi-user toegang zonder data verlies of locks.

**Business Value**: Voorkomt productie issues, maakt applicatie schaalbaar voor meerdere gebruikers.

**Total Story Points**: 7

**Target Sprint**: 1

## Stories

### STORY-001-01: Enable SQLite WAL Mode

**Story Points**: 3

**Als een** developer
**wil ik** WAL mode activeren voor de SQLite database
**zodat** meerdere gebruikers tegelijk kunnen lezen zonder locks.

#### Acceptance Criteria
- [ ] PRAGMA journal_mode=WAL uitgevoerd bij startup
- [ ] Connection string aangepast met juiste settings
- [ ] Geen "database is locked" errors bij 5 concurrent reads
- [ ] Rollback plan gedocumenteerd

#### Technical Notes
```python
# In database configuration
engine = create_engine(
    "sqlite:///data/database/definities.db",
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    }
)

# Enable WAL mode
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
```

#### Test Scenarios
1. Start 5 browser tabs tegelijk
2. Genereer definities in alle tabs
3. Verifieer geen lock errors

---

### STORY-001-02: Fix Connection Pooling

**Story Points**: 2

**Als een** developer
**wil ik** proper connection pooling configureren
**zodat** database resources efficiënt gebruikt worden.

#### Acceptance Criteria
- [ ] Pool size: 20, max overflow: 40
- [ ] Connection timeout: 30 seconden
- [ ] Pool pre-ping enabled voor connection health
- [ ] Monitoring voor pool usage

#### Technical Notes
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

#### Dependencies
- SQLAlchemy 2.0+
- Monitoring setup voor pool metrics

---

### STORY-001-03: Database UTF-8 Encoding

**Story Points**: 2

**Als een** developer
**wil ik** UTF-8 encoding forceren voor alle database operaties
**zodat** Nederlandse tekst correct opgeslagen wordt.

#### Acceptance Criteria
- [ ] PRAGMA encoding='UTF-8' actief
- [ ] Alle text columns correct encoded
- [ ] Test met ë, ï, ü, é, à, §, €, © karakters
- [ ] Bestaande data gemigreerd indien nodig

#### Technical Notes
```python
# Force UTF-8 encoding
with engine.connect() as conn:
    conn.execute(text("PRAGMA encoding='UTF-8'"))

# Test special characters
test_chars = "ëïüéà§€©"
```

#### Migration Plan
1. Backup existing database
2. Check current encoding
3. Migrate if needed
4. Verify all data intact

## Definition of Done (Epic Level)

- [ ] Alle 3 stories completed
- [ ] Database ondersteunt 10+ concurrent users
- [ ] Geen encoding issues meer
- [ ] Performance baseline established
- [ ] Documentatie bijgewerkt
- [ ] Rollback procedures getest

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| WAL mode incompatible | High | Test in staging first |
| Data corruption | Critical | Full backup voor migratie |
| Performance degradatie | Medium | Benchmark voor/na |

## Success Metrics

- Zero "database locked" errors in productie
- 100% Nederlandse tekst correct weergegeven
- Response time <100ms voor DB operations
- Support voor 10+ concurrent users

---
*Epic owner: Backend Team*
*Last updated: 2025-01-18*
