"""DEF-771 ketenverificatie: INT-02 van invoer tot export, offline en synthetisch.

Route A per casus: synthetische invoer (tmp-SQLite) → herladen → echte validatie
(tweemaal, vergeleken) → renderer (opgevangen Streamlit-aanroepen) → berekende
issues-projectie → expertlezing → vaststelpreview → export (JSON; zonder gate
diagnostisch, met gate). Route B: de bestaande schrijfroute die een volledig
validatieresultaat bewaart (bronvoorsteltoepassing, DEF-743) met synthetische
AI-grenzen uit `tests/fixtures/def743_fakes.py`, daarna werkelijk teruglezen.
Geen productiedatabase, .env, netwerk of model. Exit 1 bij een afwijkende
transport-/rendereruitkomst, en ook als route B niet is uitgevoerd of de
teruggelezen registratie ontbreekt of afwijkt. Gebruik (app-root):
.venv/bin/python <dit script> <nieuw-uitvoerpad.json>
"""

import asyncio
import json
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

sys.path[:0] = ["src", "tests", "."]
import offline_bootstrap

offline_bootstrap.install()
from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from database.models import issues_uit_validatieresultaat
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_edit_service import DefinitionEditService
from services.definition_repository import DefinitionRepository
from services.definition_workflow_service import DefinitionWorkflowService
from services.export_service import ExportFormat, ExportService
from services.interfaces import Definition
from services.null_repository import NullDefinitionRepository
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2
from services.source_proposal_service import SourceProposalService
from services.validation.modular_validation_service import ModularValidationService
from services.workflow_service import WorkflowService
from tests.fixtures.def743_fakes import (
    BEGRIP,
    BRONNEN,
    TEKST,
    VOORSTEL_JSON,
    FakeAI,
    FakeBronbeoordeling,
    bouw_beoordeling,
)
from toetsregels.manager import get_toetsregel_manager
from ui.components import validation_view
from ui.components.expert_review_tab import ExpertReviewTab

NE = "INT-02 — Niet uitgevoerd: context ontbreekt. Er is geen inhoudelijk oordeel."
VERWACHT = {  # status, signalen, vaste tekst in reden/deel, UI-kanaal
    "C83": (
        "review_required",
        [r"\bnaar\s+eigen\s+inzicht\b", r"\bredelijk\s+acht\b"],
        "Beschrijft de passage 'passende maatregel: maatregel die de rechter naar eigen inzicht oplegt wanneer hij dat redelijk acht'",
        "ui_tekst",
    ),
    "C105": ("review_required", [], "Geen signaalwoord gevonden;", "ui_tekst"),
    "C56": ("not_evaluated", [], NE, "ui_waarschuwing"),
}

C50 = "Persoon die als stelselmatige dader geldt indien hij in de vijf jaar voorafgaand aan het laatste feit drie maal wegens een misdrijf onherroepelijk is veroordeeld."
CTX = '["Synthetische Organisatie"]'
CASUS = {  # register v5: C83 (RR, marker), C105 (RR, geen marker), C56 (NE)
    "C83": (
        "passende maatregel: maatregel die de rechter naar eigen inzicht oplegt wanneer hij dat redelijk acht",
        CTX,
    ),
    "C105": ("De medewerker laat de aanvrager toe.", CTX),
    "C56": (C50, "[]"),
}


def int02(v2):
    detail = (v2.get("rule_results") or {}).get("INT-02")
    item = next(
        (r for r in v2.get("review_required", []) if r["rule_id"] == "INT-02"), {}
    )
    return {
        "status": (v2.get("rule_statuses") or {}).get("INT-02"),
        "reden": item.get("reason"),
        "signalen": sorted(item.get("signals", [])),
        "deel": detail["parts"][0]["reason"] if detail else None,
    }


def controleer(naam, uitkomst, kanaal=None):
    """Afwijkingen van de verwachte INT-02-uitkomst (leeg = klopt)."""
    status, signalen, tekst, verwacht_kanaal = VERWACHT[naam]
    fouten = []
    if uitkomst["status"] != status or uitkomst["signalen"] != sorted(signalen):
        fouten.append(f"status/signalen {uitkomst['status']} {uitkomst['signalen']}")
    drager = uitkomst["reden"] if status == "review_required" else uitkomst["deel"]
    if (
        drager is None
        or tekst not in drager
        or (status != "review_required" and drager != NE)
    ):
        fouten.append(f"tekst ontbreekt of wijkt af: {drager!r}")
    if status != "review_required" and uitkomst["reden"] is not None:
        fouten.append("NE heeft toch een reviewvraag")
    if kanaal is not None and not kanaal.get(verwacht_kanaal):
        fouten.append(f"niet zichtbaar via {verwacht_kanaal}")
    return fouten


def ui(v2, sleutel):
    shown = {
        api: []
        for api in ("markdown", "info", "warning", "success", "error", "write", "text")
    }
    for api in shown:
        setattr(
            validation_view.st, api, lambda t, *a, _a=api, **k: shown[_a].append(str(t))
        )
    validation_view.st.button = lambda *a, **k: False
    validation_view.render_validation_detailed_list(v2, key_prefix=sleutel)
    return shown


async def casus(tmp, naam, tekst, ctx, orch):
    repo = DefinitionRepository(str(tmp / f"{naam}.db"))
    did = repo.legacy_repo.create_definitie(
        DefinitieRecord(
            begrip="proef",
            definitie=tekst,
            categorie="type",
            organisatorische_context=ctx,
            juridische_context="[]",
            wettelijke_basis="[]",
            status=DefinitieStatus.REVIEW.value,
        )
    )
    record = repo.get_definitie(did)
    v2 = await orch.validate_definition(repo.van_record(record))  # herladen + validatie
    uit = int02(v2)
    zichtbaar = uit["reden"] or uit["deel"]
    toon = ui(v2, f"keten_{naam}")
    uit["ui_tekst"] = zichtbaar in toon["text"]
    uit["ui_waarschuwing"] = any(zichtbaar in w for w in toon["warning"])
    uit["fouten"] = controleer(naam, uit, uit)
    # Berekende projectie; er wordt hier niets geschreven (zie route B).
    uit["issues_projectie_int02"] = [
        i for i in issues_uit_validatieresultaat(v2) if i["code"] == "INT-02"
    ]
    herladen = repo.get_definitie(did)
    uit["record_bevat_int02"] = "INT-02" in json.dumps(vars(herladen), default=str)
    uit["definition_metadata_bevat_int02"] = "INT-02" in json.dumps(
        repo.get(did).metadata, default=str
    )
    opgeslagen_v2 = ExpertReviewTab._v2_uit_opgeslagen_validatie(herladen)
    uit["experttab_zonder_hervalidatie"] = (
        None if opgeslagen_v2 is None else int02(opgeslagen_v2)
    )
    tweede = int02(await orch.validate_definition(repo.van_record(herladen)))
    uit["tweede_validatie"] = tweede
    eerste = {k: uit[k] for k in tweede}
    uit["fouten"] += controleer(naam, tweede) + (
        [] if tweede == eerste else ["tweede validatie wijkt af"]
    )
    gate = DefinitionWorkflowService(WorkflowService(), repo).preview_gate(did)
    uit["vaststelpoort"] = gate
    uit["vaststelpoort_noemt_int02"] = "INT-02" in json.dumps(gate)
    gezien = []

    class Spy:
        async def validate_text(self, **kw):
            gezien.append(await orch.validate_text(**kw))
            return gezien[-1]

    for poort in (False, True):
        svc = ExportService(
            repository=repo.legacy_repo,
            export_dir=str(tmp / f"exp_{naam}_{poort}"),
            validation_orchestrator=Spy(),
            enable_validation_gate=poort,
        )
        try:
            pad = await svc.export_definitie_async(
                definitie_record=herladen, format=ExportFormat.JSON
            )
            uit[f"export_gate_{poort}"] = {
                "bevat_int02": "INT-02" in Path(pad).read_text("utf-8")
            }
        except ValueError as e:
            uit[f"export_gate_{poort}"] = {"fout": str(e)}
    if gezien:
        uit["exportgate_int02"] = int02(gezien[-1])
        uit["fouten"] += controleer(naam, uit["exportgate_int02"])
        uit["exportgate_acceptance_noemt_int02"] = "INT-02" in json.dumps(
            gezien[-1].get("acceptance_gate")
        )
    return uit


async def schrijfroute(tmp, naam, tekst, ctx):
    """Route B: bronvoorsteltoepassing bewaart het volledige resultaat van de kandidaat."""
    ctxs = {
        "organisatorische_context": json.loads(ctx),
        "juridische_context": [],
        "wettelijke_basis": [],
    }
    meta = {
        "status": "draft",
        "created_by": "generator",
        "sources": deepcopy(BRONNEN),
        "provenance_sources": deepcopy(BRONNEN),
        "peildatum": "2026-09-15",
        "source_assessment": bouw_beoordeling(
            BEGRIP, TEKST, ctxs, BRONNEN, scenario="fail", peildatum="2026-09-15"
        ),
        "definitie_origineel": TEKST,
        "definitie_eindtekst": TEKST,
    }
    repo = DefinitionEditRepository(str(tmp / f"b_{naam}.db"))
    did = repo.save(
        Definition(
            begrip=BEGRIP, definitie=TEKST, categorie="type", metadata=meta, **ctxs
        )
    )
    orch = ValidationOrchestratorV2(
        ModularValidationService(
            toetsregel_manager=get_toetsregel_manager(),
            repository=NullDefinitionRepository(),
        ),
        source_assessment_service=FakeBronbeoordeling("pass"),
    )
    ai = FakeAI(dict(VOORSTEL_JSON, voorstel=tekst, behouden=[]))
    service = DefinitionEditService(
        repository=repo,
        validation_service=orch,
        proposal_service=SourceProposalService(ai),
    )
    vraag = await service.vraag_verbetervoorstel(did, actor="synthetisch")
    uit = {"voorstel": {k: vraag.get(k) for k in ("status", "message", "error")}}
    if vraag.get("status") != "proposed":
        return uit | {"uitgevoerd": False}
    toegepast = await service.pas_voorstel_toe(
        did, vraag["proposal_id"], actor="synthetisch"
    )
    uit["toepassing"] = {k: toegepast.get(k) for k in ("status", "message")}
    if toegepast.get("status") != "applied":
        return uit | {"uitgevoerd": False}
    vers = int02(toegepast["validation"])
    rec = DefinitieRepository(repo.db_path).get_definitie(did)  # werkelijk teruglezen
    bewaard = (rec.get_source_proposals()[-1].get("applied") or {}).get("validation")
    expert = ExpertReviewTab._v2_uit_opgeslagen_validatie(rec)
    uit |= {
        "uitgevoerd": True,
        "vers": vers,
        "registratie_teruggelezen": None if bewaard is None else int02(bewaard),
        "expertlezing": None if expert is None else int02(expert),
    }
    uit["fouten"] = route_b_fouten(naam, uit)
    for sleutel, extra in (
        ("export_record_zonder_gate", None),
        (
            "export_met_toetsresultaten_zonder_gate",
            {"toetsresultaten": toegepast["validation"]},
        ),
    ):
        svc = ExportService(
            repository=DefinitieRepository(repo.db_path),
            export_dir=str(tmp / f"b_{naam}_{sleutel}"),
        )
        pad = await svc.export_definitie_async(
            definitie_record=rec, additional_data=extra, format=ExportFormat.JSON
        )
        uit[sleutel] = {"bevat_int02": "INT-02" in Path(pad).read_text("utf-8")}
    return uit


VELDEN = ("status", "reden", "signalen", "deel")


def route_b_fouten(naam, b):
    """Route B: niet uitgevoerd of ontbrekende/afwijkende teruggelezen registratie = fout."""
    if not b.get("uitgevoerd"):
        return ["route B niet uitgevoerd"]
    fouten = controleer(naam, b["vers"])
    terug = b.get("registratie_teruggelezen")
    if terug is None:
        return [*fouten, "teruggelezen registratie ontbreekt"]
    fouten += [f"teruggelezen: {f}" for f in controleer(naam, terug)]
    if any(terug.get(k) != b["vers"].get(k) for k in VELDEN):
        fouten.append("teruggelezen registratie wijkt af van de verse uitkomst")
    return fouten


def eindstatus(uit):
    """1 zodra route A of route B van een casus een fout heeft."""
    return int(
        any(
            u["route_a"]["fouten"] or route_b_fouten(n, u["route_b"])
            for n, u in uit.items()
        )
    )


async def main(doel):
    orch = ValidationOrchestratorV2(
        ModularValidationService(
            toetsregel_manager=get_toetsregel_manager(),
            repository=NullDefinitionRepository(),
        )
    )
    with tempfile.TemporaryDirectory() as t:
        uit = {
            n: {
                "route_a": await casus(Path(t), n, tekst, ctx, orch),
                "route_b": await schrijfroute(Path(t), n, tekst, ctx),
            }
            for n, (tekst, ctx) in CASUS.items()
        }
    uit["exitstatus"] = eindstatus(uit)
    doel.write_text(
        json.dumps(uit, ensure_ascii=False, indent=2, default=str) + "\n", "utf-8"
    )
    print(json.dumps(uit, ensure_ascii=False, indent=1, default=str))
    return uit["exitstatus"]


if __name__ == "__main__":
    doel = Path(sys.argv[1])
    if doel.exists():
        sys.exit(f"weiger overschrijven: {doel}")
    sys.exit(asyncio.run(main(doel)))
