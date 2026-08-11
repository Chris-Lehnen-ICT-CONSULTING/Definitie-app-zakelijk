# BATCH-163 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 10/10 bereiken, 4428/4428 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable architectuurdocumenten zijn gelezen; context-, path-, WAL-backup-, performance- en linkreproducties zijn veilig en offline uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B163-001 — P2 — Active architecture invents the core runtime it tells maintainers to follow

**Bewijs:** The document labels itself Active/current at lines 3-18 and docs/architectuur/README.md:23-65 makes it the main starting point for developers and AI assistants. It specifies ServiceContainer.get_instance(), 45 rules under two obsolete trees and three absent core-service paths. Elsewhere the same active document also names absent scripts/run_app.sh and three absent test paths (lines 71, 197, 824-841 and 904). At the immutable base ServiceContainer has no get_instance, the three core files are absent, and the actual tree contains 53 JSON rules under src/toetsregels/regels plus a separate validators tree. This is current guidance, not an archived proposal.

**Reproductie:** Against b958ddb, inspect hasattr(ServiceContainer, 'get_instance') (False), count 53 JSON rules, and run git cat-file -e for the documented core-service, launcher and test paths; all cited absent paths fail. Compare with lines 71, 197, 244-520, 824-841 and 904 and the active architecture hub.

**Aanbevolen oplossing:** Regenerate the active architecture inventory from importable production modules and the canonical rule registry; replace illustrative APIs with tested current snippets, link every component to an existing path, mark superseded material historical, and add an immutable-tree architecture-doc contract test.

### B163-002 — P2 — Two active canonical context contracts disagree with each other and runtime

**Bewijs:** This active canonical contract says all three context fields are list[str], all UI and services work exclusively with lists and repositories have no string fallback. The simultaneously active canonical ADR-006-CONTEXT-DISPLAY-POLICY.md:14-18 defines the organisational and legal context as strings. Runtime exposes a third contract: src/services/interfaces.py:181-215 still accepts GenerationRequest.context as str | None beside the list fields, and constructing it with context='legacy-string' succeeds. The removal of Definition.context itself is consistent; the exclusivity and field-type claims are not.

**Reproductie:** Read the front matter and type claims in both canonical documents, then with PYTHONPATH=src construct GenerationRequest(id='review', begrip='term', context='legacy-string'); type(request.context).__name__ is `str`, contradicting lines 21, 31 and 45.

**Aanbevolen oplossing:** Choose one versioned context contract, update or supersede ADR-006, explicitly document the remaining legacy adapter and removal boundary, and add generated schema/DTO/UI contract tests that prevent two documents from being canonical with incompatible field types.

### B163-004 — P2 — Active backup guidance loses committed SQLite WAL data

**Bewijs:** The active architecture prescribes plain `cp data/definities.db` and asserts that copying the SQLite file yields a complete backup. SQLite is used with WAL in this application; B010-001/B097-002 already establish the underlying product/runbook hazard. An independent temporary repro committed a table and row with WAL autocheckpoint disabled, copied only the main file, and the copy raised `OperationalError: no such table: t` while the live database contained one row. This row records the distinct false assurance in the active architecture and deduplicates the underlying implementation defect.

**Reproductie:** In a temporary directory, open SQLite in WAL mode, disable autocheckpoint, create and commit a table, insert and commit one row, then `shutil.copy2` only the main database and query the copy. The WAL exists, the live count is 1, and the copied database has no table.

**Aanbevolen oplossing:** Replace file-copy guidance with SQLite backup API or VACUUM INTO, verify integrity plus row/schema fingerprints, document restore testing, and link the canonical runbook to the already identified B010-001/B097-002 remediation.

## Deduplicaties en afwijzingen

- De WAL-hazard dedupliceert naar B010-001/B097-002; B163-004 betreft de afzonderlijke actieve false assurance.

## Niet getest

- Geen destructive reset, echte databasebackup/productiedata, netwerk/providers, clouddeployment of Mermaid/browser-rendering.
