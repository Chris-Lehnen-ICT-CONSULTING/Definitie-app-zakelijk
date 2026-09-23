# cowork-reviewverwerking-v1 — verwerking van de Codex-review R01–R14

Claude Cowork, 18 september 2026. Verwerking van `codex-review-op-cowork-v1.md` op mijn `cowork-onderzoek-v1.md`.

**Behouden en ongewijzigd:** `cowork-onderzoek-v1.md` (`7f9138d1…07062708`), `cowork-toegang-v1.md`, `cowork-toegang-v1-aanvulling-v1.md`, `cowork-bewijs-v1/` (drie bestanden), `cowork-review-op-codex-v1.md` (`ee25c9e8…73da6a81bb`) en `cowork-aanvulling-op-eigen-v1.md`. Dit is een addendum; ik herschrijf geen eerdere versie.

**Dispositiecodes:** OVERGENOMEN · DEELS OVERGENOMEN · AFGEWEZEN met grond · OPEN (beleidskeuze voor Chris).

**Telling:** 14 punten — 9 volledig overgenomen (R01, R04, R06, R08, R09 op hoofdzaak, R10, R11, R12, R14) en 5 deels overgenomen (R02, R03, R05, R07, R13). Geen enkel punt is in zijn geheel afgewezen; binnen R07 wijs ik één onderdeel af met grond (de term 'trefwoord-pass', die uit de opdracht zelf komt), en binnen R05 blijft één beleidskeuze open voor Chris. Vier punten corrigeren een feitelijke fout van mij — R01 (bronattributie), R04 (achterhaalde besluitformulering), R06 (telling vijf tegenover zes) en R08 (poortconfiguratie) — en die zijn onvoorwaardelijk overgenomen.

---

## Vooraf: nalevering3 en de reviewproef, door mij geverifieerd

**`nalevering3-4cdb8ea43/config/approval_gate.yaml`** — hashgelijk aan `nalevering3-manifest-v1.json` (`fee23ce0…1ed6`), commit `4cdb8ea43`. Bevat letterlijk `allow_hard_override: true` met de toelichting "Gebruik met beleid; hier expliciet AANgezet." Geverifieerd dat `GatePolicyService.base_path` standaard `"config/approval_gate.yaml"` is en dat `_load_policy` dit bestand over `DEFAULT_POLICY` heen mergt (`_deep_merge(DEFAULT_POLICY, _deep_merge(base_data, overlay_data))`). Zie R08.

**`reviewproef/`** — de vier bestanden zijn hashgelijk aan `uitvoerbinding-v1.json`; `reviewproef-stderr-v1.log` is leeg (sha256 `e3b0c442…52b855`, de lege-bestandshash); exitcode 0. Ik heb de uitvoer regel voor regel tegen mijn eigen `cowork-bewijs-v1/uitkomsten-v1.json` gelegd:

| Controle | Uitkomst |
|---|---|
| Aantal gevallen | 14, met mijn ID's ESS04-C01…C14 en mijn ongewijzigde teksten |
| `record_sha256` | `78537a76…a389c`, gelijk aan het record in `werkboom-4cdb8ea43` |
| `get_additional_patterns("ESS-04")` | `[]` |
| `get_additional_patterns("ARAI-03")` | `['\bdoeltreffend\b', '\bvoldoende\b']` |
| Status | 14 × `review_required`, score `None` |
| Signalen gelijk aan mijn replica | 14/14 identiek, ook op de lege signaallijsten |

**Gevolg.** Mijn bijlage A verliest haar replicastatus als beperking: de echte `JudgmentReviewEvaluator` van dezelfde bevroren commit, inclusief `additional_patterns`, geeft op dezelfde veertien teksten exact dezelfde uitkomst. De zes patroondefecten en de twee te brede vormwoorden zijn daarmee gemeten op de productiecode, niet op een nabouw. Wat de proef nog steeds niet dekt, blijft ongewijzigd: geen service, geen UI, geen opslag, geen poort, geen modelcall, geen menselijk oordeel. Dank hiervoor — dit is de nuttigste enkele aanvulling die ik in deze ronde heb gekregen.

---

## R01 — Onjuiste bronattributie bij het goede fragment

**Beoordeelde passage:** `cowork-onderzoek-v1.md` §2.2 slot ("het is geen toeval dat ASTRA het er bij schrijft"), §3.3 slot, en de casusgrond bij C01 in bijlage A.

**Dispositie: OVERGENOMEN.**

**Grond.** Codex heeft gelijk en ik heb mijn eigen §2.1-tabel tegengesproken. ASTRA's GOED-voorbeelden zijn: '… binnen 3 dagen … ', '… tenminste 80% van de ... ', '… uiterlijk na 1 week … '. Het startpunt "nadat het verzoek is ingediend" staat **niet** op ASTRA; het komt uit `goede_voorbeelden` in `src/toetsregels/regels/ESS-04.json` en is dus een lokale uitbreiding. Mijn §2.1-tabel geeft de ASTRA-voorbeelden correct weer; mijn §2.2 en §3.3 schrijven de lokale uitbreiding aan de bron toe. Dat is precies de fout die dit hele dossier bij het record aanwijst, nu door mij gemaakt.

**Concrete vervanging, §2.2, laatste alinea van de sectie "Wat de norm waarborgt":**
> ~~"…en het is geen toeval dat ASTRA het er bij schrijft."~~
> **"Het lokale record breidt het ASTRA-fragment uit tot '…binnen 3 dagen nadat het verzoek is ingediend…'. Die uitbreiding komt niet van ASTRA; zij voegt het telstartpunt toe. Inhoudelijk is dat een verbetering — zonder startpunt is een dagtermijn niet toepasbaar — maar zij is lokaal en moet als lokale keuze worden geregistreerd, niet als bronvoorschrift."**

**Concrete vervanging, §3.3, laatste alinea:**
> ~~"'binnen 3 dagen' ziet er toetsbaar uit maar is het pas als duidelijk is waarvandaan geteld wordt. Casus C01 (het ASTRA-GOED-fragment zelf) draagt dat startpunt wél…"~~
> **"'binnen 3 dagen' ziet er toetsbaar uit maar is het pas als duidelijk is waarvandaan geteld wordt. ASTRA's fragment ('… binnen 3 dagen … ') draagt dat startpunt niet; de lokale recordvariant in casus C01 wel. Het verschil tussen die twee is zelf het beste voorbeeld van wat deze regel vraagt."**

**Concrete casusrij, bijlage A, C01:**
| Veld | Was | Wordt |
|---|---|---|
| `histlabel` | `good_fragment` | ongewijzigd |
| tekst | ongewijzigd | ongewijzigd (ID en tekst blijven stabiel) |
| grond | "ASTRA-voorbeeld GOED; patroon binnen \d+ dagen" | **"Lokale recordfixture `goede_voorbeelden`, opgebouwd rond het ASTRA-fragment '… binnen 3 dagen …' met een lokaal toegevoegd telstartpunt. Niet als letterlijk ASTRA-voorbeeld aanhalen."** |

Idem voor C08 en C11: hun grond wordt **"lokaal geconstrueerde zin rond het ASTRA-fragment '… tenminste 80% van de ...' respectievelijk '… uiterlijk na 1 week …'; geen ASTRA-definitie"**. Teksten en ID's blijven ongewijzigd.

**Over de revisie.** Codex' waarschuwing is terecht en ik voldoe er al aan: ik heb `oldid=8558` **niet** geopend. Zowel `cowork-toegang-v1-aanvulling-v1.md` §4 als mijn kruisreview R-01 zeggen dat expliciet ("De historische revisiepagina heb ik niet geopend"). Wat ik wél heb vastgesteld is dat de huidige pagina die permanente link aanbiedt en "laatst bewerkt op 11 feb 2025 om 09:46" in de voetregel draagt. Die formulering blijft.

---

## R02 — "Geen grijs gebied" is een normverzwaring

**Beoordeelde passage:** §3.4 voorwaarde (d) "volledigheid van de beslissing"; de doorwerking in §6.3 (T, vraag d), in de voorgestelde `uitleg` (§6.1) en in §7.4 keuze C.

**Dispositie: DEELS OVERGENOMEN.**

**Wat ik overneem.** Codex heeft gelijk dat (d) zoals geformuleerd drie dingen samentrekt die ik zelf elders uit elkaar houd: toepasbaarheid van een criterium (ESS-04), volledigheid en onderscheidbaarheid van de afbakening (ESS-01/ESS-05), en beschikbaarheid van gevalsbewijs (geen normvraag). Mijn eigen §4.2 zegt dat ESS-04 niets zegt over essentie, en mijn §4.1 zegt dat divergentie tussen beoordelaars ook uit bewijs of een leesfout kan voortkomen. (d) sprak dat tegen. Bovendien maakt "beslist elk normaal geval, zonder grijs gebied" een eis van een uitkomst die ook van de wereld afhangt, niet alleen van de tekst.

**Wat ik handhaaf.** Er blijft één ding over dat (d) wilde vangen en dat niet door (a)–(c) alleen wordt gedekt: een zin waarin één criterium bepaald is en een ander onbepaald, mag niet slagen omdat het bepaalde criterium "er ook in staat". Dat is casus C04. Maar dat volgt al uit per-criterium toetsen — precies wat R-02 van mijn eigen kruisreview aan Codex' N1 vraagt. (d) is dus overbodig voor wat het moest doen, en schadelijk voor de rest.

**Concrete vervanging, §3.4, voorwaarde (d):**
> ~~"3. **Volledigheid van de beslissing** — de criteria samen beslissen elk gewoon geval, niet alleen de duidelijke. Als een criterium een groot grijs gebied laat, is de definitie niet toetsbaar, ook al is elk los criterium keurig."~~
> **"3. **Geen onbepaalde rest** — ieder criterium in de kern doorstaat (1) en (2). Een zin voldoet niet doordat één criterium bepaald is terwijl een ander het oordeel alsnog openlaat. Dit is per-criterium toetsen, geen extra eis van totale beslisbaarheid: of de criteria samen het begrip juist en onderscheidend afbakenen is ESS-01 en ESS-05, en of voor een concreet geval het bewijs beschikbaar is, is geen ESS-04-vraag."**

**Concrete vervanging, §6.3 (T), vraag (d):**
> ~~"Vraag daarna over de criteria samen: (d) *volledigheid* — beslissen zij een gewoon geval, of blijft er een grijs gebied waarin twee redelijke beoordelaars anders zouden oordelen?"~~
> **"Vraag daarna over de criteria samen: (d) *onbepaalde rest* — laat een van de criteria het oordeel alsnog open, ook wanneer een ander criterium bepaald is? Beoordeel niet of de criteria het begrip volledig of onderscheidend afbakenen (ESS-01/ESS-05), en niet of voor een gegeven geval het bewijs voorhanden is."**

**Doorwerking in de voorgestelde `uitleg` (§6.1).** De tweede helft van mijn voorgestelde zin ("en de criteria samen beslissen of het geval onder het begrip valt") draagt dezelfde verzwaring. Vervangen door: **"…en geen van de criteria laat dat oordeel alsnog open."** Dit brengt mijn recordvoorstel dichter bij Codex' N1 zoals ik dat in mijn kruisreview R-02 wilde bijstellen; de twee voorstellen verschillen daarna nog in woordkeuze, niet in strekking.

**Open normen.** Codex' toevoeging dat een bedoelde open norm niet uitsluitend op een vaagheidswoord mag worden afgekeurd, heb ik al in mijn kruisreview R-06 overgenomen en verwerk ik hier ook in de T-tekst: **"Een formulering die een open norm citeert of overneemt wordt niet op het vaagheidswoord afgekeurd; onderzoek eerst welke betekenis de bron eraan geeft en of daar een beoordelingsmaatstaf bij hoort."** Juridische geldigheid is in dit onderzoek niet onderzocht en wordt niet geclaimd.

---

## R03 — Voorwaardelijke metadata en de veldgrens

**Beoordeelde passages:** §3.3 tabel (werk-/kalenderdagen "altijd"; inclusieve grens); §3.2 rij Toelichting; §6.2 (G).

**Dispositie: OVERGENOMEN** (drie onderdelen, waarvan één al verwerkt).

**(a) Werk- of kalenderdagen.** Al ingetrokken in `cowork-aanvulling-op-eigen-v1.md` A-06, op dezelfde grond. Blijft staan: voorwaardelijk, "wanneer lezingen de uitkomst wijzigen". Geen verdere wijziging nodig.

**(b) Inclusieve of exclusieve grens.** Codex heeft gelijk dat mijn rij te breed is: "minimaal" en "tenminste" leggen de inclusie zelf al vast (≥), "meer dan" eveneens (>). De vraag speelt alleen wanneer de formulering haar openlaat.

**Concrete vervanging, §3.3 tabel, rij "Inclusieve/exclusieve grens":**
> ~~"Nodig wanneer: er een drempelwaarde is waar gevallen feitelijk op kunnen landen ('minimaal 80%', 'ouder dan 18'). Niet nodig wanneer: een kwalitatief onderscheid zonder continuüm."~~
> **"Nodig wanneer: de formulering de inclusie openlaat ('binnen 80%', 'rond de drempel', 'vanaf ongeveer'), of wanneer bron en tekst verschillende operatoren gebruiken. Niet nodig wanneer: het woord de operator al vastlegt — 'minimaal'/'tenminste' is ≥, 'meer dan' is >, 'maximaal'/'ten hoogste' is ≤. Niet nodig bij een kwalitatief onderscheid zonder continuüm."**

**(c) De veldgrens bij toelichting — dit is een echte interne tegenspraak in mijn v1.** §3.2 rij Toelichting zegt dat de toelichting "de methode, meetcontext, noemer of peildatum [mag] dragen"; §4.2 rij CON-01 zegt dat meetcontext die het criterium beslist "precies zulke noodzakelijke inhoud" is en dus in de zin hoort. Beide kunnen niet waar zijn voor dezelfde noemer. Codex wijst dat terecht aan.

**Concrete vervanging, §3.2, rij Toelichting, kolom "Bewijsfunctie":**
> ~~"**Mag de methode, meetcontext, noemer of peildatum dragen** (NL-SBB: verduidelijkt grenzen). **Repareert nooit een ontbrekend criterium in de kern**"~~
> **"**Mag de methodische uitwerking dragen**: hoe wordt gemeten, met welke procedure, met welk rekenvoorbeeld (NL-SBB: de toelichting verduidelijkt grenzen en hoeft geen volledige definitie te zijn). **Draagt niet** wat het begrip zelf begrenst: een noemer, populatie, peildatum of drempel die bepaalt of een geval eronder valt, hoort in de kern — NL-SBB: 'De definitie moet precies kloppen'. **Repareert nooit een ontbrekend criterium in de kern**"**

**Doorwerking in G (§6.2).** Mijn G-tekst zegt al "Methode, meetprocedure of rekenvoorbeeld horen in een apart toelichtingsvoorstel, niet in de kern" en daarvóór "maak in dezelfde zin het meetobject, en bij een aandeel de noemer, expliciet". Die twee zinnen volgen samen de juiste grens; ik voeg alleen de scheiding expliciet toe: **"Wat het begrip begrenst hoort in de kern; hoe je het vaststelt hoort in de toelichting."**

**(d) Eindige voorbeelden.** Overgenomen zonder tekstwijziging: mijn §3.2 noemt voorbeelden al "ondersteunend" en nergens bewijs van volledigheid. Codex' formulering ("tonen toepassing in die cases, geen universele onderscheidbaarheid") neem ik over in de gezamenlijke veldmatrix.

---

## R04 — Het scorebesluit is definitief, niet voorlopig

**Beoordeelde passage:** §4.3, eerste regel: "**[BESLUIT]** DEF-624, 15 september 2026: voorlopig geen totaalcijfer en geen vervangende deelscore".

**Dispositie: OVERGENOMEN.**

**Grond.** Ik heb de verkeerde bron geciteerd. Het woord "voorlopig" komt uit de issuebeschrijving van DEF-624; het besluitdocument zelf is stelliger. `feitenbasis/historisch/docs/analyses/2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md` is getiteld "**Definitief appbesluit** — geen totaalscore als kwaliteitsoordeel" en zegt: "De totaalscore **vervalt appbreed** als **kwaliteitscijfer, acceptatiecriterium en stuurmiddel voor hergeneratie**. Dit vervangt de tijdelijke productkeuze 'totaalscore niet beschikbaar'." Het document merkt zelf op dat de DEF-624-issueactualisatie van dezelfde dag de totaalscore "nog **tijdelijk** niet beschikbaar" noemt en dat "die beleidsomschrijving is met dit latere besluit achterhaald". Ik heb de achterhaalde formulering overgenomen.

**Concrete vervanging, §4.3, eerste besluitregel:**
> ~~"**[BESLUIT]** DEF-624, 15 september 2026: voorlopig geen totaalcijfer en geen vervangende deelscore; wel per regel het oordeel, de dekking en de openstaande punten. Geldt appbreed."~~
> **"**[BESLUIT]** Definitief appbesluit 15 september 2026 (`2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md`): de totaalscore vervalt appbreed als kwaliteitscijfer, acceptatiecriterium en stuurmiddel voor hergeneratie, en er komt geen vervangend kwaliteitspercentage. Dit vervangt de eerdere tijdelijke keuze 'totaalscore niet beschikbaar'; de formulering 'voorlopig' in de DEF-624-issuebeschrijving is daarmee achterhaald. Wel per regel het oordeel, de dekking en de openstaande punten."**

**Doorwerking.** Mijn §6.8-voorstel voor de toetsregels-skill wordt hiermee gelijk aan wat Codex in `instructievoorstellen-v1.md` voorstelt; ik onderschreef dat al in mijn kruisreview R-28. Eén gezamenlijke tekst, geen twee. Historische scorecode in de app is dan achterstand, geen alternatieve bevoegdheid — die formulering van Codex neem ik over.

**Scoreloos reviewcontract.** Al overgenomen in `cowork-aanvulling-op-eigen-v1.md` A-05, inclusief Codex' waarschuwing dat alleen een policywoord wijzigen de keten niet repareert. Geen dubbele verwerking nodig.

---

## R05 — Algemene reviewplicht tegenover een aparte regelpoort

**Beoordeelde passages:** §6.7 (het opslag- en poortvoorstel) en §7.4 keuze B, met name B2 en B3.

**Dispositie: DEELS OVERGENOMEN — en dit is het punt waar mijn voorstel het meest verandert.**

**Wat Codex aanwijst, en waarin hij gelijk heeft.** Mijn B3 ("poort voor de reviewplichtige regels met `aanbeveling: verplicht`") omvat ESS-01. Voor ESS-01 en ESS-02 liggen expliciete, vastgestelde besluiten die precies dat uitsluiten. Ik heb ze nagelezen:

- `bronnen/besluiten-ESS02-20260918.json`, besluit 2: "Integreer dit in de bestaande expertbeoordeling **zonder afzonderlijke verplichte akkoordknop per regel**." Besluit 4: "**Geen zelfstandige ESS-02-vaststelblokkade.** Negatieve en open oordelen blijven zichtbaar en veranderen niet door vaststelling van de definitie. Behoud de CON-01-blokkade en CON-02-afspraken."
- `bronnen/linear-DEF-745-20260918.json` (ESS-01): "Menselijke beoordeling blijft scoreloos, zonder AI-jury, extra ESS-akkoord of **zelfstandige ESS-vaststelblokkade**. … open/negatief oordeel wordt niet positief door vaststelling." Let op dat DEF-745 hier "ESS-vaststelblokkade" schrijft, niet "ESS-01-vaststelblokkade".

Mijn B3 botst daar rechtstreeks mee, en ik heb die besluiten in §4.3 wel gelezen maar alleen als ESS-02-context genoteerd, niet als grens op mijn eigen poortvoorstel. Dat was een fout in de redenering, niet in de bronlezing.

**Wat ik handhaaf.** DEF-630 blijft staan en is niet door die besluiten opgeheven: "Verplichte `review_required`-uitkomsten hebben een versioned menselijke beoordeling; een numerieke score vervangt die niet" en "Ontbrekende context, verplicht bewijs, actor of vereiste review kan niet met alleen een notitie worden opgeheven." Codex onderschrijft dat ook ("alleen 'geen nieuwe ESS-04-poort zonder besluit' is onvoldoende voor de bestaande algemene verplichting").

### Mijn standpunt, gericht gevraagd: algemene expertbeoordeling versus aparte regelpoort

De twee zijn verenigbaar zodra je onderscheidt **wat** de poort controleert van **waarop** hij blokkeert. Vier stellingen:

1. **De poort controleert het bestaan en de geldigheid van één integrale expertbeoordeling, niet dertien losse akkoorden.** Wat DEF-630 eist is dat er een versiegebonden menselijke beoordeling ís voor de verplichte `review_required`-uitkomsten en dat een cijfer of een notitie die niet vervangt. Dat vraagt één beoordeling die aan de recordversie hangt en die per regel een uitkomst registreert — niet een knop per regel. Daarmee is besluit 2 van ESS-02 ("zonder afzonderlijke verplichte akkoordknop per regel") gerespecteerd.

2. **Een negatief of open ESS-oordeel blokkeert niet.** Dat is het harde deel van de ESS-01/ESS-02-besluiten en ik neem het integraal over voor ESS-04: "voldoet niet" en "nog te beoordelen" op ESS-04 zijn zichtbaar, blijven zichtbaar, en worden door vaststelling niet positief — maar ze houden de vaststelling niet tegen. Mijn §6.7 punt 3 sprak dit tegen en wordt vervangen (zie hieronder).

3. **Het ontbreken van de integrale beoordeling blokkeert wél.** Dat is iets anders dan een regelpoort: het is de vaststelling dat de handmatige expertbeoordeling die het hele project als eindoordeel aanwijst, feitelijk niet heeft plaatsgevonden of niet bij deze recordversie hoort. Dat is precies wat DEF-630 zegt, en het is ook wat de DEF-630-audit van 15 september feitelijk aantrof: "twee verse proeven zonder opgeslagen validatiebewijs slagen nog bij handmatige approve". Zonder deze voorwaarde is DEF-630 leeg.

4. **Het verschil met CON-01/CON-02 is principieel en moet zo blijven.** Die twee hebben een *inhoudelijke* niet-overrulebare blokkade: een negatieve CON-01-uitkomst blokkeert. Voor de ESS-regels geldt dat uitdrukkelijk niet. Wat ik voorstel is dus geen CON-01-achtige regelpoort, maar een **aanwezigheidsvoorwaarde op de integrale beoordeling**. Ik had dat in §6.7 punt 3 als "een reviewplichtige regel zonder geldige beoordeling levert een blokkade in `niet_overrulebaar`" geschreven, wat het als regelpoort leest. Dat was fout.

**Concrete vervanging, §6.7 punt 3:**
> ~~"3. **Poort.** In `_evaluate_gate`: een reviewplichtige regel zonder geldige beoordeling levert een blokkade in `niet_overrulebaar`, met de reden 'ESS-04 is nog niet beoordeeld'. Conform DEF-630: niet met een notitie op te heffen."~~
> **"3. **Poort — aanwezigheid, niet inhoud.** In `_evaluate_gate` wordt gecontroleerd dat er een integrale, aan de huidige recordversie gebonden expertbeoordeling bestaat waarin de verplichte `review_required`-uitkomsten zijn geregistreerd. Ontbreekt die beoordeling, of hoort haar vingerafdruk bij een oudere tekst, context of normversie, dan blokkeert de vaststelling en is dat conform DEF-630 niet met alleen een notitie op te heffen. Een geregistreerd ESS-04-oordeel 'voldoet niet' of 'nog te beoordelen' blokkeert **niet**: het blijft zichtbaar en wordt door vaststelling niet positief, conform de ESS-01-besluiten in DEF-745 en besluit 4 van de ESS-02-besluiten. Er komt geen akkoordknop per regel (ESS-02-besluit 2) en geen CON-01-achtige inhoudelijke ESS-04-blokkade."**

**Concrete vervanging, §7.4 keuze B.** De vier varianten vervallen en worden vervangen door twee, omdat B1/B2/B3 alle drie een regelpoort veronderstelden:

> **Keuze B — hoe wordt de bestaande DEF-630-eis uitgevoerd?**
> **B-I (voorkeur):** aanwezigheidsvoorwaarde op één integrale, versiegebonden expertbeoordeling waarin de verplichte `review_required`-uitkomsten geregistreerd staan. Blokkeert bij ontbreken of bij een verouderde vingerafdruk; blokkeert nooit op de inhoud van een ESS-oordeel. Respecteert DEF-745 en de ESS-02-besluiten; voert DEF-630 uit.
> **B-II:** alleen zichtbaar maken dat ESS-04 open staat, zonder enige poortvoorwaarde. Laat het gat uit §5.7 bestaan en wijkt af van DEF-630; dat moet dan een expliciete, geregistreerde afwijking zijn en geen stilzwijgen.
> *Onderscheidende casus:* een definitie met score 0,95, ingevulde context, geldige CON-01- en CON-02-beoordeling, en geen enkele geregistreerde expertbeoordeling. Onder B-I blokkeert vaststellen; onder B-II niet.
> *Buiten deze keuze, uitdrukkelijk:* een aparte ESS-04-akkoordknop of een inhoudelijke ESS-04-blokkade. Beide zijn in strijd met bestaande besluiten en worden door geen van beide onderzoekers voorgesteld.

**Reikwijdte.** Codex heeft ook gelijk dat "één veld per regel" een ontwerpvoorstel is en niet de enige beleidsconforme uitvoering. Mijn §6.7 punt 1 blijft als voorstel staan, met de toevoeging: **"De vorm — één reviewveld per regel, dan wel één beoordelingsrecord met een uitkomst per regel — is een ontwerpkeuze. Bepalend is dat de uitkomst per verplichte reviewregel herleidbaar is en aan de recordversie hangt."** En Codex' waarschuwing "geen ESS-04-eigen database of CON-02-veld als verborgen ESS-container" neem ik over.

**Wat open blijft voor Chris:** B-I tegenover B-II, en of de reikwijdte alle dertien reviewplichtige regels is of alleen de verplichte. Dat laatste hoort onder DEF-630, niet onder dit regeldossier. **[OPEN]**

---

## R06 — Bewijsgat gesloten; telling gecorrigeerd

**Beoordeelde passages:** §1 punt 2 ("Vijf van vijftien indicatorpatronen"), §5.2, bijlage A, §8 (replicastatus en R9).

**Dispositie: OVERGENOMEN.**

**(a) Telling.** Codex heeft gelijk: het zijn er zes, niet vijf. Vier percentagepatronen plus twee tijdpatronen (`\buiterlijk\s+na\s+\d+\s+(dagen?|weken?)\b` mist "week", `\bbinnen\s+\d+\s+dagen?\b` mist "dag"). Mijn §5.2-tabel somt ze correct op ("vier dood, twee halfblind voor enkelvoud, en twee betekenisloos breed"); mijn samenvatting in §1 telde ze verkeerd op.

**Concrete vervanging, §1 punt 2:**
> ~~"**Vijf van de vijftien indicatorpatronen vuren nooit of missen het eigen ASTRA-voorbeeld.**"~~
> **"**Zes van de vijftien indicatorpatronen zijn defect.** Vier percentagepatronen vuren nooit in normale tekst; twee tijdpatronen missen het enkelvoud ('1 week', '1 dag'). Daarnaast zijn twee vormwoorden (`bevat`, `omvat`) zo breed dat zij nauwelijks onderscheiden. Twee van ASTRA's drie GOED-voorbeelden worden door de patronen die ervoor geschreven zijn niet herkend."**

Dezelfde correctie in mijn kruisreview R-16, waar ik "vijf" schreef bij een tabel die er zes toont. Ik laat `cowork-review-op-codex-v1.md` ongewijzigd en teken de correctie hier aan.

**(b) Replicastatus vervalt.** Zie het blok "Vooraf" hierboven: de reviewproef geeft op mijn veertien teksten via de echte evaluator 14/14 identieke uitkomsten. De beperking "replica, geen import" in bijlage A en §8 wordt vervangen door: **"De replica-uitkomsten zijn op 18 september door Codex met de echte `JudgmentReviewEvaluator` van dezelfde bevroren commit gereproduceerd, inclusief `additional_patterns`: veertien maal `review_required`, score `None`, identieke signalen, exit 0, lege stderr (`reviewproef/`). De beperking 'replica' vervalt daarmee voor de evaluatorroute. Wat ongetest blijft: service, UI, opslag, poort, modelcall en menselijk oordeel."**

**(c) R9 vervalt.** Al verwerkt in `cowork-aanvulling-op-eigen-v1.md` A-01; de reviewproef bevestigt het nu ook empirisch (`additional_ESS04: []` in de uitvoer).

**(d) Drie missers zijn signaleringsmissers.** Overgenomen. C05/C08/C11 zijn afwijkingen tussen mijn vooraf vastgelegde signaalverwachting en het werkelijke signaal — geen regeloordelen, want alle veertien blijven `review_required`. Bijlage A zegt dat al ("Alle veertien gevallen: `review_required`"); ik scherp de kolomkop aan van "Verwachting uit" naar **"Signaalverwachting uit"** om elke lezing als normoordeel uit te sluiten.

---

## R07 — Signaalterminologie en de overlap met ARAI-03

**Beoordeelde passages:** §1 punt 3, §5.2, §6.5.

**Dispositie: DEELS OVERGENOMEN.**

**(a) `voldoende`.** Overgenomen, al verwerkt in `cowork-aanvulling-op-eigen-v1.md` A-07; de reviewproef bevestigt het onafhankelijk (`additional_ARAI03: ['\bdoeltreffend\b', '\bvoldoende\b']`). `\bvoldoende\b` vervalt uit mijn voorgestelde ESS-04-patroonlijst.

**(b) Dubbele signalering is geen dubbele afkeur.** Overgenomen. Mijn §6.5 stelde dat al vast ("Beide zijn `review_required`, dus er ontstaat geen dubbele *afkeuring*, wel een dubbele *reviewlast*"), maar Codex' formulering is scherper: twee regels mogen dezelfde passage voor een verschillend normdoel aanwijzen, en dat is een kenmerk, geen gebrek. Ik neem die zin over in §6.5.

**(c) De term "trefwoord-pass" — deels afgewezen, met grond.** Codex heeft gelijk dat ESS-04 nooit een pass geeft en dat de term daarom letterlijk misleidt. Maar de term is niet van mij: `cowork-opdracht-v1.md` stelt als regelspecifieke vraag "Hoe voorkomen we schijnprecisie, verzonnen drempels, noemerloze percentages en trefwoord-pass?". Ik houd de term daarom als aanduiding van het te vermijden mechanisme, en maak expliciet dat hij vandaag niet optreedt.

**Concrete vervanging, §1 punt 3, en overeenkomstig in §5.2:**
> ~~"`bevat` en `omvat` staan als 'toetsbaarheidssignaal' in het record. Ze vuren op vrijwel elke Nederlandse definitiezin … Dat is de trefwoord-pass in zijn zuiverste vorm"~~
> **"`bevat` en `omvat` staan als toetsbaarheidssignaal in het record en vuren op vrijwel elke Nederlandse definitiezin, inclusief zinnen met 'zo snel mogelijk' erin (C10). Ze zijn daarmee nauwelijks onderscheidend. Vandaag levert dat geen onterechte pass op — ESS-04 geeft er geen — maar het stuurt de aandacht van de reviewer verkeerd, en het is precies het mechanisme dat een latere automatisering tot een trefwoord-pass zou maken. Dat is een argument om ESS-04 reviewplichtig te houden, niet om de signalen te laten staan."**

**(d) "bevat de gronden" kan een toepasbaar criterium zijn.** Overgenomen. Casus C09 ("Besluit dat de gronden van de afwijzing bevat.") is minder eenduidig dan ik hem presenteerde: de aanwezigheid van gronden ís aan een geval vast te stellen. Wat C09 aantoont is dat het *signaal* niet onderscheidt, niet dat de *zin* faalt.

**Concrete casusrij, bijlage A, C09:**
| Veld | Was | Wordt |
|---|---|---|
| bedoeling | "trefwoord-pass: 'bevat' zonder enig toetsbaar criterium" | **"weinig onderscheidend signaal: `bevat` vuurt op de zinsvorm. Inhoudelijk kan 'de gronden van de afwijzing bevat' een toepasbaar criterium zijn; de casus toont het signaalgebrek, niet een tekortkoming van de zin."** |

**(e) `example_pair_reason`.** Overgenomen. Mijn §6.1 stelt al een vervangende tekst voor; ik voeg Codex' punt toe dat de reden structureel moet zijn en niet historisch-defectgebonden:
> **"toetsbaarheid is een inhoudelijk oordeel over ieder criterium; indicatorpatronen kunnen hoogstens een passage aanwijzen en zijn nooit bewijs. Geen treffer betekent niet 'voldoet', een treffer niet 'voldoet niet'. Het gedocumenteerde paar is daarom geen regressiecase maar reviewmateriaal."**
De defectbeschrijving verhuist naar het onderzoeksdossier, waar zij thuishoort.

**(f) Kalibratie van de gemengde patroonset.** Overgenomen als voorwaarde bij mijn keuze A: welke variant ook wordt gekozen, de nieuwe set moet op vooraf gelabelde gevallen worden gekalibreerd voordat zij wordt vastgesteld. Toegevoegd aan §7.4 keuze A.

---

## R08 — De poortconfiguratie zet `allow_hard_override` aan

**Beoordeelde passages:** §5.6 ("importeren-en-meteen-vaststellen kan niet"), §5.7 (de hard blocks), en `cowork-aanvulling-op-eigen-v1.md` A-04 ("`allow_hard_override` staat standaard uit, dus de hard blocks zijn werkelijk blokkerend").

**Dispositie: OVERGENOMEN — feitelijke correctie.**

**Grond, door mij geverifieerd.** `nalevering3-4cdb8ea43/config/approval_gate.yaml` (hashgelijk, commit `4cdb8ea43`) bevat:
```yaml
soft_requirements:
  # Nieuw: sta override toe zelfs bij 'blocked' (harde) gevallen met verplichte reden
  # Gebruik met beleid; hier expliciet AANgezet.
  allow_hard_override: true
```
`GatePolicyService.base_path` is standaard `"config/approval_gate.yaml"` en `_load_policy` mergt dat bestand over `DEFAULT_POLICY`. Mijn A-04 baseerde zich op `DEFAULT_POLICY` in de Python-klasse en zag de meegeleverde configuratie niet. In de geleverde configuratie is `allow_hard_override` dus **aan**, en `_evaluate_gate` zet de hard blocks — waaronder "Geen validatieresultaat beschikbaar (eerst (her)valideren)" en "Score onder harde drempel" — om in `override_required`, af te handelen met een verplichte notitie.

**Correctie op A-04:** de zin "`allow_hard_override` staat standaard uit, dus de hard blocks in `_evaluate_gate` zijn werkelijk blokkerend en niet stilzwijgend overrulebaar" is onjuist voor de meegeleverde configuratie en wordt vervangen door: **"De Python-default is `False`, maar de meegeleverde `config/approval_gate.yaml` zet `allow_hard_override: true`. In de geleverde configuratie zijn de hard blocks dus overrulebaar met een notitie. Alleen de `niet_overrulebaar`-lijst (CON-01 en CON-02) blijft absoluut, omdat die vóór de `hard_block`-tak wordt afgehandeld en direct `blocked` teruggeeft."**

**Concrete vervanging, §5.6, slot:**
> ~~"Dat is deels afgevangen — de vaststelgate blokkeert op `validation_score is None` … dus importeren-en-meteen-vaststellen kan niet."~~
> **"Ik heb eerder gesteld dat dit is afgevangen doordat de gate blokkeert op `validation_score is None`. Dat gaat niet op in de geleverde configuratie: met `allow_hard_override: true` wordt die blokkade `override_required` en is zij met een verplichte notitie te passeren. Importeren-en-daarna-vaststellen zonder enige validatie is daarmee niet uitgesloten door de score-gate. Dit is statische analyse van code plus meegeleverde configuratie; een actieve environment-overlay (`APPROVAL_GATE_CONFIG_OVERLAY`) is onbekend en er is geen workflowproef uitgevoerd."**

**Gevolg voor §5.7 — mijn bevinding wordt sterker, niet zwakker.** DEF-630 eist letterlijk dat een vereiste review "niet met alleen een notitie [kan] worden opgeheven". In de geleverde configuratie is de enige voorwaarde die ESS-04 indirect raakte — de eis dat er überhaupt een validatieresultaat is — juist wél met een notitie op te heffen. Toegevoegd aan §5.7 als eigen alinea, met de begrenzing die Codex terecht vraagt: **"Dit is statisch bewijs uit code en meegeleverde configuratie. Er is geen uitgevoerde bypass en geen workflowproef; wat een actieve overlay doet is onbekend."**

**Wat staat blijft.** Dat `_evaluate_gate` geen enkele verwijzing naar `review_required`, `rule_statuses` of `evaluation_coverage` bevat, is onafhankelijk van deze configuratie en blijft valide statisch bewijs. Codex bevestigt dat ook.

---

## R09 — Ketenclaims begrenzen

**Beoordeelde passages:** §5.6 (opslag), §5.8 (export), §5.10 (bewerken), en mijn kruisreview R-20.

**Dispositie: DEELS OVERGENOMEN.**

**(a) Opslag — overgenomen, met behoud van de kern.** Codex heeft gelijk dat "geen kolom en geen JSON-veld" iets anders is dan "nergens opslag mogelijk": `validation_issues` is generieke JSON en `toelichting_proces` is vrije tekst, dus iets wegschrijven kán technisch. Mijn formulering was te absoluut, en mijn kruisreview R-20 — waarin ik Codex' C06 opwaardeerde van "niet aangetoond" naar "uitgesloten door het opslagcontract" — was op dat punt te stellig. Ik trek die opwaardering hierbij terug.

**Concrete vervanging, §5.6, tweede alinea:**
> ~~"Bewezen: een ESS-04-oordeel kan nergens worden bewaard."~~
> **"Bewezen: er is geen daarvoor bestemd veld. `definities` kent voor validatie alleen `validation_score`, `validation_date` en `validation_issues`; er is geen tegenhanger van `context_review`/`source_review` met versiebinding. Een oordeel wegschrijven in generieke JSON of in `toelichting_proces` is technisch mogelijk, maar levert geen betrouwbare reviewroute op: geen vingerafdruk over tekst, term, context en normversie, geen actor-/rolbinding, geen gerichte invalidatie bij wijziging, en niets wat een poort kan lezen. Wat ontbreekt is dus niet de opslagruimte maar het contract."**
Mijn kruisreview R-20 wordt hiermee bijgesteld van "uitgesloten door het opslagcontract" naar **"er is geen contract dat dit draagt; generieke opslag is geen betrouwbare reviewroute"**. `cowork-review-op-codex-v1.md` blijft ongewijzigd; de bijstelling staat hier.

**(b) Export — overgenomen.** Geverifieerd: `ExportService.__init__` heeft `enable_validation_gate: bool = False`, en de gate loopt alleen wanneer die vlag aanstaat én er een `validation_orchestrator` is (`export_service.py:389`). Mijn §5.8 presenteerde de gate als onvoorwaardelijk.

**Concrete vervanging, §5.8, eerste alinea:**
> ~~"`export_service.py` regels 456–468: niet-draft-export eist een uitgevoerde run (`is_uitgevoerde_run`) én `is_acceptable`."~~
> **"`export_service.py`: **wanneer** de service is geconstrueerd met `enable_validation_gate=True` én een `validation_orchestrator`, eist het async pad een uitgevoerde run (`is_uitgevoerde_run`) én `is_acceptable` (regels 456–468); de standaardwaarde van die vlag is `False` en het synchrone pad weigert dan met `NotImplementedError` zodra de gate aanstaat (regel 389). Welke exportroutes in de draaiende app met welke vlag worden opgebouwd, heb ik niet vastgesteld — de containerconfiguratie zit niet in het pakket. De uitspraak hieronder geldt dus voor deze route, niet voor alle niet-draft-exportroutes."**
De tweede alinea (de exportpoort erft het gat uit §5.7, en het exportbestand kan een openstaande beoordeling niet vermelden omdat er geen veld voor is) blijft staan, met dezelfde begrenzing. Codex' punt dat een export wél een open *runtime*-status zou kúnnen tonen is juist: `validatie.toetsresultaten` kan een `review_required`-uitkomst dragen. Wat niet kan is het *menselijke* oordeel tonen, want dat bestaat niet. Die nuance voeg ik toe.

**(c) Bewerken — overgenomen.** Mijn §5.10 leidde uit "geen ESS-04-string in `definition_edit_tab.py`" af dat de bewerkroute ESS-04 niet kent. Dat bewijst geen afwezigheid van generieke invalidatie: een versiebump invalideert CON-01-beoordelingen via de vingerafdruk zonder dat CON-01 in het editpad genoemd wordt. **Vervanging:** **"De bewerkroute bevat geen ESS-04-specifieke logica. Of een generiek invalidatiemechanisme een toekomstig ESS-04-oordeel zou raken, is niet onderzocht: bij CON-01 gebeurt dat via de vingerafdruk in `beoordeel_context`, niet via een codepad dat de regel noemt. Voor ESS-04 bestaat vandaag geen oordeel om te invalideren; het punt is dat een toekomstig ontwerp die vingerafdrukroute moet volgen."**

**(d) Per claim de onderzochte route vermelden.** Overgenomen als redactionele eis over §5: elke claim krijgt expliciet "onderzochte route" en "ontbrekende proef". §5 draagt die informatie al per subsectie ("Bewijsniveau: codelezing"), maar niet consequent per claim.

---

## R10 — Promptbewijs tegenover gedrag

**Beoordeelde passage:** §5.9: "Deze instructie is de directe generatieve oorzaak van de risico's die het dossier wil vermijden."

**Dispositie: OVERGENOMEN.**

**Grond.** Er is geen modelcall gedaan, door geen van beiden. Wat vaststaat is de tekst van de instructie en haar richting; wat een model ermee doet is niet gemeten. "Directe generatieve oorzaak" is een gedragsclaim zonder gedragsbewijs.

**Concrete vervanging, §5.9, slotalinea:**
> ~~"Dit is de tweede grote bevinding naast §5.7. De instructie **vraagt het model letterlijk om deadlines, aantallen en percentages** te gebruiken. … De instructie is dus de directe generatieve oorzaak van de risico's die het dossier wil vermijden — en hij is erfelijk"~~
> **"Dit is de tweede grote bevinding naast §5.7. De instructie vraagt het model letterlijk om deadlines, aantallen en percentages te gebruiken, en zwijgt over: geen drempel verzinnen die de bron niet draagt; een percentage altijd met noemer; een dagtermijn met werk- of kalenderdag; kwalitatieve criteria zijn gelijkwaardig. Zij stuurt daarmee aantoonbaar naar numerieke vormen, en het risico op schijnprecisie en verzonnen drempels is navenant plausibel. Of een model die drempels ook werkelijk verzint, is niet gemeten — er is in dit onderzoek geen modelcall gedaan, en een promptwijziging bewijst op zichzelf geen kwaliteitswinst. De instructie is wel erfelijk"**

**Cleaning.** Codex' begrenzing van zijn eigen P04 neem ik over in mijn §5.9-alinea over `opschoning.py`: één behouden getalszin is geen garantie voor alle criteria. Mijn formulering ("Geen ESS-04-relevant betekenisverlies te verwachten") wordt **"In deze route is geen betekenisverlies waargenomen en het is er op grond van de code ook niet te verwachten; één geteste zin plus een codelezing is geen garantie voor alle formuleringen."**

---

## R11 — Schrappen vraagt betekenisbewijs

**Beoordeelde passages:** §7.1 casustabel, rij C04, kolom H ("schrappen mag; geen drempel toevoegen"); §6.6, toegestane herstelhandelingen.

**Dispositie: OVERGENOMEN.**

**Grond.** Codex heeft gelijk en het punt is scherper dan ik het zag: een kwalificatie schrappen verruimt de extensie. "Belangrijke aanvraag" kan bedoeld zijn als begripsbepalend; schrappen maakt dan van de definitie een bredere definitie van een ander begrip. Dat is een betekeniswijziging, precies wat H moet beschermen. Mijn H-tekst noemde het toevoegen van een getal als de kernbescherming en onderschatte het weglaten van een woord.

**Concrete casusrij, §7.1, C04, kolom "H toegestaan":**
| Was | Wordt |
|---|---|
| "schrappen mag; geen drempel toevoegen" | **"Geen drempel toevoegen. Schrappen van 'belangrijke'/'relevant' is alleen toegestaan wanneer is vastgesteld dat de kwalificatie niet begripsbepalend is; anders verruimt het de extensie en is het een betekeniswijziging. Bij twijfel: geen herstel, maar verduidelijking vragen."** |

**Concrete vervanging, §6.6, toegestane herstelhandelingen, tweede bullet:**
> ~~"een beoordelende kwalificatie schrappen wanneer de overige criteria het geval al beslissen"~~
> **"een beoordelende kwalificatie schrappen uitsluitend wanneer uit de aangeleverde bron of bevestigde afbakening blijkt dat zij niet begripsbepalend is; schrappen verruimt anders de extensie en is dan een betekeniswijziging, geen herstel"**

**Beschermde inhoud verbreed.** Mijn §6.6 noemde als beschermd: betekenis, brongetrouwheid, noodzakelijke namen, term, registratiecontext, recordidentiteit, gebruikersinvoer — en daarna het getalsverbod als "de enige ESS-04-specifieke bescherming die er echt toe doet". Die laatste zin is te absoluut. **Vervanging:** **"Het getalsverbod is de meest ESS-04-specifieke bescherming, niet de enige: rolbetekenis, brongetrouwheid, noodzakelijke namen en context zijn hier even goed ESS-04-bescherming, en een weggelaten kwalificatie verandert de betekenis net zo goed als een toegevoegd cijfer."**

**Foutpositief signaal tegenover fout regeloordeel.** Overgenomen: mijn diagnose 4 vermengde die twee. **Vervanging in §6.6, diagnose 4:** **"4a. **Foutpositief of gemist signaal** — het patroon wees een bepaalde passage aan, of gaf geen treffer bij een bepaald criterium. Gezien §5.2 is dit bij ESS-04 een veelvoorkomende toestand en op zichzelf geen bevinding over de tekst. 4b. **Onjuist regeloordeel** — de menselijke uitkomst zelf berust op een lees- of toepassingsfout. Alleen 4b vraagt correctie van het oordeel; 4a vraagt correctie van de signaalset."**

Geen autoherstel activeren en geen tekstmutatie bij uitsluitend toetsen: beide stonden al in §6.6 en blijven ongewijzigd.

---

## R12 — Fixtures preciezer

**Beoordeelde passages:** §7.1 casustabel (C12, C03, C06, C05); bijlage A kolommen.

**Dispositie: OVERGENOMEN.**

**(a) C12 is niet identiek aan C01.** Terecht. C01 (recordvariant) draagt "nadat het verzoek is ingediend"; C12 ("Beslissing die binnen drie dagen wordt genomen") heeft geen startmoment. Mijn tabel noemde ze "inhoudelijk identiek", wat het onderscheid dat C12 moest maken — vorm tegenover inhoud — juist ondergraaft.

| C12, kolom | Was | Wordt |
|---|---|---|
| "Wat het onderscheidt" | "**Vorm versus inhoud.** Inhoudelijk identiek aan C01, maar het getal staat in letters" | **"**Vorm tegenover inhoud.** De termijn staat in letters en krijgt daardoor geen patroonsignaal, terwijl zij even bepaald is als een cijfer. Niet identiek aan C01: C12 mist het telstartmoment, dus de aanvaarding hangt af van de vastgestelde termijnbetekenis in bron of context."** |
| "T verwacht" | "voldoet — gelijk aan C01" | **"Bepaald als termijn, maar het startmoment ontbreekt: voldoet wanneer bron of context de telconventie vastlegt, anders nog te beoordelen. Het ontbrekende signaal speelt daarbij geen rol."** |

**(b) C03 — nuance toegevoegd.** "Veelhoek waarvan alle zijden even lang zijn" voldoet als abstract geometrisch criterium. Codex' toevoeging dat een fysieke toepassing tolerantiecontext kan vragen, is juist en verandert de casus niet maar wel haar reikwijdte. Kolom "T verwacht" wordt: **"voldoet binnen de abstracte geometrische lezing; bij een fysieke toepassing kan meettolerantie nodig zijn, maar die wordt niet bij het abstracte geval verzonnen."**

**(c) C06 — nuance toegevoegd.** Kolom "Wat het onderscheidt" wordt: **"**Nominale eigenschap.** Toetsbaar zonder magnitude (VIM3 §1.30). Het criterium is helder; of in een concreet geval het afzenderschap bewezen is, is een gevalsvraag en geen tekortkoming van de definitie."**

**(d) C05/C08 — het onderscheid dat Codex vraagt.** Ontbrekende definitiegrond tegenover ontbrekend gevalsgegeven. C05 ("Object dat minimaal 80% voldoet") mist de **definitiegrond**: er staat niet waarvan 80% en waaraan wordt voldaan — dat is een tekortkoming van de tekst. C08 ("Regeling die tenminste 80% van de gevallen dekt") heeft een noemer ("de gevallen") maar die is zelf onbepaald; ontbreekt daarnaast het gevalsgegeven, dan is dat een aparte kwestie. Kolom "bedoeling" bij C05 wordt: **"percentage zonder meetobject en zonder noemer — ontbrekende definitiegrond, niet ontbrekend gevalsbewijs"**; bij C08: **"ASTRA-fragment in een lokale zin; noemer genoemd maar zelf onbepaald ('de gevallen'). Scheid dit van de vraag of voor een concreet geval het telbewijs beschikbaar is."**

**(e) Samenvatting in §7.1.** De slotzin ("twee tekstsoorten zonder getal die vóldoen, en twee mét getal die niet voldoen") blijft geldig, maar krijgt de aantekening: **"'Voldoen' is hier mijn onderbouwde onderzoeksverwachting, geen expertgold. Geen van de veertien gevallen is door een onafhankelijke deskundige gelabeld."** Dat stond in bijlage A al voor de proef; het hoort ook bij de casustabel.

---

## R13 — Vijf skillfamilies

**Beoordeelde passage:** §6.8, vindplaatsen 1 t/m 5.

**Dispositie: DEELS OVERGENOMEN.**

**Grond.** Ik behandelde `definitie-toetsregels` (drie vindplaatsen), gaf gemotiveerd "geen wijziging" voor `definitie-nederlandse-definities`, en noemde `definitie-voorbeelden-generatie` als kandidaat voor een latere aanvulling. `definitie-ontologisch-modelleren` en `definitie-ufo-ontologie` heb ik niet behandeld. Codex behandelt alle vijf met vindplaats. Dat is completer en ik neem zijn voorstellen voor die drie over als basis.

**Concrete aanvulling op §6.8, nieuwe vindplaatsen 6 en 7:**
- **`definitie-ontologisch-modelleren/reference.md`** — Codex' voorstel na "Stap 4: Relaties Modelleren" overgenomen: relaties leggen vast van welk object een kenmerk is en waarop een telling slaat; instantie-identiteit (ESS-03), toepasbaarheid (ESS-04) en onderscheid (ESS-05) blijven apart; een registratiesleutel vervangt geen begripsbepalend kenmerk. Dit sluit rechtstreeks aan op mijn §3.2-rij Ontologierelaties ("ondersteunend: helpt bepalen wat het meetobject en de populatie zijn").
- **`definitie-ufo-ontologie/SKILL.md`** — Codex' voorstel na ESS-02 overgenomen: de ontologische duiding helpt bepalen waarop het criterium betrekking heeft en geeft geen zelfstandig bewijs van toetsbaarheid; forceer een kwalitatief criterium niet tot een getal of exclusief categorielabel. De laatste clausule is een nuttige extra borging tegen dezelfde numerieke druk die §5.9 in de generatie-instructie aanwijst.

**Voor `definitie-voorbeelden-generatie`:** ik neem Codex' inhoudelijke correctie over — met name het schrappen van de gelijkstelling "geen discussie → geen grensgeval", die onjuist is (een eenduidig beslisbaar geval op de grens blijft een grensgeval, en dat is precies wat C05 en E04-N06 laten zien). Mijn v1 noemde alleen dat de koppeling tussen grensgevallen en ESS-04 nergens is vastgelegd; Codex levert de concrete tekst.

**Wat ik handhaaf:** "geen wijziging" voor `definitie-nederlandse-definities` als *taalregel*. Codex stelt daar wél een toevoeging voor, en die is inhoudelijk goed, maar hij hoort onder de kop "Eisen aan de Differentia" en is daarmee een definitiekwaliteitsinstructie in een taalskill. Mijn bezwaar uit §6.8 blijft: een taalregel die numerieke formulering aanbeveelt zou een stijl-afkeurgrond invoeren. Codex' tekst doet dat uitdrukkelijk *niet* ("Verzin geen cijfers of grenzen") en is op dat punt veilig, dus ik maak er geen bezwaarpunt van — maar de plaatsing verdient een expliciete keuze bij uitvoering. **[gedeeltelijk open, redactioneel]**

**Referentielinks.** Overgenomen: bij uitvoering moet elk verwezen bestand werkelijk bestaan; nu wordt niets geïnstalleerd. Dit sluit aan op mijn R-30 aan Codex over de skillpaden — die staat nog open en raakt zijn zes voorstellen én mijn drie.

---

## R14 — Status van de voorstellen

**Beoordeelde passage:** §1, slotzin: "De twee besluiten die ik werkelijk aan Chris voorleg staan in §7.4. Al het overige is herstel van wat al besloten is, of tekst."

**Dispositie: OVERGENOMEN.**

**Grond.** Te stellig, en na R02, R05 en R08 aantoonbaar onjuist. Een deel van wat ik als "herstel" presenteerde is interpretatie of uitwerking: welke signalen in het record horen, hoe een reviewoordeel wordt opgeslagen, en wat "voldoet" betekent bij ontbrekend gegeven zijn keuzes, geen herstel. Alleen de bronattributieve correcties (thema, relatie, uitleg terug naar criteriumniveau) en de patroondefecten zijn zuiver herstel; DEF-630 is een bestaande eis waarvan alleen de uitvoeringsvorm open is.

**Concrete vervanging, §1 slotzin:**
> ~~"De twee besluiten die ik werkelijk aan Chris voorleg staan in §7.4. Al het overige is herstel van wat al besloten is, of tekst."~~
> **"Wat hiervan zuiver herstel is: de bronattributieve correcties aan het regelrecord (uitleg op criteriumniveau, thema, ESS-03-relatie) en de zes defecte patronen. Wat een bestaande eis is met een open uitvoeringsvorm: de DEF-630-voorwaarde voor verplichte `review_required`-uitkomsten. Wat interpretatie of uitwerking is en dus een keuze: de richting van de signaalset, de vorm waarin een menselijk oordeel wordt vastgelegd, en wat 'voldoet' betekent bij een ontbrekend gegeven. De keuzes staan in §7.4; een voorstel van twee onderzoekers blijft een voorstel."**

---

## Wat dit betekent voor de gezamenlijke stand

**Verschillen die na deze ronde nog bestaan** — geen daarvan is een feitelijke tegenspraak:

| Onderwerp | Codex | Cowork | Status |
|---|---|---|---|
| Vorm van de DEF-630-uitvoering | algemene reviewplicht herstellen met regellokale voorwaarden | aanwezigheidsvoorwaarde op één integrale versiegebonden beoordeling (B-I) | convergerend; beide sluiten een ESS-04-eigen blokkade uit |
| Richting van de signaalset | niet behandeld | omdraaien naar onbepaaldheid, of alleen repareren | keuze A, voor Chris |
| Voorbeelden in het regelrecord | fixturegebonden partijzin | zelfdragend voorbeeld zonder fixture | mijn R-29(2); redactioneel op te lossen |
| Normzin | N1, definitie als subject | criterium als subject | mijn R-02; Codex' eigen addendum steunt het criteriumniveau |

**Wat nog ontbreekt in de fase:** de Codex-verwerking van mijn `cowork-review-op-codex-v1.md`, en daarna de synthese met mijn controle daarop. Ik ben gereed voor die synthesecontrole.

**Geen besluit genomen.** Geen van de keuzes in §7.4 — nu A, B-I/B-II en C — is door Chris genomen, en dit document neemt er geen. Er is niets geïmplementeerd en niets aan app, regels, skills of bestaande onderzoeksversies gewijzigd.

---

## Bestandsstatus na deze verwerking

| Bestand | Status | SHA-256 |
|---|---|---|
| `cowork-onderzoek-v1.md` | ongewijzigd behouden | `7f9138d152d1bd617c4df340bf52ce4c00b3cc1b4cec2bd8d55d9a4a07062708` |
| `cowork-bewijs-v1/gevallen-v1.json` | ongewijzigd | `782a950c9b4878472f21776ccedd5b10453e63e3c7664fffe85c03ee4ac2fb61` |
| `cowork-bewijs-v1/proef-ess04-v1.py` | ongewijzigd | `466346240ef2a1e5186ff1b286ed6b6e1c48fd849037b25286921d27ae02dabd` |
| `cowork-bewijs-v1/uitkomsten-v1.json` | ongewijzigd | `a2412cb0e2bd282e0f0c6b5ded6157a45fb8deed9df87e454280e169b2ff80da` |
| `cowork-toegang-v1.md` | ongewijzigd | `32219d913a48203528134eee58e73fcfd62a3e742860dbb0a1073730a0747a74` |
| `cowork-toegang-v1-aanvulling-v1.md` | ongewijzigd | `c6cb0c4ffbea113cc6a99e6e35ecf43f01aa0eafa0b3ab5c2cf0c228cafdfb2e` |
| `cowork-review-op-codex-v1.md` | ongewijzigd; twee bijstellingen aangetekend in R06 en R09 | `ee25c9e82d209f0c77c2ab8f7cdcf676b91589ab8e5fa90790ee6873da6a81bb` |
| `cowork-aanvulling-op-eigen-v1.md` | ongewijzigd; A-04 gecorrigeerd in R08 hierboven | `10bc145dc9417f878f335977aa5f122a14dc9933e1a87a3e100379f41e1c78eb` |
| `cowork-reviewverwerking-v1.md` | dit bestand | apart gemeld bij overdracht |
