# BATCH-026 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 20/20 blobs, 1.820/1.820 fysieke regels en 58/58 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit de immutable Git-objecten gelezen.
Callers, regelmetadata en actieve validatiepaden zijn gevolgd; applicatiebestanden
zijn niet gewijzigd.

## Verificatie

- 62 gerichte tests in de primaire review en 35 tests in de kruisverificatie slaagden.
- Ruff en Black waren schoon voor de Pythonbestanden in scope.
- Reproducties gebruikten de echte lokale `ToetsregelManager` en validatieservice,
  zonder netwerk of credentials.

## Bevindingen

### B026-001 — P1 — geselecteerde ontologische categorie wordt genegeerd

`ESS-02.json:3-23` verlangt categorieclassificatie. De actieve service accepteert
`ontologische_categorie`, maar neemt die niet op in `EvaluationContext`; ESS-02
leest alleen `metadata["marker"]`. Met categorie `proces` en lege metadata gaf de
echte service een ESS-02-error; met dezelfde input plus marker `proces` passeerde
de regel. Aanbevolen: één canoniek categorieveld in de evaluatiecontext, met een
end-to-end orchestratorcontracttest.

### B026-002 — P1 — toepassingsvoorwaarden van regels worden niet toegepast

`ESS-03.json:17-20` beperkt de regel tot telbare zelfstandige naamwoorden, maar
de service evalueert alle geladen regels en leest `geldigheid` nergens. Een
expliciete procesinput kreeg daardoor de kritieke fout “Ontbreekt uniek
identificatiecriterium”. Aanbevolen: een applicability-gate vóór scoring en een
expliciete `not_applicable`-uitkomst buiten de score-noemer.

### B026-003 — P2 — data-afhankelijke regels slagen zonder bewijsdata

`DUP_01.json:2-21` vereist databasebewijs. Samen met SAM-05, SAM-06 en SAM-08
wordt deze regel zonder repository-, graaf-, voorkeursterm- of synoniemdata toch
in `passed_rules` gezet. Aanbevolen: rule-specifieke evaluators; ontbrekende
dependencies leveren `not_evaluated/degraded`, nooit pass.

### B026-004 — P2 — goede voorbeelden worden als verboden patroon behandeld

De generieke evaluator behandelt ieder `herkenbaar_patronen`-item als verboden
en gebruikt goede voorbeelden of uitzonderingssemantiek niet. De expliciet goede
INT-01- en INT-03-voorbeelden krijgen daardoor violations. Hetzelfde mechanisme
raakt toegestane INT-08-negatie en specifieke INT-10-bronverwijzingen.
Aanbevolen: patroonpolariteit en uitzonderingen modelleren en alle geconfigureerde
voorbeelden als parametrische contracttests uitvoeren.

## Niet getest

- Geen browser-, externe provider-, netwerk- of credentialflow.
- Geen productiegegevens; alleen lokale regelconfiguratie en validatiecalls.
