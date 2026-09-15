## Verdict

**One P2 remains in finding 2.** Findings 1, 3 and 4 are closed. Review-history storage and additive contract preservation are verified statically. This is not full-feature approval while C/F remain active.

### P2 — Identical evidence prevents recognition of a new generation

[definitie_crud.py:591](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/database/definitie_crud.py:591)

`_bronbewijs_samenvoegen()` returns immediately when sources, receipt, assessment and peildatum match. It checks the incoming generation identity only afterward.

**Concrete trigger:** consume the attempt for `gen-0001`, then save an actual `gen-0002` on that record with identical evidence. The save succeeds, but retains `gen-0001`; reload restores that old ID, and reservation returns `attempt_consumed`.

The [regression test](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/tests/unit/services/test_def743_bronbewijs_persistentie.py:1829) changes both the generation ID and assessment, bypassing this early return.

**Disposition: fix now.** Check new-generation identity before treating evidence as unchanged; add a regression with a different generation ID and identical evidence.

## Dispositions

| Item | Result |
|---|---|
| **1 — Current validation issues** | **Closed.** New issues, text and proposal evidence share one UPDATE. Old ordinary issues are archived in `applied.previous_validation_issues`; markers remain version-bound. Actual expert-review and bulk-export readers consume the updated column. |
| **2 — Generation budget** | **Partially fixed.** Reload, manual source/peildatum corrections, revalidation and apply preserve identity. New-generation boundary remains defective as described above. |
| **3 — Stale export** | **Closed.** C’s replay determines current outcomes/applicability; raw assessments remain separately labelled historical when stale. Single/bulk exports share this adapter. |
| **4 — Receipt adapter** | **Closed.** `get_contractvelden()` returns an independent receipt deepcopy under the key used by proposal diagnosis. |
| **Review-history gap** | **Closed for the reviewed routes.** Replacement/removal appends prior payload, actor, version, status and candidate binding atomically. Duplicate/non-object markers retain their raw payloads; stale history stays historical. Rejected replacement and rollback paths preserve prior state. |
| **`part_correction`** | **Verified.** D delegates validation to C §6b, retains the payload and exports C’s scoped correction/original judgment. No blanket pass is introduced. |
| **Additive `assessment_receipt`** | **Preserved structurally.** Full assessments are deep-copied and serialized without field projection through storage, reload and JSON export. No dedicated execution evidence for this new field was established. |

Optional SAM `not_evaluated` remains accepted coverage; explicit unknown/error/readiness failures remain blocked. No DEF-630 gate workaround was introduced.

## Evidence and limits

Inspected actual fixes, regression tests, readers and retained logs. The supplied green log records **145 passed**; lint records ruff/black/mypy exit 0. **I executed no tests.** Neither those targeted results nor the manual tracker failures establish canonical `make test` success.

No edits, project imports, DB access, network or delegated processes.

## SHA256 manifest

All nine **start/end hashes matched**, and all matched `/tmp/DEF-743-persistence-fix-hashes.log`.

```text
41ab0c281f7a9ec361eb4f8c95697e6d4a6ff187f4580e85e5d5ec8a0e127430  src/database/models.py
cc8a35cf79d1857724107e7a3f4f8a3ec7b4cbdae84550b43a5d3af01826ed73  src/database/definitie_crud.py
728a3a009b49accf117e005b25e8670e0df321386909db620601853eeae5ccf2  src/database/definitie_repository.py
fa2773ff04e49f4e9b8b500f5b9c398ab7ee2548d163fcb0368d6c3f3adc815a  src/services/definition_repository.py
a534bfbb37914d46bb2faed3b63e0380da22c10fec38850f4502110d9b642097  src/services/data_aggregation_service.py
9a8ef62689127534366980df9644404c0724c4291e254370186316e6ddc023c2  src/services/export_service.py
ed49cd60aed4845509cc6a89413432cc9c42709e65ca9b5c535335cdb0185ad9  src/export/export_txt.py
1b4e5d476f5ab3d615593d6467511888a3b60e23d1b6eaafd51b9cf6428458d6  tests/unit/services/test_def743_bronbewijs_persistentie.py
2faed9b60a3686c88c3aa25e902ccef31a1b005a3e0dbcb562120174908b5a75  tests/unit/services/test_def743_bronbewijs_export.py
```