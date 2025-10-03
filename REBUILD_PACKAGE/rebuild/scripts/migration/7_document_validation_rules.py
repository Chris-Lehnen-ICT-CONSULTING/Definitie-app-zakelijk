#!/usr/bin/env python3
"""Generate comprehensive validation rules documentation.

This script generates searchable HTML documentation for all 46 validation rules,
including examples, test cases, and configuration details.

Usage:
    python rebuild/scripts/migration/7_document_validation_rules.py
    python rebuild/scripts/migration/7_document_validation_rules.py --output docs/validation_rules.html
    python rebuild/scripts/migration/7_document_validation_rules.py --format markdown

Example:
    $ python rebuild/scripts/migration/7_document_validation_rules.py
    ✅ Documented 46 validation rules
    ✅ Generated HTML documentation: docs/validation_rules.html
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ValidationRuleDocumenter:
    """Generate documentation for validation rules."""

    def __init__(self):
        """Initialize documenter."""
        self.rules = []
        self.categories = {}

    def load_validation_rules(self):
        """Load validation rules from config and code."""
        logger.info("📂 Loading validation rules...")

        # Load from config directory
        config_dir = Path("config/toetsregels/regels")

        if not config_dir.exists():
            logger.warning(f"⚠️  Config directory not found: {config_dir}")
            # Fallback to generating from Python modules
            self.load_from_python_modules()
            return

        # Load JSON rule configs
        for json_file in config_dir.glob("**/*.json"):
            try:
                with open(json_file, encoding="utf-8") as f:
                    rule = json.load(f)
                    self.rules.append(rule)

                    # Categorize
                    category = rule.get("id", "UNKNOWN")[:3]
                    if category not in self.categories:
                        self.categories[category] = []
                    self.categories[category].append(rule)

            except Exception as e:
                logger.warning(f"⚠️  Could not load {json_file}: {e}")

        logger.info(f"✅ Loaded {len(self.rules)} validation rules")

    def load_from_python_modules(self):
        """Load rules by scanning Python modules (fallback)."""
        logger.info("📂 Scanning Python modules for validation rules...")

        rules_dir = Path("src/toetsregels/regels")
        if not rules_dir.exists():
            logger.error(f"❌ Rules directory not found: {rules_dir}")
            return

        # Scan for Python rule files
        categories = ["ARAI", "CON", "ESS", "INT", "SAM", "STR", "VER"]

        for category in categories:
            category_dir = rules_dir / category.lower()
            if not category_dir.exists():
                continue

            self.categories[category] = []

            for py_file in category_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue

                # Extract rule metadata from filename
                rule_id = py_file.stem.upper().replace("_", "-")

                rule = {
                    "id": rule_id,
                    "category": category,
                    "source_file": str(py_file),
                    "naam": rule_id,
                    "uitleg": f"Validation rule {rule_id}",
                }

                self.rules.append(rule)
                self.categories[category].append(rule)

        logger.info(f"✅ Found {len(self.rules)} validation rules in Python modules")

    def generate_html(self, output_path: str):
        """Generate HTML documentation.

        Args:
            output_path: Path to output HTML file
        """
        logger.info("📝 Generating HTML documentation...")

        html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Validation Rules Documentation - DefinitieAgent</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .meta {{
            opacity: 0.9;
            font-size: 0.9em;
        }}

        .search-box {{
            background: white;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .search-box input {{
            width: 100%;
            padding: 12px 20px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            transition: border-color 0.3s;
        }}

        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
        }}

        .category {{
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .category-header {{
            background: #667eea;
            color: white;
            padding: 15px 20px;
            font-size: 1.3em;
            font-weight: bold;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .category-header:hover {{
            background: #5568d3;
        }}

        .category-content {{
            padding: 20px;
        }}

        .rule {{
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 20px;
            background: #f9f9f9;
            border-radius: 5px;
        }}

        .rule-id {{
            font-size: 1.1em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .rule-name {{
            font-size: 1em;
            color: #555;
            margin-bottom: 10px;
        }}

        .rule-description {{
            color: #666;
            margin-bottom: 10px;
        }}

        .rule-meta {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e0e0e0;
        }}

        .meta-item {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.85em;
            color: #666;
        }}

        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            font-weight: bold;
        }}

        .badge-high {{ background: #ff4444; color: white; }}
        .badge-medium {{ background: #ffbb33; color: white; }}
        .badge-low {{ background: #00C851; color: white; }}

        footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            margin-top: 40px;
        }}
    </style>
    <script>
        function searchRules() {{
            const query = document.getElementById('searchInput').value.toLowerCase();
            const rules = document.querySelectorAll('.rule');

            rules.forEach(rule => {{
                const text = rule.textContent.toLowerCase();
                rule.style.display = text.includes(query) ? 'block' : 'none';
            }});
        }}
    </script>
</head>
<body>
    <div class="container">
        <header>
            <h1>📋 Validation Rules Documentation</h1>
            <div class="meta">
                Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
                Total Rules: {len(self.rules)} |
                Categories: {len(self.categories)}
            </div>
        </header>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Search rules..."
                   onkeyup="searchRules()">
        </div>
"""

        # Generate categories
        for category, rules in sorted(self.categories.items()):
            html += f"""
        <div class="category">
            <div class="category-header">
                <span>{category} - {self.get_category_name(category)}</span>
                <span>({len(rules)} rules)</span>
            </div>
            <div class="category-content">
"""

            for rule in rules:
                priority = rule.get("prioriteit", "medium")
                html += f"""
                <div class="rule">
                    <div class="rule-id">{rule.get('id', 'UNKNOWN')}</div>
                    <div class="rule-name">{rule.get('naam', 'No name')}</div>
                    <div class="rule-description">{rule.get('uitleg', 'No description')}</div>
                    <div class="rule-meta">
                        <span class="meta-item">
                            <span class="badge badge-{priority}">{priority.upper()}</span>
                        </span>
                        <span class="meta-item">📁 {rule.get('category', 'N/A')}</span>
                    </div>
                </div>
"""

            html += """
            </div>
        </div>
"""

        html += """
        <footer>
            <p>DefinitieAgent Validation Rules Documentation</p>
            <p>Generated automatically from rule configurations</p>
        </footer>
    </div>
</body>
</html>
"""

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"✅ HTML documentation saved to: {output_file}")

    def generate_markdown(self, output_path: str):
        """Generate Markdown documentation.

        Args:
            output_path: Path to output Markdown file
        """
        logger.info("📝 Generating Markdown documentation...")

        md = f"""# Validation Rules Documentation

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Total Rules:** {len(self.rules)}
**Categories:** {len(self.categories)}

---

## Table of Contents

"""

        # TOC
        for category in sorted(self.categories.keys()):
            md += f"- [{category} - {self.get_category_name(category)}](#{category.lower()})\n"

        md += "\n---\n\n"

        # Categories
        for category, rules in sorted(self.categories.items()):
            md += f"## {category} - {self.get_category_name(category)}\n\n"
            md += f"**Rules in this category:** {len(rules)}\n\n"

            for rule in rules:
                priority = rule.get("prioriteit", "medium")
                md += f"### {rule.get('id', 'UNKNOWN')}\n\n"
                md += f"**Name:** {rule.get('naam', 'No name')}  \n"
                md += f"**Priority:** {priority.upper()}  \n"
                md += f"**Category:** {rule.get('category', 'N/A')}  \n\n"
                md += f"{rule.get('uitleg', 'No description')}\n\n"
                md += "---\n\n"

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md)

        logger.info(f"✅ Markdown documentation saved to: {output_file}")

    def get_category_name(self, category: str) -> str:
        """Get full category name.

        Args:
            category: Category code

        Returns:
            Full category name
        """
        names = {
            "ARAI": "Actionable/Relevant",
            "CON": "Consistency",
            "ESS": "Essential Content",
            "INT": "Integrity",
            "SAM": "Coherence",
            "STR": "Structure",
            "VER": "Verification",
            "DUP": "Duplicate Detection",
        }
        return names.get(category, "Unknown")

    def execute(self, output_path: str, output_format: str = "html"):
        """Execute documentation generation.

        Args:
            output_path: Output file path
            output_format: Output format ("html" or "markdown")
        """
        logger.info("=" * 60)
        logger.info("VALIDATION RULES DOCUMENTATION GENERATOR")
        logger.info("=" * 60)

        # Load rules
        self.load_validation_rules()

        if len(self.rules) == 0:
            logger.error("❌ No validation rules found")
            return False

        # Generate documentation
        if output_format == "html":
            self.generate_html(output_path)
        elif output_format == "markdown":
            self.generate_markdown(output_path)
        else:
            logger.error(f"❌ Unknown format: {output_format}")
            return False

        logger.info("=" * 60)
        logger.info("✅ DOCUMENTATION GENERATION COMPLETE")
        logger.info("=" * 60)
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate validation rules documentation"
    )
    parser.add_argument(
        "--output",
        default="docs/validation_rules.html",
        help="Output file path (default: docs/validation_rules.html)",
    )
    parser.add_argument(
        "--format",
        choices=["html", "markdown"],
        default="html",
        help="Output format (default: html)",
    )

    args = parser.parse_args()

    # Execute documentation generation
    documenter = ValidationRuleDocumenter()
    success = documenter.execute(args.output, args.format)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
