# BATCH-168 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 7/7 bereiken, 5391/5391 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documenten zijn gelezen; provider-, parallelisatie-, classifier-, compliance- en SQLite-concurrencycontracten zijn veilig offline gereproduceerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B168-001 — P2 — Ready action plan encodes the wrong canonical category for woordvoerder

**Bewijs:** The READY FOR IMPLEMENTATION plan calls woordvoerder-to-TYPE a false positive but states the expected category is PROCES, repeats that output in its proposed regression at lines 267-326, and makes PROCES a success criterion at lines 389-395. The base canonical config config/classification/term_patterns.yaml:29-35 instead contains an explicit DEF-138 domain override woordvoerder: EXEMPLAAR with the rationale 'persoon in rol'. ImprovedOntologyClassifier applies that override and returns exemplaar with confidence 0.95.

**Reproductie:** At base b958ddb run ImprovedOntologyClassifier().classify('woordvoerder'); the actual result is EXEMPLAAR, confidence 0.95, reason domain override. Compare that result and config/classification/term_patterns.yaml:34 with the plan's proposed assertion at lines 289-292, which requires PROCES.

**Aanbevolen oplossing:** Mark the action plan resolved/superseded and make the canonical classification config plus an approved ontology decision the source of truth. Preserve an active regression for woordvoerder -> EXEMPLAAR; do not derive the semantic category from substring or suffix heuristics.

## Deduplicaties en afwijzingen

- Bestaande classifier-/configbevindingen zijn niet dubbel geteld; alleen de READY-plancontradictie blijft staan.

## Niet getest

- Geen echte AI/providers/netwerk/credentials, productiedata, juridische certificering, browser/UI/a11y of live traffic-concurrency.
