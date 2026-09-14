# DEF-622 — beperkte herbeoordeling van reviewcorrecties

Historisch checkpoint: dezelfde onafhankelijke Codex CLI-reviewer, geen nieuwe reviewlaag. Read-only; geen agents of MCP-delegatie.

Reviewhead: `fc20807a922e64178aba8948b46004ee654fdad5`. Alleen de correctiedelta vanaf `117e435b` beoordeeld.

1. **Cleaner — gesloten.** Samenstellingen en samentrekkingen blijven behouden tot readback; losse labels worden nog genormaliseerd.
2. **Editorbinding — gesloten.** Echte AppTest bevestigt: vergelijking zichtbaar bij begintekst, verborgen na herschrijven, opnieuw zichtbaar na terugzetten.
3. **Toelichting — deels hersteld, blijft open (middel; fix nu).** Afzonderlijk bewerken, opslaan en legen werken. Terugzetten **na een eerdere opslag** werkt niet betrouwbaar.
4. **Classificatietests — gesloten.** De bedoelde routes worden bereikt. Ook de gewijzigde integratieproeven slagen; assertions en contextpoort zijn behouden.

Resterende fout bij bevinding 3: [expert_review_tab.py:1081](/Users/chrislehnen/.codex/worktrees/855d/Definitie-app/src/ui/components/expert_review_tab.py:1081) vergelijkt met de oorspronkelijke geladen toelichting. Na opslag wordt dat referentierecord niet ververst.

**Reproductie met echte Streamlit en tijdelijke SQLite:** wijzig toelichting A naar B → sla op via ‘Wijzigingen Vereist’ → zet het veld terug naar A → sla opnieuw op. Het veld toont A, maar readback bevat nog B. De wijzigingsmarkering wordt gewist doordat A gelijk is aan het oude referentierecord; [de opslagcontrole:1285](/Users/chrislehnen/.codex/worktrees/855d/Definitie-app/src/ui/components/expert_review_tab.py:1285) ziet vervolgens geen wijziging.

**Correctie:** ververs na succesvolle opslag het geselecteerde record en de vergelijkingsbasis; voeg bewijs toe voor A → B opslaan → A terugzetten en opnieuw opslaan.

Eigen bewijs: **59 tests geslaagd**, aanvullende echte AppTest-interacties en SQLite-readback. Alles offline; geen bronwijzigingen. De brede unitgate was bij de laatste controle nog niet afgerond.

Dispositie resterende bevinding3: **fix nu**. Coördinator heeft de geselecteerde-recordbasis en opslagroute gecontroleerd; dezelfde Claude-implementer herstelt de referentie na succesvolle opslag en voegt een echte A→B opslaan→A opnieuw opslaan-proef toe. Bevindingen1,2,4 blijven gesloten.
