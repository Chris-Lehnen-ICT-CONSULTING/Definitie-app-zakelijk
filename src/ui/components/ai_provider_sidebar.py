"""AI Provider sidebar component for provider selection and API key input."""

from __future__ import annotations

import logging
import os

import streamlit as st

from ui.session_state import SessionStateManager

logger = logging.getLogger(__name__)

# Provider configurations (DEF-314: default_model resolved dynamically from ModelRouter)
_PROVIDERS = {
    "openai": {
        "label": "OpenAI (GPT)",
        "env_key": "OPENAI_API_KEY",
        "key_prefix": "sk-",
        "key_hint": "sk-...",
    },
    "anthropic": {
        "label": "Anthropic (Claude)",
        "env_key": "ANTHROPIC_API_KEY",
        "key_prefix": "sk-ant-",
        "key_hint": "sk-ant-...",
    },
}


def _get_active_model() -> str:
    """DEF-314: Get the active critical-tier model from ModelRouter."""
    try:
        from utils.container_manager import get_cached_container

        router = get_cached_container().model_router()
        _, model = router.get_model("definition_core")
        return model
    except Exception:
        return "unknown"


def render_ai_provider_sidebar() -> None:
    """Render AI provider selection and API key input in the sidebar."""
    with st.sidebar:
        st.markdown("### AI Provider")

        # Current provider from env or SessionState
        current_provider = os.getenv("AI_PROVIDER", "anthropic").lower()

        # Provider selection
        provider_options = list(_PROVIDERS.keys())
        provider_labels = [_PROVIDERS[p]["label"] for p in provider_options]

        current_index = (
            provider_options.index(current_provider)
            if current_provider in provider_options
            else 0
        )

        selected_label = st.selectbox(
            "Provider",
            options=provider_labels,
            index=current_index,
            key="ai_provider_select",
        )

        # Map label back to provider key
        selected_provider = provider_options[provider_labels.index(selected_label)]
        provider_config = _PROVIDERS[selected_provider]

        # API Key input
        env_key_name = provider_config["env_key"]
        existing_key = os.getenv(env_key_name, "")
        has_env_key = bool(existing_key)

        if has_env_key:
            masked = f"{provider_config['key_prefix']}••••••••"
            st.caption(f"Key via env: `{masked}`")

        # Always show password input for override
        st.text_input(
            f"API Key ({provider_config['key_hint']})",
            type="password",
            key="ai_api_key_input",
            help=(
                f"Voer je {provider_config['label']} API key in. "
                "Wordt alleen in geheugen opgeslagen, niet op disk."
            ),
        )

        # Read back the key from SessionState (key-only pattern)
        entered_key = SessionStateManager.get_value("ai_api_key_input", "")

        # Detect changes and apply
        provider_changed = selected_provider != current_provider
        key_changed = bool(entered_key) and entered_key != existing_key

        if provider_changed or key_changed:
            _apply_provider_change(selected_provider, entered_key or existing_key)

        # Status display
        active_provider = os.getenv("AI_PROVIDER", "anthropic").lower()
        active_config = _PROVIDERS.get(active_provider, _PROVIDERS["anthropic"])
        active_key = os.getenv(active_config["env_key"], "")

        if active_key:
            st.success(f"Active: {active_config['label']}")
            st.caption(f"Model: `{_get_active_model()}`")
        else:
            st.warning(f"Geen API key voor {active_config['label']}")


def _refresh_ai_services() -> None:
    """Herlaad de config en verwijder elke cache die de oude AI-client vasthoudt.

    DEF-730 — kritiek pad. Deze drie stappen bepalen samen welke AI-client de sessie
    krijgt, dus fouten worden hier niet opgevangen maar doorgegeven aan de aanroeper:

    1. `reload_config()` — de ConfigManager is een proces-singleton die provider en
       AI-sleutel eenmalig uit config.yaml + env leest.
    2. `reset_container()` — reset de container en zijn singleton-cache.
    3. `clear_service_cache()` — de container in de Streamlit-sessie overleeft
       `reset_container()` en zou anders de oude client blijven serveren.
    4. `reset_service_adapter_cache()` — de ServiceAdapter die het generatiepad
       gebruikt bevriest container én orchestrator, en daarmee de oude AI-client.
    """
    from config.config_manager import reload_config
    from services.container import reset_container
    from services.service_factory import reset_service_adapter_cache
    from ui.cached_services import clear_service_cache

    reload_config()
    reset_container()
    clear_service_cache()
    reset_service_adapter_cache()


def _restore_env(vorige_env: dict[str, str | None]) -> None:
    """Zet de omgevingsvariabelen terug naar hun waarde van vóór de wissel."""
    for naam, waarde in vorige_env.items():
        if waarde is None:
            os.environ.pop(naam, None)
        else:
            os.environ[naam] = waarde


def _apply_provider_change(provider: str, api_key: str) -> None:
    """Apply provider/key change: set env vars, refresh AI services, rerun."""
    provider_config = _PROVIDERS[provider]
    env_key_name = provider_config["env_key"]

    # DEF-730: bewaar de nog geldende omgeving. Faalt de refresh, dan wordt de
    # wijziging volledig teruggedraaid. Zou de nieuwe sleutel in de env blijven
    # staan terwijl de config-singleton de oude houdt, dan ziet de detectie in
    # render_ai_provider_sidebar geen openstaande wissel meer en draait de app bij
    # de volgende rerun stilzwijgend door op de oude sleutel.
    vorige_env: dict[str, str | None] = {
        "AI_PROVIDER": os.environ.get("AI_PROVIDER"),
        env_key_name: os.environ.get(env_key_name),
    }

    # Set provider env var
    os.environ["AI_PROVIDER"] = provider

    # Set API key env var for the selected provider
    if api_key:
        os.environ[env_key_name] = api_key

    logger.info("AI provider changed to: %s", provider)

    try:
        _refresh_ai_services()
    except Exception:
        # DEF-730: bewust een vaste melding, zonder exception-tekst en zonder
        # exc_info. De opgevangen fout komt uit config- of SDK-lagen die de
        # API-sleutel in hun boodschap kunnen meedragen.
        logger.error("AI provider change failed: kon AI-services niet verversen")
        _restore_env(vorige_env)
        st.error(
            "De AI-configuratie kon niet ververst worden. De wijziging is "
            "teruggedraaid en niet actief — probeer het opnieuw."
        )
        # Breekt de scriptrun af: de rest van de pagina mag niet met de oude
        # client verder. De teruggedraaide env houdt de wissel openstaand, dus de
        # volgende rerun probeert het opnieuw in plaats van stil door te gaan.
        st.stop()
        return

    # DEF-314: Reset examples generator so it picks up new provider
    try:
        from voorbeelden.unified_voorbeelden import reset_examples_generator

        reset_examples_generator()
    except Exception:
        logger.debug("Could not reset examples generator", exc_info=True)

    # DEF-730: de TabbedInterface-cache wordt hier niet meer geleegd. Die hing aan
    # `import main`, terwijl Streamlit het entrypoint als `__main__` draait: dat
    # levert een tweede module-object, dus geleegd werd hooguit de verkeerde cache.
    # De interface hangt nu aan de identiteit van de container (zie
    # main.get_tabbed_interface) en ververst dus vanzelf zodra de container dat doet.

    # Rerun to apply changes
    st.rerun()
