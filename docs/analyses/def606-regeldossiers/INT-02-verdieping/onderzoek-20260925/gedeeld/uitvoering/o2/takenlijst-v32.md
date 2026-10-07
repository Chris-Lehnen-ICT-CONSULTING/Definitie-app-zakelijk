# INT-02 O2 — actuele takenlijst v32

28 september 2026. Deze versie vervangt v31 als actuele ingang voor de coördinatie. S1 werkt in een andere, hergebruikte werkboom; de naam van die werkboom is behouden.

## Mandaat

- [x] Q1, S1, S2, U1 en E1 zijn expliciet geaccordeerd, inclusief de beschreven schema-/document-/exportcontracten en twee triggervervangingen.
- [x] Nieuw begrensd proefbudget: maximaal 43 appcalls, 43 tokenmetingen en US$12. Nog **nul** nieuwe appcalls gebruikt.
- Actions blijven uit. Geen push, merge, productieactivering of productiedata.

## Afgerond

- [x] WP5a en eerdere typecorrecties: commit f9bb9e697.
- [x] **Q1 gereed en lokaal gecommit:** ebe9c1b7c26ffe6040bffb66db4937b932406dc8.
- [x] Q1: 176 tests geslaagd; Ruff/Black groen; alle drie onafhankelijke reviewbevindingen gesloten.
- [x] Normale commit van 65 geselecteerde bron-/dossierbestanden: alle gebruikelijke hooks, inclusief Gitleaks, geslaagd. Geen controle omzeild.
- [x] Na commit zijn de drie bronblobs bytegelijk aan de finale review; index leeg en getrackte bronbestanden schoon.
- [x] Veertig nieuwe ongelabelde synthetische conceptgevallen voorbereid, buiten software- en reviewcontext. Nog geen geaccepteerde goldset.

Q1-bewijs: q1-codex-F3-eindreview-v1.md, bewijs/q1-reviewmanifest-v3.json, q1-na-commit-v1.json en q1-normale-commit-v1.log. De volledige testclaim betreft Q1; geen volledige-appsuite- of modelkwalificatieclaim.

## Actief — S1 gedeelde opslag

- [x] Vrijgekomen beheerde reviewwerkboom veilig hergebruikt; 30 aanwezige wijzigingen waren bytegelijk aan Q1-commit. Niets verwijderd.
- [x] Branch **feature/DEF-626-validatiesnapshots**, basis **ebe9c1b7c**.
- [x] Nulmeting: **170 tests geslaagd**, 95 waarschuwingen bewaard, exit0.
- [x] Beide CLI's gecontroleerd: Claude 2.1.283 en Codex 0.158.0, ingelogd.
- [x] Inventarisatie afgerond; tests eerst rood vastgelegd vóór productiecode. Eerste bruikbare run: 38 failed, 134 passed, 4 errors; bewijs/s1-rood-v2.log.
- [x] Aparte schone S1-reviewwerkboom voorbereid vanaf dezelfde basis: /Users/chrislehnen/.codex/worktrees/def626-s1-review/Definitie-app.
- [x] Eerste S1-implementatie binnen precies zestien bestanden opgeleverd door Claude; nog niet geaccepteerd of gecommit.
- [x] Coördinator: 46 tests geslaagd, 48 waarschuwingen, exit0; bronhashes voor/na gelijk.
- [ ] Werkboomselectie: 186 passed / 22 failed. Alleen met extra fixturepatch in tijdelijke kopie: 208 passed. Bredere selectie met patch: 45 nieuwe fouten plus dezelfde 7 baselinefouten.
- [x] Onafhankelijke S1-review afgerond: niet gereed, negen concreet bewezen bevindingen S1-R01 t/m R09.
- [x] Correctieronde1 opgeleverd binnen zestienbestanden:41regressietests groen; totale gerichte selectie225passed/24failed.
- [ ] Dezelfde Codex-reviewer voert herreview uit (execsession43697). Gewone retries werken; R08-retry met categoriekeuze blijft aantoonbaar open.
- [ ] Expliciet besluit op **vijftig extra bestaande bestanden** (11productie,39tests/fixtures): s1-scopeaanvulling-voorstel-v2.md. Deze vraag vervangt het nog onbeantwoorde tienbestandsvoorstel. De R03-doorwerking op9productiecallers en32testbestanden ontbreekt daarin.
- [x] Lint/mypy groen. Complexiteitsgate blijft rood: basis205 versus grens201; S1 verlaagt naar204. Geen grens aangepast.
- [ ] Reviewbevindingen verwerken en noodzakelijke scope-uitbreiding concreet voorleggen; daarna herverificatie en normale lokale commit.

Werkboom S1:
/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app

Dossier S1:
/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2

Uitvoerder: Claude-sessie 7f05cfbc-1970-4a7b-a241-c4693f11f217.
Volledige opdracht: s1-opdracht-claude-v1.md in het S1-dossier.
S1-reviewer: Codex CLI-sessie 01a0e928-8d33-7c31-b145-6aec14fe4d59, execsession43697 actief voor gerichte herreview in /Users/chrislehnen/.codex/worktrees/def626-s1-review/Definitie-app. Actuele diff-SHA256:5a03dd59cf27192c5a37422fa35f08925ec528050e42b01b7c9a59201e0c9023; correctiedeltaebe8f1dc13d8d26eaa81f5ec984c83dbc5ede6169e3f012aac6391d3043ada29; bronmanifest93cefa71ff7d8ce1afb56394d68a92523fb84126cfee202a0b58e4653d8f98de. Claude is klaar met correctie1 (exec58074 exit0); dezelfde reviewer controleert R01/R02/R03, internR07,R08,R09. R03-backendveiligheid blokkeert nog oude externeaanroepen;115nieuwe falende IDs in32testbestanden zijn daarmee verklaard. Definitieve deelaftekening wacht op herreview. R04/R05/R06 en het externe deel van R07 wachten op de gerichte scopeaanvulling. Nieuwe opdracht: s1-reviewcorrectie1-opdracht-claude-v1.md. Alle negen bevindingen hebben dispositie fix vóór S1-oplevering; niets stil geaccepteerd. Bewijs: s1-uitvoering-v1.md, bewijs/s1-reviewmanifest-v1.json en bewijs/s1-coordinator-v1.log in S1-dossier. Een ontbrekend lokaal controlescript in de implementatiewerkboom is gekoppeld aan het bestaande script in de hoofdcheckout; geen controle uitgezet. Deze lokale symlink hoort niet bij de commitselectie.

## Open vragen — blokkeren de offline bouw niet

- [ ] Goldsetbeoordelaars kiezen: twee mensen, of twee onafhankelijke CLI-voorstellen met Chris als inhoudelijke beoordelaar. Daarna labels accepteren en set bevriezen.
- [ ] Expliciet publicatieakkoord voor het volledige plan bij DEF-626 in Linear. Automatische goedkeuringscontrole wees die externe publicatie af. Geen document/status/comment gepubliceerd; geen andere route geprobeerd. Alleen externe documentatie wacht.

## Daarna — al geaccordeerd

- [ ] S2: O2-documenten duurzaam bewaren en strikt herladen; C118.
- [ ] U1: editor en actuele/historische beoordeling.
- [ ] E1: additief exportveld met herbinding op de werkelijk geëxporteerde kandidaat.
- [ ] Modelkwalificatie volgens protocol, pas na labels/freeze en binnen het begrensde budget.
- [ ] Geïntegreerde eindcontrole en oplevering; productieactivering blijft afzonderlijk.

Volgende actie: gerichte herreview afronden; resterend R08 binnen scope bij dezelfde Claude corrigeren. Scopevoorstelv2 staat open; geen ontbrekend antwoord als akkoord behandelen.

