# ESS-05 — beperkt bewijscontract `ess05-bewijsregels/3` (DEF-768)

**Status:** mechanisme voor een begrensde mechanismeproef. Geen actieve productketen: de standaard ESS-05-keten (assess/19, verify/4) gebruikt dit niet. Geen appgarantie.

Vervangt [v2](ess05-bewijsregels-contract-v2.md). v2 blijft ongewijzigd als historische reviewbron (sha256 `b0d7c292539a62aac7b6b02e225b41f0c498dad09e1030a0f5ba7e91d839747f`, gelijk aan `logs/def768/bewijsregels-contract-v2-snapshot.md`).

**Wijziging v2 → v3 (K4-rest, uit `logs/def768/bewijsregels-contractreview-result-v2.md`).** Onder v2 was een voorwaardelijke doeleis toegestaan, maar telde ze niet mee in `d_F`. Daardoor kon een groep onterecht `gedeeld` worden en kon de splitsingsregel een onterechte `pass` geven.

Voorbeeld:
- doel: tijdelijke uitgifte, en bij storing is toestemming vereist;
- kern: tijdelijk;
- buur: storingsuitgifte zonder toestemming, zowel tijdelijk als permanent.

v3 kiest de kleine reparatie: elke onverwerkte voorwaardelijke doeleis is expliciet `buiten_bereik`, vóór elke inhoudelijke aggregatie (§3 punt 10). Er komt geen algemene voorwaardelogica. Wat wijzigt en wat niet:

| Onderdeel | Versie |
|---|---|
| Regelversie (`BEWIJSREGELVERSIE`) | van `/2` naar `ess05-bewijsregels/3` |
| Interpretatieschema | ongewijzigd: `ess05-interpretatie/2` |
| Prompt | ongewijzigd: `ess05-interpretatie-prompt/1` |
| Render | ongewijzigd: `ess05-bewijsregels-render/2` |

Schema, prompt en render blijven gelijk, omdat het model voorwaarden aan de doelkant ongewijzigd getrouw moet melden: de app beslist. R15-bindingen en historische labels blijven ongemoeid.

Correcties uit v2 (`logs/def768/bewijsregels-contractreview-result-v1.md`); K1–K3 zijn in review-v2 gesloten voor het proefbereik:
- K1: geldigheid vóór inhoud;
- K2: fail alleen met bewezen tegengeval;
- K3: woorddekking is alleen een tekstcontrole;
- K4: buurgroepen in plaats van "sommige", plus in v3 de voorwaardelijke doeleis als `buiten_bereik`.

Leidend onderzoek: `reports/DEF-768-AI-20260928-R15/gericht-oplossingsonderzoek-v1.md`.

Code:
- `src/domain/ess05/bewijsregels.py`: feiten, geldigheid, regels en weergave; pure domeinlogica.
- `src/services/validation/ess05_bewijsregel_service.py`: broninterpretatie en gebonden controle.

## 1. Taakverdeling

| Wie | Doet |
|---|---|
| Model | interpreteert bronnen tot getypeerde feiten (`ess05-interpretatie/2`) |
| Aparte, geïsoleerde controle | toetst per onderwerp of die feiten door hun eigen citaten gedragen worden |
| Vaste code | controleert eerst alle geldigheid en dekking, en past pas daarna de regels toe |
| Renderer | bouwt de uitleg uitsluitend uit het regelresultaat |

Er is geen vrij conclusieveld en geen zelf ingevulde geldigheidsvlag. Een onbekend veld is `error`.

## 2. Wat het model levert

| Veld | Inhoud |
|---|---|
| `kern.bovenbegrip` | letterlijk citaat uit de definitie |
| `kern.kenmerken[]` | `id` K…, `kenmerk`, `waarde`, `citaat` (letterlijk uit de definitie) |
| `buiten_kern[]` | `id` M…, `kenmerk`, `waarde`: kenmerken van de bedoelde doelbetekenis die de definitie níet uitdrukt |
| `buurgroepen[]` | `id` G…, `buur` (buur-ID), `omschrijving`, `citaten[]`: beschreven deelgroepen van een verwant begrip, bijvoorbeeld "permanente betaalde verhuur" of "verhuur bij storing" |
| `buiten_bereik[]` | `citaat`, `reden`: constructies die het model niet in dit contract kan typeren, zoals een relatie met een gedeeld argument, een disjunctie of een uitzondering |
| `antwoorden[]` | `kenmerk_id`, `onderwerp`, `toestand`, `voorwaarden[]`, `context`, `citaten[]` |

- **`onderwerp`** is `doel`, een buur-ID (de hele buur, door de app bepaald) of een G-id (deelgroep).
- **`toestand`**, afhankelijk van het onderwerp:

| Onderwerp | Toegestane toestanden |
|---|---|
| doel en deelgroep | `bevestigd`, `ontkend`, `onbesproken` |
| hele buur | daarnaast `gemengd` (het materiaal toont gevallen met én zonder het kenmerk) en `deels` (alleen voor een deel van de gevallen iets vastgelegd) |

- **Voorwaarden** mogen in het schema alleen aan de doelkant. Aan de buurzijde hoort een voorwaarde in een eigen deelgroep; zij wordt nooit een onvoorwaardelijk kenmerk.
- **Verwerking aan de doelkant (v3).** Een voorwaardelijk doelantwoord is alleen verwerkt als hetzelfde kenmerk ook onvoorwaardelijk dezelfde toestand heeft; de voorwaarde voegt dan niets toe. Elk ander voorwaardelijk doelantwoord, bevestigd of ontkend, is `buiten_bereik` (§3 punt 10).

## 3. Geldigheid (K1): alles vóór enige inhoudelijke aggregatie

Elke fout hieronder is `error`. Er volgt dan geen fail, open of pass: `error` gaat vóór alle inhoud.

1. **Schema**: exacte velden, unieke ID's, bekende toestanden en contexten.
2. **Citaten**:
   - elk citaat staat precies één keer letterlijk in het aangewezen materiaal (`citaatfout`);
   - het materiaal hoort bij het onderwerp (`onderwerpfout`): doel = bedoelde betekenis + bronnen, níet de definitie; buur/deelgroep = eigen buurbeschrijving + bronnen + bedoelde betekenis;
   - de beschrijving van een andere buur is fout.
3. **Context** `andere` is niet combineerbaar (`contextfout`).
4. **Bewijsdoelen van de app**: elk kenmerk (K en M) × {doel, elke buur, elke deelgroep} heeft een antwoord. Anders `doeldekking_onvolledig`.
5. **Tekstdekking van de kern (alleen tekstcontrole).**
   - Wat de code eist: bovenbegrip en kenmerkcitaten staan elk precies één keer in de definitie en dekken samen elk woord, behalve het voegwoord "en".
   - Wat het oplevert: een niet-gedekt woord (verborgen conjunctie, "of", …) is `kerndekking_onvolledig`.
   - Wat het níet bewijst: dat de kenmerken het fragment volledig of juist weergeven (zie §5 en §7).
6. **Vorm van `onbesproken`**: geen eigen citaten, en het is het enige antwoord voor dat doel. De app bindt zelf het volledige relevante materiaal.
7. **Ontbrekende dekking.** Een `onbesproken`- of `deels`-antwoord over een onderwerp waarvan relevant materiaal alleen als uittreksel is gebonden, is `dekking_ontbreekt`. Dat is nooit een bewezen informatiegebrek, ook niet als een ander kenmerk wel afgrenst.
8. **Consistentie van deelgroepen met de hele buur:**
   - bij `bevestigd`/`ontkend`/`onbesproken` op buurniveau heeft elke deelgroep dezelfde toestand;
   - bij `gemengd` bestaan deelgroepen met `bevestigd` én met `ontkend`;
   - bij `deels` bestaat minstens één deelgroep met een vastgestelde toestand;
   - anders `inconsistent`.
9. **Betekeniskenmerk** (M) zonder `bevestigd` doelantwoord: `betekenisfout`.
10. **Buiten bereik** is elk van deze gevallen:
    - een niet-lege `buiten_bereik`;
    - een onverwerkte voorwaardelijke doeleis (v3, §2);
    - meer dan één `gemengd` kenmerk bij dezelfde buur (combinaties van variaties worden niet ondersteund).

    Dat gebeurt expliciet en wordt nooit stil omgezet in open, fail, pass of "onbekend". De foutmelding, en daarmee de weergave, bewaart per voorwaardelijke eis:
    - kenmerk-id, kenmerk en waarde;
    - toestand;
    - de voorwaardetekst;
    - elk citaat met materiaal-ID en letterlijke tekst.

    Voorbeeld: `M1 (toestemming: vereist) is in de doelbetekenis bevestigd alleen onder de voorwaarde bij storing [source:…: «Bij storing is … vereist»]`.
11. **Controle van de interpretatie** (§5): elke controle die niet `supported` is, geeft `semantische_controle_mislukt`.

## 4. Regels (alleen op een geldig oordeel)

Per kenmerk F en onderwerp g geldt de toestand `s_F(g)`. Bevestiging én ontkenning samen geeft `conflict`.

- **Vereist door het doel** (`d_F`): alleen `bevestigd`, zonder voorwaarden en zonder conflict. Sinds v3 bereikt geen onverwerkte voorwaardelijke doeleis deze fase meer: een eis die alleen voorwaardelijk geldt, kan dus niet meer stil buiten `d_F` vallen en een groep `gedeeld` maken.
- Per groep g (de hele buur of een deelgroep):

| Begrip | Definitie |
|---|---|
| `binnen_kern(g)` | elk kernkenmerk `bevestigd` (bewezen) |
| `buiten_doel(g)` | er is een F met `d_F` en `s_F(g) = ontkend` (bewezen) |
| `afgegrensd(g)` | er is een kernkenmerk K met `d_K` en `s_K(g) = ontkend` |
| `gedeeld(g)` | `binnen_kern(g)` en elk vereist F `bevestigd` |

Uitkomst per buur, in deze volgorde:
1. **niet_onderscheiden**: een groep met `binnen_kern` én `buiten_doel`. Dat is een beschreven tegengeval: binnen de hele kern, buiten de doelbetekenis. Het is ook `fail` als een andere deelgroep wel afgegrensd is (K4).
2. **onderscheiden**: de hele buur is afgegrensd.
3. **onderscheiden (met overlap)**, via splitsing. Dit mag alleen als:
   - de hele buur op precies één vereist kernkenmerk K* `gemengd` is;
   - op alle andere kenmerken uniform (`bevestigd`/`ontkend`/`onbesproken`);
   - elke deelgroep afgegrensd of gedeeld is.

   De deelgroepen dekken dan elk buurgeval (wel of niet K*, de rest uniform).
4. **open**, in alle andere gevallen, met de onbesliste kenmerken. Twee gevallen:
   - de buur is geheel gedeeld: "geen buurgeval buiten het doel aangetoond";
   - een kernkenmerk is onbekend of conflicterend. Dan is geen afgrenzing bewezen en ook geen niet-afgrenzing (K2). Voorbeeld: een betaalde buur met onbekende duur, terwijl de kern alleen tijdelijk noemt, blijft open en wordt geen fail.

Geheel (alleen na §3):
- geen kernkenmerk → `fail`;
- een buur niet_onderscheiden → `fail` (fail vóór open, binnen een geldig oordeel);
- een buur open → `review_required`;
- anders `pass`.

Niet ondersteund en dus niet afgeleid:
- insluiting van buurgevallen in het doel;
- relaties met gedeelde argumenten (bijvoorbeeld "dezelfde aanvraag", "dezelfde gebeurtenis") tussen afzonderlijke kenmerken;
- disjunctie en uitzonderingen in de kern;
- voorwaardelijke doeleisen (v3: expliciet `buiten_bereik`, geen toepasselijkheidsoordeel per groep);
- combinaties van meer dan één gemengd kenmerk;
- relaties tussen buren.

## 5. Controle van de interpretatie (broninterpretatie, geen volledigheidscertificaat)

Per onderwerp één geïsoleerde materiaalclaim via de bestaande `Ess05LocalVerificationService`: een eigen verzoek met alleen de uitspraak, het toetsprincipe en de eigen citaten. De uitspraak komt uit vaste sjablonen; elk feit noemt zijn eigen citaat (B1, B2, …).

| Eenheid | Wat getoetst wordt | Citaten |
|---|---|---|
| `kern` | per fragment: drukt het precies dit kenmerk uit, met elke beperking, ontkenning, voorwaarde en relatie in dat fragment; en per M-kenmerk: drukt de definitie het niet uit, ook niet anders geformuleerd | volledige definitie |
| `doel` | elk doelfeit | eigen citaten; volledig relevant materiaal bij `onbesproken` |
| `buur:<id>` | elk feit van de hele buur en van zijn deelgroepen, plus hun beschrijving | idem |

- **Wat de controle níet doet.** Zij certificeert geen volledigheid ("geen ander kenmerk") en geen afgrenzing of conclusie; dat doen de regels.
- **Leeg bereik.** Een `onbesproken` over een onderwerp zonder enig relevant materiaal stelt de app zelf vast; dat gaat niet naar de controle.

## 6. Weergave (`ess05-bewijsregels-render/2`)

- Alleen begrensde zinnen per buur en groep: afgrenzend, gedeeld, tegengeval, onbekend, conflict.
- Steeds de bereikzin: "Bereik: beperkte bewijsregels over het aangeleverde, gebonden materiaal; geen volledige ESS-05-beoordeling van de app."
- Onbekend wordt "stelt het aangeleverde materiaal niet vast … geen ontkenning".
- Nooit "valt binnen" of "geen geval buiten".

## 7. Resterende semantische afhankelijkheid (K3)

| Wat | Hoe gecontroleerd | Garantie |
|---|---|---|
| Letterlijke citaten, onderwerpmateriaal, tekstdekking, bewijsdoelen, consistentie, bereik, regels en weergave | vaste code | deterministisch |
| Juiste typering per fragment; juiste lezing van bron en buur (bijvoorbeeld "permanent" als niet tijdelijk, "zonder vergoeding" als kosteloos); `onbesproken` over het volledige materiaal | geïsoleerde LLM-controle (§5), zelfde model | geen onafhankelijkheid van modelfouten |
| Of de deelgroepen alle relevante variaties tonen; of het model een relatie of beperking als `buiten_bereik` herkent of juist meeneemt in de waarde | alleen via de fragmentcontrole en gemengd-consistentie | niet bewezen |
| Of het model een voorwaardelijke doeleis als voorwaarde meldt, in plaats van haar weg te laten of onvoorwaardelijk te maken | alleen via de doelcontrole (§5), die elk doelfeit met zijn eigen citaat toetst | niet bewezen; de v3-regel werkt pas als de voorwaarde gemeld is |

**Offline bewijs** gebruikt vooraf vastgelegde, gecontroleerde feiten. Dat bewijst de regels, niet de modelinterpretatie; die wordt afzonderlijk in de mechanismeproef getest.

**Historie blijft staan.** Historische R15-invoer, -uitvoer, -labels en -hashes blijven ongewijzigd:
- N1 was een statusgrens;
- N2 blijft een echte ongeldige afleiding;
- de motivering van P2 was dubbelzinnig.
