# DEF-622 — CI-aansluiting van bestaande baselines

PR #451 op head `3717d7d79` had twee CI-fouten, ondanks geslaagde lokale functionele gates. De job `CI/tests` stopte op zes verouderde grep-baselinelocaties. `Run Preflight Checks` faalde bij `Check timing inventory dispositions (DEF-563)`: twee hele-module-AST-hashes waren veranderd.

Herstelcommit `bc3608e48` wijzigt uitsluitend twee JSON-bestanden, negen velden:

| Baseline | Correctie | Behouden |
|---|---|---|
| `scripts/maintenance/grep_gate_baseline.json` | Zes regelnummers: interfaces195/219/688/702/714 naar205/229/698/712/724; service_factory801 naar820. | Dezelfde11 entries, rule/path/text/count identiek. |
| `docs/testing/def563-timing-baseline.json` | Twee source_sha256 en source_commit naar de beoordeelde bron3717d7d79. | Dezelfde116 identiteiten, comparisons, status en reason. |

De timinghashes betreffen `benchmark_timer::Timer::assert_under` en `test_batch_validate_performance_benefit`. Beide volledige assertiescopes, inclusief decorators en toleranties, zijn tekstueel en AST-identiek aan broncommit523c1d06e. Ook de omliggende timerfixture en klasse zijn ongewijzigd. De modulehash wijzigt door de verplaatste fixture, import en afzonderlijk gereviewde batchordertest.

## Onafhankelijke verificatie

- `make PY=... grep-check`: exit0,11 bestaande uitzonderingen,0 blokkerende bevindingen.
- `python -I -B scripts/ci/timing_assert_ratchet.py .`: exit0,116 locaties,0 wijzigingen te beoordelen.
- Preflight-selftests34/34, preflightblocking0, timingguard-selftests11/11.
- Alle actuele AST-hashes matchen de officiële inventaris. Baseline-identiteiten, vergelijkingen, beoordelingen en redenen zijn afzonderlijk vergeleken.
- Dezelfde Codex CLI-eindpakketreviewer sloot exact3717d7d79..bc3608e48 zonder nieuwe bevindingen of ontbrekend bewijs; read-only, geen delegatie.

De formeel gevraagde read-only inventarisopdracht is via de normale uitvoeringsgoedkeuring toegestaan en door de coördinator uitgevoerd. Claude heeft de reeds beoordeelde JSON-velden met Read/Edit bijgewerkt en via normale hooks gecommit. Geen beveiligingsinstellingen, gatecode, selectie, tolerantie of nieuwe uitzondering gewijzigd.

Logs en bewijs lokaal: `reports/def622/coordinator-{grep-final,timing-guard-final}.log`, `coordinator-ci-baseline-invariants.json`, `coordinator-timing-inventory-final.json`; volledig reviewoordeel `/private/tmp/DEF-622-codex-ci-baseline-review-v1-result.md`.

Productiecode en tests zijn identiek aan de eerder volledig geverifieerde bron0bb7ca0bd. De functionele gate-uitkomsten en57,26% coverage blijven daarom geldig; de gewijzigde baselines zijn gericht met hun echte guards geverifieerd. V2b blijft open en het herstelpad daarvoor gestopt; PR blijft draft, geen merge of deployment.
