## 📋 PR Type
- [x] 🐛 Bug fix

## 📄 Description
ESS-03 keurde telbaarheid af of goed op trefwoorden voor nummers en identifiers. De regel vraagt nu een scoreloos menselijk oordeel: passende begripskenmerken of natuurlijke grenzen kunnen instanties onderscheiden; een naam, nummer of ISBN is op zichzelf geen identiteitsbewijs.

## 🔗 Backlog Link
Ref: https://linear.app/definitie-app/issue/DEF-766 (onder DEF-606)

## 🎯 Changes Made
- Regelkaart, voorbeelden en generatie-/toets-/herstelinstructies volgen dezelfde telbaarheidsnorm.
- ESS-03 gebruikt `judgment_review`, `review_required` en `no_score`, met term en definitietekst als vereiste invoer. De oude semantische trefwoordroute is verwijderd.
- Bestaande UI toont de open beoordelingsvraag; ontbrekende invoer en technische fouten blijven afzonderlijk. Geen nieuwe gate of automatische reparatie.

De generieke opslag, teruglezing en afronding van menselijke oordelen en bevestigde niet-toepasselijkheid blijven open onder DEF-624. Dit is de afgebakende bugfix, geen volledige afsluiting van DEF-766.

## 🧪 Testing
- [x] `make test`: 6616 passed, 75 skipped, 722 deselected, 1 xfailed; exit 0.
- [x] `make lint`: Ruff en Black exit 0.
- [x] Offline ketentest: 3 passed; 13 onderzoekscasussen via twee echte servicelaadpaden: 26/26 verwacht, geen ESS-03-cijfer of violation.
- [x] Laatste opmaakcorrectie voor gepinde Ruff v0.16.5: AST identiek; beide ESS-03-testbestanden 65 passed; normale pre-commit-hooks groen.
- [x] Claude Code CLI implementeerde en corrigeerde; afzonderlijke Codex CLI keurde de einddiff en de gerichte opmaakdelta goed. Sessies en bewijs staan in het uitvoeringsverslag; eindmanifest-v3 SHA256 `48d837aa5019d20908ac66cc1bbab7800f5655d4c1a43e7e4023afd88165e477`.

Dit bewijst de afgebakende norm/runtime/promptaanpassing; geen volledige expert-UX-acceptatie of afgeronde menselijke reviewketen.

## 🔄 Migration Required
- [x] Geen databasemigratie, nieuwe dependency of nieuwe publieke status toegevoegd.

## 📚 Documentation
Uitvoeringsverslag: `docs/analyses/def606-regeldossiers/ESS-03-fix/2026-09-18-uitvoering-v1.md` (vastgelegde stand vóór publicatie). CLI-logs, testbewijs en de latere publicatie-lintcontrole zijn lokaal bewaard onder `reports/DEF-766-20260918*`.

## 🚀 Deployment Notes
Bijbehorende skillbronnen en Cowork-pakketten zijn gepubliceerd via https://github.com/ChrisLehnen/claude-global-setup/pull/334. De ALG-391-publicatiestop houdt live-installatie tegen; actieve installatie is niet geclaimd. Geen automatische sluiting van DEF-766 of verbreding van DEF-751-verduidelijkingsgedrag.
