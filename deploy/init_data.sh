#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$ROOT_DIR/data"

mkdir -p "$DATA_DIR/output"

for f in henu_profile.json henu_cookies.json henu_library_cookies.json xiqueer_period_time_request.json period_time_calibration_state.json; do
  if [ ! -f "$DATA_DIR/$f" ]; then
    echo '{}' > "$DATA_DIR/$f"
  fi
done

if [ ! -f "$DATA_DIR/period_time_config.json" ]; then
  cp "$ROOT_DIR/period_time_config.json" "$DATA_DIR/period_time_config.json"
fi

chmod 700 "$DATA_DIR"
chmod 600 "$DATA_DIR/henu_profile.json" "$DATA_DIR/henu_cookies.json" "$DATA_DIR/henu_library_cookies.json" "$DATA_DIR/xiqueer_period_time_request.json" "$DATA_DIR/period_time_calibration_state.json" "$DATA_DIR/period_time_config.json"

echo "初始化完成: $DATA_DIR"
