# DEF-835 INT-02 O2 — processtatus uitvoering v15

7 oktober 2026. Vervangt `processtatus-uitvoering-v14.md` (07-10) als actuele processtatus.

## Stand

- O1 (DEF-771) en de O2-beoordelingsdienst (DEF-835, PR #488, 29-09) staan op main. De O2-dienst is niet geactiveerd; de app gebruikt de O1-reviewroute. Geen WP5a-/UI-stap; GitHub Actions blijft uit.
- Werk op `feature/DEF-835-int02-o2` in de werkboom `.claude/worktrees/DEF-835-int02-o2`, gepusht als back-up. Geen PR en geen merge.
- **Fase 1 (regressie) van kwalificatieproef v7: mechanisch geslaagd**, 3/3 juist, US$0,10108. Details: `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v7-uitslag-v1.md`.
- **Fase 2 (ontwikkeling) van kwalificatieproef v7: mechanisch niet geslaagd, 18/24 juist** (minimaal 21). Juist pass 12/12, juist fail 6/6, juist review_required 0/6. Vijf onterechte passes (G042, G045, G060, G070, G076, alle met label `review_required`) en één false fail (G047). Kritieke false pass 0, technische fouten 0, citaatfouten 0; dienstregel nergens toegepast; nooit `insufficient_information`. Details: `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v7-ontwikkeling-uitslag-v1.md`.
- **Procesafspraak max_false_pass 0 voor ontwikkeling geschonden** (5). Manifest v7 had daar `null`, dus de runner telde het niet als reden.
- Patroon: bij bronnen die verschillende kanten op wijzen kiest het model één kant; "criterium of plicht" wordt beslist op de zinsvorm en op een letterlijk overeenkomende bron. Onzekerheid hooguit `non_decisive` (G045, G047, G076).
- Kosten fase 2 US$0,88056 (24 calls, gemiddeld US$0,03669), p95 9.634 ms. Cumulatief v7 US$0,98164 voor 27 calls; in akkoord v7 resteren 16 calls en circa US$11,02.
- **Hold-out niet gedraaid.**
- De inhoudelijke beoordeling van de passagegronden door Chris staat voor fase 1 en fase 2 nog open.

## Besluiten 07-10 (in `besluit-chris-promptcorrectie-en-v3-v1.md`)

Ongewijzigd ten opzichte van v14: besluiten 1–15, het laatste is manifest v7 (`872482f4…`) en fase 1. Het akkoord op fase 2 en de procesafspraak max_false_pass 0 voor ontwikkeling zijn door Chris in de sessie gegeven; ze staan (nog) niet als genummerd besluit in het besluitbestand.

## Proefhistorie

| Ronde | Prompt / contract | Fase | Uitkomst | Kosten |
|---|---|---|---|---|
| v4 | /2 / /1 | regressie | inhoudelijk 3/3, C112 `invalid_citation` | $0,082385 |
| v5 | /3 / /2 | regressie | 2/3; C107 `fail` | $0,07772 |
| variatiemeting C107 | /3 / /2 | buiten kwalificatie | 5/5 juist | — |
| v6 | /3 / /3 | regressie | gestopt na C105: `invalid_output` | $0,02649 |
| v7 | /4 / /3 | regressie | **3/3, geslaagd** | $0,10108 |
| v7 | /4 / /3 | ontwikkeling | **18/24, niet geslaagd**; 5 false pass | $0,88056 |

## Huidige keten

Ongewijzigd ten opzichte van v14: prompt `def835-int02-prompt/4` (systeemtekst /3 plus schemaroute, commit `2081899ea`) en contract `def835-int02-assessment/3` (citaatposities door de dienst, dienstregel `discretie_zonder_bedoeling`).

## Volgende actie

**Besluit van Chris over het vervolg.** De opties staan uitgewerkt in de ontwikkeluitslag:

1. prompt /5 met een bronconflictstap;
2. contract /4 met gestructureerde bronfuncties en een mechanische review-regel;
3. labelherziening G047/G070 via een nieuwe freeze (ook dan 20/24, onder 21);
4. max_false_pass 0 voor ontwikkeling in het volgende manifest.

Elke wijziging aan prompt of contract vraagt een nieuw manifest en akkoord, opnieuw regressie en daarna ontwikkeling. De hold-out blijft dicht tot ontwikkeling slaagt en Chris er apart akkoord op geeft. Ook nog te bespreken: aandachtspunt 3 (meerdere passages; in fase 2 acht keer voorgekomen zonder mechanische problemen) en de inhoudelijke beoordeling van fase 1 en 2.

## Actuele documenten

- `besluit-chris-promptcorrectie-en-v3-v1.md` — besluiten 1–15 (07-10).
- `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v7.json` en `kwalificatie-akkoord-v7.json` — de geldende proef.
- `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v7-uitslag-v1.md` (fase 1) en `kwalificatieproef-v7-ontwikkeling-uitslag-v1.md` (fase 2); bewijs in `kwalificatieproef-v7/`.
- Eerdere uitslagen: `kwalificatieproef-v4-uitslag-v1.md`, `-v5-`, `-v6-` (zelfde map) en `goldset-voorbereiding/variatiemeting-c107-v1/uitslag-v1.md`.
- `takenlijst-v51.md` — laatste takenlijst van de coördinator (30-09).

## Achterhaald (ongewijzigd bewaard)

- `processtatus-uitvoering-v14.md` (07-10): stand na fase 1 van v7, met akkoord op fase 2 als volgende actie; achterhaald door deze v15.
- Eerder als achterhaald benoemd en dat blijft zo: `processtatus-uitvoering-v13.md`, `processtatus-uitvoering-v12.md`, de akkoorden en manifesten v3–v6, `goldset-voorbereiding/labelronde-v1/takenlijst-v14.md`, `goldset-voorbereiding/herwerking-v1/uitvoeringsstatus-v1.md`.
