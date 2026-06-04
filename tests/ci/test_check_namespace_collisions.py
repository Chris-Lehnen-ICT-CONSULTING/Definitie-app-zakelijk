#!/usr/bin/env python3
"""Regressie-vangnet voor scripts/ci/check_namespace_collisions.py — DEF-410.

Dekt alle parser-stages (parametrized) en de vier scope-gaten uit de DEF-409
5-agent review: formele tests (deze file), PEP 508 direct-URL, distribution↔
import mismatch, en -r/-c recursie.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "ci"
    / "check_namespace_collisions.py"
)
_SHIM = _SCRIPT.with_suffix(".sh")


def _load_module():
    spec = importlib.util.spec_from_file_location("check_namespace_collisions", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ns = _load_module()


# --------------------------------------------------------------------------- #
# Parser-stages (gap 1: formele tests + gap 2: PEP 508 direct-URL)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("line", "expected"),
    [
        # version specs
        ("requests==2.0", "requests"),
        ("pkg>=1.0", "pkg"),
        ("pkg~=1.0", "pkg"),
        # inline comment strippen
        ("Flask>=1.0  # web framework", "flask"),
        # env markers
        ('numpy; python_version >= "3.10"', "numpy"),
        # extras
        ("requests[security]>=2.0", "requests"),
        # naam-normalisatie (PEP 503)
        ("My.Pkg_Name==1.0", "my-pkg-name"),
        # editable install met #egg=
        ("-e git+https://github.com/x/y.git#egg=mypkg", "mypkg"),
        ("--editable git+https://github.com/x/y.git#egg=mypkg", "mypkg"),
        # GAP 2 — PEP 508 direct-URL syntax `name @ url`
        ("pkg @ git+https://github.com/foo/bar.git@ref", "pkg"),
        ("attacker @ https://evil.example/wheel.whl", "attacker"),
        # non-editable #egg= URL
        ("git+https://github.com/foo/bar.git#egg=urlpkg", "urlpkg"),
        # pip-optieregels → None
        ("--extra-index-url https://example.org/simple", None),
        ("-i https://example.org/simple", None),
        ("--hash=sha256:abc", None),
        # comments / lege / frontmatter → None
        ("# pure comment", None),
        ("---", None),
        ("", None),
        ("   ", None),
        # bare path / naamloze URL → None (niet statisch benoembaar)
        ("-e .", None),
        ("git+https://github.com/foo/bar.git", None),
        # gewone bare naam
        ("pillow", "pillow"),
    ],
)
def test_extract_distribution_name(line, expected):
    assert ns.extract_distribution_name(line) == expected


def test_canonical_normalisatie():
    assert ns.canonical("PyYAML") == "pyyaml"
    assert ns.canonical("beautifulsoup4") == "beautifulsoup4"
    assert ns.canonical("typing_extensions") == "typing-extensions"


# --------------------------------------------------------------------------- #
# GAP 4 — -r/-c recursie
# --------------------------------------------------------------------------- #
def test_recursie_volgt_r_include(tmp_path):
    base = tmp_path / "requirements.txt"
    nested = tmp_path / "nested.txt"
    base.write_text("requests==2.0\n-r nested.txt\n")
    nested.write_text("hidden-pkg==1.0\n")
    names = ns.collect_distributions([base])
    assert "requests" in names
    assert "hidden-pkg" in names


def test_recursie_volgt_c_constraint(tmp_path):
    base = tmp_path / "requirements.txt"
    constraints = tmp_path / "constraints.txt"
    base.write_text("-c constraints.txt\n")
    constraints.write_text("constrained-pkg==1.0\n")
    assert "constrained-pkg" in ns.collect_distributions([base])


def test_recursie_cycle_guard(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("apkg==1.0\n-r b.txt\n")
    b.write_text("bpkg==1.0\n-r a.txt\n")
    # Mag niet oneindig recurseren.
    names = ns.collect_distributions([a])
    assert {"apkg", "bpkg"} <= names


# --------------------------------------------------------------------------- #
# GAP 3 — distribution↔import name mismatch
# --------------------------------------------------------------------------- #
def test_import_names_for_gebruikt_metadata_map():
    dist_map = {"pyyaml": {"yaml"}}
    assert ns.import_names_for("pyyaml", dist_map) == {"yaml"}


def test_import_names_for_fallback_bij_niet_geinstalleerd():
    # Niet in de map → fallback canoniek-met-underscores.
    assert ns.import_names_for("foo-bar", {}) == {"foo_bar"}


def test_collision_via_import_name_mismatch(tmp_path):
    # src/yaml botst met distributie PyYAML (import-naam yaml), ook al verschilt
    # de distributienaam. Injecteer een deterministische map (gap 3).
    src = tmp_path / "src"
    (src / "yaml").mkdir(parents=True)
    req = tmp_path / "requirements.txt"
    req.write_text("PyYAML==6.0\n")
    collisions = ns.find_collisions([req], src, dist_map={"pyyaml": {"yaml"}})
    assert collisions == {"yaml": "pyyaml"}


def test_metadata_map_mapt_pyyaml_naar_yaml_indien_geinstalleerd():
    # Integratie-check: als PyYAML in de omgeving zit, levert de echte map yaml.
    real = ns.build_distribution_import_map()
    if "pyyaml" in real:
        assert "yaml" in real["pyyaml"]
    else:
        pytest.skip("PyYAML niet geïnstalleerd in deze omgeving")


# --------------------------------------------------------------------------- #
# find_collisions — positief / negatief
# --------------------------------------------------------------------------- #
def _make_src(tmp_path, *dirs):
    src = tmp_path / "src"
    for d in dirs:
        (src / d).mkdir(parents=True)
    return src


def test_geen_collision(tmp_path):
    src = _make_src(tmp_path, "domain", "services")
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.0\nnumpy==2.0\n")
    assert ns.find_collisions([req], src, dist_map={}) == {}


def test_positieve_collision_fallback_import(tmp_path):
    src = _make_src(tmp_path, "domain", "uniquepkg")
    req = tmp_path / "requirements.txt"
    req.write_text("uniquepkg==1.0\n")
    # Lege map → fallback import-naam == 'uniquepkg' → botst met src/uniquepkg.
    assert ns.find_collisions([req], src, dist_map={}) == {"uniquepkg": "uniquepkg"}


def test_collect_src_top_levels_negeert_ruis(tmp_path):
    src = tmp_path / "src"
    (src / "domain").mkdir(parents=True)
    (src / "__pycache__").mkdir()
    (src / ".hidden").mkdir()
    (src / "pkg.egg-info").mkdir()
    (src / "main.py").write_text("x = 1\n")
    assert ns.collect_src_top_levels(src) == {"domain"}


# --------------------------------------------------------------------------- #
# main() — exit codes
# --------------------------------------------------------------------------- #
def _run_main(tmp_path, src_dirs, req_text):
    src = _make_src(tmp_path, *src_dirs)
    req = tmp_path / "requirements.txt"
    req.write_text(req_text)
    return ns.main(["--src", str(src), "--requirement", str(req)])


def test_main_exit0_geen_collision(tmp_path):
    assert _run_main(tmp_path, ["domain"], "requests==2.0\n") == 0


def test_main_exit1_collision(tmp_path):
    assert _run_main(tmp_path, ["domain", "uniquepkg"], "uniquepkg==1.0\n") == 1


def test_main_exit0_lege_requirements(tmp_path):
    assert _run_main(tmp_path, ["domain"], "# alleen comments\n\n") == 0


def test_main_exit1_missende_src(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.0\n")
    rc = ns.main(["--src", str(tmp_path / "nope"), "--requirement", str(req)])
    assert rc == 1


def test_main_exit1_lege_src(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.0\n")
    assert ns.main(["--src", str(src), "--requirement", str(req)]) == 1


# --------------------------------------------------------------------------- #
# Shim — entrypoint blijft stabiel en delegeert naar de Python-rewrite
# --------------------------------------------------------------------------- #
def _run_shim(src, req):
    # Forceer dezelfde interpreter als de testrunner (heeft `packaging`).
    env = {**os.environ, "PYTHON": sys.executable}
    return subprocess.run(
        ["bash", str(_SHIM), "--src", str(src), "--requirement", str(req)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash niet beschikbaar")
def test_shim_delegeert_en_detecteert_collision(tmp_path):
    src = _make_src(tmp_path, "domain", "uniquepkg")
    req = tmp_path / "requirements.txt"
    req.write_text("uniquepkg==1.0\n")
    result = _run_shim(src, req)
    assert result.returncode == 1
    assert "DEPENDENCY-CONFUSION" in result.stderr


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash niet beschikbaar")
def test_shim_exit0_geen_collision(tmp_path):
    src = _make_src(tmp_path, "domain")
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.0\n")
    result = _run_shim(src, req)
    assert result.returncode == 0, result.stderr
