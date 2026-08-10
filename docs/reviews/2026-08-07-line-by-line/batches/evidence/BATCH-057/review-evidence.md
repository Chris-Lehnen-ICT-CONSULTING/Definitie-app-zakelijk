# BATCH-057 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 4/4 blobs, 808/808 fysieke regels en 116/116 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- 319 scoped tests groen voor B056-B058; drie Nederlandse wetstitels en het metadataregister zijn direct tegen productiecode gereproduceerd.
- Ruff en Black waren schoon voor alle toepasselijke Pythonbestanden; object-ID's, EOF-ranges en symbol-memberships matchten het batchmanifest.

## Bevindingen

### B057-001 — P2 — Legal structure tests normalize missing common Dutch statute names

**Bewijs:** The recognizer returns no statute for Algemene wet bestuursrecht, Gemeentewet and Wet politiegegevens, so active chunk provenance is empty.

**Reproductie:** Run title detection for those three statute names; each returns None while Wetboek van Strafrecht succeeds.

**Aanbevolen oplossing:** Recognize suffix-style Dutch statute titles and scan bounded header lines instead of relying on the narrow current grammar.

### B057-002 — P3 — Metadata schema registry omits the supported api source type

**Bewijs:** BRON_TYPES contains api but the schema registry has no api model, so invalid fields pass through without the promised validation.

**Reproductie:** Validate api metadata with pagina_nummer='veertien'; the payload is returned unchanged.

**Aanbevolen oplossing:** Provide a strict schema for every declared source type and gate registry set equality; document explicit free-form variants separately.

## Niet getest

- Geen volledige echte wet-PDF-ingestie, extern netwerk of visuele UI-test; actieve chunkingcallers zijn statisch gevolgd.
