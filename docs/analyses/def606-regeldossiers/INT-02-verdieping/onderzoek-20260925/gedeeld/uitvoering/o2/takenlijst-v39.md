# INT-02 O2 — actuele takenlijst v39
29 september 2026. Vervangt v38 als procesingang.

## Afgevinkt
- [x] Vierde R08-correctie en scopeaanvulling-v2 met 50 extra bestanden geaccordeerd door Chris.
- [x] Q1: commit ebe9c1b7c, 176 tests en onafhankelijke review.
- [x] Vierde R08-correctie uitgevoerd en onafhankelijk beoordeeld. Het verkeerde succes bij een afwijkende reden is gesloten binnen het geteste bereik.
- [x] Herreview4 concreet verwerkt: R08 blijft open omdat identieke create-herhalingen na wijziging van een ander record worden geweigerd. Dit is niet geaccepteerd als contractversoepeling.
- [x] Concreet R08-opslagactievoorstel vastgelegd en afzonderlijk voorgelegd.

## In uitvoering / nog open
- [ ] S1-uitbreiding: Claude rondt de definitieve tests, mutatieproeven, gates en het rapport af. De eerste run is geen eindbewijs; finale versie v2 moet bij dezelfde bron horen.
- [ ] Daarna gerichte beoordeling door dezelfde Codex CLI-reviewer van R03/R04/R05/R06/R07 en de concrete uitbreiding.
- [ ] Resterende fouten buiten de 66 toegestane bronbestanden exact classificeren en afhandelen; nog geen toestemming voor verdere scope-uitbreiding.
- [ ] R08-opslagactievoorstel: wacht op expliciet contractbesluit. Dit blokkeert bovenstaande werkzaamheden niet.
- [ ] S1-bevindingen sluiten, eindverificatie en lokale commit.
- [ ] Vervolgens S2, U1, E1 (reeds geaccordeerd).
- [ ] Goldsetbeoordelaars, labels en freeze; daarna modelkwalificatie binnen 43 appcalls + 43 tokenmetingen / US$12. Nieuw verbruik: 0.
- [ ] Geïntegreerde oplevering; activering afzonderlijk.

## Processen en bewijs
Implementatie: /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app
Branch: feature/DEF-626-validatiesnapshots; HEAD ebe9c1b7c26ffe6040bffb66db4937b932406dc8.
Claude-sessie: 7f05cfbc-1970-4a7b-a241-c4693f11f217; actieve exec23725.
Opdrachten: s1-scopeaanvulling-opdracht-claude-v1.md en s1-scopeaanvulling-afrondopdracht-claude-v1.md.
Review: /Users/chrislehnen/.codex/worktrees/def626-s1-review/Definitie-app; nog correctie4.
Codex-sessie: 01a0e928-8d33-7c31-b145-6aec14fe4d59; momenteel geen actieve reviewrun.
Dossier: /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2
Herreview4: s1-codex-herreview-correctie4-v1.md; bronmanifest bewijs/s1-correctie4-reviewmanifest-v1.json.
R08-voorstel: s1-r08-opslagactie-voorstel-v1.md; SHA256 c554b60603ea8b44e06f99b4d57b54c43d3da25138ee4164feb7a6fbc9372140.

## Grenzen
Actions UIT. Geen push, merge, productieactivering, productiedata, echte databasemigratie of nieuwe modelcalls.
Geen verwijderingen buiten expliciet geaccordeerde wijzigingen. Prompt Forge-fallback blijft gelden; eerdere beveiligingsweigeringen niet omzeilen.
Complexiteitsgate was 204 > 201 (basis 205); nog geen volledig groene S1-claim.
Specifieke Linear-publicatie en goldsetbeoordelaars blijven open besluiten.
