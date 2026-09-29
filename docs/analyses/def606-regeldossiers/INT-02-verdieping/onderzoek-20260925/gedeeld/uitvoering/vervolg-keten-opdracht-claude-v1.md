# DEF-771 — vervolgopdracht: offline ketenverificatie

Jij bent de bestaande Claude Code CLI-uitvoerder, sessie a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Alles Nederlands. De coördinator vraagt zo nodig dezelfde Codex-reviewer om controle. Je bent niet alleen in de codebase: raak ander werk niet aan en draai geen wijzigingen terug.

## Mandaat

Chris gaf op 26 september akkoord om eerst de skill-CI en ontbrekende ketenverificatie af te handelen, vervolgens een onderbouwd merge-/uitrolvoorstel voor te leggen. Geen merge, uitrol, modelaanroep, productiedata, nieuwe dependency, schema-/contractwijziging, poort of herstelroute. DEF-626/830 blijven buiten scope. GitHub-skill-CI heeft een accountbillingblokkade; dit is door de coördinator onderzocht. Jij doet uitsluitend de ketenverificatie.

App /Users/chrislehnen/Projecten/Definitie-app, branch feature/DEF-771-int02-contract-o1, HEAD e9a865b856ca6dba85ee73bedc0e303f05fa86fb. Productiecode gelijk aan beoordeelde 9ff3eac199c3eb6e77a44ee47220f91226ffed44. Skillwerkboom /Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills op 750068253a7389e201daedc5b9aa0afd5c0be032, uitsluitend leesbron.

Lees de bestaande bronnen alleen waar nodig: gedeeld/besluiten-chris-v1.md, synthese v5 §4/§10, casusregister v5, uitvoering/wp5-eindverificatie-v1.md en takenlijst-v6.md. Geen normonderzoek herhalen. Repo CLAUDE.md en relevante rules blijven gelden.

## Concrete open vraag

Welke onderdelen van invoer → echte validatieservice → publieke rule_results → zichtbare UI-passagehulp → synthetische opslag → herladen → bestaande vaststel-/exportroutes behouden INT-02 RR/NE en passagecitaten? Welke onderdelen verliezen informatie of hebben geen aangesloten implementatie? Geen volledige keten claimen op basis van alleen losse mocks.

1. Inventariseer gericht bestaande functies en bruikbare offline tests. Start met tests/unit/ui/test_def771_int02_validation_view.py, tests/unit/services/test_def622_readback_en_export.py, tests/unit/services/test_def622_koppelingen_export_readback.py, tests/unit/services/policies/test_approval_gate_policy.py en bestaande repositorytests. Traceer daadwerkelijke aanroepen/velden. Neem drie synthetische gevallen: RR met marker (C83 of behouden C04), RR zonder marker (C105), NE (C06/C23/C56). Lees exacte casusteksten uit register. Geen nieuw semantisch oordeel.
2. Voer bestaande gerichte tests uit die de ontbrekende schakels daadwerkelijk bewijzen. Python .venv/bin/python; vóór appimports bestaande tests/offline_bootstrap gebruiken. Alleen tmp_path/in-memory synthetische database, geen data/definities.db, .env of andere productiebestanden lezen. Geen live server/app met de normale database starten.
3. Indien bestaande tests onvoldoende zijn, mag je maximaal één nieuwe diagnostische replay onder uitvoering/ schrijven (hoogstens 100 regels uitvoerbare code) met uitsluitend synthetische invoer en geïsoleerde opslag, plus log/JSON-bewijs. Jij schrijft deze zelf; coördinator schrijft geen testcode. Geen bestaande bron-/testbestanden aanpassen. Past een betekenisvolle proef niet binnen deze grens, rapporteer exacte benodigde bestanden/omvang voordat je verder gaat. Een nieuwe feature bouwen of een productiegat repareren is in deze fase niet toegestaan.
4. Leg per schakel de exact aangeroepen functie, wat werkelijk is uitgevoerd, uitkomst, bronregels, mocking/isolatie en bewijsgrens vast. Is bestaande code bijv. afhankelijk van DEF-626 voor behoud bij herladen, toon dat gericht en meld het; geen workaround of stille scope-uitbreiding.
5. Bewaar volledig commando/output/exitcodes en je rapport met vrije namen vervolg-keten-*. Geen oude bestanden overschrijven of verwijderen. Geen commits/push/PR. Gebruik bestaande volledige suite als basis; geen nieuwe volledige run voor een lees-/diagnoseopdracht.

Rapporteer uiteindelijk: aantoonbaar werkende delen, concrete open bevindingen met reproductie, eventueel klein correctievoorstel met exacte bestanden/omvang/acceptatie, en welke vervolgstap zonder nieuw akkoord kan. Stop daarna.
