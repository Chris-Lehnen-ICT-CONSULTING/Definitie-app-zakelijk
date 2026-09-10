# Instructiepublicaties (ALG-399)

Alle projectinstructies van deze repository komen uit één bron: de blokken in
`instructions/blocks/`. Wat daaruit ontstaat en waar het landt, staat vast in
`manifest.json` (welke publicaties) en `outputs.json` (welke bestanden).

**Bewerk nooit een gegenereerd bestand.** Pas het bronblok aan en genereer
opnieuw; de CI-poort ziet handmatige wijzigingen.

## Herkomst van het gereedschap

`render-instructions.py`, `check-instruction-publications.py` en
`lib/instruction_publication.py` zijn overgenomen uit het kandidaatpakket
`ALG399-bronvoorbereiding-20260909/repository-integration-v1/definitie`.

Ze zijn **niet byte-gelijk** aan die bron: bij de aansluiting zijn ze
geformatteerd volgens de bestaande projectgates (Ruff met de import-sortering uit
`[tool.ruff.lint.isort]`, daarna Black). Die delta betreft **uitsluitend
formattering en importvolgorde** — geen gedrag. De originelen en het bewijs van
AST-gelijkheid staan onder
`/private/tmp/ALG399-definitie-toolformattering-20260910/`.

Er is bewust geen lintuitzondering gemaakt: de pre-commit-config draait Ruff en
Black op alle Python (`types: [python]`), en een uitzondering zou de bestaande
kwaliteitsgate veranderen.

## Regenereren

De renderer schrijft één publicatie naar stdout. Draai hem vanuit de repo-root,
zodat hij zijn eigen `scripts/lib` kan importeren (gebruik daarom géén `-I`):

```bash
python -B scripts/render-instructions.py \
  --manifest instructions/manifest.json \
  --publication claude-cli.definitie > CLAUDE.md
```

De volledige lijst publicatie → bestand staat in `outputs.json`. Negen bestanden,
elf publicatiecontroles (twee bestanden dienen elk twee omgevingen):

| Bestand | Publicatie(s) |
|---|---|
| `CLAUDE.md` | `claude-cli.definitie` |
| `AGENTS.md` | `codex-cli.definitie`, `codex-app.definitie` |
| `instructions/generated/cowork-project.md` | `cowork.definitie` |
| `.claude/rules/patterns.md` | `claude-native.project.patterns` |
| `.claude/rules/project-rules.md` | `claude-native.project.project-rules` |
| `.claude/rules/streamlit-patterns.md` | `claude-native.project.streamlit-patterns` |
| `docs/guidelines/CLAUDE.md` | `claude-cli.guidelines` |
| `docs/guidelines/AGENTS.md` | `codex-cli.guidelines`, `codex-app.guidelines` |
| `instructions/generated/cowork-guidelines.md` | `cowork.guidelines` |

De renderer kan ook één bestand toetsen zonder het te overschrijven:

```bash
python -B scripts/render-instructions.py \
  --manifest instructions/manifest.json \
  --publication claude-cli.definitie --check CLAUDE.md
```

## Controleren

```bash
python -B -E -S scripts/check-instruction-publications.py --require-tracked
```

De checker toetst alle bestanden uit `outputs.json` op exacte bytes. Met
`--require-tracked` eist hij daarnaast dat de publicaties, de bronblokken,
`manifest.json`, `outputs.json` en het gereedschap zelf in de Git-index staan.
Hij gebruikt alleen de standaardbibliotheek.

## Tracking en CI

Sinds de ALG-399-trackingmigratie zijn de publicaties **getrackte projectoutput**.
Een schone clone bevat daarmee alle instructies; er blijft geen handgemaakt of
ongetrackt instructiebestand nodig. `AGENTS.md` in de root hoort daar sindsdien
bij en staat om die reden op de allowlist van `scripts/ci/check_root_allowlist.sh`.

Twee poorten bewaken dit:

- **CI** (`.github/workflows/ci.yml`) draait de checker met `--require-tracked`
  vóór de dependency-installatie, zodat een falende installatie de poort niet
  maskeert. De bestaande gates (`make grep-check`, `make test-tool-gates`,
  `make test-acceptance`) blijven onverkort staan.
- **Rootallowlist** (`scripts/ci/check_root_allowlist.sh`, ook als pre-commit
  hook) weigert getrackte of gestagede rootbestanden buiten de allowlist.

`tests/unit/scripts/test_instruction_publications.py` toetst verplichte output,
drift, het staged/tracked-contract en de koppeling met de rootguard.

## Native Claude-regels: verwijzing, geen tweede beleid

De bestanden onder `.claude/rules/` zijn na de migratie **gegenereerde
verwijzingen** naar `CLAUDE.md`. Ze bevatten bewust geen eigen normtekst meer:
twee versies van hetzelfde beleid lopen uiteen. De normtekst — inclusief de
rootregel — staat in `instructions/blocks/definitie.policy.md` en daarmee in de
gegenereerde `CLAUDE.md`.

Wie een projectregel wil wijzigen, past dus het bronblok aan; de verwijzing zelf
is geen bewerkbaar document.

## Oorspronkelijke bestanden

`source-archives/` bewaart de zes instructiebestanden zoals ze vóór de migratie
bestonden, inclusief de destijds ongetrackte `AGENTS.md` uit de root. Dit is
**inerte opslag**: niets leest het bij het renderen of controleren.

`source-archives/index.json` is de gezaghebbende koppeling. Per oorspronkelijk
pad legt het de `sha256` van de originele bytes vast plus de archiefnaam. Die
archiefnamen zijn padloos gemaakt (`/` wordt `__`, een leidende punt wordt
`dot`), zodat het archief geen `.claude/rules`-mappenstructuur nabouwt die op een
echte instructielocatie lijkt. De bestandsnaam is daarmee een label; de
bronidentiteit blijft de sleutel plus de hash in `index.json`.
