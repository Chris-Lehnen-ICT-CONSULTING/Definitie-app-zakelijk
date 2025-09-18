"""
Cached Service Initialization voor US-201/US-202.

Deze module gebruikt de nieuwe container_manager om caching te centraliseren.
Dit voorkomt dat services 6x per sessie worden geïnitialiseerd.

Update: Gebruikt nu utils.container_manager voor gecentraliseerde caching.
"""

import logging
from typing import Any

import streamlit as st

from utils.container_manager import (
    get_cached_container,
    get_container_with_config,
    clear_container_cache as clear_manager_cache,
    get_container_stats as get_manager_stats,
)

logger = logging.getLogger(__name__)


def get_cached_service_container(config: dict[str, Any] | None = None):
    """
    Get of maak een gecachte ServiceContainer instance.

    Deze functie is een wrapper rond container_manager voor backward compatibility.

    Args:
        config: Optionele configuratie voor de container

    Returns:
        Singleton ServiceContainer instance
    """
    if config is None:
        return get_cached_container()
    else:
        return get_container_with_config(config)


def initialize_services_once():
    """
    Initialize services in Streamlit session state als nog niet aanwezig.

    Deze functie zorgt ervoor dat de service container slechts één keer
    wordt aangemaakt en in session state wordt opgeslagen.
    """
    if "service_container" not in st.session_state:
        logger.info("📦 Initializing service container in session state")

        # Gebruik de gecachte container
        st.session_state.service_container = get_cached_service_container()

        # Track initialization stats
        if "service_init_count" not in st.session_state:
            st.session_state.service_init_count = 0
        st.session_state.service_init_count += 1

        logger.info(
            f"✅ Services initialized (count: {st.session_state.service_init_count})"
        )
    else:
        # Container bestaat al, log alleen als debug
        logger.debug("Service container already exists in session state")


def get_service(service_name: str):
    """
    Helper functie om een service op te halen uit de gecachte container.

    Args:
        service_name: Naam van de service (bijv. 'orchestrator', 'repository')

    Returns:
        Service instance of None
    """
    # Zorg dat services zijn geïnitialiseerd
    initialize_services_once()

    # Haal service op uit container
    container = st.session_state.service_container
    return container.get_service(service_name)


def clear_service_cache():
    """
    Clear de service cache (gebruik spaarzaam!).

    Dit forceert het opnieuw aanmaken van alle services bij de volgende aanroep.
    """
    logger.warning("⚠️ Clearing service cache - all services will be recreated")

    # Gebruik container_manager's clear functie
    clear_manager_cache()

    # Verwijder uit session state
    if "service_container" in st.session_state:
        del st.session_state.service_container

    # Reset init count
    if "service_init_count" in st.session_state:
        st.session_state.service_init_count = 0

    logger.info("✅ Service cache cleared")


def get_service_stats() -> dict[str, Any]:
    """
    Get statistieken over service initialization en cache performance.

    Returns:
        Dictionary met stats
    """
    stats = {
        "container_exists": "service_container" in st.session_state,
        "init_count": st.session_state.get("service_init_count", 0),
    }

    if "service_container" in st.session_state:
        container = st.session_state.service_container
        stats["container_init_count"] = container.get_initialization_count()
        stats["services_loaded"] = len(container._instances)

        # Get ToetsregelManager stats als beschikbaar
        try:
            orchestrator = container.get_service("orchestrator")
            if orchestrator and hasattr(orchestrator, "validation_service"):
                val_service = orchestrator.validation_service
                if hasattr(val_service, "validation_service"):
                    mod_val_service = val_service.validation_service
                    if hasattr(mod_val_service, "toetsregel_manager"):
                        manager = mod_val_service.toetsregel_manager
                        if hasattr(manager, "get_stats"):
                            stats["rule_cache_stats"] = manager.get_stats()
        except Exception as e:
            logger.debug(f"Could not get rule cache stats: {e}")

    return stats