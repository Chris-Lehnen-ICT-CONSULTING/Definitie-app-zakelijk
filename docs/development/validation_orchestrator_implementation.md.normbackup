# Validation Orchestrator V2 — Implementation Guide

---
document: Validation Orchestrator Implementation Guide
version: 0.1
status: DRAFT
type: Developer Guide
parent: # ../architecture/validation_orchestrator_v2.md (gearchiveerd)
related:
  - ../architecture/contracts/validation_result_contract.md
  - ../architecture/contracts/schemas/validation_result.schema.json
  - ../workflows/validation_orchestrator_rollout.md
owner: Dev Lead
created: 2025-08-29
updated: 2025-08-29
tags: [validation, orchestrator, implementation, async, schema]
---

## Doel
Praktische leidraad voor het implementeren van `ValidationOrchestratorV2` conform de architectuur en het `ValidationResult` contract. Richt zich op interfacehandtekeningen, foutbeleid, schema‑binding en batch‑semantiek.

## Interfaces

```
from typing import Iterable, Mapping, TypedDict
from dataclasses import dataclass, field
from uuid import UUID, uuid4

class ValidationResult(TypedDict):
    version: str
    overall_score: float
    is_acceptable: bool
    violations: list[dict]
    passed_rules: list[str]
    detailed_scores: dict[str, float]
    improvement_suggestions: list[dict] | None
    system: dict | None

@dataclass(frozen=True)
class ValidationContext:
    correlation_id: UUID | None = None
    profile: str | None = None
    locale: str | None = None
    trace_parent: str | None = None
    feature_flags: Mapping[str, bool] = field(default_factory=dict)

@dataclass(frozen=True)
class ValidationRequest:
    begrip: str
    text: str
    ontologische_categorie: str | None = None
    context: ValidationContext | None = None
```

## Handtekeningen

```
class ValidationOrchestratorInterface(Protocol):
    async def validate_text(
        self,
        begrip: str,
        text: str,
        ontologische_categorie: str | None = None,
        context: ValidationContext | None = None,
    ) -> ValidationResult: ...

    async def validate_definition(
        self,
        definition: Definition,
        context: ValidationContext | None = None,
    ) -> ValidationResult: ...

    async def batch_validate(
        self,
        items: Iterable[ValidationRequest],
        max_concurrency: int = 1,
    ) -> list[ValidationResult]: ...
```

## Foutbeleid
- Operationele fouten (timeouts/upstream) → degraded `ValidationResult` met cataloguscode (`TMO-*`, `UPS-*`, `INT-*`) en `system.error` gevuld; `category` = `system` in `violations[*]`.
- Programmeer/contractschendingen → raise (early fail), niet mappen.
- Cancellation: laat `asyncio.CancelledError` bubbelen.

## Correlation ID
- Indien `context.correlation_id is None`, genereer `uuid4()` en zet in `system.correlation_id` van de output.
- Propageren naar onderliggende services (logging/telemetry).

## Batch‑semantiek
- Outputvolgorde == inputvolgorde, ook bij `max_concurrency > 1` (gebruik index‑zipper of gather‑ordering).
- Start met sequentieel (`max_concurrency=1`); verhoog pas na reentrancy‑check.

## Schema‑binding
- `ValidationResult` volgen volgens `validation_result.schema.json`.
- Test: valideer responses in contracttests; geen runtime‑validatie in hot path tenzij via feature flag/sampling.

## Voorbeeld Implementatie (Skeleton)

```
class ValidationOrchestratorV2:
    def __init__(self, validation_service, cleaning_service=None):
        self.validation_service = validation_service
        self.cleaning_service = cleaning_service

    async def validate_text(self, begrip, text, ontologische_categorie=None, context=None):
        cid = (context.correlation_id if context and context.correlation_id else uuid4())
        cleaned = text
        if self.cleaning_service is not None:
            res = await self.cleaning_service.clean_text(text, begrip)
            cleaned = res.cleaned_text
        result = await self.validation_service.validate_definition(
            begrip, cleaned, ontologische_categorie, {"correlation_id": str(cid)}
        )
        # Ensure contract fields
        result.setdefault("version", "1.0.0")
        sys = result.get("system") or {}
        sys.setdefault("correlation_id", str(cid))
        result["system"] = sys
        return result

    async def validate_definition(self, definition, context=None):
        return await self.validate_text(
            definition.begrip,
            definition.definitie,
            getattr(definition, "ontologische_categorie", None),
            context,
        )

    async def batch_validate(self, items, max_concurrency=1):
        # Start sequentieel; parallelisatie volgt na reentrancy‑bevestiging
        results = []
        for req in items:
            results.append(
                await self.validate_text(
                    req.begrip, req.text, req.ontologische_categorie, req.context
                )
            )
        return results
```

## Backward Compatibility
- Oud gepind schema (`validation_result_v1.0.0.schema.json`) gebruikt `metadata` i.p.v. `system` en andere veldnamen.
- Producer‑richtlijn: produceer ALTIJD “latest” (met `system`).
- Consumer‑adapter (indien nodig): map `metadata.*` → `system.*` (o.a. `metadata.correlation_id` → `system.correlation_id`).

## Tests (uittreksel)
- JSON Schema validatie voor responses (happy/edge/degraded).
- UUID‑validatie voor `system.correlation_id` (policy‑test).
- Batch ordering en cancellation gedrag.

---
*Deze guide evolveert mee met implementatiefeedback en lessons learned uit rollout.*
