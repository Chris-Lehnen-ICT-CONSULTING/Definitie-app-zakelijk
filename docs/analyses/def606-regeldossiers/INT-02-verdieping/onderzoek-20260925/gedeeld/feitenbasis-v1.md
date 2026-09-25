# INT-02 — gedeelde feitenbasis v1

25 september 2026 · DEF-771 · opgesteld door onderzoeker A (Cowork-hoofdsessie, coördinator) vóór eigen conclusies. Dit bestand bevat uitsluitend bronfeiten, vastgelegde besluiten en historische waarnemingen; geen nieuwe interpretaties of voorstellen. Beide onderzoekslijnen (A en B) krijgen dit bestand als gedeelde start.

## 0. Identiteit en status

| Registratie | Waarde |
|---|---|
| Actieve regel | INT-02 — lokaal "Geen beslisregel"; ASTRA `Regel-kort` "geen beslisregel", `Code=INT-02` |
| Centraal Linear-issue | [DEF-771](https://linear.app/definitie-app/issue/DEF-771) (Backlog; placeholder aangemaakt 17-09-2026; geen comments, `updatedAt` = `createdAt`); parent DEF-606. Relaties: DEF-624 (resultaat-/beoordelingscontract), DEF-625 (normherkomst), DEF-626 (versiesnapshots), DEF-630 (vaststellen/export), DEF-638 (max. één repair) |
| Regelspecifiek bespreekpunt (DEF-771, letterlijk) | "Begripscriterium tegenover voorschrift of procedure beoordelen." Normdoel volgens dossier v1: "Een definitie beschrijft het begrip; zij hoort niet ongemerkt een procedure voor te schrijven. De huidige tekst verbiedt ook voorwaarden. Dat botst mogelijk met benodigde lidmaatschapscriteria en vraagt normduiding, geen stille uitzondering." |
| Historische dossierbasis | `docs/analyses/def606-regeldossiers/INT-02-v1.md` (11-09-2026, commit `d68a98a9`; SHA-256 volgens DEF-771 `1db8b4ea…`), bewijs `INT-02-bewijs-v1/{gevallen,uitkomsten,claude-review}.json` |
| Gebruikerswerkboom = leesbasis | `/Users/chrislehnen/Projecten/Definitie-app`, branch `main`, HEAD `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3` (23-09-2026, merge PR #472 DEF-766 invoerbinding). Werkboom bevat ongetrackte analyse-/dossierbestanden; **niets in de werkboom wijzigen**, alleen lezen en in de eigen uitvoermap schrijven. Venv: `.venv/bin/python` = Python 3.13.15 |
| Gedeelde onderzoeksmap | `docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/` met `gedeeld/` (dit bestand, `bronnen/`, startopdrachten, processtatus), `a-claude-cli/` (onderzoekslijn A) en `b-codex-cli/` (onderzoekslijn B) |
| Onderzoekers (keuze Chris 25-09-2026: "gebruik Codex en Claude CLI en Codex CLI") | **A** = Cowork-hoofdsessie (coördinator, synthese) met een schone Claude Code CLI-sessie op de Mac (`~/.local/bin/claude` 2.1.282, `-p`) als uitvoerende onderzoekslijn A. **B** = schone Codex CLI-sessie op de Mac (`~/.local/bin/codex` codex-cli 0.156.1, `codex exec`). Beide starten uitsluitend vanuit deze feitenbasis; nieuwe conclusies worden pas na opslag van beide v1's uitgewisseld |
| Skill | `toetsregel-onderzoek` — Mac `~/.agents/skills/toetsregel-onderzoek/SKILL.md` SHA-256 `66d65b3f…` (kopie in `gedeeld/bronnen/skill-toetsregel-onderzoek/`); references `werkcontract.md`, `startopdracht.md`, `genereren-en-toetsen.md` |
| Appbreed besluit | Geen totaalscore als kwaliteitscijfer, acceptatiegrond of hersteldriver (Chris, 15-09-2026, `docs/analyses/2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md`) |

## 1. Primaire norm — ASTRA (gelezen 25-09-2026)

Bron: `https://www.astraonline.nl/index.php?title=Geen_beslisregel&action=raw`, opgehaald 25-09-2026 vanuit de Cowork-VM (curl), bewaard als `gedeeld/bronnen/astra-INT-02-raw.wikitext` (SHA-256 `01d00ea0…`, 3.039 B). Paginageschiedenis vraagt login; revisie/datum niet verifieerbaar. Letterlijke velden:

```
|Identificatie=INT-02
|Regel-kort=geen beslisregel
|Regel=Een definitie mag niet geformuleerd worden als een beslisregel.
|Toelichting=Bij een [[Beslisregel|beslisregel]] komt oordeelsvorming kijken, de uitkomst hiervan is dus niet 100% deterministisch. Bron hiervan is vaak beleid, waar dus kennelijk een discretionaire bevoegdheid is opengelaten.

Uiteraard mag een definitie wel geformuleerd worden als een [[Afleidingsregel |afleidingsregel]], want dat is een geheel deterministisch algoritme voor het uitrekenen van een ("afgeleid") feit op basis van andere (zowel oorspronkelijke als afgeleide) feiten. Sterker nog: een afleidbaar begrip MOET gedefinieerd worden in termen van een afleidingsregel.

'''Achtergrond'''
Synoniem voor de term "beslisregel" is de DEMO-term "actieregel" (EN: Action Rule), daar gedefinieerd als "richtlijn voor actor bij het afhandelen van coördinatie-event". [...] Dat lijkt op het begrip ''Behavioral business rule'': 'a business rule that is an obligation concerning conduct, action, practice, or procedure' (Ronald G. Ross, Business Knowledge Blueprints, blz. 260).
Een "afleidingsregel" (EN: derivation rule) levert nieuwe (afgeleide) feiten op. [...] Dat lijkt op het begrip definitional rule: 'a business rule that establishes a definitional criterion that is necessarily true for each instance of a concept' (Ronald G. Ross, Business Knowledge Blueprints, blz. 268).
|Voorbeelden='''transitie-eis'''
ONJUIST: 'eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken.'
JUIST: 'eis die een organisatie ondersteunt om migratie van de huidige naar de toekomstige situatie mogelijk te maken.'
|Brondocument=DBT, 4.2
|Prioriteit=midden
|Aanbeveling=aanbevolen
|Geldigheid=alle
|Status=definitief
|Type=gehele definitie
|Thema=interne kwaliteit van de definitie
|Redactieopmerking=Aandachtspunten:
* is het verband met categorieën van business rules (zoals "afleidingsregels", "beslisregels", "geldigheidsregels") hiermee voldoende omlijnd?
* klopt het aangeven verband met "definitional rule" van Ross – zo ja, hoe dit beter uitleggen? Of onderbrengen bij de uitleg van het begrip afleidingsregel
* het voorbeeld met de term "transitie-eis" (uit Ross) vind ik niet erg sprekend; welk SRK-voorbeeld zou kunnen demonstreren waar dit een misverstand zou kunnen zijn?
```

Gekoppelde ASTRA-begrippen (zelfde datum, `gedeeld/bronnen/astra-Beslisregel-raw.wikitext` SHA-256 `35477c06…`, `astra-Afleidingsregel-raw.wikitext` SHA-256 `793375d9…`):

- **Beslisregel** — Definitie: "Algoritme waarvoor oordeelsvorming nodig is". Toelichting: "Bij een beslisregel komt oordeelsvorming kijken, de uitkomst hiervan is dus niet 100% deterministisch. Bron hiervan is vaak wet of beleid, waar dus kennelijk een discretionaire bevoegdheid is opengelaten." Voorbeeld: art. 45 lid 2 Ppw: "Indien binnen de periode van acht weken (...) gaat de tot weigering of vervallenverklaring bevoegde autoriteit tot weigering of vervallenverklaring over, tenzij hij van oordeel is dat de aanvrager respectievelijk de houder door deze beslissing onevenredig zou worden benadeeld." — "Kennelijk vindt hier een afweging over al dan niet evenredigheid van benadeling plaats; de uitslag is onderwerp van oordeelsvorming en niet deterministisch." Synoniemen: beslisregels, actieregel.
- **Afleidingsregel** — Definitie: "Een geheel deterministisch algoritme voor het uitrekenen van een ("afgeleid") feit op basis van andere (zowel originele als afgeleide) feiten." Voorbeelden o.a.: "[persoon] is '''stelselmatige dader''' op [dag] = [persoon] is in de op [dag] afgelopen vijf jaar voorafgaand aan het laatste feit drie maal wegens een misdrijf onherroepelijk veroordeeld"; "leeftijd = vandaag – geboortedatum". Toelichting: afleiden verandert de toestand van de wereld niet; originele feiten (beslissen, beoordelen, adviseren; maken, transporteren) wel.

ASTRA bevat geen patronen of regexen (geheugen `astra-normatieve-bron`). Herkomst DBT = Ronald Ross, *How to Define Business Terms in Plain English: A Primer*, §4.2 (niet gelezen; alleen de ASTRA-verwijzing).

**Feitelijke verschillen lokaal record ↔ ASTRA (geen oordeel):**

| Onderdeel | Lokaal `INT-02.json` | ASTRA |
|---|---|---|
| Regel/uitleg | "Een definitie bevat geen beslisregels **of voorwaarden**." | "Een definitie mag niet geformuleerd worden als een beslisregel." (geen woord "voorwaarden") |
| Toelichting | "…niet wat ermee moet gebeuren **of onder welke voorwaarden het geldig is**. Voorwaardelijke of normatieve formuleringen zoals 'indien', 'mits' en 'tenzij' horen thuis in regelgeving, niet in definities." | Beslisregel = oordeelsvorming/discretie, niet deterministisch; **afleidingsregel (deterministisch algoritme) is toegestaan én verplicht voor afleidbare begrippen** |
| Toetsvraag | "Bevat de definitie geen voorwaardelijke of normatieve formuleringen zoals beslisregels?" | geen toetsvraag; `Type=gehele definitie` |
| Patronen | 7 regexen: `\bindien\b`, `\bmits\b`, `\balleen als\b`, `\btenzij\b`, `\bvoor zover\b`, `\bop voorwaarde dat\b`, `\bin geval dat\b` | geen |
| Voorbeeldpaar | identiek aan ASTRA (transitie-eis, "moet ondersteunen" ↔ "ondersteunt") | idem; redactie noemt het "niet erg sprekend" |
| Prioriteit/aanbeveling/geldigheid/status/thema | midden / aanbevolen / alle / definitief / interne kwaliteit | gelijk |
| Type | "interne structuur" | "gehele definitie" |
| Brondocument | "ASTRA" | "DBT, 4.2" |

## 2. Lokaal regelrecord op main `26f2374d`

`src/toetsregels/regels/INT-02.json` — id `INT_02`; naam "Geen beslisregel"; uitleg/toelichting/toetsvraag/patronen/voorbeelden als in §1; `runtime_contract`: evaluator `judgment_review`, required_inputs `[definition_text]`, executability `judgment`, automation_status `review_required`, score_policy `excluded_from_score`, example_pair_policy `review_policy`, example_pair_reason "het gedocumenteerde paar verschilt uitsluitend in het modale werkwoord moet, wat de norm van ARAI-04 is; beslisregel-herkenning blijft daarnaast een inhoudelijk oordeel.", example_pair_issue `DEF-624`. Record is byte-gelijk aan de momentopname in `INT-02-bewijs-v1/uitkomsten.json` (commit `d68a98a9`).

Regellijsten: `config/toetsregels/toetsregels_config.yaml:150`, `config/config.yaml:182`, `src/config/config_manager.py:219` (`allowed_toetsregels`), `src/toetsregels/sets/per-categorie/interne.json:6`. `config/validation/rule_reasoning_config.yaml`: **geen** INT-02-vermelding. `.claude/rules/patterns.md`: **geen** INT-02-/beslisregel-vermelding (DEF-771 vroeg dit te controleren).

## 3. Actuele appketen op main `26f2374d` (codelezing 25-09-2026; geen nieuwe gedragsproef)

**Toetsen (T-kant).** `src/services/validation/evaluators/judgment_review.py`: INT-02 staat in de docstring als één van de acht DEF-624-oordeelregels (dertien totaal). `evaluate()` levert **altijd** `EvaluationOutcome.review_required(reden, signals=…)`; reden = `record.toetsvraag` ("Bevat de definitie geen voorwaardelijke of normatieve formuleringen zoals beslisregels?"); specifieke redenteksten met passagecitaten bestaan alleen voor ESS-01, ESS-02 en ESS-04 (`_reden_met_passages`). `_signalen()`: record-`herkenbaar_patronen` + `get_additional_patterns(code)` (voor INT-02: geen extra patronen in `src/validation/additional_patterns.py`), IGNORECASE op `ctx.cleaned_text`; signalen zijn de regexstrings, geen tekstfragmenten. Docstring: patronen zijn signaal, geen bewijs; "een algemene AI-jury voor deze dertien regels is bewust níet ingevoerd: dat vraagt per regel een afzonderlijk besluit … zoals voor CON-02 (DEF-743) en ESS-03 (DEF-766) genomen is."

`src/services/validation/modular_validation_service.py`: `review_required`-items (r. 695/1345) met `rule_id`, `category`, `reason`, `signals`; status `REVIEW_REQUIRED` telt in de dekking (r. 1618/1788), niet in een score. Resultaatcontract `src/toetsregels/runtime_contract.py`: `ResultStatus` pass/fail/review_required/not_evaluated/error; `ScorePolicy` scored/excluded_from_score/no_score.

**Weergave.** `src/ui/components/validation_view.py`: statuslabel `"review_required": "🟠 Nog te beoordelen"` (r. 251/321) en dekkingsregel "🟠 {n} nog te beoordelen" (r. 155); de samenvattingslus r. 803–808 toont de `reason`-tekst **alleen** voor ESS-01/ESS-02/ESS-04. `expert_review_tab.py:1079`: correctiestatus "nog te beoordelen (bewijs ontbreekt; motiveer)". `definition_generator_tab.py:58`: "{review_required + not_evaluated} open". Of en waar de INT-02-reden en -signalen in de detailweergave verschijnen is **niet gelezen** (open bewijs).

**Opschoning vóór toetsing.** `src/services/definition/cleaning_service.py`: geen behandeling van `indien/mits/tenzij/voorwaard*` (grep 0 treffers). INT-01-onderzoek 21-09 (feit over de keten): bij genereren wordt opgeschoond (label/aanhef weg, slotpunt erbij), bij toetsen/bewerken niet; import valideert niet.

**Poort.** Eigen INT-02-blokkade van vaststellen/export: niet gevonden; `src/services/policies/approval_gate_policy.py` bestaat (niet gelezen voor INT-02). INT-01-onderzoek 21-09 vond een dode `severity`-vergelijking in de vaststelgate en `overall_score` altijd `None` (DEF-630/622) — algemene ketenfeiten, niet INT-02-specifiek.

**Genereren (G-kant).** `src/services/prompts/modular_prompt_adapter.py:70–130` registreert `JSONBasedRulesModule(rule_prefix="INT", module_id="integrity_rules", …)`. `json_based_rules_module.py::_format_rule` (r. 228–281) rendert per regel: `🔹 **INT-02 - Geen beslisregel**` → `- Een definitie bevat geen beslisregels of voorwaarden.` → `- **Instructie:** Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als'` (instruction_map r. 377) → bij `include_examples` (config `include_examples_in_rules`) `✅ transitie-eis: … ondersteunt …` en `❌ transitie-eis: … moet ondersteunen …`. Toetsvraag wordt sinds DEF-171 niet gerenderd. `integrity_rules_module.py` (`IntegrityRulesModule`, `_build_int02_rule` met vier extra ✅/❌-paren o.a. "❌ Toegang: toestemming verleend door een bevoegde autoriteit, indien alle voorwaarden zijn vervuld") wordt alleen geëxporteerd in `modules/__init__.py` en **niet geregistreerd** in de orchestrator (grep: 0 gebruikers) — dode code. `src/services/definition_generator_enhancement.py:243` kent een sleutel `"voorwaarden": ["voorwaarde", "vereiste", "criteria"]` (functie niet gelezen).

**Restanten.** `src/toetsregels/regels/INT-02.py` (`INT02Validator`: fout-voorbeeld-substring → fail 0.0; goed-voorbeeld-substring → pass 1.0; anders patronen → fail; `get_generation_hints()` met "Beschrijf wat iets IS, niet wat ermee moet gebeuren" enz.) en `src/toetsregels/validators/INT_02.py`: volgens DEF-606 (11-08-2026) is de `.py`-laag een restant zonder productieconsument; niet opnieuw geverifieerd voor INT-02.

**Tests/fixtures.** `tests/unit/validation/test_v2_golden_int_more.py::test_int02_no_decision_rules_fail` (tekst "Toegang: toestemming verleend door een bevoegde autoriteit, indien alle voorwaarden zijn vervuld." → INT-02 in `review_required` met niet-lege `signals`, niet in `passed_rules`, geen violation). `tests/fixtures/toetsregels/runtime_cases.yaml:367–376`: `required_fields: [herkenbaar_patronen]`, issue DEF-624, probe "korting: verlaging indien tijdig betaald". `test_rule_runtime_matrix.py::TestAfgeleideTelling` bewaakt het aantal (13) review_required-regels.

**Precedenten in dezelfde keten (feiten, geen INT-02-besluit).** ESS-03: eigen AI-beoordelingsdienst `evaluators/countability_assessment.py` (DEF-766, gemerged PR #467 22-09-2026; vier scoreloze uitkomsten + één vraag; geen gate). CON-02: `source_evidence` (DEF-743). ESS-04: judgment met passagehulp (DEF-767, N2). ESS-01/ESS-02: judgment met eigen redenteksten en besluitgebonden G-blokken.

## 4. Historisch bewijs (11-09-2026, commit `d68a98a9`, `INT-02-bewijs-v1/`)

Zes gevallen (`gevallen.json`), manager- en cacheroute gelijk, offline, exit 0 (`uitkomsten.json`) — alle **review_required**, geen violations:

| Hist. label | Tekst | Signalen |
|---|---|---|
| good | "transitie-eis: eis die een organisatie ondersteunt om migratie van de huidige naar de toekomstige situatie mogelijk te maken." | — |
| bad | "transitie-eis: eis die een organisatie moet ondersteunen om …" | — (geen patroon vuurt op "moet") |
| procedure | "Aanvraag die wordt afgewezen indien een bijlage ontbreekt." | `\bindien\b` |
| membership | "Getal dat even is indien het zonder rest door twee deelbaar is." | `\bindien\b` |
| same_membership_no_if | "Geheel getal dat zonder rest door twee deelbaar is." | — |
| empty | "" | — |

Record en `judgment_review.py`-gedrag voor INT-02 zijn op main ongewijzigd (record byte-gelijk; evaluator kent geen INT-02-specifieke tak), dus deze uitkomsten gelden naar verwachting nog; niet opnieuw gemeten.

Claude-review 11-09 (`claude-review.json`): "indien X, dan Y" kan classificerend of voorschrijvend functioneren; "Een aanvraag is ontvankelijk indien…" kan descriptief lijken maar als beslisregel functioneren; grensgevallen A "Een lid is stemgerechtigd indien ingeschreven vóór 1 januari." en B "Een document geldt als gewaarmerkt mits voorzien van handtekening en datum."; steunt review_required. Dossier v1 §13 corrigeerde diens lezing van het paar (ondersteunt ↔ moet ondersteunen) en nam de grensgevallen niet als vastgesteld recht over.

Dossier v1 (11-09) §3/§4/§7/§13 (onderzoeksduiding, geen besluit): generatie scheidt afbakening van procedure; geen mechanisch verwijderen van "indien"; dezelfde zinsvorm kan classificeren of handelen voorschrijven; voorstel "classificerend kenmerk versus voorgeschreven handeling/rechtsgevolg onderscheiden, bewijs uit context/bron"; "gebruikt worden in een besluit is niet voldoende criterium om een definitie af te keuren"; open: norminterpretatie, reviewercriteria, handelingstoepassing. §14 acceptatiebasis: zelfde betekenis met/zonder indien, voorwaarde versus procedure, normatieve bron, echte lidmaatschapsafbakening, ontbrekende context/tekst; beide laadpaden en UI-review; oorspronkelijke tekst behouden.

## 5. Rechtstreeks relevante vastgelegde besluiten en buurregelfeiten

1. **Geen totaalscore** (15-09-2026): per regel oordeel/onderbouwing/vervolgstap; ontbrekende beoordeling telt niet als geslaagd noch als fout; wijzigt niet automatisch norm, ernst, scorepolicy of reviewplicht per regel.
2. **DEF-624** (16-09-2026, samenvatting uit ESS-05-feitenbasis 21-09): resultaatcontract + consumermigratie goedgekeurd; ontbrekende/ongeldige status = "onbekend"; 44 goed/fout-paren als regressiecases; "gedocumenteerd fout voorbeeld dat niet slechter scoort faalt de contracttest of heeft expliciet goedgekeurde reviewpolicy" — INT-02 draagt `review_policy` met de reden in §2.
3. **DEF-638**: maximaal één validatorgerichte repair + revalidate — Backlog; niets geactiveerd.
4. **ARAI-06-verduidelijking** (DEF-624/625, 07-09-2026): uitsluitend toetsen wijzigt de aangeleverde tekst niet; stijladvies is geen inhoudelijke afkeuring.
5. **ARAI-04 (modaliteit)** — dossier `ARAI-04-v1.md` (11-09, onderzoek, geen besluit): huidige norm vermijdt modale hulpwerkwoorden (`kan/moet/mag/zal`); generic-evaluator mist mag/zal; open normnuance of modaliteit essentieel kenmerk kan zijn; "geen automatische modaliteitsverwijdering". Het INT-02-voorbeeldpaar verschilt uitsluitend in "moet" (record-reden §2).
6. **ESS-05-besluiten** (Chris, 21-09-2026, DEF-768, `ESS-05-verdieping/onderzoek-20260921/gedeeld/besluiten-v1.md`, zusterregel-precedent, geen INT-02-besluit): K-1 LLM-beoordeling per verwant begrip zonder cijfer; K-4 geen zelfstandige blokkade; K-7 geen automatisch herstel, toetsen wijzigt nooit tekst; K-8 elke regel meldt zelf waarom een definitie niet voldoet; **K-9 context is op appniveau verplicht: zonder context wordt niet gegenereerd en niet getoetst** (aandachtspunt: app valideert vandaag wél zonder context).
7. **ESS-03-besluit** (DEF-766, 19/21-09, gebouwd 22-09): app als inhoudelijke beoordelaar via AI-beoordeling op alleen aangeleverd materiaal; uitkomsten voldoet / voldoet niet / niet van toepassing / onvoldoende informatie + één vraag; `no_score`; geen gate; geen automatische reparatie.
8. **ESS-04-besluit N2** (DEF-767): toetsbaarheid is menselijk oordeel; kwalitatieve criteria kunnen volstaan; passagehulp in de reden.
9. **INT-01** (DEF-770; onderzoek afgerond 21-09, Cowork-review 24-09): voorstel A+B: woordlijst (waaronder `indien`) vervalt als INT-01-afkeurgrond; keuzes K1–K-S **nog open bij Chris** (geen `besluiten-v1.md` in `INT-01-verdieping/`; `onderzoek-20260923/` bevat een aanvulling met synthese v3 — niet gelezen). INT-01-patroon `\bindien\b` overlapt met INT-02-patroon.
10. **DEF-771-kader**: G/T/H per veld uitwerken; ruwe modeluitvoer → extractie/opschoning → opgeslagen tekst volgen; samenhang ARAI-04/SUB1, ESS-04, ESS-05: "Elk criterium verbieden zou inhoudelijke toetsbaarheid ondergraven; de spanning moet expliciet worden besloten." Rolverdeling bij later programmeerwerk: hoofdsessie coördineert, Claude Code CLI implementeert, Codex CLI reviewt de diff (geldt niet voor dit onderzoek).
11. **DEF-815** (21-09): modelselectie per generatieonderdeel/toetsregel; kiest geen model.

## 6. Skills (actieve versies op de Mac, `~/.agents/skills`, `_claude-global-setup` HEAD `dc7dc64` 23-09-2026)

- `definitie-toetsregels/reference.md:63` (SHA-256 bestand `f3252105…`): `| INT-02 | Geen beslisregel | midden | Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als' |`. `SKILL.md` (`21b4157c…`) bevat regelcontracten alleen voor CON-01/02, ESS-01/02/03/04 (`references/{con01,con02,ess01,ess02,ess03,ess04}-*.md`); **geen** `references/int02-*.md`; SKILL.md:39 noemt nog "Elke regel heeft een JSON-configuratie en een Python-validator" en "gewogen scoring".
- `definitie-nederlandse-definities/reference.md:186` (`1be4bfce…`), sectie "Verboden Patronen → Vermijden": `- Voorwaardelijke formuleringen: \`indien\`, \`mits\`, \`tenzij\`, \`alleen als\``; r. 181 daarboven: `- Modale hulpwerkwoorden: kan, moet, mag, zal, dient te; …`.
- `definitie-juridisch-nederland`, `definitie-voorbeelden-generatie`, `definitie-ufo-ontologie`: alleen domeintermen ("voorwaardelijk sepot", "voorwaardelijke invrijheidstelling" e.d.); geen INT-02-instructie. `definitie-ontologisch-modelleren`: geen treffer.
- Cowork gebruikt gesynchroniseerde kopieën (`anthropic-skills:toetsregels`, `nederlandse-definities`) met dezelfde INT-02-passages (niet byte-gelijk).

## 7. Onderzoeksvragen, scope en registerafspraken

Q1–Q6 uit `toetsregel-onderzoek/SKILL.md §2`, uitgewerkt met veldmatrix, G (generatie-instructie), T (toetsinstructie) en H (begrensde terugkoppeling/herstel) uit `references/genereren-en-toetsen.md`. Alleen INT-02 is actief; ESS-03/04/05-, CON-01/02-, INT-01- en ARAI-04-besluiten zijn feiten over buurregels, geen INT-02-norm. Geen implementatie, geen skill-/recordwijziging, geen issues, geen betaalde modelproeven, geen productiedata.

**Casusregister — stabiele IDs.** Historische gevallen krijgen vaste IDs: INT02-C01 good, C02 bad, C03 procedure, C04 membership, C05 same_membership_no_if, C06 empty (tekst zoals §4). Nieuwe scenario's: onderzoekslijn A gebruikt INT02-C10 t/m C39, onderzoekslijn B gebruikt INT02-C50 t/m C79. Een ID behoudt zijn scenario; gewijzigde verwachting krijgt versie/reden. Verwachting vóór uitvoering vastleggen. Synthetische gevallen zijn geen gevalideerde juridische praktijkgevallen.

**Proeven.** Offline, synthetisch, verse opslag; op de Mac: `cd /Users/chrislehnen/Projecten/Definitie-app && PYTHONPATH=src .venv/bin/python …` (bijv. `ModularValidationService(get_toetsregel_manager(), None, None).validate_definition(begrip=…, text=…, ontologische_categorie=None, context={})` zoals in `test_v2_golden_int_more.py`, of de prompt-orchestrator om de INT-02-rendering vast te leggen). Bewaar commando, commit, invoer, verwachting/grond, werkelijke uitkomst, exitstatus. Geen live modelcalls, geen brede testsuite.

## 8. Wat al bewezen / te actualiseren / ontbrekend / open beleid (feitelijk, per vraag)

| Vraag | Bewezen | Te actualiseren | Ontbrekend | Open beleid |
|---|---|---|---|---|
| Q1 norm | ASTRA-tekst + Beslisregel/Afleidingsregel gelezen (§1); lokaal record voegt "voorwaarden", patronen en toetsvraag toe (§1-tabel) | Dossier v1 §2 "externe bron niet opnieuw bevestigd" is achterhaald | DBT §4.2 (Ross) niet gelezen; ASTRA-revisiegeschiedenis | Toepasselijkheid/uitzonderingen (afleidingsregel, lidmaatschapscriteria, modaliteit); type "interne structuur" ↔ "gehele definitie" |
| Q2 invoer | Alleen `definition_text` gedeclareerd; context/bron niet gebruikt door de evaluator | — | Wat context/bron/ontologie voor het functie-oordeel (criterium vs voorschrift) moeten leveren | Wat bij ontbrekende context (ESS-05 K-9 als precedent) |
| Q3 relaties | Record-reden koppelt paar aan ARAI-04; DEF-771 noemt ESS-04/ESS-05; INT-01 deelt `indien`-patroon | — | Concrete conflict/overlap-analyse ARAI-04, ESS-04, ESS-05, INT-01, STR-06 (doel), INT-08 | Eigenaarschap per normdoel |
| Q4 appgedrag | Servicegedrag 6 gevallen (11-09; code ongewijzigd); prompt-rendering (codelezing); geen INT-02-reden in UI-samenvatting | Dossier v1 §8 blijft geldig | UI-detail, opslag/snapshot, export, import, bewerken, gate; werkelijke promptuitvoer; echte modeluitvoer | — |
| Q5 voorstellen | — | — | Regeltekst, record, contract, meldingen, G/T/H-teksten, skillvervangingen | Evaluatorstrategie (judgment / AI-beoordeling naar ESS-03-patroon / deterministisch deel) |
| Q6 casussen | 6 historische + ASTRA-paar + Beslisregel-voorbeeld (Ppw) + Afleidingsregel-voorbeelden (stelselmatige dader, leeftijd) + claude-grensgevallen A/B + test/fixture-teksten | Verwachtingen onder een verduidelijkte norm | Grensgevallen criterium/voorschrift/discretie; aangeleverd vs gegenereerd; ontbrekende invoer | Besluiten voor Chris |
