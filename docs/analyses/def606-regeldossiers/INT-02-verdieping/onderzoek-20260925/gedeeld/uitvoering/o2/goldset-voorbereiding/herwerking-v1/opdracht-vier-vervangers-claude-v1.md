# DEF-835 — vier goedgekeurde inhoudelijk nieuwe vervangers voorbereiden

Je bent tekstredacteur voor vier **synthetische** INT-02-testgevallen in een verse Claude Code CLI-sessie. Dit is documentwerk. Voer de opdracht zelf uit, zonder agents of herdelegatie. Je bent niet alleen in de repository. Lees de bronnen met Read/Glob/Grep; wijzig of verwijder geen bestanden. Lever uitsluitend JSON als definitief antwoord. De coördinator bewaart dat in een nieuw dossierbestand en controleert de toegestane inhoud.

## Grondslag en bronnen

Lees deze bestanden volledig vóór je de vier voorstellen opstelt:

1. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/normcontract.md` — norm en statusgrenzen.
2. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/besluiten-chris.md` — besluitenbasis.
3. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/ontwerpregister.md` — ontwerpgevallen; nieuwe gevallen moeten inhoudelijk zelfstandig zijn.
4. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/herwerking-v1/casuspool-kandidaat-v3.json` — 40 actuele kandidaten; hieronder zijn vier expliciet uit de beoogde selectie gehaald. Gebruik de andere 36 als overlapcontrole. Wijzig deze pool niet.
5. De vier nieuwe selectiebesluiten onder `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/`: `besluit-chris-g001-v2.md`, `besluit-chris-g005-v2.md`, `besluit-chris-g016-v2.md`, `besluit-chris-g023-v2.md`.
6. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/kwalificatieprotocol-v1.md` — bestaande vier families, selectiecriteria en procedurele scheiding; je mag dit protocol niet wijzigen.

De eerdere toestemming voor beperkte externe verwerking geldt voor deze synthetische gevallen, normteksten en besluiten. Gebruik geen appcode, modelkwalificatie-uitkomsten, andere dossiers, web, API, productiedata of Gitacties. Je ziet kandidaten die later mogelijk eindtest worden; je mag later geen O2-promptontwikkelaar of appimplementator zijn.

## Concrete opdracht

Bereid precies vier inhoudelijk nieuwe vervangers voor:

- `G053` vervangt G001;
- `G054` vervangt G005;
- `G055` vervangt G016;
- `G056` vervangt G023.

De oude vier blijven intact als aanvullend ontwikkelmateriaal buiten de beoogde 40. Nieuwe gevallen mogen geen herschrijving van die vier met andere namen, actoren of objecten zijn. Zij moeten ook voldoende inhoudelijk verschillen van de overige 36 en van de 76 ontwerpgevallen. Elk geval heeft een eigen functiegrens of bronrelatie die INT-02 werkelijk toetst. Spreid de inhoudelijke situaties waar mogelijk, maar forceer geen family- of labelaantallen. Vermijd nieuwe onbewezen premissen, kunstmatige bronconflicten en sturende tekst die het normantwoord voorzegt. Fictieve bronnen mogen concrete regels, gebeurtenissen en begripskenmerken bevatten; markeer herkomst expliciet. Geen juridische geldigheidsclaim.

Neem per nieuwe kandidaat exact deze zeven velden op: `id`, `herkomst`, `begrip`, `kern`, `bedoeling`, `context`, `bronnen`. `context` bevat de lijsten `organisatorische_context`, `juridische_context`, `wettelijke_basis`. Iedere bron bevat `id`, `tekst`, `herkomst`. Gebruik voor herkomst van nieuwe gevalobjecten en nieuwe bronnen: `Synthetisch concept, voorbereid door Claude Code CLI op 30 september 2026 op basis van individuele besluiten van Chris; geen praktijk- of expertbewijs.` De context vermeldt fictie en geen claim over bestaand recht. Geen persoonsgegevens.

Geef geen label, verwachte status, familie of split in de gevalobjecten, en geef ook elders geen voorgekookt goldlabel. De onafhankelijke beoordelaars en Chris bepalen dat later. Geef per geval in een afzonderlijk selectiepunt aan wat inhoudelijk nieuw is tegenover het vervangen geval en de drie dichtstbijzijnde G- of C-gevallen. Als een kandidaat onvoldoende zelfstandig blijkt, zeg dat eerlijk in het selectiepunt en stel geen oppervlakkige variant voor. Bewaar de concrete betekenisgrond bij iedere casus.

## Exacte uitvoer

Geef uitsluitend één geldig JSON-object, zonder Markdown of tekst erbuiten:

```
{
  "status": "concept_niet_geaccepteerd",
  "normversie": "def771-int02/2",
  "vervangers": [vier volledige gevalobjecten in ID-volgorde G053..G056],
  "mapping": [
    {"oud": "G001", "nieuw": "G053", "besluitbestand": "besluit-chris-g001-v2.md"},
    {"oud": "G005", "nieuw": "G054", "besluitbestand": "besluit-chris-g005-v2.md"},
    {"oud": "G016", "nieuw": "G055", "besluitbestand": "besluit-chris-g016-v2.md"},
    {"oud": "G023", "nieuw": "G056", "besluitbestand": "besluit-chris-g023-v2.md"}
  ],
  "selectiepunten": [vier objecten met nieuw_id, inhoudelijk_verschil, nabije_ids, bronsteun, zelfstandig_of_herzien],
  "bewijsgrenzen": [korte Nederlandse teksten]
}
```

Controleer vóór de definitieve uitvoer: vier unieke nieuwe IDs, geldige structuur en synthetische herkomst; geen wijziging van de 40 bestaande gevallen; geen oppervlakkige variant; geen expliciete of impliciete labels; geen quota- of splittoewijzing. Als de opdracht voor een van de vier zonder kunstgreep niet haalbaar is, geef voor die positie geen ondeugdelijk geval maar leg het concrete probleem vast in het overeenkomstige selectiepunt en vermeld het ontbrekende ID. Nieuwe labels en inhoud zijn nog niet door Chris geaccepteerd.
