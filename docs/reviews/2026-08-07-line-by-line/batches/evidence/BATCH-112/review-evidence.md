# BATCH-112 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 1/1 bereiken, 6000/6000 fysieke regels en 0/0 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- JSON- en referentie-integriteit waren schoon; de afzonderlijke semantische modelscan reproduceerde de geregistreerde incomplete en dubbele modelrelaties.
- Object-ID's, ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B112-001 — P3 — Named OntoUML attributes omit datatype and multiplicity

**Bewijs:** Across the assigned ranges, 22 named Class properties have cardinality=null and 20 of them also have propertyType=null (B112=12, B113=1, B114=9). The first pair datum ingang/datum einde has neither field. JSON/reference integrity passes, so this is semantic incompleteness rather than syntax corruption; no repository caller loads this example.

**Reproductie:** Parse blob af044d..., walk Class.properties whose id line is 12001-30000, and count properties where cardinality or propertyType is null; accessing propertyType.id fails for 20 attributes.

**Aanbevolen oplossing:** Populate datatype references and multiplicities for every named attribute, or encode an explicit supported unknown value; add a model semantic validator that rejects incomplete attributes before publishing a fixed example.

## Niet getest

- Geen externe OntoUML-importer of visuele modelrenderer; appflows, browser, toegankelijkheid en responsive gedrag zijn niet van toepassing op deze JSON-only scope.
