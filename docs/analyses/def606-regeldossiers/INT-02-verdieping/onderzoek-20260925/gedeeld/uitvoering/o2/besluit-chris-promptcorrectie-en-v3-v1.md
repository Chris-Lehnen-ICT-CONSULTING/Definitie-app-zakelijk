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
