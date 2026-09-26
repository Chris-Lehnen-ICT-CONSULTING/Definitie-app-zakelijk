# DEF-835 — takenlijst v3

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
- [ ] WP1: coördinatorverificatie en onafhankelijke Codex CLI-review.
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

Actuele ingang: deze takenlijst v3. Plan-v1.md WP1 is geaccordeerd; akkoord-wp1-v1.md legt het akkoord vast. Fase: onafhankelijke Codex CLI-review van commit 314b817aabcaaa9f5a00d74a7633155ec74b799c. Claude Code CLI-sessie 177f1484-4e5c-482e-b431-450befdab835 implementeerde; tests/fixture zijn onveranderd t.o.v. RED. Reviewer 01a0dfa6-a610-7100-a66e-e3fefc051d4c in /private/tmp/def835-wp1-review-20260926; opdracht wp1-opdracht-codex-review-v1.md. Volgende stap: bevindingen controleren en aan dezelfde Claude-uitvoerder teruggeven. Ruff/Black schoon; lokale pre-commit-gates geslaagd. Lokale hooksymlink staat buiten de commit. Geen live modelcalls vanuit de applicatie, geen productiegegevens, geen Actions-wijziging. De eerste baselinepoging gebruikte een oude skillcheckout (vier failures/zeven errors); de tweede gebruikt de juiste werkboom en is groen. Beide logs blijven onder `bewijs/`.

Geen parallelle INT-02-opslagvoorziening bouwen. Goldset en hold-out bestaan nog niet; de 76 ontwerpgevallen zijn daarvoor geen vervanging.
