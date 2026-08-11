# BATCH-166 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 7/7 bereiken, 5882/5882 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documenten zijn gelezen; provider-, parallelisatie-, classifier-, compliance- en SQLite-concurrencycontracten zijn veilig offline gereproduceerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B166-001 — P2 — Provider-weighting validator cannot detect the double-weighting defect it claims to exclude

**Bewijs:** The active executive summary presents scripts/validate_provider_weighting.py as an automated four-part architecture validation and later marks all checks and tests passed. At immutable base b958ddb, the script's only weighting assertion is all(confidence <= 1.0) after a live lookup (script lines 23-63); it neither inspects lookup weighting nor proves that ranking applies a weight exactly once. A score double-weighted from 0.8 to 0.578 still satisfies that predicate. All four named test paths and the named ADR are absent from the base tree.

**Reproductie:** Load scripts/validate_provider_weighting.py from base b958ddb, replace ModernWebLookupService with an offline fake returning one result with confidence 0.578, and await test_no_double_weighting(); it returns True and prints the score as valid. Independently run git cat-file -e for the four paths in lines 257-258 and the ADR in line 246; all are missing.

**Aanbevolen oplossing:** Replace the live smoke script with credential-free structural and contract tests that compare raw provider confidence with the final ranked score and prove exactly one weighting step. Fail on missing artifacts, remove the validated/production-ready status until the gates exist, and keep network smoke checks separate and explicitly optional.

## Deduplicaties en afwijzingen

- De provider-validatorrelatie met B106-007 is vastgelegd; het zelfstandige false-releasebewijs blijft één finding.

## Niet getest

- Geen echte AI/providers/netwerk/credentials, productiedata, juridische certificering, browser/UI/a11y of live traffic-concurrency.
