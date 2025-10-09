#!/usr/bin/env python3
"""
Test de rechtspraak.nl zoekfunctie als alternatief voor directe scraping.
"""

from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup


def search_begrip(term: str) -> dict:
    """Zoek een begrip via de rechtspraak.nl zoekfunctie."""
    print(f"\n{'='*80}")
    print(f"Searching for: {term}")
    print(f"{'='*80}\n")

    # Verschillende zoek URL's proberen
    search_urls = [
        f"https://www.rechtspraak.nl/zoeken?zoekwoord={quote(term)}",
        f"https://www.rechtspraak.nl/SitePages/Zoeken.aspx?k={quote(term)}",
        f"https://www.rechtspraak.nl/SitePages/Search.aspx?q={quote(term)}",
    ]

    for i, url in enumerate(search_urls, 1):
        print(f"Try {i}: {url}")
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            print(f"  Status: {response.status_code}")
            print(f"  Final URL: {response.url}")

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Zoek naar zoekresultaten
                result_links = soup.find_all(
                    "a", href=lambda x: x and "juridische-begrippen" in x.lower()
                )
                print(f"  Found {len(result_links)} juridische begrippen links")

                if result_links:
                    # Neem eerste resultaat
                    first_link = result_links[0]
                    href = first_link.get("href")
                    text = first_link.get_text(strip=True)
                    full_url = urljoin("https://www.rechtspraak.nl", href)

                    print("\n✅ First result:")
                    print(f"   Title: {text}")
                    print(f"   URL: {full_url}")

                    # Probeer nu deze URL te scrapen
                    return {
                        "success": True,
                        "term": term,
                        "search_url": url,
                        "result_url": full_url,
                        "result_title": text,
                    }

                # Als geen juridische begrippen, zoek dan naar alle resultaten
                all_results = soup.find_all(
                    "a", class_=lambda x: x and "result" in " ".join(x).lower()
                )
                print(f"  Total results found: {len(all_results)}")

                # Print HTML structure voor debugging
                if len(result_links) == 0:
                    print("\n  HTML structure analysis:")
                    # Zoek naar result containers
                    result_containers = soup.find_all(
                        class_=lambda x: x
                        and any(
                            keyword in " ".join(x).lower()
                            for keyword in ["result", "search", "item"]
                        )
                    )
                    print(f"  Potential result containers: {len(result_containers)}")
                    for container in result_containers[:3]:
                        classes = " ".join(container.get("class", []))
                        print(f"    - {container.name}.{classes}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    return {"success": False, "term": term}


def analyze_search_page():
    """Analyseer de zoekpagina structuur in detail."""
    print(f"\n{'='*80}")
    print("SEARCH PAGE STRUCTURE ANALYSIS")
    print(f"{'='*80}\n")

    url = "https://www.rechtspraak.nl/zoeken?zoekwoord=onherroepelijk"
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    print(f"URL: {url}")
    print(f"Status: {response.status_code}")
    print(f"Final URL: {response.url}\n")

    # Zoek alle links
    all_links = soup.find_all("a", href=True)
    print(f"Total links: {len(all_links)}")

    # Filter juridische begrippen links
    begrippen_links = [
        link
        for link in all_links
        if "juridische-begrippen" in link.get("href", "").lower()
    ]
    print(f"Juridische begrippen links: {len(begrippen_links)}")

    if begrippen_links:
        print("\nJuridische begrippen gevonden:")
        for link in begrippen_links:
            href = link.get("href")
            text = link.get_text(strip=True)
            print(f"  - {text}")
            print(f"    {href}")

    # Zoek naar andere zoekresultaat structuren
    print("\n\nSearching for result structures:")

    # Mogelijke result selectors
    selectors = [
        ("div", {"class": lambda x: x and "result" in " ".join(x).lower()}),
        ("li", {"class": lambda x: x and "result" in " ".join(x).lower()}),
        ("div", {"class": lambda x: x and "search" in " ".join(x).lower()}),
        ("article", {}),
    ]

    for tag, attrs in selectors:
        elements = soup.find_all(tag, attrs)
        if elements:
            print(f"\nFound {len(elements)} {tag} elements")
            # Print first 3
            for el in elements[:3]:
                classes = " ".join(el.get("class", []))
                text_preview = el.get_text()[:100].replace("\n", " ")
                print(f"  {tag}.{classes}")
                print(f"    {text_preview}...")

    # Check of er JavaScript search is
    scripts = soup.find_all("script", src=True)
    search_scripts = [s for s in scripts if "search" in s.get("src", "").lower()]
    print(f"\n\nSearch-related scripts: {len(search_scripts)}")


def test_direct_page_with_context():
    """
    Test of we de begrip pagina kunnen scrapen MET JavaScript context.

    Misschien is er een pattern in de HTML dat we kunnen gebruiken.
    """
    print(f"\n{'='*80}")
    print("DIRECT PAGE WITH CONTEXT EXTRACTION")
    print(f"{'='*80}\n")

    url = "https://www.rechtspraak.nl/juridische-begrippen/Paginas/onherroepelijk.aspx"
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    # Zoek naar JSON data in de pagina (vaak gebruikt voor JS rendering)
    scripts = soup.find_all("script", type="application/json")
    print(f"JSON scripts: {len(scripts)}")
    if scripts:
        for i, script in enumerate(scripts[:3], 1):
            print(f"\nJSON script {i}:")
            content = script.string or script.get_text()
            print(content[:500])

    # Zoek naar data-* attributes met content
    elements_with_data = soup.find_all(
        attrs=lambda x: x
        and isinstance(x, dict)
        and any(k.startswith("data-") and "content" in k.lower() for k in x.keys())
    )
    print(f"\n\nElements with data-content attributes: {len(elements_with_data)}")

    # Zoek naar SharePoint hidden fields (vaak metadata)
    hidden_fields = soup.find_all("input", type="hidden")
    print(f"\nHidden fields: {len(hidden_fields)}")
    content_fields = [
        f for f in hidden_fields if "content" in f.get("name", "").lower()
    ]
    if content_fields:
        print("Content-related hidden fields:")
        for field in content_fields[:5]:
            name = field.get("name")
            value = field.get("value", "")[:100]
            print(f"  {name}: {value}...")


def main():
    """Run alle tests."""
    print("=" * 80)
    print("RECHTSPRAAK.NL SEARCH FUNCTIONALITY TEST")
    print("=" * 80)

    # Test zoeken voor verschillende termen
    test_terms = ["onherroepelijk", "cassatie", "hoger beroep"]

    results = []
    for term in test_terms:
        result = search_begrip(term)
        results.append(result)

    # Detailed analysis
    analyze_search_page()

    # Test direct extraction
    test_direct_page_with_context()

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")

    successful = [r for r in results if r.get("success")]
    print(f"Successful searches: {len(successful)}/{len(results)}")

    if successful:
        print("\n✅ Search-based approach is viable!")
        print("   Strategy:")
        print("   1. Search for term via /zoeken?zoekwoord=<term>")
        print("   2. Extract first juridische begrippen link from results")
        print("   3. Follow link to get full content")
        print("\n   Note: Content is still JS-rendered, so Selenium would be needed")
    else:
        print("\n❌ Search-based approach not viable")
        print("   Alternative needed")


if __name__ == "__main__":
    main()
