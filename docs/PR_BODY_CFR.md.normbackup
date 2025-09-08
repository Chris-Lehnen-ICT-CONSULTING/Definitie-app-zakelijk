- Doel: CFR‑plan lean maken en afstemmen op Solution Architecture zonder over‑engineering.
- Scope: Geen herstructurering; integreer nieuwe onderdelen in bestaande modules (context, prompts, aggregation). UI/session state strikt uit services.
- Bewaking: CI/CD guards en contracttests toegevoegd; feature flag voor gefaseerde uitrol.

Wijzigingen
- Geen directory‑reorg: behoud bestaande boom; uitbreiden i.p.v. dupliceren.
- Integratiepunten:
  - Context mapping (PER‑007) in `definition_generator_context.py` (dedupe + determinisme).
  - MergePolicy in `data_aggregation_service.py` (optioneel `services/merge_policy.py`).
  - ContextFormatter in `services/prompts/context_formatter.py` (PROMPT‑ vs UI‑style).
- Performance‑budgets: expliciet “in‑process” (zonder LLM); e2e met LLM apart meten/rapporteren.
- CI/CD guards:
  - Verbied `streamlit`/`st.session_state` in `src/services/**`.
  - Schema‑tests voor EnrichedContext (vereiste keys/limieten).
  - Prompt‑style tests: PROMPT zonder emoji; UI met emoji; trimming/limieten afdwingen.
- Feature flag: `ENABLE_FULL_CONTEXT_FLOW` (aan in dev/test; uit in prod tot validatie rond is).

Niet In Scope
- Code‑wijzigingen of directory‑reorganisatie.
- Zware nieuwe modellen of aparte top‑level mappen (geen `src/models`, geen `services/formatting`/`aggregation`).

Risico’s & Rollback
- Risico: scope‑creep via reorg → gemitigeerd door integratie in bestaande lagen.
- Rollback: docs‑only; revert commit volstaat. Later code‑rollout gedekt door feature flag.

Review Checklist
- Past in SA (services UI‑agnostisch; DI‑singletons ok).
- Geen duplicatie van bestaande componenten; integratieplan is minimaal en concreet.
- Performance‑budgetten realistisch en duidelijk gescope’d.
- Guards/tests dekken regressierisico’s.
- Feature flag‑aanpak beschreven en beperkt van scope.

Links
- Plan: `docs/architectuur/CFR-IMPLEMENTATION-PLAN-AGENTS.md` (gereviseerd)
- Index: `docs/INDEX.md` (“READY FOR REVIEW”)
- Changelog: `CHANGELOG.md` ([Unreleased] bijgewerkt)
