"""Regressietest voor de default retry-strategy van IntegratedConfig (DEF-477).

Borgt dat de standaard `RetryConfig` de `RetryStrategy.ADAPTIVE`-enum gebruikt en
niet de string ``"adaptive"``. `RetryStrategy` is een *plain* `Enum`, dus
``"adaptive" == RetryStrategy.ADAPTIVE`` is ``False``; met de string viel
`AdaptiveRetryManager._calculate_delay` naar de else-tak (vaste `base_delay`)
i.p.v. de adaptieve backoff (`_get_adaptive_delay`) aan te roepen.
"""

import pytest

from utils.enhanced_retry import (
    AdaptiveRetryManager,
    RetryConfig,
    RetryStrategy,
)
from utils.integrated_resilience import IntegratedConfig

pytestmark = [pytest.mark.unit]


def test_default_retry_config_uses_adaptive_enum_not_string():
    config = IntegratedConfig()

    assert config.retry_config is not None
    # Identiteit met het enum-lid — niet de toevallig gelijknamige string.
    assert config.retry_config.strategy is RetryStrategy.ADAPTIVE
    assert not isinstance(config.retry_config.strategy, str)


@pytest.mark.asyncio
async def test_adaptive_strategy_grows_delay_with_attempt():
    """Gedragstest: met ADAPTIVE roept `get_retry_delay` de adaptieve tak aan,
    waardoor de delay oploopt met het attempt-nummer (i.p.v. de else-tak met een
    constante base_delay). Dit is exact het gedrag dat de string-bug brak.
    """
    config = RetryConfig(
        base_delay=1.0,
        max_delay=60.0,
        jitter=False,  # determinisme
        strategy=RetryStrategy.ADAPTIVE,
    )
    manager = AdaptiveRetryManager(config)

    # Generieke fout → geen rate-limit/connection-multiplier.
    delay_first = await manager.get_retry_delay(ValueError("x"), attempt=0)
    delay_later = await manager.get_retry_delay(ValueError("x"), attempt=3)

    assert delay_later > delay_first  # adaptieve backoff loopt op


@pytest.mark.asyncio
async def test_fixed_strategy_keeps_delay_constant():
    """Contrast: met FIXED_DELAY blijft de delay constant over attempts — bewijst
    dat `get_retry_delay` daadwerkelijk op de strategie-enum routeert (en de
    ADAPTIVE-test hierboven dus de echte tak raakt, niet toevallig groeit)."""
    config = RetryConfig(
        base_delay=1.0,
        max_delay=60.0,
        jitter=False,
        strategy=RetryStrategy.FIXED_DELAY,
    )
    manager = AdaptiveRetryManager(config)

    delay_first = await manager.get_retry_delay(ValueError("x"), attempt=0)
    delay_later = await manager.get_retry_delay(ValueError("x"), attempt=3)

    assert delay_first == delay_later == config.base_delay
