import pytest


pytestmark = pytest.mark.smoke_web_lookup


def test_sru_gzd_parser_parses_basic_fields():
    from services.web_lookup.sru_service import SRUService, SRUConfig

    svc = SRUService()
    cfg = SRUConfig(
        name="Overheid.nl Zoekservice",
        base_url="https://zoekservice.overheid.nl/sru/Search",
        default_collection="rijksoverheid",
        record_schema="gzd",
        confidence_weight=1.0,
        is_juridical=True,
    )

    # Minimal SRU response with local-name tags (no explicit dc: namespace)
    xml = """
    <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
      <srw:records>
        <srw:record>
          <srw:recordData>
            <title>Ministerie van Justitie en Veiligheid</title>
            <description>Nieuwsbericht</description>
            <identifier>https://www.rijksoverheid.nl/ministeries/ministerie-van-justitie-en-veiligheid</identifier>
            <subject>Beleid</subject>
            <type>document</type>
            <date>2025-01-01</date>
          </srw:recordData>
        </srw:record>
      </srw:records>
    </srw:searchRetrieveResponse>
    """

    results = svc._parse_sru_response(xml, term="justitie", config=cfg)
    assert results, "Expected parsed results for local-name GZD-like XML"
    r = results[0]
    assert r.source.is_juridical is True
    assert "Justitie".lower() in (r.metadata.get("dc_title", "").lower())
    assert r.source.url.startswith("http")
