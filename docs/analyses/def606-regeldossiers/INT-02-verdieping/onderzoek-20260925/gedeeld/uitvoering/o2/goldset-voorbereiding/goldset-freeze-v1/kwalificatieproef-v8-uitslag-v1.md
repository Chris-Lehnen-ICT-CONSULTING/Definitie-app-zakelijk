# INT-02 O2 — uitslag kwalificatieproef v8, fase 1 en 2

8 oktober 2026. Vastgelegd door Claude uit de bewaarde proefbestanden in `kwalificatieproef-v8/`:
- `regressie-resultaat.json` en `regressie-bundel.json`;
- `ontwikkeling-resultaat.json` en `ontwikkeling-bundel.json`;
- `grootboek.jsonl` en de twee `*-afronding.voltooid`-bestanden.

Daarnaast is alleen de ontwikkelset (`ontwikkeling-v1.json`) gelezen. Er is geen nieuwe call gedaan. De hold-out is niet gedraaid en niet ingezien.

**Bewijsstatus: consistentietoets 7A, geen onafhankelijk bewijs.** Contract /4 is ontworpen terwijl deze 27 gevallen zichtbaar waren. Een geslaagde fase 1 of 2 zegt daarom niets over de hold-out.

## Kader

- Manifest v8 `d5a4de42…f8fa`, akkoord v8 `00a86b7f…80bb`, identiteit `86daaad9…b2f7`, gevallen `af1ab46c…6953` (zoals vastgelegd in de resultaatbestanden).
- Keten: `claude-opus-5` (gerapporteerd model bij alle 25 calls), prompt `def835-int02-prompt/5`, contract `def835-int02-assessment/4` (bronfuncties, besluit 16 en 17), schema-pin `d3ad029e…e715`.
- Criteria: minimaal 21/24 juist en `max_false_pass` 0 in elke fase.
- Geen gecachete antwoorden en geen onzekere calls.

## Fase 1: regressie

**Mechanisch geslaagd: 3/3 juist, 0 omzettingen.** Grootboek: `fase_einde` met `bewijs_opgeslagen: true`, `mechanisch_geslaagd: true` en `stopreden: null`.

Start 06:59:00 UTC, looptijd 22,0 s; 3 inferenties en 3 telverzoeken.

| Geval | Label | Uitkomst | Modelstatus | Kernvorm en bronfuncties | Onzekerheid | Afleiding | Juist? |
|---|---|---|---|---|---|---|---|
| C105 | fail | `fail` | fail | `instruction`; bedoeling `actor_prescription` | none | `voorschrift_in_kern` | ✔ |
| C107 | review_required | `review_required` | review_required | `discretion_form`; alle grondbronnen zwijgen | decisive | `discretie_zonder_bedoeling` | ✔ |
| C112 | pass | `pass` | pass | `no_act`; bedoeling `criterion` | none | `bronnen_beschrijvend` | ✔ |

Kosten US$0,11261. Latentie maximaal 7.836 ms. Invoertokens 5.487–5.511 per call; in v7 was dat 4.842–4.873. Het verschil komt van de langere prompt /5 en het /4-schema.

## Fase 2: ontwikkeling

**Mechanisch niet geslaagd. De fase is gestopt na 22 van de 24 gevallen.**

- **Stopreden:** `invalid_citation` bij G060, het 22e geval. De runner stopt bij een citaatfout. G070 en G076 zijn daardoor niet gedraaid.
- **Redenen van de runner:** `niet_volledig_uitgevoerd`, `technische_of_citaatfout`, `onterechte_goedkeuring` en `te_weinig_juist`.
- Grootboek: `fase_einde` met `bewijs_opgeslagen: true`, `mechanisch_geslaagd: false`, `stopreden: invalid_citation`.
- Start 06:59:27 UTC, looptijd 188,8 s; 22 inferenties en 22 telverzoeken.

| Teller | Waarde |
|---|---|
| juist | 19/22 |
| juist pass | 12/12 |
| juist fail | 5/6 |
| juist review_required | 2/4 |
| false pass (onterechte goedkeuring) | 1/10 (G045) |
| kritieke false pass | 0/6 |
| false fail | 0/16 |
| gemiste overtreding | 1/6 (G050) |
| citaatfout | 1/22 (G060) |
| technische fout | 0/22 |

**Afleidingen:** `bronnen_beschrijvend` 13, `voorschrift_in_kern` 3, `voorschrift_bevestigd` 2, `conflict` 2, `bronvoorschrift_niet_overgenomen` 1. Bij G060 is er geen afleiding (foutdocument).

**Omzettingen (2A): 3.**
- `pass→review_required`: 2 (G042 via `conflict`, G047 via `bronvoorschrift_niet_overgenomen`);
- `fail→review_required`: 1 (G050 via `conflict`).

Besluit 17 (`model_beslissend_onzeker`) is nergens toegepast. Het model meldde in fase 2 nergens `decisive`.

### Per geval

Afkortingen bij de bronfuncties: `bed` = bedoeling; zwijgende grondbronnen (`not_addressed`) zijn weggelaten.

| Geval | Label | Uitkomst | Modelstatus | Kernvorm en bronfuncties | Onzekerheid | Afleiding | Omzetting | Juist? |
|---|---|---|---|---|---|---|---|---|
| G011 | pass | `pass` | pass | `no_act`; bed `criterion`, B1 `derivation` | none | `bronnen_beschrijvend` | — | ✔ |
| G015 | pass | `pass` | pass | `descriptive_act`; bed `criterion`, B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G019 | pass | `pass` | pass | `no_act`; B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G027 | pass | `pass` | pass | `no_act`; bed `derivation`, B1 `derivation` | none | `bronnen_beschrijvend` | — | ✔ |
| G030 | pass | `pass` | pass | `descriptive_act`; B1 `criterion`, B2 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G039 | pass | `pass` | pass | `descriptive_act`; bed `criterion`, B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G007 | pass | `pass` | pass | `no_act`; bed `criterion`, B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G021 | pass | `pass` | pass | `descriptive_act`; bed `criterion`, B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G037 | pass | `pass` | pass | `no_act`; bed `criterion`, B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G041 | pass | `pass` | pass | `obligation_form`; B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G046 | pass | `pass` | pass | `descriptive_act`; B1 `criterion`, B2 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G055 | pass | `pass` | pass | `descriptive_act`; B1 `criterion`, B2 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G008 | fail | `fail` | fail | `instruction`; B1 `actor_prescription` | none | `voorschrift_in_kern` | — | ✔ |
| G012 | fail | `fail` | fail | `instruction`; B1 `actor_prescription` | none | `voorschrift_in_kern` | — | ✔ |
| G036 | fail | `fail` | fail | `obligation_form`; bed `unclear`, B1 `actor_prescription` | non_decisive | `voorschrift_bevestigd` | — | ✔ |
| G048 | fail | `fail` | fail | P1 `no_act`: B1 `unclear`, B2 `criterion` · P2 `descriptive_act`: B1 `actor_prescription`, B2 `not_a_criterion` | none | `voorschrift_bevestigd` | — | ✔ |
| G050 | fail | `review_required` | fail | P1 `no_act`: B1 `derivation`, B2 `derivation` · P2 `discretion_form`: B1 `discretionary_decision_rule`, B2 `criterion` | non_decisive | `conflict` | `conflict` | ✘ |
| G052 | fail | `fail` | fail | `instruction`; B1 `actor_prescription`, B2 `criterion` | none | `voorschrift_in_kern` | — | ✔ |
| G042 | review_required | `review_required` | pass | `descriptive_act`; B1 `actor_prescription`, B2 `criterion` | non_decisive | `conflict` | `conflict` | ✔ |
| G045 | review_required | `pass` | pass | `descriptive_act`; B1 `criterion` | none | `bronnen_beschrijvend` | — | ✘ (false pass) |
| G047 | review_required | `review_required` | pass | P1 `no_act`: B1 `criterion` · P2 `descriptive_act`: B1 `actor_prescription` | non_decisive | `bronvoorschrift_niet_overgenomen` | `bronvoorschrift_niet_overgenomen` | ✔ |
| G060 | review_required | `error` | — | `descriptive_act`; sleutels "B1" (`actor_prescription`) en "B2" (`criterion`) | non_decisive | — | — | ✘ (citaatfout) |
| G070 | review_required | niet gedraaid | | | | | | — |
| G076 | review_required | niet gedraaid | | | | | | — |

Bij G060 staat de modelvorm alleen in de bundel. Het document is een foutdocument (`invalid_citation` / `grond_niet_herleidbaar`) en bewaart geen oordeel.

### Kosten en latentie

| | Waarde |
|---|---|
| Kosten fase 1 | US$0,11261 (3 calls) |
| Kosten fase 2 | US$0,96146 (22 calls, gemiddeld US$0,04370 per call) |
| **Cumulatief v8 (fase 1 + 2), conservatief** | **US$1,07407** (25 calls) |
| Latentie fase 2, p95 | 13.818 ms (G046) |
| Latentie fase 2, maximaal | 17.975 ms (G060) |

Kosten zijn gemelde usage × routerprijzen; dit is geen providerfactuur. Er was geen onzekere call.

## Diagnose (Codex, offline replay, bevestigd)

**G060: citaatfout door de bronsleutel, niet door het citaat.**
- Het model schreef de sleutels "B1" en "B2" in plaats van "bron/B1" en "bron/B2".
- Daardoor faalde `sleutel in bronnen` (`contract.py` r.1127 op HEAD `c9e75ecb2`) met `grond_niet_herleidbaar`, en stopte de runner de fase.
- De citaten zelf waren exact, uniek en betekenisdragend.
- Met de juiste sleutels geeft de replay `review_required` via `conflict` (B1 `actor_prescription` tegenover B2 `criterion`). Dat is het juiste label.

**G045: onterechte pass.**
- Het model las B1 als `criterion`. B1 herhaalt alleen dezelfde dubbelzinnige "is te"-zin als de kern ("is … binnen tien werkdagen in te dienen").
- Het ontwerp (`bronfuncties-ontwerp-v1.md` r.255) verwacht B1 `unclear`. Dan volgt `review_required` via `bronnen_open`.
- Dit is het restrisico dat het ontwerp en het contractdocument v4 al noemden: de regel kan geen grond verzinnen die het model niet geeft.

**G050: label fail, uitkomst review_required.**
- Bij P2 gaf het model B1 `discretionary_decision_rule` en B2 `criterion`. Dat is een bronconflict, dus volgt review.
- Het ontwerp noemde precies dit als gevoeligheid ("B2 C bij P2 → conflict → review").
- Dit is de veilige richting: geen onterechte goedkeuring. Er is niets aan gedaan.

**Controle met de code na besluit 19 (offline, 8 oktober 2026).** Claude heeft de 22 ruwe antwoorden opnieuw beoordeeld met de aliasregel (`../bronfuncties-v1/besluit19-replay-v8.log`). Alleen G060 verandert, van `error` naar `review_required` / `conflict`. De andere 21 houden hun v8-status, ook G045 (`pass`) en G050 (`review_required`). Dit is een herbeoordeling van bewaarde antwoorden, geen nieuwe run.

## Vergelijking met v7

| | v7 (prompt /4, contract /3) | v8 (prompt /5, contract /4) |
|---|---|---|
| Fase 1 | 3/3 | 3/3 |
| Fase 2 juist | 18/24 | 19/22 (gestopt na 22) |
| juist pass | 12/12 | 12/12 |
| juist fail | 6/6 | 5/6 |
| juist review_required | 0/6 | 2/4 |
| Onterechte passes | 5 (G042, G045, G060, G070, G076) | 1 (G045) |
| False fail | 1 (G047) | 0 |
| Citaatfouten | 0 | 1 (G060) |
| Kosten fase 1 + 2 | US$0,98164 (27 calls) | US$1,07407 (25 calls) |

- **Wat beter werd.** De onterechte passes gingen van 5 naar 1. G042 en G047 zijn nu juist, en wel via een zichtbare omzetting van de dienst: het model zelf gaf nog `pass`.
- **G060** was in v7 een onterechte pass. Het model vulde het conflict nu wel goed in, maar de fase stopte op de sleutelvorm.
- **G047** was in v7 een false fail en is nu juist.
- **G050** ging van juist (fail) naar review. Dat is de prijs van de mechanische conflictregel.
- **G045** blijft een onterechte pass, met hetzelfde mechanisme als in v7 (letterlijke herhaling gelezen als kenmerk).
- G070 en G076 zijn niet gedraaid. Of de verbetering daar standhoudt, is onbekend.

## Besluit en vervolg

Chris heeft op 8 oktober 2026 besloten (besluit 19, `../../besluit-chris-promptcorrectie-en-v3-v1.md`):
1. **G060, keuze A:** de dienst accepteert onder /4 een kaal bron-ID ("B1") als "bron/B1", als dat eenduidig is. Het bewaarde document blijft canoniek.
2. **G045, keuze A:** de prompt krijgt één algemene regel: een grondbron die alleen dezelfde formulering herhaalt, is geen bewijs voor `criterion`. Dat wordt prompt `/6`.

Daarna volgen manifest v9 (offline) en opnieuw fase 1 en 2, met een apart akkoord. Het v8-bewijs blijft ongewijzigd.

## Open: inhoudelijke beoordeling

De inhoudelijke beoordeling van passagegronden, normgrond en relevantie van de vraag staat in beide resultaatbestanden op `open`; de runner vult die niet in.
