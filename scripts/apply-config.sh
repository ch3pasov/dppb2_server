#!/bin/sh
# Render project config.yaml (or config.yml) into the PB2 configs directory.
set -e
DEST="${1:?usage: apply-config.sh <pball/configs-dir>}"
CONFIG_DIR="${CONFIG_DIR:-/config}"
mkdir -p "$DEST"

YAML=""
for f in config.yaml config.yml; do
  if [ -f "$CONFIG_DIR/$f" ]; then
    YAML="$CONFIG_DIR/$f"
    break
  fi
done

if [ -z "$YAML" ]; then
  echo "dppb2: expected $CONFIG_DIR/config.yaml (or config.yml)" >&2
  exit 1
fi

exec python3 /scripts/render_config.py --config "$YAML" --dest "$DEST"
