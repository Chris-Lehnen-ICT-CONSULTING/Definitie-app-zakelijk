# DEF-606 — Antwoord op de kernvraag (git-archeologie)

**Datum:** 11 augustus 2026
**Vraag:** Was de 12.893-regels `.py`-validatorlaag bedoeld als vervanging van `_evaluate_json_rule`, of is het een restant?

## Antwoord: optie 1 — restant. De `.py`-laag is de vóórganger, niet de opvolger.

De richting van de migratie is omgekeerd aan wat het issue als mogelijkheid openliet.
`_evaluate_json_rule` is **twee maanden jónger** dan de `.py`-laag en heeft die vervangen —
niet andersom.

---

## 1. De tijdlijn (uit git, geverifieerd)

| Datum | Commit | Wat er gebeurde |
| --- | --- | --- |
| 2025-07-10 | `c6bbaf20` | Modulair toetsregelsysteem: elke regel krijgt een eigen JSON-bestand. |
| 2025-07-16 | `d7df1c43` | *"Implementeer hybride toetsregel migratie — alle 45 regels"*: de legacy `core.py`-monoliet wordt uitgesplitst naar 45 losse Python-modules, geparkeerd in `regels_backup_20250716_153755/`. |
| **2025-07-17** | **`4bcfba68`** | *"Vervang BaseValidator met flexibele JSON/Python validators"*: de `.py`-laag wordt **geactiveerd** ("45 validators geactiveerd (was 16) uit backup directory"), `JSONValidatorLoader` wordt gebouwd en aangesloten op `src/ai_toetser/modular_toetser.py`. **Dit was het productiepad.** |
| **2025-09-17** | **`3ea307e0`** | *"Enhanced V2 validation with JSON rule evaluation"*: `_evaluate_json_rule` wordt geboren — in een **andere** service (`ModularValidationService`, de V2-keten). Raakt de loader niet aan. |
| 2026-04-14 | `a5794ccb` | DEF-189 verwijdert `src/ai_toetser/` als *"legacy test-only shim, zero productie-gebruik"* — dat wás de enige consument van de `.py`-laag. `json_validator_loader.py` verhuist naar `src/toetsregels/` en blijft ongebruikt achter. |

Vandaag staat het letterlijk in de code, in `src/services/service_factory.py:8`:

> *"Er is geen legacy validatorpad meer; validatie loopt via V2 (ValidationOrchestratorV2/ModularValidationService)."*

De `.py`-laag is dus niet "nooit aangesloten geweest". Hij is **aangesloten geweest, vervangen, en
in april 2026 losgekoppeld toen zijn consument werd opgeruimd.** De bestanden bleven staan.

---

## 2. Waarom optie 2 ("migratie afmaken") technisch niet kán

De 9 verkeerd bedrade regels uit het issue zijn **niet ontstaan door latere hernummering van de
JSON-set.** Ze waren fout vanaf de geboortedag.

- `SAM-02.json` heet **onafgebroken sinds 2025-07-10** "Kwalificatie omvat geen herhaling"
  (gecontroleerd per commit: `c6bbaf20` → `5cb205e8` → `a4bb15cf` → `e2af435d` → `95be7c2e`; nooit gewijzigd).
- `SAM_02.py` zegt sinds **2025-07-17** in zijn docstring: *"Toetsregel SAM-02: Geen vage kwantoren —
  **Gemigreerd van legacy core.py**"*.

Die docstring-regel `Gemigreerd van legacy core.py` staat vandaag nog in **100 bestanden**.

Dat is de hele verklaring: de nummering van de regels in de oude `core.py` kwam **niet overeen** met
de nummering van de JSON-regelset. De bulk-migratie van 16 juli koppelde ze puur op bestandsnaam.
De `.py`-laag heeft de huidige 53-regelset dus **nooit correct geïmplementeerd** — geen enkele dag.

Gevolg voor optie 2: er is geen "steken gebleven migratie" om af te maken. Wie de loader aanzet,
moet 9 validators **from scratch** herschrijven, en heeft daarnaast geen enkele referentie-
implementatie voor de 7 baselineregels (`CON-CIRC-001`, `ESS-CONT-001`, `STR-ORG-001`,
`STR-TERM-001`, `VAL-EMP-001`, `VAL-LEN-001`, `VAL-LEN-002`) of voor DUP. Dat is geen migratie
afmaken, dat is een nieuwbouwproject met een misleidende voorraad oude code als startpunt.

---

## 3. Correcties op de cijfers in het issue

Het issue meldt *"34 paren byte-identiek, 2 verschillen, 10 bestaan alleen in `validators/`"*.
Hermeting (`cmp` over alle 45 paren, met beide naamconventies):

| | Issue | Gemeten | Toelichting |
| --- | --- | --- | --- |
| byte-identiek | 34 | **42** | De issue-analyse paarde alleen op `_` → `-` en miste daardoor de ARAI-conventie (`ARAI01.py` ↔ `ARAI-01.py`). 8 van de 9 ARAI-paren zijn óók byte-identiek. |
| verschillen | 2 | **3** | `ARAI-01`, `CON-01`, `SAM-07`. |
| alleen aan één kant | 10 | **1** | Alleen `DUP_01`, en die zit aan de `regels/`-kant, niet in `validators/`. |

Reconciliatie: 34 + 8 = 42, en 2 + 1 = 3. De "10 alleen in validators" waren de 9 ARAI-bestanden
die wél een tegenhanger hebben.

Bestandstellingen: `validators/*.py` = 45 · `regels/*.py` = 47 · `regels/*.json` = 53.

### De 3 afwijkende paren bevestigen het risico uit de juli-review

Bij alle drie is een fix in één kopie geland en niet in de andere:

- `regels/ARAI-01.py` kreeg op 2025-11-10 de fix uit **DEF-138** ("ontological category
  contradictions"). Die kopie wordt door **niets** geladen — ook niet door de loader, want die
  leest Python uitsluitend uit `validators/`. De fix is dus nooit ergens uitgevoerd.
- `validators/CON_01.py` (273 regels) en `regels/CON-01.py` (217 regels) zijn structureel
  uiteengelopen — dit is precies DEF-464.
- `validators/SAM_07.py` heeft een failure-branch die in `regels/SAM-07.py` ontbreekt.

---

## 4. Wat dit betekent voor de planning

**DEF-606 wordt: opruimen + de dekking verplaatsen naar de laag die wél draait.**

- **DEF-464 vervalt** — gaat op in de verwijdering.
- **DEF-424 blijft gewoon de god-object-refactor** van `ModularValidationService` (1.766 regels).
  Er komt geen "wordt meegelost door de migratie"-korting.
- **DEF-503 herformuleren** naar gedragstests op `_evaluate_json_rule` + de hardcoded special-cases.
  De huidige testinspanning zit op de dode laag.

### Meeverwijderen bij de sanering (anders blijft er een loader zonder lading)

- `src/toetsregels/json_validator_loader.py` — 0 referenties in `src/`.
- `src/toetsregels/validators/` (45 bestanden) en de 47 `.py` in `src/toetsregels/regels/`
  (de 53 `.json` in die map blijven natuurlijk staan — dat is de live regelset).
- Tests die uitsluitend de dode laag dekken: `tests/unit/validation/test_json_validators.py`,
  `test_validators_interface_sweep.py`, `test_con01_duplicate_count.py`, `test_DUP_01.py`,
  plus de betreffende delen van `test_working_system.py`, `test_regression_suite.py` en
  `test_performance_comprehensive.py`.

### Eén controle vóór het weggooien

De `.py`-bestanden bevatten per regel uitgewerkte regex-patronen die de generieke evaluator soms
mist (`CON_01.py` is 273 regels, `ESS_02.py` 231). Loop ze één keer door op oogstbare patronen
vóórdat ze verdwijnen. Gecontroleerd: een rijkere pluralia-tantum-lijst voor **DEF-605** zit er
níet in — die staat alleen in `VER-01.json`.

---

## Bronnen

Alle bevindingen komen uit de repo zelf (`/Users/chrislehnen/Projecten/Definitie-app`, branch `main`,
HEAD `5cf2cd80`) en uit Linear DEF-606.

Commits: `d7df1c43`, `4bcfba68`, `3ea307e0`, `a5794ccb`, `c6bbaf20`, `5cb205e8`, `95be7c2e`, `333f67f1`.
Bestanden: `src/toetsregels/json_validator_loader.py:66-95`, `src/services/validation/modular_validation_service.py:790-870`,
`src/services/service_factory.py:8`, `src/toetsregels/loader.py`.
