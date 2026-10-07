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
