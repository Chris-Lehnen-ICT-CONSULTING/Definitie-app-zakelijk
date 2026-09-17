"""Regressietests voor scripts/testing/ess02_praktijkproef.py (DEF-751).

De runner is bewijsvoering: hij moet het live-budget hard begrenzen, geen
secrets wegschrijven, nooit een productie-DB raken en de vooraf vastgelegde
betekenistoets buiten de modelprompt houden. Geen modelaanroepen hier.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from services.ai.base_client import AIClientError, ChatMessage, ChatResponse
from services.interfaces import DefinitionResponseV2
from services.prompts.prompt_service_v2 import PromptServiceV2
from toetsregels.rule_cache import get_rule_cache

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "testing"))

import ess02_praktijkproef as proef


@dataclass
class _Respons:
    stop_reason: str | None = "end_turn"
    id: str = "msg_1"
    model: str = "fake-model"
    usage: object | None = None


class _FakeSDKMessages:
    async def create(self, **kwargs):
        return _Respons(stop_reason=kwargs.get("stop"))


class _FakeSDK:
    def __init__(self) -> None:
        self.messages = _FakeSDKMessages()


class _FakeClient:
    provider_name = "fake"

    def __init__(self) -> None:
        self._client = _FakeSDK()
        self.aanroepen = 0

    async def chat_completion(
        self, messages, model, temperature=0.7, max_tokens=300, timeout=None
    ):
        self.aanroepen += 1
        await self._client.messages.create(
            stop="max_tokens" if self.aanroepen == 2 else "end_turn"
        )
        return ChatResponse(
            text=f"antwoord {self.aanroepen}", tokens_used=3, model=model
        )

    async def close(self) -> None:
        pass


async def test_budget_is_hard_en_stopt_buiten_de_retrylus():
    echt = _FakeClient()
    client = proef.RegistrerendeClient(echt, budget=2)
    bericht = [ChatMessage(role="user", content="p")]
    await client.chat_completion(bericht, model="m", max_tokens=500)
    await client.chat_completion(bericht, model="m", max_tokens=500)
    with pytest.raises(proef.LiveBudgetOverschredenError) as exc:
        await client.chat_completion(bericht, model="m", max_tokens=500)
    # Geen AIClientError: AsyncGPTClient mag de geweigerde aanroep niet herhalen.
    assert not isinstance(exc.value, AIClientError)
    assert echt.aanroepen == 2
    assert [a.volgnummer for a in client.aanroepen] == [1, 2]
    # Registratie: prompt-hash, respons en afkapping uit de ruwe SDK-respons.
    assert client.aanroepen[0].respons_tekst == "antwoord 1"
    assert client.aanroepen[0].afgekapt is False
    assert client.aanroepen[1].afgekapt is True
    assert client.aanroepen[0].prompt_sha256 == client.aanroepen[1].prompt_sha256
    assert client.aanroepen[0].max_tokens == 500


def test_afgekapt_is_onbekend_zonder_sdk_metadata():
    aanroep = proef.ModelAanroep(
        volgnummer=1,
        model_gevraagd="m",
        temperature=0.1,
        max_tokens=500,
        timeout=None,
        messages=[],
        prompt_sha256="x",
        prompt_lengte=0,
        gestart_utc="",
    )
    assert aanroep.afgekapt is None
    aanroep.sdk = {"finish_reason": "length"}
    assert aanroep.afgekapt is True


def test_scrub_verwijdert_sleutelpatronen():
    assert proef.scrub("key sk-ant-abcdefghijklmnop einde") == "key [REDACTED] einde"
    assert proef.scrub("gewone tekst") == "gewone tekst"


def test_db_buiten_projectdata_en_nooit_bestaand(tmp_path):
    with pytest.raises(SystemExit):
        proef.bevestig_buiten_productie(proef.ROOT / "data" / "definities.db")
    bestaand = tmp_path / "x.db"
    bestaand.write_bytes(b"")
    with pytest.raises(SystemExit):
        proef.bevestig_buiten_productie(bestaand)
    proef.bevestig_buiten_productie(tmp_path / "nieuw.db")


def test_live_casussen_passen_in_het_budget_en_vervolg_hangt_aan_conflict():
    assert len(proef.LIVE_CASUSSEN) <= proef.MAX_LIVE_CALLS
    ids = [c.id for c in proef.LIVE_CASUSSEN]
    assert len(ids) == len(set(ids))
    vervolg = next(c for c in proef.LIVE_CASUSSEN if c.vervolg_op)
    voorganger = next(c for c in proef.LIVE_CASUSSEN if c.id == vervolg.vervolg_op)
    assert voorganger.contract == proef.CONTRACT_CONFLICT
    assert vervolg.betekenisverduidelijking == proef.VERDUIDELIJKING_C3
    assert vervolg.documenten == voorganger.documenten == proef.CONFLICTBRONNEN


def test_ronde2_binnen_budget_en_zonder_verwachting_of_instructie_in_de_bron():
    assert (
        len(proef.LIVE_CASUSSEN_R2) <= proef.MAX_LIVE_CALLS_R2 <= proef.MAX_LIVE_CALLS
    )
    ids = [c.id for c in proef.LIVE_CASUSSEN_R2]
    assert ids[:2] == ["C3-CONFLICTBRONNEN", "C3-CONFLICTBRONNEN-verduidelijkt"]
    proces = next(c for c in proef.LIVE_CASUSSEN_R2 if c.id == "E02-004-r2")
    type_ = next(c for c in proef.LIVE_CASUSSEN_R2 if c.id == "E02-002-type-r2")
    assert proces.documenten == type_.documenten == proef.ACTIVITEITSBRON
    assert (proces.ontologische_categorie, type_.ontologische_categorie) == (
        "proces",
        "type",
    )
    bron = proef.ACTIVITEITSBRON[0]["snippet"].lower()
    for verboden in ("voldoet", "verwacht", "definieer", "slagen", "ess-02"):
        assert verboden not in bron


async def test_verwachting_staat_nooit_in_de_echte_prompt_en_bronnen_wel():
    get_rule_cache().clear_cache()
    conflict = next(c for c in proef.LIVE_CASUSSEN if c.id == "C3-CONFLICTBRONNEN")
    vervolg = next(c for c in proef.LIVE_CASUSSEN if c.vervolg_op == conflict.id)
    service = PromptServiceV2()
    for casus in (conflict, vervolg):
        prompt = (
            await service.build_generation_prompt(
                proef.maak_request(casus), context=proef.maak_context(casus)
            )
        ).text
        assert casus.verwachting not in prompt
        for bron in proef.CONFLICTBRONNEN:
            assert bron["snippet"] in prompt
    assert (
        proef.VERDUIDELIJKING_C3
        not in (
            await service.build_generation_prompt(
                proef.maak_request(conflict), context=proef.maak_context(conflict)
            )
        ).text
    )


def test_conflicttoetsen_eisen_gronden_op_de_aangeleverde_bronnen():
    casus = next(c for c in proef.LIVE_CASUSSEN if c.id == "C3-CONFLICTBRONNEN")
    response = DefinitionResponseV2(
        success=False,
        error="vraag",
        metadata={
            "error_type": "betekenisconflict",
            "betekenisconflict": {
                "vraag": "Activiteit of uitkomst?",
                "lezingen": [
                    {"lezing": "activiteit", "bron": "bron 1", "grond": "g"},
                    {"lezing": "uitkomst", "bron": "bron 2", "grond": "g"},
                ],
            },
        },
    )
    toetsen = proef.automatische_toetsen(casus, response, None, 1, 1)
    assert all(t["ok"] for t in toetsen), toetsen
    response.metadata["betekenisconflict"]["lezingen"][1]["bron"] = "bron 3"
    toetsen = proef.automatische_toetsen(casus, response, None, 1, 1)
    assert not next(t for t in toetsen if t["toets"].startswith("gronden"))["ok"]
    # Een gewone definitie is voor de conflictcasus een FAIL, geen PASS.
    gewoon = DefinitionResponseV2(success=True, metadata={})
    assert not all(
        t["ok"] for t in proef.automatische_toetsen(casus, gewoon, None, 1, 2)
    )
