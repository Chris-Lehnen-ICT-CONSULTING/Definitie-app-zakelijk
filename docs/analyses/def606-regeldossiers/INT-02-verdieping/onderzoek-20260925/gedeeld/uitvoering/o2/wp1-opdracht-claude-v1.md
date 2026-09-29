# DEF-835 WP1 — Claude Code CLI, opdracht v1 (RED)

Jij bent de Claude Code CLI-uitvoerder. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. De hoofdsessie coördineert; een afzonderlijke Codex CLI reviewt later. Alles in het Nederlands.

Chris heeft in deze chat op 26 september 2026 expliciet akkoord gegeven op WP1 uit plan-v1.md: nieuw intern beoordelingscontract, citaatcontrole en versiebinding in vijf bestanden, volledig offline. De 100-regelsgrens voor noodzakelijk INT-02-werk is al opgeheven. Er is geen akkoord voor WP2/WP3, nieuwe dependencies, databaseschema, publieke resultaatvelden, live modelevaluatie of activering. Actions blijven uit. Je bent niet alleen in deze repository; raak geen werk van anderen aan.

Werkboom: /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2
Branch: feature/DEF-835-int02-o2
Basis: 84bdc8c1b060ab50a1bd1428aed778bb2ed6007f
Dossier U: docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2
Python: /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python

## Lezen

Lees CLAUDE.md en relevante .claude/rules, globale programmeerregels, de skill test-driven-development, U/plan-v1.md (leidend, WP1 nu geaccordeerd). Lees de INT-02-synthese v5 §2/§4 en gezamenlijk-casusregister-v5 in het bovenliggende gedeeld/. Exacte casusinput en bedoeling kunnen in de genoemde bronregisters/bewijsbestanden staan; citeer herkomst in de fixture. Gebruik bestaande domain.int03/domain.ess03 alleen als patroon, niet blind kopiëren. De bestaande baseline staat in U/bewijs/baseline-v2.log: 120 passed.

## Eigenaarschap: exact vijf nieuwe inhoudelijke bestanden

- src/domain/int02/__init__.py
- src/domain/int02/contract.py
- tests/unit/domain/test_def835_int02_contract.py
- tests/fixtures/def835_int02_ontwerpgevallen.json
- docs/architectuur/contracts/int02_assessment_contract_v1.md

Je mag daarnaast nieuwe bewijsbestanden in U/bewijs en een nieuw rapport U/wp1-claude-rood-v1.md schrijven. Geen andere bestanden wijzigen, geen bestanden verwijderen, geen git reset/clean/checkout van andermans werk. Geen commit/push/PR in deze fase. De coördinator beheert processtatus/takenlijst/Linear.

## Inhoud en bewijs

Bouw in de volgende fase een zuiver domeincontract def835-int02-assessment/1, norm def771-int02/2. Nu schrijf je eerst tests, fixture en eventueel uitsluitend minimale API-stubs om verwachte functionele failures zichtbaar te maken. Stop na RED, implementeer nog geen contractlogica.

Vereisten uit het geaccordeerde plan:
- Exacte kern, begrip, bevestigde bedoeling (of expliciet onbekend), drie contextlijsten en expliciet aangeleverde bronpassages met ID/tekst.
- Gesloten modeluitvoer: verdict, passages, reason, question, uncertainty, scope_reason, coverage. Elke relevante passage exact uit de kern met nulgebaseerde start/eind exclusief; functie en grond. Grond herleidbaar naar invoerveld/bron-ID; geciteerde grond eveneens mechanisch verifieerbaar.
- Statusmapping synthese §4 letterlijk: pass, fail, review_required (inhoudelijk onzeker tegenover nog niet beoordeeld), not_evaluated, error, not_applicable. Geen cijfer; exacte appmeldingssjablonen.
- Pass vereist geldige passagebeoordeling, volledige gedeclareerde dekking, geen gebrek of beslissende onzekerheid; code bewijst geen semantische volledigheid.
- Fail voor bewezen actorvoorschrift/procedure/discretie blijft fail als elders vragen open zijn. Ongeldige uitvoer/citaat geeft error, niet fail of RR. Onvoldoende betekenisgrond geeft precies één gerichte vraag.
- NA alleen met reikwijdtegrond buiten definitietoetsbereik; afleiding is pass, ontbrekende kern/context NE; label zonder kern eveneens NE. Woordpatronen hebben geen normatieve rol.
- Exacte onveranderlijke input vastleggen in het document; defensieve kopieën en hashes, binding over begrip/kern/betekenis/context/bronnen, normversie+hash, promptversie, routeringsconfiguratiehash en gevraagde provider/model. Werkelijk gerapporteerde modelversie of expliciet unknown. Een verandering in binding maakt oud bewijs historisch, mutatie van input/oordeel kan niet stil als actueel worden geaccepteerd. Geen implementatie van databaseopslag.
- Uitvoeringsmetadata actor/status/tijdstip/foutcategorie/transportpogingen/tokens/duur/bekende kosten, ontbrekende gegevens expliciet onbekend. Geen verzonnen meting.
- Closed-world validatie van vormen/typen/enum/posities (bool is geen int), onbekende velden weigeren. Geen reparatie van ongeldige output, geen applicatiemodelcall.
- Ontwerpgevallen C06/C23/C56, C105/C107/C112/C115/C116/C117/C118. Fixtures moeten betekenisafhankelijke labels aan expliciete context/bedoeling koppelen. Het zijn ontwikkelgevallen, geen goldset of hold-out.
- Test alle bindingcomponenten afzonderlijk, geldige/ongeldige citaten en offsets, lege/onbewijsbare pass, fail plus onzekerheid, onterechte NA, exacte input behouden, score verboden, replay/historisch.
- Ontwerp de kleinste begrijpelijke API. Geen generieke infrastructuur, geen prompt/service/evaluator/UI/record/schema wijzigen. Streef naar raming 650–950 regels maar laat noodzakelijke tests niet weg voor een teller.

## RED uitvoeren en stoppen

Schrijf tests eerst. Minimale stubs mogen alleen NotImplementedError opleveren zodat de tests functioneel falen; een import-/collectiefout geldt niet als voldoende RED. Bewaar het uitgevoerde commando, exitcode en volledige output onder U/bewijs/wp1-rood-v1.log (vrije volgende versie bij conflict). Draai:
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/domain/test_def835_int02_contract.py -o addopts= -q -ra

Bestaande tests/conftest.py installeert de offline-bootstrap vóór applicatieimports. Geen netwerk, geen productiedata, geen .env uitlezen, geen globale configs wijzigen.
Rapporteer aantallen en welk ontbreken elke groep aantoont, voorgenomen API en bronnen van de cases. Stop daarna en meld 'RED gereed; wacht op coördinator voor GREEN'. Dit is een intern checkpoint, geen nieuwe gebruikersgoedkeuring.
