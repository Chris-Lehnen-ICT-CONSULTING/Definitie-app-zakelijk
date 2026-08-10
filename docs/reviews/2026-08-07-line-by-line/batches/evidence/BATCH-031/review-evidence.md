# BATCH-031 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-root`
- Scope: 20/20 blobs, 3.050/3.050 fysieke regels en 129/129 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen.
Dit validatorclasspad heeft geen interne productiecaller; bevindingen zijn bewezen
interface-/codedefecten met latente of dormante productimpact.

## Verificatie

- 92 gerichte primaire tests slaagden; onafhankelijke factory-, loader- en
  gedragsreproducties bevestigden alle bevindingen.
- Ruff en Black waren schoon voor alle scopebestanden.
- Geen netwerk, credentials of applicatiebestandswrites.

## Bevindingen

### B031-001 — P2 — 39 factories vallen terug op een omgekeerde generieke validator

39/40 toegewezen factories zoeken JSON naast `validators/`, waar die niet staat;
alleen CON_01 heeft fallback. De loader slikt `FileNotFoundError` en behandelt elk
gevonden overtredingspatroon vervolgens als pass. INT-08-negatie en STR-01-
werkwoordstart passeerden zo met score 1.0. Aanbevolen: reeds geladen config
injecteren, typed fail-loud en nooit generieke positieve polariteit aannemen.

### B031-002 — P3 — dubbele validatorbomen zijn al gedivergeerd

38/40 blobs zijn byte-identiek aan `regels/<id>.py`; CON_01 en SAM_07 verschillen.
De loader prefereert de ene boom en valt terug naar de andere. Aanbevolen: één
Pythonimplementatielaag en een tijdelijke inventory-/driftgate.

### B031-003 — P3 — CON-01 opent een DB-verbinding en slikt fouten

`CON_01.py:73-103` maakt een repository vóór is vastgesteld dat context bestaat,
sluit de onderliggende verbinding niet en slikt iedere repositoryfout. De suite
gaf drie unclosed-database-ResourceWarnings. Aanbevolen: vroeg retourneren,
beheerde dependency-injectie/lifecycle en een expliciet unavailable-beleid.

### B031-004 — P3 — INT-01 handhaaft één-zinsregel niet

`INT_01.py:66-120` controleert komma's/conjuncties maar geen zinsgrenzen.
`Proces stopt. Taak eindigt.` passeert met 0,9. Aanbevolen: robuuste
zinssegmentatie en tests voor afkortingspunten.

### B031-005 — P3 — INT-03 keurt heldere voornaamwoordverwijzing af

`INT_03.py:62-99` markeert elk pronomen als fout tenzij de volledige tekst exact
een goed voorbeeld bevat. Een directe antecedentzin met `gegevens die ...` faalt.
Aanbevolen: antecedent-/afstandanalyse en variatietests, geen voorbeeldwhitelist.

### B031-006 — P3 — ESS-03 substringclassificatie slaat samengestelde termen over

`ESS_03.py:77-103` ziet `proces` in `proces-verbaal` en classificeert het begrip
automatisch als niet-telbaar; een definitie zonder identificator passeert.
Aanbevolen: categorie/metadata primair en woord-/compound-aware fallback.

### B031-007 — P3 — ESS-04-percentagepatroon kan niet matchen

`ESS_04.py:90-99` gebruikt `\b\d+\s*%\b`; de grens na `%` bestaat niet aan
einde/spatie. `minimaal 80%` faalt dus als niet-toetsbaar. Aanbevolen: lookahead
`%(?=\W|$)` en midden-/eindezinvarianten.

### B031-008 — P3 — INT-07 koppelt uitleg niet aan de afkorting

De canonieke vorm `Dienst Justitiële Inrichtingen (DJI)` faalt, terwijl `DJI`
met een willekeurige `[[wikilink]]` passeert omdat de link globaal wordt gezocht.
Aanbevolen: expansie/link per afkortingsspan koppelen en beide volgordes testen.

## Niet getest

- Geen interne productiecaller van deze classloader gevonden.
- Geen echte DB-failure/concurrency, browser, a11y of externe diensten getest.
