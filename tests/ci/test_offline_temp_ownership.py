"""DEF-519: gewone stdlib-tempbestanden horen binnen de eigen sessieroot.

Waarom deze suite bestaat
-------------------------
De offline-gate weigert elke SQLite-opening buiten een *eigen*, tijdelijke
root. Dat is bewust streng: er is geen prefixvertrouwen op ``/tmp``, dus een
zustermap van de sessieroot is net zo verboden als de repository.

Legitieme code hoeft echter niet te weten dat er een gate draait. Wie een
tijdelijk bestand nodig heeft, schrijft `tempfile.NamedTemporaryFile()` of
`tempfile.TemporaryDirectory()` — en belandde daarmee in de algemene
systeemtempmap, dus buiten de sessieroot. De rootbatch liet dat concreet zien:
de `PerformanceTracker`-fixtures en zes echte compressed-backuptests vielen om
op een `OfflineGateError` terwijl hun tempgebruik volstrekt normaal is.

Het antwoord is *niet* om de padfilter te versoepelen, maar om de normale
stdlib-tempcreatie tijdens de offline sessie naar een verse map ónder de
eigendomsgecontroleerde sessieroot te leiden. Wat "gewoon tijdelijk" is, wordt
zo vanzelf ook "van onszelf".

Wat hier bewezen wordt
----------------------
* positief — een échte tijdelijke SQLite-database, aangemaakt langs de gewone
  `tempfile`-route, gaat open en doet echt werk;
* negatief — een *verse, synthetische* zustermap buiten de sessieroot blijft
  geweigerd; de redirect heeft de systeemtempmap dus niet en bloc toegelaten;
* kindprocessen erven de isolatie, ook zonder zelf te importeren.

Veiligheidsontwerp
------------------
* Elke probe is een vers kindproces met de projectinterpreter; alle paden zijn
  synthetisch en in deze run aangemaakt.
* Er wordt geen enkel bestaand tempbestand gelezen, verplaatst of verwijderd:
  de negatieve controle gebruikt een `TemporaryDirectory` die zij zelf aanmaakt
  en zelf weer opruimt.
* De repository- en gebruikers-DB blijven volledig buiten beeld.
* Geërfde omgevingswaarden worden nooit geprint; de probes rapporteren
  besluiten, paden binnen hun eigen sessieroot en foutnamen.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests import offline_bootstrap

pytestmark = [pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Synthetische sleutel: de vórm van een providerkey, zonder geldige waarde.
SYNTHETISCHE_KEY = "sk-ant-api03-DEF519-SYNTHETISCH-GEEN-ECHTE-SLEUTEL"


def _kindomgeving(**extra: str) -> dict[str, str]:
    """Omgeving voor een probe: de gate installeert pas in de probe zélf.

    Zonder `omgeving_zonder_startupinstallatie` zou onder de runner de
    gegenereerde `sitecustomize.py` de gate al bij interpreterstart zetten. De
    probe meet dan niet meer haar eigen installatie maar die van de ouder — en
    erft bovendien diens tempmap, waardoor de meting nietszeggend wordt.
    """
    env = offline_bootstrap.omgeving_zonder_startupinstallatie()
    env["ANTHROPIC_API_KEY"] = SYNTHETISCHE_KEY
    env["OPENAI_API_KEY"] = SYNTHETISCHE_KEY
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for naam in (
        "DEFINITIE_DISABLE_DOTENV",
        offline_bootstrap.SESSIEROOT_ENV,
        "PYTEST_ADDOPTS",
    ):
        env.pop(naam, None)
    env.update(extra)
    return env


def _draai_probe(tmp_path: Path, body: str, **env_extra: str) -> dict:
    """Draai `body` in een vers proces dat de gate zélf installeert.

    De probe legt vóór installatie vast wat de systeemtempmap was, zodat de
    negatieve controle een "buiten" kan aanwijzen zonder een pad te hardcoderen.
    `sessie` is in de body beschikbaar als de eigen sessieroot.
    """
    script = tmp_path / "probe.py"
    uitvoer = tmp_path / "resultaat.json"
    script.write_text(
        "import json, sys, tempfile\n"
        f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
        f"sys.path.insert(0, {str(REPO_ROOT / 'src')!r})\n"
        "from tests import offline_bootstrap\n"
        "from tests.offline_bootstrap import OfflineGateError\n"
        "systeem_temp = tempfile.gettempdir()\n"
        "gate_vooraf = offline_bootstrap.gate_is_actief()\n"
        "sessie = offline_bootstrap.install()\n"
        "waarnemingen = {\n"
        "    'sessieroot': str(sessie),\n"
        "    'systeem_temp': systeem_temp,\n"
        "    'temp_na_install': tempfile.gettempdir(),\n"
        "    'gate_vooraf': gate_vooraf,\n"
        "}\n" + f"{body}\n"
        f"open({str(uitvoer)!r}, 'w').write(json.dumps(waarnemingen))\n",
        encoding="utf-8",
    )
    resultaat = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(REPO_ROOT),
        env=_kindomgeving(**env_extra),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert resultaat.returncode == 0, f"probe faalde:\n{resultaat.stderr[-4000:]}"
    return json.loads(uitvoer.read_text(encoding="utf-8"))


# --- De redirect zelf -------------------------------------------------------


def test_stdlib_tempcreatie_landt_binnen_de_sessieroot(tmp_path):
    """Elke gewone `tempfile`-route levert een pad dat de gate al toestaat."""
    waarnemingen = _draai_probe(
        tmp_path,
        "import os, tempfile\n"
        "with tempfile.NamedTemporaryFile(suffix='.db') as bestand:\n"
        "    waarnemingen['named'] = bestand.name\n"
        "with tempfile.TemporaryDirectory() as map_:\n"
        "    waarnemingen['tempdir'] = map_\n"
        "handvat, pad = tempfile.mkstemp(suffix='.db')\n"
        "os.close(handvat)\n"
        "waarnemingen['mkstemp'] = pad\n"
        "waarnemingen['mkdtemp'] = tempfile.mkdtemp()\n"
        "waarnemingen['toegestaan'] = {\n"
        "    naam: offline_bootstrap.pad_is_toegestaan(waarnemingen[naam])\n"
        "    for naam in ('named', 'tempdir', 'mkstemp', 'mkdtemp')\n"
        "}\n",
    )
    sessie = Path(waarnemingen["sessieroot"])
    assert waarnemingen["toegestaan"] == {
        "named": True,
        "tempdir": True,
        "mkstemp": True,
        "mkdtemp": True,
    }, waarnemingen
    for naam in ("named", "tempdir", "mkstemp", "mkdtemp"):
        pad = Path(waarnemingen[naam])
        assert pad.is_relative_to(sessie), f"{naam} ligt buiten de sessieroot: {pad}"


def test_de_sessietempmap_is_vers_en_niet_de_systeemtempmap(tmp_path):
    """Discriminatiebewijs: zonder redirect zouden beide waarden gelijk zijn."""
    waarnemingen = _draai_probe(
        tmp_path,
        "import os\n"
        "waarnemingen['temp_env'] = {\n"
        "    naam: os.environ.get(naam) for naam in ('TMPDIR', 'TEMP', 'TMP')\n"
        "}\n"
        "waarnemingen['inhoud'] = sorted(os.listdir(waarnemingen['temp_na_install']))\n",
    )
    sessie = Path(waarnemingen["sessieroot"])
    tempmap = Path(waarnemingen["temp_na_install"])
    assert tempmap != Path(waarnemingen["systeem_temp"])
    assert tempmap.is_relative_to(sessie)
    assert set(waarnemingen["temp_env"].values()) == {str(tempmap)}
    assert waarnemingen["inhoud"] == [], "de tempmap was niet vers"


def test_tijdelijke_sqlite_opening_doet_echt_werk(tmp_path):
    """Positieve controle: de route waarop de rootbatch omviel, werkt nu echt.

    Niet alleen "geen exception": er wordt geschreven, opnieuw geopend en
    teruggelezen, zodat een gate die stilletjes naar `:memory:` zou uitwijken
    hier zou opvallen.
    """
    waarnemingen = _draai_probe(
        tmp_path,
        "import sqlite3, tempfile\n"
        "handvat, pad = tempfile.mkstemp(suffix='.db')\n"
        "import os\n"
        "os.close(handvat)\n"
        "verbinding = sqlite3.connect(pad)\n"
        "verbinding.execute('CREATE TABLE meting (naam TEXT, waarde REAL)')\n"
        "verbinding.execute(\"INSERT INTO meting VALUES ('opstarttijd', 1.5)\")\n"
        "verbinding.commit()\n"
        "verbinding.close()\n"
        "hernieuwd = sqlite3.connect(pad)\n"
        "waarnemingen['rij'] = list(hernieuwd.execute('SELECT * FROM meting'))[0]\n"
        "hernieuwd.close()\n"
        "waarnemingen['db'] = pad\n"
        "waarnemingen['bytes'] = os.path.getsize(pad)\n",
    )
    assert waarnemingen["rij"] == ["opstarttijd", 1.5]
    assert waarnemingen["bytes"] > 0, "een lege file duidt op een in-memory uitwijk"
    assert Path(waarnemingen["db"]).is_relative_to(Path(waarnemingen["sessieroot"]))


def test_verse_zustermap_buiten_de_sessieroot_blijft_verboden(tmp_path):
    """De redirect mag de systeemtempmap niet en bloc hebben toegelaten.

    De zustermap wordt hier zelf aangemaakt en meteen weer opgeruimd; er wordt
    geen bestaand tempbestand aangeraakt.
    """
    waarnemingen = _draai_probe(
        tmp_path,
        "import sqlite3, tempfile\n"
        "with tempfile.TemporaryDirectory(\n"
        "    prefix='def519-zuster-', dir=systeem_temp\n"
        ") as zuster:\n"
        "    doel = zuster + '/verboden.db'\n"
        "    waarnemingen['zuster'] = zuster\n"
        "    waarnemingen['toegestaan'] = offline_bootstrap.pad_is_toegestaan(doel)\n"
        "    try:\n"
        "        sqlite3.connect(doel).close()\n"
        "        waarnemingen['fout'] = None\n"
        "    except OfflineGateError:\n"
        "        waarnemingen['fout'] = 'OfflineGateError'\n"
        "    except Exception as exc:\n"
        "        waarnemingen['fout'] = type(exc).__name__\n"
        "    import os\n"
        "    waarnemingen['aangemaakt'] = os.path.exists(doel)\n",
    )
    assert waarnemingen["toegestaan"] is False, waarnemingen
    assert waarnemingen["fout"] == "OfflineGateError", waarnemingen
    assert waarnemingen["aangemaakt"] is False
    zuster = Path(waarnemingen["zuster"])
    assert not zuster.is_relative_to(Path(waarnemingen["sessieroot"]))
    assert not zuster.exists(), "de synthetische zustermap is niet opgeruimd"


def test_kindproces_erft_de_temp_isolatie(tmp_path):
    """Een kleinkind zonder eigen import houdt dezelfde tempmap.

    Dit is de route waarlangs pytest-workers en door tests gestarte processen
    hun tijdelijke bestanden maken; erft die de isolatie niet, dan lekt het
    tempgebruik alsnog naar de systeemtempmap.
    """
    waarnemingen = _draai_probe(
        tmp_path,
        "import subprocess, sys\n"
        "kleinkind = subprocess.run(\n"
        "    [sys.executable, '-c',\n"
        "     'import tempfile;"
        " print(tempfile.gettempdir());"
        " print(tempfile.mkdtemp())'],\n"
        "    capture_output=True, text=True, timeout=120, check=True,\n"
        ")\n"
        "waarnemingen['kleinkind'] = kleinkind.stdout.split()\n",
    )
    sessie = Path(waarnemingen["sessieroot"])
    gerapporteerd, gemaakt = waarnemingen["kleinkind"]
    assert Path(gerapporteerd) == Path(waarnemingen["temp_na_install"])
    assert Path(gemaakt).is_relative_to(sessie)


# --- De probe meet werkelijk de éérste installatie --------------------------


def test_probe_meet_de_eerste_installatie_ook_onder_de_runnerstartup(tmp_path):
    """Zonder deze eigenschap zijn alle probes hierboven stille no-ops.

    Draait de suite onder `scripts/testing/run_profile.py`, dan zet de
    gegenereerde `sitecustomize.py` de gate al bij interpreterstart. Een probe
    die dat erft, meet niet haar eigen `install()` maar die van de ouder.
    """
    waarnemingen = _draai_probe(tmp_path, "pass")
    assert waarnemingen["gate_vooraf"] is False, waarnemingen
    assert Path(waarnemingen["systeem_temp"]) != Path(waarnemingen["temp_na_install"])


def test_de_startupinstallatie_wordt_gericht_weggehaald(tmp_path):
    """Discriminatiebewijs voor de helper: alleen de gate-route verdwijnt.

    Een gewoon `PYTHONPATH`-deel zonder `sitecustomize.py` blijft staan; het
    deel dat de gate bij interpreterstart zet, gaat weg — samen met de env-var
    waarmee die `sitecustomize` deze module vindt.
    """
    onschuldig = tmp_path / "gewone-pad"
    onschuldig.mkdir()
    startup = tmp_path / "startup-pad"
    startup.mkdir()
    (startup / "sitecustomize.py").write_text("", encoding="utf-8")

    basis = {
        "PYTHONPATH": os.pathsep.join([str(startup), str(onschuldig)]),
        offline_bootstrap.BOOTSTRAPWORTEL_ENV: str(REPO_ROOT),
        "IETS_ANDERS": "blijft",
    }
    schoon = offline_bootstrap.omgeving_zonder_startupinstallatie(basis)

    assert schoon["PYTHONPATH"] == str(onschuldig)
    assert offline_bootstrap.BOOTSTRAPWORTEL_ENV not in schoon
    assert schoon["IETS_ANDERS"] == "blijft"
    assert basis["PYTHONPATH"] == os.pathsep.join([str(startup), str(onschuldig)])
