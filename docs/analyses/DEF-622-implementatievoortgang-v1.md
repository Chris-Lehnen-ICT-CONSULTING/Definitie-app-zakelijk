# DEF-622 — implementatievoortgang (Claude CLI, implementer)

Worktree `855d`, branch `feature/DEF-622-contextcontract`, basis `d68a98a90`.
Plan: `docs/plans/2026-09-14-DEF-622-contextcontract.md` + `2026-09-14-DEF-622-uitvoeringsbesluiten.md`.
Normbron: `besluiten-v10.md` (B-01 t/m B-10, alleen gelezen uit worktree ab46).

Alle tests met `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest … -p no:cacheprovider`;
offline-bootstrap actief (`tests/conftest.py`), uitsluitend synthetische data.

## Batch 1 — contexttransport (commits `09b0d6ff2`, `3d4b98507`)

RED: `tests/unit/services/orchestrators/test_def622_context_transport.py` → 3 failed (context `{}`; lijsten ontbreken).
GREEN: `src/services/orchestrators/validation_orchestrator_v2.py` — `_context_dict()` (deep copy van `metadata`),
`_enrich_context_with_definition_fields()` zet de drie lijsten altijd canoniek (ook leeg), plus
`categorie`/`ontologische_categorie`/`definition_id` — óók `None` (reviewbevinding Codex: lege recordwaarde liet
aanroeperwaarde staan).
Bestaande tests bijgewerkt op het nieuwe contract: `test_validation_orchestrator_v2.py:163-168,183-188`.
Bewijs: `tests/unit/services/orchestrators/` → 19 passed, exit 0. Pre-existing failure buiten scope:
`tests/integration/regression/test_validation_orchestrator_v2_regression.py` (opent `data/definities.db`, offline-gate).

## Batch 2 — CON-01-contract, geen cijfer, contract 1.3.0 (commit `9a4caf674`)

RED: `tests/unit/validation/test_def622_context_contract.py` → 13 failed (`rule_results` ontbreekt; oude regexnorm).
GREEN:

| Bestand | Wijziging |
|---|---|
| `src/domain/context/contract.py` (nieuw) | `beoordeel_context()`: B-01 aanwezigheid, B-04 naamtreffers (alleen geselecteerde waarden, woordgrens, casefold zoals `contextsleutel` — géén acroniemuitzondering, zie reviewfix 1), B-08 samenstelling, vingerafdruk over term+exacte recordtekst+canonieke context+contractversie(+definitieversie indien meegegeven), beoordeling alleen bij gelijke vingerafdruk, benoemde actor en reden (str-typecheck). `evidence` = gevonden tekst, `context_value` apart; positie in onderdeel-id. |
| `src/services/validation/evaluators/context_metadata.py` | Herschreven op het domeincontract; `score=None`; `metadata["rule_result"]`. |
| `src/toetsregels/runtime_contract.py`, `config/toetsregels/toetsregels_config.yaml` | `ScorePolicy.NO_SCORE = "no_score"` (enum + root-SSOT). |
| `src/toetsregels/regels/CON-01.json` | Patroonlijst weg (B-04); uitleg/toelichting op B-02; `score_policy: no_score`; voorbeeldpaar `review_policy` met reden/issue. |
| `src/services/validation/modular_validation_service.py` | `no_score` boekt nooit een score; `rule_results` in resultaat; `overall_score=None` en `samenhang=None` zolang een `no_score`-regel in de set zit; gate faalt fail-closed op `overall_score_unavailable`/`samenhang_unavailable` (score-eis niet verwijderd; herdefinitie = DEF-630); technische fout op zo'n regel → apart foutonderdeel zonder interne details. |
| `src/services/validation/interfaces.py`, `docs/architectuur/contracts/schemas/validation_result.schema.json` | Contract 1.3.0: `rule_results`, `overall_score`/categoriescores nullable; TypedDicts `RuleResult`/`RuleResultPart`. |
| `src/validation/additional_patterns.py` | CON-01-meta-frasen verwijderd (geen tweede waarheid). |
| `tests/unit/conftest.py` | Fixture `service_met_totaalscore`: echte regelset mínus `no_score`-regels — uitsluitend voor bewijs van rekenmechanica (soft floor, error/duplicaat beweegt cijfer niet); productiescore blijft `None`. |
| Bestaande tests | `test_rule_runtime_matrix.py` + `runtime_cases.yaml` (context per case; CON-01-cases op B-01/B-04), `test_v2_golden_*` (oude regexnorm → nieuwe norm), `test_contractconsistentie_def674.py`, `test_error_blokkeert_acceptatie.py`, `test_validation_guard_failclosed.py`, `test_validation_readiness.py` (1.3.0), aggregatie/determinisme (samenhang `None`, overige categorieën afgerond cijfer). |

Bewijs: `tests/unit/validation/ tests/unit/services/validation/ tests/unit/services/test_modular_validation_{aggregation,determinism,heuristics}.py tests/unit/services/orchestrators/ tests/integration/contracts/`
→ JUnit `reports/def622/batch2-junit.xml`: **1480 tests, 0 failures, 0 errors, 2 skipped** (pre-existing skips: API-key, ontbrekende golden-fixture), exit 0.

Gevolg dat Chris/coördinator moet kennen: met de echte regelset is élk validatieresultaat nu `is_acceptable=False`
met poort `overall_score_unavailable`. Consumenten daarvan (enhancement-retry, `_save_failed_attempt`,
feedback-engine, exportgate `export_service.py:412`, importpreview `definition_import_service.py:87`) zien dus
"niet acceptabel" totdat DEF-630 de gate zonder totaalscore herdefinieert. Dit is bewust fail-closed
(instructie: score-eis niet stil verwijderen).

## Reviewfixes op batch 2 (commits `3715241af`, `ddb94d1bf`)

Onafhankelijke Codex-review (`docs/analyses/DEF-622-contract-review-v1.md`, `-v2.md`): zes + één bevestigde
bevindingen, alle gesloten met RED→GREEN:

| # | Bevinding | Fix | Test |
|---|---|---|---|
| 1 | Detectie afhankelijk van opgeslagen schrijfwijze (acroniem/Unicode) | `_GevouwenTekst` (casefold + offsetmap), acroniemuitzondering weg | `test_detection_follows_casefold_regardless_of_stored_spelling` |
| 2 | `str(True)`/lijst als geldige actor/reden | `_tekst()`-typecheck | `test_review_without_actor_or_reason_does_not_count` (+4 cases) |
| 3 | Binding aan cleaned i.p.v. exacte recordtekst | evaluator op `record_text`/`raw_text`; orchestrator zet `record_text` | `test_evidence_binds_to_exact_record_text_across_cleaning` |
| R3 | `record_text` spoofbaar via caller-metadata in `validate_text` | onvoorwaardelijk uit `text`-argument | `test_validate_text_binds_record_text_to_actual_text_argument`, `test_spoofed_record_text_cannot_revive_an_old_review` |
| 4 | Deelfout wist bewezen onderdelen | `_naamdeel_veilig`, `STATUS_ERROR` in samenstelling | `test_partial_failure_keeps_proven_parts_visible` |
| 5 | `normalize_validation` maakt None → 0.0 en verliest `rule_results` | `_score_of_niet_beschikbaar`, transport van rule_results/statuses/gate/… ; `definitie_checker` slaat None nooit als 0.0 op | `tests/unit/services/test_def622_score_transport.py`, `test_niet_beschikbare_totaalscore_wordt_op_geen_route_nul` |
| 6 | `validation_view` crasht op `float(None)` | "Totaalscore: niet beschikbaar" + `render_rule_results()` (NL-labels, aanleiding/reden/vervolgstap) | `tests/unit/ui/test_def622_validation_view_geen_cijfer.py` |

Bewijs: `reports/def622/reviewfix1-junit.xml` (1565 tests, 0 failures, 7 skipped), `reports/def622/reviewfix-r3.xml` (159, 0).

## Batch 3 — gelijke context en drie keuzes (commit `5191edae1`)

RED: `tests/unit/database/test_def622_gelijke_context_lookup.py` (5 failed van 9), `tests/unit/ui/test_def622_duplicaat_keuzes.py` (6 failed van 7).
GREEN:

| Bestand | Wijziging |
|---|---|
| `src/domain/context/normalisatie.py` | `lees_contextwaarden()` — gedeelde lezer van opgeslagen JSON-contextvelden. |
| `src/database/definitie_duplicates.py` | `zoek_gelijke_context()` op genormaliseerde volledige context (begrip + synoniem, kale connectie, statusvoorrang vastgesteld > review > concept); `find_duplicates` erop. |
| `src/database/definitie_crud.py` | `find_definitie` via `zoek_gelijke_context`; `create_definitie(…, duplicate_reason)` weigert geforceerd duplicaat zonder reden, reden + bestaand id in audit; bestaand record ongemoeid. |
| `src/services/definition_repository.py`, `definition_orchestrator_v2.py` | `force_duplicate_reason` uit options → metadata → `create_definitie`. |
| `src/ui/components/duplicate_check_renderer.py` | `render_selected_definition()`; Gebruik Deze vervangt melding; Genereer Nieuw eist reden (tekstveld) en zet `force_duplicate_reason`. |
| `src/ui/components/definition_generator_tab.py` | toont gekozen record; `_score_uit_resultaat` (None → "Niet beschikbaar", geen `float(None)`). |
| `src/ui/handlers/definition_generation_handler.py` | reden meegeven; force-opties in `finally` opgeruimd (ook bij fout); interne gate eist reden. |
| `tests/apptest/def622_keuzes_app.py`, `run_def622_apptest.py`, `tests/unit/ui/test_def622_apptest_keuzes.py` | Echte Streamlit AppTest in subprocess (root-conftest mockt streamlit): offline-bootstrap in kindproces, echte `ServiceContainer`/`ServiceAdapter` met `BevrorenAIClient`, echte `DefinitionEditTab`. |

Bewijs: `reports/def622/batch3-junit.xml` (**847 tests, 0 failures**), `reports/def622/apptest-junit.xml` (7/7), artefact `reports/def622/apptest/waarnemingen.json`:
Gebruik Deze → selected id = bestaand, melding weg; Bewerk → editor laadt record (text_area bevat de tekst); Genereer Nieuw zonder reden → geen force, waarschuwing, DB ongewijzigd; met reden → nieuw `draft` (id 4) met auditreden "…bewust naast bestaande definitie 3…; reden: …", bestaand record `established` versie 1 ongewijzigd, force-opties opgebruikt, `editing_definition_id` = nieuw id; CON-01-uitleg zichtbaar; `gate_actief=True`, DB binnen sessieroot.

Bijgewerkte bestaande tests: `test_offline_core_journey.py` (DUP_01 draait nu, CON-01 signaleert "strafprocesrecht", score None), versioning-tests dragen `duplicate_reason`.

## Reviewfix op batch 3 (commit `57fd342cc`)

Codex-duplicaatreview (`docs/analyses/DEF-622-duplicaat-review-v1.md`): D1 checker-refilter met eigen normalisatie →
`contextsleutel`; D2 JSON-null → "None" in `lees_contextwaarden` → weggelaten; D3 vroege begripafwijzing liet
force-opties staan → ook daar `_wis_force_opties`; D4 bytes als auditreden → `ValueError` vóór mutatie.
Tests: `tests/unit/domain/test_def622_contextwaarden_lezer.py`, `tests/unit/integration/test_def622_checker_gelijke_context.py`,
uitbreidingen in `test_def622_duplicaat_keuzes.py` en `test_def622_gelijke_context_lookup.py`.
Bewijs: `reports/def622/reviewfix-dup-junit.xml` (**818 tests, 0 failures**).

## Batch 4 — vaststelconflict en CON-01-vaststelvoorwaarde (commit `c8879ec70`)

RED: `tests/unit/services/test_def622_vaststelconflict.py` (ImportError → 14 tests).
GREEN:

| Bestand | Wijziging |
|---|---|
| `src/database/models.py` | `VaststelconflictError`; `DefinitieRecord.get_context_review()/set_context_review()` (markerelement `CON-01-REVIEW` in `validation_issues`, geen schemawijziging). |
| `src/database/definitie_crud.py` | Invariant "max. 1 vastgesteld per begrip + volledige context, ongeacht categorie" op de persistentiegrens: `update_definitie` (statuswijziging naar vastgesteld of identiteitswijziging van een vastgesteld record, verse lezing ónder `BEGIN IMMEDIATE`) en `create_definitie` (status vastgesteld). `find_leidende_definitie`, `set_context_review`; `validation_issues` in `allowed_fields`; statusnotitie in audit. |
| `src/database/definitie_repository.py`, `src/services/definition_repository.py` | Passthroughs. |
| `src/services/definition_workflow_service.py` | `approve(…, vervang_definitie_id)`: conflictcontrole vóór én onder de transactie; bewuste vervanging archiveert het leidende record met opvolgerverwijzing en stelt het nieuwe vast in dezelfde transactie; `gate_status="conflict"`. `_evaluate_gate`: CON-01 herberekend op het record met de vastgelegde beoordeling — geen context / open naamfunctie / vervallen beoordeling / registratiegebruik → `blocked`, niet overrulebaar. |

Bewijs: `reports/def622/batch4-nieuw.xml` (14/14: B-07-gate ×5, conflict ×5 incl. gelijktijdigheid en auditrollback, persistentiegrens ×4), `reports/def622/batch4-junit.xml` (**2239 tests, 0 failures, 13 pre-existing skips**; incl. DEF-482-atomiciteit, workflow, database, UI, journey).

**Bewijsgrens DEF-630:** in de B-07-tests zijn de overige gatecomponenten synthetisch positief (`validation_score=0.9`, geen kritieke issues). De algemene score-/expertgate (in productie: `validation_score` None → "Geen validatieresultaat beschikbaar" → override-required/blocked) is niet gewijzigd en blijft DEF-630. Het onderscheid per-record (DEF-482) versus inter-record (dit) staat in de moduledocstring van de test en de commitboodschap.

## Reviewfix op batch 4 (commit `e9ecf6c09`, V1–V4)

Onafhankelijke review (Codex) op `c8879ec70`: V1 synoniemenuniciteit (ander begrip met ons begrip als synoniem is geen leidend record), V2 reviewversiebinding (eerste opzet: versienummer in de beoordeling, `set_context_review` stempelt `current+1`), V3 actorherkomst (beoordelaar = handelende gebruiker, anders geweigerd vóór mutatie), V4 dubbele/misvormde markers (fail-closed geen beoordeling). Bewijs: `reports/def622/reviewfix-establish-junit.xml` (93/0).

## Batch 5 — opslag/readback, UI, prompts, export (commit `6b233060f`)

| Bestand | Wijziging |
|---|---|
| `src/services/definition_repository.py`, `data_aggregation_service.py` | Readback: `metadata["context_review"]` uit de marker; export-aggregatie geeft de beoordeling door. |
| `src/services/orchestrators/validation_orchestrator_v2.py` | `_enrich…` zet `context_review` en `definition_version` (uit `version_number`). |
| `src/services/export_service.py` | Validatiegate vóór export met de drie opgeslagen lijsten, id, versie en beoordeling. |
| `src/ui/components/definition_edit_tab.py`, `definition_edit_service.py` | Score None-veilig; `rule_results`; bewerk-validatie stuurt `definition_id` + `context_review` mee. |
| `src/ui/components/expert_review_tab.py` | `_render_contextcontract`: open naamsignaal, functie + reden → `set_context_review`, selectie ververst; vaststelconflict → checkbox `vervang_…`. |
| `src/services/prompts/modules/context_awareness_module.py`, `json_based_rules_module.py` | B-02-norm: registratiecontext niet in de zin; naam alleen als inhoudelijk noodzakelijk (`CONTEXTNAAM_NORM`). |

Bewijs: `reports/def622/batch5-junit.xml` (**3429 tests, 0 failures, 13 skips**); nieuwe tests `test_def622_readback_en_export.py`, `test_def622_expert_review_contextcontract.py`, `test_def622_con01_promptnorm.py`.

## V2-deltareviews — versiebinding (commits `95396232b`, `dc1b12fc3`)

Deltareview op `e9ecf6c09` (V2a–V2c) en tweede deltareview op `95396232b` (V2b/V2c rest):

| Punt | Herstel |
|---|---|
| V2a verouderde invoer werd opnieuw geldig gestempeld | `set_context_review(…, *, expected_version)`: optimistic lock ónder de schrijflock (`False` bij afwijkende versie, ook als SQL-guard); payload met een ander versienummer = verouderde invoer, geweigerd vóór mutatie. UI geeft de getoonde versie mee; verouderd snapshot → waarschuwing + ververste selectie. |
| V2b ontbrekend/ongeldig reviewversienummer schakelde de controle uit | Contract: draagt het record een versie, dan telt een beoordeling zonder geldig én gelijk versienummer niet (missing/None/True/[]/{}/"invalid"/2.5); gate benoemt een niet-toegepaste beoordeling met reden. Persistentie: strikt integer (`_is_versienummer`) bij invoer én bij overnemen (True/1.0 nooit "gelijk aan 1"; marker 2.0 nooit als 3 gestempeld). |
| V2c vaststelling liet de eigen geldige beoordeling vervallen | Behoud van de binding uitsluitend bij de atomaire vaststelactie (`change_status(…, ESTABLISHED)` via interne vlag `_behoud_beoordeling`, niet via de facade). Elke andere update (score, toelichting_proces, categorie, ufo, generieke status draft/review, tekst) laat de versiegebonden beoordeling vervallen; geen automatische verlengingsregel. |

Bewijs: `reports/def622/reviewfix-v2-red-junit.xml` (RED), `reviewfix-v2-green-junit.xml` (66/66), `reviewfix-v2-regressie-junit.xml` (3448/0); `reviewfix-v2b-red-junit.xml` (9/20 RED), `reviewfix-v2b-green-junit.xml` (84/84), `reviewfix-v2b-regressie-junit.xml` (3498/0).

**Open — Important, herstelpad gestopt (max. 3 pogingen, besluit coördinator na derde deltareview op `dc1b12fc3`):**
1. Een payload zónder versienummer (missing/null) wordt bij `set_context_review` als actuele invoer gestempeld op `expected_version + 1`. Dat is het ontwerp (de UI levert geen versienummer; `expected_version` is de binding), maar de reviewer merkt het aan als restrisico: de payload zelf draagt geen bewijs van de beoordeelde versie.
2. Een opgeslagen tekstversie `"2"` (via de generieke `validation_issues`-update) wordt door het contract (`_versienummer` accepteert cijfer-tekst) als geldig gelezen → gate `pass`, maar het strikte behoud bij vaststelling (`_is_versienummer`, alleen `int`) neemt haar niet mee → na `approve` readback `blocked`. Inconsistentie tussen de contract-lezer en de persistentie-overname; niet via een vierde fix of de kwaliteitsrefactor opgelost. Voorstel voor het vervolg: één strikte versielezer voor beide (contract én persistentie, alleen `int`), als aparte, kleine wijziging met eigen RED/GREEN.

## Koppelingenreviews op batch 5 (commits `e9739635e`, `f91d12d57`)

Zes bevindingen K1–K6 op `6b233060f` en vier restpunten op `e9739635e`, plus een eigen vondst uit de expert-AppTest:

| Punt | Herstel |
|---|---|
| K1 editor zonder recordversie | `DefinitionEditTab` vervoert `definition_version` naast `context_review`. |
| K2 export vertrouwde metadata ná de `additional_data`-merge; twee lezingen; uitvoer behield vervalste velden | `ExportService.export_definitie_async`: één recordlezing voor aggregatie én validatie; validatiecontext uit `DefinitieRecord.get_contractvelden()`; `DataAggregationService._borg_contractvelden` zet id/versie/context_review/context ook in het exportobject terug op de recordwaarden (poging gelogd). |
| K3 Re-validate zonder id/review/versie (`get_org_list`/`get_jur_list` bestonden niet); selectie niet ververst | `_revalidate_definition`: één actuele lezing, `selected_review_definition` én resultaat uit diezelfde lezing via de canonieke adapter `DefinitionRepository.van_record`. |
| K4 readback splitste `\n\nToelichting:` af, beoordeling gebonden aan de volledige recordtekst; expliciete legacytekst kreeg een andere basis | Eén tekstbasis: de definitiezin (`DefinitieRecord.get_definitie_tekst()`, `splits_definitietekst`, `TOELICHTING_SCHEIDING` als enige conventievastlegging) voor gate, experttab, readback, validatie en export; ingebedde/aangepaste toelichting blijft afzonderlijk. |
| K5 verzonnen actor "expert" | Bestaande identiteit vereist (sessie-`user` of "Reviewer naam" van de reviewflow); zonder identiteit knop uitgeschakeld, geen opslag. |
| K6 checklist met absoluut benoemverbod | `DefinitionTaskModule`-checklist op de B-02-norm. De uitgeschakelde `ErrorPreventionModule` (DEF-169) is bewust niet aangeraakt. |
| Cleaning-binding (eigen vondst) | `ValidationOrchestratorV2.validate_definition` verrijkt vóór de cleaning: `clean_definition` schrijft de opgeschoonde tekst in het object terug, waardoor `record_text`/vingerafdruk aan de opgeschoonde tekst bonden en een geldige beoordeling verviel zodra cleaning een hoofdletter of punt toevoegde. |

Bewijs: `reports/def622/koppelingen-red-junit.xml` (11/15 RED), `koppelingen-green-junit.xml` (15/15), `koppelingen-regressie-junit.xml` (3488/0); `koppelingen2-red-junit.xml` (5/13 RED), `koppelingen2-green-junit.xml` (16/16), `koppelingen2-regressie-junit.xml` (3503/0). Coördinator: alle K-punten gesloten op `f91d12d57`.

## AppTest-ketenbewijs (commits `5191edae1` drie keuzes; `a21d4e459` expertactie)

`tests/apptest/def622_expert_app.py` + `run_def622_expert_apptest.py` + wrapper `tests/unit/ui/test_def622_apptest_expert.py` (subprocess, echte Streamlit `AppTest`, offline-bootstrap, synthetische DB): echte `ExpertReviewTab._render_definition_review` op een echte `ServiceContainer` (workflow-service, orchestrator mét cleaning). Keten: open signaal + gate geblokkeerd + vastleggen uitgeschakeld zonder identiteit → reviewer naam + functie + reden → vastleggen (record en beoordeling versie 2, actor "Reviewer Rood", selectie ververst, CON-01 Voldoet, gate toegestaan) → Re-validate (pass, beoordeling toegepast, geen cijfer) → Vaststellen (established, versie 3, beoordeling gebonden aan 3, één statusaudit) → vijf echte weergaven (Voldoet / Nog te beoordelen / Voldoet niet / Voldoet niet + Nog te beoordelen / Technisch probleem) zonder cijfer. Bewijs: `reports/def622/apptest/expert-junit.xml` (6/6), `expert-waarnemingen.json`; samen met de drie-keuzes-AppTest 13/13. Coördinator-run op `a21d4e459`: 13/13.

**Bewijsgrens (expliciet):** het gezaaide record draagt een synthetische `validation_score=0.9` zonder kritieke issues, zodat uitsluitend CON-01 de gate bepaalt; de bestaande vaststeller-fallback `"expert"` in `_render_review_actions` is ongewijzigd. Dit bewijst de CON-01-keten, níét een complete DEF-630-identiteits-/scoregate.

## Contractregressies en kwaliteit (commits `13f441919`, `0bb7ca0bd`)

- Drie tests naar contract 1.3.0 (geen skip, geen omzeiling): batchvolgorde via het acceptatiepatroon op de synthetische regelset mét totaalscore (fixture `service_met_totaalscore`, verhuisd naar `tests/conftest.py`), plus de expliciete vaststelling dat de echte regelset op alle vier fail-closed sluit; `test_definition_generation` asserteert `overall_score None`, `gates_failed` bevat `overall_score_unavailable`, CON-01 met echte status zonder cijfer, generatie/opslag/readback ongewijzigd; `normalize_validation` houdt een expliciete None (overige gevallen numeriek, per geval verwacht). Bewijs: `reports/def622/contractregressie-junit.xml` (11/11).
- Kwaliteitsratchets: mypy 10 → 0, complexiteit 208 → 197 (baseline 201) door helperextracties zonder gedragswijziging (`_geldige_beoordelaar`, `_bewaak_vaststelinvariant`, `_versieconflict`, `_bruikbare_beslissingen`, `_vooraf_geweigerd`, `_gate_contextlijsten`, `_boek_rule_result`, `_render_deeluitkomst`, `_leg_beoordeling_vast`, `_v2_uit_opgeslagen_validatie`; `find_leidende_definitie` servicelaag op de DB-signatuur). Bewijs: `reports/def622/quality-regressie-junit.xml` (3517/0 incl. beide AppTests).

## Skillbronpatch (niet toegepast)

`docs/analyses/DEF-622-skillpatch-v1.patch` + `DEF-622-skillpatch-v1.md` (bronhashes vóór/na, dry-run exit 0 op kopieën). Smalle B-02-normcorrectie in `definitie-toetsregels/reference.md:29`, `definitie-nederlandse-definities/reference.md:208,225,238` en een CON-01-uitzondering in `definitie-toetsregels/SKILL.md` (*Scoring & Weging*). Geen live writes op `~/.claude` of de bronrepo.

## Stand voor de finale gates (coördinator)

Stabiele checkpoint: HEAD na `0bb7ca0bd` (+ dit document en de skillpatch als `docs`-commit). Openstaand: de twee V2b-restpunten hierboven (gerapporteerd, herstelpad gestopt). Buiten scope en ongewijzigd: de algemene DEF-630-gate (totaalscore `None` → fail-closed `overall_score_unavailable` / "Geen validatieresultaat beschikbaar"), de scoreformule (DEF-624), de bestaande vaststeller-fallback. Geen PR, geen merge, geen gebruikersdatabase.
