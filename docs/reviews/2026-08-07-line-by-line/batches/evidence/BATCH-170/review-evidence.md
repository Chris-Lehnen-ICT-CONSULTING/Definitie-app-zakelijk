# BATCH-170 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 16/16 bereiken, 5847/5847 fysieke regels en 29/29 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable bronnen en symbolen zijn gelezen; import-, config-, CI-context-, Git-policy-, fuzzy-duplicate- en gerichte pytestreproducties zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B170-001 — P2 — Canonieke agentrichtlijn staat kleine verwijderingen en bestaande-bestandsformattering zonder toestemming toe

**Bewijs:** De Approval Ladder zet formattering van bestaande bestanden bij AUTO-APPROVE en vraagt voor verwijderen alleen toestemming bij meer dan vijf bestanden of kritieke paden. Regels 427-439 noemen dit document bovendien de SSoT voor agentgedrag. Dit botst met de actuele projectregel dat iedere verwijdering en iedere Write op een bestaand bestand expliciete toestemming vereist; een agent of mens die deze actieve richtlijn volgt kan dus onbedoeld gebruikerswerk wijzigen of verwijderen.

**Reproductie:** Lees regels 113-140 en de SSoT-matrix op 427-439 uit de juiste manifest/base-blob e1188ca31c8ac9a23d2623db9c0d9fa6cab50384 en vergelijk de twee toegestane categorieën met de actuele root/project-AGENTS-regels. Er is geen uitzondering die kleine verwijderingen of automatische formattering alsnog beschermt.

**Aanbevolen oplossing:** Maak één canonieke, machine-afgedwongen approval policy; vereis expliciete toestemming voor iedere verwijdering en bestaande-bestandswrite, verwijder de numerieke uitzonderingen en laat documentatie automatisch toetsen tegen de hook/security-policy die de actuele regels afdwingt.

### B170-002 — P2 — Centraal geïndexeerde frontendprompt laat AI een niet-bestaande Next.js-stack en backend-authcontract bouwen

**Bewijs:** De prompt verplicht Next.js 14, TypeScript, Tailwind en Shadcn, schrijft mappen app/components/lib/hooks/types/styles en negen tabs voor, en stelt op regels 207-222 dat authenticatie door de backend wordt afgehandeld en alleen die frontendmappen mogen wijzigen. In de immutable tree ontbreken package.json, al deze mappen en Tailwindconfiguratie; de werkelijke UI is Streamlit en er is geen aangetoond backend-authcontract. docs/INDEX.md:177 linkt dit document als frontendgeneratieprompt.

**Reproductie:** Voer git cat-file -e b958ddb:<pad> uit voor package.json, app, components, lib, hooks, types, styles en tailwind.config.{js,ts}; elk pad ontbreekt. Vergelijk de prompt met src/main.py en de aanwezige src/ui Streamlitmodules; zoek tevens naar een geïmplementeerd authenticatiecontract.

**Aanbevolen oplossing:** Archiveer de prompt of herschrijf hem voor de actuele Streamlit/FastAPI-architectuur en alleen bestaande API-contracten. Laat een clean-tree contracttest alle genoemde paden/endpoints verifiëren en valideer a11y-eisen op de werkelijk gegenereerde UI in plaats van ze alleen te declareren.

### B170-003 — P2 — Ontologie-integratievoorbeelden importeren niet en gebruiken daarna incompatibele async- en requestcontracten

**Bewijs:** classifier_integration_ui.py en service_adapter_with_classifier.py importeren ClassificationResult uit services.classification, waar het symbool niet wordt geëxporteerd; beide stoppen direct met ImportError. Daarna behandelen regels 42-55 respectievelijk 107-123 de async classify-methode als synchroon, muteert de UI een Enum-value en bouwt GenerationRequest zonder verplicht id en met niet-bestaande velden wettelijke_context en voorbeelden. De gekoppelde quickstart gebruikt daarnaast container.ontology_classifier terwijl de container ontological_classifier aanbiedt.

**Reproductie:** Pipe elk immutable Pythonblob met PYTHONPATH=src naar de project-Python; beide processen eindigen met ImportError. Inspecteer vervolgens inspect.iscoroutinefunction(OntologicalClassifier.classify), vars(ServiceContainer) en inspect.signature(GenerationRequest): classify is async, alleen ontological_classifier bestaat en GenerationRequest vereist id zonder de twee genoemde velden.

**Aanbevolen oplossing:** Verwijder of herstel de voorbeelden tegen één huidig publiek contract: exporteer/importeer het juiste resulttype, await classify, maak een nieuwe immutable overridewaarde, bouw een valide GenerationRequest inclusief id en voeg import- plus offline end-to-endtests toe die ieder gedocumenteerd voorbeeld werkelijk uitvoeren.

### B170-004 — P2 — Actieve AI-configuratiegids beschrijft een OpenAI- en multi-environmentconfiguratie die niet bestaat

**Bewijs:** De gids documenteert GPT-4.1/OpenAI-variabelen, config_default/development/testing/staging/production YAML-bestanden en ENVIRONMENT-switching. De base ConfigManager kent alleen Environment.PRODUCTION, laadt config/config.yaml en de runtime rapporteert provider anthropic met lege globale default_model; componenten gebruiken Claude-modellen. Geen van de vijf gedocumenteerde configuratiebestanden bestaat. Dit overlapt qua actuele configuratief feiten met B139-001, maar is een afzonderlijke actieve how-to die gebruikers fout laat configureren.

**Reproductie:** Importeer ConfigManager zonder credentials en print environment, config_file, api.ai_provider/default_model en voorbeelden/synoniemen; de waarden zijn production, config/config.yaml, anthropic, leeg en claude-opus-4-8. Controleer de vijf paden met git cat-file -e en zie dat ze ontbreken.

**Aanbevolen oplossing:** Genereer de configuratiegids uit het actuele schema en werkende defaults, documenteer uitsluitend ondersteunde provider/environment-variabelen en voeg executable documentation tests toe die alle imports, paden en voorbeeldwaarden tegen een pinned commit valideren.

### B170-005 — P2 — Verplichte documentcreatieworkflow verwijst naar afgeschaft backlog- en architectuurbeleid

**Bewijs:** De active/canonical workflow noemt zichzelf verplicht en schrijft docs/backlog/stories/MASTER-EPICS-USER-STORIES.md, docs/CANONICAL_LOCATIONS.md en EA/SA/TA-documenten voor. De actuele CANONICAL_LOCATIONS in dezelfde scope verklaart backlog/stories en EA/SA/TA juist verouderd en wijst per-EPIC directories plus ARCHITECTURE.md aan. DOCUMENT-STANDARDS-GUIDE blijft tegelijk active/canonical voor de drie oude architectuurdocumenten en zes niet-bestaande validatie-/migratiescripts.

**Reproductie:** Vergelijk DOCUMENT-CREATION-WORKFLOW regels 17-85 met CANONICAL_LOCATIONS regels 14-37 en 56-88. git cat-file -e faalt voor MASTER-EPICS-USER-STORIES.md, docs/CANONICAL_LOCATIONS.md, EA.md/SA.md/TA.md en alle zes scripts op DOCUMENT-STANDARDS-GUIDE:505-528.

**Aanbevolen oplossing:** Kies één canonieke documentstructuur, markeer de twee oude workflows superseded en genereer pad-/tooltabellen uit de repository. Voeg een doc-contractgate toe die active/canonical documenten laat falen op ontbrekende of expliciet verouderde paden.

### B170-006 — P3 — Dormant synoniemvoorbeeld faalt op de enrichmentroute en negeert geldige nulwaarden

**Bewijs:** ensure_synonyms gebruikt config.gpt4_timeout_seconds, terwijl SynonymConfig alleen ai_timeout_seconds bevat; zodra enrichment nodig is ontstaat AttributeError buiten de TimeoutError-afhandeling. `min_weight = min_weight or default` vervangt bovendien een geldige expliciete drempel 0.0 door 0.7. Een per-call min_count=0 hoeft niet geldig te zijn omdat het configuratiemodel minimaal 1 eist. Het Phase-2.1-voorbeeld heeft geen gevonden productiecaller, dus de impact is dormant/documentair.

**Reproductie:** Importeer het immutable voorbeeld met een lege registry en een credentialvrije fake suggester en await ensure_synonyms('term'): het eindigt op AttributeError voor gpt4_timeout_seconds. Roep get_synonyms_for_lookup(..., min_weight=0.0) aan met een spy-registry en observeer dat de standaarddrempel wordt doorgegeven.

**Aanbevolen oplossing:** Gebruik ai_timeout_seconds, behandel None expliciet in plaats van truthiness en voeg een executable doctest toe voor fast path, slow path, timeout en nulgrenzen; archiveer het voorbeeld als deze API niet langer ondersteund is.

## Deduplicaties en afwijzingen

- Configdrift relateert aan B139-001; actieve how-to-, prompt-, policy- en executable-examplecontracten blijven afzonderlijk.

## Niet getest

- Geen live AI/netwerk/credentials, externe GitHub-protection, destructive Gitflows, productiedata of Streamlit/browser/a11y-runtime.
