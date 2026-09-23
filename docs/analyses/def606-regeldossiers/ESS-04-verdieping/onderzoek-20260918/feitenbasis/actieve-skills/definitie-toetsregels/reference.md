# Toetsregels — Volledige Referentie

> On-demand referentie bij de skill `definitie-toetsregels`. Bevat de volledige 53-regel tabellen, de CON-01-uitwerking (contextvermelding, DEF-744), de scoring-verdelingen, de DEF-126 generatie-instructie-transformatie en technische referenties. ESS-02 (betekenisniveau en aard, DEF-754) staat in [`references/ess02-betekenisniveau.md`](references/ess02-betekenisniveau.md). De `SKILL.md` zelf bevat het overzicht, de categorie-tabel en de kern-drempels — lees dit bestand wanneer je specifieke regels, instructies of file-paths nodig hebt.

## Regelcategorieën — Volledig

### ARAI — AI-afgeleide Regels (9 regels)

Regels afgeleid uit AI-analyse van definitiekwaliteit:

| ID | Naam | Prior. | Instructie (generatie) |
|----|------|--------|----------------------|
| ARAI-01 | Geen vervoegd werkwoord als kern | midden | Begin de definitie met een zelfstandig naamwoord of naamwoordgroep |
| ARAI-02 | Vermijd vage containerbegrippen | midden | Vermijd containerbegrippen zoals 'aspect', 'ding', 'iets', 'element' zonder verdere specificatie |
| ARAI-02SUB1 | Lexicale containerbegrippen | midden | Vermijd algemene containertermen zoals 'aspect', 'ding', 'iets', 'element', 'factor' |
| ARAI-02SUB2 | Ambtelijke containerbegrippen | midden | Vermijd ongespecificeerde containerbegrippen zoals 'proces', 'voorziening', 'activiteit' |
| ARAI-03 | Geen subjectieve bijvoeglijke nw. | midden | Vermijd subjectieve of contextafhankelijke bijvoeglijke naamwoorden |
| ARAI-04 | Geen modale hulpwerkwoorden | midden | Vermijd modale hulpwerkwoorden zoals 'kan', 'moet', 'mag', 'zal' |
| ARAI-04SUB1 | Modale werkwoorden beperken | midden | Vermijd modale werkwoorden die onduidelijkheid scheppen over de essentie van het begrip |
| ARAI-05 | Geen impliciete aannames | midden | Vermijd impliciete verwijzingen naar aannames, gewoonten of niet-toegelichte contexten |
| ARAI-06 | Correcte definitiestart | **hoog** | Start zonder lidwoord, zonder koppelwerkwoord en zonder herhaling van het begrip |

### CON — Contextualisering (3 regels)

Regels voor contextuele inbedding van definities:

| ID | Naam | Prior. | Instructie (generatie) |
|----|------|--------|----------------------|
| CON-01 | Eigen definitie voor elke context. Registratiecontext buiten de definitiezin ¹ | **hoog** ² | Houd de registratiecontext (rechtsgebied, organisatie, wet, project) buiten de definitiezin — die hoort in het contextveld; neem een naam alleen op als die nodig is voor afbakening of identificatie en motiveer die grond |
| CON-02 | Authentieke bron | **hoog** | Baseer de definitie zoveel mogelijk op werkelijk aangeleverde, voor betekenis, context en peildatum passende authentieke of gezaghebbende bronpassages; behoud bepalende kenmerken, beperkingen en uitzonderingen; verzin geen bron, passage of vindplaats — volledige G-instructie in [`references/con02-bronbasis.md`](references/con02-bronbasis.md) |
| CON-CIRC-001 | Geen circulaire definitie | midden | Het begrip zelf mag niet letterlijk voorkomen in de definitie |

¹ Actuele app-regelnaam. "Eigen definitie voor elke context" voegt geen bredere passendheidstoets toe — of een definitie inhoudelijk bij de context past, valt onder DEF-742, niet onder CON-01.
² CON-01 levert geen cijfer en geen 0/1, maar een uitkomst per treffer; zie **§ CON-01 — Contextvermelding** hieronder.

> **CON-02 heeft geen cijfer.** De prioriteit *hoog* stuurt de aandacht, maar CON-02 kent geen gewicht en geen numerieke bijdrage aan totaal- of categoriescore (DEF-743, 15 september 2026). Het oordeel bestaat uit drie afzonderlijke controles — brongezag/toepasselijkheid, betekenissteun, verwijskwaliteit — elk met eigen bewijs en uitkomst (voldoet / voldoet niet / nog te beoordelen), over zes bronprofielen (wet/verdrag, beleid, convenant/overeenkomst, norm/standaard, vakpublicatie/begrippenregister, overig/onbekend). Upload, RAG, wiki en web zijn aanvoerroutes, geen gezag. Deskundige uitzonderingen, de toetsinstructie (T) en de herstel-op-verzoekinstructie (H): zie [`references/con02-bronbasis.md`](references/con02-bronbasis.md).

### ESS — Essentiële Structuur (6 regels)

Regels voor de kern van wat gedefinieerd wordt:

| ID | Naam | Prior. | Instructie (generatie) |
|----|------|--------|----------------------|
| ESS-01 | Essentie, niet doel | **hoog** | Beoordeel afbakening en functie/doel volgens ESS-01; signalen zijn geen bewijs; behoud de oorspronkelijke invoer. Onderbouwde bepalende functie behouden; overig doel buiten de kern |
| ESS-02 | Betekenisniveau en ontologische aard ondubbelzinnig maken ³ | **hoog** ⁴ | Laat bovenbegrip en kenmerken duidelijk maken of een algemeen begrip dan wel één bepaald ding of voorval bedoeld is, en waar relevant of de kern een activiteit of haar uitkomst is; type, exemplaar, proces en resultaat zijn hulprichtingen, geen verplichte markerwoorden — volledige N/G/T-instructie in [`references/ess02-betekenisniveau.md`](references/ess02-betekenisniveau.md) |
| ESS-03 | Instanties onderscheidbaar | **hoog** | Noem criteria voor unieke identificatie van instanties (zoals serienummer, kenteken, ID) |
| ESS-04 | Objectief toetsbaar | **midden** | Gebruik objectief toetsbare elementen (deadlines, aantallen, percentages, meetbare criteria) |
| ESS-05 | Onderscheid van verwante begrippen | **hoog** | Maak expliciet duidelijk waarin het begrip zich onderscheidt van andere verwante begrippen |
| ESS-CONT-001 | Essentiële inhoud aanwezig | **hoog** | De definitie moet minimaal 6 inhoudelijke woorden bevatten |

³ Regelnaam volgens het ESS-02-besluit van 16 september 2026 (DEF-754); de app-regelkaart volgt onder DEF-750. De vier appkeuzes zijn overlappende praktische richtingen, geen exclusieve indeling.
⁴ ESS-02 levert geen cijfer en geen 0/1: de mens beoordeelt binnen de bestaande expertbeoordeling (voldoet / voldoet niet / nog te beoordelen); een marker, label of aantal categoriewoorden geeft geen automatische pass of fail, en een negatief of open oordeel vormt geen zelfstandige vaststelblokkade. Zie [`references/ess02-betekenisniveau.md`](references/ess02-betekenisniveau.md).

### INT — Integriteit (9 regels)

Regels voor leesbaarheid en logische opbouw:

| ID | Naam | Prior. | Instructie (generatie) |
|----|------|--------|----------------------|
| INT-01 | Compacte en begrijpelijke zin | midden | Formuleer de definitie als één enkele, begrijpelijke zin |
| INT-02 | Geen beslisregel | midden | Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als' |
| INT-03 | Duidelijke voornaamwoord-verwijzing | **hoog** | Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent |
| INT-04 | Duidelijke lidwoord-verwijzing | midden | Maak bepaalde lidwoorden ('de instelling', 'het systeem') expliciet door direct te specificeren welke bedoeld wordt |
| INT-06 | Geen toelichting | **hoog** | Vermijd toelichtende formuleringen zoals 'bijvoorbeeld', 'zoals', 'dit houdt in', 'namelijk' |
| INT-07 | Toegankelijke afkortingen | midden | Licht afkortingen direct toe in dezelfde zin (bijv. DJI (Dienst Justitiële Inrichtingen)) |
| INT-08 | Positieve formulering | midden | Formuleer positief (wat iets wél is), niet negatief (wat iets niet is) |
| INT-09 | Limitatieve opsomming | midden | Maak opsommingen limitatief (vermijd 'zoals', 'bijvoorbeeld', 'onder andere', 'etc.') |
| INT-10 | Geen ontoegankelijke achtergrondkennis | **hoog** | Zorg dat de definitie begrijpelijk is zonder specialistische of niet-openbare kennis |

### SAM — Semantische Samenhang (8 regels)

Regels voor consistentie en coherentie tussen definities:

| ID | Naam | Prior. | Instructie (generatie) |
|----|------|--------|----------------------|
| SAM-01 | Kwalificatie wijkt niet af | midden | Zorg dat kwalificaties niet leiden tot een betekenis die afwijkt van het algemeen aanvaarde begrip |
| SAM-02 | Geen herhaling in kwalificatie | **hoog** | Vermijd herhaling uit de definitie van het hoofdbegrip bij het kwalificeren van begrippen |
| SAM-03 | Niet nesten van definities | **hoog** | Herhaal geen andere definitieteksten; verwijs naar het begrip of definieer afzonderlijk |
| SAM-04 | Samenstelling strijdt niet | **hoog** | Begin samengestelde begrippen met het component dat de specialisatie vormt (genus) en specificeer daarna |
| SAM-05 | Geen cirkeldefinities | **hoog** | Vermijd cirkeldefinities (wederzijdse verwijzingen tussen begrippen) |
| SAM-06 | Consistente terminologie | midden | Gebruik consistente terminologie (kies één voorkeurs-term per begrip) |
| SAM-07 | Geen betekenisverruiming | **hoog** | Vermijd betekenisverruiming; beperk je tot elementen die inherent zijn aan de term |
| SAM-08 | Synoniemen: zelfde definitie | **hoog** | Voor synoniemen: gebruik exact dezelfde definitiestructuur |

### STR — Structuur (11 regels)

Regels voor definitie-opbouw en genus-differentia:

| ID | Naam | Prior. | Instructie (generatie) |
|----|------|--------|----------------------|
| STR-01 | Start met zelfstandig naamwoord | **hoog** | Start de definitie met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord |
| STR-02 | Kick-off ≠ de term | **hoog** | Begin met een breder begrip (genus) en specificeer vervolgens hoe de term daarvan verschilt |
| STR-03 | Geen synoniem als definitie | **hoog** | Geef een volledige definitie, niet alleen een synoniem |
| STR-04 | Opening + toespitsing | **hoog** | Volg de algemene opening direct met een toespitsing die het specifieke type verduidelijkt |
| STR-05 | Essentie, niet constructie | midden | Beschrijf wat het begrip is, niet enkel uit welke onderdelen het bestaat |
| STR-06 | WAT niet WAARVOOR | **hoog** | Beschrijf wat het begrip is, niet waarvoor het dient of waarom het nodig is |
| STR-07 | Geen dubbele ontkenning | midden | Vermijd dubbele ontkenningen (zoals 'niet zonder', 'onmogelijk om niet te') |
| STR-08 | 'En' ondubbelzinnig | midden | Gebruik 'en' ondubbelzinnig (maak duidelijk of beide vereist zijn of één van beide) |
| STR-09 | 'Of' ondubbelzinnig | midden | Gebruik 'of' ondubbelzinnig (maak duidelijk of het inclusief of exclusief is) |
| STR-ORG-001 | Zinsstructuur en redundantie | midden | Maximaal 300 tekens; compacte zinsstructuur zonder redundantie |
| STR-TERM-001 | Consistente spelling | laag | Termen correct gespeld en gevormd (koppeltekens, spaties) |

### VER — Vorm (3 regels)

Regels voor de vormgeving van termen:

| ID | Naam | Prior. | Instructie (generatie) |
|----|------|--------|----------------------|
| VER-01 | Term in enkelvoud | **hoog** | Gebruik enkelvoud, tenzij het begrip een plurale-tantum is |
| VER-02 | Formulering in enkelvoud | midden | Formuleer de definitie in het enkelvoud |
| VER-03 | Werkwoord-term in infinitief | midden | Gebruik de infinitief voor werkwoord-termen (niet vervoegd) |

### DUP — Duplicaatdetectie (1 regel)

| ID | Naam | Prior. | Instructie (generatie) |
|----|------|--------|----------------------|
| DUP-01 | Geen duplicaat in database | **hoog** | Formuleer een originele definitie die substantieel verschilt van standaardformuleringen |

### VAL — Basisvalidatie (3 regels, intern)

Technische basisvalidatie die NIET meetelt in de scoring:

| ID | Naam | Prior. | Drempel |
|----|------|--------|---------|
| VAL-EMP-001 | Lege definitie is ongeldig | **hoog** | minimaal 1 teken |
| VAL-LEN-001 | Minimale lengte | midden | minimaal 5 woorden, 15 tekens |
| VAL-LEN-002 | Maximale lengte | laag | maximaal 80 woorden, 600 tekens |

## CON-01 — Contextvermelding (DEF-744)

### Norm

- De registratiecontext (rechtsgebied, organisatie, wet, project) hoort niet in de definitiezin, maar gestructureerd in het contextveld van het record.
- Een naam die inhoudelijk nodig is voor afbakening of identificatie mag in de zin staan; de grond daarvoor hoort in de toetsuitleg — er is geen apart gebruikersveld voor.
- Een letterlijke treffer op een contextnaam is een signaal voor menselijke beoordeling, geen automatische overtreding. Een hoofdletter of kleine letter beslist niets automatisch; beoordeel de functie van het woord in de zin.

### Uitkomst per treffer

| Onderscheid | Wanneer | Uitkomst | Toelichting in de toetsuitleg |
|-------------|---------|----------|-------------------------------|
| Registratievermelding | De naam zegt alleen binnen welke context de definitie geldt; de afbakening blijft zonder de naam intact | Voldoet niet op onderdeel | Verplaats de registratie naar het contextveld bij herformuleren — niet automatisch |
| Noodzakelijke naam | Een gegeven domeinfeit (vastgelegde afbakening of identificatie) maakt de naam nodig; zonder de naam is het een ander begrip | Voldoet op onderdeel | Behoud de naam; motiveer de grond (het domeinfeit), niet enkel "de zin wordt anders algemener" |
| Foutief signaal | Het woord matcht letterlijk, maar verwijst niet naar de context (bv. het woord "om" bij context "OM") | Voldoet op onderdeel | Behoud het woord; motiveer "geen contextvermelding" — geen noodzakelijke-naamclaim |
| Onduidelijk | De functie van de naam is uit de zin niet vast te stellen | Nog te beoordelen | Vraag naar functie/grond; geen automatische verwijdering, geen automatische pass |

### Voorbeelden (fictief)

De organisaties Prisma, Lumen en Vega zijn verzonnen; de kolom *Gegeven* bevat het domeinfeit dat de beoordeling draagt. Dezelfde cases staan in **definitie-nederlandse-definities** (formuleerkant).

| Context | Begrip | Gegeven | Definitie | Treffer | Uitkomst | Motivering |
|---------|--------|---------|-----------|---------|----------|------------|
| Prisma (registratieorganisatie) | dossierstuk | Een dossierstuk is buiten Prisma hetzelfde begrip; Prisma is alleen de plaats van registratie | `document dat bij Prisma is opgenomen in een dossier en de behandeling van een zaak ondersteunt` | "bij Prisma" | Voldoet niet op onderdeel | Registratie: de afbakening blijft zonder de naam intact; verplaats "Prisma" naar het contextveld |
| Lumen (uitgever) | pas | Volgens de vastgelegde domeinafbakening behoren alleen passen van uitgever Lumen tot het begrip | `toegangsbewijs dat door uitgever Lumen is verstrekt en de houder toegang geeft tot een aangesloten locatie` | "Lumen" | Voldoet op onderdeel | Noodzakelijke naam: de vastgelegde afbakening sluit passen van andere uitgevers uit; de naam draagt die afbakening |
| OM | verzoek | — | `schriftelijke vraag aan een instantie om een besluit te nemen` | "om" | Voldoet op onderdeel | Geen contextvermelding: "om" is een voegwoord in "om … te", geen verwijzing naar de context OM; geen noodzakelijke-naamclaim, geen hoofdletterheuristiek |
| Vega | bevestiging | Geen vastgelegde afbakening of toelichting over de functie van de naam | `bericht van Vega waarmee de ontvangst van een aanvraag wordt vastgelegd` | "Vega" | Nog te beoordelen | Onduidelijk of "van Vega" afbakent (alleen berichten van Vega tellen) of alleen registreert; vraag naar functie/grond |

### Meerdere treffers

Beoordeel elke treffer afzonderlijk en toon elke uitkomst. Een noodzakelijke naam maakt een registratievermelding elders in dezelfde zin niet geldig; een open treffer blijft zichtbaar als "Nog te beoordelen". Maak geen nieuwe aggregatie- of scoreformule over de treffers heen.

Gemengd voorbeeld — context: Prisma, Lumen; begrip: pas (zelfde gegeven als hierboven): `toegangsbewijs dat bij Prisma is geregistreerd en door uitgever Lumen is verstrekt aan de houder` → "Lumen": Voldoet op onderdeel (noodzakelijk, grond: vastgelegde afbakening); "bij Prisma": Voldoet niet op onderdeel (registratie → contextveld).

### Technische fout

Kan CON-01 niet worden uitgevoerd (bijvoorbeeld ontbrekende invoer of een fout in de regel), dan wordt dat afzonderlijk als technische fout getoond. Een technische fout is geen inhoudelijke uitkomst — geen Voldoet, Voldoet niet of Nog te beoordelen — en levert geen cijfer op.

### Scoring en totaalscore

- CON-01 levert geen cijfer en geen 0/1; de uitkomsten hierboven zijn het resultaat. De prioriteit *hoog* ordent de regel, maar is geen gewicht in een cijfer.
- De gewichten en drempels van de overige regels zijn ongewijzigd; de algemene cijferuitleg (gewichtsysteem, hard/soft minimum) geldt niet voor CON-01.
- Zolang DEF-624 open is, is de appbrede totaalscore tijdelijk niet beschikbaar; de afzonderlijke uitkomsten per regel blijven zichtbaar.

### Grenzen

- Menselijke review met actor, motivering en versiebinding is een appvereiste. Het advies uit deze skill is geen opgeslagen review, geen bevoegdheid, geen vaststelling en geen exportgoedkeuring.
- De algemene gate op ontbrekend bewijs (DEF-630) is hiermee niet opgelost.
- Geen automatische CON-repair: verwijder of herschrijf een treffer niet zelf (DEF-638); geef de uitkomst en de motivering.
- Of een definitie inhoudelijk past bij de context (algemene contextpassendheid) is een andere vraag dan CON-01 en valt onder DEF-742.

## Scoring — Verdelingen

### Prioriteitsverdeling

- **Hoog**: 28 regels (52,8%)
- **Midden**: 22 regels (41,5%)
- **Laag**: 2 regels (3,8%)

### Aanbevelingsverdeling

- **Verplicht**: 42 regels (79,2%)
- **Aanbevolen**: 10 regels (18,9%)

## Regel-naar-Instructie Transformatie (DEF-126)

### Hoe het werkt

Het transformatiemechanisme (DEF-126) zet validatieregels om naar generatie-instructies. In plaats van achteraf te controleren, stuurt het de LLM al bij het genereren in de goede richting.

**Werkwijze:**
1. Bij het opbouwen van de prompt worden alle actieve toetsregels geladen
2. Voor elke regel wordt de `instruction_map` in `json_based_rules_module.py` geraadpleegd
3. Als er een instructie voor de regel bestaat, wordt deze als imperatieve zin aan de prompt toegevoegd
4. Het formaat in de prompt is: `- **Instructie:** [imperatieve instructie]`

### Volledig overzicht

Van de 53 regels hebben **46 regels** een generatie-instructie. De 7 regels ZONDER instructie zijn de technische basisregels (VAL-EMP-001, VAL-LEN-001, VAL-LEN-002) en regels die puur achteraf worden gevalideerd.

De volledige instructies staan in de tabel per categorie hierboven in de kolom "Instructie (generatie)".

### Optimalisatie (DEF-171)

Na DEF-171 (promptoptimalisatie) zijn de toetsvragen uit de prompts verwijderd. Alleen de instructies blijven in de prompt staan. De toetsvragen worden nu alleen nog gebruikt door de ValidationOrchestratorV2 voor post-generatie validatie.

## Technische Referenties

- Regel JSON-bestanden: `src/toetsregels/regels/*.json`
- Python validators: `src/toetsregels/regels/*.py`
- Configuratie: `config/toetsregels/toetsregels_config.yaml`
- Prompt-integratie: `src/services/prompts/modules/json_based_rules_module.py`
- Integriteit-module: `src/services/prompts/modules/integrity_rules_module.py`
- Structuur-module: `src/services/prompts/modules/structure_rules_module.py`
- Validatie-service: `src/services/validation/modular_validation_service.py`
- Orchestratie: `src/services/orchestrators/validation_orchestrator_v2.py`
- Cache (TTL 1 uur): `src/toetsregels/rule_cache.py`
