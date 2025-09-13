---
canonical: false
status: active
owner: architecture
last_verified: 2025-09-12
applies_to: definitie-app@current
---

# US-064 – Definition Edit Interface: Implementatieplan (Codex-editie)

Deze Codex-notitie beschrijft de implementatie voor US-064. Het plan volgt de projectrichtlijnen (README.md, CLAUDE.md) en sluit aan op EPIC‑012 (orchestratieconsolidatie) en US‑062 (FeedbackService). Dit document is niet‑canoniek en dupliceert geen bestaande besluiten; het biedt een uitvoergerichte weergave voor implementatie.

Gerelateerde documenten
- Story: docs/backlog/EPIC-004/US-064/US-064.md
- Architectuur: docs/backlog/EPIC-012/EPIC-012.md (Phase 2: update_definition flow)
- Feedback: docs/backlog/EPIC-012/US-152/IMPLEMENTATION_PLAN.md (verwijst naar US‑064)

## Doelen
- Editor toont standaard de AI‑gegenereerde definitie (voorkeur de opgeschoonde variant) en biedt preview/diff.
- Stateless services; geen Streamlit in services/orchestrators; geen UI‑sessionstate als bron van waarheid.
- Conceptopslag (draft) in database met versies en audit (triggers); publiceer via review‑workflow.
- Valideer op verzoek met duidelijke feedback (errors/warnings/violations/suggestions) en hanteer kwaliteitspoorten bij publiceren.

Conform richtlijnen in CLAUDE.md/README.md: geen backwards‑compatibility paden toevoegen, services async houden (geen `asyncio.run` in services), en documentlocaties/canonical structuur respecteren.

## Scope
- Tekstbewerking, preview/diff, context/metadata‑aanpassing, voorbeeldenbeheer per type.
- Opslaan als draft (versiebump) en publiceren (naar REVIEW) via workflow‑service.
- Geen WYSIWYG in eerste iteratie; markdown‑preview volstaat. Geen collaborative editing.

## Richtlijnen (samenvatting)
- Geen ‘domein’ veld; gebruik organisatorische/juridische context (EPIC‑010).
- Geen Streamlit‑imports in services; type hints verplicht; geen bare except.
- Performantie: throttle auto‑save; `st.cache_resource` alleen in UI‑laag; regels laden met `st.cache_data` waar relevant.
- Caching: cache ServiceContainer met `@st.cache_resource`; cache data‑loads als pure functies met een expliciete cache‑buster (bijv. `last_updated.isoformat()`), niet als instance‑methods.

## UI‑ontwerp (MVP)
- Component: `src/ui/components/definition_edit_interface.py`
  - Editorpaneel: tekstveld, markdown‑preview en diff tegen oorspronkelijke AI‑tekst.
  - Context/metadata: bewerk organisatorisch/juridisch + kernmetadata.
  - Voorbeelden: per type CRUD.
  - Validatiepaneel: resultaten van `ValidationOrchestratorV2.validate_text()`.
  - Acties: “Opslaan als concept”, “Publiceer (review)”, “Herstel naar AI‑versie”, “Verwerp concept”.
- Navigatie: “Bewerk” knoppen openen editor met `?draft_id=` (of verborgen formwaarde).

Navigatie fallback: indien `st.query_params` niet beschikbaar is, gebruik `st.experimental_get/set_query_params()` (Streamlit versie‑fallback).

Voorvulstrategie editor: voorkeur volgorde = (1) opgeschoonde AI‑definitie (indien beschikbaar), (2) ruwe AI‑tekst, (3) `DefinitieRecord.definitie`. Diff vergelijkt editorinhoud met de gekozen AI‑bron; “Herstel” zet terug naar die bron.

## Backend‑ontwerp
### Orchestrator V2 – aanvullingen
- `update_definition(definition_id: int, updates: dict[str, Any]) -> DefinitionResponseV2`
  - laad → apply updates (tekst/context/metadata) → cleaning → validate → persist → log → return status/ID/validatie.
- `validate_and_save(definition: Definition) -> DefinitionResponseV2`
  - combineert validatie (+ optionele cleaning) en opslag.

Opmerkingen t.o.v. codebase:
- De methoden bestaan in `DefinitionOrchestratorV2` maar zijn placeholders. Implementeren met huidig `DefinitionResponseV2` contract; extra velden gaan in `metadata` (bijv. `updated_fields`, `duration`, `orchestrator_version`, optioneel `error_code`).
- UI verkrijgt validatie via een aparte V2‑validator of orchestrator: exposeer een `validation_orchestrator()` in de container óf documenteer een UI‑helper die `run_async` gebruikt om `ValidationOrchestratorV2.validate_text(...)` aan te roepen.

### Repository – aanvullingen
- Versies/drafts (rekening houdend met UNIQUE constraint op (begrip, organisatorische_context, juridische_context, categorie, status)):
  - `get_or_create_draft(definition_id) -> int` (zorgt dat er maximaal één DRAFT per combinatie is; hergebruikt bestaande draft indien aanwezig).
  - `create_draft_from(definition_id, updates) -> int` (nieuw record; `previous_version_id` zetten, `version_number` +1, status=draft) — alleen als er nog geen draft is.
  - `get_history(definition_id) -> list[...]` (lees `definitie_geschiedenis`).
  - `rollback_to(version_id) -> int` (genereer nieuw draft op basis van oude versie).
- Whitelist fix in `update_definitie` — definitieve set (kolommen uit schema):
  - Toestaan: `definitie`, `organisatorische_context`, `juridische_context`, `categorie`, `status`, `validation_score`, `validation_date`, `validation_issues`, `approved_by`, `approved_at`, `approval_notes`, `last_exported_at`, `export_destinations`, `updated_by`, `version_number`, `previous_version_id`.
  - Verwijderen: niet‑bestaande velden (zoals ‘metadata’, ‘validated’, ‘reviewed_by’, ‘review_date’).
- Voorbeelden‑beheer:
  - `update_voorbeelden_delta(definitie_id, nieuwe: dict[str, list[str]])` — vergelijk met bestaande records en voer alleen benodigde inserts/updates/deactivaties uit (voorkomt thrash bij autosave).
- Optimistic locking: voer `UPDATE ... WHERE id=? AND updated_at=?` uit en verifieer `rowcount==1`. Bij conflict retourneer serverversie (voor merge‑UI) met suggesties: “Herlaad”, “Overschrijf” (indien toegestaan), “Nieuwe draft maken”.

Transactiepatroon `get_or_create_draft`:
- Doe een INSERT met `status='draft'`; op UNIQUE‑violation SELECT bestaande draft. Normaliseer `juridische_context` naar lege string voor consistente matching (zoals in `find_definitie`).

Versiebeheer:
- Bump `version_number` alleen bij het creëren van een nieuwe draft of bij publiceren van een nieuwe versie, niet bij elke draft‑save.

### Workflow‑service
- `DefinitionWorkflowService` laten leunen op de services‑repository API; pas de services‑repository aan met een dunne `update_status(...)` die intern `database.definitie_repository.change_status(...)` aanroept, of wijzig de workflowservice om direct `change_status(...)` te gebruiken.
- Gestandaardiseerde `WorkflowResult` met foutcodes (bijv. `INVALID_TRANSITION`, `CONFLICT`, `NOT_FOUND`).

## Validatie tijdens het bewerken
- Knop‑gestuurd: `ValidationOrchestratorV2.validate_text(begrip, text, ontologische_categorie, context)`; throttle in UI.
- Resultaat tonen met severities en suggesties; hergebruik bestaand schema.
 - Kwaliteitspoorten (uit US‑061) voor publiceren:
   - Overall: `overall_score ≥ 0.80`.
   - Categorisch: gebruik `detailed_scores` en kies concrete sleutels (bijv. `juridisch` en `structuur` ≥ 0.75); leg selectie vast in config.
   - Violations: blokkeer bij `severity in {'error'}`; als ‘critical’ niet uniform voorkomt, map ‘error’ op blokkade en ‘warning’ op waarschuwing.
   - UX: toon gate‑reden en CTA “Los issues op”.

Rate limiting / cooldown:
- Gebruik UI‑cooldown (≥2s) én volg `definition_validation` timeout uit `src/config/rate_limit_config.py`.

## Data & AI‑voorvertoning
- Editor voorvult de opgeschoonde AI‑definitie (indien beschikbaar), anders ruwe AI‑tekst of `DefinitieRecord.definitie`.
- Diff toont verschillen tussen oorspronkelijke AI‑tekst en huidige editorinhoud.
- “Herstel naar AI‑versie” zet editorinhoud terug.

Voorbeelden‑types mapping (DB): gebruik uitsluitend `('sentence','practical','counter','synonyms','antonyms','explanation')`. Definieer UI‑labels ↔ DB‑waarden mapping en houd `UNIQUE(definitie_id, voorbeeld_type, voorbeeld_volgorde)` in acht.

## Acceptatiecriteria (uittreksel)
- AI‑definitie standaard zichtbaar met preview/diff.
- Context/metadata en voorbeelden bewerkbaar en persistent.
- Draft + auditlog bij opslaan; publiceren via workflow zet status naar REVIEW, mits kwaliteitspoorten gehaald zijn.
- Geen custom UI‑sessionstate als bron van waarheid (DB‑draft is leidend).

## Subtaken
1. UI: editor/preview/diff + robuuste navigatie (query params met fallback) en cleaning‑preview toggle; caching van resources met `@st.cache_resource` (geen services in cache‑data).
2. UI: voorbeelden‑CRUD met delta‑updates, type‑mapping en expliciete “Opslaan voorbeelden”.
3. UI: validatiepaneel en triggers met cooldown/indicator; gating‑feedback bij publiceren; gebruik `run_async` bridge naar V2‑validator.
4. Services: Orchestrator `update_definition` + `validate_and_save` (async, stateless) met uitgebreid response‑contract via `DefinitionResponseV2.metadata` (updated_fields, duration, orchestrator_version, optioneel error_code).
5. Repository: `get_or_create_draft` (INSERT→SELECT fallback), `create_draft_from`, `get_history`, `rollback_to`, whitelist fix, `update_with_lock_check` met `rowcount` verificatie, `update_voorbeelden_delta` transactie.
6. Workflow: pas services‑repository aan met `update_status(...)` (adapter op `change_status(...)`) of wijzig workflowservice om direct `change_status(...)` te gebruiken; foutcodes uniformeren in `WorkflowResult`.
7. Integratie: “Bewerk” knoppen verbinden naar editor met draft_id; publiceerflow met gates en conflict‑UX (herlaad/merge/nieuwe draft).
8. Tests: unit (repo: draft‑invariant/locking/voorbeelden‑delta; orchestrator: update/validate_save; workflow: status‑transities), integratie (UI‑flow), regressie (versies/audit/gates/examples‑delta), concurrency‑conflictcases.

## Risico’s & mitigatie
- Concurrency: optimistic locking + duidelijke melding; `rowcount`‑check en merge‑UI.
- Reruns: throttle auto‑save; validatie via knop (geen on_change‑storm); respecteer rate‑limit timeout per endpoint.
- Integratie: los method‑mismatches op vóór UI‑koppeling (services‑repository `update_status` vs DB `change_status`; validatieorchestrator toegang). Test UNIQUE‑paths (één actieve draft per combinatie) en query‑param fallback.

## Mijlpalen
- M1 Backend: repo‑uitbreidingen (get_or_create_draft met INSERT→SELECT, whitelist fix, `update_with_lock_check`, voorbeelden‑delta) + orchestrator‑methoden met `DefinitionResponseV2.metadata` contract.
- M2 UI‑MVP: editor + validatie (V2 via bridge) + draft + cleaning‑preview + robuuste navigatie (fallback inbegrepen).
- M3 Voorbeelden + publiceren met kwaliteitspoorten (detailed_scores‑keys vastgelegd) + workflow‑adapter (`update_status` ↔ `change_status`).
- M4 UX‑polish (shortcuts, highlight, optionele auto‑save) + concurrency‑UX (merge/keuzes).

## Teststrategie
- Unit: repo (get_or_create_draft/rollback/locking/voorbeelden‑delta), orchestrator (update/validate_save, response‑contract), workflow (change_status), validatie‑mapping.
- Integratie: open edit → wijzig → valideer → save draft → publiceer (met gates) → approve.
- Regressie: versiebump/audit via triggers; unique‑constraint (één draft); concurrency‑conflicts; navigatie fallback.

## Verbeteringen t.o.v. basisplan (Ultrathink)
- Draft‑beheer afgestemd op DB‑UNIQUE: `get_or_create_draft` voorkomt dubbele drafts en violation‑errors.
- Whitelist definitief vastgesteld en opgeschoond; geen fictieve kolommen meer in updates.
- Workflow‑service sluit aan op services‑repository (`change_status`) en brengt uniforme foutcodes.
- Kwaliteitspoorten (0.80/0.75/geen critical) afdwingbaar met duidelijke UX‑meldingen.
- Voorbeelden worden delta‑bewust geüpdatet om autosave‑thrash te vermijden.
- Cleaning‑preview maakt effect van cleaning transparant vóór validatie/opslag.
- Robuuste navigatie zonder afhankelijkheid van session state; query‑params met fallback.
- Concurrency‑UX (optimistic locking + keuzes) voorkomt stille overschrijvingen.
- Response‑contract uitgebreid voor betere telemetrie en foutafhandeling.
