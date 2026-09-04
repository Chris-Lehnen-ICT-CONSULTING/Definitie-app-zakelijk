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

from database.definitie_repository import (
    DefinitieRecord,
    DefinitieRepository,
    DefinitieStatus,
)

pytestmark = [pytest.mark.unit]

WACHT = 10  # boven de busy_timeout van 5 s (DEF-722)


def _record(wettelijke_basis: str | None = None) -> DefinitieRecord:
    return DefinitieRecord(
        begrip="race_begrip",
        definitie="tekst",
        categorie="proces",
        organisatorische_context='["ORG"]',
        wettelijke_basis=wettelijke_basis,
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
    tijden: dict[str, float] = {}

    def maak(naam: str) -> None:
        tijden[f"{naam}_binnen"] = time.monotonic()
        try:
            uitkomsten[naam] = ("ok", repo.create_definitie(_record()))
        except ValueError as e:
            uitkomsten[naam] = ("duplicaat", str(e))
        finally:
            tijden[f"{naam}_klaar"] = time.monotonic()
            repo._db.get_connection().close()

    thread_a = threading.Thread(target=maak, args=("A",), name="A")
    thread_b = threading.Thread(target=maak, args=("B",), name="B")
    thread_a.start()
    assert a_heeft_gecontroleerd.wait(WACHT), "thread A kwam niet tot de controle"
    thread_b.start()
    thread_a.join(WACHT)
    thread_b.join(WACHT)
    assert not thread_a.is_alive() and not thread_b.is_alive(), "threads hangen"

    # Zonder dit is een trage B een gewone sequentiële weigering, geen race.
    assert (
        tijden["B_binnen"] < tijden["A_klaar"]
    ), "thread B kwam pas na de commit van A binnen; de race is niet getest"
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


# --- _weiger_duplicaat: takken die de racetest niet raakt -------------------


def test_gearchiveerd_duplicaat_blokkeert_nieuwe_definitie_niet(tmp_path):
    repo = DefinitieRepository(str(tmp_path / "archief.db"))
    eerste = repo.create_definitie(_record())
    assert repo.change_status(eerste, DefinitieStatus.ARCHIVED, changed_by="x")

    tweede = repo.create_definitie(_record())

    assert tweede != eerste


def test_duplicaat_met_wettelijke_basis_wordt_geweigerd(tmp_path):
    repo = DefinitieRepository(str(tmp_path / "wettelijk.db"))
    repo.create_definitie(_record(wettelijke_basis='["Sr"]'))

    with pytest.raises(ValueError, match="bestaat al"):
        repo.create_definitie(_record(wettelijke_basis='["Sr"]'))
