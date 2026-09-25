# Synthesecontrole door C — INT-03 — 25 september 2026 (v1)

Controleur: onderzoeker C (Claude Code CLI, `claude-fable-5-1`, effort `xhigh`; zelfde sessie als fase 1 en 2). Gecontroleerd: `gedeeld/synthese-v1.md`, sha256 `0065ec61dc0fff50902061a722698f8ca6c8cc2d4b2d54738df95f89e822ad4e` (door C herberekend; gelijk aan de opdracht). Daarvoor gelezen: `onderzoek-a/aanvulling-a-v2.md`, `verwerking-a-v1.md`, `bewijsmanifest-a-v2.json`; `onderzoek-b/aanvulling-b-v2.md`, `review-b-op-c-v1.md` (B's review op C — door C pas nu gelezen, dus niet in `aanvulling-c-v2.md` verwerkt; zie §3), `verwerking-b-v1.md`; `onderzoek-d/aanvulling-d-v1.md`, `casusregister-d-v2.md`. Gerichte broncontroles op commit `26f2374d`: `modular_validation_service.py` (r. 1413-1427), `feitenbasis-v1.md` r. 46, `definitie-nederlandse-definities/reference.md` (sectiekoppen). Hashes van alles in `bewijsmanifest-c-v3.json`.

Oordelen: **juist** · **weglating** · **onjuiste weergave** · **te stellig** · **tegenspraak** · **aanvulling**. Kwalificatie: **M** = materieel (vereist synthese-v2) · **R** = redactioneel. Punten zijn geordend naar de zes gevraagde aspecten; SC-nummers zijn stabiel.

## 1. Puntsgewijze controle

### 1.1 Weglatingen (staat elk materieel C-punt erin, of herkenbaar niet overgenomen?)

| # | Passage / sectie synthese | Oordeel | Grond | Gevraagde correctie | M/R |
|---|---|---|---|---|---|
| SC-01 | §1 "(B: Taaladvies/Onze Taal gelezen; C/A secundair)" | weglating | D las Onze Taal W1–W4 rechtstreeks (`aanvulling-d-v1` §Opdracht); §7 van de synthese zegt zelf "alleen B/D gelezen" | "B en D gelezen; A/C secundair" | R |
| SC-02 | §2 "Bewezen op 26f2374d (A 20, B 16, C 30, D rijen …)" | weglating (getal ontbreekt) | D: 20 service-uitkomsten (E01–E10 × manager/cache) en 4 promptvarianten (`casusregister-d-v2` kop; `aanvulling-d-v1` §Q6) | "D 20" | R |
| SC-03 | §7 "A-E03/B-E03/C-E03 vervuild (lemma in tekst)" | weglating + nuance | D-E03 is dezelfde fixture-tekst met term *regeling*; D-E04 "Verslag over een besluit nadat het is vastgesteld" heeft term *verslag* in de tekst; B-E04 idem (*instrument*). B's verwerking RB-05: de gevallen blijven geldig voor de status-/signalen-nulmeting, alleen niet voor herstel- of buurregelvergelijking | Lijst aanvullen met D-E03, D-E04, B-E04 en de B-nuance overnemen ("geldig als nulmeting; niet als herstel-/buurregelgeval") | R |
| SC-04 | §1 voorbeelden: fout toevoegen = "… waarbij deze vertrekt", "… haar rechten …", "… over zijn besluit" | weglating (inconsistent met a-v2) | Geen lemmavrij 'het'-voorbeeld naast het ASTRA-paar, terwijl RA-22 dat vroeg en `aanvulling-a-v2` §5.1 er een heeft ("voorziening waardoor het kan worden voortgezet"); alternatieven: C-G2 "handeling van een medewerker aan een collega zodat het kan worden voortgezet", D "Verslag over een besluit nadat het is vastgesteld" (als JSON-voorbeeld zonder term lemmavrij) | Eén 'het'-voorbeeld toevoegen | R |
| SC-05 | §2 T-contract en opties | weglating | Gevolg per optie voor `runtime_contract` in INT-03.json ontbreekt: T-a houdt `evaluator: judgment_review`, `example_pair_policy: review_policy`; T-c vraagt een nieuwe evaluator (patroon ESS-03 `countability_assessment`) met `score_policy: excluded_from_score` (C-v2 G2 slotzin, Q3 rij CON-02/ESS-03) | Eén regel per optie toevoegen | R |
| SC-06 | §2 T-a "Te beoordelen verwijzing: '{passage}'" en "vastlegging … met versiebinding" | weglating met ontwerpgevolg | B's bewijscontract (passage met offsets, taalfunctie, kandidaten, beoordelaar/model, versie; `ReviewRequirement` heeft nu 4 velden) is tot één bijzin gereduceerd. Bovendien (B BC-10, door B gecontroleerd op `judgment_review.py` r. 157-192): `_reden_met_passages` dedupliceert identieke fragmenten met `dict.fromkeys`; drie keer 'die' levert één passage. Per-voorkomenweergave met offsets is extra ontwerp, geen ESS-04-hergebruik | In T-a opnemen: "met de bestaande helper één unieke passage per fragmenttekst; per voorkomen (offsets) is een uitbreiding van het bewijscontract (B, DEF-624/626)"; C's eigen registerverwachting "passages 'die' ×3" is hiermee onjuist (§3 E-C3) | **M** |
| SC-07 | Kop "Bewijs: proefuitkomsten-{a,b,c,d}-v1.json, proefuitkomsten-c-v2.json"; geen manifest | weglating (bewijsbinding) | De synthese bindt geen hashes van haar invoer en verwijst naar geen manifest. `bewijsmanifest-a-v2.json` (10:30) bindt a-v2 en de ontvangen v1-stukken, maar niet `aanvulling-b-v2.md`, `aanvulling-c-v2.md`, `aanvulling-d-v1.md`, `review-b-op-c-v1.md`, `verwerking-b-v1.md`, `verwerking-c-v1.md` — precies de stukken waarop de synthese steunt (RA-31 vroeg dit al voor de synthese) | Synthese-v2 met een bijbehorend manifest (bijv. `bewijsmanifest-a-v3.json`) dat alle invoer met hash bindt en de synthesehash apart meldt; C levert de hashes van de door haar gelezen invoer in `bewijsmanifest-c-v3.json` | **M** |
| SC-08 | §7 "ARAI-05 … overlap" | weglating | B en D maten ARAI-05 `pass` op alle INT-03-gevallen: de buurregel is geen vangnet (relevant voor K4(i): 'in het kader' weghalen verplaatst niets naar een werkende regel) | Toevoegen "ARAI-05 keurt geen INT-03-geval af (B/D-proef)" | R |
| SC-09 | §1 patronen (iii) | weglating | 'diens' (B-E17, C-v2 G2) ontbreekt in de uitbreidingslijst | 'diens' toevoegen | R |
| SC-10 | Feitenbasis als bron (§1, kop) | tegenspraak / weglating | `gedeeld/feitenbasis-v1.md` r. 46 noemt `_evaluate_json_rule`; de code op 26f2374d heeft `_evaluate_rule` (r. 1413) → `_evaluate_via_registry` (r. 1427). D signaleerde dit; de synthese neemt het niet op | Erratum op de feitenbasis in synthese-v2 (of feitenbasis-v2) | R |
| SC-11 | §2 "levert altijd `review_required` …" en contractrij "technische fout (`error`)" | te stellig | De service heeft al een foutgrens: ontbrekende vereiste invoer → `not_evaluated`, `RuleContractError`/exceptions → `error` (`modular_validation_service.py` r. 1430-1483; B BC-07). "Altijd review" geldt voor normaal afgeronde evaluaties | "Bij normaal afgeronde evaluatie altijd review_required; de service-foutgrens (r. 1430-1483) bestaat al" | R |

### 1.2 Standpuntweergave C (voorkeur en bewaarde verschillen)

| # | Passage / sectie | Oordeel | Grond | Gevraagde correctie | M/R |
|---|---|---|---|---|---|
| SC-12 | §3 en K3: "(a) hele INT-module — C; G en T gelijk voor de hele categorie; +4.205 tekens = 7% van de kap"; "C's v1-bezwaar vervalt" | juist | Komt overeen met `aanvulling-c-v2` B3 en `verwerking-c-v1` RC-09 | Geen | — |
| SC-13 | §1 en K6 lemma-verwijzing: "B 'onvoldoende' / C v2 + A 'geen antecedent in de definitie' / alternatief lemma+kern" | juist voor C; onvolledig voor de breedte | D's N-D1 zegt hetzelfde ("De definitie mag niet afhankelijk zijn van een ongenoemde referent uit omliggende tekst"; "Een los `deze` wordt niet vanzelf duidelijk doordat boven het veld een lemma staat"). B's "onvoldoende" is dezelfde strekking. Nuttig onderscheid uit D-E13: lemma als genus ín de kern ("Document dat …") → INT-03 voldoet, CON-CIRC-001 apart; dat is iets anders dan lemma als enig antecedent buiten de kern | K6 herformuleren: "A/B/C/D: kern moet het antecedent dragen (lemma als genus in de kern is wél een antecedent); alternatief lemma+kern als één leesobject = ander contract, keuze Chris" | R |
| SC-14 | §2 "C-tabel koppelt fail aan vaststaande bedoeling: te bespreken in synthesecontrole" en §7 "fail-bij-ambiguïteit … C fail alleen bij vaststaande bedoeling" | onjuiste weergave als *standpunt*; juiste weergave van één tabelrij | De rij "Voldoet niet" in de C-v2 T-tabel bevat inderdaad "en de bedoelde referent staat vast". Maar C's register en tekst zijn niet zo gekoppeld: C-E15 "voldoet niet, referent onbekend"; C-E08 "voldoet niet of onvoldoende informatie"; Q2 "voldoet niet of nog te beoordelen". **C trekt de koppeling in** (B BC-08; D T-D1; A volgt B): aantoonbare dubbelzinnigheid is een tekstfout → *voldoet niet* met benoemde kandidaten; de informatievraag staat ernaast als herstelgrond. *Nog te beoordelen* alleen als de beoordelaar niet kan vaststellen óf de tekst dubbelzinnig is (semantische twijfel) of als de betekenisgrond ontbreekt (B-subtype). Het T-oordeel gaat over de tekst; de bedoeling gaat over H | §2: het C-voorbehoud schrappen; §7 "bewaarde verschillen": dit verschil schrappen — A/B/C/D zijn het eens | **M** |
| SC-15 | K1 sub-keuze "zelfstandig naamwoord" versus "antecedent in de definitie" | juist | A sluit zich aan (a-v2 §1); "herhaal het zelfstandig naamwoord" blijft alleen herstelvorm in G | Geen | — |
| SC-16 | K2 "T-a nu — A/B/C/D" met UI-voorwaarde r. 803-808 | juist | = C-v2 B2, RC-05 | Geen | — |
| SC-17 | K7 "n.v.t./voldoet alleen na inhoudelijke controle" | juist, sub-keuze ontbreekt | D kiest expliciet `pass` boven `not_applicable` (D-B02); B D4 noemt `not_applicable` alleen met "expliciete dekkingssemantiek"; C-tabel gebruikt "niet van toepassing". Het statuslabel bepaalt UI-tekst en telling | K7: sub-keuze statuslabel `pass` (D/B) versus `not_applicable` (C) opnemen | R |
| SC-18 | K9 legacy en §2 "productiedood maar testlevend" | juist | = RC-10-controle | Geen | — |

### 1.3 Betekenisverlies of te stellige rijen (normtekst, G, T, meldingen, casussen, dekking)

| # | Passage / sectie | Oordeel | Grond | Gevraagde correctie | M/R |
|---|---|---|---|---|---|
| SC-19 | §1 "Voorgestelde recordtekst … (exacte teksten: a-v2 §5.1, b-v2 §N/G, c-v2 G2 — inhoudelijk gelijk)"; `toelichting` alleen als parafrase | te stellig + ontbrekende besluittekst | De drie toelichtingen zijn niet gelijk: C voegt toe "plaatsing direct na een naamwoord is niet voldoende als een ander naamwoord ook als antecedent kan worden gelezen" en de uitzonderingen 'iedereen'/'wie-wat'; B voegt toe "meerdere naamwoorden bewijzen nog geen ambiguïteit: motiveer welke lezingen werkelijk plausibel zijn"; A voegt toe "bepaal eerst of een woord verwijzend gebruikt is". K1(a) kan alleen op één exacte tekst worden besloten | Eén exacte `toelichting` opnemen: A-v2 §5.1 als basis, aangevuld met de C-zin over plaatsing en de B-zin over plausibele lezingen; de andere twee als herkomst noemen | **M** |
| SC-20 | §1 `uitleg` en `toetsvraag` | juist | Exact gelijk aan a-v2 §5.1; `uitleg` gelijk aan c-v2 G2 | Geen | — |
| SC-21 | §3 G-tekst instruction_map | juist in kern; kleine weglating | "geen tussenliggend naamwoord …" (RA-06) ✓; "voorlopige kandidaat" ✓. Weggevallen t.o.v. C-G1/B-G-B1: "context, bron en toelichting vervangen geen ontbrekende verwijzing in de kern" en "behoud actor, rol, bezit en bereik". T-contract en T-B1 zeggen dat context niet repareert; G zegt het nu niet — G↔T-spiegel onvolledig | Eén zin toevoegen: "Context, bron en toelichting vervangen geen ontbrekende verwijzing; verander actor, rol, bezit of bereik niet." | R |
| SC-22 | §3 vervangtekst reference.md r. 185: "… zie Bijzinnen" | tegenspraak (feitelijk) | `definitie-nederlandse-definities/reference.md` heeft geen sectie "Bijzinnen"; de bijzin-aanbeveling staat in "## Grammaticaregels" (r. 146-172, bijzin r. 169-171); r. 185 valt onder "## Verboden Patronen" (r. 173). Exacte publicatietekst mag geen dode verwijzing bevatten | "zie Grammaticaregels" (C-v2 G4) | R (vóór publicatie) |
| SC-23 | §2 T-a "Zonder signaal: 'Geen verwijzend woord gesignaleerd; 'het', 'zijn', 'haar' en 'dat' worden niet of onvolledig gesignaleerd — beoordeel bij twijfel.'" | te stellig / inconsistent met K4(iii) | Als Chris K4(iii) kiest (patronen uitbreiden met het/dat/zijn/haar), is de zin onjuist. Een exacte meldingstekst die van een andere keuze afhangt, moet die afhankelijkheid tonen | Tekst afleiden uit de werkelijke patroonlijst (variabel) of twee varianten geven (K4 zonder/met (iii)) | R (vóór besluit) |
| SC-24 | §2 "Meldingsteksten per uitkomst: … aanvulling-c-v2 (6 rijen)" | te stellig als bron van exacte teksten | C's rij "Voldoet" bevat een onjuiste analyse ("'die' → gebeurtenis"; beide betrekkelijke 'die' verwijzen naar 'omstandigheden' — B BC-09) en de kandidatenlijst bij 'het' (omstandigheden/omgeving/gebeurtenis/basis) is niet gemotiveerd; §2 zegt zelf terecht "kandidaten … nooit regexuitkomst" | Verwijzing voorzien van "meldingen zijn voorbeeldoutput na analyse; C-rij 'Voldoet' gecorrigeerd in synthesecontrole-c §3" | R |
| SC-25 | §2 "correcte bijzinnen ('die') vuren wél"; §4 "foutpositief signaal (correcte bijzin)" | te stellig (terminologie) | "Foutpositief" impliceert een oordeel; signalen zijn geen oordeel (B BC-06, C-v2 Q6 al per geval). Passender: "ruissignaal" (niet-verwijzende of irrelevante treffer) en "detectiehiaat" (gemiste relevante vorm) | Terminologie in §2/§4 aanpassen | R |
| SC-26 | §5 kolom "Onderscheidende casus": alleen A-IDs plus enkele B/C; D ontbreekt; §-kop verwijst voor de mapping naar `review-c-op-a-v1` §2 (zonder D) | weglating | D heeft 18 gevallen met eigen IDs; de synthese bewijst met "D vier varianten" maar mapt ze niet | Mapping D overnemen uit §4 hieronder | R |
| SC-27 | §7 "Bewaarde verschillen: K3 (smal/breed), K6 lemma-scope, fail-bij-ambiguïteit …" | onjuiste weergave (na SC-13/SC-14) | K6 lemma-scope is geen verschil tussen onderzoekers meer (allen: de kern moet dragen; het alternatief lemma+kern blijft een keuze voor Chris, geen onderzoekersstandpunt); fail-bij-ambiguïteit vervalt (SC-14). Alleen K3 blijft een echt onderzoekersverschil | §7 herschrijven: één bewaard verschil (K3) en de open keuzes zonder onderzoekersverschil apart noemen | **M** |
| SC-28 | §1 uitzondering "loos 'het' en onbepaalde/ingesloten vormen vragen geen antecedent" | juist | B S9 + D W1–W4; C secundair | Geen | — |
| SC-29 | §7 dekkingstabel (1)–(14) | juist | Alle onderdelen traceerbaar naar §1–§6; C-v2 dekkingstabel dekt hetzelfde | Geen | — |

### 1.4 Aansluiting G↔T en herstel zonder betekenisverlies

| # | Passage / sectie | Oordeel | Grond | Gevraagde correctie | M/R |
|---|---|---|---|---|---|
| SC-30 | §3 G "… lever dan één voorlopige kandidaat en laat de vraag bij de beoordeling" | weglating (overdracht G→T niet gedefinieerd) | B BC-14 en G-B2: wat mag een voorlopige kandidaat bevatten? Zonder definitie kan het model een verzonnen referent invullen of een vraag in het definitieveld zetten. Eenduidige lezing: de kandidaat bevat geen verzonnen referent en geen vraagtekst; de onduidelijkheid blijft in de tekst zichtbaar, zodat T haar als *voldoet niet* of *nog te beoordelen* met precies één vraag toont; de route is T + reviewer, niet een generatie-UI-dialoog | In §3 één zin toevoegen: "Een voorlopige kandidaat bevat geen verzonnen referent en geen vraag; de onduidelijkheid blijft zichtbaar en wordt door T met één vraag gemeld." | **M** |
| SC-31 | Normgelijkheid G↔T | juist | G ("antecedent in de definitie", "eenduidig", "verwijzend woord") en T-contract/T-a ("naar welk antecedent verwijst zij; zijn er meer kandidaten") gebruiken dezelfde norm; K1-toelichting idem | Geen | — |
| SC-32 | §4 H | juist, kleine weglatingen | Diagnose, één kandidaat, beschermde kenmerken (incl. B's lijst), stops incl. context-/bronwissel ✓. Ontbreekt: stop "herhaling van dezelfde fout" (B H-B1) en de activeringsvoorwaarde van de ene poging ("na afzonderlijk gebruikersverzoek", B BC-17) | Twee zinsdelen toevoegen | R |
| SC-33 | §4 "Integrale hertoets … (INT-01, INT-04, CON-CIRC-001, ARAI-06, SAM-02, ESS-05)" | juist | = C-v2 H + B ESS-05 | Geen | — |

### 1.5 Bewijskracht effectevaluatie (winst én verslechtering vaststelbaar?)

| # | Passage / sectie | Oordeel | Grond | Gevraagde correctie | M/R |
|---|---|---|---|---|---|
| SC-34 | §6 per variant | gedeeltelijk | G: winst (minder onduidelijke referenten) én verslechtering (drie onaanvaardbare uitkomsten) gedefinieerd ✓. H: betekenisbehoud door mens ✓. T-c: "geen foutieve afkeur van goede bijzinnen" ✓. K4(iii): "dekking-én-ruismeting" (§1) ✓. **T-a: "kwaliteit/tijd/onderbouwing van menselijke oordelen" zonder maat** — verslechtering (langzamer, meer onterechte afkeur door misleidende passage, onnodig herstel) is niet meetbaar zoals geformuleerd; B en D noemen de maten: juistheid tegen referentieoordeel, navolgbare motivering, onterechte afkeur, onnodig herstel, tijd alleen indien werkelijk gemeten, gebalanceerde volgorde oude/nieuwe hulp | Maten voor T-a toevoegen | **M** |
| SC-35 | §6 ontbrekende beslisregel | weglating | Wanneer is winst "vastgesteld"? B: "daadwerkelijk betere juiste uitkomsten én behoud van goede gevallen"; D: "bij gelijke uitkomsten geen winst aangetoond; bij regressie herstellen of aanbeveling herzien". De beschermde gevallen (nooit *voldoet niet*: A-E01/E06/E10, B-E01/E05/E06/E10/E11/E16, C-E02/E05/E06/E12/`clear_relative`/`explicit_repeat`, D-E01/E06/E07/E15/E16) staan in de vier registers maar niet in de synthese | Beslisregel + op inhoud gemapte lijst beschermde gevallen opnemen; zonder die regel kan de evaluatie niets "vaststellen" | **M** |
| SC-36 | §6 "≥6 nieuwe gevallen" | juist, keuze open | D: 12 (4 helder, 4 onhelder, 2 grensgevallen, 2 ontbrekende/strijdige invoer); C: tien; B: ≥6 | Bereik noemen of D's verdeling kiezen; eigenaar ✓ | R |
| SC-37 | §6 "Nulmeting: proefuitkomsten a/b/c/d" | juist | Vier nulmetingen op 26f2374d, alle exit 0 | Geen (mapping: SC-26) | — |

### 1.6 Resterende feitelijke tegenspraken

| # | Passage / sectie | Oordeel | Grond | Gevraagde correctie | M/R |
|---|---|---|---|---|---|
| SC-38 | §3 "INT-01.json keurt 'die'/'waarbij'/'welke' af"; regelnummers r. 466–471, r. 378, r. 803–808/859–864; cijfers 4.205/2.461/607/3.196 | juist | Door C gelezen/gemeten (`INT-01.json`; `prompt_orchestrator.py`; `validation_view.py`; `proefuitkomsten-c-v2.json`) | Geen | — |
| SC-39 | §2 "'zijn/haar/dat/hem' vuren niet" | te stellig (bewijssoort) | 'hem' is door niemand gemeten; statisch waar (staat niet in de patroonlijst) | "(gemeten: zijn/haar/dat; statisch: hem)" | R |
| SC-40 | §3 "(kopieën ~/.claude/skills en ~/.agents/skills identiek); de Cowork-kopieën … apart synchroniseren" | te stellig | Identiek: bevestigd door B en D (hashvergelijking). De Cowork-kopieën van de twee definitie-skills zijn door niemand gehasht (A-manifest v2 noemt alleen de Cowork-kopie van `toetsregel-onderzoek`, 94206774…) | "Cowork-kopieën niet gecontroleerd; vóór publicatie hashen" | R |
| SC-41 | Kop "wederzijdse reviews A↔B, A↔C, B↔C en de verwerkingen (verwerking-a/b/c-v1)" | juist, met procesfeit | C heeft `review-b-op-c-v1.md` (10:17) pas bij deze synthesecontrole gelezen; `aanvulling-c-v2.md` (10:32) verwerkt BC-01…BC-19 dus niet. De synthese suggereert niet het tegendeel, maar de lezer kan het aannemen. C verwerkt de BC-punten in §3 hieronder | Voetnoot: "C verwerkte B's review in synthesecontrole-c-v1 §3" | R |
| SC-42 | §1 "Alle vier onderzoekers stellen onafhankelijk vast …" | juist | D las A/B/C niet; A/B/C-v1 waren onafhankelijk | Geen | — |
| SC-43 | Kop "(let op: C-E01 = ASTRA-fout, A/B-E01 = ASTRA-goed)" | juist, onvolledig | D-E01 = ASTRA-goed, D-E02 = ASTRA-fout (= A/B) | "A/B/D-E01 = ASTRA-goed" | R |

## 2. Standpunt C na de synthese (expliciet, geen consensusdruk)

- **K3:** C blijft bij (a) hele INT-module altijd. Grond ongewijzigd: de toets draait alle INT-regels altijd; G en T horen voor de hele categorie gelijk te lopen; omvang is geen argument (4.205 tekens). A, B en D kiezen (b) als eerste stap. Dit is het enige echte onderzoekersverschil dat overblijft; de synthese geeft het juist weer.
- **K6 lemma-verwijzing:** C v2-standpunt ongewijzigd ("geen antecedent in de definitie → voldoet niet; herstel via genusherformulering zonder lemma"); A, B en D zeggen hetzelfde; het alternatief lemma+kern is een keuze voor Chris, geen onderzoekersstandpunt (SC-13/SC-27).
- **Fail bij ambiguïteit terwijl de herstelbedoeling onbekend is:** C trekt de koppeling in de T-tabelrij in (SC-14). Standpunt C = A/B/D: tekstfout → *voldoet niet* met kandidaten; informatievraag ernaast; *nog te beoordelen* alleen bij semantische twijfel of ontbrekende betekenisgrond.
- **K1, K2, K4, K5, K7, K8, K9:** zoals in de synthese; C-voorkeuren juist weergegeven.

## 3. Errata van C op eigen v1/v2 (naar aanleiding van `review-b-op-c-v1.md`, pas nu gelezen; bestaande bestanden blijven ongewijzigd)

| # | BC-punt | Erratum C | Gevolg voor de synthese |
|---|---|---|---|
| E-C1 | BC-08 | Koppeling "voldoet niet alleen bij vaststaande bedoeling" (C-v2 T-tabel rij 2, en "nog te beoordelen"-rij) ingetrokken; zie SC-14 | §2/§7 aanpassen |
| E-C2 | BC-09 | Meldingsvoorbeeld "INT-03 — Voldoet: 'die' → gebeurtenis; 'die gebeurtenis' → gebeurtenis" (c-v1/c-v2 T-tabel) is onjuist: beide betrekkelijke 'die' → 'omstandigheden'; alleen het aanwijzende 'die gebeurtenis' → 'gebeurtenis'. De kandidatenlijst bij 'het' (C-E01) moet gemotiveerd zijn: 'geheel' en 'gebeurtenis' zijn grammaticaal onzijdige kandidaten; 'omstandigheden'/'omgeving'/'basis' niet zonder motivering | C-tabel niet als exacte publicatietekst gebruiken (SC-24) |
| E-C3 | BC-10 | Casusregister-c-v1 kolom "T1a verwacht" ("passages 'die' ×3", "'die', 'die'") is onjuist bij hergebruik van `_reden_met_passages` (deduplicatie): één unieke passage per fragmenttekst | SC-06 |
| E-C4 | BC-06 | "Nul onderscheidend vermogen" en "foutpositieve signalen" (c-v1 Q4/Q6) → "de evaluator berekent geen semantisch onderscheid; ruissignalen (niet-verwijzende/irrelevante treffers) en detectiehiaten per geval"; de telling is in v2 al per geval | SC-25 |
| E-C5 | BC-07 | "Alles review, uitkomsten worden niet onderscheiden" (c-v1/c-v2 T-alinea) geldt voor normaal afgeronde evaluaties; de service-foutgrens `not_evaluated`/`error` bestaat (r. 1430-1483) | SC-11 |
| E-C6 | BC-12 | "compact/`include_examples_in_rules=False` verwijdert het ASTRA-paar" is alleen via `include_examples=False` in de moduleproef (P03) bewezen, niet via een compacte adaptervariant | Geen (synthese claimt dit niet) |
| E-C7 | BC-14 | C-G1 "voorlopige kandidaat": definitie zoals SC-30; niet-verwijzende vormen zijn in C-v2 G2-toelichting opgenomen, in G1 niet — akkoord met B dat G1 daar één zinsdeel over mag bevatten | SC-30 |
| E-C8 | BC-04 | C-E11 ("voorschrift dat bepaalt hoe deze regel wordt toegepast", lemma *regel*) bevat het lemma letterlijk en is daarom geen zuiver "lemma als enig antecedent"-geval; het zuivere geval is B-E09 ("verzoek waarbij deze schriftelijk wordt ingediend", lemma *aanvraag*) | K6-casus: B-E09 i.p.v. C-E11 noemen |
| E-C9 | BC-02 | Veldscope (toelichting/voorbeelden met zinsgrens, C-E16) is een voorgestelde toepassing, geen ASTRA-voorschrift; de synthese zet dit terecht onder K1/K8 | Geen |
| E-C10 | BC-16 | C-v2 "blokkeert vaststellen/export niet (in lijn met ESS-03-besluit) tenzij Chris anders beslist" is een regelspecifieke vrijstelling die niet uit ESS-03 volgt; K8-formulering van de synthese (keuze binnen het gedeelde DEF-630-contract) is juist en C sluit zich daarbij aan | Geen |
| E-C11 | BC-13 | Al verwerkt in c-v2 (RC-06/RC-09): cijfers en intrekking van het architectuurbezwaar | Geen |

## 4. Mapping van de D-gevallen (aanvulling op `review-c-op-a-v1.md` §2)

| Inhoud | D | A / B / C (uit §2 review-c-op-a) |
|---|---|---|
| ASTRA JUIST(ER) | D-E01 | A-E01 / B-E01 / C-E02 |
| ASTRA ONJUIST | D-E02 | A-E02 / B-E02 / C-E01 |
| "regeling waarbij deze afspraak geldt" (fixture, lemma in tekst) | D-E03 | A-E03 / B-E03 / C-E03 |
| 'het' als enig voornaamwoord | D-E04 ("Verslag over een besluit nadat het is vastgesteld"; lemma *verslag* in tekst) | A-E04 / B-E04 / C-E04 |
| geen voornaamwoord | D-E05 | A-E05 / B-E05 / C-E05 |
| "Persoon die een aanvraag indient." | D-E06 | A-E06 (variant) / B-E16 / `clear_relative` |
| "Teken dat een richting aangeeft." | D-E07 | A-E10 / B-E06 / P |
| bezittelijk, twee kandidaten ("… zijn vertegenwoordiger … zijn besluit") | D-E08 | `possessive_ambiguity`; A-E08 / B-E07 / C-E08 (varianten) |
| lege tekst | D-E09 (uitgevoerd) | A-E12 (ontwerp) / B-E14 / C-E10 / `empty` |
| 'in het kader' (ruissignaal) | D-E10 (uitgevoerd) | C-E06 |
| twee kandidaten vóór de bijzin | D-E11 ("Persoon met een aanvrager die …", ontwerp) | `two_candidates` |
| vooruitverwijzing | D-E12 (ontwerp) | B-E08 / C-E09 |
| lemma als genus in de kern ('dat' → Document) | D-E13 (ontwerp) | — (nieuw onderscheid; zie SC-13) |
| meerdere verwijzingen ('haar', 'het') in één zin | D-E14 (ontwerp) | — |
| voornaamwoordelijk bijwoord 'waarmee' | D-E15 (ontwerp) | — (K6 reikwijdte) |
| voegwoord 'dat' + loos 'het' ("Waarneming dat het regent") | D-E16 (ontwerp) | A-E11 / B-E10 / C-E12 (loos 'het') |
| technische fout | D-E17 (ontwerp) | B-E18 |
| bron-/bedoelingsconflict | D-E18 (ontwerp) | B-E15 |

## 5. Samenvatting en oordeel

- **Materieel (synthese-v2 nodig):** SC-06 (T-a: deduplicatie en per-voorkomen als ontwerp), SC-07 (bewijsbinding van de synthese-invoer), SC-14 en SC-27 (fail-bij-ambiguïteit is geen verschil; K6 lemma is geen onderzoekersverschil; alleen K3 blijft), SC-19 (één exacte `toelichting`), SC-30 (definitie "voorlopige kandidaat" als G→T-overdracht), SC-34 en SC-35 (maten voor T-a; beslisregel en beschermde gevallen).
- **Redactioneel maar vóór besluit/publicatie te corrigeren:** SC-22 ("zie Bijzinnen" → Grammaticaregels), SC-23 (T-a-tekst afhankelijk van K4), SC-10 (erratum feitenbasis), SC-02/SC-03/SC-26/SC-43 (D-getal, D-gevallen, D-mapping).
- **Weglatingen:** geen materieel C-punt ontbreekt; alle C-punten die niet zijn overgenomen (T-tabelrij-koppeling; "breekt modulestructuur") zijn herkenbaar en terecht niet overgenomen.
- **Standpuntweergave:** K3 en K6 juist; fail-bij-ambiguïteit was een correcte weergave van één tabelrij maar niet van C's standpunt, dat C nu expliciet gelijkschakelt met A/B/D.
- **G↔T en herstel:** normgelijk; de overdracht bij onbekende referent (SC-30) en de deduplicatie (SC-06) ontbreken; H is volledig op twee zinsdelen na.
- **Effectevaluatie:** kan winst en verslechtering vaststellen voor G, H, T-c en K4; voor T-a pas na toevoeging van maten; en alleen met een beslisregel en een lijst beschermde gevallen (SC-34/SC-35).
- **Feitelijke tegenspraken:** twee kleine (SC-10 functienaam in de feitenbasis; SC-22 sectienaam), verder geen.

Opgeleverd: `synthesecontrole-c-v1.md` (dit bestand) en `bewijsmanifest-c-v3.json`. Geen bestaand bestand gewijzigd; geen implementatie, commits, issues of andere sessies.

Bronnen: `gedeeld/synthese-v1.md` (`0065ec61…`); `onderzoek-a/aanvulling-a-v2.md`, `verwerking-a-v1.md`, `bewijsmanifest-a-v2.json`; `onderzoek-b/aanvulling-b-v2.md`, `review-b-op-c-v1.md`, `verwerking-b-v1.md`; `onderzoek-d/aanvulling-d-v1.md`, `casusregister-d-v2.md`; eigen `aanvulling-c-v2.md`, `casusregister-c-v1.md`, `review-c-op-a-v1.md`, `proefuitkomsten-c-v2.json`; code op `26f2374d`: `src/services/validation/modular_validation_service.py` r. 1413-1427 (en r. 1430-1483 via B), `src/toetsregels/regels/INT-01.json`, `gedeeld/feitenbasis-v1.md` r. 46; `_claude-global-setup/skills/definitie-nederlandse-definities/reference.md` (koppen r. 146, 173). Hashes: `bewijsmanifest-c-v3.json`.
