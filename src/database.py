SCHEMA = """
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


def insert_result(conn, result):
    with conn:
        _insert_transactions(conn, result.transactions)
        _insert_totals(conn, "sent_by_iban", "iban", result.sent_by_iban)
        _insert_totals(conn, "sent_by_bank", "banque", result.sent_by_bank)
        _insert_totals(conn, "received_by_iban", "iban", result.received_by_iban)
