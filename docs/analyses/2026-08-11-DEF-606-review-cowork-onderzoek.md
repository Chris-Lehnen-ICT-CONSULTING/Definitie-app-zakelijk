# DEF-606 — Review van het Cowork-onderzoek

**Datum:** 11 augustus 2026  
**Beoordeeld document:** `2026-08-11-DEF-606-inhoudelijk-antwoord.md`  
**Repo-HEAD van onderzoek en hercontrole:** `5cf2cd80`

## Samenvatting

De hoofdconclusie van Cowork is onderbouwd: de oude Pythonvalidatorlagen zijn
historische voorgangers/restanten en geen onafgemaakte opvolger van
`_evaluate_json_rule`. Git bevestigt de migratierichting; ASTRA en de JSON-records
bevestigen welke regelbetekenis bewaard moet blijven.

Cowork brengt daarnaast terecht een grotere contractkloof aan het licht: de
aanwezigheid van een runtimebranch bewijst nog niet dat de evaluator het eigen
gedocumenteerde goede en foute voorbeeld onderscheidt. De 44 JSON-records met
beide soorten voorbeelden moeten daarom rechtstreeks onderdeel van de
gedragssuite worden.

Eén formulering uit Cowork is te absoluut. Dat 15 gedocumenteerde foute
voorbeelden score 1,0 krijgen, bewijst dat die voorbeeldcases niet worden
herkend. Het bewijst niet dat alle 15 regels onder iedere invoer nooit kunnen
falen. De actuele runtime-matrix bereikt voor meerdere van deze regel-ID's met
andere negatieve fixtures wel een violation. De juiste conclusie is daarom:
**example-/semantische drift**, niet zonder meer **universele inertie**.

## Bronneninventaris

| Bron | Gebruik |
| --- | --- |
| `docs/analyses/2026-08-11-DEF-606-git-archeologie.md` | migratietijdlijn en bestandsherkomst |
| `docs/analyses/2026-08-11-DEF-606-inhoudelijk-antwoord.md` | Cowork-normvergelijking en duelmeting |
| gitcommits `c6bbaf20`, `d7df1c43`, `4bcfba68`, `3ea307e0`, `a5794ccb` | onafhankelijke controle van tijdlijn |
| `src/services/service_factory.py` en `src/toetsregels/manager.py` | actief productiepad |
| `src/services/validation/modular_validation_service.py` | evaluatorwerking en default-passrisico |
| `tests/fixtures/toetsregels/runtime_cases.yaml` | huidige classificatie en gerichte cases |
| `tests/unit/validation/test_rule_runtime_matrix.py` | bereikbaarheid en afgeleide telling |
| `src/toetsregels/regels/*.json` | 53 records; 44 met goed én fout voorbeeld; 35 met `brondocument: ASTRA` |
| ASTRA Standaard en Regels voor definitiekwaliteit | externe norm, beheer en regelteksten |
| Linear DEF-503, DEF-605, DEF-606 en DEF-621 | eerder vastgelegde meet- en defectcontext |

## Bevestigde bevindingen

### 1. De oude Pythonlaag is restant

De gitgeschiedenis toont de Pythonloader op 17 juli 2025 als actief pad en de
V2-JSON-evaluator vanaf 17 september 2025. Commit `a5794ccb` verwijderde op
14 april 2026 de enige productieconsument van het oude pad. In de huidige bron
heeft `JSONValidatorLoader` geen productie-import; `manager.py` laadt uitsluitend
`*.json`.

### 2. JSON bewaart de bedoelde regelidentiteit beter dan de Pythonlaag

De actuele ASTRA-regelpagina noemt onder andere CON-01, ESS-01–05, INT-01–04,
INT-06–10 en SAM-01–04 met dezelfde regelidentiteit als de JSON-records. De
betwiste Pythonmodules dragen aantoonbaar andere uit `legacy core.py` gemigreerde
onderwerpen. Daarmee is aansluiten van die modules geen herstel van de ASTRA-set.

### 3. De duelmeting legt echte drift bloot

Een lokale telling op HEAD bevestigt 53 JSON-records, waarvan 44 een niet-lege
lijst `goede_voorbeelden` én `foute_voorbeelden` hebben. Cowork rapporteert voor
de live evaluator 24 onderscheidende, 19 gelijke en 1 omgekeerd scorend paar.
Die n=1-meting is voldoende om een gemist tegenvoorbeeld te bewijzen, maar niet
om volledige correctheid van een onderscheidende regel te bewijzen.

### 4. De huidige matrix en Cowork meten verschillende dingen

De runtimefixture classificeert op dezelfde HEAD 50 regels als automatisch en
bevat per automatische regel een gerichte negatieve case die de test werkelijk
laat falen. De bijbehorende test draait groen. Cowork gebruikt daarentegen het
eerste voorbeeldpaar uit ieder JSON-record. Beide resultaten kunnen tegelijk
waar zijn: een branch is bereikbaar, terwijl het normatieve voorbeeld niet door
dezelfde heuristiek wordt herkend.

### 5. Classificatie en scorepolicy ontbreken in het echte contract

De huidige classificatie staat in een testfixture en nog niet als gevalideerd
RuleRecord-contract. Voor repository- en oordeelregels is een binaire pass bij
ontbrekende invoer misleidend. Het resultaatmodel moet minimaal onderscheid
maken tussen `pass`, `fail`, `review_required`, `not_evaluated` en `error`.
Niet-uitgevoerde regels mogen niet als 1,0 bijdragen; score en evaluatiedekking
moeten afzonderlijk zichtbaar zijn.

### 6. Bron- en projectafwijkingen moeten expliciet worden

ASTRA bevestigt de oorsprong en het beheer van de standaard. Cowork rapporteert
prioriteits-, status- en provenanceverschillen die één voor één moeten worden
geverifieerd. Projectkeuzes horen als override zichtbaar te zijn. Dat geldt in
het bijzonder voor CON-01: de lokale productnorm bewaart context als verplicht
gestructureerd gegeven en houdt context buiten de definitietekst.

## Besluit voor de uitvoering

1. Handhaaf ADR-001: de oude Pythonlagen worden niet aangesloten.
2. Voeg de 44 JSON-voorbeeldparen toe aan de uitvoerbare contracttests, naast de
   gerichte runtimefixtures.
3. Classificeer alle 53 regels als deterministisch, repositoryafhankelijk,
   oordeelafhankelijk of expliciet niet automatisch beoordeeld.
4. Leg uitkomst- en scorebeleid in het rootcontract vast; geen default-pass voor
   niet-uitgevoerde regels.
5. Werk de ontbrekende repositoryregels `SAM-01`, `SAM-08` en `DUP-01` mee uit;
   DEF-623 blijft eigenaar van SAM-02–06.
6. Beslis expliciet per oordeelregel tussen een gecontroleerde AI-jury en
   verplichte menselijke review; voer geen LLM-jury impliciet in.
7. Leg ASTRA-provenance, bronstatus en bewuste lokale afwijkingen vast en maak
   drift offline/reproduceerbaar zichtbaar.

## Beperkingen

- De Cowork-duelmeting is niet opnieuw als zelfstandig script aangetroffen; de
  gerapporteerde uitkomst is beoordeeld tegen dezelfde HEAD en de aanwezige
  JSON/testdata. De bestaande runtime-matrixtest is wel opnieuw groen gedraaid.
- De publieke ASTRA-overzichtspagina toont in de opgehaalde representatie niet
  alle rijen tegelijk. De standaardmetadata en zichtbare regelteksten zijn
  geverifieerd; Coworks volledige telling en alle tien prioriteitsverschillen
  blijven invoer voor een afzonderlijke, reproduceerbare driftcontrole.
- Eén voorbeeldpaar per regel is een regressiesignaal, geen volwaardige
  semantische goldset.

## Vervolgissues

- DEF-622 — CON-01-contextcontract end-to-end.
- DEF-623 — VER-01–03 en SAM-02–06.
- DEF-624 — classificatie van 53 regels en niet-misleidende scorepolicy.
- DEF-625 — ASTRA-herkomst, lokale afwijkingen en driftcontrole.

## Bronnen

- `docs/analyses/2026-08-11-DEF-606-git-archeologie.md`
- `docs/analyses/2026-08-11-DEF-606-inhoudelijk-antwoord.md`
- `src/services/service_factory.py`
- `src/toetsregels/manager.py`
- `src/services/validation/modular_validation_service.py`
- `tests/fixtures/toetsregels/runtime_cases.yaml`
- `tests/unit/validation/test_rule_runtime_matrix.py`
- https://www.astraonline.nl/index.php/Standaard_Definitiekwaliteit
- https://www.astraonline.nl/index.php/Regels_voor_definitiekwaliteit
- Linear DEF-503, DEF-605, DEF-606 en DEF-621
