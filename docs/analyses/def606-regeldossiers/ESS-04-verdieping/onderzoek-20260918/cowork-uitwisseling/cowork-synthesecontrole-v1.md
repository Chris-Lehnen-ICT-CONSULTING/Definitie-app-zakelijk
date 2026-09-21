# cowork-synthesecontrole-v1 — gerichte controle op de synthese

Claude Cowork, 18 september 2026. Afsluitende synthesecontrole op `synthesepakket-v1/`, conform de opdracht gericht op **weglating, standpuntweergave en betekenisverlies**. Geen nieuwe onderzoeksronde, geen gebruikersbesluit, geen implementatie, geen wijziging aan enig eerder bestand.

## 1. Beoordeelde versies en integriteit

Alle negen bestanden uit `synthesepakket-v1/manifest.json` zijn aanwezig, leesbaar en hashgelijk — **9/9**, door mij herberekend:

| Bestand | SHA-256 | Oordeel |
|---|---|---|
| `synthesevoorstel-v2.md` | `64849f2580c4ebd52814828abbed7f279cd44a80ba331f727d8a4eb7f5b7527f` | gelijk |
| `instructievoorstellen-v3.md` | `bfc90f6b702dc51963ee7b52b77fe2a51f744291327468f11617d84abe63d05b` | gelijk |
| `casusregister-v2.md` | `df31d1f776014d85384d6798ba37410335c91933779f0ad9d16042f3c9da41c1` | gelijk |
| `casusindex-v2.json` | `b9dc0e40655fa76cf55126707c891f5c2a9c60717728da76b655d9747b91dbbe` | gelijk |
| `veldrollen-en-keten-v2.md` | `114a5ceac31c762b2e7df492262fe12afd9ea770be1b6e03be487d95c7096bc5` | gelijk |
| `bron-bewijsregister-v2.md` | `34f733f1976e929308c264f6a5a0010cbdf324438390f33c44e44ecc607ea476` | gelijk |
| `codex-reviewverwerking-v1.md` | `9419b4e72a688f4ea82c1f57ec3f3baa7614b800bbfd25ccf61241ada62e31c0` | gelijk |
| `skillvindplaatsen-verificatie-v1.json` | `ad2914fe39137410189d1e047b1b9f3b6bdf1ed5d466a50bd528a4e390bb5f8b` | gelijk |
| `cowork-proefbestanden-ontvangst-v1.json` | `e41cf1610d40b7063f728ba8e252a54aeba73d29dc5002b88056fad37604841d` | gelijk |

`manifest.json` draagt `"first_versions_unchanged": true`. Geverifieerd aan mijn kant: mijn zeven bestanden zijn onveranderd (`cowork-onderzoek-v1.md` `7f9138d1…07062708`, `cowork-toegang-v1.md` `32219d91…0747a74`, `cowork-toegang-v1-aanvulling-v1.md` `c6cb0c4f…cafdfb2e`, `cowork-review-op-codex-v1.md` `ee25c9e8…73da6a81bb`, `cowork-aanvulling-op-eigen-v1.md` `10bc145d…1e1c78eb`, `cowork-reviewverwerking-v1.md` `e804dac2…6807e93c`, plus de drie bewijsbestanden). De hashes in `cowork-proefbestanden-ontvangst-v1.json` komen exact overeen met mijn drie proefbestanden.

**Casusintegriteit:** 37 tabelrijen in `casusregister-v2.md`, 37 entries in `casusindex-v2.json`, geen index-ID zonder registerrij. 14 × `ESS04-C`, 23 × `E04-N`, 7 historische labels als alias — precies 37 unieke scenario's met zeven aliasparen. **Al mijn veertien ID's en hun invoerteksten zijn ongewijzigd aanwezig.** Geen enkele fixture is aangepast om een uitkomst passend te maken; waar een verwachting wijzigde, staat de grond erbij.

**Naleveringen en proef:** `nalevering3-manifest-v1.json` → `config/approval_gate.yaml` hashgelijk. `reviewproef/` vier bestanden hashgelijk aan `uitvoerbinding-v1.json`, stderr leeg, exit 0, 14/14 identiek aan mijn replica.

---

## 2. Eindoordeel

**Besluitrijp als onderzoeksvoorstel — met één te herstellen weglating (punt 3.1) en vier kleine correcties (3.2–3.5).** Geen van de vijf raakt de aanbevolen norm, de drie hoofdkeuzes of het bewijsregister. Ik vind geen standpuntvertekening, geen nieuwe normverzwaring en geen betekenisverlies in de overgenomen posities.

Wat ik uitdrukkelijk goed vind, omdat het in dit soort syntheses meestal misgaat: de twee posities over de besluitstatus van de ESS-01/02-uitzonderingen zijn **niet** stilgetrokken naar één formulering, en het verschil is benoemd mét de gelijke uitkomstaanbeveling. Dat is precies de eerlijke weergave die deze fase vraagt.

---

## 3. Concrete punten

### 3.1 Weglating — de weergave aan de gebruiker ontbreekt volledig (materieel)

**Bevinding.** Van mijn zes hoofdbevindingen is er één niet in het synthesepakket terechtgekomen: wat de gebruiker van ESS-04 te zien krijgt. Ik heb het hele pakket doorzocht op `validation_view`, `validation_renderer`, `_reden_met_passages`, "Vereist element herkend", "heuristiek" en `testable`: **geen enkele treffer in geen enkel bestand.**

Het gaat om drie samenhangende feiten uit `cowork-onderzoek-v1.md` §5.5 en §6.4, alle op commit `4cdb8ea43`:

1. `validation_view.py:734-739` toont de reviewreden bij ingeklapte details uitsluitend voor `rule_id in ("ESS-01", "ESS-02")`. ESS-04 valt daarbuiten en verschijnt alleen als kale code in de statusregel "🟠 Nog te beoordelen: …", zonder toetsvraag, zonder passage, zonder handelingsperspectief.
2. In dezelfde commit kregen ESS-01 en ESS-02 wél `_reden_met_passages` in `judgment_review.py`; ESS-04 krijgt nog steeds de kale `toetsvraag`. **Het sjabloon bestaat dus al in hetzelfde bestand.**
3. Twee dode plekken dragen nog de afgeschafte heuristiek: `validation_renderer.py:353` geeft voor `{"ESS-03","ESS-04","ESS-05"}` de pass-verklaring "Vereist element herkend (heuristiek)", en `modular_validation_service.py:1938` de suggestie bij `reason == "testable"` ("bijv. termijn of meetbare grens"). Beide zijn vandaag onbereikbaar omdat ESS-04 geen pass en geen violation produceert. Bij ESS-02 is ditzelfde patroon in deze commit wél opgeruimd, met een comment op de plek; ESS-04 is overgeslagen.

**Waarom dit telt.** `instructievoorstellen-v3.md` bevat wél de zeven gebruikersmeldingen — inclusief de leegtemelding die via R-07 is overgenomen — maar nergens staat *waar* die teksten terechtkomen, dat ESS-04 nu van de zichtbare route is uitgesloten, of dat er een werkend sjabloon van twee buurregels klaarligt. Zonder dat staat er een set teksten zonder aanhechtingspunt. Dossieronderdeel 8 (appgedrag) en de meldingensectie zijn hierdoor onvolledig, en het is tegelijk de goedkoopste concrete verbetering in het hele dossier.

**Voorgestelde correctie — toe te voegen aan `instructievoorstellen-v3.md`, direct boven "Gebruikersmeldingen":**

> **Vindplaats en aanhechting.** De meldingen hieronder hebben twee aanhechtingspunten in de huidige code.
> (a) `src/services/validation/evaluators/judgment_review.py`: `evaluate` geeft voor ESS-04 de kale `toetsvraag` door. ESS-01 en ESS-02 krijgen daar sinds `4cdb8ea43` een reden met letterlijk geciteerde passages via `_reden_met_passages`; ESS-04 kan op datzelfde sjabloon worden aangesloten met een eigen kop en passagevraag. Dit is een aansluiting op bestaande code, geen nieuw mechanisme.
> (b) `src/ui/components/validation_view.py`, de lus over `review_required`: de altijd-zichtbare reden is beperkt tot `rule_id in ("ESS-01", "ESS-02")`. Zolang ESS-04 daar niet bij staat, blijft hij ook met een verbeterde reden onzichtbaar bij ingeklapte details.
> **Op te ruimen bij dezelfde wijziging, omdat beide teksten het afgeschafte gedrag beschrijven:** `src/ui/components/validation_renderer.py:353` (`"ESS-04"` uit de verzameling `{"ESS-03","ESS-04","ESS-05"}` halen, met dezelfde soort comment als bij ESS-02) en de suggestie bij `reason == "testable"` in `src/services/validation/modular_validation_service.py:1938`. Beide zijn bij het huidige runtimecontract onbereikbaar; ze zijn een terugvalrisico bij een volgende wijziging en geen gemeten defect.

**Status:** weglating, geen tegenspraak. Herstelbaar met bovenstaande alinea; raakt geen enkele keuze of claim.

### 3.2 Twee onjuiste casusverwijzingen in `instructievoorstellen-v3.md`

**Bevinding.** Gecontroleerd tegen `casusregister-v2.md` (dat loopt van `E04-N01` t/m `E04-N23`):

- **T2, slotregel:** "Cases: non_numeric/ambiguous_measure/observable/empty; N01/N07/N09/**N24**/**N27**/N21/N23." `N24` en `N27` bestaan niet in het register.
- **G2, appvoorwaarde:** "Cases N03/N06/**N22/N23/N22**." `N22` staat er tweemaal.

**Voorgestelde correctie.** G2: dubbele `N22` verwijderen → "Cases N03/N06/N22/N23." Voor T2 gis ik niet naar de bedoeling, maar op de inhoud van T2 liggen twee scenario's voor de hand: "Een toepasbaar maar verkeerd criterium vraagt een afzonderlijke bevinding" ↔ **N14**, en "ontbrekend bewijs … afzonderlijk vastleggen" ↔ **N17**. Verificatie en keuze bij Codex.

Terzijde, redactioneel: dezelfde regels mengen labelvorm en nummervorm ("non_numeric, N03/14/18"). Eén schrijfwijze per verwijzing houdt de koppeling naar het register eenduidig.

### 3.3 De recordtoelichting laat de veldgrens open die de veldrollen wél trekken

**Bevinding.** `veldrollen-en-keten-v2.md` legt de grens scherp: "Essentiële noemer/populatie/beperking niet uitsluitend hier verstoppen. Methodische verduidelijking mag apart." De voorgestelde `toelichting` in N2 zegt alleen: "Leg meet- of beoordelingscontext vast wanneer die de uitkomst bepaalt; denk dan aan populatie of noemer, grensinclusie, referentietijd, dagconventie en toepasselijke bronversie." Waar die gegevens thuishoren staat er niet.

**Waarom dit telt.** Het regelrecord is productconfiguratie die zelfstandig gelezen wordt, zonder het veldrollendocument ernaast. "Leg vast" zonder plaatsbepaling is precies de lezing die casus `E04-N18` (bepalend kenmerk alleen in de toelichting) afkeurt. Dit is geen tegenspraak tussen de documenten, maar een plaatsingsverlies in het document dat het langst blijft staan.

**Voorgestelde correctie — één zin toevoegen aan de `toelichting` in N2, na "…toepasselijke bronversie.":**
> "Wat het begrip zelf begrenst hoort in de definitiekern; hoe je het vaststelt — methode, meetprocedure, rekenvoorbeeld — hoort in de toelichting."

### 3.4 Patroonoptie B werkt; één van de vier percentagevormen verdient een expliciete vermelding

**Bevinding.** Ik heb de voorgestelde reparaties zelf nagerekend. `(?![\w%])` in plaats van `\b` na `%` lost het defect correct op en houdt het controlegeval terecht buiten:

| Invoer | Huidig | Met optie B |
|---|---|---|
| "tenminste 80% van de gevallen" | geen | **hit** |
| "minimaal 80%." | geen | **hit** |
| "maximaal 5% afwijking" | geen | **hit** |
| "van 12,5 % en" | geen | **hit** (met `\s*` en decimalen) |
| "minimaal 80%voldoet" (C14) | hit | **geen** — terecht |
| "binnen 1 dag" / "uiterlijk na 1 week" | geen | **hit** met `(?:dag\|dagen)` / `(?:week\|weken)` |

**Punt.** Optie B zegt "Vervang de vier percentagevormen door de equivalente vorm met optionele ruimte, decimalen en `(?![\w%])`". Voor de drie woordgebonden vormen is dat eenduidig; de vierde is het kale `\b\d+\s+%\b`, waar "equivalent" ook de `\s+` → `\s*` en de decimalen moet omvatten, anders blijft "80%" zonder spatie ongedekt. Dat werkt in mijn test, maar de zin laat het impliciet.

**Voorgestelde correctie:** één verduidelijking in optie B: "…waarbij ook de kale vorm `\b\d+\s+%\b` de optionele spatie krijgt (`\s*`), zodat zowel '80%' als '12,5 %' wordt gedekt."

**Bevestiging bij optie A.** Ik heb de kandidaatlijst op mijn veertien gevallen gedraaid. Gedrag zoals verwacht en met één relevante verbetering: **C02 en C10 krijgen nu wél een signaal** (de onbepaaldheidsvorm "zo snel mogelijk"), terwijl ze onder de huidige set niets of juist een misleidend `bevat`-signaal kregen. C09 verliest terecht zijn `bevat`-signaal. C03, C06, C07 en C12 blijven zonder signaal — voor C12 (getalwoord) is dat een bekende, in het pakket benoemde kalibratiegrens. Dit zijn signaaleigenschappen, geen normuitkomsten; de kwalificatie "nog niet empirisch gevalideerd" in het synthesevoorstel blijft juist en ik claim niets sterkers.

### 3.5 Twee kleine feitelijke aanscherpingen in mijn eigen voordeel noch nadeel

**(a) `example_pair_policy`.** N2 zegt: "`example_pair_policy: review_policy` blijft passend bij die structurele grond." Dat is juist. De vervangende `example_pair_reason` is goed en verwijdert terecht de defecthistorische formulering. Geen correctie; ik noteer alleen dat hiermee mijn eigen voorgestelde tekst (§6.1) vervalt ten gunste van de structurele formulering, en dat ik dat een verbetering vind.

**(b) De categorieblanking bij C08 is correct en volledig.** `bron-bewijsregister-v2.md` C08 vermeldt: "Andere no_score-regels kunnen categorie reeds blanken; geen onvoorwaardelijk zichtbaar categorie-lek." Ik heb dat nagegaan en het klopt preciezer dan de formulering suggereert: **ESS-02 draagt `score_policy: no_score` en valt via de prefixmapping `"ESS-": juridisch` in dezelfde categorie als ESS-04.** Omdat `zonder_cijfer` uit `state.internal_rules` en `rule_records` wordt afgeleid — vóór evaluatie, onafhankelijk van de uitkomst — wordt "juridisch" in de volledige regelset altijd geblankt. Een hypothetisch ESS-04-PASS/FAIL-cijfer landt dus wél in `rule_scores` en in het ongewogen gemiddelde, maar het zichtbare categoriecijfer wordt daarna op `None` gezet.

Dat nuanceert mijn eigen A-05 en bevestigt de Codex-formulering. Wat blijft staan: de maskering is **incidenteel, niet ontworpen** — zij hangt aan de aanwezigheid van ESS-02 in de geëvalueerde set, en `rule_scores` zelf draagt het cijfer nog. De conclusie "ontwerp het reviewcontract expliciet scoreloos" blijft daarmee onveranderd juist. Ik stel voor dat C08 die ene zin krijgt: **"De maskering komt van ESS-02 (`no_score`, zelfde categorie `juridisch`) en is incidenteel; `rule_scores` draagt het individuele cijfer nog steeds."**

---

## 4. Standpuntweergave — gecontroleerd, geen vertekening

| Mijn positie | Weergave in de synthese | Oordeel |
|---|---|---|
| B-I: aanwezigheidsvoorwaarde op één integrale versiegebonden beoordeling; geen ESS-04-inhoudsblokkade; B-II zou expliciete afwijking van DEF-630 zijn | Letterlijk zo weergegeven in "Verschil in onderbouwing", met het verschil in besluitstatus expliciet benoemd en de gelijke uitkomstaanbeveling erbij | **eerlijk** |
| Criteriumgericht onderwerp van de norm | Overgenomen in N2 en als verbetering van N1 benoemd | **eerlijk** |
| `voldoende` uit de patroonlijst wegens ARAI-03-overlap | Weergegeven als mijn oorspronkelijke voorkeur, met Codex' afwijkende lezing (overlap is geen uitsluitgrond) en verwijzing naar kalibratie. Het woord staat zichtbaar in de kandidaatlijst met die aantekening | **eerlijk**, en de oplossingsroute is beter dan mijn eigen |
| Intrekkingen: totale beslisbaarheid, absolute opslagclaim, blinde regelpoort | Alle drie genoemd in het synthesevoorstel, met verwijzing naar mijn verwerking | **eerlijk** |
| Plaatsing in `definitie-nederlandse-definities` redactioneel opengelaten | Zo weergegeven, met de juiste toevoeging dat de voorgestelde tekst geen nieuwe taalafkeurgrond invoert | **eerlijk** |
| R-30 (skillpaden) | Afgewezen als fout pad, met bewijs | **terecht** — zie §5 |

**Nieuwe normverzwaring:** niet aangetroffen. N2 is smaller dan mijn eerste formulering en breder dan een cijferplicht; de afwijzing van "alle criteria beslissen ieder geval" is in mijn eigen verwerking (R02) al overgenomen. T2 voegt geen eis toe die niet uit N2 of een vastgesteld besluit volgt.

**Betekenisverlies:** niet aangetroffen in de inhoudelijke posities. Het enige verlies is het weggevallen weergavespoor van §3.1, en dat is een weglating, geen vervorming.

---

## 5. Correcties op mijzelf die uit deze ronde volgen

**R-30 was onjuist.** Ik stelde in `cowork-review-op-codex-v1.md` dat de skillpaden onder `/Users/chrislehnen/.agents/skills/` niet verifieerbaar zijn en dat geen van de drie wortels in het gedeelde materiaal die is. Dat is feitelijk fout: `feitenbasis/bestanden-v1.json` bevat **22 bronpaden onder `.agents/skills/`**, door mij nu geteld (22 van de 36 entries), en `skillvindplaatsen-verificatie-v1.json` toont voor alle 22 `exists: true` en `same_as_snapshot: true`. Ik had het manifest alleen op de `docs/`-entries bekeken en daaruit gegeneraliseerd. De enige geldige rest van R-30 is mijn eigen mountbeperking — ik kan die map niet bereiken — en die maakt de paden niet onverifieerbaar, alleen niet door mij. **R-30 vervalt als bezwaar.**

**R-12, terzijde.** Ik schreef "een substantiebegrip ('zand', 'recidive' — ASTRA noemt ze zelf)". ASTRA onderscheidt substanties ("cocaïne", "zand") van verschijnselen ("recidive", "onweer", "regen"). Codex corrigeert dat terecht in zijn verwerking; beide zijn voorbeelden van niet-telbare betekenissen, maar het zijn verschillende categorieën.

**R-20, bevestigd ingetrokken.** Mijn opwaardering van "niet aangetoond" naar "uitgesloten door het opslagcontract" heb ik in `cowork-reviewverwerking-v1.md` R09 al teruggenomen; de synthese hanteert de juiste formulering ("in onderzochte actuele routes ontbreekt een aangesloten versiegebonden ESS-04-reviewroute"). Geen open punt meer.

Deze drie correcties staan hier; ik wijzig geen eerder bestand.

---

## 6. Besluitrijpheid als onderzoeksvoorstel

**Wel besluitrijp.** De drie hoofdkeuzes zijn scherp, met per keuze een aanbeveling, een alternatief en een onderscheidende casus. De norm N2 is bronverankerd en niet strenger dan de bron. De statusverdeling — algemene reviewplicht en afschaffing van de totaalscore als **bestaand beleid**, indicatorselectie en reviewvorm als **voorstel** — is correct en is precies het onderscheid dat Chris nodig heeft om te weten waar hij iets besluit en waar hij iets laat herstellen.

**Niet besluitrijp, en zo benoemd:** implementatieacceptatie. De opsomming in §"Nog nodig vóór implementatieacceptatie" dekt de ontbrekende proeven volledig en verstopt niets.

**Wat ik Chris zou meegeven bij lezing**, zonder ergens een keuze voor te nemen:

1. Keuze 2 is de enige met een lopende verplichting eronder. De andere twee kunnen wachten; DEF-630 loopt al sinds 4 september en de poort controleert vandaag geen enkele reviewstatus, terwijl de meegeleverde `approval_gate.yaml` de scorevoorwaarde met een notitie laat passeren.
2. Keuze 1 is omkeerbaar en goedkoop, maar geen van beide onderzoekers heeft een nieuwe patroonset op echte definities gekalibreerd. Vaststellen zonder die kalibratie is een keuze voor een ongetest ontwerp.
3. Keuze 3 is de minst zichtbare en de meest bepalende voor hoe een reviewer de app ervaart: zij beslist of "ik weet het nog niet" een eigen uitkomst is of wegvalt tegen "voldoet niet".
4. De tekstvoorstellen (N2/G2/T2/H2, meldingen, vijf skillfamilies) kunnen los van de drie keuzes worden vastgesteld, met uitzondering van de patroonparagraaf, die aan keuze 1 hangt.

---

## 7. Status van de samenwerking

| Verplicht onderdeel | Status |
|---|---|
| Twee onafhankelijke eerste onderzoeken, bewaard vóór uitwisseling | aanwezig |
| Codex-review op Cowork (R01–R14) | aanwezig |
| Cowork-review op Codex (R-01–R-33) | aanwezig |
| Cowork-verwerking van R01–R14 | aanwezig |
| Codex-verwerking van R-01–R-33 | aanwezig, dispositie op alle 33 |
| Synthesevoorstel | aanwezig, v2 |
| Cowork-synthesecontrole | dit document |
| Zichtbare verwerking van deze controle door Codex | **nog te doen** |

Na verwerking van §3.1 t/m §3.5 en de eindverificatie van het pakket is aan alle verplichte onderdelen voldaan en kan het onderzoek gezamenlijk afgerond worden genoemd. Tot dat moment niet.

**Geen besluit, geen uitvoering.** Geen van de drie keuzes is genomen. Er is niets geïmplementeerd, geen issue of PR gemaakt, geen app, regel, skill of eerder onderzoeksbestand gewijzigd, en er is geen extra sessie of agent gestart.

---

## Bijlage — controles die ik voor deze synthesecontrole heb uitgevoerd

| Controle | Uitkomst |
|---|---|
| Hashes `synthesepakket-v1/manifest.json` | 9/9 gelijk |
| `first_versions_unchanged` tegen mijn eigen zeven bestanden | bevestigd |
| `cowork-proefbestanden-ontvangst-v1.json` tegen mijn drie proefbestanden | 3/3 gelijk |
| `nalevering3-manifest-v1.json` → `approval_gate.yaml` | gelijk |
| `reviewproef/` tegen `uitvoerbinding-v1.json` | 4/4 gelijk; stderr leeg; exit 0 |
| Reviewproefuitvoer tegen mijn replica | 14/14 identieke status en signalen, alle score `None` |
| Casusregister: rijen, ID's, aliassen, index | 37 rijen, 37 index-entries, 14 + 23 + 7 aliassen, geen wees-ID |
| Mijn veertien ID's en teksten ongewijzigd | bevestigd |
| Zoektocht naar het weergavespoor (`validation_view`, `validation_renderer`, `_reden_met_passages`, "heuristiek", `testable`) | geen treffer in het hele pakket → §3.1 |
| Casusverwijzingen in `instructievoorstellen-v3.md` tegen het register | `N24`/`N27` bestaan niet; `N22` dubbel → §3.2 |
| Patroonoptie B nagerekend op zes invoeren | reparatie werkt; C14 terecht uitgesloten → §3.4 |
| Patroonoptie A-kandidaat op mijn veertien gevallen | C02/C10 krijgen signaal, C09 verliest `bevat`; overige zoals verwacht |
| `score_policy` van alle acht meegeleverde regelrecords + prefixmapping | ESS-02 = `no_score`, categorie `juridisch`, blankt dezelfde categorie als ESS-04 → §3.5(b) |
| `.agents/skills`-paden in `feitenbasis/bestanden-v1.json` | 22 van 36 → R-30 vervalt (§5) |
| Dekkingstabel veertien dossieronderdelen | alle vindplaatsen bestaan; onderdeel 8 onvolledig door §3.1 |
