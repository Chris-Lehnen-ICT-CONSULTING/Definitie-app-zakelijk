"""Driver voor het AppTest-ketenbewijs van DEF-622.

Draait buiten de pytest-conftest (die `streamlit` globaal vervangt door een
mock) met de échte Streamlit `AppTest`. Installeert eerst de offline-bootstrap
(netwerk dicht, SQLite alleen binnen de sessieroot, dummykeys) — onder
`run_profile` is die via `sitecustomize` al actief (idempotent) — zaait dan
een synthetische database, speelt de drie keuzes en de CON-01-weergave na en
schrijft de waarnemingen als JSON naar stdout.
`tests/unit/ui/test_def622_apptest_keuzes.py` start dit script als
subprocess en asserteert op die JSON.

Aanroep: `python tests/apptest/run_def622_apptest.py <pad-naar-testdatabase>`
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

APP = Path(__file__).with_name("def622_keuzes_app.py")


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
            definitie="kwaliteitsmerk voor gecontroleerde producten",
            categorie="type",
            organisatorische_context='["Stichting Zilver"]',
            juridische_context='["privaatrecht"]',
            wettelijke_basis='["Regeling Z"]',
            status=DefinitieStatus.ESTABLISHED.value,
        )
    )


def _rijen(db_pad: str) -> list[dict]:
    """Lees de definities via een nieuwe verbinding (geen repositorycache)."""
    conn = sqlite3.connect(db_pad)
    conn.row_factory = sqlite3.Row
    try:
        return [
            dict(r)
            for r in conn.execute(
                # Alleen het proefbegrip: schema.sql zaait zelf al voorbeeldrijen.
                "SELECT id, begrip, definitie, status, version_number, "
                "organisatorische_context FROM definities "
                "WHERE begrip = 'keurmerk' ORDER BY id"
            )
        ]
    finally:
        conn.close()


def _geschiedenis(db_pad: str, definitie_id: int) -> list[dict]:
    conn = sqlite3.connect(db_pad)
    conn.row_factory = sqlite3.Row
    try:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT wijziging_type, wijziging_reden FROM definitie_geschiedenis "
                "WHERE definitie_id = ? ORDER BY id",
                (definitie_id,),
            )
        ]
    finally:
        conn.close()


def _teksten(at) -> list[str]:
    uit: list[str] = []
    for verzameling in (at.markdown, at.success, at.warning, at.error, at.info):
        uit.extend(str(getattr(el, "value", el)) for el in verzameling)
    return uit


def _ss(at, sleutel: str):
    """Sessiewaarde of None; `clear_value` verwijdert de sleutel helemaal."""
    try:
        return at.session_state[sleutel]
    except KeyError:
        return None


def _vers(db_pad: str):
    from streamlit.testing.v1 import AppTest

    os.environ["DEF622_APPTEST_DB"] = db_pad
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]
    return at


def main(db_pad: str) -> dict:
    sessieroot = offline_bootstrap.install()
    assert offline_bootstrap.gate_is_actief()
    bestaand_id = _zaai(db_pad)
    waarnemingen: dict = {
        "bestaand_id": bestaand_id,
        "bootstrap": {
            "gate_actief": offline_bootstrap.gate_is_actief(),
            "sessieroot": str(sessieroot),
            "db_binnen_sessieroot": offline_bootstrap.pad_is_toegestaan(db_pad),
        },
    }

    # Uitgangssituatie: melding met de drie keuzes én de CON-01-uitleg.
    at = _vers(db_pad)
    waarnemingen["knoppen"] = [b.label for b in at.button]
    waarnemingen["start_teksten"] = _teksten(at)

    # Gebruik Deze → gekozen record zichtbaar, melding weg.
    at.button(key=f"use_{bestaand_id}").click().run()
    assert not at.exception, [str(e.value) for e in at.exception]
    waarnemingen["na_gebruik_deze"] = {
        "teksten": _teksten(at),
        "selected_id": getattr(_ss(at, "selected_definition"), "id", None),
        "check_result_weg": _ss(at, "last_check_result") is None,
    }

    # Bewerk → bewerkpad: de echte editor laadt het record.
    at = _vers(db_pad)
    at.button(key=f"edit_{bestaand_id}").click().run()
    assert not at.exception, [str(e.value) for e in at.exception]
    waarnemingen["na_bewerk"] = {
        "editing_definition_id": _ss(at, "editing_definition_id"),
        "active_tab": _ss(at, "active_tab"),
        "editing_definition_geladen_id": getattr(
            _ss(at, "editing_definition"), "id", None
        ),
        "text_areas": [str(t.value) for t in at.text_area],
        "teksten": _teksten(at),
    }

    # Genereer Nieuw zonder reden → niets geforceerd, waarschuwing.
    at = _vers(db_pad)
    at.button(key=f"new_{bestaand_id}").click().run()
    assert not at.exception, [str(e.value) for e in at.exception]
    waarnemingen["nieuw_zonder_reden"] = {
        "options": dict(_ss(at, "generation_options") or {}),
        "trigger": bool(_ss(at, "trigger_auto_generation") or False),
        "waarschuwingen": [str(w.value) for w in at.warning],
        "rijen": _rijen(db_pad),
    }

    # Genereer Nieuw met reden → de trigger start de echte handler op de
    # echte container (AI bevroren): nieuw concept in de DB, bestaand record
    # ongemoeid, force-opties opgebruikt.
    at = _vers(db_pad)
    at.text_input(key=f"new_reason_{bestaand_id}").input(
        "Bestaande definitie dekt de nieuwe regeling niet."
    ).run()
    at.button(key=f"new_{bestaand_id}").click().run()
    assert not at.exception, [str(e.value) for e in at.exception]
    rijen = _rijen(db_pad)
    nieuwe = [r for r in rijen if r["id"] != bestaand_id]
    waarnemingen["nieuw_met_reden"] = {
        "options": dict(_ss(at, "generation_options") or {}),
        "trigger": bool(_ss(at, "trigger_auto_generation") or False),
        "rijen": rijen,
        "nieuwe_ids": [r["id"] for r in nieuwe],
        "geschiedenis_nieuw": (
            _geschiedenis(db_pad, nieuwe[0]["id"]) if nieuwe else []
        ),
        "geschiedenis_bestaand": _geschiedenis(db_pad, bestaand_id),
        "editing_definition_id": _ss(at, "editing_definition_id"),
        "last_generation_result_aanwezig": _ss(at, "last_generation_result")
        is not None,
        "agent_result": {
            k: (_ss(at, "last_generation_result") or {}).get("agent_result", {}).get(k)
            for k in ("success", "error_message", "saved_definition_id")
        },
        # Alleen echte generatiefouten; violations van de toetsing worden ook
        # via st.error getoond en zijn geen fout van de keten.
        "fouten": [
            str(e.value)
            for e in at.error
            if "Fout bij generatie" in str(e.value)
            or "Generatie geweigerd" in str(e.value)
            or "Generatie geblokkeerd" in str(e.value)
        ],
    }
    return waarnemingen


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), ensure_ascii=False, default=str))
