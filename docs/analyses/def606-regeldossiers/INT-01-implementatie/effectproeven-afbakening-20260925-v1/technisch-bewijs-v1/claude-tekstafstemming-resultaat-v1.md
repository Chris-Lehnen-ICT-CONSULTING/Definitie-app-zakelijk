# DEF-770 afbakening — tekstafstemming INT-01 (onbekende afkorting), resultaat v1

Uitvoerder: Claude Code CLI-sessie 442a98fb-a377-403f-996e-433cf4a664fc. Ik heb geen agents, reviewers of extra CLI-sessies gestart.

- Geen betaalde calls of API-calls.
- Geen commit, push of bundelbouw.
- Geen wijziging aan code, tests, het INT-07-record, generatie-instructies, promptmodules, dependencies, config of schema.
- De WIP is niet aangeraakt.

**Gelezen:**

- `docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-afbakening-20260925-v1/afbakening-besluit-v1.md`
- `…/referentie-contract-v1.md`
- `logs/def770-afbakening/contractreview-v1.md`

**Bases:**

| | Commit / versie |
|---|---|
| App HEAD | `659ab505bcba2af6293917dbbcbcbaebc8a5e581` (ongewijzigd) |
| Product | `86b2c0b2…` (/10) |
| Skills HEAD | `2fa72640f6cd48d0d9e5fc9e08fd19942b05a979` (ongewijzigd) |

## Wijziging

Er is uitsluitend tekst gewijzigd, in twee passages.

1. **`src/toetsregels/regels/INT-01.json`, veld `toelichting`.**
   - Oud: „…een los label met dubbele punt, een beletselteken met vervolg en een mogelijke onbekende afkorting blijven onzeker.”
   - Nieuw: „…een los label met dubbele punt en een beletselteken met vervolg blijven onzeker, net als een punt bij een mogelijke onbekende afkorting waarna nog tekst volgt. Staat zo’n afkorting op het teksteinde zonder vervolg, dan is haar onbekende betekenis op zichzelf geen zinsstructuuronzekerheid en geen bewijs van een afgebroken formulering; de toegankelijkheid van de afkorting hoort bij INT-07.”
2. **`skills/definitie-toetsregels/reference.md`, alinea „Toetsen”, los-label-zin.**
   - Oud: „…maar open voor inhoudelijke beoordeling; kan een punt bij een onbekende afkorting horen, dan blijft de grens open.”
   - Nieuw: „…maar open voor inhoudelijke beoordeling. Kan een punt waarna nog tekst volgt bij een onbekende afkorting horen, dan blijft die grens open; een onbekende afkorting op het teksteinde zonder vervolg is op zichzelf geen zinsstructuuronzekerheid en geen bewijs van een afgebroken formulering. De toegankelijkheid van de afkorting beoordeelt INT-07.”

Beide passages zijn beperkt tot de concrete grensvraag bij vervolgtekst. Onbekendheid op het teksteinde is op zichzelf geen zinsstructuuronzekerheid, en toegankelijkheid hoort bij INT-07.

- **Runtime:** dit komt overeen met de bestaande runtime in `zinsgrenzen.py`. Aan het tekstenende ontstaat geen kandidaat; met vervolg volgen de routes „punt na een afkortingsachtige woordvorm zonder klinker” en „punt gevolgd door een kleine letter” (onzeker). Er is geen nieuwe heuristiek en geen versieverhoging.
- **Citaat zonder slotteken:** geen wijziging. De `INT-01.json`-toelichting noemt alleen het slotteken direct vóór het sluitende aanhalingsteken als mogelijke buitengrens. `reference.md` zegt al: „een citaat zonder slotteken … behouden hun beoordeling”. Er is geen aantoonbare inconsistentie.
- **Niet gewijzigd (buiten toewijzing):** de algemene zin in `reference.md` „Een afkortingspunt kan tevens zinslot zijn.” en de passage over de slotpunt van een latere vermelding van een verklaarde afkorting („blijft zonder bewezen vervolg open”). Beide gaan over punten met vervolg. Ik noem ze alleen ter beoordeling voor de reviewer.

**Exacte diff:** `logs/def770-afbakening/tekstafstemming-v1.patch`, sha256 `83fdbae707472b3479d04f7d9e745ce7b400895b40a8cb91a469c625450360bb`. Dit is `git diff HEAD` voor beide repo's; de volledige tekst staat in dat bestand.

## Hashes (SHA256)

| Bestand | Voor (= HEAD, herstelkopie) | Na |
|---|---|---|
| `src/toetsregels/regels/INT-01.json` | `0578ac1cc9588b66c98f62622f0a6beaad55587ffc17af24b6bfe026bfe94d99` | `55914032f262b8eb682f29a10d99303050488423f993ae59c258ef3b16c66fc8` |
| skills `definitie-toetsregels/reference.md` | `83bae6fd19a8baffb95613ead2284cf4527664fd26e84934867f0bc8b686d148` | `9236ac320d26d8ff8d97e1342b8dddf255bd5ebdb87ee59fa2d3d728a37d05bd` |

- **Herstelkopieën:** `logs/def770-afbakening/herstelkopie-tekstafstemming-v1/`, gemaakt met `herstelkopie-maken-v1.py` (log: 2/2 GELIJK, exit 0).
- **Onveranderd:** buiten deze twee bestanden is niets getrackt gewijzigd in app (`src`, `tests`, `config`, `scripts`, `Makefile`) of skills. `INT-07.json` is ongewijzigd (`hashes-en-diff-tekstafstemming-v1.log`).

## Promptpariteit G24 (echte PromptServiceV2 en API-verzoek, offline)

**Werkwijze.** Ik gebruikte het bestaande harnas `effectproeven-20260924-v1/g24_harnas.py prepare --arm nieuw`, met dezelfde invoer als de G24-bronbinding: `effectproeven-restherstel-20260925-v1/g24-invoer-v1.json`, sha256 `042c9b93…984f`. Het harnas bouwt per invoer het echte `GenerationRequest`, de sanitisatie en de fragmenten, roept `PromptServiceV2.build_generation_prompt` aan (tweemaal, determinismecontrole) en bouwt het canonieke API-verzoek, met offline-gate. Er zijn geen netwerkfasen uitgevoerd.

1. **Baseline.** Exact `git archive --format=tar -o logs/def770-afbakening/bron-head-v1.tar HEAD` (commit-ID `659ab505…`, sha256 `a7a00e0c…7a42`). Daarop `prepare`, uitvoer `g24-voorbereiding-head-v1.json` (sha256 `43f8bf24…5364`), log `g24-voorbereiding-head-v1.log`, **exit 0**.
2. **Na de tekstwijziging.** Het harnas accepteert alleen een git-archief. Omdat committen niet mag, maakte `afgeleide-bron-maken-v1.py` een afgeleid archief `bron-tekstafstemming-afgeleid-v1.tar` (sha256 `e7c5083b…56e8`):
   - een kopie van `bron-head-v1.tar` waarin **uitsluitend** `src/toetsregels/regels/INT-01.json` door de werkboomversie is vervangen;
   - controle in de log: 3696 leden, zelfde namen, één inhoudelijk verschillend lid;
   - de pax-header `comment` blijft `659ab505…`, dus de commit-ID in dit archief is **geen** bewijs van de inhoud;
   - de inhoud blijkt uit de sleutelhash die het harnas zelf vastlegt;
   - log `afgeleide-bron-maken-v1.log`, exit 0.

   Daarop `prepare`, uitvoer `g24-voorbereiding-tekstafstemming-v1.json` (sha256 `a4c0b32c…85f8`), **exit 0**.
3. **Vergelijking** (`promptpariteit-v1.py` → `promptpariteit-v1.log`, exit 0):
   - Beide voorbereidingen: `klaar True`, `offline_gate_actief True`, zelfde invoer.
   - Sleutelbestand `INT-01.json` volgens het harnas: head `0578ac1c…`, nieuw `55914032…`. De gewijzigde tekst zat dus werkelijk in de geladen bron; overige sleutelbestanden zijn gelijk.
   - Per invoer G01–G06 zijn **alle** voorbereidingsvelden identiek: request, sanitisatie, context, fragmentrelaties, bronnormalisatie, prompt, `prompt_sha256`, determinisme, tokentelling, gebruikte componenten, source_receipt, controles, `api_verzoek` en `api_verzoek_sha256`.
   - De prompthashes zijn gelijk aan `effectproeven-citaatbeleid-20260925-v2/g24-behoudbinding-v1.json`.

| Invoer | prompt_sha256 | api_verzoek_sha256 |
|---|---|---|
| G01 | `351170b0f364b6e3d53a4b510dea53f960e01ead007fcb831002e93e31a8332f` | `863e05ca6ae3a9cc1b6888d5bf334024596a0a21be46e072ae7a028a41041893` |
| G02 | `dc0a933c0fcc35902a9517bed80abbf578898b72966ba026956345d4d249e020` | `eac94a3084a6ac02c75585bfd11b41a578f467828c7dd828cc013b9ea5f0e91f` |
| G03 | `18c61d6490b23a207d2b026e0a071ad716869f6a73cefac1a0d99ed939a60860` | `b681c4a4f0fe3e8197de8c4f71075923141977cce9aa21a0d92aa8332fd85d89` |
| G04 | `b8e07cdca066875c6be32ac6bd0bee97a5cc33637a8553c58fd35bde2615fc2d` | `35b2cd8fb29bcb8f4d58d35409c53575c2902d5ad4e37e5dca954d703640b158` |
| G05 | `9bf3ad03493f9b1ace4c4029ece2a90c892dee0c2f79dcef87d9c173f2ad9b27` | `d238c7600e94aa53ac2ec15c605517da8354ef3e1e83cd957e32ec9bb13f1891` |
| G06 | `13ab2e25a382fcc04790d99a3694ebc9cfd65cf8bd40a9a439e25d2845363a0d` | `fafbbb25cf7bf83cf091a637da828ce37b17a50b31983511064b562c5e814c2f` |

**Uitkomst: PARITEIT IDENTIEK.** De prompts noemen INT-01 wel, maar de tekst van het veld `toelichting` staat er niet in, oud noch nieuw. `rule_cache.py` noemt `toelichting` prompt- en documentatiemetadata buiten `RUNTIME_VELDEN`, en de promptmodules lezen dit veld niet. De wijziging raakt de G24-prompt en het API-verzoek dus niet. Er is geen verdere generatieactie nodig of ondernomen.

## Tekstladen, tests en lint

| Stap | Commando | Log | Exit | Resultaat |
|---|---|---|---|---|
| JSON en regelladen, beide laadpaden | `PY logs/def770-afbakening/tekstcontrole-v1.py` | `tekstcontrole-v1.log` | 0 | JSON geldig; `toetsregel_manager` en `cached_manager` (cache eerst geleegd) laden INT-01 met exact de nieuwe toelichting; oude brede formulering weg |
| Gerichte app-tests `-m unit` | `PY logs/def770-afbakening/pytest-log-v1.py tekstafstemming-gericht-v1 …` (zie onder) | `tekstafstemming-gericht-v1.log`/`.xml` | 0 | 944 tests, 0 failures, 5 skipped |
| Skills-tests `definitie-toetsregels` | `PY -B -m pytest -q -p no:cacheprovider --tb=short tests/test_skill_package_isolation.py tests/test_build_cowork_alias_zips.py` (cwd skills) | `skills-tests-v1.log`/`.xml` | 1 | 30 passed, 1 failed (zie onder); skills-status vóór en na de tests identiek (`skills-status-voor-tests-v1.txt`) |
| Geraakte lint | `PY logs/def770-afbakening/lint-tekstafstemming-v1.py` | `lint-tekstafstemming-v1.log` | 0 | zie onder |

Gerichte app-tests (`PY` = `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python`):

- `tests/unit/validation/test_def770_int01_zinsgrenzen.py` (bevat de INT-01-recordtest)
- `test_json_validators.py`
- `test_category_mapping_externalized.py`
- `test_rule_runtime_matrix.py`
- `test_v2_golden_additional_patterns.py`
- `test_v2_golden_initial_int_con.py`
- `tests/unit/services/test_def770_int01_keten.py`
- `test_def770_int01_opslag.py`
- `tests/unit/services/prompts`

**De skills-failure is verwachte zipdrift:** `test_elke_gecommitte_aliaszip_is_inhoudelijk_actueel` meldt dat `toetsregels.zip: toetsregels/reference.md wijkt af van een verse build`. Dat is het directe gevolg van de toegewezen `reference.md`-wijziging, omdat bundelbouw in deze stap uitgesloten is. De coördinator bouwt de zips opnieuw (`scripts/build-cowork-alias-zips.py --all`).

**Geraakte lint:**

- trailing-whitespace en end-of-file-fixer: beide bestanden schoon.
- JSON geldig.
- stale-references-hook van de skills-repo (`scripts/stale_reference_detector.py`): „Geen stale references gevonden”, exit 0.
- De app-hooks gelden alleen voor Python-bestanden en raken `INT-01.json` niet.
- Ruff en Black: niet van toepassing (geen Python gewijzigd).

**Volledige suite:** niet gedraaid. Het gaat uitsluitend om een tekstdelta, en tekstladen en promptpariteit tonen geen runtimedoorwerking.

## Nieuwe bewijsbestanden (`logs/def770-afbakening/`)

- `herstelkopie-maken-v1.py`/`.log`, `herstelkopie-tekstafstemming-v1/`
- `bron-head-v1.tar`, `afgeleide-bron-maken-v1.py`/`.log`, `bron-tekstafstemming-afgeleid-v1.tar`
- `g24-voorbereiding-head-v1.json`/`.log` (+ `.json.werk`), `g24-voorbereiding-tekstafstemming-v1.json`/`.log` (+ `.json.werk`)
- `promptpariteit-v1.py`/`.log`, `tekstcontrole-v1.py`/`.log`
- `pytest-log-v1.py`, `tekstafstemming-gericht-v1.log`/`.xml`
- `skills-status-voor-tests-v1.txt`, `skills-tests-v1.log`/`.xml`
- `lint-tekstafstemming-v1.py`/`.log`
- `hashes-en-diff-tekstafstemming-v1.py`/`.log`, `tekstafstemming-v1.patch`

## Beperkingen

- De tweede voorbereiding draait op een afgeleid archief, niet op een commit. De inhoud is gebonden via de archiefhash en de sleutelhash van `INT-01.json`; de commit-ID in de header is ongewijzigd HEAD.
- Promptpariteit is aangetoond voor de zes bestaande G24-invoeren. Andere invoeren gebruiken dezelfde modules, maar zijn niet afzonderlijk gedraaid.
- Er zijn geen T24-gevallen gemaakt of gelezen.

Gestopt voor dezelfde onafhankelijke reviewer.
