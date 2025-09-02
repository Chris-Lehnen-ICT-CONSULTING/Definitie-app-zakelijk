from datetime import datetime, timezone

import pytest


def test_build_provenance_records_structure_and_ordering():
    try:
        from services.web_lookup.provenance import build_provenance
    except Exception as e:
        pytest.fail(f"provenance module missing or import failed: {e}")

    # Minimal WebLookupResult-like dicts
    now = datetime.now(timezone.utc)
    inputs = [
        {
            "provider": "wikipedia",
            "source_label": "Wikipedia NL",
            "title": "Artikel A",
            "url": "https://nl.wikipedia.org/wiki/A",
            "snippet": "A ...",
            "score": 0.8,
            "used_in_prompt": True,
            "retrieved_at": now,
        },
        {
            "provider": "sru_overheid",
            "source_label": "Overheid.nl",
            "title": "Wet B",
            "url": "https://overheid.nl/B",
            "snippet": "B ...",
            "score": 0.9,
            "used_in_prompt": False,
            "retrieved_at": now,
        },
    ]

    prov = build_provenance(inputs)
    assert isinstance(prov, list) and len(prov) == 2
    for item in prov:
        assert set(
            [
                "provider",
                "title",
                "url",
                "snippet",
                "score",
                "used_in_prompt",
                "retrieved_at",
            ]
        ).issubset(item.keys())

    # Ordering: highest score first
    assert prov[0]["score"] >= prov[1]["score"]
