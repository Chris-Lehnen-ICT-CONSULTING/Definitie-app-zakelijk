# DEF-768 — ESS-05: uitvoercontract, samenvoeging en WP7-runplan (v2)

24 september 2026 · uitvoerder Claude Code CLI (sessie
`6d273f41-0afb-480a-9034-1c87b1ecba58`) · basis `26f2374d3` · branch
`feature/DEF-768-ess05-ai-beoordeling`. Vervangt v1
(`2026-09-23-DEF-768-ess05-contract-en-runplan-v1.md`, bevroren en ongewijzigd)
na de gerichte review van 24 september (Cowork `review-v1.md`, RE5-01…RE5-12
en Codex-punten 1–5). Leidend blijven besluiten K-1…K-10 en synthese v3. Geen
modelcall uitgevoerd, geen kwaliteitswinst geclaimd; alle genoemde
uitkomsten komen uit offline tests met fakes.

## 0. Wat verandert ten opzichte van v1

| Onderdeel | v1 | v2 | Grond |
|---|---|---|---|
| Vraag per buur (§1) | kenmerkvraag | kenmerkvraag **met afgrenzing**: een ander woord of kenmerk alleen is nog geen afgrenzing | RE5-01, binnen K-3b/K-5 |
| Citaat ook in de buurdefinitie (§2) | technische fout | **signaal** in de bestaande redenweergave; alleen volledig gelijke kernen als `distinguished` blijven een technische fout | Codex-punt 2 / review correctie 5 |
| Trefwoorden 'uniek/specifiek/bijzonder' | "horen niet in de kern" | op zichzelf geen kenmerk; geen vervanging van een concreet kenmerk; als deel van naam/vaste term blijven ze staan | Codex-punt 3 |
| Beslisvolgorde (§4) | stap 6/7 | ongewijzigd, nu expliciet als **bestaande implementatiekeuze** benoemd en met een test vastgepind | Codex-punt 1, RE5-03/RE5-06 |
| `prompt_version` | `ess05-assess/1` | `ess05-assess/2` (T-tekst gewijzigd; de normhash wijzigt ook) | binding |
| Runplan (§5) | 60 calls, geen marge | **budgetvoorstel** met offline nulcallroutes apart, vier referentiegevallen, rubric | RE5-04, RE5-05 |

Het uitvoerschema, de labels (`distinguished | not_distinguished | unclear`),
de velden `distinguishing_feature_quote`/`missing_feature`/`reason` en de
invoer zijn **ongewijzigd**. Er is geen nieuw verplicht invoerveld en geen
'bedoelde betekenis' als verplicht veld; bedoelde betekenis blijft wat zij in
v1 was: optionele invoer die, als zij er is, meetelt.

## 1. De vraag per verwant begrip (K-3b, met afgrenzing)

De vraag blijft een kenmerkvraag, geen extensietoets (ESS05-E05: één persoon
kan lener én werknemer zijn). Aangescherpt binnen K-3b en K-5:

> Heeft de kern een onderbouwd kenmerk dat gevallen van het verwante begrip
> afgrenst die volgens bron of bedoelde betekenis **niet** onder dit begrip
> vallen? Gedeelde gevallen mogen. Een ander woord of een ander kenmerk alleen
> bewijst nog geen afgrenzing. Zijn de gronden onvoldoende, dan is de uitkomst
> `unclear`; verzin geen tegenvoorbeeld of betekenis.

Een kenmerk dat ook het verwante begrip draagt — in het ASTRA-paar alleen
'jeugdige' bij onttrekking en ontvluchting — grenst niets af en telt niet als
bewijs. Dit is de semantiek van `distinguished`; het schema verandert niet.

Vindplaatsen (letterlijk gelijk aan de app, gecontroleerd door tests):

- G: `src/services/prompts/modules/json_based_rules_module.py`, sleutel `"ESS-05"`
  (test: `tests/unit/services/prompts/test_def768_ess05_promptnorm.py`).
- T: `_TOETSINSTRUCTIE` en de uitkomstdefinities in `_systeemprompt`,
  `src/services/validation/ess05_assessment_service.py`
  (test: `TestNormEnPrompt` in `tests/unit/validation/test_def768_ess05_assessment_service.py`).
- Norm: `uitleg`, `toelichting` en `toetsvraag` in `src/toetsregels/regels/ESS-05.json`.

**Niet overgenomen uit RE5-01:** een nieuw besluit 'K-3c' en 'bedoelde
betekenis' als vereiste invoer. Dat zou een nieuw productbesluit en een nieuw
verplicht veld zijn; de aanscherping hierboven blijft binnen K-3b en K-5.

## 2. Modeluitvoer en codecontroles

Het JSON-schema is identiek aan v1 §2. De codecontroles (fail-closed) zijn:

| Controle | Door code bewaakt? | Uitkomst bij afwijking |
|---|---|---|
| exact de afgesproken velden en typen; elke verzonden buur precies één keer; geen onbekende ID | ja | `malformed_response` → `error` |
| `distinguished` ⇒ citaat en geen `missing_feature`; `not_distinguished` ⇒ `missing_feature` en geen citaat; `unclear` ⇒ geen citaat; buur zonder definitie ⇒ alleen `unclear` | ja | `malformed_response` |
| `lacks_differentia=true` naast een `distinguished` buur (RE5-03, eerste punt) | ja — **al afgedekt** in `src/domain/ess05/contract.py` (`_lijstfout`, "lacks_differentia strookt niet met een onderscheiden buur"); sinds 24-09 ook met een test vastgepind | `malformed_response` |
| het citaat staat letterlijk in de **definitiekern** (niet in toelichting of context) | ja (harde controle) | `unverifiable_evidence` → `error` |
| kern en buurdefinitie volledig gelijk (na witruimte, hoofdletters, slotpunt) terwijl het model `distinguished` meldt | ja | `unverifiable_evidence` ("kern gelijk aan de buurdefinitie") |
| het citaat staat óók in de buurdefinitie | **alleen signaal**: in de bestaande redenweergave van dat buuronderdeel ("Signaal: het citaat staat ook in de buurdefinitie; …"); status ongewijzigd | geen fout |
| voorstel met `source_id` citeert letterlijk uit die verzonden bronpassage | ja | `unverifiable_evidence` |
| `question` is null of precies één vraag | ja | `malformed_response` |
| of het geciteerde kenmerk werkelijk afgrenst, of de reden klopt, of een parafrase gelijkwaardig is, of een beperkt kenmerk ('jeugdige') iets afgrenst | **nee — alleen de inhoudelijke beoordeling** | — |

Waarom de gedeelde passage geen fout meer is: 'beschikt over een geldige
vergunning' tegenover 'persoon die *niet* beschikt over een geldige vergunning'
deelt woorden maar niet het kenmerk; en een langer citaat zou de oude
controle wél passeren. De controle mat dus citaatlengte, geen onderscheid.
E06 blijft in code beschermd waar code dat kan (gelijke kernen), en verder
inhoudelijk: het model moet `not_distinguished` melden, en dat geeft `fail`.
Een geparafraseerde E06-buur kan code niet herkennen; ook dan draagt alleen het
modeloordeel de afkeuring.

Tests (`tests/unit/domain/test_def768_ess05_contract.py`): positieve vs.
ontkennende predicaat, citaatlengte (kort, hele kern, langer dan de kern),
volledig gelijke kernen (ook met witruimte/hoofdletter/punt), gelijkwaardige
parafrase met `not_distinguished` → `fail`, geen signaal zonder gedeelde
passage, E05 → `pass`, E06 → `fail`. Deze tests gebruiken fakes en bewijzen
de codegrens, geen AI-kwaliteit.

## 3. Burenlijst

Ongewijzigd t.o.v. v1 §3.

## 4. Samenvoeging (code) — één beslisvolgorde

1. Geen term of tekst, of geen context → `not_evaluated` met reden; geen modelcall (K-9).
2. Technische fout (dienst, transport, burenlijst, repository, schema, citaat) → `error`.
3. Geen actieve buren én geldige deskundige bevestiging 'vergelijkingsruimte
   leeg' → `pass` 'leeg bevestigd'; geen modelcall (K-2).
4. `lacks_differentia` → `fail` met K-8-reden.
5. Een **bevestigde** buur `not_distinguished` → `fail` (buur + ontbrekend kenmerk).
   **Fail gaat vóór open.**
6. Anders `review_required` (open) met precies één vraag wanneer:
   a. een bevestigde buur `unclear` is;
   b. er een onbevestigde buur met herkomst `bron`, `model` of `ontologie` is,
      of het model nieuwe buren voorstelt (K-1) — **ongeacht** het oordeel over die buur;
   c. een onbevestigde buur met een andere herkomst (in de praktijk `repository`)
      `not_distinguished` of `unclear` is;
   d. er geen bevestigde buur is (K-2).
7. Anders → `pass`: ≥ 1 bevestigde buur, alle bevestigde buren `distinguished`.
   Een onbevestigde repositorybuur die `distinguished` is, blokkeert dat niet
   en blijft zichtbaar gemarkeerd als "repository, onbevestigd" in zijn
   buuronderdeel.

**Status van stap 6c/7:** dit is een **bestaande implementatiekeuze** van de
uitvoerder (zelfde gedrag als v1 §4, ongewijzigd in code), geen nieuw
gebruikersbesluit. Zij blijft binnen K-1 (dat alleen modelvoorstellen als
onbevestigd-blokkerend noemt) en K-2, en voert geen strengere blokkade in. Zij
beantwoordt ook RE5-06: een gevulde repository maakt ESS-05 niet structureel
open zolang de bevestigde buren onderscheiden zijn. Vastgepind in
`test_beslisvolgorde_onbevestigde_onderscheiden_buur`
(repository → `pass`, bron/model → open). Wil Chris dat een onbevestigde
repositorybuur altijd openhoudt, dan is dat een aparte keuze (strenger dan K-1).

Alles `no_score`, prioriteit `midden`; een `fail` is een zichtbare,
niet-blokkerende bevinding. Geen automatische tekstwijziging.

**Scope K-9 (RE5-08):** DEF-768 levert uitsluitend de ESS-05-lokale
`not_evaluated`; de appbrede voorwaarde "zonder context niet genereren en niet
toetsen" is DEF-622-scope.

**STR-04 en ESS-05 blijven onafhankelijk (RE5-07 niet overgenomen):** een
syntactische STR-04-fout bewijst niet per definitie een inhoudelijk
ESS-05-gebrek (een kern kan vormfouten hebben en toch een afgrenzend kenmerk
dragen). Er komt dus geen regel "elke STR-04-fail ⇒ ESS-05-fail zonder call".

## 5. WP7-runplan — budget als VOORSTEL (niet geautoriseerd)

### 5.1 Offline nulcallroutes (apart, geen callbudget)

Deze routes eindigen per contract zonder modelcall en horen in de offline
routeproef, niet in de callbegroting:

- geen term of tekst → `not_evaluated`;
- geen context (K-9) → `not_evaluated` (zo ook casus B-09 zoals beschreven:
  zaaknummer zonder context);
- geen buren + geldige lege-ruimtebevestiging (K-2) → `pass`;
- ongeldige burenlijst → `error`; te lange buurdefinitie → `input_truncated`
  zonder aanroep;
- cachetreffer met dezelfde binding.

**Niet automatisch nulcall:** een route mét context maar zonder bekende buren
en zonder lege-ruimtebevestiging roept het model wél aan — voor de K-8-vraag
(ontbreekt de toespitsing geheel?) en voor K-1-voorstellen van verwante
begrippen (`test_ook_zonder_buren_een_aanroep_voor_k8_en_voorstellen`).

### 5.2 Ontwikkelmateriaal met de vier leidende referentiegevallen

| Geval | Casus | Buur | Verwacht |
|---|---|---|---|
| ASTRA-FOUT | A-02/B-01 | ontvluchting | `fail` (bevestigde buur `not_distinguished`; 'jeugdige' grenst niets af) |
| ASTRA-GOED | A-01/B-02 | ontvluchting | `pass` (opsomming voorzieningen grenst af) |
| ESS05-E05 | lener/werknemer | werknemer | `pass` (overlap toegestaan) |
| ESS05-E06 | gebruiker/klant 'geregistreerd' | klant | `fail` |

ASTRA-paar uit de ASTRA-pagina (revisie 8561); E05/E06 zijn synthetisch
(uitleendienst) en herkenbaar als zodanig. Offline zijn alle vier als
fake-uitkomst vastgelegd in de contracttests; dat bewijst de samenvoeging, niet
het modeloordeel.

### 5.3 Callbegroting (voorstel)

| Post | Variant A (binnen plafond 60) | Variant B (vraagt besluit) |
|---|---|---|
| Ontwikkelset: 12 casussen − B-09 (nulcall) + E05 + E06 | 13 | 13 |
| T-eindset (onafhankelijk, vooraf gelabeld) | 20 | 20 |
| T-herhalingen (4 vooraf gekozen grensgevallen × 2) | 8 | 8 |
| G-calls | 16 (4 invoeren × 2 varianten × 2 runs) | 20 (5 × 2 × 2) |
| Reserve technische fouten | 3 (≈ 5 %) | 6 (10 %) |
| **Totaal** | **60** | **67** |

Geen retries buiten de reserve; mislukte calls tellen mee. **Eén**
ontwikkelronde; een tweede ronde na promptbijstelling is niet begroot en
vraagt een apart besluit. Variant B overschrijdt het WP7-plafond en wordt niet
zonder expliciet besluit van Chris gebruikt. Niets hiervan is geautoriseerd.

### 5.4 Rubric voor inhoudelijke redenen (vooraf vastgelegd; identiek voor T en G)

Een uitkomst telt alleen als inhoudelijk correct als de status klopt én de
reden op elk punt voldoet:

1. **Juiste relevante buur** — de genoemde buur is het verwante begrip waar
   het om gaat.
2. **Werkelijk onderscheidend of ontbrekend kenmerk** — bij `distinguished`
   grenst het geciteerde kenmerk werkelijk gevallen van de buur af; bij
   `not_distinguished` ontbreekt het genoemde kenmerk werkelijk.
3. **Steun in bron of bedoelde betekenis** — de afgrenzing volgt uit het
   aangeleverde materiaal.
4. **Juiste omgang met overlap en onzekerheid** — gedeelde gevallen niet als
   gebrek; onvoldoende grond als `unclear`, niet als oordeel.
5. **Geen verzonnen feit of bron** — geen verzonnen buur, kenmerk,
   tegenvoorbeeld, betekenis of bron.

Het aantal beoordelaars (Cowork stelt twee voor, met geregistreerde en
geadjudiceerde onenigheid) is een open keuze voor Chris.

### 5.5 Bewijsformat en acceptatie

Ongewijzigd t.o.v. v1 §5, met `prompt_version` `ess05-assess/2` en de rubric
van §5.4 per call vastgelegd.

## 6. Disposities van de gerichte review (24-09)

| Punt | Dispositie | Waar |
|---|---|---|
| RE5-01 | **gecorrigeerd** binnen K-3b/K-5 (G, T, norm, contractsemantiek); K-3c en verplichte 'bedoelde betekenis' **niet overgenomen** (nieuw productbesluit/veld) | §1 |
| RE5-02 | **open, voor Chris/coördinator**: de afwijking van plan-§3 is sinds v1 §1 gedocumenteerd; een formele planwijziging (besluitenrij, Linear-comment) is een gebruikersbesluit, geen uitvoerderswerk | — |
| RE5-03 eerste punt | **al afgedekt** (`_lijstfout`), nu met test | §2 |
| RE5-03 tweede punt / RE5-06 / Codex 1 | **gecorrigeerd in documentatie**: één beslisvolgorde, als bestaande implementatiekeuze; geen runtimewijziging (code en document verschilden niet) | §4 |
| RE5-04 | **als voorstel verwerkt** (variant A/B, nulcallroutes apart, E05/E06 in ontwikkelset, één ronde) | §5 |
| RE5-05 | **gecorrigeerd**: rubric vooraf; aantal beoordelaars open | §5.4 |
| RE5-07 | **niet overgenomen** (STR-04 en ESS-05 onafhankelijk) | §4 |
| RE5-08 | **gecorrigeerd** (scopezin) | §4 |
| RE5-09…RE5-12 | geen actie in deze batch (observaties/akkoord) | — |
| Codex 2 | **gecorrigeerd** (citaatcontrole, signaal, gelijke-kernenbescherming) | §2 |
| Codex 3 | **gecorrigeerd** (G, T, norm, semantische categorisatie; skillvoorstel v2) | §1 |
| Codex 4, 5 | **gecorrigeerd** in skillvoorstel v2 | `2026-09-24-DEF-768-ess05-skillvervangingen-voorstel-v2.md` |
