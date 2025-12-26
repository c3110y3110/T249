#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="$ROOT_DIR/TSR_MonitoringServer-master/TSR_MonitoringServer-master"

WATCH_DIR="${1:-$ROOT_DIR/sample_csv}"
MACHINE_NAME="${MACHINE_NAME:-ShotBlast}"
SENSOR_NAME="${SENSOR_NAME:-shot_blast_vib1}"
SERVER_HOST="${SERVER_HOST:-127.0.0.1}"
SERVER_PORT="${SERVER_PORT:-8082}"

python "$SERVER_DIR/tools/csv_bridge.py" \
  --watch-dir "$WATCH_DIR" \
  --host "$SERVER_HOST" \
  --port "$SERVER_PORT" \
  --machine-name "$MACHINE_NAME" \
  --sensor-name "$SENSOR_NAME" \
  --sensor-type "VIB" \
  --output-rate 30 \
  --replay-sleep
