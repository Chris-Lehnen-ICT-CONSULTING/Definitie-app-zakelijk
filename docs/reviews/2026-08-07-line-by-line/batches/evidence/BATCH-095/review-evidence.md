# BATCH-095 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 16/16 blobs, 3941/3941 fysieke regels en 70/70 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Synoniemenvalidatie gaf 30 groen/1 rood; Ruff, Black, py_compile en bash -n waren groen, terwijl shellcheck terecht fout eindigde.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: De validatorroot-cause is B092-003; B095-012 registreert alleen de aantoonbaar verouderde documentatie.

## Bevindingen

### B095-001 — P1 — Flat documentation archive silently overwrites same-named files

**Bewijs:** Every destination is docs/archief plus basename and ordinary mv has no collision guard; find output is whitespace-unsafe.

**Reproductie:** In a temp tree, two collision.md files were moved and only the second content remained while the script exited zero.

**Aanbevolen oplossing:** Preserve relative paths, use NUL-delimited traversal and fail preflight on every collision.

### B095-002 — P1 — Documentation reorganization mutates reviews before a guaranteed invalid move

**Bewijs:** Reviews move first, then the script moves docs/archief into its own subdirectory; the simple variant moves entire review trees without completion state.

**Reproductie:** Temp execution moved live.md then exited one with Invalid argument on the self-descendant move.

**Aanbevolen oplossing:** Preflight the whole plan, move archive children individually and restrict execution to explicitly approved completed reviews.

### B095-003 — P1 — Rename tool stages all user changes and creates its backup inside the source tree

**Bewijs:** Backup unconditionally runs git add -A, commit and tag with unchecked results; copytree destination is a child of project_root.

**Reproductie:** Mocked execution captured all Git mutations and dst_inside_src=True while the method reported success.

**Aanbevolen oplossing:** Refuse dirty trees, make backups outside the repository and keep Git mutation outside the tool.

### B095-004 — P1 — Failed rename rolls back the filename but not rewritten references

**Bewijs:** After rewriting all referers, a failed test only renames the file back; content rollback is explicitly absent.

**Reproductie:** Temp repro returned False with old_name.py restored but consumer imports and strings still changed to new_name.

**Aanbevolen oplossing:** Journal original bytes and apply/rollback all file changes atomically; never commit partial results.

### B095-005 — P2 — Installed AI pre-commit hook references missing script paths

**Bewijs:** The hook calls scripts/ai_code_reviewer.py while the canonical file is scripts/docs/ai_code_reviewer.py; setup also references missing reviewer/tracker paths.

**Reproductie:** Run with AI_AGENT_COMMIT and venv Python: the hook exits one because the file is absent.

**Aanbevolen oplossing:** Use one canonical configured path, preflight it and invoke the project interpreter explicitly.

### B095-006 — P2 — AI metrics CLI is unreachable whenever Streamlit is installed

**Bewijs:** __main__ imports Streamlit and always calls the dashboard instead of main; top-level imports also prevent a no-Streamlit fallback.

**Reproductie:** Run the report command: exit zero, no report, only bare-mode warnings and a metrics database.

**Aanbevolen oplossing:** Always parse the CLI and lazy-import Streamlit only for dashboard.

### B095-007 — P2 — Coverage analyzers accept stale output and hardcode one workstation

**Bewijs:** Nonzero pytest return codes are ignored and existing coverage.json is read; both analyzers hardcode Chris' root and targeted coverage equates filenames with execution.

**Reproductie:** Mock returncode 124 with a stale 99.9-percent file; get_coverage_data returns that stale marker.

**Aanbevolen oplossing:** Use unique temporary output, delete stale files, require zero exit and accept root as a CLI argument.

### B095-008 — P2 — Agent scoreboard integration uses a missing path and unsafe branch switching

**Bewijs:** Deployment calls scripts/agent_scoreboard.sh instead of scripts/analysis; standalone warns on dirty state but checks out anyway, lacks a restoration trap and uses unavailable Bash-3.2 mapfile.

**Reproductie:** Path lookup fails; type mapfile returns nonzero on the project Mac and a temp dirty repository still switches branches.

**Aanbevolen oplossing:** Fix the canonical path, reject dirty state, use portable reads and isolated worktrees with guaranteed restoration.

### B095-009 — P3 — Core prompt analyzer uses removed private APIs but exits successfully

**Bewijs:** Its sys.path points to the script directory; with project path set, all five cases call missing _build_role_and_basic_rules yet the process writes a failure report and exits zero.

**Reproductie:** Run outside repo for ModuleNotFoundError, then with PYTHONPATH for five failures and exit zero.

**Aanbevolen oplossing:** Package the entrypoint, use public current APIs and exit nonzero when cases fail.

### B095-010 — P3 — Dependency analyzer scans and writes during import

**Bewijs:** There is no function/main guard; importing scans cwd, prints and writes service_dependencies.json.

**Reproductie:** Import the module in a temp cwd and observe the JSON artifact.

**Aanbevolen oplossing:** Move work into pure functions and an explicit CLI with root/output arguments.

### B095-011 — P3 — Modular prompt analyzer crashes on empty or zero-sized reports

**Bewijs:** Average and loss calculations divide by result count and total original size; common issues are printed as hardcoded facts.

**Reproductie:** Empty results and one zero-original result each raise ZeroDivisionError.

**Aanbevolen oplossing:** Validate schema, handle zero denominators and derive issues from actual data.

### B095-012 — P3 — Synonym validation documentation points to a missing green suite

**Bewijs:** Docs and summary reference nonexistent tests/scripts/test_validate_synonyms.py and claim 31 green tests; actual file is under integration and is explicitly deselected.

**Reproductie:** Run the real file: 30 pass and one non-string failure; the validator defect is already B092-003.

**Aanbevolen oplossing:** Document the actual path/status, restore the test gate and keep generated counts current.

## Niet getest

- Geen scripts tegen de repository uitgevoerd, geen echte commit/tag/database/provider/netwerk; alle mutatierepro's bleven onder tijdelijke directories.
