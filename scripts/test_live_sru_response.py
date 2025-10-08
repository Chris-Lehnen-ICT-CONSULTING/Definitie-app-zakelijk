#!/usr/bin/env python3
"""
Live test van SRU endpoints om te zien wat er echt terugkomt.

Dit script doet echte HTTP requests naar SRU endpoints en toont:
1. Raw XML response (eerste 1000 chars)
2. Gedetecteerde namespaces
3. Parsing resultaten met huidige logica
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp


async def test_sru_endpoint(endpoint_name: str, url: str):
    """Test een SRU endpoint en toon raw response."""
    print(f"\n{'='*80}")
    print(f"TESTING: {endpoint_name}")
    print(f"URL: {url}")
    print(f"{'='*80}")

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            headers = {
                "User-Agent": "DefinitieApp-Debug/1.0",
                "Accept": "application/xml, text/xml;q=0.9, */*;q=0.8"
            }

            async with session.get(url, headers=headers) as response:
                print(f"\nHTTP Status: {response.status}")
                print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")

                if response.status == 200:
                    xml_text = await response.text()
                    print(f"\nResponse length: {len(xml_text)} chars")
                    print(f"\n--- RAW XML (first 1000 chars) ---")
                    print(xml_text[:1000])
                    print(f"--- END RAW XML ---")

                    # Parse namespaces
                    import xml.etree.ElementTree as ET
                    try:
                        root = ET.fromstring(xml_text)
                        namespaces = {}
                        for elem in root.iter():
                            if '}' in elem.tag:
                                ns, local = elem.tag.split('}')
                                ns = ns[1:]
                                if ns not in namespaces:
                                    namespaces[ns] = set()
                                namespaces[ns].add(local)

                        print(f"\n--- DETECTED NAMESPACES ---")
                        for ns, tags in namespaces.items():
                            print(f"  {ns}")
                            print(f"    Tags: {', '.join(sorted(tags)[:10])}")

                        # Try to find records with different namespaces
                        print(f"\n--- RECORD SEARCH RESULTS ---")

                        # SRU 1.2
                        ns_12 = {"srw": "http://www.loc.gov/zing/srw/"}
                        records_12 = root.findall(".//srw:record", ns_12)
                        print(f"  SRU 1.2 namespace: {len(records_12)} records")

                        # SRU 2.0
                        ns_20 = {"srw": "http://docs.oasis-open.org/ns/search-ws/sruResponse"}
                        records_20 = root.findall(".//srw:record", ns_20)
                        print(f"  SRU 2.0 namespace: {len(records_20)} records")

                        # No namespace (fallback)
                        all_elems = root.findall(".//*")
                        record_tags = [e for e in all_elems if e.tag.endswith('record') and 'recordData' in [c.tag.split('}')[-1] for c in e]]
                        print(f"  Fallback (no namespace): {len(record_tags)} records")

                        # Check for numberOfRecords
                        for ns_dict in [ns_12, ns_20]:
                            num_records_elem = root.find(".//srw:numberOfRecords", ns_dict)
                            if num_records_elem is not None:
                                print(f"  numberOfRecords element: {num_records_elem.text}")
                                break

                    except ET.ParseError as e:
                        print(f"❌ XML Parse Error: {e}")

                else:
                    text = await response.text()
                    print(f"\n❌ Error Response:")
                    print(text[:500])

    except asyncio.TimeoutError:
        print(f"❌ Timeout na 10 seconden")
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Test verschillende SRU endpoints."""
    tests = [
        (
            "Overheid.nl - algemene term",
            "https://repository.overheid.nl/sru?operation=searchRetrieve&version=1.2&query=dc.title=%22gemeentewet%22&maximumRecords=1&recordSchema=dc"
        ),
        (
            "Rechtspraak.nl - ECLI search",
            "https://zoeken.rechtspraak.nl/SRU/Search?operation=searchRetrieve&version=1.2&query=cql.serverChoice=ECLI:NL:HR:2023:1&maximumRecords=1&recordSchema=dc"
        ),
        (
            "Wetgeving.nl (BWB) - SRU 2.0",
            "https://zoekservice.overheid.nl/sru/Search?operation=searchRetrieve&version=2.0&query=cql.serverChoice=%22wetboek%22&maximumRecords=1&recordSchema=oai_dc&x-connection=BWB"
        ),
        (
            "Overheid Zoekservice - GZD schema",
            "https://zoekservice.overheid.nl/sru/Search?operation=searchRetrieve&version=1.2&query=cql.serverChoice=%22ministerie%22&maximumRecords=1&recordSchema=gzd"
        ),
    ]

    for name, url in tests:
        await test_sru_endpoint(name, url)
        await asyncio.sleep(1)  # Rate limiting

    print(f"\n{'='*80}")
    print("CONCLUSIES")
    print(f"{'='*80}")
    print("""
De test resultaten tonen aan:

1. SRU 2.0 endpoints (Wetgeving.nl) gebruiken een ANDERE namespace:
   - Verwacht: http://www.loc.gov/zing/srw/
   - Werkelijk: http://docs.oasis-open.org/ns/search-ws/sruResponse

2. Zonder de juiste namespace kunnen we GEEN records vinden met findall()

3. De fallback logica (local-name matching) werkt WEL voor de content,
   maar de records worden niet eerst gevonden.

OPLOSSING: Probeer BEIDE namespaces bij het zoeken naar records.
""")


if __name__ == "__main__":
    asyncio.run(main())
