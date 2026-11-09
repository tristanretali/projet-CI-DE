import sqlite3
import time

import pytest

import database
from database import create_schema, insert_result
from generate_csv import build_csv_files
from loaders import content_sha256, load_transactions
from process import find_new_files
from transformations import process


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda seconds: None)


@pytest.fixture
def contents():
    return {f"incoming/{name}": data for name, data in build_csv_files().items()}


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    create_schema(connection)
    yield connection
    connection.close()


def batch(contents):
    files = [(key, content_sha256(data)) for key, data in sorted(contents.items())]
    transactions = [
        t for _, data in sorted(contents.items()) for t in load_transactions(data)
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


def test_retry_recovers_from_transient_insertion_failures(
    conn, contents, monkeypatch
):
    result, files = batch(contents)
    fail_totals_insertion(monkeypatch, times=2)

    insert_result(conn, result, files)

    assert count(conn, "transactions") == 21
    assert count(conn, "processed_files") == 3
    assert conn.execute("SELECT SUM(total) FROM sent_by_iban").fetchone()[0] == 55145


def test_failed_insertion_leaves_nothing_behind(conn, contents, monkeypatch):
    result, files = batch(contents)
    fail_totals_insertion(monkeypatch, times=100)

    with pytest.raises(sqlite3.OperationalError):
        insert_result(conn, result, files)

    assert count(conn, "transactions") == 0
    assert count(conn, "sent_by_iban") == 0
    assert count(conn, "processed_files") == 0
    assert len(find_new_files(conn, contents)) == 3


def test_already_processed_file_is_not_inserted_again(conn, contents):
    result, files = batch(contents)
    insert_result(conn, result, files)

    with pytest.raises(sqlite3.IntegrityError):
        insert_result(conn, result, files)

    assert count(conn, "transactions") == 21
    assert conn.execute("SELECT SUM(total) FROM sent_by_iban").fetchone()[0] == 55145


def test_integrity_error_is_not_retried(conn, contents, monkeypatch):
    result, files = batch(contents)
    insert_result(conn, result, files)
    sleeps = []
    monkeypatch.setattr(time, "sleep", sleeps.append)

    with pytest.raises(sqlite3.IntegrityError):
        insert_result(conn, result, files)

    assert sleeps == []


def test_find_new_files_ignores_files_already_processed(conn, contents):
    result, files = batch(contents)
    insert_result(conn, result, files)

    assert find_new_files(conn, contents) == []


def test_find_new_files_ignores_renamed_copy_of_processed_file(conn, contents):
    result, files = batch(contents)
    insert_result(conn, result, files)
    contents["incoming/copie.csv"] = contents["incoming/transactions_001.csv"]

    assert find_new_files(conn, contents) == []


def test_find_new_files_detects_new_content(conn, contents):
    result, files = batch(contents)
    insert_result(conn, result, files)
    contents["incoming/transactions_004.csv"] = contents[
        "incoming/transactions_001.csv"
    ].replace(b"120", b"121")

    new_files = find_new_files(conn, contents)

    assert [key for key, _, _ in new_files] == ["incoming/transactions_004.csv"]


def test_find_new_files_keeps_one_copy_of_identical_files(conn, contents):
    contents["incoming/copie.csv"] = contents["incoming/transactions_001.csv"]

    assert len(find_new_files(conn, contents)) == 3
