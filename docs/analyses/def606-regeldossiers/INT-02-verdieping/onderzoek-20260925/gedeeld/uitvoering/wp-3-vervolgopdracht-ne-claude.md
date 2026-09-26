# WP3 hervatten — akkoord NE-doorgifte, 26 september 2026

Je bent dezelfde Claude Code CLI-uitvoerder, sessie a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. De coördinator verifieert, een afzonderlijke verse Codex CLI-sessie reviewt in WP5 de concrete volledige diff. Nederlands. Geen commit/push/PR/Linear-mutatie of WP4 starten.

## Akkoord en werkstaat

Chris antwoordde op 26-09-2026 “Akkoord” op wp3-transportbesluit-v1.md: bestaande WP3-stand van 685 regels geaccepteerd; gerichte NE-doorgifte via rule_results, additieve schemawijziging en algemene contractversie 2.2.0 goedgekeurd. Drie extra bestanden zijn goedgekeurd; totaal vijftien inhoudelijke bestanden, raming circa 785–865 gewijzigde regels. Dit is een raming: meld afwijkingen eerlijk, verminder geen casusdekking of leesbaarheid om een getal te halen. De functies en vijftien bestanden begrenzen de scope; nieuwe inhoudelijke scope eerst melden. De zes S1-markers en alle eerdere besluiten blijven goedgekeurd.

Appwerkboom /Users/chrislehnen/Projecten/Definitie-app, branch feature/DEF-771-int02-contract-o1, basis 0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d plus WP1–3. Skillwerkboom /Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills, dezelfde branch, basis 1e27a2da7668437423af3962cce48af5f1bc591b. Behoud alle bestaande wijzigingen; jij bent alleen schrijver van jouw inhoudelijke scope. Coördinator beheert takenlijst, opdrachten en status.

Dossier: docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/. Lees wp3-transportbesluit-v1.md en hergebruik je context uit wp-3-opdracht-claude.md. Geen nieuwe inventarisatie. De coördinator heeft 45 tests groen gereproduceerd (wp3-coordinator-tussenverificatie.log) en de NE-transportleemte functioneel bewezen (wp3-ne-transportcontrole.log).

## Uitvoering

Pas de goedgekeurde vijf punten uit wp3-transportbesluit-v1.md toe. Begin met tests die rood bewijzen dat publieke NE-doorgifte, schemaacceptatie, conversie en zichtbare exacte NE-tekst ontbreken. Bewaar log en exitstatus vóór productieaanpassing. Geen testgevallen verwijderen. Daarna implementeren, GREEN, lint en behoudtests.

Nieuwe paden in jouw scope:
- src/services/validation/interfaces.py — CONTRACT_VERSION 2.2.0;
- docs/architectuur/contracts/schemas/validation_result.schema.json — not_evaluated in parts.status en versieomschrijving;
- docs/architectuur/contracts/validation_result_contract.md — beperkte contractuitbreiding.

Overige twaalf paden blijven zoals eerder toegewezen. Voor NE: rule_results['INT-02'] met status not_evaluated, score null, fingerprint null, contract_version uit het actieve INT-02-record (/2), één invoeronderdeel met exacte reden en NE-status. Boek zowel de evaluatorroute als de serviceguardroute. Gebruik de bestaande UI-rendering; productie-UI verder niet wijzigen. RR blijft bestaande passagehulp. Geen score, gate, herstelroute, modelaanroep, expertreview-herlaadroute of issues-helper wijzigen.

Behoud bestaande checks in de UI-test (geen RR-vraag bij NE) en voeg daadwerkelijke zichtbaarheid via de bestaande waarschuwing-rendering toe. De melding in uitsluitend _evaluate_rule is geen transportbewijs. Test echte publieke service-uitkomsten met schema-validatie en bestaande conversiehelper. Controleer behoud van excluded_from_score en resultaatvelden voor andere regels.

Rond de bestaande nieuwe C1-replay af: lees werkelijke NE-redenen uit het publieke resultaat, bewaar verwachte exacte redenen, registreer exitstatus en geef bij mismatch/citaatfout niet-nul terug. Behoud oude en nieuwe verwachtingen, voorafgaande hashes en tijden. Include_examples true/false blijft G renderen. Neem C56 herkenbaar op als contextloze C50-variant; verzin geen extra juridische uitkomsten. Historische scripts/resultaten nooit overschrijven. De nieuwe proef-c1-uitvoering-na-o1.json bestaat nog niet; bij herhaling vrije pogingnaam kiezen.

Maak vooraf unieke herstelkopieën. Geen verwijderingen, dependencies of live toepassingsmodelcalls/productiedata. Tests via bestaande offline-bootstrap en .venv. Beveiliging/CLI-instellingen niet wijzigen. Maximaal drie pogingen per actie; diagnose en meld de concrete oorzaak bij het bereiken van de grens.

## Afronding WP3

Bewaar volledige GREEN-uitvoer en exitstatus voor O1/UI/contract/G plus gerichte behoudtests voor ESS-01/02/04. Contracttests met DEF771_SKILLS_ROOT=/Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills/skills. Ruff/Black op alle gewijzigde Pythonbestanden en make lint. De twee C24/C25-fixtures horen nog bij WP4; voer ze desgewenst ter rode nulmeting uit, wijzig ze nu niet. Bewezen basisfailure test_no_negative_commands_in_guide niet opnieuw onderzoeken.

Lever paden, diffstat (ook nieuwe bestanden), hashes, RED→GREEN, C1-uitkomst en open beperkingen. N/G/T/H behouden en beide skillcontracten bytegelijk bewijzen. Beperk de terugmelding tot nieuw bewijs en echte open punten; geen extra akkoordvraag voor al goedgekeurde scope. Alle volledige prompts en logs blijven in het dossier; Prompt Forge-fallback is al geautoriseerd. Stop na WP3 voor coördinatorcontrole.
