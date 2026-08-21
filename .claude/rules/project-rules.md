# Kritieke Regels (DEF Project-Specifiek)

1. **Geen ad-hoc bestanden in project root** - Geen ad-hoc werk-, analyse-, resultaat- of databaseartefacten in de project-root. In de root horen uitsluitend native projectinstructies en standaard repository-, build-, test- en securityconfiguratie, waaronder README.md, CLAUDE.md, AGENTS.md, Makefile, CHANGELOG.md, requirements*, pyproject.toml, pytest.ini, .pre-commit-config.yaml, .gitignore en .gitleaks*. Overige documentatie en werkresultaten horen in de daarvoor bestemde subdirectory. Machinaal geborgd door `scripts/ci/check_root_allowlist.sh`; die allowlist en deze regel horen samen bijgewerkt te worden. AGENTS.md blijft tot het besluit in ALG-399 ongetrackte, gegenereerde build-output en mag niet worden gestaged of gecommit; ALG-399 bepaalt daarna de definitieve trackingstrategie.
2. **SessionStateManager ONLY** - Nooit `st.session_state` direct aanspreken
3. **Database locatie** - Alleen `data/definities.db`, nergens anders
4. **Geen backwards compatibility** - Solo dev app, refactor in place
