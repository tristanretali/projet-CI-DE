import csv
import hashlib
import io
from datetime import datetime

from models import Transaction


def content_sha256(content):
    return hashlib.sha256(content).hexdigest()


def load_transactions(content):
    text = io.StringIO(content.decode("utf-8"), newline="")
    return [
        Transaction(
            datetime_transaction=datetime.fromisoformat(row["datetime_transaction"]),
            iban_origine=row["iban_origine"],
            pays_source=row["pays_source"],
            banque_source=row["banque_source"],
            iban_destinataire=row["iban_destinataire"],
            pays_destinataire=row["pays_destinataire"],
            montant=int(row["montant"]),
        )
        for row in csv.DictReader(text)
    ]
