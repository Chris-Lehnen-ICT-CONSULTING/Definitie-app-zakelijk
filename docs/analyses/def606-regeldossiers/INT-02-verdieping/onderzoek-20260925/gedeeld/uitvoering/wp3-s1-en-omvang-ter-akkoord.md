# DEF-771 — concrete S1-selectie en WP3 ter akkoord

25 september 2026. **Voorstel; niet geïmplementeerd.** Dit document bundelt W3.1/W3.2. Planakkoord dekt al de richting context_lists en nieuwe C1-replay, maar de oorspronkelijke opdracht verlangt expliciet akkoord voor deze markerlijst en het concrete grote WP3-pakket.

## 1. S1: zes aanvullende patronen

De zeven bestaande patronen blijven. Deze zes worden uitsluitend leeshulp, hoofdletterongevoelig:

| Aanvulling | Exact voorgesteld patroon | Begrenzing |
|---|---|---|
| van oordeel is | `\bvan\s+oordeel\s+is\b` | Alleen deze woordvolgorde |
| naar eigen inzicht | `\bnaar\s+eigen\s+inzicht\b` | Volledige frase |
| redelijk acht | `\bredelijk\s+acht\b` | Vindt niet automatisch “evenredig acht” |
| kan … besluiten | `\bkan\b[^.!?;\n]*\bbesluiten\b` | Geen passage over punt, vraagteken, uitroepteken, puntkomma of regelgrens |
| moet | `\bmoet\b` | Bewust breed; ook beschrijving van een plicht kan treffen |
| dient te | `\bdient\s+te\b` | “dient als/tot” wordt hiermee niet geraakt |

De code zou hiermee dertien patronen krijgen. Geen enkel patroon levert pass/fail, score of vaststelblokkade. Er is geen claim op volledige vindbaarheid of gemeten bruikbaarheid. Andere vervoegingen/woordvolgorden kunnen ontbreken; de waarschuwing zonder signaal blijft daarom nodig.

## 2. Deterministische vindbaarheidscontrole van het voorstel

Uitvoer: wp3-s1-voorstel-vindbaarheid.json. Dit is uitsluitend regexanalyse van het voorstel, geen uitgevoerde evaluator- of normtest.

| Geval | Voorgestelde S1-treffer | Beoogde appgedrag bij aanwezige kern/context |
|---|---|---|
| C02, ASTRA “moet ondersteunen” | moet | RR met neutrale passagevraag; dus niet langer de signaalloze waarschuwing |
| C13, “na afweging … evenredig acht” | Geen | RR met exacte waarschuwing; geen valse claim dat S1 dit geval vindt |
| C83, “naar eigen inzicht … redelijk acht” | Twee markers | RR met volledige passage en positie; dezelfde passage niet nodeloos dubbel tonen |
| C59, definitie van beslisregel | Geen | RR met waarschuwing; geen automatische afkeur |
| C105, “De medewerker laat de aanvrager toe.” | Geen | RR met waarschuwing ondanks de opdrachtfunctie |
| Nieuw synthetisch beschrijvend geval: “Bevoegdheid waarbij de bevoegde instantie naar eigen inzicht kan besluiten welke maatregel passend is.” | naar eigen inzicht; kan … besluiten | RR met neutrale vraag; de treffers bewijzen geen gebrek |
| Nieuw synthetisch plichtbegrip: “Verplichting die een partij moet nakomen.” | moet | RR; normatieve zaak beschrijven mag, marker is geen afkeur |
| Nieuw synthetisch functiegeval: “Voorwerp dat dient als ondersteuning.” | Geen | Geen treffer op dient te |

Voor C02 wijkt de passagevorm af van de oorspronkelijke signaalloze testverwachting. Dit is een expliciet gevolg van de voorgestelde marker “moet”; C105 blijft het bewijs voor een voorschrift zonder signaal. Goedkeuring van deze lijst omvat die aangepaste C02-verwachting. Alle overige oorspronkelijke casussen blijven behouden.

## 3. Resultaat en passagehulp

- Exacte toetsvraag, O1-vraag en waarschuwing uit synthese v5 §4; niets inkorten.
- RR met citaat van het volledige zinsdeel/de dragende zin en positie in de exacte ongewijzigde kern. Geen los markerwoord als citaat; geen positie in opgeschoonde tekst presenteren alsof die op de oorspronkelijke kern slaat. Bij onzekere grens liever de volledige kern tonen. Herhaalde identieke zinsdelen op verschillende posities onderscheiden; meerdere markers binnen dezelfde passage mogen één neutrale vraag delen.
- Technische positieconventie: nulgebaseerde start, exclusief einde, controleerbaar via kern[start:einde] == citaat; in de reden de conventie duidelijk benoemen. Geen nieuw resultaatveld of opslagcontract nodig.
- Lege kern, label zonder kern (C23) of ontbrekende context geeft not_evaluated met de exacte NE-melding. Kern/context-onderscheid tonen. Contextvereiste expliciet in INT-02 required_inputs; serviceaanpassing uitsluitend voor de INT-02-reden, overige regels behouden hun gedrag.
- UI: alleen INT-02 toevoegen aan de bestaande tuple die de reden toont. Geen issues-helper, herlaadroute, poort, herstel of O2-modelaanroep.
- Record noemt signalen expliciet niet-normatieve leeshulp. De goedgekeurde markerlijst en actuele uitvoeringsstatus komen ook in het canonieke contract en de bytegelijke kopie; bind die samen met het record aan def771-int02/2. N/G/T/H-betekenis en exacte teksten blijven gelijk. De WP1-opbouwscriptuitvoer blijft historisch WP1-bewijs; niet opnieuw uitvoeren over de latere contractversie.

## 4. Concrete bestanden en omvang

| Nr | Bestand | Werk |
|---|---|---|
| 1 | src/services/validation/evaluators/judgment_review.py | INT-02-tak, kerncontrole en passagehulp |
| 2 | src/services/validation/modular_validation_service.py | Exacte INT-02-NE-reden bij ontbrekende context |
| 3 | src/toetsregels/regels/INT-02.json | S1, leeshulpduiding, context_lists, contractversie |
| 4 | src/ui/components/validation_view.py | INT-02 in reden-tuple |
| 5 | tests/unit/validation/test_def771_int02_contract.py | Goedgekeurde inputs en versie /2; controles behouden |
| 6 | nieuw tests/unit/validation/test_def771_int02_o1.py | Casussen, posities, RR/NE, geen oordeel uit signalen |
| 7 | nieuw tests/unit/ui/test_def771_int02_validation_view.py | Reden zichtbaar, geen overige UI-wijziging |
| 8 | skillwerkboom: skills/definitie-toetsregels/references/int02-beslisregel.md | Markerselectie, versie /2 en feitelijke uitvoeringsstatus |
| 9 | skillwerkboom: skills/definitie-nederlandse-definities/references/int02-beslisregel.md | Bytegelijke kopie |
| 10 | nieuw gedeeld/uitvoering/proef-c1-uitvoering-na-o1.py | Historische proef behouden; nieuwe offline contextvarianten |

De twee SKILL.md-bestanden noemen nu expliciet contractversie /1. Die verwijzingen moeten mee naar /2: **bestanden 11 en 12**. Dat voorkomt een achterhaalde verwijzing na het bijwerken van de contracten. Geen overige skilltekst wijzigen.

**Raming: 300–500 code-/testregels plus circa 30–60 contract-/skillregels, twaalf inhoudelijke bestanden over twee repositories.** Bewijslogs en proef-c1-uitvoering-na-o1.json komen daar als uitvoer bij. Dit is groter dan de vroege WP3-raming omdat ook de in WP1 ontstane versiebinding en tests consistent moeten blijven. Geen dependencies of databaseschemawijziging.

## 5. RED en acceptatie

Eerst rood: C04/C50/C54 RR met signaal en neutrale vraag; C02 volgens de goedgekeurde moet-marker; C83 met S1; C105 waarschuwing; C06/C23/C56 NE; C13 zonder beloofde S1-treffer; C59 en de nieuwe beschrijvende gevallen nooit fail. Exacte citaten/posities, brontekst ongewijzigd en UI-reden zichtbaar. Geen signaal als oordeel of score.

De nieuwe C1-replay gebruikt synthetische context voor de RR-gevallen en afzonderlijke contextloze NE-varianten. Bewaar originele en nieuwe verwachtingen, werkelijke status, reden, citaten/posities, hashes, commando en exitstatus. Oude proef en bewijs nooit overschrijven. Geen modelcalls. WP4 herijkt daarna de bestaande C24/C25-contextfixtures; geen testgeval verwijderen.

Verificatie: gerichte GREEN-tests, lint op geraakte bestanden, bytegelijkheid en versiebinding; coördinator leest de diff en rapporteert. Onafhankelijke review van de volledige branch volgt in WP5. Geen kwaliteits- of effectclaim.
