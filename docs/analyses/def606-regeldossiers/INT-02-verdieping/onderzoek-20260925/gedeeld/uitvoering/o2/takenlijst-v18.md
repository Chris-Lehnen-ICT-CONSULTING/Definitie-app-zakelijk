# DEF-835 — actuele takenlijst v18

28 september 2026. Vervangt v17 als actuele ingang. Branch `feature/DEF-835-int02-o2`, basis `979ca0585100d94b613829d924c6d8bba4f24f1b`.

- [x] WP1–WP3 en technische proefrunner geïmplementeerd, getest en onafhankelijk gereviewd; bewijs uit v17 blijft geldig voor die commits.
- [x] Chris heeft proefprofiel/budget en WP5a goedgekeurd; zie besluit-proef-en-wp5a-v1.md.
- [x] Technische live proef uitgevoerd: drie calls, US$0,07814 berekende kosten; C105 verwacht fail, C107 onverwacht fail, C112 error wegens ongeldige citaatposities. Zie modelproef-live-verslag-v1.md. Geen kwalificatieclaim.
- [x] WP5a-opdracht schriftelijk vastgelegd en Claude Code CLI gestart, sessie 914fccdd-7899-4d5c-8aa0-1c9ab334d7d4.
- [ ] WP5a: zeven bestanden, optionele injectie, O1 blijft actief; offline TDD en regressietests lopen bij Claude.
- [ ] WP5a: concrete diff door verse Codex CLI laten reviewen; bevindingen door dezelfde uitvoerder corrigeren, bewijs verifiëren.
- [ ] Dossiercommit: twee bronhash-false-positives blokkeren normale secretcontrole. Exact voorstel met regressietests voorgelegd aan Chris; geen uitzondering toegepast. 38 bestaande staged bestanden intact houden.
- [ ] WP4: onafhankelijke goldset/hold-out en inhoudelijke modelkwalificatie, inclusief C107/C112-bevindingen.
- [ ] WP5 vervolg: gezamenlijk opslagcontract DEF-626, historische snapshots, herladen, UI/export en ketenlogging.
- [ ] WP6: finale verificatie/PR en afzonderlijke activering.

Actions blijven uit. Geen push, merge of activering. Het maximum van drie live proefcalls is gebruikt; WP5a gebruikt uitsluitend offline fakes. De bestaande O1-route blijft actief. De actuele CLI-uitvoering verandert nog geen commit; finale diff-identiteit volgt na afronding.
