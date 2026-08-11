# BATCH-135 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 15/15 bereiken, 5390/5390 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documenten zijn gelezen; lokale links, commando's, inline JavaScript, destructieve instructies en statische WCAG 2.1 AA-eigenschappen zijn gecontroleerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B135-001 — P3 — Service details and copy actions are unavailable from the keyboard

**Bewijs:** Six .service-item divs and two .code-snippet divs receive click-only behavior; none has role, tabindex or keyboard handlers. The code-copy action sets only a title, does not await/catch clipboard failure, and immediately alerts success, so unsupported/insecure clipboard contexts can fail or falsely report success. Keyboard inaccessibility is proven from the DOM/handlers; clipboard/browser behavior was not executed.

**Reproductie:** Enumerate the six service and two snippet divs at lines 441-469 and 530-609, confirm no interactive semantics, then search the script for keyboard events and find none. Inspect lines 727-730 to see the unawaited write followed by unconditional success feedback.

**Aanbevolen oplossing:** Use native buttons with visible labels, add an aria-live status region, await navigator.clipboard.writeText in try/catch with a fallback, and test keyboard activation plus both clipboard success and rejection.

### B135-002 — P3 — Small status labels fail contrast and the 400px grid cannot reflow on narrow screens

**Bewijs:** The dashboard grid has minmax(400px,1fr) with no media query. Its small white status/method labels use #3498db (3.15:1), #27ae60 (2.87:1), #f39c12 (2.19:1) and #e74c3c (3.82:1), all below 4.5:1. At widths under 440px including padding the grid necessarily overflows. CSS and ratios are proven; 200% zoom, keyboard focus rendering, touch and screen-reader output were not browser-tested. De pulse- en blinkanimaties op regels 331-385 lopen oneindig en hebben geen pauze of prefers-reduced-motion-override.

**Reproductie:** Compute contrast for the status/method declarations at lines 145-166 and 224-252. Evaluate the grid at 320 CSS px; the 400px minimum exceeds available width and no media rule overrides it.

**Aanbevolen oplossing:** Use AA-tested text colors/badge backgrounds, provide text/icons in addition to color, and replace the fixed minimum with a percentage-safe reflow rule. Add responsive, zoom and forced-colors browser tests. Stop of pauzeer automatisch bewegende content en respecteer reduced-motion.

### B135-004 — P2 — Phase-6 checklist prescribes destructive repository rollback without safety gates

**Bewijs:** The emergency rollback deletes the entire src directory with rm -rf, copies a local backup, checks out main and force-deletes the branch. Week/day rollback uses git reset --hard. No check verifies current repository/root, backup integrity, untracked files, clean status or exact commit targets. Although archived and only referenced by a stale review checklist, copying these commands can destroy current source and work. De gearchiveerde bestandsnamenworkflow bevat dezelfde procesfout met placeholder-brede rm -rf en git reset --hard zonder herstelbewijs; dit wordt als één rollback-root geteld.

**Reproductie:** Read the fenced rollback block and identify its targets/effects with shell dry reasoning; no guard or confirmation surrounds rm -rf src, git branch -D or git reset --hard. Do not execute the commands.

**Aanbevolen oplossing:** Add a DO-NOT-RUN archive banner or remove the block. For a maintained runbook, use immutable remote backups, validated paths, clean-worktree and branch checks, explicit confirmations, recoverable restore steps and a rehearsed rollback test.

## Deduplicaties en afwijzingen

- De fake-live status is samengevoegd in B134-003; de rollbackfamilie is één keer geregistreerd als B135-004.

## Niet getest

- Geen browser, keyboard/screenreader, 200%-zoom, touch, CDN/network, clipboard, API of echte scheduled workflow; browserimpact is alleen gemeld waar statisch bewezen.
