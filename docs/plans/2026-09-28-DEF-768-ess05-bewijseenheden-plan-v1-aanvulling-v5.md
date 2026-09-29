# DEF-768 — aanvulling v5 op het plan bewijseenheden (validatie van de oordeelroute na Codex-hercontrole v4, B5/B6)

> **Aanvulling op** het plan `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md` (sha256 `4b7dec58bed0479163c72ccf75d4d3af1df9213deca7ce4a37c1ecb4fb06c0e3`) en de aanvullingen v1 (sha256 `a81e6af1314e7a01b9773c30ca87ca54069a0e333f192f370002d0a6d1324f3b`), v2 (sha256 `3c409857a29f908000c098652378507230ca4e7d29331ad8bf6c51a39c2258e2`), v3 (sha256 `3e338a78daa7334ab2441ee8847cd2e9514fd4ed2fed9fb124ce5d6f9803079d`) en v4 (sha256 `922a63a6b9bcec13bd49bace58554801eb3cd73da15d6bcb0f5cfc184b3ab120`).
>
> Plan en eerdere aanvullingen blijven ongewijzigd. Waar deze aanvulling afwijkt, gaat zij voor. Zij scherpt de **oordeelprocedure van aanvulling v4** aan (stap 1, 3 en 4). Het besluit (optie 2), de beslisregel (`EINDREGEL`), C1, C3, het orakel en de invoer blijven gelijk.
>
> **Aanleiding:** de Codex-hercontrole v4 (`logs/def768/bewijseenheden-b-v1/codex-hercontrole-result-v4.md`) bevestigt dat B2-rest-3 is opgelost, maar geeft NO-GO op HEAD `2da9690c2` met twee bevindingen in de oordeelroute:
> - **B5:** `eindoordeel` valideerde de runverzameling niet. Negen A/C/D-runs plus E1 driemaal met één oordeel gaven `geslaagd` (M-d 12, E 3/3); twaalf niet-E-runs met een leeg oordeelbestand ook. Dubbele sleutels verdwenen in een dict terwijl de telling alle exemplaren meetelde.
> - **B6:** de bestandsroute herkende E en nam scores over uit de opgeslagen metadata (`runoordeel`). Gewijzigde E-metadata bij ongewijzigde ruwe uitvoer gaf met een leeg oordeelbestand `geslaagd`.
>
> **Grenzen ongewijzigd:** geen wijziging aan de norm, `src/`, de prompt, de lokale controle, skills of config; geen budgetbesluit, geen freeze en geen netwerk- of betaalde aanroep.

---

## Aangescherpte validatie

**1. Vaste runverzameling (B5).** `bewijsscorer.controleer_runs` weigert (`OordeelfoutError`) tenzij de runs precies `PROEFSLEUTELS` zijn: A/C/D/E × herhaling 1–3, twaalf unieke sleutels. Duplicaten worden geteld vóór enige dict-omzetting; een onbekende of ontbrekende run wordt geweigerd. `eindoordeel` roept deze controle als eerste aan. Een onvolledige proef levert daardoor nooit een eindoordeel op, en dus nooit `geslaagd`.

**2. E uit de proefstructuur, niet uit de metadata (B5/B6).** E zijn de sleutels `E_SLEUTELS` (E × 1–3). Metadata die daar niet bij past, is strijdig en wordt geweigerd:
- een E-run die automatisch geslaagd of behouden zou zijn, waarvoor M-d zou tellen, of die wacht zonder `e_uitvoer_sha256`;
- een niet-E-run met een voorwaardestatus, een `e_uitvoer_sha256` of het E-wachtpunt.

**3. Drie afzonderlijke oordelen voor geslaagd.** Geslaagd vereist dat E1, E2 en E3 elk precies één oordeel `behouden` hebben, gebonden aan de hash van de eigen uitvoer. Een E-run zonder gescoorde uitvoer heeft geen hash en kan dus niet `behouden` zijn; de proef slaagt dan niet.

**4. Bestandsroute: gepinde invoer en herberekening (B6).** `r18_e_oordeel.py` (`blad` en `eindoordeel`, nieuwe optie `--invoer`, standaard `bewijsregel-invoer-v5.json`):
- **Invoerbinding.** De invoer moet de sha256 hebben die de runner pint (`R18_I_INVOER_SHA256`), het schema `/6`, precies A/C/D/E met elk 3 herhalingen, en E als enige casus met een voorwaarde. Elke prompt moet aan de huidige prompt gebonden zijn en elk orakel geldig.
- **Recordconsistentie.** Per geregistreerd callrecord: schema en fase `interpretatie`, bekende `item_id`, `herhaling` in 1–3, `sleutel` = `interpretatie|<item_id>|<herhaling>`, `invoerbestand_sha256` = de pin, `geval_sha256`, prompt en orakel gelijk aan die van de casus, precies één reservering met hetzelfde `seq` en `poging` = sleutel, en de sha256 van de ruwe tekst. Dubbele sleutels en dubbele `seq` worden geweigerd.
- **Herberekening.** Score en runoordeel worden met de huidige scorer herberekend uit de gehashte ruwe tekst (geparst zoals de dienst, ontsnapt zoals de runner), en alleen als de dienst de uitvoer parste. Wijkt de opgeslagen geparste interpretatie, score of het opgeslagen runoordeel af, dan is de metadata strijdig en wordt geweigerd. De runs voor `eindoordeel` zijn de herberekende, niet de opgeslagen.
- **Niets geschreven.** Bij elke weigering wordt niets geschreven; ook het beoordelingsblad wordt alleen voor een volledige, consistente proef gemaakt.

## Correctie op aanvulling v4

Aanvulling v4, oordeelprocedure stap 4, zegt: "De sha256 van de ruwe uitvoer in elk callrecord wordt opnieuw berekend; een gewijzigd record wordt geweigerd." Dat was **te ruim**: alleen een gewijzigde ruwe tekst werd geweigerd, niet gewijzigde score- of oordeelmetadata (B6), en de runverzameling werd niet gecontroleerd (B5). Met deze aanvulling wordt een record geweigerd als de ruwe tekst, de geparste interpretatie, de score, het runoordeel of de binding aan invoer en casus niet klopt.

## Invoer

Geen nieuwe invoerversie: het orakel en de invoer zijn ongewijzigd. `bewijsregel-invoer-v5.json` (sha256 `b2c3c34dbe91d0c8b49746d8438793f3994b098620700ea4cbfe9f4a7619d8c4`) blijft de gepinde R18A-invoer.

## Restrisico's

- **Consistent vervalste records.** De route controleert alleen of de records onderling, met de gepinde invoer en met de huidige scorer consistent zijn. Een opzettelijk nagemaakt record met eigen, unieke `seq`, juiste sleutel en herberekend consistente metadata (bijvoorbeeld de ruwe tekst van E1 als E2) wordt niet herkend. Daarvoor zou een controle tegen het R18-grootboek nodig zijn; die zit niet in deze route.
- **Verlagen blijft mogelijk.** Wie de geparste interpretatie uit een record weglaat en score en runoordeel consequent op "geen interpretatie" zet, maakt de run slechter, nooit beter: zo'n E-run heeft geen hash en kan niet `behouden` zijn.
- **Scorerversie.** De herberekening gebruikt de huidige scorer. Wijzigt die na de proef, dan weigert de route oude records als strijdig; het eindoordeel moet dan met de scorer van de proef worden bepaald.
- **Onvolledige proef.** Een proef die stopte (kritiek, M-d-afkeur of technisch) krijgt geen beoordelingsblad en geen eindoordeel; haar automatische proefoordeel blijft gelden.

## Wat ongewijzigd blijft

- Besluit optie 2, `EINDREGEL`, de oordeelstatussen en het oordeelbestand (schema `def768-ess05-e-oordeel/1`).
- C1 en C3, het runoordeel en het proefoordeel.
- Budget: 18 aanroepen, cumulatief 399 → maximaal 417 binnen 427.
- R18B: `lokale-invoer-v1.json` (sha `a36172a0…5b81`).
- Contract `ess05-bewijsregels/6`, prompt /4.
- Uitvoering: geen retry, geen cache. Een betaalde stap alleen na een "go" van Chris met een eigen budgetbesluit, en pas nadat Codex deze correctie heeft gecontroleerd.
