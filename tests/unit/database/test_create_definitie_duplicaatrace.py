"""Duplicaatcontrole binnen de schrijftransactie (DEF-482, overgenomen uit DEF-483).

`create_definitie` deed de duplicaatcontrole vóór `BEGIN IMMEDIATE`; twee
gelijktijdige aanroepen zagen allebei "geen duplicaat" en slaagden allebei.
Met de controle binnen de transactie serialiseert SQLite de schrijvers en ziet
de tweede de gecommitte rij van de eerste.

Voorwaarde: `find_duplicates` mag geen committend ``with conn:``-blok
gebruiken, anders sluit de controle zelf de transactie waarin hij draait.

DEF-727: de racetest is scheduling-onafhankelijk. Thread A houdt de writelock
vast totdat thread B aantoonbaar aan zijn ``BEGIN IMMEDIATE`` is begonnen
(trace-callback op B's eigen connectie zet een event); geen vaste sleep, geen
functie-start-timestamps. Loopt de wachttijd af, dan faalt de test met een
duidelijke melding in plaats van te hangen.
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

WACHT = 10  # join-timeout, boven de busy_timeout van 5 s (DEF-722)
# A wacht op B's BEGIN. De busy_timeout is hier niet de bindende grens: A wordt
# gewekt zodra B's BEGIN IMMEDIATE begint, dus B's busy-venster (5 s) start pas
# dan en A heeft daarna alleen nog INSERT + COMMIT. Dit begrenst uitsluitend hoe
# lang B mag doen over het bereiken van zijn BEGIN; blijft onder WACHT.
LOCK_WACHT = 4.0


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


def test_gelijktijdige_creates_leveren_precies_een_definitie(tmp_path, monkeypatch):
    """Twee threads maken tegelijk dezelfde definitie; precies één slaagt.

    Volgorde, afgedwongen met events in plaats van sleeps:
    1. A doet zijn duplicaatcontrole binnen BEGIN IMMEDIATE (houdt de writelock).
    2. B start en begint zijn BEGIN IMMEDIATE; B's trace-callback zet `b_begint`
       op het moment dat dat statement begint (SQLITE_TRACE_STMT vuurt vóór de
       lock-poging; een signaal ná de lock zou deadlocken, want die lock is van A).
    3. Pas daarna insert en commit A.
    4. B krijgt de lock, ziet A's rij en weigert met ValueError.

    Bewijskracht: de handshake zelf dwingt de volgorde af; de discriminerende
    asserties zijn `uitkomsten` en `actief == 1` (met de duplicaatcontrole buiten
    de transactie slagen beide creates: ['ok', 'ok']). Of B daadwerkelijk op de
    lock heeft gewacht is vanuit Python niet observeerbaar (geen busy-handler-
    hook); de ordeningsassertie is een redundante regressiecheck, geen bewijs.

    Testnaad: de handshake hangt aan `_weiger_duplicaat` → `_duplicates.find_duplicates`
    binnen de transactie van `create_definitie`. Loopt die controle ooit anders,
    dan meldt "A bereikte find_duplicates niet" dat, niet een threadprobleem.
    """
    repo = DefinitieRepository(str(tmp_path / "race.db"))
    record = _record()
    duplicates = repo._crud._duplicates
    origineel = duplicates.find_duplicates
    a_heeft_gecontroleerd = threading.Event()
    b_begint = threading.Event()
    tijden: dict[str, float] = {}
    fouten: list[str] = []
    uitkomsten: dict[str, tuple[str, object]] = {}

    def controle_met_wachttijd(*args, **kwargs):
        resultaat = origineel(*args, **kwargs)
        if threading.current_thread() is thread_a:
            a_heeft_gecontroleerd.set()
            # A houdt de writelock vast tot B aantoonbaar aan BEGIN IMMEDIATE begint.
            if not b_begint.wait(LOCK_WACHT):
                fouten.append(
                    f"thread B begon niet binnen {LOCK_WACHT}s aan BEGIN IMMEDIATE"
                )
        return resultaat

    monkeypatch.setattr(duplicates, "find_duplicates", controle_met_wachttijd)

    def maak(naam: str) -> None:
        conn = repo._db.get_connection()

        def traceer(statement: str) -> None:
            kop = statement.strip().upper()
            if kop.startswith("BEGIN IMMEDIATE"):
                tijden.setdefault(f"{naam}_BEGIN", time.monotonic())
                if naam == "B":
                    b_begint.set()
            elif kop.startswith("COMMIT"):
                tijden.setdefault(f"{naam}_COMMIT", time.monotonic())

        conn.set_trace_callback(traceer)
        try:
            uitkomsten[naam] = ("ok", repo.create_definitie(record))
        except ValueError as e:
            uitkomsten[naam] = ("duplicaat", str(e))
        except Exception as e:  # diagnose hoort in de assertie, niet op stderr
            uitkomsten[naam] = ("fout", repr(e))
        finally:
            conn.close()

    thread_a = threading.Thread(target=maak, args=("A",), name="A", daemon=True)
    thread_b = threading.Thread(target=maak, args=("B",), name="B", daemon=True)
    try:
        thread_a.start()
        assert a_heeft_gecontroleerd.wait(WACHT), (
            "A bereikte find_duplicates niet — loopt _weiger_duplicaat nog via "
            "_duplicates.find_duplicates binnen de transactie?"
        )
        thread_b.start()
        thread_a.join(WACHT)
        thread_b.join(WACHT)
        assert not thread_a.is_alive(), "thread A hangt"
        assert not thread_b.is_alive(), "thread B hangt"
        assert not fouten, fouten

        # Discriminerend: precies één create slaagt, de ander weigert als duplicaat.
        soorten = sorted(soort for soort, _ in uitkomsten.values())
        assert soorten == ["duplicaat", "ok"], uitkomsten
        # Zelfde predicaat als DefinitieDuplicateRepository: actief = status != 'archived'.
        actief = (
            repo._db.get_connection()
            .execute(
                "SELECT COUNT(*) FROM definities WHERE begrip = ?"
                " AND status != 'archived'",
                (record.begrip,),
            )
            .fetchone()[0]
        )
        assert actief == 1

        # Redundante regressiecheck op de handshake (per constructie waar zolang
        # `fouten` leeg is): B's BEGIN IMMEDIATE begon terwijl A de writelock hield.
        assert {"B_BEGIN", "A_COMMIT"} <= tijden.keys(), (tijden, uitkomsten)
        assert tijden["B_BEGIN"] < tijden["A_COMMIT"], tijden
    finally:
        repo._db.get_connection().close()


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
