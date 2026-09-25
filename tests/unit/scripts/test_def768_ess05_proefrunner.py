"""DEF-768 WP7 — de ESS-05-proefrunner end-to-end, offline.

De providergrens is een fake `AsyncAIClient`; alles daarboven is productie
(`AIServiceV2`, `Ess05AssessmentService`, `PromptServiceV2`, contract). Dit
bewijst runnermechaniek — budget, grootboek, hervatten, reserve, afscherming,
varianten, CLI-beveiliging — en uitdrukkelijk géén modelkwaliteit.
"""

from __future__ import annotations

import asyncio
import copy
import json
import socket
import sys
from pathlib import Path

import pytest

from services.ai.base_client import AIConnectionClientError, ChatResponse
from services.ai.model_router import ModelRouter

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefgrootboek as gb
import proefinvoer as pi
import run_ess05_proef as runner

FIXTURES = ROOT / "tests" / "fixtures" / "ess05"
ONTWIKKEL = FIXTURES / "ontwikkelgevallen_v1.json"
NULCALL = FIXTURES / "nulcallroutes_v1.json"
G_INVOER = FIXTURES / "g_invoer_v2.json"


def _json(pad: Path) -> dict:
    return json.loads(pad.read_text(encoding="utf-8"))


class _FakeProvider:
    """Providergrens: telt aanroepen, geeft een vast antwoord of een fout."""

    provider_name = "fake"

    def __init__(self, tekst: str = "geen json", fout: Exception | None = None):
        self.tekst = tekst
        self.fout = fout
        self.aanroepen: list[dict] = []

    async def chat_completion(self, messages, model, **kwargs):
        self.aanroepen.append({"model": model, **kwargs, "messages": messages})
        if self.fout is not None:
            raise self.fout
        return ChatResponse(text=self.tekst, tokens_used=10, model=model)


def _omgeving(
    provider: _FakeProvider,
    *,
    router=None,
    timeout: int = 30,
    max_tokens_t: int = 1500,
    geheimen: tuple[str, ...] = ("GEHEIME-SLEUTEL-WAARDE",),
) -> runner.Omgeving:
    return runner.bouw_omgeving(
        provider,
        router or ModelRouter.from_config(),
        timeout=timeout,
        max_tokens_t=max_tokens_t,
        sdk_bewaakt=False,
        geheimen=geheimen,
    )


class _AnderValidatiemodel:
    """Echte router, alleen de T-route (`validation`) krijgt een ander model."""

    def __init__(self, model: str = "ander-validatiemodel"):
        self._router = ModelRouter.from_config()
        self._model = model

    def __getattr__(self, naam):
        return getattr(self._router, naam)

    def get_model(self, task_type, *args, **kwargs):
        provider, model = self._router.get_model(task_type, *args, **kwargs)
        return (
            (provider, self._model) if task_type == "validation" else (provider, model)
        )


def _gevallenbestand(tmp_path: Path, n: int, naam: str = "gevallen.json") -> Path:
    basis = _json(ONTWIKKEL)["gevallen"][-2]  # ESS05-E05
    gevallen = []
    for i in range(n):
        geval = copy.deepcopy(basis)
        geval["id"] = f"X-{i:02d}"
        geval["grond"] = (
            f"Vooraf vastgelegde grond nummer {i:02d} die afgeschermd blijft."
        )
        gevallen.append(geval)
    bestand: dict = {"gevallen": gevallen}
    if n >= 4:
        bestand["herhaal_ids"] = [g["id"] for g in gevallen[:4]]
    pad = tmp_path / naam
    pad.write_text(json.dumps(bestand), encoding="utf-8")
    return pad


def _g_invoer_actueel(tmp_path: Path) -> Path:
    """De G-invoer met de hash van de huidige instructie (tmp-kopie).

    De bevroren R1-invoer draagt de R1-hash en weigert sinds ronde 2 terecht
    (zie `test_g_invoer_vier_bevroren_invoeren_weigeren_de_ronde2_instructie`);
    de mechaniektests draaien daarom op deze kopie, het fixture blijft staan.
    """
    data = _json(G_INVOER)
    data["g_teksten"]["actueel"]["sha256"] = runner._sha_tekst(
        pi.huidige_g_instructie()
    )
    pad = tmp_path / "g_invoer_actueel.json"
    pad.write_text(json.dumps(data), encoding="utf-8")
    return pad


def _opslag(tmp_path: Path) -> runner.Proefopslag:
    """Geïsoleerde proefopslag (tests); echte calls gebruiken de canonieke."""
    return runner.Proefopslag(tmp_path / "uit")


def _stand(tmp_path: Path) -> dict:
    return gb.Grootboek.open(_opslag(tmp_path).grootboek).samenvatting()


def _t(omg, tmp_path, pad, fase="ontwikkeling", uitmap=None, **kwargs):
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase=fase,
            gevallenpad=pad,
            uitmap=uitmap or tmp_path / "uit",
            opslag=_opslag(tmp_path),
            **kwargs,
        )
    )


class TestBevrorenInvoer:
    def test_ontwikkelset_dertien_gevallen_met_referentieparen(self):
        gevallen, _ = pi.valideer_gevallenbestand(
            _json(ONTWIKKEL), herhaal_vereist=False
        )
        ids = [g["id"] for g in gevallen]
        assert ids == [
            "A-01", "A-02", "A-05", "A-07", "A-08", "A-12", "B-06",
            "B-07", "B-08", "A-16", "A-23", "ESS05-E05", "ESS05-E06",
        ]  # fmt: skip
        assert "B-09" not in ids
        assert _json(ONTWIKKEL)["status"] == "bevroren"

    def test_elk_ontwikkelgeval_is_een_echte_call_en_afgeschermd(self):
        from services.validation.ess05_assessment_service import laad_ess05_norm

        norm = laad_ess05_norm()
        for geval in _json(ONTWIKKEL)["gevallen"]:
            projectie = pi.modelprojectie(geval)
            assert pi.route(projectie, geval.get("lege_ruimte"))["soort"] == "aanroep"
            prompt = pi.bouw_t_prompt(projectie, norm)
            pi.controleer_afscherming(geval, prompt.teksten, norm)

    def test_g_invoer_vier_bevroren_invoeren_weigeren_de_ronde2_instructie(self):
        """Ronde 2 wijzigde de ESS-05-G-instructie: de R1-invoer past niet meer."""
        data = _json(G_INVOER)
        assert [i["id"] for i in data["invoeren"]] == [
            "G1-rol-overlap",
            "G2-naam-met-trefwoord",
            "G3-ontbrekend-kenmerk",
            "G4-meerdere-buren",
        ]
        assert data["status"] == "bevroren"
        assert data["schema"] == "def768-ess05-g-invoer/2"
        assert data["g_teksten"]["actueel"]["sha256"].startswith("1e2d7223")
        with pytest.raises(pi.InvoerfoutError, match="actuele G-tekst"):
            runner.controleer_g_teksten(data)

    def test_g_prompts_dragen_buren_identiek_in_beide_varianten(self, tmp_path):
        prompts = asyncio.run(runner.g_prompts(_json(_g_invoer_actueel(tmp_path))))
        verwacht = {
            "G1-rol-overlap": ["repository:9001"],
            "G2-naam-met-trefwoord": 1,
            "G3-ontbrekend-kenmerk": ["repository:9003"],
            "G4-meerdere-buren": 2,
        }
        for p in prompts:
            iid = p["invoer"]["id"]
            kwitantie = p["buren"]
            assert kwitantie["status"] == "ok"
            if isinstance(verwacht[iid], list):
                assert kwitantie["ids"] == verwacht[iid]
            else:
                assert kwitantie["aantal"] == verwacht[iid]
            actueel, basis = p["varianten"]["actueel"], p["varianten"]["basis"]
            for tekst in (actueel, basis):
                assert tekst.count("<verwante_begrippen>") == 1
            blok = actueel[actueel.index("Aangeleverde verwante begrippen in deze") :]
            assert basis.endswith(blok)
            assert len(p["verschil"]["verwijderd"]) == 1
            assert "aandachtspunten" not in actueel
            assert p["invoer"]["aandachtspunten"] not in actueel

    def test_g_teksten_weigeren_een_gewijzigde_actuele_instructie(self):
        data = _json(G_INVOER)
        data["g_teksten"]["actueel"]["sha256"] = "0" * 64
        with pytest.raises(pi.InvoerfoutError, match="actuele"):
            runner.controleer_g_teksten(data)


class TestVergelijking:
    def test_uitgebreide_verwachting_per_buur_blijft_bewaard(self):
        from services.validation.ess05_assessment_service import laad_ess05_norm
        from tests.unit.scripts.test_def768_ess05_proefinvoer import (
            CITAAT,
            _schemageval,
        )

        geval = _schemageval()
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), laad_ess05_norm())
        ids = {b.term: b.id for b in prompt.buren}
        document = {
            "judgment": {
                "lacks_differentia": False,
                "neighbours": [
                    {
                        "neighbour_id": ids["werknemer"],
                        "distinction": "distinguished",
                        "distinguishing_feature_quote": CITAAT,
                        "missing_feature": None,
                    },
                    {
                        "neighbour_id": ids["bezoeker"],
                        "distinction": "not_distinguished",
                        "distinguishing_feature_quote": None,
                        "missing_feature": "iets",
                    },
                ],
            }
        }
        # ADR-003: alleen een door de replay toegepast oordeel telt mee.
        toegepast = {"status": "pass", "review": {"assessment": {"applied": True}}}
        vergelijking = runner._vergelijk(geval, prompt, document, toegepast)
        werknemer, bezoeker = vergelijking["per_buur"]
        assert werknemer["term"] == "werknemer"
        assert (werknemer["verwacht"], werknemer["gekregen"]) == (
            "distinguished",
            "distinguished",
        )
        assert werknemer["correct"] is True
        assert werknemer["verwachting"] == geval["verwacht_per_buur"][0]
        assert werknemer["gekregen_citaat"] == CITAAT
        assert (bezoeker["correct"], bezoeker["gekregen_kenmerk"]) == (False, "iets")
        assert bezoeker["verwachting"]["grond"] == (
            "Zonder definitie van bezoeker blijft dit open."
        )


class TestNulcallroutes:
    def test_routes_zonder_grootboek_en_zonder_netwerk(self, tmp_path):
        samenvatting = runner.nulcallproef(NULCALL, tmp_path / "uit")
        assert samenvatting["alle_routes_zoals_verwacht"] is True
        assert samenvatting["echte_calls"] == 0
        assert not (tmp_path / "uit" / "callgrootboek.jsonl").exists()
        routes = {r["id"]: r for r in samenvatting["resultaten"]}
        assert routes["B-09"]["uitkomst_status"] == "not_evaluated"
        assert routes["N-03"]["uitkomst_status"] == "pass"
        assert routes["N-05"]["route"] == "aanroep"


class TestTFase:
    def test_een_reservering_per_geval_en_hervatten_zonder_extra_calls(self, tmp_path):
        provider = _FakeProvider()
        pad = _gevallenbestand(tmp_path, 3)
        eerste = _t(_omgeving(provider), tmp_path, pad, nieuw_grootboek=True)
        assert len(provider.aanroepen) == 3
        assert all(a["max_retries"] == 0 for a in provider.aanroepen)
        stand = _stand(tmp_path)
        assert stand["per_fase"]["ontwikkeling"] == 3
        assert stand["per_status"] == {"modelfout": 3}
        assert eerste["aanroepen_gestart"] == 3

        tweede = _t(_omgeving(provider), tmp_path, pad)
        assert len(provider.aanroepen) == 3  # hervatten: niets opnieuw
        assert tweede["overgeslagen_al_gereserveerd"] == 3

    def test_callrecord_bevat_prompt_antwoord_en_hashes_maar_labels_niet_in_prompt(
        self, tmp_path
    ):
        provider = _FakeProvider(tekst="geen json maar tekst")
        _t(
            _omgeving(provider),
            tmp_path,
            _gevallenbestand(tmp_path, 1),
            nieuw_grootboek=True,
        )
        (record_pad,) = (tmp_path / "uit").glob("ontwikkeling-*/calls/*.json")
        record = _json(record_pad)
        assert record["ruw_antwoord"] == "geen json maar tekst"
        dienst_sha = record["beoordelingsdocument"]["input"]["prompt_sha256"]
        assert record["prompt"]["sha256"] == dienst_sha
        assert "Vooraf vastgelegde grond" not in json.dumps(record["prompt"])
        verzonden = json.dumps(provider.aanroepen[0]["messages"], default=str)
        assert "Vooraf vastgelegde grond" not in verzonden
        assert record["vergelijking"]["verwacht"] == "pass"
        assert record["afsluitstatus"] == "modelfout"
        # Zonder SDK-usage: onbekend, niet verzonnen.
        assert record["kosten"]["usd"] is None
        assert "GEHEIME-SLEUTEL-WAARDE" not in record_pad.read_text(encoding="utf-8")

    def test_budget_wordt_vooraf_gecontroleerd(self, tmp_path):
        provider = _FakeProvider()
        with pytest.raises(gb.BudgetSchendingError, match="fasecap"):
            _t(
                _omgeving(provider),
                tmp_path,
                _gevallenbestand(tmp_path, 14),
                nieuw_grootboek=True,
            )
        assert provider.aanroepen == []
        assert _stand(tmp_path)["totaal"] == 0

    def test_technische_fout_telt_en_reserve_alleen_expliciet(self, tmp_path):
        # ADR-003 WP5: elke modelstap heeft een eigen reservering; een
        # technische herhaling van een meerstaps-T-geval is niet vastgelegd en
        # wordt vóór grootboek en netwerk geweigerd (reserveregels zelf: zie
        # test_def768_ess05_proefgrootboek, G-route ongewijzigd).
        pad = _gevallenbestand(tmp_path, 1)
        kapot = _FakeProvider(fout=AIConnectionClientError("verbinding weg"))
        _t(_omgeving(kapot), tmp_path, pad, nieuw_grootboek=True)
        assert len(kapot.aanroepen) == 1  # geen automatische retry
        boek = gb.Grootboek.open(_opslag(tmp_path).grootboek)
        assert boek.samenvatting()["per_status"] == {"technisch": 1}

        heel = _FakeProvider()
        _t(_omgeving(heel), tmp_path, pad)
        assert heel.aanroepen == []  # hervatten herhaalt niet vanzelf
        with pytest.raises(gb.BudgetSchendingError, match="meerstaps"):
            _t(
                _omgeving(heel),
                tmp_path,
                pad,
                technische_herhalingen=("ontwikkeling|X-00|1",),
            )
        assert heel.aanroepen == []
        stand = _stand(tmp_path)
        assert (stand["totaal"], stand["reserve"]) == (1, 0)

    def test_herhalingsfase_twee_keer_de_vier_herhaal_ids(self, tmp_path):
        provider = _FakeProvider()
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide: van de 8 herhalingen passen er
        # 4 in de fasecap van 8 (de eigenschap hieronder blijft gelijk).
        pad = _gevallenbestand(tmp_path, 6)
        _t(_omgeving(provider), tmp_path, pad, fase="t_herhaling",
           nieuw_grootboek=True, max_calls=4)  # fmt: skip
        assert len(provider.aanroepen) == 4
        boek = gb.Grootboek.open(_opslag(tmp_path).grootboek)
        assert boek.poging_gestart("t_herhaling|X-00|herhaling-1")
        assert boek.poging_gestart("t_herhaling|X-01|herhaling-2")
        assert not boek.poging_gestart("t_herhaling|X-02|herhaling-1")
        assert not boek.poging_gestart("t_herhaling|X-04|herhaling-1")

    def test_slot_hoort_bij_de_proefopslag_niet_bij_de_uitmap(self, tmp_path):
        """Twee runners met verschillende uitmappen op één proef: geweigerd."""
        provider = _FakeProvider()
        with (
            gb.Proefslot(_opslag(tmp_path).slot),
            pytest.raises(gb.BudgetSchendingError, match="andere runner"),
        ):
            _t(
                _omgeving(provider),
                tmp_path,
                _gevallenbestand(tmp_path, 1),
                uitmap=tmp_path / "andere-uitmap",
                nieuw_grootboek=True,
            )
        assert provider.aanroepen == []

    def test_tarief_van_het_routemodel_zonder_terugvalprijs(self):
        omg = _omgeving(_FakeProvider())
        for route in ("t", "g"):
            prijs, bekend = omg.prijs(route)
            model = omg.modelconfig[route]["model"]
            assert bekend is (model in omg.router.get_active_pricing())
            if bekend:
                assert prijs == omg.router.get_active_pricing()[model]

    def test_totaaldeadline_start_geen_call_die_niet_past(self, tmp_path):
        provider = _FakeProvider()
        uitkomst = _t(
            _omgeving(provider),
            tmp_path,
            _gevallenbestand(tmp_path, 2),
            nieuw_grootboek=True,
            totaal_deadline=1.0,
        )
        assert provider.aanroepen == []
        assert uitkomst["niet_gestart_deadline"] == 2


class TestProefidentiteit:
    """Punt 3: één duurzame proefidentiteit, onafhankelijk van --uitmap."""

    def test_andere_uitmap_deelt_budget_en_hervat(self, tmp_path):
        provider = _FakeProvider()
        pad = _gevallenbestand(tmp_path, 2)
        _t(_omgeving(provider), tmp_path, pad, nieuw_grootboek=True)
        tweede = _t(_omgeving(provider), tmp_path, pad, uitmap=tmp_path / "elders")
        assert len(provider.aanroepen) == 2
        assert tweede["overgeslagen_al_gereserveerd"] == 2
        assert tweede["grootboek"] == str(_opslag(tmp_path).grootboek)
        with pytest.raises(gb.BudgetSchendingError, match="bestaat al"):
            _t(
                _omgeving(provider),
                tmp_path,
                pad,
                uitmap=tmp_path / "nog-elders",
                nieuw_grootboek=True,
            )
        assert len(provider.aanroepen) == 2

    def test_echte_omgeving_weigert_andere_opslag(self, tmp_path):
        """R1 t/m R7 zijn gesloten (ADR-003); de opslagregel geldt voor een
        (hypothetisch) open R7."""
        import dataclasses

        provider = _FakeProvider()
        omg = dataclasses.replace(_omgeving(provider), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="gesloten"):
            _t(omg, tmp_path, _gevallenbestand(tmp_path, 1), nieuw_grootboek=True)
        with pytest.raises(gb.BudgetSchendingError, match="canonieke"):
            _t(
                omg,
                tmp_path,
                _gevallenbestand(tmp_path, 1),
                nieuw_grootboek=True,
                proef=dataclasses.replace(runner.PROEVEN["R7"], echt_toegestaan=True),
            )
        assert provider.aanroepen == []
        assert not _opslag(tmp_path).grootboek.exists()

    def test_canonieke_opslag_is_de_afgesproken_rapportroot(self):
        assert runner.CANONIEKE_OPSLAG.root == (
            ROOT / "reports" / "DEF-768-AI-20260924"
        )
        assert runner.CANONIEKE_OPSLAG.grootboek.name == "callgrootboek.jsonl"

    def test_cli_weigert_ander_grootboekpad_voor_de_omgeving(
        self, tmp_path, monkeypatch
    ):
        def geen_omgeving(**_kwargs):
            raise AssertionError("live_omgeving mag niet worden gebouwd")

        monkeypatch.setattr(runner, "live_omgeving", geen_omgeving)
        for proef in ("R1", "R2"):  # R1: gesloten; R2: ander pad geweigerd
            with pytest.raises(SystemExit) as exc:
                runner.main(
                    ["--proef", proef, "--fase", "ontwikkeling", "--gevallen",
                     str(ONTWIKKEL), "--echt",
                     "--grootboek", str(tmp_path / "eigen.jsonl")]
                )  # fmt: skip
            assert exc.value.code != 0
        assert not (tmp_path / "eigen.jsonl").exists()

    def test_cli_echt_gebruikt_canonieke_opslag_bij_elke_uitmap(
        self, tmp_path, monkeypatch
    ):
        import dataclasses

        # ADR-003: R7 is gesloten voor echte calls; dit mechaniekbewijs (routing
        # naar de eigen opslag) draait op een hypothetisch open R7.
        monkeypatch.setitem(runner.PROEVEN, "R7", dataclasses.replace(
            runner.PROEVEN["R7"], echt_toegestaan=True))  # fmt: skip
        gezien: dict = {}

        async def vang(omg, **kwargs):
            gezien.update(kwargs)
            return {
                "aanroepen_gestart": 0,
                "grootboek_na": {"totaal": 0},
                "kosten_usd_bekend": 0,
                "kosten_onbekend": 0,
            }

        monkeypatch.setattr(runner, "live_omgeving", lambda **_k: object())
        monkeypatch.setattr(runner, "voer_t_fase", vang)
        code = runner.main(
            ["--proef", "R7", "--fase", "ontwikkeling", "--gevallen",
             str(ONTWIKKEL), "--echt",
             "--uitmap", str(tmp_path / "willekeurig"), "--max-calls", "1"]
        )  # fmt: skip
        assert code == 0
        assert gezien["opslag"] == runner.PROEVEN["R7"].opslag
        assert gezien["uitmap"] == tmp_path / "willekeurig"
        assert gezien["max_calls"] == 1


class TestEindbindingRunner:
    """Punt 4: t_eind en t_herhaling op exact dezelfde dataset en code."""

    def test_eindfase_vereist_voorafgekozen_herhaal_ids(self, tmp_path):
        provider = _FakeProvider()
        with pytest.raises(pi.InvoerfoutError, match="herhaal_ids"):
            _t(
                _omgeving(provider),
                tmp_path,
                _gevallenbestand(tmp_path, 3),
                fase="t_eind",
                nieuw_grootboek=True,
            )
        assert provider.aanroepen == []

    def test_herhaling_met_ander_bestand_geweigerd_voor_elke_call(self, tmp_path):
        provider = _FakeProvider()
        eind = _gevallenbestand(tmp_path, 5, naam="eind.json")
        _t(_omgeving(provider), tmp_path, eind, fase="t_eind", nieuw_grootboek=True)
        assert len(provider.aanroepen) == 5
        ander = json.loads(eind.read_text(encoding="utf-8"))
        ander["gevallen"][0]["grond"] = "Stil gewijzigde grond na de eindfase."
        anderpad = tmp_path / "ander.json"
        anderpad.write_text(json.dumps(ander), encoding="utf-8")
        with pytest.raises(gb.BudgetSchendingError, match="eindbinding"):
            _t(_omgeving(provider), tmp_path, anderpad, fase="t_herhaling")
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide: van de 8 herhalingen passen er
        # 4 in de fasecap van 8 (de eigenschap hieronder blijft gelijk).
        assert len(provider.aanroepen) == 5
        _t(_omgeving(provider), tmp_path, eind, fase="t_herhaling", max_calls=4)
        assert len(provider.aanroepen) == 9
        boek = gb.Grootboek.open(_opslag(tmp_path).grootboek)
        bindingen = {
            json.dumps(r["binding"], sort_keys=True) for r in boek._reserveringen()
        }
        assert len(bindingen) == 1

    def test_codewijziging_na_eindfase_geweigerd(self, tmp_path, monkeypatch):
        provider = _FakeProvider()
        eind = _gevallenbestand(tmp_path, 5)
        _t(_omgeving(provider), tmp_path, eind, fase="t_eind", nieuw_grootboek=True)
        monkeypatch.setattr(runner, "code_sha256", lambda: "d" * 64)
        with pytest.raises(gb.BudgetSchendingError, match="eindbinding"):
            _t(_omgeving(provider), tmp_path, eind, fase="t_herhaling")
        assert len(provider.aanroepen) == 5


class TestEffectieveConfiguratie:
    """Reviewpunt 4 (rest): de werkelijk toegepaste model-/promptinstellingen."""

    def test_gelijke_instellingen_geven_gelijke_configuratie(self):
        een = runner.effectieve_config(_omgeving(_FakeProvider()))
        twee = runner.effectieve_config(_omgeving(_FakeProvider()))
        assert een == twee
        assert pi.sha_json(een) == pi.sha_json(twee)

    def test_configuratie_komt_uit_dienst_en_router_zonder_geheim(self):
        omg = _omgeving(_FakeProvider())
        cfg = runner.effectieve_config(omg)
        dienst = omg.dienst
        assert cfg["t"]["max_tokens"] == dienst._max_tokens == 1500
        assert cfg["t"]["timeout_s"] == dienst._timeout_seconds == 30
        assert cfg["t"]["max_passage_chars"] == dienst._max_passage_chars
        for veld, waarde in dienst.binding().als_dict().items():
            assert cfg["t"][veld] == waarde
        assert (cfg["t"]["provider"], cfg["t"]["model"]) == tuple(
            omg.router.get_model("validation")
        )
        assert (cfg["g"]["provider"], cfg["g"]["model"]) == tuple(
            omg.router.get_model("definition_core")
        )
        assert cfg["g"]["max_tokens"] == runner.G_MAX_TOKENS
        assert cfg["g"]["temperature_requested"] == omg.g_temperatuur
        assert cfg["g"]["max_prompt_length"] == pi.g_promptgrens() == 60000
        assert "GEHEIME-SLEUTEL-WAARDE" not in json.dumps(cfg)

    def test_configuratie_met_geheim_wordt_geweigerd(self):
        omg = _omgeving(_FakeProvider())
        model = omg.router.get_model("validation")[1]
        lek = _omgeving(_FakeProvider(), geheimen=(model,))
        with pytest.raises(gb.BudgetSchendingError, match="geheim"):
            runner.effectieve_config(lek)

    @pytest.mark.parametrize(
        "anders",
        [
            {"max_tokens_t": 3000},  # reviewrepro 1500 → 3000
            {"timeout": 60},
            {"router": "ander_model"},
        ],
    )
    def test_andere_instellingen_na_eindfase_geweigerd_voor_netwerk(
        self, tmp_path, anders
    ):
        provider = _FakeProvider()
        eind = _gevallenbestand(tmp_path, 5)
        _t(_omgeving(provider), tmp_path, eind, fase="t_eind", nieuw_grootboek=True)
        assert len(provider.aanroepen) == 5
        if anders.get("router") == "ander_model":
            anders = {"router": _AnderValidatiemodel()}
        gewijzigd = _omgeving(provider, **anders)
        assert runner.effectieve_config(gewijzigd) != runner.effectieve_config(
            _omgeving(provider)
        )
        with pytest.raises(gb.BudgetSchendingError, match="eindbinding"):
            _t(gewijzigd, tmp_path, eind, fase="t_herhaling")
        # ADR-003 WP5: twee modelstappen per geval, elk een eigen reservering;
        # de planvooraftoets rekent met beide: van de 8 herhalingen passen er
        # 4 in de fasecap van 8 (de eigenschap hieronder blijft gelijk).
        assert len(provider.aanroepen) == 5
        _t(_omgeving(provider), tmp_path, eind, fase="t_herhaling", max_calls=4)
        assert len(provider.aanroepen) == 9

    def test_technische_herhaling_met_andere_instellingen_geweigerd(self, tmp_path):
        pad = _gevallenbestand(tmp_path, 1)
        kapot = _FakeProvider(fout=AIConnectionClientError("verbinding weg"))
        _t(_omgeving(kapot), tmp_path, pad, nieuw_grootboek=True)
        heel = _FakeProvider()
        # ADR-003 WP5: een technische herhaling van een meerstaps-T-geval is
        # niet vastgelegd; met gewijzigde én met gelijke instellingen geweigerd
        # vóór het netwerk. De configuratieregel van de reserve zelf staat in
        # test_def768_ess05_proefgrootboek (reserve_weigert_andere_...).
        for omg in (_omgeving(heel, max_tokens_t=3000), _omgeving(heel)):
            with pytest.raises(gb.BudgetSchendingError, match="meerstaps"):
                _t(
                    omg,
                    tmp_path,
                    pad,
                    technische_herhalingen=("ontwikkeling|X-00|1",),
                )
        assert heel.aanroepen == []

    def test_samenvatting_en_callrecord_leggen_de_configuratie_vast(self, tmp_path):
        omg = _omgeving(_FakeProvider())
        eind = _gevallenbestand(tmp_path, 5)
        uitkomst = _t(omg, tmp_path, eind, fase="t_eind", nieuw_grootboek=True)
        cfg_sha = pi.sha_json(runner.effectieve_config(omg))
        assert uitkomst["eindbinding"]["config_sha256"] == cfg_sha
        assert uitkomst["effectieve_config"] == runner.effectieve_config(omg)
        boek = gb.Grootboek.open(_opslag(tmp_path).grootboek)
        assert {r["details"]["config_sha256"] for r in boek._reserveringen()} == {
            cfg_sha
        }


class TestCodemanifest:
    def test_manifest_bevat_de_nieuwe_g_afhankelijkheid(self):
        manifest = runner.codemanifest()
        assert "src/services/prompts/ess05_generatieburen.py" in manifest
        assert runner.identiteit()["code_sha256"] == pi.sha_json(manifest)

    def test_directe_projectimports_staan_in_het_manifest(self):
        """Eigen runner-/transportcode binnen directe scope ontbreekt niet."""
        import ast

        bronnen = [
            "scripts/ess05/run_ess05_proef.py",
            "scripts/ess05/proefinvoer.py",
            "scripts/ess05/proefgrootboek.py",
            "src/services/validation/ess05_assessment_service.py",
            # ADR-003: de verificatiestap en het bewijscontract.
            "src/services/validation/ess05_verification_service.py",
            "src/domain/ess05/bewijs.py",
            "src/services/validation/ai_beoordeling_transport.py",
            "src/services/prompts/ess05_generatieburen.py",
        ]

        def resolve(naam):
            for basis in (ROOT / "src", ROOT / "scripts" / "ess05"):
                mod = basis.joinpath(*naam.split("."))
                for kandidaat in (mod.with_suffix(".py"), mod / "__init__.py"):
                    if kandidaat.is_file():
                        return str(kandidaat.relative_to(ROOT))
            return None

        gevonden = set()
        for bron in bronnen:
            for knoop in ast.walk(ast.parse((ROOT / bron).read_text("utf-8"))):
                namen = []
                if isinstance(knoop, ast.ImportFrom) and knoop.module:
                    namen = [knoop.module] + [
                        f"{knoop.module}.{a.name}" for a in knoop.names
                    ]
                elif isinstance(knoop, ast.Import):
                    namen = [a.name for a in knoop.names]
                gevonden.update(p for n in namen if (p := resolve(n)))
        gedekt = set(runner.codemanifest()) | set(runner.BUITEN_CODEMANIFEST)
        assert sorted(gevonden - gedekt) == []


class TestGPromptgrens:
    """Reviewpunt 5 (rest): de complete G-prompt (na bronnen én buren) en
    beide G-varianten onder dezelfde grens, via de echte orchestratorstap en
    `PromptServiceV2` (repositoryburen via de lokale standin)."""

    DOCUMENT = {
        "doc_id": "doc-synthetisch-rand",
        "title": "Synthetisch reglement",
        "url": None,
        "snippet": " ".join(
            ["Synthetische documentpassage over leningen bij de instelling."] * 3
        ),
    }

    @staticmethod
    def _invoer(laatste: int) -> dict:
        invoer = copy.deepcopy(_json(G_INVOER)["invoeren"][0])
        invoer["id"] = "G-rand"
        invoer["documenten"] = []
        invoer["repository_buren"] = [
            {
                "id": 9100 + i,
                "begrip": f"randbuur{i}",
                "definitie": "x" * (laatste if i == 3 else 6000),
            }
            for i in range(4)
        ]
        return invoer

    async def _gekalibreerd(self, marge: int) -> dict:
        grens = pi.g_promptgrens()
        tekst, _ = await pi.bouw_g_prompt_met_buren(self._invoer(6000))
        invoer = self._invoer(6000 + grens - marge - len(tekst))
        tekst, buren = await pi.bouw_g_prompt_met_buren(invoer)
        assert len(tekst) == grens - marge
        assert buren["aantal"] >= 4  # de vier repositoryburen staan in de prompt
        return invoer

    async def test_bron_brengt_complete_prompt_over_de_grens(self):
        assert pi.g_promptgrens() == 60000
        invoer = await self._gekalibreerd(marge=40)
        met_bron = {**invoer, "documenten": [dict(self.DOCUMENT)]}
        with pytest.raises(pi.InvoerfoutError, match="te lang"):
            await pi.bouw_g_prompt_met_buren(met_bron)

    async def test_kleine_invoer_met_bron_blijft_normaal(self):
        invoer = {**self._invoer(200), "documenten": [dict(self.DOCUMENT)]}
        invoer["repository_buren"] = invoer["repository_buren"][:1]
        invoer["repository_buren"][0]["definitie"] = "Persoon met een lening."
        tekst, _ = await pi.bouw_g_prompt_met_buren(invoer)
        assert len(tekst) <= pi.g_promptgrens()
        assert "Synthetische documentpassage over leningen" in tekst

    async def test_beide_g_varianten_onder_dezelfde_grens(self, monkeypatch, tmp_path):
        data = _json(_g_invoer_actueel(tmp_path))
        data["invoeren"] = data["invoeren"][:1]
        prompts = await runner.g_prompts(data)
        varianten = prompts[0]["varianten"]
        lengtes = {naam: len(tekst) for naam, tekst in varianten.items()}
        assert lengtes["basis"] != lengtes["actueel"]
        langste = max(lengtes, key=lengtes.get)
        monkeypatch.setattr(pi, "g_promptgrens", lambda: min(lengtes.values()))
        with pytest.raises(pi.InvoerfoutError, match=f"te lang.*{langste}"):
            await runner.g_prompts(data)


class TestGFase:
    def test_zestien_calls_twee_varianten_en_hervatten(self, tmp_path):
        provider = _FakeProvider(
            tekst="Ontologische categorie: type\nPersoon met een lening."
        )
        omg = _omgeving(provider)
        kwargs = {
            "g_invoerpad": _g_invoer_actueel(tmp_path),
            "uitmap": tmp_path / "uit",
            "opslag": _opslag(tmp_path),
        }
        uitkomst = asyncio.run(runner.voer_g_fase(omg, nieuw_grootboek=True, **kwargs))
        assert len(provider.aanroepen) == 16
        assert uitkomst["aanroepen_gestart"] == 16
        records = [_json(p) for p in (tmp_path / "uit").glob("g-*/calls/*.json")]
        assert len(records) == 16
        per_invoer: dict[str, set] = {}
        for r in records:
            per_invoer.setdefault(r["invoer_id"], set()).add(r["prompt"]["sha256"])
            assert r["kern"] == "Persoon met een lening."
            assert "aandachtspunten" not in json.dumps(r["prompt"])
        assert all(len(shas) == 2 for shas in per_invoer.values())
        for aanroep in provider.aanroepen:
            assert aanroep["max_retries"] == 0
        asyncio.run(runner.voer_g_fase(_omgeving(provider), **kwargs))
        assert len(provider.aanroepen) == 16


class TestDroogG:
    def test_droog_g_legt_burenkwitantie_en_lokale_vergelijking_vast(self, tmp_path):
        code = runner.main(
            ["--fase", "g", "--g-invoer", str(_g_invoer_actueel(tmp_path)),
             "--uitmap", str(tmp_path / "uit"), "--droog"]
        )  # fmt: skip
        assert code == 0
        (pad,) = (tmp_path / "uit").glob("droog-g-*/droogrun.json")
        data = _json(pad)
        assert data["echte_calls"] == 0
        assert data["geplande_calls"] == 16
        assert "lokale vergelijking" in data["vergelijkingsaard"]
        buren = {b["invoer"]: b["buren"] for b in data["buren"]}
        assert buren["G3-ontbrekend-kenmerk"]["ids"] == ["repository:9003"]
        assert not (tmp_path / "uit" / "callgrootboek.jsonl").exists()


class TestCLI:
    def test_zonder_droog_of_echt_weigert_de_runner(self, capsys):
        with pytest.raises(SystemExit) as exc:
            runner.main(["--fase", "ontwikkeling", "--gevallen", str(ONTWIKKEL)])
        assert exc.value.code != 0

    def test_droog_blokkeert_het_netwerk(self):
        with runner.geen_netwerk(), pytest.raises(OSError, match="droog"):
            socket.create_connection(("127.0.0.1", 9))

    def test_droog_ontwikkeling_schrijft_prompts_zonder_grootboek(self, tmp_path):
        code = runner.main(
            [
                "--fase",
                "ontwikkeling",
                "--gevallen",
                str(ONTWIKKEL),
                "--uitmap",
                str(tmp_path / "uit"),
                "--droog",
            ]
        )
        assert code == 0
        assert not (tmp_path / "uit" / "callgrootboek.jsonl").exists()
        (bestand,) = (tmp_path / "uit").glob("droog-ontwikkeling-*/droogrun.json")
        droog = _json(bestand)
        assert droog["geplande_calls"] == 13
        assert droog["echte_calls"] == 0
