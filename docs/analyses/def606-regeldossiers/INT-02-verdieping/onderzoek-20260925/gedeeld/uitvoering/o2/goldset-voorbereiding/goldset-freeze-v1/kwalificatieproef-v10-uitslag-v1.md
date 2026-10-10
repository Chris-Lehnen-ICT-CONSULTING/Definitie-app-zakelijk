# Kwalificatieproef v10 — uitslag (v1)

8 oktober 2026. Vastgelegd door Claude uit de bewaarde bestanden in `kwalificatieproef-v10/`. Manifest v10: contract /5 (R1+R2, besluit 22), prompt /6, schema `d3ad029e…`. Consistentietoets 7A — geen onafhankelijk bewijs.

## Fase 1 (regressie)

- Stopreden: None; mechanisch geslaagd: True; kosten (conservatief, cumulatief): US$0.1133.

| Geval | Label | Uitkomst | Omzetting | Fout |
|---|---|---|---|---|
| C105 | fail | fail | — | — |
| C107 | review_required | review_required | — | — |
| C112 | pass | pass | — | — |

## Fase 2 (ontwikkeling) — onderbroken door netwerkstoring

- Stopreden: `timeout` na 6 van 24 gevallen; beëindigd 2026-10-08T15:22:38.444771+00:00; onzekere calls: ['G039'].
- Kosten (conservatief, cumulatief fase 1+2): US$0.5591.
- De timeout bij G039 viel samen met het wegvallen van de verbinding van de Mac (15:22 UTC). Dit is een infrastructuurstoring, geen modeluitkomst; de fase is daarom niet inhoudelijk beoordeelbaar.

| Geval | Label | Uitkomst | Omzetting | Fout |
|---|---|---|---|---|
| G011 | pass | pass | — | — |
| G015 | pass | pass | — | — |
| G019 | pass | pass | — | — |
| G027 | pass | pass | — | — |
| G030 | pass | review_required | conflict | — |
| G039 | pass | error | — | timeout |

## Vervolg

Besluit 24 (Chris): eenmalige technische herstart als manifest v11 (identiek aan v10 op proefmap en identiteit na), uitgevoerd met `caffeinate`. Dit blijft de laatste run van dit onderdeel (stopafspraak besluit 23).
