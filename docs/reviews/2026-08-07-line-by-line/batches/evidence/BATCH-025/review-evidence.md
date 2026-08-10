# BATCH-025 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 20/20 blobs, 1.781/1.781 fysieke regels en 61/61 Python-symbolen

Alle JSON- en Pythonblobs zijn line-by-line gelezen; alle 61 symbolen zijn
beoordeeld. 43 tests slaagden primair, 5 consolidationtests waren expliciet
skipped en 19 CON/ARAI-tests slaagden onafhankelijk.

## Bevindingen

### B025-001 — P1 — CON-01 negeert vrije gebruikerscontext

`src/toetsregels/regels/CON-01.json:3-31` verbiedt opgegeven context in de
definitie, maar de actieve generieke evaluator controleert alleen vaste regexen.
Vrije context `ZorgbrigadeUniek` in context én tekst gaf score 1 en geen violation.
Aanbevolen: alle genormaliseerde contextwaarden met veilige boundaries toetsen.

### B025-002 — P1 — CON-02 accepteert expliciet ontkende bron

`src/toetsregels/regels/CON-02.json:2-19,41-52` en de actieve helper zoeken losse
positieve woorden zonder negatieanalyse. `er is geen wet of officiële bron`
gaf helper True, score 1 en geen violation. Aanbevolen: positieve bronrelatie en
concrete bron vereisen; negatie in hetzelfde zinsdeel detecteren.

### B025-003 — P3 — ARAI-06 controleert begripherhaling niet volledig

`ARAI-06.json:3-9` belooft geen herhaling; `ARAI-06.py:42-99` controleert alleen
startpatronen. Een begrip middenin passeerde standalone. De actieve totale flow
vangt dit via `CON-CIRC-001`, dus gebruikersimpact is end-to-end gemitigeerd.
Aanbevolen: contract vernauwen of volledige check implementeren en dedupliceren.

### B025-004 — P3 — capture groups maken foutfeedback leeg

`ARAI-02SUB2.json:13` plus `ARAI-02SUB2.py:52-55,74-77` gebruikt `findall` met
capture group. `ding` gaf `gevonden ()`, `dingen` gaf `gevonden (en)`; CON-01
heeft hetzelfde patroon. De actieve generieke evaluator is niet geraakt.
Aanbevolen: non-capturing groups of `finditer().group(0)`.

### B025-005 — P3 — negen dode ARAI-factories missen hun JSON

De negen `src/toetsregels/regels/ARAI-*.py`-factories bouwen ongehyphenated
paden zoals `ARAI01.json`; alle `create_validator()`-repro's gaven
`FileNotFoundError`. Productie gebruikt de generieke JSON-evaluator en omzeilt
deze factories. Aanbevolen: naastliggend hyphenated pad/injected config of de
dode duplicaatlaag na afzonderlijke toestemming saneren.

## Niet getest

- Geen externe bron, netwerk, credentials of UI/browserflow.
- Vijf consolidationtests waren bewust nog niet actief.
