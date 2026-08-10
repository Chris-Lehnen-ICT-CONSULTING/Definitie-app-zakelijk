# BATCH-027 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Primaire reviewer: `codex-kierkegaard`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 20/20 blobs, 1.789/1.789 fysieke regels en 60/60 Python-symbolen

Alle regels en symbolen zijn rechtstreeks uit de immutable Git-objecten gelezen;
applicatiebestanden zijn niet gewijzigd.

## Verificatie

- 62 primaire en 35 onafhankelijke gerichte tests slaagden.
- Ruff en Black waren schoon.
- De actieve service-uitkomsten zijn lokaal en zonder externe diensten gereproduceerd.

## Bevindingen

### B027-001 — P1 — INT-07 markeert gewone lowercase woorden als afkorting

`INT-07.json:7-20` bevat hoofdletterpatronen zoals `\b[A-Z]{2,6}\b`, maar de
actieve generieke evaluator compileert alles met `IGNORECASE` en behandelt iedere
hit als verboden. Gewone woorden en zelfs het goede voorbeeld `Dienst
Justitiële Inrichtingen (DJI)` falen hierdoor. Aanbevolen: een hoofdlettergevoelige,
rule-specifieke afkortingsevaluator die gekoppelde expansie of link accepteert.

### B027-002 — P2 — SAM-04 werkt alleen bij een dubbelepuntrepresentatie

De regelspecificatie verwacht vergelijking van een los meegegeven samengesteld
begrip met het genus van de definitie. De actieve special-case bepaalt het eerste
token alleen als de tekst `:` bevat. Het foute voorbeeld zonder prefix staat dus
in `passed_rules`. Aanbevolen: altijd het eerste definitietoken analyseren en
alleen optioneel een exact begriplabel voor `:` verwijderen.

### B027-003 — P3 — INT-09 detecteert `o.a.` niet

`INT-09.json:7-17` gebruikt `\bo\.a\.\b`; na de laatste punt bestaat geen
woordgrens. `opsomming met o.a. auto` passeert de echte service. Aanbevolen:
lookarounds of een eind-/spatie-lookahead en tests voor hoofdletters en spaties.

### B027-004 — P3 — vier legacyvalidators implementeren andere regels dan JSON

SAM-02 valideert vage kwantoren, SAM-03 tautologie, SAM-04 verwijzingen en
SAM-05 repositorytermen, terwijl hun JSON-contracten respectievelijk herhaling,
geneste definities, samenstellingsgenus en definitiecycli beschrijven. De
primaire JSON-service gebruikt dit pad niet; de publieke legacyloader kan het wel
laden. Aanbevolen: één uitvoerbare implementatie per regel-ID en een semantische
JSON↔Python-contracttest.

## Niet getest

- Geen browser/UI of externe diensten; deze batch bevat validatiebackend.
- Actieve productie-impact van het legacy Pythonpad is niet aangetoond.
