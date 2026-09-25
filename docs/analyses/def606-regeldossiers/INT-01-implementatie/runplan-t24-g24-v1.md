# INT-01 (DEF-770) — runplan T24 en G24 na implementatie

23 september 2026 · versie 1 · **niets hieronder is uitgevoerd.** Dit plan beschrijft hoe de effectproeven uit [synthese v3](../INT-01-verdieping/onderzoek-20260923/gedeeld/synthese-v3.md) (onderzoeksboom in de hoofdcheckout, niet getrackt) op de gebouwde variant worden gedraaid. Tot beide proeven zijn uitgevoerd en beoordeeld is de status: **geïmplementeerd; kwaliteitswinst nog niet vastgesteld.**

## 0. Wat al vaststaat (en wat niet)

| Bewijs | Bron | Claimgrens |
|---|---|---|
| Nulmeting op base `26f2374d`: 6 gevallen × 2 laadpaden, 12/12 statussen conform, exit 0 | onderzoek A, `proefuitkomsten-v2.json` | alleen status; geen redenen/spans |
| Serviceproef na implementatie: 10 gevallen (E01–E08, EB03, EB04) × 2 laadpaden, 20/20 conform vooraf vastgelegde verwachting, INT-01 nooit in `passed_rules`, offline-gate actief | [`proef-na-implementatie-v1.py`](proef-na-implementatie-v1.py), [`proefuitkomsten-na-implementatie-v1.json`](proefuitkomsten-na-implementatie-v1.json) | ontwerp-/regressiegevallen, **geen ongeziene eindset**; bewijst geen effect |
| Unit- en ketentests (segmentatie, beide laadpaden, opslag/herladen/export, UI-renderer, prompt) | `tests/unit/validation/test_def770_int01_zinsgrenzen.py`, `tests/unit/services/test_def770_int01_keten.py`, `tests/unit/services/prompts/test_def770_int01_promptnorm.py` | synthetische invoer; geen modeluitvoer, geen gebruikers |

## 1. Binding vóór elke uitvoering

Leg vast en bevries, in een manifest naast de uitkomsten:

- **oude variant:** `git archive 26f2374d302fc66fc0b12ed29dc34585f7c0a5c3` (record, evaluator, prompt);
- **nieuwe variant:** de gemergde DEF-770-commit (SHA), plus sha256 van `src/toetsregels/regels/INT-01.json`, `src/services/validation/evaluators/sentence_boundary.py` en `src/services/prompts/modules/json_based_rules_module.py`;
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

1. verwachte INT-01-status: `fail` (zekere tweede zin) · `review_required` met zinsstructuur `pass` (één zin) · `review_required` met onzekere grens · `not_evaluated` (leeg);
2. bij een grens: de verwachte grenspositie (tekenindex of passage) en de redencategorie (nieuw zinsbegin, afkorting-als-slot, citaat/haakjes, opmaak, kleine letter, getal);
3. bij een hele-kerncitaat: verwacht onderdeel `broncitaat` open.

Een vooraf zeker verwacht ‘onzeker’ is een geldig label. Onenigheid wordt geregistreerd; wat de adjudicator niet eenduidig kan maken blijft een **dispuut** en telt niet in de conformiteitsnoemer. Vervanging van een geval mag alleen vóór uitvoering, met een geval uit dezelfde klasse, en blijft zichtbaar in het manifest; achteraf herlabelen is uitgesloten.

**Verzegeling.** De maker levert `t24-gevallen.json` (id, stratum, begrip, tekst, bron/reden van het geval) en de beoordelaars `t24-referenties-{a,b}.json` plus `t24-adjudicatie.json`. De coördinator legt sha256 van alle vier vast vóór de run.

**Uitvoering.** Een runner naar het model van `proef-na-implementatie-v1.py`, uitgebreid met het inlezen van `t24-gevallen.json`, draait elk geval op oude en nieuwe variant via **beide laadpaden** (ToetsregelManager en CachedToetsregelManager), offline-gate actief, verse tijdelijke opslag. Per rij vastleggen: status, `passed_rules`-lidmaatschap, melding, reviewreden, alle onderdelen met `id/status/evidence/position/reason`.

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
- **Opslag van de deeluitkomst.** De gewone opslagroutes (generatie, bewerken) bewaren geen validatieresultaat; herladen toetst opnieuw. Alleen bij het toepassen van een bronvoorstel worden violations via `issues_uit_validatieresultaat` in `validation_issues` gezet en het volledige resultaat, inclusief de INT-01-onderdelen, als historie bij het voorstel bewaard (`src/database/definitie_crud.py`, `_registratie_na_toepassing`). Een tweede zin blijft in `validation_issues` en de export zichtbaar met passage; ‘één zin vastgesteld, compactheid en begrijpelijkheid open’ staat niet in `validation_issues` of de gewone exportvelden — maar er wordt ook nergens een geslaagd INT-01-oordeel opgeslagen. Dat in de export zichtbaar maken vraagt een nieuw opgeslagen veld of marker (contractbesluit).
- **Skills.** De centrale skills `definitie-toetsregels` en `definitie-nederlandse-definities` zijn niet aangepast (buiten deze worktree); hun INT-01-rijen lopen achter op de app-instructie.
- **Menselijke gebruikersproef en herstel (DEF-638)** vallen buiten dit plan; zie synthese v3.
