# ESS-04 — exacte tekstvoorstellen, nog niet toegepast

18 september 2026 — v2, herziene Codex-teksten na kruisreview; voor synthesecontrole. Alleen toepassen na normbesluit en aparte uitvoeringsopdracht. Appvindplaatsen zijn in codebasis-4cdb8ea43/; actieve skillkopieën staan in feitenbasis/. Bestaande CON-01/02 en ESS-01/02 blijven behouden.

## N2: regelrecord ESS-04.json

Huidige uitleg: “Een definitie bevat objectief toetsbare elementen (harde deadlines, aantallen, percentages, meetbare criteria).” Probleem: cijfers domineren de instructie; losse voorbeeldfragmenten bewijzen geen volledige definitiekwaliteit. Exacte voorgestelde tekstwaarden:

**naam:** Toetsbaarheid.

**uitleg:** Ieder criterium in de definitie is binnen de bedoelde betekenis en context voldoende bepaald om navolgbaar te beoordelen of een geval eraan voldoet.

**toelichting:** Kwalitatieve criteria kunnen volstaan. Cijfers, percentages en termijnen zijn alleen behulpzaam als duidelijk is waarop zij betrekking hebben en hoe zij moeten worden toegepast. Leg meet- of beoordelingscontext vast wanneer die de uitkomst bepaalt; denk dan aan populatie of noemer, grensinclusie, referentietijd, dagconventie en toepasselijke bronversie. Verzin geen drempels of bewijs. Een onbekende uitkomst door ontbrekend gevalsbewijs is niet hetzelfde als een ontoetsbaar criterium. Een toepasbaar criterium kan nog steeds inhoudelijk onjuist of onvoldoende onderscheidend zijn; beoordeel die normdoelen afzonderlijk. Signalen en automatische controles vervangen geen inhoudelijke menselijke beoordeling.

**toetsvraag:** Zijn de begripskenmerken in de bedoelde context voldoende bepaald om hun toepasselijkheid op gevallen navolgbaar te beoordelen, en welke relevante criteria, interpretatie of bewijsgrond ontbreken nog?

**goede_voorbeelden:** “Veelhoek waarvan alle zijden even lang zijn.”; “Document waarop de afzender een handtekening heeft geplaatst.” Beide illustreren kwalitatieve criteria; het eerste betreft abstracte geometrie. Het tweede bewijst geen afzenderschap van een concrete krabbel. De kwantitatieve partijfixture blijft in het casusregister met fictieve bron F-P en wordt niet als algemeen productvoorschrift geïnstalleerd.

**foute_voorbeelden:** “Object dat minimaal 80% voldoet.” (criterium/noemer ontbreekt); “Aanvraag die zo snel mogelijk relevant wordt.” (geen afgebakend beoordelingscriterium in de opgegeven fixture).

**Grensvoorbeeld voor dossier/toelichting:** “Document waarop de afzender een handtekening heeft geplaatst.” Een zichtbare markering bewijst niet zelfstandig afzenderschap. Het criterium kan helder zijn terwijl gevalsbewijs ontbreekt.

Behouden: judgment_review en huidige ernst. Toekomstig menselijk reviewcontract expliciet scoreloos ontwerpen; no_score is kandidaat, met aantoonbaar aangesloten rule_results, transport en consumers. Geen huidige automatische scorelekclaim: review_required geeft null. Algemene DEF-630-reviewplicht geldt; ESS-04-eigen harde positieve poort blijft keuze. Actuele ASTRA-pagina is rechtstreeks gelezen (11 februari 2025 09:46, aangeboden oldid8558); oorspronkelijke Politie-bron en historische URL zijn niet gelezen. Bronregel en lokale uitwerking apart registreren. Exacte overige recordvoorstellen staan onderaan.

## G2: generatie-instructie

Vindplaats: src/services/prompts/modules/json_based_rules_module.py, _get_instruction_for_rule, ESS-04-entry. Huidig: “Gebruik objectief toetsbare elementen (deadlines, aantallen, percentages, meetbare criteria)”. Exacte vervanging:

> Beschrijf begripsbepalende kenmerken die in de bedoelde context navolgbaar op gevallen kunnen worden toegepast. Kwalitatieve criteria zijn toegestaan; voeg geen getal, percentage, termijn of registratienummer toe om toetsbaarheid te suggereren. Neem een kwantitatieve grens alleen over als de aangeleverde betekenisgrond haar ondersteunt en behoud relevante noemer, populatie, inclusie, startmoment en tijdsbasis, waaronder werk- of kalenderdagen wanneer dat onderscheidend is. Laat bepalende beperkingen in de definitiekern staan; methode, bewijsplaatsen en registratiecontext blijven apart. Bij ontbrekende of strijdige noodzakelijke grond: lever geen definitieve afbakening en verzin geen gegeven. Benoem de ontbrekende grond uitsluitend in een daarvoor bestemde aparte toelichting of verduidelijkingsuitkomst; voeg geen foutmelding, vraag of onzekere placeholder aan de definitiezin toe.

Appvoorwaarde: als de eindprompt alleen een definitiezin toelaat, kan deze instructie niet als losse vervanging worden uitgerold. De applicatie moet ontbrekende grond vooraf laten verduidelijken of een afzonderlijke niet-succesuitkomst ondersteunen. Een extra tekst naast de kandidaat lost een ontbrekend uitvoercontract niet vanzelf op. “Onvoldoende informatie” is geen definitie. Controleer volledige prompt en bronbudget bij implementatie; P03 is alleen een moduleproef. Cases N03/N06/N22/N23/N22.

## T2: toetsinstructie en reviewerhulp

Vindplaats: voorgesteld gedeeld ESS-04-referentieblok bij definitie-toetsregels; huidige reference.md:47 bevat alleen cijfergerichte tabelregel. Exacte tekst:

> Beoordeel de aangeleverde definitiekern ongewijzigd tegen ESS-04, ongeacht haar herkomst. Identificeer per relevant kenmerk het bedoelde object, de toepassingsvoorwaarde en de grond waarmee een geval kan worden beoordeeld. Beoordeel kwalitatieve criteria zonder cijferplicht. Controleer bij kwantitatieve criteria alleen de gegevens die de uitkomst bepalen: bijvoorbeeld noemer/populatie, eenheid, grensinclusie, referentietijd, termijnconventie en bronversie. Gebruik context, bronnen en aanvullingen als apart herkenbaar bewijs; voeg ze niet stil aan het toetsobject toe. Leg een vastgestelde tekortkoming, ontbrekend bewijs, een nog niet uitgevoerd menselijk oordeel en een technische fout afzonderlijk vast. Een getal, trefwoord of categorielabel bewijst geen naleving. Een toepasbaar maar verkeerd criterium vraagt een afzonderlijke bevinding over betekenis, bronsteun of onderscheidbaarheid. Vermeld tekst-/normversie, beoordeelde passage, reden en relevant tegen- of grensgeval. Tot daadwerkelijk menselijk oordeel blijft de appuitkomst voor ESS-04 ‘nog te beoordelen’; dit skilladvies registreert dat oordeel niet.

Cases: non_numeric/ambiguous_measure/observable/empty; N01/N07/N09/N24/N27/N21/N23.

## H2: terugkoppeling en begrensd herstel

Voorgestelde toevoeging aan hetzelfde referentieblok:

> Classificeer de oorzaak vóór herstel: generatieovertreding, tegenstrijdige instructies, invoer- of transportverlies, foutpositieve evaluator, ontbrekende bewijsgrond, technische fout of betekenisverlies door nabewerking. Een negatieve toets bewijst niet welke oorzaak geldt. Vergelijk waar relevant ruwe modeltekst, geëxtraheerde kern, opgeschoonde kandidaat, toetsinvoer en opgeslagen tekst met hun versies. Herstel alleen een vastgestelde fout waarvoor de beschikbare bron en bedoeling een betekenisbehoudende wijziging dragen. Houd origineel, voorstel, verschil en hertoetsing apart. Verzin geen getal, termijn, percentage, noemer, peildatum, grenswaarde, bron, context, actor of goedkeuring. Schrap een kwalificatie alleen in een afzonderlijk voorstel wanneer bevestigd is dat zij niet begripsbepalend is; een ruimer begrip is geen betekenisbehoudend herstel. Stop bij bronconflict, ontbrekende grond, betekenisverlies, herhaalde fout of uitgeputte toegestane poging. Uitsluitend toetsen verandert geen tekst. Automatische repair blijft afzonderlijk uitgesteld beleid onder DEF-638; als dat later wordt geactiveerd blijft het bestaande maximum één poging per generatie gelden. Geen totaalscore gebruiken als doel of trigger.

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

- Leeg: “ESS-04 — Niet beoordeelbaar: er is geen definitietekst om criteria in te beoordelen.”
- Open: “ESS-04 — Nog te beoordelen. Leg vast hoe het criterium ‘[passage]’ op een geval wordt toegepast.”
- Bekende fout: “ESS-04 — Voldoet niet. ‘80% voldoet’ vermeldt niet waarvan het percentage wordt berekend en aan welk criterium wordt voldaan.”
- Ontbrekend gevalsbewijs: “Het criterium is beschreven; voor dit geval ontbreekt het meet- of beoordelingsbewijs. Daardoor is de toepassing op dit geval nog onbekend.”
- Bronconflict: “De bronnen hanteren verschillende grenzen. Kies eerst de toepasselijke betekenisgrond; de definitie is niet automatisch aangepast.”
- Technische fout: “De beoordeling kon niet worden uitgevoerd. Er is geen inhoudelijk oordeel toegevoegd.”
- Verouderd oordeel: “Deze beoordeling hoort bij een eerdere tekst, context, bron of norm. Beoordeel de gewijzigde versie opnieuw.”

Gebruik concrete passage/reden in de UI. De passagevariabele is een meldingssjabloon, geen ingevuld casusbewijs.


## Aanvullende recordvelden en expliciete patroonkeuze

**thema:** `essentie van het begrip` (herkomstcorrectie tegenover huidig `toepasbaarheid`). **relatie:** voeg het object met `fulltext: Instanties uniek onderscheidbaar` en `fullurl: https://www.astraonline.nl/index.php/Instanties_uniek_onderscheidbaar` toe. De bestaande zelfverwijzing is bronverwijzing, geen tweede normrelatie; migreer die pas als de veldsemantiek is vastgelegd. **bronvermelding:** ASTRA-pagina Toetsbaarheid als geraadpleegde publicatie; `verwijzing: Politie` als door ASTRA genoemde herkomst, niet als zelfstandig gelezen bron. Andere metadata blijven behouden tenzij expliciete vergelijking een correctie draagt.

**example_pair_reason — exacte vervanging:** “Het toepassen van dit criterium vraagt beoordeling van de bedoelde betekenis en de relevante grond. Woorden, getallen en signaalpatronen leveren geen bewijs van voldoen of niet voldoen; ook zonder treffer blijft menselijke beoordeling nodig.” `example_pair_policy: review_policy` blijft passend bij die structurele grond.

**Patroonoptie A (voorkeur):** neutrale, gemengde aandachtssignalen voor mogelijke onbepaaldheid én kwantitatieve grenzen; geen positieve/negatieve automatische uitkomst. Gebruik Coworks concrete §6.1-lijst als kandidaat, met beide voorwaarden hieronder. Dit is een te kalibreren ontwerp, geen gevalideerde set. Generieke `bevat`, `omvat`, `is gedefinieerd als`, `is vastgesteld als` en `toetsbaar` vervallen als zelfstandige kwaliteitsaanwijzing. Een overlappend woord zoals `voldoende` mag onder twee normdoelen aandacht vragen; voorkom dubbele afkeur via oordeel/motivering, niet via blind uitsluiten van signalen. De definitieve keuze over dat woord is implementatiedetail na corpuscontrole, geen nieuw normbesluit.

**Patroonoptie B:** bestaande richting voorlopig behouden en alleen de zes defecte patronen corrigeren. Vervang de vier percentagevormen door de equivalente vorm met optionele ruimte, decimalen en `(?![\w%])` na `%` in plaats van `\b`; vervang `dagen?` door `(?:dag|dagen)` en `weken?` door `(?:week|weken)`. Dit repareert vormdekking, niet het gebrek aan semantische bewijskracht; getalwoorden en bedoelde open normen blijven menselijke beoordeling vragen.

**Patroonoptie C:** geen regexpassages tonen totdat een nuttige set is gekalibreerd; vaste criteriumvraag blijft altijd zichtbaar. Minder ruis, minder gerichte hulp. Geen automatische pass bij nul signalen.

Voor A/B vooraf menselijke annotatie van wat een nuttige aandachtspassage is, niet alleen wat een goede definitie is. Test percentages met/zonder spatie/decimalen, enkelvoud/meervoud, letters, werkdag, onbedoelde woordaanhechting en bedoelde open normen. De veertien bestaande proeven testen uitsluitend de huidige set; ze valideren geen nieuw patroonontwerp.

## Menselijke uitkomsten — exact voorgesteld contract in taal

- **Voldoet:** de reviewer onderbouwt dat ieder relevant criterium in de bedoelde context navolgbaar toepasbaar is. Dit zegt niets zelfstandig over waarheid, volledigheid, gevalslidmaatschap of formele vaststelling.
- **Voldoet niet:** een concrete criteriumtekortkoming is vastgesteld, met passage en reden. Bekende tekortkoming kan naast andere open vragen bestaan.
- **Nog te beoordelen:** menselijk oordeel ontbreekt, of noodzakelijke betekenis-/toepassingsgrond laat nog geen verantwoord definitieoordeel toe. Benoem welke van beide redenen geldt.
- **Gevalsbewijs ontbreekt:** het criterium kan voldoende zijn; de toepassing op dit specifieke geval blijft onbekend. Geen automatische negatieve of positieve ESS-04-status afleiden.
- **Niet beoordeelbaar / technisch probleem:** respectievelijk ontbrekend toetsobject en niet geslaagde uitvoering. Apart houden van inhoudelijk fail.

Deze menselijke taaluitkomsten mogen in de implementatie een expliciete mapping krijgen; een UI-label alleen is geen opgeslagen review. Beoordeling bindt aan tekst, term, context, relevante bronnen, norm, actor/rol en tijd. Algemene expertbeoordeling en handmatige vaststelling blijven; geen AI-jury of verplichte tweede goedkeurder geïntroduceerd.
