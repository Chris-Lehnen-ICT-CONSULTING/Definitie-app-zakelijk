#!/usr/bin/env python3
"""
Pre-commit hook om te controleren of documenten op de juiste locatie staan.
Voorkomt het committen van bestanden in verkeerde mappen.
"""

import os
import sys
from pathlib import Path

# Define allowed locations for different file types
ALLOWED_LOCATIONS = {
    # Python scripts
    ".py": ["src/", "tests/", "scripts/", "tools/", "setup.py", "manage.py"],
    # Markdown docs
    ".md": [
        "docs/",
        "archive/",
        # Root exceptions
        "README.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "LICENSE.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "CLAUDE.md",  # Claude Code project instructions
    ],
    # Reports
    ".json": [
        "src/",
        "tests/",
        "scripts/",
        "config/",
        "reports/",
        ".github/",
        "data/",
        "docs/",  # Toegevoegd voor architectuur JSON bestanden
        "package.json",
        "tsconfig.json",
    ],
    ".html": ["reports/", "docs/", "templates/", "static/"],
}

# Files that should NOT be in root (except specific exceptions)
FORBIDDEN_ROOT_PATTERNS = [
    "*_report.json",
    "*_analysis.json",
    "*_report.md",
    "*_analysis.md",
    "*_summary.md",
    "*_test_*.md",
    "test_*.py",
    "*_test.py",
    "*.html",
]


def check_file_location(filepath):
    """Check if file is in an allowed location."""
    path = Path(filepath)
    extension = path.suffix

    # Skip .bmad-core bestanden
    if str(path).startswith(".bmad-core/"):
        return True, ""

    # Skip alle dotfile directories
    if str(path).startswith("."):
        return True, ""

    # README.md bestanden zijn overal toegestaan
    if path.name == "README.md":
        return True, ""

    # Skip data directory bestanden (zoals definities.db)
    if str(path).startswith("data/"):
        return True, ""

    # Skip archive/archief directories
    if (
        str(path).startswith("archive/")
        or str(path).startswith("archief/")
        or "/archief/" in str(path)
        or "/_archive/" in str(path)
    ):
        return True, ""

    # Skip if no extension rules defined
    if extension not in ALLOWED_LOCATIONS:
        return True, ""

    # Check allowed locations
    allowed = ALLOWED_LOCATIONS[extension]

    # Check if file matches any allowed pattern
    for allowed_path in allowed:
        if allowed_path.endswith("/"):
            # Directory check
            if str(path).startswith(allowed_path):
                return True, ""
        elif str(path) == allowed_path:
            return True, ""

    # Special check for root directory files
    if "/" not in str(path):
        # Allow explicit root exceptions
        if path.name == "validation-status.json":
            return True, ""
        # Check if it matches forbidden patterns
        import fnmatch

        for pattern in FORBIDDEN_ROOT_PATTERNS:
            if fnmatch.fnmatch(path.name, pattern):
                suggestion = get_suggested_location(path)
                return (
                    False,
                    f"File '{filepath}' matches forbidden pattern '{pattern}' and should not be in root directory. Suggested location: {suggestion}",
                )

        suggestion = get_suggested_location(path)
        return (
            False,
            f"File '{filepath}' should not be in root directory. Suggested location: {suggestion}",
        )

    return (
        False,
        f"File '{filepath}' is not in an allowed location for {extension} files",
    )


def get_suggested_location(path):
    """Stel correcte locatie voor voor verkeerd geplaatst bestand."""
    filename = path.name
    extension = path.suffix

    # Python test bestanden
    if filename.startswith("test_") or filename.endswith("_test.py"):
        return "tests/"

    # Analyse scripts
    if "analyze" in filename or "analysis" in filename:
        return "scripts/analysis/"

    # Reports
    if "report" in filename and extension == ".json":
        return "reports/analysis/"

    # HTML bestanden
    if extension == ".html":
        return "reports/visualizations/"

    # Documentatie
    if extension == ".md":
        if "workflow" in filename.lower():
            return "docs/workflows/"
        if "architecture" in filename.lower() or "architectuur" in filename.lower():
            return "docs/architectuur/"
        if any(
            word in filename.lower()
            for word in [
                "test",
                "report",
                "rapport",
                "summary",
                "samenvatting",
                "analysis",
                "analyse",
            ]
        ):
            return "reports/analysis/"
        if "review" in filename.lower():
            return "docs/reviews/"
        return "docs/"

    # Algemene Python scripts
    if extension == ".py":
        return "scripts/"

    return "geschikte submap"


def main():
    """Hoofd pre-commit hook logica."""
    # Krijg lijst van staged bestanden
    files = sys.argv[1:]

    errors = []
    for filepath in files:
        # Sla verwijderde bestanden over
        if not os.path.exists(filepath):
            continue

        valid, message = check_file_location(filepath)
        if not valid:
            errors.append(message)

    if errors:
        print("❌ Document locatie fouten gevonden:\n")
        for error in errors:
            print(f"  - {error}")
        print("\nVerplaats bestanden naar de juiste locaties voor het committen.")
        print(
            "Voer uit: ./scripts/migrate-documents.sh --dry-run om voorgestelde verplaatsingen te zien"
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
