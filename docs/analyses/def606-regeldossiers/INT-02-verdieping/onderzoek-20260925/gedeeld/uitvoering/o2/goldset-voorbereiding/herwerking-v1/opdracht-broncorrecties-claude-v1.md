# DEF-835 — gerichte broncorrecties na onafhankelijke herbeoordeling

Vervolg op jouw conceptredactie in sessie 030937a3-6998-4335-9596-f621033efcad. Je blijft tekstredacteur, geen labelacceptatie-eigenaar. Dit is documentwerk, geen softwarewijziging. Werk zelf; geen herdelegatie, agents of extra CLI's. Je bent niet alleen in de repository. Alleen lezen, geen bestanden wijzigen. Alle oude uitvoer blijft bewaard.

Chris heeft de herwerkingen en concrete bronpassages geautoriseerd en expliciet toestemming gegeven voor beperkte overdracht aan de externe Claude-dienst. De coördinator heeft jouw volledige JSON in /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/../herwerking-v1/concept-herwerkingen-v1.json en de samengestelde pool in /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/../herwerking-v1/casuspool-kandidaat-v1.json opgeslagen. Technische veldcontrole: nul afwijkingen, 15 kernen exact behouden. Twee onafhankelijke beoordelaars hebben de nieuwe versie beoordeeld. Geef geen nieuwe labelvoorstellen: hun inhoudelijke verschillen beslist Chris later. Het werk hier corrigeert concreet aangetroffen bronproblemen binnen de geautoriseerde herwerking.

## Bronnen
Lees voor uitsluitend G003, G006, G018, G030:
- oorspronkelijke /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/casuspool.json
- /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/../herwerking-v1/casuspool-kandidaat-v1.json
- individuele besluit-chris-g003-v1.md, -g006-v1.md, -g018-v1.md en -g030-v1.md in /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1
- geldige norm /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/normcontract.md en besluiten /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/besluiten-chris.md.
De onderstaande bevindingen zijn terugkoppeling; behandel ze kritisch op de werkelijke bronnen, niet blind. Lees geen andere beoordelaarsuitvoer, appcode of andere dossiers. Geen web/Git/appmodelproef/productiedata.

## Vier concrete punten
1. G003: je nieuwe B1 laat het type ontstaan vanaf registratie van een aanwijzingsbesluit en vervallen na registratie van een intrekkingsbesluit. De oorspronkelijke bron zei dat aanwijzing zelf de registratie van het type is. Extra afzonderlijke momenten zijn niet als betekenisbehoud onderbouwd. Corrigeer de bron zodat het oorspronkelijke aanwijzings-/registratieverband behouden blijft; geen ongevraagde intrekkingsregeling of nieuw ontstaansmoment.
2. G006: je nieuwe B1 laat status ontstaan bij vaststelling van evenwicht, terwijl de oorspronkelijke bron een reeds aanvaard arrangement met constitutief oordeel beschrijft. Laat niet zonder grond die twee momenten samenvallen. Concretiseer de bron met behoud van reeds aanvaard zijn. Dat een registerpassage en een instructie elkaar aanvullen maakt ze niet automatisch tegenstrijdig. Forceer dus geen onzekerheidslabel; laat de bronnen zeggen wat inhoudelijk gedragen is.
3. G018: B2 introduceert verval vanaf de volgende dag, terwijl kern en B1 'zodra' gebruiken. Corrigeer die onbedoelde termijnverschuiving; voeg geen andere termijn toe. Kern en toegestane interpretaties behouden; geen label afdwingen.
4. G030: B2 bevat de volledige nominale definitiezin los tussen twee imperatieven. Beide beoordelaars vinden deze constructie kunstmatig of onvoldoende natuurlijk als concrete bron. Maak de fictieve instructiekaart coherent, terwijl kern exact behouden blijft en het oorspronkelijke uitgangspunt (dezelfde zin staat ook in de typetabel) niet wordt vervalst. Als dat geen overtuigend functievraagstuk oplevert, rapporteer precies de beperking; construeer geen conflict om review_required te krijgen. Niet zelf een nieuw geval of ander label invoeren.

## Grenzen
Alleen bedoeling/bronnen van deze vier gevalobjecten mogen veranderen. ID, herkomst, begrip, kern, context blijven exact gelijk aan de kandidaatpool. Geen andere gevallen aanpassen. De fictieve herkomst eerlijk vermelden, geen juridische waarheid claimen. Laat onderbouwde broninhoud staan; neutraler betekent niet inhoudsloos. Geen nieuwe parameters, deadlines, rollen of extra gebeurtenissen om de analyse gemakkelijker te maken. Labels/families/quotum/split/freeze niet vaststellen.

## Uitvoer
Eén geldig JSON-object zonder Markdownfences:
{
 "status":"correctievoorstel_niet_geaccepteerd",
 "gevallen":[de vier volledige gevalobjecten met oorspronkelijke zeven velden],
 "dispositie":[per ID een object met id, bevinding, afweging, actie, gewijzigde_velden, resterend_open],
 "bewijsgrenzen":[...]
}
Als een punt niet oplosbaar is binnen het akkoord, behoud de relevante inhoud en markeer resterend_open concreet, in plaats van toestemming te verzinnen. Geef geen labels. Geen bestanden schrijven; de coördinator bewaart je antwoord als nieuwe versie en controleert de verschillen. Gebruik geen tools buiten Read/Glob/Grep.
