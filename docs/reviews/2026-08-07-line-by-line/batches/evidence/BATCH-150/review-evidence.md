# BATCH-150 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 15/15 bereiken, 5854/5854 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable analyses zijn gelezen; relevante unit-tests, offline runtime- en parserreproducties, documentclaims en secret-shape-scans zijn gecontroleerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B150-001 — P2 — Ready-to-deploy provider runbook targets the wrong checkout and provides an unsafe rollback

**Bewijs:** The runbook hardcodes Chris's original checkout for both deployment and rollback, lists two test paths that do not exist at the immutable base, and rolls back with git checkout HEAD~1 config/web_lookup_defaults.yaml. Checkout of a path replaces index and worktree content without verifying that HEAD~1 is the deployment commit and can discard local configuration edits. The document simultaneously marks the changes deployed and the tests not yet passed.

**Reproductie:** Run the documented pytest tests/services/web_lookup/ command: pytest exits with file or directory not found. From another clone or worktree, resolve the line-201 cd and observe that it selects the original checkout. Git's path-checkout command then sources the config from an unrelated previous commit rather than reverting the documented change.

**Aanbevolen oplossing:** Archive the already-applied plan or regenerate it as a root-agnostic runbook, use the actual test paths, require a clean-worktree and explicit target commit, and roll back the exact change with a reviewed inverse patch or commit revert rather than checkout of HEAD~1.

### B150-002 — P3 — Race-condition index still claims a pending proven defect using test files that no longer exist

**Bewijs:** The index states 100% confidence, fourfold production loading and a pending fix, and tells readers to run two debug tests. Both test paths are absent from the immutable tree. The base cached decorator now contains a function-level lock and double-check; its maintained concurrency test suite passed all seven cases from a writable temporary working directory.

**Reproductie:** Run git cat-file -e for tests/debug/test_cached_decorator_race_condition.py and tests/debug/test_rule_cache_race_condition.py at the review base; both fail. Inspect src/utils/cache.py:238-310 and run tests/unit/utils/test_cached_decorator_concurrency.py from /private/tmp; seven tests pass.

**Aanbevolen oplossing:** Mark the analysis resolved and historical, retain executable reproduction tests when claiming proof, record the exact affected and fixed revisions, and link readers to the maintained concurrency contract and remaining per-key serialization finding B080-002.

## Deduplicaties en afwijzingen

- Het cache-raceproductdefect dedupliceert naar B080-002; de stale analyse blijft als documentfinding staan.

## Niet getest

- Geen externe provider/API/netwerk, echte sleutelwaarden, remote Git-historie, dependency-installatie, destructive rollback of browser/UI-runtime.
