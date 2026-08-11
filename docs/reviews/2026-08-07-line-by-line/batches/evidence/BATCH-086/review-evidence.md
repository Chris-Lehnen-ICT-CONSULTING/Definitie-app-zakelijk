# BATCH-086 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 13/13 blobs, 3664/3664 fysieke regels en 133/133 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De functionaliteits- en contextmodules bevatten respectievelijk 4 en 13 permanente skips; de DEF110-cases bleven groen zonder hun bedoelde doel te bereiken en de bredere selectie gaf 22 groen en 6 rood.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: Credential-eager initialisatie relateert aan PILOT-004; het overlappende B088-providercontract is in B086-001 samengevoegd.

## Bevindingen

### B086-001 — P2 — Functionality suites skip the default Anthropic provider and swallow failures

**Bewijs:** Four functionality modules gate only on OPENAI_API_KEY although the application defaults to Anthropic; credential-free runs skip all four and error paths print or return unchecked booleans.

**Reproductie:** Run the four modules without OpenAI credentials or inject an export failure; the modules skip or return False without a pytest failure.

**Aanbevolen oplossing:** Use provider-independent injected fakes, gate only explicit live-provider tests and assert every failure.

### B086-002 — P3 — All context-flow performance cases remain unconditionally skipped

**Bewijs:** All thirteen cases carry unconditional not-implemented skips although the imported context components exist.

**Reproductie:** Run the file: thirteen tests skip and none measures the current context flow.

**Aanbevolen oplossing:** Rewrite against current async prompt/context APIs with deterministic clocks and isolated caches.

### B086-003 — P2 — DEF-110 startup tests target a nonexistent tests/src/main.py and still pass

**Bewijs:** The subprocess cwd resolves to tests, so src/main.py is absent; two cases nevertheless pass on empty logs and blocking readline weakens the timeout.

**Reproductie:** Resolve the calculated target and run the first two tests: target_exists is false while both tests pass.

**Aanbevolen oplossing:** Use a repository-root fixture, communicate(timeout=...), and require process readiness and expected logs.

### B086-004 — P3 — Never-zero confidence tests accept exactly zero

**Bewijs:** The asserted lower bound is inclusive, contradicting the test name and contract.

**Reproductie:** Return confidence 0.0 from a fake classifier; every case remains green.

**Aanbevolen oplossing:** Assert confidence greater than zero and exact expected categories/bounds.

## Niet getest

- Geen echte AI-provider, credential, netwerk, productie-DB of browser; alle provider- en logrepro's waren offline.
