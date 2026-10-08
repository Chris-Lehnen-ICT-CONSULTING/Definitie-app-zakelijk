# DEF-835 — besluiten Chris: promptcorrectie /2 en v3-kwalificatieproef

7 oktober 2026. Vastgelegd door Claude (Cowork) na een punt-voor-punt doorloop van de controlebevindingen met Chris; Chris koos per punt uit voorgelegde opties met gevolgen.

## Gecontroleerde stand (07-10-2026)

- Werkboom `.claude/worktrees/DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, basis `a9fb4a0b7` (gemerged via PR #488). Prompt `def835-int02-prompt/2` staat als niet-gecommitte wijziging in `src/services/validation/int02_assessment_service.py` en `tests/unit/services/prompts/test_def835_int02_prompt.py`.
- Tests: 62 prompttests geslaagd; 783 def835/int02-unittests geslaagd (11 overgeslagen, 0 gefaald; met `--import-mode=importlib`); de gerichte selectie uit takenlijst-v51 opnieuw 452 geslaagd. Ruff en black schoon.
- Onafhankelijke Codex CLI-review (read-only, 07-10): geen blokkerende bevindingen; geen casusmateriaal in de prompt; citaten blijven hard gecontroleerd in `src/domain/int02/contract.py`.
- SHA-256 zelf nagerekend:
  - dienst `src/services/validation/int02_assessment_service.py`: `1b7144c5d0e99984dcc4130b40c9c0708ffde16539a2ccf48ccfe5804436b39f`
  - `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v3.json`: `62d1e3dbfcf19c6a6d4a32971ac27361df7f75b9eb983db7eed2878e4df8fcd1`
  - `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-gevallen-v1.json`: `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`
  - `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-payloads-v3.json`: `6dc579dc99e7c388959ff8a4b8b18a25306fe07d10a84f75af850d8a57e1a269`
  - systeemprompt /2 zoals de huidige code hem bouwt: `92deecb85fec…`, gelijk aan `systeemprompt_sha256` in het v3-manifest.

## Besluit 1 — formulering van de fail-aanwijzing

Chris gaf eerder akkoord op `promptcorrectie-voorstel-v1.md` (tot nu toe alleen vastgelegd als vinkje in `takenlijst-v51.md`). De code wijkt af van de voorsteltekst: "de aangeleverde grond uit kern, bevestigde bedoeling, context of bronpassage" in plaats van "de aangeleverde betekenisgrond"; daarnaast "actorpassage" → "passage" en "begripskenmerk" → "begripscriterium". De uitvoerder meldde dit als open punt 1 in `promptcorrectie-uitvoeringsverslag-claude-v2.md`.

**Besluit Chris: de code-formulering wordt geaccepteerd.** Reden: zij sluit aan op de T-tekst en op K1 (ook een zelfstandig actorvoorschrift in de kern is een gebrek); de letterlijke voorsteltekst zou een expliciet voorschrift in de kern als fail-grond uitsluiten. De beperking "leid fail niet enkel af uit een kwalitatief of modaal woord" blijft onverkort. Niet gekozen: terug naar de voorsteltekst (prompt /3) of eerst naast elkaar lezen.

## Besluit 2 — vastlegging

**Besluit Chris:** één besluitbestand (dit bestand) voor het akkoord op de promptcorrectie, de keuzes van 07-10 en het proefakkoord.

## Besluit 3 — aandachtspunt meerdere passages

De Codex-review van 07-10 signaleert een kleine dubbelzinnigheid (`int02_assessment_service.py:375`): de nieuwe `insufficient_information`-aanwijzing herhaalt niet dat een andere passage met een zelfstandig bewezen gebrek `fail` blijft. Elders in de systeemprompt (T-tekst) staat dat wel.

**Besluit Chris: nu niet herstellen.** Bij de bespreking van elke proefuitkomst wordt expliciet nagegaan of dit patroon optreedt; zo ja, dan herstel in prompt /3 met een nieuw manifest en een nieuw akkoord.

## Besluit 4 — veiligstellen van het werk

**Besluit Chris:** één commit op `feature/DEF-835-int02-o2` in deze werkboom (basis `a9fb4a0b7`, zodat de v3-hashes geldig blijven) met prompt /2 en het dossier, zonder de geneste `.claude/handovers/`-bestanden binnen de docs-map en zonder `.claude/hooks/check-silent-exceptions.py`. Daarna push als back-up. Geen PR en geen merge vóór de proefuitkomst. De gitleaks-hook wordt niet omzeild; blokkeert hij, dan stopt de uitvoering en wordt het gemeld.

## Besluit 5 — verouderde statusdocumenten

**Besluit Chris:** een nieuwe `processtatus-uitvoering-v13.md` met de actuele stand; de oude documenten blijven ongewijzigd en worden daarin als achterhaald benoemd.

## Besluit 6 — v3-kwalificatieproef: akkoord in stappen

**Besluit Chris: akkoord op fase 1 (regressie) alleen.**

- Nu toegestaan: uitsluitend de drie regressiegevallen C105, C107 en C112 volgens `kwalificatie-manifest-v3.json` (SHA-256 `62d1e3db…fcd1`) en `kwalificatie-gevallen-v1.json` (SHA-256 `af1ab46c…6953`); Anthropic `claude-opus-5`, profiel `def835-kwalificatieproef-opus5-v1`, prompt `def835-int02-prompt/2`, routertaak `validation`.
- Maximaal 3 calls, 0 automatische herhalingen, 0 terugval naar een ander model; grenzen per call en stopregels volgens het manifest.
- De proef draait op de commit uit besluit 4.
- Na fase 1 stopt de uitvoering, ook bij 3/3 goed. Ontwikkeling (24) en hold-out (16) vragen een afzonderlijk akkoord van Chris na bespreking van de regressie-uitkomst, binnen hetzelfde manifest en budget (totaal maximaal 43 calls en US$12).
- Geen activering van O2, geen WP5a-/UI-stap, GitHub Actions blijft uit.

## Besluit 7 — gitleaks-blokkade (07-10-2026)

De staged commit uit besluit 4 (459 bestanden) werd door de gitleaks-hook geblokkeerd met 26 bevindingen; alle 26 zijn false positives (12 SHA-256-regels van repo-bestanden, 2 regels uit een JSONL-commandolog, 12 keer de nep-fixture uit `tests/unit/utils/test_pii_redaction_api_keys.py`). Er zijn geen echte credentials gevonden.

**Besluit Chris: optie A.** Exacte uitzonderingen volgens het runbook (per bestand eigen blok, `condition = "AND"`, exact pad én volledige regel, alleen `generic-api-key`) voor de 12 hashregels en de 2 streamregels; onderbouwing per regel in `gitleaks-metadata-akkoord-v2.md`. De 4 gate-uitvoerbestanden met de nep-fixture (`bewijs/mergevoorbereiding-v1/gates/` en `bewijs/mergevoorbereiding-v1/samengevoegde-gates/`, telkens `unit-inventaris.json` en `unit-junit.xml`) worden niet gecommit; ze blijven lokaal staan. De hook wordt niet omzeild.

## Besluit 8 — manifest v4 en fase 1 (07-10-2026)

**Oorzaak.** Manifest v3 legde `anthropic` 0.107.1 vast in de identiteit. De hoofd-venv werd op 07-10 om 00:13 door Claude bij `pip install -r requirements.txt` bijgewerkt naar de al sinds juli gepinde 0.116.0 (`anthropic-0.116.0.dist-info`, mtime 2026-10-07 00:13). De runner weigerde v3 daardoor met `identiteit_gewijzigd`.

**Keuze Chris: optie A — nieuw manifest v4.** v4 is offline aangemaakt (geen API-call, geen sleutel). Het verschil met v3 is alleen `identiteit.versies.anthropic` (0.107.1 → 0.116.0), `identiteit.proefmap` en `identiteit_sha256`, plus het tijdstempel `aangemaakt`. Alle 43 payloads zijn byte-identiek aan v3; het payloadbestand verschilt alleen in de identiteitshash in de kop. Gevallen, prompt `def835-int02-prompt/2`, bron en limieten zijn gelijk.

- `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v4.json`: `57a988de4b159065f0b5279b201973c40573e07c1d8af97258fa9bbb1cf5364a`
- `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-payloads-v4.json`: `6b09b01d31fccd85d3e1b96c37f711c1c0e0cbc597bf3eefaa56aa8040be83b0`
- `identiteit_sha256` (v4): `0a095697705b8bfde676d8653b5317c5da701197f6b04975c0fc7c2a77f2d644`
- `kwalificatie-gevallen-v1.json` ongewijzigd: `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`

**Akkoord Chris: alleen fase 1** (`--fase regressie`, C105/C107/C112, maximaal 3 calls); daarna stoppen en bespreken. Het akkoordbestand `kwalificatie-akkoord-v4.json` bevat het protocolkader (43 calls, US$12), omdat de runner dat veldformaat eist; de beperking tot fase 1 is deze procesafspraak. Besluit 6 (v3) is hiermee vervangen.

**Sleutel.** De API-sleutel wordt bij de run door de shell uit de `.env` van de hoofdcheckout gelezen en niet getoond; er komt geen `.env` in de werkboom.

## Besluit 9 — citaatposities door de dienst (07-10-2026)

**Uitslag fase 1 (manifest v4).** Inhoudelijk waren alle drie de gevallen juist: C105 `fail`, C107 `insufficient_information` (hersteld ten opzichte van v2) en C112 `pass`. C105 en C107 hadden geldige citaten. C112 werd toch `invalid_citation`, omdat het model `end` te kort telde: 71 in plaats van 73 in de kern en 46 in plaats van 47 in de bedoeling. De citaten zelf stonden letterlijk in het veld. In v2 lag een `start` één codepunt te laat. Het model telt codepunten dus niet betrouwbaar, en de zelfcontrole-instructie van prompt /2 hielp daar niet tegen. Kosten $0,082385 (3 calls), stopreden `invalid_citation`. Aandachtspunt 3 (besluit 3) was in deze drie gevallen niet toetsbaar. Details: `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v4-uitslag-v1.md`.

**Keuze Chris: optie A.** De dienst bepaalt de posities. Het model levert per passage- en grondcitaat alleen het letterlijke citaat en het veld. De code zoekt het citaat als exacte substring (Python-codepunten, geen normalisatie) in de tekst van het opgegeven veld: `start` is de vindplaats en `end = start + len(quote)`. Komt het citaat 0 keer of meer dan 1 keer voor, dan volgt `invalid_citation` met een onderscheidbare reden (`niet_gevonden` of `niet_uniek`; ook `leeg` en `grond_niet_herleidbaar`). De letterlijkheidseis blijft even streng. Dit is geen stille reparatie van modelposities: het model levert ze niet meer, en meegeleverde `start`/`end` worden als onbekend veld geweigerd. Het opgeslagen document houdt `start`/`end`, nu door de code afgeleid, zodat UI en export ongewijzigd blijven. Nieuwe versies: contract `def835-int02-assessment/2` en prompt `def835-int02-prompt/3`. Uitvoering: `goldset-voorbereiding/positiecorrectie-v1/uitvoeringsverslag-claude-v1.md`.

**Afgewezen:**
- B: een strengere instructie in de prompt (de zelfcontrole-instructie van /2 hielp al niet);
- C: genummerde woorden;
- D: parkeren.

**Vervolg:**
1. Onafhankelijke Codex-review van de diff.
2. Commit en push.
3. Offline manifest v5 met nieuwe prompt-, systeemprompt-, bestands- en payloadhashes.
4. Nieuw exact akkoord van Chris op v5.
5. Daarna opnieuw alleen fase 1 (C105/C107/C112).

## Besluit 10 — manifest v5 en fase 1 (07-10-2026)

**Manifest v5.** v5 is offline aangemaakt (geen API-call, geen sleutel) op HEAD `f83959eb0` (contract `def835-int02-assessment/2`, prompt `def835-int02-prompt/3`).

Verschil met v4:
- `promptversie` `def835-int02-prompt/2` → `def835-int02-prompt/3`;
- `systeemprompt_sha256` `92deecb8…` → `da4a4112…`;
- bestandshashes van `src/domain/int02/contract.py`, `src/services/validation/int02_assessment_service.py`, `src/toetsregels/runtime_contract.py` en `tests/fixtures/def835_int02_ontwerpgevallen.json`;
- alle 43 payloads, uitsluitend in de systeemtekst (veld `system`, telkens −273 bytes);
- `identiteit.proefmap` (`kwalificatieproef-v5`), `identiteit_sha256` (`bfc574547890…`) en het tijdstempel `aangemaakt`.

Gelijk aan v4: gevallen, per geval de invoer, dataprompt en label, model, SDK `anthropic` 0.116.0, limieten, prijzen, criteria, fasevolgorde en protocol/norm.

- `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v5.json`: `6655153275346ffbc95d1b1c26c8b22c5ff7f9ff521e8900793a4ecfae498fe7`
- `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-payloads-v5.json`: `dc39a758e719f815de60d4d23c7f57498bd4875febae4d9f802f5b3e15270f04`
- `kwalificatie-gevallen-v1.json` ongewijzigd: `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`

**Akkoord Chris: alleen fase 1** (`--fase regressie`, C105/C107/C112, maximaal 3 calls); daarna stoppen en bespreken. Het akkoordbestand `kwalificatie-akkoord-v5.json` bevat net als bij v4 het protocolkader (43 calls, US$12), omdat de runner dat veldformaat eist; de beperking tot fase 1 is deze procesafspraak. Besluit 8 (v4) is hiermee vervangen.

**Sleutel.** Zoals bij v4 wordt de API-sleutel bij de run door de shell uit de `.env` van de hoofdcheckout gelezen en niet getoond; er komt geen `.env` in de werkboom.

## Besluit 11 — variatiemeting C107 (07-10-2026)

**Uitslag fase 1 (manifest v5).** 2/3 juist, mechanisch niet geslaagd (`te_weinig_juist`). C105 `fail` en C112 `pass` zijn juist, met 0 citaatfouten: de positiecorrectie van besluit 9 werkt. C107 werd `fail` (`discretionary_decision_rule`, onzekerheid `non_decisive`) terwijl `review_required` werd verwacht. In v2 was C107 ook `fail`, in v4 `review_required`. Kosten $0,07772. Details: `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v5-uitslag-v1.md`.

**Keuze Chris: optie C — eerst de variatie meten.** Vóór een herstel wordt gemeten of de C107-uitkomst toeval is of structureel: 5 losse calls op C107, buiten de kwalificatie, voor ongeveer US$0,15. Er geldt een harde kostenstop van $0,50 en er is geen automatische herhaling. De uitkomst bepaalt de keuze tussen A en B.

**Niet nu gekozen:**
- A: direct een dienstregel;
- B: prompt /4;
- D: parkeren.

**Uitvoering.** Meetscript `goldset-voorbereiding/variatiemeting-c107-v1/variatiemeting.py`. Het gebruikt dezelfde keten als de v5-proef: dienst, profiel, `claude-opus-5`, prompt /3, contract /2, limieten per call en `use_cache=False`. De verstuurde payload is byte-gelijk aan die van C107 in v5. Manifest, akkoord en grootboek van de kwalificatie worden niet gebruikt. De meting telt niet als kwalificatie.

## Besluit 12 — smalle dienstregel (07-10-2026)

**Uitslag variatiemeting.** De 5 losse calls op C107 gaven 5 keer `review_required` / `insufficient_information` (juist). Met de v5-proef erbij is C107 op prompt /3 met contract /2 dus 6 keer beoordeeld: 5 keer goed en 1 keer `fail`. Die ene fout had functie `discretionary_decision_rule` en als enige grond de kern, bij een onbekende bedoeling. De fout is geen vast patroon, maar ook geen nul-kans (ongeveer 1 op 6; 95%-interval ongeveer 0,4–64%). Details: `goldset-voorbereiding/variatiemeting-c107-v1/uitslag-v1.md`.

**Keuze Chris: optie A — een smalle, deterministische dienstregel in het contract.**

- Geeft het model `fail`, is de bevestigde bedoeling onbekend en hebben alle passages die de fail dragen functie `discretionary_decision_rule` met als grond uitsluitend het veld `kern`, dan wordt de uitkomst `review_required` met reden `insufficient_information` in plaats van `fail`.
- Draagt minstens één passage de fail op een andere manier, dan blijft het `fail`. Voorbeelden: een `actor_prescription`, of een discretionaire beslisregel met grond uit bedoeling, context of bronpassage.
- **Een expliciet actorvoorschrift in de kern blijft `fail`, conform besluit 1.**
- De omzetting is zichtbaar in het document (`omzetting: "discretie_zonder_bedoeling"`) en nooit stil. Het bewaarde oordeel houdt het verdict `fail` van het model. Er komt geen pass-pad bij.
- Het resultaatcontract eist bij `insufficient_information` precies één gerichte vraag. Daarvoor geldt een vaste, invoeronafhankelijke vraag: `Is de bedoeling dat deze passage een begripskenmerk beschrijft of de actor een afweging voorschrijft?`
- Citaten en posities blijven zoals onder contract /2. De prompt blijft `def835-int02-prompt/3` (systeemprompt `da4a4112…`, ongewijzigd).

**Afgewezen:**
- B: fase 1 opnieuw draaien zonder wijziging;
- C: stoppen.

**Uitvoering.** Contract `def835-int02-assessment/3` in `src/domain/int02/contract.py`; contractdocument `docs/architectuur/contracts/int02_assessment_contract_v3.md` (v1 en v2 ongewijzigd). Bewaarde /1- en /2-documenten worden volgens hun eigen versie gecontroleerd en zijn daarna historisch, ook het in v5 bewaarde /2-document van C107.

Keuzes van de uitvoerder, ter bevestiging bij de review:
- altijd de vaste vraag, ook als het model zelf een vraag gaf; die blijft zichtbaar in het oordeel;
- de regel geldt alleen voor modeloordelen (actor `ai`).

Testen gebeurde TDD:
- rood: 52 gefaald;
- groen: 941 def835/int02-unittests geslaagd en 11 overgeslagen; de gerichte selectie 460 geslaagd;
- na de Codex-review (07-10, "commit verantwoord: ja", twee kleine punten verwerkt): 959 geslaagd en 11 overgeslagen;
- ruff en black schoon;
- een mutatiecontrole op vijf naïeve varianten.

Verslag met open punten en gevolgen voor manifest v6: `goldset-voorbereiding/dienstregel-v1/uitvoeringsverslag-claude-v1.md`.

**Vervolg:**
1. Onafhankelijke review van de diff (gedaan: Codex, 07-10).
2. Commit, waarbij de logs met `git add -f` worden toegevoegd.
3. Offline manifest v6. Daarin veranderen de hashes van `contract.py`, de dienst (alleen de docstring) en `runtime_contract.py` (alleen commentaar), en daardoor de identiteit en de proefmap. De systeemprompt en de payloads per geval blijven gelijk.
4. Nieuw exact akkoord van Chris op v6.
5. Daarna opnieuw alleen fase 1 (C105/C107/C112).

## Besluit 13 — manifest v6 en fase 1 (07-10-2026)

**Manifest v6.** v6 is offline aangemaakt (geen API-call, geen sleutel) op HEAD `8c6bf74d2` (contract `def835-int02-assessment/3` met de dienstregel van besluit 12, prompt `def835-int02-prompt/3`).

Verschil met v5:
- bestandshashes van `src/domain/int02/contract.py` (→ `9635f9c1…`), `src/services/validation/int02_assessment_service.py` (→ `c59e373a…`) en `src/toetsregels/runtime_contract.py` (→ `27e76bf9…`);
- `identiteit.proefmap` (`kwalificatieproef-v6`), `identiteit_sha256` (`90920d6c35337be48cacb58c0f8f01616200aab332915ddc1a960c62314def4b`) en het tijdstempel `aangemaakt`.

Alle 43 payloads zijn byte-gelijk aan v5; het payloadbestand verschilt alleen in de kopregel `identiteit_sha256`. Gelijk aan v5: gevallen, per geval de invoer, dataprompt en label, promptversie en systeemprompt, model, SDK, limieten, prijzen, criteria, fasevolgorde en protocol/norm.

- `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v6.json`: `37b8e36a46c30a3d62b579a0eaf2afc544a454d709c49030c5626fa318539e37`
- `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-payloads-v6.json`: `fb556f4c52221316859ac35ba58021f3213f8aef428eaa423a318c8cf76d1f36`
- `kwalificatie-gevallen-v1.json` ongewijzigd: `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`

**Akkoord Chris: alleen fase 1** (`--fase regressie`, C105/C107/C112, maximaal 3 calls); daarna stoppen en bespreken. Het akkoordbestand `kwalificatie-akkoord-v6.json` bevat net als bij v4 en v5 het protocolkader (43 calls, US$12), omdat de runner dat veldformaat eist; de beperking tot fase 1 is deze procesafspraak. Besluit 10 (v5) is hiermee vervangen.

**Sleutel.** Zoals bij v4 en v5 wordt de API-sleutel bij de run door de shell uit de `.env` van de hoofdcheckout gelezen en niet getoond; er komt geen `.env` in de werkboom.

## Besluit 14 — schema via API (07-10-2026)

**Uitslag v6.** Fase 1 van v6 stopte na de eerste call, op C105, met `invalid_output` (stopreden van de runner; 1 inferentie). C107 en C112 zijn niet gedraaid. Het model gaf voor C105 inhoudelijk het juiste oordeel: `fail`, passage "De medewerker laat de aanvrager toe.", functie `actor_prescription`, grond de bedoeling. Maar het zette in de passage een extra veld `reason`. Het gesloten contract weigert onbekende velden, dus het document werd `error`. Bron: `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v6/regressie-bundel.json` en `regressie-resultaat.json`.

**Keuze Chris: optie A — het antwoordschema via de API meesturen** (native JSON-schema-uitvoer, `output_config.format`). Het schema legt de bestaande gesloten uitvoervorm vast. Een extra veld zoals `reason` in een passage kan het model dan niet meer produceren.

**Afgewezen:**
- B: een optioneel extra veld in het contract toestaan;
- C: fase 1 opnieuw draaien zonder wijziging;
- D: stoppen.

**Haalbaarheidsonderzoek (alleen lezen, vóór de keuze).** De keten ondersteunt gestructureerde uitvoer al:
- AIServiceV2 heeft `response_schema` als opt-in, en `async_api` geeft het door;
- de Anthropic-adapter bouwt `output_config` alleen voor de gecontroleerde combinatie in `config.yaml` (`claude-opus-5`, `api.anthropic.com`, thinking `disabled`); anders weigert hij vóór verzending;
- INT-03 gebruikt deze route al (DEF-836);
- SDK 0.116.0 ondersteunt `output_config`, ook bij `count_tokens`.

Volgens de actuele Anthropic-documentatie (gelezen door de coördinator) gelden deze grenzen: `type`/`properties`/`required`/`enum`/`anyOf`, `additionalProperties: false`, geen min/maxLength, maximaal 24 optionele parameters en 16 union-velden. De grammatica geldt niet voor thinking; INT-02 heeft thinking uitgeschakeld.

**Route.**
- `ANTWOORDSCHEMA` en `ANTWOORDSCHEMA_SHA256` staan in `src/domain/int02/contract.py`. Het schema is exact de bestaande structuur, met gesorteerde enums, nullables via `anyOf` en alles verplicht en gesloten. `ground` is een unie van drie gesloten varianten die de koppeling veld → ref van de code volgen (Codex-review 07-10, P2). De hash is vastgepind: `72adfe74…511f17` (de eerste pin `2b1ac6a8…f96191` is vervangen).
- Contractversie blijft `def835-int02-assessment/3`, want de uitvoervorm is ongewijzigd. Alle code-controles blijven ongewijzigd: citaten, ref-koppeling, vraag, samenhang en de dienstregel.
- Promptversie wordt `def835-int02-prompt/4`: dezelfde tekst als /3 (systeemprompt `da4a4112…`) plus de schemaroute.
- De dienst doet het volgende:
  - controleert de schemahash vóór de aanroep;
  - stuurt het schema mee;
  - eist dat de AI-laag het verzonden schema bevestigt en precies één tekstblok meldt;
  - meldt een niet-ondersteunde combinatie apart, met de reden `structured_output_unsupported` en zonder verzending;
  - blijft bij `refusal` fail-closed.
- De runner accepteert alleen exact dit schema in `output_config` en telt het mee in de tokenmeting. Schemahash en capability staan in de identiteit. Er is geen beta-header.

Uitvoering en tests: `goldset-voorbereiding/schemaroute-v1/uitvoeringsverslag-claude-v1.md`.

**Vervolg:**
1. Onafhankelijke review van de diff.
2. Commit (de logs met `git add -f`).
3. Offline manifest v7. De payloads veranderen, want `output_config` komt erbij. Ook de promptversie, de bestandshashes en de routerdelen van de identiteit veranderen.
4. Nieuw exact akkoord van Chris op v7.
5. Daarna opnieuw alleen fase 1 (C105/C107/C112). Die run is meteen de live-rooktest van het schema: of de API het schema accepteert, blijkt pas dan.

## Besluit 15 — manifest v7 en fase 1 (07-10-2026)

**Uitslag v6 vastgelegd.** Fase 1 van v6: 1 call (C105), `invalid_output` door het extra veld `reason` in de passage (zie besluit 14), kosten $0,02649. Cijfers: `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v6-uitslag-v1.md`; het bewijs in `kwalificatieproef-v6/` is nu mee vastgelegd.

**Manifest v7.** v7 is offline aangemaakt (geen API-call, geen sleutel) op HEAD `2081899ea`: prompt `def835-int02-prompt/4` (tekst /3, systeemprompt `da4a4112…`, plus de schemaroute), antwoordschema `72adfe7428b67bf0fd999520581f0fc2cbe801101e1e8e6df300179405511f17`, contract `def835-int02-assessment/3`.

Verschil met v6:
- elke payload krijgt `output_config` (+1.636 bytes, voor alle 43 gevallen hetzelfde); zonder dat veld is elke payload byte-gelijk aan v6;
- `promptversie` `def835-int02-prompt/3` → `def835-int02-prompt/4`;
- bestandshashes van `src/domain/int02/contract.py` (→ `de4a9659…`), `src/services/validation/int02_assessment_service.py` (→ `cf2dde81…`) en `scripts/analysis/def835_int02_modelproef.py` (→ `2de199b6…`);
- `router.supports_structured_outputs: true` en `router.antwoordschema_sha256` (`72adfe74…`) erbij;
- `identiteit.proefmap` (`kwalificatieproef-v7`), `identiteit_sha256` (`1ba9794ff9432b5c05ad7cf123f086a1c53b84756c4d32bdcc3163cc83a426a3`) en het tijdstempel `aangemaakt`.

Gelijk aan v6: gevallen, per geval de invoer, dataprompt en label, systeemprompt, model, SDK, limieten, prijzen, criteria, fasevolgorde en protocol/norm.

- `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v7.json`: `872482f4f201b2c5a7e04e3a0dd6589f088518adb7af99f395da08f89ccfc84b`
- `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-payloads-v7.json`: `ee01d03bf1dd04af0c0b1b45b7ffced12a557ae5b2cf6c08a1ac7b91f022d289`
- `kwalificatie-gevallen-v1.json` ongewijzigd: `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`

**Akkoord Chris: alleen fase 1** (`--fase regressie`, C105/C107/C112, maximaal 3 calls); deze run geldt ook als live-rooktest van het schema. Daarna stoppen en bespreken. Het akkoordbestand `kwalificatie-akkoord-v7.json` bevat net als bij v4–v6 het protocolkader (43 calls, US$12), omdat de runner dat veldformaat eist; de beperking tot fase 1 is deze procesafspraak. Besluit 13 (v6) is hiermee vervangen.

**Sleutel.** Zoals bij v4–v6 wordt de API-sleutel bij de run door de shell uit de `.env` van de hoofdcheckout gelezen en niet getoond; er komt geen `.env` in de werkboom.

## Besluit 16 — contract /4 met bronfuncties (07-10-2026)

**Uitslag fase 2 van v7 (ontwikkeling).** Mechanisch niet geslaagd: 18/24 juist (criterium minimaal 21/24). Alle zes gevallen met label `review_required` waren fout (0/6): vijf werden `pass` (G042, G045, G060, G070, G076) en één `fail` (G047). Daarmee 5 onterechte passes; manifest v7 had voor ontwikkeling `max_false_pass: null`, zodat de runner ze niet als reden telde, terwijl de procesafspraak maximaal 0 was. Het model gaf nergens `insufficient_information`. Details: `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v7-ontwikkeling-uitslag-v1.md`.

**Keuze Chris: optie A — contract /4 met gestructureerde bronfuncties**, volgens `goldset-voorbereiding/bronfuncties-ontwerp-v1.md`. Het model vult per passage een `kernvorm` in en per grondbron (bevestigde bedoeling, elk contextitem, elke bronpassage) een `function` met letterlijk citaat waar vereist, en als laatste zijn eigen `verdict`. De dienst leidt de uitkomst mechanisch af.

**De zeven keuzes (alle zeven = het advies in het ontwerp):**

1. **1B** — de bedoeling mag een bronconflict alleen naar gebrek (`fail`) beslechten, nooit naar `pass`.
2. **2A** — de dienst beslist: de regel uit de bronfuncties is leidend. Een afwijking van het modeloordeel is zichtbaar in het document (omzettingsveld, en het modeloordeel blijft bewaard). Dit kan ook `fail` → `pass` opleveren als alle bronnen "kenmerk" zeggen.
3. **3A** — één voorschrift-bron zonder tweede signaal → `review_required`.
4. **4A** — bij een door de dienst afgeleide review een vaste vraag; bronnen en citaten staan in de reden.
5. **5A** — alle bronnen zwijgen, beschrijvende kern (`descriptive_act`) en bedoeling onbekend → `review_required`.
6. **6A** — een eigen bronfunctie `not_a_criterion`; die telt als tweede signaal en als conflict met `criterion`.
7. **7A** — fase 1 en 2 van v8 zijn een consistentietoets (de regel is ontworpen met deze 27 gevallen in zicht); de hold-out, met een apart akkoord, is het enige onafhankelijke bewijs.

**Runner.** In de kwalificatieprotocol-constanten van `scripts/analysis/def835_int02_modelproef.py` wordt voor ontwikkeling `max_false_pass` 0 (was `null`). Regressie en hold-out blijven 0.

**Normatieve verschuivingen (expliciet aanvaard):**

- **Besluit 1 wordt smaller voor bronnen.** Eén bronvoorschrift draagt een `fail` niet meer zelfstandig. Het draagt alleen als de kern het voorschrift in voorschrijvende vorm overneemt (`obligation_form` of `discretion_form`), een andere bron toont dat de inhoud geen kenmerk is (`not_a_criterion`), of de bevestigde bedoeling het voorschrift bevestigt. Anders volgt `review_required`. Een zelfstandig voorschrift in de kern zelf (`instruction`) blijft altijd `fail`.
- **Afwijking van besluit 12 ("geen pass-pad").** Onder 2A kan de dienst een `fail` van het model omzetten naar `pass` als de bronnen eensluidend "kenmerk" zeggen en geen passage een gebrek of review oplevert. De dienstregel discretie zonder bedoeling gaat op in de laatste tak van de beslisregel (alle grondbronnen zwijgen).
- **Vaste vraag.** Bij een door de dienst afgeleide review is de vraag vast en invoeronafhankelijk; een vraag van het model blijft alleen zichtbaar in het bewaarde oordeel.
- **Strijdige betekenisgrond (T-tekst)** wordt mechanisch: een beschrijvende bron naast een voorschrijvende of `not_a_criterion`-bron bij dezelfde passage is een conflict. Het model kan dat conflict niet meer zelf "niet relevant" verklaren.

**Uitvoering.** Contract `def835-int02-assessment/4`, prompt `def835-int02-prompt/5` (de promptbuilder wijzigt op deze opdracht), nieuw antwoordschema met nieuwe pin, runner `max_false_pass` 0 voor ontwikkeling. Bewaarde /1-, /2- en /3-documenten blijven volgens hun eigen versie controleerbaar en worden historisch. Verslag: `goldset-voorbereiding/bronfuncties-v1/uitvoeringsverslag-claude-v1.md`.

**Vervolg:** onafhankelijke review van de diff, commit, offline manifest v8 (nieuwe contract-, prompt-, schema- en payloadhashes; ontwikkeling `max_false_pass` 0; gevallen ongewijzigd), akkoord v8 van Chris, daarna fase 1 en pas na een afzonderlijk akkoord fase 2. De hold-out vraagt opnieuw een eigen akkoord.

## Besluit 17 — beslissende modelonzekerheid blokkeert een afgeleide pass (07-10-2026)

**Aanleiding.** Open punt 1 uit het uitvoeringsverslag van contract /4. Onder 2A beslist de dienst. Daardoor werd een geval toch `pass` als het model `uncertainty: decisive` meldde maar alle bronnen "kenmerk" zeiden en de dekking volledig was. Bijvoorbeeld:
- het model geeft `insufficient_information` en de dienst maakt er `pass` van ("review → pass");
- het model geeft `fail` met beslissende twijfel en de dienst maakt er `pass` van.

Dat botste met de T-tekst: bij twijfel volgt review. De Codex-review (read-only, eindoordeel "nog niet commitbaar") legde dit punt aan Chris voor.

**Keuze Chris: optie A.** Meldt het model beslissende onzekerheid (`uncertainty = decisive`) en zou de dienst anders `pass` afleiden, dan wordt de uitkomst `review_required` / `insufficient_information`. Daarbij geldt:
- **Vaste vraag** (analoog aan 4A): `VRAAG_FUNCTIE`. De reden noemt de dragende kenmerkpassage en haar grond.
- **Modeloordeel zichtbaar:** het eigen verdict, de onzekerheid en de eigen vraag van het model blijven ongewijzigd in het bewaarde oordeel.
- **Eigen afleidingscode** `model_beslissend_onzeker`. Wijkt de status af van het modelverdict (een model-`fail` met twijfel en een kenmerkgrond), dan is dit ook de `omzetting`.
- **Gebrek gaat voor:** een afgeleide `fail` blijft `fail`. Een eigen reviewgrond (conflict, bronvoorschrift, open bron, onvolledige dekking) houdt haar eigen code.
- **Plaats:** vlak vóór de laatste pass-tak van de beslisregel.
- **Schema:** ongewijzigd. `uncertainty` zat er al in, dus de pin blijft `d3ad029e…`.

**Gevolg (bevinding Codex).**
- Het verandert de paper test niet (27/27 met 6/6 review) en ook de v7-passes niet.
- Het kan tot **13 passes** raken als het model twijfel meldt: C112, G007, G011, G015, G019, G021, G027, G030, G037, G039, G041, G046 en G055.
- Dat is de bewust aanvaarde prijs van "bij twijfel review": een onterechte review is goedkoper dan een onterechte pass, en dat past bij `max_false_pass` 0.

**Normatieve verschuiving.** Besluit 17 begrenst de fail → pass-omzetting van 2A. Een model-review kan onder /4 nooit meer `pass` worden, want `insufficient_information` vereist altijd `decisive`.

**Uitvoering.**
- Contract `def835-int02-assessment/4` (zelfde versie, nog ongecommit) in `src/domain/int02/contract.py`, in `_leid_af`.
- Contractdocument `docs/architectuur/contracts/int02_assessment_contract_v4.md`.
- Tests in `tests/unit/domain/test_def835_int02_bronfuncties.py`, sectie H.
- De mutant `onzekerheid_genegeerd_17` in de mutatiecontrole.
- Verslag: `goldset-voorbereiding/bronfuncties-v1/uitvoeringsverslag-claude-v2.md`.

## Besluit 18 — manifest v8, fase 1 en 2 als consistentietoets (08-10-2026)

**Manifest v8.** Offline aangemaakt (geen API-call, geen sleutel) op HEAD `ca32b4f74` (contract /4, besluit 16 en 17, na drie Codex-reviewrondes met eindoordeel commitbaar). Verschil met v7:
- `contractversie` `def835-int02-assessment/4` (nieuw veld in de identiteit);
- `promptversie` `def835-int02-prompt/4` → `def835-int02-prompt/5`; daardoor per geval nieuwe systeemprompt-, dataprompt- en payloadhashes;
- `router.antwoordschema_sha256` `72adfe74…` → `d3ad029e24b6b96242f4730686d3a4ebfebd9f46993607e41016761bc7fce715`;
- `criteria.ontwikkeling.max_false_pass` `null` → `0`;
- bestandshashes van `contract.py`, `int02_assessment_service.py`, `runtime_contract.py` en de runner;
- `proefmap` (`kwalificatieproef-v8`), `identiteit_sha256` (`86daaad9b746d8ce1a1d34a0dbe9bce7fa8746e19076a81b45e747cf8281b2f7`) en `aangemaakt`.

Gelijk aan v7: gevallen en fasen, gevallenmanifest, model, SDK-versies, limieten, prijzen, protocol en norm.
- `kwalificatie-manifest-v8.json`: `d5a4de426cbea46f9e7547e749a40e448bdf57232f0d053e21388de6ac1bf8fa`
- `kwalificatie-payloads-v8.json`: `52ccd4ab7a93d7a1f4c20e42115034a310813dcc8a4247dba91625d12a57d934`
- `kwalificatie-gevallen-v1.json` ongewijzigd: `af1ab46ce22c51308a58738bb7e91534dd67a2b2454c76ee2340e4e2037c6953`

**Akkoord Chris: fase 1 en, als die slaagt, fase 2.** Fase 1 (`--fase regressie`, 3 calls, ± US$0,15), daarna fase 2 (`--fase ontwikkeling`, 24 calls, ± US$1,20, `max_false_pass` 0). Beide gelden als consistentietoets (keuze 7A): de bronfuncties en de papieren toets zijn op deze zichtbare gevallen ontworpen. De hold-out blijft dicht en vraagt een eigen akkoord. Het akkoordbestand `kwalificatie-akkoord-v8.json` bevat net als bij v4–v7 het protocolkader (43 calls, US$12).

**Gitleaks-uitzondering 18.** Net als bij v7 meldde de hook 1 bevinding: r113 van manifest v8, de SHA-256 van `src/utils/async_api.py` (byte-gelijk aan r112 van v7). Uitzondering 18 volgt exact de constructie van 17 (pad én volledige regel, alleen `generic-api-key`); toelichting in `gitleaks-metadata-akkoord-v2.md`. Daarna gaf de hook 0 bevindingen; `make test-secret-scan` met de gepinde gitleaks 8.29.1 is groen. Kopie van de oude staat: `backups/def835-werk/gitleaks.toml.voor-uitzondering-18` (niet in git).

**Sleutel.** Zoals bij v4–v7 leest de shell de API-sleutel bij de run uit de `.env` van de hoofdcheckout, zonder hem te tonen; er komt geen `.env` in de werkboom.

## Besluit 19 — kaal bron-ID en prompt /6 (08-10-2026)

**Uitslag v8 (consistentietoets 7A, geen onafhankelijk bewijs).**
- Fase 1: 3/3 juist, US$0,11.
- Fase 2: gestopt na 22 van de 24 gevallen (stopreden `invalid_citation` bij G060; G070 en G076 niet gedraaid). 19/22 juist, 1 onterechte pass (G045) en 1 citaatfout (G060). Pass 12/12, fail 5/6, review 2/4. Ter vergelijking v7: 18/24, 5 onterechte passes, review 0/6.
- Cumulatief US$1,07 (conservatief, 25 calls).
- Details: `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v8-uitslag-v1.md`.

**Diagnose (Codex, offline replay, bevestigd).**
- **G060:** het model gebruikte de sleutels "B1" en "B2" in plaats van "bron/B1" en "bron/B2". De citaten waren exact, uniek en betekenisdragend. Met de juiste sleutels volgt `review_required` via `conflict`: het juiste label.
- **G045:** onterechte pass. Het model las B1, die alleen dezelfde dubbelzinnige "is te"-zin herhaalt, als `criterion`. Het ontwerp verwacht `unclear`, met `review_required` / `bronnen_open` als gevolg.
- **G050:** label fail, uitkomst `review_required` door een bronconflict. Dat is de veilige richting; er wordt niets aan gedaan.

**Keuze 1 (G060): optie A — de dienst accepteert een kaal bron-ID.**
- Alleen in de /4-route; /1–/3 blijven ongemoeid.
- Een bronfunctie met `bron` "B1" geldt als "bron/B1" als precies één bron het ID B1 heeft en "B1" zelf geen geldige sleutel is. De uitvoering sluit daarnaast gereserveerde sleutelvormen uit (`bedoeling`, `<contextveld>/…`, `bron/…`), zodat een bron-ID met zo'n vorm nooit dubbelzinnig wordt gelezen.
- Het opgeslagen document bevat de canonieke sleutel; de hercontrole blijft consistent.
- Een onbekend ID ("B9") en elke andere afwijkende sleutel blijven `grond_niet_herleidbaar`.
- De alias komt niet in de prompt.
- De contractversie blijft `def835-int02-assessment/4`: de regel verruimt alleen wat geldige invoer is, en geen bestaand /4-document wordt anders beoordeeld (onderbouwing in het contractdocument v4, "Besluit 19").

**Keuze 2 (G045): optie A — de prompt wordt verduidelijkt.**
- Nieuwe promptversie `def835-int02-prompt/6`.
- Eén algemene, casusvrije zin bij de betekenis van de bronfuncties: herhaalt een grondbron alleen dezelfde formulering als de passage, zonder te laten zien of die inhoud bepaalt wat tot het begrip behoort of een handeling voorschrijft, dan is die herhaling geen bewijs voor `criterion`; kies dan `unclear`.
- Verder wijzigt de prompt niet. Het schema blijft ongewijzigd (`d3ad029e…e715`).

**Uitvoering.** Contract en prompt in `src/domain/int02/contract.py` en `src/services/validation/int02_assessment_service.py`; contractdocument `docs/architectuur/contracts/int02_assessment_contract_v4.md`. Verslag met testuitkomsten en hashes: `goldset-voorbereiding/bronfuncties-v1/uitvoeringsverslag-claude-v3.md`.

**Vervolg.**
1. Onafhankelijke review van de diff.
2. Commit, na akkoord.
3. Offline manifest v9: promptversie `/6`, nieuwe systeemprompt-, payload- en bestandshashes; contractversie /4 en schema ongewijzigd; gevallen ongewijzigd.
4. Daarna opnieuw fase 1 en 2, met een apart akkoord van Chris op v9. Ook dat blijft een consistentietoets (7A). De hold-out vraagt opnieuw een eigen akkoord.

## Besluit 20 — manifest v9, fase 1 en 2 opnieuw (08-10-2026)

**Manifest v9.** Offline aangemaakt op HEAD `10c19e21a` (besluit 19: kaal bron-ID als alias, prompt /6). Verschil met v8: `promptversie` `/5` → `def835-int02-prompt/6` (daardoor per geval nieuwe systeemprompt- en payloadhashes), bestandshashes van `contract.py` en `int02_assessment_service.py`, `proefmap` (`kwalificatieproef-v9`), `identiteit_sha256` (`757bc2a1c1ebce80307289a95d4d33d419f5d94b021f61920b74af3f8c4b6456`) en `aangemaakt`. Gelijk aan v8: contractversie /4, antwoordschema `d3ad029e…`, gevallen en fasen, model, SDK, limieten, criteria (`max_false_pass` 0 voor ontwikkeling), protocol en norm.
- `kwalificatie-manifest-v9.json`: `30129863ebf6a379fd5eb4d667ccb22720e7e35129f5683acf8437437e98d09d`
- `kwalificatie-payloads-v9.json`: `c189daa7dfce7dd34a9c904f58e881aab00421c1ef8aef860eae15b685ca7007`

**Akkoord Chris: fase 1 en, als die slaagt, fase 2** (consistentietoets 7A, hold-out dicht). Akkoordbestand `kwalificatie-akkoord-v9.json` met hetzelfde protocolkader als v4–v8.

**Gitleaks-uitzondering 19.** Zelfde bevinding als 18 (r113, SHA-256 van `src/utils/async_api.py`), nu in manifest v9; blok 19 is mechanisch afgeleid van blok 18. Hook daarna 0 bevindingen; `make test-secret-scan` met de gepinde gitleaks groen. Kopie oude staat: `backups/def835-werk/gitleaks.toml.voor-uitzondering-19` (niet in git).

## Besluit 21 — eerst de variatie meten (08-10-2026)

**Uitslag v9 (consistentietoets 7A, geen onafhankelijk bewijs).**
- Fase 1: 3/3 juist, US$0,11.
- Fase 2: gestopt na 17 van de 24 gevallen met stopreden `kritieke_false_pass`; 15/17 juist. G052 en de zes reviewgevallen (G042, G045, G047, G060, G070, G076) zijn niet gedraaid.
  - **G050** (label fail) kreeg `pass`. Kernvorm `discretion_form`. Het model labelde B1 en B2 bij P1 als `derivation` en bij P2 als `criterion`; zonder voorschrijvende bron volgt `bronnen_beschrijvend`. In v8 zag het model bij dezelfde invoer (prompt /5) nog een conflict (B1 `discretionary_decision_rule`, B2 `criterion`).
  - **G030** (label pass) kreeg `review_required` via `conflict`: B1 `criterion`, B2 `actor_prescription`. In v8 was B2 `criterion` en de uitkomst `pass`.
- Cumulatief US$0,86 (conservatief, 20 calls).
- Vergelijking onterechte passes: v7 5, v8 1 (G045), v9 1 (G050).
- Details: `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v9-uitslag-v1.md`.

**Lezing.** De kern is de modelvariatie in het labelen van bronnen. De 15 andere gevallen die in v8 én v9 draaiden, kregen dezelfde bronfuncties en uitkomst. G050 en G030 verschillen alleen doordat het model één bron anders labelde, en de mechanische regel volgt die bronfunctie. Elke run had één onterechte pass, steeds bij een ander geval. Of dat incidenteel of structureel is, laat één run per versie niet zien.

**Keuze Chris: optie B — eerst de variatie meten.** De 24 ontwikkelgevallen draaien twee keer extra met v9 (prompt /6, schema `d3ad029e…`), voor ongeveer US$2. Er wordt niets gerepareerd: geen wijziging in contract, prompt, dienst of runner.

**Afgewezen:**
- A: O2 parkeren;
- C: een veiligheidsregel voor `discretion_form`.

**Buiten het kwalificatieprotocol.** De meting is geen kwalificatie en geen herhaling van een kwalificatiefase. Er komt geen nieuw manifest of akkoord, en het grootboek van v9 wordt niet gebruikt of aangevuld. Manifest v9 dient alleen als ijkpunt: het script controleert dat promptversie, schemahash, ketenbestanden en per geval de payload gelijk zijn aan v9. De hold-out blijft dicht en wordt niet gelezen. Het v9-bewijs blijft ongewijzigd.

**Uitvoering.** Script `goldset-voorbereiding/variatiemeting-v9/variatiemeting_v9.py`, naar het patroon van de variatiemeting C107 (besluit 11). Kenmerken:
- dezelfde keten als de runner;
- standaard een droge run;
- hard kostenplafond van US$3,00 en maximaal 48 calls;
- per call een regel met bronfuncties en het ruwe antwoord;
- een samenvatting per geval over v9-fase 2 en de herhalingen.

Opzet en startcommando: `goldset-voorbereiding/variatiemeting-v9/opdracht-en-opzet-v1.md`. De coördinator start de live run met de sleutel uit de hoofdcheckout.

## Besluit 22 — R1 en R2: discretievorm of open bron naast kenmerk is nooit pass (08-10-2026)

**Uitslag variatiemeting v9** (48 calls, US$2,17 conservatief; buiten het kwalificatieprotocol, consistentietoets 7A). Details: `goldset-voorbereiding/variatiemeting-v9/uitslag-v1.md` en `live-v1/samenvatting.md`.
- h1 21/24 juist, h2 22/24 juist; v9-fase 2 had 15/17.
- Per run 1 à 2 onterechte passes: h1 G050 en G060, h2 G060 (v9-fase 2: G050). Kritieke false pass: h1 G050 (v9-fase 2 ook G050), h2 geen.
- Stabiliteit: 20/24 stabiel (opgave Chris). `samenvatting.md` telt 22/24 gevallen met dezelfde status in alle runs (wisselend: G030 en G050); het verschil is niet uit de samenvatting te herleiden. Wisselende bronfuncties bij 7 gevallen.

**Diagnose (wat-als van Codex, offline, 93 bewaarde antwoorden uit v8, v9 en de meting).** Onterechte passes ontstaan via twee combinaties:
- **G050:** kernvorm `discretion_form` met bronnen die `derivation`/`criterion` zeggen → `bronnen_beschrijvend` → pass;
- **G060 onder /6:** B1 `unclear` en B2 `criterion` → pass, omdat het ontwerp zegt "O naast B of G telt niet".

| Variant | Onterechte passes | Kritiek | Terechte pass verloren |
|---|---|---|---|
| Nulmeting | 5 | 2 | 0 extra |
| R1 + R2 | 1 | 0 | 0 extra |

De ene die overblijft is G045 in v8 (B1 `criterion`, B2 zwijgt), die sinds prompt /6 goed gaat.

**Keuze Chris: R1 + R2, alleen in de route van bronfuncties.**
- **R1.** Bevat een passage kernvorm `discretion_form`, dan wordt de dienstuitkomst nooit pass: anders review met afleiding `discretie_nooit_pass` en de vaste vraag van besluit 12. Een afgeleide fail blijft fail.
- **R2.** Heeft een passage een grondbron `unclear` naast een grondbron `criterion`/`derivation` en zou de uitkomst anders pass zijn, dan review met afleiding `onduidelijk_naast_kenmerk` en `VRAAG_FUNCTIE`. Een fail blijft fail.
- **Volgorde:** gebrek → bestaande reviewgronden (afgeleide reviewpassage, onvolledige dekking) → R1 → R2 → besluit 17 → pass. Alleen actor `ai`.
- **Omzetting zichtbaar:** was het modelverdict pass (of fail), dan staat de code in `omzetting`; het modeloordeel blijft bewaard.
- **Contractversie /5** (`def835-int02-assessment/5`), met versiebewuste hercontrole: een bewaard /4-document wordt volgens /4 hercontroleerd en is daarna historisch. Reden: R1/R2 veranderen de afleiding; onder /4 zou een eerder geldig /4-pass-document met zo'n combinatie bij hercontrole als `error` uitvallen. Schema en prompt ongewijzigd.
- **Ontwerp:** de regel "O naast B of G telt niet" vervalt voor de pass-richting (wijzigingsnotitie in `goldset-voorbereiding/bronfuncties-ontwerp-v1.md`).

**Kanttekening.** Dit is een consistentietoets: R1 en R2 zijn mede op G050 en G060 gemaakt, en de wat-als gebruikt dezelfde zichtbare gevallen. Alleen de hold-out geeft onafhankelijk bewijs.

**Uitvoering.** `src/domain/int02/contract.py`; contractdocument `docs/architectuur/contracts/int02_assessment_contract_v5.md` (v4 blijft ongewijzigd als historische versie). Verslag met testuitkomsten, wat-als-replay en hashes: `goldset-voorbereiding/bronfuncties-v1/uitvoeringsverslag-claude-v4.md`.

## Besluit 23 — manifest v10, laatste run van dit onderdeel (08-10-2026)

**Manifest v10.** Offline aangemaakt op HEAD `7b7a6262b` (besluit 22: R1+R2, contract /5). Verschil met v9 uitsluitend: `contractversie` `/4` → `def835-int02-assessment/5`, bestandshash `contract.py` (`195cb777…`), `proefmap` (`kwalificatieproef-v10`), `identiteit_sha256` (`843d9126970bf9569f2448d50f12eb553d109c44e1784402d9c5df51a98fd350`) en `aangemaakt`. Prompt /6, schema `d3ad029e…`, payloads, gevallen, criteria en protocol byte-gelijk aan v9.
- `kwalificatie-manifest-v10.json`: `e45f97ff213a0585e47aba10406b2a076fc8f22e2fb219af0cf4dea2af6050ae`
- `kwalificatie-payloads-v10.json`: `7116930645b82bab9ce5717756ec9d235c9e0272b7f8bd093024449c84d7274e`

**Akkoord Chris: fase 1 en, als die slaagt, fase 2** (consistentietoets 7A, hold-out dicht). **Stopafspraak:** dit is de laatste run van dit onderdeel; daarna wordt de uitslag vastgelegd en stopt de iteratie op O2, ongeacht de uitkomst. Vervolgkeuze daarna: hold-out (apart akkoord) of O2 parkeren.

**Gitleaks-uitzondering 20.** Zelfde bevinding als 18/19 (r113, SHA-256 `src/utils/async_api.py`), nu in manifest v10; blok 20 mechanisch afgeleid van blok 19; hook daarna 0 bevindingen. Kopie oude staat: `backups/def835-werk/gitleaks.toml.voor-uitzondering-20` (niet in git).

## Besluit 24 — technische herstart van de laatste run (v11, 08-10-2026)

**Aanleiding.** Fase 1 van v10 slaagde (3/3, US$0,113). Fase 2 van v10 stopte na 6 gevallen op `timeout` bij G039 (15:22 UTC), precies toen de Mac de verbinding verloor: een infrastructuurstoring, geen modeluitkomst. Uitkomsten tot dan: G011, G015, G019, G027 juist (pass); G030 pass → review_required (conflict, veilige richting); G039 error (timeout). Kosten v10 ±US$0,56 (conservatief, cumulatief). Zie `kwalificatieproef-v10-uitslag-v1.md`.

**Keuze Chris: A — eenmalig herstarten.** Manifest v11 is identiek aan v10 op `proefmap`, `identiteit_sha256` en `aangemaakt` na (mechanisch gecontroleerd); geen codewijziging. Run fase 1 en fase 2 met `caffeinate` zodat de Mac niet slaapt. Dit telt als dezelfde laatste run (stopafspraak besluit 23), geen nieuwe iteratie.
- `kwalificatie-manifest-v11.json`: `bd8047f08d29e2cc7aca311587fafe6cf25672d33284f2b810a8dee01823187b` (identiteit `3ae2702c933815ea229d7bfa3b53eabbd2abd759c2d971728be2573a26b5cc64`)
- `kwalificatie-payloads-v11.json`: `d8f8e9225f1c4b0e4288ac2344bec4423a30bd8e9429d64e92eb5c3018e33d9d`

**Gitleaks-uitzondering 21.** Zelfde bevinding als 18–20 (r113, SHA-256 `src/utils/async_api.py`) in manifest v11; blok 21 mechanisch afgeleid van blok 20.

