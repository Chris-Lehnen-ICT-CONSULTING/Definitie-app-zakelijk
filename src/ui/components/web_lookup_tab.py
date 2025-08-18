"""
Web Lookup Tab - Interface voor bron en definitie lookup functionaliteit.
"""

import asyncio
import re
from datetime import datetime

import pandas as pd
import streamlit as st

from database.definitie_repository import DefinitieRepository
from ui.session_state import SessionStateManager


class WebLookupTab:
    """Tab voor web lookup functionaliteit."""

    def __init__(self, repository: DefinitieRepository):
        """Initialiseer web lookup tab."""
        self.repository = repository
        self._init_lookup_modules()

    def _init_lookup_modules(self):
        """Initialiseer lookup modules."""
        # Legacy web lookup modules zijn verplaatst naar moderne service architectuur
        # Deze tab is tijdelijk gedeactiveerd tijdens de migratie
        
        try:
            # TODO: Implementeer moderne service integration
            # from services.modern_web_lookup_service import ModernWebLookupService
            # self.modern_service = ModernWebLookupService()
            
            # Voor nu tijdelijk gedeactiveerd
            self.BronZoeker = None
            self.legacy_modules_available = False
            
        except Exception as e:
            st.error(f"❌ Web lookup service migratie in uitvoering: {str(e)}")
            self.BronZoeker = None
            self.legacy_modules_available = False

    def render(self):
        """Render web lookup tab."""
        if not self.BronZoeker:
            st.info("🔄 **Web Lookup Service Migratie**")
            st.markdown("""
            De Web Lookup functionaliteit is gemigreerd naar een moderne service architectuur.
            
            **Nieuwe implementatie beschikbaar:**
            - ✅ ModernWebLookupService met Strangler Fig pattern
            - ✅ Wikipedia API integratie (47 tests passing)
            - ✅ SRU API voor Nederlandse juridische bronnen
            - ✅ A/B testing framework voor kwaliteitsvalidatie
            
            Deze UI tab wordt binnenkort bijgewerkt om de nieuwe services te gebruiken.
            """)
            return

        st.markdown("### 🔍 Web Lookup & Validatie")

        # Main interface
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "🔍 Definitie Zoeken",
                "📚 Bron Lookup",
                "⚖️ Juridische Lookup",
                "🔧 Validatie Tools",
            ]
        )

        with tab1:
            self._render_definitie_lookup()

        with tab2:
            self._render_bron_lookup()

        with tab3:
            self._render_juridische_lookup()

        with tab4:
            self._render_validatie_tools()

    def _render_definitie_lookup(self):
        """Render definitie lookup interface."""
        st.markdown("#### 🔍 Zoek Bestaande Definities")

        col1, col2 = st.columns([2, 1])

        with col1:
            zoek_term = st.text_input(
                "Zoekterm",
                placeholder="Voer begrip in om te zoeken...",
                key="definitie_zoek_term",
            )

        with col2:
            max_resultaten = st.number_input(
                "Max resultaten",
                min_value=1,
                max_value=50,
                value=10,
                key="definitie_max_resultaten",
            )

        # Zoek opties
        with st.expander("🔧 Geavanceerde Zoek Opties", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.checkbox("🏠 Interne database", value=True, key="include_internal")
                st.checkbox("🌐 Externe bronnen", value=True, key="include_external")

            with col2:
                st.slider(
                    "Min. relevantie",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.1,
                    key="min_relevantie",
                )

            with col3:
                st.checkbox("🔗 Zoek gerelateerde", value=True, key="zoek_gerelateerde")

        # Zoek knop
        if st.button("🔍 Zoek Definities", type="primary", key="zoek_definities_btn"):
            if zoek_term:
                with st.spinner("Zoeken naar definities..."):
                    try:
                        # Async call wrapper
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        resultaat = loop.run_until_complete(
                            self.zoek_definitie(
                                zoek_term, max_resultaten=max_resultaten
                            )
                        )

                        # Store results
                        SessionStateManager.set_value(
                            "definitie_zoek_resultaat",
                            {
                                "resultaat": resultaat,
                                "timestamp": datetime.now().isoformat(),
                            },
                        )

                        self._display_definitie_zoek_resultaten(resultaat)

                    except Exception as e:
                        st.error(f"❌ Zoekfout: {str(e)}")
            else:
                st.warning("⚠️ Voer een zoekterm in")

        # Toon vorige resultaten
        previous_results = SessionStateManager.get_value("definitie_zoek_resultaat")
        if previous_results:
            st.markdown("#### 📋 Laatste Zoekresultaten")
            self._display_definitie_zoek_resultaten(previous_results["resultaat"])

    def _display_definitie_zoek_resultaten(self, resultaat):
        """Display definitie zoek resultaten."""
        if not resultaat.gevonden_definities:
            st.info("🔍 Geen definities gevonden")
            return

        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📊 Totaal gevonden", resultaat.totaal_gevonden)

        with col2:
            st.metric("🎯 Exacte matches", len(resultaat.exacte_matches))

        with col3:
            st.metric("📈 Gedeeltelijke", len(resultaat.gedeeltelijke_matches))

        with col4:
            st.metric("⏱️ Zoektijd", f"{resultaat.zoek_tijd:.3f}s")

        # Suggesties
        if resultaat.suggesties:
            st.info(" | ".join(resultaat.suggesties))

        # Resultaten per categorie
        if resultaat.exacte_matches:
            with st.expander("🎯 Exacte Matches", expanded=True):
                for definitie in resultaat.exacte_matches:
                    self._render_definitie_item(definitie)

        if resultaat.gedeeltelijke_matches:
            with st.expander("📈 Gedeeltelijke Matches", expanded=False):
                for definitie in resultaat.gedeeltelijke_matches:
                    self._render_definitie_item(definitie)

        # Gerelateerde begrippen
        if resultaat.gerelateerde_begrippen:
            with st.expander("🔗 Gerelateerde Begrippen", expanded=False):
                for begrip in resultaat.gerelateerde_begrippen:
                    if st.button(f"🔍 {begrip}", key=f"related_{begrip}"):
                        SessionStateManager.set_value("definitie_zoek_term", begrip)
                        st.rerun()

        # Duplicaat analyse
        if (
            resultaat.duplicaat_analyse
            and resultaat.duplicaat_analyse.get("gevonden_duplicaten", 0) > 0
        ):
            with st.expander("⚠️ Mogelijke Duplicaten", expanded=False):
                for dup in resultaat.duplicaat_analyse["duplicaten"]:
                    st.warning(
                        f"🔄 {dup['definitie1']} ↔ {dup['definitie2']} (gelijkenis: {dup['gelijkenis']:.2f})"
                    )
                    st.caption(dup["aanbeveling"])

    def _render_definitie_item(self, definitie):
        """Render één definitie item."""
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**{definitie.get_display_name()}**")
                st.markdown(f"*{definitie.definitie}*")
                st.caption(f"Bron: {definitie.bron}")

            with col2:
                st.write(f"**Relevantie:** {definitie.relevantie:.2f}")
                st.write(f"**Betrouwbaarheid:** {definitie.betrouwbaarheid:.2f}")
                if definitie.rechtsgebied:
                    st.caption(f"Rechtsgebied: {definitie.rechtsgebied}")

            with col3:
                if definitie.url:
                    st.link_button("🔗 Bekijk bron", definitie.url)

                if st.button(
                    "📋 Kopieer", key=f"copy_{definitie.begrip}_{hash(definitie.bron)}"
                ):
                    st.code(definitie.definitie)
                    st.success("✅ Definitie gekopieerd!")

            st.markdown("---")

    def _render_bron_lookup(self):
        """Render bron lookup interface."""
        st.markdown("#### 📚 Bron Validatie & Lookup")

        # Input sectie
        col1, col2 = st.columns(2)

        with col1:
            zoek_mode = st.selectbox(
                "Zoek modus",
                ["🔍 Zoek bronnen", "✅ Valideer bronnen in tekst"],
                key="bron_zoek_mode",
            )

        with col2:
            max_bronnen = st.number_input(
                "Max bronnen",
                min_value=1,
                max_value=20,
                value=5,
                key="bron_max_resultaten",
            )

        if "Zoek bronnen" in zoek_mode:
            # Bron zoeken
            zoek_query = st.text_input(
                "Zoek bronnen voor begrip",
                placeholder="bijv. authenticatie, verificatie...",
                key="bron_zoek_query",
            )

            if st.button("🔍 Zoek Bronnen", type="primary", key="zoek_bronnen_btn"):
                if zoek_query:
                    with st.spinner("Zoeken naar bronnen..."):
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)

                            bron_zoeker = self.BronZoeker()
                            resultaat = loop.run_until_complete(
                                bron_zoeker.zoek_bronnen(
                                    zoek_query, max_resultaten=max_bronnen
                                )
                            )

                            SessionStateManager.set_value(
                                "bron_zoek_resultaat",
                                {
                                    "resultaat": resultaat,
                                    "timestamp": datetime.now().isoformat(),
                                },
                            )

                            self._display_bron_zoek_resultaten(resultaat)

                        except Exception as e:
                            st.error(f"❌ Bron zoek fout: {str(e)}")
                else:
                    st.warning("⚠️ Voer een zoekterm in")

        else:
            # Bronnen valideren in tekst
            tekst_input = st.text_area(
                "Tekst om te analyseren",
                placeholder="Voer tekst in met bronverwijzingen...",
                height=150,
                key="bron_validatie_tekst",
            )

            if st.button(
                "✅ Valideer Bronnen", type="primary", key="valideer_bronnen_btn"
            ):
                if tekst_input:
                    with st.spinner("Analyseren van bronverwijzingen..."):
                        try:
                            # Herken bronnen in tekst
                            gevonden_bronnen = self.herken_bronnen_in_definitie(
                                tekst_input
                            )

                            # Valideer bronnen
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)

                            validatie_resultaat = loop.run_until_complete(
                                self.valideer_definitie_bronnen(tekst_input)
                            )

                            SessionStateManager.set_value(
                                "bron_validatie_resultaat",
                                {
                                    "bronnen": gevonden_bronnen,
                                    "validatie": validatie_resultaat,
                                    "timestamp": datetime.now().isoformat(),
                                },
                            )

                            self._display_bron_validatie_resultaten(
                                gevonden_bronnen, validatie_resultaat
                            )

                        except Exception as e:
                            st.error(f"❌ Bron validatie fout: {str(e)}")
                else:
                    st.warning("⚠️ Voer tekst in om te analyseren")

        # Toon vorige resultaten
        if "Zoek bronnen" in zoek_mode:
            previous_results = SessionStateManager.get_value("bron_zoek_resultaat")
            if previous_results:
                st.markdown("#### 📋 Laatste Bron Zoekresultaten")
                self._display_bron_zoek_resultaten(previous_results["resultaat"])
        else:
            previous_results = SessionStateManager.get_value("bron_validatie_resultaat")
            if previous_results:
                st.markdown("#### 📋 Laatste Validatie Resultaten")
                self._display_bron_validatie_resultaten(
                    previous_results["bronnen"], previous_results["validatie"]
                )

    def _display_bron_zoek_resultaten(self, resultaat):
        """Display bron zoek resultaten."""
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📚 Bronnen gevonden", len(resultaat.gevonden_bronnen))

        with col2:
            st.metric("⏱️ Zoektijd", f"{resultaat.zoek_tijd:.3f}s")

        with col3:
            if resultaat.gevonden_bronnen:
                avg_betrouwbaarheid = sum(
                    b.betrouwbaarheid for b in resultaat.gevonden_bronnen
                ) / len(resultaat.gevonden_bronnen)
                st.metric("📊 Gem. betrouwbaarheid", f"{avg_betrouwbaarheid:.2f}")

        # Aanbevelingen
        if resultaat.aanbevelingen:
            for aanbeveling in resultaat.aanbevelingen:
                st.info(aanbeveling)

        # Bronnen lijst
        if resultaat.gevonden_bronnen:
            for i, bron in enumerate(resultaat.gevonden_bronnen):
                with st.expander(f"📚 {bron.naam}", expanded=i < 3):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.write(f"**Type:** {bron.type.value}")
                        if bron.artikel:
                            st.write(f"**Artikel:** {bron.artikel}")
                        if bron.datum:
                            st.write(f"**Datum:** {bron.datum}")

                    with col2:
                        st.write(f"**Betrouwbaarheid:** {bron.betrouwbaarheid:.2f}")
                        st.write(f"**Validiteit:** {bron.validiteit.value}")
                        toegankelijk_icon = "✅" if bron.toegankelijkheid else "❌"
                        st.write(f"**Toegankelijk:** {toegankelijk_icon}")

                    if bron.url:
                        st.link_button("🔗 Bekijk bron", bron.url)

    def _display_bron_validatie_resultaten(self, bronnen, validatie):
        """Display bron validatie resultaten."""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📚 Bronnen gevonden", validatie["aantal_bronnen"])

        with col2:
            st.metric("📊 Validatie score", f"{validatie['validatie_score']:.2f}")

        with col3:
            wettelijk_icon = "✅" if validatie["bevat_wettelijke_bronnen"] else "❌"
            st.metric("⚖️ Wettelijke bronnen", wettelijk_icon)

        with col4:
            st.metric(
                "🔗 Toegankelijk",
                f"{validatie['toegankelijke_bronnen']}/{validatie['aantal_bronnen']}",
            )

        # Aanbevelingen
        for aanbeveling in validatie["aanbevelingen"]:
            if "✅" in aanbeveling:
                st.success(aanbeveling)
            elif "⚠️" in aanbeveling or "💡" in aanbeveling:
                st.warning(aanbeveling)
            else:
                st.info(aanbeveling)

        # Gevonden bronnen details
        if bronnen:
            st.markdown("#### 📋 Gevonden Bronverwijzingen")

            for bron in bronnen:
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.markdown(f"**{bron.naam}**")
                        st.caption(f"Type: {bron.type.value}")

                    with col2:
                        st.write(f"Betrouwbaarheid: {bron.betrouwbaarheid:.2f}")
                        st.write(f"Validiteit: {bron.validiteit.value}")

                    with col3:
                        if bron.url:
                            st.link_button("🔗 Link", bron.url)

                    if bron.metadata and bron.metadata.get("match_text"):
                        st.code(bron.metadata["match_text"])

                    st.markdown("---")

    def _render_juridische_lookup(self):
        """Render juridische lookup interface."""
        st.markdown("#### ⚖️ Juridische Verwijzingen")

        tekst_input = st.text_area(
            "Tekst voor juridische analyse",
            placeholder="Voer tekst in met mogelijke wetsverwijzingen...",
            height=150,
            key="juridische_tekst_input",
        )

        col1, col2 = st.columns(2)

        with col1:
            log_resultaten = st.checkbox(
                "📝 Log resultaten",
                value=False,
                help="Sla gevonden verwijzingen op in log bestand",
                key="juridische_log",
            )

        with col2:
            begrip_context = st.text_input(
                "Begrip context",
                placeholder="Optioneel: begrip waarvoor gezocht wordt",
                key="juridische_begrip",
            )

        if st.button(
            "⚖️ Analyseer Juridische Verwijzingen",
            type="primary",
            key="juridische_analyse_btn",
        ):
            if tekst_input:
                with st.spinner("Analyseren van juridische verwijzingen..."):
                    try:
                        resultaten = self.zoek_wetsartikelstructuur(
                            tekst_input,
                            log_jsonl=log_resultaten,
                            bron="web_lookup_interface",
                            begrip=begrip_context,
                        )

                        SessionStateManager.set_value(
                            "juridische_resultaten",
                            {
                                "resultaten": resultaten,
                                "tekst": tekst_input,
                                "timestamp": datetime.now().isoformat(),
                            },
                        )

                        self._display_juridische_resultaten(resultaten, tekst_input)

                    except Exception as e:
                        st.error(f"❌ Juridische analyse fout: {str(e)}")
            else:
                st.warning("⚠️ Voer tekst in om te analyseren")

        # Toon vorige resultaten
        previous_results = SessionStateManager.get_value("juridische_resultaten")
        if previous_results:
            st.markdown("#### 📋 Laatste Juridische Analyse")
            self._display_juridische_resultaten(
                previous_results["resultaten"], previous_results["tekst"]
            )

    def _display_juridische_resultaten(self, resultaten, tekst):
        """Display juridische analyse resultaten."""
        if not resultaten:
            st.info("⚖️ Geen juridische verwijzingen gevonden")
            return

        st.success(f"✅ {len(resultaten)} juridische verwijzing(en) gevonden")

        # Resultaten tabel
        if resultaten:
            df_data = []
            for result in resultaten:
                df_data.append(
                    {
                        "Wet": result.get("wet", ""),
                        "Artikel": result.get("artikel", ""),
                        "Lid": result.get("lid", ""),
                        "Boek": result.get("boek", ""),
                        "Sub": result.get("sub", ""),
                        "Herkend via": result.get("herkend_via", ""),
                    }
                )

            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)

            # Gedetailleerde weergave
            with st.expander("🔍 Gedetailleerde Verwijzingen", expanded=False):
                for i, result in enumerate(resultaten):
                    st.markdown(f"**Verwijzing {i+1}:**")

                    col1, col2 = st.columns(2)

                    with col1:
                        for key, value in result.items():
                            if key != "herkend_via" and value:
                                st.write(f"**{key.capitalize()}:** {value}")

                    with col2:
                        st.write(
                            f"**Herkenning:** {result.get('herkend_via', 'Onbekend')}"
                        )

                        # Genereer link naar wetten.overheid.nl (voorbeeld)
                        if result.get("wet") and result.get("artikel"):
                            st.button(
                                "🔗 Zoek op Overheid.nl",
                                key=f"overheid_link_{i}",
                                help="Open wetten.overheid.nl (functionaliteit kan uitgebreid worden)",
                            )

                    st.markdown("---")

    def _render_validatie_tools(self):
        """Render validatie tools interface."""
        st.markdown("#### 🔧 Validatie & Analyse Tools")

        tool_type = st.selectbox(
            "Selecteer tool",
            [
                "🔄 Duplicaat Detectie",
                "📊 Definities Vergelijken",
                "🧹 Tekst Opschoning",
            ],
            key="validatie_tool_type",
        )

        if "Duplicaat Detectie" in tool_type:
            self._render_duplicaat_detectie()
        elif "Definities Vergelijken" in tool_type:
            self._render_definitie_vergelijking()
        elif "Tekst Opschoning" in tool_type:
            self._render_tekst_opschoning()

    def _render_duplicaat_detectie(self):
        """Render duplicaat detectie tool."""
        st.markdown("##### 🔄 Duplicaat Detectie")

        col1, col2 = st.columns(2)

        with col1:
            begrip_input = st.text_input(
                "Begrip", placeholder="Voer begrip in...", key="dup_begrip"
            )

        with col2:
            threshold = st.slider(
                "Gelijkenis threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.05,
                key="dup_threshold",
            )

        definitie_input = st.text_area(
            "Definitie om te controleren",
            placeholder="Voer definitie in om te controleren op duplicaten...",
            height=100,
            key="dup_definitie",
        )

        if st.button(
            "🔄 Detecteer Duplicaten", type="primary", key="detecteer_dup_btn"
        ):
            if begrip_input and definitie_input:
                with st.spinner("Zoeken naar mogelijke duplicaten..."):
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        resultaat = loop.run_until_complete(
                            self.detecteer_duplicaten(
                                begrip_input, definitie_input, threshold
                            )
                        )

                        self._display_duplicaat_resultaten(resultaat)

                    except Exception as e:
                        st.error(f"❌ Duplicaat detectie fout: {str(e)}")
            else:
                st.warning("⚠️ Voer zowel begrip als definitie in")

    def _display_duplicaat_resultaten(self, resultaat):
        """Display duplicaat detectie resultaten."""
        if resultaat["duplicaat_gevonden"]:
            st.warning(
                f"⚠️ {len(resultaat['mogelijke_duplicaten'])} mogelijke duplicaten gevonden!"
            )

            for dup in resultaat["mogelijke_duplicaten"]:
                with st.expander(
                    f"🔄 {dup['begrip']} (gelijkenis: {dup['gelijkenis']:.2f})",
                    expanded=True,
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Input definitie:**")
                        st.info(resultaat["input_definitie"])

                    with col2:
                        st.markdown("**Gevonden definitie:**")
                        st.info(dup["definitie"])

                    st.write(f"**Bron:** {dup['bron']}")
                    st.write(f"**Betrouwbaarheid:** {dup['betrouwbaarheid']:.2f}")

                    if dup["gelijkenis"] > 0.9:
                        st.error("🚨 Zeer hoge gelijkenis - mogelijk exacte duplicaat")
                    elif dup["gelijkenis"] > 0.8:
                        st.warning("⚠️ Hoge gelijkenis - controleer op duplicatie")
                    else:
                        st.info("💡 Moderate gelijkenis - mogelijk gerelateerd")
        else:
            st.success("✅ Geen duplicaten gevonden")

        st.info(resultaat["aanbeveling"])

    def _render_definitie_vergelijking(self):
        """Render definitie vergelijking tool."""
        st.markdown("##### 📊 Definities Vergelijken")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Definitie 1:**")
            def1 = st.text_area(
                "Eerste definitie",
                placeholder="Voer eerste definitie in...",
                height=100,
                key="vergelijk_def1",
            )

        with col2:
            st.markdown("**Definitie 2:**")
            def2 = st.text_area(
                "Tweede definitie",
                placeholder="Voer tweede definitie in...",
                height=100,
                key="vergelijk_def2",
            )

        if st.button("📊 Vergelijk Definities", type="primary", key="vergelijk_btn"):
            if def1 and def2:
                try:
                    # Import gelijkenis analyzer
                    from web_lookup.definitie_lookup import DefinitieGelijkenisAnalyzer

                    analyzer = DefinitieGelijkenisAnalyzer()
                    gelijkenis = analyzer.bereken_gelijkenis(def1, def2)

                    # Display resultaat
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("📊 Gelijkenis Score", f"{gelijkenis:.3f}")

                    with col2:
                        if gelijkenis > 0.8:
                            st.success("🟢 Hoge gelijkenis")
                        elif gelijkenis > 0.5:
                            st.warning("🟡 Moderate gelijkenis")
                        else:
                            st.info("🔵 Lage gelijkenis")

                    with col3:
                        percentage = gelijkenis * 100
                        st.metric("📈 Percentage", f"{percentage:.1f}%")

                    # Interpretatie
                    if gelijkenis > 0.9:
                        st.error("🚨 Zeer hoge gelijkenis - mogelijk duplicaat")
                    elif gelijkenis > 0.7:
                        st.warning("⚠️ Hoge gelijkenis - controleer op overlap")
                    elif gelijkenis > 0.4:
                        st.info("💡 Moderate gelijkenis - mogelijk gerelateerd")
                    else:
                        st.success("✅ Lage gelijkenis - waarschijnlijk uniek")

                except Exception as e:
                    st.error(f"❌ Vergelijking fout: {str(e)}")
            else:
                st.warning("⚠️ Voer beide definities in")

    def _render_tekst_opschoning(self):
        """Render tekst opschoning tool."""
        st.markdown("##### 🧹 Tekst Opschoning")

        tekst_input = st.text_area(
            "Tekst om op te schonen",
            placeholder="Voer tekst in die opgeschoond moet worden...",
            height=150,
            key="opschoon_tekst",
        )

        # Opschoon opties
        with st.expander("🔧 Opschoon Opties", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                remove_extra_spaces = st.checkbox(
                    "Remove extra spaces", value=True, key="remove_spaces"
                )
                normalize_punctuation = st.checkbox(
                    "Normalize punctuation", value=True, key="norm_punct"
                )
                fix_capitalization = st.checkbox(
                    "Fix capitalization", value=False, key="fix_caps"
                )

            with col2:
                remove_line_breaks = st.checkbox(
                    "Remove line breaks", value=False, key="remove_breaks"
                )
                standardize_quotes = st.checkbox(
                    "Standardize quotes", value=True, key="std_quotes"
                )
                remove_extra_dots = st.checkbox(
                    "Remove extra dots", value=True, key="remove_dots"
                )

        if st.button("🧹 Schoon Tekst Op", type="primary", key="opschoon_btn"):
            if tekst_input:
                try:
                    # Basic text cleaning
                    cleaned_text = tekst_input

                    if remove_extra_spaces:
                        cleaned_text = re.sub(r"\s+", " ", cleaned_text)

                    if normalize_punctuation:
                        cleaned_text = re.sub(r"\s*([,.;:!?])\s*", r"\1 ", cleaned_text)

                    if standardize_quotes:
                        cleaned_text = cleaned_text.replace('"', '"').replace('"', '"')
                        cleaned_text = cleaned_text.replace(""", "'").replace(""", "'")

                    if remove_line_breaks:
                        cleaned_text = cleaned_text.replace("\n", " ").replace(
                            "\r", " "
                        )

                    if remove_extra_dots:
                        cleaned_text = re.sub(r"\.{2,}", ".", cleaned_text)

                    if fix_capitalization:
                        sentences = cleaned_text.split(". ")
                        sentences = [s.strip().capitalize() for s in sentences]
                        cleaned_text = ". ".join(sentences)

                    cleaned_text = cleaned_text.strip()

                    # Display resultaat
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Originele tekst:**")
                        st.text_area(
                            "Origineel",
                            tekst_input,
                            height=100,
                            disabled=True,
                            key="orig_display",
                        )

                    with col2:
                        st.markdown("**Opgeschoonde tekst:**")
                        st.text_area(
                            "Opgeschoond",
                            cleaned_text,
                            height=100,
                            key="cleaned_display",
                        )

                    # Statistics
                    orig_length = len(tekst_input)
                    clean_length = len(cleaned_text)
                    reduction = (
                        ((orig_length - clean_length) / orig_length * 100)
                        if orig_length > 0
                        else 0
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("📏 Originele lengte", orig_length)

                    with col2:
                        st.metric("📏 Nieuwe lengte", clean_length)

                    with col3:
                        st.metric("📉 Reductie", f"{reduction:.1f}%")

                except Exception as e:
                    st.error(f"❌ Opschoon fout: {str(e)}")
            else:
                st.warning("⚠️ Voer tekst in om op te schonen")
