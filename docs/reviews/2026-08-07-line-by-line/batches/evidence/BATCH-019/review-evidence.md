# BATCH-019 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 3/3 blobs, 1.321/1.321 fysieke regels en 0 Python-symbolen

## Verificatie

Alle regels zijn rechtstreeks uit Git-objecten gelezen. De finding is door een
tweede reviewer statisch bevestigd; de dormant write is niet uitgevoerd.

## Bevindingen

### B019-001 — P3 — ontwerpspecificatie schrijft naar filesystem-root

`prompts/implementation/prompt-generator-subagent-spec.md:19-26,219-222,
445-459,844-849` gebruikt consequent `/prompts/{slug}.md`. De leading slash
resolveert buiten de repository; containment en slugallowlist ontbreken. Er is
geen implementatie/runtimecaller gevonden. Aanbevolen: expliciete repo-root,
`repo_root / "prompts" / slug`, containmentcheck en allowlist-slugfunctie.

## Niet getest

- De write is vanwege read-only review en dormant ontwerpstatus niet uitgevoerd.
- Geen externe agent- of modelrun.
