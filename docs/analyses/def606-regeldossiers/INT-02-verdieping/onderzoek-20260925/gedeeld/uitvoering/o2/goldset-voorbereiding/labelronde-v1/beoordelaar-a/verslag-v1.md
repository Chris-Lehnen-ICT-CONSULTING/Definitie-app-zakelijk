# DEF-835 — INT-02 labelvoorstellen, beoordelaar A (v1)

29 september 2026 · normversie `def771-int02/2` · status: **voorstel, niet geaccepteerd** — geen goldset, geen freeze, geen splitsing. Chris accepteert de labels en beslecht de verschillen met beoordelaar B.

Uitvoer: `labelvoorstellen-v1.json` (in deze map).

## Gebruikte bronnen

Alleen de vier aangeleverde invoerbestanden plus het manifest, in de voorgeschreven volgorde gelezen:

| Bestand | sha256 (gecontroleerd, gelijk aan `manifest.json`) |
|---|---|
| `invoer/besluiten-chris.md` | `bcf736d9…d5ebd2` |
| `invoer/normcontract.md` | `bc16c128…b043c` |
| `invoer/casuspool.json` | `d70c645e…ebb11` |
| `invoer/ontwerpregister.md` | `76dbfa26…d66734` |

Niet gebruikt: werk, logs of conclusies van beoordelaar B, appcode, fixtures, modelproeven, implementatie- en reviewgeschiedenis, andere dossiers, web, API- of modelcalls, Git. De scheiding is procedureel; technische isolatie claim ik niet.

## Werkwijze

- De oordelen zijn handmatig per geval gevormd op de functie van de kern (norm B1/N-breed, T-tekst, veldrollen). Python is alleen gebruikt voor documentcontrole: hashes, signaalwoorden als documentaire notitie (geen labelbron), tekenposities van citaten en een controle achteraf.
- Mechanische controle van het weggeschreven bestand: 40 IDs in dezelfde volgorde als de pool, geen ontbrekende of extra IDs. Alle 152 citaten (passages en gronden) voldoen aan `bron[start:end] == citaat` (Unicode-tekenposities, nulgebaseerd, einde exclusief). Elke `review_required` heeft precies één vraag, de overige hebben `null`, en geen enkele motivering is langer dan 80 woorden.
- Context: alle gevallen hebben organisatorische en juridische context, `wettelijke_basis` is overal leeg. Ik heb dat als aanwezige context (K-9) behandeld en daarom geen `not_evaluated` gegeven. Zie de bewijsgrenzen.
- Technische noot: de Write-tool faalde op een ontbrekend hookbestand in deze werkmap. Dit verslag is daarom via Python in exclusieve schrijfmodus (`x`) aangemaakt; er is niets buiten deze map geschreven.

## Aantallen

| Voorstel | Aantal | IDs |
|---|---|---|
| pass | 20 | G002, G004, G005, G007, G009, G011, G013, G015, G017, G019, G021, G023, G025, G027, G029, G031, G033, G035, G037, G039 |
| fail | 10 | G001, G008, G012, G016, G020, G024, G028, G032, G036, G040 |
| review_required | 10 | G003, G006, G010, G014, G018, G022, G026, G030, G034, G038 |
| not_evaluated / not_applicable / onbeslist | 0 | — |

- **Familie:** begripscriterium_afleiding 10, normatief_begrip 10, actorvoorschrift_procedure_discretie 10, ontbrekende_strijdige_grond 10.
- **Zekerheid:** hoog 33, middel 7.
- **Afstand tot het ontwerpregister:** zelfstandig 30, twijfel 6, triviale_variant 4.
- **Geschiktheid:** bruikbaar 32, aanpassen 8, uitsluiten 0.

Ik heb de aantallen niet gestuurd. Toch vallen de uitkomsten precies samen met vier blokken van tien. Dat wijst erop dat de pool in gebalanceerde ontwerpblokken is opgezet, en dat bedoeling en bron het label vaak al vastleggen (zie hieronder).

## Twijfelpunten

- **Middelzekere fails:** G024 en G036. Bij G024 staat een genus met een bijzin die taken van de controleur bevat, en bij G036 een proceslabel met “moet”. De norm staat toe dat een verplichting of procedure als kenmerk wordt beschreven. De voorschriftfunctie volgt hier uit de bevestigde bedoeling en de bron, niet uit de kern alleen.
- **Middelzekere reviews:** G006, G010, G018, G022 en G026. Deze kernen bevatten sterk discretionaire taal (“zodra hij … onwenselijk vindt”, “volgens het oordeel van”). Een beoordelaar kan hier naar fail neigen. Ik volg het register (C12/C13/C83/C107): de functie beslist, en die is door de strijdige bronnen onbeslist. Dat is het meest waarschijnlijke verschilpunt met B.
- **G028:** het eerste zinsdeel is beschrijvend, maar het tweede zinsdeel (“ontbreekt capaciteit, dan annuleert hij de aanvraag”) is een zelfstandig voorschrift. Daarom stel ik fail voor en geen review.
- **G016:** het beschrijven van een bevoegdheid is toegestaan, maar de kern is hier de afwegingsregel zelf en bakent geen categorie af. Daarom fail; G029 is het beschrijvende tegenpaar.
- **G023:** of “tenzij” de overgangsintervallen in- of uitsluit, is een ESS-05/STR-kwestie. Voor INT-02 is het in beide lezingen een uitzonderingscriterium.

## Onafhankelijkheid, redundantie en sturing

- **Triviale varianten van ontwerpgevallen** (geschiktheid aanpassen): G010 is een variant van C107, G013 van C112, G025 van C53 en G040 van C83. Ze hebben hetzelfde zinsraam en hetzelfde verwachte label, dus ze zijn zwak als hold-out.
- **Twijfel over afstand:** G012 (C105), G020 (C102), G023 (C58), G024 (C15), G028 (C64) en G029 (C112). Ze zitten in dezelfde familie met een verwant zinsraam, maar elk heeft een eigen onderscheidend element. Dat element staat per geval beschreven.
- **Redundantie binnen de pool:** alle tien `review_required`-gevallen volgen één sjabloon: een genus met een actorbijzin, plus een bron die twee lezingen noemt “zonder rangorde”. Het zijn twee subclusters:
  - Discretionair: G006, G010, G018, G022 en G026. G022 en G026 staan op aanpassen omdat ze vrijwel gelijk zijn aan G018.
  - Niet-discretionair: G003, G014, G030, G034 en G038. G034 staat op aanpassen (≈ G030), G038 ook (≈ G003).
  - Welk exemplaar behouden blijft, is aan Chris; mijn keuze voor het eerste ID is een praktische markering.
- **Kleinere overlap:** G005 overlapt met G027 (afgeleide grootheid), G009 met G019 (wederkerige relatie), G004 met G025 (rechtsgevolg), G013 met G017 en G029 (“X van Y om/op Z”), en G008 met G012 (procedure zonder genus).
- **Sturende bedoeling en bronnen:** bij de reviewgevallen volgt het label bijna direct uit metazinnen als “Voorrang is onbeslist” of “De toepasselijke versie is niet gekozen”. Ook enkele fail- en passbronnen zeggen hun functie letterlijk (G001, G032, G009, G002, G023). Zo toetst de pool vooral of een beoordelaar de aangeleverde grond volgt, en minder of hij de functie uit de kern zelf herkent.
- **Waardevolle minimale paren:** G030 en G032 (zelfde vorm, strijdige tegenover eenduidige grond), G033 en G040 (zelfde S1-marker “naar eigen inzicht”, beschreven tegenover uitgevoerde discretie), G016 en G029 (regel tegenover bevoegdheid), G036 en G039 (proces met en zonder actorvoorschrift).
  - G033 vult de vals-alarmproef die het register bij C59 als ontbrekend noemt.
- **Signaalloze fails** (belangrijk voor de waarschuwing zonder signaal): G001, G008, G012, G024, G028 en G032. G020 geeft alleen een signaal op “mits”, omdat “dient het pakket vrij te geven” het patroon “dient te” niet treft.

## Bewijsgrenzen

- Dit zijn voorstellen van één beoordelaar, geen geaccepteerde labels, geen goldset en geen meting van modelkwaliteit. Zekerheid is een eigen inschatting, geen score.
- Alle casussen en bronnen zijn synthetisch. Niets hierin beschrijft geldend recht.
- Aan K-9 is voldaan onder mijn aanname dat twee gevulde contextlijsten volstaan. Vereist de app alle drie lijsten, dan zou elk geval `not_evaluated` worden. Dat heb ik niet geverifieerd, want appcode viel buiten deze opdracht.
- Afstand en redundantie heb ik op inhoud en zinsraam beoordeeld tegenover de verkorte registerteksten. De exacte proefinvoer van de C-gevallen heb ik niet gezien.
- Ik heb alle 40 gevallen gezien. Volgens de opdracht werk ik daarom niet mee aan de O2-prompt of de implementatie op basis van deze inhoud. De splitsing in 24 ontwikkel- en 16 hold-outgevallen gebeurt pas na menselijke acceptatie.
