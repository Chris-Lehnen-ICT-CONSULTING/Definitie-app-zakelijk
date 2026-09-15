## Uitkomst: één resterende P2-bevinding

### P2 — Tegenstrijdige claims verbruiken alsnog de ene voorstelpoging

**Locatie:** [source_proposal_service.py:174](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/source_proposal_service.py:174), doorwerking bij [regel 365](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/source_proposal_service.py:365).

**Trigger:** een geldig gebonden AI-assessment met `semantic_support=fail`, geverifieerd bewijs en twee claims met **identieke `text`, `aspect` en `source_id`**, maar respectievelijk `supported: true` en `supported: false`. Geen expertcorrectie en geen afgewezen bewijs.

`_negatieve_claims` selecteert uitsluitend de negatieve claim en controleert niet of dezelfde claim ook positief wordt beoordeeld. C behoudt deze combinatie bij `fail`; zijn aanvullende consistentiecontrole geldt voor `pass`. F retourneert daardoor `defective_definition` en reserveert bij [definition_edit_service.py:894](/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app/src/services/definition_edit_service.py:894) de duurzame poging.

**Impact:** een intern tegenstrijdig evaluatoroordeel wordt behandeld als geverifieerde teksttekortkoming en verbruikt de enige poging.

**Gerichte oplossing:** blokkeer deze tegenstrijdigheid vóór reservering. Behoud het afzonderlijke pad voor een deskundige negatieve correctie met eigen gebonden bewijs. Dit is een F-diagnosebevinding, geen heropening van C.

Statisch vastgesteld; dit exacte conflict is niet uitgevoerd en ontbreekt in de geïnspecteerde claimregressies.

## Afhandeling van de drie eerdere bevindingen

| Onderdeel | Dispositie |
|---|---|
| **1. Onopgeslagen tekst bij Apply** | **Code gesloten.** Knop en handler controleren dezelfde bewerking; de handler stopt vóór dienstaanroep en pending-widgetwijziging. De volledige AppTest controleert widget/DB/versie/voorstelbehoud, en na expliciet opslaan weigering met `stale_original`. Bestaande Apply-plus-herladen-test blijft aanwezig. Testdrift beperkt de vrijgave hieronder. |
| **2. Verouderd sessieoordeel versus expertcorrectie** | **Gesloten.** Altijd replay met actuele opgeslagen `source_review` en definitieversie; sessiegegevens leveren uitsluitend exact gebonden assessmentinvoer. Regressies controleren beide correctierichtingen, inclusief oorspronkelijke AI-pass → deskundige fail met eigen bewijs. |
| **3. Concrete negatieve claim vereist** | **Gedeeltelijk gesloten.** Lege, ongebonden en niet-negatieve claims blokkeren vóór reservering. Bovenstaand conflict blijft open. |
| **Aanvullende score-UI** | **Geen bevindingen.** Beide wijzigingen verwijderen uitsluitend het definitiekwaliteitstotaal, inclusief de `None`-formatteerfout. Definities, categorieën, acties en afzonderlijke classificatie-/matchmetriek blijven behouden. |

## Bewijs en beperkingen

Uitsluitend statische review en lezing van bestaande resultaten; **geen tests, imports of lint uitgevoerd**.

- [F-testlog](/tmp/DEF-743-ui-final-fix-targeted.log): 260 `PASSED`-regels, exit 0, inclusief genoemde regressies en volledige AppTests.
- [F-lintlog](/tmp/DEF-743-ui-final-fix-lint.log): Ruff en Black exit 0.
- [Aanvullend UI-testlog](/tmp/DEF-743-ui-score-residual-green.log): 26 passed, exit 0.

**Geen productdrift. Wel testdrift:** `test_def743_editor_apptest.py` veranderde tijdens deze review. De eindversie krijgt geen goedkeuring op basis van het eerdere groene log.

DEF630-`None`-scoregate is niet heropend. Geen volledige feature-Done of expertacceptatie; de canonieke rootgate blijft afzonderlijk.

## Eigen SHA-256: begin = einde

```text
120eb4f40fdb756cda83b5ee0fb8be61b3db89d0db23fab4f322b89ada2d8a65  src/services/source_proposal_service.py
5ba545d139fe708903c4ae9e0ea5ad9d5e42bbdc35c6d3d46fee31b3b63954ad  src/services/definition_edit_service.py
ef20fb662c5d538a39093a30064105eb25baac6beab1035703c6a8df8f3c3cfe  src/services/definition_workflow_service.py
8d47f9f36ccb6ca844a825c671a7a23519c7f4f90760c49ebe8ad91efbdf72ec  src/ui/components/definition_edit_tab.py
2b99f69691493836364f7c5157e3cde783d51e53c3d1979424d7859b2db0a462  src/ui/components/expert_review_tab.py
c3f63803222e7933e754667ca1c4f75955f212cf15383952746613f012013f38  src/ui/components/validation_view.py
2577e998136b686aedecac350c07f70f7c59c5cd32d459f7e5235a85ae700a49  src/ui/components/sources_renderer.py
3faf5cfe1106377f62364a80248e9f92fc35b5d5a6f24dc59f88c4549bdec4f3  src/ui/components/definition_generator_tab.py
8ac1197e803260bcdd72d13f4e097212e3562c98d5932b2a8d76ddb761753d29  src/ui/tabbed_interface.py
23fa120136de57aa3875211c7ae3d2edf2018750f68a9583a5e85b3c76b35e72  src/ui/components/tabs/import_export_beheer/format_exporter.py
fd7cb7245edf84af4f4cbb6e864d526a9c5421f6f02f0187dae0259b949fe273  src/ui/components/duplicate_check_renderer.py
5842e78f99a623ada61dbccca28f23c40e96d566405f443beb3909986cba1bc8  src/ui/components/category_renderer.py
ab2f30277d11c483fcd7ecd2223c55de5a251c40cd31f2b8b06935fd68c2dfeb  tests/fixtures/def743_fakes.py
87c3a4ca442d868ea83e37f5be3c4379bf544cd8bfe595fc35a03e5ab1851ed6  tests/unit/services/test_def743_voorstelworkflow.py
451da52b66091aa37f14be79d0b18da70e2606903ef8cfa78b05827b20ff1e66  tests/unit/services/test_def743_editor_pariteit.py
0ad0b497e2753ac94938a6d4dda0346410401492773ce6748ac035d7d43efafc  tests/unit/ui/test_def743_editor_ui.py
6916b9c73a3da5bb611628f45135b6d0226d736e8dd6860d4be1045be9a5bfc9  tests/unit/ui/test_def743_overige_scoreweergave.py
```

**Exacte drift — `tests/unit/ui/test_def743_editor_apptest.py`:**

```text
begin  82a02941635677754611aece4acd049f414a307139e6ef49d6d374201329897e
einde  722a3451b9cc0a5d44f72ca92e50f68a9543e48b69e5bfdb03e4f31d92572761
```