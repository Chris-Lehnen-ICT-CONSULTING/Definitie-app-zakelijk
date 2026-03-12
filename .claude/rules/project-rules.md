# Kritieke Regels (DEF Project-Specifiek)

1. **Geen bestanden in project root** - Alleen: README.md, CLAUDE.md, requirements*.txt, pyproject.toml, pytest.ini, .pre-commit-config.yaml
2. **SessionStateManager ONLY** - Nooit `st.session_state` direct aanspreken
3. **Database locatie** - Alleen `data/definities.db`, nergens anders
4. **Geen backwards compatibility** - Solo dev app, refactor in place
