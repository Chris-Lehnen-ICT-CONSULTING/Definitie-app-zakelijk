#!/usr/bin/env python3
"""
Debug script voor SRU XML parsing problemen.

Dit script test de huidige parsing logica met verschillende XML response formats
om te identificeren waarom bepaalde SRU endpoints geen resultaten opleveren.
"""

import xml.etree.ElementTree as ET

# Verschillende SRU response formats die we kunnen tegenkomen
SRU_12_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
  <srw:version>1.2</srw:version>
  <srw:numberOfRecords>1</srw:numberOfRecords>
  <srw:records>
    <srw:record>
      <srw:recordData>
        <dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/">
          <dc:title>Test Title SRU 1.2</dc:title>
          <dc:description>Test Description</dc:description>
          <dc:identifier>https://example.com/doc1</dc:identifier>
        </dc:dc>
      </srw:recordData>
    </srw:record>
  </srw:records>
</srw:searchRetrieveResponse>"""

SRU_20_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://docs.oasis-open.org/ns/search-ws/sruResponse">
  <srw:version>2.0</srw:version>
  <srw:numberOfRecords>1</srw:numberOfRecords>
  <srw:records>
    <srw:record>
      <srw:recordData>
        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                    xmlns:dc="http://purl.org/dc/elements/1.1/">
          <dc:title>Test Title SRU 2.0</dc:title>
          <dc:description>Test Description</dc:description>
          <dc:identifier>https://example.com/doc2</dc:identifier>
        </oai_dc:dc>
      </srw:recordData>
    </srw:record>
  </srw:records>
</srw:searchRetrieveResponse>"""

SRU_GZD_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
  <srw:version>1.2</srw:version>
  <srw:numberOfRecords>1</srw:numberOfRecords>
  <srw:records>
    <srw:record>
      <srw:recordData>
        <gzd:gzd xmlns:gzd="http://standaarden.overheid.nl/sru">
          <gzd:originalData>
            <title>Test Title GZD</title>
            <description>Test Description GZD</description>
            <identifier>https://example.com/doc3</identifier>
          </gzd:originalData>
        </gzd:gzd>
      </srw:recordData>
    </srw:record>
  </srw:records>
</srw:searchRetrieveResponse>"""

EMPTY_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
  <srw:version>1.2</srw:version>
  <srw:numberOfRecords>0</srw:numberOfRecords>
  <srw:records/>
</srw:searchRetrieveResponse>"""

ERROR_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
  <srw:version>1.2</srw:version>
  <srw:diagnostics>
    <diag:diagnostic xmlns:diag="http://www.loc.gov/zing/srw/diagnostic/">
      <diag:uri>info:srw/diagnostic/1/7</diag:uri>
      <diag:message>Unsupported parameter value</diag:message>
      <diag:details>recordSchema: gzd</diag:details>
    </diag:diagnostic>
  </srw:diagnostics>
</srw:searchRetrieveResponse>"""


def test_current_parsing_logic(xml_content: str, test_name: str) -> dict:
    """
    Test de huidige parsing logica zoals geïmplementeerd in sru_service.py.

    Args:
        xml_content: SRU XML response
        test_name: Naam van de test voor logging

    Returns:
        Dict met parsing resultaten en diagnostics
    """
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")

    result = {
        "test_name": test_name,
        "parsed_successfully": False,
        "records_found": 0,
        "issues": [],
        "namespaces_detected": {},
        "record_data": [],
    }

    try:
        root = ET.fromstring(xml_content)

        # Detecteer namespaces in de XML
        # Element.tag format: {namespace}localname
        for elem in root.iter():
            if "}" in elem.tag:
                ns, local = elem.tag.split("}")
                ns = ns[1:]  # Remove leading {
                if ns not in result["namespaces_detected"]:
                    result["namespaces_detected"][ns] = []
                result["namespaces_detected"][ns].append(local)

        print("\nNamespaces gedetecteerd:")
        for ns, tags in result["namespaces_detected"].items():
            print(f"  {ns}: {set(tags)}")

        # Huidige namespaces zoals gebruikt in sru_service.py
        namespaces = {
            "srw": "http://www.loc.gov/zing/srw/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/",
            "gzd": "http://overheid.nl/gzd",
        }

        print("\nNamespaces in code:")
        for prefix, uri in namespaces.items():
            print(f"  {prefix}: {uri}")

        # Test of we records kunnen vinden
        print("\nZoeken naar records...")
        records = root.findall(".//srw:record", namespaces)
        result["records_found"] = len(records)
        print(f"  Gevonden met namespace prefix: {len(records)} records")

        # Alternatieve zoektechniek zonder namespace (fallback)
        all_records = root.findall(".//*")
        record_tags = [elem for elem in all_records if elem.tag.endswith("record")]
        print(f"  Gevonden zonder namespace (fallback): {len(record_tags)} records")

        # Probeer ook met verschillende SRU 2.0 namespace
        sru20_ns = {"srw": "http://docs.oasis-open.org/ns/search-ws/sruResponse"}
        records_20 = root.findall(".//srw:record", sru20_ns)
        print(f"  Gevonden met SRU 2.0 namespace: {len(records_20)} records")

        # Parse elk record
        for i, record in enumerate(
            records if records else (records_20 if records_20 else record_tags)
        ):
            print(f"\n  Record {i+1}:")

            # Test huidige _find_text_local logica
            def _find_text_local(element: ET.Element, local: str) -> str:
                # 1) Zoek via bekende namespaces
                for ns in ("dc", "dcterms", "gzd"):
                    try:
                        el = element.find(f".//{ns}:{local}", namespaces)
                        if el is not None and el.text:
                            return el.text.strip()
                    except Exception:
                        continue

                # 2) Fallback: loop alle subelements en match op lokale tagnaam
                for el in element.iter():
                    try:
                        tag = el.tag
                        if "}" in tag:
                            tag = tag.split("}", 1)[1]
                        if tag.lower() == local.lower() and el.text:
                            return el.text.strip()
                    except Exception:
                        continue
                return ""

            title = _find_text_local(record, "title")
            description = _find_text_local(record, "description")
            identifier = _find_text_local(record, "identifier")

            print(f"    title: {title or '(NIET GEVONDEN)'}")
            print(f"    description: {description or '(NIET GEVONDEN)'}")
            print(f"    identifier: {identifier or '(NIET GEVONDEN)'}")

            if title or description:
                result["record_data"].append(
                    {
                        "title": title,
                        "description": description,
                        "identifier": identifier,
                    }
                )

        if result["records_found"] == 0 and len(record_tags) > 0:
            result["issues"].append(
                "Records gevonden zonder namespace, maar niet met namespace prefix"
            )

        if result["records_found"] > 0:
            result["parsed_successfully"] = True

    except ET.ParseError as e:
        result["issues"].append(f"XML Parse Error: {e}")
        print(f"\n❌ XML PARSE ERROR: {e}")
    except Exception as e:
        result["issues"].append(f"Unexpected error: {e}")
        print(f"\n❌ UNEXPECTED ERROR: {e}")

    # Check voor SRU diagnostics
    try:
        root = ET.fromstring(xml_content)
        # Probeer verschillende namespace varianten
        for diag_ns in [
            {"srw": "http://www.loc.gov/zing/srw/"},
            {"srw": "http://docs.oasis-open.org/ns/search-ws/sruResponse"},
        ]:
            diagnostics = root.find(".//srw:diagnostics", diag_ns)
            if diagnostics is not None:
                print("\n⚠️  SRU DIAGNOSTICS gevonden:")
                for child in diagnostics:
                    for elem in child:
                        tag = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
                        if elem.text:
                            print(f"    {tag}: {elem.text}")
                result["issues"].append("SRU diagnostics aanwezig")
                break
    except Exception:
        pass

    # Summary
    print(f"\n{'='*60}")
    print(f"RESULTAAT: {test_name}")
    print(f"{'='*60}")
    print(f"  ✓ Parsed: {result['parsed_successfully']}")
    print(f"  ✓ Records: {result['records_found']}")
    print(f"  ✓ Data extracted: {len(result['record_data'])}")
    if result["issues"]:
        print(f"  ⚠️  Issues: {', '.join(result['issues'])}")

    return result


def main():
    """Run parsing tests voor verschillende SRU response formats."""
    print("SRU XML PARSING DEBUG TOOL")
    print("=" * 60)

    tests = [
        (SRU_12_RESPONSE, "SRU 1.2 Response (Dublin Core)"),
        (SRU_20_RESPONSE, "SRU 2.0 Response (OAI-DC)"),
        (SRU_GZD_RESPONSE, "GZD Response (Overheid.nl)"),
        (EMPTY_RESPONSE, "Empty Response"),
        (ERROR_RESPONSE, "Error Response (Diagnostics)"),
    ]

    results = []
    for xml, name in tests:
        result = test_current_parsing_logic(xml, name)
        results.append(result)

    # Final summary
    print("\n\n" + "=" * 60)
    print("SAMENVATTING VAN ALLE TESTS")
    print("=" * 60)

    for result in results:
        status = "✓ OK" if result["parsed_successfully"] else "❌ FAIL"
        print(f"\n{status} {result['test_name']}")
        print(f"    Records: {result['records_found']}")
        print(f"    Data: {len(result['record_data'])} items")
        if result["issues"]:
            for issue in result["issues"]:
                print(f"    ⚠️  {issue}")

    # Aanbevelingen
    print("\n" + "=" * 60)
    print("AANBEVELINGEN VOOR VERBETERING")
    print("=" * 60)

    print(
        """
1. NAMESPACE MISMATCH PROBLEEM:
   - SRU 1.2 gebruikt: http://www.loc.gov/zing/srw/
   - SRU 2.0 gebruikt: http://docs.oasis-open.org/ns/search-ws/sruResponse
   - Code heeft alleen SRU 1.2 namespace!

   OPLOSSING: Probeer beide namespaces in findall()

2. GZD NAMESPACE PROBLEEM:
   - Code verwacht: http://overheid.nl/gzd
   - Werkelijke namespaces kunnen variëren per endpoint

   OPLOSSING: Gebruik local-name fallback (al geïmplementeerd)

3. DEBUG LOGGING ONTBREEKT:
   - Bij lege responses wordt niet gelogd wat er terugkwam
   - Geen logging van raw XML bij parse failures

   OPLOSSING: Log raw XML (eerste 500 chars) bij parse issues

4. DIAGNOSTICS NIET GECONTROLEERD VOOR LOGGING:
   - SRU diagnostics messages geven waardevolle debug info
   - Deze worden nu geparst maar niet gelogd in main flow

   OPLOSSING: Log diagnostics op WARNING level voor betere debugging
"""
    )


if __name__ == "__main__":
    main()
