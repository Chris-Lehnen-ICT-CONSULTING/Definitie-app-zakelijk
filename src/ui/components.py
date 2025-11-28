"""
UI components for DefinitieAgent Streamlit application.
"""

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

from config.config_manager import ConfigSection, get_config
from config.verboden_woorden import (
    laad_verboden_woorden,
    log_test_verboden_woord,
    sla_verboden_woorden_op,
)
from ui.session_state import SessionStateManager
from utils.exceptions import log_and_display_error


class UIComponents:
    """Collection of reusable UI components for the application."""

    @staticmethod
    def render_input_form() -> dict[str, Any]:
        """
        Render the main input form for definition generation.

        Returns:
            Dictionary with form data
        """
        st.write("🧾 Definitie Kwaliteit")

        # Main term input
        begrip = st.text_input(
            "Voer een term in waarvoor een definitie moet worden gegenereerd"
        )

        ui_cfg = get_config(ConfigSection.UI)

        # Organizational context (from config)
        org_options = list(getattr(ui_cfg, "organizational_contexts", []) or [])
        contextopties = st.multiselect(
            "Organisatorische context (meerdere mogelijk)",
            org_options,
            default=[],
        )
        # Toon afkortingen-uitleg als beschikbaar
        try:
            abbrev = getattr(ui_cfg, "afkortingen", {}) or {}
            if abbrev:
                with st.expander("ℹ️ Afkortingen (uitleg)", expanded=False):
                    for k in sorted(abbrev.keys()):
                        st.markdown(f"- **{k}** — {abbrev[k]}")
        except (AttributeError, TypeError) as e:
            # Config may not have abbreviations section - safe to ignore
            logger.debug(f"Afkortingen expander skipped: {e}")

        custom_context = ""
        if "Anders..." in contextopties:
            custom_context = st.text_input(
                "Voer aanvullende organisatorische context in", key="custom_context"
            )

        contexten_compleet = [opt for opt in contextopties if opt != "Anders..."]
        if custom_context.strip():
            contexten_compleet.append(custom_context.strip())

        # Juridical context (from config)
        legal_options = list(getattr(ui_cfg, "legal_contexts", []) or [])
        juridische_opties = st.multiselect(
            "Juridische context (meerdere mogelijk)",
            legal_options,
            default=[],
        )

        custom_juridisch = ""
        if "Anders..." in juridische_opties:
            custom_juridisch = st.text_input(
                "Voer aanvullende juridische context in",
                key="custom_juridische_context",
            )

        juridische_contexten = [opt for opt in juridische_opties if opt != "Anders..."]
        if custom_juridisch.strip():
            juridische_contexten.append(custom_juridisch.strip())

        # Legal basis (from config)
        law_options = list(getattr(ui_cfg, "common_laws", []) or [])
        wetopties = st.multiselect(
            "Wettelijke basis (meerdere mogelijk)",
            law_options,
            default=[],
        )

        custom_wet = ""
        if "Anders..." in wetopties:
            custom_wet = st.text_input(
                "Voer aanvullende wettelijke basis in", key="custom_wettelijke_basis"
            )

        wet_basis = [opt for opt in wetopties if opt != "Anders..."]
        if custom_wet.strip():
            wet_basis.append(custom_wet.strip())

        # Additional metadata
        datum = st.date_input("Datum voorstel", value=datetime.now(UTC).date())
        voorsteller = st.text_input("Voorgesteld door")
        ketenpartners = st.multiselect(
            "Ketenpartners die akkoord zijn",
            options=["ZM", "DJI", "KMAR", "CJIB", "JUSTID"],
        )

        # Logging toggle
        gebruik_logging = st.checkbox(
            "🛠️ Log detailinformatie per toetsregel (alleen voor ontwikkelaars)",
            value=False,
        )

        return {
            "begrip": begrip,
            "context": contexten_compleet,
            "juridische_context": juridische_contexten,
            "wet_basis": wet_basis,
            "datum": datum,
            "voorsteller": voorsteller,
            "ketenpartners": ketenpartners,
            "gebruik_logging": gebruik_logging,
            "context_dict": {
                "organisatorisch": contexten_compleet,
                "juridisch": juridische_contexten,
                "wettelijk": wet_basis,
            },
        }

    @staticmethod
    def render_ai_tab():
        """Render the AI-generated definition tab."""
        st.markdown("### 📘 AI-gegenereerde definitie")
        st.markdown(SessionStateManager.get_value("gegenereerd"))

        if SessionStateManager.get_value("marker"):
            st.markdown(
                f"**Ontologische categorie (metadata):** {SessionStateManager.get_value('marker').capitalize()}"
            )

        st.markdown("### ✨ Opgeschoonde definitie (gecorrigeerde versie)")
        st.markdown(SessionStateManager.get_value("definitie_gecorrigeerd"))

        # Example sentences
        UIComponents._render_examples()

        # Additional AI content
        UIComponents._render_ai_content()

        # Sources used
        UIComponents._render_sources()

        # AI testing results
        UIComponents._render_ai_testing()

        # Export button
        UIComponents._render_export_button()

    @staticmethod
    def _render_examples():
        """Render example sentences and cases."""
        voorbeeld_zinnen = SessionStateManager.get_value("voorbeeld_zinnen", [])
        if voorbeeld_zinnen:
            st.markdown("### 🔍 Korte voorbeeldzinnen")
            for casus in voorbeeld_zinnen:
                st.markdown(casus)

        praktijkvoorbeelden = SessionStateManager.get_value("praktijkvoorbeelden", [])
        if praktijkvoorbeelden:
            st.markdown(
                "### 🔍 Theoretische voorbeelden (Verification by instantiation)"
            )
            for casus in praktijkvoorbeelden:
                st.markdown(casus)

        tegenvoorbeelden = SessionStateManager.get_value("tegenvoorbeelden", [])
        if tegenvoorbeelden:
            st.markdown("### 🚫 Tegenvoorbeelden")
            for casus in tegenvoorbeelden:
                st.markdown(f"- {casus}")

    @staticmethod
    def _render_ai_content():
        """Render AI-generated content like explanations and synonyms."""
        toelichting = SessionStateManager.get_value("toelichting")
        if toelichting:
            st.markdown("### i️ Toelichting op definitie")
            st.info(toelichting)

        synoniemen = SessionStateManager.get_value("synoniemen")
        if synoniemen:
            st.markdown("### 🔁 Synoniemen")
            # Synoniemen is altijd een lijst van de voorbeelden generator
            if isinstance(synoniemen, list):
                synoniemen_lijst = synoniemen
            else:
                # Fallback voor het geval het toch een string is
                synoniemen_lijst = [
                    s.strip() for s in str(synoniemen).split("\n") if s.strip()
                ]
            st.success(", ".join(synoniemen_lijst))

            # Preferred term selection
            begrip = SessionStateManager.get_value("begrip", "")
            opties = ["", begrip, *synoniemen_lijst]
            keuze = st.selectbox(
                "Selecteer de voorkeurs-term (lemma)",
                opties,
                index=0,
                format_func=lambda x: x if x else "-- kies hier je voorkeurs-term --",
                help="Laat leeg als je nog geen voorkeurs-term wilt vastleggen",
            )
            SessionStateManager.set_value("voorkeursterm", keuze)
        else:
            st.markdown("### 🔁 Synoniemen")
            st.warning(
                "Geen synoniemen beschikbaar -- je kunt nu nog géén voorkeurs-term selecteren."
            )
            SessionStateManager.set_value("voorkeursterm", "")

        antoniemen = SessionStateManager.get_value("antoniemen")
        if antoniemen:
            st.markdown("### 🔄 Antoniemen")
            # Antoniemen is altijd een lijst van de voorbeelden generator
            if isinstance(antoniemen, list):
                st.warning(", ".join(antoniemen))
            else:
                # Fallback voor het geval het toch een string is
                st.warning(str(antoniemen))

    @staticmethod
    def _render_sources():
        """Render sources used by AI."""
        bronnen_gebruikt = SessionStateManager.get_value("bronnen_gebruikt")
        if bronnen_gebruikt:
            st.markdown("### 📚 Bronnen gebruikt door AI")
            st.text_area(
                "Bronnen gebruikt door AI",
                value=bronnen_gebruikt,
                height=100,
                disabled=True,
            )

    @staticmethod
    def _render_ai_testing():
        """Render AI testing results."""
        beoordeling = SessionStateManager.get_value("beoordeling_gen", [])
        if beoordeling:
            if st.button("📊 Toon/verberg AI-toetsing"):
                current_state = SessionStateManager.get_value("toon_ai_toetsing", False)
                SessionStateManager.set_value("toon_ai_toetsing", not current_state)

            if SessionStateManager.get_value("toon_ai_toetsing"):
                st.markdown("### ✔️ Toetsing AI-versie")
                UIComponents._render_test_results(beoordeling)
        else:
            st.warning("⚠️ Geen toetsresultaten beschikbaar voor de AI-versie.")

    @staticmethod
    def _render_test_results(results: list[str]):
        """Render quality test results with appropriate styling."""
        for regel in results:
            if "✔️" in regel:
                st.success(regel)
            elif "❌" in regel:
                st.error(regel)
            else:
                st.info(regel)

    @staticmethod
    def _render_export_button():
        """Render export button using new clean services."""
        if SessionStateManager.has_generated_definition():
            # Use the new export functionality from components_adapter
            from ui.components_adapter import render_export_button_new

            render_export_button_new()

    @staticmethod
    def render_modified_tab():
        """Render the modified definition tab."""
        st.markdown("### ✍️ Aangepaste definitie + toetsing")

        aangepaste_definitie = st.text_area(
            "Pas de definitie aan (optioneel):",
            value=SessionStateManager.get_value("gegenereerd"),
            height=100,
        )
        SessionStateManager.set_value("aangepaste_definitie", aangepaste_definitie)

        return st.button("🔁 Hercontroleer aangepaste definitie")

    @staticmethod
    def render_modified_testing_results():
        """Render testing results for modified definition."""
        beoordeling = SessionStateManager.get_value("beoordeling", [])
        if beoordeling:
            if st.button("📋 Toon/verberg toetsing van aangepaste versie"):
                current_state = SessionStateManager.get_value(
                    "toon_toetsing_hercontrole", True
                )
                SessionStateManager.set_value(
                    "toon_toetsing_hercontrole", not current_state
                )

            if SessionStateManager.get_value("toon_toetsing_hercontrole"):
                st.markdown("### ✔️ Toetsing aangepaste versie")
                UIComponents._render_test_results(beoordeling)

    @staticmethod
    def render_expert_tab():
        """Render the expert review tab."""
        st.markdown("### 📋 Expert-review")

        expert_review = st.text_area(
            "Ruimte voor toelichting of beoordeling door een expert (bijv. juridisch adviseur)",
            placeholder="Voer hier aanvullende opmerkingen, risico's of goedkeuring in...",
            value=SessionStateManager.get_value("expert_review", ""),
            height=150,
        )
        SessionStateManager.set_value("expert_review", expert_review)

        st.success(
            "✅ Deze toelichting wordt automatisch opgeslagen in de log (JSON en CSV)."
        )

        # Forbidden words management
        UIComponents._render_forbidden_words_management()

        # Download buttons
        UIComponents._render_download_buttons()

        # Validation viewer
        UIComponents._render_validation_viewer()

    @staticmethod
    def _render_forbidden_words_management():
        """Render forbidden words management interface."""
        with st.expander("⚙️ Verboden startwoorden beheren", expanded=False):
            try:
                huidige_lijst = laad_verboden_woorden()

                woorden_input = st.text_area(
                    "✏️ Permanente lijst van verboden startwoorden (gescheiden door komma's):",
                    value=", ".join(huidige_lijst),
                )

                if st.button("💾 Sla permanente lijst op"):
                    lijst = [w.strip() for w in woorden_input.split(",") if w.strip()]
                    sla_verboden_woorden_op(lijst)
                    st.success(
                        f"✅ Permanente lijst opgeslagen ({len(lijst)} woorden)."
                    )

                # Individual word testing
                UIComponents._render_word_testing()

            except Exception as e:
                st.error(log_and_display_error(e, "forbidden words management"))

    @staticmethod
    def _render_word_testing():
        """Render individual word testing interface."""
        st.markdown("### + Test dit woord (individueel)")

        col1, col2 = st.columns(2)

        with col1:
            test_woord = st.text_input("👁️ Te testen woord", key="test_woord_input")

        with col2:
            test_zin = st.text_input("✏️ Testzin", key="test_zin_input")

        if st.button("🧪 Voer test uit", key="test_button"):
            if not test_woord or not test_zin:
                st.warning("⚠️ Vul zowel het te testen woord als een zin in.")
            else:
                try:
                    import re

                    woord_norm = test_woord.strip().lower()
                    zin_norm = test_zin.strip().lower()

                    komt_voor = woord_norm in zin_norm
                    regex_match = bool(
                        re.match(rf"^({re.escape(woord_norm)})\s+", zin_norm)
                    )

                    log_test_verboden_woord(
                        test_woord, test_zin, komt_voor, regex_match
                    )

                    resultaat = f"🔹 `{test_woord}` in testzin → "
                    resultaat += "✔️ In zin" if komt_voor else "❌ Niet in zin"
                    resultaat += " | "
                    resultaat += (
                        "✔️ Regex-match aan begin"
                        if regex_match
                        else "❌ Geen beginmatch"
                    )

                    if regex_match:
                        st.success(resultaat)
                    elif komt_voor:
                        st.warning(resultaat)
                    else:
                        st.info(resultaat)

                except Exception as e:
                    st.error(log_and_display_error(e, "word testing"))

    @staticmethod
    def _render_download_buttons():
        """Render download buttons for logs."""
        try:
            csv_path = "log/definities_log.csv"
            if os.path.exists(csv_path):
                with open(csv_path, "rb") as f:
                    st.download_button(
                        label="📥 Download CSV-logbestand",
                        data=f,
                        file_name="definities_log.csv",
                        mime="text/csv",
                    )
        except Exception as e:
            st.error(log_and_display_error(e, "download buttons"))

    @staticmethod
    def _render_validation_viewer():
        """Render validation structure viewer."""
        with st.expander("🧪 Validatie loggingstructuur", expanded=False):
            try:
                fouten = []

                # Check JSON log
                try:
                    with open("log/definities_log.json", encoding="utf-8") as f:
                        regels = [
                            json.loads(lijn) for lijn in f.readlines() if lijn.strip()
                        ]
                        if not all("expert_review" in regel for regel in regels):
                            fouten.append(
                                "❌ JSON-log mist veld 'expert_review' in één of meer regels."
                            )
                except Exception as e:
                    fouten.append(f"❌ Kon JSON-log niet lezen: {e}")

                # Check CSV log
                try:
                    df = pd.read_csv("log/definities_log.csv")
                    if "Expert-review" not in df.columns:
                        fouten.append("❌ CSV-log bevat geen kolom 'Expert-review'.")
                except Exception as e:
                    fouten.append(f"❌ Kon CSV-log niet lezen: {e}")

                if fouten:
                    for fout in fouten:
                        st.error(fout)
                else:
                    st.success("✅ Loggingstructuur is compleet.")

            except Exception as e:
                st.error(log_and_display_error(e, "validation viewer"))
