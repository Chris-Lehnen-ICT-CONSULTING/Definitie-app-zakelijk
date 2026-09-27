"""DEF-768 fase A — lokale verificatie in een eigen, geïsoleerde verzoekcontext.

Getoetst op de werkelijke `AIServiceInterface.generate_definition`-argumenten
(spy) en op het providerpad onder `AIServiceV2` (fake providerclient): per
controlepakket precies één verzoek met alleen de uitspraak, het generieke
toetsprincipe van haar rol en haar eigen route. Metamorf: tekst buiten de
route verandert het verzoek niet; de route wel. Fail-closed op vorm, binding,
dekking en transport; een fout-positief modelantwoord wordt niet in code
gerepareerd.

Het blijvende RED-bewijs (`TestHuidigeGedeeldeContext`, strict xfail): de
huidige verifier (verify/4) stuurt voor elke claim het volledige materiaal, het
hele concept en alle routes mee — dat is geen isolatie.

Wat dit NIET bewijst: semantische juistheid van een echt model, of een volledig
geverifieerd concept (afhankelijke premissen en globale controle vallen buiten
fase A).
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from domain.ess05 import bewijs, lokale_controle as lc
from services.validation import ess05_local_verification_service as lv
from services.validation.ess05_verification_service import (
    Ess05VerificationService,
    aanroepgrens,
    bouw_verificatieprompt,
    prompthash,
)

pytestmark = [pytest.mark.unit]

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "ess05"
R13 = {
    g["id"]: g
    for g in json.loads(
        (FIXTURE / "r13_herkenbare_antwoorden_v1.json").read_text(encoding="utf-8")
    )["gevallen"]
}
_HASH = re.compile(r'packet_hash="([0-9a-f]{64})"')


def _concept(gid: str = "H2"):
    geval = R13[gid]
    concept, fouten = bewijs.valideer_antwoord(
        json.loads(geval["raw_response"]),
        geval["materiaal"],
        geval["buren"],
        schema=bewijs.ANTWOORDSCHEMA_2,
    )
    assert concept is not None, fouten
    return concept, dict(geval["materiaal"])


def _eerste(concept, rol: str) -> dict:
    return next(c for c in concept.data["claims"] if c["role"] == rol)


def _antwoordtekst(packet_hash: str, uitkomst: str = "supported", **anders) -> str:
    ruw = {
        "schema_version": lc.LOKAAL_VERIFICATIESCHEMA,
        "packet_hash": packet_hash,
        "checks": [
            {"item": lc.CONTROLE_ITEM, "outcome": uitkomst, "finding": "B1 draagt."}
        ],
    }
    ruw.update(anders)
    return json.dumps(ruw)


def _echo(uitkomst: str = "supported"):
    """Beantwoordt met de hash uit het eigen verzoek (zoals een meewerkend model)."""

    def antwoord(system_prompt: str, prompt: str) -> str:
        return _antwoordtekst(_HASH.search(prompt).group(1), uitkomst)

    return antwoord


class _SpyAI:
    """`AIServiceInterface.generate_definition`: registreert de echte argumenten."""

    default_model = "spy-model"

    def __init__(
        self, antwoord=None, *, fout: Exception | None = None, stop="end_turn"
    ):
        self.antwoord = antwoord or _echo()
        self.fout = fout
        self.stop = stop
        self.aanroepen: list[dict] = []

    async def generate_definition(self, **kwargs):
        self.aanroepen.append(kwargs)
        if self.fout is not None:
            raise self.fout
        return SimpleNamespace(
            text=self.antwoord(kwargs["system_prompt"], kwargs["prompt"]),
            model="spy-model",
            cached=False,
            tokens_used=12,
            metadata={"stop_reason": self.stop},
        )


def _dienst(ai) -> lv.Ess05LocalVerificationService:
    return lv.Ess05LocalVerificationService(ai, timeout_seconds=60, max_tokens=3000)


def _verifieer(ai, pakket):
    return asyncio.run(_dienst(ai).verifieer(pakket))


def _verzoek(ai) -> str:
    (aanroep,) = ai.aanroepen
    return aanroep["system_prompt"] + "\n" + aanroep["prompt"]


def _pakketten(gid: str = "H2"):
    concept, materiaal = _concept(gid)
    materiaal_claim = _eerste(concept, bewijs.ROL_MATERIAAL)
    gevolg = _eerste(concept, bewijs.ROL_GEVOLGTREKKING)
    return (
        concept,
        materiaal,
        lc.pakket_uit_concept(concept, materiaal_claim["id"], materiaal),
        lc.pakket_uit_concept(concept, gevolg["id"], materiaal),
    )


def _verboden(concept, claim_id: str, materiaal) -> list[str]:
    """Wat een lokaal verzoek voor `claim_id` niet mag bevatten (isolatiecontract)."""
    claims = {c["id"]: c for c in concept.data["claims"]}
    claim = claims[claim_id]
    plaatsen = {e["id"]: e for e in concept.data["evidence"]}
    eigen_teksten = {claim["text"], *(claims[p]["text"] for p in claim["premises"])}
    geciteerd = {plaatsen[e]["quote"] for e in claim["evidence"]}
    verboden = [
        c["text"]
        for c in claims.values()
        if c["text"] not in eigen_teksten
        and not any(c["text"] in t for t in eigen_teksten)
    ]
    verboden += [t for t in materiaal.values() if t not in geciteerd]
    return [*verboden, concept.hash]


class TestHuidigeGedeeldeContext:
    """RED-bewijs: verify/4 levert per claim geen geïsoleerde context."""

    @pytest.mark.xfail(
        strict=True,
        reason="verify/4 zet materiaal, concept en alle routes in één verzoek",
    )
    def test_huidige_verifier_voldoet_niet_aan_het_isolatiecontract(self):
        concept, materiaal, pakket, _ = _pakketten()
        regels = "\n".join(f"{k}: {v}" for k, v in materiaal.items())
        system, user = bouw_verificatieprompt(
            regels, concept, norm={"uitleg": "u"}, toetsinstructie="t"
        )
        claim = pakket.binding["claim"]
        lekken = [v for v in _verboden(concept, claim, materiaal) if v in system + user]
        assert lekken == []

    def test_lokale_verifier_voldoet_voor_elke_claim(self):
        concept, materiaal = _concept()
        for claim in concept.data["claims"]:
            if claim["role"] == bewijs.ROL_AFWEZIGHEID:
                continue
            ai = _SpyAI()
            _verifieer(ai, lc.pakket_uit_concept(concept, claim["id"], materiaal))
            verzoek = _verzoek(ai)
            lekken = [
                v for v in _verboden(concept, claim["id"], materiaal) if v in verzoek
            ]
            assert lekken == [], claim["id"]


class TestVerzoek:
    def test_een_aanroep_met_productieopties_en_eigen_taak(self):
        _, _, pakket, _ = _pakketten()
        ai = _SpyAI()
        _verifieer(ai, pakket)
        (aanroep,) = ai.aanroepen
        assert set(aanroep) == {
            "prompt", "system_prompt", "task_type", "temperature", "max_tokens",
            "timeout_seconds", "use_cache", "max_attempts", "max_retries",
            "token_estimate", "offload_postprocessing",
        }  # fmt: skip
        assert aanroep["task_type"] == Ess05VerificationService.TASK_TYPE
        assert (aanroep["temperature"], aanroep["use_cache"]) == (0.0, False)
        assert (aanroep["max_attempts"], aanroep["max_retries"]) == (1, 0)
        assert (aanroep["max_tokens"], aanroep["timeout_seconds"]) == (3000, 60)

    def test_systeemprompt_is_alleen_het_toetsprincipe_van_de_rol(self):
        _, _, materiaal_pakket, gevolg_pakket = _pakketten()
        for pakket in (materiaal_pakket, gevolg_pakket):
            ai = _SpyAI()
            _verifieer(ai, pakket)
            (aanroep,) = ai.aanroepen
            assert aanroep["system_prompt"] == lv.lokale_systeemprompt(pakket.rol)
            assert pakket.inhoud["uitspraak"] not in aanroep["system_prompt"]
        assert lv.lokale_systeemprompt(bewijs.ROL_MATERIAAL) != lv.lokale_systeemprompt(
            bewijs.ROL_GEVOLGTREKKING
        )

    def test_gebruikersprompt_draagt_exact_het_pakket(self):
        _, _, pakket, _ = _pakketten()
        ai = _SpyAI()
        _verifieer(ai, pakket)
        prompt = ai.aanroepen[0]["prompt"]
        assert f'packet_hash="{pakket.hash}"' in prompt
        for citaat in pakket.inhoud["citaten"]:
            assert json.dumps(citaat["citaat"], ensure_ascii=False)[1:-1] in prompt

    def test_invoerregistratie_bindt_aan_pakket_en_prompt(self):
        _, _, pakket, _ = _pakketten()
        ai = _SpyAI()
        resultaat = _verifieer(ai, pakket)
        (aanroep,) = ai.aanroepen
        assert dict(resultaat.invoer) == {
            "packet_hash": pakket.hash,
            "rol": pakket.rol,
            "prompt_version": lv.Ess05LocalVerificationService.PROMPT_VERSION,
            "packet_schema_version": lc.PAKKETSCHEMA,
            "verification_schema_version": lc.LOKAAL_VERIFICATIESCHEMA,
            "prompt_sha256": prompthash(aanroep["system_prompt"], aanroep["prompt"]),
            "deadline_seconds": 60,
            "max_tokens": 3000,
        }
        assert resultaat.attributie["model"] == "spy-model"
        assert resultaat.attributie["task_type"] == Ess05VerificationService.TASK_TYPE
        assert resultaat.raw_hash is not None


class TestMetamorf:
    def _verzoek_voor(self, concept, claim_id, materiaal):
        ai = _SpyAI()
        _verifieer(ai, lc.pakket_uit_concept(concept, claim_id, materiaal))
        (aanroep,) = ai.aanroepen
        return aanroep["system_prompt"], aanroep["prompt"]

    def test_ander_claim_of_ongeciteerd_materiaal_verandert_het_verzoek_niet(self):
        concept, materiaal, pakket, _ = _pakketten()
        claim_id = pakket.binding["claim"]
        basis = self._verzoek_voor(concept, claim_id, materiaal)
        # Een andere claim anders geformuleerd: dit verzoek blijft gelijk.
        data = concept.als_dict()
        ander = next(c for c in data["claims"] if c["id"] != claim_id)
        ander["text"] = "Volledig andere uitspraak elders in het concept."
        gewijzigd_concept = bewijs.Ess05Concept(data)
        assert gewijzigd_concept.hash != concept.hash
        assert self._verzoek_voor(gewijzigd_concept, claim_id, materiaal) == basis

    def test_ongeciteerde_tekst_in_hetzelfde_materiaal_verandert_het_verzoek_niet(self):
        concept, materiaal = _concept()
        # Een materiaalclaim die een fragment van een bron citeert.
        plaatsen = {e["id"]: e for e in concept.data["evidence"]}
        claim = next(
            c
            for c in concept.data["claims"]
            if c["role"] == bewijs.ROL_MATERIAAL
            and any(
                plaatsen[e]["material_id"].startswith("source:")
                and plaatsen[e]["quote"] != materiaal[plaatsen[e]["material_id"]]
                for e in c["evidence"]
            )
        )
        pakket = lc.pakket_uit_concept(concept, claim["id"], materiaal)
        refs = [
            lc.Citaatverwijzing(c["material_id"], c["start"], c["end"])
            for c in pakket.binding["citaten"]
        ]
        basis = lc.bouw_materiaalpakket(pakket.inhoud["uitspraak"], refs, materiaal)
        # Tekst ná de citaten van een geciteerde bron (buiten de route) wijzigen;
        # posities blijven gelijk.
        bron = next(r.material_id for r in refs if r.material_id.startswith("source:"))
        anders = {**materiaal, bron: materiaal[bron] + " Aanvullende ongeciteerde zin."}
        gewijzigd = lc.bouw_materiaalpakket(pakket.inhoud["uitspraak"], refs, anders)
        ai_a, ai_b = _SpyAI(), _SpyAI()
        _verifieer(ai_a, basis)
        _verifieer(ai_b, gewijzigd)
        assert ai_a.aanroepen[0]["prompt"] == ai_b.aanroepen[0]["prompt"]
        assert ai_a.aanroepen[0]["system_prompt"] == ai_b.aanroepen[0]["system_prompt"]
        assert basis.binding != gewijzigd.binding  # de binding ziet het wel

    def test_andere_route_verandert_verzoek_en_binding(self):
        _, _, _, gevolg = _pakketten()
        premissen = [p["uitspraak"] for p in gevolg.inhoud["premissen"]]
        kleiner = lc.bouw_gevolgtrekkingspakket(
            gevolg.inhoud["uitspraak"], premissen[:-1]
        )
        ai_a, ai_b = _SpyAI(), _SpyAI()
        a, b = _verifieer(ai_a, gevolg), _verifieer(ai_b, kleiner)
        assert ai_a.aanroepen[0]["prompt"] != ai_b.aanroepen[0]["prompt"]
        assert a.invoer["packet_hash"] != b.invoer["packet_hash"]
        assert a.invoer["prompt_sha256"] != b.invoer["prompt_sha256"]


class TestAparteContexten:
    def test_elk_pakket_een_eigen_verzoek_zonder_de_ander(self):
        _, _, p1, p2 = _pakketten()
        ai = _SpyAI()
        resultaten = asyncio.run(_dienst(ai).verifieer_pakketten([p1, p2]))
        assert [r.invoer["packet_hash"] for r in resultaten] == [p1.hash, p2.hash]
        eerste, tweede = (a["system_prompt"] + a["prompt"] for a in ai.aanroepen)
        assert p2.inhoud["uitspraak"] not in eerste and p2.hash not in eerste
        assert p1.inhoud["uitspraak"] not in tweede and p1.hash not in tweede
        for premisse in p2.inhoud["premissen"]:
            assert premisse["uitspraak"] not in eerste

    def test_dubbel_pakket_geweigerd_voor_elke_aanroep(self):
        _, _, p1, _ = _pakketten()
        ai = _SpyAI()
        with pytest.raises(ValueError, match="dubbel"):
            asyncio.run(_dienst(ai).verifieer_pakketten([p1, p1]))
        assert ai.aanroepen == []

    def test_aanroepgrens_per_verzoek_met_eigen_prompthash(self):
        _, _, p1, p2 = _pakketten()
        gezien: list[tuple[str, str]] = []

        def grens(taak: str, sha: str):
            gezien.append((taak, sha))
            return __import__("contextlib").nullcontext()

        ai = _SpyAI()
        with aanroepgrens(grens):
            resultaten = asyncio.run(_dienst(ai).verifieer_pakketten([p1, p2]))
        assert gezien == [
            (Ess05VerificationService.TASK_TYPE, r.invoer["prompt_sha256"])
            for r in resultaten
        ]


class TestUitkomstEnFouten:
    @pytest.mark.parametrize("uitkomst", bewijs.UITKOMSTEN)
    def test_uitkomst_is_gegeven_geen_fout(self, uitkomst):
        _, _, pakket, _ = _pakketten()
        resultaat = _verifieer(_SpyAI(_echo(uitkomst)), pakket)
        assert (resultaat.uitkomst, resultaat.fout) == (uitkomst, None)
        assert resultaat.bevinding == "B1 draagt."

    def test_fout_positief_wordt_niet_gerepareerd(self):
        """Een ontoereikende route (kernfragment) die het model toch steunt, blijft supported."""
        concept, materiaal = _concept()
        kern = materiaal["definition"]
        fragment = lc.bouw_materiaalpakket(
            "De hele kern noemt geen enkel kostenkenmerk.",
            [lc.Citaatverwijzing("definition", 0, kern.index(" "))],
            materiaal,
        )
        resultaat = _verifieer(_SpyAI(_echo("supported")), fragment)
        assert (resultaat.uitkomst, resultaat.fout) == ("supported", None)

    def test_antwoord_voor_een_ander_pakket_is_hashfout(self):
        _, _, p1, p2 = _pakketten()
        ai = _SpyAI(lambda s, p: _antwoordtekst(p2.hash))
        resultaat = _verifieer(ai, p1)
        assert (resultaat.uitkomst, resultaat.fout) == (None, "packet_hash_mismatch")

    @pytest.mark.parametrize(
        "checks",
        [[], [{"item": lc.CONTROLE_ITEM, "outcome": "supported", "finding": "a"}] * 2,
         [{"item": lc.CONTROLE_ITEM, "outcome": "supported", "finding": "a"},
          {"item": "extra", "outcome": "supported", "finding": "b"}]],
        ids=["ontbrekend", "dubbel", "extra"],
    )  # fmt: skip
    def test_dekking_fail_closed(self, checks):
        _, _, pakket, _ = _pakketten()
        ai = _SpyAI(lambda s, p: _antwoordtekst(pakket.hash, checks=checks))
        resultaat = _verifieer(ai, pakket)
        assert (resultaat.uitkomst, resultaat.fout) == (None, "malformed_response")

    def test_geen_json_fail_closed(self):
        _, _, pakket, _ = _pakketten()
        resultaat = _verifieer(_SpyAI(lambda s, p: "Het lijkt me gedragen."), pakket)
        assert (resultaat.uitkomst, resultaat.fout) == (None, "malformed_response")
        assert resultaat.ruw is None

    def test_weigering_van_de_provider_is_fout(self):
        _, _, pakket, _ = _pakketten()
        resultaat = _verifieer(_SpyAI(_echo(), stop="refusal"), pakket)
        assert (resultaat.uitkomst, resultaat.fout) == (None, "refusal")

    def test_afkapping_is_fout(self):
        _, _, pakket, _ = _pakketten()
        resultaat = _verifieer(_SpyAI(_echo(), stop="max_tokens"), pakket)
        assert (resultaat.uitkomst, resultaat.fout) == (None, "truncated_response")

    def test_timeout_is_fout_zonder_tweede_poging(self):
        _, _, pakket, _ = _pakketten()
        ai = _SpyAI(fout=TimeoutError("te laat"))
        resultaat = _verifieer(ai, pakket)
        assert (resultaat.uitkomst, resultaat.fout) == (None, "timeout")
        assert len(ai.aanroepen) == 1


class TestClientpad:
    """Onder de echte AIServiceV2 en clientadapter: wat de provider ontvangt."""

    def test_provider_ontvangt_per_pakket_alleen_system_en_eigen_user(self):
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
                return ChatResponse(
                    text=_antwoordtekst(_HASH.search(user).group(1)),
                    tokens_used=10,
                    model=model,
                )

        provider = _Provider()
        router = ModelRouter.from_config()
        ai = AIServiceV2(use_cache=False, ai_client=provider, model_router=router)
        verifier = Ess05VerificationService(ai, model_router=router)
        dienst = lv.Ess05LocalVerificationService.voor_verifier(
            ai, verifier, model_router=router
        )
        _, _, p1, p2 = _pakketten()
        resultaten = asyncio.run(dienst.verifieer_pakketten([p1, p2]))
        assert [r.uitkomst for r in resultaten] == ["supported", "supported"]
        assert len(provider.berichten) == 2
        for berichten, pakket in zip(provider.berichten, (p1, p2), strict=True):
            system, user = lv.bouw_lokale_prompt(pakket)
            assert berichten == [("system", system), ("user", user)]
