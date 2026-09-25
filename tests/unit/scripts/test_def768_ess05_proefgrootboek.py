"""DEF-768 WP7 — het callgrootboek en de netwerkbewaking van de ESS-05-proefrunner.

Het grootboek is het enige budgetgeheugen over alle fases en hervattingen:
append-only, hash-geketend, reservering vóór netwerk, een onafgesloten
reservering (crash) telt mee, nooit een stille reset. De bewaking laat per
reservering precies één fysieke aanroep toe en weigert SDK-retries. Geen
modelaanroepen hier: de providergrens is een fake.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

from services.ai.base_client import AIClientError, ChatResponse

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "ess05"))

import proefgrootboek as gb

SHA = "a" * 64
CODE = "c" * 64
CONFIG = "f" * 64
HERHAAL = ["E-00", "E-01", "E-02", "E-03"]


def _binding(
    dataset: str = SHA, code: str = CODE, herhaal=None, config: str = CONFIG
) -> dict:
    return {
        "dataset_sha256": dataset,
        "herhaal_ids": list(HERHAAL if herhaal is None else herhaal),
        "code_sha256": code,
        "config_sha256": config,
    }


def _nieuw(tmp_path: Path) -> gb.Grootboek:
    return gb.Grootboek.nieuw(tmp_path / "callgrootboek.jsonl")


def _reserveer_n(boek: gb.Grootboek, fase: str, n: int, start: int = 0) -> list[int]:
    extra = {"binding": _binding()} if fase in gb.EINDFASES else {}
    return [
        boek.reserveer(fase, f"{fase}|geval-{i}", invoer_sha256=SHA, **extra)["seq"]
        for i in range(start, start + n)
    ]


class TestGrootboekLevenscyclus:
    def test_nieuw_weigert_een_bestaand_grootboek(self, tmp_path):
        _nieuw(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match="bestaat al"):
            _nieuw(tmp_path)

    def test_openen_weigert_een_ontbrekend_grootboek(self, tmp_path):
        """Een verdwenen grootboek is nooit een stille nulstand."""
        with pytest.raises(gb.BudgetSchendingError, match="ontbreekt"):
            gb.Grootboek.open(tmp_path / "weg.jsonl")

    def test_hervatten_kent_eerdere_reserveringen(self, tmp_path):
        boek = _nieuw(tmp_path)
        boek.reserveer("ontwikkeling", "ontwikkeling|A-01|1", invoer_sha256=SHA)
        opnieuw = gb.Grootboek.open(boek.pad)
        assert opnieuw.gereserveerd("ontwikkeling|A-01|1")
        assert opnieuw.samenvatting()["totaal"] == 1

    def test_dezelfde_sleutel_nooit_twee_keer(self, tmp_path):
        """Geen tweede ontwikkelronde: een sleutel wordt één keer gereserveerd."""
        boek = _nieuw(tmp_path)
        boek.reserveer("ontwikkeling", "ontwikkeling|A-01|1", invoer_sha256=SHA)
        with pytest.raises(gb.BudgetSchendingError, match="al gereserveerd"):
            gb.Grootboek.open(boek.pad).reserveer(
                "ontwikkeling", "ontwikkeling|A-01|1", invoer_sha256=SHA
            )

    def test_invoer_van_een_fase_is_bevroren(self, tmp_path):
        boek = _nieuw(tmp_path)
        boek.reserveer("ontwikkeling", "ontwikkeling|A-01|1", invoer_sha256=SHA)
        with pytest.raises(gb.BudgetSchendingError, match="andere invoer"):
            boek.reserveer(
                "ontwikkeling", "ontwikkeling|A-02|1", invoer_sha256="b" * 64
            )

    def test_onbekende_fase_geweigerd(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="onbekende fase"):
            _nieuw(tmp_path).reserveer("extra", "extra|x", invoer_sha256=SHA)


class TestLimieten:
    @pytest.mark.parametrize(
        ("fase", "cap"),
        [("ontwikkeling", 13), ("t_eind", 20), ("t_herhaling", 8), ("g", 16)],
    )
    def test_fasecap_is_hard(self, tmp_path, fase, cap):
        boek = _nieuw(tmp_path)
        _reserveer_n(boek, fase, cap)
        extra = {"binding": _binding()} if fase in gb.EINDFASES else {}
        with pytest.raises(gb.BudgetSchendingError, match="fasecap"):
            boek.reserveer(fase, f"{fase}|te-veel", invoer_sha256=SHA, **extra)

    def test_totaal_zestig_inclusief_drie_technische_reserve(self, tmp_path):
        boek = _nieuw(tmp_path)
        for fase, cap in gb.FASECAPS.items():
            for seq in _reserveer_n(boek, fase, cap):
                boek.sluit(seq, "technisch", netwerk_gestart=True)
        for i in range(3):
            boek.reserveer(
                "ontwikkeling",
                f"ontwikkeling|geval-{i}",
                invoer_sha256=SHA,
                technische_herhaling=True,
            )
        assert boek.samenvatting()["totaal"] == 60 == gb.TOTAAL_MAX
        with pytest.raises(gb.BudgetSchendingError):
            boek.reserveer(
                "g", "g|geval-0", invoer_sha256=SHA, technische_herhaling=True
            )

    def test_reserve_alleen_na_technische_fout(self, tmp_path):
        boek = _nieuw(tmp_path)
        seq = boek.reserveer("ontwikkeling", "ontwikkeling|A-01|1", invoer_sha256=SHA)[
            "seq"
        ]
        boek.sluit(seq, "modelfout", netwerk_gestart=True)
        with pytest.raises(gb.BudgetSchendingError, match="geen technische fout"):
            boek.reserveer(
                "ontwikkeling",
                "ontwikkeling|A-01|1",
                invoer_sha256=SHA,
                technische_herhaling=True,
            )

    def test_reserve_nooit_zonder_eerdere_poging(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="geen eerdere poging"):
            _nieuw(tmp_path).reserveer(
                "ontwikkeling",
                "ontwikkeling|A-01|1",
                invoer_sha256=SHA,
                technische_herhaling=True,
            )

    def test_reserve_na_crash_en_na_niet_verzonden(self, tmp_path):
        boek = _nieuw(tmp_path)
        boek.reserveer("ontwikkeling", "ontwikkeling|A-01|1", invoer_sha256=SHA)
        seq = boek.reserveer("ontwikkeling", "ontwikkeling|A-02|1", invoer_sha256=SHA)[
            "seq"
        ]
        boek.sluit(seq, "niet_verzonden", netwerk_gestart=False)
        boek = gb.Grootboek.open(boek.pad)  # na een crash hervat
        r1 = boek.reserveer(
            "ontwikkeling",
            "ontwikkeling|A-01|1",
            invoer_sha256=SHA,
            technische_herhaling=True,
        )
        r2 = boek.reserveer(
            "ontwikkeling",
            "ontwikkeling|A-02|1",
            invoer_sha256=SHA,
            technische_herhaling=True,
        )
        assert r1["sleutel"] == "ontwikkeling|A-01|1#technisch-1"
        assert (r1["budget_bron"], r2["budget_bron"]) == ("reserve", "reserve")
        stand = boek.samenvatting()
        assert (stand["totaal"], stand["reserve"], stand["onafgesloten"]) == (4, 2, 3)


class TestAppendOnly:
    def test_crash_zonder_afsluiting_telt_mee(self, tmp_path):
        boek = _nieuw(tmp_path)
        boek.reserveer("g", "g|G1|basis|1", invoer_sha256=SHA)
        stand = gb.Grootboek.open(boek.pad).samenvatting()
        assert (stand["totaal"], stand["onafgesloten"]) == (1, 1)

    def test_eerdere_regels_blijven_ongewijzigd(self, tmp_path):
        boek = _nieuw(tmp_path)
        seq = boek.reserveer("g", "g|G1|basis|1", invoer_sha256=SHA)["seq"]
        voor = boek.pad.read_bytes()
        boek.sluit(seq, "voltooid", netwerk_gestart=True, details={"x": 1})
        assert boek.pad.read_bytes().startswith(voor)

    def test_gewijzigde_regel_breekt_de_keten(self, tmp_path):
        boek = _nieuw(tmp_path)
        boek.reserveer("g", "g|G1|basis|1", invoer_sha256=SHA)
        boek.reserveer("g", "g|G1|basis|2", invoer_sha256=SHA)
        regels = boek.pad.read_text(encoding="utf-8").splitlines()
        eerste = json.loads(regels[0])
        eerste["fase"] = "ontwikkeling"
        regels[0] = json.dumps(eerste, ensure_ascii=False, sort_keys=True)
        boek.pad.write_text("\n".join(regels) + "\n", encoding="utf-8")
        with pytest.raises(gb.BudgetSchendingError, match="keten"):
            gb.Grootboek.open(boek.pad)

    def test_afgekapte_regel_is_geen_stille_reset(self, tmp_path):
        boek = _nieuw(tmp_path)
        boek.reserveer("g", "g|G1|basis|1", invoer_sha256=SHA)
        with boek.pad.open("a", encoding="utf-8") as f:
            f.write('{"soort": "reserv')
        with pytest.raises(gb.BudgetSchendingError, match="onleesbaar"):
            gb.Grootboek.open(boek.pad)

    def test_afsluiten_is_eenmalig_en_alleen_voor_bestaande_seq(self, tmp_path):
        boek = _nieuw(tmp_path)
        seq = boek.reserveer("g", "g|G1|basis|1", invoer_sha256=SHA)["seq"]
        boek.sluit(seq, "voltooid", netwerk_gestart=True)
        with pytest.raises(gb.BudgetSchendingError, match="al afgesloten"):
            boek.sluit(seq, "voltooid", netwerk_gestart=True)
        with pytest.raises(gb.BudgetSchendingError, match="onbekende reservering"):
            boek.sluit(999, "voltooid", netwerk_gestart=True)

    def test_onbekende_afsluitstatus_geweigerd(self, tmp_path):
        boek = _nieuw(tmp_path)
        seq = boek.reserveer("g", "g|G1|basis|1", invoer_sha256=SHA)["seq"]
        with pytest.raises(gb.BudgetSchendingError, match="status"):
            boek.sluit(seq, "gelukt", netwerk_gestart=True)


class TestAnker:
    """Punt 3: terugval naar een leeg of ouder grootboek valt op via het anker."""

    def _twee(self, tmp_path):
        boek = _nieuw(tmp_path)
        boek.reserveer("g", "g|G1|basis|1", invoer_sha256=SHA)
        boek.reserveer("g", "g|G1|basis|2", invoer_sha256=SHA)
        return boek

    def test_anker_legt_teller_en_kop_vast(self, tmp_path):
        boek = self._twee(tmp_path)
        anker = json.loads(gb.ankerpad(boek.pad).read_text(encoding="utf-8"))
        assert anker["proef_id"] == gb.PROEF_ID
        assert anker["regels"] == 2
        assert anker["kop_sha256"] == boek.samenvatting()["kop_sha256"]

    def test_tot_nul_afgekapt_grootboek_is_geen_nulstand(self, tmp_path):
        boek = self._twee(tmp_path)
        boek.pad.write_bytes(b"")
        with pytest.raises(gb.BudgetSchendingError, match="anker"):
            gb.Grootboek.open(boek.pad)

    def test_verwijderde_complete_staart_valt_op(self, tmp_path):
        boek = self._twee(tmp_path)
        eerste = boek.pad.read_bytes().splitlines(keepends=True)[0]
        boek.pad.write_bytes(eerste)
        with pytest.raises(gb.BudgetSchendingError, match="anker"):
            gb.Grootboek.open(boek.pad)

    def test_complete_oudere_kopie_valt_op(self, tmp_path):
        boek = _nieuw(tmp_path)
        boek.reserveer("g", "g|G1|basis|1", invoer_sha256=SHA)
        oud = boek.pad.read_bytes()
        boek.reserveer("g", "g|G1|basis|2", invoer_sha256=SHA)
        boek.reserveer("g", "g|G1|basis|3", invoer_sha256=SHA)
        boek.pad.write_bytes(oud)
        with pytest.raises(gb.BudgetSchendingError, match="anker"):
            gb.Grootboek.open(boek.pad)

    def test_ander_grootboek_met_zelfde_lengte_valt_op(self, tmp_path):
        boek = self._twee(tmp_path)
        ander = gb.Grootboek.nieuw(tmp_path / "ander" / "callgrootboek.jsonl")
        ander.reserveer("g", "g|X|basis|1", invoer_sha256=SHA)
        ander.reserveer("g", "g|X|basis|2", invoer_sha256=SHA)
        boek.pad.write_bytes(ander.pad.read_bytes())
        with pytest.raises(gb.BudgetSchendingError, match="anker"):
            gb.Grootboek.open(boek.pad)

    def test_verwijderd_anker_is_geen_nulstand(self, tmp_path):
        boek = self._twee(tmp_path)
        gb.ankerpad(boek.pad).unlink()
        with pytest.raises(gb.BudgetSchendingError, match="anker"):
            gb.Grootboek.open(boek.pad)

    def test_nulreset_na_verwijderd_grootboek_geweigerd(self, tmp_path):
        boek = self._twee(tmp_path)
        boek.pad.unlink()
        with pytest.raises(gb.BudgetSchendingError, match="ontbreekt"):
            gb.Grootboek.open(boek.pad)
        with pytest.raises(gb.BudgetSchendingError, match="anker"):
            gb.Grootboek.nieuw(boek.pad)

    def test_crash_tussen_regel_en_anker_telt_de_reservering(
        self, tmp_path, monkeypatch
    ):
        """Crashvolgorde: regel (fsync) vóór anker; hervatten telt fail-closed."""
        boek = self._twee(tmp_path)

        def crash(*_args, **_kwargs):
            raise OSError("stroom weg")

        monkeypatch.setattr(gb, "_schrijf_anker", crash)
        with pytest.raises(OSError, match="stroom"):
            boek.reserveer("g", "g|G1|basis|3", invoer_sha256=SHA)
        monkeypatch.undo()
        hervat = gb.Grootboek.open(boek.pad)
        stand = hervat.samenvatting()
        assert (stand["totaal"], stand["onafgesloten"]) == (3, 3)
        anker = json.loads(gb.ankerpad(boek.pad).read_text(encoding="utf-8"))
        assert anker["regels"] == 3  # hersteld na controle

    def test_grootboek_meer_dan_een_regel_voor_op_anker_geweigerd(
        self, tmp_path, monkeypatch
    ):
        boek = self._twee(tmp_path)
        monkeypatch.setattr(gb, "_schrijf_anker", lambda *_a, **_k: None)
        boek.reserveer("g", "g|G1|basis|3", invoer_sha256=SHA)
        boek.reserveer("g", "g|G1|basis|4", invoer_sha256=SHA)
        monkeypatch.undo()
        with pytest.raises(gb.BudgetSchendingError, match="anker"):
            gb.Grootboek.open(boek.pad)


class TestEindbinding:
    """Punt 4: t_eind en t_herhaling aan één dataset-, herhaal- en codebinding."""

    def test_eindfase_zonder_binding_geweigerd(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="binding"):
            _nieuw(tmp_path).reserveer("t_eind", "t_eind|E-00|1", invoer_sha256=SHA)

    @pytest.mark.parametrize(
        "ander",
        [
            _binding(dataset="b" * 64),
            _binding(code="d" * 64),
            _binding(herhaal=["E-00", "E-01", "E-02", "E-09"]),
            _binding(config="e" * 64),  # reviewpunt 4: effectieve modelconfig
        ],
    )
    def test_herhaling_moet_de_eindbinding_volgen(self, tmp_path, ander):
        boek = _nieuw(tmp_path)
        boek.reserveer("t_eind", "t_eind|E-00|1", invoer_sha256=SHA, binding=_binding())
        with pytest.raises(gb.BudgetSchendingError, match="binding"):
            boek.reserveer(
                "t_herhaling",
                "t_herhaling|E-00|herhaling-1",
                invoer_sha256=ander["dataset_sha256"],
                binding=ander,
            )

    def test_herhaling_met_dezelfde_binding_toegestaan(self, tmp_path):
        boek = _nieuw(tmp_path)
        boek.reserveer("t_eind", "t_eind|E-00|1", invoer_sha256=SHA, binding=_binding())
        boek.reserveer(
            "t_herhaling",
            "t_herhaling|E-00|herhaling-1",
            invoer_sha256=SHA,
            binding=_binding(),
        )
        assert boek.samenvatting()["totaal"] == 2

    @pytest.mark.parametrize("zonder", ["config_sha256", "code_sha256"])
    def test_binding_zonder_code_of_configuratie_ongeldig(self, tmp_path, zonder):
        onvolledig = {k: v for k, v in _binding().items() if k != zonder}
        with pytest.raises(gb.BudgetSchendingError, match="ongeldige binding"):
            _nieuw(tmp_path).reserveer(
                "t_eind", "t_eind|E-00|1", invoer_sha256=SHA, binding=onvolledig
            )

    def test_reserve_weigert_andere_effectieve_configuratie(self, tmp_path):
        """Ook buiten de eindfases: een technische herhaling is dezelfde call."""
        boek = _nieuw(tmp_path)
        details = {"prompt_sha256": "p" * 64, "config_sha256": CONFIG}
        seq = boek.reserveer(
            "ontwikkeling", "ontwikkeling|A|1", invoer_sha256=SHA, details=details
        )["seq"]
        boek.sluit(seq, "technisch", netwerk_gestart=True)
        with pytest.raises(gb.BudgetSchendingError, match="configuratie"):
            boek.reserveer(
                "ontwikkeling",
                "ontwikkeling|A|1",
                invoer_sha256=SHA,
                technische_herhaling=True,
                details={**details, "config_sha256": "e" * 64},
            )
        herhaald = boek.reserveer(
            "ontwikkeling",
            "ontwikkeling|A|1",
            invoer_sha256=SHA,
            technische_herhaling=True,
            details=details,
        )
        assert herhaald["budget_bron"] == "reserve"

    def test_binding_moet_bij_de_invoerhash_horen(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="binding"):
            _nieuw(tmp_path).reserveer(
                "t_eind",
                "t_eind|E-00|1",
                invoer_sha256=SHA,
                binding=_binding(dataset="b" * 64),
            )

    def test_ontwikkeling_zonder_codebinding(self, tmp_path):
        """Vóór de freeze mag de code tussen ontwikkelcalls worden gecorrigeerd."""
        boek = _nieuw(tmp_path)
        boek.reserveer(
            "ontwikkeling", "ontwikkeling|A|1", invoer_sha256=SHA, binding=_binding()
        )
        boek.reserveer(
            "ontwikkeling",
            "ontwikkeling|B|1",
            invoer_sha256=SHA,
            binding=_binding(code="d" * 64),
        )
        assert boek.samenvatting()["per_fase"]["ontwikkeling"] == 2

    def test_reserve_behoudt_binding_en_prompt(self, tmp_path):
        boek = _nieuw(tmp_path)
        seq = boek.reserveer(
            "t_eind",
            "t_eind|E-00|1",
            invoer_sha256=SHA,
            binding=_binding(),
            details={"prompt_sha256": "p" * 64},
        )["seq"]
        boek.sluit(seq, "technisch", netwerk_gestart=True)
        with pytest.raises(gb.BudgetSchendingError, match="binding"):
            boek.reserveer(
                "t_eind",
                "t_eind|E-00|1",
                invoer_sha256=SHA,
                binding=_binding(code="d" * 64),
                technische_herhaling=True,
                details={"prompt_sha256": "p" * 64},
            )
        with pytest.raises(gb.BudgetSchendingError, match="prompt"):
            boek.reserveer(
                "t_eind",
                "t_eind|E-00|1",
                invoer_sha256=SHA,
                binding=_binding(),
                technische_herhaling=True,
                details={"prompt_sha256": "q" * 64},
            )
        herhaald = boek.reserveer(
            "t_eind",
            "t_eind|E-00|1",
            invoer_sha256=SHA,
            binding=_binding(),
            technische_herhaling=True,
            details={"prompt_sha256": "p" * 64},
        )
        assert herhaald["budget_bron"] == "reserve"


class TestSlot:
    def test_geen_parallelle_runners(self, tmp_path):
        with (
            gb.Proefslot(tmp_path / ".proef.lock"),
            pytest.raises(gb.BudgetSchendingError, match="andere runner"),
            gb.Proefslot(tmp_path / ".proef.lock"),
        ):
            pass
        with gb.Proefslot(tmp_path / ".proef.lock"):
            pass  # na vrijgeven weer beschikbaar


class _EchteClient:
    provider_name = "fake"

    def __init__(self, fout: Exception | None = None) -> None:
        self.aanroepen = 0
        self.fout = fout

    async def chat_completion(self, messages, model, **kwargs):
        self.aanroepen += 1
        if self.fout is not None:
            raise self.fout
        return ChatResponse(text="{}", tokens_used=12, model=model)


def _roep(client, **kwargs):
    return asyncio.run(
        client.chat_completion([], "m", temperature=0.0, max_tokens=5, **kwargs)
    )


class TestBewaakteClient:
    def test_zonder_reservering_geen_aanroep(self):
        echt = _EchteClient()
        with pytest.raises(gb.BudgetSchendingError, match="zonder reservering"):
            _roep(gb.BewaakteClient(echt), max_retries=0)
        assert echt.aanroepen == 0

    def test_budgetschending_is_geen_herhaalbare_clientfout(self):
        """De retrylus van AsyncGPTClient herhaalt AIClientError; dit nooit."""
        assert not issubclass(gb.BudgetSchendingError, AIClientError)

    def test_precies_een_aanroep_per_reservering(self):
        echt = _EchteClient()
        client = gb.BewaakteClient(echt)
        reservering = gb.Reservering(seq=1, sleutel="g|x")
        with gb.actief(reservering):
            _roep(client, max_retries=0)
            with pytest.raises(gb.BudgetSchendingError, match="tweede"):
                _roep(client, max_retries=0)
        assert echt.aanroepen == 1
        assert reservering.client_aanroepen == 1
        assert reservering.antwoord["text"] == "{}"

    @pytest.mark.parametrize("retries", [None, 1, 2])
    def test_sdk_retries_moeten_expliciet_nul_zijn(self, retries):
        echt = _EchteClient()
        with (
            gb.actief(gb.Reservering(seq=1, sleutel="g|x")),
            pytest.raises(gb.BudgetSchendingError, match="max_retries"),
        ):
            _roep(gb.BewaakteClient(echt), max_retries=retries)
        assert echt.aanroepen == 0

    def test_fout_van_de_provider_blijft_zichtbaar_en_telt(self):
        echt = _EchteClient(fout=AIClientError("netwerk weg"))
        reservering = gb.Reservering(seq=1, sleutel="g|x")
        with gb.actief(reservering), pytest.raises(AIClientError):
            _roep(gb.BewaakteClient(echt), max_retries=0)
        assert reservering.client_aanroepen == 1
        assert "netwerk weg" in reservering.fout


class _Usage:
    input_tokens = 100
    output_tokens = 20


class _Respons:
    id = "msg_1"
    model = "claude-x"
    stop_reason = "end_turn"
    usage = _Usage()


class _SDKClient:
    def __init__(self, max_retries: int) -> None:
        self.max_retries = max_retries


class _FakeMessages:
    netwerk = 0

    def __init__(self, max_retries: int) -> None:
        self._client = _SDKClient(max_retries)

    async def create(self, **kwargs):
        type(self).netwerk += 1
        return _Respons()


class TestSDKWacht:
    @pytest.fixture(autouse=True)
    def _installeer(self):
        _FakeMessages.netwerk = 0
        herstel = gb.installeer_sdk_wacht(_FakeMessages)
        yield
        herstel()

    def test_sdk_met_retries_wordt_voor_netwerk_geweigerd(self):
        reservering = gb.Reservering(seq=1, sleutel="t|x")
        with (
            gb.actief(reservering),
            pytest.raises(gb.BudgetSchendingError, match="retries"),
        ):
            asyncio.run(_FakeMessages(max_retries=2).create())
        assert _FakeMessages.netwerk == 0
        assert reservering.netwerk_gestart is False

    def test_een_sdk_aanroep_met_werkelijke_usage(self):
        reservering = gb.Reservering(seq=1, sleutel="t|x")
        with gb.actief(reservering):
            asyncio.run(_FakeMessages(max_retries=0).create())
            with pytest.raises(gb.BudgetSchendingError, match="tweede"):
                asyncio.run(_FakeMessages(max_retries=0).create())
        assert _FakeMessages.netwerk == 1
        assert reservering.netwerk_gestart is True
        assert reservering.sdk["usage"] == {"input_tokens": 100, "output_tokens": 20}

    def test_sdk_zonder_reservering_geweigerd(self):
        with pytest.raises(gb.BudgetSchendingError, match="zonder reservering"):
            asyncio.run(_FakeMessages(max_retries=0).create())
        assert _FakeMessages.netwerk == 0


class TestKosten:
    def test_kosten_uit_werkelijke_usage_en_routerprijs(self):
        kosten = gb.kosten(
            {"usage": {"input_tokens": 1000, "output_tokens": 100}},
            {"input": 0.000005, "output": 0.000025},
            prijs_bekend=True,
        )
        assert kosten["usd"] == pytest.approx(0.0075)
        assert kosten["bron"] == "sdk_usage×router_pricing"

    def test_zonder_usage_onbekend_met_reden(self):
        kosten = gb.kosten({}, {"input": 1.0, "output": 1.0}, prijs_bekend=True)
        assert kosten["usd"] is None
        assert "usage" in kosten["reden"]

    def test_terugvaltarief_wordt_niet_als_prijs_gebruikt(self):
        kosten = gb.kosten(
            {"usage": {"input_tokens": 1, "output_tokens": 1}},
            {"input": 1.0, "output": 1.0},
            prijs_bekend=False,
        )
        assert kosten["usd"] is None
        assert "tarief" in kosten["reden"]


class TestSchrijven:
    def test_schrijft_nooit_over_en_nooit_een_geheim(self, tmp_path):
        pad = tmp_path / "x.json"
        gb.schrijf_nieuw(pad, {"a": "sk-ant-abcdefghijklmnop"}, geheimen=())
        assert "sk-ant" not in pad.read_text(encoding="utf-8")
        with pytest.raises(FileExistsError):
            gb.schrijf_nieuw(pad, {"a": 1}, geheimen=())
        with pytest.raises(gb.BudgetSchendingError, match="geheim"):
            gb.schrijf_nieuw(
                tmp_path / "y.json", {"a": "xx-GEHEIM-xx"}, geheimen=("GEHEIM",)
            )
        assert not (tmp_path / "y.json").exists()
