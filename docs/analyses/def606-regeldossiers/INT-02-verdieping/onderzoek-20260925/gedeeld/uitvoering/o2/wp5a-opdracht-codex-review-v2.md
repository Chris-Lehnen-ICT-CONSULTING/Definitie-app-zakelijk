# DEF-835 WP5a — onafhankelijke reviewopdracht

Jij bent de Codex CLI-reviewer. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Review de concrete WP5a-diff, wijzig geen bronbestanden of tests. Nederlands verslag, concrete onderbouwde bevindingen met ernst én dispositievoorstel. Geen algemene herreview van ongewijzigde WP1–WP3. Geen live modelcalls, productiedata, nieuwe dependencies, stage/commit/push/merge of Actions.

Reviewroot /private/tmp/def835-wp2-review-20260927. Basis 979ca0585100d94b613829d924c6d8bba4f24f1b. De zeven WP5a-bestanden zijn als bytegelijke kopie van de stilgezette uitvoerderswerkboom op deze basis gezet. De concrete uiteindelijke identiteit staat in bewijs/wp5a-reviewmanifest-v1.json; controleer de zeven SHA256-hashes en de patchhash vóór review. Bronwijzigingen staan bewust nog niet in een commit: een afzonderlijke expliciet geaccordeerde metadata-uitzondering moet eerst een bestaande dossiercommitblokkade oplossen. Daarover geen beoordeling of bypass in deze review.

Dossier met opdracht, besluit, voorstel en testbewijs:
/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2

Lees gericht wp5a-integratievoorstel-v1.md, besluit-proef-en-wp5a-v1.md, wp5a-opdracht-claude-v1.md en wp5a-claude-verslag-v1.md met de genoemde RED/GREEN-bewijzen. Leidende brede INT-02-norm en bestaande WP1-contract blijven ongewijzigd. Lees toepasselijke projectregels/CLAUDE en requesting-code-review; je bent al de toegewezen reviewer, geen herdelegatie.

Scope: src/services/container.py, src/services/orchestrators/definition_orchestrator_v2.py, src/services/orchestrators/validation_orchestrator_v2.py, src/services/validation/modular_validation_service.py en de drie nieuwe testbestanden uit het manifest.

Acceptatie:
1. Gewone O1-route en normale container maken nul INT-02-modelcalls, ook als caller metadata of beoordeling meegeeft. Alleen expliciete O2-config met evaluator decision_rule_assessment en bewuste dienstinjectie maakt het pad bereikbaar. Geen globale vlag, impliciet profiel/modelbudget of defaultinstantiatie.
2. Kern bytegelijk, recordkern gezaghebbend; aanwezige ongeldige recordkern error, geen fallback. Caller assessment nooit vertrouwen; eigen verse invoer/binding controleren. Geen cleaning die de beoordeelde kern wijzigt.
3. Lege kern/ontbrekende context NE zonder call. Ontbrekende dienst/profiel expliciet open. Binding-, dienst- en vormfout error, geen inhoudelijk oordeel. Geen raw exceptiontekst, prompts of sleutelwaarden in nieuwe logs.
4. Alle zes statussen via echte ModularValidationService in rule_results INT-02; publieke 2.3.0 en WP1-doc intact, excluded_from_score. Geen fail als poort. C117-invalid-citation blijft error; C105/C107/C112-fakes bewijzen alleen mapping.
5. Bestaande INT-03/ESS-03/bronroutes hebben relevant regressiebewijs. TDD daadwerkelijk gedrag rood vóór productie en daarna groen, lint. Geen testgevallen/bestanden verwijderd. Geen opslag/UI/DEF-626/activering of andere scopewijziging.

De echte liveproef van eerder deze beurt kwalificeert het model NIET: C107 inhoudelijk afwijkend, C112 ongeldige citaatposities. Vraag geen promptcorrectie of extra modelcalls binnen dit WP5a-pakket. De gekozen technische route moet de beperkingen zichtbaar houden.

Verifieer met passende offline tests via /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python, PYTHONPATH=src. Je mag bestaande tests draaien en uitsluitend tijdelijke zelfstandige repros in /private/tmp aanmaken, geen productietests aanpassen. Rapporteer commandos, exit/resultaat en reikwijdte; herhaal geen volledige matrix zonder concrete open vraag. Lever inhoudelijke bevindingen, niet stijlvoorkeuren. Onbewezen vermoedens niet als bevestigde blocker opvoeren. Iedere bevinding krijgt concrete locatie, pad naar fout/trace of repro en minimale correctierichting. Als geen bevindingen, zeg dat met bewijslimieten. Maximaal drie pogingen per actie.

Eindrapport wordt door --output-last-message opgeslagen als wp5a-codex-review-v1.md. Alle overige uitvoer staat eenmaal in bewijs/wp5a-codex-stream-v1.jsonl. Meld beoordeelde manifest/diff-identiteit expliciet. Geen claim dat heel O2 af of modelgekwalificeerd is.

## Concrete open punten uit de uitvoering

Classificeer de acht open punten in het uitvoerdersverslag tegen de geaccordeerde scope en contracten, met bewijs; neem voorstellen niet automatisch over. Vooral het bestaande NE-pad vóór de evaluator (exacte invoer/melding en documentvorm) en de configuratiehelft van de binding verdienen toetsing aan actuele verplichtingen. De oude WP2-tekstguard is al aan Chris voorgelegd als achtste testbestand; wijzig die zelf niet. De twee performance_tracker-fouten en dertien mypy-fouten zijn ook op HEAD gereproduceerd: benut het behouden bewijs en herhaal geen volledige unit-suite zonder concrete nieuwe vraag. De coördinator draaide de 49 nieuwe tests, Ruff en Black met exit 0; hashes en log staan in bewijs/wp5a-coordinator-v1.json en .log. Controleer of die hashes bij deze finale snapshot passen.
