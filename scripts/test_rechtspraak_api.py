#!/usr/bin/env python3
"""
Test Rechtspraak.nl API endpoints om te bepalen wat werkt.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import aiohttp
except ImportError:
    print("ERROR: aiohttp niet geïnstalleerd. Run: pip install aiohttp")
    sys.exit(1)


async def test_endpoint(name: str, url: str) -> dict:
    """Test een endpoint."""
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*80}")

    result = {
        "name": name,
        "url": url,
        "success": False,
        "status": None,
        "error": None,
        "response_preview": None,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                result["status"] = resp.status
                text = await resp.text()
                result["response_preview"] = text[:500]

                print(f"Status: {resp.status}")

                if resp.status == 200:
                    result["success"] = True
                    print("✅ SUCCESS")
                    print(f"Response preview: {text[:200]}")
                else:
                    result["error"] = f"HTTP {resp.status}"
                    print(f"❌ HTTP {resp.status}")
                    print(f"Response preview: {text[:200]}")

    except TimeoutError:
        result["error"] = "Timeout"
        print("❌ TIMEOUT")
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ ERROR: {e}")

    return result


async def main():
    """Test Rechtspraak.nl endpoints."""
    print("=" * 80)
    print("RECHTSPRAAK.NL API ENDPOINT VERIFICATION")
    print("=" * 80)

    # Test ECLI voor een bekende uitspraak
    ecli = "ECLI:NL:RBAMS:2023:3197"

    test_cases = [
        {
            "name": "data.rechtspraak.nl - ECLI Content",
            "url": f"https://data.rechtspraak.nl/uitspraken/content?id={ecli}",
        },
        {
            "name": "data.rechtspraak.nl - ECLI Content with META",
            "url": f"https://data.rechtspraak.nl/uitspraken/content?id={ecli}&return=META",
        },
        {
            "name": "data.rechtspraak.nl - ECLI Content with DOC",
            "url": f"https://data.rechtspraak.nl/uitspraken/content?id={ecli}&return=DOC",
        },
        {
            "name": "uitspraken.rechtspraak.nl - Deep link",
            "url": f"https://uitspraken.rechtspraak.nl/#!/details?id={ecli}",
        },
    ]

    results = []
    for test_case in test_cases:
        result = await test_endpoint(test_case["name"], test_case["url"])
        results.append(result)
        await asyncio.sleep(0.5)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    working = [r for r in results if r["success"]]
    failing = [r for r in results if not r["success"]]

    print(f"\n✅ Working endpoints: {len(working)}/{len(results)}")
    for r in working:
        print(f"  - {r['name']}")

    print(f"\n❌ Failing endpoints: {len(failing)}/{len(results)}")
    for r in failing:
        print(f"  - {r['name']}: {r['error']}")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    if working:
        print("\n📌 Use REST API for Rechtspraak.nl:")
        print("   Base URL: https://data.rechtspraak.nl/uitspraken/content")
        print("   Query pattern: ?id=<ECLI>&return=META")
        print("   Note: SRU search appears to be unavailable/deprecated")
    else:
        print("\n⚠️  No working Rechtspraak.nl endpoints found!")
        print("   Possible issues:")
        print("   - Network connectivity")
        print("   - ECLI no longer exists")
        print("   - API endpoints changed")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
