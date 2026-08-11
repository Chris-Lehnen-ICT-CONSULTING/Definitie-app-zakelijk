# BATCH-091 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 8/8 blobs, 2744/2744 fysieke regels en 113/113 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Veilige selectie: 49 groen, 8 rood en 1 skip; PER-007 gaf 2 groen/5 rood en de red-phasegroep 3 groen/3 rood.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B091-001 — P2 — Legacy parity suite compares the same current implementation

**Bewijs:** Both arms construct ServiceAdapter and all twelve cases are non-strict xfail, so no legacy parity is established.

**Reproductie:** Collect the suite and inspect both factories; they resolve to the same implementation class.

**Aanbevolen oplossing:** Use an independent golden/legacy reference or replace the suite with one strict current contract.

### B091-002 — P2 — Ontology integration leaks environment state and passes after traceback

**Bewijs:** The module mutates environment variables at import and catches every exception.

**Reproductie:** Run without credentials: an API-key traceback is printed and pytest still reports one pass.

**Aanbevolen oplossing:** Use monkeypatch and an offline generator, restore state and assert semantic output.

### B091-003 — P2 — PER-007 acceptance suite uses a removed context-manager constructor

**Bewijs:** Five of seven cases call HybridContextManager without required ContextConfig and several core assertions are swallowed.

**Reproductie:** Run the file: five failures and two passes.

**Aanbevolen oplossing:** Use the current factory/config and remove all RED-era catch blocks before restoring the gate.

### B091-004 — P2 — Intentionally red PER-007 tests remain normal integration tests

**Bewijs:** The module says tests MUST FAIL but carries the integration marker and is kept green only by an explicit CI deselect.

**Reproductie:** Run directly: three pass and three fail.

**Aanbevolen oplossing:** Move unresolved RED contracts to an opt-in profile or implement and convert them to green invariants.

### B091-005 — P3 — History-removal tests swallow arbitrary failures and use the default database

**Bewijs:** The suite allows one forbidden import, catches unrelated render/repository errors and constructs live/default repositories.

**Reproductie:** Raise RuntimeError or database locked in guarded paths; the tests treat those outcomes as acceptable.

**Aanbevolen oplossing:** Require zero forbidden imports, inject a temporary DB and catch only documented exceptions.

## Niet getest

- Geen echte provider, browser of productiehistoriedatabase; rode/stale testcontracten zijn lokaal en offline beoordeeld.
