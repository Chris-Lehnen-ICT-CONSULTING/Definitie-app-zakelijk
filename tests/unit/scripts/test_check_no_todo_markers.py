"""Tests voor de TODO-marker CI-gate (DEF-459).

Borgt dat de gate docstring/string-TODO's in src/ vangt zonder false positives
op legitieme lowercase status-waarden of placeholders.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

# De gate vereist ripgrep; zonder rg exit het script met code 2. Sommige
# test-runners (bv. de CI unit-job) hebben rg niet geïnstalleerd — skip daar.
pytestmark = [
    pytest.mark.unit,
    pytest.mark.skipif(
        shutil.which("rg") is None, reason="ripgrep (rg) niet geïnstalleerd"
    ),
]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "ci" / "check_no_todo_markers.sh"


def _run(*targets: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(_SCRIPT), *[str(t) for t in targets]],
        capture_output=True,
        text=True,
        check=False,
    )


def test_docstring_todo_wordt_gedetecteerd(tmp_path):
    (tmp_path / "mod.py").write_text(
        '"""Module.\n\nTODO: implementeer dit later.\n"""\n'
    )
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "TODO" in (result.stdout + result.stderr)


def test_string_fixme_wordt_gedetecteerd(tmp_path):
    (tmp_path / "mod.py").write_text('MESSAGE = "FIXME: broken parsing"\n')
    result = _run(tmp_path)
    assert result.returncode == 1


def test_schone_file_slaagt(tmp_path):
    (tmp_path / "mod.py").write_text(
        '"""Nette module."""\n\n\ndef f():\n    return 1\n'
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_lowercase_todo_status_geen_false_positive(tmp_path):
    # 'todo' als lowercase statuswaarde mag NIET falen (case-sensitive marker).
    (tmp_path / "mod.py").write_text('STATUS = {"status": "todo"}\n')
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_xxx_placeholder_geen_false_positive(tmp_path):
    # US-XXX/BUG-XXX-achtige placeholders mogen de string-pass niet triggeren.
    (tmp_path / "mod.py").write_text('PATTERN = "US-XXX en BUG-XXX"\n')
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_productie_scope_repo_is_schoon():
    # Zonder args draait de echte productie-scope (src string-pass + comment-pass).
    # De huidige repo moet groen zijn, anders breekt de gate CI voor iedereen.
    result = subprocess.run(
        ["bash", str(_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
