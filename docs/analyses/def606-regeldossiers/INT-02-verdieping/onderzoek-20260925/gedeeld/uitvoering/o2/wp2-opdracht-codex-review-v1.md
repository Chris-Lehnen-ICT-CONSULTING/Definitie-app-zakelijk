# DEF-835 WP2 — onafhankelijke Codex CLI-review v1

Jij bent de Codex CLI-reviewer. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Review alleen; wijzig geen bronbestanden of tests. Alles Nederlands. Maximaal drie pogingen per actie.

Werkroot: /private/tmp/def835-wp2-review-20260927, detached HEAD 0e336c6c4b40fd53d4a1ef3c2283f6a99691510f.
Base: b56e0e225e65eac00ad73239900d2e6c1bfc2422
Head: 0e336c6c4b40fd53d4a1ef3c2283f6a99691510f
Review de concrete diff base..head: exact drie nieuwe bestanden (service, servicetest, prompttest), 2278 regels.
Je bent niet alleen in de codebase: implementatiewerkboom /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2 is read-only voor jou.
Dossier U=/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2. De WP2-dossierbestanden zijn nog niet gecommit en lees je daar; bron/testcode review je in je eigen root.

Chris autoriseerde WP2 op 27-09 ("Echte modelaanroepen zijn toegestaan go for wp2"), >100regels voor INT-02 eerder toegestaan. Geen nieuw dependency/schema/UI/evaluator/storage/activering. Actions uit. Offline tests, geen livecalls in review.

Lees opdracht U/wp2-opdracht-claude-rood-v1.md, groen-v1.md, U/plan-v1.md WP2, U/wp2-claude-rood-v1.md en groen-v1.md. Norm: besluiten-chris-v1.md, gezamenlijke-synthese-v5.md §2/§4, WP1 domain/int02/contract.py. Lees relevante projectregels/skill requesting-code-review, maar jij bent toegewezen reviewer en delegeert niet.

Acceptatie: exacte T, veilige scheiding data/instructie, WP1-citaat/statusvalidatie, scoreloos, immutable input/binding, expliciet profiel/route/budget, één poging zonder SDK-retry/rawcache/herstelcall, deadline/input/antwoordgrenzen, strikte JSON incl dubbele keys, cache alleen valide/full binding, eerlijke metadata/logging, geen wijziging bestaande O1-route. Vang inhoudelijke fouten die tests missen. Geen vrijblijvende refactors, arbitraire LOC-eisen of extra reviewrondes zonder concrete risico's.

Bewijs:
- RED158failed/3passed;7 aanvullende tests eerst rood; definitief169WP2tests groen.
- Coördinator603passed in3.95s op definitieve hashes: U/bewijs/wp2-coordinator-groen-v1.log.
- 434gerelateerde regressies, Ruff0.16.5/Black en lokale normale commitgates groen.
- Behoud RED-tests bytegelijk aangetoond.
- Procesafwijking: één extra functiebetekenis-test is na correctie geschreven, mutatiebewijs toont foutdetectie. Dit maakt oorspronkelijke volgorde niet alsnog TDD; beoordeel de feitelijke code/bewijsgrens.
- De uitvoerder deed mutatiecontroles en herstelde de bron bytegelijk; review alleen definitieve commit.

Bekende concrete beperkingen — niet wegredeneren:
1. AIServiceV2 geeft aangevraagde modelnaam terug, geen echte provider-ID/usage. Modelversie/in-outtokens/kosten blijvenunknown. Modelmismatchcheck vergelijkt uitsluitend AIService-response ID. Providercheck is route==profiel vóór call. Geen claim van providerattestatie.
2. Budget begrenst tekens/tokens/duur, geen monetair budget. Liveproef is toegestaan maar kostenplafond nog niet beantwoord; geen appcalls gedaan.
3. Dienstlogger geen ruwe inhoud; bestaande AsyncGPTClient logt exceptiontekst. Backend read-only binnen huidige drie bestanden. Beoordeel expliciet of dit WP2 blokkeert of integratievervolg is; geef bewijs en exacte impact.
4. Norm immutable snapshot per dienstinstantie. Wijzigingen op schijf vereisen nieuwe instantie. Geen claim automatischreload.
5. Niet-uitgevoerde configuratieblokkade is WP1not_executed/RR, met eigen servicereden; transport/outputfout error. WP1 niet verbreed.

Technische toolgrens:
- agents.enabled=false en multi_agent uit; alle geconfigureerde MCPservers voor deze sessie disabled.
- Controleer eerst daadwerkelijk zichtbare delegatietools. Als native of MCPdelegatietools zichtbaar zijn: niet gebruiken; meld concrete inventory. Gebruik alleen shell/readtools, geen externe mutaties.
- Worktree heeft géén opdracht om handovers te archiveren of te verwijderen.
- Probes mogen in /private/tmp met unieke namen; laat ze staan. Geen wijzigingen aan getrackte bron/tests, ook geen mutaties in de reviewroot.

Gerichte verificatie (geen volledige suite nodig):
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/validation/test_def835_int02_assessment_service.py tests/unit/services/prompts/test_def835_int02_prompt.py -o addopts= -q -ra
Extra tegenproef alleen bij concrete open vraag. Geef bij bevestigde bevinding bestandsregel, reproductie, impact, ernst. Geen codefixes zelf. Eindantwoord met base/head, eigen testresultaat, bevestigde punten en oordeel; noteer geen resterende bevindingen als dat werkelijk zo is. Coördinator bewaart volledig antwoord via output-last-message.

