# INT-02 — intern beoordelingscontract `def835-int02-assessment/5`

Status: intern domeincontract.
- DEF-835 WP1, akkoord 26-09-2026.
- Versie /2 na besluit 9 van Chris (07-10-2026, optie A).
- Versie /3 na besluit 12 (07-10-2026, optie A).
- Versie /4 na besluit 16 (07-10-2026; keuzes 1B, 2A, 3A, 4A, 5A, 6A en 7A) en besluit 17 (07-10-2026, optie A), met de aanvulling van besluit 19 (08-10-2026, keuze 1A: kaal bron-ID).
- **Versie /5 na besluit 22 (08-10-2026): R1 en R2** (zie "Besluit 22"). Verder gelijk aan /4.

Norm: `def771-int02/2` (INT-02, N-breed, besluiten B1–B6).

Implementatie: `src/domain/int02/contract.py`. Prompt: `def835-int02-prompt/6` in `src/services/validation/int02_assessment_service.py`, **ongewijzigd** (besluit 22 raakt alleen de afleiding aan de dienstkant). Schema: ongewijzigd (`d3ad029e…e715`).

Tests:
- `tests/unit/domain/test_def835_int02_bronfuncties.py`: /4, besluit 17, Codex-review P1, besluit 19 (sectie K) en besluit 22 (sectie L);
- `tests/unit/domain/test_def835_int02_papertest.py`: de paper test van het ontwerp, met de varianten van G060 (kale ID's, besluit 19) en van G050, G060 en G021 (besluit 22);
- `tests/unit/validation/test_def835_int02_schemaroute.py`: schema en pin;
- de /3-regels blijven getoetst in `test_def835_int02_{contract,citaatposities,dienstregel,migratie}.py`.

Hulpcontrole buiten de suite: `…/o2/goldset-voorbereiding/bronfuncties-v1/hulp/replay_besluit22_test.py` (de 93 bewaarde antwoorden opnieuw beoordeeld).

Ontwerp: `docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/bronfuncties-ontwerp-v1.md` (met de wijzigingsnotitie van besluit 22).

Vorige versies, alle historisch en inhoudelijk ongewijzigd:
- `def835-int02-assessment/1` (`int02_assessment_contract_v1.md`);
- `def835-int02-assessment/2` (`int02_assessment_contract_v2.md`);
- `def835-int02-assessment/3` (`int02_assessment_contract_v3.md`);
- `def835-int02-assessment/4` (`int02_assessment_contract_v4.md`).

## Besluit 22: wijziging ten opzichte van /4

**Aanleiding.** De variatiemeting v9 (48 calls) en een offline wat-als over 93 bewaarde antwoorden (v8, v9 en de meting) lieten twee combinaties zien die tot een onterechte pass leidden:
- **G050:** kernvorm `discretion_form`, terwijl de bronnen `derivation`/`criterion` zeggen → `bronnen_beschrijvend` → pass;
- **G060:** B1 `unclear`, B2 `criterion` → pass, omdat onder /4 "O naast B of G telt niet" ook voor de pass gold.

**R1 — discretievorm nooit pass.** Heeft een passage kernvorm `discretion_form` en zou de dienst anders pass afleiden, dan wordt het `review_required` / `insufficient_information`:
- afleiding `discretie_nooit_pass` (`REGEL_DISCRETIE_NOOIT_PASS`);
- vaste vraag `VRAAG_DISCRETIE_ZONDER_BEDOELING` (de vraag van besluit 12: beschrijft de passage een begripskenmerk of schrijft zij de actor een afweging voor?);
- reden `REDEN_DISCRETIE_NOOIT_PASS`: `Volgens {grond} is '{passage}' een kenmerk van het begrip, maar de passage laat de uitkomst afhangen van een oordeel of afweging van een actor; dat volstaat niet voor een goedkeuring`.

**R2 — open bron naast kenmerkbron geen pass.** Heeft een passage minstens één grondbron met `unclear` en daarnaast een grondbron met `criterion` of `derivation`, en zou de dienst anders pass afleiden, dan wordt het `review_required` / `insufficient_information`:
- afleiding `onduidelijk_naast_kenmerk` (`REGEL_ONDUIDELIJK_NAAST_KENMERK`);
- vaste vraag `VRAAG_FUNCTIE`;
- reden `REDEN_ONDUIDELIJK_NAAST_KENMERK`: `Volgens {grond} is '{passage}' een kenmerk van het begrip, maar {open} laat de functie open; dat volstaat niet voor een goedkeuring`. `{open}` is de eerste open grondbron in de vaste volgorde van `grondbronnen`, met citaat als het model er een gaf.

Grondbronnen zijn alle grondbronnen van /4: bedoeling, contextitems en bronpassages.

**Plaats in de afleiding** (`_leid_af`, actor `ai`):
1. gebrek → `fail` (ongewijzigd; een afgeleide fail blijft fail);
2. een afgeleide reviewpassage → review met de eigen regel (ongewijzigd);
3. onvolledige dekking → review `onvolledige_dekking` (ongewijzigd);
4. **R1**, daarna **R2** (nieuw). R1 gaat vóór R2, ook als de R2-passage eerder in de kern staat. Binnen een regel beslist de eerste passage in de kern (op `start`, `end`);
5. besluit 17 → review `model_beslissend_onzeker` (ongewijzigd);
6. pass.

R1 en R2 werken op documentniveau, zoals besluit 17. De afgeleide passage blijft in `dienst.passages` staan als `beschrijvend` met haar eigen regel (`bronnen_beschrijvend`); alleen de status, de melding, de vraag en `dienst.afleiding` veranderen. Zo verandert er niets aan bestaande fail- of reviewdocumenten: hun melding en open punt blijven gelijk.

**Omzetting zichtbaar.** Was het modelverdict `pass` (of `fail`), dan staat de regel ook in `Beoordelingsdocument.omzetting`; het modeloordeel (verdict, onzekerheid, eigen vraag) blijft ongewijzigd in het bewaarde oordeel, zoals bij besluit 17. Bij een modelverdict `insufficient_information` is er geen omzetting (de status is gelijk).

**Alleen actor `ai`.** Een menselijke beoordelaar houdt zijn eigen verdict (2A), zoals bij besluit 12. Een menselijke pass met deze combinaties blijft pass.

**Normatieve verschuiving.** De regel "O naast B of G telt niet" (ontwerp §2.3, stap 3) vervalt voor de pass-richting. Per passage blijft de afleiding beschrijvend; alleen een pass is niet meer mogelijk. Een `discretion_form` kan onder /5 nooit meer tot pass leiden. Prijs: een terecht beschrijvende passage die het model als `discretion_form` invult (ontwerp §3.2 liet dat bij G021 open), of een terecht kenmerk naast een bron die het model `unclear` noemt, wordt een onterechte review. Dat past bij `max_false_pass` 0.

### Waarom /5 en niet /4

Besluit 19 kon binnen /4 blijven: het verruimde alleen wat geldige invoer is, en geen bestaand /4-document werd anders beoordeeld. Besluit 22 verandert de **afleiding**. Een eerder geldig /4-pass-document met een van deze combinaties (zoals G050 uit v9 en de calls 17, 22 en 46 van de variatiemeting) zou bij hercontrole onder dezelfde versienaam een andere uitkomst krijgen. `toets_actualiteit` zou zo'n document dan als niet-herleidbaar (`error`) melden: een technische fout of manipulatie, terwijl er niets mis is met het document. Dat is misleidend en niet veilig.

Daarom is de contractversie opgehoogd naar `def835-int02-assessment/5`, met **versiebewuste hercontrole**:
- een bewaard /4-document wordt volgens de /4-regels (zonder R1/R2) op integriteit getoetst en is daarna, via de bindingstoets, **historisch** (`review_required` / `historical`), nooit stil anders en nooit `error`;
- een /4-document dat als /5 wordt opgegeven, of een /4-document met de uitkomst van /5, is niet-herleidbaar (`error`);
- een nieuw document valt altijd onder /5.

In de code: `_BRONFUNCTIEVERSIES = {/4, /5}` deelt de route van bronfuncties en beslisregel; `besluit22 = contractversie == /5` schakelt R1/R2 in. Het schema verandert niet (de afleiding is aan de dienstkant); de prompt verandert niet.

## Wijziging van /4 ten opzichte van /3

Onder /3 koos het model zelf per passage één functie en één grond, en volgde de status uit het eigen verdict. Kwalificatieproef v7 fase 2 liet zien waar dat misgaat:
- vijf onterechte goedkeuringen (G042, G045, G060, G070 en G076);
- een niet herkende review in 6 van de 6 gevallen.

Onder /4 (en /5) legt de beoordelaar zich eerst per grondbron vast. **De code leidt daarna de functie en de status mechanisch af.**

### Modeluitvoer

Per passage levert de beoordelaar:
- een **`kernvorm`**: de zinsvorm van de passage zelf;
- per **grondbron** precies één **bronfunctie**, met een letterlijk citaat waar dat vereist is.

Het eigen **`verdict`** staat als laatste veld.

### Grondbronnen

`grondbronnen(invoer)` geeft de grondbronnen in vaste volgorde:
1. `bedoeling` (alleen als de bevestigde bedoeling bekend is);
2. `organisatorische_context/<i>`;
3. `juridische_context/<i>`;
4. `wettelijke_basis/<i>`;
5. `bron/<id>`.

Begrip en kern zijn geen grondbron. De dataprompt geeft de lijst mee als `"grondbronnen"`.

### De dienst beslist (2A)

Bij een model (actor `ai`) is de afgeleide status leidend.
- Wijkt die af van het eigen modelverdict, dan staat de beslissende afleidingsregel in `Beoordelingsdocument.omzetting`. Dat kan ook fail → pass zijn.
- Het modelverdict, met de eigen vraag en onzekerheid, blijft onveranderd in het oordeel.

Bij een mens (actor `human`) blijft het eigen verdict de status. Het moet dan samenhangen met de afgeleide passages, anders volgt `invalid_output`.

### Vaste vragen (4A)

Bij een door de dienst afgeleide review is de vraag vast en invoeronafhankelijk. De bronnen en citaten staan in de reden.

### Besluit 17

Een afgeleide pass vraagt ook dat de beoordelaar geen beslissende onzekerheid meldt (`uncertainty` ≠ `decisive`). Anders volgt `review_required`:
- afleiding `model_beslissend_onzeker`;
- de vaste vraag `VRAAG_FUNCTIE`.

Een afgeleid gebrek gaat voor: een fail blijft fail. Onder /5 gaan R1 en R2 vóór besluit 17.

### Codex-review P1, herreview P1-rest en herreview 2

Alleen een **betekenisdragende** grondbron (minstens één **zichtbare letter**: Unicode-categorie L*, zonder de onzichtbare letters in `ONZICHTBARE_LETTERS`) kan een functie dragen. Cijfers alleen tellen niet. De eis geldt voor het passagecitaat (`leeg`), het grondcitaat (`leeg`), de grondbron zelf (`grond_niet_herleidbaar`; mag alleen zwijgen) en de bedoeling in stap 4 (telt dan als onbekend). Details: contractdocument v4, "Codex-review P1" en "Herreview Codex: P1-rest". Ongewijzigd in /5.

### Besluit 19: kaal bron-ID (aliasregel)

Een sleutel geldt als `bron/<id>` (`_canonieke_sleutel`) als hij zelf geen grondbronsleutel is, geen gereserveerde vorm heeft (`bedoeling`, `organisatorische_context/…`, `juridische_context/…`, `wettelijke_basis/…`, `bron/…`) en precies één bron exact dat ID heeft. Elke andere afwijkende sleutel blijft `invalid_citation` / `grond_niet_herleidbaar`; een kaal ID naast zijn canonieke sleutel is `invalid_output`. Het bewaarde oordeel bevat altijd de canonieke sleutel. Details: contractdocument v4, "Besluit 19". Ongewijzigd in /5.

### Schema

`ANTWOORDSCHEMA` met pin `d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715`. Besluit 17, P1, besluit 19 en besluit 22 veranderen het schema niet.

### Ongewijzigd

Deze onderdelen werken zoals onder /2–/4:
- de invoer, binding en uitvoeringsmetadata (de binding bevat de contractversie, dus /5);
- de door de code afgeleide posities (/2);
- het passagecitaat in de kern;
- de samenhang van het eigen verdict (zonder de passagefunctie-eisen);
- de statusset, de meldingssjablonen uit synthese v5 §4 en de replayvolgorde.

### Normatieve verschuivingen (besluit 16, 17 en 22)

- **Eén bronvoorschrift draagt een fail niet meer zelfstandig.** Daarvoor is een tweede signaal nodig (3A). Een voorschrift in de kern zelf (`instruction`) blijft fail.
- **De dienst kan fail → pass omzetten** als alle bronnen "kenmerk" zeggen. Besluit 17 begrenst dit bij beslissende onzekerheid; besluit 22 bij een discretievorm (R1) of een open bron naast een kenmerkbron (R2).

## Rolverdeling

**De beoordelaar** kiest per relevante passage:
- de passage zelf;
- de kernvorm;
- per grondbron de functie en het citaat;
- de dekking, de onzekerheid en een eigen verdict.

**De code** controleert en leidt af:
- structuur, citaten, volledigheid en herleidbaarheid van de grondbronnen;
- de samenhang van het eigen verdict;
- de afleiding per passage en de status;
- binding en replay.

**De code bewijst geen semantische juistheid en geen volledigheid.** Een verkeerde invulling in één richting geeft nog steeds een "geldige" afleiding. Voorbeeld: G045 met B1 `criterion` en B2 zwijgend (zoals in v8) blijft een onterechte pass; zegt B2 `unclear`, dan vangt R2 haar sinds /5 op.

## API (`domain.int02.contract`)

Als onder /4. Nieuw of gewijzigd:

| Onderdeel | Beschrijving |
|---|---|
| `CONTRACTVERSIE` | `def835-int02-assessment/5`. De regels van /1–/4 hangen aan hun vaste versienaam, niet aan deze constante. |
| `REGEL_DISCRETIE_NOOIT_PASS`, `REGEL_ONDUIDELIJK_NAAST_KENMERK` | Besluit 22, R1 en R2; ook als `omzetting`. |
| `REDEN_DISCRETIE_NOOIT_PASS`, `REDEN_ONDUIDELIJK_NAAST_KENMERK` | Redensjablonen van R1 en R2. |
| `KERNVORMEN`, `BRONFUNCTIES`, `grondbronnen`, `ANTWOORDSCHEMA(_SHA256)`, `VRAAG_*`, overige `REGEL_*`/`REDEN_*` | Ongewijzigd t.o.v. /4. |

## Gesloten beoordelaarsuitvoer

Ongewijzigd t.o.v. /4 (zie contractdocument v4, "Gesloten beoordelaarsuitvoer", met de controlevolgorde en de samenhang van het eigen verdict).

## Beslisregel

**Richtingen.** B: `criterion`/`derivation`; G: `actor_prescription`/`discretionary_decision_rule`; N: `not_a_criterion`; O: `unclear`. `not_addressed` telt niet mee.

### Per passage (ongewijzigd t.o.v. /4)

| Stap | Situatie | Uitkomst | Regel (`afleiding`) |
|---|---|---|---|
| 1 | kernvorm `instruction` | gebrek (`actor_prescription`) | `voorschrift_in_kern` |
| 2 | B naast G of N, en de bedoeling is G of N | gebrek | `bedoeling_beslist` (1B: alleen naar gebrek) |
| 2 | B naast G of N, overig | review | `conflict` |
| 3 | B (een O ernaast verandert de passage-uitkomst niet; zie R2) | beschrijvend | `bronnen_beschrijvend` |
| 3 | G of N, met een tweede signaal | gebrek | `voorschrift_bevestigd` |
| 3 | G of N, zonder tweede signaal | review | `bronvoorschrift_niet_overgenomen` (3A) |
| 3 | alleen O | review | `bronnen_open` |
| 4 | alles zwijgt, kernvorm `no_act`, of `descriptive_act` met bekende bedoeling | beschrijvend | `alleen_kern` |
| 4 | alles zwijgt, `descriptive_act`, bedoeling onbekend | review | `geen_grond_zonder_bedoeling` (5A) |
| 4 | alles zwijgt, `discretion_form`, bedoeling onbekend | review | `discretie_zonder_bedoeling` (besluit 12) |
| 4 | alles zwijgt, overig | gebrek | `voorschrift_in_kern` |

**Discretionair gebrek.** Een gebrek is discretionair als de kernvorm `discretion_form` is, of als de eerste G-bron `discretionary_decision_rule` zegt.

### Over passages en over het geheel (actor `ai`)

1. **Gebrek** → `fail` (VN over de eerste gebrekpassage; bij een reviewpassage erbij `MELDING_OPEN_PUNT`).
2. **Reviewpassage** → `review_required`, reden en vaste vraag van de eerste reviewpassage.
3. **Onvolledige dekking** → `review_required`, `onvolledige_dekking`, `VRAAG_DEKKING`.
4. **R1 (besluit 22)** → een passage met kernvorm `discretion_form`: `review_required`, `discretie_nooit_pass`, `VRAAG_DISCRETIE_ZONDER_BEDOELING`.
5. **R2 (besluit 22)** → een passage met O naast B: `review_required`, `onduidelijk_naast_kenmerk`, `VRAAG_FUNCTIE`.
6. **Beslissende onzekerheid (besluit 17)** → `review_required`, `model_beslissend_onzeker`, `VRAAG_FUNCTIE`.
7. **Pass** → V-melding over de eerste beschrijvende passage, met haar regel.

Bij `not_applicable` blijft het eigen verdict staan (`niet_van_toepassing`). Voor een mens gelden stap 4 en 5 niet.

### Vaste vragen en redenen (4A)

Als onder /4, plus:
- `discretie_nooit_pass`: vraag `VRAAG_DISCRETIE_ZONDER_BEDOELING`, reden `REDEN_DISCRETIE_NOOIT_PASS`;
- `onduidelijk_naast_kenmerk`: vraag `VRAAG_FUNCTIE`, reden `REDEN_ONDUIDELIJK_NAAST_KENMERK`.

## Statusmapping

Als onder /4, met één rij erbij:

| Situatie | `status` | `reden` | Melding | `omzetting` (alleen actor `ai`) |
|---|---|---|---|---|
| anders pass, maar R1 of R2 | `review_required` | `insufficient_information` | O met de reden van R1/R2 en de vaste vraag | de regel, als het modelverdict `pass` of `fail` was |

## Bewaard oordeel en replay

Als onder /4: `oordeel_json` met afgeleide posities en het blok `dienst` (`afleiding`, `modelstatus`, `passages`). `Binding.contractversie` is `def835-int02-assessment/5`.

**Replay.** `toets_actualiteit` leidt een /5-document opnieuw af (met R1/R2) en een /4-document volgens /4 (zonder R1/R2). Niet-herleidbaar (`error`) zijn onder meer: een gewijzigde of ontbrekende `omzetting`, status, vraag, melding, afleiding, modelstatus of dienstfunctie; een /5-document met R1/R2-combinatie dat als pass is opgeslagen; een /4-document dat als /5 is opgegeven. Een herleidbaar /1-, /2-, /3- of /4-document is historisch.

**Replay toetst samenhang, niet echtheid** (DEF-626), zoals onder /4.

## Rapportage in de proefrunner

Ongewijzigd: de runner legt `contractversie` (nu /5), `profiel.promptversie` en `router.antwoordschema_sha256` vast in de identiteit, en per geval `afleiding`, `modelstatus`, `omzetting` en `omzettingsrichting`. Een manifest (v10) moet dus contractversie /5 en de nieuwe bestandshash van `contract.py` dragen.

## Bewijsgrenzen

- **Geen semantische modelkwaliteit.** De paper test (27/27, gesynthetiseerde modeluitvoer) toetst de beslisregel, niet het model. Voor besluit 22 is de verwachte invulling van G021 `descriptive_act` geworden (het ontwerp liet `discretion_form` of `descriptive_act` toe; R1 maakt van de discretievorm een review).
- **Wat-als is een consistentietoets.** R1 en R2 zijn mede op G050 en G060 gemaakt. Dat de offline herbeoordeling van de 93 bewaarde antwoorden precies de vier bedoelde wijzigingen geeft, bewijst consistentie, geen prestatie. Alleen de hold-out (met apart akkoord) is onafhankelijk bewijs.
- **Besluit 17 raakt mogelijke passes** (tot 13, Codex-review 07-10-2026); R1 en R2 kunnen er meer raken (onterechte review bij een verkeerd ingevulde kernvorm of een te voorzichtige `unclear`).
- **Restrisico G045.** B1 `criterion` met B2 zwijgend blijft een onterechte pass.
- **Niet geactiveerd** en **geen persistentie**: zoals onder /3 en /4.
- **Mechanische vraagcontrole.** "Precies één vraag" is een vormcontrole.
