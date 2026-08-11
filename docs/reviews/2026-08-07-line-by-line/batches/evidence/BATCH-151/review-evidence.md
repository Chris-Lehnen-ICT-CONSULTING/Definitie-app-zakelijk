# BATCH-151 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 10/10 bereiken, 4822/4822 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable analyses zijn gelezen; relevante unit-tests, offline runtime- en parserreproducties, documentclaims en secret-shape-scans zijn gecontroleerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B151-001 — P1 — Secret-response runbook exposes the current key and its history scrub expression cannot match leaked keys

**Bewijs:** The incident instructions print the complete OPENAI_API_KEY to terminal output. They then recommend git filter-repo with the expression sk-proj-*==[REDACTED]==. The installed git-filter-repo parser treats that entire value as one literal because it has neither a regex or glob prefix nor the required ==> replacement delimiter. It therefore does not match ordinary sk-proj keys, while filter-repo can still rewrite repository history and create false assurance that the secret was scrubbed.

**Reproductie:** Pass the exact expression through git_filter_repo.FilteringOptions.get_replace_text: it returns one literal named sk-proj-*==[REDACTED]==, zero regexes and the default replacement. Compare it with the parser's documented password==>replacement form. Do not execute the history rewrite or print a real credential.

**Aanbevolen oplossing:** Revoke and rotate first, never print a credential, compare non-reversible fingerprints when needed, build a securely stored exact or correctly prefixed regex replacement file, test it on a disposable mirror, verify all-history gitleaks results, and only then coordinate a backed-up force-push and mandatory reclone.

### B151-002 — P2 — Security remediation downgrades dependencies and overwrites the hashed lock from the local environment

**Bewijs:** The runbook installs Pillow 11.3.0 and urllib3 2.5.0 directly, then replaces requirements.txt with pip freeze. The immutable base declares Pillow 12.3.0 and urllib3 2.7.0 in requirements.in and uses uv-generated universal hash locks. Following the document therefore downgrades current pins and destroys the source-to-lock relationship. Its final verification command imports pillow, but the Python import package is PIL; the documented command raises ModuleNotFoundError in the project environment.

**Reproductie:** Compare lines 260-273 with requirements.in and the generated requirements.txt header. Run the exact python -c import pillow, urllib3 command; it exits nonzero with No module named pillow. No claim about current CVE status is needed or made.

**Aanbevolen oplossing:** Label the 2025 version snapshot historical, update direct requirements only in requirements.in, regenerate with make lock, verify with make lock-check and make audit, and use import PIL for package-import validation.

## Deduplicaties en afwijzingen

- Geen echte credentialwaarde is gelezen of weergegeven; de finding betreft de aantoonbaar onveilige runbookprocedure.

## Niet getest

- Geen externe provider/API/netwerk, echte sleutelwaarden, remote Git-historie, dependency-installatie, destructive rollback of browser/UI-runtime.
