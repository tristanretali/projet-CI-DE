import csv
import hashlib
from datetime import datetime
from pathlib import Path

from models import Transaction


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_transactions(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return [
            Transaction(
                datetime_transaction=datetime.fromisoformat(
                    row["datetime_transaction"]
                ),
                iban_origine=row["iban_origine"],
                pays_source=row["pays_source"],
                banque_source=row["banque_source"],
                iban_destinataire=row["iban_destinataire"],
                pays_destinataire=row["pays_destinataire"],
                montant=int(row["montant"]),
            )
            for row in csv.DictReader(f)
        ]
