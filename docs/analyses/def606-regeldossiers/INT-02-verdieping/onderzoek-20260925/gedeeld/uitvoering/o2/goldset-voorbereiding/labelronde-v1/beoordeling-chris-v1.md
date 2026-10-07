# INT-02 O2 — labelvoorstellen ter beoordeling door Chris (v1)

29 september 2026 · **Alleen voorstellen; nog geen geaccepteerde goldset, freeze of modelkwalificatie.**

## Uitkomst van de voorbereiding

Twee verse CLI-sessies hebben onafhankelijk dezelfde 40 synthetische gevallen beoordeeld. Alle 40 hoofdlabels stemmen overeen: 20 `pass`, 10 `fail`, 10 `review_required`. Over geschiktheid verschillen 22 voorstellen. A noemt 32 gevallen bruikbaar en 8 aan te passen; B noemt 13 bruikbaar, 21 aan te passen en 6 uit te sluiten. Beide vinden dezelfde 13 gevallen direct bruikbaar. Deze overeenstemming vervangt jouw inhoudelijke acceptatie niet.

**Open selectiepunten:** B stelt uitsluiting voor van G013, G020, G025, G028, G032 en G040 wegens nabijheid tot bestaande ontwerpgevallen. A vindt G013/G025/G040 eveneens triviale varianten, maar stelt aanpassing voor. A noemt daarnaast G010 een triviale variant. Beide signaleren sterk sturende bronnen en herhaling bij de tien `review_required`-gevallen. Voor een onafhankelijke set van 40 is daarom nog selectie/aanpassing/vervanging nodig; de huidige pool is niet klaar om te bevriezen.

**Familieverschil:** G039 heet bij A `normatief_begrip`, bij B `anders` (beschrijvend procesbegrip). Beiden geven `pass`. Beslis de familie vóór de gestratificeerde 24/16-splitsing; verander geen label om quota te halen.

## Wat Chris nog beoordeelt

1. Lees per geval de kern, bedoeling en synthetische bron, en beoordeel het voorgestelde INT-02-label en de gronden.
2. Beslis afzonderlijk of het geval onafhankelijk en voldoende uitdagend is voor de goldset. Een geldig label maakt een triviale variant niet geschikt als hold-out.
3. Geef correcties of onbesliste gevallen expliciet aan. Alle invulregels hieronder staan bewust open.
4. Alleen na inhoudelijke acceptatie en oplossing van de selectiepunten: 24/16 verdelen, manifest vastleggen en bevriezen. Het bestaande begrensde proefmandaat mag pas daarna worden gebruikt.

Een voorstel `uitsluiten` betekent uitsluiten uit de selectie; er is geen bestand of casus verwijderd. DEF-626 is uitgesteld en de aparte keuze daarover staat open. Actions blijven uit. Deze voorbereiding heeft geen appmodelcalls gedaan en O2 niet geactiveerd.

## Bronnen en controle

[Bronmanifest](/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/manifest.json) · [Normcontract def771-int02/2](/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/normcontract.md) · [Besluiten](/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/besluiten-chris.md) · [Ontwerpregister](/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/ontwerpregister.md)

[Volledige voorstellen A](/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/beoordelaar-a/labelvoorstellen-v1.json) · [Verslag A](/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/beoordelaar-a/verslag-v1.md) · [Volledige voorstellen B](/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/beoordelaar-b/labelvoorstellen-v1.json) · [Verslag B](/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/beoordelaar-b/verslag-v1.md)

A: Claude Code CLI 2.1.283, `claude-opus-5-5`, sessie `e9963285-7fc3-41e6-bb85-6b31f43df4f0`. B: Codex CLI 0.158.0, `gpt-6-astra` / high, sessie `01a0ec8a-8346-77e2-94cf-ce9905085aac`. Beide processen exit 0. Appmodel `claude-opus-5` leverde geen labels. Scheiding is procedureel; technische toegangsisolatie wordt niet geclaimd. De geregistreerde inhoudelijke leesacties bevatten invoer en eigen uitvoer, geen peerlabels/appmodeluitkomsten. B las ook twee procedurele skills.

Coördinatorcontrole: beide bestanden bevatten alle 40 IDs precies eenmaal; alle vier bronhashes komen overeen; alle 87 kerncitaten en 186 grondcitaten staan exact op hun Unicode-tekenposities. Elke RR heeft één vraag; overige gevallen hebben null. Deze documentcontrole bewijst geen modelkwaliteit. De oorspronkelijke versies zijn behouden.

**Contextvraag uit verslag A:** A liet open of een lege `wettelijke_basis` automatisch NE veroorzaakt. De huidige code controleert `not any(invoer.context().values())` in [contract.py](/Users/chrislehnen/Projecten/Definitie-app/src/domain/int02/contract.py:277). Met de gevulde organisatorische en juridische context in alle 40 gevallen is die voorwaarde onwaar. Dit is een gerichte codelezing, geen uitgevoerde appproef.

## Overzicht van alle voorstellen

| ID | Begrip | Label A = B | Geschiktheid A | Geschiktheid B |
| --- | --- | --- | --- | --- |
| G001 | uitzonderingsroute | fail | bruikbaar | aanpassen |
| G002 | overnemende route | pass | bruikbaar | aanpassen |
| G003 | aangewezen referentie | review_required | bruikbaar | aanpassen |
| G004 | opschortingsbeding | pass | bruikbaar | bruikbaar |
| G005 | vrije bufferruimte | pass | bruikbaar | aanpassen |
| G006 | aanvaardbaar arrangement | review_required | bruikbaar | aanpassen |
| G007 | meldingsverbod | pass | bruikbaar | bruikbaar |
| G008 | geblokkeerd transport | fail | bruikbaar | bruikbaar |
| G009 | wederkerige koppeling | pass | bruikbaar | aanpassen |
| G010 | passende inzet | review_required | aanpassen | aanpassen |
| G011 | overdrachtsvenster | pass | bruikbaar | bruikbaar |
| G012 | storingsmelding | fail | bruikbaar | bruikbaar |
| G013 | bewaarplicht | pass | aanpassen | uitsluiten |
| G014 | voldoende herstel | review_required | bruikbaar | aanpassen |
| G015 | ondertekende herstelkopie | pass | bruikbaar | bruikbaar |
| G016 | toelaatbare afwijking | fail | bruikbaar | aanpassen |
| G017 | inzagerecht | pass | bruikbaar | bruikbaar |
| G018 | herroepbare uitzondering | review_required | bruikbaar | aanpassen |
| G019 | gepaarde registratie | pass | bruikbaar | bruikbaar |
| G020 | vrijgave | fail | bruikbaar | uitsluiten |
| G021 | drempelbeslissing | pass | bruikbaar | aanpassen |
| G022 | versnelde behandeling | review_required | aanpassen | aanpassen |
| G023 | getrapt meetinterval | pass | bruikbaar | aanpassen |
| G024 | controlebewijs | fail | bruikbaar | bruikbaar |
| G025 | intrekkingsbesluit | pass | aanpassen | uitsluiten |
| G026 | voorwaardelijke inschaling | review_required | aanpassen | aanpassen |
| G027 | gewogen verblijfsduur | pass | bruikbaar | bruikbaar |
| G028 | reserveringsbevestiging | fail | bruikbaar | uitsluiten |
| G029 | revisiebevoegdheid | pass | bruikbaar | bruikbaar |
| G030 | actieve aanbieding | review_required | bruikbaar | aanpassen |
| G031 | onvolledig raster | pass | bruikbaar | bruikbaar |
| G032 | spoedvak | fail | bruikbaar | uitsluiten |
| G033 | beoordelingsmarge | pass | bruikbaar | aanpassen |
| G034 | toegewezen capaciteit | review_required | aanpassen | aanpassen |
| G035 | herbruikbare capsule | pass | bruikbaar | aanpassen |
| G036 | herstelronde | fail | bruikbaar | aanpassen |
| G037 | leveringsgarantie | pass | bruikbaar | bruikbaar |
| G038 | geautoriseerde publicatie | review_required | aanpassen | aanpassen |
| G039 | adviesprocedure | pass | bruikbaar | aanpassen |
| G040 | escalatiemelding | fail | aanpassen | uitsluiten |

## Beoordeling per geval

De tekst hieronder is overgenomen uit de casuspool en de afzonderlijke voorstellen; het zijn geen nieuwe oordelen van de coördinator. Volledige citaten, offsets en grondverwijzingen staan in de twee JSON-bestanden. Alle bronnen zijn fictief.

### G001 — uitzonderingsroute

**Kern:** Bij overbelasting kiest de planner een alternatieve route als hij de extra reistijd aanvaardbaar acht.

**Bedoeling:** De zin wordt gebruikt als definitie van een routetype; de brontekst regelt een operationele keuze.

**Context:** organisatorische_context: Routeringproef Cipres (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** De planner beslist per overbelasting over omleiding en weegt daarbij de extra reistijd. Dit hoofdstuk bevat de instructies aan de planner.

**A: fail · bruikbaar · zekerheid hoog.** De kern bakent geen routetype af maar geeft de keuze van de planner weer, afhankelijk van diens eigen oordeel of extra reistijd aanvaardbaar is. Die passage functioneert als discretionaire beslisregel voor het handelen; de bron bevestigt een afweging en instructie aan de planner. Er is geen genus en geen afbakenend kenmerk.

Afstand A: zelfstandig; C13, C83, C101. Zelfde familie als C13/C83 (discretie via eigen oordeel), maar actor als zinsonderwerp zonder genus en zonder S1-marker; geen kopie.

Aandachtspunten A: Bron B1 zegt letterlijk dat het hoofdstuk instructies aan de planner bevat: sturend, maar de kern draagt het gebrek zelfstandig. Signaalloos onder de goedgekeurde markerlijst (“aanvaardbaar acht” is geen “redelijk acht”).

**B: fail · aanpassen · zekerheid hoog.** De kern laat de planner bij overbelasting een route kiezen op basis van zijn waardering van reistijd. B1 bevestigt dat dit instructies voor de operationele keuze zijn. Daarmee voert de kern een discretionaire handelingsregel uit in plaats van een routetype met kenmerken af te bakenen.

Afstand B: zelfstandig; C51, C83. C51 betreft weigering met een uitzondering; C83 het opleggen van een maatregel. Hier vormt een storing de aanleiding voor een positieve routekeuze met een afzonderlijke reistijdafweging, zonder hun discretionaire markerformulering.

Aandachtspunten B: Bedoeling noemt de operationele keuze en B1 noemt zichzelf instructies; dat stuurt de functie sterk vooraf. G016 herhaalt een actorbesluit op basis van aanvaardbaarheid van lasten; verschil is de feitelijke keuzeregel tegenover een expliciete beslismogelijkheid.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G002 — overnemende route

**Kern:** Route die dezelfde eindpunten als de hoofdroute verbindt indien de hoofdroute door een storing onbruikbaar is.

**Bedoeling:** Dit is een soort route in een fictief netwerkmodel, niet een instructie om verkeer om te leiden.

**Context:** organisatorische_context: Netwerk Riet (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het routemodel onderscheidt hoofdroutes en routes die bij uitval dezelfde eindpunten kunnen verbinden. Een routekeuzeprocedure is afzonderlijk beschreven.

**A: pass · bruikbaar · zekerheid hoog.** Genus “route” met criterium: dezelfde eindpunten verbinden als de hoofdroute, begrensd tot de situatie waarin die door storing onbruikbaar is. De voorwaardelijke bijzin draagt een lidmaatschapscriterium, geen handeling; bedoeling en bron bevestigen een routetype, met de keuzeprocedure elders. “indien” bewijst geen overtreding.

Afstand A: zelfstandig; C04, C17, C11. Voorwaardelijk criterium zoals C04/C17, maar ander domein en een voorwaarde over de situatie in plaats van over het object zelf.

Aandachtspunten A: Bedoeling zegt expliciet “niet een instructie om verkeer om te leiden”: sturend. Of “verbindt indien” het bronkenmerk “bij uitval kunnen verbinden” precies weergeeft, is ESS-05/INT-01, niet INT-02. Bevat signaalwoord “indien”: vals-alarmgeval.

**B: pass · aanpassen · zekerheid hoog.** Dezelfde eindpunten en onbruikbaarheid van de hoofdroute begrenzen het routetype. De kern draagt niemand op verkeer om te leiden. B1 ondersteunt het onderscheid tussen de route-eigenschap en een afzonderlijke keuzeprocedure; de voorwaardelijke vorm verandert die beschrijvende functie niet.

Afstand B: zelfstandig; C04, C26. C04 koppelt een getal aan deelbaarheid; C26 geeft een terugval tussen identiteitsdocumenten. Hier wordt een alternatief door een relatie tot een ander netwerkobject én diens toestand bepaald; het is geen vervanging van hun termen of drempel.

Aandachtspunten B: De bedoeling sluit expliciet een omleidingsinstructie uit en B1 plaatst de procedure elders; deze dubbele functieduiding maakt het geval erg gestuurd.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G003 — aangewezen referentie

**Kern:** Meetobject dat na aanwijzing door de commissie als referentie wordt gebruikt.

**Bedoeling:** De gebruiker heeft niet bevestigd of aanwijzing het objecttype constitueert of hier een opdracht tot gebruik wordt geformuleerd.

**Context:** organisatorische_context: Referentieproef Abeel (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Versie A noemt aanwijzing een registratie van het type meetobject. Versie B gebruikt dezelfde formulering als opdracht aan het laboratorium om het aangewezen object voortaan te gebruiken. De toepasselijke versie is niet gekozen.

**A: review_required · bruikbaar · zekerheid hoog.** De passieve bijzin kan een constitutief kenmerk of een gebruiksopdracht aan het laboratorium weergeven. De bron geeft beide versies zonder keuze en de bedoeling is onbevestigd. Zonder keuze is de functie niet vast te stellen; er is geen zelfstandig bewezen gebrek.

Vraag A: Is versie A (aanwijzing als registratie van het type meetobject) of versie B (opdracht aan het laboratorium om het aangewezen object te gebruiken) de toepasselijke grond voor deze kern?

Afstand A: zelfstandig; C30, C60, C108. Bronconflict zoals C60/C108, maar over de passagefunctie in plaats van over criteriuminhoud.

Aandachtspunten A: Label volgt vrijwel direct uit de metazin “De toepasselijke versie is niet gekozen”: sturende bron. Zonder de bron zou de passieve kern eerder op pass wijzen.

**B: review_required · aanpassen · zekerheid hoog.** De kern kan het aangewezen meetobject beschrijven, maar dezelfde formulering is volgens B1 ook een opdracht aan het laboratorium. De toepasselijke versie is niet gekozen. Aanwijzing door een commissie bewijst op zichzelf geen verboden beslisregel; zonder bronkeuze is de functie hier niet vast te stellen.

Vraag B: Geldt voor deze definitie versie A, waarin aanwijzing het meetobjecttype vastlegt, of versie B, waarin het laboratorium opdracht krijgt het object te gebruiken?

Afstand B: zelfstandig; C24, C60. C24 laat de functie van toestemming met voorwaarden open; C60 betreft strijdige bronnen bij een inschrijvingscriterium. G003 specificeert een versieconflict tussen typeaanwijzing en toekomstig gebruik van een meetobject.

Aandachtspunten B: B1 geeft beide functies al als analytische samenvatting en meldt expliciet dat geen versie gekozen is; afzonderlijke bronpassages ontbreken. Met G014, G034 en G038 wordt dezelfde onbesliste catalogus-/taaklezing herhaald; aanwijzing vóór gebruik is hier het eigen inhoudelijke accent.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G004 — opschortingsbeding

**Kern:** Onderdeel van een afspraak dat uitvoering van een prestatie onderbreekt zolang de omschreven verstoring voortduurt.

**Bedoeling:** De term benoemt het beding zelf en de werking die het afsprakenmodel eraan toekent.

**Context:** organisatorische_context: Contractproef Els (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Een opschortingsbeding koppelt de onderbreking van uitvoering aan een omschreven verstoring. Dit is een fictief model, geen uitspraak over geldend contractenrecht.

**A: pass · bruikbaar · zekerheid hoog.** De kern beschrijft een beding en de werking die het afsprakenmodel eraan toekent: onderbreking van uitvoering zolang de omschreven verstoring voortduurt. Dat is een gevolg als begripskenmerk, geen opdracht aan een partij. Bedoeling en bron bevestigen de beschrijvende functie.

Afstand A: zelfstandig; C53, C103. Rechtsgevolg beschrijven zoals C53, maar contractbeding als genus en een tijdsgebonden voorwaarde (“zolang”).

**B: pass · bruikbaar · zekerheid hoog.** Het begrip is een onderdeel van een afspraak. De kern beschrijft het daaraan verbonden onderbrekende gevolg en de duur daarvan, zonder een actor te laten besluiten tot opschorting. B1 ondersteunt die koppeling tussen beding en verstoring; een normatieve werking beschrijven is onder B1 van Chris toegestaan.

Afstand B: zelfstandig; C53, C103. C53 betreft verval van rechtsgevolgen en C103 een verandering door een rechtsfeit. Hier staat een afspraakonderdeel centraal met tijdelijke onderbreking zolang een verstoring voortduurt, geen onvoorwaardelijke vernietiging of algemene gevolgdefinitie.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G005 — vrije bufferruimte

**Kern:** Verschil tussen de capaciteit van de ontvangstbuffer en het aantal posities dat op het meetmoment bezet is.

**Bedoeling:** De term benoemt een berekende momentopname, niet een handeling van een beheerder.

**Context:** organisatorische_context: Dataproef Linde (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** De buffer heeft een vaste capaciteit. Vrije ruimte is capaciteit min bezette posities; beide worden in posities uitgedrukt.

**A: pass · bruikbaar · zekerheid hoog.** Deterministische afleiding: verschil tussen capaciteit en bezette posities op het meetmoment. Geen actor, geen handeling. De bron geeft dezelfde bewerking en eenheid; een afleidbaar begrip hoort volgens de norm juist zo gedefinieerd te worden.

Afstand A: zelfstandig; C116, C27. Afgeleide grootheid zoals C116, maar andere bewerking (verschil) en een momentopname.

Aandachtspunten A: Bedoeling “niet een handeling van een beheerder” is licht sturend.

**B: pass · aanpassen · zekerheid hoog.** De kern bepaalt vrije ruimte door capaciteit en bezette posities van elkaar af te trekken. B1 geeft de vaste capaciteit, aftrekking en gelijke eenheden. Er wordt geen beheerhandeling opgedragen en geen keuze gemaakt; de afleiding is juist een toegestane manier om dit begrip te definiëren.

Afstand B: twijfel; C116, C27. Net als C116 is dit een direct berekende grootheid; C27 gebruikt een verschil tussen twee tijdstippen. Capaciteit minus bezetting met een meetmoment is inhoudelijk anders, maar voor INT-02 blijft slechts de eenvoudige rekenkundige afleiding over; beperkte extra uitdaging.

Aandachtspunten B: Bedoeling zegt expliciet dat het geen beheerhandeling is; de formule en grootheid bieden die grond al. Nabij C116/C27; zelfstandige meerwaarde van deze eenvoudige aftrekking nog door Chris te wegen.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G006 — aanvaardbaar arrangement

**Kern:** Arrangement dat de commissie bij een evenwichtige belangenverdeling aanvaardt.

**Bedoeling:** De gebruiker heeft de beoogde referent en functie niet bevestigd.

**Context:** organisatorische_context: Arrangementproef Vijg (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** De ene bron beschrijft een reeds aanvaard arrangement met een constitutief oordeel. De andere bron schrijft de commissie voor arrangementen na een belangenafweging te aanvaarden. Voorrang is onbeslist.

**A: review_required · bruikbaar · zekerheid middel.** De bijzin kan een constitutief aanvaardingsoordeel als kenmerk beschrijven (toegestaan) of de commissie voorschrijven na afweging te aanvaarden (discretionaire beslisregel). De bronnen geven beide lezingen, voorrang is onbeslist en de bedoeling is onbevestigd. Geen zelfstandig bewezen gebrek.

Vraag A: Welke bron heeft voorrang: de beschrijving van een reeds aanvaard arrangement met constitutief oordeel, of het voorschrift aan de commissie om arrangementen na belangenafweging te aanvaarden?

Afstand A: zelfstandig; C107, C12. Menselijk oordeel als kenmerk zoals C107, maar met belangenafweging en een expliciet bronconflict over voorrang.

Aandachtspunten A: Afwegingstaal kan een beoordelaar naar fail trekken; onder de norm beslist de functie, en die is strijdig. Metazin “Voorrang is onbeslist” stuurt het label.

**B: review_required · aanpassen · zekerheid hoog.** De kern laat zowel een arrangement na aanvaarding als een regel voor het aanvaarden na belangenafweging toe. B1 bevestigt juist die strijdige lezingen zonder voorrang. Een evenwichtige belangenverdeling vergt beoordeling, maar dat alleen bewijst niet dat de definitie de beslissing uitvoert.

Vraag B: Beschrijft deze inschrijving een reeds aanvaard arrangement, of moet de commissie met deze zin na belangenafweging over aanvaarding beslissen?

Afstand B: twijfel; C107, C60. C107 heeft al het grensprobleem van een constitutief oordeel bij een categorie; G006 voegt een expliciet tweeledig bronconflict toe zoals C60. De belangenafweging maakt de handelingslezing concreet, maar beide bouwstenen zijn sterk voorgevormd.

Aandachtspunten B: De bron benoemt zelf constitutief oordeel, voorschrift en onbesliste voorrang; het conflicttype wordt vooraf verklaard. G010 en G026 herhalen de tegenstelling tussen een beoordelingsresultaat en een uit te voeren keuze, met andere onderwerpen.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G007 — meldingsverbod

**Kern:** Norm die het bekendmaken van een nog niet vrijgegeven proefresultaat uitsluit.

**Bedoeling:** Het begrip is een type norm binnen een fictief onderzoeksreglement.

**Context:** organisatorische_context: Proefreglement Acacia (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het begrippenmodel onderscheidt verboden, geboden en bevoegdheden. Het meldingsverbod heeft betrekking op bekendmaking vóór vrijgave.

**A: pass · bruikbaar · zekerheid hoog.** De kern definieert een norm naar haar inhoud: bekendmaking vóór vrijgave uitsluiten. Een verbod als begrip beschrijven is geen gedragsopdracht; de kern spreekt geen actor aan. Bedoeling en bron plaatsen het begrip in een normtypologie.

Afstand A: zelfstandig; C112, C59. Normatief begrip zoals C112, maar verbod zonder normadressaat en met andere zinsbouw.

**B: pass · bruikbaar · zekerheid hoog.** De kern beschrijft een norm en haar bereik: bekendmaken vóór vrijgave. Zij formuleert geen zelfstandige opdracht aan een publicerende actor. B1 plaatst het begrip bij de normtypen verboden, geboden en bevoegdheden. De normatieve inhoud is hier het beschreven object.

Afstand B: zelfstandig; C112. C112 beschrijft een positieve prestatieverplichting. G007 beschrijft een verbod, met vrijgave als grens aan het verboden gedrag. Dat andere normtype en de temporele beperking zijn meer dan een vervanging van partij en prestatie.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G008 — geblokkeerd transport

**Kern:** Zet een transport apart, registreer de reden en vraag de ploegchef om verdere aanwijzingen.

**Bedoeling:** Deze tekst staat in een definitieveld voor een transportstatus; zij komt letterlijk uit het fictieve handboek.

**Context:** organisatorische_context: Transporthandboek Palm (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** De geciteerde handboekregel richt zich tot de medewerker die een blokkering constateert. Het handboek is voor deze organisatie vastgesteld.

**A: fail · bruikbaar · zekerheid hoog.** De kern bestaat uit drie gebiedende handelingen voor een medewerker en noemt geen genus of kenmerk van een transportstatus. Zij functioneert als werkinstructie; de bron bevestigt dat de regel zich tot de medewerker richt. Vaststelling van het handboek geeft geen INT-02-vrijstelling.

Afstand A: zelfstandig; C105, C15, C114. Opdracht zonder signaalwoord zoals C105, maar in gebiedende wijs en als meerstappige procedure; brongezag zoals C114.

Aandachtspunten A: Signaalloos. Ook zonder bron evident; weinig onderscheidend vermogen voor moeilijke gevallen.

**B: fail · bruikbaar · zekerheid hoog.** De volledige kern bestaat uit drie opdrachten aan de medewerker. B1 bevestigt de geadresseerde bij een geconstateerde blokkering. Zij beschrijft daarmee hoe te handelen en niet wat de transportstatus is. Dat het handboek in de synthetische organisatie is vastgesteld, geeft geen vrijstelling van de brede norm.

Afstand B: zelfstandig; C114, C15. C114 combineert brongezag met een discretionaire weigering; C15 een betrekkelijke bijzin met behandeling en afwijzing. Hier worden drie rechtstreekse imperatieven overgenomen als statusdefinitie, zonder afwegingsvoorwaarde.

Aandachtspunten B: De vaststelling van het fictieve handboek is uitsluitend betekeniscontext, geen aanwijzing dat de kern voldoet.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G009 — wederkerige koppeling

**Kern:** Koppeling tussen twee objecten die vanaf elk object naar het andere object navigeerbaar is.

**Bedoeling:** De term benoemt een relatie-eigenschap in een objectmodel.

**Context:** organisatorische_context: Objectmodel Vlier (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Wederkerigheid is de aanwezigheid van beide navigatierichtingen; zij schrijft geen onderhoudshandeling voor.

**A: pass · bruikbaar · zekerheid hoog.** Genus “koppeling” met structureel criterium: navigeerbaarheid in beide richtingen. “navigeerbaar” is een eigenschap, geen opdracht. Bron en bedoeling bevestigen een relatie-eigenschap in een objectmodel.

Afstand A: zelfstandig; C113, C05. Eenvoudig lidmaatschapscriterium; geen ontwerpgeval met hetzelfde raam.

Aandachtspunten A: Bronzin “zij schrijft geen onderhoudshandeling voor” is sturend en voor het oordeel niet nodig.

**B: pass · aanpassen · zekerheid hoog.** De kern begrenst koppelingen door navigeerbaarheid van elk object naar het andere. Dit is een eigenschap van de relatie, geen opdracht tot aanleg of onderhoud. B1 bevestigt beide navigatierichtingen als betekenis van wederkerigheid.

Afstand B: zelfstandig; C05, C55. C05 betreft een rekenkundige objecteigenschap en C55 een waarneembaar oppervlak. Een tweezijdige relatie-eigenschap tussen objecten komt daarin niet voor; er is geen gedeelde concrete criteriumstructuur buiten beschrijvende afbakening.

Aandachtspunten B: B1 sluit onderhoud expliciet uit terwijl de kern zelf al duidelijk structureel is. G019 gebruikt eveneens een heen-/terugrelatie; het voegt precies één paar toe, maar de functionele uitdaging overlapt.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G010 — passende inzet

**Kern:** Inzet die volgens het oordeel van de dienstleider aansluit bij de actuele behoefte.

**Bedoeling:** Het dossier laat open of een oordeel de categorie vastlegt of de dienstleider zijn inzetkeuze moet aanpassen.

**Context:** organisatorische_context: Inzetproef Sering (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het registratiemodel noemt het oordeel constitutief. De planningshandleiding gebruikt dezelfde woorden voor een keuze over handelen. Beide zijn als grond toegevoegd.

**A: review_required · aanpassen · zekerheid middel.** Het oordeel van de dienstleider kan een constitutief kwalitatief kenmerk zijn of diens inzetkeuze sturen. De bron voegt beide lezingen toe zonder rangorde en de bedoeling laat de functie open. Een menselijk oordeel is op zichzelf geen beslisregel; zonder keuze resteert beslissende onzekerheid.

Vraag A: Is het registratiemodel (oordeel van de dienstleider als constitutief kenmerk) of de planningshandleiding (keuze over het eigen inzethandelen) de leidende grond voor deze kern?

Afstand A: triviale_variant; C107. Zelfde zinsraam als C107 (genus + “naar/volgens het oordeel van <actor>” + kwalitatief criterium) en hetzelfde verwachte label; alleen het bronconflict is toegevoegd.

Aandachtspunten A: Weinig onafhankelijk van C107; hooguit ontwikkelgeval, zwak als hold-out.

**B: review_required · aanpassen · zekerheid hoog.** Volgens de kern berust passendheid op het oordeel van de dienstleider. B1 geeft dat oordeel echter zowel een constitutieve als een handelingsgerichte functie. Geen van beide gronden is leidend gemaakt. De menselijke beoordeling alleen rechtvaardigt geen afkeur, maar de bronstrijd verhindert een gedragen pass.

Vraag B: Is hier het registratiemodel leidend dat het oordeel tot categoriekenmerk maakt, of de planningshandleiding die ermee een inzetkeuze laat uitvoeren?

Afstand B: twijfel; C107, C60. De kern volgt de structuur van C107: object dat volgens het oordeel van een beoordelaar voldoet. Het bronconflict voegt de C60-grens toe, maar inhoudelijk ligt de combinatie dicht bij die twee ontwerpen.

Aandachtspunten B: B1 noemt de functies constitutief en keuze over handelen expliciet; de bronnen zijn alleen samengevat. De onbesliste oordeelsfunctie herhaalt G006 en G026; aansluiting op actuele behoefte is het eigen criterium.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G011 — overdrachtsvenster

**Kern:** Tijdsinterval dat begint bij ontvangst van het eerste pakket en eindigt bij bevestiging van het laatste pakket.

**Bedoeling:** De term benoemt een afgebakend interval in een waarnemingsmodel.

**Context:** organisatorische_context: Transportproef Wilg (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Ontvangst en bevestiging zijn gelogde gebeurtenissen. Het venster wordt met die twee tijdstippen beschreven.

**A: pass · bruikbaar · zekerheid hoog.** Interval afgebakend door twee gelogde gebeurtenissen: ontvangst van het eerste en bevestiging van het laatste pakket. Deterministisch vast te stellen; “bevestiging” is hier een gebeurtenis, geen opdracht. Bron en bedoeling bevestigen dit.

Afstand A: zelfstandig; C27, C22. Tijdsafbakening zoals C27/C22, maar begrensd door gebeurtenissen in plaats van datums of termijnen.

**B: pass · bruikbaar · zekerheid hoog.** Ontvangst van het eerste en bevestiging van het laatste pakket bepalen begin en einde van het interval. De kern draagt geen ontvangst of bevestiging op. B1 identificeert beide als gelogde gebeurtenissen; het begrip beschrijft dus een waarneembare temporele afbakening.

Afstand B: zelfstandig; C22, C27. C22 classificeert een aangifte met een vaste termijn; C27 berekent volledige levensjaren. G011 definieert het interval zelf tussen twee verschillende grensgebeurtenissen en geeft geen vaste duur of leeftijdsberekening.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G012 — storingsmelding

**Kern:** De meldkamer opent een incidentkaart en belt vervolgens de dienstdoende technicus.

**Bedoeling:** Deze tekst wordt aangeboden als definitie van storingsmelding in een begrippenlijst bij het operationele draaiboek.

**Context:** organisatorische_context: Draaiboek Plataan (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Onder de kop Storingsmelding staan achtereenvolgens de taken openen van een incidentkaart en bellen van de technicus; deze taken gelden bij iedere gemelde storing.

**A: fail · bruikbaar · zekerheid hoog.** De kern beschrijft opeenvolgende taken van de meldkamer (kaart openen, dan technicus bellen) en geen kenmerk van een melding. De bron bevestigt dat deze taken bij iedere storing gelden. Daarmee functioneert de kern als procedure voor een actor.

Afstand A: twijfel; C105, C15. Actor als onderwerp in aantonende wijs zoals C105; nieuw zijn de tweestapsvolgorde en de breuk tussen referent (melding) en inhoud (afhandeling).

Aandachtspunten A: Signaalloos. De referentbreuk is ook ESS-materie; het INT-02-oordeel steunt op de procedurefunctie.

**B: fail · bruikbaar · zekerheid hoog.** De kern laat de meldkamer een kaart openen en vervolgens een technicus bellen. B1 bevestigt dat dit taken zijn die bij iedere storing gelden. De zin voert zo een behandelprocedure uit, hoewel zij geen moet bevat; zij bakent het begrip storingsmelding niet af.

Afstand B: zelfstandig; C105, C15. C105 geeft één ongemarkeerde opdracht; C15 combineert een behandeltermijn en conditionele afwijzing. G012 bevat twee opeenvolgende, onvoorwaardelijke taken in een zelfstandige actorzin. Het temporele verband maakt een meerstapsprocedure zonder normmarker zichtbaar.

Aandachtspunten B: G024 bevat eveneens twee geordende uitvoerderstaken zonder moet; daar zijn ze ingebed in een nominale documentomschrijving. Die verschillende inbedding heeft vergelijkingswaarde.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G013 — bewaarplicht

**Kern:** Plicht van de registratiehouder om bronbestanden gedurende de in de afspraak genoemde bewaartermijn beschikbaar te houden.

**Bedoeling:** De term benoemt de plicht, niet een opdracht in een werkinstructie.

**Context:** organisatorische_context: Archiefproef Taxus (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het fictieve afsprakenmodel bevat een bewaarplicht als relatie tussen houder, bestanden en termijn. De feitelijke uitvoering wordt elders beschreven.

**A: pass · aanpassen · zekerheid hoog.** Definitie van een plicht als normatieve relatie tussen houder, bestanden en termijn. De kern beschrijft de verplichting maar schrijft geen handeling voor. Bedoeling en bron bevestigen dat de uitvoering elders staat.

Afstand A: triviale_variant; C112. Zelfde zinsraam als C112 (“Verplichting/Plicht van <partij> om <handeling>”) en hetzelfde verwachte label; alleen inhoud en termijn verschillen.

Aandachtspunten A: Weinig onafhankelijk van C112; als hold-out nauwelijks informatief.

**B: pass · uitsluiten · zekerheid hoog.** Het gedefinieerde object is de plicht zelf, met registratiehouder, bronbestanden en bewaartermijn als onderdelen. De kern geeft geen zelfstandige werkinstructie voor het bewaren. B1 ondersteunt deze normatieve relatie; het daarin beschreven moeten bewaren is geen INT-02-overtreding.

Afstand B: triviale_variant; C112. C112 beschrijft een verplichting van een partij om een overeengekomen prestatie te verrichten. G013 vervangt partij/prestatie door registratiehouder/beschikbaar houden en specificeert een overeengekomen termijn; dezelfde plicht-om-structuur en functiegrens blijven volledig intact.

Aandachtspunten B: Voorstel tot uitsluiting als onafhankelijk goldsetgeval wegens de nauwe inhoudelijke herhaling van C112; het pass-voorstel blijft staan. Bedoeling sluit een werkinstructie expliciet uit; B1 vermeldt bovendien dat uitvoering elders staat.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G014 — voldoende herstel

**Kern:** Herstel dat de inspecteur na beoordeling als afdoende registreert.

**Bedoeling:** De bedoeling is niet bevestigd; de gebruiker wil geen keuze tussen de twee bronlezingen laten invullen.

**Context:** organisatorische_context: Herstelproef Mirte (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Bron A maakt registratie door de inspecteur constitutief voor de status voldoende herstel. Bron B is een taakinstructie over wanneer de inspecteur herstel moet afmelden. De geldende lezing ontbreekt.

**A: review_required · bruikbaar · zekerheid hoog.** De bijzin kan een constitutieve registratie als kenmerk zijn (bron A) of een taakinstructie (bron B). De geldende lezing ontbreekt en de gebruiker laat de keuze niet invullen. Geen zelfstandig bewezen gebrek; de functie blijft onbeslist.

Vraag A: Geldt bron A (registratie door de inspecteur is constitutief voor de status) of bron B (taakinstructie voor het afmelden van herstel) als grond voor deze kern?

Afstand A: zelfstandig; C107, C30, C60. Oordeel als kenmerk zoals C107, maar met registratiehandeling en een bronconflict over de functie.

Aandachtspunten A: Metazin “De geldende lezing ontbreekt” stuurt het label.

**B: review_required · aanpassen · zekerheid hoog.** Registratie na beoordeling kan de status voldoende herstel constitueren. B1 presenteert daarnaast dezelfde grond als taakinstructie voor het afmelden van herstel. De geldende lezing ontbreekt. De kern alleen beslecht dit functieconflict niet en bevat geen daarvan onafhankelijk bewezen actorvoorschrift.

Vraag B: Geldt registratie hier als constitutief kenmerk van de status voldoende herstel, of als de opdracht aan de inspecteur om herstel af te melden?

Afstand B: twijfel; C107, C60. C107 gaat eveneens over voldoende-zijn volgens een beoordelaar; G014 maakt een registratiehandeling constitutief en voegt expliciete bronstrijd toe. Dat is meer dan alleen een andere term, maar blijft nauw bij C107 plus C60.

Aandachtspunten B: B1 benoemt statusfunctie, taakinstructie en ontbrekende keuze al; de bronduiding stuurt het open oordeel sterk. G003, G034 en G038 herhalen de botsing tussen een geregistreerde/ontstane categorie en een uit te voeren taak.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G015 — ondertekende herstelkopie

**Kern:** Herstelkopie waarvan de inhoud overeenkomt met het origineel en waarvan de controlesom is ondertekend door de archiefdienst.

**Bedoeling:** Het begrip duidt een digitaal object aan; ondertekening en inhoudsgelijkheid zijn eigenschappen in het inventarisregister.

**Context:** organisatorische_context: Atlasarchief (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** In de inventaris wordt een herstelkopie ondertekend genoemd als haar inhoud gelijk is aan het origineel en de archiefdienst haar controlesom heeft ondertekend.

**A: pass · bruikbaar · zekerheid hoog.** Twee cumulatieve criteria: inhoudsgelijkheid met het origineel en een door de archiefdienst ondertekende controlesom. De handeling van de archiefdienst staat als voltooid resultaat en wordt niet voorgeschreven. Bron en bedoeling noemen beide als eigenschappen in het register.

Afstand A: zelfstandig; C19. Waarmerkcriterium zoals C19, maar zonder voorwaardewoord, met genoemde actor en extra inhoudscriterium.

**B: pass · bruikbaar · zekerheid hoog.** De kern vereist zowel overeenkomst met het origineel als een door de archiefdienst ondertekende controlesom. Dit zijn kenmerken van de herstelkopie; niemand krijgt opdracht die controles uit te voeren. B1 bevestigt dezelfde tweeledige afbakening in de inventaris.

Afstand B: zelfstandig; C19. C19 classificeert een gewaarmerkt document met handtekening en datum. G015 combineert inhoudsgelijkheid met ondertekening van een afgeleid object, de controlesom, in plaats van het document zelf. Die relaties gaan verder dan een andere documentnaam.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G016 — toelaatbare afwijking

**Kern:** De projectleider kan besluiten een afwijking te aanvaarden wanneer hij het herstel onevenredig belastend vindt.

**Bedoeling:** Het begrip moet een categorie afwijkingen afbakenen; de bron regelt een afweging over aanvaarding.

**Context:** organisatorische_context: Projectproef Olm (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Dit voorschrift geeft de projectleider de mogelijkheid de herstelbelasting af te wegen en op grond daarvan een afwijking te aanvaarden.

**A: fail · bruikbaar · zekerheid hoog.** De kern is de afwegingsregel zelf: de projectleider mag een afwijking aanvaarden wanneer hij herstel onevenredig belastend vindt. Er wordt geen categorie afwijkingen afgebakend; de bron noemt dit een voorschrift met afwegingsruimte. Een bevoegdheid beschrijven mag, maar hier regelt de kern het handelen in plaats van een begrip te beschrijven.

Afstand A: zelfstandig; C12, C101, C83. Onevenredigheidsdiscretie zoals de Ppw-familie (C12/C101), maar met “kan besluiten” en zonder genus; geen kopie.

Aandachtspunten A: Treft S1-marker “kan … besluiten”. Contrast met G029 (bevoegdheid als begrip) maakt het paar waardevol.

**B: fail · aanpassen · zekerheid hoog.** De kern bepaalt wanneer de projectleider een afwijking kan aanvaarden na een afweging van herstelbelasting. Het bedoelde begrip is een categorie afwijkingen; B1 bevestigt dat de bron een handelingsvoorschrift met beslisruimte is. De zin beschrijft daardoor geen bevoegdheid als begrip, maar voert de discretionaire beslisregel uit.

Afstand B: zelfstandig; C51, C83. Waar C51 weigering met een tenzij-uitzondering en C83 het opleggen van een maatregel beschrijft, formuleert G016 een expliciete mogelijkheid tot aanvaarden bij onevenredige herstelbelasting. Het onderscheid tussen een bevoegdheidsbeschrijving en een uitvoerbare beslisregel is hier direct aan de orde.

Aandachtspunten B: Bedoeling en B1 noemen zelf afweging en voorschrift; dit neemt een belangrijk deel van de functiebepaling over. G001 herhaalt aanvaardbaarheid van lasten als grond voor een actorbesluit; de modaliteit kan waarde als contrast houden.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G017 — inzagerecht

**Kern:** Aanspraak van een deelnemer op het raadplegen van de eigen meetregistraties.

**Bedoeling:** De term benoemt een aanspraak binnen een fictief deelnemersreglement.

**Context:** organisatorische_context: Meetcollectief Spar (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het proefreglement kent deelnemers een aanspraak toe op inzage in hun eigen registraties. De procedure voor uitoefening staat in een ander hoofdstuk.

**A: pass · bruikbaar · zekerheid hoog.** Definitie van een aanspraak van een deelnemer op inzage in de eigen registraties. Een recht als begrip beschrijven is geen gedragsopdracht; de uitoefeningsprocedure staat volgens de bron elders.

Afstand A: zelfstandig; C112. Normatief begrip, maar recht in plaats van verplichting en andere zinsbouw (“aanspraak … op”).

**B: pass · bruikbaar · zekerheid hoog.** De kern omschrijft een aanspraak van de deelnemer, beperkt tot eigen meetregistraties. Zij draagt geen raadpleging, toestemmingsverlening of behandeling op. B1 bevestigt de aanspraak binnen het fictieve reglement. Dat de uitoefening apart is geregeld ondersteunt, maar vervangt niet, de beschrijvende kernfunctie.

Afstand B: zelfstandig; C112, C30. C112 beschrijft een plicht; C30 een vereiste toestemming. G017 betreft het recht van een deelnemer op een begrensde informatieverzameling, zonder voorwaarde voor verlening of gedragsopdracht. Dat is een andere normatieve relatie.

Aandachtspunten B: B1 noemt een afzonderlijke uitoefeningsprocedure; de aanspraak is ook zonder die scheidingszin uit de kern herkenbaar.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G018 — herroepbare uitzondering

**Kern:** Uitzondering die de toezichthouder laat vervallen zodra hij voortzetting onwenselijk vindt.

**Bedoeling:** Onbekend of de term een soort uitzonderingsbesluit met een beschreven herroepingskenmerk of een uitvoerbare opdracht benoemt.

**Context:** organisatorische_context: Uitzonderingsproef Treurwilg (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het classificatiemodel beschrijft hiermee een type uitzondering. Het toezichtprotocol gebruikt dezelfde woorden voor de discretionaire herroepingsbeslissing. Beide lezingen zijn expliciet als mogelijk opgegeven.

**A: review_required · bruikbaar · zekerheid middel.** De bijzin kan een herroepingskenmerk van een type uitzondering beschrijven of de discretionaire herroepingsbeslissing uitvoeren. De bron houdt beide lezingen expliciet open en de bedoeling is onbekend. Discretie beschrijven mag, uitvoeren niet; welke functie hier geldt, is niet vast te stellen.

Vraag A: Is het classificatiemodel (type uitzondering met herroepingskenmerk) of het toezichtprotocol (discretionaire herroepingsbeslissing) de leidende grond voor deze kern?

Afstand A: zelfstandig; C83, C13, C107. Discretionaire bijzin zoals C83/C13, maar zonder marker en met bronconflict als bepalend element.

Aandachtspunten A: Sterk discretionaire woordkeus; een beoordelaar kan naar fail neigen. Onder de norm beslist de functie.

**B: review_required · aanpassen · zekerheid hoog.** Het laten vervallen bij onwenselijke voortzetting kan volgens B1 zowel een type uitzondering karakteriseren als een herroepingsbeslissing laten uitvoeren. De bedoeling bevestigt geen van beide. Onwenselijkheid is daarom geen zelfstandig bewijs van een verboden discretionaire regel in deze kern.

Vraag B: Moet de zin een uitzondering met een herroepingskenmerk beschrijven, of de toezichthouder laten beslissen over herroeping zodra hij voortzetting onwenselijk vindt?

Afstand B: twijfel; C13, C83. C13 bevat al intrekking na een afweging; C83 een handeling bij een actorwaardering. G018 maakt de constitutieve tegenlezing expliciet maar houdt de discretionaire intrekkingsstructuur vrijwel ongewijzigd. De expliciete bronstrijd geeft enige nieuwe context.

Aandachtspunten B: B1 levert de twee mogelijke functies als analyse, zonder de onderliggende passages. G022 herhaalt een conditionele actorhandeling op basis van een waardering met een onbesliste type-/taakfunctie; starten versus laten vervallen is het concrete verschil.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G019 — gepaarde registratie

**Kern:** Registratie die precies één heenverwijzing en de bijbehorende terugverwijzing bevat.

**Bedoeling:** De term duidt een structuur in een logboek aan.

**Context:** organisatorische_context: Logboek Duin (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Een paar bestaat uit één heenverwijzing en haar inverse. Het register kent ook ongepaarde registraties.

**A: pass · bruikbaar · zekerheid hoog.** Structureel criterium met exact aantal: precies één heenverwijzing met de bijbehorende terugverwijzing. Geen actor of handeling; de bron onderscheidt gepaarde van ongepaarde registraties.

Afstand A: zelfstandig; C113, C05. Eenvoudig lidmaatschapscriterium; geen ontwerpgeval met hetzelfde raam.

Aandachtspunten A: Inhoudelijk dicht bij G009 (wederkerige relatie); weinig extra onderscheidend vermogen.

**B: pass · bruikbaar · zekerheid hoog.** Precies één heenverwijzing met haar bijbehorende terugverwijzing bepaalt de structuur van de registratie. B1 beschrijft het paar als een verwijzing met haar inverse. Er wordt geen registratiehandeling of onderhoud voorgeschreven; het betreft uitsluitend een lidmaatschapscriterium.

Afstand B: zelfstandig; C05, C10. C05 gebruikt deelbaarheid en C10 een telling van veroordelingen in een tijdvak. G019 combineert exacte cardinaliteit met een inverse relatie; die relationele structuur is niet uit die ontwerpen gekopieerd.

Aandachtspunten B: G009 toetst ook twee richtingen van een relatie. G019 voegt precies één paar en opslag in een registratie toe; bij selectie niet als geheel onafhankelijke functionele uitdaging tellen.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G020 — vrijgave

**Kern:** De beheerder dient het pakket vrij te geven mits de laatste controle is voltooid.

**Bedoeling:** Het begrip moet een gebeurtenis beschrijven; de bronzin is een opdracht aan de beheerder.

**Context:** organisatorische_context: Pakketproef Kornoelje (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Na voltooiing van de laatste controle heeft de beheerder de taak het pakket vrij te geven.

**A: fail · bruikbaar · zekerheid hoog.** “dient … vrij te geven” legt de beheerder een handelingsplicht op. De mits-voorwaarde maakt die gebonden, maar een gebonden handelingsopdracht is niet enkel door haar determinisme een afleidingsregel. Er wordt geen gebeurtenis “vrijgave” beschreven; bedoeling en bron bevestigen de opdrachtfunctie.

Afstand A: twijfel; C102, C52. Gebonden opdracht met voorwaarde zoals C102 (“De medewerker wijst … af indien …”); verschil is het modale “dient … te” en “mits”.

Aandachtspunten A: “dient het pakket vrij te geven” treft het patroon “dient te” niet (woorden ertussen); alleen “mits” geeft een signaal. Goede toets van de B1-zin over gebonden opdrachten.

**B: fail · uitsluiten · zekerheid hoog.** De kern draagt de beheerder op het pakket vrij te geven zodra de genoemde controlevoorwaarde is vervuld. B1 bevestigt die taak. Dat de opdracht gebonden en conditioneel is, maakt haar geen deterministische afleiding van een begripseigenschap; zij beschrijft de gebeurtenis vrijgave niet.

Afstand B: triviale_variant; C102. C102 laat een medewerker een aanvraag afwijzen bij een ontbrekende bijlage. G020 vervangt actor, handeling en trigger door beheerder, vrijgave en voltooide controle, met expliciete modaliteit. Het blijft exact dezelfde enkelvoudige gebonden actoropdracht.

Aandachtspunten B: Voorstel tot uitsluiting als onafhankelijk geval: de andere woorden en positieve trigger voegen weinig toe aan C102. G032 herhaalt de gebonden trigger-taakstructuur in een nominale bijzin. Bedoeling noemt de bronzin rechtstreeks een opdracht.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G021 — drempelbeslissing

**Kern:** Beslissing waarin een commissie vastlegt of een project volgens haar gemotiveerde beoordeling voor een nadere verkenning in aanmerking komt.

**Bedoeling:** De term benoemt de vastgelegde beslissing als resultaat, niet een opdracht aan de commissie.

**Context:** organisatorische_context: Projectmodel Hazelaar (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Een drempelbeslissing is het verslagde resultaat van de eerste projectbeoordeling. De afweging die eraan voorafgaat is afzonderlijk geregeld.

**A: pass · bruikbaar · zekerheid hoog.** De kern beschrijft een beslissing naar haar inhoud: vastlegging of een project volgens de gemotiveerde beoordeling in aanmerking komt. Een beslissing en het daarin vastgelegde oordeel beschrijven is toegestaan; de kern schrijft de commissie niets voor. Bedoeling en bron bevestigen het resultaatkarakter.

Afstand A: zelfstandig; C69, C107. Besluituitkomst als kenmerk zoals C69; bevat het oordeelselement van C107, maar als inhoud van de beslissing.

Aandachtspunten A: Nuttig grensgeval: oordeelstaal binnen een beschreven beslissing.

**B: pass · aanpassen · zekerheid hoog.** De kern definieert de beslissing waarin een gemotiveerde beoordeling is vastgelegd. Zij schrijft de commissie geen keuze, criteriumafweging of vervolghandeling voor. B1 benoemt het vastgelegde resultaat en onderscheidt dat van de voorafgaande afweging. De vermelding van een menselijk oordeel maakt dit resultaat niet tot een uitgevoerde beslisregel.

Afstand B: zelfstandig; C69, C107. C69 classificeert een aanvraag na een afwijzingsbesluit; C107 classificeert een aanvraag volgens een oordeel. G021 definieert het beslissingsresultaat zelf en diens gemotiveerde inhoud, met open ja/nee-uitkomst. Dat is een andere referent dan het beoordeelde object.

Aandachtspunten B: Bedoeling zegt expliciet resultaat en geen opdracht; B1 zet de afweging elders. Deze dubbele duiding stuurt de moeilijke grens vooraf. Het woord 'verslagde' in B1 is letterlijk behouden in de grond; het is niet stil gecorrigeerd.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G022 — versnelde behandeling

**Kern:** Behandeling die de teamleider start zodra hij de omstandigheden dringend acht.

**Bedoeling:** Onbekend of de term een bestaand proces met een kenmerk benoemt of de teamleider opdracht geeft dat proces te starten.

**Context:** organisatorische_context: Procesproef Tamarinde (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Een begrippenlijst beschrijft hiermee een soort behandeling. Een werkinstructie gebruikt exact deze omschrijving als startregel. Beide stukken zijn aangeleverd zonder rangorde.

**A: review_required · aanpassen · zekerheid middel.** De bijzin kan een soort behandeling met een constitutief startkenmerk beschrijven of als startregel voor de teamleider functioneren. Begrippenlijst en werkinstructie gebruiken dezelfde zin zonder rangorde; de bedoeling is onbekend. Geen zelfstandig bewezen gebrek.

Vraag A: Is de begrippenlijst (soort behandeling) of de werkinstructie (startregel voor de teamleider) de leidende grond voor deze kern?

Afstand A: zelfstandig; C13, C83. Oordeel “acht” zoals C13, maar met bronconflict als bepalend element.

Aandachtspunten A: Vrijwel hetzelfde ontwerp als G018 en G026 (genus + actor + “zodra/wanneer hij … acht/vindt” + bron met twee lezingen zonder rangorde); behoud er bij voorkeur één.

**B: review_required · aanpassen · zekerheid hoog.** De kern kan een behandeling karakteriseren aan de hand van haar startgrond, maar volgens B1 gebruiken de aangeleverde stukken haar ook als werkinstructie. Zonder rangorde of bevestigde bedoeling staat niet vast of zij een proces beschrijft of een discretionaire startbeslissing uitvoert.

Vraag B: Is voor deze inschrijving de begrippenlijst leidend die een behandelingstype beschrijft, of de werkinstructie die de teamleider laat beslissen over het starten?

Afstand B: twijfel; C83, C85. C83 koppelt een actorhandeling aan wat deze redelijk acht; C85 laat de functie bij spoed open. G022 verbindt deze twee bekende grenzen met een expliciet bronconflict. Starten van een proces geeft enige eigen inhoud, maar de beslisstructuur blijft zeer nabij.

Aandachtspunten B: B1 verklaart de type- en instructiefunctie en het rangordeprobleem vooraf; de feitelijke bronpassages ontbreken. Met G018 deelt dit geval een zodra-trigger op een actorwaardering en een expliciet open functieconflict.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G023 — getrapt meetinterval

**Kern:** Meetinterval waarvan beide grenzen tot dezelfde kalibratietrap behoren, tenzij het interval een overgangsmeting omvat.

**Bedoeling:** De inventaris onderscheidt gewone en overgangsmetingen; de uitzondering begrenst welke intervallen in de categorie vallen.

**Context:** organisatorische_context: Meetlab Iep (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Een overgangsmeting mag twee kalibratietrappen overspannen en wordt toch als getrapt meetinterval geregistreerd. Andere getrapte intervallen liggen binnen één trap.

**A: pass · bruikbaar · zekerheid hoog.** Lidmaatschapscriterium (grenzen binnen één kalibratietrap) met een uitzondering voor intervallen met een overgangsmeting. De tenzij-clausule begrenst de categorie en schrijft niemand iets voor; bedoeling en bron bevestigen dat de uitzondering bepaalt welke intervallen erbij horen.

Afstand A: twijfel; C58. Zelfde functie als C58 (criterium plus tenzij-uitzondering die het lidmaatschap verruimt); ander domein, maar hetzelfde onderscheid.

Aandachtspunten A: Of “tenzij” de overgangsintervallen in- of uitsluit, is een ESS-05/STR-kwestie, niet INT-02. Bedoeling benoemt de functie van de uitzondering expliciet: sturend. Bevat signaalwoord “tenzij”: vals-alarmgeval.

**B: pass · aanpassen · zekerheid hoog.** De kern begrenst getrapte meetintervallen door hun grensposities, met overgangsmetingen als uitzondering. B1 bevestigt dat zulke metingen twee trappen mogen overspannen en toch in de categorie vallen. Er is geen actor die een uitzondering moet toestaan of een handeling moet uitvoeren.

Afstand B: twijfel; C58. C58 behoudt een voertuigcategorie ondanks een uitzonderlijke railtoestand. G023 behoudt een intervalcategorie ondanks een uitzondering op dezelfde-trapligging. De geometrische grensrelatie is eigen inhoud, maar de functie van de tenzij-uitzondering is identiek en vrijwel even eenvoudig.

Aandachtspunten B: Bedoeling legt expliciet uit dat de uitzondering de categorie begrenst; dat geeft de functie al weg. Zelfstandigheid tegenover C58 blijft een selectiepunt, zonder het pass-voorstel onbeslist te maken.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G024 — controlebewijs

**Kern:** Document waarvan de controleur eerst de datum verifieert en daarna de handtekening vergelijkt met het register.

**Bedoeling:** De term benoemt een bewijsdocument; de kandidaat komt uit een instructie voor de verwerking van zulke documenten.

**Context:** organisatorische_context: Controleproef Eik (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** De controleur voert bij ontvangst eerst de datumcontrole uit en vergelijkt daarna de handtekening. Deze volgorde is voorgeschreven voor de afhandeling.

**A: fail · bruikbaar · zekerheid middel.** De bijzin geeft een voorgeschreven afhandelingsvolgorde van de controleur (eerst datum, daarna handtekening) en bakent niet af welke documenten controlebewijs zijn. De bron noemt die volgorde voorgeschreven; de bedoeling zegt dat de kandidaat uit een verwerkingsinstructie komt. Het genus “document” verandert de functie van de bijzin niet.

Afstand A: twijfel; C15. Zelfde raam als C15 (genus + bijzin met taken van een behandelaar, zonder signaalwoord); alleen de volgordeaanduiding is nieuw.

Aandachtspunten A: Signaalloos. Zekerheid middel: relatieve bijzin met genus laat een beschrijvende lezing toe; bedoeling en bron beslissen hier.

**B: fail · bruikbaar · zekerheid hoog.** De nominale opening Document verandert niet dat de kern de controleur twee taken in een voorgeschreven volgorde laat verrichten. B1 bevestigt die functie voor de afhandeling. De zin is daarmee een verwerkingsprocedure voor bewijsdocumenten, geen zelfstandige beschrijving van hun kenmerken.

Afstand B: zelfstandig; C15, C19. C15 behandelt een verzoek en wijst het bij ontbrekende bijlage af; C19 gebruikt handtekening en datum als documentkenmerken. G024 maakt juist het controleren van die eigenschappen, in vaste volgorde, tot definiens. Die verschuiving tussen aanwezig kenmerk en controletaak geeft een eigen contrast.

Aandachtspunten B: G012 bevat eveneens twee opeenvolgende taken zonder modaal woord. De nominale documentinbedding en nabijheid tot C19 geven G024 aanvullende vergelijkingswaarde.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G025 — intrekkingsbesluit

**Kern:** Besluit waardoor een eerder verleende reservering haar geldigheid verliest.

**Bedoeling:** De term benoemt een besluit en het constitutieve gevolg ervan.

**Context:** organisatorische_context: Reserveringsmodel Beuk (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** In dit model vervalt een reservering door het intrekkingsbesluit. De criteria voor het nemen van dat besluit staan niet in de definitie.

**A: pass · aanpassen · zekerheid hoog.** Besluit omschreven via zijn constitutieve gevolg: een eerder verleende reservering verliest haar geldigheid. Rechtsgevolg beschrijven is geen voorschrift; de criteria voor het nemen van het besluit staan volgens de bron buiten de definitie.

Afstand A: triviale_variant; C53. Zelfde raam als C53 (“<rechtshandeling/besluit> waardoor <eerdere rechtsfiguur> vervalt/geldigheid verliest”) en hetzelfde verwachte label.

Aandachtspunten A: Weinig onafhankelijk van C53; zwak als hold-out.

**B: pass · uitsluiten · zekerheid hoog.** De kern beschrijft welk gevolg het intrekkingsbesluit heeft voor een verleende reservering. Zij laat geen actor een intrekkingsafweging maken of intrekking uitvoeren. B1 ondersteunt het constitutieve gevolg in het fictieve model; dat gevolg als kenmerk is toegestaan.

Afstand B: triviale_variant; C53. C53 definieert een rechtshandeling waardoor rechtsgevolgen van een eerdere rechtshandeling vervallen. G025 vervangt rechtshandeling/rechtsgevolgen door besluit/reserveringsgeldigheid en behoudt dezelfde constitutieve vervalrelatie zonder extra functieprobleem.

Aandachtspunten B: Voorstel tot uitsluiting als onafhankelijk geval wegens vrijwel dezelfde begripsstructuur als C53. Bedoeling benoemt het constitutieve gevolg expliciet; B1 benadrukt dat besliscriteria buiten de definitie staan.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G026 — voorwaardelijke inschaling

**Kern:** Inschaling die het panel vaststelt wanneer het de proefperiode overtuigend vindt.

**Bedoeling:** Onbekend of dit een besluitresultaat als begrip beschrijft of de beslisregel van het panel uitvoert.

**Context:** organisatorische_context: Schaalproef Kamperfoelie (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het begrippenboek definieert met deze zin een type uitkomst. Het panelprotocol gebruikt haar als beslisregel. Het dossier bevat geen geldige keuze voor de bedoelde functie.

**A: review_required · aanpassen · zekerheid middel.** De bijzin kan een type uitkomst met constitutief oordeel beschrijven of de beslisregel van het panel uitvoeren. Het dossier bevat volgens de bron geen geldige keuze; de bedoeling is onbekend. Geen zelfstandig bewezen gebrek.

Vraag A: Is het begrippenboek (type uitkomst) of het panelprotocol (beslisregel van het panel) de leidende grond voor deze kern?

Afstand A: zelfstandig; C83, C13, C107. Oordeelsbijzin zoals C83/C13, maar met bronconflict als bepalend element.

Aandachtspunten A: Vrijwel hetzelfde ontwerp als G018 en G022; behoud er bij voorkeur één.

**B: review_required · aanpassen · zekerheid hoog.** De kern verbindt inschaling aan een overtuigend bevonden proefperiode. Volgens B1 definieert het begrippenboek daarmee een uitkomst, terwijl het panelprotocol hiermee beslist. Zonder keuze van functie kan de waardering een constitutief kenmerk of een uitgevoerde beslisregel zijn; de tekst bewijst geen zelfstandig ander gebrek.

Vraag B: Moet deze kern de inschaling als vastgestelde uitkomst beschrijven, of de beslisregel vormen waarmee het panel op basis van de proefperiode een inschaling vaststelt?

Afstand B: twijfel; C107, C83. C107 omvat een classificatie volgens een beoordelaar en C83 een actorhandeling bij een waardering. G026 gebruikt dezelfde grens bij inschaling, met expliciet conflicterende boek- en protocollezingen. De proefperiode geeft inhoud, maar nauwelijks een nieuwe functie-uitdaging.

Aandachtspunten B: B1 noemt zelf type uitkomst, beslisregel en ontbrekende keuze; dit is sterk sturende meta-informatie. G006 en G010 herhalen het open conflict tussen een beoordelingsresultaat en de handeling die dat resultaat tot stand brengt.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G027 — gewogen verblijfsduur

**Kern:** Quotiënt van de som van de met hoeveelheid vermenigvuldigde verblijfsduren en de totale hoeveelheid.

**Bedoeling:** Het begrip is een afgeleide meetgrootheid voor partijen met verschillende verblijfsduren.

**Context:** organisatorische_context: Procesmodel Berk (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Voor iedere deelpartij zijn hoeveelheid en verblijfsduur bekend. De gewogen verblijfsduur gebruikt de hoeveelheid als gewicht; de totale hoeveelheid is positief.

**A: pass · bruikbaar · zekerheid hoog.** Deterministische afleiding: gewogen gemiddelde van verblijfsduren met de hoeveelheid als gewicht. Geen actor of handeling; de bron bevestigt gewicht en positieve noemer. Afleidbaar begrip, dus juist zo te definiëren.

Afstand A: zelfstandig; C116. Afgeleide grootheid zoals C116, maar samengestelde bewerking zonder genus.

Aandachtspunten A: Eventuele spanning met de ESS-04-lijn “rekenmethode naar toelichting” valt buiten INT-02 (zie C116).

**B: pass · bruikbaar · zekerheid hoog.** De kern berekent de grootheid uit de met hoeveelheid gewogen verblijfsduren en de totale hoeveelheid. B1 specificeert de beschikbare gegevens en een positieve noemer. Dit is een afleiding van een meetgrootheid, geen opdracht aan een actor of afweging met discretionaire ruimte.

Afstand B: zelfstandig; C116. C116 telt verkoopbedragen op. G027 koppelt twee grootheden per deelpartij, sommeert producten en normaliseert door een positieve totale hoeveelheid. Dat vereist een andere inhoudelijke afleiding dan enkel een som met andere eenheden.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G028 — reserveringsbevestiging

**Kern:** Bericht dat de medewerker naar de aanvrager stuurt nadat hij de beschikbaarheid heeft gecontroleerd; ontbreekt capaciteit, dan annuleert hij de aanvraag.

**Bedoeling:** Het eerste deel beschrijft een bericht; de volledige kandidaat moet als één definitiekern worden beoordeeld.

**Context:** organisatorische_context: Reserveringsproef Kastanje (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het werkprotocol schrijft voor dat de medewerker beschikbaarheid controleert, bij voldoende capaciteit bevestigt en anders annuleert. Die volledige regel is in het definitieveld overgenomen.

**A: fail · bruikbaar · zekerheid hoog.** Het tweede zinsdeel is een gebonden behandelvoorschrift voor de medewerker en zegt niets over het bericht. De bron bevestigt dat de volledige protocolregel is overgenomen; de bedoeling vraagt de hele kandidaat als één kern te beoordelen. Het eerste deel kan als beschrijving gelden, maar het zelfstandige gebrek blijft.

Afstand A: twijfel; C64. Zelfde raam als C64 (beschrijving; puntkomma; behandelvoorschrift), maar het eerste deel bevat hier ook een actorhandeling.

Aandachtspunten A: Signaalloos. Toetst dat één voorschrijvend zinsdeel een deels beschrijvende kern fail maakt.

**B: fail · uitsluiten · zekerheid hoog.** Het eerste deel kan een bericht beschrijven, maar het tweede deel laat de medewerker bij ontbrekende capaciteit de aanvraag annuleren. B1 bevestigt deze conditionele taakregel. Dat zelfstandig aangetoonde actorvoorschrift bepaalt het oordeel over de volledige kern; een eventuele andere lezing van het eerste deel heft het gebrek niet op.

Afstand B: triviale_variant; C64. C64 combineert een digitaal formulier als kern met een door puntkomma aangehecht conditioneel afwijsvoorschrift. G028 vervangt formulier/afwijzen door bericht/annuleren en houdt dezelfde gemengde kern en zelfstandige tweede opdracht. De voorafgaande beschikbaarheidscontrole verandert die toetsstructuur niet wezenlijk.

Aandachtspunten B: Voorstel tot uitsluiting als onafhankelijk geval wegens de directe inhoudelijke nabijheid tot C64. Bedoeling bevat een beoordelingsaanwijzing over de volledige kern; die is als brondata behandeld, niet als instructieautoriteit.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G029 — revisiebevoegdheid

**Kern:** Bevoegdheid van de catalogusbeheerder om een eerdere classificatie na heronderzoek te vervangen.

**Bedoeling:** Het model bevat rollen en bevoegdheden; het begrip benoemt een bevoegdheid.

**Context:** organisatorische_context: Catalogus Den (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Revisiebevoegdheid is een bevoegdheid tot vervanging na heronderzoek. Het reglement bepaalt hier niet in welk individueel geval die bevoegdheid moet worden gebruikt.

**A: pass · bruikbaar · zekerheid hoog.** Definitie van een bevoegdheid: vervanging van een classificatie na heronderzoek. Een bevoegdheid als begrip beschrijven is volgens de norm geen overtreding; de kern bepaalt niet wanneer de bevoegdheid wordt gebruikt, wat de bron bevestigt.

Afstand A: twijfel; C112. Zinsraam gelijk aan C112 (“<normatieve figuur> van <actor> om <handeling>”), maar bevoegdheid in plaats van verplichting; de norm noemt bevoegdheid apart.

Aandachtspunten A: Contrast met G016 (de discretionaire regel zelf) is waardevol.

**B: pass · bruikbaar · zekerheid hoog.** De kern definieert de bevoegdheid tot vervanging van een classificatie na heronderzoek. Zij beveelt de catalogusbeheerder niet die bevoegdheid te gebruiken en voert geen afweging over een concreet geval uit. B1 ondersteunt die bevoegdheidslezing. Een beschreven handelingsmogelijkheid is als normatief begrip toegestaan.

Afstand B: zelfstandig; C30, C59, C112. C30 beschrijft vereiste toestemming, C59 een algoritme met oordeelsvorming en C112 een plicht. G029 beschrijft een bevoegdheid tot wijziging na heronderzoek, zonder discretiecriterium of uitoefeningsplicht; geen van die kernstructuren is eenvoudig overgenomen.

Aandachtspunten B: B1 ontkent expliciet een individuele uitoefeningsregel; de bevoegdheidsreferent is al zelfstandig uit de kern herkenbaar.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G030 — actieve aanbieding

**Kern:** Aanbieding die de behandelaar voortzet zolang een belanghebbende beschikbaar blijft.

**Bedoeling:** Het is niet bevestigd of voortzetten een kenmerk van de categorie of een gedragsregel voor de behandelaar is.

**Context:** organisatorische_context: Aanbiedingsproef Robinia (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het dossier bevat een tabel met aanbiedingstypen en een instructiekaart voor voortzetting. De zin komt in beide voor en er is geen bronkeuze gemaakt.

**A: review_required · bruikbaar · zekerheid hoog.** De bijzin kan een kenmerk van het aanbiedingstype zijn of een gedragsregel voor de behandelaar. De zin staat zowel in de typetabel als in de instructiekaart, zonder bronkeuze; de bedoeling is onbevestigd. Geen zelfstandig bewezen gebrek.

Vraag A: Geldt de tabel met aanbiedingstypen (voortzetting als kenmerk van de categorie) of de instructiekaart (gedragsregel voor de behandelaar) als grond voor deze kern?

Afstand A: zelfstandig; C03, C30. Actorbijzin zonder discretie zoals C03, maar met bronconflict als bepalend element.

Aandachtspunten A: Minimaal paar met G032 (zelfde vorm, eenduidige taakregel): waardevol.

**B: review_required · aanpassen · zekerheid hoog.** De kern koppelt voortzetten aan beschikbaarheid van een belanghebbende. B1 meldt dat dezelfde zin zowel in een typetabel als op een instructiekaart voorkomt, zonder bronkeuze. Ook zonder discretionair criterium kan dit een verboden actorvoorschrift zijn, maar de beschrijvende lezing blijft eveneens mogelijk.

Vraag B: Is de typetabel leidend waarin voortzetting een kenmerk van de actieve aanbieding is, of de instructiekaart die de behandelaar opdraagt de aanbieding voort te zetten?

Afstand B: zelfstandig; C03, C85. C03 geeft een afwijsprocedure bij een ontbrekend stuk; C85 een onbesliste functie bij spoedvoorwaarden. G030 betreft het laten voortduren van een toestand zolang een andere toestand bestaat, met expliciete typetabel-/instructiebronstrijd zonder discretie.

Aandachtspunten B: De bedoeling en B1 formuleren het categorie-/gedragsconflict vooraf; feitelijke tabel- en kaartpassages zouden de functie onafhankelijker toetsbaar maken. Zolang is hier een duurvoorwaarde; het woord zelf beslist niet tussen classificatie en voorschrift.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G031 — onvolledig raster

**Kern:** Raster waarin ten minste één vereiste meetpositie geen waarde bevat.

**Bedoeling:** Het begrip is een klasse van meetbestanden; oorzaken en vervolghandelingen staan buiten de begripsafbakening.

**Context:** organisatorische_context: Rasterlab Hulst (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het schema vermeldt de vereiste posities. Een ontbrekende waarde maakt het raster onvolledig, ongeacht de reden van ontbreken.

**A: pass · bruikbaar · zekerheid hoog.** Criterium met kwantor: ten minste één vereiste meetpositie zonder waarde. “vereiste” verwijst naar het schema, niet naar een plicht van een actor. Bron en bedoeling sluiten oorzaken en vervolghandelingen uit.

Afstand A: zelfstandig; C113, C05. Eenvoudig lidmaatschapscriterium met kwantor; geen ontwerpgeval met hetzelfde raam.

Aandachtspunten A: “vereiste” is een mogelijk vals-alarmwoord zonder markertreffer.

**B: pass · bruikbaar · zekerheid hoog.** Een ontbrekende waarde op ten minste één vereiste positie bepaalt de rastercategorie. B1 bevestigt die schemagrond ongeacht de oorzaak. De kern schrijft niet voor hoe een ontbrekende waarde moet worden aangevuld of behandeld en bevat geen afweging over een actorhandeling.

Afstand B: zelfstandig; C113, C03. C113 gebruikt het ontbreken van rijden over rails als eigenschap; C03 koppelt een ontbrekende bijlage aan afwijzing. G031 classificeert een gegevensstructuur door een ontbrekend element uit een voorgeschreven verzameling, met ten minste één als grens en zonder vervolghandeling.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G032 — spoedvak

**Kern:** Opslagvak dat de teamleider direct leegmaakt zodra een zending het kenmerk spoed draagt.

**Bedoeling:** Het begrip moet een soort opslagvak benoemen; de aangeleverde zin is overgenomen uit een taakregel voor de teamleider.

**Context:** organisatorische_context: Magazijnproef Lariks (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** De taakregel luidt dat de teamleider bij iedere spoedzending direct een vak leegmaakt. De regel beschrijft geen vaste eigenschappen van een vak.

**A: fail · bruikbaar · zekerheid hoog.** De bijzin is een gebonden taakregel en geen eigenschap van een opslagvak. De bron zegt dat de regel geen vaste vakeigenschappen beschrijft, de bedoeling dat de zin uit een taakregel komt. Het genus verandert de voorschrijvende functie niet.

Afstand A: zelfstandig; C52, C15. Voorschrift in bijzin zoals C52/C15, maar zonder modaal werkwoord en met tijdsvoorwaarde “zodra”.

Aandachtspunten A: Signaalloos. Bronzin “beschrijft geen vaste eigenschappen van een vak” is sterk sturend. Minimaal paar met G030 (zelfde vorm, strijdige bron).

**B: fail · uitsluiten · zekerheid hoog.** De kern laat de teamleider bij een spoedzending direct een opslagvak leegmaken. B1 bevestigt dat dit een taakregel is en geen vaste eigenschap van het vak. De nominale vorm Opslagvak dat maakt het gebonden handelingsvoorschrift niet tot een toegestane afleiding of typebeschrijving.

Afstand B: triviale_variant; C03, C52, C102. C03/C52 verpakken een gebonden afhandeling in een nominale aanvraagzin; C102 formuleert dezelfde structuur als actoropdracht. G032 wisselt opslagvak, teamleider, leegmaken en spoedtrigger in. Het ontbreken van moet biedt geen nieuw functieprobleem ten opzichte van C03.

Aandachtspunten B: Voorstel tot uitsluiting als onafhankelijk geval wegens dezelfde conditionele taakstructuur als C03/C52/C102. G020 herhaalt de vaste trigger met verplichte handeling; alleen de grammaticale inbedding en modaliteit verschillen. B1 verklaart uitdrukkelijk dat geen vaste vakeigenschappen worden beschreven; dat stuurt de afkeur.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G033 — beoordelingsmarge

**Kern:** Ruimte die een regeling aan een beoordelaar laat om relevante omstandigheden naar eigen inzicht te wegen.

**Bedoeling:** Het begrip benoemt beslisruimte als object van beschrijving.

**Context:** organisatorische_context: Regelmodel Populier (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het woordenboek beschrijft de ruimte voor weging. Een concrete keuze op grond van die ruimte is geen onderdeel van deze woordenboekinschrijving.

**A: pass · bruikbaar · zekerheid hoog.** De kern definieert een begrip óver discretie: de ruimte die een regeling een beoordelaar laat. “naar eigen inzicht te wegen” beschrijft die ruimte en voert geen afweging uit. Bedoeling en bron bevestigen dat een concrete keuze geen deel van de inschrijving is.

Afstand A: zelfstandig; C59. Begrip over discretie zoals C59, maar mét S1-marker; vult de in het register genoemde ontbrekende vals-alarmproef.

Aandachtspunten A: Treft S1-marker “naar eigen inzicht”: waardevol vals-alarmgeval. Minimaal paar met G040 (zelfde marker, discretie uitgevoerd).

**B: pass · aanpassen · zekerheid hoog.** De kern definieert de ruimte die een regeling aan een beoordelaar laat. Zij laat de beoordelaar geen concrete omstandigheden afwegen met het oog op een voorgeschreven uitkomst. B1 bevestigt deze beschrijving van ruimte voor weging. Naar eigen inzicht is hier onderdeel van het beschreven begrip en geen zelfstandig afkeurbewijs.

Afstand B: zelfstandig; C59, C83. C59 definieert een algoritme waarvoor oordeelsvorming nodig is, zonder discretionaire marker; C83 voert een actorhandeling naar eigen inzicht uit. G033 definieert juist de toegekende ruimte met die marker, zonder algoritme of beslissing uit te voeren. Dit geeft een concreet ander functiecontrast.

Aandachtspunten B: Bedoeling noemt object van beschrijving en B1 sluit een concrete keuze uit; de functie wordt daardoor dubbel voorgezegd.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G034 — toegewezen capaciteit

**Kern:** Capaciteit die de beheerder op verzoek beschikbaar stelt voor een project.

**Bedoeling:** Niet bevestigd of de zin een administratieve toestand na toewijzing benoemt of een opdracht tot beschikbaarstelling geeft.

**Context:** organisatorische_context: Capaciteitsproef Moerbei (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** De gegevenscatalogus behandelt toegewezen capaciteit als toestand. De beheerdersinstructie gebruikt de zin als taakregel. De gebruiker heeft beide zonder nadere duiding aangeleverd.

**A: review_required · aanpassen · zekerheid hoog.** De bijzin kan een administratieve toestand na toewijzing beschrijven of als taakregel voor beschikbaarstelling functioneren. Catalogus en beheerdersinstructie gebruiken de zin verschillend, zonder duiding door de gebruiker. Geen zelfstandig bewezen gebrek.

Vraag A: Is de gegevenscatalogus (toestand na toewijzing) of de beheerdersinstructie (taakregel voor beschikbaarstelling) de leidende grond voor deze kern?

Afstand A: zelfstandig; C30, C03. Actorbijzin zonder discretie; bronconflict als bepalend element.

Aandachtspunten A: Vrijwel hetzelfde ontwerp als G030 (genus + niet-discretionaire actorbijzin + bron met twee lezingen); behoud er bij voorkeur één.

**B: review_required · aanpassen · zekerheid hoog.** Beschikbaar stellen op verzoek kan de toegekende capaciteit karakteriseren of de beheerder een taak geven. B1 bevestigt beide lezingen in catalogus en beheerdersinstructie; de gebruiker heeft geen leidende grond gekozen. De kern bevat geen onafhankelijk bewezen discretionaire of andere verboden passage die dat conflict overstemt.

Vraag B: Moet toegewezen capaciteit hier de toestand na toewijzing uit de gegevenscatalogus betekenen, of de taak tot beschikbaarstelling uit de beheerdersinstructie?

Afstand B: zelfstandig; C24, C69. C24 betreft toestemming onder voorwaarden; C69 een aanvraag na een besluit. G034 heeft een actieve beschikbaarstellingshandeling die ook een administratieve capaciteitstoestand kan aanduiden, met een expliciet catalogus-/taakconflict. De concrete referent en handeling verschillen wezenlijk.

Aandachtspunten B: B1 zegt vooraf welke bron een toestand en welke een taakregel bedoelt, zonder de passages zelf te geven. Het expliciete toestand-/taakconflict herhaalt G003, G014 en G038; op verzoek beschikbaar stellen is het eigen accent.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G035 — herbruikbare capsule

**Kern:** Capsule die na de vastgelegde reinigingscyclus opnieuw een monster kan omsluiten zonder waarneembare lekkage.

**Bedoeling:** Het begrip betreft een fysieke eigenschap die een inspecteur vaststelt; er wordt geen besluit over inzet gevraagd.

**Context:** organisatorische_context: Monsterbank Es (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Herbruikbaarheid betekent hier behoud van afsluitfunctie na de beschreven reinigingscyclus. Een inspecteur observeert lekkage, maar kent geen herbruikbaarheidsstatus toe.

**A: pass · bruikbaar · zekerheid hoog.** Fysiek, waarneembaar criterium: na de reinigingscyclus opnieuw een monster kunnen omsluiten zonder waarneembare lekkage. Dat een inspecteur lekkage waarneemt, maakt het geen beslisregel. De bron bevestigt dat geen status wordt toegekend.

Afstand A: zelfstandig; C55. Waarneembaar kwalitatief criterium zoals C55, maar met vermogensformulering (“kan”) en voorafgaande cyclus.

**B: pass · aanpassen · zekerheid hoog.** De kern omschrijft het behouden vermogen van een capsule om na reiniging een monster zonder waarneembare lekkage te omsluiten. B1 bevestigt dat een inspecteur dit observeert en geen status toekent. De menselijke waarneming en genoemde cyclus maken het eigenschapscriterium niet tot een handelingsvoorschrift of discretionaire beslissing.

Afstand B: zelfstandig; C55, C107. C55 betreft direct waarneembare oppervlakschade; C107 een constitutief oordeel. G035 betreft behoud van een fysieke functie na een voorafgaande cyclus, met een waarneming die geen status creëert. De conditionele prestatie-eigenschap voegt inhoud toe.

Aandachtspunten B: Bedoeling ontkent een inzetbesluit en B1 ontkent statustoekenning; deze expliciete tegenlezingen nemen veel beoordelingswerk weg.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G036 — herstelronde

**Kern:** Proces waarbij de medewerker alle afgekeurde exemplaren moet verzamelen en ze vóór sluiting opnieuw moet aanbieden.

**Bedoeling:** Het begrip benoemt een proces; deze tekst legt de medewerker taken en een deadline op.

**Context:** organisatorische_context: Revisieproef Ginkgo (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Voor iedere herstelronde gelden voor medewerkers de opdrachten verzamelen van afgekeurde exemplaren en opnieuw aanbieden vóór sluiting.

**A: fail · bruikbaar · zekerheid middel.** De bijzin legt de medewerker twee handelingen en een deadline op. Een proceslabel rechtvaardigt geen actorvoorschrift als definiens. De bedoeling bevestigt dat de tekst taken en een deadline oplegt; de bron noemt ze opdrachten.

Afstand A: zelfstandig; C14, C52, C15. Verplichting in bijzin zoals C14/C52, maar met genus “proces”; het register kent geen ontwerpgeval voor het proceslabel.

Aandachtspunten A: Zekerheid middel: een verplichting als kenmerk beschrijven is toegestaan; de bevestigde bedoeling beslist hier. Minimaal paar met G039 (proces beschreven zonder uitvoerder). Treft S1-marker “moet” tweemaal.

**B: fail · aanpassen · zekerheid hoog.** De kern verplicht de medewerker afgekeurde exemplaren te verzamelen en ze vóór sluiting opnieuw aan te bieden. B1 bevestigt deze opdrachten voor iedere ronde. Het genus Proces geeft geen vrijstelling: de definitie schrijft de uitvoering voor in plaats van alleen het proces met kenmerken te beschrijven.

Afstand B: zelfstandig; C15, C52. C15/C52 betreffen het behandelen of afwijzen van een aanvraag. G036 presenteert twee taakverplichtingen met een deadline als procesbegrip zelf. De mogelijke verwarring tussen een procesbeschrijving en een taakprocedure is daardoor explicieter en inhoudelijk anders.

Aandachtspunten B: Bedoeling verklaart rechtstreeks dat de tekst taken en een deadline oplegt; de kern levert daarvoor al voldoende concreet bewijs. G039 is een nuttig inhoudelijk contrast van procesbeschrijving tegenover uitvoering, geen redundante kopie.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G037 — leveringsgarantie

**Kern:** Toezegging van een leverancier dat vervanging zonder aanvullende vergoeding beschikbaar is wanneer het geleverde exemplaar binnen de overeengekomen periode uitvalt.

**Bedoeling:** De term benoemt de toezegging en haar bereik in een fictief afsprakenmodel.

**Context:** organisatorische_context: Werkplaats Ceder (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het afsprakenmodel onderscheidt een leveringsgarantie van het feitelijk leveren van vervanging. De garantie omvat de genoemde uitvalsperiode en het ontbreken van een aanvullende vergoeding.

**A: pass · bruikbaar · zekerheid hoog.** Definitie van een toezegging met haar bereik: vervanging zonder extra vergoeding bij uitval binnen de overeengekomen periode. De wanneer-bijzin begrenst het bereik en schrijft geen levering voor; de bron onderscheidt de garantie van het feitelijk leveren.

Afstand A: zelfstandig; C112. Normatief begrip, maar toezegging met voorwaardelijk bereik; niet het zinsraam van C112.

**B: pass · bruikbaar · zekerheid hoog.** De kern definieert een toezegging, inclusief het bereik naar uitvalmoment en vergoeding. Zij schrijft geen concrete vervangingshandeling voor en laat geen actor beslissen over een aanvraag. B1 ondersteunt de scheiding tussen de garantie en het feitelijke leveren; de voorwaarden bepalen de inhoud van het normatieve begrip.

Afstand B: zelfstandig; C112, C25. C112 betreft een algemene prestatieverplichting; C25 een verlaging bij tijdige betaling. G037 betreft een toezegging met een combinatie van uitval, periode en ontbreken van extra vergoeding. De toezeggingsreferent en drieledige reikwijdte zijn geen eenvoudige woordvervanging.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G038 — geautoriseerde publicatie

**Kern:** Publicatie die na toestemming van de eigenaar openbaar wordt gemaakt.

**Bedoeling:** De term kan in dit dossier zowel een soort publicatie als de uitvoeringsregel voor openbaarmaking aanduiden; de gebruiker heeft niet gekozen.

**Context:** organisatorische_context: Publicatieproef Magnolia (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** De catalogus gebruikt toestemming als kenmerk van de publicatie. Het publicatieprotocol gebruikt dezelfde omschrijving als opdracht aan de redactie. Geen van beide bronnen is als leidend aangewezen.

**A: review_required · aanpassen · zekerheid hoog.** De bijzin kan toestemming als kenmerk van de publicatie beschrijven of als opdracht aan de redactie functioneren. Geen van beide bronnen is leidend en de gebruiker heeft niet gekozen. Geen zelfstandig bewezen gebrek.

Vraag A: Is de catalogus (toestemming als kenmerk van de publicatie) of het publicatieprotocol (opdracht aan de redactie) de leidende grond voor deze kern?

Afstand A: zelfstandig; C30. Vereiste toestemming als kenmerk zoals C30, maar met bronconflict als bepalend element.

Aandachtspunten A: Vrijwel hetzelfde ontwerp als G003 (genus + passieve bijzin “na aanwijzing/toestemming … wordt …” + bron met twee lezingen); behoud er bij voorkeur één.

**B: review_required · aanpassen · zekerheid hoog.** De kern kan een soort publicatie beschrijven die na toestemming openbaar is gemaakt. B1 vermeldt daarnaast een protocol dat dezelfde omschrijving als opdracht aan de redactie gebruikt. Zonder leidende bron blijft onbeslist of de kern een kenmerk beschrijft of een uitvoeringsregel vormt.

Vraag B: Is toestemming hier bedoeld als kenmerk van de publicatie volgens de catalogus, of als voorwaarde waaronder de redactie volgens het protocol moet publiceren?

Afstand B: twijfel; C30, C24, C60. C30 en C24 bevatten al de grens tussen beschreven toestemming en uitvoerbare voorwaarden; C60 expliciete bronstrijd. G038 verplaatst het perspectief naar het gepubliceerde resultaat na toestemming, maar leunt sterk op dezelfde functiegrens plus conflictsjabloon.

Aandachtspunten B: B1 benoemt cataloguskenmerk, opdracht en ontbrekende voorrang expliciet; er zijn geen afzonderlijke catalogus- en protocolpassages. G003, G014 en G034 herhalen hetzelfde onbesliste categorie-/taakconflict met een voorafgaande autorisatie of handeling.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G039 — adviesprocedure

**Kern:** Samenhang van activiteiten waarmee een adviesvraag wordt ontvangen, onderzocht en van een gemotiveerd antwoord voorzien.

**Bedoeling:** Het begrip duidt een proces als geheel aan; deze inschrijving wijst geen uitvoerder aan of stappen toe.

**Context:** organisatorische_context: Procescatalogus Jeneverbes (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** De procescatalogus onderscheidt de adviesprocedure van haar werkinstructies. Het proces is herkenbaar aan ontvangst, onderzoek en een gemotiveerd advies.

**A: pass · bruikbaar · zekerheid hoog.** De kern beschrijft een proces als samenhang van activiteiten (ontvangst, onderzoek, gemotiveerd antwoord) zonder uitvoerder, opdracht of verplichting. Een procedure als begrip beschrijven is toegestaan; de bron onderscheidt de procedure van haar werkinstructies.

Afstand A: zelfstandig; C64. Geen nauw ontwerpgeval voor een procesbegrip zonder actor; C64 raakt alleen de grens met een procesvoorschrift.

Aandachtspunten A: Minimaal paar met G036 (proceslabel met actorvoorschrift). Familie-indeling: procesbegrip, bij normatief_begrip gezet vanwege de B1-zin over procedure als begripskenmerk.

**B: pass · aanpassen · zekerheid hoog.** De kern beschrijft het proces als samenhang van ontvangst, onderzoek en beantwoording. Zij wijst geen actor taken toe en voert geen beslissing over de uitvoering uit. B1 ondersteunt het onderscheid met werkinstructies. Een procedure als begrip beschrijven is toegestaan; het voorkomen van activiteiten alleen bewijst geen voorschrift.

Afstand B: zelfstandig; C15, C59. C15 bevat een behandelprocedure als definitie van een verzoek; C59 beschrijft een algoritme als begrip. G039 beschrijft het proces zelf via samenhangende activiteiten, zonder actoropdracht. Een uitgewerkte procesbeschrijving met deze referent ontbreekt in die twee ontwerpen.

Aandachtspunten B: Familie anders is hier beschrijvend procesbegrip; geen actorvoorschrift en geen normatief recht of plicht. Bedoeling ontkent het toewijzen van uitvoerder en stappen, en B1 scheidt werkinstructies af: sterke expliciete functiesturing. G036 vormt een inhoudelijk bruikbaar tegencontrast; proces als term beslist geen label.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.

### G040 — escalatiemelding

**Kern:** Melding die de coördinator naar eigen inzicht doorzet naar het bestuur wanneer hij de gevolgen ernstig genoeg vindt.

**Bedoeling:** De aangeleverde zin is bedoeld als regel voor het doorzetten van meldingen en wordt als definitie gebruikt.

**Context:** organisatorische_context: Meldproef Lijsterbes (fictief) · juridische_context: Synthetisch afsprakenmodel; geen claim over bestaand recht · wettelijke_basis: (leeg).

**Synthetische bron B1:** Het hoofdstuk geeft de coördinator opdracht per melding de ernst van de gevolgen te wegen en naar eigen inzicht te escaleren.

**A: fail · aanpassen · zekerheid hoog.** De bijzin voert een discretionaire afweging over handelen uit: doorzetten naar eigen inzicht wanneer de coördinator de gevolgen ernstig genoeg vindt. De bedoeling bevestigt dat de zin een regel voor doorzetten is; de bron noemt het een opdracht tot weging en escalatie. De melding zelf wordt niet afgebakend.

Afstand A: triviale_variant; C83. Zelfde raam als C83 (genus + actor + “naar eigen inzicht” + “wanneer hij … vindt/acht”), zelfde premisse en label.

Aandachtspunten A: Treft S1-marker “naar eigen inzicht”. Weinig onafhankelijk van C83; zwak als hold-out.

**B: fail · uitsluiten · zekerheid hoog.** De kern laat de coördinator meldingen doorzetten wanneer hij de gevolgen ernstig genoeg vindt. B1 bevestigt de opdracht per melding te wegen en naar eigen inzicht te escaleren. Daarmee functioneert de passage als discretionaire handelingsregel; de nominale opening Melding verandert die functie niet.

Afstand B: triviale_variant; C83. C83 betreft een maatregel die de rechter naar eigen inzicht oplegt wanneer hij dat redelijk acht. G040 vervangt object, actor en waardering door melding, coördinator en ernst van gevolgen en behoudt dezelfde syntaxis en beslisfunctie, inclusief naar eigen inzicht.

Aandachtspunten B: Voorstel tot uitsluiting als onafhankelijk geval wegens nagenoeg dezelfde inhoudelijke beslisstructuur als C83. Bedoeling zegt rechtstreeks dat het een regel voor doorzetten is; B1 bevestigt de opdracht nogmaals.

**Besluit Chris:** label — nog te beoordelen; geschiktheid — nog te beoordelen; eventuele correctie/onderbouwing — nog in te vullen.


