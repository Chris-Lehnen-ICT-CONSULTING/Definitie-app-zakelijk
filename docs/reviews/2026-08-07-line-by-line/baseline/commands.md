# Baseline commands

## Scope en uitvoering

- Review snapshot: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Uitvoeringsbranch: `feature/DEF-XX-uitputtende-code-review-execution`
- Interpreter: `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python`
- Python: `3.13.8`
- Datum: `2026-08-07`

De Makefile-testtargets roepen `pytest` rechtstreeks aan en respecteren de
`PY`-variabele niet. Daarom zijn voor coverage, smoke, acceptance en de
per-file integration-runs de exacte targetargumenten uitgevoerd via
`/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest`. Dit
voorkomt dat de globale Python 3.9-pytest wordt gebruikt. Er zijn geen echte
API-credentials toegevoegd en geen applicatiebestanden gewijzigd.

## Verplichte baseline

| Plancommando | Effectief commando | Exit | Real | Volledig log |
|---|---|---:|---:|---|
| `make lint` | `make PY=/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python lint` | 0 | 3,26 s | `baseline/logs/quality-lint.log` |
| `make complexity-check` | `make PY=... complexity-check` | 0 | 0,16 s | `baseline/logs/quality-complexity-check.log` |
| `make mypy-check` | `make PY=... mypy-check` | 0 | 27,10 s | `baseline/logs/quality-mypy-check.log` |
| `make overrides-check` | `make PY=... overrides-check` | 0 | 0,06 s | `baseline/logs/quality-overrides-check.log` |
| `make pins-check` | `make PY=... pins-check` | 0 | 0,05 s | `baseline/logs/quality-pins-check.log` |
| `make test-markers-check` | `make PY=... test-markers-check` | 0 | 0,09 s | `baseline/logs/quality-test-markers-check.log` |
| `make test-cov-ci` | `python -m pytest -q -n 4 --dist loadfile --cov=src --cov-report=term-missing --cov-fail-under=45 -m unit` | 1 | 41,20 s | `baseline/logs/test-cov-ci.log` |
| `make test-smoke` | `python -m pytest -q -m smoke` | 1 | 12,44 s | `baseline/logs/test-smoke.log` |
| `make test-acceptance` | `python -m pytest -q -m acceptance` | 1 | 13,05 s | `baseline/logs/test-acceptance.log` |
| `make audit` | `make PY=/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python audit` | 2 | 15,23 s | `baseline/logs/security-pip-audit.log` |
| `python3 -m bandit -r src -ll -f json` | `python -m bandit -r src -ll -f json` | 1 | 4,00 s | `baseline/logs/security-bandit.log` |
| `python3 -m pip check` | `python -m pip check` | 0 | 0,46 s | `baseline/logs/security-pip-check.log` |

`PYTHONDONTWRITEBYTECODE=1` en task-specifieke caches onder `/private/tmp`
beperkten worktreedrift. Exitcodes zijn behouden; falende tests of scanners
zijn niet opnieuw gelabeld als geslaagd.

## Integration-suite per bestand

De exacte scope is NUL-veilig uit Git afgeleid en als 76 paden vastgelegd in
`baseline/integration-files.txt`. Ieder pad is afzonderlijk uitgevoerd met:

```text
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest \
  <testbestand> -q --timeout=120
```

De twee deterministische shards dekken samen exact de lijst, zonder gaten of
overlap:

- regels 1–38: `baseline/integration-results-a.tsv`, 38 individuele logs in
  `baseline/logs/integration-a/`;
- regels 39–76: `baseline/integration-results-b.tsv`, 38 individuele logs in
  `baseline/logs/integration-b/`.

Totaal gemeten per-file duur: 247,50 seconden. Resultaat: 41 pass, 17 fail,
15 skip, 3 blocked en 0 timeout.

## Diagnostische herhalingen

| Doel | Exact commando | Exit | Real | Log |
|---|---|---:|---:|---|
| Parallelle unit-failures onderscheiden van suitegedrag | `python -m pytest -q -m unit` | 1 | 64,82 s | `baseline/logs/test-unit-serial-comparison.log` |
| Credentialhypothese begrensd toetsen | `ANTHROPIC_API_KEY=test python -m pytest -q -n 4 --dist loadfile` op de zes betrokken unitbestanden | 0 | 20,07 s | `baseline/logs/test-unit-key-diagnostic.log` |

De dummywaarde is uitsluitend voor clientinitialisatie gebruikt; er is geen
live AI-flow of betaalde externe aanroep gestart.

## Reproduceerbaarheid

Vanaf dezelfde reviewcommit, met de bestaande project-venv:

1. gebruik de effectieve commando's uit bovenstaande tabel;
2. zet geen productiecredentials;
3. voer ieder pad uit `baseline/integration-files.txt` afzonderlijk uit;
4. vergelijk exitcode én volledige log, niet alleen de laatste pytestregel.

De oorspronkelijke bronworktree en de review-base zijn door deze baseline niet
gewijzigd.

## Bewijsarchief

De paden in de tabellen zijn de paden binnen `baseline/logs.tar.gz`. Het
ongewijzigde archief bevat alle 90 ruwe logs; `baseline/logs-manifest.sha256`
pint ieder uitgepakt log afzonderlijk. Daardoor blijven originele pytest-
whitespace en scanneroutput intact zonder formattering van bewijsdata.
