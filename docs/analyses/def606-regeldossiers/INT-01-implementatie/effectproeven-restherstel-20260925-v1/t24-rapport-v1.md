# T24 — onafhankelijke restherstelproef

Uitgevoerd op gereviewde bron `108f38a3933cfe1335908d77a1aaadf0f8f36cc3`, contract `def770-int01/7`. Vooraf geldend beleid: referentie-contract-v2.md. Nieuwe onafhankelijke maker, A/B en adjudicator (Astra/high); eerste oordelen en finale referenties vóór appuitvoering verzegeld. Kleine synthetische AI-proef, geen menselijke validatie.

## Uitkomst

**Acceptatie niet gehaald: 23/24 volledig conform.** Dezelfde onafhankelijke codereviewer heeft redenen, passages en broncitaatstatus van de overige23 gecontroleerd. Eén nieuwe dekkingsafwijking (T17) blijft Important/open onder het beleid van deze proef. Geen historische labels aangepast.

- 12 automatische pass,7 fail,4 review_required,1 niet beoordeeld.
- 19/23 niet-lege gevallen automatisch beoordeeld (82,61%);19/19 zekere beslissingen normatief ondersteund.
- Beide laadpaden/opslag24/24consistent; oorspronkelijke tekst behouden;0fouten.
- Geen volledige INT-01-pass; compactheid/begrijpelijkheid blijven afzonderlijk open.

## Afwijking T17

> bord met de tekst ‘Ga verder!’ dat tijdens een oefening een vrije doorgang markeert.

Normatief en automatisch volgens beide referenties/adjudicatie pass; app review_required bij citaatslot. Een na het citaat begonnen dat-bijzin valt buiten de bestaande positieve herkenning en buiten de vooraf goedgekeurde waar+voorzetsel-/nominale categorieën. Dezelfde beperking bestaat op de base, dus geen nieuwe regressie van het herstel. Alleen het woord dat herkennen is onvoldoende veilige reparatie; een zelfstandige vervolgzin kan daarmee beginnen. Concrete bronoorzaak en reproductie: t24-onafhankelijke-bewijsreview-v1.md. Dispositie: open binnen DEF-770; geen waiver voor deze proef.

## Alle gevallen

| ID | Normatief | Verwacht automatisch | App | Conform |
|---|---|---|---|---|
| T01 | pass | pass | pass | ja |
| T02 | pass | pass | pass | ja |
| T03 | pass | pass | pass | ja |
| T04 | fail | fail | fail | ja |
| T05 | pass | pass | pass | ja |
| T06 | pass | pass | pass | ja |
| T07 | pass | pass | pass | ja |
| T08 | fail | fail | fail | ja |
| T09 | pass | pass | pass | ja |
| T10 | fail | fail | fail | ja |
| T11 | fail | fail | fail | ja |
| T12 | fail | fail | fail | ja |
| T13 | pass | pass | pass | ja |
| T14 | fail | fail | fail | ja |
| T15 | pass | pass | pass | ja |
| T16 | pass | pass | pass | ja |
| T17 | pass | pass | review_required | nee |
| T18 | fail | fail | fail | ja |
| T19 | pass | pass | pass | ja |
| T20 | pass | pass | pass | ja |
| T21 | not_evaluated | not_evaluated | not_evaluated | ja |
| T22 | review_required | review_required | review_required | ja |
| T23 | fail | review_required | review_required | ja |
| T24 | review_required | review_required | review_required | ja |

Bewijs: t24-gevallen-v1.json, referentie-contract-v2.md, t24-referentie-A/B-v1.json, t24-adjudicatie-v1.json, beide verzegelingen, t24-resultaat-oud/nieuw-v1.json, t24-vergelijking-v1.json, bronbinding-v1.json. Eventuele latere beleidsbesluiten veranderen deze historische uitkomst niet.
