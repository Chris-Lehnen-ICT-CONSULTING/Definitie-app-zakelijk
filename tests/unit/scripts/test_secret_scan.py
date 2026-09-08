"""Gedragstests voor scripts/ci/secret_scan.py (DEF-522).

`scan_directory()` is de begrensde directoryscan onder de fail-closed
secret-gate. De tests leggen drie dingen vast die stuk voor stuk een stille
doorlaat zouden opleveren:

1. **Bewijs boven exitcode.** Exit 0 is pas succes met een geldig JSON-rapport
   zonder findings, een positief gescand byteaantal en de volledige eindmelding
   "no leaks found" — zonder waarschuwing, skip, read-fout of partiële scan.
2. **Expliciete invoer.** Zonder bestaande, leesbare, niet-lege scope en zonder
   bestaande TOML-config met *actieve* regels wordt de tool niet eens gestart.
3. **Uitvoergrens.** Gitleaks-stdout/stderr en exceptietekst zijn onbetrouwbaar;
   niets daarvan mag in het resultaat, de repr of de procesuitvoer belanden.

Alle waarden zijn zelf gegenereerd en synthetisch: de markers hieronder zijn
bewust *niet* sleutelvormig, er wordt geen projectdatabase, `.env` of
historische waarde aangeraakt. Het gitleaks-proces zelf is in deze unit-suite
een double; het bewijs met de échte gepinde binary is een aparte canary.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "ci"))

import secret_scan

# Synthetische markers. Ze staan voor onbetrouwbare toolinhoud (secret, match,
# regel, logtekst, exceptietekst) en mogen nergens in publieke uitvoer opduiken.
_MARKER_SECRET = "SYNTHETISCHE-MARKER-ALFA-GEEN-ECHTE-WAARDE"
_MARKER_MATCH = "SYNTHETISCHE-MARKER-BRAVO-GEEN-ECHTE-WAARDE"
_MARKER_LOG = "SYNTHETISCHE-MARKER-CHARLIE-GEEN-ECHTE-WAARDE"

_SCHONE_STDERR = (
    b"11:20AM INF scanned ~4096 bytes (4.10 KB) in 12ms\n"
    b"11:20AM INF no leaks found\n"
)

_FINDINGS_STDOUT = json.dumps(
    [
        {
            "RuleID": "generic-api-key",
            "File": "pakket/module.py",
            "StartLine": 12,
            "Secret": _MARKER_SECRET,
            "Match": _MARKER_MATCH,
            "Line": _MARKER_LOG,
        },
        {
            "RuleID": "generic-api-key",
            "File": "pakket/andere.py",
            "StartLine": 3,
            "Secret": _MARKER_SECRET,
            "Match": _MARKER_MATCH,
            "Line": _MARKER_LOG,
        },
    ]
).encode()

_FINDINGS_STDERR = (
    b"11:20AM INF scanned ~4096 bytes (4.10 KB) in 12ms\n"
    b"11:20AM WRN leaks found: 2\n"
)

_ACTIEVE_CONFIG = "[extend]\nuseDefault = true\n"


class _ProcesDouble:
    """Legt de subprocess-aanroep vast en geeft een vast resultaat terug."""

    def __init__(
        self,
        returncode: int = 0,
        stdout: bytes = b"[]",
        stderr: bytes = _SCHONE_STDERR,
        raises: BaseException | None = None,
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.raises = raises
        self.calls: list[tuple[list[str], dict]] = []

    def __call__(self, argv, **kwargs):
        self.calls.append((list(argv), dict(kwargs)))
        if self.raises is not None:
            raise self.raises
        return subprocess.CompletedProcess(
            list(argv), self.returncode, self.stdout, self.stderr
        )

    @property
    def argv(self) -> list[str]:
        return self.calls[0][0]

    @property
    def kwargs(self) -> dict:
        return self.calls[0][1]


@pytest.fixture
def binary(tmp_path: Path) -> Path:
    """Uitvoerbaar bestand op de plek van de gepinde tool (proces is gedoubled)."""
    pad = tmp_path / "gitleaks"
    pad.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    pad.chmod(0o755)
    return pad


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """Bestaande, leesbare, niet-lege scope."""
    pad = tmp_path / "scope"
    pad.mkdir()
    (pad / "module.py").write_text("waarde = 1\n", encoding="utf-8")
    return pad


@pytest.fixture
def config(tmp_path: Path) -> Path:
    """Expliciete TOML-config met actieve regels."""
    pad = tmp_path / "gitleaks.toml"
    pad.write_text(_ACTIEVE_CONFIG, encoding="utf-8")
    return pad


@pytest.fixture
def proces(monkeypatch: pytest.MonkeyPatch) -> _ProcesDouble:
    """Standaard-double: schone scan met volledig succesbewijs."""
    double = _ProcesDouble()
    monkeypatch.setattr(secret_scan.subprocess, "run", double)
    return double


def _installeer(monkeypatch, double: _ProcesDouble) -> _ProcesDouble:
    monkeypatch.setattr(secret_scan.subprocess, "run", double)
    return double


def _scan(binary: Path, source: Path, config: Path, timeout: float = 30):
    return secret_scan.scan_directory(binary, source, config, timeout)


class _KapotPad:
    """Pad-achtig object waarvan de padresolutie faalt met onbetrouwbare tekst.

    Modelleert een faalpunt vóór de procesaanroep (resolve/read) dat geen
    `OSError` uit `subprocess` is en dus niet door de gerichte handlers valt.
    """

    def __fspath__(self) -> str:
        raise OSError(_MARKER_LOG)


def _oppervlak(resultaat, capsys) -> str:
    """Alle publieke tekst rond een resultaat, om op markerlekken te toetsen."""
    gerapporteerd = capsys.readouterr()
    return "\n".join(
        [
            repr(resultaat),
            str(resultaat),
            str(resultaat.status),
            str(resultaat.code),
            gerapporteerd.out,
            gerapporteerd.err,
        ]
    )


def _verwachte_argv(binary, config, seconden: int) -> list[str]:
    # De scope staat niet in argv maar in de cwd: Gitleaks rapporteert `File`
    # relatief aan het scanpad, en alleen met "." blijven dat de repo-relatieve
    # paden waarop de config-allowlists verankerd zijn.
    return [
        str(Path(binary).resolve()),
        "dir",
        ".",
        "--config",
        str(Path(config).resolve()),
        "--gitleaks-ignore-path",
        "/dev/null",
        "--ignore-gitleaks-allow",
        "--redact=100",
        "--no-banner",
        "--no-color",
        "--report-format=json",
        "--report-path=-",
        "--log-level=info",
        f"--timeout={seconden}",
        "--exit-code=1",
    ]


class TestNormaalSucces:
    """Exit 0 mét volledig bewijs is het enige succespad."""

    def test_schone_scan_is_clean(self, binary, source, config, proces):
        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.CLEAN
        assert resultaat.code is secret_scan.ScanErrorCode.OK
        assert resultaat.finding_count == 0
        assert resultaat.scanned_bytes == 4096
        assert resultaat.ok is True
        assert resultaat.exit_code == 0

    def test_gepinde_vlaggen_worden_ongewijzigd_gebruikt(
        self, binary, source, config, proces
    ):
        _scan(binary, source, config, timeout=30)

        assert proces.argv == _verwachte_argv(binary, config, 30)
        # De scope is verplaatst van argv naar de cwd; zonder deze assertie zou
        # een ontbrekende of verkeerde scanscope onopgemerkt blijven.
        assert proces.kwargs["cwd"] == str(Path(source).resolve())

    def test_proces_draait_zonder_shell_en_vangt_uitvoer_op(
        self, binary, source, config, proces
    ):
        _scan(binary, source, config, timeout=30)

        kwargs = proces.kwargs
        assert kwargs.get("shell", False) is False
        assert kwargs.get("capture_output") is True
        assert kwargs.get("check", False) is False
        assert kwargs["timeout"] > 30

    def test_ambient_gitleaks_env_wordt_uit_childenv_verwijderd(
        self, binary, source, config, proces, monkeypatch
    ):
        monkeypatch.setenv("GITLEAKS_CONFIG", _MARKER_LOG)
        monkeypatch.setenv("GITLEAKS_ENABLE_UPLOAD", "true")

        _scan(binary, source, config)

        env = proces.kwargs["env"]
        assert [sleutel for sleutel in env if sleutel.startswith("GITLEAKS_")] == []
        assert _MARKER_LOG not in "".join(env.values())
        assert env.get("PATH")

    def test_eigen_regels_zonder_usedefault_zijn_actief(
        self, binary, source, tmp_path, proces
    ):
        config = tmp_path / "eigen.toml"
        config.write_text(
            '[[rules]]\nid = "eigen-regel"\nregex = "AKIA[0-9A-Z]{16}"\n',
            encoding="utf-8",
        )

        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.CLEAN
        assert len(proces.calls) == 1


class TestBlokkerendeBevinding:
    """Findings en nonzero exit blokkeren; inhoud blijft binnen."""

    @pytest.fixture
    def resultaat(self, binary, source, config, monkeypatch):
        _installeer(
            monkeypatch,
            _ProcesDouble(
                returncode=1, stdout=_FINDINGS_STDOUT, stderr=_FINDINGS_STDERR
            ),
        )
        return _scan(binary, source, config)

    def test_findings_geven_blocked(self, resultaat):
        assert resultaat.status is secret_scan.ScanStatus.BLOCKED
        assert resultaat.code is secret_scan.ScanErrorCode.FINDINGS_PRESENT
        assert resultaat.finding_count == 2

    def test_blocked_is_nonzero_en_niet_ok(self, resultaat):
        assert resultaat.ok is False
        assert resultaat.exit_code != 0

    def test_findinginhoud_lekt_niet_in_resultaat(self, resultaat):
        tekst = repr(resultaat) + str(resultaat)
        for marker in (_MARKER_SECRET, _MARKER_MATCH, _MARKER_LOG):
            assert marker not in tekst


class TestConfigVerplichtEnActief:
    """Zonder bestaande, geldige, actieve config draait de tool niet."""

    def test_ontbrekende_config_wordt_afgewezen(self, binary, source, tmp_path, proces):
        resultaat = _scan(binary, source, tmp_path / "bestaat-niet.toml")

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.CONFIG_MISSING
        assert proces.calls == []

    def test_directory_als_config_wordt_afgewezen(
        self, binary, source, tmp_path, proces
    ):
        map_pad = tmp_path / "configmap"
        map_pad.mkdir()

        resultaat = _scan(binary, source, map_pad)

        assert resultaat.code is secret_scan.ScanErrorCode.CONFIG_MISSING
        assert proces.calls == []

    def test_onparseerbare_toml_wordt_afgewezen(self, binary, source, tmp_path, proces):
        config = tmp_path / "kapot.toml"
        config.write_text("[extend\nuseDefault = true\n", encoding="utf-8")

        resultaat = _scan(binary, source, config)

        assert resultaat.code is secret_scan.ScanErrorCode.CONFIG_INVALID
        assert proces.calls == []

    def test_lege_config_is_inactief(self, binary, source, tmp_path, proces):
        config = tmp_path / "leeg.toml"
        config.write_text("", encoding="utf-8")

        resultaat = _scan(binary, source, config)

        assert resultaat.code is secret_scan.ScanErrorCode.CONFIG_INACTIVE
        assert proces.calls == []

    def test_uitgeschakelde_default_zonder_regels_is_inactief(
        self, binary, source, tmp_path, proces
    ):
        config = tmp_path / "uit.toml"
        config.write_text(
            "[extend]\nuseDefault = false\nrules = []\n", encoding="utf-8"
        )

        resultaat = _scan(binary, source, config)

        assert resultaat.code is secret_scan.ScanErrorCode.CONFIG_INACTIVE
        assert proces.calls == []

    def test_uitgeschakelde_regels_worden_geweigerd(
        self, binary, source, tmp_path, proces
    ):
        # `extend.disabledRules` kan de defaultset leeghalen; welke regels dan
        # nog actief zijn, is zonder de regelset zelf niet te bewijzen.
        config = tmp_path / "uitgezet.toml"
        config.write_text(
            '[extend]\nuseDefault = true\ndisabledRules = ["generic-api-key"]\n',
            encoding="utf-8",
        )

        resultaat = _scan(binary, source, config)

        assert resultaat.code is secret_scan.ScanErrorCode.CONFIG_INACTIVE
        assert proces.calls == []

    def test_externe_extend_route_wordt_geweigerd(
        self, binary, source, tmp_path, proces
    ):
        # `extend.path`/`extend.url` laadt een tweede config die deze validator
        # niet volgt; de effectieve regelset is dan niet vastgesteld.
        config = tmp_path / "extern.toml"
        config.write_text(
            '[extend]\nuseDefault = true\npath = "gedeeld.toml"\n', encoding="utf-8"
        )

        resultaat = _scan(binary, source, config)

        assert resultaat.code is secret_scan.ScanErrorCode.CONFIG_INVALID
        assert proces.calls == []

    def test_regel_zonder_detectiecriterium_is_ongeldig(
        self, binary, source, tmp_path, proces
    ):
        config = tmp_path / "leegregel.toml"
        config.write_text('[[rules]]\nid = "zonder-regex"\n', encoding="utf-8")

        resultaat = _scan(binary, source, config)

        assert resultaat.code is secret_scan.ScanErrorCode.CONFIG_INVALID
        assert proces.calls == []


class TestScopeVerplichtEnNietLeeg:
    """Alleen een bestaande, leesbare, niet-lege directory is scanbereik."""

    def test_ontbrekende_scope_wordt_afgewezen(self, binary, config, tmp_path, proces):
        resultaat = _scan(binary, tmp_path / "weg", config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.SCOPE_MISSING
        assert proces.calls == []

    def test_bestand_als_scope_wordt_afgewezen(self, binary, config, tmp_path, proces):
        bestand = tmp_path / "los.py"
        bestand.write_text("waarde = 1\n", encoding="utf-8")

        resultaat = _scan(binary, bestand, config)

        assert resultaat.code is secret_scan.ScanErrorCode.SCOPE_MISSING
        assert proces.calls == []

    def test_lege_scope_wordt_afgewezen(self, binary, config, tmp_path, proces):
        leeg = tmp_path / "leeg"
        leeg.mkdir()

        resultaat = _scan(binary, leeg, config)

        assert resultaat.code is secret_scan.ScanErrorCode.SCOPE_EMPTY
        assert proces.calls == []


class TestToolBeschikbaarheid:
    """Een ontbrekende of onbruikbare tool is een fout, geen schone scan."""

    def test_ontbrekende_binary_wordt_afgewezen(self, source, config, tmp_path, proces):
        resultaat = _scan(tmp_path / "geen-gitleaks", source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.TOOL_MISSING
        assert proces.calls == []

    def test_niet_uitvoerbare_binary_wordt_afgewezen(
        self, source, config, tmp_path, proces
    ):
        pad = tmp_path / "gitleaks-zonder-x"
        pad.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        pad.chmod(0o644)

        resultaat = _scan(pad, source, config)

        assert resultaat.code is secret_scan.ScanErrorCode.TOOL_MISSING
        assert proces.calls == []

    def test_startfout_van_het_proces_geeft_vaste_foutcode(
        self, binary, source, config, monkeypatch
    ):
        _installeer(
            monkeypatch,
            _ProcesDouble(raises=OSError(_MARKER_LOG)),
        )

        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.TOOL_FAILED
        assert _MARKER_LOG not in repr(resultaat)


class TestGeslotenFoutgrens:
    """Geen gewone exceptie verlaat de publieke ingang — ook niet onverwacht."""

    def test_faalpunt_voor_subprocess_geeft_vaste_fout(
        self, binary, config, proces, capsys
    ):
        resultaat = _scan(binary, _KapotPad(), config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert isinstance(resultaat.code, secret_scan.ScanErrorCode)
        assert resultaat.exit_code != 0
        assert proces.calls == []
        assert _MARKER_LOG not in _oppervlak(resultaat, capsys)

    def test_onverwachte_procesfout_geeft_vaste_fout(
        self, binary, source, config, monkeypatch, capsys
    ):
        _installeer(monkeypatch, _ProcesDouble(raises=RuntimeError(_MARKER_LOG)))

        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.UNEXPECTED_FAILURE
        assert _MARKER_LOG not in _oppervlak(resultaat, capsys)

    def test_onverwachte_parserfout_geeft_vaste_fout(
        self, binary, source, config, monkeypatch, capsys
    ):
        def _kapotte_parser(*args, **kwargs):
            raise RuntimeError(_MARKER_SECRET)

        _installeer(monkeypatch, _ProcesDouble())
        monkeypatch.setattr(secret_scan.json, "loads", _kapotte_parser)

        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.UNEXPECTED_FAILURE
        assert _MARKER_SECRET not in _oppervlak(resultaat, capsys)


class TestOnbruikbareResponse:
    """Niet-decodeerbare procesuitvoer is geen bruikbaar bewijs."""

    def test_onleesbare_stderr_is_nonzero(self, binary, source, config, monkeypatch):
        _installeer(
            monkeypatch,
            _ProcesDouble(returncode=0, stderr=_SCHONE_STDERR + b"\xff\xfe\n"),
        )

        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.RESPONSE_UNREADABLE

    def test_onleesbare_stdout_is_nonzero(self, binary, source, config, monkeypatch):
        _installeer(monkeypatch, _ProcesDouble(returncode=0, stdout=b"\xff\xfe"))

        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.RESPONSE_UNREADABLE


class TestTimeout:
    """Een timeout is fail-closed, niet 'geen findings'."""

    def test_timeout_geeft_vaste_foutcode(self, binary, source, config, monkeypatch):
        _installeer(
            monkeypatch,
            _ProcesDouble(
                raises=subprocess.TimeoutExpired(
                    cmd=["gitleaks"],
                    timeout=1,
                    output=_MARKER_MATCH.encode(),
                    stderr=_MARKER_LOG.encode(),
                )
            ),
        )

        resultaat = _scan(binary, source, config, timeout=1)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.TIMEOUT
        assert resultaat.ok is False

    def test_niet_positieve_timeout_wordt_afgewezen(
        self, binary, source, config, proces
    ):
        resultaat = _scan(binary, source, config, timeout=0)

        assert resultaat.code is secret_scan.ScanErrorCode.INVALID_TIMEOUT
        assert proces.calls == []


class TestExitNulZonderBewijs:
    """Exit 0 zonder volledig bewijs is een fout, geen succes."""

    def _resultaat(self, monkeypatch, binary, source, config, stderr: bytes):
        _installeer(monkeypatch, _ProcesDouble(returncode=0, stderr=stderr))
        return _scan(binary, source, config)

    def test_ontbrekende_byteregel_is_geen_succes(
        self, binary, source, config, monkeypatch
    ):
        resultaat = self._resultaat(
            monkeypatch, binary, source, config, b"11:20AM INF no leaks found\n"
        )

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.NO_SCAN_EVIDENCE

    def test_ontbrekende_eindmelding_is_geen_succes(
        self, binary, source, config, monkeypatch
    ):
        resultaat = self._resultaat(
            monkeypatch,
            binary,
            source,
            config,
            b"11:20AM INF scanned ~4096 bytes (4.10 KB) in 12ms\n",
        )

        assert resultaat.code is secret_scan.ScanErrorCode.NO_SCAN_EVIDENCE

    def test_nul_gescande_bytes_is_geen_succes(
        self, binary, source, config, monkeypatch
    ):
        resultaat = self._resultaat(
            monkeypatch,
            binary,
            source,
            config,
            b"11:20AM INF scanned ~0 bytes (0 B) in 4ms\n11:20AM INF no leaks found\n",
        )

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.ZERO_BYTES

    def test_lege_uitvoer_is_geen_succes(self, binary, source, config, monkeypatch):
        _installeer(monkeypatch, _ProcesDouble(returncode=0, stdout=b"", stderr=b""))

        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.ok is False


class TestOnvolledigeScan:
    """Skip-, read- en partial-meldingen zijn geen schone scan."""

    @pytest.mark.parametrize(
        "stderr",
        [
            pytest.param(
                b"11:20AM WRN scanned ~4096 bytes (4.10 KB)\n"
                b"11:20AM WRN partial scan completed in 12ms\n"
                b"11:20AM WRN no leaks found in partial scan\n",
                id="partiele-scan",
            ),
            pytest.param(
                b"11:20AM WRN skipping file error=permission denied path=x\n"
                b"11:20AM INF scanned ~4096 bytes (4.10 KB) in 12ms\n"
                b"11:20AM INF no leaks found\n",
                id="skip-waarschuwing",
            ),
            pytest.param(
                b"11:20AM ERR skipping file: could not get info path=x\n"
                b"11:20AM INF scanned ~4096 bytes (4.10 KB) in 12ms\n"
                b"11:20AM INF no leaks found\n",
                id="read-fout",
            ),
        ],
    )
    def test_waarschuwing_blokkeert_succes(
        self, binary, source, config, monkeypatch, stderr
    ):
        _installeer(monkeypatch, _ProcesDouble(returncode=0, stderr=stderr))

        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.SCAN_INCOMPLETE


class TestRapportconsistentie:
    """Het JSON-rapport moet geldig zijn en met de exitcode kloppen."""

    def test_onparseerbaar_rapport_is_fout(self, binary, source, config, monkeypatch):
        _installeer(
            monkeypatch,
            _ProcesDouble(returncode=0, stdout=b"{niet-json" + _MARKER_LOG.encode()),
        )

        resultaat = _scan(binary, source, config)

        assert resultaat.code is secret_scan.ScanErrorCode.REPORT_INVALID
        assert _MARKER_LOG not in repr(resultaat)

    def test_rapport_dat_geen_array_is_is_fout(
        self, binary, source, config, monkeypatch
    ):
        _installeer(monkeypatch, _ProcesDouble(returncode=0, stdout=b'{"findings": 0}'))

        resultaat = _scan(binary, source, config)

        assert resultaat.code is secret_scan.ScanErrorCode.REPORT_INVALID

    def test_exit_nul_met_findings_is_tegenstrijdig(
        self, binary, source, config, monkeypatch
    ):
        _installeer(monkeypatch, _ProcesDouble(returncode=0, stdout=_FINDINGS_STDOUT))

        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.REPORT_INCONSISTENT
        assert resultaat.ok is False

    def test_exit_een_met_leeg_rapport_is_tegenstrijdig(
        self, binary, source, config, monkeypatch
    ):
        _installeer(monkeypatch, _ProcesDouble(returncode=1, stdout=b"[]"))

        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.REPORT_INCONSISTENT
        assert resultaat.finding_count == 0

    def test_exit_een_met_onbruikbaar_rapport_is_fout(
        self, binary, source, config, monkeypatch
    ):
        _installeer(
            monkeypatch,
            _ProcesDouble(returncode=1, stdout=_MARKER_SECRET.encode()),
        )

        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.REPORT_INVALID
        assert _MARKER_SECRET not in repr(resultaat)

    def test_onverwachte_exitcode_is_fout(self, binary, source, config, monkeypatch):
        _installeer(
            monkeypatch,
            _ProcesDouble(returncode=2, stdout=b"", stderr=_MARKER_LOG.encode()),
        )

        resultaat = _scan(binary, source, config)

        assert resultaat.status is secret_scan.ScanStatus.ERROR
        assert resultaat.code is secret_scan.ScanErrorCode.UNEXPECTED_EXIT


class TestUitvoergrens:
    """Onbetrouwbare toolinhoud verlaat de functie niet — ook niet bij fouten."""

    @pytest.fixture(
        params=["blocked", "onvolledig", "kapot-rapport", "timeout", "onverwacht"]
    )
    def scenario(self, request) -> _ProcesDouble:
        lekkende_stderr = (
            f"11:20AM WRN skipping file error={_MARKER_LOG} path={_MARKER_MATCH}\n"
            "11:20AM INF scanned ~4096 bytes (4.10 KB) in 12ms\n"
            "11:20AM INF no leaks found\n"
        ).encode()
        doubles = {
            "blocked": _ProcesDouble(
                returncode=1, stdout=_FINDINGS_STDOUT, stderr=_FINDINGS_STDERR
            ),
            "onvolledig": _ProcesDouble(returncode=0, stderr=lekkende_stderr),
            "kapot-rapport": _ProcesDouble(
                returncode=0, stdout=_MARKER_SECRET.encode(), stderr=lekkende_stderr
            ),
            "timeout": _ProcesDouble(
                raises=subprocess.TimeoutExpired(
                    cmd=["gitleaks"],
                    timeout=1,
                    output=_MARKER_SECRET.encode(),
                    stderr=_MARKER_LOG.encode(),
                )
            ),
            "onverwacht": _ProcesDouble(
                returncode=2, stdout=_MARKER_MATCH.encode(), stderr=lekkende_stderr
            ),
        }
        return doubles[request.param]

    def test_geen_synthetische_marker_in_resultaat_of_uitvoer(
        self, binary, source, config, monkeypatch, capsys, scenario
    ):
        _installeer(monkeypatch, scenario)

        resultaat = _scan(binary, source, config)

        oppervlak = _oppervlak(resultaat, capsys)
        for marker in (_MARKER_SECRET, _MARKER_MATCH, _MARKER_LOG):
            assert marker not in oppervlak

    def test_fouttoestand_gebruikt_uitsluitend_vaste_codes(
        self, binary, source, config, monkeypatch, scenario
    ):
        _installeer(monkeypatch, scenario)

        resultaat = _scan(binary, source, config)

        assert isinstance(resultaat.code, secret_scan.ScanErrorCode)
        assert isinstance(resultaat.status, secret_scan.ScanStatus)
        assert resultaat.ok is False
        assert resultaat.exit_code != 0
        assert isinstance(resultaat.finding_count, int)
        assert isinstance(resultaat.scanned_bytes, int)
