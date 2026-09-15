# DEF-622 — implementatie en bewijs

Status: reviewbare draft; implementatie niet volledig afgerond wegens de expliciete open punten hieronder. Geen merge, deploy of volledige productvrijgave. Basis `d68a98a90`, branch `feature/DEF-622-contextcontract`. Claude CLI implementeert; afzonderlijke Codex CLI-sessies reviewen; desktopcoördinator voert eigen proeven uit.

## Gedrag en bewijsgrenzen

| Onderdeel | Geïmplementeerd gedrag | Bewijs / status |
|---|---|---|
| Contexttransport | Drie canonieke recordlijsten en metadata bereiken V2; recordwaarden prevaleren, inclusief leeg/None. | Eigen16 transporttests; transportreview gesloten. |
| CON-01 | Aanwezigheid en dynamische geselecteerde naamfunctie; noodzakelijk/pass, registratie/fail, onduidelijk/open; technische fouten en alle delen zichtbaar. Geen cijfer. | Eigen480 contracttests; gerichte regressies52+66; contractreview gesloten. |
| Totaalscore | Tijdelijk None/niet beschikbaar, op expliciet besluit van Chris; geen nieuwe formule en geen impliciete CON-01 0/1. | Adapters/opslag/UI getest. Algemene scoreafhankelijke gate blijft fail-closed; zie afhankelijkheden. |
| Gelijke context | Volledige genormaliseerde lijsten, geen aliasmapping; schrijfwijze behouden. Bestaande categorie-/synoniemsemantiek bij lookup. | Eigen44 lookup/checker/keuzes/AppTest-regressies; duplicaatreview gesloten. |
| Drie gebruikerskeuzes | Gebruik Deze, Bewerk, Genereer Nieuw hebben echte consumenten. Nieuwe generatie eist reden, maakt draft en verandert bestaand vastgesteld record niet; forcekeuze eenmalig. | Echte Streamlit AppTest met productiecontainer/adapters/repository en bevroren externe AI/tokenizer; synthetische DB. |
| Vaststelconflict | Maximaal één vastgesteld record voor hetzelfde begrip + volledige context, ongeacht categorie. Bewuste vervanging archiveert en stelt atomair vast; audit/rollback/concurrency. | Eigen57→84→85→107 gerichte proeven; V1/V3/V4/V2a/V2c gesloten. V2b blijft open. |
| Versie-/actorbinding | Geen generieke verlenging bij metadata-/tekstwijziging; actor bij opslaan gelijk aan echte opslaander, latere vaststeller mag anders zijn. | Bool/floatinvoer geblokkeerd; twee V2b-restpunten hieronder. |
| Export/readback/editor/expert | Gedeelde recordcontext en definitiezin, versietransport, echte actor vereist; prompts met noodzakelijke-naamuitzondering. | Eigen 39 tests op f91d12d57; alle K1..K6 en cleaning-binding door onafhankelijke reviewer gesloten. |
| UI-uitkomsten/expertactie | Pass/fail/open, fail+open, technische fout, gemotiveerde expertactie en expliciete vaststelling. | Eigen 13 echte AppTests op a21d4e459 groen; productiecontainers/adapters/repository, synthetische DB en gecontroleerde externe grenzen. |
| Skills | Smalle normcorrectie als bronpatch met hashes. | Bronpatch6ee7c4c25 gecontroleerd: dry-run en toepassen op kopieën exit0, alle3 bron/resultaathashes exact. Globale toepassing/sync valt buiten deze levering. |

De snapshots komen uit exacte gitcommits. Bronbinding, JUnit en logs staan lokaal onder `reports/def622/coordinator-*`. Reviewdossiers in deze map leggen commits, bevindingen en dispositie vast. Positieve gerichte tests vervangen geen volledige gates of onafhankelijke review.

## Open blokkerende punten

**V2b, na drie gerichte herstelpogingen gestopt conform AGENTS.md:**

- Ontbrekende/null payloadversie kan worden gestempeld wanneer expected_version klopt; dit voldoet niet aan de opgedragen strikte payloadversie-eis.
- Marker-versie als tekst ("2") passeert de gate maar wordt niet behouden bij vaststelling: na versie3 is de review ongeldig. Gate en carry hanteren een andere typeconventie.

Zie `DEF-622-vaststel-review-v4.md`. Geen waiver; niet presenteren als afgeronde versiegebonden keten.

**Productafhankelijkheden:** DEF-630 blijft eigenaar van algemene approval-/exportgate, snapshots, identiteit en overige verplichte voorwaarden (met de bestaande onderliggende issues). Met de huidige echte regelset is de totaalscore niet beschikbaar en blijft de algemene acceptatie fail-closed. Positieve lokale vaststel-/exportproeven zetten uitsluitend overige gatevoorwaarden expliciet synthetisch positief; zij bewijzen niet de volledige productgate. DEF-624 draagt de appbrede score-uitwerking, DEF-464 latere consolidatie, DEF-742 de afzonderlijke algemene passendheidstoets.

## Projectgates

Stabiele codebron `0bb7ca0bd`; docscommit `6ee7c4c25` verandert geen code/tests/config. Finale kwaliteitsgates exit0: markers386, lint, mypy0, complexiteit197≤201, overrides2, pins consistent, weesmodules0, silent-except56≤57. Ook onafhankelijk uitgevoerd met de exacte vastgepinde Ruff0.16.5/mypy2.3.1/Black26.5.1; pakketinstallatie uitsluitend in tijdelijke venv met lockfile-hashes, gedeelde projectvenv ongewijzigd. Logs `coordinator-quality-final.log`, `coordinator-pinned-quality-final.log`. Geen grenzen verhoogd.

Finale canonieke gates op de echte werkboom, met offline-bootstrap en synthetische tijdelijke opslag:

| Gate | Uitkomst | Bewijs |
|---|---|---|
| Unit + coverage45% | Exit 0; 5082 passed, 21 subtests passed, 75 skipped, 1 xfailed, 0 failures/errors. Coverage 57,26% (21033/36735 statements) ≥45%. | `coordinator-unit-coverage-final.log`, `final-gates/unit-cov-junit.xml`, `final-gates/unit-coverage.xml` |
| Integration | Exit 0; 571 passed, 28 skipped, 15 xfailed, 2 non-strict xpassed, 0 failures/errors. | `coordinator-integration-final.log`, `final-gates/integration-junit.xml` |
| Acceptance / smoke | Exit 0; 21 passed, 5 bestaande collectie-skips, 0 failures/errors. | `coordinator-acceptance-contract-final.log`, `final-gates/acceptance-smoke-junit.xml` |
| Contract | Exit 0; 36 passed, 6 bestaande skips, 0 failures/errors. | `coordinator-acceptance-contract-final.log`, `final-gates/contract-junit.xml` |

De identieke volledige unitselectie van `make test` is gecombineerd met de strengere coveragegate; aparte markercontrole slaagt. Geen selectie, budget of vloer verkleind. Integration, acceptance en contract lopen serieel via dezelfde bewaakte runner. De gerapporteerde skips/xfails zijn bestaande disposities; nieuwe DEF-622-proeven zijn niet overgeslagen.

De laatste onafhankelijke review op f91d12d57..6ee7c4c25 vindt geen nieuwe bevestigde bevindingen:1212 synthetische vergelijkingen en afzonderlijke beoordeling van echte AppTests, contracttestupdates en bronpatch. Zie `DEF-622-eindpakket-review-v1.md`. V2b blijft expliciet open.

Preflight op bronarchief dc1 gaf drie unieke oude-scorecontracttests; bijgewerkt in13f441919 met behoud van onderscheidend gedrag. De Git-rootguard kon terecht niet op een Git-archief draaien; finale run gebruikt echte werkboom. Een timingproef miste onder gelijktijdige runs zijn5s-start; afzonderlijke herhaling exit0. Geen testbudget gewijzigd.

## Aanvullende bewijsgrenzen

Het expert-AppTest-record gebruikt overige gatevoorwaarden synthetisch positief. De bestaande vaststellerfallback `expert` blijft ongewijzigd; dit is geen bewijs van een complete echte gebruikersidentiteit bij vaststelling. De proef telt de reguliere app-statusaudit met reden; de bestaande schematrigger schrijft daarnaast een afzonderlijke rij zonder reden.

De algemene quick_validate-skillvalidator weigert de bestaande extra frontmattervelden evalScore/lastReviewed/status/triggerExamples, zowel op originele bronnen als op de gepatchte kopieën. De patch verandert geen frontmatter. Patchtoepasbaarheid en bron/resultaathashes zijn wel bewezen; geen claim van geslaagde algemene structuurvalidatie of actieve globale installatie.

## Reproduceerbare finale verificatie

Uitgevoerd op de echte werkboom, codecommit `0bb7ca0bd`, met `PY=/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python` en `GATE_REPORTS=reports/def622/final-gates`:

```text
make test-markers-check lint complexity-check mypy-check overrides-check pins-check orphan-check silent-except-check
make test-cov-ci
make test-integration
make test-acceptance test-contract
```

Alle bovenstaande gate-aanroepen eindigden met exit 0. De kwaliteitsgates zijn daarnaast herhaald met de exacte lockfile-toolversies in een tijdelijke omgeving; alle eveneens exit 0. De finale code/tests/config verschillen niet van de geteste codecommit. Geen dependencies of databaseschema gewijzigd, geen nieuwe productie-printstatements, `git diff --check` schoon voor src/tests/config. Het opgenomen unified-diff-patchbestand gebruikt vanzelfsprekend contextspaties op lege regels; die zijn nodig voor het patchformaat.

## CI-aanvulling na de eerste push

Twee CI-controles vroegen onderhoud van bestaande baselineverwijzingen. In `bc3608e48` zijn zes grep-regelnummers en twee timingmodulehashes plus de broncommit bijgewerkt. Alle uitzonderingen, beoordelingen, timingasserties en toleranties zijn behouden. Beide echte guards slagen nu lokaal en de onafhankelijke deltareview is gesloten zonder nieuwe bevindingen. Zie `DEF-622-ci-aansluiting-v1.md`. Productiecode en tests zijn ongewijzigd; de bovenstaande functionele verificatie blijft geldig.
