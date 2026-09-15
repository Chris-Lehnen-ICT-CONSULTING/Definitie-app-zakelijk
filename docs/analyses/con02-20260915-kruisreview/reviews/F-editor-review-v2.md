## Verdict: changes required

Three remaining findings. **No product-file drift during this review.**

### 1. P1 — Apply overwrites unsaved user text

[definition_edit_tab.py:1240](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/ui/components/definition_edit_tab.py:1240)

**Trigger:** Create a proposal, edit the definition without saving, then click Apply with autosave disabled or before its next save.

`ongewijzigd` disables Request but is not passed to `_render_voorstel`. Apply remains enabled, validates against the stored original, commits the proposal, and stages its text. The next render overwrites the unsaved widget value at line 518. Neither the preserved original nor proposal history contains those intervening edits.

**Fix:** Block Apply while the editor contains unsaved changes, with the same check in its handler. The current full-editor AppTest does not exercise this sequence.

### 2. P1 — Cached session verdict bypasses a newer expert correction

[definition_edit_service.py:753](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/definition_edit_service.py:753)

**Trigger:** Validate a semantic failure in the editor, then correct that part to `pass` through the expert UI. Reload the editor’s record while retaining `edit_last_validation`.

`bronbasis_van_record` accepts the old composite CON-02 result solely because its fingerprint matches. That fingerprint excludes record version and review. Consequently, F ignores the newly stored correction and can reserve/generate against the superseded failure. The reverse direction can suppress a legitimate request.

The displayed-version guard does not resolve this: after refreshing to the current version, the old validation remains cached.

**Fix:** Replay any reusable session assessment against the **current stored review and version**. The existing correction test passes `huidig_resultaat=None`, so it misses this path.

### 3. P2 — Empty semantic claims still qualify as an actionable deficiency

[source_proposal_service.py:336](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/source_proposal_service.py:336)

**Trigger:** C returns `semantic_support=fail`, a verified quotation, and `claims=[]`, for example with a conflict description rather than a concrete deficient feature.

`if claims and not any(...)` skips the rejection for an empty list and returns `defective_definition`. C permits an evidenced failure with empty claims; its additional claim-consistency guard applies to positive verdicts.

This still consumes the single attempt without identifying an actionable semantic deficiency.

**Fix:** Require an identified negative semantic claim with associated evidence; absence must stop before reservation.

## F1–F8 disposition

| Finding | Current disposition |
|---|---|
| F1 | **Partially fixed:** nonsemantic failures and cross-part evidence pooling stopped; findings 2–3 remain. |
| F2 | **Original crash closed:** pending widget update precedes construction; real full-editor Apply/reload test exists. Unsaved-input loss is finding 1. |
| F3 | **Original trigger closed:** UI transports displayed versions for request/apply/reject; service checks version and editability before calls. |
| F4 | **Original trigger closed:** prompt preserves existing citations/names; corresponding removal guards and regression exist. |
| F5 | **Closed:** matching retains original source ID plus metadata, including A/B-only differences and collision variants. |
| F6 | **Closed for reviewed triggers:** C validates assessment receipts; sent content, truncation, original content, missing and invalid receipts have distinct presentation. |
| F7 | **Closed:** malformed fields and unexpected service errors reach durable error finalization. |
| F8 | **Closed:** current D adapter supplies the receipt; zero-use transport regression checks no reservation/model call. |

Expert correction controls cover both directions, bound evidence, actor/version, replacement notice and original AI verdict. The gate evaluates corrected status without broadly skipping `source_review`. The remaining correction issue is the cached proposal path above.

Injected repository usage for editor examples is corrected. DEF-630’s `None` score block remains intact.

## Evidence limits

This was static review; **I executed no tests or application imports**.

Inspected retained evidence:

- [F5/F6 targeted log](/tmp/DEF-743-ui-manual-f56-targeted.log): `pytest exit=0`.
- [Earlier fix targeted log](/tmp/DEF-743-ui-manual-fix-targeted.log): `pytest exit=0`.
- Corresponding lint logs report Ruff and Black exit 0.

The actual AppTest includes full-editor Apply/reload, expert corrections both ways, A/B source identity and capped assessment content. It does not cover the three findings above. Root’s final canonical gate remains outstanding; **no full-feature Done claim**.

## Independent SHA-256 check

All ten product hashes were identical at review start and end:

```text
c7064dde205bb650a5460553df53d40c264db9cabac160ad7c453743c4bdb96d  src/services/source_proposal_service.py
aa376b1a494839126fbd7487e1fe6a3c53292b6f42d12251579ac8cf69944fcd  src/services/definition_edit_service.py
ef20fb662c5d538a39093a30064105eb25baac6beab1035703c6a8df8f3c3cfe  src/services/definition_workflow_service.py
2a7fcfdd5471828ffa17ff3a474fe8e3c580a6a123c703600c16bb576a7a24cf  src/ui/components/definition_edit_tab.py
2b99f69691493836364f7c5157e3cde783d51e53c3d1979424d7859b2db0a462  src/ui/components/expert_review_tab.py
c3f63803222e7933e754667ca1c4f75955f212cf15383952746613f012013f38  src/ui/components/validation_view.py
2577e998136b686aedecac350c07f70f7c59c5cd32d459f7e5235a85ae700a49  src/ui/components/sources_renderer.py
3faf5cfe1106377f62364a80248e9f92fc35b5d5a6f24dc59f88c4549bdec4f3  src/ui/components/definition_generator_tab.py
8ac1197e803260bcdd72d13f4e097212e3562c98d5932b2a8d76ddb761753d29  src/ui/tabbed_interface.py
23fa120136de57aa3875211c7ae3d2edf2018750f68a9583a5e85b3c76b35e72  src/ui/components/tabs/import_export_beheer/format_exporter.py
```