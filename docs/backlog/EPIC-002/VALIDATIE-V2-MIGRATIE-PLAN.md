# Validatie V2 Migratieplan — Legacy → V2 consolidatie

Doel
- Eén valideerpad (V2) in de hele applicatie, zonder legacy/modulaire validators in runtime.
- Volledige, deterministische regeldekking via V2 (schema‑conforme output).
- Geen ruis in logs (geen missing‑module warnings, geen schema warnings).

Scope
- Vervangt aanroepen naar `ai_toetser/modular_toetser` en `toetsregels/modular_loader` door V2.
- Centraliseert validatie via `ValidationOrchestratorV2` / `ModularValidationService`.
- Maakt DB‑schema‑initialisatie idempotent (geen WARN bij bestaande tabellen).

Probleemobservaties (huidig)
- UI roept na de V2‑flow nog de legacy/modulaire validator aan → veel "Kon Python module niet laden" warnings en inconsistente regeldekking.
- V2 gebruikt een beperkte defaultregelset zolang er geen ToetsregelManager is aangesloten.
- DB‑init logt bij elke start "Schema execution warning: table definities already exists".

Duurzame oplossing
1) Schakel legacy validator in UI uit
   - Verwijder alle aanroepen naar legacy pad in UI (o.a. `src/ui/tabbed_interface.py`):
     - `from ai_toetser.modular_toetser import toets_definitie`
     - `from toetsregels.modular_loader import load_all_toetsregels`
   - Vervang door V2:
     - Gebruik het V2‑validatieresultaat dat de `DefinitionOrchestratorV2` al teruggeeft, óf
     - Roep `validation_orchestrator.validate_text(begrip, text, ontologische_categorie, context)` aan vanuit de container.

2) Volledige regelset via V2
   - Koppel een compacte ToetsregelManager‑adapter aan `ModularValidationService`:
     - Laad alle JSON‑regels (`src/toetsregels/regels/*.json`) → vul `_internal_rules` en `_default_weights`.
     - Laat per‑regel Python modules achterwege (tenzij expliciet nodig) om fragiele imports te vermijden.
   - Doel: V2 past de volledige regelset toe, deterministisch en zonder legacy loaders.

3) Centraliseer contract en output
   - UI leest alleen het canonieke V2‑formaat:
     - `overall_score`, `is_acceptable`, `violations[]`, `passed_rules[]`.
   - Verwijder/deprecate legacy objectvormen en dubbele mapping in UI.

4) DB‑schema idempotent maken
   - In `src/database/definitie_repository._init_database`:
     - Als `schema.sql` gebruikt wordt: check of kern‑tabellen bestaan (bv. `definities`) en skip `executescript` wanneer aanwezig.
     - Of pas `schema.sql` aan zodat alle `CREATE TABLE` uitspraken `IF NOT EXISTS` gebruiken.
   - Logniveau van reeds‑bestaat scenario → INFO (geen WARNING).

5) Opruimen en documenteren
   - Markeerstubs voor legacy validators (import werkt, maar niet meer aangeroepen; duidelijke waarschuwing).
   - Korte notitie in README/CHANGELOG en update van developer docs (V2‑only pad, contract en voorbeelden).

Uitvoering in fases
- Fase A (UI‑switch):
  - UI verwijdert legacy calls en gebruikt uitsluitend V2‑validatie (via orchestrator of rechtstreeks).
  - Verifieer dat validatiesecties in UI gevuld blijven met V2‑output.

- Fase B (V2 ToetsregelManager‑adapter):
  - V2 laadt alle JSON‑regels en weegt ze (prioriteit/weight in JSON).
  - Bepaal (optioneel) per‑regel hooks voor complexe checks via een stabiele V2‑interface (geen directe module‑imports).

- Fase C (DB‑schema):
  - Idempotente init of IF NOT EXISTS; downgrade warning naar info.

- Fase D (opschonen):
  - Markeer legacy validator‑paden als deprecated of verwijder ze uit runtime‑pad.

- Fase E (tests):
  - Update tests die nog `ai_toetser/modular_toetser` importeren.
  - Voeg een regeldekking‑smoke toe (aantal geladen regels via V2) en een logsanity‑check (geen missing‑module warnings).

Acceptatiecriteria
- UI gebruikt uitsluitend V2‑validatie; geen aanroepen naar `ai_toetser/modular_toetser` of `toetsregels/modular_loader` in runtime.
- V2 past de volledige JSON‑regelset toe (zichtbaar via een eenvoudige API/telemetrie of test‑assert op rule‑count).
- Geen "Kon Python module niet laden …" warnings meer in logs.
- Geen DB‑schema warnings; init is idempotent of logt alleen INFO wanneer schema bestaat.
- Bestaande integratie‑ en smokeslagen groen; V2‑response is consistent in UI.

Risico’s en mitigatie
- Per‑regel Python modules: als er unieke logica in zit, definieer gecontroleerde hooks (optioneel) en schrijf migratietests.
- Performance: V2 blijft deterministisch; rule‑set laden gebeurt éénmalig en kan gecachet worden.

Concreet te wijzigen call‑sites
- `src/ui/tabbed_interface.py`: verwijder imports/aanroepen naar legacy validators; gebruik V2‑data.
- `src/services/service_factory.py` / container: exposeer eenvoudige V2‑validate methoden (optioneel helper) voor UI.
- `src/database/definitie_repository.py`: maak `_init_database` idempotent of pas `schema.sql` aan.

Relatie met US‑179 (categorie‑doorvoer)
- Los te tracken (EPIC‑010/US‑179): ontologische categorie expliciet doorgeven aan promptmodules, zodat categorie‑specifieke instructies en templates actief zijn. Dit staat los van de validator‑consolidatie, maar is complementair voor de kwaliteit van de gegenereerde definities.

