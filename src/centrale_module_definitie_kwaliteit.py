# ================================
# 📦 IMPORTS EN INITIALISATIE
# ================================
import os
import json
import re
from datetime import datetime
import streamlit as st
# 📌 Streamlit pagina-configuratie
st.set_page_config(page_title="DefinitieAgent", page_icon="🧠")

import pandas as pd




from dotenv import load_dotenv

from voorbeelden.voorbeelden import (
    genereer_voorbeeld_zinnen,
    genereer_praktijkvoorbeelden,
    genereer_tegenvoorbeelden
)
from ai_toetser import toets_definitie
from log.log_definitie import log_definitie, get_logger

# --- ⚙️ Config-loaders en verboden-woordenbeheer ---
# ✅ Centrale JSON-loader
from config.config_loader import laad_toetsregels, laad_verboden_woorden
# ✅ Eén keer importeren van verboden-woorden functies
from config.verboden_woorden import (
    sla_verboden_woorden_op,    # ✅ slaat gewijzigde lijst op
    log_test_verboden_woord     # ✅ logt individuele woordtests
)
from definitie_generator.generator import genereer_definitie  # de centrale definitiegenerator

from prompt_builder.prompt_builder import (
    stuur_prompt_naar_gpt,
)

logger = get_logger(__name__)
load_dotenv()



# ================================
# 🧱 NIEUWE PROMPTFUNCTIE: GESCHEIDEN RICHTLIJNEN (VERSTERKT)
# ================================
# ✅ Deze versie bevat:
#    • Heldere context en richtlijnen (verplicht vs. aanvullend)
#    • Strikte verbodsbepalingen voor herhaling/koppelwerkwoorden
#    • Slotinstructie: alleen de definitie in één zin geven
#    • Extra waarschuwingsblok om GPT scherp te houden

# ================================
# ✅ VALIDATIEMATRIX – Promptopbouw en foutafdekking
# ================================
# Deze prompt is structureel opgebouwd om typische fouten te voorkomen die GPT maakt bij definitiegeneratie.
# De onderstaande matrix toont welke valkuilen expliciet worden afgevangen in de prompttekst zelf.
#
# | Probleem                      | Afgedekt in prompt? | Toelichting                                                                 |
# |-------------------------------|---------------------|------------------------------------------------------------------------------|
# | ❌ Start met “proces waarbij” | ✅                  | Verboden via: “vermijd abstracte constructies zoals ‘proces waarbij’...”    |
# | ❌ Gebruik van het begrip     | ✅                  | Verboden via: “je mag het begrip niet herhalen, parafraseren of...”         |
# | ❌ Koppelwerkwoorden          | ✅                  | Verboden aan het begin: “is”, “betekent”, “omvat” enz.                       |
# | ❌ Lidwoorden aan het begin   | ✅                  | Verboden: “de”, “het”, “een”                                                |
# | ❌ Organisaties of afkortingen| ✅                  | Verboden tenzij strikt noodzakelijk: “de KMAR”, “OM” enz.                   |
# | ❌ Letterlijke contextvermelding| ✅                | Verboden: “in de context van...”, “op basis van...”, “volgens de...”        |
# | ❌ Subjectieve bijvoeglijkheid| ✅                  | Verboden: “essentieel”, “belangrijk”, “relevant”                             |
# | ❌ Toelichting of inleiding   | ✅                  | Verboden via instructie “géén toelichting, géén inleiding”                   |
#
# Deze matrix wordt automatisch bijgewerkt zodra de prompt wordt aangepast — wijzigingen moeten ook hierin zichtbaar blijven.
#
#def bouw_prompt_met_gesplitste_richtlijnen(
#    begrip: str,
#    context: str,
#    juridische_context: str,
#    wettelijke_basis: str,
#    web_uitleg: str,
#    regels_essentieel: list,
#    regels_aanvullend: list
#) -> str:
#    """
#    Genereert een GPT-prompt met gescheiden instructieblokken:
#    - Essentiële toetsregels (prioriteit: hoog, verplicht)
#    - Aanvullende richtlijnen (advies, informatief)
#    - Verboden patronen (taalkundig en inhoudelijk)
#    """

    # 🧠 Introductie en rolopdracht
#    prompt = (
#        "Je bent een expert in het opstellen van beleidsmatige definities voor overheidsgebruik.\n"
#        "Je taak is om een duidelijke, zakelijke definitie te formuleren voor het opgegeven begrip.\n"
#    )

    # 📌 Contextuele kaders opnemen
#    beleid_context = []
#    if context:
#        beleid_context.append(f"binnen {context}")
#    if juridische_context:
#        beleid_context.append(f"in een {juridische_context.lower()} context")
#    if wettelijke_basis:
#        beleid_context.append(f"met als wettelijke basis {wettelijke_basis}")
#    if beleid_context:
#        prompt += f"\n📌 De definitie wordt opgesteld {' en '.join(beleid_context)}.\n"#

    # ✅ Verplichte kwaliteitscriteria
#    if regels_essentieel:
#        prompt += "\n✅ De definitie moet voldoen aan deze verplichte kwaliteitseisen:\n"
#        for regel in regels_essentieel:
#            prompt += f"- {regel['id']}: {regel['uitleg']}\n"#

    # 💡 Aanvullende richtlijnen
#    if regels_aanvullend:
#        prompt += "\n💡 Aanvullende richtlijnen om rekening mee te houden:\n"
#        for regel in regels_aanvullend:
#            prompt += f"- {regel['id']}: {regel['uitleg']}\n"

    # 📎 Achtergrondinformatie (alleen als referentie)
#    prompt += (
#        "\n📎 Gebruik onderstaande achtergrondinformatie slechts als referentie. Neem niets letterlijk over:\n"
#        f"{web_uitleg}\n"
#    )

#    # 🚫 Veelgemaakte fouten (versterkt met contextspecifiek verbod)
#    prompt += (
#        "\n🚫 Veelgemaakte fouten (vermijden!):\n"
#        "- Begin de zin NIET met het begrip zelf (bijv. 'Identiteitsvaststelling is...')\n"
#        "- Gebruik GEEN koppelwerkwoorden aan het begin (zoals 'is', 'omvat', 'betekent')\n"
#        "- Begin de zin NIET met een lidwoord ('de', 'het', 'een')\n"
#        "- Vermijd abstracte constructies zoals 'proces waarbij', 'handeling die', 'vorm van'\n"
#        "- ❌ Noem GEEN context, wet of organisatie letterlijk in de definitie (zoals 'de KMAR', 'het OM', 'op basis van de AVG')\n"
#        "- ❌ Gebruik GEEN formuleringen zoals: 'binnen de context van...', 'in het kader van...', 'volgens de...'\n"
#        "- ❌ Noem GEEN organisaties of afkortingen (zoals 'de KMAR', 'het OM') tenzij absoluut noodzakelijk voor de betekenis.\n"
#        "- Vermijd subjectieve termen als 'essentieel', 'belangrijk', 'relevant'\n"
#        "- Gebruik geen opsommingen, bijzinnen of vage formuleringen\n"
#    )

#    # ✏️ Slotinstructie: scherpe afsluiting
#    prompt += (
#        "\n✏️ FORMULEER ÉÉN ENKELE ZIN die voldoet aan ALLE bovenstaande instructies.\n"
#        "⚠️ Je mag het begrip niet herhalen, parafraseren of gebruiken aan het begin van de zin.\n"
#       "💬 Geef alleen de definitie. Geen toelichting, geen inleiding.\n"
#        f"\nBegrip: {begrip}"
#    )

#    return prompt


# ================================
# 🧩 TOELICHTING GENEREREN
# ================================
# Genereert een toelichtende tekst over de betekenis en toepassing van het begrip.
def genereer_toelichting(begrip, context=None, juridische_context=None, wettelijke_basis=None):
    prompt = (
        f"Geef een korte toelichting op de betekenis en toepassing van het begrip '{begrip}', zoals het zou kunnen voorkomen in overheidsdocumenten.\n"
        f"Gebruik de contexten hieronder alleen als achtergrond en noem ze niet letterlijk:\n\n"
        f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
        f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
        f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
    )
    return stuur_prompt_naar_gpt(prompt, temperatuur=0.3)


# ================================
# 🔁 SYNONIEMEN GENEREREN
# ================================
# Genereert een lijst van max. 5 synoniemen binnen beleidsmatige context.
def genereer_synoniemen(begrip, context=None, juridische_context=None, wettelijke_basis=None):
    prompt = (
        f"Geef maximaal 5 synoniemen voor het begrip '{begrip}', relevant binnen de context van overheidsgebruik.\n"
        f"Gebruik onderstaande contexten als achtergrond. Geef de synoniemen als een lijst, zonder toelichting:\n\n"
        f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
        f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
        f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
    )
    return stuur_prompt_naar_gpt(prompt, temperatuur=0.2, max_tokens=150)



# ================================
# 🔁 ANTONIEMEN GENEREREN
# ================================
# Genereert een lijst van max. 5 antoniemen binnen beleidsmatige context.
def genereer_antoniemen(begrip, context=None, juridische_context=None, wettelijke_basis=None):
    prompt = (
        f"Geef maximaal 5 antoniemen voor het begrip '{begrip}', binnen de context van overheidsgebruik.\n"
        f"Gebruik onderstaande contexten alleen als achtergrond. Geef de antoniemen als een lijst, zonder toelichting:\n\n"
        f"Organisatorische context: {', '.join(context_dict.get('organisatorisch', [])) or 'geen'}\n"
        f"Juridische context:      {', '.join(context_dict.get('juridisch', [])) or 'geen'}\n"
        f"Wettelijke basis:        {', '.join(context_dict.get('wettelijk', [])) or 'geen'}"
    )
    return stuur_prompt_naar_gpt(prompt, temperatuur=0.2, max_tokens=150)


# ================================
# 📊 PARSE FUNCTIE TOETSRESULTATEN
# ================================
# Zet een lijst van toetsresultaten om naar een dict met sleutel "Regel X".
# Wordt bijvoorbeeld gebruikt voor visuele weergave in tabellen.
#def parse_toetsing_regels(toetsing_lijst):
#    regels_dict = {}
#    for i, regel in enumerate(toetsing_lijst, 1):
#        kolomnaam = f"Regel {i}"
#        regels_dict[kolomnaam] = regel
#    return regels_dict
    
    
# ================================
# 📥 TOETSREGELS LADEN EN TONEN
# ================================
# Laadt de toetsregels vanuit het JSON-bestand via 'laad_toetsregels()', en toont
# de regels met prioriteit 'hoog' of 'midden' bovenin de interface. Deze regels worden
# automatisch gebruikt in de promptopbouw en AI-toetsing van definities.
# Dit blok moet vóór de Streamlit-interface staan zodat 'toetsregels' beschikbaar is.

#def selecteer_richtlijnen(toetsregels):
#    return "\n".join([
#        f"- {r['id']}: {r['uitleg']}"
#        for r in toetsregels.values()
#        if r.get("prioriteit") == "hoog" and r.get("aanbeveling") == "verplicht"
#    ])

#st.write("✅ main() gestart")
toetsregels = laad_toetsregels()
#st.write("📥 Toetsregels geladen")

#with st.expander("📏 Toetsregels meegenomen in de definitie-opbouw", expanded=False, key="expander_toetsregels_prompt"):
#    st.markdown(selecteer_richtlijnen(toetsregels))

# ✅ Import aangepast: lookup.py zit in /src/web_lookup/, dus juiste modulepad is web_lookup.lookup
# ✅ Import aangepast: lookup.py zit in /src/web_lookup/, dus juiste modulepad is web_lookup.lookup
# ✅ Correcte import van de centrale routerfunctie
from web_lookup.lookup import lookup_definitie as zoek_definitie  # ✅ alias voor consistentie in bestaande code
# ✅ Hiermee blijft de rest van het script bruikbaar zonder extra aanpassingen
# ================================
# 🖥️ STREAMLIT INTERFACE
# ================================
st.write("🧾 Definitie Kwaliteit")
begrip = st.text_input("Voer een term in waarvoor een definitie moet worden gegenereerd")

lookup_resultaten = []

# ✅ Voer alleen lookup uit als gebruiker op knop heeft geklikt
if st.session_state.get("definitie_actie", False) and begrip.strip():
    lookup_resultaten = zoek_definitie(begrip)
    st.session_state["lookup_uitgevoerd"] = True  # ✅ Markeer dat lookup heeft plaatsgevonden

# ✅ Organisatorische context
# ✅ Multiselect-widget: altijd key instellen én initialiseren
contextopties = st.multiselect(
    "Organisatorische context (meerdere mogelijk)",
    [
        "OM", "ZM", "Reclassering", "DJI", "NP", "Justid", "KMAR", "FIOD",
        "CJIB", "Strafrechtketen", "Migratieketen", "Justitie en Veiligheid", "Anders..."
    ],
    default=st.session_state.get("keuze_organisatorische_context", []),
    key="keuze_organisatorische_context"
)

# ✅ Veilig: toegang altijd via get() om KeyError te voorkomen
geselecteerd = st.session_state.get("keuze_organisatorische_context", [])

# ✅ Stap 2: extra input tonen als "Anders..." is gekozen
extra_input = ""
if "Anders..." in geselecteerd:
    extra_input = st.text_input(
        "Voer aanvullende organisatorische context in",
        value=st.session_state.get("custom_organisatorische_context_input", "").strip(),
        key="custom_organisatorische_context_input",
        placeholder="Bijv. 'project NWvSv'"
    )

# ✅ Stap 3: visuele chipsweergave
contextchips = [opt for opt in geselecteerd if opt != "Anders..."]
if extra_input:
    contextchips.append(extra_input)

st.markdown("**Gekozen organisatorische context(en):**")
st.markdown(", ".join(contextchips))

# ✅ Stap 4: volledige context verzamelen
contexten_compleet = [opt for opt in geselecteerd if opt != "Anders..."]
extra = st.session_state.get("custom_organisatorische_context_input", "").strip()
if extra:
    contexten_compleet.append(extra)

context = contexten_compleet  # ✅ Deze lijst is nu veilig en volledig
    
# ✅ Juridische context
juridische_opties = st.multiselect(
    "Juridische context (meerdere mogelijk)",
    [
        "Strafrecht",
        "Civiel recht",
        "Bestuursrecht",
        "Internationaal recht",
        "Anders..."
    ],
    default=st.session_state.get("keuze_juridische_context", []),
    key="keuze_juridische_context"
)

# ✅ Veilig ophalen
geselecteerd_juridisch = st.session_state.get("keuze_juridische_context", [])

# ✅ Extra input bij 'Anders...'
extra_juridisch = ""
if "Anders..." in geselecteerd_juridisch:
    extra_juridisch = st.text_input(
        "Voer aanvullende juridische context in",
        value=st.session_state.get("custom_juridische_context_input", "").strip(),
        key="custom_juridische_context_input",
        placeholder="Bijv. 'militair strafrecht'"
    )

# ✅ Chipsweergave
juridische_chips = [opt for opt in geselecteerd_juridisch if opt != "Anders..."]
if extra_juridisch:
    juridische_chips.append(extra_juridisch)

st.markdown("**Gekozen juridische context(en):**")
st.markdown(", ".join(juridische_chips))

# ✅ Definitieve lijst
juridische_context = juridische_chips


# ✅ Wettelijke basis
wetopties = st.multiselect(
    "Wettelijke basis (meerdere mogelijk)",
    [
        "Wetboek van Strafvordering (huidige versie)",
        "Wetboek van strafvordering (nieuwe versie)",
        "Wet op de Identificatieplicht",
        "Wet op de politiegegevens",
        "Wetboek van Strafrecht",
        "Algemene verordening gegevensbescherming",
        "Anders..."
    ],
    default=st.session_state.get("keuze_wettelijke_basis", []),
    key="keuze_wettelijke_basis"
)

# ✅ Veilig ophalen
geselecteerd_wet = st.session_state.get("keuze_wettelijke_basis", [])

# ✅ Extra input bij 'Anders...'
extra_wet = ""
if "Anders..." in geselecteerd_wet:
    extra_wet = st.text_input(
        "Voer aanvullende wettelijke basis in",
        value=st.session_state.get("custom_wettelijke_basis_input", "").strip(),
        key="custom_wettelijke_basis_input",
        placeholder="Bijv. 'Wet forensische zorg'"
    )

# ✅ Chipsweergave
wet_chips = [opt for opt in geselecteerd_wet if opt != "Anders..."]
if extra_wet:
    wet_chips.append(extra_wet)

st.markdown("**Gekozen wettelijke basis(sen):**")
st.markdown(", ".join(wet_chips))

# ✅ Definitieve lijst
wet_basis = wet_chips
# ✅ Bundel alles voor latere logica
context_dict = {
    "organisatorisch": context,       # eerder gedefinieerd
    "juridisch": juridische_context,
    "wettelijk": wet_basis
}

datum = st.date_input("Datum voorstel", value=datetime.today())

voorsteller = st.text_input("Voorgesteld door")
ketenpartners = st.multiselect(
    "Ketenpartners die akkoord zijn",
    options=["ZM", "DJI", "KMAR", "CJIB", "JUSTID"])


# ✅ Toggle: logging aan/uit via checkbox
gebruik_logging = st.checkbox("🛠️ Log detailinformatie per toetsregel (alleen voor ontwikkelaars)", value=False)

# ✅ Toon belangrijkste toetsregels (hoog/midden) boven de knop “Genereer definitie” zodat de gebruiker ziet welke eisen worden meegenomen
#st.markdown("### 📏 Toetsregels meegenomen in de definitie-opbouw")
#st.markdown(selecteer_richtlijnen(toetsregels))  # geeft meteen de string die nodig is

from prompt_builder.prompt_builder import PromptBouwer, PromptConfiguratie

# ✅ Prompt pas bouwen na actie én ingevuld begrip
if st.button("Genereer definitie"):
    st.session_state["definitie_actie"] = True  # ✅ Markeer expliciete actie

actie = st.session_state.get("definitie_actie", False)

if actie and begrip.strip():
    prompt_config = PromptConfiguratie(
        begrip=begrip,
        context_dict=context_dict
    )
    pb = PromptBouwer(prompt_config)
    st.session_state["prompt_text"] = pb.bouw_prompt()

# ✅ Initialiseer sessiestatus
if "gegenereerd" not in st.session_state:
    st.session_state.gegenereerd = ""
if "beoordeling_gen" not in st.session_state:
    st.session_state.beoordeling_gen = ""
if "aangepaste_definitie" not in st.session_state:
    st.session_state.aangepaste_definitie = ""
if "beoordeling" not in st.session_state:
    st.session_state.beoordeling = ""
if "voorbeeld_zinnen" not in st.session_state:
    st.session_state.genereer_voorbeeld_zinnen = ""
if "praktijkvoorbeelden" not in st.session_state:
    st.session_state.genereer_praktijkvoorbeelden = ""
if "toelichting" not in st.session_state:
    st.session_state.toelichting = ""
if "synoniemen" not in st.session_state:
    st.session_state.synoniemen = ""
if "voorkeursterm" not in st.session_state:
    st.session_state["voorkeursterm"] = ""
if "antoniemen" not in st.session_state:
    st.session_state.antoniemen = ""



# ✅ Actie: genereer en toets definitie (verwerkt beide versies correct)
if actie and begrip:

    # 🧠 Genereer alleen de originele definitie
    # 1️⃣ Genereer volledige GPT-respons (inclusief metadata)
    raw = genereer_definitie(begrip, context_dict)
    # 2️⃣ Parse metadata-marker en zuivere definitietekst
    marker = None
    regels = raw.splitlines()
    tekstregels = []
    for regel in regels:
        if regel.lower().startswith("ontologische categorie:"):
            marker = regel.split(":",1)[1].strip()
        else:
            tekstregels.append(regel)
    definitie_origineel = "\n".join(tekstregels).strip()

    # 3️⃣ Opschonen
    from opschoning.opschoning import opschonen
    definitie_gecorrigeerd = opschonen(definitie_origineel, begrip)
    
    # 💚 Sla beide versies apart op in de sessiestatus (voor UI + logging + toetsing)
    st.session_state["definitie_origineel"] = definitie_origineel
    st.session_state["marker"] = marker or ""
    st.session_state["definitie_gecorrigeerd"] = definitie_gecorrigeerd
    st.session_state["gegenereerd"] = definitie_origineel  # deze blijft zichtbaar in Tab 1

    # 📚 AI-bronnen opvragen
    prompt_bronnen = (
        f"Geef een overzicht van de bronnen of kennis waarop je de volgende definitie hebt gebaseerd. "
        f"Noem expliciet wetten, richtlijnen of veelgebruikte definities indien van toepassing. "
        f"Begrip: '{begrip}'\n"
        f"Organisatorische context: '{', '.join(context)}'\n"
        f"Juridische context: '{', '.join(juridische_context)}'\n"
        f"Wettelijke basis: '{', '.join(wet_basis)}'"
    )
    try:
        # ✅ Gebruik de centrale GPT-aanroep
        bronnen_tekst = stuur_prompt_naar_gpt(
            prompt_bronnen,
            model="gpt-4",
            max_tokens=1000,
            temperatuur=0.2,
        )
        st.session_state.bronnen_gebruikt = bronnen_tekst.strip()
    except Exception as e:
        st.session_state.bronnen_gebruikt = f"❌ Fout bij ophalen bronnen: {e}"

        # ✅ Voer AI-toetsing uit op de opgeschoonde versie (niet meer op tuple)
        # ➤ Deze regel roept de hoofdfunctie `toets_definitie()` aan om alle toetsregels toe te passen op de gegenereerde definitie.
        #
        # ➤ Extra parameters worden meegegeven zodat specifieke toetsregels beter kunnen werken:
        #    • `begrip`: wordt doorgegeven aan regels die controle doen op gebruik van het begrip zelf (zoals SAM-05, cirkeldefinitie).
        #    • `bronnen_gebruikt`: wordt doorgegeven aan regels die expliciet naar bronvermeldingen kijken (zoals CON-02).
        #
        # ➤ De toetsresultaten worden opgeslagen in `st.session_state.beoordeling_gen`, zodat deze direct visueel getoond kunnen worden
        #    en eventueel later worden opgeslagen in CSV- of JSON-logbestanden.
        #
        # ➤ Hiermee wordt het mogelijk om toetsregels te laten werken met *meerdere bronnen van input* (zoals aparte contextvelden of AI-bijlagen),
        #    zonder dat dit ten koste gaat van eenvoud of flexibiliteit in de app.
        
    st.session_state.beoordeling_gen = toets_definitie(
        definitie_gecorrigeerd,
        toetsregels,
        begrip=begrip,
        marker=marker,                               # ← nieuw
        voorkeursterm=st.session_state["voorkeursterm"],
        bronnen_gebruikt=st.session_state.get("bronnen_gebruikt", None),
        contexten=context_dict,
        gebruik_logging=gebruik_logging  # ✅ logging nu dynamisch
    )

    # 🧩 Extra AI-inhoud genereren
    st.session_state.voorbeeld_zinnen = genereer_voorbeeld_zinnen(
        begrip,
        definitie_origineel,
        context_dict
    )
    st.session_state.praktijkvoorbeelden = genereer_praktijkvoorbeelden(
        begrip,
        definitie_origineel,
        context_dict
    )
    st.session_state.tegenvoorbeelden = genereer_tegenvoorbeelden(
        begrip,
        definitie_origineel,
        context_dict
    )
    
    st.session_state.toelichting = genereer_toelichting(begrip, context_dict)
    st.session_state.synoniemen = genereer_synoniemen(begrip, context_dict)
    st.session_state.antoniemen = genereer_antoniemen(begrip, context_dict)

    # ✅ Centrale logging voor AI-versie
    log_definitie(
        versietype="AI",
        begrip=begrip,
        context=context_dict.get("organisatorisch", []),
        juridische_context=context_dict.get("juridisch", []),
        wet_basis=context_dict.get("wettelijk", []),
        definitie_origineel=definitie_origineel,
        definitie_gecorrigeerd=definitie_gecorrigeerd,
        definitie_aangepast="",
        toetsing=st.session_state.beoordeling_gen,
        voorbeeld_zinnen =st.session_state.voorbeeld_zinnen,
        praktijkvoorbeelden =st.session_state.praktijkvoorbeelden,
        toelichting=st.session_state.toelichting,
        synoniemen=st.session_state.synoniemen,
        antoniemen=st.session_state.antoniemen,
        vrije_input=st.session_state.get("vrije_input", ""),
        prompt_text=st.session_state.get("prompt_text", ""),
        datum=datum,
        voorsteller=voorsteller,
        ketenpartners=ketenpartners,
        expert_review=st.session_state.get("expert_review", "")
)

    # 📊 Toggle AI-toetsing zichtbaar maken
    beoordeling = st.session_state.get("beoordeling_gen", [])
    if beoordeling:
        if "toon_ai_toetsing" not in st.session_state:
            st.session_state.toon_ai_toetsing = False

        if st.button("📊 Toon/verberg AI-toetsing (gegenereerde definitie)"):
            st.session_state.toon_ai_toetsing = not st.session_state.toon_ai_toetsing

        if st.session_state.toon_ai_toetsing:
            st.markdown("### ✔️ Resultaten van AI-toetsing (tegen opgeschoonde versie)")
            for regel in beoordeling:
                if "✔️" in regel:
                    st.success(regel)
                elif "❌" in regel:
                    st.error(regel)
                else:
                    st.info(regel)
    else:
        st.warning("⚠️ Geen toetsresultaten beschikbaar.")




                    
# ================================
# 🧾 UI: gescheiden tabbladen voor AI-, aangepaste- en expertweergave
# ================================
tab_ai, tab_aangepast, tab_expert = st.tabs([
    "🤖 AI-gegenereerde definitie",
    "✍️ Aangepaste definitie",
    "📋 Expert-review & toelichting"
])

# ================================
# 📘 Tab 1: AI-gegenereerde definitie en toetsing
# ================================
with tab_ai:
    st.markdown("### 📘 AI-gegenereerde definitie")
    st.markdown(st.session_state.gegenereerd)
    if st.session_state.get("marker"):
         st.markdown(f"**Ontologische categorie (metadata):** {st.session_state['marker'].capitalize()}")
         
    st.markdown("### ✨ Opgeschoonde definitie (gecorrigeerde versie)")
    st.markdown(st.session_state.get("definitie_gecorrigeerd", ""))  # 💚 Verwijdert verboden constructies

       
    if st.session_state.get("voorbeeld_zinnen"):
        st.markdown("### 🔍 korte voorbeeldzinnen")
        for casus in st.session_state.voorbeeld_zinnen:
            st.markdown(casus)
    
    if st.session_state.get("praktijkvoorbeelden"):
        st.markdown("### 🔍 Theoretische voorbeelden (Verification by instantiation)")
        for casus in st.session_state.praktijkvoorbeelden:
            st.markdown(casus)
            
    if st.session_state.get("tegenvoorbeelden"):
        st.markdown("### 🚫 Tegenvoorbeelden")
        for casus in st.session_state.tegenvoorbeelden:
            st.markdown(f"- {casus}")

    if st.session_state.toelichting:
        st.markdown("### ℹ️ Toelichting op definitie")
        st.info(st.session_state.toelichting)

    if st.session_state.synoniemen:
        st.markdown("### 🔁 Synoniemen")

        # 1️⃣ Parse de rauwe tekst (per regel één synoniem) naar een lijst
        synoniemen_lijst = [
            s.strip()
            for s in st.session_state.synoniemen.split("\n")
            if s.strip()
        ]

        # 2️⃣ Toon ze netjes in één regel
        st.success(", ".join(synoniemen_lijst))

        # 3️⃣ opties: lege placeholder + begrip + synoniemen
        opties = [""] + [begrip] + synoniemen_lijst
        keuze = st.selectbox(
            "Selecteer de voorkeurs-term (lemma)",
            opties,
            index=0,
            format_func=lambda x: x if x else "— kies hier je voorkeurs-term —",
            help="Laat leeg als je nog geen voorkeurs-term wilt vastleggen"
        )
        st.session_state["voorkeursterm"] = keuze
    else:
        st.markdown("### 🔁 Synoniemen")
        st.warning("Geen synoniemen beschikbaar — je kunt nu nog géén voorkeurs-term selecteren.")
         # geen default naar begrip, hou het leeg
        st.session_state["voorkeursterm"] = ""

    if st.session_state.antoniemen:
        st.markdown("### 🔄 Antoniemen")
        st.warning(st.session_state.antoniemen)

    if "bronnen_gebruikt" in st.session_state and st.session_state.bronnen_gebruikt:
        st.markdown("### 📚 Bronnen gebruikt door AI")
        st.text_area(
            "Bronnen gebruikt door AI",
            value=st.session_state.bronnen_gebruikt,
            height=100,
            disabled=True
        )

    beoordeling = st.session_state.get("beoordeling_gen", [])
    if beoordeling:
        if "toon_ai_toetsing" not in st.session_state:
            st.session_state.toon_ai_toetsing = False

        if st.button("📊 Toon/verberg AI-toetsing"):
            st.session_state.toon_ai_toetsing = not st.session_state.toon_ai_toetsing

        if st.session_state.toon_ai_toetsing:
            st.markdown("### ✔️ Toetsing AI-versie")
            for regel in beoordeling:
                if "✔️" in regel:
                    st.success(regel)
                elif "❌" in regel:
                    st.error(regel)
                else:
                    st.info(regel)
    else:
        st.warning("⚠️ Geen toetsresultaten beschikbaar voor de AI-versie.")

    if st.session_state.get("prompt_text"):
        with st.expander("📄 Bekijk volledige gegenereerde prompt", expanded=False):
            st.text_area(
                "Prompttekst verstuurd naar GPT",
                value=st.session_state["prompt_text"],
                height=500,
                disabled=True
            )

# ================================
# ✍️ Tab 2: Aangepaste definitie en toetsing
# ================================
with tab_aangepast:
    st.markdown("### ✍️ Aangepaste definitie + toetsing")

    st.session_state.aangepaste_definitie = st.text_area(
        "Pas de definitie aan (optioneel):",
        value=st.session_state.gegenereerd,
        height=100
    )

    if st.button("🔁 Hercontroleer aangepaste definitie"):
        if st.session_state.aangepaste_definitie.strip():
            st.session_state.beoordeling = toets_definitie(
                st.session_state.aangepaste_definitie,
                toetsregels,
                begrip=begrip,
                voorkeursterm=st.session_state["voorkeursterm"],
                bronnen_gebruikt=st.session_state.get("bronnen_gebruikt", None),
                contexten=context_dict,
                gebruik_logging=gebruik_logging  # ✅ logging nu ook hier instelbaar
            )
        else:
            st.warning("Voer eerst een aangepaste definitie in.")

    if st.session_state.beoordeling:
        if "toon_toetsing_hercontrole" not in st.session_state:
            st.session_state.toon_toetsing_hercontrole = True

        if st.button("📋 Toon/verberg toetsing van aangepaste versie"):
            st.session_state.toon_toetsing_hercontrole = not st.session_state.toon_toetsing_hercontrole

        if st.session_state.toon_toetsing_hercontrole:
            st.markdown("### ✔️ Toetsing aangepaste versie")
            for regel in st.session_state.beoordeling:
                if "✔️" in regel:
                    st.success(regel)
                elif "❌" in regel:
                    st.error(regel)
                else:
                    st.info(regel)



# ================================
# 📋 Tab 3: Expert-review & toelichting
# ================================
with tab_expert:
    st.markdown("### 📋 Expert-review")
    # ✅ Expert-review opslaan in sessiestate
    st.session_state.expert_review = st.text_area(
        "Ruimte voor toelichting of beoordeling door een expert (bijv. juridisch adviseur)",
        placeholder="Voer hier aanvullende opmerkingen, risico’s of goedkeuring in...",
        value=st.session_state.get("expert_review", ""),
        height=150
    )
    st.success("✅ Deze toelichting wordt automatisch opgeslagen in de log (JSON en CSV).")
    
    # ✅ Centrale logging voor aangepaste versie
    log_definitie(
        versietype="Aangepast",
        begrip=begrip,
        context=context,
        juridische_context=juridische_context,
        wet_basis=wet_basis,
        prompt_text=st.session_state.get("prompt_text", ""),
        definitie_origineel=st.session_state.get("definitie_origineel", ""),
        definitie_gecorrigeerd=st.session_state.get("definitie_gecorrigeerd", ""),
        definitie_aangepast=st.session_state.aangepaste_definitie,
        toetsing=st.session_state.beoordeling,
        voorbeeld_zinnen=st.session_state.get("voorbeeld_zinnen", ""),
        praktijkvoorbeelden=st.session_state.get("praktijkvoorbeelden", ""),
        toelichting=st.session_state.get("toelichting", ""),
        synoniemen=st.session_state.get("synoniemen", ""),
        antoniemen=st.session_state.get("antoniemen", ""),
        vrije_input=st.session_state.get("vrije_input", ""),
        datum=datum,
        voorsteller=voorsteller,
        ketenpartners=ketenpartners,
        expert_review=st.session_state.get("expert_review", "")
    )
    st.success("✅ Aangepaste definitie en toetsing opgeslagen.")
    
    # ================================
    # ⚙️ UI: beheer van verboden startwoorden (Expert-tabblad)
    # ================================
    from config.verboden_woorden import laad_verboden_woorden, sla_verboden_woorden_op

    with st.expander("⚙️ Verboden startwoorden beheren", expanded=False):

        # 💚 Laadt de permanente lijst vanuit verboden_woorden.json
        huidige_lijst = laad_verboden_woorden()

        # 💚 UI-veld voor bewerken van de permanente woordenlijst
        woorden_input = st.text_area(
            "✏️ Permanente lijst van verboden startwoorden (gescheiden door komma’s):",
            value=", ".join(huidige_lijst)
        )

        # 💚 Sla de gewijzigde lijst op in het JSON-bestand
        if st.button("💾 Sla permanente lijst op"):
            lijst = [w.strip() for w in woorden_input.split(",") if w.strip()]
            sla_verboden_woorden_op(lijst)
            st.success(f"✅ Permanente lijst opgeslagen ({len(lijst)} woorden).")

        # 💚 Scheiding tussen permanente en tijdelijke invoer
        # 💚 Tijdelijke override (alleen voor deze sessie)
        st.markdown("🧪 <u>Tijdelijke override (alleen voor deze sessie)</u>", unsafe_allow_html=True)

        # ================================
        # 🔁 UI: Tijdelijke override van verboden woorden (alleen indien aangevinkt)
        # ================================
        st.markdown("### 🔁 Tijdelijke override van verboden woorden (optioneel)")

        # ✅ Checkbox: bepaalt of override actief is
        gebruik_override = st.checkbox("✅ Gebruik tijdelijke override", key="activeer_override")

        if gebruik_override:
            tijdelijke_input = st.text_area(
                "✏️ Voer de tijdelijke override-woorden in (gescheiden door komma’s)",
                key="override_input_tekst"
            )

            # 💚 Verwerk invoer met strikte filtering (geen lege woorden of alleen leestekens)
            tijdelijke_lijst_raw = [w.strip() for w in tijdelijke_input.split(",") if w.strip()]
            tijdelijke_lijst = [w for w in tijdelijke_lijst_raw if re.search(r"\w", w)]

            if tijdelijke_lijst:
                # 💚 Alleen bij geldige lijst activeren we de override
                st.session_state.override_actief = True
                st.session_state.override_verboden_woorden = tijdelijke_lijst
                st.success(f"✅ Override geactiveerd met {len(tijdelijke_lijst)} geldige woorden.")
            else:
                # 💚 Invalide inhoud → override NIET activeren
                st.session_state.override_actief = False
                st.session_state.override_verboden_woorden = []
                st.warning("⚠️ Geen geldige woorden gedetecteerd. Override wordt niet toegepast.")
        else:
            # 💚 Reset override als checkbox uit staat
            st.session_state.override_actief = False
            st.session_state.override_verboden_woorden = []
            st.info("ℹ️ Geen override actief. De standaardlijst wordt gebruikt.")

        # ✅ Toon actieve status o.b.v. sessiestate
        if st.session_state.get("override_actief"):
            st.info(f"⚠️ Tijdelijke override actief met {len(st.session_state.override_verboden_woorden)} woorden.")
        else:
            st.info("ℹ️ Geen tijdelijke override actief. Standaardlijst wordt gebruikt.")
            
    # ✅ Test alle woorden uit verboden_woorden.json tegen een testzin
    st.markdown("### 🧪 Test alle verboden woorden op een testzin")

    testzin = st.text_input("Voer een testzin in om alle woorden te controleren", key="testzin_regexcheck")

    if testzin:
        woordenlijst = laad_verboden_woorden()
        st.write("🔍 Resultaten per woord:")

        for woord in woordenlijst:
            woord_norm = woord.strip().lower()
            zin_norm = testzin.strip().lower()

            # 🔍 Detectie op aanwezigheid en beginregex
            komt_voor = woord_norm in zin_norm
            regex_match = bool(re.match(rf"^({re.escape(woord_norm)})\s+", zin_norm))

            resultaat = f"🔹 `{woord}` → "
            resultaat += "✔️ In zin" if komt_voor else "❌ Niet in zin"
            resultaat += " | "
            resultaat += "✔️ Regex-match" if regex_match else "❌ Geen regex-match aan begin"

            if regex_match:
                st.success(resultaat)
            elif komt_voor:
                st.warning(resultaat)
            else:
                st.info(resultaat)
                
    # ================================
    # ✅ VOORSTEL 3 (herwerkt): Test één individueel woord op regex
    # ================================

    # 💚 Visuele kop boven test
    st.markdown("### ➕ Test dit woord (individueel)")

    # 💚 Twee kolommen naast elkaar voor woord en zin
    col1, col2 = st.columns(2)

    with col1:
        # 💚 Deze invoer laat gebruiker een woord kiezen om te testen
        # 💚 De key is uniek: voorkomt conflict met andere invoervelden (zoals in Tab 2)
        test_woord = st.text_input("👁️ Te testen woord", key="test_woord_input_enkel")

    with col2:
        # 💚 Hier voert gebruiker de zin in waarin gezocht moet worden naar het woord
        # 💚 Ook hier is de key uniek gemaakt (specifiek voor deze test)
        test_zin = st.text_input("✏️ Testzin (waar dit woord mogelijk in voorkomt)", key="test_zin_input_enkel")

    # 💚 Zodra gebruiker op de testknop klikt, wordt de test uitgevoerd
    # 💚 Unieke key toegevoegd om Streamlit-conflict te vermijden
    if st.button("🧪 Voer test uit voor dit woord", key="button_test_voorstel3"):
        if not test_woord or not test_zin:
            # 💚 Feedback bij ontbrekende invoer
            st.warning("⚠️ Vul zowel het te testen woord als een zin in.")
        else:
            # 💚 Normaliseer beide inputs naar lowercase voor consistente analyse
            woord_norm = test_woord.strip().lower()
            zin_norm = test_zin.strip().lower()

            # 💚 Controle 1: komt het woord ergens voor in de zin?
            komt_voor = woord_norm in zin_norm

            # 💚 Controle 2: matcht het woord aan het begin van de zin (regex)?
            regex_match = bool(re.match(rf"^({re.escape(woord_norm)})\s+", zin_norm))

            # 💚 Opbouw van resultaattekst
            resultaat = f"🔹 `{test_woord}` in testzin → "
            resultaat += "✔️ In zin" if komt_voor else "❌ Niet in zin"
            resultaat += " | "
            resultaat += "✔️ Regex-match aan begin" if regex_match else "❌ Geen beginmatch"

            # 💚 Logging voor analyse/doelmatigheid via Voorstel 4
            log_test_verboden_woord(test_woord, test_zin, komt_voor, regex_match)

            # 💚 Visuele terugkoppeling afhankelijk van resultaat
            if regex_match:
                st.success(resultaat)
            elif komt_voor:
                st.warning(resultaat)
            else:
                st.info(resultaat)
    # ================================
    # ➕ VOORSTEL 4b: Logging toevoegen aan individuele woordtest
    # ================================

    # 💚 UI-opbouw in kolommen
    col1, col2 = st.columns(2)

    with col1:
        test_woord = st.text_input("👁️ Verboden woord om te testen", key="test_woord_input_voorkom_dubbel_2")
        # 💚 Tweede tekstveld krijgt ook een unieke key om conflictsituatie te voorkomen

    with col2:
        test_zin = st.text_input("✏️ Testzin (waar dit woord mogelijk in voorkomt)", key="test_zin_input")

    # 💚 Actieve testknop (pas uitvoeren als gebruiker op knop klikt)
    # 💚 Unieke key toegevoegd voor voorstel 4b (voorkomt ID-conflict)
    if st.button("🧪 Voer test uit voor dit woord", key="button_test_voorstel4b"):
        if not test_woord or not test_zin:
            st.warning("⚠️ Vul zowel het te testen woord als een zin in.")
        else:
            # 💚 Normaliseer invoer voor eerlijke vergelijking
            woord_norm = test_woord.strip().lower()
            zin_norm = test_zin.strip().lower()

            # 💚 Controleer op aanwezigheid in de zin én regex-match aan het begin
            komt_voor = woord_norm in zin_norm
            regex_match = bool(re.match(rf"^({re.escape(woord_norm)})\s+", zin_norm))

            # ✅ Logging van het testresultaat (Voorstel 4b)
            # 🧠 Dit maakt analyse en debugging mogelijk in JSONL-log
            from config.verboden_woorden import log_test_verboden_woord  # ✅ Als nog niet geïmporteerd
            log_test_verboden_woord(test_woord, test_zin, komt_voor, regex_match)

            # 💚 Bouw visuele feedback op
            resultaat = f"🔹 `{test_woord}` in testzin → "
            resultaat += "✔️ In zin" if komt_voor else "❌ Niet in zin"
            resultaat += " | "
            resultaat += "✔️ Regex-match aan begin" if regex_match else "❌ Geen beginmatch"

            # 💚 Toon resultaat met passende kleur
            if regex_match:
                st.success(resultaat)
            elif komt_voor:
                st.warning(resultaat)
            else:
                st.info(resultaat)
                
                
    # ================================
    # 📖 VOORSTEL 5: Logviewer + downloadknop voor woordtest-logging
    # ================================
    # ✅ Laat toe om resultaten uit voorstel 4b direct te bekijken en downloaden
    # 💚 Controleert of veld 'expert_review' correct wordt opgeslagen in zowel JSON als CSV logs
    with st.expander("📖 Bekijk log van individuele woordtests", expanded=False):
        try:
            # 💚 Lees het JSONL-logbestand in
            logpad = "log/verboden_woord_tests.jsonl"
            with open(logpad, encoding="utf-8") as f:
                regels = [json.loads(lijn.strip()) for lijn in f if lijn.strip()]
            if regels:
                st.markdown(f"📄 Logbestand bevat {len(regels)} regels.")
                df = pd.DataFrame(regels)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("ℹ️ Logbestand is leeg.")
        except FileNotFoundError:
            st.warning("⚠️ Geen logbestand gevonden. Test eerst een woord.")
        except Exception as e:
            st.error(f"❌ Fout bij inlezen logbestand: {e}")

        # 📥 Downloadknop voor JSONL-bestand
        if os.path.exists(logpad):
            with open(logpad, "rb") as f:
                st.download_button(
                    label="📥 Download logbestand (.jsonl)",
                    data=f,
                    file_name="verboden_woord_tests.jsonl",
                    mime="application/json"
                )
            
    # 🟩 Downloadknop voor het .csv-logbestand
    with open("log/definities_log.csv", "rb") as f:
        st.download_button(
            label="📥 Download CSV-logbestand",
            data=f,
            file_name="definities_log.csv",
            mime="text/csv"
        )
    
    
    # ================================
    # 🧪 VALIDATIE: Logging bevat expert-review?
    # ================================
    # Deze tijdelijke validatie controleert of het veld 'expert_review' voorkomt in:
    # 1. Het JSON-logbestand
    # 2. Het CSV-logbestand
    # Resultaten worden direct getoond in Streamlit

    with st.expander("🧪 Validatie loggingstructuur (tijdelijk)", expanded=False):
        fouten = []

        # ✅ 1. Controle JSON-log
        try:
            with open("log/definities_log.json", "r", encoding="utf-8") as f:
                regels = [json.loads(lijn) for lijn in f.readlines() if lijn.strip()]
                if not all("expert_review" in regel for regel in regels):
                    fouten.append("❌ JSON-log mist veld 'expert_review' in één of meer regels.")
        except Exception as e:
            fouten.append(f"❌ Kon JSON-log niet lezen: {e}")

        # ✅ 2. Controle CSV-log
        try:
            df = pd.read_csv("log/definities_log.csv")
            if "Expert-review" not in df.columns:
                fouten.append("❌ CSV-log bevat geen kolom 'Expert-review'.")
        except Exception as e:
            fouten.append(f"❌ Kon CSV-log niet lezen: {e}")

        # ✅ Resultaat tonen
        if fouten:
            for fout in fouten:
                st.error(fout)
        else:
            st.success("✅ Loggingstructuur is compleet. 'expert_review' is aanwezig in zowel JSON als CSV.")


# ================================
# ✅ Toon lookup-resultaten per bron boven het prompt-blok
# Alleen zichtbaar ná uitgevoerde lookup
# ================================
if st.session_state.get("lookup_uitgevoerd", False) and lookup_resultaten:
    with st.expander("🔍 Informatie gevonden via web lookup", expanded=True):
        for resultaat in lookup_resultaten:
            bron = resultaat.get("bron", "onbekend")
            tekst = resultaat.get("definitie", "")
            status = resultaat.get("status", "onbekend")

            if tekst and status == "ok":
                st.markdown(f"**Bron: {bron}**")
                st.markdown(tekst.strip()[:1000] + "..." if len(tekst) > 1000 else tekst)
            else:
                st.markdown(f"**Bron: {bron}** – _geen bruikbaar resultaat gevonden_")