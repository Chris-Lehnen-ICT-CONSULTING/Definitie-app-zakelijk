# DEF-835 INT-02 O2 — uitvoeringsverslag dienstregel "discretie zonder bedoeling" (besluit 12, optie A)

7 oktober 2026. Uitgevoerd door Claude in werkboom `.claude/worktrees/DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, basis HEAD `78d1e0b7a`. **Niet gecommit en niet gepusht.** Er zijn geen live calls gedaan en `.env` is niet gelezen. De prompt (`def835-int02-prompt/3`), de andere toetsregels en de O1-route zijn niet gewijzigd.

## Resultaat in één alinea

Contract `def835-int02-assessment/3` voegt één smalle, deterministische regel toe aan `beoordeel`. Een C107-vormige fail van het model wordt `review_required` / `insufficient_information`. Er geldt dan:
- de vaste vraag `Is de bedoeling dat deze passage een begripskenmerk beschrijft of de actor een afweging voorschrijft?`;
- de zichtbare omzetting `omzetting: "discretie_zonder_bedoeling"` in het document.

Het bewaarde oordeel blijft de modeluitvoer met verdict `fail`, met dezelfde citaten en posities als onder /2. Een actorvoorschrift in de kern, een andere grond of een bekende bedoeling houdt de fail in stand. Bewaarde /1- en /2-documenten worden volgens hun eigen versie gecontroleerd en zijn daarna historisch. De systeemprompt is ongewijzigd (`da4a4112…`, getest).

## De regel (zoals geïmplementeerd)

De regel geldt alleen als de uitvoer al volledig geldig is (structuur, citaten en samenhang zoals onder /2) en als alle vier deze voorwaarden gelden:
1. het verdict is `fail`;
2. de actor van de uitvoering is `ai`;
3. de bevestigde bedoeling is onbekend. Getoetst is "niet gevuld"; het invoercontract staat alleen `None` toe, dus "leeg" kan niet voorkomen;
4. alle passages die de fail dragen (`actor_prescription` of `discretionary_decision_rule`) zijn `discretionary_decision_rule` met `ground.field == "kern"`, met of zonder grondcitaat.

Passages met `criterion`, `derivation` of `unclear` dragen de fail niet en tellen niet mee.

Gevolg: status `review_required`, reden `insufficient_information`, vraag = de vaste vraag en `omzetting = "discretie_zonder_bedoeling"`. De melding is het O-sjabloon met de vaste reden `De bevestigde bedoeling is onbekend; alleen de kern zelf draagt de lezing van '{citaat}' als discretionaire beslisregel`, ingevuld met het citaat van de eerste dragende passage.

Niet omgezet:
- een `actor_prescription` in de kern (besluit 1);
- een discretionaire passage met als grond het begrip, de context of een bron;
- elke combinatie met zo'n passage;
- een bekende bedoeling;
- een menselijke beoordelaar;
- elk ander verdict;
- elke ongeldige uitvoer, die `error` blijft.

Er is geen pass-pad bijgekomen.

## Gemaakte keuzes

1. **Plaats van de regel: in het contract (`beoordeel`), niet apart in de dienst.** De dienst roept `beoordeel` al aan. Door de regel in het contract te leggen, valt hij vanzelf onder de replay- en integriteitscontrole (`_herleidbaar`). Een omgezet document is dus reproduceerbaar.

   Bij de hercontrole (`toets_actualiteit`) geldt het volgende:
   - een ontbrekende actuele kern of context gaat altijd voor: dan is de uitkomst `not_evaluated`;
   - een gewijzigde `omzetting`, documentvraag (`vraag`), status, reden of melding geeft `error`;
   - een consistent gewijzigde bewaarde modelvraag (`oordeel["question"]`) kan de hercontrole niet aantonen. Na een omzetting hangen vraag en melding daar niet van af. De hercontrole toetst samenhang, geen authenticiteit; dat is de taak van de opslaglaag (DEF-626). Deze grens is vastgelegd in `test_bewijsgrens_gewijzigde_bewaarde_modelvraag_is_niet_aantoonbaar`.

   De dienst zelf is alleen in de docstring bijgewerkt.
2. **Vraag: altijd de vaste vraag, ook als het model zelf een geldige vraag gaf.**
   - Bij een fail gaat een modelvraag volgens de T-tekst (SC-C-03) over *andere* open punten, niet over de ontbrekende bedoeling waar de omzetting om draait.
   - De code kan niet vaststellen of een modelvraag gericht is.
   - De vaste vraag maakt de uitkomst invoeronafhankelijk en run-stabiel.

   De modelvraag gaat niet verloren: zij blijft zichtbaar in `oordeel["question"]` (test (g)). Gedocumenteerd in `int02_assessment_contract_v3.md` §"Wijziging ten opzichte van /2".
3. **Zichtbaarheid: nieuw documentveld `omzetting`** (`None` of `"discretie_zonder_bedoeling"`). Het staat in `als_dict()` en reist zo via `rule_results['INT-02'].assessment` mee. Het publieke resultaatcontract 2.3.0 verandert niet: `assessment` was al een vrij documentobject, en de schema-integratietest is groen (22). Het oordeel houdt verdict `fail`. Daardoor is het verschil tussen wat het model zei en de uitkomst altijd zichtbaar.
4. **Alleen actor `ai`.** Besluit 12 spreekt van "als het model `fail` geeft". Een menselijk oordeel van dezelfde vorm blijft dus `fail` (test, en mutatie M1). Zie open punt 5.
5. **/2-migratiereferentie: het echte v5-document in plaats van een nieuwe git-generator.** Het in kwalificatieproef v5 door de echte /2-code bewaarde C107-document (`kwalificatieproef-v5/regressie-resultaat.json`) wordt rechtstreeks gelezen. Het is een /2-fail van precies de vorm die nu wordt omgezet. Onder /3 wordt het `review_required` / `historical`: niet omgezet en geen `error`. Hetzelfde geldt voor de ruwe modeltekst van test (a), letterlijk uit `regressie-bundel.json`; de SHA-256 ervan is gelijk aan `antwoord_sha256` in het resultaat. Ik heb de bestaande /1-generator (`scripts/analysis/def835_int02_v1_referentiedocumenten.py`) eerst uitgebreid naar /2. Uitvoeren vroeg goedkeuring die in deze sessie niet beschikbaar was. Daarom heb ik die wijziging volledig teruggezet (`git checkout`, bestand ongewijzigd) in plaats van een ongeteste generator achter te laten. Geen andere goldset- of hold-outinhoud gebruikt: alleen C107 uit v5.
6. **Bestaand evaluatorscenario `fail_discretie` aangepast.** Het had precies de nu omgezette vorm: discretie, grond kern, bedoeling onbekend. De grond is verlegd naar `organisatorische_context[0]`, zodat het scenario het VN-discretiepad blijft dekken. Een nieuwe evaluatortest dekt de omgezette vorm (zichtbaar in `assessment`). Mutatie M3 laat zien dat het aangepaste scenario de kerngrondcontrole mee bewaakt.

## Wijzigingen (bestand:regel)

| Bestand | Wijziging |
|---|---|
| `src/domain/int02/contract.py:1-42` | Moduledocstring /3 met de dienstregel; migratietekst /1 en /2. |
| `src/domain/int02/contract.py:72-86` | `CONTRACTVERSIE = "def835-int02-assessment/3"`, `_CONTRACTVERSIE_V2`, `_BEKENDE_CONTRACTVERSIES` = {/1, /2, /3}. |
| `src/domain/int02/contract.py:115-131` | `OMZETTING_DISCRETIE_ZONDER_BEDOELING`, `VRAAG_DISCRETIE_ZONDER_BEDOELING`, `REDEN_DISCRETIE_ZONDER_BEDOELING`. |
| `src/domain/int02/contract.py:757-800` | `_discretie_zonder_bedoeling` (de voorwaarden) en `_omzetting_discretie` (status, reden, O-melding, vaste vraag). |
| `src/domain/int02/contract.py:820-834, 853` | `Beoordelingsdocument.omzetting` (default `None`) plus docstring; `als_dict()["omzetting"]`. |
| `src/domain/int02/contract.py:914-931, 959-973` | `_beoordeel`: de omzetting na de statusbepaling, alleen onder `CONTRACTVERSIE` (/3). |
| `src/domain/int02/contract.py:1042` | `_herleidbaar`: posities weglaten voor /2 én /3 (`versie != _CONTRACTVERSIE_V1`); docstring. |
| `src/services/validation/int02_assessment_service.py:1, 10-13` | Alleen docstring (contract /3; de dienstregel ligt in WP1). Prompt ongewijzigd. |
| `src/services/validation/evaluators/decision_rule_assessment.py:6` | Docstring: contract /3. |
| `src/services/validation/interfaces.py:80-81, 288` | Commentaar: /3, historisch ook /1 en /2. |
| `src/toetsregels/runtime_contract.py:124` | Commentaar: contract /3. |
| `docs/architectuur/contracts/int02_assessment_contract_v3.md` (nieuw) | Contractdocument /3. `int02_assessment_contract_v2.md` en `_v1.md` zijn ongewijzigd. |
| `tests/unit/domain/test_def835_int02_dienstregel.py` (nieuw) | 53 tests: (a)–(i), actorkeuze, prompt-/hashbewaking, dienst end-to-end. |
| `tests/unit/domain/test_def835_int02_contract.py:1-7, 78, 389, 539, 1114-1124` | Docstring, contractdoc v3, versie-asserties /3; de contractdoc moet /1, /2, /3, `discretie_zonder_bedoeling` en de vaste vraag noemen. |
| `tests/unit/domain/test_def835_int02_citaatposities.py:132-136` | Versietest naar /3 (positieregel van /2 ongewijzigd). |
| `tests/unit/validation/test_def835_int02_evaluator.py:249-272, 609-632` | Scenario `fail_discretie` met contextgrond; nieuwe test dat de omzetting zichtbaar is in `assessment`. |
| `tests/unit/domain/test_def835_int02_migratie.py` (na review) | `_actueel_document` (/3); echte /2-tests op het v5-document van C107 (positie, citaat, zonder posities, onbekende of verschillende versie). |
| `tests/unit/validation/test_def835_int02_variatiemeting.py:247-251, 301` | Het script legt de actieve contractversie vast; nu /3. De live-meting liep onder /2 (`live-v1/herkomst.json`, ongewijzigd). |

`git diff --stat` (getrackte bestanden): 9 bestanden, 184 regels erbij en 44 eraf. Nieuw: contractdoc v3, testbestand dienstregel en deze map. Er zijn geen `print()`-aanroepen in `src/` toegevoegd. `git diff --check` is schoon.

## Testmatrix (opdracht stap 3)

| Opdracht | Test(s) in `test_def835_int02_dienstregel.py` |
|---|---|
| (a) C107-vorm uit v5 → review_required/insufficient_information, vaste vraag, zichtbare omzetting | `test_c107_v5_fail_wordt_review_required_met_vaste_vraag_en_omzetting` (ruwe v5-tekst; posities 13–85 zoals /2; oordeel blijft fail; actualiteit gelijk), `test_ruwe_v5_uitvoer_is_letterlijk_die_uit_de_proef`, `test_discretie_met_kerngrond_met_of_zonder_grondcitaat_wordt_omgezet` (3), `test_niet_dragende_passages_tellen_niet_mee`, `test_meerdere_discretionaire_kernpassages_noemen_de_eerste`, `test_vaste_vraag_is_precies_een_vraag_en_invoeronafhankelijk`, dienst end-to-end `test_dienst_zet_de_ruwe_v5_fail_om_en_laat_dat_zien` |
| (b) bedoeling bekend → fail | `test_c107_v5_met_bekende_bedoeling_blijft_fail` |
| (c) actor_prescription/kern, bedoeling null → fail (besluit 1) | `test_actorvoorschrift_met_kerngrond_zonder_bedoeling_blijft_fail` (2) |
| (d) discretie/kern + actor_prescription → fail | `test_discretie_naast_actorvoorschrift_blijft_fail` (2 volgordes) |
| (e) discretie met grond context/bron, bedoeling null → fail | `test_discretie_met_andere_grond_zonder_bedoeling_blijft_fail` (context, bron, met en zonder citaat, begrip), `test_discretie_naast_discretie_met_contextgrond_blijft_fail`, `test_bedoelingsgrond_bij_onbekende_bedoeling_blijft_een_fout` (ongewijzigd /2-gedrag) |
| (f) pass/insufficient/review ongewijzigd | `test_andere_verdicts_blijven_ongewijzigd` (pass, onvoldoende, NA), `test_ontbrekende_invoer_mislukte_en_niet_uitgevoerde_beoordeling_blijven`, `test_ongeldige_fail_uitvoer_blijft_error_en_wordt_niet_omgezet` |
| (g) model gaf zelf een vraag | `test_modelvraag_bij_fail_wordt_niet_overgenomen_maar_blijft_zichtbaar` |
| (h) hercontrole stabiel; manipulatie omzettingsveld → error | `test_hercontrole_van_een_omgezet_document_is_stabiel`, `test_gemanipuleerd_omgezet_document_is_error` (8: omzetting weg/anders/met spatie, terug naar fail met en zonder omzetting, vraag weg/anders, reden), `test_omgezet_document_met_andere_melding_is_error`, `test_omzetting_op_een_niet_omgezet_document_is_error` (fail, pass, onvoldoende), `test_omgezet_document_met_gewijzigd_oordeel_is_error` |
| (i) /2-document → historisch, niet error | `test_v2_proefdocument_is_een_fail_onder_contract_2`, `test_v2_proefdocument_wordt_historisch_en_niet_omgezet_of_error`, `test_zelfde_uitvoer_onder_contract_3_wordt_wel_omgezet`, `test_gemanipuleerd_v2_proefdocument_is_error` (4), `test_v2_proefdocument_als_v3_gelabeld_is_error`; de /1-migratietests (`test_def835_int02_migratie.py`, 36) blijven groen |
| Keuze actor | `test_menselijke_beoordelaar_wordt_niet_omgezet` |
| Prompt /3 ongewijzigd | `test_prompt_blijft_versie_drie_met_dezelfde_systeemprompt`: SHA-256 van de systeemprompt = `da4a4112b580da2924b5940ac2723ef5e177ad48ef15890b66d8d91f285a7ca6` (manifest v5) |

## Testuitkomsten

| Run | Uitkomst | Log |
|---|---|---|
| Baseline vóór wijzigingen: `-k "def835 or int02" tests/unit` | 887 geslaagd, 11 overgeslagen | niet gelogd |
| **Rood** (6 bestanden: nieuw dienstregelbestand en gewijzigde bestanden) | **52 gefaald, 354 geslaagd**. Gefaald: 45 dienstregeltests (onder meer `AttributeError … omzetting`, `fail` in plaats van `review_required`, `TypeError … omzetting`), 3 contracttests (versie /2, contractdoc v3 ontbreekt), 1 citaattest, 2 variatiemetingtests (versie) en de nieuwe evaluatortest. | `rood.log` |
| Rood: dienstregeltests die al slaagden (8) | Herkomst van de v5-tekst, de prompt-hashbewaking, en manipulaties die onder /2 al `error` gaven: vraag/reden anders, oordeel gewijzigd, /2-status/melding, /2 als /3 gelabeld. Na de implementatie bewaken ze dat het document bij manipulatie `error` blijft. | `rood.log` |
| **Groen 1**: dezelfde 6 bestanden | **406 geslaagd** | `groen.log` stap 1 |
| **Groen 2**: `pytest -o addopts="" --import-mode=importlib -q -k "def835 or int02" tests/unit` | **941 geslaagd, 11 overgeslagen**, 0 gefaald (was 887 + 11; +53 dienstregel, +1 evaluator) | `groen.log` stap 2 |
| **Groen 3**: gerichte selectie (prompt, dienst, evaluator, modelproef; `promptcorrectie-testbinding-v1.md`) | **460 geslaagd** (was 459; +1 evaluatortest) | `groen.log` stap 3 |
| Lint op de 10 gewijzigde/nieuwe `.py`-bestanden | `ruff check` (venv 0.15.17): `All checks passed!`; `black --check` (26.5.1): 10 ongewijzigd (na één herformattering van `contract.py` en het nieuwe testbestand) | `groen.log` stap 4 |
| Extra: `tests/integration/contracts/test_validation_result_schema.py -k int02` | 22 geslaagd (assessment met `omzetting` tegen het echte schema) | `groen.log` extra |
| Mutatiecontrole (telkens één naïeve variant in `contract.py`, daarna teruggezet; 3 testbestanden, 168 tests) | M1 actorcontrole weg: 1 gefaald · M2 `all` → `any`: 3 · M3 kerngrondcontrole weg: 8 · M4 versiecontrole weg (regel ook bij /2-replay): 1 · M5 geldige modelvraag overnemen: 1 · herstel: 168 geslaagd | `mutatie.log` |

## Open punten

1. ~~Onafhankelijke review~~ — gedaan: Codex, 07-10, "commit verantwoord: ja"; de twee punten zijn verwerkt (zie "Review (Codex, 07-10)").
2. **Hook-ruff 0.16.5 niet gedraaid.** `uvx ruff@0.16.5` vroeg goedkeuring. De venv-ruff 0.15.17 en black zijn schoon. De pre-commit-hook is strenger (RUF036, ISC004); bij de commit blijkt of er nog iets is.
3. **SHA-256 niet berekend** van de gewijzigde bestanden en van de logs: `shasum` en `openssl` vroegen goedkeuring. Ze volgen bij manifest v6. De herkomst van de v5-tekst is wel getoetst, via de bestaande `antwoord_sha256` in de test.
4. **Logs zijn git-ignored** (`.gitignore:46 *.log`). Bij de commit `git add -f` gebruiken, zoals bij `positiecorrectie-v1/`.
5. **Keuze actor `ai`** (alleen modeloordelen worden omgezet). Graag bevestigen of verwerpen.
6. **Keuze vaste vraag** (ook als het model zelf een vraag gaf). Graag bevestigen of verwerpen. De vaste reden in de melding is een eigen formulering, net als de andere uitvoeringsteksten die niet uit synthese §4 komen, en is dus ook ter beoordeling.
7. **Inhoudelijk risico: een terechte modelfail kan worden omgezet.** Dat gebeurt als de kern alleen een discretionaire beslisregel draagt en de bedoeling onbekend is, en is bewust zo volgens besluit 12. Voor regressie en ontwikkeling raakt dit geen enkel fail-label; voor de hold-out is het nog onbekend. Zie "Impact op goldset".
8. **Label in de ontwerpgevallen-fixture.** `tests/fixtures/def835_int02_ontwerpgevallen.json` draagt nog `"contract": "def835-int02-assessment/2"`. Dat heb ik bewust niet gewijzigd: het bestand staat in het manifest en geen test leest dat label. Alle ontwerpgevallen geven onder /3 dezelfde status (`test_ontwerpgeval_geeft_verwachte_status` is groen).
9. **Volledige `make test` niet gedraaid**, alleen de def835/int02-selectie, de gerichte selectie en de schema-integratie.
10. Niet door mij aangeraakt en niet meegenomen:
    - de bestaande ongetrackte mappen `.claude/` binnen de docs-map;
    - `bewijs/mergevoorbereiding-v1/gates/` en `samengevoegde-gates/`;
    - `.claude/hooks/check-silent-exceptions.py`.

## Review (Codex, 07-10)

Oordeel van Codex: **"commit verantwoord: ja"**, met twee kleine punten. Beide zijn verwerkt vóór de commit. Logs staan in `review-correctie.log`.

1. **De /2-tests gebruikten feitelijk /3-documenten.** `_v2_document` in `test_def835_int02_migratie.py` maakte via de actuele `beoordeel` een /3-document, dus de /2-positiemutatietests toetsten /3.
   - Omgedoopt naar `_actueel_document` en `test_gemanipuleerd_actueel_document_is_error`, met de assertie dat de versie de actuele is en niet /2.
   - Nieuw, op het echte /2-document uit v5 (C107, `regressie-resultaat.json`):
     - `test_v2_proefdocument_is_echt_v2_en_wordt_historisch`;
     - `test_v2_proefdocument_met_gemanipuleerde_positie_is_error`: start ±1, end ±1, grond-start +1, grond-end −1;
     - `test_v2_proefdocument_zonder_posities_is_error`;
     - `test_v2_proefdocument_met_gewijzigde_quote_is_error`: citaat, consistent ander citaat, grondcitaat, consistent ander grondcitaat.
   - `test_onbekende_contractversie_is_error` en `test_document_en_binding_met_verschillende_versie_is_error` lopen nu over een echt /1-, een echt /2- en een actueel /3-document.
   - Rood/groen:
     - de nieuwe tests toetsen gedrag dat al bestond en slaagden direct (stap A, 107 geslaagd);
     - dat ze echt onderscheid maken, blijkt uit een tijdelijke naïeve mutatie in `_herleidbaar` ("een /2-document is altijd herleidbaar", R1): 16 gefaald, waaronder alle 12 nieuwe /2-mutatietests (stap B);
     - na het terugzetten van R1 is alles groen (stappen C–E).
2. **Formulering "manipulatie altijd error" gepreciseerd** in `int02_assessment_contract_v3.md` en in dit verslag (keuze 1):
   - een ontbrekende actuele kern of context gaat voor (`not_evaluated`);
   - een gewijzigde `omzetting` of documentvraag geeft `error`;
   - een consistent gewijzigde bewaarde modelvraag kan de hercontrole niet aantonen, omdat zij samenhang toetst en geen authenticiteit (opslaglaag, DEF-626).

   Die grens is nu ook vastgelegd in een test: `test_bewijsgrens_gewijzigde_bewaarde_modelvraag_is_niet_aantoonbaar`. Een vormfout in de modelvraag geeft wel `error`.

| Run na de review | Uitkomst |
|---|---|
| A: reviewtests op de huidige code (migratie en dienstregel) | 107 geslaagd |
| B: rood, mutatie R1 | 16 gefaald, 91 geslaagd |
| C: groen, de 6 nieuwe en gewijzigde testbestanden | 424 geslaagd |
| D: groen, `-k "def835 or int02" tests/unit` | **959 geslaagd, 11 overgeslagen**, 0 gefaald (was 941; +17 migratie, +1 dienstregel) |
| E: `ruff check` (0.15.17) en `black --check` (26.5.1) op 11 `.py`-bestanden | `All checks passed!`; 11 ongewijzigd |

## Impact op goldset (regressie + ontwikkeling)

Bron: de Codex-review en de opdracht van Chris van 07-10-2026. Ik heb dit niet zelf nagekeken; volgens de opdrachtgrens heb ik geen goldsetinhoud gelezen buiten C107.

- **Regressie (C105, C107, C112):** alleen C107 heeft een lege bedoeling, en C107 heeft label `review_required`. C105 (`fail`) en C112 (`pass`) hebben een bedoeling, dus de regel raakt ze niet.
- **Ontwikkeling (24 gevallen):** alle gevallen hebben een bedoeling, dus de regel kan daar niet ingrijpen.
- **Conclusie:** in regressie en ontwikkeling wordt **geen enkel fail-label** door de dienstregel geraakt.
- **Hold-out (16 gevallen): niet bekeken.** Of daar een `fail`-label met lege bedoeling en alleen een discretionaire kernpassage staat, is onbekend. Dat blijft een open punt bij de interpretatie van fase 3.

## Gevolgen voor manifest v6

Manifest v6 is nodig, omdat de identiteit bestandshashes bevat die veranderen. Offline aan te maken na de commit.

**Verandert:**
- `identiteit.bestanden`:
  - `src/domain/int02/contract.py` (nu `c20543f0…`; inhoudelijke wijziging: de dienstregel);
  - `src/services/validation/int02_assessment_service.py` (nu `4d9d7200…`; alleen de docstring);
  - `src/toetsregels/runtime_contract.py` (nu `205c8bdb…`; alleen commentaar).
- Daardoor `identiteit_sha256`, plus `identiteit.proefmap` (`kwalificatieproef-v6`) en het tijdstempel `aangemaakt`.
- Het payloadbestand verandert alleen in de identiteitshash in de kop.

**Verandert niet:**
- `promptversie` (`def835-int02-prompt/3`);
- `systeemprompt_sha256` (`da4a4112…`, getest);
- per geval de invoer-, dataprompt-, payload- en labelhashes. De payload bestaat uit systeemprompt, dataprompt en modelparameters, die geen van alle wijzigen; de waarden zijn bij v6 opnieuw te verifiëren;
- `normhash`, `t_tekst_sha256`, `config/config.yaml`, `INT-02.json`;
- de ontwerpgevallen-fixture;
- `ess03_assessment_service.py`, `ai_service_v2.py`, `async_api.py`, de AI-clients, `model_router.py`;
- het runnerscript `scripts/analysis/def835_int02_modelproef.py`;
- gevallen, limieten, prijzen, criteria, fasen, protocol en SDK-versies.

De contractversie zelf staat niet als apart veld in de manifestidentiteit; zij wordt via de hash van `contract.py` gebonden. Of je `contractversie: def835-int02-assessment/3` expliciet in de identiteit wilt opnemen, is een keuze voor v6.

**Gevolg voor de uitslag.** De runner telt de hoofdstatus (`document.status`) tegen het label. Een C107-antwoord zoals in v5 telt onder /3 dus als juist (`review_required`). Het grootboek en het resultaat tonen dan via `document.omzetting` dat dit door de dienstregel komt.
