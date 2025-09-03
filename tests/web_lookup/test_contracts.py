import inspect

import pytest


def test_web_lookup_contract_dataclass_structure():
    """WebLookupResult contract exposes required fields per epic spec."""
    try:
        from services.web_lookup.contracts import WebLookupResult
    except Exception as e:
        pytest.fail(f"contracts module missing or import failed: {e}")

    # Must be a dataclass-like type
    assert inspect.isclass(WebLookupResult)

    # Required fields (names only; types validated downstream)
    required = {
        "provider",
        "source_label",
        "title",
        "url",
        "snippet",
        "score",
        "used_in_prompt",
        "position_in_prompt",
        "retrieved_at",
        "content_hash",
        "error",
        "legal_refs",
        "is_authoritative",
        "legal_weight",
        "is_plurale_tantum",
        "requires_singular_check",
        "cache_key",
        "ttl_seconds",
    }

    fields = set(getattr(WebLookupResult, "__dataclass_fields__", {}).keys())
    assert required.issubset(fields), f"Missing fields: {required - fields}"


def test_lookup_error_type_contains_expected_members():
    try:
        from services.web_lookup.contracts import LookupErrorType
    except Exception as e:
        pytest.fail(f"contracts module missing or import failed: {e}")

    expected = {
        "TIMEOUT",
        "NETWORK",
        "PARSE",
        "RATE_LIMIT",
        "AUTH",
        "INVALID_RESPONSE",
    }

    members = set([m.name for m in LookupErrorType])
    assert expected.issubset(members), f"Missing error types: {expected - members}"
