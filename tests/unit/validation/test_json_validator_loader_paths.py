"""Contracttests voor padconfinement in ``JSONValidatorLoader`` (DEF-733).

Standalone uitvoerbaar (``python3.13 -I -B <dit bestand>``) én pytest-verzamelbaar.
De loaderbron wordt rechtstreeks via ``importlib.util`` geladen: geen
applicatiepackage, geen conftest, geen provider. Alle fixtures zijn verse,
bewaarde tijdelijke mappen met nepvalidators; er wordt nooit echte
gequarantainede toolcode uitgevoerd.

Bewijsvoering: elke nepvalidator schrijft bij module-executie een markerbestand.
Aanwezigheid = de code is echt uitgevoerd, afwezigheid = de code is nooit
geladen. Zo tonen de negatieve cases aan dat geblokkeerde paden niet stilletjes
alsnog geïmporteerd worden.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

try:  # pytest is niet beschikbaar bij een standalone stdlib-run
    import pytest

    pytestmark = pytest.mark.unit
except ImportError:  # pragma: no cover - alleen bij standalone uitvoering
    pytest = None


# --------------------------------------------------------------------------
# Loaderbron laden (stdlib-only module, rechtstreeks van pad)
# --------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LOADER_PATH = _REPO_ROOT / "src" / "toetsregels" / "json_validator_loader.py"


def _load_loader_module():
    spec = importlib.util.spec_from_file_location(
        "def733_json_validator_loader_undertest", _LOADER_PATH
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensief
        raise RuntimeError(f"Kon loaderbron niet laden: {_LOADER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


JSONValidatorLoader = _load_loader_module().JSONValidatorLoader


# --------------------------------------------------------------------------
# Nepvalidator-fabriek
# --------------------------------------------------------------------------

_VALIDATOR_SRC = (
    "from pathlib import Path\n"
    "\n"
    "Path({marker!r}).write_text({tag!r}, encoding='utf-8')\n"
    "\n"
    "\n"
    "class {cls}:\n"
    "    def __init__(self, config):\n"
    "        self.config = config\n"
    "\n"
    "    def validate(self, definitie, begrip, context=None):\n"
    "        return (True, {tag!r}, 1.0)\n"
)


def _mkroot() -> Path:
    """Verse tijdelijke root zonder '-' in de naam.

    De streepjesvrije naam is essentieel: de loader bouwt de Python-kandidaat
    met ``regel_id.replace('-', '_')``, wat bij een absolute ID het hele pad
    verminkt. Zonder streepjes in het pad raakt de test de echte bug.
    """
    base = "/tmp" if os.path.isdir("/tmp") else None
    return Path(tempfile.mkdtemp(prefix="def733_", dir=base))


def _write_json(path: Path, payload: dict | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload if payload is not None else {"naam": path.stem}),
        encoding="utf-8",
    )
    return path


def _write_validator(path: Path, cls: str, tag: str, marker: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _VALIDATOR_SRC.format(marker=str(marker), tag=tag, cls=cls), encoding="utf-8"
    )
    return path


class _LoaderTestBase(unittest.TestCase):
    """Bouwt per test een verse boom: regels/ + validators/ + outside/."""

    def setUp(self) -> None:
        self.root = _mkroot()
        self.regels = self.root / "regels"
        self.validators = self.root / "validators"
        self.outside = self.root / "outside"
        for directory in (self.regels, self.validators, self.outside):
            directory.mkdir(parents=True)

    def loader(self, regels_dir: Path | None = None):
        return JSONValidatorLoader(str(regels_dir if regels_dir else self.regels))


# --------------------------------------------------------------------------
# Positief: ondersteunde functionaliteit moet blijven werken
# --------------------------------------------------------------------------


class TestOndersteundeFunctionaliteit(_LoaderTestBase):
    def test_custom_regels_dir_laadt_en_cachet_echte_nepvalidator(self):
        marker = self.root / "marker_con01.txt"
        _write_json(self.regels / "CON-01.json")
        _write_validator(
            self.validators / "CON_01.py", "CON01Validator", "con01", marker
        )

        loader = self.loader()
        validator = loader.load_validator("CON-01")

        assert validator is not None
        assert marker.exists(), "validatormodule is niet echt uitgevoerd"
        assert validator.validate("def", "begrip", None) == (True, "con01", 1.0)
        assert validator.config["id"] == "CON-01"
        assert loader.load_validator("CON-01") is validator, "cache verbroken"
        assert loader.load_json_config("CON-01")["id"] == "CON-01"

        resultaten = loader.validate_definitie("een definitie", "begrip", ["CON-01"])
        assert resultaten == [
            "📊 **Toetsing Samenvatting**: 1/1 regels geslaagd (100.0%)",
            "✅ CON-01: con01",
        ]

    def test_tweede_kandidaat_zonder_streepjes_en_subcomponent_id(self):
        marker = self.root / "marker_arai.txt"
        _write_json(self.regels / "ARAI-02SUB1.json")
        _write_validator(
            self.validators / "ARAI02SUB1.py", "ARAI02SUB1Validator", "arai", marker
        )

        validator = self.loader().load_validator("ARAI-02SUB1")

        assert validator is not None, "tweede kandidaatsnaam wordt niet meer gebruikt"
        assert marker.exists()
        assert validator.validate("d", "b", None)[1] == "arai"

    def test_custom_id_met_een_component_blijft_toegestaan(self):
        marker = self.root / "marker_customx01.txt"
        _write_json(self.regels / "CUSTOMX01.json")
        _write_validator(
            self.validators / "CUSTOMX01.py", "CUSTOMX01Validator", "customx01", marker
        )

        validator = self.loader().load_validator("CUSTOMX01")

        assert validator is not None, "geen restrictie tot de 53 standaard-IDs"
        assert marker.exists()

    def test_tweede_onafhankelijke_custom_root_blijft_toegestaan(self):
        other = _mkroot()
        marker = other / "marker_other.txt"
        _write_json(other / "regels" / "CON-09.json")
        _write_validator(
            other / "validators" / "CON_09.py", "CON09Validator", "other", marker
        )

        validator = self.loader(other / "regels").load_validator("CON-09")

        assert validator is not None, "rootkeuze zelf mag niet beperkt worden"
        assert marker.exists()

    def test_ontbrekende_bestanden_geven_none_zonder_fout(self):
        loader = self.loader()
        assert loader.load_json_config("CON-77") is None
        assert loader.load_validator("CON-77") is None

        _write_json(self.regels / "CON-78.json")
        assert loader.load_json_config("CON-78") is not None
        assert loader.load_validator("CON-78") is None, "python ontbreekt"

    def test_interne_symlinks_binnen_beide_roots_blijven_werken(self):
        marker = self.root / "marker_con03.txt"
        _write_json(self.regels / "_data" / "CON-03.json")
        _write_validator(
            self.validators / "_impl" / "CON_03.py", "CON03Validator", "con03", marker
        )
        (self.regels / "CON-03.json").symlink_to(self.regels / "_data" / "CON-03.json")
        (self.validators / "CON_03.py").symlink_to(
            self.validators / "_impl" / "CON_03.py"
        )

        validator = self.loader().load_validator("CON-03")

        assert validator is not None, "interne symlinks mogen niet geblokkeerd worden"
        assert marker.exists()
        assert validator.validate("d", "b", None)[1] == "con03"


class TestLexicaleSiblingKeuze(_LoaderTestBase):
    def test_validators_dir_is_lexicale_sibling_bij_regels_dir_symlink(self):
        lex = self.root / "lex"
        real = self.root / "real"
        lex.mkdir()
        (real / "regels").mkdir(parents=True)

        marker_lex = self.root / "marker_lex.txt"
        marker_resolved = self.root / "marker_resolved.txt"
        _write_json(real / "regels" / "CON-02.json")
        _write_validator(
            lex / "validators" / "CON_02.py", "CON02Validator", "lex", marker_lex
        )
        _write_validator(
            real / "validators" / "CON_02.py",
            "CON02Validator",
            "resolved",
            marker_resolved,
        )
        link = lex / "regels"
        link.symlink_to(real / "regels", target_is_directory=True)

        validator = self.loader(link).load_validator("CON-02")

        assert validator is not None
        assert (
            validator.validate("d", "b", None)[1] == "lex"
        ), "siblingkeuze moet lexicaal blijven, niet na resolving"
        assert marker_lex.exists()
        assert not marker_resolved.exists()


# --------------------------------------------------------------------------
# Negatief: ID-vorm en padconfinement
# --------------------------------------------------------------------------


class TestRegelIdConfinement(_LoaderTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.evil_marker = self.root / "marker_evil_id.txt"
        _write_json(self.outside / "TRAV01.json", {"geheim": "buiten"})
        _write_validator(
            self.outside / "TRAV01.py", "TRAV01Validator", "evil", self.evil_marker
        )

    def test_id_moet_een_enkele_bestandsnaamcomponent_zijn(self):
        loader = self.loader()
        ongeldig = [
            "",
            ".",
            "..",
            "sub/CON-01",
            "../outside/TRAV01",
            "regels/../../outside/TRAV01",
            os.sep + "outside" + os.sep + "TRAV01",
            "outside\\TRAV01",
            "CON\x00-01",
        ]

        # Per ID twee losse subTests: een falende JSON-assert mag de
        # validatorcheck van datzelfde ID niet verbergen.
        for regel_id in ongeldig:
            with self.subTest(regel_id=regel_id, methode="load_json_config"):
                assert loader.load_json_config(regel_id) is None
            with self.subTest(regel_id=regel_id, methode="load_validator"):
                assert loader.load_validator(regel_id) is None

    def test_traversal_id_importeert_geen_python_buiten_de_root(self):
        loader = self.loader()
        regel_id = "../outside/TRAV01"

        # Eerst beide aanroepen, dan pas asserten: anders stopt de test op de
        # JSON-assert en wordt de import (het markerbewijs) nooit bereikt.
        json_config = loader.load_json_config(regel_id)
        validator = loader.load_validator(regel_id)

        assert not self.evil_marker.exists(), "code buiten de root is toch uitgevoerd"
        assert json_config is None
        assert validator is None

    def test_ongeldig_id_wordt_geweigerd_ondanks_gevulde_caches(self):
        loader = self.loader()
        # '..' en een backslash zijn op POSIX geen padtraversal richting een
        # bestaand bestand, dus zonder cachepoison zouden ze sowieso None geven;
        # de gevulde caches maken de weigering vóór de cachelookup pas echt
        # aantoonbaar (Path('..').name is '..', dus een naam-check volstaat niet).
        for regel_id in ("..", "../outside/TRAV01", "outside\\TRAV01"):
            with self.subTest(regel_id=regel_id):
                loader._json_cache[regel_id] = {"id": regel_id, "geheim": "buiten"}
                loader._validators_cache[regel_id] = object()

                json_config = loader.load_json_config(regel_id)
                validator = loader.load_validator(regel_id)

                assert json_config is None, "cache omzeilt ID-check"
                assert validator is None, "cache omzeilt ID-check"

    def test_absoluut_id_bereikt_geen_bestanden_buiten_de_roots(self):
        abs_id = str(self.outside / "ABS01")
        assert "-" not in abs_id, "tempnaam moet streepjesvrij zijn voor deze test"
        marker = self.root / "marker_abs.txt"
        _write_json(self.outside / "ABS01.json", {"geheim": "buiten"})
        _write_validator(self.outside / "ABS01.py", "ABS01Validator", "abs", marker)

        loader = self.loader()

        # Beide aanroepen vóór de asserts, zodat het importmarkerbewijs
        # daadwerkelijk ontstaat op de oude code.
        json_config = loader.load_json_config(abs_id)
        validator = loader.load_validator(abs_id)

        assert not marker.exists(), "absoluut ID voerde code buiten de root uit"
        assert json_config is None
        assert validator is None


class TestPadConfinement(_LoaderTestBase):
    def test_uitgaande_json_symlink_wordt_geblokkeerd(self):
        _write_json(self.outside / "EVIL-01.json", {"geheim": "buiten"})
        (self.regels / "EVIL-01.json").symlink_to(self.outside / "EVIL-01.json")

        loader = self.loader()

        assert loader.load_json_config("EVIL-01") is None
        assert loader.load_validator("EVIL-01") is None

    def test_uitgaande_python_symlink_wordt_geblokkeerd(self):
        marker = self.root / "marker_evil_py.txt"
        _write_json(self.regels / "EVIL-02.json")
        _write_validator(self.outside / "EVIL_02.py", "EVIL02Validator", "evil", marker)
        (self.validators / "EVIL_02.py").symlink_to(self.outside / "EVIL_02.py")

        validator = self.loader().load_validator("EVIL-02")

        assert validator is None
        assert not marker.exists(), "python buiten de root is toch geïmporteerd"

    def test_symlinkloop_en_dangling_symlink_geven_gecontroleerd_none(self):
        (self.regels / "LOOP-01.json").symlink_to(self.regels / "LOOP-01.json")
        (self.regels / "DANG-01.json").symlink_to(self.outside / "bestaat-niet.json")
        _write_json(self.regels / "LOOP-02.json")
        (self.validators / "LOOP_02.py").symlink_to(self.validators / "LOOP_02.py")

        loader = self.loader()

        assert loader.load_json_config("LOOP-01") is None
        assert loader.load_json_config("DANG-01") is None
        assert loader.load_validator("LOOP-01") is None
        assert loader.load_validator("LOOP-02") is None


if __name__ == "__main__":
    unittest.main(verbosity=2)
