# INT-02 O2 — uitslag variatiemeting C107 (besluit 11)

7 oktober 2026. Vastgelegd door Claude uit de bewaarde meetbestanden in `live-v1/` (`herkomst.json`, `runs.jsonl`, `samenvatting.json`), `dryrun-v1/` en het runlog. Chris heeft de meting live gedraaid. Bij dit verslag is geen nieuwe call gedaan.

**Dit is geen kwalificatie.** De meting valt buiten het kwalificatieprotocol en levert geen DEF-815-claim. Manifest, akkoord en grootboek van de kwalificatie zijn niet gelezen, niet geschreven en niet als bewijs hergebruikt.

## Doel

Besluit 11 (optie C): vóór een herstel meten of de `fail` van C107 in kwalificatieproef v5 toeval is of structureel. De uitkomst helpt bij de keuze tussen een dienstregel (A) en prompt /4 (B).

## Opzet

- Script `variatiemeting.py`, SHA-256 `d05ec9590c748ec62c11b8b04507079ef2d00691d9cd1c3125578af1dca1607a`, git-HEAD `ee0434676`. Er waren geen lokaal gewijzigde ketenbestanden.
- 5 losse calls na elkaar, alleen op C107, met alleen het veld `invoer` (geen label).
- Dezelfde keten als C107 in v5: dienst, profiel `def835-kwalificatieproef-opus5-v1`, Anthropic `claude-opus-5`, prompt `def835-int02-prompt/3`, contract `def835-int02-assessment/2`, limieten per call en `use_cache=False`. De dienst bepaalt de citaatposities (besluit 9).
- **Payload gelijk aan v5.** `payload_sha256` van de meting is `6f3507192174a0a90d22c8f5d8da35a87cad1d9180f159b1f5f14f9072789866` (8.685 bytes). Dat is dezelfde waarde als bij C107 in `../goldset-freeze-v1/kwalificatieproef-v5/regressie-resultaat.json`. Alle vijf de runs melden deze hash.
- Geen automatische herhaling. Per run is precies één inferentie toegestaan.
- Harde kostenstop van US$0,50. Vóór elke call moest de besteding plus een volle reservering van $0,23 binnen die grens blijven.
- **Dry-run vooraf** (`dryrun-v1/`): 0 calls, 0 inferenties, 1 verzoek opgevangen zonder verzending, stopreden `null`.

## Resultaat per run

| Run | Uitkomst | Functie | Onzekerheid | Vraag | Grond | Uitvoertokens | Kosten | Duur (call / dienst) | Gerapporteerd model |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `review_required` / `insufficient_information` | `unclear` | `decisive` | ja | kern 13–61 | 527 | $0,031045 | 8.110 / 8.736 ms | `claude-opus-5` |
| 2 | `review_required` / `insufficient_information` | `unclear` | `decisive` | ja | kern 13–82 | 654 | $0,034220 | 8.282 / 8.492 ms | `claude-opus-5` |
| 3 | `review_required` / `insufficient_information` | `unclear` | `decisive` | ja | kern 13–82 | 513 | $0,030695 | 6.352 / 6.557 ms | `claude-opus-5` |
| 4 | `review_required` / `insufficient_information` | `unclear` | `decisive` | ja | kern 13–82 | 583 | $0,032445 | 9.074 / 9.287 ms | `claude-opus-5` |
| 5 | `review_required` / `insufficient_information` | `unclear` | `decisive` | ja | kern 13–82 | 606 | $0,033020 | 9.102 / 9.322 ms | `claude-opus-5` |

Voor alle runs geldt: 3.574 invoertokens, één passage (kern 0–86), dekking `partial`, `stop_reason` `end_turn`, geen foutcategorie en niet gecachet. Elke run gaf een ander antwoord (vijf verschillende `antwoord_sha256`). De vragen gaan steeds over hetzelfde punt: welke inhoudelijke maatstaf er achter "naar het gemotiveerde oordeel van de beoordelaar voldoende onderbouwd" zit. Run 1 legt de grond iets korter (13–61, tot "beoordelaar") dan runs 2–5 (13–82, tot en met "onderbouwd").

## Totaal

| Teller | Waarde |
|---|---|
| Runs uitgevoerd | 5/5 |
| `review_required` / `insufficient_information` | 5 |
| `fail` | 0 |
| Inferenties / telverzoeken | 5 / 5 |
| Stopreden | geen (`null`) |
| Kosten (conservatief) | $0,161425 (de som per run klopt) |
| Kostenstop | $0,50, niet bereikt |
| Looptijd | 43,1 s (runlog), waarvan 40,9 s in de calls |

Kosten zijn berekend als gemelde usage × routerprijzen ($5 per 1M invoertokens en $25 per 1M uitvoertokens). Dit is geen providerfactuur. Er was geen call zonder betrouwbare boeking.

**Geheimen.** Geen enkel uitvoerbestand in `dryrun-v1/` of `live-v1/` bevat een sleutel of een Authorization-waarde. Dat is gecontroleerd op patronen, met een positieve controle op dezelfde bestanden.

**Alert.** Het runlog toont ook bij de live meting "High Error Rate 1.000" en "Low Cache Hit Rate 0.000". Vermoedelijk komt de error-alert van het ene opgevangen verzoek uit de offline voorbereiding in hetzelfde proces. Dat gebeurde ook bij v5 (zie de v5-uitslag). In de runs zelf is 0 keer een technische fout geteld. De lage cache-hit-rate past bij `use_cache=False`. De herkomst van de alert is niet apart in de monitoringcode nagelopen.

## Duiding

Op prompt /3 met contract /2 is C107 nu 6 keer beoordeeld: 1 keer in de v5-proef en 5 keer in deze meting. Dat gaf **1 keer `fail` en 5 keer `review_required`**.

- De v5-`fail` is daarmee **geen vast patroon**. De verwachte uitkomst (`review_required`, met een open vraag over de discretionaire maatstaf) is in deze steekproef de gebruikelijke.
- Hij is ook **geen nul-kans**. In deze kleine steekproef komt hij ongeveer 1 op 6 keer voor. Met 6 waarnemingen is die verhouding erg onzeker: het 95%-betrouwbaarheidsinterval (Clopper-Pearson) loopt van ongeveer 0,4% tot 64%. Een kans van een paar procent past er net zo goed bij als een kans van een op drie.
- De vijf meetruns zijn achter elkaar gedraaid binnen ongeveer een minuut, op een ander moment dan de v5-proef. Of dat verschil iets uitmaakt, valt hieruit niet af te leiden.

C107 over alle rondes:

| Ronde | Prompt / contract | Uitkomst C107 |
|---|---|---|
| v2 | /1 / /1 | `fail` |
| v4 | /2 / /1 | `review_required` / `insufficient_information` |
| v5 | /3 / /2 | `fail` (`discretionary_decision_rule`, `non_decisive`) |
| variatiemeting (5×) | /3 / /2 | 5× `review_required` / `insufficient_information` |

De keuze tussen A (dienstregel) en B (prompt /4), of een andere vervolgstap, ligt bij Chris. Het v5-bewijs blijft ongewijzigd: v5 telt als 2/3 en deze meting verandert die telling niet.
