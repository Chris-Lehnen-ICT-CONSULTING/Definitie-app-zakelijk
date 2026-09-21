# ESS-01 — begripsafbakening en functiegrens

Vastgesteld door Chris op 16 september 2026 (DEF-746). Bron: [besluiten en uitvoering](https://linear.app/definitie-app/document/ess-01-vastgestelde-besluiten-en-uitvoeringsspecificatie-16-september-b9d7124c361e). ASTRA revisie 8543 bevat geen expliciete functie-uitzondering; de functiegrens is projectbeleid. Dit advies is geen opgeslagen review of vaststelling.

### N — normtekst volgens gebruikersbesluit

> De definitie bakent het begrip af binnen de vastgelegde betekenis. Een niet-begripsbepalend doel, gewenst effect, motief of gebruik hoort niet in de definitiekern: niet als vervanging van de afbakening, niet als extra vervolggebruik en ook niet als onderscheidend kenmerk naast een genus. Een functie, rol of gebruiksbestemming mag behouden blijven wanneer herleidbare domeininformatie aantoont dat zij het begrip mede bepaalt. Bij onvoldoende of strijdige grond blijft dit punt open voor inhoudelijke beoordeling. Woordkeuze of zinsvorm beslist het oordeel niet.

Dit functiecriterium is een expliciete projectkeuze, te registreren als operationalisering of gemotiveerde afwijking onder DEF-625. Overig doel als toelichtingsvoorstel aanbieden is een appkeuze, geen letterlijk ASTRA-voorschrift. Een inhoudelijk vastgestelde overtreding geeft voldoet niet, ook bij een gezaghebbende bron. Alleen werkelijke onzekerheid over betekenis of grond blijft open. Het oordeel start geen automatische wijziging of regeneratie. Een definitie van het begrip 'doel' wordt niet op de term afgekeurd.

## G — exacte generatie-instructie

> Beschrijf de kenmerken die het begrip binnen de gegeven betekenis afbakenen. Neem geen niet-begripsbepalend doel, gewenst effect, motief of incidenteel (vervolg)gebruik op in de definitiekern, ook niet als onderscheidend kenmerk naast een genus. Behoud een functie, rol of gebruiksbestemming uitsluitend wanneer de gegeven bron of expliciet bevestigde domeinafbakening onderbouwt dat die het begrip mede bepaalt. Een bestemming is niet hetzelfde als actuele werking: sluit een defect of ongebruikt exemplaar niet onbedoeld uit. Geef gebruikte grond en onzekerheid apart bij de kandidaat; een modelmotivering is geen menselijk bewijs. De app kan overig doel of gebruik als apart toelichtingsvoorstel aanbieden. Verander term en registratiecontext niet; volg voor de definitiekern het bestaande CON-01-beleid, inclusief noodzakelijke namen. Verzin geen bron, afbakening of beoordeling. Bij ontbrekende of strijdige informatie: maak dit zichtbaar en geef hoogstens een herkenbaar voorlopig voorstel.

Vooraf controleert de app beschikbaarheid en versie van term, bedoelde betekenis/context en relevante grond. Zij maakt ontbrekende gegevens zichtbaar, zonder alle ondersteunende velden verplicht te maken. De generator levert nooit een menselijke review of vaststelling.

## T — exacte menselijke toetsinstructie

> Beoordeel de ongewijzigde definitiekern op haar vastgelegde versie en bedoelde betekenis. Onderzoek alle relevante kenmerken, ongeacht doelwoorden of zinsvorm. Classificeer per passage: afbakening, begripsbepalende functie/rol/bestemming, overig doel/gebruik, of onduidelijk. Gebruik alleen herleidbare broninformatie of expliciet bevestigde domeingrond. Vraag als hulpmiddel: wanneer het gebruik of gewenste effect verandert, maar de overige kenmerken gelijk blijven, valt het onder dezelfde bedoelde begripsafbakening? Beoordeel daarbij de bestemming of rol op het juiste type-/exemplaarniveau; een defect instrument kan nog van hetzelfde type zijn. Deze vraag is een menselijke redeneerhulp, geen automatische test.
>
> Een bevestigde inhoudelijke tekortkoming geeft 'voldoet niet'; eventuele overige open punten blijven zichtbaar. Zonder bevestigde tekortkoming maar met relevante twijfel of ontbrekende grond: 'nog te beoordelen'. Alleen wanneer alle relevante passages en afbakeningsvragen voldoende beoordeeld zijn, zonder tekort of open punt: 'voldoet aan ESS-01'. Ontbrekende invoer, niet-uitgevoerde controle en technische fout zijn afzonderlijke uitkomsten. Geen regexsignaal betekent nooit automatisch voldoet. Noteer passage, grond en reden. Een voorstel voor betere tekst staat apart; toetsing verandert de invoer niet.

De app blijft zonder geldige menselijke beoordeling `review_required`. De menselijke beoordeling wordt alleen toegepast als zij uit de vertrouwde reviewvoorziening komt en bij de afhankelijke tekst, term, context, bron-/afbakening en normversie hoort. Een aanroepveld actor/pass is geen bewijs van bevoegdheid. De review levert geen ESS-cijfer op.

## H — exacte diagnose- en herstelinstructie

> Diagnoseer eerst de oorzaak met oorspronkelijke uitvoer, nabewerking en werkelijk getoetste kandidaat: inhoudelijke tekortkoming, conflicterende instructie, verlies van invoer/transport, foutpositief signaal, ontbrekend domeinbewijs of technische storing. Een fail beslist de oorzaak niet. Alleen bij een bevestigde herstelbare tekortkoming met voldoende grond mag maximaal één nieuwe kandidaat worden voorgesteld. Behoud begripsbepalende kenmerken, bronbetekenis, noodzakelijke namen, term en registratiecontext. Bewaar origineel, reden en diff. Verplaats uitsluitend aantoonbaar overig doel/gebruik naar een apart toelichtingsvoorstel. Alleen de grammatica wijzigen is geen inhoudelijk herstel. Verzin geen ontbrekende essentie of review. Stop bij onvoldoende bewijs, onopgeloste betekenisvragen, foutpositief, betekenisverlies, storing of geen verbetering. Brongezag is geen automatische vrijstelling; pas een bestaande definitie niet automatisch aan wegens een negatief oordeel. Toets de nieuwe kandidaat en geraakte buurregels opnieuw; bij onbekende afhankelijkheden alle toepasselijke controles. Oude beoordelingen mogen niet als goedkeuring van gewijzigde inhoud of grond gelden. Toon het resultaat als concept met resterende onzekerheden.

Herstelactivatie blijft afzonderlijke DEF-638-scope. Een signaal, open review of negatief oordeel start op zichzelf geen modelcall of tekstwijziging. Een herstelvoorstel vereist een afzonderlijke gebruikerskeuze. Bestaande inactieve code die een specifiek doel toevoegt (`definition_generator_enhancement.py:285–286`) mag niet als herstelbasis worden geactiveerd zonder deze contracttests.


## Toepassing en grensgevallen

- Toezicht: “systematisch volgen van handelingen om naleving van regels te waarborgen” is een grensgeval. Onderbouw of nalevingswaarborg de betekenis bepaalt of een gewenst effect is. Geen algemeen goed/fout-label.
- “In het kader van” blijft zichtbaar als beoordelingssignaal. Toon de echte passage met reden; een hit of ontbrekende hit bewijst geen voldoen of overtreding.
- Geen afzonderlijk verplicht ESS-01-akkoord of nieuwe ESS-01-vaststelblokkade. De expert stelt de definitie als geheel handmatig vast; negatieve/open bevindingen blijven zichtbaar. Vaststelling verandert geen regeloordelen in voldoet.
- De specifieke CON-01-blokkade bij ontbrekende context of onopgeloste naamfunctie blijft; bestaande CON-02-afspraken blijven gelden.
- ESS-01 krijgt geen numerieke bijdrage. Voorlopig geen totaalcijfer of vervangende deelscore (DEF-624). Toon oordeel, grond, dekking, open punten en technische fouten afzonderlijk.
- H is uitsluitend een latere instructie na afzonderlijke herstelopdracht, geen activatie. Zonder opdracht geen herschrijving, regeneratie of modelcall.
