# INT-02 O2 — binding rode en groene prompttests

30 september 2026. Branch `feature/DEF-835-int02-o2`, basis-HEAD `a9fb4a0b7444d073813182b662056e7c3265fc7c`. De reviewer wees terecht op ontbrekende metadata bij het eerste groene log. Daarom is **na de uiteindelijke tweebestandsdiff** dezelfde selectie opnieuw gedraaid; dit document bindt de definitieve run aan bron en log.

Rood, na door Claude geschreven tests en vóór productiewijziging:

```text
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/services/prompts/test_def835_int02_prompt.py -o addopts= -q -ra
5 failed, 57 passed in 0.70s
```

`promptcorrectie-rood-coordinator-v1.log` SHA-256 `5ddc6367e02531d8fba3db3134cf407a3833b78f6f302e554b80102ab13edf81`.

Groen, na alle bewerkingen van Claude:

```text
/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/services/prompts/test_def835_int02_prompt.py tests/unit/validation/test_def835_int02_assessment_service.py tests/unit/validation/test_def835_int02_evaluator.py tests/unit/validation/test_def835_int02_modelproef.py -o addopts= -q -ra
452 passed in 29.59s
```

`promptcorrectie-groen-coordinator-v2.log` SHA-256 `9577a6b7c64f220044fabe92c96cf7eb6f70fc261faff08a6a3c627c52a6e3ea`.

Bestands-SHA-256 op het moment van de groene run:

- `src/services/validation/int02_assessment_service.py`: `1b7144c5d0e99984dcc4130b40c9c0708ffde16539a2ccf48ccfe5804436b39f`;
- `tests/unit/services/prompts/test_def835_int02_prompt.py`: `aaf188300ee0d424cfc04bd4d742c75c3376c0728fcfe75427719bad50d4c973`.

Verder: `git diff --check` schoon; Ruff voor beide gewijzigde bestanden: `All checks passed!`; Black `--check`: twee bestanden ongewijzigd. Dit is offline bewijs van promptrendering en contractregressie; het bewijst nog geen modelkwaliteit.
