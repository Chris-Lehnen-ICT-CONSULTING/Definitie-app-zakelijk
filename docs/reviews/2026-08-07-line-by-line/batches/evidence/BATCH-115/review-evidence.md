# BATCH-115 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 1/1 bereiken, 6000/6000 fysieke regels en 0/0 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- JSON- en referentie-integriteit waren schoon; de onafhankelijke endpointscan vond vier van 45 RelationViews met een afwijkende modelendpointmultiset.
- Object-ID's, ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B115-001 — P3 — Four RelationViews connect classes that do not match their model relations

**Bewijs:** Of 45 RelationViews whose definitions start in B115, four have source/target ClassView modelElement IDs different from the referenced Relation propertyType IDs: lines 31520, 32738, 35056 and 35970. The first three substitute unrelated classes (not ancestors/descendants); the fourth visualizes SRK-Identiteitsvaststelling where the model relation endpoint is null. All ClassView/Relation references and shapes otherwise resolve, so this is model/diagram semantic drift rather than a dangling-reference false positive.

**Reproductie:** Parse blob af044d..., resolve each scoped RelationView source/target ClassView to its model Class, resolve its modelElement Relation to both propertyType class IDs, and compare the two endpoint multisets; 4 of 45 differ while the same check yields 0 missing view refs and 0 invalid paths.

**Aanbevolen oplossing:** Reconcile each Relation definition with its diagram endpoints (or repoint the incorrect view), restore the null endpoint, and add an export gate asserting that every RelationView endpoint multiset equals the referenced Relation endpoint multiset.

## Niet getest

- Geen externe OntoUML-importer of visuele modelrenderer; appflows, browser, toegankelijkheid en responsive gedrag zijn niet van toepassing op deze JSON-only scope.
