# Kritieke Regels (DEF Project-Specifiek)

1. **Geen ad-hoc bestanden in project root** - Geen ad-hoc werk-, analyse-, resultaat- of databaseartefacten in de project-root. In de root horen uitsluitend native projectinstructies en standaard repository-, build-, test- en securityconfiguratie, waaronder README.md, CLAUDE.md, AGENTS.md, Makefile, CHANGELOG.md, requirements*, pyproject.toml, pytest.ini, .pre-commit-config.yaml, .gitignore en .gitleaks*. Overige documentatie en werkresultaten horen in de daarvoor bestemde subdirectory. AGENTS.md is voorlopig gegenereerde build-output; de trackingstrategie wordt beslist in ALG-399.
2. **SessionStateManager ONLY** - Nooit `st.session_state` direct aanspreken
3. **Database locatie** - Alleen `data/definities.db`, nergens anders
4. **Geen backwards compatibility** - Solo dev app, refactor in place
