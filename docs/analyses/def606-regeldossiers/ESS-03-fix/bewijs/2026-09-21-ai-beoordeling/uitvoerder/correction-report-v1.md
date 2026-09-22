# DEF-766 ESS-03 AI-beoordeling — correctieverslag ronde 1 (v1)

**Uitvoerder:** Claude Code CLI (Opus 5) · **werkboom** `/Users/chrislehnen/.codex/worktrees/2075/Definitie-app` · **branch** `feature/DEF-766-ess03-ai-beoordeling` · **base** `2c9a6e3a13afa4ecbe39163cc418e2b0f8c41644` · **HEAD ongewijzigd** (geen commits, push, PR of deletes; alle wijzigingen ongecommit in de werkboom).
**Datum:** 2026-09-21 · **Invoer:** `review-phase1-received-v1.md` (R1–R9, allen bevestigd, dispositie *fix nu*) en `browser-verification-v1.md`. Geen andere bestanden uit de onafhankelijke reviewmap gelezen.
**Bijlagen:** `correction-manifest-v1.json` (hashes van alle 57 gewijzigde/nieuwe bestanden, prompt/norm/modelhash, modeluitkomsten v2, exitcodes), `exitcodes-correctie-v1.json`, `ontwikkelrun-v2.json` + `ontwikkelrun-v2.log` (ruwe antwoorden), alle `c1-*.log`/`actieproef-run*.log` onder `/tmp/def766-ai-20260921`. Fase-1-bewijs (`phase1-*`, `ontwikkelrun-v1.*`, `ontwikkelgevallen_v1.json`) is onaangeroerd.

Werkwijze: per bevinding eerst een **gedragsmatige RED** met uitsluitend de fase-1-API (`c1-reproducties-red.log`: 6 failed; `c1-r4r5-red.log`: 3 failed; `c1-optins-red.log`: 4 failed), daarna implementatie en GREEN; nieuwe API-tests apart (`c1-contract-red.log` collectiefout → `c1-contract-green.log` 80 passed). Eindstand: alle DEF-766-suites 296 passed (`c1-def766-suites-eind3.log`, exit 0); `make test` 6853 passed (`c1-make-test-eind2.log`, exit 0); `make lint` exit 0; complexity-ratchet op baseline 201.

---

## R1 — volledige actuele binding bij toetsing, opslag en replay

**Wat er nu geldt.** Een opgeslagen of meegegeven beoordeling telt alleen als (a) contractversie én vingerafdruk (term, tekst, drie contextlijsten, toelichting/categorie/betekenisverduidelijking/ESS-03-verduidelijking, canonieke bronidentiteiten) gelijk zijn, (b) promptversie, normhash, provider én model gelijk zijn aan de **actuele** `Beoordelingsbinding`, en (c) de sha256 per vindplaats van het werkelijk verzonden materiaal (`input.materiaal`) exact het actuele materiaal is — dezelfde vindplaatsen, niet meer, niet minder. Hash-aanwezigheid alleen is geen bewijs (`_materiaalafwijzing`: ontbrekende materiaalbinding → niet actueel). Elke afwijking is zichtbaar `historical` met `expected_binding` erbij; zonder bekende actuele binding (geen dienst) kan niets als actueel gelden. Replay is netwerkvrij: de binding komt uit code (`PROMPT_VERSION`), het regelrecord (normhash) en de `ModelRouter` (`Ess03AssessmentService.binding()`), niet uit een aanroep.

**Codeplaats.**
- `src/domain/ess03/contract.py:339` `materiaalhashes`, `:353` `Beoordelingsbinding` (+`als_dict`), `:694` `_configuratieafwijzing`, `:727` `_materiaalafwijzing`, `:770` `valideer_beoordeling(..., binding=)`, `:852` `_actualiteitsafwijzing` (status → contract/vingerafdruk/model → binding → materiaal, met `historical`-kwalificatie), `:970` `_open_deel` (historisch met eerder oordeel), `:1008` `beoordeel_telbaarheid(..., binding=)`.
- `src/services/validation/ess03_assessment_service.py:381` `binding()`; document draagt `input.materiaal` (materiaalhashes), `input.intentie`, `prompt_sha256`, `deadline_seconds`.
- Keten: `src/services/orchestrators/validation_orchestrator_v2.py:484` zet `context_dict["ess03_binding"]`; `src/services/validation/evaluators/countability_assessment.py:95,100` `_binding_uit(metadata["ess03_binding"])`.
- Replay/opslag: `src/services/definition_edit_service.py:201` `ess03_uitkomst_van_definition(definition, binding=)`, `:226` `bindingsafwijzing_ess03(..., binding=)` + `:270` `_configuratieafwijzing_ess03`, `save_definition(..., ess03_binding=)` (`:502`); UI `src/ui/components/definition_edit_tab.py:1182` `_ess03_binding()` (containerdienst, None bij fout) → heropenen (`_render_ess03_section`) en opslaan (`:2199`).

**Bewijs.**
- RED (fase-1-API): `tests/unit/domain/test_def766_ess03_correcties_reproducties.py::test_r1_stale_prompt_norm_model_en_materiaal_zijn_niet_actueel` — `c1-reproducties-red.log` (exit 1).
- GREEN: `tests/unit/domain/test_def766_ess03_correcties_contract.py::TestR1VolledigeBinding` (6 tests: actuele binding+materiaal toegepast; oude prompt/norm/model historisch; afwijkende materiaalhash; ontbrekende/onvolledige materiaalbinding; zonder bekende binding niets actueel; verwachte binding gerapporteerd) — `c1-eind-contract.log` 80 passed (exit 0).
- Keten/replay: `tests/unit/services/test_def766_ess03_correcties_persistentie.py::TestBindingInKeten` (wrapper → evaluator; evaluator alleen toepassen bij actuele binding, ander model = historisch; replay op record vereist binding) — `c1-eind-persistentie.log` 43 passed (exit 0); `tests/unit/validation/test_v2_golden_ess_more.py` (zonder `ess03_binding` blijft een meegegeven beoordeling `review_required`, met binding `fail`) — `c1-golden-eind.log` 3 passed.
- **Readbackmatrix** (verzocht acceptatiebewijs): `test_def766_ess03_correcties_persistentie.py::test_readbackmatrix_invoerwijziging_maakt_de_beoordeling_niet_actueel` geparametriseerd over **term, tekst, organisatorische_context, juridische_context, wettelijke_basis, broninhoud, toelichting, betekenisverduidelijking, ESS-03-verduidelijking** (9) en `::test_readbackmatrix_configuratiewijziging_maakt_de_beoordeling_historisch` over **prompt, norm, provider, model** (4): na opslaan + herladen wordt de beoordeling zichtbaar niet-actueel/historisch met behoud van het document — `c1-eind-persistentie.log` (exit 0).

## R2 — gesloten antwoord en velden/typen; ongeldig bewijs → technische fout

**Wat er nu geldt.** `parse_modeluitvoer` accepteert uitsluitend één kaal JSON-object (eventueel in precies één codeblok dat het hele antwoord omvat); omliggende tekst, lijsten, meerdere objecten of afgekapte JSON worden niet door een deelstring 'gerepareerd'. `structuurfout_modeluitvoer` eist exact de acht velden (geen onbekende, geen ontbrekende), gesloten `verdict`/`applicability` die onderling stroken, niet-lege `reason`, optionele tekstvelden als tekst of null, `evidence` als lijst van `{location, quote}` (tekst) met minstens één item bij een afgerond oordeel, en `question` **uitsluitend** bij `insufficient_information` en dan **precies één** gerichte vraag (één zin, eindigt op `?`, één vraagteken — één string met twee vragen is geen gerichte vraag). Elke afwijking is `malformed_response` (status `error`, geen oordeel, niet gecachet). De prompt zegt dit expliciet (`Ess03AssessmentService.PROMPT_VERSION = "ess03-assess/2"`).

**Codeplaats.** `src/domain/ess03/contract.py:475` `_is_een_gerichte_vraag`, `:496-565` `_veldenfout`/`_waardenfout`/`_bewijsfout`/`_consistentiefout` → `structuurfout_modeluitvoer`; `src/services/validation/ess03_assessment_service.py:288` `parse_modeluitvoer` (`_CODEBLOK.fullmatch` + `json.loads` van het hele antwoord), `:609` `_beoordeel_antwoord` (deadline → kaal JSON → structuur → bewijs), systeemprompt antwoordvorm (`_systeemprompt`, "Exact deze acht velden", vraagvorm).

**Bewijs.** RED: `test_r2_omhuld_antwoord_wordt_niet_stil_tot_object_teruggebracht`, `test_r2_twee_vragen_in_een_string_is_niet_een_gerichte_vraag`, `test_r2_onbekend_veld_is_geen_geldig_antwoord` — `c1-reproducties-red.log`. GREEN: `TestR2GeslotenAntwoord` (parser-matrix, gesloten veldenset/typen/vraagvorm, welgevormde insufficient) — `c1-eind-contract.log`; dienst: `tests/unit/validation/test_def766_ess03_correcties_service.py::test_niet_gesloten_of_onverifieerbaar_is_technische_fout_zonder_cache` (geparametriseerd: omhuld antwoord, twee vragen, onbekend veld, verzonnen citaat → `error`, niet gecachet) en `::test_geldig_antwoord_wordt_wel_gecachet_en_heeft_geen_rejected` — `c1-eind-dienst.log` 41 passed (exit 0). De 8 echte antwoorden van run v2 waren alle kale JSON-objecten met de acht velden; de drie `insufficient_information`-antwoorden hadden elk precies één vraag (`ontwikkelrun-v2.json`).

## R3 — geen reden toepassen waarvan de grond is afgewezen; geen ruwe foutcache onder de dienst

**Wat er nu geldt.** `valideer_oordeel` geeft `(None, rejected)` zodra één bewijsitem niet letterlijk in het verzonden materiaal staat (onbekende vindplaats, leeg citaat, citaat niet in materiaal) — het hele oordeel is dan onbruikbaar; er wordt geen reden meer toegepast met 'gestript' bewijs. In de dienst is dat `unverifiable_evidence` (status `error`, `rejected` gevuld, `raw_response_sha256`, nooit gecachet). Onder de dienst wordt de ruwe antwoordcache van de gedeelde `AIServiceV2` per aanroep uitgezet (`use_cache=False`), zodat een eerder fout/afgewezen antwoord nooit uit die laag terugkomt; de dienstcache bewaart uitsluitend volledig gevalideerde oordelen.

**Codeplaats.** `src/domain/ess03/contract.py:586` `_verifieer_bewijs`, `:620` `valideer_oordeel`; `src/services/validation/ess03_assessment_service.py:609` `_beoordeel_antwoord` (unverifiable_evidence), `_technische_fout` (nooit `_onthoud`), opt-in `use_cache=False` bij de aanroep (`:530`); `src/services/ai_service_v2.py:163` `use_cache: bool | None` (per aanroep), `:331` `_cachetreffer`.

**Bewijs.** RED: `test_r3_een_verzonnen_citaat_naast_een_echt_citaat_draagt_geen_oordeel` — `c1-reproducties-red.log`. GREEN: `TestR3Bewijs` (verzonnen naast echt → onbruikbaar; uitsluitend verzonnen → onbruikbaar; geverifieerd bewijs onaangeroerd; replay met veranderd bewijs in het document niet actueel) — `c1-eind-contract.log`; `test_def766_ess03_correcties_service.py::test_ruwe_cache_van_de_gedeelde_ai_laag_wordt_omzeild` (echte `AIServiceV2` met gevulde `utils.cache`: de dienst krijgt het verse providerantwoord, niet het gecachete) en `tests/unit/services/test_def766_ai_route_optins.py::test_use_cache_false_per_aanroep_omzeilt_de_gedeelde_ruwe_cache` — `c1-eind-dienst.log`, `c1-eind-ai-laag.log` (exit 0).

## R4 — dezelfde volledige actuele betekenisgegevens in alle paden

**Wat er nu geldt.** `betekenisverduidelijking` (DEF-751) reist mee in generatievalidatie (`bronmeta["betekenisverduidelijking"]` in de generatieregistratie), in recordvalidatie (wrapper verrijkt de context uit `generation_prompt_data`) en in editor-toetsing (`bouw_validatiecontext`), en de replay (`ess03_intentie_van_definition`) gebruikt exact dezelfde waarde; zij zit in de vingerafdruk en in het materiaal (`context`-vindplaats).

**Codeplaats.** `src/services/orchestrators/definition_orchestrator_v2.py:1227,1409`; `src/services/orchestrators/validation_orchestrator_v2.py:630` `_verrijk_met_ess03_velden`; `src/services/definition_edit_service.py:162` `_betekenisverduidelijking_uit`, `:169` `ess03_intentie_van_definition`, `bouw_validatiecontext` (`:83-88`).

**Bewijs.** RED: `tests/unit/services/test_def766_ess03_correcties_reproducties_r4r5.py::test_r4_editorcontext_draagt_de_betekenisverduidelijking_van_het_record` — `c1-r4r5-red.log` (exit 1). GREEN: `test_def766_ess03_correcties_persistentie.py::TestBetekenisverduidelijking` (editorcontext neemt de recordwaarde over; replay gebruikt dezelfde waarde) en de readbackmatrix-parameter `betekenisverduidelijking` — `c1-eind-persistentie.log` (exit 0); generatie: `tests/unit/services/orchestrators/test_def766_ess03_integration.py` — `c1-eind-evaluator-keten.log` (exit 0).

## R5 — verduidelijking: expliciet mee bij save, bewust leeg ≠ ontbrekend, bewaren zonder geslaagde beoordeling

**Wat er nu geldt.** De ESS-03-verduidelijking is een eigen recordwaarde onder de bestaande JSON-opslag (`generation_prompt_data["ess03_verduidelijking"]`, beheerde sleutel in `ESS03_OWNED_KEYS`; **geen nieuwe tabel/kolom/schema**). De editor vervoert de actuele sessiewaarde expliciet bij opslaan (`updates["ess03_verduidelijking"]`, ook `""` = bewust gewist; `None` = veld niet getoond → onaangeraakt). Zij wordt nooit uit een (oude) beoordeling afgeleid: `ess03_intentie_van_definition` leest alleen `metadata["ess03_verduidelijking"]`; `_herstel_ess03_beoordeling` herstelt haar uitsluitend uit `record.get_ess03_verduidelijking()`. Een nieuwe verduidelijking wordt zonder geslaagde beoordeling bewaard, heropend en meegetoetst; het oude oordeel wordt door de vingerafdrukwijziging historisch (zichtbaar, niet toegepast).

**Codeplaats.** `src/database/models.py:94-98,607` (`ESS03_VERDUIDELIJKING_KEY`, `get_ess03_verduidelijking`: None = nooit, "" = gewist); `src/database/definitie_crud.py:1311` `_ess03_invoer_uit`, `:1326` `_geldige_ess03_verduidelijking`, `:1335` `_verwerk_registraties`, `:1374` `_voortbouwbasis`, `:1390` `_verwerk_ess03_registratie` (één lezing/serialisatie); `src/services/definition_repository.py:161` `_ess03_verduidelijking_invoer`, `:174` `_voeg_ess03_invoer_toe`, `:1279` `_herstel_ess03_beoordeling`; `src/services/definition_edit_service.py` `_apply_updates` (str → metadata), `:169-179`; `src/ui/components/definition_edit_tab.py:1169` `_sessieverduidelijking`, `:2169` `updates["ess03_verduidelijking"]`, `:1332` heropenen/toetsen.

**Bewijs.** RED: `test_r5_gewiste_verduidelijking_valt_niet_terug_op_de_oude_beoordeling`, `test_r5_zonder_sleutel_wordt_geen_verduidelijking_uit_de_beoordeling_afgeleid` — `c1-r4r5-red.log`. GREEN: `test_def766_ess03_correcties_persistentie.py::TestVerduidelijking` (bewaard en heropend zonder beoordeling; bewust gewist valt niet terug en maakt het oude oordeel historisch; nieuwe verduidelijking met verse beoordeling; gewijzigd na toetsing = stale; bindingsafwijzing gebruikt de actuele verduidelijking) — `c1-eind-persistentie.log`; editor: `tests/unit/ui/test_def766_ess03_editor.py::test_opslaan_vervoert_de_actuele_verduidelijking_ook_bewust_leeg` — `c1-eind-ui.log` 19 passed (exit 0).

**Regressie gevonden en gefixt in deze ronde (door `make test`):** een editor-opslaan met gewijzigde categorie (expliciet commando `record_category_choice`) vervoert nu óók de verduidelijking; de ESS-03-stap las de registratie opnieuw via `_registratie_basis`, die de zojuist in dezelfde UPDATE gezette keuze als 'ruwe invoer' wegfilterde → `tests/unit/ui/test_def751_categoriekeuze_ui.py` 2 failed (`c1-make-test-eind.log`, exit 2). RED-reproductie op DB-niveau: `test_def766_ess03_correcties_persistentie.py::TestVerduidelijking::test_verduidelijking_en_categoriekeuze_landen_samen_in_een_update` (`c1-keuze-ess03-red.log`, exit 1). Fix: `_voortbouwbasis` (`definitie_crud.py:1374`) — de laatste stap bouwt voort op wat de eerdere stappen (bewijs, keuzestaat) al gesaneerd in `velden` zetten. GREEN: `c1-keuze-ess03-green.log` 730 passed (incl. alle DEF-751- en database-suites); `make test` run 2 exit 0.

## R6 — gehele beoordelingsoperatie tijdbegrensd; herhalingen voorkomen op alle gebruikte lagen; echte pogingen registreren

**Wat er nu geldt.** De hele operatie (aanroep én nabewerking in de onderliggende lagen) valt onder `asyncio.timeout(timeout_seconds)`, en na terugkeer wordt de verstreken tijd nogmaals tegen de deadline gelegd: een aanroep die te laat terugkomt door blokkerende nabewerking is `timeout`, ook als de HTTP-call zelf slaagde. Voor ESS-03 krijgen alle werkelijk gebruikte lagen expliciet één poging: `AIServiceV2.generate_definition(use_cache=False, max_attempts=1, max_retries=0, token_estimate="heuristic")` → `AsyncGPTClient._make_request_with_retries(max_attempts=1)` (eigen retrylus) → `AnthropicClient/OpenAIClient.chat_completion(max_retries=0)` → `sdk.with_options(max_retries=0)` (SDK-retries per aanroep); de heuristische tokenraming voorkomt de blokkerende tiktoken-encoder-initialisatie in de nabewerking. Werkelijk waargenomen herhalingen worden gemeten via een logfilter op precies de loggers waar de SDK's/`AsyncGPTClient` een herhaling melden (`anthropic._base_client`, `openai._base_client`, `utils.async_api`; tijdelijk INFO-niveau, daarna hersteld) → `attribution.attempts_observed`/`retries_observed` in het document. Dit zijn **beperkte opt-ins** met `None`-defaults: zonder opt-in is het gedrag van alle andere app-functies ongewijzigd (retrylus, cache, tiktoken, SDK-default) — geen generiek framework, geen dependencywijziging, geen providerbrede beleidswijziging.

Over het browserlog (SDK-retry 10:44:44.986; D01 163,125 s): de oorzaak van de 163 s is niet bewezen; daarom is de test gebouwd met **werkelijk vertraagde nabewerking** (een AI-laag die na een snel antwoord blokkeert), niet op aannames. In run v2 duurde D01 7,4 s met `attempts_observed=1`.

**Codeplaats.** `src/services/validation/ess03_assessment_service.py:375` `timeout_seconds`, `:458` `_beoordeel_met_model` (`asyncio.timeout`, `_Pogingenteller`, opt-ins `:530-534`), `:609` `_beoordeel_antwoord` (deadline-check na terugkeer), `:712` `_Pogingenteller`, `_RETRY_LOGGERS`/`_RETRY_MARKERS` (`:103-108`); `src/services/ai_service_v2.py:163-166` kwargs, `:370` `_clientopties`, `_estimate_tokens(..., heuristic=)`; `src/utils/async_api.py:143-144` (pop vóór cachekey), `:214-215` `_make_request_with_retries(max_attempts, max_retries)`; `src/services/ai/base_client.py:96` protocol, `anthropic_client.py`/`openai_client.py:59,69` `with_options(max_retries=…)`.

**Bewijs.** RED: `c1-optins-red.log` (4 failed: cache/retries/encoder niet per aanroep stuurbaar). GREEN AI-laag (echte `AIServiceV2`/`AsyncGPTClient`/`AnthropicClient` met fake provider/SDK): `test_def766_ai_route_optins.py` (`use_cache=False` omzeilt de gedeelde cache; `max_attempts=1` = precies één providerpoging bij tijdelijke fout; **zonder opt-in blijft de bestaande retrylus intact**; heuristische raming slaat tiktoken over; Anthropic-client zet `max_retries` per aanroep op de SDK) — `c1-eind-ai-laag.log` 80 passed (incl. bestaande `test_ai_clients`, `test_ai_service_v2_*`, `services/ai`). GREEN dienst: `test_def766_ess03_correcties_service.py::test_route_vraagt_expliciet_geen_cache_een_poging_en_geen_sdk_retries`, `::test_blokkerende_nabewerking_overschrijdt_de_deadline_en_is_timeout` (snelle call + blokkerende nabewerking > deadline → `timeout`, geen oordeel), `::test_trage_aanroep_wordt_door_de_deadline_afgebroken`, `::test_echte_ai_laag_doet_een_poging_en_registreert_die` (echte AI-laag: 1 poging, `attempts_observed=1`), `::test_waargenomen_herhalingen_worden_geteld_niet_hardgecodeerd` (record op `anthropic._base_client` "Retrying request" → `retries_observed=1`) — `c1-eind-dienst.log` (exit 0). Echte run v2: 8/8 `attempts_observed=1`, totaal 59,3 s binnen de totale deadline van 480 s (`ontwikkelrun-v2.log`).

## R7 — technisch onvolledig bronmateriaal geeft geen onbeperkte actuele pass; replay op dezelfde verzonden bewijsbasis

**Wat er nu geldt.** Er wordt niets meer afgekapt: een bronpassage langer dan `max_passage_chars` (8000) is vóór de aanroep de technische fout `input_truncated` (status `error`, geen modelaanroep, geen inhoudelijk oordeel — dus ook geen inhoudelijke afkeuring voor een technische invoerbeperking; de melding vraagt de bron te verkorten/splitsen). Passages binnen de grens gaan volledig mee. Replay controleert het oordeel tegen exact het verzonden materiaal via de materiaalhashes (R1) én verifieert de citaten opnieuw tegen het actuele materiaal; er is geen weblookup als uitweg (de dienst doet geen zoekactie; de prompt verbiedt externe kennis als bewijs).

**Codeplaats.** `src/services/validation/ess03_assessment_service.py:485-503` (`te_lang` → `input_truncated`), `bouw_beoordelingsprompt` zonder afkapping (`:221-224` docstring), `max_passage_chars` (`:333,371`); `src/domain/ess03/contract.py:727` `_materiaalafwijzing`.

**Bewijs.** `test_def766_ess03_correcties_service.py::test_te_lange_passage_is_technische_invoerbeperking_zonder_modelaanroep` (geen aanroep, `error`/`input_truncated`, bron-id genoemd) en `::test_passage_binnen_de_grens_gaat_volledig_mee`; fase-1-test aangepast: `tests/unit/validation/test_def766_ess03_assessment_service.py` (geen `afgekapt`-gedrag meer) — `c1-eind-dienst.log` (exit 0). Replay op dezelfde bewijsbasis: `TestR3Bewijs::test_replay_met_veranderd_bewijs_in_het_document_is_niet_actueel`, readbackmatrix-parameter `broninhoud` — `c1-eind-contract.log`, `c1-eind-persistentie.log`.

## R8 — D04/D07 onterecht afgekeurd; D06 ambigu; promptverfijning met nieuwe versie

**Correctie (geautoriseerd, geen normkeuze): prompt `ess03-assess/2`.** Toegevoegd in de systeemprompt: (punt 3) "De aanwezigheid van een naam, nummer of het woord 'uniek' bewijst niets; **het ontbreken ervan is geen gebrek**. Ontbreekt in het materiaal de conventie die de identificerende werking onderbouwt (referentsoort, populatie/naamruimte, toekenning, geldigheid), dan is dat ONTBREKENDE INFORMATIE en geen bewezen gebrek: kies dan insufficient_information met één gerichte vraag naar die conventie"; fail-definitie beperkt tot "uitsluitend bij een gebrek dat uit het materiaal zelf aantoonbaar is en dat je citeert" met de drie voorbeelden; regel "Circulariteit, een definiendum dat als eigen bovenbegrip terugkeert of een ontbrekend bovenbegrip is op zichzelf geen ESS-03-grond; dat raakt andere regels … loopt het onderscheid via een genoemd middel waarvan de onderbouwing ontbreekt, dan is de uitkomst insufficient_information"; gesloten antwoordvorm (R2). Normtekst (`ESS-03.json`) ongewijzigd: normhash `372bb329…e028` gelijk aan fase 1. Systeemprompt-hash: fase 1 `722e6a2e…3d6e` → nu **`e51d06cb3c878d78f2a66135c248e5e8d2a4e95cc589a4fed816c411b125c758`**. Door de promptversie in de binding (R1) zijn alle fase-1-beoordelingen (`ess03-assess/1`) nu zichtbaar historisch.

**Ontwikkelgevallen v2** (`tests/fixtures/ess03/ontwikkelgevallen_v2.json`, nieuw; v1 onaangeroerd): labels **vóór** de eerste aanroep vastgelegd; D04 en D07 **letterlijk ongewijzigd** (gebruikersprompt-hash byte-identiek aan v1, bewezen in de droge controle en in `correction-manifest-v1.json › vergelijking_met_v1`); **D06a** = nieuwe ondubbelzinnige variant van D06 met dezelfde kandidaattekst en expliciete referent (fysieke meetinstallatie) en eenheid (één installatie = één meetobject, continuïteit bij onderdelenvervanging) in de bedoelde betekenis plus de registerconventie als bron; regressies D01 (pass), D02 (fail via bron), D05 (fail intrinsiek), D03 (not_applicable), D09 (insufficient bij strijdige bronnen). Alle vier uitkomsten in de set (pass 2, fail 2, not_applicable 1, insufficient_information 3). De runner bewijst fail-closed dat `verwacht`/`grond`/`doel` de prompt niet beïnvloeden (prompt zonder die velden is tekenidentiek; grond/doel komen nergens letterlijk voor; negatieve controle slaat aan).

**Echte run v2** (`scripts/ess03/run_ess03_gevallen.py`, productieklassen `Ess03AssessmentService` op `AIServiceV2` + `ModelRouter` route `validation` → `anthropic/claude-opus-4-8`; opt-ins `use_cache=False, max_attempts=1, max_retries=0, token_estimate=heuristic`; `AI_SDK_MAX_RETRIES=0`; dienstcache 0; deadline 60 s per beoordeling en 480 s totaal; `max_tokens` 1200; `temperature_sent=null` → **geen determinismeclaim**): **8 aanroepen, 8 transportpogingen waargenomen, 8/8 conform, 0 afgewezen citaten, 59,3 s totaal**.

| Geval | Verwacht (vooraf) | v1 (`/1`) | **v2 (`/2`)** | Duur | Pogingen | Vraag (v2) |
|---|---|---|---|---|---|---|
| D04-code-zonder-scope (ongewijzigd) | insufficient_information | fail ✗ | **insufficient_information ✓** | 9,2 s | 1 | "Volgens welke conventie wordt het registratienummer toegekend (referentsoort, populatie/naamruimte, toekennende instantie en geldigheids-/uniciteitsvoorwaarden)?" |
| D07-register-zonder-conventie (ongewijzigd) | insufficient_information | fail ✗ (circulariteit) | **insufficient_information ✓** | 8,8 s | 1 | "Wat is de onderbouwde conventie van het blijvend uniek nummer in register R, dat wil zeggen voor welke referentsoort en naamruimte/populatie het geldt en hoe toekenning en blijvende geldigheid zijn geregeld?" |
| D06a (nieuwe ondubbelzinnige variant) | pass | — (D06: fail ✗) | **pass ✓** (3 citaten: toelichting ×2, bron) | 7,6 s | 1 | — |
| D01-natuurlijke-grens | pass | pass (163,1 s) | **pass ✓** | 7,4 s | 1 | — |
| D02-isbn-exemplaar | fail | fail | **fail ✓** (bron geciteerd) | 5,5 s | 1 | — |
| D05-ontkende-uniciteit | fail | fail | **fail ✓** (intrinsiek) | 6,4 s | 1 | — |
| D03-stof | not_applicable | not_applicable | **not_applicable ✓** | 4,4 s | 1 | — |
| D09-tegenstrijdige-bronnen | insufficient_information | insufficient_information | **insufficient_information ✓** | 9,8 s | 1 | "Welk van de twee aangeleverde protocollen (A: …, of B: …) geldt voor de bedoelde betekenis van 'meetuitvoering'?" |

Ruwe antwoorden (volledig, met `raw_response_sha256`) staan in `ontwikkelrun-v2.json › resultaten[].aanroep.ruwe_tekst`; D04 (`207da69c…a714`), D07 (`47e77f02…ded8`) en D06a (`204b6a9a…58be`) hieronder letterlijk in bijlage A. Geen relabeling: de vergelijking is verwacht-vs-gekregen op vooraf vastgelegde labels. **Kwalificatie D06:** het oorspronkelijke D06 is niet opnieuw gedraaid en blijft als ambigu gekwalificeerd (referent onduidelijk in de toelichting-loze variant); D06a toont dat de code-betekenis (onderbouwde conventie + expliciete referent/eenheid → pass; genusvorm geen afkeurgrond) door het model wordt gevolgd. Dit is ontwikkeldata (synthetisch, 8 gevallen, één run, geen determinisme): het bewijst de correctie op precies deze gevallen, geen kwaliteitsclaim over de regel in het algemeen.

**Codeplaats.** `src/services/validation/ess03_assessment_service.py:131-214` `_systeemprompt`, `:334` `PROMPT_VERSION`; `scripts/ess03/run_ess03_gevallen.py` (totale deadline, `attempts_observed`, `_controleer_afscherming`, `temperature_sent`, schema `def766-ess03-proefrun/2`). Log/exit: `ontwikkelrun-v2.log` (exit 0).

## R9 — label "Onvoldoende informatie" expliciet in UI en opgeslagen replay

**Wat er nu geldt.** Een toegepast `insufficient_information`-oordeel toont in de normale weergave (regeluitkomsten, gedetailleerde lijst, editor-heropening uit de opgeslagen replay) het eigen label **"❓ Onvoldoende informatie"** met de gerichte vraag en de ontbrekende informatie; het generieke "Nog te beoordelen" blijft gereserveerd voor een werkelijk niet-beschikbaar/niet-uitgevoerd/historisch of onbruikbaar oordeel (`review.assessment.applied=False`).

**Codeplaats.** `src/ui/components/validation_view.py:513` `_LABEL_ONVOLDOENDE_INFORMATIE`, `:516` `_inhoudelijk_label(detail)` (alleen bij `applied=True` en verdict `insufficient_information`), `render_rule_results`/`_render_deeluitkomst(label_override=)`; het contract levert de grondslag (`Deeluitkomst.status=review_required` + `review.assessment.verdict`).

**Bewijs.** RED: `test_r9_onvoldoende_informatie_draagt_een_eigen_label` — `c1-reproducties-red.log`. GREEN: `tests/unit/ui/test_def766_ess03_weergave.py::TestRegeluitkomsten::test_onvoldoende_informatie_toont_precies_de_vraag` ("Onvoldoende informatie" in kop en deel, "Nog te beoordelen" afwezig, precies de vraag), `::test_niet_beschikbaar_is_geen_eindantwoord` (niet-beschikbaar blijft generiek), editor: `tests/unit/ui/test_def766_ess03_editor.py` (heropenen uit opgeslagen replay toont het label) — `c1-eind-ui.log` 19 passed (exit 0).

## Ontbrekend acceptatiebewijs — gekoppelde actieproef vaststellen én export

**Test:** `tests/unit/services/test_def766_ess03_actieproef.py` (nieuw) — echte keten `ValidationOrchestratorV2` → `ModularValidationService` (echte regelset) met fake `Ess03AssessmentService` (pass/fail/not_applicable) op een record in een echte tijdelijke SQLite-repository; de echte evaluatoruitvoer landt zoals in de app als `validation_issues`/`validation_score` op het record (`issues_uit_validatieresultaat(result)` — **geen zelf samengesteld issue**). Daarna de echte `DefinitionWorkflowService.approve(..., user_role="reviewer", expected_version=…)` met de echte `WorkflowService`, en de echte `ExportService.export_definitie_async` met en zonder validatiegate.
- **Vaststellen:** de negatieve ESS-03 (`severity=warning`, `advisory`) staat op het record, maar `gate_reasons` zijn voor pass en fail **identiek**, bevatten geen "ESS-03" en wél de bestaande blokkades (scoregate DEF-622/630, `CON-0x`); status blijft `review` in beide gevallen; not_applicable verandert de `preview_gate` evenmin.
- **Export met gate:** de gate draait de echte wrapper (dus de echte ESS-03-evaluator: 2 dienstaanroepen per scenario) en beslist voor pass en fail **gelijk** ("Export geblokkeerd: … validatiegate" door de bestaande `is_acceptable`-regel), zonder "ESS-03" in de reden. **Export zonder gate:** TXT-export slaagt met de negatieve ESS-03 zichtbaar in de inhoud via de app-route `ValidationRenderer.build_detailed_assessment(result)` → `toetsresultaten` ("⚠️ ESS-03 … AI-beoordeling").
**Log/exit:** `c1-eind-actieproef.log` 4 passed (exit 0); tussenstanden `actieproef-run1.log` (TXT-export geeft een pad, geen inhoud → test aangepast om het bestand te lezen), `actieproef-run2.log`.

## Aanvullende wijzigingen in deze ronde

- **Complexity-ratchet (CI, DEF-418):** eerste meting na de correcties 201 → 213 (+12), alle twaalf in eigen DEF-766-code (`c1-complexity.log`, exit 2). Opgelost door gerichte refactors van uitsluitend eigen/geraakte functies zonder gedragswijziging en zonder baselinewijziging: contract (`structuurfout_modeluitvoer` → vier controles + pipeline; `valideer_beoordeling` → `_vul_samenvatting`/`_actualiteitsafwijzing`/`_kaal_opgeslagen_oordeel`; `_ai_deel` → `_ai_reden` + `_ACTIE_PER_STATUS`), dienst (`_beoordeel_antwoord`), `ai_service_v2` (`_cachetreffer`, `_clientopties`, `_tokenmetadata`), `definition_edit_service` (`_configuratieafwijzing_ess03`), `definition_repository` (`_voeg_ess03_invoer_toe`), `definitie_crud` (`_ess03_invoer_uit`, `_verwerk_registraties`). Eindstand 201 = baseline (`c1-complexity-3.log`, exit 0). Alle suites na de refactors groen (`c1-refactor-crud.log` 788 passed; `c1-def766-suites-eind3.log` 296 passed).
- **Docstrings** van `ess03_assessment_service.py` (module) en `domain/ess03/contract.py` (module) bijgewerkt op R1/R2/R3/R6/R7.
- **Golden-test** `tests/unit/validation/test_v2_golden_ess_more.py` aangepast op R1 (zonder binding `review_required`, met binding `fail`) — inhoudelijke aanscherping, geen verzwakking.
- **Formattering:** ruff-fixes (2, alleen in eigen tests) en black op 15 eigen/geraakte bestanden; systeemprompt-hash daarna gecontroleerd identiek aan run v2 (`e51d06cb…`).

## Gates op de eindstand (exitcodes in `exitcodes-correctie-v1.json`)

| Gate | Log | Exit | Resultaat |
|---|---|---|---|
| `make test` (unitgate) | `c1-make-test-eind2.log` | 0 | 6853 passed, 75 skipped, 722 deselected, 1 xfailed (281,97 s); run_profile ok |
| `make lint` | `c1-make-lint-eind2.log` | 0 | ruff + black schoon |
| ruff/black op alle 51 gewijzigde/nieuwe .py | `c1-ruff-2.log`, `c1-black-2.log` | 0 | schoon |
| `make test-markers-check` | `c1-markers-eind.log` | 0 | 485 testbestanden gemarkeerd |
| `check_root_allowlist.sh` | `c1-root-allowlist-eind.log` | 0 | schoon |
| `make complexity-check` (ratchet) | `c1-complexity-3.log` | 0 | 201 = baseline |
| `check_no_todo_markers.sh` | `c1-todo.log` | 0 | schoon |
| `check-file-size.sh` (informatief) | `c1-file-size.log` | 1 | **pre-existing**: `definition_repository.py` 1353 LOC > 1000 (god-object-klasse, niet door deze ronde geïntroduceerd; geen brede fix) |
| Alle DEF-766-suites + golden ESS | `c1-def766-suites-eind3.log` | 0 | 296 passed |
| Gerelateerde regressies (DEF-743/751/622/624, orchestrator, AI-laag, database, story 2.4) | `c1-regressie-eind.log` → fix → `c1-golden-eind.log`, `c1-keuze-ess03-green.log`, `make test` | 0 | zie exitcodes |

## Budget en pogingen

Fase 1: 12 ontwikkelcalls + 2 browserbeoordelingen + 1 waargenomen SDK-retry (browserlog 10:44:44.986) = 15 conservatief. Correctieronde: **8 aanroepen, 8 transportpogingen waargenomen** (`attempts_observed=1` elk; geen retries, geen cache). Totaal conservatief **23 van 60**; er zijn 30 over voor de eindtests. Geen extra calls gedaan (D06-origineel bewust niet herhaald; run v1 niet herhaald).

## Beperkingen en buiten scope (genoteerd, niet gefixt)

- **Auto-save (`definitie_drafts` ontbreekt op de nieuwe browsertestdatabase)** uit `browser-verification-v1.md`: geen ESS-03-fixopdracht; ongewijzigd. De lokale browsertestdatabase en andermans documenten zijn niet aangeraakt.
- **D06-origineel** blijft ambigu (niet opnieuw gedraaid); D06a is de ondubbelzinnige ontwikkelvariant. De 8 uitkomsten zijn ontwikkeldata zonder determinismeclaim (`temperature_sent=null`).
- **Testartefact:** de eerste actieproef-run schreef één gitignored bestand `exports/definitie_eiland_20260921_093314.txt` in de werkboom (TXT-export schrijft cwd-relatief); niet verwijderd (geen deletes toegestaan); de test gebruikt sindsdien `monkeypatch.chdir(tmp_path)` en JSON-export in `export_dir`.
- **`check-file-size.sh`** faalt pre-existing op `definition_repository.py` (1353 LOC); deze ronde voegde daar ~20 regels aan toe (`_voeg_ess03_invoer_toe`) — geen brede fix, hoort bij het bestaande god-object-traject.
- Ongetrackte menselijke ADR (`docs/adr/ADR-002-…`) en `docs/plans/…` niet aangeraakt en niet in het manifest als uitvoerderswerk; live skills en ALG-391-freeze niet geraakt.
- **Browserharnas:** nieuwe AppTest-/browserharnascode is niet gevraagd in deze ronde; de coördinator bedient de browser (`browser-acceptance-checklist-v2.md` niet gelezen — niet aan mij toegewezen).
- **Draaiende apps:** tijdens deze ronde draaiden twee Streamlit-instanties uit deze werkboom (poorten 8543 en 8544, `src/main.py`); `data/definities.db` (gitignored, mtime 12:16:51) is door die apps geraakt, niet door mijn tests (die gebruiken uitsluitend `tmp_path`-databases). Ik heb de database niet aangeraakt. Omdat de broncode tijdens het draaien is gewijzigd (o.a. prompt `/2`, binding, refactors), moeten deze instanties **herstart** worden vóór de browserverificatie van de eindstand; anders toetst de browser mogelijk deels oude modules.

## Bijlage A — ruwe antwoorden R8-kern (letterlijk, run v2)

**D04-code-zonder-scope** (`raw_response_sha256 207da69cc5871ec9a2962508e05e277d5012b33e2dcc9572bfca9f8ecb3ea714`)
```json
{
  "verdict": "insufficient_information",
  "applicability": "applicable",
  "unit": "een meetobject",
  "reason": "De bedoelde eenheid is een afzonderlijk meetobject, waarvan er telbare instanties zijn. Het onderscheid loopt volledig via het genoemde 'registratienummer', maar de onderbouwende conventie (referentsoort, populatie/naamruimte, toekenning en geldigheid) ontbreekt in het materiaal. Een genoemd nummer bewijst op zichzelf geen identiteit, dus de beslisgrond voor het onderscheid is niet aangeleverd.",
  "evidence": [
    {"location": "definition", "quote": "Meetobject herkenbaar aan zijn registratienummer."}
  ],
  "missing_information": "De conventie die de identificerende werking van het registratienummer onderbouwt: voor welke referentsoort en binnen welke populatie/naamruimte het wordt toegekend, door wie, en met welke geldigheid (uniciteit, hergebruik, voortbestaan).",
  "question": "Volgens welke conventie wordt het registratienummer toegekend (referentsoort, populatie/naamruimte, toekennende instantie en geldigheids-/uniciteitsvoorwaarden)?",
  "uncertainty": "Zonder toelichting is niet uit te sluiten dat het bovenbegrip 'meetobject' met begripsbepalende kenmerken zelf al een natuurlijke eenheidsgrens draagt; dat is uit de kern niet af te leiden."
}
```

**D07-register-zonder-conventie** (`47e77f0221c632aee347402f9d9de01459824d5d24bb269e25abc141a1d5ded8`)
```json
{
  "verdict": "insufficient_information",
  "applicability": "applicable",
  "unit": "een meetobject onderscheiden binnen register R",
  "reason": "De bedoelde eenheid is een telbaar meetobject en het onderscheid loopt via een 'blijvend uniek nummer' binnen register R. Het woord 'uniek' en de aanwezigheid van een nummer bewijzen op zichzelf geen identiteit; de onderbouwende conventie (referentsoort, populatie/naamruimte, toekenning en geldigheid van dat nummer binnen R) is niet aangeleverd. Zonder die conventie ontbreekt de beslisgrond voor de eenheidsgrens en continuïteit.",
  "evidence": [
    {"location": "definition", "quote": "Meetobject dat binnen register R door een blijvend uniek nummer wordt onderscheiden."}
  ],
  "missing_information": "De conventie die de identificerende werking van het 'blijvend uniek nummer' binnen register R onderbouwt: voor welke referentsoort en naamruimte/populatie het nummer geldt, hoe het wordt toegekend en wat de geldigheids-/continuïteitsvoorwaarden zijn.",
  "question": "Wat is de onderbouwde conventie van het blijvend uniek nummer in register R, dat wil zeggen voor welke referentsoort en naamruimte/populatie het geldt en hoe toekenning en blijvende geldigheid zijn geregeld?",
  "uncertainty": null
}
```

**D06a-register-met-conventie-expliciete-referent** (`204b6a9a89b0c2500d40741bdcb17404936a5004b20fbe79e49e5dc233f158be`)
```json
{
  "verdict": "pass",
  "applicability": "applicable",
  "unit": "de afzonderlijke, vast op één locatie geplaatste fysieke meetinstallatie in het veld",
  "reason": "De bedoelde eenheid is telbaar: één fysieke installatie is één meetobject, ook bij gelijk type of dezelfde eigenaar. Het onderscheidingsmiddel (blijvend uniek nummer in register R) is onderbouwd in de aangeleverde bron: R kent per installatie precies één nummer toe, dat nooit wordt hergebruikt en aan dezelfde installatie gebonden blijft. De continuïteit is geregeld: vervanging van onderdelen beëindigt het meetobject niet zolang het in R is opgenomen.",
  "evidence": [
    {"location": "toelichting", "quote": "Eenheid: één installatie is één meetobject; twee installaties zijn twee meetobjecten, ook bij hetzelfde type of dezelfde eigenaar."},
    {"location": "source:doc:synth-register-r", "quote": "Register R kent aan iedere meetinstallatie bij opname precies één nummer toe. Een nummer wordt nooit hergebruikt en blijft aan dezelfde installatie gebonden zolang zij in R is opgenomen, ook na vervanging van onderdelen."},
    {"location": "toelichting", "quote": "Vervanging van onderdelen beëindigt het meetobject niet zolang de installatie in register R is opgenomen."}
  ],
  "missing_information": null,
  "question": null,
  "uncertainty": null
}
```

## Bijlage B — actuele binding

- `prompt_version`: **`ess03-assess/2`**
- `system_prompt_sha256`: **`e51d06cb3c878d78f2a66135c248e5e8d2a4e95cc589a4fed816c411b125c758`** (fase 1: `722e6a2e516acf2574c04095924c6944c21271d37c5cd72e7c6f71ef3f223d6e`)
- `norm_sha256`: **`372bb329fa6630191cc13aaed20c715613043a4790ccb6a5dd9e01949e41e028`** (ongewijzigd; bron `src/toetsregels/regels/ESS-03.json`)
- `contract_version`: `ess03/1`; runtimecontract `2.1.0`
- provider/model (ModelRouter, taak `validation`): `anthropic` / `claude-opus-4-8`
- Hashes van alle 57 gewijzigde/nieuwe bestanden (21 gewijzigd t.o.v. fase 1, 13 nieuw in deze ronde, 23 ongewijzigd): `correction-manifest-v1.json › bestanden`.
