"""Ketentest: workflow → Makefile → gate-CLI (DEF-522).

De andere suites starten de CLI rechtstreeks. Daarmee blijft één schakel
ongedekt: de aanroep die de verplichte CI-job werkelijk doet. Deze module leest
de `secrets-scan`-job uit `security.yml`, controleert dat die job en die stap niet
optioneel of `continue-on-error` zijn, en haalt de gebruikte aanroep eruit. Alleen
de exact toegestane argv (`make secret-scan`) wordt uitgevoerd; YAML-inhoud wordt
gelezen en gevalideerd, nooit als shellcode geïnterpreteerd.

De aanroep draait daarna echt, in een eigen synthetische origin+clone met exacte
kopieën van de actuele Makefile en de drie scannerscripts op hun normale
relatieve paden. Zo valt ook een omgeleide of gebroken Make→CLI-keten door de
mand, niet alleen een afwijkende YAML-string. Twee gevallen: schoon geeft `clean`
en exitcode 0, een synthetische canary in de werkboom geeft `blocked` en nonzero.

De config is de zelfgemaakte minimale fixtureconfig; de projectuitzonderingen zijn
elders bewezen. Alle procesuitvoer wordt opgevangen: faalmeldingen tonen alleen
status, code en tellingen, nooit een canarywaarde of ruwe tooltekst.

Naast de aanroep controleert de leesstap twee dingen die de uitvoering zelf niet
kan aantonen, omdat de test de omgeving van de gate expliciet zelf meegeeft:
dat de job-`env` geen context gebruikt die GitHub daar niet beschikbaar stelt
(zo'n expressie laat de hele run met nul jobs falen, ruim voordat een stap
draait), en dat de vier padwaarden die de job echt nodig heeft staan op de stap
die ze gebruikt. Dit is een gerichte regressiecontrole op die twee punten, geen
eigen validator voor workflowsyntaxis.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

pytestmark = [pytest.mark.acceptance]

sys.path.insert(0, str(Path(__file__).resolve().parent))

import secret_scan
import test_secret_scan_canary as canary_fixtures
import test_secret_scan_gate as gate

#: Gedeelde helpers; één canary-vorm, één isolatiebewijs, één child-omgeving.
_Omgeving = canary_fixtures._Omgeving
_Uitkomst = gate._Uitkomst
_verplicht_pad = canary_fixtures._verplicht_pad
_git_omgeving = canary_fixtures._git_omgeving
_diagnose = gate._diagnose
_canary = gate._canary
_canary_regel = gate._canary_regel
_origin_met_clone = gate._origin_met_clone
_CANARY_BESTAND = canary_fixtures._CANARY_BESTAND

_PROJECT = Path(__file__).resolve().parents[2]
_WORKFLOW = _PROJECT / ".github" / "workflows" / "security.yml"
_JOB = "secrets-scan"

#: De enige aanroep die deze test uitvoert. De workflow moet exact deze argv
#: gebruiken; iets anders wordt niet uitgevoerd maar afgekeurd.
_TOEGESTANE_ARGV = ["make", "secret-scan"]

#: Contexten die GitHub op `jobs.<id>.env` niet beschikbaar stelt. `runner`
#: hoort volgens de contextbeschikbaarheidstabel bij `steps.env`, niet bij
#: `jobs.<id>.env`. Een expressie met zo'n context laat het inlezen van de
#: workflow falen: de run start met nul jobs, dus de verplichte gate draait
#: nooit en de fail-closed opzet is stil weg.
_VERBODEN_JOB_CONTEXTEN = ("runner",)

#: De vier padwaarden die de job werkelijk nodig heeft, per stap die ze
#: gebruikt. De stap wordt herkend aan wat de `run` doet, niet aan de naam.
#: Zonder deze controle zou de ketentest alleen de omgeving bewijzen die zij
#: zelf aan het kindproces meegeeft, en niets over de workflow.
_STAP_ENV_EISEN: tuple[tuple[str, dict[str, str]], ...] = (
    (
        "$GITLEAKS_DIR",
        {"GITLEAKS_DIR": "${{ runner.temp }}/gitleaks"},
    ),
    (
        "make test-secret-scan",
        {
            "DEF522_GITLEAKS_BINARY": "${{ runner.temp }}/gitleaks/gitleaks",
            "DEF522_FIXTURE_ROOT": "${{ runner.temp }}/def522-fixtures",
        },
    ),
    (
        "make secret-scan",
        {"SECRET_SCAN_BINARY": "${{ runner.temp }}/gitleaks/gitleaks"},
    ),
)

#: Eén `${{ ... }}`-expressie; de inhoud wordt apart op contexten bekeken.
_EXPRESSIE = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)

#: De schakels van de keten, op hun normale relatieve paden.
_KETENBESTANDEN = (
    "Makefile",
    "scripts/ci/secret_scan.py",
    "scripts/ci/secret_scan_gate.py",
    "scripts/ci/secret_scan_precommit.py",
)

_MAKE_TIMEOUT = 300
_TOOL_TIMEOUT = "60"
_CLEAN = secret_scan.ScanStatus.CLEAN.value
_BLOCKED = secret_scan.ScanStatus.BLOCKED.value


def _verboden_contexten(waarde: str) -> list[str]:
    """De op job-niveau onbeschikbare contexten die in `waarde` voorkomen."""
    gevonden: list[str] = []
    for expressie in _EXPRESSIE.findall(waarde):
        for context in _VERBODEN_JOB_CONTEXTEN:
            patroon = rf"(?<![\w.]){re.escape(context)}\b"
            if re.search(patroon, expressie) and context not in gevonden:
                gevonden.append(context)
    return gevonden


def _keur_job_env(job: dict) -> None:
    """Weiger een job-`env` die een daar onbeschikbare context gebruikt."""
    for naam, waarde in (job.get("env") or {}).items():
        contexten = _verboden_contexten(str(waarde))
        if contexten:
            pytest.fail(
                f"job {_JOB} gebruikt op env.{naam} de context "
                f"{', '.join(contexten)}, die GitHub daar niet beschikbaar "
                "stelt. De workflow wordt afgewezen en de run krijgt nul jobs, "
                "dus de verplichte gate draait niet. Zet deze waarde op de "
                "env van de stap die hem gebruikt."
            )


def _keur_stap_env(stappen: list[dict]) -> None:
    """Eis de vaste padwaarden op de stap die ze werkelijk gebruikt."""
    for marker, verwacht in _STAP_ENV_EISEN:
        passend = [
            stap
            for stap in stappen
            if isinstance(stap.get("run"), str) and marker in stap["run"]
        ]
        if len(passend) != 1:
            pytest.fail(
                f"verwacht precies één stap waarvan de run {marker!r} gebruikt; "
                f"gevonden: {len(passend)}."
            )
        omgeving = passend[0].get("env") or {}
        for naam, waarde in verwacht.items():
            if omgeving.get(naam) != waarde:
                pytest.fail(
                    f"de stap met {marker!r} moet env.{naam} op {waarde!r} "
                    f"zetten; gevonden: {omgeving.get(naam)!r}. Zonder deze "
                    "waarde op de juiste stap bewijst de ketentest alleen de "
                    "omgeving die zij zelf meegeeft."
                )


def _gate_argv() -> list[str]:
    """Lees en valideer de gate-aanroep van de verplichte job."""
    document = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    job = document.get("jobs", {}).get(_JOB)
    if not isinstance(job, dict):
        pytest.fail(f"job {_JOB} ontbreekt in {_WORKFLOW.name}.")
    if job.get("continue-on-error") or "if" in job:
        pytest.fail(f"job {_JOB} is voorwaardelijk of continue-on-error.")

    _keur_job_env(job)
    _keur_stap_env(job.get("steps", []))

    stappen = [
        stap
        for stap in job.get("steps", [])
        if isinstance(stap.get("run"), str) and stap["run"].split() == _TOEGESTANE_ARGV
    ]
    if len(stappen) != 1:
        pytest.fail(
            f"verwacht precies één stap die {' '.join(_TOEGESTANE_ARGV)} draait; "
            f"gevonden: {len(stappen)}."
        )
    if stappen[0].get("continue-on-error") or "if" in stappen[0]:
        pytest.fail("de gate-stap is voorwaardelijk of continue-on-error.")
    return list(_TOEGESTANE_ARGV)


def _keten_clone(omgeving: _Omgeving, naam: str) -> gate._Fixture:
    """Origin met clone, plus exacte kopieën van de ketenbestanden."""
    opzet = _origin_met_clone(omgeving, naam)
    for relpad in _KETENBESTANDEN:
        doel = opzet.clone / relpad
        doel.parent.mkdir(parents=True, exist_ok=True)
        doel.write_text(
            (_PROJECT / relpad).read_text(encoding="utf-8"), encoding="utf-8"
        )
    return opzet


def _document(stdout: str) -> dict | None:
    """De JSON-regel uit de make-uitvoer; de banner van make staat ervoor."""
    for regel in reversed(stdout.splitlines()):
        try:
            gelezen = json.loads(regel)
        except ValueError:
            continue
        if isinstance(gelezen, dict):
            return gelezen
    return None


def _draai_make(
    argv: list[str], opzet: gate._Fixture, omgeving: _Omgeving, *, verboden: str
) -> _Uitkomst:
    """Voer de gevalideerde aanroep uit in de clone, met expliciete invoer."""
    kindomgeving = _git_omgeving()
    kindomgeving.update(
        {
            "PY": sys.executable,
            "SECRET_SCAN_SOURCE": str(opzet.clone),
            "SECRET_SCAN_CONFIG": str(opzet.config),
            "SECRET_SCAN_BINARY": str(omgeving.binary),
            "SECRET_SCAN_BASE": opzet.base,
            "SECRET_SCAN_HEAD": opzet.head,
            "SECRET_SCAN_TIMEOUT": _TOOL_TIMEOUT,
        }
    )
    voltooid = subprocess.run(
        argv,
        cwd=str(opzet.clone),
        capture_output=True,
        check=False,
        shell=False,
        text=True,
        timeout=_MAKE_TIMEOUT,
        env=kindomgeving,
    )
    return _Uitkomst(
        exit_code=voltooid.returncode,
        document=_document(voltooid.stdout),
        lekt=verboden in f"{voltooid.stdout}\n{voltooid.stderr}",
    )


@pytest.fixture
def omgeving() -> _Omgeving:
    """De verplicht aangewezen binary en fixture-root; geen default, geen skip."""
    return _Omgeving(
        binary=_verplicht_pad(canary_fixtures._ENV_BINARY, uitvoerbaar=True),
        fixture_root=_verplicht_pad(canary_fixtures._ENV_FIXTURE_ROOT),
    )


def test_workflowketen_op_schone_clone_geeft_clean(omgeving: _Omgeving) -> None:
    """De aanroep uit de verplichte job loopt door tot een schone uitkomst."""
    argv = _gate_argv()
    opzet = _keten_clone(omgeving, "workflow-schoon")

    uitkomst = _draai_make(argv, opzet, omgeving, verboden=_canary())

    assert not uitkomst.lekt
    assert uitkomst.document is not None, (
        f"{_diagnose(uitkomst)} — de keten leverde geen uitkomst van de gate. "
        "De aanroep uit de workflow bereikt de CLI niet."
    )
    assert uitkomst.document["status"] == _CLEAN, _diagnose(uitkomst)
    assert uitkomst.document["scanned_bytes"] > 0, _diagnose(uitkomst)
    assert uitkomst.exit_code == 0, _diagnose(uitkomst)


def test_workflowketen_blokkeert_op_canary(omgeving: _Omgeving) -> None:
    """Dezelfde aanroep blokkeert op een synthetische canary in de werkboom."""
    argv = _gate_argv()
    opzet = _keten_clone(omgeving, "workflow-canary")
    canary = _canary()
    doel = opzet.clone / _CANARY_BESTAND
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_text(_canary_regel(canary), encoding="utf-8")

    uitkomst = _draai_make(argv, opzet, omgeving, verboden=canary)

    assert not uitkomst.lekt, "de canary-waarde staat in de publieke uitvoer."
    assert uitkomst.document is not None, _diagnose(uitkomst)
    assert uitkomst.document["status"] == _BLOCKED, (
        f"{_diagnose(uitkomst)} — de canary staat in de werkboom van de clone. "
        "Een uitblijvende blokkade betekent dat de keten de gate omzeilt."
    )
    assert uitkomst.document["finding_count"] > 0, _diagnose(uitkomst)
    assert uitkomst.exit_code != 0, _diagnose(uitkomst)
