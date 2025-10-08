# SRU XML Parsing Analysis

**Datum:** 2025-10-08
**Auteur:** Claude Code (Analyse Specialist)
**Context:** Onderzoek naar waarom SRU endpoints geen resultaten opleveren

## Executive Summary

De SRU service (`src/services/web_lookup/sru_service.py`) heeft een **kritiek namespace probleem** waardoor SRU 2.0 responses niet correct worden geparsed. Dit verklaart waarom bepaalde endpoints (met name Wetgeving.nl/BWB) geen resultaten opleveren ondanks succesvolle HTTP 200 responses.

**Impact:** 🔴 HIGH - SRU 2.0 endpoints worden volledig gemist
**Fix Complexity:** 🟢 LOW - Één regel aanpassing in namespace dictionary

---

## Probleem Analyse

### 1. Namespace Mismatch (KRITIEK)

**Locatie:** `src/services/web_lookup/sru_service.py`, regel 749-755

```python
# Huidige code (INCORRECT voor SRU 2.0)
namespaces = {
    "srw": "http://www.loc.gov/zing/srw/",  # ← SRU 1.2 namespace
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "gzd": "http://overheid.nl/gzd",
}

# Records zoeken
records = root.findall(".//srw:record", namespaces)  # ← FAILS voor SRU 2.0
```

**Probleem:**
- SRU 1.2 gebruikt: `http://www.loc.gov/zing/srw/`
- SRU 2.0 gebruikt: `http://docs.oasis-open.org/ns/search-ws/sruResponse` ← **ANDERE namespace!**

**Gevolg:**
- `findall(".//srw:record", namespaces)` retourneert **lege lijst** voor SRU 2.0 responses
- Code denkt dat er geen records zijn → `return []`
- Fallback local-name logica wordt NOOIT bereikt

### 2. Test Bewijs

Debug script (`scripts/debug_sru_parsing.py`) toont aan:

```
TEST: SRU 2.0 Response (OAI-DC)
Zoeken naar records...
  Gevonden met namespace prefix (1.2): 0 records  ← FAIL
  Gevonden met namespace prefix (2.0): 1 records  ← SUCCESS

RESULTAAT: ❌ FAIL
  Records gevonden zonder namespace, maar niet met namespace prefix
```

**Bewijs:**
- SRU 1.2 namespace: 0 records gevonden
- SRU 2.0 namespace: 1 record gevonden
- Data zit ER wel, maar wordt NIET gevonden door huidige code

### 3. Betreffende Endpoints

**SRU 2.0 endpoints (BROKEN):**
- ✅ Wetgeving.nl (BWB): `https://zoekservice.overheid.nl/sru/Search` (SRU 2.0)
  - Config: `sru_version: "2.0"`
  - Verwacht: records
  - Werkelijk: lege lijst door namespace mismatch

**SRU 1.2 endpoints (WORKING):**
- ✅ Overheid.nl: `https://repository.overheid.nl/sru` (SRU 1.2)
- ✅ Rechtspraak.nl: `https://zoeken.rechtspraak.nl/SRU/Search` (SRU 1.2)
- ✅ Overheid Zoekservice (met gzd): `https://zoekservice.overheid.nl/sru/Search` (SRU 1.2)

---

## Oplossingen

### Oplossing 1: Multi-Namespace Record Search (AANBEVOLEN)

**Strategie:** Probeer beide SRU namespaces bij record search

```python
def _parse_sru_response(self, xml_content: str, term: str, config: SRUConfig) -> list[LookupResult]:
    """Parse SRU XML response naar LookupResult objecten."""
    try:
        root = ET.fromstring(xml_content)

        # SRU namespace variants (1.2 en 2.0)
        namespace_variants = [
            {
                "srw": "http://www.loc.gov/zing/srw/",  # SRU 1.2
                "dc": "http://purl.org/dc/elements/1.1/",
                "dcterms": "http://purl.org/dc/terms/",
                "gzd": "http://overheid.nl/gzd",
            },
            {
                "srw": "http://docs.oasis-open.org/ns/search-ws/sruResponse",  # SRU 2.0
                "dc": "http://purl.org/dc/elements/1.1/",
                "dcterms": "http://purl.org/dc/terms/",
                "gzd": "http://overheid.nl/gzd",
            }
        ]

        # Probeer beide namespaces
        records = []
        namespaces = None
        for ns_variant in namespace_variants:
            records = root.findall(".//srw:record", ns_variant)
            if records:
                namespaces = ns_variant  # Gebruik werkende namespace voor parse_record
                break

        if not records:
            logger.warning(
                f"No records found in SRU response from {config.name}. "
                f"Response preview: {xml_content[:200]}"
            )
            return []

        results = []
        for record in records:
            result = self._parse_record(record, term, config, namespaces)
            if result:
                results.append(result)

        # ... rest van de method
```

**Voordelen:**
- ✅ Backward compatible (SRU 1.2 blijft werken)
- ✅ Forward compatible (SRU 2.0 wordt ondersteund)
- ✅ Minimale code wijziging
- ✅ Geen performance impact

**Nadelen:**
- Geen

### Oplossing 2: Namespace Auto-Detection (ALTERNATIEF)

**Strategie:** Detecteer welke namespace gebruikt wordt in de response

```python
def _detect_sru_namespace(self, root: ET.Element) -> dict[str, str]:
    """Detecteer SRU namespace variant uit XML root."""
    # Check root element namespace
    root_ns = root.tag.split('}')[0][1:] if '}' in root.tag else ""

    if "sruResponse" in root_ns:  # SRU 2.0 namespace
        return {
            "srw": "http://docs.oasis-open.org/ns/search-ws/sruResponse",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/",
            "gzd": "http://overheid.nl/gzd",
        }
    else:  # SRU 1.2 namespace (default)
        return {
            "srw": "http://www.loc.gov/zing/srw/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/",
            "gzd": "http://overheid.nl/gzd",
        }
```

**Voordelen:**
- ✅ Dynamische namespace detectie
- ✅ Future-proof voor nieuwe SRU versies

**Nadelen:**
- ⚠️ Complexer dan Oplossing 1
- ⚠️ Edge cases mogelijk bij malformed XML

---

## Debug Logging Verbeteringen

### Probleem 2: Onvoldoende Debug Visibility

**Huidige situatie:**
- Bij `records = []` wordt gelogd: `"Parsed {len(results)} results from {config.name}"`
- Geen info over WAAROM er geen records zijn
- Geen raw XML logging bij parse failures

**Aanbevolen logging toevoegingen:**

#### 1. Log Raw XML bij Empty Results

```python
def _parse_sru_response(self, xml_content: str, term: str, config: SRUConfig) -> list[LookupResult]:
    try:
        root = ET.fromstring(xml_content)
        # ... namespace en record search ...

        if not records:
            # Log raw XML preview voor debugging
            logger.warning(
                f"No records found in SRU response from {config.name}. "
                f"XML preview: {xml_content[:500]}",
                extra={
                    "endpoint": config.name,
                    "term": term,
                    "xml_length": len(xml_content),
                }
            )
            return []
```

#### 2. Log SRU Diagnostics (al geïmplementeerd, maar niet prominent genoeg)

**Locatie:** regel 270-302 (in `_try_query`)

De diagnostic parsing is al aanwezig, maar wordt alleen gebruikt in attempt records.

**Verbetering:**
```python
# Na regel 347 (waar diagnostics worden ge-extract)
diag = _extract_diag(txt)
if diag:
    logger.warning(
        f"SRU diagnostic from {config.name}: {diag.get('diag_message')}",
        extra={
            "diagnostic_uri": diag.get("diag_uri"),
            "diagnostic_details": diag.get("diag_details"),
            "endpoint": config.name,
        }
    )
```

#### 3. Log Namespace Mismatch Detection

```python
# In _parse_sru_response, bij namespace detection
detected_ns = set()
for elem in root.iter():
    if '}' in elem.tag:
        ns = elem.tag.split('}')[0][1:]
        detected_ns.add(ns)

logger.debug(
    f"Detected namespaces in SRU response: {detected_ns}",
    extra={"endpoint": config.name}
)
```

---

## Test Coverage

### Bestaande Tests

**SRU parsing tests:**
- ✅ `tests/web_lookup/test_sru_gzd_parser.py` - Test GZD local-name parsing
- ✅ `tests/services/web_lookup/test_sru_integration.py` - Integration tests
- ✅ `tests/services/web_lookup/test_sru_circuit_breaker.py` - Circuit breaker behavior

**Ontbrekende test:**
- ❌ **SRU 2.0 namespace handling** - NIET getest!

### Nieuwe Test (AANBEVOLEN)

```python
# tests/web_lookup/test_sru_namespace_variants.py
import pytest


def test_sru_20_namespace_parsing():
    """Test dat SRU 2.0 responses correct worden geparsed."""
    from services.web_lookup.sru_service import SRUConfig, SRUService

    svc = SRUService()
    cfg = SRUConfig(
        name="Test SRU 2.0",
        base_url="https://example.com/sru",
        default_collection="",
        record_schema="oai_dc",
        sru_version="2.0",
    )

    # SRU 2.0 response met correcte namespace
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <srw:searchRetrieveResponse xmlns:srw="http://docs.oasis-open.org/ns/search-ws/sruResponse">
      <srw:version>2.0</srw:version>
      <srw:numberOfRecords>1</srw:numberOfRecords>
      <srw:records>
        <srw:record>
          <srw:recordData>
            <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                        xmlns:dc="http://purl.org/dc/elements/1.1/">
              <dc:title>Wetboek van Strafrecht</dc:title>
              <dc:description>Test description</dc:description>
              <dc:identifier>https://example.com/sr</dc:identifier>
            </oai_dc:dc>
          </srw:recordData>
        </srw:record>
      </srw:records>
    </srw:searchRetrieveResponse>"""

    results = svc._parse_sru_response(xml, term="wetboek", config=cfg)

    assert len(results) > 0, "SRU 2.0 responses should be parsed"
    assert results[0].metadata.get("dc_title") == "Wetboek van Strafrecht"


def test_sru_12_namespace_parsing():
    """Test dat SRU 1.2 responses correct blijven werken (backward compat)."""
    from services.web_lookup.sru_service import SRUConfig, SRUService

    svc = SRUService()
    cfg = SRUConfig(
        name="Test SRU 1.2",
        base_url="https://example.com/sru",
        default_collection="",
        record_schema="dc",
        sru_version="1.2",
    )

    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
      <srw:version>1.2</srw:version>
      <srw:numberOfRecords>1</srw:numberOfRecords>
      <srw:records>
        <srw:record>
          <srw:recordData>
            <dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/">
              <dc:title>Gemeentewet</dc:title>
              <dc:description>Test description</dc:description>
            </dc:dc>
          </srw:recordData>
        </srw:record>
      </srw:records>
    </srw:searchRetrieveResponse>"""

    results = svc._parse_sru_response(xml, term="gemeentewet", config=cfg)

    assert len(results) > 0, "SRU 1.2 responses should still work"
    assert results[0].metadata.get("dc_title") == "Gemeentewet"
```

---

## Implementation Checklist

### High Priority (Fix namespace issue)
- [ ] Implementeer multi-namespace record search (Oplossing 1)
- [ ] Voeg test toe voor SRU 2.0 namespace parsing
- [ ] Test met live Wetgeving.nl endpoint
- [ ] Verify backward compatibility met SRU 1.2 endpoints

### Medium Priority (Improve debugging)
- [ ] Log raw XML preview bij empty results
- [ ] Log SRU diagnostics op WARNING level (niet alleen in attempts)
- [ ] Log detected namespaces op DEBUG level
- [ ] Voeg `xml_preview` toe aan attempt records bij parse failures

### Low Priority (Nice to have)
- [ ] Voeg metrics toe voor namespace variant usage
- [ ] Create dashboard voor SRU endpoint health per namespace variant
- [ ] Documenteer SRU namespace verschillen in docstrings

---

## Root Cause

**Waarom is dit niet eerder opgevallen?**

1. **Test Coverage Gap:** Geen test voor SRU 2.0 namespace variant
2. **Silent Failure:** Code retourneert lege lijst (geen exception), lijkt normaal gedrag
3. **Fallback Masking:** Local-name fallback logica werkt WEL voor content, maar records worden nooit gevonden
4. **Circuit Breaker:** Bij lege results triggert circuit breaker → lijkt alsof endpoint gewoon leeg is

**Wanneer geïntroduceerd?**
- Waarschijnlijk bij initiële implementatie (namespace dict was altijd SRU 1.2)
- Wetgeving.nl endpoint met SRU 2.0 toegevoegd zonder namespace fix

---

## Related Issues

**Mogelijk gerelateerde problemen:**
- US-XXX: "Wetgeving.nl levert geen resultaten" (als dit bestaat)
- Performance: Circuit breaker triggert vroeg → endpoints lijken leeg
- Metrics: False negatives in endpoint health monitoring

**Volgende stappen:**
1. Fix namespace issue (hoogste prioriteit)
2. Voeg debug logging toe
3. Voeg integration test toe met live Wetgeving.nl endpoint
4. Monitor of Wetgeving.nl resultaten gaat opleveren na fix

---

## Debug Scripts

**Beschikbare tools:**
- `scripts/debug_sru_parsing.py` - Test parsing met mock XML responses
- `scripts/test_live_sru_response.py` - Test live endpoints en toon raw responses

**Gebruik:**
```bash
# Test parsing logica
python scripts/debug_sru_parsing.py

# Test live endpoints (requires network)
python scripts/test_live_sru_response.py
```

---

## Conclusie

Het SRU parsing probleem is een **klassiek namespace mismatch issue**:
- SRU 2.0 gebruikt andere namespace dan SRU 1.2
- Code probeert alleen SRU 1.2 namespace
- Result: alle SRU 2.0 endpoints lijken leeg

**Fix: 1 regel code aanpassing, grote impact op SRU 2.0 endpoint coverage.**

Prioriteit: **HIGH** - direct implementeren.
