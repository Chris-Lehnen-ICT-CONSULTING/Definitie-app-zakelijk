**Beide open Important-bevindingen gesloten. Bronvrijgave voor deze gerichte correctiedelta; geen nieuwe bevindingen.**

- **R2 — gesloten:** citaatslot plus komma, puntkomma of dubbele punt bereikt nu ook zonder spatie de onzekerheidsroute. Vijftien schrijfvrije varianten bevestigen dit, inclusief tabs en regelovergangen. De positie blijft op het oorspronkelijke slotteken; passages voegen geen ontbrekende spatie toe. T17/T20 en interne citaten behouden de verwachte onderdelen. Zie [zinsgrenzen.py:351](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:351).
- **R3 — gesloten:** `q.z. AB-12[.]`, andere onbekende afkortingen en `ca.`/`bv.` blijven onzeker. De codevrijstelling vereist nu expliciet `bijv.` als voorbeeldaankondiging plus een afsluitende code. Andere codes dan R7 werken; vervolgwoorden krijgen geen vrijstelling. Geen algemene afkortingvrijstelling meer. Zie [zinsgrenzen.py:684](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:684).
- **R1 blijft gesloten:** beide lijstfuncties zijn AST-gelijk aan v2. Skillsbron ongewijzigd.

Bewijs gecontroleerd: **RED 10/63; GREEN 513; regressie 1066 groen**, inclusief alle 513 gerichte tests ná Black. Integratie: **27 geslaagd, 1 bestaande skip**. Gepinde Ruff, Black en make lint groen.

**Finale canonieke unitgate blijft open.** Het v2-resultaat geldt niet als eindgate voor v3. Geen acceptatie- of effectvrijgave.

Beide patches reconstrueren de manifestbestanden exact. Alleen classifier en correctietest veranderden sinds v2; hashes vóór en na gelijk, geen drift.

SHA256:

- Appdiff: `a9280028b38d011c0040b794894ca9346b47fbdc18c8cbc17dea13f0d8493e3c`
- Skillsdiff: `28b993bb8f08c120376611b953710d64fde36f6ce79e06c47e08ff4e01bb874e`
- Manifest: `24e675ff60391878953591c413be6aa2df11bec2565c6eb4d21225a0cb24b94f`

Geen edits, brede testherhaling, betaalde calls of inzage in nieuwe proefdata.