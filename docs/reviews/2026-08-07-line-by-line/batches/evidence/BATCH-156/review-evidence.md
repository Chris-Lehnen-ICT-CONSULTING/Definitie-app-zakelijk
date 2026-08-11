# BATCH-156 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 29/29 bereiken, 5862/5862 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable archiefdocumenten zijn gelezen; OID-, UTF-8-, link-, credential-, policy- en documentstructuurcontroles reproduceerden de geregistreerde grenzen.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B156-001 — P2 — Archived nested CLAUDE policy conflicts with current repository safeguards

**Bewijs:** This nested CLAUDE.md tells the coding agent to refactor first and ask later (lines 8-13), make backup copies in the tree (line 24), target Python 3.11 plus Poetry or pip-tools (lines 29-32), use print debugging (line 44), log user_id and full stack traces (lines 62-68), and permits direct work on main for selected changes (lines 134-137). The immutable root CLAUDE.md instead specifies Python 3.13, the current Make/requirements workflow, no personal data in logs, and a feature branch. A second nested copy at docs/archief/bulk-archive-2025-08-18/analysis/CLAUDE.md:12-50 and 71-84 repeats the mutation and personal-log guidance. The conflicting control files are proven; actual instruction precedence in a live Claude Code session was not exercised, so behavioral reach is suspected.

**Reproductie:** At base b958ddb, select docs/archief/README.md as the target and enumerate ancestor CLAUDE.md files; docs/archief/CLAUDE.md is the nearest repository control file. Diff its lines 1-137 against root CLAUDE.md and observe the conflicting autonomy, branch, toolchain and logging rules. Repeat for a file under bulk-archive-2025-08-18/analysis to find the second nested copy.

**Aanbevolen oplossing:** Rename archived instruction snapshots so agents cannot interpret them as live control files, add an explicit historical banner, and retain exactly one current repository CLAUDE.md. If subtree instructions are intentional, reduce them to a short extension that cannot weaken branch, approval, privacy or toolchain policy; add a repository check for unexpected nested agent-control files.

### B156-002 — P3 — Architecture completion report is stored as one escaped Markdown line

**Bewijs:** The 6,232-byte blob contains one physical newline but 193 literal backslash-n sequences. Headings, lists and paragraph breaks therefore remain embedded in one physical Markdown line, so a normal Markdown renderer cannot expose the intended heading hierarchy or readable document structure.

**Reproductie:** Run git cat-file blob 813caa7904ab2b0adfa72d1d17c808e2e015a2f8 and count byte 0x0a versus the two bytes backslash+n; the counts are 1 and 193. Inspect the first bytes and observe '# ... Report\n\n**Project**' rather than real line breaks.

**Aanbevolen oplossing:** Decode the escaped newline sequences into real UTF-8 line endings, then validate the rendered Markdown heading/list structure. Preserve the original blob as historical evidence only if needed, under a non-rendered extension.

### B156-003 — P3 — Archive README is a broken ADR index with colliding ADR-005 records

**Bewijs:** The archive root describes itself as an ADR directory and links ADR-001 through ADR-004, but all four relative targets are absent from the immutable tree. It omits docs/archief/adr-history entirely, where two different records both use the identifier ADR-005; one of those also links the absent ADR-004 at adr-history/ADR-005-service-consolidatie-heroverweging.md:154. The archive root therefore cannot navigate or uniquely identify its own decisions.

**Reproductie:** Resolve each link on lines 16-19 relative to docs/archief and run git cat-file -e b958ddb:<resolved-path>; all four return missing. Then list docs/archief/adr-history/ADR-005* at the same base and observe two distinct files with the same ADR number.

**Aanbevolen oplossing:** Replace this copied ADR README with an actual archive index, link existing historical decisions, assign stable unique ADR identifiers or explicitly mark supersession, and add a case-sensitive immutable-tree link/duplicate-ID check for ADR indexes.

### B156-004 — P3 — Validation documentation hub marks a missing document canonical and active

**Bewijs:** The file calls itself the central navigation hub, marks validation_orchestrator_v2.md CANONIEK and ACTIVE at lines 3-11, repeats that missing target at lines 83 and 100, and links another absent implementation guide at lines 59 and 86. The immutable tree has neither target. Lines 107-122 retain expired 2025 review dates while line 125 claims the index is automatically updated; no production or documentation automation caller for this index was found. The sibling contract repeats the missing canonical link at architecture/contracts/validation_result_contract.md:260.

**Reproductie:** Resolve the links on lines 9, 59, 83, 86 and 100 relative to this file and compare them case-sensitively with git ls-tree -r --name-only b958ddb; the two unique file targets do not exist. Git-grep the base for validation_orchestrator_INDEX.md outside the archive and for an updater of this path; neither yields an active caller.

**Aanbevolen oplossing:** Add an archive/deprecation banner and point readers to the current implementation and contract, or restore the named canonical documents. Remove the automatic-update claim unless a fail-closed generator owns the file, and include this hub in the immutable-tree Markdown link gate.

## Deduplicaties en afwijzingen

- Generieke linkgateproblemen relateren aan B137-001; de ADR-ID-collisie en special-file-policyconflict blijven zelfstandig.

## Niet getest

- Geen browserweergave, echte Claude-instructieprecedence, netwerk, deployments, credentials of uitvoering van archiefvoorbeelden.
