# DEF-624 deellevering 1 — correctieronde 2: factory/schema-consistentie (Claude Code CLI, uitvoerder)

Werkboom: /private/tmp/def624-resultaatcontract · branch feature/DEF-624-resultaatcontract
Basis (HEAD, ongewijzigd, geen commit): bceb6ab80a930a2403b51de9a0312880de527f97
Python: /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python (3.13.15)
Deltareview: /tmp/def624-codex-deltareview-result.md — beide resterende P2-bevindingen bevestigd (fix nu);
oorspronkelijke bevindingen 1/3/4/5 gesloten en onaangeraakt gelaten.

## Bronhash (eindcode; alle gates hieronder liepen hierop, hash na afloop opnieuw gemeten: gelijk)

- Getrackte diff: /tmp/def624-claude-factory-diff-tracked.patch — sha256 `5424fc8db5ad4f97f9df01b0bb10b76f9948c0904e462265d80eeae7466e362a`
- Nieuwe/ongetrackte bestanden (9) met sha256: /tmp/def624-claude-factory-untracked-hashes.txt
- Gecombineerde einddiff-hash (patch + hashlijst): `a4be1ac3d761881cb6ac74b23166e704b6f9b38f3537c0b94872163919c4bdbf`
- `git diff --stat`: 32 bestanden, +1225/−448 (vorige ronde: +1167/−448) + 1 nieuw testbestand
  `tests/unit/services/validation/test_def624_factory_schema.py` (53 tests).
- Gewijzigd in deze ronde: `src/services/validation/result_contract.py` (+`READINESS_VELDEN`, `is_geldige_readiness`),
  `src/services/validation/types.py` (fabriek: centrale statusbepaling, `_controleer_expliciete_metadata`;
  `is_valid_result`: unknown-placeholders + readinessvorm), `docs/architectuur/contracts/validation_result_contract.md`
  (2.0.0-rij), nieuw testbestand. Geen andere bestanden aangeraakt.

## Dispositie per bevinding

| # | Bevinding | Dispositie | Correctie | Bewijs |
|---|---|---|---|---|
| A | `is_valid_result` keurde unknown met `is_acceptable=True`/score 0.95 goed; fabriek accepteerde `validation_readiness={}` bij `ruleset_incomplete` | fix nu | `is_valid_result` eist bij `validation_unknown` de placeholders (`is_acceptable` False, `overall_score` 0 zonder bool of None) en, zodra `validation_readiness` aanwezig is, de schemavorm (`is_geldige_readiness`: precies vijf velden, `ready` bool, totalen niet-negatieve gehele getallen, ID-lijsten van strings). De fabriek weigert een readiness buiten die vorm (ValueError, ook bij validated) en `ruleset_incomplete` zonder readiness; geen readiness verzonnen. | `test_probe_a1…`, `test_probe_a2…`, grensmatrix (26 varianten, verwachting vooraf tegen het echte schema geverifieerd — geen "opzetfout"), `test_fabriek_weigert_ongeldige_readiness` (8 varianten × unknown/validated) |
| B | Fabriek wierp ValueError voor status "ok"/True/1/[] (AC 1-regressie) | fix nu | De status gaat ruw in het resultaat en door `bepaal_runstatus`/`met_expliciete_runstatus` (centrale bepaling): None → `contract_status_missing`, ongeldig → `contract_status_invalid`, placeholders afgedwongen — geen exception. Alleen tegenstrijdige expliciete metadata blijft geweigerd: reden bij validated, expliciete unknown zonder contractuele reden, `ruleset_incomplete` zonder readiness, readiness buiten schemavorm, een reden die de afgeleide reden tegenspreekt. | `test_probe_b…` (4 waarden: unknown/contract_status_invalid, schema-geldig), `test_fabriek_none_status…`, `test_fabriek_weigert_tegenstrijdige_expliciete_metadata` (6), `test_fabriek_levert_voor_geldige_combinaties_schemageldige_uitvoer` (6; incl. invoer-immutabiliteit en idempotentie, None-score blijft None) |

## TDD en gates

| Stap | Commando (verkort) | Log | Exit | Resultaat |
|---|---|---|---|---|
| RED | pytest test_def624_factory_schema.py (vóór correcties) | /tmp/def624-claude-factory-red.log | 1 | 29 failed / 24 passed; geen opzetfouten (schemaverwachtingen kloppen) |
| GREEN | idem, na correcties | /tmp/def624-claude-factory-green-1.log | 0 | 53 passed |
| Bestaand | gerichte contract-/consumer-/orchestrator-selectie (24 bestanden/mappen, incl. ronde-1-tests) | /tmp/def624-claude-factory-bestaand-1.log | 0 | 845 passed, 7 skipped |
| ruff/black gewijzigde .py (37) — 1e poging | /tmp/def624-claude-factory-ruff-black-1.log | 0/1 | black: nieuw testbestand herformatteerd |
| ruff/black — eind | /tmp/def624-claude-factory-ruff-black-2.log | 0/0 | schoon |
| mypy ruw (`mypy src/ --check-untyped-defs`) | /tmp/def624-claude-factory-mypy-raw.log | 0 | 0 fouten |
| `make lint PY=…` | /tmp/def624-claude-factory-make-lint.log | 0 | schoon |
| `make mypy-check PY=…` | /tmp/def624-claude-factory-make-mypy-check.log | 0 | baseline 0 |
| `make test PY=… GATE_REPORTS=/tmp/def624-claude-gates/factory` — poging 1 | /tmp/def624-claude-factory-make-test.log | 2 | 1 failed / 6013 passed: `tests/unit/test_working_system.py::TestPerformanceBasics::test_memory_reasonable` (`assert 178667520 < 104857600`; meet RSS-toename van het pytest-proces rond `get_config_manager()`/`get_cache_config()`; bestand niet gewijzigd; slaagde in de drie eerdere gate-runs) |
| `make test` — poging 2, identieke bronhash | /tmp/def624-claude-factory-make-test-2.log | 0 | 6014 passed, 75 skipped, 1 xfailed; run_profile status=ok. Zelfde code, andere uitkomst: de geheugentest is niet-deterministisch; over de oorzaak wordt hier niets geclaimd |
| `make test-cov-ci …/factory` | /tmp/def624-claude-factory-make-test-cov-ci.log | 0 | 6014 passed; coverage 61.47% (vloer 45%) |
| `make test-contract …/factory` | /tmp/def624-claude-factory-make-test-contract.log | 0 | 36 passed, 6 skipped |

Gate-artefacten: /tmp/def624-claude-gates/factory/ (unit-junit.xml van poging 2 — poging 1 is door poging 2 overschreven in dezelfde map; de volledige log van poging 1 blijft: /tmp/def624-claude-factory-make-test.log; unit-cov-junit.xml, unit-coverage.xml, contract-junit.xml, inventarissen).
Eerdere rondes: /tmp/def624-claude-bewijs.md (ronde 0), /tmp/def624-claude-fix-bewijs.md (ronde 1); hun logs bewijzen de toenmalige code (hashes daarin), niet deze eindcode.

## Wijzigingen ná de eindgates

Geen. Alle code-/test-/docwijzigingen zijn vóór de gates gedaan; de bronhash is voor en na de gates gelijk.

## Beperkingen

- `is_valid_result` blijft bewust lichtgewicht buiten status/unknown/readiness (geen value-types van violations of categoriescores); dat is geen nieuwe algemene validator.
- Typehint van `validation_status` blijft `ValidationStatus | None`; runtime accepteert en normaliseert elke waarde (AC 1). Callers die statisch een ongeldig type meegeven ziet mypy als typefout, wat gewenst is.
- Volledige story DEF-624 blijft open (53/44-verificatie, DEF-623). Geen commit/push.
