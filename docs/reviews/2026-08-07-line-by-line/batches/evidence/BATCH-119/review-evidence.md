# BATCH-119 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 1/1 bereiken, 6000/6000 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- De volledige JSON-, ID-, referentie- en view-endpointscan was structureel groen; de semantische scan reproduceerde de geregistreerde afwijkingen.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B119-001 — P3 — Identiteitsmiddel view disagrees with the modeled contained object type

**Bewijs:** RelationView lQHd... connects Drager and Informatieobject, while referenced material relation ehfZ... connects Fysiek object and Drager. Informatieobject and Fysiek object have no ancestor/descendant relation in the Generalization graph. The identical mismatch repeats at B120 line 61105, so it is one root cause rather than two findings.

**Reproductie:** Resolve lQHdQVmAUAgAAiNL in diagram Identiteitsmiddel and compare its ClassView modelElement IDs with Relation ehfZtlmAUAgAAipw propertyType IDs; the multisets are [Drager,Informatieobject] versus [Fysiek object,Drager].

**Aanbevolen oplossing:** Confirm whether the container relation concerns a physical or information object, update the single model relation or both views consistently, and add the endpoint-consistency export gate.

### B119-002 — P3 — Named Samenvoegen Identiteit diagram is completely empty

**Bewijs:** Diagram CZZ8OmmAUAgAAiRm is named Identiteitsbehandeling - Samenvoegen Identiteit, has a valid Package owner, but stores contents as an empty array. It is the only empty named diagram in the reviewed Wave12 ranges and provides no model view to consumers of the fixed example.

**Reproductie:** Parse the Diagram definitions and select those starting at lines 36001-62543 whose contents array has length zero; exactly CZZ8... at line 54824 is returned.

**Aanbevolen oplossing:** Populate the intended merge-identity model view or mark/remove the placeholder from the published example; add a publication check that rejects unexpectedly empty named diagrams.

## Niet getest

- Geen externe OntoUML-importer of visuele modelrenderer; browser, toegankelijkheid en responsive gedrag zijn niet van toepassing op deze JSON-only scope.
