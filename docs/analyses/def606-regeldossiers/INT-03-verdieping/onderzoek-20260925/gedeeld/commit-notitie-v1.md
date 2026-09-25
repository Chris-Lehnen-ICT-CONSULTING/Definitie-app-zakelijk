# Commit-notitie — 25 september 2026

- De ruwe sessielogs (claude-run*.jsonl, codex-run*.err/.log, *.status) zijn bewust niet gecommit: het zijn hostlogs van de CLI-sessies (tot 1,3 MB, met volledige tool-uitvoer; gitleaks meldt daarin het repo-eigen voorbeeld `redis://localhost:6379` uit een grep-resultaat). Ze blijven lokaal in de werkboom staan.
- De pre-commit-hook `black` heeft de zes proefscripts (proef-a-v1.py, proef-b-v1.py, proef-c-v1.py, proef-c-v2.py, proef-d-v1.py, run1-opus55-afgebroken/proef-c-v1.py) geherformatteerd. De sha256-waarden in de bewijsmanifesten verwijzen naar de ongeformatteerde versies waarmee de proeven zijn gedraaid; de herformattering wijzigt alleen witruimte/regelafbreking, niet de logica of uitkomsten.
- Ruff (PLC0206) eiste in proef-a-v1.py `for k, gevonden in hits.items()` in plaats van `for k in hits` (regel 149); gelijkwaardige lus, geen wijziging in uitkomst.
- Ruff (PIE810) heeft in proef-c-v1.py, proef-c-v2.py, run1-opus55-afgebroken/proef-c-v1.py en proef-d-v1.py `x.startswith(a) or x.startswith(b)` samengevoegd tot `x.startswith((a, b))` (unsafe-fix); gelijkwaardig, geen wijziging in uitkomst.
- De tijdelijke offline-runtime van onderzoeker D (onderzoek-d/.offline-runtime-d-v1/, symlinks en cache) is uit de commit gehaald; lokaal blijft de map staan.
