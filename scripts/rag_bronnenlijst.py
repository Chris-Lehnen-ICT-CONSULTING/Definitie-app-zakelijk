"""Bronnenlijst van de bronbibliotheek: ophalen en importeren (DEF-620, RAG fase 3).

Leest ``config/bronnenlijst.yaml``. Twee stappen, elk apart te draaien:

``ophalen``
    Download per bron het XML/XHTML-bestand naar de bronnenmap (standaard
    ``data/bronnen/xml``, niet in git) en schrijf ``manifest.json`` (url,
    bestand, sha256, bytes, tijdstip). Controleert vóór het opslaan het formaat
    (BWB-toestand met het juiste BWB-id en de juiste versie, officiële
    publicatie, EU-XHTML met artikelen). Een bestaand bestand wordt alleen
    vervangen met ``--opnieuw``.
``importeren``
    Importeer per bron de bestanden uit de bronnenmap in een eigen collectie
    (``scripts/rag_importeer_officiele_publicatie.importeer``). ``--droog``
    parst en telt alleen. Een compleet aanwezig document wordt overgeslagen,
    een incompleet document stopt de import (exitcode 2).

Voorbeeld:
    python scripts/rag_bronnenlijst.py ophalen
    python scripts/rag_bronnenlijst.py importeren --db <kopie van bronnen.db> --droog
    python scripts/rag_bronnenlijst.py importeren --db data/bronnen.db --alleen sr pbw
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LIJST = ROOT / "config" / "bronnenlijst.yaml"
BRONNENMAP = ROOT / "data" / "bronnen" / "xml"

BWB_URL = (
    "https://repository.officiele-overheidspublicaties.nl/bwb/"
    "{id}/{versie}_0/xml/{id}_{versie}_0.xml"
)
CELLAR_URL = "http://publications.europa.eu/resource/celex/{celex}"
TIMEOUT = 120


class BronError(RuntimeError):
    """Een bron is niet op te halen of heeft niet het verwachte formaat."""


@dataclass(frozen=True)
class Bron:
    sleutel: str
    formaat: str
    collectie: str
    wet_regeling: str
    rechtsgebied: str
    urls: tuple[str, ...]
    bestanden: tuple[str, ...]
    bwb_id: str | None = None
    versie: str | None = None
    celex: str | None = None
    extra: dict = field(default_factory=dict)

    def bronmetadata(self) -> dict:
        meta = {"formaat": self.formaat, "urls": list(self.urls)}
        for sleutel in ("bwb_id", "versie", "celex"):
            if getattr(self, sleutel):
                meta[sleutel] = getattr(self, sleutel)
        return meta


def lees_lijst(pad: Path = LIJST) -> list[Bron]:
    """Lees en valideer de bronnenlijst."""
    data = yaml.safe_load(pad.read_text(encoding="utf-8")) or {}
    bronnen: list[Bron] = []
    gezien: set[str] = set()
    for item in data.get("bronnen", []):
        sleutel = item["sleutel"]
        formaat = item["formaat"]
        if sleutel in gezien:
            raise BronError(f"dubbele sleutel in bronnenlijst: {sleutel}")
        gezien.add(sleutel)
        if formaat == "bwb":
            bwb_id, versie = item["bwb_id"], str(item["versie"])
            if not re.fullmatch(r"BWBR\d{7}", bwb_id) or not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}", versie
            ):
                raise BronError(f"{sleutel}: ongeldig bwb_id of versie")
            url = BWB_URL.format(id=bwb_id, versie=versie)
            urls, bestanden = (url,), (url.rsplit("/", 1)[1],)
        elif formaat == "eu":
            celex = str(item["celex"])
            if not re.fullmatch(r"[0-9A-Z]{10,11}(-\d{8})?", celex):
                raise BronError(f"{sleutel}: ongeldige celex {celex!r}")
            urls, bestanden = (CELLAR_URL.format(celex=celex),), (f"EU_{celex}.xhtml",)
        elif formaat == "op":
            urls = tuple(item["urls"])
            bestanden = tuple(item["bestanden"])
            if len(urls) != len(bestanden) or not urls:
                raise BronError(f"{sleutel}: urls en bestanden horen bij elkaar")
        else:
            raise BronError(f"{sleutel}: onbekend formaat {formaat!r}")
        for naam in bestanden:
            if Path(naam).name != naam or naam.startswith("."):
                raise BronError(f"{sleutel}: ongeldige bestandsnaam {naam!r}")
        bronnen.append(
            Bron(
                sleutel=sleutel,
                formaat=formaat,
                collectie=item["collectie"],
                wet_regeling=item["wet_regeling"],
                rechtsgebied=item["rechtsgebied"],
                urls=urls,
                bestanden=bestanden,
                bwb_id=item.get("bwb_id"),
                versie=str(item["versie"]) if item.get("versie") else None,
                celex=str(item["celex"]) if item.get("celex") else None,
            )
        )
    if len({b.collectie for b in bronnen}) != len(bronnen):
        raise BronError("dubbele collectienaam in bronnenlijst")
    return bronnen


def _download(url: str, formaat: str) -> bytes:
    headers = {"User-Agent": "Definitie-app bronbibliotheek (DEF-620)"}
    if formaat == "eu":
        headers |= {"Accept": "application/xhtml+xml", "Accept-Language": "nld"}
    verzoek = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(verzoek, timeout=TIMEOUT) as antwoord:
        return antwoord.read()


def controleer_inhoud(bron: Bron, inhoud: bytes) -> None:
    """Controleer dat de download het verwachte document is."""
    try:
        wortel = ET.fromstring(inhoud)
    except ET.ParseError as exc:
        raise BronError(f"{bron.sleutel}: geen geldige XML ({exc})") from exc
    if bron.formaat == "bwb":
        verwacht = f"/{bron.bwb_id}/{bron.versie}/"
        if wortel.tag != "toestand" or wortel.get("bwb-id") != bron.bwb_id:
            raise BronError(f"{bron.sleutel}: geen BWB-toestand van {bron.bwb_id}")
        if verwacht not in (wortel.get("bwb-ng-vast-deel") or "") + "/":
            raise BronError(f"{bron.sleutel}: toestand is niet versie {bron.versie}")
    elif bron.formaat == "op":
        if wortel.tag != "officiele-publicatie":
            raise BronError(f"{bron.sleutel}: geen officiële publicatie")
    else:
        ns = "{http://www.w3.org/1999/xhtml}"
        artikelen = [
            d
            for d in wortel.iter(f"{ns}div")
            if re.match(r"^art_[^.]+$", d.get("id") or "")
        ]
        if wortel.tag != f"{ns}html" or not artikelen:
            raise BronError(f"{bron.sleutel}: geen EU-XHTML met artikelen")


def ophalen(
    bronnen: list[Bron], map_: Path, opnieuw: bool = False, download=_download
) -> dict:
    """Haal de bestanden op; geeft het bijgewerkte manifest."""
    map_.mkdir(parents=True, exist_ok=True)
    manifest_pad = map_ / "manifest.json"
    manifest = (
        json.loads(manifest_pad.read_text(encoding="utf-8"))
        if manifest_pad.exists()
        else {}
    )
    for bron in bronnen:
        for url, naam in zip(bron.urls, bron.bestanden, strict=True):
            doel = map_ / naam
            if doel.exists() and not opnieuw:
                print(f"aanwezig: {naam}")
                continue
            inhoud = download(url, bron.formaat)
            controleer_inhoud(bron, inhoud)
            tijdelijk = doel.with_name(f".{naam}.download")
            tijdelijk.write_bytes(inhoud)
            tijdelijk.replace(doel)
            manifest[naam] = {
                "sleutel": bron.sleutel,
                "url": url,
                "sha256": hashlib.sha256(inhoud).hexdigest(),
                "bytes": len(inhoud),
                "opgehaald_op": datetime.now().isoformat(timespec="seconds"),
            }
            print(f"opgehaald: {naam} ({len(inhoud)} bytes)")
    manifest_pad.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def _importmodule():
    pad = ROOT / "scripts" / "rag_importeer_officiele_publicatie.py"
    spec = importlib.util.spec_from_file_location(
        "rag_importeer_officiele_publicatie", pad
    )
    if spec is None or spec.loader is None:
        raise BronError(f"importscript niet te laden: {pad}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def importeren(
    bronnen: list[Bron], db: str, map_: Path, droog: bool = False, module=None
) -> int:
    """Importeer elke bron in zijn eigen collectie; stopt bij de eerste fout."""
    module = module or _importmodule()
    manifest_pad = map_ / "manifest.json"
    manifest = (
        json.loads(manifest_pad.read_text(encoding="utf-8"))
        if manifest_pad.exists()
        else {}
    )
    for bron in bronnen:
        paden = [map_ / naam for naam in bron.bestanden]
        ontbreekt = [p.name for p in paden if not p.is_file()]
        if ontbreekt:
            print(
                f"FOUT {bron.sleutel}: bestand ontbreekt {ontbreekt}; eerst 'ophalen'"
            )
            return 1
        for pad in paden:
            verwacht = manifest.get(pad.name, {}).get("sha256")
            if verwacht and hashlib.sha256(pad.read_bytes()).hexdigest() != verwacht:
                print(f"FOUT {bron.sleutel}: {pad.name} wijkt af van het manifest")
                return 1
        print(f"== {bron.sleutel}: {bron.collectie}")
        meta = bron.bronmetadata() | {
            "sha256": {p.name: manifest.get(p.name, {}).get("sha256") for p in paden}
        }
        code = module.importeer(
            db,
            bron.collectie,
            bron.wet_regeling,
            bron.rechtsgebied,
            [str(p) for p in paden],
            formaat=bron.formaat,
            droog=droog,
            bron=meta,
        )
        if code != 0:
            return code
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("stap", choices=("ophalen", "importeren"))
    ap.add_argument("--lijst", type=Path, default=LIJST)
    ap.add_argument("--map", type=Path, default=BRONNENMAP, dest="map_")
    ap.add_argument("--alleen", nargs="+", help="alleen deze sleutels")
    ap.add_argument("--opnieuw", action="store_true", help="ophalen: overschrijf")
    ap.add_argument("--db", help="importeren: bronnenbestand (bijv. data/bronnen.db)")
    ap.add_argument("--droog", action="store_true", help="importeren: alleen tellen")
    args = ap.parse_args(argv)
    try:
        bronnen = lees_lijst(args.lijst)
    except (BronError, KeyError, yaml.YAMLError) as exc:
        print(f"FOUT in bronnenlijst: {exc}")
        return 1
    if args.alleen:
        onbekend = set(args.alleen) - {b.sleutel for b in bronnen}
        if onbekend:
            print(f"FOUT: onbekende sleutel(s) {sorted(onbekend)}")
            return 1
        bronnen = [b for b in bronnen if b.sleutel in args.alleen]
    if args.stap == "ophalen":
        try:
            ophalen(bronnen, args.map_, opnieuw=args.opnieuw)
        except (BronError, OSError) as exc:
            print(f"FOUT: {exc}")
            return 1
        return 0
    if not args.db:
        print("FOUT: --db is verplicht bij importeren")
        return 1
    return importeren(bronnen, args.db, args.map_, droog=args.droog)


if __name__ == "__main__":
    raise SystemExit(main())
