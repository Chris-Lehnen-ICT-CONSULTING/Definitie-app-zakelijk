# WP5 — eindverificatie op de beoordeelde code

26 september 2026. Appcode commit 9ff3eac199c3eb6e77a44ee47220f91226ffed44; skillcode 750068253a7389e201daedc5b9aa0afd5c0be032. Getrackte werkboom na de run gecontroleerd: ongewijzigd. Latere documentatiecommits veranderen deze geteste code niet.

## Volledige suite — letterlijk resultaat

Commando: `DEF771_SKILLS_ROOT=/Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills/skills .venv/bin/pytest --randomly-seed=20260926 --tb=short --junitxml=.../wp5-pytest-na-r1.xml`. Volledig log: wp5-pytest-na-r1.log; XML: wp5-pytest-na-r1.xml. Bestaande offline-bootstrap actief.

```text
67 failed, 8215 passed, 114 skipped, 24 xfailed, 3386 warnings, 21 subtests passed in 666.76s (0:11:06)
EXITSTATUS=1
```

De coördinator heeft de failure-ID-verzamelingen uit de twee volledige XML's vergeleken: geen nieuwe failure-ID, geen verdwenen failure-ID; exact dezelfde 67. Iedere failure en oorzaak staat in wp5-testbevindingen-v1.md, met bewijs op de oorspronkelijke basis. Het eerdere basisbewijs blijft hiervoor relevant; het is geen identieke volledige baselinesuite en geen groene-suiteclaim. De vaste seed maakt de volgorde van deze eindrun reproduceerbaar; bestaande timingtests blijven metingen.

Alle 55 DEF-771-testgevallen in de definitieve XML zijn geslaagd, zonder failure of skip. De drie extra geslaagde gevallen zijn de R1-invoeren. De overlapping tussen pakketselecties wordt niet als extra onafhankelijke dekking opgeteld.

## R1 en review

- R1-correctie: twee bestanden, 38 regels; Claude Code CLI-sessie a4b588d6-e4a1-4fd6-8f80-0aac55013d90.
- RED 6 failed/28 passed, exit 1 → GREEN 149 passed, exit 0.
- Ruff, Black, make lint en normale commithooks geslaagd; logs wp5-r1-lint.log en wp5-r1-commit.log.
- C1-run3: 36/36, geen citaatfouten, exit 0. Evaluatorhash ca35ad6a6552fb6df38dd36a762bf01ba75b03767bf1a64aa109032d4c0d2771; gelijk aan de definitieve code.
- Onafhankelijke Codex CLI-sessie 01a0dc44-26c6-7de3-b2f9-b0f79e5a27ff: volledige review wp5-codex-review-v2.md, gerichte correctiereview wp5-codex-review-r1.md. R1 gesloten, geen nieuwe bevinding. Geen open inhoudelijke reviewbevinding.
- Volledige review appbasis 0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d → 5fb535ee45671007e5cb4557509560c793eec290, plus gerichte correctiediff 5fb535ee → 9ff3eac19; skillbasis 1e27a2da7668437423af3962cce48af5f1bc591b → 750068253a7389e201daedc5b9aa0afd5c0be032.

## Acceptatie en grenzen

B1/B3/B4 zijn in contract, record, G en leeshulp uitgevoerd; B2-O1 is offline bewezen binnen het genoemde bereik. B2-O2 is na afzonderlijk akkoord geregistreerd als DEF-835, zonder bouw- of modelproefautorisatie. B5/B6 zijn gerespecteerd: geen zelfstandige poort of herstelroute toegevoegd. Oorspronkelijke testgevallen en legacycode blijven aanwezig.

Actieve skillversies zijn gecontroleerd; beheerde bron en Cowork-ZIP's zijn bytegelijk bewezen. De actieve kopieën zijn nog niet bijgewerkt: geen uitrolclaim. Geen echte generatie, kwaliteitswinstmeting, menselijke beoordelingstest of volledige UI-/opslag-/vaststel-/exportdoorloop uitgevoerd. Algemene violation-code-schemafout blijft buiten deze wijziging; het nieuwe rule_results-contractdeel is wel getest.

Oplevering gebeurt als PR's, met volledige transparantie over de rode suite. Geen merge zonder Chris. Het samengestelde implementatiecriterium van DEF-771 wordt niet als volledige actieve ketenoplevering afgevinkt zolang de genoemde publicatie-/ketengrenzen open zijn.
