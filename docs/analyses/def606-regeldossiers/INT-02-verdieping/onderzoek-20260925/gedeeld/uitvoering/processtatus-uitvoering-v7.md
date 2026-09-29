# DEF-771 — processtatus v7: mergevoorbereiding, contractblokkade

26 september 2026. Dezelfde Claude Code CLI-sessie heeft de integratieopdracht afgerond (procesexit 0). Beide featurebranches hebben een voorbereide gewone merge, zonder commit of PR-merge. Bewijscommit b56e28782 is vooraf gepusht.

## Voortgang sinds takenlijst-v9

- [x] Eén appconflict en zes skillconflicten opgelost; INT-02 en INT-03 behouden.
- [x] Beide canonieke contractkopieën en beide opgedragen ZIP-bundels bytegelijk aan de bron gecontroleerd.
- [x] Gerichte tests: 1166 passed, 5 failed, 5 skipped, exit 1.
- [x] Ongewijzigde ketenproef v3: drie casussen/twee routes groen, exit 0; resultaat bytegelijk aan v3.
- [x] Ruff, Black en make lint groen.
- [ ] Contractblokkade B2 oplossen na afzonderlijk akkoord.
- [ ] Verouderde INT-03-versieassertie B1 aanpassen in de aansluitende correctie.
- [ ] Daarna integratiecommits, volledige offline suite, onafhankelijke integratiereview en PR-oplevering.
- [ ] PR-merges en actieve skillpublicatie uitsluitend na expliciet akkoord.

## Concrete blokkade en voorstel

B1: tests/unit/services/orchestrators/test_def772_int03_wrappers.py:102 verwacht 2.1.0, terwijl het goedgekeurde INT-02-contract 2.2.0 is. De assertie moet aansluiten bij de definitieve contractversie.

B2: docs/architectuur/contracts/schemas/validation_result.schema.json:344 verbiedt onbekende velden in een regeluitkomst. De reeds op main aanwezige INT-03-evaluator levert assessment en signals. Drie bestaande INT-02-tests valideren alle rule_results en vinden daardoor dit schema-/runtimeverschil. Exacte fout: Additional properties are not allowed ('assessment', 'signals' were unexpected). Coördinator heeft foutuitvoer en actuele locaties gecontroleerd.

Voorstel: laat hetzelfde uitvoerder/reviewer-paar het gedeelde schema in overeenstemming brengen met de bestaande INT-03-velden, met expliciete typen, contractversiebehandeling en regressietests voor zowel INT-02 als INT-03. Behoud de strenge controle van alle regeluitkomsten. Daarna volledige offline suite en integratiereview. Dit vraagt akkoord volgens de oorspronkelijke harde regel voor schema-/resultaatcontractwijzigingen en de stopregel voor verschillen tussen code en contract. De verruiming van 100 regels dekt dat aparte besluit niet.

De vijfde failure is de eerder vastgelegde negatieve-promptformuleringstest; geen algemene promptreparatie gestart. De korte aliasbundels van main bevatten nog geen INT-02-contract, ook vóór deze integratie niet; meenemen in het concrete publicatievoorstel.

## Bewaarstatus

App HEAD b56e2878268f744f224e8d1326c9198378b025bc, MERGE_HEAD 076c916671e4e7e9f2843d22669df38eeb79e170. Skills HEAD 750068253a7389e201daedc5b9aa0afd5c0be032, MERGE_HEAD 770de55ece429fec826c9d53fd873a109ed8e670. Opgeloste merges niet teruggedraaid of gecommit. Uitvoerdersrapport: vervolg-integratie-rapport-v1.md. Alle integratieopdrachten en logs staan in deze dossiermap. Geen actieve skills gewijzigd, geen applicatie-modelaanroepen, geen verwijderingen.
