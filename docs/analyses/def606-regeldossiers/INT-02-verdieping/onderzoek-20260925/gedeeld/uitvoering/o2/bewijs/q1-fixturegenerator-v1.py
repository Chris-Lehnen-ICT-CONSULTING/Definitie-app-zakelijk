"""Q1 (DEF-835): genereert de technische runnerfixture — GEEN goldset.

Eenmalig gebruikt om tests/fixtures/def835_int02_kwalificatie_runner.json
te schrijven (nooit overschrijven). De drie regressiegevallen nemen de
exacte invoer van C105/C107/C112 uit de ontwerpfixture over; de overige 40
gevallen zijn betekenisloze technische invoer met willekeurig toegekende
labels die alleen runnergedrag toetsen.
"""

import json
import sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
DOEL = REPO / "tests" / "fixtures" / "def835_int02_kwalificatie_runner.json"
ONTWERP = json.loads(
    (REPO / "tests/fixtures/def835_int02_ontwerpgevallen.json").read_text("utf-8")
)
PER_ID = {g["id"]: g for g in ONTWERP["gevallen"]}
PROTOCOL_SHA256 = "53a199fdff49c7ec40c10e84c79356fd72dcba6190cb75c715ce077c1054f18f"
FAMILIES = (
    ("technisch-criterium", "pass"),
    ("technisch-normatief-begrip", "pass"),
    ("technisch-actorvoorschrift", "fail"),
    ("technisch-betekenisgrond", "review_required"),
)


def technisch(geval_id: str, fase: str, familie: str, status: str) -> dict:
    return {
        "id": geval_id,
        "fase": fase,
        "familie": familie,
        "herkomst": "technische Q1-testfixture; geen goldset, geen echte casus",
        "invoer": {
            "begrip": f"testbegrip {geval_id}",
            "kern": f"Technische testkern {geval_id} zonder inhoudelijke betekenis.",
            "bedoeling": (
                None if status == "review_required" else f"testbedoeling {geval_id}"
            ),
            "organisatorische_context": ["technische testcontext"],
            "juridische_context": [],
            "wettelijke_basis": [],
            "bronnen": [],
        },
        "label": {
            "status": status,
            "normgrond": f"TECHNISCH-TESTLABEL-{geval_id}; geen normgrond",
        },
    }


gevallen = []
for geval_id in ("C105", "C107", "C112"):
    ontwerp = PER_ID[geval_id]
    gevallen.append(
        {
            "id": geval_id,
            "fase": "regressie",
            "familie": "bekende-regressie",
            "herkomst": "tests/fixtures/def835_int02_ontwerpgevallen.json (invoer exact)",
            "invoer": ontwerp["invoer"],
            "label": {
                "status": ontwerp["verwacht"]["status"],
                "normgrond": f"TECHNISCH-TESTLABEL-{geval_id}; geen normgrond",
            },
        }
    )
for nummer in range(24):
    familie, status = FAMILIES[nummer % 4]
    gevallen.append(technisch(f"TQ-O{nummer + 1:02d}", "ontwikkeling", familie, status))
# Hold-out: 4 fail, 8 pass, 4 review_required (de verdeling van het protocol).
HOLDOUT = ["pass"] * 8 + ["fail"] * 4 + ["review_required"] * 4
for nummer, status in enumerate(HOLDOUT):
    familie = {
        "pass": FAMILIES[nummer % 2][0],
        "fail": FAMILIES[2][0],
        "review_required": FAMILIES[3][0],
    }[status]
    gevallen.append(technisch(f"TQ-H{nummer + 1:02d}", "holdout", familie, status))

data = {
    "soort": "def835-int02-kwalificatie-gevallen/1",
    "technische_testfixture": True,
    "goldset": False,
    "gebruik": (
        "UITSLUITEND technische testfixture voor de offline Q1-runnertests "
        "(DEF-835). GEEN goldset, GEEN hold-out en geen geaccepteerde labels: "
        "de labels zijn willekeurig toegekend om runnergedrag te toetsen en "
        "zeggen niets over INT-02. De runner weigert dit bestand voor echte "
        "verzending."
    ),
    "protocol_sha256": PROTOCOL_SHA256,
    "freeze": {
        "status": "bevroren",
        "geaccepteerd_door": "technische testfixture; geen mens, geen labelacceptatie",
        "geaccepteerd_op": "2026-09-28",
        "bron": "Q1-unittest; geen echte freeze of goldset",
    },
    "gevallen": gevallen,
}
with DOEL.open("x", encoding="utf-8") as bestand:
    bestand.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
print(DOEL, len(gevallen))
