"""Vroege offline-bootstrap voor de testsuite (DEF-519).

Waarom dit bestand bestaat
--------------------------
De hermeticiteit in `tests/conftest.py` startte pas bij de *eerste test*: de
autouse-fixture `_disable_network` draait na collectie, dus alles wat tijdens
import van testmodules en applicatiecode gebeurt, draaide met de geërfde
omgeving van de ontwikkelaar. Deze module sluit die deur vóór er ook maar één
applicatiepakket geïmporteerd is en wordt daarom als éérste uitgevoerd — via
`tests/conftest.py`, en in de runner al bij interpreterstart via een
gegenereerde `sitecustomize.py`.

Wat `install()` afdwingt
------------------------
1. **Providerkeys.** `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` worden hard op
   ``dummy`` gezet; elke geërfde ``*_API_KEY``/``*_API_TOKEN``/``*_SECRET_KEY``
   wordt geneutraliseerd. ``dummy`` is niet-leeg (bestaande niet-leeg-guards
   blijven werken) maar heeft geen ``sk-``-prefix, zodat skip-guards de run als
   offline herkennen.
2. **Netwerk.** De uitgaande socket-API gooit `OfflineGateError`: naast
   ``connect``/``connect_ex``/``create_connection`` ook de resolverfuncties
   (``getaddrinfo``, ``gethostbyname``, ``gethostbyname_ex``,
   ``gethostbyaddr``) en de verbindingsloze UDP-route (``sendto``,
   ``sendmsg``). ``ALLOW_NETWORK=1`` versoepelt hier niets: dat is de opt-out
   van de oude *fixture*, niet van deze gate.
3. **Dotenv.** Impliciete discovery is dicht (``find_dotenv`` geeft leeg,
   ``load_dotenv(None)`` wordt geweigerd) en elk `.env` buiten de sessieroot
   wordt geweigerd — óók als de opt-outvlag is weggehaald. Een expliciet,
   door de test aangemaakt `.env` binnen de sessieroot gaat gewoon door de
   échte python-dotenv-loader, zodat `tests/unit/config/test_dotenv_loader.py`
   toetsbaar blijft.
4. **SQLite.** Elke opening moet ``:memory:`` zijn of binnen een *eigen* root
   liggen: een map die dit proces zelf heeft aangemaakt (met eigendomsmarkering)
   of expliciet heeft geadopteerd via `own_root()` — bijvoorbeeld de basetemp
   van pytest. Er is géén prefixvertrouwen op ``/tmp``: een zustermap van de
   sessieroot is net zo verboden als de repository. Paden worden
   gecanonicaliseerd, dus een symlink of URI-vorm is geen achterdeur. Ook de
   SQL-routes langs `connect()` heen (``ATTACH DATABASE``, ``VACUUM INTO``)
   worden getoetst — via de SQLite-authorizer, niet via het onderscheppen van
   `execute`. Binnen de sessie blijven ze volledig werken, en een eigen
   `Connection`-factory of authorizer van de applicatie blijft intact. Een
   expliciete ``factory=sqlite3.Connection`` krijgt de bewaakte subklasse (de
   ingebouwde klasse heeft geen ``__dict__`` en zou de gate met
   ``set_authorizer(None)`` laten wegvallen); een factory die de gate om
   diezelfde reden niet kán bewaken, wordt geweigerd in plaats van stil
   toegelaten.
5. **Tempbestanden.** De gewone stdlib-routes (`NamedTemporaryFile`,
   `TemporaryDirectory`, `mkstemp`, `mkdtemp`) wijzen tijdens de sessie naar
   een verse map *binnen* de sessieroot — via `tempfile.tempdir` én
   ``TMPDIR``/``TEMP``/``TMP``, zodat kindprocessen de isolatie erven. Zonder
   dat zou volstrekt normale code (een tijdelijke SQLite-DB, een backup die
   naar een staging-bestand schrijft) op de gate stuklopen terwijl er niets
   mis is. Dit is nadrukkelijk géén versoepeling van punt 4: de map is
   eigendom omdat zij ónder de sessieroot ligt, niet omdat zij in ``/tmp``
   staat. Een verse zustermap van de sessieroot blijft verboden.

Wat deze module *niet* is: een sandbox tegen vijandige code. Het contract is
"testdata is tijdelijk en van onszelf", niet "onbetrouwbare code insluiten".
"""

from __future__ import annotations

import os
import socket
import sqlite3
import sqlite3.dbapi2
import sys
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any

__all__ = [
    "EIGENDOMSMARKERING",
    "SESSIEROOT_ENV",
    "OfflineGateError",
    "gate_is_actief",
    "geweigerd_doel",
    "install",
    "installatie_rapport",
    "live_profiel_actief",
    "omgeving_zonder_startupinstallatie",
    "origineel_transport",
    "own_root",
    "pad_is_toegestaan",
    "session_root",
    "session_tempdir",
]

#: Env-var waarmee kindprocessen (xdist-workers, geneste runs) dezelfde
#: sessieroot erven. Alleen geldig als de map de eigendomsmarkering bevat —
#: anders is het een achterdeur waarmee je elke map tot "van ons" verklaart.
SESSIEROOT_ENV = "DEF519_SESSION_ROOT"

#: Expliciete, apart te activeren liveprofiel-schakelaar. Wordt alleen
#: gerapporteerd; deze module zet de gate nooit uit.
LIVE_PROFIEL_ENV = "DEF519_LIVE_PROFILE"

#: Env-var waarmee de door `scripts/testing/run_profile.py` gegenereerde
#: `sitecustomize.py` deze module vindt. Alleen nodig om hem weer te kunnen
#: uitschakelen voor een kindproces dat de éérste installatie meet.
BOOTSTRAPWORTEL_ENV = "DEF519_BOOTSTRAP_ROOT"

EIGENDOMSMARKERING = ".def519-session-root"

#: Naam van de tempmap binnen de sessieroot. Gewone stdlib-tempbestanden
#: (`NamedTemporaryFile`, `TemporaryDirectory`, `mkstemp`, …) horen daar te
#: landen: legitieme code hoeft niet te weten dat er een gate draait.
TEMPMAP_NAAM = "tempfiles"

#: Env-vars waaruit `tempfile` zijn standaardmap afleidt. Ze worden meegezet
#: zodat kindprocessen dezelfde isolatie erven, ook als ze zelf geen
#: `offline_bootstrap` importeren.
_TEMP_ENV = ("TMPDIR", "TEMP", "TMP")

DUMMY = "dummy"
_ALTIJD_DUMMY = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY")
_GEHEIM_ACHTERVOEGSEL = ("_API_KEY", "_API_TOKEN", "_SECRET_KEY")

#: Pakketten waarvan de aanwezigheid bij installatie betekent dat er al
#: applicatiecode met de geërfde omgeving heeft gedraaid.
APPLICATIEPAKKETTEN = frozenset(
    {
        "anthropic",
        "api",
        "config",
        "database",
        "domain",
        "openai",
        "services",
        "streamlit",
        "toetsregels",
        "ui",
        "validation",
    }
)


class OfflineGateError(RuntimeError):
    """Een testproces probeerde buiten de toegestane, tijdelijke omgeving te treden."""


_sessieroot: Path | None = None
_sessietempdir: Path | None = None
_eigen_roots: list[Path] = []

#: Uitsluitend de socketfuncties zoals ze waren vlak vóór de gate dichtging.
#: Testcode gebruikt dit om aan te tonen dat het échte transport nooit bereikt
#: wordt; andere vervangen functies horen hier bewust niet in.
_origineel_transport: dict[str, Any] = {}
_origineel_overig: dict[str, Any] = {}
_rapport: dict[str, Any] = {
    "gate_actief": False,
    "applicatiemodules_bij_installatie": None,
    "sessieroot": None,
    "sessietempdir": None,
    "systeem_tempdir": None,
}


# --- Padbeoordeling ---------------------------------------------------------


def _canoniek(pad: Path | str) -> Path:
    """Absoluut pad met alle symlinks gevolgd, ook als het bestand nog niet bestaat."""
    return Path(os.path.realpath(os.path.abspath(os.fspath(pad))))


def own_root(
    pad: Path | str, *, toegestane_resten: frozenset[str] = frozenset()
) -> Path:
    """Adopteer `pad` als eigen, tijdelijke root — alleen met eigendomsbewijs.

    Eigendom moet ergens uit blijken, anders maakt één aanroep van een
    willekeurige gebruikersmap opeens toegestane opslag. Geaccepteerd wordt:

    * een map met onze eigendomsmarkering (al eerder door ons aangemaakt, of
      geërfd door een kindproces);
    * een map die nog niet bestaat (wij maken hem);
    * een bestaande map die leeg is, op `toegestane_resten` na. Die uitzondering
      is er voor de basetemp van pytest: die bevat direct na aanmaak het eigen
      `.lock`-bestand van pytest. De aanroeper benoemt zo'n rest expliciet.

    Een bestaande map met andere inhoud wordt geweigerd. Er is bewust geen
    variant die op een padprefix (`/tmp/...`) vertrouwt.
    """
    root = _canoniek(pad)
    if root in _eigen_roots:
        return root
    if (root / EIGENDOMSMARKERING).is_file():
        _eigen_roots.append(root)
        return root
    if not root.exists():
        root.mkdir(parents=True)
    elif not root.is_dir():
        raise OfflineGateError(f"{root} is geen map en kan geen sessieroot zijn")
    else:
        resten = [
            item.name for item in root.iterdir() if item.name not in toegestane_resten
        ]
        if resten:
            raise OfflineGateError(
                f"{root} bestaat al en is niet leeg ({resten[:3]}). Een bestaande "
                "map wordt niet stilzwijgend eigendom: gebruik een verse map of "
                "een map die deze gate zelf heeft aangemaakt."
            )
    (root / EIGENDOMSMARKERING).touch()
    _eigen_roots.append(root)
    return root


def pad_is_toegestaan(pad: Path | str) -> bool:
    """True als `pad` binnen een eigen, tijdelijke root valt."""
    kandidaat = _canoniek(pad)
    return any(
        kandidaat == root or kandidaat.is_relative_to(root) for root in _eigen_roots
    )


def _db_doel_toegestaan(database: Any, uri: bool = False) -> bool:
    """Beoordeel het `database`-argument van `sqlite3.connect` of een ATTACH."""
    if isinstance(database, int):  # bestaande fd; geen padroute
        return False
    doel = os.fsdecode(database) if not isinstance(database, str) else database
    if doel == ":memory:":
        return True
    if doel.startswith("file:"):
        ontleed = urllib.parse.urlparse(doel)
        binnenpad = urllib.parse.unquote(ontleed.path)
        modus = urllib.parse.parse_qs(ontleed.query).get("mode", [])
        if binnenpad in ("", ":memory:") or "memory" in modus:
            return True
        return pad_is_toegestaan(binnenpad)
    if not doel:  # anonieme tijdelijke DB: onzichtbaar pad, dus niet toegestaan
        return False
    return pad_is_toegestaan(doel)


def _weiger_db(doel: Any) -> None:
    raise OfflineGateError(
        f"SQLite-doel {doel!r} ligt buiten de tijdelijke sessieroot "
        f"{_sessieroot}. Gebruik ':memory:' of een pad binnen de sessieroot; "
        "repository- en gebruikersdata zijn in tests niet beschikbaar."
    )


# --- SQL-routes langs connect() heen ----------------------------------------
#
# `ATTACH DATABASE` en `VACUUM INTO` openen of schrijven een bestand vanuit een
# al toegestane verbinding. De SQLite-authorizer dekt beide af, gemeten op
# SQLite 3.51.1 (bewijs: recovery-authorizer-gedrag.json):
#
#   ATTACH literal        -> actie 24, arg1 = het pad
#   ATTACH met parameter  -> actie 24, arg1 = None   (nog niet gebonden)
#   VACUUM INTO literal   -> actie 24, arg1 = het pad
#   VACUUM INTO parameter -> actie 24, arg1 = het pad (autorisatie bij uitvoer)
#
# Alleen de geparametriseerde ATTACH is principieel niet vooraf te toetsen; die
# is daarom fail-closed. SQL-tekst parsen is bewust *niet* nodig.
#
# Even bewust: de gate onderschept `execute` niet. Dat zou een extra
# Python-frame in elke traceback duwen, waardoor de herkomstdiagnose van
# `DefinitionRepository` (deepste frame van de traceback) "_def519_..." zou
# melden in plaats van "hard_delete" — zie
# tests/unit/services/test_definition_repository_fail_closed.py. Containment mag
# de foutrapportage van de applicatie niet vervalsen.


class _GateVerbinding(sqlite3.Connection):
    """Minimale subklasse: geeft een `__dict__` zodat de gate staat kan hangen.

    Gebruikt als de aanroeper geen factory meegeeft *of* expliciet de
    ingebouwde `sqlite3.Connection` vraagt. Die laatste heeft zelf geen
    `__dict__`, dus de gate zou er zijn `set_authorizer`-wrapper niet op kwijt
    kunnen; deze subklasse is functioneel identiek (`isinstance` blijft
    kloppen, geen enkele methode is overschreven) en wél bewaakbaar.

    Geeft de aanroeper een *eigen* klasse mee, dan blijft die ongemoeid —
    bestaande tests tellen op `type(self)` en overschrijven
    `cursor()`/`execute()`/`close()`.
    """


def _bewaak_verbinding(conn: Any) -> None:
    """Zet de gate-authorizer en maak `set_authorizer` samenstellend.

    De authorizer kan geen exception over de C-grens gooien, dus hij noteert het
    geweigerde doel op de verbinding en geeft DENY; SQLite maakt daar een
    `sqlite3.DatabaseError("not authorized")` van. `geweigerd_doel()` maakt
    achteraf zichtbaar dat de weigering van *deze* gate kwam en niet van een
    authorizer van de applicatie zelf.

    `set_authorizer` wordt als *instantie-attribuut* vervangen, niet als
    methode-override op een subklasse: zo blijft `type(conn)` de klasse van de
    aanroeper. Zet de applicatie later `set_authorizer(None)`, dan verdwijnt
    alleen haar eigen callback — de gate blijft staan.

    Lukt die vervanging niet (een factory zonder `__dict__`), dan is de gate op
    deze verbinding niet te handhaven: `set_authorizer(None)` zou de
    gate-authorizer meenemen. Dat is geen degradatie om stil op te vangen, dus
    de verbinding gaat dicht en de aanroeper krijgt een `OfflineGateError`.
    """
    staat: dict[str, Any] = {"schending": None, "gebruiker": None}

    def _autoriseer(actie, arg1, arg2, dbnaam, bron):
        if actie == sqlite3.SQLITE_ATTACH:
            doel = arg1 if arg1 is not None else ""
            if not doel or not _db_doel_toegestaan(doel):
                staat["schending"] = doel
                return sqlite3.SQLITE_DENY
        gebruiker = staat["gebruiker"]
        if gebruiker is not None:
            return gebruiker(actie, arg1, arg2, dbnaam, bron)
        return sqlite3.SQLITE_OK

    sqlite3.Connection.set_authorizer(conn, _autoriseer)

    def _set_authorizer(authorizer_callback):
        staat["gebruiker"] = authorizer_callback
        sqlite3.Connection.set_authorizer(conn, _autoriseer)

    try:
        conn._def519_staat = staat
        conn.set_authorizer = _set_authorizer
    except AttributeError as fout:
        # Fail-closed: de verbinding wordt losgelaten, niet teruggegeven. De
        # mislukte opruiming blijft als `__context__` zichtbaar maar mag het
        # fouttype niet bepalen — anders lijkt een geweigerde factory een
        # gewone applicatiefout.
        try:
            conn.close()
        finally:
            raise OfflineGateError(
                f"Connection-factory {type(conn).__name__} laat geen "
                "instantie-attributen toe, dus de gate kan zijn authorizer er "
                "niet op vasthouden: set_authorizer(None) zou de containment "
                "opheffen. Gebruik een gewone subklasse van sqlite3.Connection "
                "(zonder __slots__) of laat de factory weg."
            ) from fout


def geweigerd_doel(conn: Any) -> str | None:
    """Het laatste doel dat de gate op `conn` weigerde, of None.

    Maakt in tests aantoonbaar dát de weigering van de containment kwam. Een
    lege string betekent: geparametriseerde ATTACH, doel principieel onbekend.
    """
    staat = getattr(conn, "_def519_staat", None)
    return staat["schending"] if staat else None


# --- Gates ------------------------------------------------------------------


def _forceer_dummy_keys() -> None:
    for naam in _ALTIJD_DUMMY:
        os.environ[naam] = DUMMY
    for naam in list(os.environ):
        if naam.endswith(_GEHEIM_ACHTERVOEGSEL):
            os.environ[naam] = DUMMY


def _netwerkgate(naam: str):
    def _geblokkeerd(*args, **kwargs):
        raise OfflineGateError(
            f"socket.{naam} is geblokkeerd door de DEF-519-testgate. "
            "Uitgaand verkeer is in de verplichte profielen niet beschikbaar; "
            "ALLOW_NETWORK=1 heft dit niet op."
        )

    return _geblokkeerd


#: Uitgaande socket-API. De resolverfuncties en de verbindingsloze UDP-route
#: horen er net zo goed bij als `connect`: ook zij sturen pakketten de deur uit.
#: `(module-of-klasse, attribuutnaam)`.
_TRANSPORTPUNTEN = (
    (socket, "create_connection"),
    (socket, "getaddrinfo"),
    (socket, "gethostbyname"),
    (socket, "gethostbyname_ex"),
    (socket, "gethostbyaddr"),
    (socket.socket, "connect"),
    (socket.socket, "connect_ex"),
    (socket.socket, "sendto"),
    (socket.socket, "sendmsg"),
)


def _installeer_netwerkgate() -> None:
    for houder, naam in _TRANSPORTPUNTEN:
        _origineel_transport[naam] = getattr(houder, naam)
        setattr(houder, naam, _netwerkgate(naam))


#: Positie van de optionele parameters van `sqlite3.connect`, geteld ná
#: `database`: timeout, detect_types, isolation_level, check_same_thread,
#: factory, cached_statements, uri. Legacy-code geeft deze positioneel mee.
_FACTORY_POSITIE = 4
_URI_POSITIE = 6


def _bewaakbare_factory(args: tuple, kwargs: dict) -> tuple[tuple, dict]:
    """Vervang een afwezige of ingebouwde factory door `_GateVerbinding`.

    Een *eigen* klasse van de aanroeper blijft ongemoeid: `type(conn)` moet
    zijn klasse zijn. Maar `sqlite3.Connection` zelf heeft geen `__dict__`, en
    zonder plaats voor de gate-staat is `set_authorizer(None)` een uitweg uit
    de containment. Die ene klasse mappen we daarom op de bewaakte subklasse —
    functioneel identiek, geen overschreven methode.

    De factory kan ook positioneel meekomen: `connect(db, timeout,
    detect_types, isolation_level, check_same_thread, factory, ...)` is geldige
    API. Lezen we alleen `kwargs`, dan glipt de positionele vorm erdoor.
    """
    if "factory" in kwargs:
        if kwargs["factory"] is sqlite3.Connection:
            kwargs = {**kwargs, "factory": _GateVerbinding}
    elif len(args) > _FACTORY_POSITIE:
        if args[_FACTORY_POSITIE] is sqlite3.Connection:
            args = (
                args[:_FACTORY_POSITIE]
                + (_GateVerbinding,)
                + args[_FACTORY_POSITIE + 1 :]
            )
    else:
        kwargs = {**kwargs, "factory": _GateVerbinding}
    return args, kwargs


def _installeer_dbgate() -> None:
    origineel_connect = sqlite3.connect
    _origineel_overig["sqlite3.connect"] = origineel_connect

    def _gate_connect(database, *args, **kwargs):
        uri = kwargs.get("uri")
        if uri is None and len(args) > _URI_POSITIE:
            uri = args[_URI_POSITIE]
        if not _db_doel_toegestaan(database, bool(uri)):
            _weiger_db(database)
        args, kwargs = _bewaakbare_factory(args, kwargs)
        conn = origineel_connect(database, *args, **kwargs)
        _bewaak_verbinding(conn)
        return conn

    sqlite3.connect = _gate_connect
    sqlite3.dbapi2.connect = _gate_connect


def _isoleer_tempdir(root: Path) -> Path:
    """Leid de gewone stdlib-tempcreatie naar een verse map ónder `root`.

    `NamedTemporaryFile`, `TemporaryDirectory`, `mkstemp` en `mkdtemp` zijn
    volstrekt normale manieren om tijdelijk werkgeheugen op schijf te vragen.
    Zonder deze redirect landen ze in de algemene systeemtempmap — buiten de
    sessieroot, en dus onder de SQLite-gate verboden. Dat is geen fout van de
    aanroepende code: legitieme productiecode hoeft niet te weten dat er in
    tests een gate draait.

    De oplossing is expliciet géén versoepeling van de padfilter: de map ligt
    ónder de eigendomsgecontroleerde sessieroot, dus `pad_is_toegestaan` blijft
    op eigendom oordelen en een zustermap van de sessieroot blijft verboden.

    Zowel `tempfile.tempdir` als `TMPDIR`/`TEMP`/`TMP` worden gezet. Alleen de
    env-vars volstaat niet — `tempfile` heeft zijn standaardmap op dit moment
    al bepaald en gecachet — en alleen het moduleattribuut evenmin, want dan
    erven kindprocessen de isolatie niet.

    Idempotent voor een geërfde sessieroot: een kindproces adopteert dezelfde
    map in plaats van een tweede aan te maken.
    """
    tempmap = root / TEMPMAP_NAAM
    tempmap.mkdir(exist_ok=True)
    _rapport["systeem_tempdir"] = tempfile.gettempdir()
    tempfile.tempdir = str(tempmap)
    for naam in _TEMP_ENV:
        os.environ[naam] = str(tempmap)
    return tempmap


def _installeer_dotenvgate() -> None:
    try:
        import dotenv
        import dotenv.main
    except ImportError:  # pragma: no cover - dotenv hoort in requirements
        return

    origineel_load = dotenv.load_dotenv
    origineel_values = dotenv.dotenv_values
    _origineel_overig["dotenv.load_dotenv"] = origineel_load

    def _controleer(pad):
        if pad is None:
            raise OfflineGateError(
                "impliciete .env-discovery is uitgeschakeld: geef een expliciet, "
                "door de test aangemaakt pad binnen de sessieroot"
            )
        if not pad_is_toegestaan(pad):
            raise OfflineGateError(
                f".env op {os.fspath(pad)!r} ligt buiten de tijdelijke sessieroot; "
                "de omgeving van de ontwikkelaar mag een test niet beïnvloeden"
            )

    def _gate_load(dotenv_path=None, *args, **kwargs):
        _controleer(dotenv_path if dotenv_path is not None else kwargs.get("stream"))
        return origineel_load(dotenv_path, *args, **kwargs)

    def _gate_values(dotenv_path=None, *args, **kwargs):
        _controleer(dotenv_path)
        return origineel_values(dotenv_path, *args, **kwargs)

    def _geen_discovery(*args, **kwargs):
        return ""

    for module in (dotenv, dotenv.main):
        module.load_dotenv = _gate_load
        module.dotenv_values = _gate_values
        module.find_dotenv = _geen_discovery


# --- Publieke API -----------------------------------------------------------


def _bepaal_sessieroot(expliciet: Path | str | None) -> Path:
    if expliciet is not None:
        return own_root(expliciet)
    geerfd = os.environ.get(SESSIEROOT_ENV)
    if geerfd and (Path(geerfd) / EIGENDOMSMARKERING).is_file():
        return own_root(geerfd)
    # Geen eigendomsbewijs: negeer de env-waarde en maak een verse eigen root.
    return own_root(tempfile.mkdtemp(prefix="def519-sessie-"))


def omgeving_zonder_startupinstallatie(
    basis: dict[str, str] | None = None,
) -> dict[str, str]:
    """Kopie van `basis` waarin déze gate zichzelf niet bij interpreterstart zet.

    Onder `scripts/testing/run_profile.py` staat de sessieroot met een
    gegenereerde `sitecustomize.py` op ``PYTHONPATH``; elk kindproces heeft de
    gate dan al vóór zijn eerste regel geïnstalleerd. Voor een probe die juist
    de *eerste* installatie meet — bijvoorbeeld met een veilige spy op het
    transport, of met een expliciete sessieroot — is dat geen no-op maar een
    stille verandering van het meetobject: `install()` is idempotent en laat de
    spy dan ongemoeid staan.

    Deze functie haalt precies die startuproute weg: elk ``PYTHONPATH``-deel dat
    een `sitecustomize.py` bevat, plus de wortelverwijzing waarmee die
    `sitecustomize` deze module vindt. Er wordt niets aan de gate zelf
    versoepeld: het kindproces installeert hem alsnog, alleen op het moment dat
    de probe kiest. Andere omgevingswaarden blijven ongemoeid en `os.environ`
    van het huidige proces wordt niet aangeraakt.
    """
    schoon = dict(os.environ if basis is None else basis)
    schoon.pop(BOOTSTRAPWORTEL_ENV, None)
    resterend = [
        deel
        for deel in schoon.get("PYTHONPATH", "").split(os.pathsep)
        if deel and not (Path(deel) / "sitecustomize.py").is_file()
    ]
    if resterend:
        schoon["PYTHONPATH"] = os.pathsep.join(resterend)
    else:
        schoon.pop("PYTHONPATH", None)
    return schoon


def install(session_root: Path | str | None = None) -> Path:
    """Zet de gate aan (idempotent) en geef de eigen sessieroot terug."""
    global _sessieroot, _sessietempdir
    if _sessieroot is not None:
        return _sessieroot

    _rapport["applicatiemodules_bij_installatie"] = sorted(
        naam
        for naam in list(sys.modules)
        if naam.partition(".")[0] in APPLICATIEPAKKETTEN
    )
    root = _bepaal_sessieroot(session_root)
    _sessieroot = root
    os.environ[SESSIEROOT_ENV] = str(root)
    _sessietempdir = _isoleer_tempdir(root)

    _forceer_dummy_keys()
    os.environ["DEFINITIE_DISABLE_DOTENV"] = "1"
    _installeer_netwerkgate()
    _installeer_dbgate()
    _installeer_dotenvgate()

    _rapport["gate_actief"] = True
    _rapport["sessieroot"] = str(root)
    _rapport["sessietempdir"] = str(_sessietempdir)
    return root


def session_root() -> Path:
    """De eigen sessieroot; installeert de gate als dat nog niet gebeurd is."""
    return install()


def session_tempdir() -> Path:
    """De map waarheen gewone stdlib-tempcreatie tijdens de sessie wijst."""
    install()
    assert _sessietempdir is not None  # install() zet hem altijd
    return _sessietempdir


def gate_is_actief() -> bool:
    return bool(_rapport["gate_actief"])


def live_profiel_actief() -> bool:
    """Rapporteert de expliciete liveprofiel-schakelaar.

    Bewust alleen rapporterend: geen enkele env-var kan de verplichte gate
    uitzetten. Een liveprofiel is een apart runnerprofiel, geen opt-out.
    """
    return os.environ.get(LIVE_PROFIEL_ENV) == "1"


def origineel_transport() -> dict[str, Any]:
    """De socketfuncties zoals ze waren vlak vóór de gate dichtging."""
    return dict(_origineel_transport)


def installatie_rapport() -> dict[str, Any]:
    return dict(_rapport)
