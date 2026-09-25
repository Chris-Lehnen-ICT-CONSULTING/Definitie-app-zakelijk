# INT-01 (DEF-770) — runplan T24 en G24 na implementatie

23 september 2026 · versie 2 (vervangt [versie 1](runplan-t24-g24-v1.md) na de Codex-review, drie bevindingen verwerkt) · **niets hieronder is uitgevoerd.** Dit plan beschrijft hoe de effectproeven uit [synthese v3](../INT-01-verdieping/onderzoek-20260923/gedeeld/synthese-v3.md) (onderzoeksboom in de hoofdcheckout, niet getrackt) op de gebouwde variant worden gedraaid. Tot beide proeven zijn uitgevoerd en beoordeeld is de status: **geïmplementeerd; kwaliteitswinst nog niet vastgesteld.**

## 0. Wat al vaststaat (en wat niet)

| Bewijs | Bron | Claimgrens |
|---|---|---|
| Nulmeting op base `26f2374d`: 6 gevallen × 2 laadpaden, 12/12 statussen conform, exit 0 | onderzoek A, `proefuitkomsten-v2.json` | alleen status; geen redenen/spans |
| Serviceproef na implementatie: 10 gevallen (E01–E08, EB03, EB04) × 2 laadpaden, 20/20 conform vooraf vastgelegde verwachting, INT-01 nooit in `passed_rules`, offline-gate actief | [`proef-na-implementatie-v1.py`](proef-na-implementatie-v1.py), [`proefuitkomsten-na-implementatie-v1.json`](proefuitkomsten-na-implementatie-v1.json) | ontwerp-/regressiegevallen, **geen ongeziene eindset**; bewijst geen effect |
| Proef ronde 2 na de review: 13 gevallen (v1-set plus de reviewgevallen ‘enz. 3 velden’ en ‘categorie A. Het’, en J. Jansen) × 2 laadpaden, 26/26 conform inclusief onderdelen; compactheid en begrijpelijkheid apart; plus de gewone opslag-, lees- en exportroute (13 records, update met historie, wijziging buiten de laag om): alles conform, offline-gate actief | [`proef-na-implementatie-v2.py`](proef-na-implementatie-v2.py), [`proefuitkomsten-na-implementatie-v2.json`](proefuitkomsten-na-implementatie-v2.json) | idem: ontwerp-/regressiegevallen, **geen ongeziene eindset** |
| Unit- en ketentests (segmentatie, beide laadpaden, opslag/teruglezen/export met binding, herladen, UI-renderer, prompt); in-memory mutatiematrix 8/8 gevangen | `tests/unit/validation/test_def770_int01_zinsgrenzen.py`, `tests/unit/services/test_def770_int01_keten.py`, `tests/unit/services/test_def770_int01_opslag.py`, `tests/unit/services/prompts/test_def770_int01_promptnorm.py` | synthetische invoer; geen modeluitvoer, geen gebruikers |

## 1. Binding vóór elke uitvoering

Leg vast en bevries, in een manifest naast de uitkomsten:

- **oude variant:** `git archive 26f2374d302fc66fc0b12ed29dc34585f7c0a5c3` (record, evaluator, prompt);
- **nieuwe variant:** de gemergde DEF-770-commit (SHA), plus sha256 van `src/toetsregels/regels/INT-01.json`, `src/domain/int01/zinsgrenzen.py`, `src/domain/int01/opslag.py`, `src/services/validation/evaluators/sentence_boundary.py` en `src/services/prompts/modules/json_based_rules_module.py`;
- voor G24 ook modelnaam, provider, temperatuur, `max_tokens`, promptversie en de exacte bron/context per invoer.

Wijzigt een van deze bestanden na vrijgave van een eindset, dan is die set ontwikkelmateriaal geworden en is een nieuwe onafhankelijke set nodig.

## 2. T24 — ongeziene onafhankelijke evaluatorproef (geen modelcalls)

**Rollen.** Maker van de set: een onafhankelijke persoon, niet de implementator (Claude Code CLI-uitvoerder van DEF-770) en niet de reviewer. Twee referentiebeoordelaars labelen vooraf; een adjudicator beslist onenigheid vóór uitvoering. De DEF-770-coördinator wijst alle rollen aan en bewaakt de volgorde. Nog niemand is aangewezen.

**Samenstelling: 6 strata × 4 = 24 nieuwe gevallen**, per stratum waar toepasselijk positieve en negatieve tegenhangers:

| # | Stratum | Voorbeelden van variatie (niet de gevallen zelf) |
|---|---|---|
| S1 | naamwoordelijke kernen en noodzakelijke bijzinnen | kern zonder persoonsvorm; ‘die/waarbij’-bijzin; nevenschikking in een naam |
| S2 | afkortingen en getallen | titel + naam; verwijzing + nummer; afkorting die ook zinslot is; getal aan zinseinde |
| S3 | duidelijke `.?!`-grenzen | vraagzin + zin; uitroep; tweede zin met differentia; tweede zin met uitweiding |
| S4 | opmaak en lijsten | regelomloop; alinea zonder slotteken; opsommingstekens; puntkomma-opsomming |
| S5 | citaten en haakjes | hele kern geciteerd (C35); ingesloten titel met `?`; punt binnen haakjes |
| S6 | leeg en onzeker | lege kern; alleen label; kleine letter na punt; onbekende afkorting |

**Referentielabels (vooraf, per geval, door beide beoordelaars afzonderlijk):**

1. verwachte INT-01-status: `fail` (zekere tweede zin) · `review_required` met zinsstructuur `pass` (één zin) · `review_required` met onzekere grens · `not_evaluated` (leeg); compactheid en begrijpelijkheid zijn in elk niet-leeg geval twee aparte open onderdelen en worden niet gelabeld;
2. bij een grens: de verwachte grenspositie (tekenindex of passage) en de redencategorie (nieuw zinsbegin, afkorting-als-slot, citaat/haakjes, opmaak, kleine letter, getal);
3. bij een hele-kerncitaat: verwacht onderdeel `broncitaat` open.

Een vooraf zeker verwacht ‘onzeker’ is een geldig label. Onenigheid wordt geregistreerd; wat de adjudicator niet eenduidig kan maken blijft een **dispuut** en telt niet in de conformiteitsnoemer. Vervanging van een geval mag alleen vóór uitvoering, met een geval uit dezelfde klasse, en blijft zichtbaar in het manifest; achteraf herlabelen is uitgesloten.

**Verzegeling.** De maker levert `t24-gevallen.json` (id, stratum, begrip, tekst, bron/reden van het geval) en de beoordelaars `t24-referenties-{a,b}.json` plus `t24-adjudicatie.json`. De coördinator legt sha256 van alle vier vast vóór de run.

**Uitvoering.** Een runner naar het model van `proef-na-implementatie-v2.py`, uitgebreid met het inlezen van `t24-gevallen.json`, draait elk geval op oude en nieuwe variant via **beide laadpaden** (ToetsregelManager en CachedToetsregelManager), offline-gate actief, verse tijdelijke opslag. Per rij vastleggen: status, `passed_rules`-lidmaatschap, melding, reviewreden, alle onderdelen met `id/status/evidence/position/reason`, en de via de gewone opslagroute opgeslagen en teruggelezen uitkomst (`int01_beoordeling` met binding) — die moet gelijk zijn aan de service-uitkomst.

**Beoordeling per rij:** conform als status, grens (positie binnen de referentiepassage) en redencategorie overeenkomen, en INT-01 nooit in `passed_rules` staat. Per rij oud → nieuw: verbeterd / gelijk / verslechterd / onbeslist.

**Rapportage.** Alle 24 rijen tonen. Aantallen: eenduidig gelabeld = *evalueerbaar/24*; *conform/evalueerbaar*; disputen apart. Een 24/24-claim alleen als alle 24 eenduidig gelabeld en conform zijn.

**Criteriumvoorstel (vóór uitvoering door de coördinator te bevestigen):** 24/24 passende referentie-uitkomsten inclusief redenen/grenzen; geen nieuwe zekere fout (oud correct → nieuw fout); geen onterechte volledige kwaliteitsclaim. Elke nieuwe zekere fout blokkeert een effectclaim tot zij verklaard of hersteld is — en herstel maakt een nieuwe eindset nodig.

**Kosten.** Geen modelcalls. Menstijd (schatting, te bevestigen): maker 4–6 uur, twee beoordelaars elk circa 2 uur, adjudicatie circa 1 uur, run en rapport circa 2 uur.

## 3. G24 — generatie-effect (24 betaalde modelcalls, pas na begrotingsbesluit)

**Invoer: zes nieuwe bron- en contextgebonden invoeren**, gemaakt door een ander dan de implementator: (1) gewone kern, (2) noodzakelijke bijzin, (3) noodzakelijke naam, (4) limitatieve opsomming, (5) vaktaal met benoemde doelgroep, (6) risico op betekenisverlies bij inkorten. Per invoer vooraf vastgelegd: begrip, drie contextlijsten, aangeleverde bronpassage(s), bedoelde betekenis, doelgroep en de verwachte beschermde kenmerken, namen en negaties.

**Ontwerp:** 6 invoeren × oud/nieuw promptvariant × 2 herhalingen = **24 generatiecalls**, gelijk model en instellingen, gelijke bron/context. Oud = prompt uit `26f2374d`; nieuw = bevroren DEF-770-commit.

**Isolatie.** Zet voor beide armen automatische enhancement uit of bewaar de ruwe modeluitvoer vóór enhancement; beoordeel `definitie_origineel` en de opgeschoonde kandidaat. Loopt de run door de volledige app-generatie, dan start elke validatie ook de ESS-03-beoordeling en, met bronnen, de CON-02-bronbeoordeling: dat zijn extra betaalde calls. Aanbevolen is een promptharnas dat uitsluitend de generatiecall doet, zodat het aantal exact 24 is; anders moet de begroting die extra calls meetellen (zie hieronder).

**Beoordeling.** Twee inhoudelijke beoordelaars, blind voor de variant (gerandomiseerde labels), beoordelen elke kern afzonderlijk op zinsstructuur, compactheid, begrijpelijkheid voor de vastgelegde doelgroep, bronsteun en betekenisbehoud (differentia, namen, negaties). De nieuwe evaluator draait ook, maar is niet de enige rechter. Per gepaarde invoer: beide herhalingen, verbeterd / gelijk / verslechterd / onbeslist, en hun consistentie.

**Criteriumvoorstel:** minstens één inhoudelijke verbetering, geen nieuwe bron- of betekenisfout en geen verslechtering per gepaarde invoer. Een gelijkstand rechtvaardigt geen winstclaim; wisselende richting tussen herhalingen blijft ‘onbeslist’. Over extra herhalingen besluit de inhoudelijk onderzoeksleider vóór aanvullende uitvoering. Dit is verkennend bewijs, geen betrouwbaarheidsclaim.

**Begroting (vóór uitvoering te bevestigen; niet uitgevoerd).**

- Gemeten promptomvang, offline zonder modelcall (`PromptServiceV2.build_generation_prompt`, begrippen ‘transitie-eis’/type en ‘vervoersverbod’/proces, met drie contextlijsten, zonder bronnen): oud 36.940 / 36.332 tekens, nieuw 37.690 / 37.082 tekens. Met bronpassages wordt dit groter.
- Aanname voor Nederlandse tekst: 3–4 tekens per token → circa 9.500–12.600 invoertokens per call; begroot 15.000 als bovengrens inclusief bronnen. Uitvoer: begroot ten hoogste 1.000 tokens per call. Tokenaantallen vóór uitvoering exact laten tellen met de tokenteller van de provider.
- Prijs: de app registreert voor `claude-opus-5` 0,000005 USD per invoertoken en 0,000025 USD per uitvoertoken (`src/services/ai/model_router.py`, regel 70). Dat is appconfiguratie, geen geverifieerde providerprijs; haal de actuele prijs op en citeer die vóór het besluit.
- Rekenvoorbeeld met die appwaarden, alleen generatiecalls: 24 × 15.000 × 0,000005 = 1,80 USD invoer; 24 × 1.000 × 0,000025 = 0,60 USD uitvoer; **circa 2,40 USD bovengrens**. Via de volledige appketen met ESS-03- en CON-02-beoordeling per validatie: reken tot driemaal zoveel calls, **circa 7,20 USD bovengrens**.
- Stopregel: geen uitvoering zonder schriftelijk begrotingsbesluit; stop bij een foutmelding van de provider of bij overschrijding van de begrote tokens.

## 4. Open punten die de proeven begrenzen

- **Geen doelgroepveld in de app.** De instructie vraagt begrijpelijkheid ‘voor de vastgelegde doelgroep’, maar de app legt geen doelgroep vast; het open onderdeel zegt dat expliciet. G24 kan begrijpelijkheid alleen beoordelen met een in de invoer vastgelegde doelgroep buiten de app. Een doelgroepveld is een schema-/contractkeuze buiten DEF-770.
- **Opslag van de deeluitkomst (opgelost in ronde 2).** Versie 1 meldde dat ‘één zin, compactheid en begrijpelijkheid open’ nergens werd opgeslagen of geëxporteerd. Nu bewaart de persistentielaag bij elke schrijfactie die de kern zet (nieuw record, update, bronvoorsteltoepassing — alle via `create_definitie`/`update_definitie`; de enige andere tekstschrijver, `get_or_create_draft`, maakt een leeg concept zonder uitkomst, en de eerste tekst daarop loopt weer via `update_definitie`) de INT-01-deeluitkomst onder `int01_beoordeling` in de bestaande JSON-registratie `generation_prompt_data`: status, reden, alle onderdelen, en de binding (sha256 van de kern zonder toelichting, recordversie, contractversie). Een vorige uitkomst gaat naar `int01_beoordeling_history`. Lezen geeft `applied: false` met reden als de kern of contractversie niet meer overeenkomt. Export: JSON (bulk en enkel, onder `validatie`), CSV/Excel-kolom `int01_beoordeling` op UITGEBREID en COMPLEET, TXT (bulk en enkel) leesbaar. Geen nieuwe databasekolom en geen wijziging van het 2.1.0-resultaatcontract. Grenzen: records van vóór DEF-770 hebben pas na de eerstvolgende gewone schrijfactie een uitkomst (tot dan: ‘niet beoordeeld’ in de enkele TXT, lege cel elders); de enkele CSV en het BASIS-niveau exporteren, net als het bronbewijs, geen validatievelden. De UI toont de opgeslagen uitkomst nog niet apart; bij herladen toetst zij opnieuw met dezelfde deterministische functie.
- **Beheerde registratie.** Omdat elk nieuw record nu een beheerde INT-01-sleutel draagt, weigert de persistentielaag een ruwe niet-JSON-`generation_prompt_data`-schrijfactie voortaan voor alle nieuwe records (eerder alleen bij beheerde keuze- of ESS-03-gegevens). Er is geen productieroute die zo schrijft; twee bestaande tests met die premisse zijn omgezet naar een record van vóór DEF-770.
- **Skills.** De centrale skills `definitie-toetsregels` en `definitie-nederlandse-definities` zijn niet aangepast (buiten deze worktree); hun INT-01-rijen lopen achter op de app-instructie.
- **Menselijke gebruikersproef en herstel (DEF-638)** vallen buiten dit plan; zie synthese v3.
