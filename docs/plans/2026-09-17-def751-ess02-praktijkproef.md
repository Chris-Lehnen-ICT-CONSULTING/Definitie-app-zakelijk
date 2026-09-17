# DEF-751 — ESS-02-praktijkproef in de echte generatie-/toetsketen

Datum: 17 september 2026. Werkboom `/private/tmp/DEF-751-ess02-praktijkproef-20260917`, branch `feature/DEF-751-ess02-praktijkproef`, basis `52fa87a1a8f16ffa1e6a2848d6d0c8ec13624123` (B2 + C3 stap 2 + reviewcorrecties, ongewijzigd behouden).
Uitvoerder: Claude Code CLI (sessie `8fc4b963-6072-4f30-a568-b952e41d45cf`). Review: aparte Codex CLI-sessie, door de coördinator georganiseerd.
Scope: ESS-02 inhoudelijk in de appketen (generatie + toetsing). Buiten scope: DEF-752, opslag/vaststelling/export/accountarchitectuur, skillproef S1–S9b (al gedaan), productie-DB.

Bewijsmap: `/tmp/ess02-20260916-cli-evidence/semantiek-20260917/` (nieuw; bestaand bewijs niet overschreven). Per run: `manifest.json` (source-SHA, sessie, model, parameters, seams), `modelaanroepen.json` (volledige messages, prompt-sha256/lengte, ruwe respons, tokens, SDK stop_reason/usage), `<casus>.prompt.txt`, `<casus>.respons.txt`, `<casus>.json` (contracttoetsen, parseruitkomst, ESS-02-uitkomst, DB-readback), `toetsing.json`, `samenvatting.md`, `runner.log`, `<casus>.db`.

## Wat er is gebouwd

- `scripts/testing/ess02_praktijkproef.py` — opt-in proefrunner. Standaard offline (bouwt de echte prompts, geen modelaanroep); `--live` doet sequentiële aanroepen via de echte, geconfigureerde keten: `PromptServiceV2` → `AIServiceV2(use_cache=False)` op `ModelRouter.from_config()` (`definition_core` → `claude-opus-4-8`, provider anthropic) → echte app-client (`create_ai_client`) → `services.modelantwoord`-parser → `DefinitionOrchestratorV2` → echte `ModularValidationService` (ESS-02 `judgment_review`) → verse SQLite. Parameters uit de normale app-instelling: `max_tokens=500`, `temperature=get_prompt_temperature('definition')=0.1`, timeout 30 s. Hard budget (`MAX_LIVE_CALLS=8`, ronde 2 `MAX_LIVE_CALLS_R2=5`) in een registrerende client-proxy die buiten de retry-lus stopt; API-key alleen via de runtime-loader (`--dotenv` → `load_project_dotenv`), nooit gelezen of geschreven; alle uitvoer wordt op sleutelpatronen gescrubd; DB-pad onder `data/` of een bestaand bestand wordt geweigerd. Vooraf vastgelegde verwachtingen staan in de runner en komen aantoonbaar niet in de prompt (`prompt_bevat_verwachting=false` per casus).
- **Bewust vervangen seams (afgebakende proef, geen claim over de hele productieflow):** `synonym_orchestrator=None`, `web_lookup_service=None`, `rag_service=None`, `voorbeelden.genereer_alle_voorbeelden_async → {}`, `source_assessment_service=None` (CON-02 AI-bronbeoordeling uit; CON-02 blijft "niet beschikbaar"), UI-handler/`ServiceAdapter` buiten de lus (documenten via dezelfde `context["documents"]`-route als de handler; die laag is gedekt door `tests/unit/ui/test_def751_verduidelijking_keten.py`). Prompt, model, parser, orchestrator-afhandeling, opschoning, validatie en opslag zijn echt.
- Runnertests: `tests/unit/scripts/test_ess02_praktijkproef.py` (8): hard budget buiten de retry-lus, afkapdetectie via SDK-metadata, scrub, DB-wacht, budgetpassendheid ronde 1/2, verwachting nooit in de echte prompt en bronnen wél, conflicttoetsen eisen gronden op bron 1/bron 2, activiteitsbron zonder verwachting/instructie.

## Casusselectie

Live (ronde 1, 8 aanroepen): E02-001 dossierstuk labelvrij (categorie None), E02-002 proces, E02-002 type, E02-004 proces, E02-003 resultaat, E02-009 exemplaar (register v1; `text` uit het register is de verwachting, niet de invoer), C3-CONFLICTBRONNEN + hergeneratie met verduidelijking. **C3-CONFLICTBRONNEN** komt letterlijk uit `tests/unit/services/prompts/test_def750_ess02_promptnorm.py::CONFLICTBRONNEN` (handboek.txt: activiteit; besluit.txt: uitsluitend de uitkomst) en staat niet in het register; E2-03 uit het register (type-label versus activiteitkern) is door het niveau/aard-overlapbesluit géén werkelijke tegenspraak en is bewust niet als conflict getoetst. Verduidelijking: "Bedoeld wordt de activiteit van het vastleggen; het vastgelegde resultaat is een afzonderlijk begrip." (synthetische bedoeling, geen bronfeit). Contexten synthetisch (`Meetdienst`, `Archiefdienst`).
Alleen-toetsen (geen modelaanroep, exacte invoertekst door de echte ESS-02-regel): E02-005, E02-006 (marker), E02-007 (label ≠ kern), E02-010 (overlap), E02-011 (leeg + marker), E02-013 (lage zekerheid), E2-16 (marker type).

## Ronde 1 — `live-run-1` (broncode = basis 52fa87a1a, ongewijzigd; 8 aanroepen; exit 1)

Technische contractchecks (geen inhoudelijk oordeel): "PASS" = alle contracttoetsen ok (succes/definitie/ESS-02 `review_required` zonder pass, violation of cijfer/opslag/geen afkapping); bij conflict: `error_type=betekenisconflict`, ≥ 2 lezingen op bron 1/bron 2, geen definitie, niets opgeslagen.

| casus | contract | uitkomst | ruwe modeltekst (letterlijk) | coördinatorobservatie (inhoudelijk) |
|---|---|---|---|---|
| E02-001 (None) | PASS | 1 call, `end_turn` | archiefstuk dat als afzonderlijk geïdentificeerd onderdeel van een dossier is opgenomen en samen met de overige stukken de behandeling van één zaak vastlegt | documentkern zonder marker; geen conflict geforceerd. Inhoudelijke passendheid: menselijk oordeel. |
| E02-002 proces | PASS | 1 call | proces waarbij een meetdienst meetwaarden met bijbehorende identificatiekenmerken formeel vastlegt in een register onder een uniek registratienummer | activiteitkern; "uniek registratienummer" komt niet uit de invoer (bijgedachte inhoud, aandachtspunt). |
| E02-002 type | PASS | 1 call | vastlegging van meetwaarden en bijbehorende identificerende gegevens in een register na afronding van een meting | **coördinator:** 'vastlegging' is ambigu (activiteit/uitkomst); zonder inhoudelijke activiteitgegevens in de invoer bewijst een labelwissel alleen geen betekenisbehoud. Contract-PASS is geen semantische PASS. |
| E02-004 proces | **BLOCKED (runner)** | 1 call verbruikt; `DuplicateDefinitionError` bij opslag | proces waarbij een meetdienst meetwaarden met bijbehorende identificerende kenmerken formeel vastlegt in een register onder een uniek registratienummer | duplicaatwacht van de app op dezelfde begrip/context/categorie als E02-002-proces in dezelfde proef-DB — fout in de proefopzet, niet in het product. Gecorrigeerd: per casus een eigen DB. |
| E02-003 resultaat | PASS | 1 call | vastgelegde meetgegevens die voortkomen uit het waarnemen en optekenen van meetwaarden, voorzien van een uniek registratienummer waarmee elke vastlegging afzonderlijk identificeerbaar is | uitkomstkern; ESS-02 review_required. |
| E02-009 exemplaar | PASS | 1 call | meting met identificatie M-17 die als afzonderlijk voorval het vastleggen van meetwaarden aan een bepaald meetobject door de meetdienst betreft | één voorval, procesaard behouden, geen verzonnen tijd/sensor; "meetobject" is generiek. |
| C3-CONFLICTBRONNEN | PASS | 1 call | `VERDUIDELIJKING NODIG:` + JSON: vraag "Duidt 'registratie' de activiteit van het vastleggen van meetwaarden aan, of de uitkomst daarvan …?"; lezing 1 op bron 1, lezing 2 op bron 2 | **coördinator bevestigd:** conflict correct herkend; bruikbare vraag; niets opgeslagen. |
| C3 + verduidelijking | **FAIL (functioneel)** | 1 call; parser `grond_niet_aangeleverd` → `modelantwoord_ongeldig` | `VERDUIDELIJKING NODIG:` + dezelfde vraag; lezing 1 met `"bron": "context: Bedoeld wordt de activiteit …"`, lezing 2 op bron 2 | **coördinator bevestigd:** het antwoord stond volledig als DATA in de prompt (`verduidelijking volledig als DATA-regel in de prompt: ok`), maar het model stelde dezelfde vraag opnieuw en voerde de verduidelijking als contextbron op. Parser weigerde terecht (geen versoepeling). |

Toetsroute (7 casussen, `toetsing.json`): alle `review_required`, `ESS-02` niet in `passed_rules`, geen violation, `overall_score=None`, invoerbytes ongewijzigd, geen teruggegeven afwijkende tekst (geen autoherstel), reden zonder positief oordeel; marker/label geven geen vrijstelling (E02-006/E02-011/E2-16). Dit bevestigt de DEF-750-grens in de echte service; het is geen inhoudelijk oordeel over de casussen.

Daarnaast door de coördinator in de echte prompt gevonden: bij een deverbaal begrip stond in de grammaticasectie "Focus op het resultaat of de staat" / "Vermijd procesbeschrijvingen" (`grammar_module.py`), rechtstreeks strijdig met ESS-02 (betekenislaag volgt bedoeling/context) en met een opgegeven categorie proces voor hetzelfde begrip.

## Gerichte productcorrectie (coördinatorbesluit 17-09-2026; diff 3 bestanden, +44/−9)

1. `src/services/prompts/modules/grammar_module.py` — deverbaalregel schrijft geen betekenislaag meer voor op grond van de woordvorm: "kan de activiteit, haar uitkomst of één bepaald voorval aanduiden; de woordvorm bepaalt dat niet; volg de bedoelde betekenislaag uit context, bronnen, categorie en een eventuele verduidelijking (ESS-02)"; voorbeelden tonen beide lagen als toegestaan en vermenging als fout. Werkwoord- en overig-regels ongewijzigd.
2. `src/services/prompts/modules/definition_task_module.py` (`_build_conflictcontract`) — de tegenspraak die de verduidelijking beslist "is daarmee opgelost, ook al blijven de bronnen het oneens: meld haar niet opnieuw en voer de verduidelijking nooit op als bron of contextwaarde van een lezing"; een werkelijke, ándere tegenspraak mag nog wel worden gemeld.
3. `src/services/prompts/modules/ess02_aanwijzing.py` — één additieve bijzin: "de daarmee besliste tegenspraak wordt niet opnieuw gemeld" (op beide ESS-02-plaatsen, tellingen `kies niet stil` ×2 enz. ongewijzigd).

Geen parser-, validator- of orchestratorwijziging; geen vaste modelantwoorden; bronnen worden niet herschreven. ESS-01 (`hoogstens een herkenbaar voorlopig voorstel`), CON-02-instructie en DEF-750-tellingen blijven staan (bewaakt in de nieuwe test). RED/GREEN: `tests/unit/services/prompts/test_def751_praktijkproef_correcties.py` — `correcties-red.log` (5 failed, 1 passed op de basiscode), `correcties-green.log` (6 passed).

## Ronde 2 — `live-run-2` (broncode = basis + ongecommitte productdiff `productdiff-voor-ronde2.patch`, git-hash `cdba0bf704da479943275c028725ebc0618e87b8`; 4 van max 5 aanroepen; exit 0)

| casus | contract | uitkomst | ruwe modeltekst (letterlijk) | observatie |
|---|---|---|---|---|
| C3-CONFLICTBRONNEN | PASS | 1 call | `VERDUIDELIJKING NODIG:` + vraag "Duidt 'registratie' hier de activiteit van het vastleggen aan of de uitkomst daarvan (de vastgelegde meetwaarden)?"; lezingen op bron 1 en bron 2 | conflict opnieuw herkend; niets opgeslagen (recordtelling ongewijzigd). |
| C3 + verduidelijking | PASS | 1 call; parser `definitie`; `betekenisverduidelijking_gebruikt=true`; opgeslagen (id in `C3-CONFLICTBRONNEN.db`), registratie op het record bevat verduidelijking én prompt met de datalijn | activiteit waarbij meetwaarden onder een identificerend registratienummer in het register worden vastgelegd | gekozen betekenis (activiteit) behouden; resultaat niet als tweede kern; bronnen ongewijzigd in de prompt; geen nieuw conflict. "identificerend registratienummer" staat niet in bronnen of verduidelijking (bijgedachte inhoud; ESS-02 blijft `review_required`, inhoudelijk menselijk oordeel). |
| E02-004-r2 proces + werkinstructie.txt | PASS | 1 call | activiteit waarbij een medewerker meetwaarden van een sensor afleest, het meetnummer controleert en de waarden vervolgens in een register vastlegt | activiteitkern uit de inhoudelijke bron; het register wordt als gerelateerd object genoemd, geen tweede kern; geen afkeur (review_required, geen signaal). |
| E02-002-type-r2 type + dezelfde bron | PASS | 1 call | vastlegging waarbij afgelezen meetwaarden na controle van het bijbehorende meetnummer in een register worden opgenomen | **resterend inhoudelijk gat:** met identieke grond kiest het model bij label type opnieuw het ambigue 'vastlegging' als kern, terwijl bij proces 'activiteit' wordt gekozen. De differentia beschrijft de handeling; het genus laat de laag open. Contract-PASS, geen semantische PASS; menselijk oordeel vereist. |

Toetsroute ronde 2: identiek aan ronde 1 (7× PASS).

## Acceptatie (eerlijk)

- Echte tegenspraak → bruikbare vraag, geen schijndefinitie, niets opgeslagen: **bevestigd in beide rondes** (ruwe uitvoer hierboven).
- Antwoord bereikt de nieuwe prompt volledig en het resultaat behoudt de gekozen betekenis: ronde 1 **FAIL** (model bevraagt opnieuw), na correctie ronde 2 **PASS op contract én — voor deze ene uitvoer — inhoudelijk consistent met de keuze**; één modelantwoord op temperature 0.1 is geen bewijs van stabiel modelgedrag.
- Overlap en labelvrije heldere betekenis geven geen geforceerd conflict: bevestigd (E02-001 None, E02-002 type, E02-003, E02-009: geen sentinel). Inhoudelijke kwaliteit van die zinnen is niet beoordeeld als "voldoet".
- Geen nieuwe bron of fictieve samensmelting in de conflictroute: bevestigd (gronden uitsluitend bron 1/bron 2). Wel voegt het model in gewone definities inhoud toe die niet uit invoer/bronnen komt ("uniek registratienummer", "identificerend registratienummer") — ESS-02-neutraal maar relevant voor CON-/ESS-05-beoordeling.
- ESS-01-genus/differentia- en CON-normen intact: promptnorm-tests groen; niet opnieuw live beoordeeld.

## Resterende gaten

1. Type-label + activiteitbron levert 'vastlegging' als kern (ronde 1 én 2); de deverbaalcorrectie lost dat niet op. Geen verdere prompttuning zonder coördinatorbesluit.
2. De werkwoordregel in `grammar_module.py` ("Definieer als handeling of proces") is nog vormgedreven; buiten de toegestane correctie gelaten.
3. Modelgedrag is met 1 antwoord per casus gemeten (temperature 0.1, geen herhaling); geen kwaliteitspercentage of goldset-claim.
4. CON-02 AI-bronbeoordeling, voorbeelden, synoniemen, web lookup, RAG en de UI-handler zijn in deze proef niet meegelopen (seams).
5. E02-004 uit ronde 1 heeft wél een ruw modelantwoord maar geen validatie-/opslaguitkomst (runnerfout); ronde 2 (E02-004-r2, met bron) vervangt die meting niet één-op-één (andere invoer).

## Tests en gates (logs in de bewijsmap)

`runner-tests-run1/2/3.log` (7→8 passed), `correcties-red.log` / `correcties-green.log`, `regressies-gericht.log` (prompts, validatie, orchestrators, handlers, keten, DEF-154, modelantwoord, runner: 1992 tests — 1986 passed, 5 skipped, 1 xfailed; exit 0), `make-test.log` (`make test PY=…venv/bin/python`: 6353 passed, 75 skipped, 1 xfailed; exit 0), `make-lint.log` (exit 0), `ruff-run1.log` (eerste ronde met 3 bevindingen, daarna schoon; `make lint` dekt `scripts/` en `tests/` niet — apart gelint). Offline smokes: `offline-smoke-1..4`, `offline-ronde2-smoke` (exit 0; smoke-1 exit 1 = vervolgcasus onterecht BLOCKED in offline-modus, gefixt).
