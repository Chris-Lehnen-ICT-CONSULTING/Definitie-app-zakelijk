#!/usr/bin/env python3
"""
Volledige Regressietest Suite voor DefinitieAgent

Deze uitgebreide test suite valideert alle aspecten van de DefinitieAgent codebase:
- Import functionaliteit en module structuur
- Nederlandse commentaren kwaliteit en consistentie
- Core functionaliteit en workflows
- Database operaties en data integriteit
- API integraties en error handling
- Performance en memory usage
- Configuration management
- Web lookup en externe integraties

Auteur: DefinitieAgent Development Team
Versie: 1.0.0
Datum: Juli 2025
"""

import ast
import asyncio
import contextlib
import importlib
import importlib.util
import logging
import os
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

pytestmark = [pytest.mark.regression]

# `advisory`-dispositie (DEF-519) op zes afzonderlijke nodes in dit bestand; de
# overige nodes bewijzen actief gedrag en blijven onverkort verplicht. Er wordt
# hier niets op bestands- of klasseniveau weggefilterd en er komt geen skip of
# xfail bij; de bestaande optionele skip van `test_logs_module_resolution` blijft
# staan zoals hij is.
# Gedeelde owner: testdispositie-519, inhoudelijke owner niet vastgesteld.
# Gedeelde herbeoordeling: 2026-10-06. De reden en trigger per node staan bij de
# node zelf.

# Geen sys.path-mutaties hier. De oude regels wezen naar `tests/integration/src`
# (bestaat niet) en zetten `tests/integration` op positie 0, vóór `src`. Dat is
# precies het gevaar waartegen tests/conftest.py:38-54 (DEF-439) beschermt:
# `tests/integration/{database,repositories,security,services}` botsen op
# gelijknamige src-packages en zouden die shadowen. `src` staat al op het pad via
# pytest.ini (`pythonpath = src`) en conftest.
# Configureer logging voor tests
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

#: De echte projectroot. Dit bestand ligt in `tests/integration/regression/`,
#: dus `parents[3]` is de checkout. De statische scans hieronder gebruikten
#: `Path(__file__).parent.parent`, wat op `tests/integration` uitkwam; de
#: scanwortel `tests/integration/src` bestaat niet, waardoor elke scan over een
#: lege verzameling liep en groen werd zonder iets te hebben gezien.
PROJECTROOT = Path(__file__).resolve().parents[3]

#: Scanwortel voor de statische bron-/documentatiechecks. Module-globaal, zodat
#: de discriminator onderaan hem tijdelijk kan omzetten en exact terugzetten.
SRC_PAD = PROJECTROOT / "src"


def _verplichte_map(pad: Path) -> Path:
    """De scanwortel moet echt bestaan.

    Een ontbrekende wortel is geen "niets gevonden" maar een kapotte scope: elke
    scan eronder wordt dan leeg-groen.
    """
    if not pad.is_dir():
        raise AssertionError(f"scanwortel ontbreekt: {pad}")
    return pad


def _bronbestanden(wortel: Path) -> list[Path]:
    """Alle Python-bronbestanden onder `wortel`, zonder `__pycache__`.

    Faalt expliciet bij een lege uitkomst: nul bestanden tellen is geen bewijs.
    """
    bestanden = [
        pad for pad in sorted(wortel.rglob("*.py")) if "__pycache__" not in pad.parts
    ]
    if not bestanden:
        raise AssertionError(f"geen Python-bronbestanden onder {wortel}")
    return bestanden


def _verplichte_broninhoud(pad: Path) -> str:
    """Lees een *verplicht* bronbestand en weiger een lege inhoud.

    Een leeg bestand parseert probleemloos en levert nul docstrings en nul
    functies op: `ast.parse` alleen zou zo'n leeggelopen bron groen verklaren.

    Bewust beperkt tot de expliciet vereiste bronnen. Een lege `__init__.py` is
    in `src` een legitieme packagemarkering (er staan er twee) en mag de brede
    scans niet rood maken; die scans bewaken hun scope met een aggregaatteller.
    """
    tekst = pad.read_text(encoding="utf-8")
    if not tekst.strip():
        raise AssertionError(f"leeg bronbestand: {pad}")
    return tekst


def _importeer_modules(namen: list[str]) -> list[tuple[str, str]]:
    """Importeer elke module echt; geef de mislukkingen terug als (naam, fout).

    Bundelen mag — zo zie je in één run álle kapotte modules — maar de melding
    mag nooit verdwijnen. De aanroeper faalt hard op een niet-lege lijst.

    De scope moet niet leeg zijn: nul modules importeren is geen bewijs. De
    guard telt alleen of er íets te meten valt en pint geen aantal, zodat een
    gerichte injectie van twee modules gewoon tot de echte importfout komt.
    """
    assert namen, "lege importscope: er valt niets te importeren"

    mislukt: list[tuple[str, str]] = []
    for naam in namen:
        try:
            module = importlib.import_module(naam)
        # Breed opgevangen omdat een kapotte module net zo goed een SyntaxError
        # of RuntimeError kan gooien; niets gaat verloren, alles komt in de
        # lijst waarop de aanroeper hard faalt.
        except Exception as fout:
            mislukt.append((naam, f"{type(fout).__name__}: {fout}"))
            continue
        if module is None:
            mislukt.append((naam, "module importeert als None"))
    return mislukt


def _module_afwezig(naam: str) -> bool:
    """Is `naam` aantoonbaar afwezig, of bestaat hij (en moet hij dus importeren)?

    `find_spec` op een dotted naam importeert de ouders. Er wordt daarom segment
    voor segment gelopen en **niets** opgevangen: afwezigheid wordt alleen
    aangetoond met een spec die `None` is, of met een gezonde ouder die geen
    package is (dan kán een kind niet bestaan). Elke fout uit de code van een
    bestaande ouder propageert.

    Een `except` met een prefixtoets volstond niet: als het kapotte pakket zijn
    eigen ontbrekende submodule importeert (`import pakket.missing` in
    `__init__.py`), dan ís de ontbrekende naam een prefix van het gevraagde pad
    en werd de kapotte ouder alsnog als "afwezig" afgedaan.
    """
    segmenten = naam.split(".")

    # find_spec op een topniveaunaam lokaliseert alleen; het voert de module
    # niet uit. Vanaf hier bepaalt de ouderspec of dieper zoeken zin heeft.
    spec = importlib.util.find_spec(segmenten[0])
    if spec is None:
        return True

    for grens in range(2, len(segmenten) + 1):
        if spec.submodule_search_locations is None:
            # Gezonde ouder die geen package is: een kind bestaat niet.
            return True
        # Deze aanroep importeert de ouder; faalt diens code, dan propageert dat.
        spec = importlib.util.find_spec(".".join(segmenten[:grens]))
        if spec is None:
            return True

    return False


def _borg_optionele_module(naam: str) -> str:
    """Classificeer een optionele module: afwezig, of aanwezig én importeerbaar.

    Geen blanket `except ImportError`. Bestaat de spec, dan moet de import
    slagen; faalt hij, dan propageert die fout en wordt de node rood. Zo is een
    kapotte dependency onderscheiden van een module die er simpelweg niet is.
    """
    if _module_afwezig(naam):
        return "afwezig"
    importlib.import_module(naam)
    return "aanwezig"


@contextlib.contextmanager
def _tijdelijk_importpad(map_pad: Path, prefixen: list[str]):
    """Zet `map_pad` vooraan op `sys.path` en herstel daarna exact.

    Alleen de expliciet genoemde scratch-`prefixen` worden hersteld: hun vorige
    identiteit als ze er al waren, en anders hun afwezigheid. Elke andere nieuwe
    modulebinding blijft ongemoeid — "nieuw verschenen sinds het begin" is geen
    bewijs dat een binding van ons is. Werkt gelijk bij een geslaagde en bij een
    gefaalde context; er wordt niets van schijf verwijderd.
    """
    origineel_pad = list(sys.path)
    eerdere_bindings = {
        naam: module
        for naam, module in sys.modules.items()
        if any(naam == prefix or naam.startswith(f"{prefix}.") for prefix in prefixen)
    }
    sys.path.insert(0, str(map_pad))
    try:
        yield
    finally:
        sys.path[:] = origineel_pad
        for naam in [
            naam
            for naam in sys.modules
            if any(
                naam == prefix or naam.startswith(f"{prefix}.") for prefix in prefixen
            )
        ]:
            del sys.modules[naam]
        sys.modules.update(eerdere_bindings)


def _scratchmap(prefix: str) -> Path:
    """Verse scratchmap die blijft staan.

    Bewust geen `TemporaryDirectory`/`NamedTemporaryFile(delete=True)`: ook
    automatische context- of destructorcleanup is verwijderen, en deze suite
    verwijdert niets. Wat hier landt valt onder het normale OS-opruimbeleid.
    """
    return Path(tempfile.mkdtemp(prefix=prefix))


def _sluit_eigen_repositoryverbinding(repo: Any) -> None:
    """Sluit uitsluitend de thread-local SQLite-verbinding van déze repository.

    `DefinitieRepository` biedt geen `close()`; de verbinding hangt in
    `DatabaseConnection._thread_local.state`. Alleen de eigen handle gaat dicht,
    nooit een verbinding of singleton van iemand anders.
    """
    toestand = getattr(getattr(repo._db, "_thread_local", None), "state", None)
    if toestand is not None:
        toestand.close()


def _borg_validatieresultaten(
    resultaten: list[str], regel_ids: list[str]
) -> tuple[str, list[str]]:
    """Elke gevraagde regel is werkelijk geëvalueerd.

    Gemeten contract van `validate_definitie` (json_validator_loader.py:219-227):
    `results[0]` is een samenvattingsregel die met `📊` begint, daarna volgt één
    regel per gevraagd ID in dezelfde volgorde. Ontbreekt de bijbehorende
    validator, dan komt er `⏭️ <id>: Validator niet gevonden` terug en telt die
    regel in de samenvatting noch als geslaagd noch als gefaald — een stille
    degradatie die de oude assertie (`result is not None`) niet zag.

    Deze borg eist per gevraagde regel een echte uitkomst (`✅` of `❌`) en
    kruist de samenvatting tegen de getelde regels, zodat een samenvatting die
    niet bij de regels past ook opvalt.
    """
    assert len(resultaten) == len(regel_ids) + 1, (
        f"{len(resultaten)} resultaatregels voor {len(regel_ids)} gevraagde "
        f"regels plus samenvatting: {resultaten}"
    )
    samenvatting, regelresultaten = resultaten[0], resultaten[1:]
    assert samenvatting.startswith("📊"), f"geen samenvattingsregel: {samenvatting}"

    for regel_id, regel in zip(regel_ids, regelresultaten, strict=True):
        assert regel_id in regel, f"resultaatregel hoort niet bij {regel_id}: {regel}"
        assert regel.startswith(("✅", "❌")), (
            f"regel {regel_id} leverde geen echte uitkomst (validator ontbreekt "
            f"of viel om): {regel}"
        )

    aantal_geslaagd = sum(1 for regel in regelresultaten if regel.startswith("✅"))
    assert f"{aantal_geslaagd}/{len(regel_ids)} regels geslaagd" in samenvatting, (
        f"samenvatting past niet bij de {aantal_geslaagd} geslaagde regels: "
        f"{samenvatting}"
    )
    return samenvatting, regelresultaten


def _docstrings(boom: ast.Module) -> list[str]:
    """Alle docstrings in een module: modulehoofd, klassen en functies.

    Via AST in plaats van een `\"\"\"...\"\"\"`-regex. Die regex miste elke
    docstring met enkele quotes en pikte omgekeerd gewone drievoudig
    aangehaalde stringliterals op die helemaal geen docstring zijn.
    """
    gevonden = []
    for knoop in ast.walk(boom):
        if isinstance(
            knoop, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
            docstring = ast.get_docstring(knoop, clean=False)
            if docstring is not None:
                gevonden.append(docstring)
    return gevonden


class TestImportStructure(unittest.TestCase):
    """Test de import structuur en module beschikbaarheid."""

    def setUp(self):
        """Setup voor import tests."""
        self.core_modules = [
            "main",
            "ui.tabbed_interface",
            "ui.session_state",
            "database.definitie_repository",
            # Nieuwe architectuur kernmodules
            "services.service_factory",
            "services.container",
            "services.interfaces",
            # Validatie en utiliteiten
            # `ai_toetser.modular_toetser` bestond niet meer; de AI-validatie is
            # verhuisd naar services/. Actueel equivalent op deze lijst:
            "services.validation.modular_validation_service",
            "validation.definitie_validator",
            "services.modern_web_lookup_service",
            "config.config_manager",
            "utils.cache",
            "utils.smart_rate_limiter",
        ]

        self.optional_modules = [
            "document_processing.document_processor",
            "voorbeelden.unified_voorbeelden",
        ]

    def test_core_modules_import(self):
        """Test dat alle core modules correct importeren.

        De lijst blijft de bestaande vaste 13; er wordt niets repo-breed
        geïmporteerd. Eén mapping was nodig: `ai_toetser.modular_toetser` is uit
        de codebase verdwenen en het actuele equivalent op deze lijst is
        `services.validation.modular_validation_service`.

        Fouten worden gebundeld zodat één run alle kapotte modules toont, maar
        de eindassert faalt hard — geen fout-als-waarschuwing.
        """
        mislukt = _importeer_modules(self.core_modules)

        assert not mislukt, (
            f"{len(mislukt)} van {len(self.core_modules)} core modules faalden "
            f"bij import: {mislukt}"
        )

    def test_optional_modules_graceful_degradation(self):
        """Test dat optionele modules graceful degraderen.

        Alleen een module die er aantoonbaar niet is, mag ontbreken. Bestaat de
        spec, dan moet de import slagen; een kapotte dependency propageert en
        maakt deze node rood in plaats van als "niet beschikbaar" te passeren.
        """
        assert (
            self.optional_modules
        ), "lege importscope: er valt geen optionele module te classificeren"

        statussen = {
            naam: _borg_optionele_module(naam) for naam in self.optional_modules
        }

        assert set(statussen) == set(self.optional_modules), statussen
        assert all(
            status in {"afwezig", "aanwezig"} for status in statussen.values()
        ), statussen

    def test_logs_module_resolution(self):
        """Test dat logs module correct wordt opgelost (optioneel).

        De bestaande optional-dispositie blijft, maar wordt nu bewezen in plaats
        van aangenomen: pas als de module aantoonbaar afwezig is (geen kapotte
        dependency) volgt de skip. Bestaat hij weer, dan moet de import slagen.
        """
        naam = "logs.application.log_definitie"

        if _module_afwezig(naam):
            self.skipTest(
                f"{naam} is aantoonbaar afwezig in deze checkout (geen kapotte "
                "dependency). DEF-519-testdispositie: inhoudelijke owner niet "
                "vastgesteld, trigger = vrijgegeven herstel, vervalt 2026-10-06."
            )

        module = importlib.import_module(naam)
        logger_instance = module.get_logger("test")
        assert logger_instance is not None
        assert callable(module.log_definitie)

    # advisory: het packagingbeleid "elke map onder src is een package" is nooit
    # geleverd en wordt niet nagebouwd voor groen. Trigger: vrijgegeven herstel
    # van het packagingbeleid.
    @pytest.mark.advisory
    def test_package_init_files(self):
        """Test dat alle packages __init__.py bestanden hebben.

        Draait op de echte `src`-wortel en toont het aantal onderzochte mappen,
        zodat een leeggelopen scope niet meer als groen wegkomt.

        Bekende positieve rode uitkomst: het packagingbeleid "elke map onder
        `src` is een package" is nooit geleverd. Dat wordt hier niet
        weggefilterd. Dispositie: DEF-519-testdispositie, inhoudelijke owner
        niet vastgesteld, trigger = vrijgegeven herstel, vervalt 2026-10-06.
        """
        src_path = _verplichte_map(SRC_PAD)
        _bronbestanden(src_path)  # borgt dat de wortel werkelijk bronnen bevat

        onderzochte_mappen = 0
        missing_init_files = []

        for directory in src_path.rglob("*"):
            if not directory.is_dir() or directory.name.startswith("."):
                continue
            if "__pycache__" in directory.parts:
                continue
            onderzochte_mappen += 1
            if not (directory / "__init__.py").exists():
                missing_init_files.append(str(directory.relative_to(src_path)))

        assert onderzochte_mappen > 0, f"geen submappen gevonden onder {src_path}"
        assert len(missing_init_files) == 0, (
            f"Ontbrekende __init__.py bestanden in {len(missing_init_files)} van "
            f"{onderzochte_mappen} mappen: {missing_init_files}"
        )


class TestNederlandseCommentaren(unittest.TestCase):
    """Test de kwaliteit en consistentie van Nederlandse commentaren."""

    def setUp(self):
        """Setup voor commentaar tests.

        Leest de module-globale `SRC_PAD`; een ontbrekende wortel of een lege
        bestandslijst laat de setUp hier al falen in plaats van de scans
        hieronder leeg-groen te laten lopen.
        """
        self.src_path = _verplichte_map(SRC_PAD)
        self.python_files = _bronbestanden(self.src_path)

        # Nederlandse woorden die we verwachten in commentaren
        self.expected_dutch_words = [
            "voor",
            "van",
            "een",
            "het",
            "de",
            "met",
            "en",
            "in",
            "op",
            "functie",
            "klasse",
            "module",
            "bestand",
            "configuratie",
            "definitie",
            "validatie",
            "generatie",
            "database",
            "systeem",
        ]

        # Technische termen die Engels mogen blijven
        self.allowed_english_terms = [
            "import",
            "class",
            "def",
            "return",
            "if",
            "else",
            "try",
            "except",
            "API",
            "JSON",
            "HTTP",
            "URL",
            "UUID",
            "cache",
            "token",
            "hash",
        ]

    # advisory: het Nederlands-commentaarbeleid is niet geleverd; de taalgrenzen
    # blijven ongewijzigd. Trigger: vrijgegeven herstel van het taalbeleid.
    @pytest.mark.advisory
    def test_docstrings_are_dutch(self):
        """Test dat docstrings in het Nederlands zijn.

        Docstrings komen uit de AST (`_docstrings`), niet uit een
        `\"\"\"...\"\"\"`-regex: die miste single-quoted docstrings en pakte
        gewone stringliterals mee. Lees- en parsefouten propageren; de oude
        brede `except Exception` maakte van een onleesbaar bestand een stille
        warning, waardoor het bestand uit de teller viel en de grens juist
        makkelijker haalbaar werd.

        Grenzen ongewijzigd: docstrings korter dan 20 tekens tellen niet mee,
        minimaal twee Nederlandse woorden per docstring, en minder dan 10% van
        de bestanden mag zakken. Dispositie bij rood: DEF-519-testdispositie,
        inhoudelijke owner niet vastgesteld, trigger = vrijgegeven herstel,
        vervalt 2026-10-06.
        """
        non_dutch_files = []
        onderzochte_docstrings = 0

        for py_file in self.python_files:
            boom = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))

            for docstring in _docstrings(boom):
                if len(docstring.strip()) > 20:  # Skip zeer korte docstrings
                    onderzochte_docstrings += 1
                    dutch_word_count = sum(
                        1
                        for word in self.expected_dutch_words
                        if word.lower() in docstring.lower()
                    )

                    if dutch_word_count < 2:  # Verwacht minimaal 2 Nederlandse woorden
                        non_dutch_files.append(str(py_file.relative_to(self.src_path)))
                        break

        assert (
            onderzochte_docstrings > 0
        ), f"geen enkele docstring onderzocht in {len(self.python_files)} bestanden"
        assert len(non_dutch_files) < len(self.python_files) * 0.1, (
            f"Te veel bestanden zonder Nederlandse docstrings: "
            f"{len(non_dutch_files)}/{len(self.python_files)}, "
            f"eerste vijf: {non_dutch_files[:5]}"
        )

    # advisory: zie test_docstrings_are_dutch; zelfde niet-geleverde taalbeleid
    # en dezelfde trigger.
    @pytest.mark.advisory
    def test_inline_comments_are_dutch(self):
        """Test dat inline commentaren grotendeels in het Nederlands zijn.

        Leesfouten propageren (zie `test_docstrings_are_dutch`). Grenzen
        ongewijzigd: minstens 70% Nederlandse commentaarregels per bestand, en
        minder dan vijf bestanden mogen daaronder zakken.

        Dispositie bij rood: DEF-519-testdispositie, inhoudelijke owner niet
        vastgesteld, trigger = vrijgegeven herstel, vervalt 2026-10-06.
        """
        files_with_poor_dutch_comments = []
        beoordeelde_bestanden = 0

        for py_file in self.python_files:
            lines = py_file.read_text(encoding="utf-8").splitlines()

            comment_lines = [line for line in lines if line.strip().startswith("#")]

            if len(comment_lines) > 5:  # Alleen bij bestanden met genoeg commentaren
                beoordeelde_bestanden += 1
                dutch_comments = 0
                for comment in comment_lines:
                    comment_text = comment.strip("#").strip()
                    if len(comment_text) > 10:  # Skip zeer korte commentaren
                        dutch_word_count = sum(
                            1
                            for word in self.expected_dutch_words
                            if word.lower() in comment_text.lower()
                        )
                        if dutch_word_count >= 1:
                            dutch_comments += 1

                dutch_ratio = dutch_comments / len(comment_lines)
                if dutch_ratio < 0.7:  # Verwacht 70% Nederlandse commentaren
                    files_with_poor_dutch_comments.append(
                        (str(py_file.relative_to(self.src_path)), round(dutch_ratio, 2))
                    )

        assert beoordeelde_bestanden > 0, (
            f"geen enkel bestand had meer dan vijf commentaarregels "
            f"({len(self.python_files)} bestanden gescand)"
        )
        assert len(files_with_poor_dutch_comments) < 5, (
            f"Te veel bestanden met onvoldoende Nederlandse commentaren: "
            f"{len(files_with_poor_dutch_comments)}/{beoordeelde_bestanden} "
            f"beoordeeld, eerste vijf: {files_with_poor_dutch_comments[:5]}"
        )

    # advisory: het documentatiebeleid is niet geleverd; de grens 0.3 blijft
    # ongewijzigd staan. Trigger: vrijgegeven herstel van het documentatiebeleid.
    @pytest.mark.advisory
    def test_function_documentation_completeness(self):
        """Test dat belangrijke functies Nederlandse documentatie hebben.

        Meet via AST, niet via import. De oude versie draaide
        `spec.loader.exec_module` over élk bronbestand: dat voert de complete
        productcode met al haar bijwerkingen uit, en `inspect.getmembers` telde
        daarna óók de functies die een module slechts *importeert* mee. Bestanden
        die niet importeerden vielen bovendien stil weg.

        Gemeten scope, expliciet: de functies die een module zélf op moduleniveau
        definieert — zowel `def` als `async def` (`ast.FunctionDef` en
        `ast.AsyncFunctionDef` direct in `tree.body`) — met een publieke naam.
        Methodes in klassen en geneste functies vallen erbuiten, net als in de
        oude meting; geïmporteerde functies tellen niet meer mee.

        Noemer is nu de werkelijke telling in plaats van
        `len(ongedocumenteerd) + 100`. Parsefouten propageren.

        Grens ongewijzigd op 0.3 (het oude commentaar noemde 20%, wat niet
        klopte met de feitelijke 0.3 in de assertie). Dispositie bij rood:
        DEF-519-testdispositie, inhoudelijke owner niet vastgesteld, trigger =
        vrijgegeven herstel, vervalt 2026-10-06.
        """
        undocumented_functions = []
        total_functions = 0

        for py_file in self.python_files:
            boom = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))

            for knoop in boom.body:
                if not isinstance(knoop, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                if knoop.name.startswith("_"):
                    continue

                total_functions += 1
                docstring = ast.get_docstring(knoop)
                if not docstring or len(docstring) < 10:
                    undocumented_functions.append(
                        f"{py_file.relative_to(self.src_path)}:{knoop.name}"
                    )
                elif not any(
                    word in docstring.lower() for word in self.expected_dutch_words[:5]
                ):
                    undocumented_functions.append(
                        f"{py_file.relative_to(self.src_path)}:{knoop.name} (no Dutch)"
                    )

        assert (
            total_functions > 0
        ), f"geen publieke modulefuncties geteld in {len(self.python_files)} bestanden"
        assert len(undocumented_functions) / total_functions < 0.3, (
            f"Te veel ongedocumenteerde functies: {len(undocumented_functions)}/"
            f"{total_functions}, eerste tien: {undocumented_functions[:10]}"
        )


class TestStatischeScansDiscrimineren(unittest.TestCase):
    """Bewijs dat de statische scans hierboven op een kapotte scope omvallen.

    Roept de échte checkmethodes aan met een eigen tijdelijke bronmap; er wordt
    niets van `ast.parse` nagebootst. De module-globale `SRC_PAD` gaat in
    `finally` exact terug, zodat de andere nodes hun normale scope houden — dat
    herstel wordt hieronder ook expliciet nagemeten.

    De scratchmappen komen uit `tempfile.mkdtemp()` en worden bewust *niet*
    opgeruimd: deze suite verwijdert geen bestanden of mappen. Ze blijven onder
    de systeem-tempmap staan en vallen daar onder het normale OS-opruimbeleid.
    """

    @contextlib.contextmanager
    def _tijdelijke_wortel(self, wortel: Path):
        """Wijs de scanwortel tijdelijk aan `wortel` toe en zet hem terug."""
        global SRC_PAD
        origineel = SRC_PAD
        SRC_PAD = wortel
        try:
            yield
        finally:
            SRC_PAD = origineel

    def _scratchwortel(self) -> Path:
        """Verse, niet-opgeruimde scratchmap met een lege `src` erin."""
        wortel = Path(tempfile.mkdtemp(prefix="def519-legacystatic-")) / "src"
        wortel.mkdir()
        return wortel

    def test_lege_bron_laat_de_echte_scans_falen(self):
        """Een bestaande maar lege bronmap mag geen scan groen maken."""
        leeg = self._scratchwortel()

        with self._tijdelijke_wortel(leeg):
            commentaartest = TestNederlandseCommentaren("test_docstrings_are_dutch")
            with pytest.raises(AssertionError) as leeg_gevangen:
                commentaartest.setUp()
            assert "geen Python-bronbestanden" in str(leeg_gevangen.value)

            packagetest = TestImportStructure("test_package_init_files")
            with pytest.raises(AssertionError):
                packagetest.test_package_init_files()

            servicetest = TestRegressionSpecific("test_modern_service_encoding_fix")
            with pytest.raises(AssertionError) as bron_gevangen:
                servicetest.test_modern_service_encoding_fix()
            assert "modern_web_lookup_service.py" in str(bron_gevangen.value)

        assert SRC_PAD == PROJECTROOT / "src", "scanwortel niet teruggezet"

    def test_lege_verplichte_bron_haalt_de_parsecheck_niet(self):
        """Een leeg maar bestaand verplicht bronbestand parseert groen.

        Daarom moet de non-empty-controle vóór `ast.parse` komen: zonder die
        controle levert een leeggelopen verplichte bron nul bevindingen en dus
        een groene node.
        """
        wortel = self._scratchwortel()
        (wortel / "services").mkdir()
        for naam in ("modern_web_lookup_service.py", "unified_definition_generator.py"):
            (wortel / "services" / naam).write_text("", encoding="utf-8")

        with self._tijdelijke_wortel(wortel):
            servicetest = TestRegressionSpecific("test_modern_service_encoding_fix")
            with pytest.raises(AssertionError) as gevangen:
                servicetest.test_modern_service_encoding_fix()
            assert "leeg bronbestand" in str(gevangen.value)

        assert SRC_PAD == PROJECTROOT / "src", "scanwortel niet teruggezet"

    def test_kapotte_bron_propageert_de_parsefout(self):
        """Een onparsebaar bronbestand hoort de documentatiescan rood te maken."""
        wortel = self._scratchwortel()
        (wortel / "kapot.py").write_text("def kapot(:\n", encoding="utf-8")

        with self._tijdelijke_wortel(wortel):
            documentatietest = TestNederlandseCommentaren(
                "test_function_documentation_completeness"
            )
            documentatietest.setUp()
            with pytest.raises(SyntaxError):
                documentatietest.test_function_documentation_completeness()

        assert SRC_PAD == PROJECTROOT / "src", "scanwortel niet teruggezet"


class TestCoreFunctionality(unittest.TestCase):
    """Test de core functionaliteit van DefinitieAgent.

    Geen globale `sys.modules["streamlit"]`-vervanging meer. Deze vier nodes
    raken de backend (repository, toetsregels-loader, validatorloader,
    servicefactory) en hebben Streamlit niet nodig; de oude `setUp` schreef die
    module ongevraagd voor de hele proces-sessie over en zette hem nooit terug,
    met een brede `except Exception → MagicMock` die een echte importfout van de
    projectmock onzichtbaar maakte.
    """

    def test_definitie_repository_basic_operations(self):
        """Test basis database operaties op een eigen synthetische database.

        Eigen scratch-DB, echte create/get/search, en een readback via een
        tweede repository nadat de eerste verbinding dicht is — dat laatste
        bewijst dat de rij werkelijk op schijf staat en niet alleen in de
        openstaande verbinding leefde.

        De oude `os.unlink`-route is vervallen: de suite verwijdert niets. De
        DB blijft als evidence staan. Fouten propageren; de oude
        `except Exception → self.fail(...)` verborg de echte traceback.
        """
        from database.definitie_repository import (
            DefinitieRecord,
            DefinitieRepository,
        )

        db_pad = _scratchmap("def519-coreruntime-repo-") / "regressie.db"

        repo = DefinitieRepository(str(db_pad))
        self.addCleanup(_sluit_eigen_repositoryverbinding, repo)

        test_record = DefinitieRecord(
            begrip="def519_regressie_begrip",
            definitie="Test definitie voor regressietest",
            organisatorische_context="Test",
            juridische_context="test_juridisch",
            categorie="proces",
            created_by="test_suite",
        )

        created_id = repo.create_definitie(test_record)
        assert isinstance(created_id, int) and created_id > 0, created_id

        retrieved = repo.get_definitie(created_id)
        assert retrieved is not None, f"record {created_id} niet teruggelezen"
        assert retrieved.begrip == "def519_regressie_begrip"
        assert retrieved.definitie == "Test definitie voor regressietest"
        assert retrieved.organisatorische_context == "Test"
        assert retrieved.juridische_context == "test_juridisch"
        assert retrieved.categorie == "proces"

        # Exacte set, geen membership: een zoekactie die er records bij haalt is
        # net zo fout als een die het gecreëerde record mist.
        gevonden = repo.search_definities(query="def519_regressie_begrip")
        assert {r.id for r in gevonden} == {created_id}, [r.id for r in gevonden]

        # Discriminator op dezelfde echte zoekroute: een begrip dat nooit is
        # aangemaakt levert niets op. Zonder dit zou de assertie hierboven ook
        # groen zijn op een zoekfunctie die simpelweg alles teruggeeft.
        assert repo.search_definities(query="def519_nooit_aangemaakt") == []

        # Readback via een verse verbinding op hetzelfde bestand.
        _sluit_eigen_repositoryverbinding(repo)
        verse_repo = DefinitieRepository(str(db_pad))
        self.addCleanup(_sluit_eigen_repositoryverbinding, verse_repo)

        na_readback = verse_repo.get_definitie(created_id)
        assert na_readback is not None, "record overleefde de verbinding niet"
        assert na_readback.begrip == retrieved.begrip
        assert na_readback.definitie == retrieved.definitie
        assert (
            na_readback.organisatorische_context == retrieved.organisatorische_context
        )
        assert na_readback.juridische_context == retrieved.juridische_context
        assert na_readback.categorie == retrieved.categorie

    def test_configuration_loading(self):
        """Test configuratie laden en validatie.

        De bestaande `load_toetsregels`-asserts blijven staan; er komt een echte
        telling bij. Alleen dynamisch vergelijken met de bronbestanden zou een
        verdwenen regel maskeren (53 → 52 blijft dan groen), dus beide kanten
        worden gepind: de loader levert er evenveel als er JSON-bronnen zijn,
        én dat aantal is 53.

        ConfigManager wordt onvoorwaardelijk geïmporteerd — een `ImportError`
        hoort deze node rood te maken, niet "optioneel groen" te loggen.
        """
        from config.config_manager import ConfigManager, ConfigSection
        from toetsregels.loader import load_toetsregels

        toetsregels = load_toetsregels().get("regels", {})
        assert isinstance(toetsregels, dict)
        assert len(toetsregels) > 0

        # Valideer toetsregel structuur
        for _regel_id, regel_data in toetsregels.items():
            assert "uitleg" in regel_data
            assert isinstance(regel_data["uitleg"], str)
            assert len(regel_data["uitleg"]) > 10

        bronjsons = sorted((SRC_PAD / "toetsregels" / "regels").glob("*.json"))
        assert len(toetsregels) == len(bronjsons) == 53, (
            f"{len(toetsregels)} geladen regels tegenover {len(bronjsons)} "
            f"JSON-bronnen; verwacht 53"
        )

        # Eigen, absoluut en leeg config_dir: er is geen config.yaml, dus de
        # YAML-laag uit de checkout valt weg. Dat is de enige laag die hiermee
        # wordt afgesneden — `_load_from_environment()` (config_manager.py:505)
        # blijft draaien en overlayt nog steeds omgevingsvariabelen zoals
        # OPENAI_API_KEY, OPENAI_DEFAULT_TEMPERATURE, CACHE_* en LOG_LEVEL. Dat
        # providersleutels hier dummy zijn komt van de vroege offline-bootstrap,
        # niet van dit lege config_dir.
        #
        # `request_timeout` heeft geen env-overlay in `_load_from_environment`,
        # dus die waarde is aantoonbaar de code-default (APIConfig, regel 69).
        leeg_config = _scratchmap("def519-coreruntime-config-")
        config_manager = ConfigManager(config_dir=str(leeg_config))

        api_config = config_manager.get_config(ConfigSection.API)
        assert api_config.request_timeout == 30.0, api_config.request_timeout

        # Exacte tweede readback: dezelfde sectie levert dezelfde waarde op.
        tweede_lezing = config_manager.get_config(ConfigSection.API)
        assert tweede_lezing.request_timeout == 30.0, tweede_lezing.request_timeout
        assert tweede_lezing is api_config

    def test_validation_system(self):
        """Test de JSONValidatorLoader-compatibiliteit met drie echte regels.

        Bewust dezelfde beperkte claim als voorheen: dit toetst dat de
        compatibility-interface van `JSONValidatorLoader` op drie werkelijk
        aanwezige regels een echte uitkomst produceert. Het is géén uitspraak
        over de volledige validatiepipeline of over de inhoudelijke kwaliteit
        van het oordeel.

        `get_all_regel_ids()` sorteert, dus de eerste drie liggen vast. De
        oude assertie (`result is not None`) was groen zelfs als alle drie de
        validators ontbraken; nu wordt per regel een echte uitkomst geëist.
        """
        from toetsregels.json_validator_loader import json_validator_loader

        test_definitie = "Een systematisch proces voor het vaststellen van identiteit"
        test_begrip = "verificatie"

        regel_ids = json_validator_loader.get_all_regel_ids()[:3]
        assert regel_ids == ["ARAI-01", "ARAI-02", "ARAI-02SUB1"], regel_ids

        resultaten = json_validator_loader.validate_definitie(
            definitie=test_definitie,
            begrip=test_begrip,
            regel_ids=regel_ids,
            context={},
        )

        samenvatting, regelresultaten = _borg_validatieresultaten(resultaten, regel_ids)

        # Concrete actuele uitkomst per regel voor deze synthetische testtekst:
        # ARAI-01 en ARAI-02SUB1 slagen, ARAI-02 faalt op onvoldoende concreetheid.
        uitkomsten = [regel[0] for regel in regelresultaten]
        assert uitkomsten == ["✅", "❌", "✅"], list(
            zip(regel_ids, regelresultaten, strict=True)
        )
        assert "ARAI01" in regelresultaten[0]
        assert "ARAI02" in regelresultaten[1]
        assert "ARAI02SUB1" in regelresultaten[2]
        assert samenvatting == (
            "📊 **Toetsing Samenvatting**: 2/3 regels geslaagd (66.7%) | ❌ 1 gefaald"
        ), samenvatting

    def test_ai_integration_mocked(self):
        """Meet het factory/adapter-contract met een eigen orchestratordubbel.

        Wat dit bewijst: `get_definition_service()` bouwt een echte
        `ServiceAdapter` op de container die de factory aanreikt, en
        `ServiceAdapter.generate_definition` vertaalt de legacy dict-interface
        naar een `GenerationRequest` en doet daarmee een échte async
        `create_definition`-aanroep op de orchestrator van díe container.

        Wat dit nadrukkelijk NIET bewijst: echte AI-generatie. Het
        orchestratorresultaat is synthetisch. De volledige keten (echte
        orchestrator, providergrens, validatie) is elders al aangetoond in de
        kernjourney; die wordt hier niet nagebouwd.

        `openai.OpenAI` patchen is vervallen: die grens ligt niet op deze route,
        dus dat mockte niets en liet een node achter die alleen de constructor
        aanraakte.

        De eigen container komt via een `patch.object`-context op
        `services.service_factory.get_cached_container`, die exact wordt
        teruggezet. Er wordt geen singleton van anderen gemaakt, gewist of
        gesloten, en er komt geen web-, RAG- of providerverkeer aan te pas.
        """
        from services import service_factory
        from services.interfaces import Definition, DefinitionResponseV2

        verwachte_definitie = "Synthetische definitie uit de orchestratordubbel"

        class OrchestratorDubbel:
            """Beperkte dubbel: registreert de call en levert een getypeerd V2-antwoord."""

            def __init__(self) -> None:
                self.calls: list[tuple[Any, Any]] = []

            async def create_definition(self, request, context=None):
                self.calls.append((request, context))
                return DefinitionResponseV2(
                    success=True,
                    definition=Definition(
                        begrip=request.begrip,
                        definitie=verwachte_definitie,
                        organisatorische_context=list(request.organisatorische_context),
                        juridische_context=list(request.juridische_context),
                    ),
                    metadata={"bron": "orchestratordubbel"},
                )

        class ContainerDubbel:
            """Levert precies wat `ServiceAdapter.__init__` opvraagt."""

            def __init__(self, orchestrator: OrchestratorDubbel) -> None:
                self._orchestrator = orchestrator

            def orchestrator(self) -> OrchestratorDubbel:
                return self._orchestrator

            def web_lookup(self) -> None:
                return None

        eigen_orchestrator = OrchestratorDubbel()
        eigen_container = ContainerDubbel(eigen_orchestrator)
        originele_factory = service_factory.get_cached_container

        with patch.object(
            service_factory, "get_cached_container", lambda: eigen_container
        ):
            service = service_factory.get_definition_service()

            # Containeridentiteit: de adapter hangt aan ónze grens.
            assert isinstance(service, service_factory.ServiceAdapter)
            assert service.container is eigen_container
            assert service.orchestrator is eigen_orchestrator
            assert eigen_orchestrator.calls == [], "orchestrator te vroeg aangeroepen"

            # Async binnen unittest via asyncio.run: een `async def`-testmethode
            # op unittest.TestCase kan ongemerkt onuitgevoerd blijven slagen.
            respons = asyncio.run(
                service.generate_definition(
                    "def519_factory_begrip",
                    {
                        "organisatorisch": ["strafrecht"],
                        "juridisch": ["detentie"],
                    },
                )
            )

        # Exact één echte aanroep, met exact de vertaalde requestinputs.
        assert len(eigen_orchestrator.calls) == 1, eigen_orchestrator.calls
        request, _context = eigen_orchestrator.calls[0]
        assert request.begrip == "def519_factory_begrip"
        assert request.organisatorische_context == ["strafrecht"]
        assert request.juridische_context == ["detentie"]
        assert request.actor == "legacy_ui"

        # Exacte teruggegeven definitietekst uit het synthetische resultaat.
        assert isinstance(respons, DefinitionResponseV2)
        assert respons.success is True
        assert respons.definition is not None
        assert respons.definition.definitie == verwachte_definitie
        assert respons.definition.begrip == "def519_factory_begrip"

        # De factorybinding is exact teruggezet op de oorspronkelijke functie.
        assert service_factory.get_cached_container is originele_factory


class TestImportChecksDiscrimineren(unittest.TestCase):
    """Foutinjectie in de échte importchecks, niet in Pythons importmechaniek.

    Beide cases roepen de gewijzigde nodes zelf aan met een eigen gecontroleerde
    modulelijst. Eigen `sys.path`- en `sys.modules`-bindings gaan exact terug;
    de scratchmap blijft staan (deze suite verwijdert niets).
    """

    def test_ontbrekende_coremodule_faalt_de_echte_check(self):
        """Een afwezige module in de core-lijst moet de node hard laten falen."""
        importtest = TestImportStructure("test_core_modules_import")
        importtest.setUp()
        importtest.core_modules = ["json", "def519_coremodule_bestaat_niet"]

        with pytest.raises(AssertionError) as gevangen:
            importtest.test_core_modules_import()

        melding = str(gevangen.value)
        assert "def519_coremodule_bestaat_niet" in melding, melding
        assert "ModuleNotFoundError" in melding, melding
        # De werkende module uit dezelfde lijst zit niet in de mislukkingen.
        assert "'json'" not in melding, melding

    def test_kapotte_dependency_is_geen_afwezige_optie(self):
        """Een bestaande optionele module met kapotte dependency mag niet passeren."""
        pakket = _scratchmap("def519-imports-kapot-") / "def519_kapotte_dep"
        pakket.mkdir()
        (pakket / "__init__.py").write_text(
            "import def519_bestaat_niet\n", encoding="utf-8"
        )

        origineel_pad = list(sys.path)

        with _tijdelijk_importpad(pakket.parent, ["def519_kapotte_dep"]):
            # De module bestáát, dus de classificatie mag hem niet als afwezig
            # afdoen; de kapotte dependency hoort te propageren.
            assert _module_afwezig("def519_kapotte_dep") is False

            optioneeltest = TestImportStructure(
                "test_optional_modules_graceful_degradation"
            )
            optioneeltest.setUp()
            optioneeltest.optional_modules = ["def519_kapotte_dep"]

            with pytest.raises(ModuleNotFoundError) as gevangen:
                optioneeltest.test_optional_modules_graceful_degradation()
            assert gevangen.value.name == "def519_bestaat_niet"

            # Een kind van diezelfde kapotte ouder mag óók niet als "afwezig"
            # worden afgedaan: `find_spec` voert de ouder uit en die fout hoort
            # te propageren.
            with pytest.raises(ModuleNotFoundError) as kind_gevangen:
                _module_afwezig("def519_kapotte_dep.bestaat_niet")
            assert kind_gevangen.value.name == "def519_bestaat_niet"

        # Een echt afwezige module wordt wél als afwezig herkend — met een
        # gezonde ouder (`json`) en op topniveau.
        assert _module_afwezig("json.def519_bestaat_niet") is True
        assert _module_afwezig("def519_module_bestaat_niet") is True

        assert sys.path == origineel_pad, "sys.path niet exact teruggezet"
        assert "def519_kapotte_dep" not in sys.modules

    def test_kapotte_ouder_met_zelfde_prefix_propageert(self):
        """Kapotte ouder wiens ontbrekende dependency zijn eigen prefix deelt.

        Het pakket importeert `def519_zelfkapot.missing` in zijn eigen
        `__init__.py`. Wordt daarna `def519_zelfkapot.missing.child` gevraagd,
        dan is de ontbrekende naam een prefix van het gevraagde pad — en dat mag
        de kapotte ouder niet als "gewoon afwezig" laten passeren.
        """
        pakket = _scratchmap("def519-imports-zelfkapot-") / "def519_zelfkapot"
        pakket.mkdir()
        (pakket / "__init__.py").write_text(
            "import def519_zelfkapot.missing\n", encoding="utf-8"
        )

        with _tijdelijk_importpad(pakket.parent, ["def519_zelfkapot"]):
            with pytest.raises(ModuleNotFoundError) as gevangen:
                _module_afwezig("def519_zelfkapot.missing.child")
            assert gevangen.value.name == "def519_zelfkapot.missing"

        assert "def519_zelfkapot" not in sys.modules

    def test_lege_meetscope_faalt(self):
        """Een lege modulelijst mag niet vacuüm slagen."""
        importtest = TestImportStructure("test_core_modules_import")
        importtest.setUp()
        importtest.core_modules = []
        with pytest.raises(AssertionError) as core_gevangen:
            importtest.test_core_modules_import()
        assert "lege importscope" in str(core_gevangen.value)

        optioneeltest = TestImportStructure(
            "test_optional_modules_graceful_degradation"
        )
        optioneeltest.setUp()
        optioneeltest.optional_modules = []
        with pytest.raises(AssertionError) as optie_gevangen:
            optioneeltest.test_optional_modules_graceful_degradation()
        assert "lege importscope" in str(optie_gevangen.value)


class TestWebLookupFoutpad(unittest.TestCase):
    """Eén foutpadcase op de echte servicegrens: een niet-geslaagd resultaat.

    De service filtert `success=False` weg (`modern_web_lookup_service.py:298`),
    dus de lookup levert dan een lege lijst terwijl de grens wél is bereikt.

    Wat dit wél aantoont: dat filtergedrag, afzonderlijk. Wat dit **niet**
    aantoont: dat de hoofdassertie van `test_modern_web_lookup_service` door een
    mutant is getoetst — daarvoor zou die node zelf moeten worden aangeroepen en
    zien falen, en daar is hier bewust geen brede helper- of testfamilie voor
    opgetuigd.
    """

    def test_niet_geslaagd_resultaat_wordt_gefilterd(self):
        from services.interfaces import LookupRequest
        from services.modern_web_lookup_service import ModernWebLookupService

        stub = WikipediaGrensStub(succesvol_resultaat=False)
        patcher = patch(WIKIPEDIA_GRENS, stub)
        patcher.start()
        self.addCleanup(patcher.stop)

        service = ModernWebLookupService()
        resultaten = asyncio.run(
            service.lookup(LookupRequest(term=WIKI_TERM, sources=["wikipedia"]))
        )

        assert stub.aanroepen == [WIKI_TERM], stub.aanroepen
        assert resultaten == []


class TestCoreRuntimeDiscrimineert(unittest.TestCase):
    """Bewijs dat de coreruntime-asserties resultaatverlies zien.

    De oude nodes hingen op `assert result is not None` en `len(results) > 0`:
    groen ook als er niets werkelijk geëvalueerd of gevonden was. Hier wordt de
    borg uit `_borg_validatieresultaten` op een gedegradeerd resultaat losgelaten
    en moet hij omvallen.
    """

    REGEL_IDS = ["ARAI-01", "ARAI-02", "ARAI-02SUB1"]

    def test_resultaatverlies_valt_door_de_borg(self):
        """Alle drie de validators weg = drie ⏭️-regels; dat mag niet groen zijn."""
        verloren = [
            "📊 **Toetsing Samenvatting**: 0/3 regels geslaagd (0.0%)",
            *(f"⏭️ {regel_id}: Validator niet gevonden" for regel_id in self.REGEL_IDS),
        ]

        # De naïeve variant van de oude node ziet hier niets aan mankeren.
        assert verloren is not None

        with pytest.raises(AssertionError) as gevangen:
            _borg_validatieresultaten(verloren, self.REGEL_IDS)
        assert "geen echte uitkomst" in str(gevangen.value)

    def test_ontbrekende_regel_is_een_apart_foutpad(self):
        """Een niet-bestaand regel-ID levert aantoonbaar de ⏭️-route op.

        Extra foutpadbewijs op de échte loader. Dit zegt niets over de
        hoofdassertie van `test_validation_system`: die draait op drie
        bestaande regels en wordt daar zelf getoetst.
        """
        from toetsregels.json_validator_loader import json_validator_loader

        onbekend = ["DEF519-BESTAAT-NIET"]
        resultaten = json_validator_loader.validate_definitie(
            definitie="Een systematisch proces voor het vaststellen van identiteit",
            begrip="verificatie",
            regel_ids=onbekend,
            context={},
        )

        # Samenvatting plus één ⏭️-regel: de validator is niet gevonden, dus er
        # is niets geëvalueerd terwijl de samenvatting wel 0/1 meldt.
        assert len(resultaten) == 2, resultaten
        assert resultaten[0].startswith("📊"), resultaten[0]
        assert resultaten[1] == "⏭️ DEF519-BESTAAT-NIET: Validator niet gevonden"
        with pytest.raises(AssertionError):
            _borg_validatieresultaten(resultaten, onbekend)


#: De providergrens die de wikipedia-route werkelijk bereikt. Bewezen in
#: tests/unit/web_lookup/test_modern_service.py:34.
WIKIPEDIA_GRENS = "services.web_lookup.wikipedia_service.wikipedia_lookup"

#: Vaste inhoud van het bevroren providerantwoord.
WIKI_TERM = "authenticatie"
WIKI_DEFINITIE = "Bevroren Wikipedia-definitie voor authenticatie"
WIKI_URL = "https://nl.wikipedia.org/wiki/authenticatie"


class WikipediaGrensStub:
    """Bevroren downstream-providergrens; registreert elke aanroep.

    `lukt=False` laat de grens een echte exception gooien nadat de aanroep is
    geregistreerd — zo is aantoonbaar dát de route de grens bereikte en daarna
    pas faalde. `succesvol_resultaat=False` levert juist een geldig maar
    niet-geslaagd resultaat, voor het filtergedrag van de service.
    """

    def __init__(self, *, lukt: bool = True, succesvol_resultaat: bool = True) -> None:
        self.aanroepen: list[str] = []
        self.lukt = lukt
        self.succesvol_resultaat = succesvol_resultaat

    async def __call__(self, term: str, language: str = "nl"):
        from services.interfaces import LookupResult, WebSource

        self.aanroepen.append(term)
        if not self.lukt:
            raise RuntimeError("providerfout op de bevroren clientgrens (teststub)")

        return LookupResult(
            term=term,
            source=WebSource(
                name="Wikipedia",
                url=WIKI_URL,
                confidence=0.8,
                is_juridical=False,
            ),
            definition=WIKI_DEFINITIE,
            success=self.succesvol_resultaat,
        )


class TestModernWebLookupIntegration(unittest.TestCase):
    """Test moderne web lookup service functionaliteit."""

    def _lookup_met_grens(self, stub: WikipediaGrensStub) -> list:
        """Draai één echte lookup over uitsluitend de wikipedia-route."""
        from services.interfaces import LookupRequest
        from services.modern_web_lookup_service import ModernWebLookupService

        service = ModernWebLookupService()
        request = LookupRequest(term=WIKI_TERM, sources=["wikipedia"])

        patcher = patch(WIKIPEDIA_GRENS, stub)
        patcher.start()
        self.addCleanup(patcher.stop)
        return asyncio.run(service.lookup(request))

    def test_modern_web_lookup_service(self):
        """Test dat moderne web lookup service correct werkt.

        Echte `ModernWebLookupService`; alleen de downstream-providergrens is
        bevroren. `sources=["wikipedia"]` beperkt de node tot één echte route —
        geen parallelisme- of duplicaatmatrix. De oude node deed niets meer dan
        `hasattr` binnen een brede `except Exception → logger.warning`.
        """
        stub = WikipediaGrensStub()

        resultaten = self._lookup_met_grens(stub)

        # De grens is precies één keer bereikt, met de gevraagde term.
        assert stub.aanroepen == [WIKI_TERM], stub.aanroepen

        assert len(resultaten) == 1, resultaten
        resultaat = resultaten[0]
        assert resultaat.term == WIKI_TERM
        assert resultaat.definition == WIKI_DEFINITIE
        assert resultaat.success is True
        assert resultaat.source.name == "Wikipedia"
        assert resultaat.source.url == WIKI_URL

        # `validate_source` is synchroon en hoort bij dezelfde node. Beperking,
        # expliciet: `_determine_source_type` is een **heuristiek** op
        # tekstkenmerken — dit pint het actuele contract en de actuele uitkomst,
        # en zegt niets over juridische bronkwaliteit.
        from services.interfaces import WebSource
        from services.modern_web_lookup_service import ModernWebLookupService

        service = ModernWebLookupService()

        juridisch = service.validate_source(
            "Artikel 5 van het Wetboek van Strafvordering bepaalt de voorwaarden."
        )
        assert isinstance(juridisch, WebSource)
        assert juridisch.name == "Analyzed Source"
        assert juridisch.url == ""
        assert juridisch.is_juridical is True

        # Neutrale tekst als tegenhanger: zonder dit zou een classifier die
        # altijd True teruggeeft er ook doorheen komen.
        neutraal = service.validate_source("Een verhaal over sterren en planeten.")
        assert neutraal.name == "Analyzed Source"
        assert neutraal.is_juridical is False

        # `confidence` wordt alleen als type- en rangecontract getoetst; over de
        # exacte waarde of de kwaliteit ervan doet deze node geen uitspraak.
        for bron in (juridisch, neutraal):
            assert isinstance(bron.confidence, float)
            assert 0.0 <= bron.confidence <= 1.0

    def test_external_api_error_handling(self):
        """Test error handling voor externe API calls.

        `@patch("requests.get")` is vervallen: door die grens liep nooit een
        request, dus die mock bevroor niets. Nu faalt de grens die de route
        werkelijk bereikt.

        Actueel toegelaten uitkomst: `lookup` verzamelt met
        `asyncio.gather(return_exceptions=True)` en filtert exceptions weg
        (`modern_web_lookup_service.py:282-300`), dus het resultaat is een lege
        lijst. Geen brede-except-groen: dat de grens bereikt werd, wordt apart
        aangetoond.
        """
        stub = WikipediaGrensStub(lukt=False)

        resultaten = self._lookup_met_grens(stub)

        assert stub.aanroepen == [WIKI_TERM], "de providerfout is niet bereikt"
        assert resultaten == []


class TestPerformanceAndMemory(unittest.TestCase):
    """Test performance en memory usage."""

    #: Oorspronkelijke scopes, per node gescheiden gehouden: de tijdmeting deed
    #: er drie, de geheugenmeting twee. Samenvoegen zou de geheugennode stil
    #: verbreden en de vergelijkbaarheid met de bestaande grens breken.
    PERFORMANCE_MODULES = [
        "main",
        "ui.tabbed_interface",
        "database.definitie_repository",
    ]
    MEMORY_MODULES = ["main", "database.definitie_repository"]

    def test_import_performance(self):
        """Test dat modules snel genoeg importeren.

        De imports moeten éérst werkelijk slagen; pas dan zegt de tijdsgrens
        iets. De oude `except Exception → logger.warning` maakte een kapotte
        import groen zolang het falen maar snel ging.

        Meting is **process-warm**: conftest en eerdere nodes hebben deze
        modules doorgaans al in `sys.modules`, dus dit is een bovengrens op een
        her-import, geen coldstartbewijs. Er komt bewust geen subprocess- of
        benchmarkframework bij. Grens ongewijzigd op 5,0s.
        """
        start = time.perf_counter()
        mislukt = _importeer_modules(self.PERFORMANCE_MODULES)
        import_time = time.perf_counter() - start

        assert not mislukt, f"imports faalden, tijd zegt dan niets: {mislukt}"
        assert import_time < 5.0, f"Import tijd te lang: {import_time:.2f}s"

    def test_basic_memory_usage(self):
        """Test dat basis memory usage redelijk is.

        `psutil` is een vaste testdependency, geen optie: ontbreekt hij, dan is
        de toolomgeving onvolledig en hoort deze node hard te falen. De oude
        `except ImportError → groen` dekte bovendien niet alleen psutil maar ook
        de applicatie-imports eronder; die staan nu buiten elke optionele
        detectie en falen hard.

        Zelfde process-warme kanttekening als bij `test_import_performance`: de
        modules zitten doorgaans al in `sys.modules`, dus de gemeten toename is
        een plafond en geen footprintbewijs. Grens ongewijzigd op 100MB.
        """
        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        mislukt = _importeer_modules(self.MEMORY_MODULES)
        assert not mislukt, f"imports faalden, geheugen zegt dan niets: {mislukt}"

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        assert memory_increase < 100, f"Memory gebruik te hoog: {memory_increase:.1f}MB"


class TestErrorHandlingAndRobustness(unittest.TestCase):
    """Test error handling en robuustheid."""

    def test_missing_config_graceful_handling(self):
        """Test graceful handling van ontbrekende configuratie.

        De oorspronkelijke intentie blijft: een ontbrekende config mag niet
        crashen maar moet op defaults terugvallen. Alleen het middel verandert.

        `patch.dict(os.environ, {}, clear=True)` is vervallen: dat wiste de
        héle omgeving, inclusief de verplichte offline-guards. In plaats daarvan
        een eigen absoluut configpad dat aantoonbaar niet bestaat, zodat er geen
        `config.yaml` te vinden is. De omgeving blijft intact.

        Nuance die hier hoort: een ontbrekend `config_dir` snijdt alléén de
        YAML-laag af. `_load_from_environment()` (config_manager.py:505) draait
        gewoon door en leest nog steeds env-variabelen, inclusief de
        providersleutels. Dat het daarbij om **geen echte providercredentials**
        gaat, komt van de vroege offline-bootstrap die die sleutels op dummy
        zet — niet van dit ontbrekende `config_dir`. De twee gepinde defaults
        zijn juist gekozen omdat ze géén env-overlay kennen, dus ze zijn
        aantoonbaar de code-default. Er wordt geen config- of beveiligingsregel
        gewijzigd.
        """
        from config.config_manager import ConfigManager, ConfigSection

        ontbrekend_pad = _scratchmap("def519-webinput-config-") / "bestaat-niet"
        assert not ontbrekend_pad.exists(), ontbrekend_pad

        config_manager = ConfigManager(config_dir=str(ontbrekend_pad))

        # Concrete huidige defaults, beide zonder env-overlay in
        # `_load_from_environment`: APIConfig.request_timeout (regel 69) en
        # CacheConfig.max_cache_size (regel 93).
        api_config = config_manager.get_config(ConfigSection.API)
        assert api_config.request_timeout == 30.0, api_config.request_timeout

        cache_config = config_manager.get_config(ConfigSection.CACHE)
        assert cache_config.max_cache_size == 1000, cache_config.max_cache_size

        # Exacte readback: dezelfde secties leveren dezelfde objecten en waarden.
        assert config_manager.get_config(ConfigSection.API) is api_config
        assert config_manager.get_config(ConfigSection.CACHE) is cache_config
        assert config_manager.get_config(ConfigSection.API).request_timeout == 30.0

    def test_invalid_input_handling(self):
        """Test handling van ongeldige input.

        Beide oorspronkelijke workloads blijven — lege input en 10.000 tekens —
        op dezelfde drie echte compat-regels als de core-batch. De oude
        `assert result is not None` was groen op elke uitkomst, ook als geen
        enkele regel iets had geëvalueerd.

        Beperkte claim, net als in `test_validation_system`: dit toetst het
        foutgedrag van de `JSONValidatorLoader`-compatibiliteitsinterface op
        drie regels. Het is geen uitspraak over de volledige pipeline en er
        wordt geen inputvalidatiecontract of corpus verzonnen.

        **Gemeten bevinding, strikt binnen deze selectie:** lege input haalt
        deze drie regels (3/3). ARAI-01, ARAI-02 en ARAI-02SUB1 zijn negatieve
        checks ("geen werkwoorden als kern", "geen containerbegrippen"), en een
        lege definitie voldoet daar triviaal aan. Dit legt uitsluitend de
        testdekking van déze drie regels vast; er is niet onderzocht of de
        `JSONValidatorLoader` als geheel, de validatiepipeline of een andere
        ingang wél een leegtecontract kent. Er wordt hier dan ook geen
        inputvalidator of policy gebouwd en `_borg_validatieresultaten` wordt
        niet versoepeld.
        """
        from toetsregels.json_validator_loader import json_validator_loader

        regel_ids = json_validator_loader.get_all_regel_ids()[:3]
        assert regel_ids == ["ARAI-01", "ARAI-02", "ARAI-02SUB1"], regel_ids

        leeg = json_validator_loader.validate_definitie(
            definitie="", begrip="", regel_ids=regel_ids, context={}
        )
        leeg_samenvatting, leeg_regels = _borg_validatieresultaten(leeg, regel_ids)
        assert [regel[0] for regel in leeg_regels] == ["✅", "✅", "✅"], (
            "lege input haalt deze drie negatieve regels triviaal; wijkt dit af, "
            f"dan is het regelcontract veranderd: {leeg_regels}"
        )
        assert leeg_samenvatting == (
            "📊 **Toetsing Samenvatting**: 3/3 regels geslaagd (100.0%)"
        ), leeg_samenvatting

        lange_tekst = "x" * 10000
        lang = json_validator_loader.validate_definitie(
            definitie=lange_tekst, begrip="test", regel_ids=regel_ids, context={}
        )
        lang_samenvatting, lang_regels = _borg_validatieresultaten(lang, regel_ids)
        # Ook 10.000 tekens `x` haalt alle drie: er staan geen werkwoorden en
        # geen containerbegrippen in. Dat de core-batch met een échte
        # definitiezin wél een ❌ op ARAI-02 gaf, laat zien dat deze regels op
        # inhoud toetsen en niet op lengte — er is geen lengtecontract.
        assert [regel[0] for regel in lang_regels] == ["✅", "✅", "✅"], lang_regels
        assert lang_samenvatting == (
            "📊 **Toetsing Samenvatting**: 3/3 regels geslaagd (100.0%)"
        ), lang_samenvatting


class TestRegressionSpecific(unittest.TestCase):
    """Test specifieke regressies die eerder opgelost zijn."""

    # advisory: de logger en de oude architectuur worden niet herbouwd.
    # Trigger: vrijgegeven herstel van de logsmodule.
    @pytest.mark.advisory
    def test_logs_import_resolution(self):
        """Test dat logs import resolutie correct werkt (specifieke regressie).

        Dit is de harde variant van de intentie: hier hoort de module er te
        zijn. Zij is uit de checkout verdwenen, dus deze node staat positief
        rood met het exacte pad. De logger wordt niet nagebouwd en de oude
        architectuur niet hersteld.

        Dispositie: DEF-519-testdispositie, inhoudelijke owner niet vastgesteld,
        trigger = vrijgegeven herstel, vervalt 2026-10-06.

        De `sys.path.insert` naar `tests/integration` is vervallen: dat was een
        globale bijwerking midden in een test (zie de kop van deze module).
        """
        naam = "logs.application.log_definitie"
        assert not _module_afwezig(naam), (
            f"verplichte module ontbreekt: {naam} "
            f"(verwacht onder {PROJECTROOT / 'logs' / 'application'})"
        )

        module = importlib.import_module(naam)
        logger_instance = module.get_logger("regression_test")
        assert logger_instance is not None
        assert callable(module.log_definitie)

    # advisory: de verwijderde module wordt niet nagebouwd en de verwachting
    # wordt niet weggefilterd. Trigger: vrijgegeven herstel of formele
    # intrekking van de bronverwachting.
    @pytest.mark.advisory
    def test_modern_service_encoding_fix(self):
        """Test dat de verwachte servicebestanden bestaan en parsebaar zijn.

        De oude versie sloeg een ontbrekend bestand stil over (`if
        file_path.exists()`) en ving daarbovenop elke fout af, zodat een
        verwijderde bron gewoon groen bleef. Ontbreken is nu een failure met het
        exacte pad; parse-/leesfouten propageren.

        Bekende positieve rode uitkomst: `unified_definition_generator.py`
        bestaat niet meer in deze checkout. Die wordt hier niet nagebouwd en niet
        uit de lijst weggefilterd. Dispositie: DEF-519-testdispositie,
        inhoudelijke owner niet vastgesteld, trigger = vrijgegeven herstel,
        vervalt 2026-10-06.
        """
        src_path = _verplichte_map(SRC_PAD)
        service_files = [
            src_path / "services" / "modern_web_lookup_service.py",
            src_path / "services" / "unified_definition_generator.py",
        ]

        ontbrekend = [str(pad) for pad in service_files if not pad.is_file()]
        assert not ontbrekend, f"verwachte bronbestanden ontbreken: {ontbrekend}"

        for file_path in service_files:
            # Non-empty vóór het parsen: een leeg bestand parseert groen.
            inhoud = _verplichte_broninhoud(file_path)
            ast.parse(inhoud, filename=str(file_path))

    def test_init_files_presence(self):
        """Test dat alle benodigde __init__.py bestanden aanwezig zijn.

        De verwachte bestandsnamen blijven ongewijzigd; alleen de basis klopt
        nu. `Path(__file__).parent.parent` wees op `tests/integration`, waardoor
        alle vier de paden per definitie ontbraken en deze node structureel rood
        stond op een meetfout in plaats van op een echt gemis.
        """
        expected_init_files = [
            "src/__init__.py",
            "src/database/__init__.py",
            "src/tools/__init__.py",
            "tests/__init__.py",
        ]

        missing_files = [
            init_file
            for init_file in expected_init_files
            if not (PROJECTROOT / init_file).is_file()
        ]

        assert len(missing_files) == 0, (
            f"Ontbrekende __init__.py bestanden onder {PROJECTROOT}: "
            f"{missing_files}"
        )


def run_regression_suite():
    """Voer de volledige regressietest suite uit."""
    print("🧪 Starting DefinitieAgent Regressietest Suite")
    print("=" * 60)

    # Configureer test suite
    test_suite = unittest.TestSuite()

    # Voeg alle test classes toe
    test_classes = [
        TestImportStructure,
        TestNederlandseCommentaren,
        TestCoreFunctionality,
        TestModernWebLookupIntegration,
        TestPerformanceAndMemory,
        TestErrorHandlingAndRobustness,
        TestRegressionSpecific,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Voer tests uit
    runner = unittest.TextTestRunner(verbosity=2, descriptions=True, failfast=False)

    result = runner.run(test_suite)

    # Rapporteer resultaten
    print("\n" + "=" * 60)
    print("🎯 REGRESSIETEST RESULTATEN:")
    print(
        f"✅ Tests geslaagd: {result.testsRun - len(result.failures) - len(result.errors)}"
    )
    print(f"❌ Tests gefaald: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    print(f"📊 Totaal tests: {result.testsRun}")

    if result.failures:
        print("\n🔴 GEFAALDE TESTS:")
        for test, traceback in result.failures:
            print(
                f"  - {test}: {traceback.split(chr(10))[-2] if traceback else 'Unknown'}"
            )

    if result.errors:
        print("\n💥 TEST ERRORS:")
        for test, traceback in result.errors:
            print(
                f"  - {test}: {traceback.split(chr(10))[-2] if traceback else 'Unknown'}"
            )

    success_rate = (
        (result.testsRun - len(result.failures) - len(result.errors))
        / result.testsRun
        * 100
    )
    print(f"\n🏆 SUCCESS RATE: {success_rate:.1f}%")

    if success_rate >= 95:
        print("🎉 UITSTEKEND! Regressietest suite geslaagd!")
    elif success_rate >= 85:
        print("✅ GOED! Meeste tests geslaagd, enkele issues om op te lossen")
    else:
        print("⚠️ AANDACHT NODIG! Meerdere issues gevonden")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_regression_suite()
    sys.exit(0 if success else 1)
