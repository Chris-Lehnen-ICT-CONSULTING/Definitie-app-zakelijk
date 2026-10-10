# INT-02 O2 — takenlijst v41

29 september 2026. Vervangt v40. Dit is de actuele procesingang.

## Uitgevoerd en geverifieerd

- [x] Chris' akkoord op de vierde R08-correctie en de uitbreiding met 50 bestanden vastgelegd.
- [x] De goedgekeurde uitbreiding uitgevoerd binnen de 66 aangewezen bestanden.
- [x] 116/116 eerdere R03-testgevallen geslaagd; onafhankelijk gecontroleerd op volledige test-ID's.
- [x] 55 nieuwe testgevallen toegevoegd in de uitbreiding; geen bestaande test-ID verdwenen. RED: 51 failed / 4 reeds groen; 16 onderscheidende mutanten.
- [x] R04: leesroutes en aansluiting bij de buitenste transactie gesloten binnen het geteste bereik.
- [x] R05: oorspronkelijke profielblokkade, uitgevoerde historie-, backup- en foutmatrix onderbouwd. Eén hersteltest heeft nog een verkeerde startupverwachting; zie open punten.
- [x] R06: fixtures, behoud van bestaande testgevallen en bewaring van de twee afgewezen tijdelijke checkerproeven gesloten.
- [x] R07: centrale voorkeurstermschrijver gesloten; de productieaanroepers blijven open.
- [x] R10: UFO- en Toepassen-races gecorrigeerd en onafhankelijk gesloten. Alleen eigen bevestigde versies worden overgenomen.
- [x] Definitieve UI-selectie: 74 passed. De testfile met de drie timinggevallen en positieve paden: 13 passed; deze selecties overlappen.
- [x] Finale bronhashes in implementatie en review gelijk; onafhankelijke rapporten en proeven in het uitvoeringsdossier bewaard.

## Wacht op twee afzonderlijke besluiten van Chris

1. [ ] **R08-opslagactievoorstel:** oorspronkelijke create-actie als gestructureerde gegevens in het bestaande audit-JSON bewaren, inclusief de begrensde vervanging van de eerdere helpers.
   Voorstel: s1-r08-opslagactie-voorstel-v1.md.
   SHA256: c554b60603ea8b44e06f99b4d57b54c43d3da25138ee4164feb7a6fbc9372140.
2. [ ] **Restdoorwerking in 9 extra bestanden:** voorkeurstermroutes en invoertransport herstellen, testcontracten herijken en gedeeltelijke importopslag als mislukking melden via bestaande resultaatvelden.
   Voorstel: s1-restdoorwerking-voorstel-v1.md.
   SHA256: d6b3d2b0e32fd08cf0e04ea287a0775e29ddbf679ec2430194b9fa164ef8c987.

Beide vragen zijn gesteld en nog onbeantwoord. Het eerdere akkoord op 1 en 2 betrof andere concrete voorstellen: vierde correctieronde en 50-bestandenscope. Het geeft deze nieuwe contract-/scopebesluiten niet automatisch.

## Nog open voor volledige oplevering

- [ ] R08 sluiten na geaccordeerde opslagafspraak en correctie.
- [ ] R03/R07 als volledige keten sluiten: de voorkeurstermaanroepers/import werken nog niet correct.
- [ ] R06: vijf extra testbestanden herijken. Daaronder de schema-4-hersteltest, zodat ook de latere verliesvrijheidsasserties worden uitgevoerd, en de bewust rode DEF630-proef weer haar bedoelde contractassertie bereikt.
- [ ] Test- en kwaliteitsgates afhandelen; geen volledige groene S1-claim.
- [ ] S1 afronden en lokaal committen.
- [ ] Daarna S2, U1 en E1 uitvoeren (reeds geaccordeerd).
- [ ] Goldsetbeoordelaars kiezen, labels vastleggen en goldset bevriezen; daarna modelkwalificatie binnen 43 appcalls + 43 tokenmetingen / US$12.
- [ ] Geïntegreerde appverificatie en oplevering. Activering afzonderlijk.

## Bewijsgrenzen en bekende problemen

De brede unitrun op de eerdere scopeaanvullingsbron had 8.656 passed, 13 failed en 1 collection error. Elf FAILED-uitkomsten vragen de genoemde testdoorwerking; twee performance-trackerfailures en de collectionfout komen ook op de pakketstart voor. De volledige oorzaken van die baselineproblemen zijn daarmee niet opnieuw gediagnosticeerd.

De UI-correcties zijn daarna gericht hertest: de finale effectselectie heeft 174 passed en dezelfde zes history/offline-failures als vóór de wijziging. Er is geen nieuwe volledige unitrun op de huidige bron geclaimd.

Ruff, Black en mypy zijn groen voor het gecontroleerde bereik. De complexiteitsgate blijft **204 > 201**, gelijk aan de pakketstart; geen waiver of drempelverhoging.

De metadata-only-checker blijft een bestaand no-op-pad; de synoniemsynchronisatie kan vóór een buitenste commit plaatsvinden. Deze grenzen zijn niet opgelost of stilzwijgend geaccepteerd. De specifieke Linear-publicatie blijft op haar eerdere afzonderlijke besluit wachten.

## Werkstaat en bewijsverwijzingen

Implementatie: /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app
Branch: feature/DEF-626-validatiesnapshots.
Basis/HEAD: ebe9c1b7c26ffe6040bffb66db4937b932406dc8.
Huidige bron is ongecommit. Geen uitvoerder of reviewer meer actief.

Dossier: /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2

- Uitvoering: s1-scopeaanvulling-uitvoering-v1.md en s1-scopeaanvulling-uitvoering-errata-v1.md.
- Finale bewijscontrole: s1-codex-bewijscontrole-scopeaanvulling-v1.md.
- UI-correcties: s1-r10-correctie-uitvoering-v1.md en s1-r10-toepassen-uitvoering-v1.md.
- Herreview: s1-codex-herreview-r10-v1.md, SHA256 c5e362701f898c1b49efcf8a23ed50f4a49b795faee7d08931e528b54660f758.
- Manifest: bewijs/s1-r10-reviewmanifest-v1.json, SHA256 afbcb585e6d52b5807cdf65ed95da9498fd718cd2974b7be3bfdd9f35d6ea45d.
- Volledige diff: bewijs/s1-r10t-diff-v1.patch, SHA256 b0221659ef8e287e47ddf2c75c643d894c61601261053aeaea4704772bbf7c9a.
- Aggregate van 66 bronbestanden: 44ec5b68660fae61326cc3d65854c19867b1b3cc0a0f932deaa1e6130cb8bd0b.

Claude Code CLI implementeerde in sessie 7f05cfbc-1970-4a7b-a241-c4693f11f217. Codex CLI reviewde onafhankelijk in sessie 01a0e928-8d33-7c31-b145-6aec14fe4d59.

Actions blijven UIT. Geen push, merge, productieactivering, echte databasemigratie of nieuwe modelcalls. Nieuw verbruik modelkwalificatiebudget: 0. Prompt Forge-fallback en eerdere beveiligingsgrenzen blijven gelden.
