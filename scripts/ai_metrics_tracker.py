#!/usr/bin/env python3
"""
AI Code Review Metrics Tracking
Houdt statistieken bij van AI code reviews voor continue verbetering
"""

import logging
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


@dataclass
class ReviewMetric:
    """Metrics voor een enkele review sessie."""

    agent_name: str
    timestamp: datetime
    passed: bool
    iterations: int
    total_issues: int
    blocking_issues: int
    auto_fixes: int
    duration_seconds: float
    files_reviewed: int

    def to_dict(self):
        """Convert naar dict voor JSON serialization."""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict):
        """Create van dict."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class AIMetricsTracker:
    """Track en analyseer AI code review performance."""

    def __init__(self, db_path: str = "ai_metrics.db"):
        self.db_path = Path(db_path)
        self.init_database()

    def init_database(self):
        """Initialiseer SQLite database voor metrics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS review_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    passed BOOLEAN NOT NULL,
                    iterations INTEGER NOT NULL,
                    total_issues INTEGER NOT NULL,
                    blocking_issues INTEGER NOT NULL,
                    auto_fixes INTEGER NOT NULL,
                    duration_seconds REAL NOT NULL,
                    files_reviewed INTEGER NOT NULL
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS issue_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    issue_type TEXT NOT NULL,
                    issue_category TEXT NOT NULL,
                    occurrences INTEGER DEFAULT 1,
                    last_seen TIMESTAMP NOT NULL
                )
            """
            )

            conn.commit()

    def record_review(self, metric: ReviewMetric, issues: list[dict] = None):
        """Sla review metrics op in database."""
        with sqlite3.connect(self.db_path) as conn:
            # Insert main metrics
            conn.execute(
                """
                INSERT INTO review_metrics
                (agent_name, timestamp, passed, iterations, total_issues,
                 blocking_issues, auto_fixes, duration_seconds, files_reviewed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metric.agent_name,
                    metric.timestamp,
                    metric.passed,
                    metric.iterations,
                    metric.total_issues,
                    metric.blocking_issues,
                    metric.auto_fixes,
                    metric.duration_seconds,
                    metric.files_reviewed,
                ),
            )

            # Track issue patterns
            if issues:
                for issue in issues:
                    # Check if pattern exists
                    cursor = conn.execute(
                        """
                        SELECT id, occurrences FROM issue_patterns
                        WHERE agent_name = ? AND issue_type = ? AND issue_category = ?
                    """,
                        (
                            metric.agent_name,
                            issue.get("check", "unknown"),
                            issue.get("severity", "unknown"),
                        ),
                    )

                    result = cursor.fetchone()
                    if result:
                        # Update existing pattern
                        conn.execute(
                            """
                            UPDATE issue_patterns
                            SET occurrences = ?, last_seen = ?
                            WHERE id = ?
                        """,
                            (result[1] + 1, datetime.now(), result[0]),
                        )
                    else:
                        # Insert new pattern
                        conn.execute(
                            """
                            INSERT INTO issue_patterns
                            (agent_name, issue_type, issue_category, last_seen)
                            VALUES (?, ?, ?, ?)
                        """,
                            (
                                metric.agent_name,
                                issue.get("check", "unknown"),
                                issue.get("severity", "unknown"),
                                datetime.now(),
                            ),
                        )

            conn.commit()

    def get_agent_stats(self, agent_name: str, days: int = 30) -> dict:
        """Haal statistieken op voor een specifieke agent."""
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            # Overall stats
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_reviews,
                    SUM(passed) as successful_reviews,
                    AVG(iterations) as avg_iterations,
                    AVG(duration_seconds) as avg_duration,
                    AVG(total_issues) as avg_issues,
                    SUM(auto_fixes) as total_auto_fixes
                FROM review_metrics
                WHERE agent_name = ? AND timestamp > ?
            """,
                (agent_name, cutoff_date),
            )

            stats = cursor.fetchone()

            # Common issues
            cursor = conn.execute(
                """
                SELECT issue_type, issue_category, SUM(occurrences) as count
                FROM issue_patterns
                WHERE agent_name = ? AND last_seen > ?
                GROUP BY issue_type, issue_category
                ORDER BY count DESC
                LIMIT 10
            """,
                (agent_name, cutoff_date),
            )

            common_issues = cursor.fetchall()

            return {
                "total_reviews": stats[0] or 0,
                "successful_reviews": stats[1] or 0,
                "success_rate": (stats[1] / stats[0] * 100) if stats[0] else 0,
                "avg_iterations": stats[2] or 0,
                "avg_duration": stats[3] or 0,
                "avg_issues": stats[4] or 0,
                "total_auto_fixes": stats[5] or 0,
                "common_issues": [
                    {"type": row[0], "category": row[1], "count": row[2]}
                    for row in common_issues
                ],
            }

    def get_trend_data(self, days: int = 30) -> pd.DataFrame:
        """Haal trend data op voor visualisatie."""
        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(
                """
                SELECT
                    DATE(timestamp) as date,
                    agent_name,
                    COUNT(*) as reviews,
                    SUM(passed) as successful,
                    AVG(iterations) as avg_iterations,
                    AVG(total_issues) as avg_issues
                FROM review_metrics
                WHERE timestamp > ?
                GROUP BY DATE(timestamp), agent_name
                ORDER BY date DESC
            """,
                conn,
                params=(cutoff_date,),
            )

        return df

    def generate_report(self, output_path: str = "ai_metrics_report.md"):
        """Genereer een markdown rapport van alle metrics."""
        report = "# 🤖 AI Code Review Metrics Report\n\n"
        report += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Get all agents
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT DISTINCT agent_name FROM review_metrics")
            agents = [row[0] for row in cursor.fetchall()]

        report += "## 📊 Overall Performance\n\n"

        for agent in agents:
            stats = self.get_agent_stats(agent)
            report += f"### {agent}\n\n"
            report += f"- **Total Reviews**: {stats['total_reviews']}\n"
            report += f"- **Success Rate**: {stats['success_rate']:.1f}%\n"
            report += f"- **Average Iterations**: {stats['avg_iterations']:.1f}\n"
            report += f"- **Average Duration**: {stats['avg_duration']:.1f}s\n"
            report += f"- **Average Issues Found**: {stats['avg_issues']:.1f}\n"
            report += f"- **Total Auto-fixes**: {stats['total_auto_fixes']}\n\n"

            if stats["common_issues"]:
                report += "**Common Issues**:\n"
                for issue in stats["common_issues"][:5]:
                    report += f"- {issue['type']} ({issue['category']}): {issue['count']} times\n"
                report += "\n"

        # Save report
        Path(output_path).write_text(report, encoding="utf-8")
        logger.info(f"Report saved to {output_path}")

        return report


def create_streamlit_dashboard():
    """Maak een Streamlit dashboard voor metrics visualisatie."""
    st.set_page_config(
        page_title="AI Code Review Metrics", page_icon="🤖", layout="wide"
    )

    st.title("🤖 AI Code Review Metrics Dashboard")

    # Initialize tracker
    tracker = AIMetricsTracker()

    # Sidebar filters
    st.sidebar.header("Filters")
    days = st.sidebar.slider("Days to show", 7, 90, 30)

    # Get trend data
    df = tracker.get_trend_data(days)

    if df.empty:
        st.warning("No review data available yet!")
        return

    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)

    total_reviews = len(df)
    success_rate = (
        (df["successful"].sum() / df["reviews"].sum() * 100)
        if df["reviews"].sum() > 0
        else 0
    )
    avg_iterations = df["avg_iterations"].mean()
    avg_issues = df["avg_issues"].mean()

    col1.metric("Total Reviews", total_reviews)
    col2.metric("Success Rate", f"{success_rate:.1f}%")
    col3.metric("Avg Iterations", f"{avg_iterations:.1f}")
    col4.metric("Avg Issues", f"{avg_issues:.1f}")

    # Charts
    st.header("📈 Trends")

    # Success rate over time
    st.subheader("Success Rate Trend")
    daily_success = df.groupby("date").agg({"successful": "sum", "reviews": "sum"})
    daily_success["success_rate"] = (
        daily_success["successful"] / daily_success["reviews"] * 100
    )
    st.line_chart(daily_success["success_rate"])

    # Issues per agent
    st.subheader("Performance by Agent")
    agent_stats = df.groupby("agent_name").agg(
        {
            "reviews": "sum",
            "successful": "sum",
            "avg_iterations": "mean",
            "avg_issues": "mean",
        }
    )
    st.dataframe(agent_stats)

    # Common issues
    st.header("🔍 Common Issues")

    # Get all agents
    agents = df["agent_name"].unique()
    selected_agent = st.selectbox("Select Agent", agents)

    if selected_agent:
        stats = tracker.get_agent_stats(selected_agent, days)
        if stats["common_issues"]:
            issues_df = pd.DataFrame(stats["common_issues"])
            st.bar_chart(issues_df.set_index("type")["count"])

    # Export options
    st.header("📤 Export")
    if st.button("Generate Report"):
        report = tracker.generate_report()
        st.text_area("Report Preview", report, height=400)
        st.download_button(
            "Download Report",
            report,
            file_name=f"ai_metrics_report_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
        )


def main():
    """CLI interface voor metrics tracking."""
    import argparse

    parser = argparse.ArgumentParser(description="AI Code Review Metrics")
    parser.add_argument(
        "command", choices=["record", "report", "dashboard"], help="Command to execute"
    )
    parser.add_argument("--agent", type=str, help="Agent name")
    parser.add_argument("--passed", action="store_true", help="Review passed")
    parser.add_argument("--iterations", type=int, help="Number of iterations")
    parser.add_argument("--issues", type=int, help="Total issues found")
    parser.add_argument("--blocking", type=int, help="Blocking issues")
    parser.add_argument("--fixes", type=int, help="Auto-fixes applied")
    parser.add_argument("--duration", type=float, help="Duration in seconds")
    parser.add_argument("--files", type=int, help="Files reviewed")

    args = parser.parse_args()

    tracker = AIMetricsTracker()

    if args.command == "record":
        # Record a new metric
        metric = ReviewMetric(
            agent_name=args.agent or "manual",
            timestamp=datetime.now(),
            passed=args.passed,
            iterations=args.iterations or 1,
            total_issues=args.issues or 0,
            blocking_issues=args.blocking or 0,
            auto_fixes=args.fixes or 0,
            duration_seconds=args.duration or 0,
            files_reviewed=args.files or 0,
        )
        tracker.record_review(metric)
        print("✅ Metric recorded successfully")

    elif args.command == "report":
        # Generate report
        report = tracker.generate_report()
        print(report)

    elif args.command == "dashboard":
        # Launch Streamlit dashboard
        print("Launching dashboard...")
        import subprocess

        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", __file__], check=False
        )


if __name__ == "__main__":
    # Check if running in Streamlit
    try:
        import streamlit as st

        create_streamlit_dashboard()
    except ImportError:
        # Not in Streamlit, run CLI
        main()
