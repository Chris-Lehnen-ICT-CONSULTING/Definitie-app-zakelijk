# DEF-835 — WP5a implementatieopdracht

Jij bent de Claude Code CLI-uitvoerder. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Coördinator implementeert niet; verse onafhankelijke Codex CLI-review volgt. Nederlands verslag. Lees project-CLAUDE.md/.claude/rules, de globale programmeerregels en de onderstaande bronnen gericht, geen volledige herinventarisatie.

Werkboom: /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2. Branch feature/DEF-835-int02-o2, basis 979ca0585100d94b613829d924c6d8bba4f24f1b. Chris accordeerde wp5a-integratievoorstel-v1.md en de optionele API-uitbreiding/zeven bestanden met “akkoord”; vastgelegd in besluit-proef-en-wp5a-v1.md. >100 regels INT-02 toegestaan, maar houd dit pakket klein. Geen nieuwe dependencies, schema of resultaatcontractversie. Actief INT-02 blijft O1.

Leidend: wp5a-integratievoorstel-v1.md volledig lezen, WP1-contract domain/int02/contract.py, WP2 Int02AssessmentService, WP3 decision_rule_assessment-evaluator en resultaatcontract2.3.0. Norm en B1–B6 blijven gelden. De actuele echte modelproef staat in modelproef-live-verslag-v1.md: C107 inhoudelijk afwijkend, C112 ongeldig citaat. Geen modelkwalificatie bewezen. Wijzig geen prompts/norm/fixturelabels om die uitkomsten passend te maken.

Eigenaarschap UITSLUITEND:
1. src/services/container.py
2. src/services/orchestrators/definition_orchestrator_v2.py
3. src/services/orchestrators/validation_orchestrator_v2.py
4. src/services/validation/modular_validation_service.py
5. nieuw tests/unit/services/orchestrators/test_def835_int02_wrappers.py
6. nieuw tests/unit/validation/test_def835_int02_modular.py
7. nieuw tests/unit/services/test_def835_int02_container.py

Nieuwe opdrachten/verslagen/bewijs onder deze dossiermap toegestaan: wp5a-claude-verslag-v1.md en bewijs/wp5a-*. Andere bestanden/werk laten staan; je bent niet alleen in de repository. Geen bestanden of testgevallen verwijderen. Geen echte model/providercalls, productiedata, database, opslagroute, UI-wijziging, issueshelpers, DEF-626-implementatie, Actions, push/merge/activering. Als concrete API/schema/bestandsuitbreiding nodig is buiten dit mandaat, meld de vindplaats en het minimale voorstel vóór wijziging.

Doel: expliciet geïnjecteerde O2-dienst kan via generatie- en recordvalidatie het WP1-document onveranderd in rule_results['INT-02'] krijgen. Normale O1-route doet NUL INT-02-modelcalls, ook als los assessment/dienst in metadata wordt aangeboden. Alleen expliciete O2-test/proefconfig met decision_rule_assessment maakt de route bereikbaar. Geen nieuwe globale vlag of automatische defaultinstantiatie; profiel en budget expliciet verplicht. Containerfactory mag alleen op expliciet verzoek construeren, geen nieuwe impliciete modelkeuze. Lees daadwerkelijke SSOT/evaluatorconfig; geen ongecontroleerde shortcut via losse callersleutel die O1 toch een call laat doen.

Verplichte cases:
- Kern bytegelijk zonder cleaning; recordkern gezaghebbend, aanwezige ongeldige recordkern fout in plaats van fallback.
- Onbetrouwbare meegegeven int02_assessment verwijderen/negeren vóór eigen beoordeling. Verse invoer en binding bepalen actualiteit; geen caller-pass.
- Lege kern/ontbrekende context NE zonder call. Ontbrekend profiel/dienst expliciet open. Binding-/dienst-/vormfout error, nooit inhoudelijk pass/fail.
- Pass, adviserend fail, review_required, not_evaluated, not_applicable, error komen via echte ModularValidationService in rule_results. DECISION_RULE_ASSESSMENT hoort in _EVALUATORS_MET_DEELUITKOMST. Geen cijfer of poort; excluded_from_score.
- Geen raw exception/payload/secret in nieuwe logs. Geen herstelcall of modelcall bij herladen.
- Synthetische C105/C107/C112 met handmatige fake-respons bewijzen mapping, geen modelkwaliteit. C117-ongeldig citaat blijft error; C118-opslag valt buitenpakket.
- Bestaande INT-03, ESS-03 en bronbeoordelingswrappers behouden gedrag. Geen profielbudget voor andere regels overnemen als O2-kwalificatie.

TDD: gedragstest eerst, RED vastleggen tegen de ongewijzigde productiecode, dan minimale implementatie en GREEN. Laat imports van nieuwe testhelpers niet het enige RED zijn. Bewaar commando/exits en hashes. Gebruik /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python, pytest, black, ruff. Draai de drie nieuwe testbestanden en relevante bestaande wrapper/container/modular-regressie; breid alleen bij concrete doorwerking. Geen nieuwe mutatiematrix of algemene refactor.

BELANGRIJKE GIT-STAAT: er staan 38 dossierbestanden staged van een eerdere commit die de secretcontrole blokkeert op twee bewezen bronhash-false-positives (zie modelproef-dossiercommit-blokkade-v1.md). Laat die index EXACT intact. Geen unstage, geen scopeverkleining, geen allowlistwijziging, geen bypass. **Commit/stage WP5a nu niet.** Lever stabiele werkboomdiff van jouw vier bestaande en drie nieuwe bestanden, plus SHA256 per bestand en volledig testbewijs. De coördinator organiseert review van die concrete diff; de afzonderlijke securitybeslissing voor de dossiercommit loopt apart. Dit is geen toestemming de geblokkeerde commit langs andere weg te maken.

Eindverslag: per acceptatiepunt wat bewezen is, RED/GREEN met eerlijke beperkingen, totale regels/bestanden, benodigde reviewdiff-identiteit en open punten. Geen eigenreview laten starten. Max drie pogingen per actie; bij een echte blokkade concreet melden en onafhankelijk werk afronden.
