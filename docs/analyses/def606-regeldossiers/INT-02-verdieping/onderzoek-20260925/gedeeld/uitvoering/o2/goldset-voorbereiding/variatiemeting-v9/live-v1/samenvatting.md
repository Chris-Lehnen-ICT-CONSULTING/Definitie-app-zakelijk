# INT-02 O2 — variatiemeting v9, samenvatting

Automatisch opgesteld door `variatiemeting_v9.py` (live). Buiten het kwalificatieprotocol (besluit 21): geen kwalificatie, geen herhaling van een kwalificatiefase, geen DEF-815-claim. De ontwikkelgevallen zijn een consistentietoets (7A).

- Calls: 48 van 48 gepland; stopreden: —.
- Kosten (conservatief, prijzen manifest v9): US$2.16746; plafond US$3.00.

## Totaal

| | v9-fase2 | h1 | h2 |
|---|---|---|---|
| gedraaid | 17 | 24 | 24 |
| juist | 15/17 | 21/24 | 22/24 |
| onterechte passes | 1 (G050) | 2 (G050, G060) | 1 (G060) |
| kritieke false passes | 1 (G050) | 1 (G050) | 0 |

- Gevallen met wisselende status: 2 (G030, G050).
- Gevallen met wisselende bronfuncties: 7 (G011, G015, G030, G048, G050, G052, G076).

## Per geval

Bronfuncties per bron in passagevolgorde (`·` scheidt passages, `–` = `not_addressed`); `bed` = bedoeling. Een status met ✘ wijkt af van het label.

| Geval | Label | v9-fase2 | h1 | h2 | Stabiel | Wisselende bronfuncties |
|---|---|---|---|---|---|---|
| G011 | pass | `pass` | `pass` | `pass` | ja | B1: v9-fase2 derivation / h1 derivation / h2 criterion |
| G015 | pass | `pass` | `pass` | `pass` | ja | bed: v9-fase2 criterion / h1 criterion·criterion / h2 criterion·criterion; B1: v9-fase2 criterion / h1 criterion·criterion / h2 criterion·criterion; juridische_context/0: v9-fase2 – / h1 –·– / h2 –·–; organisatorische_context/0: v9-fase2 – / h1 –·– / h2 –·– |
| G019 | pass | `pass` | `pass` | `pass` | ja | — |
| G027 | pass | `pass` | `pass` | `pass` | ja | — |
| G030 | pass | `review_required` ✘ | `review_required` ✘ | `pass` | **nee** | B2: v9-fase2 actor_prescription / h1 actor_prescription / h2 criterion |
| G039 | pass | `pass` | `pass` | `pass` | ja | — |
| G007 | pass | `pass` | `pass` | `pass` | ja | — |
| G021 | pass | `pass` | `pass` | `pass` | ja | — |
| G037 | pass | `pass` | `pass` | `pass` | ja | — |
| G041 | pass | `pass` | `pass` | `pass` | ja | — |
| G046 | pass | `pass` | `pass` | `pass` | ja | — |
| G055 | pass | `pass` | `pass` | `pass` | ja | — |
| G008 | fail | `fail` | `fail` | `fail` | ja | — |
| G012 | fail | `fail` | `fail` | `fail` | ja | — |
| G036 | fail | `fail` | `fail` | `fail` | ja | — |
| G048 | fail | `fail` | `fail` | `fail` | ja | bed: v9-fase2 –·– / h1 unclear·– / h2 –·–; B1: v9-fase2 unclear·actor_prescription / h1 criterion·actor_prescription / h2 unclear·actor_prescription |
| G050 | fail | `pass` ✘ | `pass` ✘ | `review_required` ✘ | **nee** | B1: v9-fase2 derivation·criterion / h1 derivation·criterion / h2 derivation·discretionary_decision_rule |
| G052 | fail | niet gedraaid | `fail` | `fail` | ja | B2: h1 unclear / h2 criterion |
| G042 | review_required | niet gedraaid | `review_required` | `review_required` | ja | — |
| G045 | review_required | niet gedraaid | `review_required` | `review_required` | ja | — |
| G047 | review_required | niet gedraaid | `review_required` | `review_required` | ja | — |
| G060 | review_required | niet gedraaid | `pass` ✘ | `pass` ✘ | ja | — |
| G070 | review_required | niet gedraaid | `review_required` | `review_required` | ja | — |
| G076 | review_required | niet gedraaid | `review_required` | `review_required` | ja | B2: h1 actor_prescription / h2 not_a_criterion; B3: h1 – / h2 unclear |
