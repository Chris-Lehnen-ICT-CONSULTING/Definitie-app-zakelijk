"""DEF-772 WP3: de AI-verwijzingsbeoordeling (INT-03) op een deterministische fake-AI-grens.

Echte async aanroepen van `Int03AssessmentService.assess`; alleen de AI-grens
is een fake die `AIServiceInterface.generate_definition` nabootst en elke
aanroep vastlegt. Geen netwerk, geen echt model, geen productiedatabase. De
tests bewijzen wat code kan bewijzen: routing via task_type (geen hardcoded
model), de opt-ins tegen verborgen retry-stapeling en ruwe caching,
promptopbouw met de norm uit het regelrecord en het materiaal als gegevens,
citaatcontrole, fail-closed parsing, afkap- en invoergrenzen, attributie,
cache-binding en het gesloten foutbeleid — niet de inhoudelijke kwaliteit van
een model.

Reviewcorrecties (review-codex-wp3-v1, dispositie v3): afgewezen citaten,
modeltekst in structuurfouten en uitzonderingsteksten bereiken log noch
foutmelding (R2); term, toelichting, elke contextwaarde én het totale
invoerbudget zijn vóór de modelaanroep begrensd (R3).
"""

from __future__ import annotations

import hashlib
import json
import logging

import pytest

from domain.int03.contract import (
    BEVINDING_GEEN_VERWIJZEND_WOORD,
    BEVINDING_MEERDUIDIG,
    CONTRACTVERSIE,
    VERDICT_FAIL,
    VERDICT_INSUFFICIENT,
    VERDICT_PASS,
    VERWIJZING_MEERDUIDIG,
    VERWIJZING_ONBESLIST,
    bereken_int03_vingerafdruk,
)
from services.interfaces import (
    AIGenerationResult,
    AIRateLimitError,
    AIServiceError,
    AITimeoutError,
)
from services.validation.int03_assessment_service import (
    Int03AssessmentService,
    bouw_beoordelingsprompt,
    laad_int03_norm,
)

pytestmark = [pytest.mark.unit]

BEGRIP = "proefbegrip"
TEKST = (
    "Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die "
    "de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd."
)
CONTEXT = {
    "organisatorische_context": ["Synthetische Organisatie"],
    "juridische_context": [],
    "wettelijke_basis": [],
}
TOELICHTING = "Synthetische bedoelde betekenis van het proefbegrip."
#: Synthetische gevoelige inhoud die een model of SDK zou kunnen terugkaatsen (R2).
GEVOELIG = "Testpersoon Voorbeeldnaam heeft diagnose Voorbeeldziekte"
GEVOELIGE_MARKERS = ("Voorbeeldnaam", "Voorbeeldziekte")


def _uitvoer(**over):
    uitvoer = {
        "verdict": VERDICT_FAIL,
        "reason": "'het' kan naar 'Geheel' of 'gebeurtenis' verwijzen.",
        "references": [
            {
                "word": "het",
                "passage": "waardoor het volledig kan worden begrepen",
                "status": VERWIJZING_MEERDUIDIG,
                "reading": "twee plausibele lezingen",
                "candidates": [
                    {"quote": "Geheel", "reason": "onzijdig onderwerp"},
                    {"quote": "gebeurtenis", "reason": "dichtstbijzijnd naamwoord"},
                ],
            }
        ],
        "question": None,
        "uncertainty": None,
    }
    uitvoer.update(over)
    return uitvoer


GEEN_WOORD_UITVOER = {
    "verdict": VERDICT_PASS,
    "reason": "Geen verwijzend woord.",
    "references": [],
    "question": None,
    "uncertainty": None,
}


class FakeAI:
    """Deterministische AI-grens: geeft per aanroep de volgende geplande uitkomst."""

    def __init__(self, *uitkomsten, metadata=None):
        self.uitkomsten = list(uitkomsten)
        self.calls = []
        self.default_model = "fake-default-model"
        self.metadata = metadata

    async def generate_definition(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt, **kwargs})
        uitkomst = self.uitkomsten.pop(0) if self.uitkomsten else _uitvoer()
        if isinstance(uitkomst, Exception):
            raise uitkomst
        tekst = (
            uitkomst
            if isinstance(uitkomst, str)
            else json.dumps(uitkomst, ensure_ascii=False)
        )
        return AIGenerationResult(
            text=tekst,
            model="fake-model-1",
            tokens_used=42,
            generation_time=0.01,
            metadata=dict(self.metadata or {}),
        )


class FakeRouter:
    def get_model(self, task_type):
        return "fakeprovider", f"routed-{task_type}"


def _service(*uitkomsten, metadata=None, **kw):
    ai = FakeAI(*uitkomsten, metadata=metadata)
    return Int03AssessmentService(ai, model_router=FakeRouter(), **kw), ai


async def _assess(service, *, tekst=TEKST, toelichting=TOELICHTING, contexten=None):
    return await service.assess(
        BEGRIP,
        tekst,
        CONTEXT if contexten is None else contexten,
        toelichting=toelichting,
        correlation_id="def772-test",
    )


def _vingerafdruk(**over):
    args = {
        "begrip": BEGRIP,
        "tekst": TEKST,
        "contexten": CONTEXT,
        "toelichting": TOELICHTING,
    }
    args.update(over)
    return bereken_int03_vingerafdruk(
        args["begrip"], args["tekst"], args["contexten"], args["toelichting"]
    )


# --- norm -------------------------------------------------------------------------


def test_norm_komt_uit_het_actieve_regelrecord():
    norm = laad_int03_norm()
    assert set(norm) >= {"uitleg", "toelichting", "toetsvraag"}
    assert norm["uitleg"].startswith("Voor ieder voornaamwoord in de definitie")
    assert "loos 'het' of het voegwoord 'dat' verwijst niet" in norm["toelichting"]
    service, _ = _service()
    verwacht = hashlib.sha256(
        json.dumps(norm, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    assert service.norm_sha256 == verwacht


def test_binding_zonder_netwerk():
    service, ai = _service()
    binding = service.binding()
    assert ai.calls == []
    assert binding.prompt_version == Int03AssessmentService.PROMPT_VERSION
    assert binding.norm_sha256 == service.norm_sha256
    assert binding.provider == "fakeprovider"
    assert binding.model == "routed-validation"


# --- prompt -----------------------------------------------------------------------


def test_prompt_draagt_norm_k6_regels_en_materiaal_als_gegevens():
    systeem, gebruiker = bouw_beoordelingsprompt(
        BEGRIP, TEKST, CONTEXT, toelichting=TOELICHTING, norm=laad_int03_norm()
    )
    # Norm uit het record (één bron van waarheid).
    assert laad_int03_norm()["uitleg"] in systeem
    assert laad_int03_norm()["toetsvraag"] in systeem
    # K6 in de beoordelingsprompt.
    for marker in ("loos", "voegwoord", "bijzin", "vooruit", "lemma", "nabijheid"):
        assert marker in systeem.lower(), marker
    # Term ondersteunend, context/toelichting alleen betekenisgrond.
    assert "geen antecedent" in systeem.lower()
    assert "gegevens" in systeem.lower()
    # Gesloten antwoordvorm.
    for veld in ("verdict", "references", "question", "uncertainty", "candidates"):
        assert f'"{veld}"' in systeem
    assert "score" not in systeem.lower().replace("no_score", "")
    # Materiaal.
    assert TEKST in gebruiker
    assert BEGRIP in gebruiker
    assert TOELICHTING in gebruiker
    assert "Synthetische Organisatie" in gebruiker


def test_prompt_zonder_toelichting_en_context_is_deterministisch():
    a = bouw_beoordelingsprompt(BEGRIP, TEKST, {}, toelichting=None, norm={})
    b = bouw_beoordelingsprompt(BEGRIP, TEKST, {}, toelichting=None, norm={})
    assert a == b


# --- hoofdroute -------------------------------------------------------------------


async def test_gegronde_beoordeling_via_taakrouting_zonder_hardcoded_model():
    service, ai = _service(_uitvoer())
    beoordeling = await _assess(service)
    d = beoordeling.als_dict()

    assert len(ai.calls) == 1
    call = ai.calls[0]
    assert call["task_type"] == "validation"
    assert call["temperature"] == 0.0
    assert "model" not in call or call["model"] is None
    assert call["system_prompt"]
    # Outputtokenlimiet: Chris (26-09-2026) "pas de tokenlimiet aan naar max
    # 2500" — het standaardbudget van de dienst is exact wat de AI-laag krijgt.
    assert call["max_tokens"] == 2500
    assert call["timeout_seconds"] <= 60
    # Opt-ins tegen ruwe cache onder de validatie en verborgen retry-stapeling.
    assert call["use_cache"] is False
    assert call["max_attempts"] == 1
    assert call["max_retries"] == 0
    assert d["status"] == "assessed"
    assert d["contract_version"] == CONTRACTVERSIE
    assert d["prompt_version"] == Int03AssessmentService.PROMPT_VERSION
    assert d["norm_sha256"] == service.norm_sha256
    assert d["fingerprint"] == _vingerafdruk()
    assert d["attribution"]["model"] == "fake-model-1"
    assert d["attribution"]["provider"] == "fakeprovider"
    assert d["attribution"]["task_type"] == "validation"
    assert d["attribution"]["tokens_used"] == 42
    assert d["attribution"]["cached"] is False
    assert d["attribution"]["attempts_observed"] == 1
    assert d["assessed_at"]
    assert d["judgment"]["verdict"] == VERDICT_FAIL
    assert d["judgment"]["status"] == "fail"
    assert d["judgment"]["finding"] == BEVINDING_MEERDUIDIG
    assert d["judgment"]["references"][0]["word"] == "het"
    assert d["input"]["text_sha256"] == hashlib.sha256(TEKST.encode()).hexdigest()
    assert d["input"]["prompt_sha256"]
    assert d["raw_response_sha256"]
    assert d["elapsed_seconds"] >= 0


async def test_geen_verwijzend_woord_is_pass_na_modelcontrole():
    service, _ = _service(GEEN_WOORD_UITVOER)
    d = (await _assess(service, tekst="veelhoek met precies drie zijden")).als_dict()
    assert d["status"] == "assessed"
    assert d["judgment"]["verdict"] == VERDICT_PASS
    assert d["judgment"]["finding"] == BEVINDING_GEEN_VERWIJZEND_WOORD


async def test_onvoldoende_informatie_met_precies_een_vraag():
    uitvoer = _uitvoer(
        verdict=VERDICT_INSUFFICIENT,
        references=[
            {
                **_uitvoer()["references"][0],
                "status": VERWIJZING_ONBESLIST,
                "candidates": [],
            }
        ],
        question="Waarnaar verwijst 'het' volgens de bedoelde betekenis?",
    )
    service, _ = _service(uitvoer)
    d = (await _assess(service)).als_dict()
    assert d["status"] == "assessed"
    assert d["judgment"]["status"] == "review_required"
    assert d["judgment"]["question"].endswith("?")


async def test_antwoord_in_codeblok_wordt_geaccepteerd():
    service, _ = _service("```json\n" + json.dumps(_uitvoer()) + "\n```")
    d = (await _assess(service)).als_dict()
    assert d["status"] == "assessed"


# --- fail-closed parsing ---------------------------------------------------------


@pytest.mark.parametrize(
    "antwoord",
    [
        "geen json",
        "Hier is het oordeel: " + json.dumps(_uitvoer()),
        json.dumps([_uitvoer()]),
        json.dumps({**_uitvoer(), "score": 0.8}),
        json.dumps({k: v for k, v in _uitvoer().items() if k != "uncertainty"}),
        json.dumps(_uitvoer(verdict="ok")),
        json.dumps({**GEEN_WOORD_UITVOER, "question": "Wie?"}),
        json.dumps(_uitvoer(question="Wie? En wat?")),
        json.dumps(_uitvoer(verdict=VERDICT_PASS)),
    ],
    ids=[
        "geen-json",
        "omliggende-tekst",
        "lijst",
        "extra-veld",
        "ontbrekend-veld",
        "onbekend-verdict",
        "pass-met-vraag",
        "fail-met-twee-vragen",
        "verdict-strookt-niet",
    ],
)
async def test_misvormd_antwoord_is_technische_fout(antwoord):
    service, ai = _service(antwoord)
    d = (await _assess(service)).als_dict()
    assert d["status"] == "error"
    assert d["error"]["type"] == "malformed_response"
    assert d["judgment"] is None
    assert d["raw_response_sha256"] == hashlib.sha256(antwoord.encode()).hexdigest()
    # Nooit gecachet: opnieuw toetsen gaat terug naar het model.
    await _assess(service)
    assert len(ai.calls) == 2


async def test_verzonnen_citaat_is_unverifiable_evidence():
    ref = {**_uitvoer()["references"][0], "word": "zij", "passage": "zij vertrekt"}
    service, _ = _service(_uitvoer(references=[ref]))
    d = (await _assess(service)).als_dict()
    assert d["status"] == "error"
    assert d["error"]["type"] == "unverifiable_evidence"
    assert d["rejected"]
    assert d["judgment"] is None


async def test_verzonnen_kandidaat_is_unverifiable_evidence():
    ref = {
        **_uitvoer()["references"][0],
        "candidates": [
            {"quote": "Geheel", "reason": "x"},
            {"quote": "dossier", "reason": "verzonnen"},
        ],
    }
    service, _ = _service(_uitvoer(references=[ref]))
    d = (await _assess(service)).als_dict()
    assert d["error"]["type"] == "unverifiable_evidence"


# --- foutbeleid -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("exc", "soort"),
    [
        (AITimeoutError("te laat"), "timeout"),
        (AIRateLimitError("te veel"), "rate_limit"),
        (AIServiceError("kapot"), "connection"),
        (RuntimeError("onbekend"), "unknown"),
    ],
    ids=["timeout", "rate_limit", "connection", "unknown"],
)
async def test_dienstfout_is_technische_fout_nooit_oordeel(exc, soort, caplog):
    service, _ = _service(exc)
    with caplog.at_level(logging.WARNING):
        d = (await _assess(service)).als_dict()
    assert d["status"] == "error"
    assert d["error"]["type"] == soort
    assert d["judgment"] is None
    assert d["prompt_version"] == Int03AssessmentService.PROMPT_VERSION
    assert d["fingerprint"] == _vingerafdruk()
    # Privacy: de definitietekst en toelichting worden niet gelogd.
    assert TEKST not in caplog.text
    assert TOELICHTING not in caplog.text


async def test_afgekapt_antwoord_is_truncated_response():
    service, _ = _service(_uitvoer(), metadata={"stop_reason": "max_tokens"})
    d = (await _assess(service)).als_dict()
    assert d["status"] == "error"
    assert d["error"]["type"] == "truncated_response"
    assert d["attribution"]["stop_reason"] == "max_tokens"
    # Het gemelde budget is het werkelijk gebruikte standaardbudget (2500),
    # niet het oude 1200; afkappen blijft een technische fout, geen tolerantie.
    assert "max_tokens=2500" in d["error"]["message"]
    assert "1200" not in d["error"]["message"]


# --- outputtokenlimiet (Chris, 26-09-2026: "pas de tokenlimiet aan naar max 2500") ---


async def test_standaardbudget_2500_wordt_aan_de_ai_laag_doorgegeven():
    """Zonder expliciet budget stuurt de dienst exact 2500 outputtokens mee;
    provider/model (taakrouting), norm en prompt veranderen niet mee."""
    service, ai = _service(_uitvoer())
    d = (await _assess(service)).als_dict()
    (call,) = ai.calls
    assert call["max_tokens"] == 2500
    assert call["task_type"] == "validation"
    assert "model" not in call or call["model"] is None
    assert d["status"] == "assessed"
    assert d["norm_sha256"] == service.norm_sha256


async def test_expliciet_budget_1200_blijft_als_parameter_gelden():
    """Een bewust meegegeven 1200 (de eerste WP6-meetopzet) blijft exact het
    budget van die aanroep én van de afkapmelding — de default overschrijft
    geen expliciete parameter."""
    service, ai = _service(_uitvoer(), max_tokens=1200)
    await _assess(service)
    assert ai.calls[0]["max_tokens"] == 1200

    afgekapt, _ = _service(
        _uitvoer(), metadata={"stop_reason": "max_tokens"}, max_tokens=1200
    )
    d = (await _assess(afgekapt)).als_dict()
    assert d["status"] == "error"
    assert d["error"]["type"] == "truncated_response"
    assert "max_tokens=1200" in d["error"]["message"]


async def test_te_lange_invoer_is_technische_fout_zonder_aanroep():
    service, ai = _service(max_input_chars=50)
    d = (await _assess(service)).als_dict()
    assert ai.calls == []
    assert d["status"] == "error"
    assert d["error"]["type"] == "input_too_long"
    lange_toelichting = "x" * 51
    service2, ai2 = _service(max_input_chars=50)
    d2 = (
        await _assess(service2, tekst="kort", toelichting=lange_toelichting)
    ).als_dict()
    assert ai2.calls == []
    assert d2["error"]["type"] == "input_too_long"


async def test_geen_dienst_zonder_ai_service():
    with pytest.raises(ValueError, match="ai_service"):
        Int03AssessmentService(None, model_router=FakeRouter())


# --- R3: alle promptvelden en het totale budget begrensd vóór de aanroep ----------


@pytest.mark.parametrize(
    "aanroep",
    [
        {"begrip": "x" * 100_000},
        {"contexten": {**CONTEXT, "organisatorische_context": ["x" * 100_000]}},
        {"contexten": {**CONTEXT, "wettelijke_basis": ["kort", "x" * 41]}},
        {"contexten": {**CONTEXT, "juridische_context": ["x" * 41]}},
    ],
    ids=["term", "organisatorische_context", "wettelijke_basis", "juridische_context"],
)
async def test_term_en_contextwaarden_zijn_begrensd_zonder_aanroep(aanroep):
    # Reproductie van reviewbevinding R3: met max_input_chars=40 en 100.000
    # tekens in de term of een contextwaarde mag er geen modelaanroep zijn.
    service, ai = _service(max_input_chars=40)
    args = {"begrip": BEGRIP, "contexten": CONTEXT, **aanroep}
    d = (
        await service.assess(
            args["begrip"], "kort", args["contexten"], toelichting=None
        )
    ).als_dict()
    assert ai.calls == []
    assert d["status"] == "error"
    assert d["error"]["type"] == "input_too_long"
    assert d["judgment"] is None
    assert "xxxx" not in d["error"]["message"]  # veldnamen en tellingen, geen inhoud
    assert d["input"]["max_input_chars"] == 40


async def test_totaal_invoerbudget_is_begrensd_zonder_aanroep():
    # Elk veld afzonderlijk binnen de grens per veld, samen boven het budget.
    service, ai = _service(max_input_chars=40, max_total_input_chars=100)
    contexten = {
        "organisatorische_context": ["a" * 39],
        "juridische_context": ["b" * 39],
        "wettelijke_basis": ["c" * 39],
    }
    d = (
        await service.assess("d" * 39, "e" * 39, contexten, toelichting="f" * 39)
    ).als_dict()
    assert ai.calls == []
    assert d["error"]["type"] == "input_too_long"
    assert "totale invoer" in d["error"]["message"]
    assert "aaaa" not in d["error"]["message"]
    assert d["input"]["max_total_input_chars"] == 100
    assert d["input"]["input_chars"] == 6 * 39


async def test_binnen_de_grenzen_registreert_het_document_de_grenzen():
    service, ai = _service(_uitvoer())
    d = (await _assess(service)).als_dict()
    assert len(ai.calls) == 1
    assert d["input"]["max_input_chars"] == 4000
    assert d["input"]["max_total_input_chars"] >= 4000
    assert d["input"]["input_chars"] == (
        len(BEGRIP) + len(TEKST) + len(TOELICHTING) + len("Synthetische Organisatie")
    )


# --- R2: geen modelcitaat, modeltekst of uitzonderingstekst in log of melding ----


def _log_is_gevuld(caplog) -> bool:
    return any("INT-03" in r.getMessage() for r in caplog.records)


async def test_afgewezen_citaat_staat_niet_in_log_of_foutmelding(caplog):
    # Reproductie van reviewbevinding R2: een verzonnen passage met (synthetische)
    # persoonsnaam en diagnose.
    ref = {**_uitvoer()["references"][0], "passage": GEVOELIG}
    service, _ = _service(_uitvoer(references=[ref]))
    with caplog.at_level(logging.DEBUG):
        d = (await _assess(service)).als_dict()
    assert d["status"] == "error"
    assert d["error"]["type"] == "unverifiable_evidence"
    assert "passage niet in de definitie" in d["error"]["message"]
    for marker in GEVOELIGE_MARKERS:
        assert marker not in caplog.text
        assert marker not in d["error"]["message"]
    assert _log_is_gevuld(caplog)
    # Het bewijs zelf blijft in het document (UI/diagnose), gescheiden van
    # meldingen en logs.
    assert GEVOELIG in d["rejected"][0]["detail"]


async def test_structuurfout_met_modeltekst_staat_niet_in_log_of_foutmelding(caplog):
    service, _ = _service(_uitvoer(verdict=GEVOELIG))
    with caplog.at_level(logging.DEBUG):
        d = (await _assess(service)).als_dict()
    assert d["error"]["type"] == "malformed_response"
    for marker in GEVOELIGE_MARKERS:
        assert marker not in caplog.text
        assert marker not in d["error"]["message"]
    assert _log_is_gevuld(caplog)


async def test_uitzonderingstekst_staat_niet_in_log_of_foutmelding(caplog):
    # Een SDK-uitzondering kan prompt- of credentialfragmenten dragen: alleen
    # het uitzonderingstype is technische metadata.
    service, _ = _service(AIServiceError(f"sleutel sk-geheim-123; {GEVOELIG}"))
    with caplog.at_level(logging.DEBUG):
        d = (await _assess(service)).als_dict()
    assert d["error"]["type"] == "connection"
    assert "AIServiceError" in d["error"]["message"]
    for marker in (*GEVOELIGE_MARKERS, "sk-geheim-123"):
        assert marker not in caplog.text
        assert marker not in d["error"]["message"]
    assert _log_is_gevuld(caplog)


class KapotteRouter:
    """ModelRouter waarvan de modelkeuze faalt (reviewbevinding R2, v2)."""

    def get_model(self, task_type):
        msg = f"router: {GEVOELIG}"
        raise RuntimeError(msg)


async def test_routerfout_wordt_zonder_uitzonderingstekst_gelogd(caplog):
    ai = FakeAI(_uitvoer())
    service = Int03AssessmentService(ai, model_router=KapotteRouter())
    with caplog.at_level(
        logging.DEBUG, logger="services.validation.int03_assessment_service"
    ):
        binding = service.binding()
        d = (await _assess(service)).als_dict()
    # Terugval op het standaardmodel van de AI-service, zonder provider; de
    # DEBUG-melding noemt alleen taak en uitzonderingstype.
    assert binding.provider is None
    assert binding.model == ai.default_model
    assert any("ModelRouter gaf geen model" in r.getMessage() for r in caplog.records)
    for marker in GEVOELIGE_MARKERS:
        assert marker not in caplog.text
    assert d["status"] == "assessed"
    assert d["attribution"]["provider"] is None
    assert GEVOELIG not in json.dumps(d, ensure_ascii=False)


# --- cache en binding -------------------------------------------------------------


async def test_zelfde_invoer_gebruikt_de_interne_cache():
    service, ai = _service(_uitvoer(), _uitvoer())
    eerste = (await _assess(service)).als_dict()
    tweede = (await _assess(service)).als_dict()
    assert len(ai.calls) == 1
    assert eerste["attribution"]["cached"] is False
    assert tweede["attribution"]["cached"] is True
    assert tweede["judgment"] == eerste["judgment"]


@pytest.mark.parametrize(
    "wijziging",
    [
        {"tekst": TEKST + " Extra."},
        {"toelichting": "Andere bedoeling."},
        {"contexten": {**CONTEXT, "juridische_context": ["Strafrecht"]}},
    ],
    ids=["tekst", "toelichting", "context"],
)
async def test_gewijzigde_invoer_omzeilt_de_cache(wijziging):
    service, ai = _service(_uitvoer(), GEEN_WOORD_UITVOER)
    eerste = (await _assess(service)).als_dict()
    tweede = (await _assess(service, **wijziging)).als_dict()
    assert len(ai.calls) == 2
    assert tweede["fingerprint"] != eerste["fingerprint"]


async def test_andere_term_omzeilt_de_cache():
    service, ai = _service(_uitvoer(), _uitvoer())
    await _assess(service)
    await service.assess("anderbegrip", TEKST, CONTEXT, toelichting=TOELICHTING)
    assert len(ai.calls) == 2


async def test_zonder_cache_elke_keer_naar_het_model():
    service, ai = _service(_uitvoer(), _uitvoer(), cache_size=0)
    await _assess(service)
    await _assess(service)
    assert len(ai.calls) == 2
