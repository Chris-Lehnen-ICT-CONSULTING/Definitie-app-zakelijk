# DEF-835 — mergecorrectie cwd-assertie, Claude-verslag v1

29 september 2026 · Claude Code CLI-uitvoerder. Werkboom `DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, HEAD `ebe9c1b7c26ffe6040bffb66db4937b932406dc8`.

Alleen `tests/unit/validation/test_def835_int02_modelproef.py` is gewijzigd. De runner, productiecode en de werkbomen van anderen zijn niet aangeraakt. Er zijn geen livecalls gedaan, niets is verwijderd en niets is gestaged of gecommit.

## Oorzaak

De canonieke unitgate (`bewijs/mergevoorbereiding-v1/unitgate.log`: 8713 passed, 1 failed, 86 skipped) faalde op één test: `test_live_keten_drie_tellingen_drie_inferenties_en_exacte_usage`, regel 380, `assert Path.cwd() == ROOT`.

- `scripts/testing/run_profile.py` start pytest bewust vanuit een tijdelijke werkmap (`subprocess.Popen(..., cwd=str(werkmap))`, regel 844).
- De runner herstelt in `_proefomgeving` de oorspronkelijke map correct: `vorige = Path.cwd()` en in `finally` `os.chdir(vorige)`, op `scripts/analysis/def835_int02_modelproef.py` regels 891–907.
- De test nam ten onrechte aan dat de oorspronkelijke map altijd de repository is. Het defect zat in de test, niet in de runner.

## Correctie (alleen de test)

- De bestaande test-ID blijft behouden en is geparametriseerd over `startmap`:
  - `repository`: `monkeypatch.chdir(ROOT)`;
  - `buiten-repository`: `monkeypatch.chdir(tmp_path/"werkmap")`, met een assertie dat die map buiten ROOT ligt.
- `oorspronkelijk = Path.cwd()` wordt vastgelegd vóór de run. De eindassertie is nu `Path.cwd() == oorspronkelijk` in plaats van `== ROOT`.
- Er is één assertie bijgekomen: `Path(verzoek["cwd"]) != oorspronkelijk`. De keten draait dus in een andere, tijdelijke map.
- De bestaande `Path(verzoek["cwd"]) != ROOT` blijft staan, net als alle andere asserties: 3 tellingen en 3 inferenties, exacte usage, payloadhash, headers, authenticatie, kosten, sleutelprivacy en het resultaatbestand. Geen assertie is verwijderd of verzwakt.

Diff: `bewijs/mergevoorbereiding-v1/merge-cwd-diff-v1.patch` (SHA-256 `b79f364d…3fef3`).

## Bewijs (alles onder `bewijs/mergevoorbereiding-v1/`)

Alle runs zijn offline gedraaid, met neutrale providersleutels (`env -u ANTHROPIC_API_KEY -u OPENAI_API_KEY DEFINITIE_DISABLE_DOTENV=1`), de bestaande offline-bootstrap via `tests/conftest.py`, en vanuit een verse tijdelijke cwd onder `/tmp`, buiten de repository.

| Stap | Bestand | Uitkomst |
| --- | --- | --- |
| Herstelkopie | `merge-cwd-herstel-v1/test_def835_int02_modelproef.py.herstel` | SHA `60b2c420…b79e`, gelijk aan HEAD |
| Rood (oude test, tijdelijke cwd) | `merge-cwd-red-v1.log` | 1 failed, exit 1: `PosixPath('/private/tmp/def835-cwd-rood-9C9h') == ROOT`, exact de gatefout |
| Groen (gerichte test, tijdelijke cwd) | `merge-cwd-green-v1.log` | 2 passed (`[repository]`, `[buiten-repository]`), exit 0 |
| Mutantproef | `merge-cwd-mutant-v1.log` met plugin `merge-cwd-mutant-v1.py` | zie hieronder |
| Hele testfile (tijdelijke cwd) | `merge-cwd-testfile-v1.log` | **177 passed** (176 eerder + 1 extra parametrisatie), exit 0 |
| Lint | `merge-cwd-lint-v1.log` | Black: unchanged; Ruff 0.15.17 en Ruff 0.16.5: all checks passed |

Het echo-commando in `merge-cwd-red-v1.log` noemt de interpreter als `$W/../../../.venv/bin/python`. Dat is hetzelfde bestand als het werkelijk gebruikte `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python`.

## Mutantproef

De runnerbron is niet gewijzigd. Een pytest-plugin voert na de collectie de al geladen module opnieuw uit met één tekstmutatie in `_proefomgeving`.

| Mutant | `[repository]` | `[buiten-repository]` |
| --- | --- | --- |
| `herstel_naar_repo`: `os.chdir(REPO)` in plaats van `os.chdir(vorige)`, de naïeve variant die de oude test goedkeurde | passed | **failed**: cwd is ROOT, verwacht de tijdelijke werkmap |
| `geen_herstel`: geen `chdir` terug | **failed** (FileNotFoundError op de verwijderde tijdelijke map) | **error at setup**: de gemuteerde runner laat al in de manifest-fixture de cwd in een verwijderde map achter |

Beide mutanten worden dus gevonden. De naïeve variant wordt alleen gevonden door de nieuwe variant buiten de repository.

## Eindhash testfile

`tests/unit/validation/test_def835_int02_modelproef.py`: `63bf07a24c638d22a94d03b4ecdec5cd05778bc5e8f82c41411cca091e653834`.

De volledige unitgate is niet opnieuw gedraaid; de coördinator doet dat na integratie van de actuele main.
