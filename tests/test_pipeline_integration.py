import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"

BNP = "FR7630006000011234567890189"
POSTALE = "FR1420041010050500013M02606"
DEUTSCHE = "DE89370400440532013000"
SANTANDER = "ES9121000418450200051332"
FORTIS = "BE68539007547034"

EXPECTED_FLAGGED_AMOUNTS = [5001, 5500, 7500, 9800, 12000]

EXPECTED_SENT_BY_IBAN = {
    BNP: 5609,
    POSTALE: 27501,
    DEUTSCHE: 8820,
    SANTANDER: 765,
    FORTIS: 12450,
}

EXPECTED_SENT_BY_BANK = {
    "BNP Paribas": 5609,
    "La Banque Postale": 27501,
    "Deutsche Bank": 8820,
    "Santander": 765,
    "BNP Paribas Fortis": 12450,
}

EXPECTED_RECEIVED_BY_IBAN = {
    BNP: 23055,
    POSTALE: 475,
    DEUTSCHE: 7721,
    SANTANDER: 18259,
    FORTIS: 5635,
}


@pytest.fixture(scope="module")
def conn(tmp_path_factory):
    workdir = tmp_path_factory.mktemp("pipeline")
    for script in ("generate_csv.py", "process.py"):
        subprocess.run([sys.executable, str(SRC_DIR / script)], cwd=workdir, check=True)
    with closing(sqlite3.connect(workdir / "transaction.db")) as connection:
        yield connection


def totals(conn, table, key_column):
    return dict(conn.execute(f"SELECT {key_column}, total FROM {table}"))


def test_all_transactions_are_inserted(conn):
    (count,) = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()
    assert count == 21


def test_only_transactions_above_5000_are_flagged(conn):
    flagged = conn.execute(
        "SELECT montant FROM transactions WHERE flagged = 1 ORDER BY montant"
    ).fetchall()
    assert [montant for (montant,) in flagged] == EXPECTED_FLAGGED_AMOUNTS


def test_flag_is_consistent_with_amount(conn):
    (inconsistent,) = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE flagged != (montant > 5000)"
    ).fetchone()
    assert inconsistent == 0


def test_total_sent_by_iban(conn):
    assert totals(conn, "sent_by_iban", "iban") == EXPECTED_SENT_BY_IBAN


def test_total_sent_by_bank(conn):
    assert totals(conn, "sent_by_bank", "banque") == EXPECTED_SENT_BY_BANK


def test_total_received_by_iban(conn):
    assert totals(conn, "received_by_iban", "iban") == EXPECTED_RECEIVED_BY_IBAN


def test_totals_are_consistent_with_transactions(conn):
    (amount_sum,) = conn.execute("SELECT SUM(montant) FROM transactions").fetchone()
    for table in ("sent_by_iban", "sent_by_bank", "received_by_iban"):
        (total_sum,) = conn.execute(f"SELECT SUM(total) FROM {table}").fetchone()
        assert total_sum == amount_sum
