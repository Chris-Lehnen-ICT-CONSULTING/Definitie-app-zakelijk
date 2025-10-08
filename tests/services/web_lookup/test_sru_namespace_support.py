"""
Unit tests voor SRU namespace parsing fixes.

Test suite voor:
1. SRU 1.2 namespace parsing (http://www.loc.gov/zing/srw/)
2. SRU 2.0 namespace parsing (http://docs.oasis-open.org/ns/search-ws/sruResponse) - NIEUW
3. Multi-namespace fallback mechanisme
4. Diagnostic logging bij fouten
5. Schema configuratie (dc vs gzd)

Deze tests valideren de fixes voor:
- Issue: SRU 2.0 responses werden niet geparsed
- Issue: Overheid.nl 'dc schema not supported' errors
- Issue: Diagnostics werden niet gelogd
"""

from unittest.mock import MagicMock, patch

import pytest

from src.services.web_lookup.sru_service import SRUConfig, SRUService


class TestSRUNamespaceSupport:
    """Test SRU 1.2 en 2.0 namespace parsing."""

    def test_sru_12_namespace_parsing(self):
        """Test dat SRU 1.2 responses correct geparsed worden."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test SRU 1.2",
            base_url="https://example.com/sru",
            default_collection="",
            record_schema="dc",
            sru_version="1.2",
        )

        # SRU 1.2 response met http://www.loc.gov/zing/srw/ namespace
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
          <srw:version>1.2</srw:version>
          <srw:numberOfRecords>1</srw:numberOfRecords>
          <srw:records>
            <srw:record>
              <srw:recordData>
                <dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/">
                  <dc:title>Test Title SRU 1.2</dc:title>
                  <dc:description>Test description for SRU 1.2</dc:description>
                  <dc:identifier>https://example.com/1</dc:identifier>
                  <dc:subject>Test subject</dc:subject>
                </dc:dc>
              </srw:recordData>
            </srw:record>
          </srw:records>
        </srw:searchRetrieveResponse>"""

        results = svc._parse_sru_response(xml, term="test", config=cfg)

        assert len(results) == 1, "SRU 1.2 response should be parsed"
        assert results[0].metadata.get("dc_title") == "Test Title SRU 1.2"
        assert results[0].metadata.get("dc_subject") == "Test subject"
        assert results[0].source.name == "Test SRU 1.2"
        assert results[0].success is True

    def test_sru_20_namespace_parsing(self):
        """Test dat SRU 2.0 responses correct geparsed worden (NIEUW FIX)."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test SRU 2.0",
            base_url="https://example.com/sru",
            default_collection="",
            record_schema="oai_dc",
            sru_version="2.0",
        )

        # SRU 2.0 response met http://docs.oasis-open.org/ns/search-ws/sruResponse namespace
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://docs.oasis-open.org/ns/search-ws/sruResponse">
          <srw:version>2.0</srw:version>
          <srw:numberOfRecords>1</srw:numberOfRecords>
          <srw:records>
            <srw:record>
              <srw:recordData>
                <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                            xmlns:dc="http://purl.org/dc/elements/1.1/">
                  <dc:title>Wetboek van Strafrecht</dc:title>
                  <dc:description>Test BWB content from SRU 2.0</dc:description>
                  <dc:identifier>https://example.com/bwb</dc:identifier>
                  <dc:type>Wet</dc:type>
                </oai_dc:dc>
              </srw:recordData>
            </srw:record>
          </srw:records>
        </srw:searchRetrieveResponse>"""

        results = svc._parse_sru_response(xml, term="wetboek", config=cfg)

        assert (
            len(results) == 1
        ), "SRU 2.0 response should be parsed after namespace fix"
        assert results[0].metadata.get("dc_title") == "Wetboek van Strafrecht"
        assert results[0].metadata.get("dc_type") == "Wet"
        assert "BWB" in results[0].definition or "Wetboek" in results[0].definition

    def test_namespace_fallback_mixed_response(self):
        """Test dat namespace fallback correct werkt bij mixed/unknown namespaces."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test Mixed NS",
            base_url="https://example.com/sru",
            default_collection="",
            record_schema="dc",
            sru_version="1.2",
        )

        # Response met onbekende namespace maar correcte local-names
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
          <srw:records>
            <srw:record>
              <srw:recordData>
                <custom:record xmlns:custom="http://example.com/custom">
                  <title>Fallback Title</title>
                  <description>Fallback description via local-name matching</description>
                  <identifier>https://example.com/fallback</identifier>
                </custom:record>
              </srw:recordData>
            </srw:record>
          </srw:records>
        </srw:searchRetrieveResponse>"""

        results = svc._parse_sru_response(xml, term="fallback", config=cfg)

        # Moet werken via local-name fallback in _find_text_local()
        assert (
            len(results) == 1
        ), "Mixed namespace should be handled via local-name fallback"
        assert results[0].metadata.get("dc_title") == "Fallback Title"

    def test_multiple_records_parsing(self):
        """Test dat meerdere records correct geparsed worden."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test Multi-Record",
            base_url="https://example.com/sru",
            default_collection="",
            record_schema="dc",
            sru_version="1.2",
        )

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
          <srw:numberOfRecords>2</srw:numberOfRecords>
          <srw:records>
            <srw:record>
              <srw:recordData>
                <dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/">
                  <dc:title>First Record</dc:title>
                  <dc:description>First description</dc:description>
                  <dc:identifier>https://example.com/1</dc:identifier>
                </dc:dc>
              </srw:recordData>
            </srw:record>
            <srw:record>
              <srw:recordData>
                <dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/">
                  <dc:title>Second Record</dc:title>
                  <dc:description>Second description</dc:description>
                  <dc:identifier>https://example.com/2</dc:identifier>
                </dc:dc>
              </srw:recordData>
            </srw:record>
          </srw:records>
        </srw:searchRetrieveResponse>"""

        results = svc._parse_sru_response(xml, term="record", config=cfg)

        assert len(results) == 2, "Should parse both records"
        assert results[0].metadata.get("dc_title") == "First Record"
        assert results[1].metadata.get("dc_title") == "Second Record"

    def test_empty_response(self):
        """Test dat lege responses correct afgehandeld worden."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test Empty",
            base_url="https://example.com/sru",
            default_collection="",
            record_schema="dc",
            sru_version="1.2",
        )

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
          <srw:numberOfRecords>0</srw:numberOfRecords>
          <srw:records>
          </srw:records>
        </srw:searchRetrieveResponse>"""

        results = svc._parse_sru_response(xml, term="nothing", config=cfg)

        assert len(results) == 0, "Empty response should return empty list"

    def test_malformed_xml_handling(self):
        """Test dat malformed XML gracefully afgehandeld wordt."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test Malformed",
            base_url="https://example.com/sru",
            default_collection="",
            record_schema="dc",
            sru_version="1.2",
        )

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
          <srw:records>
            <srw:record>
              <!-- Missing closing tag -->
        </srw:searchRetrieveResponse>"""

        results = svc._parse_sru_response(xml, term="test", config=cfg)

        # Should return empty list without crashing
        assert len(results) == 0, "Malformed XML should return empty list"


class TestSRUSchemaConfiguration:
    """Test schema configuration per endpoint."""

    def test_overheid_nl_uses_gzd_schema(self):
        """Test dat Overheid.nl repository gebruikt GZD schema (FIX)."""
        svc = SRUService()

        # Check dat overheid endpoint gzd schema heeft
        assert "overheid" in svc.endpoints
        config = svc.endpoints["overheid"]

        assert (
            config.record_schema == "gzd"
        ), "Overheid.nl repository moet GZD schema gebruiken (fix voor 'dc not supported' error)"

    def test_overheid_zoek_uses_gzd_schema(self):
        """Test dat Overheid.nl Zoekservice GZD schema gebruikt (FIX)."""
        svc = SRUService()

        # Check dat overheid_zoek endpoint gzd schema heeft
        assert "overheid_zoek" in svc.endpoints
        config = svc.endpoints["overheid_zoek"]

        assert (
            config.record_schema == "gzd"
        ), "Overheid.nl Zoekservice moet GZD schema gebruiken (fix voor 'dc not supported' error)"

    def test_wetgeving_nl_uses_gzd_schema(self):
        """Test dat Wetgeving.nl GZD schema gebruikt (FIX 2025-10-08)."""
        svc = SRUService()

        assert "wetgeving_nl" in svc.endpoints
        config = svc.endpoints["wetgeving_nl"]

        # CHANGED: oai_dc → gzd (matches working Overheid.nl config)
        assert (
            config.record_schema == "gzd"
        ), "Wetgeving.nl moet GZD schema gebruiken (na schema fix)"
        assert config.sru_version == "2.0", "Wetgeving.nl gebruikt SRU 2.0"

    def test_rechtspraak_sru_disabled(self):
        """Test dat Rechtspraak.nl SRU endpoint is disabled (nu REST only)."""
        svc = SRUService()

        # Rechtspraak is nu commented out in sru_service.py (DNS failure)
        # Gebruik in plaats daarvan rechtspraak_rest_service.py met REST API
        assert "rechtspraak" not in svc.endpoints, (
            "Rechtspraak SRU moet disabled zijn (zoeken.rechtspraak.nl bestaat niet meer). "
            "Gebruik rechtspraak_rest_service.py voor ECLI lookups."
        )


class TestSRUDiagnosticLogging:
    """Test dat SRU diagnostics correct gelogd worden."""

    def test_diagnostic_logging_on_schema_error(self):
        """Test dat SRU diagnostics gelogd worden bij schema errors."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test Diagnostics",
            base_url="https://example.com",
            record_schema="dc",
            default_collection="",
        )

        # XML met diagnostic: schema not supported
        xml_with_diag = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
          <srw:version>1.2</srw:version>
          <srw:diagnostics>
            <diag:diagnostic xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/">
              <diag:uri>info:srw/diagnostic/1/6</diag:uri>
              <diag:message>record schema not supported</diag:message>
              <diag:details>Schema 'dc' is not supported by this endpoint</diag:details>
            </diag:diagnostic>
          </srw:diagnostics>
          <srw:numberOfRecords>0</srw:numberOfRecords>
        </srw:searchRetrieveResponse>"""

        with patch("src.services.web_lookup.sru_service.logger"):
            results = svc._parse_sru_response(xml_with_diag, term="test", config=cfg)

            # Verify empty results (geen crash)
            assert (
                len(results) == 0
            ), "Response met diagnostics moet lege lijst returnen"

            # Note: Diagnostic logging gebeurt in search() method, niet in _parse_sru_response()
            # Deze test valideert dat parsing niet crasht bij diagnostics

    def test_diagnostic_extraction_helper_method(self):
        """Test dat _extract_diag_from_response() diagnostics correct parsed."""
        svc = SRUService()

        # SRU 2.0 diagnostic response
        xml_sru20 = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://docs.oasis-open.org/ns/search-ws/sruResponse">
          <srw:diagnostics>
            <diag:diagnostic xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/">
              <diag:uri>info:srw/diagnostic/1/6</diag:uri>
              <diag:message>record schema not supported</diag:message>
              <diag:details>Schema 'dc' is not available</diag:details>
            </diag:diagnostic>
          </srw:diagnostics>
        </srw:searchRetrieveResponse>"""

        diag = svc._extract_diag_from_response(xml_sru20)

        assert diag.get("diag_uri") == "info:srw/diagnostic/1/6"
        assert diag.get("diag_message") == "record schema not supported"
        assert diag.get("diag_details") == "Schema 'dc' is not available"

    def test_diagnostic_extraction_sru_12(self):
        """Test diagnostic extraction voor SRU 1.2 namespace."""
        svc = SRUService()

        xml_sru12 = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
          <srw:diagnostics>
            <diag:diagnostic xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/">
              <diag:uri>info:srw/diagnostic/1/1</diag:uri>
              <diag:message>General error</diag:message>
            </diag:diagnostic>
          </srw:diagnostics>
        </srw:searchRetrieveResponse>"""

        diag = svc._extract_diag_from_response(xml_sru12)

        assert diag.get("diag_uri") == "info:srw/diagnostic/1/1"
        assert diag.get("diag_message") == "General error"

    def test_diagnostic_extraction_no_diagnostics(self):
        """Test dat geen diagnostics in success response geen errors geeft."""
        svc = SRUService()

        xml_success = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
          <srw:numberOfRecords>5</srw:numberOfRecords>
        </srw:searchRetrieveResponse>"""

        diag = svc._extract_diag_from_response(xml_success)

        assert diag == {}, "Geen diagnostics moet lege dict returnen"


class TestSRUGZDSchemaSupport:
    """Test GZD (Government Zoekmachine Dublin Core) schema parsing."""

    def test_gzd_schema_parsing(self):
        """Test dat GZD schema responses correct geparsed worden."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test GZD",
            base_url="https://example.com/sru",
            default_collection="",
            record_schema="gzd",
            sru_version="1.2",
        )

        # GZD schema response (gebruikt local-name fallback)
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
          <srw:records>
            <srw:record>
              <srw:recordData>
                <gzd:gzd xmlns:gzd="http://overheid.nl/gzd">
                  <title>GZD Test Titel</title>
                  <description>GZD test beschrijving</description>
                  <identifier>https://zoekservice.overheid.nl/test</identifier>
                  <type>Wetsartikel</type>
                </gzd:gzd>
              </srw:recordData>
            </srw:record>
          </srw:records>
        </srw:searchRetrieveResponse>"""

        results = svc._parse_sru_response(xml, term="test", config=cfg)

        assert (
            len(results) == 1
        ), "GZD schema should be parsed via namespace registration"
        assert results[0].metadata.get("dc_title") == "GZD Test Titel"
        assert results[0].metadata.get("dc_type") == "Wetsartikel"
        assert results[0].metadata.get("record_schema") == "gzd"


class TestSRUConfidenceCalculation:
    """Test confidence score berekening."""

    def test_exact_title_match_high_confidence(self):
        """Test dat exacte titel match hoge confidence geeft."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test",
            base_url="https://example.com",
            record_schema="dc",
            default_collection="",
            confidence_weight=1.0,
        )

        confidence = svc._calculate_confidence(
            term="wetboek van strafrecht",
            title="Wetboek van Strafrecht",
            description="",
            subject="",
            config=cfg,
        )

        assert (
            confidence >= 0.9
        ), "Exacte title match moet hoge confidence (>= 0.9) geven"

    def test_partial_title_match_medium_confidence(self):
        """Test dat partial titel match medium confidence geeft."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test",
            base_url="https://example.com",
            record_schema="dc",
            default_collection="",
            confidence_weight=1.0,
        )

        confidence = svc._calculate_confidence(
            term="strafrecht",
            title="Wetboek van Strafrecht - Artikel 1",
            description="",
            subject="",
            config=cfg,
        )

        assert (
            0.7 <= confidence <= 0.9
        ), "Partial title match moet medium confidence geven"

    def test_description_match_lower_confidence(self):
        """Test dat description match lagere confidence geeft dan title match."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test",
            base_url="https://example.com",
            record_schema="dc",
            default_collection="",
            confidence_weight=1.0,
        )

        confidence = svc._calculate_confidence(
            term="strafrecht",
            title="Wetsartikel",
            description="Dit artikel gaat over strafrecht",
            subject="",
            config=cfg,
        )

        assert (
            0.5 <= confidence <= 0.75
        ), "Description match moet lagere confidence geven"


class TestSRURecordSkipping:
    """Test dat records zonder titel/beschrijving geskipt worden."""

    def test_skip_record_without_title_and_description(self):
        """Test dat records zonder titel EN beschrijving geskipt worden."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test",
            base_url="https://example.com",
            record_schema="dc",
            default_collection="",
        )

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
          <srw:records>
            <srw:record>
              <srw:recordData>
                <dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/">
                  <dc:identifier>https://example.com/empty</dc:identifier>
                  <dc:type>Unknown</dc:type>
                </dc:dc>
              </srw:recordData>
            </srw:record>
            <srw:record>
              <srw:recordData>
                <dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/">
                  <dc:title>Valid Record</dc:title>
                  <dc:identifier>https://example.com/valid</dc:identifier>
                </dc:dc>
              </srw:recordData>
            </srw:record>
          </srw:records>
        </srw:searchRetrieveResponse>"""

        results = svc._parse_sru_response(xml, term="test", config=cfg)

        # Eerste record moet geskipt zijn, tweede moet parsed zijn
        assert len(results) == 1, "Record zonder titel/beschrijving moet geskipt worden"
        assert results[0].metadata.get("dc_title") == "Valid Record"


class TestSRUMetadataExtraction:
    """Test metadata extractie uit SRU records."""

    def test_metadata_extraction_complete(self):
        """Test dat alle metadata velden correct geëxtraheerd worden."""
        svc = SRUService()
        cfg = SRUConfig(
            name="Test Metadata",
            base_url="https://example.com",
            record_schema="dc",
            default_collection="",
        )

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
          <srw:records>
            <srw:record>
              <srw:recordData>
                <dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/">
                  <dc:title>Complete Metadata Record</dc:title>
                  <dc:description>Full description with all fields</dc:description>
                  <dc:identifier>https://example.com/complete</dc:identifier>
                  <dc:subject>Legal Subject</dc:subject>
                  <dc:type>Wet</dc:type>
                  <dc:date>2025-01-15</dc:date>
                </dc:dc>
              </srw:recordData>
            </srw:record>
          </srw:records>
        </srw:searchRetrieveResponse>"""

        results = svc._parse_sru_response(xml, term="metadata", config=cfg)

        assert len(results) == 1
        metadata = results[0].metadata

        # Verify all metadata fields
        assert metadata.get("dc_title") == "Complete Metadata Record"
        assert metadata.get("dc_subject") == "Legal Subject"
        assert metadata.get("dc_type") == "Wet"
        assert metadata.get("dc_date") == "2025-01-15"
        assert metadata.get("dc_identifier") == "https://example.com/complete"
        assert metadata.get("sru_endpoint") == "Test Metadata"
        assert metadata.get("record_schema") == "dc"
        assert "retrieved_at" in metadata
        assert "content_hash" in metadata
