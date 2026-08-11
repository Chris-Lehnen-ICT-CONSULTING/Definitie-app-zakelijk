# BATCH-118 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 1/1 bereiken, 6000/6000 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- De volledige JSON-, ID-, referentie- en view-endpointscan was structureel groen; de semantische scan reproduceerde de geregistreerde afwijkingen.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B118-001 — P3 — Conceptual-model view substitutes a different class for a mediation endpoint

**Bewijs:** RelationView xRJp... in Conceptueel Model - uitgebreid connects Feit.Verdachte/veroordeelde to Verdachte/veroordeelde. Its referenced mediation 7QMP... instead connects Feit.Verdachte/veroordeelde to FeitBetrokkenheid. Verdachte/veroordeelde and FeitBetrokkenheid are unrelated in the model's transitive Generalization graph. The other two B118 mismatches are the already recorded B114 null-endpoint relations.

**Reproductie:** Resolve RelationView xRJpgqmGAqACSSyv source and target ClassViews, resolve Relation 7QMPwvGGAqACTgx2 propertyType IDs, and compare the endpoint multisets; the view returns [iXkf...,RjaU...] while the relation returns [iXkf...,ZaHH...].

**Aanbevolen oplossing:** Repoint the view to the intended mediation or correct the relation endpoint after domain review, and enforce view/relation endpoint equality during model export.

## Niet getest

- Geen externe OntoUML-importer of visuele modelrenderer; browser, toegankelijkheid en responsive gedrag zijn niet van toepassing op deze JSON-only scope.
