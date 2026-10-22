import argparse
import csv
from pathlib import Path

COLUMNS = [
    "datetime_transaction",
    "iban_origine",
    "pays_source",
    "banque_source",
    "iban_destinataire",
    "pays_destinataire",
    "montant",
]

ACCOUNTS = {
    "A1": {
        "iban": "FR7630006000011234567890189",
        "pays": "FR",
        "banque": "BNP Paribas",
    },
    "A2": {
        "iban": "FR1420041010050500013M02606",
        "pays": "FR",
        "banque": "La Banque Postale",
    },
    "A3": {"iban": "DE89370400440532013000", "pays": "DE", "banque": "Deutsche Bank"},
    "A4": {"iban": "ES9121000418450200051332", "pays": "ES", "banque": "Santander"},
    "A5": {"iban": "BE68539007547034", "pays": "BE", "banque": "BNP Paribas Fortis"},
}

# Cas limites
TRANSACTIONS_BY_FILE = {
    "transactions_001.csv": [
        ("2025-01-10T09:15:00", "A1", "A3", "120.50"),
        ("2025-01-10T10:02:00", "A1", "A4", "4999.99"),
        ("2025-01-10T11:45:00", "A2", "A1", "5000.00"),
        ("2025-01-10T13:20:00", "A3", "A1", "7500.00"),
        ("2025-01-10T15:05:00", "A4", "A5", "35.00"),
        ("2025-01-10T16:40:00", "A1", "A3", "80.00"),
    ],
    "transactions_002.csv": [
        ("2025-01-11T08:00:00", "A1", "A2", "250.00"),
        ("2025-01-11T08:30:00", "A2", "A3", "5000.01"),
        ("2025-01-11T09:10:00", "A3", "A4", "1200.00"),
        ("2025-01-11T10:00:00", "A4", "A1", "300.00"),
        ("2025-01-11T11:25:00", "A5", "A1", "9800.00"),
        ("2025-01-11T12:00:00", "A5", "A2", "150.75"),
        ("2025-01-11T13:35:00", "A1", "A4", "60.00"),
        ("2025-01-11T14:50:00", "A2", "A5", "5500.00"),
        ("2025-01-11T16:15:00", "A3", "A1", "45.25"),
        ("2025-01-11T17:30:00", "A4", "A3", "20.00"),
    ],
    "transactions_003.csv": [
        ("2025-01-12T09:00:00", "A1", "A5", "100.00"),
        ("2025-01-12T10:30:00", "A2", "A4", "12000.00"),
        ("2025-01-12T12:15:00", "A3", "A2", "75.00"),
        ("2025-01-12T14:45:00", "A5", "A3", "2500.00"),
        ("2025-01-12T18:00:00", "A4", "A1", "410.20"),
    ],
}


def build_rows(transactions):
    rows = []
    for dt, origin_key, dest_key, amount in transactions:
        origin = ACCOUNTS[origin_key]
        dest = ACCOUNTS[dest_key]
        rows.append(
            [
                dt,
                origin["iban"],
                origin["pays"],
                origin["banque"],
                dest["iban"],
                dest["pays"],
                amount,
            ]
        )
    return rows


def generate_csv_files(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for filename, transactions in TRANSACTIONS_BY_FILE.items():
        path = output_dir / filename
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)
            writer.writerows(build_rows(transactions))
        paths.append(path)
    return paths


def main():
    parser = argparse.ArgumentParser(
        description="Génère des CSV de transactions financières"
    )
    parser.add_argument(
        "--output-dir", default="data", help="dossier de sortie (défaut : data)"
    )
    args = parser.parse_args()

    for path in generate_csv_files(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
