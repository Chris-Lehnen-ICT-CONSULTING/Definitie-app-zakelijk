# DEF-624 — CI-correctie PR #459: grep-gate-baseline (make grep-check) — Claude Code CLI, uitvoerder

Werkboom: /private/tmp/def624-resultaatcontract · branch feature/DEF-624-resultaatcontract
HEAD (ongewijzigd, geen commit door mij): b063664269c612e686e7b1c68ebc53a65e7f4aa1 · basis bceb6ab80a930a2403b51de9a0312880de527f97
Python: /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python (3.13.15)
CI-failure: /tmp/def624-pr459-tests-failure.log — `make grep-check` (DEF-665, fail-closed):
`stale rule=context-str path=src/services/service_factory.py line=825 · invalid reason=baseline_stale`, exit 2.

## Vaststelling (zelf gecontroleerd)

De gate (`scripts/maintenance/grep_gate.py::_handhaaf`) matcht een baseline-entry op (path, line, text) en eist
het vastgelegde `count`. De entry:

- rule `context-str`, path `src/services/service_factory.py`, text
  `        self, begrip: str, context: str | dict | None = None, **kwargs: Any`, count 1.
- Basis bceb6ab8: die tekst staat op regel **825** (`git show bceb6ab8…:src/services/service_factory.py`).
- HEAD b0636642 én werkboom: dezelfde tekst staat op regel **857**; het bestand bevat hem exact één keer
  (`grep -c` = 1). De verschuiving (+32) komt van de DEF-624-wijzigingen hoger in het bestand
  (`_score_of_none`, `_extract_score`, `_met_discriminator`, `_score_of_niet_beschikbaar`).
- Er speelt niets anders dan een regelverschuiving: rule, path, text en count zijn ongewijzigd; geen nieuwe
  entry, geen uitzondering, geen gatewijziging.

## Correctie

`scripts/maintenance/grep_gate_baseline.json`: uitsluitend `"line": 825` → `"line": 857` van die ene entry
(1 regel, +1/−1). Diff: /tmp/def624-ci-correctie-baseline-diff.patch — sha256
`3ee7e6097bbba3a229a5d74ff9387110dbfd8525a64b454c61670a468ee8334b`; baselinebestand na correctie sha256
`8b20c45aa71f10fef5fded9f39df053df2d32ab47e22d2badb4b8ac4c4146032`.

```diff
       "path": "src/services/service_factory.py",
-      "line": 825,
+      "line": 857,
       "text": "        self, begrip: str, context: str | dict | None = None, **kwargs: Any",
       "count": 1
```

## Bewijs

| Stap | Commando | Log | Exit | Resultaat |
|---|---|---|---|---|
| RED | `make grep-check PY=…` vóór correctie | /tmp/def624-ci-correctie-grep-check-red.log | 2 | stale baseline entries=1 (service_factory.py line=825), baseline_stale |
| GREEN | `make grep-check PY=…` na correctie | /tmp/def624-ci-correctie-grep-check-green.log | 0 | baselined=11, baseline entries=11, blocking findings=0 |

Geen extra tests (regelnummer-spiegel is niet betekenisvol). De mappercorrectie uit
/tmp/def624-claude-ci-correctie-bewijs.md blijft intact en staat los van dit bestand. Geen commit/push.
