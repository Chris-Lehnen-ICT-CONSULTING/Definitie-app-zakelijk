# DEF-835 — technische modelproef, voorstel v1

28 september 2026. Vervolg op het afgeronde WP3 (558b50c3f161f819cda6c445f7f81b70888918ac). Chris heeft echte modelaanroepen toegestaan en opgedragen verder te gaan. Dit document concretiseert het nog open proefprofiel en budget; de algemene toestemming wordt niet opnieuw gevraagd.

## Eerstvolgende uitvoerbare stap

Een aparte runner gebruikt de bestaande keten Int02AssessmentService → AIServiceV2 → AsyncGPTClient → AnthropicClient. Geen productiecode, publieke contracten, routerconfiguratie of actieve INT-02-regel wijzigen. Twee nieuwe softwarebestanden: `scripts/analysis/def835_int02_modelproef.py` en `tests/unit/validation/test_def835_int02_modelproef.py`. Verwacht 300–500 regels inclusief tests; de verruiming voor INT-02 geldt. Geen dependency erbij.

De runner wordt eerst offline gebouwd en onafhankelijk gereviewd. Dat kan doorgaan vóór de concrete budgetbeslissing. Standaard alleen een offline voorbereiding; echte verzending vereist expliciete live-optie en een exact passend akkoordmanifest. Niet automatisch doorgaan bij onbekende configuratie.

## Profiel en grenzen ter vaststelling

- Experimenteel technisch proefprofiel `def835-technische-proef-opus5-v1`; provider `anthropic`, aangevraagd model `claude-opus-5`, taak `validation`. Bestaande router/capabilitybeleid wordt gecontroleerd, niet gewijzigd. Een proefautorisatie is geen inhoudelijke modelkwalificatie volgens DEF-815.
- Maximaal drie inferencecalls, sequentieel: C105, C107 en C112 uit `tests/fixtures/def835_int02_ontwerpgevallen.json`. Alleen het veld `invoer` gaat naar het model, nooit fixture-respons of verwacht label. Alle invoer is synthetisch. De gevallen testen respectievelijk voorschrift, ontbrekende bedoeling en definitie van een normatieve zaak. Zij zijn ontwikkelmateriaal, geen onafhankelijke goldset/hold-out.
- Per call maximaal 6.000 uitvoertokens, 120 seconden en vooraf maximaal 16.000 geschatte invoertokens via de gratis provider-tokenmeting op exact dezelfde requestinhoud. Maximaal drie telrequests. Geen retries, fallback, herstelcall, tools, batch, fast mode of promptcache. Totale looptijd maximaal tien minuten, inclusief preflight.
- Voorstel kostenplafond: **US$1 aan standaard API-gebruik**. Bij $5/M invoer en $25/M uitvoer is de begrote bovengrens 3 × (16.000 × $0,000005 + 6.000 × $0,000025) = **$0,69**, met $0,31 marge. Tokenmeting is een schatting; deze begroting is geen garantie over de providerfactuur/belasting. De runner reserveert vóór elke call conservatief budget, meet daadwerkelijk input/outputgebruik en stopt bij afwijkende of ontbrekende usage, onbekende prijsvariant, overschrijding of technische fout.
- Stop ook bij afkapping, ongeldige JSON/citaten/binding of gewijzigde payload/configuratie. Een inhoudelijk ander oordeel wordt gerapporteerd; er volgt geen automatische promptverbetering of herhaling.
- Geheimen alleen via bestaande lokale configuratie, nooit in opdracht, argumenten, rapport of logs. Geen productiedatabase lezen; relatieve monitoring/cache gaat naar een afzonderlijke tijdelijke proefmap. Volledige synthetische requests/antwoorden alleen in het aangewezen bewijsdossier, diagnostiek zonder payloads of foutberichten van de provider. Geen claim dat algemene ketenlogging daarmee is opgelost.
- Bewaar synthetisch bewijs lokaal in dit repositorydossier gedurende het DEF-835-traject; geen automatische verwijdering. Geen eigen retentieclaim over de provider. Versturen omvat de synthetische invoer en norm/T-prompt.

## Bewijs en acceptatie van de technische proef

Offline: nul netwerk in standaardmodus; echte keten met fake providergrens; harde maxima over drie gevallen; stop bij fouten; geen retry/cache/fallback; geen fixturelabels in requests; manifest/hashbinding; weigering zonder akkoord of bij mismatch; geen overschrijven bestaand bewijs; geredigeerde foutregistratie. Eerst rood, daarna groen, relevante regressie en lint.

Live: bewaar aangevraagde en gerapporteerde model-ID, prompt/norm/config/invoerhashes, exacte provider-input/outputtokens, stopreden, tijdsduur, berekende kosten, ongewijzigd WP1-document en mechanische status. Een semantisch onverwachte uitkomst is een bevinding, geen reden om labels te veranderen. Drie geldige antwoorden bewijzen alleen dat deze technische keten op deze drie invoeren werkt; geen algemene INT-02-modelkwalificatie.

## Vervolg naar volledige integratie

1. WP4: onafhankelijke labels/hold-out, acceptatie-eigenaar en kwaliteitsgrenzen vóór inhoudelijke evaluatie vaststellen. De bestaande 76 ID's blijven ontwikkelmateriaal.
2. WP5: concrete uitbreiding van container, validation orchestrator en ModularValidationService; daarna save/reload/UI/export via de gedeelde DEF-626-historie. Constructor/API, opslag/schema en bestandsbereik eerst afzonderlijk voorleggen. Geen tweede INT-02-opslagroute.
3. WP6: ketenverificatie en PR. Activering blijft een afzonderlijk besluit; Actions blijven uit.

Actueel opgehaalde Linear-bronnen: DEF-626 en DEF-815 staan in Backlog (geraadpleegd 28-09); DEF-835 In Progress. De voorbereide technische proef loopt vooruit op hun implementatie, zonder te claimen dat hun acceptatiecriteria zijn vervuld. Het algemene modelkwalificatie-/versiebeleid blijft open.

## Prijs- en API-bronnen

Geraadpleegd 28 september 2026: [Anthropic Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview) (model-ID en standaardtarief) en [token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting) (kosteloos, geschatte aantallen). Repo: `src/services/ai/model_router.py:44` e.v. en `config/config.yaml` capabilitybeleid. De daadwerkelijke routeruitkomst wordt door de proef gecontroleerd.
