"""DEF-768: de G-stopguard ziet ook een door `AIServiceV2` ingepakte bewakingsweigering.

De SDK-wacht (`gb.installeer_sdk_wacht`) weigert een SDK-client met retries ≠ 0
met een `BudgetSchendingError`; `AIServiceV2.generate_definition` pakt die in
als `AIServiceError("Unexpected error in AI generation: …")`, zonder de
klassenaam. Een stopguard die alleen op de tekst `BudgetSchendingError` let,
laat de G-run dan doorlopen en elke volgende reservering verbruiken. De
weigering zelf staat op de reservering (`Reservering.schending`).

Offline: fake provider, echte SDK-wacht op een fake SDK-klasse, tijdelijk
grootboek; geen netwerk, geen G-model-, prompt- of transportwijziging.
"""

from __future__ import annotations

import asyncio
import json
import sys
from types import SimpleNamespace

import pytest

from services.ai.base_client import ChatResponse
from tests.unit.scripts.test_def768_ess05_proefrunner import (
    ROOT,
    _FakeProvider,
    _g_invoer_actueel,
    _omgeving,
    _opslag,
)

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefgrootboek as gb
import run_ess05_proef as runner


class _SDK:
    """Fake SDK-berichtenklasse; `create` wordt door de SDK-wacht bewaakt."""

    def __init__(self, max_retries: int) -> None:
        self._client = SimpleNamespace(max_retries=max_retries)

    async def create(self, **_kwargs):
        return SimpleNamespace(id="msg", model="m", stop_reason="end_turn")


@pytest.fixture
def sdk_wacht():
    herstel = gb.installeer_sdk_wacht(_SDK)
    yield
    herstel()


class _SDKProvider(_FakeProvider):
    """Doet per aanroep één SDK-aanroep met de opgegeven SDK-retries."""

    def __init__(self, max_retries: int) -> None:
        super().__init__(tekst="Ontologische categorie: type\nPersoon met een lening.")
        self.max_retries = max_retries

    async def chat_completion(self, messages, model, **kwargs):
        self.aanroepen.append({"model": model, **kwargs})
        await _SDK(self.max_retries).create()
        return ChatResponse(text=self.tekst, tokens_used=10, model=model)


def _g(provider, tmp_path):
    return asyncio.run(
        runner.voer_g_fase(
            _omgeving(provider),
            g_invoerpad=_g_invoer_actueel(tmp_path),
            uitmap=tmp_path / "uit",
            opslag=_opslag(tmp_path),
            nieuw_grootboek=True,
        )
    )


def _reserveringen(tmp_path) -> list[dict]:
    regels = _opslag(tmp_path).grootboek.read_text(encoding="utf-8").splitlines()
    return [r for r in map(json.loads, regels) if r["soort"] == "reservering"]


def test_ingepakte_sdk_weigering_stopt_de_g_run(sdk_wacht, tmp_path):
    provider = _SDKProvider(max_retries=2)
    with pytest.raises(gb.BudgetSchendingError, match="bewaking greep in"):
        _g(provider, tmp_path)
    assert len(provider.aanroepen) == 1
    assert len(_reserveringen(tmp_path)) == 1
    (pad,) = (tmp_path / "uit").rglob("calls/*.json")
    record = json.loads(pad.read_text(encoding="utf-8"))
    # De fouttekst bevat de klassenaam niet: juist daarom faalde de tekstguard.
    assert "BudgetSchendingError" not in record["fout"]
    assert "max_retries=2" in record["transport"]["bewakingsweigering"]


def test_positief_zonder_weigering_loopt_de_g_run_door(sdk_wacht, tmp_path):
    """Zelfde keten zonder weigering: alle zestien calls (de guard discrimineert)."""
    provider = _SDKProvider(max_retries=0)
    uitkomst = _g(provider, tmp_path)
    assert uitkomst["aanroepen_gestart"] == 16
    assert len(provider.aanroepen) == 16


def test_gewone_providerfout_stopt_de_g_run_niet(tmp_path):
    """Een transportfout is geen bewakingsweigering: geen stop, wel afgesloten."""
    provider = _FakeProvider(fout=ConnectionError("netwerk weg"))
    uitkomst = _g(provider, tmp_path)
    assert uitkomst["aanroepen_gestart"] == 16
    assert len(_reserveringen(tmp_path)) == 16
