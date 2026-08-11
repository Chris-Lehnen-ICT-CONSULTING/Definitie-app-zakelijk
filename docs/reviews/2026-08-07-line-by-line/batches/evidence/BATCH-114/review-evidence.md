# BATCH-114 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 1/1 bereiken, 6000/6000 fysieke regels en 0/0 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- JSON- en referentie-integriteit waren schoon; de afzonderlijke semantische modelscan reproduceerde de geregistreerde incomplete en dubbele modelrelaties.
- Object-ID's, ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B114-001 — P3 — Two rendered relations have no source endpoint in the model layer

**Bewijs:** Participational relations rqC... and vDb... each contain a first Property with cardinality 1 but propertyType=null; both second ends target J7s3.... Their RelationViews in diagram Bepalen identiteit - events do have different source ClassViews resolving to PLi59... and 5wB..., so diagram and model layers disagree. All raw IDs/references otherwise resolve.

**Reproductie:** Parse Relation.properties and require two non-null propertyType.id values; these two return [None,J7s3...] and a normal endpoint extraction raises on the null propertyType. Compare their RelationView source modelElement IDs.

**Aanbevolen oplossing:** Restore each missing source propertyType from the verified intended class, reconcile model and diagram layers, and gate exports on exactly two resolvable endpoints per binary relation.

## Niet getest

- Geen externe OntoUML-importer of visuele modelrenderer; appflows, browser, toegankelijkheid en responsive gedrag zijn niet van toepassing op deze JSON-only scope.
