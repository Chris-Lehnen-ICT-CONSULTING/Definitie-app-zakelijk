"""DEF-768 — functioneel UI-bewijs ESS-05 met de échte Streamlit ``AppTest``.

Zelfde opzet als ``test_def743_sources_presentation.py``: de pytest-conftest
vervangt ``streamlit`` procesbreed door een mock, dus dit bestand start zichzelf
als subprocess-driver (``python <dit bestand> --driver <uitvoer.json>``) achter
``tests.offline_bootstrap`` en leest de waarnemingen terug.

Per toestand een eigen record in een tijdelijke SQLite-database (eigen context,
zodat records elkaars repository-buren niet zijn), een echte toetsing
(``ValidationOrchestratorV2`` + ``ModularValidationService`` + echte
burensamenstelling en ESS-05-contract/-aggregatie) en opslag via het echte
editor-opslagpad. Alleen het modeltransport is een fixture
(``FakeEss05Assessor``): dit is UI-bewijs, géén bewijs van modelkwaliteit.

Zes toestanden — Voldoet, Voldoet niet, Nog te beoordelen, Technische fout,
Niet uitgevoerd (geen context → 'Niet beoordeeld') en lege ruimte bevestigd —
elk op vijf echte renderpaden:

* ``gedeeld``   ``render_validation_detailed_list`` (de gedeelde weergave);
* ``generatie`` ``ValidationRenderer.render_validation_results`` (generatortab);
* ``editor``    de volledige ``DefinitionEditTab.render()`` met het resultaat
  van 'Valideren' in de sessie;
* ``expert``    ``ExpertReviewTab._render_definition_review()`` met het
  resultaat van 'Re-validate' in de sessie;
* ``heropend``  de volledige editor zónder sessieresultaat: ESS-05 uit het
  opgeslagen record (heropenen uit SQLite, replay zonder modelaanroep).

Waargenomen: alle tekst-, metric-, dataframe- en JSON-elementen in
documentvolgorde. Getoetst: geen ESS-05-cijfer, geen 0/1, geen totaalscore of
vervangende deelscore; reden, buur (term/herkomst/bevestiging), dragend citaat
of ontbrekend kenmerk en precies één open vraag waar van toepassing; een
technische fout of niet-uitgevoerde toets nooit als inhoudelijk besluit.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.slow]

REPO = Path(__file__).resolve().parents[3]
ACTOR = "Reviewer Rood"
BEGRIP = "lener"
TEKST = "Persoon met een actuele lening bij de instelling."
BUUR = {
    "term": "werknemer",
    "definitie": "Persoon met een arbeidsovereenkomst met de instelling.",
    "herkomst": "bron",
    "bevestigd": True,
}
LEGE_GROND = "Enig begrip in deze synthetische context."

#: toestand → (scenario van de fixture, context aanwezig, buur aanwezig)
TOESTANDEN: dict[str, tuple[str, bool, bool]] = {
    "voldoet": ("pass", True, True),
    "voldoet_niet": ("fail", True, True),
    "nog_te_beoordelen": ("open", True, True),
    "technische_fout": ("error", True, True),
    "niet_uitgevoerd": ("pass", False, True),
    "leeg_bevestigd": ("pass", True, False),
}
PADEN = ("gedeeld", "generatie", "editor", "expert", "heropend")

VERWACHT_LABEL = {
    "voldoet": "✅ Voldoet",
    "voldoet_niet": "❌ Voldoet niet",
    "nog_te_beoordelen": "🟠 Nog te beoordelen",
    "technische_fout": "⚙️ Technisch probleem",
    "niet_uitgevoerd": "⏸️ Niet beoordeeld",
    "leeg_bevestigd": "✅ Voldoet",
}

# ------------------------------------------------------------------ driver
#
# `AppTest.from_function` voert de functie als los script uit: modulevariabelen
# van dit bestand zijn daar niet zichtbaar. De procesbrede staat leeft daarom
# op de fixturemodule (één object in `sys.modules`).


def _toets(db: str, did: int, assessor) -> dict:
    """Zoals 'Valideren': echte wrapper, echte repository-buren, fixturetransport."""
    import asyncio

    from services.definition_edit_repository import DefinitionEditRepository
    from services.definition_edit_service import (
        bouw_validatiecontext,
        normaliseer_validatieresultaat,
    )
    from services.definition_repository import DefinitionRepository
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
    from services.validation.interfaces import ValidationContext
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from toetsregels.manager import get_toetsregel_manager

    geladen = DefinitionRepository(db).get(did)
    wrapper = ValidationOrchestratorV2(
        ModularValidationService(
            get_toetsregel_manager(), repository=DefinitionEditRepository(db)
        ),
        ess05_assessment_service=assessor,
        ess05_burenbron=DefinitionRepository(db),
    )
    ruw = asyncio.run(
        wrapper.validate_text(
            begrip=geladen.begrip,
            text=geladen.definitie,
            ontologische_categorie=geladen.categorie,
            context=ValidationContext(
                metadata=bouw_validatiecontext(geladen, dict(geladen.metadata))
            ),
        )
    )
    return normaliseer_validatieresultaat(ruw)


def _opzet() -> dict:
    """Eenmalig per driverproces: tmp-DB, zes records, toetsing en opslag."""
    import tempfile
    from datetime import UTC, datetime

    from domain.ess05.expertacties import bevestig_lege_ruimte
    from services.definition_edit_repository import DefinitionEditRepository
    from services.definition_edit_service import (
        DefinitionEditService,
        ess05_uitkomst_van_definition,
    )
    from services.definition_repository import DefinitionRepository
    from services.interfaces import Definition
    from tests.fixtures import def768_fakes
    from tests.fixtures.def768_fakes import BINDING, FakeEss05Assessor

    db = str(Path(tempfile.mkdtemp()) / "ess05-ui.db")
    repo = DefinitionEditRepository(db)
    service = DefinitionEditService(repository=repo, validation_service=None)
    gevallen: dict[str, dict] = {}
    for nr, (toestand, (scenario, met_context, met_buur)) in enumerate(
        TOESTANDEN.items()
    ):
        meta: dict = {"status": "draft", "created_by": "tester"}
        if met_buur:
            meta["ess05_buren"] = [dict(BUUR)]
        did = repo.save(
            Definition(
                begrip=BEGRIP,
                definitie=TEKST,
                categorie="type",
                organisatorische_context=(
                    [f"Synthetische Uitleendienst {nr}"] if met_context else []
                ),
                juridische_context=[],
                wettelijke_basis=[],
                gerelateerde_begrippen=[],
                metadata=meta,
            )
        )
        if toestand == "leeg_bevestigd":
            vingerafdruk = ess05_uitkomst_van_definition(
                DefinitionRepository(db).get(did), None, None
            )["fingerprint"]
            lege = bevestig_lege_ruimte(
                vingerafdruk,
                grond=LEGE_GROND,
                actor=ACTOR,
                at=datetime.now(UTC).isoformat(timespec="seconds"),
            )
            service.save_definition(
                did, {"ess05_lege_ruimte": lege}, user=ACTOR, validate=False
            )
        assessor = FakeEss05Assessor(scenario=scenario)
        resultaat = _toets(db, did, assessor)
        v2 = resultaat.get("raw_v2") or {}
        opslag = service.save_definition(
            did,
            {},
            user=ACTOR,
            reason="DEF-768 UI-bewijs: opslaan na toetsing",
            validate=False,
            ess05_assessment=v2.get("ess05_assessment"),
            ess05_actieve_buren=v2.get("ess05_actieve_buren"),
            ess05_binding=BINDING,
        )
        gevallen[toestand] = {
            "did": did,
            "resultaat": resultaat,
            "modelaanroepen": len(assessor.calls),
            "opslag": {
                k: opslag.get(k)
                for k in (
                    "success",
                    "ess05_assessment_persisted",
                    "ess05_assessment_reason",
                )
            },
        }
    staat = {"db": db, "gevallen": gevallen, "binding": BINDING, "actor": ACTOR}
    def768_fakes.APPTEST_STATE = staat  # type: ignore[attr-defined]
    return staat


def _app(toestand: str, pad: str) -> None:
    from copy import deepcopy

    import streamlit as st

    from database.definitie_repository import DefinitieRepository
    from services.definition_edit_repository import DefinitionEditRepository
    from services.null_repository import NullDefinitionRepository
    from services.orchestrators.validation_orchestrator_v2 import (
        ValidationOrchestratorV2,
    )
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from tests.fixtures import def768_fakes
    from tests.fixtures.def768_fakes import FakeEss05Assessor
    from toetsregels.manager import get_toetsregel_manager
    from ui import cached_services
    from ui.components.definition_edit_tab import DefinitionEditTab
    from ui.components.expert_review_tab import ExpertReviewTab
    from ui.components.validation_renderer import ValidationRenderer
    from ui.components.validation_view import render_validation_detailed_list
    from ui.session_state import SessionStateManager

    staat = def768_fakes.APPTEST_STATE  # type: ignore[attr-defined]
    geval = staat["gevallen"][toestand]
    did, resultaat = geval["did"], geval["resultaat"]
    v2 = resultaat.get("raw_v2") or {}

    # De actuele ESS-05-binding komt in de app uit de gecachte dienst; hier de
    # fixturedienst (zelfde binding als waarmee is getoetst). Geen netwerk.
    # Zoals de DEF-622-expertapp: een echte `ServiceContainer` op de tijdelijke
    # database; geen codepad mag de productiecontainer of -DB optuigen.
    if not getattr(cached_services, "_def768_ess05_ui", False):
        from database import definitie_repository as repo_module
        from services.container import ServiceContainer
        from utils import container_manager

        repo_module.get_definitie_repository(staat["db"])
        container = ServiceContainer(
            {
                "db_path": staat["db"],
                "enable_monitoring": False,
                "enable_ontology": False,
            }
        )

        class _Container:
            def __getattr__(self, naam: str):
                return getattr(container, naam)

            @staticmethod
            def ess05_assessment_service():
                return FakeEss05Assessor()

        omhulsel = _Container()
        container_manager.get_cached_container = lambda: omhulsel
        cached_services.get_cached_container = lambda: omhulsel
        cached_services.get_cached_service_container = lambda config=None: omhulsel
        cached_services._def768_ess05_ui = True  # type: ignore[attr-defined]

    SessionStateManager.set_value("user", staat["actor"])
    st.markdown(f"## DEF-768 UI-bewijs · {toestand} · {pad}")
    if pad == "gedeeld":
        render_validation_detailed_list(
            deepcopy(v2), key_prefix="gedeeld", show_toggle=False
        )
    elif pad == "generatie":
        ValidationRenderer().render_validation_results(deepcopy(v2))
    elif pad in ("editor", "heropend"):
        if SessionStateManager.get_value("def768_klaargezet") is None:
            SessionStateManager.set_value("def768_klaargezet", True)
            SessionStateManager.set_value("editing_definition_id", did)
            if pad == "editor":
                SessionStateManager.set_value(
                    "edit_last_validation",
                    {**deepcopy(resultaat), "editing_definition_id": did},
                )
        orchestrator = ValidationOrchestratorV2(
            ModularValidationService(
                toetsregel_manager=get_toetsregel_manager(),
                repository=NullDefinitionRepository(),
            ),
            ess05_assessment_service=FakeEss05Assessor(),
        )
        DefinitionEditTab(
            repository=DefinitionEditRepository(staat["db"]),
            validation_service=orchestrator,
        ).render()
    elif pad == "expert":
        facade = DefinitieRepository(staat["db"])
        if SessionStateManager.get_value("def768_klaargezet") is None:
            SessionStateManager.set_value("def768_klaargezet", True)
            SessionStateManager.set_value(
                "selected_review_definition", facade.get_definitie(did)
            )
            SessionStateManager.set_value(f"review_v2_validation_{did}", deepcopy(v2))
        ExpertReviewTab(facade)._render_definition_review()


def _leaf(node) -> dict:
    soort = type(node).__name__
    waarde = getattr(node, "value", None)
    item = {"type": soort, "waarde": None if waarde is None else str(waarde)}
    for attr in ("label", "key"):
        extra = getattr(node, attr, None)
        if isinstance(extra, str):
            item[attr] = extra
    if soort == "Metric":
        item["delta"] = str(getattr(node, "delta", None))
    return item


def _loop(node, uit: list[dict]) -> None:
    """Alle elementen in documentvolgorde (ook binnen expanders/kolommen)."""
    kinderen = getattr(node, "children", None)
    if isinstance(kinderen, dict):
        label = getattr(node, "label", None)
        if isinstance(label, str):
            uit.append({"type": type(node).__name__, "waarde": label, "label": label})
        for sleutel in sorted(kinderen):
            _loop(kinderen[sleutel], uit)
        return
    uit.append(_leaf(node))


def _waarneming(toestand: str, pad: str) -> dict:
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(
        _app, kwargs={"toestand": toestand, "pad": pad}, default_timeout=300
    )
    at.run()
    elementen: list[dict] = []
    _loop(at.main, elementen)
    return {
        "exceptions": [str(e.value) for e in at.exception],
        "elementen": elementen,
        "metrics": [{"label": m.label, "waarde": str(m.value)} for m in at.metric],
        "dataframes": [str(d.value) for d in at.dataframe],
        "json": [str(j.value) for j in at.json],
    }


def _driver(uit_pad: str) -> None:
    for pad in (str(REPO), str(REPO / "src")):
        if pad not in sys.path:
            sys.path.insert(0, pad)
    from tests import offline_bootstrap

    sessieroot = offline_bootstrap.install()
    staat = _opzet()
    waarnemingen: dict = {
        "gate_actief": offline_bootstrap.gate_is_actief(),
        "db_binnen_sessieroot": offline_bootstrap.pad_is_toegestaan(staat["db"]),
        "sessieroot": str(sessieroot),
        "bewijsgrens": (
            "UI-bewijs met fixturetransport (FakeEss05Assessor); geen modelkwaliteit"
        ),
        "gevallen": {
            t: {
                "did": g["did"],
                "modelaanroepen": g["modelaanroepen"],
                "opslag": g["opslag"],
                "ess05_status": (g["resultaat"].get("rule_statuses") or {}).get(
                    "ESS-05"
                ),
            }
            for t, g in staat["gevallen"].items()
        },
        "weergaven": {t: {p: _waarneming(t, p) for p in PADEN} for t in TOESTANDEN},
    }
    Path(uit_pad).parent.mkdir(parents=True, exist_ok=True)
    Path(uit_pad).write_text(
        json.dumps(waarnemingen, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ------------------------------------------------------------------ pytest


@pytest.fixture(scope="module")
def waarnemingen(tmp_path_factory) -> dict:
    uit = tmp_path_factory.mktemp("def768-ess05-apptest") / "waarnemingen.json"
    proces = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--driver", str(uit)],
        cwd=str(REPO),
        # Bewust de bestaande omgeving (zie DEF-622): de offline-gate en
        # dummykeys komen uit de bootstrap, niet van hier.
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    assert proces.returncode == 0, proces.stderr[-6000:]
    return json.loads(uit.read_text(encoding="utf-8"))


#: Begin van een andere regeluitkomst of -uitleg (kop of 'REGEL — …'-regel),
#: of van de dekkingsregel (tellingen, geen score): daar eindigt ESS-05.
_KOP = re.compile(
    r"^(?:\*\*)?(?!ESS-05\b)[A-Z]{2,5}(?:-[A-Z]+)*-\d{2,3}(?:\*\*)? [·—]"
    r"|^\*\*Beoordelingsdekking\*\*|^ℹ️ Toon uitleg"
)
_ESS05_KOP = "**ESS-05** · "
#: Een ESS-05-cijfer: een losse 0/1, een breuk x/1, een percentage of 'score'.
_CIJFER = re.compile(
    r"(?<![\w.,/-])[01](?:[.,]\d+)?(?![\w.,/-])|\b\d+\s*/\s*1\b|\d\s*%|(?i:\bscore\b)"
)


def _teksten(weergave: dict) -> list[str]:
    return [e["waarde"] or "" for e in weergave["elementen"]]


def _segmenten(weergave: dict) -> list[list[str]]:
    """Elke ESS-05-regeluitkomst: kop tot de volgende regelkop of sectie."""
    segmenten: list[list[str]] = []
    huidig: list[str] | None = None
    for e in weergave["elementen"]:
        tekst = e["waarde"] or ""
        if tekst.startswith(_ESS05_KOP):
            huidig = [tekst]
            segmenten.append(huidig)
        elif huidig is not None and (
            _KOP.match(tekst)
            or tekst.startswith(("#", "Herkomst: AI-beoordeling per verwant"))
            or e["type"] in ("Button", "TextInput", "TextArea", "Selectbox")
        ):
            huidig = None
        elif huidig is not None:
            huidig.append(tekst)
    return segmenten


def _alle(waarnemingen: dict):
    for toestand in TOESTANDEN:
        for pad in PADEN:
            yield toestand, pad, waarnemingen["weergaven"][toestand][pad]


def test_driver_offline_zonder_fouten_en_echte_opslag(waarnemingen):
    assert waarnemingen["gate_actief"] is True
    assert waarnemingen["db_binnen_sessieroot"] is True
    gevallen = waarnemingen["gevallen"]
    for toestand in ("voldoet", "voldoet_niet", "nog_te_beoordelen"):
        assert gevallen[toestand]["opslag"]["ess05_assessment_persisted"] is True
    # Zonder context en bij een bevestigde lege ruimte: geen modelaanroep.
    assert gevallen["niet_uitgevoerd"]["modelaanroepen"] == 0
    assert gevallen["leeg_bevestigd"]["modelaanroepen"] == 0
    for toestand, pad, weergave in _alle(waarnemingen):
        assert weergave["exceptions"] == [], (toestand, pad)


def _verwacht_label(toestand: str, pad: str) -> str:
    # Een technische fout wordt bewust niet opgeslagen (geen besluit om te
    # bewaren): heropend uit de database is ESS-05 dan 'niet beoordeeld' en
    # dus open — nooit Voldoet of Voldoet niet.
    if toestand == "technische_fout" and pad == "heropend":
        return "🟠 Nog te beoordelen"
    return VERWACHT_LABEL[toestand]


def _statuslijst(weergave: dict, label: str) -> list[str]:
    """Statuslijstregels ('Niet beoordeeld: …'); het icoon staat soms apart."""
    return [
        t for t in _teksten(weergave) if t.startswith((f"{label}: ", f"⏸️ {label}: "))
    ]


@pytest.mark.parametrize("pad", PADEN)
@pytest.mark.parametrize("toestand", list(TOESTANDEN))
def test_status_label_per_pad(waarnemingen, toestand, pad):
    weergave = waarnemingen["weergaven"][toestand][pad]
    segmenten = _segmenten(weergave)
    assert segmenten, (toestand, pad)
    for segment in segmenten:
        kop = segment[0]
        assert kop.startswith(f"{_ESS05_KOP}{_verwacht_label(toestand, pad)}"), kop
        assert kop.endswith("— zonder cijfer (uitkomst met motivering)")


def test_heropend_toont_opgeslagen_uitkomst(waarnemingen):
    """Heropenen uit SQLite: ESS-05 uit het record, in een eigen expander."""
    for toestand in TOESTANDEN:
        weergave = waarnemingen["weergaven"][toestand]["heropend"]
        assert any(
            "Onderscheid (ESS-05)" in (e.get("label") or "")
            for e in weergave["elementen"]
        ), toestand


def test_geen_ess05_cijfer_totaalscore_of_deelscore(waarnemingen):
    for toestand, pad, weergave in _alle(waarnemingen):
        for segment in _segmenten(weergave):
            tekst = "\n".join(segment).replace("ESS-05", "")
            assert not _CIJFER.search(tekst), (toestand, pad, _CIJFER.search(tekst))
        for regel in _teksten(weergave):
            if regel.startswith("**Totaalscore:**"):
                assert "niet beschikbaar" in regel, (toestand, pad, regel)
            assert "Totaalscore: 0" not in regel
        assert weergave["metrics"] == [], (toestand, pad, weergave["metrics"])
        for frame in weergave["dataframes"] + weergave["json"]:
            assert "ESS-05" not in frame, (toestand, pad)


#: De buur met herkomst en bevestiging, als label of in de per-buurregel.
_BUUR = re.compile(r"werknemer’? \(bron, bevestigd\)")
_VRAAG = re.compile(r"Wat onderscheidt[^?]*\?")


def test_reden_buur_en_citaat_of_kenmerk_zichtbaar(waarnemingen):
    for toestand, pad, weergave in _alle(waarnemingen):
        tekst = "\n".join("\n".join(s) for s in _segmenten(weergave))
        waar = (toestand, pad)
        if toestand == "voldoet":
            assert "ESS-05 — Voldoet: onderscheiden van alle bevestigde" in tekst, waar
            assert _BUUR.search(tekst), waar
            assert "aanleiding: '" in tekst, waar  # dragend citaat bij de buur
        elif toestand == "voldoet_niet":
            assert "ESS-05 — Voldoet niet:" in tekst, waar
            assert "ontbreekt" in tekst or "ontbrekend" in tekst, waar
            assert _BUUR.search(tekst), waar
        elif toestand == "nog_te_beoordelen":
            assert "ESS-05 — Open:" in tekst, waar
            assert _BUUR.search(tekst), waar
        elif toestand == "technische_fout" and pad != "heropend":
            assert "kon niet worden uitgevoerd" in tekst, waar
            assert "geen inhoudelijk oordeel" in tekst, waar
        elif toestand == "technische_fout":
            assert "niet beoordeeld" in tekst, waar
        elif toestand == "niet_uitgevoerd":
            assert "zonder context is niet te bepalen" in tekst, waar
        elif toestand == "leeg_bevestigd":
            assert LEGE_GROND in tekst, waar
            assert "deskundige bevestig" in tekst, waar
            assert "geen verwante begrippen" in tekst, waar


def test_precies_een_open_vraag_waar_van_toepassing(waarnemingen):
    """Eén open vraag: één unieke vraag (in reden en/of '❓ Vraag'-regel)."""
    for toestand, pad, weergave in _alle(waarnemingen):
        for segment in _segmenten(weergave):
            vragen = set(_VRAAG.findall("\n".join(segment)))
            vraagregels = [r for r in segment if r.startswith("_❓ Vraag:")]
            if toestand == "nog_te_beoordelen":
                assert len(vragen) == 1, (toestand, pad, vragen)
                assert len(vraagregels) <= 1, (toestand, pad, vraagregels)
            else:
                assert not vragen and not vraagregels, (toestand, pad, vragen)


def test_technisch_en_niet_uitgevoerd_nooit_als_inhoudelijk_besluit(waarnemingen):
    for toestand in ("technische_fout", "niet_uitgevoerd"):
        for pad in PADEN:
            weergave = waarnemingen["weergaven"][toestand][pad]
            segmenten = _segmenten(weergave)
            assert segmenten, (toestand, pad)
            for segment in segmenten:
                tekst = "\n".join(segment)
                assert "Voldoet" not in tekst, (toestand, pad, tekst[:300])
            # Geen success-element (groen oordeel) met een ESS-05-uitkomst.
            assert not any(
                e["type"] == "Success" and "ESS-05 —" in (e["waarde"] or "")
                for e in weergave["elementen"]
            ), (toestand, pad)


@pytest.mark.parametrize("pad", PADEN)
def test_niet_uitgevoerd_met_reden_zonder_modelcall_en_zonder_dubbeling(
    waarnemingen, pad
):
    """Zonder context: 'Niet beoordeeld' mét contractreden en vervolgstap in
    élk pad (gedeelde weergave, generatie, editor, expert, heropend), geen
    modelaanroep, geen oordeel, en ESS-05 niet nog eens kaal in de statuslijst."""
    assert waarnemingen["gevallen"]["niet_uitgevoerd"]["modelaanroepen"] == 0
    weergave = waarnemingen["weergaven"]["niet_uitgevoerd"][pad]
    segmenten = _segmenten(weergave)
    assert len(segmenten) >= 1, pad
    for segment in segmenten:
        tekst = "\n".join(segment)
        assert segment[0].startswith(f"{_ESS05_KOP}⏸️ Niet beoordeeld"), pad
        assert "zonder context is niet te bepalen" in tekst, pad
        assert "Vervolgstap" in tekst, pad
    for regel in _statuslijst(weergave, "Niet beoordeeld"):
        assert "ESS-05" not in regel, (pad, regel)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--driver":
        _driver(sys.argv[2])
    else:  # pragma: no cover - alleen als driver bedoeld
        raise SystemExit("gebruik: --driver <uitvoer.json>")
