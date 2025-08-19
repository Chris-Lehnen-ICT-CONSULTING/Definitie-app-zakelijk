# STORY-001: Database Concurrent Access & Encoding Fixes

## User Story
Als een **developer**
wil ik dat de database concurrent access ondersteunt zonder locks EN dat alle encoding issues opgelost zijn
zodat meerdere gebruikers tegelijk de applicatie kunnen gebruiken zonder errors en alle Nederlandse tekst correct wordt weergegeven.

## Acceptance Criteria
- [ ] SQLite WAL mode geactiveerd voor concurrent reads
- [ ] Connection pooling geconfigureerd met juiste settings
- [ ] UTF-8 encoding geforceerd voor alle database operaties
- [ ] Web lookup module volledig herschreven (5 broken versies consolideren)
- [ ] Geen "database is locked" errors meer bij normaal gebruik
- [ ] Character encoding consistent door hele applicatie
- [ ] Alle "_broken" en "_encoding_issue" files verwijderd

## Technical Notes

### Implementation Approach
1. Update database connection string met WAL mode
2. Configure SQLAlchemy connection pool settings
3. Add encoding parameters to all text operations
4. **CRITICAL: Consolideer web lookup module**
   - Verwijder: `definitie_lookup_broken.py`
   - Verwijder: `definitie_lookup_encoding_issue.py`
   - Verwijder: `bron_lookup_encoding_issue.py`
   - Creëer één werkende `web_lookup_service.py`
5. Add retry logic for transient locks

### Code Changes Required
```python
# Database configuration
engine = create_engine(
    "sqlite:///data/database/definities.db",
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    },
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    encoding='utf-8'  # Force UTF-8
)

# Enable WAL mode
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
    conn.execute(text("PRAGMA encoding='UTF-8'"))

# Web lookup fix
async def lookup_definition(term: str) -> List[Dict]:
    async with httpx.AsyncClient() as client:
        # Ensure proper encoding
        response = await client.get(
            url,
            params={"q": term},
            headers={"Accept-Charset": "utf-8"}
        )
        response.encoding = 'utf-8'  # Force UTF-8 decoding
        return parse_results(response.text)
```

### Dependencies
- SQLAlchemy configuration update
- Complete web lookup service rewrite (niet alleen refactoring)
- Database migration to apply WAL mode
- Remove alle broken/encoding_issue files

## QA Notes

### Test Scenarios
1. **Concurrent Access Test**
   - Open 5 browser tabs simultaneously
   - Generate definitions in all tabs at once
   - Verify no lock errors occur

2. **Encoding Test**
   - Test with special characters: ë, ï, ü, é, à
   - Test with legal symbols: §, €, ©
   - Verify correct display in UI and database

3. **Web Lookup Test**
   - Search for terms with diacritics
   - Verify results display correctly
   - Check database storage of results

### Edge Cases
- Very long definitions (>1000 chars)
- Rapid successive requests from same user
- Database backup while app is running
- Special Unicode characters in legal texts

### Expected Behavior
- Zero "database is locked" errors
- All Dutch characters display correctly
- Web lookup returns properly encoded results
- Database operations complete within 100ms

## Definition of Done
- [ ] Code implemented and peer reviewed
- [ ] Unit tests written and passing
- [ ] Integration tests for concurrent access
- [ ] Manual QA completed
- [ ] Documentation updated
- [ ] No regression in existing functionality

## Priority
**High** - This is a P1 bug affecting core functionality

## Estimated Effort
**5 story points** - 2 days of development work (verhoogd vanwege web lookup rewrite)

## Sprint
Sprint 1 - Quick Wins

---
*Story generated from PRD Epic 1: Quick Wins & Stabilisatie*
