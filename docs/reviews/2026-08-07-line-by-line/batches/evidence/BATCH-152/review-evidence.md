# BATCH-152 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 9/9 bereiken, 5627/5627 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable analyses zijn gelezen; relevante unit-tests, offline runtime- en parserreproducties, documentclaims en secret-shape-scans zijn gecontroleerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B152-001 — P2 — RuleCache evidence report declares high confidence from a verifier that reports failure and still exits successfully

**Bewijs:** The report calls the verifier direct evidence and concludes that all modules receive one shared dictionary, yet its own gaps section admits there is no run output, open-call counter or direct I/O trace. A fresh offline run from /private/tmp logged FAIL: Modules got different dict references and then printed All 4 modules got same dict reference and US-202 fix is working correctly before exiting zero; it logged only one load, so one loader execution is plausible, but the claimed shared-reference proof is internally false-green. This is the already recorded script defect B107-003; the new issue is the report's high-confidence conclusion.

**Reproductie:** Run scripts/verify_rulecache_behavior.py from a writable temporary working directory with the base src on PYTHONPATH. Observe the explicit FAIL followed by the unconditional success conclusion and exit code zero. Compare this with report lines 290-307, which explicitly admit that no direct I/O proof or benchmark output was found.

**Aanbevolen oplossing:** Replace narrative inference with a failing automated contract that counts function-body executions and file opens, make every invariant affect the exit code, pin the measured revision and raw output, and supersede mutually contradictory RuleCache analyses.

### B152-002 — P2 — Active architecture review still escalates two resolved conditions as current critical incidents

**Bewijs:** Front matter marks the review active, while its summary and priority list say a complete working OpenAI key is currently present in four tracked documents and make dev is broken because scripts/run_app.sh is missing. At the immutable base, those four documents contain zero unredacted sk-proj tokens and the Makefile dev target calls the existing scripts/deployment/run_app.sh. The historic key's revocation and remote-history state were not tested, but the document's current-tree and startup claims are demonstrably stale.

**Reproductie:** Scan the four named documents at the base for sk-proj followed by at least 20 key characters; the count is zero. Inspect Makefile:7-10 and verify scripts/deployment/run_app.sh exists. Contrast those results with lines 15-17, 84-88, 104-105 and 127-132 of the review.

**Aanbevolen oplossing:** Change status to historical or superseded, preserve the reviewed commit as snapshot metadata, regenerate current-state claims from executable checks, and keep unresolved history or revocation questions separate from resolved working-tree findings.

### B152-003 — P3 — Concrete classifier fix guide targets removed files and proposes a main-thread-only timeout

**Bewijs:** The proposed regex protection installs signal.SIGALRM inside classifier execution. Python raises ValueError when signal.signal is called outside the main interpreter thread, so the fix is incompatible with worker execution and non-POSIX platforms. The guide's target src/services/ufo_classifier_service.py and its debug verification tests are absent from the immutable tree; the maintained classifier is src/ontologie/improved_classifier.py. The guide remains a TODO and is operationally dormant.

**Reproductie:** Submit a function that calls signal.signal(signal.SIGALRM, ...) to ThreadPoolExecutor; its future raises ValueError: signal only works in main thread of the main interpreter. Run git cat-file -e for the documented source and debug test paths; they are absent at the base.

**Aanbevolen oplossing:** Archive the guide or rebase it on the maintained classifier, prefer bounded input and safe regexes or a timeout mechanism valid in the actual execution context, and publish runnable tests against current paths before presenting concrete fixes.

## Deduplicaties en afwijzingen

- Het false-green verifierscript dedupliceert naar B107-003; B152-001 registreert de zelfstandige evidence-integriteit.

## Niet getest

- Geen externe provider/API/netwerk, echte sleutelwaarden, remote Git-historie, dependency-installatie, destructive rollback of browser/UI-runtime.
