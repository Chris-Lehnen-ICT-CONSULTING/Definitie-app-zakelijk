"""Thread-isolatietests voor SQLite-connecties (DEF-488)."""

from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

import pytest

from database.db_connection import DatabaseConnection

pytestmark = [pytest.mark.unit]


def test_reader_thread_does_not_commit_writer_transaction(tmp_path):
    """Een read op thread B mag de transactie van thread A niet committen."""
    db_path = tmp_path / "thread-isolation.db"
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

    writer_started = threading.Event()
    reader_finished = threading.Event()
    writer_finished = threading.Event()

    def write_then_rollback() -> None:
        def write_then_fail() -> None:
            with db.transaction() as writer_conn:
                writer_conn.execute("INSERT INTO writes VALUES ('thread A')")
                writer_started.set()
                assert reader_finished.wait(timeout=3), "reader thread bleef hangen"
                raise RuntimeError("rollback thread A")

        try:
            with pytest.raises(RuntimeError, match="rollback thread A"):
                write_then_fail()
        finally:
            db.get_connection().close()
            writer_finished.set()

    def read_metadata() -> None:
        assert writer_started.wait(timeout=3), "writer thread startte niet"
        try:
            assert db.has_legacy_columns() is True
            reader_finished.set()
            assert writer_finished.wait(timeout=3), "writer thread bleef hangen"
        finally:
            db.get_connection().close()

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            writer = executor.submit(write_then_rollback)
            reader = executor.submit(read_metadata)
            reader.result(timeout=5)
            writer.result(timeout=5)
    finally:
        conn.close()
    with closing(sqlite3.connect(db_path)) as verification_conn:
        rows = verification_conn.execute("SELECT value FROM writes").fetchall()

    assert rows == []


def test_rollback_on_one_thread_keeps_other_thread_commit(tmp_path):
    """Thread B commit na A's rollback blijft zelfstandig behouden."""
    db_path = tmp_path / "rollback-isolation.db"
    db = DatabaseConnection(str(db_path))
    setup_connection = db.get_connection()
    try:
        setup_connection.execute("CREATE TABLE writes (value TEXT NOT NULL)")
    finally:
        setup_connection.close()

    second_connection_ready = threading.Event()
    writer_started = threading.Event()
    connections_compared = threading.Event()
    first_writer_finished = threading.Event()
    writer_connections: list[sqlite3.Connection] = []

    def rollback_first_writer() -> None:
        def write_then_fail() -> None:
            assert second_connection_ready.wait(timeout=3)
            with db.transaction() as connection:
                writer_connections.append(connection)
                connection.execute("INSERT INTO writes VALUES ('thread A')")
                writer_started.set()
                assert connections_compared.wait(timeout=3)
                raise RuntimeError("rollback thread A")

        try:
            with pytest.raises(RuntimeError, match="rollback thread A"):
                write_then_fail()
        finally:
            db.get_connection().close()
            first_writer_finished.set()

    def commit_second_writer() -> None:
        connection = db.get_connection()
        try:
            second_connection_ready.set()
            assert writer_started.wait(timeout=3)
            is_isolated = connection is not writer_connections[0]
            connections_compared.set()
            assert first_writer_finished.wait(timeout=3)
            assert is_isolated, "thread B kreeg de connectie van thread A"

            with db.transaction() as transaction_connection:
                assert transaction_connection is connection
                transaction_connection.execute("INSERT INTO writes VALUES ('thread B')")
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_writer = executor.submit(rollback_first_writer)
        second_writer = executor.submit(commit_second_writer)
        first_writer.result(timeout=7)
        second_writer.result(timeout=7)

    with closing(sqlite3.connect(db_path)) as verification_conn:
        rows = verification_conn.execute("SELECT value FROM writes").fetchall()

    assert rows == [("thread B",)]
