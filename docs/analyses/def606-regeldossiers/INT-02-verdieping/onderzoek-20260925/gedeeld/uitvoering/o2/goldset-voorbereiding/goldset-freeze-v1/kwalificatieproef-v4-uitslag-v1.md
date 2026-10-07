# INT-02 O2 — uitslag kwalificatieproef v4, fase 1 (regressie)

7 oktober 2026. Vastgelegd door Claude uit de bewaarde proefbestanden in `kwalificatieproef-v4/` (`regressie-resultaat.json`, `regressie-bundel.json`, `grootboek.jsonl`). Er is geen nieuwe call gedaan en er is niets opnieuw gedraaid.

## Kader

- Manifest `kwalificatie-manifest-v4.json`, SHA-256 `57a988de4b159065f0b5279b201973c40573e07c1d8af97258fa9bbb1cf5364a`; identiteit `0a095697705b8bfde676d8653b5317c5da701197f6b04975c0fc7c2a77f2d644`.
- Akkoord `kwalificatie-akkoord-v4.json`, SHA-256 `77e044aa6a6746033703ecf8dde5baa6d4c02e9d13252d3bc4222fcceb558ec2`; gevallen `af1ab46c…6953`.
- Anthropic `claude-opus-5`, profiel `def835-kwalificatieproef-opus5-v1`, prompt `def835-int02-prompt/2`, contract `def835-int02-assessment/1`.
- Uitsluitend fase 1 (C105, C107, C112), volgens besluit 8.
- Start 11:17:43 UTC, einde 11:18:05 UTC, looptijd 21,8 s.
- 3 inferenties en 3 telverzoeken; 0 herhalingen en 0 terugval naar een ander model.
- Grootboek: `fase_einde` met `bewijs_opgeslagen: true`, `mechanisch_geslaagd: false`, `stopreden: invalid_citation`.

## Per geval

| Geval | Verwacht | Model (verdict) | Inhoud | Citaten | Uitkomst |
|---|---|---|---|---|---|
| C105 | fail | fail (`actor_prescription`, grond: bevestigde bedoeling) | ✔ juist | ✔ geldig: kern 0–36 en bedoeling 0–23 kloppen exact | `fail`, geldig |
| C107 | review_required (insufficient_information) | insufficient_information (`unclear`, uncertainty `decisive`, één vraag) | ✔ juist, **hersteld t.o.v. v2**: in v2 koos het model `fail` en lag `start` één codepunt te laat (14 i.p.v. 13) | ✔ geldig: kern 0–86 en grond kern 13–61 kloppen exact | `review_required` / `insufficient_information`, geldig |
| C112 | pass | pass (`criterion`, grond: bevestigde bedoeling) | ✔ juist | ✘ `end` te kort geteld: kerncitaat 0–**71** i.p.v. 0–**73** (73 codepunten); bedoelingscitaat 0–**46** i.p.v. 0–**47** (47 codepunten). Beide citaten staan letterlijk in het veld. | `error` / `invalid_citation` |

Mechanische telling volgens de runner:

| Teller | Waarde |
|---|---|
| juist | 2/3 |
| juist fail | 1/1 |
| juist review_required | 1/1 |
| juist pass | 0/1 |
| false pass | 0/2 |
| kritieke false pass | 0/1 |
| false fail | 0/2 |
| citaatfout | 1/3 |
| technische fout | 0/3 |

Redenen voor niet geslaagd: `niet_volledig_uitgevoerd`, `technische_of_citaatfout` en `te_weinig_juist`.

**Inhoudelijk was fase 1 3/3 juist.** De enige afwijking is het tellen van codepunten door het model. Dat paste in het patroon van v2 en de zelfcontrole-instructie van prompt /2 hielp er niet tegen. De inhoudelijke beoordeling van de passagegronden door Chris staat in `regressie-resultaat.json` nog op `open`.

## Kosten en latentie

| Geval | Invoertokens | Uitvoertokens | Kosten |
|---|---|---|---|
| C105 | 3.644 | 263 | $0,024795 |
| C107 | 3.675 | 520 | $0,031375 |
| C112 | 3.668 | 315 | $0,026215 |
| **Totaal** | | | **$0,082385** |

Kosten zijn gemelde usage × routerprijzen ($5 per 1M invoertokens en $25 per 1M uitvoertokens). Er was geen onzekere call. Dit is geen providerfactuur.

Latentie maximaal en p95: 9.656 ms (C107).

## Stopreden

`invalid_citation` bij C112. De runner stopte na de fase volgens het manifest. Er volgden geen ontwikkel- of hold-outcalls en er is geen automatische herhaling gedaan.

## Aandachtspunt 3 (besluit 3, meerdere passages)

**Niet toetsbaar in deze 3 gevallen.** Alle drie de antwoorden hadden precies één passage, dus het patroon "een andere passage met een zelfstandig bewezen gebrek blijft fail naast een open vraag" kwam niet voor. Het punt blijft open voor de volgende proefuitkomsten.

## Vervolg

Chris koos op 07-10-2026 optie A (besluit 9): de dienst bepaalt de citaatposities en het model levert alleen citaat en veld. Dat is uitgewerkt in `../positiecorrectie-v1/uitvoeringsverslag-claude-v1.md`, met contract `/2` en prompt `/3`. Manifest v4 is daarmee achterhaald. Fase 1 wordt pas opnieuw gedraaid na Codex-review, commit/push, een offline manifest v5 en een nieuw akkoord van Chris. Het v4-bewijs blijft ongewijzigd.
