# INT-02 O2 — bundelvoorstel voor de zeven open kandidaatgevallen (v1)

30 september 2026. Besluitvoorstel, **geen goldbesluit, splitsing of freeze**. Chris' laatste akkoord in de chat is opgevat als akkoord op gebundelde bespreking. Het was geen afzonderlijke inhoudelijke acceptatie van G049. Als Chris een andere bedoeling had, blijft dit uitsluitend een voorstel.

## Bron en controle

- De te bespreken inhoud staat in `../herwerking-v1/casuspool-kandidaat-v4.json`, SHA-256 `2c1919ee143f11551d9cb643667243ecb610769aa528548286a9fe4c7bbdbe64`. De pool bevat 40 unieke kandidaten en vervangt in die selectie G001/G005/G016/G023 door G053–G056. Oudere gevallen blijven bewaard.
- G049/G051/G052 zijn onafhankelijk beoordeeld in `../herwerking-v1/samengevoegde-voorstellen-v1.json`. G053–G056 zijn door twee verse CLI-sessies beoordeeld in `../herwerking-v1/beoordeling-vier-a-met-posities-v1.json` (SHA-256 `3f0b5d941523503d0069d0350bac49937de04376cd6abf17e9423e196388df43`) en `../herwerking-v1/beoordeling-vier-b-met-posities-v1.json` (SHA-256 `c270a4e9319b61f3270cee5ad01655f1c96b09e527c94c111ec71ec23870df2d`). Voor deze vier zijn alle 40 passages en gronden opnieuw op exacte citaatposities in de v4-pool gecontroleerd: 40/40 geldig.
- De twee annotatoren stellen voor alle zeven dezelfde hoofdstatus voor. Bij G055 en G056 verschillen zij over de familie; Chris' keuze daarover blijft nodig. De bron is synthetisch en vormt geen praktijk- of expertbewijs.

## Voorstel per open geval

| Geval | Voorstel voor hoofdstatus | Familievoorstel | Waarom en afbakening |
| --- | --- | --- | --- |
| **G049 — jaarverslag** | `fail` | `actorvoorschrift_procedure_discretie` | De statutaire voorleggingsplicht vóór 1 april is in de kern overgenomen; een verslag dat pas in mei is voorgelegd, heet volgens de fictieve bron en bedoeling nog steeds jaarverslag. Beide annotatoren: `fail`, zelfstandig. Vervanger van G032. |
| **G051 — noodopvangplaats** | `fail` | `actorvoorschrift_procedure_discretie` | De kern gebruikt het dagelijkse vrijhouden tot 23.00 uur door de begeleider, terwijl de bedoelde categorie volgens de capaciteitsplanning uit aangewezen bedden bestaat. Beide: `fail`, zelfstandig. De verhouding tussen vaste aanwijzing en dagelijkse bedkeuze blijft een afzonderlijke betekenisvraag. Vervanger van G038. |
| **G052 — voorrangsaanvraag** | `fail` | `actorvoorschrift_procedure_discretie` | De aangeboden kern is een imperatieve afwegings- en voorrangverleningsstap, gericht aan de intakemedewerker. Het geregistreerde resultaat in B2 maakt de imperatieven niet beschrijvend. Beide: `fail`, zelfstandig. Vervanger van G040. |
| **G053 — reiskostenvergoeding** | `fail` | `actorvoorschrift_procedure_discretie` | De administratie krijgt achtereenvolgens berekenen, begrenzen en overmaken als handelingen; de overdracht is zelfstandig een uitvoeringsopdracht. Een deterministische berekening maakt die opdracht niet tot een begripsafleiding. Beide: `fail`, zelfstandig. Inhoudelijk nieuwe vervanger van G001. |
| **G054 — eerstgerechtigde inschrijving** | `pass` | `begripscriterium_afleiding` | De hoogste wachtpunten en bij gelijkstand het laagste inschrijfnummer vormen een deterministische rangschikking. Het afzonderlijke aanbodvoorschrift voor het bestuur staat alleen in de bron. Beide: `pass`, zelfstandig. Het toepassingsbereik bij meerdere vrijgekomen tuinen op één dag kan elders verduidelijking vragen; dit verandert het INT-02-voorstel niet. Vervanger van G005. |
| **G055 — openbare vergadering** | `pass` | voorstel `normatief_begrip` | De kern beschrijft de status van een ledenraadsvergadering zonder voorafgaande beslotenverklaring. De discretionaire privacyafweging staat alleen in de bron. Beide: `pass`, zelfstandig. A noemt de familie `normatief_begrip`, omdat een genomen beslissing de status bepaalt; B noemt `begripscriterium_afleiding`, omdat de kern een negatief statuscriterium bevat. Voorstel: A's familie, omdat het normatief bepaalde vergaderstatus betreft; het label hangt daar niet van af. Vervanger van G016. |
| **G056 — zaalwacht** | `pass` | voorstel `normatief_begrip` | De kern karakteriseert de gedefinieerde medewerkerstaak; zij draagt een derde of de lezer geen stap op. Beide: `pass`, zelfstandig. A noemt de familie `normatief_begrip` wegens de rol en bijbehorende taken; B `begripscriterium_afleiding` wegens de functieomschrijving. Voorstel: A's familie. Of een aangewezen medewerker die de taken feitelijk niet uitvoert nog zaalwacht is, blijft een afzonderlijk afbakeningspunt buiten het INT-02-oordeel. Vervanger van G023. |

De familievoorstellen voor G055/G056 dienen uitsluitend de testdekking en veranderen het geadviseerde hoofdlabel niet. Als Chris een andere familie kiest, worden de hieronder genoemde aantallen opnieuw berekend.

## Stopregel vóór 24/16-splitsing

Van de 40 kandidaten hebben **33** al een inhoudelijk besluit in deze chat: 23 `pass`, 7 `fail` en 3 `review_required`. Als alle zeven voorstellen hierboven worden overgenomen, wordt de verdeling **26 `pass`, 11 `fail`, 3 `review_required`**. Met de voorgestelde families van G055/G056 is de familieverdeling **11 begripscriterium, 15 normatief begrip, 11 actorvoorschrift, 3 ontbrekende/strijdige grond**.

Het geaccordeerde `kwalificatieprotocol-v1.md` plant **10 per familie**, verdeeld als 6 ontwikkeling en 4 hold-out. De bestaande pool kan dus geen geldige 24/16-splitsing volgens dat plan dragen: er ontbreken **zeven** echte onzekerheidsgevallen. Ook de hold-outeis van 3/4 juiste onzekerheidsuitkomsten veronderstelt vier van zulke gevallen. Labels omzetten voor een quotum is uitgesloten.

**Aanbevolen vervolgbesluit:** accepteer of corrigeer de zeven inhoudelijke voorstellen afzonderlijk binnen dit ene bundelbesluit; laat daarna zeven inhoudelijk nieuwe gevallen met werkelijk ontbrekende of strijdige betekenisgrond voorbereiden en onafhankelijk beoordelen. Selecteer pas op basis van hun kwaliteit welke zeven overschotgevallen als aanvullend ontwikkelmateriaal buiten de 40 blijven (bij deze familievoorstellen: vijf normatieve, één begripscriterium en één actorvoorschrift). Niets wordt verwijderd. Komt deze aanvulling niet tot zeven geldige `review_required`-gevallen, dan wordt het protocol expliciet herzien vóór een split. Geen modelkwalificatie of activering vóór geldige freeze.

## Gevraagd aan Chris

Eén bundelreactie volstaat: (1) akkoord of correcties per G049/G051/G052/G053/G054/G055/G056, inclusief de families van G055/G056; (2) akkoord op aanvullen met onafhankelijk beoordeelde onzekerheidsgevallen als route naar de bestaande 10-per-familie-verdeling. Een akkoord op dit voorstel autoriseert nog geen 24/16-splitsing, live modelproef of activering.
