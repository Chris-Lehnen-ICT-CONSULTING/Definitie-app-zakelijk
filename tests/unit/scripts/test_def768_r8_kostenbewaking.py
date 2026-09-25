"""DEF-768 R8 — proefidentiteit, kostenbewaking en payloadwacht (offline).

Voorbereiding van de ADR-003-proef (logs/def768/livevervolg-proefvoorstel-
technisch-v1.md §3/§6, met de leidende correcties van root): 68 modelstappen
(6 ontwikkeling, 6 verifier-only, 40 t_eind, 16 t_herhaling), reserve 0,
cumulatief 427, fail-closed routerbudget USD 25 en per-fase callcaps.

Bewijst mechaniek, geen modelkwaliteit en geen factuurgrens:

* elke stap reserveert vóór het netwerk duurzaam een kostengrens uit de
  vaste bytegrens, een expliciete overheadmarge en `max_tokens`; het
  grootboek weigert zodra de lopende som (werkelijk waar bekend, anders de
  grens) plus de nieuwe grens het plafond zou overschrijden;
* een crash (reservering zonder afsluiting) en een timeout zonder usage
  tellen met hun grens; een werkelijke overschrijding telt met haar werkelijke
  bedrag;
* een niet-geaccepteerd geval stopt de proef duurzaam; een fase start pas als
  haar voorganger volledig geaccepteerd is; V en T delen code- en
  configuratiebinding;
* de SDK-wacht weigert vóór het netwerk alles buiten de toegelaten
  platte-tekstpayload (tools, caching, niet-tekstblokken, thinking aan, ander
  model of `max_tokens`, te veel bytes) en controleert achteraf de usage.

Geen netwerk, geen echte of betaalde call; tijdelijke grootboeken.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefgrootboek as gb

pytestmark = [pytest.mark.unit]

H = "a" * 64
V = "validation"
W = "ess05_verification"


def _binding(dataset: str = H, code: str = "c" * 64, config: str = "d" * 64, n=4):
    return {
        "dataset_sha256": dataset,
        "herhaal_ids": [f"X{i}" for i in range(n)],
        "code_sha256": code,
        "config_sha256": config,
        "freeze_sha256": "f" * 64,
    }


def _boek(tmp_path: Path) -> gb.Grootboek:
    return gb.Grootboek.nieuw(tmp_path / "r8" / "callgrootboek.jsonl", gb.R8)


def _stap(boek, fase, poging, index, *, binding=None, invoer=H):
    """Reserveer stap `index` van `poging` zoals `Stappenpoging` dat doet."""
    taken = gb.R8.fasestappen[fase]
    namen = ("beoordeling", "verificatie") if len(taken) == 2 else ("verificatie",)
    return boek.reserveer(
        fase,
        f"{poging}/{namen[index]}",
        invoer_sha256=invoer,
        binding=binding,
        poging=poging,
        stap=namen[index],
        vorige_stap=namen[index - 1] if index else None,
        task_type=taken[index],
    )


def _geval(boek, fase, poging, *, geaccepteerd=True, binding=None, invoer=H):
    for i in range(len(gb.R8.fasestappen[fase])):
        res = _stap(boek, fase, poging, i, binding=binding, invoer=invoer)
        boek.sluit(res["seq"], "voltooid", netwerk_gestart=True)
    boek.registreer_geval(fase, poging, geaccepteerd=geaccepteerd, reden="synthetisch")


def _ontwikkeling_klaar(boek):
    for i in range(3):
        _geval(boek, "ontwikkeling", f"ontwikkeling|D{i}|1")


V_BINDING = {**_binding(n=0), "dataset_sha256": "b" * 64}


# --- identiteit en begroting --------------------------------------------------------


class TestIdentiteit:
    def test_r8_telling_reserve_en_voorganger(self):
        r8 = gb.R8
        assert r8.proef_id == "DEF-768-AI-20260925-R8"
        assert dict(r8.fasecaps) == {
            "ontwikkeling": 6,
            "verificatie_alleen": 6,
            "t_eind": 40,
            "t_herhaling": 16,
        }
        assert r8.reserve_max == 0
        assert r8.totaal_max == 68
        assert r8.voorganger is gb.R7
        assert r8.cumulatief_max == 427
        assert r8.modelstappen_per_geval == 2

    def test_stappen_en_volgorde_per_fase(self):
        assert dict(gb.R8.fasestappen) == {
            "ontwikkeling": (V, W),
            "verificatie_alleen": (W,),
            "t_eind": (V, W),
            "t_herhaling": (V, W),
        }
        assert dict(gb.R8.fasevolgorde) == {
            "ontwikkeling": (),
            "verificatie_alleen": ("ontwikkeling",),
            "t_eind": ("verificatie_alleen",),
            "t_herhaling": ("t_eind",),
        }
        assert gb.R8.stop_bij_eerste_fout is True
        assert gb.R8.gedeelde_codebinding is True

    def test_oude_identiteiten_ongewijzigd(self):
        for oud in (gb.R1, gb.R2, gb.R3, gb.R4, gb.R5, gb.R6, gb.R7):
            assert oud.kostenbewaking is None
            assert oud.fasestappen is None
            assert oud.stop_bij_eerste_fout is False
        assert gb.R7.totaal_max == 40 and gb.R7.cumulatief_max == 362

    def test_kostenbewaking_expliciet_en_in_nanodollar(self):
        kb = gb.R8.kostenbewaking
        assert kb.plafond_nusd == 25_000_000_000
        assert kb.model == "claude-opus-5"
        # Routertarief claude-opus-5: $5 / $25 per 1M tokens.
        assert (kb.tarief_invoer_nusd, kb.tarief_uitvoer_nusd) == (5_000, 25_000)
        assert kb.max_tokens == 3000
        assert kb.overhead_tokens == 12_000
        assert dict(kb.bytegrens) == {V: 36_000, W: 48_000}

    def test_stapgrens_berekening(self):
        kb = gb.R8.kostenbewaking
        # (bytegrens + overhead) × invoertarief + max_tokens × uitvoertarief
        assert kb.stapgrens_nusd(V) == (36_000 + 12_000) * 5_000 + 3000 * 25_000
        assert kb.stapgrens_nusd(V) == 315_000_000
        assert kb.stapgrens_nusd(W) == (48_000 + 12_000) * 5_000 + 3000 * 25_000
        assert kb.stapgrens_nusd(W) == 375_000_000
        with pytest.raises(gb.BudgetSchendingError, match="onbekende taak"):
            kb.stapgrens_nusd("definition_core")

    def test_volledige_begroting_past_binnen_het_plafond(self):
        # 3 + 20 + 8 volledige ketens à 0,69 plus 6 verificaties à 0,375.
        assert gb.begroting_nusd(gb.R8) == 23_640_000_000
        assert gb.begroting_nusd(gb.R8) <= gb.R8.kostenbewaking.plafond_nusd

    def test_r8_opent_alleen_onder_eigen_identiteit(self, tmp_path):
        boek = _boek(tmp_path)
        with pytest.raises(gb.BudgetSchendingError):
            gb.Grootboek.open(boek.pad, gb.R7)
        assert gb.Grootboek.open(boek.pad, gb.R8).identiteit is gb.R8


# --- kostenreservering ------------------------------------------------------------------


class TestKostenreservering:
    def test_reservering_draagt_taak_en_kostengrens(self, tmp_path):
        boek = _boek(tmp_path)
        res = _stap(boek, "ontwikkeling", "ontwikkeling|D0|1", 0)
        assert res["task_type"] == V
        assert res["kosten_grens_nusd"] == 315_000_000
        regels = boek.pad.read_text(encoding="utf-8").splitlines()
        assert json.loads(regels[-1])["kosten_grens_nusd"] == 315_000_000

    def test_zonder_taak_of_poging_geweigerd(self, tmp_path):
        boek = _boek(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match="task_type"):
            boek.reserveer(
                "ontwikkeling",
                "ontwikkeling|D0|1/beoordeling",
                invoer_sha256=H,
                poging="ontwikkeling|D0|1",
                stap="beoordeling",
                vorige_stap=None,
            )
        with pytest.raises(gb.BudgetSchendingError, match="meerstapspoging"):
            boek.reserveer(
                "ontwikkeling", "ontwikkeling|D0|1", invoer_sha256=H, task_type=V
            )
        assert boek.samenvatting()["totaal"] == 0

    def test_taak_buiten_de_vaste_volgorde_geweigerd(self, tmp_path):
        boek = _boek(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match="taak"):
            boek.reserveer(
                "ontwikkeling",
                "ontwikkeling|D0|1/beoordeling",
                invoer_sha256=H,
                poging="ontwikkeling|D0|1",
                stap="beoordeling",
                vorige_stap=None,
                task_type=W,
            )

    def test_lopende_stand_telt_grens_werkelijk_en_crash(self, tmp_path):
        boek = _boek(tmp_path)
        a = _stap(boek, "ontwikkeling", "ontwikkeling|D0|1", 0)
        boek.sluit(
            a["seq"], "voltooid", netwerk_gestart=True, kosten_werkelijk_nusd=50_000_000
        )
        b = _stap(boek, "ontwikkeling", "ontwikkeling|D0|1", 1)
        boek.sluit(b["seq"], "technisch", netwerk_gestart=True)  # timeout, geen usage
        _stap(boek, "ontwikkeling", "ontwikkeling|D1|1", 0)  # crash: nooit gesloten
        stand = gb.Grootboek.open(boek.pad, gb.R8).kostenstand()
        assert stand["gereserveerd_nusd"] == 315_000_000 * 2 + 375_000_000
        assert stand["werkelijk_bekend_nusd"] == 50_000_000
        # Werkelijk waar bekend (50M), anders de grens (375M timeout, 315M crash).
        assert stand["lopend_nusd"] == 50_000_000 + 375_000_000 + 315_000_000

    def test_werkelijke_overschrijding_telt_met_haar_werkelijke_bedrag(self, tmp_path):
        boek = _boek(tmp_path)
        a = _stap(boek, "ontwikkeling", "ontwikkeling|D0|1", 0)
        boek.sluit(
            a["seq"],
            "voltooid",
            netwerk_gestart=True,
            kosten_werkelijk_nusd=900_000_000,
        )
        assert boek.kostenstand()["lopend_nusd"] == 900_000_000

    def test_plafond_weigert_voor_het_netwerk_en_blijft_na_heropenen(self, tmp_path):
        boek = _boek(tmp_path)
        a = _stap(boek, "ontwikkeling", "ontwikkeling|D0|1", 0)
        # Een (onmogelijk grote) werkelijke overschrijding vult het plafond bijna.
        boek.sluit(
            a["seq"],
            "voltooid",
            netwerk_gestart=True,
            kosten_werkelijk_nusd=24_700_000_000,
        )
        with pytest.raises(gb.BudgetSchendingError, match="kostenplafond"):
            _stap(boek, "ontwikkeling", "ontwikkeling|D0|1", 1)
        heropend = gb.Grootboek.open(boek.pad, gb.R8)
        with pytest.raises(gb.BudgetSchendingError, match="kostenplafond"):
            _stap(heropend, "ontwikkeling", "ontwikkeling|D0|1", 1)
        assert heropend.samenvatting()["totaal"] == 1

    def test_samenvatting_toont_kosten(self, tmp_path):
        boek = _boek(tmp_path)
        _stap(boek, "ontwikkeling", "ontwikkeling|D0|1", 0)
        kosten = boek.samenvatting()["kosten"]
        assert kosten["plafond_nusd"] == 25_000_000_000
        assert kosten["lopend_nusd"] == 315_000_000
        assert kosten["resterend_nusd"] == 25_000_000_000 - 315_000_000

    def test_slot_sluit_een_tweede_runner_uit(self, tmp_path):
        with (
            gb.Proefslot(tmp_path / "slot"),
            pytest.raises(gb.BudgetSchendingError, match="slot"),
            gb.Proefslot(tmp_path / "slot"),
        ):
            pass

    def test_cumulatief_427_past_428_niet(self, tmp_path):
        from tests.unit.scripts.test_def768_r3_proef import _boek as keten_boek

        # 359 werkelijke R1–R7-calls: vijf rondes à 57 en twee T-rondes à 37.
        voorgangers = []
        for naam, identiteit, n in (
            ("r7", gb.R7, 37),
            ("r6", gb.R6, 37),
            ("r5", gb.R5, 57),
            ("r4", gb.R4, 57),
            ("r3", gb.R3, 57),
            ("r2", gb.R2, 57),
            ("r1", gb.R1, 57),
        ):
            keten_boek(tmp_path / naam, identiteit, n)
            voorgangers.append(
                gb.Grootboek.lees(tmp_path / naam / "callgrootboek.jsonl", identiteit)
            )
        boek = _boek(tmp_path)
        gb.controleer_cumulatief(boek, voorgangers, 68)
        with pytest.raises(gb.BudgetSchendingError, match="427"):
            gb.controleer_cumulatief(boek, voorgangers, 69)


# --- stop- en volgorderegel, gedeelde binding ---------------------------------------


class TestStopEnVolgorde:
    def test_geweigerd_geval_stopt_de_proef_duurzaam(self, tmp_path):
        boek = _boek(tmp_path)
        _geval(boek, "ontwikkeling", "ontwikkeling|D0|1", geaccepteerd=False)
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            _stap(boek, "ontwikkeling", "ontwikkeling|D1|1", 0)
        heropend = gb.Grootboek.open(boek.pad, gb.R8)
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            _stap(heropend, "ontwikkeling", "ontwikkeling|D1|1", 0)

    def test_geval_alleen_na_volledig_afgesloten_stappen(self, tmp_path):
        boek = _boek(tmp_path)
        _stap(boek, "ontwikkeling", "ontwikkeling|D0|1", 0)
        with pytest.raises(gb.BudgetSchendingError, match="afgesloten"):
            boek.registreer_geval(
                "ontwikkeling", "ontwikkeling|D0|1", geaccepteerd=True, reden="x"
            )
        with pytest.raises(gb.BudgetSchendingError, match="geen reservering"):
            boek.registreer_geval(
                "ontwikkeling", "ontwikkeling|X|1", geaccepteerd=True, reden="x"
            )

    def test_geval_eenmalig(self, tmp_path):
        boek = _boek(tmp_path)
        _geval(boek, "ontwikkeling", "ontwikkeling|D0|1")
        with pytest.raises(gb.BudgetSchendingError, match="al geregistreerd"):
            boek.registreer_geval(
                "ontwikkeling", "ontwikkeling|D0|1", geaccepteerd=True, reden="x"
            )

    def test_fase_start_pas_na_volledig_geaccepteerde_voorganger(self, tmp_path):
        boek = _boek(tmp_path)
        _geval(boek, "ontwikkeling", "ontwikkeling|D0|1")
        with pytest.raises(gb.BudgetSchendingError, match="ontwikkeling"):
            _stap(
                boek,
                "verificatie_alleen",
                "verificatie_alleen|V0|1",
                0,
                binding=V_BINDING,
                invoer="b" * 64,
            )
        _geval(boek, "ontwikkeling", "ontwikkeling|D1|1")
        _geval(boek, "ontwikkeling", "ontwikkeling|D2|1")
        _stap(
            boek,
            "verificatie_alleen",
            "verificatie_alleen|V0|1",
            0,
            binding=V_BINDING,
            invoer="b" * 64,
        )

    def test_t_eind_pas_na_zes_geaccepteerde_verificaties(self, tmp_path):
        boek = _boek(tmp_path)
        _ontwikkeling_klaar(boek)
        with pytest.raises(gb.BudgetSchendingError, match="verificatie_alleen"):
            _stap(boek, "t_eind", "t_eind|R1|1", 0, binding=_binding())
        _v_klaar_na_ontwikkeling(boek)
        _stap(boek, "t_eind", "t_eind|R1|1", 0, binding=_binding())

    def test_v_en_t_delen_code_en_configuratie(self, tmp_path):
        boek = _boek(tmp_path)
        _ontwikkeling_klaar(boek)
        _v_klaar_na_ontwikkeling(boek)
        with pytest.raises(gb.BudgetSchendingError, match="code"):
            _stap(boek, "t_eind", "t_eind|R1|1", 0, binding=_binding(code="e" * 64))
        with pytest.raises(gb.BudgetSchendingError, match="config"):
            _stap(boek, "t_eind", "t_eind|R1|1", 0, binding=_binding(config="e" * 64))

    def test_v_en_t_hebben_elk_een_eigen_freeze(self, tmp_path):
        """Elke eindgroep bevriest op haar eigen groep (v/t); alleen code en
        configuratie zijn gedeeld (proefvoorstel par. 6.1)."""
        boek = _boek(tmp_path)
        _ontwikkeling_klaar(boek)
        _v_klaar_na_ontwikkeling(boek)
        eigen_freeze = {**_binding(), "freeze_sha256": "e" * 64}
        _stap(boek, "t_eind", "t_eind|R1|1", 0, binding=eigen_freeze)

    def test_fasestart_vooraf_toetsbaar(self, tmp_path):
        boek = _boek(tmp_path)
        boek.controleer_fasestart("ontwikkeling")
        with pytest.raises(gb.BudgetSchendingError, match="ontwikkeling"):
            boek.controleer_fasestart("verificatie_alleen")
        _geval(boek, "ontwikkeling", "ontwikkeling|D0|1", geaccepteerd=False)
        with pytest.raises(gb.BudgetSchendingError, match="gestopt"):
            boek.controleer_fasestart("ontwikkeling")

    def test_gevallen_in_samenvatting(self, tmp_path):
        boek = _boek(tmp_path)
        _geval(boek, "ontwikkeling", "ontwikkeling|D0|1")
        assert boek.samenvatting()["gevallen"] == {
            "ontwikkeling": {"geaccepteerd": 1, "geweigerd": 0}
        }


def _v_klaar_na_ontwikkeling(boek):
    for i in range(6):
        _geval(
            boek,
            "verificatie_alleen",
            f"verificatie_alleen|V{i}|1",
            binding=V_BINDING,
            invoer="b" * 64,
        )


# --- payloadwacht op de SDK-grens ---------------------------------------------------------


class _SDK:
    """Fake SDK-berichtenklasse; telt werkelijke netwerkaanroepen."""

    netwerk: list[dict] = []
    usage = {"input_tokens": 100, "output_tokens": 20}

    def __init__(self) -> None:
        self._client = SimpleNamespace(max_retries=0)

    async def create(self, **kwargs):
        type(self).netwerk.append(kwargs)
        return SimpleNamespace(
            id="msg",
            model="claude-opus-5",
            stop_reason="end_turn",
            usage=SimpleNamespace(**type(self).usage),
        )


@pytest.fixture
def sdk():
    _SDK.netwerk = []
    _SDK.usage = {"input_tokens": 100, "output_tokens": 20}
    herstel = gb.installeer_sdk_wacht(_SDK)
    yield _SDK
    herstel()


def _grens(task_type: str = V) -> gb.Stapgrens:
    return gb.R8.kostenbewaking.stapgrens(task_type)


def _payload(**anders):
    payload = {
        "model": "claude-opus-5",
        "max_tokens": 3000,
        "thinking": {"type": "disabled"},
        "system": "Systeeminstructie.",
        "messages": [{"role": "user", "content": "Beoordeel dit."}],
        "timeout": 60.0,
    }
    payload.update(anders)
    return payload


def _roep(payload, grens=None):
    res = gb.Reservering(seq=1, sleutel="s", grens=grens or _grens())

    async def aanroep():
        with gb.actief(res):
            return await _SDK().create(**payload)

    return res, asyncio.run(aanroep())


class TestPayloadwacht:
    def test_geldige_platte_tekst_gaat_door_en_telt_bytes(self, sdk):
        res, _ = _roep(_payload())
        assert len(sdk.netwerk) == 1
        body = {k: v for k, v in _payload().items() if k != "timeout"}
        verwacht = len(
            json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
        assert res.payload_bytes == verwacht
        assert res.schending is None

    @pytest.mark.parametrize(
        ("anders", "melding"),
        [
            ({"tools": [{"name": "x"}]}, "niet toegestaan"),
            ({"tool_choice": {"type": "auto"}}, "niet toegestaan"),
            ({"extra_body": {"x": 1}}, "niet toegestaan"),
            ({"stream": True}, "niet toegestaan"),
            ({"model": "claude-haiku-4-5-20251001"}, "model"),
            ({"max_tokens": 6000}, "max_tokens"),
            ({"thinking": {"type": "enabled", "budget_tokens": 1024}}, "thinking"),
            (
                {
                    "system": [
                        {
                            "type": "text",
                            "text": "s",
                            "cache_control": {"type": "ephemeral"},
                        }
                    ]
                },
                "system",
            ),
            (
                {"messages": [{"role": "user", "content": [{"type": "image"}]}]},
                "messages",
            ),
            ({"messages": [{"role": "user", "content": "x", "extra": 1}]}, "messages"),
            ({"messages": [{"role": "system", "content": "x"}]}, "messages"),
        ],
    )
    def test_niet_afgedekte_payload_geweigerd_voor_het_netwerk(
        self, sdk, anders, melding
    ):
        with pytest.raises(gb.BudgetSchendingError, match=melding):
            _roep(_payload(**anders))
        assert sdk.netwerk == []

    def test_ontbrekende_thinking_geweigerd(self, sdk):
        payload = _payload()
        del payload["thinking"]
        with pytest.raises(gb.BudgetSchendingError, match="thinking"):
            _roep(payload)
        assert sdk.netwerk == []

    def test_te_veel_bytes_geweigerd_voor_het_netwerk(self, sdk):
        te_lang = "x" * 36_001
        with pytest.raises(gb.BudgetSchendingError, match="bytegrens"):
            _roep(_payload(messages=[{"role": "user", "content": te_lang}]))
        assert sdk.netwerk == []

    def test_omit_waarden_tellen_als_afwezig(self, sdk):
        anthropic = pytest.importorskip("anthropic")
        _roep(_payload(temperature=anthropic.omit))
        assert len(sdk.netwerk) == 1

    def test_usage_boven_de_aangenomen_tokengrens_is_een_schending(self, sdk):
        body = {k: v for k, v in _payload().items() if k != "timeout"}
        grens = (
            len(json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode())
            + 12_000
        )
        sdk.usage = {"input_tokens": grens + 1, "output_tokens": 20}
        with pytest.raises(gb.BudgetSchendingError, match="aanname"):
            _roep(_payload())
        assert len(sdk.netwerk) == 1  # de aanroep gebeurde; de run stopt

    @pytest.mark.parametrize(
        "usage",
        [
            {"input_tokens": 10, "output_tokens": 3001},
            {"input_tokens": 10, "output_tokens": 1, "cache_read_input_tokens": 5},
            {"input_tokens": 10, "output_tokens": 1, "cache_creation_input_tokens": 5},
            {"input_tokens": None, "output_tokens": 1},
        ],
    )
    def test_usage_buiten_de_grens_is_een_schending(self, sdk, usage):
        sdk.usage = usage
        with pytest.raises(gb.BudgetSchendingError):
            _roep(_payload())

    def test_zonder_grens_gedraagt_de_wacht_zich_als_voorheen(self, sdk):
        res = gb.Reservering(seq=1, sleutel="s")

        async def aanroep():
            with gb.actief(res):
                return await _SDK().create(tools=[{"name": "x"}])

        asyncio.run(aanroep())
        assert len(sdk.netwerk) == 1


class TestWerkelijkeKosten:
    def test_kosten_uit_usage_in_nanodollar(self):
        kb = gb.R8.kostenbewaking
        sdk = {"usage": {"input_tokens": 8000, "output_tokens": 600}}
        assert gb.kosten_nusd(sdk, kb) == 8000 * 5_000 + 600 * 25_000

    def test_cachetokens_tellen_conservatief_mee(self):
        kb = gb.R8.kostenbewaking
        sdk = {
            "usage": {
                "input_tokens": 10,
                "output_tokens": 1,
                "cache_read_input_tokens": 4,
                "cache_creation_input_tokens": 2,
            }
        }
        assert gb.kosten_nusd(sdk, kb) == (10 + 2 * (4 + 2)) * 5_000 + 25_000

    def test_zonder_usage_onbekend(self):
        assert gb.kosten_nusd({}, gb.R8.kostenbewaking) is None
