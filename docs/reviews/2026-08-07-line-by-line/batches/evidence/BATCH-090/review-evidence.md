# BATCH-090 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 7/7 blobs, 2321/2321 fysieke regels en 138/138 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Veilige selectie: 21 groen en 7 skips; Brave gaf 3 groen/5 skips en de overige focusrun 17 groen/1 skip, aangevuld met tijdelijke-DB-repro's.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: SQLite-lifecyclewaarschuwingen vallen onder bestaande PILOT-011/B012-bevindingen en zijn niet opnieuw geteld.

## Bevindingen

### B090-001 — P2 — Duplicate integration tests delete from the default application database

**Bewijs:** The fixture obtains the default repository and executes direct DELETE cleanup against data/definities.db before and after every test.

**Reproductie:** Trace get_definitie_repository or patch its constructor; the resolved path is the live default database.

**Aanbevolen oplossing:** Inject a tmp_path database, reset singletons and use rollback or public cleanup APIs.

### B090-002 — P2 — Offline orchestrator test can reach the global examples generator

**Bewijs:** Any sk-* value passes the key guard and, despite other mocks, the real phase calls the process-global examples generator.

**Reproductie:** Use a dummy sk- key with a spy; one global generator call is observed.

**Aanbevolen oplossing:** Inject or disable the generator and keep real-provider probes explicitly opt-in.

### B090-003 — P2 — SRU integration performs real HTTP and includes a vacuous dead-endpoint case

**Bewijs:** The tests have no offline transport guard; the removed Rechtspraak endpoint returns no attempts and still satisfies the upper-bound assertion.

**Reproductie:** Run with network disabled or inspect transport injection; the live path is attempted while the dead scenario passes with zero work.

**Aanbevolen oplossing:** Use fixed XML and mock transport, assert nonempty attempts, and isolate live probes.

### B090-004 — P3 — Brave integration can pass without exercising Brave

**Bewijs:** Five contracts skip when Brave is disabled and the unconditional dedupe case can succeed with Wikipedia alone.

**Reproductie:** Run under default configuration: three pass and five skip.

**Aanbevolen oplossing:** Enable Brave in the fixture, mock providers and assert both source calls and retained records.

### B090-005 — P3 — DEF-154 pipeline fabricates token savings and module reads

**Bewijs:** Old tokens are defined as current plus 100 and modules are labeled readers merely because shared state exists.

**Reproductie:** Replace the implementation with identical output; the constructed reduction remains.

**Aanbevolen oplossing:** Compare a pinned baseline and instrument actual shared-state reads and writes.

### B090-006 — P3 — Definition-save tests neither verify metadata nor concurrency

**Bewijs:** Metadata is fetched without content assertions and a serial list comprehension is described as concurrent saves.

**Reproductie:** Drop metadata or serialize all writes; the assertions remain green.

**Aanbevolen oplossing:** Assert exact metadata roundtrip and run synchronized concurrent writers with separate connections.

## Niet getest

- Geen echte Brave/SRU/AI-call, credentials, productie-DB of browser; data- en timingrepro's gebruikten tijdelijke stores.
