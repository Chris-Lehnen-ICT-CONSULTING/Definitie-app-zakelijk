# DEF-622 contextcontract — implementatieplan

> Uitvoering: **executing-plans**, **test-driven-development**, **requesting-code-review**, **verification-before-completion**.

**Doel:** B-01 t/m B-10 doorvoeren in het actieve context-, validatie-, duplicaat- en vaststelpad, met onderscheidend gedrag en behoud van historie.

**Architectuur:** Hergebruik de drie canonieke lijsten en `domain/context/normalisatie.py`. CON-01 beoordeelt aanwezigheid en de functie van geselecteerde namen; DUP_01 blijft eigenaar van duplicaatbevindingen. Gebruik de bestaande SQLite-transactie en versiecontrole voor vaststelling; DEF-630 blijft eigenaar van de algemene kwaliteits-/exportgate.

**Stack:** Python 3.13, SQLite, Streamlit, pytest; geen nieuwe dependencies.

## Besluiten en afhankelijkheden

- Basis: schone eigen worktree, branch `feature/DEF-622-contextcontract`, `origin/main` = `d68a98a90` na fetch op 14 september 2026.
- Leidende bron: actuele DEF-622 inclusief B-10, plus rechtstreeks gelezen `besluiten-v10.md` uit de ab46-bronworktree. Synthese v4 en duplicaatcontrole v1 zijn historische implementatiebronnen, geen actueel uitvoeringsbewijs.
- DEF-621, DEF-674 zijn Done. DUP_01 draagt inmiddels duplicaatdetectie; CON-01 draagt uitsluitend formulering. Contextnormalisatie bestaat al.
- DEF-464 is Backlog en reserveert cleanup na pariteitsbewijs; geen oude Pythonvalidator aansluiten of verwijderen.
- DEF-630 is Backlog; snapshot-/stale-/identity-/ontologyvoorwaarden blijven daar en bij DEF-626/627/617/642. Geen volledige productketen claimen zolang verplichte afhankelijkheden ontbreken.
- Appbrede scorekeuze is nog niet besloten. Vraag is gesteld; onafhankelijke transport-/duplicaatwerkzaamheden kunnen doorgaan. Geen impliciete score 0/1 voor CON-01.
- Categorie telt nu bij generatorlookup én DUP_01 mee wanneer opgegeven. Behoud dit bestaande onderscheid voor lookup; voorkom dat categorie een ontsnapping wordt aan de vastgestelde exclusiviteit voor begrip + volledige context. Verschil expliciet testen.
- Lopende zichtbare Codex-taak CON-02 betreft onderzoek. Geen actieve DEF-630/464-implementatietaak aangetroffen in de taaklijst; beide issues staan Backlog.
- Opdracht autoriseert de noodzakelijke code-, prompt-, UI- en testwijzigingen en een reviewbare PR; geen merge/deploy, geen bronworktree wijzigen, geen gebruikersdatabase gebruiken.

## Uitvoeringsstappen

### 1. Contexttransport (onafhankelijk)

Bestanden: `src/services/orchestrators/validation_orchestrator_v2.py`; nieuw `tests/unit/services/orchestrators/test_def622_context_transport.py`.

1. Schrijf een test waarin `validate_text` metadata met alle drie lijsten ontvangt en de echte servicegrens inspecteert; controleer invoer onveranderd.
2. Schrijf een test waarin een Definition met lege en gevulde lijsten expliciet prevaleert boven conflicterende caller-metadata; controleer categorie/id voor duplicaatuitsluiting.
3. Draai de tests en bewaar de verwachte ontbrekende-contextasserties.
4. Transporteer metadata en gebruik de bestaande enrichmenthelper met canonicalisatie, inclusief expliciete lege lijsten; geen soft-fail op dit contract.
5. Draai nieuwe tests plus bestaande orchestrator-tests; commit deze transportstap.

### 2. CON-01-uitkomstcontract

Bestanden: `src/domain/context/contract.py` (nieuw), `src/services/validation/evaluators/context_metadata.py`, `src/toetsregels/regels/CON-01.json`, `src/services/validation/modular_validation_service.py`; nieuw `tests/unit/validation/test_def622_context_contract.py`.

1. RED: ontbrekende/lege context, dynamische naam, gewoon woord zonder geselecteerde naam, noodzakelijke naam met actuele onderbouwing, registratiegebruik, open én falend, technische fout; geen cijfer.
2. GREEN: gestructureerde deeluitkomsten met aanleiding, reden, actie en runtimeoorzaak; alleen inhoudelijk beoordeeld registratiegebruik faalt. Bind beoordeling aan exacte tekst en canonieke context, actor en contractversie.
3. Behoud deeluitkomsten door service en schemas; geen impliciete numerieke pass/fail. Score-afhankelijke wijziging pas na antwoord op de open productkeuze.
4. Bewijs gedrag via echte V2 + productiemanager/cache; commit.

### 3. Gelijke context en drie generatiekeuzes

Bestanden: `src/database/definitie_crud.py`, `src/ui/components/duplicate_check_renderer.py`, `src/ui/components/definition_generator_tab.py`, `src/ui/handlers/definition_generation_handler.py`, `src/services/validation/evaluators/duplicate_detection.py`.

1. RED: case/volgorde/dubbele waarden herkennen; overlap en categorieverschil niet als exacte lookup behandelen; bestaand vastgesteld record heeft voorkeur boven concept/historie.
2. GREEN: deel normalisatie en match volledige lijsten; vermijd onbegrensde lookup buiten begrip.
3. RED: Gebruik Deze toont daadwerkelijk gekozen record, Bewerk opent bewerkpad, Genereer Nieuw draagt verplichte reden en maakt concept zonder mutatie bestaand record; force-keuze blijft niet plakken.
4. GREEN: sluit de daadwerkelijke consumenten aan; test renderer met Streamlit AppTest en synthetische repository.
5. Regressies en commit.

### 4. Vaststelconflict en verplichte CON-01-beoordeling

Bestanden: `src/services/definition_workflow_service.py`, `src/database/definitie_crud.py`, `src/database/definitie_repository.py`, `src/services/definition_repository.py`; nieuwe tests onder `tests/unit/services/`.

1. RED: geen context ondanks override weigeren; open naamfunctie weigeren; gewijzigd bewijs weigeren; concept blijft mogelijk.
2. RED: bewuste keuze om bestaand vastgesteld record te vervangen vereist; twee concurrerende vaststelpogingen laten nooit twee leidende records over; auditfout rolt beide wijzigingen terug.
3. GREEN: hercontroleer conflict onder dezelfde transactielock, archiveer goedgekeurde vervanging en stel nieuwe definitie atomair vast met bestaande expected_version-guard en statusaudit.
4. Bewijs onderscheid tussen per-record DEF-482-garantie en nieuwe inter-recordconflictafhandeling. Algemene gatevoorwaarden blijven expliciete DEF-630-afhankelijkheid.
5. Regressietests DEF-482; commit.

### 5. Opslag, UI, prompts en exportaansluiting

Bestanden: relevante adapters in `src/services/definition_repository.py`, `src/services/export_service.py`, `src/ui/components/validation_results_renderer.py`, `src/ui/components/definition_edit_tab.py`, `src/services/prompts/modules/context_awareness_module.py` en actieve CON-01-instructieconsumenten (precieze callsites vastleggen vóór wijziging).

1. RED: readback bewaart drie lijsten, CON-01-deeluitkomsten en actuele beoordeling; gewijzigd concept hergebruikt geen oud oordeel.
2. RED: Nederlandse presentatie toont aanleiding/reden/vervolgstap voor alle drie statussen en falen plus open; technische fout apart. Expert kan naamfunctie gemotiveerd afhandelen binnen bestaande handmatige flow.
3. GREEN: bewaar bewijs en toon uitkomsten; lijn actieve prompts af op noodzakelijke-naamuitzondering, zonder algemene passendheidstoets uit DEF-742 toe te voegen.
4. Controleer relevante import-/exportgrenzen met synthetische data en benoem wat door DEF-630 geblokkeerd blijft. Skills buiten project alleen via reviewbare bronpatch, niet stil live overschrijven.
5. Regressies en commit.

### 6. Verificatie en oplevering

1. Gerichte tests: `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest <nieuwe-en-relevante-tests> -q` (offline-bootstrap actief, uitsluitend tijdelijke synthetische DB's).
2. Projectgates: `make PY=/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python test`, `make ... test-integration`, `make ... test-acceptance`, `make ... lint`. Bewaar logs onder `reports/` en lees exitstatus/inventaris.
3. Onafhankelijke code-review op exacte diff, concrete bevindingen oplossen en noodzakelijke deltaverificatie.
4. DEF-622 bijwerken met scope, uitgevoerde proeven en resterende eigenaren/afhankelijkheden. Geen Done bij open acceptatiecriteria.
5. Reviewbare PR; geen merge of deploy. Bij noodzakelijke open afhankelijkheid eerlijk als draft/deellevering presenteren.
