# Casusregister B — INT-03 — v1

Vastgelegd vóór uitvoering. Normverwachtingen zijn onafhankelijke voorstellen van B, behalve het expliciete ASTRA-paar. Voor alle tekstgevallen geldt dezelfde T-norm bij generatie en aangeleverde inhoud; alleen G/H mogen een nieuwe kandidaat voorstellen. Precieze invoer en runtimeverwachtingen staan in [proefverwachtingen-b-v1.json](proefverwachtingen-b-v1.json).

Historische IDs blijven ongewijzigd: `clear_relative`, `two_candidates`, `external_reference`, `possessive_ambiguity`, `explicit_repeat`, `empty` uit `../../../INT-03-bewijs-v1/gevallen.json`; daarnaast P/N/G uit het dossier van 7 september. Nieuwe B-IDs zijn geen hernummering.

## INT03-B-E01 — context

- Invoer: 'Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor die gebeurtenis volledig kan worden begrepen en geanalyseerd.'
- Bedoeling/informatie: De gebeurtenis wordt begrepen.
- G: Behoud die gebeurtenis; relatieve die-zinnen toegestaan.
- T: Voldoet aan INT-03 volgens ASTRA-voorbeeld; geen oordeel over overige regels.
- H: Geen herstel.
- Grond: ASTRA JUIST(ER), aangeleverde raw-bron
- Relaties: INT-03
- Uitvoering: huidige service op beide laadpaden; normkwaliteit niet automatisch gemeten; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E02 — context

- Invoer: 'Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd.'
- Bedoeling/informatie: De gebeurtenis wordt begrepen; het benoemt dat niet eenduidig.
- G: Genereer die gebeurtenis, niet het.
- T: Voldoet niet volgens ASTRA-paar; kandidaten geheel en gebeurtenis met afwijkend grammaticaal geslacht.
- H: Alleen met gegeven bedoeling het vervangen door die gebeurtenis; behoud rest.
- Grond: ASTRA ONJUIST, aangeleverde raw-bron
- Relaties: INT-03
- Uitvoering: huidige service op beide laadpaden; normkwaliteit niet automatisch gemeten; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E03 — regeling

- Invoer: 'regeling waarbij deze afspraak geldt'
- Bedoeling/informatie: Deze afspraak is niet geïdentificeerd.
- G: Vraag welke afspraak; verzin geen inhoud.
- T: Voldoet niet als losstaande definitie: deze afspraak heeft geen identificerende grond; herstelgrond ontbreekt afzonderlijk.
- H: Stop en vraag welke afspraak bedoeld is.
- Grond: Onderzoeksinterpretatie B van ASTRA; synthetisch, nog onafhankelijk te beoordelen
- Relaties: INT-03, INT-04, ARAI-05, CON-CIRC-001
- Uitvoering: huidige service op beide laadpaden; normkwaliteit niet automatisch gemeten; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E04 — instrument

- Invoer: 'instrument voor een besluit nadat het is vastgesteld'
- Bedoeling/informatie: Bedoeld is het besluit; ook instrument is onzijdig.
- G: Benoem het besluit expliciet.
- T: Voldoet niet: het kan instrument of besluit betekenen.
- H: Alleen bij bevestigde bedoeling: nadat het besluit is vastgesteld.
- Grond: Onderzoeksinterpretatie B van ASTRA; synthetisch, nog onafhankelijk te beoordelen
- Relaties: INT-03, CON-02
- Uitvoering: huidige service op beide laadpaden; normkwaliteit niet automatisch gemeten; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E05 — driehoek

- Invoer: 'veelhoek met drie zijden'
- Bedoeling/informatie: Driezijdige veelhoek.
- G: Behoud deze kern.
- T: Voldoet aan INT-03 na vaststelling dat verwijzende voornaamwoorden ontbreken; alternatief niet van toepassing vraagt productkeuze.
- H: Geen herstel.
- Grond: Onderzoeksinterpretatie B van ASTRA; synthetisch, nog onafhankelijk te beoordelen
- Relaties: INT-03
- Uitvoering: huidige service op beide laadpaden; normkwaliteit niet automatisch gemeten; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E06 — pijl

- Invoer: 'teken dat een richting aangeeft'
- Bedoeling/informatie: Dat verwijst naar teken.
- G: Behoud relatieve bijzin.
- T: Voldoet: dat → teken.
- H: Geen herstel.
- Grond: Onderzoeksinterpretatie B van ASTRA; synthetisch, nog onafhankelijk te beoordelen
- Relaties: INT-03, INT-01
- Uitvoering: huidige service op beide laadpaden; normkwaliteit niet automatisch gemeten; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E07 — kennisgeving

- Invoer: 'bericht van een medewerker aan een leidinggevende over zijn besluit'
- Bedoeling/informatie: Zijn kan de medewerker of de leidinggevende aanduiden.
- G: Vraag wiens besluit of gebruik gegeven bedoeling.
- T: Voldoet niet wegens twee plausibele bezitters; bedoelde bezitter nog onbekend.
- H: Geen automatische keuze; vraag wiens besluit.
- Grond: Onderzoeksinterpretatie B van ASTRA; synthetisch, nog onafhankelijk te beoordelen
- Relaties: INT-03
- Uitvoering: huidige service op beide laadpaden; normkwaliteit niet automatisch gemeten; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E08 — verzending

- Invoer: 'handeling waarbij, zodra deze gereed is, de aanvraag wordt verzonden'
- Bedoeling/informatie: Deze wijst vooruit naar de aanvraag.
- G: Vooruitverwijzing mag als ondubbelzinnig; voorkeur heldere volgorde.
- T: Beoordeling nodig: grammaticale vooruitverwijzing is geen overtreding op zichzelf; handeling/aanvraag moeten worden afgewogen.
- H: Bij bevestigde bedoeling voorstel: handeling waarbij de aanvraag wordt verzonden zodra de aanvraag gereed is; controleer geen nieuwe betekenis.
- Grond: Onderzoeksinterpretatie B van ASTRA; synthetisch, nog onafhankelijk te beoordelen
- Relaties: INT-03, INT-01, INT-02
- Uitvoering: ontwerpgeval, niet uitgevoerd; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E09 — aanvraag

- Invoer: 'verzoek waarbij deze schriftelijk wordt ingediend'
- Bedoeling/informatie: Deze zou naar het lemma aanvraag verwijzen, niet grammaticaal naar het onzijdige verzoek.
- G: Formuleer zelfstandig: schriftelijk ingediend verzoek, mits betekenis gelijk.
- T: Onder voorgestelde norm voldoet niet als het losse lemma het ontbrekende antecedent moet leveren; alternatief lemma meetellen is expliciet normbesluit.
- H: Geen blinde vervanging door aanvraag vanwege CON-CIRC-001; herformuleren na betekeniscontrole.
- Grond: Onderzoeksinterpretatie B van ASTRA; synthetisch, nog onafhankelijk te beoordelen
- Relaties: INT-03, CON-CIRC-001, STR-02
- Uitvoering: ontwerpgeval, niet uitgevoerd; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E10 — regenperiode

- Invoer: 'periode waarin het regent'
- Bedoeling/informatie: Het is onpersoonlijk, geen te zoeken ding.
- G: Behoud onpersoonlijk het.
- T: Geen INT-03-overtreding; niet kunstmatig antecedent eisen.
- H: Geen herstel.
- Grond: Taalkundige uitzondering als voorstel; afzonderlijke bronverdieping nog nodig
- Relaties: INT-03
- Uitvoering: ontwerpgeval, niet uitgevoerd; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E11 — toegangsrecht

- Invoer: 'recht voor iedereen op toegang'
- Bedoeling/informatie: Iedereen duidt een bereik aan, geen vooraf genoemd zelfstandig naamwoord.
- G: Behoud als universeel bereik werkelijk bedoeld is.
- T: Geen afkeur alleen wegens ontbreken eerder zelfstandig naamwoord; bereik en bronbetekenis controleren.
- H: Geen fictief antecedent toevoegen.
- Grond: Onze Taal noemt onbepaalde voornaamwoorden; toepassing INT-03 is voorstel
- Relaties: INT-03, CON-02, ESS-05
- Uitvoering: ontwerpgeval, niet uitgevoerd; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E12 — machtiging

- Invoer: 'toestemming waarmee deze een aanvraag indient'
- Bedoeling/informatie: Bronpassage noemt vertegenwoordiger; kern noemt deze persoon niet.
- G: Gebruik alleen bevestigde actor, behoud bronpassage apart.
- T: Losse kern voldoet niet; bron kan bedoeling aantonen maar repareert de kern niet.
- H: Voorstel met vertegenwoordiger uitsluitend wanneer bron dat ondersteunt.
- Grond: Onderzoeksinterpretatie B van ASTRA; synthetisch, nog onafhankelijk te beoordelen
- Relaties: INT-03, ARAI-05, CON-02
- Uitvoering: ontwerpgeval, niet uitgevoerd; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E13 — overdracht

- Invoer: 'handeling van een medewerker aan een collega waarbij deze vertrekt'
- Bedoeling/informatie: Niet gegeven wie vertrekt.
- G: Vraag of medewerker of collega vertrekt.
- T: Voldoet niet wegens beide plausibele antecedenten; herstelbedoeling ontbreekt.
- H: Geen keuze op basis van dichtstbijzijnde woord.
- Grond: Synthetische herneming historische N; historische N behoudt eigen identiteit
- Relaties: INT-03
- Uitvoering: ontwerpgeval, niet uitgevoerd; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E14 — leeg

- Invoer: ''
- Bedoeling/informatie: Geen definitie aangeboden.
- G: Vraag definitietekst/benodigde inhoud.
- T: Niet beoordeeld wegens ontbrekend toetsobject; geen inhoudelijke pass of fail INT-03.
- H: Geen herstel van verzonnen definitie.
- Grond: Onderzoeksinterpretatie B van ASTRA; synthetisch, nog onafhankelijk te beoordelen
- Relaties: INT-03, VAL-EMP-001
- Uitvoering: huidige service op beide laadpaden; normkwaliteit niet automatisch gemeten; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E15 — bericht

- Invoer: 'bericht van een medewerker over zijn besluit'
- Bedoeling/informatie: Bron zegt besluit medewerker; gebruikersbedoeling zegt besluit leidinggevende.
- G: Stop op bron-/bedoelingsconflict.
- T: Verwijzing in tekst kan duidelijk zijn; betekenisconflict afzonderlijk, niet automatisch INT-03-fail.
- H: Geen wijziging totdat conflict is opgehelderd.
- Grond: Onderzoeksinterpretatie B van ASTRA; synthetisch, nog onafhankelijk te beoordelen
- Relaties: INT-03, CON-02
- Uitvoering: ontwerpgeval, niet uitgevoerd; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E16 — verzoeker

- Invoer: 'persoon die een aanvraag indient'
- Bedoeling/informatie: Die verwijst naar persoon; hypothetische evaluator noemt die fout.
- G: Behoud correcte tekst.
- T: Voldoet; hypothetische fail is evaluatorfout, geen generatieovertreding.
- H: Herstel evaluator/signaalduiding, niet de definitie.
- Grond: Onderzoeksinterpretatie B van ASTRA; synthetisch, nog onafhankelijk te beoordelen
- Relaties: INT-03, INT-01
- Uitvoering: ontwerpgeval, niet uitgevoerd; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E17 — vertegenwoordiger

- Invoer: 'persoon die namens een aanvrager diens aanvraag indient'
- Bedoeling/informatie: Diens hoort bij aanvrager.
- G: Behoud rolrelatie en bezitsrelatie.
- T: Voldoet indien diens ondubbelzinnig aanvrager aanduidt; geen herstel tot vertegenwoordigersaanvraag.
- H: Verwerp voorstel dat aanvrager vervangt door vertegenwoordiger; betekenisverlies.
- Grond: Onderzoeksinterpretatie B van ASTRA; synthetisch, nog onafhankelijk te beoordelen
- Relaties: INT-03, CON-02, CON-CIRC-001
- Uitvoering: ontwerpgeval, niet uitgevoerd; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## INT03-B-E18 — pijl

- Invoer: 'teken dat een richting aangeeft'
- Bedoeling/informatie: Synthetische technische fout vóór inhoudelijk oordeel.
- G: Bestaande kandidaat behouden.
- T: Technische fout, geen pass/fail; afzonderlijk van E06 omdat de uitvoervoorwaarde verschilt.
- H: Stop; herstart beoordeling pas na technisch herstel.
- Grond: Ontworpen foutcontract, niet geïnjecteerd in deze proef
- Relaties: INT-03
- Uitvoering: ontwerpgeval, niet uitgevoerd; werkelijk resultaat indien uitgevoerd: `proefuitkomsten-b-v1.json`, selector ID.

## Effectevaluatie en grenzen

De 18 gevallen zijn ontwerpgevallen, geen onafhankelijke juridische goldset. Vóór echte effectmeting laat A een onafhankelijke deskundige minimaal zes nieuwe, niet bij promptontwerp gebruikte varianten vastleggen: relatieve verwijzing, bezit, vooruitverwijzing, onpersoonlijk het, verwijzing naar een hele gebeurtenis en bronconflict. Behoud die verwachtingen en beoordeel oude/nieuwe uitkomsten blind. De aantallen zijn een voorgesteld kleinschalig ontwerp, geen statistische garantie. Zie Q6 in aanvulling-b-v1.md voor eigenaarschap en uitvoering.
