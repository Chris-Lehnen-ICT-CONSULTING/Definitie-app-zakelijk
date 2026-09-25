# Aanvulling onderzoeker C — INT-03 (Voornaamwoord-verwijzing duidelijk) — 25 september 2026 (v1)

Onderzoeker C: Claude Code CLI, headless, model `claude-fable-5-1`, effort `xhigh`. Onafhankelijke eerste versie: vóór opslag zijn geen bestanden uit `onderzoek-a/`, `onderzoek-b/` of de afgebroken run `onderzoek-c/run1-opus55-afgebroken/` gelezen; de sessielogs `claude-run2.*` in `onderzoek-c/` zijn de hostlogs van deze sessie en zijn evenmin gelezen. Dit is een onderzoek en besluitvoorstel; niets is geïmplementeerd, geen issue of commit aangemaakt.

## 0. Toegang en leesbasis

- Leesbasis: commit `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3` op branch `onderzoek/DEF-772-INT-03-20260925`; `git status --porcelain src config tests` is leeg (geen codewijzigingen in de werkboom). INT-03.json heeft sha256 `9c917925…`, gelijk aan `source_sha256` in het historische `uitkomsten.json` (11-09): het regelrecord is sinds d68a98a9 ongewijzigd; de validatieketen wél (DEF-750/766/767, zie `git log` op `judgment_review.py`).
- Skills: `~/.agents/skills/` en `~/.claude/skills/` zijn vanuit deze sessie **niet leesbaar** (werkmapbeperking van de CLI-sessie). Gebruikt is de aangewezen bron van waarheid `~/Projecten/_claude-global-setup/skills/`; de hashes komen overeen met de feitenbasis: `toetsregel-onderzoek/SKILL.md` `66d65b3f…` (de Mac-versie met Q6 en effectevaluatie), `definitie-toetsregels/SKILL.md` `21b4157c…`, `definitie-toetsregels/reference.md` `f3252105…`. De Cowork-kopieën (`94206774…`) zijn niet gelezen.
- Niet gelezen: Ross, *How to define business terms in plain English* (DBT) §4.3 en de Onze Taal-pagina over voornaamwoorden. Claims daarover zijn hieronder als *niet geverifieerd* gemarkeerd. De ASTRA-pagina is gelezen uit `gedeeld/astra-INT-03-raw-20260925.txt` (sha256 `121c4fbb…`).
- Gelezen bronbestanden met hashes staan in `bewijsmanifest-c-v1.json`.

## Q1 — Norm: wat waarborgt ASTRA, wat is lokaal, wanneer geldt de regel, welke uitzonderingen

**Bronfeit (ASTRA, letterlijk).** Regel: "Voor ieder voornaamwoord binnen een definitie dient duidelijk te zijn *waarnaar* verwezen wordt." Toelichting: voornaamwoorden "(zoals ‘hij’, ‘het’, ‘zij’, ‘die’, ‘dit’, ‘dat’) verwijzen naar ‘dingen’ …; in de definitie moet duidelijk zijn welk ding dat betreft." Voorbeeld bij *context*: ONJUIST "… waardoor **het** volledig kan worden begrepen …", JUIST(ER) "… waardoor **die gebeurtenis** volledig kan worden begrepen …". Brondocument DBT 4.3; prioriteit hoog; aanbeveling verplicht; geldigheid "alle"; status definitief; type "term".

**Wat de norm waarborgt (interpretatie).** Het criterium is een *lezerscriterium over referentie*: elke verwijzing moet voor de lezer op precies één ding in de definitie slaan. De norm verbiedt voornaamwoorden niet (het eigen JUIST-voorbeeld bevat tweemaal het betrekkelijke 'die'), eist geen bepaalde afstand ("dezelfde zin") en eist geen bepaalde woordsoort van het antecedent. Omdat "duidelijk voor de lezer" een oordeel is, is de norm niet met een woordenlijst te beslissen; dat is een normfeit, geen implementatiekeuze.

**Lokale toevoegingen in `src/toetsregels/regels/INT-03.json` (implementatie, geen normbewijs).**

| Veld | Lokaal | Verhouding tot ASTRA |
|---|---|---|
| `uitleg` | "Definities mogen geen voornaamwoorden bevatten waarvan niet direct duidelijk is waarnaar verwezen wordt." | Negatief geherformuleerd; "direct" is een toevoeging; inhoudelijk gelijk. |
| `toelichting` | "… altijd **in dezelfde zin of zinsdeel** … welk **zelfstandig naamwoord** bedoeld is …" | Verscherping. Voor een definitie van één zin (INT-01) valt "dezelfde zin" samen met "in de definitie"; ze wordt materieel bij (a) "zinsdeel" als nabijheidseis, (b) velden met meer zinnen (toelichting, voorbeelden), (c) "zelfstandig naamwoord": sluit een naamwoordgroep of een hele propositie als antecedent uit ('dat' verwijzend naar een handeling). Geen ASTRA-grond. |
| `toetsvraag` | "Bevat de definitie voornaamwoorden zoals 'deze', 'dit', 'die'? Zo ja: …" | Versmalt de aandacht tot aanwijzende voornaamwoorden; het ASTRA-voorbeeld gaat juist over 'het'. |
| `herkenbaar_patronen` (10) | deze, dit, die, daarvan, daarbij, waarvan, waarmee, "inzienelijk maken" (verschrijving), waarbij, "in het kader" | Eigen toevoeging; ASTRA kent geen patronen. Vier zijn voornaamwoordelijke bijwoorden, twee zijn geen verwijzing ('in het kader' hoort bij ARAI-05/INT-10). Ontbreken: het, hij, zij, dat, hem, haar, hun, zijn, ervan, hiervan, daarmee, hetgeen, welke. |
| extra patroon (`src/validation/additional_patterns.py` r. 36-38) | `\b(deze\|dit\|die\|daarvan)\b(?!\s+(begrip\|definitie\|regel))` | Uitzondering voor "deze regel/definitie/begrip"; is **dood** omdat het recordpatroon `\bdeze\b` toch vuurt (proef E07). |
| `type` / `geldigheid` / `brondocument` | "interne structuur" / "gehele definitie" / "ASTRA" | ASTRA: "term" / "alle" / DBT 4.3. De herkomst is afgevlakt (DEF-625-thema); "gehele definitie" is een bereikuitspraak, geen normwijziging. |
| `runtime_contract` | judgment_review, review_required, excluded_from_score, example_pair_policy review_policy (DEF-624) | Besluit: reviewplichtig omdat "het patroon ook op het eigen goede voorbeeld vuurt". Proef E01/E02 bevestigt dat op 26f2374d. |

**Toepasselijkheid.** Dezelfde norm geldt voor gegenereerde, bewerkte, geïmporteerde en aangeleverde definitietekst, bij toetsen, review, conceptopslag, vaststelling en export; uitsluitend toetsen wijzigt de tekst niet. Primair object is de definitiezin; voor toelichting, voorbeelden en tegenvoorbeelden geldt de norm ook, maar daar mag een antecedent over een zinsgrens lopen (ASTRA: "in de definitie"), wat de lokale "dezelfde zin" zou verbieden (registergeval INT03-C-E16; besluitpunt B1).

**Uitzonderingen — onderbouwd of open.**

1. *Betrekkelijk voornaamwoord direct na zijn antecedent* ("persoon **die** een aanvraag indient"): voldoet. Onderbouwd door het ASTRA-JUIST-voorbeeld zelf en door `definitie-nederlandse-definities/reference.md` r. 169-171 (bijzin ✅). Geen afkeurgrond; als signaal hooguit laag.
2. *Voorlopig of expletief 'het'/'er'* ("het is toegestaan", "er wordt getoetst"): geen verwijzing, dus niet van toepassing. Taalkundig gangbaar; Onze Taal-pagina niet gelezen → *niet geverifieerd*.
3. *Bezittelijke voornaamwoorden* (zijn/haar/hun): vallen onder "ieder voornaamwoord"; geen uitzondering. Nu volledig ongedekt (proef E08, historisch possessive_ambiguity).
4. *Vooruitverwijzing binnen de definitie* ("zodra deze gereed is, wordt de aanvraag verzonden"): ASTRA sluit het niet uit; de lokale "dezelfde zin" evenmin. Leesbaarheid lijdt. **Open (B6)**; voorstel: toegestaan als eenduidig, geen zelfstandige afkeurgrond, wel generatie-stijlvoorkeur "antecedent eerst".
5. *Verwijzing naar het gedefinieerde begrip zelf* ("… deze regel …" bij lemma *regel*): het antecedent is het lemma, buiten de definitiezin; tegelijk CON-CIRC-001-domein. **Open (B6)**; voorstel: INT-03 beoordeelt de referentie als duidelijk, CON-CIRC-001 beoordeelt de lemmaherhaling; herstel moet beide ontwijken.
6. *Voornaamwoordelijke bijwoorden* (daarvan, waarmee, waarbij): verwijzen wél (daarvan = van dat). Onder de norm; als betrekkelijk bijwoord direct na het antecedent geldt uitzondering 1.
7. *'in het kader', 'inzienelijk maken'*: geen verwijzing; uit de INT-03-lijst (proef E06).

**Stijlvoorkeur versus afkeurgrond.** "Herhaal liever het zelfstandig naamwoord" (legacy `INT-03.py` hints) en "Vermijden: deze, dit, die, dat" (`definitie-nederlandse-definities/reference.md` r. 185) zijn generatiestijl; de enige afkeurgrond is een verwijzing zonder eenduidig antecedent. Een bestaande definitie wordt niet afgekeurd omdat zij een voornaamwoord bevat.

## Q2 — Noodzakelijke en ondersteunende invoer; veldmatrix

Noodzakelijk is uitsluitend de te toetsen tekst (`required_inputs: [definition_text]`). De term is ondersteunend (uitzondering 5, afgrenzing van CON-CIRC-001). Context, ontologie en toelichting maken een bedoelde referent plausibeler maar mogen een structureel ambigue zin niet "duidelijk" verklaren: de definitie moet zelfstandig leesbaar blijven (ook ASTRA-thema "interne kwaliteit"). Ontbrekende tekst is geen INT-03-uitkomst maar een ontbrekend toetsobject (VAL-EMP-001; nu levert de app toch `review_required`, proef E10). Tegenstrijdige informatie (toelichting noemt referent A, de zin leest als B) is een oordeel *voldoet niet* of *nog te beoordelen*; nooit een stille herschrijving. AI mag geen antecedent, toelichting of bron verzinnen om een verwijzing te "verhelderen".

| Veld | Zelf toetsobject en criterium | Bewijs voor ander oordeel | Invoer bij generatie | Mag AI dit opleveren/wijzigen? | Herkomst; ontbrekend/conflicterend |
|---|---|---|---|---|---|
| Definitiezin | Ja: elke verwijzing eenduidig naar één antecedent in de zin | — | Uitvoer | Voorstel; herstel alleen op verzoek, betekenis gelijk | Ontbreekt → VAL-EMP-001, geen INT-03-oordeel |
| Context (org./jur./wet.) | Nee | Kan een kandidaat plausibeler maken; bewijst geen eenduidigheid | Ondersteunend; bepaalt nu of de INT-instructie überhaupt in de prompt staat (Q4) | Nee (CON-01-contract) | Ontbreekt → norm geldt onverkort; AI mag geen context aannemen |
| Definitiebronnen | Nee | Bronpassage kan de oorspronkelijke referent tonen; bij uitsnijden kan het antecedent verloren gaan | Ondersteunend (CON-02) | Nee | Conflict bron/zin → nog te beoordelen, geen herschrijving van de bron |
| Ontologierelaties (UFO, rollen) | Nee | Rolrelatie maakt een kandidaat waarschijnlijker; geen grammaticaal bewijs | Ondersteunend | Categorie is een te controleren claim (ESS-02) | Geen automatische referentkeuze uit een categorie |
| Voorbeelden / praktijkvoorbeelden | Ja, zelfde criterium; antecedent mag over zinsgrens (B1) | Tonen de bedoelde actor | Niet nodig | Voorstel | Gegenereerd voorbeeld is geen bevestiging van de zin |
| Tegenvoorbeelden | Ja, zelfde criterium | Kunnen een alternatieve referent zichtbaar maken | Niet nodig | Voorstel | idem |
| Grensgevallen | Ja, zelfde criterium | Meerdere syntactische kandidaten benoemen | Niet nodig | Voorstel | idem |
| Synoniemen | Nee (termlabels; lidwoord/voornaamwoord in een label is geen INT-03-kwestie) | Kunnen lezing beïnvloeden (SAM-06/08) | Niet nodig | n.v.t. | — |
| Homoniemen | Nee | Kunnen een kandidaat ambigu maken | Niet nodig | n.v.t. | — |
| Toelichting | Ja, zelfde criterium, antecedent mag over zinsgrens | Kan de bedoelde referent vastleggen als reviewerbewijs; repareert de zin niet | Ondersteunend | Voorstel, apart van de kern | Conflict toelichting/zin → voldoet niet of nog te beoordelen |
| Term/lemma, registratiesleutel | Nee | Nodig voor uitzondering 5 en CON-CIRC-001 | Verplicht | Nee | Term ≠ conceptidentiteit ≠ sleutel: niet verwisselen |

## Q3 — Relaties met andere regels: conflict of overlap, wie beslist

| Regel | Relatie | Aard | Wie beslist |
|---|---|---|---|
| INT-01 (één zin; `generic`, scored) | `INT-01.json` bevat `\bdie\b` en `\bwaarbij\b` als patronen; een INT-03-conforme bijzin ("persoon die …") en het INT-03-herstel via herhaling ("… waarbij de persoon …") krijgen van INT-01 een fail (INT-01-verdieping 23-09, INT01-E01/E03). | **Conflict bij herstel** | INT-01-dossier (de 'die'-indicator); niet hier over te nemen. INT-03-herstel moet het INT-01-signaal tonen, niet stil kiezen. |
| INT-04 (lidwoordverwijzing) | Beide gaan over referentieduidelijkheid; INT-04 = bepaald lidwoord + naamwoord zonder specificatie. Herhaling van het zelfstandig naamwoord ("de persoon") kan INT-04 raken. | Overlap | INT-04-dossier; hertoetsen na INT-03-herstel. |
| ARAI-05 / INT-10 (impliciete aannames, achtergrondkennis) | 'in het kader' zit in de INT-03-lijst maar is ARAI-05-materie (`ARAI-05.json` "in het systeem" e.d.). Antecedent buiten de definitie (external_reference) raakt ook INT-10. | Overlap door verkeerd geplaatst patroon | Hier: patroon uit INT-03 halen (B4); ARAI-05 ongewijzigd. |
| CON-CIRC-001 (lemma niet letterlijk in de zin) | Herstel "deze regel" → "regel" bij lemma *regel* schendt CON-CIRC-001; verwijzing naar het lemma via voornaamwoord is de omgekeerde route (E11). | **Conflict bij herstel** | Chris (B5/B6): herstel via herformulering zonder lemma. |
| SAM-02 (geen herhaling in kwalificatie) | Herhaling van een zelfstandig naamwoord bij samengestelde begrippen kan SAM-02 raken. | Mogelijke overlap, niet onderzocht | SAM-02-dossier. |
| ESS-01 | 'zodat', 'waardoor … begrepen' (E01, E04) zijn doelsignalen; los van INT-03. | Overlap in dezelfde zinnen, geen conflict | ESS-01 ongewijzigd. |
| CON-02 / ESS-03 (AI-beoordeling, DEF-743/766) | Procedureel sjabloon voor optie T2 (evaluator + async wrapper + contract met vingerafdruk, vier uitkomsten, binding aan promptversie/normhash/model). | Werkvorm, geen normrelatie | ADR-001: per regel apart besluit (B2). |
| ESS-04 (DEF-767) | `_reden_met_passages` is het sjabloon voor optie T1a (letterlijke passages in de reden). | Werkvorm | B2. |

## Q4 — Bewezen appgedrag per ingang; ontbrekende bewijzen

**Toetsen (service, manager- én cachepad; proef route A, 15 gevallen × 2 routes, exitstatus 0).**
- Elke tekst, ook zonder voornaamwoord (E05) en de lege tekst (E10), levert `review_required`; `validation_status` = `validated`; nooit een violation. Reden = letterlijk de toetsvraag uit het record; signalen = de vurende regexstrings (`judgment_review.py` r. 65-78, 195-216) — geen geciteerde passages, geen kandidaat-antecedenten. Er is voor INT-03 geen regelspecifieke tak (alleen ESS-01/02/04).
- De signalen onderscheiden het ASTRA-paar niet (E01 = E02: `\bdie\b` + extra patroon); het probleemwoord 'het' (E01, E04) en bezittelijk 'haar'/'zijn' (E08, possessive_ambiguity) geven **geen** signaal; 'in het kader' geeft een niet-voornaamwoordsignaal (E06); de uitzondering in het extra patroon is dood (E07); bij possessive_ambiguity wijst het signaal naar het onproblematische 'die'. De zes historische gevallen (11-09) leveren op 26f2374d dezelfde uitkomsten.
- Bewezen: de signaalhulp heeft nul onderscheidend vermogen voor de norm; de reviewplicht is de enige inhoudelijke werking.

**Genereren (proef route B).**
- Het live INT-03-blok is exact: kop, `uitleg`, "**Instructie:** Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent in dezelfde zin", ✅/❌ ASTRA-paar (P01). De `toelichting` ("dezelfde zin of zinsdeel", "zelfstandig naamwoord") wordt **niet** gerenderd; de lokale verscherping bereikt het model alleen via "in dezelfde zin". Zonder voorbeelden (P03) verdwijnt het ASTRA-paar.
- **Het INT-blok staat alleen in de prompt bij juridische of wettelijke context** (P06/P07 aanwezig; P04 zonder context en P05 met alleen organisatorische context: `integrity_rules` en `sam_rules` overgeslagen). Oorzaak: `prompt_orchestrator._get_active_modules` r. 466-471 (DEF-123). Dit actualiseert de 7-09-claim op 26f2374d en verklaart het 7-09-bewijs (drie van vier varianten zonder INT-module). Gevolg: voor definities zonder juridische/wettelijke context ontvangt het model **geen enkele** INT-instructie (INT-01 t/m INT-10) terwijl de toets alle INT-regels draait: G en T lopen structureel uiteen voor de hele INT-categorie. Meting: prompt 25.925 tekens (geen context) tegen 35.907 (juridisch), onder de kap van 60.000.
- `IntegrityRulesModule` (`integrity_rules_module.py`, hardcoded INT-03-tekst met extra paar "Voorwaarde: …") wordt alleen geëxporteerd in `modules/__init__.py` en gebruikt in `tests/unit/services/prompts/test_def171_optimization.py`; niet geregistreerd in `modular_prompt_adapter.py` r. 70-148 → dode module. Legacy `src/toetsregels/regels/INT-03.py` en `src/toetsregels/validators/INT_03.py` zijn byte-identiek (sha256 `3e4b15ea…`), worden nergens in `src/` geïmporteerd; `ToetsregelManager` laadt uitsluitend `*.json`. `src/validation/definitie_validator.py` (INT-03-mapping r. 180, 230, 598) heeft geen consument in `src/`. Bewijs is statisch (grep + laderinspectie); een dynamische lading langs een andere route is niet uitgesloten maar niet gevonden.

**UI en vervolg (statisch gelezen, niet uitgevoerd).**
- `validation_view.py`: INT-03 verschijnt uitsluitend als code in één infolijn "🟠 Nog te beoordelen: INT-03, …" (`_statuslijst_regels` r. 237-263; weergave r. 859-864 met `continue`, dus zonder uitleg-expander). Alleen ESS-01/02/04 krijgen hun reden als tekst (r. 803-808). Het woord `signals` komt in `src/ui` niet voor: de signalen zijn nergens zichtbaar. De reviewer ziet dus noch de toetsvraag noch de passages.
- Expertreview (`expert_review_tab.py` r. 1601-1654, 1769 e.v.): één besluit per definitie (goedkeuren/wijzigingen/afwijzen + opmerkingen). Een per-regelbeoordeling met vingerafdruk bestaat alleen voor CON-01 (`set_context_review`), CON-02 (bronreview) en ESS-03 (assessment). **Er wordt geen reviewbesluit per INT-03 of per signaal opgeslagen.**
- Transport: `service_factory.py` r. 297-312 laat `review_required` meereizen; `definition_edit_service.py` r. 302-319 herbindt alleen ESS-03 bij bewerking, INT-03-items reizen ongewijzigd mee. Export: `src/export/export_txt.py` r. 14 mapt `review_required` naar "nog te beoordelen" (label; inhoud niet geproefd). Of `review_required` in `definities.validation_issues` (schema r. 62) landt: niet geverifieerd.

**Ontbrekende bewijzen.** Geen Streamlit-run (UI-weergave niet gedraaid); geen opslag-/herlaadproef; geen exportinhoud; import- en vaststel-/exportpoort (DEF-630) niet onderzocht; geen modelproef (dus geen bewijs dat het model de instructie naleeft of dat de afwezigheid van het INT-blok de uitvoer verslechtert).

## Q5 — Aanbevolen regeltekst, appgedrag/meldingen en skill-/promptvervangingen

### G — generatie-instructie (exacte vervangende tekst met vindplaats)

Probleem met de huidige instructie (`json_based_rules_module.py` r. 378): (1) noemt alleen 'deze', 'dit', 'die', terwijl het ASTRA-voorbeeld over 'het' gaat en bezittelijke vormen ongenoemd blijven; (2) "in dezelfde zin" is lokaal (B1); (3) zegt niet dat een bijzin direct na het antecedent goed is, zodat het model ook correcte bijzinnen kan gaan mijden (en INT-01 dat beloont); (4) geeft geen herstelvorm en geen betekenisgrens; (5) bereikt het model alleen bij juridische/wettelijke context (transport, B3).

**G1 — `instruction_map["INT-03"]` (r. 378), voorstel:**

> Laat elk verwijzend woord in de definitie — voornaamwoorden zoals 'het', 'hij', 'zij', 'deze', 'dit', 'die', 'dat', 'zijn', 'haar', 'hun' en voornaamwoordelijke bijwoorden zoals 'daarvan', 'waarmee' — voor de lezer eenduidig naar precies één antecedent in de definitie verwijzen. Een betrekkelijke bijzin direct na het antecedent ('persoon die een aanvraag indient') is goed. Kan een verwijzing op meer dan één antecedent slaan of staat het antecedent buiten de definitie, herhaal dan het bedoelde zelfstandig naamwoord of herformuleer, zonder het begrip zelf in de definitie op te nemen. Verander de betekenis niet en verzin geen antecedent; blijkt de bedoelde referent niet uit de gegeven betekenis, context of bron, lever dan één voorlopige kandidaat en laat de vraag bij de beoordeling.

**G2 — `INT-03.json`:** `uitleg` → "Voor ieder voornaamwoord in de definitie is voor de lezer duidelijk waarnaar het verwijst." (ASTRA-getrouw, positief). `toelichting` → "Voornaamwoorden en voornaamwoordelijke bijwoorden ('het', 'deze', 'die', 'dat', 'zijn', 'daarvan' …) verwijzen naar een antecedent. Dat antecedent staat in de definitie zelf en is eenduidig; een betrekkelijke bijzin direct na het antecedent voldoet. Gebruikelijke herstelvormen zijn herhaling van het bedoelde zelfstandig naamwoord of herformulering, met behoud van betekenis." (de zinsnede "dezelfde zin of zinsdeel" vervalt of blijft, afhankelijk van B1). `toetsvraag` → "Bevat de definitie een voornaamwoord of voornaamwoordelijk bijwoord? Zo ja: is voor de lezer eenduidig welk antecedent in de definitie bedoeld is, of zijn er meer kandidaten of geen antecedent?" `goede_voorbeelden` aanvullen met "Persoon die een aanvraag indient." (uitzondering 1), `foute_voorbeelden` met "Persoon met een vertegenwoordiger die een aanvraag indient." en "Verplichting van de werkgever om de werknemer over haar rechten te informeren." `brondocument` → "ASTRA (Ross, DBT 4.3)". `example_pair_policy` blijft `review_policy` zolang T0/T1a geldt.

**G3 — `definitie-toetsregels/reference.md` r. 64:** "| INT-03 | Duidelijke voornaamwoord-verwijzing | **hoog** | Laat elk voornaamwoord ('het', 'deze', 'die', 'dat', 'zijn', 'haar' …) eenduidig naar één antecedent in de definitie verwijzen; een bijzin direct na het antecedent is goed; herhaal anders het zelfstandig naamwoord of herformuleer zonder betekenisverandering |". Eventueel een kort INT-03-blok in `SKILL.md` naar het voorbeeld van ESS-04 (norm, G, T, geen cijfer, geen poort).

**G4 — `definitie-nederlandse-definities/reference.md` r. 185:** "- Verwijzingen zonder eenduidig antecedent in de definitie: `het`, `deze`, `dit`, `die`, `dat`, `zijn`, `haar`, `daarvan` enz. (INT-03); een betrekkelijke bijzin direct na het antecedent (`persoon die …`) is correct, zie Grammaticaregels".

**G5 — transport (B3):** `prompt_orchestrator._get_active_modules` r. 466-471: `integrity_rules` onafhankelijk van context activeren (SAM apart beslissen). Vooraf te controleren door de app: INT-blok aanwezig in de gebouwde prompt (metadata `skipped_modules`), tekst niet leeg. Wat een modelvoorstel blijft: de kandidaat zelf; verplichte menselijke review blijft bestaan.

### T — toetsinstructie en appgedrag

**Wat het mechanisme nu doet (bewezen):** altijd `review_required`; reden = toetsvraag; signalen = patroonstrings; geen passages; UI toont alleen de code. Uitkomsten *overtreding*, *ontbrekend bewijs*, *beoordeling nodig* en *technische fout* worden niet onderscheiden; alles is "nog te beoordelen".

**Wat het zou moeten opleveren (contract, ongeacht optie):**

| Uitkomst | Wanneer | Meldingstekst (voorstel) |
|---|---|---|
| Voldoet | elke verwijzing heeft één antecedent in de definitie | "INT-03 — Voldoet: 'die' → gebeurtenis; 'die gebeurtenis' → gebeurtenis." |
| Voldoet niet | een verwijzing zonder antecedent of met meer kandidaten, en de bedoelde referent staat vast | "INT-03 — Voldoet niet: 'het' heeft geen eenduidig antecedent; kandidaten: omstandigheden, omgeving, gebeurtenis, basis. Herstel: noem het bedoelde antecedent, bijvoorbeeld 'die gebeurtenis'." |
| Niet van toepassing | geen verwijzend woord | "INT-03 — Niet van toepassing: de definitie bevat geen verwijzend voornaamwoord." |
| Nog te beoordelen (onvoldoende informatie) | meer kandidaten en de bedoeling blijkt niet uit tekst, toelichting of bron; precies één vraag | "INT-03 — Nog te beoordelen: 'haar' kan naar de werkgever of de werknemer verwijzen. Vraag: wiens rechten zijn bedoeld?" |
| Niet beoordeeld (ontbrekend bewijs) | lege tekst | `not_evaluated` "vereiste invoer ontbreekt: definition_text" (zoals ESS-03) |
| Technische fout | beoordeling niet uitgevoerd | "INT-03 — Technisch probleem: beoordeling niet uitgevoerd; geen oordeel." |

Uitsluitend toetsen wijzigt de tekst niet; een negatieve uitkomst blokkeert vaststellen/export niet (in lijn met ESS-03-besluit 21-09) tenzij Chris anders beslist; geen cijfer (excluded_from_score blijft).

**Opties.**
- **T0 — huidig behouden.** Geen kosten; nul onderscheidend vermogen; reviewer ziet niets (Q4). Niet aanbevolen.
- **T1a — menselijk oordeel met verbeterde signaalhulp** (patroon ESS-04 `_reden_met_passages`): reden = "INT-03 — Nog te beoordelen. Te beoordelen verwijzing: '{passage}'. Naar welk antecedent verwijst zij; zijn er meer kandidaten? Dit signaal geeft nog geen oordeel."; zonder passage: "Geen verwijzend woord gesignaleerd; 'het', 'zijn' en 'haar' worden niet gesignaleerd — beoordeel bij twijfel." Patroonlijst opschonen (B4). UI: reden tonen zoals bij ESS-04 (r. 807 uitbreiden met INT-03). Kandidaat-antecedenten zijn zonder woordsoort-/zinsontleding niet betrouwbaar te bepalen; een parser (bijv. spaCy-nl) is een nieuwe afhankelijkheid (**T1b**, afgeraden voor lage precisie).
- **T2 — AI-beoordeling zoals ESS-03/CON-02.** Nieuwe evaluator (bijv. `reference_assessment`) + async dienst + domeincontract: vier uitkomsten + fout, citaat van de verwijzing en van elk kandidaat-antecedent moet letterlijk in de tekst staan (code controleert citaatbestaan), vingerafdruk over term, tekst, contextlijsten, toelichting; binding aan promptversie/normhash/provider/model; niet-blokkerend, geen cijfer; bij *onvoldoende informatie* precies één vraag (verduidelijkingsroute zoals ESS-03). Kosten: één modelaanroep per validatie, goldset (dit register), ADR-001-besluit, privacy (definitietekst gaat naar het model, zoals bij ESS-03).

Aanbeveling C: **T1a nu** (kleine wijziging, zelfde patroon als ESS-04, geen afhankelijkheid, maakt de reviewhulp eindelijk zichtbaar) en **T2 als afzonderlijk besluit** nadat de ESS-03-ervaring (kosten, foutbeleid) is geëvalueerd. T0 en T1b niet.

### H — begrensde terugkoppeling en herstel

Diagnose vóór herstel bij een falende gegenereerde definitie: (a) werkelijke generatieovertreding (E01-vorm); (b) instructie-/transportverlies: het INT-blok stond niet in de prompt (P04/P05) — dan is de generator niet "fout", de keten is dat; (c) foutpositieve signaalhulp (E02, E06, clear_relative); (d) ontbrekend bewijs: verwijzing zonder signaal (E04, E08) — de toets bewijst niets, de mens moet lezen; (e) technische storing.

Herstelvormen (alleen op verzoek, nooit automatisch; consistent met DEF-638 en de CON-01-lijn): (1) vervang het ambigue voornaamwoord door het bedoelde zelfstandig naamwoord met passend bepaald/aanwijzend woord ('die gebeurtenis'); (2) herformuleer tot een betrekkelijke bijzin direct na het antecedent. Beschermd: betekenis, brongetrouwheid, noodzakelijke namen (CON-01), recordidentiteit, gebruikersinvoer. Stop: referent onbekend (E15), herstel zou het lemma invoegen (CON-CIRC-001, E11), herstel zou INT-01 ('die', 'waarbij') of INT-04 raken zonder dat de gebruiker dat ziet (E14), betekenis verandert, foutpositieve evaluator (E02). Poginglimiet: één automatische kandidaat, daarna mens (productkeuze). Hertoetsing van de gewijzigde tekst plus INT-01, INT-04, CON-CIRC-001, ARAI-06 en SAM-02; oude oordelen over gewijzigde tekst gelden niet. Gebruiker ontvangt: toetsresultaat per uitkomst, conceptstatus, of de expertbeoordeling en vaststelling nog open staan.

## Q6 — Beoogde kwaliteitswinst, vergelijking vóór/na, risico's, besluiten

**Nulmeting (dit onderzoek).** T0: 15/15 gevallen `review_required`, 0 onderscheid tussen goed en fout ASTRA-paar, 2 van 5 werkelijke overtredingen zonder enig signaal (E04, E08), 3 foutpositieve signalen op correcte zinnen (E02, E06, clear_relative), reviewer ziet code zonder reden of passage. G: INT-instructie afwezig zonder juridische/wettelijke context.

**Beoogde verbetering en criteria (vooraf).**
- G: minder eerste-poging-definities met een verwijzing zonder eenduidig antecedent, met name 'het' en bezittelijke vormen; behoud: correcte bijzinnen blijven toegestaan, geen lemma-invoeging, geen betekenisverandering, geen langere zinnen door overbodige herhaling. Onaanvaardbaar: het model vermijdt alle voornaamwoorden en levert stroeve herhalingen, of verzint antecedenten.
- T: op het register moet E01, E04, E08, two_candidates, possessive_ambiguity, external_reference als *voldoet niet* of *nog te beoordelen met vraag* uitkomen; E02, E05, E06, E12, clear_relative, explicit_repeat mogen nooit *voldoet niet* worden; E10 wordt *niet beoordeeld*. Motivering citeert de verwijzing en, bij T2, de kandidaten letterlijk. Meer groene uitkomsten zijn geen winst; terecht *nog te beoordelen* met een goede vraag wel.
- H: betekenisbehoud in ≥ alle voorgestelde herstellingen, beoordeeld door een mens tegen bron/bedoeling; geen buurregelovertreding zonder melding.

**Vergelijking vóór/na (ontwerp).** Zelfde invoer, betekenis en verwachtingen: het register (A + B), plus tien niet voor het ontwerp gebruikte definities uit een synthetische set (niet uit productiegegevens). Varianten: oude vs. nieuwe instructie (G1) bij aanwezig INT-blok; oude keten zonder INT-blok vs. keten met INT-blok (G5); T0 vs. T1a (reviewerbeoordelingen met hulp) vs. T2 (oordelen + motivering). Model, bronnen en instellingen gelijk; herhaalde runs (≥ 3) om toeval te scheiden van effect. Beoordeling blind voor variant, tegen de vooraf vastgelegde normverwachting; de nieuwe evaluator is niet de enige maatstaf voor zichzelf. Rapportage: verbeterd / gelijk / verslechterd / onbeslist per geval, met aantallen en steekproefgrens; geen generalisatie buiten de onderzochte gevallen.

**Nu nog niet uitvoerbaar.** (1) Generatieproef met live model: niet geautoriseerd in dit onderzoek; eigenaar: uitvoerder DEF-772 na besluit B2/B3; afhankelijk van modelautorisatie en vastgelegde prompt-/normversie. (2) T1a/T2-uitkomsten: bestaan pas na implementatie; eigenaar: uitvoerder; nulmeting is hier. (3) Reviewerproef (helpt de passagehulp echt?): eigenaar Chris; afhankelijk van T1a-oplevering. Status na implementatie zonder dit bewijs: *geïmplementeerd; kwaliteitswinst nog niet vastgesteld*.

**Risico's en bewijsgaten.** Uitvoeringsvolgorde: eerst G5 (INT-blok altijd) en dan pas een strengere T, anders keurt een scherpere toets definities af die zonder instructie zijn gegenereerd. Een opgeschoonde patroonlijst met 'het'/'zijn'/'haar' geeft veel foutpositieve passages (lidwoord, werkwoord); alleen als hulp met passage, nooit als afkeur. T2 stuurt definitietekst naar een model (zelfde privacyafweging als ESS-03). INT-01 blijft de bijzin bestraffen zolang dat dossier niet is besloten.

## Besluitpunten voor Chris

| # | Keuze | Opties en gevolgen | Voorkeur C |
|---|---|---|---|
| B1 | Normreikwijdte | (a) ASTRA-tekst als norm: antecedent "in de definitie", eenduidig; "dezelfde zin/zinsdeel" en "zelfstandig naamwoord" vervallen als eis (blijven stijlvoorkeur). (b) Lokale verscherping handhaven: strenger dan ASTRA, keurt toelichting met zinsgrensverwijzing (E16) af, sluit propositie-antecedenten uit. | (a) |
| B2 | Toetsmechanisme | T0 behouden / T1a passagehulp + reden zichtbaar / T1b parser / T2 AI-beoordeling (ADR-001, kosten, privacy). | T1a nu, T2 als apart besluit; niet T1b |
| B3 | INT-instructies in elke prompt | (a) `integrity_rules` altijd activeren (+~10K tekens, onder kap; geldt voor alle INT-regels); (b) alleen INT-03 los toevoegen (breekt de modulestructuur); (c) laten (G en T blijven uiteenlopen). SAM apart. | (a) |
| B4 | Patroonlijst | (a) opschonen tot verwijzende woorden, 'in het kader' en 'inzienelijk maken' eruit, extra patroon verwijderen (dood), 'het/dat/zijn/haar/hun' als laag-precisiesignaal met passage; (b) ongewijzigd. | (a), alleen als signaal |
| B5 | Herstelbeleid | (a) alleen op verzoek, één kandidaat, stopregels als in H; (b) automatisch herstel na fail (afgeraden: betekenisrisico, DEF-638). | (a) |
| B6 | Uitzonderingen | vooruitverwijzing toegestaan mits eenduidig? verwijzing naar het lemma: INT-03 duidelijk maar CON-CIRC-001? expletief 'het' n.v.t. | ja / ja+CON-CIRC / ja |
| B7 | Opruimen legacy | `IntegrityRulesModule`, `INT-03.py`/`INT_03.py`, INT-03-mapping in `definitie_validator.py` verwijderen (tech-debt, buiten deze regel; past bij DEF-507-lijn). | tracken |

Wat bestaand beleid herstelt: B3 (DEF-126/171 bedoelden instructies voor alle regels), B4-opschoning, T1a (DEF-624/767-lijn). Wat een nieuw normbesluit vraagt: B1, B2-T2, B6.

## Dekkingstabel

| Onderdeel | Waar |
|---|---|
| (1) doel/betekenis, (2) norm/besluiten, (3) toepasselijkheid | Q1 |
| (4) context, (5) bronnen, (6) ontologie, (7) aanvullingen | Q2 veldmatrix |
| (8) appgedrag, (10) status/score/poorten | Q4, T |
| (9) skills/prompts | Q5 G1–G5 |
| (11) proeven | proef-c-v1.py, proefverwachtingen/-uitkomsten, casusregister A/C |
| (12) samenhang | Q3 |
| (13) verbeteringen/review | Q5, besluitpunten |
| (14) acceptatie/overdracht | Q6, casusregister B |

## Opgeleverd, ontbrekend, volgende overdracht

Opgeleverd in `onderzoek-c/`: `aanvulling-c-v1.md`, `casusregister-c-v1.md`, `proefverwachtingen-c-v1.json`, `proef-c-v1.py`, `proefuitkomsten-c-v1.json`, `bewijsmanifest-c-v1.json`, plus het uitvoerlog `proef-c-v1-run1.log` (stdout/stderr van de proef; extra bestand, mag door Chris worden verwijderd). Ontbrekend: UI-, opslag-, export- en modelproeven (Q4/Q6); Ross DBT §4.3 en Onze Taal niet gelezen; de sessie kon `~/.agents/skills/` niet lezen (identieke bron gebruikt). Volgende overdracht: onderzoeker A ontvangt deze v1 voor de wederzijdse review; C reviewt daarna de volledige onderzoeken van A en B en verwerkt ontvangen punten in een v2. Geen gezamenlijke afronding geclaimd.

## Bronnen

- ASTRA: `gedeeld/astra-INT-03-raw-20260925.txt` (sha256 `121c4fbb…`); feitenbasis `gedeeld/feitenbasis-v1.md` (`c160479a…`); startopdracht `gedeeld/startopdracht-c-v1.md` (`e70b6fd4…`).
- Historisch: `docs/analyses/def606-regeldossiers/INT-03-v1.md` (`b01ecc2c…`), `INT-03-bewijs-v1/gevallen.json`, `uitkomsten.json`, `claude-review.json`; `docs/analyses/2026-09-07-definitiekwaliteit-dossiers-int-sam.md` r. 127-156; `…-int-sam-prompt-bewijs.json` (rule_presence INT-03 en skipped_modules per variant).
- Code (leesbasis 26f2374d): `src/toetsregels/regels/INT-03.json`; `src/services/validation/evaluators/judgment_review.py` r. 1-78, 157-216; `src/validation/additional_patterns.py` r. 36-38; `src/services/validation/modular_validation_service.py` r. 843-917, 1575-1627; `src/services/validation/interfaces.py` r. 267-278; `src/services/prompts/modules/json_based_rules_module.py` r. 130-200, 228-281, 378; `src/services/prompts/modules/prompt_orchestrator.py` r. 403-515; `src/services/prompts/modular_prompt_adapter.py` r. 52-158; `src/services/prompts/modules/integrity_rules_module.py` r. 182-206; `src/toetsregels/regels/INT-03.py`; `src/validation/definitie_validator.py` r. 180, 230; `src/ui/components/validation_view.py` r. 237-263, 316-326, 795-880; `src/ui/components/expert_review_tab.py` r. 1218-1246, 1601-1654, 1769-1848; `src/services/service_factory.py` r. 297-312; `src/services/definition_edit_service.py` r. 255-319; `src/export/export_txt.py` r. 14; `src/database/schema.sql` r. 59-62; `src/services/validation/evaluators/countability_assessment.py`, `source_evidence.py`, `src/domain/ess03/contract.py` r. 1-58 (sjabloon T2); `src/toetsregels/regels/INT-01.json`, `ARAI-05.json`, `CON-CIRC-001.json`; `tests/fixtures/toetsregels/runtime_cases.yaml` r. 378-387; `tests/unit/validation/test_rule_runtime_matrix.py` r. 163-243.
- Skills (bron van waarheid `_claude-global-setup/skills/`): `toetsregel-onderzoek/SKILL.md` + references; `definitie-toetsregels/SKILL.md`, `reference.md` r. 60-70, 146-179; `definitie-nederlandse-definities/reference.md` r. 169-171, 181-188.
- Eigen proef: `proef-c-v1.py`, `proefverwachtingen-c-v1.json`, `proefuitkomsten-c-v1.json`, `proef-c-v1-run1.log` (exitstatus 0).
