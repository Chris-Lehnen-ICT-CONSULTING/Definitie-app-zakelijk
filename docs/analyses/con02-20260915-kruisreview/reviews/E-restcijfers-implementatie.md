# DEF-743 — resterende kwaliteitscijfers in de UI (besluit 3), rapport

15 september 2026 · Claude Code CLI · branch `feature/DEF-743-con02-bronbasis` · worktree `/Users/chrislehnen/.codex/worktrees/8b34/Definitie-app`. Uitsluitend drie bestanden geraakt (zie manifest). Niets gecommit/gepusht/verwijderd; geen andere implementatie, fixture, test of doc aangeraakt.

## Wat is gewijzigd (presentatie-opschoning binnen het goedgekeurde besluit "geen totaalcijfer")

| Bestand | Plek | Vóór | Ná |
| --- | --- | --- | --- |
| `src/ui/components/duplicate_check_renderer.py` | `_render_existing_definition` (kol. 2, ex-regels 102–103) | `**Score:** {validation_score:.2f}` voor elke truthy historische score | Weg. Status, categorie, aanmaakdatum, definitietekst, context (org/jur/wet), de drie keuzes (Gebruik Deze / Bewerk / Genereer Nieuw) en het redenveld ongewijzigd. Geen vervangend cijfer, geen nieuwe tekst. |
| `src/ui/components/category_renderer.py` | `render_definition_comparison` (ex-regels 438–440; de enige "regeneration comparison"-methode, geen andere aanroeper in `src/`) | `**Kwaliteitsscore nieuwe definitie:** {validation_score:.2f}` — bij `None` een `TypeError` | Weg. Oude én nieuwe definitie met categorienaam blijven; dict- en objectresultaat ongewijzigd afgehandeld. |

Niet aangeraakt, bewust: `Vertrouwen` (duplicaatcheck-confidence) en `Match n: … (Score: …)` (`match_score` van een duplicaatmatch) in dezelfde renderer, en de ontologische classificatie-/UFO-scores in `category_renderer` — aparte feitelijke metrieken, geen definitiekwaliteitstotaal.

## Verificatie (TDD)

| Stap | Uitkomst | Log |
| --- | --- | --- |
| RED — nieuw `tests/unit/ui/test_def743_overige_scoreweergave.py` (8 tests) | 3 gefaald (positieve score zichtbaar; vergelijking toont cijfer; `None` → `TypeError`), 5 geslaagd | `/tmp/DEF-743-ui-score-residual-red.log` |
| GREEN — zelfde bestand + buren `test_def622_duplicaat_keuzes.py`, `test_def622_apptest_keuzes.py` | **26 geslaagd, 0 gefaald**, exit 0 | `/tmp/DEF-743-ui-score-residual-green.log` |
| Ruff + Black op de 3 bestanden | schoon, exit 0/0 | `/tmp/DEF-743-ui-score-residual-lint.log` |
| SHA256-manifest (3 bestanden) | — | `/tmp/DEF-743-ui-score-residual-hashes.log` |

De tests volgen het bestaande mockpatroon (`patch("ui.components.<module>.st")` + kolommen als `MagicMock`, `button` → `False`) en toetsen zichtbaar gedrag via de echte componentaanroepen (`render_check_results` met een `DefinitieCheckResult`, `render_selected_definition`, `render_definition_comparison`): geen kwaliteitslabel/-cijfer bij positieve, nul-, `None`- en ontbrekende score; geen exceptie; definitie, context, status, categorie, datum, keuzes, redenveld en beide vergelijkingsteksten aanwezig. Geen spiegeling van exacte code.

## Manifest

```
fd7cb7245edf84af4f4cbb6e864d526a9c5421f6f02f0187dae0259b949fe273  src/ui/components/duplicate_check_renderer.py
5842e78f99a623ada61dbccca28f23c40e96d566405f443beb3909986cba1bc8  src/ui/components/category_renderer.py
6916b9c73a3da5bb611628f45135b6d0226d736e8dd6860d4be1045be9a5bfc9  tests/unit/ui/test_def743_overige_scoreweergave.py
```

`git diff --stat` op de twee bronbestanden: 2 files changed, 5 insertions(+), 5 deletions(-).

## Grenzen

Gerichte unit-/componenttests met gemockte Streamlit; geen brede gate (root draait de canonieke test). Geen bewijs over andere UI-plekken buiten deze twee; geen scoregate-/beleidswijziging; geen nieuwe dependency. Geen "feature done"-claim.
