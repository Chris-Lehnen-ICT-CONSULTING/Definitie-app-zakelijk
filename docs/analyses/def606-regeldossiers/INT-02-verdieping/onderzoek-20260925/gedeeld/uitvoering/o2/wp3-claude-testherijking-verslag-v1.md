# DEF-835 WP3 — verslag herijking vijf bestaande testbestanden (Claude Code CLI v1)

28 september 2026. Uitvoerder: dezelfde Claude Code CLI-sessie c75abf0d-3c01-4c02-a672-536d75daa15a (claude-opus-5-5). Er zijn geen agents, reviewers of extra CLI-sessies gestart.

Mandaat: `wp3-scopeaanvulling-tests-v1.md`. Chris gaf op 28-09-2026 akkoord met "akkoord om het te fixen".

Werkboom: branch `feature/DEF-835-int02-o2`, HEAD `91949c883c6de9ffc21740173aee457eb77cbe5a`.

Geen commit, push, merge, Actions, modelcalls, productiedata of verwijderingen.

## 1. Scope en diffomvang

Ik heb uitsluitend de vijf geaccordeerde testbestanden gewijzigd. Omvang volgens `git diff --numstat`:

| Bestand | +/− | Wijziging |
|---|---|---|
| `tests/unit/validation/test_def771_int02_o1.py` | +19/−3 | Versiepin `:291` gaat naar `"2.3.0"`, met een commentaarregel. Het contractcommentaar krijgt twee regels voor 2.3.0. `test_onbekende_velden_en_int03_velden_elders_blijven_afgewezen` is herijkt, zie §2. |
| `tests/unit/validation/test_validation_readiness.py` | +3/−2 | De testnaam wordt `test_contractversie_is_verhoogd_naar_2_3_0`, met één commentaarregel voor 2.3.0. De pin gaat naar `"2.3.0"`. |
| `tests/unit/services/orchestrators/test_def743_source_assessment_wrappers.py` | +2/−1 | Commentaarregel voor DEF-835; de pin gaat naar `"2.3.0"`. |
| `tests/unit/services/orchestrators/test_def772_int03_wrappers.py` | +4/−3 | Het actuele versiecommentaar is herschreven. De historische verwijzing "sinds 2.2.0 (DEF-771)" blijft staan. De pin gaat naar `"2.3.0"`. |
| `tests/unit/services/orchestrators/test_def766_ess03_wrappers.py` | +3/−2 | Het commentaar is aangevuld met 2.3.0; de pin gaat naar `"2.3.0"`. |

Totaal +31/−11.

**Wat ongewijzigd bleef:**
- Historische versiegeschiedenis heb ik niet herschreven. Voorbeelden zijn de regels 1.2.0–2.2.0 in de readiness-test en de module-docstring van `test_def772_int03_wrappers.py`, die DEF-772 destijds beschrijft.
- Productiecode, schema en config: `git diff 9769730d6 -- src config docs/architectuur` is leeg, en de werkboom wijkt daarin niet af van HEAD.
- Geen skip, xfail of filter, en geen dependencies.

Elke versiecontrole blijft een echte vergelijking met de letterlijke waarde `"2.3.0"`: `CONTRACT_VERSION` en `result["version"]`. Er is niets vervangen door een tautologie.

## 2. Behoud van cases (O1-contracttest)

`test_onbekende_velden_en_int03_velden_elders_blijven_afgewezen`:

**Behouden.** De uitgangsvalidaties `_fouten(met) == []` en `_fouten(ne) == []` staan er nog. De geval `INT-03 onbekend` wordt nog steeds geweigerd, en de exacte NE-melding (`NE.replace("{kern/context}", "context")`) blijft getoetst.

**Beide oude INT-02-cases** (`signals: []` en `assessment: None`) zijn behouden. Alleen het verwachte resultaat is omgedraaid, van geweigerd naar schemageldig (`_fouten(kopie) == []`). Dat is precies het goedgekeurde 2.3.0-gedrag.

**Toegevoegd** om het gesloten contract te blijven bewaken:
- INT-02 met een onbekend veld wordt geweigerd;
- INT-02 met `signals` als tekst wordt geweigerd;
- INT-02 met `assessment` als tekst wordt geweigerd;
- `signals: []` en `assessment: None` op **CON-01** worden geweigerd, zowel in de NE-uitkomst als in de INT-03-uitkomst. Een vooraf-assertie controleert dat CON-01 in beide uitkomsten voorkomt, zodat die weigering niet vacuüm is.

Geen testfunctie, parametrisatie of assertie is verwijderd. Het aantal verzamelde tests in de vijf bestanden is 121, zowel vóór als na de wijziging.

## 3. Uitkomsten

Commando: `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest <bestanden> -o addopts= --import-mode=importlib -q -ra`.

| Stap | Resultaat | Log |
|---|---|---|
| RED: vijf bestanden ongewijzigd | **8 failed, 113 passed**, exit 1. Precies de acht bekende failures: vijf versiepins, waarvan drie via de O1-parametrisatie, plus de INT-02-`signals`-rij | `bewijs/wp3-testherijking-rood-v1.log` |
| GREEN: vijf herijkte bestanden | **121 passed**, exit 0 | `bewijs/wp3-testherijking-groen-v1.log` |
| Gerichte regressie over 11 bestanden: de vijf, beide WP3-bestanden, `test_def772_int03_evaluator`, `test_evaluator_registry_contract`, `test_rule_cache_runtime_contract` en `test_def835_int02_contract` | **555 passed**, exit 0 | `bewijs/wp3-testherijking-regressie-v1.log` |
| Lint op de vijf bestanden: Ruff 0.15.17, Ruff 0.16.5 (pre-commit-rev, zonder `--fix`), Black 26.5.1 `--check`, `git diff --check` | alles exit 0 | `bewijs/wp3-testherijking-lint-v1.log` |

De telling klopt met eerdere metingen: 121 (vijf bestanden) + 119 (WP3) + 315 (de vier overige regressiebestanden, gelijk aan eerdere metingen) = 555. De eerder vastgelegde losse isolatie- en importkwesties buiten deze set zijn niet opnieuw gedraaid, zoals opgedragen.

## 4. Herstelkopieën en hashes

Herstelkopieën, gemaakt vooraf. Hun git-blob is gelijk aan HEAD:
- `bewijs/wp3-testherijking-herstelkopie-test_def771_int02_o1-v1.py` (`4d3da1a9…`)
- `…-test_validation_readiness-v1.py` (`a704f616…`)
- `…-test_def743_source_assessment_wrappers-v1.py` (`605614f9…`)
- `…-test_def772_int03_wrappers-v1.py` (`fc09587c…`)
- `…-test_def766_ess03_wrappers-v1.py` (`203f5254…`)

SHA-256 na herijking. Dezelfde waarden staan in de koppen van de GREEN- en regressielogs:

| Bestand | sha256 |
|---|---|
| `test_def771_int02_o1.py` | `020c97cc9513b617fd68ece1bbf57a59514dae55d664be28849b89addc9417b9` |
| `test_validation_readiness.py` | `044881acd4314c1326276a0f69090ecdd8a5cbcd8719168c484e75d44d8e6221` |
| `test_def743_source_assessment_wrappers.py` | `db5e489bd1a0849fd8a9b16655c31839aa17d550f710870a679f6b2d9f2a329c` |
| `test_def772_int03_wrappers.py` | `d9390dc293bc652b067ac30abba40f1fba32860b19c8d29d9412d0e5bf785828` |
| `test_def766_ess03_wrappers.py` | `91c3c5ef55015abf5e75567d6f288e81219a6f8eabadc59f9d1e7c2ddc14a249` |

## 5. Grenzen

- Dit betreft uitsluitend testverwachtingen. Er is geen nieuw contractbesluit genomen en er is geen appintegratie gedaan (WP5).
- Het actieve INT-02-record blijft O1.
- Geen nieuwe brede unitrun.
- Alle pogingen slaagden in één keer.

## Bronnen

- Bevinding en voorstel: `wp3-scopeaanvulling-tests-v1.md`, `wp3-claude-groen-verslag-v1.md` §3.
- Opdracht van de coördinator van 28-09-2026, met het citaat van Chris.
- Werkstaat en productiebasis: `git diff --numstat`, `git diff 9769730d6 -- src config docs/architectuur` (leeg).
- De logs en herstelkopieën hierboven.
