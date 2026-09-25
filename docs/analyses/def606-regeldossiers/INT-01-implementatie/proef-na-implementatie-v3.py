"""DEF-770 ronde 3: offline proef na de tweede Codex-review (proef v2 blijft
ongewijzigd). Nieuw t.o.v. v2: een losse hoofdletter zonder naamcontext is
onzeker ('categorie A. Heeft', 'categorie A. Registratie', 'J. Jansen'); met
titel ('dr. J. Jansen') één zin; de enkele CSV-export draagt de uitkomst.


Uitbreiding van proef v1 (die ongewijzigd blijft):
- servicegevallen v1 plus de twee reviewgevallen van bevinding 2 ('enz. 3
  velden', 'categorie A. Het') en de beschermde naamgevallen (dr. Smit,
  J. Jansen), via beide laadpaden;
- per geval de onderdelen, waarbij compactheid en begrijpelijkheid twee aparte
  open onderdelen met een eigen reden moeten zijn (bevinding 3);
- de gewone opslag-, lees- en exportroute (bevinding 1): record aanmaken,
  teruglezen, tekst wijzigen via update, tekst buiten de laag om wijzigen, en
  export naar JSON, CSV en TXT. Verwacht: dezelfde uitkomst als de service,
  gebonden aan kern en versie, nooit stil geslaagd.
Verwachtingen staan vóór de uitvoering in GEVALLEN en in _opslagproef.

Aanroep vanuit de repositorywortel:
    <python> -B docs/analyses/.../proef-na-implementatie-v3.py <uitvoerpad.json>
"""

import asyncio
import csv
import json
import logging
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
UIT = Path(sys.argv[1]).resolve()
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tests import offline_bootstrap

offline_bootstrap.install()
werk = offline_bootstrap.session_root() / "int01-na-implementatie-v3"
werk.mkdir()
for naam in ("src", "config"):
    (werk / naam).symlink_to(ROOT / naam, target_is_directory=True)
(werk / "data").mkdir()
os.chdir(werk)
sys.path.insert(0, str(ROOT / "src"))
logging.disable(logging.CRITICAL)

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
)
from domain.int01.opslag import tekstvingerafdruk
from services.data_aggregation_service import DataAggregationService
from services.export_service import (
    ExportFormat,
    ExportLevel,
    ExportService,
)
from services.validation.modular_validation_service import (
    ModularValidationService,
)
from toetsregels.cached_manager import CachedToetsregelManager
from toetsregels.manager import ToetsregelManager

ASTRA = (
    "eis die een organisatie moet ondersteunen om migratie van de huidige naar "
    "de toekomstige situatie mogelijk te maken."
)
OPEN = {"compactheid": "review_required", "begrijpelijkheid": "review_required"}
# id, begrip, tekst, verwachte status, verwachte onderdelen (id -> status)
GEVALLEN = [
    (
        "INT01-E01",
        "transitie-eis",
        ASTRA,
        "review_required",
        {"zinsstructuur": "pass", **OPEN},
    ),
    (
        "INT01-E02",
        "object",
        "Object dat gegevens bevat.",
        "review_required",
        {"zinsstructuur": "pass", **OPEN},
    ),
    (
        "INT01-E03",
        "object",
        "Object die gegevens bevat.",
        "review_required",
        {"zinsstructuur": "pass", **OPEN},
    ),
    (
        "INT01-E04",
        "document",
        "Document op naam van dr. Smit.",
        "review_required",
        {"zinsstructuur": "pass", **OPEN},
    ),
    (
        "INT01-E05",
        "object",
        "Wat is dit? Afgebakend object.",
        "fail",
        {"zinsgrens_1": "fail", **OPEN},
    ),
    (
        "INT01-E06",
        "object",
        "Afgebakend object. Heeft vaste vorm.",
        "fail",
        {"zinsgrens_1": "fail", **OPEN},
    ),
    (
        "INT01-E07",
        "veelhoek",
        "Veelhoek met precies\ndrie zijden.",
        "review_required",
        {"zinsstructuur": "pass", **OPEN},
    ),
    (
        "INT01-E08",
        "object",
        "“Afgebakend object. Heeft vaste vorm.”",
        "fail",
        {"zinsgrens_1": "fail", "broncitaat": "review_required", **OPEN},
    ),
    (
        "INT01-EB03",
        "object",
        "Object met gegevens enz. Het wordt geregistreerd.",
        "review_required",
        {"zinsgrens_onzeker_1": "review_required", **OPEN},
    ),
    (
        "INT01-EB04",
        "voertuig",
        "Voertuig voor personenvervoer. Het heeft ten hoogste acht zitplaatsen.",
        "fail",
        {"zinsgrens_1": "fail", **OPEN},
    ),
    # Reviewbevinding 2: onvoldoende context = zichtbaar onzeker met passage.
    (
        "INT01-R2a",
        "object",
        "Object met gegevens enz. 3 velden zijn verplicht.",
        "review_required",
        {"zinsgrens_onzeker_1": "review_required", **OPEN},
    ),
    (
        "INT01-R2b",
        "object",
        "Object in categorie A. Het wordt geregistreerd.",
        "review_required",
        {"zinsgrens_onzeker_1": "review_required", **OPEN},
    ),
    (
        "INT01-R2c",
        "rapport",
        "rapport van J. Jansen over detentie.",
        "review_required",
        {"zinsgrens_onzeker_1": "review_required", **OPEN},
    ),
    (
        "INT01-R3a",
        "object",
        "Object in categorie A. Heeft een vaste vorm.",
        "review_required",
        {"zinsgrens_onzeker_1": "review_required", **OPEN},
    ),
    (
        "INT01-R3b",
        "object",
        "Object in categorie A. Registratie is verplicht.",
        "review_required",
        {"zinsgrens_onzeker_1": "review_required", **OPEN},
    ),
    (
        "INT01-R3c",
        "rapport",
        "rapport van dr. J. Jansen over detentie.",
        "review_required",
        {"zinsstructuur": "pass", **OPEN},
    ),
]


def _delen(detail: dict) -> dict:
    return {p["id"]: p["status"] for p in detail.get("parts", [])}


def _rij(geval: tuple, route: str, res: dict) -> dict:
    gid, _, tekst, verwacht, verwachte_delen = geval
    detail = res["rule_results"].get("INT-01") or {}
    delen = _delen(detail)
    redenen = {p["id"]: p["reason"] for p in detail.get("parts", [])}
    apart = redenen.get("compactheid") != redenen.get("begrijpelijkheid")
    status = res["rule_statuses"].get("INT-01")
    return {
        "id": gid,
        "route": route,
        "tekst": tekst,
        "verwacht": verwacht,
        "status": status,
        "verwachte_onderdelen": verwachte_delen,
        "onderdelen": [
            {k: p[k] for k in ("id", "status", "evidence", "position", "reason")}
            for p in detail.get("parts", [])
        ],
        "compactheid_en_begrijpelijkheid_apart": apart,
        "in_passed_rules": "INT-01" in res["passed_rules"],
        "matches": status == verwacht and delen == verwachte_delen and apart,
    }


def _export(pad: Path, did: int, formaat: ExportFormat) -> Path:
    repo = DefinitieRepository(str(pad))
    service = ExportService(
        repository=repo,
        data_aggregation_service=DataAggregationService(repo),
        export_dir=str(werk / "exports"),
    )
    return Path(
        service.export_multiple_definitions(
            [repo.get_definitie(did)], format=formaat, level=ExportLevel.UITGEBREID
        ).path
    )


def _exportbeeld(pad: Path, did: int) -> dict:
    json_rij = json.loads(_export(pad, did, ExportFormat.JSON).read_text("utf-8"))[
        "definities"
    ][0]["int01_beoordeling"]
    with open(_export(pad, did, ExportFormat.CSV), newline="", encoding="utf-8") as f:
        csv_cel = json.loads(next(csv.DictReader(f))["int01_beoordeling"])
    repo = DefinitieRepository(str(pad))
    enkel = ExportService(
        repository=repo,
        data_aggregation_service=DataAggregationService(repo),
        export_dir=str(werk / "exports"),
    ).export_definitie(definitie_id=did, format=ExportFormat.CSV)
    with open(enkel, newline="", encoding="utf-8") as f:
        enkele_csv_cel = json.loads(next(csv.DictReader(f))["int01_beoordeling"])
    txt = _export(pad, did, ExportFormat.TXT).read_text("utf-8")
    txt_regels = [
        r.strip()
        for r in txt.splitlines()
        if "INT-01" in r or r.strip().startswith("- ")
    ]
    return {
        "json": json_rij,
        "csv_gelijk_aan_json": csv_cel == json_rij and enkele_csv_cel == json_rij,
        "txt_regels": txt_regels,
    }


def _opslagproef() -> dict:
    pad = werk / "data" / "proef.db"
    repo = DefinitieRepository(str(pad))
    uitkomsten = {}
    for gid, begrip, tekst, verwacht, verwachte_delen in GEVALLEN:
        did = repo.create_definitie(
            DefinitieRecord(begrip=f"{begrip}-{gid}", definitie=tekst, categorie="type")
        )
        gelezen = (
            DefinitieRepository(str(pad)).get_definitie(did).get_int01_beoordeling()
        )
        beeld = _exportbeeld(pad, did)
        uitkomsten[gid] = {
            "status": gelezen["status"],
            "applied": gelezen["applied"],
            "binding": gelezen["binding"],
            "matches": (
                gelezen["status"] == verwacht
                and _delen(gelezen) == verwachte_delen
                and gelezen["applied"] is True
                and gelezen["binding"]["tekst_sha256"] == tekstvingerafdruk(tekst)
                and beeld["json"] == gelezen
                and beeld["csv_gelijk_aan_json"]
            ),
            "export": beeld,
        }
    # Tekstwijziging via de gewone updateroute: nieuwe uitkomst, historie.
    did = repo.create_definitie(
        DefinitieRecord(begrip="wijziging", definitie=ASTRA, categorie="type")
    )
    repo.update_definitie(
        did, {"definitie": "Afgebakend object. Heeft vaste vorm."}, "proef"
    )
    na = DefinitieRepository(str(pad)).get_definitie(did)
    nieuw, historie = na.get_int01_beoordeling(), na.get_int01_beoordeling_history()
    update = {
        "status": nieuw["status"],
        "binding": nieuw["binding"],
        "historie": [h["assessment"]["status"] for h in historie],
        "matches": nieuw["status"] == "fail"
        and nieuw["binding"]["version_number"] == 2
        and [h["assessment"]["status"] for h in historie] == ["review_required"],
    }
    # Tekstwijziging buiten de persistentielaag: uitkomst historisch, zichtbaar.
    did2 = repo.create_definitie(
        DefinitieRecord(begrip="buitenom", definitie=ASTRA, categorie="type")
    )
    with sqlite3.connect(pad) as conn:
        conn.execute(
            "UPDATE definities SET definitie = ? WHERE id = ?", ("Ander. Tekst.", did2)
        )
    buitenom = DefinitieRepository(str(pad)).get_definitie(did2).get_int01_beoordeling()
    beeld2 = _exportbeeld(pad, did2)
    buiten = {
        "applied": buitenom["applied"],
        "applied_reason": buitenom["applied_reason"],
        "txt_toont_niet_toegepast": any(
            "niet toegepast" in r for r in beeld2["txt_regels"]
        ),
        "matches": buitenom["applied"] is False
        and beeld2["json"]["applied"] is False
        and any("niet toegepast" in r for r in beeld2["txt_regels"]),
    }
    return {"per_geval": uitkomsten, "update": update, "buiten_de_laag_om": buiten}


async def main() -> int:
    rijen = []
    for route, manager in (
        ("manager", ToetsregelManager()),
        ("cache", CachedToetsregelManager()),
    ):
        svc = ModularValidationService(manager, None, None)
        for geval in GEVALLEN:
            res = await svc.validate_definition(
                begrip=geval[1], text=geval[2], context={}
            )
            rijen.append(_rij(geval, route, res))
    opslag = _opslagproef()
    rapport = {
        "basis": "26f2374d302fc66fc0b12ed29dc34585f7c0a5c3 + niet-gecommitte DEF-770-diff (ronde 3)",
        "python": sys.version,
        "offline_gate": offline_bootstrap.gate_is_actief(),
        "scope": "service manager/cache + gewone opslag/lees/exportroute (JSON, CSV, TXT); geen live model, geen UI-browser, geen normvalidatie",
        "rows": rijen,
        "opslag": opslag,
        "alle_serviceverwachtingen_gehaald": all(r["matches"] for r in rijen),
        "alle_opslagverwachtingen_gehaald": all(
            v["matches"] for v in opslag["per_geval"].values()
        )
        and opslag["update"]["matches"]
        and opslag["buiten_de_laag_om"]["matches"],
        "nooit_int01_in_passed_rules": not any(r["in_passed_rules"] for r in rijen),
    }
    with UIT.open("x", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2, default=str)
    ok = (
        rapport["alle_serviceverwachtingen_gehaald"]
        and rapport["alle_opslagverwachtingen_gehaald"]
        and rapport["nooit_int01_in_passed_rules"]
    )
    return 0 if ok else 1


raise SystemExit(asyncio.run(main()))
