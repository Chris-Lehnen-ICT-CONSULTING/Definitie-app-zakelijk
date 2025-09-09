Title: Pending async-taken bij afsluiten (SmartRateLimiter/ResilienceFramework)

Status: Open
Severity: Medium (netjes sluiten, resource-lekken voorkomen)
Componenten: utils.resilience, utils.smart_rate_limiter, AsyncGPTClient

Beschrijving
- Bij het stoppen van de app verschijnen asyncio-fouten:
  - "Task was destroyed but it is pending!" voor taken van `ResilienceFramework` en `SmartRateLimiter`.
- Duidt op niet-netjes geannuleerde/afgewachte achtergrondtaken.

Reproductie
1) Start app, voer een generatie uit.
2) Stop app (Ctrl+C of Streamlit shutdown).
3) Observeer asyncio errors in logs.

Analyse/Root cause hypothese
- Achtergrondtaken worden gestart maar er is geen centrale shutdown‐procedure (cancel + await).
- Mogelijk ontbreekt een `ServiceContainer.shutdown()` of Streamlit on_session_end hook die deze taken afsluit.

Acceptatiecriteria
- Bij afsluiten geen "Task was destroyed" meldingen.
- Rate limiter, resilience framework en eventuele async clients (OpenAI) worden netjes afgesloten.

Aanpakvoorstel
- Voeg een `shutdown()` toe aan ServiceContainer die achtergrondtaken stopt en clients sluit.
- Integreer shutdown in Streamlit lifecycle (bijv. via `st.on_session_end` of try/finally in entrypoints).
- Zorg dat `AsyncGPTClient` en andere async clients een `aclose()`/`close()` aanbieden en worden aangeroepen.

Referenties
- `src/utils/resilience.py`, `src/utils/smart_rate_limiter.py`
- `src/services/container.py`
- `src/utils/async_api.py`
