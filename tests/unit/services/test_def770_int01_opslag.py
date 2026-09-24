"""DEF-770 (INT-01): de deeluitkomst via de gewone opslag-, lees- en exportroutes.

Reviewbevinding 1: bij één zin verdween de open INT-01-dekking bij opslag en
export (er is dan geen violation om op te slaan). Vereist: de onderdelen
(zinsstructuur, grenzen met passage, compactheid en begrijpelijkheid apart),
hun redenen en de binding aan exact de beoordeelde kern en recordversie
worden opgeslagen, teruggelezen en geëxporteerd — en een uitkomst van een
andere tekst geldt nooit stil voor de huidige.

Bewijsgrens: echte SQLite in een tijdelijke map, echte repositories en
exportservice. Geen modelaanroep.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

import pytest

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)
from domain.int01.opslag import INT01_BEOORDELING_FIELD, tekstvingerafdruk
from services.data_aggregation_service import DataAggregationService
from services.definition_repository import DefinitionRepository
from services.export_service import ExportFormat, ExportLevel, ExportService
from services.interfaces import Definition

pytestmark = [pytest.mark.unit]

EEN_ZIN = (
    "eis die een organisatie moet ondersteunen om migratie van de huidige naar "
    "de toekomstige situatie mogelijk te maken."
)
TWEE_ZINNEN = "Afgebakend object. Heeft vaste vorm."
ONZEKER = "Object met gegevens enz. 3 velden zijn verplicht."
TOELICHTING = "Het wordt geregistreerd. Zie ook het beleidskader."
OPEN_DELEN = {"compactheid": "review_required", "begrijpelijkheid": "review_required"}


def _delen(beoordeling: dict) -> dict[str, str]:
    return {d["id"]: d["status"] for d in beoordeling["parts"]}


def _nieuw(pad: Path, tekst: str) -> int:
    return DefinitieRepository(str(pad)).create_definitie(
        DefinitieRecord(
            begrip="transitie-eis",
            definitie=tekst,
            categorie="type",
            organisatorische_context='["Stichting Zilver"]',
            juridische_context="[]",
            wettelijke_basis="[]",
            status=DefinitieStatus.DRAFT.value,
        )
    )


def _lees(pad: Path, did: int) -> DefinitieRecord:
    record = DefinitieRepository(str(pad)).get_definitie(did)
    assert record is not None
    return record


def _exportservice(pad: Path, tmp_path: Path) -> ExportService:
    repo = DefinitieRepository(str(pad))
    return ExportService(
        repository=repo,
        data_aggregation_service=DataAggregationService(repo),
        export_dir=str(tmp_path / "exports"),
    )


def _bulk(pad: Path, tmp_path: Path, did: int, formaat: ExportFormat) -> Path:
    resultaat = _exportservice(pad, tmp_path).export_multiple_definitions(
        [_lees(pad, did)], format=formaat, level=ExportLevel.UITGEBREID
    )
    return Path(resultaat.path)


def _json_rij(pad: Path, tmp_path: Path, did: int) -> dict:
    inhoud = _bulk(pad, tmp_path, did, ExportFormat.JSON).read_text(encoding="utf-8")
    [rij] = json.loads(inhoud)["definities"]
    return rij


def _csv_int01(pad: Path, tmp_path: Path, did: int) -> dict:
    with open(_bulk(pad, tmp_path, did, ExportFormat.CSV), newline="") as f:
        [rij] = list(csv.DictReader(f))
    return json.loads(rij["int01_beoordeling"])


class TestOpslagEnTeruglezen:
    def test_een_zin_open_met_twee_aparte_onderdelen(self, tmp_path):
        pad = tmp_path / "int01.db"
        did = _nieuw(pad, EEN_ZIN)
        uit = _lees(pad, did).get_int01_beoordeling()
        assert uit["status"] == "review_required" and uit["score"] is None
        assert uit["applied"] is True
        assert _delen(uit) == {"zinsstructuur": "pass", **OPEN_DELEN}
        redenen = {d["id"]: d["reason"] for d in uit["parts"]}
        assert redenen["compactheid"] != redenen["begrijpelijkheid"]
        assert uit["binding"] == {
            "tekst_sha256": tekstvingerafdruk(EEN_ZIN),
            "version_number": 1,
        }

    def test_onzekere_grens_open_met_passage(self, tmp_path):
        pad = tmp_path / "int01.db"
        did = _nieuw(pad, ONZEKER)
        uit = _lees(pad, did).get_int01_beoordeling()
        assert uit["status"] == "review_required"
        onzeker = [d for d in uit["parts"] if d["id"].startswith("zinsgrens_onzeker")]
        assert len(onzeker) == 1
        assert "enz. 3" in onzeker[0]["evidence"]
        assert onzeker[0]["reason"]
        assert "zinsstructuur" not in _delen(uit)

    def test_tweede_zin_fail_met_passage(self, tmp_path):
        pad = tmp_path / "int01.db"
        did = _nieuw(pad, TWEE_ZINNEN)
        uit = _lees(pad, did).get_int01_beoordeling()
        assert uit["status"] == "fail"
        assert _delen(uit) == {"zinsgrens_1": "fail", **OPEN_DELEN}
        [grens] = [d for d in uit["parts"] if d["id"] == "zinsgrens_1"]
        assert "object. Heeft" in grens["evidence"]

    def test_aparte_toelichting_telt_niet_mee(self, tmp_path):
        repo = DefinitionRepository(str(tmp_path / "int01.db"))
        did = repo.save(
            Definition(
                begrip="transitie-eis",
                definitie=EEN_ZIN,
                toelichting=TOELICHTING,
                categorie="type",
                organisatorische_context=["Stichting Zilver"],
                metadata={"status": "draft", "created_by": "synthetisch"},
            )
        )
        record = repo.get_definitie(did)
        assert "Toelichting:" in record.definitie
        uit = record.get_int01_beoordeling()
        # Gebonden aan de kern zónder toelichting; de tweede zin van de
        # toelichting is geen INT-01-grens.
        assert uit["binding"]["tekst_sha256"] == tekstvingerafdruk(EEN_ZIN)
        assert uit["status"] == "review_required" and uit["applied"] is True
        # Ook via de servicelaag (Definition.metadata) teruggelezen.
        herladen = repo.get(did)
        assert herladen.metadata[INT01_BEOORDELING_FIELD]["status"] == "review_required"
        assert herladen.metadata[INT01_BEOORDELING_FIELD]["applied"] is True


class TestTekstwijziging:
    def test_update_van_de_kern_levert_nieuwe_uitkomst_en_historie(self, tmp_path):
        pad = tmp_path / "int01.db"
        did = _nieuw(pad, EEN_ZIN)
        repo = DefinitieRepository(str(pad))
        assert repo.update_definitie(did, {"definitie": TWEE_ZINNEN}, "tester")
        record = _lees(pad, did)
        uit = record.get_int01_beoordeling()
        assert record.version_number == 2
        assert uit["status"] == "fail" and uit["applied"] is True
        assert uit["binding"] == {
            "tekst_sha256": tekstvingerafdruk(TWEE_ZINNEN),
            "version_number": 2,
        }
        [vorige] = record.get_int01_beoordeling_history()
        assert vorige["assessment"]["status"] == "review_required"
        assert vorige["assessment"]["binding"]["version_number"] == 1
        assert vorige["superseded_on_version"] == 2

    def test_update_zonder_kernwijziging_behoudt_de_uitkomst(self, tmp_path):
        pad = tmp_path / "int01.db"
        did = _nieuw(pad, EEN_ZIN)
        voor = _lees(pad, did).get_int01_beoordeling()
        repo = DefinitieRepository(str(pad))
        assert repo.update_definitie(did, {"toelichting_proces": "notitie"}, "t")
        record = _lees(pad, did)
        assert record.get_int01_beoordeling()["assessed_at"] == voor["assessed_at"]
        assert record.get_int01_beoordeling_history() == []

    def test_wijziging_buiten_de_persistentielaag_maakt_uitkomst_historisch(
        self, tmp_path, monkeypatch
    ):
        pad = tmp_path / "int01.db"
        did = _nieuw(pad, EEN_ZIN)
        with sqlite3.connect(pad) as conn:
            conn.execute(
                "UPDATE definities SET definitie = ? WHERE id = ?", (TWEE_ZINNEN, did)
            )
        uit = _lees(pad, did).get_int01_beoordeling()
        assert uit["applied"] is False
        assert "gewijzigd" in uit["applied_reason"]

        rij = _json_rij(pad, tmp_path, did)
        assert rij["int01_beoordeling"]["applied"] is False
        assert _csv_int01(pad, tmp_path, did)["applied"] is False
        txt = _bulk(pad, tmp_path, did, ExportFormat.TXT).read_text(encoding="utf-8")
        assert "niet toegepast" in txt

        monkeypatch.chdir(tmp_path)
        enkel = _exportservice(pad, tmp_path).export_definitie(
            definitie_id=did, format=ExportFormat.TXT
        )
        assert "niet toegepast" in Path(enkel).read_text(encoding="utf-8")

    def test_ruwe_registratie_kan_de_uitkomst_niet_vervalsen(self, tmp_path):
        pad = tmp_path / "int01.db"
        did = _nieuw(pad, TWEE_ZINNEN)
        repo = DefinitieRepository(str(pad))
        vals = {INT01_BEOORDELING_FIELD: {"status": "pass", "parts": []}, "x": 1}
        repo.update_definitie(did, {"generation_prompt_data": json.dumps(vals)}, "t")
        uit = _lees(pad, did).get_int01_beoordeling()
        assert uit["status"] == "fail" and uit["applied"] is True
        with pytest.raises(ValueError, match="beheerde"):
            repo.update_definitie(did, {"generation_prompt_data": None}, "t")
        assert _lees(pad, did).get_int01_beoordeling()["status"] == "fail"


class TestExport:
    def test_een_zin_in_json_csv_en_txt_met_aparte_onderdelen(
        self, tmp_path, monkeypatch
    ):
        pad = tmp_path / "int01.db"
        did = _nieuw(pad, EEN_ZIN)
        opgeslagen = _lees(pad, did).get_int01_beoordeling()

        rij = _json_rij(pad, tmp_path, did)
        assert rij["int01_beoordeling"] == opgeslagen
        assert _csv_int01(pad, tmp_path, did) == opgeslagen

        txt = _bulk(pad, tmp_path, did, ExportFormat.TXT).read_text(encoding="utf-8")
        assert "Zinsgrenzen (INT-01)" in txt
        assert "INT-01 — nog te beoordelen" in txt
        assert "compactheid: nog te beoordelen" in txt
        assert "begrijpelijkheid: nog te beoordelen" in txt
        assert "zinsstructuur: voldoet" in txt

        monkeypatch.chdir(tmp_path)
        service = _exportservice(pad, tmp_path)
        enkel_txt = Path(
            service.export_definitie(definitie_id=did, format=ExportFormat.TXT)
        ).read_text(encoding="utf-8")
        assert "Zinsgrenzen (INT-01)" in enkel_txt
        assert "begrijpelijkheid: nog te beoordelen" in enkel_txt
        enkel_json = json.loads(
            Path(
                service.export_definitie(definitie_id=did, format=ExportFormat.JSON)
            ).read_text(encoding="utf-8")
        )
        assert enkel_json["validatie"]["int01_beoordeling"] == opgeslagen

    @pytest.mark.parametrize("tekst", [EEN_ZIN, TWEE_ZINNEN, ONZEKER])
    def test_enkele_csv_export_draagt_de_gebonden_uitkomst(self, tmp_path, tekst):
        # Reviewronde 2: de enkele CSV (UI-exportknop) verloor INT-01.
        pad = tmp_path / "int01.db"
        did = _nieuw(pad, tekst)
        opgeslagen = _lees(pad, did).get_int01_beoordeling()
        enkel = _exportservice(pad, tmp_path).export_definitie(
            definitie_id=did, format=ExportFormat.CSV
        )
        with open(enkel, newline="", encoding="utf-8") as f:
            [rij] = list(csv.DictReader(f))
        cel = json.loads(rij["int01_beoordeling"])
        assert cel == opgeslagen
        assert cel["status"] != "pass" and cel["applied"] is True
        assert cel["binding"]["tekst_sha256"] == tekstvingerafdruk(tekst)
        assert {"compactheid", "begrijpelijkheid"} <= set(_delen(cel))

    def test_enkele_csv_export_toont_oude_uitkomst_als_niet_toegepast(self, tmp_path):
        pad = tmp_path / "int01.db"
        did = _nieuw(pad, EEN_ZIN)
        with sqlite3.connect(pad) as conn:
            conn.execute(
                "UPDATE definities SET definitie = ? WHERE id = ?", (TWEE_ZINNEN, did)
            )
        enkel = _exportservice(pad, tmp_path).export_definitie(
            definitie_id=did, format=ExportFormat.CSV
        )
        with open(enkel, newline="", encoding="utf-8") as f:
            [rij] = list(csv.DictReader(f))
        assert json.loads(rij["int01_beoordeling"])["applied"] is False

    def test_tweede_zin_in_export_met_passage(self, tmp_path):
        pad = tmp_path / "int01.db"
        did = _nieuw(pad, TWEE_ZINNEN)
        assert _csv_int01(pad, tmp_path, did)["status"] == "fail"
        txt = _bulk(pad, tmp_path, did, ExportFormat.TXT).read_text(encoding="utf-8")
        assert "INT-01 — voldoet niet" in txt
        assert "object. Heeft" in txt

    def test_record_zonder_opgeslagen_uitkomst_is_zichtbaar_niet_beoordeeld(
        self, tmp_path, monkeypatch
    ):
        # Een record van vóór DEF-770: geen INT-01-sleutel in de registratie.
        pad = tmp_path / "int01.db"
        did = _nieuw(pad, EEN_ZIN)
        with sqlite3.connect(pad) as conn:
            conn.execute(
                "UPDATE definities SET generation_prompt_data = NULL WHERE id = ?",
                (did,),
            )
        assert _lees(pad, did).get_int01_beoordeling() is None
        # Lege exportcel (zoals elk leeg veld), geen verzonnen uitkomst.
        assert _json_rij(pad, tmp_path, did)["int01_beoordeling"] == ""
        monkeypatch.chdir(tmp_path)
        enkel = _exportservice(pad, tmp_path).export_definitie(
            definitie_id=did, format=ExportFormat.TXT
        )
        tekst = Path(enkel).read_text(encoding="utf-8")
        assert "geen opgeslagen INT-01-uitkomst: niet beoordeeld" in tekst
        # De eerstvolgende gewone schrijfactie legt de uitkomst alsnog vast.
        DefinitieRepository(str(pad)).update_definitie(
            did, {"toelichting_proces": "n"}, "t"
        )
        assert _lees(pad, did).get_int01_beoordeling()["status"] == "review_required"
