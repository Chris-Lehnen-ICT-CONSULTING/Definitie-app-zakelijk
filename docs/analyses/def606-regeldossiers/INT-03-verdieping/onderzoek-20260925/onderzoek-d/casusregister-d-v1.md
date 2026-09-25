# Casusregister onderzoeker D — INT-03 — v1

25 september 2026. Zelfstandige ontwerpverwachtingen, vastgelegd vóór uitvoering. Normvoorstel N-D1 is geen vastgesteld beleid. [Machineleesbare invoer en verwachtingen](proefverwachtingen-d-v1.json).

## Gebruik en bewijsgrens

Elke casus geldt voor dezelfde tekst als aangeleverde én gegenereerde kandidaat. Uitsluitend toetsen verandert niets; G/H mogen alleen een afzonderlijk voorstel geven. Alleen E01–E10 worden in de huidige service uitgevoerd, via manager en cache. E11–E18 zijn ontwerpgevallen. Geen G-/H-modeluitvoer, menselijke gebruikersproef of juridische praktijkvalidatie. Uitkomsten worden afzonderlijk in [proefuitkomsten-d-v1.json](proefuitkomsten-d-v1.json) bewaard; dit register blijft vooraf vastgelegd.

## Historische identiteit

Historische IDs blijven intact: clear_relative, two_candidates, external_reference, possessive_ambiguity, explicit_repeat en empty in INT-03-bewijs-v1/gevallen.json; P/N/G in het dossier van 7 september. E06 correspondeert inhoudelijk met clear_relative, E08 met possessive_ambiguity, E09 met empty en E07 met P. D-IDs zijn eigen meetidentiteiten met expliciete bedoeling, geen hernummering of vervanging. Vooruitverwijzing uit de historische review is verder uitgewerkt als E12.

## Vooraf vastgelegde gevallen

### INT03-D-E01 — context

- Invoer: Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor die gebeurtenis volledig kan worden begrepen en geanalyseerd.

- Bedoeling/informatie: De gebeurtenis wordt begrepen; beide relatieve die-verwijzingen betreffen omstandigheden.

- Grond: ASTRA-snapshot 25-09, JUIST(ER); JSON goed voorbeeld

- G: Behoud duidelijke verwijzingen; geen schrappen van die.

- T: voldoet voor INT-03 volgens ASTRA-paar; geen oordeel over alle andere regels.

- H: Geen herstel nodig.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: offline serviceproef gepland; huidig verwacht review_required. Geen voorspelling van modelkwaliteit.

### INT03-D-E02 — context

- Invoer: Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd.

- Bedoeling/informatie: De gebeurtenis wordt begrepen; het kan ook als geheel worden gelezen en maakt de bedoelde gebeurtenis niet duidelijk.

- Grond: ASTRA-snapshot 25-09, ONJUIST; JSON fout voorbeeld

- G: Maak die gebeurtenis expliciet bij dezelfde betekenis.

- T: voldoet niet volgens ASTRA-paar; niet afleiden uit het aantal voornaamwoorden.

- H: Vervang alleen het laatste het door die gebeurtenis bij bevestigde bedoeling; hertoets buren.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: offline serviceproef gepland; huidig verwacht review_required. Geen voorspelling van modelkwaliteit.

### INT03-D-E03 — regeling

- Invoer: regeling waarbij deze afspraak geldt

- Bedoeling/informatie: Welke afspraak is bedoeld is niet aangeleverd; regeling en afspraak zijn niet vooraf als identiek bevestigd.

- Grond: Bestaande runtimefixture + expliciete synthetische bedoeling D

- G: Vraag welke afspraak bedoeld is; geen afspraak verzinnen.

- T: voldoet niet als zelfstandig te lezen definitie: deze afspraak niet identificeerbaar; herstelgrond ontbreekt. Indien domeinlezer die afspraak aantoonbaar kan bepalen: beoordeling nodig tot die onderbouwing er is.

- H: Stop zonder voorstel totdat afspraak/bedoeling bevestigd is.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: offline serviceproef gepland; huidig verwacht review_required. Geen voorspelling van modelkwaliteit.

### INT03-D-E04 — verslag

- Invoer: Verslag over een besluit nadat het is vastgesteld.

- Bedoeling/informatie: Het besluit is vastgesteld; verslag en besluit zijn twee grammaticaal mogelijke kandidaten.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Schrijf: Verslag over een vastgesteld besluit.

- T: voldoet niet: het laat verslag/besluit open.

- H: Herformuleer alleen met de vastgelegde bedoeling; behoud volgorde/relatie.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: offline serviceproef gepland; huidig verwacht review_required. Geen voorspelling van modelkwaliteit.

### INT03-D-E05 — aantekening

- Invoer: Schriftelijke vastlegging van een waarneming.

- Bedoeling/informatie: Geen verwijzend voornaamwoord; geen extra context nodig voor INT-03.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Behoud de zin.

- T: voldoet voor INT-03 na inhoudelijke afwezigheidscontrole; geen regex-afwezigheid als bewijs.

- H: Geen herstel.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: offline serviceproef gepland; huidig verwacht review_required. Geen voorspelling van modelkwaliteit.

### INT03-D-E06 — aanvrager

- Invoer: Persoon die een aanvraag indient.

- Bedoeling/informatie: Die verwijst naar persoon.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Behoud betrekkelijke bijzin.

- T: voldoet.

- H: Geen herstel; INT-01-patroonconflict apart melden.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: offline serviceproef gepland; huidig verwacht review_required. Geen voorspelling van modelkwaliteit.

### INT03-D-E07 — pijl

- Invoer: Teken dat een richting aangeeft.

- Bedoeling/informatie: Dat verwijst naar teken.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Behoud betrekkelijke bijzin.

- T: voldoet.

- H: Geen herstel.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: offline serviceproef gepland; huidig verwacht review_required. Geen voorspelling van modelkwaliteit.

### INT03-D-E08 — kennisgever

- Invoer: Persoon die zijn vertegenwoordiger informeert over zijn besluit.

- Bedoeling/informatie: Het besluit van de persoon is bedoeld; de tweede zijn kan ook bij de vertegenwoordiger horen.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Maak eigenaar van het besluit expliciet.

- T: voldoet niet bij deze vastgelegde dubbele lezing; tweede zijn beoordelen.

- H: Voorstel: Persoon die zijn vertegenwoordiger informeert over het besluit van de persoon; beoordeel leesbaarheid en behoud.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: offline serviceproef gepland; huidig verwacht review_required. Geen voorspelling van modelkwaliteit.

### INT03-D-E09 — object

- Invoer: (lege tekst)

- Bedoeling/informatie: Geen definitietekst.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Vraag de definitie of voldoende invoer voor generatie.

- T: niet beoordeeld wegens lege kern; leegte is VAL-EMP-001, geen inhoudelijke INT-03-pass of overtreding.

- H: Stop; niet herstellen vanuit verzonnen kenmerken.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: offline serviceproef gepland; huidig verwacht review_required. Geen voorspelling van modelkwaliteit.

### INT03-D-E10 — kadernotitie

- Invoer: Notitie in het kader van een onderzoek.

- Bedoeling/informatie: Het is lidwoord; in het kader is een frase, geen voornaamwoordverwijzing.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Geen wijziging onder INT-03.

- T: voldoet voor INT-03; zelfstandige inhoud/ARAI-05 elders beoordelen.

- H: Een frasehit is geen reparatiegrond.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: offline serviceproef gepland; huidig verwacht review_required. Geen voorspelling van modelkwaliteit.

### INT03-D-E11 — vertegenwoordiger

- Invoer: Persoon met een aanvrager die een aanvraag indient.

- Bedoeling/informatie: Nog onbeslist of persoon of aanvrager indient.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Vraag wie indient.

- T: voldoet niet bij vastgestelde twee lezingen; voor herstel onvoldoende bedoeling.

- H: Stop vóór keuze van actor; maximaal één gericht voorstel na bevestiging.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: ontwerp; niet uitgevoerd. Geen voorspelling van modelkwaliteit.

### INT03-D-E12 — aanvraagbericht

- Invoer: Bericht dat, zodra deze gereed is, de aanvraag vergezelt.

- Bedoeling/informatie: Dat verwijst naar bericht; deze verwijst vooruit naar de aanvraag.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Voorkeur voor expliciete aanvraag, maar vooruitwijzing niet categorisch verbieden.

- T: beoordeling nodig: vooruitverwijzing is geen fout op zichzelf; voldoet indien onafhankelijke lezing eenduidig aanvraag vaststelt.

- H: Geen automatische vervanging; alternatief met de aanvraag pas na bevestiging.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: ontwerp; niet uitgevoerd. Geen voorspelling van modelkwaliteit.

### INT03-D-E13 — document

- Invoer: Document dat voor archivering is bestemd.

- Bedoeling/informatie: De kern herhaalt lemma document; dat verwijst duidelijk naar het genus document.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Kies passend ander genus alleen indien inhoudelijk onderbouwd.

- T: INT-03 voldoet; mogelijke circulariteit apart.

- H: Los CON-CIRC-001 niet op door een onduidelijk het in te voeren.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: ontwerp; niet uitgevoerd. Geen voorspelling van modelkwaliteit.

### INT03-D-E14 — meldende persoon

- Invoer: Persoon die een bericht indient nadat de ontvanger haar heeft bevestigd dat het is ontvangen.

- Bedoeling/informatie: Haar is de persoon; het is het bericht, maar bevestiging kan anders gelezen worden.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Behoud actorrelaties; maak gerichte verwijzingen duidelijk.

- T: beoordeling nodig; alle verwijzingen apart onderbouwen, geen geslacht/ontologie als automatische keuze.

- H: Niet op goed geluk haar of het vervangen; stop bij onvoldoende betekenisgrond.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: ontwerp; niet uitgevoerd. Geen voorspelling van modelkwaliteit.

### INT03-D-E15 — ontvangstbericht

- Invoer: Bericht waarmee de ontvanger de ontvangst bevestigt.

- Bedoeling/informatie: Waarmee verwijst naar bericht.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Behoud duidelijk voornaamwoordelijk bijwoord.

- T: voldoet volgens voorgestelde uitbreiding naar verwijzende constructies.

- H: Geen herstel.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: ontwerp; niet uitgevoerd. Geen voorspelling van modelkwaliteit.

### INT03-D-E16 — waarneming

- Invoer: Waarneming dat het regent.

- Bedoeling/informatie: Het is onpersoonlijk gebruikt, zonder aan te wijzen antecedent.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Geen object bijverzinnen voor het.

- T: voldoet voor referentiële duidelijkheid volgens N-D1; expliciete uitzondering moet Chris bevestigen.

- H: Geen herstel onder INT-03; lemmaherhaling apart.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: ontwerp; niet uitgevoerd. Geen voorspelling van modelkwaliteit.

### INT03-D-E17 — aanvrager

- Invoer: Persoon die een aanvraag indient.

- Bedoeling/informatie: Zelfde type duidelijke relatie als E06, maar evaluator/invoertransport valt technisch uit.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: G-kandidaat blijft ongewijzigd.

- T: error; geen inhoudelijk oordeel, geen afkeur.

- H: Stop; technische oorzaak herstellen buiten tekst. Niet uitgevoerd; foutinjectie buiten huidige nulmeting.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: ontwerp; niet uitgevoerd. Geen voorspelling van modelkwaliteit.

### INT03-D-E18 — kennisgeving

- Invoer: Mededeling aan een ontvanger waarbij deze wordt geregistreerd.

- Bedoeling/informatie: Bronpassage zegt ontvanger; opgegeven bedoeling zegt mededeling.

- Grond: Synthetisch ontwerp D; normvoorstel N-D1, nog te besluiten

- G: Maak conflict zichtbaar; geen definitieve kandidaat op één gekozen lezing.

- T: beoordeling nodig over bedoeling; tekst kan dubbelzinnig zijn, bronconflict afzonderlijk registreren.

- H: Stop zonder herschrijving tot eigenaar conflict oplost.

- Geraakt: INT-01, ARAI-05, CON-CIRC-001; na wijziging nieuwe versie en hertoetsing.

- Bewijs: ontwerp; niet uitgevoerd. Geen voorspelling van modelkwaliteit.

## Effectevaluatie en tegenbewijs

Deze 18 gevallen zijn ontwikkelgevallen en mogen niet als onafhankelijke ongeziene evaluatieset worden gepresenteerd. Na Chris’ normbesluit bevriest een onafhankelijke beoordelaar aanvullend 12 ongeziene gevallen (4 duidelijke, 4 onduidelijke, 2 niet-referentiële/vooruitwijzende grensgevallen, 2 ontbrekende/strijdige-invoergevallen). Vóór model- of gebruikersproeven legt die beoordelaar G/T/H-verwachtingen en bedoelde referenten vast. Voor/na: dezelfde invoer, bronset, modelinstellingen en norm, alleen onderzochte instructie of beoordelingshulp verschilt. Betekenisverlies is onaanvaardbaar; trefwoordvermijding en meer groene statussen tellen niet als winst. Uitwerking, eigenaar en uitvoeringsvoorwaarden: aanvulling-d-v1.md §Q6.
