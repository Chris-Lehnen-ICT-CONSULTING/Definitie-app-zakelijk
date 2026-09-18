#!/usr/bin/env python3
"""Bouwt het CON-02 deskundige-acceptatiepakket (2026-09-16).

Leest uitsluitend bestaande bronnen (nooit gewijzigd) en schrijft in een
doelmap. Geen productiecode, geen ketenuitvoering, geen menselijke oordelen.
Herhaalbaar: dezelfde invoer geeft dezelfde uitvoer.

Aanroep:
  python3 bouw_pakket.py [--hist DIR] [--uit DIR] [--dry-run]

Bronnen:
  --hist DIR   historische praktijkmap (layout praktijk-20260914-v1: 5 bestanden
               + fixtures/); de twee kruisreviewbestanden komen uit de repo.
  (geen)       de snapshots in basis/ en bronfixtures/ van dit pakket.
  Van alle 7 gelezen bronbestanden wordt een byte-identieke snapshot in
  <doel>/basis/ gezet; de oorspronkelijke paden zijn alleen provenance.

Doel:
  --uit DIR    doelmap. Standaard: de eerstvolgende NIET-bestaande versiemap
               con02-acceptatie-20260916-vN naast dit pakket.
  Er bestaat GEEN overschrijfroute: een doelmap die al inhoud heeft wordt
  altijd geweigerd, ongeacht die inhoud. Bestaande pakketten (en dus ook
  ingevulde formulieren/oordelen) kunnen door dit script nooit worden
  gewijzigd of genulstelde. Onbekende opties worden geweigerd.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent
REPO = PKG.parents[2]
KRUIS_REL = "docs/analyses/con02-20260915-kruisreview"

sys.path.insert(0, str(PKG))
from verifieer_pakket import OORDEELBLOK_LEEG  # één template voor bouwer én verifier

BASIS_COMMIT = "29b0900d4a7f501849d0963616b3f78106299aa3"
PAKKET_DATUM = "2026-09-16"
EERSTE_ZES = ["C02-P01", "C02-P02", "C02-P04", "C02-P11", "C02-P16", "C02-P31"]

# naam -> (bestandsnaam, herkomst: "hist" | "repo")
BRONNEN = {
    "besluiten_v3": ("besluiten-20260915-v3.md", "repo"),
    "register_kruisreview_v2": ("casusregister-geintegreerd-v2.json", "repo"),
    "actief_pakket_v1": ("actief-pakket-v1.json", "hist"),
    "praktijktestgevallen_v4": ("praktijktestgevallen-v4.md", "hist"),
    "bronmanifest_v3": ("bronmanifest-v3.json", "hist"),
    "register_praktijk_v6": ("casusregister-geintegreerd-v6.json", "hist"),
    "retrieval_fixtures_v1": ("retrieval-fixtures-v1.json", "hist"),
}

# Hash-recept uit het historische bouwscript
# (gth-20260914-v1/bouw-casusregister-codex-v1.py, regel 72).
SCENARIO_HASH_VELDEN = ["scenario", "title", "input", "given", "source_ids"]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def scenario_hash(case: dict) -> str:
    sub = {k: v for k, v in case.items() if k in SCENARIO_HASH_VELDEN}
    return sha256_bytes(
        json.dumps(sub, sort_keys=True, ensure_ascii=False).encode("utf-8")
    )


def stop(msg: str) -> None:
    raise SystemExit(f"GEWEIGERD: {msg}")


# --------------------------------------------------------------------------
# Passages: exacte substrings uit de fixturebytes; de bouwer faalt als een
# passage niet letterlijk in het bestand staat.
# --------------------------------------------------------------------------
def sectie(tekst: str, kop: str) -> str:
    """Tekst tussen een markdown-kop en de volgende kop van gelijk niveau."""
    m = re.search(rf"^{re.escape(kop)}\n(.*?)(?=^## |\Z)", tekst, re.S | re.M)
    if not m:
        stop(f"kop niet gevonden: {kop!r}")
    return m.group(1).strip()


def regel_met(tekst: str, fragment: str) -> str:
    for r in tekst.splitlines():
        if fragment in r:
            return r
    stop(f"regel niet gevonden: {fragment!r}")
    return ""


def passages_voor(source_id: str, tekst: str, chunks: dict) -> list[dict]:
    """Geeft [(locator, passage)] per bron; passage is letterlijke broninhoud."""
    if source_id in ("S-AWB13", "S-RENAME"):
        return [
            {"locator": c["locator"], "passage": c["chunk_text"]}
            for c in chunks.values()
            if c["source_id"] == "S-AWB13"
        ]
    if source_id == "S-BW3":
        return [
            {"locator": c["locator"], "passage": c["chunk_text"]}
            for c in chunks.values()
            if c["source_id"] == "S-BW3"
        ]
    if source_id == "S-AWB32":
        return [
            {
                "locator": "artikel 3:2",
                "passage": regel_met(tekst, "Bij de voorbereiding"),
            }
        ]
    if source_id == "S-UPLOAD32":
        return [
            {
                "locator": "beschrijvende kop (geen wettekst)",
                "passage": tekst.splitlines()[0],
            },
            {
                "locator": "wetszin onder beschrijvende kop",
                "passage": regel_met(tekst, "Bij de voorbereiding"),
            },
        ]
    if source_id == "M-UPLOAD":
        return [
            {
                "locator": "artikeltekst (GEMUTEERD)",
                "passage": regel_met(tekst, "Bij de voorbereiding"),
            }
        ]
    if source_id in ("S-WIKI", "M-WIKI"):
        return [
            {
                "locator": "frontmatter: confidence",
                "passage": regel_met(tekst, "confidence:"),
            },
            {
                "locator": "frontmatter: lifecycle",
                "passage": regel_met(tekst, "lifecycle:"),
            },
            {"locator": "Definitie", "passage": sectie(tekst, "## Definitie")},
        ]
    if source_id == "S-WIKISOURCE":
        return [
            {"locator": "Samenvatting", "passage": sectie(tekst, "## Samenvatting")}
        ]
    if source_id == "S-RAW":
        return [
            {
                "locator": "The core idea (eerste alinea)",
                "passage": sectie(tekst, "## The core idea").split("\n\n")[0],
            },
            {
                "locator": "Architecture / Raw sources",
                "passage": regel_met(tekst, "**Raw sources**"),
            },
        ]
    if source_id == "M-RAW":
        return [
            {
                "locator": "Architecture / Raw sources (GEMUTEERD)",
                "passage": regel_met(tekst, "**Raw sources**"),
            }
        ]
    if source_id == "S-RAWREGISTER":
        return [
            {
                "locator": "rij 2026-07-08-karpathy-llm-wiki-gist.md",
                "passage": regel_met(tekst, "| 2026-07-08-karpathy"),
            }
        ]
    if source_id == "S-ASTRA-ACTUEEL":
        return [
            {
                "locator": "tabel: Regel (letterlijk)",
                "passage": sectie(tekst, "## Regel — letterlijk"),
            },
            {
                "locator": "tabel: Toelichting (samenvatting, geen citaat)",
                "passage": sectie(tekst, "## Toelichting — samengevat"),
            },
        ]
    stop(f"geen passagerecept voor {source_id}")
    return []


KIND_LABEL = {
    "primary_law_transcription": "primaire wetstranscriptie (echt)",
    "existing_local_upload": "bestaand lokaal uploadbestand (echt, zonder eigen herkomst)",
    "derived_wiki": "afgeleide wikipagina (echt, lokaal)",
    "derived_source_page": "afgeleide bronpagina (echt, lokaal)",
    "historical_primary_capture": "historische primaire capture (echt, lokaal)",
    "intentional_test_mutation": "SYNTHETISCHE MUTANT — bewust gewijzigde testkopie, geen echte revisie",
    "identical_bytes_renamed": "hernoemde byte-identieke kopie (testconstructie)",
    "local_register_excerpt": "uittreksel uit lokaal bronregister (echt, gedeeltelijk)",
    "primary_norm_read_short_quote_and_summary": "normbron: kort citaat + samenvatting (geen volledige bronbytes)",
}
SYNTHETISCH_KINDS = ("intentional_test_mutation", "identical_bytes_renamed")


# --------------------------------------------------------------------------
# Huidige laag: projectbesluiten (besluiten-20260915-v3.md) per casus.
# Geen nieuwe oordelen; alleen welke besluiten de historische verwachting raken.
# --------------------------------------------------------------------------
BESLUITEN = {
    "B1": {
        "bron": "besluiten-20260915-v3.md §1",
        "titel": "Deskundige verwijzingsuitzondering — goedgekeurd",
        "kern": "Alleen voor een bestaande bron ZONDER bruikbare hyperlink; bronversie bewaard, stabiele documentidentificatie en exacte vindplaats vastgelegd, deskundige motiveert en accepteert, app toont herkenbaar als uitzondering. Brongezag/toepasselijkheid en betekenissteun worden onverminderd beoordeeld. Nog geen implementatie.",
    },
    "B2": {
        "bron": "besluiten-20260915-v3.md §2",
        "titel": "CON-02-herstel alleen op verzoek — goedgekeurd",
        "kern": "Een CON-02-failure activeert geen automatische herstelpoging. De app toont probleem en onderbouwing; gebruiker vraagt afzonderlijk een voorstel aan, oorspronkelijke tekst blijft bewaard, overgenomen wijziging wordt opnieuw getoetst. Ontbrekend bewijs, transportverlies of onjuiste beoordeling zijn niet vanzelf fouten in de definitiezin.",
    },
    "B3": {
        "bron": "besluiten-20260915-v3.md §3",
        "titel": "Voorlopig geen totaalcijfer — goedgekeurd",
        "kern": "CON-02 krijgt geen numerieke bijdrage; per regel zichtbaar: voldoet / voldoet niet / nog te beoordelen, plus beoordelingsdekking. Ontbrekende beoordelingen worden niet als nul of volledige score ingevuld. Lagere dekking mag geen hogere kwaliteit suggereren.",
    },
}

ALGEMENE_HUIDIGE_LAAG = [
    "B3: CON-02 levert geen cijfer; het te verwachten oordeel is 'voldoet' / 'voldoet niet' / 'nog te beoordelen' per aspect (bronbasis, betekenissteun, verwijskwaliteit). Historische T-teksten die een oordeel benoemen zijn ontwerpverwachtingen, geen vastgestelde uitkomst.",
    "B2: het historische H-veld beschrijft wat een herstelvoorstel zou moeten doen ÁLS de gebruiker er om vraagt. Het is geen automatische stap en geen verwachting dat de app zelf herstelt.",
    "De in casusregister-geintegreerd-v2.json genoemde open beleidspunten (hyperlinkuitzondering, CON02-herstelactivatie, totaalscore/noemer) zijn door besluiten-v3 besloten; de historische documenten blijven intact als momentopname.",
]

SPECIFIEKE_HUIDIGE_LAAG = {
    "C02-P04": [
        "B1: de bron mist versie/URL; een verwijzingsuitzondering is NIET automatisch van toepassing. Zij vereist een bewaarde bronversie, stabiele documentidentificatie, exacte vindplaats én deskundige motivering/acceptatie. Zonder dat blijft herkomst 'nog te beoordelen'; een bestandsnaam of externe manifestkoppeling is geen ontvangen bewijs.",
    ],
    "C02-P05": [
        "B1: de controle-passage S-AWB32 heeft een bruikbare hyperlink (origin-URL in bronmanifest); de uitzondering is hier niet aan de orde. Of de app die koppeling feitelijk heeft ontvangen is niet vastgesteld.",
    ],
    "C02-P28": [
        "B3: de historische 'testscore 0.99' is synthetische scenario-input en blijft ongewijzigd in het historische record. De huidige verwachting toont GEEN totaalcijfer; er is dus ook geen cijfer dat ontbrekend bronbewijs zou kunnen opheffen. Ontbrekend bewijs/review blijft blokkerend voor vaststelling en niet-draft-export (bestaand DEF-630-contract) en vervalt niet.",
        "B2: geen automatische herstelpoging; het ontbreken van bewijs is geen fout in de definitiezin.",
    ],
    "C02-P29": [
        "B1: er bestaat een gerichte primaire online vindplaats (origin-URL S-AWB13); een verwijzing naar alleen de startpagina valt niet onder de uitzondering. De uitzondering is niet automatisch van toepassing.",
        "B2: aanpassing van de verwijzing alleen op verzoek; definitiezin en passage blijven bewaard.",
    ],
    "C02-P30": [
        "B1: niet van toepassing (link en vindplaats aanwezig). Alleen de citeervorm is aan de orde; dat is verwijskwaliteit, geen betekenissteun.",
        "B2: inkorting van de citeervorm alleen als afzonderlijk voorstel op verzoek.",
    ],
    "C02-P31": [
        "B1: de deskundige verwijzingsuitzondering is NIET automatisch van toepassing. Zij geldt uitsluitend voor een bestaande bron zonder bruikbare hyperlink; in deze casus is de gerichte primaire online link beschikbaar (origin-URL S-AWB13, wetten.overheid.nl art. 1:3). Een leeg hyperlinkveld terwijl de link bestaat blijft een verwijskwaliteitsgebrek, tenzij een deskundige expliciet en gemotiveerd anders vaststelt — dat oordeel is niet gegeven.",
        "B2: aanvulling van de hyperlink alleen als afzonderlijk voorstel op verzoek; definitiezin en bronpassage exact behouden.",
        "B3: geen cijfer; verwachte weergave is 'verwijskwaliteit: voldoet niet' naast afzonderlijke bronbasis/betekenissteun-oordelen — als ontwerpverwachting, niet als vastgestelde uitkomst.",
    ],
    "C02-P09": [
        "B3: een retrievalscore (synthetisch 0.99) is geen regelcijfer en geen passagebewijs; het regeloordeel volgt uit de passage, niet uit de score.",
    ],
    "C02-P10": [
        "B3: ontbrekende relevante passage buiten top-5 mag niet leiden tot een positief oordeel door hogere 'dekking' te suggereren; 'nog te beoordelen' of 'voldoet niet' met onderbouwing, nooit stil pass.",
    ],
    "C02-P26": [
        "B3/B2: een boolean reviewed=true is geen beoordelaarsbewijs en geen dekkingsbewijs; er is geen automatische correctie.",
    ],
}


def huidige_laag(case_id: str, route: str) -> list[str]:
    regels = list(SPECIFIEKE_HUIDIGE_LAAG.get(case_id, []))
    if route == "bronverwijzing" and case_id not in SPECIFIEKE_HUIDIGE_LAAG:
        regels.append(
            "B1: alleen van toepassing zonder bruikbare hyperlink; hier niet automatisch."
        )
    return regels + ALGEMENE_HUIDIGE_LAAG


def leeg_expertoordeel() -> dict:
    return {
        "status": "pending",
        "actor": None,
        "datum": None,
        "besluit": None,
        "motivering": None,
        "goldset": False,
    }


# --------------------------------------------------------------------------
# Bron- en doelresolutie met guards
# --------------------------------------------------------------------------
def resolve_bronnen(hist: Path | None) -> tuple[dict[str, tuple[Path, str]], Path, str]:
    """{naam: (leespad, provenance)}, fixturemap, fixture-provenance."""
    out: dict[str, tuple[Path, str]] = {}
    for naam, (bestand, herkomst) in BRONNEN.items():
        if hist is not None:
            p = (REPO / KRUIS_REL / bestand) if herkomst == "repo" else (hist / bestand)
            prov = str(p)
        else:
            p = PKG / "basis" / bestand
            prov = f"{PKG.name}/basis/{bestand} (snapshot; oorspronkelijke provenance in register van {PKG.name})"
        if not p.exists():
            stop(f"bron ontbreekt: {naam} -> {p}")
        out[naam] = (p, prov)
    if hist is not None:
        return out, hist / "fixtures", str(hist / "fixtures")
    return out, PKG / "bronfixtures", f"{PKG.name}/bronfixtures (snapshot)"


def volgende_versiemap() -> Path:
    n = 1
    while (
        PKG.parent / f"con02-acceptatie-{PAKKET_DATUM.replace('-', '')}-v{n}"
    ).exists():
        n += 1
    return PKG.parent / f"con02-acceptatie-{PAKKET_DATUM.replace('-', '')}-v{n}"


def controleer_doel(uit: Path) -> str:
    """Doelmap moet nieuw zijn (of bestaand én leeg). Elke bestaande inhoud wordt
    geweigerd, ongeacht wat erin staat: er bestaat geen overschrijfroute."""
    if uit.exists():
        if not uit.is_dir():
            stop(f"doel {uit} bestaat en is geen map")
        inhoud = sorted(p.name for p in uit.iterdir())
        if inhoud:
            stop(
                f"doel {uit} bestaat al en is niet leeg ({len(inhoud)} items, o.a. {inhoud[:3]}); "
                "bouwen kan uitsluitend naar een nieuwe map — kies --uit <nieuwe map>"
            )
        return f"doel {uit} — bestaande lege map"
    return f"doel {uit} — nieuw"


def schrijf(doel: Path, b: bytes) -> None:
    doel.parent.mkdir(parents=True, exist_ok=True)
    doel.write_bytes(b)


OPTIES = {"--hist", "--uit", "--dry-run"}


def parse_argv(argv: list[str]) -> tuple[Path | None, Path, bool]:
    """(hist, uit, dry). Onbekende opties worden geweigerd; er is geen overschrijfvlag."""
    onbekend = [a for a in argv if a.startswith("--") and a not in OPTIES]
    if onbekend:
        stop(f"onbekende optie(s) {onbekend}; toegestaan: {sorted(OPTIES)}")
    hist = Path(argv[argv.index("--hist") + 1]).resolve() if "--hist" in argv else None
    uit = (
        Path(argv[argv.index("--uit") + 1]).resolve()
        if "--uit" in argv
        else volgende_versiemap()
    )
    return hist, uit, "--dry-run" in argv


# --------------------------------------------------------------------------
def main(argv: list[str]) -> None:
    hist, uit, dry = parse_argv(argv)

    bronnen, fx_map, fx_prov = resolve_bronnen(hist)
    doelbesluit = controleer_doel(uit)
    print(
        "bronnen:",
        (
            "historische map " + str(hist)
            if hist
            else f"snapshots {PKG.name}/basis + bronfixtures"
        ),
    )
    print("doel:   ", doelbesluit)
    if dry:
        print("dry-run: niets geschreven")
        return

    gelezen: dict[str, bytes] = {n: p.read_bytes() for n, (p, _) in bronnen.items()}
    v2 = json.loads(gelezen["register_kruisreview_v2"])
    v6 = json.loads(gelezen["register_praktijk_v6"])
    manifest = json.loads(gelezen["bronmanifest_v3"])
    retrieval = json.loads(gelezen["retrieval_fixtures_v1"])
    chunks = {c["fixture_chunk_id"]: c for c in retrieval["chunks"]}

    v6_p = {c["id"]: c for c in v6["cases"] if c["id"].startswith("C02-P")}
    v2_all = {c["id"]: c for c in v2["cases"]}
    v2_p = {k: v for k, v in v2_all.items() if k.startswith("C02-P")}
    if len(v6_p) != 31 or len(v2_p) != 31 or len(v2_all) != 94:
        stop("verwachte aantallen (31/31/94) kloppen niet")

    # ---- 0. basis-snapshots van de 7 gelezen bronbestanden ------------------
    uit.mkdir(parents=True, exist_ok=True)
    gelezen_bronnen = {}
    for naam, (_p, prov) in bronnen.items():
        bestand, herkomst = BRONNEN[naam]
        schrijf(uit / "basis" / bestand, gelezen[naam])
        gelezen_bronnen[naam] = {
            "snapshot": f"basis/{bestand}",
            "sha256": sha256_bytes(gelezen[naam]),
            "bytes": len(gelezen[naam]),
            "provenance": prov,
            "repo_pad": f"{KRUIS_REL}/{bestand}" if herkomst == "repo" else None,
        }

    # ---- 1. fixtures byte-identiek kopiëren + manifest ----------------------
    manifest_rows = []
    fixture_tekst: dict[str, str] = {}
    for s in manifest["sources"]:
        rel = Path(s["path"]).relative_to("fixtures")
        src = fx_map / rel
        if not src.exists():
            stop(f"fixture ontbreekt: {src}")
        b = src.read_bytes()
        if sha256_bytes(b) != s["sha256"] or len(b) != s["bytes"]:
            stop(f"fixture {s['id']} wijkt af van bronmanifest-v3 (hash/bytes)")
        schrijf(uit / "bronfixtures" / rel, b)
        fixture_tekst[s["id"]] = b.decode("utf-8")
        synthetisch = s["kind"] in SYNTHETISCH_KINDS
        manifest_rows.append(
            {
                "id": s["id"],
                "pakketpad": f"bronfixtures/{rel.as_posix()}",
                "historisch_pad": s["path"],
                "sha256": s["sha256"],
                "bytes": len(b),
                "kind": s["kind"],
                "kind_label": KIND_LABEL[s["kind"]],
                "synthetisch": synthetisch,
                "synthetisch_label": (
                    "SYNTHETISCH — test-mutatie/constructie, geen echte bronrevisie"
                    if synthetisch
                    else "echt bestaand materiaal (kopie/transcriptie, zie verification)"
                ),
                "origin": s["origin"],
                "origin_sha256": s.get("origin_sha256"),
                "source_version": s["source_version"],
                "retrieved_at": s.get("retrieved_at"),
                "locators": s["locators"],
                "verification_historisch": s["verification"],
                "copied_at_historisch": s.get("copied_at"),
            }
        )

    passages: dict[str, list[dict]] = {}
    for row in manifest_rows:
        sid = row["id"]
        ps = passages_voor(sid, fixture_tekst[sid], chunks)
        for p in ps:
            if p["passage"] not in fixture_tekst[sid]:
                stop(f"passage niet letterlijk in fixture {sid}: {p['locator']}")
        passages[sid] = ps
        row["passages"] = ps

    (uit / "bronmanifest-sha256.json").write_text(
        json.dumps(
            {
                "pakket": uit.name,
                "datum": PAKKET_DATUM,
                "basis_commit": BASIS_COMMIT,
                "afgeleid_van": {
                    "snapshot": "basis/bronmanifest-v3.json",
                    "sha256": gelezen_bronnen["bronmanifest_v3"]["sha256"],
                },
                "fixture_provenance": fx_prov,
                "regel": "Alle 13 fixtures zijn byte-identiek gekopieerd; sha256 en bytes zijn gelijk aan basis/bronmanifest-v3.json. Passages zijn letterlijke substrings van de fixturebytes. 'synthetisch: true' = bewust gemaakte testdata, geen echte bronrevisie.",
                "aantal": len(manifest_rows),
                "date_semantics_historisch": manifest["date_semantics"],
                "fixtures": manifest_rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # ---- 2. Acceptatie-register -------------------------------------------
    manifest_by_id = {r["id"]: r for r in manifest_rows}
    cases_out = []
    for cid in sorted(v6_p):
        h6 = v6_p[cid]
        h2 = v2_p[cid]["historisch_record_ongewijzigd"]
        if (
            h6["input"] != h2["input"]
            or h6["given"] != h2["given"]
            or h6["when"] != h2["when"]
        ):
            stop(f"historische invoer v6/v2 verschilt: {cid}")
        sh = scenario_hash(h6)
        if sh != h2["scenario_input_sha256"]:
            stop(f"scenario_input_sha256 niet reproduceerbaar: {cid}")

        recept = None
        if h6.get("retrieval_recipe"):
            rid = (
                h6["retrieval_recipe"]
                if isinstance(h6["retrieval_recipe"], str)
                else h6["retrieval_recipe"].get("id")
            )
            r = retrieval["recipes"].get(rid)
            recept = {
                "id": rid,
                "synthetisch": True,
                "label": "SYNTHETISCHE rangorde/score — geen echte retrievalrun (retrieval-fixtures-v1.json: synthetic_ranking=true, live_retrieval_executed=false)",
                "top_k": r["top_k"] if r else None,
                "min_score": r["min_score"] if r else None,
                "ranked_candidates": r["ranked_candidates"] if r else None,
                "expected_returned_ids": r["expected_returned_ids"] if r else None,
            }

        cases_out.append(
            {
                "id": cid,
                "in_eerste_zes": cid in EERSTE_ZES,
                "historisch_ongewijzigd": {
                    "bron": "basis/casusregister-geintegreerd-v6.json = historisch_record_ongewijzigd in basis/casusregister-geintegreerd-v2.json",
                    "title": h6["title"],
                    "route": h6["route"],
                    "priority": h6["priority"],
                    "source_ids": h6["source_ids"],
                    "input": h6["input"],
                    "given": h6["given"],
                    "when": h6["when"],
                    "retrieval_recipe": h6.get("retrieval_recipe"),
                    "scenario_input_sha256": sh,
                    "hash_recept": "sha256(json.dumps({scenario,title,input,given,source_ids}, sort_keys=True, ensure_ascii=False)) — identiek aan gth-20260914-v1/bouw-casusregister-codex-v1.py r.72",
                },
                "historische_verwachtingen": {
                    "label": "HISTORISCH ONTWERP — geen actuele pass, geen goldset, niet uitgevoerd",
                    "then_v6": h6["then"],
                    "source_based_oracle": h6["source_based_oracle"],
                    "expert_question": h6["expert_question"],
                    "policy_dependency_v6": h6.get("policy_dependency"),
                    "expectation_version_v6": h6.get("expectation_version"),
                    "gth_v1": {
                        "G": h2["G"],
                        "T": h2["T"],
                        "H": h2["H"],
                        "expectation_version": h2["expectation_version"],
                    },
                    "cowork_aanvulling_v1": v2_p[cid].get(
                        "historische_cowork_aanvulling"
                    ),
                    "actuele_verwachting_v1_kruisreview": v2_p[cid][
                        "actuele_verwachting_v1"
                    ],
                    "wijzigingsgrond_kruisreview": v2_p[cid]["wijzigingsgrond"],
                    "execution_historisch": h6["execution"],
                    "gate_historisch": h6["gate"],
                },
                "huidige_laag_projectbesluiten": {
                    "label": "PROJECTBESLUITEN (besluiten-20260915-v3.md) — specificatie, geen implementatieclaim, geen deskundig oordeel",
                    "toelichting": huidige_laag(cid, h6["route"]),
                },
                "bronbinding": [
                    {
                        "id": sid,
                        "pakketpad": manifest_by_id[sid]["pakketpad"],
                        "sha256": manifest_by_id[sid]["sha256"],
                        "kind": manifest_by_id[sid]["kind"],
                        "kind_label": manifest_by_id[sid]["kind_label"],
                        "synthetisch": manifest_by_id[sid]["synthetisch"],
                        "source_version": manifest_by_id[sid]["source_version"],
                        "origin": manifest_by_id[sid]["origin"],
                        "locators": manifest_by_id[sid]["locators"],
                        "passages": passages[sid],
                    }
                    for sid in h6["source_ids"]
                ],
                "retrieval_recept": recept,
                "bewijsstatus": {
                    "fixturebestand_in_pakket": True,
                    "feitelijk_door_app_ontvangen": "NIET VASTGESTELD — geen appketenuitvoering in dit pakket",
                    "modelcontext_vastgelegd": False,
                    "ketenuitvoering": "geen",
                    "modelkwaliteit_bewezen": False,
                },
                "expert": leeg_expertoordeel(),
                "voorbeoordeling_codex_cowork": None,
            }
        )

    overzicht = []
    for cid, c in v2_all.items():
        h = c["historisch_record_ongewijzigd"]
        titel = (
            h.get("title")
            or h.get("scenario_type")
            or h.get("scenario")
            or h.get("theme")
            or ""
        )
        overzicht.append(
            {
                "id": cid,
                "historische_bron": c["historische_bron"],
                "in_acceptatiepakket_31": cid.startswith("C02-P"),
                "categorie": (
                    "praktijkcasus (P)"
                    if cid.startswith("C02-P")
                    else "overige ontwerpcasus"
                ),
                "korte_titel": titel,
                "deskundig_gevalideerd_kruisreview": c["deskundig_gevalideerd"],
                "expert": leeg_expertoordeel(),
            }
        )

    register = {
        "pakket": uit.name,
        "datum": PAKKET_DATUM,
        "status": "Deskundige acceptatie PENDING voor alle casussen; geen goldset; geen appketenuitvoering; geen modelkwaliteit bewezen. Codex/Cowork-voorbeoordeling volgt apart (veld voorbeoordeling_codex_cowork = null).",
        "werkbranch": "feature/DEF-743-con02-acceptatie",
        "basis_commit": BASIS_COMMIT,
        "gelezen_bronnen": gelezen_bronnen,
        "gelezen_bronnen_toelichting": "snapshot = byte-identieke kopie in dit pakket (de enige bron voor verificatie); provenance = pad waarvan bij bouw gelezen is (alleen herkomstinformatie); repo_pad = relatieve repo-locatie indien de bron in deze repo getrackt is.",
        "lagen": {
            "historisch_ongewijzigd": "scenario-input/IDs/given/when exact zoals in basis/casusregister-geintegreerd-v6.json (hash-gecontroleerd)",
            "historische_verwachtingen": "then/oracle/G/T/H uit basis/v6 en basis/v2 (GTH-v1/kruisreview) — ontwerp, geen pass",
            "huidige_laag_projectbesluiten": "basis/besluiten-20260915-v3.md §1–§3 toegepast als specificatiecontext",
            "expert": "leeg: status pending, actor null, datum null, besluit null, motivering null, goldset false",
        },
        "besluiten_v3": BESLUITEN,
        "eerste_zes_voorgesteld": EERSTE_ZES,
        "aantallen": {
            "acceptatiecasussen": len(cases_out),
            "overzicht_ids": len(overzicht),
            "overige_ontwerpcases": len(overzicht) - len(cases_out),
            "fixtures": len(manifest_rows),
            "basis_snapshots": len(gelezen_bronnen),
        },
        "cases": cases_out,
        "overzicht_94": overzicht,
    }
    (uit / "acceptatie-register.json").write_text(
        json.dumps(register, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    schrijf_formulier(uit, register)
    schrijf_overzicht(uit, register)
    print(
        f"OK: {len(cases_out)} casussen, {len(overzicht)} IDs, {len(manifest_rows)} fixtures, {len(gelezen_bronnen)} basis-snapshots -> {uit}"
    )
    if not (uit / "START-HIER.md").exists():
        print(
            "let op: START-HIER.md en de scripts zijn handgeschreven; kopieer/actualiseer die apart voor een nieuwe versiemap"
        )


def md_quote(tekst: str) -> str:
    return "\n".join("> " + r for r in tekst.splitlines())


def schrijf_formulier(uit: Path, reg: dict) -> None:
    L: list[str] = []
    L.append("# CON-02 — Deskundigenformulier acceptatiepakket v1")
    L.append("")
    L.append(
        f"Datum pakket: {reg['datum']} · Basis: `{reg['basis_commit'][:9]}` · Branch: `{reg['werkbranch']}`"
    )
    L.append("")
    L.append(
        "**Status: alle 31 casussen PENDING. Geen goldset. Geen appketenuitvoering. Geen modelkwaliteit bewezen.**"
    )
    L.append("")
    L.append(
        "Dit formulier bevat per casus (1) de ongewijzigde historische scenario-input, (2) de historische brongebonden onderbouwing en vraag, (3) de exacte bronpassages met locator/hash/link, (4) de huidige laag met de projectbesluiten van 15 september 2026, en (5) lege beoordelingsvelden. Historische verwachtingen zijn ontwerpen; ze zijn nergens gepromoveerd tot 'pass'. Waar een bron een synthetische mutant of testconstructie is, staat dat expliciet."
    )
    L.append("")
    L.append(
        "Onderscheid dat overal geldt: **bestand aanwezig in dit pakket** ≠ **feitelijk door de app/het model ontvangen**. Het tweede is in dit pakket nergens vastgesteld."
    )
    L.append("")
    L.append("## Projectbesluiten (huidige laag)")
    L.append("")
    for k, b in reg["besluiten_v3"].items():
        L.append(f"- **{k} — {b['titel']}** ({b['bron']}): {b['kern']}")
    L.append("")
    L.append("## Beoordelingsschaal")
    L.append("")
    L.append(
        "Per casus vult de deskundige in: **Acceptatie** (de historische verwachting + huidige laag is juist als acceptatiecriterium) of **Afwijzing** (met motivering), plus actor en datum. Een lege regel is 'pending'. Er is geen cijfer (B3)."
    )
    L.append("")
    L.append(
        f"Voorgestelde eerste zes: {', '.join(reg['eerste_zes_voorgesteld'])}. Volgorde daarna: P03–P31 op nummer."
    )
    L.append("")
    L.append("---")

    for c in reg["cases"]:
        h = c["historisch_ongewijzigd"]
        hv = c["historische_verwachtingen"]
        L.append("")
        ster = " ★ eerste zes" if c["in_eerste_zes"] else ""
        L.append(f"## {c['id']} — {h['title']}{ster}")
        L.append("")
        L.append(
            f"**Route:** {h['route']} · **Prioriteit:** {h['priority']} · **Bronnen:** {', '.join(h['source_ids'])} · **scenario_input_sha256:** `{h['scenario_input_sha256'][:16]}…`"
        )
        L.append("")
        L.append("### 1. Historische scenario-input (ongewijzigd)")
        L.append("")
        for k, v in h["input"].items():
            L.append(
                f"- **{k}:** {json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v}"
            )
        L.append(f"- **Gegeven:** {h['given']}")
        L.append(f"- **Wanneer:** {h['when']}")
        if c["retrieval_recept"]:
            r = c["retrieval_recept"]
            L.append(f"- **Retrievalrecept {r['id']}** — {r['label']}")
            if r["ranked_candidates"]:
                L.append(
                    "  - rangorde (synthetisch): "
                    + ", ".join(
                        f"{x['fixture_chunk_id']}={x['score']}"
                        for x in r["ranked_candidates"]
                    )
                )
                L.append(
                    f"  - top_k={r['top_k']}, min_score={r['min_score']}, verwacht teruggegeven: {', '.join(r['expected_returned_ids'])}"
                )
        L.append("")
        L.append("### 2. Bronnen — exacte inhoud, locator, versie, link")
        L.append("")
        for b in c["bronbinding"]:
            syn = (
                " — **SYNTHETISCH (mutant/testconstructie)**"
                if b["synthetisch"]
                else ""
            )
            L.append(f"**{b['id']}** · {b['kind_label']}{syn}")
            L.append("")
            L.append(f"- pakketpad: `{b['pakketpad']}` · sha256 `{b['sha256']}`")
            L.append(
                f"- bronversie: {b['source_version'] if b['source_version'] is not None else 'onbekend (null)'}"
            )
            origin = b["origin"]
            if isinstance(origin, str) and origin.startswith("http"):
                L.append(f"- link: <{origin}>")
            else:
                L.append(f"- herkomst (geen hyperlink): `{origin}`")
            L.append(f"- locators (manifest): {'; '.join(b['locators'])}")
            for p in b["passages"]:
                L.append(f"- **{p['locator']}** — letterlijk:")
                L.append("")
                L.append(md_quote(p["passage"]))
                L.append("")
        L.append(
            "### 3. Historische brongebonden onderbouwing en vraag (ontwerp, geen pass)"
        )
        L.append("")
        L.append(
            f"- **Onderbouwing (source_based_oracle):** {hv['source_based_oracle']}"
        )
        L.append(f"- **Historische verwachting (then, v6):** {hv['then_v6']}")
        L.append(f"- **T (GTH-v1):** {hv['gth_v1']['T']}")
        L.append(f"- **G (GTH-v1):** {hv['gth_v1']['G']}")
        L.append(f"- **H (GTH-v1, alleen op verzoek — B2):** {hv['gth_v1']['H']}")
        if hv["cowork_aanvulling_v1"]:
            cw = hv["cowork_aanvulling_v1"]
            L.append(
                f"- **Cowork-aanvulling v1 (historisch):** T: {cw.get('T')} · H: {cw.get('H')} · bewijssoort: {cw.get('bewijssoort')}"
            )
        lv = hv["actuele_verwachting_v1_kruisreview"].get("locatorvoorwaarde")
        if lv:
            L.append(f"- **Locatorvoorwaarde (kruisreview-v2):** {lv}")
        L.append(f"- **Deskundigenvraag:** {hv['expert_question']}")
        L.append("")
        L.append("### 4. Huidige laag — projectbesluiten 15-09-2026")
        L.append("")
        for t in c["huidige_laag_projectbesluiten"]["toelichting"]:
            L.append(f"- {t}")
        L.append("")
        L.append("### 5. Bewijsstatus")
        L.append("")
        L.append(
            "- Fixturebestand in pakket: ja · Feitelijk door app ontvangen: **niet vastgesteld** · Ketenuitvoering: geen · Modelkwaliteit bewezen: nee"
        )
        L.append("")
        # Leeg beoordelingsblok: exact de template waartegen de verifier toetst.
        L.extend(OORDEELBLOK_LEEG)

    (uit / "deskundigenformulier.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def schrijf_overzicht(uit: Path, reg: dict) -> None:
    L = ["# Overzicht 94 IDs — CON-02 acceptatiepakket v1", ""]
    L.append(
        f"{reg['aantallen']['overzicht_ids']} unieke IDs uit `basis/casusregister-geintegreerd-v2.json` (kruisreview): {reg['aantallen']['acceptatiecasussen']} praktijkcasussen in dit acceptatiepakket + {reg['aantallen']['overige_ontwerpcases']} overige ontwerpcases (niet in het formulier, wel bewaard; expert pending)."
    )
    L.append("")
    L.append(
        "| ID | Historische bron | In pakket (31) | Categorie | Korte titel/scenario | Expert |"
    )
    L.append("|---|---|---|---|---|---|")
    for o in reg["overzicht_94"]:
        L.append(
            f"| {o['id']} | {o['historische_bron']} | {'ja' if o['in_acceptatiepakket_31'] else 'nee'} | {o['categorie']} | {str(o['korte_titel']).replace('|', '/')} | pending |"
        )
    (uit / "overzicht-94-ids.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
