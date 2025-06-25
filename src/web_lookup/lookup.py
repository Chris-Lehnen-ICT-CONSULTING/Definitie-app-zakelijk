# web_lookup.py

# ────────────────────────────────────────────────────────────────────────
# Bibliotheken voor HTTP-verzoeken, HTML-parsing en XML-verwerking
# ────────────────────────────────────────────────────────────────────────
import os
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# ────────────────────────────────────────────────────────────────────────
# Functie: definities ophalen van Wikipedia (eerste paragraaf)
# ────────────────────────────────────────────────────────────────────────
def zoek_definitie_op_wikipedia(begrip: str) -> str:
    """
    Vraagt de Nederlandstalige Wikipedia-pagina op voor 'begrip'
    en retourneert de eerste alinea als definitie.
    """
    zoekterm = begrip.replace(" ", "_")
    url = f"https://nl.wikipedia.org/wiki/{zoekterm}"
    try:
        r = requests.get(url, timeout=5)
        # Als de pagina gevonden is, parse de HTML
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            eerste_paragraaf = soup.find("p")
            # Controleer of de paragraaf niet leeg is
            if eerste_paragraaf and eerste_paragraaf.text.strip():
                return eerste_paragraaf.text.strip()
            # Fallback bij lege alinea
            return "⚠️ Geen duidelijke definitie gevonden op Wikipedia."
        # Foutmelding bij andere HTTP-status
        return f"⚠️ Wikipedia gaf statuscode {r.status_code}"
    except Exception as e:
        # Netwerk- of parsefout
        return f"❌ Fout bij ophalen van Wikipedia: {e}"

# ────────────────────────────────────────────────────────────────────────
# Functie: placeholder voor bredere websearch (nog niet geïmplementeerd)
# ────────────────────────────────────────────────────────────────────────
def zoek_definitie_via_websearch(begrip: str) -> str:
    """
    Stubfunctie: toont dat we hier later een echte websearch kunnen doen
    (bv. via SerpAPI of een andere zoek-API).
    """
    return f"(🔍 Zoeken op web naar: '{begrip}' — deze functie is nog niet geïmplementeerd)"

# ────────────────────────────────────────────────────────────────────────
# Functie: definities ophalen via Overheid.nl SRU-zoekservice
# ────────────────────────────────────────────────────────────────────────
def zoek_definitie_op_overheidnl(begrip: str) -> str:
    """
    Vraagt Overheid.nl SRU API aan met 'begrip' in de titel
    en retourneert titel + eerste alinea van de gevonden publicatie.
    """
    zoekterm = begrip.replace(" ", "%20")
    url = f"https://zoekservice.overheid.nl/sru/Search?query=title={zoekterm}&maximumRecords=1"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return f"⚠️ Overheid.nl gaf statuscode {response.status_code}"

        # Parse XML-response
        root = ET.fromstring(response.content)
        record = root.find(".//{http://www.loc.gov/zing/srw/}recordData")
        if record is None:
            return "⚠️ Geen resultaten via Overheid.nl API."

        # Haal titel en link naar detailpagina op
        title_el = record.find(".//{http://purl.org/dc/elements/1.1/}title")
        id_el = record.find(".//{http://purl.org/dc/elements/1.1/}identifier")
        link = id_el.text if id_el is not None else None

        detail_tekst = ""
        if link:
            # Probeert detailpagina te scrapen voor extra info
            try:
                detail_resp = requests.get(link, timeout=5)
                detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
                content = detail_soup.select_one("main")
                if content:
                    paragrafen = content.find_all("p")
                    eerste_alinea = paragrafen[0].get_text(strip=True) if paragrafen else ""
                    # Beperk tot 400 tekens
                    detail_tekst = eerste_alinea[:400]
            except Exception:
                detail_tekst = "(geen extra informatie opgehaald van detailpagina)"

        return (
            f"Titel: {title_el.text if title_el is not None else '(titel onbekend)'}\n"
            f"Details: {detail_tekst}...\n"
            f"(bron: Overheid.nl)"
        )
    except Exception as e:
        return f"❌ Fout bij ophalen van Overheid.nl: {e}"

# ────────────────────────────────────────────────────────────────────────
# Functie: combinatieresultaat Wikipedia + Overheid.nl
# ────────────────────────────────────────────────────────────────────────
def zoek_definitie_combinatie(begrip: str) -> str:
    """
    Levert zowel Wikipedia- als Overheid.nl-resultaat in één string.
    """
    wiki = zoek_definitie_op_wikipedia(begrip)
    overheid = zoek_definitie_op_overheidnl(begrip)
    return f"📚 Wikipedia: {wiki}\n\n📘 Overheid.nl:\n{overheid}"

# ────────────────────────────────────────────────────────────────────────
# Plurale-tantum check: Wiktionary → Wikipedia
# ────────────────────────────────────────────────────────────────────────
def is_plurale_tantum(term: str) -> bool:
    """
    Controleert of 'term' alleen in het meervoud voorkomt door:
      1) UniMorph offline (Number=Sing check) → als enkelvoud bestaat → False
      2) Scrapen lead-paragrafen van Wiktionary (tot de eerste <h2>)
      3) Fallback: Wikipedia-heuristiek
      4) Uitgebreide trefwoorden ‘alleen in het meervoud’, ‘alleen meervoud’, ‘plurale tantum’
    """

    # 2) Wiktionary lead scraping
    wiki_url = f"https://nl.wiktionary.org/wiki/{term.capitalize()}"
    try:
        resp = requests.get(wiki_url, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        lead = []
        for elem in soup.select("div.mw-parser-output > *"):
            if elem.name == "h2":
                break
            if elem.name == "p":
                lead.append(elem.get_text().lower())
        text = " ".join(lead)
        if any(kw in text for kw in ("alleen in het meervoud", "alleen meervoud", "plurale tantum")):
            return True
    except Exception:
        pass

    # 3) Fallback Wikipedia
    wp_url = f"https://nl.wikipedia.org/wiki/{term.capitalize()}"
    try:
        resp = requests.get(wp_url, timeout=5)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            eerste_p = soup.find("p")
            text = eerste_p.get_text().lower() if eerste_p else ""
            if any(kw in text for kw in ("alleen in het meervoud", "alleen meervoud", "plurale tantum")):
                return True
    except Exception:
        pass

    return False