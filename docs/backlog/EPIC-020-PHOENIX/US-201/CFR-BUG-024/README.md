---
id: CFR-BUG-024
titel: MockStreamlit mist cache decorators (cache_data/cache_resource) → import/cascade test failures
status: OPEN
severity: HIGH
component: testing-infra
owner: platform
gevonden_op: 2025-09-19
canonical: false
last_verified: 2025-09-19
applies_to: definitie-app@v2
---

# CFR-BUG-024: MockStreamlit mist cache decorators → import/cascade failures

## Beschrijving
Tests mocken `streamlit` met een eenvoudig object/MagicMock zonder de decorators `cache_data` en `cache_resource`. Modules die bij import deze decorators toepassen (bijv. `src/utils/container_manager.py`, `src/toetsregels/rule_cache.py`) falen of werken niet correct, waardoor testcollectie en runtime cascade-failures ontstaan.

Voorbeelden:
- `src/utils/container_manager.py:40` gebruikt `@st.cache_resource`
- `src/toetsregels/rule_cache.py:21,72` gebruiken `@st.cache_data`

## Verwacht gedrag
Test‑mocks bieden no‑op decorators voor `st.cache_data` en `st.cache_resource` zodat import en calls in testcontext veilig passeren.

## Reproduceren
1) Zet een minimale MockStreamlit zonder decorator‑methods in `sys.modules['streamlit']`
2) Importeer `src/utils/container_manager.py` in een test
3) Importerror/AttributeError treedt op, of decoratie wordt als attributetoegang behandeld → failures

## Oplossing
- Voeg centrale test‑mock toe: `tests/mocks/streamlit_mock.py` met no‑op implementaties:
  ```python
  class MockStreamlit:
      def __init__(self):
          self.session_state = {}
      def cache_data(self, **kwargs):
          return lambda f: f
      def cache_resource(self, **kwargs):
          return lambda f: f
  ```
- Gebruik de mock vroeg in tests (conftest.py of per test) vóór import van modules die Streamlit gebruiken.

## Acceptatiecriteria
- Import van `container_manager` en `rule_cache` werkt in tests zonder echte Streamlit.
- Geen AttributeError op `cache_data`/`cache_resource` tijdens testcollectie en runtime.

## Relatie
- Gerelateerd aan US-201 (ServiceContainer caching) — decorators geïntroduceerd; tests moeten dit ondersteunen.
- Zie ook CFR-BUG-023 (UI‑dependencies buiten UI) — architectuurgate; dit bugrapport dekt specifiek test‑mock infra.

## Tests
- Smoke: import `container_manager` in een test met MockStreamlit → geen error.
- E2E: volledige testsuite kan verzamelen en doorlopen tot eerste functionele assertions.

