# DEF-835 — actuele takenlijst v23

28 september 2026. Vervangt v22 als actuele ingang. Branch `feature/DEF-835-int02-o2`; HEAD `f9bb9e6973926a3cf768995f5d879f6edfd6322d`.

- [x] Chris heeft F2/F3 en de configuratiesnapshot-API expliciet goedgekeurd; akkoord vastgelegd.
- [x] WP5a: optionele O2-integratie gebouwd en gecorrigeerd door Claude CLI; F1–F4 door dezelfde onafhankelijke Codex CLI-reviewer gesloten.
- [x] Dertien resterende WP1/WP2-typefouten hersteld door oorspronkelijke uitvoerders; beide oorspronkelijke reviewers akkoord, geen open bevindingen.
- [x] Eindcontrole op gecombineerde bron: **526 tests geslaagd**, mypy **geen fouten in 411 bronbestanden**, Ruff/Black groen. Bronhashes vóór en na controle gelijk.
- [x] Brede gerichte regressie vóór de typecorrecties: 2.966 tests geslaagd, nul overslagen. Dit is geen volledige-appsuiteclaim.
- [x] Normale lokale commit `f9bb9e697` geslaagd: 10 code/testbestanden plus 60 opdrachten, verslagen en bewijsbestanden. Gitleaks en toepasselijke hooks geslaagd; geen hookbypass, geen scanverkleining.
- [x] Na commit: alle 10 bronblobs exact gelijk aan eindmanifest-v5; index leeg en geen resterende getrackte bronwijzigingen in src/tests.
- [x] O1 blijft actief (`judgment_review`); Actions opnieuw alleen-lezen gecontroleerd: `enabled=false`. Geen push, merge, activering of nieuwe liveappcalls.
- [ ] **WP4 modelkwalificatie:** onafhankelijke goldset/hold-out, benoemde inhoudelijke beoordelaars en vooraf vastgestelde kwaliteitsgrenzen; daarna nieuw begrensd proefbesluit. De eerdere 3-callproef is verbruikt; C107/C112 leverden geen geslaagd kwalificatiebewijs.
- [ ] **WP5 vervolg:** gedeelde opslag/historie/herladen/C118, UI/export en ketenlogging. DEF-626 staat bij actuele Linear-controle nog Backlog. Een afgebakend vervolgplan en de vereiste schema-/contractbesluiten moeten vooraf worden vastgesteld; geen parallelle INT-02-opslagroute.
- [ ] **WP6:** finale O2-acceptatie, PR/oplevering en afzonderlijke activering na bewijs. Twee eerder op de basis aangetoonde performance_tracker-fouten blijven benoemd; geen volledige groene-suiteclaim.

Geen CLI-processen actief. Er staat geen akkoordvraag meer open voor F2/F3 of de typecorrecties. Volgende noodzakelijke stap: de nog ontbrekende goldsetbesluiten en het afgebakende opslag-/UI-vervolg concreet vaststellen; deze vallen buiten het afgeronde WP5a-pakket. Actuele details: `processtatus-uitvoering-v11.md`; geleverde inhoud en bewijs: `oplevering-wp5a-v1.md`. Lokale volledige CLIstreams en herstelkopieën zijn behouden; niet alle historische uitvoeringsartefacten zijn gecommit.
