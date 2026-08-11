# BATCH-165 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 9/9 bereiken, 5149/5149 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable architectuurdocumenten zijn gelezen; context-, path-, WAL-backup-, performance- en linkreproducties zijn veilig en offline uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B165-001 — P3 — Unlabelled deployment diagram resurrects the rejected cloud architecture

**Bewijs:** The unlabelled diagram under the active architecture diagrams directory presents a Production Environment with AWS ALB/WAF, a multi-node Kubernetes microservice cluster, PostgreSQL primary/standby, Redis, S3, DataDog/NewRelic and OpenAI. The canonical active ARCHITECTURE.md:13-40 and architecture README:9-34 explicitly say the application is local, SQLite, non-production, not cloud-native, and that Kubernetes/microservices are rejected enterprise fantasy. No proposal/archive/status marker distinguishes the diagram from current architecture.

**Reproductie:** Render or read the 63-line Mermaid blob and enumerate its production nodes, then compare them with ARCHITECTURE.md:13-40 and docs/architectuur/README.md:9-34. A base-tree reference search finds no status-bearing wrapper for this diagram.

**Aanbevolen oplossing:** Move the diagram to the dated enterprise archive or add an unmistakable rejected/historical banner in a wrapper document; replace the active diagram with the actual Streamlit/FastAPI, SQLite and external-provider deployment and link it from the canonical hub.

### B165-002 — P3 — Ready detector design fails its own threshold test and every trend calculation

**Bewijs:** The Ready for Implementation checklist gives executable detector code. Its threshold comparison uses strict `>` but the immediately following test expects exactly 10% over target to be warning; executing the snippet returns `ok`. Its trend code unpacks three values from `numpy.polyfit(..., 1)`, which returns two coefficients and raises ValueError before any severity is produced. The combined evaluator additionally lacks guards for zero target, zero standard deviation and zero median. The proposed detector module is absent, so reachability is dormant/design-time rather than current runtime.

**Reproductie:** Execute the documented check_threshold_breach with current=550, target value 500 and warning/error 10/20; it returns `ok`, not the asserted `warning`. Execute `slope, intercept, r_value = numpy.polyfit([0,1,2,3,4], [1,2,3,4,5], 1)`; it raises `ValueError: not enough values to unpack (expected 3, got 2)`.

**Aanbevolen oplossing:** Define inclusive boundary semantics and table-driven tests, use a regression API that actually returns correlation (or compute it separately), guard zero/degenerate baselines, validate metric direction and identifiers, and make the executable tests pass before retaining Ready for Implementation status.

### B165-003 — P3 — Unimplemented checklist marks future success metrics complete

**Bewijs:** Although the document is Ready for Implementation and its detector, CI, dashboard and deployment tasks remain unchecked, the success section marks every 30-day, 60-day and developer-experience outcome complete: 100% recording, 50+ baselines, regressions caught, zero critical misses, cost reduction and four-star feedback. At the base the proposed regression_detector.py, performance benchmark/export/compare scripts and .github/workflows/performance.yml do not exist. The checked boxes therefore cannot serve as implementation or outcome evidence.

**Reproductie:** Compare the all-checked outcome block with the unchecked implementation phases (for example lines 411-416 and 1361-1391), then use `git cat-file -e` for src/monitoring/regression_detector.py, scripts/monitoring/run_performance_benchmarks.py and .github/workflows/performance.yml; all are absent at b958ddb.

**Aanbevolen oplossing:** Reset outcomes to unchecked acceptance criteria until measured, attach dated machine-generated evidence and sample counts for every completed criterion, separate target metrics from observed results, and fail documentation validation when outcome boxes are checked without artifact links.

## Deduplicaties en afwijzingen

- Onveilige SQLite-copyvoorbeelden dedupliceren naar B163-004; ontbrekende ADR-links bleven secundaire P3-signalen.

## Niet getest

- Geen destructive reset, echte databasebackup/productiedata, netwerk/providers, clouddeployment of Mermaid/browser-rendering.
