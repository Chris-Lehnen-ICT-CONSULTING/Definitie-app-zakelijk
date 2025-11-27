#!/usr/bin/env python3
"""
Test script voor rechtspraak.nl begrippen scraping.

Test de HTML structuur en parsing strategie voor juridische begrippen.
"""

import time
from typing import Optional

import requests
from bs4 import BeautifulSoup


def test_begrip_url(term: str, url: str) -> dict:
    """Test één begrip URL en return de resultaten."""
    print(f"\n{'='*80}")
    print(f"Testing: {term}")
    print(f"URL: {url}")
    print(f"{'='*80}")

    start = time.time()

    try:
        response = requests.get(url, timeout=10)
        elapsed = time.time() - start

        result = {
            "term": term,
            "url": url,
            "status_code": response.status_code,
            "response_time_ms": int(elapsed * 1000),
            "success": response.status_code == 200,
            "error": None,
            "html_structure": {},
            "parsed_content": {},
        }

        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}"
            print(f"❌ FAILED: HTTP {response.status_code}")
            return result

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Test verschillende selector strategieën
        print(f"\n✅ Response received ({elapsed:.2f}s)")
        print(f"HTML size: {len(response.text)} bytes")

        # 1. Test voorgestelde selectors
        content_div = soup.find("div", class_=["content", "ms-rtestate-field"])
        print(f"\nTest 1 - div.content/ms-rtestate-field: {bool(content_div)}")

        # 2. Test alternatieve selectors
        main_content = soup.find("main")
        article = soup.find("article")
        print(f"Test 2 - main tag: {bool(main_content)}")
        print(f"Test 3 - article tag: {bool(article)}")

        # 3. Zoek alle divs met class attributes
        print("\nAll divs with classes (first 20):")
        divs_with_class = soup.find_all("div", class_=True)[:20]
        for div in divs_with_class:
            classes = " ".join(div.get("class", []))
            text_preview = div.get_text()[:80].strip().replace("\n", " ")
            print(f"  - div.{classes}: {text_preview}...")

        # 4. Zoek content-gerelateerde divs
        print("\nSearching for content-related divs:")
        content_candidates = soup.find_all(
            "div",
            class_=lambda x: x
            and any(
                keyword in " ".join(x).lower()
                for keyword in ["content", "body", "text", "artikel", "page", "main"]
            ),
        )
        print(f"Found {len(content_candidates)} content candidates")
        for i, candidate in enumerate(content_candidates[:5], 1):
            classes = " ".join(candidate.get("class", []))
            text_preview = candidate.get_text()[:100].strip().replace("\n", " ")
            print(f"  {i}. div.{classes}")
            print(f"     Text: {text_preview}...")

        # 5. Haal definitie tekst op (beste poging)
        definition_text = None
        definition_source = None

        if content_div:
            definition_text = content_div.get_text(strip=True)
            definition_source = "div.content/ms-rtestate-field"
        elif content_candidates:
            # Neem de grootste content div
            best_candidate = max(content_candidates, key=lambda x: len(x.get_text()))
            definition_text = best_candidate.get_text(strip=True)
            definition_source = f"div.{' '.join(best_candidate.get('class', []))}"
        elif main_content:
            definition_text = main_content.get_text(strip=True)
            definition_source = "main"
        elif article:
            definition_text = article.get_text(strip=True)
            definition_source = "article"

        if definition_text:
            print(f"\n📝 Definition extracted from: {definition_source}")
            print(f"Length: {len(definition_text)} characters")
            print(f"Preview: {definition_text[:300]}...")

            result["parsed_content"]["definition"] = definition_text[
                :500
            ]  # First 500 chars
            result["parsed_content"]["full_length"] = len(definition_text)
            result["parsed_content"]["source_selector"] = definition_source
        else:
            print("\n❌ No definition text found!")
            result["error"] = "No definition text found"

        # 6. Zoek gerelateerde begrippen
        links = soup.find_all(
            "a", href=lambda x: x and "juridische-begrippen" in x.lower()
        )
        print(f"\n🔗 Related terms found: {len(links)}")
        if links:
            related_terms = [link.get_text(strip=True) for link in links[:5]]
            print(f"Examples: {', '.join(related_terms)}")
            result["parsed_content"]["related_terms"] = related_terms

        # Store HTML structure info
        result["html_structure"] = {
            "has_content_div": bool(content_div),
            "has_main": bool(main_content),
            "has_article": bool(article),
            "num_content_candidates": len(content_candidates),
            "num_related_links": len(links),
        }

        return result

    except requests.Timeout:
        elapsed = time.time() - start
        print(f"❌ TIMEOUT after {elapsed:.2f}s")
        return {
            "term": term,
            "url": url,
            "success": False,
            "error": "Timeout",
            "response_time_ms": int(elapsed * 1000),
        }
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ ERROR: {e}")
        return {
            "term": term,
            "url": url,
            "success": False,
            "error": str(e),
            "response_time_ms": int(elapsed * 1000),
        }


def test_direct_url_construction(term: str) -> dict:
    """Test of directe URL constructie werkt."""
    formatted_term = term.lower().replace(" ", "-")
    url = (
        f"https://www.rechtspraak.nl/juridische-begrippen/Paginas/{formatted_term}.aspx"
    )
    return test_begrip_url(term, url)


def main():
    """Test de drie voorgestelde begrippen."""
    test_cases = [
        (
            "onherroepelijk",
            "https://www.rechtspraak.nl/juridische-begrippen/Paginas/onherroepelijk.aspx",
        ),
        (
            "cassatie",
            "https://www.rechtspraak.nl/juridische-begrippen/Paginas/cassatie.aspx",
        ),
        (
            "hoger beroep",
            "https://www.rechtspraak.nl/juridische-begrippen/Paginas/hoger-beroep.aspx",
        ),
    ]

    results = []

    print("=" * 80)
    print("RECHTSPRAAK.NL BEGRIPPEN SCRAPING TEST")
    print("=" * 80)

    for term, url in test_cases:
        result = test_begrip_url(term, url)
        results.append(result)
        time.sleep(1)  # Be nice to the server

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"\nTotal tests: {len(results)}")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")

    if successful:
        avg_time = sum(r["response_time_ms"] for r in successful) / len(successful)
        print(f"\nAverage response time: {avg_time:.0f}ms")

    # Detailed results
    print("\nDetailed Results:")
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"\n{status} {r['term']}")
        print(f"   Status: {r.get('status_code', 'N/A')}")
        print(f"   Time: {r['response_time_ms']}ms")
        if r.get("error"):
            print(f"   Error: {r['error']}")
        if r.get("parsed_content", {}).get("source_selector"):
            print(f"   Selector: {r['parsed_content']['source_selector']}")
            print(f"   Text length: {r['parsed_content'].get('full_length', 0)} chars")

    # Test URL constructie strategie
    print("\n" + "=" * 80)
    print("TESTING URL CONSTRUCTION STRATEGY")
    print("=" * 80)

    print("\nTest case: 'hoger beroep' → 'hoger-beroep.aspx'")
    result = test_direct_url_construction("hoger beroep")
    if result["success"]:
        print("✅ Direct URL construction works!")
    else:
        print("❌ Direct URL construction failed")
        print("   Would need fallback to search")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    if len(successful) == len(results):
        print("\n✅ All tests passed!")
        print("   - HTML parsing is feasible")
        print("   - Direct URL construction works")
        print("   - Selectors need to be finalized based on findings")
    elif len(successful) > 0:
        print(f"\n⚠️  Partial success ({len(successful)}/{len(results)})")
        print("   - Some begrippen are accessible")
        print("   - Need fallback strategy for failures")
    else:
        print("\n❌ All tests failed")
        print("   - Scraping may not be viable")
        print("   - Consider alternative approaches")

    return results


if __name__ == "__main__":
    main()
