# BATCH-096 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 12/12 blobs, 3603/3603 fysieke regels en 107/107 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De gerichte B096-B098-selectie gaf gezamenlijk 74/74 groen; Ruff, Black, bash -n en plist-validatie waren schoon voor de toepasselijke scope.
- Object-ID's, EOF-ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B096-001 — P2 — --check-only mutates files and reports no-op ADR sync as completed

**Bewijs:** The CLI parses --check-only but never branches on it; construction writes sync-config, sync_all writes sync-state, and the no-op ADR updater is counted via synced=len(adrs) (supporting lines 88-110 and 303-349). Temp CLI created config/state/report and reported items_synced=1 while the architecture documents were unchanged.

**Reproductie:** Create minimal EA/SA plus one ADR in a temp project and run architecture_sync.py --check-only --output report.json; observe three written files and items_synced=1.

**Aanbevolen oplossing:** Make check-only side-effect-free, implement or remove ADR mutation, and derive synced counts from verified before/after changes.

### B096-002 — P2 — --quiet suppresses the warning exit status

**Bewijs:** The warning branch exits 2 only when not quiet. The same warning-only temp project exited 2 normally and 0 with --quiet while both reports said overall_status=warning.

**Reproductie:** Run the validator on warning-only EA/SA documents once normally and once with --quiet; compare exit codes 2 and 0.

**Aanbevolen oplossing:** Let --quiet affect output only; map report status to the same exit code in every presentation mode.

### B096-003 — P3 — Performance analyzer drops I/O analysis and ignores failed pytest runs

**Bewijs:** content.count("Path(") returns int, then .count(".write") raises AttributeError and the broad except silently skips each file; the subprocess return code at lines 30-40 is also unused and outer failures only print.

**Reproductie:** Evaluate content.count("Path(").count(".write") or run the analyzer on an I/O-heavy test; no I/O result is recorded. Stub pytest to return nonzero and observe no failing process status.

**Aanbevolen oplossing:** Count Path/write patterns separately, surface parse errors, inspect pytest returncode, and return nonzero when measurement is invalid.

### B096-004 — P3 — Dependency analyzer misses relative and src-prefixed layer imports

**Bewijs:** The regex cannot capture leading-dot imports and get_layer recognizes ui.* but not src.ui.*. A temp service containing from .local import x and from src.ui.widget import y produced only src.ui.widget classified Other and zero violations.

**Reproductie:** Analyze a temp module with those two imports and assign it to services.demo; inspect imports, get_layer, and find_violations.

**Aanbevolen oplossing:** Use ast.Import/ImportFrom with level handling, normalize the configured source package prefix, and test relative/multiline/aliased imports.

## Niet getest

- Geen echte provider, credential, netwerk, productie-DB of browser; destructieve en externe paden zijn alleen statisch, met mocks of op tijdelijke data onderzocht.
