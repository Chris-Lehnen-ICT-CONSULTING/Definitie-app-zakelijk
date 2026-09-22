# DEF-766 ESS-03 AI-beoordeling — voortgang fase 1 (uitvoerder: Claude Code CLI)

Werkboom: /Users/chrislehnen/.codex/worktrees/2075/Definitie-app · branch feature/DEF-766-ess03-ai-beoordeling · base 2c9a6e3a1

## Ontwerpkeuzes (na inspectie CON-02-patroon)

1. **Contractmodule** `src/domain/ess03/contract.py` (zuiver, geen AI/DB/Streamlit), naar analogie van `domain/sources/contract.py`.
   - `CONTRACTVERSIE = "ess03/1"`; vier inhoudelijke uitkomsten (`verdict`): `pass`, `fail`, `not_applicable`, `insufficient_information`.
   - Technische status van een beoordeling: `assessed | error | unavailable`.
   - Vingerafdruk over term, exacte kandidaattekst, drie contextlijsten, bedoelde betekenis (toelichting, opgegeven categorie als claim, betekenisverduidelijking, ESS-03-verduidelijking) en canonieke bronidentiteiten (hergebruik `canoniseer_bronnen`).
   - Bewijs: letterlijke citaten met vindplaats (`definition | term | toelichting | verduidelijking | context | source:<id>`), door code gecontroleerd (`vind_citaat`).
2. **Additieve statusrepresentatie** voor "niet van toepassing": nieuw `ResultStatus.NOT_APPLICABLE = "not_applicable"` in `toetsregels/runtime_contract.py`, gespiegeld in `toetsregels_config.yaml` (`result_status`), `interfaces.py` (Literal/TypedDicts), JSON-schema (2.1.0, additief), dekking (`evaluation_coverage.not_applicable`) en UI-labels. Bestaande statussen veranderen niet van betekenis; `evaluated` blijft pass+fail.
   - `insufficient_information` → `ResultStatus.REVIEW_REQUIRED` (open met precies één gerichte vraag in het deel); onderscheiden van "beoordeling niet beschikbaar" via het deel-id en de reden.
3. **Dienst** `src/services/validation/ess03_assessment_service.py`: één aanroep via `AIServiceInterface.generate_definition(task_type="validation")`, ModelRouter kiest model; parse fail-closed; cache alleen `assessed` op (vingerafdruk, promptversie, provider/model); geen retries; fouten → `status: error`.
4. **Evaluator** `CountabilityAssessmentEvaluator` (`EvaluatorType.COUNTABILITY_ASSESSMENT = "countability_assessment"`), ESS-03.json wijst hem aan; `automation_status: automated`, `score_policy: no_score` blijft.
5. **Keten**: `ValidationOrchestratorV2._beoordeel_telbaarheid` (async, vóór de sync evaluator), `context_dict["ess03_assessment"]`, `result["ess03_assessment"]`; container + DefinitionOrchestratorV2 injecteren de dienst.
6. **Niet-blokkerend**: ESS-03-FAIL levert een violation met expliciete severity-override (`warning`/`medium`) zodat noch `acceptance_gate` (critical-telling) noch de vaststel-gate (`Kritieke issues`/`hoge issues`) erdoor verandert; getest op `_evaluate_gate` en `is_acceptable`.
7. **Opslag**: `generation_prompt_data["ess03_assessment"]` (bestaande JSON-kolom, geen schema), structurele updates-sleutel `ess03_assessment`, herstel naar `Definition.metadata["ess03_assessment"]`, binding via vingerafdruk (stale ⇒ niet toegepast, zichtbaar).

## Log
- 09:0x Inspectie CON-02-patroon, evaluatorregister, orchestrators, DB-laag, UI, gate, bestaande ESS-03-tests afgerond.
- WP1 contract: RED exit 2 (collectiefout) → GREEN 44 passed (tests/unit/domain/test_def766_ess03_contract.py).
- WP2 dienst+prompt: RED exit 2 → GREEN 26 passed (tests/unit/validation/test_def766_ess03_assessment_service.py).
- WP3 evaluator/keten: RED exit 2 → GREEN 30 passed (test_def766_ess03_evaluator.py); wrappers RED 9 failed → GREEN 9 passed (test_def766_ess03_wrappers.py). Regressie gerelateerde suites: 2134 passed.
- Oude ESS-03-tests inhoudelijk vervangen (judgment_review-branches verwijderd; matrixtelling 36/13/4; AI-oordeelklasse CON-02+ESS-03; contractversie 2.1.0).
- WP4a UI: RED 7 failed → GREEN; volledige tests/unit/ui: 577 passed na aanpassing dekkingsdict-test.
- WP4b persistentie: RED exit 2 → GREEN 15 passed; WP4c editor: RED 5 failed → GREEN 6 passed; WP3c generatie-integratie: RED 4 failed → GREEN 10 passed.
- 12 ontwikkelgevallen vastgelegd (tests/fixtures/ess03/ontwikkelgevallen_v1.json) vóór de eerste modelaanroep; echte run 12 calls claude-opus-4-8: 9/12 conform, 0 rejected (ontwikkelrun-v1.json).
- make lint exit 0; markers OK; root-allowlist OK; make test run 2: 6764 passed, exit 0.
- Manifest en verslag geschreven: phase1-manifest-v1.json, phase1-report-v1.md. Uitvoerder stopt; wacht op eindtestset.
