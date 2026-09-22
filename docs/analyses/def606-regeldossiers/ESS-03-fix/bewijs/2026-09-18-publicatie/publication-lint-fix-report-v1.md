# DEF-766 — publicatie-lintcorrectie (ISC004) · rapport v1

18 september 2026 · Claude Code CLI-uitvoerder · werkboom `/Users/chrislehnen/.codex/worktrees/2075/Definitie-app`, branch `bugfix/DEF-766-ess03-telbaarheid`. Geen commit, push, installatie, staging- of configwijziging; geen andere bestanden geraakt.

## Bevinding (gereproduceerd vóór de fix)

Gepinde pre-commit ruff-hook `v0.16.5` (`.pre-commit-config.yaml:7`) meldt **ISC004** ("Unparenthesized implicit string concatenation in collection") tweemaal in `tests/unit/validation/test_def766_ess03_telbaarheid.py`: `:164-165` (goede_voorbeelden) en `:168-169` (foute_voorbeelden). Hook exit 1, geen auto-fix beschikbaar (alleen `--unsafe-fixes`), dus de hook heeft zelf niets aangepast. Log: `publication-lint-precommit-before.log`.

## Correctie (uitsluitend opmaak, via Edit)

Beide impliciete stringconcatenaties binnen de lijstliteralen zijn in expliciete haakjes gezet; letterlijke tekst, waarden en asserties ongewijzigd. Brondiff: 8 regels toegevoegd, 4 verwijderd (543 → 547 regels).

```
         assert goed == [
-            "Afzonderlijk aaneengesloten landoppervlak dat op het afgesproken "
-            "peilmoment volledig door water is omgeven."
+            (
+                "Afzonderlijk aaneengesloten landoppervlak dat op het afgesproken "
+                "peilmoment volledig door water is omgeven."
+            )
         ]
         assert fout == [
-            "Boekexemplaar dat uitsluitend door zijn ISBN van andere fysieke "
-            "exemplaren wordt onderscheiden."
+            (
+                "Boekexemplaar dat uitsluitend door zijn ISBN van andere fysieke "
+                "exemplaren wordt onderscheiden."
+            )
         ]
```

## Bewijs

| Controle | Commando (Python 3.13-venv `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python`) | Resultaat | Log |
|---|---|---|---|
| AST-identiteit | `ast.dump(ast.parse(src), include_attributes=False)` vóór (gestagede kopie `publication-lint-before.py`) en na | **identiek**: SHA256 `bf77c0d9333b7447166862e9c316a1a8a1f4854a06a4db5ffcd5c62998fefdbf` beide; tegencontrole mét positieattributen verschilt wél (alleen opmaak veranderd) | `publication-lint-ast-before.log`, `publication-lint-ast-compare.log` |
| Gepinde ruff-hook na fix | `python -m pre_commit run ruff --files <bestand>` (pre-commit 4.3.0, rev v0.16.5, normale hooks) | **Passed, exit 0** | `publication-lint-precommit-after.log` |
| Black-hook na fix | `python -m pre_commit run black --files <bestand>` | Passed, exit 0 | idem |
| Twee ESS-03-testbestanden | `pytest tests/unit/validation/test_def766_ess03_telbaarheid.py tests/unit/services/prompts/test_def766_ess03_promptnorm.py -q -p no:cacheprovider -o addopts=""` met dummy API-keys | **65 passed, exit 0** | `publication-lint-tests.log` |

Volledige suite niet herhaald: de wijziging is AST-identiek en de gerichte checks slagen (conform opdracht).

## Staat voor de coördinator

- `git status`: alle oorspronkelijke bestanden staan nog gestaged; alleen `tests/unit/validation/test_def766_ess03_telbaarheid.py` toont `AM` (gestagede versie = manifest-v2-hash `fd352e88…`, werkboomversie = deze correctie). De coördinator moet de delta zelf stagen; ik heb de staging niet aangeraakt.
- Nieuwe bestandshash (werkboom): `b52cff1078c5ed0e77496b3ef3bc688c87d37b4a2fae6d225923d3e8a53f4383` (`publication-lint-hash-after.txt`).
- Delta voor de Codex-reviewer: uitsluitend bovenstaande 12 regels in één bestand; manifest-v2 blijft voor de overige 14 bestanden geldig.
