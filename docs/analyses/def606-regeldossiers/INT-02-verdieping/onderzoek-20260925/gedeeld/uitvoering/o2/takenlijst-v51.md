# INT-02 O2 — prompt /2 gereed, v3-manifest wacht op exact proefakkoord

30 september 2026. Vervangt v50 als procesingang; eerdere versies en v1/v2-proefbewijzen blijven bewaard.

- [x] Chris gaf akkoord op `promptcorrectie-voorstel-v1.md` en vroeg direct door te gaan met O2.
- [x] Claude Code CLI schreef eerst prompttests; coördinator draaide 5 rood / 57 groen vóór code. Daarna beperkte implementatie van prompt `/2`.
- [x] Definitieve gerichte offline run: 452 geslaagd; Ruff, Black en diffcheck schoon. Bron- en loghashes: `goldset-voorbereiding/goldset-freeze-v1/promptcorrectie-testbinding-v1.md`.
- [x] Afzonderlijke verse Codex CLI-review: geen blocker; de ene bewijsopmerking is met `promptcorrectie-testbinding-v1.md` afgehandeld.
- [x] Nieuw offline `kwalificatie-manifest-v3.json` en labelvrije payloads aangemaakt; exacte hashes en grenzen in `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-voorstel-v3.md`.
- [ ] Chris geeft afzonderlijk akkoord op de exacte v3-manifest- en gevallenhash volgens het bestaande protocol.
- [ ] Na akkoord alleen de drie bekende regressies live draaien; bij elke stopregel bewijs vastleggen en niet automatisch herhalen.
- [ ] Na geslaagde regressie ontwikkeling en hold-out volgens protocol; daarna inhoudelijke grondbeoordeling door Chris, appintegratie en afzonderlijk activeringsbesluit.

O2 en Actions blijven uit; geen push of merge in deze stap.
