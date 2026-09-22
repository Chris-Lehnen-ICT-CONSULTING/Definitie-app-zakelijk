# DEF-766 / ESS-03 — implementatierapport v1 (Claude Code CLI-uitvoerder)

18 september 2026 · werkboom `/Users/chrislehnen/.codex/worktrees/2075/Definitie-app` · branch `bugfix/DEF-766-ess03-telbaarheid` · base `4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb` · geen commit, merge, push, DB-activering of modelcall.

**Diff-identiteit (eindstand):** `/tmp/def766-cli/app-verification-manifest-v2.json` (SHA256 `c7fb78168a577b42b8261dbd5a87b42299a8d0f19aff3468989938366961e4d4`), 15 bestanden; volledige patch incl. de twee nieuwe tests: `/tmp/def766-cli/def766-diff-v1.patch` (SHA256 `c3484d50a845ec076e2312083aa89bf97c142aa9f2b144f3796b34250d4ac538`, 1277 regels). Manifest-v1 (16 bestanden) is een **tussenstand**: daarop is de Codex-P2 (derde "kies niet stil" → 9 unitfailures) gevonden; die is in manifest-v2 gecorrigeerd (zie §4).

## 1. Wijzigingen

### Productiecode (8 bestanden, +125/−42 zonder tests)

| Bestand | Wat | Criterium |
|---|---|---|
| `src/toetsregels/regels/ESS-03.json` | `naam` ongewijzigd; `uitleg`, `toelichting`, `toetsvraag`, `geldigheid` exact uit tekstvoorstellen-v3 §1 (toelichting aangevuld met de bron/uitwerking-scheiding uit besluitnotitie v2 §1 en de ASTRA-revisieprovenance); nieuw voorbeeldpaar N05/N04 (synthetisch, onderdeelgericht); `relatie` + "Eigen definitie voor elke context"; `runtime_contract` volledig: `judgment_review`, `required_inputs [definition_text, term]`, `judgment`, `review_required`, `no_score`, `review_policy` met reden (synthetisch/onderdeelgericht benoemd) en issue `DEF-766`. `herkenbaar_patronen` ongewijzigd (nu reviewerhulp-signaal, geen bewijs) | 1, 2 |
| `src/services/validation/evaluators/positive_indicator.py` | ESS-03-indicator (`_UNIEKE_IDENTIFICATIE`, reden `unique_id`) verwijderd; docstring documenteert waarom (servicemeting 13×2). Alleen ESS-05 blijft | 3 |
| `src/services/validation/evaluators/judgment_review.py` | ESS-03-tak: lege tekst → `not_evaluated` (alleen ESS-03; gedeelde invoerregel ongewijzigd); `_ess03_reden` met de T-tekst als open vraag ("Nog te beoordelen: is voldoende duidelijk wat hier als één instantie geldt?"), niet-toepasselijkheid als vast te leggen oordeel, categorielabel als registratie (geen vrijstelling), signalen als "Te beoordelen passage" met de vraag "Wat identificeert deze code of claim, binnen welke populatie en geldigheid?"; docstring 13→14 regels | 3, 4 |
| `src/services/validation/evaluators/generic.py` | Alleen docstring (ESS-03 niet langer positieve-patroonregel) | — |
| `src/services/validation/modular_validation_service.py` | `unique_id`-suggestie "Voeg een uniek identificatiecriterium toe (nummer/code/registratie)" verwijderd met DEF-766-toelichting (N23: nummer vernauwt een natuurlijke grens). Geen gedeelde policy geraakt | 4 |
| `src/services/prompts/modules/json_based_rules_module.py` | ESS-03-instructie (G) vervangen door de tekst uit tekstvoorstellen-v3 §2. Eén bewuste aanpassing: "Vraag … om gerichte verduidelijking" is binnen het bestaande uitvoercontract (één zin, alleen de kern; DEF-750-P2, DEF-751-conflictcontract uitsluitend ESS-02) geformuleerd als: onbesliste grens zonder werkelijke tegenspraak → één voorlopige kandidaat zonder melding in de zin, verduidelijkingsvraag blijft bij de ESS-03-beoordeling; werkelijke tegenspraak over de teleenheid → geen stille keuze, geen betwiste telconventie in de kern. Eigen bewoording, zodat de DEF-750/751-frasepins ESS-02-scoped blijven | 4 |
| `src/ui/components/validation_view.py` | Open ESS-03-reden wordt net als ESS-01/02 letterlijk (`st.text`) getoond, ook bij ingeklapte details | 5 (weergave) |
| `src/ui/components/validation_renderer.py` | Heuristische pass-reden "Vereist element herkend" niet meer voor ESS-03 (komt nooit meer als geslaagd binnen) | 3 |

### Tests (5 bestaande bijgewerkt, 2 nieuw; +722 nieuw, +88/−34 bestaand)

| Bestand | Wat |
|---|---|
| `tests/unit/validation/test_def766_ess03_telbaarheid.py` (nieuw, 543 r.) | Contract (evaluator/required_inputs/executability/automation_status/score_policy/example_pair_policy+reason+issue, voorbeelden, relatie, indicator weg); evaluator op de 11 casusregister-cases (H-good … N05) → `review_required`, geen cijfer/violation, geen "voldoet", geen regex-artefact, geen nummerplicht; N03 signaal "registratienummer" als te beoordelen passage; N05 geen afkeur/geen "voeg"; categorielabel = registratie; lege tekst → `not_evaluated`; N06-metadata verandert niets. **Service-route over beide laadpaden** (ToetsregelManager én CachedToetsregelManager→RuleCache, module-fixture met `clear_cache()`): volledige set → `review_required`, niet in `passed_rules`, geen ESS-03-violation, `overall_score None`, `detailed_scores.juridisch None`, ESS-03 genoemd in de `overall_score_unavailable`-reden; ontbrekende term → `not_evaluated`; lege tekst + term → `not_evaluated` (VAL-EMP-001 blijft de fail); evaluatorcrash → `error`, apart foutonderdeel in `rule_results` zonder interne details, `is_acceptable False`; `_verwerk_uitkomst(geen_cijfer=True)` boekt geen score. Geen automatisch herstel: `build_suggestion(reason="unique_id")` geeft geen nummeropdracht; geen ESS-03-suggestie in het resultaat; renderer verzint geen pass-reden. Weergave: reden letterlijk via `st.text` |
| `tests/unit/services/prompts/test_def766_ess03_promptnorm.py` (nieuw, 179 r.) | ESS-03-regelkaart draagt naam/uitleg/G-kern/nieuw voorbeeldpaar, geen oude nummerinstructie, geen ESS-02-gepinde frasen; kandidaat alleen zonder werkelijke tegenspraak (C3-scheiding); ESS-01/02-kaarten ongewijzigd; échte samengestelde prompt (4 categorieën): G-kern exact 1×, oude tekst afwezig, geen instructie die met het uitvoercontract botst, ESS-02-conflictmelding blijft de enige uitzondering |
| `tests/unit/validation/test_contractinvarianten_def676.py` | Proefregel ESS-03 → INT-10 (ESS-03 is nu judgment/no_score/review_policy en dus geen bruikbaar anker; precies de drift die de preconditietest aanwijst) |
| `tests/fixtures/toetsregels/runtime_cases.yaml` | ESS-03 van positief/negatief/grens naar `probe` + `reden` + `issue: DEF-766` (oude positieve case als probe) |
| `tests/unit/validation/test_rule_runtime_matrix.py` | `TestAfgeleideTelling` 36/13/4 → 35/14/4 met DEF-766-toelichting |
| `tests/unit/validation/test_v2_golden_ess_more.py` | ESS-03-test herschreven naar signaaldiscriminatie (claim → signaal + passage; zonder claim → geen signaal; beide open, nooit pass/fail) volgens de DEF-670-les |
| `tests/integration/test_offline_core_journey.py` | Gemeten verwachting 34/29/5/15 → 33/29/4/16 (`coverage_ratio` 0,6226); ESS-03 uit `VERWACHTE_GEFAALDE_REGELS` |

Niet gewijzigd (bewust): `src/toetsregels/regels/ESS-03.py` (validatorlaag; `json_validator_loader` heeft geen productie-import, alleen een commentaarverwijzing in `evaluators/__init__.py`) en `src/validation/definitie_validator.py:207,609` (legacy DEF-507; niet geïmporteerd buiten `src/validation/`). Beide zijn **geen levend pad**; conform het DEF-750-precedent onaangeraakt gelaten. `definition_task_module.py:289` (commentaar "ESS-03/05 in de prompt") blijft juist.

## 2. Acceptatiecriteria

| # | Status | Bewijs |
|---|---|---|
| 1 | ✅ | Norm-/geldigheidsvelden in ESS-03.json; voorbeelden als synthetisch/onderdeelgericht benoemd in `example_pair_reason`; geen nummer-/naam-/uniek-plicht; niet-telbare lezing buiten toepassing, geen algemene vrijstelling (toelichting + `_ess03_reden`) |
| 2 | ✅ | `runtime_contract` volledig volgens tekstvoorstellen-v3 §1; `TestRegelcontract` |
| 3 | ✅ | Indicator verwijderd; `not_evaluated` (term/lege tekst), `review_required` (open), `error` (crash) op de echte service; geen cijfer, geen violation → geen critical-bijdrage aan de gate, geen reparatie. Gedeelde policies ongewijzigd. Legacy paden: niet bereikbaar (zie boven) |
| 4 | ✅ met één bewuste formulering | G/T/H-inhoud toegepast; G-zin over verduidelijking binnen het uitvoercontract geformuleerd (§1). Betekenisbehoud: geen identifier/bron/conventie verzinnen, stof niet tot monster, noodzakelijke namen behouden, registratiecontext buiten de kern; toetsen verandert niets. Geen modelcall |
| 5 | ⚠️ **deels; expliciet onafgedekt** | Weergave van de open reden via de bestaande `validation_view` ✅. Opslag/teruglezen/actie van een **afgerond** menselijk ESS-03-oordeel of bevestigde niet-toepasselijkheid: **niet mogelijk binnen bestaande contracten** — de keten kent alleen regelspecifieke markers (CON-01/CON-02) en een categoriekeuze-event; `judgment_review` leest niets terug. Lacune, codeverwijzingen en drie kleinste besluitopties: `/tmp/def766-cli/contract-gap-v1.md`. ESS-03 staat hiermee op hetzelfde punt als ESS-01/02/04; er wordt geen oud oordeel als actueel en geen vaststelling als ESS-03-pass gepresenteerd |
| 6 | ✅ | RED→GREEN met casusregister-cases, beide laadpaden, term/tekst/error/no_score/prompt/geen-herstel gedekt; bestaande opslag/UI getest voor zover het contract draagt (weergave). Ontbrekende functionaliteit gemeld onder 5 |
| 7 | ✅ | Zie §3; baseline en eindstand beide gemeten met de Python 3.13-venv; geen deps geïnstalleerd; bronconfiguratie ongewijzigd |
| 8 | ✅ (alleen voorstel) | `/tmp/def766-cli/skill-change-plan-v1.md`; niets in `_claude-global-setup` of geïnstalleerde kopieën gewijzigd. **Bevinding:** de beheerde bron loopt voor 3 van de 5 skills achter op de geïnstalleerde kopieën (DEF-743/744/746/754 nooit teruggesynchroniseerd) — distributie zonder terugsync zou die teksten overschrijven |

## 3. Testcommando's, exitcodes, logs (alle onder `/tmp/def766-cli/`)

`PY=/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python` (3.13.15); `ANTHROPIC_API_KEY=sk-ant-api03-unit-test-dummy OPENAI_API_KEY=sk-unit-test-dummy PYTHONDONTWRITEBYTECODE=1` bij elke pytest/make-run (werkboom heeft geen `.env`; dummy-keys, geen echte API). Omgevingsstap: `ln -s ~/Projecten/Definitie-app/.claude/hooks .claude/hooks` (git-ignored, `git status` schoon).

| Stap | Commando | Exit | Log |
|---|---|---|---|
| Baseline unit | `make PY=$PY test` | **0** — 6557 passed, 75 skipped, 1 xfailed | `baseline-make-test.log` |
| Baseline lint | `make PY=$PY lint` | **0** | `baseline-make-lint.log` |
| Baseline journey | `$PY -m pytest tests/integration/test_offline_core_journey.py -q -p no:cacheprovider` | **0** — 3 passed | `baseline-offline-journey.log` |
| RED | `$PY -m pytest tests/unit/validation/test_def766_ess03_telbaarheid.py tests/unit/services/prompts/test_def766_ess03_promptnorm.py -q --tb=line` | **1** — 62 failed, 2 passed (invariantie-guards: ESS-01/02-kaarten ongewijzigd; metadata-onafhankelijkheid) | `red-def766-tests.log` |
| GREEN (nieuw) | idem, `--tb=short` | **0** — 64 passed | `green-def766-tests-run1.log` |
| Gerichte regressies 1 | 12 bestanden/mappen (contractinvarianten, matrix, golden, DEF-750/746/743, registry, aggregatie, taaktransformatie, v2_json_rules, tests/unit/ui) | **1** — 2 failed (DEF-750 split-count door hergebruikte frase) | `green-gerichte-regressies-run1.log` |
| Prompt 2 (tussenstand) | DEF-750 + ESS-03-tests | 0 — 86 passed (met tijdelijk aangepaste DEF-750-counts, later teruggedraaid) | `green-prompt-run2.log` |
| Journey na fix | journey | **0** — 3 passed | `green-offline-journey.log` |
| Unit (tussenstand = manifest-v1) | `make PY=$PY test` | **2** — 9 failed, 6606 passed (DEF-751-frasepins "kies niet stil" 3≠2) | `green-make-test.log` |
| Correctie | ESS-03-G in eigen bewoording; `git checkout -- tests/unit/services/prompts/test_def750_ess02_promptnorm.py`; ESS-03-prompttest pint de C3-scheiding zelf | — | — |
| Prompt 3 | `$PY -m pytest tests/unit/services/prompts/ tests/unit/validation/test_def766_ess03_telbaarheid.py -q -o addopts=""` | **0** — 417 passed, 5 skipped, 1 xfailed | `green-prompts-run3.log` |
| **Eind unit** | `make PY=$PY test` | **0** — 6616 passed, 75 skipped, 1 xfailed (runner: verzameld 6687, exitcode 0) | `final-make-test.log` |
| **Eind lint** | `make PY=$PY lint` (ruff + black op src/config) | **0** | `final-make-lint.log` |
| Testlint | `ruff check` + `black --check` op de 6 gewijzigde/nieuwe testbestanden | 0 | (inline in sessie) |
| **Eind journey** | journey | **0** — 3 passed | `final-offline-journey.log` |
| Functioneel bewijs | `$PY /tmp/def766-cli/proef-na-fix.py` — de 13 onderzoekscasussen (proefinvoer-v1.json) door de echte service, beide laadpaden | **0** — 26/26: `review_required` (H-empty zonder term: `not_evaluated`), geen ESS-03-violation, niet in passed_rules, score None, juridisch None; signalen alleen bij code-/uniek-claims (H-good, N01, N02, N03, N04, N06) | `proef-na-fix.log`, `proef-na-fix.json` |

Netto: 6616 − 6557 = +59 uitgevoerde unittests (64 nieuw; de ESS-03-matrixcases gingen per laadpad van drie reachability-cases naar één probe; de oude ESS-03-golden is 1:1 vervangen).

## 4. Baselinefouten en reviewcorrectie

- Baseline was volledig groen (unit, lint, journey); er is geen pre-existing failure.
- De enige rode tussenstand (manifest-v1: 9 failures in `test_def751_conflict_promptnorm.py` en `test_def751_praktijkproef_correcties.py`) is door mijn eerste G-formulering veroorzaakt (letterlijk "kies niet stil"/"zonder werkelijke tegenspraak"/"geef één voorlopige kandidaat" hergebruikt, die DEF-750/751 op exact 2 pinnen). Codex-app-review-v1 rapporteerde dit als P2. Correctie: ESS-03 draagt dezelfde C3-scheiding in eigen woorden; DEF-750-test staat weer op HEAD; geen bestaande assertie verzwakt. Eindstand bewezen met `final-make-test.log` exit 0.

## 5. Open besluiten (voor Chris / coördinator)

1. **Acceptatie 5 / DEF-624:** keuze uit de opties in `contract-gap-v1.md` (A generieke `rule_review`-marker met terugleespad; B `rule_results`-detail zonder nieuwe status; C afwachten). Zonder besluit blijft een afgerond menselijk ESS-03-oordeel en een bevestigde niet-toepasselijkheid niet opslaanbaar/herkenbaar; ESS-03 blijft na elke validatie `review_required` (zoals ESS-01/02/04).
2. **Verduidelijkingsroute voor ESS-03:** de G-tekst vraagt niet om een tweede uitvoerregel; werkelijke tegenspraak over de teleenheid krijgt géén melding-sentinel (DEF-751 is uitdrukkelijk ESS-02-scoped). Wil Chris die conflictroute verbreden naar de teleenheid, dan is dat een afzonderlijk contractbesluit.
3. **Skilldistributie:** eerst de drift beheerde bron ↔ geïnstalleerde kopieën oplossen (skill-change-plan §0), daarna de vijf passages toepassen.
4. Optioneel: een `docs/plans/…-def766-…md`-specificatie zoals bij DEF-750; niet aangemaakt (niet gevraagd, buiten "alleen software").

## 6. Diffstat (eindstand)

```
 src/services/prompts/modules/json_based_rules_module.py     | 33 ++++++++++-
 src/services/validation/evaluators/generic.py              |  7 ++-
 src/services/validation/evaluators/judgment_review.py      | 68 ++++++++++++++++++++--
 src/services/validation/evaluators/positive_indicator.py   | 30 +++++-----
 src/services/validation/modular_validation_service.py      | 11 ++--
 src/toetsregels/regels/ESS-03.json                         | 31 ++++++----
 src/ui/components/validation_renderer.py                   |  4 +-
 src/ui/components/validation_view.py                       | 11 ++--
 tests/fixtures/toetsregels/runtime_cases.yaml              | 20 +++----
 tests/integration/test_offline_core_journey.py             | 13 +++--
 tests/unit/validation/test_contractinvarianten_def676.py   | 10 ++--
 tests/unit/validation/test_rule_runtime_matrix.py          |  7 ++-
 tests/unit/validation/test_v2_golden_ess_more.py           | 44 +++++++++++---
 13 files changed, 213 insertions(+), 76 deletions(-)
 nieuw: tests/unit/validation/test_def766_ess03_telbaarheid.py (543 r.)
 nieuw: tests/unit/services/prompts/test_def766_ess03_promptnorm.py (179 r.)
```

Geen toegangs- of securityweigering opgetreden. Geen agents, reviewers of extra CLI-sessies gestart.
