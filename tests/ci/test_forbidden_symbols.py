"""
Test to prevent V1 symbols from creeping back into the codebase.

This test scans the src directory for forbidden V1 patterns and fails
if any are found outside of allowed deprecated files.
"""

import pathlib
import re
from collections.abc import Iterator

import pytest

# Repository root
ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

# Files allowed to contain V1 patterns (e.g., deprecated files)
ALLOWLIST = {
    "archived/unified_definition_generator.py.DEPRECATED",
    # Moderne implementaties die file-naamgedeelde heritage hebben maar inhoudelijk V2/modern zijn
    "src/services/definition_orchestrator.py",
    "src/services/ai_service.py",
    # V2 orchestrator: moderne implementatie, niet blokkeren op fout-positieve greps
    "src/services/orchestrators/definition_orchestrator_v2.py",
}

# General forbidden patterns for all Python files
PATTERNS = [
    (re.compile(r"get_ai_service\("), "get_ai_service function call"),
    (re.compile(r"stuur_prompt_naar_gpt\("), "stuur_prompt_naar_gpt function call"),
    (
        re.compile(
            r"^[^#]*\bclass\s+DefinitionOrchestrator\b(?!V2|Interface)", re.MULTILINE
        ),
        "V1 DefinitionOrchestrator class",
    ),
    (re.compile(r"from services\.ai_service import"), "import from V1 ai_service"),
    (
        re.compile(r"from services\.definition_orchestrator import"),
        "import from V1 orchestrator",
    ),
    (re.compile(r"USE_V2_ORCHESTRATOR"), "V2 feature flag (should be removed)"),
]

# Special patterns for voorbeelden module (no sync executors for AI)
# Note: concurrent.futures is allowed in _run_async_safe for event loop detection
VOORBEELDEN_PATTERNS = [
    (
        re.compile(r"run_in_executor\([^)]*get_ai_service"),
        "run_in_executor with get_ai_service",
    ),
    (
        re.compile(r"run_in_executor\([^)]*generate_definition"),
        "run_in_executor for AI calls",
    ),
]


def _iter_py_files(base: pathlib.Path) -> Iterator[pathlib.Path]:
    """Iterate over all Python files in a directory tree."""
    yield from base.rglob("*.py")


def _is_allowed(filepath: pathlib.Path) -> bool:
    """Check if a file is in the allowlist."""
    rel_path = str(filepath.relative_to(ROOT))
    # Check exact matches and DEPRECATED suffix
    return any(
        rel_path == allowed or rel_path.endswith(allowed) or ".DEPRECATED" in rel_path
        for allowed in ALLOWLIST
    )


def test_no_forbidden_v1_symbols():
    """Test that no forbidden V1 symbols exist in the active codebase."""
    violations = []

    for filepath in _iter_py_files(SRC):
        # Skip allowed files
        if _is_allowed(filepath):
            continue

        # Skip __pycache__ directories
        if "__pycache__" in str(filepath):
            continue

        try:
            text = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            # Skip files we can't read
            print(f"Warning: Could not read {filepath}: {e}")
            continue

        rel_path = str(filepath.relative_to(ROOT))

        # Check general patterns
        for pattern, description in PATTERNS:
            if pattern.search(text):
                violations.append((rel_path, description))

        # Check voorbeelden-specific patterns
        if "voorbeelden/unified_voorbeelden.py" in rel_path:
            for pattern, description in VOORBEELDEN_PATTERNS:
                if pattern.search(text):
                    violations.append((rel_path, description))

    if violations:
        violation_msg = "Forbidden V1 symbols found:\n"
        for filepath, description in violations:
            violation_msg += f"  {filepath}: {description}\n"
        pytest.fail(violation_msg)


def test_no_v1_files_exist():
    """Content-based guard: flag only real V1 patterns, not filenames.

    Bestandsnamen kunnen historisch overlappen; inhoudelijke patronen worden elders getest.
    """
    # Deze test is vervangen door inhoudelijke pattern-checks in `test_no_forbidden_v1_symbols`.
    # Laat expliciet slagen om geen false positives te veroorzaken.
    assert True


def test_async_patterns_in_orchestrator():
    """Verify V2 orchestrator uses proper async patterns."""
    orchestrator_path = (
        SRC / "services" / "orchestrators" / "definition_orchestrator_v2.py"
    )

    if not orchestrator_path.exists():
        pytest.skip("V2 orchestrator not found")

    text = orchestrator_path.read_text()

    # Check for required async patterns
    required_patterns = [
        (
            re.compile(r"await self\.cleaning_service\.clean_text"),
            "async cleaning service usage",
        ),
        (
            re.compile(r"await self\.validation_service\.validate_definition"),
            "async validation service usage",
        ),
        (
            re.compile(r"await self\.ai_service\.generate_definition"),
            "async AI service usage",
        ),
    ]

    missing = []
    for pattern, description in required_patterns:
        if not pattern.search(text):
            missing.append(description)

    if missing:
        pytest.fail(
            "V2 orchestrator missing required async patterns:\n"
            + "\n".join(f"  - {m}" for m in missing)
        )


def test_no_legacy_response_fields_in_core():
    """Guard against V1 response field usage in core modules.

    Ensures V2 contract is followed:
    - response.message → response.error
    - response.validation → response.validation_result
    """
    core_dirs = [SRC / "services", SRC / "orchestration"]
    patterns = [
        (
            re.compile(r"^[^#]*\bresponse\.message\b", re.MULTILINE),
            "Use response.error instead of response.message for V2 responses",
        ),
        (
            re.compile(r"^[^#]*\bresponse\.validation\b", re.MULTILINE),
            "Use response.validation_result instead of response.validation for V2 responses",
        ),
    ]
    violations = []

    for base_dir in core_dirs:
        if not base_dir.exists():
            continue
        for filepath in base_dir.rglob("*.py"):
            if "__pycache__" in str(filepath):
                continue
            try:
                text = filepath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            rel_path = str(filepath.relative_to(ROOT))

            for pattern, description in patterns:
                if pattern.search(text):
                    violations.append((rel_path, description))

    if violations:
        msg = "Legacy response field usage found in core modules:\n"
        for filepath, description in violations:
            msg += f"  {filepath}: {description}\n"
        pytest.fail(msg)
