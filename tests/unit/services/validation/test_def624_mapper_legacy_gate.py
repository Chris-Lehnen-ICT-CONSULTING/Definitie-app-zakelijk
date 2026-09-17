"""DEF-624 — CI-correctie: legacy-patterngate op `mappers._score_uit_object`.

De EPIC-010-gate "Check for deprecated attributes" (epic-010-gates.yml)
weigert elke niet-commentaarregel in src/services/ met een letterlijke
`.overall_score`-attribuuttoegang (PR #459). `_score_uit_object` is een
compatibiliteitsmapper over een dynamische legacygrens en leest het veld
daarom - zoals de mapper vóór DEF-624 al deed - via `getattr` met een
sentinel. De semantiek verandert niet: aanwezige `overall_score` vóór
`score`, expliciete None blijft None, ontbrekend wordt de bestaande default
0.0, een onleesbaar getal de bestaande fallback 0.0.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from services.validation.mappers import _score_uit_object

pytestmark = [pytest.mark.unit]

MAPPERS_PAD = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "services"
    / "validation"
    / "mappers.py"
)
# Spiegel van de CI-gate: rg -n -P "^(?!\s*#).*\.overall_score" | grep -v ValidationResult
_GATE = re.compile(r"^(?!\s*#).*\.overall_score")


def test_mappers_bevat_geen_letterlijke_overall_score_attribuuttoegang() -> None:
    treffers = [
        f"{nr}: {regel.rstrip()}"
        for nr, regel in enumerate(
            MAPPERS_PAD.read_text(encoding="utf-8").splitlines(), start=1
        )
        if _GATE.search(regel) and "ValidationResult" not in regel
    ]
    assert treffers == [], treffers


@dataclass
class _Beide:
    overall_score: Any
    score: Any


@dataclass
class _AlleenScore:
    score: Any


@dataclass
class _AlleenOverall:
    overall_score: Any


@pytest.mark.parametrize(
    ("obj", "verwacht"),
    [
        pytest.param(_Beide(0.9, 0.1), 0.9, id="overall_score_gaat_voor_score"),
        pytest.param(_Beide(None, 0.1), None, id="expliciete_none_overall_score"),
        pytest.param(_AlleenScore(0.75), 0.75, id="legacy_score"),
        pytest.param(_AlleenScore(None), None, id="expliciete_none_score"),
        pytest.param(_AlleenScore("0.5"), 0.5, id="numerieke_string"),
        pytest.param(_AlleenScore("nvt"), 0.0, id="onleesbaar_valt_terug"),
        pytest.param(_AlleenOverall(1), 1.0, id="int_wordt_float"),
        pytest.param(object(), 0.0, id="ontbrekend_is_default"),
        pytest.param(Mock(spec=[]), 0.0, id="mock_zonder_attributen"),
    ],
)
def test_score_uit_object_semantiek(obj: Any, verwacht: float | None) -> None:
    uit = _score_uit_object(obj)
    if verwacht is None:
        assert uit is None
    else:
        assert uit == verwacht and isinstance(uit, float)
