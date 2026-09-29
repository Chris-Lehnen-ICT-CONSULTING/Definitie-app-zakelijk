# DEF-835 WP3 — tussenoplevering na onafhankelijke review

28 september 2026. De negen geaccordeerde bestanden zijn geïmplementeerd en gereviewd. WP3 als geheel blijft open door acht verouderde assertions in vijf bestaande testbestanden buiten het huidige mandaat.

## Geleverd

- Pure synchrone INT-02 O2-evaluator decision_rule_assessment, geregistreerd in runtime-enum, registry en root-SSOT.
- Hergebruik van WP1 voor actuele invoer/configuratie, citaat- en documentcontrole. Zes uitkomsten; fail adviserend en scoreloos. Signalen bepalen geen oordeel.
- Publiek resultaatcontract 2.3.0: assessment/signals voor INT-02 naast bestaande INT-03, andere regelvelden blijven gesloten.
- Actief INT-02-record blijft O1. Geen appintegratie, modelproef, productieactivering, push, PR of merge. Actions niet gewijzigd.

Exacte inhoudelijke bestanden staan in wp3-scopeaanvulling-v1.md. De eerste implementatie telt 1497 toevoegingen en 4 vervangingen/verwijderde tekstregels over negen bestanden, waarvan 1174 toegevoegde testregels. De omvangverruiming voor INT-02 is geaccordeerd. Geen bestanden of bestaande testgevallen verwijderd. R1 voegde vervolgens 14 testregels toe en wijzigde de evaluator met +4/−2.

## Commits en rollen

- Branch feature/DEF-835-int02-o2.
- Basis: 2be81c577653f8efbab6fa2c3794598556d32d13.
- Eerste implementatie: d3fc53eaed14e6a303605146b7e5f8b9ea3cef5e.
- Gereviewde correctie/eindcode: 9769730d6e4a68dda9834c21c384f140e16c75e4.
- Claude Code CLI 2.1.283, claude-opus-5-5: sessie c75abf0d-3c01-4c02-a672-536d75daa15a, implementatie en correctie.
- Codex CLI 0.157.1, gpt-6-astra/high (rollout gecontroleerd): verse WP3-review en gerichte herreview in sessie 01a0e4f2-9a94-70b2-9dcd-87202e24b697.
- Aparte reviewwerkboom /private/tmp/def835-wp2-review-20260927 hergebruikt, detached op eindcode, getrackte bestanden schoon.
- Coördinator: opdrachten, bewijscontrole, eigen tests, diff en lokale commits. Geen implementatie/testcode geschreven.

## Bewijs

| Stap | Waargenomen resultaat |
| --- | --- |
| O1/schema-nulmeting | 55 passed in 1.36s, exit 0 |
| WP3 RED | 92 failed, 19 passed in 5.53s, exit 1; geen collectie-/setupfouten |
| Eerste GREEN | 111 passed, exit 0; testbestanden bytegelijk aan RED |
| Coördinator bredere gerichte selectie | 539 passed, 8 failed in 2.63s, exit 1; alle acht bekende oude assertions |
| Onafhankelijke eerste review | 111 passed; één bewezen Important/P2-fout WP3-R1 |
| R1 RED | 8 failed, 111 passed, exit 1 |
| R1 GREEN eindversie | 119 passed, exit 0; bytegelijke tests |
| Coördinator eindcode | 119 passed in 0.97s, exit 0 |
| Onafhankelijke herreview | 119 passed in 1.05s, exit 0; R1 gesloten, geen nieuwe bevinding |
| Ruff/Black en normale lokale commitgates | Geslaagd |

De coördinatorselectie bevat de twee WP3-bestanden plus O1, INT-03 evaluator, evaluatorregistry, rootcontractcache, WP1 en de vier andere versiepinbestanden. De R1-correctie wijzigde alleen de evaluator en zijn testbestand; de acht bekende bestaande failures zijn hierdoor niet opgelost.

Volledig bewijs staat onder bewijs/, met commando's, exitcodes en bestandshashes. [Eerste review](wp3-codex-review-v1.md), [herreview](wp3-codex-herreview-r1-v1.md), [R1-verslag](wp3-claude-r1-verslag-v1.md), [coördinator eindcode](bewijs/wp3-coordinator-r1-v1.log).

### Brede unitrun en beperkingen

Claude draaide aanvullend een brede unitselectie: 8395 passed, 10 failed, 86 skipped, 1 xfailed, 1 collectie-error. Acht failures zijn bovenstaande oude assertions. Twee failures betreffen de OfflineGate bij performance_tracker; Claude rapporteerde dezelfde failures op basis-HEAD, maar deze basisvergelijking is niet onafhankelijk bevestigd. Eén import-file-mismatch ontstond bij een commando zonder importlibmodus. De volledige run is bewaard in bewijs/wp3-claude-breed-unit-v1.log.

Geen volledige-suite- of algemene regressiegroenclaim. Geen semantische modelkwaliteitsclaim. Geen verborgen omzetting van rode tests naar groen: diagnoses in tijdelijke kopieën tellen niet als gewijzigde of geslaagde repositorytests.

## Reviewdispositie

**WP3-R1 — fix nu, gesloten.** Een aanwezige ongeldige record_text viel terug op raw_text en kon een actueel pass/fail opleveren. Acht nieuwe RED-tests bewezen dit. De correctie gebruikt fallback uitsluitend bij een ontbrekende sleutel; ongeldige waarden gaan nu naar WP1-validatie en leveren error, zonder assessment/violation. Lege string blijft NE. Dezelfde reviewer controleerde de correctie en het behoud van fallback/NE onafhankelijk.

## Nog vereist vóór aftekenen WP3

Chris heeft nog geen antwoord gegeven op de gebundelde vraag voor vijf extra bestaande testbestanden. Het concrete voorstel staat in [wp3-scopeaanvulling-tests-v1.md](wp3-scopeaanvulling-tests-v1.md). Zeven geparametriseerde failures pinnen versie 2.2.0; één weigert de inmiddels geaccordeerde INT-02-detailvelden. De functionele cases moeten blijven bestaan en hun contractverwachtingen moeten naar 2.3.0 worden herijkt.

Na akkoord: dezelfde Claude-uitvoerder voert die beperkte herijking uit, coördinator draait de geraakte selectie, dezelfde reviewer beoordeelt de testdelta. Geen nieuwe volledige implementatieronde of heronderzoek.

Daarna blijven WP4 (onafhankelijke goldset/modelkwaliteit), WP5 (gedeelde opslag/ketenintegratie incl. ModularValidationService, ketenlogging en backendmetadata) en WP6 (eindgates/PR/afzonderlijke activering) open. Voor de reeds toegestane echte modelproef staan profiel en kostenplafond nog open.

## Proces

Volledige prompts zijn lokaal in dit dossier bewaard. Prompt Forge-fallback blijft gelden na de eerder geblokkeerde bereikbaarheidscheck; geen omzeiling. Claude had alleen Read/Glob/Grep/Edit/Write/Bash en geen MCP-delegatietools. Codex bevestigde afwezigheid van native/MCP-delegatietools; shelltoegang blijft een werkafspraak. Geen extra agent- of CLI-sessies door uitvoerder/reviewer gestart.
