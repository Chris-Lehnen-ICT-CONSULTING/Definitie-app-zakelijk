# BATCH-109 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 8/8 bereiken, 3715/3715 fysieke regels en 0/0 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De 17 relevante validatiecontracttests waren groen; JSON, YAML en de vier JSON Schema-documenten parseerden en valideerden structureel.
- Object-ID's, ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B109-001 — P2 — Pinned v1 validation schema is published without the promised compatibility adapter or regression gate

**Bewijs:** The active validation interface publishes CONTRACT_VERSION='1.0.0', while the latest version/system payload and pinned v1.0.0 metadata payload are mutually incompatible under that same semantic version. The contract document promises a v1-to-latest adapter, golden fixtures and compatibility tests, but all three are absent; CI checks schema syntax only.

**Reproductie:** Validate a minimal latest payload against latest (pass) and pinned v1 (fail: metadata required), then a minimal v1 payload against v1 (pass) and latest (fail: version/system required). Confirm the adapter and golden fixture paths named by the contract do not exist.

**Aanbevolen oplossing:** Assign a real new semantic version to the breaking latest contract and implement a tested v1 adapter with golden compatibility fixtures, or formally withdraw the pinned v1 contract.

### B109-002 — P2 — Critical active test plan reports stale rule counts, coverage and system contracts as current

**Bewijs:** The document marks itself KRITIEK, ACTIEF and monthly updated but is dated 2025-09-08. It specifies 45 validation rules and OpenAI, while the base contains 53 rule JSON files. It reports 76% current coverage and other quality metrics without evidence, while the canonical CI gate is a 45% ratchet. Its configured tests/bdd/features path is absent.

**Reproductie:** Count src/toetsregels/regels/*.json at the immutable base (53), inspect Makefile test-cov-ci (--cov-fail-under=45), and verify tests/bdd/features does not exist; compare these facts with lines 190-206, 231-315 and 390-401.

**Aanbevolen oplossing:** Generate commit- and date-bound metrics automatically, distinguish targets from measurements, link every current claim to evidence and fail CI when the active plan becomes stale.

### B109-003 — P2 — Published traceability matrix points only to missing canonical documents and assigns stories to multiple parent epics

**Bewijs:** All 14 epics, 104 epic/story assignments and 93 requirements lack the canonical paths prescribed by the developer guide. Ten story IDs have multiple parent epics. EPIC-005 referenced_by lists EPIC-004 stories US-021..023 instead of its own story set. This is related to B100-008/B100-009 but is the separately broken published artifact.

**Reproductie:** Load the matrix, build story-to-epics, and compare every expected docs/backlog canonical path with git ls-tree at the base; results are 14/14, 104/104 and 93/93 missing plus ten multi-owner stories.

**Aanbevolen oplossing:** Regenerate only from a validated canonical inventory and enforce existing paths, unique story ownership and bidirectional relation equality in CI.

## Niet getest

- Geen externe contractconsumer, OntoUML-importer, browser, provider, netwerk of echte credentials; document- en modelscope is offline beoordeeld.
