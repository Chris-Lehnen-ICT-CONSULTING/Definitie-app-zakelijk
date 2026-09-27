# DEF-835 WP3-R1 — correctieverslag Claude Code CLI v1

28 september 2026. Dezelfde Claude Code CLI-uitvoerder (sessie c75abf0d-3c01-4c02-a672-536d75daa15a, claude-opus-5-5). Er zijn geen agents, reviewers of extra CLI-sessies gestart.

- Bron: `wp3-codex-review-v1.md`, bevinding WP3-R1 (Important/P2), bevestigd door de coördinator.
- Werkboom en branch: `feature/DEF-835-int02-o2`, HEAD `d3fc53eaed14e6a303605146b7e5f8b9ea3cef5e`.
- Geen commit of push.

## Bevinding en correctie

**Bevinding.** Een aanwezige `record_text` die geen tekst is, zoals `None`, `42`, `[]` of `{}`, viel terug op `raw_text`. Een meegegeven oordeel werd daardoor actueel pass of fail. Het contract staat de terugval alleen toe als de sleutel ontbreekt.

**Correctie.** In `decision_rule_assessment.py` staat nu `kern = metadata.get("record_text", ctx.raw_text)`. De default geldt alleen bij een ontbrekende sleutel. Een aanwezige niet-tekst gaat ongewijzigd naar de bestaande WP1-validatie (`Int02Invoer`: "kern moet tekst zijn"). Het bestaande pad `Int02ContractError` geeft daarna `error` met `MELDING_E`, zonder assessment en violation, en met `review.actuality = null`.

Ongewijzigd gebleven:
- een lege string blijft tekst en geeft dus NE;
- een afwezige sleutel valt terug op `raw_text`;
- de signalen gebruiken nog steeds `""` voor een niet-tekst.

De module-docstring noemt de nieuwe regel expliciet.

Omvang (`git diff --numstat` t.o.v. `d3fc53ea`):
- `src/services/validation/evaluators/decision_rule_assessment.py`: +4/−2;
- `tests/unit/validation/test_def835_int02_evaluator.py`: +14/−0.

Er zijn geen andere bestanden gewijzigd. De vijf voorgestelde extra testbestanden zijn niet aangeraakt.

## Test (eerst rood)

Nieuwe test: `TestFoutEnOngeldig::test_aanwezige_ongeldige_recordtekst_valt_niet_terug_op_raw_text`, geparametriseerd over:
- scenario `pass` en `fail`;
- `record_text` `None`, `42`, `[]` en `{}`.

Dat zijn de acht gereproduceerde combinaties. De test gebruikt de bestaande helper `_assert_fout`, die controleert op:
- status `error` en score null;
- exacte melding `MELDING_E`, in `reason` en in het onderdeel;
- geen violation;
- `assessment` null;
- `review.actuality` null, dus geen actueel oordeel;
- JSON-serialiseerbaarheid.

Deze bestaande tests zijn ongewijzigd en bleven groen:
- `test_zonder_recordtekst_geldt_de_aangeleverde_tekst` (terugval op `raw_text` bij een afwezige sleutel);
- `test_kern_is_de_exacte_recordtekst`;
- de NE-gevallen, waaronder de lege kern.

## Uitkomsten en hashes

Commando voor beide testbestanden:
`/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/validation/test_def835_int02_evaluator.py tests/integration/contracts/test_validation_result_schema.py -o addopts= -p no:cacheprovider -q -ra`

| Stap | Evaluator sha256 | Testbestand sha256 | Resultaat | Log |
|---|---|---|---|---|
| RED, vóór de fix | `2b8ee83d85a8c6d0…` (= reviewhead) | `b6cc73787a4618b9…` | **8 failed, 111 passed**, exit 1. Alle 8 geven `PASS`/`FAIL` waar `ERROR` wordt verwacht | `bewijs/wp3-claude-r1-rood-v1.log` |
| GREEN v1, eerste fix | `9d012c789d0cbfe4…` | `b6cc73787a4618b9…` | 119 passed, exit 0 | `bewijs/wp3-claude-r1-groen-v1.log` |
| GREEN v2, eindstand | `effb899daf4eb61a…` | `b6cc73787a4618b9…` | **119 passed**, exit 0 | `bewijs/wp3-claude-r1-groen-v2.log` |

Het schematestbestand bleef steeds `712f5e527bd33a5f…` (ongewijzigd). De testbestanden zijn in RED en GREEN byte-gelijk.

Volledige eindhashes:
- evaluator: `effb899daf4eb61aa5c3b2ef0eec3949735090abc2c8d32185fe2fdb3b9a92bd`;
- evaluatortest: `b6cc73787a4618b9b99964350f8ae87b2b0f82dcef8528f5ff8d43f74d99981e`.

Lint (`bewijs/wp3-claude-r1-lint-v1.log`):
- **Ronde 1** faalde op Ruff SIM401 bij de eerste fixvorm (`metadata["record_text"] if "record_text" in metadata else ctx.raw_text`). Die fout gold voor Ruff 0.15.17 en voor de pre-commitversie 0.16.5; Black was groen.
- **Aanpassing.** Ik heb de SIM401-suggestie `metadata.get("record_text", ctx.raw_text)` overgenomen. De semantiek is dezelfde: de default geldt alleen bij een ontbrekende sleutel.
- **Ronde 2**, als gemarkeerd vervolg in hetzelfde log: beide Ruff-versies en Black zijn groen (exit 0).

`git diff --check` gaf exit 0.

Het GREEN v1-log hoort bij de tussentijdse evaluatorhash en blijft bewaard. v2 is de geldige eindstand.

## Grenzen

- Geen nieuwe brede unitrun, zoals opgedragen.
- De acht bekende regressiefailures in de vijf niet-geaccordeerde testbestanden blijven open. Deze correctie raakt ze niet.
- Geen contractbesluit en geen appintegratie (WP5). Het actieve INT-02-record blijft O1.

## Bronnen

- `wp3-codex-review-v1.md` (WP3-R1).
- `src/services/validation/evaluators/decision_rule_assessment.py` r. 111–114.
- `src/domain/int02/contract.py` r. 201–203 (`Int02Invoer`: kern moet tekst zijn).
- De logs hierboven.
