#!/bin/sh
# Render config/server.yaml (or .yml) into the PB2 configs directory.
set -e
DEST="${1:?usage: apply-config.sh <pball/configs-dir>}"
CONFIG="${CONFIG_DIR:-/config}"
mkdir -p "$DEST"

YAML=""
for f in server.yaml server.yml; do
  if [ -f "$CONFIG/$f" ]; then
    YAML="$CONFIG/$f"
    break
  fi
done

if [ -z "$YAML" ]; then
  echo "dppb2: expected $CONFIG/server.yaml (or server.yml)" >&2
  exit 1
fi

exec python3 /scripts/render_config.py --config "$YAML" --dest "$DEST"
