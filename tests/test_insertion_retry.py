import sqlite3
import time

import pytest

import database
from database import create_schema, insert_result
from generate_csv import generate_csv_files
from loaders import file_sha256, load_transactions
from process import find_new_files
from transformations import process


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda seconds: None)


@pytest.fixture
def data_dir(tmp_path):
    generate_csv_files(tmp_path / "data")
    return tmp_path / "data"


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    create_schema(connection)
    yield connection
    connection.close()


def batch(data_dir):
    files = [(path.name, file_sha256(path)) for path in sorted(data_dir.glob("*.csv"))]
    transactions = [
        t for path in sorted(data_dir.glob("*.csv")) for t in load_transactions(path)
    ]
    return process(transactions), files


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def fail_totals_insertion(monkeypatch, times):
    real = database._insert_totals
    calls = []

    def flaky(*args):
        calls.append(1)
        if len(calls) <= times:
            raise sqlite3.OperationalError("database is locked")
        return real(*args)

    monkeypatch.setattr(database, "_insert_totals", flaky)


def test_retry_recovers_from_transient_insertion_failures(conn, data_dir, monkeypatch):
    result, files = batch(data_dir)
    fail_totals_insertion(monkeypatch, times=2)

    insert_result(conn, result, files)

    assert count(conn, "transactions") == 21
    assert count(conn, "processed_files") == 3
    assert conn.execute("SELECT SUM(total) FROM sent_by_iban").fetchone()[0] == 55145


def test_failed_insertion_leaves_nothing_behind(conn, data_dir, monkeypatch):
    result, files = batch(data_dir)
    fail_totals_insertion(monkeypatch, times=100)

    with pytest.raises(sqlite3.OperationalError):
        insert_result(conn, result, files)

    assert count(conn, "transactions") == 0
    assert count(conn, "sent_by_iban") == 0
    assert count(conn, "processed_files") == 0
    assert len(find_new_files(conn, data_dir)) == 3


def test_already_processed_file_is_not_inserted_again(conn, data_dir):
    result, files = batch(data_dir)
    insert_result(conn, result, files)

    with pytest.raises(sqlite3.IntegrityError):
        insert_result(conn, result, files)

    assert count(conn, "transactions") == 21
    assert conn.execute("SELECT SUM(total) FROM sent_by_iban").fetchone()[0] == 55145


def test_integrity_error_is_not_retried(conn, data_dir, monkeypatch):
    result, files = batch(data_dir)
    insert_result(conn, result, files)
    sleeps = []
    monkeypatch.setattr(time, "sleep", sleeps.append)

    with pytest.raises(sqlite3.IntegrityError):
        insert_result(conn, result, files)

    assert sleeps == []


def test_find_new_files_ignores_files_already_processed(conn, data_dir):
    result, files = batch(data_dir)
    insert_result(conn, result, files)

    assert find_new_files(conn, data_dir) == []


def test_find_new_files_ignores_renamed_copy_of_processed_file(conn, data_dir):
    result, files = batch(data_dir)
    insert_result(conn, result, files)
    first = sorted(data_dir.glob("*.csv"))[0]
    (data_dir / "copie.csv").write_bytes(first.read_bytes())

    assert find_new_files(conn, data_dir) == []


def test_find_new_files_detects_new_content(conn, data_dir):
    result, files = batch(data_dir)
    insert_result(conn, result, files)
    new_file = data_dir / "transactions_004.csv"
    new_file.write_text(
        (data_dir / "transactions_001.csv").read_text().replace("120", "121")
    )

    assert [path.name for path, _ in find_new_files(conn, data_dir)] == [new_file.name]


def test_find_new_files_keeps_one_copy_of_identical_files(conn, data_dir):
    first = sorted(data_dir.glob("*.csv"))[0]
    (data_dir / "copie.csv").write_bytes(first.read_bytes())

    assert len(find_new_files(conn, data_dir)) == 3
