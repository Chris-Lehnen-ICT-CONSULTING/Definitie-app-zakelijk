# DEF-766 / ESS-03 — wijzigingsvoorstel voor de vijf skillpassages (alleen inspectie, niets gewijzigd)

18 september 2026 · uitvoerder Claude Code CLI. Bron van de teksten: `tekstvoorstellen-v3.md` §5 en `gezamenlijke-besluitnotitie-v2.md` §1 (onderzoeksmap ESS-03-verdieping/onderzoek-20260918). Dit plan is een concrete diff-beschrijving voor de coördinator; er is geen skillbestand gewijzigd, geen geïnstalleerde kopie overschreven en de andere checkout is niet aangeraakt.

## 0. Vastgestelde drift tussen beheerde bron en geïnstalleerde kopieën (blokkerend voor "veilige distributie")

Gemeten met `cmp`/`diff` op 18 september 2026:

| Skill | `~/Projecten/_claude-global-setup/skills/…` (beheerde bron, branch `feature/ALG-449-informatieopslag-werkplan`, laatste skillcommit `e87c9ee`) | `~/.agents/skills/…` = `~/.claude/skills/…` (geïnstalleerd, byte-gelijk aan elkaar) |
|---|---|---|
| definitie-toetsregels `SKILL.md`, `reference.md` | Versie 0.2 (ALG-329); **geen** CON-01 (DEF-744), CON-02 (DEF-743), ESS-01 (DEF-746) of ESS-02 (DEF-754) tekst; map `references/` ontbreekt | Versie 0.5 (DEF-754) mét `references/{con02-bronbasis,ess01-functiegrens,ess02-betekenisniveau}.md` en de zin "Productbesluit 15 september 2026 (DEF-743/DEF-624): voorlopig geen totaalcijfer …" |
| definitie-nederlandse-definities `SKILL.md`, `reference.md` | Ouder (geen ESS-01/ESS-02-blokken) | Versie 0.4 (DEF-754) met ESS-01- en ESS-02-blokken vóór "## Referenties" (regels 49-57) |
| definitie-ufo-ontologie `SKILL.md`, `reference.md` | Verschilt | Verschilt (niet regel-voor-regel geanalyseerd; ESS-03-passages hieronder zijn op de geïnstalleerde kopie gebaseerd) |
| definitie-ontologisch-modelleren | **Gelijk** | **Gelijk** |
| definitie-voorbeelden-generatie | **Gelijk** | **Gelijk** |

Gevolg: de "beheerde bron" is voor drie van de vijf skills **achter** op wat werkelijk geïnstalleerd is. De DEF-743/744/746/754-skillwijzigingen zijn kennelijk rechtstreeks in `~/.agents/skills` en `~/.claude/skills` gezet en nooit teruggesynchroniseerd naar `_claude-global-setup`. Een ESS-03-diff op de beheerde bron zonder eerst die achterstand in te halen zou bij distributie de DEF-743/744/746/754-teksten **overschrijven**. De coördinator moet dus eerst besluiten: (a) geïnstalleerde kopieën als feitelijke basis terugsynchroniseren naar `_claude-global-setup` (aparte ALG-taak, niet in scope), en pas daarna (b) de ESS-03-diff hieronder toepassen. Onderstaande vindplaatsen verwijzen daarom naar de **geïnstalleerde** kopie (`~/.agents/skills`), zoals ook tekstvoorstellen-v3 §5 doet; de regelnummers voor de beheerde bron staan erbij waar ze afwijken.

## 1. `definitie-toetsregels/reference.md` — ESS-03-tabelrij + nieuwe paragraaf

**Vindplaats geïnstalleerd:** regel 46 (ESS-tabel). **Beheerde bron:** regel 41.

Huidige rij (beide):

```
| ESS-03 | Instanties onderscheidbaar | **hoog** | Noem criteria voor unieke identificatie van instanties (zoals serienummer, kenteken, ID) |
```

Vervang door (exact uit tekstvoorstellen-v3 §5, met voetnootverwijzing ⁵ in de stijl van de bestaande ³/⁴):

```
| ESS-03 | Instanties uniek onderscheidbaar (telbaarheid) ⁵ | **hoog** ⁵ | Maak bij een telbare lezing duidelijk wat één, dezelfde en een andere instantie is; gebruik alleen onderbouwde relevante grenzen of conventies. Geen nummerplicht, woordbewijs of automatische semantische goedkeuring. |
```

Voeg na de bestaande voetnoten ³/⁴ (geïnstalleerd: na regel 52) toe:

```
⁵ Regelnaam en instructie volgens het ESS-03-voorstel (DEF-766); prioriteit hoog stuurt de aandacht en is geen zelfstandig nieuw blokkeerbesluit. ESS-03 levert geen cijfer en geen 0/1: de mens beoordeelt binnen de bestaande expertbeoordeling (voldoet / voldoet niet / niet van toepassing / nog te beoordelen); een naam, nummer, code of het woord 'uniek' geeft geen automatische pass of fail. Zie § ESS-03 — eenheid en identiteit.
```

Voeg **direct na de ESS-tabel en haar voetnoten, vóór "### INT — Integriteit"** een paragraaf toe:

```
### ESS-03 — eenheid en identiteit

> Dit voorstel geldt pas na het ESS-03-besluit; de geldende CON-01/02- en ESS-01/02-afspraken blijven behouden.

**Norm (gezamenlijke besluitnotitie v2 §1):**

Bij een begrip waarvoor afzonderlijke instanties in de bedoelde betekenis relevant zijn, maakt de definitie onafhankelijke materiedeskundigen een eenduidige telling mogelijk bij dezelfde betekenis, relevante informatie en context. De kern maakt voldoende duidelijk wat als één instantie geldt en waardoor instanties van elkaar worden onderscheiden. Een passend bovenbegrip en begripsbepalende kenmerken kunnen daarvoor volstaan; een administratieve identifier is niet verplicht.

Vraag alleen aanvullende grenzen, tijd-, scope- of continuïteitsvoorwaarden wanneer het onderscheid daarvan afhangt. Een naam, nummer of het woord 'uniek' bewijst op zichzelf geen identiteit. Een code kan ondersteunen als haar referentsoort, populatie en relevante toekennings-/geldigheidsvoorwaarden zijn onderbouwd.

Een niet-telbare stof- of verschijnsellezing hoeft niet in kunstmatige porties of registraties te worden veranderd. Een uitdrukkelijk gekozen afgebakende hoeveelheid of gebeurtenis kan wel telbaar zijn. Verschillende tellingen kunnen wijzen op een gebrekkige afbakening, maar ook op verschillende betekenissen of contexten; onderzoek die oorzaak vóór een negatief oordeel.

**Bron en uitwerking gescheiden.** De huidige ASTRA-regel (https://www.astraonline.nl/index.php/Instanties_uniek_onderscheidbaar) onderbouwt het interbeoordelaarsdoel, de niet-telbare uitzondering, de mogelijke betekenisdivergentie en de contextrelatie. ASTRA noemt zand/cocaïne en regen/onweer/recidive als voorbeelden bij de uitzondering; dit is geen vrijstelling voor alle hoeveelheden, processen, abstracta of een UFO-stereotype. De proportionaliteit, concrete bewijsvoorwaarden en continuïteitsuitwerking hierboven zijn een lokaal operationaliseringsvoorstel, geen letterlijke ASTRA-transcriptie.

**Genereren (G):** zie de app-instructie in de ESS-03-regelkaart (`src/services/prompts/modules/json_based_rules_module.py`, sleutel `ESS-03`): bepaal uit de bedoelde betekenis wat als één instantie geldt; maak een noodzakelijke eenheidsgrens duidelijk met bovenbegrip en kenmerken; identifier alleen met onderbouwde referentsoort, scope en geldigheid; verzin geen nummer, bron of telconventie; maak een stof niet stil tot monster; vraag bij een onbesliste grens om gerichte verduidelijking.

**Toetsen (T):**

Beoordeel de ongewijzigde definitiekern bij de vastgelegde term, bedoelde betekenis, context en kandidaatversie. Stel eerst vast welke eenheid bedoeld is en of afzonderlijke instanties relevant zijn. Onderzoek vervolgens wat één, dezelfde en een andere instantie onderscheidt. Een passend bovenbegrip kan een herkenbare natuurlijke grens al dragen. Controleer alleen aanvullende scope, tijd, bron of geheel/deelconventie die het oordeel werkelijk bepaalt. Beoordeel bij codes wat zij identificeren en binnen welke populatie en geldigheid; aanwezigheid van een naam, nummer of woord bewijst niets. Geef een gemotiveerd inhoudelijk oordeel alleen na beoordeling van de relevante grond. Houd ontbrekend bewijs, onbesliste toepasselijkheid, niet-toepasselijkheid en technische fouten afzonderlijk herkenbaar. Verander de invoer niet. Een automatisch signaal, gekozen categorie, record-ID of algemene vaststelling is geen inhoudelijke ESS-03-goedkeuring.

**Terugkoppeling en herstel (H):**

Stel vóór een herstelvoorstel vast of de oorzaak een inhoudelijke generatieovertreding, tegenstrijdige instructie, invoer-/transportverlies, foutieve evaluatoruitkomst, ontbrekend bewijs, technische fout of schadelijke nabewerking is. Gebruik daarvoor waar relevant de ruwe, geëxtraheerde, opgeschoonde, getoetste en opgeslagen tekst met hun invoer-/bronversies. Alleen een negatieve toetsuitkomst bewijst de oorzaak niet. Uitsluitend toetsen laat de oorspronkelijke tekst intact. Maak op gebruikersverzoek een afzonderlijke kandidaat en verschil, uitsluitend met beschikbare betekenisgrond. Verzin geen identiteit, naamruimte, bron, datum of menselijk oordeel. Stop bij ontbrekende grond, bronconflict, herhaalde fout of betekenisverlies. Toekomstig automatisch herstel blijft begrensd tot het afzonderlijk goedgekeurde DEF-638-beleid: maximaal één poging per generatie; dit advies activeert die mogelijkheid niet. Hertoets de veranderde kandidaat en geraakte regels; bewaar eerdere teksten en oordelen als historie.
```

Bij daadwerkelijke goedkeuring de kopregel "Dit voorstel geldt pas na het ESS-03-besluit …" vervangen door concrete besluitdatum en versie — nooit vooraf invullen.

## 2. `definitie-toetsregels/SKILL.md` — sectie Scoring & Weging

**Vindplaats geïnstalleerd:** regel 74-75 (blockquote "> **Geen cijfer voor ESS-01, ESS-02 of CON-02; voorlopig geen totaalcijfer.** …"). **Beheerde bron:** de zin bestaat daar **niet** (v0.2); daar is niets te corrigeren totdat de drift uit §0 is ingehaald.

Vervang in de geïnstalleerde tekst uitsluitend het fragment

```
Productbesluit 15 september 2026 (DEF-743/DEF-624): voorlopig geen totaalcijfer en geen vervangende deelscore over alleen cijfergevende regels — toon per regel het oordeel (voldoet / voldoet niet / nog te beoordelen) en welke controles daadwerkelijk zijn uitgevoerd.
```

door

```
Het definitieve appbrede besluit van 15 september 2026 schaft de totaalscore af als kwaliteitscijfer, acceptatiegrond en hersteldriver. Toon per regel het gemotiveerde oordeel, de uitvoeringsdekking, open acties en actuele expertbeoordeling. Een telling is geen kwaliteitspercentage; dit besluit wijzigt individuele regelpolicies niet automatisch.
```

en voeg ESS-03 toe aan de kopzin: "**Geen cijfer voor ESS-01, ESS-02, ESS-03 of CON-02; …**" plus één zin: "ESS-03 krijgt evenmin een cijfer of 0/1: het menselijke oordeel is voldoet / voldoet niet / niet van toepassing / nog te beoordelen; een naam, nummer of het woord 'uniek' geeft geen automatische pass of fail, en een negatief of open oordeel vormt geen zelfstandige vaststelblokkade."

Let op (tekstvoorstellen-v3 §5): de overige tijdelijke-scorezinnen ("Zolang DEF-624 open is, is de appbrede totaalscore tijdelijk niet beschikbaar", regel 93) en de legacy gewichten/drempels (regels 62-72) moeten bij die afzonderlijke gedeelde uitvoering coherent worden gemaakt — eigenaar DEF-624. Niet alleen één zin wijzigen en de rest als actueel normadvies laten staan.

Versieregel (regel 109) bij uitvoering: "0.6 — DEF-766 (ESS-03 eenheid en identiteit; menselijke beoordeling zonder cijfer)".

## 3. `definitie-nederlandse-definities/SKILL.md` — nieuw ESS-03-blok

**Vindplaats geïnstalleerd:** tussen regel 55 (ESS-02-blok) en regel 57 ("## Referenties"). **Beheerde bron:** heeft geen ESS-01/ESS-02-blok; invoegen vóór "## Referenties" (regel 40) pas na inhalen van de drift.

Voeg toe:

```
## ESS-03 — één instantie onderscheiden

**ESS-03 — één instantie onderscheiden.** Maak bij een telbare lezing een noodzakelijke eenheidsgrens duidelijk met een passend bovenbegrip en kenmerken; een code is niet verplicht. Gebruik alleen onderbouwde scope- en continuïteitsvoorwaarden. Een noodzakelijke naam blijft behouden volgens CON-01. Verander een stof, kwaliteit, type, rol, proces of uitkomst niet om een nummer te kunnen toevoegen. Meld ontbrekende noodzakelijke betekenisgrond afzonderlijk. Voor de gemeenschappelijke beoordeling en herstelgrenzen gelden de ESS-03-instructies van toetsregels; de inhoudelijke beoordeling is menselijk en is geen opgeslagen review door deze skill.
```

Casekoppeling H-mass_noun, N05, N12, N16, N20, N23. Dit blok vervangt geen bestaande ESS-02-generatievoorbeelden. Versieregel (regel 79): "0.5 — DEF-766 (ESS-03 één instantie onderscheiden)".

## 4. `definitie-ufo-ontologie/reference.md` — ESS-03-toepassing + Collective-cel

**Vindplaats geïnstalleerd:** na de tabel "Substantiële Endurants" (regels 15-25) en de tabel "Moment-endurants" (regels 29-33), d.w.z. na het blok "Belangrijk onderscheid Mode vs Quality" (regel 38) en vóór "### UFO-B — Perdurants" (regel 40).

Voeg toe:

```
**ESS-03-toepassing.** Scheid de identiteit van een begrip, een domeininstantie en haar registratierecord. Een geërfd identiteitscriterium kan volstaan; ieder subtype hoeft geen eigen nummer te introduceren. Een categorielabel bepaalt niet hoe instanties worden geteld. Leg bij relevante levensloopvragen vast welke verandering het object behoudt of beëindigt, met bron of expliciete domeinconventie. Bij een geheel is lidmaatschapswijziging niet zonder meer identiteitsverlies; bij een stof moet een gekozen hoeveelheid of monster onderscheiden blijven van de stoflezing. Onbekende conventies blijven open.
```

Vervang in regel 24 uitsluitend de cel "Eigen identiteit via lidmaatschap" door:

```
Eigen identiteitsprincipe; lidmaatschap en continuïteit volgens de bedoelde geheelsoort en onderbouwde conventie
```

Cases N10-16. Geen algemene herclassificatie van commissie/raad/gezin.

## 5. `definitie-ontologisch-modelleren/reference.md` — na Stap 3 (bron en geïnstalleerd gelijk)

**Vindplaats:** na de tabel "Verfijning met UFO-stereotypen" (eindigt regel 77, rij `«collective»`), vóór de volgende stap.

Voeg toe:

```
**ESS-03 — wat wordt geteld.** Leg bij een voor ESS-03 relevante eenheidsvraag vast wat wordt geteld: object, roluitoefening, gebeurtenis, hoeveelheid, abstracte entiteit of registratie. Modelleer een identifier met zijn referentsoort en noodzakelijke namespace-/geldigheidsgrond; een technische sleutel vervangt geen domeinidentiteit. Bij deel/geheel, splitsing, samenvoeging of hervatting onderscheid je identiteit van opvolging en samenstelling. Verander een brongebonden conventie niet om een registratie makkelijker uniek te maken. Een modelrelatie ondersteunt de definitie, maar is geen zelfstandig positief regeloordeel.
```

Cases N07-14, N17. Overige modelleerkeuzes en exclusieve categorieclaims vallen onder ESS-02/DEF-37, niet stil wijzigen.

## 6. `definitie-voorbeelden-generatie/reference.md` — ESS-03-rij + toelichting (bron en geïnstalleerd gelijk)

**Vindplaats:** regel 162, tabel "Relatie met Toetsregels".

Huidige rij:

```
| **ESS-03** (Instanties onderscheidbaar) | Voorbeelden tonen concrete identificatiecriteria |
```

Vervang door:

```
| **ESS-03** (Instanties onderscheidbaar) | Toon onder dezelfde bedoelde lezing één instantie, twee verschillende instanties en waar relevant dezelfde instantie na verandering. Vergelijk codebotsingen, naamruimte, deel/geheel of hervatting alleen wanneer die de telling bepalen; een naam of nummer alleen is geen bewijs. |
```

Voeg direct onder de tabel (na regel 167, vóór "## Intensie-Extensie Toetsprotocol") toe:

```
Leg per ESS-03-geval de telsoort, relevante context, bron/conventie en verwachte telling met reden vooraf vast. Maak een synthetisch voorbeeld herkenbaar als voorstel; claim geen praktijk- of deskundigenbewijs. Neem bij een stoflezing ook het verschil met een expliciet monster of partij mee. Voorbeelden bewijzen niet dat de kern volledig is en mogen een ontbrekend essentieel criterium niet stil repareren. Bij tegengestelde conventies toon je het verschil en vraag je welke geldt.
```

Cases H-mass_noun/N16, N08/N09 en N12/N13. Geen magisch minimumaantal voorbeelden als garantie.

## 7. Uitvoeringsvolgorde voor de coördinator

1. Drift §0 oplossen (terugsync geïnstalleerd → `_claude-global-setup`, of expliciet besluit dat de geïnstalleerde kopie de bron is).
2. Skillwijzigingen 1-6 toepassen op die basis, in een eigen ALG-/DEF-branch; versieregels bijwerken; `references/`-bestanden (toetsregels) niet raken behalve als besloten wordt de ESS-03-norm als apart `references/ess03-eenheid-identiteit.md` te distribueren zoals bij ESS-01/ESS-02 (dan §1-paragraaf daarheen en in reference.md een verwijzing).
3. Distributie naar `~/.agents/skills` en `~/.claude/skills` via het bestaande sync-script, niet handmatig.
4. De skillteksten claimen géén opgeslagen menselijke review en géén implementatiestatus van de app-keten (zie contract-gap-v1.md).
