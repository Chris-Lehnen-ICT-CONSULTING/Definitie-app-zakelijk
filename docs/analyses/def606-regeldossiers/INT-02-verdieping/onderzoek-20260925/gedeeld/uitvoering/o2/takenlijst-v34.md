# INT-02 O2 — takenlijst v34
28 september 2026. Vervangt v33 als actuele procesingang; eerdere bewijsverwijzingen blijven geldig.

## Afgevinkt
- [x] WP5a/typecorrecties: f9bb9e697.
- [x] Q1 kwalificatierunner: ebe9c1b7c26ffe6040bffb66db4937b932406dc8, 176 tests en onafhankelijke review groen; lokaal gecommit.
- [x] S1 eerste implementatie en onafhankelijke review: negen concrete bevindingen vastgelegd.
- [x] Correctie1: R01/R02/R09 gesloten; R03-writer en interne R07 gesloten, externe doorwerking open.
- [x] Correctie2: identieke editoropslag met categoriekeuze werkt zonder writes; keuzeconflicten geweigerd. 51 gerichte regressietests geslaagd.
- [x] Herreview2: 16 bronhashes, 29 bewijsbestanden en volledige/correctiediff bevestigd. Oorspronkelijk R08-editorvoorbeeld gesloten; andere expliciete auditreden blijft ten onrechte als identiek bevestigd.
- [x] Deze resterende R08-fout geaccepteerd voor correctie binnen de bestaande scope en aan dezelfde Claude-uitvoerder teruggegeven.

## Actief
- [ ] Correctie3: dezelfde run-ID met afwijkende expliciete auditreden moet worden geweigerd; identieke effectieve reden blijft idempotent. Eerst rood, dan minimale correctie, gerichte verificatie en dezelfde onafhankelijke reviewer.
- [ ] S1 resterend: externe R03-aanroepers, R04 leestransacties, R05 historisch schemaherstel, R06 fixtures en externe R07-voorkeurstermroute.
- [ ] Besluit op s1-scopeaanvulling-voorstel-v2.md: 50 extra bestaande bestanden (11 productie, 39 tests/fixtures), 700–1500 regels geraamd. Dit vervangt het onbeantwoorde tienbestandsvoorstel; nog geen uitbreiding uitgevoerd.
- [ ] Na sluiting S1: S2 O2-documentbewaring/herladen, U1 editor, E1 export.
- [ ] Goldsetbeoordelaars kiezen, inhoudelijke labels accepteren, freeze; daarna modelkwalificatie binnen geaccordeerde 43 appcalls + 43 tokenmetingen / US$12. Nog nul nieuwe appcalls.
- [ ] Geïntegreerde eindcontrole en oplevering; productieactivering afzonderlijk.

## Bewijsgrenzen
Correctie2 totale gerichte selectie: 235 passed / 24 bekende failures. Geraakt categoriekeuzepad: 128 passed / 19 bekende failures, identiek aan correctie1. Extern 115 bekende R03-failure-ID’s; geen volledige-appsuitegroen. Ruff/Black/mypy schoon; complexiteit 204 > 201 (basis205), geen drempelwijziging.

Werkboom: /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app
Branch: feature/DEF-626-validatiesnapshots; HEAD ebe9c1b7c. S1 ongecommit/ongestaged.
Dossier: /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2
Correctie2-diff: 48f6f0e27307d8af21a72e25f7062b455604f6f7116fc3e583ad2cecd22a1e3a.
Rapport: s1-codex-herreview-correctie2-v1.md.
Actieve opdracht: s1-reviewcorrectie3-opdracht-claude-v1.md.
Claude-sessie7f05cfbc-1970-4a7b-a241-c4693f11f217, exec81750.
Codex-reviewer01a0e928-8d33-7c31-b145-6aec14fe4d59; herreview2 afgerond, exec18211 exit0.

Actions UIT. Geen push, merge, productiedata of productieactivering. Geen bestanden/tests/historie verwijderd. Prompt Forge-fallback blijft geldig.
De specifieke Linearpublicatievraag blijft onbeantwoord na automatische afwijzing; geen externe publicatie of omweg.
