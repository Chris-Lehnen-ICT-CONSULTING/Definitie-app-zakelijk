# DEF-624 — CI-correctie PR #459: integratiesuite (15 failures) — Claude Code CLI, uitvoerder

Werkboom: /private/tmp/def624-resultaatcontract · branch feature/DEF-624-resultaatcontract
HEAD (ongewijzigd, geen commit door mij): b063664269c612e686e7b1c68ebc53a65e7f4aa1
Python: /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python (3.13.15)
CI-log: /tmp/def624-pr459-integration-job.log (15 FAILED, gericht gelezen na ANSI-strip).

## Oorzaak (per geval vastgesteld)

Alle 15 failures hebben één oorzaak: de dubbels voor de validatiedienst (`validate_definition`-return-dicts) dragen
geen `validation_status`. Sinds DEF-624 maakt `ensure_schema_compliance` (via `DefinitionOrchestratorV2.
_normaliseer_validatie` en `ValidationOrchestratorV2`) zo'n resultaat fail-closed `validation_unknown`
(`contract_status_missing`): `is_acceptable` → False, `overall_score` → placeholder 0.0. Daardoor:
`definition.valid is False` (orchestrator-happy-paths), `is_acceptable is True`-asserties falen (Story 2.4
performance/regressie via `ValidationOrchestratorV2.validate_text`), `process_validation_feedback` wordt wél
aangeroepen (de orchestrator voedt de feedbacklus bij een niet-acceptabel resultaat) zodat
`assert_not_awaited()` faalt, en `monitoring.complete_generation(success=…)` meldt False. De
`assert_not_awaited`-verwachtingen zijn dus niet verouderd: ze volgen zodra het dubbel een run vertegenwoordigt.
Er is geen productielogica die onterecht afkeurt; het fail-closed contract werkt precies zoals bedoeld.

## Aangepaste fixtures (uitsluitend dubbels die aantoonbaar een uitgevoerde run voorstellen)

| Bestand | Fixture | Reden |
|---|---|---|
| tests/integration/services/orchestrators/test_definition_orchestrator_v2.py | helper `validatieresultaat` (+ docstring; `ensure_schema_compliance` geeft sinds DEF-624 een kopie, inhoud gelijk) | schema-conforme stand-in voor het resultaat van de validatiedienst (score + oordeel = run) |
| tests/integration/regression/test_story_2_4_regression.py | helper `validatieresultaat` (+ docstring) | idem |
| tests/integration/test_v2_orchestrator_integration.py | helper `validatieresultaat` (+ docstring) | idem |
| tests/integration/performance/test_story_2_4_performance.py | fixture `fast_mock_validation_service` return-dict | "fast mock validation" = uitgevoerde run met `duration_ms` |
| tests/integration/services/orchestrators/test_definition_orchestrator_v2_enhancement_success.py | `fail_result` én `ok_result` | eerste run faalt, tweede (na enhancement) slaagt — beide zijn runs |
| tests/integration/services/orchestrators/test_definition_orchestrator_v2_feedback.py | `ok_result` | geaccepteerde run met warning-violation |
| tests/integration/services/orchestrators/test_definition_orchestrator_v2_monitoring.py | `validate_definition.return_value` | geslaagde run (monitoring `success=True`, tokens 77) |

Elke wijziging is één expliciete regel `"validation_status": "validated"` (constante `VALIDATION_STATUS_VALIDATED`
in het eerste bestand) in de dict, met DEF-624-commentaar. Geen assertions, performancegrenzen, skips of xfails
gewijzigd; geen algemene stempel (de drie `Mock`/`AsyncMock`-gevallen in de Story-2.4-performancesuite die al
`skip`-gemarkeerd waren, en alle cases voor ontbrekende status elders, blijven onaangeraakt).

Nieuwe regressie (betekenisvol, geen duplicaat van bestaand bewijs — het orchestratorpad was nog niet gedekt):
`TestDefinitionOrchestratorV2::test_validatieresultaat_zonder_runstatus_is_geen_oordeel` — een dubbel zonder
status met `is_acceptable=True`/0.91 → `definition.valid False`, `complete_generation(success=False)`, feedbacklus
krijgt `validation_unknown`/`contract_status_missing`/`is_acceptable False`, dubbel niet gemuteerd. Het
RED-bewijs voor dit gedrag is de CI-failure zelf (identieke situatie vóór de fixture-migratie).

Correctie tijdens het werk: de eerste invoeging van de nieuwe test landde midden in `test_feedback_integration`
(twee slotasserties werden per ongeluk in de nieuwe test opgenomen — GREEN-poging 1 faalde daarop:
/tmp/def624-integratie-correctie-green.log, exit 1). Hersteld: die asserties staan weer in
`test_feedback_integration`; GREEN-poging 2 groen.

## Bewijs

| Stap | Commando (verkort) | Log | Exit | Resultaat |
|---|---|---|---|---|
| RED | pytest 7 betrokken bestanden (vóór correctie) | /tmp/def624-integratie-correctie-red.log | 1 | 15 failed / 21 passed / 3 skipped — exact de 15 uit CI |
| GREEN-1 | idem na fixture-migratie + nieuwe test | /tmp/def624-integratie-correctie-green.log | 1 | 1 failed (verkeerd geplaatste asserties, zie boven) / 36 passed |
| GREEN-2 | idem na herstel | /tmp/def624-integratie-correctie-green-2.log | 0 | 37 passed, 3 skipped |
| ruff/black gewijzigde .py (9) — 1e poging | /tmp/def624-integratie-correctie-lint.log | 0/1 | black: test_definition_orchestrator_v2.py herformatteerd (alleen regellengte in de nieuwe test) |
| ruff/black — eind | /tmp/def624-integratie-correctie-lint-2.log | 0/0 | schoon; herdraai bestand: 11 passed |
| `make mypy-check PY=…` | /tmp/def624-integratie-correctie-mypy-check.log | 0 | baseline 0 |
| `make test-integration PY=… GATE_REPORTS=/tmp/def624-claude-gates/integratie` (hermetische runner) | /tmp/def624-integratie-correctie-make-test-integration.log | 0 | 572 passed, 28 skipped, 15 xfailed, 2 xpassed (beide in tests/integration/test_legacy_vs_new_parity.py, informatieve parity-suite, niet door mij geraakt), 0 failed; run_profile status=ok |

Geen resterende failure.

## Totale CI-correctieset t.o.v. HEAD b0636642 (mapper + baseline + integratie)

- Getrackte diff: /tmp/def624-integratie-correctie-diff-tracked.patch — sha256
  `bc2f6a84eb3a83640046366f84fd76b0c4ef4fc0214a1093a40321c2ec6d66ba` (9 bestanden, +76/−11)
- Nieuw: tests/unit/services/validation/test_def624_mapper_legacy_gate.py — sha256
  `cfe944e4a6cf3c6bfd5ca29d3e3eb364aabe95b7ec8c4b88e95d4c02ad2c26b9`
- Gecombineerde einddiff-hash: `119ca975b02b8349c472721a2b5457ef015f2694bac82af26cf34c9a5927475a`
- Diff-hash na de integratiegate opnieuw gemeten: gelijk. Eerdere bewijsbestanden
  (/tmp/def624-claude-ci-correctie-bewijs.md, /tmp/def624-claude-baseline-correctie-bewijs.md) ongewijzigd.

Geen commit/push; geen .env of gebruikersdatabase; geen echte API-aanroepen (dummy-sleutels in de omgeving,
offline-gate van de runner actief). Klaar voor de read-only Codex CLI-deltareview. Volledige story DEF-624 blijft open.
