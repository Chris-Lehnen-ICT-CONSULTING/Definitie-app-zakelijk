# INT-02 — Geen beslisregel · onderzoek onderzoekslijn A (v1)

25 september 2026 · DEF-771 (parent DEF-606) · uitvoerende onderzoekslijn A (schone Claude Code CLI-sessie, gestart door de Cowork-hoofdsessie) · fase **onafhankelijke eerste versie**. Onderzoek, geen normbesluit en geen implementatieopdracht. Niets gelezen uit `b-codex-cli/`.

**Labels.** [F] bronfeit · [B] vastgelegd besluit · [W] waarneming/proef · [I] interpretatie van A · [V] voorstel van A. Casussen: [`casusregister-a-v1.md`](casusregister-a-v1.md). Proeven: [`bewijs/`](bewijs/) — verwachtingen vooraf in [`bewijs/verwachtingen-a-v1.md`](bewijs/verwachtingen-a-v1.md), uitvoering in [`bewijs/proeflog-a-v1.md`](bewijs/proeflog-a-v1.md).

## 0. Startpositie, toegang en leesbasis

| Punt | Waarde |
|---|---|
| Leesbasis | HEAD `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3` [W]. **Afwijking:** de werkboom staat niet op `main` maar op de checkout-branch `onderzoek/DEF-772-INT-03-20260925`. De commit is wel gelijk aan de opgegeven main-HEAD en er zijn geen getrackte wijzigingen, dus de leesbasis is inhoudelijk dezelfde. |
| Hergebruik van historisch bewijs (`d68a98a9`) | `git diff d68a98a9 26f2374d -- src/toetsregels/regels/INT-02.json` is leeg: het record is ongewijzigd [W]. `judgment_review.py`, `modular_validation_service.py`, `json_based_rules_module.py`, `additional_patterns.py` en `runtime_contract.py` zijn **wel** gewijzigd (483+/56−; commits voor ESS-01/02/03/04, DEF-746/750/766/767). De evaluator heeft nog steeds geen INT-02-tak (`judgment_review.py:72-78`). Daarom is het oude bewijs niet automatisch hergebruikt: P1 heeft C01–C06 opnieuw gemeten en die uitkomsten zijn identiek (proeflog V7) [W]. |
| Toegang | Alle genoemde bestanden zijn leesbaar, op één na: **`src/services/definition/cleaning_service.py` bestaat niet**. Het werkelijke pad is `src/services/cleaning_service.py`. Niet volledig gelezen (bewust, want tijd): de ESS-04-, ESS-05-, INT-01-, samenhang- en overzichtsdossiers, de ESS-05-besluiten, de INT-01-besluitnotitie en -synthese v2, de productbedoeling, de DEF-625-bronaanvulling, `expert_review_tab.py`, `countability_assessment.py`, `INT-02.py`, `validators/INT_02.py` en `runtime_cases.yaml`. Daarvoor is de samenvatting in de feitenbasis gebruikt. Wel volledig gelezen: `ARAI-04-v1.md`, `INT-02-v1.md`, `judgment_review.py`, de relevante delen van `json_based_rules_module.py`, `modular_prompt_adapter.py`, `validation_view.py` en `definition_workflow_service.py::_evaluate_gate`, de records INT-02, STR-09 en INT-10, en de skillpassages. |
| Werkwijze | Geen agents, geen modelcalls, geen netwerk en geen repo-wijzigingen. Er is alleen geschreven in `a-claude-cli/`. Shell-omleidingen werden door de toolpermissie geweigerd. Daarom zijn stdout en exitstatus overgenomen uit de tooluitvoer (zie de beperking in de proeflog). |

## 1. Q1 — Norm, lokale aanvullingen, toepasselijkheid en uitzonderingen

### 1.1 Wat ASTRA waarborgt [F]

- **Regel:** "Een definitie mag niet geformuleerd worden als een beslisregel." `Type=gehele definitie`: het gaat om de functie van de hele definitie, niet om een woord.
- **Toelichting:** een beslisregel vraagt oordeelsvorming en is "niet 100% deterministisch", vaak omdat beleid "een discretionaire bevoegdheid" openlaat. Tegelijk geldt: "Uiteraard mag een definitie wel geformuleerd worden als een afleidingsregel … Sterker nog: een afleidbaar begrip MOET gedefinieerd worden in termen van een afleidingsregel."
- **Achtergrond:** de beslisregel is synoniem met de DEMO-"actieregel" ("richtlijn voor actor bij het afhandelen van coördinatie-event"). Die lijkt op Ross' *behavioral business rule*: "an obligation concerning conduct, action, practice, or procedure". De afleidingsregel lijkt op de *definitional rule*: "a definitional criterion that is necessarily true for each instance of a concept".
- **Voorbeeldpaar:** ONJUIST "eis die een organisatie **moet** ondersteunen …", JUIST "eis die een organisatie ondersteunt …". De redactieopmerking noemt het voorbeeld zelf "niet erg sprekend" en vraagt of de afbakening tegenover afleidings- en geldigheidsregels "voldoende omlijnd" is.
- **Beslisregel-pagina:** de definitie is "Algoritme waarvoor oordeelsvorming nodig is". Het voorbeeld is art. 45 lid 2 Ppw ("… tenzij hij van oordeel is dat … onevenredig zou worden benadeeld"). **Afleidingsregel-pagina:** stelselmatige dader, leeftijd. Afleiden "verandert de toestand van de wereld niet"; beslissen en beoordelen doen dat wel.

### 1.2 Interpretatie van het normdoel [I]

ASTRA onderscheidt **functie**, niet **zinsvorm**. Uit de drie pagina's volgen twee verboden functies en één toegestane functie:

1. **N-a: geen discretionaire beslissing in de definitie.** De uitkomst van "valt dit onder het begrip?" mag niet afhangen van een afweging of oordeel van een actor (Ppw: "tenzij hij van oordeel is …").
2. **N-b: geen gedragsvoorschrift of procedure als definitie.** De definitie schrijft niet voor wat iemand moet doen of hoe iets wordt afgehandeld (Achtergrond: actieregel, *obligation concerning conduct*). Het ASTRA-paar valt precies hieronder: "moet ondersteunen" maakt van een kenmerk een verplichting.
3. **Toegestaan en voor afleidbare begrippen vereist:** een deterministisch criterium dat voor elke instantie vaststaat (afleidingsregel of *definitional rule*), ongeacht of het met "indien", "mits" of "voor zover" wordt geschreven.

Hieruit volgt dat het ASTRA-voorbeeldpaar **wel** een INT-02-voorbeeld is, en niet alleen een ARAI-04-voorbeeld. De record-reden "verschilt uitsluitend in het modale werkwoord moet, wat de norm van ARAI-04 is" (`INT-02.json:44`) beschrijft het woordverschil juist, maar verklaart de functie niet. Het woord hoort bij ARAI-04, de verplichting bij INT-02. Dit is overlap, geen conflict (§3).

### 1.3 Lokale aanvullingen [F] en hun beoordeling [I]

| Lokale toevoeging | Beoordeling |
|---|---|
| "…geen beslisregels **of voorwaarden**" (uitleg) en "of onder welke voorwaarden het geldig is" (toelichting) | **Verruimt de norm tegen ASTRA in.** Een afleidingsregel *is* een voorwaardelijk criterium (stelselmatige dader: "drie maal … veroordeeld"). Een verbod op "voorwaarden" verbiedt dus wat ASTRA toestaat en voor afleidbare begrippen zelfs verplicht stelt. Dit is de kern van het DEF-771-bespreekpunt. |
| Toetsvraag "Bevat de definitie geen voorwaardelijke of normatieve formuleringen zoals beslisregels?" | Vraagt naar de vorm ("voorwaardelijk") en is dubbel ontkennend, waardoor "ja" betekent dat het in orde is. Niet in ASTRA. Mist de onderscheidende vraag (vaststaand criterium tegenover voorschrift of afweging). |
| Zeven patronen (`indien`, `mits`, `alleen als`, `tenzij`, `voor zover`, `op voorwaarde dat`, `in geval dat`) | Niet in ASTRA. P1 laat zien dat ze niet onderscheiden. Van 11 treffers zijn er 6 onder de ASTRA-lezing in orde. Van 7 onder de norm te verwerpen gevallen missen ze er 4 (C02, C13, C14, C15), waaronder het ASTRA-foutvoorbeeld zelf [W]. Ze zijn hooguit bruikbaar als leeshulp. |
| `type: "interne structuur"` tegenover ASTRA "gehele definitie" | De lokale typering suggereert een zinsbouwregel. ASTRA typeert de hele definitie, wat past bij een functieoordeel. [V]: "gehele definitie". |
| `brondocument: "ASTRA"` tegenover "DBT, 4.2" | Herkomst onvolledig. DBT §4.2 (Ross) is **niet gelezen**. Claims over Ross steunen alleen op de ASTRA-citaten. |
| Toelichting "Bron hiervan is vaak beleid" (INT-02) tegenover "wet of beleid" (Beslisregel) | Klein verschil. Discretie kan ook uit de wet komen (Ppw-voorbeeld). |

### 1.4 Toepasselijkheid en uitzonderingen

- **Toepasselijk** [I]: alle definities (geldigheid "alle"). De vraag is steeds welke functie de kern heeft, niet welk woord erin staat.
- **Noodzakelijke lidmaatschapscriteria** (bespreekpunt DEF-771), ook in voorwaardelijke zinsvorm (C04, C17, C19, C20): [I] deze vallen **niet** onder het verbod. Ze zijn *definitional rules*. Of "Getal dat even is indien …" een goede definitievorm is (kick-off, circulariteit, één zin), beoordelen ARAI-06, STR-01, INT-01 en ESS-05, niet INT-02. Wie dit onder INT-02 verbiedt, ondergraaft ESS-04 (toetsbare criteria) en ESS-05 (onderscheidende kenmerken). Dat constateerde dossier v1 §12 al. → besluit **B-2**.
- **Begripscriterium tegenover voorschrift of procedure** (bespreekpunt DEF-771): [V] het toetscriterium is **"staat het kenmerk voor elke instantie vast, of legt de tekst vast wat iemand moet doen of mag afwegen?"**. Signaalwoorden beslissen dit niet. "Gebruikt worden in een besluit" of "resultaat van een besluit zijn" maakt een definitie geen beslisregel (dossier v1 §13; C30).
- **Grensgevallen**:
  - Een rechtsgevolg- of grondslagdefinitie (C16, "boete die wordt opgelegd wanneer …") kan als kenmerk (grond) of als verplichting van het bestuursorgaan worden gelezen → **B-6**.
  - Een onbepaalde voorwaarde ("indien alle voorwaarden zijn vervuld", C24) is eerder een ESS-04/INT-10-probleem dan een beslisregel.
  - Een modaal werkwoord dat een vermogen uitdrukt ("kan") is ARAI-04-terrein (open nuance in `ARAI-04-v1.md` §1). Dat is geen verplichting en dus geen INT-02.
- **Niet onderbouwd als uitzondering:** een categorie-label (bijvoorbeeld "PROCES") maakt een procedurebeschrijving niet toelaatbaar. Een procesbegrip beschrijft *wat* het proces is, niet wat een actor *moet* doen.

## 2. Q2 — Invoer, onderbouwing, ontbrekende of strijdige informatie

[F] Het contract declareert alleen `definition_text` (`INT-02.json:37-39`). De evaluator leest alleen `ctx.cleaned_text`. Context verandert niets: C29 is identiek aan C03 (P1 V4) [W]. [I] Voor het onderscheid tussen criterium en voorschrift/discretie is de tekst meestal voldoende (C12, C14 en C15 zijn intrinsiek herkenbaar). Context of een bronpassage is **ondersteunend** in grensgevallen: C16, C25 en citaat tegenover eigen formulering.

**Veldrollenmatrix** (genereren-en-toetsen §A):

| Veld | Zelf toetsobject en criterium | Bewijs voor ander oordeel | Invoer bij generatie | Mag AI dit opleveren/wijzigen? | Herkomst, ontbrekend/conflicterend |
|---|---|---|---|---|---|
| Definitiezin (kern) | **Ja**: vaststaand criterium tegenover voorschrift/afweging | — | Resultaat | Ja, bij generatie. Bij toetsen nooit wijzigen | Leeg → **NB**, geen V (C06/C23) |
| Term | Nee | Leesbaarheid: een woord in de term is geen signaal (C21) | Verplicht | Nee | — |
| Organisatorische/juridische context, wettelijke basis | Nee | Ondersteunend: wijst op een procedure- of beleidsdomein (C25) | Ondersteunend. Zonder context mag het INT-02-oordeel wel (intrinsiek). Algemene contextplicht = ESS-05-K-9/CON-01, niet INT-02 | Nee, niet verzinnen | Strijdig → **OI** met één vraag |
| Definitiebronnen/bronpassage | Nee (CON-02) | Sterk ondersteunend: toont of de bron een afweging of voorschrift (Ppw) of een criterium bevat. **Een wettelijk voorschrift in de bron maakt het niet toelaatbaar om dat voorschrift in de kern over te nemen** | Ondersteunend. G mag het criterium uit de bron halen, niet de handelingsregel | Nee | Bron alleen met procedure → geen kern verzinnen (C33) |
| Ontologische categorie | Nee | Zwak: PROCES tegenover RESULTAAT helpt lezen, beslist niet | Ondersteunend | Nee (ESS-02: claim) | — |
| Bedoelde betekenis/toelichting | Nee | Ondersteunend: de plek waar een uit de kern gehaalde regel kan landen | Ondersteunend | AI mag een apart toelichtingsvoorstel doen (ESS-01-lijn) | — |
| Voorbeelden/tegenvoorbeelden/grensgevallen | Nee | Een tegenvoorbeeld dat op een afweging steunt verraadt discretie | Niet nodig | Voorstel, apart gemarkeerd | Gegenereerde voorbeelden zijn geen bevestiging |
| Synoniemen/homoniemen | Nee | Niet relevant voor INT-02 (reden: de functie hangt niet van de term af) | Niet nodig | — | — |
| Metadata/status/menselijk oordeel | Nee | Vastgelegd INT-02-reviewoordeel moet aan de tekstversie gebonden zijn (DEF-626) | — | Nee | Oordeel over een oude tekst is geen actueel oordeel |

## 3. Q3 — Relaties met andere regels

| Regel | Relatie | Conflict of overlap | Wie beslist |
|---|---|---|---|
| **ARAI-04 / ARAI-04SUB1** (modaliteit) | Het ASTRA-paar verschilt in "moet". P1: C02 en C14 geven ARAI-04 én SUB1 fail; INT-02 geeft geen signaal [W] | **Overlap**. ARAI-04 = woord of vorm (ook "kan"/vermogen), INT-02 = functie (verplichting). Verschil: "kan" (vermogen) valt niet onder INT-02, en een voorschrift zonder modaal werkwoord (C15) valt niet onder ARAI-04 | ARAI-04 over modale woordkeuze en de open vermogensnuance. INT-02 over voorschrift en discretie. De record-reden in INT-02 corrigeren (**B-5**) |
| **INT-01** (één zin/compact) | Deelt `\bindien\b`. INT-01 is `generic`/`scored` en faalt in P1 op 20 van 25 teksten, ook zonder `indien` [W] | Overlap met ruis. Een INT-02-vormverbod komt via INT-01 als scoreafkeur binnen. INT-01-voorstel A+B (woordlijst vervalt) ligt open bij Chris [B, open] | INT-01-besluit (DEF-770). Voor INT-02 alleen de vaststelling dat `indien` daar geen INT-02-grond is |
| **INT-10** (ontoegankelijke achtergrondkennis) | **Nieuw [W]:** `INT-10.json:15` bevat `\bindien\b`, evaluator `generic`, `automated`, `scored`. Alle 8 `indien`-teksten falen op INT-10, geen enkele tekst zonder `indien` faalt | **Verkapte INT-02-woordafkeur in een andere regel.** Voor de eigen norm van INT-10 (niet-openbare kennis) is dit een foutpositief (C04, C11, C17 en C26 vergen geen achtergrondkennis) | INT-10-eigenaar (DEF-606-regeldossier INT-10). [V] melden, niet hier besluiten (**B-7**) |
| **ESS-03** (G) | De ESS-03-instructie zegt "behoud inhoudelijk noodzakelijke namen **en voorwaarden**". De INT-02-instructie zegt "Vermijd voorwaardelijke formuleringen". Beide staan in dezelfde prompt (P2 W1/W4) [W] | **G-conflict op woordniveau.** Inhoudelijk geen conflict onder N-A1: noodzakelijke voorwaarden zijn criteria | Oplossen via de nieuwe INT-02-G (§5.2). ESS-03-besluit (DEF-766) blijft staan |
| **STR-09** | ✅-voorbeeld "Een persoon met een paspoort of, **indien** niet beschikbaar, een identiteitskaart" staat in dezelfde prompt (P2 W3) [W] | G-tegenstrijdig signaal voor het model. Onder N-A1 is het voorbeeld INT-02-conform (C26) | STR-09-eigenaar. Voor INT-02 lost de nieuwe G het op |
| **ESS-04** (toetsbaarheid) | G "Gebruik objectief toetsbare elementen (deadlines, aantallen …)". Toetsbare criteria komen vaak in voorwaardelijke vorm voor. Besluit N2: kwalitatieve criteria kunnen volstaan [B] | Overlap. Een verbod op voorwaarden **ondergraaft** ESS-04. C24 ("alle voorwaarden") is eerder ESS-04 | ESS-04 over toetsbaarheid. INT-02 alleen over functie |
| **ESS-05** (onderscheid/lidmaatschap) | Onderscheidende kenmerken zijn lidmaatschapscriteria | Overlap. Een verbod op voorwaarden raakt ESS-05. Geen conflict onder N-A1 | ESS-05-besluiten (K-1…K-9) blijven gelden |
| **ESS-01** (functie/doel) | Procedure en doel liggen dicht bij elkaar ("om … mogelijk te maken") | Overlap | ESS-01 over doel en gebruik. INT-02 over voorschrift en afweging |
| **STR-06** (doel) | Het ASTRA-paar bevat een doelbijzin. STR-06 blijft RR in P1 | Alleen overlap in het voorbeeld | STR-06 |
| **INT-08** (negatief) | "tenzij"/"niet" = uitzonderingsvorm. INT-08 faalt in P1 op C04, C05, C16 en C26 | Geen INT-02-relatie behalve de vorm | INT-08 |
| **STR-08, SAM-07** | STR-08-toelichting noemt "een opsomming van kenmerken **of voorwaarden**" in definities als normaal [F]. SAM-07 heeft het patroon "en indien nodig" | Bevestigt dat de regelset voorwaarden in definities elders als gewoon behandelt → inconsistent met INT-02 "of voorwaarden" | — |

## 4. Q4 — Feitelijk appgedrag per ingang

| Ingang | Invoer → transport → oordeel → opslag → weergave → vervolg | Bewijsniveau |
|---|---|---|
| **Uitsluitend toetsen** (service) | Tekst ongewijzigd (orchestrator geeft `None` als cleaning; `cleaned_text == text`) → `JudgmentReviewEvaluator` → altijd `review_required`, reden = toetsvraag, signalen = regexstrings, ook bij lege tekst → `rule_statuses["INT-02"]="review_required"`, telt in de dekking, niet in een score | **[W] P1**, 25 casussen, offline servicelaag |
| **Genereren** | Prompt bevat het INT-02-blok (letterlijk: P2 W1). Geen toetsvraag. De dode `IntegrityRulesModule` (met het ❌ "Toegang"-voorbeeld) is niet geregistreerd. In dezelfde prompt staan ESS-03 "behoud … voorwaarden" en STR-09 ✅ met `indien` → daarna opschoning (label/aanhef weg, punt erbij; geen behandeling van indien/mits/tenzij volgens de feitenbasis: grep 0 treffers) → toetsing van de opgeschoonde kandidaat zoals hierboven | **[W] P2** module-niveau. Volledige `build_prompt` en echte modeluitvoer **niet** gemeten |
| **Bewerken/hertoetsen** | Zelfde servicepad. Geen opschoning bij toetsen (INT-01-onderzoek 21-09) | Codelezing en feitenbasis. Geen eigen proef |
| **Import** | Valideert niet (INT-01-onderzoek 21-09) → geen INT-02-status tot hertoetsen | Feitenbasis. Niet opnieuw geverifieerd |
| **UI-weergave** | `validation_view.py:803-808`: de open reden verschijnt alleen voor ESS-01/02/04. **INT-02 verschijnt alleen als code** in de regel "🟠 Nog te beoordelen: …, INT-02, …" (`_statuslijst_regels`, r. 237-263; r. 862-864 slaat de uitleg-expander over voor statuslijnen). Reden en signalen van INT-02 zijn voor de gebruiker dus **niet zichtbaar**. De INT-10-afkeur op `indien` verschijnt wel als "❌/⚠️ INT-10 … Waarom niet geslaagd" | Codelezing. **Geen UI-test** |
| **Expertreview** | `expert_review_tab.py:1079`: "nog te beoordelen (bewijs ontbreekt; motiveer)" (feitenbasis). Geen INT-02-specifieke hulp | Feitenbasis. Niet gelezen |
| **Opslag/snapshot** | Geen INT-02-specifiek veld. Binding van een reviewoordeel aan de tekstversie is DEF-626 | Niet onderzocht |
| **Vaststellen** | `_evaluate_gate` (`definition_workflow_service.py:715-812`) kijkt naar context, CON-01/CON-02-blokkades, `validation_score` (None → blokkade) en `severity == "critical"` in `validation_issues`. **`review_required`-items van INT-02 spelen geen rol** [W, codelezing]. Een INT-10-violation kan via severity of score wél meetellen (severity niet gemeten) | Codelezing. Geen gateproef |
| **Export** | Geen INT-02-poort gevonden (feitenbasis) | Niet onderzocht |

**Foutsoorten (diagnose)** [I]:
- **Validatorfout:** de reden draagt geen passage en geen onderscheidende vraag; lege tekst krijgt RR in plaats van NB/not_evaluated.
- **Buurregelfout:** INT-10 (`indien` gescoord); INT-01 (ruis).
- **Instructie-/normconflict:** het lokale "of voorwaarden" tegenover ASTRA; G-conflict met ESS-03 en STR-09.
- **Transport- of weergavefout:** INT-02-reden en -signalen worden niet getoond.
- **Generatorfout:** niet vastgesteld; er is geen modeluitvoer gemeten.
- **Ontbrekende informatie:** DBT §4.2 en de ASTRA-revisie.
- **Onbesliste normkeuzes:** B-1 t/m B-6.

## 5. Q5 — Voorstellen

### 5.1 Norm (N) en record [V]

**Gemeenschappelijke norm N-A1** (vervangt `uitleg` en `toelichting`):

> **uitleg:** "Een definitie beschrijft wat het begrip is met kenmerken die voor elke instantie vaststaan; zij is geen beslisregel die de uitkomst aan een afweging of oordeel overlaat, en geen voorschrift over wat iemand moet doen of hoe iets wordt afgehandeld."
>
> **toelichting:** "Bij een beslisregel komt oordeelsvorming kijken: de uitkomst is niet volledig deterministisch, omdat wet of beleid een discretionaire bevoegdheid openlaat (bijvoorbeeld 'tenzij zij van oordeel is dat …'). Ook een gedragsvoorschrift of procedure ('moet', 'wordt afgewezen', 'beoordeelt binnen zes weken') hoort niet in een definitie. Een deterministisch criterium mag wel — ook in voorwaardelijke vorm met 'indien', 'mits' of 'voor zover' — en een afleidbaar begrip wordt juist met zo'n afleidingsregel gedefinieerd. Of een voorwaardelijke zin een goede definitievorm is, beoordelen andere regels. Dat een begrip het resultaat is van een besluit of in een besluit wordt gebruikt, maakt de definitie geen beslisregel."
>
> **toetsvraag:** "Legt de definitie vast wat het begrip is met criteria die voor elke instantie vaststaan, of schrijft zij een handeling of procedure voor of laat zij de uitkomst afhangen van een afweging of oordeel?"

Overige recordvelden:
- `type`: "gehele definitie".
- `brondocument`: "ASTRA (DBT, 4.2)".
- `goede_voorbeelden`: het bestaande ASTRA-JUIST plus "stelselmatige dader: persoon die in de vijf jaar voorafgaand aan het laatste feit drie maal wegens een misdrijf onherroepelijk is veroordeeld." (C10).
- `foute_voorbeelden`: het bestaande ASTRA-ONJUIST plus "weigering: besluit waarmee de bevoegde autoriteit een aanvraag afwijst, tenzij zij van oordeel is dat de aanvrager daardoor onevenredig zou worden benadeeld." (C12).
- `example_pair_reason`: "het ASTRA-paar verschilt in 'moet': de verplichting maakt de definitie een gedragsvoorschrift (INT-02); het modale woord is daarnaast ARAI-04. Beslisregelherkenning blijft een inhoudelijk oordeel."
- `herkenbaar_patronen`: behouden als **leeshulp**, aangevuld met signalen voor N-a/N-b die nu gemist worden: `\bvan oordeel\b`, `\bnaar het oordeel van\b`, `\b(acht|achten)\b`, `\bafweging\b`, `\bmoet(en)?\b`, `\bdient te\b`, `\bwordt (afgewezen|geweigerd|toegekend|verleend)\b`. Nadrukkelijk als signaal, nooit als afkeur.

Alternatief (minimaal): alleen "of voorwaarden" en de voorwaardenzin uit de toelichting schrappen en de toetsvraag vervangen. De rest blijft ongewijzigd.

### 5.2 Generatie-instructie (G) [V]

**Huidig** (`json_based_rules_module.py:377`): "Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als'". Met de uitleg: "Een definitie bevat geen beslisregels of voorwaarden." (P2 W1).
**Probleem:** het verbiedt een vorm die ASTRA toestaat en verplicht stelt. Het botst met ESS-03-G ("behoud … voorwaarden") en met het STR-09-✅-voorbeeld. Het kan leiden tot het stil weglaten van noodzakelijke criteria (C31). Het mist de werkelijke fouten (voorschrift, afweging).
**Vervanging:**

> "Beschrijf wat het begrip is met kenmerken die voor elke instantie vaststaan. Een noodzakelijk criterium of een deterministische afleiding hoort in de kern, ook als de bron het voorwaardelijk formuleert; schrijf het bij voorkeur als kenmerk ('geheel getal dat zonder rest door twee deelbaar is'), zonder het criterium weg te laten of te verzwakken. Neem geen voorschrift op over wat iemand moet doen of hoe een aanvraag of zaak wordt afgehandeld, en geen afweging die aan het oordeel van een persoon of instantie wordt overgelaten ('tenzij zij van oordeel is dat …'). Bevat de bron zo'n handelingsregel of discretionaire bevoegdheid, beschrijf dan het begrip zelf en laat de regel buiten de definitiezin; die kan hoogstens als afzonderlijk toelichtingsvoorstel. Verzin geen vast criterium om een afweging te vervangen. Geeft de beschikbare informatie alleen de procedure en niet wat het begrip is, lever dan hoogstens een herkenbaar voorlopige kandidaat."

**App vooraf:** term, bedoelde betekenis, context en bronpassages doorgeven, en de oorspronkelijke modeluitvoer vóór opschoning bewaren voor diagnose. **Toetsgevallen:** C04/C05/C11 (criterium behouden), C12/C13 (discretie weg, niets verzonnen), C03/C15 (procedure weg), C33 (onthouding). Een promptwijziging bewijst geen betere generatie (§6).

### 5.3 Toetsinstructie (T) en evaluatorstrategie [V]

**Opties** (geen model gekozen, DEF-815; geen nieuwe LLM-toets verplicht):

| Optie | Inhoud | Gevolgen |
|---|---|---|
| **O1 — judgment_review met INT-02-passagehulp** (ESS-04-patroon, DEF-767) | `_int02_reden`: een kop met de nieuwe toetsvraag, per getroffen passage de neutrale vraag, zonder treffer een expliciete waarschuwing dat een voorschrift ook zonder signaalwoord kan voorkomen. Lege kern → `not_evaluated` met reden in plaats van RR. UI toont de reden (zoals ESS-01/02/04) | Klein en deterministisch, geen kosten of privacyvragen. Het oordeel blijft menselijk. Lost de onzichtbaarheid en de misleidende vraag op, niet het gemiste signaal bij C13/C15 (deels wel via de extra patronen) |
| **O2 — AI-beoordeling naar het ESS-03/ESS-05-K-1-patroon** | Scoreloos, vier uitkomsten (V/VN/niet van toepassing → hier NB/OI + één vraag), letterlijke citaatcontrole, alleen aangeleverd materiaal, geen gate, geen herschrijving | Vergt een eigen besluit over prompt, model (DEF-815), goldset, kosten, privacy en foutbeleid (ADR-001). INT-02 is intrinsiek vaak goed te beoordelen, maar zonder goldset is de kwaliteit onbewezen |
| **O3 — deterministisch deel** | Alleen voor expliciete discretiemarkers ("van oordeel is", "naar het oordeel van") automatisch VN | **Afgeraden** [I]: ook een geciteerde bevoegdheid of een begrip *over* discretie ("discretionaire bevoegdheid: bevoegdheid waarbij het bestuursorgaan naar eigen oordeel …") zou falen. Hooguit als sterker signaal binnen O1 |

**Aanbeveling A:** nu O1. O2 als afzonderlijke latere keuze (**B-4**).

**T-tekst voor O1** (voorstel voor `judgment_review.py`, analoog aan `_ess04_reden`):
- Kop: "INT-02 — Nog te beoordelen: legt de definitie vast wat het begrip is (een criterium dat voor elke instantie vaststaat, eventueel in voorwaardelijke vorm), of schrijft zij een handeling of procedure voor of laat zij de uitkomst afhangen van een afweging of oordeel?"
- Per passage: "Te beoordelen passage: {passage}. Staat dit kenmerk voor elke instantie vast (toegestaan), of is het een voorschrift of een afweging? Dit signaal geeft nog geen inhoudelijk oordeel."
- Zonder signaal: "Geen signaalwoord gevonden. Een voorschrift of afweging kan ook zonder signaalwoord voorkomen; beoordeel de functie van de kern."
- Lege kern: status `not_evaluated`, reden "INT-02 — Niet beoordeeld: er is geen definitiekern om te beoordelen."

**Uitkomsten voor de reviewer en een eventuele O2** (gebruikersuitleg):
- V: "De definitie legt vaststaande kenmerken vast; een voorwaardelijke formulering is hier een criterium, geen beslisregel."
- VN (N-a): "De uitkomst hangt af van een afweging of oordeel ('…'); dat hoort in de regelgeving, niet in de definitie."
- VN (N-b): "De definitie schrijft voor wat iemand moet doen of hoe iets wordt afgehandeld ('…'), in plaats van te beschrijven wat het begrip is."
- OI: "Uit de tekst blijkt niet of '…' een vaststaand kenmerk of een toekenningsregel is. Vraag: …?"
- Technisch: "De INT-02-beoordeling kon niet worden uitgevoerd; er is geen inhoudelijk oordeel gegeven."

Toetsen wijzigt de tekst nooit [B, ARAI-06-verduidelijking]. Er is geen score (excluded/no_score) en geen gate [B, 15-09].

### 5.4 Begrensde terugkoppeling (H) — ontwerp onder DEF-638 [V]

- **Diagnose vóór advies:**
  - Werkelijke generatieovertreding: een voorschrift of afweging in de kern.
  - Instructie- of normconflict: de huidige "vermijd indien"-G of ESS-03-G.
  - Foutpositieve buurregel: INT-10 of INT-01 op `indien`.
  - Ontbrekend bewijs: C24, C25.
  - Technische storing.
  Een INT-10- of INT-01-fail op `indien` is **geen** grond voor een INT-02-herstel.
- **Herstelbaar met beschikbare gegevens:** een voorschrift uit de kern halen als de kern zonder voorschrift nog een begrip beschrijft (C03 → "verzoek om …"). Voorwaardelijke vorm → kenmerkvorm (C04 → C05) is een **stijlvoorstel**, geen INT-02-herstel.
- **Beschermd:** criteria, drempels en termijnen (C10/C11), bronbetekenis, term, context en gebruikersinvoer.
- **Stoppen bij:**
  - een voorstel dat een criterium laat vallen (C31);
  - een voorstel dat een afweging door een verzonnen criterium vervangt (C32);
  - een voorstel dat de reikwijdte verandert (C14);
  - een bron die alleen de procedure bevat (C33).
- **Limiet en hertoetsing:** maximaal één poging (DEF-638, nog niet geactiveerd). Na een wijziging INT-02 plus ESS-01, ESS-04, ESS-05, ARAI-04 en INT-01 opnieuw toetsen. Een oud RR-oordeel geldt niet voor de nieuwe tekst.
- **Gebruiker:** krijgt een voorstel naast de ongewijzigde originele tekst; aangeleverde tekst wordt nooit automatisch aangepast (C28). Toetsresultaat, conceptstatus, expertreview en vaststelling blijven gescheiden.

### 5.5 Skills en prompts: huidig → probleem → vervanging → toetsgeval [V]

| Vindplaats (huidig) | Probleem | Exacte vervanging | Soort | Toetsgeval |
|---|---|---|---|---|
| `json_based_rules_module.py:377` "Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als'" | Vormverbod tegen ASTRA in; G-conflict | G-tekst §5.2 | generatie | C04, C11, C12, C15 |
| `INT-02.json` `uitleg` (wordt in de prompt gerenderd) | "of voorwaarden" | N-A1-uitleg §5.1 | norm/generatie | C04, C10 |
| `~/.agents/skills/definitie-toetsregels/reference.md:63` "`\| INT-02 \| Geen beslisregel \| midden \| Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als' \|`" | Idem; skill toetst op woorden | "`\| INT-02 \| Geen beslisregel \| midden \| Geen voorschrift of afweging in de definitie; een vaststaand criterium mag, ook met 'indien' — zie references/int02-beslisregel.md \|`" | toets/reviewerhulp | C04 (V), C12 (VN) |
| `definitie-toetsregels`: geen `references/int02-*.md` | Er is geen regelcontract (wel voor CON-01/02 en ESS-01…04) | Nieuw `references/int02-beslisregel.md` in N/G/T/H-vorm (formaat: `ess03-eenheid-identiteit.md`): **N** = N-A1; **grenzen** = geen woordbewijs, lidmaatschapscriteria toegestaan, rechtsgevolg (B-6), geen score of gate; **G** = §5.2; **T** = toetsvraag + vier uitkomsten + formuleringen §5.3; **H** = §5.4. Voorbeelden: ✅ C10, C05, C19; ❌ C02 (ASTRA), C12 (Ppw), C15; grens C16, C24 | reviewerhulp | C02, C10, C12, C16, C24 |
| `~/.agents/skills/definitie-nederlandse-definities/reference.md:186` "- Voorwaardelijke formuleringen: `indien`, `mits`, `tenzij`, `alleen als`" (sectie "Vermijden") | Vormverbod; ook de pendant van de modale regel staat op r. 184 (niet r. 181 zoals in de feitenbasis) | "- Beslisregels en voorschriften: geen afweging die aan iemands oordeel wordt overgelaten ('tenzij … van oordeel is') en geen handelingsvoorschrift ('moet', 'wordt afgewezen'). Een vaststaand criterium mag, bij voorkeur als kenmerk ('geheel getal dat zonder rest door twee deelbaar is') in plaats van 'getal dat even is indien …' — laat het criterium niet weg (INT-02)." | generatie (skill) | C04→C05, C12, C31 |
| `definitie-toetsregels/SKILL.md:39` "Elke regel heeft een JSON-configuratie en een Python-validator" en "gewogen scoring" | Verouderd (.py-laag is restant; geen totaalscore [B]) | Buiten INT-02-scope; melden aan de skill-eigenaar | — | — |
| `integrity_rules_module.py` (`_build_int02_rule`, ❌ "Toegang …indien alle voorwaarden zijn vervuld") | Dode code met een tegen N-A1 in strijd zijnd voorbeeld (C24 is OI, niet VN) | Geen tekstvervanging. Verwijderen of expliciet als dood markeren is een afzonderlijke opdracht | — | C24 |
| `judgment_review.py:70-78` (reden = toetsvraag) | Geen passage en geen onderscheidende vraag | T-tekst O1 §5.3 | toets | C03, C12, C13, C06 |
| `validation_view.py:807` `("ESS-01","ESS-02","ESS-04")` | INT-02-reden niet zichtbaar | "INT-02" toevoegen aan de tuple (weergave-voorstel) | UI | C03 |
| `tests/unit/validation/test_v2_golden_int_more.py::test_int02_no_decision_rules_fail` | Naam "fail" suggereert VN; tekst is onder N-A1 OI (C24) | Naam en verwachting herijken na B-1. Geen wijziging nu | test | C24 |

## 6. Q6 — Beoogde kwaliteitswinst, effectevaluatie, risico's

**Beoogde winst** [V]:
- **T:** reviewers herkennen voorschriften en afwegingen (C02, C12–C15) en keuren criteria in voorwaardelijke vorm niet af (C04, C11, C17, C19, C20).
- **G:** minder voorschriften en afwegingen in gegenereerde kernen, **zonder** verlies van noodzakelijke criteria.
- **Keten:** geen verborgen scoreafkeur op `indien` via INT-10.
- **Onaanvaardbare verslechtering:** criteria die verdwijnen of verzwakken (C31), verzonnen criteria (C32), aangeleverde tekst die wordt gewijzigd.

**Nulmeting (beschikbaar, P1):**
- Signalen: 11 treffers, waarvan 3 onder N-A1 een VN aanwijzen. 4 VN-gevallen hebben geen signaal.
- UI: 0 van 25 toont een INT-02-reden (codelezing).
- INT-10: 8 `indien`-afkeuren, waarvan 6 onder N-A1 geen INT-02-fout zijn.

**Vergelijking vóór/na (ontwerp):**
1. **T-deterministisch:** P1 opnieuw draaien op dezelfde 25 casussen na O1. Criteria:
   - de reden bevat de passage en de nieuwe vraag;
   - C06/C23 → not_evaluated;
   - geen enkele V-casus krijgt een fail;
   - INT-10 faalt niet meer op `indien` (alleen als B-7 wordt uitgevoerd).
   Uitvoerbaar zodra er code is (eigenaar: Claude Code CLI-uitvoerder, reviewer Codex CLI, volgens de rolverdeling).
2. **T-menselijk:** twee beoordelaars met en zonder passagehulp op een blinde set (C02–C27 plus nieuwe, niet voor het ontwerp gebruikte gevallen), vergeleken met de vooraf vastgelegde N-A1-verwachting. Meet VN-herkenning en foutieve VN op criteria. Eigenaar: Chris (beoordelaars, toestemming). Pas na B-1/B-4.
3. **G:** echte generatie met een vastgelegd model, prompt- en normversie. Begrippen met een bron die een criterium bevat (stelselmatige dader, leeftijd), een bron met discretie (Ppw) en een bron met alleen een procedure; meerdere runs per variant. Blind beoordelen op: voorschrift of afweging in de kern (VN), criterium behouden, onthouding bij alleen-procedure. **Niet uitgevoerd; vergt autorisatie voor modelcalls.** Eigenaar: nog toe te wijzen; afhankelijk van B-1 en de uitvoering van §5.2.
4. **O2 (als gekozen):** goldset met onafhankelijke referentiebeoordeling, inclusief grensgevallen C16, C24 en C25. Modelovereenstemming is geen kwaliteitsbewijs.

**Risico's en bewijsgaten:**
- DBT §4.2 is niet gelezen en de ASTRA-revisie is onbekend.
- De juridische grensgevallen zijn synthetisch.
- De INT-10-severity en het gate-effect zijn niet gemeten.
- Er is geen UI-test en geen `build_prompt`-proef.
- Een nieuwe G kan het model laten doorslaan naar voorwaardelijke vormen die andere regels (INT-01, STR-01) laten falen. Dat moet de G-evaluatie laten zien.
- Status na een eventuele implementatie zonder effectbewijs: **geïmplementeerd; kwaliteitswinst nog niet vastgesteld**.

## 7. Proeven: uitgevoerd en niet uitgevoerd

| Proef | Status | Bewijs |
|---|---|---|
| P1 servicegedrag, 25 casussen (C01–C06 opnieuw, C10–C27, C29) | Uitgevoerd, exit 0, commit `26f2374d` | `bewijs/proef-p1-service.py`, `p1-invoer.json`, `p1-uitkomsten.json`, proeflog. Twee voorspellingsfouten (C21, C15) gedocumenteerd, geen codeafwijking |
| P2 promptrendering op module-niveau | Uitgevoerd, exit 0 | `bewijs/proef-p2-prompt.py`, `p2-uitkomsten.json`, proeflog |
| Volledige `build_prompt`, echte modelgeneratie, UI (Streamlit), opslag/snapshot, gate, import, export, expertreview | **Niet uitgevoerd**: niet nodig voor de kernclaims of niet geautoriseerd (modelcalls). Codelezing waar vermeld | — |
| C28, C30–C33 | Ontwerpcasussen, niet uitgevoerd | casusregister |

## 8. Besluiten voorgelegd aan Chris

| ID | Keuze | Voorkeur A | Alternatief en gevolg | Onderscheidende casus |
|---|---|---|---|---|
| **B-1** | Normduiding INT-02: functie (voorschrift/afweging) of vorm (voorwaardelijke formulering) | Functie, N-A1 (§5.1). "of voorwaarden" vervalt | Vorm handhaven → C04/C10/C11/C17/C19/C20 blijven "verdacht", in strijd met ASTRA's afleidingsregel. Botst met ESS-03/04/05 | C04, C10, C11 |
| **B-2** | Vallen noodzakelijke lidmaatschapscriteria in voorwaardelijke zinsvorm onder INT-02? | Nee. De vorm is voor INT-01/STR-01/ARAI-06 | Ja → INT-02 wordt een stijlregel en verdubbelt INT-01 | C04 tegenover C05, C17 tegenover C18 |
| **B-3** | Omvat INT-02 naast discretie (N-a) ook gedragsvoorschriften (N-b)? | Ja (ASTRA-Achtergrond en het eigen voorbeeldpaar) | Alleen N-a → het ASTRA-paar en C14/C15 zijn geen INT-02-fout meer (alleen ARAI-04 of niets) | C02, C15 |
| **B-4** | Evaluatorstrategie | O1 nu; O2 later als afzonderlijk besluit met goldset | O2 direct → besluit over model, kosten en goldset nodig (DEF-815, ADR-001). O3 afgeraden | C12, C13, C16 |
| **B-5** | Voorbeeldpaar en `example_pair_reason` | Paar behouden plus C10 ✅ en C12 ❌; reden corrigeren | Paar vervangen door een SRK-voorbeeld (redactiewens ASTRA) → eigen bronkeuze nodig | C02, C12 |
| **B-6** | Rechtsgevolg- of grondslagdefinitie ("boete die wordt opgelegd wanneer …") | Toegestaan als onderscheidende grond; formulering "opgelegd wegens …" | Als VN lezen → veel juridische begrippen raken in conflict | C16, C30 |
| **B-7** | `\bindien\b` in INT-10 (gescoord) en INT-01 | Melden aan de eigenaars van INT-10 en INT-01; buiten INT-02 besluiten | Laten staan → verborgen scoreafkeur op criteria blijft | C04, C11, C26 |
| **B-8** | Lege of ontbrekende kern | `not_evaluated`/NB in plaats van RR | RR houden → een reviewvraag over niets | C06, C23 |
| **B-9** | INT-02-reden zichtbaar in de UI | Ja (zoals ESS-01/02/04) | Nee → de reviewer ziet alleen de code | C03 |

Herstel van bestaand beleid (geen nieuw normbesluit): B-8, B-9 en het markeren van de dode `IntegrityRulesModule`. Een nieuw normbesluit is nodig voor B-1, B-2, B-3, B-5 en B-6. B-4 en B-7 zijn product- of eigenaarskeuzes.

## 9. Dekkingstabel (veertien dossieronderdelen)

| Onderdeel | Waar |
|---|---|
| 1 doel · 2 norm/besluiten · 3 toepasselijkheid | §1 |
| 4 context · 5 definitiebronnen · 6 ontologie · 7 aanvullingen | §2 (matrix) |
| 8 appgedrag · 10 status/score/poorten | §4 |
| 9 skills/prompts | §5.2, §5.5 |
| 11 proeven | §7, bewijs/ |
| 12 samenhang | §3 |
| 13 verbeteringen/review | §5, §8 (kruisreview volgt in de volgende fase) |
| 14 acceptatie/overdracht | §6, casusregister |

## Bronnen

- ASTRA: `gedeeld/bronnen/astra-INT-02-raw.wikitext`, `astra-Beslisregel-raw.wikitext`, `astra-Afleidingsregel-raw.wikitext` (citaten via `gedeeld/feitenbasis-v1.md` §1; opgehaald 25-09-2026).
- Records: `src/toetsregels/regels/INT-02.json`, `INT-10.json:15`, `INT-01.json:18,40-46`, `STR-09.json:13`, `STR-08.json` (toelichting), `SAM-07.json:8`.
- Code: `src/services/validation/evaluators/judgment_review.py:65-78,157-216`; `src/services/validation/modular_validation_service.py:843-912`; `src/services/prompts/modules/json_based_rules_module.py:228-281,340-377`; `src/services/prompts/modular_prompt_adapter.py:70-135,206-284`; `src/ui/components/validation_view.py:237-263,794-808,859-879`; `src/services/definition_workflow_service.py:715-812`; `src/services/orchestrators/definition_orchestrator_v2.py:313-317`; `src/services/cleaning_service.py:93`.
- Git: `git diff --stat d68a98a9 26f2374d -- …` (§0).
- Dossiers: `docs/analyses/def606-regeldossiers/INT-02-v1.md`, `ARAI-04-v1.md`. Feitenbasis: `gedeeld/feitenbasis-v1.md`.
- Skills: `~/.agents/skills/definitie-toetsregels/reference.md:63`, `references/ess03-eenheid-identiteit.md` (formaat); `~/.agents/skills/definitie-nederlandse-definities/reference.md:181-187`.
- Proeven: `bewijs/verwachtingen-a-v1.md`, `bewijs/proeflog-a-v1.md`, `bewijs/p1-uitkomsten.json`, `bewijs/p2-uitkomsten.json`.
