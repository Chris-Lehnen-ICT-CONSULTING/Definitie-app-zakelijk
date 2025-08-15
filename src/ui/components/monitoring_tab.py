"""
Monitoring Tab - Interface voor API monitoring en performance tracking.
"""

import asyncio
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database.definitie_repository import DefinitieRepository
from ui.session_state import SessionStateManager


class MonitoringTab:
    """Tab voor monitoring en performance tracking."""

    def __init__(self, repository: DefinitieRepository):
        """Initialiseer monitoring tab."""
        self.repository = repository
        self._init_api_monitor()

    def _init_api_monitor(self):
        """Initialiseer API monitor."""
        try:
            import sys
            from pathlib import Path

            sys.path.append(str(Path(__file__).parents[2] / "monitoring"))

            from api_monitor import (
                AlertSeverity,
                CostCalculator,
                MetricsCollector,
                MetricType,
                get_metrics_collector,
                record_api_call,
            )

            # Store classes for use
            self.get_metrics_collector = get_metrics_collector
            self.record_api_call = record_api_call
            self.MetricsCollector = MetricsCollector
            self.CostCalculator = CostCalculator
            self.AlertSeverity = AlertSeverity
            self.MetricType = MetricType

            # Initialize collector
            self.collector = self.get_metrics_collector()

        except Exception as e:
            st.error(f"❌ Kon API monitor niet laden: {str(e)}")
            self.collector = None

    def render(self):
        """Render monitoring tab."""
        if not self.collector:
            st.error("❌ API Monitor niet beschikbaar")
            return

        st.markdown("### 📈 Monitoring Dashboard")

        # Main interface
        tab1, tab2, tab3, tab4 = st.tabs(
            ["🔴 Real-time", "📊 Metrics", "💰 Kosten", "⚠️ Alerts"]
        )

        with tab1:
            self._render_realtime_dashboard()

        with tab2:
            self._render_metrics_dashboard()

        with tab3:
            self._render_cost_dashboard()

        with tab4:
            self._render_alerts_dashboard()

    def _render_realtime_dashboard(self):
        """Render real-time monitoring dashboard."""
        st.markdown("#### 🔴 Real-time Performance")

        # Auto-refresh toggle
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            auto_refresh = st.checkbox(
                "🔄 Auto Refresh", value=False, key="auto_refresh"
            )

        with col2:
            refresh_interval = st.selectbox(
                "Refresh Rate",
                [5, 10, 30, 60],
                index=1,
                key="refresh_interval",
                help="Seconden tussen refreshes",
            )

        with col3:
            if st.button("🔄 Refresh Nu", type="primary"):
                st.rerun()

        # Get real-time metrics
        try:
            metrics = self.collector.get_realtime_metrics()

            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "📞 API Calls (5min)",
                    metrics["total_calls"],
                    help="Totaal aantal API calls in laatste 5 minuten",
                )

            with col2:
                success_rate = metrics["success_rate"] * 100
                st.metric(
                    "✅ Success Rate",
                    f"{success_rate:.1f}%",
                    help="Percentage succesvolle API calls",
                )

            with col3:
                cache_rate = metrics["cache_hit_rate"] * 100
                st.metric(
                    "💾 Cache Hit Rate",
                    f"{cache_rate:.1f}%",
                    help="Percentage cache hits",
                )

            with col4:
                avg_time = metrics["avg_response_time"]
                st.metric(
                    "⏱️ Avg Response Time",
                    f"{avg_time:.2f}s",
                    help="Gemiddelde response tijd",
                )

            # Performance indicators
            st.markdown("#### 🎯 Performance Indicators")

            col1, col2 = st.columns(2)

            with col1:
                # Response time gauge
                fig_response = go.Figure(
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=avg_time,
                        domain={"x": [0, 1], "y": [0, 1]},
                        title={"text": "Response Time (s)"},
                        delta={"reference": 3.0},
                        gauge={
                            "axis": {"range": [None, 10]},
                            "bar": {"color": "darkblue"},
                            "steps": [
                                {"range": [0, 3], "color": "lightgreen"},
                                {"range": [3, 7], "color": "yellow"},
                                {"range": [7, 10], "color": "red"},
                            ],
                            "threshold": {
                                "line": {"color": "red", "width": 4},
                                "thickness": 0.75,
                                "value": 7,
                            },
                        },
                    )
                )
                fig_response.update_layout(height=300)
                st.plotly_chart(fig_response, use_container_width=True)

            with col2:
                # Success rate gauge
                fig_success = go.Figure(
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=success_rate,
                        domain={"x": [0, 1], "y": [0, 1]},
                        title={"text": "Success Rate (%)"},
                        delta={"reference": 95},
                        gauge={
                            "axis": {"range": [None, 100]},
                            "bar": {"color": "darkgreen"},
                            "steps": [
                                {"range": [0, 80], "color": "red"},
                                {"range": [80, 95], "color": "yellow"},
                                {"range": [95, 100], "color": "lightgreen"},
                            ],
                            "threshold": {
                                "line": {"color": "red", "width": 4},
                                "thickness": 0.75,
                                "value": 90,
                            },
                        },
                    )
                )
                fig_success.update_layout(height=300)
                st.plotly_chart(fig_success, use_container_width=True)

            # Endpoint breakdown
            if metrics["endpoint_metrics"]:
                st.markdown("#### 🎯 Per Endpoint Metrics")

                endpoint_data = []
                for endpoint, ep_metrics in metrics["endpoint_metrics"].items():
                    endpoint_data.append(
                        {
                            "Endpoint": endpoint,
                            "Calls": ep_metrics["total_calls"],
                            "Success Rate": f"{ep_metrics['success_rate']*100:.1f}%",
                            "Avg Response": f"{ep_metrics['avg_response_time']:.2f}s",
                            "Cache Hit Rate": f"{ep_metrics['cache_hit_rate']*100:.1f}%",
                            "Cost": f"${ep_metrics['total_cost']:.4f}",
                        }
                    )

                df_endpoints = pd.DataFrame(endpoint_data)
                st.dataframe(df_endpoints, use_container_width=True)

            # Active alerts
            if metrics["active_alerts"]:
                st.markdown("#### ⚠️ Actieve Alerts")
                for alert in metrics["active_alerts"]:
                    severity_color = {
                        "info": "🔵",
                        "warning": "🟡",
                        "error": "🟠",
                        "critical": "🔴",
                    }.get(alert["severity"], "⚪")

                    st.warning(
                        f"{severity_color} **{alert['name']}** - Laatste trigger: {alert['last_triggered']} (Count: {alert['trigger_count']})"
                    )

        except Exception as e:
            st.error(f"❌ Kon real-time metrics niet laden: {str(e)}")

        # Auto-refresh logic
        if auto_refresh:
            import time

            time.sleep(refresh_interval)
            st.rerun()

    def _render_metrics_dashboard(self):
        """Render historical metrics dashboard."""
        st.markdown("#### 📊 Historical Metrics")

        # Time range selector
        col1, col2, col3 = st.columns(3)

        with col1:
            time_range = st.selectbox(
                "Tijdsperiode",
                ["Laatste uur", "Laatste 6 uur", "Laatste 24 uur", "Aangepast"],
                key="metrics_time_range",
            )

        with col2:
            if time_range == "Aangepast":
                st.datetime_input(
                    "Start tijd",
                    value=datetime.now() - timedelta(hours=1),
                    key="metrics_start_time",
                )

        with col3:
            if time_range == "Aangepast":
                st.datetime_input(
                    "End tijd", value=datetime.now(), key="metrics_end_time"
                )

        # Generate sample metrics data for visualization
        # In production, this would come from the metrics collector
        try:
            # Create sample time series data
            now = datetime.now()
            if time_range == "Laatste uur":
                time_points = [now - timedelta(minutes=5 * i) for i in range(12, 0, -1)]
            elif time_range == "Laatste 6 uur":
                time_points = [
                    now - timedelta(minutes=30 * i) for i in range(12, 0, -1)
                ]
            else:
                time_points = [now - timedelta(hours=2 * i) for i in range(12, 0, -1)]

            # Create sample data
            import random

            random.seed(42)  # For consistent demo data

            sample_data = []
            for t in time_points:
                sample_data.append(
                    {
                        "timestamp": t,
                        "response_time": random.uniform(1.0, 5.0),
                        "success_rate": random.uniform(0.85, 1.0),
                        "cache_hit_rate": random.uniform(0.2, 0.8),
                        "throughput": random.uniform(10, 50),
                        "cost_per_hour": random.uniform(0.1, 1.0),
                    }
                )

            df_metrics = pd.DataFrame(sample_data)

            # Response time chart
            st.markdown("##### ⏱️ Response Time Trend")
            fig_response = px.line(
                df_metrics,
                x="timestamp",
                y="response_time",
                title="API Response Time Over Time",
            )
            fig_response.update_layout(
                xaxis_title="Time", yaxis_title="Response Time (seconds)"
            )
            st.plotly_chart(fig_response, use_container_width=True)

            # Multi-metric chart
            st.markdown("##### 📈 Multi-Metric Overview")

            col1, col2 = st.columns(2)

            with col1:
                # Success rate and cache hit rate
                fig_rates = go.Figure()
                fig_rates.add_trace(
                    go.Scatter(
                        x=df_metrics["timestamp"],
                        y=df_metrics["success_rate"] * 100,
                        mode="lines+markers",
                        name="Success Rate (%)",
                        line=dict(color="green"),
                    )
                )
                fig_rates.add_trace(
                    go.Scatter(
                        x=df_metrics["timestamp"],
                        y=df_metrics["cache_hit_rate"] * 100,
                        mode="lines+markers",
                        name="Cache Hit Rate (%)",
                        line=dict(color="blue"),
                    )
                )
                fig_rates.update_layout(
                    title="Success & Cache Rates",
                    xaxis_title="Time",
                    yaxis_title="Percentage (%)",
                )
                st.plotly_chart(fig_rates, use_container_width=True)

            with col2:
                # Throughput and cost
                fig_perf = go.Figure()
                fig_perf.add_trace(
                    go.Scatter(
                        x=df_metrics["timestamp"],
                        y=df_metrics["throughput"],
                        mode="lines+markers",
                        name="Throughput (req/min)",
                        yaxis="y",
                    )
                )

                # Add secondary y-axis for cost
                fig_perf.add_trace(
                    go.Scatter(
                        x=df_metrics["timestamp"],
                        y=df_metrics["cost_per_hour"],
                        mode="lines+markers",
                        name="Cost ($/hour)",
                        yaxis="y2",
                        line=dict(color="red"),
                    )
                )

                fig_perf.update_layout(
                    title="Throughput & Cost",
                    xaxis_title="Time",
                    yaxis=dict(title="Throughput (req/min)", side="left"),
                    yaxis2=dict(title="Cost ($/hour)", side="right", overlaying="y"),
                )
                st.plotly_chart(fig_perf, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Kon metrics dashboard niet laden: {str(e)}")

    def _render_cost_dashboard(self):
        """Render cost analysis dashboard."""
        st.markdown("#### 💰 Cost Analysis & Optimization")

        try:
            # Generate cost optimization report
            if st.button("📊 Generate Cost Report", type="primary"):
                with st.spinner("Genereer cost optimization rapport..."):
                    report = self.collector.generate_cost_optimization_report()

                    if "error" in report:
                        st.warning(f"⚠️ {report['error']}")
                    else:
                        # Store report
                        SessionStateManager.set_value(
                            "cost_report",
                            {"data": report, "timestamp": datetime.now().isoformat()},
                        )

            # Display cost report
            cost_report_data = SessionStateManager.get_value("cost_report")
            if cost_report_data:
                report = cost_report_data["data"]

                # Cost overview metrics
                st.markdown("##### 💵 Cost Overview")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "💰 Total Cost (24h)", f"${report.get('total_cost', 0):.4f}"
                    )

                with col2:
                    st.metric(
                        "📅 Est. Monthly Cost",
                        f"${report.get('estimated_monthly_cost', 0):.2f}",
                    )

                with col3:
                    st.metric("📞 Total Calls", report.get("total_calls", 0))

                with col4:
                    avg_cost_per_call = report.get("total_cost", 0) / max(
                        report.get("total_calls", 1), 1
                    )
                    st.metric("💸 Avg Cost/Call", f"${avg_cost_per_call:.6f}")

                # Cost breakdown
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("##### 📊 Performance Metrics")

                    cache_hit_rate = report.get("cache_hit_rate", 0) * 100
                    st.metric("💾 Cache Hit Rate", f"{cache_hit_rate:.1f}%")

                    error_rate = report.get("error_rate", 0) * 100
                    st.metric("❌ Error Rate", f"{error_rate:.1f}%")

                    avg_tokens = report.get("avg_tokens_per_call", 0)
                    st.metric("🔤 Avg Tokens/Call", f"{avg_tokens:.0f}")

                with col2:
                    st.markdown("##### 💸 Cost Breakdown")

                    wasted_cost = report.get("wasted_cost", 0)
                    st.metric("🗑️ Wasted Cost", f"${wasted_cost:.4f}")

                    if wasted_cost > 0:
                        waste_percentage = (
                            wasted_cost / report.get("total_cost", 1)
                        ) * 100
                        st.metric("📈 Waste Percentage", f"{waste_percentage:.1f}%")

                # Recommendations
                recommendations = report.get("recommendations", [])
                if recommendations:
                    st.markdown("##### 💡 Cost Optimization Recommendations")

                    for i, rec in enumerate(recommendations):
                        priority_color = {
                            "high": "🔴",
                            "medium": "🟡",
                            "low": "🟢",
                        }.get(rec.get("priority", "low"), "⚪")

                        with st.expander(
                            f"{priority_color} {rec.get('type', 'Unknown').title()} - {rec.get('priority', 'low').title()} Priority",
                            expanded=i == 0,
                        ):
                            st.write(rec.get("description", "No description available"))
                            if "potential_savings" in rec:
                                st.success(
                                    f"💰 Potential savings: {rec['potential_savings']}"
                                )

                # Cost projection
                st.markdown("##### 📈 Cost Projection")

                # Create projection chart
                daily_cost = report.get("total_cost", 0)
                projection_days = list(range(1, 31))
                projected_costs = [daily_cost * day for day in projection_days]

                fig_projection = go.Figure()
                fig_projection.add_trace(
                    go.Scatter(
                        x=projection_days,
                        y=projected_costs,
                        mode="lines+markers",
                        name="Projected Cost",
                        line=dict(color="red"),
                    )
                )

                fig_projection.update_layout(
                    title="30-Day Cost Projection (Based on 24h Usage)",
                    xaxis_title="Days",
                    yaxis_title="Cumulative Cost ($)",
                )
                st.plotly_chart(fig_projection, use_container_width=True)

            # Cost calculator
            st.markdown("##### 🧮 Cost Calculator")

            col1, col2 = st.columns(2)

            with col1:
                daily_requests = st.number_input(
                    "Daily Requests",
                    min_value=1,
                    max_value=10000,
                    value=100,
                    key="calc_daily_requests",
                )

                avg_tokens = st.number_input(
                    "Average Tokens per Request",
                    min_value=10,
                    max_value=5000,
                    value=500,
                    key="calc_avg_tokens",
                )

            with col2:
                if st.button("💰 Calculate Monthly Cost"):
                    monthly_cost = self.CostCalculator.estimate_monthly_cost(
                        daily_requests, avg_tokens
                    )
                    st.success(f"📊 Estimated Monthly Cost: ${monthly_cost:.2f}")

                    # Show breakdown
                    st.info(f"📈 Daily cost: ${monthly_cost/30:.3f}")
                    st.info(
                        f"📉 Cost per request: ${monthly_cost/(daily_requests*30):.6f}"
                    )

        except Exception as e:
            st.error(f"❌ Kon cost dashboard niet laden: {str(e)}")

    def _render_alerts_dashboard(self):
        """Render alerts configuration and history."""
        st.markdown("#### ⚠️ Alerts & Notifications")

        try:
            # Alert configuration
            st.markdown("##### ⚙️ Alert Configuration")

            # Get current alerts
            alerts = self.collector.alerts

            for i, alert in enumerate(alerts):
                with st.expander(f"⚠️ {alert.name}", expanded=False):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Type:** {alert.metric_type.value}")
                        st.write(f"**Threshold:** {alert.threshold_value}")
                        st.write(f"**Comparison:** {alert.comparison}")

                    with col2:
                        st.write(f"**Severity:** {alert.severity.value}")
                        st.write(f"**Window:** {alert.window_minutes} min")
                        st.write(f"**Cooldown:** {alert.cooldown_minutes} min")

                    with col3:
                        enabled = st.checkbox(
                            "Enabled", value=alert.enabled, key=f"alert_enabled_{i}"
                        )

                        if enabled != alert.enabled:
                            alert.enabled = enabled
                            st.success("✅ Alert updated")

                        st.write(f"**Triggered:** {alert.trigger_count} times")
                        if alert.last_triggered:
                            st.write(
                                f"**Last:** {alert.last_triggered.strftime('%H:%M:%S')}"
                            )

            # Add new alert
            st.markdown("##### ➕ Add New Alert")

            col1, col2, col3 = st.columns(3)

            with col1:
                new_alert_name = st.text_input("Alert Name", key="new_alert_name")
                new_metric_type = st.selectbox(
                    "Metric Type",
                    [m.value for m in self.MetricType],
                    key="new_metric_type",
                )
                st.number_input("Threshold Value", value=1.0, key="new_threshold")

            with col2:
                st.selectbox("Comparison", ["gt", "lt", "eq"], key="new_comparison")
                st.selectbox(
                    "Severity",
                    [s.value for s in self.AlertSeverity],
                    key="new_severity",
                )
                st.number_input(
                    "Window (minutes)",
                    min_value=1,
                    max_value=120,
                    value=5,
                    key="new_window",
                )

            with col3:
                if st.button("➕ Add Alert"):
                    if new_alert_name and new_metric_type:
                        # Create new alert (simplified implementation)
                        st.success(f"✅ Alert '{new_alert_name}' would be added")
                        st.info("💡 Alert creation feature coming soon")
                    else:
                        st.error("❌ Please fill in alert name and metric type")

            # Alert history
            st.markdown("##### 📜 Recent Alert History")

            # Create sample alert history
            sample_alerts = [
                {
                    "timestamp": datetime.now() - timedelta(minutes=30),
                    "alert": "High Error Rate",
                    "severity": "error",
                    "value": "15.2%",
                    "threshold": "10%",
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=2),
                    "alert": "Slow Response Time",
                    "severity": "warning",
                    "value": "12.5s",
                    "threshold": "10.0s",
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=4),
                    "alert": "Low Cache Hit Rate",
                    "severity": "info",
                    "value": "25%",
                    "threshold": "30%",
                },
            ]

            for alert_entry in sample_alerts:
                severity_color = {
                    "info": "🔵",
                    "warning": "🟡",
                    "error": "🟠",
                    "critical": "🔴",
                }.get(alert_entry["severity"], "⚪")

                st.warning(
                    f"{severity_color} **{alert_entry['alert']}** "
                    f"({alert_entry['timestamp'].strftime('%H:%M:%S')}) - "
                    f"Value: {alert_entry['value']} | Threshold: {alert_entry['threshold']}"
                )

        except Exception as e:
            st.error(f"❌ Kon alerts dashboard niet laden: {str(e)}")

    def simulate_api_call(self):
        """Simulate an API call for testing purposes."""
        try:
            import random

            # Simulate API call
            asyncio.run(
                self.record_api_call(
                    endpoint="simulation",
                    function_name="test_function",
                    duration=random.uniform(0.5, 3.0),
                    success=random.choice([True, True, True, False]),
                    tokens_used=random.randint(100, 800),
                    cache_hit=random.choice([True, False]),
                )
            )

            return True
        except Exception:
            return False
