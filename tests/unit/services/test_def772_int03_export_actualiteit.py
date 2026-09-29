"""DEF-772 WP4 v3 — INT-03-exportactualiteit ná de definitieve samenstelling.

Reviewbevinding (Codex, review v1): de INT-03-replay bond aan de recordtekst
en de ingebedde toelichting vóórdat de aggregatie de uiteindelijke uitvoer
samenstelde. Daarna kon de export een andere toelichting (`explanation` uit
de voorbeeldentabel of `additional_data`) of een `definitie_aangepast`
bevatten, terwijl de beoordeling `pass`/`applied=True` bleef dragen — een
actuele goedkeuring voor een andere kandidaat dan de geëxporteerde.

Deze tests lopen de échte exportroutes (`ExportService` +
`DataAggregationService`, daadwerkelijk geschreven JSON-/CSV-/TXT-bestanden,
readback uit die bestanden) op een échte tijdelijke SQLite-database en
bewijzen dat de beoordeling na de fix gebonden is aan exact de kandidaat die
de export draagt (begrip, tekst — `definitie_aangepast` als die er is, anders
`definitie_origineel` —, de drie contextlijsten van de uitvoer en de
uiteindelijke toelichting, ook na expliciet leegmaken). Een afwijkende
kandidaat maakt de beoordeling zichtbaar historisch (`applied=False`, geen
actuele pass); het opgeslagen document blijft als historisch bewijs bewaard
en de database verandert niet. Het exportdocument benoemt (`candidate`) aan
welke waarden en uit welke exportvelden de beoordeling gebonden is, zodat een
dubbele tekst (origineel én aangepast) niet misleidt.

Grens: de binding is `BINDING` uit de WP3-fixture (geen modelaanroep); de
beoordelingsdocumenten zijn synthetisch (`bouw_int03_beoordeling`), gebonden
aan de opgeslagen kandidaat.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pytest

from database.definitie_repository import DefinitieRepository
from services.data_aggregation_service import DataAggregationService
from services.definition_repository import DefinitionRepository
from services.export_service import ExportFormat, ExportLevel, ExportService
from services.interfaces import Definition
from tests.fixtures.def772_fakes import BINDING, bouw_int03_beoordeling

pytestmark = [pytest.mark.unit]

BEGRIP = "archiefkaart"
ZIN = "Beschrijving van een verzameling documenten die bij een zaak horen."
ZIN_ANDERS = "Beschrijving van een verzameling documenten die bij een dossier horen."
TOELICHTING = "Synthetische toelichting bij de archiefkaart."
TOELICHTING_DB = "Toelichting uit de voorbeeldentabel (explanation)."
TOELICHTING_EXTRA = "Aanvullende toelichting uit de exportsessie."
ORG = ["Stichting Zilver"]
JUR = ["privaatrecht"]
WET = ["Regeling Z"]
CONTEXT = {
    "organisatorische_context": list(ORG),
    "juridische_context": list(JUR),
    "wettelijke_basis": list(WET),
}
VELDEN_ORIGINEEL = {
    "begrip": "begrip",
    "text": "definitie_origineel",
    "toelichting": "toelichting",
    "context": "context_dict",
}
VELDEN_AANGEPAST = {**VELDEN_ORIGINEEL, "text": "definitie_aangepast"}


@pytest.fixture(autouse=True)
def _werkmap(tmp_path, monkeypatch):
    # De enkele TXT-export schrijft naar `exports/` onder de werkmap.
    monkeypatch.chdir(tmp_path)


def _document(toelichting: str | None) -> dict[str, Any]:
    return bouw_int03_beoordeling(BEGRIP, ZIN, CONTEXT, toelichting, scenario="pass")


def _record(
    tmp_path, *, toelichting: str | None = TOELICHTING, explanation: str | None = None
) -> tuple[Path, int, dict[str, Any]]:
    """Een echt record met een aan zijn kandidaat gebonden INT-03-beoordeling;
    optioneel een afzonderlijk opgeslagen `explanation`-voorbeeld."""
    pad = tmp_path / "actualiteit.db"
    document = _document(toelichting)
    did = DefinitionRepository(str(pad)).save(
        Definition(
            begrip=BEGRIP,
            definitie=ZIN,
            toelichting=toelichting,
            categorie="type",
            organisatorische_context=list(ORG),
            juridische_context=list(JUR),
            wettelijke_basis=list(WET),
            metadata={
                "status": "draft",
                "created_by": "generator",
                "int03_assessment": document,
            },
        )
    )
    if explanation is not None:
        assert DefinitieRepository(str(pad)).save_voorbeelden(
            did, {"explanation": [explanation]}
        )
    return pad, did, document


def _service(pad: Path, tmp_path) -> ExportService:
    repo = DefinitieRepository(str(pad))
    return ExportService(
        repository=repo,
        data_aggregation_service=DataAggregationService(repo, int03_binding=BINDING),
        export_dir=str(tmp_path / "exports"),
    )


def _json(pad: Path, tmp_path, did: int, **extra: Any) -> dict[str, Any]:
    uit = _service(pad, tmp_path).export_definitie(
        definitie_id=did, format=ExportFormat.JSON, **extra
    )
    return json.loads(Path(uit).read_text(encoding="utf-8"))


def _csv(pad: Path, tmp_path, did: int, **extra: Any) -> dict[str, str]:
    uit = _service(pad, tmp_path).export_definitie(
        definitie_id=did, format=ExportFormat.CSV, **extra
    )
    with open(uit, newline="", encoding="utf-8") as f:
        [rij] = list(csv.DictReader(f))
    return rij


def _txt(pad: Path, tmp_path, did: int, **extra: Any) -> str:
    uit = _service(pad, tmp_path).export_definitie(
        definitie_id=did, format=ExportFormat.TXT, **extra
    )
    return Path(uit).read_text(encoding="utf-8")


def _bulk(pad: Path, tmp_path, did: int, formaat: ExportFormat) -> Path:
    repo = DefinitieRepository(str(pad))
    resultaat = _service(pad, tmp_path).export_multiple_definitions(
        [repo.get_definitie(did)], format=formaat, level=ExportLevel.COMPLEET
    )
    return Path(resultaat.path)


def _int03_sectie(txt: str) -> str:
    kop = "Verwijzingen (INT-03):"
    assert kop in txt
    return txt.split(kop, 1)[1].split("\n\n", 1)[0]


def _kandidaat(
    doc: dict[str, Any], *, tekst: str, toelichting: str | None, velden: dict
) -> None:
    kandidaat = doc["candidate"]
    assert kandidaat["begrip"] == BEGRIP
    assert kandidaat["text"] == tekst
    assert kandidaat["toelichting"] == toelichting
    assert kandidaat["context"] == CONTEXT
    assert kandidaat["fields"] == velden


def _actueel(doc: dict[str, Any], **kandidaat: Any) -> None:
    assert doc["status"] == "pass"
    assert doc["applied"] is True and doc["historical"] is False
    assert doc["verdict"] == "pass"
    [verwijzing] = doc["references"]
    assert verwijzing["word"] == "die"
    _kandidaat(doc, **kandidaat)


def _historisch(doc: dict[str, Any], **kandidaat: Any) -> None:
    assert doc["status"] == "review_required"
    assert doc["applied"] is False and doc["historical"] is True
    assert "gewijzigd" in doc["reason"]
    assert doc["verdict"] == "pass"  # zichtbaar als historie, geen actuele pass
    assert doc["references"] == []
    _kandidaat(doc, **kandidaat)


def _db_onveranderd(pad: Path, did: int, document: dict[str, Any]) -> None:
    """Exporteren wijzigt niets: het oorspronkelijke document blijft (als
    historisch bewijs) staan, zonder historie, tekst en versie gelijk."""
    rec = DefinitieRepository(str(pad)).get_definitie(did)
    assert rec.get_int03_assessment() == document
    assert rec.get_int03_assessment_history() == []
    assert rec.get_definitie_tekst() == ZIN
    assert rec.version_number == 1


def test_ongewijzigde_export_is_gebonden_aan_de_uitgevoerde_kandidaat(tmp_path):
    pad, did, document = _record(tmp_path)
    uit = _json(pad, tmp_path, did)
    assert uit["definitie"]["definitie_origineel"] == ZIN
    assert uit["definitie"]["definitie_aangepast"] is None
    assert uit["taalkundig"]["toelichting"] == TOELICHTING
    assert uit["context"] == {
        "organisatorisch": ORG,
        "juridisch": JUR,
        "wettelijk": WET,
    }
    doc = uit["validatie"]["int03_beoordeling"]
    _actueel(doc, tekst=ZIN, toelichting=TOELICHTING, velden=VELDEN_ORIGINEEL)
    assert doc["document"] == document
    txt = _txt(pad, tmp_path, did)
    sectie = _int03_sectie(txt)
    assert "INT-03 — voldoet" in sectie and "niet toegepast" not in sectie
    assert "Gebonden aan:" in sectie and "definitie_origineel" in sectie
    _db_onveranderd(pad, did, document)


def test_afwijkende_opgeslagen_explanation_maakt_de_beoordeling_historisch(tmp_path):
    """(1) Zonder aanvullende data: de export draagt de `explanation` uit de
    voorbeeldentabel als toelichting, niet de ingebedde toelichting waaraan
    de beoordeling bond — enkel én bulk, JSON/CSV/TXT."""
    pad, did, document = _record(tmp_path, explanation=TOELICHTING_DB)
    uit = _json(pad, tmp_path, did)
    assert uit["taalkundig"]["toelichting"] == TOELICHTING_DB
    assert uit["definitie"]["definitie_origineel"] == ZIN
    doc = uit["validatie"]["int03_beoordeling"]
    _historisch(doc, tekst=ZIN, toelichting=TOELICHTING_DB, velden=VELDEN_ORIGINEEL)
    assert doc["document"] == document  # het oorspronkelijke bewijs blijft

    rij = _csv(pad, tmp_path, did)
    assert rij["toelichting"] == TOELICHTING_DB
    assert json.loads(rij["int03_beoordeling"])["applied"] is False

    txt = _txt(pad, tmp_path, did)
    assert TOELICHTING_DB in txt
    assert "niet toegepast" in _int03_sectie(txt)
    assert "INT-03 — nog te beoordelen" in txt

    # Bulk (zelfde aggregatie, geen aanvullende data).
    [bulk] = json.loads(
        _bulk(pad, tmp_path, did, ExportFormat.JSON).read_text(encoding="utf-8")
    )["definities"]
    assert bulk["toelichting"] == TOELICHTING_DB
    assert bulk["int03_beoordeling"]["applied"] is False
    assert bulk["int03_beoordeling"]["candidate"]["toelichting"] == TOELICHTING_DB
    with open(_bulk(pad, tmp_path, did, ExportFormat.CSV), newline="") as f:
        [bulk_rij] = list(csv.DictReader(f))
    assert json.loads(bulk_rij["int03_beoordeling"])["applied"] is False
    bulk_txt = _bulk(pad, tmp_path, did, ExportFormat.TXT).read_text(encoding="utf-8")
    assert "niet toegepast" in bulk_txt
    _db_onveranderd(pad, did, document)


def test_aanvullende_gewijzigde_toelichting_maakt_de_beoordeling_historisch(tmp_path):
    """(2) `additional_data["toelichting"]` vervangt de toelichting in de
    uitvoer; de beoordeling is dan historisch. Dezelfde toelichting als de
    gebonden blijft actueel (controle)."""
    pad, did, document = _record(tmp_path)
    extra = {"toelichting": TOELICHTING_EXTRA}
    uit = _json(pad, tmp_path, did, additional_data=extra)
    assert uit["taalkundig"]["toelichting"] == TOELICHTING_EXTRA
    _historisch(
        uit["validatie"]["int03_beoordeling"],
        tekst=ZIN,
        toelichting=TOELICHTING_EXTRA,
        velden=VELDEN_ORIGINEEL,
    )
    rij = _csv(pad, tmp_path, did, additional_data=extra)
    assert rij["toelichting"] == TOELICHTING_EXTRA
    assert json.loads(rij["int03_beoordeling"])["applied"] is False
    txt = _txt(pad, tmp_path, did, additional_data=extra)
    assert TOELICHTING_EXTRA in txt and "niet toegepast" in _int03_sectie(txt)

    controle = _json(pad, tmp_path, did, additional_data={"toelichting": TOELICHTING})
    assert controle["taalkundig"]["toelichting"] == TOELICHTING
    _actueel(
        controle["validatie"]["int03_beoordeling"],
        tekst=ZIN,
        toelichting=TOELICHTING,
        velden=VELDEN_ORIGINEEL,
    )
    _db_onveranderd(pad, did, document)


def test_expliciet_lege_aanvullende_toelichting_volgt_de_uiteindelijke_uitvoer(
    tmp_path,
):
    """(3) Expliciet leegmaken via `additional_data["toelichting"] = ""`.

    a. Record zonder ingebedde toelichting (beoordeling gebonden aan geen
       toelichting) mét een `explanation`-voorbeeld: de standaardexport draagt
       dat voorbeeld → historisch; expliciet leeg → de uitvoer draagt geen
       toelichting → de beoordeling is weer actueel.
    b. Record mét ingebedde toelichting: de bestaande terugval van de
       aggregatie vult een lege toelichting weer met de ingebedde (ongewijzigd
       gedrag); de uitvoer draagt dus de gebonden toelichting → actueel.
    """
    pad, did, document = _record(tmp_path, toelichting=None, explanation=TOELICHTING_DB)
    assert DefinitieRepository(str(pad)).get_definitie(did).definitie == ZIN
    standaard = _json(pad, tmp_path, did)
    assert standaard["taalkundig"]["toelichting"] == TOELICHTING_DB
    _historisch(
        standaard["validatie"]["int03_beoordeling"],
        tekst=ZIN,
        toelichting=TOELICHTING_DB,
        velden=VELDEN_ORIGINEEL,
    )
    leeg = _json(pad, tmp_path, did, additional_data={"toelichting": ""})
    assert leeg["taalkundig"]["toelichting"] == ""
    _actueel(
        leeg["validatie"]["int03_beoordeling"],
        tekst=ZIN,
        toelichting=None,
        velden=VELDEN_ORIGINEEL,
    )
    txt = _txt(pad, tmp_path, did, additional_data={"toelichting": ""})
    assert TOELICHTING_DB not in txt
    sectie = _int03_sectie(txt)
    assert "INT-03 — voldoet" in sectie and "niet toegepast" not in sectie
    assert "toelichting: geen" in sectie
    rec = DefinitieRepository(str(pad)).get_definitie(did)
    assert rec.get_int03_assessment() == document
    assert rec.get_int03_assessment_history() == []

    pad_b, did_b, document_b = _record(tmp_path.joinpath("b"), toelichting=TOELICHTING)
    uit_b = _json(pad_b, tmp_path, did_b, additional_data={"toelichting": ""})
    assert uit_b["taalkundig"]["toelichting"] == TOELICHTING  # bestaande terugval
    _actueel(
        uit_b["validatie"]["int03_beoordeling"],
        tekst=ZIN,
        toelichting=TOELICHTING,
        velden=VELDEN_ORIGINEEL,
    )
    _db_onveranderd(pad_b, did_b, document_b)


def test_definitie_aangepast_maakt_de_beoordeling_historisch_en_benoemt_de_tekst(
    tmp_path,
):
    """(4) Een `definitie_aangepast` is de geëxporteerde kandidaat (zoals ook
    de validatiegate haar toetst); de export draagt dan twee teksten en de
    beoordeling benoemt aan welke zij gebonden is. Een andere zin → historisch;
    dezelfde zin als aangepaste tekst → actueel, gebonden aan
    `definitie_aangepast` (controle)."""
    pad, did, document = _record(tmp_path)
    extra = {"definitie_aangepast": ZIN_ANDERS}
    uit = _json(pad, tmp_path, did, additional_data=extra)
    assert uit["definitie"]["definitie_origineel"] == ZIN
    assert uit["definitie"]["definitie_aangepast"] == ZIN_ANDERS
    assert uit["taalkundig"]["toelichting"] == TOELICHTING
    doc = uit["validatie"]["int03_beoordeling"]
    _historisch(doc, tekst=ZIN_ANDERS, toelichting=TOELICHTING, velden=VELDEN_AANGEPAST)
    assert doc["document"]["fingerprint"] != doc["fingerprint"]
    rij = _csv(pad, tmp_path, did, additional_data=extra)
    assert rij["definitie_aangepast"] == ZIN_ANDERS
    assert json.loads(rij["int03_beoordeling"])["candidate"]["text"] == ZIN_ANDERS
    assert json.loads(rij["int03_beoordeling"])["applied"] is False
    txt = _txt(pad, tmp_path, did, additional_data=extra)
    sectie = _int03_sectie(txt)
    assert "niet toegepast" in sectie
    assert "definitie_aangepast" in sectie and ZIN_ANDERS in sectie

    controle = _json(pad, tmp_path, did, additional_data={"definitie_aangepast": ZIN})
    assert controle["definitie"]["definitie_aangepast"] == ZIN
    _actueel(
        controle["validatie"]["int03_beoordeling"],
        tekst=ZIN,
        toelichting=TOELICHTING,
        velden=VELDEN_AANGEPAST,
    )
    _db_onveranderd(pad, did, document)


def test_aanvullende_context_wordt_geborgd_en_de_binding_volgt_de_uitvoer(tmp_path):
    """Context uit `additional_data` wordt door de bestaande K2-borging op de
    recordwaarden teruggezet; de export draagt de recordcontext en de
    beoordeling blijft daaraan gebonden (controle)."""
    pad, did, document = _record(tmp_path)
    uit = _json(
        pad,
        tmp_path,
        did,
        additional_data={"context_dict": {"organisatorisch": ["Stichting Goud"]}},
    )
    assert uit["context"]["organisatorisch"] == ORG
    _actueel(
        uit["validatie"]["int03_beoordeling"],
        tekst=ZIN,
        toelichting=TOELICHTING,
        velden=VELDEN_ORIGINEEL,
    )
    _db_onveranderd(pad, did, document)
