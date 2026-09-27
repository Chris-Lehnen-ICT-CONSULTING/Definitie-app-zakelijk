# DEF-835 — WP2 oplevering v1

27 september 2026. Offline WP2 geaccepteerd na onafhankelijke herreview. Actuele werkstaat: [takenlijst-v7.md](takenlijst-v7.md). Leidend plan: plan-v1.md, met akkoord-wp2-v1.md.

## Geleverd
De begrensde INT-02 AI-beoordelingsdienst en letterlijke T-prompt zijn gebouwd. De dienst gebruikt het WP1-contract voor citaatcontrole en statusmapping, gescheiden systeem-/dataprompt, expliciete modelprofielen, invoer-/uitvoer-/tijdlimieten, één transportpoging zonder SDK-retry/herstelcall en een cache voor gevalideerde beoordelingen. Wijziging van invoer, norm, prompt, profiel, budget of effectief capability-beleid verandert de binding/cache.

Drie inhoudelijke bestanden:
- src/services/validation/int02_assessment_service.py
- tests/unit/validation/test_def835_int02_assessment_service.py
- tests/unit/services/prompts/test_def835_int02_prompt.py

Bestaande O1, WP1, adapters/backend, configuratie, evaluator, publiek resultaatcontract/schema, container, UI en opslag zijn niet gewijzigd. Geen nieuwe dependencies, appmodelcalls, productiedata, push, PR, merge of activering. Actions zijn niet gewijzigd en blijven volgens de gebruikersopdracht uit.

## Commits en rollen
- Branch: feature/DEF-835-int02-o2.
- WP2-basis: b56e0e225e65eac00ad73239900d2e6c1bfc2422.
- Eerste code: 0e336c6c4b40fd53d4a1ef3c2283f6a99691510f.
- Gecorrigeerde/geaccepteerde code: 48a6b3fa57b541fb2b8e868c269f6f77012a2ca1.
- Claude Code CLI 2.1.283 (claude-opus-5-5): uitvoering/correcties, sessie 99ef6e30-cc76-445a-932d-8c8bd578b835.
- Codex CLI 0.157.1 (gpt-6-astra/high, rolloutcontext gecontroleerd): onafhankelijke review/herreview, sessie 01a0e1e2-3d37-7111-bc1d-805954a52a16, aparte werkboom /private/tmp/def835-wp2-review-20260927.
- Coördinator: opdracht, verificatie, concrete diff, bewijs en commits; geen implementatie/testcode geschreven.

## Bewijs
| Stap | Resultaat |
| --- | --- |
| Eerste RED | 158 failed, 3 passed; geen collectie-/setupfouten; coördinator herhaalde dit. |
| Aanvullende parser-RED | 7 failures vóór implementatie. |
| Eerste GREEN | 169 WP2-tests; coördinator 603 inclusief gerichte regressies. |
| Onafhankelijke review | Drie P2-bevindingen, alle met reproduceerbaar bewijs. |
| Correctie-RED | 19 failed, 167 passed op oorspronkelijke service met dezelfde tests als correctie-GREEN. |
| Correctie-GREEN | 186 WP2-tests en 434 gerichte regressietests geslaagd. |
| Coördinator finale inhoud | **620 passed in 4.01s**, exit 0. |
| Onafhankelijke herreview | **186 passed in 1.45s**, exit 0; F1/F2/F3 gesloten. |
| Lint/commitgates | Ruff0.16.5, Black en normale lokale pre-commitcontroles geslaagd. |

Dit is gerichte offline verificatie, geen volledige-suite- of semantische modelkwaliteitsclaim.
[Herreview](wp2-codex-correctiereview-v1.md), [correctierapport](wp2-claude-correcties-v1.md), [coördinatorlog](bewijs/wp2-coordinator-eind-v1.log).

Eén extra functiebetekenistest is tijdens eerste GREEN na de fix geschreven. Mutatiebewijs toont detectie van de fout, maar verandert de volgorde niet; dit blijft een expliciete TDD-procesafwijking. De oorspronkelijke RED-tests zijn behouden; twee onjuiste transporttellingsassertions zijn gemotiveerd herijkt, zonder testgevallen te verwijderen.

## Reviewdispositie
1. **F1 — fix nu, gesloten:** afgekapt of niet aantoonbaar afgerond antwoord geeft error, nooit een inhoudelijk of gecachet oordeel. De huidige OpenAI-adapter verliest finish_reason; daarom geeft deze route voorlopig géén inhoudelijk O2-oordeel. Een adaptercorrectie valt buiten WP2.
2. **F2 — fix nu, gesloten:** temperature/thinking-capabilitybeleid zit in de binding. Wijzigingen leiden tot cacheverversing en historische afwijzing. Ontbrekend beleid blokkeert vóór de call.
3. **F3 — fix nu, gesloten:** transportpogingen zijn unknown wanneer de interface ze niet meet; 0 alleen bij vaststaande serviceblokkades vóór de call.
4. **Transportlogging — gemotiveerde scopewaiver:** bestaande AsyncGPTClient kan providerexceptiontekst loggen. Eigen dienstlogger logt geen ruwe inhoud. Alleen aanvaard voor het offline/niet-geactiveerde pakket; ketenbrede inhoudsvrije logging blijft verplicht vóór integratie/activering. Geen privacyclaim over de hele keten.

## Autorisatie en echte modelproef
Chris autoriseerde op 27 september: “Echte modelaanroepen zijn toegestaan go for wp2”. Die toestemming blijft geldig en wordt niet teruggedraaid. Er is nog geen appmodelproef uitgevoerd: de aanvullende vraag over het concrete kostenplafond is nog niet beantwoord. De voorgestelde technische proef gebruikt uitsluitend synthetische invoer en maximaal drie calls; geen productieactivering of goldsetkwalificatie.

Voor uitvoering van die proef moeten kostenplafond en een passend expliciet proefprofiel worden vastgelegd. Het bestaande Budget begrenst tokens/tekens/duur; het garandeert geen monetair plafond. Werkelijke modelversie/usage/kosten blijven unknown zolang de backend ze niet doorgeeft. Geen ongekwalificeerd productiemodel of kwaliteitsbewijs verzonnen.

## Integratievoorwaarden en vervolg
- WP3: afzonderlijk akkoord voor evaluator/publiek resultaatcontract/schema en de zeven geplande bestanden.
- Service en adapter gebruiken bij integratie dezelfde routerconfiguratie; geen attestatie van werkelijk verzonden providerbeleid.
- Backendstopreden voor OpenAI, ketenlogging en betere provider-/usagemetadata moeten in het verdere integratieplan expliciet worden besloten.
- WP4: onafhankelijke goldset/hold-out, expertlabels en vooraf vastgestelde kwaliteitseisen blijven open. Ontwerpgevallen zijn geen hold-out.
- WP5: gedeelde opslag/herlaadroute volgens DEF-626, UI/export/historische binding.
- WP6: finale gates/PR en afzonderlijke activering. DEF-835 blijft In Progress; brede acceptatiecriteria niet als geheel afgevinkt.

## Proces
Alle CLI-prompts staan volledig in dit dossier; lokale Prompt Forge-fallback blijft gelden na de eerder geblokkeerde bereikbaarheidscheck. Claude kreeg alleen Read/Glob/Grep/Edit/Write/Bash en geen MCP/delegatietools; reviewer meldde geen zichtbare delegatietools en gebruikte geen delegatie. Bronbewijzen staan eenmaal onder bewijs; ruwe CLIstreams blijven lokaal. De mislukte update van takenlijst-v5 door bestandsbeveiliging is niet omzeild; v6 en v7 zijn nieuwe versies, eerdere bestanden behouden.

