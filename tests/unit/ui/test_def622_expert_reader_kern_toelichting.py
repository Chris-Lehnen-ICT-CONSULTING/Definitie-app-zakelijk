"""DEF-622 vervolgcriteria — kern en toelichting bij de legacy expertreader.

CON-GT-007 / CW-GEN-11: de servicelaag bedt een toelichting in de kolom
`definitie` in (`<zin>\\n\\nToelichting: …`). De domeinreader splitst dat
(K4); de legacy expertconstructor (`DefinitieRecord` → `ExpertReviewTab`)
toonde en bewerkte de samengevoegde tekst. Nu:

* details tonen de definitiezin en de toelichting afzonderlijk;
* de bewerkweergave bewerkt uitsluitend de zin; bij opslaan blijft de
  toelichting afzonderlijk behouden (opnieuw ingebed via dezelfde conventie);
* de tekstvergelijking (besluit Chris) verschijnt ook bij een opnieuw geopend
  record — alleen met echt bewijs en alleen zolang de zin de
  generatie-eindtekst is; historisch/stale: geen melding.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from database.models import TOELICHTING_SCHEIDING
from ui.components.expert_review_tab import ExpertReviewTab
from ui.components.tekstwijziging import MELDING_TEKST_AANGEPAST
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

ZIN = "Kwaliteitskeurmerk dat uitsluitend door Stichting Zilver wordt verleend."
TOELICHTING = "Stichting Goud verleent een ander merk."
KERN_RUW = "kwaliteitskeurmerk dat uitsluitend door Stichting Zilver wordt verleend"


@pytest.fixture
def repo(tmp_path) -> DefinitieRepository:
    return DefinitieRepository(str(tmp_path / "expert-reader.db"))


@pytest.fixture
def sessie(monkeypatch):
    monkeypatch.setattr(st, "session_state", {}, raising=False)
    SessionStateManager.set_value("user", "synthetische-expert")
    return st.session_state


def _record(
    repo: DefinitieRepository, *, definitie: str, bewijs: dict[str, Any] | None = None
) -> DefinitieRecord:
    rec = DefinitieRecord(
        begrip="Zilverkeurmerk",
        definitie=definitie,
        categorie="type",
        organisatorische_context='["Stichting Zilver"]',
        status=DefinitieStatus.REVIEW.value,
        validation_score=0.9,
    )
    if bewijs is not None:
        rec.generation_prompt_data = json.dumps(bewijs, ensure_ascii=False)
    did = repo.create_definitie(rec)
    gelezen = repo.get_definitie(did)
    assert gelezen is not None
    return gelezen


def _mock_st() -> MagicMock:
    m = MagicMock()
    m.columns.side_effect = lambda spec: [
        MagicMock() for _ in range(len(spec) if isinstance(spec, list) else spec)
    ]
    m.expander.return_value.__enter__ = lambda s: s
    m.expander.return_value.__exit__ = lambda s, *a: False
    return m


def _details(repo: DefinitieRepository, rec: DefinitieRecord) -> MagicMock:
    """Render de echte detailsweergave met één mock-`st` voor tab én
    renderer; het gedeelde voorbeeldenblok is geen onderdeel van deze proef."""
    m = _mock_st()
    with (
        patch("ui.components.expert_review_tab.st", m),
        patch("ui.components.tekstwijziging.st", m),
        patch("ui.components.examples_block.render_examples_block", MagicMock()),
    ):
        ExpertReviewTab(repo)._render_definition_details(rec)
    return m


def _teksten(m: MagicMock) -> list[str]:
    uit: list[str] = []
    for api in ("markdown", "info", "text", "caption", "warning", "write", "success"):
        uit.extend(str(c.args[0]) for c in getattr(m, api).call_args_list if c.args)
    return uit


def test_details_tonen_zin_en_toelichting_afzonderlijk(repo, sessie):
    rec = _record(repo, definitie=f"{ZIN}{TOELICHTING_SCHEIDING} {TOELICHTING}")
    m = _details(repo, rec)

    teksten = _teksten(m)
    assert ZIN in teksten, teksten
    assert TOELICHTING in teksten, teksten
    # Nooit de samengevoegde kolomtekst als 'de definitie'.
    assert all(TOELICHTING_SCHEIDING not in t for t in teksten)


def test_bewerkweergave_bewerkt_alleen_de_zin(repo, sessie):
    rec = _record(repo, definitie=f"{ZIN}{TOELICHTING_SCHEIDING} {TOELICHTING}")
    m = _mock_st()
    # Elk tekstveld geeft (zoals Streamlit) zijn eigen, ongewijzigde waarde terug.
    m.text_area.side_effect = lambda _label, **kw: SessionStateManager.get_value(
        kw["key"], ""
    )
    with patch("ui.components.expert_review_tab.st", m):
        ExpertReviewTab(repo)._render_comparison_view(rec)

    assert SessionStateManager.get_value(f"edit_def_{rec.id}") == ZIN
    # Ongewijzigd: geen 'aangepast'-markering en geen bewerkte versie; de
    # toelichting staat in een eigen veld (reviewbevinding 3), niet in de zin.
    assert SessionStateManager.get_value(f"edited_definition_{rec.id}") is None
    assert SessionStateManager.get_value(f"edited_toelichting_{rec.id}") is None
    teksten = _teksten(m)
    assert ZIN in teksten and all(TOELICHTING_SCHEIDING not in t for t in teksten)


def test_opslaan_van_bewerkte_zin_behoudt_de_toelichting(repo, sessie):
    rec = _record(repo, definitie=f"{ZIN}{TOELICHTING_SCHEIDING} {TOELICHTING}")
    nieuwe_zin = "Kwaliteitskeurmerk dat door Stichting Zilver wordt verleend."
    SessionStateManager.set_value(f"edited_definition_{rec.id}", nieuwe_zin)
    m = _mock_st()
    with patch("ui.components.expert_review_tab.st", m):
        ExpertReviewTab(repo)._submit_review(
            rec, "📝 Wijzigingen Vereist", "", "synthetische-expert"
        )

    na = repo.get_definitie(rec.id)
    assert na.get_definitie_tekst() == nieuwe_zin
    assert na.definitie == f"{nieuwe_zin}{TOELICHTING_SCHEIDING} {TOELICHTING}"


def test_tekstvergelijking_bij_opnieuw_geopend_record_met_bewijs(repo, sessie):
    rec = _record(
        repo,
        definitie=ZIN,
        bewijs={
            "prompt": "…",
            "definitie_kern_geextraheerd": KERN_RUW,
            "definitie_eindtekst": ZIN,
            "tekst_na_generatie_aangepast": True,
        },
    )
    m = _details(repo, rec)

    m.warning.assert_any_call(MELDING_TEKST_AANGEPAST)
    letterlijk = "\n".join(str(c.args[0]) for c in m.text.call_args_list)
    assert KERN_RUW in letterlijk and ZIN in letterlijk


@pytest.mark.parametrize(
    ("definitie", "bewijs"),
    [
        (ZIN, None),
        (ZIN, {"prompt": "…"}),
        (
            ZIN,
            {
                "definitie_kern_geextraheerd": ZIN,
                "definitie_eindtekst": ZIN,
                "tekst_na_generatie_aangepast": False,
            },
        ),
        (
            "Door de expert herschreven zin.",
            {
                "definitie_kern_geextraheerd": KERN_RUW,
                "definitie_eindtekst": ZIN,
                "tekst_na_generatie_aangepast": True,
            },
        ),
    ],
    ids=["historisch-geen-bewijs", "historisch-alleen-prompt", "ongewijzigd", "stale"],
)
def test_geen_melding_zonder_bewijs_ongewijzigd_of_stale(
    repo, sessie, definitie, bewijs
):
    rec = _record(repo, definitie=definitie, bewijs=bewijs)
    m = _details(repo, rec)

    assert all(
        MELDING_TEKST_AANGEPAST not in str(c.args[0])
        for c in m.warning.call_args_list
        if c.args
    )
