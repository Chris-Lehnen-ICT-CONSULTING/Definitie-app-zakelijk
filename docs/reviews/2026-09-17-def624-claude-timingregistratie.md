# DEF-624 — CI-correctie PR #459: timing-inventarisbaseline (DEF-563) — Claude Code CLI, uitvoerder

Werkboom: /private/tmp/def624-resultaatcontract · branch feature/DEF-624-resultaatcontract
HEAD (ongewijzigd, geen commit door mij): 48b6ad75482f97132db1e5b7e078edfb2819587d
Python: /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python (3.13.15)
CI-failure: /tmp/def624-pr459-preflight-v2.log — `scripts/ci/timing_assert_ratchet.py .`:
`timing-inventaris: 116 locaties; 10 te beoordelen wijzigingen` (10× "gewijzigd"), exit 1.

## Vaststelling (zelf geverifieerd)

De ratchet (alleen AST, geen uitvoering) hasht per testmodule de volledige AST (`source_sha256`) en legt per
scope de timingvergelijkingen vast (`comparisons`). De DEF-624-fixturemigratie (commit 48b6ad75) wijzigde drie
integratiemodules (expliciete `validation_status` in validatiedubbels, docstrings, één nieuwe niet-timingtest),
waardoor de module-hash van alle scopes in die bestanden verschoof.

Vergelijking actuele inventaris (`--inventory`, /tmp/def624-timingregistratie-inventory-huidig.json) met de
baseline (/tmp/def624-timingregistratie-vergelijking.log):

- baseline 116 entries, inventaris 116 locaties; **0 nieuw, 0 verdwenen**; **106 identiek**;
- **precies de 10 gemelde entries** wijken uitsluitend in `source_sha256` af, met **identieke `comparisons`**:
  - `tests/integration/performance/test_story_2_4_performance.py` (7 scopes): `a4a96e80…` → `7e50a025…`
  - `tests/integration/regression/test_story_2_4_regression.py` (1 scope): `22312d0f…` → `0941148c…`
  - `tests/integration/services/orchestrators/test_definition_orchestrator_v2.py` (2 scopes): `56ab172e…` → `9a70f774…`
  (één nieuwe hash per bestand, consistent met een module-hash).
- Diff van de drie modules basis bceb6ab8 → HEAD 48b6ad75 (+52/−4): verwijderde regels zijn uitsluitend vier
  docstringregels van de `validatieresultaat`-helpers; toegevoegde asserties horen alle bij de nieuwe
  niet-timingtest `test_validatieresultaat_zonder_runstatus_is_geen_oordeel`. Geen timingassertie,
  performancegrens (`MAX_*`/`MIN_*`), sleep, timeout of decorator gewijzigd (onafhankelijk reviewbevestigd:
  /tmp/def624-codex-ci-review-result.md).

Geen andere afwijking aangetroffen; geen nieuwe uitzonderingen nodig.

## Wijziging (uitsluitend metadata, patroon DEF-746 commit 4b9949804)

`docs/testing/def563-timing-baseline.json` — tekstuele vervanging met behoud van opmaak en sleutelvolgorde:
- 10× `source_sha256` van precies die entries → actuele module-hash;
- 1× `source_commit`: `c187337a2a04a2ee32a2b2c25c203f9ae5bd849d` → `48b6ad75482f97132db1e5b7e078edfb2819587d`.
- Nacontrole (/tmp/def624-timingregistratie-nacontrole.log): 116/116 entries, identieke keys en volgorde;
  `comparisons`, `status` en `reason` van alle 116 entries identiek; alleen de 10 hashes + `source_commit`
  verschillen. `git diff --stat`: 1 bestand, +11/−11 (22 regels; /tmp/def624-timingregistratie-update.log).
- Geen `--update`-generatie, geen versoepeling van grenzen, geen productie- of testcode gewijzigd.

## Bewijs

| Stap | Commando | Log | Exit | Resultaat |
|---|---|---|---|---|
| selftests vóór | `python -I -B scripts/ci/test_timing_assert_ratchet.py` | /tmp/def624-timingregistratie-selftest-voor.log | 0 | OK |
| ratchet vóór (RED) | `python -I -B scripts/ci/timing_assert_ratchet.py .` | /tmp/def624-timingregistratie-ratchet-voor.log | 1 | 116 locaties; 10 te beoordelen wijzigingen (zelfde 10 als CI) |
| inventaris | `… --inventory` | /tmp/def624-timingregistratie-inventory-huidig.json | 0 | 116 locaties |
| vergelijking | veld-voor-veld script | /tmp/def624-timingregistratie-vergelijking.log | — | 10 alleen-hash, 0 comparisons-afwijkingen |
| actualisatie | vervangscript | /tmp/def624-timingregistratie-update.log | — | 7+1+2 entries + source_commit |
| ratchet na (GREEN) | `python -I -B scripts/ci/timing_assert_ratchet.py .` | /tmp/def624-timingregistratie-ratchet-na.log | 0 | 116 locaties; 0 te beoordelen wijzigingen |
| selftests na | `python -I -B scripts/ci/test_timing_assert_ratchet.py` | /tmp/def624-timingregistratie-selftest-na.log | 0 | OK |
| nacontrole | JSON-vergelijking HEAD ↔ werkboom | /tmp/def624-timingregistratie-nacontrole.log | — | zie boven |

Diff: /tmp/def624-timingregistratie-diff.patch — `git diff` sha256
`2fdc7726e95a45f6c9f798cf9cb9c7b4fae458f2c232ad164b41044136a1408e` (/tmp/def624-timingregistratie-diffhash.txt).
Geen suites lokaal gedupliceerd (alleen bewijsmetadata; de normale CI draait op de vervolgcommit).
Geen commit/push; klaar voor de onafhankelijke Codex CLI-review. Eerdere bewijsbestanden ongewijzigd.
