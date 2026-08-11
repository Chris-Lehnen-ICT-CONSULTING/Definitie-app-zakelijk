# BATCH-137 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 19/19 bereiken, 5675/5675 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documenten zijn gelezen; case-sensitive Git-tree-link-, privacy-, commando- en statische HTML-controles reproduceerden de geregistreerde afwijkingen.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B137-001 — P2 — Central documentation hubs contain 37 broken internal links

**Bewijs:** A case-sensitive immutable-tree link scan finds 30 missing targets in docs/INDEX.md, although line 59 says all links were verified and line 99 calls the absent docs/portal/index.html the primary portal. The root README links users to this index. The supporting central hub docs/README.md:13-65 adds seven broken links, including both occurrences of all three claimed canonical architecture documents; docs/README.md:79 also reports 46 rules while the base README and current architecture documentation report 53. Drie extra analyse-links in B140 zijn eveneens gebroken (twee door absolute werkstationpaden en één door een verplaatste test); dit is dezelfde ontbrekende repositorybrede linkintegriteitsgate en krijgt geen apart B140-ID.

**Reproductie:** Extract each Markdown link from both files at base b958ddb, resolve it relative to the source path, and compare case-sensitively with `git ls-tree -r --name-only b958ddb`; 30 of 60 internal links in docs/INDEX.md and 7 of 26 in docs/README.md have no file or directory target.

**Aanbevolen oplossing:** Replace links with existing canonical targets, remove or restore the portal and obsolete dashboards, update volatile counts from authoritative sources, and add a case-sensitive immutable-tree link check for both central hubs to CI.

### B137-002 — P2 — Ready-for-execution plan uses an invalid Ruff CLI and forces the original checkout

**Bewijs:** The document declares itself READY FOR EXECUTION, but its two automated fixes use `ruff --fix I001` and `ruff --fix UP035`; Ruff 0.15.17 rejects that option placement with exit 2 (`unexpected argument '--fix'`). The execution block also hardcodes `cd /Users/chrislehnen/Projecten/Definitie-app`, which leaves any clone or review worktree and can direct later fix commands at the wrong checkout.

**Reproductie:** Run the exact line-43 command with project Ruff and observe exit 2 before any linting. From the isolated review worktree, resolve or execute only line 96 and observe that it selects Chris's original checkout instead of the current repository root.

**Aanbevolen oplossing:** Use root-agnostic commands such as `ruff check --fix --select I001 src config` and `ruff check --fix --select UP035 src config`, require an asserted repository root, and validate every published runbook command in a disposable checkout.

### B137-003 — P3 — Archived validation migration stub redirects to a nonexistent canonical document

**Bewijs:** The seven-line stub says it has been replaced and tells readers to use docs/architecture/validation_orchestrator_v2.md, but that path is absent from the immutable tree. Because redirecting is the stub's only function, following its instruction reaches no canonical architecture document.

**Reproductie:** Run `git cat-file -e b958ddb139b4754d1644ca4b4f22b1683d8ad108:docs/architecture/validation_orchestrator_v2.md`; Git exits 128. Existing related documents are under docs/workflows, docs/testing and docs/archief instead.

**Aanbevolen oplossing:** Point the stub to the actual maintained canonical document using a real Markdown link and cover archive redirects in the case-sensitive documentation link check.

### B137-004 — P3 — Archived synchronization dashboard lacks language and mobile semantics

**Bewijs:** The HTML element has no `lang` attribute, the head has no viewport metadata, and metric headings jump from h1 directly to h3. This prevents deterministic document-language announcement and causes legacy desktop-layout scaling on mobile. The page is archived and has no active caller to this exact path, so operational reach is dormant.

**Reproductie:** Inspect the complete 39-line blob or search it for `lang=`, `name="viewport"` and `<h2`; none is present, while lines 18, 23, 28 and 33 use h3. Tidy reports no structural parse error, so these semantic issues remain source-proven; browser and screen-reader behavior was not exercised.

**Aanbevolen oplossing:** Add `<html lang="en">`, a responsive viewport meta tag and a sequential h1/h2 hierarchy; if the dashboard is intentionally archival only, render it inertly or clearly label it as a historical snapshot.

## Deduplicaties en afwijzingen

- Drie extra B140-linkbreuken zijn samengevoegd in B137-001; het hardcoded-rootpatroon relateert aan B098-008/B102-005 maar de ongeldige uitvoerklare Ruff-flow is zelfstandig.

## Niet getest

- Geen externe URLs, echte destructive commands, browser/mobile/screenreader-runtime, credentials of historische benchmarks.
