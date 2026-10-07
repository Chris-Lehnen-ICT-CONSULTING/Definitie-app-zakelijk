"""DEF-835 modelproef — mutatiematrix buiten de werkboom.

Per mutatie: kopie van runner en testbestand naar een tijdelijke map, één
naïeve tekstmutatie in de runner, testbestand wijst naar de kopie. Verwacht:
elke mutatie laat minstens één test falen. De werkboom wordt niet gewijzigd.
Gebruik: <venv-python> modelproef-mutatie-v1.py <werkboom>
"""

import subprocess
import sys
import tempfile
from pathlib import Path

WERKBOOM = Path(sys.argv[1]).resolve()
RUNNER = WERKBOOM / "scripts/analysis/def835_int02_modelproef.py"
TESTS = WERKBOOM / "tests/unit/validation/test_def835_int02_modelproef.py"
PY = sys.executable

MUTATIES = {
    "M1-logs-niet-stil": ("lg.disabled = True", "lg.disabled = False"),
    "M2-telling-pas-na-succes": (
        "        self.inferenties += 1  # telt vóór verzending: ook een mislukte call\n",
        "",
    ),
    "M3-geen-servicetiercontrole": (
        '            or usage.get("service_tier") != "standard"\n',
        "",
    ),
    "M4-geen-identiteitscontrole": (
        'raise ProefGeweigerd("identiteit_gewijzigd")',
        "pass",
    ),
    "M5-akkoord-truthy": ("akkoord[k] is True", "bool(akkoord[k])"),
    "M6-geen-tellimiet": (
        "if self.telverzoeken >= self.limieten.max_telverzoeken:",
        "if False:",
    ),
    "M7-geen-cachecontrole": (
        'and not _bevat_sleutel(payload, "cache_control")',
        "and True",
    ),
    "M8-geen-hashbinding-transport": (
        'self._stop("payload_hash_mismatch")',
        "pass",
    ),
}

bron = RUNNER.read_text("utf-8")
testbron = TESTS.read_text("utf-8")
uitslagen = []
for naam, (oud, nieuw) in MUTATIES.items():
    assert bron.count(oud) == 1, (naam, bron.count(oud))
    with tempfile.TemporaryDirectory(prefix="def835-mutatie-") as tmp:
        runner = Path(tmp) / "runner.py"
        runner.write_text(
            bron.replace(oud, nieuw).replace(
                "REPO = Path(__file__).resolve().parents[2]",
                f"REPO = Path({str(WERKBOOM)!r})",
            ),
            "utf-8",
        )
        test = Path(tmp) / "test_mutant.py"
        test.write_text(
            testbron.replace(
                'SCRIPT = ROOT / "scripts" / "analysis" / "def835_int02_modelproef.py"',
                f"SCRIPT = Path({str(runner)!r})",
            ).replace(
                "ROOT = Path(__file__).resolve().parents[3]",
                f"ROOT = Path({str(WERKBOOM)!r})",
            ),
            "utf-8",
        )
        proces = subprocess.run(
            [PY, "-m", "pytest", str(test), "-p", "no:cacheprovider", "-q",
             "--tb=no", "-c", str(WERKBOOM / "pytest.ini"),
             "--rootdir", str(WERKBOOM)],
            cwd=WERKBOOM, capture_output=True, text=True, check=False,
        )
        regel = proces.stdout.strip().splitlines()[-1] if proces.stdout else ""
        gedood = proces.returncode != 0
        uitslagen.append(gedood)
        print(f"{naam}: exit={proces.returncode} {'GEDOOD' if gedood else 'OVERLEEFT'} | {regel}")
print(f"gedood {sum(uitslagen)}/{len(uitslagen)}")
sys.exit(0 if all(uitslagen) else 1)
