# DEF-766 / ESS-03 — kleine echte generatieproef (modelproef) · rapport v1

18 september 2026, 17:50 CEST · Claude Code CLI-uitvoerder · werkboom `/Users/chrislehnen/.codex/worktrees/2075/Definitie-app` (branch `bugfix/DEF-766-ess03-telbaarheid`, gestagede ESS-03-fix incl. ISC004-correctie). **Verificatie, geen implementatie:** geen repositorybron, test, configuratie, database of skill gewijzigd; alleen tijdelijke artefacten onder `/tmp/def766-cli/`.

## Beperkte claim (vooraf)

Steekproef van **vier** echte generaties, één aanroep per case, temperatuur 0,1. Dit bewijst dat de huidige ESS-03-regelkaart en G-instructie de echte prompt bereiken en dat het geconfigureerde model op deze vier synthetische invoeren geen identifierplicht toevoegt, de bedoelde betekenis behoudt en een stof niet tot monster maakt. Het bewijst **niet**: een voltooide menselijke ESS-03-beoordeling of opslag daarvan (contractlacune DEF-624, zie `contract-gap-v1.md`), statistische modelkwaliteit, eerste-pogingkwaliteit in het algemeen, of UX-acceptatie. Verwachte grenzen zijn afgeleid uit tekstvoorstellen-v3/casusregister-v4 en vooraf in het script vastgelegd; er zijn geen gouden expertlabels gebruikt. Het model kan het ✅-voorbeeld van de regelkaart en de meegegeven verduidelijking hebben geëchood (zie kanttekeningen).

## Opzet (echte keten, gespiegeld aan de orchestrator)

| Onderdeel | Waarde | Bron |
|---|---|---|
| Prompt | échte `PromptServiceV2().build_generation_prompt(request)`; `GenerationRequest` met `begrip`, `ontologische_categorie="type"`, synthetische `organisatorische_context`, en de bedoelde betekenis via het bestaande typed veld `betekenisverduidelijking` (rendert als DATA-regel "Verduidelijking van de bedoelde betekenislaag door de gebruiker: …" in het contextblok; DEF-751) | `prompt_service_v2.py:414-425`, `context_awareness_module.py:39-68` |
| Model | échte `AIServiceV2` op `create_ai_client(provider, api_key)` + `ModelRouter.from_config()`; geen modeloverride → `definition_core` = **`claude-opus-4-8`** (provider `anthropic`), exact zoals `ServiceContainer.ai_service()` | `container.py:266-289`, `model_router.py:104-116` |
| Parameters | `temperature = get_prompt_temperature("definition")` = **0,1**; `max_tokens = 500` (orchestrator-default, ≤ 600); `timeout_seconds = 60` | `definition_orchestrator_v2.py:1001-1018` |
| Retries/cache | client-lus `RateLimitConfig(max_retries=1)` = één poging; SDK via bestaande env-override `AI_SDK_MAX_RETRIES=0`, `AI_CLIENT_TIMEOUT=60` (DEF-566); `use_cache=False` → `cached=False` op alle vier | `async_api.py:211`, `services/ai/__init__.py:54-55` |
| Bronnen | geen web-lookup, RAG of documenten (`source_receipt.status = "none"`, `web.enabled=false`); geen zelfbedachte externe bronnen | `modelproef-v1.json` |
| Credentials | project-`.env` geladen via `load_project_dotenv(pad=…)` (override=False); alleen `api_key_aanwezig: true` vastgelegd; geen key, geen env in uitvoer (grep op `sk-` over alle artefacten: 0 treffers) | `dotenv_loader.py` |
| Isolatie | CWD = `/tmp/def766-cli/modelproef-werkmap` (runtime-artefacten `cache/api_metrics.json`, regel-FileCache, `logs/`, `exports/` landen daar); `git status` van de werkboom ongewijzigd; niets opgeslagen in een database | — |
| Toetsing | de geëxtraheerde kandidaat (`extract_definition_from_gpt_response`, byte-gelijk aan de ruwe tekst) daarna offline door de échte `ModularValidationService` (ToetsregelManager) — géén extra modelcall | — |

Droge run vooraf (`MODELPROEF_DRY=1`, geen modelaanroep): alle vier prompts 29.465–29.505 tekens, ESS-03-kaart exact 1×, G-kern ("verzin geen nummer, bron of telconventie") aanwezig, oude nummerinstructie afwezig, verduidelijking aanwezig, **PII-scan 0 treffers** (e-mail/telefoon/BSN-patroon/gebruikersnaam/`/Users/`-pad). Prompt-hashes van droge en echte run identiek (deterministische prompt, DEF-581).

Artefacten: `modelproef-v1.py` (script), `modelproef-v1.json` (volledig verslag), `modelproef-prompt-<case>.txt` (uitgaande prompts), `modelproef-dry-run.log`, `modelproef-run.log` (exit 0).

## Resultaten per case

Alle vier: `status=definitie` (geen conflictmelding/sentinel), `model=claude-opus-4-8`, `cached=false`, `retry_count=0`, geen technische fout. Tokens zijn de **schatting van de service** (tiktoken-fallback op prompt+antwoord, ~7.250 per call), niet de providertelling.

### MP-01 · eiland (natuurlijke grens op peilmoment, geen identifier)

- Invoer: begrip `eiland`, categorie type, context "Synthetische waterbeheerder", verduidelijking: "Bedoeld is het natuurlijke object: een afzonderlijk aaneengesloten stuk land dat op het afgesproken peilmoment volledig door water is omgeven."
- Prompt SHA256 `e9a65c4d82d4…` (29.505 tekens). Duur 2,8 s.
- Kandidaat: **"aaneengesloten stuk land dat op het afgesproken peilmoment volledig door water is omgeven"**
- Analyse tegen de vooraf vastgelegde grenzen:
  - Identifierplicht: **geen** — geen nummer, code, register of registratieplicht toegevoegd (identifier-signaalwoorden: geen).
  - Betekenisbehoud: **ja** — natuurlijke eenheidsgrens (aaneengesloten, door water omgeven, peilmoment); geen vernauwing tot geregistreerde eilanden. "Afzonderlijk" uit de verduidelijking is niet letterlijk overgenomen; "aaneengesloten stuk land" draagt dezelfde individuatie.
  - Stof→monster: n.v.t.
- Kanttekening: de kandidaat ligt zeer dicht bij het ✅-voorbeeld van de ESS-03-regelkaart en bij de verduidelijking; dit is dus vooral bewijs dat de G-instructie/het voorbeeld doorkomt, niet van zelfstandige afbakeningskwaliteit.
- Toetsing kandidaat: ESS-03 `review_required`, geen violation, geen signalen, `overall_score None`. (Andere regels: ESS-05, VER-01, VER-03 gefaald — buiten ESS-03-scope; niet geanalyseerd.)

### MP-02 · water als stof (expliciet geen monster)

- Invoer: begrip `water`, type, "Synthetisch laboratorium", verduidelijking: "Bedoeld is water als stof (de vloeistof zelf), uitdrukkelijk niet een monster, partij of afgemeten hoeveelheid."
- Prompt SHA256 `377965ca19c4…`. Duur 2,5 s.
- Kandidaat: **"chemische verbinding die bestaat uit moleculen met twee waterstofatomen en één zuurstofatoom en die bij standaarddruk tussen 0 en 100 graden Celsius in vloeibare toestand verkeert"**
- Analyse:
  - Identifierplicht: **geen**.
  - Stof→monster-verschuiving: **geen** — geen monster, portie, partij, hoeveelheid, registratie (monster-signaalwoorden: geen); de stoflezing is behouden ("chemische verbinding … in vloeibare toestand").
  - Betekenisbehoud: **ja** (stof; de "vloeistof zelf" is als toestandsvoorwaarde opgenomen). De chemische/fysische juistheid van de toestandsgrenzen is niet beoordeeld (geen expertlabel; buiten ESS-03).
- Toetsing kandidaat: ESS-03 `review_required`, geen violation, geen signalen. Inhoudelijk hoort hier de menselijke uitspraak "niet van toepassing (stoflezing)" — precies wat de keten nu nog niet kan vastleggen (contract-gap §2). (Andere regels: CON-CIRC-001 vuurt op "waterstofatomen" — circulariteitsheuristiek op substring; ESS-05, ESS-CONT-001, INT-01, VER-01 — buiten scope.)

### MP-03 · watermonster (afzonderlijk afgenomen hoeveelheid uit één bemonstering)

- Invoer: begrip `watermonster`, type, "Synthetisch laboratorium", verduidelijking: "Bedoeld is de afzonderlijk afgenomen hoeveelheid water uit één bemonstering, als op zichzelf staande eenheid."
- Prompt SHA256 `d1ac038df09a…`. Duur 2,4 s.
- Kandidaat: **"hoeveelheid water die bij één bemonstering is afgenomen en als op zichzelf staande eenheid wordt behandeld voor onderzoek"**
- Analyse:
  - Identifierplicht: **geen** — geen monsternummer, label, barcode of registratie als noodzakelijk kenmerk.
  - Eenheidsgrens: via bovenbegrip + kenmerk ("hoeveelheid water … bij één bemonstering afgenomen"): één bemonsteringshandeling → één eenheid, zoals de verwachting (N16-lijn). De continuïteitsconventie (wat na overhevelen of splitsen één monster blijft) is niet gegeven en niet verzonnen; blijft terecht open.
  - Betekenisbehoud: **ja** — niet terug naar de stof (MP-02) en niet naar de handeling zelf. "als op zichzelf staande eenheid wordt behandeld" echoot de verduidelijking; "voor onderzoek" voegt een doelbepaling toe (ESS-01-terrein, niet ESS-03).
- Toetsing kandidaat: ESS-03 `review_required`, geen violation, geen signalen. (Andere regels: ESS-05, INT-01, VER-01 — buiten scope.)

### MP-04 · fysiek boekexemplaar (ISBN gedeeld door meerdere exemplaren)

- Invoer: begrip `boekexemplaar`, type, "Synthetische bibliotheek", verduidelijking: "Bedoeld is het fysieke exemplaar van een boek; het ISBN is gedeeld door alle exemplaren van dezelfde uitgave."
- Prompt SHA256 `ce18d55ebdfb…`. Duur 3,3 s.
- Kandidaat: **"fysiek exemplaar van een gedrukte of anderszins vervaardigde uitgave, dat als één afzonderlijk stuk van andere exemplaren van dezelfde uitgave wordt onderscheiden door zijn eigen materiële verschijning en plaatsing"**
- Analyse:
  - Identifierplicht: **geen** — het ISBN wordt niet als onderscheidend criterium gebruikt (het ❌-voorbeeld is vermeden); geen verzonnen exemplaarnummer of barcode.
  - Betekenisbehoud: **ja** — fysiek exemplaar, onderscheiden van de uitgave/titel.
  - Kanttekening (inhoudelijk open, niet automatisch te beslissen): "onderscheiden door zijn eigen materiële verschijning en plaatsing" — *plaatsing* is een veranderlijk kenmerk en geen identiteitsprincipe door de tijd (vgl. N08/N09-lijn). Of dit als eenheidsgrens volstaat, is precies de menselijke ESS-03-vraag; de runtime houdt hem terecht open.
- Toetsing kandidaat: ESS-03 `review_required`, geen violation, geen signalen. (Andere regels: ESS-05, INT-01, VER-01 — buiten scope.)

## Samenvattend

| Case | Identifier toegevoegd? | Betekenis behouden? | Stof→monster? | Conflictmelding? | ESS-03 runtime |
|---|---|---|---|---|---|
| MP-01 eiland | nee | ja | n.v.t. | nee | review_required, geen violation |
| MP-02 water | nee | ja (stof) | **nee** | nee | review_required (inhoudelijk: n.v.t.-oordeel nog niet vastlegbaar) |
| MP-03 watermonster | nee | ja (afgebakende hoeveelheid) | n.v.t. (bewust monster) | nee | review_required |
| MP-04 boekexemplaar | nee (ISBN niet als criterium) | ja | n.v.t. | nee | review_required; "plaatsing" is een open inhoudelijke vraag |

Op deze vier synthetische invoeren gedraagt de echte keten zich zoals de ESS-03-fix beoogt: de G-instructie komt door, er wordt geen nummer/code/registratie verzonnen, de bedoelde lezing blijft staan en de stof wordt niet tot monster gemaakt; toetsen verandert de kandidaat niet en levert een open, scoreloos ESS-03-oordeel.

## Bevindingen en grenzen (geen toestemming voor codewijziging)

1. **Contractlacune bevestigd in de praktijk (MP-02):** de juiste menselijke uitkomst "ESS-03 niet van toepassing (stoflezing)" kan nergens worden vastgelegd; de kandidaat blijft `review_required`. Besluit onder DEF-624 (contract-gap-v1.md, opties A/B/C); ADR-002 is niet geaccordeerd en hier niet gebruikt.
2. **Verduidelijkingskanaal:** de bedoelde betekenis is meegegeven via `betekenisverduidelijking`, dat in de prompt als "keuze van de betekenislaag" is geframed (DEF-751). Er is geen apart kanaal voor "bedoelde teleenheid/stoflezing"; of dat wenselijk is, is een UI-/contractkeuze voor Chris.
3. **Echo-risico:** MP-01 en MP-03 liggen dicht bij respectievelijk het regelkaartvoorbeeld en de verduidelijking; deze proef onderscheidt niet tussen "begrepen" en "overgenomen".
4. **Buiten scope, wel waargenomen:** ESS-05 en VER-01 falen op alle vier kandidaten; CON-CIRC-001 vuurt op "waterstofatomen" (substring van "water"). Niet geanalyseerd, geen bevinding over ESS-03.
5. **Steekproefgrootte** n=4, één run, temperatuur 0,1: geen statistisch kwaliteitsbewijs; geen volledige UX-acceptatie; geen menselijke beoordeling of opslag uitgevoerd.

Geen tokens/API-keys of omgeving afgedrukt; geen extra retryrondes; vier aanroepen totaal; geen definitie opgeslagen; werkboom `git status` ongewijzigd (alleen de door de coördinator geplaatste `docs/adr/ADR-002-…` staat ongestaged, niet door mij aangeraakt).
