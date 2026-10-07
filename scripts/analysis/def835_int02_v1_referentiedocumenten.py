"""DEF-835 positiecorrectie — /1-referentiedocumenten uit HEAD-gedrag.

Eenmalig hulpmiddel bij de reviewcorrectie (Codex, 07-10-2026). Laadt
`src/domain/int02/contract.py` en de ontwerpgevallen-fixture letterlijk uit
een git-revisie (standaard 3ba526dae, contract def835-int02-assessment/1) en
maakt met díe code geldige /1-documenten. Het resultaat is de fixture
`tests/fixtures/def835_int02_contract_v1_documenten.json`, waarmee de
migratieregressietests bewijzen dat een bewaard /1-document na de overgang
naar /2 historisch wordt en niet `error`.

Geen netwerk, geen model, geen sleutel. Gebruik (vanuit de repo-root):

    python scripts/analysis/def835_int02_v1_referentiedocumenten.py [revisie]
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOEL = REPO / "tests" / "fixtures" / "def835_int02_contract_v1_documenten.json"
CONTRACT = "src/domain/int02/contract.py"
FIXTURE = "tests/fixtures/def835_int02_ontwerpgevallen.json"

#: Synthetische configuratie (geen proef- of productieconfiguratie).
CONFIGURATIE = {
    "normhash": hashlib.sha256(b"def835-migratie-testnorm").hexdigest(),
    "promptversie": "def835-int02-prompt/2",
    "routeringshash": hashlib.sha256(b"def835-migratie-routering").hexdigest(),
    "provider": "synthetisch",
    "model": "synthetisch-model",
}

#: Synthetisch extra geval: onder /1 geldig met de tweede vindplaats van een
#: niet-uniek citaat; onder /2 zou dezelfde uitvoer `niet_uniek` zijn.
NIET_UNIEK = {
    "id": "SYN-niet-uniek",
    "invoer": {
        "begrip": "dagtotaal",
        "kern": "Totaal van de dag, berekend als som van de dag.",
        "bedoeling": "Synthetische afleiding van een dagtotaal.",
        "organisatorische_context": ["synthetische begrippenstudie"],
        "juridische_context": [],
        "wettelijke_basis": [],
        "bronnen": [],
    },
    "modelrespons": {
        "verdict": "pass",
        "passages": [
            {
                "quote": "van de dag",
                "start": 36,
                "end": 46,
                "function": "derivation",
                "ground": {
                    "field": "kern",
                    "ref": None,
                    "quote": None,
                    "start": None,
                    "end": None,
                },
            }
        ],
        "reason": "Synthetische afleiding.",
        "question": None,
        "uncertainty": "none",
        "scope_reason": None,
        "coverage": "complete",
    },
}


def _git(revisie: str, pad: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{revisie}:{pad}"],
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def _laad_contract(bron: bytes) -> types.ModuleType:
    module = types.ModuleType("def835_contract_v1_referentie")
    sys.modules[module.__name__] = module
    exec(compile(bron, f"<git:{CONTRACT}>", "exec"), module.__dict__)
    return module


def _gevallen(fixture: dict) -> list[dict]:
    gevallen = []
    for geval in fixture["gevallen"]:
        for nr, versie in enumerate(geval.get("versies", [geval])):
            if versie.get("modelrespons") is None:
                continue
            if versie["uitvoering"]["status"] != "completed":
                continue
            naam = geval["id"] + (f"-{geval['variant']}" if "variant" in geval else "")
            if "versies" in geval:
                naam += f"-v{nr + 1}"
            gevallen.append({"id": naam, **versie})
    return [*gevallen, NIET_UNIEK]


def main(revisie: str = "3ba526dae") -> None:
    contract_bron = _git(revisie, CONTRACT)
    fixture_bron = _git(revisie, FIXTURE)
    c = _laad_contract(contract_bron)
    assert c.CONTRACTVERSIE == "def835-int02-assessment/1", c.CONTRACTVERSIE
    configuratie = c.Configuratie(**CONFIGURATIE)
    documenten = []
    for geval in _gevallen(json.loads(fixture_bron)):
        doc = c.beoordeel(
            c.maak_invoer(**geval["invoer"]),
            configuratie,
            geval["modelrespons"],
            c.Uitvoering(actor="ai", status="completed"),
        )
        if doc.status == "error":
            continue  # alleen geldige /1-documenten zijn migratiereferentie
        documenten.append(
            {
                "id": geval["id"],
                "document": doc.als_dict(),
                "oordeel_json": doc.oordeel_json,
            }
        )
    rev = subprocess.run(
        ["git", "rev-parse", revisie], cwd=REPO, check=True, capture_output=True
    )
    uit = {
        "soort": "def835-int02-contract-v1-referentiedocumenten/1",
        "gebruik": (
            "Migratieregressie (Codex-review 07-10-2026): geldige documenten, "
            "gemaakt met de /1-contractcode uit git. Ontwikkelgevallen en één "
            "synthetisch geval; geen goldset en geen hold-out."
        ),
        "herkomst": {
            "revisie": rev.stdout.decode().strip(),
            "contract_pad": CONTRACT,
            "contract_sha256": hashlib.sha256(contract_bron).hexdigest(),
            "fixture_pad": FIXTURE,
            "fixture_sha256": hashlib.sha256(fixture_bron).hexdigest(),
            "generator": str(Path(__file__).resolve().relative_to(REPO)),
        },
        "configuratie": CONFIGURATIE,
        "documenten": documenten,
    }
    DOEL.write_text(
        json.dumps(uit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main(*sys.argv[1:])
