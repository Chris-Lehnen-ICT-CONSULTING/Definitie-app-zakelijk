# BATCH-043 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 7/7 blobs, 2993/2993 fysieke regels en 107/107 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatiebestanden zijn niet gewijzigd.

## Verificatie

- 176 primaire gerichte tests en 56 onafhankelijke crosstests groen; workflow- en UI-reproducties met fakes; Ruff en Black schoon.
- De onafhankelijke verifier heeft alle kandidaten gedisponeerd en de P1-codepaden opnieuw beoordeeld.

## Bevindingen

### B043-001 — P1 — Expert edits persist before an impossible approval transition

**Bewijs:** Edits are written before submit_for_review, while queued records already have REVIEW status and review-to-review is rejected.

**Reproductie:** Run the actual workflow with a queued review record; transition fails after the edit write.

**Aanbevolen oplossing:** Provide one transactional approve command that includes edits, status and audit.

### B043-002 — P1 — UFO update is outside the approval transaction

**Bewijs:** Category update is separate, its result is ignored, and approval then reloads state independently.

**Reproductie:** Make category update succeed and approval fail, then invert the failures; state becomes partial or approval uses the old category.

**Aanbevolen oplossing:** Commit category, edits, approval and audit in one workflow transaction with a required result.

### B043-003 — P2 — Expert preview crashes on an invalid format specifier

**Bewijs:** A conditional is embedded inside a numeric format specifier.

**Reproductie:** Preview a score of 0.8; Python raises ValueError for the invalid '.2f if ...' specifier.

**Aanbevolen oplossing:** Compute the score label before formatting and test numeric and missing scores.

### B043-004 — P2 — Synonym review swallows partial failures and reports success

**Bewijs:** Helpers suppress item failures and the renderer always shows full success then reruns.

**Reproductie:** Make the second of two updates raise; both calls occur, no failure result returns, and the UI follows the success path.

**Aanbevolen oplossing:** Return per-item structured outcomes and display partial counts before rerun.

### B043-005 — P2 — Synonym reviews use a hardcoded actor

**Bewijs:** Review persistence always passes reviewed_by='user'.

**Reproductie:** Capture calls for two principals; both are stored as user.

**Aanbevolen oplossing:** Require the authenticated principal and reject audit actions without identity.

### B043-006 — P2 — Save Draft claims success without persisting

**Bewijs:** The active control only displays that draft functionality is coming soon and performs no write.

**Reproductie:** Click Save Draft with a fake repository; no persistence method is called while the UI presents a saved-style message.

**Aanbevolen oplossing:** Disable and label the control as unavailable or implement real draft persistence with failure feedback.

## Niet getest

- Geen live approvaltransactie of echte principal/gebruikersdata gebruikt.
- Visueel contrast, toetsenbord, screenreader, touch en responsive viewports zijn niet met een browserbackend getest.
