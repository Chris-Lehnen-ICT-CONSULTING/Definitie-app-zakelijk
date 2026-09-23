# DEF-821 — ESS-04-generatie en verduidelijkingsroute
Datum: 23 september 2026. Basis: b687c1615d4abd30b5b6d38dd55e64f6a758e187.
Opdracht: Chris heeft de aanbevolen combinatie van G2-instructie, G2-2-route en vergelijking vóór/na opgedragen ("doe dit"). Claude Code CLI implementeert; een afzonderlijke Codex CLI-sessie reviewt; coördinator schrijft geen software.

## Besluiten en beantwoorde ontwerpvragen
1. Alleen prompttekst aanpassen of ook uitvoerroute? Beide samen, conform DEF-767 G2-2 van 21 september 09:11 UTC. Geen definitie mogelijk is een aparte niet-succesuitkomst; nooit een definitiezin.
2. Vooraf blokkeren of modeluitkomst verwerken? Bestaand modelantwoordcontract uitbreiden: ontbrekende noodzakelijke betekenisgrond moet apart kunnen worden gemeld, zonder fictieve conflictlezingen. Bestaande ESS-02-conflictroute blijft intact.
3. Is iedere onzekerheid ontbrekende grond? Nee. Kwalitatieve betekenis kan genoeg zijn; een ontbrekend categorie-label of ontbrekend gevalsbewijs is op zichzelf geen tekort aan betekenisgrond. Geen nieuwe automatische ESS-04-jury.
4. Kwaliteitsbewijs? Vergelijk echte modeluitvoer op dezelfde vooraf vastgelegde synthetische invoer en normverwachtingen, oude/nieuwe volledige appprompt, model/settings gelijk, twee herhalingen. Houd twee casussen buiten implementatie/tuning. Rapporteer verbetering/gelijk/verslechtering/onzeker; AI-beoordeling is geen menselijke gebruikerstest.

## Codebase en patronen
Bestaand: services/modelantwoord.py strict sentinel/JSON-parser; orchestrators/definition_orchestrator_v2.py split vóór schoonmaak/toetsing/opslag; definition_task_module.py eindcontract; json_based_rules_module.py instructie; services/interfaces.py en adapters transport; ui/helpers/betekenisconflict.py bindt antwoord aan invoer/generatie; handler/tab tonen en hergenereren. Sluit hier zo klein mogelijk op aan. Async AIServiceV2, ModelRouter, SessionStateManager; geen dependencies, schemawijzigingen of logging van model-/persoonsinhoud. Andere werkbomen blijven onaangeraakt.

## Acceptatiecriteria
- AC1: exacte G2-v5-entry actief samen met G2-2-route. Volledige eindprompt heeft één consistent uitvoercontract; geen resterende exclusiviteit die de nieuwe uitkomst verbiedt. Ondersteunde numerieke grenzen blijven behouden, geen cijferplicht.
- AC2: strikt herkenbare aparte uitkomst voor ontbrekende noodzakelijke betekenisgrond, met concrete ontbrekende grond en gerichte vraag. Gemengd/misvormd antwoord faalt veilig; geen verzonnen bronconflict nodig.
- AC3: aparte uitkomst passeert vóór opschonen, validatie, verrijking en opslag; success=false, geen definitie/id/oordeel. Transport naar UI blijft compleet. Reguliere definitie en ESS-02-conflict blijven werken.
- AC4: UI toont ontbrekende grond en vraag als modelmelding, apart van definitie/technische fout. Antwoord kan expliciet verzonden en bij ongewijzigde invoer gebruikt worden; gewijzigde invoer maakt oud antwoord ongeldig. Geen HTML/Markdown-injectie via modelvelden.
- AC5: ketenproef met echte repository/tijdelijke database bewijst nul definitie-opslag bij verduidelijking en correcte opslag/readback na een reguliere kandidaat. Test parsing, transport, rendering en hergeneratie, incl. fout- en grensgevallen.
- AC6: bestaande ESS-04 judgment_review/review_required/excluded_from_score en patronen blijven; norm, generatieprompt en geïnstalleerd skillreferentieblok zijn inhoudelijk consistent. Geen DEF-630/624-reviewworkflow bouwen.
- AC7: relevante RED/GREEN-tests, make test en make lint, exact gekoppeld aan einddiff; concrete onafhankelijke Codex-review en afhandeling van bevindingen.
- AC8: echte vóór/na-effectproef met vooraf bevroren cases/verwachtingen, volledige prompts, instellingen, ruwe uitkomsten en tekstversies. Geen mocks als effectbewijs. Ontbrekende live toegang of onbeslist resultaat expliciet rapporteren; geen claim van gebruikerswinst zonder gebruikersproef.

## Effectproef — vooraf vastgelegde ontwikkelcasussen
Alle hieronder genoemde afspraken zijn fictieve betekenisgrond voor de proef, geen juridische feiten.
D1 'gelijkzijdige veelhoek': veelhoek met alle zijden even lang. Verwacht kwalitatieve kandidaat, geen extra meettolerantie/getal.
D2 'geselecteerde partij': minstens 80% van alle voorwerpen in de partij is blauw; exact 80% telt mee. Verwacht grens/noemer/inclusie behouden.
D3 'geselecteerde partij': minimaal 80% voldoet; niet gegeven waaraan of waarvan percentage wordt berekend. Verwacht aparte ontbrekende-gronduitkomst, geen verzonnen noemer/criterium.
D4 'tijdige reactie': reactie binnen drie dagen na ontvangst; onderscheid werk-/kalenderdagen is expliciet nog onbeslist maar bepalend. Verwacht vraag om dagconventie, geen eigen keuze.
D5 'ondertekend document': document waarop de afzender een handtekening heeft geplaatst; bij één concreet document is onbekend of de krabbel van de afzender is. Verwacht kwalitatieve kandidaat, geen blokkade alleen wegens gevalsbewijs.
D6 'tijdige melding': fictieve afspraak expliciet binnen drie werkdagen na ontvangst, ontvangstdag telt niet mee en derde werkdag telt wel. Verwacht betekenisbehoud, geen kalenderdagen en geen weglaten van grensbeperking.
Twee extra gevallen worden door de coördinator pas na implementatie bevroren geëvalueerd zonder prompttuning. Maximaal 32 live generatieaanroepen voor de vergelijkingsproef (8 cases × 2 versies × 2 herhalingen), via bestaande provider/modelconfig. Onafhankelijke vergelijking door reviewer, geen expertlabelclaim.

## Uitvoering en grenzen
Werkboom: .claude/worktrees/DEF-821-ess04-generatie.
Branch: feature/DEF-821-ess04-generatie-verduidelijking.
Geen merge zonder oplevering. Geen verwijderen van bestanden; geen beschermde .claude/rules-edits. Gebruik bestaande .venv van hoofdrepo. Evaluatiescripts/testcode schrijft uitsluitend Claude. Bestaande bronbestanden gericht editen is onderdeel van de opdracht; bronherkomst en herstelbaarheid behouden via Git.

