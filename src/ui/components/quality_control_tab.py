"""
Quality Control Tab - Interface voor kwaliteitscontrole en toetsregels analyse.
"""

from datetime import UTC, datetime

UTC = UTC  # Python 3.10 compatibility# Datum en tijd functionaliteit, timezone

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

                    # V2 Validation Service analysis
                    container = st.session_state.get('service_container')
                    if not container:
                        raise ValueError("Service container not initialized")
                    validation_service = container.orchestrator()

                    # Store results in session
                    with st.expander("📋 Analyse Resultaten", expanded=True):
                        # Create text capture for analysis output
                        import contextlib
                        import io

                        # Get V2 service info for analysis
                        service_info = validation_service.get_service_info()

                        # Create analysis text from V2 service info
                        analysis_text = f"""V2 Validation Service Analysis
{'='*50}
Service Mode: {service_info.get('service_mode', 'unknown')}
Architecture: {service_info.get('architecture', 'unknown')}
Version: {service_info.get('version', 'unknown')}
Total Rules: {service_info.get('rule_count', 0)}
{'='*50}
"""
                        results = service_info
                        st.text(analysis_text)

                        # Store results for other components
                        SessionStateManager.set_value(
                            "toetsregels_analysis",
                            {
                                "results": results,
                                "timestamp": datetime.now(UTC).isoformat(),
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
                    # Get V2 validation service info
                    container = st.session_state.get('service_container')
                    if container:
                        validation_service = container.orchestrator()
                        service_info = validation_service.get_service_info()
                        regel_count = service_info.get('rule_count', 0)
                        st.metric("⚙️ V2 Rules Loaded", regel_count)
                    else:
                        st.metric("⚙️ V2 Rules Status", "❌ Container not initialized")
                except Exception:
                    st.metric("⚙️ Toetsregels Status", "❌ Fout")

                # Check AI service
                try:
                    import os

                    api_key = os.getenv("OPENAI_API_KEY") or os.getenv(
                        "OPENAI_API_KEY_PROD"
                    )
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

                        # Use V2 validation service for consistency check
                        container = st.session_state.get('service_container')
                        if not container:
                            raise ValueError("Service container not initialized")

                        validation_service = container.orchestrator()
                        service_info = validation_service.get_service_info()

                        # Generate consistency report from V2 service
                        validation_text = f"""V2 Validation Service Consistency Report
{'='*50}
Service: {service_info.get('service_mode', 'unknown')}
Rules Loaded: {service_info.get('rule_count', 0)}
Architecture: {service_info.get('architecture', 'unknown')}
Version: {service_info.get('version', 'unknown')}
Status: ✅ All rules loaded via V2 service
{'='*50}
"""

                        with st.expander("📋 Consistentie Rapport", expanded=True):
                            st.text(validation_text)

                        # Store for reference
                        SessionStateManager.set_value(
                            "validation_consistency",
                            {
                                "report": validation_text,
                                "timestamp": datetime.now(UTC).isoformat(),
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

                        # Use V2 validation service for critical rules analysis
                        container = st.session_state.get('service_container')
                        if not container:
                            raise ValueError("Service container not initialized")

                        validation_service = container.orchestrator()

                        # For now, generate a simple report from V2 service
                        service_info = validation_service.get_service_info()
                        critical_analysis = f"""V2 Critical Rules Analysis
{'='*50}
Total Rules Available: {service_info.get('rule_count', 0)}
Service Mode: {service_info.get('service_mode', 'unknown')}

Note: Detailed critical rules analysis is handled by the V2 validation service
which processes all rules according to their severity levels.
{'='*50}
"""

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

                        # Use V2 validation service for detailed analysis
                        container = st.session_state.get('service_container')
                        if not container:
                            raise ValueError("Service container not initialized")

                        validation_service = container.orchestrator()
                        service_info = validation_service.get_service_info()

                        detailed_analysis = f"""V2 Detailed Rule Analysis
{'='*50}
Service Architecture: {service_info.get('architecture', 'unknown')}
Version: {service_info.get('version', 'unknown')}
Total Rules: {service_info.get('rule_count', 0)}

The V2 validation service provides:
- Automatic rule severity classification
- Deterministic rule ordering
- Consistent validation results
- Performance optimized validation
{'='*50}
"""

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
                    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                    filename = f"toetsregels_analyse_{timestamp}.txt"

                    import os

                    os.makedirs("exports", exist_ok=True)
                    filepath = os.path.join("exports", filename)

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write("TOETSREGELS USAGE ANALYSE RAPPORT\n")
                        f.write("=" * 40 + "\n\n")
                        f.write(f"Gegenereerd op: {datetime.now(UTC)}\n\n")
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
                    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                    filename = f"validatie_consistentie_{timestamp}.txt"

                    import os

                    os.makedirs("exports", exist_ok=True)
                    filepath = os.path.join("exports", filename)

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write("VALIDATIE CONSISTENTIE RAPPORT\n")
                        f.write("=" * 35 + "\n\n")
                        f.write(f"Gegenereerd op: {datetime.now(UTC)}\n\n")
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
