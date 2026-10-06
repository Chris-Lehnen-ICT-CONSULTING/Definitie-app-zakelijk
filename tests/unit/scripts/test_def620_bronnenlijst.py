"""DEF-620 (RAG fase 3): bronnenlijst ophalen en importeren."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from services.rag.bronnen_schema import zorg_voor_bronnen_schema
from tests.unit.scripts.test_def620_rag_scripts import _laad, _NepEmbedder
from tests.unit.services.rag.test_def620_wetparsers import BWB_XML, EU_OJ

# EU_OJ noemt de verordening, zodat de identiteitscontrole slaagt.
EU_OJ = EU_OJ.replace(
    '<div id="rct_1">',
    '<p class="oj-doc-ti">Verordening (EU) 2016/679</p><div id="rct_1">',
)
OP_XML = """<?xml version="1.0" encoding="utf-8"?>
<officiele-publicatie><metadata>
<meta name="OVERHEIDop.externMetadataRecord"
 content="https://zoek.officielebekendmakingen.nl/stb-2026-56/metadata.xml"/>
</metadata><artikel><kop><nr>1.1.1</nr></kop><al>Tekst.</al></artikel>
</officiele-publicatie>"""

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]

LIJST = """
bronnen:
  - sleutel: testwet
    formaat: bwb
    bwb_id: BWBR0009999
    versie: "2026-01-01"
    collectie: "Testwet (versie 1-1-2026)"
    wet_regeling: "Testwet (versie 1-1-2026)"
    rechtsgebied: penitentiair_recht
  - sleutel: avg
    formaat: eu
    celex: 32016R0679
    collectie: "AVG"
    wet_regeling: "AVG"
    rechtsgebied: europees_recht
"""


@pytest.fixture
def bl(tmp_path, monkeypatch):
    mod = _laad("rag_bronnenlijst", monkeypatch)
    lijst = tmp_path / "bronnenlijst.yaml"
    lijst.write_text(LIJST, encoding="utf-8")
    return mod, lijst, tmp_path


def _nep_download(url, formaat):
    return (EU_OJ if formaat == "eu" else BWB_XML).encode("utf-8")


def test_echte_bronnenlijst_is_geldig(monkeypatch):
    mod = _laad("rag_bronnenlijst", monkeypatch)
    bronnen = mod.lees_lijst(ROOT / "config" / "bronnenlijst.yaml")
    assert len(bronnen) == 21
    sleutels = {b.sleutel for b in bronnen}
    assert {"sv-geldend", "sv-nieuw", "sr", "avg", "eidas", "bw1", "bw2"} <= sleutels
    # wijzigingswetten bewust niet als eigen collectie
    assert not {b.bwb_id for b in bronnen} & {
        "BWBR0026180", "BWBR0043990", "BWBR0048252",
    }  # fmt: skip
    sv = next(b for b in bronnen if b.sleutel == "sv-geldend")
    assert sv.urls == (
        (
            "https://repository.officiele-overheidspublicaties.nl/bwb/"
            "BWBR0001903/2026-07-01_0/xml/BWBR0001903_2026-07-01_0.xml"
        ),
    )


@pytest.mark.parametrize(
    ("vervang", "fout"),
    [
        (("sleutel: avg", "sleutel: testwet"), "dubbele sleutel"),
        (("BWBR0009999", "BWBR99"), "ongeldig bwb_id"),
        (("celex: 32016R0679", "celex: ../x"), "ongeldige celex"),
        (
            ('collectie: "AVG"', 'collectie: "Testwet (versie 1-1-2026)"'),
            "dubbele collectie",
        ),
    ],
)
def test_ongeldige_bronnenlijst(bl, vervang, fout):
    mod, lijst, _tmp = bl
    lijst.write_text(LIJST.replace(*vervang), encoding="utf-8")
    with pytest.raises(mod.BronError, match=fout):
        mod.lees_lijst(lijst)


def test_bestandsnaam_met_pad_geweigerd(bl):
    mod, lijst, _tmp = bl
    lijst.write_text(
        "bronnen:\n  - sleutel: x\n    formaat: op\n    urls: [https://x/y.xml]\n"
        "    bestanden: [../buiten.xml]\n    collectie: X\n    wet_regeling: X\n"
        "    rechtsgebied: strafrecht\n",
        encoding="utf-8",
    )
    with pytest.raises(mod.BronError, match="ongeldige bestandsnaam"):
        mod.lees_lijst(lijst)


def test_controle_inhoud_weigert_verkeerd_document(bl):
    mod, lijst, _tmp = bl
    testwet, avg = mod.lees_lijst(lijst)
    mod.controleer_inhoud(testwet, BWB_XML.encode())
    mod.controleer_inhoud(avg, EU_OJ.encode())
    with pytest.raises(mod.BronError, match="geen BWB-toestand"):
        mod.controleer_inhoud(
            testwet, BWB_XML.replace("BWBR0009999", "BWBR0001111").encode()
        )
    with pytest.raises(mod.BronError, match="niet versie"):
        mod.controleer_inhoud(
            testwet, BWB_XML.replace("2026-01-01", "2025-01-01").encode()
        )
    with pytest.raises(mod.BronError, match="geen EU-XHTML"):
        mod.controleer_inhoud(avg, b'<html xmlns="http://www.w3.org/1999/xhtml"/>')
    with pytest.raises(mod.BronError, match="geen geldige XML"):
        mod.controleer_inhoud(avg, b"<html>")


def test_ophalen_schrijft_bestanden_en_manifest_en_slaat_bestaande_over(bl):
    mod, lijst, tmp = bl
    bronnen = mod.lees_lijst(lijst)
    map_ = tmp / "xml"
    manifest = mod.ophalen(bronnen, map_, download=_nep_download)
    namen = sorted(p.name for p in map_.iterdir())
    assert namen == [
        "BWBR0009999_2026-01-01_0.xml",
        "EU_32016R0679.xhtml",
        "manifest.json",
    ]
    assert (
        manifest["EU_32016R0679.xhtml"]["sha256"]
        == hashlib.sha256(EU_OJ.encode()).hexdigest()
    )

    def mag_niet(url, formaat):
        raise AssertionError("bestaand bestand opnieuw opgehaald")

    mod.ophalen(bronnen, map_, download=mag_niet)  # alles aanwezig


def test_ophalen_bewaart_niets_bij_verkeerde_download(bl):
    mod, lijst, tmp = bl
    bronnen = mod.lees_lijst(lijst)
    with pytest.raises(mod.BronError):
        mod.ophalen(bronnen, tmp / "xml", download=lambda url, f: b"<foutpagina/>")
    assert not (tmp / "xml" / "BWBR0009999_2026-01-01_0.xml").exists()


@pytest.fixture
def import_klaar(bl, monkeypatch):
    mod, lijst, tmp = bl
    bronnen = mod.lees_lijst(lijst)
    map_ = tmp / "xml"
    mod.ophalen(bronnen, map_, download=_nep_download)
    imp = _laad("rag_importeer_officiele_publicatie", monkeypatch)
    monkeypatch.setattr(imp, "EmbeddingService", _NepEmbedder)
    db = tmp / "bronnen.db"
    zorg_voor_bronnen_schema(db)
    return mod, bronnen, map_, imp, db


def test_importeren_per_bron_een_collectie_met_bronmetadata(import_klaar):
    mod, bronnen, map_, imp, db = import_klaar
    assert mod.importeren(bronnen, str(db), map_, module=imp) == 0
    conn = sqlite3.connect(db)
    rijen = conn.execute(
        "SELECT k.collection_name, k.metadata_json, COUNT(c.id) FROM rag_collections k "
        "JOIN rag_chunks c ON c.collection_id = k.id GROUP BY k.id ORDER BY k.id"
    ).fetchall()
    types = {r[0] for r in conn.execute("SELECT DISTINCT file_type FROM rag_documents")}
    conn.close()
    assert [(r[0], r[2]) for r in rijen] == [
        ("Testwet (versie 1-1-2026)", 4),  # artikel 1, 5 + 2 begripsbepalingen
        ("AVG", 3),
    ]
    meta = json.loads(rijen[0][1])
    assert meta["type"] == "wetgeving"
    assert meta["rechtsgebied"] == "penitentiair_recht"
    assert meta["bron"]["bwb_id"] == "BWBR0009999"
    assert meta["bron"]["sha256"]["BWBR0009999_2026-01-01_0.xml"]
    assert types == {"application/xml", "application/xhtml+xml"}
    assert mod.importeren(bronnen, str(db), map_, module=imp) == 0  # idempotent


def test_importeren_weigert_ontbrekend_of_gewijzigd_bestand(import_klaar, capsys):
    mod, bronnen, map_, imp, db = import_klaar
    (map_ / "EU_32016R0679.xhtml").write_text(
        EU_OJ + "<!-- anders -->", encoding="utf-8"
    )
    assert mod.importeren(bronnen, str(db), map_, module=imp) == 1
    assert "wijkt af van het manifest" in capsys.readouterr().out
    (map_ / "BWBR0009999_2026-01-01_0.xml").unlink()
    assert mod.importeren(bronnen, str(db), map_, module=imp) == 1
    assert "ontbreekt" in capsys.readouterr().out


def test_cli_onbekende_sleutel_en_ontbrekende_db(bl, capsys):
    mod, lijst, tmp = bl
    assert mod.main(["importeren", "--lijst", str(lijst), "--map", str(tmp)]) == 1
    assert "--db is verplicht" in capsys.readouterr().out
    assert mod.main(["ophalen", "--lijst", str(lijst), "--alleen", "bestaat-niet"]) == 1


def test_importscript_formaat_bwb(tmp_path, monkeypatch):
    imp = _laad("rag_importeer_officiele_publicatie", monkeypatch)
    monkeypatch.setattr(imp, "EmbeddingService", _NepEmbedder)
    xml = tmp_path / "BWBR0009999_2026-01-01_0.xml"
    xml.write_text(BWB_XML, encoding="utf-8")
    db = tmp_path / "bronnen.db"
    argv = [
        "--db", str(db), "--collectie", "T", "--wet-regeling", "T",
        "--rechtsgebied", "Penitentiair recht", "--formaat", "bwb",
        "--bestanden", str(xml),
    ]  # fmt: skip
    assert imp.main(argv) == 0
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone()[0] == 4
    conn.close()
    assert imp.importeer(str(db), "T", "T", "strafrecht", [str(xml)], "xyz") == 1


def test_identiteit_op_en_eu(bl):
    mod, lijst, _tmp = bl
    _testwet, avg = mod.lees_lijst(lijst)
    op = mod.Bron(
        sleutel="sv", formaat="op", collectie="c", wet_regeling="w",
        rechtsgebied="strafrecht", urls=("https://zoek.officielebekendmakingen.nl/stb-2026-56.xml",),
        bestanden=("a.xml",),
    )  # fmt: skip
    mod.controleer_inhoud(op, OP_XML.encode(), op.urls[0])
    with pytest.raises(mod.BronError, match="niet stb-2026-57"):
        mod.controleer_inhoud(
            op,
            OP_XML.encode(),
            "https://zoek.officielebekendmakingen.nl/stb-2026-57.xml",
        )
    with pytest.raises(mod.BronError, match="niet CELEX"):
        mod.controleer_inhoud(avg, EU_OJ.replace("2016/679", "2016/680").encode())
    # ander document dat de AVG alleen citeert: titel 2016/680, citaat 2016/679
    citeert = EU_OJ.replace("2016/679", "2016/680").replace(
        "Overweging die niet meegaat.", "Zie Verordening (EU) 2016/679."
    )
    with pytest.raises(mod.BronError, match="niet CELEX"):
        mod.controleer_inhoud(avg, citeert.encode())
    # wijzigingsverordening die de AVG in haar eigen titel noemt
    wijziging = EU_OJ.replace(
        "Verordening (EU) 2016/679",
        "Verordening (EU) 2026/1234 tot wijziging van Verordening (EU) 2016/679",
    )
    with pytest.raises(mod.BronError, match="niet CELEX"):
        mod.controleer_inhoud(avg, wijziging.encode())
    assert mod._eu_identiteit_klopt(
        "32014R0910", "", ["VERORDENING (EU) Nr. 910/2014 VAN"]
    )
    with pytest.raises(mod.BronError, match="geen Nederlandse tekst"):
        mod.controleer_inhoud(avg, EU_OJ.replace("Artikel 4", "Article 4").encode())


def test_eu_identiteit_geconsolideerd(bl):
    mod, _lijst, _tmp = bl
    assert mod._eu_identiteit_klopt(
        "02014R0910-20241018", "x 02014R0910 — NL — 18.10.2024 — 002.003 y"
    )
    assert not mod._eu_identiteit_klopt(
        "02014R0910-20241018", "x 02014R0910 — EN — 18.10.2024 y"
    )


def test_onderbroken_ophaalronde_laat_geen_bestand_zonder_manifest(bl):
    mod, lijst, tmp = bl
    bronnen = mod.lees_lijst(lijst)
    map_ = tmp / "xml"

    def tweede_faalt(url, formaat):
        if formaat == "eu":
            raise OSError("netwerk weg")
        return _nep_download(url, formaat)

    with pytest.raises(OSError, match="netwerk weg"):
        mod.ophalen(bronnen, map_, download=tweede_faalt)
    manifest = json.loads((map_ / "manifest.json").read_text(encoding="utf-8"))
    assert list(manifest) == ["BWBR0009999_2026-01-01_0.xml"]
    # hervatten haalt alleen het ontbrekende bestand op
    mod.ophalen(bronnen, map_, download=_nep_download)
    manifest = json.loads((map_ / "manifest.json").read_text(encoding="utf-8"))
    assert sorted(manifest) == ["BWBR0009999_2026-01-01_0.xml", "EU_32016R0679.xhtml"]


def test_bestaand_bestand_zonder_manifest_wordt_gecontroleerd(bl):
    mod, lijst, tmp = bl
    bronnen = mod.lees_lijst(lijst)
    map_ = tmp / "xml"
    map_.mkdir()
    (map_ / "BWBR0009999_2026-01-01_0.xml").write_text("<geen-wet/>", encoding="utf-8")
    with pytest.raises(mod.BronError, match="geen BWB-toestand"):
        mod.ophalen(bronnen[:1], map_, download=_nep_download)
    (map_ / "BWBR0009999_2026-01-01_0.xml").write_text(BWB_XML, encoding="utf-8")
    manifest = mod.ophalen(bronnen[:1], map_, download=_nep_download)
    assert "BWBR0009999_2026-01-01_0.xml" in manifest
    (map_ / "BWBR0009999_2026-01-01_0.xml").write_text(BWB_XML + " ", encoding="utf-8")
    with pytest.raises(mod.BronError, match="wijkt af van het manifest"):
        mod.ophalen(bronnen[:1], map_, download=_nep_download)


def test_importeren_weigert_bestand_zonder_manifestregel(import_klaar, capsys):
    mod, bronnen, map_, imp, db = import_klaar
    (map_ / "manifest.json").write_text("{}", encoding="utf-8")
    assert mod.importeren(bronnen, str(db), map_, module=imp) == 1
    assert "staat niet in het manifest" in capsys.readouterr().out


def test_gewijzigde_bron_in_bestaande_collectie_wordt_geweigerd(import_klaar, capsys):
    mod, bronnen, map_, imp, db = import_klaar
    assert mod.importeren(bronnen[:1], str(db), map_, module=imp) == 0
    pad = map_ / "BWBR0009999_2026-01-01_0.xml"
    gewijzigd = BWB_XML.replace("de directeur", "De directeur").replace(
        "houdt", "oefent"
    )
    pad.write_text(gewijzigd, encoding="utf-8")
    manifest = json.loads((map_ / "manifest.json").read_text(encoding="utf-8"))
    manifest[pad.name]["sha256"] = hashlib.sha256(pad.read_bytes()).hexdigest()
    (map_ / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    capsys.readouterr()
    assert mod.importeren(bronnen[:1], str(db), map_, module=imp) == 2
    assert "bron gewijzigd" in capsys.readouterr().out
