# DEF-835 — zeven nieuwe synthetische gevallen met onzekere betekenisgrond

Je bent tekstredacteur in een **verse Claude Code CLI-sessie**. Doe dit documentwerk zelf, zonder agents of herdelegatie. Je bent niet alleen in deze repo; wijzig of verwijder geen bestanden. Lees uitsluitend de hieronder genoemde bronnen. Lever één geldig JSON-object als definitief antwoord; de coördinator bewaart het in een nieuwe dossierfile. Geen Git-, app-, web-, API- of productiedatahandelingen. Je mag later geen O2-promptontwikkelaar of appimplementator zijn, omdat je mogelijke eindtestgevallen ziet.

## Bronnen — volledig lezen vóór schrijven

1. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/normcontract.md` — INT-02-norm en resultaatgrenzen.
2. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/besluiten-chris.md` — besluitenbasis.
3. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/ontwerpregister.md` — 76 ontwerpgevallen, alleen om overlap te voorkomen.
4. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/herwerking-v1/casuspool-kandidaat-v4.json` — 40 actuele kandidaten, alleen om overlap te voorkomen. Wijzig deze pool niet.
5. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/kwalificatieprotocol-v1.md` — vier families en onafhankelijke beoordeling. Quota zijn een selectieplan; forceer er geen label of familie voor.

De gebruiker heeft de beperkte externe verwerking van synthetische gevallen, normteksten en besluiten eerder toegestaan. Alle voorbeelden en bronnen zijn fictief; vermeld geen geldend recht of persoonsgegevens. Lees geen individuele labelbesluiten, beoordelaarsvoorstellen, appuitkomsten of kwalificatieproef.

## Concrete opdracht

Bereid maximaal zeven **inhoudelijk nieuwe** conceptgevallen voor, met IDs `G057` tot en met `G063`. Het doel is de nog dun bezette familie waarin ontbrekende of strijdige betekenisgrond de **INT-02-functie** werkelijk onbeslist laat. Maak voor elk geval twee of meer concrete, synthetische bronnen en een neutrale gebruikersbedoeling die genoeg inhoud geven om het probleem te analyseren. Laat de bronnen een echte open keuze over de functie van een zinsdeel dragen: begripskenmerk of overgenomen handelingsregel. Een louter onbekende feitelijke waarde, een ander kwaliteitsgebrek of het woord “onduidelijk” zonder twee verdedigbare lezingen volstaat niet. Een zelfstandig bewezen voorschrift moet ook als zodanig herkenbaar blijven; presenteer dat niet kunstmatig als onzekerheid.

Maak zeven verschillende mechanismen/domeinen en vermijd oppervlakkige varianten van G042/G045/G047, de andere 37 G-kandidaten en de 76 C-ontwerpen. De nieuwe gevallen hoeven niet allemaal in de beoogde familie te belanden: onafhankelijke beoordelaars bepalen dat. Als je een geval niet zonder kunstgreep kunt construeren, laat het ID open en leg het inhoudelijke probleem in een selectiepunt uit. Maak geen bron die zelf het INT-02-oordeel voorschrijft. Benoem geen verwacht label, status, familie of split in de gevalobjecten of elders in je antwoord.

Ieder gevalobject heeft **exact** deze zeven velden: `id`, `herkomst`, `begrip`, `kern`, `bedoeling`, `context`, `bronnen`. `context` bevat exact de lijsten `organisatorische_context`, `juridische_context`, `wettelijke_basis`. Iedere bron heeft `id`, `tekst`, `herkomst`. Gebruik als geval- en bronherkomst: `Synthetisch concept, voorbereid door Claude Code CLI op 30 september 2026 voor DEF-835; geen praktijk- of expertbewijs.` De context vermeldt fictie en geen claim over bestaand recht. Bronverwijzingen en gebeurtenissen moeten intern consistent en controleerbaar zijn. Een bron mag tekst over een procedure bevatten, maar de procedure mag het te beoordelen oordeel niet al weggeven.

Geef per geval buiten het gevalobject een selectiepunt met `id`, `inhoudelijke_nieuwheid`, `nabije_ids`, `open_bronvraag`, `risico_op_triviale_variant`. Beschrijf de nabije G/C-casussen concreet. Beperk de tekst tot de relevante INT-02-functiegrens; geen stilzwijgende reparatie van de kern. De kandidaatpool blijft ongewijzigd.

## Exacte uitvoer

Geef uitsluitend JSON, zonder Markdownfences of tekst erbuiten:

{
  "status": "concept_niet_geaccepteerd",
  "normversie": "def771-int02/2",
  "gevallen": [maximaal zeven gevalobjecten in ID-volgorde G057..G063],
  "selectiepunten": [één object per aangeboden geval, plus eventuele concrete verklaring voor een ontbrekend ID],
  "bewijsgrenzen": [korte Nederlandse teksten]
}

Controleer vóór het antwoord: unieke IDs, zeven velden per geval, synthetische herkomst, neutrale bedoeling, intern consistente bronnen, geen labels en geen oppervlakkige variant. De coördinator en twee onafhankelijke beoordelaars controleren de voorstellen; jouw tekst is nog geen goldset.
