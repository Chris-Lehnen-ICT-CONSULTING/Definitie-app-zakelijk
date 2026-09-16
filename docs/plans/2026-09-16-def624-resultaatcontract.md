# DEF-624 — eerste deellevering: fail-closed resultaatcontract

Datum: 16 september 2026. Status: goedgekeurd door Chris ("helder en akkoord", 16 september 2026, na uitleg
van de ontbrekende-statusroutes) en in uitvoering. Het akkoord dekt de grotere wijziging (>5 bestanden,
>100 regels), de resultaat-schemamigratie (contract 2.0.0, historisch 1.4.0 gepind) en de betrokken
validatieconsumers. Leidende keuze: legacy-invoer blijft leesbaar, maar een afwezige, null of ongeldige
validation_status wordt validation_unknown met een concrete contractreden.
Werkboom: /private/tmp/def624-resultaatcontract
Branch: feature/DEF-624-resultaatcontract
Basis: bceb6ab80a930a2403b51de9a0312880de527f97 (actuele origin/main bij start).

## Doel en afbakening

Een ontbrekende of ongeldige runstatus mag niet als uitgevoerd validatiebewijs gelden.
Consolideer de resultaatdefinities en draag bestaande regeluitkomsten, beoordelingdekking,
redenen en bronbeoordeling ongewijzigd door de bestaande conversies.
Dit is de zelfstandige contract-/consumermigratie binnen DEF-624; geen claim dat de gehele story klaar is.
De 53 inhoudelijke classificaties en 44 voorbeeldparen blijven apart aantoonbaar te beoordelen.
De semantische VER/SAM-implementaties blijven bij DEF-623; de formele afhankelijkheid blijft staan.
DEF-626 beheert append-only opslag/readback; DEF-627 actualiteit; DEF-630 het algemene vaststel/exportbeleid.
Geen nieuwe reviewdatabase, authenticatiestelsel, AI-jury, dependencies of wijziging van normregels/prompts/skills.

## Vastgestelde bronnen

- DEF-624 actuele beschrijving + comment 2 september over types/interfaces/schema-drift.
- Productbesluit 15 september: geen totaal- of vervangend deelscorecijfer.
- Audit 15 september: types.normalize_to_unified zonder aangetroffen actieve productiecaller;
  wel contractdrift. Niet presenteren als bewezen productie-incident.
- In huidige broncode: schema default validated; ServiceAdapter kopieert alleen aanwezige status;
  gedeelde validation_view stopt alleen bij expliciete validation_unknown.
- DefinitieChecker, bronacceptatie/hertoetsing en optionele exportvalidatie consumeren resultaatvelden;
  onderzoek alle daadwerkelijke callers voordat een wijziging wordt gedaan.

## Voorgestelde migratiekeuze

Behoud compatibele leesbaarheid van legacyresultaten, maar interpreteer afwezige, null of ongeldige
validation_status als validation_unknown met een concrete ontbrekende/ongeldige-contractreden.
Alleen een producent die werkelijk een run uitvoerde mag expliciet validated produceren.
Het schema mag nooit default validated declareren. Maak de canonieke uitvoervorm en legacy-invoergrens
expliciet; geen stilzwijgende discriminated-unionmigratie of hard afwijzen van alle historische records.

Consolideer de types op één huidige contractdefinitie met herexports/compatibiliteitsfuncties waar nodig.
Behoud publieke imports/factories voor zover ze inhoudelijk veilig te migreren zijn. Geen verwijderen.
None (score niet beschikbaar) blijft None; nooit via normalisatie in 0.0 veranderen.
Een unknown-resultaat kan geen is_acceptable=True, groene gate of gepasseerde-regelbewijs opleveren.
Bestaande regels-/bronuitkomsten blijven beschikbaar voor uitleg, zonder als actuele geldige verklaring
te worden gepresenteerd. Geen readinessmetingen verzinnen; onbekende readiness is geen lege complete set.
Voor aantoonbaar incomplete regels blijft de bestaande precieze readiness en ruleset_incomplete-reden behouden.
validated betekent uitsluitend uitgevoerde run; een fail, open review of technische regelfout blijft zichtbaar.

## Waarschijnlijke wijzigingsgebieden

- src/services/validation/interfaces.py, types.py en mappers.py; eventueel klein gedeeld contracthulpmodule.
- docs/architectuur/contracts/schemas/validation_result.schema.json (historisch gepinde schemas behouden).
- src/services/interfaces.py en service_factory.py (getypeerd transport).
- src/ui/components/validation_view.py en definition_generator_tab.py (consument van ontbrekende status).
- src/integration/definitie_checker.py (geen score bewaren uit onbekend bewijs).
- Bewezen levende resultaatconsumers in definition_edit_service.py, source_proposal_service.py,
  database/definitie_crud.py en export_service.py: alleen de statuscontrole, geen nieuwe persistentiemechaniek/gatepolicy.
- Gerichte contract-, adapter-, UI-, opslaggrens- en exportgrensregressietests; bestaande fixtures alleen
  expliciet validated maken wanneer de fixture daadwerkelijk een uitgevoerde run representeert.
Verwacht meer dan 5 bestanden en meer dan 100 regels; exacte diff volgt uit uitvoering.

## Acceptatiecriteria

1. Afwezige, null en ongeldige status krijgen aan normale dict-, legacy-object- en factorygrenzen een
   expliciete onbekend-uitkomst. Hoge score en is_acceptable=True kunnen dit niet omzeilen.
2. Bestaande valide/unknown-uitkomsten verliezen validation_status, unknown_reason, validation_readiness,
   rule_statuses, rule_results, review_required, evaluation_coverage of source_assessment niet bij conversie.
   Bronobjecten blijven ongewijzigd; herhaalde normalisatie is inhoudelijk idempotent.
3. Typebinding, actuele schemaversie en fabriekuitvoer zijn onderling consistent; schema-validatie
   bewijst de canonieke gevallen. Bestaande imports blijven bruikbaar. Geen verzonnen passed_rules.
4. None scores blijven None; de app toont geen totaal- of vervangend deelscorecijfer. Runstatus is
   onafhankelijk van goed/fout/open beoordeling. Geen extra reviewblokkeerbeleid.
5. De gedeelde UI toont bij ontbrekend/ongeldig runbewijs een juiste reden en geen groene gate;
   ze schrijft dat niet onterecht toe aan niet geladen regels.
6. Actieve adapter -> UI en opslag-/hertoetsings-/optionele exportgrenzen worden functioneel getest,
   ook met een ontbrekende discriminator. Bij benodigde repositorydata echte tijdelijke SQLite gebruiken.
   Geen score of bronbewijs als geldig bewaren/accepteren bij onbekend runbewijs.
7. Bestaande CON-01/02-beveiligingen en uitsluitend-toetsen-tekstbehoud blijven intact.
   De nog ontbrekende integrale snapshot/readback/exportvoorzieningen expliciet aan 626/627/630 overdragen.
8. Claude voert TDD en relevante tests uit, daarna make test, make lint, make test-cov-ci; log per commando
   met exitstatus. Geen testverzwakking, skips of updates van baselines zonder concrete onderbouwing.
9. Afzonderlijke Codex CLI reviewt de exacte resulterende diff, correctheid/regressies en alle criteria.
   Bevestigde bevindingen gaan terug naar dezelfde Claude-sessie; Codex reviewt daarna de einddiff.
   Coördinator controleert logs, eindhash en dekking van review. DEF-624 blijft open zolang de volledige
   storycriteria nog niet bewezen zijn.

## Verplichte rolverdeling en sessiebeperkingen

Coördinator onderzoekt, kiest scope, controleert bewijs en doet repository-/Linearcoördinatie.
Alle code/test/prompt/skillwijzigingen uitsluitend door echte ~/.local/bin/claude.
Codex CLI reviewt alleen-lezen. Geen interne subagents als vervanging.
Alleen coördinator start CLI-sessies; uitvoerder en reviewer starten geen agents, reviewers of CLI's.
Hooks blijven actief. Geen bypass van weigeringen. Geen gebruikersdatabase, .env of echte app-modelcalls.
Geen merge, push, commit of werkboomopruiming door uitvoerder/reviewer.

## Preflightbewijs

Claude Code 2.1.270, sessie b1911239-ba2c-4354-8fa1-f8e3a46d64d2:
PREFLIGHT_OK, init uitsluitend Bash/Read/Grep/Glob, mcp_servers leeg, exit 0.
Log /tmp/def624-claude-preflight.jsonl.
Codex CLI 0.154.0, sessie 01a0aaaf-4448-7c00-8d9c-dee1fda8c75d:
PREFLIGHT_OK, geen delegatietools, exit 0, agents.enabled=false en geconfigureerde MCP-servers uit.
Log /tmp/def624-codex-preflight-v2.jsonl.
Eerste strict-config-proef faalde vóór de sessie op bestaand onbekend configveld core;
gewone configuratielading slaagde. Geen globale configuratie aangepast.
