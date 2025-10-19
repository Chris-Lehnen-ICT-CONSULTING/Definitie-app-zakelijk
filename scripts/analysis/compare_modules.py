#!/usr/bin/env python3
"""
Vergelijkingstool voor verschillende versies van prompt modules.

Vergelijkt de output van de huidige module implementatie met
verbeterde versies om impact te meten.
"""

import difflib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.definition_generator_context import EnrichedContext
from src.services.prompts.modular_prompt_builder import ModularPromptBuilder


class ModuleComparator:
    """Vergelijkt verschillende module implementaties."""

    def __init__(self):
        """Initialize comparator."""
        self.current_builder = ModularPromptBuilder()
        self.comparisons = []

    def compare_outputs(
        self,
        begrip: str,
        context: EnrichedContext,
        current_output: str,
        improved_output: str,
    ) -> dict[str, Any]:
        """Vergelijk twee module outputs."""

        # Basic metrics
        comparison = {
            "begrip": begrip,
            "timestamp": datetime.now().isoformat(),
            "current": {
                "length": len(current_output),
                "lines": len(current_output.split("\n")),
                "sections": self._count_sections(current_output),
            },
            "improved": {
                "length": len(improved_output),
                "lines": len(improved_output.split("\n")),
                "sections": self._count_sections(improved_output),
            },
            "diff": {
                "length_change": len(improved_output) - len(current_output),
                "length_change_percent": (
                    (
                        (len(improved_output) - len(current_output))
                        / len(current_output)
                        * 100
                    )
                    if current_output
                    else 0
                ),
                "similarity_ratio": self._calculate_similarity(
                    current_output, improved_output
                ),
                "added_lines": [],
                "removed_lines": [],
                "modified_sections": [],
            },
        }

        # Detailed diff analysis
        diff = list(
            difflib.unified_diff(
                current_output.split("\n"),
                improved_output.split("\n"),
                lineterm="",
                n=3,
            )
        )

        for line in diff:
            if line.startswith("+") and not line.startswith("+++"):
                comparison["diff"]["added_lines"].append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                comparison["diff"]["removed_lines"].append(line[1:])

        # Quality improvements
        comparison["improvements"] = self._identify_improvements(
            current_output, improved_output
        )

        return comparison

    def _count_sections(self, text: str) -> int:
        """Tel het aantal hoofdsecties in de tekst."""
        markers = ["###", "**", "📌", "⚠️", "BELANGRIJK:"]
        count = 0
        for marker in markers:
            count += text.count(marker)
        return count

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Bereken similarity ratio tussen twee teksten."""
        return difflib.SequenceMatcher(None, text1, text2).ratio()

    def _identify_improvements(self, current: str, improved: str) -> list[str]:
        """Identificeer specifieke verbeteringen."""
        improvements = []

        # Check voor structurele verbeteringen
        if improved.count("\n\n") > current.count("\n\n"):
            improvements.append("Betere paragraaf scheiding")

        if "- " in improved and improved.count("- ") > current.count("- "):
            improvements.append("Meer gebruik van bullet points")

        if improved.count("**") > current.count("**"):
            improvements.append("Verbeterde emphasis/formatting")

        # Check voor inhoudelijke verbeteringen
        important_keywords = ["moet", "belangrijk", "let op", "vereist", "verplicht"]
        for keyword in important_keywords:
            if (
                keyword.lower() in improved.lower()
                and keyword.lower() not in current.lower()
            ):
                improvements.append(f"Toegevoegd: {keyword} instructie")

        # Check voor duidelijkere instructies
        if (
            "bijvoorbeeld:" in improved.lower()
            and "bijvoorbeeld:" not in current.lower()
        ):
            improvements.append("Voorbeelden toegevoegd")

        return improvements

    def generate_comparison_report(
        self, output_dir: Path = Path("comparison_reports")
    ) -> None:
        """Genereer een vergelijkingsrapport."""
        output_dir.mkdir(exist_ok=True)

        report = {
            "report_date": datetime.now().isoformat(),
            "total_comparisons": len(self.comparisons),
            "summary": {
                "average_length_change": (
                    sum(c["diff"]["length_change"] for c in self.comparisons)
                    / len(self.comparisons)
                    if self.comparisons
                    else 0
                ),
                "average_similarity": (
                    sum(c["diff"]["similarity_ratio"] for c in self.comparisons)
                    / len(self.comparisons)
                    if self.comparisons
                    else 0
                ),
                "common_improvements": self._find_common_improvements(),
            },
            "detailed_comparisons": self.comparisons,
        }

        # Save JSON report
        report_file = (
            output_dir
            / f"module_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # Generate HTML report
        html_report = self._generate_html_report(report)
        html_file = (
            output_dir
            / f"module_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_report)

        print(f"Reports saved to: {report_file} and {html_file}")

    def _find_common_improvements(self) -> list[str]:
        """Vind verbeteringen die in meerdere vergelijkingen voorkomen."""
        all_improvements = []
        for comp in self.comparisons:
            all_improvements.extend(comp.get("improvements", []))

        # Count occurrences
        improvement_counts = {}
        for imp in all_improvements:
            improvement_counts[imp] = improvement_counts.get(imp, 0) + 1

        # Return most common
        common = [imp for imp, count in improvement_counts.items() if count >= 2]
        return sorted(common, key=lambda x: improvement_counts[x], reverse=True)

    def _generate_html_report(self, report: dict[str, Any]) -> str:
        """Genereer een HTML vergelijkingsrapport."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Module Comparison Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .comparison {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .metrics {{ display: flex; justify-content: space-around; }}
        .metric {{ text-align: center; padding: 10px; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
        .neutral {{ color: #666; }}
        .diff-view {{ background: #f5f5f5; padding: 10px; font-family: monospace; font-size: 12px; }}
        .added {{ background-color: #e6ffed; }}
        .removed {{ background-color: #ffebe9; }}
        h1, h2, h3 {{ color: #333; }}
    </style>
</head>
<body>
    <h1>Module Comparison Report</h1>
    <p>Generated: {report['report_date']}</p>

    <div class="summary">
        <h2>Summary</h2>
        <div class="metrics">
            <div class="metric">
                <h3>Total Comparisons</h3>
                <p>{report['total_comparisons']}</p>
            </div>
            <div class="metric">
                <h3>Avg Length Change</h3>
                <p class="{'positive' if report['summary']['average_length_change'] < 0 else 'negative'}">
                    {report['summary']['average_length_change']:+.0f} chars
                </p>
            </div>
            <div class="metric">
                <h3>Avg Similarity</h3>
                <p class="neutral">{report['summary']['average_similarity']:.1%}</p>
            </div>
        </div>

        <h3>Common Improvements</h3>
        <ul>
            {''.join(f'<li>{imp}</li>' for imp in report['summary']['common_improvements'])}
        </ul>
    </div>

    <h2>Detailed Comparisons</h2>
"""

        for comp in report["detailed_comparisons"]:
            change_class = (
                "positive" if comp["diff"]["length_change"] < 0 else "negative"
            )
            html += f"""
    <div class="comparison">
        <h3>Begrip: {comp['begrip']}</h3>
        <div class="metrics">
            <div class="metric">
                <strong>Length Change:</strong>
                <span class="{change_class}">{comp['diff']['length_change']:+d} chars ({comp['diff']['length_change_percent']:+.1f}%)</span>
            </div>
            <div class="metric">
                <strong>Similarity:</strong> {comp['diff']['similarity_ratio']:.1%}
            </div>
            <div class="metric">
                <strong>Sections:</strong> {comp['current']['sections']} → {comp['improved']['sections']}
            </div>
        </div>

        <h4>Improvements</h4>
        <ul>
            {''.join(f'<li>{imp}</li>' for imp in comp.get('improvements', []))}
        </ul>

        <h4>Changes</h4>
        <div class="diff-view">
            <div class="removed">Removed: {len(comp['diff']['removed_lines'])} lines</div>
            <div class="added">Added: {len(comp['diff']['added_lines'])} lines</div>
        </div>
    </div>
"""

        html += """
</body>
</html>
"""
        return html


def demonstrate_improved_module(begrip: str) -> str:
    """
    Demonstratie van een verbeterde versie van de core instructions module.

    Dit is een voorbeeld van hoe we de module kunnen verbeteren.
    """
    return f"""Je bent een ervaren Nederlandse expert in het opstellen van beleidsmatige en juridische definities voor de Nederlandse overheid.

**Je opdracht**: Formuleer een heldere, eenduidige definitie voor het begrip '{begrip}'.

### Definitie vereisten:
• **Formaat**: Één volledige zin die het begrip volledig verklaart
• **Stijl**: Zakelijk, formeel en geschikt voor officiële overheidsdocumenten
• **Structuur**: Begin met "{begrip} is..." of "{begrip} betreft..."
• **Taal**: Helder Nederlands zonder jargon (tenzij onvermijdelijk)

### Kwaliteitscriteria:
✓ Ondubbelzinnig - geen ruimte voor meerdere interpretaties
✓ Volledig - bevat alle essentiële kenmerken
✓ Afgebakend - maakt duidelijk wat WEL en NIET onder de definitie valt
✓ Contextgevoelig - past bij de Nederlandse overheidscontext

⚠️ **LET OP**:
- Geen toelichtingen, voorbeelden of extra uitleg toevoegen
- Alleen de definitie zelf in één zin
- Vermijd cirkelredeneringen (gebruik het begrip niet in de eigen definitie)

BELANGRIJK: Focus op precisie en helderheid. De definitie moet juridisch houdbaar zijn."""


def main():
    """Hoofdfunctie voor module vergelijking."""
    comparator = ModuleComparator()

    # Test cases
    test_begrippen = ["blockchain", "opsporing", "natuurinclusief bouwen"]

    for begrip in test_begrippen:
        # Get current output (simplified for demo)
        current = (
            f"Je bent een ervaren Nederlandse expert. Definieer '{begrip}' in één zin."
        )

        # Get improved output
        improved = demonstrate_improved_module(begrip)

        # Create dummy context
        context = EnrichedContext({}, {}, [], {})

        # Compare
        comparison = comparator.compare_outputs(begrip, context, current, improved)
        comparator.comparisons.append(comparison)

    # Generate report
    comparator.generate_comparison_report()

    print("Comparison complete. Check comparison_reports directory for results.")


if __name__ == "__main__":
    main()
