"""DEF-770 (INT-01): de beperkte dekking reist consistent door de keten.

Eén vastgestelde zin is een deelbevinding: compactheid en begrijpelijkheid
zijn niet beoordeeld. Die beperkte claim moet overal hetzelfde blijven —
service-uitkomst, UI-weergave, opgeslagen oordeel, herladen en export — en
nergens mag een groen, volledig INT-01-oordeel ontstaan. Een tweede zin blijft
overal zichtbaar met passage en reden.

Bewijsgrens: echte validatieservice en orchestrator, echte SQLite in een
tijdelijke map, echte exportservice en de gedeelde UI-renderer met een
gemockte Streamlit-laag. Geen modelaanroep, geen browser.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from database.models import issues_uit_validatieresultaat
from services.data_aggregation_service import DataAggregationService
from services.definition_edit_service import normaliseer_validatieresultaat
from services.definition_repository import DefinitionRepository
from services.export_service import ExportFormat, ExportLevel, ExportService
from services.interfaces import Definition
from services.orchestrators.validation_orchestrator_v2 import ValidationOrchestratorV2

pytestmark = [pytest.mark.unit]

EEN_ZIN = (
    "eis die een organisatie moet ondersteunen om migratie van de huidige naar "
    "de toekomstige situatie mogelijk te maken."
)
TWEE_ZINNEN = "Afgebakend object. Heeft vaste vorm."
TOELICHTING = "Het wordt geregistreerd. Zie ook het beleidskader."


def _orchestrator() -> ValidationOrchestratorV2:
    from services.null_repository import NullDefinitionRepository
    from services.validation.modular_validation_service import (
        ModularValidationService,
    )
    from toetsregels.manager import get_toetsregel_manager

    return ValidationOrchestratorV2(
        ModularValidationService(
            toetsregel_manager=get_toetsregel_manager(),
            repository=NullDefinitionRepository(),
        )
    )


def _definition(tekst: str) -> Definition:
    return Definition(
        begrip="transitie-eis",
        definitie=tekst,
        toelichting=TOELICHTING,
        categorie="type",
        organisatorische_context=["Stichting Zilver"],
        juridische_context=["bestuursrecht"],
        wettelijke_basis=["Awb"],
        metadata={"status": "draft", "created_by": "synthetisch"},
    )


def _int01_issues(issues: list[dict]) -> list[dict]:
    return [i for i in issues if (i.get("rule_id") or i.get("code")) == "INT-01"]


class TestHerladen:
    """Opslaan met ingebedde toelichting, herladen, opnieuw toetsen."""

    @pytest.mark.asyncio
    async def test_toelichting_telt_niet_mee_en_uitkomst_is_stabiel(self, tmp_path):
        repo = DefinitionRepository(str(tmp_path / "keten.db"))
        did = repo.save(_definition(EEN_ZIN))
        record = repo.get_definitie(did)
        # De kolom draagt de toelichting (met een eigen tweede zin) ingebed.
        assert "Toelichting:" in (record.definitie or "")

        herladen = repo.get(did)
        assert herladen.definitie == EEN_ZIN
        orchestrator = _orchestrator()
        via_definitie = await orchestrator.validate_definition(herladen)
        via_tekst = await orchestrator.validate_text(
            begrip=herladen.begrip, text=herladen.definitie
        )
        for resultaat in (via_definitie, via_tekst):
            assert resultaat["rule_statuses"]["INT-01"] == "review_required"
            delen = {
                p["id"]: p["status"]
                for p in resultaat["rule_results"]["INT-01"]["parts"]
            }
            assert delen == {
                "zinsstructuur": "pass",
                "compactheid": "review_required",
                "begrijpelijkheid": "review_required",
            }
            assert "INT-01" not in resultaat["passed_rules"]

        # De editor-normalisatie (herladen in de bewerk-tab) bewaart de
        # deeluitkomst en de open status; er ontstaat geen groene regel.
        ui = normaliseer_validatieresultaat(via_tekst)
        assert ui["rule_statuses"]["INT-01"] == "review_required"
        assert ui["rule_results"]["INT-01"]["parts"][0]["id"] == "zinsstructuur"
        assert not [i for i in ui["issues"] if i["rule"] == "INT-01"]

    @pytest.mark.asyncio
    async def test_tweede_zin_blijft_na_herladen_zichtbaar(self, tmp_path):
        repo = DefinitionRepository(str(tmp_path / "keten.db"))
        did = repo.save(_definition(TWEE_ZINNEN))
        resultaat = await _orchestrator().validate_definition(repo.get(did))
        assert resultaat["rule_statuses"]["INT-01"] == "fail"
        ui = normaliseer_validatieresultaat(resultaat)
        (issue,) = [i for i in ui["issues"] if i["rule"] == "INT-01"]
        assert "object. Heeft" in issue["message"]


class TestOpslagEnExport:
    """Het opgeslagen oordeel (`validation_issues`) en de export."""

    async def _opgeslagen(self, tmp_path: Path, tekst: str) -> tuple[Path, int]:
        resultaat = await _orchestrator().validate_text(
            begrip="transitie-eis", text=tekst
        )
        record = DefinitieRecord(
            begrip="transitie-eis",
            definitie=tekst,
            categorie="type",
            organisatorische_context='["Stichting Zilver"]',
            juridische_context="[]",
            wettelijke_basis="[]",
            status=DefinitieStatus.DRAFT.value,
        )
        record.set_validation_issues(issues_uit_validatieresultaat(resultaat))
        pad = tmp_path / "export.db"
        did = DefinitieRepository(str(pad)).create_definitie(record)
        return pad, did

    def _export(self, pad: Path, tmp_path: Path, did: int, formaat: ExportFormat):
        repo = DefinitieRepository(str(pad))
        service = ExportService(
            repository=repo,
            data_aggregation_service=DataAggregationService(repo),
            export_dir=str(tmp_path / "exports"),
        )
        return service.export_multiple_definitions(
            [repo.get_definitie(did)], format=formaat, level=ExportLevel.UITGEBREID
        )

    @pytest.mark.asyncio
    async def test_tweede_zin_opgeslagen_en_geexporteerd_met_passage(self, tmp_path):
        pad, did = await self._opgeslagen(tmp_path, TWEE_ZINNEN)
        teruggelezen = DefinitieRepository(str(pad)).get_definitie(did)
        (issue,) = _int01_issues(teruggelezen.get_validation_issues_list())
        assert issue["severity"] == "warning"
        assert "object. Heeft" in issue["description"]
        assert "Compactheid en begrijpelijkheid" in issue["description"]

        json_pad = self._export(pad, tmp_path, did, ExportFormat.JSON).path
        [rij] = json.loads(Path(json_pad).read_text(encoding="utf-8"))["definities"]
        assert "object. Heeft" in json.dumps(rij, ensure_ascii=False)

        csv_pad = self._export(pad, tmp_path, did, ExportFormat.CSV).path
        with open(csv_pad, newline="", encoding="utf-8") as f:
            [csv_rij] = list(csv.DictReader(f))
        assert "object. Heeft" in csv_rij["validation_issues"]

    @pytest.mark.asyncio
    async def test_een_zin_wordt_als_open_deeluitkomst_opgeslagen(self, tmp_path):
        pad, did = await self._opgeslagen(tmp_path, EEN_ZIN)
        teruggelezen = DefinitieRepository(str(pad)).get_definitie(did)
        # Geen violation (er is geen tekortkoming vastgesteld) ...
        assert not _int01_issues(teruggelezen.get_validation_issues_list())
        # ... maar ook geen stilte: de open deeluitkomst reist mee.
        json_pad = self._export(pad, tmp_path, did, ExportFormat.JSON).path
        [rij] = json.loads(Path(json_pad).read_text(encoding="utf-8"))["definities"]
        int01 = rij["int01_beoordeling"]
        assert int01["status"] == "review_required" and int01["applied"] is True
        assert {d["id"]: d["status"] for d in int01["parts"]} == {
            "zinsstructuur": "pass",
            "compactheid": "review_required",
            "begrijpelijkheid": "review_required",
        }
        assert '"status": "pass"' not in json.dumps(
            {k: v for k, v in int01.items() if k != "parts"}
        )


def _render(resultaat: dict) -> MagicMock:
    from ui.components import validation_view

    with patch.object(validation_view, "st") as mock_st:
        mock_st.button.return_value = False
        validation_view.render_validation_detailed_list(
            resultaat, key_prefix="def770", show_toggle=False
        )
    return mock_st


def _teksten(mock: MagicMock) -> list[str]:
    return [str(c.args[0]) for c in mock.call_args_list if c.args]


class TestUIWeergave:
    @pytest.mark.asyncio
    async def test_een_zin_toont_deelbevinding_en_open_onderdeel(self):
        resultaat = await _orchestrator().validate_text(
            begrip="transitie-eis", text=EEN_ZIN
        )
        mock_st = _render(resultaat)
        koppen = [t for t in _teksten(mock_st.markdown) if t.startswith("**INT-01**")]
        assert koppen and "Nog te beoordelen" in koppen[0]
        groen = _teksten(mock_st.success)
        assert any("Eén definitieformulering vastgesteld" in t for t in groen)
        # Geen groene regelregel voor INT-01 als geheel.
        assert not [t for t in groen if t.startswith("✅ INT-01")]
        # Compactheid en begrijpelijkheid zijn twee aparte open onderdelen,
        # elk met een eigen reden.
        open_ = _teksten(mock_st.warning)
        compact = [t for t in open_ if "Compactheid is nog niet" in t]
        begrijp = [t for t in open_ if "Begrijpelijkheid is nog niet" in t]
        assert len(compact) == 1 and len(begrijp) == 1
        assert compact != begrijp
        assert "doelgroep" in begrijp[0] and "doelgroep" not in compact[0]

    @pytest.mark.asyncio
    async def test_tweede_zin_toont_passage_als_fout_onderdeel(self):
        resultaat = await _orchestrator().validate_text(
            begrip="object", text="Wat is dit? Afgebakend object."
        )
        mock_st = _render(resultaat)
        fouten = _teksten(mock_st.error)
        assert any("dit? Afgebakend" in t for t in fouten)
        regels = _teksten(mock_st.warning) + fouten
        assert any(t.startswith("⚠️ INT-01") for t in regels)
