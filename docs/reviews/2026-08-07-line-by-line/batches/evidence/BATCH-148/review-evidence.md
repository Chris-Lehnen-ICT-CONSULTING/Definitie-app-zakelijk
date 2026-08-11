# BATCH-148 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 9/9 bereiken, 5515/5515 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable analyses zijn gelezen; historische tellingen, ontbrekende suites, shell-/AST-reproducties, linkscans en veilige gate-simulaties zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B148-001 — P2 — Recommended bulk session-state fixer deterministically generates invalid Python

**Bewijs:** The first regex changes every constant-key access before assignment and deletion are distinguished. An assignment becomes SessionStateManager.get_value("active_tab") = "edit" and deletion becomes del SessionStateManager.get_value("session_key"); ast.parse rejects both. The plan still labels this a low-risk find-and-replace and writes every src/ui Python file in place.

**Reproductie:** Apply the three re.sub calls in documented order to st.session_state["active_tab"] = "edit" and del st.session_state["session_key"], then call ast.parse on each result; both raise SyntaxError.

**Aanbevolen oplossing:** Withdraw the regex fixer. Use an AST/CST migration that distinguishes load/store/delete contexts, emits a reviewable diff without in-place writes, and is gated by parsing, formatting and focused session-state tests.

### B148-002 — P2 — Recommended pre-commit checks accept violations and reject clean trees

**Bewijs:** The first and third recommended hooks use bare grep as a prohibition gate: a forbidden match returns zero, which pre-commit treats as success, while a clean tree returns one and fails. The middle hook is additionally malformed because its argument list contains a literal pipe and grep -v without a shell, so it is not the pipeline the document describes. All three gates therefore fail their stated contract.

**Reproductie:** Run the first and third grep commands with matching and clean input and observe return codes 0 and 1, the inverse of the intended pre-commit outcome. Inspect the middle hook's argv and observe that the pipe is passed literally rather than interpreted by a shell.

**Aanbevolen oplossing:** Wrap each search so matches exit 1, no matches exit 0 and tool errors remain failures; scope scans to staged files where appropriate and add positive, negative and grep-error self-tests for every hook.

### B148-003 — P3 — Ready migration runbook targets obsolete paths and creates its archive outside the repository

**Bewijs:** The script creates /docs/archief with a leading slash but moves files into relative docs/archief. All three docs/migration sources are absent from b958ddb because they already live under docs/archief/2025-01-cleanup; docs/migrations/history_tab_removal.md is also absent. The four links proposed for INDEX resolve relative to docs/analyses and are broken. Nevertheless the document ends Ready for Implementation.

**Reproductie:** Check each source and target using git cat-file -e at b958ddb, then resolve lines 316-319 relative to docs/analyses; the sources and all four link targets are absent. Inspect line 288 to see the absolute /docs target differs from the relative move destinations.

**Aanbevolen oplossing:** Mark the analysis superseded and remove executable instructions, or regenerate it from the current tree. Any maintained migration must resolve one verified repo root, preflight exact sources/targets, use git mv, validate links and stop atomically on mismatch.

## Deduplicaties en afwijzingen

- Absolute homepaden dedupliceren naar B136-001; reset-hard-instructies naar B135-004.

## Niet getest

- Geen externe URLs/netwerk, destructive commands, echte credentials/productiedata, historische benchmarks of browser/UI-runtime.
