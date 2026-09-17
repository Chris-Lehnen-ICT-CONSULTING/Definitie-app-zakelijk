Klaar. Alleen `docs/analyses/con02-uitvoering-20260917-v1/cli-bewijs/run_con02.py` aangepast; `/tmp`-origineel, productiecode en manifest onaangeroerd; geen run, geen modelcalls.

**Resultaat**
- `ruff check` → All checks passed (was 7: 5× SIM115, 2× B905)
- `black --check` → unchanged
- `py_compile` → OK

**Mijn wijzigingen (de rest van de `git diff` hierboven is de al bestaande hook-formattering/import-opsplitsing):**

1. Regel 52–58 — SIM115 (3×): `json.load(open(...))` → `json.loads(Path.read_text(encoding="utf-8"))` voor REG, PLAN en MAN. Zelfde inhoud; bestand wordt gesloten.
2. Regel 106 — B905: `zip(docs, fids)` → `zip(docs, fids, strict=True)`. Lijsten zijn per constructie even lang (één doc per fixture-id).
3. Regel 218–222 — B905: `zip(("snippets","documenten"), upload(...))` → `strict=True`. `upload` retourneert altijd een 2-tuple.
4. Regel 266–267 — SIM115: `json.dump(res, open(..., "w"), ...)` → `with open(..., "w") as fh: json.dump(res, fh, ...)`.
5. Regel 308–320 — SIM115: idem voor `runmatrix-ruw.json`.

Geen andere semantische wijziging.
