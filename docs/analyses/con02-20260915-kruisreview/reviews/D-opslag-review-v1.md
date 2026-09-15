## Findings

**Four actionable findings. Package D needs corrections.**

### 1. P1 — Applying a proposal leaves the previous validation issues active

[definitie_crud.py:1348](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/database/definitie_crud.py:1348)

`apply_source_proposal()` stores the full result in `proposal.applied.validation`, but updates only the text, generation registration and score. It never updates `validation_issues`.

**Trigger:** apply a proposal whose full revalidation finds a new violation, or resolves an existing one. After reload, `Definition.metadata["validation_issues"]` still contains the original issues. The actual [expert-review reader](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/ui/components/expert_review_tab.py:1050) can therefore display “Geen validatie issues gevonden” despite new violations; bulk export likewise reads the old column.

**Correction:** atomically publish the new candidate’s validation issues alongside its full result, preserving historical issues/reviews separately. This does not require changing the DEF-630 score gate.

### 2. P2 — Source or peildatum edits reset the durable proposal budget

[definitie_crud.py:614](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/database/definitie_crud.py:614)

`_bronbewijs_samenvoegen()` preserves `generation_identity` only when sources and peildatum are unchanged.

**Trigger:** consume a proposal attempt, reload the definition, change `metadata["peildatum"]` or a source’s locator, then save. Reload does not restore `generation_id` at metadata’s top level, so this update derives a new identity. `reserve_source_proposal()` compares attempts only against that new identity and permits another reservation without another original generation.

**Correction:** preserve the original generation identity through manual source/context/date corrections. Change it only when an actual new generation is recorded.

### 3. P2 — Export presents stale source assessments as current

[data_aggregation_service.py:110](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/data_aggregation_service.py:110)

Export combines the structural `current` flag with the raw stored assessment, without checking the assessment’s fingerprint or contract version.

**Trigger:** reload a record with positive source assessments, change a source or peildatum, and save without reassessing. D constructs a new evidence envelope containing the old assessment. Its candidate/context match the record, so `current=True`; JSON exports that combination, and TXT renders the old parts as “voldoet” alongside the current-evidence message.

C’s replay rejects that assessment, but these export paths never use replay.

**Correction:** distinguish current source data from current assessment applicability. Use C’s existing binding/replay checks before presenting assessment outcomes, retaining stale evidence as explicitly historical.

### 4. P2 — Record contract adapter drops the receipt needed by proposal diagnosis

[models.py:384](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/database/models.py:384)

`get_contractvelden()` returns sources, assessment and peildatum, but omits the stored `source_receipt`. The actual [proposal caller](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/definition_edit_service.py:750) reads that exact key, so its receipt is always `None`.

**Trigger:** a stored receipt records supplied sources but zero sources used in the generation prompt, while a subsequent assessment provides an evidenced failure. `diagnose_bronbasis()` has an explicit transport-loss guard for this case, but the missing receipt bypasses it and permits a proposal reservation/model call.

**Correction:** return an independent copy of the stored receipt through this record adapter.

## Reviewed manifest

Branch: `feature/DEF-743-con02-bronbasis`
BASE/HEAD: `dc7a70e80a47b750d8800c334805a968857bbd7b`

**Start and end SHA256 hashes matched for all nine files:**

```text
912749a5f7cda53ef15c17a39f309f6ee9acea9f81547776d18c8aad83d46c47  src/database/models.py
e4b3d481a8d622004e31cafd51d1f99f3b3b21fbd9a555246d3b5ea651cfc25a  src/database/definitie_crud.py
728a3a009b49accf117e005b25e8670e0df321386909db620601853eeae5ccf2  src/database/definitie_repository.py
e95822dac25a4aee0a76476b62be6bd1553417dfd22acea44a55b6f7f53458e4  src/services/definition_repository.py
08c2164bfe2455fa5c8fc78b6f6436e662ce1263610a838e066d6a7f3af35b1e  src/services/data_aggregation_service.py
9a8ef62689127534366980df9644404c0724c4291e254370186316e6ddc023c2  src/services/export_service.py
5df7fb241680513cf6fe6423b6c632347d5866f4da0a44aa67afa2ebe9ad7f3d  src/export/export_txt.py
f60f1976a359783f6dc34ff5ec311ae83b8bcb9c36d831d4f3a9bc756c751864  tests/unit/services/test_def743_bronbewijs_persistentie.py
17dae4d1e15500db332dbd1c7869ad9eceb9d81129306b8ccfb913a1d96920a1  tests/unit/services/test_def743_bronbewijs_export.py
```

**Verification limits:** static review of the actual diff, both untracked test files, caller contracts and existing targeted/lint logs. No tests executed, project imports, edits or production DB access. Historical logs do not establish test success for this exact manifest. The known `part_correction` work and separate DEF-630 score gate are not findings.
