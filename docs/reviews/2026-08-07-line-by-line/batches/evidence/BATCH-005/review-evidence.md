# BATCH-005 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-hypatia`
- Onafhankelijke verifier: `codex-galileo`
- Scope: 14/14 bereiken, 5181/5181 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle 14 immutable dependency-, rule- en lockblobs zijn gelezen; namespace-, lock-, RTF-, serializer-, middleware-, gitignore-, pytest- en pip-checkgates zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B005-001 — P2 — UV-hashlocks laten de dependency-confusion-gate nul dependencies controleren

**Bewijs:** Alle 92 runtime-items en alle 96 items in requirements-dev.txt beginnen als een uv-continuatieregel `naam==versie \` met hashes op vervolgregels. De actieve scripts/ci/check_namespace_collisions.py parseert iedere fysieke regel afzonderlijk met packaging.Requirement; de trailing backslash veroorzaakt InvalidRequirement en wordt stil als None overgeslagen. Een echte default-run op beide locks eindigt met exitcode 0 en meldt `geen packages in requirements*.txt — 23 src/-modules ongecontroleerd`, hoewel de locks samen 188 package-items bevatten. De pre-commitconfig roept deze guard als dependency-confusion-check aan. De 55 gerichte tests slagen maar bevatten geen uv-multiline/hashlockfixture.

**Reproductie:** Voer `python scripts/ci/check_namespace_collisions.py` uit en observeer exit 0 plus nul gevonden packages. Roep daarnaast `extract_distribution_name('services==1.0 \\')` aan: dat retourneert None, terwijl dezelfde regel zonder backslash `services` retourneert. `collect_distributions(DEFAULT_REQ_FILES)` retourneert op de immutable locks een lege set.

**Aanbevolen oplossing:** Parseer eerst volledige logische requirementrecords door backslashcontinuaties en pip-opties/hashes samen te voegen, en voer daarna packaging.Requirement uit. Laat de gate fail-closed stoppen wanneer niet-lege lockbestanden nul dependencies opleveren. Voeg regressietests toe met een echte uv-generated hashlock en een botsende src-modulenaam.

### B005-002 — P2 — Productie-lock mist de parser voor een actief aangeboden RTF-uploadpad

**Bewijs:** Noch requirements.in noch de gehashte runtime-lock bevat striprtf. Toch declareert document_extractor.py RTF als ondersteund en importeert het striprtf op regels 269-281. De actieve directe UI-caller src/ui/renderers/rag_management_renderer.py:224-280 biedt `.rtf` aan en accepteert iedere niet-lege retourwaarde. Zonder dependency retourneert de extractor de niet-lege waarschuwing `RTF extractie vereist striprtf library`; de UI kan die als documenttekst opslaan en daarna succes tonen. DocumentProcessor blokkeert zulke placeholders wel, maar de directe RAG- en chunkerflows niet.

**Reproductie:** Controleer requirements.in en requirements.txt op striprtf: geen match. Roep met de project-Python de extractor aan op een minimaal RTF-document; de retourwaarde is de niet-lege dependencywaarschuwing. Traceer daarna src/ui/renderers/rag_management_renderer.py:258-280: alleen leegte wordt afgewezen, waarna ingest_document en st.success volgen.

**Aanbevolen oplossing:** Voeg striprtf gepind toe aan requirements.in en regenereer de hashlock, of verwijder RTF uit de ondersteunde uploadtypen. Gebruik een typed extractionresultaat en laat directe RAG-, chunker- en processorflows dependency-/placeholderfouten uniform afwijzen; test een echt minimaal RTF-bestand in een schone runtime.

### B005-003 — P2 — Uitvoerbare Prompt-Forge-werklijst instrueert verouderde fixes en onveilige dependency-mutaties

**Bewijs:** Regels 5-6 instrueren een ontwikkelaar of agent deze werklijst uit te voeren. De eerste taak gebruikt `pip install bleach --break-system-packages` en wijzigt de gegenereerde requirements.txt rechtstreeks. Middleware- en pickleclaims zijn stale: SecurityHeadersMiddleware is actief en cache.py/resilience.py gebruiken safe_serializer. Het widgetdeel is slechts gedeeltelijk stale: drie custom multiline text_inputs gebruiken nog value+key in definition_edit_tab.py, terwijl de oude zes aantallen/locaties niet meer kloppen en overlappen met B042-003/B097-006. Het bestand blijft een zelfstandig, handmatig actief agent-entrypoint met onveilige multidomeinremediatie; het dependencydeel relateert aan B151-002.

**Reproductie:** Vergelijk regels 5-159 met de requirements-header/Make-lockflow, middlewarewiring, safe_serializer-imports en definition_edit_tab.py:541-546,632-637,672-677. Draai de twintig gerichte serializer-/wiringtests offline; zij zijn groen terwijl de operatorinstructie de oude fixes nog voorschrijft.

**Aanbevolen oplossing:** Markeer de maart-werklijst en beide rapporten expliciet als historisch/niet-uitvoerbaar of regenereer ze tegen een gepinde commit en actuele issue-status. Verbied `--break-system-packages` en directe edits aan generated locks; laat dependencywijzigingen uitsluitend via requirements.in plus make lock/lock-check lopen en laat elk taakrecept zijn paden en precondities in een schone checkout bewijzen.

### B005-004 — P3 — Bedoelde handover-uitzondering blijft door de uitgesloten parentdirectory genegeerd

**Bewijs:** Regel 133 sluit de volledige directory docs/archief/ uit. De negaties op regels 134-135 proberen docs/archief/handovers opnieuw toe te laten, maar Git kan een bestand niet opnieuw opnemen wanneer een bovenliggende directory volledig uitgesloten blijft. De base-tree bevat bestaande getrackte handovers, zodat het defect alleen nieuwe bestanden raakt en makkelijk onzichtbaar blijft.

**Reproductie:** Voer `git check-ignore -v --no-index docs/archief/handovers/new-handover.md` uit. Git retourneert exitcode 0 en wijst regel 133 (`docs/archief/`) aan, niet de twee bedoelde uitzonderingen.

**Aanbevolen oplossing:** Negeer de inhoud van docs/archief met een patroon dat de parentdirectory zelf traverseerbaar laat, bijvoorbeeld `docs/archief/*`, en behoud daarna de twee handover-negaties. Voeg een kleine check-ignore-regressietest toe voor een nieuw genest handoverbestand.

### B005-005 — P3 — Projectregel verbiedt zeven bestaande rootbestanden inclusief de canonieke lockbronnen

**Bewijs:** Regel 3 staat in de projectroot alleen README.md, CLAUDE.md, requirements*.txt, pyproject.toml, pytest.ini en .pre-commit-config.yaml toe. De immutable root bevat veertien bestanden waarvan zeven hierdoor verboden zijn: .gitignore, .gitleaks.toml, .gitleaksignore, CHANGELOG.md, Makefile, requirements.in en requirements-dev.in. Juist de uitgesloten Makefile en beide .in-bestanden vormen op Makefile:39-48 de canonieke make lock/lock-check-workflow. Een agent die deze verplichte regel volgt krijgt dus een contract dat strijdig is met de huidige repositoryarchitectuur.

**Reproductie:** Classificeer de blob-items uit `git ls-tree b958ddb...` tegen de letterlijke allowlist op regel 3. Van de veertien rootbestanden vallen er zeven buiten. Controleer daarna Makefile:39-48: beide uitgesloten requirements-*.in-bronnen zijn verplichte invoer voor de gehashte locks.

**Aanbevolen oplossing:** Vervang de statische incomplete allowlist door een expliciet actueel rootcontract of formuleer de regel als `geen nieuwe ongeaccordeerde rootbestanden`. Neem minimaal Makefile, requirements.in, requirements-dev.in en de security-/Gitconfigbestanden op en borg de lijst met een repositorytest zodat instructies en tree samen evolueren.

## Deduplicaties en afwijzingen

- Het dependency-mutatiegedeelte relateert aan B151-002; widgetstate-overlap valt onder B042-003/B097-006. De vijf hier geregistreerde roots blijven zelfstandig.

### B005-006 — P2 — Actieve aiohttp-client gebruikt een versie met een bereikbaar malformed-response-DoS

**Bewijs:** De immutable bron pint aiohttp==3.14.1 en requirements.txt:9 dezelfde versie. Het volledige runtime-auditbestand /private/tmp/pip-audit.json (SHA-256 6b5114c7fc88fe49ae1b287b6f4851919ecc1269c6996f93fd726325699393ca) meldt PYSEC-2026-3545/CVE-2026-69244 met fix 3.14.3 en twee WebSocket-advisories met fix 3.14.2. De applicatie maakt actieve ClientSession-GET-aanroepen naar externe diensten in rechtspraak_rest_service.py:47-72, sru_service.py:184-337, wikipedia_service.py:66-342, wikipedia_synonym_extractor.py:115-355 en wiktionary_service.py:48-208; modern_web_lookup_service.py:260-282 en 500-772 roept deze flows aan. Daardoor is de kwetsbare C-responseparser bereikbaar bij een malforme externe respons. Er is geen aiohttp-WebSocket- of servergebruik gevonden, zodat de twee overige advisories momenteel niet bereikbaar zijn.

**Reproductie:** Lees /private/tmp/pip-audit.json en selecteer aiohttp 3.14.1: PYSEC-2026-3545 noemt een out-of-bounds heap read en client-DoS met fix 3.14.3. Zoek vervolgens in de immutable base naar ClientSession en session.get in de vijf weblookupservices en naar ws_connect/aiohttp.web: de HTTP-clientcalls zijn aanwezig, WebSocket/servercalls niet. Een daadwerkelijke malforme netwerkrespons is wegens de veilige offline review niet verstuurd.

**Aanbevolen oplossing:** Pin minimaal aiohttp 3.14.3 in requirements.in, regenereer de universele hashlock via make lock en draai make lock-check, make audit en de gemockte weblookuptests. Gebruik AIOHTTP_NO_EXTENSIONS=1 alleen tijdelijk als upgraden werkelijk onmogelijk is; 3.14.2 is onvoldoende omdat CVE-2026-69244 pas in 3.14.3 is opgelost.

### B005-007 — P3 — Verouderde expliciete GitPython-pin houdt zeven advisories in de runtime-lock

**Bewijs:** De commentaarregel noemt een oudere gerepareerde advisory maar pint GitPython nog op 3.1.55; requirements.txt:507-512 bevestigt dat de package zowel expliciet als transitief via Streamlit wordt geïnstalleerd. Het actuele pip-auditbestand meldt zeven advisories met fixes verspreid over 3.1.56, 3.1.57 en 3.1.58, zodat alleen 3.1.58 alle zeven afdekt. Een volledige base-zoekactie vond geen import van git/GitPython en geen calls naar de kwetsbare Repo-, Commit-, IndexFile-, tag- of configuratie-API's. Exploit-reachability is daarom niet bewezen.

**Reproductie:** Selecteer gitpython uit /private/tmp/pip-audit.json: versie 3.1.55 bevat zeven advisories en de hoogste vereiste fixversie is 3.1.58. Zoek in src en scripts naar import git, from git, Repo, IndexFile, TagReference en de in de advisories genoemde methoden; er is geen toepasselijke caller. Controleer requirements.txt:510-512 voor de transitieve Streamlit-relatie.

**Aanbevolen oplossing:** Werk de beveiligingspin bij naar GitPython 3.1.58 en regenereer de hashlock, of verwijder de directe dependency als beleid transitieve packages niet direct pint en borg dat de resolver minimaal 3.1.58 kiest. Voeg een auditregressie toe die voorkomt dat een op een oude advisory gebaseerde expliciete pin later nieuwe fixes blokkeert.

### B005-008 — P2 — Actieve PyMuPDF-PDF/RAG-flow mist aantoonbare keuze tussen AGPL-compliance en commerciële licentie

**Bewijs:** requirements.in:50 en requirements.txt:1698 pinnen PyMuPDF 1.28.0. De immutable code dispatcht application/pdf naar _extract_pdf, importeert fitz en opent/verwerkt ieder PDF-document in src/document_processing/document_extractor.py:31-65,106-122. Dit pad is actief bereikbaar via DocumentProcessor, DocumentChunker en de Streamlit PDF-uploader/RAG-ingestie. De base-tree noemt het project Private / All rights reserved maar bevat geen LICENSE, COPYING, NOTICE, AGPL/source-offer of Artifex-licentieregistratie. De officiële PyMuPDF-documentatie stelt dat PyMuPDF/MuPDF onder AGPL of een commerciële Artifex-licentie beschikbaar is en noemt commerciële PDF-naar-RAG/data-pipelines expliciet als gebruik waarvoor die keuze relevant is. Dit bewijst een actieve compliancebeslissing, niet dat een externe commerciële overeenkomst ontbreekt of juridisch non-compliance vaststaat.

**Reproductie:** Inspecteer base b958ddb requirements.in:50 en requirements.txt:1698; traceer fitz.open vanuit document_extractor.py via de PDF-uploader/RAG-ingestie. Inventariseer de immutable tree op LICENSE, COPYING, NOTICE, AGPL en Artifex (geen resultaten). Vergelijk de gebruiksroute met de officiële PyMuPDF license- en FAQ-pagina. Trek uit repo-afwezigheid nadrukkelijk niet de conclusie dat geen extern contract bestaat.

**Aanbevolen oplossing:** Laat eigenaar/juridisch adviseur vóór distributie of deployment één basis vastleggen en verifiëren: een toepasselijke commerciële Artifex-licentie registreren, of een volledig passend AGPL-complianceprogramma documenteren en uitvoeren. Als geen van beide past, vervang PyMuPDF door een juridisch goedgekeurde parser. Voeg SBOM/licentiebeleid-CI en een niet-openbare contractreferentie toe.

## Niet getest

- Geen schone package-install/lockregeneratie, online advisoryfreshness, echte RTF-browserupload/RAG-persistence of operatoruitvoering van Prompt-Forge/Claude.
