# DEF-835 — actuele takenlijst v6

27 september 2026. Leidend: plan-v1.md met akkoord-wp2-v1.md. Vorige takenlijsten zijn historisch bewijs. Nieuwe versie omdat bestandsbeveiliging de update van v5 weigerde; v5 is ongewijzigd behouden.

- [x] WP1-contract afgerond, 297 tests geslaagd, onafhankelijke review akkoord.
- [x] WP2 en echte modelaanroepen geautoriseerd door Chris.
- [x] Beide CLI’s gecontroleerd: Claude 2.1.283 en Codex 0.157.1 aangemeld.
- [x] WP2 RED: 158 failed/3 passed, coördinator herhaald; 7 aanvullende tests eerst rood.
- [x] WP2 GREEN: 169 tests; coördinator 603 inclusief regressie; lint en commitgates groen.
- [ ] Onafhankelijke Codex CLI-review; bevindingen afhandelen.
- [ ] Kostenplafond/profiel technische modelproef vastleggen; binnen autorisatie uitvoeren.
- [ ] WP2 bewijs, definitieve commit en terugkoppeling.
- [ ] WP3 publiek resultaatcontract/schema apart akkoord en bouwen.
- [ ] WP4 onafhankelijke goldset/hold-out, kwaliteitsgrenzen en gekwalificeerde modelevaluatie.
- [ ] WP5 gedeelde opslag-/herlaadroute DEF-626 en appintegratie.
- [ ] WP6 eindverificatie, PR en afzonderlijk activeringsbesluit.

Werkboom: .claude/worktrees/DEF-835-int02-o2. Basis b56e0e225e65eac00ad73239900d2e6c1bfc2422. Codecommit 0e336c6c4b40fd53d4a1ef3c2283f6a99691510f. Onafhankelijke review loopt via wp2-opdracht-codex-review-v1.md, Codex-sessie 01a0e1e2-3d37-7111-bc1d-805954a52a16; Claude-sessie 99ef6e30-cc76-445a-932d-8c8bd578b835.

Eén extra functiebetekenis-test kwam na de fix; mutatiebewijs aanwezig, geen volledige TDD-claim. Providerattributie en transportlogging hebben expliciete grenzen in wp2-claude-groen-v1.md. Actions blijven uit. Geen nieuwe dependencies, geen productiegegevens. Echte calls zijn toegestaan; budgetkeuze staat open en blokkeert alleen de betaalde proef.
