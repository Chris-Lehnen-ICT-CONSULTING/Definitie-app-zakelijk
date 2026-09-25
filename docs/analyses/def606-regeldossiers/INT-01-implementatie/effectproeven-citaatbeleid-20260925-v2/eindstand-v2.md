# INT-01 — correcties gereviewd; acceptatie-afbakening nog open

25 september 2026. **Technische correcties gereed en gereviewd; onafhankelijke acceptatie nog niet gehaald.** DEF-770 blijft In Progress. Beide PR’s blijven draft. Geen merge of live skillsactivatie (ALG-391).

## Huidige bron

- App: `86b2c0b20a2913484256b931e6e3c7848391ed13`, contract `def770-int01/10`.
- Skills: `2fa72640f6cd48d0d9e5fc9e08fd19942b05a979`.
- Binding: [correctie-bronbinding-v1.json](correctie-bronbinding-v1.json). De historische T24 in deze map is op `/9` uitgevoerd; zij wordt niet achteraf als acceptatie van `/10` gepresenteerd.

## Uitgevoerd

Het expliciet goedgekeurde algemene citaatbeleid is toegepast. Grammatica-afhankelijke positieve citaatpaden zijn verwijderd. Na onafhankelijke proeven zijn concrete fouten hersteld: lijstcontext over meerdere opsommingsleden, citaatslot met tussenliggende komma/puntkomma/dubbele punt (ook zonder spatie), en onterechte extra onzekerheid bij expliciet aangekondigde voorbeeldcodes/getallen. Bij deze herstelde grensgevallen behouden onbekende afkortingen en niet-ondersteunde vervolgen hun onzekerheid; de twee hieronder genoemde afbakeningsvragen blijven apart open. Contractversies voorkomen hergebruik van verouderde opgeslagen beoordelingen.

Claude Code CLI implementeerde en verwerkte de correcties in sessie `442a98fb-a377-403f-996e-433cf4a664fc`. Dezelfde onafhankelijke Codex CLI-reviewer `01a0cfac-ea05-7700-ba73-8b5659751c1c` reviewde met **Astra/high** de concrete app- en skillsdiffs. Alle bevestigde codebevindingen zijn gesloten. De coördinator schreef geen productcode of unit-tests. Zie [rollenbinding](rollenbinding-v1.json) en [laatste gerichte review](technisch-bewijs-v1/astra-correctiereview-v4.md).

## Verificatie op de uiteindelijke bron

- Canonieke `make test`: **7567 passed, 75 skipped, 1 bestaande DEF-609-xfail, 21 subtests; exit 0**. De offlinebeveiliging bleef actief. [Volledig log](technisch-bewijs-v1/make-test-finaal-v4.txt), [JUnit](technisch-bewijs-v1/finale-unit-v4-junit-geredigeerd.xml), [inventaris](technisch-bewijs-v1/finale-unit-v4-inventaris-geredigeerd.json).
- Laatste correctie: RED 9/17; GREEN 534; regressie 1087 geslaagd; integratie 27 geslaagd en 1 bestaande skip. Gepinde Ruff, Black en make lint: exit 0.
- Bundels: **94 tests en 2 subtests geslaagd**; canonieke ZIP-inhoud gelijk aan de bron; alias conform bestaande naamrewrite. [Bewijs](technisch-bewijs-v1/bundeltests-v4.txt).
- Eerdere directe pytest-aanroepen gaven twee SQLite-offlinefouten; die zijn op de ongewijzigde base gereproduceerd en passeren via de voorgeschreven canonieke runner. Eén DEF-126 `red_phase`-prompttest faalt ook op de base en valt buiten de unitgate; de reviewer heeft de expliciete scopewaiver bevestigd. Deze mislukte runs zijn niet als groen gepresenteerd.

## Onafhankelijke proeven

Voor elke T24: nieuwe maker, twee afzonderlijke referentiebeoordelaars en afzonderlijke adjudicator; alle Astra/high zonder tools. Bron en referenties zijn vóór appuitvoering verzegeld. Dit zijn kleine synthetische AI-proeven, geen menselijke validatie.

| Proef | Bron | Statusconform | Volledig, inclusief diagnostiek | Uitkomst |
|---|---|---:|---:|---|
| Algemeen citaatbeleid v1 | `/8`, `ad4be749` | 22/24 | 20/24 | Niet gehaald; bevestigde codefouten daarna hersteld |
| Citaatcorrecties v2 | `/9`, `58f70cb1` | 22/24 | 21/24 | Niet gehaald; twee afbakeningsvragen en één codefout |

De laatste codefout (`bijv. 12.`) is onder `/10` hersteld en onafhankelijk gesloten. Voor `/10` is nog geen nieuwe onafhankelijke T24 gestart. [Historisch T24-rapport](t24-rapport-v1.md), [bewijsreview](t24-onafhankelijke-bewijsreview-v1.md), [vorige proef](../effectproeven-citaatbeleid-20260925-v1/t24-rapport-v1.md). Alle oorspronkelijke labels en resultaten blijven intact.

**G24 blijft geslaagd binnen de bestaande claimgrens:** 3 paren inhoudelijk beter, 9 gelijk, geen waargenomen nieuwe betekenis-/bronfout of verslechtering. De zes volledige prompts en API-verzoeken zijn gelijk aan de succesvolle generatiebron; generatiecode/configuratie en generatieskill bleven ongewijzigd. De bestaande 48 ruwe/opgeschoonde teksten geven onder `/10` 96 consistente service-uitkomsten en 48 consistente opslagcontroles, zonder fouten of volledige INT-01-pass. [Behoudbinding](g24-behoudbinding-contract10-v1.json).

De eerdere beperkingen blijven gelden: gedeeld betekenisverlies bij G04 en actoronzekerheid bij G02 zijn niet opgelost door dit citaatwerk; de proef bewijst geen algemeen foutloze generatie. Er zijn geen nieuwe betaalde generatiecalls gedaan. Cumulatief US$7,533075 van US$8,10; resterend US$0,566925.

## Twee afbakeningsvragen — nog geen gebruikersbesluit

1. `zacht uitgesproken aanwijzing met de woorden ‘nu beginnen’ waarmee een luisteroefening wordt geopend.` Er staat geen zinseindteken in het citaat. Referentie A verwacht pass; B/adjudicatie lezen het proefcontract ruimer en verwachten review. Het leidende besluit en de bronreviews behouden citaten zonder slotteken. Dit vereist eenduidige overdracht, geen stil herlabelen.
2. `waarde waarmee de uitloop van een proefwiel wordt genoteerd in zkr.` De onbekende afkorting staat op het teksteinde. Er is geen vervolg of buitenste grens aangetoond; onbekende betekenis bewijst geen afgebroken formulering. De referenties vragen toch een open formuleringsbeoordeling.

De coördinator heeft Chris expliciet gevraagd of beide op zinsstructuur mogen slagen zolang er geen concrete grens of afgebroken formulering is, met compactheid/begrijpelijkheid inhoudelijk open. Dat is het advies, **nog geen vastgesteld besluit**. De vraag is tijdens het overige herstel gesteld; er is nog geen antwoord ontvangen.

Vervolg na dit besluit: referentiecontract vooraf eenduidig maken en vervolgens nieuwe onafhankelijke T24. Geen mergevrijgave op basis van de huidige proeven.

## Publicatiekopieën van testbewijs

De geheimenscanner blokkeerde de eerste bewijscommit op twaalf sleutelvormen in testnamen. Alle twaalf komen exact overeen met de samengestelde `_PROJECT_OPENAI_KEY`-testfixture uit `tests/unit/utils/test_pii_redaction_api_keys.py`. Vier publicatiekopieën van JUnit/inventaris zijn daarom geredigeerd: uitsluitend deze parameterwaarde is vervangen door een zichtbaar redactie-label. Testaantallen, statussen en overige inhoud blijven behouden; originele uitvoer en oorspronkelijke hashes blijven lokaal beschikbaar. Scannerconfiguratie en beveiligingsregels zijn ongewijzigd. Zie [redactiebinding](publicatie-redactie-v1.json). De eerdere onafhankelijke oplevercheck betreft de originele bewijsversie; de publicatiekopieën zijn herkenbaar als afgeleide documenten.
