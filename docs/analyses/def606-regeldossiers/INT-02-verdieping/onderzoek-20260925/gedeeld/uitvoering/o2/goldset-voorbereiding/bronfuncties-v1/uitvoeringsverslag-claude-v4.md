# Uitvoeringsverslag v4: besluit 22 (R1 + R2, contract /5)

DEF-835 · INT-02 O2 · 08-10-2026 · Claude. Werkboom op branch `feature/DEF-835-int02-o2`, HEAD `258d26d89`.

**Alles staat nog ongecommit.** Er zijn geen API- of netwerkcalls gedaan, `.env` is niet gelezen en er zijn geen hold-outbestanden geopend (de replaytest weigert elk pad met holdout/hold-out/hold_out vóór het openen). Er staat geen `print()` in `src/`. Er is niets verwijderd. Het al aanwezige ongecommitte werk (uitslag v9, besluit 21, variatiemeting v9 met live-v1 en `test_def835_int02_variatiemeting_v9.py`) is niet aangeraakt; besluit 22 is alleen achter besluit 21 toegevoegd.

De sessie werd halverwege afgebroken door een netwerkonderbreking. Daarna is de stand met `git status`/`git diff` vastgesteld en afgemaakt; de mutatieruns en de `-k`-run zijn na de onderbreking (opnieuw) gedraaid.

## 1. Wijzigingen per bestand

**`src/domain/int02/contract.py`**
- r.1: moduledocstring noemt `/5`; r.26–35: R1, R2 en de volgorde in de docstring; r.79–80: /4 is bij replay historisch.
- r.123–141: versies. `_CONTRACTVERSIE_V5` (r.127), `CONTRACTVERSIE = /5` (r.128), `_CONTRACTVERSIE_V4` als vorige versie, `_BRONFUNCTIEVERSIES = {/4, /5}` (r.138) en `_BEKENDE_CONTRACTVERSIES` daarop gebaseerd.
- r.230–233: `REGEL_DISCRETIE_NOOIT_PASS = "discretie_nooit_pass"` en `REGEL_ONDUIDELIJK_NAAST_KENMERK = "onduidelijk_naast_kenmerk"`.
- r.251–252: vaste vragen in `_VRAAG_BIJ_REGEL`: R1 → `VRAAG_DISCRETIE_ZONDER_BEDOELING` (de vraag van besluit 12, die precies de R1-twijfel benoemt), R2 → `VRAAG_FUNCTIE`.
- r.280–290: redensjablonen `REDEN_DISCRETIE_NOOIT_PASS` en `REDEN_ONDUIDELIJK_NAAST_KENMERK`.
- r.1381–1416: nieuw `_geen_pass_besluit22(oordeel, dienst, invoer)`: geeft (regel, reden) als R1 of R2 een pass blokkeert.
- r.1419–1435: `_leid_af` krijgt parameter `besluit22`; docstring.
- r.1518–1531: **de plek**: na gebrek (r.1498), na de afgeleide reviewpassage en onvolledige dekking (`open_punt`), vóór besluit 17 en de pass. Alleen bij `besluit22` en actor `ai`.
- r.1731 en r.1737: `_beoordeel` gebruikt de bronfunctieroute voor /4 én /5; `besluit22 = contractversie == /5`.
- r.1858: `_herleidbaar` behandelt /4 en /5 gelijk (zonder `dienst` en posities terug naar modelvorm, daarna opnieuw afleiden volgens de eigen versie).
- Docstrings van `Beoordelingsdocument`, `_beoordeel` en `_herleidbaar` bijgewerkt.

**Gekozen plek, precies.** Volgorde in `_leid_af` (actor `ai`):
1. gebrek → fail;
2. afgeleide reviewpassage → review met de eigen regel;
3. dekking ≠ `complete` → `onvolledige_dekking`;
4. **R1**: de eerste passage in de kern (op `start`, `end`) met kernvorm `discretion_form`;
5. **R2**: de eerste passage in de kern met een `unclear`-grondbron naast een `criterion`/`derivation`-grondbron;
6. besluit 17 (`uncertainty = decisive`);
7. pass.

R1 gaat altijd vóór R2, ook over passages heen. R1/R2 werken op documentniveau, zoals besluit 17: de dienstpassage blijft `beschrijvend` / `bronnen_beschrijvend`. Daardoor veranderen geen bestaande fail- of reviewmeldingen (geen extra open punt in een VN-melding). Een mens houdt zijn eigen verdict (2A, net als besluit 12).

**Tests**
- `tests/unit/domain/test_def835_int02_bronfuncties.py`:
  - r.60: `V5`;
  - r.182: versietest naar /5 (/3 en /4 blijven herleidbaar);
  - r.260: `test_geldige_uitvoer_wordt_geaccepteerd` verwacht /5;
  - r.625: `test_stap3_open_bron_naast_beschrijvende_bron_…` verwacht nu review (R2), met de passage nog beschrijvend (was pass);
  - r.1146: serialisatietest verwacht /5;
  - r.2009–2430: nieuwe sectie L (19 testfuncties, 40 testgevallen). Zie §2.
- `tests/unit/domain/test_def835_int02_papertest.py`:
  - r.85–89: G021 verwacht nu `descriptive_act` (het ontwerp liet beide kernvormen toe; met `discretion_form` geeft R1 review);
  - r.344: `test_g045_…`: met B2 `unclear` nu review (R2), met B2 zwijgend (zoals v8) nog steeds pass; versie /5;
  - r.374, r.383, r.390: nieuwe varianten G050 (R1), G060 (R2) en G021 als discretievorm (de prijs van R1).
- `tests/unit/validation/test_def835_int02_modelproef.py` r.1758–1771: identiteit bindt contract /5 (testnaam `…contract_vijf…`).
- `tests/unit/validation/test_def835_int02_variatiemeting.py` r.257–259 en r.365: het C107-meetscript legt de actieve versie vast, nu /5.

**Mutatieplugin** `mutatie/mutatie_plugin.py` r.147–162: `r1_weg_b22`, `r2_weg_b22` en extra `r12_ook_onder_v4_b22` (R1/R2 ook onder /4).

**Hulpbestanden** (niet in de suite):
- `hulp/replay_besluit22_test.py`: de wat-als als test (§3);
- `hulp/besluit22_inventaris.py`: inventaris van de bewaarde antwoorden, gebruikt bij de opzet.

**Documenten**
- `docs/architectuur/contracts/int02_assessment_contract_v5.md` (nieuw; v4 ongewijzigd als historische versie);
- `goldset-voorbereiding/bronfuncties-ontwerp-v1.md`: wijzigingsnotitie besluit 22 bovenaan, twee commentaarregels in §2.3 en de G021-rij in §3.2;
- `o2/besluit-chris-promptcorrectie-en-v3-v1.md` r.398 e.v.: besluit 22;
- `goldset-voorbereiding/variatiemeting-v9/uitslag-v1.md` (nieuw);
- `o2/processtatus-uitvoering-v16.md` (nieuw).

**Niet gewijzigd:** prompt en dienst (`int02_assessment_service.py`), schema, runner, `runtime_contract.py`.

## 2. Contractversie: opgehoogd naar /5

R1/R2 veranderen de **afleiding**, niet alleen wat geldige invoer is (anders dan besluit 19). Een eerder geldig /4-pass-document met zo'n combinatie (bijvoorbeeld G050 uit v9, calls 17, 22 en 46 van de meting) zou bij hercontrole onder dezelfde versienaam niet meer exact volgen: `toets_actualiteit` zou het als `error` melden, alsof het gemanipuleerd is. Daarom /5 met versiebewuste hercontrole:
- een /4-document wordt volgens /4 (zonder R1/R2) getoetst en is daarna historisch;
- een /4-document met de uitkomst van /5, of een /4-document dat als /5 wordt opgegeven, is `error`;
- een /5-document met R1/R2 is bij hercontrole het bewaarde oordeel; manipulatie (omzetting weg, status pass, afleiding terug) is `error`.

Het schema verandert niet (de afleiding zit aan de dienstkant). De prompt verandert niet.

## 3. Testuitkomsten

| Meting | Uitkomst | Log |
|---|---|---|
| Nulmeting vóór de wijziging (`-k "def835 or int02"` tests/unit) | 1509 geslaagd, 11 overgeslagen | `besluit22-nulmeting.log` |
| Rood, vóór de implementatie | 32 gefaald, alle bedoeld: 24 in bronfuncties (sectie L, versie, R2 in stap 3), 4 papertest, 1 replay, 1 modelproef, 2 variatiemeting (C107) | `besluit22-rood.log` |
| Gericht (bronfuncties, papertest, dienstregel, prompt, schemaroute, modelproef, variatiemeting, variatiemeting v9, dienst) | 1035 geslaagd, 11 gefaald (zie §4) | `besluit22-groen-0-gericht.log` |
| `-k "def835 or int02"` tests/unit | 1538 geslaagd, 11 overgeslagen, 11 gefaald (dezelfde 11) | `besluit22-groen-1-def835-int02.log` |
| INT-03 / ESS-03 | 786 geslaagd | `besluit22-groen-2-int03-ess03.log` |
| ruff (src, tests, eigen hulpbestanden, plugin) | All checks passed | `besluit22-ruff.log` |
| black `--check` (idem) | 1010 bestanden ongewijzigd | `besluit22-black.log` |
| Papieren toets | 92 geslaagd: 27/27 met 6/6 review, plus de varianten | `besluit22-papertest.log` |
| Mutatiecontrole | 24/24 gedood, nulmeting 610/610; `r1_weg_b22` 13, `r2_weg_b22` 14, `r12_ook_onder_v4_b22` 4 | `besluit22-mutatie.log`, `mutatie/resultaten/besluit22-*.xml` |
| Wat-als-replay (93 bewaarde antwoorden) | precies de vier wijzigingen; besluit-19-replay van v8 nog groen | `besluit22-replay-watals.log` |

**Sectie L** dekt onder meer:
- R1 met `criterion`, `derivation` en twee kenmerkbronnen → review; met een gebrek (gebrekpassage, discretiebron, bedoeling beslist, alleen kern met bekende bedoeling) → fail;
- R2 met O+C, O-met-citaat+C, O+D, C-dan-O, context-O, bedoeling-C → review; alleen O blijft `bronnen_open`; alleen C blijft pass; fail blijft fail; een conflict gaat voor;
- de volgorde (bestaande reviewgronden vóór R1, R1 en R2 vóór besluit 17, R1 vóór R2), de omzetting (wel bij modelverdict pass/fail, niet bij `insufficient_information`), de exacte melding, en een mens die zijn pass houdt;
- de hercontrole (/5 consistent, /4 historisch, vervalsingen `error`).

**Afwijking in de rode stap.** `test_geldige_uitvoer_wordt_geaccepteerd` pint de actuele contractversie. Die had ik in de rode stap niet aangepast; hij werd pas rood na de versiewissel en is daarna op /5 gezet. Verder: in de eerste rode run stond in de replaytest bij G060 v8 `omzetting None`; de bewaarde waarde is `conflict` (modelverdict pass). Die verwachting is vóór de implementatie gecorrigeerd.

**Cwd.** De containertests zijn cwd-afhankelijk. Een `-k`-run vanuit de logmap gaf daardoor 4 extra fouten; de geldige run is die vanuit de werkboomroot (tabel).

## 4. De 11 fouten: het v9-meetscript weigert de nieuwe keten

Alle 11 zitten in `tests/unit/validation/test_def835_int02_variatiemeting_v9.py` (ongecommit, niet door mij gewijzigd) met oorzaak `ketenbestand_afwijkend`. `variatiemeting_v9.py` controleert de bestandshashes van de keten tegen manifest v9, en `contract.py` wijkt nu bewust af (`1ee52782…` → `195cb777…`). Dat is het bedoelde gedrag van de bewaking: de meting hoort bij v9 en is afgerond. De tests draaien echter met de echte bestanden en worden daardoor rood. Dit vraagt een keuze van Chris; ik heb het bestand bewust laten staan:
- (a) de tests pinnen de ketenhashes via monkeypatch (alleen het testbestand verandert), of
- (b) het script en de tests als historisch markeren (bijv. met een skip zodra `contract.py` niet meer gelijk is aan v9, met reden).

## 5. Wat-als-replay

`hulp/replay_besluit22_test.py` beoordeelt elk ruw antwoord opnieuw met de huidige code en vergelijkt (status, afleiding, omzetting) met wat bewaard is: v8 en v9 regressie en ontwikkeling (22 + 3 + 17 + 3) en de 48 calls van de meting (invoer uit `ontwikkeling-v1.json`), samen 93.

Gewijzigd:

| Antwoord | Bewaard | Nu |
|---|---|---|
| v9 ontwikkeling G050 | pass, `bronnen_beschrijvend` | review_required, `discretie_nooit_pass`, omzetting idem |
| meting h1 call 17 G050 | pass, `bronnen_beschrijvend` | review_required, `discretie_nooit_pass`, omzetting idem |
| meting h1 call 22 G060 | pass, `bronnen_beschrijvend` | review_required, `onduidelijk_naast_kenmerk`, omzetting idem |
| meting h2 call 46 G060 | pass, `bronnen_beschrijvend` | review_required, `onduidelijk_naast_kenmerk`, omzetting idem |
| v8 ontwikkeling G060 | error | review_required, `conflict` (besluit 19, al bekend) |

Verder geen enkele wijziging. G045 uit v8 blijft pass (B1 `criterion`, B2 zwijgt): de bekende restfout. Dit is een consistentietoets: de regels zijn mede op G050/G060 gemaakt.

## 6. Hashes

- **ANTWOORDSCHEMA:** `d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715`, **ongewijzigd** (gepind in `test_def835_int02_schemaroute.py` r.76, groen).
- **Systeemprompt /6:** `a8f701ac3ec262f44efa3415d34e4931f4b637eb4d430b33aa8694d77e89d8e7`, **ongewijzigd** (gepind in `test_def835_int02_dienstregel.py` r.103 en `test_def835_int02_schemaroute.py` r.93, groen; de dienstmodule is niet gewijzigd).
- **Bestanden** (stand van dit verslag, ongecommit), tegen manifest v9:
  - `src/domain/int02/contract.py`: `195cb777a33eb8208a5eb30a21b436d3ecfa2a78e321d27241b50713e22b6d97` (v9: `1ee52782…f94cf`, **gewijzigd**);
  - `src/services/validation/int02_assessment_service.py`: `3a69a4d8…1684`, ongewijzigd;
  - `src/toetsregels/runtime_contract.py`: `b520dcb9…de4d`, ongewijzigd;
  - `scripts/analysis/def835_int02_modelproef.py`: `4bd076f3…e964`, ongewijzigd.

## 7. Wat nodig is voor manifest v10

**Identiteit:**
- `contractversie`: `def835-int02-assessment/4` → **`def835-int02-assessment/5`**;
- `profiel.promptversie`: `def835-int02-prompt/6`, ongewijzigd;
- `router.antwoordschema_sha256`: `d3ad029e…e715`, ongewijzigd;
- bestandshash van `contract.py` (definitief na commit; nu `195cb777…`);
- `proefmap` `kwalificatieproef-v10`, `identiteit_sha256`, `aangemaakt`.

**Ongewijzigd verwacht:** systeemprompt- en payloadhashes per geval (de dataprompt bevat geen contractversie; in de offline dry-run controleren), gevallen (`af1ab46c…6953`), criteria (21/24, `max_false_pass` 0), model, SDK, limieten en prijzen.

**Gitleaks:** waarschijnlijk dezelfde bevinding als bij v8/v9 (r113, SHA-256 van `src/utils/async_api.py`) → uitzondering 20, mechanisch afgeleid van 19.

**Open punten:**
1. De 11 rode tests van het v9-meetscript (§4): keuze (a) of (b) van Chris vóór de commit, anders blijft de def835-selectie rood.
2. Verouderde commentaarregels die nog `/4` noemen in `int02_assessment_service.py` r.1, `runtime_contract.py` r.124, `interfaces.py` r.80/288 en `decision_rule_assessment.py` r.6. Bewust niet aangepast: de eerste twee zijn ketenbestanden in het manifest, en een commentaarwijziging zou alleen hun hash veranderen. Kan in een aparte opruimstap.
3. Het stabiliteitsgetal: de opdracht noemt 20/24, `samenvatting.md` 22/24 (zelfde status in alle runs). Niet herleid.
4. `hulp/replay_v8_besluit19_test.py` (van besluit 19) voldoet niet aan black; niet door mij aangepast.
5. Niet gedraaid: pre-commit-ruff v0.16.5, de volledige unit-suite (`-m unit`), een live-run.
6. Restrisico R1/R2: meer onterechte reviews als het model een terecht beschrijvende passage als `discretion_form` invult of een bron te snel `unclear` noemt. Telt mee in `min_juist` (21/24).

**Volgorde:** korte check (review van deze diff, keuze over §4) → commit → manifest v10 offline met gitleaks-uitzondering 20 → akkoord Chris → fase 1 + 2 → uitslag → stop (afspraak Chris: v10 is de laatste run van dit onderdeel).
