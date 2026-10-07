# INT-02 O2 — uitslag kwalificatieproef v6, fase 1 (regressie)

7 oktober 2026. Vastgelegd door Claude uit de bewaarde proefbestanden in `kwalificatieproef-v6/` (`regressie-resultaat.json`, `regressie-bundel.json`, `grootboek.jsonl`, `regressie-afronding.voltooid`). Er is geen nieuwe call gedaan en er is niets opnieuw gedraaid. De inhoudelijke duiding staat al in besluit 14 van `../../besluit-chris-promptcorrectie-en-v3-v1.md`; deze notitie legt de cijfers vast.

## Kader

- Manifest `kwalificatie-manifest-v6.json`, SHA-256 `37b8e36a46c30a3d62b579a0eaf2afc544a454d709c49030c5626fa318539e37`; identiteit `90920d6c35337be48cacb58c0f8f01616200aab332915ddc1a960c62314def4b`.
- Akkoord `kwalificatie-akkoord-v6.json`, SHA-256 `955d84dc8f84be6b6a8ac19b9f41bb5a911ef2de6301cf478b1385be1e45bc4a`; gevallen `af1ab46c…6953`.
- Anthropic `claude-opus-5` (gerapporteerd model), profiel `def835-kwalificatieproef-opus5-v1`, prompt `def835-int02-prompt/3`, contract `def835-int02-assessment/3`.
- Uitsluitend fase 1 (C105, C107, C112), volgens besluit 13.
- Start 15:15:11 UTC, einde 15:15:18 UTC, looptijd 6,7 s.
- 1 inferentie en 1 telverzoek; daarna gestopt.
- Grootboek: `fase_einde` met `bewijs_opgeslagen: true`, `mechanisch_geslaagd: false`, `stopreden: "invalid_output"`.

## Uitkomst

| Geval | Verwacht | Waargenomen | Toelichting |
|---|---|---|---|
| C105 | fail | `error` (`invalid_output`) | HTTP 200, `stop_reason` `end_turn`, één tekstblok. Het model oordeelde inhoudelijk `fail` (passage "De medewerker laat de aanvrager toe.", functie `actor_prescription`, grond de bedoeling), maar zette in de passage een extra veld `reason`. Het gesloten contract weigert onbekende velden, dus het document werd `error`. |
| C107 | review_required | niet gedraaid | De runner stopte na C105. |
| C112 | pass | niet gedraaid | De runner stopte na C105. |

Redenen niet geslaagd volgens de runner: `niet_volledig_uitgevoerd`, `technische_of_citaatfout`, `te_weinig_juist` (0/1 juist, 1 technische fout).

## Kosten en latentie

| Geval | Invoertokens | Uitvoertokens | Kosten |
|---|---|---|---|
| C105 | 3.543 | 351 | $0,02649 |

Kosten zijn gemelde usage × routerprijzen ($5 per 1M invoertokens en $25 per 1M uitvoertokens). Er was geen onzekere call. Dit is geen providerfactuur. Latentie 4.780 ms.

## Vervolg

Chris koos op 07-10-2026 optie A (besluit 14): het antwoordschema via de API meesturen (prompt /4). Manifest v7 en het akkoord daarop staan in besluit 15. Het v6-bewijs blijft ongewijzigd.
