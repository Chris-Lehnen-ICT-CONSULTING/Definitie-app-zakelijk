# DEF-835 — actuele takenlijst v27

28 september 2026. Deze versie vervangt v26 als actuele ingang. Werkboom: /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2. Branch: feature/DEF-835-int02-o2. Basiscommit: f9bb9e6973926a3cf768995f5d879f6edfd6322d; Q1 is nog niet gecommit.

## Besluiten en grenzen

- [x] Chris gaf “akkoord! go” op Q1, S1, S2, U1 en E1, de concrete contracten, de twee genoemde triggervervangingen en het proefbudget van maximaal 43 appcalls / 43 tokenmetingen / US$12. Zie vervolg-akkoord-v1.md.
- [ ] De keuze van goldsetbeoordelaars staat nog open: twee mensen of twee onafhankelijke CLI-voorstellen met Chris als inhoudelijke beoordelaar.
- Actions blijven uit. Geen push, merge, productieactivering of productiedata. Er zijn nog nul nieuwe appcalls gedaan.

## Gereed

- [x] WP5a en eerdere typecorrecties gecommit en onafhankelijk gereviewd.
- [x] Q1 gebouwd door Claude CLI binnen de drie toegestane software-/testbestanden.
- [x] Eerste TDD: 79 failures / 77 geslaagde tests → 156 geslaagd.
- [x] Onafhankelijke review bewees F1 (parallelle calls), F2 (p95) en F3 (bewijsopslag).
- [x] Eerste correctie: 15 failures / 156 geslaagd → 171 geslaagd; coördinator herhaalde de tests en lint op dezelfde hashes.
- [x] Dezelfde reviewer sloot F1 en F2; beide artefactfouten van F3 zijn ook gesloten.
- [x] Resterende F3-fout bij fsync ná flush gericht gecorrigeerd: vooraf blijvende open markering, pas na geslaagde afronding atomair naar voltooid.
- [x] Uiteindelijke volledige Q1-run: 176 geslaagd; Ruff/Black groen. Coördinator herhaalde alle 8 F3-tests: geslaagd, 168 andere tests niet opnieuw geselecteerd. Bronhashes gelijk; volledig bewijs blijft geldig.
- [x] Veertig nieuwe, ongelabelde synthetische conceptgevallen opgesteld. Nog geen expertlabels, splitsing of freeze. Software-uitvoerder en reviewer hebben deze pool niet gelezen.

## Actief

- [ ] **Laatste gerichte F3-herreview** door dezelfde Codex CLI-reviewer. Opdracht: q1-F3-fsync-opdracht-codex-v1.md. Verwacht verslag: q1-codex-F3-eindreview-v1.md.
- [ ] Na gesloten bevindingen: normale lokale Q1-commit met alle gebruikelijke hooks; bronblobs vergelijken met reviewmanifest.

Claude-sessie: 585f02d8-1256-466a-a2ac-ae45d7cbc746 (klaar).
Codex-reviewer: 01a0e8ca-2df9-7780-ba7a-b18c26caefe7 (actief).
Reviewwerkboom: /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app.
Finale bronbinding: bewijs/q1-reviewmanifest-v3.json, q1-coordinator-v3.json en q1-F3-fsync-hashmanifest-v1.json. Uitvoering: q1-uitvoering-v2.md.

## Daarna — akkoord is al verleend

- [ ] S1: gedeelde DEF-626-opslag op eigen featurebranch; conceptbriefing en actuele Linear-bronkopie liggen klaar.
- [ ] S2: O2-documentopslag, herladen en C118.
- [ ] U1: editor/weergave; E1: export.
- [ ] Benoemde beoordelaars leveren onafhankelijke labels; Chris accepteert; daarna freeze.
- [ ] Begrensde modelevaluatie, pas na labels/freeze.
- [ ] Geïntegreerde eindverificatie en oplevering; activering blijft een afzonderlijk besluit.

De eerdere update van v25 is door de lokale hook geweigerd. Dat doel is intact gebleven; opvolgende werkstaten zijn volgens de gebruikersafspraak nieuwe versies. Geen beveiligingscontrole is omzeild.

