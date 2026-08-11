# BATCH-169 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 14/14 bereiken, 5879/5879 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documenten zijn gelezen; provider-, parallelisatie-, classifier-, compliance- en SQLite-concurrencycontracten zijn veilig offline gereproduceerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B169-001 — P2 — Active canonical compliance documents mark every control compliant and simultaneously declare NO-GO

**Bewijs:** This canonical active v2 matrix marks AVG, Wjsg, BIO, OWASP and every listed regulation compliant solely from requirement mappings. docs/compliance/COMPLIANCE-GAPS.md is simultaneously canonical, active, v2 and last verified on the same date, but lines 23-75 and 127-166 say SSO, compliant audit logging, data classification, AVG documentation and security testing are missing; lines 360-367 identify five critical gaps and NO-GO without four of them. A requirements cross-reference is not evidence that legal or security controls operate.

**Reproductie:** At base b958ddb inspect the frontmatter of both documents; each says canonical:true, status:active, applies_to:definitie-app@v2 and last_verified:2025-09-08. Compare JUSTICE-COMPLIANCE-MATRIX.md:124-136 with COMPLIANCE-GAPS.md:23-75,127-166,360-367 to obtain compliant and NO-GO for the same control set.

**Aanbevolen oplossing:** Create one authoritative control register with per-control status, scoped evidence, owner, assessment date and residual risk. Treat requirement mapping as applicability rather than proof of compliance, archive contradictory snapshots, and make documentation validation reject multiple active canonical conclusions for the same release.

### B169-002 — P2 — Unique-index design relies on a non-atomic application duplicate check

**Bewijs:** The design removes the database uniqueness invariant while claiming application logic maintains data integrity, later rating integrity loss LOW and saying users must explicitly confirm duplicates. In production src/database/definitie_crud.py:39-70, find_duplicates executes before and outside the insert transaction. Once migration 009 removes idx_definities_unique_full, concurrent creates can both observe no duplicate and then both insert without allow_duplicate=True. A two-repository barrier repro produced ids 3 and 4, no exceptions, index count 0 and two identical active rows.

**Reproductie:** Initialize a temporary database at base b958ddb and create two DefinitieRepository instances. Wrap each find_duplicates call so it records its empty result and waits at a threading.Barrier, then concurrently call create_definitie with identical begrip/context/category/wettelijke_basis and allow_duplicate=False. Query the database afterward: both calls succeed and two matching rows exist while idx_definities_unique_full is absent.

**Aanbevolen oplossing:** Retain a database-enforced invariant that matches the intended version/current-record semantics, or serialize duplicate-check plus insert in one BEGIN IMMEDIATE transaction and handle conflict explicitly. Make intentional duplicates/version creation a separate audited API and add a deterministic concurrent regression test.

## Deduplicaties en afwijzingen

- Migratie- en WAL-defecten dedupliceren naar B085/B163; de compliancecontradictie en actuele duplicate-race zijn zelfstandig.

## Niet getest

- Geen echte AI/providers/netwerk/credentials, productiedata, juridische certificering, browser/UI/a11y of live traffic-concurrency.
