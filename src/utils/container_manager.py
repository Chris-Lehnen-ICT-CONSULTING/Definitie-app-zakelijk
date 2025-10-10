"""
Container Manager met pure‑Python caching voor ServiceContainer.

Dit module voorkomt dat ServiceContainer onnodig vaak wordt geïnitialiseerd
door een proces‑lokale LRU‑cache (singleton) te gebruiken. Dit reduceert
opstarttijd en houdt het systeem UI‑agnostisch (geen Streamlit‑afhankelijkheid).

US‑201: Optimaliseer ServiceContainer caching
US-202: Remove custom config support - singleton only
"""

import logging
import os
from functools import lru_cache
from typing import Any

from services.container import ContainerConfigs, ServiceContainer

logger = logging.getLogger(__name__)


# Custom container functions removed (US-202):
# Multiple cache mechanisms caused duplicate container initialization.
# Use get_cached_container() singleton for all cases.


@lru_cache(maxsize=1)
def get_cached_container() -> ServiceContainer:
    """
    Get of create een gecachede ServiceContainer instance (singleton).

    Deze functie gebruikt Python's lru_cache om ervoor te zorgen dat de
    ServiceContainer maar 1x wordt geïnitialiseerd. De container blijft
    in geheugen als singleton instance.

    BELANGRIJK: Deze functie accepteert GEEN parameters. Dit is cruciaal voor
    correct cache gedrag omdat lru_cache func() en func(None) als verschillende
    cache keys behandelt, wat leidt tot dubbele initialisatie.

    Fix: US-202 - Remove cache key parameter to ensure true singleton behavior.
    Voorheen: func() en func(None) maakten 2 verschillende containers.
    Nu: func() maakt altijd dezelfde singleton container.

    Returns:
        Singleton ServiceContainer instance
    """
    logger.info("🚀 Creating singleton ServiceContainer (cache miss - first request)")

    # Bepaal environment configuratie
    env = os.getenv("APP_ENV", "production")

    if env == "development":
        config = ContainerConfigs.development()
    elif env == "testing":
        config = ContainerConfigs.testing()
    else:
        config = ContainerConfigs.production()

    # Log configuratie details
    logger.info(f"Environment: {env}")
    logger.info(f"Database path: {config.get('db_path', 'default')}")
    logger.info(f"Monitoring enabled: {config.get('enable_monitoring', False)}")

    # Maak en retourneer de container
    container = ServiceContainer(config)

    # Verificatie log dat services maar 1x worden aangemaakt
    # Log container ID voor debugging van duplicate containers
    container_id = container.get_container_id()
    logger.info(
        f"✅ ServiceContainer succesvol geïnitialiseerd en gecached (ID: {container_id})"
    )

    return container


# get_container_with_config() removed (US-202):
# This function caused duplicate container initialization by creating
# separate cache entries. All code now uses get_cached_container() singleton.


def clear_container_cache():
    """
    Clear de ServiceContainer cache voor development/testing.

    Deze functie forceert het opnieuw initialiseren van de container
    bij de volgende aanroep. Nuttig tijdens development of bij config wijzigingen.
    """
    logger.info("🗑️ Clear ServiceContainer cache")

    # Clear de singleton cache
    try:
        get_cached_container.cache_clear()
    except Exception:
        pass

    logger.info("✅ Container cache gecleared")


def get_container_stats() -> dict[str, Any]:
    """
    Get statistieken over de huidige ServiceContainer.

    Returns:
        Dictionary met container statistieken
    """
    try:
        container = get_cached_container()

        # Tel geïnitialiseerde services
        service_count = len(container._instances)

        # Verzamel service namen
        service_names = list(container._instances.keys())

        return {
            "initialized": True,
            "service_count": service_count,
            "services": service_names,
            "config": {
                "db_path": container.db_path,
                "has_api_key": bool(container.openai_api_key),
            },
        }
    except Exception as e:
        return {"initialized": False, "error": str(e)}


# Lazy loading helpers voor specifieke services
@lru_cache(maxsize=1)
def get_cached_orchestrator():
    """
    Get de orchestrator service met lazy loading.

    Returns:
        DefinitionOrchestratorV2 instance
    """
    container = get_cached_container()
    return container.orchestrator()


@lru_cache(maxsize=1)
def get_cached_repository():
    """
    Get de repository service met lazy loading.

    Returns:
        DefinitionRepository instance
    """
    container = get_cached_container()
    return container.repository()


@lru_cache(maxsize=1)
def get_cached_web_lookup():
    """
    Get de web lookup service met lazy loading.

    Returns:
        ModernWebLookupService instance
    """
    container = get_cached_container()
    return container.web_lookup()


# Development helper voor debugging
def debug_container_state():
    """
    Print debug informatie over de container state.

    Gebruik deze functie tijdens development om te verifiëren
    dat de container correct wordt gecached.
    """
    stats = get_container_stats()

    print("=" * 60)
    print("ServiceContainer Debug Info")
    print("=" * 60)

    if stats["initialized"]:
        print("✅ Container geïnitialiseerd")
        print(f"📦 Aantal services: {stats['service_count']}")
        print(f"🔧 Services: {', '.join(stats['services'])}")
        print(f"💾 Database: {stats['config']['db_path']}")
        print(f"🔑 API Key: {'✓' if stats['config']['has_api_key'] else '✗'}")
    else:
        print(f"❌ Container niet geïnitialiseerd: {stats.get('error', 'Unknown')}")

    print("=" * 60)


# Backward compatibility exports
__all__ = [
    "get_cached_container",
    "clear_container_cache",
    "get_container_stats",
    "get_cached_orchestrator",
    "get_cached_repository",
    "get_cached_web_lookup",
    "debug_container_state",
]
