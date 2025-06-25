# web_lookup.py
import os
import csv
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# ✅ Wikipedia: haal eerste paragraaf op

def zoek_definitie_op_wikipedia(begrip):
    zoekterm = begrip.replace(" ", "_")
    url = f"https://nl.wikipedia.org/wiki/{zoekterm}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            eerste_paragraaf = soup.find("p")
            if eerste_paragraaf and eerste_paragraaf.text.strip():
                return eerste_paragraaf.text.strip()
            else:
                return "⚠️ Geen duidelijke definitie gevonden op Wikipedia."
        else:
            return f"⚠️ Wikipedia gaf statuscode {r.status_code}"
    except Exception as e:
        return f"❌ Fout bij ophalen van Wikipedia: {e}"

# 🔧 Placeholder voor bredere webzoekopdracht (bijv. Serper, SerpAPI, Bing)
def zoek_definitie_via_websearch(begrip):
    return f"(🔍 Zoeken op web naar: '{begrip}' — deze functie is nog niet geïmplementeerd)"

# ✅ Hybride lookup: overheid.nl API + optionele scraping

def zoek_definitie_op_overheidnl(begrip):
    zoekterm = begrip.replace(" ", "%20")
    url = f"https://zoekservice.overheid.nl/sru/Search?query=title={zoekterm}&maximumRecords=1"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return f"⚠️ Overheid.nl gaf statuscode {response.status_code}"

        root = ET.fromstring(response.content)
        record = root.find(".//{http://www.loc.gov/zing/srw/}recordData")
        if record is None:
            return "⚠️ Geen resultaten via Overheid.nl API."

        metadata = record.find(".//{http://purl.org/dc/elements/1.1/}title")
        title = metadata.text if metadata is not None else "(titel onbekend)"

        identifier = record.find(".//{http://purl.org/dc/elements/1.1/}identifier")
        link = identifier.text if identifier is not None else None

        detail_tekst = ""
        if link:
            try:
                detail_response = requests.get(link, timeout=5)
                detail_soup = BeautifulSoup(detail_response.text, "html.parser")
                content = detail_soup.select_one("main")
                if content:
                    paragrafen = content.find_all("p")
                    eerste_alinea = paragrafen[0].get_text(strip=True) if paragrafen else ""
                    detail_tekst = eerste_alinea[:400]
            except Exception:
                detail_tekst = "(geen extra informatie opgehaald van detailpagina)"

        return (
            f"Titel: {title}\n"
            f"Details: {detail_tekst}...\n"
            f"(bron: Overheid.nl)"
        )

    except Exception as e:
        return f"❌ Fout bij ophalen van Overheid.nl: {e}"

# ✅ Combinatiefunctie: Wikipedia + Overheid.nl combineren

def zoek_definitie_combinatie(begrip):
    wiki = zoek_definitie_op_wikipedia(begrip)
    overheid = zoek_definitie_op_overheidnl(begrip)
    return f"📚 Wikipedia: {wiki}\n\n📘 Overheid.nl:\n{overheid}"

# ────────────────────────────────────────────────────────────────────────
#  Plurale-tantum check: UniMorph offline → Wiktionary API → Wikipedia HTML
# ────────────────────────────────────────────────────────────────────────

_UNIMORPH_PATH = os.path.join(os.path.dirname(__file__), "data", "unimorph_nl.tsv")

def _has_singular_unimorph(term: str) -> bool:
    if not os.path.exists(_UNIMORPH_PATH):
        return False
    term_lc = term.lower()
    try:
        with open(_UNIMORPH_PATH, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for lemma, form, feats in reader:
                if lemma.lower() == term_lc and "Number=Sing" in feats:
                    return True
    except Exception:
        pass
    return False

def _is_plurale_tantum_wiktionary(term: str) -> bool:
    api_url = "https://nl.wiktionary.org/w/api.php"
    params = {
        "action": "parse",
        "page": term.capitalize(),
        "prop": "categories",
        "format": "json",
    }
    try:
        resp = requests.get(api_url, params=params, timeout=5)
        resp.raise_for_status()
        cats = resp.json().get("parse", {}).get("categories", [])
        return any("Plurale tantum" in c.get("*", "") for c in cats)
    except Exception:
        return False

def is_plurale_tantum(term: str) -> bool:
    # 1) Offline UniMorph
    if _has_singular_unimorph(term):
        return False
    # 2) Wiktionary-API
    if _is_plurale_tantum_wiktionary(term):
        return True
    # 3) Fallback Wikipedia HTML
    url = f"https://nl.wikipedia.org/wiki/{term.capitalize()}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            p = soup.find("p")
            text = (p.get_text() or "").lower()
            return "alleen in het meervoud" in text or "plurale tantum" in text
    except Exception:
        pass
    return False