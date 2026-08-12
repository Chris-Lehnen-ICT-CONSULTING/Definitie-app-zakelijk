# BATCH-004 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-kierkegaard`
- Scope: 26/26 bereiken, 5226/5226 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle 26 immutable configuratieblobs zijn gelezen; parser-, gitleaks-, pre-commit-, configconsumptie-, pytest-, lint-, type- en pincontroles zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B004-001 — P1 — Globale Gitleaks-allowlists schakelen secret-detectie uit voor alle tests en documentatie

**Bewijs:** De globale allowlists noemen onder meer `.*test_.*.py`, tests/security en vrijwel alle documentatiepaden, maar zetten geen AND-condition. Gitleaks combineert deze criteria daardoor als alternatieven: alleen het pad is voldoende om iedere secretmatch te onderdrukken. De configuratie is actief in pre-commit en de securityworkflow.

**Reproductie:** Scan met de baseconfig drie tijdelijke Git-repositories die elk dezelfde synthetische, niet-echte PAT-vorm bevatten. Met lokaal gitleaks 8.28.0 geven docs/ en tests/ exitcode 0 en nul findings; dezelfde inhoud onder src/ geeft exitcode 1 en één finding. Dit bewijst dat het pad, niet alleen het voorbeeldpatroon, wordt toegestaan.

**Aanbevolen oplossing:** Gebruik per uitzondering `condition = "AND"` met zo smal mogelijke path-, regex- en/of stopwordcriteria; sta nooit hele test- of documentatiebomen toe. Voeg in pre-commit/CI adversarial secret-canaries toe voor iedere toegestane padklasse.

### B004-002 — P2 — Pre-commit smokehook maskeert iedere test- en runnerfout als succes

**Bewijs:** De hook voert `pytest -m smoke --tb=short --maxfail=1 -q || true` uit. `|| true` converteert testfailures, collection/importfouten en een ontbrekende runner allemaal naar exitcode 0, zodat de hook geen blokkade kan vormen.

**Reproductie:** Voer exact de hookcommand uit met PATH=/usr/bin:/bin. Bash meldt `pytest: command not found`, maar de volledige command retourneert exitcode 0.

**Aanbevolen oplossing:** Verwijder `|| true`, voer pytest via een reproduceerbare projectinterpreter uit en laat elke onverwachte niet-nulstatus door. Modelleer een eventuele bewust niet-beschikbare smokeomgeving afzonderlijk als expliciete skip, niet als algemeen succes.

### B004-003 — P2 — AI-service leest rate-limitwaarden uit de verkeerde configuratiesectie

**Bewijs:** De YAML definieert requests_per_minute=60, requests_per_hour=1000 en max_concurrent_requests=10 onder `rate_limiting`. ConfigManager materialiseert die sectie als `rate_limiting`, terwijl AIServiceV2 regels 79-94 niet-bestaande `rate_limit_*` attributen onder `api` leest en daardoor terugvalt op 60/3000/10. Ook RATE_LIMIT_RPM/RPH-overrides landen in de genegeerde sectie.

**Reproductie:** Laad de baseconfig met ConfigManager en construeer AIServiceV2 met netwerkclients gemockt. De config rapporteert 60/1000/10; de service rapporteert 60/3000/10, en `api` heeft de gezochte rpm/rph-attributen niet.

**Aanbevolen oplossing:** Construeer RateLimitConfig vanuit `config_mgr.rate_limiting`, map de daadwerkelijke veldnamen expliciet en valideer grenzen. Voeg contracttests toe met afwijkende YAML-waarden en environment-overrides.

### B004-004 — P2 — Weblookup-hoofdschakelaar en drie ingeschakelde providers hebben geen runtime-effect

**Bewijs:** De configuratie bevat `web_lookup.enabled` en schakelt eur_lex, wikidata en dbpedia in. ModernWebLookupService._setup_sources leest de hoofdschakelaar niet en bouwt voor die drie providers geen source. Daardoor kan globaal uitschakelen de zeven wel gebouwde sources niet stoppen en zijn drie geconfigureerde providers nooit beschikbaar.

**Reproductie:** Monkeypatch offline de geladen config naar global enabled=false met eur_lex/wikidata/dbpedia enabled=true en construeer de service met providerclients gemockt. `global_enabled=False`, maar de runtime bevat brave_search, overheid, overheid_zoek, rechtspraak, wetgeving, wikipedia en wiktionary; dbpedia, eur_lex en wikidata ontbreken.

**Aanbevolen oplossing:** Gebruik een getypeerd providerschema, blokkeer de volledige service wanneer de hoofdschakelaar uit staat en faal bij een ingeschakelde maar niet-ondersteunde provider. Test exacte gelijkheid tussen geconfigureerde en gebouwde providers.

### B004-005 — P2 — De vermeende toetsregels-single-source-of-truth voert vrijwel geen beleidssecties uit

**Bewijs:** De configuratie declareert laadbeleid, prioriteiten, scoring, uitvoering, caching, validatie, dependencies, rapportage, tests en overrides. In de immutable base laadt alleen violation_builder.py dit bestand en leest uitsluitend `violation_category_prefixes`; de overige beleidssecties hebben geen productieconsumer. De 119 relevante groene tests oefenen alleen configuratiebasics en de externe categoriemapping uit.

**Reproductie:** Zoek exacte bestandsnaam en top-level sleutels in alle baseblobs en traceer iedere YAML-loader. Alleen violation_builder.py opent dit bestand en gebruikt de prefixmapping; er bestaat geen runtimepad dat bijvoorbeeld require_both_formats, execution, scoring of dependencybeleid toepast.

**Aanbevolen oplossing:** Maak één getypeerde loader de daadwerkelijke bron voor managers/services en faal op onbekende of inerte sleutels; voeg mutation/contracttests per beleidssectie toe. Verwijder of archiveer secties die bewust alleen documentatie zijn.

### B004-006 — P3 — Trunk declareert een afwijkende Python- en linttoolchain buiten de pin-consistentiecheck

**Bewijs:** Trunk pint Python 3.10.8, gitleaks 8.28.0, black 25.9.0, ruff 0.14.3 en isort 7, terwijl de canonieke projecttooling Python 3.13, gitleaks 8.29.1, black 26.5.1 en ruff 0.15.20 gebruikt en isort expliciet door Ruff is vervangen. `check_tool_pins.py` meldt groen omdat het Trunk niet controleert. Geen CI-caller voor Trunk werd gevonden, dus de impact is lokaal/dormant.

**Reproductie:** Vergelijk de baseblobs `.trunk/trunk.yaml`, `.pre-commit-config.yaml` en `requirements-dev.txt` en voer `python scripts/check_tool_pins.py` uit. De versies wijken aantoonbaar af terwijl de check `consistent across all sources` rapporteert.

**Aanbevolen oplossing:** Verwijder de ongebruikte Trunkconfig of lijn alle versies en linters uit. Neem iedere behouden tooldeclaratie op in de pin-check en test dat lokale en CI-tools dezelfde configuratie en Pythonversie gebruiken.

### B004-007 — P3 — Meerdere omvangrijke production-gelabelde ontologieconfiguraties hebben geen runtimeconsumer

**Bewijs:** ufo_rules.yaml (v2, 16 categorieën), ufo_rules_v5.yaml (v5, 10 categorieën, `production-ready`) en category_patterns.yaml (4 categorieën) definiëren onderling verschillende classificatiecontracten. Exacte pad- en filenaamtracering in src/tests/scripts vindt voor geen van deze bestanden een loader; de actieve improved classifier gebruikt config/classification/term_patterns.yaml. De bestanden zijn dus dormant configuratieschaduw, geen huidige runtimepolicy.

**Reproductie:** Inventariseer alle YAML-open/load-calls in de base en zoek exacte bestandsnamen `ufo_rules.yaml`, `ufo_rules_v5.yaml` en `category_patterns.yaml`. Er zijn geen consumers; construeer vervolgens de actieve classifier en observeer dat die term_patterns.yaml laadt.

**Aanbevolen oplossing:** Wijs één getypeerde en geversioneerde ontologieconfiguratie als canoniek aan en archiveer of verwijder de overige na expliciete toestemming. Voeg een reachability- en schemacheck toe die production-gelabelde config zonder consumer afkeurt.

## Deduplicaties en afwijzingen

- Feature-statusinjectie/statusgates en approval-gatedrift dedupliceren naar B100-007, B106-013 en B039-003/B047-003.

## Niet getest

- Geen live GitHub-/pre-commit-hosted execution, externe Trunk-run, echte weblookup- of AI-providercall, netwerk, credentials of UI/browserflow.
