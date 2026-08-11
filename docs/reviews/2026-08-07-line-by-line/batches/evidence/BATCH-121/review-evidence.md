# BATCH-121 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 1/1 bereiken, 6000/6000 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle byte-regels zijn lossless beoordeeld; na uitsluitend in-memory herstel van de bekende 0xEB-encodingfout waren JSON-, ID-, referentie- en graphgates groen.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### INV-ENCODING-D2C4CCDFC47C — P1 — Blocking text encoding error

**Bewijs:** The immutable blob contains exactly fourteen isolated Latin-1 0xEB bytes at lines 12310, 23559, 23659, 23759, 25412, 26736, 28436, 28580, 29830, 29882, 30784, 30984, 31034 and 46549; strict UTF-8 decoding fails at the first byte.

**Reproductie:** Read blob 054a58f4a8bbf6baaa1b4b71d16c14c3dae43b34 as bytes, attempt strict UTF-8 decoding, then enumerate each decode-error byte and its physical line.

**Aanbevolen oplossing:** Re-encode the fourteen intended ë characters as UTF-8 in a separately approved source fix and add strict UTF-8 plus JSON parsing to the artifact publication gate.

### B121-001 — P3 — Second fixed model silently omits enumeration literals and inheritance edges

**Bewijs:** After replacing only the fourteen invalid Latin-1 0xEB bytes with their intended UTF-8 encoding in memory, fixed_v2 is structurally identical to fixed.json except for exactly twenty-two removed model definitions and no additions. Nineteen removed Literal objects empty the Scantype, Status identiteit, Kwalificatie zekerheid and Grondslagsoort enumerations, whose v2 classes expose literals=null. Three removed Generalization objects eliminate direct Natuurlijk Persoon inheritance for Strafrechtketenpartij, Externe persoonsrol and Natuurlijke Justitiabele2. No repository consumer or change rationale was found, so the semantic loss is dormant and its intent remains uncertain.

**Reproductie:** Read both immutable Git blobs, repair v2 in memory with raw.replace(b'\xeb', 'ë'.encode('utf-8')), parse both JSON documents, recursively index model definitions by id and compare the id sets. The result is removed=22 (Literal=19, Generalization=3), added=0; inspect the four surviving v2 enumeration classes and observe literals is null.

**Aanbevolen oplossing:** Restore the omitted literals and inheritance edges if they were lost during export, or document and version the intentional semantic change. Add a golden structural-diff gate with an explicit allowlist for removed model IDs and validate that enumerations retain their required literals and role hierarchies retain an identity-provider path.

## Niet getest

- Geen externe OntoUML-importer of visuele renderer; de bron is niet gewijzigd en de resterende ranges B126-B131 zijn nog niet inhoudelijk beoordeeld.
