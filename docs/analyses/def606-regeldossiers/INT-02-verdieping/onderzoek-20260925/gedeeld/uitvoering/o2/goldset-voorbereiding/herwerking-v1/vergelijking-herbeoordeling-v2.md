# Herbeoordeling INT-02 O2 — actuele bespreekversie v2

29 september 2026. Vervolg op vergelijking-herbeoordeling-v1.md. De actuele kandidaatpool is v3; oudere stukken blijven als bewijs behouden.

## Uitgevoerd en gecontroleerd

- 15 herwerkingen en 12 vervangers voorbereid; 13 oorspronkelijke gevallen ongewijzigd behouden. De 40 zijn nog kandidaten.
- Twee onafhankelijke CLI-beoordelingen van de 27 nieuwe/gewijzigde gevallen uitgevoerd, gevolgd door gerichte correctie en hercontrole van G003/G006/G018/G030 en één laatste verwijzingscorrectie in G018-B1. Alle CLI-runs afgerond met exit 0.
- Alleen geautoriseerde velden gewijzigd; kernen van de herwerkingen intact. Hergebruik van eerdere beoordelingen per geval door exacte objectgelijkheid onderbouwd.
- Actuele combinatie: **158/158 citaten exact**, alle bronbindingen en IDs gecontroleerd. Tekenposities waar nodig mechanisch uit unieke citaatstrings afgeleid. Eén oorspronkelijke einde-index van A/G023 is in een bewaarde nieuwe versie gecorrigeerd.
- **20/27 labels gelijk, 7 verschillen.** Dit zijn voorstellen, geen door Chris geaccepteerde nieuwe goldlabels.

Bronnen: [actuele pool](casuspool-kandidaat-v3.json), [samengevoegde voorstellen met herkomst per geval](samengevoegde-voorstellen-v1.json), [manifest v3](manifest-kandidaat-v3.json). Poolhash: `e2ee47f91ef65e2cfe7c2b0001293ddc74e92627774243c8596e025865ea5857`. Voorstellenhash: `23a8b404fd21b178d31bb418b8cea785cf8ea253b6aa8e0f62502a773c12957c`.

## Actuele voorstellen

| ID | Begrip | A | B | Geschiktheid A / B |
|---|---|---|---|---|
| G001 | uitzonderingsroute | fail | fail | bruikbaar / uitsluiten |
| G002 | overnemende route | pass | pass | bruikbaar / bruikbaar |
| G003 | aangewezen referentie | review_required | pass | aanpassen / bruikbaar |
| G005 | vrije bufferruimte | pass | pass | bruikbaar / bruikbaar |
| G006 | aanvaardbaar arrangement | pass | pass | bruikbaar / bruikbaar |
| G014 | voldoende herstel | review_required | pass | bruikbaar / bruikbaar |
| G016 | toelaatbare afwijking | fail | fail | bruikbaar / uitsluiten |
| G018 | herroepbare uitzondering | review_required | pass | bruikbaar / bruikbaar |
| G021 | drempelbeslissing | pass | pass | bruikbaar / bruikbaar |
| G023 | getrapt meetinterval | pass | pass | bruikbaar / bruikbaar |
| G030 | actieve aanbieding | pass | pass | bruikbaar / bruikbaar |
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

## Wat de correcties hebben veranderd

- G003: aanwijzing en registratie zijn weer één gebeurtenis; ongevraagde intrekkings- en kalibratiestappen verwijderd uit de nieuwe bronversie. A blijft onzeker, B ziet een beschreven objectrelatie. Het verschil is inhoudelijk en blijft open.
- G006: bron bindt weer aan reeds aanvaarde arrangementen en het constitutieve oordeel. Beide reviewers nu pass; aanvullende register- en procedurepassages zijn niet automatisch een bronconflict. Chris moet de nieuwe versie nog accepteren.
- G018: ‘volgende dag’ vervangen door dezelfde ‘zodra’-grond als de kern; de losse verwijzing naar een niet-genoemd voorbehoud hersteld naar het beschreven kenmerk. Beide sluiten de bronfouten; A blijft review_required, B pass. Geen nieuwe correctieronde om overeenstemming af te dwingen.
- G030: de nominale zin staat als kopregel boven een samenhangende werkwijze. Beide reviewers nu pass. De oorspronkelijke onzekerheidsverwachting wordt niet voor een quotum gehandhaafd.

Dit beschrijft correcties aan nieuwe conceptbestanden; geen oorspronkelijke bron of geval verwijderd of overschreven.

## Inhoudelijke verschillen voor Chris

1. **G003:** volgens A blijft alternatieve regelversie/type tegenover gebruik onbeslist; volgens B zijn de passages verenigbaar en beschrijft de kern een objectrelatie. A betwijfelt bovendien of het onzekerheidsgeval vooral ESS/CON meet.
2. **G014:** volgens A vraagt statusbeschrijving tegenover registratieopdracht een keuze; volgens B beschrijft de kern de constitutieve registratie en staat de uitvoeringsdeadline alleen in de aanvullende bron.
3. **G018:** volgens A herhaalt de typebron de kern zonder voldoende zelfstandige grond; volgens B geeft het contrast vaste/herroepbare uitzonderingen precies die typegrond.
4. **G042:** volgens A een toegestaan afschermkenmerk; volgens B onbekend of de rode rand gerealiseerd hekwerk of een uit te voeren afscherming aangeeft.
5. **G045:** volgens A ‘is in te dienen’ als voorschrift; volgens B onvoldoende grond voor plicht tegenover mogelijkheid omdat de bronnen dezelfde constructie in beide functies gebruiken.
6. **G047:** volgens A overgenomen termijnplicht; volgens B onbekend of te late meldingen ook afmeldingen zijn, zodat de functie van de termijn openblijft.
7. **G050:** volgens A discretionaire uitzondering in de kern; volgens B beschreven bedrag met een vastgesteld percentage als parameter. B wijst daarnaast op het verschil tussen passend vinden en vaststellen en op de geldigheidsduur. Dat betekenis-/selectiepunt blijft open.

Deze opsomming is een vergelijking, geen adjudicatie. Labels worden niet bij meerderheid of via een quotum gekozen.

## Selectie en nog te accepteren inhoud

- **G001 eerst aan Chris voorgelegd:** beide fail; A bruikbaar met twijfel aan afstand, B uitsluiten wegens nabijheid tot C13/C83 en overlap met G016/G052. Voorstel coördinator: bewaren als ontwikkelmateriaal buiten de40 en nieuwe vervanger. Nog geen antwoord ontvangen op de asyncvraag; geen vervanging uitgevoerd.
- G016: vergelijkbaar selectiedispuut, nog niet voorgelegd als nieuwe vervangingskeuze.
- G039: beiden pass, familieverschil normatief_begrip tegenover begripscriterium_afleiding; nog expliciet afhandelen.
- Andere meerwaarde-/overlapvragen uit de individuele besluiten en reviewers blijven traceerbaar in de oorspronkelijke voorstellen. Gelijke labels betekenen niet automatisch voldoende onafhankelijke testwaarde.
- G035: nieuwe proefparameters zijn synthetische concretiseringen, geen eerder vastgelegde feiten. Beide vinden de INT-02-functie behouden; Chris accepteert de kandidaattekst nog.
- Alle nieuwe of gewijzigde versies vragen inhoudelijke acceptatie. Oude labels en akkoord op herwerking zijn geen automatische acceptatie van nieuwe tekst.
- Pas daarna definitieve selectie, haalbaarheid van vier families en 24/16-verdeling beoordelen. Een benodigde protocolwijziging vraagt een expliciet besluit; geen aantallen of labels stil aanpassen.

## Bewijsgrenzen

Geen appmodelkwalificatie of effectmeting uitgevoerd. Geen software-, Git-, Actions- of O2-activeringswijziging. DEF-626 blijft uitgesteld. Bronmateriaal is fictief/synthetisch; geen uitspraak over geldend recht. CLI-overeenstemming bewijst geen normjuistheid of appkwaliteit. Alle betrokken sessies zagen kandidaten voor de eindtest en worden niet hergebruikt voor O2-promptontwikkeling of implementatie.
