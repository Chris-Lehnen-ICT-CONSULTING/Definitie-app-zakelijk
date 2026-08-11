# BATCH-136 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 20/20 bereiken, 5674/5674 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documenten zijn gelezen; case-sensitive Git-tree-link-, privacy-, commando- en statische HTML-controles reproduceerden de geregistreerde afwijkingen.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B136-001 — P3 — Archived review report exposes 795 personal workstation paths

**Bewijs:** All 795 Ruff issue rows embed the absolute prefix /Users/chrislehnen/Projecten/Definitie-app, disclosing a personal account name and local checkout layout in a tracked artifact. The active report generator renders issue.file_path verbatim, so the same output shape can recur; the reviewed artifact itself is archived and has no active application caller. Dezelfde root is onafhankelijk teruggevonden op vijftien regels in B139-B142, waaronder ConfigManager-, container- en contextanalyses; deze worden niet dubbel geteld.

**Reproductie:** Run `git show b958ddb139b4754d1644ca4b4f22b1683d8ad108:docs/ARCHIEF/review-rapport.md | rg -c '/Users/chrislehnen/Projecten/Definitie-app'`; it returns 795, spanning lines 13 through 807.

**Aanbevolen oplossing:** Store repository-relative paths in generated reports, redact user/home-directory segments before serialization, add a privacy regression test for generated artifacts and sanitize or replace the committed archive copy.

## Deduplicaties en afwijzingen

- Dezelfde absolute-workstation-pathroot in B139-B142 is samengevoegd in B136-001.

## Niet getest

- Geen externe URLs, echte destructive commands, browser/mobile/screenreader-runtime, credentials of historische benchmarks.
