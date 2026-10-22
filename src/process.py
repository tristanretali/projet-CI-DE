import sqlite3
from contextlib import closing
from pathlib import Path

from database import create_schema, insert_result
from loaders import load_transactions
from transformations import process

DATA_DIR = Path("data")
DB_PATH = Path("transaction.db")


def print_result(result):
    for title, totals in (
        ("Envoyé par IBAN", result.sent_by_iban),
        ("Envoyé par banque", result.sent_by_bank),
        ("Reçu par IBAN", result.received_by_iban),
    ):
        print(f"{title} :")
        for key, total in sorted(totals.items()):
            print(f"  {key} : {total}")
    flagged = [t for t in result.transactions if t.flagged]
    print(f"Transactions flaggées : {len(flagged)}/{len(result.transactions)}")


def main():
    transactions = [
        transaction
        for path in sorted(DATA_DIR.glob("*.csv"))
        for transaction in load_transactions(path)
    ]
    result = process(transactions)
    print_result(result)

    with closing(sqlite3.connect(DB_PATH)) as conn:
        create_schema(conn)
        insert_result(conn, result)


if __name__ == "__main__":
    main()
