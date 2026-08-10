# BATCH-022 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 1/1 blob, 488/488 fysieke regels en 0 Python-symbolen

## Bevindingen

### B022-001 — P3 — template bevat ongeldige en tegenstrijdige consensuslogica

`prompts/templates/TEMPLATE-deep-analysis.md:130-143` bevat Python
`CRITICAL_THRESHOLD = 75%`, wat een `SyntaxError` geeft. Regels 308-331
vervangen de eerder gewogen consensus bovendien door een ongewogen ratio.
Aanbevolen: `0.75/0.60/0.50` en één canonieke gewogen formule met executable
doctest. Het betreft een Markdowntemplate; runtime-import is niet van toepassing.

## Niet getest

- Geen gegenereerde externe analyse- of modelrun.
