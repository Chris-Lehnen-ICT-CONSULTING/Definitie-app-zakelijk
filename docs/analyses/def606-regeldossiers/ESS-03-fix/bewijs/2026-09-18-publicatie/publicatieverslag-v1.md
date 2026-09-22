# DEF-766 — publicatie afgerond, menselijke reviewketen open

18 september 2026. Dit verslag actualiseert de publicatiestand uit het eerdere uitvoeringsverslag; het oorspronkelijke test- en reviewbewijs blijft bewaard.

## Gepubliceerd

- App-PR [465](https://github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk/pull/465) regulier gemergd op 18 september om 16:00:16 UTC. Beoordeelde head f51a38307d8ca36591e9363c9c1aa1bdd859ead7; ongewijzigde basis 4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb; merge 2c9a6e3a13afa4ecbe39163cc418e2b0f8c41644. Alle 29 PR-controles geslaagd.
- Skill-PR [334](https://github.com/ChrisLehnen/claude-global-setup/pull/334) regulier gemergd. Beoordeelde head f9f6e1da1868b0cdfddb81eb67b970132c17c64b; merge 5ad373d17085044d73d4e39a8439cbce25931124. Drie CI-controles geslaagd; acht teksten identiek aan de eindreview, vijf Cowork-pakketten bytegewijs gelijk aan de bron.
- Geen branches of werkbomen verwijderd. Geen claim dat een draaiende app al is herstart of dat de skills live zijn geïnstalleerd.

## Functioneel bewijs en bronbinding

Lokale unitgate: 6616 passed, 75 skipped, 722 deselected, 1 xfailed, exit 0; lint exit 0; offline journey 3 passed; 13 onderzoekscasussen via twee echte laadpaden: 26/26 conform verwachting.

CI op de gepubliceerde apphead: 6606 passed, 85 skipped, 722 deselected, 1 xfailed; coverage 64%, gate geslaagd. Acceptance/smoke 21 passed, 5 skipped. Integration 571 passed, 29 skipped, 15 xfailed, 2 xpassed; gate exit 0. Zie app-ci-tests-v1.log en app-pr-final-checks-v2.json. Lokale en CI-aantallen afzonderlijk gerapporteerd.

Normale commitcontrole vond twee ISC004-opmaakfouten in één nieuw testbestand. Dezelfde Claude-uitvoerder corrigeerde uitsluitend haakjes om twee stringconcatenaties. AST-identiteit met de eerder beoordeelde versie bevestigd; overige 14 bestanden onveranderd; gepinde Ruff/Black en 65 gerichte tests opnieuw groen. Dezelfde Codex-reviewer keurde de opmaakdelta goed. Eindmanifest-v3 SHA256 48d837aa5019d20908ac66cc1bbab7800f5655d4c1a43e7e4023afd88165e477 is tegen alle 15 bestanden in commit en werkboom geverifieerd. Normale hooks, prepush lint en dependency-audit bleven actief.

Vier echte generatieproeven via bestaande PromptServiceV2/AIServiceV2 en geconfigureerd claude-opus-4-8: eiland, water als stof, watermonster, boekexemplaar. Geen cache/retries, geen databaseopslag. Geen identifierplicht of stof→monster-verschuiving waargenomen. Alle vier kandidaten terug als scoreloze open ESS-03-beoordeling. Plaatsing bij boekexemplaar blijft inhoudelijk twijfelachtig; andere regels geven eveneens bevindingen. Kleine synthetische steekproef, geen statistisch kwaliteitsbewijs of expertacceptatie. Zie modelproef-report-v1.md, modelproef-v1.json en modelproef-coordinator-verification-v1.json. De bronbestanden bleven identiek aan de gepubliceerde commit tijdens deze proef.

## Daadwerkelijke rollen

Claude Code CLI implementeerde en corrigeerde; Codex CLI reviewde de concrete diffs read-only. Coördinator controleerde bewijs, publiceerde en schreef uitsluitend coördinatiedocumenten/artefactverwerking.

| Rol | Sessie | Bewijs |
|---|---|---|
| Appimplementatie, lintcorrectie en modelproef | 249fbdd8-5a76-4551-aeb8-c9405211296a | claude-publication-lint-v1.jsonl; claude-modelproef-v1.jsonl; eerdere claude-implementation-v1.jsonl in reports/DEF-766-20260918 |
| Appreview en gerichte deltareviews | 01a0b513-20c4-79e1-9ead-b64d3ffcbc7b | app-review-v3.md; codex-app-review-v3.jsonl; eerdere app-review-v2.md in vorige bewijsmap |
| Skillimplementatie/correctie | 358c4720-9168-450e-8d64-233f7d40809b | claude-skills-v1.jsonl en claude-skills-correction-v1.jsonl in vorige bewijsmap |
| Skillreview | 01a0b50e-e49b-7880-b877-b86fd3d3e68d | skills-review-v2.md en codex-skills-review-v2.jsonl in vorige bewijsmap |

## Resterend — niet als voltooid aangemerkt

1. Gedeelde menselijke reviewafronding: opslag, teruglezen, uitkomsten en bevestigde niet-toepasselijkheid, actualiteit en bediening. Dit vraagt besluiten onder DEF-624/626/627/630; DEF-766 blijft open. Eerste keuze aan Chris gesteld: gedeelde voorziening, eerst ESS-03 (advies), of specifiek voor ESS-03, of uitstellen. Nog geen antwoord ontvangen. Daarna pas één volgend punt tegelijk bespreken.
2. Verduidelijkingsgedrag voor teleenheid en conflicten; geen stilzwijgende verbreding van DEF-751.
3. Volledige menselijke ketenacceptatie na implementatie van die besluiten. De huidige tests bewijzen die ontbrekende keten niet.
4. Live-skillinstallatie. Bestaande marker /Users/chrislehnen/.claude/.global-setup-deployment-freeze-ALG-391 zegt: “Opheffen: UITSLUITEND handmatig, na expliciet akkoord — plan v7 Task 10.” Niet opgeheven of omzeild. Acht doelbestanden komen nog overeen met de oude basis; inventaris en bronhashes voorbereid in skills-installation-inventory-v1.json.

Voorstel: docs/adr/ADR-002-menselijke-regelbeoordeling-v1.md is lokaal, untracked en expliciet Voorgesteld. Geen nieuw schema, enum, reviewdatabase of blokkerende policy goedgekeurd of gebouwd.
