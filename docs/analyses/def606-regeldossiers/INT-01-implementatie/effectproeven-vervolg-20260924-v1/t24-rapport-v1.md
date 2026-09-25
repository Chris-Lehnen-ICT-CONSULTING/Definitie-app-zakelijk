# T24 — nieuwe onafhankelijke toetsproef: 22/24 conform

25 september 2026. Gemeten appbron: `23cc51bfddc5ee9393dea52e6a52a55b3e65615d`, beoordelingscontract `def770-int01/6`. **Acceptatie niet gehaald.** De twee oorspronkelijke herstelbevindingen zijn gesloten; deze proef brengt twee nieuwe afwijkingen aan het licht. Gelijknamige casus-ID’s uit oudere sets verwijzen naar andere teksten.

## Opzet en resultaat

Een nieuwe onafhankelijke maker leverde 24 synthetische gevallen. Twee nieuwe Astra/high-beoordelaars vormden zelfstandig normatieve en automatische referenties. Een derde beoordelaar besliste verschillen. Contract, gevallen, bron en referenties zijn verzegeld vóór appuitvoering. Geen historische tekst, label of score is gewijzigd.

- **22/24 volledig conform** status, reden/passage en relevante broncitaatstatus; bevestigd door dezelfde onafhankelijke codereviewer na uitvoering.
- Zinsstructuur: **13 pass, 6 fail, 4 review_required, 1 not_evaluated**.
- Automatische dekking: **19/23 niet-lege gevallen = 82,61%**. Daarvan zijn **18/19 normatief ondersteund**. De negentiende automatische beslissing geeft onbewezen zekerheid bij een los label.
- Beide laadpaden en opslag: **24/24 consistent**, oorspronkelijke teksten behouden, nul uitvoeringsfouten en nul volledige INT-01-passes.
- Bij de vier automatische doorverwijzingen beoordeelt de normatieve referentie één tekst als pass en drie als fail. Compactheid en begrijpelijkheid blijven aparte inhoudelijke beoordelingen.

## Nieuwe T20 — onnodige doorverwijzing bij nominale titelvoortzetting

> fiche bij het fictieve oefenboek ‘Wie opent het luik?’ met de kleurcode van de bijbehorende opdracht

Referentie: normatief en automatisch pass. App: review_required bij het citaatslot. Dit is geen voortzetting met waar + voorzetsel, waarvoor het nieuwe gebruikersbesluit geldt. De reviewer reproduceerde dat de bestaande voorzetselgroepherkenning hoogstens een lidwoord plus één kernwoord ondersteunt. Zij strandt op **van de bijbehorende opdracht**; zonder bijbehorende accepteert dezelfde helper de voortzetting wel.

**Important, open blocker binnen DEF-770; geen waiver.** Dit is een gemeten beperking van de herkenning, geen reden om het verzegelde referentielabel achteraf te wijzigen.

## Nieuwe T22 — zekere deelclaim zonder positieve grond

Begrip én tekst:

> schakelblad

Referentie: inhoudelijke beoordeling nodig; een los begripslabel biedt onvoldoende bewijs van een definitieformulering. App: zinsstructuur-pass. De bestaande labelcontrole herkent alleen een afsluitende dubbele punt; zonder gevonden grenssignaal ontstaat vervolgens automatisch een pass.

**Important, open blocker binnen DEF-770; geen waiver.** Het totale INT-01-oordeel blijft wel review_required. De fout betreft de zekere deelclaim over zinsstructuur; er is geen volledige kwaliteitsgoedkeuring gegeven.

## Bewijs en beperking

Voor de overige 22 gevallen bevestigde de reviewer de redenen, passages en broncitaatstatus. Bij T14 normaliseert de app witruimte in de grenspassage; de grens blijft herkenbaar en de oorspronkelijke tekst blijft behouden. Lege T21 wordt niet beoordeeld. De oude arm is eveneens uitgevoerd zonder fouten en als historische vergelijking bewaard; zijn uitkomsten worden niet als /6-contractresultaten gepresenteerd.

Maker: Astra/high `01a0d535-0354-7213-81dc-9b6d9eb850a4`. Nieuwe referentiesessies: `01a0d70b-f2d6-79f0-a0a9-b0f308524c94` en `01a0d70b-fd37-7973-846d-96e29abc0732`. Nieuwe adjudicator: `01a0d70f-dc94-7563-9a8f-6f86757ba045`. Zij gebruikten geen tools, appcode of appuitkomsten. De codereviewer zag deze gevallen pas na de bevroren proef. Dit is AI-beoordeeld synthetisch bewijs, geen menselijke validatie of algemene betrouwbaarheidsclaim.

Bewijs: [contract vooraf](referentie-contract-v2.md), [referentieverzegeling](t24-referenties-verzegeling-v1.json), [adjudicatie](t24-adjudicatie-v1.json), [mechanische vergelijking](t24-vergelijking-v1.json), [nieuwe appuitvoer](t24-resultaat-nieuw-v1.json), [oude appuitvoer](t24-resultaat-oud-v1.json), [bevestiging door reviewer](../herstel-20260924-v1/astra-acceptatiebevindingen-v1.md) en [onafhankelijke rollen](onafhankelijke-rollenbinding-v1.json).
