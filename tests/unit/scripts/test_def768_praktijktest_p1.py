"""DEF-768 P1 — rooktest-script ESS-05 op echte definities, offline bewezen.

Budgetbesluit Chris (optie A): max 15 modelaanroepen, geen retry/cache, alleen
ESS-05, alleen op een kopie van de database. Deze tests bewijzen de
weigeringen en de harde teller met stubs en een tijdelijke SQLite: geen
netwerk, geen echte client, geen echte database.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.ai.base_client import AIConnectionClientError, ChatResponse
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import praktijktest_p1 as p1

pytestmark = [pytest.mark.unit]

ORG = ["Synthetische Rechtbank"]
DEFINITIES = {
    "verdachte": "persoon tegen wie een redelijk vermoeden van schuld bestaat",
    "raadsman": "advocaat die een verdachte in een strafzaak bijstaat",
    "getuige": "persoon die over feiten uit eigen waarneming verklaart",
}


class _TelProvider:
    """Providerclient die elke aanroep telt; optioneel een fout."""

    def __init__(self, fout: Exception | None = None) -> None:
        self.aanroepen = 0
        self.fout = fout

    async def chat_completion(self, messages, model, **kwargs):
        self.aanroepen += 1
        if self.fout is not None:
            raise self.fout
        return ChatResponse(
            text="{}", tokens_used=3, model=model, stop_reason="end_turn"
        )


async def _een_aanroep(teller: p1.Teller, client: p1.TellendeClient) -> None:
    with teller.grens("validation", "a" * 64):
        await client.chat_completion(messages=[], model="m", max_retries=0)


def _sha(pad: Path) -> str:
    return hashlib.sha256(pad.read_bytes()).hexdigest()


@pytest.fixture
def bron_db(tmp_path) -> tuple[Path, list[int]]:
    """Drie definities in dezelfde context, als schone database zonder WAL."""
    zaad = tmp_path / "zaad" / "definities.db"
    zaad.parent.mkdir()
    repo = DefinitionRepository(str(zaad))
    ids = [
        repo.save(
            Definition(
                begrip=begrip,
                definitie=tekst,
                categorie="type",
                organisatorische_context=list(ORG),
                juridische_context=[],
                wettelijke_basis=[],
                metadata={"status": "draft", "created_by": "test"},
            )
        )
        for begrip, tekst in DEFINITIES.items()
    ]
    bron = tmp_path / "bron" / "definities.db"
    bron.parent.mkdir()
    van, naar = sqlite3.connect(zaad), sqlite3.connect(bron)
    van.backup(naar)
    naar.execute("PRAGMA journal_mode=DELETE")
    van.close()
    naar.close()
    return bron, ids


@pytest.fixture
def geen_client(monkeypatch):
    """Elke poging een echte client te maken faalt de test."""

    def _verboden(*_a, **_k):
        raise AssertionError("er mag geen echte client worden gemaakt")

    monkeypatch.setattr("services.ai.create_ai_client", _verboden)
    monkeypatch.setattr(p1, "echte_client", _verboden)


class TestHardeTeller:
    def test_stopt_bij_15_zonder_16e_provideraanroep(self):
        teller, provider = p1.Teller(), _TelProvider()
        client = p1.TellendeClient(provider, teller)
        for _ in range(15):
            asyncio.run(_een_aanroep(teller, client))
        with pytest.raises(p1.PlafondstopError, match="plafond van 15"):
            asyncio.run(_een_aanroep(teller, client))
        assert provider.aanroepen == 15
        assert len(teller.aanroepen) == 15
        assert teller.gestopt == "plafond van 15 modelaanroepen bereikt"

    def test_nooit_retry_tweede_poging_geweigerd(self):
        teller, provider = p1.Teller(), _TelProvider()
        client = p1.TellendeClient(provider, teller)

        async def _twee_pogingen():
            with teller.grens("validation", "a" * 64):
                await client.chat_completion(messages=[], model="m", max_retries=0)
                await client.chat_completion(messages=[], model="m", max_retries=0)

        with pytest.raises(p1.PlafondstopError, match="geen retry"):
            asyncio.run(_twee_pogingen())
        assert provider.aanroepen == 1
        assert teller.gestopt is not None
        with pytest.raises(p1.PlafondstopError, match="teller gestopt"):
            asyncio.run(_een_aanroep(teller, client))
        assert provider.aanroepen == 1

    def test_sdk_retries_ongelijk_nul_geweigerd(self):
        teller, provider = p1.Teller(), _TelProvider()
        client = p1.TellendeClient(provider, teller)

        async def _met_retries():
            with teller.grens("validation", "a" * 64):
                await client.chat_completion(messages=[], model="m", max_retries=2)

        with pytest.raises(p1.PlafondstopError, match="max_retries"):
            asyncio.run(_met_retries())
        assert provider.aanroepen == 0

    def test_technische_fout_stopt_direct(self):
        teller = p1.Teller()
        client = p1.TellendeClient(_TelProvider(AIConnectionClientError("weg")), teller)
        with pytest.raises(AIConnectionClientError):
            asyncio.run(_een_aanroep(teller, client))
        assert teller.gestopt == "technische fout in aanroep 1"
        assert teller.aanroepen[0]["fout"].startswith("AIConnectionClientError")

    def test_andere_taak_dan_ess05_geweigerd(self):
        teller = p1.Teller()
        with (
            pytest.raises(p1.PlafondstopError, match="alleen ESS-05"),
            teller.grens("definition_core", "a" * 64),
        ):
            pass
        assert teller.aanroepen == []

    def test_aanroep_buiten_de_teller_geweigerd(self):
        teller, provider = p1.Teller(), _TelProvider()
        client = p1.TellendeClient(provider, teller)
        with pytest.raises(p1.PlafondstopError, match="buiten de ESS-05-teller"):
            asyncio.run(client.chat_completion(messages=[], model="m", max_retries=0))
        assert provider.aanroepen == 0

    def test_sdk_teller_eist_retries_nul_en_legt_kosten_vast(self):
        class _Messages:
            def __init__(self, retries):
                self._client = SimpleNamespace(max_retries=retries)

            async def create(self, **_):
                usage = SimpleNamespace(input_tokens=1000, output_tokens=200)
                return SimpleNamespace(usage=usage)

        teller = p1.Teller(eis_kosten=True)
        herstel = p1.installeer_sdk_teller(_Messages, teller)
        try:

            async def _aanroep(retries):
                with teller.grens("ess05_verification", "b" * 64):
                    await _Messages(retries).create()

            asyncio.run(_aanroep(0))
            assert teller.aanroepen[0]["kosten_nusd"] == 1000 * 5_000 + 200 * 25_000
            with pytest.raises(p1.PlafondstopError, match="max_retries=2"):
                asyncio.run(_aanroep(2))
        finally:
            herstel()

    def test_onbekende_kosten_stoppen_de_echte_teller(self):
        teller = p1.Teller(eis_kosten=True)
        with teller.grens("validation", "a" * 64):
            pass
        assert teller.gestopt == "kosten van aanroep 1 onbekend"


class TestBudgetbesluit:
    def _besluit(self, tmp_path, **wijziging) -> Path:
        besluit = {
            "extra_modelaanroepen_max": 15,
            "records": [277, 365, 278],
            "reserve": 0,
            "retry": False,
            "cache": False,
            "lokaal_kostenplafond_usd": "1.00",
            **wijziging,
        }
        pad = tmp_path / "besluit.json"
        pad.write_text(json.dumps(besluit), encoding="utf-8")
        return pad

    def test_afwijkende_hash_geweigerd(self, tmp_path):
        pad = self._besluit(tmp_path)
        with pytest.raises(SystemExit, match="wijkt af"):
            p1.controleer_besluit(pad, "0" * 64)

    def test_ontbrekend_besluit_geweigerd(self, tmp_path):
        with pytest.raises(SystemExit, match="ontbreekt"):
            p1.controleer_besluit(tmp_path / "geen.json", "0" * 64)

    def test_passende_hash_maar_ander_plafond_geweigerd(self, tmp_path):
        pad = self._besluit(tmp_path, extra_modelaanroepen_max=16)
        with pytest.raises(SystemExit, match="extra_modelaanroepen_max"):
            p1.controleer_besluit(pad, _sha(pad))

    def test_passend_besluit_geaccepteerd(self, tmp_path):
        pad = self._besluit(tmp_path)
        assert p1.controleer_besluit(pad, _sha(pad))["records"] == [277, 365, 278]

    def test_gepind_besluit_klopt_indien_aanwezig(self):
        if not p1.BESLUIT.is_file():
            pytest.skip("logs/ is lokaal (git-ignored); besluit niet aanwezig")
        assert p1.controleer_besluit()["extra_modelaanroepen_max"] == 15

    def test_echt_met_afwijkend_besluit_maakt_geen_client_en_geen_map(
        self, tmp_path, bron_db, geen_client
    ):
        bron, ids = bron_db
        opdracht = p1.Opdracht(
            uitmap=tmp_path / "uit",
            echt=True,
            db=bron,
            records=ids,
            besluit=self._besluit(tmp_path),
            besluit_sha256="0" * 64,
        )
        with pytest.raises(SystemExit, match="wijkt af"):
            p1.voer_uit(opdracht)
        assert not (tmp_path / "uit").exists()


class TestDroogrun:
    def test_zonder_echt_geen_client_alleen_ess05_en_db_ongewijzigd(
        self, tmp_path, bron_db, geen_client, monkeypatch
    ):
        from services.orchestrators.validation_orchestrator_v2 import (
            ValidationOrchestratorV2 as Orch,
        )

        for naam in (
            "_beoordeel_bronnen",
            "_beoordeel_telbaarheid",
            "_beoordeel_verwijzingen",
            "_beoordeel_int02",
        ):
            monkeypatch.setattr(Orch, naam, _verboden_ai_regel(naam))
        bron, ids = bron_db
        voor = _sha(bron)
        s = p1.voer_uit(p1.Opdracht(uitmap=tmp_path / "uit", db=bron, records=ids))
        assert s["fout"] is None
        assert (
            _sha(bron) == voor == s["database_sha256_voor"] == s["database_sha256_na"]
        )
        assert s["database_ongewijzigd"] is True
        assert s["budgetbesluit_sha256"] is None
        aanroepen = s["aanroepen"]
        assert aanroepen, "de droogrun moet de ESS-05-route echt doorlopen"
        assert {a["task_type"] for a in aanroepen} <= {
            "validation",
            "ess05_verification",
        }
        assert {a["promptversie"] for a in aanroepen} <= {
            "ess05-interpretatie-prompt/4",
            "ess05-local-verify/1",
        }
        assert [a["volgnummer"] for a in aanroepen] == list(
            range(1, len(aanroepen) + 1)
        )
        assert all(a["provider_aanroepen"] == 1 for a in aanroepen)
        for record_id in ids:
            record = json.loads(
                (tmp_path / "uit" / f"record-{record_id}.json").read_text()
            )
            assert len(record["buren"]) == 2
            assert {b["herkomst"] for b in record["buren"]} == {"repository"}
            assert record["document"]["contract_version"] == "ess05/3"
            assert record["aanroepen"][0]["soort"] == "interpretatie"
            assert record["ui_regels"][0].startswith("ESS-05 · ")
        assert (tmp_path / "uit" / "samenvatting.md").is_file()

    def test_bestaande_uitvoermap_geweigerd(self, tmp_path, bron_db, geen_client):
        bron, ids = bron_db
        (tmp_path / "uit").mkdir()
        with pytest.raises(SystemExit, match="bestaat al"):
            p1.voer_uit(p1.Opdracht(uitmap=tmp_path / "uit", db=bron, records=ids))
        assert list((tmp_path / "uit").iterdir()) == []

    def test_main_zonder_echt_draait_droog(
        self, tmp_path, bron_db, geen_client, monkeypatch
    ):
        bron, ids = bron_db
        monkeypatch.setattr(p1, "ECHTE_DB", bron)
        monkeypatch.setattr(p1.Opdracht, "__init__", _opdracht_met(bron, ids))
        assert p1.main(["--uitmap", str(tmp_path / "uit")]) == 0

    def test_stub_citeert_letterlijk_ook_met_afwijkende_witruimte(self):
        definitie = (
            "Soort  \nrechtsbijstandverlener die als advocaat optreedt [Bron 1]."
        )
        user = (
            "Te interpreteren begrip: raadsman\nVerwante begrippen (buur-ID: term):\n"
            "- repository:277: verdachte\n\nMateriaal (gegevens; interpreteer):\n"
            f'<materiaal id="definition" herkomst="d" omvang="volledig">{definitie}'
            "</materiaal>"
        )
        ruw = p1._stubinterpretatie(user)
        citaten = [ruw["kern"]["bovenbegrip"], ruw["kern"]["kenmerken"][0]["citaat"]]
        assert all(definitie.count(c) == 1 for c in citaten)
        assert [a["onderwerp"] for a in ruw["antwoorden"]] == ["doel", "repository:277"]


def _verboden_ai_regel(naam: str):
    async def _verboden(*_a, **_k):
        raise AssertionError(f"{naam}: alleen ESS-05 mag draaien")

    return _verboden


def _opdracht_met(bron: Path, ids: list[int]):
    oorspronkelijk = p1.Opdracht.__init__

    def _init(self, uitmap, echt=False, **_):
        oorspronkelijk(self, uitmap=uitmap, echt=echt, db=bron, records=ids)

    return _init
