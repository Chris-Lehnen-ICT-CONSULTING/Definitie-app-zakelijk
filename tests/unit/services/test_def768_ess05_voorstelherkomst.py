"""DEF-768 (reviewbevinding 2): een modelvoorstel blijft `herkomst=model`.

K-1 en het uitvoercontract: elk door het model voorgesteld verwant begrip is
`herkomst=model, bevestigd=false`, ook als het model er een bronverwijzing
(`source_id`) en een letterlijk citaat (`quote`) bij geeft. Die bronverwijzing
is afzonderlijke provenance en blijft end-to-end behouden: in het voorstel, bij
overnemen, in `ess05_buren` (opslaan en herladen, zonder schemawijziging) en in
de editor. Een echte bronbuur (herkomst `bron`, niet van het model) blijft
ongewijzigd geldig.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from domain.ess05 import expertacties
from domain.ess05.contract import (
    STATUS_OPEN,
    bronverwijzing,
    normaliseer_buren,
)
from services.definition_edit_repository import DefinitionEditRepository
from services.definition_repository import DefinitionRepository
from services.interfaces import Definition
from tests.unit.domain.test_def768_ess05_contract import (
    LENER,
    WERKNEMER,
    _beoordeel,
    _buur,
    _document,
    _nb,
    _oordeel,
)
from tests.unit.ui.test_def768_ess05_editor import (
    ORG,
    _mock_st,
    _tab,
    _teksten,
    _vul_editor,
)
from ui.session_state import SessionStateManager

pytestmark = [pytest.mark.unit]

AT = "2026-09-23T10:00:00+00:00"
BRONTEKST = "De lener en de borg tekenen samen de overeenkomst."
CITAAT = "de borg"


def _bron_id() -> tuple[list[dict[str, Any]], str]:
    from domain.ess05.contract import beoordelingsmateriaal

    bronnen = [{"source_id": "wet-1", "content": BRONTEKST}]
    materiaal = beoordelingsmateriaal("lener", LENER, bronnen, ())
    return bronnen, next(k for k in materiaal if k.startswith("source:"))[7:]


def _uitkomst_met_bronvoorstel():
    bronnen, bron_id = _bron_id()
    buren = [_buur("werknemer", WERKNEMER)]
    bid = normaliseer_buren(buren)[0].id
    doc = _document(
        "lener",
        LENER,
        buren,
        _oordeel(
            [_nb(bid, "distinguished", quote="met een actuele lening")],
            proposals=[
                {
                    "term": "borg",
                    "source_id": bron_id,
                    "quote": CITAAT,
                    "reason": "Genoemd in de bron.",
                }
            ],
        ),
        bronnen=bronnen,
    )
    return _beoordeel("lener", LENER, buren, doc, bronnen=bronnen), bron_id


class TestVoorstel:
    def test_voorstel_met_broncitaat_blijft_model_en_behoudt_de_verwijzing(self):
        uitkomst, bron_id = _uitkomst_met_bronvoorstel()
        assert uitkomst.status == STATUS_OPEN
        (voorstel,) = uitkomst.review["proposals"]
        assert voorstel["herkomst"] == "model"
        assert voorstel["bevestigd"] is False
        assert voorstel["id"].startswith("model:")
        assert (voorstel["source_id"], voorstel["quote"]) == (bron_id, CITAAT)
        assert bronverwijzing(voorstel) == {"source_id": bron_id, "quote": CITAAT}

    def test_voorstel_zonder_bron_heeft_geen_bronverwijzing(self):
        assert bronverwijzing({"source_id": None, "quote": None}) is None
        assert bronverwijzing({"source_id": "x", "quote": " "}) is None
        assert bronverwijzing({}) is None


class TestOvernemen:
    def test_overnemen_bewaart_model_onbevestigd_en_de_bronverwijzing(self):
        uitkomst, bron_id = _uitkomst_met_bronvoorstel()
        (voorstel,) = uitkomst.review["proposals"]
        lijst = expertacties.neem_voorstel_over([], voorstel, actor="d", at=AT)
        (buur,) = lijst
        assert (buur["herkomst"], buur["bevestigd"]) == ("model", False)
        assert (buur["source_id"], buur["quote"]) == (bron_id, CITAAT)
        # Een later besluit (bevestigen) laat de bronverwijzing staan.
        (bevestigd,) = expertacties.bevestig_buur(
            lijst, [], buur["id"], actor="d", at=AT
        )
        assert bevestigd["bevestigd"] is True
        assert (bevestigd["source_id"], bevestigd["quote"]) == (bron_id, CITAAT)
        assert bevestigd["herkomst"] == "model"

    def test_overnemen_zonder_bron_voegt_geen_lege_verwijzing_toe(self):
        (buur,) = expertacties.neem_voorstel_over(
            [],
            {"term": "borg", "herkomst": "model", "source_id": None, "quote": None},
            actor="d",
            at=AT,
        )
        assert "source_id" not in buur and "quote" not in buur

    def test_halve_bronverwijzing_wordt_geweigerd(self):
        with pytest.raises(ValueError, match="source_id en quote"):
            expertacties.neem_voorstel_over(
                [],
                {"term": "borg", "herkomst": "model", "source_id": "x", "quote": None},
                actor="d",
                at=AT,
            )

    def test_echte_bronbuur_blijft_bron(self):
        (buur,) = expertacties.neem_voorstel_over(
            [], {"term": "borg", "herkomst": "bron"}, actor="d", at=AT
        )
        assert buur["herkomst"] == "bron"
        assert normaliseer_buren([buur])[0].herkomst == "bron"


BRONBUUR = {
    "id": "model:borg",
    "term": "borg",
    "definitie": None,
    "herkomst": "model",
    "bevestigd": False,
    "source_id": "wet-1#p1",
    "quote": CITAAT,
    "actor": "deskundige",
    "at": AT,
}


def _record(**metadata: Any) -> Definition:
    return Definition(
        begrip="lener",
        definitie=LENER,
        categorie="type",
        organisatorische_context=list(ORG),
        juridische_context=[],
        wettelijke_basis=[],
        metadata={"status": "draft", "created_by": "tester", **metadata},
    )


class TestOpslag:
    def test_bronverwijzing_overleeft_opslaan_en_herladen(self, tmp_path):
        repo = DefinitionRepository(str(tmp_path / "herkomst.db"))
        did = repo.save(_record(ess05_buren=[dict(BRONBUUR)]))
        (terug,) = repo.get(did).metadata["ess05_buren"]
        assert terug == BRONBUUR

    @pytest.mark.parametrize(
        "halve",
        [{"quote": None}, {"source_id": None}, {"source_id": 3}],
        ids=["zonder-citaat", "zonder-bron", "bron-geen-tekst"],
    )
    def test_ongeldige_bronverwijzing_schrijft_niets(self, tmp_path, halve):
        from services.exceptions import RepositoryError

        repo = DefinitionRepository(str(tmp_path / "halve.db"))
        did = repo.save(_record())
        voor = repo.get_generation_prompt_data(did)
        geladen = repo.get(did)
        geladen.metadata["ess05_buren"] = [{**BRONBUUR, **halve}]
        with pytest.raises((RepositoryError, ValueError)):
            repo.save(geladen)
        assert repo.get_generation_prompt_data(did) == voor


class TestEditor:
    @pytest.fixture
    def opzet(self, tmp_path, monkeypatch):
        import streamlit as st

        monkeypatch.setattr(st, "session_state", {}, raising=False)
        repo = DefinitionEditRepository(str(tmp_path / "herkomst-ui.db"))
        did = repo.save(_record())
        return repo, did

    def test_overnemen_en_opslaan_bewaart_model_en_bronverwijzing(self, opzet):
        repo, did = opzet
        geladen = DefinitionRepository(repo.db_path).get(did)
        _vul_editor(did, geladen)
        SessionStateManager.set_value("user", "deskundige")
        tab = _tab(repo)
        uitkomst, bron_id = _uitkomst_met_bronvoorstel()
        (voorstel,) = uitkomst.review["proposals"]

        with patch("ui.components.definition_edit_tab.st", _mock_st()):
            fout = tab._pas_ess05_besluit_toe(geladen, "neem_over", voorstel=voorstel)
        assert fout is None
        (buur,) = SessionStateManager.get_value(f"edit_{did}_ess05_buren")
        assert (buur["herkomst"], buur["bevestigd"]) == ("model", False)
        assert (buur["source_id"], buur["quote"]) == (bron_id, CITAAT)

        with patch("ui.components.definition_edit_tab.st", _mock_st()):
            tab._save_definition()
        (terug,) = DefinitionRepository(repo.db_path).get(did).metadata["ess05_buren"]
        assert (terug["herkomst"], terug["bevestigd"]) == ("model", False)
        assert (terug["source_id"], terug["quote"]) == (bron_id, CITAAT)

    def test_editor_toont_model_als_herkomst_en_de_bron_apart(self, opzet):
        repo, did = opzet
        geladen = DefinitionRepository(repo.db_path).get(did)
        _vul_editor(did, geladen)
        SessionStateManager.set_value(f"edit_{did}_ess05_buren", [dict(BRONBUUR)])
        tab = _tab(repo)
        m = _mock_st()
        with (
            patch("ui.components.definition_edit_tab.st", m),
            patch("ui.components.validation_view.st", m),
        ):
            tab._render_ess05_section(geladen)
        teksten = _teksten(m)
        assert any("borg (model, onbevestigd)" in t for t in teksten), teksten
        assert not any("(bron," in t for t in teksten), teksten
        assert any("wet-1#p1" in t and CITAAT in t for t in teksten), teksten

    def test_voorstel_toont_de_bronverwijzing_bij_de_knop(self, opzet):
        repo, did = opzet
        tab = _tab(repo)
        uitkomst, bron_id = _uitkomst_met_bronvoorstel()
        m = _mock_st()
        with patch("ui.components.definition_edit_tab.st", m):
            tab._render_ess05_nieuwe_buren(
                _record(), did, (), {"review": uitkomst.review}
            )
        teksten = _teksten(m)
        assert any(bron_id in t and CITAAT in t for t in teksten), teksten
        knoppen = [str(c.args[0]) for c in m.button.call_args_list if c.args]
        assert any("‘borg’" in k and "model" in k for k in knoppen), knoppen
