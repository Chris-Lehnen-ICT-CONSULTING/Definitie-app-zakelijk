"""Tests voor scripts/silent_except_ratchet.py (DEF-393/DEF-609).

De ratchet is de meetbasis onder DEF-393: als `classify()` een stille handler
verkeerd indeelt, verschuift de baseline en verdwijnt schuld uit beeld. Deze
tests leggen het gedrag per categorie vast, inclusief de randgevallen die de
review van PR #390 aanwees.

Let op bij het uitbreiden: de pre-commit-hook `check-silent-exceptions.py`
blokkeert bestanden die het patroon "brede except gevolgd door pass/return"
letterlijk bevatten. De fixtures hieronder stellen die code daarom dynamisch
samen via `_PASS`/`_RET`, zodat de hook niet op de testcode zelf aanslaat.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

import silent_except_ratchet as ser

# Zie moduledocstring: uit elkaar gehouden zodat de hook niet triggert.
_PASS = "pass"
_RET = "return None"


def _classify_source(source: str) -> list[str]:
    """Classificeer alle brede handlers in een stuk broncode."""
    import ast

    source = textwrap.dedent(source)
    tree = ast.parse(source)
    lines = source.split("\n")
    return [
        ser.classify(node, lines)
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler) and ser.is_broad(node)
    ]


class TestClassify:
    """De vier categorieën, en de randgevallen die ze kunnen verstoren."""

    def test_stille_handler_is_A(self):
        assert _classify_source(f"""
            try:
                risky()
            except Exception:
                {_PASS}
        """) == ["A"]

    def test_kale_except_is_A(self):
        assert _classify_source(f"""
            try:
                risky()
            except:  # noqa: E722
                {_RET}
        """) == ["A"]

    def test_gelogde_handler_is_B(self):
        assert _classify_source("""
            try:
                risky()
            except Exception as e:
                logger.warning("mislukt: %s", e)
        """) == ["B"]

    def test_streamlit_feedback_telt_als_B(self):
        assert _classify_source("""
            try:
                risky()
            except Exception as e:
                st.error(f"mislukt: {e}")
        """) == ["B"]

    def test_hergooiende_handler_is_C(self):
        assert _classify_source("""
            try:
                risky()
            except Exception:
                raise
        """) == ["C"]

    def test_marker_maakt_stille_handler_D(self):
        assert _classify_source(f"""
            try:
                risky()
            # Intentional broad catch: externe parser gooit van alles
            except Exception:
                {_PASS}
        """) == ["D"]

    def test_specifieke_exception_telt_niet_mee(self):
        assert _classify_source(f"""
            try:
                risky()
            except ValueError:
                {_PASS}
        """) == []

    def test_tuple_met_exception_telt_wel_mee(self):
        assert _classify_source(f"""
            try:
                risky()
            except (KeyError, Exception):
                {_PASS}
        """) == ["A"]

    @pytest.mark.xfail(
        reason="DEF-609: ast.walk pakt geneste scopes mee, dus dit telt nu als C",
        strict=True,
    )
    def test_raise_in_geneste_functie_telt_niet_als_hergooien(self):
        """Een raise in een geneste def verlaat de handler niet.

        Dit legt de bekende onderschatting uit DEF-609 vast: zolang deze test
        xfail is, weten we dat de baseline een ondergrens is. Zodra de scope-fix
        landt slaat hij om naar XPASS en moet de baseline opnieuw worden gezet.
        """
        assert _classify_source(f"""
            try:
                risky()
            except Exception:
                def _herstel():
                    raise RuntimeError("elders")
                {_PASS}
        """) == ["A"]


class TestIsBroad:
    def test_herkent_exception_en_baseexception(self):
        import ast

        for naam in ("Exception", "BaseException"):
            tree = ast.parse(f"try:\n    x()\nexcept {naam}:\n    {_PASS}\n")
            handlers = [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)]
            assert ser.is_broad(handlers[0]) is True

    def test_kale_except_is_breed(self):
        import ast

        tree = ast.parse(f"try:\n    x()\nexcept:\n    {_PASS}\n")
        handlers = [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)]
        assert ser.is_broad(handlers[0]) is True


class TestScan:
    def test_telt_per_categorie_over_meerdere_bestanden(self, tmp_path: Path):
        (tmp_path / "a.py").write_text(
            textwrap.dedent(f"""
                try:
                    x()
                except Exception:
                    {_PASS}
            """),
            encoding="utf-8",
        )
        (tmp_path / "b.py").write_text(
            textwrap.dedent("""
                try:
                    x()
                except Exception as e:
                    logger.error("boem: %s", e)
            """),
            encoding="utf-8",
        )

        counts, silent = ser.scan(files=sorted(tmp_path.glob("*.py")), base=tmp_path)

        assert counts["A"] == 1
        assert counts["B"] == 1
        assert [rel for rel, _, _ in silent] == ["a.py"]

    def test_onparsebaar_bestand_wordt_overgeslagen(self, tmp_path: Path):
        (tmp_path / "kapot.py").write_text("def (:\n", encoding="utf-8")
        counts, silent = ser.scan(files=[tmp_path / "kapot.py"], base=tmp_path)
        assert sum(counts.values()) == 0
        assert silent == []


class TestFailClosed:
    """De guards die voorkomen dat de gate stil groen wordt."""

    def test_lege_scan_breekt_af(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "een.py").write_text("x = 1\n", encoding="utf-8")

        with pytest.raises(SystemExit) as exc:
            ser.iter_source_files(src=src, min_expected=100)

        assert "vals-groene gate" in str(exc.value)

    def test_checkout_onder_archive_wordt_niet_weggefilterd(self, tmp_path: Path):
        """Regressie: skip-filters mogen niet op het absolute pad matchen."""
        repo = tmp_path / "archive" / "repo"
        src = repo / "src"
        src.mkdir(parents=True)
        for i in range(3):
            (src / f"m{i}.py").write_text("x = 1\n", encoding="utf-8")

        gevonden = ser.iter_source_files(src=src, min_expected=1)

        assert len(gevonden) == 3, "pad met 'archive/' erin mag niet gefilterd worden"
