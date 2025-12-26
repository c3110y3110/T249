#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="$ROOT_DIR/TSR_MonitoringServer-master/TSR_MonitoringServer-master"

cd "$SERVER_DIR"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
