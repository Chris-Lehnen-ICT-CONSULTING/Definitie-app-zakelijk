# BATCH-075 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-root`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 8/8 blobs, 1207/1207 fysieke regels en 131/131 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- Alle 83 tests groen; de hoofdgate selecteerde 68 en sloeg alle 15 modulebreed slow gemarkeerde TokenBucket-tests over.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.
- Dedupe/relatie: Serializer temp-file concurrency is verwant maar niet identiek aan B049-003, dat uitsluitend HMAC-keyaanmaak betrof.

## Bevindingen

### B075-001 — P2 — Smart rate limiter does not enforce its timeout contract

**Bewijs:** TokenBucket sleeps in 100 ms chunks without remaining-budget capping and uses wall time; HIGH and CRITICAL acquisition calls it without the requested timeout.

**Reproductie:** A 10 ms TokenBucket timeout returns after 101 ms; HIGH acquisition with a 10 ms timeout returns true after 501 ms. A backward clock step lets timeout zero succeed.

**Aanbevolen oplossing:** Use one monotonic deadline, cap every sleep to remaining time and pass the budget through all priority paths.

### B075-002 — P2 — Concurrent safe serializer writes collide on one temporary path

**Bewijs:** Atomic-write tests cover only one writer; safe_save always uses target.suffix.tmp, so concurrent writers share and move the same file.

**Reproductie:** Synchronize two writers immediately before os.replace; one succeeds and the other raises FileNotFoundError for the moved temp file.

**Aanbevolen oplossing:** Create a unique same-directory temp file per writer, fsync it and atomically replace; test thread and process concurrency.

### B075-003 — P3 — Serializer reserves ordinary __datetime__ dictionaries without an envelope

**Bewijs:** The roundtrip suite covers actual datetime only; object_hook converts any dictionary containing __datetime__ and discards normal mapping semantics.

**Reproductie:** Save {'__datetime__':'not-a-date','business':'kept'}; save succeeds and safe_load raises ValueError.

**Aanbevolen oplossing:** Use a versioned tagged envelope with an exact shape or escape reserved user dictionaries, then test collision roundtrips.

### B075-004 — P3 — Moderate HTML sanitization preserves executable SVG onbegin

**Bewijs:** The test explicitly requires onbegin to remain; public default-moderate HTML detection returns the SVG animate attribute unchanged. Active SecurityService uses strict mode and no moderate unsafe-HTML renderer caller was found.

**Reproductie:** Sanitize an SVG animate tag with onbegin at moderate level; the payload and handler remain unchanged.

**Aanbevolen oplossing:** Use a maintained parser allowlist, remove every on* attribute and restrict SVG; add browser-backed vectors if moderate HTML remains public.

### B075-005 — P3 — Rule cache monitoring suite passes when monitoring is absent

**Bewijs:** The availability assertion is a tautology and every behavioral assertion is conditional on a truthy monitor.

**Reproductie:** Set the RuleCache monitor to None and call all six monitoring tests; all return successfully.

**Aanbevolen oplossing:** Require monitoring in monitoring-specific tests and separately test the intentional disabled fallback with explicit assertions.

### B075-006 — P3 — Default local unit command excludes every TokenBucket behavior test

**Bewijs:** The whole module is marked slow, so make test's unit-and-not-slow selection deselects all 15 cases; unit-only coverage jobs still include them.

**Reproductie:** Run the file with the make-test marker expression; pytest reports 15 deselected and exits with no tests selected.

**Aanbevolen oplossing:** Mark only true timing cases slow and replace waits with a fake clock so core input and timeout contracts stay in the fast gate.

### B075-007 — P3 — Export sink AST guard ignores async functions and dead guard calls

**Bewijs:** The scanner selects only ast.FunctionDef and accepts a guard name anywhere in ast.walk; a new async sink or an unreachable nested call can bypass the claimed fail-closed registry.

**Reproductie:** Parse one async _export function and one sync function; _sink_functies returns only the sync function.

**Aanbevolen oplossing:** Include AsyncFunctionDef and verify direct live data flow to each sink, backed by behavior-level sabotage tests.

### B075-008 — P3 — Normal security middleware test accepts server errors as success

**Bewijs:** The normal-request assertion requires only status not equal to 403 and explicitly permits 500, so application failure still satisfies the named pass-through behavior.

**Reproductie:** Return status 500 from the normal route; the assertion remains true.

**Aanbevolen oplossing:** Require the expected successful status and response schema, with separate explicit tests for backend failure headers.

### B075-009 — P3 — Token bucket accepts a zero refill rate and then divides by zero

**Bewijs:** Tests validate requested tokens and timeout but not constructor rate or capacity; RateLimitConfig also has no runtime bounds.

**Reproductie:** Construct TokenBucket(rate=0, capacity=1), exhaust it and acquire; wait-time calculation raises ZeroDivisionError.

**Aanbevolen oplossing:** Validate finite positive rate and capacity at configuration and constructor boundaries with zero, negative, NaN and infinity tests.

## Niet getest

- Geen multiprocess/NFS serializerstress, live providerload of browser-XSS-keten; thread-, fake-clock- en sanitizerrepro's zijn wel deterministisch bewezen.
