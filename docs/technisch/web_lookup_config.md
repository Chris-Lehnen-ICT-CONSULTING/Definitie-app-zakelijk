# Web Lookup Configuratie (Episch Verhaal 3)

Deze applicatie gebruikt één centrale configuratie voor de moderne web lookup en prompt‑augmentatie.

- Standaard bestand: `config/web_lookup_defaults.yaml`
- Optionele override: zet `WEB_LOOKUP_CONFIG=/pad/naar/een/ander.yaml` als je tijdelijk een andere config wilt gebruiken.

## Kernsecties

- `web_lookup.enabled`: schakel moderne web lookup in/uit (standaard: true)
- `web_lookup.providers` per provider:
  - `enabled`: bron aan/uit
  - `weight`: relatieve weging voor ranking
  - `timeout`: timeouts in seconden
  - `cache_ttl`: cache TTL in seconden (voor toekomstige caching)
  - `min_score`: minimum score OM mee te nemen
- `web_lookup.cache` (voor toekomstige caching): strategy, ttl, max_entries
- `web_lookup.sanitization`: beleid voor het veilig opschonen van snippets
- `web_lookup.context_mappings`: optionele, domeinspecifieke hints
- `web_lookup.prompt_augmentation`:
  - `enabled`: voeg top‑K context toe aan de prompt
  - `max_snippets`: maximum aantal snippets
  - `max_tokens_per_snippet`: token‑budget per snippet (approx)
  - `total_token_budget`: totaal token‑budget (approx)
  - `prioritize_juridical`: autoritatieve bronnen eerst
  - `section_header`: koptekst van de contextsectie
  - `snippet_separator`: scheidingsteken per snippet
  - `position`: `prepend`, `after_context` of `before_examples`

## Gedrag

- Zonder env‑variabelen gebruikt de app altijd `config/web_lookup_defaults.yaml`.
- Als `WEB_LOOKUP_CONFIG` is gezet, wordt dat pad gebruikt (hoogste prioriteit).
- Prompt‑augmentatie staat standaard aan in de defaults.

## Waar dit gebruikt wordt

- `ModernWebLookupService`: leest provider‑instellingen en wegingen
- `DefinitionOrchestratorV2`: verrijkt context en schrijft `definition.metadata["sources"]`
- `PromptServiceV2`: injecteert optioneel een contextsectie in de prompt
- UI (`definition_generator_tab`): toont “📚 Gebruikte Bronnen” uit `metadata.sources`

## Snelle validatie

- Unit/integratie: `pytest -q tests/web_lookup`
- App (dev): `streamlit run src/main.py` en een definitie genereren; controleer bronnen en promptsectie.
