# ESS-05 — beperkt bewijscontract `ess05-bewijsregels/4` (DEF-768)

**Status:** mechanisme voor een begrensde mechanismeproef. Geen actieve productketen: de standaard ESS-05-keten (assess/19, verify/4) gebruikt dit niet. Geen appgarantie.

Vervangt [v3](ess05-bewijsregels-contract-v3.md). v3 blijft ongewijzigd als historische bron (sha256 `57aa4c3ea03f3fdf5556c422e8190f4b74bec2fc0fe761e215e3da2c8a569e86`). R16 is op v3 uitgevoerd en blijft daarop gepind. De runner weigert R16 onder v4 fail-closed.

## Wijziging v3 → v4 (R16-herstel)

Grondslag: `logs/def768/bewijsregels-r16-uitvoerreview-result-v1.md` (sha256 `f4171e75…070bf`). De R16-proef mislukte, 0/3:

- **A/B.** Het model citeerde letterlijk geldige woorden die meer dan eens in de bron staan ("aan een medewerker", "de medewerker geeft de apparatuur daarna terug"), zonder unieke onderwerpbinding. Dit is terecht een `citaatfout`.
- **C.** Het doelpakket bevatte alleen fragmenten. De lokale bronscope (de inleiding "alleen voor deze beoordelingstest") ontbrak, net als de binding tussen "Uitleen:" en de teruggaafzin. Het sjabloon maakte van elk feit "voor elk geval van uitleen", ook als het model de context `algemeen` markeerde. De controle eiste ten onrechte letterlijk "elk/altijd", maar scope en binding ontbraken wel.

De reparatie is de kleinste die de betekenis vastlegt. Unieke vindplaats wordt niet versoepeld, er komt geen eerste-substringregel, en de app verzint geen onderwerp of scope.

| Onderdeel | Versie |
|---|---|
| Regelversie (`BEWIJSREGELVERSIE`) | van `/3` naar `ess05-bewijsregels/4` |
| Interpretatieschema | ongewijzigd: `ess05-interpretatie/2` |
| Prompt | van `/1` naar `ess05-interpretatie-prompt/2` |
| Render | ongewijzigd: `ess05-bewijsregels-render/2` |
| Lokale controle (`Ess05LocalVerificationService`, R15-gepind) | ongewijzigd |

Drie wijzigingen:

1. **Onderwerpbinding in bronnen met meerdere begrippen (§3 punt 2, nieuw).** Soms noemt een bron meer dan één geregistreerd begrip (het doelbegrip of een buurterm). Dan moet elk broncitaat voor onderwerp X de naam van X bevatten en geen andere geregistreerde naam; anders volgt een `onderwerpfout`.
   - Een naam telt als hij als woord(begin) voorkomt, hoofdletterongevoelig.
   - Noemt een bron hooguit één begrip, dan geldt de eis niet.
   - De eis geldt niet voor de buurbeschrijving en de bedoelde betekenis.
   - Gevolg: een Verhuur-passage bewijst geen Uitleen, een losse teruggaafzin zonder "Uitleen" wordt geweigerd, en een citaat moet het onderwerp plus de zin waarnaar een verwijzing terugwijst behouden.
2. **Reikwijdte en domein in de controlepakketten (§5).**
   - Een feit luidt "voor {begrip} geldt …", niet meer "voor elk geval van {begrip} geldt …".
   - Een eenheid met een positief feit (alles behalve `onbesproken`, of een deelgroep) krijgt een kop. Die kop citeert de volledige tekst van elk gebruikt materiaal plus de vastgelegde context, en eist:
     - binnen dat materiaal en de vastgelegde context, niet daarbuiten;
     - elk feit is een bepaling in dat materiaal, geen enkel voorval en geen voorwaardelijke afspraak, tenzij het feit zijn voorwaarde zelf noemt.
   - Het contextveld van het model kan het vastgelegde domein niet meer laten vallen: de context wordt altijd geciteerd.
   - `onbesproken` blijft de strenge volledigheidscontrole: "het volledige geciteerde materiaal … zegt over {begrip} niets over … of het tegendeel".
3. **Prompt /2.**
   - `bevestigd` betekent: volgens een bepaling in het materiaal geldt het kenmerk voor elk geval van dat onderwerp binnen het materiaal. Een enkel voorval of een voorwaardelijke afspraak is geen bepaling.
   - Elk citaat staat precies één keer in zijn materiaal.
   - In een bron met meerdere begrippen citeert het model een samenhangende passage met de naam van het onderwerp ('Uitleen: …'), inclusief de zin waarnaar een verwijzing terugwijst, en zonder de naam van een ander begrip. Het kort nooit in tot woorden die ook elders staan.

**Bekende grenzen (fail-closed, nooit een onterechte pass):**

- Een citaat dat beide namen moet noemen, zoals de rol-overlap "een werknemer kan ook lener zijn", wordt geweigerd. Overlap moet via het kenmerk worden geciteerd.
- Een verbogen of samengestelde naam telt niet als naam; "uitlenen" is bijvoorbeeld niet "uitleen". Dan geeft de regel een `onderwerpfout`. Als de bron daardoor hooguit één begrip noemt, geldt de eis niet.
- Of de controle een bepaling werkelijk onderscheidt van een voorval of voorwaarde, blijft een modeloordeel (§7).

De rest van dit contract is gelijk aan v3. Waar v4 iets toevoegt, staat dat hieronder gemarkeerd.

Code:
- `src/domain/ess05/bewijsregels.py`: feiten, geldigheid, regels en weergave; pure domeinlogica.
- `src/services/validation/ess05_bewijsregel_service.py`: broninterpretatie en gebonden controle.

## 1. Taakverdeling

| Wie | Doet |
|---|---|
| Model | interpreteert bronnen tot getypeerde feiten (`ess05-interpretatie/2`) |
| Aparte, geïsoleerde controle | toetst per onderwerp of die feiten door hun eigen citaten gedragen worden, binnen het gebonden materiaal en de vastgelegde context |
| Vaste code | controleert eerst alle geldigheid en dekking, en past pas daarna de regels toe |
| Renderer | bouwt de uitleg uitsluitend uit het regelresultaat |

Er is geen vrij conclusieveld en geen zelf ingevulde geldigheidsvlag. Een onbekend veld is `error`.

## 2. Wat het model levert

Ongewijzigd ten opzichte van v3 §2 (schema `ess05-interpretatie/2`). De betekenis van `bevestigd` en `ontkend` is aangescherpt tot een bepaling in het materiaal (prompt /2). Een voorval of een voorwaardelijke afspraak is geen bepaling.

## 3. Geldigheid (K1): alles vóór enige inhoudelijke aggregatie

Zoals v3 §3, met in punt 2 een extra eis:

2. **Citaten**:
   - elk citaat staat precies één keer letterlijk in het aangewezen materiaal (`citaatfout`, ongewijzigd);
   - het materiaal hoort bij het onderwerp (`onderwerpfout`): doel = bedoelde betekenis + bronnen, níet de definitie; buur/deelgroep = eigen buurbeschrijving + bronnen + bedoelde betekenis;
   - de beschrijving van een andere buur is fout;
   - **v4:** noemt een bron meer dan één geregistreerd begrip, dan noemt een broncitaat voor onderwerp X de naam van X en geen andere geregistreerde naam (`onderwerpfout`). Dit wordt gecontroleerd ná de unieke vindplaats, dus een herhaald kort citaat blijft een `citaatfout`.

De overige punten 1 en 3–11 zijn ongewijzigd.

## 4. Regels (alleen op een geldig oordeel)

Ongewijzigd ten opzichte van v3 §4.

## 5. Controle van de interpretatie (broninterpretatie, geen volledigheidscertificaat)

Per onderwerp één geïsoleerde materiaalclaim via de bestaande `Ess05LocalVerificationService`. Die dienst en haar systeemprompt zijn ongewijzigd (R15-gepind). De uitspraak komt uit vaste sjablonen; elk feit noemt zijn eigen citaat (B1, B2, …).

| Eenheid | Wat getoetst wordt | Citaten |
|---|---|---|
| `kern` | ongewijzigd | volledige definitie |
| `doel` | elk doelfeit als bepaling binnen het gebonden materiaal en de vastgelegde context | eigen citaten; **v4:** bij een positief feit ook de volledige tekst van elk gebruikt materiaal plus de context; volledig relevant materiaal bij `onbesproken` |
| `buur:<id>` | elk feit van de hele buur en van zijn deelgroepen, plus hun beschrijving | idem |

**Sjablonen (v4):**

- Kop, alleen bij een positief feit: "Binnen het gebonden materiaal en de vastgelegde context (B…), niet daarbuiten, is elk feit hieronder over {begrip} een bepaling in dat materiaal: geen enkel voorval en geen voorwaardelijke afspraak, tenzij het feit zijn voorwaarde zelf noemt."
- Feit: "voor {begrip} geldt {kenmerk}[ niet][, alleen onder de voorwaarde …] (B…)". Voor een deelgroep: "voor de deelgroep '…' van {begrip} geldt …".
- `gemengd` en `deels`: als v3, zonder het contextzinsdeel (het domein staat in de kop).
- `onbesproken`: "het volledige geciteerde materiaal (B…) zegt over {begrip} niets over {kenmerk} of het tegendeel", ongewijzigd streng. Zonder positief feit komt er geen kop.

Verder geldt:

- **Wat de controle níet doet.** Zij certificeert geen volledigheid buiten het materiaal en geen afgrenzing of conclusie; dat doen de regels. Een positief feit claimt geen universaliteit buiten het gebonden materiaal.
- **Leeg bereik.** Ongewijzigd.

## 6. Weergave (`ess05-bewijsregels-render/2`)

Ongewijzigd ten opzichte van v3 §6.

## 7. Resterende semantische afhankelijkheid (K3)

| Wat | Hoe gecontroleerd | Garantie |
|---|---|---|
| Letterlijke en unieke citaten, onderwerpmateriaal, **onderwerpbinding in bronnen met meerdere begrippen (v4)**, tekstdekking, bewijsdoelen, consistentie, bereik, regels, **scope en context in de controlepakketten (v4)** en weergave | vaste code | deterministisch |
| Juiste typering per fragment; juiste lezing van bron en buur; `onbesproken` over het volledige materiaal; **of een passage een bepaling is en geen voorval of voorwaardelijke afspraak (v4)**; of het model een voorwaarde of ontkenning in de gekozen passage correct meldt | geïsoleerde LLM-controle (§5), zelfde model | geen onafhankelijkheid van modelfouten; niet bewezen |
| Of het model onder prompt /2 benoemde, unieke passages kiest | alleen via de geldigheidscontrole: een fout citaat geeft `citaatfout`/`onderwerpfout` | niet bewezen (fail-closed) |
| Of de deelgroepen alle relevante variaties tonen; voorwaardelijke doeleisen | als v3 | niet bewezen |

**Offline bewijs** gebruikt vooraf vastgelegde, gecontroleerde feiten plus de ongewijzigde R16-antwoorden als regressiebron. Synthetisch gecorrigeerde bindingsvarianten zijn geen modeluitvoer. Dit bewijst de regels en de pakketinhoud, niet de modelinterpretatie.

**Historie blijft staan.** De R16-invoer, -uitvoer, -freeze, het grootboek en de resultaten blijven ongewijzigd. Onder v4 zijn de historische A/B/C-antwoorden al in de geldigheidsfase ongeldig (`onderwerpfout`); de vastgelegde v3-uitslagen veranderen daardoor niet.
