#!/usr/bin/env python3
"""
Debug script om de exacte HTML structuur van rechtspraak.nl te analyseren.

Focus op waarom div.content/ms-rtestate-field GEVONDEN wordt maar GEEN tekst bevat.
"""

import requests
from bs4 import BeautifulSoup


def analyze_html_structure(url: str):
    """Diepgaande analyse van HTML structuur."""
    print(f"Analyzing: {url}\n")

    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    # Zoek de content div
    content_div = soup.find("div", class_="ms-rtestate-field")
    print(f"Found div.ms-rtestate-field: {bool(content_div)}")

    if content_div:
        print("\nContent div attributes:")
        for attr, value in content_div.attrs.items():
            print(f"  {attr}: {value}")

        print(f"\nContent div children ({len(list(content_div.children))} total):")
        for i, child in enumerate(content_div.children, 1):
            if hasattr(child, "name"):
                print(f"  {i}. <{child.name}> - text: '{child.get_text()[:100]}'")
            else:
                text = str(child).strip()
                if text:
                    print(f"  {i}. [TEXT] - '{text[:100]}'")

        print("\nFull content div HTML (first 1000 chars):")
        print(content_div.prettify()[:1000])

    # Zoek naar JavaScript-rendered content indicatoren
    print(f"\n{'='*80}")
    print("JAVASCRIPT INDICATORS")
    print(f"{'='*80}")

    scripts = soup.find_all("script")
    print(f"Total script tags: {len(scripts)}")

    # Zoek naar SharePoint specifieke markers
    sharepoint_markers = soup.find_all(string=lambda x: x and "SharePoint" in x)
    print(f"SharePoint references: {len(sharepoint_markers)}")

    # Zoek naar data-attributes die client-side rendering suggereren
    data_attrs = []
    for element in soup.find_all():
        if hasattr(element, "attrs") and isinstance(element.attrs, dict):
            if any(k.startswith("data-") for k in element.attrs):
                data_attrs.append(element)
    print(f"Elements with data-* attributes: {len(data_attrs)}")

    # Check voor React/Angular/Vue markers
    react_markers = soup.find_all(attrs={"data-reactroot": True}) or soup.find_all(
        attrs={"data-react-checksum": True}
    )
    angular_markers = soup.find_all(attrs={"ng-app": True}) or soup.find_all(
        attrs={"ng-controller": True}
    )
    vue_markers = soup.find_all(attrs={"v-app": True})

    print(f"React markers: {len(react_markers)}")
    print(f"Angular markers: {len(angular_markers)}")
    print(f"Vue markers: {len(vue_markers)}")

    # Zoek naar "loading" indicatoren
    loading_divs = soup.find_all(
        "div", class_=lambda x: x and "loading" in " ".join(x).lower()
    )
    print(f"Loading divs: {len(loading_divs)}")
    if loading_divs:
        print(
            "Loading div classes:",
            [" ".join(div.get("class", [])) for div in loading_divs[:3]],
        )

    # Check of de content div ID/classes heeft die JS targets
    print(f"\n{'='*80}")
    print("POTENTIAL JS TARGETS")
    print(f"{'='*80}")

    # Zoek alle divs met IDs
    divs_with_id = soup.find_all("div", id=True)
    print(f"Divs with ID attributes: {len(divs_with_id)}")
    for div in divs_with_id[:10]:
        div_id = div.get("id")
        div_classes = " ".join(div.get("class", []))
        has_content = len(div.get_text(strip=True)) > 50
        print(f"  #{div_id} (.{div_classes}) - has_content: {has_content}")

    # Zoek naar WebPart specifieke elementen (SharePoint)
    webparts = soup.find_all(class_=lambda x: x and "webpart" in " ".join(x).lower())
    print(f"\nWebPart elements: {len(webparts)}")
    for wp in webparts[:5]:
        wp_classes = " ".join(wp.get("class", []))
        wp_id = wp.get("id", "no-id")
        print(f"  #{wp_id} (.{wp_classes})")

    # Zoek naar de headtitle - die werkt WEL
    headtitle = soup.find("div", class_="headtitle")
    if headtitle:
        print(f"\n✅ Headtitle found: {headtitle.get_text(strip=True)}")
        print("   This proves static content IS present in HTML")

    # Check for noscript fallback
    noscript = soup.find_all("noscript")
    print(f"\nNoScript tags: {len(noscript)}")
    if noscript:
        for ns in noscript[:3]:
            print(f"  Content: {ns.get_text()[:100]}")


def check_alternative_selectors(url: str):
    """Test alternatieve selector strategieën."""
    print(f"\n{'='*80}")
    print("ALTERNATIVE SELECTOR TESTS")
    print(f"{'='*80}\n")

    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    selectors = [
        ("div.ms-rtestate-field", soup.find("div", class_="ms-rtestate-field")),
        (
            "div[id*='content']",
            soup.find("div", id=lambda x: x and "content" in x.lower()),
        ),
        (
            "div[class*='content']",
            soup.find("div", class_=lambda x: x and "content" in " ".join(x).lower()),
        ),
        ("div.ms-WPBody", soup.find("div", class_="ms-WPBody")),
        ("div.ms-webpart-chrome", soup.find("div", class_="ms-webpart-chrome")),
        (".rs-wrapper", soup.select_one(".rs-wrapper")),
    ]

    for selector, element in selectors:
        if element:
            text = element.get_text(strip=True)
            print(f"✅ {selector}")
            print(f"   Text length: {len(text)} chars")
            print(f"   Preview: {text[:150]}...")
        else:
            print(f"❌ {selector} - not found")


def main():
    """Run full analysis."""
    url = "https://www.rechtspraak.nl/juridische-begrippen/Paginas/onherroepelijk.aspx"

    analyze_html_structure(url)
    check_alternative_selectors(url)

    print(f"\n{'='*80}")
    print("CONCLUSION")
    print(f"{'='*80}")
    print("\nDe div.ms-rtestate-field bestaat WEL, maar bevat GEEN statische content.")
    print("Dit is een klassiek SharePoint Server-Side Rendering (SSR) probleem:")
    print("  - Content wordt via JavaScript/SharePoint Web Services geladen")
    print("  - BeautifulSoup kan alleen statische HTML parsen")
    print("  - Selenium/Playwright nodig voor client-side rendered content")


if __name__ == "__main__":
    main()
