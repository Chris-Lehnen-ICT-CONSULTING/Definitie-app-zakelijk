---
name: no-root-files
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    # Detecteert bestanden in project root die NIET zijn toegestaan
    # Toegestaan: README.md, CLAUDE.md, requirements*.txt, pyproject.toml, pytest.ini, .pre-commit-config.yaml, Makefile, .gitignore, .python-version
    # Pattern matcht: pad zonder subdirectory + niet-toegestane bestandsnaam
    pattern: ^(?!.*/)(?!README\.md$|CLAUDE\.md$|requirements.*\.txt$|pyproject\.toml$|pytest\.ini$|\.pre-commit-config\.yaml$|Makefile$|\.gitignore$|\.python-version$|\.env.*$|\.DS_Store$).*$
---

**BESTAND IN PROJECT ROOT GEDETECTEERD**

Je probeert een bestand aan te maken in de project root. Dit is **verboden** volgens CLAUDE.md §Critical Rules.

**Toegestane bestanden in root:**
- `README.md`, `CLAUDE.md`
- `requirements*.txt`, `pyproject.toml`
- `pytest.ini`, `.pre-commit-config.yaml`
- `Makefile`, `.gitignore`, `.python-version`
- `.env*` (environment files)

**Correcte locaties:**
| Type | Locatie |
|------|---------|
| Python code | `src/` |
| Tests | `tests/` |
| Scripts | `scripts/` |
| Documentatie | `docs/` |
| Data/DB | `data/` |
| Config | `config/` |
| Logs | `logs/` |

**Waarom deze regel:**
Een opgeruimde project root maakt navigatie makkelijker en voorkomt vervuiling met tijdelijke of experimentele bestanden.

**Zie:** CLAUDE.md §Critical Rules, §File Locations
