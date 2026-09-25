# Claude Code CLI — DEF-771, uitsluitend WP1

Status: Chris heeft WP1 expliciet goedgekeurd op 25-09-2026: acht bestanden, geraamd 220–340 regels. Ook bijhouden van takenlijst/processtatus is goedgekeurd. Voer uitsluitend WP1 uit.

## Rol

Jij bent de Claude Code CLI-uitvoerder. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. De coördinator organiseert en verifieert. Een afzonderlijke verse Codex CLI-sessie reviewt later de concrete diff en schrijft geen bronbestanden. Alle terugkoppeling is Nederlands.

Lees AGENTS.md, CLAUDE.md en toepasselijke regels. Je bent niet alleen in de repositories: behoud alle bestaande wijzigingen van anderen. Geen bestanden, testgevallen of dode code verwijderen. Maak vóór wijziging unieke herstelkopieën volgens de projectregels. Geen dependencies installeren, schema wijzigen, live toepassingsmodelaanroepen doen of productiedata lezen. Maximaal drie pogingen per actie; daarna melden.

## Werkbasis en bronnen

App: /Users/chrislehnen/Projecten/Definitie-app, branch feature/DEF-771-int02-contract-o1, basis 0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d.

Skills: /Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills, branch feature/DEF-771-int02-contract-o1, basis origin/main 1e27a2da7668437423af3962cce48af5f1bc591b. Behoud de bestaande INT-01-aanvullingen. Schrijf niet in de andere checkout of actieve skillkopieën.

Dossier relatief aan app: docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/.

Lees volledig: gedeeld/besluiten-chris-v1.md; gedeeld/gezamenlijke-synthese-v5.md; gedeeld/gezamenlijk-casusregister-v5.md; gedeeld/besluitnotitie-chris-v5.md. Lees veldmatrix b-codex-cli/onderzoek-b-v3.md §Q2/V02 inclusief RA-B-12/13 en RB-A-07. Besluiten B1–B6 zijn leidend boven voorstelstatus in onderzoeksstukken. Exacte teksten rechtstreeks uit de bron kopiëren; niet reconstrueren of inkorten.

## Wijzigingsscope: acht inhoudelijke bestanden

In de app:

1. src/toetsregels/regels/INT-02.json
2. nieuw tests/unit/validation/test_def771_int02_contract.py

In de geïsoleerde skillwerkboom:

3. nieuw skills/definitie-toetsregels/references/int02-beslisregel.md
4. nieuw skills/definitie-nederlandse-definities/references/int02-beslisregel.md
5. skills/definitie-toetsregels/reference.md
6. skills/definitie-nederlandse-definities/reference.md
7. skills/definitie-toetsregels/SKILL.md
8. skills/definitie-nederlandse-definities/SKILL.md

Raming 220–340 gewijzigde/toegevoegde regels. Bewijsbestanden en herstelkopieën apart benoemen. Voor extra inhoudelijke bestanden of noodzakelijke contractwijzigingen eerst aan de coördinator melden. Niet doorwerken aan WP2–WP6.

## TDD en inhoud

Schrijf eerst de contracttests en voer ze uit tegen de bestaande record- en skillinhoud. Bewaar commando, uitvoer en exitstatus als RED-bewijs. Een ontbrekende dependency of verkeerde werkdirectory geldt niet als inhoudelijk RED-bewijs. Gebruik de bestaande offline pytest-omgeving en toepasselijke markers.

De canonieke bron bevat versie en datum, N uit synthese §2 met brede variant en expliciete lokale bronannotatie, veldrollen, exacte G uit §3, T met reviewerhulp/appmeldingen/statusmapping/signaalbeleid uit §4 en H uit §5 uitsluitend als toelichtingsvoorstel; geen herstelroute (DEF-832). Benoem de genomen besluiten, herkomst en bewijsgrenzen. De tweede skillreferentie is bytegelijk.

Neem voorbeelden met herkomst en premissen uit het register op: positief C10/C05/C19/C53/C112/C113/C116; negatief C02/C12/C52/C105/C114; grens C16/C24/C55/C58/C107. Presenteer de ontwerpverwachtingen niet als gemeten modelkwaliteit.

Record: vervang uitleg, toelichting, toetsvraag, type, brondocument en example_pair_reason exact volgens synthese §6. Bewaar het letterlijke ASTRA-bronpaar en review_policy; voeg uitsluitend de in §6 genoemde functievoorbeelden met herkomst toe. Bind het record aan de contractversie. Voeg geen ongespecificeerde recordinhoud toe. Evaluator judgment_review en excluded_from_score blijven; required_inputs/contextwijziging hoort bij WP3.

Vervang beide reference.md-zinnen letterlijk volgens §6 na SC-C-02. Voeg in beide SKILL.md het gerichte INT-02-blok toe, inclusief geen kwaliteitscijfer, vervallen totaalscore sinds 15-09-2026, actief JSON-runtimecontract en skilladvies dat geen opgeslagen expertbeoordeling is. Geen algemene skillsanering.

De contracttest bewijst record-uitleg en toetsvraag tegenover het canonieke contract, versieovereenkomst, bytegelijkheid van de twee skillcontracten, behoud ASTRA-paar/review_policy en de opgegeven voorbeeld-ID's. Gebruik geen stilzwijgende skips of een hardgecodeerd persoonlijk homepad. Omdat de skills in een tweede repository staan: maak de benodigde bronlocatie expliciet in het testcommando en meld de consequenties voor zelfstandig draaien/CI voordat daarvoor extra scope nodig wordt. Een bronkopie mag nooit ongemerkt als canonieke bron worden voorgesteld.

## Verificatie en terugmelding

Draai de gerichte contracttests GREEN en de relevante lintcontrole; bewaar onverkorte uitvoer met commando en exitstatus onder gedeeld/uitvoering/ in nieuwe bestanden. Rapporteer gewijzigde paden, diffstat per repository, gebruikte basis/werkboom, contract-SHA-256, bronvergelijking, RED/GREEN-bewijs en resterende beperkingen. Test geen live provider.

Stop bij een besluitconflict of wanneer exacte tekst niet in het bestaande contract past; citeer bron en code en stel een oplossing voor. Doe geen commit, push, PR, Linear-mutatie of actieve skillpublicatie in deze opdracht. Meld het pakket aan de coördinator en wacht.
