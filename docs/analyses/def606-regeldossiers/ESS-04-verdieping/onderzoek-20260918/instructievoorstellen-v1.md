# ESS-04 — exacte tekstvoorstellen, nog niet toegepast

18 september 2026. Alleen toepassen na normbesluit en aparte uitvoeringsopdracht. Appvindplaatsen zijn in codebasis-4cdb8ea43/; actieve skillkopieën staan in feitenbasis/. Bestaande CON-01/02 en ESS-01/02 blijven behouden.

## N1: regelrecord ESS-04.json

Huidige uitleg: “Een definitie bevat objectief toetsbare elementen (harde deadlines, aantallen, percentages, meetbare criteria).” Probleem: cijfers domineren de instructie; losse voorbeeldfragmenten bewijzen geen volledige definitiekwaliteit. Exacte voorgestelde tekstwaarden:

**naam:** Toetsbaarheid.

**uitleg:** De definitie beschrijft kenmerken waarmee binnen de bedoelde betekenis en context navolgbaar kan worden beoordeeld of een geval onder het begrip valt.

**toelichting:** Kwalitatieve criteria kunnen volstaan. Cijfers, percentages en termijnen zijn alleen behulpzaam als duidelijk is waarop zij betrekking hebben en hoe zij moeten worden toegepast. Leg meet- of beoordelingscontext vast wanneer die de uitkomst bepaalt; denk dan aan populatie of noemer, grensinclusie, referentietijd, dagconventie en toepasselijke bronversie. Verzin geen drempels of bewijs. Een onbekende uitkomst door ontbrekend gevalsbewijs is niet hetzelfde als een ontoetsbaar criterium. Een toepasbaar criterium kan nog steeds inhoudelijk onjuist of onvoldoende onderscheidend zijn; beoordeel die normdoelen afzonderlijk. Signalen en automatische controles vervangen geen inhoudelijke menselijke beoordeling.

**toetsvraag:** Zijn de begripskenmerken in de bedoelde context voldoende bepaald om hun toepasselijkheid op gevallen navolgbaar te beoordelen, en welke relevante criteria, interpretatie of bewijsgrond ontbreken nog?

**goede_voorbeelden:** “Speelkaart waarvan de achterzijde blauw is.” (synthetische kaartset met vastgelegde kleurindeling); “Partij waarvan minimaal 80% van alle op 18 september 2026 ontvangen exemplaren onbeschadigd is.” (uitsluitend fictieve bron F-P uit casusregister, geen willekeurig 80%-advies).

**foute_voorbeelden:** “Object dat minimaal 80% voldoet.” (criterium/noemer ontbreekt); “Aanvraag die zo snel mogelijk relevant wordt.” (geen afgebakend beoordelingscriterium in de opgegeven fixture).

**Grensvoorbeeld voor dossier/toelichting:** “Document waarop de afzender een handtekening heeft geplaatst.” Een zichtbare markering bewijst niet zelfstandig afzenderschap. Het criterium kan helder zijn terwijl gevalsbewijs ontbreekt.

Behouden totdat afzonderlijk besloten: judgment_review, excluded_from_score en huidige ernst. Geen wijziging naar no_score of zelfstandige poort impliciet afleiden. Bronherkomst bevat straks de exact geverifieerde ASTRA-revisie plus lokale uitwerking; actuele ASTRA-tekst ontbreekt nu, dus niet reconstrueren.

## G1: generatie-instructie

Vindplaats: src/services/prompts/modules/json_based_rules_module.py, _get_instruction_for_rule, ESS-04-entry. Huidig: “Gebruik objectief toetsbare elementen (deadlines, aantallen, percentages, meetbare criteria)”. Exacte vervanging:

> Beschrijf begripsbepalende kenmerken die in de bedoelde context navolgbaar op gevallen kunnen worden toegepast. Kwalitatieve criteria zijn toegestaan; voeg geen getal, percentage, termijn of registratienummer toe om toetsbaarheid te suggereren. Neem een kwantitatieve grens alleen over als de aangeleverde betekenisgrond haar ondersteunt en behoud relevante noemer, populatie, inclusie en tijdsbasis. Laat bepalende beperkingen in de definitiekern staan; methode, bewijsplaatsen en registratiecontext blijven apart. Bij ontbrekende of strijdige noodzakelijke grond: vraag via de beschikbare verduidelijkingsroute om die grond en lever geen verzonnen afbakening.

Appvoorwaarde: als de eindprompt alleen een definitiezin toelaat, moet verduidelijking buiten dat uitvoerveld een ondersteunde route hebben. “Onvoldoende informatie” is geen definitie. Controleer volledige prompt en bronbudget bij implementatie; P03 is alleen een moduleproef. Cases N03/N06/N12/N13/N22.

## T1: toetsinstructie en reviewerhulp

Vindplaats: voorgesteld gedeeld ESS-04-referentieblok bij definitie-toetsregels; huidige reference.md:47 bevat alleen cijfergerichte tabelregel. Exacte tekst:

> Beoordeel de aangeleverde definitiekern ongewijzigd tegen ESS-04, ongeacht haar herkomst. Identificeer per relevant kenmerk het bedoelde object, de toepassingsvoorwaarde en de grond waarmee een geval kan worden beoordeeld. Beoordeel kwalitatieve criteria zonder cijferplicht. Controleer bij kwantitatieve criteria alleen de gegevens die de uitkomst bepalen: bijvoorbeeld noemer/populatie, eenheid, grensinclusie, referentietijd, termijnconventie en bronversie. Gebruik context, bronnen en aanvullingen als apart herkenbaar bewijs; voeg ze niet stil aan het toetsobject toe. Leg een vastgestelde tekortkoming, ontbrekend bewijs, een nog niet uitgevoerd menselijk oordeel en een technische fout afzonderlijk vast. Een getal, trefwoord of categorielabel bewijst geen naleving. Een toepasbaar maar verkeerd criterium vraagt een afzonderlijke bevinding over betekenis, bronsteun of onderscheidbaarheid. Vermeld tekst-/normversie, beoordeelde passage, reden en relevant tegen- of grensgeval. Tot daadwerkelijk menselijk oordeel blijft de appuitkomst voor ESS-04 ‘nog te beoordelen’; dit skilladvies registreert dat oordeel niet.

Cases: non_numeric/ambiguous_measure/observable/empty; N01/N07/N09/N14/N17/N21/N23.

## H1: terugkoppeling en begrensd herstel

Voorgestelde toevoeging aan hetzelfde referentieblok:

> Classificeer de oorzaak vóór herstel: generatieovertreding, tegenstrijdige instructies, invoer- of transportverlies, foutpositieve evaluator, ontbrekende bewijsgrond, technische fout of betekenisverlies door nabewerking. Een negatieve toets bewijst niet welke oorzaak geldt. Vergelijk waar relevant ruwe modeltekst, geëxtraheerde kern, opgeschoonde kandidaat, toetsinvoer en opgeslagen tekst met hun versies. Herstel alleen een vastgestelde fout waarvoor de beschikbare bron en bedoeling een betekenisbehoudende wijziging dragen. Houd origineel, voorstel, verschil en hertoetsing apart. Verzin geen drempel, bron, context, actor of goedkeuring. Stop bij bronconflict, ontbrekende grond, betekenisverlies, herhaalde fout of uitgeputte toegestane poging. Uitsluitend toetsen verandert geen tekst. Automatische repair blijft afzonderlijk uitgesteld beleid onder DEF-638; als dat later wordt geactiveerd blijft het bestaande maximum één poging per generatie gelden. Geen totaalscore gebruiken als doel of trigger.

## Exacte skillwijzigingen

Alle onderstaande paden vallen onder /Users/chrislehnen/.agents/skills/. Dit zijn voorstellen; geen actieve bestanden aangepast.

1. **definitie-toetsregels/reference.md:47**, vervang de ESS-04-tabelrij door de volgende vier celwaarden: **ESS-04**; **Toetsbaarheid van begripskenmerken**; **midden**; **Beschrijf navolgbaar toepasbare criteria; kwalitatief waar passend, kwantitatief alleen met onderbouwde grens en relevante meetcontext. Signalen vervangen geen menselijke beoordeling.** Cases N01/03/05/06.

2. **definitie-toetsregels/SKILL.md**, voeg na ESS-02 toe: **ESS-04 — Toetsbaarheid. Gebruik het versiegebonden ESS-04-contract N/G/T/H. Kwalitatieve criteria kunnen volstaan; getallen en signalen bewijzen geen toetsbaarheid. Ontbrekend gevalsbewijs is niet automatisch een definitiefout. Behoud origineel en betekenis; menselijke review blijft nodig, zonder fictieve registratie door de skill.** Voeg bij uitvoering de werkelijk meeverpakte relatieve referentielink toe. Alle cases.

3. **definitie-nederlandse-definities/reference.md**, na “Eisen aan de Differentia”, voeg toe: **Toetsbaarheid (ESS-04): formuleer elk begripsbepalend kenmerk zo dat toepassing op een geval navolgbaar is. Kwalitatieve relaties of eigenschappen kunnen volstaan. Verzin geen cijfers of grenzen; behoud relevante bronbeperkingen en vraag ontbrekende betekenisgrond via de verduidelijkingsroute. Toetsbaarheid bewijst niet dat het kenmerk noodzakelijk of voldoende onderscheidend is.** Cases non_numeric, N03/14/18.

4. **definitie-voorbeelden-generatie/reference.md**, vervang onder “Intensie-extensie-afstemming” het blok “De definitie is correct als” en “Als een voorbeeld niet klopt” door: **Voorbeelden toetsen de toepasbaarheid van kenmerken; een eindige verzameling bewijst geen volledige juistheid. Label verwachte lidmaatschappen vooraf met onafhankelijke betekenisgrond. Positieve gevallen voldoen aan de relevante gezamenlijke criteria; tegenvoorbeelden vallen op een aantoonbaar criterium buiten het begrip. Neem grensgevallen precies op en, waar zinvol, aan beide zijden van een grens. Ook een eenduidig beslisbaar geval op de grens is een grensgeval. Onderscheid ontbrekend gevalsbewijs, verschil in criteriumbetekenis en verschil in beoordeling. Gegenereerde voorbeelden en twee eensluidende AI-antwoorden zijn geen onafhankelijke expertlabels.** Hiermee vervallen ook de onzuivere intensie/extensie-subsetnotatie en “geen discussie → geen grensgeval”. Cases N06/07/15/16/17.

5. **definitie-ontologisch-modelleren/reference.md**, na “Stap 4: Relaties Modelleren”, voeg toe: **Gebruik relaties voor ESS-04 om vast te leggen van welk object een kenmerk is, waarop een telling slaat en welke relatie voor lidmaatschap relevant is. Houd instantie-identiteit (ESS-03), toepasbaarheid van criteria (ESS-04) en onderscheid tussen begrippen (ESS-05) apart. Een registratiesleutel of gemeten toevallige eigenschap vervangt geen begripsbepalend kenmerk. Modelleer homoniemen betekenisgebonden, zonder criterium van het ene begrip naar het andere over te dragen.** Cases N08/14/19.

6. **definitie-ufo-ontologie/SKILL.md**, na ESS-02, voeg toe: **Bij ESS-04 helpt de ontologische duiding bepalen waarop het criterium betrekking heeft. Zij geeft geen zelfstandig bewijs van toetsbaarheid: beoordeel kenmerk, object en relevante bewijsgrond. Behoud de vastgestelde scheiding van betekenisniveau en aard; forceer een kwalitatief criterium niet tot een getal of een exclusief categorielabel.** Cases N05/14/19.

Het gedeelde N/G/T/H-document kan bij uitvoering references/ess04-toetsbaarheid.md worden, met dezelfde meeverpakte versie in betrokken skills. Geen verwijzing naar een niet-bestaand bestand installeren. Bestaande normteksten van buurregels niet vervangen.

**Bestaande appbrede besluitcorrectie, geen nieuw ESS-04-beleid:** vervang in toetsregels SKILL.md §Scoring & Weging en de CON-01-scorealinea de formuleringen over tijdelijk/voorlopig geen totaalcijfer door: **De totaalscore is appbreed vervallen als kwaliteitscijfer, acceptatiegrond en hersteldriver (besluit 15 september 2026). Toon afzonderlijke oordelen, uitvoeringsdekking, benodigde acties en actuele expertbeoordeling. Historische gewichten en technische scores geven geen zelfstandige beslissingsbevoegdheid. Individuele ernst, scorepolicy en vervolgvoorwaarden blijven afzonderlijk bepaald.** Algemene migratie onder DEF-624/630; geen andere regelrecords stil herschrijven.

## Gebruikersmeldingen

- Open: “ESS-04 — Nog te beoordelen. Leg vast hoe het criterium ‘[passage]’ op een geval wordt toegepast.”
- Bekende fout: “ESS-04 — Voldoet niet. ‘80% voldoet’ vermeldt niet waarvan het percentage wordt berekend en aan welk criterium wordt voldaan.”
- Ontbrekend gevalsbewijs: “Het criterium is beschreven; voor dit geval ontbreekt het meet- of beoordelingsbewijs. Daardoor is de toepassing op dit geval nog onbekend.”
- Bronconflict: “De bronnen hanteren verschillende grenzen. Kies eerst de toepasselijke betekenisgrond; de definitie is niet automatisch aangepast.”
- Technische fout: “De beoordeling kon niet worden uitgevoerd. Er is geen inhoudelijk oordeel toegevoegd.”
- Verouderd oordeel: “Deze beoordeling hoort bij een eerdere tekst, context, bron of norm. Beoordeel de gewijzigde versie opnieuw.”

Gebruik concrete passage/reden in de UI. De passagevariabele is een meldingssjabloon, geen ingevuld casusbewijs.
