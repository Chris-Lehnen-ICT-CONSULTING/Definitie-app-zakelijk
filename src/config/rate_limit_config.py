"""
Rate limiting configuratie voor verschillende endpoints.

Dit bestand bevat endpoint-specifieke configuraties voor optimale performance
en het voorkomen van API rate limit errors.
"""

from dataclasses import dataclass

from utils.smart_rate_limiter import RateLimitConfig, RequestPriority


@dataclass
class EndpointConfig:
    """Configuratie voor een specifieke endpoint."""

    tokens_per_second: float
    bucket_capacity: int
    burst_capacity: int
    target_response_time: float
    timeout: float
    priority_weights: dict[RequestPriority, float] | None = None


# Endpoint-specifieke configuraties
ENDPOINT_CONFIGS: dict[str, EndpointConfig] = {
    # Voorbeelden generatie endpoints - hogere rate limits voor parallel processing
    "examples_generation_sentence": EndpointConfig(
        tokens_per_second=5.0,  # Verhoogd van 3.0 naar 5.0 voor snellere parallel processing
        bucket_capacity=20,  # Verhoogd van 15 naar 20 voor grotere bursts
        burst_capacity=12,  # Verhoogd van 10 naar 12
        target_response_time=2.0,
        timeout=20.0,  # Sync met decorator timeout
    ),
    "examples_generation_practical": EndpointConfig(
        tokens_per_second=5.0,  # Verhoogd van 3.0 naar 5.0
        bucket_capacity=20,  # Verhoogd van 15 naar 20
        burst_capacity=12,  # Verhoogd van 10 naar 12
        target_response_time=2.0,
        timeout=45.0,  # DEF-108: sync met decorator (was 20.0)
    ),
    "examples_generation_counter": EndpointConfig(
        tokens_per_second=5.0,  # Verhoogd van 3.0 naar 5.0
        bucket_capacity=20,  # Verhoogd van 15 naar 20
        burst_capacity=12,  # Verhoogd van 10 naar 12
        target_response_time=2.0,
        timeout=30.0,  # DEF-108: sync met decorator (was 20.0)
    ),
    "examples_generation_synonyms": EndpointConfig(
        tokens_per_second=5.0,  # Verhoogd van 3.0 naar 5.0
        bucket_capacity=20,  # Verhoogd van 15 naar 20
        burst_capacity=12,  # Verhoogd van 10 naar 12
        target_response_time=2.0,
        timeout=30.0,  # Sync met decorator timeout (5 items)
    ),
    "examples_generation_antonyms": EndpointConfig(
        tokens_per_second=5.0,  # Verhoogd van 3.0 naar 5.0
        bucket_capacity=20,  # Verhoogd van 15 naar 20
        burst_capacity=12,  # Verhoogd van 10 naar 12
        target_response_time=2.0,
        timeout=30.0,  # Sync met decorator timeout (5 items)
    ),
    "examples_generation_explanation": EndpointConfig(
        tokens_per_second=3.0,  # Verhoogd van 1.5 naar 3.0
        bucket_capacity=12,  # Verhoogd van 8 naar 12
        burst_capacity=6,  # Verhoogd van 4 naar 6
        target_response_time=3.0,
        timeout=30.0,  # Sync met decorator timeout
    ),
    # Definitie generatie endpoints - normale rate limits
    "definition_generation": EndpointConfig(
        tokens_per_second=2.0,
        bucket_capacity=10,
        burst_capacity=5,
        target_response_time=2.5,
        timeout=120.0,  # Verhoogd van 20s naar 120s voor complete V2 flow met voorbeelden
    ),
    "definition_validation": EndpointConfig(
        tokens_per_second=2.5,
        bucket_capacity=12,
        burst_capacity=6,
        target_response_time=2.0,
        timeout=15.0,
    ),
    # Web lookup endpoints - lagere rate limits
    "web_search": EndpointConfig(
        tokens_per_second=1.0,
        bucket_capacity=5,
        burst_capacity=3,
        target_response_time=5.0,
        timeout=30.0,
    ),
    "web_scrape": EndpointConfig(
        tokens_per_second=0.5,
        bucket_capacity=3,
        burst_capacity=2,
        target_response_time=10.0,
        timeout=60.0,
    ),
    # Default configuratie voor niet-gespecificeerde endpoints
    "default": EndpointConfig(
        tokens_per_second=2.0,
        bucket_capacity=10,
        burst_capacity=5,
        target_response_time=2.0,
        timeout=15.0,
    ),
}


def get_rate_limit_config(endpoint_name: str) -> RateLimitConfig:
    """
    Haal de rate limit configuratie op voor een specifieke endpoint.

    Args:
        endpoint_name: Naam van de endpoint

    Returns:
        RateLimitConfig voor de endpoint
    """
    # Gebruik endpoint-specifieke config of default
    endpoint_config = ENDPOINT_CONFIGS.get(endpoint_name, ENDPOINT_CONFIGS["default"])

    # Converteer naar RateLimitConfig
    config = RateLimitConfig(
        tokens_per_second=endpoint_config.tokens_per_second,
        bucket_capacity=endpoint_config.bucket_capacity,
        burst_capacity=endpoint_config.burst_capacity,
        target_response_time=endpoint_config.target_response_time,
    )

    # Voeg priority weights toe als gespecificeerd
    if endpoint_config.priority_weights:
        config.priority_weights = endpoint_config.priority_weights

    return config


def get_endpoint_timeout(endpoint_name: str) -> float:
    """
    Haal de aanbevolen timeout op voor een endpoint.

    Args:
        endpoint_name: Naam van de endpoint

    Returns:
        Timeout in seconden
    """
    endpoint_config = ENDPOINT_CONFIGS.get(endpoint_name, ENDPOINT_CONFIGS["default"])
    return endpoint_config.timeout


# Utility functies voor monitoring
def get_all_endpoints() -> list[str]:
    """Haal lijst van alle geconfigureerde endpoints op."""
    return [name for name in ENDPOINT_CONFIGS if name != "default"]


def validate_endpoint_config(endpoint_name: str) -> bool:
    """Valideer of een endpoint correct geconfigureerd is."""
    if endpoint_name not in ENDPOINT_CONFIGS:
        return False

    config = ENDPOINT_CONFIGS[endpoint_name]
    return (
        config.tokens_per_second > 0
        and config.bucket_capacity > 0
        and config.burst_capacity > 0
        and config.target_response_time > 0
        and config.timeout > 0
    )
