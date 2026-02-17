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
        current_provider = os.getenv("AI_PROVIDER", "openai").lower()

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
        active_provider = os.getenv("AI_PROVIDER", "openai").lower()
        active_config = _PROVIDERS.get(active_provider, _PROVIDERS["openai"])
        active_key = os.getenv(active_config["env_key"], "")

        if active_key:
            st.success(f"Active: {active_config['label']}")
            st.caption(f"Model: `{_get_active_model()}`")
        else:
            st.warning(f"Geen API key voor {active_config['label']}")


def _apply_provider_change(provider: str, api_key: str) -> None:
    """Apply provider/key change: set env vars, reset container, rerun."""
    provider_config = _PROVIDERS[provider]

    # Set provider env var
    os.environ["AI_PROVIDER"] = provider

    # Set API key env var for the selected provider
    if api_key:
        os.environ[provider_config["env_key"]] = api_key

    logger.info("AI provider changed to: %s", provider)

    # Reset the service container so it picks up new config
    try:
        from services.container import reset_container

        reset_container()
    except Exception:
        logger.warning("Container reset failed during provider change", exc_info=True)

    # DEF-314: Reset examples generator so it picks up new provider
    try:
        from voorbeelden.unified_voorbeelden import reset_examples_generator

        reset_examples_generator()
    except Exception:
        logger.debug("Could not reset examples generator", exc_info=True)

    # Clear the cached TabbedInterface so it gets a fresh container
    try:
        from main import get_tabbed_interface

        get_tabbed_interface.clear()
    except Exception:
        logger.debug("Could not clear interface cache", exc_info=True)

    # Rerun to apply changes
    st.rerun()
