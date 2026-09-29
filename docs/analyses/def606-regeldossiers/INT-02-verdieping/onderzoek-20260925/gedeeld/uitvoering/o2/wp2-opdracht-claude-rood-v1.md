# DEF-835 WP2 — Claude Code CLI-uitvoerder, RED-opdracht v1

Jij bent de Claude Code CLI-uitvoerder. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Je bent niet de coördinator. Alles Nederlands. Maximaal drie pogingen per actie.

## Opdracht en autorisatie
Chris heeft op 27 september 2026 gezegd: "Echte modelaanroepen zijn toegestaan go for wp2". Bouw WP2 uit U/plan-v1.md, met de bestaande geaccepteerde WP1-code. Omvang boven 100 regels voor INT-02 is toegestaan. Geen dependencies, publieke schemawijzigingen, nieuwe app-route, Actions, push of merge. WP2 betekent drie nieuwe inhoudelijke bestanden:
1. src/services/validation/int02_assessment_service.py
2. tests/unit/validation/test_def835_int02_assessment_service.py
3. tests/unit/services/prompts/test_def835_int02_prompt.py

Werkboom: /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2
Branch: feature/DEF-835-int02-o2
Basis: b56e0e225e65eac00ad73239900d2e6c1bfc2422
U = docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2

Je bent niet alleen in de codebase. Respecteer bestaande wijzigingen; wijzig alleen jouw drie inhoudelijke bestanden en de hieronder genoemde nieuwe bewijs/rapportbestanden. WP1-contract, bestaande INT-03-service, providerlagen, configuratie, tests en skills zijn read-only. Als dit wezenlijk onmogelijk blijkt, rapporteer concrete interfacebeperking, geen verbreding.

## Bronnen
Lees U/plan-v1.md WP2 + ontwerpcontract, U/wp1-oplevering-v1.md, docs/architectuur/contracts/int02_assessment_contract_v1.md, src/domain/int02/contract.py.
Lees volledig relevante normpassages in ../gezamenlijke-synthese-v5.md §2–4 (U ligt één map onder uitvoering: zoek correcte dossierpad), besluiten-chris-v1.md. Exacte T letterlijk renderen; geen eigen inkorting. Record src/toetsregels/regels/INT-02.json is de runtime normbron; neem normversie/hash op in binding, behoud koppeling met contract def771-int02/2.
Lees CLAUDE.md, .claude/rules/patterns.md, project-rules.md en relevante AIServiceInterface/AIServiceV2/ModelRouter-interfaces. INT-03-service toont bestaande opt-ins voor één transportpoging, geen retries, geen ruwe cache, deadline, stop-reason en attributie. Controleer daadwerkelijke werking i.p.v. aannemen. Hergebruik bestaande helpers zonder bestaande code te wijzigen.
Gebruik test-driven-development; tests/conftest.py blokkeert netwerk voor de offline suite.

## Inhoudelijke acceptatie
- Async service met expliciet geïnjecteerde AIServiceInterface en ModelRouter; task_type validation, geen hardcoded provider/model of nieuwe routertaak. Geen containeractivering.
- Gescheiden system-/dataprompt: letterlijke T uit synthese §4 + norm + gesloten WP1 JSON-contract. Alle invoer uitsluitend gegevens, JSON veilig geserialiseerd; geen impliciete bronophaling, herstel of score. Offsets Python Unicode-codepoints, start0/einde exclusief.
- WP1 bepaalt mechanische beoordeling/gesloten structuur/citaatcontrole/statusmapping; niet dupliceren of wijzigen.
- Modelprofiel vooraf expliciet gekwalificeerd/gebonden; geen kwalificatieclaim uit enkel routerdefault. Gevraagde provider/model en daadwerkelijke respons mismatch -> technische fout. Onbekende gerapporteerde versie eerlijk unknown; geen verzonnen metingen. Router-/norm-/promptconfigwijzigingen invalideren cache.
- Kern/context ontbreekt -> not_evaluated zonder servicecall.
- Eén transportpoging, geen SDK-retries of herstelcall, geen ruwe providercache, bounded deadline, bounded invoer en uitvoer/budget. Een bestaande opt-in moet daadwerkelijk aan providerinterface doorgegeven worden.
- Exceptiontekst en ruwe prompt/response nooit loggen; technische fouten en inhoudelijke onzekerheid onderscheiden. Timeout, afgekapt antwoord, malformed JSON, duplicate keys, fictief citaat, router mismatch, ongekwalificeerd profiel, budgetoverschrijding -> geen stille pass/fail.
- Cache alleen na volledig geldig WP1-resultaat en complete binding; immutable resultaat, geen gewijzigde invoer/norm/prompt/router/model/budget langs cache laten glippen. Cache geen errors, geen eeuwig onbeperkte geheugengroei.
- Bestaande WP1 uitvoeringsmetadata heeft slechts timeout/transport/provider als transportfoutcategorie. Breid domeincontract niet stil uit: detailreden mag service-resultaatmetadata zijn; contract behoudt coherent technische error en juiste melding. Ontbrekend profiel/budget blijft expliciet niet uitgevoerd/technisch geblokkeerd, geen modelverdict.
- Geen nieuwe generieke infrastructuur. Publieke evaluator/resultaatschema/storage/UI/record blijven voor WP3+.

## Alleen RED nu
Schrijf beide betekenisvolle testbestanden en minimale importeerbare servicestubs (NotImplementedError is aanvaardbaar); geen GREEN-implementatie vóór coördinator RED heeft gecontroleerd.
Test o.a. T letterlijk, datainjectie, alle bovenstaande foutpaden, cache/rebinding en metadata, plus echte bestaande AI-interfacecompatibiliteit waar offline mogelijk. Fixtures uitsluitend fake/modelmock; geen live calls in tests.
Doe de nodige concrete API-keuzes binnen WP2 en documenteer ze compact. Geen kwaliteitslabel voor een echt model in deze fase. Echte technische smoke volgt apart na besluit budget/profiel; coördinator regelt dit. Geen .env/credentials lezen of weergeven.

Bewaar complete RED-uitvoer en exitcode in U/bewijs/wp2-rood-v1.log.
Draai: /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/validation/test_def835_int02_assessment_service.py tests/unit/services/prompts/test_def835_int02_prompt.py -o addopts= -q -ra
Schrijf U/wp2-claude-rood-v1.md met aantallen echte failures/setup-errors, testreden, gekozen service-API, onderzochte providerinterface, concrete beperkingen en lijst gewijzigde bestanden.
Geen commit/push. Stop na RED zodat de coördinator het bewijs kan controleren.

