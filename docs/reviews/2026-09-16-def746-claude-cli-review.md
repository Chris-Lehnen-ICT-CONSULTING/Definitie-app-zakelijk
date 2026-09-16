# Reviewrapport DEF-746/747 (PR456) — onafhankelijke CLI-review en test

## 1. Geverifieerde basis, HEAD en scope

| Item | Waarde | Bewijs |
|---|---|---|
| Werkboom / branch | `/Users/chrislehnen/.codex/worktrees/9415/Definitie-app` · `feature/DEF-746-ess01-instructies` | `git branch --show-current` |
| Basis | `29b0900d4` = `origin/main` = `git merge-base origin/main HEAD` | eigen `git rev-parse`/`merge-base` |
| HEAD | `c187337a2a04a2ee32a2b2c25c203f9ae5bd849d` | `git rev-parse HEAD` |
| Diff | 3 commits (c5dc1e5a2 A-app, c79a65ffb B1, c187337a2 promptlengte), 19 bestanden, +389/−87 | `git diff --stat basis..HEAD` |
| Niet aangeraakt | onderzoekswerkboom 86af, skill-PR332 | — |

Scope beoordeeld tegen de meegegeven besluiten (functiegrens, brongezag ≠ vrijstelling, signaal ≠ oordeel, geen nieuwe blokkade, B1 exacte invoer, B2/C open, 20k geen harde grens) plus `docs/plans/2026-09-16-def746-technische-specificatie.md` en `…def747-faseoverdracht.md`.

## 2. Bevindingen (gerangschikt naar ernst)

### Bekende CI-bevinding (blokkeert de merge-check; los van deze diff bevestigd)

**K1 — Timing-inventaris rood op `test_performance_baseline`.**
- Trigger: `docs/testing/def563-timing-baseline.json` draagt voor `tests/integration/test_modular_prompt_builder.py::TestBasicPromptGeneration::test_performance_baseline` `source_sha256 = 75c40351…`. Ik heb zelf de AST-hash van het bestand op basis `29b0900d4` berekend: **75c40351…** (baseline was in sync). Op HEAD: **3436a67dbc1ffabfbe2c9ebc9210d6d7d920e3c33723dc5e73689e03de39a7c7** — identiek aan de door jou genoemde inventaris-hash. `comparisons` is ongewijzigd (`generation_time < 1.0`).
- Oorzaak: de hash is over de **hele bestands-AST** (`scripts/ci/timing_assert_ratchet.py:139-140`), dus de fixture-signatuur + `record_testsuite_property`-regels (`test_modular_prompt_builder.py:90,113-115`) flippen hem. CI-stap: `.github/workflows/quality-gates.yml:99`.
- Bewijs: `/tmp/def746-claude-review-timing-ratchet.log` (exit 1, "1 te beoordelen wijzigingen"); selftests van de guard: OK, exit 0 (`…timing-selftest.log`).
- **Dispositie: fix nu, gericht.** Alleen in die ene entry `source_sha256` → `3436a67d…` en op bestandsniveau `source_commit` → de beoordeelde broncommit; `comparisons`, `status: unreviewed` en `reason` ongewijzigd laten (precedent: `docs/analyses/DEF-622-ci-aansluiting-v1.md:10`). Doe dit als **laatste** commit die testbestanden raakt — elke latere wijziging in dat testbestand verandert de hash opnieuw.

### Important — geen bevestigde bevindingen

### LOW (bevestigd; elk met dispositie)

**L1 — Test pint het letterlijke renderkanaal niet.** `tests/unit/validation/test_def746_ess01_signalen.py:53-60` zet `markdown/info/warning/success/error/write/text` alle op één `shown`-lijst; de assertie op r.63 slaagt dus ook als iemand `st.text` (`validation_view.py:644`) door `st.markdown` vervangt. De spec-eigenschap "letterlijk, niet als Markdown/HTML" is daarmee onbewaakt. Productie is wél correct: mijn proef toont de reden **uitsluitend** via `st.text`, met `*…*`, `<b>` en `[link](…)` uit de invoer intact (5/5 passed, `/tmp/def746-claude-review-rendererkanaal.log`). → **fix nu** (goedkoop: per kanaal capteren, alleen `text` mag de reden dragen) of tracked.

**L2 — Verouderde docstring na B1.** `src/services/orchestrators/definition_orchestrator_v2.py:1529-1533` zegt nog "de validatie-orchestrator schoont het meegegeven Definition-object in-place". Dat mechanisme is met B1 verdwenen; de mutatieguard (r.1543-1575) blijft terecht als vangnet en wordt door `test_def622_generatiegrens.py:357-414` nog echt doorlopen (mutatie nu ná toetsing geïnjecteerd op de validatorgrens — geldige herbedrading). → **fix nu** (docstring) of tracked.

**L3 — Dode `cleaning_service`-parameter op de toetsorchestrator.** `validation_orchestrator_v2.py:131-141` bewaart de parameter "voor compatibiliteit" (r.128); `definition_orchestrator_v2.py:303-307` injecteert hem nog; in de klasse wordt hij nergens meer gelezen. Projectregel 4 zegt "geen backwards compatibility"; de DEF-747-faseoverdracht kiest expliciet voor "constructor blijft compatibel". Zelfde patroon in de testhelper: `validatie_cleaning` in `test_def622_generatiegrens.py:111,122` heeft geen aanroepers meer. → **expliciete waiver** op grond van de faseoverdracht, óf tracked opruiming bij B2.

**L4 — Pre-existing promptconflict buiten de bekende STR-06/ESS-05-lijst.** `src/toetsregels/regels/CON-01.json:8` levert als ✅-voorbeeld "Toezicht is het systematisch volgen van handelingen **om te** beoordelen …" — een ESS-01-signaalpatroon op precies de term die deze PR als "Grensgeval — toezicht" markeert (`template_module.py:226`). In de gerenderde prompt staan dus naast elkaar: ✅ toezicht-met-doelzin (CON-01, prompt r.196) en "grensgeval, onderbouw eerst" (template). Niet door deze PR geïntroduceerd (`git diff basis..HEAD -- CON-01.json` is leeg); wel een grens aan de claim "vijf prompts consistent". Bewijs: scan van alle `goede_voorbeelden` tegen de ESS-01-patronen vindt exact twee treffers: CON-01 (`om te`) en ESS-05 (`gericht op`, bekend DEF-637). → **tracked**: toevoegen aan de restconflictlijst DEF-625/637.

**L5 — Dekkingsgaten in de promptnormtest.** `tests/unit/services/prompts/test_def746_ess01_promptnorm.py:57-73`: alleen "Proces" krijgt een positieve assertie op de grensgevaltekst; Object/Maatregel/Informatie/algemeen alleen negatieve asserties (afwezigheid van oude strings). `test_categorie_is_geen_functiegrond` (r.76-86) eveneens alleen negatief. Een regressie die de grensgevalregels voor Object/Maatregel wist, valt niet op. → **fix nu** (klein) of tracked.

### Observaties (geen bevestigde bevinding; reden vermeld)

- **O1 — Semantische spanning in de prompt, niet te bewijzen zonder providerproef.** De G-instructie (`json_based_rules_module.py:315-322`) vraagt "grond en onzekerheid **apart** bij de kandidaat" en de outputspec (`output_specification_module.py:146`) noemt "afzonderlijk voorstel", terwijl de slotinstructie "één enkele zin, zonder toelichting" luidt en de extractor (`opschoning_enhanced.py:68-87`) álle niet-kopregels behoudt. Als een model toch een tweede regel produceert, belandt die in de definitietekst. De spec accepteert dit ("Eén-zin-uitvoer blijft gelden"); geen modelcalls toegestaan → niet bevestigd. Advies: begrensde providerproef zodra C/DEF-748 opent.
- **O2 — Geciteerde "passage" is alleen het triggerwoord** (`hit.group()`, `judgment_review.py:69-71`), bijv. "Te beoordelen passage: om te." Spec-conform, maar dun voor een beoordelaar; contextvenster is een latere verbetering.
- **O3 — Reden alleen voor ESS-01 zichtbaar** (`validation_view.py:643`); de overige elf oordeelregels blijven codes-only. Past bij A-scope.
- **O4 — Gedragsverandering voor gebruikers:** edit-/expert-/import-/exporttoetsing oordeelt nu op de rauwe tekst i.p.v. de opgeschoonde; uitkomsten kunnen afwijken van vóór B1 (bedoeld per DEF-747; vermeldenswaard in de PR-tekst).

### Wat ik positief heb geverifieerd (tegen de besluiten)

- ESS-01 blijft `review_required`/`excluded_from_score`; `runtime_contract` ongewijzigd; `review_policy` heeft reden+issue (`runtime_contract.py:585-603`); telling van 12 oordeelregels ongewijzigd (unitsuite groen).
- Signaal ≠ oordeel: hit, geen hit, ASTRA-paar, toezicht-zin, alsook `actor/pass` in de context → altijd `review_required`, nooit in `violations`/`passed_rules` (`test_def746_ess01_signalen.py`, ook via cache; eigen probe).
- Geen automatische regeneratie: enhancement wordt alleen door `violations` getriggerd (`definition_orchestrator_v2.py:1621-1647`); ESS-01 levert er nooit een.
- Geen nieuwe vaststelblokkade: `grep ESS-01 src/` toont geen gating-logica; CON-01/02-evaluators onaangeraakt.
- B1: `validate_text`/`validate_definition` sturen exact `text`/`definition.definitie`; `record_text` = dezelfde tekst; `_beoordeel_bronnen` krijgt `recordtekst` = `context_dict["record_text"]` (`validation_orchestrator_v2.py:187-204, 252-272, 484`); object en metadata onveranderd (`test_def747_…:32-43`). In productie krijgt `ModularValidationService` geen cleaner (`definition_orchestrator_v2.py:289-294`), dus `cleaned_text == text` tot in de evaluators. Generatiecleaning (fase 6, r.1103-1112) en mutatieguard behouden.
- Callers: edit-tab (`definition_edit_tab.py:1751-1802`), edit-service sync-pad, expert-tab, import (`definition_import_service.py:72-73,152`: opslag bouwt altijd een vers object — B1 maakt getoetst=opgeslagen hier juist consistent), export-gate (`export_service.py:442-452`) — geen caller schoont zelf vóór toetsen.
- Vijf prompts: G-instructie, JSON-uitleg, outputspec, taakmodule, semantische module en templates formuleren dezelfde functiegrens; oude doeltemplates/✅-doelvoorbeelden zijn weg (bevestigd in gedumpte prompts per categorie, `/tmp/def746-claude-review-prompt2-*.txt`). STR-06 en ESS-05 blijven zoals bekend.
- 20k-besluit: `test_performance_baseline` bewaart `> 5000` en `< 1.0 s`; junit-property `prompt_length_chars=21834`, `prompt_length_reference_chars=20000` (`/tmp/def746-claude-review-integration/integration-junit.xml`) — exact zoals de laatste commit stelt.

## 3. Zelf uitgevoerde tests

| Commando | Resultaat | Exit | Log |
|---|---|---|---|
| `make test` (unitgate, offline runner) | **5841 passed**, 75 skipped, 1 xfailed, 21 subtests passed, 721 deselected; runner verzameld=5912; 220 s | 0 | `/tmp/def746-claude-review-unit.log`, rapporten `/tmp/def746-claude-review-unit/` |
| `make test-integration` | **571 passed**, 28 skipped, 15 xfailed, 2 xpassed, 0 failures; 135 s | 0 | `/tmp/def746-claude-review-integration.log`, `…-integration/` |
| `make lint` (ruff + black, src/config) | schoon, 388 bestanden | 0 | `/tmp/def746-claude-review-lint.log` |
| ruff + black op de 8 gewijzigde testbestanden | schoon | 0/0 | `/tmp/def746-claude-review-lint-tests.log` |
| gerichte run van de 7 gewijzigde/nieuwe testbestanden | 78 passed | 0 | `/tmp/def746-claude-review-gericht.log` |
| `timing_assert_ratchet.py .` | 1 gewijzigd (K1), 116 locaties | 1 | `/tmp/def746-claude-review-timing-ratchet.log`, inventaris `…-timing-inventory.json` |
| `test_timing_assert_ratchet.py` (selftests) | OK | 0 | `/tmp/def746-claude-review-timing-selftest.log` |
| `preflight_checks.py .` / `check_root_allowlist.sh` | blocking=0 / allowlist OK | 0/0 | `…-preflight.log`, `…-rootallowlist.log` |
| Proef rendererkanaal (tijdelijke test onder /tmp) | 5 passed: reden alleen via `st.text` | 0 | `/tmp/def746-claude-review-rendererkanaal.log` |
| Probes: promptdumps per categorie; scan goede voorbeelden op ESS-01-patronen; AST-hash basis/HEAD | zie L4/K1 | — | `/tmp/def746-claude-review-prompt*.txt`, `…-goedevoorbeelden.py`, `…-asthash.py` |

**Ongeteste routes (bewust):** echte AI-generatie/providercalls (uitgesloten), Streamlit-UI end-to-end in de browser, B2 (opslag/snapshots/export-readback), semantische modelkwaliteit van de nieuwe instructies (O1).

## 4. Mergeadvies

**Mergebaar na één gerichte correctie (K1).** De diff doet wat de besluiten vragen, de volledige unit- en integratiesuites plus lint zijn groen op exact HEAD `c187337a2`, en ik heb geen productdefect gevonden. Het enige rode signaal is de timing-inventaris, en dat is een baseline-hash die door een inhoudelijk ongewijzigde timingassertie is geflipt.

Volgorde die ik adviseer:
1. **Eerst** (goedkoop, vóór de baseline): L1 (kanaal pinnen), L2 (docstring), L5 (positieve asserties) — samen < 30 regels; L3 formeel als waiver noteren of als opruimissue.
2. **Daarna, als laatste testwijziging:** K1 — baseline-entry hash `3436a67d…` (herbereken na stap 1 als `test_modular_prompt_builder.py` opnieuw wordt geraakt) + `source_commit`.
3. L4 en O1 als tracked issues (DEF-625/637 resp. C/DEF-748) — geen mergeblokkers.

"Tracked" vereist een Linear-ID; die kan ik binnen dit mandaat niet aanmaken — dat is aan de coördinator.

## 5. Onafhankelijkheid, weigeringen en git-status

- Alles hierboven heb ik zelf gelezen, gedraaid en geverifieerd; geen agents, subprocessen, workflows of extra CLI-sessies; eerdere Codex-reviews niet als bewijs gebruikt.
- **Toolweigeringen (niet omzeild):** (1) `ls -la .env .claude/hooks` — permissie geweigerd; (2) security-guard: "Pipe naar interpreter" bij `… | python -c` — herschreven naar scripts onder /tmp; (3) security-guard: `rm` van een tijdelijk testbestand in de repo geweigerd — het hele commando (incl. aanmaak) is nooit uitgevoerd; ik heb de proef daarna vanuit `/tmp` gedraaid met `--noconftest -p tests.conftest`, zodat de repo onaangeraakt bleef.
- Handovers uit de SessionStart-hook heb ik gelezen maar **niet** gearchiveerd (read-only mandaat).
- Geen wijziging aan bron, tests, baseline, config of docs; geen commit/push/merge; geen Linear-/GitHub-berichten; alle artefacten onder `/tmp/def746-claude-review-*`.
- **git-status vóór:** schoon op `c187337a2`, branch `feature/DEF-746-ess01-instructies`. **Na:** schoon, zelfde HEAD en branch (`git status --porcelain` leeg).

**Bronnen:** eigen `git`-uitvoer (basis/HEAD/merge-base/diff); `docs/plans/2026-09-16-def746-technische-specificatie.md`; `docs/plans/2026-09-16-def747-faseoverdracht.md`; `docs/analyses/DEF-622-ci-aansluiting-v1.md:10,17`; genoemde bron- en testbestanden met regelnummers; `.github/workflows/quality-gates.yml:96-99`; de logbestanden in de tabel onder §3.

## Coördinator — verwerking van bevindingen

Review uitgevoerd door de echte Claude Code CLI 2.1.270, sessie e6a178e6-b063-495a-a66b-2854e6ce5f92, model claude-opus-5[1m]. Effectieve tools: Bash, Read, Grep, Glob; geen MCP-servers en geen delegatietools. Dit is een andere review dan de eerdere Codex-subagentreviews. Volledig sessielog: /tmp/def746-claude-cli-review.stream.jsonl.

K1/L1/L2/L5: correcties voorbereid, nog NIET toegepast. De normale apply_patch-aanroep werd door PreToolUse geweigerd bij het bestaande orchestratorbestand; geen alternatieve route gebruikt. De samengestelde patch staat in /tmp/DEF-746-claude-review-correcties.patch. Na handmatige toepassing eerst readback, gerichte tests, werkelijke timingguard en een deltareview door dezelfde Claude CLI-sessie. Appmerge blijft wachten.

L3: expliciete waiver voor deze levering. De geaccepteerde DEF-747-faseoverdracht behoudt de constructorparameter om B1 als gerichte wijziging te leveren; dit is geen beweerde actieve cleaningfunctie. Een eventuele latere API-opschoning valt buiten deze reviewcorrectie.

L4: bestaande CON-01-voorbeeldspanning toevoegen aan restconflicten DEF-625/637. Het positieve CON-01-label gaat over die regel, maar kan in de gecombineerde prompt als algemener oordeel worden gelezen; geen CON-01-normwijziging in deze patch.

O1: nog onbewezen modelgedrag; registreren bij DEF-748/638 als toekomstig acceptatiepunt. Geen modelcall of herstelactivatie. O2/O3/O4 zijn binnen de beschreven scope; PR beschrijft het behoud van ruwe toetsinvoer al.

De skill-PR332 is reeds regulier gemerged (6df26e9e54c4b2e2c5df75a3bd84bba9ca5ede89). App-PR456 is NIET gemerged.

## Addendum — correcties toegepast en door Claude CLI geverifieerd

De bovenstaande melding dat de correctiepatch nog niet was toegepast is historisch. Chris heeft de patch handmatig toegepast; reverse-applycontrole en hashcontrole zijn geslaagd. Volledige patchhash: `bfd222def949715c5620cfd6892f1bac45b75a6c3a7d2f8282873dc6ff49620e`.

Dezelfde Claude Code CLI-sessie heeft K1, L1, L2 en L5 gesloten: 43 gerichte tests geslaagd, timingguard 116 locaties zonder afwijkingen, baseline-invarianten en Ruff/Black groen. De productie-AST zonder docstrings is identiek aan c187337a2; de eerder door Claude uitgevoerde volledige suites blijven relevant. De aangescherpte rendertest faalt aantoonbaar bij een in-memory omschakeling van st.text naar st.markdown (10 verwachte failures). Geen nieuwe codebevindingen. Claude geeft akkoord voor commit/push/CI/merge; merge blijft afhankelijk van de actuele GitHub-controles.

Het volledige deltaoordeel staat in `2026-09-16-def746-claude-cli-deltareview.md`. Logs: `/tmp/def746-claude-delta-{tests,timing,timing-selftest,lint,invarianten,l1-mutatie}.log`. L3-waiver, L4 bij DEF-637 en O1 bij DEF-748 blijven zoals hierboven vastgelegd.
