#!/usr/bin/env python3
"""
Test script om SRU endpoints te verifiëren.
Valideert URL's en CQL query syntax voor Nederlandse juridische bronnen.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import aiohttp
except ImportError:
    print("ERROR: aiohttp niet geïnstalleerd. Run: pip install aiohttp")
    sys.exit(1)


async def test_endpoint(name: str, url: str, query: str, extra_info: str = "") -> dict:
    """Test een SRU endpoint met een simpele query."""
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"Query: {query}")
    if extra_info:
        print(f"Info: {extra_info}")
    print(f"{'='*80}")

    result = {
        "name": name,
        "url": url,
        "query": query,
        "success": False,
        "status": None,
        "records": 0,
        "error": None,
        "diagnostics": None,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                result["status"] = resp.status
                text = await resp.text()

                print(f"Status: {resp.status}")

                if resp.status == 200:
                    # Parse voor records
                    import xml.etree.ElementTree as ET

                    try:
                        root = ET.fromstring(text)
                        # Try different namespace variants
                        namespaces = [
                            {"srw": "http://www.loc.gov/zing/srw/"},  # SRU 1.2
                            {
                                "srw": "http://docs.oasis-open.org/ns/search-ws/sruResponse"
                            },  # SRU 2.0
                        ]

                        records = []
                        for ns in namespaces:
                            records = root.findall(".//srw:record", ns)
                            if records:
                                break

                        result["records"] = len(records)
                        result["success"] = True
                        print(f"✅ SUCCESS - Found {len(records)} records")

                        # Check diagnostics
                        for ns in namespaces:
                            diag = root.find(".//srw:diagnostics", ns)
                            if diag is not None:
                                msg_el = diag.find(".//srw:message", ns)
                                if msg_el is not None and msg_el.text:
                                    result["diagnostics"] = msg_el.text
                                    print(f"⚠️  Diagnostic: {msg_el.text}")
                                break

                    except ET.ParseError as e:
                        result["error"] = f"XML parse error: {e}"
                        print(f"❌ XML parse error: {e}")
                        print(f"Response preview: {text[:500]}")
                else:
                    result["error"] = f"HTTP {resp.status}"
                    print(f"❌ HTTP {resp.status}")
                    print(f"Response preview: {text[:500]}")

    except TimeoutError:
        result["error"] = "Timeout"
        print("❌ TIMEOUT")
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ ERROR: {e}")

    return result


async def main():
    """Test alle SRU endpoints."""
    print("=" * 80)
    print("SRU ENDPOINT VERIFICATION TEST")
    print("=" * 80)

    # Test cases met verschillende query strategieën
    test_cases = [
        # Wetgeving.nl (BWB via Zoekservice)
        {
            "name": "Wetgeving.nl - Current (BWB via Zoekservice)",
            "url": "https://zoekservice.overheid.nl/sru/Search?operation=searchRetrieve&version=2.0&query=cql.serverChoice%20any%20%22strafrecht%22&maximumRecords=3&x-connection=BWB&recordSchema=oai_dc",
            "query": 'cql.serverChoice any "strafrecht"',
            "extra_info": "Current implementation with x-connection=BWB",
        },
        {
            "name": "Wetgeving.nl - Alternative 1 (Direct wetten.nl SRU)",
            "url": "https://wetten.overheid.nl/SRU/Search?operation=searchRetrieve&version=1.2&query=cql.serverChoice%20any%20%22strafrecht%22&maximumRecords=3&recordSchema=dc",
            "query": 'cql.serverChoice any "strafrecht"',
            "extra_info": "Direct wetten.nl endpoint (if exists)",
        },
        {
            "name": "Wetgeving.nl - Alternative 2 (Repository SRU with BWB collection)",
            "url": "https://repository.overheid.nl/sru?operation=searchRetrieve&version=1.2&query=cql.serverChoice%20any%20%22strafrecht%22%20AND%20dc.type%3D%22wet%22&maximumRecords=3&recordSchema=gzd",
            "query": 'cql.serverChoice any "strafrecht" AND dc.type="wet"',
            "extra_info": "Repository with type filter for laws",
        },
        # Rechtspraak.nl
        {
            "name": "Rechtspraak.nl - Current (zoeken.rechtspraak.nl/SRU/Search)",
            "url": "https://zoeken.rechtspraak.nl/SRU/Search?operation=searchRetrieve&version=1.2&query=cql.serverChoice%20any%20%22vonnis%22&maximumRecords=3&recordSchema=dc",
            "query": 'cql.serverChoice any "vonnis"',
            "extra_info": "Current implementation",
        },
        {
            "name": "Rechtspraak.nl - Alternative (zoeken.rechtspraak.nl/sru/Search)",
            "url": "https://zoeken.rechtspraak.nl/sru/Search?operation=searchRetrieve&version=1.2&query=cql.serverChoice%20any%20%22vonnis%22&maximumRecords=3&recordSchema=dc",
            "query": 'cql.serverChoice any "vonnis"',
            "extra_info": "Case-variant URL",
        },
        # Overheid.nl
        {
            "name": "Overheid.nl - Current (repository.overheid.nl)",
            "url": "https://repository.overheid.nl/sru?operation=searchRetrieve&version=1.2&query=cql.serverChoice%20any%20%22beleid%22&maximumRecords=3&recordSchema=gzd",
            "query": 'cql.serverChoice any "beleid"',
            "extra_info": "Current repository endpoint",
        },
        {
            "name": "Overheid.nl Zoekservice - Current",
            "url": "https://zoekservice.overheid.nl/sru/Search?operation=searchRetrieve&version=2.0&query=cql.serverChoice%20any%20%22beleid%22&maximumRecords=3&recordSchema=gzd",
            "query": 'cql.serverChoice any "beleid"',
            "extra_info": "Zoekservice endpoint",
        },
    ]

    results = []
    for test_case in test_cases:
        result = await test_endpoint(
            test_case["name"],
            test_case["url"],
            test_case["query"],
            test_case.get("extra_info", ""),
        )
        results.append(result)
        await asyncio.sleep(0.5)  # Rate limiting

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    working = [r for r in results if r["success"]]
    failing = [r for r in results if not r["success"]]

    print(f"\n✅ Working endpoints: {len(working)}/{len(results)}")
    for r in working:
        print(f"  - {r['name']}: {r['records']} records")

    print(f"\n❌ Failing endpoints: {len(failing)}/{len(results)}")
    for r in failing:
        print(f"  - {r['name']}: {r['error']}")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    wetgeving_working = [r for r in working if "Wetgeving.nl" in r["name"]]
    rechtspraak_working = [r for r in working if "Rechtspraak.nl" in r["name"]]

    if wetgeving_working:
        best = max(wetgeving_working, key=lambda x: x["records"])
        print("\n📌 Best Wetgeving.nl endpoint:")
        print(f"   {best['name']}")
        print(f"   URL: {best['url'].split('?')[0]}")
        print(f"   Records: {best['records']}")
    else:
        print("\n⚠️  No working Wetgeving.nl endpoint found!")
        print("   Consider:")
        print("   1. Check official documentation at wetten.nl")
        print("   2. Verify x-connection parameter requirements")
        print("   3. Try different recordSchema values (dc, oai_dc, gzd)")

    if rechtspraak_working:
        best = max(rechtspraak_working, key=lambda x: x["records"])
        print("\n📌 Best Rechtspraak.nl endpoint:")
        print(f"   {best['name']}")
        print(f"   URL: {best['url'].split('?')[0]}")
        print(f"   Records: {best['records']}")
    else:
        print("\n⚠️  No working Rechtspraak.nl endpoint found!")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
