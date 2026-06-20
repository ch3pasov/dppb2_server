#!/usr/bin/env python3
"""Read the maps: list from config.yaml (for Docker init loops and validation)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required", file=sys.stderr)
    sys.exit(1)


def parse_maps(data: dict) -> list[str]:
    if not isinstance(data, dict):
        print("config root must be a mapping", file=sys.stderr)
        sys.exit(1)
    m = data.get("maps")
    if not isinstance(m, list) or len(m) < 1:
        print("maps must be a non-empty list of map names (basenames, no .bsp)", file=sys.stderr)
        sys.exit(1)
    out: list[str] = []
    for i, x in enumerate(m):
        if not isinstance(x, str) or not x.strip():
            print(f"maps[{i}] must be a non-empty string", file=sys.stderr)
            sys.exit(1)
        name = x.strip()
        for bad in ("/", "\\", ".."):
            if bad in name:
                print(f"invalid map name {name!r} (no paths)", file=sys.stderr)
                sys.exit(1)
        out.append(name)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Print map names from config.yaml")
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--first", action="store_true", help="print only the first map (startup map)")
    args = ap.parse_args()
    raw = args.config.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    names = parse_maps(data if isinstance(data, dict) else {})
    if args.first:
        print(names[0])
    else:
        for n in names:
            print(n)


if __name__ == "__main__":
    main()
