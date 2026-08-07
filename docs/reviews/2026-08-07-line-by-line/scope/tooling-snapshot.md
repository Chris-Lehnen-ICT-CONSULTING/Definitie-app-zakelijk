# Reviewtooling-snapshot

- `REVIEW_BASE_SHA`: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- `TOOLING_SHA`: `c514f81d517dac0471bbf4c1a302a5be406193bf`
- tooling commit timestamp: `2026-08-07T12:04:27+02:00`
- applicatiescope: uitsluitend de tree en blobs van `REVIEW_BASE_SHA`
- reviewinfrastructuur: uitsluitend de drie toolblobs van `TOOLING_SHA`
- eerste reviewer: `agent:inventory-tooling`
- onafhankelijke verifier: `agent:inventory-spec-review`

## Verificatiebewijs

- TDD RED: eerst 1 failure/40 skips; daarna 28/31 en 16/16 gerichte regressies rood.
- Finale toolingtests: 108 verzameld, 108 geslaagd, exitcode 0.
- Ruff: `All checks passed!`, exitcode 0.
- Black: drie bestanden ongewijzigd in checkmodus, exitcode 0.
- Onafhankelijke line-by-line herreview: 4.428 regels gelezen; geen resterende P1/P2-bewijsgaten.
- Adversarial verificatie: raw paden, Git-objectdrift, line-/batchpartities, `out_of_scope`, untracked symlinks, externe untracked-root, `SCOPE_SHA`, batchmanifest- en membershiphashes.

De reviewtools maken geen deel uit van de applicatiesnapshot. Hun exacte blob-SHA's en regelaantallen staan in `review-infrastructure.csv`.
