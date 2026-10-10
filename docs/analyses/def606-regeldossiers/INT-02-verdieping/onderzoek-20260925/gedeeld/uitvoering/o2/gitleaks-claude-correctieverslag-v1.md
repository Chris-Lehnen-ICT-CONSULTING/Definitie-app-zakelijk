# DEF-835 — correctieverslag A/B (Claude Code CLI)

28 september 2026. Dezelfde uitvoerder als `gitleaks-claude-verslag-v1.md` (sessie 5bc9ae88-46e4-489b-9a78-489c125a07bd). Grondslag is `gitleaks-codex-review-v1.md`, bevindingen A en B, beide met dispositie **fix nu** van de coördinator. Er zijn geen agents, reviewers of andere CLI-sessies gestart. Er is niets gestaged, ontstaged of gecommit, en er is geen `git write-tree` gedraaid.

## Startcontrole

Deze staat is bij de start gemeten en was gelijk aan de review:

- HEAD: `979ca0585100d94b613829d924c6d8bba4f24f1b`
- Index (`git ls-files -s | git hash-object --stdin`): `f9e05035f332c6b8e82762703f056bd7fd6426b3`
- 38 staged bestanden
- Pakkethashes gelijk aan de reviewtabel: config `8bb3a279…d812`, testmodule `77d803cc…9aaa`, Makefile `1083b45b…ae49`, runbook `cd485f28…067b`

Van de drie te raken bestanden zijn vooraf herstelkopieën gemaakt. Die dienen ook als basis voor de correctiediff:

- `bewijs/gitleaks-correctie-herstelkopie-gitleaks.toml-v1` — `8bb3a279…d812`
- `bewijs/gitleaks-correctie-herstelkopie-test_secret_scan_def835_metadata.py-v1` — `77d803cc…9aaa`
- `bewijs/gitleaks-correctie-herstelkopie-test_secret_scan_metadata.py-v1` — `f58c3976…4bf8`, gelijk aan HEAD

## A — bestaande zelfscan in `scripts/ci/test_secret_scan_metadata.py`

**RED.** Eerst is alleen de byte-eis aangescherpt, `scanned_bytes >= len(configtekst)`, met het oude pad `.gitleaks.toml` ongewijzigd.

- Commando: `DEF522_GITLEAKS_BINARY=/Users/chrislehnen/.cache/pre-commit/repo1h6yag49/golangenv-default/bin/gitleaks DEF522_FIXTURE_ROOT=<mktemp -d> PYTEST_ADDOPTS= PYTEST_PLUGINS= /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest -q -p no:cacheprovider -rA scripts/ci/test_secret_scan_metadata.py`
- Uitkomst: **exit 1**. Er slagen 12 tests. Alleen `test_projectconfig_blokkeert_zichzelf_niet` faalt, met `status=clean … bytes=115`: dat zijn uitsluitend de bytes van het controlebestand, de configtekst is overgeslagen.
- Tussenversie van de module: `a24b1c36…1e8c`. Log: `bewijs/gitleaks-correctie-A-rood-v1.log`.

**Minimale correctie.** Er zijn drie dingen veranderd:

- `_CONFIG_NAAM` wordt `"def522/projectconfig-kopie.txt"`. Het commentaar erbij legt uit waarom `.gitleaks.toml` niet wordt gelezen: de default-allowlist `gitleaks\.toml` (`config/gitleaks.toml:25`) is via `useDefault` actief.
- De docstring beschrijft nu een neutrale scan van de configtekst met bytebewijs. "Blokkeert de gate haar eigen configbestand" is vervangen door "kon de configtekst zelf een waarneming opleveren".
- Het testgeval, alle fixtures en de overige 12 tests zijn ongewijzigd. `_CONFIG_NAAM` wordt alleen in deze zelftest gebruikt.

## B — toelichting `[f]`

- **`.gitleaks.toml`, commentaar bij uitzondering 3.** De tekenklasse volgt de schrijfwijze van de bestaande uitzonderingen. Voor deze regel is ze niet strikt nodig zolang `async_api\.py` ge-escaped blijft. Ze is een aanvullende waarborg, geen voorwaarde.
- **`scripts/ci/test_secret_scan_def835_metadata.py`, docstring van de zelftest.** Dezelfde precisering: de escape voorkomt de zelfwaarneming al, de tekenklasse is aanvullend.
- **Regex, paden, `targetRules`, `condition`, `regexTarget` en de beschrijving zijn ongewijzigd.** Gecontroleerd: `tomllib.load(herstelkopie) == tomllib.load(.gitleaks.toml)` geeft `gelijk`, exit 0. Alleen het commentaar is dus gewijzigd.

## GREEN en lint — `bewijs/gitleaks-correctie-groen-v1.log`

| Stap | Commando | Exit | Uitkomst |
| --- | --- | --- | --- |
| Configvergelijking | `.venv/bin/python -c` met tomllib, herstelkopie tegen actuele config | 0 | gelijk |
| Tests | `DEF522_GITLEAKS_BINARY=<gepind> DEF522_FIXTURE_ROOT=<mktemp -d> PYTEST_ADDOPTS= PYTEST_PLUGINS= .venv/bin/python -m pytest -q -p no:cacheprovider -rA scripts/ci/test_secret_scan_def835_metadata.py scripts/ci/test_secret_scan_metadata.py` | 0 | 35 geslaagd (22 + 13), 0 gefaald |
| Ruff | `uvx ruff@0.16.5 check` op beide modules (hookversie) | 0 | All checks passed |
| Black | `black 26.5.1 --check` op beide modules | 0 | ongewijzigd |

De volledige suite van 105 tests is niet herhaald. De Makefile-selectie, de scannercode en de overige suites zijn ongewijzigd. De wijzigingen raken alleen commentaar in de config en twee modules die hierboven volledig zijn gedraaid.

## Diffs en eindhashes

- Correctiediff tegen de herstelkopieën: `bewijs/gitleaks-correctie-diff-v1.patch`, sha256 `6e469e9c5f35a70f06618262e765406611576d14ffbe91a25ca7f814e93b6bf7`. Omvang: 3 bestanden, 28 regels erbij en 20 eraf.
- Volledige vijfbestandsdiff tegen de basis `979ca058…`: `bewijs/gitleaks-correctie-vijfbestandsdiff-v1.patch`, sha256 `d579491ccb02aa3ceefec1cb8d1662ae13d33b3667a03391a45740d5314c4dd6`.

| Bestand | sha256 na correctie |
| --- | --- |
| `.gitleaks.toml` | `5e74df0cc7dd29999e11ce4e5ebac0542d729ef4a340933fce88145d81219e1f` |
| `scripts/ci/test_secret_scan_def835_metadata.py` | `1a0135c2de16ed7d84fa5f683ca574f76aecee1450cc4fc13ecb1962ab122041` |
| `scripts/ci/test_secret_scan_metadata.py` | `f277d92320cf9579c5f08b87c86ba57437a19ec8d712f7594bb67c4832aa3516` |
| `Makefile` (ongemoeid) | `1083b45bcf7ba358862e887771418cbe3619d966f9132f140c151d4dd35fae49` |
| `docs/technisch/def522-secret-scan-runbook.md` (ongemoeid) | `cd485f28bebcbe705623fa856a77a5c8e2af20be9e672cf61e11608376e1067b` |

Bewijsbestanden: `gitleaks-correctie-A-rood-v1.log` `fe6491d6…c9ac` en `gitleaks-correctie-groen-v1.log` `101d6557…15e8`.

## Eindstaat index en werkboom

- HEAD is `979ca058…`. Index is `f9e05035f332c6b8e82762703f056bd7fd6426b3`, gelijk aan de start.
- Er staan 38 staged bestanden. De sha256 van die lijst is `902ddaa7…8f5e`, ook gelijk aan de start.
- Geen van de vijf pakketbestanden staat in de index.
- De WP5a-bestanden onder `src/` en `tests/unit/` zijn niet aangeraakt.
- Er zijn geen bestanden of testgevallen verwijderd.
- Alle acties lukten in één poging.

Hier stop ik voor de herreview.
