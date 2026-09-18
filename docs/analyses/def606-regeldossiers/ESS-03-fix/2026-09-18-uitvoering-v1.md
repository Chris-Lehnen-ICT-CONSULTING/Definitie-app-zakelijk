# DEF-766 — ESS-03-fix en verificatie

18 september 2026. De afgebakende ESS-03-appfix en bijbehorende skillteksten zijn geïmplementeerd, getest en onafhankelijk gereviewd. De volledige menselijke beoordelingsketen is **niet afgerond**: daarvoor ontbreekt het gedeelde DEF-624-contract. Geen commit, push, merge, databaseactivering of skillinstallatie uitgevoerd.

## Resultaat

ESS-03 beoordeelt telbaarheid en individuatie bij dezelfde betekenis, informatie en context. De regelkaart, voorbeelden, generatie-instructie, toetsuitleg en hersteladvies volgen die norm. Een nummer, naam, code of woordtreffer geeft geen semantische goed- of afkeuring meer. De regel gebruikt `judgment_review`, `review_required` en `no_score`; term en definitietekst zijn verplicht. Ontbrekende invoer, open beoordeling en technische fouten zijn onderscheiden. De gedeelde UI toont de open beoordelingsvraag. Geen nieuwe ESS-03-gate of automatische herstelactie ingevoerd.

De vijf bijbehorende skillpassages zijn aangepast in een afzonderlijke beheerwerkboom. De gerichte ESS-03-score-uitzondering is ook in het toetsregels-entrypoint aangebracht. Eerdere CON-01/02- en ESS-01/02-teksten zijn behouden.

## Bewijs

Alle hieronder genoemde bewijsbestanden en volledige CLI-logs zijn bewaard onder [reports/DEF-766-20260918](/Users/chrislehnen/.codex/worktrees/2075/Definitie-app/reports/DEF-766-20260918). Deze map is git-ignored; dit verslag is wel onderdeel van de werkdiff.

| Controle | Eindresultaat | Bewijsbestand |
|---|---|---|
| Unitgate `make test` | 6616 passed, 75 skipped, 722 deselected, 1 xfailed, exit 0 | `final-make-test.log` |
| `make lint` | Ruff en Black exit 0 | `final-make-lint.log` |
| Offline ketentest | 3 passed, exit 0 | `final-offline-journey.log` |
| Onderzoekscasussen door echte service | 13 × manager/cache = 26 uitkomsten conform verwachting; geen ESS-03-violation of cijfer | `proef-na-fix.json`, `proef-na-fix.log` |
| TDD | 62 nieuwe tests faalden op oude implementatie; 2 invarianten slaagden; daarna 64 groen | `red-def766-tests.log`, `green-def766-tests-run1.log` |
| Skillcorrectie | 38 gerichte checks en referentie-/descriptioncontroles geslaagd | `skills-correction-report-v1.md` |
| Onafhankelijke review | Beide P2-bevindingen gesloten; geen resterende bevindingen binnen scope | `app-review-v2.md`, `skills-review-v2.md` |

De basis had 6557 geslaagde unit-tests. De tussenstand brak bestaande prompt-aantalsasserties. Dezelfde Claude-uitvoerder corrigeerde de ESS-03-formulering en herstelde de bestaande DEF-750-test naar HEAD; geen bestaande asserties verzwakt. De volledige eindunitgate is daarna opnieuw uitgevoerd. De andere P2 betrof een ontbrekende ESS-03-score-uitzondering in het skill-entrypoint en is door dezelfde skilluitvoerder hersteld. Beide oorspronkelijke reviewers controleerden de eigen correctiediff.

De generieke skillvalidator weigert reeds op de basis repo-eigen frontmatterkeys; dit is geen nieuwe fout. Repo-validaties en YAML-parse slagen. Skillcontroles bewijzen tekstconsistentie en vindbaarheid, geen modelgedrag. De servicecases zijn synthetisch, geen expertgoldset; geen echte modelcalls uitgevoerd.

## Identiteit en daadwerkelijke CLI-rollen

| Onderdeel | Werkboom / basis / sessie |
|---|---|
| App | `/Users/chrislehnen/.codex/worktrees/2075/Definitie-app`, branch `bugfix/DEF-766-ess03-telbaarheid`, basis `4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb` |
| App-implementatie en correctie | echte `/Users/chrislehnen/.local/bin/claude` 2.1.270, sessie `249fbdd8-5a76-4551-aeb8-c9405211296a`; log `claude-implementation-v1.jsonl` |
| App-review en deltareview | Codex CLI, sessie `01a0b513-20c4-79e1-9ead-b64d3ffcbc7b`; logs `codex-app-review-v1.jsonl`, `codex-app-review-v2.jsonl` |
| Skills | `/private/tmp/def766-skills`, branch `bugfix/DEF-766-ess03-skills`, basis `9f5ae6f3bb4b990a855bc0969bc4f6067c02c197` |
| Skillimplementatie en correctie | echte Claude Code CLI, sessie `358c4720-9168-450e-8d64-233f7d40809b`; logs `claude-skills-v1.jsonl`, `claude-skills-correction-v1.jsonl` |
| Skillreview en deltareview | Codex CLI, sessie `01a0b50e-e49b-7880-b877-b86fd3d3e68d`; logs `codex-skills-review-v1.jsonl`, `codex-skills-review-v2.jsonl` |

Claude-uitvoerders hadden alleen Bash/Read/Edit/Write en geen MCP-tools; de gecontroleerde sessieresultaten melden nul gestarte subagents. Codex-reviewers draaiden read-only met delegatie uitgeschakeld. De coördinator schreef geen software, tests of bijbehorende promptteksten.

Exact beoordeelde app-identiteit: 15 software-/testbestanden in `app-verification-manifest-v2.json`, SHA256 `c7fb78168a577b42b8261dbd5a87b42299a8d0f19aff3468989938366961e4d4`; patch `def766-diff-v1.patch`, SHA256 `c3484d50a845ec076e2312083aa89bf97c142aa9f2b144f3796b34250d4ac538`.

Exact beoordeelde skillidentiteit: 8 bestanden in `skills-review-manifest-v2.json`, SHA256 `d10531485f649380aabf16eb1d4a10dd4a76c903cbb5fda3742ae9e869582ae2`. Een volledige skillpatch inclusief nieuwe referenties is als `skills-final.patch` bewaard. De coördinator heeft beide eindmanifests tegen de werkbestanden gecontroleerd: nul afwijkingen; zie `coordinator-verification.json`.

## Open gedeelde aansluiting

De huidige generieke oordeel-evaluator leest geen opgeslagen menselijke regelreviews terug. De app kent daarvoor alleen CON-01/02-specifieke opslag en voor ESS-02 een categoriekeuze-event. Een afgerond ESS-03-oordeel of bevestigde niet-toepasselijkheid kan daarom nog niet versiegebonden worden opgeslagen, teruggelezen en als afgerond worden getoond. ESS-03 blijft tot de gedeelde uitbreiding ter beoordeling staan. Dit is het expliciet open acceptatiecriterium 5; geen volledige ketengoedkeuring geclaimd.

`contract-gap-v1.md` bevat de codeverwijzingen en besluitopties. Chris is gevraagd of dit onder DEF-624 blijft of eerst een generiek contractvoorstel nodig is. Het vervolgbericht ‘ga verder aub’ is gevolgd door afronding van de onafhankelijke fixes en reviews; er is geen nieuwe status, opslagmarker, schema of ESS-03-knop verzonnen. Verbreding van de specifieke DEF-751-conflictuitvoer naar teleenheid is evenmin besloten.

De gemelde skillbron-drift uit het app-uitvoerdersrapport is nader opgelost als **basiskeuze**: de actieve, beheerde DEF-754-branch is gevonden en de vijf doelbestanden kwamen exact overeen met de geïnstalleerde versies. De primaire beheercheckout en `origin/main` liepen achter. Daarom is de skillfix van die geverifieerde DEF-754-basis afgetakt; niets blind teruggesynchroniseerd of geïnstalleerd. Publicatie moet deze bestaande afhankelijkheid behouden.

Het afgeronde onderzoeksdossier in werkboom 6554 is ongewijzigd bewaard; geen onderzoek herstart en geen Cowork-UI overgenomen.
