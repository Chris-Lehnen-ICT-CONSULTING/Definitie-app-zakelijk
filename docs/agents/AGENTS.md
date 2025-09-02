# Repository Guidelines

## Projectstructuur & modules
- `src/`: Broncode. Ingang: `src/main.py` (Streamlit, tabinterface). Belangrijke pakketten: `services/`, `validation/`, `database/`, `ui/`, `toetsregels/`, `utils/`.
- `tests/`: Pytest suites met markers; `pytest.ini` zet `pythonpath=src` en `testpaths=tests`.
- `docs/`: Actieve documentatie (architectuur/requirements/analyses). Gebruik canonieke locaties; vermijd `docs/archief/`.
- `scripts/`: Lint/format, analyses, hooks en onderhoud (o.a. `ai-agent-wrapper.py`, `hooks/check-doc-location.py`).
- `data/`, `cache/`, `reports/`: Lokale artefacten; niet committen.

## Ontwikkelen, bouwen en testen
- Setup: `python -m venv .venv && source .venv/bin/activate` (Python 3.10+; 3.11 aanbevolen)
- Dependencies: `pip install -r requirements.txt` (dev-tools: `-r requirements-dev.txt`)
- Start UI: `streamlit run src/main.py`
- Testen:
  - Alles: `pytest`
  - Markers: `pytest -m "unit" | "integration" | "contract" | "not slow"`
  - Stop bij eerste fout: `pytest -x`
- Kwaliteit: `ruff check . --fix` en `black src/`
- Pre-commit: `pre-commit install && pre-commit run -a` (incl. documentlocatie‑check)

## Stijl & naamgeving
- Formatter: Black (88 kolommen). Linter: Ruff (pycodestyle/pyflakes/isort/pep8-naming; zie `pyproject.toml`).
- Naamgeving: `snake_case` functies/variabelen, `PascalCase` klassen. Modules in `snake_case`.
- Taal: Engelstalige identifiers waar passend; Nederlandstalige comments/docstrings voor domeinlogica. Volg bestaande patronen per map (bv. `toetsregels/`, `ontologie/`).
- Richtlijnen: type hints voor nieuwe code, gesorteerde imports, geen `bare except`.

## Test richtlijnen
- Framework: pytest (asyncio geconfigureerd). Markers: `unit`, `integration`, `contract`, `slow`.
- Bestanden: `tests/test_*.py` of `tests/*_test.py`. Vermijd netwerk in standaard runs; markeer externe afhankelijkheden als `integration`.
- Golden dataset: zie `docs/testing/` voor validatie‑datasets en drempels (drift/coverage).
- Voorbeelden: `pytest tests/services/test_definition_generator.py::test_happy_path` en `pytest -m "not slow"`.

## Commits & PR’s
- Gebruik Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
- PR‑vereisten: duidelijke beschrijving, impact/motivatie, gelinkte issues, relevante screenshots (UI), testnotities.
- Checks: `pytest` groen, `ruff`/`black` schoon, pre‑commit ok. Documenten plaatsen volgens `docs/CANONICAL_LOCATIONS.md`.

## Architectuuroverzicht
- Solution Architecture: zie `docs/architectuur/SOLUTION_ARCHITECTURE.md` voor technische componenten, afhankelijkheden en feature‑registry.
- ADR’s (Architecture Decision Records): `docs/architectuur/beslissingen/` (bijv. ADR‑001 t/m ADR‑005). Raadpleeg relevante ADR’s bij grotere wijzigingen of refactors.

## Security & configuratie
- Config: runtime laadt geen `.env`. Stel `OPENAI_API_KEY` (of `OPENAI_API_KEY_PROD`) in via je omgeving of gebruik het VS Code launch‑profiel (mapping). Gebruik `.env.example` alleen als template voor tooling; commit nooit secrets.
- Status: geen productie‑auth/encryptie; behandel als dev‑omgeving. Zie `src/security/security_middleware.py` en `docs/SECURITY_AND_FEEDBACK_ANALYSIS.md` voor risico’s.
- Data: houd gevoelige/gegenereerde outputs in `data/`, `cache/`, `reports/` buiten git.

## (Optioneel) Agent‑ondersteuning
- Snelle kwaliteitsronde: `python scripts/ai-agent-wrapper.py` (probeert Ruff/Black/pytest; auto‑fix waar mogelijk).
