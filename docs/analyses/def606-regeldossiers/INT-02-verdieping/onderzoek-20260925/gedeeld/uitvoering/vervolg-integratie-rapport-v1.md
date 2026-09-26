# DEF-771 — integratie actuele main (INT-02 + INT-03), voorbereide merges (v1)

26 september 2026. Claude Code CLI-uitvoerder a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Opdracht: `vervolg-integratie-opdracht-claude-v1.md`. Geen commit, push of PR-merge; beide merges staan voorbereid (`--no-commit --no-ff`) voor de coördinator. Geen mergecommit gemaakt.

## Identiteiten (vóór merge gecontroleerd, getrackte werkboom schoon)

| Werkboom | Branch | HEAD | MERGE_HEAD |
|---|---|---|---|
| App `/Users/chrislehnen/Projecten/Definitie-app` | feature/DEF-771-int02-contract-o1 | b56e2878268f744f224e8d1326c9198378b025bc | 076c916671e4e7e9f2843d22669df38eeb79e170 |
| Skills `…/.worktrees/DEF-771-int02-skills` | feature/DEF-771-int02-contract-o1 | 750068253a7389e201daedc5b9aa0afd5c0be032 | 770de55ece429fec826c9d53fd873a109ed8e670 |

Logs: `vervolg-integratie-app-merge-v1.log`, `vervolg-integratie-skills-merge-v1.log`.

## Handmatig opgelost

**App — `src/services/prompts/modules/json_based_rules_module.py` (enig conflict).** Onze INT-02-G (letterlijk ongewijzigd) plus de INT-03-G van main (met DEF-772-commentaar). Weg: de oude INT-02-verbodszin van main ("Vermijd voorwaardelijke formuleringen …") en de oude INT-03-zin van onze branch ("… in dezelfde zin"). Commentaarbinding gecorrigeerd `def771-int02/1` → `def771-int02/2` (bestaand contract). Diff t.o.v. main: uitsluitend het INT-02-blok. Poging 1 van het oplosscript stopte op een eigen te grove controle (de tekst "dezelfde zin" staat in het main-commentaar); er was niets geschreven. Poging 2 toetste op de exacte oude regels.

**Skills — tekst.** Per bestand combineren beide zijden een eigen wijziging t.o.v. de merge-base 1e27a2da:
- `definitie-toetsregels/SKILL.md`, `definitie-nederlandse-definities/SKILL.md`: onze sectie `## INT-02` gevolgd door de volledige `## INT-03`-sectie van main.
- `definitie-toetsregels/reference.md`: onze INT-02-tabelrij plus de nieuwe INT-03-rij van main.
- `definitie-nederlandse-definities/reference.md`: de nieuwe INT-03-regel van main (vervangt "Impliciete verwijzingen") plus onze INT-02-regel (vervangt "Voorwaardelijke formuleringen").
Script: `/tmp/def771_skills_oplossen.py` (eerste aanroep via heredoc door de securityhook geweigerd, niets uitgevoerd). Resultaat t.o.v. main: exact de oorspronkelijke INT-02-delta (+10/−2 op vier bestanden plus beide contracten).

**Skills — binaire bundels.** `cowork-exports/definitie-toetsregels.zip` en `definitie-nederlandse-definities.zip` zijn opnieuw gebouwd met de bestaande generator `./scripts/export-skills-for-cowork.sh definitie-toetsregels definitie-nederlandse-definities` (repositorybron `skills/`, alleen deze twee ZIP's; geen `--live`, geen install/publicatie, niets in `~/.claude` of `~/.agents`). Log `vervolg-integratie-skills-zips-v1.log`, exit 0. Niet gekozen: `cowork-rebuild-skill-zips.sh` (leest `~/.claude/skills`), `build-cowork-alias-zips.py` (maakt de korte alias-ZIP's).

Gestaged: alleen deze zeven bestanden als conflictoplossing; het overige merge-index is inkomend mainwerk. Geen ongetrackt bestand gestaged. Geen conflictmarkers of unmerged entries meer (`vervolg-integratie-diffs-v1.log`).

## Contract en bundels bytegelijk

- Beide `int02-beslisregel.md`: SHA-256 bc16c128c43e247b25db996d25059af48fe56dccea5cdc4012ceb401746b043c (`def771-int02/2`).
- ZIP-inhoud (`vervolg-integratie-zipcontrole-v1.log`, exit 0): per lid gelijk aan de getrackte skillbron (13 leden elk); verschil met de main-ZIP uitsluitend `SKILL.md`, `reference.md` en `references/int02-beslisregel.md`.

## Verificatie

**Tests** (`vervolg-integratie-tests-v1.log`, offline, `DEF771_SKILLS_ROOT` = skillwerkboom): 1166 passed, 5 failed, 5 skipped (bestaande "Run AFTER consolidation"-skips), exit 1. Geselecteerd met `rg`: alle DEF-771-tests, alle DEF-772-unittests, de prompttests rond `json_based_rules_module`, ESS-01/02/03/04-promptbehoud en -signalen, resultaatcontract, runtime-matrix, golden INT, orchestrator- en wrappertests. Integratietests (`tests/integration/…`) bewust niet gedraaid.

- INT-02-G exact: `test_def771_int02_promptnorm` 4/4; contract 15/15; UI 2/2; O1 28/31 (zie B2).
- INT-03-G exact: `test_def772_int03_promptnorm` 8/8; DEF-772 totaal 366 passed, 1 failed (zie B1).
- ESS-01-promptbehoud: `test_def746_ess01_promptnorm` 12/12.

Failures:
1. `test_definition_task_transformation.py::test_no_negative_commands_in_guide` — bekende basisfailure, niet onderzocht.
2. **B1** `test_def772_int03_wrappers.py::test_validate_text_verkrijgt_verse_beoordeling_met_binding`: `assert result["version"] == CONTRACT_VERSION == "2.1.0"` → `'2.2.0' == '2.1.0'`. Nieuwe maintest pint de oude versie; onze goedgekeurde additieve 2.2.0 blijft. Zelfde klasse als de WP5-correctie.
3. **B2** `test_def771_int02_o1.py::test_ne_resultaat_past_in_schema_en_conversie[C23]`, `[C56]` en `::test_rr_boekt_geen_int02_deeluitkomst_en_andere_regels_blijven`: onze schematest valideert alle `rule_results`; `rule_results['INT-03']` (main, `pronoun_reference_assessment.py`) bevat `assessment` en `signals`, die het resultaatschema (`additionalProperties: false`) niet toestaat — ook niet in de mainversie van het schema. INT-02 zelf voldoet (C06, waar INT-03 geen deeluitkomst met die velden levert, slaagt). Dit is een contractgat van main dat onze test zichtbaar maakt, geen INT-02-breuk.

**Ketenproef v3** (script ongewijzigd, SHA-256 d36c4b5f…1df2fe3) op de geïntegreerde werkboom: `vervolg-integratie-keten-v1.json`/`.log`, exit 0; C83/C105/C56 foutloos in route A en route B. De JSON is bytegelijk aan `vervolg-keten-replay-v3.json` (a4037120…217ebd): de proefuitvoer bevat geen bronhashes; die staan in `vervolg-integratie-diffs-v1.log`. Bron van dit bewijs: HEAD b56e2878 + MERGE_HEAD 076c9166 + werkboomdiff (nog geen mergecommit); skills HEAD 75006825 + MERGE_HEAD 770de55e.

**Lint** (`vervolg-integratie-lint-v1.log`): Ruff en Black op de promptmodule exit 0; `make lint` exit 0.

## Staged diff

- App t.o.v. main 076c9166: 160 bestanden (+75655/−31) — de volledige inhoud van onze featurebranch (code, tests, dossier), in `src/` alleen de eerder goedgekeurde DEF-771-bestanden plus de opgeloste promptmodule.
- App t.o.v. onze vorige HEAD b56e2878: 55 bestanden (+10957/−175) — het inkomende mainwerk (INT-03, ESS-01, workflows, `.claude/…` van main) plus de conflictoplossing; in `src/` 24 bestanden (+3375/−129).
- Skills t.o.v. main 770de55e: 8 bestanden (+364/−2): de INT-02-delta en de twee geregenereerde ZIP's.
- Skills t.o.v. vorige HEAD 75006825: 8 bestanden (+61/−5): INT-03-teksten van main, de alias-ZIP's van main en de twee geregenereerde ZIP's.

## Hashes (SHA-256, werkboom)

App: `json_based_rules_module.py` 86e949d5…2b53d8; `judgment_review.py` c70798d9…d259a23f; `modular_validation_service.py` d0380e13…331830df0f; `interfaces.py` 3a8a8600…4b48a4 (CONTRACT_VERSION 2.2.0, onveranderd); schema 8fcb8c84…1c85fe. Skills: toetsregels `SKILL.md` bba6c03e…94d7, `reference.md` 4d3d7e7d…a053; nederlandse-definities `SKILL.md` 88335792…8dc39, `reference.md` 932b9c64…820c; ZIP's 5bf7e3ff…c988 en e31a50a9…4a74. Volledige lijst: `vervolg-integratie-diffs-v1.log`.

## Open punten (niet opgelost, buiten de toegewezen bestanden)

- **B1 — minimale oplossing:** in `tests/unit/services/orchestrators/test_def772_int03_wrappers.py` de assertie naar `"2.2.0"` (1–2 regels), zoals WP5. Vergt toewijzing van dat bestand.
- **B2 — keuze nodig:** (a) de DEF-772-eigenaar breidt het resultaatschema uit voor `assessment`/`signals` in een regeluitkomst (schema-/contractbesluit, niet binnen deze opdracht), of (b) onze drie DEF-771-schematests valideren alleen `rule_results['INT-02']` (±3 regels in `test_def771_int02_o1.py`) en het schemagat wordt apart geborgd. (b) verbergt een echt contractgat; ik adviseer (a) met tijdelijke (b) alleen als de coördinator dat besluit.
- **Alias-ZIP's** `cowork-exports/toetsregels.zip` en `nederlandse-definities.zip` (inkomend van main) bevatten het INT-02-contract niet; dat gold al vóór de merge op onze branch (HEAD-alias zonder `int02-beslisregel.md`). Opnieuw bouwen met `build-cowork-alias-zips.py` valt buiten de opgedragen twee bundels.
- De volledige pytest-suite en integratietests zijn niet gedraaid (coördinator). De UI-/opslag-/exportgrenzen uit `vervolg-keten-rapport-v3.md` blijven gelden; geen volledige ketenoplevering.
