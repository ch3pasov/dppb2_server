#!/bin/sh
# Run PB2 dedicated server; first map comes from generated rotation.txt (same order as config.yaml maps:).
set -e
ROT="${PB2_ROTATION_FILE:-/paintball2/pball/configs/rotation.txt}"
if [ ! -f "$ROT" ]; then
  echo "start_dedicated.sh: rotation.txt not found: $ROT" >&2
  exit 1
fi
MAP=$(awk '/^\[maplist\]/{getline; print; exit}' "$ROT")
if [ -z "$MAP" ]; then
  echo "start_dedicated.sh: no map line after [maplist] in $ROT" >&2
  exit 1
fi
cd /paintball2 || exit 1
exec start.sh +set dedicated 1 +exec server.cfg +map "$MAP"
