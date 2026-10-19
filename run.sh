#!/bin/sh
# Load .env and start the app.
cd "$(dirname "$0")" && set -a && . ./.env && set +a && exec .venv/bin/python -W default app.py
