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
