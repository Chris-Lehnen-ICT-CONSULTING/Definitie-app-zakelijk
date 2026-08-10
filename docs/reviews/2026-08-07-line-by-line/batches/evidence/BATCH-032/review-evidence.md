# BATCH-032 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-root`
- Scope: 20/20 blobs, 2.712/2.712 fysieke regels en 120/120 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen.
De huidige hoofdflow gebruikt de alternatieve JSON-service; deze classimplementaties
zijn latent/dormant tenzij een externe consumer de publieke loader gebruikt.

## Verificatie

- 92 primaire tests slaagden; onafhankelijke configgestuurde reproducties
  bevestigden alle vijf bevindingen.
- Ruff en Black waren schoon.

## Bevindingen

### B032-001 — P2 — INT-08 laat meerdere foutieve negaties samen passeren

`INT_08.py:58-130` reduceert matches tot unieke woorden. Zodra éénzelfde negatie
ergens na `die` voorkomt, geldt zij overal als toegestaan en wordt vóór de
foute-voorbeeldcheck geretourneerd. `persoon die niet rookt en geen bewijs heeft`
passeert volledig. Aanbevolen: occurrence-spans en relatieve-bijzingrenzen,
foute voorbeelden vóór allow-return.

### B032-002 — P3 — INT-09 maakt punt-eindigende regexen onmatchbaar

`INT_09.py:35-43` wikkelt ieder configpatroon in woordgrenzen. Patronen als
`etc\.` en `enz\.` matchen daardoor niet; `..., etc.` passeert. Aanbevolen:
configregex exact compileren en grenzen alleen bij letterlijke tokens toevoegen.

### B032-003 — P2 — zes SAM-validators implementeren een ander contract

SAM-02..06 en SAM-08 valideren andere semantiek of negeren vereiste
repository-/voorkeursterm-/synoniemcontext. Eigen contractcases voor alle zes
passeerden of gaven een oordeel zonder de benodigde data. Aanbevolen: een
expliciete regel-ID→implementatiecontractlaag, ontbrekende parameters als
unavailable en parametrische canonical good/bad tests.

### B032-004 — P3 — STR-01/02 missen hoofdletter- en begripkickoff

STR-01 gebruikt case-sensitive `re.match`, waardoor `Is een ...` passeert.
STR-02 negeert het losse `begrip` en detecteert alleen herhaling als die al in de
definitietekst staat. Aanbevolen: `IGNORECASE`/strip en het eerste lemma-token
direct met het genormaliseerde begrip vergelijken.

### B032-005 — P3 — STR-08/09 geven false positives en misleidende labels

Een duidelijke cumulatieve `en`-zin faalt; `met of zonder` faalt ondanks whitelist
door een overlappende losse `of`-match. Capture groups leveren bovendien lege of
afgeknotte labels. Aanbevolen: ambiguïteit modelleren, overlappende submatches
onderdrukken en noncapturing groepen/match.group(0) gebruiken.

## Niet getest

- Geen interne productiecaller van de classloader gevonden.
- Geen browser, a11y, externe libraryconsumer, AI, netwerk of credentials getest.
