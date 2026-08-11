# BATCH-098 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 20/20 blobs, 3309/3309 fysieke regels en 58/58 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De gerichte B096-B098-selectie gaf gezamenlijk 74/74 groen; Ruff, Black, bash -n en plist-validatie waren schoon voor de toepasselijke scope.
- Object-ID's, EOF-ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B098-001 — P2 — Baseline comparison compares the baseline with itself

**Bewijs:** Baseline mode assigns new_results=old_results and then performs a normal comparison. A one-definition baseline exited 0 and reported 1/1 score matches (100%) without running/loading new validation results.

**Reproductie:** Run the CLI with --baseline on a JSON containing one definition and --format console.

**Aanbevolen oplossing:** Require actual new results or execute the new validator; otherwise label baseline-only mode and do not emit comparison metrics.

### B098-002 — P3 — Empty validation comparisons crash report generation

**Bewijs:** Console percentages divide by len(self.comparisons); HTML repeats the division at lines 276-289. ValidationComparer().generate_console_report() raised ZeroDivisionError.

**Reproductie:** Instantiate ValidationComparer without compare results and generate console or HTML output, or pass an empty baseline.

**Aanbevolen oplossing:** Handle zero comparisons explicitly with an empty-state report and a documented CLI status.

### B098-003 — P2 — Untrusted definition names are inserted into HTML without escaping

**Bewijs:** comp.begrip is interpolated directly into td markup. A temp comparison containing <img src=x onerror=alert(1)> wrote that payload verbatim to the report; browser execution was intentionally not attempted.

**Reproductie:** Construct old/new ValidationResult objects with an HTML payload as begrip, compare them, generate HTML, and search the file for the raw payload.

**Aanbevolen oplossing:** Escape every dynamic HTML value (or render with autoescaping templates) and add a restrictive CSP when reports are served.

### B098-004 — P3 — Generated comparison HTML lacks table semantics and sufficient header contrast

**Bewijs:** The document uses <html> without lang, a table without caption, th without scope, and white on #4CAF50 has a 2.78:1 contrast ratio below WCAG AA 4.5:1 for normal text. Static inspection confirmed all semantic attributes absent; browser/screen-reader testing was not run.

**Reproductie:** Generate an HTML report and inspect html/table/th markup; calculate relative luminance for #fff versus #4CAF50.

**Aanbevolen oplossing:** Set lang=nl, add caption and scope=col, use a darker green meeting 4.5:1, then run axe and manual keyboard/screen-reader checks.

### B098-005 — P2 — AI-review installers leave partially modified environments on failure

**Bewijs:** The first installer replaces the existing pre-commit hook before pip installation and lacks set -e/rollback; mocked pip/pre-commit failures still exited 0 and printed Setup Complete with the original moved. setup_ai_review.sh uses set -e but writes venv/config/hooks incrementally without rollback (supporting lines 22-127 and 217-279).

**Reproductie:** Run setup-ai-review.sh in a temp fake repo with failing pip/pre-commit wrappers and an existing hook; inspect exit code and hooks.

**Aanbevolen oplossing:** Preflight dependencies first, stage output, use set -euo pipefail plus a rollback trap, and atomically publish hooks/config only after verification.

### B098-006 — P3 — Dormant deployment scripts reference files absent from the immutable base

**Bewijs:** quick_deploy also requires missing migration/monitor/rollback helpers at lines 143-220, and start_app.sh:11-12 runs missing src/app.py; git cat-file proved all five absent while src/main.py exists.

**Reproductie:** At base b958ddb, git cat-file -e each referenced helper and src/app.py, or run quick_deploy test/start_app in an isolated checkout.

**Aanbevolen oplossing:** Remove obsolete launchers or retarget the supported entry point and helper set, then add a clean-checkout smoke test.

### B098-007 — P3 — Local branch-name validator rejects names accepted by active CI

**Bewijs:** The local regex omits bugfix, dependabot and DEF-N prefixes while .github/workflows/quality-gates.yml:106-126 accepts them. bugfix/DEF-1-fix exited 1 locally; the local script appears dormant/manual.

**Reproductie:** Run scripts/ci/validate-branch-name.sh bugfix/DEF-1-fix and compare with the CI regex.

**Aanbevolen oplossing:** Define one shared branch policy implementation/config and invoke it from both local tooling and CI.

### B098-008 — P3 — Installed launchd backup job hardcodes one developer checkout

**Bewijs:** Program, log and working-directory strings hardcode /Users/chrislehnen/Projecten/Definitie-app. setup_auto_backup.sh:17-47 copies the plist verbatim, so another user or moved checkout installs invalid targets; installed launchctl state was not changed/tested.

**Reproductie:** Resolve the project in another temp path and inspect the plist copied by the installer; all target paths still point at Chris original checkout.

**Aanbevolen oplossing:** Generate the plist from the resolved project root (or a stable wrapper/config), validate all targets before launchctl load, and add an install dry-run.

## Niet getest

- Geen echte provider, credential, netwerk, productie-DB of browser; destructieve en externe paden zijn alleen statisch, met mocks of op tijdelijke data onderzocht.
