# INT-02 O2 — uitslag kwalificatieproef v9, fase 1 en 2

8 oktober 2026. Vastgelegd door Claude uit de bewaarde proefbestanden in `kwalificatieproef-v9/`:
- `regressie-resultaat.json` en `regressie-bundel.json`;
- `ontwikkeling-resultaat.json` en `ontwikkeling-bundel.json`;
- `grootboek.jsonl` en de twee `*-afronding.voltooid`-bestanden.

Daarnaast zijn alleen de ontwikkelset (`ontwikkeling-v1.json`) en manifest v9 gelezen. Er is geen nieuwe call gedaan. De hold-out is niet gedraaid en niet ingezien.

**Bewijsstatus: consistentietoets 7A, geen onafhankelijk bewijs.** Contract /4 is ontworpen terwijl deze 27 gevallen zichtbaar waren. Een geslaagde fase 1 of 2 zegt daarom niets over de hold-out.

## Kader

- Manifest v9 `30129863…d09d`, akkoord v9 `7ef15723…9c7e`, identiteit `757bc2a1…6456`, gevallen `af1ab46c…6953` (zoals vastgelegd in de resultaatbestanden).
- Keten: `claude-opus-5` (gerapporteerd model bij alle 20 calls), prompt `def835-int02-prompt/6` (besluit 19), contract `def835-int02-assessment/4`, schema-pin `d3ad029e…e715`.
- Criteria: minimaal 21/24 juist en `max_false_pass` 0 in elke fase.
- Geen gecachete antwoorden en geen onzekere calls.

## Fase 1: regressie

**Mechanisch geslaagd: 3/3 juist, 0 omzettingen.** Grootboek: `fase_einde` met `bewijs_opgeslagen: true`, `mechanisch_geslaagd: true` en `stopreden: null`.

Start 08:04:54 UTC, looptijd 23,4 s; 3 inferenties en 3 telverzoeken.

| Geval | Label | Uitkomst | Modelstatus | Kernvorm en bronfuncties | Onzekerheid | Afleiding | Juist? |
|---|---|---|---|---|---|---|---|
| C105 | fail | `fail` | fail | `instruction`; bedoeling `actor_prescription` | none | `voorschrift_in_kern` | ✔ |
| C107 | review_required | `review_required` | review_required | `discretion_form`; alle grondbronnen zwijgen | decisive | `discretie_zonder_bedoeling` | ✔ |
| C112 | pass | `pass` | pass | `no_act`; alle grondbronnen zwijgen | non_decisive | `alleen_kern` | ✔ |

C112 is wel anders gelabeld dan in v8. Daar gaf het model de bedoeling als `criterion`, met afleiding `bronnen_beschrijvend` en onzekerheid `none`. De uitkomst is dezelfde.

Kosten US$0,11431. Latentie maximaal 9.728 ms (C107). Invoertokens 5.587–5.611 per call.

## Fase 2: ontwikkeling

**Mechanisch niet geslaagd. De fase is gestopt na 17 van de 24 gevallen.**

- **Stopreden:** `kritieke_false_pass` bij G050, het 17e geval. Dat geval heeft label `fail` en kreeg uitkomst `pass`. De runner stopt bij een kritieke false pass. G052, G042, G045, G047, G060, G070 en G076 zijn daardoor niet gedraaid.
- **Redenen van de runner:** `niet_volledig_uitgevoerd`, `kritieke_false_pass`, `onterechte_goedkeuring` en `te_weinig_juist`.
- Grootboek: `fase_einde` met `bewijs_opgeslagen: true`, `mechanisch_geslaagd: false`, `stopreden: kritieke_false_pass`.
- Start 08:06:01 UTC, looptijd 150,3 s; 17 inferenties en 17 telverzoeken.

| Teller | Waarde |
|---|---|
| juist | 15/17 |
| juist pass | 11/12 |
| juist fail | 4/5 |
| juist review_required | 0/0 (geen gedraaid) |
| false pass (onterechte goedkeuring) | 1/5 (G050) |
| kritieke false pass | 1/5 (G050) |
| false fail | 0/12 |
| gemiste overtreding | 1/5 (G050) |
| onterechte onthouding | 1/17 (G030) |
| citaatfout | 0/17 |
| technische fout | 0/17 |

**Afleidingen:** `bronnen_beschrijvend` 12, `voorschrift_bevestigd` 2, `voorschrift_in_kern` 2, `conflict` 1.

**Omzettingen (2A): 1.** `pass→review_required` bij G030, via `conflict`.

Besluit 17 (`model_beslissend_onzeker`) is nergens toegepast. Het model meldde in fase 2 nergens `decisive`.

### Per geval

Afkortingen bij de bronfuncties: `bed` = bedoeling; zwijgende grondbronnen (`not_addressed`) zijn weggelaten.

| Geval | Label | Uitkomst | Modelstatus | Kernvorm en bronfuncties | Onzekerheid | Afleiding | Omzetting | Juist? |
|---|---|---|---|---|---|---|---|---|
| G011 | pass | `pass` | pass | `no_act`; bed `criterion`, B1 `derivation` | none | `bronnen_beschrijvend` | — | ✔ |
| G015 | pass | `pass` | pass | `descriptive_act`; bed `criterion`, B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G019 | pass | `pass` | pass | `no_act`; B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G027 | pass | `pass` | pass | `no_act`; bed `derivation`, B1 `derivation` | none | `bronnen_beschrijvend` | — | ✔ |
| G030 | pass | `review_required` | pass | `descriptive_act`; B1 `criterion`, B2 `actor_prescription` | non_decisive | `conflict` | `conflict` | ✘ (onterechte onthouding) |
| G039 | pass | `pass` | pass | `descriptive_act`; bed `criterion`, B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G007 | pass | `pass` | pass | `no_act`; bed `criterion`, B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G021 | pass | `pass` | pass | `descriptive_act`; B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G037 | pass | `pass` | pass | `no_act`; bed `criterion`, B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G041 | pass | `pass` | pass | `obligation_form`; B1 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G046 | pass | `pass` | pass | `descriptive_act`; B1 `criterion`, B2 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G055 | pass | `pass` | pass | `descriptive_act`; B1 `criterion`, B2 `criterion` | none | `bronnen_beschrijvend` | — | ✔ |
| G008 | fail | `fail` | fail | `instruction`; B1 `actor_prescription` | none | `voorschrift_in_kern` | — | ✔ |
| G012 | fail | `fail` | fail | `instruction`; B1 `actor_prescription` | none | `voorschrift_in_kern` | — | ✔ |
| G036 | fail | `fail` | fail | `obligation_form`; bed `unclear`, B1 `actor_prescription` | non_decisive | `voorschrift_bevestigd` | — | ✔ |
| G048 | fail | `fail` | fail | P1 `no_act`: B1 `unclear`, B2 `criterion` · P2 `descriptive_act`: B1 `actor_prescription`, B2 `not_a_criterion` | none | `voorschrift_bevestigd` | — | ✔ |
| G050 | fail | `pass` | pass | P1 `no_act`: B1 `derivation`, B2 `derivation` · P2 `discretion_form`: B1 `criterion`, B2 `criterion` | non_decisive | `bronnen_beschrijvend` | — | ✘ (kritieke false pass) |
| G052 | fail | niet gedraaid | | | | | | — |
| G042 | review_required | niet gedraaid | | | | | | — |
| G045 | review_required | niet gedraaid | | | | | | — |
| G047 | review_required | niet gedraaid | | | | | | — |
| G060 | review_required | niet gedraaid | | | | | | — |
| G070 | review_required | niet gedraaid | | | | | | — |
| G076 | review_required | niet gedraaid | | | | | | — |

### De twee afwijkende gevallen

Bron: `kwalificatieproef-v9/ontwikkeling-resultaat.json`, het bewaarde document per geval.

**G050 (label fail, uitkomst pass, kritieke false pass).**

| Passage | Kernvorm | B1 | B2 |
|---|---|---|---|
| P1 "Bedrag van vijf procent van de kale maandhuur" | `no_act` | `derivation`: "De servicetoeslag bedraagt vijf procent van de kale maandhuur." | `derivation`: "Servicetoeslag: 12 × 5% van € 640 = € 384." |
| P2 "tenzij de huurcommissie een lager percentage passend vindt" | `discretion_form` | `criterion`: "De huurcommissie kan voor een lid een lager percentage vaststellen als zij dat gelet op de inkomenssituatie van het lid passend vindt." | `criterion`: "Voorbeeldregel voor een lid met een door de huurcommissie vastgesteld percentage van 3%" |

- Het model gaf zelf `pass`, met onzekerheid `non_decisive`. De dienst leidde ook `pass` af (`bronnen_beschrijvend`). Er is dus geen omzetting.
- Het model las de bevoegdheidszin in B1 als kenmerk (`criterion`), niet als discretionaire beslisregel. Daardoor had de `discretion_form` in de kern geen tweede signaal, en de fail ging verloren.
- In v8 gaf het model bij P2 nog B1 `discretionary_decision_rule` en B2 `criterion`. Dat was een conflict en leverde `review_required` op. De invoer is in v9 gelijk, de prompt is /6 in plaats van /5 (één extra zin over herhaling, besluit 19). Of de andere lezing komt door die zin of door variatie tussen runs, is uit één run niet af te leiden.

**G030 (label pass, uitkomst review_required, onterechte onthouding).**

| Passage | Kernvorm | B1 | B2 |
|---|---|---|---|
| "Aanbieding die de behandelaar voortzet zolang een belanghebbende beschikbaar blijft." | `descriptive_act` | `criterion`: "Overige rijen: 'vervallen aanbieding' (geen belanghebbende meer beschikbaar; …)" | `actor_prescription`: "Controleer per actieve aanbieding of er nog een belanghebbende beschikbaar is. Zet de aanbieding voort zolang dat het geval is." |

- Het model gaf zelf `pass`. De dienst zette dat om naar `review_required` via `conflict`: een beschrijvende bron naast een voorschrijvende bij dezelfde passage (besluit 16).
- In v8 las het model B2 als `criterion`. Dan volgt `pass` (juist).
- Dit is de veilige richting: geen onterechte goedkeuring.

### Kosten en latentie

| | Waarde |
|---|---|
| Kosten fase 1 | US$0,11431 (3 calls) |
| Kosten fase 2 | US$0,74410 (17 calls, gemiddeld US$0,04377 per call) |
| **Cumulatief v9 (fase 1 + 2), conservatief** | **US$0,85841** (20 calls) |
| Latentie fase 2, p95 | 16.373 ms (G041) |
| Latentie fase 2, maximaal | 16.373 ms (G041) |
| Invoertokens fase 2 | 5.744–6.185 per call |

Kosten zijn gemelde usage × routerprijzen; dit is geen providerfactuur. Er was geen onzekere call. Het cumulatieve bedrag staat ook in `ontwikkeling-resultaat.json` (`cumulatief.kosten_usd_conservatief`).

## Vergelijking v7, v8 en v9

| | v7 (prompt /4, contract /3) | v8 (prompt /5, contract /4) | v9 (prompt /6, contract /4) |
|---|---|---|---|
| Fase 1 | 3/3 | 3/3 | 3/3 |
| Fase 2 juist | 18/24 | 19/22 (gestopt na 22) | 15/17 (gestopt na 17) |
| juist pass | 12/12 | 12/12 | 11/12 |
| juist fail | 6/6 | 5/6 | 4/5 |
| juist review_required | 0/6 | 2/4 | 0/0 (geen gedraaid) |
| Onterechte passes | 5 (G042, G045, G060, G070, G076) | 1 (G045) | 1 (G050, kritiek) |
| False fail | 1 (G047) | 0 | 0 |
| Citaatfouten | 0 | 1 (G060) | 0 |
| Stopreden fase 2 | — (volledig) | `invalid_citation` (G060) | `kritieke_false_pass` (G050) |
| Kosten fase 1 + 2 | US$0,98164 (27 calls) | US$1,07407 (25 calls) | US$0,85841 (20 calls) |

- **Elke run één onterechte pass, steeds bij een ander geval.** v8 had er één bij G045 (label review). v9 had er één bij G050 (label fail, dus kritiek). G045, het doel van prompt /6, is in v9 niet bereikt. Of /6 daar werkt, is onbekend.
- **De afwijkingen zitten in de bronfuncties, niet in de afleiding.** De 15 andere gevallen die in v8 én v9 draaiden, kregen dezelfde kernvorm, dezelfde bronfuncties en dezelfde uitkomst. G050 en G030 verschillen alleen doordat het model één bron anders labelde (G050: B1 bij P2; G030: B2). De dienstregel deed in beide runs wat hij moet doen met wat het model aanleverde.
- **De richting wisselt.** G050 ging van veilig (review) naar kritiek (pass). G030 ging van juist (pass) naar veilig (review).
- G052 en de zes reviewgevallen zijn in v9 niet gedraaid. Hoe die onder /6 uitvallen, is onbekend.

## Lezing en vervolg

De kern is de variatie in het labelen van bronnen door het model. Hetzelfde geval met dezelfde invoer krijgt per run een andere bronfunctie, en de mechanische regel volgt die bronfunctie. Of dat incidenteel is of structureel, kan één run per versie niet laten zien.

Chris heeft op 8 oktober 2026 besloten (besluit 21, `../../besluit-chris-promptcorrectie-en-v3-v1.md`): eerst de variatie meten, buiten de kwalificatie. De 24 ontwikkelgevallen draaien twee keer extra met v9 (prompt /6, schema `d3ad029e…`), voor ongeveer US$2. Er wordt niets gerepareerd. Opzet en script: `../variatiemeting-v9/opdracht-en-opzet-v1.md`. Het v9-bewijs blijft ongewijzigd.

## Open: inhoudelijke beoordeling

De inhoudelijke beoordeling van passagegronden, normgrond en relevantie van de vraag staat in beide resultaatbestanden op `open`; de runner vult die niet in.
