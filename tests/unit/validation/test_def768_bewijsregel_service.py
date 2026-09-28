"""DEF-768 — broninterpretatie plus gebonden controle (`ess05-bewijsregels/4`).

Spy op de echte `AIServiceInterface`-argumenten en, onder de echte AIServiceV2,
op de providerberichten. Het model is hier een fake: dit bewijst de keten
(één interpretatie, geldigheid vóór controle, geïsoleerde controles, stop bij
de eerste afwijzing), niet de modelkwaliteit.
"""

from __future__ import annotations

import asyncio
import copy
import json
import re
from types import SimpleNamespace

import pytest

from domain.ess05 import bewijsregels as br
from domain.ess05.lokale_controle import (
    LOKAAL_VERIFICATIESCHEMA,
    bouw_gevolgtrekkingspakket,
)
from services.validation import ess05_bewijsregel_service as bs
from services.validation.ess05_local_verification_service import (
    Ess05LocalVerificationService,
)
from services.validation.ess05_verification_service import aanroepgrens
from tests.unit.domain import (
    test_def768_bewijsregels as domeintest,
    test_def768_bewijsregels as dt,
)
from tests.unit.domain.test_def768_bewijsregels import (
    BRON,
    BRON_A,
    BRON_C,
    BUUR,
    BUUR_A,
    BUUR_C,
    DEFINITIE,
    _interpretatie_a,
    _interpretatie_c,
    _invoer,
    _zonder,
)

pytestmark = [pytest.mark.unit]

_HASH = re.compile(r'<controlepakket packet_hash="([0-9a-f]{64})">')


def _controleantwoord(user: str, uitkomst: str = "supported") -> str:
    return json.dumps(
        {
            "schema_version": LOKAAL_VERIFICATIESCHEMA,
            "packet_hash": _HASH.search(user).group(1),
            "checks": [{"item": "uitspraak", "outcome": uitkomst, "finding": "x"}],
        }
    )


class _SpyAI:
    """`generate_definition`: registreert de argumenten; interpretatie of controle."""

    default_model = "spy-model"

    def __init__(self, interpretatie, *, controle=lambda naam: "supported", fout=None):
        self.interpretatie = interpretatie
        self.controle = controle
        self.fout = fout
        self.aanroepen: list[dict] = []

    async def generate_definition(self, **kwargs):
        self.aanroepen.append(kwargs)
        if self.fout is not None:
            raise self.fout
        if kwargs["task_type"] == bs.Ess05BewijsregelService.TASK_TYPE:
            tekst = (
                self.interpretatie
                if isinstance(self.interpretatie, str)
                else json.dumps(self.interpretatie)
            )
        else:
            user = kwargs["prompt"]
            naam = (
                "kern" if "In de definitie (B1)" in user
                else "buur" if "verhuur" in user.split("Volgens de citaten:", 1)[-1]
                else "doel"
            )  # fmt: skip
            tekst = _controleantwoord(user, self.controle(naam))
        return SimpleNamespace(
            text=tekst, model="spy-model", cached=False, tokens_used=10,
            metadata={"stop_reason": "end_turn"},
        )  # fmt: skip


def _dienst(ai) -> bs.Ess05BewijsregelService:
    controle = Ess05LocalVerificationService(ai, timeout_seconds=60, max_tokens=3000)
    return bs.Ess05BewijsregelService(ai, controle=controle)


def _beoordeel(ai, invoer):
    return asyncio.run(_dienst(ai).beoordeel(invoer))


class TestDrieVarianten:
    def test_a_open_na_een_interpretatie_en_drie_controles(self):
        ai = _SpyAI(_interpretatie_a())
        resultaat = _beoordeel(ai, _invoer())
        assert resultaat.uitkomst == "review_required"
        assert [a["task_type"] for a in ai.aanroepen] == [
            "validation", "ess05_verification", "ess05_verification", "ess05_verification",
        ]  # fmt: skip
        assert [naam for naam, _ in resultaat.controles] == [
            "kern",
            "doel",
            f"buur:{BUUR}",
        ]
        assert resultaat.aanroepen == 4

    def test_b_ontbrekende_dekking_error_na_een_aanroep_zonder_controles(self):
        ai = _SpyAI(_interpretatie_a())
        resultaat = _beoordeel(ai, _invoer(onvolledig={BRON}))
        assert (resultaat.uitkomst, resultaat.fout.soort) == (
            "error",
            "dekking_ontbreekt",
        )
        assert len(ai.aanroepen) == 1 and resultaat.controles == ()

    def test_c_pass_na_een_interpretatie_en_drie_controles(self):
        ai = _SpyAI(_interpretatie_c())
        resultaat = _beoordeel(ai, _invoer(BRON_C, BUUR_C))
        assert resultaat.uitkomst == "pass"
        assert len(ai.aanroepen) == 4
        assert "duur" in resultaat.tekst and br.BEREIKZIN in resultaat.tekst


class TestInterpretatieverzoek:
    def test_een_aanroep_op_de_beoordelingsroute_zonder_cache_of_retry(self):
        ai = _SpyAI(_interpretatie_a())
        _beoordeel(ai, _invoer())
        eerste = ai.aanroepen[0]
        assert (eerste["task_type"], eerste["temperature"], eerste["use_cache"],
                eerste["max_attempts"], eerste["max_retries"], eerste["max_tokens"]) == (
            "validation", 0.0, False, 1, 0, 3000,
        )  # fmt: skip

    def test_prompt_bevat_materiaal_en_buren_maar_geen_verwachting(self):
        ai = _SpyAI(_interpretatie_a())
        _beoordeel(ai, _invoer(onvolledig={BRON}))
        prompt = ai.aanroepen[0]["prompt"]
        for tekst in (DEFINITIE, BRON_A, BUUR_A, BUUR, "verhuur"):
            assert tekst in prompt
        assert 'omvang="uittreksel"' in prompt
        for verboden in ("review_required", "verwacht", "pass", "fail", "unsupported"):
            assert verboden not in prompt

    def test_controle_ziet_alleen_zijn_eigen_onderwerp(self):
        ai = _SpyAI(_interpretatie_a())
        _beoordeel(ai, _invoer())
        kern, doel, buur = (a["prompt"] for a in ai.aanroepen[1:])
        assert DEFINITIE in kern and BRON_A not in kern and BUUR_A not in kern
        # v4 (R16-herstel): het doel krijgt zijn eigen bron volledig plus de
        # vastgelegde context, maar geen buurbeschrijving en geen feit over verhuur.
        uitspraak = re.search(r'"uitspraak": "([^"]*)"', doel).group(1)
        assert BUUR_A not in doel and BRON_A in doel and "erhuur" not in uitspraak
        assert "Servicedesk ICT-middelen" in doel
        assert DEFINITIE not in buur
        for prompt in (kern, doel, buur):
            assert "review_required" not in prompt and "pass" not in prompt

    def test_elke_aanroep_gaat_door_de_aanroepgrens(self):
        gezien = []

        from contextlib import contextmanager

        @contextmanager
        def grens(task_type, prompt_sha):
            gezien.append(task_type)
            yield

        ai = _SpyAI(_interpretatie_c())
        with aanroepgrens(grens):
            _beoordeel(ai, _invoer(BRON_C, BUUR_C))
        assert gezien == ["validation", *["ess05_verification"] * 3]


class TestStructureleWeigering:
    """Een model dat alles `supported` noemt, redt geen ongeldige interpretatie."""

    def test_fase_a_accepteerde_de_n2_samenstelling_bij_een_meegaand_model(self):
        # Contrast: het fase-A-mechanisme laat de vrije gevolgtrekking over aan
        # het model; een model dat supported zegt, geeft supported.
        ai = _SpyAI(None)
        pakket = bouw_gevolgtrekkingspakket(
            "Het materiaal beschrijft geen verhuurgeval buiten uitleen.",
            ["De kern noemt terbeschikkingstelling.", "De verhuurbeschrijving noemt geen kosten.",
             "Over verhuur staat verder niets vast."],
        )  # fmt: skip
        controle = Ess05LocalVerificationService(
            ai, timeout_seconds=60, max_tokens=3000
        )
        assert asyncio.run(controle.verifieer(pakket)).uitkomst == "supported"

    def test_ontbrekend_bewijsdoel_error_zonder_een_enkele_controle(self):
        ruw = copy.deepcopy(_interpretatie_a())
        ruw["antwoorden"] = _zonder(ruw["antwoorden"], "K1", BUUR)
        ai = _SpyAI(ruw)
        resultaat = _beoordeel(ai, _invoer())
        assert (resultaat.uitkomst, resultaat.fout.soort) == (
            "error",
            "doeldekking_onvolledig",
        )
        assert len(ai.aanroepen) == 1

    def test_vrij_conclusieveld_error(self):
        ruw = copy.deepcopy(_interpretatie_a())
        ruw["conclusie"] = "het materiaal beschrijft geen verhuurgeval buiten uitleen"
        resultaat = _beoordeel(_SpyAI(ruw), _invoer())
        assert (resultaat.uitkomst, resultaat.fout.soort) == ("error", "schemafout")

    @pytest.mark.parametrize(
        ("afgewezen", "aanroepen"), [("kern", 2), ("doel", 3), ("buur", 4)]
    )
    def test_afgewezen_premisse_laat_de_conclusie_vallen_en_stopt(
        self, afgewezen, aanroepen
    ):
        ai = _SpyAI(
            _interpretatie_c(),
            controle=lambda naam: "unsupported" if naam == afgewezen else "supported",
        )
        resultaat = _beoordeel(ai, _invoer(BRON_C, BUUR_C))
        assert (resultaat.uitkomst, resultaat.fout.soort) == (
            "error", "semantische_controle_mislukt",
        )  # fmt: skip
        assert len(ai.aanroepen) == aanroepen
        assert resultaat.regels is None and "Geen oordeel" in resultaat.tekst

    def test_undetermined_is_geen_supported(self):
        ai = _SpyAI(_interpretatie_c(), controle=lambda naam: "undetermined")
        resultaat = _beoordeel(ai, _invoer(BRON_C, BUUR_C))
        assert resultaat.uitkomst == "error" and len(ai.aanroepen) == 2

    def test_voorwaardelijke_doeleis_buiten_bereik_zonder_een_enkele_controle(self):
        # K4-rest (v3): het reviewertegenvoorbeeld wordt geen pass, ook als elk
        # controleverzoek supported zou zeggen; er volgt geen controle.
        k4 = domeintest.TestK4VoorwaardelijkeDoeleis()
        ai = _SpyAI(k4._ruw())
        resultaat = _beoordeel(ai, k4._invoer())
        assert (resultaat.uitkomst, resultaat.fout.soort) == ("error", "buiten_bereik")
        assert len(ai.aanroepen) == 1 and resultaat.controles == ()
        assert "bij storing" in resultaat.tekst and k4.EIS in resultaat.tekst

    def test_verloren_beperking_hangt_af_van_de_kerncontrole(self):
        # K3: tekstdekking slaagt; alleen de fragmentcontrole kan het verlies zien.
        k3 = domeintest.TestK3Tekstdekking()
        afgewezen = _SpyAI(
            k3._verlies(),
            controle=lambda n: "unsupported" if n == "kern" else "supported",
        )
        resultaat = _beoordeel(afgewezen, k3._invoer())
        assert resultaat.fout.soort == "semantische_controle_mislukt"
        assert "uitsluitend eigen" in afgewezen.aanroepen[1]["prompt"]


class TestTransportEnVorm:
    def test_transportfout_bij_interpretatie_error_na_een_aanroep(self):
        ai = _SpyAI(_interpretatie_a(), fout=TimeoutError("te laat"))
        resultaat = _beoordeel(ai, _invoer())
        assert resultaat.uitkomst == "error" and len(ai.aanroepen) == 1

    def test_geen_json_is_malformed(self):
        resultaat = _beoordeel(_SpyAI("dit is geen json"), _invoer())
        assert (resultaat.uitkomst, resultaat.fout.soort) == (
            "error",
            "malformed_response",
        )

    def test_zonder_definitie_geen_aanroep(self):
        invoer = br.Vergelijkingsinvoer(
            term="uitleen", materiaal={BUUR: BUUR_A}, buren=((BUUR, "verhuur"),)
        )
        ai = _SpyAI(_interpretatie_a())
        assert _beoordeel(ai, invoer).uitkomst == "error"
        assert ai.aanroepen == []


class TestPromptV4:
    """Tekstcontrole van prompt /4; bewijst niets over modelgedrag."""

    def test_versies(self):
        identiteit = bs.Ess05BewijsregelService.contractidentiteit()
        assert (
            identiteit["interpretation_prompt_version"]
            == "ess05-interpretatie-prompt/4"
        )
        assert identiteit["bewijsregel_version"] == "ess05-bewijsregels/6"
        assert identiteit["interpretation_schema_version"] == "ess05-interpretatie/3"

    def test_eenheden_genummerd_definitie_en_context_letterlijk(self):
        _, user = bs.bouw_interpretatieprompt(dt._invoer())
        assert f"[U1] {dt.BUUR_A}" in user
        assert "[U2] Uitleen:" in user
        assert f">{dt.DEFINITIE}</materiaal>" in user
        assert ">organisatorische_context: Servicedesk ICT-middelen</materiaal>" in user

    def test_hergebruik_en_verplicht_bewijs_expliciet_zonder_dubbelzinnigheid(self):
        system = bs.interpretatiesysteemprompt()
        assert "Hetzelfde nummer mag bij zoveel antwoorden staan" in system
        assert "minstens één eenheidsnummer" in system
        assert "nooit definitie of context" in system
        assert "precies één keer" not in system  # R17: twee betekenissen verwijderd
        assert '"citaten": ["U<n>"]' in system


class TestClientpad:
    def test_provider_krijgt_per_stap_alleen_system_en_eigen_user(self):
        from services.ai.base_client import ChatResponse
        from services.ai.model_router import ModelRouter
        from services.ai_service_v2 import AIServiceV2

        class _Provider:
            provider_name = "fake"

            def __init__(self):
                self.berichten: list[list[tuple[str, str]]] = []

            async def chat_completion(self, messages, model, **kwargs):
                self.berichten.append([(m.role, m.content) for m in messages])
                user = next(m.content for m in messages if m.role == "user")
                tekst = (
                    _controleantwoord(user)
                    if "<controlepakket" in user
                    else json.dumps(_interpretatie_c())
                )
                return ChatResponse(text=tekst, tokens_used=10, model=model)

        provider = _Provider()
        router = ModelRouter.from_config()
        ai = AIServiceV2(use_cache=False, ai_client=provider, model_router=router)
        controle = Ess05LocalVerificationService(ai, model_router=router)
        dienst = bs.Ess05BewijsregelService(ai, controle=controle, model_router=router)
        resultaat = asyncio.run(dienst.beoordeel(_invoer(BRON_C, BUUR_C)))
        assert resultaat.uitkomst == "pass"
        assert len(provider.berichten) == 4
        assert all([r for r, _ in b] == ["system", "user"] for b in provider.berichten)
        system, user = bs.bouw_interpretatieprompt(_invoer(BRON_C, BUUR_C))
        assert provider.berichten[0] == [("system", system), ("user", user)]
