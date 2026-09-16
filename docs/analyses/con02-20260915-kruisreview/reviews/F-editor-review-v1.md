## Verdict: changes required

Independent **static review** against `dc7a70e80` on `feature/DEF-743-con02-bronbasis`. Eight actionable findings:

### F1 — P1: Nonsemantic failures enable text repair

[source_proposal_service.py:244](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/source_proposal_service.py:244)

A valid C assessment with `source_authority=fail` or `reference_quality=fail`, while `semantic_support=pass`, becomes `defective_definition` and enables a proposal. F collects evidence across parts and accepts **any** failing part; it never establishes an actionable semantic deficiency or distinguishes norm/evaluator conflict.

Consequently, requesting help for unsuitable authority or inadequate reference consumes the single durable text-repair attempt, even if the model subsequently refuses. C verifies quotations per part; that does **not** establish a defect in the sentence. Require a semantic finding with associated evidence and an actionable diagnosis before reservation.

### F2 — P1: Successful Apply crashes the full editor after committing

[definition_edit_tab.py:1284](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/ui/components/definition_edit_tab.py:1284)

The full render creates `edit_{id}_definitie` at line 516 before rendering the proposal controls. After D commits successfully, Apply assigns that widget’s session-state key. The installed Streamlit implementation explicitly raises `StreamlitAPIException` for this operation.

The database changes, but refreshing the editor and replacing its validation result are skipped. Stage the update before widget construction or use a callback. The current AppTest renders isolated sections and checks that Apply exists; it does not click Apply in the full editor.

### F3 — P2: Apply substitutes the latest version for the displayed version

[definition_edit_service.py:1055](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/definition_edit_service.py:1055)

Apply accepts no displayed `expected_version`; it rereads the record and passes that fresh version to D. If another session archives the record after the editor loaded it, the cached UI still permits Apply. F does not recheck the current status, and D’s version check succeeds against the freshly supplied version.

This is a caller mismatch: D protects changes during validation, but F discards the user’s displayed-version boundary. Pass and check that version, including current editability.

### F4 — P2: Proposal instructions prohibit valid inline citations

[source_proposal_service.py:307](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/source_proposal_service.py:307)

When repairing another semantic omission in a sentence containing a valid inline citation, the system prompt explicitly instructs the model to include no citation or context name. This contradicts the accepted preservation contract. Output checks only detect newly introduced strings; removing the existing citation passes those checks.

Permit valid existing citations and necessary names/context, and restrict the prohibition to cosmetic additions.

### F5 — P2: Identical passages receive the wrong source identity

[sources_renderer.py:518](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/ui/components/sources_renderer.py:518)

Two distinct sources containing identical passage text share a content hash. `_canonieke_ids` assigns `kandidaten[0]` to both rows. The second row consequently displays the first source’s ID, version, locator and matching AI evidence, alongside its own title/link.

Match the complete canonical source identity; passage equality is insufficient.

### F6 — P2: The displayed passage differs from the assessed passage

[sources_renderer.py:397](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/ui/components/sources_renderer.py:397)

The source list displays only `snippet`/`context`, while C assesses canonical `prompt_content`, then `snippet`/`chunk_text`/`content`. A sanitized or truncated source therefore displays its original passage rather than the actual assessed content. A source containing only `content` or `chunk_text` displays no full passage.

Render the canonical assessed passage explicitly, with the original separately labelled where useful.

### F7 — P2: Malformed structured output leaves a permanent unfinished reservation

[source_proposal_service.py:620](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/source_proposal_service.py:620)

Valid JSON containing `"behouden": 123` raises `TypeError` during iteration, outside the service’s exception handling. The reservation already exists, but `record_source_proposal_outcome` is never reached. The UI catches the exception only in session state; reload leaves `reserved` with no durable error outcome and the attempt consumed.

Validate field types and finalize parsing failures as `error`, preserving the one-attempt limit.

### F8 — P2: Stored receipts never reach transport diagnosis

[definition_edit_service.py:750](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/definition_edit_service.py:750)

F reads `source_receipt` from `record.get_contractvelden()`, but the current D adapter does not return that key. The receipt is available through `get_source_evidence()`.

Thus a stored receipt showing supplied sources but zero sources used never reaches the explicit transport-loss branch. With a subsequent failing assessment, F can instead enable text repair. Read the receipt through the actual D interface.

## Evidence and limits

- No tests, application imports, network calls or database access executed.
- F tests and retained logs were inspected. No complete green F run bound to this reviewed snapshot was established.
- Apply passes the full validation dictionary and assessment to D; no duplicate D-owned persistence finding is raised.
- DEF-630’s `None` score block remains unchanged.
- Human `part_correction` remains the acknowledged integration gap.
- **No full-feature Done claim.**

## Product-file drift

Eight product files retained identical start/end SHA-256 hashes.

`src/ui/components/expert_review_tab.py` changed during review:

```text
start 567d618f07406a399885318a07cd6fe6e3fddb0a28a731c4b8ec93adfc05d5bd
end   0ba6111426b826015c2547b6bd3ed890ae435f47621b3e491608b37d37578968
```

**No approval for the drifting expert file.** The findings above reference unchanged files.