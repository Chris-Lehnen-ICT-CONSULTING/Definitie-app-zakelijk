# WP3 — aangetoonde transportleemte en gerichte aanvulling

25 september 2026. Coördinatorcontrole na de WP3-run van Claude Code CLI, sessie a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Dit document is een voorstel; de hieronder genoemde contractuitbreiding is nog niet uitgevoerd.

## Vastgesteld

- Chris' eerdere akkoord voor WP2, de twaalf WP3-bestanden en de zes S1-markers blijft geldig. Registratie: akkoord-wp2-wp3-s1.md.
- WP3 telt nu 685 gewijzigde regels binnen dezelfde twaalf bestanden; de raming was 330–560. De uitvoerder heeft de overschrijding te laat gemeld. Er is niets geschrapt om het regelaantal terug te brengen.
- RED: wp3-red.log, 31 failures, exit 1 vóór productieaanpassingen.
- Eigen coördinatorrun: 45 tests geslaagd, exit 0, met expliciete DEF771_SKILLS_ROOT. Bewijs: wp3-coordinator-tussenverificatie.log. Dit zijn O1-, UI-, contract- en G-tests; geen volledige suite of onafhankelijke review.
- De exacte NE-melding ontstaat intern, maar wordt niet doorgegeven in het publieke validatieresultaat. Een offline functionele controle op een losse term en ontbrekende context bevestigt beide gevallen. Bewijs: wp3-ne-transportcontrole.log, exit 0.

Letterlijke uitkomsten uit de controle:

> INT-02 — Niet uitgevoerd: kern ontbreekt. Er is geen inhoudelijk oordeel.

> INT-02 — Niet uitgevoerd: context ontbreekt. Er is geen inhoudelijk oordeel.

Beide hebben status not_evaluated, maar melding_in_publiek_resultaat=false, publiek_rule_result=null en publiek_review_item=[]. De tests bewijzen de interne reden via _evaluate_rule; ze bewijzen momenteel dus geen zichtbare NE-appmelding.

## Code en besluit raken elkaar

- Synthese v5 §4, regel 59, noemt de exacte NE-tekst een appmelding.
- ModularValidationService._verwerk_uitkomst, regels 1627–1691: rule_statuses ontvangt de status; review_required ontvangt alleen RR-redenen. _boek_rule_result neemt alleen daadwerkelijk aanwezige metadata['rule_result'] over. De INT-02-NE-reden gaat hierdoor verloren.
- validation_view.py:485–577 kan bestaande gestructureerde deeluitkomsten al met een reden tonen. Een extra UI-route is niet nodig.
- Het actuele schema, docs/architectuur/contracts/schemas/validation_result.schema.json:318–320, staat voor parts.status alleen ["pass", "fail", "review_required", "error", "not_applicable"] toe. Een NE-deeluitkomst past nog niet in dit contract.
- src/services/validation/interfaces.py:69 declareert CONTRACT_VERSION = "2.1.0".

De opdracht vraagt vooraf akkoord voor elke schema-/resultaatcontractwijziging en stoppen bij een besluitrelevant verschil tussen dossier en code. Daarom wordt deze aanvulling eerst voorgelegd. De al goedgekeurde context_lists-guard wordt niet opnieuw ter discussie gesteld.

## Aanbevolen aanvulling binnen WP3

1. Geef uitsluitend de INT-02-NE-uitkomst door via het bestaande rule_results['INT-02']: status not_evaluated, score null, fingerprint null (geen uitgevoerd oordeel), contract_version def771-int02/2, en één invoeronderdeel met status not_evaluated en de exacte NE-reden. Geen inhoudelijke review, score of violation toevoegen.
2. Boek die INT-02-uitkomst gericht in de service, met behoud van excluded_from_score en de werking van andere regels. Hergebruik de bestaande resultaatdoorgifte en bestaande UI voor gestructureerde deeluitkomsten. De enige wijziging aan productie-UI-code blijft de al goedgekeurde toevoeging aan de RR-tuple.
3. Breid parts.status in het schema additief uit met not_evaluated; versioneer het algemene resultaatcontract naar 2.2.0 en documenteer de beperkte betekenis. Geen nieuw top-level veld, dependency of databasewijziging.
4. Laat dezelfde Claude-uitvoerder eerst rode tests toevoegen voor publieke doorgifte, schema-validatie, conversie en zichtbare exacte NE-tekst. Controleer C06/C23/C56, geen RR-vraag bij NE en geen score-/gateverandering. Bewaar bestaande tests en controles.
5. Rond daarna de C1-replay af. Leg ook werkelijke NE-redenen en de exitstatus vast; een mismatch moet een niet-nul exit geven. Het huidige nog niet uitgevoerde script doet deze drie dingen nog niet volledig. Historische proef en uitkomsten blijven behouden.

## Bestanden en omvang ter akkoord

De bestaande twaalf WP3-bestanden blijven de uitvoerscope. Drie aanvullende bestanden:

- src/services/validation/interfaces.py — contractversie;
- docs/architectuur/contracts/schemas/validation_result.schema.json — NE-status voor deeluitkomst en versieomschrijving;
- docs/architectuur/contracts/validation_result_contract.md — beperkte contractuitbreiding beschrijven.

Tests blijven binnen de bestaande WP3-testbestanden. Raming van de aanvulling: 100–180 gewijzigde regels voor transport, tests, schema/documentatie en replayvoltooiing; totale WP3-raming circa 785–865 regels in vijftien inhoudelijke bestanden. Een inhoudelijke scope-uitbreiding buiten dit voorstel wordt vooraf gemeld.

Alternatief: de transportleemte expliciet open laten en alleen de interne NE-reden opleveren. Daarmee kan de zichtbare NE-appmelding niet als gerealiseerd worden afgevinkt. Voorkeur: de gerichte aanvulling hierboven, zodat de vastgelegde melding de gebruiker bereikt.

## Actuele voortgang

- [x] W3.3 — RED vastgelegd.
- [x] W3.4 — Goedgekeurde O1/S1/contextwijzigingen gebouwd, versie /2; publieke NE-doorgifte is een aanvullende open leemte.
- [ ] W3.5 — Tussencontrole 45 groen; definitieve lint-/behoudcontrole en onafhankelijke review volgen.
- [ ] W3.6 — C1-replay en bewijs nog niet uitgevoerd.
- [ ] Aanvullend schema-/resultaatcontractakkoord van Chris.

WP4–WP6 zijn nog niet gestart. Geen commits, PR's, Linear-mutaties, actieve skillpublicatie of merge uitgevoerd.
