"""SQLite-containment overleeft een expliciete `Connection`-factory (DEF-519).

Het gat dat deze suite dichtzet
-------------------------------
`tests/offline_bootstrap.py` hangt zijn gate-authorizer aan de verbinding en
vervangt daarna `set_authorizer` als *instantie-attribuut*, zodat een eigen
authorizer van de applicatie samengesteld wordt in plaats van de gate te
verdringen. Dat werkt alleen als de verbinding een `__dict__` heeft.

Een aanroeper die expliciet `factory=sqlite3.Connection` meegeeft, krijgt de
ingebouwde klasse — en die heeft géén `__dict__`. De toewijzing gooide
`AttributeError`, die stil werd opgeslokt. Wat overbleef was een verbinding
waarop `set_authorizer(None)` de gate-authorizer gewoon weghaalt: een
geparametriseerde `ATTACH` naar een pad buiten de sessieroot maakte daarna
echt een bestand aan (root-bewijs: root-gate-boundaries-nhyhq6ll/result.json,
``outcome="allowed"``, ``outside_created=true``).

Veiligheidsontwerp van deze suite
---------------------------------
* **Alleen verse, synthetische doelen.** Elk verboden doel ligt in een boom die
  de test zelf onder `tmp_path` aanmaakt, met een *kunstmatige* repo- en
  home-structuur als fixture. Er wordt geen repository-DB, geen echte `HOME` en
  geen gebruikersdata geopend, gelezen of verwijderd. Het ongetrackte
  incidentbestand `tests/def519-verboden-probe.db` blijft onaangeraakt.
* **Geen prefixvertrouwen.** De sessieroot van het probe-proces én de verboden
  boom liggen allebei onder een tijdelijke map; alleen de eerste is toegestaan.
  Een zustermap is dus net zo verboden als de repository.
* **Kindprocessen met harde buitengrens.** Elke probe draait in een vers proces
  met `PROBE_TIMEOUT` als deadline, zodat een verbinding die blijft hangen de
  suite niet ophoudt. Geen netwerk: de gate zelf sluit dat af.
* **De weigering moet van de gate komen.** Naast het exceptietype toetsen we
  `geweigerd_doel()`; zo kan een willekeurige `DatabaseError` (typefout in de
  SQL, ontbrekende map) een test niet groen maken. En het doel mag daarna niet
  bestaan — de weigering moet effect hebben gehad, niet alleen tekst.

Wat bewust *niet* verandert
---------------------------
De gate onderschept `execute` niet en wikkelt geen eigen klasse om een factory
van de aanroeper heen. Beide zouden bestaand gedrag breken:
`tests/unit/database/test_migratie_io_en_resourcefouten.py` telt op
`type(self)` van een eigen factory, en
`tests/unit/services/test_definition_repository_fail_closed.py` leest de
herkomst van een fout uit het diepste traceback-frame. Die twee contracten
staan hieronder als expliciete regressietests.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from tests.offline_bootstrap import SESSIEROOT_ENV

pytestmark = [pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Harde buitengrens per probe-proces. Ruim genoeg voor een koude interpreter,
#: strak genoeg om een hangende verbinding zichtbaar te maken in plaats van de
#: suite te laten wachten.
PROBE_TIMEOUT = 60

#: Aanroepvormen voor de ingebouwde factory. `connect(db, timeout, detect_types,
#: isolation_level, check_same_thread, factory, cached_statements, uri)` is
#: geldige API: leest de gate de factory alleen uit `kwargs`, dan glipt de
#: positionele vorm erdoor.
BUILTIN_AANROEP = {
    "keyword": 'sqlite3.connect(":memory:", factory=sqlite3.Connection)',
    "positioneel": (
        'sqlite3.connect(":memory:", 5.0, 0, "", True, sqlite3.Connection, 128, False)'
    ),
}

#: SQL-routes die vanuit een toegestane verbinding een bestand aanmaken.
#: `verwacht_doel` volgt het gemeten authorizer-gedrag op SQLite 3.51.1: bij een
#: geparametriseerde ATTACH kent SQLite het pad nog niet, dus is de gate
#: fail-closed met een leeg doel.
SQL_ROUTES = {
    "attach_literal": (
        'conn.execute("ATTACH DATABASE \'" + doel + "\' AS extern")',
        "pad",
    ),
    "attach_parameter": (
        'conn.execute("ATTACH DATABASE ? AS extern", (doel,))',
        "onbekend",
    ),
    "vacuum_into": (
        'conn.execute("VACUUM INTO \'" + doel + "\'")',
        "pad",
    ),
}

#: Een factory zoals productiecode en bestaande tests hem gebruiken: een echte
#: Python-subklasse die `cursor()`, `execute()` en `close()` overschrijft en op
#: `type(self)` telt.
EIGEN_FACTORY = """\
class Eigen(sqlite3.Connection):
    close_calls = 0
    cursor_calls = 0
    geziene_sql = []

    def cursor(self, *rest):
        type(self).cursor_calls += 1
        return super().cursor(*rest)

    def execute(self, sql, *rest):
        type(self).geziene_sql.append(str(sql).split()[0].upper())
        return super().execute(sql, *rest)

    def close(self):
        type(self).close_calls += 1
        super().close()
"""

#: Een factory die géén instantie-attributen toelaat. `__slots__ = ()` op een
#: subklasse van een C-type levert precies dezelfde situatie op als de
#: ingebouwde `sqlite3.Connection`: geen `__dict__`, dus de gate kan zijn staat
#: er niet aan hangen. Anders dan bij de ingebouwde klasse is er hier geen
#: bewaakte vervanging mogelijk — de aanroeper wil déze klasse. Fail-closed dus.
ONVERANDERLIJKE_FACTORY = """\
class Onveranderlijk(sqlite3.Connection):
    __slots__ = ()
    close_calls = 0
    instanties = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        type(self).instanties.append(self)

    def close(self):
        type(self).close_calls += 1
        super().close()
"""

_PROBE_SJABLOON = """\
import json
import sys

sys.path.insert(0, {repo!r})

from tests import offline_bootstrap
from tests.offline_bootstrap import OfflineGateError

sessie = offline_bootstrap.install()
waarnemingen = {{"sessieroot": str(sessie)}}

{body}

with open({uitvoer!r}, "w", encoding="utf-8") as bestand:
    json.dump(waarnemingen, bestand)
"""


def _kindomgeving() -> dict[str, str]:
    """Omgeving voor een probe-proces: dummykeys, geen geërfde sessieroot."""
    env = dict(os.environ)
    env["ANTHROPIC_API_KEY"] = "dummy"
    env["OPENAI_API_KEY"] = "dummy"
    env["DEFINITIE_DISABLE_DOTENV"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Zonder deze twee zou het kind de sessieroot van de lopende run erven en
    # daarmee een andere grens toetsen dan de gate in productie trekt.
    for naam in (SESSIEROOT_ENV, "PYTEST_ADDOPTS"):
        env.pop(naam, None)
    return env


def _draai_probe(tmp_path: Path, body: str, naam: str = "probe") -> dict:
    """Draai `body` in een vers proces met de gate actief en geef de JSON terug.

    In de body zijn `sessie` (de eigen sessieroot) en `waarnemingen` (het
    resultaatobject) beschikbaar. De assertions draaien op die data, niet op
    stdout: een probe die halverwege sterft levert geen half resultaat op maar
    een harde fout.
    """
    script = tmp_path / f"{naam}.py"
    uitvoer = tmp_path / f"{naam}-resultaat.json"
    script.write_text(
        _PROBE_SJABLOON.format(
            repo=str(REPO_ROOT),
            uitvoer=str(uitvoer),
            body=textwrap.dedent(body).strip("\n"),
        ),
        encoding="utf-8",
    )
    resultaat = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(REPO_ROOT),
        env=_kindomgeving(),
        capture_output=True,
        text=True,
        timeout=PROBE_TIMEOUT,
        check=False,
    )
    assert resultaat.returncode == 0, f"probe faalde:\n{resultaat.stderr[-4000:]}"
    return json.loads(uitvoer.read_text(encoding="utf-8"))


def _verboden_boom(tmp_path: Path) -> Path:
    """Verse synthetische map buiten elke sessieroot, met kunstmatige repo/home.

    Fixture-parameter, géén echte HOME of repository-root: er verandert niets
    aan de omgeving van de gebruiker en er wordt geen bestaand bestand
    aangeraakt.
    """
    root = tmp_path / "verboden-root"
    (root / "synthetische-repo" / "data").mkdir(parents=True)
    (root / "synthetische-home" / ".definitie").mkdir(parents=True)
    return root


def _verboden_doel(tmp_path: Path) -> Path:
    return _verboden_boom(tmp_path) / "synthetische-repo" / "data" / "extern.db"


# --- De ingebouwde factory als ontsnappingsroute ----------------------------


@pytest.mark.parametrize("vorm", sorted(BUILTIN_AANROEP))
@pytest.mark.parametrize("route", sorted(SQL_ROUTES))
def test_expliciete_builtin_factory_kan_de_containment_niet_uitzetten(
    tmp_path, vorm, route
):
    """`factory=sqlite3.Connection` plus `set_authorizer(None)` blijft ingesloten.

    Dit is de gemeten ontsnapping: de gate kon zijn `set_authorizer`-wrapper niet
    op de ingebouwde klasse zetten, ving die `AttributeError` stil op, en liet
    daarmee een verbinding achter waarvan de applicatie de authorizer eenvoudig
    kon weghalen. Zowel de keyword- als de positionele aanroepvorm moet dicht
    zijn, en de weigering moet aantoonbaar van de gate komen.
    """
    doel = _verboden_doel(tmp_path)
    aanroep = BUILTIN_AANROEP[vorm]
    uitvoering, verwacht_doel = SQL_ROUTES[route]
    waarnemingen = _draai_probe(
        tmp_path,
        f"""
        import sqlite3

        doel = {str(doel)!r}
        conn = {aanroep}
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        # De applicatie haalt haar eigen authorizer weg. Dat mag: het is
        # bestaand, legitiem gedrag. De gate mag er niet mee verdwijnen.
        conn.set_authorizer(None)
        try:
            {uitvoering}
            waarnemingen["fout"] = None
        except Exception as exc:
            waarnemingen["fout"] = type(exc).__name__
            waarnemingen["bericht"] = str(exc)
        waarnemingen["geweigerd_doel"] = offline_bootstrap.geweigerd_doel(conn)
        waarnemingen["is_connection"] = isinstance(conn, sqlite3.Connection)
        conn.close()
        """,
        naam=f"builtin-{vorm}-{route}",
    )

    assert waarnemingen["fout"] == "DatabaseError", waarnemingen
    # SQLite meldt een weigering bij het prepareren als "not authorized" en bij
    # het uitvoeren (VACUUM INTO) als "authorization denied".
    assert waarnemingen["bericht"] in ("not authorized", "authorization denied")
    if verwacht_doel == "pad":
        assert waarnemingen["geweigerd_doel"] == str(doel)
    else:
        assert waarnemingen["geweigerd_doel"] == ""
    assert waarnemingen["is_connection"] is True
    assert not doel.exists(), "de route heeft alsnog een bestand aangemaakt"


def test_builtin_factory_binnen_de_sessieroot_blijft_volledig_werken(tmp_path):
    """Positieve controle: geen blanket-deny op de ingebouwde factory.

    Een gate die `factory=sqlite3.Connection` simpelweg zou weigeren, maakt de
    vorige test groen zonder iets in te sluiten. Binnen de eigen root moeten
    `ATTACH`, cross-database lezen, `VACUUM INTO` en `:memory:` gewoon echte
    SQLite-semantiek houden, en de verbinding moet een `sqlite3.Connection`
    blijven.
    """
    waarnemingen = _draai_probe(
        tmp_path,
        """
        import sqlite3

        extern = sessie / "tweede.db"
        kopie = sessie / "kopie.db"
        conn = sqlite3.connect(str(sessie / "hoofd.db"), factory=sqlite3.Connection)
        waarnemingen["is_connection"] = isinstance(conn, sqlite3.Connection)
        conn.executescript(
            "CREATE TABLE t (naam TEXT);"
            "INSERT INTO t (naam) VALUES ('rechtspersoon');"
        )
        conn.execute("ATTACH DATABASE '" + str(extern) + "' AS tweede")
        conn.execute("CREATE TABLE tweede.u AS SELECT naam FROM t")
        waarnemingen["via_attach"] = conn.execute(
            "SELECT naam FROM tweede.u"
        ).fetchall()
        conn.execute("DETACH DATABASE tweede")
        conn.commit()
        conn.execute("VACUUM INTO '" + str(kopie) + "'")
        cursor = conn.cursor()
        waarnemingen["via_cursor"] = cursor.execute("SELECT naam FROM t").fetchall()
        cursor.close()
        conn.close()

        geheugen = sqlite3.connect(":memory:", factory=sqlite3.Connection)
        waarnemingen["memory_ok"] = geheugen.execute("SELECT 1").fetchone()[0]
        geheugen.close()

        uit_kopie = sqlite3.connect(str(kopie))
        waarnemingen["uit_kopie"] = uit_kopie.execute("SELECT naam FROM t").fetchall()
        uit_kopie.close()
        """,
        naam="builtin-positief",
    )

    assert waarnemingen["is_connection"] is True
    assert waarnemingen["via_attach"] == [["rechtspersoon"]]
    assert waarnemingen["via_cursor"] == [["rechtspersoon"]]
    assert waarnemingen["memory_ok"] == 1
    assert waarnemingen["uit_kopie"] == [["rechtspersoon"]]


# --- Bestaand gedrag dat de fix niet mag breken -----------------------------


def test_eigen_python_factory_blijft_intact_en_bewaakt(tmp_path):
    """Een eigen factory houdt zijn klasse, zijn overrides én de gate.

    Bestaande tests injecteren faalpaden via een eigen `Connection`-subklasse en
    tellen op `type(self)`; productiecode zet daarnaast een eigen authorizer en
    haalt die weer weg. Alle drie moeten blijven werken, terwijl de containment
    staat blijft.
    """
    doel = _verboden_doel(tmp_path)
    waarnemingen = _draai_probe(
        tmp_path,
        f"""
        import sqlite3

{textwrap.indent(EIGEN_FACTORY, " " * 8)}
        doel = {str(doel)!r}
        conn = sqlite3.connect(str(sessie / "eigen.db"), factory=Eigen)
        waarnemingen["is_eigen_klasse"] = type(conn) is Eigen
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")

        conn.set_authorizer(
            lambda actie, *rest: sqlite3.SQLITE_DENY
            if actie == sqlite3.SQLITE_INSERT
            else sqlite3.SQLITE_OK
        )
        try:
            conn.execute("INSERT INTO t (id) VALUES (1)")
            waarnemingen["eigen_deny_werkt"] = False
        except sqlite3.DatabaseError:
            waarnemingen["eigen_deny_werkt"] = True

        conn.set_authorizer(None)
        conn.execute("INSERT INTO t (id) VALUES (2)")
        cursor = conn.cursor()
        waarnemingen["rijen_na_reset"] = cursor.execute(
            "SELECT count(*) FROM t"
        ).fetchone()[0]
        cursor.close()

        try:
            conn.execute("ATTACH DATABASE '" + doel + "' AS extern")
            waarnemingen["gate_overleefde"] = False
        except sqlite3.DatabaseError:
            waarnemingen["gate_overleefde"] = True
        waarnemingen["geweigerd_doel"] = offline_bootstrap.geweigerd_doel(conn)
        conn.close()
        waarnemingen["close_calls"] = Eigen.close_calls
        waarnemingen["cursor_calls"] = Eigen.cursor_calls
        waarnemingen["geziene_sql"] = Eigen.geziene_sql
        """,
        naam="eigen-factory",
    )

    assert waarnemingen["is_eigen_klasse"] is True
    assert waarnemingen["eigen_deny_werkt"] is True
    assert waarnemingen["rijen_na_reset"] == 1
    assert waarnemingen["gate_overleefde"] is True
    assert waarnemingen["geweigerd_doel"] == str(doel)
    assert waarnemingen["close_calls"] == 1
    assert waarnemingen["cursor_calls"] == 1
    # De override van `execute` is echt gebruikt: de gate wikkelt er niets
    # omheen en onderschept `execute` niet.
    assert waarnemingen["geziene_sql"] == ["CREATE", "INSERT", "INSERT", "ATTACH"]


def test_herkomstdiagnose_wijst_naar_de_aanroeper_niet_naar_de_gate(tmp_path):
    """Het diepste traceback-frame blijft de functie van de applicatie.

    `DefinitionRepository` leest zijn `origin` uit het diepste frame van de
    traceback (src/services/definition_repository.py:1062). Zou de gate `execute`
    onderscheppen om de ingebouwde factory af te dekken, dan meldt die diagnose
    voortaan een gate-functie in plaats van `hard_delete`.
    """
    doel = _verboden_doel(tmp_path)
    waarnemingen = _draai_probe(
        tmp_path,
        f"""
        import sqlite3

        doel = {str(doel)!r}
        conn = sqlite3.connect(":memory:", factory=sqlite3.Connection)
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        conn.set_authorizer(None)


        def hard_delete_achtig(verbinding, pad):
            return verbinding.execute("ATTACH DATABASE '" + pad + "' AS extern")


        try:
            hard_delete_achtig(conn, doel)
            waarnemingen["fout"] = None
        except sqlite3.DatabaseError as exc:
            waarnemingen["fout"] = type(exc).__name__
            spoor = exc.__traceback__
            while spoor is not None and spoor.tb_next is not None:
                spoor = spoor.tb_next
            waarnemingen["herkomst"] = spoor.tb_frame.f_code.co_name
            waarnemingen["herkomst_bestand"] = spoor.tb_frame.f_code.co_filename
        conn.close()
        """,
        naam="herkomst",
    )

    assert waarnemingen["fout"] == "DatabaseError"
    assert waarnemingen["herkomst"] == "hard_delete_achtig"
    assert "offline_bootstrap" not in waarnemingen["herkomst_bestand"]
    assert not doel.exists()


# --- Factories die de gate niet kan bewaken ---------------------------------


def test_factory_zonder_instantie_attributen_faalt_gesloten(tmp_path):
    """Onbewaakbaar betekent geweigerd, niet stilzwijgend toegestaan.

    Bij de ingebouwde klasse mag de gate een bewaakte subklasse in de plaats
    zetten; bij een eigen klasse zónder `__dict__` mag dat niet — de aanroeper
    wil díe klasse. Dan is er maar één veilige uitkomst: `OfflineGateError`, en
    de half-geopende verbinding wordt losgelaten in plaats van teruggegeven.
    """
    waarnemingen = _draai_probe(
        tmp_path,
        f"""
        import sqlite3

{textwrap.indent(ONVERANDERLIJKE_FACTORY, " " * 8)}
        try:
            conn = sqlite3.connect(":memory:", factory=Onveranderlijk)
            waarnemingen["fout"] = None
            waarnemingen["bericht"] = ""
            waarnemingen["oorzaak"] = None
            conn.close()
        except OfflineGateError as exc:
            waarnemingen["fout"] = "OfflineGateError"
            waarnemingen["bericht"] = str(exc)
            oorzaak = exc.__cause__
            waarnemingen["oorzaak"] = None if oorzaak is None else type(oorzaak).__name__
        except Exception as exc:
            waarnemingen["fout"] = type(exc).__name__
            waarnemingen["bericht"] = str(exc)
            waarnemingen["oorzaak"] = None

        waarnemingen["close_calls"] = Onveranderlijk.close_calls
        waarnemingen["aantal_instanties"] = len(Onveranderlijk.instanties)
        if Onveranderlijk.instanties:
            try:
                Onveranderlijk.instanties[0].execute("SELECT 1")
                waarnemingen["hergebruik"] = None
            except Exception as exc:
                waarnemingen["hergebruik"] = type(exc).__name__
        """,
        naam="onbewaakbaar",
    )

    assert waarnemingen["fout"] == "OfflineGateError", waarnemingen
    # De fout benoemt de klasse, zodat een ontwikkelaar niet hoeft te raden
    # welke factory de gate niet kon bewaken.
    assert "Onveranderlijk" in waarnemingen["bericht"]
    assert waarnemingen["oorzaak"] == "AttributeError"
    # De verbinding is echt losgelaten, niet alleen "niet teruggegeven".
    assert waarnemingen["aantal_instanties"] == 1
    assert waarnemingen["close_calls"] == 1
    assert waarnemingen["hergebruik"] == "ProgrammingError"


def test_falende_cleanup_verbergt_de_gatefout_niet(tmp_path):
    """Een `close()` die zelf stukgaat mag de weigering niet overschaduwen.

    Anders zou een factory met een kapotte `close()` de containmentfout kunnen
    maskeren als een gewone `RuntimeError` — en dan lijkt het een bug in de
    applicatie in plaats van een geweigerde factory.
    """
    waarnemingen = _draai_probe(
        tmp_path,
        """
        import sqlite3


        class Weerbarstig(sqlite3.Connection):
            __slots__ = ()

            def close(self):
                raise RuntimeError("sluiten mislukt")


        try:
            sqlite3.connect(":memory:", factory=Weerbarstig)
            waarnemingen["fout"] = None
            waarnemingen["context"] = None
        except OfflineGateError as exc:
            waarnemingen["fout"] = "OfflineGateError"
            context = exc.__context__
            waarnemingen["context"] = None if context is None else type(context).__name__
        except Exception as exc:
            waarnemingen["fout"] = type(exc).__name__
            waarnemingen["context"] = None
        """,
        naam="falende-cleanup",
    )

    assert waarnemingen["fout"] == "OfflineGateError", waarnemingen
    # De mislukte opruiming blijft zichtbaar als context, maar bepaalt niet het
    # type van de fout die de aanroeper ziet.
    assert waarnemingen["context"] == "RuntimeError"
