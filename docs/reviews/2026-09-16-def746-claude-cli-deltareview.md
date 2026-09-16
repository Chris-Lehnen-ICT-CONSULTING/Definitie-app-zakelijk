# Deltareview correcties PR456 (K1/L1/L2/L5) — eindcontrole

**Basis van deze delta:** HEAD `c187337a2` (ongewijzigd), branch `feature/DEF-746-ess01-instructies`; werkboom bevat exact de vier gecorrigeerde bestanden (`git status`: 4× ` M` + untracked `docs/reviews/…claude-cli-review.md`). Patch `/tmp/DEF-746-claude-review-correcties.patch` heeft sha256 `bfd222de…9620e8` (bevestigd) en `git apply --check -R` slaagt: de werkboom is precies HEAD + deze patch. Git-status vóór en na mijn controle identiek; ik heb niets gewijzigd.

## Bevindingen per punt

| Punt | Status | Bewijs |
|---|---|---|
| **K1** baseline | **Gesloten** | Diff = 2 regels: `source_commit` `3717d7d79` → `c187337a2` en de ene `source_sha256` → `3436a67d…`. Programmatische invariantencheck: 116 → 116 entries, identieke sleutelset, `comparisons`/`status`/`reason` van alle 116 ongewijzigd, enige afwijkend veld = die ene hash (`/tmp/def746-claude-delta-invarianten.log`). Huidige AST-hash van `test_modular_prompt_builder.py` = `3436a67d…` = baseline-entry; `comparisons` = `['generation_time < 1.0']`; testbestand zelf identiek aan HEAD. Echte guard: **116 locaties, 0 te beoordelen wijzigingen, exit 0**; selftests OK, exit 0 (`…-delta-timing.log`, `…-delta-timing-selftest.log`). JSON parseerbaar. |
| **L1** kanaal-pinning | **Gesloten** | `test_def746_ess01_signalen.py:52-69`: per kanaal een eigen lijst, closure correct gebonden via `_api=api`; `item["reason"] in shown["text"]` is lijst-lidmaatschap (dus de **volledige** reason als één `st.text`-aanroep) en alle overige kanalen negatief geasserteerd. Discriminatiebewijs in-memory (geen repo-edit): met `st.text` omgeleid naar `st.markdown` falen **10/10** renderparametrizaties (`/tmp/def746-claude-delta-l1-mutatie.log`, exit 1) — de oude versie zou hier zijn geslaagd. |
| **L2** docstring | **Gesloten** | Diff raakt uitsluitend de docstring van `_toets_kandidaat` (`definition_orchestrator_v2.py:1529-1531`): beschrijft nu de niet-muterende toetsroute en benoemt de guard expliciet als vangnet. AST van HEAD vs werkboom met docstrings genormaliseerd: **identiek** → geen uitvoerbare productiewijziging; de eerdere volledige unit-/integratieruns blijven daarmee geldig bewijs. Guard-tests `test_def622_generatiegrens.py`: 13/13 groen. |
| **L5** positieve asserties | **Gesloten** | `test_def746_ess01_promptnorm.py:76-82`: Object (systeem/register + "zonder grond blijft dit open"), Maatregel (interventie + "alleen toelaatbaar bij deze bevestigde grond"); r.94-104: type ("Grensgevallen: maatregel en interventie" + "Zonder grond geen voorbeeld…"), resultaat ("een doel of functie alleen met begripsbepalende grond volgens ESS-01"). Alle strings komen letterlijk uit `template_module.py:232-243` en `semantic_categorisation_module.py:223,241`; 12/12 groen. |

**Disposities L3/L4/O1** (waiver op faseoverdracht; comment bij DEF-637; acceptatiepunt bij DEF-748/638): conform mijn advies, geen codewijziging nodig; niet door mij geverifieerd in Linear (buiten mandaat).

## Eigen testuitkomsten

| Commando | Uitkomst | Exit | Log |
|---|---|---|---|
| Gerichte tests (signalen 11, promptnorm 12, def622-guard 13, def747 2, `test_modular_prompt_builder` 5) | **43 passed**, 0 failed | 0 | `/tmp/def746-claude-delta-tests.log` |
| `timing_assert_ratchet.py .` / selftests | 116 locaties, 0 wijzigingen / OK | 0 / 0 | `…-delta-timing.log`, `…-delta-timing-selftest.log` |
| ruff + black op de 3 Python-bestanden | schoon | 0 / 0 | `/tmp/def746-claude-delta-lint.log` |
| Baseline-invarianten + AST-vergelijking | zie tabel | — | `/tmp/def746-claude-delta-invarianten.log` |
| L1-mutatieproef (plugin `/tmp/def746_mut_plugin.py`) | 10 failed / 1 passed (verwacht) | 1 | `/tmp/def746-claude-delta-l1-mutatie.log` |
| Root-allowlist | OK | 0 | — |

Volledige unit- (5841 passed) en integratieruns (571 passed) uit mijn vorige beurt blijven geldig: de enige productiewijziging is bewezen docstring-only.

## Nieuwe concrete bevindingen

Geen in code of tests. Eén administratief punt voor de coördinator: `docs/reviews/2026-09-16-def746-claude-cli-review.md:99` stelt nog "correcties voorbereid, nog NIET toegepast"; het aangekondigde addendum ontbreekt nog in het untracked bestand — vóór commit toevoegen, anders documenteert de repo een achterhaalde staat.

## Mergeadvies

**Akkoord voor commit/push/CI/merge.** Alle vier bevindingen zijn gesloten met uitvoerbaar bewijs; de timingguard is groen; productiegedrag is aantoonbaar ongewijzigd; L1 is nu een echte regressiebewaker. Eén voorwaarde bij het committen: `test_modular_prompt_builder.py` mag niet meer worden aangeraakt vóór de merge (anders valt K1 opnieuw om), en het reviewrapport moet het addendum krijgen.

Deze deltareview is door mij zelf uitgevoerd in dezelfde reviewersessie, zonder agents, extra CLI-sessies, repo-edits, commits of provider-/modelcalls; handovers gelezen maar niet gearchiveerd (read-only mandaat).

**Bronnen:** `git diff`/`git status`/`git apply --check -R` op werkboom 9415; genoemde bestanden met regelnummers; `scripts/ci/timing_assert_ratchet.py:139-140`; logbestanden `/tmp/def746-claude-delta-*.log`.

Coördinator: het gevraagde addendum is vóór commit toegevoegd aan het oorspronkelijke reviewrapport. Canonieke volledige patchhash: bfd222def949715c5620cfd6892f1bac45b75a6c3a7d2f8282873dc6ff49620e. De afgekorte hash in het reviewerantwoord bevat een typografische fout; de volledige hash is afzonderlijk gecontroleerd.
