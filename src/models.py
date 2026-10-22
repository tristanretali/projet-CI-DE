from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Transaction:
    datetime_transaction: datetime
    iban_origine: str
    pays_source: str
    banque_source: str
    iban_destinataire: str
    pays_destinataire: str
    montant: int
    flagged: bool = False


@dataclass(frozen=True)
class ProcessingResult:
    sent_by_iban: dict[str, int]
    sent_by_bank: dict[str, int]
    received_by_iban: dict[str, int]
    transactions: list[Transaction]
