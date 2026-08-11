# BATCH-102 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-root`
- Scope: 17/17 blobs, 3836/3836 fysieke regels en 106/106 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De relevante mypy-ratchettests gaven 34/34 groen; Ruff, Black, Python-compile en bash -n waren schoon voor de toepasselijke scope.
- Object-ID's, EOF-ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B102-001 — P1 — Active grep gate scans the wrong root and treats rg errors as clean

**Bewijs:** Repository root resolution is one parent too shallow; several checks collapse rg rc=2/no-files into OK, so the active CI gate can pass without scanning intended files.

**Reproductie:** Run the gate from its normal location with tracing or point a check at a nonexistent subtree; observe the shallow root and OK after rg error/no files.

**Aanbevolen oplossing:** Resolve root from git rev-parse --show-toplevel, fail closed on rg rc>1/no expected files, and seed one violation per gate in CI self-tests.

### B102-002 — P2 — Document cleanup resolves the project root to scripts/

**Bewijs:** Path(__file__).parent.parent resolves to scripts rather than repository root; main uses it at lines 446-449, so context/double cleanup fixers traverse the wrong subtree.

**Reproductie:** Instantiate/run the tool from a clean checkout and print/inspect project_root and its selected documentation paths.

**Aanbevolen oplossing:** Use git root or parents[2], pass root explicitly, and assert expected docs/config anchors before mutation.

### B102-003 — P2 — Document cleanup can erase malformed frontmatter and report failed writes as success

**Bewijs:** Malformed YAML frontmatter is parsed/fixed through broad fallback paths that can silently remove it; write-result propagation in lines 266-331 can return success despite a failed write.

**Reproductie:** Process a temp Markdown file with malformed frontmatter, then monkeypatch the write operation to fail; compare output and returned success.

**Aanbevolen oplossing:** Parse conservatively, preserve original bytes on invalid YAML, make writes atomic, and return failure unless the exact new bytes persist.

### B102-004 — P3 — Broken-link fixer writes its report in dry-run mode

**Bewijs:** The dry-run guard covers content fixes but report generation at lines 242-266 still writes output, violating a side-effect-free preview contract.

**Reproductie:** Run --dry-run in a temp project and compare the file tree before/after; the report is newly created.

**Aanbevolen oplossing:** Route every write through one dry-run policy; print report to stdout or require an explicit output opt-in.

### B102-005 — P2 — Requirement fixers hardcode the original checkout and can write across worktrees

**Bewijs:** The script hardcodes /Users/chrislehnen/Projecten/Definitie-app; related v2/translation/smart fixers use the same pattern, so invoking from another worktree targets the original checkout.

**Reproductie:** Run from an isolated temp/worktree and inspect the resolved target paths without applying changes.

**Aanbevolen oplossing:** Resolve repository root from the script/git context, accept --root, reject targets outside it, and add an isolated-worktree test.

### B102-006 — P3 — Smart-compliance threshold is printed but not used

**Bewijs:** The configured/printed threshold is not used in the pass decision; lines 700-715 hardcode a count of four, so changing threshold does not change outcome.

**Reproductie:** Run the evaluator twice with different thresholds against the same four-check input and compare the unchanged result.

**Aanbevolen oplossing:** Calculate the decision from the configured threshold and total checks, validate bounds, and test boundary values.

## Niet getest

- Geen productie-DB, GitHub writes, externe API, Docker/Redis/launchd of actieve browser; migratie- en recoveryrepro's gebruikten tijdelijke SQLite-data.
