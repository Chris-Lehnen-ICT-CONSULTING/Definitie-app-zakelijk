# DEF-622 — versiebindingsproblemen gesloten na expliciete hervatting

Chris heeft expliciet opdracht gegeven beide open versiebindingsproblemen te herstellen. Daarmee is het eerder gestopte V2b-herstelpad hervat. Deze notitie vervangt de open dispositie van V2b in `DEF-622-vaststel-review-v4.md`; het historische bewijs blijft behouden.

**Fix:** `be9ddfb75a38ad157727e1c274a070f456191c3b`, vanaf `9ba0a5b4b0365815fb4b1383fda63534053c134f`. Claude CLI is de implementer. Eén strikte integerconventie geldt voor reviewpayload, gate en behoud bij vaststelling. De expert-UI geeft de daadwerkelijk beoordeelde versie expliciet mee; `expected_version` blijft een afzonderlijke concurrencycontrole.

## Uitgevoerd bewijs

- RED op vaste oude productiebron met de nieuwe tests: 79 tests, 14 failures, 0 errors/skips, exit1. Beide oorspronkelijke bugs en de ontbrekende UI-payloadversie reproduceren. Een deel van de aanvullende contractfailures betreft strengere redenasserties; deze zijn geen afzonderlijke nieuwe bugclaims.
- GREEN: 120 tests, 0 failures/errors/skips, exit0. Inclusief echte Streamlit expertactie, save/readback/approve/readback, losse reviewer/vaststeller, stale/ABA, auditrollback en bestaande readback/export- en atomiciteitsproeven.
- Gepinde Ruff/Black controleren de drie gewijzigde productiebestanden, beide exit0.
- Alle productiehashes van de GREEN-run matchen de commit. Eén testbestand is door normale commithooks uitsluitend anders afgebroken; de AST is identiek.

Bewijs: `reports/def622/vervolg/coordinator-versie-baseline-red.xml/.log`, `coordinator-versie-red-bron.json`, `coordinator-versie-green.xml/.log`, `coordinator-versie-green-bron.json`, `coordinator-versie-commit-binding.json`.

## Onafhankelijke review

Dezelfde Codex CLI-reviewer (`01a0a033-e7d6-73b1-ac75-cde7c46c09e3`) beoordeelde de exacte delta read-only, zonder delegatie. Eigen proeven op git-bron en synthetische SQLite in geheugen bevestigen:

- ontbrekend/null en verkeerd getypeerde payloadversies worden vóór database-/auditmutatie geweigerd;
- opgeslagen tekstversies en andere fouttypen blokkeren de gate en worden niet geldig herstempeld;
- het geldige integerpad blijft na vaststelling/readback gebonden;
- stale/ABA, generieke wijzigingen en auditfouten respecteren actualiteit en atomiciteit;
- onopgeslagen fragmentsemantiek blijft werken; misvormde recordversies geven geen vrijstelling;
- de echte expert-UI levert de beoordeelde payloadversie.

Oordeel: **V2b gesloten, geen concrete fixregressies in deze delta.** Resultaat: `/private/tmp/DEF-622-versie-hervat-review-v1-result.md`.

Dit sluit uitsluitend de twee versiebindingsproblemen. De nieuwe generatie-, nabewerkings- en tekstvergelijkingscriteria worden afzonderlijk geïmplementeerd en geverifieerd; dit document claimt geen volledige DEF-622-oplevering of algemene DEF-630-gate.
