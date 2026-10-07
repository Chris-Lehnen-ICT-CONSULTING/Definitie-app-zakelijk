# INT-02 O2 — actuele takenlijst v30

28 september 2026. Deze versie vervangt v29 als actuele ingang voor de coördinatie. S1 werkt in een andere, hergebruikte werkboom; de naam van die werkboom is behouden.

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
- [ ] Onafhankelijke S1-review actief; herstelroute, overige schrijvers en bewijsbinding expliciet inbegrepen.
- [x] Lint/mypy groen. Complexiteitsgate blijft rood: basis205 versus grens201; S1 verlaagt naar204. Geen grens aangepast.
- [ ] Reviewbevindingen verwerken en noodzakelijke scope-uitbreiding concreet voorleggen; daarna herverificatie en normale lokale commit.

Werkboom S1:
/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app

Dossier S1:
/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2

Uitvoerder: Claude-sessie 7f05cfbc-1970-4a7b-a241-c4693f11f217.
Volledige opdracht: s1-opdracht-claude-v1.md in het S1-dossier.
S1-reviewer: Codex CLI-sessie 01a0e928-8d33-7c31-b145-6aec14fe4d59, execsession37240, actief in /Users/chrislehnen/.codex/worktrees/def626-s1-review/Definitie-app. Diff-SHA256: 1dcdcf97fea0e378755443be492f6d3f05f0f55bf11b4d25d7f6fc437fd1c1e6; bronmanifest eb63ca9b00d62eff883e6bcb16a61f709defa902bb8d14e8e500e7e5f1aeca59. Claude is gereed en wacht op concrete correcties in dezelfde sessie. Bewijs: s1-uitvoering-v1.md, bewijs/s1-reviewmanifest-v1.json en bewijs/s1-coordinator-v1.log in S1-dossier. Een ontbrekend lokaal controlescript in de implementatiewerkboom is gekoppeld aan het bestaande script in de hoofdcheckout; geen controle uitgezet. Deze lokale symlink hoort niet bij de commitselectie.

## Open vragen — blokkeren de offline bouw niet

- [ ] Goldsetbeoordelaars kiezen: twee mensen, of twee onafhankelijke CLI-voorstellen met Chris als inhoudelijke beoordelaar. Daarna labels accepteren en set bevriezen.
- [ ] Expliciet publicatieakkoord voor het volledige plan bij DEF-626 in Linear. Automatische goedkeuringscontrole wees die externe publicatie af. Geen document/status/comment gepubliceerd; geen andere route geprobeerd. Alleen externe documentatie wacht.

## Daarna — al geaccordeerd

- [ ] S2: O2-documenten duurzaam bewaren en strikt herladen; C118.
- [ ] U1: editor en actuele/historische beoordeling.
- [ ] E1: additief exportveld met herbinding op de werkelijk geëxporteerde kandidaat.
- [ ] Modelkwalificatie volgens protocol, pas na labels/freeze en binnen het begrensde budget.
- [ ] Geïntegreerde eindcontrole en oplevering; productieactivering blijft afzonderlijk.

Volgende actie: de onafhankelijke S1-review afronden en één concreet voorstel maken voor aantoonbaar benodigde extra bestanden. Correcties binnen bestaand mandaat bij dezelfde Claude-uitvoerder; geen onafhankelijke review opnieuw starten zonder nieuwe wijziging of open bevinding.

