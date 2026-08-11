# BATCH-147 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 12/12 bereiken, 5754/5754 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable analyses zijn gelezen; historische tellingen, ontbrekende suites, shell-/AST-reproducties, linkscans en veilige gate-simulaties zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B147-001 — P2 — Decision-maker entrypoint is based on a grossly incorrect test inventory

**Bewijs:** The report declares the application production-ready and cites 241 test files and only 249 test functions as a strength. At its introducing commit 5e0ce9bf62b3777d446c0920d64588b3e2c347cb, 241 conventional test*.py paths is correct, but the tree contains 2,215 sync/async test-function definitions; 268 is the broader count of all Python files under tests, including helpers and conftest files. docs/analyses/REVIEW_INDEX.md:9-14 directs decision makers to start with this report without a stale-data warning.

**Reproductie:** At commit 5e0ce9bf62b3777d446c0920d64588b3e2c347cb, count conventional test*.py paths under tests (241), all Python paths under tests (268), and sync/async test-function definitions (2,215); compare the function count with lines 71-72 and follow REVIEW_INDEX.md lines 9-14.

**Aanbevolen oplossing:** Replace hand-entered metrics with a generated snapshot that records commit, commands, collection exit code and timestamp; remove the production-ready verdict or add an unmistakable historical/stale banner and point decision makers to current verified gates.

### B147-002 — P2 — Validation phase is marked complete although its only named suite does not exist

**Bewijs:** The checklist marks Phase 3 Validation & Testing COMPLETE and names tests/integration/test_instruction_optimization.py as its validation suite. That path is absent from base b958ddb; pytest --collect-only on the documented path exits 4 with file or directory not found. The checklist's validation-tests-pass item remains unchecked, and related claimed artifacts CLAUDE.md.v4.0 and scripts/rollback_optimization.sh are also absent.

**Reproductie:** Run project Python with pytest -q -p no:cacheprovider --collect-only tests/integration/test_instruction_optimization.py; observe exit code 4. Verify the three named paths with git cat-file -e against b958ddb.

**Aanbevolen oplossing:** Do not mark validation complete until a committed suite collects at least one test and passes on the pinned artifacts. Record the command, commit and output, or relabel this package as an unimplemented historical proposal.

### B147-003 — P2 — Ready-for-approval prompt plan contains a non-executable mutation recipe

**Bewijs:** The Phase-1 block is fenced as bash and presented as the four-hour implementation. bash -n fails at move_section('metadata', ...); move_section, keep_only_positive_examples and consolidate_rules are neither shell commands nor repository scripts. The first sed -i target output/prompt.txt and the referenced ui/definition_detail.py and tests/services/prompts paths are absent from the pinned tree, so the advertised quick-win flow cannot start or verify.

**Reproductie:** Extract lines 307-327 from blob 37ccbac524a6763ab6f0f4d14d7267c158f32a30 and pass them to bash -n; observe a syntax error. Check each named command with command -v/git grep and each path with git cat-file -e against b958ddb; all listed pseudo-commands and target paths are absent.

**Aanbevolen oplossing:** Replace pseudocode with a real reviewed script or clearly label it non-executable. Resolve targets from the repository root, preflight every path, use dry-run/diff output, and require an existing focused test suite before any mutation or push.

## Deduplicaties en afwijzingen

- Alleen als bestaand of voltooid gepresenteerde gates zijn als ontbrekend geregistreerd; toekomstige voorstellen niet.

## Niet getest

- Geen externe URLs/netwerk, destructive commands, echte credentials/productiedata, historische benchmarks of browser/UI-runtime.
