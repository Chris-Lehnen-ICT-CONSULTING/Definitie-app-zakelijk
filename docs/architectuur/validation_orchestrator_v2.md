# Validation Orchestrator V2 — Architectuur & Migratieplan

**Status: CANONICAL - IMPLEMENTED (Story 2.1 & 2.2)**
**Version: 1.0.0**
**Last Updated: 2025-08-29**
**Previous Version: [Archived Migration Doc](../archief/validation/validation-orchestrator-migration.md)**

## Implementation Status
- ✅ **Story 2.1**: ValidationOrchestratorInterface - COMPLETED
- ✅ **Story 2.2**: Core Implementation - COMPLETED
- ⏳ **Story 2.3**: Container Wiring - PENDING
- ⏳ **Story 2.4**: Integration & Migration - PENDING
- ⏳ **Story 2.5**: Testing & QA - PENDING
- ⏳ **Story 2.6**: Production Rollout - PENDING

## Implementation Details

### Core Files (Story 2.2)
- `src/services/orchestrators/validation_orchestrator_v2.py` - Thin orchestration layer (135 lines)
- `src/services/validation/interfaces.py` - ValidationOrchestratorInterface & TypedDict contracts
- `src/services/validation/mappers.py` - Dataclass → Schema conversion
- `src/services/feature_flags.py` - Shadow mode & canary deployment support

### Error Policy
- **Degraded Mode**: Operationele fouten resulteren in SYS-SVC-001 violations
- **No Exceptions**: Alle paden retourneren ValidationResult
- **Correlation Tracking**: UUID propagatie door hele stack

### Context Propagation
Volledige context wordt doorgegeven:
- `correlation_id` - Voor distributed tracing
- `profile` - Voor validatie profiel selectie
- `locale` - Voor taal-specifieke validatie
- `feature_flags` - Voor runtime configuratie

Dit document beschrijft de rationale, architectuur en migratiestappen om validatie te scheiden in een eigen, moderne V2‑orchestrator, conform de EA/SA‑principes. Het doel is een duidelijke verantwoordelijkheidsscheiding, hergebruikbare validatieflows en beter testbare, async‑vriendelijke modules.

## Samenvatting
- Maak een aparte `ValidationOrchestratorV2` voor validatieflows (single en batch), los van de definitie‑generatie.
- Gebruik de bestaande moderne validator (`src/validation/definitie_validator.py`) als bron van waarheid en map resultaten 1‑op‑1 naar `services.interfaces.ValidationResult`.
- Laat `DefinitionOrchestratorV2` de validation orchestrator aanroepen, niet direct de validator.
- Migreer incrementeel, met CI‑guardrails tegen V1/legacy patroongebruik.

## Doelen
- Single responsibility: validatie loskoppelen van generatie.
- Hergebruik: dezelfde validatieroute voor import, bulk, UI‑checks en API.
- Async & schaalbaarheid: eigen timeout/retry/policy, batch en parallelisme waar verantwoord.
- Testbaarheid: smallere surface‑area, heldere interfaces, unit/integration tests.

## Scope
- Toevoegen van `ValidationOrchestratorV2` (async), interface + minimale implementatie.
- Aanpassen van callsites om V2‑contracten te gebruiken (geen `response.message`/`response.validation`).
- Mapping modern validator → `services.interfaces.ValidationResult`.

Niet in scope (nu):
- Herziening van UI state‑management (SessionState) – volgt separaat.
- Opschonen/async maken van `CleaningService` – eigen migratiespoor.

## Huidige situatie (relevant)
- `DefinitionOrchestratorV2` valideert direct via een serviceadapter; validatielogica en mapping zitten in `src/services/definition_validator.py`.
- Moderne validator in `src/validation/definitie_validator.py` heeft een `validate(...)` methode (en `validate_definitie(...)` helper) die een rijk `ValidationResult` teruggeeft (rule‑violations, scores, etc.).
- Er was een bug door een niet‑bestaande call (`valideer_definitie`); daarnaast bestond een contract‑mismatch in outputvelden (V1 `message` vs V2 `error`, V1 `validation` vs V2 `validation_result`).

## Gewenste situatie
- `ValidationOrchestratorV2` orkestreert validatie (single/batch), optioneel met pre‑cleaning en resultaatverrijking/logging.
- `DefinitionOrchestratorV2` roept deze orchestrator aan via een duidelijk async‑contract, en verwerkt enkel de uitkomst.
- Mapping van de moderne validator naar `services.interfaces.ValidationResult` is centraal en consistent.

## Architectuur
### Componenten
- `ValidationOrchestratorV2` (nieuw): orchestrator voor validatie.
- `ValidationServiceInterface` (bestaand): async servicecontract dat de orchestrator gebruikt (adapters toegestaan in transitie).
- Moderne validator (bestaand): `src/validation/definitie_validator.py` — domeinlogica voor evaluatie en scoring.
- Optioneel: `CleaningServiceInterface` voor pre‑cleaning van tekst voordat regels worden toegepast.

### Interfaces (voorstel)
```
class ValidationOrchestratorInterface(ABC):
    @abstractmethod
    async def validate_text(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: ValidationContext | None = None,
    ) -> ValidationResult: ...

    @abstractmethod
    async def validate_definition(
        self,
        definition: Definition,
        context: ValidationContext | None = None,
    ) -> ValidationResult: ...

    @abstractmethod
    async def batch_validate(
        self,
        items: Iterable[ValidationRequest],
        max_concurrency: int = 1,
    ) -> list[ValidationResult]: ...
```

### Sequencing (single validate)
1) (Optioneel) Pre‑cleaning via `CleaningServiceInterface.clean_text(...)`.
2) Validatie via `ValidationServiceInterface` of directe moderne validator.
3) Mapping naar `services.interfaces.ValidationResult`.
4) (Optioneel) Persist/logging/metrics (time, rule coverage, etc.).

## Configuratie
- Thresholds en regelcategorieën in een `ValidationConfig` (min_score, enabled_categories).
- (Optioneel) Toggle pre‑cleaning, performance parameters (batch size, max_concurrency).

## Migratieplan
Fase 1 — Bugfix & contractzuivering (korte termijn)
- In `src/services/definition_validator.py`: roep de moderne validator aan met `validate(...)` (of `validate_definitie(...)`) in plaats van de niet‑bestaande `valideer_definitie(...)`.
- Map het moderne resultaat direct naar `services.interfaces.ValidationResult` (gebruik `overall_score`, `is_acceptable`, `violations`, `passed_rules`, `detailed_scores`, `improvement_suggestions`).
- Verwijder legacy loops die “toets_resultaten” strings opbouwen — moderne data is leidend.
- Werk callsites bij naar V2‑namen (geen `response.message`/`response.validation`).

Fase 2 — Nieuwe orchestrator introduceren
- Voeg `src/services/orchestrators/validation_orchestrator_v2.py` toe met minimale implementatie:
  - `validate_text`, `validate_definition`, `batch_validate` (sequentieel afhandelen; parallelisme later, na thread‑safety check).
  - Injecteer `ValidationServiceInterface` en (optioneel) `CleaningServiceInterface` via container.

Fase 3 — Integratie in generator‑flow
- Laat `DefinitionOrchestratorV2` de validation orchestrator aanroepen i.p.v. direct de validator/service.
- Houd enhancement/re‑validatie via dezelfde orchestrator.

Fase 4 — Breder gebruik
- UI/integratie (duplicate check, import) direct laten valideren via de validation orchestrator waar passend.
- Documenteer een lichte sync‑adapter indien nodig voor legacy UI paden.

Fase 5 — Opschonen
- Verwijder overbodige validatiepaden, oude helpers en redundante mappingcode.
- Houd CI‑guardrails actief tegen V1‑patronen én tegen `response.message`/`response.validation` in core.

## Impact op code
Toe te voegen
- `src/services/orchestrators/validation_orchestrator_v2.py`
- (optioneel) `src/services/validation/{service.py, mappers.py, config.py}` voor nette scheiding.

Aan te passen (gefaseerd)
- `src/services/definition_validator.py` — directe mapping op moderne validator.
- `src/services/container.py` — instantiatie/injectie van `ValidationOrchestratorV2` naast de V2 generator‑orchestrator.
- `src/services/orchestrators/definition_orchestrator_v2.py` — call naar validation orchestrator.

Guardrails (CI/tests)
- `tests/ci/test_forbidden_symbols.py`: uitbreiden met check op `response.message` en `response.validation` in `src/services` en `src/orchestration`.
- (Optioneel) CI grep‑stap die dezelfde patronen afvangt vroeg in de pipeline.

## Rollback
- Orchestrator is add‑only; revert is eenvoudig door de container wiring terug te zetten en oude callpaths te gebruiken.

## Open punten / risico’s
- Parallel batch‑validatie vereist bevestiging van thread‑/reentrancy van validator/rule‑managers. Start sequentieel.
- CleaningService is nog sync; adapter blijft nodig tenzij we `CleaningService` async maken (apart spoor).

## Appendix: Voorbeeld skelet ValidationOrchestratorV2
```
from typing import Any, Iterable
from services.interfaces import (
    Definition,
    ValidationResult,
    ValidationServiceInterface,
    CleaningServiceInterface,
)

class ValidationOrchestratorV2:
    def __init__(
        self,
        validation_service: ValidationServiceInterface,
        cleaning_service: CleaningServiceInterface | None = None,
    ) -> None:
        self.validation_service = validation_service
        self.cleaning_service = cleaning_service

    async def validate_text(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        cleaned = text
        if self.cleaning_service is not None:
            res = await self.cleaning_service.clean_text(text, begrip)
            cleaned = res.cleaned_text
        return await self.validation_service.validate_definition(
            begrip, cleaned, ontologische_categorie, context
        )

    async def validate_definition(self, definition: Definition) -> ValidationResult:
        text = definition.definitie
        if self.cleaning_service is not None:
            res = await self.cleaning_service.clean_definition(definition)
            text = res.cleaned_text
        return await self.validation_service.validate_definition(
            definition.begrip, text, definition.ontologische_categorie
        )

    async def batch_validate(
        self,
        items: Iterable[ValidationRequest],
        max_concurrency: int = 1,
    ) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        for req in items:
            results.append(
                await self.validate_text(
                    req.begrip,
                    req.text,
                    ontologische_categorie=req.ontologische_categorie,
                    context=req.context,
                )
            )
        return results
```
---
canonical: false
status: active
owner: validation
last_verified: 2025-09-02
applies_to: definitie-app@v2
---
