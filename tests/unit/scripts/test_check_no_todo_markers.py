"""Tests voor de TODO-marker CI-gate (DEF-459, DEF-735).

Borgt dat de gate docstring/string-TODO's in src/ vangt zonder false positives
op legitieme lowercase status-waarden of placeholders (DEF-459), en dat elk
meegegeven argument als pad wordt gelezen — nooit als ripgrep-optie (DEF-735).
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# De gate vereist ripgrep; zonder rg exit het script met code 2. Sommige
# test-runners (bv. de CI unit-job) hebben rg niet geïnstalleerd — skip daar.
# De guard staat per test i.p.v. modulebreed, zodat de argv-grenstests met de
# fake rg-provider óók draaien op runners zonder ripgrep.
_requires_rg = pytest.mark.skipif(
    shutil.which("rg") is None, reason="ripgrep (rg) niet geïnstalleerd"
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "ci" / "check_no_todo_markers.sh"


def _run(*targets: Path | str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(_SCRIPT), *[str(t) for t in targets]],
        capture_output=True,
        text=True,
        check=False,
        cwd=None if cwd is None else str(cwd),
    )


@_requires_rg
def test_docstring_todo_wordt_gedetecteerd(tmp_path):
    (tmp_path / "mod.py").write_text(
        '"""Module.\n\nTODO: implementeer dit later.\n"""\n'
    )
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "TODO" in (result.stdout + result.stderr)


@_requires_rg
def test_string_fixme_wordt_gedetecteerd(tmp_path):
    (tmp_path / "mod.py").write_text('MESSAGE = "FIXME: broken parsing"\n')
    result = _run(tmp_path)
    assert result.returncode == 1


@_requires_rg
def test_schone_file_slaagt(tmp_path):
    (tmp_path / "mod.py").write_text(
        '"""Nette module."""\n\n\ndef f():\n    return 1\n'
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


@_requires_rg
def test_lowercase_todo_status_geen_false_positive(tmp_path):
    # 'todo' als lowercase statuswaarde mag NIET falen (case-sensitive marker).
    (tmp_path / "mod.py").write_text('STATUS = {"status": "todo"}\n')
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


@_requires_rg
def test_xxx_placeholder_geen_false_positive(tmp_path):
    # US-XXX/BUG-XXX-achtige placeholders mogen de string-pass niet triggeren.
    (tmp_path / "mod.py").write_text('PATTERN = "US-XXX en BUG-XXX"\n')
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


@_requires_rg
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


# --- DEF-735: argv-grens tussen opties en targets ---------------------------

# Fake rg-provider. Legt uitsluitend de eigen argumenten vast en geeft een
# vooraf ingestelde status/uitvoer terug: geen bestandssysteem-scan, geen
# env-dump, geen secrets. Hierdoor draait het argv-contract ook op runners
# zonder ripgrep.
_FAKE_RG_SOURCE = r"""#!/usr/bin/env bash
set -u

{
  printf 'INVOCATION\n'
  for arg in "$@"; do
    printf 'ARG\t%s\n' "$arg"
  done
} >>"$FAKE_RG_LOG"

# De gate gebruikt `rg -v` als lege-regelfilter op stdin; die aanroep hoort
# niet bij de scan-passes en wordt hier functioneel nagebootst.
if [ "${1:-}" = "-v" ]; then
  status=1
  while IFS= read -r line; do
    if [ -n "${line//[[:space:]]/}" ]; then
      printf '%s\n' "$line"
      status=0
    fi
  done
  exit "$status"
fi

count_file="$FAKE_RG_LOG.count"
n=$(cat "$count_file" 2>/dev/null || printf '0')
n=$((n + 1))
printf '%s' "$n" >"$count_file"

out_var="FAKE_RG_OUT_$n"
status_var="FAKE_RG_STATUS_$n"
if [ -n "${!out_var:-}" ]; then
  printf '%s\n' "${!out_var}"
fi
exit "${!status_var:-1}"
"""


class _FakeRg:
    """Draait de gate met een fake `rg` vooraan op PATH en leest het argv-log."""

    def __init__(self, bindir: Path, log: Path) -> None:
        self._bindir = bindir
        self._log = log

    def run(
        self,
        *targets: Path | str,
        statuses: tuple[int, ...] = (1, 1),
        outputs: tuple[str, ...] = ("", ""),
    ) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PATH"] = f"{self._bindir}{os.pathsep}{env['PATH']}"
        env["FAKE_RG_LOG"] = str(self._log)
        gekoppeld = zip(statuses, outputs, strict=True)
        for index, (status, output) in enumerate(gekoppeld, start=1):
            env[f"FAKE_RG_STATUS_{index}"] = str(status)
            env[f"FAKE_RG_OUT_{index}"] = output
        return subprocess.run(
            ["bash", str(_SCRIPT), *[str(t) for t in targets]],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    @property
    def scans(self) -> list[list[str]]:
        """Argv per scan-pass, in aanroepvolgorde (de `rg -v`-filter valt af)."""
        invocaties: list[list[str]] = []
        for regel in self._log.read_text().splitlines():
            if regel == "INVOCATION":
                invocaties.append([])
            elif regel.startswith("ARG\t"):
                invocaties[-1].append(regel[len("ARG\t") :])
        return [argv for argv in invocaties if argv[:1] != ["-v"]]


@pytest.fixture
def fake_rg(tmp_path):
    bindir = tmp_path / "fakebin"
    bindir.mkdir()
    script = bindir / "rg"
    script.write_text(_FAKE_RG_SOURCE)
    script.chmod(0o755)
    return _FakeRg(bindir=bindir, log=tmp_path / "rg-argv.log")


def _splits_op_scheidingsteken(argv: list[str]) -> tuple[list[str], list[str]]:
    assert "--" in argv, f"rg-aanroep zonder expliciet scheidingsteken: {argv}"
    grens = argv.index("--")
    return argv[:grens], argv[grens + 1 :]


def test_opties_staan_voor_en_targets_na_het_scheidingsteken(fake_rg, tmp_path):
    doel = tmp_path / "mod.py"

    resultaat = fake_rg.run(doel)

    assert resultaat.returncode == 0, resultaat.stdout + resultaat.stderr
    scans = fake_rg.scans
    assert len(scans) == 2, scans
    for argv in scans:
        opties, doelen = _splits_op_scheidingsteken(argv)
        assert doelen == [str(doel)]
        assert "-e" in opties
        assert opties.count("--glob") == 2
        assert "--glob" not in doelen


def test_pre_achtig_argument_wordt_nooit_als_rg_optie_doorgegeven(fake_rg, tmp_path):
    injectie = f"--pre={tmp_path / 'pre.sh'}"

    fake_rg.run(tmp_path / "bron", injectie)

    scans = fake_rg.scans
    assert len(scans) == 2, scans
    for argv in scans:
        opties, doelen = _splits_op_scheidingsteken(argv)
        assert injectie in doelen
        assert injectie not in opties


@pytest.mark.parametrize("falende_pass", [1, 2])
def test_toolerror_blijft_exit_2(fake_rg, tmp_path, falende_pass):
    statuses = [1, 1]
    statuses[falende_pass - 1] = 2

    resultaat = fake_rg.run(tmp_path, statuses=tuple(statuses))

    assert resultaat.returncode == 2, resultaat.stdout + resultaat.stderr
    assert "ripgrep-executiefout" in resultaat.stderr


def test_zonder_treffers_blijft_exit_0(fake_rg, tmp_path):
    resultaat = fake_rg.run(tmp_path, statuses=(1, 1))

    assert resultaat.returncode == 0, resultaat.stdout + resultaat.stderr
    assert "No TODO-like markers found" in resultaat.stdout


@pytest.mark.parametrize("treffende_pass", [1, 2])
def test_treffer_blijft_exit_1_en_wordt_gerapporteerd(
    fake_rg, tmp_path, treffende_pass
):
    statuses = [1, 1]
    outputs = ["", ""]
    statuses[treffende_pass - 1] = 0
    outputs[treffende_pass - 1] = "mod.py:1:regel met TODO-marker"

    resultaat = fake_rg.run(tmp_path, statuses=tuple(statuses), outputs=tuple(outputs))

    assert resultaat.returncode == 1, resultaat.stdout + resultaat.stderr
    assert "mod.py:1:regel met TODO-marker" in resultaat.stderr


@_requires_rg
def test_pre_argument_wordt_niet_als_preprocessor_uitgevoerd(tmp_path):
    """Regressie DEF-735: `--pre=<script>` werd door rg als optie gelezen,
    waardoor een willekeurig script draaide én de gate stil op 0 eindigde.

    Na de fix is het hele argument één padnaam. Die naam bestaat niet, dus
    beide passes geven een rg-executiefout en de bestaande errorprioriteit
    laat de gate fail-closed op 2 eindigen — nooit stil op 0.
    """
    bron = tmp_path / "bron"
    bron.mkdir()
    (bron / "input.py").write_text("# TODO: marker\n")

    sentinel = tmp_path / "preprocessor-heeft-gedraaid"
    preprocessor = tmp_path / "pre.sh"
    preprocessor.write_text(f'#!/usr/bin/env bash\n: >"{sentinel}"\n')
    preprocessor.chmod(0o755)

    resultaat = _run(bron, f"--pre={preprocessor}")

    assert not sentinel.exists(), "preprocessor is via --pre uitgevoerd"
    assert resultaat.returncode == 2, resultaat.stdout + resultaat.stderr
    assert "ripgrep-executiefout" in resultaat.stderr


@_requires_rg
def test_pad_met_spatie_blijft_werken(tmp_path):
    map_met_spatie = tmp_path / "map met spatie"
    map_met_spatie.mkdir()
    (map_met_spatie / "mod.py").write_text('MELDING = "FIXME: kapot"\n')

    resultaat = _run(map_met_spatie)

    assert resultaat.returncode == 1, resultaat.stdout + resultaat.stderr
    assert "map met spatie" in resultaat.stderr


@_requires_rg
def test_pad_met_voorloopstreepje_blijft_werken(tmp_path):
    (tmp_path / "-dash-mod.py").write_text('MELDING = "FIXME: kapot"\n')

    resultaat = _run("-dash-mod.py", cwd=tmp_path)

    assert resultaat.returncode == 1, resultaat.stdout + resultaat.stderr
    # rg drukt bij één expliciet bestand geen bestandsnaam af, wel de regel.
    assert "FIXME: kapot" in resultaat.stderr


@_requires_rg
def test_markdown_en_html_blijven_uitgesloten(tmp_path):
    (tmp_path / "notitie.md").write_text("# TODO: staat in docs\n")
    (tmp_path / "pagina.html").write_text("<!-- TODO: staat in markup -->\n")

    resultaat = _run(tmp_path)

    assert resultaat.returncode == 0, resultaat.stdout + resultaat.stderr
