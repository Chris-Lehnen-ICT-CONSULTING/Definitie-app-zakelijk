# Changelog

Alle noemenswaardige wijzigingen aan DefinitieAgent worden in dit bestand vastgelegd.

Het formaat is gebaseerd op [Keep a Changelog](https://keepachangelog.com/nl/1.1.0/)
en dit project volgt (informeel) [Semantic Versioning](https://semver.org/lang/nl/).

> Dit bestand is aangemaakt in juli 2026 (DEF-496). Wijzigingen van vóór die datum
> zijn niet uitputtend teruggevuld; raadpleeg de git-history en Linear (project `DEF`)
> voor oudere details.

## [Unreleased]

### Beveiliging
- Gelekte OpenAI-key uit vier git-getrackte docs onder `docs/analyses/` geredigeerd; key gerevoked (DEF-491). Git-history-scrub resteert.
- PII-redactiefilter op de log-handlers i.p.v. de root-logger, zodat child-loggers gedekt zijn (DEF-486).
- Context-isolatie per Streamlit-sessie; proces-globale context-lek verholpen (DEF-484).

### Toegevoegd
- In-memory memo in `RuleCache` zodat de 53 toetsregels tijdens validatie niet herhaaldelijk van disk worden gedeserialiseerd (DEF-496).
- Atomaire multi-step DB-transacties via `DatabaseConnection.transaction()` (`BEGIN IMMEDIATE` + nesting-guard) (DEF-391).
- Hashed, gelockte requirements: `requirements.in`/`requirements-dev.in` → `make lock` (DEF-426).

### Gewijzigd
- `make dev` verwijst nu naar het bestaande `scripts/deployment/run_app.sh` (DEF-489).
- README-claims gecorrigeerd naar de werkelijkheid: LLM-model (GPT-5-familie/Claude via `ModelRouter`), 53 toetsregels, Python 3.13, `.env` wordt geladen, coverage-ratchet 45% (DEF-489).
- `forbidden-patterns`-hook blokkeert nu (fail-closed) i.p.v. gemaskeerd door `|| true` (DEF-465).
- Diagnostische scratch-scripts verplaatst van `tests/unit/` naar `tests/manual/scratch/` (niet verzameld); false-green tests verwijderd (DEF-493).

### Verwijderd
- Dode legacy-shim `src/orchestration/definitie_agent.py` (geen importeurs) (DEF-494).

## [2.3.0] - 2025-09-19

Baseline vóór dit changelog-bestand. Kernpunten (zie README/git-history):

- V1→V2-migratie afgerond; clean V2-architectuur (`ValidationOrchestratorV2`, `UnifiedDefinitionGenerator`, `ModularValidationService`).
- Definition Edit Interface met version history en auto-save.
- Web Lookup (Epic 3) en document-upload voor contextverrijking.

[Unreleased]: https://github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk/compare/main...HEAD
