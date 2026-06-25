"""Regressietest voor de default retry-strategy van IntegratedConfig (DEF-477).

Borgt dat de standaard `RetryConfig` de `RetryStrategy.ADAPTIVE`-enum gebruikt en
niet de string ``"adaptive"``. `RetryStrategy` is een *plain* `Enum`, dus
``"adaptive" == RetryStrategy.ADAPTIVE`` is ``False``; met de string viel
`AdaptiveRetryManager._calculate_delay` naar de else-tak (vaste `base_delay`)
i.p.v. de adaptieve backoff (`_get_adaptive_delay`) aan te roepen.
"""

import pytest

from utils.enhanced_retry import RetryStrategy
from utils.integrated_resilience import IntegratedConfig

pytestmark = [pytest.mark.unit]


def test_default_retry_config_uses_adaptive_enum_not_string():
    config = IntegratedConfig()

    assert config.retry_config is not None
    # Identiteit met het enum-lid — niet de toevallig gelijknamige string.
    assert config.retry_config.strategy is RetryStrategy.ADAPTIVE
    assert not isinstance(config.retry_config.strategy, str)


def test_adaptive_strategy_selects_adaptive_delay_branch():
    """De enum laat `_calculate_delay` de adaptieve tak kiezen, niet de else."""
    from utils.enhanced_retry import RetryStrategy as _RS

    config = IntegratedConfig()
    strategy = config.retry_config.strategy

    # Reproduceer de tak-selectie uit AdaptiveRetryManager._calculate_delay:
    # alleen bij de enum komt de uitvoering bij de ADAPTIVE-tak terecht.
    selected = (
        "adaptive"
        if strategy == _RS.ADAPTIVE
        else "fixed-fallback"  # de else-tak die de bug veroorzaakte
    )
    assert selected == "adaptive"
