"""Driver voor het AppTest-ketenbewijs van de expertactie (DEF-622).

Draait buiten de pytest-conftest (die `streamlit` globaal vervangt door een
mock) met de échte Streamlit `AppTest`. Installeert eerst de offline-bootstrap
(idempotent onder `run_profile`), zaait een synthetisch review-record met een
naam uit de context in de definitiezin, speelt de expertketen na op de echte
`ExpertReviewTab` en schrijft de waarnemingen als JSON naar stdout:

1. uitgangssituatie: CON-01 "Nog te beoordelen", gate geblokkeerd, en zonder
   gebruikersidentiteit is "Leg beoordeling vast" uitgeschakeld (K5);
2. reviewer naam (het bestaande widget van de reviewflow) + naamfunctie +
   reden → "Leg beoordeling vast" → readback: beoordeling op het record met
   actor en versiebinding; CON-01 "Voldoet"; gate "toegestaan";
3. "Re-validate" (K3) → de orchestrator ziet de beoordeling (CON-01 pass);
4. "Vaststellen" → readback: established, versie +1, beoordeling gebonden
   aan de nieuwe versie (V2c);
5. de vijf CON-01-weergaven (Voldoet / Voldoet niet / Nog te beoordelen /
   Voldoet niet + Nog te beoordelen / Technisch probleem) uit de gedeelde
   validatieweergave.

Aanroep: `python tests/apptest/run_def622_expert_apptest.py <pad-naar-testdatabase>`
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _pad in (str(REPO), str(REPO / "src")):
    if _pad not in sys.path:
        sys.path.insert(0, _pad)

from tests import offline_bootstrap

APP = Path(__file__).with_name("def622_expert_app.py")
ZIN = "kwaliteitsmerk dat uitsluitend door Stichting Zilver wordt verleend"
REVIEWER = "Reviewer Rood"
REDEN = "Stichting Zilver is de exclusieve uitgever van dit keurmerk."


def _zaai(db_pad: str) -> int:
    from database.definitie_repository import (
        DefinitieRecord,
        DefinitieRepository,
        DefinitieStatus,
    )

    repo = DefinitieRepository(db_pad)
    return repo.create_definitie(
        DefinitieRecord(
            begrip="keurmerk",
            definitie=ZIN,
            categorie="type",
            organisatorische_context='["Stichting Zilver"]',
            juridische_context='["privaatrecht"]',
            wettelijke_basis='["Regeling Z"]',
            status=DefinitieStatus.REVIEW.value,
            # Expliciet geïsoleerde overige gatevoorwaarde (DEF-630): alleen
            # CON-01 bepaalt hier de gate.
            validation_score=0.9,
        )
    )


def _rij(db_pad: str, definitie_id: int) -> dict:
    """Lees het record via een nieuwe verbinding (geen repositorycache)."""
    from database.definitie_repository import DefinitieRepository

    rec = DefinitieRepository(db_pad).get_definitie(definitie_id)
    assert rec is not None
    review = rec.get_context_review()
    conn = sqlite3.connect(db_pad)
    try:
        # Alleen de app-audit (met reden): schema.sql zaait in een verse DB
        # ook een trigger die een tweede rij zonder reden schrijft.
        geschiedenis = [
            r[0]
            for r in conn.execute(
                "SELECT wijziging_type FROM definitie_geschiedenis "
                "WHERE definitie_id = ? AND wijziging_reden IS NOT NULL ORDER BY id",
                (definitie_id,),
            )
        ]
    finally:
        conn.close()
    return {
        "status": rec.status,
        "version_number": rec.version_number,
        "definitie": rec.definitie,
        "updated_by": rec.updated_by,
        "approved_by": rec.approved_by,
        "review": review,
        "geschiedenis": geschiedenis,
    }


def _teksten(at) -> list[str]:
    uit: list[str] = []
    for verzameling in (
        at.markdown,
        at.caption,
        at.success,
        at.warning,
        at.error,
        at.info,
        at.text,
    ):
        uit.extend(str(getattr(el, "value", el)) for el in verzameling)
    return uit


def _knop(at, sleutel: str) -> dict:
    knop = at.button(key=sleutel)
    return {"label": knop.label, "disabled": bool(knop.disabled)}


def _ss(at, sleutel: str):
    try:
        return at.session_state[sleutel]
    except KeyError:
        return None


def _vers(db_pad: str, record_id: int):
    from streamlit.testing.v1 import AppTest

    os.environ["DEF622_APPTEST_DB"] = db_pad
    os.environ["DEF622_APPTEST_RECORD"] = str(record_id)
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]
    return at


def _functiesleutels(at, record_id: int) -> list[str]:
    prefix = f"con01_{record_id}_"
    return [
        s.key
        for s in at.selectbox
        if s.key and s.key.startswith(prefix) and s.key.endswith("_functie")
    ]


def main(db_pad: str) -> dict:
    sessieroot = offline_bootstrap.install()
    assert offline_bootstrap.gate_is_actief()
    record_id = _zaai(db_pad)
    waarnemingen: dict = {
        "record_id": record_id,
        "bootstrap": {
            "gate_actief": offline_bootstrap.gate_is_actief(),
            "sessieroot": str(sessieroot),
            "db_binnen_sessieroot": offline_bootstrap.pad_is_toegestaan(db_pad),
        },
    }

    # 1. Uitgangssituatie.
    at = _vers(db_pad, record_id)
    functies = _functiesleutels(at, record_id)
    waarnemingen["start"] = {
        "teksten": _teksten(at),
        "functiesleutels": functies,
        "vastleggen": _knop(at, f"con01_{record_id}_vastleggen"),
        "vaststellen": _knop(at, f"approve_btn_{record_id}"),
        "rij": _rij(db_pad, record_id),
    }
    assert len(functies) == 1, functies
    functie_sleutel = functies[0]
    reden_sleutel = functie_sleutel[: -len("_functie")] + "_reden"

    # 2. Identiteit + naamfunctie + reden → vastleggen → readback.
    at.text_input(key="reviewer_name_input").input(REVIEWER).run()
    at.selectbox(key=functie_sleutel).select("necessary").run()
    at.text_input(key=reden_sleutel).input(REDEN).run()
    waarnemingen["ingevuld"] = {
        "vastleggen": _knop(at, f"con01_{record_id}_vastleggen"),
    }
    at.button(key=f"con01_{record_id}_vastleggen").click().run()
    assert not at.exception, [str(e.value) for e in at.exception]
    na_vastleggen = _rij(db_pad, record_id)
    waarnemingen["na_vastleggen"] = {
        "teksten": _teksten(at),
        "rij": na_vastleggen,
        "geselecteerde_versie": getattr(
            _ss(at, "selected_review_definition"), "version_number", None
        ),
        "vaststellen": _knop(at, f"approve_btn_{record_id}"),
    }

    # 3. Re-validate: de orchestrator ziet de beoordeling.
    at.button(key=f"revalidate_{record_id}").click().run()
    assert not at.exception, [str(e.value) for e in at.exception]
    v2 = _ss(at, f"review_v2_validation_{record_id}") or {}
    waarnemingen["na_revalidate"] = {
        "con01_status": (v2.get("rule_statuses") or {}).get("CON-01"),
        "review": (v2.get("rule_results") or {}).get("CON-01", {}).get("review"),
        "overall_score": v2.get("overall_score", "ontbreekt"),
        "teksten": _teksten(at),
    }

    # 4. Vaststellen → readback.
    at.button(key=f"approve_btn_{record_id}").click().run()
    assert not at.exception, [str(e.value) for e in at.exception]
    waarnemingen["na_vaststellen"] = {
        "teksten": _teksten(at),
        "rij": _rij(db_pad, record_id),
    }

    # 5. De vijf weergaven (zelfde run: de sectie staat onder de review).
    waarnemingen["weergaven"] = {
        naam: {
            "con01_status": (res.get("rule_statuses") or {}).get("CON-01"),
            "overall_score": res.get("overall_score", "ontbreekt"),
        }
        for naam, res in (_ss(at, "def622_uitkomsten") or {}).items()
    }
    waarnemingen["weergave_teksten"] = _teksten(at)
    return waarnemingen


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), ensure_ascii=False, default=str))
