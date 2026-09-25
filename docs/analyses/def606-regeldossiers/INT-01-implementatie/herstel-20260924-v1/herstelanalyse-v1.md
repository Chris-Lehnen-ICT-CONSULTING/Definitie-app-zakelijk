# DEF-770 — herstelanalyse v1 (oorzaakdiagnose vóór correctie)

24 september 2026 · uitvoerder: Claude Code CLI · basis `ee13ae1d7ce05482bd61f37dd51099b7ba8d23f0` · branch `feature/DEF-770-int01-effectproeven`.

Bronnen (read-only historisch bewijs): `effectproeven-20260924-v1/` — `t24-rapport-v1.md`, `t24-gevallen.json`, `t24-adjudicatie.json`, `t24-eindbeoordeling-v1.json`, `g24-rapport-v1.md`, `g24-einduitkomst-v1.json`, `g24-invoer.json`, `g24-voorbereiding-nieuw-v1.json` (echte prompts). De 24 T24- en 6 G24-gevallen zijn na deze correctie ontwikkelmateriaal; er is niets herlabeld.

## 1. T24 — zes afwijkingen, grondoorzaak per geval

Alle regelnummers verwijzen naar `src/domain/int01/zinsgrenzen.py` op de basis.

| Geval | Tekst (kort) | Referentie | App | Grondoorzaak |
|---|---|---|---|---|
| T15 | `pakket met uitsluitend:\n- een routeblad;\n- …` | zinsstructuur pass | 3 onzekere grenzen | `_regelgrenzen` (r408–428) meldt elke regel die met een opsommingsteken begint als onzeker zodra de vorige regel niet op `.?!…` eindigt. Dat de vorige regel met `:` of `;` eindigt — het teken dat de zin juist doorloopt — telt niet mee. |
| T17 | `code die de melding 'Gereed. Neem de bak mee.' op … laat verschijnen.` | pass | 2 onzekere grenzen | Een punt binnen een ingesloten citaat is altijd onzeker (`_classificeer_punt` r394–395), en de punt vóór het sluitende aanhalingsteken gevolgd door kleine letter valt in de tak "punt gevolgd door kleine letter" (r397–404). Citaat (vermelding van andermans tekst) en haakjes (eigen tekst) worden gelijk behandeld (`ingesloten`, r258). |
| T19 | `“strook … onbelicht blijft.”` | pass + open onderdeel `broncitaat` | pass zonder `broncitaat` | `regeluitkomst` (r542–545) voegt het broncitaatonderdeel alleen toe bij `geheel_geciteerd and zekere_grenzen`. Een geheel geciteerde kern van één zin mist daardoor het open onderdeel. |
| T22 | `Oefenstatus:` | onzeker (onvoldoende informatie) | pass | Er is geen kandidaat (geen `.?!`, geen regelovergang); een kern die op een dubbele punt eindigt wordt nergens herkend. |
| T23 | `onderbreking van de geluidsproef... daarna opnieuw luisteren` | onzeker | pass | `_classificeer_weglating` (r311–314) meldt een beletselteken alleen onzeker vóór een hoofdletter; vóór een kleine letter geeft het "geen grens". |
| T24 | `strook voor tijdelijke bundeling. controle volgens zqv. blijft vereist` | fail (zekere grens na `bundeling.`) | onzeker | `_classificeer_punt` (r397–404) maakt elke punt vóór een kleine letter onzeker, ook na een volledig woord gevolgd door een zelfstandige zin met persoonsvorm. De oude app gaf hier `fail`; de nieuwe regressie ontstond door die generieke tak. |

### Gekozen generalisaties (geen ID- of begripsuitzondering)

1. **Opsomming binnen één kern (T15).** Een lijstregel na een regel die op `:`, `;` of `,` eindigt, zet dezelfde zin voort: geen grens. Nabij negatief: een lijstregel na een regel zónder zulk teken blijft onzeker; een punt met hoofdletter binnen een lijstitem blijft een zekere grens.
2. **Ingesloten citaat (T17).** Leestekens binnen een gesloten, ingesloten aanhalingstekenpaar horen bij de vermelde tekst en vormen geen buitenste zinsgrens. Haakjes (eigen tekst van de definitie) blijven ongewijzigd onzeker. Een geheel geciteerde kern blijft inhoudelijk tellen (twee zinnen blijven twee zinnen). Nabij: punt ná het citaat gevolgd door hoofdletter blijft zeker; ongepaard aanhalingsteken geeft geen uitzondering.
3. **Broncitaat bij iedere geheel geciteerde kern (T19).** Het open onderdeel `broncitaat` volgt uit het citeren zelf, niet uit het aantal zinnen.
4. **Los label (T22).** Een kern die (na witruimte) op een dubbele punt eindigt, is onvolledig: zichtbaar onzeker met de passage. Nabij positief: `status: actief` blijft één zin.
5. **Beletselteken met vervolg (T23).** Een beletselteken gevolgd door verdere tekst is altijd onzeker (onderbreking binnen de zin of zinseinde is niet vast te stellen). Nabij: een beletselteken aan het einde of binnen een citaat geeft geen grens.
6. **Kleine letter na een zekere zinsgrens (T24).** Zeker alleen als beide kanten dat dragen: het woord vóór de punt is een volledig woord (≥ 5 letters, met klinker, geen bekende of gestippelde afkorting) **én** het vervolg bevat vóór de volgende duidelijke grens een eenduidige persoonsvorm uit een gesloten lijst (hulp- en koppelwerkwoorden zoals `is`, `wordt`, `blijft`, `heeft`, `kan`, `moet`). Anders blijft het onzeker. Ambigue vormen (`zijn`, `was`, `wil`) staan bewust niet in de lijst. Nabij negatief: `bundeling. controle volgens protocol` (geen persoonsvorm) en `afd. controle blijft vereist` (afkortingsvorm) blijven onzeker.

Bekende grens van 6: een onbekende afkorting van ≥ 5 letters met klinker, gevolgd door kleine letter en een persoonsvorm, wordt als tweede zin gemeld (vals `fail`). Dat is zichtbaar met passage en reden; de regel als geheel blijft nooit `pass` en blokkeert niet zelfstandig.

### Contractversie

Punten 1–6 wijzigen de betekenis van opgeslagen deeluitkomsten. `CONTRACTVERSIE` gaat van `def770-int01/1` naar `def770-int01/2`. De bestaande binding (`opslag._bindt_aan`, `lees_beoordeling`) maakt een onder `/1` opgeslagen uitkomst daardoor historisch ("andere INT-01-contractversie; opnieuw toetsen") en `met_nieuwe_beoordeling` bouwt bij de volgende schrijfactie een verse uitkomst met historie. Geen migratie, geen schemawijziging.

## 2. G24 — waarom INT-01 soms niet in de prompt staat

**Bevinding.** In de echte prompts (`g24-voorbereiding-nieuw-v1.json`) ontbreekt de hele sectie `### 🔒 Integriteit Regels (INT)` bij G01, G04 en G05; bij G02, G03 en G06 staat zij er. Precies G01/G04/G05 hebben een lege `juridische_context` en `wettelijke_basis` (`g24-invoer.json`). Daarom waren die prompts oud/nieuw byte-identiek: de gewijzigde INT-01-instructie bereikte ze niet.

**Oorzaak in de echte PromptServiceV2-route.** `PromptServiceV2 → UnifiedPromptBuilder → ModularPromptAdapter → PromptOrchestrator.build_prompt`. In `src/services/prompts/modules/prompt_orchestrator.py` r466–471 (`_get_active_modules`, DEF-123-tokenoptimalisatie) wordt `integrity_rules` (en `sam_rules`) alleen geactiveerd bij `has_juridische_context() or has_wettelijke_context()`. Bij alleen organisatorische context of zonder context valt INT-01 dus weg.

**Toepasselijkheidsbesluit.** INT-01 geldt voor iedere definitie: `INT-01.json` heeft `geldigheid: "alle"`, en de validatie toetst INT-01 altijd, ongeacht context (T24 en G24 draaiden met `context={}`). Generatie en toetsing spreken dus niet dezelfde norm bij niet-juridische context. Dat is een aantoonbare noodzaak voor INT-01.

Voor de overige INT-regels en SAM verandert niets. Ook hun records zeggen grotendeels `alle`/`gehele definitie`, maar die bredere inconsistentie valt buiten deze opdracht ("geen contexttoepasselijkheid van andere normen zonder bewezen noodzaak"). Ik meld haar als open punt voor de coördinator.

**Ingreep (smal, bestaand patroon).** Hetzelfde patroon als DEF-743 voor CON-02 (`json_based_rules_module.py` r30–43):
- de integrity-module wordt altijd geactiveerd;
- de module toont zonder juridische of wettelijke context uitsluitend INT-01, met de overige INT-regels in `rules_skipped`;
- met juridische of wettelijke context blijft de volledige INT-set ongewijzigd.

Het bewijs loopt via de echte `PromptServiceV2` voor vier contextvarianten (geen, alleen organisatorisch, alleen juridisch, alleen wettelijk), met bronreceipt en bronvolledigheid.

## 3. G24 — betekenisbehoud: instructiegebrek versus modelvariatie

Classificatie op herhaling en variant (4 teksten per dossier: oud/nieuw × 2). Een verschijnsel in alle vier teksten heet systematisch; in één tekst heet het variatie. Dit is een indicatie uit zes dossiers, geen causaal bewijs.

| Verschijnsel | Dossier | Voorkomen | Mogelijke instructiedruk in de echte prompt | Duiding |
|---|---|---|---|---|
| `kan worden voortgezet` wordt `wordt voortgezet` (modaliteit) | G02 | 4/4 | ARAI-04 en ARAI-04SUB1: "Vermijd modale hulpwerkwoorden", met ✅ zonder `kan` naast ❌ met `kan`. Er staat nergens dat een mogelijkheid dan anders uitgedrukt moet worden. | Systematisch; plausibel instructiegebrek |
| exclusieve oorzaak (`uitsluitend doordat` vs `doordat uitsluitend`) | G02 | 1/4 | — | Modelvariatie |
| lopend onderzoek als toepassingsvoorwaarde ontbreekt | G06 | 4/4 | INT-02: "Vermijd voorwaardelijke formuleringen zoals … 'alleen als'". Er staat niet dat een afbakenende voorwaarde als kenmerk behouden moet worden. | Systematisch; plausibel instructiegebrek |
| beperkingen (zegt niets over juistheid of uitkomst) ontbreken | G06 | 4/4 | INT-08 (positief formuleren) en "geen toelichtende uitweiding"; INT-01 noemt negaties, maar niet expliciet brongebonden beperkingen | Systematisch; deels normkeuze (niet elke bronbijzaak hoort in de kern) |
| `die voortduurt` met dubbel antecedent | G06 | 1/4 | — (INT-03 bestaat al) | Modelvariatie |
| "verschil is op zichzelf geen bewijs van verlies" ontbreekt | G05 | 4/4 | G05 kreeg geen INT-sectie (§2); verder dezelfde druk als hierboven | Systematisch; mede door de ontbrekende INT-01-sectie |

**Ingreep (gericht, binnen INT-01, geen buurregelnorm gewijzigd).** De INT-01-instructie heeft al de betekenisbehoudbepaling ("behoud negaties en de bronbetekenis; maak de betekenis niet smaller of ruimer om korter te formuleren"). Ik vul die aan met concrete, normconforme uitvoeringsaanwijzingen die ook gelden bij herformuleren om een andere regel te volgen:
- een mogelijkheid wordt geen feit (druk haar zo nodig zonder modaal werkwoord uit), dus verenigbaar met ARAI-04;
- `uitsluitend` blijft bij het deel waarop het slaat;
- een afbakenende toepassings- of eindvoorwaarde wordt als kenmerk geformuleerd in plaats van weggelaten, dus verenigbaar met INT-02;
- een verwijzing wijst naar één antecedent;
- een brongebonden beperking blijft staan als zij het begrip afbakent;
- expliciet: niet-afbakenende bronbijzaken niet opnemen, zodat niet alle bronbijzaken verplicht worden en de definitie niet onnodig langer wordt.

ARAI-04, INT-02 en INT-08 zelf blijven ongewijzigd. Dat hun instructies los gelezen tot betekenisverlies kunnen leiden, meld ik als open normpunt.

## 4. Verwachte bestanden en noodzaak

| Bestand | Ingreep | Noodzaak |
|---|---|---|
| `src/domain/int01/zinsgrenzen.py` | generalisaties 1–6, broncitaat, `CONTRACTVERSIE` → `/2`, docstring | T15/T17/T19/T22/T23/T24 |
| `src/services/prompts/modules/prompt_orchestrator.py` | `integrity_rules` altijd actief | §2 |
| `src/services/prompts/modules/json_based_rules_module.py` | INT: zonder juridische/wettelijke context alleen INT-01; aanvulling op de INT-01-instructie | §2, §3 |
| `src/toetsregels/regels/INT-01.json` | toelichting: citaat, opsomming, label, beletselteken, kleine letter | overeenstemming record en evaluator |
| `tests/unit/validation/test_def770_herstel_zinsgrenzen.py` (nieuw) | zes gevallen en nabije tegenhangers, beide laadpaden, contractversie en opslag | TDD |
| `tests/unit/services/prompts/test_def770_herstel_promptdoorwerking.py` (nieuw) | echte PromptServiceV2, vier contextvarianten, receipt | TDD, §2 en §3 |
| bestaande DEF-770/DEF-743-tests | drie verwachtingen die de oude semantiek vastlegden (ingesloten citaat onzeker, `object. heeft` onzeker, integrity inactief zonder juridische context) en een helper die op INT-02 splitst | semantiek bewust gewijzigd; herstelkopie bewaard |

Een skillstekst die dezelfde INT-01-instructie of zinsgrensregels bevat (skills-PR #355) moet mogelijk worden afgestemd. Dat valt buiten deze opdracht en meld ik aan de coördinator.
