"""
Quality Control Tab - Interface voor kwaliteitscontrole en toetsregels analyse.
"""

from datetime import datetime, timezone  # Datum en tijd functionaliteit, timezone

import streamlit as st  # Streamlit web interface framework

from database.definitie_repository import (  # Database toegang voor definities
    DefinitieRepository,
)
from ui.session_state import (  # Sessie status management voor Streamlit
    SessionStateManager,
)


class QualityControlTab:
    """Tab voor kwaliteitscontrole en system health.

    Biedt dashboard voor kwaliteitsmetriek monitoring, toetsregel analyse,
    en systeem gezondheid controle van de DefinitieAgent applicatie.
    """

    def __init__(self, repository: DefinitieRepository):
        """Initialiseer quality control tab met database repository."""
        self.repository = repository  # Database repository voor definitie data toegang

    def render(self):
        """Render quality control tab."""
        st.markdown("### 🔧 Kwaliteitscontrole Dashboard")

        # Main sections
        col1, col2 = st.columns([1, 1])

        with col1:
            self._render_toetsregels_analysis()

        with col2:
            self._render_system_health()

        # Full width sections
        st.markdown("---")
        self._render_validation_consistency()

        st.markdown("---")
        self._render_rule_coverage_analysis()

    def _render_toetsregels_analysis(self):
        """Render toetsregels usage analyse."""
        st.markdown("#### 📊 Toetsregels Analyse")

        if st.button("🔍 Voer Analyse Uit", type="primary"):
            with st.spinner("Analyseer toetsregels gebruik..."):
                try:
                    # Import analysis module dynamically
                    import sys
                    from pathlib import Path

                    sys.path.append(str(Path(__file__).parents[2] / "analysis"))

                    from toetsregels_usage_analysis import (
                        analyze_critical_rules,
                        analyze_rule_usage,
                    )

                    # Store results in session
                    with st.expander("📋 Analyse Resultaten", expanded=True):
                        # Create text capture for analysis output
                        import contextlib
                        import io

                        # Capture print output
                        captured_output = io.StringIO()
                        with contextlib.redirect_stdout(captured_output):
                            results = analyze_rule_usage()
                            analyze_critical_rules()

                        # Display captured output
                        analysis_text = captured_output.getvalue()
                        st.text(analysis_text)

                        # Store results for other components
                        SessionStateManager.set_value(
                            "toetsregels_analysis",
                            {
                                "results": results,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "analysis_text": analysis_text,
                            },
                        )

                        st.success("✅ Analyse voltooid!")

                except Exception as e:
                    st.error(f"❌ Fout bij analyse: {e!s}")
                    st.code(f"Foutdetails: {e}")

        # Show previous results if available
        previous_analysis = SessionStateManager.get_value("toetsregels_analysis")
        if previous_analysis:
            st.caption(
                f"Laatste analyse: {previous_analysis.get('timestamp', 'Onbekend')}"
            )

            if st.button("📄 Toon Laatste Resultaten"):
                with st.expander("📋 Vorige Analyse", expanded=True):
                    st.text(
                        previous_analysis.get("analysis_text", "Geen data beschikbaar")
                    )

    def _render_system_health(self):
        """Render system health metrics."""
        st.markdown("#### 🩺 System Health")

        try:
            # Database health
            recent_definitions = self.repository.search_definities(limit=5)

            col1, col2 = st.columns(2)

            with col1:
                st.metric("📊 Database Status", "✅ Actief")
                st.metric("📋 Recente Definities", len(recent_definitions))

            with col2:
                # Check config health
                try:
                    from config.config_loader import load_toetsregels

                    regels = load_toetsregels()
                    regel_count = len(regels.get("regels", {}))
                    st.metric("⚙️ Toetsregels Geladen", regel_count)
                except Exception:
                    st.metric("⚙️ Toetsregels Status", "❌ Fout")

                # Check AI service
                try:
                    import os

                    api_key = os.getenv("OPENAI_API_KEY")
                    ai_status = "✅ Geconfigureerd" if api_key else "❌ Ontbreekt"
                    st.metric("🤖 AI Service", ai_status)
                except Exception:
                    st.metric("🤖 AI Service", "❌ Fout")

        except Exception as e:
            st.error(f"❌ Kon system health niet laden: {e!s}")

    def _render_validation_consistency(self):
        """Render validation consistency check."""
        st.markdown("#### ✅ Validatie Consistentie")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔍 Check JSON-Python Consistentie"):
                with st.spinner("Controleer consistentie..."):
                    try:
                        # Import validator dynamically
                        import sys
                        from pathlib import Path

                        sys.path.append(
                            str(Path(__file__).parents[2] / "validatie_toetsregels")
                        )

                        from validator import valideer_toetsregels

                        # Paths for validation
                        config_path = (
                            Path(__file__).parents[2] / "config" / "toetsregels.json"
                        )
                        core_path = Path(__file__).parents[2] / "ai_toetser" / "core.py"

                        # Capture validation output
                        import contextlib
                        import io

                        captured_output = io.StringIO()
                        with contextlib.redirect_stdout(captured_output):
                            valideer_toetsregels(str(config_path), str(core_path))

                        validation_text = captured_output.getvalue()

                        with st.expander("📋 Consistentie Rapport", expanded=True):
                            st.text(validation_text)

                        # Store for reference
                        SessionStateManager.set_value(
                            "validation_consistency",
                            {
                                "report": validation_text,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                        )

                    except Exception as e:
                        st.error(f"❌ Validatie fout: {e!s}")

        with col2:
            if st.button("📊 Analyseer Kritieke Regels"):
                with st.spinner("Analyseer kritieke regels..."):
                    try:
                        import sys
                        from pathlib import Path

                        sys.path.append(str(Path(__file__).parents[2] / "analysis"))

                        import contextlib
                        import io

                        from toetsregels_usage_analysis import analyze_critical_rules

                        captured_output = io.StringIO()
                        with contextlib.redirect_stdout(captured_output):
                            analyze_critical_rules()

                        critical_analysis = captured_output.getvalue()

                        with st.expander("🚨 Kritieke Regels Analyse", expanded=True):
                            st.text(critical_analysis)

                    except Exception as e:
                        st.error(f"❌ Fout bij kritieke regels analyse: {e!s}")

        with col3:
            if st.button("🔧 Gedetailleerde Regel Analyse"):
                with st.spinner("Voer gedetailleerde analyse uit..."):
                    try:
                        import sys
                        from pathlib import Path

                        sys.path.append(str(Path(__file__).parents[2] / "analysis"))

                        import contextlib
                        import io

                        from toetsregels_usage_analysis import detailed_rule_analysis

                        captured_output = io.StringIO()
                        with contextlib.redirect_stdout(captured_output):
                            detailed_rule_analysis()

                        detailed_analysis = captured_output.getvalue()

                        with st.expander("🔍 Gedetailleerde Analyse", expanded=True):
                            st.text(detailed_analysis)

                    except Exception as e:
                        st.error(f"❌ Fout bij gedetailleerde analyse: {e!s}")

    def _render_rule_coverage_analysis(self):
        """Render rule coverage analysis."""
        st.markdown("#### 📈 Regel Coverage Analyse")

        # Get analysis data if available
        analysis_data = SessionStateManager.get_value("toetsregels_analysis")

        if analysis_data and "results" in analysis_data:
            results = analysis_data["results"]

            # Create coverage visualization
            col1, col2, col3, col4 = st.columns(4)

            # Calculate overall statistics
            all_gen_rules = set()
            all_val_rules = set()

            for category_data in results.values():
                all_gen_rules.update(category_data["generation"]["rule_ids"])
                all_val_rules.update(category_data["validation"]["rule_ids"])

            total_used = all_gen_rules | all_val_rules
            both_systems = all_gen_rules & all_val_rules

            with col1:
                st.metric("🔧 Generatie Regels", len(all_gen_rules))

            with col2:
                st.metric("🔍 Validatie Regels", len(all_val_rules))

            with col3:
                st.metric("⚡ Beide Systemen", len(both_systems))

            with col4:
                st.metric("📊 Totaal Gebruikt", len(total_used))

            # Category breakdown
            st.markdown("##### 📋 Coverage per Categorie")

            for category, data in results.items():
                with st.expander(f"📁 {category.upper()}", expanded=False):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write("**Generatie:**")
                        st.write(f"Regels: {data['generation']['count']}")
                        st.write(f"IDs: {', '.join(data['generation']['rule_ids'])}")

                    with col2:
                        st.write("**Validatie:**")
                        st.write(f"Regels: {data['validation']['count']}")
                        st.write(f"IDs: {', '.join(data['validation']['rule_ids'])}")

                    with col3:
                        st.write("**Overlap:**")
                        overlap_pct = data["comparison"]["overlap_percentage"]
                        st.write(f"Percentage: {overlap_pct:.1f}%")

                        if data["comparison"]["unused_rules"]:
                            st.write("**Ongebruikt:**")
                            st.write(f"{', '.join(data['comparison']['unused_rules'])}")

        else:
            st.info(
                "💡 Voer eerst een toetsregels analyse uit om coverage data te zien"
            )

    def _render_export_options(self):
        """Render export options for quality data."""
        st.markdown("#### 📁 Export Opties")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Export Analyse Rapport"):
                analysis_data = SessionStateManager.get_value("toetsregels_analysis")
                if analysis_data:
                    # Export analysis to file
                    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                    filename = f"toetsregels_analyse_{timestamp}.txt"

                    import os

                    os.makedirs("exports", exist_ok=True)
                    filepath = os.path.join("exports", filename)

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write("TOETSREGELS USAGE ANALYSE RAPPORT\n")
                        f.write("=" * 40 + "\n\n")
                        f.write(f"Gegenereerd op: {datetime.now(timezone.utc)}\n\n")
                        f.write(
                            analysis_data.get("analysis_text", "Geen data beschikbaar")
                        )

                    st.success(f"✅ Rapport geëxporteerd naar: {filepath}")
                else:
                    st.warning("⚠️ Geen analyse data beschikbaar om te exporteren")

        with col2:
            if st.button("✅ Export Validatie Rapport"):
                validation_data = SessionStateManager.get_value(
                    "validation_consistency"
                )
                if validation_data:
                    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                    filename = f"validatie_consistentie_{timestamp}.txt"

                    import os

                    os.makedirs("exports", exist_ok=True)
                    filepath = os.path.join("exports", filename)

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write("VALIDATIE CONSISTENTIE RAPPORT\n")
                        f.write("=" * 35 + "\n\n")
                        f.write(f"Gegenereerd op: {datetime.now(timezone.utc)}\n\n")
                        f.write(validation_data.get("report", "Geen data beschikbaar"))

                    st.success(f"✅ Validatie rapport geëxporteerd naar: {filepath}")
                else:
                    st.warning("⚠️ Geen validatie data beschikbaar om te exporteren")

        with col3:
            if st.button("🔧 Reset Analyse Cache"):
                SessionStateManager.clear_value("toetsregels_analysis")
                SessionStateManager.clear_value("validation_consistency")
                st.success("✅ Analyse cache gereset")
                st.rerun()
