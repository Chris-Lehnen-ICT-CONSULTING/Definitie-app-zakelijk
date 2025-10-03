#!/usr/bin/env python3
"""
Compare validation results between OLD and NEW systems.

This CLI tool loads validation results from both systems and generates
comprehensive comparison reports in multiple formats (HTML, JSON, console, CSV).

Usage:
    python scripts/compare_validation_results.py --old results_old.json --new results_new.json
    python scripts/compare_validation_results.py --baseline baseline_42_definitions.json --format html
    python scripts/compare_validation_results.py --help

EPIC-026 Phase 1 - Rebuild Validation
"""

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@dataclass
class ValidationResult:
    """Validation result for a single definition."""

    begrip: str
    overall_score: float
    is_acceptable: bool
    rule_results: list[dict[str, Any]]
    system: str  # "OLD" or "NEW"


@dataclass
class ComparisonResult:
    """Comparison result between OLD and NEW systems."""

    begrip: str
    old_score: float
    new_score: float
    score_diff: float
    old_acceptable: bool
    new_acceptable: bool
    acceptability_match: bool
    rule_count_old: int
    rule_count_new: int
    severity: str  # "none", "low", "medium", "high", "critical"


class ValidationComparer:
    """Compare validation results between systems."""

    SEVERITY_THRESHOLDS = {
        "critical": 0.20,  # >20% score difference
        "high": 0.10,  # 10-20% score difference
        "medium": 0.05,  # 5-10% score difference
        "low": 0.01,  # 1-5% score difference
        "none": 0.0,  # <1% score difference
    }

    def __init__(self):
        """Initialize comparer."""
        self.comparisons: list[ComparisonResult] = []

    def load_old_results(self, filepath: Path) -> list[ValidationResult]:
        """Load OLD system validation results."""
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        results = []
        definitions = data.get("definitions", [])

        for defn in definitions:
            score = defn.get("validation_score") or 0.0
            results.append(
                ValidationResult(
                    begrip=defn.get("begrip", "unknown"),
                    overall_score=score,
                    is_acceptable=score >= 0.6 if score is not None else False,
                    rule_results=defn.get("validation_issues", []) or [],
                    system="OLD",
                )
            )

        return results

    def load_new_results(self, filepath: Path) -> list[ValidationResult]:
        """Load NEW system validation results."""
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        results = []
        definitions = data.get("definitions", [])

        for defn in definitions:
            results.append(
                ValidationResult(
                    begrip=defn.get("begrip", "unknown"),
                    overall_score=defn.get("validation_score", 0.0) or 0.0,
                    is_acceptable=defn.get("is_acceptable", False),
                    rule_results=defn.get("rule_results", []) or [],
                    system="NEW",
                )
            )

        return results

    def compare(
        self, old_results: list[ValidationResult], new_results: list[ValidationResult]
    ) -> None:
        """
        Compare OLD and NEW validation results.

        Args:
            old_results: Results from OLD system
            new_results: Results from NEW system
        """
        # Create lookup dictionaries
        old_dict = {r.begrip: r for r in old_results}
        new_dict = {r.begrip: r for r in new_results}

        # Find all begrippen
        all_begrippen = set(old_dict.keys()) | set(new_dict.keys())

        # Compare each begrip
        for begrip in sorted(all_begrippen):
            old_result = old_dict.get(begrip)
            new_result = new_dict.get(begrip)

            if old_result and new_result:
                comparison = self._compare_single(old_result, new_result)
                self.comparisons.append(comparison)
            else:
                # Missing in one system
                print(
                    f"Warning: '{begrip}' missing in {'NEW' if old_result else 'OLD'} system"
                )

    def _compare_single(
        self, old: ValidationResult, new: ValidationResult
    ) -> ComparisonResult:
        """Compare a single definition's results."""
        score_diff = abs(old.overall_score - new.overall_score)
        severity = self._determine_severity(score_diff)

        return ComparisonResult(
            begrip=old.begrip,
            old_score=old.overall_score,
            new_score=new.overall_score,
            score_diff=score_diff,
            old_acceptable=old.is_acceptable,
            new_acceptable=new.is_acceptable,
            acceptability_match=old.is_acceptable == new.is_acceptable,
            rule_count_old=len(old.rule_results),
            rule_count_new=len(new.rule_results),
            severity=severity,
        )

    def _determine_severity(self, score_diff: float) -> str:
        """Determine severity based on score difference."""
        if score_diff >= self.SEVERITY_THRESHOLDS["critical"]:
            return "critical"
        elif score_diff >= self.SEVERITY_THRESHOLDS["high"]:
            return "high"
        elif score_diff >= self.SEVERITY_THRESHOLDS["medium"]:
            return "medium"
        elif score_diff >= self.SEVERITY_THRESHOLDS["low"]:
            return "low"
        else:
            return "none"

    def generate_console_report(self) -> str:
        """Generate console-friendly text report."""
        lines = []
        lines.append("\n" + "=" * 100)
        lines.append("VALIDATION COMPARISON REPORT")
        lines.append("=" * 100)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append(f"Total Comparisons: {len(self.comparisons)}")

        # Summary statistics
        matches = sum(1 for c in self.comparisons if c.score_diff <= 0.01)
        acceptability_matches = sum(
            1 for c in self.comparisons if c.acceptability_match
        )

        lines.append("\n" + "-" * 100)
        lines.append("SUMMARY STATISTICS")
        lines.append("-" * 100)
        lines.append(
            f"Score Matches (±1%):           {matches} ({matches/len(self.comparisons)*100:.1f}%)"
        )
        lines.append(
            f"Acceptability Matches:         {acceptability_matches} ({acceptability_matches/len(self.comparisons)*100:.1f}%)"
        )

        # Severity breakdown
        severity_counts = {}
        for c in self.comparisons:
            severity_counts[c.severity] = severity_counts.get(c.severity, 0) + 1

        lines.append("\nSeverity Breakdown:")
        for severity in ["critical", "high", "medium", "low", "none"]:
            count = severity_counts.get(severity, 0)
            pct = count / len(self.comparisons) * 100
            lines.append(f"  {severity.upper():12} {count:4d} ({pct:5.1f}%)")

        # Top mismatches
        mismatches = [c for c in self.comparisons if c.severity != "none"]
        if mismatches:
            lines.append("\n" + "-" * 100)
            lines.append("TOP 10 MISMATCHES")
            lines.append("-" * 100)
            lines.append(
                f"{'Begrip':<30} {'OLD Score':>10} {'NEW Score':>10} {'Diff':>10} {'Severity':<10}"
            )
            lines.append("-" * 100)

            for comparison in sorted(
                mismatches, key=lambda x: x.score_diff, reverse=True
            )[:10]:
                lines.append(
                    f"{comparison.begrip:<30} "
                    f"{comparison.old_score:>10.4f} "
                    f"{comparison.new_score:>10.4f} "
                    f"{comparison.score_diff:>10.4f} "
                    f"{comparison.severity:<10}"
                )

        lines.append("\n" + "=" * 100)

        return "\n".join(lines)

    def generate_html_report(self, output_path: Path) -> None:
        """Generate HTML report with styling."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("<meta charset='utf-8'>")
        html.append("<title>Validation Comparison Report</title>")
        html.append("<style>")
        html.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        html.append("h1 { color: #333; }")
        html.append(
            "table { border-collapse: collapse; width: 100%; margin-top: 20px; }"
        )
        html.append(
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }"
        )
        html.append("th { background-color: #4CAF50; color: white; }")
        html.append("tr:nth-child(even) { background-color: #f2f2f2; }")
        html.append(".critical { background-color: #ffcccc; }")
        html.append(".high { background-color: #ffddaa; }")
        html.append(".medium { background-color: #ffffcc; }")
        html.append(".low { background-color: #e6ffe6; }")
        html.append(
            ".summary { margin: 20px 0; padding: 15px; background-color: #f0f0f0; border-left: 4px solid #4CAF50; }"
        )
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")

        # Title and timestamp
        html.append("<h1>Validation Comparison Report</h1>")
        html.append(f"<p><strong>Generated:</strong> {datetime.now().isoformat()}</p>")
        html.append(
            f"<p><strong>Total Comparisons:</strong> {len(self.comparisons)}</p>"
        )

        # Summary
        matches = sum(1 for c in self.comparisons if c.score_diff <= 0.01)
        acceptability_matches = sum(
            1 for c in self.comparisons if c.acceptability_match
        )

        html.append("<div class='summary'>")
        html.append("<h2>Summary Statistics</h2>")
        html.append(
            f"<p><strong>Score Matches (±1%):</strong> {matches} ({matches/len(self.comparisons)*100:.1f}%)</p>"
        )
        html.append(
            f"<p><strong>Acceptability Matches:</strong> {acceptability_matches} ({acceptability_matches/len(self.comparisons)*100:.1f}%)</p>"
        )
        html.append("</div>")

        # Detailed table
        html.append("<h2>Detailed Comparison</h2>")
        html.append("<table>")
        html.append("<tr>")
        html.append("<th>Begrip</th>")
        html.append("<th>OLD Score</th>")
        html.append("<th>NEW Score</th>")
        html.append("<th>Difference</th>")
        html.append("<th>OLD Accept</th>")
        html.append("<th>NEW Accept</th>")
        html.append("<th>Severity</th>")
        html.append("</tr>")

        for comp in sorted(self.comparisons, key=lambda x: x.score_diff, reverse=True):
            row_class = comp.severity if comp.severity != "none" else ""
            html.append(f"<tr class='{row_class}'>")
            html.append(f"<td>{comp.begrip}</td>")
            html.append(f"<td>{comp.old_score:.4f}</td>")
            html.append(f"<td>{comp.new_score:.4f}</td>")
            html.append(f"<td>{comp.score_diff:.4f}</td>")
            html.append(f"<td>{'✓' if comp.old_acceptable else '✗'}</td>")
            html.append(f"<td>{'✓' if comp.new_acceptable else '✗'}</td>")
            html.append(f"<td>{comp.severity.upper()}</td>")
            html.append("</tr>")

        html.append("</table>")
        html.append("</body>")
        html.append("</html>")

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html))

        print(f"✓ HTML report saved to: {output_path}")

    def generate_json_report(self, output_path: Path) -> None:
        """Generate JSON report for programmatic analysis."""
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_comparisons": len(self.comparisons),
            },
            "summary": {
                "score_matches": sum(
                    1 for c in self.comparisons if c.score_diff <= 0.01
                ),
                "acceptability_matches": sum(
                    1 for c in self.comparisons if c.acceptability_match
                ),
                "severity_breakdown": {},
            },
            "comparisons": [],
        }

        # Severity breakdown
        for severity in ["critical", "high", "medium", "low", "none"]:
            count = sum(1 for c in self.comparisons if c.severity == severity)
            report["summary"]["severity_breakdown"][severity] = count

        # Comparisons
        for comp in self.comparisons:
            report["comparisons"].append(
                {
                    "begrip": comp.begrip,
                    "old_score": comp.old_score,
                    "new_score": comp.new_score,
                    "score_diff": comp.score_diff,
                    "old_acceptable": comp.old_acceptable,
                    "new_acceptable": comp.new_acceptable,
                    "acceptability_match": comp.acceptability_match,
                    "severity": comp.severity,
                }
            )

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"✓ JSON report saved to: {output_path}")

    def generate_csv_report(self, output_path: Path) -> None:
        """Generate CSV report for spreadsheet analysis."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(
                [
                    "Begrip",
                    "OLD Score",
                    "NEW Score",
                    "Difference",
                    "OLD Acceptable",
                    "NEW Acceptable",
                    "Acceptability Match",
                    "Severity",
                ]
            )

            # Data rows
            for comp in sorted(
                self.comparisons, key=lambda x: x.score_diff, reverse=True
            ):
                writer.writerow(
                    [
                        comp.begrip,
                        f"{comp.old_score:.4f}",
                        f"{comp.new_score:.4f}",
                        f"{comp.score_diff:.4f}",
                        "Yes" if comp.old_acceptable else "No",
                        "Yes" if comp.new_acceptable else "No",
                        "Yes" if comp.acceptability_match else "No",
                        comp.severity.upper(),
                    ]
                )

        print(f"✓ CSV report saved to: {output_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Compare validation results between OLD and NEW systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two result files
  python scripts/compare_validation_results.py --old results_old.json --new results_new.json

  # Generate HTML report from baseline
  python scripts/compare_validation_results.py --baseline baseline_42_definitions.json --format html

  # Generate all formats
  python scripts/compare_validation_results.py --old old.json --new new.json --format all
        """,
    )

    parser.add_argument("--old", type=Path, help="Path to OLD system results (JSON)")
    parser.add_argument("--new", type=Path, help="Path to NEW system results (JSON)")
    parser.add_argument(
        "--baseline",
        type=Path,
        help="Path to baseline definitions (includes OLD results)",
    )
    parser.add_argument(
        "--format",
        choices=["console", "html", "json", "csv", "all"],
        default="console",
        help="Output format (default: console)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for reports (default: current directory)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.baseline and (not args.old or not args.new):
        parser.error("Either --baseline or both --old and --new must be provided")

    # Initialize comparer
    comparer = ValidationComparer()

    # Load results
    if args.baseline:
        print(f"Loading baseline from: {args.baseline}")
        old_results = comparer.load_old_results(args.baseline)
        # For baseline mode, NEW results are the same (for now)
        new_results = old_results
        print(f"  Loaded {len(old_results)} definitions")
    else:
        print(f"Loading OLD results from: {args.old}")
        old_results = comparer.load_old_results(args.old)
        print(f"  Loaded {len(old_results)} OLD results")

        print(f"Loading NEW results from: {args.new}")
        new_results = comparer.load_new_results(args.new)
        print(f"  Loaded {len(new_results)} NEW results")

    # Compare
    print("\nComparing results...")
    comparer.compare(old_results, new_results)
    print(f"  Completed {len(comparer.comparisons)} comparisons")

    # Generate reports
    output_dir = args.output or Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.format in ["console", "all"]:
        print(comparer.generate_console_report())

    if args.format in ["html", "all"]:
        html_path = (
            output_dir
            / f"validation_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        comparer.generate_html_report(html_path)

    if args.format in ["json", "all"]:
        json_path = (
            output_dir
            / f"validation_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        comparer.generate_json_report(json_path)

    if args.format in ["csv", "all"]:
        csv_path = (
            output_dir
            / f"validation_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        comparer.generate_csv_report(csv_path)


if __name__ == "__main__":
    main()
