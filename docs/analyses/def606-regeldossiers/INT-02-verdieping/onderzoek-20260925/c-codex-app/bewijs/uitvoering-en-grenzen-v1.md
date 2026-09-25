# Uitvoering en bewijsgrenzen

Werkdirectory: `/Users/chrislehnen/Projecten/Definitie-app`. Commit `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`. Verwachtingen eerst opgeslagen in `proefopzet-v1.json`; daarna script en uitvoering.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/c-codex-app/bewijs/proeven-c-v1.py
```

Stdout/stderr: `proefuitvoer-v1.log`; procesexit: `exitstatus-v1.txt` (0). P1–P6 zijn alle uitgevoerd; script vangt per proef uitzonderingen en registreert die afzonderlijk. De exitcode alleen is dus geen bewijs dat iedere proef slaagde: gecontroleerd op `uitgevoerd=true` voor alle zes.

De schrijfbeveiliging blokkeerde tijdens imports één `os.mkdir('cache')` buiten de eigen map. Geen bypass of cache-aanpassing uitgevoerd; alle zes proeven voltooiden via de gebruikte laadroute. `sys.dont_write_bytecode` en `PYTHONDONTWRITEBYTECODE=1` voorkomen pycache. Netwerkconnecties zijn in het proefproces geblokkeerd.

P1: echte evaluator, echt record; geen service-/UI-/opslagbewijs. P2: echte formatter `_format_rule`, echt record, twee instellingen; niet de complete promptorchestrator of modelcall. Registratie van dit moduletype is afzonderlijk statisch vastgesteld. P3: echte ModularValidationService met echte manager; overige regels draaien lokaal mee maar worden niet inhoudelijk onderzocht; geen AI-beoordelingsdienst. Het veld `runstatus` in dit proefbestand leest per abuis sleutel `status` in plaats van `validation_status`. De null bewijst geen ontbrekende runtime-status. INT-02-status/reason/signals zijn wel juist uitgelezen. De gehele-runstatus is in deze uitvoer niet gemeten en wordt niet geclaimd. P4: echte CleaningService, twee teksten; labelwijziging maar behoud van indien en criterium. De omschrijvingen in applied_rules zijn door de app geleverd en bewijzen niet dat elke omschreven wijziging werkelijk plaatsvond. P5: één uit bron geëxtraheerde UI-helper met geïnjecteerd resultaat, geen Streamlit-schermtest. P6: echte bronfunctie, gecontroleerde vervanging van CON-01/02-hulp en recordinterface; geen database, bevoegdheidscontrole of echte vaststelling. Score .9 is een geïnjecteerde isolatievoorwaarde, geen actuele appscore.

Geen echte generatie, geen modelbenchmark, geen UI-doorloop, geen persistente opslag-/exportproef, geen betaalde oproep of productiedata. De normverwachtingen zijn voorstellen of brongebonden interpretaties; de actuele uitkomst review_required is geen bevestiging daarvan.
