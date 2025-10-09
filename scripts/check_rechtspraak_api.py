#!/usr/bin/env python3
"""
Check of rechtspraak.nl een API heeft of alternatieve toegang biedt.

Test:
1. robots.txt - voor scraping policy
2. sitemap.xml - voor data structuur
3. Zoek functionaliteit - mogelijk API achter de schermen
4. SharePoint REST API endpoints
"""

from urllib.parse import urljoin

import requests


def check_robots_txt(base_url: str):
    """Check robots.txt voor scraping policy."""
    print(f"\n{'='*80}")
    print("ROBOTS.TXT CHECK")
    print(f"{'='*80}\n")

    url = urljoin(base_url, "/robots.txt")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ robots.txt found\n")
            print(response.text[:1000])
            print("\n...")

            # Check for specific restrictions
            lines = response.text.lower().split("\n")
            restricted = [
                line
                for line in lines
                if "disallow" in line and "juridische-begrippen" in line
            ]
            if restricted:
                print("\n⚠️  Juridische begrippen explicitly disallowed:")
                for line in restricted:
                    print(f"   {line}")
            else:
                print("\n✅ No explicit disallow for juridische-begrippen")

        else:
            print(f"❌ No robots.txt (HTTP {response.status_code})")
    except Exception as e:
        print(f"❌ Error: {e}")


def check_sitemap(base_url: str):
    """Check sitemap.xml."""
    print(f"\n{'='*80}")
    print("SITEMAP CHECK")
    print(f"{'='*80}\n")

    for path in ["/sitemap.xml", "/sitemap_index.xml", "/sitemap"]:
        url = urljoin(base_url, path)
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Found: {path}")
                # Check if it contains juridische-begrippen
                if "juridische-begrippen" in response.text.lower():
                    print("   Contains juridische-begrippen entries")
                    # Count entries
                    count = response.text.lower().count("juridische-begrippen")
                    print(f"   Entries: ~{count}")
                else:
                    print("   No juridische-begrippen found")
                return True
        except Exception:
            continue

    print("❌ No sitemap found")
    return False


def check_sharepoint_rest_api(base_url: str):
    """Check SharePoint REST API endpoints."""
    print(f"\n{'='*80}")
    print("SHAREPOINT REST API CHECK")
    print(f"{'='*80}\n")

    endpoints = [
        "/_api/web",
        "/_api/lists",
        "/_api/web/lists/getbytitle('Juridische Begrippen')",
        "/_vti_bin/listdata.svc",
    ]

    for endpoint in endpoints:
        url = urljoin(base_url, endpoint)
        try:
            response = requests.get(
                url, headers={"Accept": "application/json;odata=verbose"}, timeout=10
            )
            print(f"Testing: {endpoint}")
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print("  ✅ API accessible!")
                print(f"  Content-Type: {response.headers.get('Content-Type')}")
                print(f"  Size: {len(response.text)} bytes")
                return True
            elif response.status_code == 401:
                print("  ⚠️  Authentication required")
            elif response.status_code == 403:
                print("  ❌ Forbidden")
            else:
                print("  ❌ Not accessible")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    return False


def check_search_functionality(base_url: str):
    """Check of er een zoek API bestaat."""
    print(f"\n{'='*80}")
    print("SEARCH API CHECK")
    print(f"{'='*80}\n")

    # SharePoint search endpoints
    search_endpoints = [
        "/_api/search/query?querytext='onherroepelijk'",
        "/zoeken?zoekwoord=onherroepelijk",
        "/_layouts/15/osssearchresults.aspx?k=onherroepelijk",
    ]

    for endpoint in search_endpoints:
        url = urljoin(base_url, endpoint)
        try:
            response = requests.get(
                url,
                headers={"Accept": "application/json"},
                timeout=10,
                allow_redirects=True,
            )
            print(f"Testing: {endpoint}")
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                # Check if contains results
                if "onherroepelijk" in response.text.lower():
                    print("  ✅ Search works! Found results")
                    return True
                else:
                    print("  ⚠️  Endpoint works but no results")
            else:
                print(f"  ❌ Status {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    return False


def check_direct_content_api():
    """Check of de begrippen als JSON beschikbaar zijn."""
    print(f"\n{'='*80}")
    print("DIRECT CONTENT API CHECK")
    print(f"{'='*80}\n")

    # Probeer verschillende formaten
    base = "https://www.rechtspraak.nl/juridische-begrippen/Paginas/onherroepelijk"
    variants = [
        f"{base}.json",
        f"{base}.xml",
        f"{base}.aspx?format=json",
        f"{base}.aspx?output=json",
    ]

    for url in variants:
        try:
            response = requests.get(url, timeout=10)
            print(f"Testing: {url}")
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                print(f"  Content-Type: {content_type}")
                if "json" in content_type or "xml" in content_type:
                    print("  ✅ Structured data available!")
                    return True
        except Exception:
            continue

    print("❌ No structured data endpoints found")
    return False


def main():
    """Run all checks."""
    base_url = "https://www.rechtspraak.nl"

    print("=" * 80)
    print("RECHTSPRAAK.NL API & SCRAPING POLICY ANALYSIS")
    print("=" * 80)

    check_robots_txt(base_url)
    check_sitemap(base_url)
    has_api = check_sharepoint_rest_api(base_url)
    has_search = check_search_functionality(base_url)
    has_structured = check_direct_content_api()

    # Final recommendation
    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}\n")

    if has_api or has_structured:
        print("✅ API ACCESS AVAILABLE")
        print("   Use SharePoint REST API or structured data endpoints")
    elif has_search:
        print("⚠️  SEARCH API AVAILABLE")
        print("   Can use search but may not be reliable for all terms")
    else:
        print("❌ NO API FOUND")
        print("   Options:")
        print("   1. Contact rechtspraak.nl for data export/API access")
        print("   2. Use Selenium/Playwright for browser automation")
        print("   3. Use alternative sources (Wikipedia, Overheid.nl)")


if __name__ == "__main__":
    main()
