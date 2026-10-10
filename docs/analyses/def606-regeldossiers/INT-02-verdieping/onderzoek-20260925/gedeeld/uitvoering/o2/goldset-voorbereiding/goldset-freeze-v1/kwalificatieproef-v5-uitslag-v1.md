# INT-02 O2 — uitslag kwalificatieproef v5, fase 1 (regressie)

7 oktober 2026. Vastgelegd door Claude uit de bewaarde proefbestanden in `kwalificatieproef-v5/` (`regressie-resultaat.json`, `regressie-bundel.json`, `grootboek.jsonl`, `regressie-afronding.voltooid`). Er is geen nieuwe call gedaan en er is niets opnieuw gedraaid.

## Kader

- Manifest `kwalificatie-manifest-v5.json`, SHA-256 `6655153275346ffbc95d1b1c26c8b22c5ff7f9ff521e8900793a4ecfae498fe7`; identiteit `bfc574547890f5fa0783131e94a16e4c8d33b196807fa6b3c3fbca18282768e9`.
- Akkoord `kwalificatie-akkoord-v5.json`, SHA-256 `83618a8503dbd7e41b4af5c1adafc20f8e928ce131c53b24c035590374eb3dfe`; gevallen `af1ab46c…6953`.
- Anthropic `claude-opus-5` (gerapporteerd model bij alle drie de calls), profiel `def835-kwalificatieproef-opus5-v1`, prompt `def835-int02-prompt/3`, contract `def835-int02-assessment/2`. De dienst bepaalt de citaatposities (besluit 9).
- Uitsluitend fase 1 (C105, C107, C112), volgens besluit 10.
- Start 13:26:02 UTC, einde 13:26:20 UTC, looptijd 17,6 s.
- 3 inferenties en 3 telverzoeken; 0 herhalingen en 0 terugval naar een ander model.
- Grootboek: `fase_einde` met `bewijs_opgeslagen: true`, `mechanisch_geslaagd: false`, `stopreden: null`.

## Per geval

| Geval | Verwacht | Model (verdict) | Inhoud | Citaten | Uitkomst |
|---|---|---|---|---|---|
| C105 | fail | fail (`actor_prescription`, onzekerheid `none`, grond: bevestigde bedoeling) | ✔ juist | ✔ geldig: kern 0–36 en bedoeling 0–23 | `fail`, geldig |
| C107 | review_required (insufficient_information) | fail (`discretionary_decision_rule`, onzekerheid `non_decisive`, grond: kern 13–85, geen vraag) | ✘ onjuist: het model ziet de discretionaire afweging als zelfstandig gebrek in plaats van een open vraag te stellen | ✔ geldig: kern 13–85 en grond kern 13–85 | `fail`, geldig |
| C112 | pass | pass (`criterion`, onzekerheid `none`, grond: bevestigde bedoeling) | ✔ juist | ✔ geldig: kern 0–73 en bedoeling 0–47, posities door de dienst afgeleid | `pass`, geldig |

Mechanische telling volgens de runner:

| Teller | Waarde |
|---|---|
| juist | 2/3 |
| juist fail | 1/1 |
| juist review_required | 0/1 |
| juist pass | 1/1 |
| false pass | 0/2 |
| kritieke false pass | 0/1 |
| false fail | 1/2 |
| gepaste onthouding | 0/1 |
| citaatfout | 0/3 |
| technische fout | 0/3 |

Reden voor niet geslaagd: alleen `te_weinig_juist` (2/3, vereist 3/3).

**De positiecorrectie werkt: 0 citaatfouten.** C112, dat in v4 op `invalid_citation` strandde, is nu geldig met precies de posities die in v4 te kort werden geteld (0–73 en 0–47). De enige afwijking is inhoudelijk: C107. De inhoudelijke beoordeling van de passagegronden door Chris staat in `regressie-resultaat.json` nog op `open`.

## C107 over de proefrondes

| Ronde | Prompt / contract | Uitkomst C107 |
|---|---|---|
| v2 | /1 / /1 | `fail` (en een `start` één codepunt te laat) |
| v4 | /2 / /1 | `review_required` / `insufficient_information` (juist) |
| v5 | /3 / /2 | `fail` (`discretionary_decision_rule`, `non_decisive`) |

Tussen v4 en v5 is de systeemtekst alleen gewijzigd door de positiecorrectie (citaatposities niet meer door het model); de dataprompt van C107 is gelijk. Of de wisseling tussen v4 en v5 toeval is of door de promptwijziging komt, valt uit één call per ronde niet af te leiden. Daarvoor koos Chris eerst een variatiemeting (besluit 11).

## Kosten en latentie

| Geval | Invoertokens | Uitvoertokens | Kosten |
|---|---|---|---|
| C105 | 3.543 | 269 | $0,024440 |
| C107 | 3.574 | 418 | $0,028320 |
| C112 | 3.567 | 285 | $0,024960 |
| **Totaal** | | | **$0,07772** |

Kosten zijn gemelde usage × routerprijzen ($5 per 1M invoertokens en $25 per 1M uitvoertokens). Er was geen onzekere call. Dit is geen providerfactuur.

Latentie maximaal en p95: 6.434 ms (C107).

## Alert High Error Rate

De melding "High Error Rate" komt uit de dry-run vooraf, niet uit de live fase. De dry-run vangt elk verzoek op en verstuurt niets; de monitoring van de keten (`src/monitoring/api_monitor.py`) telt die opgevangen verzoeken als mislukte calls. In de live fase zelf zijn 0 technische fouten geteld. Deze herkomst is door Chris gemeld; de proefbestanden bevatten de alert zelf niet.

## Stopreden

Geen (`null`). Alle drie de gevallen zijn uitgevoerd; de fase is afgesloten met het bewijs opgeslagen. Er volgden geen ontwikkel- of hold-outcalls en er is geen automatische herhaling gedaan.

## Aandachtspunt 3 (besluit 3, meerdere passages)

**Niet toetsbaar in deze 3 gevallen.** Alle drie de antwoorden hadden precies één passage, dus het patroon "een andere passage met een zelfstandig bewezen gebrek blijft fail naast een open vraag" kwam niet voor. Het punt blijft open voor de volgende proefuitkomsten.

## Vervolg

Chris koos op 07-10-2026 optie C (besluit 11): eerst meten of de C107-uitkomst toeval is of structureel, met 5 losse calls op C107 buiten de kwalificatie (`../variatiemeting-c107-v1/`). De uitkomst bepaalt de keuze tussen een dienstregel (A) en prompt /4 (B). Het v5-bewijs blijft ongewijzigd.
