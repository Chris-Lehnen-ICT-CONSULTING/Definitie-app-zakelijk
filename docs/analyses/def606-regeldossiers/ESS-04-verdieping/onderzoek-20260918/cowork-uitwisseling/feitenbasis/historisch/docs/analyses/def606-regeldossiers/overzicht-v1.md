# DEF-606 — overzicht van 53 regeldossiers

11 september 2026 · onderzoeksdossiers gereed voor gezamenlijke bespreking.

**Volgende fase: Chris en Codex bespreken één toetsregel tegelijk.** Begin voorgesteld met [CON-01](CON-01-v1.md). Er is geen implementatie gestart of normvoorstel automatisch goedgekeurd.

Lees [plan v4](../../plans/2026-09-11-def606-analyseplan-v4.md) voor de schone sessie en [samenhang](samenhang-v1.md) voor de gedeelde beslispunten. De onderstaande links wijzen de nieuwste dossier-versies aan; hun 14 onderdelen bevatten context, definitiebronnen, ontologie, aanvullende informatie, appgedrag, skills, proeven en wederzijdse Claude/Codex-review.

Alle 53 hebben bespreekstatus **nog met Chris te bespreken**. Bestaande eerder vastgelegde besluiten blijven geldig waar het dossier ze expliciet aanwijst. Het overzicht is een vindlijst, geen bulkvolgorde.

| Regel en dossier | Lokale regelnaam | Belangrijkste bespreekpunt |
|---|---|---|
| [ARAI-01](ARAI-01-v1.md) | geen werkwoord als kern (vervoegd werkwoord) | Beperkte werkwoordlijst mist vervoegde kernen; nominale procesinhoud afzonderlijk houden. |
| [ARAI-02](ARAI-02-v1.md) | Vermijd vage containerbegrippen | Vage woorden en concreet genus worden verward; toepasselijkheidsvoorwaarde ontbreekt. |
| [ARAI-02SUB1](ARAI-02SUB1-v1.md) | Lexicale containerbegrippen vermijden | Containerwoord kan vakterm zijn; lijst mist andere vaagheid. |
| [ARAI-02SUB2](ARAI-02SUB2-v1.md) | Ambtelijke containerbegrippen vermijden | Proces/activiteit worden ook met concrete toespitsing afgekeurd. |
| [ARAI-03](ARAI-03-v1.md) | Beperk gebruik van bijvoeglijke naamwoorden | Essentieel adjectief tegenover subjectief oordeel; nog inhoudelijke review. |
| [ARAI-04](ARAI-04-v1.md) | Vermijd modale hulpwerkwoorden | Modaliteit, capaciteit en zelfs zelfstandig naamwoord kan onderscheiden. |
| [ARAI-04SUB1](ARAI-04SUB1-v1.md) | Beperk gebruik van modale werkwoorden | Overlap met hoofdregel; modaliteit en criterium niet blind verbieden. |
| [ARAI-05](ARAI-05-v2.md) | Vermijd impliciete aannames | Expliciete verwijzingen geraakt, verborgen voorkennis gemist. |
| [ARAI-06](ARAI-06-v1.md) | Correcte definitiestart: geen lidwoord, geen koppelwerkwoord, geen herhaling begrip | Generatiestijl versus uitsluitend toetsen; indirect effect via STR-01. |
| [CON-01](CON-01-v1.md) | Eigen definitie voor elke context. Contextspecifieke formulering zonder expliciete benoeming | Contextminimum, gekozen labels en doorgifte worden niet volledig gecontroleerd. |
| [CON-02](CON-02-v1.md) | Baseren op authentieke bron | Bronwoorden bewijzen geen authentieke of ondersteunende definitiebron. |
| [CON-CIRC-001](CON-CIRC-001-v1.md) | Geen circulaire definitie | Letterlijke herhaling is geen volledige semantische cirkelcontrole. |
| [DUP_01](DUP_01-v1.md) | Geen duplicaat definities in database | Term/context/categorie en eigen record; andere formulering voorkomt duplicaat niet. |
| [ESS-01](ESS-01-v1.md) | Essentie, niet doel | Essentie versus doel vraagt functiebeleid en inhoudelijk oordeel. |
| [ESS-02](ESS-02-v1.md) | Ontologische categorie expliciteren (type / particulier / proces / resultaat) | Marker kan tekstcontrole omzeilen; lokale categorieën en hoofdreferent onderscheiden. |
| [ESS-03](ESS-03-v1.md) | Instanties uniek onderscheidbaar (telbaarheid) | Telbaarheid/identiteit wordt niet bewezen door een nummer of specifiek. |
| [ESS-04](ESS-04-v1.md) | Toetsbaarheid | Toetsbaarheid vraagt criteria, referentie en beoordelingsprocedure. |
| [ESS-05](ESS-05-v1.md) | Voldoende onderscheidend | Onderscheidende kenmerken worden niet betrouwbaar door positieve woorden herkend. |
| [ESS-CONT-001](ESS-CONT-001-v1.md) | Essentiële inhoud aanwezig | Zes tokens meten hoeveelheid, niet essentiële inhoud. |
| [INT-01](INT-01-v2.md) | Compacte en begrijpelijke zin | Bijzinnen/afkortingen kunnen foutief afkeuren; compactheid is geen patroonlijst. |
| [INT-02](INT-02-v1.md) | Geen beslisregel | Begripscriterium tegenover voorschrift of procedure beoordelen. |
| [INT-03](INT-03-v1.md) | Voornaamwoord-verwijzing duidelijk | Antecedent en verwijzingsbereik vereisen inhoudelijke review. |
| [INT-04](INT-04-v1.md) | Lidwoord-verwijzing duidelijk | Vaste lidwoordcombinaties treffen ook duidelijke verwijzingen. |
| [INT-06](INT-06-v1.md) | Definitie bevat geen toelichting | Kern en toelichting onderscheiden zonder noodzakelijke kenmerken te verplaatsen. |
| [INT-07](INT-07-v1.md) | Alleen toegankelijke afkortingen | Afkortingsdetectie bewijst toegankelijkheid niet; uitgelegde afkorting kan falen. |
| [INT-08](INT-08-v1.md) | Positieve formulering | Toegestane beperkende ontkenning wordt niet consequent gerespecteerd. |
| [INT-09](INT-09-v1.md) | Opsomming in extensionele definitie is limitatief | Volledigheid van een opsomming is geen zoals-detector. |
| [INT-10](INT-10-v1.md) | Geen ontoegankelijke achtergrondkennis nodig | Brongezag en toegankelijkheid voor doelgroep zijn afzonderlijke vragen. |
| [SAM-01](SAM-01-v1.md) | Kwalificatie leidt niet tot afwijking | Repository aanwezig leidt tot review, niet tot uitgevoerde betekenisvergelijking. |
| [SAM-02](SAM-02-v2.md) | Kwalificatie omvat geen herhaling | Woord/labelpatronen bewijzen geen redundantie ten opzichte van hoofdbegrip. |
| [SAM-03](SAM-03-v1.md) | Definitieteksten niet nesten | Nesting blijft niet beoordeeld, ook met een echte verse repository. |
| [SAM-04](SAM-04-v1.md) | Begrip-samenstelling strijdt niet met samenstellende begrippen | Woordcomponent/colonheuristiek bewijst geen semantische consistentie. |
| [SAM-05](SAM-05-v1.md) | Geen cirkeldefinities | Directe herhaling en echte definitiecycli onderscheiden; evaluator uitgesteld. |
| [SAM-06](SAM-06-v2.md) | Één synoniem krijgt voorkeur | Expliciete voorkeur, synoniemen, taal en concept; invoergate en keuzecontrole ontbreken deels. |
| [SAM-07](SAM-07-v1.md) | Geen betekenisverruiming binnen definitie | Extra-substring kan extractie raken; betekenisverruiming zonder marker gemist. |
| [SAM-08](SAM-08-v1.md) | Synoniemen hebben één definitie | Gedeelde betekenis/definitie voor synoniemen wordt nog niet gecontroleerd. |
| [STR-01](STR-01-v1.md) | definitie start met zelfstandig naamwoord | Nominale groep, juist genus en lidwoordstijl worden door elkaar geraakt. |
| [STR-02](STR-02-v1.md) | Kick-off ≠ de term | Bovenbegrip nauwelijks gecontroleerd; labelvorm en eindwoord sturen uitslag. |
| [STR-03](STR-03-v1.md) | Definitie ≠ synoniem | Synoniemvervanging tegenover echte inhoud; terecht nog semantische review. |
| [STR-04](STR-04-v1.md) | Kick-off vervolgen met toespitsing | Afgebroken Proces dat passeert; toespitsing niet inhoudelijk bewezen. |
| [STR-05](STR-05-v1.md) | Definitie ≠ constructie | Alleen onderdelen versus constitutieve samenstelling; geen algemeen onderdelenverbod. |
| [STR-06](STR-06-v1.md) | Essentie ≠ informatiebehoefte | Functie, bedoeling en gebruikersbehoefte; herschrijving kan betekenis veranderen. |
| [STR-07](STR-07-v1.md) | Geen dubbele ontkenning | Graniet zonder triggert; negatiescope en morfologie ontbreken. |
| [STR-08](STR-08-v1.md) | Dubbelzinnige 'en' is verboden | Cumulatie, alternatief, collectiviteit en naamgebruik onderscheiden. |
| [STR-09](STR-09-v1.md) | Dubbelzinnige 'of' is verboden | Inclusief/exclusief, fallback, synoniem en vraagfunctie onderscheiden. |
| [STR-ORG-001](STR-ORG-001-v1.md) | Zinsstructuur en redundantie | 300-tekengrens en simpel/complex zijn geen semantische redundantiecontrole. |
| [STR-TERM-001](STR-TERM-001-v1.md) | Consistente terminologie (koppelteken) | Alleen exacte frase HTTP protocol; geen algemene spellingcontrole. |
| [VAL-EMP-001](VAL-EMP-001-v2.md) | Lege definitie is ongeldig | Gewone leegte faalt; onzichtbare U+200B/BOM kunnen passeren. |
| [VAL-LEN-001](VAL-LEN-001-v1.md) | Minimale lengte (woorden/tekens) | Minimum 5 tokens/15 tekens kan inhoud afkeuren en opvulling toelaten. |
| [VAL-LEN-002](VAL-LEN-002-v1.md) | Maximale lengte (woorden/tekens) | Maximum 80 tokens/600 codepoints; telcontract en betekenisbehoud expliciteren. |
| [VER-01](VER-01-v1.md) | Term in enkelvoud | Woordsoort en pluralia tantum vóór suffixcontrole bepalen. |
| [VER-02](VER-02-v1.md) | Definitie in enkelvoud | Enkelvoudige hoofdformulering niet verwarren met meervoudige onderdelen. |
| [VER-03](VER-03-v1.md) | Werkwoord-term in infinitief | Besluit/beleid zijn geen vervoegd werkwoord; toepasselijkheid ontbreekt. |

## Bewijs en leeswijzer

- Per dossier: onderdeel 11 wijst naar eigen invoer/uitkomsten; onderdeel 13 naar ruwe Claude-review en Codex-oordeel. Voorgestelde acceptatiegevallen zijn geen al uitgevoerde UI-tests.
- [Eindcontrole](eindcontrole-v1.json): 53 dossiers, elk onderdelen 1–14, lokale dossierlinks en bronbinding gecontroleerd; manager/cache-resultaten gelijk. Geen semantische goedkeuring.
- Vijf gecorrigeerde tweede versies zijn leidend: ARAI-05, INT-01, SAM-02, SAM-06 en VAL-EMP-001. Oude versies en eerdere proefpogingen blijven behouden.
- Onderzoekscommit: `d68a98a909630e15db6e1cb9c9c8171f957bff9d`. Tijdelijke clone: `/private/tmp/def606-analyse-20260911`; herstelinstructie staat in plan v4.
- De 37 automated / 12 review_required / 4 not_evaluated zijn recorddeclaraties. Ze zeggen niet hoeveel regels inhoudelijk betrouwbaar werken. Veel dossiers tonen juist onvoldoende dekking.
- [Productbedoeling en skills](../2026-09-11-DEF-606-productbedoeling-toetsregels-skills-v1.md) en [basisanalyse](../2026-09-11-DEF-606-analyserapport-v2.md) blijven gedeelde achtergrond. Externe ASTRA-detailactualiteit, volledige UI-keten en menselijke normreview zijn niet voor alle regels bewezen.

Na onze bespreking wordt alleen het daadwerkelijke besluit voor de actieve regel in een nieuwe versie vastgelegd. Implementatie vergt een afzonderlijke opdracht.
