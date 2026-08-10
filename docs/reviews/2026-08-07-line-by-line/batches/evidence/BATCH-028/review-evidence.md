# BATCH-028 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 20/20 blobs, 1.595/1.595 fysieke regels en 60/60 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit de immutable Git-objecten gelezen;
applicatiebestanden zijn niet gewijzigd.

## Verificatie

- 62 primaire en 35 onafhankelijke gerichte tests slaagden.
- Ruff en Black waren schoon.
- Duplicate-OIDs en de afwijkende SAM-07-kopie zijn rechtstreeks vergeleken.

## Bevindingen

### B028-001 — P3 — stale SAM-07-kopie retourneert altijd false

`src/toetsregels/regels/SAM-07.py:63-95` berekent eerst een resultaat, maar
retourneert vóór de conversie onvoorwaardelijk `(False, ..., 0.0)`. De voorkeurskopie
onder `validators/` heeft een ander OID en deze fout niet; het defect is daarom
bewezen maar dormant in de huidige hoofdflow. Aanbevolen: één bron genereren en
tot verwijdering een automatische driftassertion afdwingen.

## Niet getest

- Geen actieve caller van de stale `regels/`-kopie gevonden.
- Geen browser, netwerk, credentials of externe AI gebruikt.
