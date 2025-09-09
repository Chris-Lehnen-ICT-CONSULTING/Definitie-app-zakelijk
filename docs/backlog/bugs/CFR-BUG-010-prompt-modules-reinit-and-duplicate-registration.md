Title: Prompt-modules worden herhaaldelijk geïnitialiseerd en meervoudig geregistreerd

Status: Open
Severity: Medium-High (prestaties/noise, mogelijk geheugen/duplicaatlogica)
Componenten: services.prompts.*, PromptOrchestrator, UnifiedPromptBuilder

Beschrijving
- Tijdens een enkele UI-run worden prompt-modules meerdere keren geïnitialiseerd én opnieuw geregistreerd in de `PromptOrchestrator`.
- Logfragment laat herhaalde lijnen zien zoals:
  - "Module '<naam>' succesvol geïnitialiseerd" (meerdere keren voor dezelfde module)
  - "Module '<naam>' geregistreerd" (opnieuw)

Reproductie
1) Start de app (nieuwe services actief).
2) Genereer een definitie of open de generator-tab.
3) Bekijk logs: herhaalde init/registratie voor dezelfde modules.

Analyse/Root cause hypothese
- Zowel `ui.tabbed_interface.TabbedInterface` als `ui.components.definition_generator_tab.DefinitionGeneratorTab` maken een `UnifiedPromptBuilder`/`RegenerationService` aan, wat onderliggend de `PromptOrchestrator` en modules triggert.
- Er is geen guard/singleton/idempotency bij module-registratie; iedere builder-aanmaak registreert modules opnieuw.

Impact
- Onnodige CPU/IO, lawaaiige logs, potentieel meerdere identieke module-instanties in geheugen.

Acceptatiecriteria
- Bij een standaard UI-flow worden modules hooguit eenmaal geïnitialiseerd en geregistreerd.
- `UnifiedPromptBuilder`/`PromptOrchestrator` gebruikt een singleton of idempotente registratie.
- Logvolume neemt merkbaar af; geen dubbele "geregistreerd" logs voor dezelfde module binnen één sessie.

Aanpakvoorstel
- Centraliseer builder/orchestrator creatie via `ServiceContainer` met caching (singleton per sessie).
- Voeg idempotente checks toe in `PromptOrchestrator.register_module()` (skip bij herhaalde registratie van dezelfde sleutel).
- Verplaats `RegenerationService` init naar één plek (bijv. alleen in `TabbedInterface`) en injecteer waar nodig.

Referenties
- `src/ui/tabbed_interface.py` (RegenerationService init)
- `src/ui/components/definition_generator_tab.py` (RegenerationService init)
- `src/services/prompts/*`, `src/services/prompts/modules/*`

