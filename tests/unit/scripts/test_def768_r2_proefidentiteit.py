"""DEF-768 ronde 2 — tweede proefidentiteit in het callgrootboek.

Ronde 1 (`DEF-768-WP7-ess05-proef-20260924`) blijft ongewijzigd en de
standaard; ronde 2 (`DEF-768-AI-20260924-R2`) is een expliciete, vaste tweede
identiteit met eigen grootboek, anker, fasecaps en eindgroepen. Geen vrij
configureerbare caps of reset: alleen deze twee identiteiten bestaan.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "ess05"))

import proefgrootboek as gb

SHA = "a" * 64
CODE = "c" * 64
CONFIG = "f" * 64
FREEZE = "e" * 64
HERHAAL = ["E-00", "E-01", "E-02", "E-03"]


def _t_binding(freeze: str = FREEZE, herhaal=None) -> dict:
    return {
        "dataset_sha256": SHA,
        "herhaal_ids": list(HERHAAL if herhaal is None else herhaal),
        "code_sha256": CODE,
        "config_sha256": CONFIG,
        "freeze_sha256": freeze,
    }


def _g_binding(freeze: str = FREEZE) -> dict:
    return {**_t_binding(freeze), "herhaal_ids": []}


def _r2(tmp_path: Path) -> gb.Grootboek:
    return gb.Grootboek.nieuw(tmp_path / "r2" / "callgrootboek.jsonl", identiteit=gb.R2)


def _binding_voor(identiteit: gb.Proefidentiteit, fase: str) -> dict | None:
    groep = identiteit.eindgroep(fase)
    if groep is None:
        return None
    if identiteit is gb.R1:
        return {k: v for k, v in _t_binding().items() if k != "freeze_sha256"}
    return _g_binding() if groep.naam == "g" else _t_binding()


def _vul(boek: gb.Grootboek, identiteit: gb.Proefidentiteit) -> None:
    """Alle fasecaps volledig reserveren."""
    for fase, cap in identiteit.fasecaps.items():
        for i in range(cap):
            boek.reserveer(
                fase,
                f"{fase}|g-{i}",
                invoer_sha256=SHA,
                binding=_binding_voor(identiteit, fase),
            )


class TestIdentiteiten:
    def test_r1_is_ongewijzigd_en_de_standaard(self, tmp_path):
        assert gb.R1.proef_id == gb.PROEF_ID == "DEF-768-WP7-ess05-proef-20260924"
        assert dict(gb.R1.fasecaps) == gb.FASECAPS
        assert gb.R1.reserve_max == gb.RESERVE_MAX == 3
        assert gb.R1.totaal_max == gb.TOTAAL_MAX == 60
        assert gb.R1.bindingsvelden == gb.BINDINGSVELDEN
        boek = gb.Grootboek.nieuw(tmp_path / "callgrootboek.jsonl")
        assert boek.identiteit is gb.R1
        anker = gb.ankerpad(boek.pad).read_text(encoding="utf-8")
        assert '"proef_id": "DEF-768-WP7-ess05-proef-20260924"' in anker

    def test_r2_caps_uit_het_besluit(self):
        assert gb.R2.proef_id == "DEF-768-AI-20260924-R2"
        assert dict(gb.R2.fasecaps) == {
            "ontwikkeling": 9,
            "g_ontwikkeling": 4,
            "t_eind": 20,
            "t_herhaling": 8,
            "g": 16,
        }
        assert gb.R2.reserve_max == 3
        assert gb.R2.totaal_max == 60
        assert gb.R2.voorganger is gb.R1
        assert gb.R2.cumulatief_max == 117
        assert "freeze_sha256" in gb.R2.bindingsvelden

    def test_eindgroepen_per_identiteit(self):
        assert gb.R1.eindgroep("t_herhaling").fases == frozenset(
            {"t_eind", "t_herhaling"}
        )
        assert gb.R1.eindgroep("g") is None
        assert gb.R2.eindgroep("g").herhaal_aantal == 0
        assert gb.R2.eindgroep("t_eind").herhaal_aantal == 4
        assert gb.R2.eindgroep("ontwikkeling") is None
        assert gb.R2.eindgroep("g_ontwikkeling") is None

    def test_identiteiten_zijn_niet_te_wijzigen(self):
        with pytest.raises(AttributeError):
            gb.R2.reserve_max = 99  # type: ignore[misc]
        with pytest.raises(TypeError):
            gb.R2.fasecaps["t_eind"] = 99  # type: ignore[index]


class TestAnkerPerIdentiteit:
    def test_r2_anker_draagt_r2(self, tmp_path):
        boek = _r2(tmp_path)
        anker = gb.ankerpad(boek.pad).read_text(encoding="utf-8")
        assert '"proef_id": "DEF-768-AI-20260924-R2"' in anker
        assert gb.Grootboek.open(boek.pad, identiteit=gb.R2).identiteit is gb.R2

    def test_r2_grootboek_niet_als_r1_te_openen(self, tmp_path):
        boek = _r2(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match="hoort niet bij"):
            gb.Grootboek.open(boek.pad)

    def test_r1_grootboek_niet_als_r2_te_openen(self, tmp_path):
        r1 = gb.Grootboek.nieuw(tmp_path / "callgrootboek.jsonl")
        with pytest.raises(gb.BudgetSchendingError, match="hoort niet bij"):
            gb.Grootboek.open(r1.pad, identiteit=gb.R2)

    def test_onbekende_identiteit_geweigerd(self, tmp_path):
        eigen = gb.Proefidentiteit(
            proef_id="vrij",
            fasecaps={"ontwikkeling": 999},
            reserve_max=99,
            eindgroepen=(),
            bindingsvelden=gb.BINDINGSVELDEN,
        )
        with pytest.raises(gb.BudgetSchendingError, match="onbekende proefidentiteit"):
            gb.Grootboek.nieuw(tmp_path / "x.jsonl", identiteit=eigen)
        assert not (tmp_path / "x.jsonl").exists()


class TestR2Budget:
    @pytest.mark.parametrize(
        ("fase", "cap"),
        [("ontwikkeling", 9), ("g_ontwikkeling", 4), ("t_eind", 20),
         ("t_herhaling", 8), ("g", 16)],
    )  # fmt: skip
    def test_fasecap_is_hard(self, tmp_path, fase, cap):
        boek = _r2(tmp_path)
        binding = _binding_voor(gb.R2, fase)
        for i in range(cap):
            boek.reserveer(fase, f"{fase}|{i}", invoer_sha256=SHA, binding=binding)
        with pytest.raises(gb.BudgetSchendingError, match="fasecap"):
            boek.reserveer(fase, f"{fase}|extra", invoer_sha256=SHA, binding=binding)

    def test_g_ontwikkeling_bestaat_niet_in_r1(self, tmp_path):
        boek = gb.Grootboek.nieuw(tmp_path / "callgrootboek.jsonl")
        with pytest.raises(gb.BudgetSchendingError, match="onbekende fase"):
            boek.reserveer("g_ontwikkeling", "g_ontwikkeling|G1", invoer_sha256=SHA)

    def test_totaal_zestig_met_drie_reserve(self, tmp_path):
        boek = _r2(tmp_path)
        _vul(boek, gb.R2)
        assert boek.samenvatting()["totaal"] == 57
        for i in range(3):
            seq = boek._reserveringen()[i]["seq"]
            boek.sluit(seq, "technisch", netwerk_gestart=True)
            boek.reserveer(
                "ontwikkeling",
                f"ontwikkeling|g-{i}",
                invoer_sha256=SHA,
                technische_herhaling=True,
            )
        stand = boek.samenvatting()
        assert (stand["totaal"], stand["reserve"], stand["totaal_max"]) == (60, 3, 60)
        assert stand["proef_id"] == "DEF-768-AI-20260924-R2"
        assert stand["fasecaps"]["g_ontwikkeling"] == 4


class TestR2Eindbinding:
    def test_g_eind_vereist_binding_met_freeze(self, tmp_path):
        boek = _r2(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match="eindbinding"):
            boek.reserveer("g", "g|G1|basis|run1", invoer_sha256=SHA)
        zonder_freeze = {k: v for k, v in _g_binding().items() if k != "freeze_sha256"}
        with pytest.raises(gb.BudgetSchendingError, match="ongeldige binding"):
            boek.reserveer(
                "g", "g|G1|basis|run1", invoer_sha256=SHA, binding=zonder_freeze
            )
        assert boek.samenvatting()["totaal"] == 0

    def test_g_eind_heeft_geen_herhaal_ids(self, tmp_path):
        boek = _r2(tmp_path)
        with pytest.raises(gb.BudgetSchendingError, match="ongeldige binding"):
            boek.reserveer(
                "g", "g|G1|basis|run1", invoer_sha256=SHA, binding=_t_binding()
            )
        boek.reserveer("g", "g|G1|basis|run1", invoer_sha256=SHA, binding=_g_binding())

    def test_andere_freeze_na_eerste_eindreservering_geweigerd(self, tmp_path):
        boek = _r2(tmp_path)
        boek.reserveer("t_eind", "t_eind|E1|1", invoer_sha256=SHA, binding=_t_binding())
        with pytest.raises(gb.BudgetSchendingError, match="eindbinding"):
            boek.reserveer(
                "t_herhaling",
                "t_herhaling|E1|herhaling-1",
                invoer_sha256=SHA,
                binding=_t_binding(freeze="d" * 64),
            )
        boek.reserveer(
            "t_herhaling",
            "t_herhaling|E1|herhaling-1",
            invoer_sha256=SHA,
            binding=_t_binding(),
        )

    def test_t_en_g_groep_binden_elk_apart(self, tmp_path):
        boek = _r2(tmp_path)
        boek.reserveer("t_eind", "t_eind|E1|1", invoer_sha256=SHA, binding=_t_binding())
        # De G-groep begint zijn eigen binding (andere freeze mag).
        boek.reserveer(
            "g", "g|G1|basis|run1", invoer_sha256=SHA, binding=_g_binding("d" * 64)
        )
        with pytest.raises(gb.BudgetSchendingError, match="eindbinding"):
            boek.reserveer(
                "g", "g|G1|basis|run2", invoer_sha256=SHA, binding=_g_binding()
            )

    def test_ontwikkelfases_zonder_binding(self, tmp_path):
        boek = _r2(tmp_path)
        boek.reserveer("ontwikkeling", "ontwikkeling|E06|1", invoer_sha256=SHA)
        boek.reserveer("g_ontwikkeling", "g_ontwikkeling|G1|actueel|run1",
                       invoer_sha256=SHA)  # fmt: skip
        assert boek.samenvatting()["per_fase"]["g_ontwikkeling"] == 1


class TestAlleenLezen:
    def test_lezen_schrijft_niets(self, tmp_path):
        boek = gb.Grootboek.nieuw(tmp_path / "callgrootboek.jsonl")
        boek.reserveer("ontwikkeling", "ontwikkeling|1", invoer_sha256=SHA)
        anker = gb.ankerpad(boek.pad)
        # Crash tussen regel en anker: open() zou het anker herstellen.
        vorig = anker.read_bytes()
        boek.reserveer("ontwikkeling", "ontwikkeling|2", invoer_sha256=SHA)
        anker.write_bytes(vorig)
        grootboek_voor = boek.pad.read_bytes()
        stand = gb.Grootboek.lees(boek.pad).samenvatting()
        assert stand["totaal"] == 2
        assert anker.read_bytes() == vorig
        assert boek.pad.read_bytes() == grootboek_voor

    def test_lezen_controleert_keten_en_identiteit(self, tmp_path):
        boek = gb.Grootboek.nieuw(tmp_path / "callgrootboek.jsonl")
        boek.reserveer("ontwikkeling", "ontwikkeling|1", invoer_sha256=SHA)
        with pytest.raises(gb.BudgetSchendingError, match="hoort niet bij"):
            gb.Grootboek.lees(boek.pad, identiteit=gb.R2)
        boek.pad.write_bytes(boek.pad.read_bytes().replace(b"ontwikkeling|1", b"x"))
        with pytest.raises(gb.BudgetSchendingError):
            gb.Grootboek.lees(boek.pad)

    def test_ontbrekend_grootboek_is_geen_nulstand(self, tmp_path):
        with pytest.raises(gb.BudgetSchendingError, match="ontbreekt"):
            gb.Grootboek.lees(tmp_path / "callgrootboek.jsonl")


class TestCumulatief:
    @staticmethod
    def _r1_met(tmp_path: Path, extra_reserve: int) -> gb.Grootboek:
        r1 = gb.Grootboek.nieuw(tmp_path / "r1" / "callgrootboek.jsonl")
        _vul(r1, gb.R1)
        for i in range(extra_reserve):
            seq = r1._reserveringen()[i]["seq"]
            r1.sluit(seq, "technisch", netwerk_gestart=True)
            r1.reserveer(
                "ontwikkeling",
                f"ontwikkeling|g-{i}",
                invoer_sha256=SHA,
                technische_herhaling=True,
            )
        return gb.Grootboek.lees(r1.pad)

    def test_r1_plus_r2_nooit_boven_117(self, tmp_path):
        r1 = self._r1_met(tmp_path, extra_reserve=1)  # 58 in ronde 1
        r2 = _r2(tmp_path)
        gb.controleer_cumulatief(r2, r1, 59)
        with pytest.raises(gb.BudgetSchendingError, match="117"):
            gb.controleer_cumulatief(r2, r1, 60)

    def test_telt_eigen_reserveringen_mee(self, tmp_path):
        r1 = self._r1_met(tmp_path, extra_reserve=0)  # 57
        r2 = _r2(tmp_path)
        r2.reserveer("ontwikkeling", "ontwikkeling|E06|1", invoer_sha256=SHA)
        gb.controleer_cumulatief(r2, r1, 59)
        with pytest.raises(gb.BudgetSchendingError, match="117"):
            gb.controleer_cumulatief(r2, r1, 60)

    def test_voorganger_moet_de_juiste_identiteit_hebben(self, tmp_path):
        r2 = _r2(tmp_path)
        ander = gb.Grootboek.lees(_r2(tmp_path / "ander").pad, identiteit=gb.R2)
        with pytest.raises(gb.BudgetSchendingError, match="voorganger"):
            gb.controleer_cumulatief(r2, ander, 1)

    def test_r1_heeft_geen_voorganger(self, tmp_path):
        r1 = gb.Grootboek.nieuw(tmp_path / "callgrootboek.jsonl")
        with pytest.raises(gb.BudgetSchendingError, match="voorganger"):
            gb.controleer_cumulatief(r1, r1, 1)
