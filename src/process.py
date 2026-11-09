import sqlite3
from contextlib import closing
from pathlib import Path

from database import create_schema, get_processed_hashes, insert_result
from loaders import content_sha256, load_transactions
from s3 import fetch_csv_files, get_client
from transformations import process

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


def find_new_files(conn, contents):
    processed = get_processed_hashes(conn)
    new_files = {}
    for key, content in sorted(contents.items()):
        sha256 = content_sha256(content)
        if sha256 not in processed:
            new_files.setdefault(sha256, (key, content))
    return [(key, sha256, content) for sha256, (key, content) in new_files.items()]


def main():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        create_schema(conn)
        new_files = find_new_files(conn, fetch_csv_files(get_client()))
        if not new_files:
            print("Aucun nouveau fichier à traiter")
            return

        transactions = [
            transaction
            for _, _, content in new_files
            for transaction in load_transactions(content)
        ]
        result = process(transactions)
        print(f"{len(new_files)} nouveau(x) fichier(s) à traiter")
        print_result(result)
        insert_result(conn, result, [(key, sha256) for key, sha256, _ in new_files])


if __name__ == "__main__":
    main()
