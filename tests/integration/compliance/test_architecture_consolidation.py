"""
Automated tests for architecture documentation consolidation validation.
Ensures canonical documents, templates, archives, and links are properly maintained.

Dit zijn historische documentcontroles: ze toetsen aanwezigheid, omvang en
tekstpatronen van documenten. Ze zijn géén compliance-oordeel over ASTRA/NORA.

DEF-519: BASE_DIR wees naar tests/integration (parents[1]) in plaats van de
projectwortel, dus elke controle keek in een niet-bestaande boom. Daarnaast
maakten `if not ...exists(): continue` en een runtime `pytest.skip` de uitslag
vals-groen bij nul bronnen. Beide zijn hier gecorrigeerd; een ontbrekende
verplichte bron faalt nu met het concrete pad.

Dispositie van de resterende rode nodes (geen skip/xfail, blijven zichtbaar):
  * ontbrekende EA/SA/TA/README-docfeiten en het consolidatie-archief -> DEF-619
  * ASTRA/NORA-intentie (test_astra_compliance_maintained) -> DEF-468
  trigger: de genoemde story; herbeoordeling uiterlijk 2026-10-06.
Geen documenten herbouwd en geen complianceoplevering in deze batch.
"""

import os
import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.compliance]

# `advisory`-dispositie (DEF-519), uitsluitend op de nodes die hieronder de
# marker dragen. De vier nodes zonder marker bewijzen actief gedrag en blijven
# onverkort in de verplichte gate; er wordt hier niets op bestandsniveau
# weggefilterd.
#
# Reden: de documentatiefacts uit deze suite horen bij DEF-619; de fixturefouten
# zijn hersteld, dus de resterende REDs zijn echte documentatiedrift en geen
# testdefect. Oude architectuurdocs worden niet herbouwd om groen te worden.
# Owner: DEF-619 (EA/SA/README-facts en documentatiedrift).
# Trigger: DEF-619 levert de documentatiefacts.
# Herbeoordeling: 2026-10-06.
# Uitzondering: `test_astra_compliance_maintained` heeft een eigen owner
# (DEF-468) en staat daar apart genoteerd.


class TestArchitectureConsolidation:
    """Test suite for validating architecture documentation consolidation."""

    # tests/integration/compliance/<dit bestand> -> parents[3] is de projectwortel.
    BASE_DIR = Path(__file__).resolve().parents[3]
    ARCH_DIR = BASE_DIR / "docs" / "architectuur"
    ARCHIVE_DIR = BASE_DIR / "docs" / "archief" / "2025-09-architectuur-consolidatie"

    def test_base_dir_points_at_checkout(self):
        """Discriminator: de scope moet de echte checkout zijn, niet leeg.

        Zonder deze node kan een verkeerde BASE_DIR opnieuw ongemerkt een lege
        boom opleveren waarin controles niets vinden.
        """
        assert (self.BASE_DIR / "pytest.ini").is_file(), self.BASE_DIR
        assert (self.BASE_DIR / "src").is_dir(), self.BASE_DIR
        assert (self.BASE_DIR / "docs").is_dir(), self.BASE_DIR

    @pytest.mark.advisory
    def test_canonical_docs_exist(self):
        """Test that all canonical architecture docs exist."""
        required_docs = [
            "ENTERPRISE_ARCHITECTURE.md",
            "SOLUTION_ARCHITECTURE.md",
            "TECHNICAL_ARCHITECTURE.md",
            "README.md",
        ]

        for doc_name in required_docs:
            doc_path = self.ARCH_DIR / doc_name
            assert (
                doc_path.exists()
            ), f"Canonical document {doc_name} not found at {doc_path}"
            assert (
                doc_path.stat().st_size > 1000
            ), f"Document {doc_name} appears to be empty or too small"

    def test_templates_accessible(self):
        """Test that all templates are in correct location."""
        template_dir = self.ARCH_DIR / "templates"
        assert template_dir.exists(), f"Template directory not found at {template_dir}"

        required_templates = [
            "ENTERPRISE_ARCHITECTURE_TEMPLATE.md",
            "SOLUTION_ARCHITECTURE_TEMPLATE.md",
            "TECHNICAL_ARCHITECTURE_TEMPLATE.md",
        ]

        for template_name in required_templates:
            template_path = template_dir / template_name
            assert (
                template_path.exists()
            ), f"Template {template_name} not found at {template_path}"
            assert (
                template_path.stat().st_size > 1000
            ), f"Template {template_name} appears to be empty"

    @pytest.mark.advisory
    def test_archive_structure(self):
        """Test that archive is properly organized."""
        assert (
            self.ARCHIVE_DIR.exists()
        ), f"Archive directory not found at {self.ARCHIVE_DIR}"

        # Check for key subdirectories
        expected_dirs = [
            "ea-variants",
            "sa-variants",
            "ta-variants",
            "old-templates",
            "consolidation-reports",
        ]

        for dir_name in expected_dirs:
            dir_path = self.ARCHIVE_DIR / dir_name
            assert dir_path.exists(), f"Archive subdirectory {dir_name} not found"

        # Check for documentation files
        readme_path = self.ARCHIVE_DIR / "README.md"
        assert readme_path.exists(), "Archive README.md not found"

        migration_log = self.ARCHIVE_DIR / "MIGRATION_LOG.md"
        assert migration_log.exists(), "MIGRATION_LOG.md not found in archive"

    @pytest.mark.advisory
    def test_cross_references_between_docs(self):
        """Test that canonical docs properly reference each other."""
        # Check EA references SA and TA
        ea_path = self.ARCH_DIR / "ENTERPRISE_ARCHITECTURE.md"
        sa_path = self.ARCH_DIR / "SOLUTION_ARCHITECTURE.md"
        ta_path = self.ARCH_DIR / "TECHNICAL_ARCHITECTURE.md"

        ontbrekend = [str(p) for p in (ea_path, sa_path, ta_path) if not p.exists()]
        assert not ontbrekend, f"Verplichte bron(nen) ontbreken: {ontbrekend}"

        with open(ea_path, encoding="utf-8") as f:
            ea_content = f.read()

        assert "SOLUTION_ARCHITECTURE.md" in ea_content, "EA doesn't reference SA"
        assert "TECHNICAL_ARCHITECTURE.md" in ea_content, "EA doesn't reference TA"

        # Check SA references EA (TA reference is optional but recommended)
        with open(sa_path, encoding="utf-8") as f:
            sa_content = f.read()

        assert "ENTERPRISE_ARCHITECTURE.md" in sa_content, "SA doesn't reference EA"

        # Check TA references EA and SA
        with open(ta_path, encoding="utf-8") as f:
            ta_content = f.read()

        assert "ENTERPRISE_ARCHITECTURE.md" in ta_content, "TA doesn't reference EA"
        assert "SOLUTION_ARCHITECTURE.md" in ta_content, "TA doesn't reference SA"

    @pytest.mark.advisory
    def test_no_broken_internal_links(self):
        """Test that no broken internal links exist in main architecture docs.

        DEF-519: ontbrekende documenten werden overgeslagen en gevonden broken
        links eindigden in `pytest.skip`, waardoor nul onderzochte bronnen als
        groen telden. Beide zijn nu een failure met concrete details.
        """
        broken_links = []
        onderzochte_docs = []

        canonical_docs = [
            "ENTERPRISE_ARCHITECTURE.md",
            "SOLUTION_ARCHITECTURE.md",
            "TECHNICAL_ARCHITECTURE.md",
            "README.md",
        ]

        ontbrekend = [
            str(self.ARCH_DIR / doc_name)
            for doc_name in canonical_docs
            if not (self.ARCH_DIR / doc_name).exists()
        ]
        assert not ontbrekend, f"Verplichte bron(nen) ontbreken: {ontbrekend}"

        for doc_name in canonical_docs:
            doc_path = self.ARCH_DIR / doc_name
            onderzochte_docs.append(doc_name)

            with open(doc_path, encoding="utf-8") as f:
                content = f.read()

            # Find markdown links (excluding URLs and anchors)
            pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
            matches = re.findall(pattern, content)

            for link_text, link_target in matches:
                # Skip external URLs and anchors
                if link_target.startswith(("http", "#")):
                    continue

                # Resolve relative paths
                if link_target.startswith("./"):
                    link_target = link_target[2:]

                # Build full path
                if link_target.startswith("/"):
                    full_path = self.BASE_DIR / link_target[1:]
                else:
                    full_path = doc_path.parent / link_target

                # Check if file exists
                if not full_path.exists():
                    broken_links.append(
                        {
                            "document": doc_name,
                            "text": link_text,
                            "target": link_target,
                            "resolved_path": str(full_path),
                        }
                    )

        # Discriminator: nul onderzochte bronnen mag nooit groen zijn.
        assert onderzochte_docs, "Geen enkel canoniek document onderzocht"

        if broken_links:
            details = "\n".join(
                f"  - [{link['text']}]({link['target']}) in {link['document']}"
                f" -> {link['resolved_path']}"
                for link in broken_links[:10]
            )
            raise AssertionError(
                f"Found {len(broken_links)} broken internal links:\n{details}"
            )

    # Eigen owner: niet-geïmplementeerde ASTRA/NORA-intentie, geen positieve
    # complianceclaim. Owner DEF-468, trigger: DEF-468 implementeert het
    # ASTRA/NORA-contract, herbeoordeling 2026-10-06.
    @pytest.mark.advisory
    def test_astra_compliance_maintained(self):
        """Historische documentcontrole op het aantal ASTRA-trefwoorden.

        Dit telt tekstvoorkomens in documenten. Het is uitdrukkelijk GEEN
        vaststelling van ASTRA-compliance; die claim kan niet uit trefwoorden
        volgen (DEF-468 houdt de ASTRA/NORA-intentie).
        """
        min_references = {
            "ENTERPRISE_ARCHITECTURE.md": 5,
            "SOLUTION_ARCHITECTURE.md": 1,
            "TECHNICAL_ARCHITECTURE.md": 3,
        }

        for doc_name, min_count in min_references.items():
            doc_path = self.ARCH_DIR / doc_name
            assert doc_path.exists(), f"Verplichte bron ontbreekt: {doc_path}"

            with open(doc_path, encoding="utf-8") as f:
                content = f.read()

            # Count ASTRA references (case insensitive)
            astra_count = len(re.findall(r"ASTRA|astra", content, re.IGNORECASE))
            assert (
                astra_count >= min_count
            ), f"{doc_name} has only {astra_count} ASTRA references, expected at least {min_count}"

    @pytest.mark.advisory
    def test_document_sizes_acceptable(self):
        """Test that consolidated documents are not too large."""
        max_size_kb = 150  # Maximum acceptable size in KB

        canonical_docs = [
            "ENTERPRISE_ARCHITECTURE.md",
            "SOLUTION_ARCHITECTURE.md",
            "TECHNICAL_ARCHITECTURE.md",
        ]

        for doc_name in canonical_docs:
            doc_path = self.ARCH_DIR / doc_name
            assert doc_path.exists(), f"Verplichte bron ontbreekt: {doc_path}"

            size_kb = doc_path.stat().st_size / 1024
            assert (
                size_kb <= max_size_kb
            ), f"{doc_name} is {size_kb:.1f}KB, exceeds max size of {max_size_kb}KB"

    def test_index_updated_with_new_structure(self):
        """Test that INDEX.md properly references the new structure."""
        index_path = self.BASE_DIR / "docs" / "INDEX.md"
        assert index_path.exists(), "INDEX.md not found"

        with open(index_path, encoding="utf-8") as f:
            content = f.read()

        # Check for canonical document references
        assert "ENTERPRISE_ARCHITECTURE.md" in content, "INDEX doesn't reference EA"
        assert "SOLUTION_ARCHITECTURE.md" in content, "INDEX doesn't reference SA"
        assert "TECHNICAL_ARCHITECTURE.md" in content, "INDEX doesn't reference TA"

        # Check for template references
        assert (
            "templates/ENTERPRISE_ARCHITECTURE_TEMPLATE.md" in content
        ), "INDEX doesn't reference EA template"
        assert (
            "templates/SOLUTION_ARCHITECTURE_TEMPLATE.md" in content
        ), "INDEX doesn't reference SA template"
        assert (
            "templates/TECHNICAL_ARCHITECTURE_TEMPLATE.md" in content
        ), "INDEX doesn't reference TA template"

    def test_no_duplicate_architecture_docs(self):
        """Test that no duplicate architecture documents exist outside archive."""
        # Find all .md files that might be duplicates
        docs_dir = self.BASE_DIR / "docs"
        assert docs_dir.is_dir(), f"docs-map ontbreekt: {docs_dir}"
        onderzochte_bestanden = 0

        duplicate_patterns = [
            r"EA[-_].*\.md",
            r"SA[-_].*\.md",
            r"TA[-_].*\.md",
            r".*ENTERPRISE.*ARCHITECTURE.*\.md",
            r".*SOLUTION.*ARCHITECTURE.*\.md",
            r".*TECHNICAL.*ARCHITECTURE.*\.md",
        ]

        potential_duplicates = []

        for root, _dirs, files in os.walk(docs_dir):
            # Skip archive directories. De map heet op schijf 'ARCHIEF';
            # de oude hoofdlettergevoelige check sloeg die niet over.
            if "archief" in root.lower() or "archive" in root.lower():
                continue

            # Skip the canonical architecture directory
            if str(self.ARCH_DIR) in root:
                continue

            for file in files:
                if not file.endswith(".md"):
                    continue

                onderzochte_bestanden += 1

                for pattern in duplicate_patterns:
                    if re.match(pattern, file, re.IGNORECASE):
                        potential_duplicates.append(os.path.join(root, file))
                        break

        # Discriminator: een lege scope mag deze node niet groen maken.
        assert onderzochte_bestanden > 0, f"Geen .md-bestanden gevonden in {docs_dir}"

        assert (
            len(potential_duplicates) == 0
        ), f"Found potential duplicate architecture docs outside archive: {potential_duplicates}"

    @pytest.mark.advisory
    def test_frontmatter_present_in_canonical_docs(self):
        """Test that canonical documents have proper frontmatter."""
        canonical_docs = [
            "ENTERPRISE_ARCHITECTURE.md",
            "SOLUTION_ARCHITECTURE.md",
            "TECHNICAL_ARCHITECTURE.md",
        ]

        for doc_name in canonical_docs:
            doc_path = self.ARCH_DIR / doc_name
            assert doc_path.exists(), f"Verplichte bron ontbreekt: {doc_path}"

            with open(doc_path, encoding="utf-8") as f:
                content = f.read()

            # Check for frontmatter
            assert content.startswith("---"), f"{doc_name} missing frontmatter"

            # Extract frontmatter
            parts = content.split("---", 2)
            if len(parts) >= 2:
                frontmatter = parts[1]

                # Check for required frontmatter fields (flexible format)
                assert (
                    "canonical:" in frontmatter
                ), f"{doc_name} missing canonical field in frontmatter"
                assert (
                    "status:" in frontmatter
                ), f"{doc_name} missing status in frontmatter"
                # Versie-informatie blijft optioneel (bestaande intentie). De
                # runtime pytest.skip die hier stond maakte de uitslag onzichtbaar
                # en is verwijderd zonder een nieuwe eis toe te voegen.


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
