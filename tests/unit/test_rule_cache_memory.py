"""DEF-496: RuleCache serveert de bulk-regels uit een in-memory memo.

Bewijst dat get_all_rules() de (disk-lezende) @cached-loader niet bij elke
call opnieuw aanroept, en dat clear_cache() de memo invalideert.
"""

from unittest.mock import patch

import pytest

from toetsregels import rule_cache as rc
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]


@pytest.fixture
def fresh_cache():
    """Singleton-cache met lege memo (voorkomt cross-test-pollutie)."""
    cache = get_rule_cache()
    cache._rules_memo = None
    cache._rules_memo_ts = 0.0
    return cache


def test_get_all_rules_loads_from_disk_only_once(fresh_cache):
    """Meerdere get_all_rules-calls raken de disk-loader slechts één keer."""
    real_loader = rc._load_all_rules_cached

    with patch.object(rc, "_load_all_rules_cached", wraps=real_loader) as spy:
        first = fresh_cache.get_all_rules()
        second = fresh_cache.get_all_rules()
        third = fresh_cache.get_all_rules()

    assert spy.call_count == 1, "loader mag maar één keer worden aangeroepen"
    assert isinstance(first, dict) and first, "regels moeten geladen zijn"
    # Zelfde object uit de memo (geen her-deserialisatie van disk).
    assert first is second is third


def test_clear_cache_invalidates_memo(fresh_cache):
    """Na clear_cache() wordt de loader opnieuw aangeroepen."""
    real_loader = rc._load_all_rules_cached

    with patch.object(rc, "_load_all_rules_cached", wraps=real_loader) as spy:
        fresh_cache.get_all_rules()  # laadt (call 1)
        fresh_cache.get_all_rules()  # memo-hit
        assert spy.call_count == 1

        fresh_cache.clear_cache()  # invalidatie
        fresh_cache.get_all_rules()  # herlaadt (call 2)

    assert spy.call_count == 2


def test_memo_data_matches_loader(fresh_cache):
    """De gememoiseerde data is inhoudelijk gelijk aan een directe load."""
    direct = rc._load_all_rules_cached(str(fresh_cache.regels_dir))
    fresh_cache._rules_memo = None
    fresh_cache._rules_memo_ts = 0.0

    via_cache = fresh_cache.get_all_rules()

    assert set(via_cache.keys()) == set(direct.keys())
    assert len(via_cache) > 0
