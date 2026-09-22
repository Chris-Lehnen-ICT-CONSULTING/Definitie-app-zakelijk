## 📋 PR Type
- [x] ✨ New feature (non-breaking change which adds functionality)
- [x] 🔧 Configuration change
- [x] ✅ Test update

## 📄 Description
ESS-03 (telbaarheid / instanties uniek onderscheidbaar) wordt door de app zelf inhoudelijk beoordeeld via één AI-beoordelingsdienst op de bestaande AIServiceV2/ModelRouter-route. Vier scoreloze uitkomsten: voldoet, voldoet niet, niet van toepassing, onvoldoende informatie (met precies één gerichte vraag). Alleen aangeleverde informatie (kandidaat, bedoelde betekenis, context, bronnen), gesloten parser met citaatcontrole tegen het werkelijk verzonden materiaal, volledige binding (kandidaat/term/context/bronnen/norm/prompt/model) bij opslag en replay, verouderde beoordeling nooit stil actueel. Een negatieve uitkomst blokkeert vaststellen/export niet en start geen automatische herschrijving. Alle ESS-03-uitkomsten blijven `no_score`.

Daarnaast: app-default van `claude-opus-4-8` naar `claude-opus-5`; configuratiegestuurde thinking-guard (`thinking=disabled` voor opus-5/sonnet-5, andere modellen byte-identiek); `stop_reason` uit het API-antwoord in `ChatResponse` en `AIGenerationResult.metadata`; afkapping (`max_tokens`) in ESS-03 als technische fout `truncated_response` (fail-closed, niet gecachet).

## 🔗 Backlog Link
Ref: DEF-766 (onder DEF-606). Besluitdocument: https://linear.app/definitie-app/document/def-766-ess-03-ai-beoordeling-besluiten-en-uitvoeringsplan-21-fa353ea41dcb

## 🎯 Changes Made
- `6c71bf128` feat: contract (`src/domain/ess03/contract.py`), dienst (`src/services/validation/ess03_assessment_service.py`), evaluator (`countability_assessment.py`), container/orchestrator-integratie, opslag via bestaande JSON-metadata (`ess03_assessment`, `ess03_assessment_history`, `ess03_verduidelijking`), editor-UI met verduidelijkingsveld en herbinding, additieve `not_applicable`-representatie in runtimecontract/schema (2.1.0); ~1.900 regels wijzigingen + nieuwe tests. Fase 1 + twee correctieronden (R1–R9, A/B/C) door Claude Code CLI, onafhankelijk gereviewd.
- `0ec86aced` chore: app-default naar `claude-opus-5` (ModelRouter `_DEFAULT_CONFIG`, prijstabel).
- `c0d3423ab` fix: thinking-guard (`config/config.yaml` `model_routing.capabilities.anthropic.thinking_default_on`, `ModelRouter.thinking_default_on`, `AnthropicClient._verzendbeleid`), `ChatResponse.stop_reason` + transport via `response_hook`, ESS-03 `truncated_response`; None-guard voor mypy in `definition_edit_tab.py`.
- Bewuste afwijking van de globale drempel (>100 regels/>5 bestanden): vooraf geautoriseerd in het plan van 21-09 (`docs/plans/2026-09-21-DEF-766-ess03-ai-beoordeling-v1.md`).

## 🧪 Testing
- [x] Unit tests pass — `make test` 6902 passed, 0 failed (unitgate, exit 0); `make lint` schoon; complexity 199 < baseline 201; mypy 0; markers 491/491; root-allowlist en TODO-check schoon.
- [ ] Integration tests pass — niet gedraaid (gate is unit-only, zie CLAUDE.md coverage-baseline).
- [x] Manual testing completed — browsercontrole op de eindstand (Opus 5): onvoldoende informatie → verduidelijking → opnieuw toetsen → voldoet → opslaan → heropenen actueel → tekstwijziging maakt oordeel historisch; 2 echte calls.
- [x] No regression in existing functionality — golden ESS-tests, runtime-matrix, DEF-743/751/622/624/808 editor- en orchestratorregressies groen (1053 + 1899 passed in gerichte runs).

**Inhoudelijke eindtest (30 echte calls op `claude-opus-5`, verzegelde onafhankelijke set van 20 gevallen, 5 per uitkomst):** 19/20 zoals vooraf vastgelegd (voldoet 5/5, voldoet niet 4/5, niet van toepassing 5/5, onvoldoende informatie 5/5); 0 onterechte goedkeuringen; 0 technische fouten; 113/113 citaten letterlijk; 3 metamorfosen, 2 injectiepogingen en 4 herhalingen behouden uitkomst en grond. Enige afwijking HT08: model gaf "onvoldoende informatie" (met gerichte vraag) waar "voldoet niet" was vastgelegd — conservatief; eigenaar accepteert deze Opus-5-strengheid, prompt bewust niet bijgesteld. Synthetische set, geen expertgoldset, geen statistische claim.

**Onafhankelijke reviews** (Claude Code CLI, aparte sessie, read-only): delta-review v1 (geen blokkerende bevindingen; F1 gefixt in `c0d3423ab`), delta-review v3 (JA), inhoudelijke eindtestreview (inhoudelijk gereed voor merge). Rapporten en al het bewijs staan lokaal onder `reports/DEF-766-AI-20260921/` (git-ignored; duurzame locatie nog te bepalen, zie disposities).

## 📊 Performance Impact
- [x] Potential performance impact (describe mitigation) — per validatie één extra AI-call (ESS-03, ~7–16 s, max_tokens 1200, deadline 60 s, geen retries, cache alleen op volledige binding). Thinking uit op Opus 5 houdt de bestaande tokenbudgetten app-breed geldig.

## 🔄 Migration Required
- [x] No migration required — opslag via bestaande JSON-metadata; geen schemawijziging, geen nieuwe dependency.
- [x] Configuration change required — `config/config.yaml` `model_routing.capabilities.anthropic.thinking_default_on` (in deze PR).

## 📚 Documentation
- [x] Added/updated code comments
- [x] Added ADR (Architecture Decision Record) — `docs/adr/ADR-002-menselijke-regelbeoordeling-v1.md` is een bewaard, **niet-leidend** eerder voorstel (menselijke beoordeling); het leidende besluit staat in het plan van 21-09 en in Linear.

## ✅ Checklist
- [x] My code follows the project's style guidelines
- [x] I have performed a self-review of my own code
- [x] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation — regel-/UI-hulptekst over de Opus-5-neiging (K1/K2) volgt als tracked issue
- [x] My changes generate no new warnings or errors
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] New and existing unit tests pass locally with my changes
- [x] Any dependent changes have been merged and published (#465 bugfix ESS-03 scoreloos)
- [x] Contract schema validation uitgevoerd — `docs/architectuur/contracts/schemas/validation_result.schema.json`, `test_root_ssot_contract.py`, `test_rule_runtime_matrix.py`
- [x] ValidationResult contract compliance verified — runtimecontract 2.1.0, additief `not_applicable`
- [x] No TODO/FIXME/XXX/TBD/HACK markers in code (CI will enforce)

## 🚀 Deployment Notes
Openstaande disposities (geen blokkade voor merge, wel vast te leggen):
- F2: technische ESS-03-fout telt als `evaluation_error`-acceptatieblokkade via bestaand DEF-624-beleid — waiver of tracken onder DEF-630.
- F3 (schrijfroute bij onbekende binding meldt "actueel"), F4 (negatieve readbacktest betekenisverduidelijking), F5 (`_Pogingenteller` niet thread-veilig) — tracked issues.
- D1: `fable-5`/`mythos-5` bewust niet in `thinking_default_on` (waiver; app routeert er niet naar).
- K1/K2: Opus-5-neiging naar "onvoldoende informatie" bij verwijzende formuleringen/placeholders — documenteren in regel-/UI-hulptekst.
- K6: `reports/` is git-ignored; bewijs duurzaam onderbrengen (voorstel `docs/analyses/def606-regeldossiers/ESS-03-fix/`).
- Geen live-skillinstallatie (ALG-391-freeze).

## 🔐 Security Checklist
- [x] No hardcoded secrets or credentials — gitleaks-hook groen; constante hernoemd (`ESS03_VERDUIDELIJKING_VELD`) om een vals alarm te vermijden
- [x] Input validation implemented — gesloten parser, citaatcontrole, materiaal als data (injectiebescherming, 2 injectiegevallen in de eindtest)
- [x] No SQL injection vulnerabilities — bestaande parametrized CRUD
- [x] Proper error handling (no sensitive data in errors) — oorzaakketen geredigeerd, geen sleutels/promptinhoud in logs
- [x] Authentication/authorization checks in place — n.v.t.

## 🎭 Feature Flag (if applicable)
Geen feature flag: de dienst is standaard geïnjecteerd (acceptatiecontract punt 10). Terugdraaien = revert van de drie commits; de modelwissel (`0ec86aced`) is los terug te draaien.

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_016yYJevjJW3ADkaBePctPhk
