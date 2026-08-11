# BATCH-179 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 19/19 bereiken, 5815/5815 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable documenten zijn gelezen; privacy-, schema-, API-, teststrategie- en gerichte pytestreproducties zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B179-001 — P2 — Promptopslagspecificatie stelt volledige PII-bevattende prompts en tracebacks centraal beschikbaar zonder privacycontrols

**Bewijs:** De READY FOR IMPLEMENTATION-specificatie kiest expliciet voor opslag van de volledige prompt van 10KB+ (regels 101-104), maakt prompt_full_text verplicht (132-133) en bewaart error_traceback (174-177). De optionele detail-UI toont de volledige prompt (870-872) en een CSV-export staat gepland (1061-1066). De securitysectie erkent dat prompts PII kunnen bevatten, maar schuift redactie door naar Phase 2 (1007-1016) en noemt alleen dezelfde toegangscontrole als definities en cascade-delete. Alle acht benoemde implementatie- en testpaden ontbreken op de base, zodat dit een nog-dormant maar concreet onveilig ontwerpcontract is.

**Reproductie:** Lees regels 101-177 en 1007-1025 uit blob c6faeb3853c2b6715268dff17e520041089e6fb6. Controleer met git cat-file -e de acht genoemde migration/model/service/repository/UI/testpaden; ieder ontbreekt. Vul conceptueel een context met e-mail/BSN in: volgens het gekozen schema komt die tekst ongeredigeerd in prompt_full_text en mogelijk in traceback, view, UI en export terecht.

**Aanbevolen oplossing:** Maak dataminimalisatie een must-have vóór implementatie: sla standaard alleen templateversie, gehashte/gestructureerde variabelen en gesaniteerde foutcodes op; redacteer PII vóór persistence; versleutel en autoriseer een eventueel afzonderlijk auditarchief; leg doel, bewaartermijn, inzage/verwijdering en exportbeleid vast; voeg negatieve PII- en autorisatietests toe voordat de migratie mag landen.

### B179-002 — P3 — Actieve canonieke agentarchitectuur vereist een workflow-router en elf agents die in de huidige omgeving niet bestaan

**Bewijs:** Het document beschrijft ~/.claude/agents/workflows/workflows.yaml, drie workflows en elf agents en maakt de router later verplicht. Op de gecontroleerde host bevat ~/.claude/agents alleen README.md, code-simplifier.md en security-reviewer.md. Die externe configuratie heeft echter geen repositorycaller en kan op een andere host bestaan; alleen de hostgebonden stale instructie is bewezen, niet P2-reachability.

**Reproductie:** Lees regels 19-48 en 317-362 uit blob 43e75f82f158115f70ee484e80278e0627095b57. Voer find ~/.claude/agents -maxdepth 2 -type f uit: alleen README.md en twee agents verschijnen, zonder workflows-directory. Een maintainer kan daardoor het verplichte tweestappenprotocol niet starten.

**Aanbevolen oplossing:** Markeer deze analyse superseded of lever de workflows als versiebeheerbare Codex/Claude-plugin met een gegenereerde agentinventaris. Laat een documentatiegate alle genoemde agent- en workflow-ID's tegen de werkelijk geïnstalleerde configuratie valideren en bied een werkend fallbackproces wanneer externe agents ontbreken.

### B179-003 — P3 — Canonieke Anders-root-causeanalyse bevat niet-reproduceerbare code-, gebruikers-, prestatie- en aansprakelijkheidsclaims

**Bewijs:** Het definitieve/canonieke, expliciet op v1.0 gerichte document claimt 100% uitval, 0% ASTRA/NORA-compliance en EUR 50K aansprakelijkheid per definitie (23-33), later 17,5x vertraging en 2,8x geheugengebruik (182-190) plus 15 dagelijkse meldingen en vijf bevestigende gebruikers (254-257), maar koppelt geen run, dataset, ticket, logbestand of commit. De aangewezen huidige base-regels src/ui/tabbed_interface.py:641-662 bevatten testknoppen in plaats van de getoonde cleanupcode; het genoemde context_selector.py ontbreekt en de hardcoded waarden zijn niet in de actuele selectorcode aanwezig. Het document blijft vanaf ADR-005 en de implementatieroadmap bereikbaar.

**Reproductie:** Vergelijk regels 23-53, 182-190 en 238-257 uit blob f906f7819646cb33702f38edb47dc7312f7b8149 met git show b958ddb:src/ui/tabbed_interface.py rond 641-662 en git cat-file -e voor src/ui/components/context_selector.py. Zoek vervolgens de genoemde testwaarden en bewijsartefacten in de immutable tree; de codeverwijzingen reproduceren niet en ondersteunende meetdata ontbreekt.

**Aanbevolen oplossing:** Label het document prominent als historische, niet-geverifieerde analyse of pin de exacte onderzochte commit. Vervang juridische, gebruikers- en prestatiegetallen door links naar geanonimiseerde meetartefacten met methode en datum; genereer codeverwijzingen tegen die commit en link vanuit huidige ADR's naar de bewezen huidige status.

### B179-004 — P2 — Promptopslagschema blokkeert zowel pending logs als meerdere generatiepogingen

**Bewijs:** De specificatie maakt definitie_id tegelijk NOT NULL en UNIQUE, terwijl create_pending_log() vóór definitieopslag een rij zonder definitie_id invoegt en de zelfde specificatie meerdere generatiepogingen per definitie belooft. De schema- en lifecyclecontracten zijn daardoor onderling onuitvoerbaar.

**Reproductie:** Voer het gedocumenteerde schema in een in-memory SQLite-database uit: de pending insert faalt met NOT NULL constraint failed. Geef daarna twee pogingen dezelfde definitie_id; de tweede faalt met UNIQUE constraint failed.

**Aanbevolen oplossing:** Gebruik een aparte attempt/session-identiteit en een nullable pending foreign key of een afzonderlijke pendingtabel. Maak de overgang naar een definitie atomair en test pending, linking, failure en meerdere pogingen.

### B179-005 — P2 — Canonieke uploadgids belooft metadata-only logging terwijl productie ruwe bestandsnamen logt

**Bewijs:** De canonieke, vanuit README en de actieve uploadflow bereikbare gids zegt dat alleen type, duur, status en lengte worden gelogd. DocumentProcessor logt de ruwe bestandsnaam op de succes-, fout- en evictionpaden, zodat namen dossier- of persoonsinformatie kunnen lekken naar operationele logs.

**Reproductie:** Verwerk veilig een tijdelijk bestand met naam ALICE-CASE-SECRET.txt en capture de logs. De volledige naam verschijnt in `Document ALICE-CASE-SECRET.txt succesvol verwerkt`, in strijd met het beschreven metadata-only contract.

**Aanbevolen oplossing:** Log alleen document-ID, type, grootte of een keyed hash; sanitize ook foutdetails en bestandsnamen. Voeg een privacyregressietest toe die gevoelige sentinelbestandsnamen in alle logrecords verbiedt.

## Deduplicaties en afwijzingen

- B179-002 is afgewaardeerd naar P3 wegens hostgebonden externe configuratie; promptprivacy en schemacontracten blijven zelfstandig.

## Niet getest

- Geen live GitHub/Prometheus/AI/netwerk/credentials, productiedata, juridische AVG-certificering of Streamlit/browser/a11y-runtime.
