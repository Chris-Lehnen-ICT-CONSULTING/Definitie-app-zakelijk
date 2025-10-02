#!/usr/bin/env python3
"""Debug script om session state te inspecteren en op te schonen."""

import streamlit as st

st.title("🔍 Session State Debug Tool")

st.markdown("## Context Velden")

# Toon de huidige session state voor context velden
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Organisatorische Context")
    if "org_context_values" in st.session_state:
        st.write("Huidige waardes:")
        for val in st.session_state.org_context_values:
            st.write(f"• {val}")

        if st.button("🗑️ Wis Org Context"):
            st.session_state.org_context_values = []
            st.success("Organisatorische context gewist!")
            st.rerun()
    else:
        st.info("Geen waardes in session state")

with col2:
    st.markdown("### Juridische Context")
    if "jur_context_values" in st.session_state:
        st.write("Huidige waardes:")
        for val in st.session_state.jur_context_values:
            st.write(f"• {val}")

        if st.button("🗑️ Wis Jur Context"):
            st.session_state.jur_context_values = []
            st.success("Juridische context gewist!")
            st.rerun()
    else:
        st.info("Geen waardes in session state")

with col3:
    st.markdown("### Wettelijke Basis")
    if "wet_basis_values" in st.session_state:
        st.write("Huidige waardes:")
        for val in st.session_state.wet_basis_values:
            st.write(f"• {val}")

        if st.button("🗑️ Wis Wet Basis"):
            st.session_state.wet_basis_values = []
            st.success("Wettelijke basis gewist!")
            st.rerun()
    else:
        st.info("Geen waardes in session state")

st.markdown("---")

# Toon problematische waardes
st.markdown("## 🚨 Problematische Waardes")

base_org_options = [
    "OM", "ZM", "Reclassering", "DJI", "NP", "Justid",
    "KMAR", "FIOD", "CJIB", "Strafrechtketen",
    "Migratieketen", "Justitie en Veiligheid", "Anders..."
]

base_jur_options = [
    "Strafrecht", "Civiel recht", "Bestuursrecht",
    "Internationaal recht", "Europees recht",
    "Migratierecht", "Anders..."
]

base_wet_options = [
    "Wetboek van Strafvordering (huidige versie)",
    "Wetboek van strafvordering (nieuwe versie)",
    "Wet op de Identificatieplicht",
    "Wet op de politiegegevens",
    "Wetboek van Strafrecht",
    "Algemene verordening gegevensbescherming",
    "Anders..."
]

problems_found = False

# Check organisatorische context
if "org_context_values" in st.session_state:
    invalid_org = [v for v in st.session_state.org_context_values
                   if v == "Anders..." or (v not in base_org_options and v not in st.session_state.org_context_values)]
    if invalid_org:
        st.error(f"❌ Ongeldige waardes in Organisatorische context: {invalid_org}")
        problems_found = True

# Check juridische context
if "jur_context_values" in st.session_state:
    invalid_jur = [v for v in st.session_state.jur_context_values
                   if v == "Anders..." or v == "en nu"]
    if invalid_jur:
        st.error(f"❌ Ongeldige waardes in Juridische context: {invalid_jur}")
        problems_found = True

# Check wettelijke basis
if "wet_basis_values" in st.session_state:
    invalid_wet = [v for v in st.session_state.wet_basis_values
                   if v == "Anders..." or v == "toetsen"]
    if invalid_wet:
        st.error(f"❌ Ongeldige waardes in Wettelijke basis: {invalid_wet}")
        problems_found = True

if not problems_found:
    st.success("✅ Geen problematische waardes gevonden!")

st.markdown("---")

# Globale reset
st.markdown("## 🔄 Globale Acties")

col1, col2 = st.columns(2)

with col1:
    if st.button("🗑️ WIS ALLE CONTEXT VELDEN", type="primary"):
        st.session_state.org_context_values = []
        st.session_state.jur_context_values = []
        st.session_state.wet_basis_values = []
        st.success("✅ Alle context velden gewist!")
        st.rerun()

with col2:
    if st.button("🔍 Toon Volledige Session State"):
        st.json({k: v for k, v in st.session_state.items()
                if "context" in k.lower() or "wet" in k.lower() or "jur" in k.lower() or "org" in k.lower()})

st.markdown("---")
st.markdown("### Instructies")
st.markdown("""
1. **Problematische waardes**: 'Anders...', 'toetsen', 'en nu' zijn vaak de boosdoeners
2. **Oplossing**: Wis de betreffende context en probeer opnieuw
3. **Preventie**: Selecteer nooit 'Anders...' zonder direct een waarde in te voeren
""")
