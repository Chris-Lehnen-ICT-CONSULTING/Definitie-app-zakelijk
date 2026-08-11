# BATCH-144 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 10/10 bereiken, 5909/5909 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable analyses zijn gelezen; prompttests, baseline-CLI-, AST-deletion-, SQL-rollback-, link- en fencecontroles reproduceerden de geregistreerde grenzen.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B144-001 — P2 — Mandatory DEF-155 baseline gate references a missing test and unsupported pytest options

**Bewijs:** The risk report makes pre/post baseline capture a mandatory circular-validation safeguard, but `tests/services/test_definition_generator.py` is absent from the immutable tree and neither `--baseline-capture` nor `--baseline-compare` is registered by pytest. Other decision documents depend on missing `tests/debug/generate_baseline_def126.py` and `measure_tokens_def126.py`, so the published safety gate cannot produce the evidence on which the go/no-go decision relies.

**Reproductie:** Run project Python with `-m pytest -p no:cacheprovider tests/services/test_definition_generator.py --baseline-capture`; pytest exits 4 with `unrecognized arguments: --baseline-capture`, and `git cat-file -e` confirms the test path is absent at base b958ddb.

**Aanbevolen oplossing:** Implement a maintained baseline command and committed fixtures before presenting the gate as mandatory, assert non-empty exact test scope and artifacts, migrate all decision documents to that single command, and make a failed or missing baseline block the refactor.

### B144-002 — P3 — Prompt architecture report describes an obsolete 16-module runtime with ErrorPrevention enabled

**Bewijs:** The report repeatedly states that 16 modules are registered and that ErrorPreventionModule actively injects context. At the immutable base, ModularPromptAdapter registers 15 modules and explicitly leaves ErrorPreventionModule disabled as redundant (src/services/prompts/modular_prompt_adapter.py:15-26,52-130). The report is dated but not marked superseded and ends as ready for implementation planning, so its central context-flow model no longer describes production.

**Reproductie:** Instantiate `get_cached_orchestrator()` offline with `PYTHONPATH=src`; `len(o.modules)` is 15 and `"error_prevention" in o.modules` is false. Compare that output with the module list and execution model at lines 83-147.

**Aanbevolen oplossing:** Mark the report as a historical snapshot and link to current architecture, or regenerate the module inventory and context-flow diagram from the registered runtime modules; add an architecture-doc test that compares documented IDs with the adapter registry.

### B144-003 — P2 — DEF-156 analysis conflates source-code deduplication with 2,800 runtime prompt-token savings

**Bewijs:** The archaeology report claims that consolidating five duplicated Python implementations saves about 2,800 tokens, 39% of the generated prompt budget, and repeats that ROI at lines 823-832. But the completed Phase-1 report states the refactor preserved byte-for-byte identical output (`DEF-156-PHASE-1-RESULTATEN.md:11,82-87,296`). A byte-identical prompt has an identical token count; the refactor removed source duplication while still emitting all five distinct rule categories.

**Reproductie:** Compare the claimed runtime token reduction with the later report's byte-identical-output assertion. For any deterministic tokenizer, identical prompt bytes necessarily yield the same token sequence and count, so 2,800 runtime tokens cannot have been saved by this refactor.

**Aanbevolen oplossing:** Separate source LOC/token metrics from generated-prompt metrics, retract the 2,800-token and 39% runtime claims, and require before/after serialized prompts plus tokenizer version and measured counts for every prompt-budget assertion.

### B144-004 — P2 — Documented data rollback mutates the default database and then cannot apply its recovery status

**Bewijs:** The runbook targets data/definities.db directly. Its selection reads a nonexistent generation_metadata column; CREATE TABLE IF NOT EXISTS definities_rollback_backup can retain an unversioned stale snapshot; and the later UPDATE writes nonexistent notes plus status needs_regeneration, while schema.sql permits only imported, draft, review, established or archived. The referenced scripts/regenerate_definitions.py also does not exist.

**Reproductie:** Create an in-memory SQLite table with the canonical status CHECK and one row, execute the documented backup statement, then execute the documented UPDATE: the backup table persists with one row but the UPDATE fails the status CHECK (and against the full schema fails earlier on missing columns), leaving a partial recovery attempt.

**Aanbevolen oplossing:** Never target the default database from a copied runbook. Require an explicitly selected verified backup and dry-run, validate the canonical schema and workflow statuses, execute backup and mutation in one transaction with immutable audit metadata, and add a tested restoration/postcondition path that rolls back atomically on any mismatch.

## Deduplicaties en afwijzingen

- Bekende return-value testwarnings dedupliceren naar B054-001; toekomstige voorstelbestanden zijn alleen als missing gemeld wanneer ze een verplichte bestaande gate zouden vormen.

## Niet getest

- Geen externe URLs/netwerk, echte API/credentials/productiedata, daadwerkelijke git/sed/database-mutaties of historische performancebenchmarks.
