# Aanvulling onderzoeker C — INT-03 (Voornaamwoord-verwijzing duidelijk) — 25 september 2026 (v2)

Onderzoeker C: Claude Code CLI, headless, model `claude-fable-5-1`, effort `xhigh`. Dit is het volledig herziene advies na de wederzijdse review (fase 2). `aanvulling-c-v1.md` (sha256 `31f3a532…`) blijft ongewijzigd staan; de verschillen staan in §"Wijzigingen ten opzichte van v1" en zijn per punt herleid in `verwerking-c-v1.md`. Dit is een onderzoek en besluitvoorstel; niets is geïmplementeerd, geen issue of commit aangemaakt.

## Wijzigingen ten opzichte van v1

| # | Wijziging | Herkomst |
|---|---|---|
| W1 | Uitzondering 1 en alle G-teksten (G1–G4): "betrekkelijke bijzin direct na zijn antecedent" → "betrekkelijke bijzin waarvan het antecedent eenduidig is (geen tussenliggend naamwoord dat als antecedent kan worden gelezen)" | RC-08 (A); eigen geval `two_candidates` |
| W2 | Uitzondering 2 (expletief 'het'): "niet geverifieerd" → "secundair onderbouwd via B S9 (Taaladvies/Onze Taal, door B gelezen; door C niet zelf gelezen)" | RC-15; WebFetch in deze sessie niet toegestaan |
| W3 | Uitzondering 5 (verwijzing naar het lemma) en B6: standpunt gewijzigd naar "voldoet niet — geen antecedent in de definitie", tenzij Chris lemma+kern als één leesobject kiest | review-c-op-b RB-C-04 (CON-CIRC-001 toetst alleen het letterlijke lemma; inconsistentie met eigen `external_reference`-oordeel) |
| W4 | Uitzonderingen 8 ('iedereen') en 9 ('wie/wat' met ingesloten antecedent) toegevoegd | B S9 |
| W5 | Q3: STR-04-relatie toegevoegd; INT-01-rij met B's buurstatusmeting; CON-CIRC-001-rij met de grens van de letterlijke controle | A Q3; B-proef |
| W6 | Q4 "Genereren": aanvullende meting `proef-c-v2` (INT-module 4.205 / 2.461 tekens, INT-03-blok 607, SAM 3.196); B3-cijfer "+~10K" gecorrigeerd naar +4.205 (INT) resp. +7.401 (INT+SAM); bezwaar "optie (b) breekt de modulestructuur" ingetrokken (DEF-743-patroon) | RC-06, RC-09; eigen proef |
| W7 | Q4 "legacy": `validators/INT_03.py` wordt door de unit-suite via `json_validator_loader.py` uitgevoerd (productiedood, testlevend); `regels/INT-03.py` is de dode kopie; `definitie_validator.py`-claim met exacte grep-uitkomst; B7 herformuleerd | RC-10, RC-12; gerichte broncontrole |
| W8 | G1 ingekort tot instructielengte; uitleg naar G2/G3; twee zinnen uit B's G-B1 (context/bron/toelichting buiten de kern; actor/rol/bezit/bereik niet wijzigen) verkort opgenomen | RC-07; RB-C-13 |
| W9 | G2 `toetsvraag` aangevuld met B's onderscheid "onduidelijkheid ≠ ontbrekende beoordeling of ontbrekende herstelgrond"; foute voorbeelden lemmavrij gehouden | RB-C-12; RB-05 |
| W10 | T1a noemt de UI-uitbreiding (`validation_view.py` r. 803-808) expliciet als voorwaarde; verwijzing naar B's meldingentabel als superset | RC-05; RB-C-15 |
| W11 | H: te beschermen betekeniskenmerken (actor, rol, bezit, reikwijdte, bronbeperkingen, recordidentiteit) en "bewaar origineel, voorstel en verschil" toegevoegd | RB-C-18 |
| W12 | Q6 nulmeting per geval i.p.v. telling; holdout door onafhankelijke deskundige vooraf vastgelegd | RC-14; B Q6 |
| W13 | Casusregister-errata (C-E03 vervuild door lemma; E07/E11 lezen per W3; uitzondering-1-formulering) en ID-mapping A/B/C | RB-05; review-c-op-a §2 |

## 0. Toegang en leesbasis

- Leesbasis: commit `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3` op branch `onderzoek/DEF-772-INT-03-20260925`; `git status --porcelain src config tests` is leeg vóór en na de proeven (geen codewijzigingen). INT-03.json sha256 `9c917925…`, gelijk aan `source_sha256` in het historische `uitkomsten.json` (11-09): het regelrecord is sinds d68a98a9 ongewijzigd; de validatieketen wél (DEF-750/766/767).
- Skills: `~/.agents/skills/` en `~/.claude/skills/` zijn vanuit deze sessie niet leesbaar (werkmapbeperking). Gebruikt is `~/Projecten/_claude-global-setup/skills/`; hashes conform de feitenbasis (`toetsregel-onderzoek/SKILL.md` `66d65b3f…`, `definitie-toetsregels/SKILL.md` `21b4157c…`, `reference.md` `f3252105…`). B bevestigt hashgelijkheid met `~/.agents/skills`.
- Niet gelezen: Ross DBT §4.3 (ook A en B niet); Onze Taal/Taaladvies (alleen B; C's poging via WebFetch is in deze sessie niet toegestaan). Claims daarover zijn "secundair via B" gemarkeerd.
- Fase 2: na opslag van v1 zijn `onderzoek-a/` (aanvulling, reviews, proefbestanden, manifest) en `onderzoek-b/` (aanvulling, casusregister, proefbestanden, manifest) volledig gelezen; hashes in `bewijsmanifest-c-v2.json`.
- Eigen proeven: `proef-c-v1.py` (v1; route A 30 rijen, route B 7 rijen, exit 0) en `proef-c-v2.py` (fase 2; moduleomvang INT/SAM, exit 0), beide onder de DEF-519-offline-gate, zonder modelcalls, productiegegevens of brede testsuite.

## Q1 — Norm: wat waarborgt ASTRA, wat is lokaal, wanneer geldt de regel, welke uitzonderingen

**Bronfeit (ASTRA, letterlijk).** Regel: "Voor ieder voornaamwoord binnen een definitie dient duidelijk te zijn *waarnaar* verwezen wordt." Toelichting: voornaamwoorden "(zoals 'hij', 'het', 'zij', 'die', 'dit', 'dat') verwijzen naar 'dingen' …; in de definitie moet duidelijk zijn welk ding dat betreft." Voorbeeld bij *context*: ONJUIST "… waardoor **het** volledig kan worden begrepen …", JUIST(ER) "… waardoor **die gebeurtenis** volledig kan worden begrepen …" (tweemaal betrekkelijk 'die', eenmaal aanwijzend 'die gebeurtenis'). Brondocument DBT 4.3; prioriteit hoog; aanbeveling verplicht; geldigheid "alle"; status definitief; type "term".

**Wat de norm waarborgt (interpretatie, gedeeld met A en B).** Een *lezerscriterium over referentie*: elke verwijzing moet voor de lezer op precies één ding in de definitie slaan. De norm verbiedt voornaamwoorden niet, eist geen afstand ("dezelfde zin"), geen positie ("direct voorafgaand") en geen woordsoort van het antecedent (een naamwoordgroep of, zelden, een hele propositie kan antecedent zijn — B N-B1; A houdt "zelfstandig naamwoord" aan, sub-keuze bij B1). Omdat "duidelijk voor de lezer" een oordeel is, is de norm niet met een woordenlijst te beslissen.

**Lokale toevoegingen in `src/toetsregels/regels/INT-03.json` (implementatie, geen normbewijs).**

| Veld | Lokaal | Verhouding tot ASTRA |
|---|---|---|
| `uitleg` | "Definities mogen geen voornaamwoorden bevatten waarvan niet direct duidelijk is waarnaar verwezen wordt." | Negatief geherformuleerd; "direct" is een toevoeging; inhoudelijk gelijk. |
| `toelichting` | "… altijd **in dezelfde zin of zinsdeel** … welk **zelfstandig naamwoord** bedoeld is …" | Verscherping zonder ASTRA-grond: (a) "zinsdeel" als nabijheidseis, (b) velden met meer zinnen (toelichting, voorbeelden; E16), (c) "zelfstandig naamwoord" sluit naamwoordgroep/propositie uit. Wordt in de prompt **niet** gerenderd (`_format_rule` r. 228-281); bereikt het model alleen via "in dezelfde zin" in `instruction_map`. |
| `toetsvraag` | "Bevat de definitie voornaamwoorden zoals 'deze', 'dit', 'die'? Zo ja: …" | Versmalt tot aanwijzende voornaamwoorden; het ASTRA-voorbeeld gaat over 'het'. |
| `herkenbaar_patronen` (10) | deze, dit, die, daarvan, daarbij, waarvan, waarmee, "inzienelijk maken" (verschrijving), waarbij, "in het kader" | Eigen toevoeging. Vier voornaamwoordelijke bijwoorden; twee geen verwijzing ('in het kader' is ARAI-05/ESS-01-materie; ARAI-05 dekt het INT-03-gat overigens niet: B-proef ARAI-05 `pass` op alle gevallen). Ontbreken: het, hij, zij, dat, hem, haar, hun, zijn, diens, ervan, hiervan, daarmee, hetgeen, welke. |
| extra patroon (`src/validation/additional_patterns.py` r. 36-38) | `\b(deze\|dit\|die\|daarvan)\b(?!\s+(begrip\|definitie\|regel))` | Uitzondering is **dood**: het recordpatroon `\bdeze\b` vuurt toch (C-E07, A-E09). |
| `type` / `geldigheid` / `brondocument` | "interne structuur" / "gehele definitie" / "ASTRA" | ASTRA: "term" / "alle" / DBT 4.3. Cosmetische drift (DEF-625). |
| `runtime_contract` | judgment_review, review_required, excluded_from_score, example_pair_policy review_policy (DEF-624) | Reviewplichtig omdat "het patroon ook op het eigen goede voorbeeld vuurt" — bevestigd door A, B en C op 26f2374d. |

**Toepasselijkheid.** Dezelfde norm geldt voor gegenereerde, bewerkte, geïmporteerde en aangeleverde definitietekst, bij toetsen, review, conceptopslag, vaststelling en export; uitsluitend toetsen wijzigt de tekst niet. Primair object is de definitiezin (de "kern", B); voor toelichting, voorbeelden en tegenvoorbeelden geldt de norm ook, maar daar mag een antecedent over een zinsgrens lopen (ASTRA: "in de definitie"; C-E16; besluitpunt B1). Het lemma, de context, bronnen en de toelichting maken geen deel uit van de kern en kunnen een ontbrekend antecedent niet leveren (Q2).

**Uitzonderingen — onderbouwd of open.**

1. *Betrekkelijke bijzin waarvan het antecedent eenduidig is* ("persoon **die** een aanvraag indient", "teken **dat** een richting aangeeft"): voldoet. Onderbouwd door het ASTRA-JUIST-voorbeeld, `definitie-nederlandse-definities/reference.md` r. 169-171 en `STR-04.json` (`goede_voorbeelden` "proces dat beslissers informeert"). Plaatsing direct na een naamwoord is **niet** voldoende: in "Persoon met een vertegenwoordiger **die** een aanvraag indient" (`two_candidates`) staat 'die' direct na 'vertegenwoordiger' en kan toch op 'persoon' slaan (RC-08). Twee naamwoorden vóór de bijzin maken de bijzin niet automatisch dubbelzinnig; de hele zin en de functie bepalen de lezing (B). Geen afkeurgrond; als signaal hooguit laag.
2. *Voorlopig of expletief 'het'/'er'* ("het is toegestaan", "periode waarin het regent", "er wordt getoetst"): geen verwijzing, dus niet van toepassing. Secundair onderbouwd via B S9 (Taaladvies: loos onderwerp; door B gelezen 25-09); door C niet zelf gelezen. A-E11, B-E10 en C-E12 verwachten alle "n.v.t.".
3. *Bezittelijke voornaamwoorden* (zijn/haar/hun/diens): vallen onder "ieder voornaamwoord"; geen uitzondering; nu ongedekt (C-E08, A-E08, B-E07, `possessive_ambiguity`). 'diens' kan juist eenduidig zijn (B-E17).
4. *Vooruitverwijzing binnen de definitie* ("zodra deze gereed is, wordt de aanvraag verzonden"): ASTRA sluit het niet uit. **Open (B6)**; gezamenlijk voorstel A/B/C: toegestaan als eenduidig, geen zelfstandige afkeurgrond, wel generatie-stijlvoorkeur "antecedent eerst".
5. *Verwijzing naar het gedefinieerde begrip zelf* ("… deze regel …" bij lemma *regel*; "verzoek waarbij deze … wordt ingediend" bij lemma *aanvraag*): **gewijzigd standpunt (W3).** Het enige antecedent staat buiten de definitietekst; onder ASTRA ("binnen een definitie … waarnaar") heeft het voornaamwoord dus geen antecedent in de definitie → *voldoet niet*, met herstel door genusherformulering zonder het lemma (zoals bij `external_reference`). Grond: `CON-CIRC-001.json` toetst alleen het *letterlijke* begrip ("mag het begrip zelf niet letterlijk bevatten"), zodat een voornaamwoordelijke cirkel bij de v1-splitsing (INT-03 duidelijk, CON-CIRC beslist) onbeoordeeld zou blijven; en de definitie moet zelfstandig leesbaar zijn (Q2). Alternatief voor Chris (B6): lemma+kern als één leesobject — dan voldoet de verwijzing, maar dat is een ander lees- en exportcontract (B) en A's "grensgeval/INT-06" wordt dan het passende oordeel. Drie standpunten expliciet; geen consensusdruk.
6. *Voornaamwoordelijke bijwoorden* (daarvan, waarmee, waarbij): verwijzen wél; onder de norm; als betrekkelijk bijwoord met eenduidig antecedent geldt uitzondering 1.
7. *'in het kader', 'inzienelijk maken'*: geen verwijzing; uit de INT-03-lijst (C-E06).
8. *Onbepaald voornaamwoord* ('iedereen', 'niemand'): duidt een bereik aan, heeft geen antecedent; geen afkeurgrond (B-E11; B S9, door C niet zelf gelezen).
9. *Ingesloten antecedent* ('wie …', 'wat …'): het antecedent zit in het voornaamwoord zelf; geen afkeurgrond (B S9, idem).

**Stijlvoorkeur versus afkeurgrond.** "Herhaal liever het zelfstandig naamwoord" (legacy hints) en "Vermijden: deze, dit, die, dat" (`definitie-nederlandse-definities/reference.md` r. 185) zijn generatiestijl; de enige afkeurgrond is een verwijzing zonder eenduidig antecedent in de definitie. Een bestaande definitie wordt niet afgekeurd omdat zij een voornaamwoord bevat; een signaal is geen afkeuring en geen signaal is geen goedkeuring (B).

## Q2 — Noodzakelijke en ondersteunende invoer; veldmatrix

Noodzakelijk is uitsluitend de te toetsen tekst (`required_inputs: [definition_text]`), gebonden aan een tekstversie/hash (B-bewijscontract). De term is ondersteunend (uitzondering 5, afgrenzing van CON-CIRC-001). Context, ontologie en toelichting maken een bedoelde referent plausibeler maar mogen een structureel ambigue zin niet "duidelijk" verklaren: de definitie moet zelfstandig leesbaar blijven. Ontbrekende tekst is geen INT-03-uitkomst maar een ontbrekend toetsobject (VAL-EMP-001; nu levert de app toch `review_required`: C-E10, B-E14). Tegenstrijdige informatie (toelichting noemt referent A, de zin leest als B) is *voldoet niet* of *nog te beoordelen*; nooit een stille herschrijving. AI mag geen antecedent, toelichting of bron verzinnen.

| Veld | Zelf toetsobject en criterium | Bewijs voor ander oordeel | Invoer bij generatie | Mag AI dit opleveren/wijzigen? | Herkomst; ontbrekend/conflicterend |
|---|---|---|---|---|---|
| Definitiezin (kern) | Ja: elke verwijzing eenduidig naar één antecedent in de zin | — | Uitvoer | Voorstel; herstel alleen op verzoek, betekenis gelijk | Ontbreekt → VAL-EMP-001, geen INT-03-oordeel; tekstversie binden |
| Context (org./jur./wet.) | Nee | Kan een kandidaat plausibeler maken; bewijst geen eenduidigheid | Ondersteunend; bepaalt nu of de INT-instructie in de prompt staat (Q4) | Nee (CON-01-contract) | Ontbreekt → norm geldt onverkort; AI mag geen context aannemen |
| Definitiebronnen | Nee | Bronpassage kan de oorspronkelijke referent tonen | Ondersteunend (CON-02) | Nee | Conflict bron/zin → nog te beoordelen; bron niet herschrijven |
| Ontologierelaties | Nee | Rolrelatie maakt een kandidaat waarschijnlijker; geen grammaticaal bewijs | Ondersteunend | Categorie is een te controleren claim (ESS-02) | Geen automatische referentkeuze uit een categorie |
| Voorbeelden / praktijkvoorbeelden | Ja, zelfde criterium; antecedent mag over zinsgrens (B1) | Tonen de bedoelde actor | Niet nodig | Voorstel, gelabeld synthetisch | Gegenereerd voorbeeld is geen bevestiging van de zin |
| Tegenvoorbeelden | Ja, zelfde criterium | Alternatieve referent zichtbaar maken | Niet nodig | Voorstel | idem |
| Grensgevallen | Ja, zelfde criterium | Meerdere kandidaten benoemen | Niet nodig | Voorstel | idem |
| Synoniemen | Nee (termlabels) | Kunnen lezing beïnvloeden (SAM-06/08) | Niet nodig | n.v.t. | — |
| Homoniemen | Nee | Kunnen een kandidaat ambigu maken | Niet nodig | n.v.t. | — |
| Toelichting | Ja, zelfde criterium, antecedent mag over zinsgrens | Kan de bedoelde referent vastleggen als reviewerbewijs; repareert de zin niet | Ondersteunend | Voorstel, apart van de kern | Conflict toelichting/zin → voldoet niet of nog te beoordelen |
| Term/lemma, registratiesleutel | Nee; levert géén antecedent voor de kern (uitzondering 5) | Nodig voor CON-CIRC-001 | Verplicht | Nee | Term ≠ conceptidentiteit ≠ sleutel |

## Q3 — Relaties met andere regels: conflict of overlap, wie beslist

| Regel | Relatie | Aard | Wie beslist |
|---|---|---|---|
| INT-01 (één zin; `generic`, scored) | `INT-01.json` `herkenbaar_patronen` bevat `\bdie\b`, `\bwaarbij\b`, `\bwelke\b` en de komma; een INT-03-conforme bijzin en het INT-03-herstel via herhaling krijgen van INT-01 een fail. **Gemeten** door B: INT-01 `fail` op B-E01 (ASTRA-goed), B-E02 en B-E03; door A bevestigd (RB-04). | **Conflict bij generatie én herstel** | INT-01-dossier (DEF-770); INT-03-herstel moet het INT-01-signaal tonen, niet stil kiezen. |
| STR-04 (kick-off met toespitsing) | De betrekkelijke bijzin is dé toespitsingsvorm (`STR-04.json` goed voorbeeld "proces dat beslissers informeert"; patroon r. 9 keurt juist een kick-off mét 'die' zónder vervolg af). | Overlap; INT-03 mag de bijzin niet ontmoedigen | STR-04 ongewijzigd; G1 noemt de bijzin als toegestaan. |
| INT-04 (lidwoordverwijzing) | Herhaling van het zelfstandig naamwoord ("de persoon") kan INT-04 raken. | Overlap | INT-04-dossier; hertoetsen na INT-03-herstel. |
| ARAI-05 / INT-10 (impliciete aannames) | 'in het kader' zit in de INT-03-lijst maar is ARAI-05-materie; antecedent buiten de definitie raakt ook INT-10. ARAI-05 keurt de INT-03-gevallen niet af (B-proef: `pass` op alle acht) — geen vangnet. | Overlap door verkeerd geplaatst patroon | Patroon uit INT-03 (B4); ARAI-05 ongewijzigd. |
| CON-CIRC-001 (lemma niet letterlijk in de zin) | Herstel "deze regel" → "regel" bij lemma *regel* schendt CON-CIRC-001 (B-proef: `fail` op B-E03/E04, door constructie van die gevallen). De regel toetst **alleen het letterlijke lemma** (`uitleg`, evaluator `generic`), dus een voornaamwoordelijke cirkel (uitzondering 5) vangt hij niet — INT-03 moet dat doen. | **Conflict bij herstel; gat bij voornaamwoordelijke cirkel** | Chris (B5/B6): herstel via herformulering zonder lemma. |
| SAM-02 (geen herhaling in kwalificatie) | Herhaling bij samengestelde begrippen kan SAM-02 raken. | Mogelijke overlap, niet onderzocht | SAM-02-dossier. |
| ESS-01 | 'zodat', 'waardoor … begrepen' zijn doelsignalen; los van INT-03. | Overlap in dezelfde zinnen | ESS-01 ongewijzigd. |
| INT-06 (geen toelichting in de definitie) | "dit houdt in" is primair INT-06 (A; `INT-06.json` door C niet gelezen). | Overlap, niet geverifieerd | INT-06-dossier. |
| CON-02 / ESS-03 (AI-beoordeling, DEF-743/766) | Procedureel sjabloon voor optie T2. | Werkvorm | ADR-001: per regel apart besluit (B2). |
| ESS-04 (DEF-767) | `_reden_met_passages` is het sjabloon voor T1a. | Werkvorm | B2. |

## Q4 — Bewezen appgedrag per ingang; ontbrekende bewijzen

**Toetsen (service, manager- én cachepad; proef route A, 15 gevallen × 2 routes, exitstatus 0; bevestigd door A met 10 gevallen en B met 8, B met buurstatussen).**
- Elke tekst, ook zonder voornaamwoord (E05) en de lege tekst (E10), levert `review_required`; `validation_status` = `validated`; nooit een violation. Reden = letterlijk de toetsvraag; signalen = de vurende regexstrings (`judgment_review.py` r. 65-78, 195-216) — geen passages, geen kandidaten. Geen regelspecifieke tak voor INT-03 (alleen ESS-01/02/04); geen lege-tekst-tak.
- De signalen onderscheiden het ASTRA-paar niet (C-E01 = C-E02; A-E01 = A-E02; B-E01 = B-E02): `\bdie\b` + extra patroon; 'het' (E01, E04), bezittelijk 'haar'/'zijn' (E08, `possessive_ambiguity`, A-E08, B-E07) en betrekkelijk 'dat' (P, A-E10, B-E06) geven **geen** signaal; 'in het kader' geeft een niet-voornaamwoordsignaal (E06); de uitzondering in het extra patroon is dood (E07, A-E09). De zes historische gevallen (11-09) leveren op 26f2374d dezelfde uitkomsten.
- **ID-mapping:** het ASTRA-paar heet bij A en B E01 (goed)/E02 (fout) en bij C E01 (fout)/E02 (goed); de volledige mapping van alle A/B/C-gevallen staat in `review-c-op-a-v1.md` §2. De synthese moet op inhoud mappen.
- Bewezen: de signaalhulp heeft nul onderscheidend vermogen voor de norm; de reviewplicht is de enige inhoudelijke werking.

**Genereren (proef route B; aanvullend `proef-c-v2`).**
- Het live INT-03-blok is exact: kop, `uitleg`, "**Instructie:** Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent in dezelfde zin", ✅/❌ ASTRA-paar (P01; byte-gelijk aan A's en B's meting). De `toelichting` wordt **niet** gerenderd. Zonder voorbeelden (P03) verdwijnt het ASTRA-paar.
- **Het INT-blok staat alleen in de prompt bij juridische of wettelijke context** (P06/P07 aanwezig; P04 zonder context en P05 met alleen organisatorische context: `integrity_rules` en `sam_rules` overgeslagen). Oorzaak: `prompt_orchestrator._get_active_modules` r. 466-471 (het `if` op r. 467; DEF-123). Bevestigd door A (moduleselectie) en B (drie varianten). Gevolg: zonder juridische/wettelijke context ontvangt het model **geen enkele** INT-instructie (INT-01 t/m INT-10) terwijl de toets alle INT-regels draait.
- Omvang (proef-c-v1): 25.925 tekens (geen context), 28.500 (organisatorisch), 35.907 (juridisch), 35.931 (wettelijk); kap 60.000. Omvang per module (`proef-c-v2`, dezelfde `JSONBasedRulesModule`-instanties als de adapter registreert, begrip "context"): INT-module **4.205** tekens met voorbeelden (9 regels), **2.461** zonder; INT-03-blok alleen **607**; SAM-module **3.196** (8 regels); INT+SAM 7.401 ≈ het P05→P06-verschil (7.407; rest: scheidingstekens r. 364 en contexttekst). B's absolute lengtes liggen ≈ 1,7K lager (andere begrip-/contextteksten; delta's gelijk op ±40 tekens).
- Legacy (gerichte broncontrole fase 2): `IntegrityRulesModule` (hardcoded INT-03-tekst) wordt niet geregistreerd in `modular_prompt_adapter.py` r. 70-148; alleen geëxporteerd (`modules/__init__.py`) en geïnstantieerd in `tests/unit/services/prompts/test_def171_optimization.py` r. 75, 99 → dode promptmodule. `ToetsregelManager` laadt uitsluitend `*.json` (`manager.py` r. 161, 306, 383). Daarnaast bestaat `src/toetsregels/json_validator_loader.py`, dat `validators/INT_03.py` dynamisch laadt (r. 150-173; `regels_dir.parent / "validators"`, r. 157): in `src/` heeft die loader alleen een commentaarregel als verwijzing (`evaluators/__init__.py` r. 5), maar de **testsuite gebruikt hem** (`tests/unit/validation/test_json_validators.py` r. 67-90 voert álle validators uit, dus ook INT_03; verder `test_working_system.py`, `test_con01_duplicate_count.py`, `test_json_validator_loader_paths.py` (DEF-733), `tests/integration/regression/test_regression_suite.py`, `performance/test_performance_comprehensive.py`; `scripts/detect_orphan_modules.py` r. 39/77 documenteert "alleen door tests" en "dynamisch via importlib"). `validators/INT_03.py` is dus **productiedood maar testlevend**; `regels/INT-03.py` (byte-identiek, sha256 `3e4b15ea…`) heeft geen loader en is de dode kopie. `src/validation/definitie_validator.py` (INT-03-mapping r. 180, 230, 598): grep over `src/`, `tests/`, `scripts/` → geen consument behalve de modulenaam-string in `tests/integration/regression/test_regression_suite.py` r. 314 (import-rooktest). De vier `get_generation_hints` bereiken de prompt niet.

**UI en vervolg (statisch gelezen, niet uitgevoerd; door A en B bevestigd).**
- `validation_view.py`: INT-03 verschijnt uitsluitend als code in "🟠 Nog te beoordelen: INT-03, …" (`_statuslijst_regels` r. 237-263; weergave r. 859-864 met `continue`, zonder expander). Alleen ESS-01/02/04 krijgen hun reden als tekst (r. 803-808). `signals` komt in `src/ui` niet voor. De reviewer ziet noch toetsvraag noch passages.
- Expertreview (`expert_review_tab.py` r. 1601-1654, 1769 e.v.): één besluit per definitie; per-regelbeoordeling alleen voor CON-01, CON-02, ESS-03. **Geen reviewbesluit per INT-03 of per signaal** (gedeeld ketendefect DEF-626/627).
- Transport: `service_factory.py` r. 297-312 laat `review_required` meereizen; `definition_edit_service.py` r. 302-319 herbindt alleen ESS-03. Export: `export_txt.py` r. 14 label "nog te beoordelen". Opslag in `validation_issues`: niet geverifieerd.

**Ontbrekende bewijzen.** Geen Streamlit-run; geen opslag-/herlaadproef; geen exportinhoud; import- en vaststel-/exportpoort (DEF-630) niet onderzocht; geen modelproef; Ross DBT §4.3 door niemand gelezen; taalbronnen alleen door B.

## Q5 — Aanbevolen regeltekst, appgedrag/meldingen en skill-/promptvervangingen

### G — generatie-instructie (exacte vervangende tekst met vindplaats)

Probleem met de huidige instructie (`json_based_rules_module.py` r. 378): (1) noemt alleen 'deze', 'dit', 'die'; (2) "in dezelfde zin" is lokaal (B1); (3) zegt niet dat een eenduidige bijzin goed is, zodat het model correcte bijzinnen kan gaan mijden (en INT-01 dat beloont); (4) geen herstelvorm, geen betekenisgrens; (5) bereikt het model alleen bij juridische/wettelijke context (B3).

**G1 — `instruction_map["INT-03"]` (r. 378), voorstel (één instructieregel):**

> Laat elk verwijzend woord ('het', 'hij', 'zij', 'deze', 'dit', 'die', 'dat', 'zijn', 'haar', 'hun', 'daarvan', 'waarmee') eenduidig naar precies één antecedent in de definitie verwijzen; een betrekkelijke bijzin met eenduidig antecedent ('persoon die een aanvraag indient') is goed. Bij meer kandidaten of een antecedent buiten de definitie: herhaal het bedoelde naamwoord of herformuleer, zonder het begrip zelf op te nemen, zonder actor, rol, bezit of bereik te veranderen en zonder een antecedent te verzinnen; context, bron en toelichting vervangen geen ontbrekende verwijzing. Blijkt de bedoelde referent niet, lever dan één voorlopige kandidaat en laat de vraag bij de beoordeling.

**G2 — `INT-03.json`:** `uitleg` → "Voor ieder voornaamwoord in de definitie is voor de lezer duidelijk waarnaar het verwijst." `toelichting` → "Voornaamwoorden en voornaamwoordelijke bijwoorden ('het', 'deze', 'die', 'dat', 'zijn', 'haar', 'diens', 'daarvan' …) verwijzen naar een antecedent dat in de definitie zelf staat en eenduidig is; het lemma, de context en de toelichting leveren geen antecedent. Een betrekkelijke bijzin waarvan het antecedent eenduidig is, voldoet; plaatsing direct na een naamwoord is daarvoor niet voldoende als een ander naamwoord ook als antecedent kan worden gelezen. Niet-verwijzend 'het' ('het is toegestaan'), onbepaalde voornaamwoorden ('iedereen') en 'wie/wat' met ingesloten antecedent vragen geen antecedent. Meerdere naamwoorden bewijzen nog geen dubbelzinnigheid. Gebruikelijke herstelvormen: herhaling van het bedoelde naamwoord of herformulering, met behoud van betekenis en zonder het lemma." (de zinsnede "dezelfde zin of zinsdeel" vervalt; B1). `toetsvraag` → "Bevat de definitie een voornaamwoord of voornaamwoordelijk bijwoord? Zo ja: is voor de lezer eenduidig welk antecedent in de definitie bedoeld is? Benoem de passage en de plausibele kandidaten en onderscheid onduidelijkheid van een ontbrekende beoordeling of een ontbrekende herstelgrond." `goede_voorbeelden` aanvullen met "Persoon die een aanvraag indient." en "Teken dat een richting aangeeft."; `foute_voorbeelden` met "Persoon met een vertegenwoordiger die een aanvraag indient.", "Verplichting van de werkgever om de werknemer over haar rechten te informeren." en "Handeling van een medewerker aan een collega zodat het kan worden voortgezet." (alle lemmavrij; synthetisch, geen ASTRA-citaat). `brondocument` → "ASTRA (Ross, DBT 4.3)". `example_pair_policy` blijft `review_policy` zolang T0/T1a geldt.

**G3 — `definitie-toetsregels/reference.md` r. 64:** "| INT-03 | Duidelijke voornaamwoord-verwijzing | **hoog** | Laat elk voornaamwoord ('het', 'deze', 'die', 'dat', 'zijn', 'haar' …) eenduidig naar één antecedent in de definitie verwijzen; een betrekkelijke bijzin met eenduidig antecedent is goed; herhaal anders het naamwoord of herformuleer zonder betekenisverandering en zonder het lemma |". `SKILL.md`: korte INT-03-alinea naar het voorbeeld van ESS-04 (norm, G, T, geen cijfer, geen poort): "INT-03 krijgt geen cijfer; uitkomst per verwijzing: voldoet / voldoet niet (kandidaten) / niet van toepassing / nog te beoordelen (één vraag); een signaal is geen afkeuring en geen signaal is geen goedkeuring; een eenduidige betrekkelijke bijzin is geen overtreding; herstel alleen op verzoek, zonder het lemma in te voegen; skilladvies is geen opgeslagen menselijke beoordeling."

**G4 — `definitie-nederlandse-definities/reference.md` r. 185:** "- Verwijzingen zonder eenduidig antecedent in de definitie: `het`, `deze`, `dit`, `die`, `dat`, `zijn`, `haar`, `daarvan` enz. (INT-03); een betrekkelijke bijzin waarvan het antecedent eenduidig is (`persoon die …`) is correct, zie Grammaticaregels; niet-verwijzend `het` vraagt geen antecedent".

**G5 — transport (B3):** `prompt_orchestrator._get_active_modules` r. 466-471: `integrity_rules` onafhankelijk van context activeren (SAM apart beslissen). Alternatief (b): module altijd activeren en binnen `JSONBasedRulesModule` alleen INT-03 contextvrij tonen naar het DEF-743-patroon (`_CONTEXTVRIJE_REGELS`, r. 472-476) — technisch haalbaar zonder de modulestructuur te breken (correctie op v1). Vooraf te controleren door de app: INT-blok aanwezig (metadata `skipped_modules`/`rules_skipped`), tekst niet leeg.

### T — toetsinstructie en appgedrag

**Wat het mechanisme nu doet (bewezen):** altijd `review_required`; reden = toetsvraag; signalen = patroonstrings; geen passages; UI toont alleen de code. *Overtreding*, *ontbrekend bewijs*, *beoordeling nodig* en *technische fout* worden niet onderscheiden.

**Wat het zou moeten opleveren (contract, ongeacht optie):**

| Uitkomst | Wanneer | Meldingstekst (voorstel) |
|---|---|---|
| Voldoet | elke verwijzing heeft één antecedent in de definitie, of er is na inhoudelijke controle geen verwijzend woord | "INT-03 — Voldoet: 'die' → gebeurtenis; 'die gebeurtenis' → gebeurtenis." |
| Voldoet niet | een verwijzing zonder antecedent in de definitie of met meer kandidaten, en de bedoelde referent staat vast | "INT-03 — Voldoet niet: 'het' heeft geen eenduidig antecedent; kandidaten: omstandigheden, omgeving, gebeurtenis, basis. Herstel: noem het bedoelde antecedent, bijvoorbeeld 'die gebeurtenis'." |
| Niet van toepassing | geen verwijzend woord (alleen na inhoudelijke controle; een lege regexlijst volstaat niet — B D4) | "INT-03 — Niet van toepassing: de definitie bevat geen verwijzend voornaamwoord." |
| Nog te beoordelen (onvoldoende informatie) | meer kandidaten en de bedoeling blijkt niet uit tekst, toelichting of bron; precies één vraag | "INT-03 — Nog te beoordelen: 'haar' kan naar de werkgever of de werknemer verwijzen. Vraag: wiens rechten zijn bedoeld?" |
| Niet beoordeeld (ontbrekend toetsobject) | lege tekst | `not_evaluated` "vereiste invoer ontbreekt: definition_text" (zoals ESS-03) |
| Technische fout | beoordeling niet uitgevoerd | "INT-03 — Technisch probleem: beoordeling niet uitgevoerd; geen oordeel." |

B's meldingentabel (T-B1) is een superset met de subtypes "overtreding + ontbrekende herstelgrond" en "betekenisgrond ontbreekt"; de synthese kan die overnemen. Uitsluitend toetsen wijzigt de tekst niet; een negatieve uitkomst blokkeert vaststellen/export niet (in lijn met ESS-03-besluit 21-09) tenzij Chris anders beslist; geen cijfer.

**Opties.**
- **T0 — huidig behouden.** Geen kosten; nul onderscheidend vermogen; reviewer ziet niets. Niet aanbevolen.
- **T1a — menselijk oordeel met verbeterde signaalhulp** (patroon ESS-04 `_reden_met_passages`): reden = "INT-03 — Nog te beoordelen. Te beoordelen verwijzing: '{passage}'. Naar welk antecedent verwijst zij; zijn er meer kandidaten? Dit signaal geeft nog geen oordeel."; zonder passage: "Geen verwijzend woord gesignaleerd; 'het', 'zijn' en 'haar' worden niet gesignaleerd — beoordeel bij twijfel." Patroonlijst opschonen (B4). **Voorwaarde:** UI-uitbreiding `validation_view.py` r. 803-808 (reden en passages voor INT-03 tonen), anders blijft de hulp onzichtbaar (RC-05). Kandidaat-antecedenten zijn zonder zinsontleding niet betrouwbaar; een parser (**T1b**) is een nieuwe afhankelijkheid en wordt afgeraden.
- **T2 — AI-beoordeling zoals ESS-03/CON-02.** Nieuwe evaluator + async dienst + domeincontract: vier uitkomsten + fout, citaatcontrole (verwijzing en kandidaten letterlijk in de tekst), vingerafdruk over term, tekst, contextlijsten, toelichting; binding aan promptversie/normhash/provider/model; niet-blokkerend, geen cijfer; bij *onvoldoende informatie* precies één vraag. Kosten: één modelaanroep per validatie, goldset (de registers A/B/C), ADR-001-besluit, privacy (definitietekst naar het model, zoals bij ESS-03).

Aanbeveling C: **T1a nu** en **T2 als afzonderlijk besluit** na evaluatie van de ESS-03-ervaring; T0 en T1b niet. A (T-a nu, T-c apart) en B (optie 2, AI apart) adviseren gelijkluidend; het blijft besluit B2.

### H — begrensde terugkoppeling en herstel

Diagnose vóór herstel: (a) werkelijke generatieovertreding (C-E01-vorm); (b) instructie-/transportverlies: het INT-blok stond niet in de prompt (P04/P05) — de keten is fout, niet de generator; (c) foutpositieve signaalhulp (C-E02, C-E06, `clear_relative`); (d) ontbrekend bewijs: verwijzing zonder signaal (C-E04, C-E08); (e) technische storing.

Herstelvormen (alleen op verzoek, nooit automatisch; DEF-638, CON-01-lijn): (1) vervang het ambigue voornaamwoord door het bedoelde naamwoord met passend bepaald/aanwijzend woord ('die gebeurtenis'); (2) herformuleer tot een betrekkelijke bijzin met eenduidig antecedent; (3) bij lemma-verwijzing: genusherformulering zonder het lemma. Beschermd: betekenis, actor, rol, bezit, reikwijdte, bronbeperkingen, brongetrouwheid, noodzakelijke namen (CON-01), recordidentiteit, gebruikersinvoer (lijst naar B H-B1). Bewaar origineel, voorstel en verschil. Stop: referent onbekend (C-E15), herstel zou het lemma invoegen (CON-CIRC-001, C-E11), herstel raakt INT-01 ('die', 'waarbij') of INT-04 zonder dat de gebruiker dat ziet (C-E14), betekenis verandert, foutpositieve evaluator (C-E02), bron-/bedoelingsconflict (B-E15), context- of bronwissel na het herstelvoorstel. Poginglimiet: één automatische kandidaat, daarna mens. Hertoetsing van de gewijzigde tekst plus INT-01, INT-04, CON-CIRC-001, ARAI-06, SAM-02; oude oordelen over gewijzigde tekst gelden niet. Gebruiker ontvangt: toetsresultaat per uitkomst, conceptstatus, of expertbeoordeling en vaststelling nog open staan.

## Q6 — Beoogde kwaliteitswinst, vergelijking vóór/na, risico's, besluiten

**Nulmeting (dit onderzoek, per geval; geen percentage).** T0: alle 15 C-gevallen (en alle A- en B-gevallen) `review_required`; het ASTRA-paar (C-E01/E02) krijgt identieke signalen; werkelijke overtredingen zónder enig signaal: C-E04 ('het'), C-E08 ('haar'); overtredingen met een signaal dat niet naar het probleemwoord wijst: C-E01 ('het' onzichtbaar, 'die' gesignaleerd), `possessive_ambiguity` ('zijn' onzichtbaar, 'die' gesignaleerd); foutpositieve signalen op correcte zinnen: C-E02, C-E06 ('in het kader'), `clear_relative`, `explicit_repeat` ('waarbij'); de reviewer ziet de code zonder reden of passage. G: INT-instructie afwezig zonder juridische/wettelijke context.

**Beoogde verbetering en criteria (vooraf).**
- G: minder eerste-poging-definities met een verwijzing zonder eenduidig antecedent, met name 'het' en bezittelijke vormen; behoud: eenduidige bijzinnen blijven toegestaan, geen lemma-invoeging, geen betekenisverandering, geen langere zinnen door overbodige herhaling. Onaanvaardbaar (verslechtering): het model vermijdt alle voornaamwoorden en levert stroeve herhalingen, of verzint antecedenten.
- T: C-E01, C-E04, C-E08, `two_candidates`, `possessive_ambiguity`, `external_reference`, C-E11 moeten *voldoet niet* of *nog te beoordelen met vraag* worden; C-E02, C-E05, C-E06, C-E12, `clear_relative`, `explicit_repeat` mogen nooit *voldoet niet* worden; C-E10 wordt *niet beoordeeld*. Motivering citeert de verwijzing en, bij T2, de kandidaten letterlijk. Meer groene uitkomsten zijn geen winst; terecht *nog te beoordelen* met een goede vraag wel.
- H: betekenisbehoud in alle voorgestelde herstellingen, beoordeeld door een mens tegen bron/bedoeling; geen buurregelovertreding zonder melding.

**Vergelijking vóór/na (ontwerp).** Zelfde invoer, betekenis en verwachtingen: de registers A, B en C (op inhoud gemapt), plus minimaal zes tot tien niet voor het ontwerp gebruikte definities, vóór de evaluatie vastgelegd door een onafhankelijke deskundige (B) en afgeschermd voor A, B en C (die elkaars registers inmiddels kennen). Varianten: oude vs. nieuwe instructie (G1) bij aanwezig INT-blok; keten zonder vs. met INT-blok (G5); T0 vs. T1a vs. T2. Model, bronnen en instellingen gelijk; ≥ 3 herhaalde runs. Beoordeling blind voor variant, tegen de vooraf vastgelegde normverwachting; de nieuwe evaluator is niet de enige maatstaf voor zichzelf. Rapportage: verbeterd / gelijk / verslechterd / onbeslist per geval, met aantallen en steekproefgrens; geen generalisatie.

**Nu nog niet uitvoerbaar.** (1) Generatieproef met live model: niet geautoriseerd; eigenaar uitvoerder DEF-772 na besluit B2/B3. (2) T1a/T2-uitkomsten: pas na implementatie. (3) Reviewerproef: eigenaar Chris na T1a. Status na implementatie zonder dit bewijs: *geïmplementeerd; kwaliteitswinst nog niet vastgesteld*.

**Risico's en bewijsgaten.** Volgorde: eerst G5 (INT-blok altijd), dan pas een strengere T. Een opgeschoonde patroonlijst met 'het'/'zijn'/'haar'/'dat' geeft veel foutpositieve passages (lidwoord, werkwoord, voegwoord); alleen als hulp met passage, nooit als afkeur. T2 stuurt definitietekst naar een model. INT-01 blijft de bijzin bestraffen zolang dat dossier niet is besloten.

## Besluitpunten voor Chris

| # | Keuze | Opties en gevolgen | Voorkeur C |
|---|---|---|---|
| B1 | Normreikwijdte | (a) ASTRA-tekst: antecedent "in de definitie", eenduidig; "dezelfde zin/zinsdeel" vervalt als eis; sub-keuze: antecedent = "zelfstandig naamwoord" (A) of ruimer "antecedent in de definitie" (B/C). (b) Lokale verscherping handhaven (keurt E16 af, sluit propositie-antecedenten uit). | (a), ruime lezing |
| B2 | Toetsmechanisme | T0 / T1a passagehulp + reden zichtbaar (vereist UI r. 803-808) / T1b parser / T2 AI-beoordeling (ADR-001, kosten, privacy). Sub-keuze D4 (B): "niet van toepassing" alleen na inhoudelijke controle. | T1a nu, T2 apart; niet T1b |
| B3 | INT-instructies in elke prompt | (a) `integrity_rules` altijd activeren: +4.205 tekens (INT, met voorbeelden; +7.401 met SAM), onder de kap; geldt voor INT-01…INT-10, die de toets nu al altijd draait. (b) alleen INT-03 contextvrij via het DEF-743-patroon: +607 tekens; haalbaar zonder breuk. (c) laten: G en T blijven uiteenlopen. Verschil (a)/(b) is beleid, geen omvang. A en B kiezen (b). | (a): G en T gelijk laten lopen voor de hele categorie |
| B4 | Patroonlijst | (a) opschonen tot verwijzende woorden, 'in het kader' en 'inzienelijk maken' eruit, extra patroon verwijderen (dood; één plek = het record), 'het/dat/zijn/haar/hun/diens' als laag-precisiesignaal met passage; (b) ongewijzigd. | (a), alleen als signaal |
| B5 | Herstelbeleid | (a) alleen op verzoek, één kandidaat, stopregels als in H; (b) automatisch herstel na fail (afgeraden). | (a) |
| B6 | Uitzonderingen | vooruitverwijzing: toegestaan mits eenduidig? · lemma-verwijzing: voldoet niet (geen antecedent in de definitie; C v2, B) / grensgeval-INT-06 (A) / lemma+kern als één leesobject (ander contract)? · expletief 'het', 'iedereen', 'wie/wat': n.v.t.? | ja / voldoet niet / ja (secundair via B) |
| B7 | Opruimen legacy | `IntegrityRulesModule` (dode promptmodule, alleen test_def171), `regels/INT-03.py` (dode kopie), `validators/INT_03.py` (productiedood, door de unit-suite via `json_validator_loader` uitgevoerd — opruimen raakt `test_json_validators`, `test_working_system` e.a.), INT-03-mapping in `definitie_validator.py` (geen consument; modulenaam in import-rooktest). Tech-debt buiten deze regel (DEF-507-lijn). | tracken; niet in DEF-772 |

Wat bestaand beleid herstelt: B3 (DEF-126/171 bedoelden instructies voor alle regels), B4-opschoning, T1a (DEF-624/767-lijn). Wat een nieuw normbesluit vraagt: B1, B2-T2, B6.

## Casusregister-errata (op `casusregister-c-v1.md`, dat ongewijzigd blijft)

- C-E03 ("regeling: regeling waarbij deze afspraak geldt"): bevat het lemma; CON-CIRC-001 faalt door de constructie (B-meting op het tekstidentieke B-E03). Opvolger voor de synthese/goldset: "voorschrift waarbij deze afspraak geldt" (term *regeling*), zelfde INT-03-verwachting.
- C-E07 ("bepaling waarin deze regel wordt uitgelegd", term *toelichting*) en C-E11 (lemma *regel*): kolom "norm" leest per W3 als *voldoet niet* (geen antecedent in de definitie), tenzij Chris bij B6 het lemma als leesobject kiest.
- Uitzondering-1-formulering in de kolommen G/H ("bijzin direct na het antecedent") leest als "bijzin waarvan het antecedent eenduidig is" (W1).
- ID-mapping met A en B: `review-c-op-a-v1.md` §2.

## Dekkingstabel

| Onderdeel | Waar |
|---|---|
| (1) doel/betekenis, (2) norm/besluiten, (3) toepasselijkheid | Q1 |
| (4) context, (5) bronnen, (6) ontologie, (7) aanvullingen | Q2 veldmatrix |
| (8) appgedrag, (10) status/score/poorten | Q4, T |
| (9) skills/prompts | Q5 G1–G5 |
| (11) proeven | proef-c-v1/-v2 met verwachtingen/uitkomsten; casusregister A/C; mapping A/B/C |
| (12) samenhang | Q3 |
| (13) verbeteringen/review | Q5, besluitpunten, review-c-op-a/-b, verwerking-c |
| (14) acceptatie/overdracht | Q6, casusregister B, hieronder |

## Opgeleverd, ontbrekend, volgende overdracht

Opgeleverd in `onderzoek-c/` (fase 1, ongewijzigd): `aanvulling-c-v1.md`, `casusregister-c-v1.md`, `proefverwachtingen-c-v1.json`, `proef-c-v1.py`, `proefuitkomsten-c-v1.json`, `proef-c-v1-run1.log`, `bewijsmanifest-c-v1.json`. Fase 2: `review-c-op-a-v1.md`, `review-c-op-b-v1.md`, `verwerking-c-v1.md`, `aanvulling-c-v2.md` (dit bestand), `proefverwachtingen-c-v2.json`, `proef-c-v2.py`, `proefuitkomsten-c-v2.json`, `proef-c-v2-run1.log` (extra uitvoerlog), `bewijsmanifest-c-v2.json`. Ontbrekend: UI-, opslag-, export- en modelproeven; Ross DBT §4.3; taalbronnen niet zelf gelezen. Volgende overdracht: naar A voor verwerking van de reviews van B en C en voor de synthese; C voert daarna de synthesecontrole uit. Geen gezamenlijke afronding geclaimd.

## Bronnen

- ASTRA: `gedeeld/astra-INT-03-raw-20260925.txt` (`121c4fbb…`); feitenbasis `gedeeld/feitenbasis-v1.md` (`c160479a…`); startopdracht en reviewopdracht C.
- Onderzoeken A en B: `onderzoek-a/aanvulling-a-v1.md` (`3b3bc4e5…`), `review-a-op-b-v1.md`, `review-a-op-c-v1.md`, `proefverwachtingen-a-v1.json`, `proef-a-v1.py`, `proefuitkomsten-a-v1.json`, `bewijsmanifest-a-v1.json`; `onderzoek-b/aanvulling-b-v1.md` (`d791e7f7…`), `casusregister-b-v1.md`, `proefverwachtingen-b-v1.json`, `proef-b-v1.py`, `proefuitkomsten-b-v1.json`, `bewijsmanifest-b-v1.json` (hashes in `bewijsmanifest-c-v2.json`).
- Historisch: `docs/analyses/def606-regeldossiers/INT-03-v1.md`, `INT-03-bewijs-v1/`; `2026-09-07-definitiekwaliteit-dossiers-int-sam.md` r. 127-156.
- Code (26f2374d): `src/toetsregels/regels/INT-03.json`, `INT-01.json`, `STR-04.json`, `CON-CIRC-001.json`, `ARAI-05.json`; `src/toetsregels/manager.py` r. 161, 306, 383; `src/toetsregels/json_validator_loader.py` r. 99-110, 150-173, 245-261; `src/services/validation/evaluators/judgment_review.py`; `evaluators/__init__.py` r. 5; `src/validation/additional_patterns.py` r. 36-38; `src/validation/definitie_validator.py`; `src/services/validation/modular_validation_service.py`; `src/services/validation/interfaces.py` r. 267-278; `src/services/prompts/modules/json_based_rules_module.py` r. 130-200, 228-281, 378; `prompt_orchestrator.py` r. 364, 403-476; `modular_prompt_adapter.py` r. 52-158; `integrity_rules_module.py`; `src/ui/components/validation_view.py` r. 237-263, 795-880; `expert_review_tab.py`; `src/services/service_factory.py` r. 297-312; `src/services/definition_edit_service.py` r. 255-319; `src/export/export_txt.py` r. 14; `tests/unit/validation/test_json_validators.py` r. 67-90; `tests/unit/validation/test_json_validator_loader_paths.py`; `tests/unit/test_working_system.py`; `tests/unit/validation/test_con01_duplicate_count.py`; `tests/integration/regression/test_regression_suite.py` r. 301-326, 866-1473; `tests/integration/performance/test_performance_comprehensive.py`; `tests/unit/services/prompts/test_def171_optimization.py` r. 15, 75, 99; `scripts/detect_orphan_modules.py` r. 39, 77; `tests/fixtures/toetsregels/runtime_cases.yaml`.
- Skills (`_claude-global-setup/skills/`): `toetsregel-onderzoek/SKILL.md` + references; `definitie-toetsregels/SKILL.md` (secties r. 60-78, 95), `reference.md` r. 64; `definitie-nederlandse-definities/reference.md` r. 169-171, 181-188.
- Eigen proeven: `proef-c-v1.py` → `proefuitkomsten-c-v1.json` (exit 0); `proef-c-v2.py` → `proefuitkomsten-c-v2.json` (exit 0); beide met vooraf vastgelegde verwachtingen.
