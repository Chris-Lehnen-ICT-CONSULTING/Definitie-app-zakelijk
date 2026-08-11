# BATCH-101 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 20/20 blobs, 3739/3739 fysieke regels en 104/104 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De import-v9-unitset gaf 22/22 groen; Ruff en Black waren schoon op 36 Pythonbestanden en bash -n op zeven shellbestanden.
- Object-ID's, EOF-ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B101-001 — P1 — Generation-log table rebuild leaves SQLite views pointing to the dropped old table

**Bewijs:** ALTER TABLE generation_logs RENAME updates dependent view SQL to generation_logs_old; the script later drops that table without recreating views. The historical v7 migration documents the same SQLite behavior.

**Reproductie:** Create an in-memory generation_logs table and view, call fix_generation_logs and query the view; SQLite raises no such table: main.generation_logs_old.

**Aanbevolen oplossing:** Inventory and recreate dependent views around the rebuild, then run foreign_key_check and query every recreated view before committing.

### B101-002 — P1 — Unicode fixer can turn valid Python string literals into invalid syntax

**Bewijs:** Curly quotes are replaced contextlessly across complete Python files and writes occur before any syntax validation.

**Reproductie:** Process a temporary file containing s = "He said “hi”"; the result is s = "He said "hi"" and ast.parse raises SyntaxError.

**Aanbevolen oplossing:** Perform token-aware transformations, preserve quote context and compile all proposed outputs before atomically replacing any source file.

### B101-003 — P1 — TXT recovery parser truncates definitions at ordinary colon-prefixed continuation lines

**Bewijs:** Every line matching words followed by a colon becomes a new field, not only known export headers. The recovery CLI auto-confirms when stdin is noninteractive.

**Reproductie:** Parse a definition whose continuation begins 'Let op:'; only the text before that line remains in definitie.

**Aanbevolen oplossing:** Use a whitelist/state-machine parser for known headers, validate previews and checksums, and require an explicit --yes flag for noninteractive imports.

### B101-004 — P1 — NaN-context cleanup silently replaces malformed context data with empty arrays

**Bewijs:** Any JSON parse exception returns an empty list, after which main updates and commits the record without backup, dry-run or error status.

**Reproductie:** Run main against a temporary SQLite row containing '[not valid json'; it exits zero and stores [] in that field.

**Aanbevolen oplossing:** Treat parse failures as blocking or quarantine them, add dry-run and verified backup support, and update records transactionally only after explicit review.

### B101-005 — P2 — Secret cleanup prints complete discovered keys and executes commands through eval

**Bewijs:** The final grep captures and echoes complete matching lines. Command execution is routed through eval; ShellCheck reports SC2294.

**Reproductie:** Run the script from a temporary directory containing a fake sk-REVIEW-SECRET value; the complete value appears in stdout.

**Aanbevolen oplossing:** Report only filenames and line numbers or redact matched values, remove eval and pass commands as properly quoted arguments.

### B101-006 — P2 — Functional verification accepts unrelated configuration and fewer rules than it claims

**Bewijs:** A config without web_lookup returns success true, and the rule test documents 53 but passes any count of at least 45.

**Reproductie:** Inject load_web_lookup_config returning {'totally_unrelated': true}; test_config_sections reports success. Return 45 rule objects and the rule-count contract also passes.

**Aanbevolen oplossing:** Validate the exact configuration schema and canonical rule IDs/count, and make mismatches fail the verification process.

### B101-007 — P3 — Documentation link checker treats valid file links with fragments as broken and is not wired

**Bewijs:** The checker resolves the full target including #fragment as a filesystem path. The hooks README presents it as active, but no corresponding pre-commit hook exists.

**Reproductie:** Check a Markdown link to an existing target.md#heading; the function returns a broken-link error.

**Aanbevolen oplossing:** Strip query and fragment before filesystem resolution, optionally validate headings separately, and register the hook in pre-commit and CI.

### B101-008 — P3 — Changed-file formatter hooks split valid Git paths and silently restage files

**Bewijs:** Both Black and Ruff hooks capture newline-separated paths and expand them unquoted, allowing whitespace and glob splitting; both then run git add on the expanded list. ShellCheck reports SC2086 for execution and staging.

**Reproductie:** Stage a scoped Python filename containing spaces or glob characters in an isolated repository and run either hook; the path is split or expanded and staging is mutated.

**Aanbevolen oplossing:** Use git diff -z with NUL-safe arrays, pass each path as an argument and leave staging changes explicit to the caller.

### B101-009 — P3 — Linear issue fetch can hang indefinitely and emits raw remote error bodies

**Bewijs:** requests.post has no timeout and non-200 or GraphQL errors are printed verbatim. No active production caller was found.

**Reproductie:** Static inspection confirms the unbounded call and raw output paths; live network timing and response contents were intentionally not tested.

**Aanbevolen oplossing:** Set bounded connect/read timeouts, use structured status handling and log only sanitized error summaries with correlation identifiers.

### B101-010 — P3 — Wikipedia synonym export preserves spreadsheet formula prefixes from external data

**Bewijs:** Candidate fields are written directly through csv.DictWriter and the documented next step is manual spreadsheet review. A synthetic =HYPERLINK value remains formula-prefixed in the CSV; exploitability from live Wikipedia input was not tested.

**Reproductie:** Export a synthetic SynonymCandidate whose synonym starts with =HYPERLINK; inspect the first data row and observe the leading equals sign is preserved.

**Aanbevolen oplossing:** Neutralize fields beginning with equals, plus, minus or at-sign before spreadsheet-oriented export and clearly treat all external cells as untrusted text.

## Niet getest

- Geen destructive scripts op echte documentatie, geen live GitHub/Linear/Wikipedia/AI-tools of credentials, en geen browser/screenreader/spreadsheet-executie.
