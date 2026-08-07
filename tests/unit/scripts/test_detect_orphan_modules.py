"""Tests voor scripts/detect_orphan_modules.py (DEF-600/DEF-609).

Dit script was de bewijsvoering onder een verwijdering van 1.706 regels. De
review van PR #390 stelde terecht dat zulke bewijsvoering zelf getest hoort te
zijn: een vals-positief leidt hier tot het weggooien van levende code.

De tests bouwen een mini-repo in tmp_path en toetsen per import-vorm of een
module terecht wel of niet als wees wordt gemeld.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

import detect_orphan_modules as dom


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    """Bouw een mini-repo; geeft de root terug."""
    for rel, inhoud in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(inhoud), encoding="utf-8")
    return tmp_path


def _orphans(root: Path) -> set[str]:
    orphans, _ = dom.find_orphans(root=root, scan_roots=("src",), min_expected=1)
    return {rel for rel, _ in orphans}


def _entrypoints(root: Path) -> set[str]:
    _, eps = dom.find_orphans(root=root, scan_roots=("src",), min_expected=1)
    return set(eps)


class TestImportVormen:
    """Per import-vorm: wordt de geïmporteerde module herkend als levend?"""

    def test_module_zonder_importer_is_wees(self, tmp_path: Path):
        root = _repo(
            tmp_path,
            {
                "src/__init__.py": "",
                "src/gebruikt.py": "def f():\n    return 1\n",
                "src/wees.py": "def g():\n    return 2\n",
                "src/main.py": "from gebruikt import f\n",
            },
        )
        assert _orphans(root) == {"src/wees.py"}

    def test_absolute_import(self, tmp_path: Path):
        root = _repo(
            tmp_path,
            {
                "src/__init__.py": "",
                "src/doel.py": "X = 1\n",
                "src/app.py": "import doel\n",
            },
        )
        assert "src/doel.py" not in _orphans(root)

    def test_from_module_import_symbool(self, tmp_path: Path):
        root = _repo(
            tmp_path,
            {
                "src/__init__.py": "",
                "src/doel.py": "def helper():\n    return 1\n",
                "src/app.py": "from doel import helper\n",
            },
        )
        assert "src/doel.py" not in _orphans(root)

    def test_relatieve_from_dot_import(self, tmp_path: Path):
        """Regressie: `from . import x` belandde alleen in de symbool-index."""
        root = _repo(
            tmp_path,
            {
                "src/__init__.py": "",
                "src/pkg/__init__.py": "from . import doel\n",
                # exporteert bewust niets: alleen de modulenaam kan hem redden
                "src/pkg/doel.py": "_intern = 1\n",
                "src/app.py": "import pkg\n",
            },
        )
        assert "src/pkg/doel.py" not in _orphans(root)

    def test_dynamische_import_via_string(self, tmp_path: Path):
        root = _repo(
            tmp_path,
            {
                "src/__init__.py": "",
                "src/plugin.py": "_x = 1\n",
                "src/loader.py": textwrap.dedent("""\
                    import importlib

                    mod = importlib.import_module("src.plugin")
                    """),
            },
        )
        assert "src/plugin.py" not in _orphans(root)


class TestUitzonderingen:
    def test_cli_entrypoint_telt_niet_als_wees(self, tmp_path: Path):
        root = _repo(
            tmp_path,
            {
                "src/__init__.py": "",
                "src/tool.py": (
                    "def main():\n"
                    "    return 0\n"
                    "\n"
                    'if __name__ == "__main__":\n'
                    "    main()\n"
                ),
            },
        )
        assert _orphans(root) == set()
        assert _entrypoints(root) == {"src/tool.py"}

    def test_streamlit_pages_zijn_vrijgesteld(self, tmp_path: Path):
        root = _repo(
            tmp_path,
            {
                "src/__init__.py": "",
                "src/pages/overzicht.py": "x = 1\n",
            },
        )
        assert _orphans(root) == set()

    def test_dynamisch_geladen_validators_zijn_vrijgesteld(self, tmp_path: Path):
        root = _repo(
            tmp_path,
            {
                "src/__init__.py": "",
                "src/toetsregels/validators/VER_01.py": "class V:\n    pass\n",
            },
        )
        assert _orphans(root) == set()

    def test_init_bestanden_tellen_niet_mee(self, tmp_path: Path):
        root = _repo(tmp_path, {"src/__init__.py": "", "src/pkg/__init__.py": ""})
        assert _orphans(root) == set()


class TestFailClosed:
    """De guards die voorkomen dat de gate stil groen wordt."""

    def test_lege_scan_breekt_af(self, tmp_path: Path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "een.py").write_text("x = 1\n", encoding="utf-8")

        with pytest.raises(SystemExit) as exc:
            dom.iter_python_files(("src",), root=tmp_path, min_expected=100)

        assert "vals-groene gate" in str(exc.value)

    def test_checkout_onder_archive_wordt_niet_weggefilterd(self, tmp_path: Path):
        """Regressie: skip-filters mogen niet op het absolute pad matchen."""
        repo = tmp_path / "archief" / "project"
        (repo / "src").mkdir(parents=True)
        for i in range(3):
            (repo / "src" / f"m{i}.py").write_text("x = 1\n", encoding="utf-8")

        gevonden = dom.iter_python_files(("src",), root=repo, min_expected=1)

        assert len(gevonden) == 3, "pad met 'archief/' erin mag niet gefilterd worden"

    def test_pycache_wordt_wel_gefilterd(self, tmp_path: Path):
        (tmp_path / "src" / "__pycache__").mkdir(parents=True)
        (tmp_path / "src" / "echt.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "src" / "__pycache__" / "echt.py").write_text(
            "x = 1\n", encoding="utf-8"
        )

        gevonden = dom.iter_python_files(("src",), root=tmp_path, min_expected=1)

        assert [p.name for p in gevonden] == ["echt.py"]


class TestHasMainBlock:
    def test_herkent_standaardvorm(self, tmp_path: Path):
        p = tmp_path / "x.py"
        p.write_text('if __name__ == "__main__":\n    pass\n', encoding="utf-8")
        assert dom.has_main_block(p) is True

    def test_module_zonder_main_block(self, tmp_path: Path):
        p = tmp_path / "y.py"
        p.write_text("x = 1\n", encoding="utf-8")
        assert dom.has_main_block(p) is False


class TestExportedSymbols:
    def test_publieke_klassen_en_functies(self, tmp_path: Path):
        p = tmp_path / "m.py"
        p.write_text(
            "class Publiek:\n    pass\n\n"
            "def functie():\n    return 1\n\n"
            "def _prive():\n    return 2\n",
            encoding="utf-8",
        )
        assert set(dom.exported_symbols(p)) == {"Publiek", "functie"}

    def test_generieke_namen_worden_genegeerd(self, tmp_path: Path):
        p = tmp_path / "m.py"
        p.write_text("logger = 1\nT = 2\nEcht = 3\n", encoding="utf-8")
        assert set(dom.exported_symbols(p)) == {"Echt"}
