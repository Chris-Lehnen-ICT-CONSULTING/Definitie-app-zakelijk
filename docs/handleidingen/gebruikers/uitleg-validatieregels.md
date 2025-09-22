---
canonical: true
status: active
owner: validation
last_verified: 2025-09-22
applies_to: definitie-app@v2
---

# Uitleg Validatieregels (CON-01 e.a.)

Deze pagina legt in gewone mensentaal uit hoe de belangrijkste validatieregels in de Definitie‑app werken. De regels helpen om definities consequent, herbruikbaar en toetsbaar te maken.

## In het kort
- Regels controleren de tekst van je definitie en geven waarschuwingen of fouten met concrete tips.
- Sommige regels kijken ook naar gekozen context (organisatorisch, juridisch, wettelijke basis) en naar bestaande definities om duplicaten te voorkomen.
- Je ziet per regel meldingen terug met iconen en een korte suggestie om te verbeteren.

## CON‑01 — Contextspecifieke formulering, zonder expliciet te benoemen

Doel: laat de definitie passen in de gekozen context, maar noem die context niet letterlijk in de definitietekst.

Wat wordt gecontroleerd:
- Letterlijke contextwoorden uit je selectie in de tekst (organisatorische_context, juridische_context, wettelijke_basis).
- Brede contexttaal via herkenningspatronen, zoals “in de context van”, “in het kader van”, “juridisch”, namen als “DJI/OM/KMAR”, of “volgens het Wetboek van …”.
- Vergelijking met goede/foute voorbeelden (snelle heuristiek).
- Duplicaatcontrole: bestaat er al een definitie met hetzelfde begrip én precies dezelfde context? Dan volgt een waarschuwing (of fout als duplicaat is geforceerd).

Beoordeling in grote lijnen:
- Context letterlijk genoemd → fout (score 0.0) met duidelijke melding.
- Brede contexttaal gevonden, maar geen “fout voorbeeld” → waarschuwing (score ~0.5): tekst mogelijk te vaag/contextgericht.
- Lijkt op “fout voorbeeld” → fout (0.0).
- Lijkt op “goed voorbeeld” → ok (1.0).
- Niets verdachts → ok (0.9).
- Duplicaatcontext gevonden → waarschuwing; kan escaleren naar fout bij geforceerde duplicaat.

Praktische schrijftips:
- Schrijf contextneutraal; vermijd “in de/het kader/context van”, namen (DJI/OM/KMAR) en “volgens het Wetboek van …”.
- Laat de context impliciet doorklinken via precieze, domeinpassende formulering.

Voorbeeld:
- Context: org = DJI, jur = strafrecht.
  - “Registratie is … binnen de context van het strafrecht bij DJI.” → fout (context letterlijk genoemd).
  - “Registratie is het formeel vastleggen van gegevens in een geautoriseerd systeem.” → ok; als zo’n definitie al bestaat met dezelfde context, volgt een duplicaat‑waarschuwing.

## Andere veelgebruikte regels (kort)
- ESS‑01 — Doel/teleologie vermijden: geen “om te/teneinde…”, focus op wat het begrip ís.
- STR‑01 — Start met zelfstandig naamwoord: begin na het lemma met het kernwoord, geen hulpwerkwoord of lidwoord.
- INT‑01 — Eén compacte zin: vermijd opsommingen en bijzinnen; maak het bondig en eenduidig.

Meer details vind je in de backlog en technische documentatie. Deze pagina focust op de praktische kant voor het schrijven van goede definities.

## Overzicht alle toetsregels

Onderstaande tabel geeft per regel een korte omschrijving. Dit omvat zowel de uitgebreide regels (per categorie) als de interne basisregels (VAL‑*/STR‑* e.d.) die voor extra vangrails zorgen.

| Code | Naam | Korte uitleg |
|------|------|--------------|
| ARAI-01 | geen werkwoord als kern (afgeleid) | De kern van de definitie mag geen werkwoord zijn, om verwarring tussen handelingen en concepten te voorkomen. |
| ARAI-02 | Vermijd vage containerbegrippen | De definitie mag geen containerbegrippen bevatten die op zichzelf weinig verklarende waarde hebben. |
| ARAI-02SUB1 | Lexicale containerbegrippen vermijden | Vermijd algemene termen als 'aspect', 'ding', 'iets' of 'element' in definities. |
| ARAI-02SUB2 | Ambtelijke containerbegrippen vermijden | Vermijd vaagtaal zoals ‘proces’, ‘voorziening’ of ‘activiteit’ als deze niet worden gespecificeerd. |
| ARAI-03 | Beperk gebruik van bijvoeglijke naamwoorden | Definities bevatten zo min mogelijk subjectieve of contextafhankelijke bijvoeglijke naamwoorden. |
| ARAI-04 | Vermijd modale hulpwerkwoorden | Definities vermijden het gebruik van modale hulpwerkwoorden zoals 'kunnen', 'mogen', 'moeten' of 'zullen'. |
| ARAI-04SUB1 | Beperk gebruik van modale werkwoorden | Definities vermijden modale werkwoorden zoals ‘kan’, ‘mag’, ‘moet’, omdat deze onduidelijkheid scheppen over de essentie van het begrip. |
| ARAI-05 | Vermijd impliciete aannames | Een definitie bevat geen impliciete aannames die alleen met voorkennis begrepen kunnen worden. |
| ARAI-06 | Correcte definitiestart: geen lidwoord, geen koppelwerkwoord, geen herhaling begrip | De definitie mag niet beginnen met een lidwoord, geen koppelwerkwoord bevatten aan het begin en het begrip mag niet herhaald worden in de definitie. |
| CON-01 | Eigen definitie voor elke context. Contextspecifieke formulering zonder expliciete benoeming | Formuleer de definitie zó dat deze past binnen de opgegeven context(en), zonder deze expliciet te benoemen in de definitie zelf. |
| CON-02 | Baseren op authentieke bron | Gebruik een gezaghebbende of officiële bron als basis voor de definitie. |
| CON-CIRC-001 | Geen circulaire definitie | De definitie mag het begrip zelf niet letterlijk bevatten. |
| DUP_01 | Geen duplicaat definities in database | Controleer of er geen identieke of zeer vergelijkbare definitie al bestaat in de database voor hetzelfde begrip. |
| ESS-01 | Essentie, niet doel | Een definitie beschrijft wat iets is, niet wat het doel of de bedoeling ervan is. |
| ESS-02 | Ontologische categorie expliciteren (type / particulier / proces / resultaat) | Indien een begrip meerdere ontologische categorieën kan aanduiden, moet uit de definitie ondubbelzinnig blijken welke van deze vier bedoeld wordt: soort (type), exemplaar (particulier), proces of resultaat. |
| ESS-03 | Instanties uniek onderscheidbaar (telbaarheid) | Een definitie moet criterium(en) bevatten waarmee afzonderlijke instanties uniek herkenbaar en telbaar zijn (singulariteit of pluraliteit). |
| ESS-04 | Toetsbaarheid | Een definitie bevat objectief toetsbare elementen (harde deadlines, aantallen, percentages, meetbare criteria). |
| ESS-05 | Voldoende onderscheidend | Een definitie moet duidelijk maken wat het begrip uniek maakt ten opzichte van andere verwante begrippen. |
| ESS-CONT-001 | Essentiële inhoud aanwezig | De definitie bevat voldoende inhoud om de essentie te dekken. |
| INT-01 | Compacte en begrijpelijke zin | Een definitie is compact en in één enkele zin geformuleerd. |
| INT-02 | Geen beslisregel | Een definitie bevat geen beslisregels of voorwaarden. |
| INT-03 | Voornaamwoord-verwijzing duidelijk | Definities mogen geen voornaamwoorden bevatten waarvan niet direct duidelijk is waarnaar verwezen wordt. |
| INT-04 | Lidwoord-verwijzing duidelijk | Definities mogen geen onduidelijke verwijzingen met de lidwoorden 'de' of 'het' bevatten. |
| INT-06 | Definitie bevat geen toelichting | Een definitie bevat geen nadere toelichting of voorbeelden, maar uitsluitend de afbakening van het begrip. |
| INT-07 | Alleen toegankelijke afkortingen | In een definitie gebruikte afkortingen zijn voorzien van een voor de doelgroep direct toegankelijke referentie. |
| INT-08 | Positieve formulering | Een definitie wordt in principe positief geformuleerd, dus zonder ontkenningen te gebruiken; uitzondering voor onderdelen die de definitie specifieker maken. |
| INT-09 | Opsomming in extensionele definitie is limitatief | Een extensionele definitie definieert een begrip door opsomming van alle bedoelde elementen; deze opsomming moet uitsluitend limitatief zijn. |
| INT-10 | Geen ontoegankelijke achtergrondkennis nodig | Een definitie moet begrijpelijk zijn zonder specialistische of niet-openbare kennis; uitzondering: zeer specifieke verwijzing naar openbare bron (bijv. wet met artikel). |
| SAM-01 | Kwalificatie leidt niet tot afwijking | Een definitie mag niet zodanig zijn geformuleerd dat deze afwijkt van de betekenis die de term in andere contexten heeft. |
| SAM-02 | Kwalificatie omvat geen herhaling | Als een begrip wordt gekwalificeerd, mag de definitie geen herhaling bevatten uit of conflict bevatten met de definitie van het hoofdbegrip. |
| SAM-03 | Definitieteksten niet nesten | Een definitie van een begrip of een belangrijk deel daarvan mag niet letterlijk herhaald worden in de definitie van een ander begrip. |
| SAM-04 | Begrip-samenstelling strijdt niet met samenstellende begrippen | De betekenis van een samengesteld begrip mag niet in strijd zijn met de betekenissen van de samenstellende begrippen; de samenstelling leidt tot een specialisatie van één van de delen. |
| SAM-05 | Geen cirkeldefinities | Een cirkeldefinitie (wederzijdse of meerdiepse verwijzing tussen begrippen) mag niet voorkomen. |
| SAM-06 | Één synoniem krijgt voorkeur | Kies per begrip één voorkeurs-term (lemma). |
| SAM-07 | Geen betekenisverruiming binnen definitie | De definitie mag de betekenis van de term niet uitbreiden met extra elementen die niet in de term besloten liggen. |
| SAM-08 | Synoniemen hebben één definitie | Voor synoniemen wordt één en dezelfde definitie gehanteerd. |
| STR-01 | definitie start met zelfstandig naamwoord | De definitie moet starten met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord. |
| STR-02 | Kick-off ≠ de term | De definitie moet beginnen met verwijzing naar een breder begrip, en dan de verbijzondering ten opzichte daarvan aangeven. |
| STR-03 | Definitie ≠ synoniem | De definitie van een begrip mag niet simpelweg een synoniem zijn van de te definiëren term. |
| STR-04 | Kick-off vervolgen met toespitsing | Een definitie moet na de algemene opening meteen toespitsen op het specifieke begrip. |
| STR-05 | Definitie ≠ constructie | Een definitie moet aangeven wat iets is, niet uit welke onderdelen het bestaat. |
| STR-06 | Essentie ≠ informatiebehoefte | Een definitie geeft de aard van het begrip weer, niet de reden waarom het nodig is. |
| STR-07 | Geen dubbele ontkenning | Een definitie bevat geen dubbele ontkenning. |
| STR-08 | Dubbelzinnige 'en' is verboden | Een definitie bevat geen 'en' die onduidelijk maakt of beide kenmerken vereist zijn of slechts één van beide. |
| STR-09 | Dubbelzinnige 'of' is verboden | Een definitie bevat geen 'of' die onduidelijk maakt of beide mogelijkheden gelden of slechts één van de twee. |
| STR-ORG-001 | Zinsstructuur en redundantie | Vermijd extreem lange zinnen en tegenstrijdige/onnodige herhaling. |
| STR-TERM-001 | Consistente terminologie (koppelteken) | Gebruik correcte terminologie en interpunctie (bijv. 'HTTP-protocol'). |
| VAL-EMP-001 | Lege definitie is ongeldig | De definitietekst mag niet leeg zijn. |
| VAL-LEN-001 | Minimale lengte (woorden/tekens) | De definitie moet een minimale lengte hebben om betekenisvol te zijn. |
| VAL-LEN-002 | Maximale lengte (woorden/tekens) | De definitie mag niet onnodig lang of overladen zijn. |
| VER-01 | Term in enkelvoud | De te definiëren term moet in het enkelvoud staan, tenzij deze alleen in het meervoud bestaat. |
| VER-02 | Definitie in enkelvoud | De definitie is geformuleerd in het enkelvoud. |
| VER-03 | Werkwoord-term in infinitief | Een werkwoord als term moet in de onbepaalde wijs (infinitief) staan. |

Let op: deze uitleg focust op gebruik. Voor technische details (regex‑patronen, drempels, interne weging) en de meest recente canonieke bronnen, zie de technische documentatie en configuratiebestanden in de repository.

## Regel‑specifieke uitleg

Onderstaande secties geven per regel een korte gebruiksuitleg in dezelfde vorm.

### ARAI-01 — geen werkwoord als kern (afgeleid)
- Wat controleert het: de kern van de definitie is geen werkwoordsvorm.
- Hoe beoordeeld: detecteert werkwoordkernen; markeert bij twijfel als waarschuwing.
- Veelvoorkomende fouten: “is het uitvoeren van…”.
- Schrijftips: kies een zelfstandig naamwoord als kern (genus), niet een activiteit.

### ARAI-02 — Vermijd vage containerbegrippen
- Wat controleert het: containerbegrippen die weinig verklaren.
- Hoe beoordeeld: herkent patronen (bijv. ‘component/onderdeel’ zonder specificatie).
- Veelvoorkomende fouten: “onderdeel dat…”, “component die…”.
- Schrijftips: maak concreet welke soort/klasse het betreft; voeg differentia toe.

### ARAI-02SUB1 — Lexicale containerbegrippen vermijden
- Wat controleert het: algemene termen als ‘aspect’, ‘ding’, ‘iets’, ‘element’.
- Hoe beoordeeld: markeert bij voorkomen als vaag.
- Schrijftips: vervang door de specifieke klasse of eigenschap.

### ARAI-02SUB2 — Ambtelijke containerbegrippen vermijden
- Wat controleert het: ambtelijke vaagtaal (‘proces’, ‘voorziening’, ‘activiteit’) zonder specificatie.
- Hoe beoordeeld: markeert bij voorkomen zonder nadere afbakening.
- Schrijftips: specificeer het type of resultaat van de activiteit.

### ARAI-03 — Beperk gebruik van bijvoeglijke naamwoorden
- Wat controleert het: subjectieve/contextafhankelijke bijvoeglijk naamwoordgebruik.
- Hoe beoordeeld: markeert woorden als ‘voldoende’, ‘doeltreffend’ e.d.
- Schrijftips: gebruik objectieve, toetsbare kwalificaties of laat ze weg.

### ARAI-04 — Vermijd modale hulpwerkwoorden
- Wat controleert het: ‘kunnen’, ‘mogen’, ‘moeten’, ‘zullen’ in definities.
- Hoe beoordeeld: markeert modale vormen als ruis.
- Schrijftips: definieer wat het begrip is; geen mogelijkheden of verplichtingen.

### ARAI-04SUB1 — Beperk gebruik van modale werkwoorden
- Wat controleert het: varianten (‘kan’, ‘mag’, ‘moet’).
- Schrijftips: zie ARAI‑04.

### ARAI-05 — Vermijd impliciete aannames
- Wat controleert het: kennis die niet in de definitie staat.
- Hoe beoordeeld: heuristisch, vaak in combinatie met vage termen.
- Schrijftips: maak criteria expliciet of verwijs buiten de definitie via context/bronvelden.

### ARAI-06 — Correcte definitiestart
- Wat controleert het: start niet met lidwoord/koppelwerkwoord; herhaal het lemma niet.
- Hoe beoordeeld: markeert openingspatronen.
- Schrijftips: start met het genus (bv. “model …”).

### CON-01 — Contextspecifieke formulering zonder expliciete benoeming
- Zie uitgebreide sectie bovenaan (CON‑01).

### CON-02 — Baseren op authentieke bron
- Wat controleert het: aanwezigheid van een authentieke basis.
- Hoe beoordeeld: let op patronen als ‘volgens’, ‘conform’, ‘gebaseerd op’ (positief signaal) of afwezigheid ervan (advies).
- Schrijftips: bronverwijzing maak je in de bijbehorende velden of neutraal in de tekst.

### CON-CIRC-001 — Geen circulaire definitie
- Wat controleert het: lemma komt letterlijk terug in de definitie.
- Hoe beoordeeld: fout bij match.
- Schrijftips: omschrijf zonder het lemma te herhalen (genus + differentia).

### DUP_01 — Geen duplicaat definities in database
- Wat controleert het: identieke definitie bij hetzelfde begrip.
- Hoe beoordeeld: waarschuwing (of fout bij geforceerde duplicaat) met verwijzing naar bestaande definitie.
- Schrijftips: hergebruik of differentieer context/lemma.

### ESS-01 — Essentie, niet doel
- Wat controleert het: doel/teleologie in plaats van essentie.
- Hoe beoordeeld: markeert patronen zoals ‘om te’, ‘teneinde’, ‘met als doel’.
- Schrijftips: beschrijf wat het ís; doelen en gebruik horen niet in de definitie.

### ESS-02 — Ontologische categorie expliciteren
- Wat controleert het: expliciet maken of het een type, particulier (exemplaar), proces of resultaat is.
- Hoe beoordeeld: vereist duidelijke marker of contextsignaal; mist → melding.
- Schrijftips: voeg ‘soort van …’, ‘exemplaar van …’, of ‘proces dat …’ toe.

### ESS-03 — Instanties uniek onderscheidbaar
- Wat controleert het: criterium om instanties te tellen/herkennen.
- Hoe beoordeeld: afwezigheid van identificerende elementen → melding.
- Schrijftips: noem nummer/code/registratie of uniek kenmerk.

### ESS-04 — Toetsbaarheid
- Wat controleert het: objectief toetsbare elementen.
- Hoe beoordeeld: markeert aanwezigheid/afwezigheid van meetbare criteria.
- Schrijftips: voeg kwantitatieve grenzen of voorwaarden toe.

### ESS-05 — Voldoende onderscheidend
- Wat controleert het: onderscheid met verwante begrippen.
- Hoe beoordeeld: markeert vaagheden/overlap.
- Schrijftips: voeg differentia toe die het begrip afbakent.

### ESS-CONT-001 — Essentiële inhoud aanwezig
- Wat controleert het: niet te summier.
- Schrijftips: voeg de kerncomponenten toe (genus + belangrijkste differentia).

### INT-01 — Compacte en begrijpelijke zin
- Wat controleert het: één zin, geen overbodige bijzinnen.
- Hoe beoordeeld: markeert meerdere zinnen/verbindingswoorden.
- Schrijftips: schrijf bondig en lineair.

### INT-02 — Geen beslisregel
- Wat controleert het: voorwaarden of if/then‑achtige tekst.
- Schrijftips: verplaats beslislogica naar beleid/regels, niet de definitie.

### INT-03 — Voornaamwoord‑verwijzing duidelijk
- Wat controleert het: ‘dit/die/deze/daarvan’ met onduidelijke referent.
- Schrijftips: vervang door de concrete term.

### INT-04 — Lidwoord‑verwijzing duidelijk
- Wat controleert het: ‘de/het’ zonder antecedent.
- Schrijftips: noem het referent expliciet.

### INT-06 — Geen toelichting in definitie
- Wat controleert het: uitleg of voorbeelden in plaats van afbakening.
- Schrijftips: zet toelichting buiten de definitie.

### INT-07 — Alleen toegankelijke afkortingen
- Wat controleert het: onduidelijke afkortingen.
- Schrijftips: definieer eerst of verwijs naar publiek toegankelijke bron.

### INT-08 — Positieve formulering
- Wat controleert het: onnodige ontkenningen.
- Schrijftips: herformuleer positief.

### INT-09 — Limitatieve opsomming (extentioneel)
- Wat controleert het: of een extentionele definitie werkelijk limitatief is.
- Schrijftips: geef expliciet alle elementen, zonder open einde.

### INT-10 — Geen verborgen achtergrondkennis nodig
- Wat controleert het: specialistische/niet‑openbare kennis.
- Schrijftips: verwijs kort naar openbare bron (bijv. wet+artikel) indien nodig.

### SAM-01 — Kwalificatie leidt niet tot afwijking
- Wat controleert het: kwalificatie verandert betekenis t.o.v. standaardterm.
- Schrijftips: laat kwalificatie specialiseren, niet herdefiniëren.

### SAM-02 — Kwalificatie omvat geen herhaling
- Wat controleert het: herhaling/conflict met definitie hoofdbegrip.
- Schrijftips: noem alleen het onderscheidende criterium.

### SAM-03 — Definitieteksten niet nesten
- Wat controleert het: letterlijke herhaling elders.
- Schrijftips: parafraseer of verwijs, niet kopiëren.

### SAM-04 — Samenstelling strijdt niet met samenstellende begrippen
- Wat controleert het: samenstelling is een specialisatie, geen tegenstelling.
- Schrijftips: begin met genus uit de samenstelling, voeg differentia toe.

### SAM-05 — Geen cirkeldefinities
- Wat controleert het: wederzijdse/meerdiepse cirkels.
- Schrijftips: verbreek de cirkel, voeg zelfstandig criterium toe.

### SAM-06 — Één synoniem krijgt voorkeur
- Wat controleert het: consistent gebruik van voorkeurs‑term.
- Schrijftips: kies één lemma en verwijs overige als synoniem.

### SAM-07 — Geen betekenisverruiming binnen definitie
- Wat controleert het: extra elementen die buiten de term vallen.
- Schrijftips: beperk tot essentie van de term.

### SAM-08 — Synoniemen hebben één definitie
- Wat controleert het: dezelfde definitie voor synoniemen.
- Schrijftips: beheer via lemma/synoniem‑beheer.

### STR-01 — Start met zelfstandig naamwoord
- Wat controleert het: juiste openingsstructuur.
- Schrijftips: genus + differentia, geen lidwoord/hulpwerkwoord.

### STR-02 — Kick‑off ≠ de term
- Wat controleert het: begint met breder begrip, daarna toespitsing.
- Schrijftips: noem genus expliciet.

### STR-03 — Definitie ≠ synoniem
- Wat controleert het: geen pure synonymie.
- Schrijftips: voeg afbakenend criterium toe.

### STR-04 — Kick‑off vervolgen met toespitsing
- Wat controleert het: na de opening meteen specificeren.
- Schrijftips: kom snel tot het onderscheidende.

### STR-05 — Definitie ≠ constructie
- Wat controleert het: opsomming van onderdelen i.p.v. essentie.
- Schrijftips: beschrijf aard/klasse, niet componenten.

### STR-06 — Essentie ≠ informatiebehoefte
- Wat controleert het: uitleg ‘waarom’ i.p.v. ‘wat’.
- Schrijftips: verplaats motivering buiten definitie.

### STR-07 — Geen dubbele ontkenning
- Wat controleert het: ‘niet … niet’ e.d.
- Schrijftips: herschrijf naar positieve, eenduidige formulering.

### STR-08 — Dubbelzinnige ‘en’ verboden
- Wat controleert het: onduidelijke conjunctie.
- Schrijftips: specificeer of het cumulatief of alternatief is.

### STR-09 — Dubbelzinnige ‘of’ verboden
- Wat controleert het: ambiguïteit door ‘of’.
- Schrijftips: maak keuze of geef exclusiviteit expliciet aan.

### STR-ORG-001 — Zinsstructuur en redundantie
- Wat controleert het: te lange/complexe zinnen, herhaling, tegenstrijdigheid.
- Schrijftips: deel zinnen op, verwijder redundantie.

### STR-TERM-001 — Consistente terminologie (koppelteken)
- Wat controleert het: terminologie en typografie (bijv. koppelteken).
- Schrijftips: volg terminologie‑standaard (bijv. ‘HTTP‑protocol’).

### VAL-EMP-001 — Lege definitie is ongeldig
- Wat controleert het: niet‑lege tekst.
- Schrijftips: vul minimaal de essentie in.

### VAL-LEN-001 — Minimale lengte
- Wat controleert het: minimum aan woorden/tekens.
- Schrijftips: zorg dat alle kerninformatie aanwezig is.

### VAL-LEN-002 — Maximale lengte
- Wat controleert het: maximum aan woorden/tekens.
- Schrijftips: houd het compact; verwijder bijzinnen.

### VER-01 — Term in enkelvoud
- Wat controleert het: lemma in enkelvoud (tenzij plurale tantum).
- Schrijftips: gebruik enkelvoud of motiveer uitzondering.

### VER-02 — Definitie in enkelvoud
- Wat controleert het: tekst in enkelvoudsvorm.
- Schrijftips: vermijd meervoudsvormen die dubbelzinnig zijn.

### VER-03 — Werkwoord‑term in infinitief
- Wat controleert het: onbepaalde wijs voor werkwoord‑lemma’s.
- Schrijftips: schrijf lemma als infinitief (bv. ‘registreren’).
