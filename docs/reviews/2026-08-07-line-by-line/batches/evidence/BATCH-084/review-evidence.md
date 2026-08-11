# BATCH-084 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 20/20 blobs, 1726/1726 fysieke regels en 105/105 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Manifest-/marker-/collectieproeven bewezen de niet-ontdekte bestanden en late netwerkfixture; toepasselijke normale tests vielen binnen 175 groen en 3 skips.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B084-001 — P3 — Import smoke file collects no tests while printing success

**Bewijs:** The filename misses test_*.py, defines no test function and imports no application module, yet prints that all modules load.

**Reproductie:** Run the file explicitly with pytest; zero tests are collected.

**Aanbevolen oplossing:** Replace it with a parametrized import smoke under a discoverable filename, or remove it with explicit approval.

### B084-002 — P3 — Test README reports obsolete paths and evidence

**Bewijs:** The document reports 2025-era counts and root files that no longer describe the current suite; current unit collection has thousands of items and collection errors.

**Reproductie:** Compare documented 47-passing claims and paths with current collection and the skipped modern-service suite.

**Aanbevolen oplossing:** Generate volatile metrics from CI or remove counts, and date every retained verification claim.

### B084-003 — P3 — Benchmark fallback fixture is structurally unreachable

**Bewijs:** The detection try block only assigns True and contains no import or operation that can raise, so the fallback path can never be selected.

**Reproductie:** Trace the block with pytest-benchmark absent; no statement in the try can signal absence.

**Aanbevolen oplossing:** Use importlib.util.find_spec or actual plugin/fixture detection and test both installed and absent cases.

### B084-004 — P3 — Outbound-network block starts too late for collection and session setup

**Bewijs:** The hard-block fixture is function-scoped autouse, so imports, collection hooks and earlier session fixtures execute before it; no current collection-time outbound call was proven.

**Reproductie:** Inspect fixture ordering and place a hypothetical import-time socket call before function setup; the fixture cannot intercept it.

**Aanbevolen oplossing:** Enforce the block at process/plugin-hook or OS sandbox level and add a collect-time canary.

## Niet getest

- Geen echte collection-time outbound verbinding gestart; die reachability blijft suspected. Geen browser/a11y.
