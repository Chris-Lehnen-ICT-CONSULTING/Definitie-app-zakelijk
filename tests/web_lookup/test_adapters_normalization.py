from datetime import datetime


def test_wikipedia_build_lookup_result_contract_like():
    from services.web_lookup.wikipedia_service import WikipediaService

    svc = WikipediaService(language="nl")
    page_info = {"title": "Amsterdam"}
    page_details = {
        "pageid": 12345,
        "title": "Amsterdam",
        "type": "standard",
        "timestamp": "2025-01-01T00:00:00Z",
        "content_urls": {
            "desktop": {"page": "https://nl.wikipedia.org/wiki/Amsterdam"}
        },
        "extract": "Amsterdam is de hoofdstad van Nederland.",
    }

    result = svc._build_lookup_result("Amsterdam", page_info, page_details)
    assert result.source.name == "Wikipedia"
    assert result.source.url.startswith("https://nl.wikipedia.org/wiki/")
    assert result.source.is_juridical is False
    # Metadata contains retrieved_at and content_hash
    assert "retrieved_at" in result.metadata
    assert "content_hash" in result.metadata


def test_sru_parse_response_adds_metadata_and_url():
    from services.web_lookup.sru_service import SRUConfig, SRUService

    svc = SRUService()
    cfg = SRUConfig(
        name="Overheid.nl",
        base_url="https://repository.overheid.nl/sru",
        default_collection="rijksoverheid",
        record_schema="dc",
        confidence_weight=1.0,
        is_juridical=True,
    )

    xml = """
    <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/" xmlns:dc="http://purl.org/dc/elements/1.1/">
      <srw:records>
        <srw:record>
          <srw:recordData>
            <dc:title>Wetboek van Strafrecht</dc:title>
            <dc:description>Beschrijving</dc:description>
            <dc:identifier>https://wetten.overheid.nl/BWBR0001854/</dc:identifier>
            <dc:subject>Strafrecht</dc:subject>
            <dc:type>wet</dc:type>
            <dc:date>2020-01-01</dc:date>
          </srw:recordData>
        </srw:record>
      </srw:records>
    </srw:searchRetrieveResponse>
    """

    results = svc._parse_sru_response(xml, term="Strafrecht", config=cfg)
    assert results, "Expected at least one result"
    r = results[0]
    assert r.source.url.startswith("http")
    assert r.source.is_juridical is True
    assert "retrieved_at" in r.metadata
    assert "content_hash" in r.metadata
