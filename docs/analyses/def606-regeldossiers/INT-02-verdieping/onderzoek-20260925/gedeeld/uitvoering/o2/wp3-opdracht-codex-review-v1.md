# DEF-835 WP3 — onafhankelijke Codex CLI-review

Jij bent de Codex CLI-reviewer. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Je schrijft of corrigeert geen bronbestanden/tests. De coördinator geeft bevestigde bevindingen terug aan dezelfde Claude-uitvoerder. Geen push, merge, Actions, live appmodelcalls, productiedata of verwijderingen. Maximaal drie pogingen per actie.

## Scope en identiteit

Reviewwerkroot /private/tmp/def835-wp2-review-20260927 wordt hergebruikt, maar jouw sessie is vers voor WP3. Werk detached op d3fc53eaed14e6a303605146b7e5f8b9ea3cef5e.
Base 2be81c577653f8efbab6fa2c3794598556d32d13.
Review exact deze negen-bestandendiff. Lees relevante projectregels en requesting-code-review-skill. WP1/WP2 zijn al onafhankelijk gereviewd; herhaal geen volledige analyse daarvan.

Leidende bronnen in de repo: docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/besluiten-chris-v1.md; gezamenlijk dossier gezamenlijke-synthese-v5.md §2/§4; gedeeld/uitvoering/o2/plan-v1.md WP3.

Alle recente prompts/logs/verslagen staan als lokale documenten onder:
/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2
Lees wp3-scopeaanvulling-v1.md (negen bestanden expliciet geaccordeerd), wp3-opdracht-claude-rood-v1.md, wp3-claude-rood-verslag-v1.md, wp3-claude-groen-verslag-v1.md, wp3-scopeaanvulling-tests-v1.md. De laatste is alleen een VOORSTEL; Chris heeft de vijf extra bestaande testbestanden nog niet geaccordeerd.

## Functionele acceptatie

- Nieuw puur/synchroon decision_rule_assessment-evaluatortype, root-SSOT en registry consistent; actief INT-02-record blijft O1.
- Huidige input/configuratie bepaalt actualiteit via WP1. Geen inhoudelijke pass/fail zonder geldig, actueel en herleidbaar oordeel. Gegevens uit historisch document niet als huidige input gebruiken. Alle zes statuspaden met de exacte WP1-meldingen; geen signaalwoord als normbewijs; fail adviserend en scoreloos, geen poort/herstel.
- Goed gedefinieerde kleine metadata-interface; ongeldige waarden worden geen onterechte inhoudelijke oordelen. Bron/citaat/binding/grenzen logisch consistent. Geen ongecontroleerde documentmutatie.
- Publiek contract 2.3.0: alleen INT-02 mag optionele assessment/signals naast reeds bestaande INT-03; onbekende velden blijven gesloten. De echte evaluatoruitkomst schema-geldig.
- TDD-bewijs: RED 92 failed/19 passed → GREEN 111 passed met **bytegelijke testbestanden**. Testsha's staan in logs; geen bestaande testgevallen verwijderd.
- Buiten scope: ModularValidationService-boekhouding/container/orchestrator/UI/opslag/activering (WP5). Bekende set _EVALUATORS_MET_DEELUITKOMST moet daar nog aangesloten worden. Niet als nieuwe WP3-bevinding herhalen, wel bewijsgrens expliciet houden.

## Geldig bewijs en open punten

Coördinator heeft 547 tests uitgevoerd met importlib: 539 passed, 8 failed, alleen bekende verouderde assertions in vijf bestaande testbestanden. Log bewijs/wp3-coordinator-verificatie-v1.log.
Daarvoor 111 WP3-tests groen; gerichte regressies 354 passed/4 failed en vier versiepinfiles 74 passed/4 failed.
Oude assertions pinnen 2.2.0; één verbiedt juist de nu geaccordeerde INT-02-velden. Herijking wacht op expliciet bestandsakkoord; niet stil wijzigen. Dit blijft een open opleverpunt, geen volledige regressiegroenclaim.
Brede unitrun door uitvoerder: 8395 passed, 10 failed, 1 error, 86 skipped, 1 xfailed. Twee andere failures zijn volgens uitvoerder voorbestaande OfflineGateErrors in performance_tracker; één collectionerror door importmodus. Controleer bronbewijs indien je deze claims overneemt, anders als onbevestigde verklaring markeren. Geen nieuwe volledige suite nodig voor deze review.
Normale lokale commitgates geslaagd, Ruff/Black groen. Geen appcalls, geen activering.

## Uitvoering en resultaat

Controleer branch/head en effectieve toolinventaris: native/MCP-delegatietools moeten afwezig zijn; meld wat je daadwerkelijk ziet. Geen extra CLI via shell.
Gebruik bestaande Python /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python. Gerichte onafhankelijke tests/proeven om concrete risico's te controleren zijn toegestaan, uitsluitend offline, buiten bron/testbestanden. Vermijd pytest in de hele tempwerkroot als daarin historische proefbestanden liggen: selecteer expliciete testpaden. Geen onderhoud aan globale regels, handovers, skills of andere werkbomen.

Rapporteer in het Nederlands: beoordeelde base/head, uitgevoerde verificatie met exitcodes, bevindingen met ernst/bestand/regel en concreet reproduceerbaar bewijs, per relevant criterium conclusie en grenzen. Geen theoretische checklist of stijlbevindingen. Geef bij geen nieuwe bevindingen dat expliciet aan, maar houd het bestaande acht-failures-opleverpunt zichtbaar. Geen codecorrecties.

Je finale antwoord wordt door --output-last-message bewaard als wp3-codex-review-v1.md in het dossier; stream afzonderlijk. Stop na review.
