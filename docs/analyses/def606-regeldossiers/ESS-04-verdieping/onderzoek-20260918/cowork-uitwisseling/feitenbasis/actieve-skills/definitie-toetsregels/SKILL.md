---
name: toetsregels
description: "Valideer en score een definitie tegen de 53 toetsregels (9 categorieën); genereer generatie-instructies. Triggers: \"toetsregels\", \"valideer definitie\", \"kwaliteitscheck\", \"score definitie\". NOT for formulering/taalregels (use definitie-nederlandse-definities)."
triggerExamples:
  positive:
    - "Valideer deze definitie"
    - "Valideer deze definitie met de toetsregels"
    - "Beoordeel deze definitie"
    - "Geef een kwaliteitscheck score voor deze definitie"
    - "Welke generatie-instructie past bij deze categorie?"
    - "Check de kwaliteit van deze definitie"
  negative:
    - "Schrijf een definitie volgens de Nederlandse taalregels" # → definitie-nederlandse-definities
    - "Maak een ontologisch model" # → definitie-ontologisch-modelleren
    - "Geef voorbeelden bij deze definitie" # → definitie-voorbeelden-generatie
lastReviewed: null
evalScore: null
status: active
---

# Toetsregels — Validatieregels voor Definitiekwaliteit

Referentie voor de 53 toetsregels (validatieregels) van de DefinitieAgent, verdeeld over 9 categorieën, inclusief scoring, weging en generatie-instructie-transformatie.

## Wanneer gebruiken

- Een definitie moet worden gevalideerd tegen kwaliteitsregels
- Validatieresultaten moeten worden geïnterpreteerd of uitgelegd aan de gebruiker
- Een nieuwe toetsregel moet worden aangemaakt of aangepast
- Toetsregels moeten worden omgezet naar generatie-instructies voor LLM-prompts
- De prioriteit of het gewicht van een specifieke regel moet worden bepaald
- De werking van het scorings- of drempelsysteem moet worden begrepen
- Een treffer op een contextnaam moet worden beoordeeld (CON-01: registratie, noodzakelijke naam, foutief signaal of nog te beoordelen)

**Niet gebruiken voor:** taalkundige formuleringsregels (gebruik **definitie-nederlandse-definities**), ontologische classificatie (gebruik **definitie-ufo-ontologie**), of juridische context (gebruik **definitie-juridisch-nederland**).

## Overzicht

Het systeem bevat **53 toetsregels** verdeeld over **9 categorieën**. Elke regel heeft een JSON-configuratie en een Python-validator. Regels worden parallel uitgevoerd met gewogen scoring; ESS-01 (inhoudelijke beoordeling), ESS-02 (menselijke betekenisbeoordeling), CON-01 (uitkomst per treffer) en CON-02 (drie afzonderlijke controles) zijn daarvan uitgezonderd en leveren geen cijfer (zie Scoring & Weging). Daarnaast zijn **46 van de 53 regels** getransformeerd naar generatie-instructies die in de LLM-prompts worden opgenomen (DEF-126).

### Categorieën op een rij

| Categorie | Naam | Aantal | Gewicht | Prioriteit |
|-----------|------|--------|---------|------------|
| ARAI | AI-afgeleide regels | 9 | 1.0 | 1 (hoogste) |
| CON | Contextualisering | 3 | 1.0 | 2 |
| ESS | Essentiële structuur | 6 | 1.0 | 3 |
| INT | Integriteit | 9 | 0.9 | 4 |
| SAM | Semantische samenhang | 8 | 0.8 | 5 |
| STR | Structuur | 11 | 0.7 | 6 |
| VER | Vorm | 3 | 1.0 | 7 |
| DUP | Duplicaatdetectie | 1 | 1.0 | 8 |
| VAL | Basisvalidatie | 3 | — | — (intern) |
| **Totaal** | | **53** | | |

## De 53 regels

De volledige 53-regel tabellen per categorie (ARAI, CON, ESS, INT, SAM, STR, VER, DUP, VAL) — met prioriteit en generatie-instructie per regel — staan in **[`reference.md`](reference.md)**. Het categorie-overzicht hierboven geeft de aantallen, gewichten en prioriteit per categorie; lees `reference.md` voor de individuele regels wanneer je een definitie daadwerkelijk valideert of een specifieke regel nodig hebt.

### CON-02 — bronbasis (G/T/H)

Bij genereren op aangeleverde bronnen, toetsen op CON-02 of een CON-02-herstelvoorstel op verzoek: lees **[`references/con02-bronbasis.md`](references/con02-bronbasis.md)**. Kern: drie afzonderlijke controles (brongezag/toepasselijkheid, betekenissteun, verwijskwaliteit) met eigen bewijs en uitkomst; zes bronprofielen; upload/RAG/wiki/web zijn routes, geen gezag; deskundige uitzonderingen zijn geen gewoon "voldoet"; herstel alleen op verzoek, nooit automatisch. CON-02 krijgt geen cijfer.

## ESS-01 — begripsafbakening, functie en doel

Lees bij genereren of toetsen het [gedeelde N/G/T/H-contract](references/ess01-functiegrens.md). Behoud uitsluitend onderbouwde begripsbepalende functies; overig doel buiten de kern. Toets ongewijzigde invoer. Een bevestigde overtreding blijft voldoet niet, ongeacht brongezag. Geen automatische wijziging of regeneratie. Toezicht blijft een grensgeval; “in het kader van” blijft een zichtbaar signaal. Geen ESS-01-cijfer, aparte akkoordplicht of nieuwe vaststelblokkade; CON-01/02-afspraken blijven gelden. Skilladvies is geen opgeslagen menselijke review.

## ESS-02 — betekenisniveau en aard

Lees bij genereren of toetsen het [gedeelde ESS-02-contract](references/ess02-betekenisniveau.md). ESS-02 onderscheidt betekenisniveau (algemeen begrip of één bepaald ding/voorval) en aard (bijvoorbeeld activiteit of uitkomst). TYPE, PROCES, RESULTAAT en EXEMPLAAR zijn overlappende praktische richtingen, geen verplichte markerwoorden en geen exclusieve indeling; een categoriewoord of label bewijst niet dat de kern klopt. De app geeft signalen; de mens beoordeelt ESS-02 binnen de bestaande expertbeoordeling — tot dan is de uitkomst "nog te beoordelen". Geen ESS-02-cijfer en geen zelfstandige ESS-02-vaststelblokkade; negatief of open blijft zichtbaar en wordt door vaststelling niet positief. Een bewuste handmatige categoriekeuze (actor, tijd, versie) bevestigt alleen de daarin uitgedrukte bedoeling; een default of modelvoorstel niet; een werkelijk bron-/contextconflict eerst verduidelijken. Toets de ongewijzigde kern; herstel alleen op verzoek. Skilladvies is geen opgeslagen menselijke beoordeling; CON-01/02- en ESS-01-afspraken blijven gelden.

## Scoring & Weging

> **Geen cijfer voor ESS-01, ESS-02 of CON-02; voorlopig geen totaalcijfer.** ESS-01 vraagt inhoudelijke beoordeling en krijgt geen numerieke bijdrage; ook een negatief oordeel veroorzaakt geen nieuwe ESS-01-vaststelblokkade. ESS-02 krijgt evenmin een cijfer of 0/1: het menselijke oordeel is voldoet / voldoet niet / nog te beoordelen, en een negatief of open oordeel vormt geen zelfstandige vaststelblokkade. CON-02 heeft geen gewicht en geen numerieke bijdrage aan totaal- of categoriescore; de prioriteit *hoog* stuurt de aandacht, niet een cijfer. Productbesluit 15 september 2026 (DEF-743/DEF-624): voorlopig geen totaalcijfer en geen vervangende deelscore over alleen cijfergevende regels — toon per regel het oordeel (voldoet / voldoet niet / nog te beoordelen) en welke controles daadwerkelijk zijn uitgevoerd. De gewichten en drempels hieronder zijn de bestaande generieke configuratie van andere regelrecords; ze zijn historisch en gelden niet als CON-02- of kwaliteitsoordeel zolang er geen totaalscore is. Dit herschrijft de app-brede scoregate niet: hoe de app een ontbrekende totaalscore bij vaststellen behandelt, valt onder DEF-630.

### Gewichtsysteem

| Prioriteit | Gewicht | Betekenis |
|-----------|---------|-----------|
| hoog | 1.0 | Blokkerend bij falen — de definitie voldoet niet aan een fundamentele eis |
| midden | 0.7 | Significant effect op score — kwaliteitsvermindering |
| laag | 0.4 | Informatief — verbetersuggestie |

### Drempelwaarden

| Drempel | Waarde | Gevolg |
|---------|--------|--------|
| Hard minimum | 0.75 | Definitie wordt geblokkeerd — moet worden verbeterd |
| Soft minimum | 0.65 | Override nodig — gebruiker moet expliciet goedkeuren |

### Uitzondering: CON-01 (contextvermelding)

CON-01 krijgt géén cijfer en géén 0/1: elke treffer op een contextnaam krijgt een eigen uitkomst — *Voldoet op onderdeel*, *Voldoet niet op onderdeel* of *Nog te beoordelen* — met motivering in de toetsuitleg. Een letterlijke treffer is een signaal voor menselijke beoordeling, geen automatische overtreding; verwijder of herschrijf niets automatisch. De gewichten en drempels hierboven gelden voor de overige regels en zijn ongewijzigd. Zolang DEF-624 open is, is de appbrede totaalscore tijdelijk niet beschikbaar; de afzonderlijke uitkomsten per regel blijven zichtbaar. Menselijke review (actor, motivering, versiebinding) is een appvereiste — het advies uit deze skill is geen opgeslagen review, bevoegdheid, vaststelling of exportgoedkeuring. Onderscheidingen, voorbeelden en grenzen: [`reference.md`](reference.md) § CON-01.

> **Prioriteit-/aanbevelingsverdelingen** en de **DEF-126 regel-naar-generatie-instructie-transformatie** (incl. DEF-171-optimalisatie): zie [`reference.md`](reference.md).

## Gerelateerde skills

| Skill | Relatie |
|-------|---------|
| **definitie-nederlandse-definities** | Taalregels — STR, INT, VER en CON-01 (contextvermelding) in context van formulering |
| **definitie-ufo-ontologie** | Categorie — UFO-achtergrond bij de vier praktische richtingen; ESS-02 betekenisniveau en aard als hulpmiddel, geen exclusieve indeling |
| **definitie-ontologisch-modelleren** | Structuur — SAM-regels voor samenhangcontrole tegen het model |
| **definitie-voorbeelden-generatie** | Illustratie — ESS-05 onderscheid aantonen via voorbeelden |
| **definitie-juridisch-nederland** | Context — CON-regels voor juridische contextverwerking |

> **Technische referenties** (JSON-bestanden, Python validators, prompt-modules, config-paths): zie [`reference.md`](reference.md).

*Versie: 0.5 — DEF-754 (ESS-02 betekenisniveau en aard, menselijke beoordeling zonder cijfer); 0.4 — DEF-743 (CON-02 bronbasis G/T/H + geen-cijferbesluit); 0.3 — ALG-329 (progressive disclosure: regeltabellen + detail → reference.md) — DEF-744 (CON-01 contextvermelding: uitkomst per treffer, geen cijfer)*
