# Epic 2: Web Lookup Module Herstel

**Epic Goal**: Consolideer en fix de 5 broken web lookup implementaties tot één werkende service.

**Business Value**: Herstel kritieke functionaliteit voor juridische bronnen lookup.

**Total Story Points**: 10

**Target Sprint**: 1-2

## Context

De web lookup module heeft momenteel 5 verschillende implementaties:
- `definitie_lookup.py`
- `definitie_lookup_broken.py` ❌
- `definitie_lookup_encoding_issue.py` ❌
- `bron_lookup.py`
- `bron_lookup_encoding_issue.py` ❌

Dit moet geconsolideerd worden naar één werkende service.

## Stories

### STORY-002-01: Analyse & Cleanup Broken Files

**Story Points**: 2

**Als een** developer
**wil ik** alle web lookup files analyseren
**zodat** ik weet wat te behouden en wat te verwijderen.

#### Acceptance Criteria
- [ ] Lijst van 5 files met functionaliteit analyse
- [ ] Identificatie van beste implementatie onderdelen
- [ ] Cleanup plan voor broken files
- [ ] Documentatie van encoding issues

#### Analysis Tasks
```bash
# Find all lookup files
find src/web_lookup -name "*lookup*.py" -exec ls -la {} \;

# Check for differences
diff definitie_lookup.py definitie_lookup_broken.py

# Identify encoding issues
grep -n "encoding" *.py
```

#### Expected Output
- Comparison matrix van features per file
- Lijst van te behouden functionaliteit
- Encoding probleem root causes

---

### STORY-002-02: Implementeer Nieuwe Web Lookup Service

**Story Points**: 5

**Als een** developer
**wil ik** één consolidated web lookup service
**zodat** encoding correct werkt voor alle bronnen.

#### Acceptance Criteria
- [ ] Nieuwe `web_lookup_service.py` geïmplementeerd
- [ ] UTF-8 support voor requests en responses
- [ ] Error handling voor network issues
- [ ] Support voor wetten.nl, officielebekendmakingen.nl, rechtspraak.nl

#### Technical Implementation
```python
import httpx
from typing import List, Dict
import logging

class WebLookupService:
    """Consolidated web lookup service met proper encoding."""

    SOURCES = {
        "wetten.nl": {
            "base_url": "https://wetten.overheid.nl",
            "search_endpoint": "/zoeken"
        },
        "officielebekendmakingen.nl": {
            "base_url": "https://www.officielebekendmakingen.nl",
            "search_endpoint": "/zoeken"
        },
        "rechtspraak.nl": {
            "base_url": "https://www.rechtspraak.nl",
            "api_endpoint": "/api/search"
        }
    }

    async def search(self, term: str, source: str) -> List[Dict]:
        """Search with proper UTF-8 handling."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.SOURCES[source]["base_url"] + "/search",
                params={"q": term},
                headers={"Accept-Charset": "utf-8"},
                timeout=30.0
            )
            response.encoding = 'utf-8'
            return self._parse_results(response.text, source)
```

#### Error Handling
- Network timeouts
- Invalid responses
- Encoding errors
- Rate limiting

---

### STORY-002-03: Integreer met UI & Test

**Story Points**: 3

**Als een** gebruiker
**wil ik** web lookup resultaten zien in de UI
**zodat** ik juridische bronnen kan raadplegen.

#### Acceptance Criteria
- [ ] Web Lookup tab volledig functioneel
- [ ] Nederlandse tekst correct weergegeven
- [ ] Loading states en error feedback
- [ ] Resultaten caching voor performance

#### UI Integration
```python
# In web_lookup_tab.py
async def perform_search():
    with st.spinner("Zoeken..."):
        try:
            results = await lookup_service.search(
                term=st.session_state.search_term,
                source=st.session_state.selected_source
            )
            display_results(results)
        except Exception as e:
            st.error(f"Zoeken mislukt: {str(e)}")
```

#### Test Cases
1. Zoek "aansprakelijkheid" in wetten.nl
2. Zoek "gemeente§verordening" (special chars)
3. Zoek "café" (diacritics)
4. Test timeout handling
5. Test empty results

## Definition of Done (Epic Level)

- [ ] Alle 3 stories completed
- [ ] 5 broken files verwijderd
- [ ] 1 werkende service actief
- [ ] Alle Nederlandse karakters correct
- [ ] UI tab volledig functioneel
- [ ] Performance <3 sec per search
- [ ] Unit tests voor encoding

## Migration Plan

1. **Sprint 1**: Analyse & nieuwe service (stories 1-2)
2. **Sprint 2**: UI integratie & cleanup (story 3)

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| External API changes | High | Abstract API interface |
| Rate limiting | Medium | Implement caching |
| Breaking UI | High | Feature flag for rollout |

## Success Metrics

- 100% searches return valid UTF-8
- Zero encoding errors in logs
- Response time <3 seconds
- 3 juridische bronnen werkend

## Cleanup Checklist

- [ ] Remove `definitie_lookup_broken.py`
- [ ] Remove `definitie_lookup_encoding_issue.py`
- [ ] Remove `bron_lookup_encoding_issue.py`
- [ ] Archive working parts van old files
- [ ] Update all imports
- [ ] Update documentation

---
*Epic owner: Backend Team*
*Last updated: 2025-01-18*
