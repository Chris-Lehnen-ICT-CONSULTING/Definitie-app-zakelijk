# Kwalificatieproef v11 — uitslag (v1)

8 oktober 2026. Vastgelegd door Claude uit `kwalificatieproef-v11/`. Manifest v11 = technische herstart van v10 (besluit 24): contract /5 (R1+R2, besluit 22), prompt /6, schema `d3ad029e…`. **Consistentietoets 7A — geen onafhankelijk bewijs**; de regels en de papieren toets zijn mede op deze zichtbare gevallen gemaakt.

## Samenvatting

- Fase 1 (regressie): mechanisch geslaagd True.
- Fase 2 (ontwikkeling): mechanisch geslaagd True; stopreden None.
- Juist 23/24; onterechte passes 0/12; kritieke onterechte passes 0/6; onterechte fails 0/18.
- Per label: pass 12/12, fail 5/6, review_required 6/6.
- Technische fouten 0/24, citaatfouten 0/24.
- Omzettingen door de dienst: {'totaal': 7, 'per_richting': {'fail→review_required': 1, 'pass→review_required': 6}, 'per_regel': {'bronnen_open': 1, 'bronvoorschrift_niet_overgenomen': 1, 'conflict': 4, 'onduidelijk_naast_kenmerk': 1}}.
- Kosten (conservatief, cumulatief fase 1+2): US$1.1983.

In alle 6 reviewgevallen gaf het model zelf `pass`; de mechanische beslisregel van de dienst (conflict, bronnen_open, bronvoorschrift_niet_overgenomen, R2) zette ze om naar review. G050 (label fail) werd review (veilige richting).

## Fase 1

| Geval | Label | Uitkomst | Model | Omzetting |
|---|---|---|---|---|
| C105 | fail | fail ✔ | fail | — |
| C107 | review_required | review_required ✔ | insufficient_information | — |
| C112 | pass | pass ✔ | pass | — |

## Fase 2

| Geval | Label | Uitkomst | Model | Omzetting |
|---|---|---|---|---|
| G011 | pass | pass ✔ | pass | — |
| G015 | pass | pass ✔ | pass | — |
| G019 | pass | pass ✔ | pass | — |
| G027 | pass | pass ✔ | pass | — |
| G030 | pass | pass ✔ | pass | — |
| G039 | pass | pass ✔ | pass | — |
| G007 | pass | pass ✔ | pass | — |
| G021 | pass | pass ✔ | pass | — |
| G037 | pass | pass ✔ | pass | — |
| G041 | pass | pass ✔ | pass | — |
| G046 | pass | pass ✔ | pass | — |
| G055 | pass | pass ✔ | pass | — |
| G008 | fail | fail ✔ | fail | — |
| G012 | fail | fail ✔ | fail | — |
| G036 | fail | fail ✔ | fail | — |
| G048 | fail | fail ✔ | fail | — |
| G050 | fail | review_required ✘ | fail | conflict |
| G052 | fail | fail ✔ | fail | — |
| G042 | review_required | review_required ✔ | pass | conflict |
| G045 | review_required | review_required ✔ | pass | bronnen_open |
| G047 | review_required | review_required ✔ | pass | bronvoorschrift_niet_overgenomen |
| G060 | review_required | review_required ✔ | pass | onduidelijk_naast_kenmerk |
| G070 | review_required | review_required ✔ | pass | conflict |
| G076 | review_required | review_required ✔ | pass | conflict |

## Verloop v7 → v11 (fase 2)

| Proef | Juist | Onterechte passes | Review terecht |
|---|---|---|---|
| v7 | 18/24 | 5 | 0/6 |
| v8 | 19/22 (gestopt) | 1 | 2/4 |
| v9 | 15/17 (gestopt) | 1 (kritiek) | — |
| v11 | 23/24 | 0 | 6/6 |

## Stop (besluit 23/24)

Dit was de laatste run van dit onderdeel. De iteratie op O2 stopt hier. Vervolgkeuze voor Chris: de hold-out (16 gevallen, enig onafhankelijk bewijs; apart akkoord) of O2 parkeren. De variatiemeting v9 liet 1–2 onterechte passes per run zien vóór R1+R2; of R1+R2 die variatie in nieuwe gevallen opvangt, kan alleen de hold-out laten zien.
