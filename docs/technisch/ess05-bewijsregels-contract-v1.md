# ESS-05 — beperkt bewijscontract `ess05-bewijsregels/1` (DEF-768)

> **Vervangen door [`ess05-bewijsregels-contract-v2.md`](ess05-bewijsregels-contract-v2.md)** na de onafhankelijke contractreview (`logs/def768/bewijsregels-contractreview-result-v1.md`). Deze v1 bevat vier aangetoonde normafwijkingen en blijft alleen als historie bewaard; zij is niet geïmplementeerd.

**Status:** mechanisme, geen actieve productketen. De standaard ESS-05-keten (assess/19, verify/4) gebruikt dit contract nog niet. Leidende onderbouwing: `reports/DEF-768-AI-20260928-R15/gericht-oplossingsonderzoek-v1.md` en `logs/def768/r15-logica-heronderzoek-result-v1.md`.

Code:
- `src/domain/ess05/bewijsregels.py`: feiten, dekking, regels en renderer. Pure domeinlogica.
- `src/services/validation/ess05_bewijsregel_service.py`: broninterpretatie en gebonden controle.

## 1. Waarom

In fase A zag de verifier alleen zijn eigen route, maar besliste hij nog zelf of een samengestelde conclusie volgt. Zo werd een ongeldige gevolgtrekking geaccepteerd (L-N2): "geen verhuurgeval buiten uitleen", afgeleid uit genus plus onbekende kosten.

In dit contract doet vaste code de afleiding. Het model interpreteert alleen bronnen tot getypeerde feiten. Een aparte, geïsoleerde controle toetst die interpretatie. De uitleg wordt uit het regelresultaat opgebouwd.

## 2. Wat het model levert (`ess05-interpretatie/1`)

Het antwoord is één gesloten JSON-object. Er is geen vrij conclusieveld en geen `geldig`-vlag; een onbekend veld is `error`.

| Veld | Inhoud |
|---|---|
| `kern.bovenbegrip` | letterlijk citaat uit de definitie |
| `kern.kenmerken[]` | `id` (K1…), `kenmerk` (aspect, bijvoorbeeld duur), `waarde` (bijvoorbeeld tijdelijk), `citaat` (letterlijk uit de definitie) |
| `buiten_kern[]` | `id` (M1…), `kenmerk`, `waarde`: kenmerken van de bedoelde betekenis van het doel die de definitie níet uitdrukt |
| `antwoorden[]` | `kenmerk_id`, `onderwerp` (`doel` of een buur-ID), `toestand`, `kwantificatie`, `voorwaarden`, `context`, `citaten[]` (`material_id`, `citaat`) |

- `toestand` is `bevestigd` (het kenmerk geldt), `ontkend` (het tegendeel geldt) of `onbesproken` (het relevante materiaal zegt er niets over).
- `kwantificatie` is `alle` of `sommige` bij bevestigd/ontkend, en `null` bij onbesproken.
- `context` is `algemeen`, `zaakcontext` of `andere`.

## 3. Wat de app bepaalt en in code controleert

**Bewijsdoelen.** Voor elk kenmerk (K én M) × {doel, elke buur uit de door de app bevestigde burenlijst} is minstens één antwoord verplicht. Een ontbrekend doel, een onbekend kenmerk of een onbekend onderwerp is `error` (`doeldekking_onvolledig` of `schemafout`). Het model kan geen doel weglaten en geen buur toevoegen.

**Kerndekking.** Bovenbegrip en kenmerkcitaten moeten elk precies één keer letterlijk in de definitie staan. Samen moeten ze elk woord van de volledige definitie dekken. Alleen het voegwoord "en" en leestekens mogen daarbuiten vallen.
- Een niet-gedekt woord (verborgen extra conjunctie, "of", "tenzij", …) is `error` (`kerndekking_onvolledig`).
- Daardoor is "kenmerk X ontbreekt in de kern" alleen afleidbaar uit een decompositie van de volledige definitie, nooit uit een fragment.
- Of een woord ontbreekt telt niet. Of een kenmerk ontbreekt volgt uit de getypeerde (kenmerk, waarde): "zonder vergoeding" kan hetzelfde kenmerk als "kosteloos" zijn. Die gelijkstelling is interpretatie en wordt gecontroleerd (§5).

**Onderwerp en bronbereik.** Wat telt als relevant materiaal:

| Onderwerp | Relevant materiaal |
|---|---|
| doel | bedoelde betekenis (`meaning`) + bronnen (`source:*`); de definitie zelf telt níet als bewijs voor de doelbetekenis |
| buur b | `neighbour:b` + bronnen + bedoelde betekenis; de beschrijving van een ándere buur of de definitie is `onderwerpfout` |

Regels bij de antwoorden:
- **Citaten** staan precies één keer letterlijk in het aangewezen materiaal (`citaatfout`).
- **`onbesproken`** heeft geen citaten en is het enige antwoord voor dat doel. De app bindt zelf het volledige relevante materiaal; het model kan dat bereik niet verkleinen.
- **Onvolledig gebonden materiaal.** Is een relevant materiaal alleen als uittreksel gebonden (`onvolledig`), dan krijgt `onbesproken` de status `dekking_ontbreekt`. Het wordt dus nooit een bewezen informatiegebrek.
- **Context `andere`**: een feit uit een andere context is niet combineerbaar (`contextfout`).
- **Betekeniskenmerken.** Een M-kenmerk vraagt een `bevestigd` doelantwoord; anders is het niet als betekeniskenmerk onderbouwd (`betekenisfout`).

## 4. Regels

Per kenmerk en onderwerp komen de antwoorden samen tot één toestand:
- **onbesproken**; of **dekking_ontbreekt** als relevant materiaal onvolledig is;
- **conflict**: zowel bevestigd als ontkend;
- **ontkend_alle**: ontkend, `alle`, zonder voorwaarden;
- **ontkend_sommige**: overige ontkenningen; een voorwaarde betekent: niet elk geval;
- **bevestigd_alle**: bevestigd, `alle`, zonder voorwaarden;
- **bevestigd_deels**: overige bevestigingen.

Doelbetekenis vereist het kenmerk = `bevestigd_alle` aan de doelkant.

Per buur en kernkenmerk K. Alleen hetzelfde kenmerk, dezelfde context (algemeen/zaakcontext) en de doelkant zonder voorwaarden worden gecombineerd.

| Doelkant | Buurkant | Aspect |
|---|---|---|
| vereist | ontkend_alle / ontkend_sommige | **afgrenzend** (bij `sommige` blijven gedeelde gevallen mogelijk: overlap) |
| – | bevestigd_alle | **gedeeld** |
| overig | overig | **onbeslist**: `onbekend`, `conflict`, `dekking_ontbreekt` of `doelbetekenis_niet_vastgesteld` |

Per buur en betekeniskenmerk M: doel vereist en buur ontkend geeft **mist_in_kern**. Volgens bron of betekenis vallen buurgevallen dan buiten het doel, maar de kern drukt dit kenmerk niet uit.

Uitkomst per buur, in deze volgorde:
1. **onderscheiden**: minstens één afgrenzend kernkenmerk.
2. **niet_onderscheiden**: minstens één `mist_in_kern`.
3. **fout**: een aspect van K of M met `dekking_ontbreekt`.
4. **open**: een onbeslist aspect, of niets anders dan gedeelde kenmerken ("geen afwijkend buurgeval aangetoond").

Geheel, met de bestaande prioriteit:
- interpretatiefout → `error`;
- geen kernkenmerk → `fail`;
- een buur niet_onderscheiden → `fail`;
- een buur fout → `error`;
- een buur open → `review_required`;
- anders `pass`.

Een bewezen fail gaat dus vóór open. Een onbekend kenmerk blokkeert een ander bewezen onderscheid niet.

Bewust níet ondersteund:
- insluiting ("buurgevallen vallen binnen het doel");
- disjunctie of uitzonderingen in de kern;
- voorwaardelijke doelvereisten (worden `doelbetekenis_niet_vastgesteld`);
- relaties tussen buren;
- een verplicht expliciet uitgesloten exemplaar.

Een samengestelde conclusie van het model bestaat in dit contract niet.

## 5. Controle van de interpretatie

De app bouwt per onderwerp één materiaalclaim en toetst die met de bestaande `Ess05LocalVerificationService`. Dat is een eigen verzoek met alleen de uitspraak, het toetsprincipe en de eigen citaten. De uitspraak komt uit vaste sjablonen, niet uit modeltekst.

| Eenheid | Uitspraak | Citaten |
|---|---|---|
| `kern` | bovenbegrip + precies deze kenmerken, geen andere (ook niet de M-kenmerken) | volledige definitie |
| `doel` | alle doelantwoorden | hun citaten + volledig relevant materiaal bij `onbesproken` |
| `buur:<id>` | alle antwoorden over die buur | idem |

- **Volgorde.** Controles lopen pas als de voorlopige uitkomst geen `error` is.
- **Eerste afwijking.** Stoppen bij de eerste controle die niet `supported` is. Het resultaat wordt dan `error` (`semantische_controle_mislukt`). Een afhankelijke conclusie vervalt zo altijd samen met een afgewezen premisse.
- **Geen doorbreking.** Een model dat alles `supported` noemt, verandert niets aan de regels uit §4. Een ongeldige combinatie wordt al in code geweigerd.
- **Leeg bereik.** Een `onbesproken` over een onderwerp zonder enig relevant materiaal is door de app vastgesteld en gaat niet naar de controle.

## 6. Uitkomst en weergave

- `error`: de modeluitvoer of dekking is onbruikbaar; er is geen oordeel over de definitie.
- `review_required`: het informatiegebrek is correct vastgesteld.
- **Weergave** (`ess05-bewijsregels-render/1`): uitsluitend begrensde zinnen per buur (afgrenzend, gedeeld, onbekend, conflict, mist in de kern), steeds met de bereikzin "Bereik: beperkte bewijsregels over het aangeleverde, gebonden materiaal; geen volledige ESS-05-beoordeling van de app."
- **Taalgrens.** Onbekend wordt "stelt het aangeleverde materiaal niet vast", nooit "ontbreekt" of "valt binnen".

## 7. Grenzen

- **Correct rekenen is geen correcte extractie.** Een verkeerd geïnterpreteerd feit geeft een geldige maar inhoudelijk verkeerde uitkomst. De controle per onderwerp verkleint dat risico, maar gebruikt hetzelfde model en is dus geen onafhankelijkheid van modelfouten.
- **Kenmerk-labels** worden alleen binnen één interpretatie vergeleken, via ID's. Er is geen woordvergelijking tussen interpretaties.
- **Onvolledig gebonden materiaal** (uittreksel) kan geen informatiegebrek bewijzen. Een positief onderscheid uit het wel gebonden deel blijft mogelijk.
- **Historie blijft staan.** Historische R15-invoer, -uitvoer, -labels en -hashes blijven ongewijzigd. N1 was een statusgrens, N2 een echte ongeldige afleiding, en de motivering van P2 was dubbelzinnig. Dit contract herlabelt niets.
