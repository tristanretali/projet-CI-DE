import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from models import Transaction


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
                montant=Decimal(row["montant"]),
            )
            for row in csv.DictReader(f)
        ]
