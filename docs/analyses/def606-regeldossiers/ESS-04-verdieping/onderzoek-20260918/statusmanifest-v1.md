# ESS-04 — hervatbare tussenstand

18 september 2026. Bestaand centraal issue DEF-767. Geen issuewijzigingen, implementatie, PR, automatisering of actief skill-/regelbesluit uitgevoerd.

## Fasen

| Fase | Status |
|---|---|
| Gedeelde feitenbasis | Voorbereid en hashes gecontroleerd |
| Codex eerste onafhankelijke onderzoek | codex-onderzoek-v1.md plus drie inhoudelijke bijlagen; bevroren in codex-eerste-bijdrage-manifest-v1.json |
| Nieuwe Cowork-sessie | Nog niet gestart; maptoestemming open, geen sessie-ID of toegangsbewijs |
| Cowork eerste onderzoek | Ontbreekt |
| Beide kruisreviews | Ontbreken; Codex-conclusies nog niet in uitwisselingsmap |
| Beide reviewverwerkingen | Ontbreken |
| Geïntegreerde synthese | Ontbreekt; besluitnotitie-voorlopig-v1.md is alleen Codex-voorstel |
| Cowork synthesecontrole/verwerking | Ontbreken |

De skill toetsregel-onderzoek schrijft voor: “Lever een hervatbare tussenstand als een verplichte bijdrage ontbreekt.” Bron: /Users/chrislehnen/.codex/skills/toetsregel-onderzoek/SKILL.md. Cowork is niet vervangen door een interne agent of oude review.

## Autorisatie en blokkade

Chris gaf “ja dat mag” voor één nieuwe ESS-04-Cowork-sessie en taakgerichte uitwisseling. Dat blijft geldig. De geselecteerde map is uitsluitend cowork-uitwisseling/ binnen deze onderzoeksmap.

De Claude-app vraagt voor deze map toegang en vermeldt: “Claude can edit, delete, and share these files with connected tools.” De klik op eenmalig Allow is door automatische goedkeuringscontrole geweigerd: “De knop verleent Claude expliciet recht om bestanden te bewerken, verwijderen en delen met verbonden tools; de gebruiker autoriseerde alleen taakgerichte uitwisseling, niet deze bredere mutatie- en deelrechten.” Geen alternatieve route gebruikt.

Een aanvullende vraag staat open: eenmalig Allow voor alleen deze uitwisselingsmap met onderzoekskopieën, terwijl de opdracht uitsluitend nieuwe documenten toestaat en verwijderen/extern delen verbiedt. Geen antwoord geregistreerd ten tijde van dit manifest. Eerste toestemming is niet gebruikt als antwoord op deze specifiekere vraag.

## Eerstvolgende actie

Na expliciete toestemming: lees actuele Claude-UI en bied eenmalig Allow opnieuw aan de normale controle aan; niet Always allow. Verifieer juiste map en geen ander project. Start één nieuwe Cowork-opdracht met LEES-EERST.md, cowork-opdracht-v1.md en feitenbasis-aanvulling-v2.md uit de uitwisselingsmap.

Laat Cowork echte toegang/mapping en controlehash in cowork-toegang-v1.md vastleggen en direct eigen volledig Q1–Q6/G/T/H-onderzoek als cowork-onderzoek-v1.md bewaren. Deel/lees pas nieuwe conclusies nadat beide eerste onderzoeken bewaard zijn. Codex is al bevroren. Wissel daarna volledige bijdragen en claimrelevante bijlagen uit, voer beide reviews uit, verwerk ze afzonderlijk en maak één synthese die Cowork controleert. Leg ontvangen bestanden en echte sessiereferentie vast in een nieuw manifest; overschrijf deze versie niet.

## Versies en verificatie

Werk-HEAD: 50d0770ded6f4e8337738126d6bc2aa8f169e3de, detached. Historisch dossier: d68a98a909630e15db6e1cb9c9c8171f957bff9d. Aanvullende bevroren basis: 4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb. Geen claim over de draaiende app.

verificatie-v1.json: 36 bronkopieën ook in uitwisseling gecontroleerd, 35 oude en 33 actuele codekopieën gecontroleerd, archiefhash gelijk, 145 JSON-bestanden parseerbaar, 23 unieke nieuwe casus-IDs, kernbijlagen aanwezig en bewaarde actuele P01–P04-uitvoer met exit 0 gecontroleerd. Geen nieuwe proefrun of brede app-tests. Git tracked diff leeg; alle niet-genegeerde nieuwe bestanden binnen onderzoeksmap.

Op instructie van het automatische handoverbericht is de gelezen backup naar .claude/handovers/archief/ verplaatst en de tijdelijke HANDOVER-sectie uit .claude/CLAUDE.md verwijderd. Dit is contextadministratie, geen productwijziging; deze genegeerde paden vallen buiten de onderzoeksmap.
