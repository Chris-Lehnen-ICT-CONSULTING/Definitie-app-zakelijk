# BATCH-116 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 1/1 bereiken, 6000/6000 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- De volledige JSON-, ID-, referentie- en view-endpointscan was structureel groen; de semantische scan reproduceerde de geregistreerde afwijkingen.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B116-001 — P3 — Three diagrams bind relations to unrelated endpoint classes

**Bewijs:** Three novel B116 RelationViews disagree with their referenced Relation endpoints: Strafrechttraject line 37674 connects Persoon als verdachte aanmerken to Verdachte although HCAD... models Verdachte/veroordeelde to Verdachte; Overview line 39690 connects Natuurlijk Persoon to Geboorte although ERH... models Natuurlijk Persoon at both ends; Overview line 41148 connects Strafrechtketen identifier to SRK-identiteitsregister although 4sXV... models Register to SRK-identiteitsregister. In each case the substituted classes are neither equal nor ancestors/descendants. Three other B116 mismatches are duplicates of B111/B115 findings.

**Reproductie:** Parse blob af044d..., select RelationViews whose id definitions start at 36001-42000, resolve source/target ClassViews and the referenced Relation.properties propertyType IDs, compare endpoint multisets, then use the Generalization graph to test the unmatched pairs. The three stated novel pairs remain unrelated.

**Aanbevolen oplossing:** Determine the intended relation for each diagram, repoint the view or correct the model endpoints, and add an export validator requiring every RelationView endpoint multiset to equal its referenced Relation endpoint multiset.

## Niet getest

- Geen externe OntoUML-importer of visuele modelrenderer; browser, toegankelijkheid en responsive gedrag zijn niet van toepassing op deze JSON-only scope.
