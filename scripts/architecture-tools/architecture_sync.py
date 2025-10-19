#!/usr/bin/env python3
"""
Architecture Synchronization Service
Ensures EA and SA documents stay synchronized while maintaining separation
"""

import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SyncItem:
    """Item that needs synchronization between documents"""

    type: str  # 'metric', 'reference', 'status', 'decision'
    source_doc: str
    source_section: str
    content: str
    target_doc: str
    target_section: str
    last_sync: str | None = None
    checksum: str | None = None


@dataclass
class SyncReport:
    """Synchronization report"""

    timestamp: str
    items_checked: int
    items_synced: int
    conflicts: list[dict[str, Any]]
    warnings: list[str]
    status: str  # 'success', 'warning', 'error'


class ArchitectureSync:
    """Manages synchronization between EA and SA documents"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.arch_root = self.project_root / "docs" / "architectuur"
        self.sync_config_path = self.arch_root / "sync-config.yaml"
        self.sync_state_path = self.arch_root / "sync-state.json"

        # Load configuration
        self.config = self._load_sync_config()
        self.state = self._load_sync_state()

    def _load_sync_config(self) -> dict[str, Any]:
        """Load synchronization configuration"""
        default_config = {
            "sync_rules": {
                "shared_metrics": {
                    "source": "EA",
                    "targets": ["SA"],
                    "sections": ["KPIs", "Performance Targets"],
                    "pattern": r"\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|",
                },
                "cross_references": {"auto_update": True, "validate_targets": True},
                "architecture_decisions": {
                    "source": "ADRs",
                    "sync_to": ["EA", "SA"],
                    "format": "summary",
                },
            },
            "validation": {
                "max_content_overlap": 0.1,  # 10%
                "required_cross_refs": [
                    {"from": "SA", "to": "EA", "sections": ["Business Context"]},
                    {
                        "from": "EA",
                        "to": "SA",
                        "sections": ["Technical Implementation"],
                    },
                ],
            },
        }

        if self.sync_config_path.exists():
            with open(self.sync_config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                # Merge with defaults
                default_config.update(config)
        else:
            # Create default config file
            with open(self.sync_config_path, "w", encoding="utf-8") as f:
                yaml.dump(default_config, f, default_flow_style=False)

        return default_config

    def _load_sync_state(self) -> dict[str, Any]:
        """Load previous synchronization state"""
        if self.sync_state_path.exists():
            with open(self.sync_state_path, encoding="utf-8") as f:
                return json.load(f)
        return {"last_sync": None, "checksums": {}, "items": []}

    def _save_sync_state(self):
        """Save current synchronization state"""
        with open(self.sync_state_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def sync_all(self) -> SyncReport:
        """Perform complete synchronization"""
        print("🔄 Starting architecture synchronization...")

        conflicts = []
        warnings = []
        items_synced = 0

        try:
            # Load documents
            ea_doc = self._load_document("ENTERPRISE_ARCHITECTURE.md")
            sa_doc = self._load_document("SOLUTION_ARCHITECTURE.md")

            if not ea_doc or not sa_doc:
                return SyncReport(
                    timestamp=datetime.now().isoformat(),
                    items_checked=0,
                    items_synced=0,
                    conflicts=[],
                    warnings=["One or more architecture documents not found"],
                    status="error",
                )

            # Synchronize shared metrics
            metrics_result = self._sync_shared_metrics(ea_doc, sa_doc)
            items_synced += metrics_result["synced"]
            conflicts.extend(metrics_result["conflicts"])
            warnings.extend(metrics_result["warnings"])

            # Update cross-references
            refs_result = self._update_cross_references(ea_doc, sa_doc)
            items_synced += refs_result["synced"]
            conflicts.extend(refs_result["conflicts"])
            warnings.extend(refs_result["warnings"])

            # Sync ADRs
            adr_result = self._sync_architecture_decisions()
            items_synced += adr_result["synced"]
            warnings.extend(adr_result["warnings"])

            # Validate consistency
            validation_result = self._validate_consistency(ea_doc, sa_doc)
            warnings.extend(validation_result["warnings"])
            conflicts.extend(validation_result["conflicts"])

            # Update state
            self.state["last_sync"] = datetime.now().isoformat()
            self._save_sync_state()

            status = "error" if conflicts else "warning" if warnings else "success"

            return SyncReport(
                timestamp=datetime.now().isoformat(),
                items_checked=len(self.state.get("items", [])),
                items_synced=items_synced,
                conflicts=conflicts,
                warnings=warnings,
                status=status,
            )

        except Exception as e:
            return SyncReport(
                timestamp=datetime.now().isoformat(),
                items_checked=0,
                items_synced=0,
                conflicts=[{"type": "system_error", "message": str(e)}],
                warnings=[],
                status="error",
            )

    def _load_document(self, filename: str) -> dict[str, Any] | None:
        """Load and parse architecture document"""
        file_path = self.arch_root / filename
        if not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")

        return {
            "path": file_path,
            "content": content,
            "sections": self._parse_sections(content),
            "checksum": hashlib.md5(content.encode()).hexdigest(),
        }

    def _parse_sections(self, content: str) -> dict[str, str]:
        """Parse markdown sections"""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split("\n"):
            header_match = re.match(r"^(#+)\s+(.+)$", line)
            if header_match:
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = header_match.group(2)
                current_content = []
            else:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _sync_shared_metrics(self, ea_doc: dict, sa_doc: dict) -> dict[str, Any]:
        """Synchronize shared metrics between documents"""
        print("  📊 Syncing shared metrics...")

        synced = 0
        conflicts = []
        warnings = []

        # Find metrics tables in EA
        ea_content = ea_doc["content"]
        sa_content = sa_doc["content"]

        # Look for KPI tables
        kpi_pattern = r"\|\s*KPI\s*\|[^\n]*\n\|[^\n]*\n((?:\|[^\n]*\n)*)"
        ea_kpis = re.findall(kpi_pattern, ea_content, re.MULTILINE)
        sa_kpis = re.findall(kpi_pattern, sa_content, re.MULTILINE)

        if ea_kpis and sa_kpis:
            # Compare KPIs
            ea_kpi_data = self._parse_table(ea_kpis[0])
            sa_kpi_data = self._parse_table(sa_kpis[0])

            # Check for conflicts
            for kpi in ea_kpi_data:
                if kpi["name"] in [s["name"] for s in sa_kpi_data]:
                    sa_kpi = next(s for s in sa_kpi_data if s["name"] == kpi["name"])
                    if kpi["target"] != sa_kpi["target"]:
                        conflicts.append(
                            {
                                "type": "metric_conflict",
                                "metric": kpi["name"],
                                "ea_value": kpi["target"],
                                "sa_value": sa_kpi["target"],
                            }
                        )

        return {"synced": synced, "conflicts": conflicts, "warnings": warnings}

    def _parse_table(self, table_content: str) -> list[dict[str, str]]:
        """Parse markdown table into list of dictionaries"""
        rows = []
        lines = table_content.strip().split("\n")

        for line in lines:
            if "|" in line:
                cells = [cell.strip() for cell in line.split("|") if cell.strip()]
                if len(cells) >= 3:
                    rows.append(
                        {
                            "name": cells[0],
                            "current": cells[1] if len(cells) > 1 else "",
                            "target": cells[2] if len(cells) > 2 else "",
                        }
                    )

        return rows

    def _update_cross_references(self, ea_doc: dict, sa_doc: dict) -> dict[str, Any]:
        """Update and validate cross-references"""
        print("  🔗 Updating cross-references...")

        synced = 0
        conflicts = []
        warnings = []

        # Find cross-references that need updating
        ref_pattern = r"→\s*\[([^\]]+)\]\s*Section\s*([\d\.]+)"

        ea_refs = re.findall(ref_pattern, ea_doc["content"])
        sa_refs = re.findall(ref_pattern, sa_doc["content"])

        # Validate references
        for ref_text, section in ea_refs + sa_refs:
            target_doc = sa_doc if "SA" in ref_text else ea_doc
            if not self._section_exists(target_doc, section):
                warnings.append(f"Invalid reference to {ref_text} Section {section}")

        return {"synced": synced, "conflicts": conflicts, "warnings": warnings}

    def _section_exists(self, doc: dict, section: str) -> bool:
        """Check if a section exists in a document"""
        # Look for section numbers in headers
        pattern = rf"^#+\s+{re.escape(section)}[^\n]*"
        return bool(re.search(pattern, doc["content"], re.MULTILINE))

    def _sync_architecture_decisions(self) -> dict[str, Any]:
        """Synchronize architecture decisions from ADRs"""
        print("  📋 Syncing architecture decisions...")

        synced = 0
        warnings = []

        adr_dir = self.arch_root / "beslissingen"
        if not adr_dir.exists():
            warnings.append("ADR directory not found")
            return {"synced": synced, "warnings": warnings}

        # Read all ADRs
        adrs = []
        for adr_file in adr_dir.glob("ADR-*.md"):
            content = adr_file.read_text(encoding="utf-8")
            adr_data = self._parse_adr(content)
            if adr_data:
                adrs.append(adr_data)

        # Update ADR sections in EA and SA documents
        if adrs:
            self._update_adr_references(adrs)
            synced = len(adrs)

        return {"synced": synced, "warnings": warnings}

    def _parse_adr(self, content: str) -> dict[str, str] | None:
        """Parse ADR content"""
        title_match = re.search(r"^#\s+ADR-\d+:\s*(.+)$", content, re.MULTILINE)
        status_match = re.search(r"\*\*Status\*\*:\s*(.+)", content)
        decision_match = re.search(r"\*\*Decision\*\*:\s*(.+)", content)

        if title_match:
            return {
                "title": title_match.group(1),
                "status": status_match.group(1) if status_match else "Unknown",
                "decision": decision_match.group(1) if decision_match else "",
            }

        return None

    def _update_adr_references(self, adrs: list[dict[str, str]]):
        """Update ADR references in architecture documents"""
        # This would update the ADR sections in both EA and SA documents
        # Implementation depends on specific section structure

    def _validate_consistency(self, ea_doc: dict, sa_doc: dict) -> dict[str, Any]:
        """Validate consistency between documents"""
        print("  ✅ Validating consistency...")

        warnings = []
        conflicts = []

        # Check for content overlap
        overlap_ratio = self._calculate_content_overlap(
            ea_doc["content"], sa_doc["content"]
        )
        max_overlap = self.config["validation"]["max_content_overlap"]

        if overlap_ratio > max_overlap:
            warnings.append(
                f"Content overlap {overlap_ratio:.1%} exceeds threshold {max_overlap:.1%}"
            )

        # Check required cross-references
        for req_ref in self.config["validation"]["required_cross_refs"]:
            if not self._has_cross_reference(ea_doc, sa_doc, req_ref):
                warnings.append(
                    f"Missing required cross-reference from {req_ref['from']} to {req_ref['to']}"
                )

        return {"warnings": warnings, "conflicts": conflicts}

    def _calculate_content_overlap(self, content1: str, content2: str) -> float:
        """Calculate content overlap between two documents"""
        # Simple implementation - could be enhanced with more sophisticated algorithms
        paragraphs1 = set(self._extract_paragraphs(content1))
        paragraphs2 = set(self._extract_paragraphs(content2))

        if not paragraphs1 or not paragraphs2:
            return 0.0

        overlap = len(paragraphs1.intersection(paragraphs2))
        total = len(paragraphs1.union(paragraphs2))

        return overlap / total if total > 0 else 0.0

    def _extract_paragraphs(self, content: str) -> list[str]:
        """Extract paragraphs from content"""
        # Remove code blocks and headers
        clean_content = re.sub(r"```[\s\S]*?```", "", content)
        clean_content = re.sub(r"^#+.*$", "", clean_content, flags=re.MULTILINE)

        return [
            p.strip() for p in clean_content.split("\n\n") if len(p.strip()) > 50
        ]

    def _has_cross_reference(self, ea_doc: dict, sa_doc: dict, req_ref: dict) -> bool:
        """Check if required cross-reference exists"""
        source_doc = ea_doc if req_ref["from"] == "EA" else sa_doc
        target_name = req_ref["to"]

        # Look for cross-reference pattern
        pattern = rf"→.*{target_name}"
        return bool(re.search(pattern, source_doc["content"], re.IGNORECASE))

    def generate_sync_dashboard(self) -> str:
        """Generate HTML dashboard for sync status"""
        report = self.sync_all()

        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Architecture Sync Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .status-{report.status} {{ color: {'green' if report.status == 'success' else 'orange' if report.status == 'warning' else 'red'}; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <h1>Architecture Synchronization Dashboard</h1>
    <p class="status-{report.status}">Status: {report.status.upper()}</p>
    <p>Last sync: {report.timestamp}</p>

    <div class="metric">
        <h3>Items Checked</h3>
        <p>{report.items_checked}</p>
    </div>

    <div class="metric">
        <h3>Items Synced</h3>
        <p>{report.items_synced}</p>
    </div>

    <div class="metric">
        <h3>Conflicts</h3>
        <p>{len(report.conflicts)}</p>
    </div>

    <div class="metric">
        <h3>Warnings</h3>
        <p>{len(report.warnings)}</p>
    </div>

    {self._generate_details_html(report)}
</body>
</html>
        """


    def _generate_details_html(self, report: SyncReport) -> str:
        """Generate detailed HTML for sync report"""
        html = ""

        if report.conflicts:
            html += "<h2>Conflicts</h2><ul>"
            for conflict in report.conflicts:
                html += f"<li>{conflict.get('type', 'Unknown')}: {conflict.get('message', 'No details')}</li>"
            html += "</ul>"

        if report.warnings:
            html += "<h2>Warnings</h2><ul>"
            for warning in report.warnings:
                html += f"<li>{warning}</li>"
            html += "</ul>"

        return html

    def save_report(self, report: SyncReport, output_file: Path | None = None):
        """Save sync report to file"""
        if output_file is None:
            output_file = self.arch_root / "sync-report.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)

        print(f"✅ Sync report saved to {output_file}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Synchronize architecture documents")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument("--output", type=Path, help="Output file for sync report")
    parser.add_argument(
        "--dashboard", action="store_true", help="Generate HTML dashboard"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Check sync status only"
    )

    args = parser.parse_args()

    sync_service = ArchitectureSync(args.project_root)

    if args.dashboard:
        dashboard_html = sync_service.generate_sync_dashboard()
        dashboard_file = sync_service.arch_root / "sync-dashboard.html"
        with open(dashboard_file, "w", encoding="utf-8") as f:
            f.write(dashboard_html)
        print(f"✅ Dashboard generated: {dashboard_file}")
    else:
        report = sync_service.sync_all()

        print(f"\n🔄 Sync Status: {report.status.upper()}")
        print(f"Items checked: {report.items_checked}")
        print(f"Items synced: {report.items_synced}")
        print(f"Conflicts: {len(report.conflicts)}")
        print(f"Warnings: {len(report.warnings)}")

        if report.conflicts:
            print("\n❌ Conflicts:")
            for conflict in report.conflicts:
                print(f"  - {conflict.get('message', str(conflict))}")

        if report.warnings:
            print("\n⚠️  Warnings:")
            for warning in report.warnings:
                print(f"  - {warning}")

        if args.output:
            sync_service.save_report(report, args.output)
        else:
            sync_service.save_report(report)

        # Exit with appropriate code
        if report.status == "error":
            sys.exit(1)
        elif report.status == "warning":
            sys.exit(2)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
