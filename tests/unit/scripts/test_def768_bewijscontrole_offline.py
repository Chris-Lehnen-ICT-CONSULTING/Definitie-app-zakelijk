"""DEF-768 / ADR-003: offline proefinfrastructuur voor de tweestaps-ESS-05-keten.

De huidige T-software doet per geval twee clientaanroepen (conceptoordeel en
semantische verificatie), elk met een eigen reservering (correctie v2; zie
`test_def768_stapreservering`); er is geen nieuw proefbudget. Bewijst, zonder
netwerk en zonder betaalde calls:

* het codemanifest bindt de bewijs- en verificatiecode; de effectieve
  configuratie en de freeze binden de verifierroute, het model, de
  verificatieprompt en haar tokengrens;
* ronde 7 is gesloten voor echte calls (de oude R7-freeze hoort bij de
  eenstaps-`/13`-software) en geen enkele ronde staat open;
* een echte tweestaps-T-fase wordt vóór grootboek en netwerk geweigerd, ook
  als een (niet-geregistreerde) ronde in de test open zou staan;
* offline krijgt de tweede fase een eigen reservering (niet meer geweigerd
  binnen die van de eerste); het callrecord registreert beide fasen
  afzonderlijk en een onbruikbare verificatie geeft nooit een pass;
* de nulcallroute van de proefinvoer rekent met hetzelfde materiaal als de
  dienst (context en bedoelde betekenis inbegrepen);
* de vergelijking gebruikt alleen een door de replay toegepast oordeel.

Fakes bewijzen de keten, niet het detectievermogen van een echte verifier.
"""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

import pytest

from services.validation.ess05_assessment_service import (
    Ess05AssessmentService,
    laad_ess05_norm,
)
from services.validation.ess05_verification_service import Ess05VerificationService
from tests.fixtures.def768_fakes import (
    antwoord_uit_spec,
    bouw_ess05_beoordeling,
    materiaal_uit_prompt,
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
import proefinvoer as pi
import run_ess05_proef as runner


def _sha(pad: Path) -> str:
    return hashlib.sha256(Path(pad).read_bytes()).hexdigest()


def _open_r7(tmp_path: Path, pad: Path) -> runner.Proef:
    """R7 zoals een (hypothetisch) open ronde, met opslag in tmp."""
    return dataclasses.replace(
        runner.PROEVEN["R7"],
        echt_toegestaan=True,
        opslag=runner.Proefopslag(tmp_path / "r7"),
        t_ontwikkelinvoer_sha256=_sha(pad),
    )


def _t(omg, tmp_path, pad, proef, **kw):
    return asyncio.run(
        runner.voer_t_fase(
            omg,
            fase="ontwikkeling",
            gevallenpad=pad,
            uitmap=tmp_path / "uit",
            opslag=runner.Proefopslag(tmp_path / "r7"),
            proef=proef,
            voorganger_opslag=_voorgangers(tmp_path),
            nieuw_grootboek=True,
            **kw,
        )
    )


class _ConceptProvider(_FakeProvider):
    """Beantwoordt de beoordelingsvraag met een geldig `/2`-conceptoordeel."""

    async def chat_completion(self, messages, model, **kwargs):
        prompt = "\n".join(str(getattr(m, "content", "") or "") for m in messages)
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
        self.tekst = json.dumps(antwoord_uit_spec(spec, materiaal))
        return await super().chat_completion(messages, model, **kwargs)


class TestBinding:
    def test_manifest_bindt_bewijs_en_verificatiecode(self):
        for pad in (
            "src/domain/ess05/bewijs.py",
            "src/services/validation/ess05_verification_service.py",
        ):
            assert pad in runner._CODEBESTANDEN, pad
            assert pad in runner.codemanifest()

    def test_effectieve_config_bindt_de_verifierroute(self):
        omg = _omgeving(_FakeProvider(), max_tokens_t=1500)
        cfg = runner.effectieve_config(omg)
        verifier = cfg["t_verificatie"]
        assert verifier["task_type"] == Ess05VerificationService.TASK_TYPE
        assert verifier["prompt_version"] == Ess05VerificationService.PROMPT_VERSION
        provider, model = omg.router.get_model("ess05_verification")
        assert (verifier["provider"], verifier["model"]) == (provider, model)
        assert verifier["max_tokens"] == omg.dienst.verification_service.max_tokens
        assert verifier["timeout_s"] == omg.timeout
        assert "temperature_sent" in verifier
        assert "thinking_expliciet_uit" in verifier
        # De T-binding draagt alle tien ESS-05-bindingsvelden.
        assert cfg["t"]["verification_model"] == model
        assert cfg["t"]["renderer_version"] == omg.dienst.binding().renderer_version

    def test_effectieve_config_verandert_met_het_verifiermodel(self):
        class _AnderVerifier:
            def __init__(self):
                from services.ai.model_router import ModelRouter

                self._router = ModelRouter.from_config()

            def __getattr__(self, naam):
                return getattr(self._router, naam)

            def get_model(self, task_type, *a, **kw):
                if task_type == "ess05_verification":
                    return "anthropic", "ander-verifiermodel"
                return self._router.get_model(task_type, *a, **kw)

        basis = runner.effectieve_config(_omgeving(_FakeProvider()))
        ander = runner.effectieve_config(
            _omgeving(_FakeProvider(), router=_AnderVerifier())
        )
        assert pi.sha_json(basis) != pi.sha_json(ander)

    def test_freeze_bindt_de_verificatieprompt(self):
        omg = _omgeving(_FakeProvider())
        velden = runner.freezevelden(omg, runner.PROEVEN["R7"], "t")
        assert velden["prompt_version"] == Ess05AssessmentService.PROMPT_VERSION
        assert (
            velden["verification_prompt_version"]
            == Ess05VerificationService.PROMPT_VERSION
        )


class TestGeenEchteCalls:
    def test_alleen_r11_staat_open_voor_echte_calls(self):
        # R10 (besluit Chris 26-09) is na de inhoudelijke stop op R720 (C3)
        # gesloten, net als R1–R7, de gestopte R8 en R9; alleen R11 (eigen
        # besluit, 26-09) is open. De besluiten blijven gepind.
        assert [n for n, p in runner.PROEVEN.items() if p.echt_toegestaan] == [
            "R11",
            "R12",
            "R13",
            "R14",
            "R15",
            "R16",
            "R17",
        ]
        assert runner.PROEVEN["R11"].budgetbesluit_sha256 is not None
        assert runner.PROEVEN["R10"].budgetbesluit_sha256 is not None
        assert runner.PROEVEN["R9"].budgetbesluit_sha256 is not None
        assert runner.PROEVEN["R8"].budgetbesluit_sha256 is not None

    def test_oude_r7_freeze_past_niet_op_de_huidige_software(self, tmp_path):
        """Een freeze met de R7-identiteit (T/13) start geen call meer."""
        omg = _omgeving(_FakeProvider())
        freeze = dict(runner.freezevelden(omg, runner.PROEVEN["R7"], "t"))
        freeze["prompt_version"] = "ess05-assess/13"
        freeze.pop("verification_prompt_version")
        pad = tmp_path / "freeze.json"
        pad.write_text(json.dumps(freeze), encoding="utf-8")
        with pytest.raises(gb.BudgetSchendingError, match="prompt_version"):
            runner.controleer_freeze(
                pad,
                omg,
                runner.PROEVEN["R7"],
                "t",
                dataset_sha256="x",
                herhaal_ids=[],
            )

    def test_cli_echt_r7_geweigerd_zonder_omgeving(self, monkeypatch, tmp_path):
        def verboden(**_kw):
            raise AssertionError("geen live omgeving voor een gesloten ronde")

        monkeypatch.setattr(runner, "live_omgeving", verboden)
        pad = _gevallenbestand(tmp_path, 9)
        with pytest.raises(SystemExit) as fout:
            runner.main(["--proef", "R7", "--fase", "ontwikkeling", "--gevallen",
                         str(pad), "--uitmap", str(tmp_path), "--echt"])  # fmt: skip
        assert fout.value.code == 2

    def test_echte_tweestaps_t_geweigerd_voor_grootboek_en_netwerk(self, tmp_path):
        # Correctie v2: een programmatisch geopende kopie van R7 is niet de
        # geregistreerde proef; de geregistreerde open R7 weigert op het aantal
        # goedgekeurde modelstappen (test_def768_stapreservering).
        pad = _gevallenbestand(tmp_path, 9)
        provider = _ConceptProvider()
        omg = dataclasses.replace(_omgeving(provider), echt=True)
        with pytest.raises(gb.BudgetSchendingError, match="geregistreerde"):
            _t(omg, tmp_path, pad, _open_r7(tmp_path, pad))
        assert provider.aanroepen == []
        assert not (tmp_path / "r7" / "callgrootboek.jsonl").exists()

    def test_eenstaps_dienst_zou_de_weigering_niet_raken(self, tmp_path):
        """Positieve controle: het aantal stappen volgt uit de dienst (verifier
        aanwezig of niet), niet uit de ronde."""
        omg = dataclasses.replace(_omgeving(_FakeProvider()), echt=True)
        assert runner.clientaanroepen_per_t_geval(omg.dienst) == 2

        class _Eenstaps:
            TASK_TYPE = "validation"
            PROMPT_VERSION = "x"

        assert runner.clientaanroepen_per_t_geval(_Eenstaps()) == 1


class TestOfflineTweeFasen:
    def test_tweede_fase_eigen_reservering_onbruikbare_verificatie_geen_pass(
        self, tmp_path
    ):
        """Correctie v2 (plan WP5): de verificatie krijgt een eigen reservering
        in plaats van een weigering binnen die van de beoordeling. Deze provider
        beantwoordt ook de verificatievraag met een concept: onbruikbaar, dus
        een fout van de verificatiefase en nooit een pass."""
        pad = _gevallenbestand(tmp_path, 1)
        provider = _ConceptProvider()
        proef = dataclasses.replace(
            runner.PROEVEN["R7"], t_ontwikkelinvoer_sha256=_sha(pad)
        )
        _t(_omgeving(provider), tmp_path, pad, proef)
        assert len(provider.aanroepen) == 2
        assert all(a["model"] for a in provider.aanroepen)
        (record_pad,) = (tmp_path / "uit").rglob("001-ontwikkeling-*.json")
        record = json.loads(record_pad.read_text(encoding="utf-8"))
        fasen = record["fasen"]
        assert set(fasen) == {"beoordeling", "verificatie"}
        assert fasen["beoordeling"]["task_type"] == "validation"
        assert fasen["beoordeling"]["raw_response_sha256"]
        assert fasen["verificatie"]["task_type"] == "ess05_verification"
        assert [s["stap"] for s in record["reserveringen"]] == [
            "beoordeling",
            "verificatie",
        ]
        assert [s["client_aanroepen"] for s in record["reserveringen"]] == [1, 1]
        assert record["transport"]["bewakingsweigering"] is None
        assert record["beoordelingsdocument"]["error"]["phase"] == "verification"
        assert record["reserveringen"][1]["afsluitstatus"] == "modelfout"
        assert record["uitkomst"]["status"] != "pass"


class TestProefinvoer:
    PROJECTIE = {
        "begrip": "lener",
        "tekst": "Persoon met een actuele lening bij de instelling.",
        "context": {
            "organisatorische_context": ["X" * 50],
            "juridische_context": [],
            "wettelijke_basis": [],
        },
        "buren": [
            {
                "term": "klant",
                "definitie": "Kort.",
                "herkomst": "gebruiker",
                "bevestigd": True,
            }
        ],
    }

    def test_nulcallroute_rekent_met_context_als_materiaal(self):
        """Zelfde materiaal als de dienst: een te lange context is
        `input_truncated` vóór het netwerk, net als in `Ess05AssessmentService`."""
        route = pi.route(self.PROJECTIE, None, max_passage_chars=30)
        assert route["soort"] == "nulcall"
        assert "context" in route["reden"]

    def test_binnen_de_grens_blijft_het_een_aanroep(self):
        route = pi.route(self.PROJECTIE, None, max_passage_chars=400)
        assert route["soort"] == "aanroep"


class TestVergelijking:
    def test_alleen_een_toegepast_oordeel_telt(self):
        geval = json.loads(
            (ROOT / "tests/fixtures/ess05/ontwikkelgevallen_v1.json").read_text(
                encoding="utf-8"
            )
        )["gevallen"][-2]
        projectie = pi.modelprojectie(geval)
        prompt = pi.bouw_t_prompt(projectie, laad_ess05_norm())
        bronnen_ruw, buren_ruw = pi.transport(projectie)
        document = bouw_ess05_beoordeling(
            projectie["begrip"],
            projectie["tekst"],
            projectie.get("context") or {},
            bronnen_ruw,
            buren=buren_ruw,
            intentie=pi.intentie(projectie),
            scenario="fail",
        )
        assert document["judgment"]["neighbours"]
        document["verification"] = None
        uitkomst = pi.replay(projectie, assessment=document, binding=None)
        vergelijking = runner._vergelijk(geval, prompt, document, uitkomst)
        assert vergelijking["lacks_differentia"] is None
        assert all(b["gekregen"] is None for b in vergelijking["per_buur"])
