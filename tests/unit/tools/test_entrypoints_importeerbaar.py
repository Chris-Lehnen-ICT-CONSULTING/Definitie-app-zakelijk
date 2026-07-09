"""Elk entrypoint moet importeerbaar zijn (DEF-579).

`src/tools/definitie_manager.py` en `src/tools/setup_database.py` importeerden
`generation.definitie_generator`, een package dat bij de restructure van
2025-08-15 (commit 2d4e3dd8) is verdwenen. Beide CLI's waren daardoor bijna een
jaar onuitvoerbaar zonder dat iets faalde: er was geen test die ze aanraakte.

Deze guard importeert elk entrypoint in een schoon subprocess. Een gebroken
import (verplaatste module, typefout) faalt nu meteen.
"""

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_REPO = Path(__file__).resolve().parents[3]
_SRC = _REPO / "src"

# Module-paden van de entrypoints. Streamlit-pagina's staan er bewust NIET bij:
# die roepen `st.set_page_config()` op module-niveau aan en klappen buiten een
# Streamlit-runtime. Hun import wordt gedekt door de app-smoke.
_ENTRYPOINT_MODULES = [
    "api.feature_status_api",
    "cli.performance_cli",
    "database.migrate_database",
    "tools.definitie_manager",
    "tools.rag_smoke_test",
    "tools.setup_database",
]


def test_er_zijn_entrypoint_modules():
    assert len(_ENTRYPOINT_MODULES) >= 6


@pytest.mark.parametrize("module", _ENTRYPOINT_MODULES)
def test_entrypoint_is_importeerbaar(module):
    """Importeer in een subprocess: entrypoints hebben import-side-effects
    (logging-bootstrap) die de testrun niet horen te beïnvloeden."""
    resultaat = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        cwd=_REPO,
        env={"PYTHONPATH": str(_SRC), "PATH": ""},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert resultaat.returncode == 0, (
        f"{module} is niet importeerbaar — de CLI is onuitvoerbaar:\n"
        f"{resultaat.stderr[-800:]}"
    )
