# DEF-835 — takenlijst v4

26 september 2026. Plan: [plan-v1.md](plan-v1.md). Branch `feature/DEF-835-int02-o2`; basis `84bdc8c1b060ab50a1bd1428aed778bb2ed6007f`.

- [x] Actuele main ophalen en aparte featurewerkboom maken.
- [x] DEF-835, gekoppelde specificatie, DEF-815 en DEF-626 ophalen.
- [x] INT-02-besluiten, T-statusmapping en relevante actuele code inventariseren.
- [x] Beide verplichte CLI’s op beschikbaarheid en aanmelding controleren.
- [x] Actuele skillbron onderscheiden van oudere hoofdcheckout; hash vergelijken.
- [x] Gerichte offline nulmeting: 120 passed in 1.45s; exit 0.
- [x] Concrete WP1-bestanden en nieuw intern contract ter beoordeling vastleggen.
- [x] Chris: WP1-contract en start bouwpakket akkoord (26-09, expliciet antwoord in chat).
- [x] WP1: Claude-opdracht opgeslagen, 162 rood → 162 groen; coördinator 282 groen inclusief regressie.
- [x] WP1: coördinatorverificatie en onafhankelijke Codex CLI-review; drie P2-punten gecorrigeerd en gesloten.
- [ ] WP2: AI-service/prompt offline bouwen en verifiëren.
- [ ] Chris: WP3 publiek resultaatcontract/schema akkoord.
- [ ] WP3: evaluator en schema offline bouwen en verifiëren.
- [ ] Goldseteigenaar, twee beoordelaars en evaluatiecriteria vaststellen.
- [ ] Nieuwe goldset en afgescheiden hold-out opstellen, beoordelen en bevriezen.
- [ ] Modelprofiel, budget, privacy/bewaartermijn en proefautorisatie vaststellen.
- [ ] Geautoriseerde modelevaluatie met individuele uitkomsten uitvoeren.
- [ ] Gedeelde opslag-/herlaadroute afstemmen met DEF-626; specifiek integratieplan.
- [ ] Appintegratie, UI/export en historische binding aantoonbaar leveren.
- [ ] Finale onafhankelijke review en lokale offline gates.
- [ ] PR en acceptatiebewijs; apart activeringsbesluit.
- [ ] O2 pas afronden wanneer alle DEF-835-criteria bewezen zijn.

## Werkstatus

Actuele ingang: deze takenlijst v4. WP1 is afgerond. Zie [oplevering](wp1-oplevering-v1.md) voor bewijs en beperkingen. Geaccepteerde codecommit: d83ddbc5d7eee991ebff0aac2643983be11d8472. Eindverificatie: 297 tests geslaagd; onafhankelijke reviewer: 177 tests en 26 tegenproeven geslaagd, alle drie bevindingen gesloten. Volgende pakket: WP2, begrensde AI-service en T-prompt, offline. Het plan blijft leidend voor aparte contract-, goldset-, modelbudget- en activeringsbesluiten. O2 is nog niet in de app geactiveerd; DEF-835 blijft In Progress. Actions blijven uit.
