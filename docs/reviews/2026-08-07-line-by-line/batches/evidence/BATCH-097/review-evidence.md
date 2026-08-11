# BATCH-097 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 20/20 blobs, 3457/3457 fysieke regels en 79/79 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De gerichte B096-B098-selectie gaf gezamenlijk 74/74 groen; Ruff, Black, bash -n en plist-validatie waren schoon voor de toepasselijke scope.
- Object-ID's, EOF-ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B097-001 — P1 — Archive deletion uses every historical archive ID instead of the successful copy set

**Bewijs:** run() discards the local successful definition_ids, selects every ID in the archive DB, archives children for and deletes all those IDs from source. Child INSERT OR IGNORE counters also increment without checking changes (supporting lines 135-180 and 194-286). Temp DB selected only ID 1 but pre-existing archive ID 2 caused source IDs [1,2] both to be deleted.

**Reproductie:** Seed source IDs 1 old and 2 future; pre-seed archive ID 2; run days=30 --delete-source and query source after commit.

**Aanbevolen oplossing:** Carry an exact per-row copy ledger, verify parent/child row contents and changes, and delete only IDs atomically proven copied in this run.

### B097-002 — P1 — Hourly backup copies only the SQLite main file and silently omits committed WAL data

**Bewijs:** The documented hourly job uses cp on definities.db then only PRAGMA integrity_check. With WAL held open, live rows were [(1),(2)] while the copied main file contained [(1)] and still returned integrity_check=ok; the launchd job runs hourly (plist lines 10-22).

**Reproductie:** In a temp WAL DB, checkpoint row 1, hold a reader, commit row 2 from another connection, copy only the main file, then query and integrity-check the copy.

**Aanbevolen oplossing:** Use SQLite backup/VACUUM INTO while coordinating writers, atomically publish the verified backup, and validate row/schema fingerprints. Related to B010-001 but a distinct active backup path.

### B097-003 — P2 — Restore overwrites the live database non-atomically and has no rollback

**Bewijs:** After verifying the source, shutil.copy2 writes directly to self.db_path; restored verification happens afterward and neither exception nor failed verification restores the safety backup. A mocked interrupted copy left the live file as b"partial" and raised.

**Reproductie:** Use two valid temp SQLite files, monkeypatch module shutil.copy2 to write a prefix then raise, and call restore_backup(..., create_backup_before_restore=False).

**Aanbevolen oplossing:** Restore to a separate file, verify/fsync it, quiesce connections and sidecars, atomically replace the database, and automatically roll back on failure.

### B097-004 — P2 — Archive and restore CLIs open log files before creating the log directory

**Bewijs:** Both archive_data.py and backup_restore.py configure FileHandler at import, while logs mkdir occurs only in main after argument parsing (backup supporting lines 23-31 and 400-403). From a fresh temp cwd, --help exited 1 with FileNotFoundError for logs/archive.log and logs/backup_restore.log.

**Reproductie:** cd to an empty temp directory and invoke each absolute script path with --help.

**Aanbevolen oplossing:** Create/resolve the log directory before handlers, defer logging setup until main, and keep --help side-effect-free.

### B097-005 — P2 — Partial synonym failures are reported as no results and still exit successfully

**Bewijs:** process_term catches every exception and returns [], process_terms cannot distinguish failure from no matches, and main exits 0 when any other term yielded rows (supporting lines 330-347). Offline dummy terms bad/good yielded one success row, no failure metadata, and a truthy result.

**Reproductie:** Use a dummy orchestrator that raises for one term and returns one synonym for another; run process_terms on both and inspect exported rows/exit decision.

**Aanbevolen oplossing:** Return structured per-term outcomes, export failures, summarize partial completion, and use a documented nonzero partial-failure exit code.

### B097-006 — P2 — Streamlit anti-pattern gate misses multiline widget calls

**Bewijs:** check_file feeds one physical line at a time to a regex requiring value and key within one call. A multiline st.text_input(value=..., key=...) produced zero errors; this checker is active in pre-commit.

**Reproductie:** Write the widget call across four lines in a temp src/ui file and invoke StreamlitPatternChecker.check_file.

**Aanbevolen oplossing:** Parse calls with ast/CST and test multiline calls, keyword order, aliases and nested expressions.

### B097-007 — P2 — Active legacy gate treats an invalid ripgrep regex as PASS

**Bewijs:** The request.context negative lookahead at line 97 requires PCRE, but rg is called without -P and stderr/exit status are collapsed by || true. Direct rg returned 2 regex parse error; the script exited 0 and printed PASS. The active workflow repeats rg without -P at .github/workflows/epic-010-gates.yml:53-62.

**Reproductie:** Run rg request\.context(?!_|\w) src --type py and then the shell gate; compare exit 2 with the gate PASS.

**Aanbevolen oplossing:** Use rg -P and distinguish match=0, no-match=1 and tool-error>1; seed a forbidden fixture in a CI self-test.

### B097-008 — P3 — File-size checker word-splits filenames and skips large files containing spaces

**Bewijs:** FILES="$@" followed by for file in $FILES splits paths. A temp file named large file.py with 1001 code lines exited 0 and emitted no size finding. The pre-commit wrapper additionally does not forward filenames and forces warning-only behavior.

**Reproductie:** Pass a greater-than-1000-line temp Python path containing a space as the sole argument.

**Aanbevolen oplossing:** Keep arguments in an array, use NUL-delimited discovery, forward pre-commit filenames explicitly, and test whitespace/newline paths.

## Niet getest

- Geen echte provider, credential, netwerk, productie-DB of browser; destructieve en externe paden zijn alleen statisch, met mocks of op tijdelijke data onderzocht.
