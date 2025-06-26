import os
import re
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
    contexten = contexten or {}
    definitie_lc = definitie.lower()
    expliciete_hits = []

    # 🟩 1. Controleer op expliciete herhaling van opgegeven contextwaarden
    for label, waarde in contexten.items():
        if not waarde:
            continue
        waarde_clean = waarde.lower().strip()

        # Herken ook afleidingen, zoals enkelvoud/meervoud of veelvoorkomende varianten
        varianten = {
            waarde_clean,
            waarde_clean + 'e',       # juridisch ➝ juridische
            waarde_clean + 'en',      # instantie ➝ instanties
            waarde_clean.rstrip('e')  # juridische ➝ juridisch
        }

        for variant in varianten:
            if variant and variant in definitie_lc:
                expliciete_hits.append(variant)

    if expliciete_hits:
        return f"❌ CON-01: opgegeven context(en) komen expliciet terug in de definitie → {', '.join(set(expliciete_hits))}"

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
def toets_CON_02(definitie, regel, bronnen_gebruikt=None):
    if not bronnen_gebruikt or not bronnen_gebruikt.strip():
        return "❌ CON-02: geen opgegeven bronnen gevonden (veld 'bronnen_gebruikt' is leeg of ontbreekt)"

    bronnen_lc = bronnen_gebruikt.lower()

    if any(kw in bronnen_lc for kw in ["artikel", "art.", "titel", "hoofdstuk", "lid", "paragraaf"]):
        return f"✔️ CON-02: bronvermelding aanwezig en voldoende specifiek → {bronnen_gebruikt.strip()}"

    elif any(kw in bronnen_lc for kw in ["wetboek", "avg", "wet", "beleidsregel", "richtlijn", "verordening"]):
        return f"🟡 CON-02: bronvermelding aanwezig ({bronnen_gebruikt.strip()}), maar mogelijk te algemeen"

    return f"❌ CON-02: bronvermelding gevonden ({bronnen_gebruikt.strip()}), maar niet herkend als authentiek of specifiek"


# ✅ Toetsing voor regel ESS-01 (Essentie, niet doel)
def toets_ESS_01(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    doelzinnen_gevonden = set()
    for patroon in patroon_lijst:
        doelzinnen_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goede_aanwezig = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    foute_aanwezig = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not doelzinnen_gevonden:
        if foute_aanwezig:
            return "❌ ESS-01: geen doelgerichte formuleringen gevonden, maar inhoud lijkt op fout voorbeeld"
        return "✔️ ESS-01: geen doelgerichte formuleringen aangetroffen in de definitie"

    if goede_aanwezig:
        return f"✔️ ESS-01: doelgerichte formuleringen herkend ({', '.join(doelzinnen_gevonden)}) en correct zoals goed voorbeeld"

    if foute_aanwezig:
        return f"❌ ESS-01: doelgerichte formuleringen gevonden ({', '.join(doelzinnen_gevonden)}), en lijkt op fout voorbeeld"

    return f"❌ ESS-01: doelgerichte formuleringen gevonden ({', '.join(doelzinnen_gevonden)}), zonder duidelijke toelichting"

# ✅ Toetsing voor regel ESS-02 (Type of instantie)
def toets_ESS_02(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    types_gevonden = set()
    for patroon in patroon_lijst:
        types_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goede_aanwezig = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    foute_aanwezig = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not types_gevonden:
        if foute_aanwezig:
            return "❌ ESS-02: geen type of instantie gevonden, en definitie lijkt op fout voorbeeld"
        return "❌ ESS-02: geen expliciet type of instantie herkend in de definitie"

    if goede_aanwezig:
        return f"✔️ ESS-02: type(n) herkend ({', '.join(types_gevonden)}) en correct uitgelegd"

    if foute_aanwezig:
        return f"❌ ESS-02: type(n) herkend ({', '.join(types_gevonden)}), maar lijkt op fout voorbeeld"

    return f"❌ ESS-02: type(n) herkend ({', '.join(types_gevonden)}), maar zonder duidelijke toelichting"

# ✅ Toetsing voor regel ESS-03 (Instanties uniek onderscheidbaar)
def toets_ESS_03(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    kenmerken_gevonden = set()
    for patroon in patroon_lijst:
        kenmerken_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goede_aanwezig = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    foute_aanwezig = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not kenmerken_gevonden:
        if foute_aanwezig:
            return "❌ ESS-03: geen unieke kenmerken gevonden, en lijkt op fout voorbeeld"
        return "❌ ESS-03: geen unieke of onderscheidende formuleringen gevonden"

    if goede_aanwezig:
        return f"✔️ ESS-03: unieke kenmerken gevonden ({', '.join(kenmerken_gevonden)}) en correct toegelicht"

    if foute_aanwezig:
        return f"❌ ESS-03: kenmerken gevonden ({', '.join(kenmerken_gevonden)}), maar lijkt op fout voorbeeld"

    return f"❌ ESS-03: kenmerken gevonden ({', '.join(kenmerken_gevonden)}), zonder duidelijke toelichting"

# ✅ Toetsing voor regel ESS-04 (Toetsbaarheid)
def toets_ESS_04(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    toetscriteria_gevonden = set()
    for patroon in patroon_lijst:
        toetscriteria_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goede_aanwezig = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    foute_aanwezig = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not toetscriteria_gevonden:
        if foute_aanwezig:
            return "❌ ESS-04: geen toetsbare elementen gevonden, en lijkt op fout voorbeeld"
        return "❌ ESS-04: geen toetsbare elementen herkend in de definitie"

    if goede_aanwezig:
        return f"✔️ ESS-04: toetsbare elementen herkend ({', '.join(toetscriteria_gevonden)}) en correct toegepast"

    if foute_aanwezig:
        return f"❌ ESS-04: toetsbare elementen gevonden ({', '.join(toetscriteria_gevonden)}), maar lijkt op fout voorbeeld"

    return f"❌ ESS-04: toetsbare elementen gevonden ({', '.join(toetscriteria_gevonden)}), zonder duidelijke toelichting"

# ✅ Toetsing voor regel ESS-05 (Voldoende onderscheidend)
def toets_ESS_05(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    onderscheidingen_gevonden = set()
    for patroon in patroon_lijst:
        onderscheidingen_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goede_aanwezig = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    foute_aanwezig = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not onderscheidingen_gevonden:
        if foute_aanwezig:
            return "❌ ESS-05: geen onderscheidende elementen en lijkt op fout voorbeeld"
        return "❌ ESS-05: geen onderscheidende formulering aangetroffen in de definitie"

    if goede_aanwezig:
        return f"✔️ ESS-05: onderscheidende elementen gevonden ({', '.join(onderscheidingen_gevonden)}) en correct toegepast"

    if foute_aanwezig:
        return f"❌ ESS-05: onderscheidende elementen gevonden ({', '.join(onderscheidingen_gevonden)}), maar lijkt op fout voorbeeld"

    return f"❌ ESS-05: onderscheidende elementen gevonden ({', '.join(onderscheidingen_gevonden)}), maar geen correcte uitleg of context gevonden"

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

# ✅ Toetsing voor regel INT-02 (Geen beslisregel)
def toets_INT_02(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    besliswoorden = set()
    for patroon in patroon_lijst:
        besliswoorden.update(re.findall(patroon, definitie, re.IGNORECASE))

    foute_voorbeelden_aanwezig = any(
        voorbeeld.lower() in definitie.lower()
        for voorbeeld in regel.get("foute_voorbeelden", [])
    )

    if not besliswoorden:
        return "✔️ INT-02: geen beslisregels of voorwaardelijke formuleringen aangetroffen"

    if foute_voorbeelden_aanwezig:
        return (
            f"❌ INT-02: beslisformuleringen gevonden ({', '.join(besliswoorden)}), "
            f"en komt overeen met fout voorbeeld"
        )
    else:
        return (
            f"❌ INT-02: beslisformuleringen gevonden ({', '.join(besliswoorden)}), "
            f"maar geen expliciet fout voorbeeld herkend"
        )

# ✅ Toetsing voor regel INT-03 (Voornaamwoord-verwijzing duidelijk)
def toets_INT_03(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    verwijzingen = set()
    for patroon in patroon_lijst:
        verwijzingen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    context_duidelijk = any(
        vb.lower() in definitie.lower()
        for vb in goede_voorbeelden
    )

    if not verwijzingen:
        return "✔️ INT-03: geen voornaamwoord-verwijzingen aangetroffen"

    if context_duidelijk:
        return f"✔️ INT-03: voornaamwoorden gevonden ({', '.join(verwijzingen)}), maar duidelijk verwezen"
    else:
        return f"❌ INT-03: voornaamwoorden gevonden ({', '.join(verwijzingen)}), maar onduidelijk waarnaar verwezen wordt"

# ✅ Toetsing voor regel INT-04 (Lidwoord-verwijzing duidelijk)
def toets_INT_04(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    verwijzingen = set()
    for patroon in patroon_lijst:
        verwijzingen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    context_duidelijk = any(
        vb.lower() in definitie.lower()
        for vb in goede_voorbeelden
    )

    if not verwijzingen:
        return "✔️ INT-04: geen onduidelijke lidwoord-verwijzingen aangetroffen"

    if context_duidelijk:
        return f"✔️ INT-04: lidwoorden gevonden ({', '.join(verwijzingen)}), maar context voldoende duidelijk"
    else:
        return f"❌ INT-04: lidwoorden gevonden ({', '.join(verwijzingen)}), context mogelijk onduidelijk"

# ✅ Toetsing voor regel INT-06 (Definitie bevat geen toelichting)
def toets_INT_06(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    toelichting_gevonden = set()
    for patroon in patroon_lijst:
        toelichting_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    foute_voorbeelden = regel.get("foute_voorbeelden", [])
    foute_aanwezig = any(
        vb.lower() in definitie.lower()
        for vb in foute_voorbeelden
    )

    if not toelichting_gevonden:
        return "✔️ INT-06: geen toelichtende elementen in de definitie"

    if foute_aanwezig:
        return (
            f"❌ INT-06: toelichtende elementen gevonden ({', '.join(toelichting_gevonden)}), "
            f"en lijkt op fout voorbeeld"
        )
    else:
        return f"❌ INT-06: toelichtende elementen gevonden ({', '.join(toelichting_gevonden)}), maar geen expliciet fout voorbeeld herkend"

# ✅ Toetsing voor regel INT-07 (afkortingen)
def toets_INT_07(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    afkortingen_gevonden = set()
    for patroon in patroon_lijst:
        afkortingen_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    uitleg_aanwezig = any(uitleg.lower() in definitie.lower() for uitleg in goede_voorbeelden)
    foute_uitleg_aanwezig = any(fout.lower() in definitie.lower() for fout in foute_voorbeelden)

    if not afkortingen_gevonden:
        if uitleg_aanwezig:
            return "✅ INT-07: geen afkortingen gevonden, definitie komt overeen met goed voorbeeld"
        return "✅ INT-07: geen afkortingen gevonden in de definitie"

    if uitleg_aanwezig:
        return f"✅ INT-07: afkortingen gevonden ({', '.join(afkortingen_gevonden)}) en correct toegelicht"

    if foute_uitleg_aanwezig:
        return f"❌ INT-07: afkortingen gevonden ({', '.join(afkortingen_gevonden)}), maar formulering lijkt op fout voorbeeld"

    return f"❌ INT-07: afkortingen gevonden ({', '.join(afkortingen_gevonden)}), maar geen toelichting of verwijzing gevonden"

# ✅ Toetsing voor regel INT-08 (Positieve formulering)
def toets_INT_08(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    negatieve_vormen = set()
    for patroon in patroon_lijst:
        negatieve_vormen.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    uitleg_aanwezig = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    foute_aanwezig = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not negatieve_vormen:
        if uitleg_aanwezig:
            return "✅ INT-08: geen negatieve formuleringen en komt overeen met goed voorbeeld"
        return "✅ INT-08: definitie bevat geen negatieve formuleringen"

    if uitleg_aanwezig:
        return f"✅ INT-08: negatieve termen ({', '.join(negatieve_vormen)}) gevonden, maar correct geformuleerd"

    if foute_aanwezig:
        return f"❌ INT-08: negatieve termen ({', '.join(negatieve_vormen)}) gevonden, lijkt op fout voorbeeld"

    return f"❌ INT-08: negatieve termen ({', '.join(negatieve_vormen)}) gevonden, zonder duidelijke uitleg"

# ✅ Toetsing voor regel INT-09 (Opsomming is limitatief)
def toets_INT_09(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    opsommingen_gevonden = set()
    for patroon in patroon_lijst:
        opsommingen_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    uitleg_aanwezig = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    foute_aanwezig = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not opsommingen_gevonden:
        if uitleg_aanwezig:
            return "✅ INT-09: geen opsommingen, definitie komt overeen met goed voorbeeld"
        return "✅ INT-09: geen opsommingen gevonden in de definitie"

    if uitleg_aanwezig:
        return f"✅ INT-09: opsommingen ({', '.join(opsommingen_gevonden)}) correct als limitatief verwoord"

    if foute_aanwezig:
        return f"❌ INT-09: opsommingen ({', '.join(opsommingen_gevonden)}) lijken op fout voorbeeld"

    return f"❌ INT-09: opsommingen ({', '.join(opsommingen_gevonden)}) gevonden, maar zonder duidelijke toelichting"

# ✅ Toetsing voor regel INT-10 (Geen ontoegankelijke achtergrondkennis nodig)
def toets_INT_10(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    verwijzingen_gevonden = set()
    for patroon in patroon_lijst:
        verwijzingen_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    uitleg_aanwezig = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    foute_aanwezig = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not verwijzingen_gevonden:
        if uitleg_aanwezig:
            return "✅ INT-10: geen ontoegankelijke verwijzingen en komt overeen met goed voorbeeld"
        return "✅ INT-10: geen ontoegankelijke of impliciete achtergrondverwijzingen gevonden"

    if uitleg_aanwezig:
        return f"✅ INT-10: verwijzingen ({', '.join(verwijzingen_gevonden)}) zijn voldoende verklaard"

    if foute_aanwezig:
        return f"❌ INT-10: verwijzingen ({', '.join(verwijzingen_gevonden)}) gevonden, formulering lijkt op fout voorbeeld"

    return f"❌ INT-10: verwijzingen ({', '.join(verwijzingen_gevonden)}) gevonden, zonder uitleg of toelichting"

#✅ Toetsing voor regel SAM-01 (Kwalificatie leidt niet tot afwijking)
def toets_SAM_01(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    kwalificaties_gevonden = set()
    for patroon in patroon_lijst:
        kwalificaties_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    if not kwalificaties_gevonden:
        return "✔️ SAM-01: geen afwijkende kwalificaties aangetroffen in de definitie"

    uitleg_aanwezig = any(
        voorbeeld.lower() in definitie.lower()
        for voorbeeld in regel.get("goede_voorbeelden", [])
    )

    if uitleg_aanwezig:
        return f"✔️ SAM-01: kwalificaties ({', '.join(kwalificaties_gevonden)}) zijn correct toegepast zoals in goede voorbeelden"
    else:
        return f"❌ SAM-01: kwalificaties ({', '.join(kwalificaties_gevonden)}) kunnen afwijken van gebruikelijke betekenis"

#✅ Toetsing voor regel SAM-02 (Kwalificatie omvat geen herhaling)
def toets_SAM_02(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    herhalingen = set()
    for patroon in patroon_lijst:
        herhalingen.update(re.findall(patroon, definitie, re.IGNORECASE))

    if not herhalingen:
        return "✔️ SAM-02: geen herhalingen van de term of elementen ervan in de definitie"

    uitleg_aanwezig = any(
        voorbeeld.lower() in definitie.lower()
        for voorbeeld in regel.get("goede_voorbeelden", [])
    )

    if uitleg_aanwezig:
        return f"✔️ SAM-02: herhaling(en) ({', '.join(herhalingen)}) zijn betekenisvol gebruikt"
    else:
        return f"❌ SAM-02: overbodige herhaling(en) gevonden in definitie ({', '.join(herhalingen)})"

#✅ Toetsing voor regel SAM-03 (Definitieteksten niet nesten)
def toets_SAM_03(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    nesten = set()
    for patroon in patroon_lijst:
        nesten.update(re.findall(patroon, definitie, re.IGNORECASE))

    if not nesten:
        return "✔️ SAM-03: geen geneste of verweven definities aangetroffen"

    uitleg_aanwezig = any(
        voorbeeld.lower() in definitie.lower()
        for voorbeeld in regel.get("goede_voorbeelden", [])
    )

    if uitleg_aanwezig:
        return f"✔️ SAM-03: verwijzingen ({', '.join(nesten)}) correct gebruikt"
    else:
        return f"❌ SAM-03: definitie bevat geneste verwijzingen ({', '.join(nesten)}), liever afzonderlijk definiëren"

# ✅ Toetsing voor regel SAM-04 (Begrip-samenstelling strijdt niet met samenstellende begrippen)
# Deze toets controleert of de definitie van een samengesteld begrip niet in tegenspraak is
# met de betekenis van de samenstellende begrippen. Het gebruikt regex-patronen om conflicten
# zoals "geen X" of "niet van toepassing op Y" te detecteren, en vergelijkt de formulering
# met bekende foute en goede voorbeelden om semantische inconsistentie op te sporen.
def toets_SAM_04(definitie, regel):
    patroon_lijst = regel.get("herkenbaar_patronen", [])
    conflicten_gevonden = set()
    for patroon in patroon_lijst:
        conflicten_gevonden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goede_voorbeelden = regel.get("goede_voorbeelden", [])
    foute_voorbeelden = regel.get("foute_voorbeelden", [])

    goede_aanwezig = any(vb.lower() in definitie.lower() for vb in goede_voorbeelden)
    foute_aanwezig = any(vb.lower() in definitie.lower() for vb in foute_voorbeelden)

    if not conflicten_gevonden:
        if goede_aanwezig:
            return "✔️ SAM-04: geen semantisch conflict gevonden – consistent met samenstellende begrippen zoals bij goed voorbeeld"
        return "✔️ SAM-04: geen conflictieve formuleringen aangetroffen – mogelijk correct gedefinieerd"

    if foute_aanwezig:
        return (
            f"❌ SAM-04: mogelijk conflict tussen begrip en deelbegrippen herkend "
            f"({', '.join(conflicten_gevonden)}), en lijkt sterk op fout voorbeeld"
        )

    return (
        f"❌ SAM-04: potentieel conflict gevonden tussen begrip en samenstellende delen "
        f"({', '.join(conflicten_gevonden)}), zonder duidelijke toelichting of verantwoording"
    )

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
    Breidt uit met check op expliciete goede en foute voorbeelden.
    """
    # 1️⃣ Uitzondering: plurale tantum
    if is_plurale_tantum(term):
        return "✔️ VER-01: term is plurale tantum (uitzondering)"

    # 2️⃣ Expliciete foute voorbeelden?
    for foute in regel.get("foute_voorbeelden", []):
        if term.lower() == foute.lower():
            return f"❌ VER-01: term '{term}' staat in lijst met foute voorbeelden"

    # 3️⃣ Expliciete goede voorbeelden?
    for goed in regel.get("goede_voorbeelden", []):
        if term.lower() == goed.lower():
            return "✔️ VER-01: term staat in lijst met goede voorbeelden"

    # 4️⃣ Regex-patronen op de ingevoerde term
    patronen = regel.get("herkenbaar_patronen", [])
    meervoudig = set()
    for patroon in patronen:
        meervoudig.update(re.findall(patroon, term, re.IGNORECASE))

    if not meervoudig:
        return "✔️ VER-01: term is enkelvoudig"
    gevonden = ", ".join(sorted(meervoudig))
    return f"❌ VER-01: term in meervoud herkend ({gevonden})"

### ✅ Toetsing voor regel VER-02 (Definitie in enkelvoud)
def toets_VER_02(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    meervoudig = set()
    for patroon in patronen:
        meervoudig.update(re.findall(patroon, definitie, re.IGNORECASE))

    goed = any(g.lower() in definitie.lower() for g in regel.get("goede_voorbeelden", []))
    fout = any(f.lower() in definitie.lower() for f in regel.get("foute_voorbeelden", []))

    if not meervoudig:
        return "✔️ VER-02: definitie is enkelvoudig geformuleerd"
    if fout:
        return f"❌ VER-02: meervoudsvorm herkend ({', '.join(meervoudig)}), zoals in fout voorbeeld"
    return f"❌ VER-02: meervoudsvorm herkend ({', '.join(meervoudig)}), eenduidigheid controleren"

### ✅ Toetsing voor regel VER-03 (Werkwoord-term in infinitief)
def toets_VER_03(definitie, regel):
    patronen = regel.get("herkenbaar_patronen", [])
    werkwoorden = set()
    for patroon in patronen:
        werkwoorden.update(re.findall(patroon, definitie, re.IGNORECASE))

    goed = any(g.lower() in definitie.lower() for g in regel.get("goede_voorbeelden", []))
    fout = any(f.lower() in definitie.lower() for f in regel.get("foute_voorbeelden", []))

    if not werkwoorden:
        return "✔️ VER-03: werkwoordterm correct in infinitief"
    if fout:
        return f"❌ VER-03: vervoegde vorm gevonden ({', '.join(werkwoorden)}), zoals in fout voorbeeld"
    return f"❌ VER-03: werkwoord niet in infinitief ({', '.join(werkwoorden)}), controle nodig"


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
