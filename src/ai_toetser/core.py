import os
import re
from typing import Dict, Any, Optional
from web_lookup.lookup import is_plurale_tantum
# --- 🔪 Externe bibliotheken (via pip) ---
# 📌 Streamlit pagina-configuratie
#st.set_page_config(page_title="DefinitieAgent", page_icon="🧠")

from dotenv import load_dotenv
from openai import OpenAI

# --- 🔄 Eigen modules (projectspecifiek) ---

# --- ⚙️ Config-loaders en verboden-woordenbeheer ---
# ✅ Centrale JSON-loaders
from config.config_loader import laad_toetsregels
# ✅ Opschoning van GPT-definitie (externe module)
from config.verboden_woorden import laad_verboden_woorden, genereer_verboden_startregex


# 🌱 Initialiseer OpenAI-client
load_dotenv()

# 💚 --------------- VERPLAATSTE OPENAI-CLIENT ---------------  
def _get_openai_client() -> OpenAI:          # ✅ privé helper  
    """
    # ✅ Maakt OpenAI-client alléén aan wanneer hij voor het eerst nodig is.
    #    Zo kan het pakket zonder OPENAI_API_KEY geïmporteerd worden.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY ontbreekt. Zet deze variabele in .env of in je CI-secrets."
        )
    return OpenAI(api_key=api_key)
# 💚 ----------------------------------------------------------


# ✅ Toetsing voor regel CON-01 (Contextspecifieke formulering zonder expliciete benoeming)
# Deze toetsregel controleert of de definitie géén expliciete verwijzing bevat naar de opgegeven context(en).
#
# 🟩 Toelichting voor ontwikkelaars:
# ➤ Alleen de contexten die expliciet zijn opgegeven via het contexten-dict worden getoetst.
#    Voorbeeld: {"organisatie": "DJI", "juridisch": "Strafrecht"}
# ➤ De JSON-patronen worden nog steeds gebruikt als bredere herkenning van contexttaal (indirect).
# ➤ Directe herhaling van opgegeven contextwaarden (of herkenbare afleidingen) is *niet toegestaan*.
# ➤ Dit voorkomt dat de definitie dubbelop of contextbevestigend wordt geformuleerd.
# ➤ Goede voorbeelden zijn impliciet afgestemd op context zonder deze te benoemen.

def toets_CON_01(definitie: str, regel: dict, contexten: dict = None) -> str:
    """
    CON-01: context mag niet letterlijk in de definitie voorkomen.
    1️⃣ Dynamisch: user-gegeven contexten
    2️⃣ Statisch: JSON-patronen
    3️⃣ Expliciete foute voorbeelden
    4️⃣ Expliciete goede voorbeelden
    5️⃣ Fallback: ✔️
    """
    definitie_lc = definitie.lower()
    contexten = contexten or {}

    # ✅ 1️⃣ Dynamisch: user-gegeven contexten
    expliciete_hits = []
    for label, waarde in contexten.items():
        if not waarde:
            continue
        w = waarde.lower().strip()
        varianten = {
            w,
            w + "e",
            w + "en",
            w.rstrip("e")
        }
        for var in varianten:
            if var and var in definitie_lc:
                expliciete_hits.append(var)
    if expliciete_hits:
        gevonden = ", ".join(sorted(set(expliciete_hits)))
        return f"❌ CON-01: opgegeven context letterlijk in definitie herkend (‘{gevonden}’)"

    # ✅ 2️⃣ Statisch: patronen uit JSON
    for patroon in regel.get("herkenbaar_patronen", []):
        if re.search(patroon, definitie, re.IGNORECASE):
            return "❌ CON-01: contextpatroon herkend in definitie"

    # ✅ 3️⃣ Foute voorbeelden (JSON)
    for fout in regel.get("foute_voorbeelden", []):
        if fout.lower() in definitie_lc:
            return "❌ CON-01: definitie bevat expliciet fout voorbeeld"

    # ✅ 4️⃣ Goede voorbeelden (JSON)
    for goed in regel.get("goede_voorbeelden", []):
        if goed.lower() in definitie_lc:
            return "✔️ CON-01: definitie komt overeen met goed voorbeeld"

    # ✅ 5️⃣ Fallback: geen contextuele verwijzing
    return "✔️ CON-01: geen expliciete contextvermelding in definitie"

    # 🟩 2. Herken bredere contexttermen via reguliere patronen uit JSON
    patronen = regel.get("herkenbaar_patronen", [])
    contextuele_term_hits = set()
    for patroon in patronen:
        contextuele_term_hits.update(re.findall(patroon, definitie, re.IGNORECASE))

    # 🟩 3. Vergelijk met voorbeeldzinnen
    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])
    goede_match = any(vb.lower() in definitie_lc for vb in goede_voorbeelden)
    foute_match = any(vb.lower() in definitie_lc for vb in foute_voorbeelden)

    if contextuele_term_hits:
        if foute_match:
            return f"❌ CON-01: bredere contexttermen herkend ({', '.join(contextuele_term_hits)}), en lijkt op fout voorbeeld"
        return f"🟡 CON-01: bredere contexttaal herkend ({', '.join(contextuele_term_hits)}), formulering mogelijk vaag"

    if goede_match:
        return "✔️ CON-01: geen expliciete context, formulering komt overeen met goed voorbeeld"

    return "✔️ CON-01: geen expliciete contextverwijzing aangetroffen"

# ✅ CON-02: Deze regel controleert of er een expliciete bronvermelding aanwezig is via het veld 'bronnen_gebruikt'.
# ➤ Een goede definitie is gebaseerd op een gezaghebbende bron (zoals wetgeving, een beleidsregel of standaard),
#     en noemt deze bron expliciet, bijvoorbeeld: “artikel 1, lid 2 van het Wetboek van Strafvordering”.
# ➤ Deze toets kijkt naar het door AI gegenereerde veld 'bronnen_gebruikt', en niet naar de tekst van de definitie zelf.
# ➤ Bij afwezigheid van dit veld of als het leeg is, wordt de definitie afgekeurd.
# ➤ Als er wel een bron wordt genoemd, maar deze te algemeen is (zoals alleen “de AVG” of “wetgeving”),
#     volgt een neutrale waarschuwing dat verdere specificatie nodig is.
# ➤ Alleen concrete verwijzingen zoals “art. 3.2 Besluit justitiële gegevens” of “Titel 1.4 Awb” leiden tot een positief oordeel.
#💚 Groene uitlegregels in de code:
#	•	We laden éénmalig de JSON (regel) vanuit laad_toetsregels().
#	•	bronpatronen_specifiek en bronpatronen_algemeen worden in de JSON beheerd, niet meer in de code.
#	•	Zo kun je in één plek (de JSON) de lijst uitbreiden of aanpassen.
def toets_CON_02(definitie: str, regel: dict, bronnen_gebruikt: str = None) -> str:
    """
    CON-02: baseren op authentieke bron.
    1️⃣ ❌ lege of ontbrekende 'bronnen_gebruikt'
    2️⃣ ✔️ concrete bronpatronen (art., lid, paragraaf…)
    3️⃣ 🟡 algemene bronpatronen (wet, AVG…)
    4️⃣ ❌ anders: niet authentiek genoeg
    """
    # 1️⃣ ❌ geen bronnen opgegeven
    if not bronnen_gebruikt or not bronnen_gebruikt.strip():
        return "❌ CON-02: geen opgegeven bronnen gevonden (veld 'bronnen_gebruikt' is leeg of ontbreekt)"

    bg = bronnen_gebruikt.strip()
    lc = bg.lower()

    # 2️⃣ ✔️ check concrete patronen uit JSON
    for pat in regel.get("bronpatronen_specifiek", []):
        if re.search(pat, lc):
            # ✅ concreet genoeg
            return f"✔️ CON-02: bronvermelding voldoende specifiek → {bg}"

    # 3️⃣ 🟡 check algemene patronen uit JSON
    for pat in regel.get("bronpatronen_algemeen", []):
        if re.search(pat, lc):
            return f"🟡 CON-02: bronvermelding aanwezig ({bg}), maar mogelijk te algemeen"

    # 4️⃣ ❌ fallback
    return f"❌ CON-02: bronvermelding gevonden ({bg}), maar niet herkend als authentiek of specifiek"


# ✅ Toetsing voor regel ESS-01 (Essentie, niet doel)
def toets_ESS_01(definitie: str, regel: dict) -> str:
    """
    ESS-01: Beschrijf de essentie, niet het doel.
    ❌ Als één van de doel-patronen in de definitie opduikt.
    ✔️ Anders: geen doelgerichte formuleringen aangetroffen.
    """
    # 1️⃣ per doel-patroon controleren: zodra er één match is ➞ fout
    for patroon in regel.get("herkenbaar_patronen", []):
        match = re.search(patroon, definitie, re.IGNORECASE)
        if match:
            return (
                f"❌ ESS-01: doelpatroon “{match.group(0)}” herkend in definitie "
                f"(patroon: {patroon})"
            )

    # 2️⃣ fallback: geen enkel doel-patroon gevonden ➞ OK
    return "✔️ ESS-01: geen doelgerichte formuleringen aangetroffen"



def toets_ESS_02(definitie: str, regel: Dict[str, Any]) -> str:
    """
    ESS-02: Ontologische categorie expliciteren (type / particulier / proces / resultaat)
    -----------------------------------------------------------------------------------
    Indien een begrip meerdere ontologische categorieën kan aanduiden, 
    moet uit de definitie ondubbelzinnig blijken welke van deze vier bedoeld wordt:
      • type (soort)
      • particulier (exemplaar)
      • proces (activiteit)
      • resultaat (uitkomst)

    Volgorde:
      1️⃣ Expliciete foute voorbeelden per categorie → ❌
      2️⃣ Detectie via patronen per categorie
      3️⃣ Één categorie hit → ✔️
      4️⃣ Meerdere hits → ❌ ambiguïteit
      5️⃣ Geen hits → check goede voorbeelden per categorie → ✔️
      6️⃣ Anders → ❌ geen duidelijke marker
    """
    d = definitie.lower().strip()

    # 1️⃣ Expliciete foute voorbeelden per categorie
    categories = [
        ("type", "foute_voorbeelden_type"),
        ("particulier", "foute_voorbeelden_particulier"),
        ("proces", "foute_voorbeelden_proces"),
        ("resultaat", "foute_voorbeelden_resultaat"),
    ]
    for cat, key in categories:
        for voorbeeld in regel.get(key, []):
            if voorbeeld.lower() in d:
                return (f"❌ ESS-02: expliciet fout voorbeeld voor {cat} gevonden "
                        f"– vermijd deze formulering")

    # 2️⃣ Detectie via patronen per categorie
    hits: Dict[str, List[str]] = {}
    pattern_keys = {
        "type": "herkenbaar_patronen_type",
        "particulier": "herkenbaar_patronen_particulier",
        "proces": "herkenbaar_patronen_proces",
        "resultaat": "herkenbaar_patronen_resultaat",
    }
    for cat, pat_key in pattern_keys.items():
        for pat in regel.get(pat_key, []):
            if re.search(pat, d, flags=re.IGNORECASE):
                hits.setdefault(cat, []).append(pat)

    # 3️⃣ Één categorie → ✔️
    if len(hits) == 1:
        cat, pats = next(iter(hits.items()))
        unieke = ", ".join(sorted(set(pats)))
        return f"✔️ ESS-02: eenduidig als {cat} gedefinieerd ({unieke})"

    # 4️⃣ Meerdere categorieën → ❌ ambiguïteit
    if len(hits) > 1:
        found = ", ".join(sorted(hits.keys()))
        return (f"❌ ESS-02: ambiguïteit – meerdere categories herkend ({found}); "
                "kies één betekenislaag")

    # 5️⃣ Geen hits → goede voorbeelden per categorie
    good_keys = {
        "type": "goede_voorbeelden_type",
        "particulier": "goede_voorbeelden_particulier",
        "proces": "goede_voorbeelden_proces",
        "resultaat": "goede_voorbeelden_resultaat",
    }
    for cat, key in good_keys.items():
        for voorbeeld in regel.get(key, []):
            if voorbeeld.lower() in d:
                return f"✔️ ESS-02: eenduidig als {cat} gedefinieerd (voorbeeld match)"

    # 6️⃣ Fallback → geen marker
    return ("❌ ESS-02: geen duidelijke ontologische marker "
            "(type, particulier, proces of resultaat) gevonden")
def toets_ESS_03(definitie: str, regel: dict) -> str:
    """
    ESS-03: Instanties uniek onderscheidbaar (telbaarheid).
    1️⃣ Expliciete foute voorbeelden → ❌
    2️⃣ Expliciete goede voorbeelden → ✔️
    3️⃣ Detectie unieke-ID-criteria via JSON-patronen → ✔️/❌
    4️⃣ Fallback: altijd ❌ als niets gevonden.
    """
    d_lc = definitie.lower().strip()

    # 1️⃣ Expliciete foute voorbeelden eerst afvangen
    for fout in regel.get("foute_voorbeelden", []):
        if fout.lower() in d_lc:
            return "❌ ESS-03: definitie mist unieke identificatiecriteria (fout voorbeeld aangetroffen)"

    # 2️⃣ Expliciete goede voorbeelden daarna
    for goed in regel.get("goede_voorbeelden", []):
        if goed.lower() in d_lc:
            return "✔️ ESS-03: expliciete unieke identificatiecriteria gevonden (volgens goed voorbeeld)"

    # 3️⃣ Detectie via patronen uit JSON
    gevonden = set()
    for patroon in regel.get("herkenbaar_patronen", []):
        for m in re.finditer(patroon, definitie, flags=re.IGNORECASE):
            gevonden.add(m.group(0).strip())

    if gevonden:
        labels = ", ".join(sorted(gevonden))
        return f"✔️ ESS-03: unieke identificatiecriteria herkend ({labels})"

    # 4️⃣ Fallback: geen criteria gevonden
    return "❌ ESS-03: geen unieke identificatiecriteria gevonden; definitie is niet telbaar onderscheidbaar"
    

def toets_ESS_04(definitie: str, regel: dict) -> str:
    """
    ESS-04: Toetsbaarheid.
    Een definitie moet toetsbare criteria bevatten zodat een gebruiker
    objectief kan vaststellen of iets wel of niet onder het begrip valt.

    Bron (ASTRA DBT 3.1):
      • FOUT-voorbeelden: vage bewoordingen als ‘zo snel mogelijk’, ‘zo veel mogelijk’
      • GOED-voorbeelden: harde deadlines (‘binnen 3 dagen’), percentages (‘tenminste 80%’)
      • Toetsvraag: “Is het mogelijk op basis van de definitie vast te stellen of iets
        wel of niet onder het begrip valt?”

    JSON-velden gebruikt:
      - foute_voorbeelden: expliciete vage formuleringsgevallen
      - goede_voorbeelden: concrete, gewenste toetsformuleringen
      - herkenbaar_patronen: regex voor tijd/percentage/‘objectieve criteria’ e.d.
    """
    d = definitie.lower().strip()

    # ℹ️ 1️⃣ Expliciete FOUT-voorbeelden uit JSON afvangen
    #   Dit blok pakt zinnen die in de config staan als “foute voorbeelden”.
    #   Die duiden op vage, niet-toetsbare bewoording.
    for fout in regel.get("foute_voorbeelden", []):
        if fout.lower() in d:
            return (
                "❌ ESS-04: bevat vage bewoording "
                "(bijv. ‘zo snel mogelijk’) – definitie is niet toetsbaar"
            )

    # ℹ️ 2️⃣ Expliciete GOED-voorbeelden uit JSON herkennen
    #   Hierin staan voorbeelden zoals ‘binnen 3 dagen’, die we direct honoreren.
    for goed in regel.get("goede_voorbeelden", []):
        if goed.lower() in d:
            return (
                "✔️ ESS-04: bevat toetsbare criteria "
                "(volgens goed voorbeeld uit config)"
            )

    # ℹ️ 3️⃣ Patronen uit JSON op zoek naar harde criteria
    #   De JSON bevat patronen als '\bbinnen\s+\d+\s+dagen\b', ‘\b\d+ %\b’, etc.
    gevonden = []
    for patroon in regel.get("herkenbaar_patronen", []):
        if re.search(patroon, definitie, flags=re.IGNORECASE):
            gevonden.append(patroon)

    # ℹ️ 3a️⃣ Extra automatische checks voor getallen/tijd/percentage
    #   Mocht de JSON uit de config niet alle gevallen bevatten,
    #   dan herkennen we hier nog ruwe numerieke uitdrukkingen.
    if re.search(r"\b\d+\s*(dagen|weken|uren|maanden)\b", d):
        gevonden.append("AUTO: numeriek tijdspatroon")
    if re.search(r"\b\d+\s*%\b", d):
        gevonden.append("AUTO: percentagepatroon")

    if gevonden:
        unieke = ", ".join(sorted(set(gevonden)))
        return f"✔️ ESS-04: toetsbaar criterium herkend ({unieke})"

    # ℹ️ 4️⃣ Fallback: niets gevonden → definitie is niet toetsbaar
    return (
        "❌ ESS-04: geen toetsbare elementen gevonden; "
        "definitie bevat geen harde criteria voor objectieve toetsing"
    )

# ✅ Toetsing voor regel ESS-05 (Voldoende onderscheidend)
def toets_ESS_05(definitie: str, regel: dict) -> str:
    """
    ESS-05: Voldoende onderscheidend.
    Een definitie moet expliciet maken waarin het begrip zich onderscheidt
    van verwante begrippen in hetzelfde domein.

    Bron (ASTRA DBT ESS-05):
      • FOUT-voorbeelden: vage of niet-onderscheidende formuleringen.
      • GOED-voorbeelden: expliciete tegenstelling of uniek kenmerk.
      • Toetsvraag: “Maakt de definitie duidelijk waarin het begrip zich
        onderscheidt van andere begrippen?”

    JSON-velden gebruikt:
      - foute_voorbeelden: expliciete misser-zinnen uit config
      - goede_voorbeelden: ideale voorbeeldzinnen uit config
      - herkenbaar_patronen: regex voor tegenstelling/verschil/unique kenmerken
    """
    d = definitie.lower().strip()

    # ℹ️ 1️⃣ Expliciete FOUT-voorbeelden afvangen
    #    Deze voorbeelden staan in de JSON als “foute_voorbeelden”.
    for fout in regel.get("foute_voorbeelden", []):
        if fout.lower() in d:
            return (
                "❌ ESS-05: definitie bevat niet-onderscheidende formulering "
                f"(fout voorbeeld: “…{fout}…”)"
            )

    # ℹ️ 2️⃣ Expliciete GOED-voorbeelden direct honoreren
    #    Deze voorbeelden tonen hoe het wél moet (zichtbare tegenstelling / uniek kenmerk).
    for goed in regel.get("goede_voorbeelden", []):
        if goed.lower() in d:
            return (
                "✔️ ESS-05: onderscheidende formulering aangetroffen "
                "(volgens goed voorbeeld)"
            )

    # ℹ️ 3️⃣ Patronen uit JSON op zoek naar sleutelwoorden
    #    Bijvoorbeeld “in tegenstelling tot”, “verschilt van”, “specifiek voor”, etc.
    gevonden = []
    for patroon in regel.get("herkenbaar_patronen", []):
        if re.search(patroon, definitie, flags=re.IGNORECASE):
            gevonden.append(patroon)

    if gevonden:
        labels = ", ".join(sorted(set(gevonden)))
        return (
            f"✔️ ESS-05: onderscheidende patroon(en) herkend ({labels})"
        )

    # ℹ️ 4️⃣ Fallback: niets gevonden → definitie is onvoldoende onderscheidend
    return (
        "❌ ESS-05: geen onderscheidende elementen gevonden; "
        "definitie maakt niet duidelijk waarin het begrip zich onderscheidt"
    )

# ✅ Toetsing voor regel INT-01 (Compacte en begrijpelijke zin)
def toets_INT_01(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    complexiteit_gevonden = set()
    for patroon in patroon_lijst:
        complexiteit_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goede_aanwezig = any(
        voorbeeld.lower() in definitie.lower()
        for voorbeeld in goede_voorbeelden
    )
    foute_aanwezig = any(
        voorbeeld.lower() in definitie.lower()
        for voorbeeld in foute_voorbeelden
    )

    if not complexiteit_gevonden:
        if goede_aanwezig:
            return "✔️ INT-01: definitie is compact en komt overeen met goed voorbeeld"
        else:
            return "✔️ INT-01: geen complexe elementen herkend – mogelijk goed geformuleerd"

    if foute_aanwezig:
        return (
            f"❌ INT-01: complexe elementen gevonden ({', '.join(complexiteit_gevonden)}), "
            f"en definitie lijkt op fout voorbeeld"
        )
    else:
        return (
            f"❌ INT-01: complexe elementen gevonden ({', '.join(complexiteit_gevonden)}), "
            f"maar geen expliciet fout voorbeeld herkend"
        )

def toets_INT_02(definitie: str, regel: dict) -> str:
    """
    INT-02: Geen beslisregel of voorwaardelijke formuleringen.

    1️⃣ Expliciete foute voorbeelden uit JSON → direct ❌  
    2️⃣ Expliciete goede voorbeelden uit JSON → direct ✔️  
    3️⃣ Detectie via patronen (zoals 'indien', 'mits', etc.) → ❌  
    4️⃣ Fallback: geen beslisregels aangetroffen → ✔️  

    Uitleg:
    - Een definitie mag niet als beslisregel geformuleerd worden;
      dat hoort in regelgeving, niet in een lemma.
    - Afleidingsregels (deterministische algoritmen) zijn wél toegestaan,
      maar vallen buiten INT-02 (toets op voorwaardelijke taal).
    """
    tekst = definitie.lower()

    # 1️⃣ Expliciete foute voorbeelden krijgen prioriteit
    for fout in regel.get("foute_voorbeelden", []):
        if fout.lower() in tekst:
            return "❌ INT-02: voorwaardelijke formulering aangetroffen (komt precies overeen met fout voorbeeld)"

    # 2️⃣ Expliciete goede voorbeelden daarna
    for goed in regel.get("goede_voorbeelden", []):
        if goed.lower() in tekst:
            return "✔️ INT-02: voorbeeldtekst komt overeen met goed voorbeeld (geen beslisregel)"

    # 3️⃣ Patronen voor voorwaardelijke taal detecteren
    patronen = regel.get("herkenbaar_patronen", [])
    gevonden = []
    for pat in patronen:
        if re.search(pat, definitie, flags=re.IGNORECASE):
            gevonden.append(pat)
    if gevonden:
        labels = ", ".join(sorted(set(gevonden)))
        return f"❌ INT-02: voorwaardelijke taal herkend ({labels})"

    # 4️⃣ Fallback: geen beslisregel of voorwaardelijke formulering
    return "✔️ INT-02: geen beslisregels of voorwaardelijke formuleringen aangetroffen"

def toets_INT_03(definitie: str, regel: dict) -> str:
    """
    INT-03: Voornaamwoord-verwijzing duidelijk
    --------------------------------------------------
    Een definitie mag geen onduidelijke verwijzingen naar 
    “iets” bevatten via voornaamwoorden als 'deze', 'dit', 'die', enz.
    Elk voornaamwoord moet in de zin zelf direct naar zijn antecedent
    verwijzen, zodat de definitie zelfstandig leesbaar is.

    Werkwijze:
      1️⃣ Zoek alle voornaamwoorden via de regex-patronen uit JSON.
      2️⃣ Als er géén voornaamwoorden zijn: ✔️ geen probleem.
      3️⃣ Als er voornaamwoorden zijn:
         a. Controleer of een expliciet goed voorbeeld uit JSON 
            in de tekst voorkomt → ✔️
         b. Anders: ❌ onduidelijke verwijzing

    Uitlegregels:
      - “deze”, “dit”, etc. zijn pas acceptabel als je in hetzelfde 
        zinsdeel direct zegt waar “deze” naar verwijst.
      - Een definitie moet in éé́n keer lezen, zonder dat de lezer
        achteraf moet gissen welk zelfstandig naamwoord bedoeld is.
    """
    tekst = definitie.strip()
    tekst_lc = tekst.lower()

    # 1️⃣ Verzamel alle voornaamwoordhits
    patterns = regel.get("herkenbaar_patronen", [])
    gevonden = []
    for pat in patterns:
        for m in re.finditer(pat, tekst, flags=re.IGNORECASE):
            gevonden.append(m.group(0))

    # 2️⃣ Geen voornaamwoorden → OK
    if not gevonden:
        return "✔️ INT-03: geen onduidelijke voornaamwoord-verwijzing aangetroffen"

    # 3️⃣ Controle op expliciet goed voorbeeld
    for goed in regel.get("goede_voorbeelden", []):
        if goed.lower() in tekst_lc:
            # we vertrouwen hier op de JSON-voorbeeldzin dat die de
            # pronomen op een correcte manier elimineert
            return (
                f"✔️ INT-03: voornaamwoorden gevonden "
                f"({', '.join(sorted(set(gevonden)))}) maar correct opgehelderd"
            )

    # 4️⃣ Anders: foutmelding met de gematchte pronomen
    distinct = ", ".join(sorted(set(gevonden)))
    return (
        f"❌ INT-03: onduidelijke voornaamwoord-verwijzingen aangetroffen "
        f"({distinct}); antecedent niet expliciet gemaakt"
    )


def toets_INT_04(definitie: str, regel: dict) -> str:
    """
    INT-04: Lidwoord-verwijzing duidelijk
    -------------------------------------
    Bij een bepaald lidwoord (‘de’, ‘het’) in een definitie moet
    direct helder zijn waarnaar verwezen wordt. Anders is de zin
    vaag of contextafhankelijk.

    Stappen:
      1️⃣ Zoek alle ‘de X’ / ‘het Y’ treffers met de JSON-patronen.
      2️⃣ Als geen treffers: ✔️ geen onduidelijke verwijzingen.
      3️⃣ Anders:
         a. Als één van de goede voorbeelden uit JSON voorkomt → ✔️
         b. Anders → ❌ onduidelijke lidwoord-verwijzing(en).

    Uitleg:
      • “De instelling” mag alleen als je meteen zegt **welke**
        instelling (bijv. “de instelling (de Raad voor de Rechtspraak)”).
      • Zoniet: gebruik “een instelling” of benoem de antecedent direct.
    """
    tekst = definitie.strip()
    tekst_lc = tekst.lower()

    # 1️⃣ Verzamel alle ‘de …’ / ‘het …’ matches
    hits = []
    for patroon in regel.get("herkenbaar_patronen", []):
        for match in re.finditer(patroon, tekst, flags=re.IGNORECASE):
            hits.append(match.group(0))

    # 2️⃣ Geen onduidelijke lidwoord-verwijzingen
    if not hits:
        return "✔️ INT-04: geen onduidelijke lidwoord-verwijzingen aangetroffen"

    # 3️⃣ Controle op expliciete goede voorbeelden
    for goed in regel.get("goede_voorbeelden", []):
        if goed.lower() in tekst_lc:
            unieke = ", ".join(sorted(set(hits)))
            return (
                f"✔️ INT-04: lidwoord-verwijzingen ({unieke}) "
                f"maar correct gespecificeerd volgens voorbeeld"
            )

    # ❌ Fallback: onduidelijke verwijzingen blijven staan
    unieke = ", ".join(sorted(set(hits)))
    return (
        f"❌ INT-04: onduidelijke lidwoord-verwijzingen ({unieke}); "
        f"specificeer expliciet of gebruik onbepaald lidwoord"
    )

def toets_INT_06(definitie: str, regel: dict) -> str:
    """
    INT-06: Definitie bevat geen toelichting.
    
    Een definitie moet zelfstandig afbakenen wat een begrip is, zonder
    nadere uitleg of voorbeelden in dezelfde zin.
    
    Toetsstappen:
      1️⃣ Expliciete foute voorbeelden uit JSON → ❌
      2️⃣ Detectie toelichtende signalen via regex-patronen → ❌
      3️⃣ Fallback: geen toelichting aangetroffen → ✔️

    JSON-velden gebruikt:
      • `foute_voorbeelden`: expliciete voorbeeldzinnen die toelichting bevatten
      • `herkenbaar_patronen`: lijst regex-patronen voor toelichtingssignalen
    """
    tekst = definitie.strip().lower()

    # 1️⃣ Expliciete foute voorbeelden eerst (prioriteit)
    for fout in regel.get("foute_voorbeelden", []):
        if fout.lower() in tekst:
            return (
                "❌ INT-06: definitie bevat expliciete toelichting "
                f"(voorbeeld: “{fout}”)."
            )

    # 2️⃣ Generieke detectie via toelichtingspatronen
    gevonden = []
    for patroon in regel.get("herkenbaar_patronen", []):
        if re.search(patroon, tekst):
            gevonden.append(patroon)

    if gevonden:
        samples = ", ".join(f"“{pat}”" for pat in gevonden)
        return (
            "❌ INT-06: toelichtende signalen herkend via patronen "
            f"{samples}."
        )

    # 3️⃣ Fallback: geen toelichting
    return "✔️ INT-06: geen toelichtende elementen in de definitie gevonden"

# ✅ Toetsing voor regel INT-07 (afkortingen)
import re

def toets_INT_07(definitie: str, regel: dict) -> str:
    """
    INT-07: Alleen toegankelijke afkortingen.

    1️⃣ Vind alle afkortingen via JSON-patronen.
    2️⃣ Expliciete foute voorbeelden eerst (zonder toelichting) → ❌
    3️⃣ Voor elke gevonden afkorting check:
         • DJI (Dienst Justitiële Inrichtingen)
         • AVG (…​)
         • [AVG](…​)
         • [[…​]]
       Zo niet → afkorting missen toelichting.
    4️⃣ Als alle afkortingen ok zijn → ✔️
       Anders → ❌ met de lijst van afkortingen zonder toelichting.
    """
    tekst = definitie
    tekst_lc = tekst.lower()

    # 1️⃣ Expliciete foute voorbeelden krijgen prioriteit
    for fout in regel.get("foute_voorbeelden", []):
        if fout.lower() in tekst_lc:
            return f"❌ INT-07: afkorting zonder uitleg aangetroffen in voorbeeld (‘{fout}’)"

    # 2️⃣ Vind álle afkortingen via JSON-patronen
    afk_patronen = regel.get("herkenbaar_patronen", [])
    afkorts = set()
    for pat in afk_patronen:
        afkorts.update(re.findall(pat, tekst))

    if not afkorts:
        return "✔️ INT-07: geen afkortingen in de definitie"

    # 3️⃣ Voor elke afkorting: controleren op uitleg of link
    zonder_toelichting = []
    for ab in sorted(afkorts):
        esc = re.escape(ab)
        # check op "(…​)" direct na de afkorting
        has_parenth = bool(re.search(rf"{esc}\s*\([^)]*?\)", tekst))
        # check op Markdown link [AB](…)
        has_mdlink  = bool(re.search(rf"\[{esc}\]\(.*?\)", tekst))
        # check op Wiki-link [[…]]
        has_wikilink = bool(re.search(rf"\[\[.*?\]\]", tekst))

        if not (has_parenth or has_mdlink or has_wikilink):
            zonder_toelichting.append(ab)

    # 4️⃣ Eindoordeel
    if zonder_toelichting:
        labels = ", ".join(zonder_toelichting)
        return f"❌ INT-07: geen toelichting voor afkorting(en): {labels}"
    return f"✔️ INT-07: alle afkortingen voorzien van directe toelichting of link"
# ✅ Toetsing voor regel INT-08 (Positieve formulering)
import re
from typing import Dict

def toets_INT_08(definitie: str, regel: Dict) -> str:
    """
    INT-08: Positieve formulering
    -----------------------------
    Een definitie wordt in principe positief geformuleerd (geen ontkenningen),
    met uitzondering van specificerende onderdelen (bijv. relatieve bijzinnen).

    Stappen:
      1️⃣ Verzamel alle herkenbare negatieve patronen uit de JSON-regel.
      2️⃣ Normaliseer naar kleine letters en maak uniek.
      3️⃣ Identificeer 'allowed' negaties: voorkomen binnen een relatieve bijzin.
      4️⃣ Bepaal 'disallowed' negaties: alle overige.
      5️⃣ Controleer aanwezigheid van goede en foute voorbeelden.
      6️⃣ Formuleer het resultaatbericht (✔️/❌) op basis van disallowed, allowed en voorbeelden.
    """
    # 1️⃣ 💚 Haal de herkenbare negatieve patronen op
    patronen = regel.get("herkenbaar_patronen", [])

    # 2️⃣ 💚 Vind alle matches en maak uniek (lowercase)
    gevonden = []
    for pat in patronen:
        gevonden.extend(re.findall(pat, definitie, flags=re.IGNORECASE))
    negatieve_vormen = {v.lower() for v in gevonden}

    # 3️⃣ 💚 Detecteer allowed negaties in specificerende context (relatieve bijzin)
    allowed = set()
    for neg in list(negatieve_vormen):
        patroon_context = rf'\bdie\b.*\b{re.escape(neg)}\b'
        if re.search(patroon_context, definitie, flags=re.IGNORECASE):
            allowed.add(neg)

    # 4️⃣ 💚 Bepaal disallowed negaties
    disallowed = sorted(nv for nv in negatieve_vormen if nv not in allowed)

    # 5️⃣ 💚 Check voorbeelden
    goede = [vb.lower() for vb in regel.get("goede_voorbeelden", [])]
    fout = [vb.lower() for vb in regel.get("foute_voorbeelden", [])]
    uitleg_aanwezig = any(v in definitie.lower() for v in goede)
    fout_aanwezig = any(v in definitie.lower() for v in fout)

    # 6️⃣ 💚 Formuleer resultaat
    if not disallowed:
        if allowed:
            return (
                f"✅ INT-08: alleen toegestane negatieve termen "
                f"({', '.join(allowed)}) in specificerende context"
            )
        if uitleg_aanwezig:
            return "✅ INT-08: geen negatieve formuleringen en komt overeen met goed voorbeeld"
        return "✅ INT-08: definitie bevat geen negatieve formuleringen"

    # Er zijn disallowed negaties
    if uitleg_aanwezig:
        return (
            f"✅ INT-08: negatieve termen ({', '.join(disallowed)}) gevonden, "
            "maar correct geformuleerd volgens goed voorbeeld"
        )
    if fout_aanwezig:
        return (
            f"❌ INT-08: negatieve termen ({', '.join(disallowed)}) gevonden, "
            "lijkt op fout voorbeeld"
        )
    return (
        f"❌ INT-08: negatieve termen ({', '.join(disallowed)}) gevonden, "
        "zonder duidelijke uitleg"
    )


# ✅ Toetsing voor regel INT-09 (Opsomming is limitatief)
def toets_INT_09(definitie: str, regel: Dict) -> str:
    """
    INT-09: Opsomming in extensionele definitie is limitatief
    --------------------------------------------------------
    In extensionele definities worden alle bedoelde elementen opgesomd.
    Wanneer een definitie opsommingstermen bevat (zoals 'zoals', 'bijvoorbeeld'),
    moet expliciet blijken dat de genoemde elementen de enige mogelijke zijn.

    Stappen:
      1️⃣ Haal alle ongewenste opsommingspatronen uit JSON op.
      2️⃣ Verzamel alle treffers (lowercase, uniek).
      3️⃣ Check of een goed voorbeeld uit JSON in de definitie staat.
      4️⃣ Check of een fout voorbeeld uit JSON in de definitie staat.
      5️⃣ Als geen ongewenste termen gevonden:
          – Als goed voorbeeld aanwezig → ✅ geen ongewenste termen, komt overeen met goed voorbeeld
          – Anders            → ✅ geen ongewenste opsommingstermen gevonden
      6️⃣ Als wel ongewenste termen gevonden:
          – Als goed voorbeeld aanwezig → ✅ opsommingswoorden (...) voorkomen, maar correct limitatief verwoord
          – Als fout voorbeeld aanwezig  → ❌ opsommingswoorden (...) lijken op fout voorbeeld
          – Anders                       → ❌ opsommingswoorden (...) zonder duidelijke limitatieve aanduiding
    """
    # 1️⃣ 💚 Haal de herkenbare ongewenste opsommingspatronen op
    patronen = regel.get("herkenbaar_patronen", [])

    # 2️⃣ 💚 Verzamel alle treffers (lowercase, uniek)
    ongewenste_termen = {
        match.group(0).lower()
        for pat in patronen
        for match in re.finditer(pat, definitie, flags=re.IGNORECASE)
    }

    # 3️⃣ & 4️⃣ 💚 Voorbeelden-check
    tekst_lc = definitie.lower()
    goede = [vb.lower() for vb in regel.get("goede_voorbeelden", [])]
    fout  = [vb.lower() for vb in regel.get("foute_voorbeelden", [])]
    uitleg_aanwezig = any(vb in tekst_lc for vb in goede)
    fout_aanwezig  = any(vb in tekst_lc for vb in fout)

    # 5️⃣ 💚 Geen ongewenste termen gevonden
    if not ongewenste_termen:
        if uitleg_aanwezig:
            return "✅ INT-09: geen ongewenste opsommingswoorden, komt overeen met goed voorbeeld"
        return "✅ INT-09: geen ongewenste opsommingswoorden gevonden"

    # 6️⃣ 💚 Ongewenste termen wél gevonden
    termen_str = ", ".join(sorted(ongewenste_termen))
    if uitleg_aanwezig:
        return (
            f"✅ INT-09: opsommingswoorden ({termen_str}) voorkomen, "
            "maar correct limitatief verwoord volgens goed voorbeeld"
        )
    if fout_aanwezig:
        return f"❌ INT-09: opsommingswoorden ({termen_str}) lijken op fout voorbeeld"
    return f"❌ INT-09: opsommingswoorden ({termen_str}) zonder duidelijke limitatieve aanduiding"

# ✅ Toetsing voor regel INT-10 (Geen ontoegankelijke achtergrondkennis nodig)
def toets_INT_10(definitie: str, regel: Dict) -> str:
    """
    INT-10: Geen ontoegankelijke achtergrondkennis nodig
    ---------------------------------------------------
    Een definitie mag niet verwijzen naar impliciete of niet-openbare kennis.
    Uitzondering: zeer specifieke verwijzing naar openbare bron (bv. wet met artikel).
    
    Stappen:
      1️⃣ Haal alle herkenbare achtergrondverwijzings­patronen op uit JSON.
      2️⃣ Verzamel alle treffers (lowercase, uniek).
      3️⃣ Controleer op aanwezigheid van goede voorbeelden.
      4️⃣ Controleer op aanwezigheid van foute voorbeelden.
      5️⃣ Als geen ongewenste verwijzingen:
         – Als goed voorbeeld aanwezig → ✅ komt overeen met voorbeeld
         – Anders                 → ✅ geen ontoegankelijke verwijzingen
      6️⃣ Als wel ongewenste verwijzingen:
         – Als goed voorbeeld aanwezig → ✅ verwijzingen (…) zijn toegestaan volgens voorbeeld
         – Als fout voorbeeld aanwezig  → ❌ verwijzingen (…) lijken op fout voorbeeld
         – Anders                       → ❌ verwijzingen (…) zonder toelichting
    """
    # 1️⃣ ✅ Haal patronen op
    patronen = regel.get("herkenbaar_patronen", [])

    # 2️⃣ ✅ Verzamel treffers (lowercase, uniek)
    vondsten = {
        m.group(0).lower()
        for pat in patronen
        for m in re.finditer(pat, definitie, flags=re.IGNORECASE)
    }

    # 3️⃣ & 4️⃣ ✅ Voorbeelden-check
    tekst_lc = definitie.lower()
    goede = [vb.lower() for vb in regel.get("goede_voorbeelden", [])]
    fout  = [vb.lower() for vb in regel.get("foute_voorbeelden", [])]
    goed_aanwezig = any(v in tekst_lc for v in goede)
    fout_aanwezig = any(v in tekst_lc for v in fout)

    # 5️⃣ ✅ Geen ongewenste verwijzingen gevonden
    if not vondsten:
        if goed_aanwezig:
            return "✅ INT-10: geen ontoegankelijke verwijzingen, komt overeen met goed voorbeeld"
        return "✅ INT-10: geen ontoegankelijke of impliciete achtergrondverwijzingen gevonden"

    # 6️⃣ ✅/❌ Ongewenste verwijzingen wél gevonden
    items = ", ".join(sorted(vondsten))
    if goed_aanwezig:
        return f"✅ INT-10: verwijzingen ({items}) zijn toegestaan volgens goed voorbeeld"
    if fout_aanwezig:
        return f"❌ INT-10: verwijzingen ({items}) gevonden, formulering lijkt op fout voorbeeld"
    return f"❌ INT-10: verwijzingen ({items}) gevonden, zonder uitleg of toelichting"

def toets_SAM_01(definitie: str, regel: Dict[str, Any]) -> str:
    """
    SAM-01: Kwalificatie leidt niet tot afwijking
    --------------------------------------------
    Een definitie van een gekwalificeerd begrip moet de basisterm expliciet bevatten
    en mag geen nieuwe betekenis introduceren: de gekwalificeerde term is altijd
    een subcategorie van de niet-gekwalificeerde term (genus + differentia-patroon).

    Stappen:
      1️⃣ Haal herkenbare kwalificatie-adjectieven op uit de JSON-regel.
      2️⃣ Verzamel alle kwalificaties (lowercase, uniek).
      3️⃣ Als er geen kwalificaties zijn → ✔️ geen afwijkende kwalificaties.
      4️⃣ Controleer op aanwezigheid van goede voorbeelden.
      5️⃣ Controleer op aanwezigheid van foute voorbeelden.
      6️⃣ Formuleer resultaatbericht:
         – ✔️ bij goede voorbeelden
         – ❌ bij foute voorbeelden
         – ❌ anders: mogelijke semantische afwijking
    """
    # 1️⃣ 💚 Haal patronen voor kwalificaties op
    patronen = regel.get("herkenbaar_patronen", [])

    # 2️⃣ 💚 Verzamel alle matches (lowercase, uniek)
    kwalificaties = {
        m.group(0).lower()
        for pat in patronen
        for m in re.finditer(pat, definitie, flags=re.IGNORECASE)
    }

    # 3️⃣ 💚 Geen kwalificaties aangetroffen
    if not kwalificaties:
        return "✔️ SAM-01: geen afwijkende kwalificaties aangetroffen in de definitie"

    # 4️⃣ & 5️⃣ 💚 Check voorbeelden
    tekst_lc = definitie.lower()
    goede = [vb.lower() for vb in regel.get("goede_voorbeelden", [])]
    fout  = [vb.lower() for vb in regel.get("foute_voorbeelden", [])]
    goed_aanwezig = any(v in tekst_lc for v in goede)
    fout_aanwezig = any(v in tekst_lc for v in fout)

    # 6️⃣ 💚 Resultaatberichten
    items = ", ".join(sorted(kwalificaties))
    if goed_aanwezig:
        return f"✔️ SAM-01: kwalificaties ({items}) correct toegepast volgens goede voorbeelden"
    if fout_aanwezig:
        return f"❌ SAM-01: kwalificaties ({items}) wijken af volgens fout voorbeeld"
    return f"❌ SAM-01: kwalificaties ({items}) kunnen afwijken van algemeen aanvaarde betekenis"

#✅ Toetsing voor regel SAM-02 (Kwalificatie omvat geen herhaling)
def fetch_base_definition(term: str) -> Optional[str]:
    """
    Placeholder: haal officiële definitie van 'term' op uit een externe repository.
    Momenteel nog niet geïmplementeerd → altijd None.
    """
    # TODO: vervang deze stub door een echte API- of JSON-lookup.
    return None

def toets_SAM_02(definitie: str, regel: Dict[str, Any]) -> str:
    """
    SAM-02: Kwalificatie omvat geen herhaling
    -----------------------------------------
    Vergelijk een gekwalificeerde definitie met de officiële basisterm-definitie
    (genus + differentia). Zonder repository valt de controle terug op:
    maximaal één letterlijke vermelding van de basisterm in de differentia.

    Stappen:
      1️⃣ Splits basisterm (voor ':') en body (na ':').
      2️⃣ Probeer de officiële basisterm-definitie op te halen.
         – Als gevonden: parse genus/differentia en controleer conflict.
         – Anders: fallback naar regex-based herhalingscheck.
      3️⃣ Als fallback:
         • Tel hoe vaak de basisterm in de body voorkomt.
         • ≤1 → ✔️, >1 → ❌ (met voorbeelden-check).
    """
    # 1️⃣ 💚 Splits kop en body
    kop, _, body = definitie.partition(':')
    basisterm = kop.strip().lower()
    body_lc = body.lower()

    # 2️⃣ 💚 Probeer officiële definitie op te halen
    base_def = fetch_base_definition(basisterm)
    if base_def is not None:
        # 2a️⃣ 💚 Parse genus + differentia (eenvoudig via split)
        _, _, base_diff = base_def.partition(':')
        # Check: genus (basisterm) moet in gekwalificeerde definitie
        if basisterm not in definitie.lower():
            return f"❌ SAM-02: genus (‘{basisterm}’) ontbreekt in gekwalificeerde definitie"
        # Check: geen letterlijke herhaling van basisterm in differentia meer dan eens
        count = len(re.findall(rf'\b{re.escape(basisterm)}\b', body_lc))
        if count > 1:
            return f"❌ SAM-02: overbodige herhaling van '{basisterm}' in differentia"
        return f"✔️ SAM-02: gekwalificeerde definitie sluit aan op genus+differentia-patroon"

    # 3️⃣ 💚 Fallback: regex-based herhalingscheck
    count_fallback = len(re.findall(rf'\b{re.escape(basisterm)}\b', body_lc))

    # <=1 vermelding = geen overbodige herhaling
    if count_fallback <= 1:
        return "✔️ SAM-02: geen overbodige herhaling van het hoofdbegrip in de definitie"

    # >1 vermelding = check voorbeelden
    tekst_lc = definitie.lower()
    goede = [vb.lower() for vb in regel.get("goede_voorbeelden", [])]
    fout  = [vb.lower() for vb in regel.get("foute_voorbeelden", [])]
    goed_aanwezig = any(g in tekst_lc for g in goede)
    fout_aanwezig = any(f in tekst_lc for f in fout)
    if goed_aanwezig:
        return f"✔️ SAM-02: meerdere vermeldingen van '{basisterm}' maar betekenisvol volgens goed voorbeeld"
    if fout_aanwezig:
        return f"❌ SAM-02: herhaling van '{basisterm}' lijkt op fout voorbeeld"
    return f"❌ SAM-02: overbodige herhalingen van '{basisterm}' gevonden in de definitie"

#✅ Toetsing voor regel SAM-03 (Definitieteksten niet nesten)
def toets_SAM_03(definitie: str, regel: Dict[str, Any]) -> str:
    """
    SAM-03: Definitieteksten niet nesten
    ------------------------------------
    Een definitie van een begrip, of een belangrijk deel daarvan, mag niet
    letterlijk worden herhaald in de definitie van een ander begrip.
    
    Stappen:
      1️⃣ Haal herkenbare patronen op uit de JSON-regel.
      2️⃣ Vind alle matches (lowercase, uniek).
      3️⃣ Als geen matches → ✔️ geen geneste definities.
      4️⃣ Check op aanwezigheid van goede voorbeelden.
      5️⃣ Check op aanwezigheid van foute voorbeelden.
      6️⃣ Formuleer ✔️/❌ op basis van deze checks.
    """
    # 1️⃣ 💚 Haal patronen op
    patronen = regel.get("herkenbaar_patronen", [])
    
    # 2️⃣ 💚 Verzamel alle genestelde trefwoorden
    nesten = {
        m.group(0).lower()
        for pat in patronen
        for m in re.finditer(pat, definitie, flags=re.IGNORECASE)
    }

    # 3️⃣ 💚 Geen geneste definities
    if not nesten:
        return "✔️ SAM-03: geen geneste of verweven definities aangetroffen"

    # 4️⃣ & 5️⃣ 💚 Voorbeelden-check
    tekst_lc = definitie.lower()
    goede = [vb.lower() for vb in regel.get("goede_voorbeelden", [])]
    fout  = [vb.lower() for vb in regel.get("foute_voorbeelden", [])]
    goed_aanwezig = any(g in tekst_lc for g in goede)
    fout_aanwezig = any(f in tekst_lc for f in fout)

    # 6️⃣ 💚 Resultaatbericht
    items = ", ".join(sorted(nesten))
    if goed_aanwezig:
        return f"✔️ SAM-03: verwijzingen ({items}) correct volgens goed voorbeeld"
    if fout_aanwezig:
        return f"❌ SAM-03: definities bevatten ({items}), lijkt op fout voorbeeld"
    return f"❌ SAM-03: definitie bevat geneste verwijzingen ({items}), definities liever afzonderlijk"
def toets_SAM_04(definitie: str, regel: Dict[str, Any]) -> str:
    """
    SAM-04: Begrip-samenstelling strijdt niet met samenstellende begrippen
    ---------------------------------------------------------------------
    De definitie van een samengesteld begrip moet een specialisatie zijn
    van één van de samenstellende delen (genus). De definitie moet daarom
    beginnen met dat genus, gevolgd door een differentia.

    Stappen:
      1️⃣ Splits composite_term (kop) en body (na ':').
      2️⃣ Isolatie van het deel vóór 'van', 'die' of 'dat'.
      3️⃣ Bepaal genus_word als het laatste woord uit dat fragment.
      4️⃣ Controleer of composite_term (zonder spaties) eindigt op genus_word.
      5️⃣ Override met voorbeelden:
         • ✔️ als goed voorbeeld aanwezig
         • ❌ als fout voorbeeld aanwezig
    """
    # 1️⃣ 💚 Splits kop en body
    kop, _, body = definitie.partition(':')
    composite = kop.strip().replace(" ", "").lower()
    body_lc = body.strip().lower()

    # 2️⃣ 💚 Isolatie vóór de eerste 'van', 'die' of 'dat'
    intro = re.split(r'\bvan\b|\bdie\b|\bdat\b', body_lc, maxsplit=1)[0]

    # 3️⃣ 💚 Pak laatste token als genus_word
    tokens = intro.strip().split()
    genus_word = tokens[-1] if tokens else ""

    # 4️⃣ 💚 Genus–check
    conflict = not composite.endswith(genus_word)

    # 5️⃣ 💚 Voorbeelden-override
    tekst_lc = definitie.lower()
    goed = [vb.lower() for vb in regel.get("goede_voorbeelden", [])]
    fout = [vb.lower() for vb in regel.get("foute_voorbeelden", [])]
    if any(g in tekst_lc for g in goed):
        return "✔️ SAM-04: consistent met samenstellende begrippen (volgens goed voorbeeld)"
    if any(f in tekst_lc for f in fout):
        return "❌ SAM-04: strijdig met samenstellende begrippen (volgens fout voorbeeld)"

    # Return op basis van genus-check
    if not conflict:
        return f"✔️ SAM-04: genus (‘{genus_word}’) sluit aan op compositie (‘{composite}’)"
    return f"❌ SAM-04: genus (‘{genus_word}’) komt niet overeen met compositie (‘{composite}’)"

# ✅ SAM-05: gebruikt dezelfde controle als ARAI06 maar focust enkel op cirkeldefinitie
def toets_SAM_05(definitie: str, regel: dict, begrip: str = None) -> str:
    """
    Controleert of de definitie een cirkeldefinitie is op basis van:
    - Herhaling van het begrip
    - Begrip gevolgd door verboden beginconstructie
    """
    woordenlijst = laad_verboden_woorden()
    definitie_gecorrigeerd = definitie.strip().lower()
    begrip_clean = begrip.strip().lower() if begrip else ""

    # 💚 Check op expliciete cirkeldefinitie zoals 'Begrip is ...'
    patroon_cirkel = rf"^{begrip_clean}\s+(" + "|".join(woordenlijst) + r")\b"
    expliciet_cirkel = re.search(patroon_cirkel, definitie_gecorrigeerd, flags=re.IGNORECASE)

    # 💚 Check op begrip elders in de tekst
    bevat_begrip = begrip_clean in definitie_gecorrigeerd

    if expliciet_cirkel:
        return "❌ SAM-05: definitie start met cirkeldefinitie (begrip gevolgd door verboden constructie)"
    if bevat_begrip:
        return f"❌ SAM-05: definitie bevat het begrip zelf ('{begrip_clean}'), mogelijke cirkeldefinitie"

    return "✔️ SAM-05: geen cirkeldefinitie herkend"

# ✅ Toetsing voor regel SAM-06 (Één synoniem krijgt voorkeur)
def toets_SAM_06(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    matches = set()
    for patroon in patronen:
        matches.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goed = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    fout = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not matches:
        if goed:
            return "✔️ SAM-06: duidelijke voorkeursbenaming, conform goed voorbeeld"
        return "✔️ SAM-06: geen synoniemgebruik herkend"

    if fout:
        return f"❌ SAM-06: mogelijke synoniemstructuur herkend ({', '.join(matches)}), lijkt op fout voorbeeld"
    if not goed:
        return f"❌ SAM-06: synoniemen herkend ({', '.join(matches)}), maar geen duidelijke voorkeursbenaming"

    return f"✔️ SAM-06: synoniemen correct gebruikt ({', '.join(matches)}) en goed voorbeeld herkend"


# ✅ Toetsing voor regel SAM-07 (Geen betekenisverruiming binnen definitie)
def toets_SAM_07(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    uitbreidingen = set()
    for patroon in patronen:
        uitbreidingen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goed = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    fout = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not uitbreidingen:
        if fout:
            return "❌ SAM-07: geen expliciete uitbreidingen gevonden, maar formulering lijkt op fout voorbeeld"
        return "✔️ SAM-07: geen uitbreidende elementen herkend"

    if goed:
        return f"✔️ SAM-07: uitbreiding(en) herkend ({', '.join(uitbreidingen)}), maar correct gebruikt zoals in goed voorbeeld"
    if fout:
        return f"❌ SAM-07: uitbreiding(en) herkend ({', '.join(uitbreidingen)}), en lijkt op fout voorbeeld"

    return f"❌ SAM-07: uitbreiding(en) herkend ({', '.join(uitbreidingen)}), zonder correcte toelichting"


# ✅ Toetsing voor regel SAM-08 (Synoniemen hebben één definitie)
def toets_SAM_08(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    verwijzingen = set()
    for patroon in patronen:
        verwijzingen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goed = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    fout = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not verwijzingen:
        if fout:
            return "❌ SAM-08: geen verwijzing gevonden maar formulering lijkt op fout voorbeeld"
        return "✔️ SAM-08: geen synoniemverwijzing herkend – mogelijk correct toegepast"

    if goed:
        return f"✔️ SAM-08: synoniemverwijzing(en) herkend ({', '.join(verwijzingen)}), correct toegepast"
    if fout:
        return f"❌ SAM-08: synoniemverwijzing(en) herkend ({', '.join(verwijzingen)}), maar formulering lijkt op fout voorbeeld"

    return f"❌ SAM-08: synoniemverwijzing(en) herkend ({', '.join(verwijzingen)}), maar zonder bevestiging via goed voorbeeld"


# ✅ Toetsing voor regel STR-01 (definitie start met zelfstandig naamwoord)
def toets_STR_01(definitie, regel):
    beginwoorden = regel.get("herkenbaar_patronen", [])
    fout_begin = [w for w in beginwoorden if re.match(w, definitie)]

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goed = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    fout = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if fout_begin:
        if fout:
            return f"❌ STR-01: definitie begint met werkwoord ({', '.join(fout_begin)}), en lijkt op fout voorbeeld"
        return f"❌ STR-01: definitie begint met werkwoord ({', '.join(fout_begin)})"

    if goed:
        return "✔️ STR-01: definitie start correct met zelfstandig naamwoord en komt overeen met goed voorbeeld"
    return "✔️ STR-01: geen werkwoordelijke start herkend – mogelijk goed geformuleerd"


# ✅ Toetsing voor regel STR-02 (Kick-off ≠ de term)
def toets_STR_02(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    herhalingen = set()
    for patroon in patronen:
        herhalingen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goed = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    fout = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if herhalingen:
        if fout:
            return f"❌ STR-02: kick-off term is herhaling van begrip ({', '.join(herhalingen)}), en lijkt op fout voorbeeld"
        return f"❌ STR-02: kick-off term is herhaling van begrip ({', '.join(herhalingen)})"

    if goed:
        return "✔️ STR-02: definitie start met breder begrip en komt overeen met goed voorbeeld"
    return "✔️ STR-02: geen herhaling van term herkend – mogelijk correct geformuleerd"

### ✅ Toetsing voor regel STR-03 (Definitie ≠ synoniem)
def toets_STR_03(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    synoniemen_gevonden = set()
    for patroon in patronen:
        synoniemen_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    uitleg_aanwezig = any(g.lower() in definitie.lower() for g in goede_voorbeelden)
    foute_aanwezig = any(f.lower() in definitie.lower() for f in foute_voorbeelden)

    if not synoniemen_gevonden:
        if uitleg_aanwezig:
            return "✔️ STR-03: geen synonieme formulering, komt overeen met goed voorbeeld"
        return "✔️ STR-03: geen synonieme formulering gevonden"

    if foute_aanwezig:
        return f"❌ STR-03: formulering lijkt synoniem ({', '.join(synoniemen_gevonden)}), komt overeen met fout voorbeeld"
    return f"❌ STR-03: formulering lijkt synoniem ({', '.join(synoniemen_gevonden)}), zonder verdere uitleg"

### ✅ Toetsing voor regel STR-04 (Kick-off vervolgen met toespitsing)
def toets_STR_04(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    match = any(re.search(patroon, definitie, re.IGNORECASE) for patroon in patronen)

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goed = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    fout = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if match:
        if goed:
            return "✔️ STR-04: kick-off gevolgd door correcte toespitsing"
        if fout:
            return "❌ STR-04: kick-off zonder toespitsing, komt overeen met fout voorbeeld"
        return "❌ STR-04: kick-off herkend, maar geen toespitsing aangetroffen"
    return "✔️ STR-04: geen algemene kick-off zonder toespitsing"

### ✅ Toetsing voor regel STR-05 (Definitie ≠ constructie)
def toets_STR_05(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    constructie_termen = set()
    for patroon in patronen:
        constructie_termen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goed = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    fout = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not constructie_termen:
        if goed:
            return "✔️ STR-05: geen constructieformulering en komt overeen met goed voorbeeld"
        return "✔️ STR-05: geen constructie-elementen gevonden"

    if fout:
        return f"❌ STR-05: formulering lijkt opsomming van onderdelen ({', '.join(constructie_termen)})"
    return f"❌ STR-05: mogelijke constructieformulering ({', '.join(constructie_termen)}), geen goede toelichting gevonden"

### ✅ Toetsing voor regel STR-06 (Essentie ≠ informatiebehoefte)
def toets_STR_06(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    info_termen = set()
    for patroon in patronen:
        info_termen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede = any(g.lower() in definitie.lower() for g in regel.get("goede_voorbeelden", []))
    fout = any(f.lower() in definitie.lower() for f in regel.get("foute_voorbeelden", []))

    if not info_termen:
        if goede:
            return "✔️ STR-06: geen informatiebehoefte, formulering volgt goed voorbeeld"
        return "✔️ STR-06: geen formuleringen die informatiebehoefte suggereren"

    if fout:
        return f"❌ STR-06: formuleringen suggereren informatiebehoefte ({', '.join(info_termen)}), lijkt op fout voorbeeld"
    return f"❌ STR-06: formuleringen suggereren informatiebehoefte ({', '.join(info_termen)}), zonder goede toelichting"

### ✅ Toetsing voor regel STR-07 (Geen dubbele ontkenning)
def toets_STR_07(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    dubbele_ontkenning = set()
    for patroon in patronen:
        dubbele_ontkenning.update(re.findall(patroon, definitie, re.IGNORECASE))

    foute = any(f.lower() in definitie.lower() for f in regel.get("foute_voorbeelden", []))

    if not dubbele_ontkenning:
        return "✔️ STR-07: geen dubbele ontkenning aangetroffen"

    if foute:
        return f"❌ STR-07: dubbele ontkenning herkend ({', '.join(dubbele_ontkenning)}), overeenkomend met fout voorbeeld"
    return f"❌ STR-07: dubbele ontkenning herkend ({', '.join(dubbele_ontkenning)}), controle nodig"

### ✅ Toetsing voor regel STR-08 (Dubbelzinnige 'en' is verboden)
def toets_STR_08(definitie, regel):
    import re

    # ── 1) Start met je JSON-patronen en breid uit met strikte regex voor "A, B en C" en "X en Y"
    patronen = list(regel.get("herkenbaar_patronen", [])) + [
        r"\b\w+,\s*\w+\s+en\s+\w+\b",   # bv. “A, B en C”
        r"\b\w+\s+en\s+\w+\b",          # bv. “X en Y”
    ]

    # ── 2) Match alle gevonden ‘en’-constructies
    en_vormen = set()
    for pat in patronen:
        en_vormen.update(re.findall(pat, definitie, re.IGNORECASE))

    # ── 3) Whitelist uitzonderingen (optioneel)
    whitelist = {
        "in en uitsluiting",
        "vraag en antwoord",
        "verificatie en bevestiging",
        # voeg hier meer vaste combinaties toe
    }
    en_vormen = {ev for ev in en_vormen if ev.lower() not in whitelist}

    # ── 4) Controle op goede/foute voorbeelden uit je JSON
    goed = any(
        vb.lower() in definitie.lower()
        for vb in regel.get("goede_voorbeelden", [])
    )
    fout = any(
        vb.lower() in definitie.lower()
        for vb in regel.get("foute_voorbeelden", [])
    )

    # ── 5) Beslis en retourneer resultaat
    if not en_vormen:
        return "✔️ STR-08: geen dubbelzinnige 'en'-constructies aangetroffen"
    if en_vormen and goed:
        return "✔️ STR-08: 'en' staat er wel, maar komt overeen met goed voorbeeld"
    if fout:
        return f"❌ STR-08: dubbelzinnige 'en' gevonden ({', '.join(en_vormen)}) en lijkt op fout voorbeeld"
    return f"❌ STR-08: dubbelzinnige 'en' gevonden ({', '.join(en_vormen)}), context verduidelijken"

### ✅ Toetsing voor regel STR-09 (Dubbelzinnige 'of' is verboden)
def toets_STR_09(definitie, regel):
    import re

    # ── 1) Combineer JSON-patronen met strikte regex voor "A, B of C" en "X of Y"
    patronen = list(regel.get("herkenbaar_patronen", [])) + [
        r"\b\w+,\s*\w+\s+of\s+\w+\b",   # bv. “A, B of C”
        r"\b\w+\s+of\s+\w+\b",          # bv. “X of Y”
    ]

    # ── 2) Verzamel alle gevonden ‘of’-constructies
    of_vormen = set()
    for pat in patronen:
        of_vormen.update(re.findall(pat, definitie, re.IGNORECASE))

    # ── 3) Whitelist uitzonderingen (optioneel)
    whitelist = {
        "en/of",
        "met of zonder",
        "al dan niet",   # voeg hier meer vaste combinaties toe
    }
    ambigue = {ov for ov in of_vormen if ov.lower() not in whitelist}

    # ── 4) Controle op goede/foute voorbeelden uit je JSON
    goed = any(
        vb.lower() in definitie.lower()
        for vb in regel.get("goede_voorbeelden", [])
    )
    fout = any(
        vb.lower() in definitie.lower()
        for vb in regel.get("foute_voorbeelden", [])
    )

    # ── 5) Beslis en retourneer resultaat
    if not ambigue:
        return "✔️ STR-09: geen dubbelzinnige 'of'-constructies aangetroffen"
    if ambigue and goed:
        return "✔️ STR-09: 'of'-constructie komt overeen met goed voorbeeld"
    if fout:
        return f"❌ STR-09: dubbelzinnige 'of' gevonden ({', '.join(ambigue)}) en lijkt op fout voorbeeld"
    return f"❌ STR-09: dubbelzinnige 'of' gevonden ({', '.join(ambigue)}), context verduidelijken"

### ✅ Toetsing voor regel VER-01 (Term in enkelvoud)

def toets_VER_01(term: str, regel: dict) -> str:
    """
    VER-01: term in enkelvoud, tenzij plurale tantum.
    Volgorde van checks:
      1. Uitzondering plurale tantum
      2. Expliciete foute voorbeelden
      3. Algemene meervoudscheck (term.endswith('en'))
      4. Expliciete goede voorbeelden
      5. Fallback enkelvoud
    """

    # 1️⃣ Uitzondering: plurale tantum  
    # ✅ Plurale tantum worden opgehaald via lookup.py  
    #    Hiermee vangen we woorden zoals “kosten” of “hersenen” op  
    if is_plurale_tantum(term):
        return "✔️ VER-01: term is plurale tantum (uitzondering)"

    # 2️⃣ Expliciete foute voorbeelden  
    # ✅ Deze lijst uit toetsregels.json krijgt prioriteit vóór de algemene meervoudscheck  
    for foute in regel.get("foute_voorbeelden", []):
        if term.lower() == foute.lower():
            return f"❌ VER-01: term '{term}' staat in lijst met foute voorbeelden"

    # 3️⃣ Algemene meervoudscheck  
    # ✅ Eenvoudige suffix-check (endswith 'en') is performant en voldoende voor de meeste zelfstandige naamwoorden  
    if term.lower().endswith("en"):
        return f"❌ VER-01: term in meervoud herkend ('{term}')"

    # 4️⃣ Expliciete goede voorbeelden  
    # ✅ Voor onregelmatige woorden die wel op “en” eindigen maar toch enkelvoudig bedoeld zijn  
    for goed in regel.get("goede_voorbeelden", []):
        if term.lower() == goed.lower():
            return "✔️ VER-01: term staat in lijst met goede voorbeelden"

    # 5️⃣ Fallback: enkelvoud  
    # ✅ Als geen van bovenstaande checks triggeren, is de term correct enkelvoudig  
    return "✔️ VER-01: term is enkelvoudig"

### ✅ Toetsing voor regel VER-02 (Definitie in enkelvoud)
### ✅ Toetsing voor regel VER-02 (Definitie in enkelvoud)
def toets_VER_02(definitie: str, regel: dict, term: str) -> str:
    """
    VER-02: definitie in enkelvoud, tenzij het begrip alleen meervoud kent.
      1️⃣ Uitzondering plurale tantum
      2️⃣ Expliciete foute voorbeelden (gewoon lemma-check)
      3️⃣ Expliciete goede voorbeelden
      4️⃣ Patronen voor meervoudsconstructies
      5️⃣ Fallback enkelvoud
    """
    # 🔧 Helper: normaliseer tekst (lowercase, verwijder alle niet-alfanumerieke karakters)
    def _normalize(text: str) -> str:
        txt = text.lower().strip()
        # ✅ Alles behalve letters en cijfers weg
        return re.sub(r"[^\w\s]", "", txt)

    # ✅ 1️⃣ Uitzondering: als term plurale tantum is, altijd OK
    if is_plurale_tantum(term):
        return "✔️ VER-02: definitie in enkelvoud (plurale tantum-uitzondering)"

    # 🧽 Genormaliseerde definitie-tekst voor voorbeeld-checks
    norm_def = _normalize(definitie)

    # ✅ 2️⃣ Expliciete foute voorbeelden vóórrang geven
    for fout in regel.get("foute_voorbeelden", []):
        if _normalize(fout) in norm_def:
            return "❌ VER-02: foute voorbeeldconstructie in definitie aangetroffen"

    # ✅ 3️⃣ Expliciete goede voorbeelden daarna honoreren
    for goed in regel.get("goede_voorbeelden", []):
        if _normalize(goed) in norm_def:
            return "✔️ VER-02: goede voorbeeldconstructie in definitie aangetroffen"

    # ✅ 4️⃣ Meervoudsconstructies detecteren via patronen
    for patroon in regel.get("herkenbaar_patronen", []):
        if re.search(patroon, definitie, re.IGNORECASE):
            return "❌ VER-02: meervoudige formulering herkend"

    # ✅ 5️⃣ Fallback: definitie is enkelvoudig
    return "✔️ VER-02: definitie is in enkelvoud geformuleerd"

### ✅ Toetsing voor regel VER-03 (Werkwoord-term in infinitief)
def toets_VER_03(term: str, regel: dict) -> str:
    """
    VER-03: werkwoord-term in infinitief.
      1️⃣ Expliciete foute voorbeelden → ❌
      2️⃣ Expliciete goede voorbeelden → ✔️
      3️⃣ Generieke vervoegingscheck via regex → ❌
      4️⃣ Fallback: eindigt op 'en' → infinitief → ✔️
      5️⃣ Anders: afwijkende vorm → ❌
    """
    # ✅ 1️⃣ Expliciete foute voorbeelden eerst (prioriteit)
    for foute in regel.get("foute_voorbeelden", []):
        # ✅ Vervoegde term komt exact overeen met foutvoorbeeld
        if term.lower() == foute.lower():
            return f"❌ VER-03: term '{term}' is vervoegd (fout voorbeeld)"

    # ✅ 2️⃣ Expliciete goede voorbeelden daarna
    for goed in regel.get("goede_voorbeelden", []):
        # ✅ One-to-one match met goed-voorbeeld
        if term.lower() == goed.lower():
            return "✔️ VER-03: term staat in lijst met goede voorbeelden"

    # ✅ 3️⃣ Generieke vervoegingscheck: detecteer eindigend op t of d via regex-patronen
    for patroon in regel.get("herkenbaar_patronen", []):
        # ✅ Gebruik re.fullmatch voor volledige term-match
        if re.fullmatch(patroon, term, re.IGNORECASE):
            return f"❌ VER-03: vervoegde vorm herkend ('{term}'), niet in infinitief"

    # ✅ 4️⃣ Fallback: eindigt op 'en' → typisch infinitief
    if term.lower().endswith("en"):
        return "✔️ VER-03: term is in infinitief (correct)"

    # ❓ 5️⃣ Anders: geen duidelijk patroon → waarschuwing
    return f"❌ VER-03: term '{term}' lijkt niet in infinitief te staan"


# ✅ Toetsing voor regel ARAI01 (geen werkwoord als kern)
# Deze regel controleert of de kern van de definitie een zelfstandig naamwoord is, en dus geen werkwoord.
# ➤ Vermijdt verwarring tussen concepten en handelingen. Werkwoorden maken de definitie vaag of procedureel.
# ➤ Herkent patronen als 'is', 'doet', 'vormt', etc. en vergelijkt met voorbeeldzinnen.
def toets_ARAI01(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    werkwoorden_gevonden = set()
    for patroon in patroon_lijst:
        werkwoorden_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede = regel.get("goede_voorbeelden", [])
    foute = regel.get("foute_voorbeelden", [])
    goed_aanwezig = any(g.lower() in definitie.lower() for g in goede)
    fout_aanwezig = any(f.lower() in definitie.lower() for f in foute)

    if not werkwoorden_gevonden:
        if goed_aanwezig:
            return "✔️ ARAI01: geen werkwoorden als kern, en goede formulering herkend"
        return "✔️ ARAI01: geen werkwoorden als kern gevonden in de definitie"

    if fout_aanwezig:
        return f"❌ ARAI01: werkwoord(en) als kern gevonden ({', '.join(werkwoorden_gevonden)}), lijkt op fout voorbeeld"
    return f"❌ ARAI01: werkwoord(en) als kern gevonden ({', '.join(werkwoorden_gevonden)}), geen toelichting herkend"

#✅ toets_ARAI02SUB1 – Lexicale containerbegrippen vermijden
def toets_ARAI02SUB1(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    container_termen = set()
    for patroon in patronen:
        container_termen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goed = any(g.lower() in definitie.lower() for g in regel.get("goede_voorbeelden", []))
    fout = any(f.lower() in definitie.lower() for f in regel.get("foute_voorbeelden", []))

    if not container_termen:
        if goed:
            return "✔️ ARAI02SUB1: geen lexicale containerbegrippen, definitie sluit aan bij goed voorbeeld"
        return "✔️ ARAI02SUB1: geen containerbegrippen aangetroffen"

    if fout:
        return f"❌ ARAI02SUB1: containerbegrippen gevonden ({', '.join(container_termen)}), zoals in fout voorbeeld"
    return f"❌ ARAI02SUB1: containerbegrippen gevonden ({', '.join(container_termen)}), onvoldoende concreet"

#✅ toets_ARAI02SUB2 – Ambtelijke containerbegrippen vermijden
def toets_ARAI02SUB2(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    container_termen = set()
    for patroon in patronen:
        container_termen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goed = any(g.lower() in definitie.lower() for g in regel.get("goede_voorbeelden", []))
    fout = any(f.lower() in definitie.lower() for f in regel.get("foute_voorbeelden", []))

    if not container_termen:
        if goed:
            return "✔️ ARAI02SUB2: geen ambtelijke containerbegrippen, definitie sluit aan bij goed voorbeeld"
        return "✔️ ARAI02SUB2: geen ambtelijke containerbegrippen aangetroffen"

    if fout:
        return f"❌ ARAI02SUB2: ambtelijke containerbegrippen gevonden ({', '.join(container_termen)}), zoals in fout voorbeeld"
    return f"❌ ARAI02SUB2: containerbegrippen gevonden ({', '.join(container_termen)}), onvoldoende specifiek"
# ✅ Toetsing voor regel ARAI02 (Vermijd vage containerbegrippen)
# Deze regel controleert of er vage containerbegrippen in de definitie staan zonder nadere specificatie.
# ➤ Containerwoorden als ‘proces’, ‘systeem’ of ‘aspect’ moeten gevolgd worden door concrete toelichting.
# ➤ Herkent patronen zoals ‘proces’ (zonder ‘dat/van’) en vergelijkt met goede en foute voorbeelden.
def toets_ARAI02(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    containers = set()
    for patroon in patroon_lijst:
        containers.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede = regel.get("goede_voorbeelden", [])
    foute = regel.get("foute_voorbeelden", [])
    goed_aanwezig = any(g.lower() in definitie.lower() for g in goede)
    fout_aanwezig = any(f.lower() in definitie.lower() for f in foute)

    if not containers:
        if goed_aanwezig:
            return "✔️ ARAI02: geen containerbegrippen zonder specificatie, komt overeen met goed voorbeeld"
        return "✔️ ARAI02: geen containerbegrippen zonder concretisering aangetroffen"

    if fout_aanwezig:
        return f"❌ ARAI02: containerbegrippen zonder specificatie gevonden ({', '.join(containers)}), lijkt op fout voorbeeld"
    return f"❌ ARAI02: containerbegrippen zonder specificatie gevonden ({', '.join(containers)}), onvoldoende concreet"

# ✅ Toetsing voor regel ARAI03 (Beperk subjectieve bijvoeglijke naamwoorden)
# Deze regel spoort subjectieve of contextgevoelige bijvoeglijke naamwoorden op die de objectiviteit verminderen.
# ➤ Vermijdt vage termen zoals ‘belangrijk’ of ‘adequaat’ die afbreuk doen aan de toetsbaarheid.
# ➤ Gebruikt herkenbare patronen en vergelijkt de formulering met voorbeelden.
def toets_ARAI03(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    bijvoeglijk = set()
    for patroon in patroon_lijst:
        bijvoeglijk.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede = regel.get("goede_voorbeelden", [])
    foute = regel.get("foute_voorbeelden", [])
    goed_aanwezig = any(g.lower() in definitie.lower() for g in goede)
    fout_aanwezig = any(f.lower() in definitie.lower() for f in foute)

    if not bijvoeglijk:
        if goed_aanwezig:
            return "✔️ ARAI03: geen subjectieve bijvoeglijke naamwoorden, komt overeen met goed voorbeeld"
        return "✔️ ARAI03: geen subjectieve bijvoeglijke naamwoorden aangetroffen"

    if fout_aanwezig:
        return f"❌ ARAI03: subjectieve bijvoeglijke naamwoorden gevonden ({', '.join(bijvoeglijk)}), lijkt op fout voorbeeld"
    return f"❌ ARAI03: subjectieve bijvoeglijke naamwoorden gevonden ({', '.join(bijvoeglijk)}), onvoldoende objectief"

# ✅ Toetsing voor regel ARAI04 (Vermijd modale hulpwerkwoorden)
# Deze regel controleert of modale werkwoorden worden gebruikt zoals 'kan', 'moet', 'zou'.
# ➤ Modale hulpwerkwoorden maken de definitie vaag en afhankelijk van context of intentie.
# ➤ Herkent bekende modale termen en vergelijkt met voorbeeldzinnen.
def toets_ARAI04(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    modalen = set()
    for patroon in patroon_lijst:
        modalen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede = regel.get("goede_voorbeelden", [])
    foute = regel.get("foute_voorbeelden", [])
    goed_aanwezig = any(g.lower() in definitie.lower() for g in goede)
    fout_aanwezig = any(f.lower() in definitie.lower() for f in foute)

    if not modalen:
        if goed_aanwezig:
            return "✔️ ARAI04: geen modale hulpwerkwoorden, komt overeen met goed voorbeeld"
        return "✔️ ARAI04: geen modale hulpwerkwoorden aangetroffen"

    if fout_aanwezig:
        return f"❌ ARAI04: modale hulpwerkwoorden gevonden ({', '.join(modalen)}), lijkt op fout voorbeeld"
    return f"❌ ARAI04: modale hulpwerkwoorden gevonden ({', '.join(modalen)}), niet geschikt voor heldere definitie"

#✅ toets_ARAI04SUB1 – Beperk gebruik van modale werkwoorden
def toets_ARAI04SUB1(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    modale_termen = set()
    for patroon in patronen:
        modale_termen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goed = any(g.lower() in definitie.lower() for g in regel.get("goede_voorbeelden", []))
    fout = any(f.lower() in definitie.lower() for f in regel.get("foute_voorbeelden", []))

    if not modale_termen:
        if goed:
            return "✔️ ARAI04SUB1: geen modale werkwoorden gevonden, definitie komt overeen met goed voorbeeld"
        return "✔️ ARAI04SUB1: geen modale werkwoorden aangetroffen in de definitie"

    if fout:
        return f"❌ ARAI04SUB1: modale werkwoorden herkend ({', '.join(modale_termen)}), zoals in fout voorbeeld"
    return f"❌ ARAI04SUB1: modale werkwoorden herkend ({', '.join(modale_termen)}), kan verwarring veroorzaken"


# ✅ Toetsing voor regel ARAI05 (Vermijd impliciete aannames)
# Deze regel detecteert formuleringen die verwijzen naar context of gewoonten zonder toelichting.
# ➤ Een definitie moet zelfstandig begrijpelijk zijn en mag geen impliciete voorkennis vereisen.
# ➤ Herkent patronen als ‘zoals bekend’ of ‘in het systeem’ en vergelijkt met voorbeeldzinnen.
def toets_ARAI05(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    aannames = set()
    for patroon in patroon_lijst:
        aannames.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede = regel.get("goede_voorbeelden", [])
    foute = regel.get("foute_voorbeelden", [])
    goed_aanwezig = any(g.lower() in definitie.lower() for g in goede)
    fout_aanwezig = any(f.lower() in definitie.lower() for f in foute)

    if not aannames:
        if goed_aanwezig:
            return "✔️ ARAI05: geen impliciete aannames gevonden, komt overeen met goed voorbeeld"
        return "✔️ ARAI05: geen impliciete aannames aangetroffen"

    if fout_aanwezig:
        return f"❌ ARAI05: impliciete aannames gevonden ({', '.join(aannames)}), lijkt op fout voorbeeld"
    return f"❌ ARAI05: impliciete aannames gevonden ({', '.join(aannames)}), onvoldoende duidelijk"


# ✅ Toetsing voor regel ARAI06 (Strikte startregels: geen lidwoord, geen werkwoord, geen herhaling)
# Deze regel controleert of de definitie voldoet aan de formele opbouwvereisten voor een correcte start.
# ➤ De definitie mag NIET starten met een lidwoord (‘de’, ‘het’, ‘een’).
# ➤ De definitie mag NIET beginnen met een koppelwerkwoord (‘is’, ‘omvat’, ‘betekent’).
# ➤ De definitie mag NIET het ingevoerde begrip (term) letterlijk herhalen.
# ➤ Dit voorkomt cirkeldefinities, formele slordigheid en contextloze fragmenten.



def toets_ARAI06(definitie: str, begrip: str) -> dict[str, str]:
    """
    Toets of de definitie NIET begint met verboden constructies:
     - vrije koppelwerkwoorden ('is', 'omvat', ...)
     - lidwoorden ('de', 'het', 'een')
     - cirkelconstructies ('begrip is', 'begrip verwijst naar', ...)
    Geeft een dict terug met:
        resultaat: True/False
        reden: toelichting of het patroon dat matchte
    """
    # 1) Normaliseer
    definitie_lower = definitie.strip().lower()

    # 2) Haal de lijst met verboden woorden op
    data = laad_verboden_woorden()
    verboden_lijst = data.get("verboden_woorden", []) if isinstance(data, dict) else []

    # 3) Genereer regex-patronen
    regex_lijst = genereer_verboden_startregex(begrip, verboden_lijst)

    # 4) Sorteer patronen op lengte (langste eerst) om overlap netjes af te handelen
    regex_lijst.sort(key=len, reverse=True)

    # 5) Match van alle patronen
    for patroon in regex_lijst:
        if re.match(patroon, definitie_lower, flags=re.IGNORECASE):
            return {
                "resultaat": False,
                "reden": f"Begint met verboden constructie: {patroon}"
            }

    # 6) Geen match → OK
    return {
        "resultaat": True,
        "reden": "✅ Geen opbouwfouten."
    }

# ✅ Hoofdfunctie: toetsing op alle regels met optionele extra context
# Deze functie doorloopt alle toetsregels en roept voor elke regel de centrale dispatcher aan.
# ➤ Nieuw: met logging wrapper (optioneel aan/uit te zetten via gebruik_logging=True)

def toets_definitie(definitie, regels, begrip=None, bronnen_gebruikt=None, contexten=None, gebruik_logging=False):
    """
    Voert alle toetsregels uit op de opgegeven definitie.

    ➤ Logging van individuele toetsresultaten is optioneel:
      • Gebruik gebruik_logging=True om uitgebreide logregels te krijgen
      • Logging omvat:
          - Toetsregel-ID
          - Triggerende patronen (indien aanwezig)
          - Resultaat ✔️ / ❌ / 🟡

    ➤ Speciaal gedrag voor bepaalde regels:
      - begrip is vereist bij o.a. SAM-05, ARAI06
      - bronnen_gebruikt is vereist bij CON-02
      - contexten is vereist bij CON-01
    """
    resultaten = []
    for regel_id, regel_data in regels.items():
        resultaat = toets_op_basis_van_regel(
            definitie,
            regel_id,
            regel_data,
            begrip=begrip,
            bronnen_gebruikt=bronnen_gebruikt,
            contexten=contexten
        )
        resultaten.append(resultaat)

        # 💚 Voeg loggingregel toe per resultaat
        if gebruik_logging:
            print(f"[LOG] Regel {regel_id}: {resultaat}")
            patronen = regel_data.get("herkenbaar_patronen", [])
            if patronen:
                gevonden = set()
                for patroon in patronen:
                    gevonden.update(re.findall(patroon, definitie, flags=re.IGNORECASE))
                if gevonden:
                    print(f"[LOG] → Triggerende patronen: {', '.join(sorted(gevonden))}")
                else:
                    print("[LOG] → Geen patronen getriggerd.")
            else:
                print("[LOG] → Geen herkenbare patronen gedefinieerd.")

    return resultaten

# ✅ Dispatcher: koppelt regel-ID's aan bijbehorende toetsfuncties
DISPATCHER = {
    "CON-01": toets_CON_01,
    "CON-02": toets_CON_02,
    "ESS-01": toets_ESS_01,
    "ESS-02": toets_ESS_02,
    "ESS-03": toets_ESS_03,
    "ESS-04": toets_ESS_04,
    "ESS-05": toets_ESS_05,
    "INT-01": toets_INT_01,
    "INT-02": toets_INT_02,
    "INT-03": toets_INT_03,
    "INT-04": toets_INT_04,
    "INT-06": toets_INT_06,
    "INT-07": toets_INT_07,
    "INT-08": toets_INT_08,
    "INT-09": toets_INT_09,
    "INT-10": toets_INT_10,
    "SAM-01": toets_SAM_01,
    "SAM-02": toets_SAM_02,
    "SAM-03": toets_SAM_03,
    "SAM-04": toets_SAM_04,
    "SAM-05": toets_SAM_05,
    "SAM-06": toets_SAM_06,
    "SAM-07": toets_SAM_07,
    "SAM-08": toets_SAM_08,
    "STR-01": toets_STR_01,
    "STR-02": toets_STR_02,
    "STR-03": toets_STR_03,
    "STR-04": toets_STR_04,
    "STR-05": toets_STR_05,
    "STR-06": toets_STR_06,
    "STR-07": toets_STR_07,
    "STR-08": toets_STR_08,
    "STR-09": toets_STR_09,
    "VER-01": toets_VER_01,
    "VER-02": toets_VER_02,
    "VER-03": toets_VER_03,
    "ARAI01": toets_ARAI01,
    "ARAI02": toets_ARAI02,
    "ARAI02SUB1": toets_ARAI02SUB1,
    "ARAI02SUB2": toets_ARAI02SUB2,
    "ARAI03": toets_ARAI03,
    "ARAI04": toets_ARAI04,
    "ARAI04SUB1": toets_ARAI04SUB1,
    "ARAI05": toets_ARAI05,
    "ARAI06": toets_ARAI06,
}

# ✅ Centrale dispatcher per regel met dynamische toewijzing
# Deze functie koppelt een toetsregel-ID aan de juiste toetsfunctie.
# Hij gebruikt de DISPATCHER dictionary om automatisch de juiste toetsfunctie aan te roepen.
#
# ➤ Sommige toetsfuncties vereisen een extra argument:
#     • `begrip`, bijvoorbeeld bij SAM-05 (controle op cirkeldefinities)
#     • `bronnen_gebruikt`, bijvoorbeeld bij CON-02 (controle op expliciete bronvermelding)
#
# ➤ De lijst `regels_met_begrip` bevat alle regels waarbij het begrip als extra argument nodig is.
# ➤ De lijst `regels_met_bronnen` bevat alle regels die extra input nodig hebben over bronnen.
#
# ➤ Voor deze speciale gevallen wordt de functie aangeroepen met:
#     functie(definitie, regel, begrip=..., bronnen_gebruikt=...)
#
# ➤ Alle fouten worden afgevangen zodat de app niet crasht bij ontbrekende of foutieve aanroepen.
# ➤ Als er geen toetsfunctie bekend is voor een regel-ID, wordt een waarschuwingsbericht getoond.

def toets_op_basis_van_regel(definitie, regel_id, regel, begrip=None, bronnen_gebruikt=None, contexten=None):
    """
    Routeert de definitie en metadata naar de juiste toetsfunctie op basis van het regel-ID.
    Ondersteunt extra argumenten zoals begrip (voor cirkeldefinities), bronnen (voor bronvermelding),
    en contexten (voor expliciete herhaling van organisatie of juridische termen).
    """

    functie = DISPATCHER.get(regel_id)
    if not functie:
        return f"🟡 {regel_id}: nog geen toetsfunctie geïmplementeerd"

    regels_met_begrip = {"SAM-05", "ARAI06"}
    regels_met_bronnen = {"CON-02"}
    regels_met_context = {"CON-01"}

    try:
        if regel_id in regels_met_begrip:
            return functie(definitie, regel, begrip=begrip)
        elif regel_id in regels_met_bronnen:
            return functie(definitie, regel, bronnen_gebruikt=bronnen_gebruikt)
        elif regel_id in regels_met_context:
            return functie(definitie, regel, contexten=contexten)
        else:
            return functie(definitie, regel)
    except Exception as e:
        return f"⚠️ {regel_id}: fout bij uitvoeren toetsfunctie – {e}"
        
# ✅ Voorbeeldgebruik
if __name__ == "__main__":
    regels = laad_toetsregels()
    test_definitie = "DJI is verantwoordelijk voor het detentiebeleid."
    uitslag = toets_definitie(test_definitie, regels)
    for r in uitslag:
        print(r)
