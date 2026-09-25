# INT-01 — uitvoering conservatieve beoordeling en nieuwe proeven

24 september 2026. **Correcties uitgevoerd en gepusht; acceptatie- en effectcriteria nog niet gehaald. Beide PR’s blijven concept.** Dit document volgt eindstatus-herstel-v1.md op; historische proeven en reviews blijven ongewijzigd.

## Wat is uitgevoerd

Het goedgekeurde besluit is uitgewerkt in [conservatieve-beoordeling-uitwerking-v2.md](conservatieve-beoordeling-uitwerking-v2.md). Mogelijke grenzen na punt plus kleine letter blijven onzeker. Aanwijzingen die geen zekere zinsgrens bewijzen, leveren inhoudelijke beoordeling op. Herstel van citaat-, haakjes- en afkortingsgevallen is doorgevoerd. Compactheid en begrijpelijkheid blijven afzonderlijke open beoordelingen; een zins-pass is geen volledige INT-01-pass. Contract `/4` maakt oudere `/1`, `/2` en `/3`-uitkomsten niet actueel. Skillsreferentie en distributiebundels zijn daarmee gelijkgetrokken; geen liveactivatie onder ALG-391.

- Appbron: `c7f5d7dc921740f85a10d932480da338f9c2c276`, [concept-PR474](https://github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk/pull/474).
- Skillsbron: `ed0fcfdcc169c37058f0436fc92c1e07752366b8`, [concept-PR356](https://github.com/ChrisLehnen/claude-global-setup/pull/356).
- Implementatie: echte Claude Code CLI, sessie `442a98fb-a377-403f-996e-433cf4a664fc`.
- Onafhankelijke diffreview: Codex CLI, `gpt-6-astra`/high, sessie `01a0cfac-ea05-7700-ba73-8b5659751c1c`. Correcties gingen terug naar dezelfde uitvoerder en reviewer. Root schreef geen productcode/tests.
- Einddiff op basis `6c18ce7127f0a785fefdd6bc952175a030be8643`: SHA256 `92f95666d4945d5075f3ec2de2dbdd61cbfcdae824d806d5b6d38f2b92a5f57c`. [Functionele review](astra-eindproef-review-v3.md), [bevestiging na testopmaak](astra-testlint-review-v1.md), [eindmanifest](eindproef-review-manifest-v4.json).

## Technisch bewijs

267 gerichte tests geslaagd. Brede unitgate: **7.271 geslaagd, 75 overgeslagen, 1 xfail en 21 subtests**, exit 0. De laatste wijziging groepeerde drie teststrings expliciet; volledige Python-AST gelijk, productiecode en skills bytegelijk. Daardoor blijft de brede gate op dezelfde functionaliteit van toepassing. Gepinde Ruff/Black-commithooks en dependency-audit geslaagd. Skills: 94 tests en 2 subtests groen; canonieke en aliasreferenties na commit opnieuw tegen bron en bestaande naamrewrites gecontroleerd. Bron-, bundel- en testbinding: [commit-en-bewijsbinding-v2.json](../effectproeven-herstel-20260924-v1/commit-en-bewijsbinding-v2.json).

Volledige CLI-logs en opdrachten staan lokaal in `logs/def770-herstel/` en `logs/def770-eindproeven/`. De gepubliceerde manifests, beoordelingen en testlogs verwijzen naar deze sessies. Rawbestanden met eerder vastgestelde secretscan-falsepositives en tijdelijke uitgepakte bron-/databasedirectories worden niet meegepubliceerd; geen wijziging aan de scangates.

## Onafhankelijke eindproeven

| Proef | Uitkomst | Betekenis |
|---|---|---|
| Verse T24 op `/4` | **22/24 volledig conform; 23/24 statuslabels** | 2 open acceptatiebevindingen |
| Automatische zekerheid | **18/18 automatische beslissingen normatief ondersteund** | Alleen deze kleine synthetische set; geen algemene betrouwbaarheidsclaim |
| Automatische dekking | 18/23 niet-leeg = **78,26%** | 10 pass, 8 fail, 5 doorverwijzingen; 1 lege tekst |
| Laadpaden/opslag | 24/24 consistent, 0 uitvoeringsfouten | Geen volledige INT-01-pass |
| G24 | **1 verbeterd, 4 verslechterd, 6 gelijk, 1 onbeslist** | Geen effectvrijgave; 4 nieuwe bron-/betekenisfouten |

De [verse T24](../effectproeven-herstel-20260924-v1/t24-herproef-v1/rapport-v1.md) gebruikt nieuwe onafhankelijke maker-, A-, B- en adjudicatorsessies, alle Astra/high zonder tools. Invoer en referenties waren vóór uitvoering verzegeld. Dezelfde Codex CLI-reviewer bevestigde [T20 en T24 als Important-acceptatieafwijkingen](../effectproeven-herstel-20260924-v1/t24-herproef-v1/bevindingstoets-v1.md). T20 verwijst een expliciete titel met aansluitende bijzin onnodig door. T24 verwijst terecht door, maar noemt interne punten van een lokaal verklaarde afkorting als reden; de echte twijfel betreft de aansluiting van de formulering. T18 heeft alleen redundante diagnostiek naast een juiste fail.

De eerdere bekende herstelset is na correcties 24/24 statusconform. Dat is ontwikkelregressie; het vervangt de verse eindproef niet. Oude labels en uitslagen blijven staan.

[G24](../effectproeven-herstel-20260924-v1/g24-rapport-v1.md) toont verlies van een aansluitrelatie, een onterechte verplichte afwijkende invoertijd en verlies van een gezamenlijk bewaarvereiste. De generatieprompts, API-verzoeken en bronontvangstbewijzen van `/3` en `/4` zijn bij alle zes dossiers exact gelijk. G24 is daarom inhoudelijk herbruikbaar. De `/4`-evaluator is afzonderlijk offline gecontroleerd op 48 ruwe/opgeschoonde teksten, 96 serviceobservaties: gelijke laadpaden, opslag consistent, geen fouten. Zinsstructuur-pass detecteert deze betekenisfouten niet. [Herbinding](../effectproeven-herstel-20260924-v1/g24-contract4-binding-v1.json).

Generatiekosten: US$1,775215 voor deze run; cumulatief US$3,71545 binnen het goedgekeurde US$5. Geen betaalde herhaling voor de classifier. Over: US$1,28455. Een volgende betaalde proef vereist vooraf een nieuwe budgetraming; de laatste runraming past niet in dat restant.

## Open werk en oplevergrens

De twee T24-bevindingen en de G24-betekenisfouten blijven open in DEF-770. De criteria zijn niet afgezwakt en reviews zijn niet als effectbewijs gepresenteerd. De bronreview was voor de onderzochte diff akkoord; de latere onafhankelijke proeven geven **geen acceptatievrijgave**.

Een vervolg moet de twee concrete automatische-beoordelingsgevallen oplossen en betekenisbehoud bij generatie aantoonbaar verbeteren. Alleen een uitgebreidere lijst herkenningspatronen toevoegen bewijst geen algemene taalbetrouwbaarheid. De scope en bewijsopzet moeten die twee problemen afzonderlijk behandelen; daarna is opnieuw onafhankelijke acceptatie nodig op een bevroren bron. Geen nieuwe heuristiekronde, betaalde generatieproef, merge of liveactivatie gestart in deze opleverfase.
