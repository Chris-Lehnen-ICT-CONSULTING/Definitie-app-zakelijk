# Vergelijking onafhankelijke herbeoordeling — v1

29 september 2026. Betreft kandidaatpool-v1 met SHA-256 `428b1d2e70895ed51484b919ad176f8fc50a4c717f8b877b5777e1c2aaf61128`. Dit is geen geaccepteerde goldset, splitsing of freeze.

## Controle en bronbinding

Beide CLI-sessies afgerond met exit 0, elk 27 gevallen. A: Claude Code CLI, sessie `16a630ad-b17a-4247-821f-e4a72a9c1e00`, model `claude-opus-5-5`. B: Codex CLI, sessie `01a0ed91-b6cb-73f2-948c-0cb76cb040b0`, `gpt-6-astra` met high. Hun prompts, ruwe uitvoer en logs staan in deze map. Beoordelaars hebben niet elkaars of de redacteurconclusies gekregen.

Alle IDs en vijf bronhashes kloppen. 154 citaten gecontroleerd. Eén einde-index bij A/G023 was één teken te kort; in A/labelvoorstellen-v2.json mechanisch van 110 naar 111 gecorrigeerd, zonder citaat, label of motivering te wijzigen. Ruwe A-v1 blijft behouden. Na deze correctie: 154/154 citaten exact op de opgegeven Unicode-posities.

Gebruikte resultaten: [A v2](beoordelaar-a/labelvoorstellen-v2.json), [B v1](beoordelaar-b/labelvoorstellen-v1.json), [controle](coordinatorcontrole-citaten-v1.json). De 13 ongewijzigde gevallen zijn alleen overlapcontext; bestaande beoordelingen zijn niet opnieuw uitgevoerd.

## Overzicht

20 van de 27 labels gelijk; 7 verschillen. Gelijke labels zijn geen automatisch akkoord op geschiktheid. Alle hieronder getoonde labels blijven voorstellen voor de kandidaatversie.

| ID | Begrip | A | B | Geschiktheid A / B |
|---|---|---|---|---|
| G001 | uitzonderingsroute | fail | fail | bruikbaar / uitsluiten |
| G002 | overnemende route | pass | pass | bruikbaar / bruikbaar |
| G003 | aangewezen referentie | review_required | review_required | bruikbaar / aanpassen |
| G005 | vrije bufferruimte | pass | pass | bruikbaar / bruikbaar |
| G006 | aanvaardbaar arrangement | review_required | pass | bruikbaar / aanpassen |
| G014 | voldoende herstel | review_required | pass | bruikbaar / bruikbaar |
| G016 | toelaatbare afwijking | fail | fail | bruikbaar / uitsluiten |
| G018 | herroepbare uitzondering | review_required | pass | bruikbaar / aanpassen |
| G021 | drempelbeslissing | pass | pass | bruikbaar / bruikbaar |
| G023 | getrapt meetinterval | pass | pass | bruikbaar / bruikbaar |
| G030 | actieve aanbieding | review_required | review_required | aanpassen / aanpassen |
| G033 | beoordelingsmarge | pass | pass | bruikbaar / bruikbaar |
| G035 | herbruikbare capsule | pass | pass | bruikbaar / bruikbaar |
| G036 | herstelronde | fail | fail | bruikbaar / bruikbaar |
| G039 | adviesprocedure | pass | pass | bruikbaar / bruikbaar |
| G041 | meldplichtige wijziging | pass | pass | bruikbaar / bruikbaar |
| G042 | afgeschermd proefvlak | pass | review_required | bruikbaar / bruikbaar |
| G043 | vervaltermijn | pass | pass | bruikbaar / bruikbaar |
| G044 | proefmonster | fail | fail | bruikbaar / bruikbaar |
| G045 | aanvullend stuk | fail | review_required | bruikbaar / bruikbaar |
| G046 | werkmandaat | pass | pass | bruikbaar / bruikbaar |
| G047 | afmelding | fail | review_required | bruikbaar / bruikbaar |
| G048 | tussentijdse meting | fail | fail | bruikbaar / bruikbaar |
| G049 | jaarverslag | fail | fail | bruikbaar / bruikbaar |
| G050 | servicetoeslag | fail | pass | bruikbaar / aanpassen |
| G051 | noodopvangplaats | fail | fail | bruikbaar / bruikbaar |
| G052 | voorrangsaanvraag | fail | fail | bruikbaar / bruikbaar |

## Labelverschillen, met oorspronkelijke motiveringen

### G006

**A — review_required:** De kern neemt het werkwoord en de voorwaarde over uit de aanvaardingsregel van art. 7 lid 2 (B2), waarin de commissie belangen afweegt. B1 geeft een constitutieve statuslezing. Onder B2 voert de kern een discretionaire afweging uit; onder B1 beschrijft zij een beslissing als kenmerk. De bedoeling noemt beide stukken zonder keuze.

**B — pass:** B1 geeft een concrete statusgrond: de vaststelling van een evenwichtige verdeling. B2 beschrijft de daarmee verbonden aanvaarding. De kern karakteriseert het arrangement via die aanvaarding en schrijft niet zelf een afwegingsprocedure voor. De twee passages kunnen naast elkaar gelden; een bronconflict volgt niet uit hun verschillende documentfuncties.

### G014

**A — review_required:** De passage past op beide stukken. B1 maakt de registratie constitutief voor de status. B2 geeft de inspecteur een gebonden opdracht om na de herinspectie te registreren. De gebruiker wil uitdrukkelijk niet kiezen. Onder B1 is de passage een beschreven kenmerk, onder B2 een overgenomen handelingsopdracht; de functie blijft onbeslist.

**B — pass:** B1 maakt registratie expliciet constitutief voor voldoende herstel. De kern beschrijft precies herstel met dat registratiekenmerk. B2 legt uit wanneer de inspecteur moet registreren, maar die deadline en opdracht staan niet in de kern. Een beschrijving van de status vergt hier geen keuze tegen de werkinstructie.

### G018

**A — review_required:** B2 is precies de discretionaire herroepingsregel die de kern verwoordt. B1 gebruikt bijna dezelfde woorden, maar als inhoud van een voorbehoud waaronder de uitzondering is verleend; dat is een classificatiekenmerk. De kern noemt het voorbehoud niet. De bedoeling noemt beide stukken als mogelijke grond. Kenmerkfunctie of beslisregelfunctie is onbeslist.

**B — pass:** B1 onderscheidt verleende uitzonderingen door het al dan niet geldende herroepingsvoorbehoud. De kern beschrijft de uitzondering via dat kenmerk. Zij draagt de toezichthouder geen periodieke beoordeling op. Dat B2 de uitoefening regelt, maakt het beschreven voorbehoud niet zelfstandig tot een uitvoeringsopdracht.

### G042

**A — pass:** Het proefvlak wordt afgebakend met een concreet, controleerbaar kenmerk (hekwerk van ten minste 1,20 m). De kern noemt geen actor en schrijft geen handeling voor. B2 gebruikt de term als kaartcategorie. B1 formuleert de afscherming als plicht voor proefvlakken onder ontheffing; ook in die lezing beschrijft de kern een kenmerk. Het weglaten van 'onder ontheffing' is een betekenisvraag buiten INT-02.

**B — review_required:** B1 staat tussen beheervoorschriften en draagt een afschermhandeling. B2 benoemt een kaartcategorie, maar zegt niet of een rode rand gerealiseerd hekwerk of een afschermopdracht aangeeft. De kern kan daardoor een fysieke klasse beschrijven of het voorschrift overnemen; kaartplaatsing alleen beslist dat niet.

### G045

**A — fail:** Het eerste deel bakent het stuk af. De bijzin neemt de indieningsregel uit art. 9 (B1) over. B2 laat zien dat 'is … te + infinitief' in deze regeling een voorschrift aan de aanvrager is. Niets in bedoeling of bronnen maakt de termijn tot kenmerk van een aanvullend stuk. Zonder actor en zonder signaalwoord blijft de passage een voorschrift.

**B — review_required:** B1 herhaalt de modale constructie zonder haar functie uit te werken. B2 gebruikt dezelfde constructie zowel bij ondertekening als bij de mogelijkheid bezwaar te maken. Daardoor ontbreekt specifieke grond om de kern als indieningsplicht of als toegestane aanvulling met termijnkenmerk te lezen.

### G047

**A — fail:** Het eerste deel bakent de melding af. De bijzin legt vast wie meldt en binnen welke termijn; dat komt letterlijk overeen met de meldregel in §8.2 (B1). Bedoeling (maandcijfers) en B2 maken melder of termijn niet tot kenmerk van een afmelding. De passage werkt als procedurevoorschrift in de kern.

**B — review_required:** De eerste zinshelft beschrijft de melding. B1 legt de coördinator een termijn op, terwijl B2 alleen een totaal aantal afmeldingen geeft. Nergens blijkt of te late meldingen onder dat begrip vallen. Daarom is niet onderbouwd of de relatieve bijzin een typekenmerk of een overgenomen uitvoeringsplicht is.

### G050

**A — fail:** Het eerste deel is een deterministische afleiding. De uitzondering laat het bedrag afhangen van wat de huurcommissie 'passend vindt'; B1 beschrijft dat als een discretionaire bevoegdheid. De kern voert daarmee een afweging over het rechtsgevolg uit als onderdeel van de begripsbepaling: een beslisregel in de zin van ASTRA.

**B — pass:** De kern beschrijft een bedrag en een uitzondering op het toepasselijke percentage. B1 en B2 verbinden die uitzondering aan een door de commissie vastgesteld percentage dat vervolgens in de afrekening wordt gebruikt. De kern draagt de commissie geen afweging op. Een constitutieve beslissing als parameter maakt de bedragomschrijving niet zelf tot een handelingsregel.

## Dispositie van concrete bronpunten

- G003: extra afzonderlijke registratie-/intrekkingsmomenten laten corrigeren; opnieuw gericht beoordelen.
- G006: statusgrond weer binden aan het oorspronkelijke reeds aanvaard zijn; geen automatisch bronconflict uit aanvullende documenten afleiden. Correctie en gerichte herbeoordeling volgen.
- G018: termijnverschuiving ‘de volgende dag’ tegenover ‘zodra’ laten corrigeren; geen nieuw label vooraf kiezen.
- G030: onnatuurlijke nominale definitiezin tussen imperatieven in instructiekaart laten herstellen binnen het bestaande scenario. Als dat geen overtuigende open functievraag oplevert, die beperking behouden en aan Chris voorleggen.
- G035: nieuwe synthetische proefparameters zijn door B expliciet gesignaleerd; beide beoordelaars noemen de INT-02-functie behouden en het geval bruikbaar. Parameters niet als oude bronfeiten presenteren; inhoudelijke acceptatie van deze versie staat open.
- G050: volgens B wijkt passend vinden af van een vastgesteld percentage met beperkte geldigheid. De reviewers verschillen ook inhoudelijk over pass/fail. Dit wordt als concreet beslispunt behandeld, niet stil geaccepteerd of tot automatisch fail gemaakt.

De redacteur corrigeert de eerste vier punten via opdracht-broncorrecties-claude-v1.md. Deze v1-vergelijking blijft aan de bestaande bronversie gebonden en wordt niet over nieuwe teksten heen toegepast.

## Selectie en familie

- G001 en G016: beide reviewers fail; A bruikbaar met twijfel over ontwerpafstand, B uitsluiten wegens geringe afstand tot C13/C83 en overlap. Nieuwe vervanging vraagt een expliciet selectiebesluit; het eerdere akkoord betrof herwerking. G001 is nu als eerste vraag aan Chris voorgelegd.
- G039: beiden pass; A normatief_begrip, B begripscriterium_afleiding. De redacteur stelt eveneens familie begripscriterium/afleiding voor. Familie nog niet vastgesteld.
- Overige overlap-/meerwaardepunten blijven in de oorspronkelijke resultaten en redactievoorstellen bewaard, waaronder G005/C27/C116, G023/C58, G012/G024 en de nieuwe paren G047/G049 en G042/G051. Een gedeelde familie is niet automatisch een triviale variant; concrete afweging per geval vereist.
- Na labelacceptatie opnieuw bezien of de afgesproken vier families en 24/16-verdeling haalbaar zijn. Geen labels naar een quotum sturen en geen protocolwijziging impliciet doorvoeren.

## Bewijsgrenzen

Dit is documentcontrole en vergelijking van twee modelvoorstellen. Chris accepteert de labels en selectie. Geen appmodelkwalificatie of effectmeting uitgevoerd, geen software/Git/Actions gewijzigd, O2 niet geactiveerd. Alle inhoud is synthetisch; geen verklaring over geldend recht. De benoemde modelovereenstemming bewijst geen normjuistheid of appkwaliteit.
