"""DEF-768 reviewcorrectie BC-01: geïmporteerd ESS-05-bewijs is nooit actueel.

Echte JSON-export en -import (`DefinitieRepository.export_to_json` /
`import_from_json`), echte tijdelijke SQLite, readback via
`DefinitionRepository.get` en de editorreplay (`ess05_uitkomst_van_definition`,
zoals `DefinitionEditTab._render_ess05_section`). Geen netwerk, geen modelcall.

* Een lokaal werkelijk verkregen beoordeling blijft na opslaan en laden een
  actuele pass (positieve controle).
* Een samenhangend vervalst document (M3-C: concept, verificatie en beide
  hashvelden consistent herschreven; sinds `ess05-assess/15` ook ruwe respons
  en afleidingsbinding) speelt lokaal als pass af — de replay
  toetst consistentie, geen herkomst — maar via JSON-import wordt het nooit een
  actuele beoordeling.
* Ook een legitieme export → import geeft zonder nieuwe beoordeling geen
  actuele pass; het aangeleverde document blijft als herkenbare niet-actuele
  historie bewaard (niets gaat verloren).
* Een na de import nieuw berekende beoordeling voldoet wel.
* Een geïmporteerde lege-ruimtebevestiging (claim van een deskundige uit het
  bestand) geeft evenmin een actuele pass.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from database.definitie_repository import DefinitieRepository
from database.ess05_registratie import neutraliseer_geimporteerde_ess05
from domain.ess05.bewijs import Ess05Concept
from domain.ess05.contract import CONTRACTVERSIE, bereken_ess05_vingerafdruk
from services.definition_edit_service import (
    ess03_intentie_van_definition,
    ess05_uitkomst_van_definition,
)
from services.definition_repository import DefinitionRepository
from tests.fixtures.def768_fakes import (
    BINDING,
    antwoord_uit_concept,
    bouw_ess05_beoordeling,
)
from tests.unit.services.test_def768_ess05_persistentie import (
    BEGRIP,
    BUREN,
    CONTEXT,
    TEKST,
    _definition,
)

pytestmark = [pytest.mark.unit]


def _doc_voor(geladen) -> dict[str, Any]:
    """Een contractconforme pass-beoordeling voor exact dit geladen record."""
    return bouw_ess05_beoordeling(
        BEGRIP,
        TEKST,
        CONTEXT,
        [],
        buren=BUREN,
        intentie=ess03_intentie_van_definition(geladen),
        uitgesloten_termen=("borg",),  # de afgewezen buur uit BUREN
    )


def _replay(repo: DefinitionRepository, did: int) -> dict[str, Any]:
    return ess05_uitkomst_van_definition(repo.get(did), None, BINDING)


def _lokaal(tmp_path: Path, naam: str = "bron.db") -> tuple[DefinitionRepository, int]:
    repo = DefinitionRepository(str(tmp_path / naam))
    did = repo.save(_definition(metadata={"ess05_assessment": None}))
    geladen = repo.get(did)
    geladen.metadata["ess05_assessment"] = _doc_voor(geladen)
    repo.save(geladen)
    return repo, did


def _vervals(doc: dict[str, Any]) -> dict[str, Any]:
    """M3-C: concept, verificatie en beide hashvelden samenhangend herschreven,
    inclusief de ruwe respons en de afleidingsbinding daarvan."""
    doc = deepcopy(doc)
    doc["concept"]["claims"][0]["text"] = "Vervalste, niet geverifieerde onderbouwing."
    nieuw = Ess05Concept(deepcopy(doc["concept"])).hash
    doc["verification"]["candidate_hash"] = nieuw
    doc["verification_input"]["candidate_hash"] = nieuw
    ruw = json.dumps(antwoord_uit_concept(doc["concept"]), ensure_ascii=False)
    ruwe_hash = hashlib.sha256(ruw.encode("utf-8")).hexdigest()
    doc["raw_response"] = ruw
    doc["raw_response_sha256"] = ruwe_hash
    doc["concept_derivation"]["raw_response_sha256"] = ruwe_hash
    doc["concept_derivation"]["concept_hash"] = nieuw
    return doc


def _export(bron: DefinitionRepository, pad: Path, mutatie=None) -> Path:
    bron.legacy_repo.export_to_json(str(pad))
    data = json.loads(pad.read_text(encoding="utf-8"))
    # De export bevat ook eerdere versies; importeer alleen de nieuwste.
    item = max(
        (d for d in data["definities"] if d["begrip"] == BEGRIP),
        key=lambda d: (d.get("version_number") or 0, d.get("id") or 0),
    )
    if mutatie is not None:
        registratie = json.loads(item["generation_prompt_data"])
        mutatie(registratie)
        item["generation_prompt_data"] = json.dumps(registratie, ensure_ascii=False)
    data["definities"] = [item]
    pad.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return pad


def _importeer(
    tmp_path: Path, pad: Path, naam: str = "doel.db"
) -> tuple[DefinitionRepository, int]:
    doel = DefinitionRepository(str(tmp_path / naam))
    gelukt, mislukt, fouten = DefinitieRepository(doel.db_path).import_from_json(
        str(pad), import_by="tester"
    )
    assert (gelukt, mislukt, fouten) == (1, 0, [])
    (record,) = [  # een verse database bevat ook seedrecords
        r for r in doel.legacy_repo.search_definities(limit=None) if r.begrip == BEGRIP
    ]
    assert record.source_type == "imported"
    return doel, record.id


def test_positief_lokaal_verkregen_beoordeling_is_actueel(tmp_path):
    repo, did = _lokaal(tmp_path)
    assert _replay(repo, did)["status"] == "pass"


def test_samenhangend_vervalst_document_speelt_lokaal_wel_af(tmp_path):
    """Controle: de replay toetst consistentie, geen herkomst (M3-C). Dit
    maakt de importgrens hieronder noodzakelijk."""
    repo, did = _lokaal(tmp_path)
    geladen = repo.get(did)
    vervalst = _vervals(geladen.metadata["ess05_assessment"])
    uitkomst = ess05_uitkomst_van_definition(
        geladen, None, BINDING, assessment=vervalst
    )
    assert uitkomst["status"] == "pass"


def test_vervalst_document_via_json_import_is_nooit_actueel(tmp_path):
    bron, _ = _lokaal(tmp_path)

    def vervals(registratie: dict[str, Any]) -> None:
        registratie["ess05_assessment"] = _vervals(registratie["ess05_assessment"])

    doel, did = _importeer(tmp_path, _export(bron, tmp_path / "x.json", vervals))
    geladen = doel.get(did)
    assert "ess05_assessment" not in geladen.metadata
    uitkomst = _replay(doel, did)
    assert uitkomst["status"] != "pass"
    assert "Vervalste" not in json.dumps(uitkomst, ensure_ascii=False)


def test_legitieme_import_is_herkenbare_niet_actuele_historie(tmp_path):
    bron, bron_id = _lokaal(tmp_path)
    origineel = bron.get(bron_id).metadata["ess05_assessment"]
    doel, did = _importeer(tmp_path, _export(bron, tmp_path / "x.json"))
    assert _replay(doel, did)["status"] != "pass"
    registratie = doel.get_generation_prompt_data(did) or {}
    assert "ess05_assessment" not in registratie
    (historie,) = registratie["ess05_assessment_history"]
    assert historie["assessment"] == origineel  # niets verloren
    assert historie["herkomst"] == "import"
    assert historie["actueel"] is False
    # Burenlijst met expertbesluiten blijft invoergegeven.
    assert registratie["ess05_buren"] == BUREN


def test_na_import_nieuw_berekende_beoordeling_voldoet(tmp_path):
    bron, _ = _lokaal(tmp_path)
    doel, did = _importeer(tmp_path, _export(bron, tmp_path / "x.json"))
    geladen = doel.get(did)
    geladen.metadata["ess05_assessment"] = _doc_voor(geladen)
    doel.save(geladen)
    assert _replay(doel, did)["status"] == "pass"
    # De geïmporteerde historie blijft staan naast de nieuwe beoordeling.
    registratie = doel.get_generation_prompt_data(did) or {}
    assert registratie["ess05_assessment_history"][0]["herkomst"] == "import"


def test_enkelvoudige_import_via_de_service_is_evenmin_actueel(tmp_path):
    """Late regressie (na de fix toegevoegd): de enkelvoudige importroute
    (`DefinitionImportService` → `DefinitionRepository.save` met
    `source_type: imported` in de metadata) loopt via dezelfde create-grens."""
    bron, bron_id = _lokaal(tmp_path)
    doc = bron.get(bron_id).metadata["ess05_assessment"]
    doel = DefinitionRepository(str(tmp_path / "enkel.db"))
    did = doel.save(
        _definition(metadata={"source_type": "imported", "ess05_assessment": doc})
    )
    assert "ess05_assessment" not in doel.get(did).metadata
    assert _replay(doel, did)["status"] != "pass"
    registratie = doel.get_generation_prompt_data(did) or {}
    assert registratie["ess05_assessment_history"][-1]["assessment"] == doc


def test_geimporteerde_lege_ruimtebevestiging_geeft_geen_pass(tmp_path):
    vingerafdruk = bereken_ess05_vingerafdruk(
        BEGRIP,
        TEKST,
        CONTEXT,
        (),
        intentie=ess03_intentie_van_definition(_definition()),
        buren=(),
    )
    lege = {
        "fingerprint": vingerafdruk,
        "contract_version": CONTRACTVERSIE,
        "grond": "Deskundige: geen verwante begrippen in deze context.",
        "actor": "deskundige",
        "at": "2026-09-25T10:00:00+00:00",
    }
    bron = DefinitionRepository(str(tmp_path / "bron.db"))
    bron_id = bron.save(
        _definition(
            metadata={
                "ess05_assessment": None,
                "ess05_buren": [],
                "ess05_lege_ruimte": lege,
            }
        )
    )
    # Positieve controle: lokaal vastgelegd voldoet de bevestiging.
    assert _replay(bron, bron_id)["status"] == "pass"

    doel, did = _importeer(tmp_path, _export(bron, tmp_path / "x.json"))
    assert "ess05_lege_ruimte" not in doel.get(did).metadata
    registratie = doel.get_generation_prompt_data(did) or {}
    # Bewaard als herkenbare, niet-actuele importhistorie (BC-01-H: lijst).
    (bewaard,) = registratie["ess05_lege_ruimte_imported"]
    assert bewaard["lege_ruimte"] == lege
    assert (bewaard["herkomst"], bewaard["actueel"]) == ("import", False)
    assert _replay(doel, did)["status"] != "pass"


# --- BC-01-H: eerdere importbevestiging blijft bij herimport bewaard ---------------


def _lege_ruimte(grond: str, at: str) -> dict[str, Any]:
    return {
        "fingerprint": bereken_ess05_vingerafdruk(
            BEGRIP,
            TEKST,
            CONTEXT,
            (),
            intentie=ess03_intentie_van_definition(_definition()),
            buren=(),
        ),
        "contract_version": CONTRACTVERSIE,
        "grond": grond,
        "actor": "deskundige",
        "at": at,
    }


LEGE_A = _lege_ruimte(
    "Deskundige A: geen verwante begrippen.", "2026-09-20T10:00:00+00:00"
)
LEGE_B = _lege_ruimte("Deskundige B: bevestigd na import.", "2026-09-25T10:00:00+00:00")


def _geimporteerde_lege(registratie: dict[str, Any]) -> list[Any]:
    return [e["lege_ruimte"] for e in registratie["ess05_lege_ruimte_imported"]]


def test_herimport_bewaart_eerdere_en_nieuwe_lege_ruimtebevestiging(tmp_path):
    """Echte route: import (A) → lokaal bevestigd (B, actuele pass) → export →
    herimport. A en B blijven beide herkenbare importhistorie; actueel is leeg."""
    bron = DefinitionRepository(str(tmp_path / "bron.db"))
    bron.save(
        _definition(
            metadata={
                "ess05_assessment": None,
                "ess05_buren": [],
                "ess05_lege_ruimte": LEGE_A,
            }
        )
    )
    doel, did = _importeer(tmp_path, _export(bron, tmp_path / "x.json"))

    # Positieve lokale route blijft intact: een lokale bevestiging is actueel.
    geladen = doel.get(did)
    geladen.metadata["ess05_lege_ruimte"] = LEGE_B
    doel.save(geladen)
    assert _replay(doel, did)["status"] == "pass"
    lokaal = doel.get_generation_prompt_data(did) or {}
    assert lokaal["ess05_lege_ruimte"] == LEGE_B
    assert LEGE_A["grond"] in json.dumps(lokaal, ensure_ascii=False)

    derde, did3 = _importeer(tmp_path, _export(doel, tmp_path / "y.json"), "derde.db")
    registratie = derde.get_generation_prompt_data(did3) or {}
    assert "ess05_lege_ruimte" not in registratie
    # Vormonafhankelijk: beide bevestigingen staan nog in de registratie.
    bewaard = json.dumps(registratie, ensure_ascii=False)
    assert LEGE_A["grond"] in bewaard, "eerdere importbevestiging A verloren"
    assert LEGE_B["grond"] in bewaard
    assert _geimporteerde_lege(registratie) == [LEGE_A, LEGE_B]
    for entry in registratie["ess05_lege_ruimte_imported"]:
        assert (entry["herkomst"], entry["actueel"]) == ("import", False)
    assert "ess05_lege_ruimte" not in derde.get(did3).metadata
    assert _replay(derde, did3)["status"] != "pass"


def test_enkel_bewaard_document_uit_eerdere_vorm_blijft_behouden():
    """Compatibiliteit: `ess05_lege_ruimte_imported` als enkel document (vorm
    van vóór BC-01-H) wordt historie-item; niets gaat verloren."""
    registratie = {
        "ess05_lege_ruimte_imported": deepcopy(LEGE_A),
        "ess05_lege_ruimte": deepcopy(LEGE_B),
    }
    neutraliseer_geimporteerde_ess05(registratie, versie=3, nu="2026-09-25T12:00:00")
    assert "ess05_lege_ruimte" not in registratie
    bewaard = json.dumps(registratie, ensure_ascii=False)
    assert LEGE_A["grond"] in bewaard, "eerdere importbevestiging A verloren"
    assert _geimporteerde_lege(registratie) == [LEGE_A, LEGE_B]
    oud, nieuw = registratie["ess05_lege_ruimte_imported"]
    assert (oud["herkomst"], oud["actueel"]) == ("import", False)
    assert "superseded_at" not in oud  # geen verzonnen tijdstip
    assert (nieuw["superseded_at"], nieuw["superseded_on_version"]) == (
        "2026-09-25T12:00:00",
        3,
    )


def test_herhaald_normaliseren_bouwt_geen_duplicaten_op():
    registratie = {
        "ess05_lege_ruimte_imported": deepcopy(LEGE_A),
        "ess05_lege_ruimte": deepcopy(LEGE_B),
        "ess05_assessment": {"status": "assessed", "fingerprint": "f"},
    }
    neutraliseer_geimporteerde_ess05(registratie, versie=1, nu="t1")
    eerste = deepcopy(registratie)
    neutraliseer_geimporteerde_ess05(registratie, versie=2, nu="t2")
    assert registratie == eerste
    assert len(registratie["ess05_assessment_history"]) == 1


def test_zelfde_bevestiging_opnieuw_aangeleverd_geeft_geen_duplicaat():
    registratie = {"ess05_lege_ruimte": deepcopy(LEGE_A)}
    neutraliseer_geimporteerde_ess05(registratie, versie=1, nu="t1")
    registratie["ess05_lege_ruimte"] = deepcopy(LEGE_A)  # herimport, ongewijzigd
    neutraliseer_geimporteerde_ess05(registratie, versie=2, nu="t2")
    assert _geimporteerde_lege(registratie) == [LEGE_A]
