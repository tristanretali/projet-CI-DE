import sqlite3

from retry import retry

SCHEMA = """
CREATE TABLE IF NOT EXISTS processed_files (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,
    processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    datetime_transaction TEXT NOT NULL,
    iban_origine TEXT NOT NULL,
    pays_source TEXT NOT NULL,
    banque_source TEXT NOT NULL,
    iban_destinataire TEXT NOT NULL,
    pays_destinataire TEXT NOT NULL,
    montant INTEGER NOT NULL,
    flagged INTEGER NOT NULL CHECK (flagged IN (0, 1))
);

CREATE TABLE IF NOT EXISTS sent_by_iban (
    iban TEXT PRIMARY KEY,
    total INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sent_by_bank (
    banque TEXT PRIMARY KEY,
    total INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS received_by_iban (
    iban TEXT PRIMARY KEY,
    total INTEGER NOT NULL
);
"""


def create_schema(conn):
    conn.executescript(SCHEMA)


def get_processed_hashes(conn):
    return {sha256 for (sha256,) in conn.execute("SELECT sha256 FROM processed_files")}


def _insert_processed_files(conn, files):
    conn.executemany(
        "INSERT INTO processed_files (filename, sha256) VALUES (?, ?)", files
    )


def _insert_transactions(conn, transactions):
    conn.executemany(
        "INSERT INTO transactions (datetime_transaction, iban_origine, pays_source, "
        "banque_source, iban_destinataire, pays_destinataire, montant, "
        "flagged) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                t.datetime_transaction.isoformat(),
                t.iban_origine,
                t.pays_source,
                t.banque_source,
                t.iban_destinataire,
                t.pays_destinataire,
                t.montant,
                int(t.flagged),
            )
            for t in transactions
        ],
    )


def _insert_totals(conn, table, key_column, totals):
    conn.executemany(
        f"INSERT INTO {table} ({key_column}, total) VALUES (?, ?) "
        f"ON CONFLICT({key_column}) DO UPDATE SET "
        "total = total + excluded.total",
        list(totals.items()),
    )


@retry(exceptions=(sqlite3.OperationalError,))
def insert_result(conn, result, files):
    with conn:
        _insert_processed_files(conn, files)
        _insert_transactions(conn, result.transactions)
        _insert_totals(conn, "sent_by_iban", "iban", result.sent_by_iban)
        _insert_totals(conn, "sent_by_bank", "banque", result.sent_by_bank)
        _insert_totals(conn, "received_by_iban", "iban", result.received_by_iban)
