# BATCH-113 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 1/1 bereiken, 6000/6000 fysieke regels en 0/0 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit immutable Git-objecten gelezen. Callers, foutpaden en relevante tests zijn gevolgd; applicatie- en testbestanden zijn niet gewijzigd.

## Verificatie

- JSON- en referentie-integriteit waren schoon; de afzonderlijke semantische modelscan reproduceerde de geregistreerde incomplete en dubbele modelrelaties.
- Object-ID's, ranges, line owners en symbol-memberships matchten het batchmanifest exact.

## Bevindingen

### B113-001 — P3 — Two orphan relations duplicate the same creation edge

**Bewijs:** Relations PZ5t... at 19757 and jccai... at 20357 exactly duplicate HCAD... at 17857: null name, creation stereotype, ordered endpoints RjaU... -> INw0..., cardinality 1/1. Only HCAD has a RelationView; the two B113 duplicates have zero diagram references. Semantic signature count is three instead of one.

**Reproductie:** Parse all Relation definitions, group by (name, stereotype, ordered propertyType IDs), and list groups with count >1; inspect diagram references for the three IDs.

**Aanbevolen oplossing:** Keep one canonical creation relation, remove the two unreferenced duplicates, and validate uniqueness of semantic relation signatures while allowing one model relation to be reused by multiple views.

### B113-002 — P3 — Three generalization edges are defined twice

**Bewijs:** The specific/general pairs Tce8...->iYjV..., KpRJ...->iYjV..., and _fiC...->iYjV... each have two different Generalization IDs. The model has 227 definitions but only 224 unique directed edges. A single generalization (_iy...) is already reused in two diagrams, proving duplicate model definitions are not needed for multiple views.

**Reproductie:** Parse Generalization objects and group IDs by (specific.id, general.id); three groups each contain two IDs at lines 23145/23250, 23160/23205 and 23175/23220.

**Aanbevolen oplossing:** Retain one generalization ID per directed class pair, repoint every GeneralizationView to it, and add a uniqueness assertion for specific/general pairs.

## Niet getest

- Geen externe OntoUML-importer of visuele modelrenderer; appflows, browser, toegankelijkheid en responsive gedrag zijn niet van toepassing op deze JSON-only scope.
