"""Duplicaatcontrole binnen de schrijftransactie (DEF-482, overgenomen uit DEF-483).

`create_definitie` deed de duplicaatcontrole vóór `BEGIN IMMEDIATE`; twee
gelijktijdige aanroepen zagen allebei "geen duplicaat" en slaagden allebei.
Met de controle binnen de transactie serialiseert SQLite de schrijvers en ziet
de tweede de gecommitte rij van de eerste.

Voorwaarde: `find_duplicates` mag geen committend ``with conn:``-blok
gebruiken, anders sluit de controle zelf de transactie waarin hij draait.
"""

from __future__ import annotations

import threading
import time

import pytest

from database.definitie_repository import DefinitieRecord, DefinitieRepository

pytestmark = [pytest.mark.unit]

WACHT = 10  # boven de busy_timeout van 5 s (DEF-722)


def _record() -> DefinitieRecord:
    return DefinitieRecord(
        begrip="race_begrip",
        definitie="tekst",
        categorie="proces",
        organisatorische_context='["ORG"]',
    )


# --- T6 -------------------------------------------------------------------


def test_find_duplicates_laat_lopende_transactie_open(tmp_path):
    repo = DefinitieRepository(str(tmp_path / "leespad.db"))
    with repo._db.transaction() as conn:
        conn.execute(
            "INSERT INTO definities (begrip, definitie, categorie) VALUES ('tx', 't', 'proces')"
        )
        repo.find_duplicates("race_begrip", '["ORG"]')
        assert conn.in_transaction, "find_duplicates heeft de transactie gecommit"


# --- T7 -------------------------------------------------------------------


def test_gelijktijdige_creates_leveren_precies_een_definitie(tmp_path):
    repo = DefinitieRepository(str(tmp_path / "race.db"))
    duplicates = repo._crud._duplicates
    origineel = duplicates.find_duplicates
    a_heeft_gecontroleerd = threading.Event()

    def controle_met_pauze(*args, **kwargs):
        resultaat = origineel(*args, **kwargs)
        if threading.current_thread().name == "A":
            a_heeft_gecontroleerd.set()
            time.sleep(0.5)  # houd het venster tussen controle en INSERT open
        return resultaat

    duplicates.find_duplicates = controle_met_pauze
    uitkomsten: dict[str, tuple[str, object]] = {}

    def maak(naam: str) -> None:
        try:
            uitkomsten[naam] = ("ok", repo.create_definitie(_record()))
        except ValueError as e:
            uitkomsten[naam] = ("duplicaat", str(e))
        finally:
            repo._db.get_connection().close()

    thread_a = threading.Thread(target=maak, args=("A",), name="A")
    thread_b = threading.Thread(target=maak, args=("B",), name="B")
    thread_a.start()
    assert a_heeft_gecontroleerd.wait(WACHT), "thread A kwam niet tot de controle"
    thread_b.start()
    thread_a.join(WACHT)
    thread_b.join(WACHT)
    assert not thread_a.is_alive() and not thread_b.is_alive(), "threads hangen"

    soorten = sorted(soort for soort, _ in uitkomsten.values())
    assert soorten == ["duplicaat", "ok"], uitkomsten
    actief = (
        repo._db.get_connection()
        .execute(
            "SELECT COUNT(*) FROM definities WHERE begrip = 'race_begrip'"
            " AND status != 'archived'"
        )
        .fetchone()[0]
    )
    assert actief == 1
