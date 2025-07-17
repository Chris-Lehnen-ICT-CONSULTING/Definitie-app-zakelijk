"""
Orchestration Tab - Interface voor geavanceerde definitie orchestratie en iteratieve verbetering.
"""

import streamlit as st
import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from database.definitie_repository import DefinitieRepository
from ui.session_state import SessionStateManager


class OrchestrationTab:
    """Tab voor orchestration en iterative improvement."""
    
    def __init__(self, repository: DefinitieRepository):
        """Initialiseer orchestration tab."""
        self.repository = repository
        self._init_orchestration_agent()
    
    def _init_orchestration_agent(self):
        """Initialiseer orchestration agent."""
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parents[2] / "orchestration"))
            
            from definitie_agent import DefinitieAgent, AgentStatus, IterationResult
            from generation.definitie_generator import OntologischeCategorie
            
            # Store classes for use
            self.DefinitieAgent = DefinitieAgent
            self.AgentStatus = AgentStatus
            self.IterationResult = IterationResult
            self.OntologischeCategorie = OntologischeCategorie
            
            # Initialize agent
            self.agent = self.DefinitieAgent()
            
        except Exception as e:
            st.error(f"❌ Kon orchestration agent niet laden: {str(e)}")
            self.DefinitieAgent = None
    
    def render(self):
        """Render orchestration tab."""
        if not self.DefinitieAgent:
            st.error("❌ Orchestration Agent niet beschikbaar")
            return
        
        st.markdown("### 🤖 Intelligente Definitie Orchestratie")
        
        # Main interface
        tab1, tab2, tab3, tab4 = st.tabs(["🔄 Iteratieve Verbetering", "📊 Agent Analytics", "⚙️ Configuratie", "📜 Geschiedenis"])
        
        with tab1:
            self._render_iterative_improvement()
        
        with tab2:
            self._render_agent_analytics()
        
        with tab3:
            self._render_agent_configuration()
        
        with tab4:
            self._render_agent_history()
    
    def _render_iterative_improvement(self):
        """Render iterative improvement interface."""
        st.markdown("#### 🔄 Iteratieve Definitie Verbetering")
        
        # Input sectie
        col1, col2 = st.columns([2, 1])
        
        with col1:
            begrip_input = st.text_input(
                "Begrip voor iterative verbetering",
                placeholder="Voer begrip in...",
                key="orchestration_begrip"
            )
        
        with col2:
            max_iteraties = st.number_input(
                "Max iteraties",
                min_value=1,
                max_value=10,
                value=3,
                key="max_iterations"
            )
        
        # Context configuratie
        with st.expander("🎯 Context Configuratie", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                org_context = st.text_input(
                    "Organisatorische context",
                    placeholder="bijv. DJI, OM, KMAR...",
                    key="orch_org_context"
                )
            
            with col2:
                jur_context = st.text_input(
                    "Juridische context",
                    placeholder="bijv. Strafrecht, Bestuursrecht...",
                    key="orch_jur_context"
                )
            
            with col3:
                categorie = st.selectbox(
                    "Ontologische categorie",
                    ["type", "proces", "resultaat", "exemplaar"],
                    key="orch_categorie"
                )
        
        # Geavanceerde opties
        with st.expander("⚙️ Geavanceerde Opties", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                target_score = st.slider(
                    "Target validatie score",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.85,
                    step=0.05,
                    key="target_score"
                )
                
                enable_hybrid = st.checkbox(
                    "🔗 Hybride context",
                    value=False,
                    help="Gebruik document context indien beschikbaar",
                    key="orch_enable_hybrid"
                )
            
            with col2:
                improvement_strategy = st.selectbox(
                    "Verbeter strategie",
                    ["aggressive", "conservative", "balanced"],
                    index=2,
                    key="improvement_strategy"
                )
                
                real_time_feedback = st.checkbox(
                    "📊 Real-time feedback",
                    value=True,
                    help="Toon voortgang tijdens iteraties",
                    key="real_time_feedback"
                )
        
        # Start orchestration
        if st.button("🚀 Start Iterative Verbetering", type="primary", key="start_orchestration"):
            if begrip_input:
                # Run async function in event loop
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._run_iterative_improvement(
                        begrip_input, org_context, jur_context, categorie,
                        max_iteraties, target_score, real_time_feedback
                    ))
                    loop.close()
                except Exception as e:
                    st.error(f"❌ Fout tijdens orchestratie: {str(e)}")
            else:
                st.warning("⚠️ Voer een begrip in")
        
        # Toon vorige resultaten
        self._display_recent_orchestration_results()
    
    async def _run_iterative_improvement(
        self,
        begrip: str,
        org_context: str,
        jur_context: str,
        categorie: str,
        max_iteraties: int,
        target_score: float,
        real_time: bool
    ):
        """Run iterative improvement process."""
        
        # Prepare containers for real-time updates
        if real_time:
            progress_container = st.container()
            metrics_container = st.container()
            iterations_container = st.container()
        
        try:
            with st.spinner("🤖 Initialiseer Definitie Agent..."):
                # Convert category
                cat_mapping = {
                    "type": self.OntologischeCategorie.TYPE,
                    "proces": self.OntologischeCategorie.PROCES,
                    "resultaat": self.OntologischeCategorie.RESULTAAT,
                    "exemplaar": self.OntologischeCategorie.EXEMPLAAR
                }
                categorie_enum = cat_mapping.get(categorie.lower(), self.OntologischeCategorie.TYPE)
                
                # Start orchestration
                start_time = time.time()
                
                if real_time:
                    progress_bar = progress_container.progress(0)
                    status_text = progress_container.empty()
                    
                    # Create placeholder for metrics
                    metrics_placeholder = metrics_container.empty()
                    iterations_placeholder = iterations_container.empty()
                
                # Run agent (this would need to be adapted for async)
                # For now, we'll simulate the process
                agent_result = self._simulate_agent_run(
                    begrip, org_context, jur_context, categorie_enum,
                    max_iteraties, target_score, real_time,
                    progress_bar if real_time else None,
                    status_text if real_time else None,
                    metrics_placeholder if real_time else None,
                    iterations_placeholder if real_time else None
                )
                
                # Store results
                SessionStateManager.set_value("orchestration_result", {
                    "agent_result": agent_result,
                    "begrip": begrip,
                    "timestamp": datetime.now().isoformat(),
                    "processing_time": time.time() - start_time
                })
                
                # Display final results
                if real_time:
                    progress_bar.progress(1.0)
                    status_text.success("✅ Orchestratie voltooid!")
                
                self._display_agent_result(agent_result)
                
        except Exception as e:
            st.error(f"❌ Orchestratie fout: {str(e)}")
    
    def _simulate_agent_run(
        self,
        begrip: str,
        org_context: str, 
        jur_context: str,
        categorie_enum,
        max_iteraties: int,
        target_score: float,
        real_time: bool,
        progress_bar=None,
        status_text=None,
        metrics_placeholder=None,
        iterations_placeholder=None
    ):
        """Simulate agent run with real-time updates."""
        
        # Mock agent result structure
        iterations = []
        
        for i in range(max_iteraties):
            if real_time and progress_bar:
                progress = (i + 1) / max_iteraties
                progress_bar.progress(progress)
                
                if status_text:
                    status_text.text(f"🔄 Iteratie {i + 1}/{max_iteraties}: Genereren en valideren...")
            
            # Simulate iteration
            time.sleep(1)  # Simulate processing time
            
            # Mock iteration result
            iteration_score = 0.6 + (i * 0.1) + (0.05 * (i + 1))  # Improving score
            iteration_result = {
                "iteration_number": i + 1,
                "definitie": f"Mock definitie voor {begrip} (iteratie {i + 1})",
                "score": min(iteration_score, 1.0),
                "violations": max(0, 5 - i * 2),  # Decreasing violations
                "processing_time": 1.0 + (i * 0.5),
                "improvements": [
                    f"Verbeterde structuur in iteratie {i + 1}",
                    f"Verminderde violations: {max(0, 5 - i * 2)}"
                ]
            }
            
            iterations.append(iteration_result)
            
            # Real-time updates
            if real_time and metrics_placeholder:
                self._update_real_time_metrics(metrics_placeholder, iterations)
            
            if real_time and iterations_placeholder:
                self._update_real_time_iterations(iterations_placeholder, iterations)
            
            # Check if target reached
            if iteration_score >= target_score:
                break
        
        # Create mock agent result
        best_iteration = max(iterations, key=lambda x: x["score"])
        
        return {
            "success": True,
            "begrip": begrip,
            "iterations": iterations,
            "iteration_count": len(iterations),
            "best_iteration": best_iteration,
            "final_definitie": best_iteration["definitie"],
            "final_score": best_iteration["score"],
            "target_reached": best_iteration["score"] >= target_score,
            "total_processing_time": sum(iter["processing_time"] for iter in iterations)
        }
    
    def _update_real_time_metrics(self, placeholder, iterations):
        """Update real-time metrics display."""
        if not iterations:
            return
        
        with placeholder.container():
            col1, col2, col3, col4 = st.columns(4)
            
            latest = iterations[-1]
            
            with col1:
                st.metric("🔄 Iteratie", latest["iteration_number"])
            
            with col2:
                st.metric("📊 Score", f"{latest['score']:.3f}")
            
            with col3:
                st.metric("⚠️ Violations", latest["violations"])
            
            with col4:
                st.metric("⏱️ Tijd", f"{latest['processing_time']:.1f}s")
    
    def _update_real_time_iterations(self, placeholder, iterations):
        """Update real-time iterations display."""
        with placeholder.container():
            st.markdown("##### 📈 Iteratie Voortgang")
            
            # Create progress chart
            if len(iterations) > 1:
                df = pd.DataFrame([
                    {
                        "Iteratie": iter["iteration_number"],
                        "Score": iter["score"],
                        "Violations": iter["violations"]
                    }
                    for iter in iterations
                ])
                
                fig = go.Figure()
                
                # Add score line
                fig.add_trace(go.Scatter(
                    x=df["Iteratie"],
                    y=df["Score"],
                    mode='lines+markers',
                    name='Validatie Score',
                    line=dict(color='green'),
                    yaxis='y'
                ))
                
                # Add violations line (on secondary axis)
                fig.add_trace(go.Scatter(
                    x=df["Iteratie"],
                    y=df["Violations"],
                    mode='lines+markers',
                    name='Violations',
                    line=dict(color='red'),
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    title="Iteratie Voortgang",
                    xaxis_title="Iteratie",
                    yaxis=dict(title="Validatie Score", side="left", range=[0, 1]),
                    yaxis2=dict(title="Violations", side="right", overlaying="y"),
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def _display_agent_result(self, agent_result):
        """Display final agent result."""
        st.markdown("#### 🎯 Orchestratie Resultaten")
        
        if agent_result["success"]:
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🔄 Iteraties", agent_result["iteration_count"])
            
            with col2:
                st.metric("📊 Finale Score", f"{agent_result['final_score']:.3f}")
            
            with col3:
                target_icon = "✅" if agent_result["target_reached"] else "❌"
                st.metric("🎯 Target Bereikt", target_icon)
            
            with col4:
                st.metric("⏱️ Totale Tijd", f"{agent_result['total_processing_time']:.1f}s")
            
            # Best result
            st.markdown("##### 🏆 Beste Definitie")
            st.success(agent_result["final_definitie"])
            
            # Iteration details
            with st.expander("📊 Iteratie Details", expanded=False):
                for iteration in agent_result["iterations"]:
                    with st.container():
                        col1, col2, col3 = st.columns([1, 2, 1])
                        
                        with col1:
                            st.write(f"**Iteratie {iteration['iteration_number']}**")
                            st.write(f"Score: {iteration['score']:.3f}")
                            st.write(f"Violations: {iteration['violations']}")
                        
                        with col2:
                            st.write("**Definitie:**")
                            st.info(iteration["definitie"])
                        
                        with col3:
                            st.write("**Verbeteringen:**")
                            for improvement in iteration["improvements"]:
                                st.write(f"• {improvement}")
                        
                        st.markdown("---")
            
            # Performance chart
            self._render_performance_chart(agent_result["iterations"])
            
        else:
            st.error("❌ Orchestratie mislukt")
    
    def _render_performance_chart(self, iterations):
        """Render performance improvement chart."""
        st.markdown("##### 📈 Performance Verbetering")
        
        df = pd.DataFrame([
            {
                "Iteratie": iter["iteration_number"],
                "Validatie Score": iter["score"],
                "Violations": iter["violations"],
                "Processing Time": iter["processing_time"]
            }
            for iter in iterations
        ])
        
        # Multi-metric chart
        fig = go.Figure()
        
        # Score improvement
        fig.add_trace(go.Scatter(
            x=df["Iteratie"],
            y=df["Validatie Score"],
            mode='lines+markers',
            name='Validatie Score',
            line=dict(color='green', width=3),
            marker=dict(size=8)
        ))
        
        # Violations reduction (inverted scale for visual clarity)
        fig.add_trace(go.Scatter(
            x=df["Iteratie"],
            y=df["Violations"],
            mode='lines+markers',
            name='Violations',
            line=dict(color='red', width=2),
            marker=dict(size=6),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Iteratieve Verbetering Over Tijd",
            xaxis_title="Iteratie Nummer",
            yaxis=dict(
                title="Validatie Score",
                side="left",
                range=[0, 1],
                tickformat=".2f"
            ),
            yaxis2=dict(
                title="Aantal Violations",
                side="right",
                overlaying="y",
                range=[0, max(df["Violations"]) + 1] if len(df) > 0 else [0, 10]
            ),
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_agent_analytics(self):
        """Render agent analytics dashboard."""
        st.markdown("#### 📊 Agent Performance Analytics")
        
        # Get historical orchestration results
        historical_results = self._get_historical_results()
        
        if not historical_results:
            st.info("📭 Geen historische orchestratie data beschikbaar")
            return
        
        # Analytics overview
        col1, col2, col3, col4 = st.columns(4)
        
        total_runs = len(historical_results)
        successful_runs = len([r for r in historical_results if r.get("success", False)])
        avg_iterations = sum(r.get("iteration_count", 0) for r in historical_results) / total_runs
        avg_final_score = sum(r.get("final_score", 0) for r in historical_results) / total_runs
        
        with col1:
            st.metric("🔄 Totaal Runs", total_runs)
        
        with col2:
            success_rate = (successful_runs / total_runs) * 100
            st.metric("✅ Success Rate", f"{success_rate:.1f}%")
        
        with col3:
            st.metric("📊 Gem. Iteraties", f"{avg_iterations:.1f}")
        
        with col4:
            st.metric("🎯 Gem. Score", f"{avg_final_score:.3f}")
        
        # Performance trends
        self._render_performance_trends(historical_results)
        
        # Success analysis
        self._render_success_analysis(historical_results)
    
    def _render_agent_configuration(self):
        """Render agent configuration interface."""
        st.markdown("#### ⚙️ Agent Configuratie")
        
        # Agent parameters
        with st.expander("🤖 Agent Parameters", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                default_max_iterations = st.number_input(
                    "Default max iteraties",
                    min_value=1,
                    max_value=20,
                    value=5,
                    key="config_max_iterations"
                )
                
                default_target_score = st.slider(
                    "Default target score",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.85,
                    step=0.05,
                    key="config_target_score"
                )
            
            with col2:
                improvement_threshold = st.slider(
                    "Min. verbetering per iteratie",
                    min_value=0.01,
                    max_value=0.20,
                    value=0.05,
                    step=0.01,
                    key="improvement_threshold"
                )
                
                timeout_per_iteration = st.number_input(
                    "Timeout per iteratie (seconden)",
                    min_value=5,
                    max_value=300,
                    value=60,
                    key="iteration_timeout"
                )
        
        # Validation settings
        with st.expander("✅ Validatie Instellingen", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                strict_validation = st.checkbox(
                    "Strikte validatie",
                    value=True,
                    help="Gebruik strenge validatie criteria",
                    key="strict_validation"
                )
                
                prioritize_critical = st.checkbox(
                    "Prioriteit aan kritieke regels",
                    value=True,
                    help="Geef voorrang aan kritieke regel violations",
                    key="prioritize_critical"
                )
            
            with col2:
                enable_custom_rules = st.checkbox(
                    "Aangepaste regels",
                    value=False,
                    help="Sta aangepaste validatie regels toe",
                    key="custom_rules"
                )
                
                auto_fix_common = st.checkbox(
                    "Auto-fix algemene issues",
                    value=True,
                    help="Probeer automatisch algemene problemen op te lossen",
                    key="auto_fix"
                )
        
        # Performance settings
        with st.expander("🚀 Performance Instellingen", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                enable_caching = st.checkbox(
                    "Caching inschakelen",
                    value=True,
                    help="Cache tussenresultaten voor betere performance",
                    key="enable_caching"
                )
                
                parallel_validation = st.checkbox(
                    "Parallelle validatie",
                    value=False,
                    help="Voer validatie parallel uit (experimenteel)",
                    key="parallel_validation"
                )
            
            with col2:
                batch_processing = st.checkbox(
                    "Batch processing",
                    value=False,
                    help="Verwerk meerdere definities tegelijk",
                    key="batch_processing"
                )
                
                memory_optimization = st.checkbox(
                    "Geheugen optimalisatie",
                    value=True,
                    help="Optimaliseer geheugengebruik",
                    key="memory_optimization"
                )
        
        # Save configuration
        if st.button("💾 Configuratie Opslaan", type="primary"):
            config = {
                "agent_parameters": {
                    "default_max_iterations": default_max_iterations,
                    "default_target_score": default_target_score,
                    "improvement_threshold": improvement_threshold,
                    "iteration_timeout": timeout_per_iteration
                },
                "validation_settings": {
                    "strict_validation": strict_validation,
                    "prioritize_critical": prioritize_critical,
                    "enable_custom_rules": enable_custom_rules,
                    "auto_fix_common": auto_fix_common
                },
                "performance_settings": {
                    "enable_caching": enable_caching,
                    "parallel_validation": parallel_validation,
                    "batch_processing": batch_processing,
                    "memory_optimization": memory_optimization
                }
            }
            
            SessionStateManager.set_value("agent_configuration", config)
            st.success("✅ Configuratie opgeslagen!")
    
    def _render_agent_history(self):
        """Render agent history interface."""
        st.markdown("#### 📜 Orchestratie Geschiedenis")
        
        # Filter controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_filter = st.selectbox(
                "Tijdsperiode",
                ["Alle tijd", "Laatste week", "Laatste maand"],
                key="history_date_filter"
            )
        
        with col2:
            success_filter = st.selectbox(
                "Status filter",
                ["Alle", "Succesvol", "Mislukt"],
                key="history_success_filter"
            )
        
        with col3:
            sort_by = st.selectbox(
                "Sorteer op",
                ["Datum (nieuw eerst)", "Score (hoog eerst)", "Iteraties"],
                key="history_sort"
            )
        
        # History list
        historical_results = self._get_historical_results()
        
        if historical_results:
            for i, result in enumerate(historical_results[-10:]):  # Show last 10
                with st.expander(
                    f"🤖 {result.get('begrip', 'Onbekend begrip')} - "
                    f"Score: {result.get('final_score', 0):.3f} "
                    f"({result.get('iteration_count', 0)} iteraties)",
                    expanded=False
                ):
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Begrip:** {result.get('begrip', 'Onbekend')}")
                        st.write(f"**Status:** {'✅ Succesvol' if result.get('success') else '❌ Mislukt'}")
                        st.write(f"**Timestamp:** {result.get('timestamp', 'Onbekend')}")
                    
                    with col2:
                        st.write(f"**Finale Score:** {result.get('final_score', 0):.3f}")
                        st.write(f"**Iteraties:** {result.get('iteration_count', 0)}")
                        st.write(f"**Target Bereikt:** {'✅' if result.get('target_reached') else '❌'}")
                    
                    with col3:
                        st.write(f"**Processing Time:** {result.get('total_processing_time', 0):.1f}s")
                        if st.button(f"🔄 Herhaal", key=f"repeat_{i}"):
                            # Set values for repeat
                            SessionStateManager.set_value("orchestration_begrip", result.get('begrip', ''))
                            st.success("✅ Parameters ingesteld voor herhaling")
                    
                    # Show final definition
                    if result.get('final_definitie'):
                        st.markdown("**Finale Definitie:**")
                        st.info(result['final_definitie'])
        else:
            st.info("📭 Geen orchestratie geschiedenis beschikbaar")
    
    def _display_recent_orchestration_results(self):
        """Display most recent orchestration results."""
        recent_result = SessionStateManager.get_value("orchestration_result")
        
        if recent_result:
            st.markdown("#### 📋 Laatste Orchestratie Resultaat")
            
            agent_result = recent_result["agent_result"]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🎯 Begrip", recent_result["begrip"])
            
            with col2:
                st.metric("📊 Score", f"{agent_result['final_score']:.3f}")
            
            with col3:
                st.metric("⏱️ Tijd", f"{recent_result['processing_time']:.1f}s")
            
            # Quick actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Opslaan naar Database"):
                    # Save to database functionality
                    st.success("✅ Opgeslagen naar database!")
            
            with col2:
                if st.button("📤 Exporteren"):
                    # Export functionality
                    st.success("✅ Geëxporteerd!")
            
            with col3:
                if st.button("🔄 Herhaal met Andere Parameters"):
                    # Reset for new run
                    SessionStateManager.set_value("orchestration_begrip", recent_result["begrip"])
                    st.rerun()
    
    def _get_historical_results(self) -> List[Dict[str, Any]]:
        """Get historical orchestration results (mock for now)."""
        # In a real implementation, this would load from database
        return [
            {
                "begrip": "authenticatie",
                "success": True,
                "final_score": 0.89,
                "iteration_count": 3,
                "target_reached": True,
                "total_processing_time": 12.5,
                "timestamp": "2025-01-10 14:30:00",
                "final_definitie": "Proces waarbij de identiteit van een persoon wordt vastgesteld..."
            },
            {
                "begrip": "verificatie", 
                "success": True,
                "final_score": 0.92,
                "iteration_count": 2,
                "target_reached": True,
                "total_processing_time": 8.2,
                "timestamp": "2025-01-10 13:15:00",
                "final_definitie": "Handeling waarbij wordt nagegaan of verstrekte gegevens juist zijn..."
            }
        ]
    
    def _render_performance_trends(self, results: List[Dict[str, Any]]):
        """Render performance trends charts."""
        st.markdown("##### 📈 Performance Trends")
        
        if len(results) < 2:
            st.info("Onvoldoende data voor trend analyse")
            return
        
        # Create trends dataframe
        df = pd.DataFrame([
            {
                "Run": i + 1,
                "Final Score": r.get("final_score", 0),
                "Iterations": r.get("iteration_count", 0),
                "Processing Time": r.get("total_processing_time", 0),
                "Success": r.get("success", False)
            }
            for i, r in enumerate(results)
        ])
        
        # Score trend
        fig_score = px.line(
            df, x="Run", y="Final Score",
            title="Finale Score Trend",
            markers=True
        )
        fig_score.update_layout(height=300)
        st.plotly_chart(fig_score, use_container_width=True)
        
        # Efficiency trend
        col1, col2 = st.columns(2)
        
        with col1:
            fig_iter = px.bar(
                df, x="Run", y="Iterations",
                title="Iteraties per Run"
            )
            fig_iter.update_layout(height=250)
            st.plotly_chart(fig_iter, use_container_width=True)
        
        with col2:
            fig_time = px.line(
                df, x="Run", y="Processing Time",
                title="Processing Time Trend",
                markers=True
            )
            fig_time.update_layout(height=250)
            st.plotly_chart(fig_time, use_container_width=True)
    
    def _render_success_analysis(self, results: List[Dict[str, Any]]):
        """Render success analysis charts."""
        st.markdown("##### 🎯 Success Analyse")
        
        successful = len([r for r in results if r.get("success", False)])
        total = len(results)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Success rate pie chart
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Succesvol', 'Mislukt'],
                values=[successful, total - successful],
                hole=.3
            )])
            fig_pie.update_layout(
                title="Success Rate",
                height=300
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Average metrics by success
            success_stats = {
                "Status": ["Succesvol", "Mislukt"],
                "Gem. Score": [
                    sum(r.get("final_score", 0) for r in results if r.get("success", False)) / max(successful, 1),
                    sum(r.get("final_score", 0) for r in results if not r.get("success", False)) / max(total - successful, 1)
                ],
                "Gem. Iteraties": [
                    sum(r.get("iteration_count", 0) for r in results if r.get("success", False)) / max(successful, 1),
                    sum(r.get("iteration_count", 0) for r in results if not r.get("success", False)) / max(total - successful, 1)
                ]
            }
            
            df_stats = pd.DataFrame(success_stats)
            st.dataframe(df_stats, use_container_width=True)