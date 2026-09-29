# DEF-835 — oplevering WP1 v1

26 september 2026 · WP1 afgerond binnen de geaccordeerde offline scope.
Actuele takenlijst: [takenlijst-v4.md](takenlijst-v4.md).

## Resultaat

Het interne contract `def835-int02-assessment/1` is geïmplementeerd: exacte invoersnapshot, versiegebonden beoordeling, gesloten modeluitvoer, citaat- en grondcontrole, scoreloze statusmapping en historische afwijzing. Normversie blijft `def771-int02/2`.

Exact vijf inhoudelijke bestanden zijn toegevoegd:
- `src/domain/int02/__init__.py`
- `src/domain/int02/contract.py`
- `tests/unit/domain/test_def835_int02_contract.py`
- `tests/fixtures/def835_int02_ontwerpgevallen.json`
- `docs/architectuur/contracts/int02_assessment_contract_v1.md`

Daarnaast bevat de branch het coördinatiedossier met akkoord, plan, opdrachten en bewijs. Er is geen bestaande productieroute gewijzigd. O1 blijft actief.

## Commits en rollen

Branch: `feature/DEF-835-int02-o2`.
- Basis: `84bdc8c1b060ab50a1bd1428aed778bb2ed6007f`.
- Eerste implementatie: `314b817aabcaaa9f5a00d74a7633155ec74b799c`.
- Gecorrigeerde en geaccepteerde code: `d83ddbc5d7eee991ebff0aac2643983be11d8472`.

Claude Code CLI 2.1.283 (Opus 5.5) implementeerde en corrigeerde in sessie `177f1484-4e5c-482e-b431-450befdab835`.
Codex CLI 0.157.1 reviewde onafhankelijk in sessie `01a0dfa6-a610-7100-a66e-e3fefc051d4c`, aparte werkboom `/private/tmp/def835-wp1-review-20260926`. Rolloutcontext bevestigt `gpt-6-astra`, effort `high`.

De coördinator schreef geen implementatie of tests, controleerde de concrete diff, herhaalde de verificatie en beheerde commits en dossier.

## Bewijs

| Stap | Werkelijk resultaat |
| --- | --- |
| Eerste RED | 162 failures op ontbrekende logica/document; geen collectie- of setupfouten. Coördinator herhaalde dit. |
| Eerste GREEN | 162 tests geslaagd; tests en fixture bytegelijk aan RED. |
| Review | Drie P2-bevindingen; alle drie disposition “fix nu”. |
| Correctie-RED | 15 nieuwe failures naast 162 geslaagde bestaande tests, op de ongewijzigde eerste implementatie. |
| Correctie-GREEN | 177 tests geslaagd. Geen bestaande test verwijderd of afgezwakt. |
| Eindverificatie coördinator | 297 tests geslaagd op de definitieve inhoud, inclusief 120 bestaande INT-02/INT-03-/resultaatcontractcontroles. |
| Onafhankelijke herreview | 177 tests geslaagd en 26 aanvullende tegenproeven; alle drie P2’s gesloten. |
| Commitcontroles | Alle normale lokale pre-commitcontroles geslaagd, inclusief Ruff 0.16.5, Black, gitleaks en smokechecks. |

Volledige uitvoer staat lokaal onder `bewijs/`; CLIstreams zijn daar eenmaal opgeslagen. [Herreview](wp1-codex-correctiereview-v1.md), [correctierapport](wp1-claude-correcties-v1.md), [lintcorrectie](wp1-claude-commitlint-v1.md). Het compacte eindlog staat in `bewijs/wp1-coordinator-eind-v1.log`.

De eerste correctiecommit faalde op drie ISC004-lintmeldingen die de lokale Ruff 0.15.17 niet zag. De echte hook gebruikt 0.16.5. Claude voegde alleen haakjes rond drie teststrings toe; AST-controle bewees identieke waarden, 177 tests zijn daarna opnieuw geslaagd. Configuratie en versies zijn niet gewijzigd.

## Gesloten reviewpunten

1. Lege of uitsluitend uit witruimte bestaande grondtekst kan geen pass/fail dragen: `error/invalid_citation`.
2. Sjablooninvulling interpreteert ingevoegde tekst niet opnieuw: citaten en vragen met placeholdertekst blijven letterlijk.
3. Niet-decodeerbare replay-JSON geeft een technische fout; de genoemde ValueError en RecursionError lekken niet meer uit de replayroute.

## Bestandsbinding

- Domeincontract Python: SHA-256 `4791cc0692dcc12981c6529b9a7446cce5f440cec72f9fc767f972dc19c39896`.
- Finale tests: SHA-256 `368401797e216de4cbcdb8373a9815e9d3f338b4116a485fe3c61971a14d7e97`.
- Intern contractdocument: SHA-256 `6e00cdef89c9d11680d80249ef3934ac53f08b39a1bbf4e7140b2eac18c32bf4`.

## Grenzen en vervolg

Dit levert het zuivere offline WP1-contract. Het bewijst geen modelkwaliteit, onafhankelijke goldset, betaalde evaluatie, opslag/herladen, appintegratie of productieactivering. De 76 ontwerp-ID’s blijven ontwikkelmateriaal; de nieuwe fixture is geen hold-out. DEF-835 blijft In Progress; de brede issueacceptatiecriteria worden niet als volledig afgedekt afgevinkt.

Volgende werkpakket is WP2: de begrensde AI-service en T-prompt, eerst offline. Het publieke schema/resultaatcontract (WP3), goldset/modelbudget, gedeelde opslagroute (DEF-626) en activering vragen de in het plan afgebakende vervolgbesluiten.

Geen appmodelcalls, productiedata, nieuwe dependencies, publieke schemawijziging, push, PR, merge of wijziging aan Actions in deze WP1-uitvoering. Actions blijven uit.

## Procesdetails

Alle CLI-opdrachten staan volledig in dit dossier. Prompt Forge gebruikt de eerder toegestane lokale fallback na de geblokkeerde bereikbaarheidscheck.

Claude GREEN/correcties had uitsluitend Bash/Edit/Glob/Grep/Read/Write en geen MCP-koppelingen. Codex meldde geen delegatietools, maar overige MCP-tools bleven zichtbaar ondanks de sessieconfig; die zijn niet gebruikt. Volledige MCP-uitschakeling wordt daarom niet geclaimd.

De lokale hooksymlink `.claude/hooks/check-silent-exceptions.py` verwijst naar de bestaande hook in de hoofdcheckout, zodat die ook in de werkboom kon werken. Deze symlink is niet gecommit. Niets verwijderd. Ruwe logs en tijdelijke reviewwerkboom blijven behouden.
