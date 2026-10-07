# INT-02 O2 — takenlijst v36
28 september 2026. Vervangt v35 als actuele procesingang.

## Afgevinkt
- [x] WP5a/typecorrecties: commit f9bb9e697.
- [x] Q1 kwalificatierunner: commit ebe9c1b7c26ffe6040bffb66db4937b932406dc8; 176 tests en onafhankelijke review groen.
- [x] S1 eerste implementatie en onafhankelijke review: negen concrete bevindingen.
- [x] R01/R02/R09 gesloten binnen gecontroleerd bereik. R03 centrale schrijver en interne R07-draftcreate gesloten; externe doorwerking open.
- [x] R08 identieke editorherhaling met categoriekeuze werkt zonder nieuwe schrijfacties in de tabellen; afwijkende keuzeactie geweigerd.
- [x] R08 auditreden bij editor en gewone update: identieke reden blijft idempotent; gewijzigde reden wordt geweigerd. Onafhankelijk gereproduceerd.
- [x] Correctie3: 63 gerichte regressietests geslaagd; acht nieuwe gevallen eerst rood op correctie2.
- [x] Herreview3 afgerond; alle zestien bronhashes in beide werkbomen, elf statische bewijzen en beide diffs bevestigd.

## Open — geen actieve CLI
- [ ] **R08 duplicaat-create:** volledige oude samengestelde eventtekst als nieuwe expliciete reden wordt nog ten onrechte als identieke herhaling geaccepteerd. Binnen bestaande bestanden, bewezen in herreview3. Geen vierde correctieronde gestart na drie rondes; terugkoppeling volgens de stopregel uit de opdracht.
- [ ] Besluit op aanvullende gerichte R08-correctieronde. Doel: de vergelijking met/zonder duplicaatdeel aan de oorspronkelijke create-actie binden, zodat andere expliciete reden conflict geeft en echte retry blijft werken. Eerst het concrete tegenvoorbeeld rood vastleggen; dezelfde Claude/Codex-rollen. Als oorspronkelijke actie niet ondubbelzinnig uit bestaande gegevens volgt, dat melden; geen ongeautoriseerde schemawijziging.
- [ ] Besluit op [scopevoorstel v2](/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/s1-scopeaanvulling-voorstel-v2.md): 50 extra bestaande bestanden (11 productie, 39 tests/fixtures), 700–1500 regels geraamd. De eerdere vraag staat nog open.
- [ ] S1 externe R03-aanroepers, R04 leestransacties, R05 historisch schemaherstel, R06 fixtures en externe R07-voorkeurstermroute.
- [ ] S1 eindverificatie en normale lokale commit; nu ongecommit en ongestaged.
- [ ] Daarna de al geaccordeerde S2 O2-documentbewaring/herladen, U1 editor, E1 export.
- [ ] Goldsetbeoordelaars kiezen, labels inhoudelijk accepteren, freeze. Daarna modelkwalificatie binnen 43 appcalls + 43 tokenmetingen / US$12; nog nul nieuwe appcalls.
- [ ] Geïntegreerde eindcontrole en oplevering; productieactivering afzonderlijk.

## Finale stand en bewijs
Werkboom: /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app
Branch: feature/DEF-626-validatiesnapshots; HEAD ebe9c1b7c26ffe6040bffb66db4937b932406dc8.
Dossier: /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2
Volledige diff-SHA256: a5ec70465099edddab285cdc08e265ad538b464b01aec406a6900605afab6f90.
Correctie3-delta: f4324a91c8cd72f6775f0138b7bb8821a7e69f5ec646cb81b900be17e32af905.
[Onafhankelijke herreview3](/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/s1-codex-herreview-correctie3-v1.md).

Claude Code CLI: sessie7f05cfbc-1970-4a7b-a241-c4693f11f217, correctie3-exec81750 exit0.
Codex CLI: sessie01a0e928-8d33-7c31-b145-6aec14fe4d59, herreview3-exec51917 exit0.
Volledige opdrachten/logs in dossier. De coördinator heeft geen software of tests geïmplementeerd.

## Bewijsgrenzen
63 gerichte R-tests passed. Totale gerichte selectie247 geslaagd / 24 bekende fouten; keuzepad128 geslaagd / 19 bekende fouten. Extern 115 bekende R03-ID’s. Ruff/Black/mypy schoon; complexiteit204>201 (basis205), geen drempelwijziging. Het reviewerprobescript eindigt exit0 maar bevat het falende producttegenvoorbeeld; geen totaalgoedkeuring van S1 of volledige-appsuiteclaim.

Actions blijven UIT. Geen push, merge, productiedata, productieactivering of echte databasemigratie. Geen bestanden/tests/historie verwijderd. Prompt Forge-fallback blijft geldig. De specifieke Linearpublicatievraag blijft onbeantwoord na automatische afwijzing; niet gepubliceerd/omzeild.
