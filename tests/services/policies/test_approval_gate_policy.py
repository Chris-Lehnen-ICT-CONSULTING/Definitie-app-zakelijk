import os
import time as _time
import types

import pytest

from services.policies.approval_gate_policy import (DEFAULT_POLICY,
                                                    GatePolicyService)


class _StubYAML:
    def __init__(
        self, base_path: str, overlay_path: str, base_data: dict, overlay_data: dict
    ):
        self._base_path = base_path
        self._overlay_path = overlay_path
        self._base_data = base_data
        self._overlay_data = overlay_data

    def safe_load(self, f):
        # Choose dataset by file name
        name = getattr(f, "name", "")
        if os.path.abspath(name) == os.path.abspath(self._base_path):
            return self._base_data
        if os.path.abspath(name) == os.path.abspath(self._overlay_path):
            return self._overlay_data
        return {}


def test_policy_merge_and_ttl(monkeypatch, tmp_path):
    base = tmp_path / "approval_gate.yaml"
    overlay = tmp_path / "overlay.yaml"
    base.write_text("ignored-content", encoding="utf-8")
    overlay.write_text("ignored-content", encoding="utf-8")

    # Prepare fake yaml loader returning dicts based on file name
    base_data = {"thresholds": {"hard_min_score": 0.9}}
    overlay_data = {
        "soft_requirements": {"missing_wettelijke_basis_soft": False},
        "cache": {"ttl_seconds": 1},
    }

    stub_yaml = _StubYAML(str(base), str(overlay), base_data, overlay_data)

    # Patch yaml import helper
    monkeypatch.setattr(
        "services.policies.approval_gate_policy._safe_import_yaml",
        lambda: stub_yaml,
    )

    # Pretend files exist
    monkeypatch.setenv("APPROVAL_GATE_CONFIG_OVERLAY", str(overlay))

    svc = GatePolicyService(base_path=str(base))

    # Control time for TTL
    t = [1000.0]

    def fake_time():
        return t[0]

    monkeypatch.setattr("time.time", fake_time)

    # First load
    p1 = svc.get_policy()
    assert p1.hard_min_score == 0.9  # from base
    assert (
        p1.soft_requirements.get("missing_wettelijke_basis_soft") is False
    )  # from overlay
    assert p1.ttl_seconds == 1

    # Within TTL → cached object
    t[0] += 0.5
    p2 = svc.get_policy()
    assert p2 is p1

    # After TTL → reload (new object)
    t[0] += 5
    p3 = svc.get_policy()
    assert p3 is not p1


def test_policy_defaults_when_missing_yaml(monkeypatch, tmp_path):
    # Patch yaml to empty loader and os.path.exists to False
    monkeypatch.setattr(
        "services.policies.approval_gate_policy._safe_import_yaml",
        lambda: types.SimpleNamespace(safe_load=lambda f: {}),
    )

    # Non-existing base path
    base_path = tmp_path / "does_not_exist.yaml"
    svc = GatePolicyService(base_path=str(base_path))

    policy = svc.get_policy()
    # Verify we fall back to DEFAULT_POLICY values
    assert policy.hard_min_score == DEFAULT_POLICY["thresholds"]["hard_min_score"]
    assert policy.soft_min_score == DEFAULT_POLICY["thresholds"]["soft_min_score"]
    assert policy.hard_requirements["min_one_context_required"] is True
