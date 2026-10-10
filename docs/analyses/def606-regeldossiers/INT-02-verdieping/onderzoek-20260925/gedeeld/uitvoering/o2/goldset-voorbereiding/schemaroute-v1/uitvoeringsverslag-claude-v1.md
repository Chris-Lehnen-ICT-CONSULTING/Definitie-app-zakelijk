# Uitvoeringsverslag — schemaroute v1 (besluit 14, optie A)

DEF-835 INT-02 O2 · 07-10-2026 · branch `feature/DEF-835-int02-o2`, basis-HEAD `ec1f38320` · **niet gecommit, niet gepusht** · geen live calls, `.env` niet gelezen.

## Doel

In v6 stopte fase 1 op C105 met `invalid_output`. Het model zette een extra veld `reason` in een passage; de inhoud was verder juist. Besluit 14 kiest optie A: de bestaande gesloten uitvoervorm gaat als JSON-schema mee naar de API (`output_config.format`). Daarbij gelden drie randvoorwaarden:

- contract, prompttekst en alle code-controles blijven gelijk;
- ESS-03, INT-03, generatie en de O1-route blijven functioneel onaangeroerd;
- de runner laat alleen exact dit schema door.

## Wijzigingen (bestand:regel)

### Productiecode

**`src/domain/int02/contract.py`**
- :13-18: de docstring noemt het schema.
- :57-58: `__all__` is uitgebreid.
- :164-243: `ANTWOORDSCHEMA` en `ANTWOORDSCHEMA_SHA256`. De hash is na de review `72adfe7428b67bf0fd999520581f0fc2cbe801101e1e8e6df300179405511f17`; de eerste pin was `2b1ac6a8…f96191`. `ground` is `_GRONDSCHEMA` (:176-201): drie gesloten varianten, zie "Review (Codex, 07-10)".
- `CONTRACTVERSIE` blijft `def835-int02-assessment/3`.
- Geen enkele controlefunctie is gewijzigd.

**`src/services/validation/int02_assessment_service.py`**
- :24-33: docstring met de schemaroute; :35-44: docstring met de volgorde.
- :150-153: `PROMPT_VERSION = "def835-int02-prompt/4"`, met de toelichting "/4 = zelfde tekst + schemaroute".
- :123-126: imports (en `Mapping` in de standaardimport).
- :732-734: pincontrole vóór de aanroep; bij afwijking `schema_mismatch`.
- :793-795: `response_schema=ANTWOORDSCHEMA`.
- :797-802: een schemaweigering vóór verzending geeft `structured_output_unsupported`.
- :968-983: antwoordcontrole: eerst de schemabevestiging (`schema_unconfirmed`), na de stopreden precies één tekstblok (`unexpected_content_blocks`).
- :993-1006: `_schema_niet_ondersteund` volgt de oorzaakketen, naar het voorbeeld van `_int03_foutsoort`.
- De prompttekst is ongewijzigd: de systeemprompt-hash blijft `da4a4112…`.

**`scripts/analysis/def835_int02_modelproef.py`**
- :11-15: docstring.
- :137-144: `output_config` in `TOEGESTANE_VELDEN` en in `TELVELDEN`.
- :393-410: `_exact_uitvoerschema` vergelijkt de dict én de volgordegevoelige hash.
- :736: `output_config` is verplicht in `_controleer`.
- :1150-1170: het routerdeel van de identiteit krijgt `supports_structured_outputs` en `antwoordschema_sha256`.
- `SDK_HEADERS` en `VASTE_HEADERS` zijn ongewijzigd: geen beta-header.

### Tests

**Nieuw: `tests/unit/validation/test_def835_int02_schemaroute.py` (40 tests)**
- Schemavorm (:265-317).
- Hash gepind en volgordegevoelig (:335).
- Subprocessen met PYTHONHASHSEED 0-7 (:353).
- Ontwerpfixtures voldoen aan het schema (:383).
- De v6-respons van C105 voldoet niet; zonder het veld wel (:392, :402).
- 16 afwijkingen die schema én contract weigeren (:455).
- Dienst (:587-682).
- Echte keten AIServiceV2 → AnthropicClient → SDK → MockTransport (:759, :777).

**`tests/unit/validation/test_def835_int02_modelproef.py`**
- :45-46: `SCHEMA` en `OUTPUT_CONFIG`.
- :259-263: payloadtest.
- :395-399: de tokenmeting telt `output_config` mee.
- :642: `BODY` met schema.
- :2348-2446: vier schemaroute-tests, waarvan één met 8 varianten.

**`tests/unit/validation/test_def835_int02_assessment_service.py`**
- :238-244: FakeAI bevestigt het schema.
- :539-540: het schema reist mee.
- :1058-1066: `_Provider`-metadata.
- :1091: kwargs met schema.
- :1277-1299: de OpenAI-route geeft nu `structured_output_unsupported`, met 0 SDK-calls.

**`tests/unit/validation/test_def835_int02_variatiemeting.py`**
- :39-42: commentaar.
- :246, :329: promptversie /4.
- :255-298: de v5-payload plus alleen `output_config`. De dry-run is bewust niet meer byte-gelijk aan v5.

**Overige testbestanden**
- `tests/unit/services/prompts/test_def835_int02_prompt.py:217, :355`: promptversie /4.
- `tests/unit/domain/test_def835_int02_dienstregel.py:700-710, :738-740, :760`: de fake bevestigt het schema; /4 met dezelfde systeemprompt.
- `tests/unit/services/orchestrators/test_def835_int02_wrappers.py:506-528`: de fake bevestigt het schema.

`git diff --stat`: 9 getrackte bestanden, 408 regels erbij en 40 eraf. Daarbij komen nieuw, ongetrackt: het testbestand en deze map.

## Keuzes

1. **Schemahash zonder `sort_keys` (bewuste afwijking van de opdrachttekst).**
   - De opdracht noemde "canonieke JSON, sort_keys, vaste separators". Ik pin de hash met `services.ai.base_client.response_schema_sha256`: compacte JSON met vaste separators, maar zonder `sort_keys`.
   - Reden: dat is de functie waarmee de AI-laag het verzonden schema bevestigt (`metadata.response_schema_sha256`). Met een sort_keys-hash zou de bevestigingscontrole nooit kunnen slagen.
   - Daarnaast zou een sort_keys-hash blind zijn voor de eigenschapsvolgorde. Die stuurt de provider wel, en de opdracht eist "veldvolgorde gelijk aan de prompt".
   - Het doel van sort_keys (procesonafhankelijkheid) wordt bereikt met gesorteerde enums. De subprocestest met acht verschillende seeds bewijst dat; dezelfde test laat zien dat de ruwe frozenset-volgorde wél per seed verschilt.
   - INT-03 werkt op dezelfde manier. **Graag bevestigen bij de review.**
2. **`ground` als unie van gesloten varianten (na de review).** In v1 stond `ref` als een losse `anyOf` string/integer/null. Codex wees dat af (P2, zie hieronder). Nu volgt het schema de koppeling veld → ref exact. Wat het schema niet kan uitdrukken, blijft in de code: niet-lege `reason` en bron-ID, een context-index als Python-int (`0.0` past in het schema, maar de code weigert het), indexbereik, bestaan van de bron, en letterlijkheid en uniciteit van citaten.
3. **Niet-ondersteund geeft `not_executed`, geen `error`.**
   - INT-02 classificeert alle blokkades vóór verzending (profiel, router, beleid, invoer) als `not_executed`, wat leidt tot review_required/not_assessed met een servicereden en transportpogingen 0.
   - Een schemaweigering door de AI-laag gebeurt aantoonbaar vóór de SDK-call. De echte-ketentest laat 0 requests zien. Dus dezelfde klasse, met de eigen reden `structured_output_unsupported` en het uitzonderingstype; de uitzonderingstekst komt niet in het resultaat.
   - Een afwijkende pin (`schema_mismatch`) valt in dezelfde klasse.
   - INT-03 maakt hier een technische fout (`unsupported_configuration`) van. Dit is dus een bewuste INT-02-keuze, **ter bevestiging bij de review**.
4. **Volgorde van de antwoordcontrole.**
   - De bevestiging van de schemahash komt vóór de stopreden. Een niet-bevestigd schema maakt elk antwoord onbruikbaar.
   - De bloktypecontrole komt ná de stopreden, zodat een afgekapt antwoord `truncated_response` blijft.
   - Beide redenen zijn `completed` zonder geldige uitvoer, dus `error` met `invalid_output`. Zo'n resultaat wordt nooit gecachet.
   - `refusal` blijft `unconfirmed_completion` (fail-closed).
5. **Binding en cache zijn niet uitgebreid met de schemahash.** Het schema is vastgepind op prompt /4. Een ander schema faalt vóór de aanroep tot er een nieuwe pin en promptversie is, dus de promptversie in de binding dekt het schema. `supports_structured_outputs` verandert de payload niet: het is verzenden of blokkeren. Daarom komt het niet in de routeringshash van de dienst; de runner legt het wel vast in de identiteit.
6. **De runner eist `output_config`.** Ontbreken is ook `payload_niet_toegestaan`: onder /4 mag er geen stille terugval naar vrije tekst over de lijn gaan. Gelijkheid wordt dubbel getoetst: met een dict-vergelijking en met de volgordegevoelige hash. Die hash vangt ook `0`/`1` tegenover `false`/`true`. De identiteit legt `thinking` vast zoals de adapter het verstuurt (`disabled` als `thinking_default_on`).
7. **OpenAI-route.** De OpenAI-adapter weigert elk schema vóór verzending. Daardoor kan INT-02 via OpenAI nu niet meer draaien: `structured_output_unsupported`, 0 SDK-calls. Dat was al zo in effect, want zonder `finish_reason` was er nooit een oordeel. Twee bestaande F1-tests zijn daarop aangepast.
8. **Variatiemeting C107.** De tests die byte-gelijkheid met de v5-payload eisten, zijn bewust gesprongen. Ze toetsen nu dat de payload gelijk is aan de v5-payload plus alleen exact `output_config`, en dat de dry-run niet meer byte-gelijk is. De meting van 07-10-2026 is daarmee historisch. Het meetscript zelf is niet gewijzigd.
9. **Testfakes.** De FakeAI-, `_Provider`-, dienstregel- en wrapper-fakes bootsen nu na wat AIServiceV2 en de Anthropic-adapter melden bij een schema: de hash en `["text"]`. Zonder die nabootsing zou elke bestaande oordeeltest `schema_unconfirmed` geven. De wrapper-test (O1-wrappers rond de INT-02-dienst) heeft alleen een fake-aanpassing; de productiecode van de wrappers is niet aangeraakt.

## Tests

Logs staan in deze map. De samenvatting en de mutatiecontrole staan in `groen.log`.

| Stap | Selectie | Uitslag |
|---|---|---|
| Nulmeting | `-k "def835 or int02" tests/unit` | 959 passed, 11 skipped |
| Rood | zeven testbestanden (`rood.log`) | 61 failed, 520 passed |
| Groen 1 | dezelfde zeven bestanden | 581 passed |
| Groen 2 | `-k "def835 or int02" tests/unit` | 1010 passed, 11 skipped |
| Groen 3 | `-k "int03 or ess03 or def836 or def766 or def772" tests/unit`, met `test_def836_int03_schema_route.py` | 791 passed |
| Groen 4 | ruff + black op de tien Python-bestanden | schoon |
| Mutatie M1 | runner zonder volgordegevoelige hash | 1 test rood (andere-volgorde) |
| Mutatie M2 | dienst zonder bloktypecontrole | 4 tests rood |

Als extra vangnet draaide de volledige unit-suite (`-m unit tests/unit`, dezelfde vlaggen): **8808 passed, 2 failed**, 81 skipped.

- Beide falers zitten in `tests/unit/test_performance_tracker.py::TestGlobalTracker`. Het is een `OfflineGateError`: `data/definities.db` ligt buiten de sessieroot.
- Ze falen ook als ik het bestand los draai. Ze raken geen INT-02-, schema- of AI-code.
- Waarschijnlijk komt het door mijn aanroep: `-o addopts=""` vanuit de repo, in plaats van de canonieke gate.
- Niet nagemeten op HEAD zonder deze wijziging.

`make test` en `make lint` zelf zijn niet gedraaid.

## Risico's

- **De API kan het schema met een 400 weigeren.** Dat blijkt pas live. Het schema blijft binnen de gedocumenteerde subset (0 optionele parameters, 6 unions, alleen `type`/`properties`/`required`/`additionalProperties`/`items`/`enum`/`anyOf`), maar de echte API heeft het nog niet gezien. De runner boekt een 400 als `providerfout` (fouttype zonder tekst) en stopt. De eerste fase-1-run onder v7 is dus tegelijk de live-rooktest.
- **De tokenmeting met `output_config`.** De SDK accepteert het veld bij `count_tokens` (0.116.0, gecontroleerd in de geïnstalleerde code). Of het endpoint het accepteert en meetelt, is pas live te zien; bij een fout stopt de runner met `tokenmeting_mislukt` vóór de inference.
- **Het modelgedrag kan verschuiven.** Constrained decoding en de schemavolgorde kunnen de inhoud beïnvloeden: de keuze van functie, gronden en vraag. De v5/v6-uitslagen zijn niet één-op-één vergelijkbaar. De gesloten vorm is afgedwongen; de semantiek niet. De code-controles (citaten, samenhang, dienstregel) blijven het vangnet.
- **Refusal en `max_tokens` blijven fail-closed.** Een antwoord dat het schema schendt, wordt nooit gerepareerd.

## Gevolgen voor manifest v7

- **Payloads:** alle 43 veranderen, want `output_config` komt erbij. De systeemprompt en de dataprompt per geval blijven gelijk.
- **Identiteit:**
  - `profiel.promptversie` → `def835-int02-prompt/4`;
  - `router.supports_structured_outputs` (true) en `router.antwoordschema_sha256` (`72adfe74…`) komen erbij;
  - de bestandshashes van `contract.py`, de dienst en de runner veranderen;
  - de proefmap wordt `kwalificatieproef-v7`.
- **Ongewijzigd:** headernamen (geen beta), gevallen, labels, limieten, prijzen, criteria en norm.
- **Nodig:** een nieuw exact akkoord van Chris op v7. Daarna alleen fase 1.

## Review (Codex, 07-10)

Oordeel van Codex: "commit verantwoord: nee", met één P2-bevinding.

### P2 en de fix

**Bevinding.** In het eerste schema mocht `ground.ref` tekst, een geheel getal of null zijn, los van `field`. De contractcontrole (`_controleer_grondvorm`, `contract.py` :614-623) eist wel vaste combinaties. Daardoor waren drie combinaties schema-conform maar gaven ze `invalid_output`. Bevestigd:
- `kern` met ref `"willekeurig"`;
- `bron` met ref `null`;
- `juridische_context` met ref `null`.

Het schema liet dus precies het soort fout door dat het moest voorkomen.

**Fix** (`contract.py` :176-201, `_grondvariant` en `_GRONDSCHEMA`). `ground` is nu een `anyOf` van drie gesloten varianten, in promptvolgorde en volgens de echte coderegels:

| Variant | `field` (enum, gesorteerd) | `ref` |
|---|---|---|
| scalair | `bedoeling`, `begrip`, `kern` (= `_SCALAIRE_GRONDEN`) | `null` |
| context | `juridische_context`, `organisatorische_context`, `wettelijke_basis` (= `_CONTEXTVELDEN`) | `integer` |
| bron | `bron` | `string` |

Elke variant heeft `additionalProperties: false`. Alle velden zijn verplicht en `quote` blijft `string|null`. De enums komen uit dezelfde constanten als de code. `const` is niet nodig: een enum met één waarde drukt hetzelfde uit en blijft binnen de geteste subset van sleutelwoorden.

**Wat in de code blijft:**
- niet-lege bron-ID (`_gevuld`);
- indexbereik en bestaan van de bron (`_grondbron`, `invalid_citation`);
- niet-lege `reason`;
- letterlijkheid en uniciteit van citaten.

**Grenzen.** Het schema heeft 0 optionele parameters (grens 24) en 6 unions (grens 16): `question`, `scope_reason`, `ground` en drie keer `quote`.

**Nieuwe schemahash:** `72adfe7428b67bf0fd999520581f0fc2cbe801101e1e8e6df300179405511f17` (was `2b1ac6a8…f96191`). Contract, dienst en runner lezen de pin uit het contract. De tests pinnen de nieuwe waarde letterlijk, in de schemaroute-test en in de identiteitstest van de runner. Ze controleren ook dat die afwijkt van de eerste pin. De test met acht hashseeds blijft groen.

### Tests (TDD)

**Rood** (`rood-review.log`, schemaroute- en runnertests): 14 gefaald, 233 geslaagd. Daarbij:
- de drie bevestigde combinaties;
- de exacte grondvarianten;
- de grenstelling (6 unions);
- de nieuwe pin, ook in de runner;
- de matrixtest, rood op een echt verschil (`bedoeling`, ref 0).

**Nieuwe en aangepaste tests** in `test_def835_int02_schemaroute.py`:
- :341: `ground` is exact de verwachte unie en volgt de indeling van het contract.
- :375: de drie bevestigde combinaties zijn niet schema-conform, en ook de code weigert ze.
- :395: elke grondvariant heeft een conform voorbeeld, met en zonder citaat; 14 gevallen.
- :407: de matrixtest gaat over alle 7 velden × 11 ref-waarden × 3 citaatwaarden. Schema en contractvorm moeten dezelfde uitkomst geven, met als enige toegestane uitzondering een lege bron-ID, die alleen de code kan weigeren.
- :427: grenzen op (0, 6).
- Alle geldige ontwerpgevallen blijven conform.

Bij de eerste groene run faalde de matrixtest nog op een fout in de test zelf: een lijst als ref is niet hashbaar. Die fout is hersteld.

**Groen** (`groen-review.log`):

| Selectie | Uitslag |
|---|---|
| Zeven gewijzigde testbestanden | 600 geslaagd |
| `-k "def835 or int02" tests/unit` | 1029 geslaagd, 11 overgeslagen (19 meer dan v1) |
| INT-03/ESS-03 | 791 geslaagd |
| ruff + black | schoon |

### Bevestigd door Codex (ongewijzigd)

- De schemahash zonder `sort_keys`, met dezelfde functie als de AI-laag; deze is volgordegevoelig en procesonafhankelijk.
- De dienstcontroles: pin vóór de aanroep, schema meesturen, bevestiging van hash en precies één tekstblok, refusal fail-closed.
- `structured_output_unsupported` geeft `not_executed`, dus review_required/not_assessed. Dat stopt de fase en kan geen proef laten slagen.
- De runner: exact `output_config`, ook in volgorde; telt mee in de tokenmeting; identiteit met schemahash en capability; geen beta-header.
- De neveneffecten: de OpenAI-route is dicht vóór verzending, de variatiemeting is historisch, de fakes bootsen de AI-laag na.
- Prompt /4 heeft dezelfde tekst als /3 (systeemprompt `da4a4112…`).
- De twee `test_performance_tracker`-falers staan hier los van.

## Herreview (Codex, 07-10)

Oordeel: "commit verantwoord: ja". Er was één niet-blokkerende P3; die is verwerkt. Alleen de testcode is gewijzigd, de productiecode niet.

**P3.** De testvalidator las JSON-schema `integer` als uitsluitend een Python-`int`, en de matrix had geen `0.0`. Volgens JSON Schema (Draft 2020-12) is een getal zonder breukdeel ook een `integer`. Een context-ref `0.0` past dus in het schema, maar de contractcode weigert hem (`_is_int`). Die weigering is veilig: het resultaat is `invalid_output`, nooit een oordeel.

**Verwerkt** in `test_def835_int02_schemaroute.py`:
- De validator (`_type_klopt`) leest `integer` nu volgens JSON Schema: elk eindig getal zonder breukdeel, ook `0.0` en `1.0`, maar geen `true`/`false`.
- De matrix bevat nu ook `0.0` en `1.0`.
- `_alleen_in_code` beschrijft de twee toegestane afwijkingen, waarbij het schema accepteert en alleen de code weigert:
  1. een lege of alleen-witruimte bron-ID;
  2. een context-index als geheel getal van het type float (`0.0`, `1.0`).
- De lookup houdt rekening met het type, omdat in Python `0.0 == 0` geldt.

**Testuitkomsten** (`groen-herreview.log`):

| Selectie | Uitslag |
|---|---|
| Schemaroutetests | 59 geslaagd |
| `-k "def835 or int02" tests/unit` | 1029 geslaagd, 11 overgeslagen |
| ruff + black | schoon |

## Open punten

1. Manifest v7 offline (schemahash `72adfe74…`), het akkoord van Chris, fase 1 als live-rooktest.
