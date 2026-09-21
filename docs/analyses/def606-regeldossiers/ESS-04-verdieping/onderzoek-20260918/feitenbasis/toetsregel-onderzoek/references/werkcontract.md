# Werkcontract voor terugkerend regelonderzoek

Dit is een werkvorm, geen verplichte documentproductie. Pas bestaande dossiers aan door verwijzing/hergebruik; volg expliciet afgesproken paden en versies. Geef twee onderzoekers dezelfde feitenbasis en Q1–Q6. Bewaar de onafhankelijke antwoorden pas daarna naast elkaar.

## Minimale informatie per onderzoek

| Registratie | Velden die beslissingen ondersteunen |
|---|---|
| Opdracht/status | Actieve regel; beoogde uitkomst; wat al is geautoriseerd; onderzoekers/sessie-identiteit; exacte gedeelde locatie; fase; ontvangen/ontbrekende bijdragen; volgend concreet werkpunt. |
| Bronnen/besluiten | ID; bron/sectie of bestand; versie/datum; toegang; norm/implementatie/besluit; toepassingsbereik; vervangt/vult aan; geraakte onderzoeksvraag. |
| Claim | Stabiel ID; precieze uitspraak; feit/besluit/waarneming/interpretatie/voorstel; bron/proef; commit/runtime indien relevant; zekerheid en beperking. |
| Casus | Stabiel ID; invoer en bedoelde betekenis; benodigde informatie; verwachting per beleidsoptie en grond; uitgevoerd/niet uitgevoerd; werkelijke uitkomst; betrokken regels; gebruikersgevolg. |
| Route | Ingang; ontvangen/verzonden waarden; oordeel/status/score/dekking; opgeslagen/getoonde informatie; mogelijke handeling; bewijsniveau en ontbrekende grens. |
| Review/dispositie | Punt-ID; versie/claim van de ander; bevestigd/aangevuld/tegengesproken/onvoldoende bewezen/beleidskeuze; grond; effect; verwerking en vindplaats. |
| Besluit | Wat staat al vast; open keuze; voorkeur per onderzoeker; alternatief; gevolgen; onderscheidende casus; benodigde gebruikersbeslissing of ontbrekend bewijs. |

Meestal volstaan een bron-/casusregister, twee onderzoeksbijdragen met ieder review en verwerking, één besluitnotitie en relevante proefbijlagen. Een review of dispositie mag onderdeel van een onderzoekersdocument zijn. Laat het onderzoeksmanifest aanwijzen welke versie actueel is; nummering op zichzelf bepaalt niet de status. Gebruik nieuwe versies voor uitgewisselde/vastgelegde bijdragen; werk concepten alleen bij volgens het geldende bestandsbeleid.

## Samenwerking starten en uitvoeren

Codex coördineert de samenwerking. Cowork is een afzonderlijke onderzoekssessie, geen vervanging door een kort modeladvies. Bij uitvoering vanuit Cowork: lever de eigen faseproducten en benodigde overdracht aan Codex; neem zijn rol of sessie niet stil over.

1. **Bepaal de startpositie.** Lees bestaande opdracht, autorisatie en processtatus. Leg de actieve regel, Codex- en Cowork-sessie, bronbasis, gedeelde locatie en laatst voltooide fase vast. Controleer de identiteit van een aangewezen sessie; gebruik geen afgeronde sessie van een andere regel. Een reeds geautoriseerde geschikte sessie mag direct worden gebruikt. Start een nieuwe sessie alleen als de gebruiker dat heeft toegestaan.
2. **Maak de tweede lijn concreet.** Vul de [startopdracht](startopdracht.md) in met geverifieerde projectpaden, bronversies, regel en werkmap. Gebruik beschikbare, toegestane middelen voor de overdracht. Is toegang of toestemming nog nodig, lever eerst de ingevulde opdracht en het bronpakket en vraag gericht om precies die ontbrekende handeling. Vraag geen algemene herbevestiging van het onderzoek. Meld de blokkade bij aanvang, niet pas bij oplevering van een solorapport.
3. **Controleer ontvangst.** Verifieer dat Cowork de opdracht, skill met referenties en historische bronnen werkelijk kan lezen. Installatie van de skill in Cowork is niet vereist wanneer de bestanden leesbaar zijn aangeleverd. Noteer de werkelijke padmapping; een geplakt pad of een voorbereid ZIP-bestand bewijst geen toegang. Geef bij ontbrekende toegang het exacte bestand en een bruikbare overdrachtsroute aan.
4. **Voer de faseovergangen uit.** Houd per overdracht afzender, ontvanger, bestand/versie, ontvangstbewijs, status en volgende actie bij. Gebruik volledige bijdragen en claimrelevante bijlagen, met inhoudshashes wanneer nodig. Codex levert niet alleen een lijst ontbrekende reviews op, maar vraagt en verzamelt de geautoriseerde bijdragen daadwerkelijk. Wacht tijdens actief werk via beschikbare middelen op relevante resultaten en ga daarna door. Bij onderbreking: bewaar een hervatbare tussenstand; suggereer geen achtergrondbewaking en maak geen automatisering zonder opdracht.

## Fasen en overdracht

| Fase | Concrete actie en voorwaarde voor doorgaan |
|---|---|
| Gedeelde feitenbasis | Codex levert historische bronnen, actuele besluiten, Q1–Q6 en scope aan Cowork. Cowork bevestigt toegang. Nieuwe Codex-conclusies zijn geen startmateriaal. |
| Onafhankelijke eerste versies | Beiden beantwoorden Q1–Q6 en bewaren hun eigen volledige v1. Ieder mag meteen beginnen. Wissel pas nieuwe conclusies uit nadat beide eerste versies aantoonbaar opgeslagen zijn. |
| Wederzijdse review | Codex leest en reviewt het volledige Cowork-onderzoek met relevante bijlagen. Codex draagt zijn volledige onderzoek over met de expliciete opdracht aan Cowork om dit inhoudelijk te reviewen. Beide reviews moeten werkelijk ontvangen zijn. |
| Verwerking door beiden | Codex verwerkt elk Cowork-punt met oordeel, grond en vindplaats. Codex stuurt zijn review aan Cowork en vraagt dezelfde verwerking. Controleer ook de werkelijk ontvangen Cowork-verwerking; versturen alleen voltooit deze fase niet. |
| Synthese en controle | Codex integreert beide herziene adviezen en resterende verschillen. Stuur de volledige synthese aan Cowork voor controle op weglating, standpuntweergave en betekenisverlies. Verwerk de ontvangen controle zichtbaar. |
| Oplevering | Controleer beide onderzoeken, beide reviews, beide verwerkingen en de verwerkte synthesecontrole. Lever de besluitnotitie en bewijsverwijzingen op; beleidskeuzes blijven bij de gebruiker. |

Gebruik bijvoorbeeld `codex-onderzoek-v1.md`, `cowork-onderzoek-v1.md`, `codex-review-op-cowork-v1.md`, `cowork-review-op-codex-v1.md`, beide reviewverwerkingen en `gezamenlijke-synthese-v1.md` met `cowork-review-op-synthese-v1.md`. Volg bestaande bestandsnamen waar bruikbaar. Een fase mag in een bestaand document staan wanneer versie en ontvangst afzonderlijk verifieerbaar blijven.

Beide eerste versies mogen dezelfde historische bronnen gebruiken. Ze lezen vóór opslag geen nieuwe conclusies, review of synthese van de ander. Als Codex al een eerste onderzoek heeft: behoud dit en geef Cowork eerst uitsluitend de gedeelde feitenbasis. Als een onderzoeker de nieuwe conclusies al heeft gelezen, benoem dat de eerste beoordeling niet meer onafhankelijk is; herstel zo nodig met een nog onbeïnvloede, geautoriseerde sessie. Claim geen onafhankelijkheid door een bestandsnaam te veranderen.

Plan één volledige wederzijdse review en één synthesecontrole. Extra werk lost een concreet materieel punt op. Wacht niet op algemene instemming als alle punten verwerkt en resterende verschillen beleidskeuzes zijn. Ontbrekende verplichte review blijft ontbrekend; tijdsverloop geldt niet als instemming. Bij hervatten: controleer werkelijk ontvangen versies en ga door bij de eerstvolgende open fase, zonder voltooid onderzoek opnieuw te laten doen.

## Genereren en toetsen binnen dezelfde norm

Gebruik het [dossiersjabloon voor genereren en toetsen](genereren-en-toetsen.md) bij beide startopdrachten, onderzoeken, reviews en de synthesecontrole. Leg G/T/H en veldrollen vast binnen de bestaande dossieronderdelen. Een instructie voor generatie is geen bewijs van generatiekwaliteit; een falende toets is geen bewijs dat de generator de fout maakte.

## Dekking bij DefinitieAgent

Gebruik het aangewezen bestaande dossier als vertrekpunt; ontdek versies via de opdracht en repository. Maak geen actuele besluiten afhankelijk van vaste CON-01-paden of issue-ID's in deze skill.

De veertien dossieronderdelen zijn: (1) doel/betekenis, (2) norm/besluiten, (3) toepasselijkheid, (4) context, (5) definitiebronnen, (6) ontologie/relaties, (7) aanvullingen, (8) appgedrag, (9) skills/prompts, (10) status/score/poorten, (11) proeven, (12) samenhang, (13) verbeteringen/review, (14) acceptatie/overdracht. Eén verwijzing naar een gedeeld antwoord kan meerdere onderdelen dekken; maak geen veertien parallelle verhalen.

Beoordeel context, bronnen en ontologie naar hun functie voor de actieve regel. Behandel voorbeelden, praktijkvoorbeelden, tegenvoorbeelden, grensgevallen, synoniemen, homoniemen en toelichting afzonderlijk als relevant/niet relevant, met reden. Verwissel conceptidentiteit, registratiesleutel en term niet. Bronpassages en aanvullingen repareren geen onvolledige kern en horen niet stil in een andere getoetste tekst terecht te komen.

Controleer toepasselijkheid op genereren, uitsluitend toetsen, import, bewerken, review, conceptopslag, vaststelling en export/herbeoordeling. Voer alleen de nog benodigde grensproeven uit. Noteer waar gedeelde ketendefecten elders al bewezen zijn, hun eigenaar en hun betekenis voor deze regel. Heropen geen algemene poort-/identiteitsbesluiten omdat één regel wordt onderzocht.

Voor skill-/promptvoorstellen: huidige passage en vindplaats → probleem → exacte vervanging → toetsgeval. Onderscheid generatie-instructie, toetsinstructie en reviewerhulp. Een nieuw betekeniskenmerk om het domein herkenbaar te maken is een inhoudelijke verandering, geen onschuldige stijlcorrectie.

## Wat de volgende echte toepassing moet leren

Houd alleen nuttige procesgegevens bij: aantal werkelijk open vragen, hergebruikte versus nieuwe proeven, late besluitcorrecties, materiële reviewcorrecties en benodigde extra rondes. Gebruik geen modelcijfers of tijdwinstpercentages zonder meetbasis.

De methode is niet bewezen efficiënt doordat een skillbestand geldig is. Beoordeel bij volgende regels of bovenliggende besluiten eerder gevonden worden, verwachtingen stabiel blijven, bewijsclaims smaller/juister zijn en de gebruiker uit de korte notitie een besluit kan nemen. Verbeter de skill op concrete uitkomsten; voeg niet voor elk hypothetisch randgeval een vaste verplichte stap toe.
