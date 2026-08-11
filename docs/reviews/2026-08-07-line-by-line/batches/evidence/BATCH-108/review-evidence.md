# BATCH-108 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 1/1 bereiken, 67/67 fysieke regels en 0/0 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- De gerichte selectie gaf 73 groene en acht verwachte rode gevallen; de rode gevallen bewijzen de geregistreerde contract- en omgevingsproblemen. Ruff, Black en bash -n waren schoon.
- Object-ID's, ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B108-001 — P3 — Juridisch RAG-corpus mist bron consolidatie en versieprovenance

**Bewijs:** Het bestand bevat titel, BWBR-id en tekst maar geen bron-URL, ophaaldatum, consolidatie- of geldigheidsdatum of contenthash. De RAG-smokecaller ingest alleen tekst en bestandsnaam en hergebruikt iedere reeds gevulde vaste collection zonder contenthash.

**Reproductie:** Inspecteer bestand en ingest_wettekst; wijzig de fixture na eerste ingest en observeer in een tijdelijke RAG-DB dat de nonempty-collection-fastpath hergebruikt. Juridische actualiteit zelf is niet getest.

**Aanbevolen oplossing:** Voeg officiële bron, as-of of geldigheid en SHA-256 toe en koppel collection-versie of re-ingest aan de contenthash.

## Niet getest

- Geen echte provider, credential, netwerk, productiedatabase of browser; muterende scripts zijn alleen statisch, met mocks of op tijdelijke data onderzocht.
