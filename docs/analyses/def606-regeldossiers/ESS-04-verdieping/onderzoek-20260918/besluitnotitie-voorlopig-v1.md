# ESS-04 — voorlopige beslisnotitie van Codex

18 september 2026. Zelfstandig voorstel; geen vastgestelde norm of geïntegreerde synthese. Cowork-onderzoek, beide reviews/verwerkingen en synthesecontrole ontbreken. Zie [status en hervatting](statusmanifest-v1.md).

## Aanbevolen norm

**De definitie beschrijft kenmerken waarmee binnen de bedoelde betekenis en context navolgbaar kan worden beoordeeld of een geval onder het begrip valt.**

Kwalitatieve criteria kunnen volstaan. Getallen bewijzen op zichzelf geen toetsbaarheid, juiste betekenis of bronsteun. Ontbrekend bewijs over één geval bewijst evenmin dat de definitie ondeugdelijk is. Dit is een lokale operationalisering; de actuele oorspronkelijke ASTRA-passage kon niet worden geverifieerd.

Drie onderscheidende voorbeelden uit het [casusregister](casusregister-v1.md):

- Een speelkaart met blauwe achterzijde kan binnen een vastgelegde kleurindeling toetsbaar zijn zonder cijfer (N05).
- “Object dat minimaal 80% voldoet” mist criterium en noemer; het cijfer vult die niet aan (historisch ambiguous_measure).
- “Meer dan 80%” is toepasbaar maar wijkt af als de bron “minimaal 80%” voorschrijft. Het geval 80/100 onderscheidt toetsbaarheid van bronjuistheid (N07).

## Gevolgen voor generatie, toetsing en herstel

Generatie gebruikt beschikbare betekenisgrond en behoudt relevante populatie, grens en tijd. Geen willekeurige drempel toevoegen om meetbaarheid te suggereren. Toetsing beoordeelt de oorspronkelijke kern; context, bron en toelichting blijven afzonderlijk bewijs. Een signaal of review_required-status is geen uitgevoerd menselijk oordeel. De aansluiting van ESS-04 op gedeelde beoordelingsopslag is nog niet aangetoond.

Herstel onderscheidt generatieovertreding, brongebrek, transportverlies, tegenstrijdige instructies, onjuiste evaluatoruitkomst, technische fout en betekenisverlies bij nabewerking. Alleen een afzonderlijk voorstel maken als de grond voor correctie beschikbaar is. Automatisch herstel blijft uitgesteld.

[Exacte tekstvoorstellen](instructievoorstellen-v1.md) bevatten norm, G/T/H-instructies, voorbeelden, gebruikersmeldingen en wijzigingen voor de vijf betrokken skills. Ze zijn nergens toegepast.

## Werkelijk bewijs

Vier beperkte offline proeven op commit 4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb tonen:

- ESS-04 blijft review_required, ook met fictieve pass-/reviewermetadata.
- Actuele normalisatie bewaart reviewstatus en dekking. Het transportverlies in de oudere werkboom is geen actuele bevinding. Ontbrekende runstatus wordt unknown.
- De concrete generatie-instructie benadrukt nog deadlines, aantallen en percentages. Geen live modeluitkomst getest.
- Eén partijzin behoudt grens, noemer en peildatum bij extractie/cleaning. Opslag en de volledige gebruikersroute zijn niet uitgevoerd.

Het [bewijsregister](bron-bewijsregister-v1.md) scheidt waarnemingen van voorstellen. Zeven historische gevallen zijn behouden en 23 nieuwe gevallen uitgewerkt; de meeste zijn acceptatieontwerpen. [Verificatie](verificatie-v1.json) bevestigt bronkopieën, codehashes, lokale verwijzingen en beschreven loguitkomsten; geen inhoudelijke expertacceptatie.

## Keuzes na wederzijdse review

| Keuze | Voorlopig Codex-advies | Onderscheidend geval of gevolg |
|---|---|---|
| Norm | Voorgestelde norm zonder cijferplicht | N05 kwalitatief; N07 meetbaar maar verkeerde bronafbakening |
| Bewijscontext | Alleen gegevens eisen die toepassing of herleidbaarheid bepalen | N08 noemer; N12 bronversie; N17 ontbrekend gevalsbewijs |
| Menselijke beoordeling | Integreren in bestaande expertreview; geen AI-jury afleiden uit buurregels | P01: metadata is geen oordeel; opslag/readback nog te bewijzen |
| Zelfstandige ESS-04-poort | Nu geen extra blokkade afleiden uit ernst/scorepolicy | Open ESS-04-keuze, geen reeds vastgesteld ESS-01/02-besluit |
| Twee beoordelaars | Gerichte kalibratie en risicogevallen | N15 toepassingsfout tegenover N16 betekenisverschil; geen algemene tweepersoonsverplichting |

Bestaande besluiten over context, bronbasis, ESS-01/02 en vervallen totaalscore blijven behouden. Nieuw bewijs is nodig voor de actuele ASTRA-norm, deskundige casuslabels en de echte beoordelings-/opslag-/exportketen. Besluitvorming en uitvoering volgen na voltooiing van het afgesproken onderzoek.

Volledige onderbouwing: [Codex-onderzoek Q1–Q6](codex-onderzoek-v1.md).
