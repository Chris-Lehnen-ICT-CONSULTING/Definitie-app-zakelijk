# ─────────────────────────────────────────────────────────────────────────────
# 🔍 Clusteranalyse bronnen (Lookup-Clusteranalyse – 2025-07-04)
# Doel: classificatie van bronnen op implementatiecomplexiteit
# Categorie 1: Eenvoudig te implementeren (Quick Wins)
#  • Wikipedia (MediaWiki API)
#  • Wiktionary (MediaWiki API of wiktionaryparser)
#  • Ensie.nl (eenvoudige HTML)
#  • Overheid.nl / Wetten.nl (gestructureerde HTML)
#  • Strafrechtketen.nl (eenvoudige structuur)
#  • IATE (downloadbare dataset)
#  • Kamerstukken.nl (semi-gestructureerde HTML)
# Deze bronnen vormen fase 1 van het roadmapplan (Sprint 1)
#
# Latere clusters (matig complex, complex) volgen in roadmapdocumentatie.
# Deze analyse is leidend voor prioritering en PO-besluitvorming.
# ─────────────────────────────────────────────────────────────────────────────
# web_lookup.py

# ────────────────────────────────────────────────────────────────────────
# Bibliotheken voor HTTP-verzoeken, HTML-parsing en XML-verwerking
# ────────────────────────────────────────────────────────────────────────
import os
import json
import requests
from typing import Optional
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
# Functie: definities ophalen van Wiktionary (MediaWiki API)
# ────────────────────────────────────────────────────────────────────────
def zoek_definitie_op_wiktionary(begrip: str) -> str:
    """
    Vraagt de Nederlandstalige Wiktionary API aan voor 'begrip'
    en retourneert de eerste definitie van het lemma.
    """
    zoekterm = begrip.replace(" ", "_")
    url = f"https://nl.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "exintro": True,
        "titles": zoekterm,
        "redirects": 1,
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page in pages.items():
                extract = page.get("extract", "")
                if extract:
                    # Strip HTML tags
                    soup = BeautifulSoup(extract, "html.parser")
                    text = soup.get_text(separator="\n").strip()
                    if text:
                        return text
            return "⚠️ Geen duidelijke definitie gevonden op Wiktionary."
        return f"⚠️ Wiktionary gaf statuscode {r.status_code}"
    except Exception as e:
        return f"❌ Fout bij ophalen van Wiktionary: {e}"

# ────────────────────────────────────────────────────────────────────────
# Functie: definities ophalen van Ensie.nl (eenvoudige HTML)
# ────────────────────────────────────────────────────────────────────────
def zoek_definitie_op_ensie(begrip: str) -> str:
    """
    Scrape de Ensie.nl pagina voor 'begrip' en retourneert de eerste alinea.
    """
    zoekterm = begrip.replace(" ", "-")
    url = f"https://www.ensie.nl/definitie/{zoekterm}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # De definitie staat vaak in <div class="definition"> of eerste <p> in main
            div_def = soup.find("div", class_="definition")
            if div_def and div_def.text.strip():
                return div_def.text.strip()
            main = soup.find("main")
            if main:
                p = main.find("p")
                if p and p.text.strip():
                    return p.text.strip()
            return "⚠️ Geen duidelijke definitie gevonden op Ensie.nl."
        return f"⚠️ Ensie.nl gaf statuscode {r.status_code}"
    except Exception as e:
        return f"❌ Fout bij ophalen van Ensie.nl: {e}"

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
# Functie: definities ophalen van Strafrechtketen.nl (eenvoudige structuur)
# ────────────────────────────────────────────────────────────────────────
def zoek_definitie_op_strafrechtketen(begrip: str) -> str:
    """
    Scrape Strafrechtketen.nl voor 'begrip' en retourneert de eerste alinea.
    """
    zoekterm = begrip.replace(" ", "-").lower()
    url = f"https://www.strafrechtketen.nl/kennisbank/definities/{zoekterm}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # Zoek eerste <p> binnen main of content div
            main = soup.find("main") or soup.find("div", class_="content")
            if main:
                p = main.find("p")
                if p and p.text.strip():
                    return p.text.strip()
            return "⚠️ Geen duidelijke definitie gevonden op Strafrechtketen.nl."
        return f"⚠️ Strafrechtketen.nl gaf statuscode {r.status_code}"
    except Exception as e:
        return f"❌ Fout bij ophalen van Strafrechtketen.nl: {e}"

# ────────────────────────────────────────────────────────────────────────
# Functie: definities ophalen van Kamerstukken.nl (semi-gestructureerde HTML)
# ────────────────────────────────────────────────────────────────────────
def zoek_definitie_op_kamerstukken(begrip: str) -> str:
    """
    Scrape Kamerstukken.nl voor 'begrip' en retourneert de eerste alinea.
    """
    zoekterm = begrip.replace(" ", "+")
    url = f"https://www.kamerstukken.nl/search?k={zoekterm}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # Zoek eerste resultaat en pak eerste alinea van samenvatting
            result = soup.find("div", class_="search-result")
            if result:
                summary = result.find("p")
                if summary and summary.text.strip():
                    return summary.text.strip()
            return "⚠️ Geen duidelijke definitie gevonden op Kamerstukken.nl."
        return f"⚠️ Kamerstukken.nl gaf statuscode {r.status_code}"
    except Exception as e:
        return f"❌ Fout bij ophalen van Kamerstukken.nl: {e}"

# ────────────────────────────────────────────────────────────────────────
# Functie: definities ophalen van IATE (downloadbare dataset)
# ────────────────────────────────────────────────────────────────────────
def zoek_definitie_op_iate(begrip: str) -> str:
    """
    Stubfunctie voor IATE: omdat IATE dataset gedownload moet worden,
    hier een placeholder die aangeeft dat deze bron nog niet geïmplementeerd is.
    """
    return "(ℹ️ IATE-lookup nog niet geïmplementeerd; dataset vereist aparte verwerking)"

# ────────────────────────────────────────────────────────────────────────
# Centrale routeringsfunctie: lookup_definitie
# ────────────────────────────────────────────────────────────────────────
def lookup_definitie(begrip: str, bron: Optional[str] = None) -> str:
    """
    Haalt de definitie op van 'begrip' via de opgegeven bron.
    Beschikbare bronnen: wikipedia, wiktionary, ensie, overheidnl,
    strafrechtketen, kamerstukken, iate, combinatie.
    Als bron niet gespecificeerd is, wordt 'combinatie' gebruikt.
    """
    bron = (bron or "combinatie").lower()
    if bron == "wikipedia":
        return zoek_definitie_op_wikipedia(begrip)
    elif bron == "wiktionary":
        return zoek_definitie_op_wiktionary(begrip)
    elif bron == "ensie":
        return zoek_definitie_op_ensie(begrip)
    elif bron == "overheidnl":
        return zoek_definitie_op_overheidnl(begrip)
    elif bron == "strafrechtketen":
        return zoek_definitie_op_strafrechtketen(begrip)
    elif bron == "kamerstukken":
        return zoek_definitie_op_kamerstukken(begrip)
    elif bron == "iate":
        return zoek_definitie_op_iate(begrip)
    elif bron == "combinatie":
        return zoek_definitie_combinatie(begrip)
    else:
        return f"⚠️ Onbekende bron '{bron}'. Beschikbare bronnen: wikipedia, wiktionary, ensie, overheidnl, strafrechtketen, kamerstukken, iate, combinatie."

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

# ✅ Deze functie bestond in de vorige versie en wordt elders nog geïmporteerd.
# ✅ Zorgt voor backward compatibility met bestaande modules zoals ai_toetser.core
# ✅ Verwijst door naar lookup_definitie (de centrale router)
def zoek_definitie_via_websearch(begrip: str, context: Optional[str] = None) -> Optional[str]:
    """
    ✅ Legacy-ondersteuning voor oudere modules
    ✅ Verwijst intern door naar de nieuwe lookup_definitie(...) router
    """
    return lookup_definitie(begrip, context)

# ─────────────────────────────────────────────────────────────────────────────
# ✅ Éénmalig JSON inladen en cachen
# ─────────────────────────────────────────────────────────────────────────────
_PLURALE_TANTUM_SET = None  # ✅ Module-variabele voor caching: laden we één keer

def _load_plurale_tantum() -> set:
    """
    Laadt de lijst van plurale-tantum woorden uit de JSON en retouneert een set.
    
    # ✅ Caching in module-variabele voor performance:
    #   Bij de eerste aanroep leest deze functie het JSON-bestand in en zet alle
    #   termen om naar lowercase in een Python-set. Volgende aanroepen hergebruiken
    #   deze set, zodat we niet telkens de schijf op hoeven.
    
    Stappen:
    1. Bepaal pad op basis van de bestandslocatie van deze module.
    2. Open en parse het JSON-bestand `nl_pluralia_tantum_100.json`.
    3. Haal de lijst op uit de key `"plurale_tantum"`.
    4. Zet elk woord naar lowercase en stop in een set voor O(1) lookup.
    """
    global _PLURALE_TANTUM_SET
    if _PLURALE_TANTUM_SET is None:
        # 🔧 Bepaal het pad naar de JSON in de submap "data"
        pad = os.path.join(
            os.path.dirname(__file__),
            "data",
            "nl_pluralia_tantum_100.json"
        )
        # 🔧 Open het bestand en laad de JSON
        with open(pad, encoding="utf-8") as f:
            data = json.load(f)
        # ✅ Zet alle termen naar lowercase voor betrouwbare, case-insensitive lookup
        raw_list = data.get("plurale_tantum", [])
        _PLURALE_TANTUM_SET = {w.strip().lower() for w in raw_list if isinstance(w, str)}
    return _PLURALE_TANTUM_SET

def is_plurale_tantum(term: str) -> bool:
    """
    Controleert of `term` een plurale-tantum is, d.w.z. een woord dat alleen in
    meervoud bestaat (zoals 'kosten' of 'hersenen').
    
    Werkwijze:
    1. Normaliseer de invoer:
       • Verwijder omliggende whitespace (strip).
       • Zet om naar lowercase voor case-insensitive vergelijking.
    2. Kijk of de genormaliseerde term in de gecachte set zit.
    3. Return True als het woord in de lijst staat, anders False.
    
    # ✅ Deze check geeft een stevige exception-vrijstelling voor woorden die
    #   alleen in meervoud voorkomen, zodat ze niet onterecht als fout
    #   gemarkeerd worden in VER-01.
    """
    # 🔧 Normaliseren van de term
    term_norm = term.strip().lower()
    # 🔍 Membership-test in de gecachte plurale-tantum set
    return term_norm in _load_plurale_tantum()