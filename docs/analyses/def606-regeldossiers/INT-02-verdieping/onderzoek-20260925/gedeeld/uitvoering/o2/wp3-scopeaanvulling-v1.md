# DEF-835 WP3 — scopeaanvulling v1

27 september 2026. Voorstel voor twee noodzakelijke aanvullingen op de zeven bestanden uit plan-v1.md. Nog geen WP3-code gewijzigd.

## Ontvangen akkoord

Chris antwoordde “Akkoord” op de WP2-oplevering die WP3 (evaluator en resultaatcontract) als volgend, apart te accorderen bouwpakket noemde. Dit autoriseert het beschreven WP3-contract en de zeven geplande bestanden. De verruiming boven 100 regels blijft gelden. Echte modelaanroepen zijn al toegestaan; het concrete kostenplafond van de afzonderlijke technische proef staat nog open.

## Aangetroffen planomissie

Het betreft een onvolledige bestandslijst in het plan, geen gewijzigd inhoudelijk INT-02-besluit.

1. **Root-SSOT moet dezelfde evaluatorwaarden kennen.**
   - src/toetsregels/runtime_contract.py:260: “Faalt zichtbaar wanneer de YAML-waardesets afwijken van de Python-enums.”
   - :290–305 vergelijkt de YAML-lijst met EvaluatorType en meldt bij een nieuw enumlid: “mist waarden die de runtime wel kent”.
   - config/toetsregels/toetsregels_config.yaml:105 bevat als laatste bestaande evaluator “pronoun_reference_assessment”.
   - Alleen het Python-enum uitbreiden met decision_rule_assessment zou daardoor het laden van de gehele regelsuite laten falen.
   - Noodzakelijke aanvulling: dezelfde evaluatorwaarde in runtime_contract.evaluators in deze YAML opnemen. Geen actieve INT-02-recordselectie wijzigen.

2. **De producent gebruikt een centrale Python-contractversie.**
   - src/services/validation/interfaces.py:77: CONTRACT_VERSION = "2.2.0".
   - :276–279 documenteert assessment/signals alleen voor INT-03.
   - tests/integration/contracts/test_validation_result_schema.py:136–139 vergelijkt de geproduceerde version met deze constante.
   - Alleen document/schema op 2.3.0 zetten zou de geproduceerde versie op2.2.0 laten staan.
   - Noodzakelijke aanvulling: centrale constante naar2.3.0 en gerichte TypedDict-documentatie voor INT-02. De reeds aanwezige assessment/signals-velden blijven optioneel; geen extra publieke velden boven het goedgekeurde voorstel.

## Concrete wijzigingsscope (negen bestanden)

Oorspronkelijk geaccordeerd:
1. nieuw src/services/validation/evaluators/decision_rule_assessment.py
2. src/toetsregels/runtime_contract.py
3. src/services/validation/evaluators/__init__.py
4. docs/architectuur/contracts/validation_result_contract.md
5. docs/architectuur/contracts/schemas/validation_result.schema.json
6. nieuw tests/unit/validation/test_def835_int02_evaluator.py
7. tests/integration/contracts/test_validation_result_schema.py

Aanvullend te accorderen:
8. config/toetsregels/toetsregels_config.yaml — alleen nieuwe bekende evaluatorwaarde/toelichting.
9. src/services/validation/interfaces.py — contractversie2.3.0 en gerichte documentatie van INT-02 assessment/signals.

Raming aanvullingen: circa10–25 regels, geen dependencies. O1 blijft actief; geen modelcalls, containerintegratie, UI, database, poort of herstel. Actions blijven uit.

## Tests en acceptatie

Eerst rood: evaluatorregistratie met geldige rootpolicy, canonieke uitvoerversie2.3.0, INT-02 assessment/signals alleen voor deze regel en bestaande INT-03, gesloten onbekende velden, alle zes statuspaden inclusief ontbrekend/historisch/ongeldig oordeel, scoreloos en advisory fail. Daarna implementatie door Claude Code CLI en onafhankelijke Codex CLI-review op concrete diff.

Bestaande norm, WP1/WP2 en O1-gedrag blijven leidend. Geen verse herinventarisatie of volledige review van andere werkpakketten. Akkoord nodig volgens de oorspronkelijke expliciete bestands-/contractgrenzen; dit wordt niet verondersteld uit de100-regelsverruiming.

Werkboom /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2; branch feature/DEF-835-int02-o2; basis2be81c577653f8efbab6fa2c3794598556d32d13.

