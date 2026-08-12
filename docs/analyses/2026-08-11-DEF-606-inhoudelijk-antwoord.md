# DEF-606 — Inhoudelijk antwoord op de kernvraag

**Datum:** 11 augustus 2026 · **Aanvulling op:** `2026-08-11-DEF-606-git-archeologie.md`

De eerste ronde onderzocht alleen de *herkomst* van beide lagen. Deze ronde onderzoekt wat de
regels inhoudelijk **zouden moeten doen** — en toetst beide implementaties daaraan.

---

## Kort antwoord

**Optie 1 — restant.** Dat blijft staan, maar de doorslaggevende reden is niet meer de git-historie:
de `.py`-laag implementeert **aantoonbaar een andere regelset dan de norm waarop het systeem
gebaseerd is**. Hij kán de bedoelde opvolger niet zijn.

Tegelijk laat dit onderzoek een probleem zien dat groter is dan de opruimklus: **de winnende laag
implementeert zijn eigen norm maar voor twee derde.** 15 van de 44 toetsbare regels geven het
*eigen gedocumenteerde foute voorbeeld* een score van 1,0 — ze kunnen niet falen.

---

## 1. De normatieve bron is gevonden: ASTRA

De 53 regels zijn geen eigen bedenksel. Het veld `brondocument` in de regel-JSONs wijst 35× naar
"ASTRA". Dat is de **Architectuur Strafrechtketen**, en de relevante bron is de
**Standaard Definitiekwaliteit**.

| | |
| --- | --- |
| Publieke vindplaats | https://www.astraonline.nl/index.php/Regels_voor_definitiekwaliteit |
| Standaard | https://www.astraonline.nl/index.php/Standaard_Definitiekwaliteit |
| Herkomst | *Standaarden en Richtlijnen voor opstellen van definities*, v1.0 (17-01-2018), team Metadata Management (MDM) van de Justitiële Informatiedienst (Justid) |
| Aangescherpt | 2024, door de ModelAutoriteit Strafrechtketen (**MAS**) |
| Beheer nu | SRK-Expertgroep Semantiek (SES); akkoord SES 10-02-2025 |
| Omvang | **36 genummerde regels**, exact jullie ID-schema en categorieën |
| Onderliggende primaire bron | Ronald Ross, *How to Define Business Terms in Plain English: A Primer* ("DBT") — 18 van de 36 regels, met paragraafnummers 1.1 t/m 6.1 |

Verdeling van de bronnen bij ASTRA zelf: DBT 18×, Politie 13×, MAS 4×, VenV/MDM 1×.

**Uw 53 = ASTRA's 36 + 17 eigen toevoegingen** (de 9 ARAI-regels, DUP, en de 7 baseline VAL/CIRC/
CONT/ORG/TERM-regels). Het gat bij **INT-05 is geërfd van ASTRA**, geen fout in de app.

---

## 2. Beslissend: de JSON-laag is een getrouwe transcriptie van ASTRA, de `.py`-laag niet

Ik heb drie bronnen naast elkaar gelegd: de ASTRA-wikitekst (verbatim opgehaald), de `naam`/
`toetsvraag`/`uitleg` in de regel-JSONs, en de docstrings van de `.py`-validators.

**De JSON `naam`-velden zijn letterlijk ASTRA's `Regel-kort`:**

| ID | ASTRA `Regel-kort` (verbatim) | App JSON `naam` |
| --- | --- | --- |
| STR-05 | definitie ≠ constructie | Definitie ≠ constructie |
| STR-06 | essentie ≠ informatiebehoefte | Essentie ≠ informatiebehoefte |
| STR-08 | dubbelzinnige 'en' is verboden | Dubbelzinnige 'en' is verboden |
| SAM-06 | één synoniem krijgt voorkeur | Één synoniem krijgt voorkeur |
| ESS-04 | toetsbaarheid | Toetsbaarheid |
| VER-01 | term in enkelvoud | Term in enkelvoud |

Dit geldt voor **alle 36**. Ook de `toetsvraag`- en `uitleg`-velden volgen ASTRA's `Regel` en
`Toelichting`.

**De `.py`-laag matcht ASTRA op geen van de negen betwiste regels:**

| ID | ASTRA-regel (verbatim, ingekort) | `.py`-docstring |
| --- | --- | --- |
| VER-01 | "De term … moet in het enkelvoud staan, tenzij het woord alleen als meervoud bestaat." | Versie-onafhankelijk |
| VER-02 | "De definitie moet worden geformuleerd in de enkelvoudsvorm…" | Geen tijdsgebonden formuleringen |
| VER-03 | "Een werkwoord moet gedefinieerd worden als infinitief…" | Geen verwijzingen naar specifieke data |
| SAM-02 | "Als een begrip wordt gekwalificeerd, mag de definitie geen herhaling bevatten…" | Geen vage kwantoren |
| SAM-03 | "Een definitie … mag niet herhaald worden in de definitie van een ander begrip." | Geen tautologie |
| SAM-04 | "De definitie van een samengesteld begrip mag niet strijdig zijn met de onderliggende begrippen." | Geen cirkelverwijzing |
| SAM-05 | "Een cirkeldefinitie mag niet voorkomen." | Repository termen gebruiken |

**Dit sluit optie 2 definitief uit.** De vraag was niet alleen "welke laag is nieuwer", maar "welke
laag doet wat de regel moet doen". Antwoord: de JSON-laag draagt de norm, de `.py`-laag draagt de
inhoud van een verdwenen `core.py` die niets met ASTRA te maken heeft.

> **Bijvangst:** de skill `definitie-toetsregels` (`reference.md`) wijkt op 14 regels af van ASTRA
> — het is een parafrase, geen bron. Waar die skill en de JSON van elkaar verschillen, heeft de
> **JSON** gelijk. De skill noemt STR-01 bijvoorbeeld prioriteit "hoog"; ASTRA zegt "laag".

---

## 3. Empirische toets: de 53× bereikbaarheidsmatrix

44 van de 53 regels dragen in hun eigen JSON een **goed** en een **fout** voorbeeld. Dat is een
uitvoerbare specificatie: de regel hoort het goede voorbeeld hoger te scoren dan het foute.
Beide implementaties zijn daar tegenaan gedraaid, op de huidige code
(geverifieerd op HEAD `5cf2cd80`; regel-JSONs md5 `1a62ed2d…`).

| | LIVE `_evaluate_json_rule` | `.py`-laag via loader |
| --- | --- | --- |
| Onderscheidt goed van fout | 24 | 27 |
| **Blind** (zelfde score voor beide) | **19** | 15 |
| **Omgekeerd** (fout scoort hóger) | **1** | 1 |
| Niet laadbaar | 0 | 1 (DUP_01) |

**15 regels in de live engine geven het eigen FOUTE voorbeeld score 1,0** — ze kunnen dus nooit
falen: `ARAI-03, DUP-01, ESS-01, ESS-04, INT-02, INT-06, SAM-01, SAM-02, SAM-03, SAM-05, SAM-08,
STR-03, STR-05, STR-06, VER-03`.

**VER-01 is omgekeerd:** het foute voorbeeld `"gegevens"` krijgt 1,0, het goede voorbeeld
`"gegeven"` krijgt 0,7. Dat is **DEF-605, empirisch bevestigd in de actieve engine**.

Deze uitkomsten zijn **ongewijzigd na PR #396** (de RuleCache-fix van DEF-606): die bewaart nu wel
de runtime-velden, maar laat geen van de 15 blinde regels alsnog vuren.

> Dit is de matrix die DEF-606 zelf als acceptatiecriterium eist ("CI genereert een 53×
> reachabilitymatrix"). De eerdere schatting "37 actief, 10 inert, 3 kunnen nooit falen" is
> hiermee vervangen door een gemeten uitkomst.

---

## 4. Waarom aansluiten van de `.py`-laag dit niet oplost

De 15 blinde regels vallen in drie soorten — en maar één daarvan is een implementatiegat:

**(a) Vergt repository-context — onmogelijk op één losse tekst (6 regels)**
`SAM-01, SAM-02, SAM-03, SAM-05, SAM-08, DUP-01`. ASTRA's SAM-05 luidt: *"Twee definities zijn
circulair als het ene begrip gebruikt wordt in de definitie van het andere begrip en andersom."*
Dat is per definitie niet te zien aan één string.

**(b) Vergt semantisch oordeel — geen regex-kwestie (8 regels)**
`ESS-01` (essentie vs. doel), `ESS-04` (toetsbaarheid), `INT-02` (beslisregel), `INT-06`
(toelichting), `STR-03` (synoniem als definitie), `STR-05` (constructie), `STR-06`
(informatiebehoefte), `ARAI-03` (subjectieve bijvoeglijke naamwoorden).

**(c) Gewoon niet geïmplementeerd (1 regel)** — `VER-03` (infinitief).

**Elf regels zijn blind in béíde lagen**: `ARAI-03, ESS-01, INT-07, SAM-03, SAM-05, SAM-08, STR-03,
STR-05, STR-06, STR-09, VER-03`. De `.py`-laag bedraden verplaatst het probleem dus, het lost het niet op.

**En er is geen "juiste" regex om naar terug te vallen.** De ASTRA-bron bevat *geen* patronen,
reguliere expressies of detectie-instructies — het zijn natuurlijke-taalregels met prozavoorbeelden.
Alle `herkenbaar_patronen` in de JSONs zijn eigen toevoegingen. Beide lagen zijn homegrown
heuristiek; de norm schrijft de detectie niet voor.

---

## 5. Overige drift ten opzichte van de bron

| Bevinding | Detail |
| --- | --- |
| **Prioriteitsdrift: 10 van 36** | `ESS-05` midden→hoog · `SAM-01` hoog→midden · `SAM-06` laag→midden · `STR-01` laag→hoog · `STR-02` laag→hoog · `STR-07/08/09` laag→midden · `VER-02` hoog→midden · `VER-03` laag→midden. Dit stuurt rechtstreeks de gewogen score. |
| **Twee regels zijn bij de bron nog in discussie** | `STR-02` en `STR-04` hebben in ASTRA `Status=discussie`, niet `definitief` — juist de kick-off/genus-differentia-regels die de app als hard behandelt. |
| **Brondocument afgevlakt** | ASTRA onderscheidt DBT / Politie / MAS / VenV-MDM; de app zet 35× "ASTRA". Herkomst per regel is verloren. |
| **ESS-02 is opgerekt** | ASTRA: *"type of instantie"* (binair). App: vier UFO-categorieën (type/proces/resultaat/exemplaar). Bewuste eigen uitbreiding — maar niet als zodanig gedocumenteerd. |
| **DEF-605 is terecht tegen de bron** | ASTRA VER-01 bevat de plurale-tantum-uitzondering letterlijk, mét verwijzing naar de Wikipedia-lijst. Let op: die lijst noemt zichzelf *"onvolledig"* (~80 soortnamen). Een gecureerde eigen lijst is onvermijdelijk en moet als eigen projectbeslissing worden vastgelegd, niet als normverwijzing. |

---

## 6. Wat dit betekent voor DEF-606

Het antwoord op de kernvraag is **optie 1**, maar de klus die eronder ligt is niet "opruimen".

1. **Verwijderen kan** (`validators/` 45 + `regels/*.py` 47 + `json_validator_loader.py`) — de laag
   draagt de norm niet en lost geen enkel blind punt op. DEF-464 vervalt.
2. **De echte klus is regels classificeren naar toetsbaarheid**, en dat is precies de open vraag die
   DEF-606 zelf stelt:
   - *patroon-toetsbaar* → JSON-evaluator (de huidige weg, werkt voor ~24 regels);
   - *repository-toetsbaar* → aparte evaluator die de begrippenverzameling meekrijgt (6 regels);
   - *oordeel-toetsbaar* → LLM-jurering, óf expliciet markeren als niet-automatiseerbaar (8 regels).
3. **Zolang stap 2 niet gebeurt, is de kwaliteitsscore stelselmatig te hoog**: 15 regels dragen
   altijd 1,0 bij. Dat sluit aan op de eerder vastgelegde DEF-621-bevinding dat de score omhoog gaat
   bij een onvolledige regelset.
4. **Overweeg de ASTRA-wiki als bron te blijven volgen.** Hij is publiek, wordt actief beheerd (SES,
   2025) en is per regel op te halen via
   `https://www.astraonline.nl/index.php?title=<Regel-kort>&action=raw`. Een periodieke diff tegen
   de eigen JSONs vangt drift zoals hierboven automatisch af.

---

## Verantwoording

- **Code:** repo `/Users/chrislehnen/Projecten/Definitie-app`, branch `main`, HEAD `5cf2cd80`.
  De empirische matrix is gedraaid op een kopie waarvan de regel-JSONs en `rule_cache.py`
  md5-identiek zijn aan HEAD.
- **Norm:** astraonline.nl, verbatim opgehaald per regelpagina (`action=raw`), 36 regels.
- **Reproductie:** het duel-script leest per regel `goede_voorbeelden[0]` en `foute_voorbeelden[0]`
  en roept enerzijds `ModularValidationService._evaluate_rule`, anderzijds
  `JSONValidatorLoader.load_validator(...).validate(...)` aan.
- **Beperking, expliciet:** n = 1 voorbeeldpaar per regel. "Onderscheidt" bewijst niet dat een regel
  volledig correct is; "blind" bewijst wél dat de regel zijn eigen tegenvoorbeeld niet herkent.
  Voor de acceptatiecriteria van DEF-606 is een bredere voorbeeldset per regel nodig.
