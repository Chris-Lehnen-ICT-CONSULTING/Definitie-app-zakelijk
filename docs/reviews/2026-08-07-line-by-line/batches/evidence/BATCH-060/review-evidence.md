# BATCH-060 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 7/7 blobs, 2178/2178 fysieke regels en 144/144 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Primaire dummy-clientrun over B059-B061: 251 groen, 1 skip en 1 verwachte xfail; export-, repository- en testbereikproeven zijn offline uitgevoerd.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B060-001 — P2 — Single-definition exports collide within one second

**Bewijs:** The tests perform one export only; filenames use a second-resolution timestamp and normal write mode.

**Reproductie:** Freeze the clock and export the same term twice; both paths are equal and only the second content remains.

**Aanbevolen oplossing:** Use a collision-proof identifier with exclusive or atomic creation and test two JSON and CSV exports in one clock tick.

### B060-002 — P2 — Repository get masks database failures as not-found

**Bewijs:** The test explicitly expects every backend exception to become None, identical to a successful lookup miss.

**Reproductie:** Make get_definitie raise 'database locked'; DefinitionRepository.get returns None and edit callers report that the definition does not exist.

**Aanbevolen oplossing:** Raise a typed repository or connection error for backend failures and reserve None for a proven no-row result.

### B060-003 — P3 — Draft race test never reaches its injected conflict

**Bewijs:** The exact draft is created first, so the second call returns on its initial SELECT before the second-connection failure injection.

**Reproductie:** Count _get_connection calls; both IDs match but the injected second call is never reached.

**Aanbevolen oplossing:** Model an initially empty SELECT followed by a competing INSERT and assert the IntegrityError recovery query actually runs.

### B060-004 — P3 — Lazy evaluation test contains no production call or assertion

**Bewijs:** The test defines two local classes and exits without constructing a validator, invoking behavior or asserting anything.

**Reproductie:** Replace the production lazy path with any behavior; this test remains green because it executes none of it.

**Aanbevolen oplossing:** Invoke the real lazy computation and assert zero work for non-consumers and exactly one computation for consumers.

## Niet getest

- Geen productiedatabase of live exportdirectory; alle writes bleven in tijdelijke directories en browser-UX is niet getest.
