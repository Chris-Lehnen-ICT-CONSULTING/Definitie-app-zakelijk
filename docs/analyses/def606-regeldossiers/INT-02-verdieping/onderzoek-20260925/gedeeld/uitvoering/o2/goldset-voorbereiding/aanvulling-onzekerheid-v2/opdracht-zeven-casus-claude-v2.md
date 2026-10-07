# DEF-835 — tweede reeks synthetische gevallen met werkelijk open functiegrond

Je bent tekstredacteur in een **verse Claude Code CLI-sessie**. Doe dit documentwerk zelf, zonder agents of herdelegatie. Je bent niet alleen in de repo; lees alleen de genoemde bronnen en wijzig of verwijder niets. Geen Git-, app-, web-, API-, modelkwalificatie- of productiedatahandelingen. Lever uitsluitend JSON als definitief antwoord. De coördinator bewaart het resultaat in een nieuw dossierbestand. Je mag later geen O2-promptontwikkelaar of appimplementator zijn, omdat je mogelijke eindtestgevallen ziet.

## Bronnen — volledig lezen

1. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/normcontract.md` — INT-02-norm en statusgrenzen.
2. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/besluiten-chris.md` — besluitenbasis.
3. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/ontwerpregister.md` — 76 ontwerpgevallen, alleen overlapcontrole.
4. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/herwerking-v1/casuspool-kandidaat-v4.json` — 40 huidige kandidaten, alleen overlapcontrole.
5. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/aanvulling-onzekerheid-v1/zeven-onzekerheidsgevallen-gevalobjecten-v1.json` — eerdere concepten G057–G063, alleen overlapcontrole. Lees **geen** beoordelingen of redacteursselectiepunten daarbij.
6. `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/../kwalificatieprotocol-v1.md` — families en onafhankelijke procedure. Het selectieplan is geen labelquotum.

De gebruiker heeft beperkte externe verwerking van synthetische gevallen, normteksten en besluiten toegestaan. Alle voorbeelden en bronnen zijn fictief, zonder geldend recht of persoonsgegevens. Lees geen individuele labelbesluiten, beoordelaarsvoorstellen, appuitkomsten of kwalificatieproef.

## Opdracht

Bereid maximaal zeven nieuwe conceptgevallen `G064`–`G070` voor, met **verschillende inhoudelijke contexten en bronmechanismen**. De eerste reeks bleek als geheel onvoldoende open functiegronden te bevatten: enkele gevallen konden onafhankelijk en overtuigend als toegestane begripsbeschrijving of als voorschrift worden gelezen. Dit is procesfeedback, geen labelinformatie per geval. Voorkom nieuwe gevallen die bij lezing van de concrete bronnen direct één functie krijgen.

Voor elk nieuw geval moet de exacte kernpassage twee **brongebonden, verdedigbare** functies kunnen hebben: (a) criterium/status/afleiding in een definitie, (b) een in de definitie overgenomen regel die iemands handelen of discretionaire keuze stuurt. Bied daarvoor minimaal twee concrete, gelijktijdig relevante fictieve bronnen met voldoende tekst en waar nodig een concreet gebruiksvoorbeeld. Maak duidelijk waarom geen bronhiërarchie, geldigheidsdatum of gebruikersbedoeling het verschil al oplost. De bronnen moeten onderling intern consistent blijven als document; conflicterende informatie tussen documenten mag juist het probleem zijn. Vermijd simpele “versie A/versie B” herhalingen, louter ontbrekende waarden, alleen een modaal woord, en onwaarschijnlijke speciaal voor de test bedachte dubbelzinnigheid. Als een bron een interpretatie al beslissend bewijst, bied dat geval niet aan. Een op zichzelf bewezen actorvoorschrift is geen onzekerheid.

Een beoordelaar mag alsnog `pass` of `fail` concluderen; je mag geen status, familie of split voorschrijven. Forceer geen zeven gevallen als dat tot zwakke voorbeelden leidt: laat een ID open en vermeld het concrete probleem. De nieuwe inhoud moet verschillen van G042/G045/G047, G057/G060, de overige G-kandidaten en de 76 C-ontwerpen; andere actoren of objecten bij dezelfde structuur volstaan niet. Geen bron die zelf een INT-02-oordeel geeft.

Per gevalobject exact zeven velden: `id`, `herkomst`, `begrip`, `kern`, `bedoeling`, `context`, `bronnen`. `context` bevat exact de lijsten `organisatorische_context`, `juridische_context`, `wettelijke_basis`. Iedere bron heeft `id`, `tekst`, `herkomst`. Gebruik voor geval- en bronherkomst: `Synthetisch concept, voorbereid door Claude Code CLI op 30 september 2026 voor DEF-835; geen praktijk- of expertbewijs.` Vermeld in de context dat alles fictief is en geen bestaand recht claimt. De bedoeling is neutraal en kiest niet tussen de bronlezingen.

Buiten de gevalobjecten: één selectiepunt per nieuw geval met `id`, `inhoudelijke_nieuwheid`, `nabije_ids`, `open_bronvraag`, `risico_op_triviale_variant`. Deze velden bevatten geen verwacht label of familie. De beoordelaars krijgen uitsluitend de gevalobjecten, niet de selectiepunten. Bewaar concrete betekenisgrond en vermijd kunstmatige bronconflicten.

## Exacte uitvoer

Eén geldig JSON-object, zonder Markdown:

{
  "status": "concept_niet_geaccepteerd",
  "normversie": "def771-int02/2",
  "gevallen": [maximaal zeven volledige gevalobjecten, op ID-volgorde G064..G070],
  "selectiepunten": [één per geval en eventuele ontbrekende-ID-uitleg],
  "bewijsgrenzen": [korte Nederlandse teksten]
}

Controleer voor definitief antwoord: unieke IDs, zeven velden, bronconsistentie, synthetische herkomst, neutrale bedoeling, geen labels, geen oppervlakkige varianten en geen wijziging van de bestaande pool. Je uitvoer is nog geen goldset.
