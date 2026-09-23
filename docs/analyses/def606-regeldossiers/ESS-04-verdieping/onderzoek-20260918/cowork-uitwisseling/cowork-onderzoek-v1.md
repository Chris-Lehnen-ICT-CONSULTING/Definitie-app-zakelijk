# cowork-onderzoek-v1 — ESS-04 Toetsbaarheid

Onafhankelijk eerste onderzoek door Claude Cowork (afzonderlijke ESS-04-sessie), 18 september 2026.
Regel: ESS-04 — Toetsbaarheid. Centraal issue: DEF-767. Codebasis: commit `4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb` (`werkboom-4cdb8ea43/` + `nalevering-4cdb8ea43/`), vergelijkingsbasis `50d0770ded6f4e8337738126d6bc2aa8f169e3de` (`werkboom/`), historische dossierbasis `d68a98a909630e15db6e1cb9c9c8171f957bff9d`.

**Onafhankelijkheid.** Bij het schrijven van deze v1 zijn geen `codex-onderzoek-*`, `besluitnotitie-*`, `casusregister-*`, nieuwe proefuitkomsten of synthese gelezen; die bestaan niet in deze map. Wel gelezen en als *gedeelde bronobservatie* behandeld: `astra-bronobservatie-v2.md` en `nalevering-leeswijzer-v1.md` (beide expliciet bronmateriaal, geen conclusies). De ASTRA-pagina heb ik daarna **zelf** rechtstreeks gelezen; §2.1 vermeldt mijn eigen waarneming, niet de overgenomen observatie.

**Aard van dit stuk.** Onderzoek en voorstel. Geen implementatie, geen normbesluit, geen wijziging aan app, regels, skills of bestaande bestanden.

---

## 0. Leeswijzer bij de claimsoorten

Elke uitspraak hieronder draagt een markering:

| Markering | Betekenis |
|---|---|
| **[BRON]** | letterlijk gelezen primaire bron (ASTRA, NL-SBB, VIM3) met vindplaats |
| **[BESLUIT]** | vastgelegd projectbesluit uit Linear of een dossier, met datum/issue |
| **[CODE]** | waarneming in de bevroren codebasis, met bestand en regelnummer |
| **[PROEF]** | uitkomst van de offline proef in bijlage A |
| **[INTERPRETATIE]** | mijn duiding van bron, besluit of code |
| **[VOORSTEL]** | mijn voorstel; blijft een voorstel, ook als de tweede onderzoeker het deelt |

---

## 1. Samenvatting voor Chris

Zes dingen, in volgorde van gewicht:

1. **De app-regeltekst verschuift de ASTRA-norm.** ASTRA zegt: *een criterium in een definitie moet toetsbaar zijn*. Het regelrecord zegt: *een definitie bevat objectief toetsbare elementen (harde deadlines, aantallen, percentages, meetbare criteria)*. Dat is een kwaliteitseis aan criteria veranderd in een inhoudsboodschappenlijst, en het is precies de bron van schijnprecisie en verzonnen drempels. Herstelbaar met tekst, geen nieuw normbesluit nodig (§2, §6.1).
2. **Vijf van de vijftien indicatorpatronen vuren nooit of missen het eigen ASTRA-voorbeeld.** Alle vier percentagepatronen zijn in normale zinnen dood; `uiterlijk na 1 week` en `binnen 1 dag` worden gemist. Aantoonbaar, reproduceerbaar (§5.2, bijlage A). Dit is een defect, geen normvraag.
3. **`bevat` en `omvat` staan als "toetsbaarheidssignaal" in het record.** Ze vuren op vrijwel elke Nederlandse definitiezin, inclusief zinnen met "zo snel mogelijk" erin (§5.2, casus C10). Dat is de trefwoord-pass in zijn zuiverste vorm — nu ongevaarlijk omdat ESS-04 reviewplichtig is, maar het is óók de reden waarom hij dat moet blijven.
4. **Er is geen enkele plek waar een menselijk ESS-04-oordeel wordt opgeslagen.** CON-01 en CON-02 hebben ieder een eigen, aan de recordversie gebonden reviewopslag en een niet-overrulebare vaststelblokkade. ESS-04 heeft niets: geen kolom, geen veld, geen gate. Een definitie kan vandaag worden vastgesteld terwijl ESS-04 letterlijk nooit is beoordeeld (§5.6, §5.7).
5. **Dat is geen nieuw normvoorstel maar achterstallig bestaand beleid.** DEF-630 draagt sinds 4 september 2026 het criterium: *"Verplichte `review_required`-uitkomsten hebben een versioned menselijke beoordeling; een numerieke score vervangt die niet."* Dat criterium is niet geïmplementeerd (§4.3, §5.7).
6. **De gebruiker ziet van ESS-04 alleen de regelcode.** ESS-01 en ESS-02 kregen in deze commit een leesbare reviewreden mét geciteerde passages; ESS-04 kreeg alleen de kale toetsvraag, en verschijnt in de ingeklapte weergave als niets meer dan `ESS-04` in een rijtje. Het sjabloon ligt er al (§5.5, §6.4).

De twee besluiten die ik werkelijk aan Chris voorleg staan in §7.4. Al het overige is herstel van wat al besloten is, of tekst.

---

## 2. Q1 — Oorspronkelijke norm, lokale aanvulling, toepasselijkheid, uitzonderingen

### 2.1 De oorspronkelijke norm, zelf gelezen

**[BRON]** https://www.astraonline.nl/index.php/Toetsbaarheid , op 18 september 2026 rechtstreeks geopend in de browser van deze sessie. Pagina toegankelijk. Voetregel: "Deze pagina is voor het laatst bewerkt op 11 feb 2025 om 09:46." Aangeboden permanente link: `https://www.astraonline.nl/index.php?title=Toetsbaarheid&oldid=8558`. De revisiepagina zelf heb ik niet geopend; de onderliggende Politiebron evenmin.

Velden zoals de pagina ze toont:

| Veld | Waarde op ASTRA |
|---|---|
| Id | ESS-04 |
| Regel - kort | toetsbaarheid |
| **Regel** | **"Een criterium als onderdeel van een definitie moet toetsbaar zijn."** |
| Toelichting | "De verschillende specificaties en de beperkende bepalingen moeten toetsbare elementen bevatten om aan de eis van een werkbare definitie te voldoen. Iemand die de definitie hanteert moet kunnen 'meten' of aan een criterium is voldaan." |
| Voorbeelden FOUT | '… zo snel mogelijk …', '… zo veel mogelijk …', '… moet zo mogelijk … ' |
| Voorbeelden GOED | '… binnen 3 dagen … ', '… tenminste 80% van de ... ', '… uiterlijk na 1 week … ' |
| Verwijzing | Politie |
| Prioriteit | midden |
| Aanbeveling | verplicht |
| Geldig voor | alle |
| Status | definitief |
| Relatie met andere regel | Instanties uniek onderscheidbaar (ESS-03) |
| Type | element in de definitie |
| **Thema** | **essentie van het begrip** |

Dit komt overeen met `astra-bronobservatie-v2.md`; ik heb het onafhankelijk waargenomen.

### 2.2 Wat de norm waarborgt

**[INTERPRETATIE]** Drie dingen staan er, en drie dingen staan er niet.

Wat er staat:

- Het **toetsobject is het criterium**, niet de definitie als geheel. De norm eist niet dat *een definitie een toetsbaar element bevat*; hij eist dat *een criterium dat in de definitie staat, toetsbaar is*. Dat is een kwaliteitseis aan de onderdelen, geen aanwezigheidseis voor een soort onderdeel.
- De maatstaf is de **hanteerbaarheid door een gebruiker**: "iemand die de definitie hanteert moet kunnen 'meten' of aan een criterium is voldaan". Het gaat om vaststelbaarheid van gevalslidmaatschap, niet om een meetinstrument.
- De **aanhalingstekens rond 'meten'** zijn van ASTRA zelf. De bron markeert het woord dus uitdrukkelijk als oneigenlijk gebruikt.

Wat er niet staat:

- Geen eis van een getal, termijn of percentage. De GOED-voorbeelden zijn illustraties van *bepaaldheid* tegenover *onbepaaldheid*; de FOUT-voorbeelden zijn alle drie onbepaaldheidsformules ("zo … mogelijk"). De as is bepaald/onbepaald, niet numeriek/niet-numeriek.
- Geen eis van meetcontext, noemer, peildatum of bronversie.
- Geen uitzonderingsclausule. "Geldig voor: alle" — anders dan ESS-03, dat op ASTRA "Geldig voor: telbare zelfstandige naamwoorden" draagt. **[BRON]** https://www.astraonline.nl/index.php/Instanties_uniek_onderscheidbaar

**[BRON]** JCGM VIM3 §2.1: measurement is "process of experimentally obtaining one or more quantity values that can reasonably be attributed to a quantity" (https://jcgm.bipm.org/vim/en/2.1.html). §1.30: een nominal property is "property of a phenomenon, body, or substance, where the property has no magnitude"; NOTE 1 daarbij: "A nominal property has a value, which can be expressed in words, by alphanumerical codes, or by other means"; de informatieve annotatie van 3 december 2013: "Nominal properties are distinguished from quantities, which are properties that have a magnitude, that is, they can be compared in terms of greater or lesser." (https://jcgm.bipm.org/vim/en/1.30.html)

**[INTERPRETATIE]** Meten in metrologische zin bestaat alleen voor grootheden. Een nominale eigenschap heeft wel een waarde en is dus vaststelbaar, maar wordt niet gemeten. Zou "meten" in ASTRA metrologisch gelezen worden, dan zou ESS-04 nominale kenmerken (handtekening geplaatst ja/nee, alle zijden even lang) buiten de norm plaatsen terwijl "Geldig voor: alle" staat — een lezing die de regel intern tegenstrijdig maakt. Samen met de aanhalingstekens van ASTRA zelf is dat mijns inziens beslissend: **'meten' betekent hier vaststellen, niet meten.**

**[BRON]** NL-SBB, vastgestelde versie 10 oktober 2024, §2.4.1.2 Notities, bij `definitie`: "Aan de hand van een definitie kan iemand bepalen of zijn eigen begrip behorende bij een term overeenkomt met het begrip dat gedefinieerd wordt." En bij `toelichting`: "Een toelichting wordt gebruikt om de grenzen van een begrip te verduidelijken … Een toelichting hoeft geen volledige definitie te zijn". Bij `uitleg`: "De definitie moet precies kloppen."

**[INTERPRETATIE]** NL-SBB bevestigt de functie (vaststelbaarheid van lidmaatschap) en levert bovendien de veldscheiding die §3 nodig heeft: de definitie moet kloppen, de toelichting mag de grenzen verduidelijken — maar is geen definitie. Een toelichting kan dus wel de meetcontext dragen en niet een ontbrekend criterium repareren.

### 2.3 De lokale aanvulling, en waar die de norm verschuift

**[CODE]** `werkboom-4cdb8ea43/src/toetsregels/regels/ESS-04.json`, sha256 `78537a76…a389c` (identiek in beide werkbomen; geen wijziging tussen `50d0770` en `4cdb8ea43`).

| Veld | ASTRA | Regelrecord | Oordeel |
|---|---|---|---|
| Regel/uitleg | "Een criterium als onderdeel van een definitie moet toetsbaar zijn." | "Een definitie bevat objectief toetsbare elementen (harde deadlines, aantallen, percentages, meetbare criteria)." | **verschuiving** |
| Toetsvraag | — (ASTRA kent dit veld niet) | "Bevat de definitie elementen waarmee je objectief kunt vaststellen of iets wel of niet onder het begrip valt?" | lokale toevoeging, inhoudelijk dicht bij de norm |
| Toelichting | 'meten' tussen aanhalingstekens | "Zonder toetsbare criteria kan een lezer niet objectief vaststellen of iets onder de definitie valt." + goed/fout-lijstjes | eerste zin trouw; de lijstjes versmallen |
| Thema | essentie van het begrip | `"thema": "toepasbaarheid"` | **afwijkend** |
| Brondocument/verwijzing | Verwijzing: Politie | `"brondocument": "ASTRA"` | ASTRA is de vindplaats, Politie de bron |
| Relatie | Instanties uniek onderscheidbaar | `relatie` verwijst terug naar Toetsbaarheid zelf | **onjuist** |
| Prioriteit/aanbeveling/geldigheid/status | midden / verplicht / alle / definitief | idem | gelijk |

**[INTERPRETATIE]** Drie afwijkingen, van zwaar naar licht:

1. **De uitleg.** Van "een criterium moet toetsbaar zijn" naar "een definitie bevat toetsbare elementen (harde deadlines, aantallen, percentages …)". Dit doet drie dingen tegelijk: het verplaatst het toetsobject van criterium naar definitie, het maakt van een kwaliteitseis een aanwezigheidseis, en het somt als eerste twee voorbeelden numerieke vormen op. Dit is de directe tekstuele oorsprong van de drie risico's die de opdracht noemt: schijnprecisie, verzonnen drempels en noemerloze percentages. De toetsvraag in hetzelfde record is trouwens wél trouw — het record spreekt zichzelf tegen.
2. **Het thema.** ASTRA: "essentie van het begrip". Record: "toepasbaarheid". Klein maar niet onschuldig: het duwt ESS-04 weg van de vraag *wat maakt dit begrip dit begrip* naar *is dit praktisch bruikbaar*.
3. **De relatie.** ASTRA legt één expliciete relatie: naar ESS-03. Het record zet in `relatie` een verwijzing naar de eigen pagina. De enige door de bron gelegde regelrelatie is dus in de app verdwenen.

**[INTERPRETATIE]** Wat géén verschuiving is en moet blijven: `prioriteit: midden`, `aanbeveling: verplicht`, `geldigheid: alle`, `status: definitief` komen exact overeen. En het `runtime_contract` (judgment/review_required/excluded_from_score) is géén afwijking van ASTRA maar een lokale uitvoeringskeuze over automatiseerbaarheid — daarover §4.1.

### 2.4 Toepasselijkheid

**[INTERPRETATIE]** "Geldig voor: alle" **[BRON]**, dus de regel geldt voor iedere definitie, ongeacht ingang, ontologische categorie of telbaarheid. De toepassing verschilt per ingang, de norm niet. Concreet:

| Ingang | Geldt ESS-04? | Wat de norm daar betekent |
|---|---|---|
| Generatie | ja | geen drempel verzinnen die de bron niet draagt; onbepaaldheidsformules vermijden |
| Uitsluitend toetsen | ja | oordeel over de ongewijzigde tekst; geen tekstwijziging |
| Import | ja, dezelfde norm | aangeleverde inhoud wordt niet milder of strenger beoordeeld |
| Bewerken | ja | na wijziging vervalt een eerder oordeel |
| Review | ja — dit is de plek waar het oordeel ontstaat | |
| Conceptopslag | ja, als open punt | "nog te beoordelen" is een uitkomst, geen leegte |
| Vaststelling | ja | zie §5.7 |
| Export/herbeoordeling | ja | een export moet de openstaande beoordeling meedragen |

### 2.5 Uitzonderingen: onderbouwd, open, of afgewezen

**[BRON]** ASTRA kent geen uitzondering. **[BESLUIT]** `cowork-opdracht-v1.md`: "CON-02 heeft eigen goedgekeurde AI-beoordeling en bronuitzonderingen; kopieer dit beleid niet automatisch naar ESS-04." Dus de CON-02-uitzonderingsconstructie (geen passende bron, verwijzingsuitzondering, deelcorrectie) geldt hier niet.

| Kandidaat-uitzondering | Status | Grond |
|---|---|---|
| Kwalitatieve criteria zonder getal | **geen uitzondering — gewone toepassing** | de norm eist bepaaldheid, niet een getal (§2.2); "Geldig voor: alle" |
| Niet-telbare of substantiebegrippen | **open beleidskeuze** | ASTRA beperkt ESS-03 tot telbare zelfstandige naamwoorden maar ESS-04 niet. Of een substantiebegrip ("zand", "recidive") een toetsbaar criterium *kan* dragen is een echte vraag; ik stel geen uitzondering voor, wel een expliciete reviewaanwijzing |
| Definities die een onbepaald begrip definiëren (het begrip is zelf "spoedeisend") | **open beleidskeuze** | analoog aan het ESS-01-beleid "een definitie van het begrip 'doel' wordt niet op de term afgekeurd". Hier is het lastiger: de definitie van een vaag begrip moet nog steeds zeggen wanneer iets eronder valt |
| Zeer korte of lege tekst | **geen uitzondering; aparte uitkomst** | ontbrekende invoer is geen "voldoet" en geen "voldoet niet" (§5.4) |
| Stijlvoorkeur voor numerieke formulering | **uitdrukkelijk afgewezen** | de opdracht verbiedt een extra afkeurgrond uit een stijlvoorkeur; een bestaande kwalitatieve definitie mag niet alsnog worden afgekeurd omdat een generatievoorkeur getallen mooier vindt |

---

## 3. Q2 — Noodzakelijke versus ondersteunende invoer, en de veldrollen

### 3.1 Toetsobject en bewijs

**[CODE]** Het record declareert `"required_inputs": ["definition_text"]` — één invoer. **[INTERPRETATIE]** Dat is juist als minimum en onvoldoende als volledige beschrijving van wat een *mens* nodig heeft. Het onderscheid dat de opdracht vraagt:

- **Toetsobject**: de definitiekern (de definitiezin), op een vastgelegde versie. Alleen dit wordt beoordeeld.
- **Noodzakelijk bewijs**: de bedoelde betekenis/afbakening van het begrip, want zonder te weten wát afgebakend moet worden, kun je niet zeggen of het criterium lidmaatschap beoordeelbaar maakt. In de praktijk: term + context.
- **Ondersteunende informatie**: alles wat helpt het oordeel te vormen of de meetcontext te begrijpen — bronpassage, toelichting, voorbeelden, grensgevallen.
- **Uitsluitend presentatie**: alles wat alleen de leesbaarheid dient.

**[INTERPRETATIE]** Belangrijk: aanvullende velden zijn nooit een reparatie. Een toelichting die uitlegt dat "substantieel" 20% betekent, maakt "substantieel" in de kern niet toetsbaar — NL-SBB zegt het zelf: de definitie moet precies kloppen, de toelichting verduidelijkt grenzen **[BRON]**. Dit is dezelfde lijn als het historische dossier §7.

### 3.2 Veldrolmatrix

Per veld afzonderlijk, zoals `genereren-en-toetsen.md` §A vraagt. "Mag AI wijzigen?" gaat over de generatie-/herstelroute; bij uitsluitend toetsen is het antwoord overal nee.

| Veld | Zelf toetsobject voor ESS-04? | Bewijsfunctie voor het ESS-04-oordeel | Rol bij generatie | Mag AI dit opleveren/wijzigen? | Ontbrekend of conflicterend |
|---|---|---|---|---|---|
| **Definitiezin (kern)** | **Ja — het enige toetsobject.** Criterium: is ieder in de kern gebruikt criterium bepaald genoeg om lidmaatschap vast te stellen? | n.v.t. (is het object) | verplichte uitvoer | voorstel; nooit stil wijzigen bij toetsen | leeg ⇒ aparte uitkomst "niet beoordeelbaar", nooit voldoet |
| **Context (org./jur./wettelijk)** | Nee | **Noodzakelijk** wanneer het criterium contextafhankelijk is (werkdag, peildatum, populatie). Bepaalt wat "vaststelbaar" hier betekent | verplichte invoer; hoort niet in de zin (CON-01) | AI mag context niet verzinnen of wijzigen | ontbrekend ⇒ blokkeert vaststellen al via CON-01; voor ESS-04: oordeel blijft open waar het criterium er van afhangt |
| **Definitiebronnen** | Nee | **Noodzakelijk zodra de kern een drempel of grens noemt**: de bron moet die drempel dragen | gezaghebbende invoer | AI mag geen bron of passage verzinnen; CON-02-beleid blijft eigenaar | drempel zonder brondekking ⇒ ESS-04 signaleert, CON-02 oordeelt over het bronbewijs; niet dubbel afkeuren |
| **Ontologierelaties / UFO-categorie** | Nee | **Ondersteunend**: helpt bepalen wat het meetobject en de populatie zijn (een proces telt anders dan een type) | ondersteunend | voorstel; label is geen bewijs (ESS-02-besluit) | ontbreken ⇒ geen ESS-04-gevolg |
| **Voorbeelden** | Nee | **Ondersteunend**: tonen dat het criterium in gewone gevallen werkt | ondersteunende uitvoer | voorstel | ontbreken ⇒ geen gevolg |
| **Praktijkvoorbeelden** | Nee | **Ondersteunend, sterker**: leveren waarneembaar bewijs dat het criterium in het veld vast te stellen is | ondersteunende uitvoer | voorstel; geen praktijkgeval verzinnen | een gefabriceerd praktijkgeval is schadelijker dan geen |
| **Tegenvoorbeelden** | Nee | **Ondersteunend, het meest diagnostisch**: een tegenvoorbeeld dat op het criterium faalt bewijst dat het criterium onderscheidend werkt | ondersteunende uitvoer | voorstel | ontbreken ⇒ geen gevolg |
| **Grensgevallen** | Nee | **Ondersteunend en beslissend bij drempels**: tonen inclusief/exclusief en referentietijd | ondersteunende uitvoer | voorstel | bij een drempel zonder grensgeval blijft de inclusiviteit open |
| **Synoniemen** | Nee | **Ondersteunend**: een synoniem moet hetzelfde criterium dragen; doet het dat niet, dan is het geen synoniem | ondersteunend | voorstel | conflict ⇒ signaal voor SAM-08, niet voor ESS-04 |
| **Homoniemen** | Nee | **Ondersteunend**: onderscheiden het meetobject (welke "pad") | ondersteunend | voorstel | ASTRA noemt homoniem/polyseem bij ESS-03, niet bij ESS-04 |
| **Toelichting** | **Nee — en dit is de scherpste grens** | **Mag de methode, meetcontext, noemer of peildatum dragen** (NL-SBB: verduidelijkt grenzen). **Repareert nooit een ontbrekend criterium in de kern** | ondersteunende uitvoer; apart voorstel | voorstel; mag niet stil in de getoetste kern belanden | toelichting die het enige criterium bevat ⇒ kern voldoet niet |
| **Metadata (versie, actor, datum, bronversie)** | Nee | **Noodzakelijk voor de houdbaarheid van het oordeel**, niet voor de inhoud ervan | registratie | AI vult dit niet | ontbrekende versiebinding ⇒ het oordeel is niet herbruikbaar (§5.7) |

### 3.3 Wanneer zijn meetcontext, noemer, grens, referentietijd en bronversie werkelijk nodig?

**[INTERPRETATIE]** Niet altijd — dat is het punt. Een universele metadata-eis voor elk kwalitatief kenmerk is precies de schijnprecisie die de norm wil vermijden. Mijn criterium: **een meetcontextelement is nodig wanneer twee redelijke beoordelaars met dezelfde tekst en dezelfde context tot een ander oordeel over hetzelfde geval zouden kunnen komen zonder dat element.**

| Element | Nodig wanneer | Niet nodig wanneer |
|---|---|---|
| Meetobject / populatie | de kern een verhouding, aandeel of aantal noemt | het criterium een eigenschap van het individuele geval is |
| Noemer | er een percentage of aandeel in de kern staat — **altijd** | er geen verhouding is |
| Inclusieve/exclusieve grens | er een drempelwaarde is waar gevallen feitelijk op kunnen landen ("minimaal 80%", "ouder dan 18") | een kwalitatief onderscheid zonder continuüm |
| Referentietijd / peildatum | de eigenschap in de tijd verandert (leeftijd, status, saldo) | de eigenschap tijdsinvariant is (aantal zijden) |
| Werk- of kalenderdagen | een termijn in dagen in de kern staat — **altijd**, dit is een klassieke stille ambiguïteit | er geen dagtermijn is |
| Bronversie | de drempel of grens uit een bron komt | het criterium uit de begripsdefinitie zelf volgt |
| Conflictafhandeling | bron en context verschillende drempels geven | er één bron is |

**[INTERPRETATIE]** En de andere kant op: "binnen 3 dagen" ziet er toetsbaar uit maar is het pas als duidelijk is *waarvandaan* geteld wordt. Casus C01 (het ASTRA-GOED-fragment zelf) draagt dat startpunt wél ("nadat het verzoek is ingediend"); het is geen toeval dat ASTRA het er bij schrijft.

### 3.4 Wat maakt gevalslidmaatschap beoordeelbaar?

De regelspecifieke kernvraag uit de opdracht. **[INTERPRETATIE]** Mijn antwoord in vier voorwaarden, waarvan géén numeriek is:

1. **Aanwijsbaarheid** — het criterium wijst een eigenschap aan die aan een geval valt te constateren (waarnemen, opzoeken, afleiden), niet een oordeel over het geval. "Handtekening geplaatst" is aanwijsbaar; "belangrijk" niet.
2. **Bepaaldheid** — de eigenschap heeft een grens die niet per beoordelaar verschuift. Dat kan een getal zijn, maar ook een tweewaardig onderscheid ("alle zijden even lang") of een gesloten opsomming.
3. **Volledigheid van de beslissing** — de criteria samen beslissen elk gewoon geval, niet alleen de duidelijke. Als een criterium een groot grijs gebied laat, is de definitie niet toetsbaar, ook al is elk los criterium keurig.
4. **Verankering** — waar het criterium van iets buiten de tekst afhangt (een bron, een peildatum, een register), is dat iets aanwijsbaar.

**Wat het niet is:** numerieke meetbaarheid (voorwaarde 2 kan kwalitatief worden vervuld); juistheid (een toetsbaar criterium kan het verkeerde begrip afbakenen — ESS-04 zegt niets over of het *goede* criterium is gekozen); essentieel onderscheid (dat is ESS-01 en ESS-05).

**Kwalitatieve criteria volstaan** wanneer 1–4 vervuld zijn. **[PROEF]** C03 en C06 zijn daar de gevallen van: "alle zijden even lang" en "handtekening geplaatst" vervullen alle vier zonder enig getal, en krijgen van de huidige patronen geen enkel signaal.

**Hoe schijnprecisie te voorkomen:** de vier voorwaarden toepassen op elk criterium afzonderlijk, niet op de zin als geheel. C04 ("Belangrijke aanvraag die binnen 3 dagen relevant wordt") heeft één bepaald criterium en twee onbeoordeelbare; het geheel is niet toetsbaar. Een regel die per zin kijkt of er "een toetsbaar element in zit" keurt dit goed. Dat is de kern van de verschuiving in §2.3.

---

## 4. Q3 — Relaties met andere regels

Ik onderzoek hier uitsluitend de relatie; ik beslis niets over de buurregels en neem hun besluiten niet over.

### 4.1 De ASTRA-relatie: ESS-03

**[BRON]** ASTRA legt precies één regelrelatie bij ESS-04: "Instanties uniek onderscheidbaar". De ESS-03-pagina: "Een definitie maakt het mogelijk om instanties van het gedefinieerde begrip uniek te identificeren en van elkaar te onderscheiden. … De definitie 'moet eenduidig tellen mogelijk maken' door verschillende onafhankelijke materiedeskundigen." En: "als verschillende materiedeskundigen tot verschillende uitkomsten komen, dan kan aanscherping van de definitie nodig zijn, of er is sprake van een homoniem … of polyseem". Geldig voor: telbare zelfstandige naamwoorden.

**[INTERPRETATIE]** Twee dingen volgen hieruit, en het tweede is belangrijk:

- De arbeidsdeling: **ESS-03 gaat over het individueren van instanties** (is dit één brug of vier?), **ESS-04 over het beslissen van lidmaatschap** (is dit ding een brug?). Ze overlappen waar een telcriterium tegelijk het lidmaatschapscriterium is, maar ze kunnen los falen: "zand" is niet telbaar (ESS-03 niet van toepassing) maar kan wel toetsbaar afgebakend zijn.
- **De tweebeoordelaarsproef is normatief verankerd bij ESS-03, niet bij ESS-04.** De opdracht vraagt mij twee onafhankelijke beoordelaars als kwaliteitsproef te onderzoeken. Mijn bevinding: het is bij ESS-03 een expliciete bronformulering en bij ESS-04 niet. Ik stel daarom **geen universele tweepersoonspoort** voor en waarschuw ertegen die stilzwijgend uit ESS-03 over te nemen. Wat ik wél voorstel is de methodische variant: **onafhankelijk labelen van grensgevallen als kalibratie van de reviewinstructie** — een onderzoeksinstrument, geen productpoort (§7.3).

Daarbij hoort het onderscheid dat de opdracht vraagt: **verschil in betekenis** (twee beoordelaars lezen een ander begrip in de definitie — dat is een homoniem/polyseem-signaal en ESS-03/ESS-05-terrein) versus **verschil in toepassing of bewijs** (zelfde begrip, ander oordeel over of dit geval eronder valt — dát is een ESS-04-signaal). Alleen het tweede is bewijs dat het criterium onvoldoende bepaald is.

### 4.2 De overige relaties

| Regel | Relatie | Conflict of overlap? | Wie beslist |
|---|---|---|---|
| **ARAI-03** (subjectieve bijvoeglijke naamwoorden) | Sterkste praktische overlap. "Belangrijke", "relevant", "adequaat" zijn tegelijk een ARAI-03-treffer en een ESS-04-onbeoordeelbaarheid. **[CODE]** ARAI-03 draagt hetzelfde runtimecontract: `judgment_review` / `review_required` / `excluded_from_score` | **Overlap, geen conflict.** Verschillende gronden: ARAI-03 is een formuleringsregel (`type: formulering`), ESS-04 een elementregel (`type: element in de definitie`). ARAI-03 is `aanbeveling: optioneel`, ESS-04 `verplicht` | ARAI-03 beslist over het woord, ESS-04 over de beoordeelbaarheid. Risico: **dubbele melding voor één tekstprobleem**; zie §6.5 |
| **ESS-01** (essentie, niet doel) | Onafhankelijk. Een toetsbaar criterium kan een doel zijn ("bedoeld om binnen 3 dagen te worden afgehandeld") | Geen conflict | ESS-01 |
| **ESS-02** (betekenisniveau en aard) | Ondersteunend: het niveau bepaalt mede wat een geval ís | Geen conflict | ESS-02 |
| **ESS-03** | zie §4.1 | Overlap bij telcriteria | ESS-03 voor individuering |
| **ESS-05** (voldoende onderscheidend) | Nauw verwant en makkelijk te verwarren. ESS-05: onderscheidt het begrip zich van *verwante begrippen*. ESS-04: kun je van een *geval* vaststellen of het eronder valt. Een definitie kan toetsbaar en niet-onderscheidend zijn (toetsbaar criterium dat ook op het buurbegrip past) en omgekeerd | Geen conflict; wel verwarringsrisico in reviewteksten | ESS-05 |
| **CON-01** (context niet in de zin) | **Spanning, en die is reëel.** Meetcontext (peildatum, werkdagen, populatie) is soms nodig om een criterium toetsbaar te maken, maar registratiecontext hoort volgens CON-01 buiten de zin | **Schijnbaar conflict, oplosbaar.** CON-01 verbiedt *registratiecontext* in de zin en laat uitdrukkelijk toe wat "inhoudelijk noodzakelijk is om het begrip af te bakenen" **[CODE]** `json_based_rules_module.py` CON-01-instructie. Meetcontext die het criterium beslist, is precies zulke noodzakelijke inhoud | CON-01 blijft eigenaar van de contextgrens. **Ik stel geen wijziging aan CON-01 voor**; ik stel vast dat de bestaande formulering ruimte laat en dat de ESS-04-instructie daarnaar moet verwijzen in plaats van een eigen regel te maken |
| **CON-02** (bronbasis) | Complementair: waar ESS-04 een drempel in de kern signaleert, is CON-02 eigenaar van de vraag of de bron die drempel draagt | Geen conflict; wel **risico op dubbele afkeur** van hetzelfde ongefundeerde getal | CON-02 voor het bronbewijs. ESS-04 oordeelt alleen over bepaaldheid, niet over gefundeerdheid |

**[INTERPRETATIE]** Eén algemene grens die de opdracht expliciet noemt en die ik onderschrijf: **een reproduceerbaar gemeten eigenschap hoeft niet begripsbepalend te zijn.** "Voertuig dat op dinsdag is geregistreerd" is volmaakt toetsbaar en volstrekt niet-essentieel. ESS-04 zegt niets over essentie. Reviewteksten die de twee vragen samenvoegen ("is dit een goed criterium?") zijn daarom fout; §6.3 splitst ze.

### 4.3 De bovenliggende besluiten

**[BESLUIT]** DEF-624, 15 september 2026: voorlopig geen totaalcijfer en geen vervangende deelscore; wel per regel het oordeel, de dekking en de openstaande punten. Geldt appbreed.

**[BESLUIT]** DEF-624: ESS-04 is een van de acht regels die per besluit reviewplichtig zijn (`review_required`, `excluded_from_score`).

**[BESLUIT]** DEF-630 (*roadmapcorrectie vastgesteld door Chris op 4 september 2026*), onder "Verplicht regressiegedrag", letterlijk:

> "Verplichte `review_required`-uitkomsten hebben een versioned menselijke beoordeling; een numerieke score vervangt die niet."

en

> "Ontbrekende context, verplicht bewijs, actor of vereiste review kan niet met alleen een notitie worden opgeheven."

**[INTERPRETATIE]** Dit is het belangrijkste besluitfeit van dit onderzoek. Het antwoord op "moet een ESS-04-oordeel worden vastgelegd voordat een definitie kan worden vastgesteld?" is al gegeven, op 4 september 2026, appbreed. §5.7 toont dat het niet is uitgevoerd. Mijn voorstel in §6.6 is daarom **herstel van bestaand beleid**, geen nieuw normbesluit — met één echte productkeuze die wél nieuw is (§7.4, keuze B).

**[BESLUIT]** DEF-638: maximaal één gerichte repair, herstelontwerp niet geactiveerd; `enhancement_service` wordt als `None` geïnjecteerd. Dit onderzoek activeert niets.

**[BESLUIT]** ESS-02 (DEF-750/754): niveau en aard apart; menselijke inhoudelijke beoordeling; geen cijfer; geen zelfstandige ESS-02-vaststelblokkade. **[INTERPRETATIE]** Let op de asymmetrie die hieruit volgt: ESS-02 kreeg uitdrukkelijk *geen* eigen blokkade, CON-01 en CON-02 wél. Voor ESS-04 is dat nooit besloten. Dat maakt §7.4-keuze B een echte keuze en niet een gevolgtrekking.

---

## 5. Q4 — Daadwerkelijk bewezen appgedrag per ingang

Per ingang volg ik invoer → transport → oordeel → opslag → weergave → handeling, en scheid codelezing, serviceproef en UI-bewijs.

### 5.1 De keten in één beeld

**[CODE]** Root-SSOT `config/toetsregels/toetsregels_config.yaml` (ESS-04 in `rule_ids`, regel 136) → `src/toetsregels/runtime_contract.py` (typecontrole, `RuleContractError` bij afwijking) → `src/toetsregels/manager.py` / `cached_manager.py` → `src/services/validation/modular_validation_service.py` → evaluator `judgment_review` → `EvaluationOutcome.review_required` → `review_items` → resultaatdict → `result_contract.neem_contractvelden_over` → UI.

### 5.2 Het oordeel zelf — codelezing

**[CODE]** `src/services/validation/evaluators/judgment_review.py`, regels 54–65:

```python
def evaluate(self, record, ctx, deps) -> EvaluationOutcome:
    signalen = self._signalen(record, ctx, deps)
    toetsvraag = str(record.get("toetsvraag") or record.get("naam") or "").strip()
    reden = toetsvraag or "Deze regel vereist een inhoudelijk oordeel."
    code = record.rule_id.upper()
    if code == "ESS-01":
        reden = self._ess01_reden(ctx, signalen)
    elif code == "ESS-02":
        reden = self._ess02_reden(ctx, signalen)
    return EvaluationOutcome.review_required(reden, signals=signalen)
```

**[CODE]** Bewezen: ESS-04 levert **altijd** `review_required`, ongeacht tekst en signalen. Geen pad naar pass of fail. Dat is conform DEF-624 en is het sterke punt van de huidige implementatie.

**[CODE]** Gedragsverschil tussen de twee commits (`diff werkboom ↔ werkboom-4cdb8ea43`): in `50d0770` had geen enkele oordeelregel een eigen reden; in `4cdb8ea43` kregen **ESS-01 en ESS-02** een leesbare reden met letterlijk geciteerde passages (`_reden_met_passages`). ESS-04 kreeg dat niet. Het sjabloon bestaat dus, en ESS-04 valt erbuiten.

**[CODE]** De signaalfunctie, regels 150–171: patronen uit `herkenbaar_patronen` plus `get_additional_patterns(code)` uit `validation.additional_patterns`. **Dat bestand is niet in het pakket** (§8). Alles hieronder over signalen geldt dus onder voorbehoud van eventuele extra patronen voor ESS-04.

**[PROEF] De patroondefecten.** Offline replica, bijlage A, 14 gevallen, 3 afwijkingen van de vooraf vastgelegde verwachting — alle drie doordat een patroon níet vuurde waar het record dat kennelijk bedoelde:

| Patroon in het record | Werkelijk gedrag | Bewijs |
|---|---|---|
| `\btenminste\s+\d+%\b` | vuurt **nooit** in normale tekst | `\b` na `%` vereist direct een woordteken; "tenminste 80% van de" → geen treffer, "tenminste 80%x" → wel. Casus C08 (ASTRA's eigen GOED-voorbeeld) |
| `\bminimaal\s+\d+%\b` | vuurt **nooit** in normale tekst | idem. Casus C05 versus controlegeval C14 ("80%voldoet" → wél treffer) |
| `\bmaximaal\s+\d+%\b` | vuurt **nooit** in normale tekst | idem |
| `\b\d+\s+%\b` | vuurt **nooit** in normale tekst | idem |
| `\buiterlijk\s+na\s+\d+\s+(dagen?|weken?)\b` | mist "1 week" | `weken?` = "weke" + optionele "n"; "week" valt erbuiten. Casus C11 — opnieuw ASTRA's eigen GOED-voorbeeld |
| `\bbinnen\s+\d+\s+dagen?\b` | mist "1 dag" | `dagen?` = "dage" + optionele "n" |
| `\bbevat\b`, `\bomvat\b` | vuren op vrijwel elke definitiezin | Casus C09 en C10; C10 bevat bovendien "zo snel mogelijk" en krijgt tóch een "toetsbaarheidssignaal" |

**[INTERPRETATIE]** Netto: van vijftien patronen zijn er vier dood, twee halfblind voor enkelvoud, en twee (`bevat`/`omvat`) betekenisloos breed. Twee van ASTRA's drie GOED-voorbeelden worden door de patronen die ervoor gemaakt zijn niet herkend. Het `example_pair_reason` in het record zegt dat de patronen "vuren op elk getal of elke tijdsaanduiding en missen het eigen foute voorbeeld" — de eerste helft klopt voor `bevat`/`omvat`, maar de werkelijke situatie is ernstiger en deels omgekeerd: ze missen hun eigen **goede** voorbeelden.

**[INTERPRETATIE]** Dit is vandaag onschadelijk voor het oordeel (dat is toch altijd `review_required`) en schadelijk voor de reviewer: de signalen sturen zijn aandacht verkeerd. Het is ook een **latente valstrik**: zodra iemand ESS-04 ooit zou willen automatiseren op deze patronen, is de uitkomst aantoonbaar willekeurig.

### 5.3 Transport — waar het oordeel wél en niet aankomt

**[CODE]** `modular_validation_service.py` regels 1617–1626: `REVIEW_REQUIRED` gaat naar `review_items`, **niet** naar `passed_rules`, **niet** naar `rule_scores`, **niet** naar `violations`. Bewezen: geen stille pass, geen scorebijdrage.

**[CODE]** `modular_validation_service.py:1344` zet `"review_required": review_items` in het resultaat; `:1780` telt de dekking per status.

**[CODE]** `nalevering-4cdb8ea43/src/services/validation/result_contract.py` regels 56–66: `CONTRACTVELDEN` bevat `("review_required", list, False)`, `("rule_statuses", dict, False)` en `("evaluation_coverage", dict, False)`; `neem_contractvelden_over` kopieert wat de bron werkelijk draagt. **[INTERPRETATIE]** Ik had op grond van `mappers.py` en `types.py` (die de velden niet noemen) transportverlies vermoed. De nalevering **weerlegt dat**: de reviewplicht overleeft de conversies. Ik noteer dit expliciet als een hypothese die door bewijs is verworpen.

**[CODE]** `result_contract.met_expliciete_runstatus`: bij een onbekende run worden `is_acceptable=False` en een numerieke score 0.0 afgedwongen, terwijl "regeluitkomsten, dekking, reviewplicht … ongewijzigd mee[reizen]". Fail-closed en behoud van uitleg. Correct.

### 5.4 Ingang: uitsluitend toetsen

**[CODE]** `validation_orchestrator_v2.py` regels 152–185: "Valideer exact de aangeleverde tekst zonder opschoning. … uitsluitend toetsen gebruikt exact de invoer. Cleaning hoort bij een expliciete generatie-/voorstelstap." En `context_dict["record_text"] = text` onvoorwaardelijk uit het argument, zodat een aanroeper de binding niet kan spoofen.

**[INTERPRETATIE]** Bewezen op codeniveau: **alleen-toetsen wijzigt de tekst niet.** Dit is precies wat `genereren-en-toetsen.md` §C eist en wat ik bij de andere ingangen als norm aanhoud.

**Bewijsniveau:** codelezing. Geen serviceproef, geen UI-proef.

**Lege tekst:** **[PROEF]** C07 geeft `review_required` met de kale toetsvraag als reden. **[INTERPRETATIE]** Formeel juist (geen pass), inhoudelijk misleidend: de gebruiker krijgt bij een lege definitie dezelfde vraag als bij een volle. Ontbrekende invoer verdient een eigen uitkomst; §6.4 lost dit op.

### 5.5 Weergave

**[CODE]** `validation_view.py` regels 730–739:

```python
for review_item in validation_result.get("review_required") or []:
    ...
    if rule_id in ("ESS-01", "ESS-02"):
        st.text(str(review_item.get("reason") or f"{rule_id} — Nog te beoordelen"))
```

**[CODE]** Bewezen: ESS-04 is uitgesloten van de altijd-zichtbare reviewreden. Hij verschijnt uitsluitend via `_statuslijst_regels` (`validation_view.py:245`) als kale code in de regel "🟠 Nog te beoordelen: …", en alleen wanneer de gebruiker de details openklapt. Geen toetsvraag, geen passage, geen aanwijzing wat te doen.

**[CODE]** `validation_view.py:150-157`: de dekkingsregel toont "🟠 {n} nog te beoordelen" — ESS-04 telt daarin mee. Dat werkt.

**[CODE] Latente valstrik.** `validation_renderer.py:353`:

```python
if rid in {"ESS-03", "ESS-04", "ESS-05"}:
    return "Vereist element herkend (heuristiek)."
```

Dit is de *pass-verklaring* van ESS-04. Hij is vandaag onbereikbaar, want `_format_passed_rules` krijgt alleen `passed_rules` en `review_required` komt daar niet in (§5.3). **[INTERPRETATIE]** Maar hij staat er wel, met de tekst "Vereist element herkend" — exact de heuristische pass die DEF-624 heeft afgeschaft. Ditzelfde patroon is bij ESS-02 wél opgeruimd, met een comment op de plek (`validation_renderer.py:346-349`). ESS-04 is overgeslagen. Dode code die precies het verboden gedrag beschrijft, is een terugvalrisico bij de volgende wijziging.

**[CODE]** Idem `modular_validation_service.py:1938`: `if reason == "testable" and c == "ESS-04": return "Maak een objectief toetsbaar element expliciet (bijv. termijn of meetbare grens)."` — een suggestie bij een violation die ESS-04 niet meer kan produceren. Ook hier: dode code die "termijn of meetbare grens" als het antwoord presenteert.

**Bewijsniveau:** codelezing. **Geen UI-proef uitgevoerd** — de meegeleverde snapshot draait niet (§8) en een Streamlit-proef valt buiten de toegestane scope.

### 5.6 Opslag

**[CODE]** `src/database/schema.sql`, tabel `definities`: kolommen voor validatie zijn `validation_score`, `validation_date`, `validation_issues` (JSON array van issues). **Er is geen kolom, en geen JSON-veld, waarin een menselijk oordeel per reviewplichtige regel wordt vastgelegd.**

**[CODE]** Ter vergelijking, wat CON-01 en CON-02 wél hebben: `definition_repository.set_context_review(definitie_id, review, updated_by, *, expected_version)` (regel 1426) en `set_source_review(... expected_version)` (regel 1215), beide met optimistic lock op de beoordeelde recordversie, plus `get_context_review()`, `get_source_review()`, `get_source_review_status()`, `get_source_review_history()`.

**[INTERPRETATIE]** Bewezen: een ESS-04-oordeel kan nergens worden bewaard. Een reviewer die vandaag naar de tekst kijkt en concludeert "dit criterium is niet toetsbaar" heeft geen veld om dat in te zetten. Het oordeel bestaat alleen in zijn hoofd en hoogstens in `toelichting_proces` (vrij tekstveld). Dat is niet versiegebonden, niet machineleesbaar, en niet door enige poort te lezen.

**[CODE] Import.** `nalevering-4cdb8ea43/src/services/definition_import_service.py`: `validate_single()` berekent `ok = validation.get("is_acceptable")`, maar `import_single()` gebruikt `preview.ok` **nergens**; het blokkeert alleen op duplicaten. De validatie-uitkomst wordt na de duplicaatcontrole weggegooid — er wordt geen `validation_score`, geen `validation_issues` en geen reviewregister bij het record opgeslagen. Het record krijgt `status="draft"`, `source_type="imported"`.

**[INTERPRETATIE]** Gevolg voor ESS-04: een geïmporteerde definitie draagt géén spoor van de reviewplicht. Dat is deels afgevangen — de vaststelgate blokkeert op `validation_score is None` met "Geen validatieresultaat beschikbaar (eerst (her)valideren)" **[CODE]** `definition_workflow_service.py:753` — dus importeren-en-meteen-vaststellen kan niet. Maar zodra iemand één keer hervalideert, is de score gevuld en is ESS-04 opnieuw onzichtbaar voor de poort (§5.7). Het fail-closed-gedrag hangt hier aan de score, niet aan de review.

**[CODE]** Terzijde: `import_single` zet een `asyncio.wait_for(..., timeout=2.0)` om validatie + duplicaatcontrole samen. Bij overschrijding: geen import, met melding. Fail-closed, maar 2 seconden is krap voor een validatie die 53 regels draait; buiten ESS-04-scope, wel het melden waard.

### 5.7 Vaststelling — het centrale bewijs

**[CODE]** `definition_workflow_service.py`, `_evaluate_gate` (regels 715–840). De poort kijkt naar, en uitsluitend naar:

1. aanwezigheid van minimaal één context (org./jur./wettelijk);
2. `validation_score` — `None` ⇒ blokkade "Geen validatieresultaat beschikbaar"; onder `hard_min` ⇒ blokkade; tussen soft en hard ⇒ `override_required`;
3. severities in `validation_issues` — `critical` ⇒ blokkade, `high` ⇒ override;
4. `_con01_blokkades(definition)` — niet-overrulebaar;
5. `_con02_blokkades(definition)` — niet-overrulebaar;
6. ontbrekende wettelijke basis ⇒ soft.

**[CODE]** `_con01_blokkades` (regel 861 e.v.) herberekent de CON-01-uitkomst op het record en gebruikt de opgeslagen expertbeoordeling, "die telt alleen wanneer haar vingerafdruk bij de huidige tekst, context en term hoort. Uitkomsten: Voldoet → geen blokkade; Voldoet niet → blokkade met de reden; **Nog te beoordelen → blokkade** met wat er nog beoordeeld moet worden."

**[INTERPRETATIE]** Dat is exact het gedrag dat DEF-630 voor álle verplichte `review_required`-uitkomsten voorschrijft — en het bestaat, werkend, voor twee regels. **Voor ESS-04 bestaat het niet.** Er is geen verwijzing naar `review_required`, `rule_statuses` of `evaluation_coverage` in de hele gatefunctie.

**Bewezen gevolg [CODE], niet met een proef bevestigd:** een definitie met een voldoende `validation_score`, ingevulde context, geen kritieke issues, een geldige CON-01-beoordeling en een geldig CON-02-bronbewijs wordt vastgesteld (`DefinitieStatus.ESTABLISHED`) terwijl ESS-04 de status `review_required` draagt en nooit door een mens is beoordeeld. De poort ziet die status niet, en kan hem ook niet zien: hij staat nergens op het record.

**[BESLUIT]** DEF-630, audit 15 september 2026: "twee verse proeven zonder opgeslagen validatiebewijs slagen nog bij handmatige approve. Null-score geeft override_required; score 0.95 geeft gate pass." **[INTERPRETATIE]** Dat is onafhankelijk, verser bewijs uit het project zelf dat de poort op de score leunt en niet op reviewbewijs. Mijn codelezing is daarmee consistent.

**Bewijsniveau:** codelezing, ondersteund door een vastgelegde projectproef (DEF-630-audit). Geen eigen end-to-end-proef — dat zou databaseschrijven vragen en valt buiten de toegestane scope.

### 5.8 Export en herbeoordeling

**[CODE]** `export_service.py` regels 456–468: niet-draft-export eist een uitgevoerde run (`is_uitgevoerde_run`) én `is_acceptable`. **[CODE]** De JSON-export draagt `validatie.toetsresultaten`, `review.expert_review` en `bronnen.bronbewijs`.

**[INTERPRETATIE]** De exportpoort erft precies het gat uit §5.7: `is_acceptable` weet niets van openstaande reviewplichten. En omdat er geen ESS-04-reviewveld is, kan het exportbestand ook niet vermelden dat ESS-04 nog open staat. Een ontvanger van de export ziet een definitie die er beoordeeld uitziet.

### 5.9 Generatie

**[CODE]** `json_based_rules_module.py:331`: de volledige ESS-04-generatie-instructie is één regel:

> "Gebruik objectief toetsbare elementen (deadlines, aantallen, percentages, meetbare criteria)"

**[CODE]** Ter vergelijking: ESS-01 (regels 308–325) en CON-02 kregen uitgebreide instructies met bronregels, verbod op verzinnen, omgang met ontbrekende informatie en het onderscheid voorstel/bewijs. ESS-02 verwijst naar een gedeelde aanwijzing.

**[INTERPRETATIE]** Dit is de tweede grote bevinding naast §5.7. De instructie **vraagt het model letterlijk om deadlines, aantallen en percentages** te gebruiken. Er staat geen woord over: geen drempel verzinnen die de bron niet draagt; een percentage altijd met noemer; een dagtermijn altijd met werk- of kalenderdag; kwalitatieve criteria zijn gelijkwaardig. De instructie is dus de directe generatieve oorzaak van de risico's die het dossier wil vermijden — en hij is erfelijk: hij komt uit dezelfde verschoven `uitleg` van §2.3.

**[CODE]** `opschoning.py`: de nabewerking verwijdert alleen vormconstructies aan het begin (lidwoorden, koppelwerkwoorden) en dwingt hoofdletter en punt af; sinds DEF-622 blijven betekenisdragende frasen staan. **[INTERPRETATIE]** Geen ESS-04-relevant betekenisverlies te verwachten: de opschoning raakt het begin van de zin, criteria staan doorgaans verderop. Wel: opschoning draait bij generatie en **niet** bij import (§5.6) — dezelfde tekst kan dus langs twee ingangen als twee verschillende strings worden getoetst. Voor ESS-04 is dat effect klein maar niet nul (`bevat` aan het zinsbegin).

**[CODE]** `definition_orchestrator_v2.py` regels 1815–1866 (`_toets_kandidaat`): de getoetste kandidaat is exact de opgeslagen kandidaat; wijzigt de validatie de tekst tóch, dan wordt hertoetst; blijft dat gebeuren, dan `KandidaatNietStabielError` en **niets opslaan**. Sterk en correct.

**[CODE]** `_herstelbare_overtredingen` (regel 1909): alleen `violations` komen in aanmerking, met uitsluiting van regels zonder cijfer. **[INTERPRETATIE]** ESS-04 produceert nooit een violation, dus ESS-04 kan nooit automatisch tekstherstel uitlokken. Correct, en het blijft correct zolang de evaluator `review_required` levert. **[BESLUIT]** De herstelservice is bovendien niet geactiveerd (`enhancement_service=None`, DEF-638).

### 5.10 Bewerken en conceptopslag

**[CODE]** `definition_edit_tab.py` is met 2501 regels het grootst gewijzigde bestand tussen de twee commits (1045 gewijzigde regels). Ik heb er geen ESS-04-specifieke logica in aangetroffen (`grep ESS-04` levert alleen de vijf plaatsen van §5.1). **[INTERPRETATIE]** Dat is zelf de bevinding: de bewerkroute kent ESS-04 niet en kan dus ook geen eerder oordeel invalideren — wat vandaag niet uitmaakt omdat er geen oordeel te invalideren is, maar wat §6.6 wél moet regelen.

---

## 6. Q5 — Concrete teksten: regel, G, T, H, meldingen, skills

Alle voorstellen met huidige vindplaats. Voorstellen, geen besluiten.

### 6.1 Regelrecord — `src/toetsregels/regels/ESS-04.json`

**Huidige `uitleg`:**
> "Een definitie bevat objectief toetsbare elementen (harde deadlines, aantallen, percentages, meetbare criteria)."

**Probleem:** verplaatst het toetsobject van criterium naar definitie, maakt van een kwaliteitseis een aanwijzigheidseis, en zet numerieke vormen voorop (§2.3).

**[VOORSTEL] vervangende `uitleg`:**
> "Ieder criterium in de definitie is zo bepaald dat een gebruiker aan een concreet geval kan vaststellen of het criterium is vervuld, en de criteria samen beslissen of het geval onder het begrip valt. Een criterium mag kwalitatief zijn; een getal, termijn of percentage is niet vereist en op zichzelf niet voldoende."

**Huidige `toelichting`:**
> "Zonder toetsbare criteria kan een lezer niet objectief vaststellen of iets onder de definitie valt. Voorbeelden van *niet*-toetsbaar: 'zo snel mogelijk', 'zo veel mogelijk'. Wél-toetsbaar: 'binnen 3 dagen', 'tenminste 80%', 'uiterlijk na 1 week'."

**[VOORSTEL] vervangende `toelichting`:**
> "Zonder toetsbare criteria kan een lezer niet vaststellen of een geval onder het begrip valt. De scheidslijn is bepaald tegenover onbepaald, niet numeriek tegenover kwalitatief. Niet toetsbaar zijn onbepaaldheidsformules ('zo snel mogelijk', 'zo veel mogelijk', 'zo mogelijk') en beoordelende kwalificaties zonder maatstaf ('belangrijk', 'relevant', 'adequaat'). Wel toetsbaar zijn bepaalde termijnen met startpunt ('binnen 3 dagen nadat het verzoek is ingediend'), aandelen met noemer ('tenminste 80% van de aanvragen'), uiterste termijnen ('uiterlijk na 1 week') en kwalitatieve criteria die een aanwijsbaar kenmerk noemen ('waarvan alle zijden even lang zijn', 'waarop de afzender een handtekening heeft geplaatst'). Een getal maakt een criterium niet toetsbaar wanneer het meetobject, de noemer, de grens of het referentiemoment ontbreekt, of wanneer de zin daarnaast onbeoordeelbare kwalificaties bevat."

**[VOORSTEL] `thema`:** `"toepasbaarheid"` → `"essentie van het begrip"`, conform ASTRA **[BRON]**.

**[VOORSTEL] `relatie`:** voeg de door ASTRA gelegde relatie toe en behoud de eigen vindplaats:
```json
"relatie": [
  {"fulltext": "Toetsbaarheid", "fullurl": "https://www.astraonline.nl/index.php/Toetsbaarheid"},
  {"fulltext": "Instanties uniek onderscheidbaar", "fullurl": "https://www.astraonline.nl/index.php/Instanties_uniek_onderscheidbaar"}
]
```

**[VOORSTEL] `goede_voorbeelden` / `foute_voorbeelden`:** de huidige zijn ASTRA-zinsfragmenten, geen definities. Aanvullen met volledige, zelf onderscheidende gevallen (zonder de ASTRA-fragmenten te verwijderen):

- goed: "Document waarop de afzender een handtekening heeft geplaatst." *(kwalitatief, toetsbaar — sluit de numerieke lezing uit)*
- fout: "Belangrijke aanvraag die binnen 3 dagen relevant wordt." *(schijnprecisie — sluit de "een getal is genoeg"-lezing uit)*

**[VOORSTEL] `herkenbaar_patronen`.** Twee opties; ik geef mijn voorkeur en het alternatief.

*Voorkeur — de patronen omdraaien naar onbepaaldheid.* De huidige lijst zoekt naar bewijs van toetsbaarheid, wat principieel niet kan (afwezigheid van een trefwoord bewijst niets) en bovendien defect is. De ASTRA-FOUT-voorbeelden zijn wél patroonvormig:

```json
"herkenbaar_patronen": [
  "\\bzo\\s+(snel|veel|spoedig|vaak|kort|lang)\\s+mogelijk\\b",
  "\\bzo\\s+mogelijk\\b",
  "\\bindien\\s+mogelijk\\b",
  "\\bwaar\\s+nodig\\b",
  "\\bin\\s+beginsel\\b",
  "\\bdoorgaans\\b",
  "\\bregelmatig\\b",
  "\\btijdig\\b",
  "\\bvoldoende\\b",
  "\\bsubstanti(eel|ele)\\b",
  "\\bpassend(e)?\\b",
  "\\bredelijk(e)?\\b",
  "\\bgeruime\\s+tijd\\b",
  "\\b\\d+(?:[.,]\\d+)?\\s*%",
  "\\bbinnen\\s+\\d+\\s+(dag|dagen|week|weken|maand|maanden|werkdag|werkdagen)\\b",
  "\\buiterlijk\\s+(na|binnen|op)\\s+\\d+\\s+(dag|dagen|week|weken|maand|maanden|werkdag|werkdagen)\\b",
  "\\b(tenminste|ten\\s+minste|minimaal|maximaal|ten\\s+hoogste)\\s+\\d+(?:[.,]\\d+)?\\s*%"
]
```

De eerste dertien wijzen onbepaaldheid aan (*kijk hier, dit is vermoedelijk niet toetsbaar*); de laatste vier wijzen drempels aan (*kijk hier, controleer noemer, grens en referentietijd*). Beide zijn voor de reviewer nuttig; geen van beide is bewijs. De `%`-patronen eindigen bewust **niet** op `\b` en staan `12,5 %` toe; de termijnpatronen noemen enkelvoud, meervoud en werkdagen expliciet.

**`\bbevat\b`, `\bomvat\b`, `\bheeft als eigenschap\b`, `\bwordt gekenmerkt door\b`, `\bcontrole op\b`, `\baan de hand van\b`, `\bobjectieve criteria\b`, `\bwaarneembare\b`, `\btoetsbaar\b` [VOORSTEL] vervallen**: zij vuren op de vorm van willekeurig welke definitiezin en zijn de zuivere trefwoord-pass (§5.2, casus C09/C10).

*Alternatief, als "signalen moeten aanwijzen waar het goed zit" de voorkeur houdt:* behoud de huidige opzet maar repareer de vier `%`-patronen (`\b` na `%` weghalen) en de twee termijnpatronen (enkelvoud toevoegen), en verwijder alleen `bevat`/`omvat`. Dat is de kleinere ingreep; hij lost de defecten op maar niet de misleidende richting.

**`runtime_contract` [VOORSTEL] ongewijzigd**: `judgment_review` / `review_required` / `excluded_from_score` blijven. §5.2 is een argument vóór behoud, niet tegen. Alleen `example_pair_reason` behoeft correctie — de huidige tekst beschrijft het defect onjuist:

> **[VOORSTEL]** "toetsbaarheid is een inhoudelijk oordeel; de indicatorpatronen wijzen hoogstens een passage aan en zijn geen bewijs. De patronen missen bovendien twee van de drie ASTRA-GOED-voorbeelden ('tenminste 80% van de …', 'uiterlijk na 1 week') en vuren op vormwoorden die in vrijwel elke definitiezin staan."

### 6.2 G — generatie-instructie

**Huidige vindplaats 1:** `src/services/prompts/modules/json_based_rules_module.py:331`.
**Huidige vindplaats 2:** `feitenbasis/actieve-skills/definitie-toetsregels/reference.md:47` (zelfde tekst, in de regeltabel).

**Huidige tekst:**
> "Gebruik objectief toetsbare elementen (deadlines, aantallen, percentages, meetbare criteria)"

**[VOORSTEL] vervangende tekst (beide vindplaatsen gelijkluidend):**

> Formuleer ieder criterium in de definitiekern zo dat een gebruiker aan een concreet geval kan vaststellen of eraan is voldaan. Vermijd onbepaaldheidsformules ('zo snel mogelijk', 'zo veel mogelijk', 'waar nodig', 'tijdig') en beoordelende kwalificaties zonder maatstaf ('belangrijk', 'relevant', 'passend', 'voldoende'). Een kwalitatief criterium dat een aanwijsbaar kenmerk noemt is volwaardig; een getal is niet vereist. Neem een getal, termijn, percentage of grenswaarde **alleen** op wanneer de aangeleverde bron of de bevestigde context die waarde draagt — verzin geen drempel en leid er geen af uit een voorbeeld. Wanneer je een drempel opneemt, maak in dezelfde zin het meetobject, en bij een aandeel de noemer, expliciet; noem bij een termijn in dagen of het werkdagen of kalenderdagen zijn en vanaf welk moment wordt geteld. Voeg geen registratiecontext toe: volg het bestaande CON-01-beleid, waarin alleen een inhoudelijk noodzakelijke afbakening in de zin thuishoort. Ontbreekt de grond voor een noodzakelijke grens, gebruik dan geen getal maar benoem het ontbrekende gegeven apart bij de kandidaat; lever hoogstens een herkenbaar voorlopig voorstel. Methode, meetprocedure of rekenvoorbeeld horen in een apart toelichtingsvoorstel, niet in de kern. Verzin geen bron, geen meetcontext en geen menselijke beoordeling.

**[INTERPRETATIE]** Wat de app vóóraf moet controleren en wat modelvoorstel blijft: de app controleert beschikbaarheid en versie van term, context en aangeleverde bron, en maakt ontbrekende gegevens zichtbaar. Zij maakt daarmee géén veld verplicht. Of een opgenomen drempel werkelijk door de bron wordt gedragen is een CON-02-vraag en geen ESS-04-generatiecontrole. De generator levert nooit een menselijke beoordeling.

### 6.3 T — toetsinstructie

**Huidige vindplaats:** er is geen ESS-04-toetsinstructie. Wat de reviewer krijgt is `record["toetsvraag"]`, letterlijk doorgegeven door `judgment_review.evaluate` (§5.2). De vindplaats voor een nieuwe instructie, volgens het bestaande patroon: `feitenbasis/actieve-skills/definitie-toetsregels/references/ess04-toetsbaarheid.md`, met een verwijzende sectie in `definitie-toetsregels/SKILL.md` naast de bestaande ESS-01- en ESS-02-secties.

**[VOORSTEL] exacte toetsinstructie:**

> Beoordeel de ongewijzigde definitiekern op haar vastgelegde versie, samen met de vastgelegde term en context. Toets niet de zin als geheel, maar **ieder criterium afzonderlijk**.
>
> Vraag per criterium: (a) *aanwijsbaarheid* — wijst het een eigenschap aan die aan een geval valt te constateren, of vraagt het een oordeel over het geval? (b) *bepaaldheid* — ligt de grens vast, of verschuift zij per beoordelaar? (c) *verankering* — als het criterium afhangt van een bron, register, peildatum of populatie, is die aanwijsbaar? Vraag daarna over de criteria samen: (d) *volledigheid* — beslissen zij een gewoon geval, of blijft er een grijs gebied waarin twee redelijke beoordelaars anders zouden oordelen?
>
> Een criterium mag kwalitatief zijn. Afwezigheid van een getal is nooit een grond voor 'voldoet niet'. Aanwezigheid van een getal is nooit een grond voor 'voldoet': controleer bij een aandeel de noemer, bij een drempelwaarde of de grens inclusief of exclusief is, bij een termijn in dagen of het werkdagen of kalenderdagen betreft en vanaf welk moment wordt geteld, en bij een tijdsafhankelijke eigenschap het referentiemoment. Controleer ook of de zin naast het bepaalde criterium onbeoordeelbare kwalificaties bevat die het oordeel alsnog openlaten.
>
> Beoordeel niet of het gekozen criterium het *juiste* of *essentiële* criterium is — dat is ESS-01 en ESS-05. Beoordeel niet of instanties telbaar zijn — dat is ESS-03. Beoordeel niet of een gebruikt getal door de bron wordt gedragen — dat is CON-02; signaleer het wel als waarneming. Een reproduceerbaar vast te stellen eigenschap kan volstrekt niet-begripsbepalend zijn en toch aan ESS-04 voldoen.
>
> Uitkomsten, gescheiden: **voldoet aan ESS-04** alleen wanneer alle criteria (a)–(c) doorstaan en (d) geen grijs gebied laat; **voldoet niet** bij een bevestigd onbepaald of niet-aanwijsbaar criterium, met citaat van de passage en de grond; **nog te beoordelen** bij echte twijfel of wanneer een noodzakelijk gegeven (context, bron, peildatum) ontbreekt — noem dan wélk gegeven; **niet beoordeelbaar** bij lege of afgebroken tekst; **technisch probleem** bij een fout in de uitvoering. Een patroonsignaal is geen van deze uitkomsten: geen treffer betekent nooit 'voldoet', een treffer nooit 'voldoet niet'.
>
> Noteer per uitkomst: de beoordeelde passage, de grond, en de recordversie waarop is beoordeeld. Toetsen verandert de invoer niet; een betere formulering is een apart voorstel.

**[INTERPRETATIE]** Dezelfde instructie geldt voor gegenereerde en aangeleverde inhoud. Geen milder oordeel voor import, geen strenger oordeel voor AI-uitvoer.

### 6.4 Appmeldingen

**Huidige vindplaats 1:** `judgment_review.evaluate`, `reden = toetsvraag` — de gebruiker leest: *"Bevat de definitie elementen waarmee je objectief kunt vaststellen of iets wel of niet onder het begrip valt?"* zonder passage, zonder wat te doen.
**Huidige vindplaats 2:** `validation_view.py:734-739` — ESS-04 is uitgesloten van de altijd-zichtbare reden.

**[VOORSTEL]** Sluit ESS-04 aan op het bestaande `_reden_met_passages`-sjabloon (het staat er al, §5.2), met een eigen kop en vraag:

> **Kop:** "ESS-04 — Nog te beoordelen: kan een gebruiker aan een concreet geval vaststellen of het onder dit begrip valt? Beoordeel ieder criterium afzonderlijk op aanwijsbaarheid en bepaaldheid, en de criteria samen op volledigheid. Een kwalitatief criterium volstaat; een getal is niet vereist en op zichzelf niet voldoende."
>
> **Vraag bij een passage:** "Maakt deze passage vaststelbaar of een geval onder het begrip valt, of laat zij dat open? Controleer bij een getal het meetobject, de noemer, de grens en het referentiemoment."
>
> **Zonder treffer:** "Geen patroonsignaal gevonden; inhoudelijke beoordeling blijft nodig." *(bestaande tekst van het sjabloon, ongewijzigd)*

**[VOORSTEL]** Aparte melding bij lege of te korte tekst (§5.4, casus C07), zodat ontbrekende invoer niet dezelfde tekst krijgt als een volle definitie:
> "ESS-04 — Niet beoordeelbaar: er is geen definitietekst om criteria in te beoordelen."

**[VOORSTEL]** Ruim de twee dode plekken op (§5.5), niet als opschoning maar omdat hun tekst het verboden gedrag beschrijft:
- `validation_renderer.py:353` — haal `"ESS-04"` uit `{"ESS-03","ESS-04","ESS-05"}` en zet er, net als bij ESS-02, een comment: ESS-04 is reviewplichtig en komt nooit als geslaagde regel binnen.
- `modular_validation_service.py:1938` — de `reason == "testable"`-suggestie ("bijv. termijn of meetbare grens") is onbereikbaar en stuurt bovendien naar de numerieke lezing; laten vervallen, of vervangen door "Maak het criterium zo bepaald dat een gebruiker aan een geval kan vaststellen of eraan is voldaan."

### 6.5 Voorkomen van dubbele afkeur

**[VOORSTEL]** ARAI-03 en ESS-04 vuren beide op "belangrijk"/"relevant" (§4.2). Beide zijn `review_required`, dus er ontstaat geen dubbele *afkeuring*, wel een dubbele *reviewlast* voor hetzelfde woord. Aanbeveling: laat de ESS-04-reviewtekst de grond expliciet noemen ("dit woord laat het lidmaatschap open" — een ander verwijt dan ARAI-03's "dit woord is subjectief"), en voeg géén ARAI-03-woordenlijst toe aan de ESS-04-patronen. De enige overlap die ik in mijn voorgestelde patroonlijst laat staan is `voldoende`, `substantieel`, `passend`, `redelijk` — die staan niet in ARAI-03's lijst (`effectief`, `belangrijk`, `relevant`, `toereikend`, `adequaat`) en vullen hem dus aan in plaats van hem te dupliceren.

### 6.6 H — diagnose en begrensde terugkoppeling

**[VOORSTEL] exacte diagnose-instructie:**

> Stel vóór enig hersteladvies de oorzaak vast, met de oorspronkelijke modeluitvoer, de nabewerking en exact de bewaarde kandidaat naast elkaar. Onderscheid:
>
> 1. **Generatieovertreding** — het model gebruikte een onbepaaldheidsformule of een beoordelende kwalificatie waar de invoer een bepaald criterium toeliet.
> 2. **Instructie- of normconflict** — de generatie-instructie vroeg een drempel die de bron niet draagt; de instructie zelf is de fout, niet de uitvoer. *(Zolang de huidige G-tekst van §6.2 niet is vervangen, is dit een reële en waarschijnlijke diagnose.)*
> 3. **Invoer- of transportverlies** — het criterium stond in de modeluitvoer en is in de nabewerking verdwenen, of de getoetste tekst wijkt af van de bewaarde kandidaat.
> 4. **Foutpositieve evaluator** — het signaal wees een passage aan die wel degelijk bepaald is; of, omgekeerd, een bepaald criterium kreeg geen signaal. Gezien §5.2 is dit bij ESS-04 een veelvoorkomende toestand en géén bewijs van een tekstfout.
> 5. **Ontbrekend bewijs** — het criterium hangt af van een bron, peildatum of populatie die niet is aangeleverd. Dan is er niets te herstellen: het gegeven moet komen, niet de tekst veranderen.
> 6. **Technische fout** — de evaluatie is niet uitgevoerd.
> 7. **Schadelijke nabewerking** — een opschoon- of herstelstap heeft het criterium gewijzigd of verwijderd.
>
> Een openstaande reviewplicht is **geen** van deze zeven en is dus nooit een herstelgrond: ESS-04 levert geen `fail` en start daarom niets.

**[VOORSTEL] begrensde herstelinstructie (voorstel voor later; activeert niets):**

> Herstel op ESS-04 is alleen toegestaan na een afzonderlijke gebruikersopdracht en alleen bij diagnose 1 of 7. Herstel is niet toegestaan bij 2, 4, 5 en 6 — daar wordt de instructie, het signaal, het gegeven of de storing aangepakt, niet de tekst.
>
> Beschermd en niet te wijzigen: de betekenis van de kern, brongetrouwheid en bronpassages, namen die nodig zijn om het begrip af te bakenen, de term, de registratiecontext, de recordidentiteit en alle door de gebruiker ingevoerde tekst. **Er wordt nooit een getal, termijn, percentage, noemer, peildatum of grenswaarde toegevoegd die niet in de aangeleverde bron of bevestigde context staat.** Dat is de enige ESS-04-specifieke bescherming die er echt toe doet: het verschil tussen herstel en verzinnen is hier precies één cijfer.
>
> Toegestane herstelhandelingen: een onbepaaldheidsformule vervangen door een criterium dat uit de aangeleverde bron volgt; een beoordelende kwalificatie schrappen wanneer de overige criteria het geval al beslissen; een aanwezige maar impliciete meetcontext (noemer, werkdag/kalenderdag, startmoment) expliciteren **uitsluitend** wanneer die uit de bron of context blijkt. Alles wat een nieuwe grens invoert is geen herstel.
>
> Maximaal één poging, als productkeuze (conform DEF-638; dit onderzoek stelt geen aantal vast). Stop bij: herhaling zonder verbetering, betekenisverlies, bronconflict, een vermoedelijk foutpositief signaal, ontbrekend bewijs, of wanneer het herstel een andere regel zou schenden.
>
> Bewaar oorspronkelijke uitvoer, herstelgrond, diff en stopreden. Toets de gewijzigde tekst opnieuw op ESS-04 **en** op de geraakte buurregels; bij onbekende afhankelijkheden op alle toepasselijke controles. Een eerder menselijk ESS-04-oordeel over de oude tekst vervalt bij elke wijziging en geldt nooit als goedkeuring van de nieuwe tekst.
>
> Wat de gebruiker ziet: bij succes de nieuwe kandidaat als **concept** met diff en resterende onzekerheden, en de vermelding dat de menselijke ESS-04-beoordeling opnieuw nodig is; bij een open beoordeling het ontbrekende gegeven; bij storing de technische fout apart; bij uitgeputte pogingen de oorspronkelijke kandidaat met de stopreden. Toetsresultaat, conceptstatus, expertbeoordeling en vaststelling blijven vier gescheiden dingen.

### 6.7 Opslag en poort — het herstel van DEF-630

**[VOORSTEL]** Dit is de enige voorgestelde gedragswijziging buiten tekst. Ik beschrijf hem als voorstel; de beslissing is §7.4-keuze B.

Naar het bestaande CON-01-model, dat aantoonbaar werkt:

1. **Opslag.** Eén reviewveld per reviewplichtige regel, met dezelfde vorm als `context_review`: uitkomst (`voldoet` / `voldoet niet` / `nog te beoordelen` / `niet beoordeelbaar`), motivering, actor, tijdstip, en een vingerafdruk over de beoordeelde tekst + term + context + normversie. Schrijfpad naar analogie van `set_context_review(..., expected_version=...)` **[CODE]** `definition_repository.py:1426`.
2. **Herberekening op het record**, niet hergebruik van een oude runuitkomst — precies zoals `_con01_blokkades` het doet: de beoordeling telt alleen wanneer haar vingerafdruk bij de huidige tekst en context hoort. Een bewerking maakt het oordeel automatisch ongeldig, zonder aparte invalidatiecode.
3. **Poort.** In `_evaluate_gate`: een reviewplichtige regel zonder geldige beoordeling levert een blokkade in `niet_overrulebaar`, met de reden "ESS-04 is nog niet beoordeeld". Conform DEF-630: niet met een notitie op te heffen.
4. **Weergave en export.** De uitkomst verschijnt in de reviewtab naast CON-01/CON-02, en in de JSON-export onder `review`.

**[INTERPRETATIE]** Reikwijdte is hier de gevoelige vraag. ESS-04 is één van dertien reviewplichtige regels **[CODE]** `judgment_review.py` docstring. Een poort die alleen op ESS-04 blokkeert is inconsistent; een poort die op alle dertien blokkeert maakt vaststellen in één klap dertien keer zwaarder. Dat is geen ESS-04-besluit maar een appbreed besluit onder DEF-630, en ik leg het als zodanig voor (§7.4-B). Wat ik hier vaststel is uitsluitend: **het mechanisme bestaat al voor twee regels, het is voor alle verplichte reviewuitkomsten besloten, en het ontbreekt voor ESS-04.**

### 6.8 Skills

**Vindplaats 1:** `definitie-toetsregels/reference.md:47` — de regeltabelrij. **[VOORSTEL]** vervang de generatie-instructiekolom door de tekst van §6.2.

**Vindplaats 2:** `definitie-toetsregels/SKILL.md` — bevat secties voor CON-02, ESS-01 en ESS-02, elk verwijzend naar een `references/*.md`. **[VOORSTEL]** voeg een gelijkvormige ESS-04-sectie toe:

> ## ESS-04 — toetsbaarheid van criteria
>
> Lees bij genereren of toetsen het [gedeelde ESS-04-contract](references/ess04-toetsbaarheid.md). ESS-04 eist dat ieder criterium in de kern bepaald genoeg is om aan een concreet geval vast te stellen of eraan is voldaan, en dat de criteria samen het geval beslissen. De scheidslijn is bepaald tegenover onbepaald, niet numeriek tegenover kwalitatief: een kwalitatief criterium volstaat, en een getal is op zichzelf niet voldoende. Neem geen drempel op die de bron niet draagt; maak bij een aandeel de noemer, bij een dagtermijn werk- of kalenderdagen en bij een tijdsafhankelijk kenmerk het referentiemoment expliciet. ESS-04 oordeelt niet over de juistheid of essentie van het gekozen criterium (ESS-01/ESS-05), niet over telbaarheid (ESS-03) en niet over brongezag (CON-02). De app geeft signalen; de mens beoordeelt. Geen ESS-04-cijfer. Skilladvies is geen opgeslagen menselijke beoordeling.

**Vindplaats 3 [VOORSTEL] nieuw:** `definitie-toetsregels/references/ess04-toetsbaarheid.md`, met N/G/T/H-structuur naar het model van `ess01-functiegrens.md`: de normtekst van §2.1–2.2, de G van §6.2, de T van §6.3, de H van §6.6, plus de grensgevallen van §7.1.

**Vindplaats 4:** `definitie-nederlandse-definities/SKILL.md`. **[VOORSTEL]** geen wijziging. ESS-04 is geen formuleringsregel; een taalregel die numerieke formulering aanbeveelt zou precies de verboden stijl-afkeurgrond invoeren.

**Vindplaats 5:** `definitie-voorbeelden-generatie`. **[VOORSTEL]** geen wijziging aan de skill; wel de waarneming dat grensgevallen bij een drempel de belangrijkste ondersteunende uitvoer voor ESS-04 zijn (§3.2) en dat die koppeling nergens is vastgelegd. Kandidaat voor een latere, aparte aanvulling.

---

## 7. Q6 — Casussen, risico's, keuzes

### 7.1 Onderscheidende casussen

Volledig register in bijlage A; hier de gevallen die tússen de opties beslissen. De zeven historische labels zijn behouden en aan stabiele ID's gekoppeld.

| ID | Invoer | Wat het onderscheidt | G verwacht | T verwacht | H toegestaan |
|---|---|---|---|---|---|
| **C03** `non_numeric` | "Veelhoek waarvan alle zijden even lang zijn." | **De hele numerieke lezing.** Als ESS-04 een getal eist, faalt dit; volgens de norm voldoet het | criterium behouden; geen getal toevoegen | voldoet | geen herstel |
| **C04** `unfounded_number` | "Belangrijke aanvraag die binnen 3 dagen relevant wordt." | **Schijnprecisie.** Als ESS-04 per zin kijkt, slaagt dit; per criterium faalt het | "belangrijke"/"relevant" niet gebruiken | voldoet niet; citeer beide kwalificaties | schrappen mag; geen drempel toevoegen |
| **C05** `ambiguous_measure` | "Object dat minimaal 80% voldoet." | **Noemer.** Getal aanwezig, meetobject en noemer afwezig | percentage alleen met noemer | voldoet niet (of open bij ontbrekende context) | noemer alleen expliciteren als bron hem draagt |
| **C06** `observable` | "Document waarop de afzender een handtekening heeft geplaatst." | **Nominale eigenschap.** Toetsbaar zonder magnitude (VIM3 §1.30) | prima uitvoer | voldoet | geen herstel |
| **C12** | "Beslissing die binnen drie dagen wordt genomen." | **Vorm versus inhoud.** Inhoudelijk identiek aan C01, maar het getal staat in letters | gelijkwaardig aan C01 | voldoet — gelijk aan C01 | geen herstel |
| **C13** | "Aanvraag die binnen 3 werkdagen na ontvangst wordt behandeld." | **Werk- versus kalenderdag.** Explicieter dan C01 en toch patroonloos | voorbeeldig | voldoet | geen herstel |
| **C10** | "Melding die zo snel mogelijk wordt gedaan en het dossiernummer bevat." | **Trefwoord-pass.** ASTRA-FOUT-formulering die van de huidige patronen een positief signaal krijgt | onbepaaldheidsformule vermijden | voldoet niet | "zo snel mogelijk" alleen vervangen als de bron een termijn draagt |
| **C14** | "Kandidaat die minimaal 80%voldoet." | **Controlegeval** dat de `\b`-fout aantoont; inhoudelijk hetzelfde als C05 | n.v.t. | gelijk aan C05 | n.v.t. |

**[INTERPRETATIE]** C03/C06 tegenover C04/C05 is het scharnier van dit hele dossier: twee tekstsoorten zonder getal die vóldoen, en twee mét getal die niet voldoen. Elke regelformulering die deze vier niet correct sorteert, is fout. De huidige `uitleg` sorteert ze verkeerd om.

### 7.2 Risico's en bewijsgaten

| # | Risico of gat | Ernst | Wat het zou wegnemen |
|---|---|---|---|
| R1 | Vaststelling zonder ESS-04-beoordeling (§5.7) | **hoog** — raakt de betrouwbaarheid van elke vastgestelde definitie | §6.7 / keuze B |
| R2 | Generatie-instructie vraagt om getallen (§5.9) | **hoog** — produceert actief de schijnprecisie die de norm verbiedt | §6.2 (tekst, geen besluit nodig) |
| R3 | Patroondefecten (§5.2) | midden — stuurt reviewaandacht verkeerd; wordt hoog zodra iemand automatiseert | §6.1 |
| R4 | Export draagt openstaande reviewplicht niet mee (§5.8) | midden | volgt uit §6.7 |
| R5 | Dode pass-tekst "Vereist element herkend (heuristiek)" (§5.5) | midden — terugvalrisico bij volgende wijziging | §6.4 |
| R6 | Import bewaart geen validatie-uitkomst (§5.6) | midden — nu afgevangen door de scoregate, breekt zodra iemand hervalideert | volgt uit §6.7 |
| R7 | ESS-04 niet zichtbaar voor de gebruiker (§5.5) | midden | §6.4 |
| R8 | **Geen UI-bewijs.** Alles over weergave, reviewregistratie en vaststelling is codelezing | — | een UI-proef; buiten de toegestane scope van dit onderzoek |
| R9 | **`validation.additional_patterns` niet leesbaar** — er kunnen extra ESS-04-signalen bestaan die ik niet ken (§8) | — | één bestand |
| R10 | **Geen eigen end-to-end-proef** van generatie→opslag→vaststelling | — | vraagt databaseschrijven; buiten scope |
| R11 | De synthetische gevallen in bijlage A zijn **geen gevalideerde juridische praktijkgevallen** en hebben geen expertgold | — | onafhankelijk gelabelde grensgevallen (§7.3) |

### 7.3 Twee onafhankelijke beoordelaars — wat ik er wél en niet van maak

**[BRON]** De formulering staat bij ESS-03, niet bij ESS-04 (§4.1). **[INTERPRETATIE]** Daarom:

- **Niet voorstellen:** een verplichte tweede beoordelaar als vaststelvoorwaarde voor ESS-04. Daar is geen bronbasis voor, en `cowork-opdracht-v1.md` stelt uitdrukkelijk dat algemene expertbeoordeling en handmatige vaststelling blijven gelden en dat een verplichte tweede persoon *niet* is besloten.
- **Wel voorstellen, als onderzoeksinstrument:** laat twee mensen onafhankelijk een set grensgevallen labelen (voldoet / voldoet niet / nog te beoordelen) vóórdat de nieuwe toetsinstructie (§6.3) wordt vastgesteld. Divergentie meet dan de duidelijkheid van de instructie, niet de kwaliteit van de definities. Scheid daarbij divergentie over *betekenis* (ESS-03/ESS-05-signaal) van divergentie over *toepassing* (ESS-04-signaal) — §4.1.
- **Verwachting vooraf, te toetsen:** ik verwacht dat C03, C06, C12 en C13 eensluidend "voldoet" krijgen en C02, C04, C10 eensluidend "voldoet niet"; dat C05 uiteenvalt afhankelijk van of de beoordelaar de ontbrekende noemer als "voldoet niet" of "nog te beoordelen" leest. Dat laatste is de plek waar §6.3 nog onvoldoende scherp is en waar de kalibratie dus het meest oplevert.

### 7.4 Wat ik aan Chris voorleg

**Al besloten, alleen uit te voeren — geen nieuw normbesluit:**
- de tekstvervangingen §6.1–§6.4, §6.8 (brengen het record terug naar de ASTRA-norm en repareren aantoonbare defecten);
- het opruimen van de twee dode plekken §6.4;
- de DEF-630-eis dat verplichte reviewuitkomsten een versiegebonden menselijke beoordeling hebben.

**Keuze A — de indicatorpatronen.** Omdraaien naar onbepaaldheidssignalen (§6.1, voorkeur) of de huidige richting behouden en alleen de defecten repareren (alternatief).
*Gevolg A1 (omdraaien):* de reviewer wordt naar de vermoedelijke probleempassages gestuurd; sluit aan bij de ASTRA-FOUT-voorbeelden, die wél patroonvormig zijn. Meer treffers op gewone teksten.
*Gevolg A2 (repareren):* kleinste ingreep, geen nieuw gedrag, maar de signalen blijven naar "hier staat een getal, dus goed" wijzen — de lezing die §2.3 juist wil corrigeren.
*Onderscheidende casussen:* C02 en C10 (krijgen alleen bij A1 een signaal); C03 en C06 (krijgen bij geen van beide een signaal en moeten tóch voldoen).
*Mijn voorkeur:* A1.

**Keuze B — de vaststelpoort, en voor hoeveel regels.** Dit is de enige echte productkeuze.
*B1:* poort alleen voor ESS-04. Snel, maar willekeurig: waarom deze van de dertien?
*B2:* poort voor alle dertien reviewplichtige regels. Consistent en conform DEF-630, maar vaststellen wordt in één keer aanzienlijk zwaarder — dertien oordelen per definitie.
*B3:* poort voor de reviewplichtige regels met `aanbeveling: verplicht` (ESS-04 en ESS-01 zijn dat; ARAI-03 is `optioneel`). Volgt een bestaand recordveld in plaats van een nieuwe lijst, en sluit aan bij hoe ASTRA zelf onderscheidt.
*B4:* geen poort; alleen zichtbaar maken dat ESS-04 open staat, zoals bij ESS-02 is besloten.
*Gevolg voor Chris:* B2 en B3 maken vaststellen trager en betrouwbaarder; B4 laat het huidige gat bestaan maar maakt het zichtbaar — en wijkt af van DEF-630, wat dan een expliciete afwijking moet zijn, geen stilzwijgen.
*Onderscheidende casus:* een definitie met score 0,95, ingevulde context, geldige CON-01/CON-02-beoordeling en een onbeoordeelde ESS-04. Onder B1/B2/B3 blokkeert vaststellen; onder B4 niet.
*Mijn voorkeur:* B3, met de aantekening dat de reikwijdte onder DEF-630 hoort en niet onder dit regeldossier.

**Keuze C — wat "voldoet" betekent bij een ontbrekend gegeven.** Wanneer een criterium afhangt van een niet-aangeleverde bron of peildatum: is dat "voldoet niet" (het staat niet in de tekst) of "nog te beoordelen" (het gegeven kan alsnog komen)? §6.3 kiest nu voor "nog te beoordelen". Dat is een echte keuze; C05 is de onderscheidende casus. *Gevolg:* "voldoet niet" leidt sneller tot herschrijven van een definitie die misschien prima is; "nog te beoordelen" houdt vaker een punt open en blokkeert onder keuze B vaker de vaststelling.

---

## 8. Bewijsgrenzen en wat ik nog nodig heb

**Geverifieerd:** alle 33 bestanden van `werkboom-4cdb8ea43`, alle 36 kopieën in `feitenbasis/`, alle 3 bestanden van `nalevering-4cdb8ea43` zijn aanwezig, leesbaar en hashgelijk aan hun manifest. Zie `cowork-toegang-v1.md` en `cowork-toegang-v1-aanvulling-v1.md`.

**Correctie op mijn eigen toegangsrapport:** ik meldde `src/services/import_service.py` als ontbrekend. `nalevering-leeswijzer-v1.md` stelt terecht dat die manifestregel `available=false` draagt en dat de werkelijke service `definition_import_service.py` heet. Mijn melding was onjuist; de aanvulling corrigeert hem.

**Niet leesbaar, met gevolg voor een concrete claim:**

| Ontbrekend bestand | Welke claim het raakt | Prioriteit |
|---|---|---|
| `src/validation/additional_patterns.py` | **Alle signaalclaims in §5.2 en bijlage A.** `get_additional_patterns("ESS-04")` kan extra patronen toevoegen die ik niet ken | **1 — hoogste** |
| `src/services/validation/evaluators/registry.py` | of ESS-04 werkelijk naar `judgment_review` wordt gerouteerd (ik leid dat af uit het record en het contract, niet uit het register) | 2 |
| `src/services/validation/types_internal.py` | de velden van `EvaluationContext` (`cleaned_text`, `metadata`) waarop mijn replica steunt | 3 |
| `src/services/policies/approval_gate_policy.py` | de werkelijke `hard_min_score`, `soft_min_score` en `allow_hard_override` in §5.7 | 4 |
| `src/services/validation/violation_builder.py` (`category_for_rule`) | de categorie waaronder ESS-04 in de UI landt (historisch "juridisch") | 5 |
| `src/services/validation/readiness.py` | het `validation_readiness`-gedrag bij een incomplete regelset | 6 |
| `tests/unit/validation/test_rule_runtime_matrix.py` | of de telling van dertien reviewplichtige regels werkelijk wordt bewaakt | 7 |
| enige test op ESS-04 in de actuele commit | de snapshot bevat geen tests; `werkboom/` had er één (`test_v2_golden_ess_more.py`) | 8 |

**Bewijsniveau per claim:** §2 is primaire bronlezing; §4.3 is besluitlezing; §5 is codelezing, met één offline replicaproef (bijlage A) en zonder serviceproef of UI-proef; §6 en §7 zijn voorstellen.

**Wat een replica niet bewijst:** bijlage A is geen import van de echte evaluator (het pakket draait niet, §8). De replica volgt `_signalen` en `evaluate` regel voor regel, maar mist `get_additional_patterns`. De uitkomst "altijd `review_required`" volgt bovendien rechtstreeks uit de gelezen code en heeft de proef niet nodig; wat de proef werkelijk toevoegt zijn de patroondefecten, en die zijn pure regexeigenschappen die van de rest van het pakket niet afhangen.

---

## 9. Dekking van de veertien dossieronderdelen

Eén matrix, geen veertien parallelle verhalen.

| # | Onderdeel | Waar behandeld | Belangrijkste uitkomst |
|---|---|---|---|
| 1 | Doel/betekenis | §2.1, §2.2, §3.4 | Vaststelbaarheid van gevalslidmaatschap; bepaald tegenover onbepaald, niet numeriek |
| 2 | Norm/besluiten | §2.1, §2.3, §4.3 | ASTRA zelf gelezen (oldid 8558); record wijkt af in uitleg, thema en relatie; DEF-624/630/638 gelezen |
| 3 | Toepasselijkheid | §2.4, §2.5 | "Geldig voor: alle"; geen bronuitzondering; twee open beleidsvragen |
| 4 | Context | §3.2, §3.3, §4.2 | Noodzakelijk zodra het criterium ervan afhangt; geen universele metadata-eis; geen conflict met CON-01 |
| 5 | Definitiebronnen | §3.2, §4.2, §6.2 | Noodzakelijk zodra de kern een drempel noemt; CON-02 blijft eigenaar van het brongezag |
| 6 | Ontologie/relaties | §3.2, §4.1 | Ondersteunend voor meetobject en populatie; ESS-03 is de enige ASTRA-relatie |
| 7 | Aanvullingen | §3.2 | Volledige veldrolmatrix; toelichting mag meetcontext dragen, repareert nooit de kern |
| 8 | Appgedrag | §5 (alle subs) | Altijd `review_required`; geen stille pass; geen opslag; geen poort; geen zichtbare reden |
| 9 | Skills/prompts | §5.9, §6.2, §6.8 | G-instructie vraagt actief om getallen; vervangtekst en drie vindplaatsen benoemd |
| 10 | Status/score/poorten | §5.3, §5.7, §6.7 | `excluded_from_score` werkt; de vaststelpoort ziet de reviewplicht niet — DEF-630 onuitgevoerd |
| 11 | Proeven | Bijlage A, §5.2 | 14 gevallen, offline, synthetisch, 3 afwijkingen — alle drie patroondefecten |
| 12 | Samenhang | §4.1, §4.2, §6.5 | ESS-03 (bron), ARAI-03 (overlap), ESS-05 (verwarring), CON-01/02 (eigenaarschap); geen buurregelbesluiten |
| 13 | Verbeteringen/review | §6, §7.3 | Concrete vervangteksten; tweebeoordelaarsproef alleen als kalibratie, niet als poort |
| 14 | Acceptatie/overdracht | §7.1, §7.4, §8, §10 | Acceptatiegevallen met G/T/H-verwachting; drie keuzes; bewijsgrenzen; volgende actie |

---

## 10. Opgeleverde bestanden en volgende actie

| Bestand | Inhoud |
|---|---|
| `cowork-toegang-v1.md` | toegangsverantwoording en hashes (bevat de import-melding die hieronder wordt gecorrigeerd) |
| `cowork-toegang-v1-aanvulling-v1.md` | correctie op de importmelding; hashes van de nalevering |
| `cowork-onderzoek-v1.md` | dit document |
| `cowork-bewijs-v1/gevallen-v1.json` | het casusregister met vooraf vastgelegde verwachtingen |
| `cowork-bewijs-v1/proef-ess04-v1.py` | het uitgevoerde proefscript |
| `cowork-bewijs-v1/uitkomsten-v1.json` | de proefuitkomsten |

**Volgende actie:** deze v1 is volledig en opgeslagen. Ik ben gereed om het volledige Codex-onderzoek en zijn claimrelevante bijlagen te ontvangen en per punt te reviewen (claim/versie → oordeel → bron of tegenbewijs → gevolg/correctie), en daarna de Codex-review op dit stuk zichtbaar te verwerken.

**Gericht verzoek, in volgorde van belang:** `src/validation/additional_patterns.py`, `src/services/validation/evaluators/registry.py`, `src/services/validation/types_internal.py` en `src/services/policies/approval_gate_policy.py` uit dezelfde bevroren commit — de eerste raakt rechtstreeks de hardheid van §5.2.

**Nog niet gezamenlijk afgerond:** beide reviews, beide verwerkingen en de synthesecontrole ontbreken.

---

## Bijlage A — Casusregister en proefuitkomsten

**Opzet.** Offline, synthetisch, geen productiegegevens, geen modelcall, verse opslag.
Regelrecord `src/toetsregels/regels/ESS-04.json` uit commit `4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb`, sha256 `78537a76b454e1c652a1601b1804abdf3b28092f88547de3fea9c410d91a389c`.
Uitvoercommando: `python3 proef-ess04-v1.py` (Python 3.10.12), exitstatus 0. Uitgevoerd 2026-09-18T14:47:42.

**Aard van het bewijs: replica, geen import.** De meegeleverde snapshot draait niet (ontbrekende modules, §8).
`proef-ess04-v1.py` volgt `JudgmentReviewEvaluator._signalen` en `evaluate` regel voor regel, met dezelfde `re.IGNORECASE`-compilatie
en dezelfde `search()`-semantiek, **zonder** `get_additional_patterns('ESS-04')` omdat `validation/additional_patterns.py` niet leesbaar is.
De patroonuitkomsten zijn daarmee een ondergrens: er kunnen extra signalen bestaan, er kunnen er niet minder zijn.

**Verwachtingen zijn vóór uitvoering vastgelegd** in `gevallen-v1.json` en zijn niet achteraf bijgesteld.
De zeven historische labels uit `ESS-04-bewijs-v1/gevallen.json` zijn behouden en aan stabiele ID's gekoppeld (C01–C07); C08–C14 zijn nieuw.

### A.1 Uitkomsten

| ID | Historisch label | Invoer | Status | Signaal verwacht | Signaal werkelijk | Getroffen patroon | Verwachting uit |
|---|---|---|---|---|---|---|---|
| ESS04-C01 | good_fragment | …binnen 3 dagen nadat het verzoek is ingediend… | review_required | ja | ja | `\bbinnen\s+\d+\s+dagen?\b` | ja |
| ESS04-C02 | bad_fragment | …zo snel mogelijk na ontvangst… | review_required | nee | nee | — | ja |
| ESS04-C03 | non_numeric | Veelhoek waarvan alle zijden even lang zijn. | review_required | nee | nee | — | ja |
| ESS04-C04 | unfounded_number | Belangrijke aanvraag die binnen 3 dagen relevant wordt. | review_required | ja | ja | `\bbinnen\s+\d+\s+dagen?\b` | ja |
| ESS04-C05 | ambiguous_measure | Object dat minimaal 80% voldoet. | review_required | ja | nee | — | **NEE** |
| ESS04-C06 | observable | Document waarop de afzender een handtekening heeft geplaatst. | review_required | nee | nee | — | ja |
| ESS04-C07 | empty | (leeg) | review_required | nee | nee | — | ja |
| ESS04-C08 | — | Regeling die tenminste 80% van de gevallen dekt. | review_required | ja | nee | — | **NEE** |
| ESS04-C09 | — | Besluit dat de gronden van de afwijzing bevat. | review_required | ja | ja | `\bbevat\b` | ja |
| ESS04-C10 | — | Melding die zo snel mogelijk wordt gedaan en het dossiernummer bevat. | review_required | ja | ja | `\bbevat\b` | ja |
| ESS04-C11 | — | Verzoek dat uiterlijk na 1 week is afgehandeld. | review_required | ja | nee | — | **NEE** |
| ESS04-C12 | — | Beslissing die binnen drie dagen wordt genomen. | review_required | nee | nee | — | ja |
| ESS04-C13 | — | Aanvraag die binnen 3 werkdagen na ontvangst wordt behandeld. | review_required | nee | nee | — | ja |
| ESS04-C14 | — | Kandidaat die minimaal 80%voldoet. | review_required | ja | ja | `\bminimaal\s+\d+%\b` | ja |

**Alle veertien gevallen: `review_required`.** Geen enkel pad naar pass of fail — bevestigt DEF-624 op deze route.
**Afwijkingen van de vooraf vastgelegde verwachting: 3** (C05, C08, C11).

### A.2 Wat de drie afwijkingen aantonen

Alle drie zijn afwijkingen in dezelfde richting: een patroon dat het record kennelijk bedoelde, vuurt niet.

- **C05 en C08** — de percentagepatronen eindigen op `\b` direct na `%`. Een woordgrens vereist aan één zijde een woordteken; na `%` volgt in normale tekst een spatie of een punt, dus geen grens. Controlegeval **C14** (`80%voldoet`, woordteken direct na `%`) vuurt wél en bewijst dat dit de oorzaak is. Dit treft alle vier de patronen `\btenminste\s+\d+%\b`, `\bminimaal\s+\d+%\b`, `\bmaximaal\s+\d+%\b` en `\b\d+\s+%\b`. C08 is letterlijk ASTRA's eigen GOED-voorbeeld 'tenminste 80% van de …'.
- **C11** — `\buiterlijk\s+na\s+\d+\s+(dagen?|weken?)\b`: `weken?` staat voor 'weke' plus een optionele 'n' en dekt 'week' dus niet. Opnieuw ASTRA's eigen GOED-voorbeeld 'uiterlijk na 1 week'. Dezelfde constructie in `\bbinnen\s+\d+\s+dagen?\b` mist 'binnen 1 dag' (los geverifieerd, niet als casus opgenomen).

### A.3 Wat de proef bevestigde

- **C09 en C10** — `\bbevat\b` vuurt op gewone definitiezinnen. C10 ("Melding die **zo snel mogelijk** wordt gedaan en het dossiernummer **bevat**") bevat een ASTRA-FOUT-formulering en krijgt niettemin een positief 'toetsbaarheidssignaal'. Dit is de trefwoord-pass in zijn zuiverste vorm en het sterkste argument om `bevat`/`omvat` te laten vervallen (§6.1).
- **C03, C06, C12, C13** — vier teksten die volgens de voorgestelde norm voldoen, krijgen géén enkel signaal. Kwalitatieve criteria (C03, C06), een termijn in letters (C12) en een explicietere werkdagtermijn (C13) zijn voor de huidige patronen onzichtbaar. Afwezigheid van een signaal zegt hier dus niets, wat precies de reden is dat de regel reviewplichtig moet blijven.
- **C02** — het ASTRA-FOUT-fragment krijgt terecht geen signaal, maar krijgt daarmee ook geen enkele aanwijzing dat hier iets mis is. Onder het voorgestelde omgekeerde patroonontwerp (§6.1, keuze A1) zou dit wél een signaal krijgen; dat is het verschil dat keuze A beslist.
- **C07** (lege tekst) — `review_required` met dezelfde kale toetsvraag als een volle definitie. Formeel juist, voor de gebruiker misleidend (§6.4).

### A.4 Reden die de gebruiker krijgt

Bij alle veertien gevallen identiek, want `judgment_review.evaluate` geeft voor ESS-04 de kale toetsvraag door:

> "Bevat de definitie elementen waarmee je objectief kunt vaststellen of iets wel of niet onder het begrip valt?"

Geen passage, geen aanwijzing, geen onderscheid tussen een lege en een volle definitie. ESS-01 en ESS-02 krijgen in dezelfde commit wél een reden met geciteerde passages (§5.2, §5.5).

### A.5 Wat deze proef niet bewijst

Geen echte generatiekwaliteit (geen modelcall, geen vastgelegde model-/promptversie, geen steekproef). Geen routegedrag door de volledige app (geen serviceproef, geen UI-proef, geen opslag- of vaststelproef). Geen juridische praktijkvaliditeit: de veertien teksten zijn synthetisch en onafhankelijk van expertgold. De uitspraken over opslag, weergave en vaststelling in §5.5–§5.8 steunen uitsluitend op codelezing.

---

## Bijlage B — Inhoudshashes voor overdrachtszekerheid

SHA-256 van de bijlagen bij deze v1. De hash van `cowork-onderzoek-v1.md` zelf wordt bij de overdracht apart gemeld (een bestand kan zijn eigen hash niet dragen).

| Bestand | SHA-256 |
|---|---|
| `cowork-bewijs-v1/gevallen-v1.json` | `782a950c9b4878472f21776ccedd5b10453e63e3c7664fffe85c03ee4ac2fb61` |
| `cowork-bewijs-v1/proef-ess04-v1.py` | `466346240ef2a1e5186ff1b286ed6b6e1c48fd849037b25286921d27ae02dabd` |
| `cowork-bewijs-v1/uitkomsten-v1.json` | `a2412cb0e2bd282e0f0c6b5ded6157a45fb8deed9df87e454280e169b2ff80da` |
| `cowork-toegang-v1.md` | `32219d913a48203528134eee58e73fcfd62a3e742860dbb0a1073730a0747a74` |
| `cowork-toegang-v1-aanvulling-v1.md` | `c6cb0c4ffbea113cc6a99e6e35ecf43f01aa0eafa0b3ab5c2cf0c228cafdfb2e` |

Bronbinding: regelrecord `ESS-04.json` sha256 `78537a76b454e1c652a1601b1804abdf3b28092f88547de3fea9c410d91a389c`, commit `4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb`; nalevering uit dezelfde commit, manifest `nalevering-manifest-v1.json`; ASTRA-pagina Toetsbaarheid zoals aangeboden met permanente link `oldid=8558`, laatst bewerkt 11 februari 2025 09:46.
