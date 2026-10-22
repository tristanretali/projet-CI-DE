#!/bin/sh
set -e
cd "$(dirname "$0")"

rm -rf data transaction.db

python3 src/generate_csv.py
python3 src/process.py
