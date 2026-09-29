# DEF-835 WP1 — GREEN-opdracht v1

Jij bent dezelfde Claude Code CLI-uitvoerder, sessie 177f1484-4e5c-482e-b431-450befdab835. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies.

De coördinator heeft RED gecontroleerd: 162 failures, geen collectie/setupfouten; functionele stubs plus ontbrekend document. Je kunt nu binnen het expliciet geaccordeerde WP1 GREEN uitvoeren. Geen nieuwe gebruikersgoedkeuring nodig.

Leidend blijven U/plan-v1.md WP1, akkoord-wp1-v1.md en wp1-opdracht-claude-v1.md. U=docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2. Werkboom /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2, branch feature/DEF-835-int02-o2, basis84bdc8c1b. Eigenaarschap blijft exact dezelfde vijf inhoudelijke bestanden.

Implementeer het kleinste leesbare zuivere contract dat de inhoudelijke criteria bewijst. Niet uitsluitend tests groen maken: verifieer ook dat openbare constructors en replay de validatie niet omzeilen, dat een incoherent of gemanipuleerd document geen actueel oordeel wordt, en dat wijzigingen van betekenisgrond volledig binden. Geen generieke infrastructuur of andere packages toevoegen. Wijzig alleen je eigen bestanden; bestaande rootcode/tests blijven staan.

De eigen formuleringen uit RED zijn voor dit interne contract aanvaardbaar als uitvoeringstekst, mits duidelijk als zulke aanvullingen gedocumenteerd en onderscheiden van letterlijke synthesesjablonen:
- Nog niet beoordeeld volgt de T-toestand letterlijk.
- NA vraagt een reikwijdtegrond; geen claim dat het sjabloon uit synthese komt.
- Discretievariant mag bij de VN-basistekst met geldig citaat en grond getoond worden, zonder nieuwe norm.
- Precies één vraag mechanisch controleren maar geen semantische zekerheid claimen.
De 650–950 regels was een raming; noodzakelijke inhoud valt onder geautoriseerde omvangverruiming. Vermijd overbodige duplicatie. Niets verwijderen om een teller te halen.

Laat .claude/hooks/check-silent-exceptions.py als lokale symlink staan; niet committen en geen overige omgevingsaanpassingen uitvoeren. Geen productiedata, netwerk/modelcalls vanuit de app, .env, Actions of externe mutaties.

TDD: behoud de aangetoonde rode tests. Als een test aantoonbaar onjuist is, motiveer de correctie met bron; niet aanpassen om een implementatiefout te verbergen. Bewaar GREEN volledige output + exitcode in U/bewijs/wp1-groen-v1.log, en Ruff/Black checkoutput in eigen bewijsbestand. Draai:
- /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/domain/test_def835_int02_contract.py -o addopts= -q -ra
- dezelfde Python -m ruff check src/domain/int02 tests/unit/domain/test_def835_int02_contract.py
- dezelfde Python -m black --check src/domain/int02 tests/unit/domain/test_def835_int02_contract.py
Formatteer indien nodig uitsluitend eigen Pythonbestanden met bestaande formatter en verifieer opnieuw.

Schrijf docs/architectuur/contracts/int02_assessment_contract_v1.md conform gerealiseerde API met statusmapping, exacte meldingen/herkomst, veldtypen, foutbeleid, versie/replay en bewijsgrenzen (geen persistentie, geen semantische modelkwaliteit).

Maak U/wp1-claude-groen-v1.md met daadwerkelijke bestanden/regels, test- en lintresultaten, wijzigingen t.o.v. RED, interfacekeuzes, beperkingen. Geen commit/push; coördinator inspecteert en commit de concrete vijf bestanden en het dossier voor onafhankelijke review. Stop als GREEN met bewijs gereed is.
