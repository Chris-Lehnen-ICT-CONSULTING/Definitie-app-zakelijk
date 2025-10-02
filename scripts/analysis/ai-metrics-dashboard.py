#!/usr/bin/env python3
"""
AI Agent Metrics Dashboard for DefinitieAgent Project

Simple monitoring dashboard for AI code generation performance.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


class AIMetricsDashboard:
    """Dashboard for monitoring AI agent code generation metrics."""

    def __init__(self, metrics_file: str = "ai_metrics.json"):
        self.metrics_file = Path(metrics_file)
        self.metrics = self.load_metrics()

    def load_metrics(self) -> dict:
        """Load metrics from JSON file."""
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                return json.load(f)
        return {}

    def display_dashboard(self):
        """Display the metrics dashboard."""
        print("\n" + "=" * 60)
        print("🤖 AI Agent Performance Dashboard")
        print("=" * 60)
        print(f"Generated at: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        if not self.metrics:
            print("\n⚠️  No metrics data available yet.")
            print("Run some AI code reviews first!")
            return

        # Overall statistics
        total_reviews = sum(m["total_reviews"] for m in self.metrics.values())
        total_success = sum(m["successful_reviews"] for m in self.metrics.values())
        overall_success_rate = (
            (total_success / total_reviews * 100) if total_reviews > 0 else 0
        )

        print("\n📊 Overall Statistics")
        print(f"   Total Reviews: {total_reviews}")
        print(f"   Successful: {total_success}")
        print(f"   Success Rate: {overall_success_rate:.1f}%")

        # Per-agent statistics
        print("\n📈 Per-Agent Performance")
        print("-" * 60)

        for agent_name, metrics in sorted(self.metrics.items()):
            self._display_agent_metrics(agent_name, metrics)

        # Insights
        self._display_insights()

    def _display_agent_metrics(self, agent_name: str, metrics: dict):
        """Display metrics for a single agent."""
        if metrics["total_reviews"] == 0:
            return

        success_rate = (metrics["successful_reviews"] / metrics["total_reviews"]) * 100
        avg_iterations = metrics["total_iterations"] / metrics["total_reviews"]
        avg_fixes = metrics["auto_fixes"] / metrics["total_reviews"]

        print(f"\n🤖 {agent_name}")
        print(f"   Reviews: {metrics['total_reviews']}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Avg Iterations: {avg_iterations:.1f}")
        print(f"   Avg Auto-fixes: {avg_fixes:.1f}")

        # Performance indicator
        if success_rate >= 90:
            print("   Performance: 🟢 Excellent")
        elif success_rate >= 70:
            print("   Performance: 🟡 Good")
        else:
            print("   Performance: 🔴 Needs Improvement")

    def _display_insights(self):
        """Display insights and recommendations."""
        print("\n💡 Insights & Recommendations")
        print("-" * 60)

        best_agent = None
        best_success_rate = 0

        for agent_name, metrics in self.metrics.items():
            if metrics["total_reviews"] >= 5:  # Minimum reviews for comparison
                success_rate = (
                    metrics["successful_reviews"] / metrics["total_reviews"]
                ) * 100
                if success_rate > best_success_rate:
                    best_success_rate = success_rate
                    best_agent = agent_name

        if best_agent:
            print(
                f"✨ Best Performer: {best_agent} ({best_success_rate:.1f}% success rate)"
            )

        # General recommendations
        total_reviews = sum(m["total_reviews"] for m in self.metrics.values())
        if total_reviews < 10:
            print("📌 Recommendation: More data needed for meaningful insights")
        else:
            avg_iterations = (
                sum(m["total_iterations"] for m in self.metrics.values())
                / total_reviews
            )
            if avg_iterations > 3:
                print("⚠️  High average iterations - consider improving AI prompts")

    def export_report(self, output_file: str):
        """Export metrics to a markdown report."""
        with open(output_file, "w") as f:
            f.write("# AI Agent Code Review Metrics Report\n\n")
            f.write(f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            if not self.metrics:
                f.write("No metrics data available.\n")
                return

            f.write("## Summary\n\n")
            f.write(
                "| Agent | Reviews | Success Rate | Avg Iterations | Avg Auto-fixes |\n"
            )
            f.write(
                "|-------|---------|--------------|----------------|----------------|\n"
            )

            for agent_name, metrics in sorted(self.metrics.items()):
                if metrics["total_reviews"] > 0:
                    success_rate = (
                        metrics["successful_reviews"] / metrics["total_reviews"]
                    ) * 100
                    avg_iterations = (
                        metrics["total_iterations"] / metrics["total_reviews"]
                    )
                    avg_fixes = metrics["auto_fixes"] / metrics["total_reviews"]

                    f.write(
                        f"| {agent_name} | {metrics['total_reviews']} | "
                        f"{success_rate:.1f}% | {avg_iterations:.1f} | "
                        f"{avg_fixes:.1f} |\n"
                    )

        print(f"\n📄 Report exported to: {output_file}")

    def reset_metrics(self, agent_name: str | None = None):
        """Reset metrics for specific agent or all agents."""
        if agent_name:
            if agent_name in self.metrics:
                del self.metrics[agent_name]
                print(f"✅ Reset metrics for {agent_name}")
            else:
                print(f"⚠️  No metrics found for {agent_name}")
        else:
            self.metrics = {}
            print("✅ Reset all metrics")

        with open(self.metrics_file, "w") as f:
            json.dump(self.metrics, f, indent=2)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Agent Metrics Dashboard")
    parser.add_argument("--export", help="Export report to file")
    parser.add_argument("--reset", help="Reset metrics (agent name or 'all')")

    args = parser.parse_args()

    dashboard = AIMetricsDashboard()

    if args.reset:
        if args.reset == "all":
            dashboard.reset_metrics()
        else:
            dashboard.reset_metrics(args.reset)
    elif args.export:
        dashboard.export_report(args.export)
    else:
        dashboard.display_dashboard()


if __name__ == "__main__":
    main()
