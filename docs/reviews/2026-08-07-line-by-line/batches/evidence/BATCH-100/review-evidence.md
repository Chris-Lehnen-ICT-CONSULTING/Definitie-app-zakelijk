# BATCH-100 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 13/13 blobs, 3870/3870 fysieke regels en 95/95 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De import-v9-unitset gaf 22/22 groen; Ruff en Black waren schoon op 36 Pythonbestanden en bash -n op zeven shellbestanden.
- Object-ID's, EOF-ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B100-001 — P1 — Documentation normalizer corrupts prose and structured dates and targets another checkout

**Bewijs:** Case-insensitive whole-document replacements convert ordinary Dutch 'om' to 'OM' and rewrite every ISO-looking date, including structured values. main hardcodes the original checkout for both input and report output.

**Reproductie:** Normalize 'Dit is om te testen op 2026-08-11' plus a JSON date; output becomes 'Dit is OM' and 11-08-2026 in both prose and JSON.

**Aanbevolen oplossing:** Use Markdown/frontmatter-aware transformations, derive and validate the active repository root, default to dry-run and write atomically only after structural validation.

### B100-002 — P1 — Production baseline export publishes audit identities and internal provenance into tracked documentation

**Bewijs:** The production query exports created_by, updated_by, approved_by, imported_from and other audit fields; output metadata includes the absolute database path. The tracked base artifact has 42 definitions, including 36 created_by, five updated_by and 36 imported_from values. Current values are service labels, but the export mechanism does not prevent personal identities.

**Reproductie:** Inspect the SELECT allowlist and run jq over the immutable baseline artifact to count populated audit fields and read export_metadata.database_path.

**Aanbevolen oplossing:** Export only approved business fields, anonymize or omit identity/provenance metadata, remove workstation paths and keep production-derived artifacts outside tracked documentation.

### B100-003 — P2 — Translation scripts fabricate performance, legal and integration claims

**Bewijs:** The translator inserts fixed 99-percent, 50-percent and 30-percent metrics, compliance frameworks and named justice integrations without source data. Priority selection is applied only after translate_directory has already written files; the older translator similarly invents an 80-percent reduction.

**Reproductie:** Pass neutral text containing 'verbetert' or 'vermindert' through the enhancement function, or 'reduces review time' through the companion translator; fixed percentages are added.

**Aanbevolen oplossing:** Limit automation to linguistic translation, require cited structured metadata for substantive claims and filter scope before any file is processed.

### B100-004 — P2 — Requirements renumbering has no fail-fast, collision or reference-integrity safeguards

**Bewijs:** An unguarded cd is followed by a long sequence of moves and in-place edits without set -e, destination collision checks, reference updates or rollback. ShellCheck confirms SC2164.

**Reproductie:** Run bash -n and ShellCheck, then inspect behavior after a failed cd or a pre-existing destination: the script continues with partial operations.

**Aanbevolen oplossing:** Fail fast, validate source and target inventory, use a collision-free two-phase mapping, update all references and support transactional rollback.

### B100-005 — P3 — Backlog restructuring never copies epic files because its wildcard is quoted

**Bewijs:** The -f test quotes ${epic_id}*.md as one literal path, so the wildcard cannot expand unless a filename literally contains an asterisk.

**Reproductie:** Create an isolated EPIC-001-description.md and evaluate the same quoted -f expression; it is false.

**Aanbevolen oplossing:** Expand a guarded glob into an array, validate the match count and copy the selected explicit path.

### B100-006 — P2 — Active feature-status workflow always resolves its dashboard HTML below scripts

**Bewijs:** The HTML path uses parent.parent from scripts/docs, producing scripts/docs/architectuur instead of repository docs/architectuur. The active GitHub workflow invokes this script.

**Reproductie:** Call update_html_file with mocked feature data; it reports the scripts/docs path missing and returns false.

**Aanbevolen oplossing:** Resolve the repository root correctly, validate the output path before the network request and regression-test the workflow entrypoint offline.

### B100-007 — P2 — GitHub issue titles are interpolated into executable feature-status JavaScript

**Bewijs:** Remote issue names are inserted inside single-quoted JavaScript strings without escaping. The current wrong output path blocks publication but the generator itself is injectable.

**Reproductie:** Generate data for a feature named with a quote, array close and alert call; the JavaScript output contains the executable payload unchanged.

**Aanbevolen oplossing:** Serialize remote data as JSON, never concatenate source strings into JavaScript and enforce a restrictive CSP on the generated page.

### B100-008 — P2 — Traceability auto-fix makes semantic assignments from weak heuristics in a hardcoded checkout

**Bewijs:** Story dependencies are inferred from consecutive numbering and orphan epics from substring counts or number ranges; apply_fixes writes those suggestions automatically. main targets Chris' original docs directory rather than the active checkout.

**Reproductie:** Create an orphan story containing a generic keyword such as 'file' or 'user'; the heuristic selects an epic and --auto-fix writes that semantic choice.

**Aanbevolen oplossing:** Generate reviewable proposals only, require explicit confirmation for semantic changes and accept a validated repository root as an argument.

### B100-009 — P2 — Migration validator reports success for an empty scope and never signals detected defects

**Bewijs:** Empty epic, story and requirement sets make all difference sets empty and print MIGRATION SUCCESSFUL. The function returns no status and the script exits zero even when orphaned or missing references are printed.

**Reproductie:** Point its Path constructor at empty temporary directories; output claims success with Epics: 0, Stories: 0 and Requirements: 0.

**Aanbevolen oplossing:** Require expected nonzero inventory and structural invariants, aggregate failures and return a nonzero process status whenever validation fails.

### B100-010 — P2 — Global frontmatter normalizer flattens nested link mappings

**Bewijs:** The custom parser tracks only one current key/list and treats nested map keys as top-level fields. A links mapping re-renders as empty links plus top-level epics and requirements.

**Reproductie:** Parse and render frontmatter containing links.epics and links.requirements in an isolated call; compare the resulting structure with the input.

**Aanbevolen oplossing:** Replace the custom parser with a schema-validated YAML round trip and block writes when semantic equivalence is not preserved.

## Niet getest

- Geen destructive scripts op echte documentatie, geen live GitHub/Linear/Wikipedia/AI-tools of credentials, en geen browser/screenreader/spreadsheet-executie.
