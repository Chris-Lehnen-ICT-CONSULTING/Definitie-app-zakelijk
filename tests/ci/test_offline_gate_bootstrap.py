"""Contracttests voor de vroege offline-bootstrap en het runnerprofiel (DEF-519).

Waarom deze tests bestaan
-------------------------
De bestaande hermeticiteit in `tests/conftest.py` start *na* de imports: de
autouse-fixture `_disable_network` draait pas als een test begint. Alles wat
tijdens collectie geïmporteerd wordt, draait daarvoor met de geërfde omgeving
van de ontwikkelaar: echte providerkeys, een leesbare `.env` en open sockets.

Veiligheidsontwerp van deze suite
---------------------------------
* **Nooit echt netwerk, ook niet in de RED-fase.** Elk probe-proces vervangt
  het echte transport (`connect`, `connect_ex`, `create_connection`,
  `getaddrinfo`) door een spy die `SpyBereikt` gooit — een `BaseException`,
  zodat een `except Exception` in de probe hem niet kan opslokken. Een groene
  netwerktest eist daarom twee dingen tegelijk: exact `OfflineGateError` én een
  spy die nooit is aangeroepen. Een echte `ConnectionRefusedError` of DNS-fout
  kan een test dus niet groen maken.
* **Nooit echte repo- of gebruikersdata openen.** Verboden DB-doelen liggen in
  een verse synthetische map buiten de sessieroot van het probe-proces, met een
  kunstmatige "repo"- en "home"-structuur als fixture-parameter. Na afloop
  toetst de test dat er geen bestand is aangemaakt. De echte `HOME` wordt nooit
  herdefinieerd.
* **Geen map wordt stilzwijgend vertrouwd.** De sessieroot van het probe-proces
  én de verboden map liggen allebei onder `$TMPDIR`; alleen de eerste is
  toegestaan. Dat sluit een `/tmp`-prefixvertrouwen uit.
* **Geen afhankelijkheid van ongetrackte artefacten.** Elk weigerdoel en elke
  sentinel wordt door de test zelf aangemaakt, zodat de suite ook in een verse
  clone en in CI hetzelfde bewijst. Het incidentbestand
  `tests/def519-verboden-probe.db` blijft als bewijsmateriaal staan maar wordt
  door geen enkele test geopend of gelezen.

Geërfde env-waarden worden nooit geprint: de probes rapporteren besluiten en
foutnamen, geen omgevingswaarden.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests import offline_bootstrap

pytestmark = [pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "scripts" / "testing" / "run_profile.py"

#: Synthetische sleutel: de vórm van een providerkey, zonder geldige waarde.
SYNTHETISCHE_KEY = "sk-ant-api03-DEF519-SYNTHETISCH-GEEN-ECHTE-SLEUTEL"

#: Loopback-poort die niets bedient. Wordt nooit werkelijk benaderd: de spy
#: onderschept elke poging voordat er een pakket kan vertrekken.
LOOPBACK = ("127.0.0.1", 9)

#: Prelude van elk probe-script. Wordt vóór `install()` uitgevoerd, zodat de
#: gate de spy als "origineel transport" opslaat.
_SPY_PRELUDE = '''import socket


class SpyBereikt(BaseException):
    """Sentinel: het échte transport is bereikt. Geen `except Exception` vangt dit."""


spy = {"bereikt": 0}


def _spy(*args, **kwargs):
    spy["bereikt"] += 1
    raise SpyBereikt("echt transport bereikt")


socket.create_connection = _spy
socket.getaddrinfo = _spy
socket.gethostbyname = _spy
socket.gethostbyname_ex = _spy
socket.gethostbyaddr = _spy
socket.socket.connect = _spy
socket.socket.connect_ex = _spy
socket.socket.sendto = _spy
socket.socket.sendmsg = _spy
'''

#: De uitgaande socket-API die de gate moet dekken. De resolver-functies en de
#: verbindingsloze UDP-route zijn net zo goed uitgaand verkeer als `connect`.
GEDEKT_TRANSPORT = [
    "connect",
    "connect_ex",
    "create_connection",
    "getaddrinfo",
    "gethostbyaddr",
    "gethostbyname",
    "gethostbyname_ex",
    "sendmsg",
    "sendto",
]


def _kindomgeving(**extra: str) -> dict[str, str]:
    """Omgeving voor een probe-proces: geërfde providerkey + ALLOW_NETWORK=1.

    Precies de situatie die de gate moet neutraliseren. De sessieroot van de
    lopende testrun wordt weggehaald, zodat het kind zijn eigen root aanmaakt.

    De startupinstallatie van de gate gaat er óók uit. Draait deze suite onder
    `scripts/testing/run_profile.py`, dan staat de sessieroot met een
    gegenereerde `sitecustomize.py` op ``PYTHONPATH`` en is de gate al
    geïnstalleerd vóór de eerste regel van de probe. `install()` is idempotent,
    dus een veilige spy die de probe dáárna op het transport zet, blijft dan
    gewoon staan en de probe meet de installatie van de ouder in plaats van
    haar eigen. Er wordt niets versoepeld: het kind installeert de gate alsnog,
    alleen op het moment dat de probe kiest.
    """
    env = offline_bootstrap.omgeving_zonder_startupinstallatie()
    env["ANTHROPIC_API_KEY"] = SYNTHETISCHE_KEY
    env["OPENAI_API_KEY"] = SYNTHETISCHE_KEY
    env["ALLOW_NETWORK"] = "1"
    for naam in ("DEFINITIE_DISABLE_DOTENV", "DEF519_SESSION_ROOT", "PYTEST_ADDOPTS"):
        env.pop(naam, None)
    env.update(extra)
    return env


def _draai_probe(
    tmp_path: Path, body: str, *, installeer: bool = True, **env_extra: str
) -> dict:
    """Draai `body` in een vers proces met de transportspy én de gate actief.

    De probe schrijft zijn waarnemingen als JSON; de assertions draaien op die
    data. `sessie` is in de body beschikbaar als de eigen sessieroot. Met
    ``installeer=False`` bepaalt de body zelf wanneer en hoe `install()` draait —
    nodig om het gedrag van een *expliciete* sessieroot te toetsen.
    """
    script = tmp_path / "probe.py"
    uitvoer = tmp_path / "resultaat.json"
    opstart = (
        "sessie = offline_bootstrap.install()\n"
        "waarnemingen = {'sessieroot': str(sessie)}\n"
        if installeer
        else "waarnemingen = {}\n"
    )
    script.write_text(
        "import json, sys\n"
        f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
        f"sys.path.insert(0, {str(REPO_ROOT / 'src')!r})\n"
        + _SPY_PRELUDE
        + "from tests import offline_bootstrap\n"
        "from tests.offline_bootstrap import OfflineGateError\n" + opstart + f"{body}\n"
        "waarnemingen['spy_bereikt'] = spy['bereikt']\n"
        f"open({str(uitvoer)!r}, 'w').write(json.dumps(waarnemingen))\n",
        encoding="utf-8",
    )
    resultaat = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(REPO_ROOT),
        env=_kindomgeving(**env_extra),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert resultaat.returncode == 0, f"probe faalde:\n{resultaat.stderr[-4000:]}"
    return json.loads(uitvoer.read_text(encoding="utf-8"))


def _verboden_boom(tmp_path: Path) -> Path:
    """Verse synthetische map buiten elke sessieroot, met kunstmatige repo/home.

    Fixture-parameter, géén echte HOME of repo-root: er verandert niets aan de
    omgeving van de gebruiker en er wordt geen bestaand bestand aangeraakt.
    """
    root = tmp_path / "verboden-root"
    (root / "synthetische-repo" / "data").mkdir(parents=True)
    (root / "synthetische-home" / ".definitie").mkdir(parents=True)
    return root


# --- Omgeving: providerkeys en dotenv ---------------------------------------


def test_geerfde_providerkey_wordt_overschreven_met_dummy(tmp_path):
    """Een echt ogende key in de shell mag nooit in een testproces belanden."""
    waarnemingen = _draai_probe(
        tmp_path,
        "import os\n"
        "waarnemingen['anthropic'] = os.environ['ANTHROPIC_API_KEY']\n"
        "waarnemingen['openai'] = os.environ['OPENAI_API_KEY']\n",
    )
    # 'dummy' is niet-leeg (de niet-leeg-guards van bestaande tests blijven
    # werken) maar heeft geen sk-prefix, dus de skip-guards van de
    # integration-suite blijven de run als offline herkennen.
    assert waarnemingen["anthropic"] == "dummy"
    assert waarnemingen["openai"] == "dummy"
    assert waarnemingen["anthropic"] != SYNTHETISCHE_KEY


def test_impliciete_dotenv_discovery_is_dicht_ook_zonder_opt_out(tmp_path):
    """De opt-out-vlag alleen is geen bescherming; het pad zelf wordt geweigerd.

    De probe leest géén bestaande `.env`: hij toetst het besluit over het echte
    repo- en home-pad en laat de loader daarna los op een synthetisch bestand in
    de verboden map.
    """
    verboden = _verboden_boom(tmp_path)
    nep_env = verboden / "synthetische-repo" / ".env"
    nep_env.write_text("DEF519_MAG_NIET_LADEN=gelekt\n", encoding="utf-8")
    waarnemingen = _draai_probe(
        tmp_path,
        "import os, pathlib, dotenv\n"
        "from config.dotenv_loader import DISABLE_ENV_VAR, load_project_dotenv, project_dotenv_path\n"
        "waarnemingen['opt_out_gezet'] = os.environ.get(DISABLE_ENV_VAR) == '1'\n"
        "waarnemingen['repo_env_toegestaan'] = offline_bootstrap.pad_is_toegestaan(project_dotenv_path())\n"
        "waarnemingen['home_env_toegestaan'] = offline_bootstrap.pad_is_toegestaan(pathlib.Path.home() / '.env')\n"
        "waarnemingen['find_dotenv'] = dotenv.find_dotenv()\n"
        "os.environ.pop(DISABLE_ENV_VAR, None)\n"
        "try:\n"
        f"    load_project_dotenv(pad=pathlib.Path({str(nep_env)!r}), force=True)\n"
        "    waarnemingen['fout'] = None\n"
        "except OfflineGateError:\n"
        "    waarnemingen['fout'] = 'OfflineGateError'\n"
        "except Exception as exc:\n"
        "    waarnemingen['fout'] = type(exc).__name__\n"
        "waarnemingen['gelekt'] = os.environ.get('DEF519_MAG_NIET_LADEN')\n",
    )
    assert waarnemingen["opt_out_gezet"] is True
    assert waarnemingen["repo_env_toegestaan"] is False
    assert waarnemingen["home_env_toegestaan"] is False
    assert waarnemingen["find_dotenv"] == "", "directory-stack-discovery is nog open"
    assert waarnemingen["fout"] == "OfflineGateError"
    assert waarnemingen["gelekt"] is None


def test_expliciete_synthetische_dotenv_blijft_door_de_echte_loader_gaan(tmp_path):
    """`tests/unit/config/test_dotenv_loader.py` moet toetsbaar blijven.

    Een expliciet, door de test aangemaakt `.env` binnen de eigen sessieroot
    gaat door de échte python-dotenv-loader, ook zonder opt-out.
    """
    waarnemingen = _draai_probe(
        tmp_path,
        "import os\n"
        "from config.dotenv_loader import DISABLE_ENV_VAR, load_project_dotenv\n"
        "os.environ.pop(DISABLE_ENV_VAR, None)\n"
        "pad = sessie / 'synthetisch.env'\n"
        "pad.write_text('DEF519_UIT_SESSIE_ENV=geladen\\n', encoding='utf-8')\n"
        "waarnemingen['geladen'] = load_project_dotenv(pad=pad, force=True)\n"
        "waarnemingen['waarde'] = os.environ.get('DEF519_UIT_SESSIE_ENV')\n",
    )
    assert waarnemingen["geladen"] is True
    assert waarnemingen["waarde"] == "geladen"


# --- Netwerk ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("naam", "aanroep"),
    [
        ("create_connection", "socket.create_connection(doel, timeout=1)"),
        ("connect", "socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(doel)"),
        (
            "connect_ex",
            "socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex(doel)",
        ),
        ("getaddrinfo", "socket.getaddrinfo('def519.invalid', 443)"),
        ("gethostbyname", "socket.gethostbyname('def519.invalid')"),
        ("gethostbyname_ex", "socket.gethostbyname_ex('def519.invalid')"),
        ("gethostbyaddr", "socket.gethostbyaddr('127.0.0.1')"),
        (
            "sendto",
            "socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(b'x', doel)",
        ),
        (
            "sendmsg",
            "socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendmsg([b'x'], [], 0, doel)",
        ),
    ],
)
def test_uitgaand_verkeer_faalt_voor_het_echte_transport(tmp_path, naam, aanroep):
    """Ook met ALLOW_NETWORK=1: exact OfflineGateError én spy nooit bereikt.

    De spy-assertie is het echte bewijs: zonder gate zou de aanroep bij het
    (vervangen) transport uitkomen en `SpyBereikt` opleveren, niet een
    toevallige `ConnectionRefusedError` die een zwakkere test groen houdt.
    """
    waarnemingen = _draai_probe(
        tmp_path,
        f"doel = {LOOPBACK!r}\n"
        "try:\n"
        f"    {aanroep}\n"
        "    waarnemingen['fout'] = None\n"
        "except OfflineGateError:\n"
        "    waarnemingen['fout'] = 'OfflineGateError'\n"
        "except SpyBereikt:\n"
        "    waarnemingen['fout'] = 'SpyBereikt'\n"
        "except Exception as exc:\n"
        "    waarnemingen['fout'] = type(exc).__name__\n",
    )
    assert waarnemingen["fout"] == "OfflineGateError", f"{naam}: {waarnemingen}"
    assert waarnemingen["spy_bereikt"] == 0, f"{naam}: echt transport aangeroepen"


def test_de_transportspy_maakt_een_echte_poging_zichtbaar(tmp_path):
    """Discriminatiebewijs: bereikt iets het opgeslagen transport, dan zien we dat.

    Zonder deze test zou `spy_bereikt == 0` ook waar zijn als de spy nooit
    bedraad was.
    """
    waarnemingen = _draai_probe(
        tmp_path,
        "origineel = offline_bootstrap.origineel_transport()\n"
        "waarnemingen['gedekt'] = sorted(origineel)\n"
        "try:\n"
        f"    origineel['create_connection']({LOOPBACK!r}, timeout=1)\n"
        "    waarnemingen['fout'] = None\n"
        "except SpyBereikt:\n"
        "    waarnemingen['fout'] = 'SpyBereikt'\n",
    )
    assert waarnemingen["fout"] == "SpyBereikt"
    assert waarnemingen["spy_bereikt"] == 1
    assert waarnemingen["gedekt"] == GEDEKT_TRANSPORT


# --- SQLite-containment -----------------------------------------------------


@pytest.mark.parametrize("alias", ["sqlite3", "sqlite3.dbapi2"])
@pytest.mark.parametrize(
    ("naam", "relatief"),
    [
        ("synthetische_repo", "synthetische-repo/data/definities.db"),
        ("synthetische_home", "synthetische-home/.definitie/definities.db"),
    ],
)
def test_db_buiten_de_sessieroot_wordt_geweigerd(tmp_path, alias, naam, relatief):
    """Geen enkele alias mag buiten de eigen sessieroot schrijven.

    De verboden map ligt onder dezelfde `$TMPDIR` als de sessieroot: een gate
    die `/tmp` als geheel vertrouwt, faalt hier.
    """
    doel = _verboden_boom(tmp_path) / relatief
    waarnemingen = _draai_probe(
        tmp_path,
        "import sqlite3, sqlite3.dbapi2\n"
        f"doel = {str(doel)!r}\n"
        "try:\n"
        f"    {alias}.connect(doel).close()\n"
        "    waarnemingen['fout'] = None\n"
        "except OfflineGateError:\n"
        "    waarnemingen['fout'] = 'OfflineGateError'\n"
        "except Exception as exc:\n"
        "    waarnemingen['fout'] = type(exc).__name__\n",
    )
    assert waarnemingen["fout"] == "OfflineGateError", f"{naam}/{alias}: {waarnemingen}"
    assert not doel.exists(), "er is alsnog een bestand aangemaakt"


@pytest.mark.parametrize("vorm", ["uri", "uri_met_query", "symlink"])
def test_omweg_via_uri_of_symlink_wordt_geweigerd(tmp_path, vorm):
    """Canonicalisatie: URI-vorm en symlink zijn geen achterdeur.

    De symlink zélf ligt in de toegestane sessieroot en wijst naar buiten; een
    gate die alleen het opgegeven pad bekijkt, laat hem door.
    """
    doel = _verboden_boom(tmp_path) / "synthetische-repo" / "data" / "definities.db"
    if vorm == "symlink":
        aanroep = (
            "link = sessie / 'sluiproute.db'\n"
            f"link.symlink_to({str(doel)!r})\n"
            "doel_arg, uri = str(link), False\n"
        )
    else:
        achtervoegsel = "?mode=rwc" if vorm == "uri_met_query" else ""
        aanroep = f"doel_arg, uri = 'file:' + {str(doel)!r} + {achtervoegsel!r}, True\n"
    waarnemingen = _draai_probe(
        tmp_path,
        "import sqlite3\n" + aanroep + "try:\n"
        "    sqlite3.connect(doel_arg, uri=uri).close()\n"
        "    waarnemingen['fout'] = None\n"
        "except OfflineGateError:\n"
        "    waarnemingen['fout'] = 'OfflineGateError'\n"
        "except Exception as exc:\n"
        "    waarnemingen['fout'] = type(exc).__name__\n",
    )
    assert waarnemingen["fout"] == "OfflineGateError", f"{vorm}: {waarnemingen}"
    assert not doel.exists()


def test_relatief_pad_vanuit_een_repo_achtige_cwd_wordt_geweigerd(tmp_path):
    """Een relatief pad mag niet ontsnappen via de werkmap van het proces.

    De CWD is een verse, synthetische repo-achtige map buiten de sessieroot met
    een eigen sentinel van nul bytes. De echte repo en `HOME` worden niet
    aangeraakt en er wordt geen bestaand artefact geopend.
    """
    nep_repo = _verboden_boom(tmp_path) / "synthetische-repo"
    (nep_repo / "tests").mkdir()
    sentinel = nep_repo / "tests" / "def519-sentinel.db"
    sentinel.touch()
    waarnemingen = _draai_probe(
        tmp_path,
        "import os, sqlite3\n"
        f"os.chdir({str(nep_repo)!r})\n"
        "waarnemingen['cwd_buiten_sessie'] = not os.getcwd().startswith(str(sessie))\n"
        "try:\n"
        "    sqlite3.connect('tests/def519-sentinel.db').close()\n"
        "    waarnemingen['fout'] = None\n"
        "except OfflineGateError:\n"
        "    waarnemingen['fout'] = 'OfflineGateError'\n"
        "except Exception as exc:\n"
        "    waarnemingen['fout'] = type(exc).__name__\n",
    )
    assert waarnemingen["cwd_buiten_sessie"] is True
    assert waarnemingen["fout"] == "OfflineGateError"
    assert sentinel.stat().st_size == 0, "SQLite heeft alsnog een header geschreven"


@pytest.mark.parametrize(
    "doel_expr",
    [
        "':memory:'",
        "'file::memory:?cache=shared'",
        "str(sessie / 'echt.db')",
    ],
)
def test_memory_en_sessie_db_gebruiken_echte_sqlite(tmp_path, doel_expr):
    """Geen DB-mock: schrijven en teruglezen gaat echt door SQLite."""
    waarnemingen = _draai_probe(
        tmp_path,
        "import sqlite3\n"
        f"doel = {doel_expr}\n"
        "conn = sqlite3.connect(doel, uri=doel.startswith('file:'))\n"
        "conn.execute('CREATE TABLE t (id INTEGER PRIMARY KEY, naam TEXT)')\n"
        "conn.execute(\"INSERT INTO t (naam) VALUES ('rechtspersoon')\")\n"
        "conn.commit()\n"
        "waarnemingen['rijen'] = conn.execute('SELECT naam FROM t').fetchall()\n"
        "conn.close()\n",
    )
    assert waarnemingen["rijen"] == [["rechtspersoon"]]


# --- SQL-routes langs connect() heen ----------------------------------------
#
# `ATTACH DATABASE` en `VACUUM INTO` openen of schrijven een bestand vanuit een
# reeds toegestane (memory- of sessie-)verbinding. Een gate op `connect()`
# alleen is daarmee te omzeilen. De SQLite-authorizer sluit dat af *zonder* dat
# de gate elke `execute` hoeft te onderscheppen — dat laatste zou een extra
# Python-frame in elke traceback duwen en de diagnostiek van de repository
# vervalsen (zie tests/unit/services/test_definition_repository_fail_closed.py).
# Gemeten op SQLite 3.51.1: bij een geparametriseerde VACUUM INTO geeft de
# authorizer het échte doelpad, bij een geparametriseerde ATTACH `None` —
# daarom is die laatste fail-closed.


@pytest.mark.parametrize(
    ("naam", "sql", "geparametriseerd", "verwacht_doel"),
    [
        ("attach", "ATTACH DATABASE '{doel}' AS extern", False, "pad"),
        ("attach_parameter", "ATTACH DATABASE ? AS extern", True, "onbekend"),
        ("vacuum_into", "VACUUM INTO '{doel}'", False, "pad"),
        ("vacuum_into_parameter", "VACUUM INTO ?", True, "pad"),
    ],
)
def test_sql_route_naar_een_bestand_buiten_de_sessieroot_wordt_geweigerd(
    tmp_path, naam, sql, geparametriseerd, verwacht_doel
):
    """Vanuit een toegestane memory-verbinding mag geen extern bestand ontstaan."""
    doel = _verboden_boom(tmp_path) / "synthetische-repo" / "data" / "extern.db"
    aanroep = "conn.execute(sql, (doel,))" if geparametriseerd else "conn.execute(sql)"
    waarnemingen = _draai_probe(
        tmp_path,
        "import sqlite3\n"
        f"doel = {str(doel)!r}\n"
        f"sql = {sql!r}.format(doel=doel)\n"
        "conn = sqlite3.connect(':memory:')\n"
        "conn.execute('CREATE TABLE t (id INTEGER PRIMARY KEY)')\n"
        "try:\n"
        f"    {aanroep}\n"
        "    waarnemingen['fout'] = None\n"
        "except Exception as exc:\n"
        "    waarnemingen['fout'] = type(exc).__name__\n"
        "    waarnemingen['bericht'] = str(exc)\n"
        "waarnemingen['geweigerd_doel'] = offline_bootstrap.geweigerd_doel(conn)\n"
        "conn.close()\n",
    )
    assert waarnemingen["fout"] == "DatabaseError", f"{naam}: {waarnemingen}"
    # SQLite meldt een weigering bij het prepareren als "not authorized" en bij
    # het uitvoeren (VACUUM INTO) als "authorization denied". Beide zijn een
    # echte authorizer-weigering; een andere tekst zou een andere fout zijn.
    assert waarnemingen["bericht"] in (
        "not authorized",
        "authorization denied",
    ), f"{naam}: {waarnemingen['bericht']!r}"
    if verwacht_doel == "pad":
        assert waarnemingen["geweigerd_doel"] == str(doel)
    else:
        # SQLite kent het pad hier nog niet; fail-closed met een leeg doel.
        assert waarnemingen["geweigerd_doel"] == ""
    assert not doel.exists(), f"{naam} heeft alsnog een bestand aangemaakt"


def test_gate_overleeft_een_eigen_authorizer_van_de_applicatie(tmp_path):
    """Productiecode mag zijn eigen authorizer zetten én weer weghalen.

    `tests/unit/services/test_definition_repository_fail_closed.py` injecteert
    faalpaden via `set_authorizer(...)` en zet daarna `set_authorizer(None)`.
    Beide moeten werken zónder dat de containment verdwijnt.
    """
    doel = _verboden_boom(tmp_path) / "synthetische-repo" / "data" / "extern.db"
    waarnemingen = _draai_probe(
        tmp_path,
        "import sqlite3\n"
        f"doel = {str(doel)!r}\n"
        "conn = sqlite3.connect(':memory:')\n"
        "conn.execute('CREATE TABLE t (id INTEGER PRIMARY KEY)')\n"
        "conn.set_authorizer(lambda actie, *rest: sqlite3.SQLITE_DENY\n"
        "                    if actie == sqlite3.SQLITE_INSERT else sqlite3.SQLITE_OK)\n"
        "try:\n"
        "    conn.execute('INSERT INTO t (id) VALUES (1)')\n"
        "    waarnemingen['eigen_deny_werkt'] = False\n"
        "except sqlite3.DatabaseError:\n"
        "    waarnemingen['eigen_deny_werkt'] = True\n"
        "conn.set_authorizer(None)\n"
        "conn.execute('INSERT INTO t (id) VALUES (2)')\n"
        "waarnemingen['na_reset_normaal'] = conn.execute('SELECT count(*) FROM t').fetchone()[0]\n"
        "try:\n"
        '    conn.execute("ATTACH DATABASE \'" + doel + "\' AS extern")\n'
        "    waarnemingen['gate_overleefde'] = False\n"
        "except sqlite3.DatabaseError:\n"
        "    waarnemingen['gate_overleefde'] = True\n"
        "waarnemingen['geweigerd_doel'] = offline_bootstrap.geweigerd_doel(conn)\n"
        "conn.close()\n",
    )
    assert waarnemingen["eigen_deny_werkt"] is True
    assert waarnemingen["na_reset_normaal"] == 1
    assert waarnemingen["gate_overleefde"] is True
    assert waarnemingen["geweigerd_doel"] == str(doel)
    assert not doel.exists()


def test_sql_routes_binnen_de_sessieroot_behouden_echte_sqlite_semantiek(tmp_path):
    """Geen blanket-deny: ATTACH en VACUUM INTO blijven binnen de sessie werken.

    Cross-database lezen na ATTACH en een leesbare kopie na VACUUM INTO — dat is
    het gedrag waar migratie- en backupcode op leunt.
    """
    waarnemingen = _draai_probe(
        tmp_path,
        "import sqlite3\n"
        "extern = sessie / 'tweede.db'\n"
        "kopie = sessie / 'kopie.db'\n"
        "conn = sqlite3.connect(str(sessie / 'hoofd.db'))\n"
        "conn.executescript(\n"
        '    "CREATE TABLE t (naam TEXT);"\n'
        "    \"INSERT INTO t (naam) VALUES ('rechtspersoon');\"\n"
        ")\n"
        'conn.execute("ATTACH DATABASE \'" + str(extern) + "\' AS tweede")\n'
        "conn.execute('CREATE TABLE tweede.u AS SELECT naam FROM t')\n"
        "waarnemingen['via_attach'] = conn.execute('SELECT naam FROM tweede.u').fetchall()\n"
        "conn.execute('DETACH DATABASE tweede')\n"
        "conn.commit()\n"
        'conn.execute("VACUUM INTO \'" + str(kopie) + "\'")\n'
        "conn.close()\n"
        "waarnemingen['extern_bestaat'] = extern.is_file()\n"
        "kopie_conn = sqlite3.connect(str(kopie))\n"
        "waarnemingen['uit_kopie'] = kopie_conn.execute('SELECT naam FROM t').fetchall()\n"
        "kopie_conn.close()\n",
    )
    assert waarnemingen["via_attach"] == [["rechtspersoon"]]
    assert waarnemingen["extern_bestaat"] is True
    assert waarnemingen["uit_kopie"] == [["rechtspersoon"]]


# --- De sqlite3-API blijft intact -------------------------------------------

#: Een factory zoals productiecode en bestaande tests hem gebruiken: een echte
#: subklasse die `cursor()`, `execute()` en `close()` overschrijft en op
#: `type(self)` telt. Zie tests/unit/database/test_migratie_io_en_resourcefouten.py.
_EIGEN_FACTORY = (
    "class Eigen(sqlite3.Connection):\n"
    "    close_calls = 0\n"
    "    geziene_sql = []\n"
    "    def execute(self, sql, *rest):\n"
    "        type(self).geziene_sql.append(str(sql).split()[0].upper())\n"
    "        return super().execute(sql, *rest)\n"
    "    def close(self):\n"
    "        type(self).close_calls += 1\n"
    "        super().close()\n"
)


def test_eigen_connection_factory_blijft_de_eigen_klasse(tmp_path):
    """De gate mag `type(conn)` niet veranderen.

    Bestaande tests injecteren faalpaden via een eigen `Connection`-subklasse en
    tellen op `type(self)`. Een gate die daaromheen een eigen subklasse wikkelt,
    laat die tellers stilletjes op nul staan.
    """
    waarnemingen = _draai_probe(
        tmp_path,
        "import sqlite3\n"
        + _EIGEN_FACTORY
        + "conn = sqlite3.connect(str(sessie / 'eigen.db'), factory=Eigen)\n"
        "waarnemingen['is_eigen_klasse'] = type(conn) is Eigen\n"
        "conn.execute('CREATE TABLE t (id INTEGER PRIMARY KEY)')\n"
        "conn.close()\n"
        "waarnemingen['close_calls'] = Eigen.close_calls\n"
        "waarnemingen['geziene_sql'] = Eigen.geziene_sql\n",
    )
    assert waarnemingen["is_eigen_klasse"] is True
    assert waarnemingen["close_calls"] == 1
    assert waarnemingen["geziene_sql"] == ["CREATE"]


def test_gate_werkt_ook_op_een_eigen_connection_factory(tmp_path):
    """Containment mag niet afhangen van de afwezigheid van een eigen factory."""
    doel = _verboden_boom(tmp_path) / "synthetische-repo" / "data" / "extern.db"
    waarnemingen = _draai_probe(
        tmp_path,
        "import sqlite3\n" + _EIGEN_FACTORY + f"doel = {str(doel)!r}\n"
        "conn = sqlite3.connect(str(sessie / 'eigen.db'), factory=Eigen)\n"
        "try:\n"
        '    conn.execute("ATTACH DATABASE \'" + doel + "\' AS extern")\n'
        "    waarnemingen['geweigerd'] = False\n"
        "except sqlite3.DatabaseError:\n"
        "    waarnemingen['geweigerd'] = True\n"
        "waarnemingen['geweigerd_doel'] = offline_bootstrap.geweigerd_doel(conn)\n"
        "conn.close()\n",
    )
    assert waarnemingen["geweigerd"] is True
    assert waarnemingen["geweigerd_doel"] == str(doel)
    assert not doel.exists()


def test_legacy_positionele_connect_argumenten_blijven_werken(tmp_path):
    """`connect(db, timeout, detect_types, isolation_level, check_same_thread,
    factory, cached_statements, uri)` is geldige API en moet correct gelezen.

    De `uri`-vlag staat op positie 7 na `database`; leest de gate hem op de
    verkeerde positie, dan glipt een `file:`-doel buiten de sessieroot erdoor.
    """
    doel = _verboden_boom(tmp_path) / "synthetische-repo" / "data" / "extern.db"
    waarnemingen = _draai_probe(
        tmp_path,
        "import sqlite3\n" + _EIGEN_FACTORY + "conn = sqlite3.connect(\n"
        "    str(sessie / 'positioneel.db'), 5.0, 0, '', True, Eigen, 128, False)\n"
        "waarnemingen['is_eigen_klasse'] = type(conn) is Eigen\n"
        "conn.close()\n"
        "try:\n"
        f"    sqlite3.connect('file:' + {str(doel)!r}, 5.0, 0, '', True,\n"
        "                    sqlite3.Connection, 128, True).close()\n"
        "    waarnemingen['uri_fout'] = None\n"
        "except OfflineGateError:\n"
        "    waarnemingen['uri_fout'] = 'OfflineGateError'\n"
        "except Exception as exc:\n"
        "    waarnemingen['uri_fout'] = type(exc).__name__\n",
    )
    assert waarnemingen["is_eigen_klasse"] is True
    assert waarnemingen["uri_fout"] == "OfflineGateError"
    assert not doel.exists()


# --- Eigenaarschap van de sessieroot ----------------------------------------


def test_geneste_processen_erven_dezelfde_sessieroot(tmp_path):
    """xdist-workers en geneste runs delen één eigenaar zonder nieuwe map.

    Dit is het mechanisme waarmee een kindproces dezelfde offlinegaranties
    krijgt zonder dat het bij echte bestanden kan.
    """
    eerste = _draai_probe(tmp_path, "pass")
    tweede_map = tmp_path / "tweede"
    tweede_map.mkdir()
    tweede = _draai_probe(
        tweede_map,
        "import sqlite3\n"
        "sqlite3.connect(str(sessie / 'gedeeld.db')).close()\n"
        "waarnemingen['bestaat'] = (sessie / 'gedeeld.db').is_file()\n",
        DEF519_SESSION_ROOT=eerste["sessieroot"],
    )
    assert tweede["sessieroot"] == eerste["sessieroot"]
    assert tweede["bestaat"] is True


def test_sessieroot_uit_de_omgeving_zonder_eigendomsbewijs_wordt_genegeerd(tmp_path):
    """Geen env-achterdeur: een willekeurige map wordt niet stilzwijgend eigendom."""
    nep = tmp_path / "niet-van-ons"
    nep.mkdir()
    waarnemingen = _draai_probe(
        tmp_path,
        "import pathlib, sqlite3\n"
        f"nep = pathlib.Path({str(nep)!r})\n"
        "waarnemingen['toegestaan'] = offline_bootstrap.pad_is_toegestaan(nep / 'x.db')\n"
        "try:\n"
        "    sqlite3.connect(str(nep / 'x.db')).close()\n"
        "    waarnemingen['fout'] = None\n"
        "except OfflineGateError:\n"
        "    waarnemingen['fout'] = 'OfflineGateError'\n",
        DEF519_SESSION_ROOT=str(nep),
    )
    assert waarnemingen["sessieroot"] != str(nep)
    assert waarnemingen["toegestaan"] is False
    assert waarnemingen["fout"] == "OfflineGateError"
    assert list(nep.iterdir()) == [], "de nepmap is alsnog gebruikt"


@pytest.mark.parametrize("route", ["own_root", "install"])
def test_bestaande_gevulde_map_wordt_niet_geadopteerd(tmp_path, route):
    """Eigendom moet blijken uit versheid of markering, niet uit "wij vragen het".

    Zonder deze regel maakt één `own_root(pad)` of `install(pad)` van een
    willekeurige gebruikersmap opeens toegestane opslag.
    """
    bezet = tmp_path / "bezette-map"
    bezet.mkdir()
    (bezet / "gebruikersdata.txt").write_text("niet van ons", encoding="utf-8")
    aanroep = (
        "offline_bootstrap.own_root(pad)"
        if route == "own_root"
        else "offline_bootstrap.install(pad)"
    )
    waarnemingen = _draai_probe(
        tmp_path,
        f"pad = {str(bezet)!r}\n"
        "try:\n"
        f"    {aanroep}\n"
        "    waarnemingen['fout'] = None\n"
        "except OfflineGateError:\n"
        "    waarnemingen['fout'] = 'OfflineGateError'\n"
        "except Exception as exc:\n"
        "    waarnemingen['fout'] = type(exc).__name__\n"
        "waarnemingen['toegestaan'] = offline_bootstrap.pad_is_toegestaan(pad)\n",
        installeer=route != "install",
    )
    assert waarnemingen["fout"] == "OfflineGateError", waarnemingen
    assert waarnemingen["toegestaan"] is False
    assert (bezet / "gebruikersdata.txt").read_text(encoding="utf-8") == "niet van ons"
    assert not (bezet / ".def519-session-root").exists(), "markering toch geschreven"


def test_verse_lege_map_kan_wel_expliciet_eigendom_worden(tmp_path):
    """Tegenhanger: zonder deze route kan de runner geen eigen root aanwijzen."""
    vers = tmp_path / "verse-map"
    vers.mkdir()
    waarnemingen = _draai_probe(
        tmp_path,
        "import sqlite3\n"
        f"pad = {str(vers)!r}\n"
        "offline_bootstrap.own_root(pad)\n"
        "waarnemingen['toegestaan'] = offline_bootstrap.pad_is_toegestaan(pad)\n"
        "sqlite3.connect(pad + '/echt.db').close()\n",
    )
    assert waarnemingen["toegestaan"] is True
    assert (vers / ".def519-session-root").is_file()
    assert (vers / "echt.db").is_file()


def test_allow_network_versoepelt_de_verplichte_gate_niet(tmp_path):
    """ALLOW_NETWORK=1 zet niets uit; het liveprofiel is een aparte schakelaar."""
    waarnemingen = _draai_probe(
        tmp_path,
        "import os\n"
        "waarnemingen['gate_actief'] = offline_bootstrap.gate_is_actief()\n"
        "waarnemingen['live'] = offline_bootstrap.live_profiel_actief()\n"
        "waarnemingen['dotenv_uit'] = os.environ.get('DEFINITIE_DISABLE_DOTENV')\n",
    )
    assert waarnemingen["gate_actief"] is True
    assert waarnemingen["live"] is False
    assert waarnemingen["dotenv_uit"] == "1"


# --- Bedrading: de bootstrap draait voor alle applicatie-imports ------------


def test_bootstrap_draait_voor_elke_applicatie_import_in_een_echte_pytestrun(tmp_path):
    """Gedragsbewijs in plaats van een AST-check op het eerste statement.

    `install()` legt vast wélke applicatiepakketten al in `sys.modules` stonden
    op het moment dat de gate dichtging. Was dat er ook maar één, dan heeft
    applicatiecode met de geërfde omgeving kunnen draaien. Een AST-check kan dat
    niet zien (en zou `from __future__` / stdlib-volgorde onmogelijk maken).
    """
    doel = _verboden_boom(tmp_path) / "synthetische-repo" / "data" / "definities.db"
    plugin = tmp_path / "def519_bedrading_plugin.py"
    rapport = tmp_path / "bedrading.json"
    plugin.write_text(
        "import json, os, sqlite3\n"
        "\n"
        "\n"
        "def pytest_collection_finish(session):\n"
        "    from tests import offline_bootstrap\n"
        "    waarnemingen = dict(offline_bootstrap.installatie_rapport())\n"
        "    waarnemingen['anthropic'] = os.environ.get('ANTHROPIC_API_KEY')\n"
        "    waarnemingen['dotenv_uit'] = os.environ.get('DEFINITIE_DISABLE_DOTENV')\n"
        "    try:\n"
        f"        sqlite3.connect({str(doel)!r}).close()\n"
        "        waarnemingen['db_fout'] = None\n"
        "    except Exception as exc:\n"
        "        waarnemingen['db_fout'] = type(exc).__name__\n"
        f"    open({str(rapport)!r}, 'w').write(json.dumps(waarnemingen))\n",
        encoding="utf-8",
    )
    env = _kindomgeving()
    env["PYTHONPATH"] = str(tmp_path)
    resultaat = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "def519_bedrading_plugin",
            "--collect-only",
            "-q",
            "tests/ci/test_check_namespace_collisions.py",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert rapport.is_file(), (
        "plugin schreef geen rapport:\n"
        f"{resultaat.stdout[-3000:]}\n{resultaat.stderr[-3000:]}"
    )
    waarnemingen = json.loads(rapport.read_text(encoding="utf-8"))
    assert waarnemingen["applicatiemodules_bij_installatie"] == []
    assert waarnemingen["gate_actief"] is True
    assert waarnemingen["anthropic"] == "dummy"
    assert waarnemingen["dotenv_uit"] == "1"
    assert waarnemingen["db_fout"] == "OfflineGateError"
    assert not doel.exists()


# --- Runnerprofiel ----------------------------------------------------------


#: Eén synthetische suite met alle vier de markers. De profieltests leiden hun
#: verwachting af uit dit bestand, niet uit de bron van de runner.
MINI_SUITE = {
    "tests/test_scope.py": (
        "import pytest\n\n"
        "@pytest.mark.unit\ndef test_unit():\n    assert True\n\n"
        "@pytest.mark.integration\ndef test_integratie():\n    assert True\n\n"
        "@pytest.mark.acceptance\ndef test_acceptatie():\n    assert True\n\n"
        "@pytest.mark.smoke\ndef test_smoke():\n    assert True\n"
    )
}


def _mini_project(tmp_path: Path, bestanden: dict[str, str]) -> Path:
    """Bouw een vers, synthetisch pytest-project (nooit de echte suite)."""
    root = tmp_path / "miniproject"
    (root / "tests").mkdir(parents=True)
    (root / "pytest.ini").write_text(
        "[pytest]\ntestpaths = tests\naddopts = -q\n"
        "markers =\n    unit: unit\n    integration: integration\n"
        "    acceptance: acceptance\n    smoke: smoke\n",
        encoding="utf-8",
    )
    for naam, inhoud in bestanden.items():
        (root / naam).write_text(inhoud, encoding="utf-8")
    return root


def _uitvoer(resultaat: subprocess.CompletedProcess) -> str:
    return resultaat.stdout + resultaat.stderr


def _draai_runner(
    root: Path, *args: str, timeout: int = 180
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RUNNER), "--project-root", str(root), *args],
        cwd=str(REPO_ROOT),
        env=_kindomgeving(),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


@pytest.mark.parametrize(
    ("profiel", "verwacht"),
    [
        ("unit", {"test_unit"}),
        ("integration", {"test_integratie"}),
        ("acceptance-smoke", {"test_acceptatie", "test_smoke"}),
    ],
)
def test_profiel_selecteert_precies_de_bedoelde_nodes(tmp_path, profiel, verwacht):
    """Gedragsbewijs: verzamelde nodeids en exitcode, geen spiegel van de bron.

    Eén collectie per run: de inventaris komt uit dezelfde pytest-aanroep die de
    tests draait, niet uit een extra `--collect-only`-ronde per profiel.
    """
    root = _mini_project(tmp_path, MINI_SUITE)
    inventaris = tmp_path / "inventaris.json"
    resultaat = _draai_runner(root, profiel, "--inventory", str(inventaris))
    assert resultaat.returncode == 0, _uitvoer(resultaat)
    assert "pytest-aanroepen=1" in _uitvoer(resultaat)
    data = json.loads(inventaris.read_text(encoding="utf-8"))
    assert data["profiel"] == profiel
    assert {item["nodeid"].rsplit("::", 1)[-1] for item in data["items"]} == verwacht
    assert all(item["markers"] for item in data["items"]), data["items"]


def test_sabotage_maakt_precies_het_integratieprofiel_rood(tmp_path):
    """Een opzettelijk falende integratietest breekt die gate en alleen die."""
    root = _mini_project(
        tmp_path,
        MINI_SUITE
        | {
            "tests/test_sabotage.py": "import pytest\n\n"
            "@pytest.mark.integration\ndef test_sabotage():\n    assert 1 == 2\n"
        },
    )
    integratie = _draai_runner(root, "integration")
    unit = _draai_runner(root, "unit")
    assert integratie.returncode != 0
    assert "status=testfalen" in _uitvoer(integratie)
    assert unit.returncode == 0, _uitvoer(unit)


def test_runner_geeft_nonzero_bij_lege_selectie(tmp_path):
    root = _mini_project(
        tmp_path,
        {
            "tests/test_alleen_unit.py": "import pytest\n\n"
            "@pytest.mark.unit\ndef test_a():\n    assert True\n"
        },
    )
    resultaat = _draai_runner(root, "integration")
    assert resultaat.returncode != 0
    assert "status=lege-selectie" in _uitvoer(resultaat)


def test_runner_geeft_nonzero_bij_collectiefout(tmp_path):
    root = _mini_project(
        tmp_path,
        {"tests/test_kapot.py": "import bestaat_niet_def519\n"},
    )
    resultaat = _draai_runner(root, "unit")
    assert resultaat.returncode != 0
    assert "status=collectiefout" in _uitvoer(resultaat)


def test_runner_geeft_nonzero_bij_toolfout(tmp_path):
    """Een onbruikbare pytest-config is een toolfout, geen geslaagde run."""
    root = _mini_project(tmp_path, MINI_SUITE)
    (root / "pytest.ini").write_text(
        "[pytest]\naddopts = --deze-vlag-bestaat-niet\n", encoding="utf-8"
    )
    resultaat = _draai_runner(root, "unit")
    assert resultaat.returncode != 0
    assert "status=toolfout" in _uitvoer(resultaat)


def test_runner_kapt_af_op_het_procesbudget(tmp_path):
    """Harde deadline: een hangende test eindigt nonzero, niet stil groen.

    De runner overleeft zijn eigen kill — bewijs dat alleen de procesgroep van
    het kind wordt geraakt en niet die van de runner zelf.
    """
    root = _mini_project(
        tmp_path,
        {
            "tests/test_hangt.py": "import pytest, time\n\n"
            "@pytest.mark.unit\ndef test_hangt():\n    time.sleep(300)\n"
        },
    )
    start = time.monotonic()
    resultaat = _draai_runner(root, "unit", "--budget", "8", timeout=120)
    verstreken = time.monotonic() - start
    assert resultaat.returncode != 0
    assert verstreken < 60, f"budget niet afgedwongen: {verstreken:.1f}s"
    uitvoer = _uitvoer(resultaat)
    assert "status=budget-overschreden" in uitvoer
    treffer = re.search(r"gedood-pid=(\d+)", uitvoer)
    assert treffer, uitvoer
    with pytest.raises(ProcessLookupError):
        os.kill(int(treffer.group(1)), 0)


#: Het "nieuwe" bestand uit de discoverytest hieronder. Naam en testnaam staan
#: apart zodat de node-id eruit wordt *afgeleid* in plaats van uitgeschreven.
#: Een voluit genoteerde bestandsnaam-plus-nodeketen zou de verwijzingsguard van
#: DEF-676 (tests/unit/validation/test_verwijzingen_bestaan.py) als een belofte
#: over déze repository lezen, terwijl dit bestand pas in `tmp_path` ontstaat.
NIEUW_BESTAND = "tests/test_gloednieuw.py"
NIEUWE_TEST = "test_nieuw"


def test_runner_vindt_nieuwe_tests_zonder_allowlist(tmp_path):
    """Discovery via markers: een nieuw bestand komt vanzelf in de gate."""
    root = _mini_project(
        tmp_path,
        {
            "tests/test_bestaand.py": "import pytest\n\n"
            "@pytest.mark.integration\ndef test_a():\n    assert True\n",
            NIEUW_BESTAND: "import pytest\n\n"
            f"@pytest.mark.integration\ndef {NIEUWE_TEST}():\n    assert True\n",
        },
    )
    inventaris = tmp_path / "inventaris.json"
    resultaat = _draai_runner(root, "integration", "--inventory", str(inventaris))
    assert resultaat.returncode == 0, _uitvoer(resultaat)
    nodes = {
        item["nodeid"]
        for item in json.loads(inventaris.read_text(encoding="utf-8"))["items"]
    }
    verwacht = f"{Path(NIEUW_BESTAND).name}::{NIEUWE_TEST}"
    assert any(verwacht in n for n in nodes), nodes


def test_runner_negeert_pytest_addopts_uit_de_omgeving(tmp_path):
    """De gebruikersomgeving mag een profiel niet oprekken of verzwakken."""
    root = _mini_project(tmp_path, MINI_SUITE)
    inventaris = tmp_path / "inventaris.json"
    resultaat = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--project-root",
            str(root),
            "unit",
            "--inventory",
            str(inventaris),
        ],
        cwd=str(REPO_ROOT),
        env=_kindomgeving(PYTEST_ADDOPTS="-m integration"),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert resultaat.returncode == 0, _uitvoer(resultaat)
    data = json.loads(inventaris.read_text(encoding="utf-8"))
    assert {item["nodeid"].rsplit("::", 1)[-1] for item in data["items"]} == {
        "test_unit"
    }


@pytest.mark.parametrize("gevuld", [True, False])
def test_runner_weigert_een_bestaande_niet_eigen_basetemp(tmp_path, gevuld):
    """pytest leegt `--basetemp`; ook een lege vreemde map wordt niet geadopteerd."""
    bezet = tmp_path / "bestaande-map"
    bezet.mkdir()
    if gevuld:
        (bezet / "niet-van-ons.txt").write_text("data", encoding="utf-8")
    root = _mini_project(tmp_path, MINI_SUITE)
    resultaat = _draai_runner(root, "unit", "--basetemp", str(bezet))
    assert resultaat.returncode != 0
    assert "status=onveilige-basetemp" in _uitvoer(resultaat)
    assert bezet.is_dir()
    if gevuld:
        assert (bezet / "niet-van-ons.txt").is_file(), "map is alsnog geleegd"
    else:
        assert list(bezet.iterdir()) == []


def test_runner_draait_de_gate_in_het_pytest_kindproces(tmp_path):
    """De runner zet CWD, sessieroot en gate op vóór pytest importeert.

    De synthetische suite opent een DB buiten de sessieroot; die test hoort rood
    te worden, en het bestand mag niet bestaan.
    """
    verboden = _verboden_boom(tmp_path) / "synthetische-repo" / "data" / "definities.db"
    root = _mini_project(
        tmp_path,
        {
            "tests/test_db.py": "import pytest, sqlite3\n\n"
            "@pytest.mark.unit\ndef test_verboden_db():\n"
            f"    sqlite3.connect({str(verboden)!r}).close()\n\n"
            "@pytest.mark.unit\ndef test_relatieve_default_db():\n"
            "    import pathlib\n"
            "    pathlib.Path('data').mkdir(exist_ok=True)\n"
            "    sqlite3.connect('data/definities.db').close()\n"
            "    assert pathlib.Path('data/definities.db').is_file()\n"
        },
    )
    resultaat = _draai_runner(root, "unit")
    assert resultaat.returncode != 0
    assert "status=testfalen" in _uitvoer(resultaat)
    assert "OfflineGateError" in _uitvoer(resultaat)
    assert not verboden.exists()
    assert not (root / "data" / "definities.db").exists(), (
        "de relatieve default-DB landde in de projectmap in plaats van in de "
        "verse werkmap van de runner"
    )


# --- De AI-smoke mag onder offline dummyconfiguratie niet starten ------------
#
# De `live`-marker houdt deze node uit de runnerprofielen, maar niet uit élke
# automatische start: de bestaande pre-commit-hook draait `pytest -m smoke`
# zónder `not live`. De eigen skip-guard van de node is daarmee de enige
# overgebleven rem, en die toetste alleen of er íéts in de omgeving stond. De
# offline-bootstrap zet providerkeys hard op `dummy` — niet leeg — dus die guard
# liet de node door.
#
# Deze probe draait de échte node onder de echte gate. De providerfunctie wordt
# vóór elke testbody vervangen door een async spy die zijn bereik registreert en
# meteen een `BaseException`-sentinel gooit; er kan dus ook in de RED-fase geen
# providercall vertrekken. De transportspy van deze suite blijft daarnaast
# gewoon actief. Er wordt niets geassserteerd over `_HAS_API_KEY` zelf: alleen
# over wat pytest werkelijk deed.

#: De echte smoke-node die hier onder de gate wordt gedraaid.
AI_SMOKE_BESTAND = REPO_ROOT / "tests" / "smoke" / "test_smoke_generation.py"
AI_SMOKE_NODE = "test_smoke_generation"

#: Probe-body: draait de echte node via `pytest.main`, met een collectieplugin
#: die uitsluitend `module._run_generation_smoke` vervangt.
AI_SMOKE_PROBE = '''
import pytest as _pytest


class AiSpyBereikt(BaseException):
    """Sentinel: de providerfunctie is bereikt. Geen `except Exception` vangt dit."""


ai_spy = {"bereikt": 0}


async def _ai_spy(*args, **kwargs):
    ai_spy["bereikt"] += 1
    raise AiSpyBereikt("de AI-providerfunctie is bereikt")


class _Waarnemer:
    """Vervangt vóór elke testbody uitsluitend de providerfunctie."""

    def __init__(self):
        self.geselecteerd = []
        self.rapporten = []

    def pytest_collection_modifyitems(self, session, config, items):
        for item in items:
            self.geselecteerd.append(item.nodeid.split("::")[-1])
            module = getattr(item, "module", None)
            if module is not None and hasattr(module, "_run_generation_smoke"):
                module._run_generation_smoke = _ai_spy

    def pytest_runtest_logreport(self, report):
        self.rapporten.append(report.when + ":" + report.outcome)


waarnemer = _Waarnemer()
waarnemingen["pytest_exitcode"] = int(
    _pytest.main(
        [
            SMOKE_BESTAND,
            "-m",
            "smoke",
            "-p",
            "no:randomly",
            "--basetemp",
            str(sessie / "smoke-basetemp"),
            "--no-header",
        ],
        plugins=[waarnemer],
    )
)
waarnemingen["geselecteerd"] = waarnemer.geselecteerd
waarnemingen["rapporten"] = waarnemer.rapporten
waarnemingen["ai_spy_bereikt"] = ai_spy["bereikt"]
'''


def test_ai_smoke_wordt_overgeslagen_onder_offline_dummyconfiguratie(tmp_path):
    """`pytest -m smoke` mag de echte AI-node offline niet uitvoeren.

    Dit is de opdracht van de bestaande pre-commit-hook, ongewijzigd
    nagebootst: het bestand plus `-m smoke`, zonder `not live`. De echte
    skipif-decorator en de echte testfunctie draaien; alleen de providerfunctie
    is vervangen.

    Met de oude guard (alleen "staat er iets in de omgeving?") wordt de node
    uitgevoerd, bereikt de spy en is de uitkomst nonzero — dat is de rode
    oorzaak van deze node. Groen betekent: exact één geselecteerde node, door
    pytest zelf als skip gerapporteerd, geen callfase, en beide spies op nul.

    Dit bewijst niets over de geldigheid van een sleutel of over budget; het
    bewijst alleen dat een dummyconfiguratie de node niet start.
    """
    waarnemingen = _draai_probe(
        tmp_path,
        f"SMOKE_BESTAND = {str(AI_SMOKE_BESTAND)!r}\n" + AI_SMOKE_PROBE,
    )

    assert waarnemingen["pytest_exitcode"] == 0, waarnemingen
    assert waarnemingen["geselecteerd"] == [AI_SMOKE_NODE], waarnemingen
    assert waarnemingen["rapporten"].count("setup:skipped") == 1, waarnemingen
    assert "call:passed" not in waarnemingen["rapporten"], waarnemingen
    assert "call:failed" not in waarnemingen["rapporten"], waarnemingen
    assert waarnemingen["ai_spy_bereikt"] == 0, waarnemingen
    assert waarnemingen["spy_bereikt"] == 0, waarnemingen
