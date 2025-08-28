# Checklist — Root-bestanden

Regel: vink een item pas af als het voorstel + acceptatiecriteria in `CODE_REVIEW_REPORT.md` staat. Items met “EXCLUDED (generated/secret)” nemen we niet op in de review, tenzij je anders aangeeft.

## ROOT

- [ ] [.gitignore](CODE_REVIEW_REPORT.md#-gitignore)
- [ ] [.pre-commit-config.yaml](CODE_REVIEW_REPORT.md#-pre-commit-config-yaml)
- [ ] [CHANGELOG.md](CODE_REVIEW_REPORT.md#changelog-md)
- [ ] [CONTRIBUTING.md](CODE_REVIEW_REPORT.md#contributing-md)
- [ ] [PROMPT_SYSTEM_ANALYSIS.md](CODE_REVIEW_REPORT.md#prompt_system_analysis-md)
- [ ] [pyproject.toml](CODE_REVIEW_REPORT.md#pyproject-toml)
- [ ] [README.md](CODE_REVIEW_REPORT.md#readme-md)
- [ ] [requirements-dev.txt](CODE_REVIEW_REPORT.md#requirements-dev-txt)
- [ ] [requirements.txt](CODE_REVIEW_REPORT.md#requirements-txt)
- [ ] [temperature_analysis_complete.md](CODE_REVIEW_REPORT.md#temperature_analysis_complete-md)
- [ ] [temperature_analysis.md](CODE_REVIEW_REPORT.md#temperature_analysis-md)

## EXCLUDED (generated/secret)

- [ ] .coverage — EXCLUDED (generated)
- [ ] .DS_Store — EXCLUDED (os)
- [ ] .env — EXCLUDED (secret)
- [ ] .env.backup — EXCLUDED (secret)
- [ ] .env.example — EXCLUDED (example, alleen opnemen indien gewenst)
- [ ] .env.new_services_disabled — EXCLUDED (secret)
- [ ] definities.db — EXCLUDED (database artifact)
