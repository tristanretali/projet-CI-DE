#!/bin/sh
set -e
cd "$(dirname "$0")"

if [ -d .venv ]; then
    . .venv/bin/activate
fi

docker compose up -d
python3 src/generate_csv.py
python3 src/process.py
