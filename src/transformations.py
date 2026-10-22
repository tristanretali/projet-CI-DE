from collections import defaultdict
from dataclasses import replace
from decimal import Decimal

from models import ProcessingResult

FLAG_THRESHOLD = Decimal("5000")


def _sum_by(transactions, key):
    totals = defaultdict(Decimal)
    for transaction in transactions:
        totals[key(transaction)] += transaction.montant
    return dict(totals)


def total_sent_by_iban(transactions):
    return _sum_by(transactions, lambda t: t.iban_origine)


def total_sent_by_bank(transactions):
    return _sum_by(transactions, lambda t: t.banque_source)


def total_received_by_iban(transactions):
    return _sum_by(transactions, lambda t: t.iban_destinataire)


def flag_transactions(transactions, threshold=FLAG_THRESHOLD):
    return [replace(t, flagged=t.montant > threshold) for t in transactions]


def process(transactions):
    return ProcessingResult(
        sent_by_iban=total_sent_by_iban(transactions),
        sent_by_bank=total_sent_by_bank(transactions),
        received_by_iban=total_received_by_iban(transactions),
        transactions=flag_transactions(transactions),
    )
