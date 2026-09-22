# DEF-766 ESS-03 AI-beoordeling — correctieverslag ronde 2 (v2)

**Uitvoerder:** Claude Code CLI (Opus 5) · **werkboom** `/Users/chrislehnen/.codex/worktrees/2075/Definitie-app` · **branch** `feature/DEF-766-ess03-ai-beoordeling` · **base** `2c9a6e3a13afa4ecbe39163cc418e2b0f8c41644` · HEAD ongewijzigd; geen commits/push/PR/deletes; geen dependencies, schemawijzigingen of live-skillactivering.
**Invoer:** `correction-report-v1.md`/`correction-manifest-v1.json`, `browser-verification-v2.md`, `browser-v2-input-and-source-seal.json`, `browser-v2-pass-saved.json`, `browser-v2-cleared-saved.json`, `browser-v2-clarification-input.md`, `browser-app-v2-start2.log` (regels 96–105). Onafhankelijke eindset niet gelezen.
**Bijlagen:** `correction-manifest-v2.json` (61 bestanden met sha256, waarvan 13 in ronde 2 gewijzigd/nieuw; vergelijking met manifest v1 en met de browser-v2-seal), `exitcodes-correctie-v2.json`, alle `c2-*.log`, `c2-c-transportproef.json`. Eerdere rapporten/logs/manifests onaangeroerd. **Geen nieuwe echte modelcalls**; prompt `ess03-assess/2` (systeemprompt-hash `e51d06cb…b125c758`), norm `372bb329…41e028` en de 8/8-ontwikkelrun v2 zijn ongewijzigd behouden (manifest: `ongewijzigd_t_o_v_correctie_v1: true`).

Eindstand: alle DEF-766-suites 313 passed; gerelateerde regressies 1053 passed; `make test` 6870 passed (exit 0); `make lint` 0; complexity-ratchet 200 < baseline 201; markers/root-allowlist/TODO 0.

---

## A — R1/R5: het normale editor-validatieresultaat volgt de huidige formulier-/recordbinding — **gefixt**

**Oorzaak.** Het bovenste resultatenblok toont `edit_last_validation` (sessiestate, het resultaat van de laatste "Valideren") ongewijzigd: het was niet aan het record gebonden, werd niet gewist bij Annuleren of bij het openen van een (ander) record, en werd bij opslaan niet vervangen (de edit-service valideert alleen sync; de app-orchestrator is async → `result["validation"]` is None). De aparte replaysectie herbond wél aan de huidige kandidaat; het normale blok niet. Precies het browserbeeld van stap 5.

**Fix (shared layer first).**
- Servicelaag `src/services/definition_edit_service.py:251` `herbind_ess03_in_validatieresultaat(resultaat, kandidaat, *, binding)`: pure replay van de ESS-03-beoordeling uit het resultaat (`ess03_assessment`) via het contract tegen de kandidaat zoals die nú in het formulier staat (term, tekst, drie contextlijsten, toelichting/categorie/betekenisverduidelijking/ESS-03-verduidelijking, bronset) én de actuele prompt/norm/provider/model. Klopt de binding → hetzelfde object; anders een kopie waarin ESS-03 consistent open/historisch is in `rule_results`, `rule_statuses`, `passed_rules`, `violations`, `review_required` en `evaluation_coverage` (+ `ess03_rebound`-marker). Het origineel wordt niet gemuteerd en de beoordeling blijft erin: dezelfde verduidelijking terugzetten maakt haar weer actueel (geen blinde invalidatie, geen hertoets/netwerkcall). `ess03_uitkomst_van_definition(..., assessment=)` (`:205`) accepteert daarvoor een expliciet document.
- UI-adapter `src/ui/components/definition_edit_tab.py`: `_kandidaat_uit_formulier` (`:1270`, gedeeld door de replaysectie en het normale blok; widgetwaarden, anders de geladen waarde, incl. de recordverduidelijking), `_actueel_sessieresultaat` (`:2409`: alleen het resultaat van het record dat nu bewerkt wordt — `editing_definition_id` reist mee vanuit `_validate_definition` (`:2362`) — en herbonden vóór weergave), `_render_fullwidth_validation_results` (`:2388`). State-hygiëne: `_cancel_edit` wist `edit_last_validation`; `_start_edit_session` (`:2005`) begint zonder oud resultaat.

**Bewijs.**
- RED (echte state-route: echte `ValidationOrchestratorV2` + `ModularValidationService` + fake ESS-03-dienst → `normaliseer_validatieresultaat` → `edit_last_validation`; mocked `st`): `tests/unit/ui/test_def766_ess03_editor_herbinding.py` — `c2-a-red.log` exit 1: na wissen van de verduidelijking toont het blok nog `**ESS-03** · ✅ Voldoet`; een ander record toont het oude resultaat.
- GREEN: `::test_normaal_validatieresultaat_volgt_de_huidige_binding` — uitgangspunt actuele pass; (1) wissen zónder opslaan → geen actuele pass, "historisch … pass" zichtbaar, dekking `voldoet` −1, ESS-03 niet meer onder geslaagde regels; (1b) dezelfde verduidelijking terugzetten → weer actuele pass; (1c) tekstwijziging zonder opslaan → geen actuele pass; (2) wissen én opslaan (record `""`, geen hertoets) → geen actuele pass, historisch; (3) Annuleren → `edit_last_validation` None; heropenen → geen ESS-03-blok. `::test_openen_van_een_ander_record_toont_geen_oud_resultaat`. Servicelaag: `tests/unit/services/test_def766_ess03_herbinding_service.py` (zelfde object bij gelijke binding; geparametriseerd verduidelijking-gewist/tekst-gewijzigd/ander-model/geen-binding → consistent historisch; fail → geen violation bij afwijking en weer een niet-blokkerende violation bij terugkeer; kaal resultaat ongemoeid). Logs: `c2-a-green.log`, `c2-a-green2.log` (9 passed), `c2-a-suites.log` (126 passed incl. editor-regressies DEF-743/751/808/622), `c2-eind-a-herbinding.log` exit 0.
- Historische weergave blijft: het label/deel meldt "De eerdere AI-beoordeling (eerder oordeel: pass) is historisch en geldt niet als actueel oordeel: …" — geen actuele geldige pass.

**Dispositie:** fix nu — uitgevoerd. **Browsercontrole (coördinator):** stap 5 van v2 herhalen; verwacht bovenaan geen "Voldoet" voor ESS-03 na wissen (met en zonder opslaan), wél historisch; na Annuleren/heropenen geen oud blok; verduidelijking terugzetten → pass weer actueel zonder modelcall.

## B — R6: totale tijdbegrenzing inclusief nabewerking — **gefixt, met eerlijke grens**

**Wat er mis was.** De vorige test bewees alleen detectie achteraf (FakeAI met `time.sleep`, assert `elapsed ≥ 0,3`). `asyncio.timeout` kan een synchroon blok in de eventloop-thread niet onderbreken.

**Fix (beperkt opt-in).** `AIServiceV2.generate_definition(..., offload_postprocessing=False)` (`src/services/ai_service_v2.py:167`) en `_nabewerking` (`:377`): met de opt-in draaien de nabewerkingsstappen ná het providerantwoord — tokenraming en cache-write — via `asyncio.to_thread`, zodat zij voor de aanroeper een await-punt zijn dat `asyncio.timeout` daadwerkelijk kan onderbreken; raming vóór cache-write, zodat een onderbreking niets cachet. Zonder opt-in exact het bestaande inline gedrag (bewezen: `test_zonder_opt_in_blijft_de_nabewerking_van_generate_definition_inline`, thread-identiteit). `Ess03AssessmentService` zet de opt-in (`ess03_assessment_service.py:552`).

**Wat technisch afdwingbaar is — en wat niet.** Afdwingbaar op elk await-punt: het transport (verbinden/verzenden/lezen), rate limiter, retry-wachttijden en — met de opt-in — de nabewerking van de AI-laag. Bij het verstrijken annuleert `asyncio.timeout` de wachtende taak: de lopende HTTP-aanroep wordt afgebroken (httpx sluit de request bij `CancelledError`); een al gestarte werkthread loopt uit tot zij klaar is (Python kan een thread niet stoppen), maar haar resultaat wordt nooit gebruikt, gecachet of beoordeeld; de dienst geeft direct `status: error/timeout` zonder `judgment`. **Niet** afdwingbaar door asyncio: synchrone CPU-segmenten in de eventloop-thread zelf (JSON-parse van de SDK-respons, ESS-03-parse/validatie — microseconden); daarvoor blijft de meting achteraf het vangnet (een te laat antwoord is een timeout zonder oordeel en zonder cache) — dat is detectie, geen begrenzing, en zo staat het nu ook in de docstrings (`ess03_assessment_service.py` module-docstring R6-alinea, `_beoordeel_met_model`, `_beoordeel_antwoord`). Geen harde-deadlineclaim voor die segmenten.

**Bewijs.**
- RED: `tests/unit/validation/test_def766_ess03_correcties_service.py::test_vertraagde_nabewerking_op_de_echte_route_komt_binnen_de_deadline_terug` — echte `AIServiceV2` + echte `AsyncGPTClient` met fake provider (direct geldig antwoord) en de **productie-nabewerking** `AIServiceV2._estimate_tokens` gemonkeypatcht op 0,6 s blokkeren; deadline 0,2 s → `c2-b-red.log` exit 1: "kwam pas na 0,613 s terug".
- GREEN: terugkeer < 0,45 s (5× herhaald, stabiel), `status=error/timeout`, `judgment=None`, `service._cache == {}`, één providercall; het te late antwoord landt nergens: na de uitloopwacht gaat een volgende aanroep opnieuw naar de provider (2 calls) en is `assessed`. Vangnettest hernoemd en herdocumenteerd als detectie: `::test_vangnet_een_te_laat_teruggekeerd_antwoord_is_timeout_zonder_oordeel`. Logs: `c2-b-green.log` (123 passed incl. fase-1-dienst-, opt-in- en AI-laagtests), `c2-eind-b-deadline.log` (43 passed).

**Dispositie:** fix nu — uitgevoerd. Geen generiek framework, geen nieuwe afhankelijkheden (`asyncio.to_thread` is stdlib).

## C — verbindingsfout call 2 (12:12:48.999): oorzaak **bewezen** en gefixt, zonder retries

**Onderzoek.** Browserlog: call 1 HTTP 200 (12:11:17.899), call 2 om 12:12:48.999 `Anthropic connection error` **1 ms** na "ModelRouter initialized", zonder httpx-requestregel ("HTTP Request: POST …" ontbreekt), `API call failed after 1 attempts`; herkansing 12:13:40 200. Hypothese: loopaffiniteit van het httpx-verbindingspool in de gedeelde `AsyncAnthropic`-client (containersingleton `container.py:_get_ai_client`) over de per aanroep nieuwe `asyncio.run()`-loop van `ui.helpers.async_bridge.run_async`.

**Deterministische transportproef met de echte stack** (`scripts/ess03/proef_eventloop_transport.py` — echte `anthropic.AsyncAnthropic`/httpx-pool tegen een lokale fake `/v1/messages` op loopback met keep-alive; geen netwerk, geen sleutel, geen betaalde call; buiten pytest omdat de DEF-519-gate ook loopback-sockets blokkeert): `c2-c-transportproef.json`/`.log`, exit 0, alle drie conform —
1. kale `AsyncAnthropic(max_retries=0)` over 3 loops: loop 1 ok, **loop 2 `APIConnectionError: Connection error.` ← `RuntimeError: Event loop is closed`**, loop 3 ok (pool geschoond na de fout) — exact het browserpatroon;
2. echte keten `AnthropicClient(rebind_on_new_loop=False)` → `AIServiceV2` → `Ess03AssessmentService` via `run_async`: aanroep 2 `error/connection` na 0,002 s, `attempts_observed=1`;
3. dezelfde keten met de correctie: 3× `assessed`, `attempts_observed=1`, `retries_observed=0`, server ontvangt 3 requests.

Conclusie: geen toevallige netwerkfout maar reproduceerbaar hergebruik van een aan een gesloten eventloop gebonden keep-alive-verbinding. Dit verklaart ook de in fase 1 waargenomen SDK-retry (10:44:44.986): met SDK-default `max_retries=2` werd dezelfde fout stil herkanst; de R6-opt-in `max_retries=0` maakte haar zichtbaar.

**Fix (beperkt, geen retries).** `src/services/ai/base_client.py:47` `Eventloopwacht` (zwakke referentie naar de loop van het vorige gebruik) en `:29` `foutketen` (geredigeerde oorzaakketen). `AnthropicClient(rebind_on_new_loop=True)` (`anthropic_client.py:53`) en `_sdk_voor_deze_loop` (`:77`): draait er een andere loop dan bij het vorige gebruik, dan één verse SDK-client (nieuw pool) met dezelfde opties; binnen dezelfde loop blijft dezelfde client. De oude client wordt losgelaten (sluiten op een gesloten loop kan niet; sockets sluiten met de GC). Dezelfde wacht in `OpenAIClient` (`openai_client.py:45,64`) voor pariteit van de providerabstractie. De connection-errorlog draagt nu de oorzaakketen (`APIConnectionError: … ← RuntimeError: Event loop is closed`), met sleutelredactie. Geen SDK- of eigen retries aangezet; `attempts_observed` blijft 1.
Kanttekening scope: de fix zit in de gedeelde providerclient (daar zit het defect), niet in een ESS-03-route-opt-in — de vlag `rebind_on_new_loop` maakt het gedrag uitschakelbaar en toetsbaar; andere appfuncties verliezen alleen een verborgen fout+retry.

**Bewijs.** Pytest op de SDK-grens (`tests/unit/services/test_def766_ess03_eventloop_transport.py`, fake SDK die zich aan de loop van het eerste gebruik bindt, achter de echte `AnthropicClient → AIServiceV2 → Ess03AssessmentService` via `run_async`): zonder correctie faalt aanroep 2 (`error/connection`, 1 poging); met correctie 3× `assessed` zonder retries, 3 constructies (opstart + 2 nieuwe loops) met identieke opties; binnen één loop geen nieuwe client; oorzaakketen gelogd zonder geheim; `Eventloopwacht`-gedrag; OpenAI-pariteit — `c2-c-green.log` 80 passed (incl. bestaande AI-clienttests), `c2-eind-c-eventloop.log` 6 passed. Eerste pytest-poging met loopback-server: `c2-c-red.log` (OfflineGateError → daarom het script voor de echte stack).

**Resterende onzekerheid.** De browsersessie zelf is niet opnieuw gedraaid (geen budget); de bewezen oorzaak reproduceert het waargenomen patroon exact (immediate fout, geen requestlog, herkansing ok), maar dat de call van 12:12:48 déze oorzaak had en geen andere (bv. een door de server gesloten keep-alive na 91 s idle — dat zou een `RemoteProtocolError`/`ConnectError`-oorzaak geven en ook onder `max_retries=0` zichtbaar zijn) is niet uit de UI-log af te leiden: die logde de oorzaak niet. Met `foutketen` staat de oorzaak vanaf nu wél in het log. Beide varianten worden door de fix (vers pool per loop) grotendeels afgedekt; een échte server-side keep-alive-sluiting blijft een technische fout zonder retry — dat is conform de R6-afspraak en wordt als zodanig getoond.

**Dispositie:** fix nu — uitgevoerd (oorzaak bewezen op transportniveau; UI-incident niet opnieuw gedraaid).

## Regressies, lint en ratchets op de eindcode

| Gate | Log | Exit | Resultaat |
|---|---|---|---|
| `make test` (unitgate) | `c2-make-test-2.log` | 0 | 6870 passed, 75 skipped, 722 deselected, 1 xfailed (292,4 s); run_profile ok |
| `make lint` | `c2-make-lint.log` | 0 | schoon |
| ruff/black op alle 55 gewijzigde/nieuwe .py | `c2-ruff-alle.log`, `c2-black-alle.log` | 0 | schoon |
| `make complexity-check` | `c2-complexity.log` | 0 | 200 < baseline 201 (baseline niet aangepast) |
| `make test-markers-check` | `c2-markers.log` | 0 | 488 testbestanden |
| root-allowlist / TODO-markers | `c2-root-allowlist.log`, `c2-todo.log` | 0 | schoon |
| Alle DEF-766-suites + golden ESS | `c2-eind-def766-alle.log` | 0 | 313 passed |
| Gerelateerde regressies (DEF-743/751/622/624/808 editor, orchestrator, story 2.4, AI-clients/AIServiceV2/routing, classifier, database, async-bridge) | `c2-eind-regressie.log` | 0 | 1053 passed |

Tussenstand eerlijk gemeld: `make test` run 1 (`c2-make-test.log`, exit 2) faalde op één test die de client via `__new__` construeert (loopwacht-attribuut ontbrak); die test zet nu `_rebind_on_new_loop=False`; run 2 groen. Betekenis-/opslag- en andere-regelregressies zijn in de suites hierboven meegedraaid (categoriekeuze, CON-01/CON-02, bronbewijs, DUP, vaststelconflict, export-readback).

## Budget

26 conservatieve transportpogingen na browserfase 2; **0 nieuwe echte modelcalls in deze ronde** (alle proeven deterministisch: fake provider, fake SDK, lokale fake server). Met 30 geplande eindtests blijft de som 56 (4 ruimte).

## Buiten scope / genoteerd

- `definitie_drafts` (auto-save) ongewijzigd — geen ESS-03-opdracht. Lokale synthetische browsertestdatabase niet aangeraakt (tests gebruiken `tmp_path`).
- Het eigen TXT-testartefact in `exports/` blijft staan (geen delete-route).
- **Herstart vereist** van de draaiende Streamlit-instantie(s) uit deze werkboom (8544; eventueel 8543) vóór de laatste browsercontrole: `anthropic_client.py`, `ai_service_v2.py`, `definition_edit_service.py`, `ess03_assessment_service.py` en `definition_edit_tab.py` zijn t.o.v. de browser-v2-seal gewijzigd (manifest: `gelijk_aan_browser_v2_seal: false`; `definitie_crud.py`, `contract.py`, `validation_orchestrator_v2.py`, `validation_view.py`, `async_api.py` ongewijzigd t.o.v. de seal).
- Nieuw script `scripts/ess03/proef_eventloop_transport.py` (loopback, geen netwerk) is bewust geen pytest: de unitgate blokkeert loopback-sockets; aanpassen van die gate is een beleidsbesluit dat ik niet heb genomen.
