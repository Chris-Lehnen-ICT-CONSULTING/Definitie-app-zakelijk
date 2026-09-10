"""DEF-563: echte CLI-proeven op dummybron, zonder app-imports of pytest."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("timing_assert_ratchet.py")
SOURCE = """import time
LIMIT = 1
def test_work():
    start = time.perf_counter()
    t = time.perf_counter() - start
    rate = 100 / t
    assert (t < LIMIT and rate > 10)
"""


class TimingRatchetTests(unittest.TestCase):
    def setUp(self):
        # Bewijsfixtures blijven staan; geen cleanup van bestaande bestanden.
        self.root = Path(tempfile.mkdtemp(prefix="def563-ratchet-test-"))
        (self.root / "tests").mkdir()

    def run_gate(self, *args):
        assert SCRIPT.is_file(), "De timing-inventarischecker ontbreekt"
        return subprocess.run(
            [sys.executable, "-I", "-B", str(SCRIPT), str(self.root), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    def write_source(self, source=SOURCE, name="test_dummy.py"):
        (self.root / "tests" / name).write_text(source, encoding="utf-8")

    def inventory(self):
        result = self.run_gate("--inventory")
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    def baseline(self, inventory):
        entries = {
            key: {**value, "status": "unreviewed", "reason": "Bestaande schuld"}
            for key, value in inventory["entries"].items()
        }
        path = self.root / "baseline.json"
        path.write_text(
            json.dumps({"schema": 1, "source_commit": "a" * 40, "entries": entries}),
            encoding="utf-8",
        )
        return str(path)

    def test_tracks_clock_alias_arithmetic_and_symbolic_boolean_bounds(self):
        self.write_source(
            SOURCE.replace("import time", "import time as timer").replace(
                "time.", "timer."
            )
        )
        entries = self.inventory()["entries"]
        assert len(entries) == 1
        entry = entries["tests/test_dummy.py::test_work"]
        assert entry["comparisons"] == ["t < LIMIT", "rate > 10"]

    def test_hit_rate_memory_and_assertion_message_are_not_timing(self):
        self.write_source("""def test_ratios():
    assert stats["hit_rate"] > 0.9
    assert memory_growth < 100
    assert value > 0, "duration too short"
    assert config.timeout_seconds == 60
    assert result.duration_ms is not None
""")
        assert self.inventory()["entries"] == {}

    def test_mocked_clock_and_reversed_bounds_remain_review_candidates(self):
        self.write_source("""@patch("time.perf_counter")
def test_timer(clock):
    clock.side_effect = [1.0, 1.05]
    assert 40 < first_time < 60
""")
        entry = next(iter(self.inventory()["entries"].values()))
        assert entry["comparisons"] == ["40 < first_time < 60"]

    def test_equal_count_replacement_is_not_accepted(self):
        self.write_source()
        baseline = self.baseline(self.inventory())
        assert self.run_gate("--baseline", baseline).returncode == 0
        self.write_source(SOURCE.replace("t < LIMIT", "t < 200"))
        result = self.run_gate("--baseline", baseline)
        assert result.returncode == 1, result.stderr

    def test_deleted_assertion_or_changed_external_limit_requires_review(self):
        self.write_source()
        baseline = self.baseline(self.inventory())
        for source in [
            SOURCE.replace("LIMIT = 1", "LIMIT = 200"),
            "def test_work():\n    assert True\n",
        ]:
            with self.subTest(source=source):
                self.write_source(source)
                assert self.run_gate("--baseline", baseline).returncode == 1

    def test_new_candidate_cannot_hide_behind_lower_count(self):
        self.write_source()
        baseline = self.baseline(self.inventory())
        self.write_source("def test_work():\n    assert True\n")
        self.write_source("def test_new():\n    assert elapsed < 1\n", "test_new.py")
        assert self.run_gate("--baseline", baseline).returncode == 1

    def test_whitespace_comments_do_not_invalidate_review(self):
        self.write_source()
        baseline = self.baseline(self.inventory())
        self.write_source("# comment\n\n" + SOURCE)
        assert self.run_gate("--baseline", baseline).returncode == 0

    def test_empty_scope_parse_error_and_missing_baseline_fail_closed(self):
        assert self.run_gate("--inventory").returncode == 2
        self.write_source("def broken(:\n")
        assert self.run_gate("--inventory").returncode == 2
        self.write_source()
        assert self.run_gate().returncode == 2

    def test_symlink_is_not_read(self):
        (self.root / "tests" / "test_external.py").symlink_to(self.root / "absent.py")
        assert self.run_gate("--inventory").returncode == 2

    def test_nested_scopes_are_distinct_without_executing_source(self):
        self.write_source("""from time import perf_counter as clock
raise RuntimeError("Tests mogen niet worden uitgevoerd")
class TestOne:
    def test_same(self):
        start = clock()
        z = clock() - start
        assert z < 1
if True:
    class TestTwo:
        def test_same(self):
            assert elapsed < 2
""")
        assert set(self.inventory()["entries"]) == {
            "tests/test_dummy.py::TestOne::test_same",
            "tests/test_dummy.py::TestTwo::test_same",
        }

    def test_invalid_status_empty_reason_and_duplicate_json_keys_fail(self):
        self.write_source()
        inventory = self.inventory()
        baseline = Path(self.baseline(inventory))
        original = json.loads(baseline.read_text())
        key = next(iter(original["entries"]))
        for field, value in [
            ("status", "approved-whatever"),
            ("status", []),
            ("reason", ""),
        ]:
            data = json.loads(json.dumps(original))
            data["entries"][key][field] = value
            baseline.write_text(json.dumps(data))
            assert self.run_gate("--baseline", str(baseline)).returncode == 2
        baseline.write_text('{"schema": 1, "schema": 1, "entries": {}}')
        assert self.run_gate("--baseline", str(baseline)).returncode == 2


if __name__ == "__main__":
    unittest.main()
