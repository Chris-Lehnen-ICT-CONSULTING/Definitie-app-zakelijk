"""
Container Manager met pure‑Python caching voor ServiceContainer.

Dit module voorkomt dat ServiceContainer onnodig vaak wordt geïnitialiseerd
door een proces‑lokale LRU‑cache (singleton) te gebruiken. Dit reduceert
opstarttijd en houdt het systeem UI‑agnostisch (geen Streamlit‑afhankelijkheid).

US‑201: Optimaliseer ServiceContainer caching
"""

import hashlib
import json
import logging
import os
from functools import lru_cache
from typing import Any

from services.container import ContainerConfigs, ServiceContainer

logger = logging.getLogger(__name__)


# Kleine LRU-cache voor custom containers op basis van config-hash
@lru_cache(maxsize=8)
def _create_custom_container(_hash: str, _config_json: str) -> ServiceContainer:
    import json as _json

    logger.info(f"🔧 Maak custom ServiceContainer (hash: {_hash[:8]}...)")
    return ServiceContainer(_json.loads(_config_json))


def _get_config_hash(config: dict[str, Any]) -> str:
    """
    Genereer een hash van de configuratie voor cache invalidatie.

    Args:
        config: Service container configuratie

    Returns:
        SHA256 hash van de configuratie
    """
    # Sorteer keys voor consistente hashing
    config_str = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


@lru_cache(maxsize=1)
def get_cached_container(_config_hash: str | None = None) -> ServiceContainer:
    """
    Get of create een gecachede ServiceContainer instance.

    Deze functie gebruikt Streamlit's cache_resource decorator om ervoor te zorgen
    dat de ServiceContainer maar 1x wordt geïnitialiseerd per sessie. De container
    blijft in geheugen tussen reruns.

    Args:
        _config_hash: Hash van de configuratie (voor cache busting)

    Returns:
        Singleton ServiceContainer instance
    """
    logger.info("🚀 Initialiseer ServiceContainer (gebeurt 1x per sessie)")

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
    logger.info("✅ ServiceContainer succesvol geïnitialiseerd en gecached")

    return container


def get_container_with_config(config: dict[str, Any] | None = None) -> ServiceContainer:
    """
    Get een ServiceContainer met optionele custom configuratie.

    Als geen configuratie wordt meegegeven, wordt de standaard environment
    configuratie gebruikt. Custom configuraties zorgen voor een nieuwe cache entry.

    Args:
        config: Optionele custom configuratie

    Returns:
        ServiceContainer instance
    """
    if config is None:
        # Gebruik standaard environment-based configuratie
        return get_cached_container()

    # Voor custom config, genereer hash voor cache key
    config_hash = _get_config_hash(config)

    # Maak nieuwe container met custom config (aparte cache entry)
    # Gebruik een kleine LRU-cache op basis van hash en een JSON snapshot
    import json as _json

    return _create_custom_container(
        config_hash, _json.dumps(config, sort_keys=True, default=str)
    )


def clear_container_cache():
    """
    Clear de ServiceContainer cache voor development/testing.

    Deze functie forceert het opnieuw initialiseren van de container
    bij de volgende aanroep. Nuttig tijdens development of bij config wijzigingen.
    """
    logger.info("🗑️ Clear ServiceContainer cache")

    # Clear de caches voor containers
    try:
        get_cached_container.cache_clear()
    except Exception:
        pass
    try:
        _create_custom_container.cache_clear()
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
    "get_container_with_config",
    "clear_container_cache",
    "get_container_stats",
    "get_cached_orchestrator",
    "get_cached_repository",
    "get_cached_web_lookup",
    "debug_container_state",
]
