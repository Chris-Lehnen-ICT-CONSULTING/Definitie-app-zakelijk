# Definitief appbesluit — geen totaalscore als kwaliteitsoordeel

15 september 2026 · versie 1 · **besloten door Chris; geen softwareoplevering**.

## Besluit en autorisatie

De totaalscore vervalt appbreed als **kwaliteitscijfer, acceptatiecriterium en stuurmiddel voor hergeneratie**. Dit vervangt de tijdelijke productkeuze ‘totaalscore niet beschikbaar’. Er wordt geen nieuwe formule of vervangend kwaliteitspercentage ingevoerd.

Bron: gesprek ‘Onderzoek DEF-606 en toetsregels’, taak `01a08f9d-a779-7382-b062-d0b38524a42f`. Chris antwoordde op 15 september 2026 **‘ja’** op het concrete voorstel en de vraag: ‘Wil je dit als definitieve appbrede keuze vastleggen, ter vervanging van de tijdelijke keuze “totaalscore niet beschikbaar”?’ Onderstaande onderdelen stonden in dat voorstel.

## Het vervangende overzicht

| Onderdeel | Vastgelegde richting |
|---|---|
| Toetsuitkomsten | Per regel het oordeel, de onderbouwing en eventuele vervolgstap. |
| Volledigheid | Welke controles daadwerkelijk zijn uitgevoerd, ontbreken of technisch mislukten. |
| Benodigde acties | Welke inhoudelijke fouten en open vragen aandacht vragen. |
| Expertbeoordeling | Of de actuele definitieversie is beoordeeld en handmatig vastgesteld. |

- Een inhoudelijke overtreding wordt niet gecompenseerd door positieve uitkomsten op andere regels.
- Een ontbrekende beoordeling telt niet als geslaagd en niet als inhoudelijke fout.
- Een telling van uitkomsten mag het overzicht ondersteunen, maar wordt geen percentage ‘definitiekwaliteit’.
- Eventuele interne technische scores krijgen geen zelfstandige beslissingsbevoegdheid.

## Doorwerking en grenzen

Dit is een **appbrede** keuze onder DEF-606. Het wijzigt niet automatisch de norm, toepasselijkheid, ernst, individuele scorepolicy of reviewplicht van alle afzonderlijke toetsregels. Die blijven per regel te onderzoeken en besluiten. Het besluit betekent ook niet dat iedere bevinding zonder onderscheid alle gebruikershandelingen blokkeert: toegestane conceptopslag, betekenis van adviezen en concrete vaststel-/exportvoorwaarden volgen hun eigen contract.

CON-01 had al een afzonderlijk besluit om geen cijfer te geven (B-06). De nieuwe appbrede keuze vervangt B-01–B-10 niet; zij vult het eerder afzonderlijk gelaten totaalscorebeleid in. Expertbeoordeling en handmatige vaststelling blijven vereist; een positief automatisch overzicht stelt niet vast.

De precieze migratie van bestaande UI-, API-, opslag-, export- en generatieconsumers vraagt een uitvoeringsplan binnen de bestaande eigenaarschappen. Dit besluit is geen opdracht om nu code, schema's, historische gegevens of skills te verwijderen of te veranderen. Het trekt eerder afzonderlijk verleende uitvoeringsopdrachten niet in.

## Relevante bestaande eigenaren en actualiteit

- [DEF-624 — classificatie en resultaatcontract](https://linear.app/definitie-app/issue/DEF-624): gelezen op 15 september 2026; de issueactualisatie van die dag noemt de totaalscore nog **tijdelijk** niet beschikbaar en houdt score-uitwerking open. Die beleidsomschrijving is met dit latere besluit achterhaald voor de appbrede totaalscore. Classificatie, semantisch bewijs, dekking en consumer-/resultaatcontractwerk blijven relevant; dit besluit voltooit het issue niet.
- [DEF-622 — CON-01-contextcontract](https://linear.app/definitie-app/issue/DEF-622): bestaande implementatietaak moet de definitieve richting kennen; geen dubbele implementatie starten.
- [DEF-626 — validatiesnapshots](https://linear.app/definitie-app/issue/DEF-626) en [DEF-630 — vaststel-/exportvoorwaarden](https://linear.app/definitie-app/issue/DEF-630): betrekken bij de migratie van resultaatconsumers en beslisvoorwaarden; het besluit vervangt niet hun volledige contract.

Deze registratie wijzigt geen Linear-omschrijving of issuestatus. De CON-01-hoofdsessie en bestaande implementatietaak ontvangen de besluitnotitie om hun actuele basis hiermee aan te vullen.

## Onderbouwing en toekomstig acceptatiebewijs

Het [gezamenlijke CON-01-besluitvoorstel v2](def606-regeldossiers/CON-01-verdieping/generatie-toetsing-vervolg-20260914/gezamenlijk-besluitvoorstel-generatie-v2.md) en het [casusregister v2](def606-regeldossiers/CON-01-verdieping/generatie-toetsing-vervolg-20260914/casusregister-generatie-v2.md) laten op de daar gebonden codeversie zien dat een hogere totaalscore geen betere begripsafbakening bewijst. De proefwaarnemingen worden hier niet als actuele meting van inmiddels gewijzigde code gepresenteerd. De rechtstreekse grond voor de beleidswijziging is Chris' expliciete besluit.

Bij afzonderlijk opgedragen uitvoering aantonen:

1. De actieve gebruikersweergave presenteert geen geaggregeerd kwaliteitscijfer of vervangend kwaliteitspercentage.
2. Acceptatie en herstelkeuzes gebruiken geen totaalscore als beslisgrond; relevante regelbevindingen, bewijs, uitvoeringsstatus en vereiste beoordeling blijven herkenbaar.
3. Positieve andere regels compenseren een vastgestelde overtreding niet. Een technische fout of ontbrekende beoordeling levert geen inhoudelijke pass of fail op.
4. Het overzicht onderscheidt uitkomsten, uitgevoerde controles, open acties en actuele expertbeoordeling; tellingen suggereren geen kwaliteitsmeting.
5. Handmatige vaststelling en toegestane conceptopslag blijven volgens hun bestaande voorwaarden werken. Consumercompatibiliteit wordt expliciet gemigreerd, niet door ontbrekende scores stil naar nul of één te converteren.

Deze acceptatiepunten zijn afgeleid van het besluit en **nog niet door deze registratie uitgevoerd**.
