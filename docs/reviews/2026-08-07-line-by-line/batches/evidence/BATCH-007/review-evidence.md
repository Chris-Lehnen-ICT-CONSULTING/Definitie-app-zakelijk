# BATCH-007 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 20/20 blobs, 2.381/2.381 fysieke regels en 119/119 Python-symbolen

Alle inhoud is rechtstreeks uit de immutable Git-objecten gelezen. Callers en
tests zijn in de base-tree opgezocht. Er zijn geen applicatiebestanden gewijzigd.

## Verificatie

- De primaire gecombineerde regressierun: 126 tests geslaagd.
- De onafhankelijke adversarial verificatie: 42 relevante tests geslaagd.
- Ruff en Black op alle toegewezen Pythonbestanden: geslaagd.
- Geen netwerk of echte credentials gebruikt.

## Bewezen bevindingen

### B007-001 — P2 — juridische verwijzingen worden gemist of corrupt geëxtraheerd

`src/domain/juridisch/patronen.py:76-105` staat bij klassieke wetboeken slechts
één titelwoord toe en gebruikt elders een onbegrensde `[A-Za-z\s]+`. De actieve
caller `DocumentProcessor._extract_legal_references` accepteert een niet-lege,
maar corrupte match en gebruikt dan geen fallback. Reproductie:
`Wetboek van Burgerlijke Rechtsvordering, artikel 1` geeft `[]`; twee artikelen
in één zin worden één match waarvan de wetnaam vervolgtekst bevat. Aanbevolen:
non-greedy herkenning met expliciete lookahead op interpunctie, einde of een
volgende verwijzing, plus parametrische tests voor multiword-wetboeken en twee
citaties in één zin.

### B007-002 — P1 — trusted-hostcontrole is door substringspoofing te omzeilen

`src/domain/autoriteit/betrouwbaarheid.py:134-175` zoekt vertrouwde domeinnamen
als substring in de volledige URL. Zowel
`https://wetten.overheid.nl.attacker.example/x` als
`https://evil.example/?next=rechtspraak.nl` worden vertrouwd; de tweede krijgt
voor `EXTERNE_BRON` score `0.6` en de motivatie “Vertrouwd overheidsdomein”.
De foutieve securitypredicate is bewezen; een actuele UI-route die hier een URL
aan levert is niet gevonden. Aanbevolen: `urlsplit`, hostname-normalisatie
(lowercase, IDNA, trailing dot) en alleen exacte host of subdomeinmatch.

### B007-003 — P2 — gemengde organisatiekeys zijn onbereikbaar

`src/domain/context/organisatie_wetten.py:59-98,162-188,230-233` definieert
`Reclassering` en `Justid`, maar uppercaset iedere lookup. Reproductie:
`OM` levert data, terwijl `Reclassering` en `Justid` `(False, {})` opleveren.
Er is geen actuele productiecaller gevonden. Aanbevolen: één `casefold()`-index
voor zowel statische keys als invoer en een round-triptest voor iedere key.

### B007-004 — P2 — vier van vijf juridische afkortingen werken niet

`src/domain/juridisch/patronen.py:58-65,126-129` bewaart `Sv`, `Sr`, `Rv` en
`RvS` mixed-case, maar zoekt uitsluitend uppercase. `BW` werkt; de andere vier
geven `None`. Er is geen actuele productiecaller gevonden. Aanbevolen: mapping
en invoer met dezelfde `casefold()`-normalisatie behandelen.

### B007-005 — P2 — geografische pluralia falen door asymmetrische casing

`src/domain/linguistisch/pluralia_tantum.py:113-142,164-180` bewaart geografische
namen met hoofdletters maar vergelijkt lowercase input en prefixen rechtstreeks
met die set. `Nederlandse Antillen` en `Verenigde Staten` falen in beide
casingvarianten. Er is geen actuele productiecaller gevonden. Aanbevolen: een
gecasefolde zoekindex, met originele spelling alleen voor weergave.

### B007-006 — P2 — classifier vertrouwt semantisch ongeldige AI-JSON

`src/services/classification/ontological_classifier.py:55-74,187-215,293-300`
controleert het responsecontract en de ranges niet. Een fake response met
`confidence=42` en `scores={"garbage":-999}` wordt `high` en betrouwbaar.
De fout is bewezen; buiten lazy container en tests is geen actuele `classify()`-
caller gevonden. Aanbevolen: strikt schema, finite confidence in `[0,1]`, exacte
U/F/O-keys, waarderanges, somcontrole en typevalidatie.

### B007-007 — P2 — definitietekst beïnvloedt definitievalidatie niet

`src/services/classification/ontological_classifier.py:260-291` documenteert
contextextractie uit `definition_text`, maar roept alleen `classify(begrip)` aan.
Een spy met `DEFINITION-SENTINEL` zag uitsluitend `classify("X")`. Er is geen
live caller gevonden. Aanbevolen: neem de tekst veilig op in de prompt/context,
of verwijder de parameter en hernoem het contract.

## Afgewezen vermoedens en niet getest

- De TYPE-fallback bij nulscore is expliciet DEF-138-gedrag en geen nieuwe bug.
- Niet getest: echte AI-responses, credentials of netwerkverkeer; actieve UI-
  exploitability van de hostspoof; visuele UI/a11y/responsive aspecten, omdat
  deze batch geen renderende UI bevat.
