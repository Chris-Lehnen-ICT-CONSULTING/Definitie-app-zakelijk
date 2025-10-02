from datetime import UTC, datetime, timezone

import pytest


def _mk_result(provider: str, title: str, url: str, score: float, content_hash: str):
    """Factory for minimal WebLookupResult-like dicts for ranking/dedup tests."""
    return {
        "provider": provider,
        "source_label": provider.title(),
        "title": title,
        "url": url,
        "snippet": title,
        "score": score,
        "used_in_prompt": False,
        "position_in_prompt": -1,
        "retrieved_at": datetime.now(UTC),
        "content_hash": content_hash,
        "error": None,
        "legal_refs": [],
        "is_authoritative": provider in {"sru_overheid", "rechtspraak"},
        "legal_weight": 1.0 if provider == "sru_overheid" else 0.0,
        "is_plurale_tantum": False,
        "requires_singular_check": False,
        "cache_key": f"{provider}:x:y",
        "ttl_seconds": 3600,
    }


def test_rank_and_dedup_applies_weights_and_determinism():
    try:
        from services.web_lookup.ranking import rank_and_dedup
    except Exception as e:
        pytest.fail(f"ranking module missing or import failed: {e}")

    items = [
        _mk_result("wikipedia", "A", "https://wikipedia.org/a", 0.8, "h1"),
        _mk_result("sru_overheid", "B", "https://overheid.nl/b", 0.6, "h2"),
        _mk_result("wikipedia", "C", "https://wikipedia.org/c", 0.9, "h3"),
        # Duplicate by URL (should keep highest final score)
        _mk_result("wikipedia", "C-dup", "https://wikipedia.org/c", 0.85, "h3"),
    ]

    provider_weights = {"wikipedia": 0.7, "sru_overheid": 1.0}
    ranked = rank_and_dedup(items, provider_weights)

    # Deduped length: 3 unique URLs
    assert len(ranked) == 3

    # Deterministic order: by final_score desc, then authoritative, then title asc, then url
    finals = []
    for r in ranked:
        w = provider_weights.get(r["provider"], 1.0)
        finals.append(round(w * float(r["score"]), 6))

    assert finals == sorted(finals, reverse=True)


def test_dedup_by_content_hash_when_urls_differ():
    from services.web_lookup.ranking import rank_and_dedup

    items = [
        _mk_result("wikipedia", "SameContent1", "https://w.org/x1", 0.5, "same"),
        _mk_result("wikipedia", "SameContent2", "https://w.org/x2", 0.6, "same"),
    ]
    ranked = rank_and_dedup(items, {"wikipedia": 0.7})
    assert len(ranked) == 1
    # Keeps higher score item
    assert ranked[0]["title"].startswith("SameContent2")
