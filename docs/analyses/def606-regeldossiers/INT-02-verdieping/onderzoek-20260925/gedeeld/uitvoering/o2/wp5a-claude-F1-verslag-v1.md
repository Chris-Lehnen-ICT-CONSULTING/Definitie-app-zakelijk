# DEF-835 — WP5a correctie F1: verslag Claude Code CLI-uitvoerder (v1)

28 september 2026. Uitvoerder: Claude Code CLI, hervatte WP5a-sessie. Opdracht: `wp5a-opdracht-claude-F1-v1.md`; bevinding F1 uit `wp5a-codex-review-v1.md`, gereproduceerd met `/private/tmp/wp5a-codex-repro-20260928-v1.py` (alleen gelezen). Basis `979ca0585100d94b613829d924c6d8bba4f24f1b`. Ik heb geen agents, reviewers of extra CLI-sessies gestart en geen model- of providercalls gedaan. **Niets gestaged, gecommit of gepusht.** Aan F2 en F3 is niets gewijzigd, ook niet via een private-field-workaround.

## Uitkomst

F1 is gecorrigeerd. Onder O2 (`decision_rule_assessment`) slaat `ModularValidationService._evaluate_via_registry` de voorafgaande `missing_inputs`-onderschepping over. Daardoor doet uitsluitend de O2-evaluator de WP1-invoercontrole, op de oorspronkelijke recordkern (`record_text`) in plaats van `cleaned_text`. NE krijgt de O2-vorm en ongeldige aanwezige kern of bedoeling wordt `error`. Het O1-pad (DEF-771-NE via `int02_niet_uitgevoerd`) blijft ongewijzigd. De tien nieuwe F1-tests waren rood tegen WP5a-v1 en zijn nu groen, net als de 49 eerdere WP5a-tests. De F3-tekstguard blijft rood in de regressie; die is niet gedeselecteerd of hernoemd.

### De correctie (enige productiewijziging, +6 regels)

`src/services/validation/modular_validation_service.py`, in `_evaluate_via_registry`, direct na `ontbrekend = missing_inputs(record, beschikbaar)`:

```python
if record.evaluator is EvaluatorType.DECISION_RULE_ASSESSMENT:
    ontbrekend = ()
```

Met commentaar dat de O2-evaluator zelf de volledige WP1-invoercontrole doet. Dit is voldoende omdat het INT-02-record alleen `definition_text` (altijd beschikbaar) en `context_lists` vereist. De O2-evaluator (`decision_rule_assessment.py:110-133`) bouwt de invoer met `maak_invoer` uit `record_text`. Is de invoer ongeldig, dan geeft hij `error`. Zonder configuratie geeft hij NE of 'nog te beoordelen' op basis van `ontbrekende_invoer`. De wrapper doet in al deze gevallen al geen aanroep.

## Verplichte regressies: RED → GREEN

| Scenario (review F1) | Test | RED tegen v1 | GREEN |
| --- | --- | --- | --- |
| Gevulde kern, geen context, cleaning maakt `""` | `test_f1_ne_volgt_…[kern-cleaning-leeg]` (modular) en `test_f1_zonder_context_…[kern-cleaning-leeg]` (wrapper) | melding ongelijk (v1: "kern en context") | NE, "context ontbreekt", O2-vorm, 0 calls |
| Lege kern, geen context, cleaning vult | `…[leeg-cleaning-kern]` (beide) | melding ongelijk (v1: "context") | NE, "kern en context", O2-vorm, 0 calls |
| None-kern zonder context | `test_f1_ongeldige_metadata_…[recordkern-none]` (modular) en `test_f1_zonder_context_…[recordkern-none]` (wrapper, recordroute) | `'not_evaluated' == 'error'` | `error`, `MELDING_E`, O2-vorm, 0 calls |
| Ongeldige bedoeling (42) zonder context | `…[bedoeling-getal]` (beide) | `'not_evaluated' == 'error'` | `error`, `MELDING_E`, O2-vorm, 0 calls |
| Juiste NE-vorm (contractversie, review, assessment, onderdeel) | `test_f1_ne_volgt_…[zonder-cleaning]` en `_assert_o2_vorm` in elke F1-test | `'def771-int02/2' == 'def835-int02-assessment/1'` | `contract_version` `def835-int02-assessment/1`, `review` `{"actuality": None}`, `assessment` `None`, één onderdeel `beoordeling` |
| Guard: lege kern mét context | `test_f1_ne_volgt_…[lege-kern-met-context]` | al groen (liep in v1 al via de evaluator) | groen |

In elke F1-test worden eerst de status en de exacte melding gecontroleerd, daarna de documentvorm. Zo laat de RED de meldingsfout bij cleaning apart zien, los van de vormfout.

Bewijs (dossier `bewijs/`):

| Log | Wat | Uitkomst | SHA-256 |
| --- | --- | --- | --- |
| `wp5a-F1-rood-v1.log` | Eerste RED; de contractversie-assertie maskeerde de meldingsfout | 9 failed, 1 passed, exit 1. Blijft staan; vervangen door v2 | `90da438eaf5b3bd2672018789db7c120a39d9c971ecb76508cb941c0a3595be9` |
| `wp5a-F1-rood-v2.log` | RED met status en melding vóór de vorm; productie = v1 (`737b8632…9829`) | **9 failed, 1 passed, exit 1** | `e505e0ad6777090eb3a6979fcf049bd3d857c8256725090222540e3bd2579dcd` |
| `wp5a-F1-groen-nieuwe-tests-v1.log` | Drie WP5a-testbestanden: 49 v1-tests plus 10 F1-tests | **59 passed, exit 0** | `0b41e9e589dbf7a36c24006c5de6202008e5bd007f49c32d8d7a8373da7b527f` |
| `wp5a-F1-regressie-v1.log` | Dezelfde gerichte set als `wp5a-groen-v1.log` (orchestrators, `tests/unit/validation` incl. DEF-771-O1-tests, containers, modular, INT-01/03/ESS-03, DEF-771-view); F3 niet gedeselecteerd | **2.908 passed, 11 skipped, 1 failed (F3)**, exit 1 (v1: 2.898 + 1 failed) | `3578d92d9f1aaece74e0ca555c48e1661dd6b07f1a4c170b4c1bcc585d7c2e45` |
| `wp5a-F1-lint-v1.log` | black 26.5.1, ruff 0.15.17, ruff 0.16.5 (pre-commit-rev) op de drie gewijzigde bestanden | alle exit 0 | `db2b7a2295e1a31fb9e8bb9d1ed9013211bdd16bb84cea47af3ff617e5ee6660` |
| `wp5a-F1-correctiediff-v1.patch` | Delta t.o.v. WP5a-v1 (reviewmanifest-v1) voor de drie gewijzigde bestanden | productie +6; modular-tests +101/−2; wrappertests +76 | `29517a408175bf71a0e4c72166e4f6adac7b6948fca03cbf86dda2123027b2a4` |
| `wp5a-F1-werkboomdiff-v1.patch` | Volledige zevenbestandenpatch t.o.v. HEAD na F1 (1.702 regels) | — | `a577e702f9b488e55516456e414810fcb504120840c86a68c550ce7df250d6d1` |

De volledige commando's en exits staan in de kop en de laatste regel van elke log. De volledige unit-suite en mypy zijn volgens de opdracht niet opnieuw gedraaid.

### Eerlijke kanttekeningen

- **Testwijziging na RED-v2.** Na RED-v2 is alleen het commentaar in de bestaande test `test_ontbrekende_kern_of_context_is_ne_zonder_oordeel` aangepast (2 regels, geen assertie). Dat commentaar zei dat ontbrekende context via het DEF-771-pad loopt. Bewijs: met het oude commentaar teruggezet geeft het huidige bestand exact de in RED-v2 vastgelegde hash `e410a27b…f065`. De wrappertests zijn byte-identiek aan de RED-v2-stand (`ed66ecef…4459`). De lint-log is gecontroleerd tegen de eindhashes (`shasum -c` OK).
- **De `−2` in de modular-testdiff** zijn precies die twee commentaarregels. Er zijn geen testgevallen verwijderd.
- **`signals` bij `error` en NE.** De O2-evaluator vult bij `error` en NE nog wel `rule_result.signals` met treffers van recordpatronen. Voorbeeld: met bedoeling 42 en de kern "De medewerker moet de aanvrager toelaten." verschijnt `['\\bmoet\\b']`. Dat is WP3-ontwerp: een leeshulp uit het regelrecord, geen modeluitvoer, geen oordeel, geen violation en geen reviewitem (de F1-tests controleren dat laatste op modular-niveau). Het evaluatorbestand valt buiten het mandaat, dus ik heb dit niet gewijzigd. Moet "geen modelsignaal" ook deze patroonsignalen uitsluiten, dan is dat een aparte wijziging in `decision_rule_assessment.py`.
- **Buiten de repository** staan de hulpartefacten `/tmp/wp5a-F1-basis/` (kopie van de drie v1-bestanden als diffbasis) en `/tmp/wp5a_F1_signalen.py`. Ik heb niets verwijderd.

## Actuele identiteit (zeven bestanden, ongestaged)

| Bestand | SHA-256 | T.o.v. manifest-v1 |
| --- | --- | --- |
| `src/services/container.py` | `32a5ae789a0f131a036e4f1aa66d98cd05e4ea99ca1e77545529592de781e42a` | ongewijzigd |
| `src/services/orchestrators/definition_orchestrator_v2.py` | `db1093e54c6c917fb6b37f49b153cdd1f2465274da94fb1bb74bfe1ef724d4ca` | ongewijzigd |
| `src/services/orchestrators/validation_orchestrator_v2.py` | `7faf7380ca1d4a332d0110ddfac53ced9c094223ef533199a87c6229f125f419` | ongewijzigd |
| `src/services/validation/modular_validation_service.py` | `84a9e330c263afeea519363e1ac692950c93df3c1c15a2634fef5d5d722ab6c2` | F1 (+6) |
| `tests/unit/services/orchestrators/test_def835_int02_wrappers.py` | `ed66ecef4e5867568b879a1a9607d80772b04ea18660222eeaff295a6d484459` | F1 (+76) |
| `tests/unit/validation/test_def835_int02_modular.py` | `ca09aa5220b4e25cc55f8d90831abfc03a69034328b259b11d1227afcb799400` | F1 (+101/−2) |
| `tests/unit/services/test_def835_int02_container.py` | `5048a1c4bf68fe58d8315a85129269e3eff27737e0b833b6bef177e2c3f69ae9` | ongewijzigd |

Git-staat: de index is exact intact, met dezelfde 38 bestanden (namenlijst identiek). De hash van `git diff --cached` is nog steeds `941070627b508626b13b3c4d13b00bf5000966a8f728d0425802ed7b9fd5d214`. Buiten deze drie bestanden en de nieuwe `bewijs/wp5a-F1-*`-bestanden plus dit verslag is niets gewijzigd. De coördinatorbestanden `wp5a-F1-claude-stream-v1.jsonl` en `wp5a-F1-claude-stderr-v1.log` zijn niet aangeraakt.

## Open punten

1. **F2 (configuratiebinding) blijft open** en wacht op het akkoord over de dienst-API. Ik heb niets gewijzigd.
2. **F3 (WP2-tekstguard, `test_def835_int02_assessment_service.py:305-308`) blijft open.** Hij faalt zichtbaar in `wp5a-F1-regressie-v1.log`.
3. **Patroonsignalen bij `error`/NE**: zie de kanttekening hierboven. Het is een besluit of die ook onder "geen modelsignaal" vallen.
4. Hierna stop ik, zodat dezelfde reviewer de delta (`wp5a-F1-correctiediff-v1.patch`) kan controleren.

## Bronnen

- `wp5a-codex-review-v1.md` (F1, regels 11-24)
- `/private/tmp/wp5a-codex-repro-20260928-v1.py`
- `src/services/validation/modular_validation_service.py` (`_evaluate_via_registry`, rond regel 1481-1500)
- `src/services/validation/evaluators/decision_rule_assessment.py:107-148`
- `src/toetsregels/regels/INT-02.json` (`required_inputs`: `definition_text`, `context_lists`)
- `src/domain/int02/contract.py` (`MELDING_NE`, `MELDING_E`, `ontbrekende_invoer`)
