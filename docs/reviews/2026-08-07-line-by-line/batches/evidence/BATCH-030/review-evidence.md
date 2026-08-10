# BATCH-030 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 20/20 blobs, 644/644 fysieke regels en 16/16 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen;
applicatiebestanden zijn niet gewijzigd.

## Verificatie

- Onderdeel van 206 primaire gerichte tests; Ruff en Black waren schoon.
- Setleden, bestandsnamen, metadata en duplicaten zijn mechanisch vergeleken.

## Bevindingen

### B030-001 — P3 — regelset-ID's verwijzen naar niet-bestaande regels

`per-categorie/arai.json:5-13` gebruikt ARAI01..06 en meerdere context-/prioriteitssets
gebruiken `ARAI06`, terwijl canonieke blobs `ARAI-01`..`ARAI-06` heten. Geen van
de negen categorieleden is via bestandsnaam laadbaar; ARAI01/02-factories zoeken
bovendien JSON naast de validator. De primaire V2-flow gebruikt deze legacysets
niet. Aanbevolen: één canonieke ID-resolver en een startup/CI foreign-key-gate
over alle setleden.

### B030-002 — P3 — context- en prioriteitssets bevatten duplicaten en stale leden

Elk contextbestand bevat 37 rijen maar slechts 34 unieke IDs. Metadata-gebaseerde
vergelijking toont daarnaast ontbrekende canonieke regels en het ongeldige ARAI06.
Managerresultaten behouden 36 laadbare rijen maar slechts 33 unieke regels. De
actieve V2-flow gebruikt deze legacysets niet en de oudere validator dedupliceert.
Aanbevolen: sets genereren uit regelmetadata of exacte uniciteit/set-equality/FK's
in CI afdwingen.

## Niet getest

- Actieve V2-impact van deze legacy setbestanden is niet aangetoond.
- Geen browser, externe dienst of credentials gebruikt.
