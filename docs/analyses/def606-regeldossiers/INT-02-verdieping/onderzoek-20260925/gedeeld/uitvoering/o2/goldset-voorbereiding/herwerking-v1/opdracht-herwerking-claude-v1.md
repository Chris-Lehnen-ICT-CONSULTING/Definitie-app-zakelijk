# DEF-835 — goedgekeurde goldsetherwerkingen voorbereiden

Je bent tekstredacteur voor synthetische testgevallen, in een verse Claude Code CLI-sessie. Dit is documentwerk, geen softwarewijziging. Voer deze opdracht zelf uit; geen agents, extra CLI's of herdelegatie. Je bent niet de enige in deze repository. Je mag geen bestanden wijzigen of verwijderen: lees bronnen met Read/Glob/Grep en geef de gevraagde JSON als je definitieve antwoord. De coördinator bewaart die als nieuw document en controleert de toegestane verschillen.

## Opdrachtbasis en bronnen
Lees volledig:
1. /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/besluiten-chris.md
2. /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/normcontract.md
3. /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/casuspool.json
4. /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/ontwerpregister.md
5. De individuele besluiten /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/besluit-chris-g001-v1.md tot en met besluit-chris-g040-v1.md; G009-v2 vervangt het selectiedeel van G009-v1. G022-v1 is het nieuwste vervangingsbesluit; bespreking-chris-g022-v1.md blijft achtergrond.
6. /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/../../kwalificatieprotocol-v1.md: bestaande selectiecriteria, geen toestemming deze te wijzigen.

De gebruiker heeft ieder geval besproken en de aanpassingen/vervangingen expliciet goedgekeurd. Maak nu de concrete nieuwe kandidaatteksten. Chris heeft geen nieuwe labels geaccepteerd. Gebruik de oorspronkelijke beoordelaarsbestanden NIET als extra bron; de individuele besluiten bevatten de relevante geautoriseerde acties. Geen appcode, prompts van het te kwalificeren model, modelproefuitkomsten, andere dossiers, web, API-calls, productiedata of Gitacties.

## Exacte toegestane acties
- Ongewijzigd behouden (niet opnemen in herwerkingen of vervangers): G004 G007 G008 G011 G012 G015 G017 G019 G024 G027 G029 G031 G037. Die blijven exact zoals in casuspool.json.
- Herwerken, exacte kern/ID/begrip/context behouden: G001 G002 G003 G005 G006 G014 G016 G018 G021 G023 G030 G033 G035 G036 G039.
- Bij G005 G023 G036 alleen bedoeling wijzigen; bronnen blijven exact gelijk.
- Bij G001 G002 G016 G021 G033 G035 G039 bedoeling en bronnen neutraler formuleren, zonder de betekenis te veranderen. G033 houdt "naar eigen inzicht", G016/G036 houden de bewust foutieve kernelementen.
- Bij G003 G006 G014 G018 G030 concrete fictieve bronpassages uitwerken voor de gestelde functies, en bedoeling neutraler maken. Geen samenvatting die zegt "twee functies/onbeslist/geen rangorde", maar werkelijk inhoudelijk vergelijkbare passages met herkenbare synthetische herkomst. Ontbrekende informatie eerlijk laten ontbreken. Forceer geen review_required: een zelfstandig bewezen gebrek blijft fail. Benoem in selectiepunten als de onzekerheid niet overtuigend te onderbouwen is zonder de vastgelegde kern/betekenis te wijzigen; dan geen kunstmatig conflict construeren.
- Nieuwe vervangers, volledige inhoud nieuw, exacte mapping:
  G009 -> G041; G010 -> G042; G013 -> G043; G020 -> G044;
  G022 -> G045; G025 -> G046; G026 -> G047; G028 -> G048;
  G032 -> G049; G034 -> G050; G038 -> G051; G040 -> G052.
  Oude gevallen blijven intact buiten de nieuwe selectie. Geen oppervlakkige vervanging van actor/object/woorden in bekende G- of C-gevallen. Voorzie inhoudelijk nieuwe functiegrenzen en concrete betekenisgronden. Markeer iedere bron als fictief, geen juridische geldigheidsclaim.
- Resterende selectievragen inhoudelijk uitwerken: G005 tegenover C116/C27; G012 tegenover C105/C15; G014 tegenover G003; G016 tegenover G001; G018 na vervanging G022/G026; G023 tegenover C58; G024 tegenover C15; G029 tegenover C112; G039 familie. Geen gevallen buiten expliciete vervangingslijst stil verwijderen/vervangen.
- Vier families uit protocol blijven het selectieplan; geen labelquota afdwingen. G039 is inhoudelijk een beschrijvend procesbegrip: verzin geen recht/plicht om het normatief te noemen. Geef een concreet voorstel voor afhandeling, maar wijzig de afgesproken familieverdeling niet.

## Kwaliteit van teksten
Geen zinnen als "geen beslisregel", "beschrijft alleen", "geen actorinstructie", "onzekerheid is beslissend" in bedoelingen/bronnen: zulke tekst zegt het normantwoord voor. Bronnen mogen WEL concrete opdrachten, rechten, waarnemingen, feiten, condities bevatten als dat werkelijk de betekenisgrond is. Neutraler is niet betekenisloos; niet alle bronsteun verwijderen. Behoud noodzakelijke rol, referent, condities, EN/OF, termijnen en negaties. Synthetische foute kernen hoeven niet goed te worden gemaakt. Geen herstel van definities in strijd met Chris' besluit. Vervangers mogen positieve of negatieve of werkelijk onbesliste gevallen zijn; uiteindelijk label is voor onafhankelijke beoordelaars en Chris.
Alle nieuw opgestelde herkomstregels: "Synthetisch concept, voorbereid door Claude Code CLI op 29 september 2026 op basis van individuele besluiten van Chris; geen praktijk- of expertbewijs." De 15 oorspronkelijke herkomstvelden in herwerkingen juist ongewijzigd laten voor vergelijkbaarheid; de versieherkomst staat in het wijzigingslog.

## Exacte uitvoer
Geef uitsluitend één geldig JSON-object, geen Markdownfences of tekst erbuiten:
{
 "status":"concept_niet_geaccepteerd",
 "normversie":"def771-int02/2",
 "herwerkingen":[15 volledige gevalobjecten met oorspronkelijke velden id,herkomst,begrip,kern,bedoeling,context,bronnen],
 "vervangers":[12 volledige nieuwe gevalobjecten met dezelfde zeven velden, IDs G041..G052],
 "wijzigingslog":[27 objecten met id, oorspronkelijke_id, besluitbestand, gewijzigde_velden, toelichting],
 "selectiepunten":[objecten met ids, bronverwijzingen, bevinding, concreet_voorstel, vereist_besluit],
 "bewijsgrenzen":[korte Nederlandse teksten]
}
Per bron object id (B1 enz.), tekst, herkomst. Context heeft drie lijsten organisatorische_context, juridische_context, wettelijke_basis; gebruik synthetische context zonder persoonsdata. Geen label/status/familie/split in gevalobjecten; geen goldlabels produceren. Geen claims van gemeten modelkwaliteit. Je ziet alle kandidaten en mag later niet optreden als O2-promptontwikkelaar/implementator. Geen hold-outsplit of freeze.

Lees alles vóór schrijven. Controleer zelf volledigheid 15+12, exacte IDs, ongewijzigde kernen van herwerkingen en inhoudelijke afstand van vervangers. Als een actie inhoudelijk niet haalbaar blijkt, leg die precies bij selectiepunten vast en behoud oorspronkelijke tekst; geen verzonnen overeenstemming.
