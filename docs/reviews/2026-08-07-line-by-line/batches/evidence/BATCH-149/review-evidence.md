# BATCH-149 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 9/9 bereiken, 5886/5886 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable analyses zijn gelezen; relevante unit-tests, offline runtime- en parserreproducties, documentclaims en secret-shape-scans zijn gecontroleerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B149-001 — P2 — Complete ontology analysis asserts an end-to-end category path that is not wired

**Bewijs:** The report labels itself a complete very thorough investigation and says category validation is fully implemented and the category flows through the entire generation pipeline. In the same report, lines 179-217 admit that the assignment source and UI integration were not found. At the immutable base, ModularValidationService accepts ontologische_categorie but never puts it in EvaluationContext; ESS-02 reads only metadata marker. This is the already independently proven production defect B026-001, so the new finding is limited to the report's false assurance.

**Reproductie:** Read the report's lines 3-20 and 177-268, then inspect validate_definition at the immutable base: ontologische_categorie occurs in the signature but is not copied into EvaluationContext. The B026 reproduction shows that category proces with empty metadata still fails ESS-02 while metadata marker proces passes.

**Aanbevolen oplossing:** Replace inferred data-flow claims with executable end-to-end contract evidence, link the report to B026-001, mark the analysis superseded until the production defect is fixed, and distinguish discovered code paths from behavior actually exercised.

## Deduplicaties en afwijzingen

- Het productiecontractdefect dedupliceert naar B026-001; B149-001 betreft de afzonderlijke false-assurance in het rapport.

## Niet getest

- Geen externe provider/API/netwerk, echte sleutelwaarden, remote Git-historie, dependency-installatie, destructive rollback of browser/UI-runtime.
