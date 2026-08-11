# BATCH-120 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 1/1 bereiken, 2543/2543 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- De volledige JSON-, ID-, referentie- en view-endpointscan was structureel groen; de semantische scan reproduceerde de geregistreerde afwijkingen.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B120-001 — P3 — Two register diagrams reuse a relation with a different target class

**Bewijs:** RelationViews DVhk... and YbDF... in Registreren identiteit and Generiek RegisterManagement both connect Record to Register. Referenced material relation hlgB... instead connects Record to Identiteits-record. Register and Identiteits-record are unrelated in the model's Generalization graph, so the repeated rendering does not represent the modeled edge.

**Reproductie:** Resolve the ClassView endpoints for RelationViews DVhkJ1mAUAgAAimV and YbDF.1mAU.DeTztD and compare them with Relation hlgBe1mAU.DeTzJ5 propertyType IDs; both views yield [Record,Register], while the model yields [Record,Identiteits-record].

**Aanbevolen oplossing:** Create or reference the correct Record-to-Register relation, or change both diagrams to Identiteits-record after domain confirmation; validate endpoint equality for every RelationView before export.

## Niet getest

- Geen externe OntoUML-importer of visuele modelrenderer; browser, toegankelijkheid en responsive gedrag zijn niet van toepassing op deze JSON-only scope.
