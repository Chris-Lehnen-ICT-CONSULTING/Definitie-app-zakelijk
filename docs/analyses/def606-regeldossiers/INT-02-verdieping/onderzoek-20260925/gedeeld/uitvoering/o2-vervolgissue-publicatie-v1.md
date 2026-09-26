# [STORY] INT-02 — AI-beoordeling (O2) met goldset

Status: aanmaak als vervolgissue expliciet goedgekeurd door Chris op 26 september 2026. Dit registreert vervolgwerk; implementatie, modelaanroepen en productiewissel zijn niet geautoriseerd.

## Doel en besluitbasis

B2 uit besluiten-chris-v1.md: O1 nu uitvoeren, O2 afzonderlijk inplannen. Onderzoek een scoreloze AI-beoordeling van de INT-02-functiegrens op basis van het versiegebonden contract: begripscriterium en deterministische afleiding tegenover actorvoorschrift, procedure en discretionaire beslisregel. Een woord of patroontreffer bewijst geen oordeel. Het model wijzigt de definitie niet.

Leidende inhoud: gezamenlijke-synthese-v5.md §2–4 en §8–10; gezamenlijk-casusregister-v5.md. De 76 ontwerp-ID's zijn ontwikkel- en regressiegevallen, geen onafhankelijke hold-out.

## Scope

1. Stel vóór evaluatie een onafhankelijke goldset vast met expertlabels, bronpassages, bevestigde bedoeling, context, normversie en een afgescheiden hold-out. Leg eigenaar, selectie, twijfelgevallen en beoordelingsprocedure vast. Neem de grenzen C105, C107, C112, C115 en C116 mee; kopiëren van de 76 ontwerpgevallen is onvoldoende onafhankelijk bewijs.
2. Versioneer prompt, regelcontract, routeringsbeleid, gevraagde model-ID en werkelijk gerapporteerde modelversie; registreer onbekende versies expliciet. Sluit aan op DEF-815 en diens prerequisites en kwaliteitscriteria. Geen ongekwalificeerde fallback of stilzwijgende modelwissel.
3. Gebruik uitsluitend aangeleverde kern, betekenis, context en bronpassages. Bewaar exacte beoordeelde tekst en citeer per oordeel de relevante passage met functie en grond. Controleer citaten mechanisch; C117 toetst een niet uit de invoer afkomstig citaat. Een ongeldig citaat levert geen positieve of negatieve inhoudelijke uitspraak op.
4. Leg vooraf kostenbudget, privacy, logging, bewaartermijnen en autorisatie voor echte modelproeven vast. Geen productiedata of betaalde proef onder de huidige DEF-771-uitvoeringsopdracht. Offline tests bewijzen contractgedrag; modelkwaliteit vereist afzonderlijk geautoriseerd evaluatiebewijs.
5. Werk technisch foutbeleid uit volgens ADR-001: onbeschikbaar model, timeout, ongeldige uitvoer, ontbrekend bewijs en budgetoverschrijding mogen geen stille goedkeuring geven. Technische fout en inhoudelijke onzekerheid blijven onderscheiden.
6. Behoud de scoreloze statusmapping uit synthese §4 en de exacte bijbehorende appmeldingen. Bind een oordeel aan tekst-, betekenis-, context-, bron- en normversie. Gewijzigde gronden maken het vorige oordeel historisch.

## Statusmapping en oordeelvoorwaarden

| Uitkomst | Runtime | Vereist bewijs |
|---|---|---|
| Voldoet | `pass` | Alle relevante passages beoordeeld; geen aangetoond INT-02-gebrek of beslissende onzekerheid. |
| Voldoet niet | `fail` | Concrete passage, geldig citaat, functie en grond. Een zelfstandig aangetoond gebrek blijft fail wanneer andere vragen openstaan. |
| Onvoldoende informatie | `review_required` | Ontbrekende of strijdige betekenisgrond met precies één gerichte vraag. |
| Open menselijke beoordeling | `review_required` | Eigen reden en uitvoeringsmetadata: beoordeling nog niet uitgevoerd. |
| Niet uitgevoerd | `not_evaluated` | Kern of vereiste context ontbreekt; geen inhoudelijk oordeel. |
| Technische fout | `error` | Technische oorzaak vastgelegd; geen inhoudelijk oordeel. |
| Niet van toepassing | `not_applicable` | Gemotiveerde reikwijdtegrond buiten het definitietoetsbereik. Een toegestane afleiding is geen NA-geval. |

Geen score of totaalcijfer. Geen INT-02-poort toevoegen; poortbeleid volgt DEF-831, inclusief de daar nog te besluiten CON-01-keuze. Geen herstelroute; DEF-832 blijft leidend.

## Acceptatiecriteria

- [ ] Goldset en hold-out zijn onafhankelijk van de 76 ontwerpgevallen opgesteld, bevroren en door een benoemde eigenaar geaccepteerd.
- [ ] Prompt-, model-, norm-, input- en contextversies zijn herleidbaar; historische uitkomsten worden niet overschreven.
- [ ] Offline tests bewijzen alle statuspaden, citaatcontrole (C117), versiegebondenheid (C118), ontbrekende context en technisch foutgedrag.
- [ ] Geautoriseerde modelevaluatie rapporteert per geval onterechte goedkeuring, onterechte afkeur, gemiste overtreding, passende onthouding, onzekerheid en technische fout; kwaliteitsgrenzen zijn vooraf vastgelegd.
- [ ] Kosten, responstijd, privacy, foutbeleid en fallback zijn vooraf beslist; productieactivering volgt pas na expliciet geaccepteerd bewijs.
- [ ] Kerntekst blijft ongewijzigd; geen automatische herstelroute, signaalafkeur of zelfstandige poort toegevoegd.
- [ ] Concrete implementatiediff is onafhankelijk gereviewd volgens de CLI-rolverdeling; effectclaims zijn beperkt tot uitgevoerd bewijs.

## Relaties en bronnen

Gerelateerd aan DEF-771, DEF-766 en DEF-768. Afstemming met DEF-815 (model-/promptbeleid), DEF-831 (poortbeleid), DEF-832 (geen betekenisreparatie) en het resultaatcontract uit DEF-624. Bestaande snapshot-/herlaadwerkzaamheden uit DEF-626 worden niet stil bij deze specificatie betrokken.

Bronnen gecontroleerd: lokaal besluiten-chris-v1.md en gezamenlijke-synthese-v5.md; ADR-001 in docs/adr/ADR-001-json-rulecontract-en-evaluatorstrategie.md; DEF-815 via Linear opgehaald op 26 september 2026. De definitieve issue-relaties en actuele doelissues worden bij de geautoriseerde aanmaak gecontroleerd.


## Specificatie-protocol — voorbereiding vóór bouwen

| Aspect | Bevinding |
|---|---|
| Relevante bestanden | Op app-HEAD 5fb535ee: src/toetsregels/regels/INT-02.json, src/services/validation/evaluators/judgment_review.py, src/services/validation/modular_validation_service.py en src/ui/components/validation_view.py. O1 is de huidige implementatie op de featurebranch; nog geen merge-/uitrolclaim. |
| Bestaande patronen | .claude/rules/patterns.md: drie gestructureerde contextlijsten, AI-aanroepen via AIServiceV2, modelselectie via ModelRouter, asynchrone I/O en expliciet foutbeleid. Geen tweede modelregister of generieke AI-fallback introduceren. |
| Afhankelijkheden | INT-02-contract, DEF-624-resultaatcontract, DEF-815-modelbeleid en de beoordeelde ESS-03/ESS-05-patronen (DEF-766/DEF-768); poortbeleid DEF-831 en herstelbeleid DEF-832 blijven leidend. Concrete technische herbruikbaarheid bij uitvoering verifiëren. |

### Open vragen vóór implementatie

1. Wie bezit en accepteert de onafhankelijke goldset, welke vooraf vastgelegde foutgrenzen gelden per uitkomst en hoe worden onbesliste expertlabels behandeld?
2. Welk model-/promptprofiel, evaluatiebudget en privacy-/bewaarbeleid autoriseert Chris, en wat is de toegestane fallback bij onbeschikbaarheid of budgetoverschrijding?

### Uitvoering en rolverdeling

Repo en werkdirectory: /Users/chrislehnen/Projecten/Definitie-app. Bij uitvoering eerst actuele origin/main ophalen en een eigen featurebranch voor het nieuwe issue maken; nooit direct op main werken. Exacte scope en branch volgen de toekomstige uitvoeringsopdracht. De hoofdsessie coördineert, echte Claude Code CLI implementeert, afzonderlijke Codex CLI reviewt de concrete diff. Geen bouwstart door deze registratie.

Aanvullende procescriteria: wijzigingen gecommit op de eigen featurebranch en verwijzingen gecontroleerd vóór oplevering. Nog geen van de implementatiecriteria is afgevinkt.
