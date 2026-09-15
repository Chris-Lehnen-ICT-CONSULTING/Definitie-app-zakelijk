# DEF-622 — deltareview koppelingen

Bron: `95396232b..e9739635e`. Zelfde onafhankelijke Codex CLI-reviewer `01a0a047-7df4-7b12-b5b2-603834446fba`, read-only zonder delegatie. Volledig resultaat lokaal `/private/tmp/DEF-622-codex-connections-deltareview-v1-result.md`.

K1 (editorversie), K5 (ontbrekende actor blokkeren) en K6 (finale prompt) gesloten. K2/K3/K4 behouden vier Important-restpunten, alle FIX NU aan dezelfde Claude-implementer:

- Exportvalidatie is beschermd, maar uitvoer laat contractvelden nog overschrijven door aanvullende data.
- Nieuwe tweede recordlezing kan validatie en uitvoer verschillende versies geven.
- Expert-hervalidatie gebruikt actueel record maar selectie/scherm blijft oud.
- Expliciete identieke legacytekst met Toelichting krijgt andere tekstbasis dan impliciete recordexport.

Eigen coördinatorproef: 22 tests, exit 0, nul fouten/skips op exacte git-archivebron `/private/tmp/DEF622-connections-fix-jp4fgbo9`; bronbinding en JUnit/log `reports/def622/coordinator-connections-fix*`. De vier ontbrekende regressies zijn hiermee niet gesloten; reviewer heeft ze afzonderlijk gereproduceerd. De implementer schrijft gerichte regressies en levert een selectieve fixcommit.
