# INT-02 O2 — C107 blokkeert modelkwalificatie (takenlijst v50)

30 september 2026. Vervangt v49 als procesingang; oudere bestanden blijven historisch bewijs.

- [x] Nieuwe lokale sleutel en verhoogde uitvoerroute gebruikt onder het exact gebonden v2-akkoord.
- [x] Anthropic-bereikbaarheid en gebruik vastgesteld: twee tokenmetingen en twee inferenties met HTTP 200, standaard/global, samen US$0,05109.
- [x] C105 leverde het verwachte `fail`. C107 leverde ruwe `fail` en een citaatinterval dat één codepunt te laat begint; het contract wees dit terecht af als `invalid_citation`. De regressiefase stopte, C112 is niet uitgevoerd. Bewijs: `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-uitvoeringsverslag-v2.md`.
- [x] Gerichte promptcorrectie `/2` als voorstel uitgewerkt, zonder code of norm te veranderen: `goldset-voorbereiding/goldset-freeze-v1/promptcorrectie-voorstel-v1.md`.
- [ ] Chris bespreekt/accordeert de promptbuildercorrectie conform `CLAUDE.md`.
- [ ] Na akkoord: Claude Code CLI schrijft offline eerst rode tests, dan promptversie `/2`; aparte verse Codex CLI-sessie reviewt de diff. Geen hold-outinhoud in hun context.
- [ ] Daarna nieuw exact gebonden manifest, nieuw begrensd proefakkoord en eerst opnieuw regressie. Geen v2-retry.
- [ ] Alleen na geslaagde regressie ontwikkeling en hold-out; daarna appintegratie en afzonderlijk activeringsbesluit.

O2 en Actions blijven uit. Geen codewijziging, push of merge in deze stap.
