"""DEF-743 pakket F — handmatig verbetervoorstel: alleen op verzoek, max één aanroep.

Echte `DefinitionEditRepository` op een tijdelijke SQLite-database (D-primitieven
`reserve_source_proposal` / `record_source_proposal_outcome` /
`apply_source_proposal` / `set_source_proposal_status`), echte
`ValidationOrchestratorV2` + `ModularValidationService` voor de hertoetsing, en
twee geteld nagebootste AI-grenzen (`FakeAI` voor het voorstel,
`FakeBronbeoordeling` voor de bronbeoordeling). Geen model, netwerk of
productie-DB.

Bewezen:

* 0 modelaanroepen bij weergave (`bronbasis_van_record`) en bij een CON-02-fail
  zonder verzoek; precies 1 bij een expliciete aanvraag.
* Oorzaak eerst: geen bronnen / technische fout / verouderde beoordeling /
  AI-onzekerheid / voldoet ⇒ geblokkeerd zonder aanroep én zonder reservering.
* Dubbelklik, rerun en herladen (verse repository) leveren `attempt_consumed`:
  de poging is duurzaam verbruikt (ook na een storing of afgewezen voorstel).
* Het origineel blijft ongewijzigd tot een expliciete Apply; Apply hertoetst de
  kandidaat mét dezelfde bronset, slaat tekst + nieuwe beoordeling + historie
  atomair op tegen de getoonde versie; een oude pass blijft niet staan.
* Verouderd voorstel (tekst intussen gewijzigd) en technische hertoetsfout
  laten het origineel intact; afwijzen bewaart het bewijs.
* Uitvoercontroles: contextinjectie, kaal bronwoord, leeg of ongewijzigd
  voorstel worden `blocked` (geen stille reparatie), een storing `error`.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any

import pytest

from database.definitie_repository import DefinitieRepository
from domain.sources.contract import bereken_bronvingerafdruk
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import DefinitionEditService
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from services.source_proposal_service import (
    OORZAAK_AI_ONZEKER,
    OORZAAK_GEEN_BEVINDING,
    OORZAAK_GEEN_BEWIJS,
    OORZAAK_STALE,
    OORZAAK_TECHNISCH,
    OORZAAK_TEKORTKOMING,
    OORZAAK_TRANSPORT,
    SourceProposalService,
    controleer_voorstel,
    diagnose_bronbasis,
)
from tests.fixtures.def743_fakes import (
    BEGRIP,
    BRONNEN,
    CITAAT,
    JUR,
    ORG,
    TEKST,
    VOORSTEL_JSON,
    WET,
    FakeAI,
    FakeBronbeoordeling,
    bouw_beoordeling,
)

pytestmark = [pytest.mark.unit]

ACTOR = "synthetische-redacteur"
CONTEXTEN = {
    "organisatorische_context": ORG,
    "juridische_context": JUR,
    "wettelijke_basis": WET,
}


# ------------------------------------------------------------------ helpers


def _echte_validatie(beoordeling: FakeBronbeoordeling):
    from services.null_repository import NullDefinitionRepository
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from toetsregels.manager import get_toetsregel_manager

    return ValidationOrchestratorV2(
        ModularValidationService(
            toetsregel_manager=get_toetsregel_manager(),
            repository=NullDefinitionRepository(),
        ),
        source_assessment_service=beoordeling,
    )


def _definition(*, scenario: str = "fail", bronnen: list | None = None, **meta: Any):
    bronnen = deepcopy(BRONNEN) if bronnen is None else bronnen
    metadata: dict[str, Any] = {
        "status": "draft",
        "created_by": "generator",
        "sources": deepcopy(bronnen),
        "provenance_sources": deepcopy(bronnen),
        "source_assessment": (
            bouw_beoordeling(
                BEGRIP,
                TEKST,
                CONTEXTEN,
                bronnen,
                scenario=scenario,
                peildatum="2026-09-15",
            )
            if bronnen
            else None
        ),
        "definitie_origineel": TEKST,
        "definitie_eindtekst": TEKST,
        "peildatum": "2026-09-15",
    }
    metadata.update(meta)
    return Definition(
        begrip=BEGRIP,
        definitie=TEKST,
        categorie="type",
        organisatorische_context=list(ORG),
        juridische_context=list(JUR),
        wettelijke_basis=list(WET),
        metadata=metadata,
    )


@pytest.fixture
def repo(tmp_path) -> DefinitionEditRepository:
    return DefinitionEditRepository(str(tmp_path / "voorstel.db"))


def _service(
    repo: DefinitionEditRepository,
    ai: FakeAI | None,
    beoordeling: FakeBronbeoordeling | None = None,
) -> DefinitionEditService:
    return DefinitionEditService(
        repository=repo,
        validation_service=_echte_validatie(beoordeling or FakeBronbeoordeling("pass")),
        proposal_service=SourceProposalService(ai) if ai is not None else None,
    )


def _vraag(service: DefinitionEditService, did: int, **kw: Any) -> dict[str, Any]:
    return asyncio.run(service.vraag_verbetervoorstel(did, actor=ACTOR, **kw))


def _pas_toe(service: DefinitionEditService, did: int, pid: str) -> dict[str, Any]:
    return asyncio.run(service.pas_voorstel_toe(did, pid, actor=ACTOR))


def _record(repo, did):
    rec = DefinitieRepository(repo.db_path).get_definitie(did)
    assert rec is not None
    return rec


# ------------------------------------------------------ diagnose (puur)


def _con02(status: str, delen: list[dict], review: dict | None = None) -> dict:
    return {"status": status, "parts": delen, "review": review or {}}


def _deel(pid: str, status: str, field: str | None = "source_assessment") -> dict:
    return {"id": pid, "status": status, "field": field, "reason": f"{pid} {status}"}


def test_diagnose_onderscheidt_de_oorzaken():
    beoordeling = bouw_beoordeling(BEGRIP, TEKST, CONTEXTEN, BRONNEN, scenario="fail")
    assert (
        diagnose_bronbasis(None, None, validation_status="validation_unknown").oorzaak
        == OORZAAK_TECHNISCH
    )
    assert diagnose_bronbasis(None, None).oorzaak == OORZAAK_GEEN_BEWIJS
    geen_bron = _con02(
        "review_required",
        [_deel("source_authority", "review_required", None)],
        {"assessment": {"status": "no_sources", "applied": False}},
    )
    assert diagnose_bronbasis(geen_bron, None).oorzaak == OORZAAK_GEEN_BEWIJS
    fout = _con02("error", [_deel("source_authority", "error")])
    assert (
        diagnose_bronbasis(
            fout, {"status": "error", "error": {"type": "timeout"}}
        ).oorzaak
        == OORZAAK_TECHNISCH
    )
    kwitantie = diagnose_bronbasis(
        fout, {"status": "error", "error": {"type": "receipt_error"}}
    )
    assert kwitantie.oorzaak == OORZAAK_TRANSPORT
    stale = _con02(
        "review_required",
        [_deel("semantic_support", "review_required")],
        {"assessment": {"status": "assessed", "applied": False, "reason": "gewijzigd"}},
    )
    assert diagnose_bronbasis(stale, beoordeling).oorzaak == OORZAAK_STALE
    onzeker = _con02(
        "review_required",
        [_deel("semantic_support", "review_required")],
        {"assessment": {"status": "assessed", "applied": True}},
    )
    assert diagnose_bronbasis(onzeker, beoordeling).oorzaak == OORZAAK_AI_ONZEKER
    voldoet = _con02(
        "pass",
        [_deel("semantic_support", "pass")],
        {"assessment": {"status": "assessed", "applied": True}},
    )
    assert diagnose_bronbasis(voldoet, beoordeling).oorzaak == OORZAAK_GEEN_BEVINDING
    tekortkoming = _con02(
        "fail",
        [_deel("semantic_support", "fail")],
        {"assessment": {"status": "assessed", "applied": True}},
    )
    d = diagnose_bronbasis(tekortkoming, beoordeling)
    assert d.oorzaak == OORZAAK_TEKORTKOMING and d.voorstel_mogelijk
    assert d.bewijs and d.bewijs[0]["quote"] == CITAAT
    # Een fail zónder geverifieerd citaat is geen bewezen tekortkoming.
    zonder_bewijs = deepcopy(beoordeling)
    for deel in zonder_bewijs["parts"].values():
        deel["evidence"] = []
    assert (
        diagnose_bronbasis(tekortkoming, zonder_bewijs).oorzaak == OORZAAK_GEEN_BEWIJS
    )
    # Transportverlies: alles geleverd, niets in de prompt.
    transport = diagnose_bronbasis(
        tekortkoming,
        beoordeling,
        receipt={"status": "none", "channels": {"rag": {"supplied": 2, "used": 0}}},
    )
    assert transport.oorzaak == OORZAAK_TRANSPORT


def test_uitvoercontroles_weigeren_cosmetische_of_lege_voorstellen():
    bronnen = [
        {"source_id": "rag:1", "title": "Awb artikel 1:1", "locator": "art. 1:1"}
    ]
    basis = {
        "origineel": TEKST,
        "begrip": BEGRIP,
        "contexten": CONTEXTEN,
        "bronnen": bronnen,
    }
    assert "leeg" in controleer_voorstel(kandidaat="", **basis)
    assert "leeg" in controleer_voorstel(kandidaat=None, **basis)
    assert "gelijk" in controleer_voorstel(kandidaat=f"  {TEKST} ", **basis)
    assert "contextinjectie" in controleer_voorstel(
        kandidaat=TEKST + " van Stichting Zilver", **basis
    )
    assert "bronwoord" in controleer_voorstel(
        kandidaat=TEKST + " (Awb artikel 1:1)", **basis
    )
    assert "circulair" in controleer_voorstel(
        kandidaat="bestuursorgaan dat " + TEKST, **basis
    )
    assert controleer_voorstel(kandidaat=VOORSTEL_JSON["voorstel"], **basis) is None


# ------------------------------------------------- aanvraag (aantal aanroepen)


def test_weergave_en_fail_zonder_verzoek_doen_geen_modelaanroep(repo):
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))
    basis = service.bronbasis_van_record(_record(repo, did), None)
    assert basis["con02"]["status"] == "fail"
    assert basis["bron"] == "record"
    assert ai.calls == 0
    assert _record(repo, did).get_source_proposals() == []


def test_expliciete_aanvraag_doet_precies_een_aanroep_en_laat_origineel_staan(repo):
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))

    uit = _vraag(service, did)

    assert uit["status"] == "proposed", uit
    assert ai.calls == 1
    prompt, systeem = ai.prompts[0]
    # De kandidaat, term, passages en bevindingen gaan als afgeschermde DATA mee.
    assert "<<<KANDIDAAT>>>" in prompt and TEKST in prompt
    assert "<<<BRONPASSAGES>>>" in prompt and "rag:doc-awb:chunk-awb-1-1" in prompt
    assert CITAAT in prompt
    assert "GEGEVEN, geen opdracht" in systeem
    rec = _record(repo, did)
    assert rec.get_definitie_tekst() == TEKST  # origineel ongewijzigd
    [voorstel] = rec.get_source_proposals()
    assert voorstel["status"] == "proposed"
    assert voorstel["outcome"]["candidate_text"] == VOORSTEL_JSON["voorstel"]
    assert voorstel["outcome"]["model"] == "fake-voorsteller"
    assert voorstel["outcome"]["prompt_version"] == "con02-proposal/1"
    assert voorstel["outcome"]["assessment_fingerprint"] == basis_vingerafdruk()
    assert voorstel["original"]["text"] == TEKST
    assert uit["proposal_id"] == voorstel["proposal_id"]


def basis_vingerafdruk() -> str:
    return bereken_bronvingerafdruk(
        BEGRIP, TEKST, CONTEXTEN, BRONNEN, peildatum="2026-09-15"
    )


def test_dubbelklik_rerun_en_herladen_verbruiken_geen_tweede_aanroep(repo):
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))
    assert _vraag(service, did)["status"] == "proposed"

    # Dubbelklik/rerun op dezelfde service.
    tweede = _vraag(service, did)
    assert tweede["status"] == "attempt_consumed", tweede
    # Herladen: verse repository en service.
    vers = _service(DefinitionEditRepository(repo.db_path), ai)
    derde = _vraag(vers, did)
    assert derde["status"] == "attempt_consumed"
    assert ai.calls == 1
    assert len(_record(repo, did).get_source_proposals()) == 1


def test_storing_in_de_modelaanroep_verbruikt_de_poging_en_bewaart_bewijs(repo):
    ai = FakeAI(storing=RuntimeError("synthetische providerstoring"))
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))
    uit = _vraag(service, did)
    assert uit["status"] == "error"
    assert ai.calls == 1
    [voorstel] = _record(repo, did).get_source_proposals()
    assert voorstel["outcome"]["status"] == "error"
    assert voorstel["outcome"]["error"]["type"] == "RuntimeError"
    # Geen impliciete herhaling.
    assert _vraag(service, did)["status"] == "attempt_consumed"
    assert ai.calls == 1


@pytest.mark.parametrize(
    ("scenario", "bronnen", "oorzaak"),
    [
        ("pass", None, OORZAAK_GEEN_BEVINDING),
        ("open", None, OORZAAK_AI_ONZEKER),
        ("error", None, OORZAAK_TECHNISCH),
        ("fail", [], OORZAAK_GEEN_BEWIJS),
    ],
)
def test_zonder_aantoonbare_tekortkoming_geen_aanroep_en_geen_reservering(
    repo, scenario, bronnen, oorzaak
):
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario=scenario, bronnen=bronnen))
    uit = _vraag(service, did)
    assert uit["status"] == "blocked", uit
    assert uit["diagnose"]["cause"] == oorzaak
    assert ai.calls == 0
    rec = _record(repo, did)
    assert rec.get_source_proposals() == []  # poging niet verbruikt
    assert rec.version_number == 1


def test_verouderde_beoordeling_blokkeert_zonder_aanroep(repo):
    """Het record draagt een beoordeling voor een andere tekst: eerst hertoetsen."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))
    bewerkt = DefinitionRepository(repo.db_path).get(did)
    bewerkt.definitie = TEKST + " (bewerkt)"
    assert repo.save(bewerkt) == did
    uit = _vraag(service, did)
    assert uit["status"] == "blocked"
    assert uit["diagnose"]["cause"] == OORZAAK_STALE
    assert ai.calls == 0


def test_opgeslagen_gebonden_beoordeling_gaat_voor_op_het_sessieresultaat(repo):
    """De opgeslagen volledige beoordeling (exact gebonden aan record) is de
    invoer voor de replay; een sessieresultaat — ook met passende vingerafdruk
    — vervangt die niet, en een sessieresultaat voor een andere tekst evenmin."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="pass"))
    rec = _record(repo, did)
    # Sessie: wrapper-beoordeling zegt fail (met bewijs) voor exact deze kandidaat.
    vers = bouw_beoordeling(
        BEGRIP, TEKST, CONTEXTEN, BRONNEN, scenario="fail", peildatum="2026-09-15"
    )
    from domain.sources.contract import beoordeel_bronbasis

    uitkomst = beoordeel_bronbasis(
        BEGRIP, TEKST, CONTEXTEN, BRONNEN, assessment=vers, peildatum="2026-09-15"
    )
    sessie = {
        "rule_results": {"CON-02": uitkomst.als_dict()},
        "source_assessment": vers,
        "validation_status": "validated",
    }
    basis = service.bronbasis_van_record(rec, sessie)
    assert basis["bron"] == "record" and basis["con02"]["status"] == "pass"
    # Andere vingerafdruk (andere tekst): eveneens record.
    ander = deepcopy(sessie)
    ander["rule_results"]["CON-02"]["fingerprint"] = "anders"
    ander["source_assessment"]["fingerprint"] = "anders"
    basis2 = service.bronbasis_van_record(rec, ander)
    assert basis2["bron"] == "record" and basis2["con02"]["status"] == "pass"


def test_zonder_voorsteldienst_geen_aanroep_en_expliciete_melding(repo):
    service = _service(repo, None)
    did = repo.save(_definition(scenario="fail"))
    uit = _vraag(service, did)
    assert uit["status"] == "unavailable"
    assert _record(repo, did).get_source_proposals() == []


def test_zonder_actor_wordt_niets_aangevraagd(repo):
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))
    uit = asyncio.run(service.vraag_verbetervoorstel(did, actor="  "))
    assert uit["status"] == "no_actor"
    assert ai.calls == 0


@pytest.mark.parametrize(
    ("antwoord", "reden"),
    [
        ({**VOORSTEL_JSON, "voorstel": None}, "geen voorstel"),
        (
            {**VOORSTEL_JSON, "voorstel": TEKST + " van Stichting Zilver"},
            "contextinjectie",
        ),
        ({**VOORSTEL_JSON, "voorstel": TEKST + " (Awb artikel 1:1)"}, "bronwoord"),
        ({**VOORSTEL_JSON, "voorstel": TEKST}, "gelijk"),
        ({**VOORSTEL_JSON, "reden": ""}, "geen reden"),
    ],
)
def test_ongeschikt_modelantwoord_wordt_blocked_en_verbruikt_de_poging(
    repo, antwoord, reden
):
    ai = FakeAI(antwoord)
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))
    uit = _vraag(service, did)
    assert uit["status"] == "blocked", uit
    assert reden in (uit["message"] or "")
    assert ai.calls == 1
    [voorstel] = _record(repo, did).get_source_proposals()
    assert voorstel["outcome"]["status"] == "blocked"
    assert _record(repo, did).get_definitie_tekst() == TEKST


def test_niet_json_antwoord_is_een_technische_fout(repo):
    ai = FakeAI("Dit is geen JSON.")
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))
    uit = _vraag(service, did)
    assert uit["status"] == "error"
    assert uit["error"]["type"] == "malformed_response"


# ------------------------------------------------------------- toepassen


def test_toepassen_hertoetst_met_dezelfde_bronnen_en_slaat_atomair_op(repo):
    ai = FakeAI()
    hertoets = FakeBronbeoordeling("pass")
    service = _service(repo, ai, hertoets)
    did = repo.save(_definition(scenario="fail"))
    aanvraag = _vraag(service, did)
    pid = aanvraag["proposal_id"]
    versie_voor = _record(repo, did).version_number

    uit = _pas_toe(service, did, pid)

    assert uit["status"] == "applied", uit
    assert hertoets.calls == 1
    assert hertoets.laatste_bronnen == BRONNEN  # DEZELFDE bronset
    assert hertoets.laatste_tekst == VOORSTEL_JSON["voorstel"]
    assert ai.calls == 1  # toepassen is geen tweede modelaanroep
    rec = _record(repo, did)
    assert rec.get_definitie_tekst() == VOORSTEL_JSON["voorstel"]
    assert rec.version_number == versie_voor + 1 == uit["version_number"]
    [voorstel] = rec.get_source_proposals()
    assert voorstel["status"] == "applied"
    bewijs = rec.get_source_evidence()
    assert bewijs["origin"] == "proposal_applied"
    assert bewijs["candidate"]["definitie"] == VOORSTEL_JSON["voorstel"]
    nieuwe_vingerafdruk = bereken_bronvingerafdruk(
        BEGRIP, VOORSTEL_JSON["voorstel"], CONTEXTEN, BRONNEN, peildatum="2026-09-15"
    )
    assert bewijs["source_assessment"]["fingerprint"] == nieuwe_vingerafdruk
    # Geen oude pass: de opgeslagen beoordeling is de nieuwe (voor de kandidaat).
    assert rec.get_source_evidence_history()[-1]["candidate"]["definitie"] == TEKST
    # Het hertoetsingsresultaat gaat als actueel resultaat terug naar de UI.
    assert (
        uit["validation"]["rule_results"]["CON-02"]["fingerprint"]
        == nieuwe_vingerafdruk
    )


def test_verouderd_voorstel_wordt_geweigerd_en_origineel_blijft(repo):
    ai = FakeAI()
    service = _service(repo, ai, FakeBronbeoordeling("pass"))
    did = repo.save(_definition(scenario="fail"))
    pid = _vraag(service, did)["proposal_id"]
    bewerkt = DefinitionRepository(repo.db_path).get(did)
    bewerkt.definitie = TEKST + " (intussen bewerkt)"
    assert repo.save(bewerkt) == did

    uit = _pas_toe(service, did, pid)
    assert uit["status"] == "stale_original", uit
    rec = _record(repo, did)
    assert rec.get_definitie_tekst() == TEKST + " (intussen bewerkt)"
    assert rec.get_source_proposal(pid)["status"] == "proposed"


def test_technische_hertoetsfout_laat_origineel_intact(repo):
    ai = FakeAI()
    service = _service(repo, ai, FakeBronbeoordeling("error"))
    did = repo.save(_definition(scenario="fail"))
    pid = _vraag(service, did)["proposal_id"]
    versie = _record(repo, did).version_number

    uit = _pas_toe(service, did, pid)
    assert uit["status"] == "technical_error", uit
    assert "CON-02" in uit["message"] or "bronbeoordeling" in uit["message"]
    rec = _record(repo, did)
    assert rec.get_definitie_tekst() == TEKST
    assert rec.version_number == versie
    assert rec.get_source_proposal(pid)["status"] == "proposed"


def test_storing_in_de_beoordelingsdienst_bij_hertoetsing_laat_origineel_intact(repo):
    ai = FakeAI()
    service = _service(repo, ai, FakeBronbeoordeling("raise"))
    did = repo.save(_definition(scenario="fail"))
    pid = _vraag(service, did)["proposal_id"]
    uit = _pas_toe(service, did, pid)
    assert uit["status"] == "technical_error"
    assert _record(repo, did).get_definitie_tekst() == TEKST


def test_versieconflict_bij_toepassen_schrijft_niets(repo, monkeypatch):
    ai = FakeAI()
    service = _service(repo, ai, FakeBronbeoordeling("pass"))
    did = repo.save(_definition(scenario="fail"))
    pid = _vraag(service, did)["proposal_id"]
    # Tussen lezen en schrijven wijzigt iemand het record (status-only).
    origineel_apply = repo.apply_source_proposal

    def _race(*args: Any, **kwargs: Any):
        from database.models import DefinitieStatus

        DefinitieRepository(repo.db_path).change_status(
            did, DefinitieStatus.REVIEW, "iemand-anders"
        )
        return origineel_apply(*args, **kwargs)

    monkeypatch.setattr(repo, "apply_source_proposal", _race)
    uit = _pas_toe(service, did, pid)
    assert uit["status"] == "version_conflict", uit
    rec = _record(repo, did)
    assert rec.get_definitie_tekst() == TEKST
    assert rec.get_source_proposal(pid)["status"] == "proposed"


def test_afwijzen_bewaart_het_voorstel_als_bewijs(repo):
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))
    pid = _vraag(service, did)["proposal_id"]
    uit = service.wijs_voorstel_af(did, pid, actor=ACTOR, note="Te ruim.")
    assert uit["status"] == "rejected"
    voorstel = _record(repo, did).get_source_proposal(pid)
    assert voorstel["status"] == "rejected"
    assert voorstel["outcome"]["candidate_text"] == VOORSTEL_JSON["voorstel"]
    # Afgewezen = poging verbruikt; toepassen kan niet meer.
    assert _vraag(service, did)["status"] == "attempt_consumed"
    assert asyncio.run(service.pas_voorstel_toe(did, pid, actor=ACTOR))["status"] == (
        "invalid_status"
    )
    assert ai.calls == 1


# ------------------------------------------- reviewbevindingen F1/F3/F4/F7/F8


@pytest.mark.parametrize("scenario", ["authority_fail", "reference_fail"])
def test_f1_niet_tekstuele_tekortkoming_verbruikt_de_poging_niet(repo, scenario):
    """F1: brongezag/verwijzing 'voldoet niet' bij geslaagde betekenissteun is
    geen gebrek in de definitiezin: geen reservering, geen modelaanroep."""
    from services.source_proposal_service import OORZAAK_NIET_TEKSTUEEL

    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario=scenario))
    basis = service.bronbasis_van_record(_record(repo, did), None)
    assert basis["con02"]["status"] == "fail"  # de regel faalt wél
    uit = _vraag(service, did)
    assert uit["status"] == "blocked", uit
    assert uit["diagnose"]["cause"] == OORZAAK_NIET_TEKSTUEEL
    assert ai.calls == 0
    assert _record(repo, did).get_source_proposals() == []


def test_f1_bewijs_hoort_bij_het_falende_betekenisonderdeel(repo):
    """F1: het bewijs voor het voorstel komt uitsluitend uit `semantic_support`
    (eigen citaten + niet-gesteunde claims), niet uit een pool van alle delen."""
    beoordeling = bouw_beoordeling(BEGRIP, TEKST, CONTEXTEN, BRONNEN, scenario="fail")
    # Verwijder het citaat bij betekenissteun; gezag/verwijzing houden hun citaat.
    beoordeling["parts"]["semantic_support"]["evidence"] = []
    from domain.sources.contract import beoordeel_bronbasis

    uitkomst = beoordeel_bronbasis(
        BEGRIP, TEKST, CONTEXTEN, BRONNEN, assessment=beoordeling
    )
    con02 = uitkomst.als_dict()
    # De kern maakt een fail zonder eigen bewijs 'open'; de diagnose mag dan
    # niet op het bewijs van andere onderdelen terugvallen.
    d = diagnose_bronbasis(con02, beoordeling)
    assert d.oorzaak != OORZAAK_TEKORTKOMING
    assert not d.voorstel_mogelijk
    # Met eigen bewijs: alleen dat bewijs (en de niet-gesteunde claim) gaat mee.
    volledig = bouw_beoordeling(BEGRIP, TEKST, CONTEXTEN, BRONNEN, scenario="fail")
    d2 = diagnose_bronbasis(
        beoordeel_bronbasis(
            BEGRIP, TEKST, CONTEXTEN, BRONNEN, assessment=volledig
        ).als_dict(),
        volledig,
    )
    assert d2.oorzaak == OORZAAK_TEKORTKOMING
    assert {b["part"] for b in d2.bewijs} == {"semantic_support"}
    assert any("rechterlijke macht" in b for b in d2.bevindingen)


def test_f1_afgewezen_modelclaim_op_betekenissteun_stopt(repo):
    """F1: een vermoede evaluatorfout (afgewezen claim op hetzelfde onderdeel)
    is geen betrouwbare, uitvoerbare bevinding."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail_rejected"))
    uit = _vraag(service, did)
    assert uit["status"] == "blocked", uit
    assert uit["diagnose"]["cause"] == OORZAAK_AI_ONZEKER
    assert ai.calls == 0


def test_f1_deskundige_correctie_van_betekenissteun_wordt_gehonoreerd(repo):
    """F1: corrigeert de deskundige `semantic_support` naar pass, dan is er
    geen tekortkoming meer (oorspronkelijk AI-oordeel blijft zichtbaar);
    corrigeert zij naar fail mét gebonden bewijs, dan is dát het bewijs."""
    from domain.sources.normalisatie import canoniseer_bronnen

    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))
    rec = _record(repo, did)
    awb = next(b for b in canoniseer_bronnen(BRONNEN) if b.source_id.startswith("rag:"))

    def _correctie(status: str, quote: str) -> dict[str, Any]:
        rec_nu = _record(repo, did)
        return {
            "type": "part_correction",
            "accepted": True,
            "actor": ACTOR,
            "rationale": "Deskundig oordeel over de betekenissteun.",
            "version_number": rec_nu.version_number,
            "fingerprint": basis_vingerafdruk(),
            "part_id": "semantic_support",
            "status": status,
            "evidence": [
                {
                    "source_id": awb.source_id,
                    "content_hash": awb.content_hash,
                    "source_version": awb.version,
                    "quote": quote,
                    "locator": awb.locator,
                }
            ],
        }

    assert repo.set_source_review(
        did,
        _correctie("pass", CITAAT),
        updated_by=ACTOR,
        expected_version=rec.version_number,
    )
    basis = service.bronbasis_van_record(_record(repo, did), None)
    assert (
        basis["con02"]["review"]["applied_correction"]["original"]["status"] == "fail"
    )
    uit = _vraag(service, did)
    assert (
        uit["status"] == "blocked"
        and uit["diagnose"]["cause"] == OORZAAK_GEEN_BEVINDING
    )
    assert ai.calls == 0

    # Correctie naar fail: het deskundige bewijs draagt het voorstel.
    rec2 = _record(repo, did)
    assert repo.set_source_review(
        did,
        _correctie("fail", "met uitzondering van de rechterlijke macht"),
        updated_by=ACTOR,
        expected_version=rec2.version_number,
    )
    uit2 = _vraag(service, did)
    assert uit2["status"] == "proposed", uit2
    assert uit2["diagnose"]["cause"] == OORZAAK_TEKORTKOMING
    assert [b["quote"] for b in uit2["diagnose"]["evidence"]] == [
        "met uitzondering van de rechterlijke macht"
    ]
    assert ai.calls == 1
    # Het oorspronkelijke AI-oordeel blijft bewaard (in de kernsamenvatting).
    basis2 = service.bronbasis_van_record(_record(repo, did), None)
    assert (
        basis2["con02"]["review"]["applied_correction"]["original"]["status"] == "fail"
    )


def test_f8_kwitantie_zonder_werkelijk_gebruik_is_transportverlies(repo):
    """F8: een opgeslagen kwitantie (via D `get_contractvelden`) met geleverde
    maar nul gebruikte bronnen ⇒ transport, geen reservering, geen aanroep."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(
        _definition(
            scenario="fail",
            source_receipt={
                "version": "1",
                "status": "none",
                "sources": [],
                "omitted": [
                    {
                        "source_type": "rag",
                        "source_id": "chunk-awb-1-1",
                        "reason": "budget",
                    },
                    {
                        "source_type": "document",
                        "source_id": "upload-7",
                        "reason": "budget",
                    },
                ],
                "errors": [],
                "channels": {
                    "rag": {"enabled": True, "supplied": 1, "used": 0},
                    "document": {"enabled": True, "supplied": 1, "used": 0},
                },
            },
        )
    )
    rec = _record(repo, did)
    assert rec.get_contractvelden().get(
        "source_receipt"
    )  # D-adapter levert de kwitantie
    uit = _vraag(service, did)
    assert uit["status"] == "blocked", uit
    assert uit["diagnose"]["cause"] == OORZAAK_TRANSPORT
    assert ai.calls == 0
    assert _record(repo, did).get_source_proposals() == []


@pytest.mark.parametrize(
    "antwoord",
    [
        {**VOORSTEL_JSON, "behouden": 123},
        {**VOORSTEL_JSON, "behouden": "geen lijst"},
        {**VOORSTEL_JSON, "voorstel": {"tekst": "object"}},
        {**VOORSTEL_JSON, "reden": ["lijst"]},
        {**VOORSTEL_JSON, "onzekerheid": {"x": 1}},
    ],
)
def test_f7_misvormde_veldtypes_worden_een_duurzame_error_uitkomst(repo, antwoord):
    """F7: geldig JSON met verkeerde veldtypes eindigt als `error` bij D — geen
    permanente `reserved`, de poging blijft verbruikt, geen herhaling."""
    ai = FakeAI(antwoord)
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))
    uit = _vraag(service, did)
    assert uit["status"] == "error", uit
    assert uit["error"]["type"] == "malformed_fields"
    [voorstel] = _record(repo, did).get_source_proposals()
    assert voorstel["status"] != "reserved"
    assert voorstel["outcome"]["status"] == "error"
    assert _vraag(service, did)["status"] == "attempt_consumed"
    assert ai.calls == 1


def test_f7_onverwachte_fout_in_de_dienst_wordt_vastgelegd_zonder_bronlek(
    repo, monkeypatch
):
    """F7: een onverwachte exceptie ná de reservering (parser/provider) wordt
    als `error` vastgelegd; de melding lekt geen prompt- of bronpassage."""
    from services import source_proposal_service as m

    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))

    def _klapt(*a: Any, **k: Any):
        raise RuntimeError("parser kapot: " + "X" * 10)

    monkeypatch.setattr(m, "parse_voorstel", _klapt)
    uit = _vraag(service, did)
    assert uit["status"] == "error", uit
    [voorstel] = _record(repo, did).get_source_proposals()
    assert voorstel["outcome"]["status"] == "error"
    melding = voorstel["outcome"]["error"]["message"]
    assert "<<<" not in melding and TEKST not in melding and CITAAT not in melding
    assert _vraag(service, did)["status"] == "attempt_consumed"


def test_f3_getoonde_versie_reist_mee_en_wijkt_niet_stil_uit(repo):
    """F3: aanvraag, toepassen en afwijzen nemen de door de UI getoonde
    `expected_version` mee; een intussen gewijzigd record ⇒ versieconflict
    zónder modelaanroep of hertoetsing, nooit stil de nieuwste versie."""
    ai = FakeAI()
    hertoets = FakeBronbeoordeling("pass")
    service = _service(repo, ai, hertoets)
    did = repo.save(_definition(scenario="fail"))
    getoond = _record(repo, did).version_number

    # Iemand anders wijzigt de status (versie +1) na het tonen.
    from database.models import DefinitieStatus

    assert DefinitieRepository(repo.db_path).change_status(
        did, DefinitieStatus.REVIEW, "iemand-anders"
    )
    uit = _vraag(service, did, expected_version=getoond)
    assert uit["status"] == "version_conflict", uit
    assert ai.calls == 0
    assert _record(repo, did).get_source_proposals() == []

    # Met de actuele versie: aanvraag slaagt.
    actueel = _record(repo, did).version_number
    aanvraag = _vraag(service, did, expected_version=actueel)
    assert aanvraag["status"] == "proposed"
    pid = aanvraag["proposal_id"]
    # Getoonde versie is na de reservering opnieuw verouderd (status-wijziging).
    na_aanvraag = _record(repo, did).version_number
    assert DefinitieRepository(repo.db_path).change_status(
        did, DefinitieStatus.DRAFT, "iemand-anders"
    )
    toepassing = asyncio.run(
        service.pas_voorstel_toe(did, pid, actor=ACTOR, expected_version=na_aanvraag)
    )
    assert toepassing["status"] == "version_conflict", toepassing
    assert hertoets.calls == 0  # geen hertoetsing op een verouderde weergave
    assert _record(repo, did).get_definitie_tekst() == TEKST
    afwijzing = service.wijs_voorstel_af(
        did, pid, actor=ACTOR, expected_version=na_aanvraag
    )
    assert afwijzing["status"] == "version_conflict"
    assert _record(repo, did).get_source_proposal(pid)["status"] == "proposed"


def test_f3_gearchiveerd_of_vastgesteld_record_is_niet_bewerkbaar(repo):
    """F3: een intussen gearchiveerd/vastgesteld record weigert aanvraag én
    toepassen veilig (geen aanroep), ook als de UI nog een editor toonde."""
    from database.models import DefinitieStatus

    ai = FakeAI()
    hertoets = FakeBronbeoordeling("pass")
    service = _service(repo, ai, hertoets)
    did = repo.save(_definition(scenario="fail"))
    pid = _vraag(service, did)["proposal_id"]
    versie = _record(repo, did).version_number
    assert DefinitieRepository(repo.db_path).change_status(
        did, DefinitieStatus.ARCHIVED, "iemand-anders"
    )
    nieuw = _record(repo, did).version_number
    toepassing = asyncio.run(
        service.pas_voorstel_toe(did, pid, actor=ACTOR, expected_version=nieuw)
    )
    assert toepassing["status"] == "not_editable", toepassing
    assert hertoets.calls == 0
    assert versie != nieuw and _record(repo, did).get_definitie_tekst() == TEKST
    aanvraag = _vraag(service, did, expected_version=nieuw)
    assert aanvraag["status"] == "not_editable"
    assert ai.calls == 1


def test_f4_bestaande_verwijzing_en_naam_blijven_behouden(repo):
    """F4: een geldige bestaande inline verwijzing/naam in de zin mag blijven
    (geen afwijzing), maar mag niet worden weggehaald; alleen cosmetische
    toevoeging wordt geweigerd. De prompt zegt hetzelfde."""
    from services.source_proposal_service import bouw_voorstelprompt

    origineel = TEKST + " (artikel 1:1 Awb)"
    bronnen = [
        {"source_id": "rag:1", "title": "Awb artikel 1:1", "locator": "artikel 1:1 Awb"}
    ]
    basis = {
        "origineel": origineel,
        "begrip": BEGRIP,
        "contexten": CONTEXTEN,
        "bronnen": bronnen,
    }
    # Behouden verwijzing + inhoudelijke wijziging: toegestaan.
    assert (
        controleer_voorstel(
            kandidaat=TEKST
            + ", met uitzondering van de rechterlijke macht (artikel 1:1 Awb)",
            **basis,
        )
        is None
    )
    # Verwijzing/naam weggehaald: geweigerd (bekende betekenis niet strippen).
    afwijzing = controleer_voorstel(
        kandidaat=TEKST + ", met uitzondering van de rechterlijke macht", **basis
    )
    assert afwijzing and "verwijder" in afwijzing
    # Cosmetische toevoeging blijft geweigerd.
    assert "bronwoord" in controleer_voorstel(
        origineel=TEKST,
        kandidaat=TEKST + " (Awb artikel 1:1)",
        begrip=BEGRIP,
        contexten=CONTEXTEN,
        bronnen=bronnen,
    )
    _, systeem = bouw_voorstelprompt(
        begrip=BEGRIP,
        tekst=origineel,
        contexten=CONTEXTEN,
        bronnen=[],
        bevindingen=[],
        bewijs=[],
    )
    laag = systeem.lower()
    assert "behoud" in laag and "bestaande" in laag and "verwijzing" in laag
    assert "geen bronvermelding, citaat of contextnaam in de zin" not in laag


# ------------------------------------ vervolgreview: cache vs. correctie, lege claims


def _correctiepayload(repo, did, *, status: str, quote: str) -> dict[str, Any]:
    from domain.sources.normalisatie import canoniseer_bronnen

    awb = next(b for b in canoniseer_bronnen(BRONNEN) if b.source_id.startswith("rag:"))
    rec = _record(repo, did)
    return {
        "type": "part_correction",
        "accepted": True,
        "actor": ACTOR,
        "rationale": "Deskundig oordeel over de betekenissteun.",
        "version_number": rec.version_number,
        "fingerprint": basis_vingerafdruk(),
        "part_id": "semantic_support",
        "status": status,
        "evidence": [
            {
                "source_id": awb.source_id,
                "content_hash": awb.content_hash,
                "source_version": awb.version,
                "quote": quote,
                "locator": awb.locator,
            }
        ],
    }


def _sessieresultaat(scenario: str) -> dict[str, Any]:
    """Een bewaard editor-validatieresultaat (raw_v2) voor de opgeslagen tekst."""
    from domain.sources.contract import beoordeel_bronbasis

    beoordeling = bouw_beoordeling(
        BEGRIP, TEKST, CONTEXTEN, BRONNEN, scenario=scenario, peildatum="2026-09-15"
    )
    uitkomst = beoordeel_bronbasis(
        BEGRIP,
        TEKST,
        CONTEXTEN,
        BRONNEN,
        assessment=beoordeling,
        peildatum="2026-09-15",
    )
    return {
        "rule_results": {"CON-02": uitkomst.als_dict()},
        "source_assessment": beoordeling,
        "validation_status": "validated",
    }


def test_cache_oude_sessiefail_wordt_niet_boven_nieuwe_correctie_naar_pass_gesteld(
    repo,
):
    """Bevinding 2: de sessie bewaart een CON-02-fail; daarna corrigeert de
    deskundige `semantic_support` naar pass (recordversie +1). De aanvraag
    moet de correctie honoreren: geen reservering, geen modelaanroep."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))
    oud_sessieresultaat = _sessieresultaat("fail")
    rec = _record(repo, did)
    assert repo.set_source_review(
        did,
        _correctiepayload(repo, did, status="pass", quote=CITAAT),
        updated_by=ACTOR,
        expected_version=rec.version_number,
    )
    actueel = _record(repo, did)
    basis = service.bronbasis_van_record(actueel, oud_sessieresultaat)
    assert basis["con02"]["status"] == "pass", basis["con02"]["status"]
    assert basis["con02"]["review"]["applied_correction"]["status"] == "pass"
    assert (
        basis["con02"]["review"]["applied_correction"]["original"]["status"] == "fail"
    )
    uit = _vraag(
        service,
        did,
        huidig_resultaat=oud_sessieresultaat,
        expected_version=actueel.version_number,
    )
    assert (
        uit["status"] == "blocked"
        and uit["diagnose"]["cause"] == OORZAAK_GEEN_BEVINDING
    )
    assert ai.calls == 0
    assert _record(repo, did).get_source_proposals() == []


def test_cache_oude_sessiepass_onderdrukt_geen_nieuwe_correctie_naar_fail(repo):
    """Omgekeerd: sessie zegt pass, de deskundige corrigeert naar fail mét
    gebonden bewijs — een legitieme, actuele bevinding: voorstel mogelijk."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="pass"))
    oud_sessieresultaat = _sessieresultaat("pass")
    rec = _record(repo, did)
    assert repo.set_source_review(
        did,
        _correctiepayload(
            repo, did, status="fail", quote="met uitzondering van de rechterlijke macht"
        ),
        updated_by=ACTOR,
        expected_version=rec.version_number,
    )
    actueel = _record(repo, did)
    uit = _vraag(
        service,
        did,
        huidig_resultaat=oud_sessieresultaat,
        expected_version=actueel.version_number,
    )
    assert uit["status"] == "proposed", uit
    assert uit["diagnose"]["cause"] == OORZAAK_TEKORTKOMING
    assert ai.calls == 1
    # Het oude AI-oordeel blijft zichtbaar en historisch in de kernsamenvatting.
    basis = service.bronbasis_van_record(_record(repo, did), oud_sessieresultaat)
    assert (
        basis["con02"]["review"]["applied_correction"]["original"]["status"] == "pass"
    )


def test_sessiebeoordeling_wordt_alleen_hergebruikt_bij_exacte_binding(repo):
    """Als de opgeslagen beoordeling niet bindt (technisch mislukt), telt een
    sessiebeoordeling alleen bij exacte binding — en dan als invoer voor de
    replay tegen de ACTUELE review/versie, nooit als samengesteld verdict."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="error"))
    rec = _record(repo, did)
    sessie = _sessieresultaat("fail")
    basis = service.bronbasis_van_record(rec, sessie)
    assert basis["bron"] == "sessie" and basis["con02"]["status"] == "fail"
    assert basis["con02"]["review"]["assessment"]["applied"] is True
    # Een niet-gebonden sessiebeoordeling (vervalste vingerafdruk) telt niet,
    # ook al claimt het samengestelde sessieresultaat nog steeds "fail".
    vervalst = deepcopy(sessie)
    vervalst["source_assessment"]["fingerprint"] = "anders"
    basis2 = service.bronbasis_van_record(rec, vervalst)
    assert basis2["bron"] == "record" and basis2["con02"]["status"] == "error"


def test_lege_claims_bij_semantische_fail_rechtvaardigen_geen_voorstel(repo):
    """Bevinding 3: `semantic_support=fail` met geverifieerd citaat maar
    `claims=[]` benoemt geen concreet gebrek — stop vóór reservering."""
    from services.source_proposal_service import OORZAAK_GEEN_CLAIM

    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(
        _definition(
            scenario="fail",
            source_assessment=bouw_beoordeling(
                BEGRIP,
                TEKST,
                CONTEXTEN,
                BRONNEN,
                scenario="fail",
                peildatum="2026-09-15",
                claims=[],
            ),
        )
    )
    uit = _vraag(service, did)
    assert uit["status"] == "blocked", uit
    assert uit["diagnose"]["cause"] == OORZAAK_GEEN_CLAIM
    assert ai.calls == 0
    assert _record(repo, did).get_source_proposals() == []  # poging beschikbaar


@pytest.mark.parametrize(
    "claim",
    [
        {
            "aspect": "uitzondering",
            "text": "",
            "supported": False,
            "source_id": "rag:doc-awb:chunk-awb-1-1",
        },
        {
            "aspect": "",
            "text": "x",
            "supported": False,
            "source_id": "rag:doc-awb:chunk-awb-1-1",
        },
        {
            "aspect": "uitzondering",
            "text": "x",
            "supported": False,
            "source_id": "doc:upload-7",
        },
        {
            "aspect": "uitzondering",
            "text": "x",
            "supported": None,
            "source_id": "rag:doc-awb:chunk-awb-1-1",
        },
    ],
    ids=["lege tekst", "leeg aspect", "bron zonder bewijs", "niet negatief"],
)
def test_ongeldige_of_ongebonden_claim_rechtvaardigt_geen_voorstel(repo, claim):
    from services.source_proposal_service import OORZAAK_GEEN_CLAIM

    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(
        _definition(
            scenario="fail",
            source_assessment=bouw_beoordeling(
                BEGRIP,
                TEKST,
                CONTEXTEN,
                BRONNEN,
                scenario="fail",
                peildatum="2026-09-15",
                claims=[claim],
            ),
        )
    )
    uit = _vraag(service, did)
    assert uit["status"] == "blocked", uit
    assert uit["diagnose"]["cause"] == OORZAAK_GEEN_CLAIM
    assert ai.calls == 0


def test_geidentificeerde_negatieve_claim_met_bewijs_is_uitvoerbaar(repo):
    """Positieve controle: één negatieve claim (tekst/aspect, supported=false,
    bron met geverifieerd bewijs) ⇒ voorstel mogelijk, bevinding benoemd."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(_definition(scenario="fail"))
    uit = _vraag(service, did)
    assert uit["status"] == "proposed", uit
    assert any("niet gesteund (uitzondering)" in b for b in uit["diagnose"]["findings"])
    assert ai.calls == 1


# --------------------------- Codex-eindreview P2: tegenstrijdige claims

_AWB_ID = "rag:doc-awb:chunk-awb-1-1"
_CLAIM_TEKST = "met uitzondering van de rechterlijke macht"


def _claim(*, supported: bool | None, text: str = _CLAIM_TEKST) -> dict[str, Any]:
    return {
        "aspect": "uitzondering",
        "text": text,
        "supported": supported,
        "source_id": _AWB_ID,
    }


def _definitie_met_claims(claims: list[dict[str, Any]]):
    return _definition(
        scenario="fail",
        source_assessment=bouw_beoordeling(
            BEGRIP,
            TEKST,
            CONTEXTEN,
            BRONNEN,
            scenario="fail",
            peildatum="2026-09-15",
            claims=claims,
        ),
    )


def test_tegenstrijdige_claims_verbruiken_de_poging_niet(repo):
    """P2 (eindreview): dezelfde claim (tekst, aspect, bron) zowel `supported:
    true` als `false` is een intern tegenstrijdig evaluatoroordeel — geen
    geverifieerde tekortkoming. Blokkeer vóór reservering: geen voorstelrecord,
    geen modelaanroep, poging blijft beschikbaar."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(
        _definitie_met_claims([_claim(supported=True), _claim(supported=False)])
    )
    voor = _record(repo, did)
    uit = _vraag(service, did)
    assert uit["status"] == "blocked", uit
    assert uit["diagnose"]["cause"] == OORZAAK_AI_ONZEKER
    assert uit["proposal_id"] is None
    assert ai.calls == 0
    na = _record(repo, did)
    assert na.get_source_proposals() == []
    assert na.version_number == voor.version_number


def test_tegenstrijdigheid_telt_ongeacht_volgorde_en_witruimte(repo):
    """Het conflict wordt herkend ongeacht claimvolgorde en cosmetische
    verschillen in de tekst (witruimte/hoofdletters)."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(
        _definitie_met_claims(
            [
                _claim(supported=False),
                _claim(supported=True, text=f"  {_CLAIM_TEKST.upper()} "),
            ]
        )
    )
    uit = _vraag(service, did)
    assert uit["status"] == "blocked" and uit["diagnose"]["cause"] == OORZAAK_AI_ONZEKER
    assert ai.calls == 0 and _record(repo, did).get_source_proposals() == []


def test_consistente_negatieve_claim_naast_andere_positieve_claim_is_uitvoerbaar(
    repo,
):
    """Legitieme controle: een negatieve claim naast een positieve claim over
    een ándere tekst is consistent ⇒ voorstel mogelijk (één aanroep). Een
    dubbele, gelijkgerichte negatieve claim is evenmin een conflict."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(
        _definitie_met_claims(
            [
                _claim(supported=True, text="krachtens publiekrecht ingesteld"),
                _claim(supported=False),
                _claim(supported=False),
            ]
        )
    )
    uit = _vraag(service, did)
    assert uit["status"] == "proposed", uit
    assert uit["diagnose"]["cause"] == OORZAAK_TEKORTKOMING
    assert any("niet gesteund (uitzondering)" in b for b in uit["diagnose"]["findings"])
    assert ai.calls == 1


def test_deskundige_negatieve_correctie_blijft_los_van_claimconflict(repo):
    """Het afzonderlijke pad van een deskundige negatieve correctie met eigen
    gebonden bewijs blijft uitvoerbaar, ook als de AI-claims tegenstrijdig zijn."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(
        _definitie_met_claims([_claim(supported=True), _claim(supported=False)])
    )
    rec = _record(repo, did)
    assert repo.set_source_review(
        did,
        _correctiepayload(repo, did, status="fail", quote=_CLAIM_TEKST),
        updated_by=ACTOR,
        expected_version=rec.version_number,
    )
    actueel = _record(repo, did)
    uit = _vraag(service, did, expected_version=actueel.version_number)
    assert uit["status"] == "proposed", uit
    assert uit["diagnose"]["cause"] == OORZAAK_TEKORTKOMING
    assert ai.calls == 1


# ----------------- Codex-kwaliteitsreview P2: misvormd kwitantiekanaal


def _kwitantie(kanalen: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": "1",
        "status": "none",
        "sources": [],
        "omitted": [],
        "errors": [],
        "channels": kanalen,
    }


def _geldig_kanaal(geleverd: int = 0, gebruikt: int = 0) -> dict[str, Any]:
    return {"enabled": True, "supplied": geleverd, "used": gebruikt}


def test_misvormd_kwitantiekanaal_blokkeert_voor_reservering(repo):
    """P2 (kwaliteitsreview): een aanwezig maar misvormd kanaal (lijst i.p.v.
    dict) in de opgeslagen kwitantie mag niet als 'geen transportprobleem'
    doorgaan. Geldige fail + negatieve claim, toch: blocked vóór reservering,
    geen voorstelrecord, 0 modelaanroepen, versie ongewijzigd, expliciete
    diagnose."""
    from services.source_proposal_service import OORZAAK_KWITANTIE_ONGELDIG

    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(
        _definition(
            scenario="fail",
            source_receipt=_kwitantie({"rag": [{"supplied": 1, "used": 0}]}),
        )
    )
    voor = _record(repo, did)
    assert voor.get_contractvelden().get("source_receipt")  # D levert haar
    uit = _vraag(service, did)
    assert uit["status"] == "blocked", uit
    assert uit["diagnose"]["cause"] == OORZAAK_KWITANTIE_ONGELDIG
    assert uit["diagnose"]["proposal_possible"] is False
    assert any("rag" in b for b in uit["diagnose"]["findings"])
    assert uit["proposal_id"] is None
    assert ai.calls == 0
    na = _record(repo, did)
    assert na.get_source_proposals() == []
    assert na.version_number == voor.version_number


@pytest.mark.parametrize(
    "kanaal",
    [
        {"enabled": True, "supplied": True, "used": 0},
        {"enabled": True, "supplied": 1, "used": -1},
        {"enabled": True, "supplied": "1", "used": 0},
        {"enabled": True, "supplied": 1.0, "used": 0},
        {"enabled": True, "supplied": None, "used": 0},
        {"enabled": True, "used": 0},
        "rag",
    ],
    ids=[
        "bool",
        "negatief",
        "tekst",
        "float",
        "None",
        "ontbrekende telling",
        "kanaal geen dict",
    ],
)
def test_misvormde_kanaaltelling_wordt_niet_tot_nul_gedwongen(repo, kanaal):
    """bool/negatief/niet-geheel/ontbrekend telt niet stilzwijgend als 0:
    aanwezig-maar-onleesbaar ⇒ blocked, geen reservering, geen aanroep."""
    from services.source_proposal_service import OORZAAK_KWITANTIE_ONGELDIG

    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(
        _definition(
            scenario="fail",
            source_receipt=_kwitantie({"rag": kanaal, "web": _geldig_kanaal()}),
        )
    )
    uit = _vraag(service, did)
    assert uit["status"] == "blocked", uit
    assert uit["diagnose"]["cause"] == OORZAAK_KWITANTIE_ONGELDIG
    assert ai.calls == 0
    assert _record(repo, did).get_source_proposals() == []


def test_channels_zelf_misvormd_blokkeert_ook(repo):
    """`channels` aanwezig maar geen dict: even onleesbaar ⇒ blocked."""
    from services.source_proposal_service import OORZAAK_KWITANTIE_ONGELDIG

    ai = FakeAI()
    service = _service(repo, ai)
    kwitantie = _kwitantie({})
    kwitantie["channels"] = [{"rag": _geldig_kanaal()}]
    did = repo.save(_definition(scenario="fail", source_receipt=kwitantie))
    uit = _vraag(service, did)
    assert uit["status"] == "blocked" and uit["diagnose"]["cause"] == (
        OORZAAK_KWITANTIE_ONGELDIG
    )
    assert ai.calls == 0 and _record(repo, did).get_source_proposals() == []


def test_geldige_kwitantie_met_lege_kanalen_laat_voorstel_toe(repo):
    """Controle: een geldige kwitantie met lege kanalen (0/0, zoals E die
    schrijft) is geen transportprobleem — legitieme fail + negatieve claim ⇒
    proposed, precies één aanroep. Geldige tellingen blijven exact."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(
        _definition(
            scenario="fail",
            source_receipt=_kwitantie(
                {
                    "rag": _geldig_kanaal(),
                    "web": _geldig_kanaal(),
                    "document": _geldig_kanaal(),
                }
            ),
        )
    )
    uit = _vraag(service, did)
    assert uit["status"] == "proposed", uit
    assert uit["diagnose"]["cause"] == OORZAAK_TEKORTKOMING
    assert ai.calls == 1
    assert [v["status"] for v in _record(repo, did).get_source_proposals()] == [
        "proposed"
    ]


def test_geldige_kwitantie_met_werkelijk_gebruik_laat_voorstel_toe(repo):
    """Controle: geleverd én gebruikt (2/2) is geen transportverlies ⇒ proposed."""
    ai = FakeAI()
    service = _service(repo, ai)
    did = repo.save(
        _definition(
            scenario="fail",
            source_receipt=_kwitantie({"rag": _geldig_kanaal(2, 2)}),
        )
    )
    uit = _vraag(service, did)
    assert uit["status"] == "proposed", uit
    assert ai.calls == 1
