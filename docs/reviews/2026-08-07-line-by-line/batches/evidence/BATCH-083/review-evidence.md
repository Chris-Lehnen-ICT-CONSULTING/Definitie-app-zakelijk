# BATCH-083 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 6/6 blobs, 511/511 fysieke regels en 32/32 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Normale scope gaf 175 groen en 3 skips; de drie geskippte modern-servicecases draaiden offline groen maar één foutpad had een verkeerde oorzaak.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: Productimpact van URL-deduplicatie blijft onder B035-006; B083-004 registreert uitsluitend het regressietestgat.

## Bevindingen

### B083-001 — P2 — Web and document source text is escaped twice before prompt XML

**Bewijs:** Source sanitization HTML-escapes text and the XML formatter escapes the resulting entities again; tests inspect tags and counts but not round-trip text.

**Reproductie:** Pass A & B < C through sanitization and XML formatting; output contains A &amp;amp; B &amp;lt; C.

**Aanbevolen oplossing:** Normalize to safe plain text and escape exactly once at XML serialization; parse the output and assert exact text round-trip.

### B083-002 — P3 — ECLI boost regression accepts zero boost

**Bewijs:** The central assertion uses greater-than-or-equal, so identical base and ECLI scores satisfy the named boost contract.

**Reproductie:** Patch contract conversion to return 0.5 for both records; the test still passes.

**Aanbevolen oplossing:** Require a strict increase and exact boost/cap boundary values.

### B083-003 — P3 — Modern web service suite remains wholly skipped after fixtures returned

**Bewijs:** A module skip still says fixtures were removed although the stubs are present; direct calls pass and the error test succeeds for a constructor TypeError rather than the intended search error.

**Reproductie:** Run normally to see three skips, then invoke the functions offline: all pass but the error path logs SRUServiceStub takes no arguments.

**Aanbevolen oplossing:** Remove the stale skip, implement an explicit raising stub mode and consolidate overlapping suites.

### B083-004 — P3 — URL dedup test accidentally tests content-hash dedup instead

**Bewijs:** Both duplicate URLs also share content_hash h3, so the test cannot distinguish URL deduplication from the implementation's hash-first behavior.

**Reproductie:** Use the same canonical URL with different hashes; two records survive, reproducing existing product finding B035-006.

**Aanbevolen oplossing:** Use distinct or empty hashes and assert the exact retained URL record; keep product impact deduplicated to B035-006.

## Niet getest

- Geen echte webprovider of browser; ranking-, XML- en skipproeven waren offline.
