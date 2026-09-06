#!/usr/bin/env python3
"""Begrensde testrunner met één profiel per hoofdgate (DEF-519).

De drie verplichte gates (`unit`, `integration`, `acceptance-smoke`) draaien
allemaal via dit script, zodat er geen verborgen tweede selectie kan ontstaan.
Daarnaast bestaan er twee optionele, niet-verplichte profielen (`advisory`,
`future`) voor precies de nodes die de hoofdgates uitsluiten. Ze draaien onder
exact dezelfde offline-bootstrap, dezelfde status- en bewijsregels en hetzelfde
procesbudget; ze zijn alleen niet verplicht. Er is geen live-profiel: `live`
valt overal buiten, en dit script vraagt of verleent geen toegang tot echte
providers, kosten of netwerk.

Wat de runner regelt vóórdat pytest ook maar geïmporteerd wordt:

* **Sessieroot.** Een verse tijdelijke map met eigendomsmarkering. Alles wat de
  run aan data aanmaakt hoort daarbinnen te landen.
* **Werkmap.** Een verse CWD binnen die sessieroot, met `config/` en `src/` als
  symlink naar het project en een lege `data/`. Daardoor landt het
  CWD-relatieve standaardpad `data/definities.db` in tijdelijke opslag in
  plaats van in de werkmap van de ontwikkelaar, terwijl `config.yaml` gewoon
  gevonden wordt (hetzelfde patroon als de bestaande `hermetische_werkmap`).
* **Bootstrap bij interpreterstart.** Een gegenereerde `sitecustomize.py` in de
  sessieroot installeert `tests.offline_bootstrap`. `site` importeert dat vóór
  pytest zelf, en elk kindproces (xdist-workers, geneste runs) erft dezelfde
  omgeving en dezelfde sessieroot.
* **Omgeving.** Dummy providerkeys, dotenv uit, `ALLOW_NETWORK` weg en
  `PYTEST_ADDOPTS` weg — de gebruikersomgeving mag een verplicht profiel niet
  oprekken of verzwakken.

Uitkomsten zijn expliciet: lege selectie, collectiefout, toolfout, testfalen en
budgetoverschrijding geven elk een eigen nonzero exitcode en een `status=`-regel.
Die regel begint altijd op een eigen nieuwe regel, ook als het pytest-kind zijn
laatste uitvoer zonder newline op de gedeelde stdout achterliet. Er is geen pad
waarlangs een run stil groen wordt.

De inventaris scheidt de overslag-soorten die pytest zelf ook scheidt:
collectie-skips (een module die zichzelf overslaat en dus nooit een node
oplevert), skips per unieke node uit setup of body, xfails en niet-strikte
XPASSes. Elke telling staat naast haar node-ids, zodat zij per node tegen de
JUnit van dezelfde run te leggen is.

Wat "groen" minimaal vereist
----------------------------
`status=ok` wordt pas gemeld als álle onderstaande bewijsstukken er zijn. Elk
ervan komt uit de run zelf, niet uit een aanname over hoe pytest zich hoort te
gedragen:

* een leesbare inventaris met de verwachte velden (`geen-inventaris`);
* bewijs dat de offline-bootstrap in het pytest-proces actief was, op déze
  sessieroot (`geen-bootstrapbewijs`);
* minstens één werkelijk uitgevoerde, niet-overgeslagen testcall
  (`geen-uitvoering`) — een niet-lege collectie is nadrukkelijk niet genoeg.

Daarnaast is de aanroep zelf begrensd: doorgegeven pytest-opties gaan door een
allowlist van rapportage- en coverage-vlaggen (`verboden-optie`), en het
procesbudget moet eindig en positief zijn (`ongeldig-budget`). Een fout in de
bootstrap stopt de interpreter vóór pytest ook maar start (`bootstrapfout`) in
plaats van als `site`-waarschuwing door te lopen.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

#: Markerselectie per profiel. `make test`/CI roepen uitsluitend deze namen aan.
#:
#: Het `integration`-profiel selecteert de *vereniging* van het integratiepad en
#: de integrationmarker: de gegenereerde plugin geeft elke node onder
#: `<rootdir>/tests/integration/` de integrationmarker vóórdat pytest zijn eigen
#: `-m`-filtering toepast. Zonder die stap zouden de contract-, regression-,
#: compliance-, performance- en golden-bestanden in die map — die geen
#: integrationmarker dragen — stil buiten de verplichte gate vallen.
#:
#: De twee hoofdgates zonderen precies één soort node uit: die zichzelf
#: expliciet `advisory`, `future` of `live` noemt. Dat is een uitsluiting op
#: eigen verklaring, geen blanket-filter — `slow`, `performance` en `red_phase`
#: blijven gewoon binnen de gate, en er is geen lijst met bestandsnamen.
#: `unit` filtert helemaal niets weg: alle unittests, inclusief `slow` en
#: inclusief een node die zichzelf advisory noemt.
#:
#: `advisory` en `future` zijn optionele profielen voor exact hun eigen marker.
#: Buiten de verplichte gate staan betekent niet stil groen mogen zijn: een
#: echte assertiefout daar levert net zo goed `status=testfalen` en nonzero op.
#: `live` heeft bewust géén profiel — die nodes raken een echte externe dienst
#: en worden hier nooit gestart.
PROFIELEN = {
    "unit": "unit",
    "integration": "integration and not (advisory or future or live)",
    "acceptance-smoke": "(acceptance or smoke) and not (advisory or future or live)",
    "advisory": "advisory",
    "future": "future",
    # Bestaande required check "Validation Contract Tests". Dezelfde
    # uitsluitingen als de hoofdgates; de contractnodes onder `tests/integration`
    # blijven daarnaast gewoon deel van de integrationunie.
    "contract": "contract and not (advisory or future or live)",
}

EIGENDOMSMARKERING = ".def519-session-root"
STANDAARDBUDGET = 900.0

EXITCODES = {
    "ok": 0,
    "testfalen": 1,
    "collectiefout": 2,
    "onveilige-basetemp": 3,
    "toolfout": 4,
    "lege-selectie": 5,
    "onderbroken": 6,
    "intern": 7,
    "verboden-optie": 8,
    "ongeldig-budget": 9,
    "geen-inventaris": 10,
    "geen-bootstrapbewijs": 11,
    "geen-uitvoering": 12,
    "bootstrapfout": 13,
    "coverage-data-bestaat-al": 14,
    "coverage-config-onbruikbaar": 15,
    "coverage-unsupported-config": 16,
    "coverage-geen-data": 17,
    "coverage-onder-vloer": 18,
    "coverage-rapportfout": 19,
    "budget-overschreden": 124,
}

#: Exitcodes van het gegenereerde coverage-entrypoint. Bewust hoog en uniek,
#: zodat ze niet met pytest-exitcodes of BOOTSTRAP_EXITCODE botsen.
COV_CONFIG = 90
COV_UNSUPPORTED = 92
COV_GEEN_DATA = 93
COV_ONDER_VLOER = 94
COV_RAPPORTFOUT = 95

#: Kindexitcode → runnerstatus.
COV_STATUS = {
    COV_CONFIG: "coverage-config-onbruikbaar",
    COV_UNSUPPORTED: "coverage-unsupported-config",
    COV_GEEN_DATA: "coverage-geen-data",
    COV_ONDER_VLOER: "coverage-onder-vloer",
    COV_RAPPORTFOUT: "coverage-rapportfout",
}

#: Exitcode waarmee de gegenereerde `sitecustomize.py` de interpreter afbreekt
#: als de bootstrap niet installeert. `site` slikt een gewone exception in
#: (waarschuwing op stderr, interpreter start alsnog), dus de bootstrap moet het
#: proces zélf beëindigen — vóór pytest of applicatiecode ook maar begint.
BOOTSTRAP_EXITCODE = 91

_SITECUSTOMIZE = f'''"""Gegenereerd door scripts/testing/run_profile.py — installeert de offline-gate."""

import os
import sys

try:
    _wortel = os.environ["DEF519_BOOTSTRAP_ROOT"]
    if _wortel not in sys.path:
        sys.path.insert(0, _wortel)

    from tests import offline_bootstrap

    offline_bootstrap.install()
except BaseException:
    # `site` zou hier alleen een waarschuwing van maken en gewoon doorstarten.
    # Een ongeïnstalleerde gate mag echter nooit tot een draaiende testrun
    # leiden, dus stoppen we vóór er applicatiecode is geïmporteerd.
    import traceback

    print(
        "[run_profile] offline-bootstrap kon niet installeren; "
        "de interpreter stopt vóór pytest of applicatiecode start.",
        file=sys.stderr,
    )
    traceback.print_exc()
    sys.stderr.flush()
    os._exit({BOOTSTRAP_EXITCODE})
'''

_COVERAGE_ENTRY = f'''"""Gegenereerd door run_profile.py — seriële coverage rond één pytest.main.

pytest-cov is hier bewust niet in het spel: zijn `Central.finish` combineert
altijd, ook zonder xdist, en `CoverageData.update` doet dat met
`ATTACH DATABASE ?`. Op autorisatiemoment is die parameter nog ongebonden, dus de
offline-gate weigert hem fail-closed. Dit entrypoint meet daarom zelf met de
ondersteunde Coverage-API: één proces, één datafile, geen combine, geen append.
"""

import json
import os
import sys


def _fout(code, melding):
    print(f"[run_profile:coverage] {{melding}}", file=sys.stderr)
    sys.stderr.flush()
    return code


def main():
    spec = json.loads(os.environ["DEF519_COVERAGE"])

    import coverage

    kwargs = {{"data_file": spec["data_file"], "config_file": spec["config_file"]}}
    if spec["source"]:
        kwargs["source"] = spec["source"]
    if spec["branch"]:
        kwargs["branch"] = True
    try:
        cov = coverage.Coverage(**kwargs)
    except BaseException as fout:  # configuratie is hier de enige oorzaak
        return _fout({COV_CONFIG}, f"configuratie onbruikbaar: {{fout}}")

    # Publieke API, geen private config-attributen.
    if cov.get_option("paths"):
        return _fout(
            {COV_UNSUPPORTED},
            "[paths] wordt niet ondersteund; het wordt niet stil gestript",
        )
    if cov.get_option("run:parallel"):
        return _fout(
            {COV_UNSUPPORTED},
            "parallel-configuratie wordt niet ondersteund; combine is geblokkeerd",
        )

    import pytest

    pytest_code = None
    cov.start()
    try:
        pytest_code = int(pytest.main(sys.argv[1:]))
    finally:
        try:
            cov.stop()
            cov.save()
        except BaseException as fout:
            # Een al rode suite houdt zijn eigen exitcode; alleen na groene
            # tests wordt de save-fout zelf de uitkomst.
            if pytest_code:
                sys.exit(pytest_code)
            sys.exit(_fout({COV_RAPPORTFOUT}, f"opslaan mislukt: {{fout}}"))

    if pytest_code != 0:
        return pytest_code

    data = cov.get_data()
    if not any(data.lines(bestand) for bestand in data.measured_files()):
        return _fout({COV_GEEN_DATA}, "geen enkele werkelijk gemeten regel")

    try:
        # Zonder expliciete term/term-missing blijft `report:show_missing` uit de
        # configuratie leidend.
        toon_missend = spec["show_missing"]
        if toon_missend is None:
            toon_missend = bool(cov.get_option("report:show_missing"))
        totaal = cov.report(show_missing=toon_missend)
        for doel in spec["xml"]:
            cov.xml_report(outfile=doel)
    except BaseException as fout:
        return _fout({COV_RAPPORTFOUT}, f"rapportage mislukt: {{fout}}")

    vloer = spec["fail_under"]
    if vloer is None:
        vloer = cov.get_option("report:fail_under") or 0
    if vloer and totaal < float(vloer):
        return _fout(
            {COV_ONDER_VLOER}, f"dekking {{totaal:.2f}} ligt onder vloer {{vloer}}"
        )

    print(f"[run_profile:coverage] totaal={{totaal:.2f}} vloer={{vloer}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

_PLUGIN = '''"""Gegenereerd door scripts/testing/run_profile.py — één collectie-inventaris."""

import json
import os

import pytest

_rapportpad = os.environ["DEF519_REPORT"]
_verzameld = {
    "items": [],
    "collectiefouten": 0,
    "collectie_overgeslagen": [],
    "uitgevoerd": 0,
    "overgeslagen": [],
    "xfail": [],
    "xpassed": [],
}
_bewijs = {"gate_actief": False, "sessieroot": None, "applicatiemodules": None}


def _noteer(verzameling, nodeid):
    """Leg een node eenmalig vast; skips tellen per node, niet per rapport."""
    if nodeid not in verzameling:
        verzameling.append(nodeid)


def pytest_configure(config):
    """Leg het bootstrapbewijs vast vóór er ook maar iets verzameld wordt.

    Het bewijs komt uit de module die de gate daadwerkelijk installeerde, niet
    uit de aanname dat `sitecustomize` gedraaid heeft. Ontbreekt de gate, dan
    stopt de run hier — niet na een groen ogende sessie.
    """
    from tests import offline_bootstrap

    if not offline_bootstrap.gate_is_actief():
        raise pytest.UsageError(
            "[run_profile] de offline-bootstrap is niet actief in dit "
            "pytest-proces; de verplichte gate kan niet worden overgeslagen."
        )
    rapport = offline_bootstrap.installatie_rapport()
    _bewijs["gate_actief"] = True
    _bewijs["sessieroot"] = rapport["sessieroot"]
    _bewijs["applicatiemodules"] = rapport["applicatiemodules_bij_installatie"]


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Maak van `integration` de unie van het integratiepad en de marker.

    Alles onder `<rootdir>/tests/integration/` hoort bij de integratiegate, ook
    wanneer het bestand alleen een `contract`-, `regression`-, `compliance`-,
    `performance`- of `golden`-marker draagt. Die nodes krijgen hier de
    integrationmarker erbij, zodat pytest ze bij zijn eigen `-m`-selectie
    meeneemt.

    De volgorde is wezenlijk: de native markerdeselectie in
    `_pytest/mark/__init__.py` is een hookimplementatie met standaardprioriteit
    (geen `tryfirst`/`trylast`), en pluggy roept de `tryfirst`-groep daar
    gegarandeerd vóór aan. Er wordt niets gedeselecteerd of verwijderd — alleen
    een marker toegevoegd — en uitsluitend bij dit ene profiel. Nodes met een
    integrationmarker elders in de boom blijven vanzelf staan; een unit-only
    node buiten dit pad wordt niet aangeraakt.

    De wortel is `config.rootpath`, dus de rootdir van de draaiende pytest — het
    project waarvan de tests draaien, niet de repository waaruit de bootstrap
    geladen wordt.
    """
    if os.environ.get("DEF519_PROFILE") != "integration":
        return
    doelmap = os.path.realpath(
        os.path.join(str(config.rootpath), "tests", "integration")
    )
    for item in items:
        pad = getattr(item, "path", None)
        if pad is None:
            continue
        # Met de scheidingstekengrens erbij, anders zou `tests/integration_x`
        # ook als treffer gelden.
        echt = os.path.realpath(str(pad))
        if echt != doelmap and not echt.startswith(doelmap + os.sep):
            continue
        if not any(merk.name == "integration" for merk in item.iter_markers()):
            item.add_marker(pytest.mark.integration)


def pytest_collectreport(report):
    """Collectiefouten en collectie-skips zijn verschillende uitkomsten.

    Een module die zichzelf op moduleniveau overslaat levert geen enkel item op.
    Die uitkomst kan dus per definitie niet uit de nodetelling blijken, terwijl
    JUnit haar wél als overgeslagen geval rapporteert. Zonder deze aparte
    telling zijn de twee administraties niet te reconciliëren.
    """
    if report.failed:
        _verzameld["collectiefouten"] += 1
    elif report.skipped:
        _noteer(_verzameld["collectie_overgeslagen"], report.nodeid)


def pytest_collection_finish(session):
    """Na alle deselecties: `session.items` is de definitieve selectie.

    In `pytest_collection_modifyitems` zou de markerfiltering (`-m`) nog niet
    zijn toegepast en telde de inventaris de hele suite mee.
    """
    for item in session.items:
        _verzameld["items"].append(
            {
                "nodeid": item.nodeid,
                "markers": sorted({merk.name for merk in item.iter_markers()}),
            }
        )


def pytest_runtest_logreport(report):
    """Scheid werkelijk gedraaide bodies van skips, xfails en XPASSes.

    `uitgevoerd` blijft precies wat het was: een `call` die als `passed` of
    `failed` eindigde. Een xfail bereikt zijn body wel, maar pytest levert hem
    als `skipped` met `wasxfail` af en de suite heeft er geen assertie mee
    bewezen; hij telt dus niet als uitvoering, en een xfail-only selectie blijft
    `geen-uitvoering`. Een niet-strikte XPASS eindigt als echte `passed` — die
    body is werkelijk gedraaid en geslaagd, dus die telt wél mee, en wordt
    daarnaast apart zichtbaar gemaakt omdat JUnit hem niet van een gewone pass
    onderscheidt. Een strikte XPASS is bij pytest een gewone `failed` zonder
    `wasxfail` en blijft dus gewoon testfalen.

    Skips worden per unieke node vastgelegd, niet per rapport: een setupskip
    levert alleen een setuprapport, een runtimeskip alleen een callrapport.
    Zonder de setupfase eruit zou de eerste soort volledig onzichtbaar blijven.
    """
    if report.outcome == "skipped" and report.when in ("setup", "call"):
        soort = "xfail" if hasattr(report, "wasxfail") else "overgeslagen"
        _noteer(_verzameld[soort], report.nodeid)
        return
    if report.when != "call":
        return
    if report.outcome in ("passed", "failed"):
        _verzameld["uitgevoerd"] += 1
        if report.outcome == "passed" and hasattr(report, "wasxfail"):
            _noteer(_verzameld["xpassed"], report.nodeid)


def pytest_sessionfinish(session, exitstatus):
    """Schrijf de inventaris: tellingen én de nodes waar ze uit volgen.

    Elke telling staat naast haar node-ids, zodat een consument de inventaris
    per node tegen de JUnit van dezelfde run kan leggen in plaats van twee
    losse totalen te moeten geloven.
    """
    with open(_rapportpad, "w", encoding="utf-8") as bestand:
        json.dump(
            {
                "profiel": os.environ.get("DEF519_PROFILE", ""),
                "items": _verzameld["items"],
                "collectiefouten": _verzameld["collectiefouten"],
                "collectie_overgeslagen": len(_verzameld["collectie_overgeslagen"]),
                "collectie_overgeslagen_nodes": _verzameld["collectie_overgeslagen"],
                "uitgevoerd": _verzameld["uitgevoerd"],
                "overgeslagen": len(_verzameld["overgeslagen"]),
                "overgeslagen_nodes": _verzameld["overgeslagen"],
                "xfail": len(_verzameld["xfail"]),
                "xfail_nodes": _verzameld["xfail"],
                "xpassed": len(_verzameld["xpassed"]),
                "xpassed_nodes": _verzameld["xpassed"],
                "bootstrap": dict(_bewijs),
            },
            bestand,
        )
'''

#: Doorgegeven pytest-opties gaan door een allowlist, niet langs een zwarte
#: lijst: alleen rapportage- en coveragevlaggen mogen erdoor. Alles wat het
#: profiel, de collectie, de configuratie of het pluginregister kan aanpassen
#: (`-m`, `-k`, `-p`, `-c`, `-o`, `--collect-only`, `--ignore`, `--deselect`,
#: paden, ...) valt daarmee vanzelf af, ook opties die pytest later toevoegt.
TOEGESTANE_VLAGGEN = frozenset(
    {
        "-q",
        "-v",
        "-vv",
        "--quiet",
        "--verbose",
        "--cov",
        "--cov-branch",
        "--no-header",
        "--no-summary",
    }
)

#: Opties met een waarde. Uitsluitend de `--optie=waarde`-vorm: een losse
#: waarde als los argument is niet van een testpad te onderscheiden.
TOEGESTANE_VOORVOEGSELS = (
    "--tb=",
    "--durations=",
    "--color=",
    "--junitxml=",
    "--junit-xml=",
    "--cov=",
    "--cov-report=",
    "--cov-config=",
    "--cov-fail-under=",
    "-r",
)


def _meld(status: str, profiel: str, aanroepen: int, **extra: object) -> int:
    """Meld de uitkomst als één machineleesbare regel op een eigen regel.

    De newline vooraf is onvoorwaardelijk. Het pytest-kind deelt deze stdout en
    schrijft zijn voortgangstekens zonder afsluiting; eindigt een run hard of
    wordt hij afgekapt, dan staat er een onafgesloten regel op de stroom. Zonder
    eigen newline plakt de status daarachter (`..[run_profile] status=…`) en
    vindt geen enkele regelgebaseerde lezer hem nog — Make, CI en de gates
    zoeken allemaal op `[run_profile] status=` aan het regelbegin. De kolom van
    het kind is hier niet uit te lezen, dus voorwaardelijk afdrukken kan niet.
    Status, exitcode en velden blijven onveranderd.
    """
    code = EXITCODES[status]
    velden = " ".join(
        f"{naam.replace('_', '-')}={waarde}" for naam, waarde in extra.items()
    )
    print(
        f"\n[run_profile] status={status} exitcode={code} profiel={profiel} "
        f"pytest-aanroepen={aanroepen} {velden}".rstrip(),
        flush=True,
    )
    return code


def _maak_sessieroot() -> Path:
    root = Path(tempfile.mkdtemp(prefix="def519-runner-"))
    (root / EIGENDOMSMARKERING).touch()
    return root


def _maak_werkmap(sessieroot: Path, projectroot: Path) -> Path:
    """Verse CWD met het project als symlink en een lege `data/`."""
    werkmap = sessieroot / "werkmap"
    werkmap.mkdir()
    for naam in ("config", "src"):
        bron = projectroot / naam
        if bron.is_dir():
            (werkmap / naam).symlink_to(bron, target_is_directory=True)
    (werkmap / "data").mkdir()
    return werkmap


def _basetemp_is_veilig(pad: Path) -> bool:
    """pytest leegt `--basetemp`; alleen een nog niet bestaande map is veilig.

    Ook een bestaande *lege* map wordt geweigerd: leeg zijn is geen bewijs van
    eigendom, en de map kan tussen controle en run gevuld raken.
    """
    return not pad.exists()


def _dood_procesgroep(proces: subprocess.Popen) -> None:
    """Beëindig uitsluitend de procesgroep van het eigen kind."""
    try:
        pgid = os.getpgid(proces.pid)
    except ProcessLookupError:
        return
    if pgid == os.getpgid(0):  # pragma: no cover - start_new_session voorkomt dit
        proces.kill()
    else:
        os.killpg(pgid, signal.SIGKILL)
    try:
        proces.wait(timeout=30)
    except subprocess.TimeoutExpired:  # pragma: no cover - SIGKILL faalt niet stil
        pass


def _bouw_omgeving(sessieroot: Path, projectroot: Path, profiel: str) -> dict[str, str]:
    env = dict(os.environ)
    for naam in ("PYTEST_ADDOPTS", "ALLOW_NETWORK"):
        env.pop(naam, None)
    env["DEF519_BOOTSTRAP_ROOT"] = str(Path(__file__).resolve().parents[2])
    env["DEF519_SESSION_ROOT"] = str(sessieroot)
    env["DEF519_PROFILE"] = profiel
    env["DEF519_REPORT"] = str(sessieroot / "inventaris.json")
    env["DEFINITIE_DISABLE_DOTENV"] = "1"
    env["ANTHROPIC_API_KEY"] = "dummy"
    env["OPENAI_API_KEY"] = "dummy"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    bestaand = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{sessieroot}{os.pathsep}{bestaand}" if bestaand else str(sessieroot)
    )
    return env


def _geweigerde_opties(extra_pytest: list[str]) -> list[str]:
    """De doorgegeven argumenten die niet door de allowlist komen."""
    return [
        argument
        for argument in extra_pytest
        if argument not in TOEGESTANE_VLAGGEN
        and not argument.startswith(TOEGESTANE_VOORVOEGSELS)
    ]


def _ontleed_coverage(extra_pytest: list[str]) -> tuple[dict | None, list[str], str]:
    """Splits de coverageopties af van de pytestargumenten.

    De `--cov*`-vlaggen gaan nadrukkelijk NIET door naar pytest: dan zou
    pytest-cov meten en combineren. Ze worden hier vertaald naar de
    Coverage-API-aanroep in het gegenereerde entrypoint. Wat niet ondersteund
    wordt, faalt fail-closed via `verboden-optie`.

    Geeft `(spec of None, resterende pytestargumenten, foutreden of "")`.
    """
    spec: dict = {
        "source": [],
        "branch": False,
        "config_file": None,
        "fail_under": None,
        "xml": [],
        # None = geen expliciete term-override; de configuratie beslist.
        "show_missing": None,
    }
    gevraagd = False
    rest: list[str] = []

    for argument in extra_pytest:
        if argument == "--cov":
            gevraagd = True
        elif argument.startswith("--cov="):
            gevraagd = True
            spec["source"].append(argument.split("=", 1)[1])
        elif argument == "--cov-branch":
            gevraagd = True
            spec["branch"] = True
        elif argument.startswith("--cov-config="):
            gevraagd = True
            spec["config_file"] = argument.split("=", 1)[1]
        elif argument.startswith("--cov-fail-under="):
            gevraagd = True
            waarde = argument.split("=", 1)[1]
            try:
                vloer = float(waarde)
            except ValueError:
                return None, [], f"ongeldige-vloer={waarde}"
            if not math.isfinite(vloer) or not 0.0 <= vloer <= 100.0:
                return None, [], f"ongeldige-vloer={waarde}"
            spec["fail_under"] = vloer
        elif argument.startswith("--cov-report="):
            gevraagd = True
            vorm = argument.split("=", 1)[1]
            if vorm.startswith("xml:"):
                # Absoluut maken vanuit de aanroep-CWD: het kind draait in een
                # verse werkmap en zou een relatief pad daar neerzetten.
                spec["xml"].append(str(Path(vorm.split(":", 1)[1]).resolve()))
            elif vorm == "term-missing":
                spec["show_missing"] = True
            elif vorm == "term":
                spec["show_missing"] = False
            else:
                return None, [], f"rapportvorm-niet-ondersteund={vorm}"
        else:
            rest.append(argument)

    return (spec if gevraagd else None), rest, ""


def _budget_is_bruikbaar(budget: float) -> bool:
    """Een deadline is alleen begrenzend als hij eindig en positief is."""
    return math.isfinite(budget) and budget > 0


def _lees_rapport(pad: Path) -> object | None:
    """De inventaris, of None als hij ontbreekt of geen leesbare JSON is."""
    if not pad.is_file():
        return None
    try:
        return json.loads(pad.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _items(rapport: object) -> list | None:
    if isinstance(rapport, dict) and isinstance(rapport.get("items"), list):
        return rapport["items"]
    return None


def _status_uit_resultaat(returncode: int, rapport: object) -> str:
    if returncode == BOOTSTRAP_EXITCODE:
        return "bootstrapfout"
    if returncode in COV_STATUS:
        # Het entrypoint geeft deze codes pas ná groene tests; een rode suite
        # houdt zijn eigen pytest-exitcode en dus zijn eigen status.
        return COV_STATUS[returncode]
    if isinstance(rapport, dict) and rapport.get("collectiefouten"):
        return "collectiefout"
    items = _items(rapport)
    if returncode == 5 or (items is not None and not items):
        return "lege-selectie"
    return {
        0: "ok",
        1: "testfalen",
        2: "onderbroken",
        3: "intern",
        4: "toolfout",
    }.get(returncode, "intern")


def _bewijs_ontbreekt(rapport: object, sessieroot: Path) -> str | None:
    """De status die een schijnbaar geslaagde run alsnog rood maakt, of None.

    Wordt uitsluitend toegepast op het pad dat anders `ok` zou melden: een
    gewone testfout, collectiefout of toolfout houdt zijn eigen, preciezere
    status. Zo verandert deze controle niets aan bestaande uitkomsten en sluit
    hij enkel de stil-groene paden af.
    """
    if not isinstance(rapport, dict) or _items(rapport) is None:
        return "geen-inventaris"
    uitgevoerd = rapport.get("uitgevoerd")
    if not isinstance(uitgevoerd, int) or isinstance(uitgevoerd, bool):
        return "geen-inventaris"
    bewijs = rapport.get("bootstrap")
    if not isinstance(bewijs, dict) or bewijs.get("gate_actief") is not True:
        return "geen-bootstrapbewijs"
    gemeld = bewijs.get("sessieroot")
    if not isinstance(gemeld, str) or os.path.realpath(gemeld) != os.path.realpath(
        sessieroot
    ):
        return "geen-bootstrapbewijs"
    if uitgevoerd <= 0:
        return "geen-uitvoering"
    return None


def main(argv: list[str] | None = None) -> int:
    ontleder = argparse.ArgumentParser(description=__doc__)
    ontleder.add_argument("profiel", choices=sorted(PROFIELEN))
    ontleder.add_argument(
        "--project-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Project waarvan de tests draaien (default: deze repository).",
    )
    ontleder.add_argument(
        "--inventory", help="Schrijf de collectie-inventaris hierheen."
    )
    ontleder.add_argument("--basetemp", help="pytest-basetemp; moet nog niet bestaan.")
    ontleder.add_argument(
        "--budget",
        type=float,
        default=STANDAARDBUDGET,
        help=f"Harde procesdeadline in seconden (default: {STANDAARDBUDGET:.0f}).",
    )
    argumenten, extra_pytest = ontleder.parse_known_args(argv)

    geweigerd = _geweigerde_opties(extra_pytest)
    if geweigerd:
        return _meld(
            "verboden-optie",
            argumenten.profiel,
            0,
            opties=",".join(geweigerd),
            reden="alleen-rapportage-en-coverage-opties-zijn-toegestaan",
        )
    cov_spec, extra_pytest, cov_fout = _ontleed_coverage(extra_pytest)
    if cov_fout:
        return _meld(
            "verboden-optie",
            argumenten.profiel,
            0,
            opties=cov_fout,
            reden="alleen-xml-term-en-term-missing-worden-ondersteund",
        )
    if not _budget_is_bruikbaar(argumenten.budget):
        return _meld(
            "ongeldig-budget",
            argumenten.profiel,
            0,
            budget=argumenten.budget,
            reden="budget-moet-eindig-en-positief-zijn",
        )

    projectroot = Path(argumenten.project_root).resolve()
    sessieroot = _maak_sessieroot()

    if argumenten.basetemp is not None:
        basetemp = Path(argumenten.basetemp)
        if not _basetemp_is_veilig(basetemp):
            return _meld(
                "onveilige-basetemp",
                argumenten.profiel,
                0,
                basetemp=basetemp,
                reden="map-bestaat-al",
            )
    else:
        basetemp = sessieroot / "pytest-basetemp"

    werkmap = _maak_werkmap(sessieroot, projectroot)
    (sessieroot / "sitecustomize.py").write_text(_SITECUSTOMIZE, encoding="utf-8")
    (sessieroot / "def519_runner_plugin.py").write_text(_PLUGIN, encoding="utf-8")

    pytest_argumenten = [
        "-p",
        "def519_runner_plugin",
        "--rootdir",
        str(projectroot),
        "--basetemp",
        str(basetemp),
        "-m",
        PROFIELEN[argumenten.profiel],
        *extra_pytest,
        str(projectroot / "tests"),
    ]
    ini = projectroot / "pytest.ini"
    if ini.is_file():
        # Vóór `-p`, anders komt de vlag tussen `-p` en zijn waarde te staan.
        pytest_argumenten[0:0] = ["-c", str(ini)]

    if cov_spec is None:
        opdracht = [sys.executable, "-m", "pytest", *pytest_argumenten]
    else:
        # `Coverage.start()` roept intern `erase()` op de eigen datafile aan.
        # Daarom een gegarandeerd nieuw pad in de verse sessieroot: nooit een
        # bestaand `.coverage` gebruiken, overschrijven of verwijderen.
        datamap = sessieroot / "coverage"
        datafile = datamap / ".coverage"
        if datafile.exists():
            return _meld(
                "coverage-data-bestaat-al",
                argumenten.profiel,
                0,
                datafile=datafile,
                reden="bestaande-coveragedata-wordt-nooit-hergebruikt",
            )
        if cov_spec["config_file"] is None:
            standaard = projectroot / "pyproject.toml"
            cov_spec["config_file"] = str(standaard) if standaard.is_file() else False
        else:
            # Vanuit de aanroep-CWD absoluut maken: het kind draait in een verse
            # werkmap, waar een relatief configpad niet bestaat.
            opgegeven = Path(cov_spec["config_file"]).resolve()
            if not opgegeven.is_file():
                return _meld(
                    "coverage-config-onbruikbaar",
                    argumenten.profiel,
                    0,
                    config=cov_spec["config_file"],
                    reden="opgegeven-cov-config-bestaat-niet",
                )
            cov_spec["config_file"] = str(opgegeven)
        datamap.mkdir(parents=True)
        cov_spec["data_file"] = str(datafile)
        entrypad = sessieroot / "def519_coverage_entry.py"
        entrypad.write_text(_COVERAGE_ENTRY, encoding="utf-8")
        opdracht = [sys.executable, str(entrypad), *pytest_argumenten]

    env = _bouw_omgeving(sessieroot, projectroot, argumenten.profiel)
    if cov_spec is not None:
        env["DEF519_COVERAGE"] = json.dumps(cov_spec)
    proces = subprocess.Popen(
        opdracht, cwd=str(werkmap), env=env, start_new_session=True
    )
    try:
        returncode = proces.wait(timeout=argumenten.budget)
    except subprocess.TimeoutExpired:
        pid = proces.pid
        _dood_procesgroep(proces)
        return _meld(
            "budget-overschreden",
            argumenten.profiel,
            1,
            gedood_pid=pid,
            budget=argumenten.budget,
        )

    rapport = _lees_rapport(sessieroot / "inventaris.json")
    if argumenten.inventory and rapport is not None:
        if cov_spec is not None and isinstance(rapport, dict):
            # De meting landt in de verse sessieroot, niet op een vaste plek in
            # de checkout. Zonder deze verwijzing kan CI de werkelijk
            # geproduceerde datafile niet archiveren — en zou daarvoor een
            # generieke `--data-file`-optie of een tweede pad langs de gate
            # nodig zijn.
            rapport["coverage_artefacten"] = {
                "data_file": cov_spec["data_file"],
                "xml": list(cov_spec["xml"]),
                "sessieroot": str(sessieroot),
            }
        Path(argumenten.inventory).write_text(
            json.dumps(rapport, indent=2), encoding="utf-8"
        )

    status = _status_uit_resultaat(returncode, rapport)
    if status == "ok":
        status = _bewijs_ontbreekt(rapport, sessieroot) or "ok"
    items = _items(rapport)
    tellingen = rapport if isinstance(rapport, dict) else {}
    return _meld(
        status,
        argumenten.profiel,
        1,
        pytest_exitcode=returncode,
        verzameld=len(items) if items is not None else 0,
        uitgevoerd=tellingen.get("uitgevoerd", "onbekend"),
        overgeslagen=tellingen.get("overgeslagen", "onbekend"),
        collectie_overgeslagen=tellingen.get("collectie_overgeslagen", "onbekend"),
        xfail=tellingen.get("xfail", "onbekend"),
        xpassed=tellingen.get("xpassed", "onbekend"),
        sessieroot=sessieroot,
    )


if __name__ == "__main__":
    sys.exit(main())
