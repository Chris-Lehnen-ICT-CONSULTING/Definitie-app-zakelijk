# DEF-622 — herbeoordeling van de opgeslagen expertselectie

Historisch, brongebonden checkpoint van dezelfde onafhankelijke reviewer.

Reviewhead: `4c09d1bd35915ed8a643777e8b1ad6ea83b7b217`.

**Restpunt 3 blijft gedeeltelijk open — middel, fix nu.**

De oorspronkelijke A → B opslaan → A terugzetten → opnieuw opslaan-proef slaagt met echte AppTest/SQLite. Tekst, selectie en versie komen overeen. Ook slagen **18 gerichte tests**.

Eén foutpad blijft hetzelfde probleem veroorzaken: [expert_review_tab.py:1366](/Users/chrislehnen/.codex/worktrees/855d/Definitie-app/src/ui/components/expert_review_tab.py:1366). Als de veldopslag slaagt maar de aansluitende goedkeuringsworkflow een exception geeft, wordt de selectie niet ververst.

Eigen proef met een geïnjecteerde workflowexception:

- SQLite bevat **B, versie 2**.
- De selectie blijft **A, versie 1**.
- Terugzetten naar A en opnieuw opslaan laat SQLite op **B** staan.

De foutmelding verschijnt correct; er wordt geen succes gemeld. Bij een gewone geblokkeerde workflowuitkomst werkt de refresh wel.

**Correctie:** garandeer readback na bevestigde veldopslag, ook wanneer de vervolgactie een exception geeft. Behoud daarbij de foutmelding en recordbinding.

Alleen deze correctiedelta onderzocht; volledig offline, synthetische opslag, geen bronwijzigingen.

Dispositie: **fix nu**, uitsluitend de exceptionvariant binnen restpunt3. De coördinator reproduceerde onafhankelijk dat de veldopslag B bevat terwijl de selectie A blijft na een workflowexception (`coordinator-expert-refresh-exception-red.json`). De normale opslagreeks en bevindingen1,2,4 blijven gesloten. De minimale vervolgaanpassing ververst de selectie direct na zekere veldopslag, vóór de vervolgactie; latere readback na verdere updates blijft behouden.
