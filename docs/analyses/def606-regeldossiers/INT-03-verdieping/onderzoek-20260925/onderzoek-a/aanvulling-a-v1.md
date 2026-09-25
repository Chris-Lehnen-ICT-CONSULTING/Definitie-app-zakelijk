# INT-03 — onderzoek A (Cowork, Claude) — v1 — 25 september 2026

Onderzoeker A / coördinator. Leesbasis commit 26f2374d (main 23-09), branch onderzoek/DEF-772-INT-03-20260925. Bronnen: gedeeld/feitenbasis-v1.md (sha256 c160479a…), gedeeld/astra-INT-03-raw-20260925.txt, historisch dossier INT-03-v1.md, 7-09-dossier §INT-03, code op 26f2374d, skills op de Mac. Eigen proef: proef-a-v1.py → proefuitkomsten-a-v1.json (exit 0, offline gate actief, python 3.13.15). Opgeslagen vóór het lezen van bijdragen van B (Codex CLI) en C (Claude Code CLI).

Legenda: **F** bronfeit · **B** vastgelegd besluit · **W** waarneming/proef · **I** interpretatie · **V** voorstel.

## Q1 — Norm, lokale aanvulling, toepasselijkheid, uitzonderingen

**F (ASTRA, 25-09):** "Voor ieder voornaamwoord binnen een definitie dient duidelijk te zijn *waarnaar* verwezen wordt." Toelichting noemt persoonlijke én aanwijzende/betrekkelijke voornaamwoorden ('hij', 'het', 'zij', 'die', 'dit', 'dat'); geldigheid "alle", type "term", verplicht, prioriteit hoog, bron DBT §4.3 (Ross; niet gelezen). Het voorbeeldpaar contrasteert 'het' (onjuist) met 'die gebeurtenis' (juister) — dus: **herhaling van het zelfstandig naamwoord is de door de norm gedemonstreerde oplossing, en 'die' als betrekkelijk voornaamwoord komt driemaal in het juiste voorbeeld voor.**

**F (app-record) versus norm — lokale aanvullingen:**
1. `uitleg` is een verbodsformulering ("mogen geen voornaamwoorden bevatten waarvan niet direct duidelijk…"); inhoudelijk gelijk aan ASTRA, met het woord "direct" als lokale toevoeging.
2. `toelichting` voegt toe: "in dezelfde zin of zinsdeel" en "welk zelfstandig naamwoord". **I:** "dezelfde zin" is bij een definitie (INT-01: één zin) vrijwel altijd vervuld en dus geen echte eis; "zinsdeel" is een versmalling zonder ASTRA-grond die correcte constructies ("… waardoor die gebeurtenis …" — antecedent staat in een ander zinsdeel) ten onrechte zou raken. Voorstel: schrappen (Q5).
3. `herkenbaar_patronen` zijn eigen toevoegingen. Ze bevatten (a) echte voornaamwoorden: deze, dit, die, daarvan; (b) betrekkelijke bijwoorden: waarvan, waarmee, waarbij, daarbij — verwijzend, dus verdedigbaar als *signaal*; (c) niet-verwijzende woordgroepen: "in het kader" (ESS-01-signaal) en "inzienelijk maken" (typfout, geen voornaamwoord). Niet in de lijst maar wél in ASTRA: 'het', 'hij', 'zij', 'dat'; evenmin bezittelijk ('zijn', 'haar', 'hun') of 'ervan/hiervan/daarmee'. **W:** het foute ASTRA-voorbeeld (E02) geeft exact dezelfde signalen als het goede (E01); het onderscheidende woord 'het' geeft geen signaal (proef).
4. `type: interne structuur` en `geldigheid: gehele definitie` wijken tekstueel af van ASTRA ("term", "alle"); cosmetische drift (DEF-625-scope). Prioriteit hoog = ASTRA.

**Toepasselijkheid (I):** de regel geldt zodra de definitietekst een voornaamwoord bevat (persoonlijk, aanwijzend, betrekkelijk, bezittelijk, voornaamwoordelijk bijwoord). Zonder voornaamwoord is de regel niet van toepassing; dat is inhoudelijk een "voldoet / n.v.t.", geen "nog te beoordelen". Geldt bij genereren, uitsluitend toetsen, import, bewerken en herbeoordeling; bij vaststelling is het een inhoudelijke reviewvraag, geen aparte poort (geen INT-03-specifieke blokkade, in lijn met besluiten ESS-02/ESS-04).

**Uitzonderingen:**
- Onderbouwd: een betrekkelijk voornaamwoord direct na zijn antecedent ("persoon **die** wordt verdacht…", "teken **dat** een richting aangeeft") voldoet — dit is de aanbevolen genus-differentiaconstructie (skill nederlandse-definities; ASTRA-voorbeeld zelf). Herhaling van het zelfstandig naamwoord na een aanwijzend voornaamwoord ("die gebeurtenis") voldoet.
- Open (beleidskeuze): (i) verwijzing naar de definitie/het begrip zelf ("deze definitie", "dit begrip") — grammaticaal duidelijk, maar hoort inhoudelijk niet in een definitiezin (INT-06/toelichting); (ii) vooruitverwijzing (kataforisch) — grammaticaal mogelijk maar in definities zeldzaam; (iii) 'het' als voorlopig onderwerp ("waardoor het mogelijk is dat…") — geen verwijzing, mag geen signaal/afkeur geven.

## Q2 — Invoer en onderbouwing

| Gegeven | Rol voor INT-03 | Ontbrekend/tegenstrijdig |
|---|---|---|
| Definitiezin | Toetsobject; noodzakelijk en op zichzelf voldoende (regel is intern, geldigheid alle) | Leeg → VAL-EMP-001/technisch; INT-03 geeft dan geen oordeel (niet "nog te beoordelen") |
| Begrip/term | Ondersteunend: om te zien of een voornaamwoord naar het lemma zelf verwijst | Ontbrekend begrip belemmert INT-03 niet |
| Context (org/jur/wet) | Geen toetsobject. Mag de *bedoelde* referent duidelijk maken voor de reviewer, maar mag een structureel ambigue zin niet "zelfstandig duidelijk" verklaren | Context die een andere referent suggereert dan de zin → reviewvraag, geen automatische keuze |
| Definitiebronnen | Idem: bronpassage kan de oorspronkelijke referent tonen (bij uitsnijden gaat antecedent verloren) | Bronconflict apart registreren (CON-02), INT-03 blijft over de tekst |
| Ontologierelaties | Ondersteunend (rol maakt kandidaat plausibeler), nooit bewijs | — |
| Voorbeelden/praktijk/tegenvoorbeelden/grensgevallen | Zelf toetsobject met dezelfde leesbaarheidseis (antecedent mag daar over zinnen lopen); geen bewijs voor de definitiezin | — |
| Synoniemen/homoniemen | Niet relevant voor INT-03 (wel voor lezing van de referent bij homoniemen) | — |
| Toelichting | Mag intentie vastleggen; repareert de definitiezin niet | — |

## Q3 — Relaties met andere regels

- INT-04 (lidwoordverwijzing): zelfde normdoel (referentie duidelijk), ander woordsoort; overlap, geen conflict. Eén gezamenlijke reviewvraag "waarnaar verwijst X?" is denkbaar, maar buiten dit dossier.
- INT-01 (één begrijpelijke zin): geen conflict in de norm; het historische dossier stelt dat INT-01-patronen 'die' afkeuren — **niet door mij geverifieerd**; als dat klopt, straft INT-01 de constructie die INT-03 juist aanbeveelt (te controleren in INT-01-dossier, eigenaar DEF-770).
- STR-04 (kick-off gevolgd door toespitsing) en nederlandse-definities: de betrekkelijke bijzin is dé toespitsingsvorm; INT-03 mag die niet ontmoedigen.
- INT-06 (geen toelichting): "dit houdt in", "dit betekent" zijn primair INT-06-signalen; 'dit' daarin is geen INT-03-probleem.
- CON-CIRC-001 / ARAI-06: herstel door het lemma te herhalen als antecedent kan een cirkel-/herhalingssignaal geven; H moet dat tonen.
- ESS-05, ARAI-05: ambiguïteit kan onderscheidend vermogen raken; INT-03 beslist alleen over verwijsduidelijkheid.
Wie beslist: INT-03 over de duidelijkheid van de verwijzing; de herstelde zin wordt integraal hergetoetst (INT-01, CON-CIRC-001, STR-04).

## Q4 — Bewezen gedrag (proef op 26f2374d) en bewijsgaten

**Toetsing (W, 10 gevallen × routes manager/cache, identiek):** alle gevallen `review_required`, nooit `violation`, reden altijd de letterlijke toetsvraag ("Bevat de definitie voornaamwoorden zoals 'deze', 'dit', 'die'? Zo ja: is voor de lezer direct helder waarnaar ze verwijzen?"), signalen = patroonstrings zonder geciteerde passage. Concreet:
- E01 (ASTRA goed) en E02 (ASTRA fout): identieke uitkomst en signalen — de keten onderscheidt het normpaar niet.
- E04 ('het' enig voornaamwoord), E08 ('zijn'), E10 ('dat'): geen of alleen een bijwoord-signaal; de reviewer krijgt geen aanwijzing bij precies de woorden die ASTRA noemt.
- E05 (geen voornaamwoord): toch `review_required` — de dekking toont een open oordeel waar de regel niet van toepassing is.
- E09 ('deze definitie'): recordpatroon vuurt, additional-patroon niet: de negatieve lookahead in additional_patterns.py is dood gewicht zolang het record zelf `\bdeze\b` bevat.
Dit actualiseert het historische bewijs (11-09) op de gewijzigde keten na DEF-766/767: de "altijd review"-werking is ongewijzigd.

**Generatie (W):** de live INT-03-blok in de prompt (JSONBasedRulesModule, exacte tekst in proefuitkomsten-a-v1.json → prompt.blok_met_voorbeelden) bestaat uit naam, `uitleg`, instructie "Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent in dezelfde zin" en het ASTRA-paar als ✅/❌. **Maar:** `PromptOrchestrator._get_active_modules` (prompt_orchestrator.py r. 461–465, DEF-123) activeert `integrity_rules` alleen bij juridische of wettelijke context. Proef: geen context → niet actief; alleen organisatorische context → niet actief; juridisch of wettelijk → actief. **Gevolg (I): bij generatie zonder juridische/wettelijke context krijgt het model géén INT-03-instructie (en geen enkele INT-regel), terwijl ASTRA INT-03 als verplicht met geldigheid "alle" stelt.** Dit is een appbrede keuze (DEF-123) die alle INT- en SAM-regels raakt; dit dossier signaleert, beslist niet over de andere regels.
Statisch: `IntegrityRulesModule` wordt nergens geïnstantieerd (alleen definitie + export); de legacy loader komt alleen in commentaar voor; `validators/INT_03.py` en `regels/INT-03.py` worden nergens geïmporteerd. De vier `get_generation_hints` van de legacy validator (o.a. "Herhaal liever het zelfstandig naamwoord…") bereiken de prompt dus niet.

**Skills (F):** definitie-toetsregels/reference.md r. 64 geeft alleen de korte instructie zonder "dezelfde zin" en zonder uitzondering; SKILL.md heeft geen INT-03-contract (wel voor CON-01/02, ESS-01–04). definitie-nederlandse-definities/reference.md r. 185 zet 'deze/dit/die/dat zonder duidelijk antecedent' onder "Vermijden" en beveelt elders de betrekkelijke bijzin aan — consistent met de norm, maar de twee passages verwijzen niet naar elkaar.

**Niet bewezen (bewijsgaten):** volledige `build_prompt` met echte UnifiedGeneratorConfig/UI-route (alleen moduleselectie en blokrendering getest); UI-weergave van reden/signalen voor INT-03 (validation_view.py alleen gelezen); opslag van een reviewbesluit per INT-03-signaal (DEF-626-scope); export; modelnaleving van de instructie (geen live calls); of INT-01 werkelijk 'die' afkeurt.

## Q5 — Voorstellen (regeltekst, app, skills/prompts)

### 5.1 Regelrecord (src/toetsregels/regels/INT-03.json) — V
- `uitleg` → "Voor ieder voornaamwoord in de definitie is direct duidelijk waarnaar het verwijst." (ASTRA-getrouw, positief geformuleerd.)
- `toelichting` → "Persoonlijke, aanwijzende, betrekkelijke en bezittelijke voornaamwoorden ('hij', 'het', 'zij', 'die', 'dat', 'dit', 'deze', 'zijn', 'haar', 'hun') en voornaamwoordelijke bijwoorden ('daarvan', 'waarbij') verwijzen naar iets in de definitie. De lezer moet zonder context kunnen bepalen welk zelfstandig naamwoord bedoeld is. Een betrekkelijk voornaamwoord direct na zijn antecedent ('persoon die …', 'teken dat …') voldoet. Zijn er meer kandidaten, herhaal dan het zelfstandig naamwoord ('die gebeurtenis' in plaats van 'het')." Schrap "in dezelfde zin of zinsdeel". Alternatief (behoud): "dezelfde zin" laten staan als toelichting bij INT-01 — geen normeis.
- `toetsvraag` → "Welke voornaamwoorden bevat de definitie en naar welk zelfstandig naamwoord verwijst elk daarvan? Is dat voor de lezer zonder context eenduidig?"
- `herkenbaar_patronen` → verwijder "\\bin het kader\\b" en "\\binzienelijk maken\\b"; voeg toe: "\\b(hij|zij|dat|zijn|haar|hun|ervan|hiervan|daarmee|daarop)\\b" en, bewust apart met lagere zekerheid, "\\bhet\\b(?=\\s+(kan|wordt|is|moet|volledig|geheel|mogelijk))" als signaal voor 'het' als voornaamwoord (lidwoordgebruik uitsluiten is niet betrouwbaar; vandaar alleen signaal, nooit oordeel). Verwijder de dubbele regel in additional_patterns.py of maak het record-patroon `\bdeze\b(?!\s+(begrip|definitie|regel))` — één plek.
- `example_pair_reason` blijft (patroon vuurt op het goede voorbeeld); voeg als goed voorbeeld toe "persoon die wordt verdacht van een strafbaar feit" en als fout voorbeeld "handeling van een medewerker aan een collega waarbij deze vertrekt".
- `type`/`geldigheid` conform ASTRA ("term", "alle") → DEF-625.

### 5.2 Toetsingsmechanisme (T) — opties, keuze voor Chris (Q6)
Huidig: `judgment_review` generiek: altijd "nog te beoordelen" met de toetsvraag. Drie opties:
- **T-a Verbeterde reviewhulp (minimaal):** eigen tak `_int03_reden` in judgment_review.py naar het patroon van ESS-01/02/04 (`_reden_met_passages`): per gevonden voornaamwoord de passage citeren met de vraag "Naar welk zelfstandig naamwoord verwijst '<woord>'? Noem de kandidaten." Zonder signaal: "Geen voornaamwoordsignaal gevonden; controleer 'het', 'zijn', 'haar', 'hun' handmatig" (eerlijk over de detectiegrens). Uitkomst blijft review_required, scoreloos. Winst: reviewer ziet wáár te kijken; verlies: E05 blijft ten onrechte open.
- **T-b Reviewhulp + n.v.t.-uitkomst:** als T-a, maar zonder enig (uitgebreid) signaal → `not_applicable`/`pass` met reden "geen voornaamwoord aangetroffen". Risico: gemiste 'het'/'zijn' worden stil groen (E04/E08 zouden zonder uitgebreide patronen pass worden). Alleen verantwoord mét de uitgebreide patroonlijst én zichtbare tekst "automatische woordcontrole, geen betekeniscontrole".
- **T-c AI-beoordeling zoals ESS-03 (DEF-766-patroon):** aparte evaluator met vier scoreloze uitkomsten: voldoet / voldoet niet (met het voornaamwoord en de kandidaat-antecedenten) / niet van toepassing (geen voornaamwoord) / onvoldoende informatie (precies één vraag: "Verwijst 'deze' naar de medewerker of de collega?"). Alleen op de definitietekst, prompt-/modelversie vastgelegd, geen gate, geen herschrijving. Dit is een nieuw productbesluit (ADR-001: prompt/model/goldset/kosten/foutbeleid), niet door onderzoekers te nemen.
In alle opties: geen INT-03-cijfer, geen aparte vaststelblokkade; technische fout apart (`error`); lege tekst geen INT-03-oordeel.

Meldingstekst (V, voor T-a/T-c, gebruikersgericht): "INT-03 — Nog te beoordelen: '{woord}' in '…{passage}…' kan verwijzen naar {kandidaten}. Kies de bedoelde betekenis of herhaal het zelfstandig naamwoord." / "INT-03 — Voldoet: elk voornaamwoord verwijst eenduidig ({woord} → {antecedent})." / "INT-03 — Niet van toepassing: de definitie bevat geen voornaamwoord."

### 5.3 Generatie-instructie (G) — exacte vervangingen
- json_based_rules_module.py `instruction_map["INT-03"]` (r. 378), huidig: "Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent in dezelfde zin" → **V:** "Laat elk voornaamwoord ('die', 'dat', 'deze', 'dit', 'het', 'zijn', 'haar', 'hun') ondubbelzinnig naar één zelfstandig naamwoord in de definitie verwijzen; zet een betrekkelijke bijzin direct achter het woord waarop zij slaat (persoon die …) en herhaal bij twijfel het zelfstandig naamwoord (die gebeurtenis, niet het)". Probleem met de huidige tekst: 'het'/'dat'/bezittelijk ontbreken; "dezelfde zin" is loos; de aanbevolen constructie wordt niet genoemd, terwijl de skill nederlandse-definities 'die/dat' onder "Vermijden" zet — het model krijgt twee signalen die elkaar lijken tegen te spreken.
- JSON `uitleg`/voorbeelden: zie 5.1 (de prompt rendert die letterlijk; het extra goede voorbeeld toont de toegestane bijzin).
- prompt_orchestrator.py `_get_active_modules` (r. 461–465): **beleidskeuze K3** — (a) `integrity_rules` altijd activeren (ASTRA: INT-regels gelden altijd; kost promptlengte, raakt ook INT-01…INT-10), (b) alleen INT-03 (en evt. INT-04) buiten juridische context tonen via een kleine "altijd-tonen"-lijst zoals `_CONTEXTVRIJE_REGELS` bij CON-02, (c) huidige keuze handhaven (dan is de instructie in de meeste generaties afwezig en is G de facto uitsluitend de grammatica-/skillkennis van het model). Aanbeveling A: (b) als smalle stap, (a) als apart DEF-123-besluit.
- Skill definitie-toetsregels/reference.md r. 64 → "| INT-03 | Duidelijke voornaamwoord-verwijzing | **hoog** | Laat elk voornaamwoord (die, dat, deze, dit, het, zijn, haar, hun) eenduidig naar één zelfstandig naamwoord in de definitie verwijzen; betrekkelijke bijzin direct na het antecedent is goed, herhaal anders het zelfstandig naamwoord |". SKILL.md: korte INT-03-alinea onder Scoring: "INT-03 krijgt geen cijfer; uitkomst per voornaamwoord: voldoet / voldoet niet (kandidaten) / n.v.t. / nog te beoordelen; een betrekkelijke bijzin is geen overtreding; herstel alleen op verzoek en zonder het lemma in te voegen."
- Skill definitie-nederlandse-definities/reference.md r. 185 → "Impliciete verwijzingen: `deze`, `dit`, `die`, `dat`, `het`, `zijn/haar/hun` zonder eenduidig antecedent (een betrekkelijke bijzin direct na het antecedent — `persoon die …` — is juist de aanbevolen vorm, zie Bijzinnen)".

### 5.4 Terugkoppeling/herstel (H) — begrensd
- Diagnose vóór herstel: echte overtreding (E02/E07/E08) · instructie-/normconflict (INT-01 keurt 'die' af?) · foutpositieve signaalhulp (E01/E06/E10: signaal op correcte bijzin) · ontbrekend bewijs (E04: geen signaal maar wel fout) · technische fout.
- Toegestaan herstel (alleen op verzoek, DEF-638): vervang het voornaamwoord door het bedoelde zelfstandig naamwoord als precies één kandidaat is bevestigd (door gebruiker of ondubbelzinnige zinsbouw); anders stel de vraag. Beschermd: betekenis, bronwoorden, noodzakelijke namen; nooit het lemma invoegen als antecedent (CON-CIRC-001/ARAI-06), nooit de zin splitsen (INT-01), nooit een bijzin schrappen om een signaal weg te krijgen.
- Na herstel: integrale hertoets (INT-01, CON-CIRC-001, STR-04, ESS-05). Maximaal één herstelpoging; daarna open laten met vraag.

## Q6 — Kwaliteitswinst, effectevaluatie, risico's, besluiten

**Beoogde winst.** T: reviewers zien per voornaamwoord de passage en kandidaten en krijgen geen open oordeel bij definities zonder voornaamwoord (E05); fouten die ASTRA expliciet noemt ('het') worden niet meer stil gemist. G: gegenereerde definities gebruiken de aanbevolen bijzinconstructie en herhalen het zelfstandig naamwoord bij meerdere kandidaten; in generaties zonder juridische context is er überhaupt een INT-03-instructie. Behoudcriteria: correcte bijzinnen (E01/E06/E10) mogen na wijziging nooit "voldoet niet" krijgen; geen extra INT-01/CON-CIRC-signalen door herstel; geen betekenisverlies.

**Vergelijking vóór/na (ontwerp).** Nulmeting T = proefuitkomsten-a-v1.json (alles review_required, signalen zoals gemeten). Na T-a/T-b/T-c: zelfde tien gevallen plus vijf niet voor het ontwerp gebruikte gevallen (aan te leveren door B/C of Chris), verwachting per geval in de casustabel hieronder; beoordeling van de motiveringstekst door een mens zonder kennis van de variant. G: pas meetbaar met geautoriseerde modelruns (vast model, promptversie oud/nieuw, ≥5 begrippen × ≥3 runs, blinde beoordeling op INT-03 én INT-01/CON-CIRC); nu niet uitvoerbaar — eigenaar: Chris (autorisatie) / uitvoerende sessie na implementatie; afhankelijkheid: besluit K3 en implementatie-PR. Reviewhulp: gebruikersproef met twee reviewers, met/zonder passagehulp, op E02/E04/E07/E08 — eigenaar Chris, moment na T-implementatie.
Status na eventuele implementatie zonder dit bewijs: **geïmplementeerd; kwaliteitswinst nog niet vastgesteld.**

**Casusregister A (IDs stabiel; hist. IDs P/N/G en INT-03-bewijs-v1 niet hernummerd).** Kolommen: G = verwacht gedrag van een generator die de nieuwe instructie volgt; T = normoordeel (nieuw) naast huidig (alles review_required); H = toegestane herstelactie.

| ID | Invoer (term: tekst) | G | T nieuw (T-a/T-c) | H | Bewijs |
|---|---|---|---|---|---|
| INT03-A-E01 | context: … waardoor **die gebeurtenis** … | zo formuleren | voldoet (T-c) / review met passage 'die' (T-a) | geen | proef: review_required, sig die |
| INT03-A-E02 | context: … waardoor **het** … | niet zo; 'die gebeurtenis' | voldoet niet: 'het' → geheel/omgeving/gebeurtenis | vervang door 'die gebeurtenis' na bevestiging | proef: review_required, sig identiek aan E01 |
| INT03-A-E03 | regeling: regeling waarbij **deze** afspraak geldt | niet zo | voldoet niet: 'deze afspraak' zonder antecedent | vraag welke afspraak; geen automatisch herstel | proef: review_required, sig deze/waarbij |
| INT03-A-E04 | vastlegging: … waardoor **het** wordt bewaard | niet zo | voldoet niet: 'het' zonder antecedent | vraag | proef: review_required, géén signaal |
| INT03-A-E05 | toezicht: controle op naleving … | n.v.t. | n.v.t./voldoet (geen voornaamwoord) | geen | proef: review_required (onterecht open) |
| INT03-A-E06 | verdachte: persoon **die** wordt verdacht … | zo formuleren | voldoet (bijzin direct na antecedent) | geen | proef: review_required, sig die |
| INT03-A-E07 | overdracht: … collega waarbij **deze** vertrekt | niet zo; noem medewerker/collega | voldoet niet: kandidaten medewerker, collega | vraag; na keuze vervangen | proef: review_required, sig deze/waarbij |
| INT03-A-E08 | prijsafspraak: … waarbij **zijn** prijs … | niet zo | voldoet niet: 'zijn' → aanbieder/afnemer | vraag | proef: review_required, sig alleen waarbij |
| INT03-A-E09 | begrip: term waarvoor **deze** definitie geldt | vermijden (toelichting) | grensgeval: verwijzing duidelijk; INT-06-signaal | geen INT-03-herstel | proef: review_required, sig deze (record), niet additional |
| INT03-A-E10 | pijl: teken **dat** een richting aangeeft | zo formuleren | voldoet | geen | proef: review_required, géén signaal |
| INT03-A-E11 (ontwerp, niet uitgevoerd) | vergunning: besluit waardoor **het** mogelijk is een activiteit uit te voeren | toegestaan ('het' voorlopig onderwerp) | voldoet (geen verwijzing) | geen | niet uitgevoerd — test tegen foutpositieve 'het'-detectie |
| INT03-A-E12 (ontwerp) | leeg: "" | — | geen INT-03-oordeel (VAL-EMP-001) | — | niet uitgevoerd |
| INT03-A-E13 (ontwerp, aangeleverde tekst = E07) | import van E07 ongewijzigd | — | zelfde oordeel als E07; tekst blijft ongewijzigd | herstel alleen op verzoek | dezelfde norm voor gegenereerd en aangeleverd |

**Risico's/bewijsgaten:** patroonuitbreiding met 'het'/'zijn' geeft nieuwe foutpositieven (lidwoord, 'zijn' als werkwoord) — daarom nooit oordeel, alleen passagehulp; T-c vraagt model-/promptversiebeheer en goldset (DEF-766-ervaring hergebruiken); K3 raakt promptlengte en alle INT/SAM-regels; UI/opslag niet getest.

**Besluiten voor Chris:**
- K1 Normtekst: ASTRA-getrouwe uitleg/toelichting zonder "dezelfde zin/zinsdeel" (aanbevolen) of behoud lokale versmalling.
- K2 Toetsmechanisme: T-a (reviewhulp met passages, altijd open), T-b (idem + n.v.t. zonder signaal), T-c (AI-beoordeling zoals ESS-03). Aanbeveling A: T-a nu als herstel binnen bestaand beleid; T-c als afzonderlijk nieuw besluit, pas na ESS-03-evaluatie.
- K3 Generatie: INT-03-instructie altijd in de prompt (smal, zoals CON-02) of hele INT-module altijd of huidige DEF-123-keuze handhaven.
- K4 Patroonlijst opschonen en uitbreiden (herstel bestaand beleid: signalen zijn hulp, geen bewijs) — inclusief één plek (record óf additional_patterns).
- K5 Herstelbeleid: vervanging alleen bij één bevestigde kandidaat; nooit lemma-invoeging; één poging.
- K6 Skills: reference.md r. 64 en nederlandse-definities r. 185 vervangen (bestaand beleid: skill volgt JSON) — kan onafhankelijk van K2/K3.
Bestaand beleid herstellen: K1 (ASTRA-getrouwheid, DEF-625), K4, K6, T-a. Nieuw normbesluit: T-b/T-c, K3, K5.

## Dekking Q1–Q6 / dossieronderdelen
(1) doel/betekenis Q1 · (2) norm/besluiten Q1, Q6 · (3) toepasselijkheid Q1 · (4) context Q2 · (5) bronnen Q2 · (6) ontologie Q2 · (7) aanvullingen Q2 · (8) app Q4, 5.2 · (9) skills/prompts Q4, 5.3 · (10) status/score/poorten 5.2 · (11) proeven Q4, casusregister · (12) samenhang Q3 · (13) verbeteringen Q5 · (14) acceptatie casusregister, Q6.
Niet gedekt/ontbrekend bewijs: UI-weergave, opslag reviewbesluit, export, volledige build_prompt, modelnaleving, INT-01-'die'-claim.
