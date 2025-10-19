#!/usr/bin/env python3
"""
Architecture Validator - Ensures EA/SA document consistency
Checks for overlap, validates cross-references, ensures proper separation
"""

import difflib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ValidationResult:
    """Result of a validation check"""

    check_name: str
    status: str  # 'pass', 'warning', 'error'
    message: str
    details: list[str] = None
    file_path: str = None
    line_number: int = None


@dataclass
class CrossReference:
    """Cross-reference between documents"""

    source_file: str
    source_line: int
    reference_text: str
    target_file: str
    target_section: str
    is_valid: bool = None


class ArchitectureValidator:
    """Validates architecture document consistency and compliance"""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.arch_root = self.project_root / "docs" / "architectuur"
        self.results: list[ValidationResult] = []

        # Define document types and their expected characteristics
        self.ea_characteristics = {
            "strategic_keywords": [
                "business",
                "capability",
                "governance",
                "investment",
                "stakeholder",
            ],
            "max_tech_detail_ratio": 0.3,  # Max 30% technical content
            "required_sections": [
                "Business Architecture",
                "Information Architecture",
                "Governance",
            ],
        }

        self.sa_characteristics = {
            "technical_keywords": [
                "api",
                "component",
                "deployment",
                "code",
                "database",
            ],
            "min_tech_detail_ratio": 0.7,  # Min 70% technical content
            "required_sections": [
                "System Architecture",
                "Technical Design",
                "API Design",
            ],
        }

        # Cross-reference patterns
        self.cross_ref_patterns = [
            r"→\s*\[?([^\]]+)\]?\s*Section\s*([\d\.]+)",  # → EA Section 1.1
            r"See\s+([^\s]+)\s+Section\s*([\d\.]+)",  # See SA Section 2.1
            r"Link\s+to\s+([^\s]+)\s*([\d\.]+)",  # Link to EA 3.2
        ]

    def validate_all(self) -> dict[str, any]:
        """Run all validation checks"""
        print("🔍 Starting architecture validation...")

        # Check if documents exist
        ea_doc = self.arch_root / "ENTERPRISE_ARCHITECTURE.md"
        sa_doc = self.arch_root / "SOLUTION_ARCHITECTURE.md"

        if not ea_doc.exists():
            self.results.append(
                ValidationResult(
                    "document_existence",
                    "error",
                    "Enterprise Architecture document not found",
                    file_path=str(ea_doc),
                )
            )

        if not sa_doc.exists():
            self.results.append(
                ValidationResult(
                    "document_existence",
                    "error",
                    "Solution Architecture document not found",
                    file_path=str(sa_doc),
                )
            )

        if not ea_doc.exists() or not sa_doc.exists():
            return self._generate_report()

        # Read documents
        ea_content = ea_doc.read_text(encoding="utf-8")
        sa_content = sa_doc.read_text(encoding="utf-8")

        # Run validation checks
        self._check_document_separation(ea_content, sa_content)
        self._check_content_overlap(ea_content, sa_content)
        self._validate_cross_references(ea_content, sa_content)
        self._check_required_sections(ea_content, sa_content)
        self._check_abstraction_levels(ea_content, sa_content)
        self._validate_template_compliance(ea_content, sa_content)

        return self._generate_report()

    def _check_document_separation(self, ea_content: str, sa_content: str):
        """Check if documents maintain proper separation of concerns"""
        print("  📋 Checking document separation...")

        # Check EA for too much technical content
        tech_ratio = self._calculate_technical_content_ratio(ea_content)
        if tech_ratio > self.ea_characteristics["max_tech_detail_ratio"]:
            self.results.append(
                ValidationResult(
                    "document_separation",
                    "warning",
                    f'EA document has {tech_ratio:.1%} technical content (max {self.ea_characteristics["max_tech_detail_ratio"]:.1%})',
                    details=self._find_technical_sections(ea_content),
                )
            )

        # Check SA for too much business content
        tech_ratio_sa = self._calculate_technical_content_ratio(sa_content)
        if tech_ratio_sa < self.sa_characteristics["min_tech_detail_ratio"]:
            self.results.append(
                ValidationResult(
                    "document_separation",
                    "warning",
                    f'SA document has {tech_ratio_sa:.1%} technical content (min {self.sa_characteristics["min_tech_detail_ratio"]:.1%})',
                    details=self._find_business_sections(sa_content),
                )
            )

    def _check_content_overlap(self, ea_content: str, sa_content: str):
        """Check for duplicate content between documents"""
        print("  🔄 Checking content overlap...")

        # Split into paragraphs and check for similarities
        ea_paragraphs = self._extract_paragraphs(ea_content)
        sa_paragraphs = self._extract_paragraphs(sa_content)

        duplicates = []
        for i, ea_para in enumerate(ea_paragraphs):
            for j, sa_para in enumerate(sa_paragraphs):
                similarity = difflib.SequenceMatcher(None, ea_para, sa_para).ratio()
                if (
                    similarity > 0.8 and len(ea_para) > 100
                ):  # 80% similar and substantial content
                    duplicates.append(
                        {
                            "ea_paragraph": i + 1,
                            "sa_paragraph": j + 1,
                            "similarity": similarity,
                            "content": ea_para[:100] + "...",
                        }
                    )

        if duplicates:
            self.results.append(
                ValidationResult(
                    "content_overlap",
                    "warning",
                    f"Found {len(duplicates)} potentially duplicate paragraphs",
                    details=[
                        f"EA para {d['ea_paragraph']} <-> SA para {d['sa_paragraph']} ({d['similarity']:.1%} similar)"
                        for d in duplicates
                    ],
                )
            )

    def _validate_cross_references(self, ea_content: str, sa_content: str):
        """Validate that cross-references between documents are valid"""
        print("  🔗 Validating cross-references...")

        # Find all cross-references
        ea_refs = self._find_cross_references(ea_content, "EA")
        sa_refs = self._find_cross_references(sa_content, "SA")

        all_refs = ea_refs + sa_refs
        invalid_refs = []

        for ref in all_refs:
            if not self._validate_cross_reference(ref, ea_content, sa_content):
                invalid_refs.append(ref)

        if invalid_refs:
            self.results.append(
                ValidationResult(
                    "cross_references",
                    "error",
                    f"Found {len(invalid_refs)} invalid cross-references",
                    details=[
                        f"{ref.source_file}:{ref.source_line} -> {ref.reference_text}"
                        for ref in invalid_refs
                    ],
                )
            )

        # Check for missing cross-references
        missing_refs = self._find_missing_cross_references(ea_content, sa_content)
        if missing_refs:
            self.results.append(
                ValidationResult(
                    "missing_cross_references",
                    "warning",
                    f"Found {len(missing_refs)} potential missing cross-references",
                    details=missing_refs,
                )
            )

    def _check_required_sections(self, ea_content: str, sa_content: str):
        """Check if required sections are present"""
        print("  📑 Checking required sections...")

        # Check EA required sections
        ea_sections = self._extract_sections(ea_content)
        for required in self.ea_characteristics["required_sections"]:
            if not any(required.lower() in section.lower() for section in ea_sections):
                self.results.append(
                    ValidationResult(
                        "required_sections",
                        "error",
                        f"EA missing required section: {required}",
                    )
                )

        # Check SA required sections
        sa_sections = self._extract_sections(sa_content)
        for required in self.sa_characteristics["required_sections"]:
            if not any(required.lower() in section.lower() for section in sa_sections):
                self.results.append(
                    ValidationResult(
                        "required_sections",
                        "error",
                        f"SA missing required section: {required}",
                    )
                )

    def _check_abstraction_levels(self, ea_content: str, sa_content: str):
        """Check if documents maintain appropriate abstraction levels"""
        print("  🎯 Checking abstraction levels...")

        # Check for code snippets in EA (should be minimal)
        ea_code_blocks = len(re.findall(r"```[\s\S]*?```", ea_content))
        if ea_code_blocks > 2:
            self.results.append(
                ValidationResult(
                    "abstraction_level",
                    "warning",
                    f"EA contains {ea_code_blocks} code blocks (should be minimal for strategic document)",
                )
            )

        # Check for business strategy in SA (should be references only)
        business_terms = [
            "roi",
            "investment",
            "business case",
            "strategic",
            "governance",
        ]
        sa_business_mentions = sum(
            len(re.findall(term, sa_content, re.IGNORECASE)) for term in business_terms
        )
        if sa_business_mentions > 10:  # Allow some references
            self.results.append(
                ValidationResult(
                    "abstraction_level",
                    "warning",
                    f"SA contains {sa_business_mentions} business strategy mentions (should focus on implementation)",
                )
            )

    def _validate_template_compliance(self, ea_content: str, sa_content: str):
        """Check if documents follow their respective templates"""
        print("  📋 Checking template compliance...")

        # Check if EA follows enterprise template structure
        ea_expected_sections = [
            "Executive Summary",
            "Business Architecture",
            "Information Architecture",
            "Application Architecture",
            "Technology Architecture",
            "Governance",
        ]

        sa_expected_sections = [
            "Executive Summary",
            "System Architecture",
            "Technical Design",
            "Integration Architecture",
            "Security Implementation",
            "Performance Engineering",
        ]

        # Validate EA structure
        ea_sections = self._extract_sections(ea_content)
        missing_ea = [
            sec
            for sec in ea_expected_sections
            if not any(sec.lower() in s.lower() for s in ea_sections)
        ]
        if missing_ea:
            self.results.append(
                ValidationResult(
                    "template_compliance",
                    "warning",
                    f'EA missing template sections: {", ".join(missing_ea)}',
                )
            )

        # Validate SA structure
        sa_sections = self._extract_sections(sa_content)
        missing_sa = [
            sec
            for sec in sa_expected_sections
            if not any(sec.lower() in s.lower() for s in sa_sections)
        ]
        if missing_sa:
            self.results.append(
                ValidationResult(
                    "template_compliance",
                    "warning",
                    f'SA missing template sections: {", ".join(missing_sa)}',
                )
            )

    # Helper methods

    def _calculate_technical_content_ratio(self, content: str) -> float:
        """Calculate ratio of technical vs business content"""
        technical_keywords = [
            "api",
            "database",
            "code",
            "deployment",
            "kubernetes",
            "docker",
            "sql",
            "http",
            "json",
        ]
        business_keywords = [
            "business",
            "strategy",
            "governance",
            "investment",
            "stakeholder",
            "capability",
        ]

        tech_count = sum(
            len(re.findall(keyword, content, re.IGNORECASE))
            for keyword in technical_keywords
        )
        business_count = sum(
            len(re.findall(keyword, content, re.IGNORECASE))
            for keyword in business_keywords
        )

        total = tech_count + business_count
        return tech_count / total if total > 0 else 0

    def _extract_paragraphs(self, content: str) -> list[str]:
        """Extract paragraphs from markdown content"""
        # Remove markdown headers, code blocks, etc.
        clean_content = re.sub(r"```[\s\S]*?```", "", content)
        clean_content = re.sub(r"^#+.*$", "", clean_content, flags=re.MULTILINE)

        return [
            p.strip() for p in clean_content.split("\n\n") if len(p.strip()) > 50
        ]

    def _extract_sections(self, content: str) -> list[str]:
        """Extract section headers from markdown"""
        return re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)

    def _find_cross_references(
        self, content: str, source_type: str
    ) -> list[CrossReference]:
        """Find all cross-references in content"""
        refs = []
        lines = content.split("\n")

        for i, line in enumerate(lines):
            for pattern in self.cross_ref_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    refs.append(
                        CrossReference(
                            source_file=source_type,
                            source_line=i + 1,
                            reference_text=match.group(0),
                            target_file=(
                                match.group(1) if len(match.groups()) > 0 else "unknown"
                            ),
                            target_section=(
                                match.group(2) if len(match.groups()) > 1 else "unknown"
                            ),
                        )
                    )

        return refs

    def _validate_cross_reference(
        self, ref: CrossReference, ea_content: str, sa_content: str
    ) -> bool:
        """Validate a specific cross-reference"""
        target_content = ea_content if "EA" in ref.target_file else sa_content

        # Look for the target section
        section_pattern = rf"^#+\s+{re.escape(ref.target_section)}[^\n]*"
        return bool(
            re.search(section_pattern, target_content, re.MULTILINE | re.IGNORECASE)
        )

    def _find_missing_cross_references(
        self, ea_content: str, sa_content: str
    ) -> list[str]:
        """Find places where cross-references should exist but don't"""
        missing = []

        # Look for mentions of business concepts in SA that should reference EA
        business_mentions = re.findall(
            r"(business capability|governance|compliance|investment)",
            sa_content,
            re.IGNORECASE,
        )
        if business_mentions and "→ EA" not in sa_content:
            missing.append("SA mentions business concepts but lacks EA references")

        # Look for mentions of technical concepts in EA that should reference SA
        tech_mentions = re.findall(
            r"(api|deployment|database|implementation)", ea_content, re.IGNORECASE
        )
        if tech_mentions and "→ SA" not in ea_content:
            missing.append("EA mentions technical concepts but lacks SA references")

        return missing

    def _find_technical_sections(self, content: str) -> list[str]:
        """Find sections that are too technical for EA"""
        technical_indicators = ["```", "api/", "database schema", "deployment", "code"]
        sections = []

        current_section = None
        for line in content.split("\n"):
            if re.match(r"^#+\s+", line):
                current_section = line.strip()
            elif current_section and any(
                indicator in line.lower() for indicator in technical_indicators
            ) and current_section not in sections:
                sections.append(current_section)

        return sections

    def _find_business_sections(self, content: str) -> list[str]:
        """Find sections that are too business-focused for SA"""
        business_indicators = [
            "stakeholder",
            "governance",
            "investment",
            "roi",
            "business case",
        ]
        sections = []

        current_section = None
        for line in content.split("\n"):
            if re.match(r"^#+\s+", line):
                current_section = line.strip()
            elif current_section and any(
                indicator in line.lower() for indicator in business_indicators
            ) and current_section not in sections:
                sections.append(current_section)

        return sections

    def _generate_report(self) -> dict[str, any]:
        """Generate validation report"""
        errors = [r for r in self.results if r.status == "error"]
        warnings = [r for r in self.results if r.status == "warning"]
        passed = [r for r in self.results if r.status == "pass"]

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": len(self.results),
                "errors": len(errors),
                "warnings": len(warnings),
                "passed": len(passed),
                "overall_status": (
                    "error" if errors else "warning" if warnings else "pass"
                ),
            },
            "errors": [self._result_to_dict(r) for r in errors],
            "warnings": [self._result_to_dict(r) for r in warnings],
            "passed": [self._result_to_dict(r) for r in passed],
        }


    def _result_to_dict(self, result: ValidationResult) -> dict[str, any]:
        """Convert ValidationResult to dictionary"""
        return {
            "check": result.check_name,
            "status": result.status,
            "message": result.message,
            "details": result.details or [],
            "file": result.file_path,
            "line": result.line_number,
        }

    def save_report(self, report: dict[str, any], output_file: Path | None = None):
        """Save validation report to file"""
        if output_file is None:
            output_file = self.arch_root / "validation-report.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ Validation report saved to {output_file}")

    def print_summary(self, report: dict[str, any]):
        """Print validation summary to console"""
        summary = report["summary"]
        status_emoji = {"pass": "✅", "warning": "⚠️", "error": "❌"}

        print(
            f"\n{status_emoji[summary['overall_status']]} Architecture Validation Summary"
        )
        print(f"Total checks: {summary['total_checks']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        print(f"❌ Errors: {summary['errors']}")

        if report["errors"]:
            print("\n❌ Errors:")
            for error in report["errors"]:
                print(f"  - {error['message']}")

        if report["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in report["warnings"]:
                print(f"  - {warning['message']}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate architecture document consistency"
    )
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument("--output", type=Path, help="Output file for validation report")
    parser.add_argument("--quiet", action="store_true", help="Only show errors")

    args = parser.parse_args()

    validator = ArchitectureValidator(args.project_root)
    report = validator.validate_all()

    if not args.quiet:
        validator.print_summary(report)

    if args.output:
        validator.save_report(report, args.output)
    else:
        validator.save_report(report)

    # Exit with error code if validation failed
    if report["summary"]["overall_status"] == "error":
        sys.exit(1)
    elif report["summary"]["overall_status"] == "warning" and not args.quiet:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
