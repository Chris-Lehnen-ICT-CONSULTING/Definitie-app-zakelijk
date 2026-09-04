"""Aanvullende connection-ownershipcontracten voor DEF-488."""

from __future__ import annotations

import gc
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, suppress

import pytest

from database.db_connection import DatabaseConnection
from services.container import ContainerConfigs

pytestmark = [pytest.mark.unit]


def _database_with_test_tables(tmp_path):
    db_path = tmp_path / "metadata-read.db"
    db = DatabaseConnection(str(db_path))
    conn = db.get_connection()
    conn.execute("""
        CREATE TABLE definities (
            id INTEGER PRIMARY KEY,
            datum_voorstel TEXT,
            ketenpartners TEXT
        )
        """)
    conn.execute("CREATE TABLE writes (value TEXT NOT NULL)")
    return db_path, db


def test_connections_are_not_shared_between_threads(tmp_path):
    db = DatabaseConnection(str(tmp_path / "connection-ownership.db"))
    main_connection = db.get_connection()
    workers_ready = threading.Barrier(2)
    connections_acquired = threading.Barrier(2)

    def get_worker_connection():
        workers_ready.wait(timeout=3)
        connection = db.get_connection()
        try:
            connections_acquired.wait(timeout=3)
            return threading.get_ident(), id(connection)
        finally:
            if connection is not main_connection:
                connection.close()

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            first_future = executor.submit(get_worker_connection)
            second_future = executor.submit(get_worker_connection)
            first = first_future.result(timeout=5)
            second = second_future.result(timeout=5)

        assert first[0] != second[0]
        assert first[1] != second[1]
        assert first[1] != id(main_connection)
        assert second[1] != id(main_connection)
    finally:
        main_connection.close()


def test_same_thread_reuses_connection(tmp_path):
    db = DatabaseConnection(str(tmp_path / "same-thread.db"))
    connection = db.get_connection()

    try:
        assert connection is db.get_connection()
    finally:
        connection.close()


def test_metadata_read_does_not_commit_same_thread_transaction(tmp_path):
    db_path, db = _database_with_test_tables(tmp_path)

    def write_read_then_fail() -> None:
        with db.transaction() as conn:
            conn.execute("INSERT INTO writes VALUES ('same thread')")
            assert db.has_legacy_columns() is True
            raise RuntimeError("rollback metadata read")

    try:
        with pytest.raises(RuntimeError, match="rollback metadata read"):
            write_read_then_fail()

        with closing(sqlite3.connect(db_path)) as verification_conn:
            rows = verification_conn.execute("SELECT value FROM writes").fetchall()

        assert rows == []
    finally:
        db.get_connection().close()


def test_testing_memory_database_keeps_same_thread_state():
    db = DatabaseConnection(ContainerConfigs.testing()["db_path"])
    connection = db.get_connection()

    try:
        connection.execute("CREATE TABLE state (value TEXT NOT NULL)")
        connection.execute("INSERT INTO state VALUES ('behouden')")
        rows = connection.execute("SELECT value FROM state").fetchall()
        assert [row[0] for row in rows] == ["behouden"]
    finally:
        connection.close()


def test_worker_connection_closes_when_thread_state_is_released(tmp_path):
    db = DatabaseConnection(str(tmp_path / "thread-lifecycle.db"))
    worker_connections: list[sqlite3.Connection] = []

    def acquire_connection() -> None:
        connection = db.get_connection()
        connection.execute("CREATE TABLE lifecycle (value TEXT NOT NULL)")
        worker_connections.append(connection)

    worker = threading.Thread(target=acquire_connection)
    worker.start()
    worker.join(timeout=5)
    assert not worker.is_alive()
    del worker
    gc.collect()

    connection = worker_connections[0]
    try:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")
    finally:
        with suppress(sqlite3.ProgrammingError):
            connection.close()
