# BATCH-087 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 9/9 blobs, 3136/3136 fysieke regels en 144/144 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Exacte scopeselectie: 41 groen, 11 rood, 17 skips en 2 xfails; ieder rood/stale contract is afzonderlijk tegen de productiecaller getraceerd.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B087-001 — P2 — PER-007 performance suite never reaches its criteria

**Bewijs:** Seven cases construct GenerationRequest without required id and the remaining formatter case is skipped.

**Reproductie:** Run the file: seven TypeErrors and one skip.

**Aanbevolen oplossing:** Use a canonical valid request factory and current context/formatter flow before measuring PER-007 invariants.

### B087-002 — P3 — Rule-cache performance test patches after singleton caches are warm

**Bewijs:** The suite discards measured times, never verifies loader call count and receives the real 53-rule cache instead of TEST-01.

**Reproductie:** Run the focused file: the cache-used case fails with production rules.

**Aanbevolen oplossing:** Reset every cache layer, inject the loader and assert one load plus explicit hit/miss behavior.

### B087-003 — P3 — Performance suites retain stale skips and measure test sleeps

**Bewijs:** Across the assigned performance files seventeen tests skip, two xfail and multiple green API timings never use their patched client.

**Reproductie:** Run the group and instrument the fake client; the timing cases pass without production calls.

**Aanbevolen oplossing:** Keep deterministic service-level measurements and remove or repair obsolete skips and xfails.

### B087-004 — P2 — Category regeneration regression targets a removed UI method

**Bewijs:** The test calls removed DefinitionGeneratorTab._trigger_regeneration_with_category; the companion flow uses the wrong key, omits request id and prints mismatches.

**Reproductie:** Run both files: regeneration raises AttributeError and complete flow skips.

**Aanbevolen oplossing:** Exercise the current CategoryRenderer flow with valid request fixtures and hard assertions.

### B087-005 — P3 — Legacy activation test converts prompt failures into a pass

**Bewijs:** The test catches prompt-building exceptions and returns a boolean that pytest ignores.

**Reproductie:** Force build_prompt to raise: output reports failure but pytest marks the case passed.

**Aanbevolen oplossing:** Let unexpected exceptions propagate and assert prompt content and selected strategy.

## Niet getest

- Geen live Streamlitbrowser, externe provider, performancebelasting of productiegegevens; tests en callers zijn lokaal gevolgd.
