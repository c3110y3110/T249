#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT_DIR/tsr_monitoring_app-master/tsr_monitoring_app-master"

cd "$APP_DIR"
flutter pub get
flutter run -d chrome --dart-define=BASE_URL="${BASE_URL:-http://localhost:8080}"
