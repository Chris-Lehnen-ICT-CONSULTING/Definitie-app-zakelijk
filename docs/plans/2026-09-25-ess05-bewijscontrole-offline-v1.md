# ESS-05 bewijscontrole — implementatieplan offline

> **For Claude:** REQUIRED SUB-SKILL: gebruik **executing-plans** via `/Users/chrislehnen/.agents/skills/executing-plans/SKILL.md` om dit plan uit te voeren. De oudere `superpowers:`-alias is hier niet vereist. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies.

**Goal:** de goedgekeurde optie C uit ADR-003 offline implementeren en verifiëren, inclusief contract, toetsdienst, consumers en voorbereiding van skills.

**Architecture:** een gesloten conceptoordeel doorloopt vaste bewijscontroles en één aparte semantische verificatie. Alleen een volledig gebonden en goedgekeurde combinatie wordt toegepast; de bestaande ESS-05-normstatussen blijven behouden. Concept, verificatie en toegepast oordeel blijven afzonderlijk en versiegebonden beschikbaar in de bestaande JSON-opslag.

**Tech Stack:** bestaande Python-, pytest-, Streamlit-, SQLite- en ModelRouter-infrastructuur; geen nieuwe dependency.

## Besluit en grenzen

Chris gaf op 25 september 2026 expliciet akkoord op offline implementatie inclusief contract-, parser- en bijbehorende skillwijzigingen. Leidende specificatie: [ADR-003](../adr/ADR-003-ess05-gestructureerde-bewijscontrole-v1.md), hash `78dcf7cb37ad93da790b69c16b758cff14a4835d6d438fb3de30fd27c7224909`. Onafhankelijke ontwerpreview zonder bevindingen: `logs/def768/ess05-bewijsontwerp-review-result-v1.md`.

Deze toestemming omvat de noodzakelijke omvang en contractbreuk van `/1` naar `/2`. Geen nieuwe appaanroepen, betaalde proef, modelwissel, installatie, sync, upload, commit, push, PR, merge of livegang. De laatste concrete vraag betrof alleen deze offline levering. Het cumulatieve callbudget blijft 359; R7 wordt niet heropend en de drie transportreservecalls zijn niet beschikbaar voor ontwikkeling van dit ontwerp.

Appwerkboom: `/Users/chrislehnen/.codex/worktrees/95eb/Definitie-app`; branch `feature/DEF-768-ess05-ai-beoordeling`; basis `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`. Skillswerkboom: `/Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-768-ess05-skills`, branch `feature/DEF-768-ess05-skills`. Bestaande R1–R7-wijzigingen behouden. Unieke herstelkopie vóór elke bron-/testwijziging; geen bestanden verwijderen.

## Rollen en uitvoering

- Coördinator: dit plan, acceptatiecriteria, start-/eindbinding en bewijscontrole. Schrijft geen productcode, tests of bijbehorende promptteksten; daarom bevat dit plan gedragscriteria in plaats van voorgeschreven implementatiecode.
- Appuitvoerder: bestaande Claude Code CLI-sessie `6d273f41-0afb-480a-9034-1c87b1ecba58`. Eigenaar van appcode, apptests en bijbehorende prompts; schrijft niet in skillswerkboom.
- Appreviewer: bestaande Codex CLI-sessie `01a0cfd5-6d5f-7b70-a259-9c19974f9264`, uitsluitend lezen/reviewen van de concrete diff.
- Skilluitvoerder: bestaande Claude Code CLI-sessie `8dc28dba-f6e1-47e9-8e58-8d60d3d1c4df`, na stabiele appcontractbinding. Skillreviewer `01a0d311-355a-7133-8291-f9b2e40dcc01`.
- Alleen de coördinator start deze CLI's. Geen uitvoerder/reviewer start agents of extra CLI's. Gebruik echte `~/.local/bin/claude`, geen wrapper.

De appcontract-/service-/consumerwijzigingen vormen één samenhangende levering: geen half gemigreerde keten opleveren. Uitvoerder meldt tussentijdse RED/GREEN-checkpoints en gaat binnen het mandaat door. Daarna één concrete diffreview; alleen bij echte bevindingen gerichte correctie en herreview door dezelfde personen. Skills volgen op de definitieve appbinding. Geen nieuwe gebruikersakkoorden tussen reeds geautoriseerde stappen.

## Werkpakketten app

### 1. Startbewijs en gesloten bewijscontract

**Bestanden:** `src/domain/ess05/contract.py`; nieuwe ESS-05-eigen module `src/domain/ess05/bewijs.py` indien nodig; `tests/unit/domain/test_def768_ess05_contract.py`; nieuw `tests/unit/domain/test_def768_ess05_bewijs.py`.

1. Leg startdiff en relevante bronhashes vast onder `logs/def768/bewijscontrole-offline/`; controleer branch, basis en historische manifests.
2. Schrijf falende tests voor het gesloten `/2`-concept, echte/niet-bestaande citaten, materiaal-ID's, dekkingscontrole, dubbele IDs, ontbrekende verplichte controles en afleiding van `lacks_differentia`.
3. Voer die tests uit en bewaar RED met concrete oorzaken.
4. Implementeer de contractvalidatie volgens ADR-003: bewijsplaatsen, claims, kenmerken, buren, voorstellen en vraag. Geen semantische juistheid claimen op grond van letterlijke aanwezigheid.
5. Voer dezelfde tests uit tot GREEN; refactor en draai de relevante tests/lint opnieuw.

### 2. Tweestapsdienst en transport

**Bestanden:** `src/services/validation/ess05_assessment_service.py`; eventueel nieuwe `src/services/validation/ess05_verification_service.py`; `src/services/validation/ai_beoordeling_transport.py` uitsluitend indien noodzakelijk; `src/services/ai/model_router.py`; de bestaande `model_routing`-configuratie; `src/services/container.py`; `tests/unit/validation/test_def768_ess05_assessment_service.py`; nieuw `tests/unit/validation/test_def768_ess05_verificatie.py`.

1. Schrijf en draai falende tests met een fake AI-service: eerste stap ongeldig → nul verifierverzoeken; geldig concept → precies één verifierverzoek; positieve complete verificatie → toegepast oordeel; afwijzing/timeout/afkapping/verkeerde hash → error zonder fallback.
2. Implementeer eerste-stap- en verificatieprompts en gesloten antwoorden. Verifier ziet oorspronkelijke norm/materiaal en concept, geen proeflabels. Geen casusgebonden regels of verborgen reparatie-/consensuslus.
3. Bind beide routerkeuzes, configuraties, prompts, schema-/rendererversies, concept en materiaal. Eigen verificatietaak gebruikt dezelfde geconfigureerde modelkeuze, geen hardcoded nieuw model. Geen wijziging van ESS-03-binding door gedeeld typegebruik.
4. Registreer beide attributies, ruwe antwoordhashes, fasen, tijd en tokengebruik. Leg begrensde timeout-/tokenafhandeling vast; nooit afgekapt materiaal als geverifieerd behandelen.
5. Draai de falende tests opnieuw; verifieer positieve `unclear`, lege kenmerkenlijst en afwezigheidsclaims naast foutgevallen.

### 3. Replay, cache en opslag

**Bestanden:** `src/domain/ess05/contract.py`; `src/domain/ess05/expertacties.py` voor noodzakelijke versie-/actualiteitsdoorwerking; `src/database/ess05_registratie.py`; `src/database/models.py`; `src/services/definition_edit_service.py`; `src/services/definition_repository.py`; `tests/unit/services/test_def768_ess05_persistentie.py`; `tests/unit/services/test_def768_ess05_editservice.py`.

1. Schrijf/draai RED: veranderd concept, materiaal, model of verifierprompt maakt oordeel niet-actueel; ontbrekende verificatie mag nooit een pass produceren; `/1` blijft historie; wijziging bewaart vorige beoordeling.
2. Implementeer gescheiden concept/verificatie/oordeel in bestaande JSON-opslag en ESS-05-eigen dubbele binding. Geen nieuwe tabel/kolom of backfill van verzonnen verificatie.
3. Controleer cachehits alleen bij volledige binding; errors worden niet als successen gecachet. Afgewezen voorstellen en buurbevestiging tellen mee in actualiteit.
4. GREEN voor echte tijdelijke repositoryopslag, teruglezen en gelijktijdige wijziging. Alleen lezen van historie veroorzaakt geen modelverzoek.

### 4. Wrapper, resultaatcontract en UI

**Bestanden:** `src/services/orchestrators/validation_orchestrator_v2.py`; `src/services/validation/evaluators/distinction_assessment.py`; `src/services/validation/interfaces.py`; `docs/architectuur/contracts/schemas/validation_result.schema.json`; `src/ui/components/definition_edit_tab.py`; `src/ui/components/validation_view.py`; bestaande DEF-768-wrapper-, weergave-, editor- en AppTest-tests.

1. Schrijf/draai RED voor volledig gecontroleerde pass/fail/open, technische verificatiefout, historische uitkomst en ontbreken van invoer.
2. Migreer consumers en zichtbare redenen. Geen vrije ongecontroleerde tweede paragraaf; ook ontbrekend kenmerk, voorstel, onzekerheid en vraag vallen onder verificatie.
3. Behoud statusprioriteit, één gerichte vraag, nulcallroutes en geldige expertbesluiten. Een verifierafwijzing is een onbruikbare uitvoering en geen afkeuring van de definitie.
4. GREEN voor opslag → wrapper → resultaat → UI. Controleer expliciet dat ongeverifieerde concepten niet als actuele geldige motivering verschijnen.

### 5. Offline proefinfrastructuur en regressies

**Bestanden:** `scripts/ess05/run_ess05_proef.py`; `scripts/ess05/proefgrootboek.py` alleen noodzakelijke voorbereiding; `tests/fixtures/def768_fakes.py`; bestaande `tests/unit/scripts/test_def768_*`; nieuw `tests/unit/scripts/test_def768_bewijscontrole_offline.py`.

1. Schrijf/draai RED voor twee fasen met afzonderlijke callregistratie/reservering en blokkade van ongeautoriseerde echte uitvoer. Geen nieuw actief proefbudget toevoegen. Historische rondes nooit passend maken door oude output te herschrijven.
2. Werk fakefixtures en offline keten door; nieuwe `/2`-fixtures zijn herkenbaar nieuw ontworpen, oorspronkelijke R1–R7-antwoorden blijven intact.
3. Gebruik R705/R712/R719 en positieve varianten als ontwerptegenvoorbeelden; een stub die correct weigert bewijst alleen de keten, niet het detectievermogen van de echte verifier.
4. Behoud semantische normregressies: overlap, te ruime kern, bronleemte versus kernfout, voorstelherkomst en ontbreken differentia. Geen testversoepeling om groen te krijgen; oude tekstvormasserties mogen gemotiveerd worden gemigreerd.
5. Maak huidige software ongeschikt voor echte calls via oude R7-freeze; bind de verifiercode/config in nieuwe bronidentiteit. Bewaar G-instructie en G-transport, en controleer alleen de daadwerkelijk geraakte gedeelde delen opnieuw.

### 6. Definitieve appverificatie en review

1. Voer gerichte tests per werkpakket uit met het bestaande projectprofiel. Gebruik `make test` als volledige unitgate; behoud projectregels rond integration-tests die netwerk kunnen starten.
2. Voer `make lint` uit; eventuele bestaande/onverwante fouten concreet scheiden van nieuwe fouten. Draai geen betalende integratietests. Gebruik gerichte offline integratie/AppTest voor de keten.
3. Geef exacte commando's, RED/GREEN-aantallen, exitcodes, skips en beperkingen in `logs/def768/bewijscontrole-offline-implementatie-resultaat-v1.md`. Geef einddiffidentiteit (ook nieuwe bestanden), materiaal-/code-/prompt-/configbinding en herstelkopieënmanifest.
4. Stop voor de coördinator, zonder zelf een reviewer te starten. Coördinator geeft dezelfde Codex CLI-reviewer het plan, ADR, start/einddiff en testbewijs.
5. Verwerk bevestigde bevindingen met dezelfde Claude-sessie; dezelfde Codex-reviewer controleert de correctiediff. Verifieer geraakte controles op uiteindelijke code. R7-semantische bevindingen blijven open tot echte modelproef.

## Werkpakket skills — na stabiele appbinding

**Bestanden in skillswerkboom:** `skills/definitie-toetsregels/references/ess05-onderscheid.md`; `skills/definitie-nederlandse-definities/references/ess05-onderscheid.md`; dezelfde vier reeds betrokken export-ZIPs en bestaande pakket-/exporttests. Bestaande skilluitvoerder bepaalt de exacte vier exportpaden vanuit v11, zonder andere ZIPs te raken.

1. Coördinator levert de definitieve gereviewde appcontract-/promptbinding, bronfragmenten en noodzakelijke instructiewijzigingen.
2. Skilluitvoerder bewaart unieke herstelkopieën en past beide contracten gelijk aan. Geen standalone skill als technisch geverifieerd presenteren als de appketen niet daadwerkelijk is aangeroepen; geen fictieve appkoppeling of nieuwe runner bouwen.
3. Behoud norm/G-betekenis; wijzig alleen noodzakelijke contractleden in dezelfde vier pakketten. Andere skillbestanden, acht andere ZIPs en legacyleden behouden.
4. Verifieer pakket-/exporttests en bytebinding; rapport `docs/2026-09-25-DEF-768-skillvoorbereiding-resultaat-v12.md` (vrije volgende versie gebruiken indien nodig). Zelfde skillreviewer controleert concrete diff en bronpariteit.
5. Geen liveinstallatie. Beperkingen van de standalone skill en uitgestelde semantische acceptatie blijven expliciet. Livepoorten appmerge en ALG-391 Task10 A–E blijven bestaan.

## Acceptatie van deze offline levering

- Gesloten structuur en verplichte volledige verificatiedekking; indicator wordt afgeleid; geen goedkeuring op alleen citaten.
- Precies de geautoriseerde tweestapsketen; geen verborgen inhoudelijke retry, fallback of reparatie.
- Versie-, model-, prompt-, concept- en materiaalbinding over cache, replay, opslag en UI; legacy alleen historie.
- Alle zichtbare inhoud onder verificatie; correcte onzekerheid en bestaande statusprioriteit behouden.
- Nul nieuwe echte appaanroepen; budget359 en historische bewijsbestanden intact; G-/normscope behouden.
- Relevante tests, projectgates en onafhankelijke concrete diffreview op dezelfde uiteindelijke software. Skills voorbereid en afzonderlijk gereviewd.
- Oplevering noemt CLI-sessies, logs, diffidentiteit en resterende semantische onzekerheid. Geen claim dat offline tests het modeldetectievermogen bewijzen.

Er is geen extra beslismoment nodig om deze goedgekeurde offline stappen te beginnen. Een echte proef met nieuwe modelaanroepen vereist later een concreet onderbouwd budgetbesluit.
