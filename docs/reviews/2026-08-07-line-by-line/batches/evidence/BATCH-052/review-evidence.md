# BATCH-052 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 12/12 blobs, 1725/1725 fysieke regels en 128/128 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Gecombineerde kandidaatselectie voor B049/B051/B052/B053: 185 groen en 1 verwachte xfail; classificatie- en importstategrenzen zijn offline gecontroleerd.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B052-001 — P2 — Classifier tests allow unjustified HIGH confidence normalization

**Bewijs:** Assertions use broad lower bounds and do not reject HIGH confidence derived from weak or absent signals.

**Reproductie:** Return confidence 1.0/HIGH for a weak 0.1 winner or zero evidence; the relevant tests do not enforce calibration.

**Aanbevolen oplossing:** Add calibrated exact/range expectations for weak, empty, tied and dominant evidence.

### B052-002 — P3 — Import test permanently prepends scripts to sys.path

**Bewijs:** The module mutates sys.path at import time and never restores it.

**Reproductie:** Import the test module and compare sys.path before and after; the scripts path remains at index zero.

**Aanbevolen oplossing:** Use monkeypatch.syspath_prepend inside a fixture or import by file spec and restore state.

## Niet getest

- Geen echte AI-provider of externe classificatiecall; alleen unitcontracten en processtate.
