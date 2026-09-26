"""DEF-768 / ADR-003 WP5: een eigen reservering per modelstap (offline).

Een T-geval heeft twee modelstappen (conceptoordeel, semantische
verificatie). Bewijst met de volledige offline keten — runner, grootboek,
bewaakte client, `AIServiceV2`, echte ESS-05-dienst met verifier, fake
provider (en waar nodig de echte SDK-wacht op een fake SDK-klasse):

* elke feitelijke aanroep heeft een eigen reservering met dezelfde
  pogingidentiteit, eigen ruwe-antwoordhash, attributie, kosten en afsluiting;
* een reservering ontstaat pas bij de aanroep, nooit vooraf;
* een parserfout in stap 1 kost alleen de eerste reservering;
* is er geen budget voor stap 2, dan weigert het grootboek vóór de aanroep en
  stopt de run fail-closed; het plan rekent vooraf met elke stap;
* afbreken en fouten sluiten elke gemaakte reservering af;
* geen semantische retry: geen tweede stap-1/2, geen hervatting van een
  gestarte poging, geen technische herhaling van een meerstapspoging;
* geen oude goedkeuring: R1–R7 keuren één stap per geval goed; een echte
  tweestapsrun wordt vóór grootboek en netwerk geweigerd, ook programmatisch.

Geen netwerk, geen echte of betaalde call; tijdelijke grootboeken.
"""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.ai.base_client import ChatResponse
from services.validation.ess05_verification_service import aanroepgrens
from tests.fixtures.def768_fakes import (
    antwoord_uit_spec,
    is_verificatievraag,
    materiaal_uit_prompt,
    verificatie_voor,
)
from tests.unit.scripts.test_def768_ess05_proefrunner import (
    ROOT,
    _FakeProvider,
    _gevallenbestand,
    _omgeving,
)
from tests.unit.scripts.test_def768_r7_proef import _voorgangers

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefgrootboek as gb
import run_ess05_proef as runner

_CONCEPTBLOK = re.compile(
    r'<conceptoordeel candidate_hash="[0-9a-f]{64}">\n(.*?)\n</conceptoordeel>', re.S
)


def _sha(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def _sha_bestand(pad: Path) -> str:
    return hashlib.sha256(Path(pad).read_bytes()).hexdigest()


class _SDK:
    """Fake SDK-berichtenklasse met werkelijke usage; bewaakt door de SDK-wacht."""

    def __init__(self) -> None:
        self._client = SimpleNamespace(max_retries=0)

    async def create(self, **_kwargs):
        return SimpleNamespace(
            id="msg",
            model="m",
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=100, output_tokens=20),
        )


class _TweestapsProvider(_FakeProvider):
    """Beantwoordt de beoordeling met een geldig concept en de verificatie
    met een volledige verificatie van exact dat concept."""

    def __init__(
        self,
        *,
        parserfout: bool = False,
        uitkomsten: dict[str, str] | None = None,
        sdk: bool = False,
        bij_aanroep=None,
        fout_bij_verificatie: BaseException | None = None,
        fout_bij_beoordeling: BaseException | None = None,
    ) -> None:
        super().__init__()
        self.parserfout = parserfout
        self.uitkomsten = uitkomsten or {}
        self.sdk = sdk
        self.bij_aanroep = bij_aanroep
        self.fout_bij_verificatie = fout_bij_verificatie
        self.fout_bij_beoordeling = fout_bij_beoordeling
        self.stappen: list[str] = []
        self.antwoorden: list[str] = []

    async def chat_completion(self, messages, model, **kwargs):
        prompt = "\n".join(str(getattr(m, "content", "") or "") for m in messages)
        stap = "verificatie" if is_verificatievraag(prompt) else "beoordeling"
        self.stappen.append(stap)
        if self.bij_aanroep is not None:
            self.bij_aanroep(stap)
        if stap == "beoordeling" and self.fout_bij_beoordeling is not None:
            raise self.fout_bij_beoordeling
        if stap == "verificatie":
            if self.fout_bij_verificatie is not None:
                raise self.fout_bij_verificatie
            concept = json.loads(html.unescape(_CONCEPTBLOK.search(prompt).group(1)))
            tekst = json.dumps(verificatie_voor(concept, uitkomsten=self.uitkomsten))
        elif self.parserfout:
            tekst = "geen json"
        else:
            materiaal = materiaal_uit_prompt(prompt)
            spec = {
                "lacks_differentia": True,
                "reason": "Synthetische reden.",
                "neighbours": [
                    {
                        "neighbour_id": plek.removeprefix("neighbour:"),
                        "distinction": "not_distinguished",
                        "missing_feature": "Synthetisch ontbrekend kenmerk.",
                        "reason": "Synthetisch buuroordeel.",
                    }
                    for plek in materiaal
                    if plek.startswith("neighbour:")
                ],
            }
            tekst = json.dumps(antwoord_uit_spec(spec, materiaal))
        if self.sdk:
            await _SDK().create()
        self.aanroepen.append({"model": model, **kwargs})
        self.antwoorden.append(tekst)
        return ChatResponse(text=tekst, tokens_used=10, model=model)


@pytest.fixture
def sdk_wacht():
    herstel = gb.installeer_sdk_wacht(_SDK)
    yield
    herstel()


def _proef(pad: Path) -> runner.Proef:
    """R7-mechaniek offline (gesloten voor echte calls) op deze invoer."""
    return dataclasses.replace(
        runner.PROEVEN["R7"], t_ontwikkelinvoer_sha256=_sha_bestand(pad)
    )


_VOORGANGERS: dict[Path, object] = {}


def _t(omg, tmp_path, pad, *, nieuw=True, **kw):
    if tmp_path not in _VOORGANGERS:  # eenmaal per test aangemaakt, dan hervat
        _VOORGANGERS[tmp_path] = _voorgangers(tmp_path)
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase="ontwikkeling",
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=runner.Proefopslag(tmp_path / "r7"),
            proef=_proef(pad),
            voorganger_opslag=_VOORGANGERS[tmp_path],
            nieuw_grootboek=nieuw,
            **kw,
        )
    )


def _regels(tmp_path) -> list[dict]:
    pad = tmp_path / "r7" / "callgrootboek.jsonl"
    return [json.loads(r) for r in pad.read_text(encoding="utf-8").splitlines()]


def _reserveringen(tmp_path) -> list[dict]:
    return [r for r in _regels(tmp_path) if r["soort"] == "reservering"]


def _afsluitingen(tmp_path) -> dict[int, dict]:
    return {r["seq"]: r for r in _regels(tmp_path) if r["soort"] == "afsluiting"}


def _records(tmp_path) -> list[dict]:
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted((tmp_path / "uit").rglob("calls/*.json"))
    ]


class TestTweeReserveringenPerGeval:
    def test_elke_aanroep_een_eigen_reservering_met_eigen_bewijs(
        self, sdk_wacht, tmp_path
    ):
        pad = _gevallenbestand(tmp_path, 1)
        provider = _TweestapsProvider(sdk=True)
        omg = dataclasses.replace(_omgeving(provider), sdk_bewaakt=True)
        uitkomst = _t(omg, tmp_path, pad)

        assert provider.stappen == ["beoordeling", "verificatie"]
        reserveringen = _reserveringen(tmp_path)
        assert [(r["seq"], r["stap"]) for r in reserveringen] == [
            (1, "beoordeling"),
            (2, "verificatie"),
        ]
        (poging,) = {r["poging"] for r in reserveringen}
        assert poging.startswith("ontwikkeling|") and poging.endswith("|1")
        assert [r["sleutel"] for r in reserveringen] == [
            f"{poging}/beoordeling",
            f"{poging}/verificatie",
        ]
        assert all(r["budget_bron"] == "fase" for r in reserveringen)
        afsluitingen = _afsluitingen(tmp_path)
        for seq in (1, 2):
            assert afsluitingen[seq]["status"] == "voltooid"
            assert afsluitingen[seq]["netwerk_gestart"] is True
            assert afsluitingen[seq]["details"]["client_aanroepen"] == 1
            assert afsluitingen[seq]["details"]["sdk_aanroepen"] == 1

        (record,) = _records(tmp_path)
        document = record["beoordelingsdocument"]
        assert document["status"] == "assessed"
        stappen = record["reserveringen"]
        assert [s["stap"] for s in stappen] == ["beoordeling", "verificatie"]
        assert [s["seq"] for s in stappen] == [1, 2]
        for stap, antwoord, documenthash, taak in zip(
            stappen,
            provider.antwoorden,
            (
                document["raw_response_sha256"],
                document["verification_raw_response_sha256"],
            ),
            ("validation", "ess05_verification"),
            strict=True,
        ):
            assert stap["ruw_antwoord_sha256"] == _sha(antwoord) == documenthash
            assert stap["attributie"]["task_type"] == taak
            assert stap["afsluitstatus"] == "voltooid"
            assert stap["kosten"]["input_tokens"] == 100
            assert stap["kosten"]["output_tokens"] == 20
            assert stap["transport"]["sdk"]["usage"] == {
                "input_tokens": 100,
                "output_tokens": 20,
            }
        assert stappen[0]["ruw_antwoord_sha256"] != stappen[1]["ruw_antwoord_sha256"]
        assert uitkomst["grootboek_na"]["totaal"] == 2

    def test_reservering_ontstaat_pas_bij_de_aanroep(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 1)
        gezien: dict[str, tuple[int, int]] = {}

        def bij_aanroep(stap: str) -> None:
            gezien[stap] = (
                len(_reserveringen(tmp_path)),
                len(_afsluitingen(tmp_path)),
            )

        _t(_omgeving(_TweestapsProvider(bij_aanroep=bij_aanroep)), tmp_path, pad)
        # Tijdens stap 1 bestaat alleen haar eigen reservering; stap 2 is
        # nergens vooraf als verbruikt geteld.
        assert gezien == {"beoordeling": (1, 0), "verificatie": (2, 0)}
        assert len(_afsluitingen(tmp_path)) == 2

    def test_parserfout_kost_alleen_de_eerste_reservering(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 1)
        provider = _TweestapsProvider(parserfout=True)
        _t(_omgeving(provider), tmp_path, pad)
        assert provider.stappen == ["beoordeling"]
        (reservering,) = _reserveringen(tmp_path)
        assert reservering["stap"] == "beoordeling"
        assert _afsluitingen(tmp_path)[1]["status"] == "modelfout"
        (record,) = _records(tmp_path)
        assert [s["stap"] for s in record["reserveringen"]] == ["beoordeling"]
        assert record["beoordelingsdocument"]["error"]["phase"] == "assessment"


class TestBudget:
    def _vul(self, tmp_path, pad, aantal: int) -> None:
        """Een bestaand R7-grootboek (tmp) met `aantal` afgesloten ontwikkelcalls."""
        boek = gb.Grootboek.nieuw(tmp_path / "r7" / "callgrootboek.jsonl", gb.R7)
        for i in range(aantal):
            res = boek.reserveer(
                "ontwikkeling",
                f"ontwikkeling|vul-{i}|1",
                invoer_sha256=_sha_bestand(pad),
            )
            boek.sluit(res["seq"], "voltooid", netwerk_gestart=True)

    def test_geen_budget_voor_stap_twee_weigert_voor_de_aanroep(
        self, tmp_path, monkeypatch
    ):
        """Harde grens in het grootboek zelf, ook als de planvooraftoets zou
        ontbreken: stap 2 wordt geweigerd vóór de aanroep, stap 1 afgesloten,
        de run stopt fail-closed."""
        pad = _gevallenbestand(tmp_path, 1)
        self._vul(tmp_path, pad, 8)
        monkeypatch.setattr(runner, "_controleer_plan", lambda *a, **k: None)
        provider = _TweestapsProvider()
        with pytest.raises(gb.BudgetSchendingError, match="bewaking greep in"):
            _t(_omgeving(provider), tmp_path, pad, nieuw=False)
        assert provider.stappen == ["beoordeling"]
        reserveringen = _reserveringen(tmp_path)
        assert len(reserveringen) == 9
        assert reserveringen[-1]["stap"] == "beoordeling"
        assert _afsluitingen(tmp_path)[9]["status"] == "voltooid"
        (record,) = _records(tmp_path)
        assert "fasecap" in record["transport"]["bewakingsweigering"]
        assert record["beoordelingsdocument"]["error"]["phase"] == "verification"
        assert record["uitkomst"]["status"] != "pass"

    def test_plan_rekent_vooraf_met_elke_stap_zonder_te_reserveren(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 1)
        self._vul(tmp_path, pad, 8)
        provider = _TweestapsProvider()
        with pytest.raises(gb.BudgetSchendingError, match="plan vraagt 2 calls"):
            _t(_omgeving(provider), tmp_path, pad, nieuw=False)
        assert provider.stappen == []
        assert len(_reserveringen(tmp_path)) == 8


class TestAfsluiting:
    def test_fout_in_stap_twee_sluit_beide_af(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 1)
        provider = _TweestapsProvider(fout_bij_verificatie=ConnectionError("weg"))
        _t(_omgeving(provider), tmp_path, pad)
        assert provider.stappen == ["beoordeling", "verificatie"]
        afsluitingen = _afsluitingen(tmp_path)
        assert [afsluitingen[s]["status"] for s in (1, 2)] == ["voltooid", "technisch"]

    def test_afbreken_in_stap_twee_sluit_beide_af(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 1)
        provider = _TweestapsProvider(fout_bij_verificatie=asyncio.CancelledError())
        with pytest.raises(asyncio.CancelledError):
            _t(_omgeving(provider), tmp_path, pad)
        afsluitingen = _afsluitingen(tmp_path)
        assert len(_reserveringen(tmp_path)) == 2
        assert [afsluitingen[s]["status"] for s in (1, 2)] == ["voltooid", "technisch"]

    def test_annulering_in_stap_twee_schrijft_het_bewijs_van_stap_een(
        self, sdk_wacht, tmp_path
    ):
        """BC-04: het callrecord wordt vóór het doorgeven van de annulering
        geschreven, met het beschikbare antwoord, de hash, het gebruik en de
        attributie van stap 1 en een afzonderlijke afsluiting per stap."""
        pad = _gevallenbestand(tmp_path, 1)
        provider = _TweestapsProvider(
            sdk=True, fout_bij_verificatie=asyncio.CancelledError()
        )
        omg = dataclasses.replace(_omgeving(provider), sdk_bewaakt=True)
        with pytest.raises(asyncio.CancelledError):
            _t(omg, tmp_path, pad)
        assert provider.stappen == ["beoordeling", "verificatie"]  # geen herhaling
        assert len(_reserveringen(tmp_path)) == 2
        (record,) = _records(tmp_path)
        assert record["beoordelingsdocument"] is None
        assert "geannuleerd" in record["fout"]
        assert record["uitkomst"]["status"] != "pass"
        een, twee = record["reserveringen"]
        assert (een["stap"], een["seq"], een["afsluitstatus"]) == (
            "beoordeling",
            1,
            "voltooid",
        )
        assert een["ruw_antwoord"] == provider.antwoorden[0]
        assert een["ruw_antwoord_sha256"] == _sha(provider.antwoorden[0])
        assert een["task_type"] == "validation"
        assert een["transport"]["client"]["model"]
        assert een["transport"]["sdk"]["usage"] == {
            "input_tokens": 100,
            "output_tokens": 20,
        }
        assert (een["kosten"]["input_tokens"], een["kosten"]["output_tokens"]) == (
            100,
            20,
        )
        assert (twee["stap"], twee["seq"], twee["afsluitstatus"]) == (
            "verificatie",
            2,
            # SDK-meting: de annulering viel vóór de SDK-aanroep, dus geen
            # netwerkstart in stap 2.
            "afgebroken",
        )
        assert twee["task_type"] == "ess05_verification"
        assert twee["ruw_antwoord"] is None
        afsluitingen = _afsluitingen(tmp_path)
        assert [afsluitingen[s]["status"] for s in (1, 2)] == ["voltooid", "afgebroken"]

    def test_annulering_in_stap_een_schrijft_het_callrecord(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 1)
        provider = _TweestapsProvider(fout_bij_beoordeling=asyncio.CancelledError())
        with pytest.raises(asyncio.CancelledError):
            _t(_omgeving(provider), tmp_path, pad)
        assert provider.stappen == ["beoordeling"]
        (reservering,) = _reserveringen(tmp_path)
        assert reservering["stap"] == "beoordeling"
        (record,) = _records(tmp_path)
        (een,) = record["reserveringen"]
        assert (een["stap"], een["afsluitstatus"], een["ruw_antwoord"]) == (
            "beoordeling",
            "technisch",
            None,
        )
        assert een["task_type"] == "validation"
        assert "geannuleerd" in record["fout"]


class TestGeenSemantischeRetry:
    def test_afgewezen_verificatie_wordt_niet_herhaald(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 1)
        provider = _TweestapsProvider(uitkomsten={"core_features": "unsupported"})
        _t(_omgeving(provider), tmp_path, pad)
        assert provider.stappen == ["beoordeling", "verificatie"]
        afsluitingen = _afsluitingen(tmp_path)
        assert [afsluitingen[s]["status"] for s in (1, 2)] == ["voltooid", "modelfout"]
        (record,) = _records(tmp_path)
        assert (
            record["beoordelingsdocument"]["error"]["type"]
            == "semantic_verification_failed"
        )
        # Hervatten slaat de gestarte poging over: geen tweede ronde.
        _t(_omgeving(provider), tmp_path, pad, nieuw=False)
        assert provider.stappen == ["beoordeling", "verificatie"]
        assert len(_reserveringen(tmp_path)) == 2

    def test_technische_herhaling_van_een_meerstapsgeval_geweigerd(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 1)
        provider = _TweestapsProvider(parserfout=True)
        _t(_omgeving(provider), tmp_path, pad)
        sleutel = _reserveringen(tmp_path)[0]["poging"]
        with pytest.raises(gb.BudgetSchendingError, match="meerstaps"):
            _t(
                _omgeving(provider),
                tmp_path,
                pad,
                nieuw=False,
                technische_herhalingen=[sleutel],
            )
        assert provider.stappen == ["beoordeling"]
        assert len(_reserveringen(tmp_path)) == 1


class TestGrootboekStapregels:
    """De stapregels zitten in het grootboek zelf (generiek, niet T-specifiek)."""

    @pytest.fixture
    def boek(self, tmp_path):
        return gb.Grootboek.nieuw(tmp_path / "gb.jsonl", gb.R7)

    def _stap(self, boek, stap, vorige=None, **kw):
        return boek.reserveer(
            "ontwikkeling",
            f"p/{stap}",
            invoer_sha256="a" * 64,
            poging="p",
            stap=stap,
            vorige_stap=vorige,
            **kw,
        )

    def test_volgorde_en_eenmaligheid(self, boek):
        with pytest.raises(gb.BudgetSchendingError, match="volgt niet op"):
            self._stap(boek, "verificatie", "beoordeling")
        self._stap(boek, "beoordeling")
        with pytest.raises(gb.BudgetSchendingError, match="al gereserveerd"):
            self._stap(boek, "beoordeling")
        self._stap(boek, "verificatie", "beoordeling")
        with pytest.raises(gb.BudgetSchendingError, match="al gereserveerd"):
            self._stap(boek, "verificatie", "beoordeling")
        assert boek.poging_gestart("p")
        assert not boek.poging_gestart("q")
        assert boek.samenvatting()["totaal"] == 2

    def test_technische_herhaling_van_een_stap_geweigerd(self, boek):
        self._stap(boek, "beoordeling")
        with pytest.raises(gb.BudgetSchendingError, match="meerstaps"):
            self._stap(boek, "beoordeling", technische_herhaling=True)

    def test_stapsleutel_moet_poging_en_stap_dragen(self, boek):
        with pytest.raises(gb.BudgetSchendingError, match="poging/stap"):
            boek.reserveer(
                "ontwikkeling",
                "iets-anders",
                invoer_sha256="a" * 64,
                poging="p",
                stap="beoordeling",
            )

    def test_enkelvoudige_reservering_blijft_zoals_zij_was(self, boek):
        res = boek.reserveer("ontwikkeling", "t|x|1", invoer_sha256="a" * 64)
        assert "poging" not in res and "stap" not in res
        assert boek.poging_gestart("t|x|1")

    def test_onbekende_stap_buiten_de_volgorde_geweigerd(self, boek):
        poging = gb.Stappenpoging(
            boek,
            fase="ontwikkeling",
            poging="p",
            stappen=(
                ("validation", "beoordeling"),
                ("ess05_verification", "verificatie"),
            ),
            invoer_sha256="a" * 64,
        )
        with (
            pytest.raises(gb.BudgetSchendingError, match="volgorde"),
            poging.stap("ess05_verification", "b" * 64),
        ):
            pass
        assert "volgorde" in poging.schending
        assert boek.samenvatting()["totaal"] == 0


class TestGeenOudeGoedkeuring:
    def test_oude_rondes_keuren_een_stap_per_geval_goed(self):
        oud = ("R1", "R2", "R3", "R4", "R5", "R6", "R7")
        assert {runner.PROEVEN[n].identiteit.modelstappen_per_geval for n in oud} == {1}
        # R8 (livevervolg), R9 (gerichte herproef), R10 (na het R9-
        # bewijsherstel) en R11 (na het R10-C3-herstel, 26-09) zijn eigen
        # tweestapsidentiteiten met een eigen budgetbesluit; R8–R10 zijn na hun
        # stop gesloten (R10 na C3), alleen R11 is open — geen oude goedkeuring.
        for naam in ("R8", "R9", "R10", "R11"):
            assert runner.PROEVEN[naam].identiteit.modelstappen_per_geval == 2
        assert set(runner.PROEVEN) == {*oud, "R8", "R9", "R10", "R11", "R12", "R13"}
        assert [n for n, p in runner.PROEVEN.items() if p.echt_toegestaan] == [
            "R11",
            "R12",
            "R13",
        ]

    def test_geregistreerde_open_r7_weigert_een_echte_tweestapsrun(
        self, tmp_path, monkeypatch
    ):
        pad = _gevallenbestand(tmp_path, 1)
        open_r7 = dataclasses.replace(
            _proef(pad),
            echt_toegestaan=True,
            opslag=runner.Proefopslag(tmp_path / "r7"),
        )
        monkeypatch.setitem(runner.PROEVEN, "R7", open_r7)
        provider = _TweestapsProvider()
        omg = dataclasses.replace(_omgeving(provider), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="modelstappen"):
            asyncio.run(
                runner.voer_t_fase(
                    omg,
                    fase="ontwikkeling",
                    gevallenpad=pad,
                    uitmap=tmp_path / "uit",
                    opslag=open_r7.opslag,
                    proef=open_r7,
                    nieuw_grootboek=True,
                )
            )
        assert provider.stappen == []
        assert not (tmp_path / "r7").exists()

    def test_programmatische_niet_geregistreerde_proef_geweigerd(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 1)
        open_r7 = dataclasses.replace(
            _proef(pad),
            echt_toegestaan=True,
            opslag=runner.Proefopslag(tmp_path / "r7"),
        )
        provider = _TweestapsProvider()
        omg = dataclasses.replace(_omgeving(provider), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="geregistreerde"):
            asyncio.run(
                runner.voer_t_fase(
                    omg,
                    fase="ontwikkeling",
                    gevallenpad=pad,
                    uitmap=tmp_path / "uit",
                    opslag=open_r7.opslag,
                    proef=open_r7,
                    nieuw_grootboek=True,
                )
            )
        assert provider.stappen == []
        assert not (tmp_path / "r7").exists()

    def test_positieve_controle_stappengoedkeuring_is_de_weigerende_regel(
        self, tmp_path, monkeypatch
    ):
        """Keurt de (geregistreerde) identiteit twee stappen goed, dan passeert
        deze controle; het grootboek kent zo'n identiteit niet en weigert
        daarna alsnog vóór netwerk (er bestaat geen R8)."""
        pad = _gevallenbestand(tmp_path, 1)
        identiteit = dataclasses.replace(gb.R7, modelstappen_per_geval=2)
        open_r7 = dataclasses.replace(
            _proef(pad),
            identiteit=identiteit,
            echt_toegestaan=True,
            opslag=runner.Proefopslag(tmp_path / "r7"),
        )
        monkeypatch.setitem(runner.PROEVEN, "R7", open_r7)
        omg = dataclasses.replace(_omgeving(_TweestapsProvider()), echt=True)
        runner._controleer_goedkeuring(omg, open_r7)  # geen weigering
        with pytest.raises(gb.BudgetSchendingError, match="onbekende proefidentiteit"):
            gb.Grootboek.nieuw(tmp_path / "x.jsonl", identiteit)


def test_stappen_volgen_uit_de_dienst():
    omg = _omgeving(_FakeProvider())
    assert runner.t_stappen(omg.dienst) == (
        ("validation", "beoordeling"),
        ("ess05_verification", "verificatie"),
    )
    assert runner.clientaanroepen_per_t_geval(omg.dienst) == 2


def test_aanroepgrens_is_zonder_proef_leeg():
    """De gewone appdienst kent geen proefbudget: zonder grens gebeurt er niets."""
    from services.validation import ess05_verification_service as vs

    assert vs._AANROEPGRENS.get() is None
    with aanroepgrens(None):
        assert vs._AANROEPGRENS.get() is None
