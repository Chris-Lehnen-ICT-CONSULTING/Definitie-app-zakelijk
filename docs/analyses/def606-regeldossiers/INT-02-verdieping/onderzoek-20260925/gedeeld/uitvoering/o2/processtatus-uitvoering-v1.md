# DEF-835 — processtatus uitvoering v1

26 september 2026 · [plan](plan-v1.md) · [takenlijst](takenlijst-v1.md).

Inventarisatie afgerond. DEF-835 In Progress. Basis 84bdc8c1b060ab50a1bd1428aed778bb2ed6007f; branch feature/DEF-835-int02-o2. Geen implementatie gestart. WP1-contract ter akkoord in de chat. Linear-plan: https://linear.app/definitie-app/document/def-835-uitvoeringsplan-o2-v1-ter-akkoord-40a20db222a2.

## Nulmeting

Vanuit de O2-werkboom uitgevoerd:

```sh
DEF771_SKILLS_ROOT=/Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills/skills /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/validation/test_def771_int02_contract.py tests/unit/validation/test_def771_int02_o1.py tests/unit/ui/test_def771_int02_validation_view.py tests/unit/services/prompts/test_def771_int02_promptnorm.py tests/unit/validation/test_def772_int03_assessment_service.py tests/integration/contracts/test_validation_result_schema.py -o addopts= -q -ra
```

Letterlijke samenvatting: `120 passed in 1.45s`; exit 0. Volledige uitvoer: [baseline-v2.log](bewijs/baseline-v2.log). [Eerste poging](bewijs/baseline-v1.log) gebruikte de verouderde hoofdcheckout van de skillrepo: vier failures en zeven setup-errors. Correctie betrof uitsluitend het bronpad. Geen TDD-rood→groenclaim; dit is een bestaande baseline.

## Open punten

- Akkoord WP1-contract; daarna Claude Code CLI implementatie en Codex CLI-review.
- Later: publiek contract/schema, goldset/eigenaar, modelkwalificatie/budget/privacy, gedeelde opslagketen en activering.
- Prompt Forge-check door securityhook geweigerd; toegestane lokale dossierfallback. Geen implementatieprompts verstuurd.
- Actions blijven uit. Geen live modelaanroepen, productiegegevens of broncodewijzigingen.
